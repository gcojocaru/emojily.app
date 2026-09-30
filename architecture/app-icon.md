# App icon (`Settings/AppIconSettingsView.swift`) — free

*Part of the Emojily architecture reference. Up: [OVERVIEW.md](../../OVERVIEW.md) · Index: [§6 Features](../../OVERVIEW.md#6-features)*

---


Settings → Preferences → **App Icon** lets people switch between the primary icon and four bundled
alternates. Gallery taps update an in-screen preview; the app calls `UIApplication` only after the person
taps **Apply Icon**, so browsing choices does not repeatedly trigger the system confirmation. The view
model reads the installed alternate icon from iOS, which remains the source of truth rather than duplicating
the selection in preferences.
The asset catalog registers `AppIcon-Laughing`, `AppIcon-Friends`, `AppIcon-AllGood`, and `AppIcon-Glam`
for both production and development app targets.
