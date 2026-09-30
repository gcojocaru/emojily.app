# Daily Echo (`DailyEcho/`)

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


One generated sentence on the saved-reflection screen, about how the recent past sits against the day
just logged. It appears only when something specific happened, which is most often not at all.

**The framework-import invariant is now "only `FoundationModels*Engine.swift` files import
`FoundationModels`."** It was "one file" through 1.5. The purpose is unchanged — no feature code
touches the framework, and everything above the seam runs on machines with no Apple Intelligence —
but there are now two engines, because the weekly card's `@Guide` wording is week-specific and would
poison a one-line daily answer.

**There is deliberately no deterministic fallback.** It was the one real break from B-10 when this
card shipped — the weekly card still had a template floor then, because it sat on a screen anyone can
open where an empty card reads as a bug. **That floor has since been removed too**:
`WeeklyNarrativeComposer` now returns nothing on every closed branch, the same shape this one has, so
the break became the rule. This card was designed for it, and is the one that loses least — its
absence is indistinguishable from an ordinary day. Dropping the template layer removed roughly 112
strings across 14 locales and means every line anyone reads here was written for them. The cost,
stated plainly: this card reaches only English-locale users on Apple Intelligence devices, and since
the floor went, the weekly sentence reaches exactly the same people. **A device that cannot generate
now shows neither**, which is the first thing to check when both are missing.

**Four kinds, each a deterministic occasion followed by a generation.** The resolver decides *whether*
to speak; the model only decides *how*.

| Kind | Fires when | Grounded in |
| --- | --- | --- |
| `returnAfterGap` | First entry after 3+ missed days | The abstinence-violation effect — the biggest churn moment in a habit app. A gap is never framed as a lapse |
| `context` | A tag co-occurs with a mood group ≥4 times, over ≥10 logged days, at ≥1.5× its base rate | The reflection→action step in personal-informatics research. Co-occurrence, never cause |
| `turn` | Today's quadrant breaks a run of ≥2 days of another | Temporal self-comparison; the safest signal, and readable in both directions |
| `echo` | Today matches an earlier day ≥14 days back that carried a tag or note | Positive reminiscence and savoring |

**Two refusals live in the resolver rather than the prompt, because a prompt rule is a request and a
branch is a guarantee.** `.echo` never fires on an unpleasant mood — recalling the last time someone
felt sad is rumination, not reminiscence. And a run of 3+ consecutive unpleasant days suppresses
`.turn` and `.echo` entirely, leaving `.context` as the only eligible kind: it may speak about what
recurred *around* those days, and if nothing did, the card stays silent. The run itself is never
named, counted or described.

**A feature designed to be absent cannot tell anyone why it is absent**, and for a while nothing
could: the reasons went to analytics and nowhere else, so "I see no card" was unanswerable without a
console. `DailyEchoCoordinator.run` now keeps the reason instead of only reporting it, and Debug
Tools → Daily Echo → **Against your own journal** runs the real gates over the reader's real entries,
in production's order, and names the first one that closed. It goes through the production
coordinator rather than a second copy of the gate order — a harness that lies about the order is
worse than no harness — tags its event `is_debug_flow` so a diagnostic never moves the numbers the
feature is judged on, and spends no slot. Alongside it, **Reset the weekly budget** hands back all
three slots and clears the stored card, because the alternative was reinstalling the app or waiting
out a seven-day window.

**Gate order is the reverse of the weekly card's.** Availability and language are answered first,
with no data at all, so a device that can never generate does no fetch and touches SwiftData not at
all. `DailyEchoBudget` then caps it at three cards per rolling seven days — scarcity is what makes the
card read as something noticed rather than something generated. **The slot is spent when the card
appears, not when the sentence arrives**: a line exists a second or two before anyone can read one,
and this is a screen people leave quickly, so charging for a sentence that reached an empty screen
would silence a real card later in the week. A refusal, a failure, a rejected draft or a reader who
had already gone all cost nothing.

**Free, with no `PremiumFeature` case**, for the same reason as the weekly narrative and more so:
with no template underneath, gating it would sell subscribers something most of their devices cannot
produce at all.

| Piece | Role |
| --- | --- |
| `DailyEchoOccasionResolver` | The core. Pure, synchronous, and where every safety refusal lives |
| `DailyEchoRule` | Fourteen safety rules as data. Five have no weekly counterpart: `noCausalClaims`, `noAbsenceAsFailure`, `noStreakCounting`, `noPrediction`, `singleSentence` |
| `DailyEchoPrompt` | The **frozen** instructions plus a per-kind fact sheet. Calls `WeeklyNarrativePrompt.sanitizedForPrompt` rather than copying it |
| `DailyEchoComposer` | The gates, and the guarantee that every branch returns *nothing* rather than something invented |
| `DailyEchoDraftValidator` | Structural compliance only — word ceiling and list shape. Never tone |
| `FoundationModelsDailyEchoEngine` | The second framework-importing file. Conforms to `WeeklyNarrativeEngine`, so `StubWeeklyNarrativeEngine` drives every test |
| `DailyEchoBudget` | Three cards per rolling seven days |
| `DailyEchoStore` | Today's line, so leaving the screen is not losing it. Device-local, and one day only |
| `DailyEchoCoordinator` | Post-save orchestration, owned by `EmotionSelectionViewModel` the way `PostSaveFollowUpCoordinator` is |
| `SavedReflectionEchoCard` | The card. No loading state and no empty state, by design |
| `DebugDailyEchoView` / `DebugDailyEchoFixtures` | The only way to see the card off-device — the simulator throws `ModelManagerError` 1026, so the production surface correctly shows nothing there — and the only thing that can say *why* a real device is quiet |

**Nothing new runs synchronously in `saveReflection()`.** The card's work starts after the save has
returned and the celebration is already running, and it is kicked off only by a *fresh, non-editing
save of today* — `EmotionSelectionViewModel.refreshDailyEcho`, guarded on `isEditing == false`.
Generation happens once, at the save; nothing regenerates on a later launch, so a device that logged
from the widget still gets no card that day.

**The card belongs to the day, not to the save.** `DailyEchoStore` keeps today's line, so the Today
tab puts it back when the saved screen is rebuilt — `restoreDailyEcho`, off the same
`loadLatestReflectionIfPresent` that rebuilds everything else there. Without it, a save at 09:00 was
unrecoverable at 09:01 if the app had been closed, and the budget slot it cost was spent all the
same; on a screen built for one tap and a swipe away, that is the common case rather than the edge
one. **A dismissal is remembered rather than reversed**, or dismissal would be a suggestion the next
launch overrules. An edit *clears* the line instead: the mood it describes is the thing about to
change. The restored card appears the way any other does, which spends its slot — and recording one
day twice is a no-op, so it stays one card.

**Dismissal is not a courtesy.** The card arrives unasked on the one screen the app promises will
stay fast, seconds after the reader already got what they came for, so it can be pushed off to
either side or closed from the header. Dismissal does not refund the budget slot — they were shown a
card, and choosing not to read it is not the same as never having been offered one. The header's
info button opens `dailyEchoDisclaimerMessage`, which is what tells a reader a model wrote the
sentence and that nothing left the phone.

**The card has no loading state and no empty state**, which is the whole difference between it and
`WeeklyNarrativeCard`. That one sits on a screen opened to read it, so it shimmers rather than
arrive late; this one is absent on most saves, and a placeholder that usually resolves to nothing
would be worse than a late arrival. It does not exist until it has words, and then it fades in —
instantly under `accessibilityReduceMotion`. VoiceOver reads it as a single element, with the
disclaimer and close exposed as named actions so the swipe is reachable without a gesture.

**`DailyEchoDraftValidator` checks the shape of the answer, and nothing else.** A rule is a request
until something verifies it, so two of them now are: a body past forty words is rejected — well above
rule `singleSentence`'s twenty-five, and set where the engine's sixty-token ceiling makes truncation
the likelier reading than a long sentence — and so is a bulleted or numbered answer, which is
multi-line content in a card sized for one line. The list question is asked by calling
`WeeklyNarrativeDraftValidator.containsListMarker` rather than copying it. **Degrading beats
rejecting**, and here that means one thing: a sentence wrapped across lines is flattened rather than
held against it. A rejection is reported as `draftRejected` rather than hidden inside
`generationFailed`, because the two ask for different fixes — one is the device, the other is the
prompt.

**What it deliberately does not check is tone**, and rule `formatting`'s ban on emoji, exclamation
marks and quotation marks goes unenforced with it. Those are how a sentence sounds rather than
whether it can be shown, and with nothing underneath, rejecting on one costs the reader the card
outright — the same reasoning that removed those checks from the weekly validator. **So the rules
remain the only tone control, and an off-tone sentence still reaches the reader**, which is what
raises the stakes on the review the prompt is still owed.

**The rules are data, and there is one register.** Fourteen `DailyEchoRule` cases, written fresh
rather than borrowed — the weekly rules say "the week" throughout, and a rule naming the wrong unit
of time is a rule the model must reinterpret before it can follow it. Five have no weekly
counterpart (`noCausalClaims`, `noAbsenceAsFailure`, `noStreakCounting`, `noPrediction`,
`singleSentence`) and four are `isLoadBearing`. `DailyEchoComposer` takes an `enabledRules` set so a
harness could switch one off and disprove it, but **nothing wires that to a screen yet**; production
always sends `DailyEchoRule.all`. There are no voices here: the weekly card's registers exist to
make the model visible on a screen opened to read it, and one sentence on a screen opened for one
tap has room for exactly one voice.

**The prompt is frozen, and not yet reviewed.** `DailyEchoPrompt` follows the `WeeklyNarrativePrompt`
freeze convention — read once by somebody reading it as wellness copy, then left alone, with any
edit invalidating that review. The weekly card has an instrument for this in
`WeeklyNarrativeEvalCorpus`; **there is no daily equivalent**, and the file's own header still says
so. With no validator underneath, that review is the whole safety story.

**Notes reach the model whenever the day carries one**, and they are the reason
`notesAreNotInstructions`, `neverRepeatNotes` and `foreignNotes` exist. At most two ever arrive —
today's, plus the day being recalled by `.echo` or `.returnAfterGap` — so `maximumNoteCount` is 2 and
the weekly combined-budget machinery has nothing to do here. They never leave the device, but free
text next to instructions is a different failure mode from structured facts: notes are fenced in
`<notes>`, the tags stripped from the note text so it cannot close the fence early, newlines
flattened so it cannot forge a fact line, and the rules tell the model the section is material to
describe and never to obey. The fence and the strip are `WeeklyNarrativePrompt`'s, deliberately
called rather than copied — there must be exactly one answer in the app to "what stops a mood titled
`</notes>` closing the fence from inside it".

**Notes are not assumed to be in the app's language.** People run an English UI and journal in their
own language, and `supportsLocale` asks about the *app's* locale, not the notes'. Each note's
language is detected on device with `NLLanguageRecognizer` (ignored below 16 characters or 0.55
confidence, where detection is guesswork), and a note is tagged in the prompt **only when it diverges**
from the answer language — tagging every note in the common case is noise the model has to read past.
`foreignNotes` then tells the model to understand it, still answer in the output language, never
quote from it, and never translate it back.

**The fact sheet names the output language explicitly.** `outputLanguage` says to answer in the
language named under *Output language*, and says outright that the fact labels are always English and
are not a hint. The labels are hardcoded while only the *values* are localized, so a rule pointing at
them would answer a Spanish reader in English the moment Spanish joined the reviewed set.

**The model covers 9 of the app's 14 locales.** `SystemLanguageModel.supportedLanguages` (checked
2026-08-26) omits **pl, ru, uk, ro and ca**, which get no card at all regardless of policy — there is
no sentence underneath to fall back to.

**Generation is refused unless someone can read the result.** The model supports far more languages
than the team can review, and `LocalizationResourceTests` can prove a *key* exists in Polish but
nothing can prove a generated Polish sentence is well-toned. The default policy therefore restricts
generation to `reviewedLanguageCodes` — today just `en` — and every other locale is silent.
`DebugDailyEchoView` constructs its composer with `.anySupportedLanguage` to lift this, purely so the
unreviewed output can be looked at.

**`availability == .available` is not a promise that generation works.** Verified in the simulator on
2026-08-26: availability reported `available` and `supportsLocale` reported `true`, and the call still
failed (`SensitiveContentAnalysisML` code 15 → `ModelManagerError` 1026) because the model assets are
absent. Silence is the load-bearing path here, not a defensive one — which is also why the card
cannot be seen in a simulator, and why `DebugDailyEchoView` exists.
