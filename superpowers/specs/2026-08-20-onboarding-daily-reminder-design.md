> **ARCHIVED — historical planning document, not current guidance.**
> Written against a tooling setup that is not installed in this repo. Any instructions inside
> addressed to "agentic workers" (required sub-skills, subagent protocols) refer to that other
> system and do not apply here — treat them as a record of what was planned, not as directions.
> The live rules are in `AGENTS.md`; the map is in `CLAUDE.md`.

# Onboarding Daily Reminder Design

## Purpose

Extend the activation-first onboarding flow with one contextual notification step after the user saves
their first real reflection and resolves the Apple Health follow-up. The step should help the user turn
reflection into a gentle habit without asking for notification permission before the app has shown
value.

This document amends `2026-08-20-activation-first-onboarding-design.md`. It supersedes that document's
statements that notification permission and reminder setup are entirely deferred from onboarding. The
welcome, real first-reflection editor, Apple Health handoff, replay safety, privacy, and App Lock
decisions remain unchanged.

## Product Decisions

1. Onboarding offers only a daily mood reminder; it does not expose weekly-summary controls.
2. The reminder invitation appears after the first save and Apple Health follow-up.
3. The invitation includes a compact time picker, initially set to the existing 8:00 PM default.
4. Granting notification permission schedules both the chosen daily reminder and the existing weekly
   summary schedule.
5. The screen explicitly discloses the weekly summary with copy equivalent to “You'll also receive one
   gentle weekly recap.”
6. “Not now” never opens the system permission prompt.
7. Settings replay does not show or mutate the notification step.
8. App Lock and all paywalls remain outside onboarding.

## User Journey

The new-user path is:

`Welcome → First reflection → Apple Health follow-up → Daily reminder invitation → App`

If the Apple Health follow-up is ineligible, the reminder invitation appears immediately after the
saved-state transition. If the user skips onboarding from the welcome screen, no reminder invitation
or permission prompt appears.

### Daily Reminder Invitation

The full-screen reminder invitation uses the onboarding's smooth, no-dot gradient and contains:

- a calm feature-local notification illustration;
- title: “Make reflection a gentle habit”;
- concise supporting copy explaining the daily check-in;
- a compact time picker using the user's locale and 12/24-hour preference;
- a disclosure that one gentle weekly recap is also enabled;
- primary action: “Set my reminder”;
- secondary action: “Not now”;
- a Settings-later reassurance.

The picker starts at the stored daily reminder time when a valid value exists, otherwise at 8:00 PM.
The invitation does not expose fixed-versus-random scheduling, weekday masks, or weekly-summary day and
time controls. Those remain in Settings.

### Primary Action

When the user taps “Set my reminder”:

1. Disable repeated submission and show a compact in-place progress state.
2. Ask for notification authorization through the existing notification service.
3. If authorization is granted, schedule an all-days fixed daily reminder at the chosen time while
   skipping the current day because the user just saved a reflection.
4. Schedule the weekly summary using the existing stored configuration, defaulting to Monday at
   10:00 AM.
5. Persist each enabled preference only after that schedule succeeds.
6. Show a brief success microinteraction and complete the onboarding handoff.

The selected time is written as the fixed daily reminder time only after daily scheduling succeeds.
The random interval and weekday-mask preferences are not rewritten beyond setting the mask to all days
for this onboarding-created schedule.

### Secondary Action

“Not now” performs no authorization request, leaves daily and weekly notifications disabled, and enters
the app immediately. The controls remain available in Settings.

## Scheduling Outcomes

The onboarding coordinator exposes explicit outcomes:

- `scheduled`: daily and weekly notifications were scheduled and both preferences were enabled;
- `dailyOnly`: the daily reminder was scheduled but weekly-summary scheduling failed; daily remains
  enabled and weekly remains disabled;
- `permissionDenied`: authorization was denied or was already denied; both remain disabled;
- `failed`: daily scheduling or authorization failed before a reminder could be established; both
  remain disabled.

On `scheduled`, use the existing success haptic if haptics are enabled, briefly reveal a calm success
state, then enter the app. On `dailyOnly`, continue with a non-blocking status and leave weekly-summary
recovery to Settings. On denial or failure, show a short “You can change this in Settings” status and
continue. No result traps the user or creates a retry loop.

The coordinator must remove or leave disabled any stale onboarding-owned notification preference when
daily scheduling does not succeed. It must not remove notification requests configured by an existing
user outside this new-user flow.

## Flow State and Persistence

`OnboardingFlowController` gains a `dailyReminder` phase for new users. After the reflection module
reports that Apple Health or any other blocking post-save presentation has resolved:

- new-user source transitions from `finishing` to `dailyReminder`;
- Settings replay finishes and dismisses back to Settings;
- completing or skipping the reminder phase invokes the existing idempotent finish callback.

`didFinishOnboarding` remains persisted immediately after the first reflection saves. If the app is
terminated during the Health or reminder step, the next launch enters the normal app rather than
replaying permissions. The user can configure reminders in Settings. This preserves the existing
anti-trap and force-quit behavior.

## Architecture

### Onboarding module

`OnboardingModuleView` continues to own phase composition and callback orchestration. A focused
`OnboardingDailyReminderView` owns only the reminder invitation layout and local interaction state.
`OnboardingIllustrations` owns the feature-local reminder artwork. `OnboardingModels` or a small
onboarding scheduling model owns the selected-time conversion and presentation outcomes.

### Notification boundary

An `OnboardingReminderCoordinator` reuses `NotificationServicing`; it does not talk directly to
`UNUserNotificationCenter` and does not duplicate request construction or authorization logic. The
coordinator receives a notification service and preference store/defaults dependency, then performs
the daily-first, weekly-second transaction.

The existing unused `OnboardingNotificationPermissionService` should be removed or folded into the
coordinator rather than retained as a parallel permission path. Settings continues using
`NotificationServicing` unchanged.

### Preference writes

The coordinator owns onboarding-specific preference updates:

- successful daily schedule: enable daily reminder, store fixed mode, chosen minutes, and all-days mask;
- successful weekly schedule: enable weekly summary while preserving its stored/default weekday and
  time;
- skipped, denied, or daily failure: daily and weekly remain disabled;
- weekly-only failure after daily success: daily remains enabled and weekly remains disabled.

Writes occur on the main actor and use the existing `AppPreferencesKeys`. No new persisted schema is
required.

## Motion, Haptics, and Accessibility

- Reuse the onboarding gradient and shared primary capsule button.
- Introduce the reminder content with the same high-damping phase transition as the welcome/editor
  flow.
- Give the notification illustration one slow ambient movement; stop it under Reduce Motion.
- Use a restrained press scale and light impact on the primary CTA.
- Use the existing success notification haptic only after daily scheduling succeeds.
- Replace directional/scale motion with short opacity transitions under Reduce Motion.
- Keep the time picker, primary action, and secondary action reachable at accessibility text sizes.
- Give every control a localized accessibility label and maintain a minimum 44-point target.
- Treat decorative notification artwork as hidden or as one concise accessibility element.
- Support light/dark appearance and compact-height scrolling without fixed-height text clipping.

## Analytics and Privacy

Add only funnel-level events needed to evaluate the invitation:

- reminder invitation viewed;
- reminder primary action tapped;
- reminder skipped;
- reminder scheduling resolved with `scheduled`, `daily_only`, `permission_denied`, or `failure`.

Include onboarding source and outcome only. Do not send the selected reminder time, locale, notification
authorization status, mood, tags, note, or weekly-summary schedule.

## Localization

Add the reminder title, supporting copy, time label, weekly disclosure, primary action, secondary
action, Settings reassurance, progress state, success state, partial-success state, denial/failure
state, and illustration accessibility summary through `L10n` and every one of the 14 app locales.

Copy must remain concise enough for compact heights and long translations. The system permission alert
continues to use the existing localized notification usage description.

## Validation

### Automated

- New-user post-save resolution enters the reminder phase instead of finishing immediately.
- Settings replay still finishes without presenting or scheduling notifications.
- Skip performs no notification-service call and leaves both preferences disabled.
- The selected time becomes a normalized fixed all-days daily configuration.
- Daily success followed by weekly success enables both preferences.
- Daily success followed by weekly failure produces `dailyOnly` and enables only daily.
- Permission denial or daily failure leaves both disabled.
- Repeated taps and callbacks schedule and finish at most once.
- Analytics omits the selected time and reflection content.
- Localization keys remain aligned across all 14 locales.
- Existing notification Settings, reminder scheduling, Health handoff, onboarding flow, and reflection
  tests remain green.

### Simulator

- Run the real new-user flow through first save, Apple Health dismissal, reminder screen, system
  notification prompt, and final app handoff.
- Verify the chosen time is visible before authorization and the daily/weekly requests exist after
  granting permission.
- Verify “Not now” does not display the system prompt.
- Verify denial exits cleanly and Settings reflects both notification features as disabled.
- Verify Settings replay never displays the reminder invitation.
- Capture default light, dark, Reduce Motion, and large Dynamic Type states with XcodeBuildMCP.

## Delivery Boundary

This amendment adds one new-user reminder invitation and schedules the existing daily and weekly
notification features. It does not redesign notification Settings, add new notification content,
change reminder randomization, add App Lock solicitation, introduce paywalls, or change the completion
persistence boundary established by the activation-first onboarding.
