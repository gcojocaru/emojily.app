# Goals (`Goals/`) — free tier capped at 1

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


Weekly check-in targets. A goal is either **`.checkIn`** (any reflection counts) or **`.tag`** (only
reflections carrying a specific tag), with a target of 1–7 times per week.

| Piece | Role |
| --- | --- |
| `MoodGoalModels` | `MoodGoal`, `MoodGoalProgress`, `MoodGoalLimits`, `MoodGoalDefaults.recommendedGoal` |
| `MoodGoalStore` | Persists to `AppPreferencesKeys.moodGoals` as a JSON blob; sanitizes on read and write |
| `MoodGoalProgressCalculator` | Pure trailing-7-day progress, skipping disabled goals |
| `MoodGoalsViewModel` | CRUD, the free-tier gate, and paywall attribution |
| `MoodGoalCompletionTracker` | Per-week dedup for the `goal_completed_week` event |
| `GoalsSettingsView` | Settings → Goals: list, editor sheet, swipe-to-delete |

**Gating.** `MoodGoalLimits.maxFreeGoalCount = 1`, `maxPremiumGoalCount = 10`, both enforced in
`MoodGoalsViewModel`. A free user attempting a second goal gets `PremiumFeature.moodGoals` and the
paywall; a *premium* user at 10 gets a disabled button and no paywall — there is nothing left to sell.
Editing and deleting are never gated, so a free user at their limit can still change the goal they have.

**Personalization.** `MoodGoalDefaults.recommendedGoal(goalAnswer:cadenceAnswer:)` turns the
onboarding questionnaire answers into a suggested goal, surfaced as "Use recommended goal" and as the
prefill for a new goal. This is the payoff those onboarding questions were collected for.

**Sync.** Goals sync through iCloud KV — `moodGoals` is registered in `syncedPreferenceDescriptors`
as `.data`. `MoodGoalCompletionTracker`'s storage is deliberately **not** synced: it is per-device
analytics bookkeeping, and mirroring it would let one device suppress another's event.
