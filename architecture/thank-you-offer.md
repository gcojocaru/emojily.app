# Thank-you offer (`ThankYouOffer/`)

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---

A one-time thank-you for the readers who were here before 1.5: Premium at a lower price, through a
product of its own (`yearly_thank_you`), on a secondary paywall presented after their first save on
the new build and open for three days after that from the Settings tab.

**Why a product of its own, and not an offer.** The audience is free readers who have never
subscribed, and every StoreKit way of discounting for them is the wrong shape: a promotional offer
needs a signature from the app's private key (a server) *and* only applies to customers who have
subscribed before; a win-back offer is for lapsed subscribers; an offer code makes the reader type
something. A second product, `yearly_thank_you`, does none of that — an ordinary `purchase()`, one
tap, Apple's payment sheet — and the store prices it in every storefront's currency. It is the annual
plan under a second name (`SubscriptionPlan(productID:)` reads it as `.annual`, so an entitlement
bought through it is premium like any other) and is sold nowhere else: `SubscriptionManager` keeps
it in `thankYouOfferProduct`, out of `availableProducts`, so the paywall never picks it as its
default.

**App Store Connect decides what the discount is, and the app reads whichever it finds.** Either the
product is simply cheaper than `yearly_sub` and renews at its own price, or it carries an introductory
offer for the first year and renews at its full price after. `ThankYouOffer.terms(for:comparedTo:)`
measures the thank-you product against the ordinary yearly one: the original price is what
`yearly_sub` costs, the offer price is the introductory price when the store will apply one to this
reader and the product's own price otherwise, the renewal price is the product's own, and the saving
is worked out from the two. Three honest edges: an introductory offer the store will *not* give this
reader (`hasIntroductoryOffer` without `introOffer` — eligibility is per group, so anyone who ever
took the free trial on `yearly_sub` is out) yields no terms; an offer that is not actually cheaper
yields no saving; and the coordinator presents the screen only for a real discount. Nothing on the
screen is a number the store did not give.

**Only readers the store has confirmed are free see it.** `SubscriptionManager.isPremium` is `false`
for *everyone* until StoreKit answers, so the gate is `PremiumStatusProviding.isConfirmedFree` —
`hasResolvedStatus && !isPremium`. A subscriber never sees the screen; an unresolved status, or a
thank-you product the store has not priced yet, leaves the offer pending for the next save rather than
spending it blind. The debug premium override sets `isPremium` but not `hasResolvedStatus` — it is
not an answer from the store.

**The screen is deliberately not `PaywallInsightsPreviewView`.** That paywall sells a choice of plans.
This one sells one product, and its weight is on recognition and support rather than on a feature
list: a thank-you, a countdown, one *support* card in the What's New sheet's voice — what going
Premium does for a very small team, the paywall's four feature lines and an "And more…" line
(`thank_you_offer.features.more` — the four are the headlines, not all of Premium) folded behind one
`PREMIUM` capsule (`SharedUI/PremiumBadge`) that opens on a tap and scrolls itself into view, and an
invitation to write back — and one button that names the price and purchases through
`SubscriptionManager`, with the renewal line above it and the paywall's restore / terms / privacy
row beneath, as any auto-renewing purchase needs. The
saving is worked out only to decide whether to present at all; the screen does not put a
struck-through price in the reader's face. Success closes the screen. Presented as a full-screen
cover after the saved-reflection celebration, held back the same ~0.8 s the Health prompt is, for the
same reason.

**The screen opens on the reader's own journal.** `ThankYouOfferJourney` is read from the store on
appear — never written anywhere — and gives the hero its cast: the emojis actually saved on their
reflections (a custom emoji they picked, not the catalogue's), most recent day first, each once, at
most eight. `ThankYouOfferHeroView` puts them in orbit around the gift, the onboarding welcome's
picture with the reader's faces in it. Under the title, chips carry their numbers: days logged
(counting up from zero, reusing `insights.tag.day_count`), the month they first logged
(`thank_you_offer.journey.since`), and the current run when it is two days or more (reusing the saved
card's streak string; same `MoodStreakCalculator` rule). One clock drives the hero — entrance and
drift are both functions of time since appear, so nothing can fall out of step — and Reduce Motion is
the same drawing with the clock stopped at the end. The sections below arrive one after another
through `staggeredAppear`. A journal with nothing in it (the debug menu on a fresh install) shows the
gift alone and no chips. The chips wear the accent, like the countdown: the recognition should read
before the ask does. The hero, the chips, the message and the whole support card (feature list
closed) fit above the footer on a 6.1" phone without scrolling — the countdown shares the close
bar's row rather than taking a row of its own, and the message stops at the discount because the
card names what Premium is. That fit is the sizing constraint on the hero; keep it when changing
anything above the card.

**The countdown is a real deadline.** `markShown` banks `thankYouOffer.deadline` the first time the
screen is shown — three days out (`ThankYouOffer.window`) — and never moves it. Both the screen's
countdown and the Settings entry run on it, through one `ThankYouOfferView.countdownText`: while the
window is open and the reader is still confirmed free, the **Settings tab** carries
`ThankYouOfferSettingsCard` right under the subscription card, with the same clock, one tap back to
the offer; when it closes, or the reader is premium, the card is gone and the app stops offering.
(The card first lived on the subscription screen one level down, where a reader who had just
closed the offer would not think to look.) `SettingsView` observes `thankYouOffer.hasShown`, so the
card appears the moment a save starts the clock on a tab that is already built. Every real way onto
the screen banks the deadline before presenting; a screen with none has no clock to show, so the
countdown chip is left out rather than claiming the offer has ended — which is what the Debug Tools
button, opening the screen without starting the clock, used to show every time. The introductory
offer itself lives in App Store Connect and should not expire sooner than this window can end for
the last reader to update.

**Who qualifies is decided at launch, before anything writes to the slate.**
`ThankYouOffer.recordEligibilityAtLaunchIfNeeded()` runs from `EveryDayEmojiApp.init()`, *before*
`WhatsNewAnnouncement.recordInstallBaselineIfNeeded()` and before onboarding can finish. It reads the
same three signals the What's New sheet reads: `didFinishOnboarding` is set (an existing reader, not a
fresh install); `whatsNew.lastSeenVersion` is empty (the sheet is new in 1.5, so an empty slate means a
pre-1.5 build); and `moodEntryCount` is at least 1 (they logged, not merely installed). The decision is
banked as `thankYouOffer.isPending`, because by the time the save happens the sheet has filled the
slate. The record is idempotent: a pending offer survives later launches, and a shown one is never
re-decided.

**It is spent by a save, not by a launch.** `PostSaveFollowUpCoordinator` presents at most one thing
per save; the offer sits after the first-save prompts (reminder invitation, Health) and *ahead of the
review request*, because it is a one-shot tied to this update and the review recurs on its own
cadence. Marked as shown at the moment of the decision, not at dismissal — a force-quit mid-read is
not a reason to offer twice. Saves made inside onboarding present nothing and do not spend it.

**Or by asking for Premium in the release notes.** The What's New sheet goes to exactly this
audience, and its Premium rows open onto "See Premium". Sending an owed reader from there to the
full-price paywall, a save before offering them the same year for less, would sell them the dearer
product by accident — so `WhatsNewPremiumDestination` sends them here instead, on the same terms the
save path uses (confirmed free, offer priced and cheaper), and the sheet marks the offer shown the way
a save would. It also leads here while the three-day window is open.

**Only readers the store has confirmed are free.** `SubscriptionManager.isPremium` is `false` for
*everyone* until StoreKit answers, so the gate is `PremiumStatusProviding.isConfirmedFree` —
`hasResolvedStatus && !isPremium`. A subscriber never sees the screen; an unresolved status leaves the
offer pending for the next save rather than spending it blind. The debug premium override sets
`isPremium` but not `hasResolvedStatus` — it is not an answer from the store.

**Analytics:** `thank_you_offer_shown` / `_dismissed` / `_feedback_tapped` carry `source`
(`reflection_save`, `settings`, `whats_new`, `debug`); the purchase reports through the ordinary
`subscription_started` / `_completed` / `_failed` with `plan: annual`, since that is what it is, and
`source: thank_you_offer`, which is what tells it apart from the paywall's full-price annual.

**Debug:** Debug Tools shows pending, shown and open, opens the screen on demand, and resets
all three keys. Opening it spends the offer the way a save does: the three-day clock starts — or
starts again, once it has run out — so the countdown and the Settings card can be looked at. The *launch* path needs a pre-1.5 slate: reset What's New too, log once, and relaunch.
The premium override must be **off** to see it from a save. See [`debug-tooling.md`](debug-tooling.md).

**Known limits.** `moodEntryCount` counts UI saves only, which is every save a pre-1.5 build could
make. The product's display name is visible in the App Store's in-app purchase list, so it is named
plainly. A StoreKit configuration Xcode has attached to a simulator overrides the fixture a test
loads, so `SubscriptionManagerTests` asserts the product's shape, not its prices.
