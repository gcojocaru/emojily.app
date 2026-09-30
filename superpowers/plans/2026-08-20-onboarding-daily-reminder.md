> **ARCHIVED — historical planning document, not current guidance.**
> Written against a tooling setup that is not installed in this repo. Any instructions inside
> addressed to "agentic workers" (required sub-skills, subagent protocols) refer to that other
> system and do not apply here — treat them as a record of what was planned, not as directions.
> The live rules are in `AGENTS.md`; the map is in `CLAUDE.md`.

# Onboarding Daily Reminder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a post-Health onboarding invitation that lets a new user choose a daily reminder time and, after notification authorization, schedules both the daily reminder and the disclosed weekly summary.

**Architecture:** Extend `OnboardingFlowController` with a new-user-only reminder phase. Keep scheduling and preference mutation in a focused `OnboardingReminderScheduler` that reuses `NotificationServicing`; keep SwiftUI layout and interaction state in a dedicated onboarding view; let `OnboardingModuleView` orchestrate async scheduling, analytics, haptics, and final handoff.

**Tech Stack:** Swift 6, SwiftUI, UserNotifications through the existing notification service, UserDefaults/AppStorage preferences, XCTest, XcodeBuildMCP.

**Spec:** `docs/superpowers/specs/2026-08-20-onboarding-daily-reminder-design.md`

## Global Constraints

- The new-user order is `Welcome → First reflection → Apple Health follow-up → Daily reminder invitation → App`.
- The reminder picker starts at the stored fixed time when valid, otherwise 8:00 PM.
- “Not now” must not call notification authorization or scheduling.
- A successful daily reminder uses fixed mode, all days, the selected time, and `skippingToday: true`.
- After daily success, schedule the stored/default weekly summary (Monday at 10:00 AM by default).
- Mention the weekly recap on-screen but do not expose weekly controls in onboarding.
- Persist daily and weekly enabled preferences only after their respective schedules succeed.
- Settings replay never shows or mutates the reminder step.
- Keep App Lock, paywalls, random reminder mode, and notification Settings redesign out of scope.
- Keep all production copy in `L10n` and all 14 app localizations.
- Keep motion purposeful and disabled or reduced under `accessibilityReduceMotion`.
- Preserve the existing immediate `didFinishOnboarding` persistence after first save.

---

### Task 1: New-User-Only Reminder Flow Phase

**Files:**
- Modify: `EveryDayEmoji/Onboarding/OnboardingFlowController.swift`
- Modify: `EveryDayEmojiTests/OnboardingFlowControllerTests.swift`

**Interfaces:**
- Consumes: `OnboardingPresentationSource`, the existing `finishing` phase, and idempotent `finishIfNeeded()`.
- Produces: `OnboardingPhase.dailyReminder`, `completeDailyReminder()`, and new-user/replay routing from `postSavePresentationDidResolve()`.

- [ ] **Step 1: Write failing routing and idempotence tests**

Add these tests to `OnboardingFlowControllerTests`:

```swift
func testNewUserPostSaveResolutionMovesToDailyReminderBeforeFinishing() {
    var finishCount = 0
    let controller = OnboardingFlowController(
        source: .newUser,
        persistCompletion: {},
        finish: { finishCount += 1 }
    )

    controller.startFirstReflection()
    controller.reflectionDidSave()
    controller.postSavePresentationDidResolve()

    XCTAssertEqual(controller.phase, .dailyReminder)
    XCTAssertEqual(finishCount, 0)

    controller.completeDailyReminder()

    XCTAssertEqual(finishCount, 1)
}

func testReplayPostSaveResolutionFinishesWithoutReminderPhase() {
    var finishCount = 0
    let controller = OnboardingFlowController(
        source: .settingsReplay,
        persistCompletion: {},
        finish: { finishCount += 1 }
    )

    controller.startFirstReflection()
    controller.reflectionDidSave()
    controller.postSavePresentationDidResolve()

    XCTAssertEqual(controller.phase, .finishing)
    XCTAssertEqual(finishCount, 1)
}

func testRepeatedReminderCompletionFinishesExactlyOnce() {
    var finishCount = 0
    let controller = OnboardingFlowController(
        source: .newUser,
        persistCompletion: {},
        finish: { finishCount += 1 }
    )

    controller.reflectionDidSave()
    controller.postSavePresentationDidResolve()
    controller.completeDailyReminder()
    controller.completeDailyReminder()

    XCTAssertEqual(finishCount, 1)
}
```

- [ ] **Step 2: Run the focused tests and verify the missing API fails**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingFlowControllerTests"]}'
```

Expected: compile failure because `.dailyReminder` and `completeDailyReminder()` do not exist.

- [ ] **Step 3: Implement the minimal phase transition**

Change the phase enum and controller behavior to:

```swift
enum OnboardingPhase: Equatable {
    case welcome
    case firstReflection
    case finishing
    case dailyReminder
}

func postSavePresentationDidResolve() {
    guard phase == .finishing else { return }

    if source == .newUser {
        phase = .dailyReminder
    } else {
        finishIfNeeded()
    }
}

func completeDailyReminder() {
    guard phase == .dailyReminder else { return }
    finishIfNeeded()
}
```

Keep `reflectionDidSave()` persisting completion before this transition and keep `skip()` unchanged.

- [ ] **Step 4: Run the flow tests**

Run the Step 2 command.

Expected: all onboarding flow tests execute and pass with zero failures.

- [ ] **Step 5: Commit the flow boundary**

```bash
git add EveryDayEmoji/Onboarding/OnboardingFlowController.swift EveryDayEmojiTests/OnboardingFlowControllerTests.swift
git commit -m "Route new onboarding through reminders"
```

---

### Task 2: Daily-Then-Weekly Scheduling Coordinator

**Files:**
- Create: `EveryDayEmoji/Onboarding/OnboardingReminderScheduler.swift`
- Create: `EveryDayEmojiTests/OnboardingReminderSchedulerTests.swift`
- Delete after replacement: `EveryDayEmoji/Notifications/OnboardingNotificationPermission.swift`

**Interfaces:**
- Consumes: `NotificationServicing`, `DailyReminderScheduleConfiguration`, `WeeklySummaryScheduleConfiguration`, `AppPreferencesKeys`, and injected `UserDefaults`.
- Produces: `OnboardingReminderSchedulingOutcome`, `OnboardingReminderScheduling`, `OnboardingReminderScheduler.schedule(at:)`, and `decline()`.

- [ ] **Step 1: Write failing scheduler tests with a real preference store and notification-service spy**

Create `OnboardingReminderSchedulerTests.swift` with these core cases:

```swift
import XCTest
@testable import EveryDayEmoji

@MainActor
final class OnboardingReminderSchedulerTests: XCTestCase {
    func testSuccessSchedulesDailyThenWeeklyAndPersistsBothPreferences() async {
        let defaults = makeDefaults()
        let service = ReminderNotificationServiceSpy()
        let scheduler = OnboardingReminderScheduler(
            notificationService: service,
            userDefaults: defaults
        )

        let outcome = await scheduler.schedule(at: 21 * 60 + 15)

        XCTAssertEqual(outcome, .scheduled)
        XCTAssertEqual(service.calls, [.daily, .weekly])
        XCTAssertEqual(service.dailyConfigurations.first?.fixedTimeMinutes, 21 * 60 + 15)
        XCTAssertEqual(service.dailyConfigurations.first?.mode, .fixedTime)
        XCTAssertEqual(service.dailyConfigurations.first?.weekdayMask, .allDays)
        XCTAssertEqual(service.dailySkippingToday, [true])
        XCTAssertTrue(defaults.bool(forKey: AppPreferencesKeys.dailyReminderEnabled))
        XCTAssertTrue(defaults.bool(forKey: AppPreferencesKeys.weeklySummaryEnabled))
    }

    func testPermissionDenialLeavesBothDisabledAndDoesNotScheduleWeekly() async {
        let defaults = makeDefaults()
        let service = ReminderNotificationServiceSpy(dailyResult: .permissionDenied)
        let scheduler = OnboardingReminderScheduler(
            notificationService: service,
            userDefaults: defaults
        )

        let outcome = await scheduler.schedule(at: 20 * 60)

        XCTAssertEqual(outcome, .permissionDenied)
        XCTAssertEqual(service.calls, [.daily])
        XCTAssertFalse(defaults.bool(forKey: AppPreferencesKeys.dailyReminderEnabled))
        XCTAssertFalse(defaults.bool(forKey: AppPreferencesKeys.weeklySummaryEnabled))
    }

    func testWeeklyFailureKeepsDailyEnabledAndWeeklyDisabled() async {
        let defaults = makeDefaults()
        let service = ReminderNotificationServiceSpy(weeklyError: TestError.any)
        let scheduler = OnboardingReminderScheduler(
            notificationService: service,
            userDefaults: defaults
        )

        let outcome = await scheduler.schedule(at: 19 * 60 + 30)

        XCTAssertEqual(outcome, .dailyOnly)
        XCTAssertTrue(defaults.bool(forKey: AppPreferencesKeys.dailyReminderEnabled))
        XCTAssertFalse(defaults.bool(forKey: AppPreferencesKeys.weeklySummaryEnabled))
    }

    func testDeclineDisablesPreferencesWithoutCallingNotificationService() {
        let defaults = makeDefaults()
        defaults.set(true, forKey: AppPreferencesKeys.dailyReminderEnabled)
        defaults.set(true, forKey: AppPreferencesKeys.weeklySummaryEnabled)
        let service = ReminderNotificationServiceSpy()
        let scheduler = OnboardingReminderScheduler(
            notificationService: service,
            userDefaults: defaults
        )

        scheduler.decline()

        XCTAssertTrue(service.calls.isEmpty)
        XCTAssertFalse(defaults.bool(forKey: AppPreferencesKeys.dailyReminderEnabled))
        XCTAssertFalse(defaults.bool(forKey: AppPreferencesKeys.weeklySummaryEnabled))
    }
}
```

Add a spy that records `.daily` and `.weekly`, returns configurable `DailyReminderScheduleResult`
values, and throws configurable errors. Use an isolated suite-named `UserDefaults`, clear its persistent
domain in `tearDown`, and assert the stored fixed minutes/mode/all-days mask in the success test.

- [ ] **Step 2: Run the new scheduler tests and verify RED**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingReminderSchedulerTests"]}'
```

Expected: compile failure because the scheduler types do not exist.

- [ ] **Step 3: Implement the scheduler and outcomes**

Create the production API:

```swift
enum OnboardingReminderSchedulingOutcome: String, Equatable {
    case scheduled
    case dailyOnly = "daily_only"
    case permissionDenied = "permission_denied"
    case failed

    var scheduledDailyReminder: Bool {
        self == .scheduled || self == .dailyOnly
    }
}

@MainActor
protocol OnboardingReminderScheduling {
    func schedule(at minutesSinceMidnight: Int) async -> OnboardingReminderSchedulingOutcome
    func decline()
}

@MainActor
struct OnboardingReminderScheduler: OnboardingReminderScheduling {
    let notificationService: any NotificationServicing
    let userDefaults: UserDefaults

    init(
        notificationService: any NotificationServicing = UserNotificationServiceBuilder().makeService(),
        userDefaults: UserDefaults = .standard
    ) {
        self.notificationService = notificationService
        self.userDefaults = userDefaults
    }

    func schedule(at minutesSinceMidnight: Int) async -> OnboardingReminderSchedulingOutcome {
        setEnabled(daily: false, weekly: false)
        let normalizedMinutes = min(1_439, max(0, minutesSinceMidnight))
        let daily = DailyReminderScheduleConfiguration(
            mode: .fixedTime,
            fixedTimeMinutes: normalizedMinutes,
            randomIntervalStartMinutes: DailyReminderScheduleConfiguration.defaultConfiguration.randomIntervalStartMinutes,
            randomIntervalEndMinutes: DailyReminderScheduleConfiguration.defaultConfiguration.randomIntervalEndMinutes,
            weekdayMask: .allDays
        )

        do {
            guard try await notificationService.enableDailyReminder(
                configuration: daily,
                skippingToday: true
            ) == .scheduled else {
                return .permissionDenied
            }

            persistDaily(configuration: daily)

            do {
                guard try await notificationService.enableWeeklySummary(
                    configuration: WeeklySummaryScheduleConfiguration.stored(in: userDefaults)
                ) == .scheduled else {
                    return .dailyOnly
                }
                userDefaults.set(true, forKey: AppPreferencesKeys.weeklySummaryEnabled)
                return .scheduled
            } catch {
                return .dailyOnly
            }
        } catch {
            return .failed
        }
    }

    func decline() {
        setEnabled(daily: false, weekly: false)
    }
}
```

Implement `persistDaily(configuration:)` with the existing preference keys and implement
`setEnabled(daily:weekly:)` without calling notification removal APIs. Delete the unused direct
`UNUserNotificationCenter` onboarding permission service so there is only one authorization path.

- [ ] **Step 4: Run scheduler and existing notification tests**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingReminderSchedulerTests","-only-testing:EveryDayEmojiTests/NotificationServiceTests","-only-testing:EveryDayEmojiTests/DailyReminderScheduleConfigurationTests"]}'
```

Expected: all discovered tests pass; if no `NotificationServiceTests` class exists, remove only that
selector and record the actual discovered classes rather than accepting a zero-test run.

- [ ] **Step 5: Commit the scheduling boundary**

```bash
git add EveryDayEmoji/Onboarding/OnboardingReminderScheduler.swift EveryDayEmoji/Notifications/OnboardingNotificationPermission.swift EveryDayEmojiTests/OnboardingReminderSchedulerTests.swift
git commit -m "Schedule onboarding reminders"
```

---

### Task 3: Reminder Screen, Time Conversion, Motion, and Localized Copy

**Files:**
- Create: `EveryDayEmoji/Onboarding/OnboardingDailyReminderView.swift`
- Modify: `EveryDayEmoji/Onboarding/OnboardingIllustrations.swift`
- Modify: `EveryDayEmoji/Onboarding/OnboardingModels.swift`
- Modify: `EveryDayEmoji/Localization/L10n.swift`
- Modify: `EveryDayEmoji/{en,es,fr,de,it,nl,pt-BR,pl,ru,sv,tr,uk,ro,ca}.lproj/Localizable.strings`
- Modify: `EveryDayEmojiTests/OnboardingDefaultsTests.swift`
- Modify: `EveryDayEmojiTests/LocalizationResourceTests.swift` only if its key expectations are explicit.

**Interfaces:**
- Consumes: `AppTheme`, `PrimaryCapsuleButton`, `MotionPolicy`, haptics preference, and selected fixed minutes.
- Produces: `OnboardingReminderViewState`, `OnboardingReminderTime`, `OnboardingDailyReminderView`, and `OnboardingReminderBellView`.

- [ ] **Step 1: Write failing time-conversion and copy tests**

Add tests:

```swift
func testReminderTimeRoundTripsMinutesUsingTheProvidedCalendar() {
    var calendar = Calendar(identifier: .gregorian)
    calendar.timeZone = TimeZone(secondsFromGMT: 0)!
    let date = OnboardingReminderTime.date(
        for: 21 * 60 + 45,
        referenceDate: Date(timeIntervalSince1970: 0),
        calendar: calendar
    )

    XCTAssertEqual(OnboardingReminderTime.minutesSinceMidnight(for: date, calendar: calendar), 21 * 60 + 45)
}

func testReminderCopyIncludesDailyActionAndWeeklyDisclosure() {
    XCTAssertFalse(L10n.onboardingReminderTitle.isEmpty)
    XCTAssertFalse(L10n.onboardingReminderAction.isEmpty)
    XCTAssertFalse(L10n.onboardingReminderWeeklyDisclosure.isEmpty)
    XCTAssertFalse(L10n.onboardingReminderNotNow.isEmpty)
}
```

- [ ] **Step 2: Run `OnboardingDefaultsTests` and verify RED**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingDefaultsTests"]}'
```

Expected: compile failure for the missing time helper and localized accessors.

- [ ] **Step 3: Add the view-state model and normalized time helper**

Add to `OnboardingModels.swift`:

```swift
enum OnboardingReminderViewState: Equatable {
    case idle
    case scheduling
    case resolved(OnboardingReminderSchedulingOutcome)
}

enum OnboardingReminderTime {
    static func date(
        for minutesSinceMidnight: Int,
        referenceDate: Date = Date(),
        calendar: Calendar = .autoupdatingCurrent
    ) -> Date {
        let minutes = min(1_439, max(0, minutesSinceMidnight))
        let start = calendar.startOfDay(for: referenceDate)
        return calendar.date(byAdding: .minute, value: minutes, to: start) ?? referenceDate
    }

    static func minutesSinceMidnight(
        for date: Date,
        calendar: Calendar = .autoupdatingCurrent
    ) -> Int {
        let components = calendar.dateComponents([.hour, .minute], from: date)
        return min(1_439, max(0, (components.hour ?? 0) * 60 + (components.minute ?? 0)))
    }
}
```

- [ ] **Step 4: Implement the reminder invitation and illustration**

Create `OnboardingDailyReminderView` with this interface:

```swift
struct OnboardingDailyReminderView: View {
    let initialMinutes: Int
    let state: OnboardingReminderViewState
    let onSchedule: (Int) -> Void
    let onSkip: () -> Void
}
```

The view must:

- use the feature-local smooth gradient rather than `DottedGradientBackground`;
- initialize a `@State Date` through `OnboardingReminderTime.date(for:)`;
- present a compact wheel or compact-style `DatePicker` with `.hourAndMinute`;
- show localized daily copy, explicit weekly disclosure, and Settings reassurance;
- disable repeated actions while `.scheduling`;
- map `.resolved` outcomes to localized success/partial/denial/failure status;
- use a `ScrollView` plus safe-area padding so both actions remain reachable at accessibility sizes;
- keep both actions at least 44 points high;
- use `OnboardingReminderBellView`, with decorative layers hidden behind one accessibility label;
- use opacity instead of drift/scale when Reduce Motion is enabled.

Add 13 new `L10n` accessors and matching keys to all 14 localizations:

```text
onboarding.reminder.eyebrow
onboarding.reminder.title
onboarding.reminder.message
onboarding.reminder.time_label
onboarding.reminder.weekly_disclosure
onboarding.reminder.action
onboarding.reminder.not_now
onboarding.reminder.settings_hint
onboarding.reminder.scheduling
onboarding.reminder.success
onboarding.reminder.daily_only
onboarding.reminder.unavailable
onboarding.reminder.illustration.accessibility
```

English intent:

```text
A GENTLE ROUTINE
Make reflection a gentle habit
Choose when you'd like a small daily check-in.
Reminder time
You'll also receive one gentle weekly recap.
Set my reminder
Not now
You can change this anytime in Settings.
Setting your reminder…
Your reminder is ready.
Your daily reminder is ready. Weekly recap can be enabled in Settings.
You can enable reminders later in Settings.
A calm reminder bell
```

- [ ] **Step 5: Run view-model/localization tests and build**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingDefaultsTests","-only-testing:EveryDayEmojiTests/LocalizationResourceTests"]}'
xcodebuildmcp simulator build --prefer-xcodebuild --output text
```

Expected: all selected tests pass, every locale has matching keys, and the app builds.

- [ ] **Step 6: Commit the reminder presentation**

```bash
git add EveryDayEmoji/Onboarding EveryDayEmoji/Localization/L10n.swift EveryDayEmoji/*.lproj/Localizable.strings EveryDayEmojiTests/OnboardingDefaultsTests.swift EveryDayEmojiTests/LocalizationResourceTests.swift
git commit -m "Build onboarding reminder invitation"
```

---

### Task 4: Module Wiring, Analytics, Haptics, and Final Handoff

**Files:**
- Modify: `EveryDayEmoji/Onboarding/OnboardingModuleView.swift`
- Modify: `EveryDayEmoji/Analytics/AnalyticsModels.swift`
- Modify: `EveryDayEmojiTests/AnalyticsServiceTests.swift`
- Modify: `EveryDayEmojiTests/OnboardingFlowControllerTests.swift`

**Interfaces:**
- Consumes: `OnboardingReminderScheduling`, `OnboardingReminderViewState`, `.dailyReminder`, and existing onboarding callbacks.
- Produces: reminder screen composition, idempotent async scheduling, outcome analytics, success haptics, and correct source-aware handoff timing.

- [ ] **Step 1: Write failing privacy-safe analytics tests**

Add to `AnalyticsServiceTests`:

```swift
func testReminderAnalyticsContainSourceAndOutcomeWithoutSelectedTime() {
    let viewed = AnalyticsEvent.onboardingReminderViewed(source: .newUser)
    let resolved = AnalyticsEvent.onboardingReminderResolved(
        source: .newUser,
        outcome: .dailyOnly
    )

    XCTAssertEqual(viewed.name, "onboarding_reminder_viewed")
    XCTAssertEqual(viewed.payload.values, ["source": "new_user"])
    XCTAssertEqual(resolved.name, "onboarding_reminder_resolved")
    XCTAssertEqual(
        resolved.payload.values,
        ["source": "new_user", "outcome": "daily_only"]
    )
    XCTAssertNil(resolved.payload.values["time"])
}
```

- [ ] **Step 2: Run the analytics test and verify RED**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/AnalyticsServiceTests/testReminderAnalyticsContainSourceAndOutcomeWithoutSelectedTime"]}'
```

Expected: compile failure for the missing reminder analytics events.

- [ ] **Step 3: Add reminder analytics events**

Add event cases:

```swift
case onboardingReminderViewed(source: OnboardingPresentationSource)
case onboardingReminderPrimaryTapped(source: OnboardingPresentationSource)
case onboardingReminderSkipped(source: OnboardingPresentationSource)
case onboardingReminderResolved(
    source: OnboardingPresentationSource,
    outcome: OnboardingReminderSchedulingOutcome
)
```

Map them to these names and payloads:

```text
onboarding_reminder_viewed       { source }
onboarding_reminder_primary_tapped { source }
onboarding_reminder_skipped      { source }
onboarding_reminder_resolved     { source, outcome }
```

Do not add time, authorization status, mood, tag, or note properties.

- [ ] **Step 4: Inject and compose the scheduler in `OnboardingModuleView`**

Extend the initializer:

```swift
init(
    source: OnboardingPresentationSource,
    onPersistCompletion: @escaping () -> Void,
    onFinish: @escaping () -> Void,
    journalServiceBuilder: any EmotionJournalServiceBuilding = SwiftDataEmotionJournalServiceBuilder(),
    reminderScheduler: any OnboardingReminderScheduling = OnboardingReminderScheduler(),
    analyticsService: any AnalyticsTracking = DefaultAnalyticsServiceBuilder().makeService()
)
```

Add state:

```swift
@State private var reminderState: OnboardingReminderViewState = .idle
@State private var hasTrackedReminderView = false
```

Compose `.dailyReminder` with `OnboardingDailyReminderView` using
`DailyReminderScheduleConfiguration.stored().fixedTimeMinutes` as its initial value. Track the view once.

Implement primary scheduling as one guarded `Task`:

```swift
guard reminderState == .idle else { return }
reminderState = .scheduling
analyticsService.track(.onboardingReminderPrimaryTapped(source: flowController.source))
let outcome = await reminderScheduler.schedule(at: minutes)
reminderState = .resolved(outcome)
analyticsService.track(.onboardingReminderResolved(source: flowController.source, outcome: outcome))

if outcome.scheduledDailyReminder {
    HapticFeedback.playIfEnabled(.notification(.success), isEnabled: hapticsEnabled)
}

try? await ContinuousClock().sleep(
    for: reduceMotion ? .milliseconds(150) : .milliseconds(500)
)
analyticsService.track(.onboardingHandoffCompleted(source: flowController.source))
flowController.completeDailyReminder()
```

On skip, call `reminderScheduler.decline()`, track skip and handoff, and call
`completeDailyReminder()` immediately. Move `onboardingHandoffCompleted` out of the reflection callback:
new users track it only after the reminder step; Settings replay tracks it when post-save resolution
dismisses the replay.

Add `@AppStorage(AppPreferencesKeys.hapticsEnabled)` to honor the existing preference. Keep the replay
close overlay and ensure `.dailyReminder` is unreachable for replay.

- [ ] **Step 5: Run flow, scheduler, and analytics tests**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingFlowControllerTests","-only-testing:EveryDayEmojiTests/OnboardingReminderSchedulerTests","-only-testing:EveryDayEmojiTests/AnalyticsServiceTests"]}'
```

Expected: every selected test executes and passes with zero failures.

- [ ] **Step 6: Commit module integration**

```bash
git add EveryDayEmoji/Onboarding/OnboardingModuleView.swift EveryDayEmoji/Analytics/AnalyticsModels.swift EveryDayEmojiTests/AnalyticsServiceTests.swift EveryDayEmojiTests/OnboardingFlowControllerTests.swift
git commit -m "Connect onboarding reminder handoff"
```

---

### Task 5: Documentation and Integrated Verification

**Files:**
- Modify: `OVERVIEW.md`
- Modify only if verification exposes defects: onboarding/notification source or tests.

**Interfaces:**
- Consumes: completed reminder phase, scheduler, localized view, and existing Apple Health onboarding stack.
- Produces: source-of-truth documentation, full regression evidence, notification-request evidence, and final screenshots.

- [ ] **Step 1: Update `OVERVIEW.md`**

Replace the statement that reminders are entirely deferred. Document:

- the exact post-Health daily reminder invitation;
- compact 8:00 PM-default time picker;
- explicit weekly recap disclosure;
- daily fixed/all-days plus weekly stored/default scheduling;
- skip/denial/failure preference behavior;
- new-user-only behavior and replay exclusion;
- Reduce Motion, Dynamic Type, analytics privacy, and Settings fallback.

Keep App Lock deferred and keep notification Settings as the owner of advanced schedule controls.

- [ ] **Step 2: Run the focused onboarding and notification regression suite**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingFlowControllerTests","-only-testing:EveryDayEmojiTests/OnboardingReminderSchedulerTests","-only-testing:EveryDayEmojiTests/OnboardingDefaultsTests","-only-testing:EveryDayEmojiTests/EmotionSelectionViewModelTests","-only-testing:EveryDayEmojiTests/PostSaveFollowUpCoordinatorTests","-only-testing:EveryDayEmojiTests/HealthPostSavePromptControllerTests","-only-testing:EveryDayEmojiTests/DailyReminderScheduleConfigurationTests","-only-testing:EveryDayEmojiTests/AnalyticsServiceTests","-only-testing:EveryDayEmojiTests/LocalizationResourceTests"]}'
```

Expected: all selected tests execute and pass with zero failures or skips.

- [ ] **Step 3: Run the full simulator suite and build**

Run:

```bash
xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text
xcodebuildmcp simulator build --prefer-xcodebuild --output text
```

Expected: all tests pass and the build succeeds. If the configured iPhone 17 is unavailable, use the
nearest installed iPhone 17-family simulator by UUID and report that override rather than changing repo
defaults.

- [ ] **Step 4: Verify the real grant path on a clean simulator**

Run `xcodebuildmcp simulator build-and-run`, then use `snapshot-ui`, `tap`, `screenshot`, and the system
notification prompt to verify:

1. Welcome and first-reflection activation remain unchanged.
2. Dismissing Apple Health reveals the reminder invitation.
3. The compact picker starts at 8:00 PM on fresh defaults and remains editable.
4. The weekly recap disclosure is visible before authorization.
5. “Set my reminder” opens the real system notification prompt exactly once.
6. Granting schedules a daily request at the selected time and a weekly request at the stored/default
   schedule.
7. The final handoff enters the saved reflection in the normal app.

Inspect pending requests with a read-only simulator command or debugger evidence; do not infer them from
the preference toggles alone.

- [ ] **Step 5: Verify skip, replay, and accessibility variants**

On clean or isolated simulator states:

- “Not now” must hand off without a system prompt or pending daily/weekly requests.
- Settings replay must finish after the reflection/Health path and never show the reminder invitation.
- In dark appearance, Reduce Motion, and accessibility-extra-extra-extra-large Dynamic Type, all copy,
  picker controls, disclosure, and both actions remain reachable by scrolling and have meaningful labels.
- The reminder illustration is one accessibility element and decorative layers are hidden.

Capture the default reminder screen and one accessibility variant as screenshots.

- [ ] **Step 6: Review and commit the final branch**

Run:

```bash
git status --short
git diff --check origin/codex/apple-health-first-save-prompt...HEAD
git diff --stat origin/codex/apple-health-first-save-prompt...HEAD
```

Then commit documentation or verification-exposed fixes:

```bash
git add OVERVIEW.md EveryDayEmoji EveryDayEmojiTests docs/superpowers/plans/2026-08-20-onboarding-daily-reminder.md
git commit -m "Finish onboarding reminder integration"
```

Expected: clean worktree, no whitespace errors, no generated artifacts, and only onboarding,
notification-boundary, analytics, localization, test, plan, and documentation files in scope.
