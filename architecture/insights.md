# Insights (`Insights/`) — premium

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


Trailing **30 days** with a **7-day** flow view. Sections: period summary, streaks (current + longest),
**goals**, **pattern highlights**, top tags, quadrant balance, weekly flow, tag↔mood correlations, and a
30-day-over-30-day comparison (`improved` / `same` / `declined`).

**Streak protection (B-16):** one isolated missed day per calendar month is bridged rather than
resetting the streak — a pure, stateless recomputation in `InsightsViewModel.makeStreaks` (and
mirrored in `MonthlyMoodStats.currentStreak` for the widgets), never persisted, never applied to
`today`, never bridging two consecutive misses. The current-streak card shows a "❄️ N day(s)
protected" caption when it applies. Not premium-gated on its own — it's a correctness fix to an
already-gated number.

**Goals** renders a progress ring per enabled goal from `MoodGoalProgressCalculator.weeklyProgress`,
over the **trailing 7 days** (not the 30-day window the rest of the tab uses). Empty state falls back
to `insights.goals.empty`. See §6, Goals.

**Pattern highlights** (`MoodPatternEngine.swift`) surface up to 3 plain-language observations:
strongest positive tag, strongest challenging tag, a 7-day consistency gap, and the strongest
quadrant-to-quadrant mood shift — all scoped to the trailing 30 days. `MoodPatternEngine.insights`
returns `[]` outright for a user with no history, so the section renders nothing rather than a
half-built card. Fully tested (`MoodPatternEngineTests.swift`); `InsightsViewModel` maps each
insight kind to display copy via `L10n`, reusing `L10n.insightsDayCount` and
`L10n.weeklySummaryDaysLogged` rather than adding new count-formatting strings.

Free users get **Goals** in full — it sits outside the gate and stays interactive — while the rest of
the tab is blurred behind a locked overlay ([InsightsView.swift](../../EveryDayEmoji/Insights/InsightsView.swift)).
The tab is *not* scroll-disabled; `.scrollDisabled` has no occurrences in the file. Changed in B-05, which
made Goals the free section so a free user's goal progress is visible without a paywall.
