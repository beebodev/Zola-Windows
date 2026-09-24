# P3PRE Audit 07 — Visual Tokens

K7 values are copied, not re-sampled. Contrast was recomputed against `#080808` and matches K7 exactly.

## Colour table

| Proposed key | Brush key | Hex | Role | Contrast vs `#080808` |
|---|---|---|---|---|
| `ZolaBackgroundColor` | `ZolaBackgroundBrush` | `#080808` | Window / scene background | — |
| `ZolaAmberPrimaryColor` | `ZolaAmberPrimaryBrush` | `#FFD37A` | Wordmark, tagline, mantra, menu labels, HUD values, time, footer, active VU ticks, dock icons | 14.16 |
| `ZolaAmberMutedColor` | `ZolaAmberMutedBrush` | `#8A6A2A` | Section headers, Core Systems icon strokes, dock separator | 3.98 |
| `ZolaAmberDarkColor` | `ZolaAmberDarkBrush` | `#5A4820` | Dividers at 0.5 alpha, inactive VU ticks, location outline at 0.8 alpha. Not for text. | 2.27 |
| `ZolaAlertGlowColor` | `ZolaAlertGlowBrush` | `#FFE7A5` | ALERT glow override (§6) | 16.43 |
| `ZolaPresenceAmberColor` | `ZolaPresenceAmberBrush` | `#FFD05A` | Particles; SVG-era eye glow | — |
| `ZolaPresenceGoldCoreColor` | `ZolaPresenceGoldCoreBrush` | `#FFF0B0` | SVG-era chest highlight | — |
| `ZolaPresenceGoldDimColor` | `ZolaPresenceGoldDimBrush` | `#D89123` | SVG-era outer ring | — |
| `ZolaPresenceSkinHoloColor` | `ZolaPresenceSkinHoloBrush` | `#B56F24` | SVG-era skin base | — |

Muted amber at 3.98:1 is below WCAG AA 4.5:1 for small text. K7 uses it for 7sp section headers. Recorded for Q-N. The value is not changed.

`ObsidianSurface #141414`, `ObsidianAccent #C4A882`, and `ObsidianTextPrimary #E8DDD0` are not in the HUD/dock token set. They are not proposed here.

Phase 4: the emissive JPEG peaks at about 31/255 (Phase 3). The baseline Helix render is darker than the Android reference (`P3PRE-AUD-18`). The glow the model shows comes from its textures plus `PhongMaterialCore.EmissiveColor`, not from these tokens. The `Presence*` colours were for the SVG layers K1 retired. They do not recolour the GLB.

## Type table

`FontFamily` is the form that rendered in the spike: an absolute file path, `#`, then the family name. A repo-relative `ms-appx` form was not tested. Size is `K7 size × S`. S is Q-N and is not chosen here.

| Style name | Family file | FontWeight | CharacterSpacing | LineHeight | Foreground | Size |
|---|---|---|---|---|---|---|
| `ZolaWordmarkStyle` | `rajdhani_semibold.ttf#Rajdhani SemiBold` | 600 | 176 | — | `ZolaAmberPrimaryBrush` | `34 × S` |
| `ZolaWordmarkOrbitronStyle` | `orbitron_medium.ttf#Orbitron Medium` | 500 | 176 | — | `ZolaAmberPrimaryBrush` | `34 × S` |
| `ZolaTaglineStyle` | `rajdhani_semibold.ttf#Rajdhani` | 600 | 214 | 9 × S | primary | `7 × S` |
| `ZolaMantraStyle` | `rajdhani_regular.ttf#Rajdhani` | 400 | 125 | 10 × S | primary | `8 × S` |
| `ZolaSectionHeaderStyle` | semibold file | 600 | 286 | — | muted | `7 × S` |
| `ZolaRowLabelStyle` | regular file | 400 | 100 | — | primary | `8 × S` |
| `ZolaRightHeaderStyle` | semibold file | 600 | 143 | — | muted | `7 × S` |
| `ZolaRightValueStyle` | semibold file | 600 | 100 | — | primary | `10 × S` |
| `ZolaTimeStyle` | semibold file | 600 | 0 | — | primary | `10 × S` |
| `ZolaFooterStyle` | regular file | 400 | 0 | — | primary | `7 × S` |

`shots/fonts.png` shows 1× lines only a few pixels tall and a readable 2× pair. The first wordmark is Rajdhani SemiBold. The second is Orbitron Medium. Q-M and Q-N stay open.

SemiBold was applied both as the family name `Rajdhani SemiBold` and as `FontWeight` 600 on `Rajdhani`. Both wordmark lines drew. Which of those two mechanisms selected the SemiBold file was not isolated.

## Where tokens would live

WinUI 3 keeps a shared dictionary in `App.xaml` `Application.Resources`, merged beside `XamlControlsResources` (`App.xaml` 7–12). A `ResourceDictionary` of `Color`, `SolidColorBrush`, and `Style` resources is the usual single source. Nothing like that exists today.

`Zola.Client` defines no custom colours or fonts. `MainWindow.xaml.cs` `BubbleBrush` (905–924) reads theme brushes and falls back to hardcoded `Color` values. Those are chat-bubble fills, not HUD tokens. They would clash with a fixed obsidian palette only where the bubble still uses `ThemeResource` / `AccentFillColorDefaultBrush`.

## Light / dark theme

`App.xaml` does not set `RequestedTheme`. The window follows Windows. `ThemeResource` keys in use: `DividerStrokeColorDefaultBrush`, plus the four system fill brushes in `BubbleBrush`. Under a fixed `#080808` dictionary those theme brushes still flip with the Windows theme unless the window sets `RequestedTheme="Dark"` or the bubble code stops reading them.
