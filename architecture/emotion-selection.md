# Emotion selection — the core screen (`EmotionSelection/`)

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


**12 built-in emotions**, each mapped to one of four quadrants used throughout Insights:

| Quadrant | Emotions |
| --- | --- |
| `excited` | happy 😊 · confident 😎 · grateful 😇 |
| `calm` | calm 😌 · neutral 😐 · touched 🥲 |
| `sad` | sad 🙁 · crying 😢 · tired 😴 |
| `stressed` | angry 😡 · nervous 😬 · mindblown 🤯 |

**6 built-in tags:** work · friends · exercise · family · creative · rest. Wherever a tag is drawn
as a chip — the editor's picker, the saved reflection, the calendar day detail — it goes through
[TagChip](../../EveryDayEmoji/SharedUI/TagChip.swift), which carries the tag's `TagStyle` symbol and colour
and fills with that colour once the tag applies. Chips wrap via `WrappingHStack` rather than sitting
in an equal-width grid, so each one is only as wide as its label.

On top of that: **custom emoji overrides** (swap the emoji for a built-in emotion),
a **custom mood catalog** (fully user-defined moods), and **custom tags** — each with its own store
and free/premium limit. All three live in
[MoodCatalogViewModel](../../EveryDayEmoji/EmotionSelection/MoodCatalogViewModel.swift), which owns what there *is* to
pick from; `EmotionSelectionViewModel` owns the reflection being written. They meet in one place —
resolved tag options depend on the current selection — and that is a parameter
(`catalog.tagOptions(selectedTagIDs:)`), deliberately not shared state, so no cache has to be
invalidated when either side moves. An entry carries several tags. Notes cap at 500 characters; tag and mood
titles at 20.

The screen is split into section views (`...HeaderSection`, `...EmojiPickerSection`, `...TagsSection`,
`...DescriptionSection`, `...StatusSection`, `...SaveButtonSection`, `...SavedReflectionSection`),
orchestrated by `EmotionSelectionModuleView`. `AGENTS.md` requires that split be preserved.

**The saved state is its own screen, not a confirmation.** Once the day is logged, the picker is
replaced by three cards composed in `EmotionSelectionSavedReflectionSection`:

| Card | Owns |
| --- | --- |
| `SavedReflectionHeroCard` | The mood as the subject — emoji, title, save time, tag chips, the inline tag editor, and the Change / Share actions |
| `LivingEmoji` | The saved emoji, alive: it leans with the phone (Core Motion, re-centred on how the phone is held) and bounces on a tap, with sparks in the mood's colour; five quick taps throw a shower of the emoji (`EmojiPlay`). Decoration — VoiceOver skips it; Reduce Motion keeps only a haptic and a glow |
| `SavedReflectionNoteCard` | The note, read back or edited in place; the whole card is the field, and it is kept wholly clear of the keyboard as it is edited and grows |
| `SavedReflectionWeekCard` | The seven days ending on the entry day, the current streak, the same-mood count, and the link to Insights |

Everything on that screen is tinted by the saved mood's quadrant colour
([QuadrantStyle](../../EveryDayEmoji/SharedUI/QuadrantStyle.swift)), including the screen background — the
editor stays neutral so no mood looks pre-selected.

Tags and the note can be changed **without leaving the saved state**:
`EmotionSelectionViewModel.updateSavedReflection(tagIDs:note:)` writes straight through
`updateReflection`, deliberately skipping the save celebration and the post-save follow-ups — tweaking
context is not logging a new day. Only "Change" returns to the editor.

**Deleting the day lives in that editor**, as "Delete This Day" under Save — only when it was opened
from a saved day, so the saved card itself stays uncluttered (B-43). After a confirmation,
`EmotionSelectionViewModel.deleteEntryDay()` removes every record for the day and leaves an empty
editor for the same date; `ReflectionDeletionSideEffects` clears what else claimed the day. From the
calendar, `onReflectionDeleted` closes the day screen, since the day it showed is gone.

The week card's data comes from `SavedReflectionWeekOverviewBuilder`, a pure function over flattened
records. Its streak uses [MoodStreakCalculator](../../EveryDayEmoji/SharedData/MoodStreakCalculator.swift) —
the same forgiveness rule Insights applies, so the two screens never disagree. The Home query is
bounded to a 730-day lookback because it runs on every app open; Insights walks the full history.

The view model orchestrates; the rules live in four focused, separately tested units:

| Unit | Owns |
| --- | --- |
| `EmotionOptionComposer` | Emoji-override application, built-in + custom mood merging, sorting, sanitizing stored definitions |
| `CustomEmotionValidator` | Create/edit validation for custom moods, plus `CustomEmotionMutationError` |
| `ReflectionTagCatalog` | Tag ordering, sanitizing stored preferences, custom-tag validation, resolving the visible option list |
| `PostSaveFollowUpCoordinator` | Everything after a successful new save: entry counter, one-time Health prompt, review request, widget prompt, daily-reminder refresh |

`PostSaveFollowUpCoordinator.handleSave(draft:isEditing:isReflectionFromToday:)` returns a `PostSaveFollowUp`
the view model applies, and at most one follow-up fires per save. **New post-save behavior belongs
there**, not in the save path.

> **`EmotionSelectionViewModel` is still 1064 lines** — the largest file in the app. The pure logic
> is extracted; the remaining bulk is state declarations plus the custom-mood and tag mutation flows,
> which still own published state directly. See `BACKLOG.md` B-21.
