# Mood recap story (`MoodRecap/`) — free, from Today

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


A full-screen, tappable story: intro, title, grid build, top-mood reveal with a ticking counter
and confetti, spectrum bars, podium, outro. Seven scenes over 22 seconds, ported from the design
project's `Month video.html`.

**The running order is built from the data, not fixed.** `video-recap.jsx` hardcodes seven scenes
against a 22-second stage, which is right for a design file with one canned month behind it and
wrong for real journals: a reader with two distinct moods has no podium, one with no tags has no tag
scene, and a single month has no months chart. `RecapTimeline.scenes(for:)` assembles the beats that
earned their place and the stage lasts as long as they take.

**Eleven possible beats.** Intro, title, grid, top mood, months, streak, weekday, spectrum, tags,
podium, outro. Four are new work rather than ports — months (twelve bars, best month named), streak
(the run counted up and drawn as cells lighting in sequence), weekday (seven columns where height is
how often and colour is what it usually felt like), and tags (the only scene that answers *why*
rather than *how it felt*, in `TagStyle`'s own colours). `bestMonth` and `longestStreak` were already
being computed by B-15 and never shown.

**One story, two periods.** `RecapPeriod` is `.month` or `.year`, and exactly one scene differs —
a month shows a calendar with an emoji in every cell, and a year cannot, because 365 cells leave
about six points each. The year speaks in **colour** instead: each logged day takes its quadrant's
accent, so the grid reads as the shape of the year rather than a wall of dots, and it builds a
week-column at a time because 53 columns cascade better than 365 days. Everything else — top mood,
spectrum, podium, outro — reads the same derived numbers either way.

**B-15's four day states live here now**, and they matter more in a story than they did on a card:
`beforeStart` and `future` are days that were never the reader's to log, and drawing them as gaps
is what makes a half-lived year look like a failed one. `eligibleDayCount` follows the same rule,
so the year quotes "30 of 31 days" rather than "30 of 365".

**The easings are ported, not approximated.** `RecapEasing` and `recapAnimate` are transcribed from
the design's `animations.jsx`, and the scenes are laid out in its 1080×1920 canvas. Every number in
`RecapScenes.swift` is therefore the design's own number and stays auditable against the source; a
SwiftUI spring would have made each one a guess. It also means these views can render a share image
at full resolution.

**Three deliberate departures from the source.** It is a story you hold, not a video that plays —
tap-forward, tap-back, hold-to-pause, and swipe-down-to-close, because that is what a story in an app
is expected to do. (The transport overlay sits *under* the chrome for the same reason: layered over
it, as it first shipped, a full-screen tap target covered the close button and the X advanced the
story instead of closing it.)

**Reduce Motion turns the video off, not the story**: each scene renders at its settled state, only
advances on a tap, and no clock is installed at all. And the top-mood line reads its adjective off
the quadrant rather than hardcoding "happy", which would be untrue of a month that was mostly
anything else.

**VoiceOver stops the clock too, and the scene becomes the control.** The tap halves are hidden from
VoiceOver — a full-screen target whose meaning depends on where it is touched cannot be spoken — so
`RecapTransport.autoplays` treats VoiceOver like Reduce Motion, and each scene is one combined,
*adjustable* element: swipe up for the next scene, down for the previous, with "Scene 3 of 9" as its
value. Every scene is a new element, and focus is moved onto it, so VoiceOver reads the whole scene
rather than only the changed position. Adjusting past the last scene stays put instead of closing;
the close button and the two-finger escape close it. The two grids are the only scenes drawn as
shapes: the month grid speaks as one "30 of 31 days" summary instead of sixty-odd fragments, and the
colour-only year grid is hidden, since the line beside it already says the same thing.

**The last scene exports the story as a video.** Tapping the outro's share button
renders the whole recap to a 1080×1920 MP4 and opens the share sheet — which is
also where "Save Video" lives, so one path covers both sharing and saving. It works
because the scenes were always pure functions of a scene-local clock: rendering
frame *n* is just asking `RecapFrame` for time `n / 30`, so the exporter and the
live story use the same views. The final share button is shown only in the live
story; exports omit it and center the remaining emoji and closing message.
Closing text stays center-aligned when it wraps. Rendering is the slow part, not
encoding, so the loop yields between frames and reports honest progress rather
than freezing behind a spinner. Measured: 31.5s at 1080×1920/30fps, ~14 MB.
Half a minute is long enough to change your mind, so the overlay has Cancel, and
closing the story stops the render too; either way the half-written file is
deleted. A failure is an alert with Try Again — it used to share the caption
alone, with no sign the video was missing (B-50).

**Recorded music and sparse card cues.** The bed is the first 40 seconds of
Holizna's “Poor, But Happy,” instrumental jazz guitar with a light lo-fi beat;
the seven scheduled cue assets use Kenney Casino Audio card recordings. Both
sources are CC0. [`Audio/CREDITS.md`](../../EveryDayEmoji/MoodRecap/Audio/CREDITS.md)
records provenance and measurements, and
[`scripts/prepare_recap_audio.py`](../../scripts/prepare_recap_audio.py) prepares
the downloaded archives. The older synthesis scripts are historical experiments.
Forty seconds covers the longest current story without a loop boundary.

**Sound is off by default, with a visible choice.** A localized speaker button
has a 44-point target and accessible state. The same preference controls audio
in the exported MP4. Playback respects silent mode, pauses during holds and when
the app becomes inactive, and stops at the end or when sharing. Seeking discards
skipped cues and repositions the music; prepared cue players preserve overlapping
sounds.

**One schedule and mix for playback and export.** A complete year has at most
10 cues, a complete month 9, and a sparse period 5. Transitions, counting sounds
and bursts are absent from the schedule; export completion is haptic only.
Both paths use the same per-sound gains and a 0.25-second fade-in and 1-second
fade-out for the bed, adjusted to the actual story duration. See
[`recap-audio.md`](../recap-audio.md) and
[`recap-sound-design.md`](../recap-sound-design.md). Tone and balance against the
visuals still require listening on a phone speaker.

**Offered on Today, for the eight days it is news.** It is free, because a share card's value is
that people post it, and it now lives where the reader already is instead of behind a tab. The
Insights button is gone: an entry point that is only interesting for a week a month reads as clutter
for the other three, and a recap nobody is told about is a recap nobody watches.

`MoodRecapOffer` still picks the period rather than offering a menu — December and January belong to
the year, every other month offers the month that just closed. `MoodRecapHint` decides *when* Today
mentions it: the **last day of the period** (the one case where it offers the period ending today
rather than the one before) plus the **first seven days** of the next one. Two things close the
window early — opening the recap, and a period with nothing logged in it, which would otherwise be a
screen reading "0 days, 0 feelings" over an empty grid.

**The hint is the only dark card on a light screen**, because the recap *is* a dark full-bleed story
and the card previews what tapping it opens. It opens through `//recap` rather than presenting its
own cover, so the story has exactly one presentation site — `AppTabContainerView` — whether it was
reached from the hint, from the archive, or from its notification, and exactly one place that marks
the period seen. It stays off a day opened from the calendar (`tracksCurrentDay`): the same editor
backfills any date, and "your August recap is ready" on top of 6 August answers a question nobody
asked. Debug Tools has a switch that forces the card on regardless of date, entries, or seen state,
since eight days a month is awkward to catch on purpose.

**Past recaps — premium (`MoodRecapArchive`), from Insights.** The hint is about one period and one
week; the archive is the other half of that decision, because a two-year-old journal has two years
of recaps and there was no way back to any of them. It lists every **closed** month and year that
has entries — same closing rule as the hint, so the month Today is currently offering is also the
first row rather than the list lagging a day behind the card above it, and December's year is the
same exception `MoodRecapOffer` already makes.

**The newest recap stays free; everything older is premium.** Gating the current one would invert
the reason the feature exists — a share card only markets the app if people can still make one — so
what is sold is the *back catalogue*, which is worth something precisely to the people who have been
logging long enough to have one. Locked rows still show the real month and the real day count rather
than a blurred panel: the list is of the reader's own journal, and hiding it would sell nothing while
making the app look like it was withholding their own months from them.

The row is hidden entirely until something has closed — an entry point that can only lead to a
paywall is not an entry point. The archive checks before it asks, and `presentRecap(period:)` checks
again, since a `//recap?period=` link can arrive from outside the app.

**Analytics (B-42).** `RecapViewingSession` reports one viewing as `recap_story_opened` and
`recap_story_closed`: period, origin, and whether it autoplayed or moved only by hand (Reduce Motion
or VoiceOver), with the furthest scene reached on the close in place of an event per scene. The
origin rides the deep link as `from=hint|notification|archive`, because every surface opens the
story through the same link; a link without one counts as `link`, and the debug menu as `debug`.
`recap_export_finished` and `recap_share_finished` follow the video out.

**Localized across all 14 locales.** Two traps were worth getting right rather than retrofitting.
The top-mood line is **one whole sentence per quadrant**, not a shared sentence with a mood word
slotted in — a fragment cannot carry gender or case agreement, so "You were %@" breaks the moment it
reaches Romanian or the Slavic locales. And months and weekdays use the **declined** form (`MMMM`,
`weekdaySymbols`) inside sentences and the **standalone** form (`LLLL`) for labels, because Russian
wants "в августе" in a sentence and "Август" on an axis.

**The design's line was "You were happy more often than not."** These describe the *days* instead —
"More bright days than not." — for the same reason `WeeklyNarrativeRule.noJudgement` exists: a recap
may describe a stretch and must not characterise whoever lived it.
