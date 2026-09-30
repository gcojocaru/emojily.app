# What's new (`WhatsNew/`)

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---

A sheet of release notes, shown once per release to readers who were already using the app, plus the
one place the app asks to hear back.

**The release names its own version** rather than reading the bundle's `MARKETING_VERSION`. The notes
are written by hand, so a build that ships without new notes stays quiet instead of re-announcing the
last set under a new number. Bumping `version` in `WhatsNewRelease.current` is the deliberate act that
makes the sheet appear again, and versions compare component-wise as numbers — a string compare would
read `1.10` as older than `1.9` and silence a whole release.

**Two tiers.** `highlights` are the features worth a row each — what a reader would miss if nobody
told them. `improvements` are the smaller things — a default, a gesture, a screen that got faster —
folded behind one "Smaller updates and improvements" row that opens in place, so the sheet stays
about the features while still owning up to everything else.

**The list is what was delivered, read off the commits.** 1.4 is the last build that shipped, so the
1.5 notes cover every commit since that reaches a reader, whichever changelog section it landed in.
The highlights are the recap story, past recaps, logging from the widget and Control Center (one
row), the living emoji, search, deleting a day or everything, and the on-device sentences; the rest
are smaller updates. Anything still behind a debug switch — Year in Pixels, today — stays out until
it ships.

**A line about something the reader will never see is left out.** The weekly sentence and Daily Echo
are written by Apple Intelligence, on eligible devices, in English only, and the notes go to every
locale. `WhatsNewRequirement.onDeviceWriting` marks those lines, and
`WhatsNewRelease.available(canWriteOnDevice:)` drops them where Daily Echo's own gate (`DailyEchoComposer.unavailableReason()`)
gives a permanent no — an ineligible device or an unreviewed language. Apple Intelligence switched
off, or its model still downloading, keeps them: that reader is a setting or a few minutes away.

**Premium features say so.** A highlight with a `premium` `PaywallContext` wears the `PREMIUM`
capsule (`SharedUI/PremiumBadge`) beside "See Premium", and for a free reader the whole row is the
button; a subscriber sees "Included in your Premium" beside the capsule instead. In 1.5 that is one
row — past recaps, the release's only paid surface.

**"See Premium" never sells full price to someone about to be offered less.** The notes and the
thank-you discount go to the same people — readers who were here before the update — so
`WhatsNewPremiumDestination` sends anyone the discount is owed to, or still open for, to
`ThankYouOfferView`, on exactly the terms the save path presents it on: confirmed free by the store,
and the offer priced lower than `yearly_sub`. Opening it from here spends a pending offer the same way
a save would — the three-day clock starts and Settings offers the way back. Everyone else gets the
ordinary paywall, opened with source `whats_new` for analytics and the row's own context for what it
leads with, so a reader who asked about past recaps sees past recaps. Both are presented as covers
over the sheet, and closing them returns the reader to the notes.

**A fresh install is never shown the notes.** Every line describes a feature a new user is meeting for
the first time, so there is nothing to catch them up on. The signal is `didFinishOnboarding`, read at
launch from `EveryDayEmojiApp.init()` — *before* onboarding can set it. A fresh install still reads
`false` there and has the current release banked as already seen; a reader who is updating reads
`true`, keeps their empty slate, and gets the sheet. Reading it any later would be useless: by the
time the tab container appears, a new user who has just finished onboarding is indistinguishable from
one who updated.

**Marked as told when presented, not when closed.** A force-quit part-way through reading is not a
reason to open the same notes again on the next launch.

`whatsNew.lastSeenVersion` is deliberately **not** an iCloud-synced preference. The sheet is a one-shot
piece of local UI, and mirroring it would let the first device to launch consume the announcement for
every other one — the same reasoning as the widget prompt.

**It looks like the other celebration screens.** The week-one card and the thank-you offer set the
language — see [`playful-screens.md`](../design/playful-screens.md). `WhatsNewHeroView` is the
week-one ring told about the app: one tile per highlight, in its mood colour, lands clockwise round a
ring that closes with a flare and a burst around the version number. The rows below lead with the
same tiles (`WhatsNewGlyphTile`), and each row arrives as its tile lands — the hero's beat, passed to
`.revealed(…, step:)` — so the picture is the table of contents. Mood light drifts behind it
(`MoodAurora`), and "Got it" is there from the first frame. The show runs once per presentation —
coming back from a paywall does not replay it — and Reduce Motion draws it closed and still, with no
haptics.

**It is short on purpose.** A sheet that has to be scrolled through to reach "Got it" is a chore. The
hero is 150 pt, the features are one card of rows with a single line of detail each, and the smaller
updates and the feedback share one card at the foot. On a 6.3" phone every feature is on screen
above "Got it" without scrolling, and the foot card is a short scroll below. Keep it that way: a
detail that needs a second line wants rewriting, and past seven highlights the rest belong in the
smaller updates — `WhatsNewReleaseTests` holds the list to seven.

**The feedback row is the point of the sheet as much as the notes are.** An update note is the moment
a reader has just been told the app changed, which is the moment they are most likely to have an
opinion about it, so the invitation to write in sits in the same sheet rather than three taps away in
Settings. It opens `SubscriptionSupportLinks.supportEmail`, the same address as Settings → Help.

**Where it appears:** `AppTabContainerView`, which onboarding never renders — so the container's first
appearance is exactly the first thing an existing user sees after an update.

**Analytics:** `whats_new_shown`, `_dismissed`, `_feedback_tapped` and `_improvements_expanded`, each
with `version` and `source` (`launch`, `debug`, `screenshot`). Shown and dismissed are counted once per
presentation, not once per paywall visit: a cover opened from the sheet takes it off screen and gives
it back. The paywall reports `paywall_shown{source: whats_new}` and the purchase
`subscription_started{source: whats_new}`; the thank-you route reports
`thank_you_offer_shown{source: whats_new}`.

**Audited.** The `whatsNew` screenshot scenario shows the sheet to a free reader on a device that can
write, and `AccessibilityAuditTests.testWhatsNewIsOperable` audits it — after waiting for the
feedback row, the last thing to arrive, since the rows rise in over a second or so.

**Debug:** the sheet is a once-per-release, once-per-install surface, so Debug Tools carries both
halves — a button that opens it on demand, and a reset that forgets the stored version so the *launch*
path can be exercised again. See [`debug-tooling.md`](debug-tooling.md).

**Writing the next release's notes:** bump `version`, replace `highlights` and `improvements` from the
changelog, give each highlight a tint so no two neighbours share a colour (a test checks the ring
wraps cleanly), set `premium` on anything paid, and set `requirement` on anything a device might not
be able to show. Every line is a new pair of strings in all 14 catalogues.
