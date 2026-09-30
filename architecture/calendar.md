# Calendar (`Calendar/`)

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


Month grid of logged moods, with a selected-day card and a day-detail screen.
The calendar surface scrolls vertically when its content exceeds the available height, including at
accessibility text sizes, while horizontal drags on the month grid continue to change months.

**The editor and the saved card are one design.** The mood grid, note, and tags each sit in a
`surfaceFill` card with the same radii, stroke, and shadow the saved cards use; "Add mood" is the
same dashed invitation as "Add a note"; and the note field is the saved note card's twin, growing
with what is typed rather than holding a fixed block. **Colour follows the choice:** picking a mood
tints its grid cell (`EmotionPickerCellStyle`, shared with the all-emotions sheet), the save button,
the note's caret, and the tag card's edit action with that mood's quadrant colour — the same colour
the saved card, the week strip, and the calendar's day card then carry. The screen *background*
stays neutral in the editor (`activeMoodTint`) so no mood looks pre-selected before a pick.
`EmotionQuadrant.onAccentColor` supplies the ink for anything filled with a quadrant colour: the
excited yellow cannot carry white text.

**The selected-day card is a preview of the day screen.** `CalendarSelectedDayCardView` carries the
logged mood's quadrant colour (`CalendarViewModel.quadrant(for:)`) as a gradient wash, shows the emoji
in its own glow, renders tags as `TagChip`s, and reads the note back below a hairline — the same
language as the Today tab's saved card, compressed to a summary. An unlogged past day shows the
dashed "Log this day" invitation; a future day stays neutral with no action.

**The day screen is the Today tab.** `CalendarDayDetailView` hosts `EmotionSelectionModuleHostView`
bound to that day (`loadsExistingReflectionOnAppear: true`), so a logged day lands on the same saved
card the Today tab shows — tags and the note editable in place, "Change" flipping to the editor
inline — and an unlogged past day lands straight in the editor. Both the day card's log action and
its detail arrow push that one screen; there is no separate read-only layout and no modal edit sheet.
A future day, which cannot be logged, is the one exception and keeps a "No entry yet" state.
The screen reports its own `entry_detail` impression via the module's `screenImpression`.

**Backfill:** any past day can be logged from the day card or detail screen; future days cannot.
`EmotionSelectionViewModel` takes a `loggingDate` and resolves every day-scoped read/write against it.
Backfilling deliberately does **not** mark today as logged and does **not** reschedule the daily reminder.
A month share card renders a 1080×1920 image (`CalendarShareImageRenderer`).

**Year in Pixels — built, and hidden for now.** Not offered in 1.5: Calendar is the month alone
unless Debug Tools' "Year in Pixels" switch is on, and only a debug build has that switch
(`YearInPixelsFeature`). Everything below is what the switch turns on.

**Two styles, to compare on a device.** Debug Tools also picks how a day is drawn
(`YearInPixelsStyle`): **colours** — each day in its mood's quadrant colour, on the recap's mesh —
or **emojis** — each day as its own face, on a neutral lilac ground so the faces carry the colour,
with the legend listing the year's top faces and the card's miniature ringing the most-felt face with
the next ones. The emoji grid keeps the colour grid's rows — each face as tall as its row — so both
styles are the same length. The grid, the bloom, the posters and the video all follow the choice; a
shipped build draws colour.

**Year in Pixels.** A dark card under the month and its selected day — the year's bloom in
miniature, the year, and the days logged (`YearInPixelsTeaserCard`) — opens the Year screen
(`CalendarRoute.year`). The screen ([YearInPixelsView](../../EveryDayEmoji/Calendar/YearInPixelsView.swift))
is the one Calendar surface made to be looked at, so it borrows the recap's language: a near-black
ground lit in the year's own colours, the year in a gradient, one verdict line (the recap's
`recap.top_mood.line.*`), and twelve month columns of up to thirty-one glowing pixels, one per day in
its mood's colour. It *plays in* on appear and on a year change — a 2.4 s sweep from 1 January, the
newest days burning brighter, a soft haptic per month, a success haptic and a bump at the end, the
day count ticking up beside it — and is simply there under Reduce Motion. Under it: days logged,
the longest streak, the most-felt emoji, and a legend counting each colour. Tapping a day opens it
over the year, so Back returns there; arrows or a horizontal swipe change the year, and nothing
after the current one. The data is [YearInPixels](../../EveryDayEmoji/Calendar/YearInPixels.swift) —
pure, and unit-tested — loaded by `CalendarViewModel.loadYear()` in one fetch for the year, only when
the card is on offer. It carries the calendar it was built with, so a cell maps back to the right
date whatever the device's. VoiceOver meets the grid as one adjustable element — swipe up or down
between months ("March, logged 20 of 31"), double-tap to open one.

"Share year" opens `YearPosterPreview`: the year's posters as cards side by side, one per layout
(`YearPosterLayout`) — swipe to choose, with the neighbours peeking in at the edges and dots
underneath — and **Share video** and **Share image** share whichever card is in front. The card in
front plays its five seconds (`YearPosterTimeline`); a tap replays it, or brings a neighbour
forward. Every poster ([YearInPixelsShareRenderer](../../EveryDayEmoji/Calendar/YearInPixelsShareRenderer.swift), 1080×1920)
carries the month card's badge and footer in their dark variants, on the recap's mesh:

- **Bloom** — the year as a flower: twelve petals clockwise from January, each that month's days
  from the base outwards in rows of 1–4, the most-felt emoji at the heart — with the verdict and the
  three numbers. It opens and turns once.
- **Pixels** — the Year screen's grid (`YearPixelPosterGrid`), painted by the grid's own painters so
  a day looks the same shared as on screen, with its legend. The grid takes whatever height the
  title and legend leave it, so a legend that wraps shortens the rows rather than the footer. It
  sweeps in from 1 January.
- **Podium** — the year's three most-felt faces on the recap's podium, over the spectrum of the four
  quadrants in colour, or the next five faces and the three numbers in emojis. Offered only when the
  year has three faces to stand on.

The video is the front card's five seconds, silent, written frame by frame by
`ImageSequenceVideoWriter` over a mesh drawn once; it renders behind the recap's "Making your
video…" overlay, with Cancel. VoiceOver meets the carousel as one adjustable element: the card in
front is described, "Page 2 of 3" is its value, and swiping up or down changes card. Free, like the
month card.


**History search** lives in the same folder and opens from the calendar:
[HistorySearchScreen](../../EveryDayEmoji/Calendar/HistorySearchScreen.swift) hosts it,
[HistorySearchViewModel](../../EveryDayEmoji/Calendar/HistorySearchViewModel.swift) holds the query and
results, [HistorySearchMatcher](../../EveryDayEmoji/Calendar/HistorySearchMatcher.swift) does the matching
(pure, and unit-tested by `HistorySearchMatcherTests`), and
[HistorySearchResultsView](../../EveryDayEmoji/Calendar/HistorySearchResultsView.swift) renders them.
Free, and it searches notes and tags across the whole journal.
