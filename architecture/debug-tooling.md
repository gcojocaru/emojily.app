# Debug tooling (`Debug/`) — debug builds only

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


Shake to open Debug Tools: mock-data prefill, emoji shuffle, weekly-summary mock, the **B-10
on-device summary prototype**, recap sound, the **recap hint** override (shows Today's recap card
outside its eight-day window), the **What's New** sheet and a reset for the release it has already
shown, motion tuning, and the **premium override** toggle (premium without a
StoreKit purchase). `AppScreenshotSupport` drives the deterministic App Store screenshot scenarios.

**"Debug builds only" was aspirational until 2026-08-28.** The shake handler carried no build guard,
so any shipped build opened this menu by shaking the phone. Survivable when it held an emoji shuffle;
not once B-10 put the user's own journal notes and switches for an AI prompt's safety rules behind it.
`DebugToolsAvailability.isEnabled` now gates both the shake trigger and the sheet presentation, and
`DebugToolsAvailabilityTests` pins it along with `WeeklyNarrativeFeatureFlag` and the exclusion of
experimental voices from `selectableCases`.

Shake is unreachable from any simulator automation, so nothing behind this menu could be verified on a
simulator. `DebugToolsLaunchOverride` opens it from the `-debug-tools-on-launch` launch argument
instead — debug builds only, inert without the argument.

---
