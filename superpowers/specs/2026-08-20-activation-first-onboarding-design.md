> **ARCHIVED — historical planning document, not current guidance.**
> Written against a tooling setup that is not installed in this repo. Any instructions inside
> addressed to "agentic workers" (required sub-skills, subagent protocols) refer to that other
> system and do not apply here — treat them as a record of what was planned, not as directions.
> The live rules are in `AGENTS.md`; the map is in `CLAUDE.md`.

# Activation-First Onboarding Design

## Purpose

Redesign Emojily onboarding around the fastest meaningful activation event: saving a real first reflection. The current seven-step flow explains the product, asks three personalization questions, requests notification permission, and offers App Lock before the user has experienced the core interaction. The replacement earns those later requests by demonstrating value first.

The primary success measure is the percentage of new users who save a first reflection. Secondary measures are welcome-to-editor conversion, time to first save, onboarding skip rate, and successful completion of the contextual Apple Health follow-up.

## Product Principles

1. Let the user do the real thing immediately.
2. Ask for permissions only when their value is clear.
3. Use motion to communicate state and responsiveness, not to delay progress.
4. Preserve a calm, private tone; avoid gamified confetti or pressure.
5. Never trap a user in onboarding.

## User Journey

### 1. Welcome

New users see one full-screen welcome page:

- Eyebrow: “A moment for you”
- Title: “How did today feel?”
- Supporting text: “Choose one emoji now. Add context only if you want.”
- Primary action: “Log my first mood”
- Secondary action: “Maybe later”

The visual is a central mood in a translucent surface with four smaller floating mood surfaces. It sits on a smooth adaptive gradient with no dotted texture.

The primary action moves directly to the real reflection editor. “Maybe later” marks onboarding complete and enters the normal app without showing another prompt.

### 2. First Reflection

The existing `EmotionSelectionModuleView` provides the editor. An explicit first-reflection presentation context changes only onboarding-specific presentation:

- The title is “How are you feeling today?”
- Tags and the note remain available and clearly optional.
- Custom-mood creation and management affordances are hidden during this first interaction.
- App tabs, settings, paywalls, reminders, and App Lock are not introduced.
- Existing emotion selection, validation, persistence, save behavior, accessibility, and haptics are reused.

This is not a demo or a second implementation of the editor. A successful save creates the user's real first reflection.

### 3. Save and Handoff

On the first successful save:

1. Persist `didFinishOnboarding` immediately and track onboarding completion once.
2. Keep the current editor mounted long enough to display its saved state and any selected post-save follow-up.
3. If the contextual Apple Health prompt is eligible, let it complete or be dismissed before replacing the onboarding container.
4. If no follow-up is presented, enter the normal app after the saved-state transition completes.
5. Crossfade into `AppTabContainerView`. The freshly saved reflection remains visible when the normal emotion tab loads.

Persisting completion before the visual handoff prevents a force-quit during the Health prompt from returning the user to onboarding on the next launch.

The Health prompt remains owned by the reflection module and the post-save coordinator. Onboarding observes a small completion callback; it does not duplicate Health eligibility or authorization logic.

## Deferred Setup

The redesigned onboarding does not request notification permission, reminder cadence, reminder time, or App Lock.

- Apple Health remains a contextual prompt after the first successful save when supported.
- Reminder setup remains available in Settings and should later be offered through a separate contextual engagement feature, not this change.
- App Lock remains available in Settings and should later be offered after the user has stored private content, not this change.

The onboarding goal question is removed. It currently personalizes a paywall badge more than the core experience. Existing stored goal and cadence answers remain readable for current users so paywall and goal recommendations do not regress. Legacy preference keys and mapping types are retained; new users simply do not receive new questionnaire answers.

## Replay From Settings

“Replay onboarding” must no longer set the persisted completion flag to false. It presents the welcome experience as a full-screen replay while the user remains an onboarded user.

In replay mode:

- “Log my first mood” opens the normal editor context, loading today's existing reflection if present.
- “Maybe later” dismisses the replay.
- Saving or dismissing returns to Settings without changing onboarding completion or consuming first-user analytics.

This prevents an existing user from being treated as new after replaying the introduction.

## Architecture

### Onboarding module

`OnboardingModuleView` remains the owner of flow and callbacks, with a small phase model:

- `welcome`
- `firstReflection`
- `finishing`

`OnboardingPageView` owns the welcome composition. `OnboardingIllustrations` owns the floating mood hero and its animation. `OnboardingModels` owns the page content and phase/presentation types. `OnboardingDefaults` supplies the single localized welcome model. The obsolete pager and questionnaire composition are removed from the active flow.

The onboarding background is feature-specific and uses the existing theme's adaptive gradient colors without `DottedGradientBackground`. It stays in `Onboarding/` because the no-dot treatment is part of this experience, not a new global app background.

### Reflection module

Add a narrow presentation context to the reflection host/module, with normal behavior as the default. The first-reflection context controls copy and optional management affordances; it does not branch persistence or business logic.

Add a post-save presentation-resolution callback at the reflection-module boundary. It fires when a successful save has no blocking follow-up, or after the current post-save prompt has been handled. The onboarding module uses this callback only to time the visual handoff.

### Content composition

`ContentView` remains lightweight. It selects among the onboarding container and normal tab container from the persisted completion flag plus an in-memory handoff flag. Onboarding owns its internal phases; `ContentView` persists completion and performs the final root transition.

## Motion and Haptics

### Welcome

- The central emoji breathes with a very small scale and rotation change.
- Four surrounding emoji surfaces drift independently by a few points.
- Ambient motion is slow, deterministic, and pauses when off-screen.
- The primary CTA uses the existing accent gradient and a restrained press scale.
- Tapping the CTA produces a light impact haptic.

### Welcome to editor

- Content moves left and fades while the editor enters from the trailing edge with a spring.
- Target timing is approximately 450–550 ms with high damping and no bounce past the safe area.
- The transition is interruptible and cannot block interaction after completion.

### Reflection interaction

- Reuse the existing selection haptic and emoji pulse.
- The save CTA becomes fully emphasized when a valid mood is selected.
- Do not add haptics to optional tags or text entry beyond existing behavior.

### Successful save

- Reuse the existing success notification haptic.
- The selected emoji settles into the saved card with a short scale/position spring.
- A checkmark appears just after the emoji lands.
- No confetti, sound, artificial loading delay, or repeating celebration is used.

### Reduced Motion

When Reduce Motion is enabled:

- Disable floating and breathing loops.
- Replace directional and scale transitions with a 0.2-second opacity transition.
- Show the success state and checkmark without spring motion.
- Preserve haptic behavior according to the app's existing haptics preference.

## Accessibility and Layout

- All text uses localization resources and supports Dynamic Type.
- The hero is one concise accessibility element; decorative orbiting emojis are hidden from VoiceOver.
- Primary and secondary actions have explicit labels and remain inside safe areas.
- Editor focus order follows the normal reflection screen.
- No progress dots are shown because the experience is not a multi-page questionnaire.
- Layout must fit the configured iPhone 17 simulator, compact-height devices, and accessibility text sizes without fixed-height text clipping.
- Light and dark appearances use the existing adaptive color system.

## Analytics

Retain the onboarding screen impression and completion events, and add only funnel events needed to evaluate the redesign:

- welcome viewed
- first-reflection CTA tapped
- onboarding skipped
- first reflection saved
- onboarding handoff completed

Record source (`new_user` or `settings_replay`) and elapsed time to first save. Do not send selected mood, note, tags, or other reflection content as onboarding analytics.

## Failure and Interruption Behavior

- A failed reflection save leaves the user in the editor with the existing retryable error UI. Onboarding is not completed.
- A failed Apple Health export leaves its prompt retryable according to the Health prompt design. Onboarding completion is already persisted, but the visual handoff waits until the prompt is dismissed or succeeds.
- If the app terminates after the reflection saves, the persisted completion flag opens the normal app next launch.
- If the app terminates before saving, it returns to the welcome page next launch.
- If today's reflection already exists because of sync or an unusual migration state, the onboarding editor loads it rather than creating a duplicate.
- Repeated taps on welcome and save actions are guarded while their transition or save is in progress.

## Localization

Add the welcome, first-reflection title, and replay copy to `L10n` and every supported localization. Remove obsolete onboarding questionnaire, notification, philosophy, and App Lock copy only where it is no longer referenced. Preserve any strings still used by Settings, paywall personalization, reminder configuration, or legacy-user behavior.

## Validation

### Automated

- Onboarding defaults expose exactly one welcome model.
- New-user primary action enters the first-reflection phase.
- Skip persists completion and enters the app without saving.
- Successful save persists completion once and waits for post-save presentation resolution before root handoff.
- Relaunch behavior differs correctly before and after a successful save.
- Settings replay never clears `didFinishOnboarding` or emits new-user completion analytics.
- First-reflection presentation hides management affordances while normal presentation remains unchanged.
- Localization keys remain complete and aligned across all supported locales.
- Existing reflection persistence, Health prompt, saved-state, goal recommendation, and legacy questionnaire mapping tests remain green.

### Simulator

- Build and run using the repository's XcodeBuildMCP defaults.
- Exercise first launch through first save on the configured iPhone 17 simulator.
- Capture welcome, selected-mood, saved, and Apple Health prompt states.
- Verify light and dark appearance, Reduce Motion, large Dynamic Type, VoiceOver labels/order, safe areas, and interactive control visibility.
- Confirm a force-quit after save reopens the normal app rather than onboarding.

## Delivery Boundary

This change redesigns activation onboarding and its handoff. It does not implement a new reminder solicitation, a post-content App Lock campaign, new paywall behavior, or a global background redesign.

The implementation branch is stacked on `codex/apple-health-first-save-prompt` because the approved first-save handoff includes PR #23's contextual Apple Health prompt. Its pull request should target that branch until PR #23 merges, then be rebased onto `main`.
