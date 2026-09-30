> **ARCHIVED — historical planning document, not current guidance.**
> Written against a tooling setup that is not installed in this repo. Any instructions inside
> addressed to "agentic workers" (required sub-skills, subagent protocols) refer to that other
> system and do not apply here — treat them as a record of what was planned, not as directions.
> The live rules are in `AGENTS.md`; the map is in `CLAUDE.md`.

# Activation-First Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace the seven-step setup flow with one animated welcome screen that hands new users into the real reflection editor and completes onboarding after their first successful save.

**Architecture:** `OnboardingModuleView` becomes a small phase-driven container around the welcome page and the existing reflection module. A testable `OnboardingFlowController` owns transition/completion semantics, while a narrow `EmotionSelectionPresentationContext` changes first-use presentation without forking save logic. `ContentView` persists completion immediately after save but keeps onboarding mounted until any post-save Health prompt resolves.

**Tech Stack:** Swift 6, SwiftUI, SwiftData, Combine/ObservableObject, XCTest, XcodeBuildMCP, existing `MotionPolicy`, `HapticFeedback`, localization, and analytics infrastructure.

**Spec:** `docs/superpowers/specs/2026-08-20-activation-first-onboarding-design.md`

## Global Constraints

- Onboarding uses the real reflection persistence and post-save behavior; no demo editor or duplicate save path.
- The onboarding background is a smooth adaptive gradient with no dotted texture.
- New user onboarding contains one welcome page; notification, reminder, questionnaire, and App Lock requests are removed from the active flow.
- Existing questionnaire preference keys and legacy goal/cadence mapping remain readable for current users.
- All new user-visible strings use `L10n` and every supported localization.
- Motion honors Reduce Motion; haptics honor `AppPreferencesKeys.hapticsEnabled`.
- Interactive controls respect safe areas, Dynamic Type, and VoiceOver.
- Onboarding remains under `EveryDayEmoji/Onboarding/`; reusable reflection changes remain under `EveryDayEmoji/EmotionSelection/`.
- Update `OVERVIEW.md` alongside behavior and architecture changes.
- The branch remains stacked on `codex/apple-health-first-save-prompt` until PR #23 merges.

---

### Task 1: Testable Onboarding Flow State

**Files:**
- Create: `EveryDayEmoji/Onboarding/OnboardingFlowController.swift`
- Modify: `EveryDayEmoji/Onboarding/OnboardingModels.swift`
- Modify: `EveryDayEmoji/Onboarding/OnboardingDefaults.swift`
- Test: `EveryDayEmojiTests/OnboardingFlowControllerTests.swift`
- Test: `EveryDayEmojiTests/OnboardingDefaultsTests.swift`

**Interfaces:**
- Produces: `enum OnboardingPresentationSource { case newUser, settingsReplay }`
- Produces: `enum OnboardingPhase { case welcome, firstReflection, finishing }`
- Produces: `@MainActor final class OnboardingFlowController: ObservableObject`
- Produces: `startFirstReflection()`, `skip()`, `reflectionDidSave()`, and `postSavePresentationDidResolve()`.
- Produces: `OnboardingDefaults.welcomePage: OnboardingPageModel`.

- [x] **Step 1: Write failing controller and defaults tests**

```swift
@MainActor
func testNewUserSavePersistsCompletionBeforeVisualHandoff() {
    var persistenceCount = 0
    var finishCount = 0
    let controller = OnboardingFlowController(
        source: .newUser,
        persistCompletion: { persistenceCount += 1 },
        finish: { finishCount += 1 }
    )

    controller.startFirstReflection()
    controller.reflectionDidSave()

    XCTAssertEqual(controller.phase, .finishing)
    XCTAssertEqual(persistenceCount, 1)
    XCTAssertEqual(finishCount, 0)

    controller.postSavePresentationDidResolve()
    XCTAssertEqual(finishCount, 1)
}

@MainActor
func testReplaySkipFinishesWithoutPersistingNewUserCompletion() {
    var persistenceCount = 0
    var finishCount = 0
    let controller = OnboardingFlowController(
        source: .settingsReplay,
        persistCompletion: { persistenceCount += 1 },
        finish: { finishCount += 1 }
    )

    controller.skip()

    XCTAssertEqual(persistenceCount, 0)
    XCTAssertEqual(finishCount, 1)
}

func testDefaultsExposeOnlyTheActivationWelcomePage() {
    XCTAssertEqual(OnboardingDefaults.steps.count, 1)
    XCTAssertEqual(OnboardingDefaults.welcomePage.illustrationStyle, .moodOrbit)
}
```

- [x] **Step 2: Run the focused tests and verify the new API is missing**

Run: `xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingFlowControllerTests","-only-testing:EveryDayEmojiTests/OnboardingDefaultsTests"]}'`

Expected: FAIL because `OnboardingFlowController`, `OnboardingPresentationSource`, and `OnboardingDefaults.welcomePage` do not exist.

- [x] **Step 3: Implement the minimal flow state and single welcome model**

```swift
enum OnboardingPresentationSource: String, Equatable {
    case newUser = "new_user"
    case settingsReplay = "settings_replay"
}

enum OnboardingPhase: Equatable {
    case welcome
    case firstReflection
    case finishing
}

@MainActor
final class OnboardingFlowController: ObservableObject {
    @Published private(set) var phase: OnboardingPhase = .welcome
    let source: OnboardingPresentationSource

    private let persistCompletion: () -> Void
    private let finish: () -> Void
    private var hasPersistedCompletion = false
    private var hasFinished = false

    init(
        source: OnboardingPresentationSource,
        persistCompletion: @escaping () -> Void,
        finish: @escaping () -> Void
    ) {
        self.source = source
        self.persistCompletion = persistCompletion
        self.finish = finish
    }

    func startFirstReflection() { phase = .firstReflection }
    func skip() { persistCompletionIfNeeded(); finishIfNeeded() }
    func reflectionDidSave() { phase = .finishing; persistCompletionIfNeeded() }
    func postSavePresentationDidResolve() { finishIfNeeded() }
}
```

Replace the old question/action step model with a single `.moodOrbit` welcome page while retaining `OnboardingQuestionnaireGoal` and `OnboardingQuestionnaireCadence` mapping types for legacy consumers.

- [x] **Step 4: Run focused tests and verify they pass**

Run the Task 1 command again.

Expected: all `OnboardingFlowControllerTests` and `OnboardingDefaultsTests` pass.

- [x] **Step 5: Commit the state boundary**

```bash
git add EveryDayEmoji/Onboarding/OnboardingFlowController.swift EveryDayEmoji/Onboarding/OnboardingModels.swift EveryDayEmoji/Onboarding/OnboardingDefaults.swift EveryDayEmojiTests/OnboardingFlowControllerTests.swift EveryDayEmojiTests/OnboardingDefaultsTests.swift
git commit -m "Add activation onboarding flow state"
```

---

### Task 2: Welcome Screen, Smooth Background, and Motion

**Files:**
- Modify: `EveryDayEmoji/Onboarding/OnboardingPageView.swift`
- Modify: `EveryDayEmoji/Onboarding/OnboardingIllustrations.swift`
- Modify: `EveryDayEmoji/Onboarding/OnboardingModuleView.swift`
- Test: `EveryDayEmojiTests/OnboardingDefaultsTests.swift`

**Interfaces:**
- Consumes: `OnboardingDefaults.welcomePage`, `OnboardingFlowController`, and `.moodOrbit` from Task 1.
- Produces: `OnboardingGradientBackground` scoped to the onboarding module.
- Produces: `OnboardingMoodOrbitView` with a single VoiceOver summary.
- Produces: `OnboardingModuleView(source:onPersistCompletion:onFinish:)`.

- [x] **Step 1: Add failing structural assertions for welcome content**

```swift
func testWelcomePageUsesActivationCopyAndNoPagerAction() {
    let page = OnboardingDefaults.welcomePage
    XCTAssertEqual(page.sectionTitle, L10n.onboardingWelcomeSection)
    XCTAssertEqual(page.title, L10n.onboardingWelcomeTitle)
    XCTAssertEqual(page.actionTitle, L10n.onboardingWelcomeAction)
    XCTAssertEqual(page.illustrationStyle, .moodOrbit)
}
```

- [x] **Step 2: Run `OnboardingDefaultsTests` and verify it fails on missing localized accessors**

Run: `xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingDefaultsTests"]}'`

Expected: FAIL because the activation copy accessors do not exist yet.

- [x] **Step 3: Build the welcome composition and phase transition**

Implement `OnboardingPageView` as one safe-area-aware page with:

```swift
ZStack {
    OnboardingGradientBackground()
    VStack(spacing: 0) {
        welcomeCopy
        OnboardingMoodOrbitView(animationProfile: page.animationProfile)
        Spacer(minLength: 20)
        PrimaryCapsuleButton(title: page.actionTitle, showsTrailingIndicator: true, action: onPrimaryTap)
        Button(L10n.onboardingWelcomeLater, action: onSkipTap)
    }
}
```

`OnboardingGradientBackground` fills a `LinearGradient(colors: AppTheme.backgroundColors, startPoint: .topLeading, endPoint: .bottomTrailing)` and does not instantiate `DottedGradientBackground` or `AppScreenBackground`.

Build the hero from one 72-point central emoji and four 28-point orbiting emoji surfaces. Use existing glass colors/strokes, hide the four decorative surfaces from accessibility, and expose the group as `L10n.onboardingWelcomeMoodPreviewAccessibility`.

Drive the ambient offsets with existing `MotionPolicy`. With Reduce Motion, render all elements at their resting positions. Trigger a light impact through `HapticFeedback.playIfEnabled(.impact(.light), isEnabled: hapticsEnabled)` before moving to `.firstReflection`.

Switch phases inside `OnboardingModuleView` with an asymmetric trailing-edge/opacity transition; use opacity only when Reduce Motion is enabled.

- [x] **Step 4: Run the focused default tests**

Run the Task 2 command again.

Expected: `OnboardingDefaultsTests` pass.

- [x] **Step 5: Commit the welcome experience**

```bash
git add EveryDayEmoji/Onboarding/OnboardingPageView.swift EveryDayEmoji/Onboarding/OnboardingIllustrations.swift EveryDayEmoji/Onboarding/OnboardingModuleView.swift EveryDayEmojiTests/OnboardingDefaultsTests.swift
git commit -m "Build activation-first onboarding welcome"
```

---

### Task 3: First-Reflection Presentation and Post-Save Resolution

**Files:**
- Modify: `EveryDayEmoji/EmotionSelection/EmotionSelectionModuleView.swift`
- Modify: `EveryDayEmoji/EmotionSelection/EmotionSelectionEmojiPickerSection.swift`
- Modify: `EveryDayEmoji/HealthIntegration/HealthPostSavePromptController.swift`
- Test: `EveryDayEmojiTests/EmotionSelectionViewModelTests.swift`
- Test: `EveryDayEmojiTests/HealthPostSavePromptControllerTests.swift`

**Interfaces:**
- Produces: `enum EmotionSelectionPresentationContext { case standard, firstReflection }`.
- Produces: `EmotionSelectionModuleHostView(serviceBuilder:analyticsService:loggingDate:presentationContext:onReflectionSaved:onPostSavePresentationResolved:)`, with default `.standard` context and empty callbacks.
- Produces: a module-local `isAwaitingPostSavePresentationResolution` guard.
- Consumes: existing Health prompt `isPresented` and widget prompt `shouldShowWidgetPrompt` state.

- [x] **Step 1: Add failing presentation-context and resolution tests**

Add pure computed-policy coverage rather than screenshot-testing private SwiftUI nodes:

```swift
func testFirstReflectionPresentationUsesFocusedCopyAndHidesManagement() {
    XCTAssertEqual(EmotionSelectionPresentationContext.firstReflection.title, L10n.onboardingFirstReflectionTitle)
    XCTAssertFalse(EmotionSelectionPresentationContext.firstReflection.showsMoodManagement)
    XCTAssertTrue(EmotionSelectionPresentationContext.standard.showsMoodManagement)
}
```

Extend `HealthPostSavePromptControllerTests` to verify that `isPresented` changes from true to false on both dismiss and successful export so the module can resolve the handoff reliably.

- [x] **Step 2: Run focused reflection and Health tests and verify failure**

Run: `xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/EmotionSelectionViewModelTests","-only-testing:EveryDayEmojiTests/HealthPostSavePromptControllerTests"]}'`

Expected: FAIL because `EmotionSelectionPresentationContext` does not exist.

- [x] **Step 3: Add the narrow presentation context and resolution callbacks**

```swift
enum EmotionSelectionPresentationContext: Equatable {
    case standard
    case firstReflection

    var title: String {
        self == .firstReflection ? L10n.onboardingFirstReflectionTitle : L10n.emotionSelectionTitle
    }

    var showsMoodManagement: Bool { self == .standard }
}
```

Pass the context from the host into the module. Use it only for the title and `showsManageButton`/add-custom-mood affordances. Keep the same view model, save method, tags, note, haptics, and saved-state rendering.

After a successful `saveReflection()`:

1. Call `onReflectionSaved()`.
2. If neither Health nor widget presentation is active, call `onPostSavePresentationResolved()` after the saved-state animation transaction yields.
3. Otherwise set `isAwaitingPostSavePresentationResolution = true`.
4. In `EmotionSelectionSheetsModifier`, observe the active post-save sheet state. When both are false and the awaiting binding is true, clear the guard and invoke `onPostSavePresentationResolved()` exactly once.

- [x] **Step 4: Run focused reflection and Health tests**

Run the Task 3 command again.

Expected: all focused tests pass and existing standard presentation assertions remain unchanged.

- [x] **Step 5: Commit the reusable reflection boundary**

```bash
git add EveryDayEmoji/EmotionSelection/EmotionSelectionModuleView.swift EveryDayEmoji/EmotionSelection/EmotionSelectionEmojiPickerSection.swift EveryDayEmoji/HealthIntegration/HealthPostSavePromptController.swift EveryDayEmojiTests/EmotionSelectionViewModelTests.swift EveryDayEmojiTests/HealthPostSavePromptControllerTests.swift
git commit -m "Support focused first-reflection presentation"
```

---

### Task 4: Root Completion Handoff and Settings Replay

**Files:**
- Modify: `EveryDayEmoji/ContentView.swift`
- Modify: `EveryDayEmoji/Settings/AboutSettingsView.swift`
- Modify: `EveryDayEmoji/Onboarding/OnboardingModuleView.swift`
- Test: `EveryDayEmojiTests/OnboardingFlowControllerTests.swift`

**Interfaces:**
- Consumes: flow controller and reflection callbacks from Tasks 1 and 3.
- Produces: `ContentView` in-memory `keepsOnboardingMountedDuringHandoff` state.
- Produces: replay `fullScreenCover` that never mutates `didFinishOnboarding`.

- [x] **Step 1: Add failing idempotence and replay tests**

```swift
@MainActor
func testRepeatedSaveAndResolutionCallbacksCompleteExactlyOnce() {
    var persistenceCount = 0
    var finishCount = 0
    let controller = OnboardingFlowController(
        source: .newUser,
        persistCompletion: { persistenceCount += 1 },
        finish: { finishCount += 1 }
    )

    controller.reflectionDidSave()
    controller.reflectionDidSave()
    controller.postSavePresentationDidResolve()
    controller.postSavePresentationDidResolve()

    XCTAssertEqual(persistenceCount, 1)
    XCTAssertEqual(finishCount, 1)
}
```

- [x] **Step 2: Run `OnboardingFlowControllerTests` and verify the idempotence test fails until guards are complete**

Run: `xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingFlowControllerTests"]}'`

Expected: FAIL if duplicate completion is not yet guarded.

- [x] **Step 3: Wire new-user composition and replay presentation**

In `ContentView`, show onboarding when either the completion preference is false or the in-memory handoff flag is true:

```swift
if didFinishOnboarding == false || keepsOnboardingMountedDuringHandoff {
    OnboardingModuleView(
        source: .newUser,
        onPersistCompletion: {
            keepsOnboardingMountedDuringHandoff = true
            guard didFinishOnboarding == false else { return }
            analyticsService.track(.onboardingCompleted(source: .newUser))
            didFinishOnboarding = true
        },
        onFinish: { keepsOnboardingMountedDuringHandoff = false },
        journalServiceBuilder: journalServiceBuilder,
        analyticsService: analyticsService
    )
} else {
    AppTabContainerView(
        journalServiceBuilder: journalServiceBuilder,
        analyticsService: analyticsService
    )
}
```

In `AboutSettingsView`, replace `didFinishOnboarding = false` with `isOnboardingReplayPresented = true`, then present `OnboardingModuleView(source: .settingsReplay, onPersistCompletion: {}, onFinish: dismiss)` in a full-screen cover. Keep the confirmation alert but make replay non-destructive.

- [x] **Step 4: Run flow tests and build the app**

Run the Task 4 test command.

Run: `xcodebuildmcp simulator build --prefer-xcodebuild --output text`

Expected: tests pass and the app compiles with the repository defaults.

- [x] **Step 5: Commit root and replay behavior**

```bash
git add EveryDayEmoji/ContentView.swift EveryDayEmoji/Settings/AboutSettingsView.swift EveryDayEmoji/Onboarding/OnboardingModuleView.swift EveryDayEmojiTests/OnboardingFlowControllerTests.swift
git commit -m "Connect onboarding completion and replay"
```

---

### Task 5: Analytics, Localization, Legacy Cleanup, and Documentation

**Files:**
- Modify: `EveryDayEmoji/Analytics/AnalyticsModels.swift`
- Modify: `EveryDayEmoji/Localization/L10n.swift`
- Modify: `EveryDayEmoji/*.lproj/Localizable.strings`
- Modify: `EveryDayEmoji/Onboarding/OnboardingQuestionnaire.swift`
- Delete: `EveryDayEmoji/Onboarding/OnboardingQuestionnairePageView.swift`
- Modify: `EveryDayEmojiTests/AnalyticsServiceTests.swift`
- Modify: `EveryDayEmojiTests/LocalizationResourceTests.swift`
- Modify: `OVERVIEW.md`

**Interfaces:**
- Produces: source-aware onboarding funnel events with `new_user` and `settings_replay` values.
- Preserves: `OnboardingQuestionnaireGoal` and `OnboardingQuestionnaireCadence` for legacy stored values.

- [x] **Step 1: Add failing analytics and localization coverage**

```swift
func testActivationOnboardingEventsContainSourceWithoutReflectionContent() {
    let event = AnalyticsEvent.onboardingFirstReflectionStarted(source: .newUser)
    XCTAssertEqual(event.name, "onboarding_first_reflection_started")
    XCTAssertEqual(event.payload.values["source"], "new_user")
    XCTAssertNil(event.payload.values["emotion_id"])
}
```

Add the new welcome/first-reflection keys to the localization required-key fixture so parity fails until every locale is updated.

- [x] **Step 2: Run analytics and localization tests and verify failure**

Run: `xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/AnalyticsServiceTests","-only-testing:EveryDayEmojiTests/LocalizationResourceTests","-only-testing:EveryDayEmojiTests/DailyReminderScheduleConfigurationTests","-only-testing:EveryDayEmojiTests/MoodGoalsViewModelTests"]}'`

Expected: FAIL on missing activation events and localization keys; legacy mapping tests continue to compile.

- [x] **Step 3: Add source-aware events and all localized copy**

Add:

```swift
case onboardingFirstReflectionStarted(source: OnboardingPresentationSource)
case onboardingFirstReflectionSaved(source: OnboardingPresentationSource, elapsedSeconds: Int)
case onboardingHandoffCompleted(source: OnboardingPresentationSource)
case onboardingCompleted(source: OnboardingPresentationSource)
```

Payloads contain only `source` and a nonnegative integer duration where applicable. Never include mood, tags, or note content.

Add localized keys for the welcome eyebrow, title, subtitle, CTA, later action, hero accessibility summary, and first-reflection title across all supported locales. Remove obsolete questionnaire page composition and unreferenced setup copy/accessors while retaining legacy enums and preference consumers.

Update `OVERVIEW.md` to describe the one-screen activation flow, real first reflection, post-save Health handoff, deferred reminder/App Lock setup, settings replay semantics, smooth no-dot background, and motion/accessibility behavior.

- [x] **Step 4: Run the focused analytics/localization/legacy tests**

Run the Task 5 command again.

Expected: all focused tests pass, every locale has the same required keys, and legacy recommendation tests remain green.

- [x] **Step 5: Commit copy, analytics, cleanup, and docs**

```bash
git add EveryDayEmoji/Analytics/AnalyticsModels.swift EveryDayEmoji/Localization/L10n.swift EveryDayEmoji/*.lproj/Localizable.strings EveryDayEmoji/Onboarding/OnboardingQuestionnaire.swift EveryDayEmoji/Onboarding/OnboardingQuestionnairePageView.swift EveryDayEmojiTests/AnalyticsServiceTests.swift EveryDayEmojiTests/LocalizationResourceTests.swift OVERVIEW.md
git commit -m "Finish activation onboarding integration"
```

---

### Task 6: Integrated Verification and Visual Evidence

**Files:**
- Modify only if verification exposes an onboarding-scoped defect.

**Interfaces:**
- Consumes the completed activation flow from Tasks 1–5.
- Produces build, test, accessibility, and screenshot evidence for handoff.

- [x] **Step 1: Run the focused onboarding regression suite**

Run: `xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text --json '{"extraArgs":["-only-testing:EveryDayEmojiTests/OnboardingFlowControllerTests","-only-testing:EveryDayEmojiTests/OnboardingDefaultsTests","-only-testing:EveryDayEmojiTests/EmotionSelectionViewModelTests","-only-testing:EveryDayEmojiTests/PostSaveFollowUpCoordinatorTests","-only-testing:EveryDayEmojiTests/HealthPostSavePromptControllerTests","-only-testing:EveryDayEmojiTests/AnalyticsServiceTests","-only-testing:EveryDayEmojiTests/LocalizationResourceTests","-only-testing:EveryDayEmojiTests/DailyReminderScheduleConfigurationTests","-only-testing:EveryDayEmojiTests/MoodGoalsViewModelTests"]}'`

Expected: all selected tests execute and pass with zero failures.

- [x] **Step 2: Run the full simulator test suite**

Run: `xcodebuildmcp simulator test --prefer-xcodebuild --progress false --output text`

Expected: all tests execute and pass. If the host again reports `errno=28`, preserve the focused result and report the environment failure separately from product assertions.

- [x] **Step 3: Build and run the real first-launch flow**

Run: `xcodebuildmcp simulator build-and-run`

Use `snapshot-ui`, `tap`, and `screenshot` to capture:

1. smooth-gradient welcome with all actions visible;
2. first-reflection editor with management affordances hidden;
3. selected mood with enabled save CTA;
4. saved reflection and contextual Apple Health prompt;
5. post-dismissal normal app handoff.

- [x] **Step 4: Verify accessibility variants**

Repeat the welcome/editor inspection with Reduce Motion enabled, dark appearance, and large Dynamic Type. Confirm the mood-orbit hero is one accessibility element, decorative emojis are hidden, and no action clips or falls outside the safe area.

- [x] **Step 5: Review the final branch diff**

Run:

```bash
git status --short
git diff --check origin/codex/apple-health-first-save-prompt...HEAD
git diff --stat origin/codex/apple-health-first-save-prompt...HEAD
```

Expected: no uncommitted source changes, no whitespace errors, and only onboarding/reflection-boundary/localization/analytics/test/documentation files in scope.
