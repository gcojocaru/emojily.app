# Apple Health (`HealthIntegration/`) — free

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


Writes reflections to Health as **State of Mind** samples. Write-only: the service requests
`toShare: [stateOfMindType], read: []` and the app never queries Health.

| Piece | Role |
| --- | --- |
| `HealthStateOfMindMapping` | Emotion → valence/label, tag → association, and the sync identifiers |
| `HealthStateOfMindSyncService` | Authorization plus the two save paths (single draft, batch of records) |
| `HealthPostSavePromptController` | One-time first-save prompt state and immediate export after authorization |
| `HealthPostSavePromptView` | Contextual explainer shown after the first successful reflection |
| `HealthSettingsViewModel` | The opt-in toggle, backfill, and result state |
| `HealthSettingsView` | Settings → Data → Privacy & Health |

**Contextual first-save prompt.** After the first successful new reflection, Health-capable devices
show one non-blocking explainer before the system authorization sheet. "Save to Health" requests
authorization by exporting that just-saved reflection, then enables future mirroring. "Not now"
dismisses the prompt; it is never shown again, and unavailable devices never see it. The prompt flag
is device-local because both Health availability and authorization are device-specific.

**One control, both behaviors.** Turning "Save to Health" on requests authorization, backfills every
existing reflection, and leaves the preference on so `PostSaveFollowUpCoordinator` mirrors each
future save. Turning it off only stops future writes — reflections already in Health are left alone,
since deleting a user's Health data from a settings toggle would be a worse surprise than keeping it.

**Mirroring runs on edits too**, not just new saves, so an edited reflection replaces what Health
holds for that day. It is fire-and-forget: logging a mood never blocks on, or fails because of,
HealthKit — failures are logged only.

**Deduplication is HealthKit's, not ours.** Each sample carries
`HKMetadataKeySyncIdentifier` keyed on `loggedDayKey` plus `HKMetadataKeySyncVersion` from
`updatedAt`, so re-exporting replaces rather than duplicates, and re-exporting unchanged data is a
no-op. Verified empirically: a full export run twice left the sample count unchanged at 16.

**The note is never written to Health** — only the mood, its valence, and one tag association.
