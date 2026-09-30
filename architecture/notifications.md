# Notifications (`Notifications/`)

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


- **Daily reminder** — two modes: `fixedTime`, or `randomInInterval` (a random time inside a window, scheduled per-day ahead). Weekday masks: all days or weekdays-only.
- Fixed-time schedules normally use repeating calendar triggers; when a caller explicitly skips the
  current day, they use the same bounded concrete-date plan as random schedules so tomorrow is the
  earliest possible request.
- **Weekly summary notification** — chosen weekday + time, deep-links to `//weekly-summary`.
- **Monthly recap notification** — the 1st of the month at 10:00, deep-links to `//recap`. On by
  default. It has no schedule controls, because the thing it announces has a date of its own; and it
  is a single repeating request with period-neutral copy, because in January the story on offer is
  the *year*, and twelve month-specific requests would spend twelve of the sixty-four pending slots
  the daily reminder already leans on.
- All three are **free**. All three sync their settings across devices.
- Because random-interval reminders are scheduled as concrete future requests, a **BGAppRefreshTask** (`com.plainpro.EveryDayEmoji.notification-refresh`) tops them up in the background.
