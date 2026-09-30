> **ARCHIVED — historical planning document, not current guidance.**
> Written against a tooling setup that is not installed in this repo. Any instructions inside
> addressed to "agentic workers" (required sub-skills, subagent protocols) refer to that other
> system and do not apply here — treat them as a record of what was planned, not as directions.
> The live rules are in `AGENTS.md`; the map is in `CLAUDE.md`.

# Activation Onboarding & Monetization — Fix List

Review of the activation-first onboarding (`codex/activation-first-onboarding`, PR #25), the
daily-reminder step (`codex/apple-health-first-save-prompt`, PR #26) as merged to `main` at `1cabd46`,
and the acquisition → activation → subscription funnel those two feed.

- **Written:** 2026-08-21
- **Specs reviewed:** `docs/superpowers/specs/2026-08-20-activation-first-onboarding-design.md`,
  `docs/superpowers/specs/2026-08-20-onboarding-daily-reminder-design.md`
- **Also reviewed for §3:** `PREMIUM_FEATURES.md`, `EveryDayEmoji/Subscription/`, `SK1.storekit`,
  `EveryDayEmoji/Insights/InsightsView.swift`, `screenshots-generator/src/app/page.tsx`, `docs/index.html`
- **Evidence:** source read of `EveryDayEmoji/Onboarding/` + handoff sites, and a runtime pass on an
  **erased** iPhone 17 Pro simulator (`Debug`, build succeeded in 25s) covering welcome → first
  reflection → Health prompt → reminder invitation → app → Insights paywall gate, at default and AX5
  Dynamic Type.
- **Not run:** the XCTest suite. XcodeBuildMCP was not connected in the review session, so the build
  used the fallback simulator build tool rather than the `AGENTS.md` default toolchain.

The flow as built is sound and the specs were followed closely. Nothing in §1–2 argues against the
activation-first bet. §3 is where that bet meets the paywall, and it is where the money is.

---

## 1. Fix list

Severity: **P1** = fix before the next release · **P2** = fix during 1.5 · **P3** = cleanup.
Effort follows `BACKLOG.md`: **S** ≈ ≤1 day.

**Model** is the recommended model to hand the item to. The rule of thumb used throughout:

- **Haiku 4.5** — the change is localized and fully specified here; no judgment left to make.
- **Sonnet 5** — real code work across a few files, or a layout/state bug needing diagnosis, but the
  target behaviour is unambiguous.
- **Opus 5** — the item requires product judgment, cross-system reasoning, or copy/pricing decisions
  where the *right answer is not stated* and getting it wrong is expensive.

| ID | Title | Area | Sev | Effort | Model |
| --- | --- | --- | --- | --- | --- |
| OB-1 | ✅ **Fixed** — reminder scheduler pushed `false` to iCloud and could disable another device's reminders | correctness | **P1** | S | Opus 5 |
| OB-2 | A cloud import of `didFinishOnboarding` mid-onboarding tears down the unsaved first reflection | correctness | **P1** | S | Opus 5 |
| OB-3 | Disabled "Save Reflection" is transparent and collides with the tag chips | visual | **P1** | S | Sonnet 5 |
| OB-5 | Saved reflection is never seen — the Health sheet covers it instantly | UX | **P1** | S | Sonnet 5 |
| OB-6 | Permission denial gets no readable acknowledgement (~500 ms) and no retry | UX | **P1** | S | Sonnet 5 |
| OB-7 | `.finishing → .dailyReminder` is not wrapped in `withAnimation`, so the transition hard-cuts | motion | **P2** | S | Haiku 4.5 |
| OB-8 | Long-press customization is live during the first reflection, and the copy advertises it | UX | **P2** | S | Sonnet 5 |
| OB-9 | Onboarding eyebrows truncate at accessibility text sizes | a11y | **P2** | S | Haiku 4.5 |
| OB-10 | Welcome CTA falls below the fold at AX sizes with no scroll affordance | a11y | **P2** | S | Sonnet 5 |
| OB-11 | Secondary-button tap targets are likely text-sized, not 44 pt | a11y | **P2** | S | Sonnet 5 |
| OB-12 | Reminder time picker reads as a label, not a control | UX | **P2** | S | Opus 5 |
| OB-13 | `PrimaryCapsuleButton` has no disabled appearance | visual | **P3** | S | Haiku 4.5 |
| OB-14 | `onboarding_completed` counts skippers; handoff event missing on the skip path | analytics | **P2** | S | Opus 5 |
| OB-15 | Dead code left by the redesign | cleanup | **P3** | S | Haiku 4.5 |
| OB-16 | Two new Swift 6 concurrency warnings in `OnboardingReminderScheduler` | debt | **P3** | S | Haiku 4.5 |
| OB-17 | Today tab observed hung on "Checking today's reflection" after the skip path | correctness | **P2** | S | Sonnet 5 |

### OB-17 · Today tab hung after skip · **P2** · ✅ root-caused — see MON-1

On a freshly erased simulator with no iCloud account, taking "Maybe later" from the welcome screen
landed on a Today tab that spun on "Checking today's reflection" indefinitely, with the tab bar
unresponsive. A relaunch recovered.

**Resolved during the MON-1 investigation:** this is not a CloudKit/SwiftData container problem and has
nothing to do with the skip path. It is the main-actor freeze in `SyncPreferencesCoordinator.syncLocalChangesToCloud()`.
Fixing MON-1 fixes this. Keep this entry only as the regression test to run afterwards: fresh install,
iCloud signed out, skip path, confirm the Today tab resolves.

---

### OB-1 · Reminder scheduler pushes `false` to iCloud · **P1** · ✅ FIXED 2026-08-21

Fixed on `fix/ob-1-onboarding-reminder-preference-clobber`. The rule the scheduler now documents and
enforces: **onboarding may only ever turn notification preferences on.**

- Dropped the `setEnabled(daily: false, weekly: false)` that opened `schedule()`. It made even the
  fully successful path write `false` first, and `UserDefaults.didChangeNotification` pushes that
  transient value to iCloud before the `true` lands.
- `decline()` is now a documented no-op. "Not now" never requested authorization and never scheduled
  anything, so for a new user there is nothing to undo — and for a returning user the old `false`
  was destroying real settings.
- Both `.dailyOnly` exits now leave `weeklySummaryEnabled` unwritten. Daily succeeded, so
  notifications are authorized, and leaving the preference alone lets `refreshWeeklySummaryScheduleIfNeeded`
  retry on the next scene activation — the old `false` prevented that self-heal.
- Removed the now-unused `setEnabled` helper.

Tests: 5 added, 3 rewritten (they asserted the bug), 12 in the file, **434 in the suite, 0 failures**
on an iOS 26.5 simulator. The regression guard worth knowing about is
`testSuccessNeverWritesFalseBeforeScheduling`, which samples `UserDefaults.didChangeNotification` —
the same signal `SyncPreferencesCoordinator` uses — so it catches transient writes that a
before/after assertion cannot see.

Tests assert on `persistentDomain(forName:)` rather than `bool(forKey:)`, because
`weeklySummaryEnabled` has a registered default of `true` and `object(forKey:)` resolves it; only the
persistent domain distinguishes "written" from "defaulted".

**Known, accepted consequence.** A brand-new user who taps "Not now" (or is denied permission) leaves
`weeklySummaryEnabled` at its registered default `true`, so the Settings toggle reads ON while nothing
is scheduled. This is not a new state — it is exactly what a welcome-screen skipper has always had,
and `refreshWeeklySummaryScheduleIfAuthorized` no-ops when unauthorized, so no notification or prompt
results. Worth its own item; it is not OB-1's to fix, and fixing it by writing `false` is the bug.

**Original report follows.**


`OnboardingReminderScheduler.schedule()` opens with `setEnabled(daily: false, weekly: false)`
(`OnboardingReminderScheduler.swift:34`), and `decline()` does the same (`:71`). Both
`settings.dailyReminderEnabled` and `settings.weeklySummaryEnabled` are in
`AppPreferencesKeys.syncedPreferenceDescriptors`, and `SyncPreferencesCoordinator.syncLocalChangesToCloud`
pushes any local value that differs from the cloud value. `dailyReminderEnabled` has no registered
default, so the "don't seed iCloud with a fallback this device never chose" guard does not cover it.

**Failure path.** A user reinstalls, or installs on a second device. `didFinishOnboarding` lives in
NSUbiquitousKeyValueStore and has not arrived yet, so onboarding shows. They tap **Not now** →
`false` is written locally → pushed to iCloud → the reminder on their other device silently stops.

**This is not theoretical.** During this review, uninstalling and reinstalling the app on the
simulator produced a first launch whose defaults already read:

```
"app.didFinishOnboarding" => true
"settings.dailyReminderEnabled" => true
"settings.dailyReminderFixedTimeMinutes" => 840
"onboarding.questionnaire.cadence" => "weekdays"
```

All of it restored from KVS after the container was wiped. The import won that race; OB-1 is what
happens when it loses.

**Fix.** Do not pre-clear in `schedule()` — write `dailyReminderEnabled`/`weeklySummaryEnabled` only
on the branches that actually succeed. Have `decline()` write nothing, or record the decline in a
device-local key that is not in `syncedPreferenceDescriptors`.

### OB-2 · Cloud import can destroy an in-progress first reflection · **P1**

`ContentView` holds `didFinishOnboarding` as `@AppStorage` over `UserDefaults.standard`, which is the
same store `SyncPreferencesCoordinator` writes to when `didChangeExternallyNotification` fires. Same
race as OB-1: if the cloud value lands while the user is picking a mood or typing their first note,
`showsOnboarding` flips to `false` and the editor is unmounted with the entry unsaved.
`keepsOnboardingMountedDuringHandoff` only guards the window *after* a save.

**Fix.** Latch the onboarding container for the lifetime of the session once it has been presented,
rather than re-deriving it from the synced flag on every change. A cloud import should not be able to
change the root while onboarding owns the screen.

### OB-3 · Disabled save button is transparent over the tag chips · **P1**

Before a mood is picked — the state every new user lands in — the pinned "Save Reflection" button is
a semi-transparent blue slab in a `safeAreaInset`, with the tag chips scrolling visibly *through* it.
"Save Reflection" and the "Creative" chip render on top of each other and neither is legible.

This is the single most important screen in the funnel, and it looks broken for the first several
seconds of it. Reproduced in both light and dark appearance.

**Fix.** Give the disabled state an opaque or materially-backed treatment instead of reduced opacity
over scrolling content, or put a background/blur behind the inset bar.

### OB-5 · The user never sees their saved reflection · **P1**

The activation-first spec says to "keep the current editor mounted long enough to display its saved
state" and describes a deliberate celebration: the emoji settles into the saved card, then a
checkmark. In practice the Apple Health sheet presents *immediately* on save and covers all of it.

So the sequence a new user actually experiences is: do the thing → **ask** → **ask** → land in the
app. The reward for the activation action is replaced by two requests, and the payoff moment the
motion spec designed is never rendered.

**Fix.** Hold the saved state for a beat (~700–900 ms, or until the celebration animation completes)
before presenting the Health prompt.

### OB-6 · Denial gets no acknowledgement and no retry · **P1**

`OnboardingReminderCoordinator` sleeps a fixed 150/500 ms after *any* outcome, then hands off. On
`permissionDenied` the status line "You can enable reminders later in Settings." is on screen for
half a second. In the runtime pass, tapping **Don't Allow** went straight to the app with no visible
acknowledgement at all — the `.accessibilityAnnouncement` is cut off by the view change too.

`hasAcceptedAction` also latches, so a transient `failed` leaves no way to retry.

**Fix.** Make the delay outcome-dependent — keep ~500 ms for `scheduled`, hold ~2 s (or require a
tap) for `dailyOnly`, `permissionDenied` and `failed`. Consider allowing a retry on `failed`.

### OB-7 · The reminder transition hard-cuts · **P2**

The welcome → editor phase change is wrapped in `withAnimation(phaseAnimation)`
(`OnboardingModuleView.swift:85`), but the `onPostSavePresentationResolved` closure at
`OnboardingModuleView.swift:113` calls `postSavePresentationDidResolve()` bare. The `@Published`
change lands outside a transaction, so the `.transition(editorTransition)` declared on the reminder
view never plays. Confirmed at runtime: the reminder screen appears with no animation.

### OB-8 · Long-press customization is live during the first reflection · **P2**

`onLongPressEmotion` (`EmotionSelectionModuleView.swift:316`) is **not** gated by
`presentationContext`. Long-pressing a mood during onboarding opens the full "Personalize Calm"
sheet — suggestion browser, custom emoji keyboard, the lot. The header copy actively invites it:
"Long press an emoji to customize it".

No paywall is reachable (both premium gates live behind the hidden "Add mood" and "Edit Tags"
buttons, and emoji overrides are free), so the spec's paywall claim holds. But on the screen whose
only job is "tap one emoji and save", the secondary copy teaches a customization gesture instead.

**Fix.** Gate `onLongPressEmotion` on `presentationContext.showsMoodManagement`, and swap the hint
for first-reflection-appropriate copy (or drop it).

### OB-9 · Eyebrows truncate at accessibility sizes · **P2**

At AX5, "A MOMENT FOR YOU" renders as "A MOMENT FO…". The title and subtitle in
`OnboardingPageView.welcomeCopy` both carry `.fixedSize(horizontal: false, vertical: true)`; the
`sectionTitle` `Text` does not. `OnboardingDailyReminderView.copy` has the same omission on its
eyebrow. One-line fix in both files.

### OB-10 · Welcome CTA falls below the fold at AX sizes · **P2**

At AX5 the primary CTA is off-screen on first paint. It *is* reachable — the `ScrollView` with
`frame(minHeight:)` does its job and nothing clips — but there is no affordance indicating more
content below, on the screen whose entire purpose is getting that button tapped.

**Fix.** Pin the action area to the bottom as a `safeAreaInset` so it stays visible while the copy
and hero scroll behind it.

### OB-11 · Secondary tap targets are likely text-sized · **P2**

"Maybe later" (`OnboardingPageView.swift:109`) and "Not now"
(`OnboardingDailyReminderView.swift:141`) apply `.frame(minHeight: 44).contentShape(Rectangle())` to
the **Button**, not inside its label. Everywhere else in the codebase — `SettingsNavigationRow`,
`DayCellView`, `GoalsSettingsView` — the modifiers go inside the label. As written, the hit region is
probably just the text bounds, which makes `OnboardingAccessibilityLayout.minimumTapTargetHeight` a
statement of intent rather than a guarantee. **Verify with Accessibility Inspector before fixing.**

### OB-12 · The reminder time picker reads as a label · **P2**

The compact `DatePicker` renders as a small grey `20:00` pill, left-aligned in a card with a large
empty right side. It is the only interactive control on the screen and it looks inert. A user can
easily accept the default without realising the time was theirs to choose — which matters, because
the default determines whether the reminder ever fits their day.

**Fix.** Give the row a label-plus-value layout with the value right-aligned and visibly tappable,
or use a segmented set of common times with a custom option.

### OB-13 · No disabled appearance on the primary capsule · **P3**

`PrimaryCapsulePressStyle` only handles `isPressed`. After the reminder resolves, `actionsDisabled`
is true but the title reverts from "Setting your reminder…" to "Set my reminder" and the button still
looks live. (The secondary "Not now" does dim correctly, so the two disagree.) Add an
`@Environment(\.isEnabled)`-driven opacity.

### OB-14 · Analytics will misread the funnel · **P2**

`onboardingCompleted` fires from `ContentView.persistOnboardingCompletion`, which is reached by both
**save** and **skip** — so it is not an activation metric. The spec's primary success measure maps to
`onboarding_first_reflection_saved` instead. Also: `onboardingHandoffCompleted` never fires on the
welcome-skip path, and `onboardingSkipped` doubles as the replay-close event (source-tagged, so
filterable, but easy to misread).

**Fix.** Document the intended funnel definitions alongside the events, or rename
`onboarding_completed` to something that reflects what it measures.

### OB-15 · Dead code from the redesign · **P3**

- `PremiumFeature.onboarding` — the paywall source is now referenced only from a `#Preview`.
  Onboarding cannot reach a paywall by design, so the case should go.
- `OnboardingQuestionnaireCadence.reminderWeekdayMask` and `.shouldAutoEnableDailyReminder` — now
  referenced only by tests; the new scheduler hardcodes `.allDays`. The `goal` half of
  `OnboardingQuestionnaire.swift` is still live (`MoodGoalModels`, paywall badge) and must stay.
- Cosmetic: `onboarding.reminder.eyebrow` is stored pre-uppercased in all 14 locales *and* the view
  applies `.textCase(.uppercase)`, while `onboarding.welcome.section` is stored in sentence case.
  Harmless today, inconsistent.

### OB-16 · New concurrency warnings · **P3**

The build emits 77 warnings, which `AGENTS.md` treats as existing project debt — but two of them are
new, from this work: `OnboardingReminderScheduler.swift:26` calls a main-actor-isolated
`makeService()` and initializer from a synchronous nonisolated context, twice.

---

## 2. UX analysis

### What the redesign gets right

**The core bet is correctly implemented.** The user reaches the real editor in one tap and their
first save is a real reflection, not a demo. The old flow asked seven screens' worth of questions
before showing anything; this one asks nothing. That is the right trade for a product whose entire
positioning is "logging takes one tap".

**The welcome screen is genuinely calm.** One idea, one action, no progress dots, no carousel, a
restrained hero. It sets the emotional register the product is selling, which matters more here than
in most categories.

**Permission asks are honest.** The Health sheet leads with "Your notes stay in Emojily. Emojily never
reads your Health data." The reminder screen discloses the weekly recap up front rather than burying
it, and both carry a "you can change this in Settings" reassurance. This is better than most apps in
the category and worth protecting.

**Both dead ends are real exits.** "Maybe later" and "Not now" work, do not re-prompt, and do not
trap. The spec's "never trap a user in onboarding" principle holds.

### Where the experience costs activation

**The shape of the flow is: do the thing → ask → ask → land.** The user completes the activation
action and is immediately met with an Apple Health request, then a notifications request, before
seeing any consequence of what they just did (OB-5). Each ask is individually well-argued and
correctly placed after value. Together they convert the payoff moment into a gauntlet. The saved
card — the emoji settling in, the checkmark, "Today was Peaceful" — is the product's whole promise
made concrete, and no new user currently sees it before being asked for something.

The cheapest high-value change in this document is holding the saved state for one beat before the
Health sheet.

**The activation screen has a visual defect in its default state** (OB-3). A transparent button
colliding with the tag chips is the first impression of the app's craft, on the screen that decides
whether the funnel completes at all.

**The screen is also busier than its job requires.** "What shaped today?" and the note field are
present and scrollable before a mood is picked, and the header advertises a long-press customization
gesture that opens a whole secondary feature (OB-8). The spec correctly hid mood and tag management;
the hint copy and the gesture itself slipped through. For a first reflection the ideal screen is:
title, twelve emoji, save.

**Denial is unacknowledged** (OB-6). A user who taps "Don't Allow" is dropped into the app with no
confirmation that anything happened. That reads as a glitch rather than a respected choice, on a
screen otherwise careful about tone.

**The reminder time is effectively not a choice** (OB-12). The one decision this screen asks for is
presented as a grey pill that looks like a label. Most users will accept 8:00 PM without registering
it was configurable — and a reminder at the wrong time is the difference between a habit and an
uninstall.

### Product-level observations

**The skip path is a permanent dead end.** "Maybe later" completes onboarding forever: no reminder
offer, no second chance, no captured preference. The old questionnaire at least learned cadence.
Whatever fraction of new users take that door currently get no habit hook at all. If
`onboarding_skipped` turns out to be non-trivial, a deferred re-offer (session 2 or 3) is a bigger
lever than anything else in this document.

**No paywall exists anywhere in onboarding.** That is the deliberate spec call, and defensible — but
it means trial conversion now rests entirely on in-app trigger sites. Worth pairing with B-32 and
B-30 before deciding it was correct.

**Two permission asks back to back is a testable choice, not a settled one.** Watch
`onboarding_reminder_viewed` → `onboarding_reminder_resolved` against a variant that defers the
reminder to a later session. The current ordering is reasonable; it is not obviously optimal.

**The confirmation renames the user's mood.** The picker says "Calm"; the confirmation says "Today
was Peaceful". This is systematic and deliberate — `emotion.mood_title.*` is a separate, more poetic
register than `emotion.option.*` (Angry→Intense, Sad→Heavy, Nervous→Anxious). Not a bug. But on a
user's very first reflection, having their choice renamed is a small comprehension cost, and
Angry→"Intense" in particular softens a feeling the user chose deliberately. Worth a conscious
decision rather than inheritance.

### Accessibility

Layout resilience at AX5 is better than expected — the welcome screen scrolls, nothing clips, and the
CTA stays reachable. Three gaps: eyebrows truncate (OB-9), the CTA falls below the fold (OB-10), and
the secondary-button hit regions need verifying (OB-11).

Separately, the saved-reflection card truncates at AX5 — "Today was Peaceful" becomes "Today was…",
losing the mood name that is the entire content of the card, and the body text overflows behind the
tab bar. That screen is outside the onboarding module but is where onboarding delivers the user, so
it is tracked here even though it sits outside the flow.

The app has still never had a runtime VoiceOver pass (`BACKLOG.md` B-19). This flow — the first
experience every new user has — is the best possible place to spend that first pass.

---

## 3. Monetization and acquisition

Onboarding is the first half of a funnel whose second half is the paywall. Reviewed together because
the activation-first redesign changed the paywall's inputs without anyone deciding to.

Same severity and model conventions as §1. Several items here are **decisions**, not fixes — they are
listed with a recommendation, but the call is the owner's.

| ID | Title | Area | Sev | Effort | Model |
| --- | --- | --- | --- | --- | --- |
| MON-1 | ✅ **Fixed** — scene activation blocked the main actor on synchronous iCloud KVS reads, freezing the whole app | correctness | **P0** | M | Opus 5 |
| MON-5 | Free tier gets nothing in Insights — introduce a real free window | packaging | **P1** | M | Opus 5 |
| MON-6 | Paywall personalization is dead for every post-redesign install | conversion | **P1** | S | Opus 5 |
| MON-7 | Annual is underpriced and the monthly/annual gap is 72% | pricing | **P2** | S–M | Opus 5 |
| MON-8 | No one-time / lifetime product | pricing | **P2** | M | Opus 5 |
| MON-9 | Trial is offered at day 0, against an empty screen | conversion | **P2** | M | Opus 5 |
| MON-10 | Paywall copy advertises features that are free | trust | **P2** | S | Haiku 4.5 |
| MON-11 | Paywall telemetry cannot explain *why* users don't convert | analytics | **P2** | S | Opus 5 |
| MON-12 | App Store metadata is not version-controlled | acquisition | **P2** | S | Sonnet 5 |
| MON-13 | Privacy — the strongest differentiator — is screenshot #6 | acquisition | **P2** | S | Opus 5 |
| MON-14 | Insights lock overlay ignores Dynamic Type | a11y | **P3** | S | Haiku 4.5 |

---

### MON-1 · Scene activation blocks the main actor on synchronous iCloud KVS reads · **P0** · ✅ FIXED 2026-08-21

Fixed on `fix/mon-1-sync-preferences-main-actor-hang`. A new `UbiquitousPreferenceStore` actor owns
every store access and batches the descriptors, so a pass is one hop off the main actor and back
rather than 21 blocking XPC calls on it. External imports now read only the keys the notification
names, local-change passes are coalesced, and `synchronize()` retries are scheduled rather than
awaited.

Verified twice over: three new tests, two of which were **confirmed to fail** when the store is
forced back onto the main actor; and `sample(1)` on the running app now shows the main thread idle in
its normal run loop with **zero** `..._WAITING_FOR_A_SYNCHRONOUS_REPLY` frames anywhere in the
process, across launch and a background/foreground cycle. Before: 2599/2599 samples blocked, no main
thread in the sample at all.

This also closes OB-17.

**Original report follows.**

**Investigated 2026-08-21. The CTA is not dead — the app was frozen.** The original symptom ("Unlock
full insights" ignoring four taps) was one manifestation of an app-wide main-actor hang. The taps were
queued, not lost: the paywall eventually appeared, then its own close button stopped responding too.

`sample(1)` on the running process gave an unambiguous stack — **100% of samples (2599/2599)** parked in:

```
EveryDayEmojiApp.swift:165
 → AppSceneActivationRefreshCoordinator.handleSceneDidBecomeActive()   (@MainActor)
   → AppSyncController.handleSceneDidBecomeActive()                    AppSync.swift:577
     → SyncPreferencesCoordinator.syncLocalChangesToCloud()            AppSync.swift:428
       → SyncedPreferenceDescriptor.value(in:)                         AppSync.swift:259
         → NSUbiquitousKeyValueStore.object(forKey:)
           → SYDClientToDaemonConnection objectForKey:error:
             → __NSXPCCONNECTION_IS_WAITING_FOR_A_SYNCHRONOUS_REPLY__
               → mach_msg2_trap                                        ← blocked
```

**The mechanism.** `syncLocalChangesToCloud()` loops every entry in `syncedPreferenceDescriptors`
(21 of them) and calls `descriptor.value(in: cloudStore)` on each. `NSUbiquitousKeyValueStore.object(forKey:)`
is a **synchronous XPC round-trip** to the SyncedDefaults daemon. So each call is up to 21 blocking
IPC calls, and it is invoked from a `@MainActor` context. When that daemon is slow or unreachable, the
main actor is held for the duration and the entire UI freezes — no tab switches, no button taps, no
sheet dismissals.

**It runs far more often than "on activation".** `SyncPreferencesCoordinator.start()` also subscribes
to `UserDefaults.didChangeNotification` and calls `syncLocalChangesToCloud()` on **every** fire
(`AppSync.swift:374`). That notification posts on every `UserDefaults` write the app makes — so saving
a reflection, toggling a setting, or completing onboarding each trigger a full 21-key synchronous
cloud scan on the main actor. `start()` additionally runs `importCloudValues(mode: .initial)`, another
full pass, during launch.

**This explains every unexplained symptom in this document:**

- OB-17's "Checking today's reflection" spinner that never resolved
- the unresponsive tab bar on that screen
- the "dead" paywall CTA, and the paywall's own close button
- the paywall stuck on "Subscriptions are unavailable" with a spinner — `refreshSubscriptions()` is
  `await`ed *after* `refreshSync()` in the coordinator, so a wedged KVS read starves StoreKit too
- `xcrun simctl launch` hanging without returning

**How much of this is real.** Reproduced on an erased simulator with no iCloud account. On a healthy
device these XPC calls normally return in well under a millisecond, so most users will never see the
freeze. But the exposure is real wherever the daemon is slow: iCloud signed out, poor network, post-restore,
or daemon under load. And the amplification — up to 21 synchronous IPC calls per `UserDefaults` write,
on the main actor — is unconditional and happens on every device regardless of daemon health.

**Fix.** Move `syncLocalChangesToCloud()` off the main actor entirely; the KVS store is thread-safe and
nothing in that loop needs main-actor isolation. Then debounce the `didChangeNotification` subscription
so a burst of preference writes coalesces into one pass instead of one pass per key written.

**This is the same subsystem as OB-1 and OB-2.** Three separate defects now trace to
`SyncPreferencesCoordinator`: it can clobber another device's settings (OB-1), it can tear down the
onboarding editor mid-entry (OB-2), and it can freeze the app (MON-1). That file deserves one
deliberate pass rather than three patches — recommend doing all three together, on Opus 5.

**Downgraded from this item:** the tab-bar occlusion theory. The tab bar is a system iOS 26 `TabView`,
and the overlap beneath it is a separate, purely visual bottom-inset problem — it was never eating taps.

### MON-5 · Give the free tier a real window · **P1**

Free users currently get *nothing* in the headline feature. The strongest available fix:

**7-day insights free · 30-day, comparisons and correlations premium.**

This makes the store screenshots honest, gives a reason to keep logging, and converts the paywall
frame from "pay to see anything" to "pay to see more" — reliably the better-converting of the two.
Needs a packaging decision plus real gating work across `InsightsView`, hence **M**.

### MON-6 · Personalization is dead for every new install · **P1**

`personalizedBadge` reads the stored questionnaire goal
([PaywallInsightsPreviewView.swift:143](EveryDayEmoji/Subscription/PaywallInsightsPreviewView.swift:143)).
The activation-first redesign removed the goal question, so **every user installing after PR #25 has
no goal answer** and the paywall headline falls back to generic — silently undoing the B-05
personalization work for 100% of new users. The mood-goal recommendation lost the same input.

Nobody decided to turn this off; it fell out of two correct decisions made in different files. This is
the concrete cost of the redesign and the clearest argument for reviewing onboarding and paywall
together.

**Recommendation:** do not reinstate the questionnaire. Derive intent from behaviour — most-logged
mood, top tag — which is better signal than a self-reported answer and costs the user nothing.

### MON-7 · Pricing · **P2** · decision

Monthly **$2.99** ($35.88/yr) · Annual **$9.99** with a 1-week trial = **$0.83/mo**, a **72% discount**.

Two problems. $9.99/yr sits well below category norms (Daylio ≈ $23.99/yr; Bearable and Stoic higher)
for a product pitched on understanding, not cheapness — roughly half the plausible ARPU. And a 72% gap
makes monthly a pure decoy; typical annual discounts run 40–50%, and this one is steep enough to
signal the annual price is arbitrary.

**Recommendation:** annual $14.99–19.99, monthly $3.99. **Blocked on B-30** — do not move price before
reading 1.4's telemetry, and note there is no experiment infrastructure to test with
(`insights_preview_variant` is a stub, B-32).

### MON-8 · No one-time purchase · **P2** · decision

Two products, both recurring. A privacy-positioned app attracts precisely the users most hostile to
subscriptions. Already suspected in B-32; this review is a second vote for it.

### MON-9 · Trial timing · **P2** · decision

The 1-week trial is offered at day 0 against an empty Insights screen. A trial is most valuable when
the thing it unlocks is visible. Offer it at ~day 7, when the calendar has shape and the user has
something to be curious about.

### MON-10 · The paywall advertises free features · **P2**

`paywall.insights_preview.feature.3` = "Weekly summary & mood streaks". Weekly summary *notifications*
are free for both tiers. Older `paywall.feature.share_summary.*` strings describe sharing, also free.
Selling something the user already has is a small trust leak on the screen that can least afford one.
Likely overlaps the B-24 dead-string sweep.

### MON-11 · The funnel cannot be diagnosed · **P2**

Five paywall events exist: `paywall_shown`, `paywall_dismissed`, `subscription_started`,
`subscription_completed`, `subscription_failed`. Missing: plan toggled, scroll depth, trial-start →
convert, and source × outcome. You can currently answer "they didn't buy" but never "why".

Add before changing price — otherwise MON-7 is an untestable guess. Note MON-1 as the reason
`paywall_shown` counts may already be understated.

### MON-12 · App Store metadata is not in the repo · **P2**

No `fastlane/` or metadata directory. Title, subtitle, keywords and description — the entire ASO
surface for an app that depends on organic search — live only in App Store Connect: undiffable,
unreviewable, with no history. The screenshot pipeline is version-controlled; the words are not.

### MON-13 · Privacy is buried · **P2**

"Never leaves your iCloud. No servers. No accounts." is the most defensible differentiator in a
category full of data-harvesting apps, and it is screenshot **#6** — past where most viewers swipe.
Positioning constraint #3 in `OVERVIEW.md` treats privacy as a product commitment; the store treats it
as a footnote. Recommend promoting to #2, behind the one-tap hook.

### MON-14 · The lock overlay ignores Dynamic Type · **P3**

`premiumLockedOverlay` uses `.font(.custom("AvenirNext-Bold", size: 20))` with no `relativeTo:`, so
the paywall gate does not scale with the user's text size — confirmed at runtime, where changing the
simulator's content size left the section unchanged.

---

## 4. Suggested order

**Onboarding**

1. **OB-3, OB-5** — the visible first-impression defects. Together roughly a day, and they
   change what every new user sees.
2. **OB-1, OB-2** — the two correctness bugs. Narrow races, silent consequences, cheap fixes.
3. **OB-6, OB-8, OB-12** — the friction points with the clearest activation cost.
4. **OB-7, OB-9, OB-10, OB-11** — motion and accessibility polish.
5. **OB-13 … OB-17** — cleanup, analytics hygiene, and the OB-17 repro.

**Monetization**

1. **MON-1 + OB-1 + OB-2 together** — all three are `SyncPreferencesCoordinator`, and MON-1 is a P0
   that can freeze the app on any screen. One deliberate pass over that file, not three patches.
2. **B-30** (`BACKLOG.md`) — read 1.4's telemetry. An hour of work, and it gates MON-7 and MON-9.
3. **MON-6, MON-10** — cheap, and each one is currently telling the user something untrue.
4. **MON-5** — the packaging change. The largest single lever in this document.
5. **MON-11**, then **MON-7, MON-8, MON-9** — instrument first, then price and time the trial.
6. **MON-12, MON-13, MON-14**.

Everything in §3 above **MON-11** is reasoning from structure, not from your data. B-30 has been open
since 1.4 and remains the only item that can reorder this list.

`OVERVIEW.md` §Onboarding already describes the flow accurately; only its "Last verified 2026-08-08"
header is stale.
