# Emojily App Icon Brief

## Direction
The app's strongest visual signals are:

- cool slate-to-blue backgrounds
- soft dotted texture
- frosted glass cards with white strokes
- a bright blue interactive accent
- warm, friendly emoji illustration as the emotional focal point

That points to an icon built around one clear idea: **a calm emoji orb in front of a frosted daily-tracking card**.

## Why This Fits The App
This concept is grounded in the current UI system:

- Shared theme colors and glass treatment come from `EveryDayEmoji/SharedUI/DottedGradientBackground.swift`.
- The calendar and day-selection language comes from `EveryDayEmoji/Calendar/DayCellView.swift`.
- The mood-first interaction comes from `EveryDayEmoji/EmotionSelection/EmotionSelectionEmojiPickerSection.swift`.
- The onboarding illustrations already pair daily tracking with soft emoji-forward visuals.

## Primary Prompt
Use this prompt with your image model of choice:

```text
Design a premium iOS app icon for “Emojily”, a daily mood-tracking app. Create a single centered composition inside an iOS app icon rounded square. The background should be a soft cool gradient in light slate, mist blue, and a subtle warm peach tint, with a refined dotted texture and gentle glow. In the center, show a frosted glass calendar card with smooth rounded corners, translucent white layers, subtle inner highlights, and a crisp white stroke. On the calendar grid, highlight one selected day with a vivid electric blue accent. In front of the card, place one warm glossy emoji face, calm and friendly, slightly smiling, with soft dimensional lighting. The overall style should feel modern, minimal, polished, and emotionally warm, combining glassmorphism with soft 3D illustration. Keep the silhouette bold and readable at small sizes. No text, no border, no transparency, no busy scene, no multiple floating objects.
```

## Negative Prompt
```text
Avoid rainbow gradients, heavy purple bias, childish sticker style, kawaii proportions, excessive sparkles, multiple emojis, text, tiny details, photorealism, hard shadows, black background, neon cyberpunk style, flat clip-art style, and cluttered compositions.
```

## Variants Worth Trying
- Calendar-first: make the glass daily card larger and the emoji smaller, if you want the "daily tracking" concept to read first.
- Emotion-first: enlarge the emoji and simplify the card behind it, if you want stronger App Store shelf recognition.
- Blue-first: push the accent blue stronger and reduce peach, if you want the icon to match the in-app UI more strictly.

## Selection Checklist
Pick the candidate that still reads clearly when scaled down:

- The emoji face is recognizable at 60 px.
- The glass card still reads as one shape, not noise.
- The blue selected-day accent is visible but not dominant.
- The background feels premium, not magical or candy-like.
- The icon looks related to the app UI, not just the onboarding art.

## Local Concept
First local vector concept:

- `docs/branding/everydayemoji-app-icon-concept.svg`

This is a directional mock, not a final production icon. Use it as a reference image or as a composition guide for generated variants.
