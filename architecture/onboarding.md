# Onboarding (`Onboarding/`)

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


Eight steps, ordered so the user **is given something before anything is asked of them**:
welcome → pick → reflect → payoff → Apple Health → why-you're-here → rhythm → ready.
`OnboardingFlowController` owns the phase machine; each step's layout lives in its own view and
`OnboardingModuleView` only decides which one is on screen. Every step's copy is data-driven through
`OnboardingCopyModel` in `OnboardingDefaults`, and every step composes `OnboardingStepScaffold`, which
carries the shared paddings plus the AX behaviour (copy that wraps instead of truncating, actions
reachable behind a scroll, 44-point secondary targets).

**Welcome** is unchanged: a smooth adaptive gradient with no dotted texture, a central mood surface
and four smaller ones drifting gently, "Log my first mood" and "Maybe later". Decorative tiles are
hidden from VoiceOver behind one concise hero label.

**Pick** is a flat 3×4 grid of the twelve daily moods. One tap is a whole entry — there is no Continue
button — and the tap commits, pulses the cell in its quadrant colour, then advances. No quadrant
headings, no "Add mood", and no long-press customization: the first run does not advertise a feature
it has switched off. Quadrant colour comes from `QuadrantStyle` in `SharedUI/`, shared with Insights.

**Reflect** is the real `EmotionSelectionModuleView` in its `.firstReflection` presentation, already
carrying the pick. Normal persistence, tags, notes, selection haptics, save validation and saved-state
behaviour are reused; custom-mood and custom-tag management stay hidden so onboarding cannot reach a
paywall. Because the pick already happened on its own screen, the editor shows the chosen mood back to
the user (`EmotionSelectionPickedMoodSection`) with the grid behind a "Change" disclosure, labels the
note field "Want to say why?", and offers "The emoji is enough" as a second way to save. A reflection
already stored for today outranks the pick, which is applied only after the initial load resolves.

**Payoff** lands the day cell in the Calendar tab's own month grid — the same weekday header and day
cells, not a lookalike — a beat after the screen arrives, with a running "1 of 31 days" count. This is
the first thing onboarding gives, and it comes before Health, the goal question and the notification
ask.

**Apple Health** is a step of its own rather than a sheet thrown over the saved-reflection celebration.
It discloses that notes stay in Emojily and that Emojily never reads Health data.
`OnboardingHealthCoordinator` owns the exactly-once action gate: authorization is followed immediately
by an export of the reflection just saved, so connecting never skips the entry that motivated it, and a
failed backfill still counts as connected because mirroring is on and the next save will land. Any
resolution — connect or skip — spends the in-app post-save Health prompt, so Health is asked exactly
once. On a device without Health the action is disabled and the step says so.

**Why-you're-here** returns the goal question that the activation-first redesign dropped (MON-6), but
in a different position: after the user has logged a day and seen the payoff, with each option naming
what it changes. The answer is written to the existing `questionnaireGoal` preference as it is chosen,
so `PersonalizationSignal` picks it up and prefers it over behavioural inference; skipping leaves
inference in charge and nothing regresses. The step also deliberately separates the two system
prompts, so Health and notifications never land back to back.

**Rhythm** asks cadence first and lets it choose the time, rather than opening on a time picker.
"Every day" and "Weekdays" schedule a fixed-time daily reminder (all days / Mon–Fri via the cadence's
weekday mask); "When I feel like it" schedules the weekly recap only, so opting out of a daily nudge
still leaves a thread back to the app. The time control is an explicit −/+ stepper at half-hour
granularity plus Morning/Midday/Evening presets, replacing the compact `DatePicker` that read as a
label rather than a control (OB-12); Settings keeps the exact picker and all advanced schedule
controls. The chosen cadence is stored in the existing `questionnaireCadence` preference.

**Ready** recaps today's mood, the goal, the check-in and Health, and hands off with "Open Emojily".
The Health row is omitted on devices without Health rather than reading "Off".

Onboarding may only ever turn notification and Health preferences **on**. Skipping, denial, or failure
before scheduling leaves preferences untouched; if daily scheduling succeeds but the weekly request is
denied or fails, the daily preference stays enabled and the weekly one stays disabled. Every resolved
path shows localized status, then hands off after a short delay — a success only long enough to
register, anything unexpected long enough to be read (OB-6). `OnboardingReminderCoordinator` and
`OnboardingHealthCoordinator` each own their exactly-once action gate, scheduling task, outcome
analytics, haptic decision and final handoff. Analytics records the step, the source and coarse
outcomes only — never the selected time, authorization status, mood, tags, or note.

Completion is persisted the moment the first reflection saves, so a force-quit during any later step
cannot reopen onboarding; only `OnboardingRootPresentation.finish()` takes onboarding down, and no
transition may run once it has handed off.

**The skip path.** "Maybe later" completes onboarding without trapping the user, and now also records
the skip. On that user's first real log, `PostSaveFollowUpCoordinator` offers the reminder once —
the ask the exit never got to make — via `OnboardingDeferredReminderSheet`, at the moment they have
shown the app is worth a nudge rather than on a first launch when they had no reason to think so. It
is suppressed if a reminder is already enabled (for example from another device), and it is offered
exactly once. Because that save is spent on the reminder, the Health prompt slides to the next save
rather than being lost; the two never land together. Saves made *inside* onboarding present no
follow-up at all — onboarding sequences its own asks — while still counting the entry and still running
the always-on side effects such as Health mirroring.

**Motion between steps.** The two screens are never on screen together: the outgoing step clears out
over 165 ms on a sharp curve, and only once it is gone does the next one settle in over 460 ms on a
long, soft decelerate. A cross-fade would put two competing headlines on top of each other for a few
frames, which is exactly what makes a flow feel cheap. Copy, body and actions then arrive a beat
behind the screen itself with heavily overlapping delays, so it reads as one motion landing rather
than a queue of elements animating. `OnboardingMotion` owns the curves and durations and
`OnboardingStepTransitionModifier` the poses; `OnboardingModuleView.handOff(to:)` sequences the two
phases, and phases that share a screen collapse via `OnboardingPhase.displayStep` so the editor is
never torn down mid-save. Reduce Motion keeps the hand-off and drops only the geometry — no scale, no
travel — alongside removing ambient loops and the pick's commit pause. At accessibility text sizes the display headline and pinned save action cap at
the first accessibility category while scrollable content keeps the user's requested size. App Lock
remains deferred to Settings rather than requested before value is shown.

Settings replay presents the same eight steps in a full-screen cover with a 44-point close action
available throughout, and never clears the completion preference.
