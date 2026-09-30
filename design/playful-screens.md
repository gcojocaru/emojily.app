# Playful screens

*Part of the Emojily design reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · [§11 Design system](../../OVERVIEW.md#11-design-system)*

---

Most of Emojily is quiet on purpose: Today, Calendar, Insights and Settings are glass cards on a
dotted ground, and the mood is the loudest thing on them. A few screens are allowed to be louder —
the ones that mark a **moment**. This is how those screens are built, so a new one looks like it
belongs with the rest and not like a one-off.

The three reference implementations, in the order they were built:

| Screen | Moment | Files |
| --- | --- | --- |
| Thank-you offer | A reader who was here before 1.5 | `ThankYouOffer/ThankYouOfferView.swift`, `ThankYouOfferHeroView.swift` |
| Week-one card | Seven logged days | `Subscription/FirstWeekOfferView.swift`, `FirstWeekOfferHeroView.swift` |
| What's New | A release | `WhatsNew/WhatsNewSheetView.swift`, `WhatsNewHeroView.swift` |

The shared pieces live in `SharedUI/CelebrationMotion.swift` (`CelebrationTiming`, `MoodAurora`,
`.revealed(_:order:reduceMotion:)`) and `SharedUI/MotionSystem.swift` (`MotionPolicy`,
`CelebrationRingEffect`, `.staggeredAppear`). Reach for those before writing a curve or a glow of
your own.

**When not to use it.** Everyday screens, forms, errors, anything a reader passes through several
times a day. A celebration that happens every time stops being one, and motion on a screen people
use to get something done is a tax on them.

## The shape of the screen, top to bottom

**1. The ground.** `AppScreenBackground()` with `MoodAurora(colors:)` over it — three blurred blobs
in mood colours, drifting slowly. Pass the colour the screen is *about* first; it fills the largest
blob. The week-one card passes the week's colours, most felt first; the release notes pass their
highlights' colours in ring order.

**2. The hero.** One picture that is about the moment — the reader's own emojis where there are
some (the week's seven, closing a ring; their recent faces, orbiting a gift), the release's own
features where there are not. The rules every hero follows:

- **One clock.** A `TimelineView` measures seconds since `appearedAt` and draws the whole scene as a
  pure function of that number. There is no animation state to fall out of step with the picture.
  Use `CelebrationTiming.progress(_:delay:duration:)` for each beat, `easeOutBack` for things that
  land (it overshoots and settles, like a spring), `easeInOut` for things that are drawn.
- **Things are set down, not faded in.** Tiles arrive from a little outside their place (or fly
  out from the centre, in the thank-you's orbit), scaled down, and pop into it one after another —
  0.15–0.17 s apart on the rings, 0.07 s in the orbit. On a ring, a stroke drawn in their colours
  follows them round, clockwise from the top.
- **The close is the payoff.** When the last piece lands: `CelebrationRingEffect` rings out from
  the centre, a burst of sparkles and dots flies outwards in the pieces' colours, the glow flares
  and settles, and the number in the middle — days logged, the version — pops in, in heavy
  rounded type with a gradient ink.
- **Then it breathes.** The glow scales a few percent on a four-second cycle and the tiles bob
  gently — only when `MotionPolicy.allowsAmbientLoops`.
- **Once per presentation.** Guard the start with `appearedAt == nil`. A sheet that opens a
  full-screen cover gets `onAppear` again when the cover closes, and the show should not replay.
- **Reduce Motion is the same drawing with the clock stopped:** `scene(at: CelebrationTiming.settled,
  drifting: false)`. Nothing lands, flares or floats, and nothing is missing.
- **Sized to the screen's budget.** The thank-you hero is 176 pt so the whole offer fits above its
  footer; the week-one ring is 264 pt because the ring *is* the card; the release notes' is 150 pt
  because a whole list has to fit under it without scrolling.

**3. Haptics follow the picture.** On a ring, a soft impact as each piece lands and
`.notification(.success)` as it closes; the thank-you's orbit has one soft impact as the gift lands.
Time them against the same clock so the buzz and the landing coincide. Respect
`AppPreferencesKeys.hapticsEnabled`, and play nothing under Reduce Motion — a buzz for an animation
that is not there is noise.

**4. The words wait for the picture.** A title in `AvenirNext-Heavy` 34 (`relativeTo: .largeTitle`)
— Bold 27 where space is tight, as on the thank-you offer — and a line under it in Medium 16. They
arrive with `.revealed(isRevealed, order:, reduceMotion:)` once the hero has mostly landed (1.25 s
on the week-one card), 0.09 s apart, rising 14 pt. Sections further down continue the same `order`.
Where the lines belong to pieces of the picture, pass the hero's own beat as `step:` and start when the
first piece lands: the release notes' rows each arrive as their tile does. Mark the title `.isHeader`. The thank-you offer, which has no
single moment for the hero to land on, uses `.staggeredAppear` at 0.11 s steps instead.

**5. Chips for facts.** Numbers and deadlines about the reader go in capsules: accent text on
`accentSoft` with a small leading symbol (the thank-you's countdown and journey chips), or a mood
pill — the mood colour as a 16 % fill and 40 % stroke, the text in `textPrimary` — when the fact is
a mood (the week-one card's sentence).

**6. Cards for content.** `AppSurfaceCard(cornerRadius: 24)` behind each section, 16 pt inside.
Where a card stands for something with a colour, lead with a **tile**: the surface fill, a 14 % wash
of the mood colour and a 55 % stroke of it, with a symbol in the mood's `inkColor` (an emoji brings
its own colour). `WhatsNewGlyphTile` is the symbol version. The same tile in the hero and on the
card is what makes the picture read as a table of contents.

**7. Premium, said plainly.** A Premium thing wears `PremiumBadge` — the one `PREMIUM` capsule, the
same on the paywall, the recap archive and here. The way in is a button that says "See Premium",
never a price (prices belong to the paywall and to the thank-you offer's own button), and it opens
the paywall with both a `PremiumFeature` source, for analytics, and a `PaywallContext`, so the
paywall leads with the thing the reader was looking at. A subscriber sees a line saying it is
included instead of an offer to buy it again.

**8. Folding the rest away.** When there is more than the screen should lead with — the thank-you's
feature list, the release notes' smaller updates — fold it behind one row: a symbol in an
`accentSoft` circle, a title, a count if it helps, and a chevron that turns 180°. The row is the
toggle and at least 44 pt tall. The lines drop in with `.opacity.combined(with: .move(edge: .top))`
inside a `.clipped()` container, and after 80 ms the scroll view brings them up so the reader sees
what they asked for.

**9. The way out is there from the first frame.** Buttons sit in `.safeAreaInset(edge: .bottom)`
on `.ultraThinMaterial` and never wear `.revealed`: the animation is a reward to watch, never a wait
before you can leave. When the screen asks for something, saying no takes the same effort as saying
yes — a full-size secondary button, plainly worded.

## Colour

- **Mood colours** (`EmotionQuadrant.accentColor`) are for fills, washes, rings and light. The
  bright-days yellow cannot carry white text or a thin glyph.
- **`inkColor`** is the mood colour as ink — for symbols and type drawn in a mood on a light surface.
- **`onAccentColor`** is the ink for text *on* a filled mood colour — dark on yellow, white on the rest.
- **The accent blue** is the app speaking for itself: the release notes' glow and version, chips,
  Premium. A reader's own moment is told in their mood colours; the app's moment in its own.
- Run neighbouring pieces round the palette so no two adjacent ones share a colour — the last and
  the first included, since they meet when a ring closes.

## Accessibility

- **The hero is one element or none.** Either `.accessibilityElement(children: .ignore)` with a
  label that says what it shows (the week's emojis, the version) or `.accessibilityHidden(true)`
  when the words below say it all (the thank-you's orbit).
- **Decoration** — symbols, the aurora, glows — carries `.accessibilityHidden(true)`. A conditional
  hide goes through `.accessibilityHidden(while:)`: `accessibilityHidden(false)` is not neutral, and
  un-hides every decoration beneath it. That is why nothing above these screens hides itself — App
  Lock keeps VoiceOver out as a modal container instead.
- **Combine a card's text** with `.accessibilityElement(children: .combine)` so the badge, the title
  and the detail are one stop; keep its button a separate element.
- **44 pt** for every tap target, including text-only buttons (`.frame(minHeight: 44)` and a
  `contentShape`).
- **Give the audit something to wait for.** Staged entrances mean content arrives over a second or so.
  A screen with a screenshot scenario puts an accessibility identifier on the last thing to arrive,
  and its audit test passes it as `awaiting:`.

## Checklist for a new one

1. Is this a moment, and is it the reader's or the app's? That decides whose colours and whose
   picture.
2. Ground: `AppScreenBackground` + `MoodAurora`, lead colour first.
3. Hero: one clock from `appearedAt`, `CelebrationTiming` curves, a close with
   `CelebrationRingEffect`, ambient motion only under `allowsAmbientLoops`, the settled scene under
   Reduce Motion, started once.
4. Haptics timed to the landings, off under Reduce Motion and when the reader turned them off.
5. Words through `.revealed`; buttons never.
6. Premium through `PremiumBadge` and a paywall opened with a source *and* a context.
7. Accessibility as above, and a screenshot scenario with an audit test if the screen is reachable
   often enough to matter.
