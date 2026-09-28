# P3-LOOK Progress — Fidelity

## Branch

- Branch: `p3-look-fidelity`
- Base SHA: `4609c697937d2a5300897ec4575c02b38357f720` (plan v1.4 commit; branch point)
- Plan v1.4 commit SHA: `4609c697937d2a5300897ec4575c02b38357f720`
- Recorded HEAD before the plan commit: `e7824f7cefb55c8341a606486cdc14aeca2cb70d` (`docs: record P3-RENDER merge SHA`), a direct successor of P3-RENDER merge `f61e1ae014bdf22bc0cab04e128bd93f0ffdebe5`
- Plan source SHA-256 (v1.4): `79459077886624b26251231e7258b1db04ea1212f02328dbc66e4c0f06df7c99` (matched)
- Plan source SHA-256 (v1.5): `251b9e69f09cd3f4e2290e9bf8ee0af8dfe7c053d7e0d740c5ab8ba67665287d` (matched; on this branch, not a separate `main` commit)
- Plan source SHA-256 (v1.6): `8d143a8f68bee787b683f3831b9e5ff4b3f7029d53eacfdf809d64d0e842db71` (matched; on this branch)
- Prompt: P3-LOOK v1.1
- Addendum: P3-LOOK Tone Mapping v1.0 / `P3-D19`
- Addendum: P3-LOOK Finish the Track v1.0 / `P3-D20` / `P3-D21`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Plan v1.4, Branch, and Progress Document | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Shell (dock, notice, polish) | COMPLETE |
| 4 | Build: PresenceLook, Rim, Bloom, and the Debug Reload | COMPLETE |
| 5 | Tuning Rounds | COMPLETE (look approved) |
| T1 | Tone map: Read and Check | COMPLETE |
| T2 | Tone map: Build the Pass | COMPLETE |
| T3 | Tone map: Retune with Android reference values | COMPLETE (look approved) |
| 6 | Backdrop / decoration (`P3-D21`) | deferred — no glow, rings, brackets; particles → Track 5 |
| 7 | Texture Size and Memory | replaced by finish-addendum Step 3 (recorded) |
| 8 | Smoke Test | COMPLETE |
| 9 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** `PresenceLook.cs`, `PresenceBackdrop.cs`, `PresenceView.cs`, `MainWindow.xaml(.cs)`, `Themes/ZolaTokens.xaml`, plan (now v1.6), and this progress document. v1.5 / `P3-D19` also allows `Presence/Shaders/AcesTonemap.hlsl`, `Presence/Shaders/AcesTonemap.cso`, `Presence/PostEffectToneMap.cs`, and **one** `EmbeddedResource` line in `Zola.Client.csproj`. `P3-D21` removes backdrop/decoration from this track. No `ZolaDisplayState`, voice/session/RPC files, `App.xaml(.cs)`, or the GLB. No packages. No image files under `windows-client/`.
- **G-ARCH:** The build plan is truth. A conflict that affects a task is a stop.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** Track 2 and Track 3 behaviour stays, including load order, `LoadAsync` coalescing, generation checks, `InvalidateScene()` only on debug reload or failed validation, pause/resume, lock reuse, and the fallback.
- **G-COMMENT:** One `// P3-LOOK: … — P3-D0X/P3-D1X` (XAML: `<!-- P3-LOOK: … -->`) per logically distinct changed block.
- **G-STOP:** Stop after each phase and after every tuning round. Wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-LORE-SCOPE:** `ROADMAP.md`, `DESIGN_DECISIONS.md`, and `OPEN_QUESTIONS.md` are out of scope, including closeout. The Phase 1 plan replacement is a plan commit, not a lore update.
- **G-NO-CROSS-SCOPE:** Android Zola, Ava, and the P3PRE spike folder are out of scope. The two reference PNGs may be viewed.
- **G-TOKENS:** UI values in `ZolaTokens.xaml`. 3D look values as named constants in `PresenceLook.cs`. No colour or number literals in code bodies. K7 colours from tokens where one applies.
- **Framing (developer-approved Phase 4/5 addition):** camera position, look direction and FOV live in `PresenceLook.cs` and the F12 JSON (same all-or-nothing validation, with ranges). Unchanged values to start. Tune so the whole bust is visible, the base is inside the window, the chest diamond is about two-thirds down, and there is room below her for Phase 6 floor rings. HUD and hidden dock stay clear. Holds at 900×640, 1280×800 and maximized; any round that changes framing includes all three. No user camera control — Track 3 fixed-view rules still apply.
- **G-RESTRAINT:** She is the subject. Backdrop stays dim. Bloom must not wash dark surfaces or blur her face. Prefer calmer.
- **G-BUDGET:** Static GPU with bloom on and nothing moving ≤ 1% averaged over 60 s (Audit 03 / P3-RENDER A7). If a post-effect forces continuous rendering, stop BLOCKED.
- **G-DEBUG:** `Ctrl+Shift+F9` blink, `F10` reload, `F11` morph, `F12` look JSON (all-or-nothing). `#if DEBUG` only. JSON is never read in Release and never committed. F8 texture-size plan removed.
- **G-FEEDBACK-SCOPE:** Tuning feedback changes values, not scope.
- **Live window (developer-approved):** after each tuning round, leave the leading variant live — or the one named. Say which one is live. Do not restore an earlier look unless asked.
- **G-DEPS:** None, except `fxc.exe` from a Windows SDK already installed on this machine, used once to compile `AcesTonemap.hlsl`. No install, no package, no compile step in the project. If `fxc` is absent, stop BLOCKED.

## Phase 1

Working tree was clean on `main`. Pulled; already up to date. HEAD before the plan commit: `e7824f7cefb55c8341a606486cdc14aeca2cb70d` (matches the prompt).
Plan v1.4 SHA-256 matched. `git diff` against the committed v1.3 file showed only the v1.4 surface: `P3-D11` dock line; new `P3-D17` and `P3-D18`; Track 4 dock/notice, iteration aid, memory, and exit criteria; Track 5 blink-side note; lore closeout and checklist `P3-D18`; deferrals row (dock auto-hide removed); version footer.
Committed on `main` and pushed. Branch `p3-look-fidelity` created from that commit. No source files modified.

## Phase 2

Read in full: `PresenceView.cs`, `GlbTextureLocator.cs`, `MorphTarget.cs`, `SessionLockWatcher.cs`, `MainWindow.xaml`, `MainWindow.xaml.cs` (1179 lines), `ZolaTokens.xaml`. Binding plan sections, Audit 03 Lighting / fidelity, Audit 04 §6, SYNTHESIS `-16`/`-18`/`-25`/`-26`, P3-SHELL / P3-RENDER progress, lore files (G-LORE-SCOPE: no edits). Viewed both reference PNGs.

No source files modified. Scripts in `%TEMP%\p3look\`.

### 1. Bloom (KC4)

`HelixToolkit.WinUI.SharpDX.PostEffectBloom` is an `Element3D` (XML `seealso Element3D`). Attach the same way lights attach: `_view.Items.Add(new PostEffectBloom { … })` once, next to `EnsureLightsAndEnvironment`. It is not a viewport property.

Documented properties (WinUI XML 3.1.2): `EffectName`, `ThresholdColor`, `NumberOfBlurPass`, `BloomExtractIntensity`, `BloomPassIntensity`, `BloomCombineIntensity`, `BloomCombineSaturation`. Core type `PostEffectBloomCore` is labelled "Outline blur effect" and "Must not put in shared model across multiple viewport".

Nothing in the XML says bloom starts a continuous render loop. Frames are still gated by `IRenderHost.IsRendering` (XML: "whether this instance is rendering") and `InvalidateRender`. Track 3 already sets `RenderHost.IsRendering` from `_pauseReasons` and Ready. Bloom runs only on frames that already render. Pause (`IsRendering = false`) should still stop work. **Prove it in Phase 4** with the 60 s static GPU measure and a minimize check. If bloom forces a loop, stop BLOCKED per G-BUDGET.

### 2. Rim light

Use a third `DirectionalLight3D`, same type as key and fill. Camera is at `(0, 0.05, 3.15)` looking `(0, 0, −3.372)`, so she faces +Z. Key already comes from front-upper-left `(−0.3, −0.8, −1)`. Rim comes from behind, slightly up: direction toward +Z so it grazes cheekbones, collarbones and hair tips. Colour: cream-white, conservative (G-RESTRAINT). No `PointLight3D` — direction is enough and matches the existing lights. Values live in `PresenceLook.cs`.

### 3. Backdrop (KC5)

`HelixToolkit.Geometry.MeshBuilder.AddQuad(...)` with UVs for the glow (large enough that vertical-FOV 35° never shows an edge, including maximized widescreen). `MeshBuilder.AddCylinder(p1, p2, radius, theta)` with a short vertical span as the floor disc (no `AddDisk`). Convert with `ToMeshGeometry3D()`. Material: `PhongMaterialCore` or `PBRMaterialCore` with an in-memory `TextureModel(Stream)` — radial amber gradient for the glow, concentric rings for the disc, K7 amber bytes, no files.

Join in `AttachOnUi` under the same generation check as the bust: build bytes off the UI thread with the import (or a worker step), attach on the dispatcher after `_host.Clear(true)` and the bust `AddNode`. Keep them behind / under her (`ModelMatrix`). They go on `_host` so reload detaches them with `Clear(true)`. Window clear stays `#080808`.

### 4. Texture downscale (KC10)

Built-in route, no package: `Windows.Graphics.Imaging.BitmapDecoder.CreateAsync` on an `InMemoryRandomAccessStream` of each JPEG, then `BitmapTransform` (`ScaledWidth`/`ScaledHeight` 1024, `InterpolationMode.Fant`), `GetPixelDataAsync`, re-encode to a stream, `new TextureModel(stream, false)`.

Runs in `ImportOnWorker` (already `Task.Run`), on the four maps: imported Phong `DiffuseMap` / `NormalMap` / `EmissiveMap` plus `GlbTextureLocator` `Image_1`. The GLB file is not written. `Ctrl+Shift+F8` will `InvalidateScene()` + `LoadAsync()` with a size flag.

### 5. Resource ownership (KC11)

| Object | Owner | IDisposable / release | Evidence |
|---|---|---|---|
| `HelixToolkitScene` / imported `GroupNode` root | `ImportBundle` until `AttachOnUi`; then `_host` | No `Dispose` in XML. GPU released by detach. | `AttachOnUi` `AddNode`; `Clear(true)` XML: "If detach = false, then developer must manage the life cycle" |
| `BoneSkinMeshNode` + morph weights | child of imported root; `_morph` is a view | `SceneNode.Detach`: "release all graphics resources" | Helix XML `SceneNode.Detach` |
| Imported `PhongMaterialCore` maps (`DiffuseMap`, `NormalMap`, `EmissiveMap`) | imported material, then copied onto new `PBRMaterialCore` | `TextureModel` has **no** `Dispose` in XML | `TextureModel` XML: loader + Guid only |
| `PBRMaterialCore` built in `AttachOnUi` | assigned to `morph.Material`; node owns the reference | `MaterialCore` has no `Dispose` in XML | `PresenceView` 505–522 |
| `RoughnessMetallic` `TextureModel` | `ImportBundle` then the PBR | no `Dispose`; `DiscardBundle` only drops the ref | `DiscardBundle` 759–767 |
| `_envTexture` + lights + `EnvironmentMap3D` | `PresenceView`; created once in `EnsureLightsAndEnvironment` | kept across reloads **deliberately** | `_lightsAdded`; Track 3 memory findings |
| `DefaultEffectsManager` | `_view.EffectsManager`, constructed in the ctor | `IDisposable`; disposed in `PresenceView.Dispose` | lives across reloads — correct (device/shaders) |
| `Importer` | worker, `using` | `IDisposable` (used with `using`) | `ImportOnWorker` 471 |
| Viewport / `_host` | `PresenceView` | `_host.Clear(true)` on invalidate and dispose | `InvalidateScene` 283; `Dispose` 330 |
| Phase 6 backdrop textures + nodes | `PresenceBackdrop` / `PresenceView`; attached on `_host` | same as the bust: detach on `Clear(true)`; drop managed refs on reload and on close. No `TextureModel.Dispose`. | this table |
| Stale generation | `RunLoadAsync` `IsCurrent` | `DiscardBundle` (drop refs, never attach). No GPU created. | 438–442, 446–451 |

Formal soak vs 25% and any extra `Dispose` stay in Phase 7.

### 6. Composer accent (KC9)

WinUI `DefaultTextBoxStyle` (`generic.xaml`) uses these lightweight keys. The focused underline is `TextControlElevationBorderFocusedBrush` (bottom stop is `SystemAccentColorLight2`). Scope replacements on `ZolaComposerStyle`:

- `TextControlBorderBrush`
- `TextControlBorderBrushPointerOver`
- `TextControlBorderBrushFocused`
- `TextControlElevationBorderFocusedBrush`
- `TextControlBorderThemeThicknessFocused`
- `TextControlSelectionHighlightColor`

Caret is **not** a resource. It is `TextBox.CaretBrush`. Set that on `ZolaComposerStyle`. Amber tokens only.

### 7. Dock and notice wiring (KC7 / KC8)

**Dock — `UpdateDockVisibility()` (new, only decider).** Call from:

- `RootGrid` `PointerMoved` / `PointerExited` (new)
- `DockHost` `GotFocus` / `LostFocus` (new)
- panel open/close: `OnConversationClick` 1072, `HideConversation` 1097, `OnSessionsToggle` 712, `HideSessions` 748
- `UpdateChrome()` 687 (covers `_streaming`)
- `Window.Activated` (new) — evaluate the pointer immediately; do not wait for the next move. **No `Activated` hook exists today.**

**Notice — `UpdateNoticeVisibility()` (new, only decider).** Triggered by `RegisterPropertyChangedCallback(TextBlock.TextProperty, …)` on `StatusText` and `DetailText`, plus `UpdateChrome()`. **No writer is edited.**

`_lastTurnErrored` does not exist yet. Planned assignments only:

| Action | Site | Lines |
|---|---|---|
| **Set** | `FinishTurn` when `outcome == "error"` (the `StyleLive("error", …)` path) | 561–567 |
| **Clear** | `OnSubmitAcknowledged` (turn accepted; typed and voice) | 399–418 |
| **Clear** | `ClearTranscript` (new session and resume already clear the transcript) | 910–918; callers 768, 823 |

Not cleared by wake, mic, recording, or a transcript that never submits. Nothing else in those methods changes.

`StatusText.Text` writers (unchanged): 130, 138, 159, 184, 190, 228, 251, 273, 312, 348, 365, 372, 410, 429, 444, 454, 488, 549, 567, 597, 769, 782, 813, 832, 846.

`DetailText.Text` writers (unchanged): 131, 172, 583, 600, 736.

### 8. Glyph sheet (KC9)

`P3-LOOK_glyphs.png`. Segoe Fluent Icons at 24 px (`ZolaDockIconSize`), `#FFD37A` on `#080808`. Names from the Microsoft Fluent Icons list.

Voice/Text: `U+E8D4` Contact2 (current), `U+E8AB` Switch, `U+E765` KeyboardClassic, `U+E720` Microphone, `U+E7F5` Speakers, `U+E8BD` Message.

Sessions: `U+E8A5` Document (current), `U+E8F1` Library, `U+E8B7` Folder, `U+E81C` History, `U+E716` People, `U+E8FD` BulletedList.

### 9. Current look, round 0

First composite had a title-bar white bar, unmatched framing, and Android HUD in the crop. Redone under Phase 3 (KC2) before Phase 4 — see **Round 0 redo (KC2)** below. `P3-LOOK_round0.png` is the redone file.

### 10. Flags

None that block Phase 3. Bloom vs continuous render is measured in Phase 4, not assumed. `Window.Activated` and the two visibility methods are new work, not conflicts. `ROADMAP.md` still says Phase 3 is not started (lore out of scope).

## Phase 3

Source: `Themes/ZolaTokens.xaml`, `MainWindow.xaml`, `MainWindow.xaml.cs` only. Build: `"C:\Program Files\dotnet\dotnet.exe" build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` — 0 warnings. Looked at every PNG before it was copied into this folder.

### Tokens

- `ZolaMantraIndent` `100,0,0,0`
- `ZolaLayerDecoration` `5`
- `DockRevealMargin` `12`, `DockHideDelaySeconds` `2`, `DockFadeMilliseconds` `180` (was `DockRevealZoneHeight` `120`; amended during Phase 8)
- `NoticeHoldSeconds` `4`
- `ZolaGlyphVoiceText` `U+E8AB` (Switch), `ZolaGlyphSessions` `U+E81C` (History)

### Composer accent (KC9)

WinUI `TextBox` has no `CaretBrush` (`WMC0090` / `CS1061`). The caret follows `Foreground` (`ZolaTextPrimary`). `Style.Resources` is invalid (`WMC0011`), so the lightweight keys live on `Composer.Resources`:

- `TextControlBorderBrush` → `ZolaAmberDark`
- `TextControlBorderBrushPointerOver` → `ZolaAmberMuted`
- `TextControlBorderBrushFocused` / `TextControlElevationBorderFocusedBrush` → `ZolaAmberPrimary`
- `TextControlSelectionHighlightColor` → `ZolaAmberMuted`

Focused zoom (`P3-LOOK_phase3_composer_focus.png`): caret visible, amber underline, **0** system-blue pixels, 589 amber-ish.

### Dock (KC7 / P3-D17)

`UpdateDockVisibility` is the only decider. `SetDockRevealed` is its helper. `DockHost.Opacity` is written only there. Search-confirm: no other dock show/hide path. Reveal on pointer-in-footprint (see Phase 8 amendment), focus inside `DockHost`, overlay, sessions, or `_streaming`. Otherwise a 2 s delay, then fade 180 ms (snap if `UISettings.AnimationsEnabled == false`). Hidden dock is `Opacity=0` and `IsHitTestVisible=false`. `SetCursorPos` alone does not raise `PointerMoved`; the capture script uses `mouse_event` plus `Activated` → `QueryCursorInRoot`.

### Notice (KC8 / P3-D18)

`UpdateNoticeVisibility` is the only decider. `SetNoticeShown` is its helper. No `StatusText` / `DetailText` writer was edited. `_lastTurnErrored` set in `FinishTurn` when `outcome == "error"`; cleared in `OnSubmitAcknowledged` (after the early return) and `ClearTranscript`. Sticky = `_unreachable|_switchInFlight|_historyPending|_lastTurnErrored`. `DetailText` only while sticky. Overlay open: notice is `Left` / width = leftover so 900 px does not cover it.

### Screenshots

| File | What it shows |
|---|---|
| `P3-LOOK_phase3_900_overlay_notice.png` | 900×640 client. Overlay open. `Session ready.` centred in the leftover width, clear of the panel. Mantra indent 100. Switch + History glyphs. |
| `P3-LOOK_phase3_composer_focus.png` | Composer zoom, caret in the box, amber chrome, no system accent. |
| `P3-LOOK_phase3_dock_hidden.png` | 1280×800 client. Dock gone. Full bust, diamond and shoulders. |
| `P3-LOOK_phase3_dock_shown.png` | 1280×800 client. Dock visible. Voice/Text = Switch `E8AB`, Sessions = History `E81C`. |

### Round 0 redo (KC2)

Script only, `%TEMP%\p3look\remake-round0.ps1`. Client-area capture (`GetClientRect` + `ClientToScreen`), 1280×800 at screen 88,71. No title-bar bar. Looked at the capture, the two bust crops, and the composite before replacing `P3-LOOK_round0.png`.

Same framing both sides: top of hair to below the chest diamond, shoulders in. Android is bust only (HUD crumbs in the corners filled black; no dock). Windows bust is full, chest and shoulders included. Both scaled to height 720.

Samples by landmark (crop coordinates, then RGB):

| Side | Landmark | Crop xy | RGB | Feature |
|---|---|---|---|---|
| Windows | cheek | 160,340 | 190,118,56 | left cheekbone highlight |
| Windows | hair | 171,34 | 255,219,89 | bun tip |
| Windows | chest | 210,688 | 255,255,207 | diamond centre |
| Android | cheek | 60,250 | 181,122,66 | left cheekbone highlight |
| Android | hair | 135,38 | 255,196,139 | bun tip |
| Android | chest | 100,488 | 255,235,181 | diamond centre |

Windows crop from the hidden client frame: origin 430,18 size 420×770. Android crop from `android_hud_reference.png`: origin 108,80 size 252×658.

| Region | Windows | Android | Audit 03 L9 | Audit 03 Android |
|---|---|---|---|---|
| Cheek | 190,118,56 | 181,122,66 | 204,124,56 | 226,181,116 |
| Hair | 255,219,89 | 255,196,139 | 251,148,66 | 101,58,16 |
| Chest | 255,255,207 | 255,235,181 | 255,255,197 | 255,219,139 |

Samples have no pass/fail (`P3-D13`). The Windows frame is still even: too much ambient/fill, almost no cream rim, bloom off. That is Phase 4.

### Flags

None that block Phase 4. Missing `CaretBrush` is a recorded WinUI gap; the focused underline is amber. Bloom vs continuous render stays a Phase 4 measure.

## Carried from P3-RENDER

- Tune colouring.
- Hide the dock until mouse-over (now `P3-D17`).
- Remove "Session ready" and the session/stored notice from over the bust (now `P3-D18`).
- Revisit memory after reloads alongside the texture-size test, including whether explicit scene disposal is worth adding.

### Memory findings (Track 3)

The soak passed. Private bytes stayed in a band and did not step up per reload.
The reload path releases GPU resources by detaching (`Clear(true)`), and managed memory is left to the garbage collector.
The environment map is kept deliberately.
`DiscardBundle` releases by dropping references; no GPU resources exist before attach.
The steady state after reloads is about 1.3 GB, versus about 790 MB cold.

## Tuning log

| Round | Values changed | Side-by-side | Developer feedback |
|---|---|---|---|
| 0 | current L9 (no look change) | `P3-LOOK_round0.png` (KC2 redo) | |
| 1 | conservative rim + bloom on; L9 lights and framing unchanged | `P3-LOOK_round1.png` | there are white flecks on her face that weren't there before, and she's still orange all over instead of dark skin with amber highlights |
| 2 | 2a Track 3 emissive `(1,1,1,1)`; 2b bloom off; 2c rim off. Face close-ups, same crop. | `P3-LOOK_round2.png` | the rim light causes the flecks |
| 3 | rim off; ambient darker/neutral; fill weaker/desaturated; env cube dimmer/cooler; key unchanged | `P3-LOOK_round3.png`, `P3-LOOK_round3_face.png` | the skin is right now — dark, not orange, no flecks. Keep this ambient, fill and environment as the base. But she's too dark and flat: no highlights on her forehead, cheekbones, nose, lips or neck, the hair has gone brown, and the eyes and diamond are dim compared with Android. |
| 4 | 4A/4B gold key strengths; same dim side-behind rim. Ambient/fill/env held. | `P3-LOOK_round4.png` | take B as the base, and drop the rim (agreed; it lights the mesh dots). The sculpting is right, but she's still far darker than Android, and B is already near white, so there's no headroom. |
| 5 | `keyIntensity` added; 4B colour; rim off; 5A B-dir vs 5B frontal, both 2.8. | `P3-LOOK_round5.png` | take 5B (frontal, keyIntensity 2.8). The dot grid on the forehead is part of her design (Android shows it too); keep it subtle, no action needed. Hair now reads gold; drop hair from round 6. |
| 6 | 5B key held. Emissive + bloom two strengths. Hair dropped. Base glow left for Phase 6. | `P3-LOOK_round6.png` | take 6A. In 6B the diamond loses its outline and the centre line flares into a hot spot on her forehead. 6A keeps the diamond crisp with a soft halo, which matches Android. |
| 7 | 6A base. 7A key shifted to amber gold. 7B adds low amber side fill. Rim off, bloom held. | `P3-LOOK_round7.png` | *(judged from a window that had been restored to 6A; 7B is the base for round 8)* |
| 8 | 7B base. `metallicFactor` / `roughnessFactor` / map toggle. Warm env. 8A 0.3 / 8B 0.55. | `P3-LOOK_round8.png` | Round 8 read as a step back. Highlights too hot and too orange/red; mid-tones and shadows too dark. Android is less saturated (more yellow-bronze) and flatter. |
| 9 | Auto-match vs Android KC2. 7B + metallic off. Best d10 yellow key. | `P3-LOOK_round9.png` | good progress. Keep d10 as the base. |
| 10 | d10 base. Bloom sat 0.25, cream emissive, ambient lift. Rim tried and dropped. | `P3-LOOK_round10.png` | |

## Texture and memory

| Size | Load time | Peak WS during load | Resting WS | Private bytes |
|---|---|---|---|---|
| 2048² | | | | |
| 1024² | | | | |

Developer pick: *(Phase 7)*

| Soak (chosen size) | WS | Private bytes |
|---|---|---|
| start | | |
| after 1–6 | | |
| idle 2 min | | |

Explicit disposal: *(Phase 7, KC11)*

## Discrepancies

- `ROADMAP.md` still says "Phase 3 — not started". Lore is out of scope (G-LORE-SCOPE). It does not change this track.
- In the v1.4 plan, `P3-D16` is listed after `P3-D17` / `P3-D18`. Copied verbatim. Not a deviation.
- WinUI `TextBox` has no `CaretBrush`. Phase 2 planned a style setter. The caret uses `Foreground` instead. Focused border keys are amber.

Flags: none that block tuning. Bloom does not force a continuous loop.

## Phase 4

Developer-approved addition (this proceed): framing is tunable. Camera position `(0, 0.05, 3.15)`, look `(0, 0, −3.372)` and FOV `35` moved into `PresenceLook.cs` unchanged. They are in the F12 JSON under the same all-or-nothing parse, with named ranges. Track 3 fixed-view rules stay: no user camera control; the camera changes only through these constants / a validated JSON apply. Tuning goal: whole bust visible, base inside the window, chest diamond about two-thirds down, room below her for Phase 6 floor rings; HUD and hidden dock stay clear. Holds at 900×640, 1280×800 and maximized. Any round that changes framing includes all three sizes.

`PresenceLook.cs` holds L9 lights (unchanged), conservative rim (cream `220,205,180`, direction `(0.15, −0.25, 1)`), conservative bloom (threshold `0.85/0.78/0.55`, 1 blur pass, extract `0.4`, pass `0.55`, combine `0.28`, saturation `0.8`), and L9 emissive `(1,1,1,1)`.

`PresenceView` creates the rim `DirectionalLight3D` and `PostEffectBloom` once next to the existing lights. `ApplyLook()` pushes the current look onto the camera, lights, bloom and `PBRMaterialCore.EmissiveColor` as one UI-thread operation. `Ctrl+Shift+F12` (`#if DEBUG`) reads `%LOCALAPPDATA%\ZolaClient\debug\presence-look.json`, merges missing keys from the current look, validates every supplied key, and rejects the whole update on any failure. It does not reload the model. Search: no lighting, bloom or emissive literal remains in `PresenceView`.

Build: `"C:\Program Files\dotnet\dotnet.exe" build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` — 0 warnings.

### Static GPU (bloom on)

Same method as P3-RENDER A7: `GPU Engine(pid_*)\Utilization Percentage`, 1 s interval, sum of pid instances.

| Measure | Seconds | Avg | Max |
|---|---|---|---|
| Static, bloom on, nothing moving | 60 | 0.0005% | 0.0311% |
| Minimized | 30 | 0.0000% | 0.0000% |

Minimize still pauses. Bloom does not force a continuous render loop.

### Round 1 side-by-side

`P3-LOOK_round1.png` — KC2 client-area bust crop, same framing and landmarks as the redone round 0. Looked at before saving. Windows samples: cheek `190,118,56` @ 160,340; hair `255,219,89` @ 171,34; chest `255,255,208` @ 210,688. Still even vs Android; rim and bloom are intentionally quiet. Framing unchanged this round, so only 1280×800.

## Phase 5 — Tuning

Round 1 feedback (verbatim): there are white flecks on her face that weren't there before, and she's still orange all over instead of dark skin with amber highlights.

### Round 2 — fleck isolation

Same 1280×800 client framing. Face crop `500,90 280×400` on every panel. One change from the round 1 look per image, via F12 JSON.

| Panel | Change | Flecks |
|---|---|---|
| Round 1 | baseline (rim + bloom) | bright white sparkles on forehead and cheeks |
| 2a | emissive set to Track 3 `(1,1,1,1)` (already the round 1 value) | still there |
| 2b | bloom intensities 0, threshold 1 | still there |
| 2c | rim colour `0,0,0` | **gone** (forehead sparkle disappears) |

`P3-LOOK_round2.png` — four face close-ups. Looked at the faces, the four-up, and forehead zooms before saving.

**The rim light is what adds the white flecks.** Bloom does not remove them. Emissive was already the Track 3 value.

Round 2 confirmed (verbatim): the rim light causes the flecks.

### Round 3 — darker skin, rim off

Env cube tint is now a look value (`envRedBase` / `Span`, `envGreenBase` / `Span`, `envBlueBase`, `envBlueFaceStep`) so F12 can dim and cool it. Defaults stay the old warm cube. Bloom and emissive unchanged.

| Key | Round 1 | Round 3 |
|---|---|---|
| rim | `220,205,180` | `0,0,0` |
| ambient | `90,70,40` | `14,14,16` |
| fill | `180,120,60` | `32,28,24` |
| env cube | `80/140, 40/70, 10+4·face` | `14/18, 14/16, 14+1·face` |
| key | `255,220,170` `(-0.3,-0.8,-1)` | unchanged |
| bloom, emissive | round 1 | unchanged |

Windows landmark samples: cheek `83,51,30` @ 160,340; hair `211,124,58` @ 171,34; chest `228,198,162` @ 210,688.

Looked at the full frame, the face close-up, and the KC2 composite before saving. No white flecks. Sides of the face fall into shadow; amber stays on the key side, hair, eyes and diamond.

Round 3 feedback (verbatim): the skin is right now — dark, not orange, no flecks. Keep this ambient, fill and environment as the base. But she's too dark and flat: no highlights on her forehead, cheekbones, nose, lips or neck, the hair has gone brown, and the eyes and diamond are dim compared with Android.

Developer-approved from now on: when a change could overshoot, show two strengths side by side in the same round.

### Round 4 — sculpt (gentle rim)

Ambient, fill and env held from round 3. Bloom and emissive left for round 5.

| | 4A moderate | 4B strong |
|---|---|---|
| key | `255,218,115` | `255,238,155` |
| key direction | `(-0.3,-0.8,-1)` both | |
| rim | `56,46,32` both | |
| rim direction | `(0.58,-0.2,0.72)` side and slightly behind, both | |

`P3-LOOK_round4.png` — A | B bust, face, hair. Looked at before saving.

**Flecks:** they come back, faintly, on the forehead at this rim (both A and B). Not the bright round-1 sparkles, but they are there at a useful look. Proposal: drop the rim again and get edge highlights from the key (and bloom in round 5) instead of a back light that lights mesh dots.

Cheek landmark (shadow side) A `83,50,26` / B `83,53,29`. Hair landmark A `211,124,46` / B `211,133,54`. B reads slightly brighter on hair and forehead; the sculpt (highlights vs shadow sides) is the same shape on both.

Round 4 feedback (verbatim): take B as the base, and drop the rim (agreed; it lights the mesh dots). The sculpting is right, but she's still far darker than Android, and B is already near white, so there's no headroom.

Developer-approved: add a key intensity multiplier (float, validated range) on top of the key colour so it can go brighter than white while keeping its hue. When a change could overshoot, two strengths stay allowed in the same round.

### Round 5 — key intensity, two directions

`keyIntensity` is a look value (`PresenceLook.DefaultKeyIntensity` `1`, range `0`–`8`, JSON `keyIntensity`). `ApplyLook` writes it onto the key `LightNode.Color` as `Color4` so the hue of `keyR/G/B` can go past byte white. Defaults in `PresenceLook.cs` stay L9; this round's values are JSON only.

4B colour kept (`255,238,155`). Rim `0,0,0`. Ambient, fill and env held from round 3. Bloom and emissive left for round 6.

Probed intensities `1.0` / `2.0` / `2.8` / `3.6` on B's direction. `2.8` is the first that reads gold, not bronze; `3.6` still holds hue. Used `2.8` (G-RESTRAINT).

| | 5A | 5B |
|---|---|---|
| key | `255,238,155` both | |
| keyIntensity | `2.8` both | |
| key direction | `(-0.3,-0.8,-1)` B's | `(0,-0.55,-1)` frontal |
| rim | `0,0,0` both | |

`P3-LOOK_round5.png` — A | B bust, face, hair. Looked at before saving.

5A keeps the side sculpt: gold on forehead, one cheek, nose, lips and neck; the far side stays in shadow. 5B runs the gold down the centre (forehead, nose bridge, lips, chin) with both cheekbones lit; the sides of the face still fall away. Hair is gold rather than brown on both. Eyes, centre line, diamond and base stay for round 6.

Cheek landmark A `196,118,50` / B `212,127,53` @ 160,340. Hair landmark A `255,255,115` / B `255,255,125` @ 171,34. Chest landmark clips `255,255,255` @ 210,688 on both (diamond / chest plane).

**Flecks:** rim is off. The bright white rim sparkles do not return. A regular amber dot grid is visible on the forehead at this key strength (both A and B) — mesh/texture dots catching the brighter key, not the rim. Noted; not the round-1 white flecks.

Round 5 feedback (verbatim): take 5B (frontal, keyIntensity 2.8). The dot grid on the forehead is part of her design (Android shows it too); keep it subtle, no action needed. Hair now reads gold; drop hair from round 6.

### Round 6 — glow (emissive and bloom)

5B key held (`255,238,155`, intensity `2.8`, direction `(0,-0.55,-1)`). Rim off. Ambient, fill and env held from round 3. Key not raised.

Hair dropped this round. Forehead grid left as design.

**Base glow:** the pool of light in the black under the bust, and any floor disc, belong with the Phase 6 floor rings (framing already left room). The bust mesh has no emissive base. The on-chest glow around the diamond is this round (bloom). Left the floor pool.

Gold (not white) was below the old bloom blue threshold (`0.55`), so only the white core extracted. Threshold B dropped so the gold ring can bloom. A stronger probe (4 passes, extract `1.35`, combine `1.15`) washed the face magenta — discarded (G-RESTRAINT).

| | 6A moderate | 6B stronger |
|---|---|---|
| emissive | `2.2, 2.1, 1.85` | `2.3, 2.2, 1.95` |
| bloom threshold | `0.72 / 0.52 / 0.16` | `0.74 / 0.54 / 0.18` |
| blur passes | `3` | `3` |
| extract / pass / combine / sat | `1.05 / 1.0 / 0.85 / 0.85` | `1.15 / 1.05 / 0.95 / 0.7` |

`P3-LOOK_round6.png` — A | B bust, face, diamond. Looked at before saving.

Eyes read hotter and nearer white-gold, with a soft halo (stronger on B). Diamond bloom is larger and softer on B; the line stays sharp. Face is not blurred; dark skin holds. Cheek landmark A `235,128,60` / B `247,130,62` @ 160,340 (up from 5B `212,127,53` — some bloom reaches the cheek sample; the face still reads dark).

Round 6 feedback (verbatim): take 6A. In 6B the diamond loses its outline and the centre line flares into a hot spot on her forehead. 6A keeps the diamond crisp with a soft halo, which matches Android.

6A is live in the running client at 1280×800 for a full-window look before approve. Values stay in JSON; `PresenceLook.cs` defaults are unchanged. No `look approved` yet. Phase 6 not started.

Not approved yet (verbatim): the face is missing the amber/gold touches. Android has a warm gold sheen worked into the skin across the cheekbones, temples and jawline, and warm edges along the sides of the face and neck. Ours has gold only in narrow highlights down the centre, and the surrounding skin reads dark brown.

### Round 7 — warmer gold in the skin

6A held as the base. Rim stays off. Bloom and emissive unchanged. Key direction and intensity held (`(0,-0.55,-1)`, `2.8`).

| | 7A | 7B |
|---|---|---|
| key | `255,200,90` (was `255,238,155`) | same |
| fill | 6A `32,28,24` `(0.6,-0.2,-0.5)` | `150,70,12` `(0.8,-0.2,-0.4)` |

`P3-LOOK_round7.png` — A | B bust, face, side. Looked at before saving.

7A moves the lit planes (forehead, cheekbones, nose, lips, jaw) from cream toward amber gold. Sides stay in shadow. 7B adds a one-sided gold sheen on the cheek, jaw and neck edge; the far side stays dark. Not the round-1 all-over orange (ambient and env still the dim round-3 values; fill is saturated but far below L9 `180,120,60`).

Cheek landmark A `235,111,39` / B `255,115,39` @ 160,340 (6A was `235,128,60` — A is more amber, less cream; B is a bit brighter from the fill).

**Flecks:** rim off. No white rim sparkles on A or B. Forehead shows the design dot grid only.

6A was restored live after round 7 (wrong). The live window must show the candidate. From now on the leading or named variant stays live.

Round 7 used as base for round 8: **7B**.

### Round 8 — gold in the skin (material)

7B held. Rim off. Bloom unchanged.

The GLB metallic-roughness map B channel is ~0, so `MetallicFactor` alone does nothing. Added look values: `metallicFactor` (default `1`, range `0`–`1`), `roughnessFactor` (default `1`, range `0`–`1`), and `useRoughnessMetallicMap` (default `true`). Defaults keep the map on (current look). For this round the map is off so the factors are the material.

Roughness `0.42` on both (texture mean was about `0.36`; a little rougher so the sheen spreads instead of going chrome). Env moved from the dim round-3 cube to moderate warm amber `40/72, 24/42, 8+2·face` — not L9.

| | 8A | 8B |
|---|---|---|
| metallicFactor | `0.3` | `0.55` |
| roughnessFactor | `0.42` both | |
| useRoughnessMetallicMap | `false` both | |
| env | `40/72, 24/42, 8+2` both | |

`P3-LOOK_round8.png` — A | B bust large, face, side. Looked at before saving.

8A is a burnished gold sheen across the face, not only the key stripe. Sides stay darker. 8B is stronger, more chrome, and the centre line / diamond flare more. Background samples `8,8,8`. Not the round-1 all-over orange.

Landmark samples (Windows bust crop; Android from `android_hud_reference.png` bust crop `108,80 252×658`):

| Landmark | Win xy | 8A | 8B | Android xy | Android |
|---|---|---|---|---|---|
| cheek | 160,340 | `255,134,44` | `255,157,51` | 60,250 | `181,122,66` |
| forehead | 190,200 | `113,63,28` | `95,54,26` | 90,155 | `163,112,69` |
| jaw | 155,450 | `85,40,19` | `69,33,18` | 125,390 | `120,86,58` |

**Flecks:** no white rim sparkles. Forehead shows the design grid plus some gold speckle from the sheen.

**Live: 8A** at 1280×800. No `look approved` yet. Phase 6 not started.

Round 8 feedback (verbatim): Round 8 read as a step back. The samples show why: our highlights are too hot and too orange/red, and the mid-tones and shadows are too dark. Android's face is less saturated (more yellow-bronze) and flatter.

### Round 9 — auto-match

Helix 3.1.2 has no tone mapping, colour grading, exposure or gamma on `Viewport3DX` or as a post-effect (Audit 03 L5 agrees). Built-in posts are Bloom (already a look value), MeshBorderHighlight, MeshOutlineBlur, XRay, XRayGrid. Not built.

Start: 7B, metallic off (`useRoughnessMetallicMap` true). 15 look-JSON iterations logged in `%TEMP%\p3look\round9-log.md`. Did not reach 10% / 0.05 ratio on every landmark. Hard limits held on the final candidate.

**Biggest difference:** shifting the key from orange `255,200,90` at intensity `2.8` to yellow-gold `240,215,145` at `2.5`.

**Best (d10), live:** key `240,215,145` intensity `2.5`; ambient `18,16,16`; fill `80,60,22` `(0.8,-0.2,-0.4)`; env still round-3 dim; bloom/emissive 6A; rim off; metallic map on.

**Alternative (d8):** same key hue, intensity `2.35`, ambient `22,20,18`, fill `90,70,28`.

`P3-LOOK_round9.png` — best | Android, large bust + face. Looked at before saving.

Face mean: Windows bright `53.2` sat `0.611` / Android bright `68.1` sat `0.743` (HSV sat on dark bronze reads high; the orange/red chroma is lower on d10 than on 7B).

| Landmark | Win xy | Best d10 | Android xy | Android | dGR | dBR |
|---|---|---|---|---|---|---|
| forehead | 190,200 | `111,71,36` | 118,175 | `100,57,26` | 0.07 | 0.06 |
| cheekL | 160,330 | `117,62,26` | 60,250 | `174,114,59` | 0.13 | 0.12 |
| cheekR | 262,330 | `110,59,26` | 178,248 | `85,56,38` | 0.12 | 0.21 |
| nose | 210,275 | `164,86,31` | 126,200 | `162,99,49` | 0.09 | 0.11 |
| lip | 210,360 | `130,74,35` | 126,270 | `137,87,45` | 0.07 | 0.06 |
| chin | 210,412 | `131,74,37` | 126,318 | `129,69,21` | 0.03 | 0.12 |
| jawL | 155,448 | `57,33,19` | 78,348 | `49,27,9` | 0.03 | 0.15 |
| jawR | 250,420 | `82,47,21` | 148,360 | `50,27,13` | 0.03 | 0.00 |
| neck | 210,505 | `51,33,21` | 126,400 | `104,58,23` | 0.09 | 0.19 |

Background `8,8,8`. No white flecks. Diamond outline crisp. Face not blurred. Static GPU 60 s avg `0.0018%` max `0.1078%`.

**Live: d10 (best)** at 1280×800. No `look approved` yet. Phase 6 not started.

Round 9 feedback (verbatim): Round 9: good progress. Keep d10 as the base. Helix has no tone mapping, so the remaining gap is the ACES signature: bright areas fade toward cream on Android (hair highlights, eyes nearly white), and Android's mid-tones are brighter (face mean 68 vs 53).

### Round 10 — ACES roll-off with built-in levers

Base d10. Ten look-JSON iterations in `%TEMP%\p3look\round10-log.md`. Hard limits held (background `8,8,8`, no white flecks on the kept candidates, diamond outline kept, face not blurred). Did not land face mean in 65–70.

Bloom combine saturation down to `0.25` and emissive shifted to `2.05,2.0,1.9` cool the glow a little. They do not turn hair highlights or eyes cream: the emissive map is orange, and `EmissiveColor` only multiplies it. Environment strength (`28/36, 26/32, 20+1`, neutral-warm) did not move skin mid-tones while the metallic-roughness map stays on (GLB B channel ~0, so the surface is non-metal and ignores the IBL). The lift that moved the face was ambient.

Rim `#F5A623` at low (`40,27,6`, from the side and slightly behind) did not fleck the face at key `2.5` (0 bright forehead specks) and added nothing visible, so it was dropped. The same rim on key `2.7` put 4 bright specks on the forehead.

**Best (e8), live:** key `240,215,145` intensity `2.5`; ambient `50,46,40`; fill `80,60,22` `(0.8,-0.2,-0.4)`; rim off; emissive `2.05,2.0,1.9`; bloom saturation `0.25` (other bloom stays 6A); env still round-3 dim; metallic map on. Face mean `84.4` sat `0.478` — past the 65–70 band, and the landmark score got worse (`1.08` vs d10 `0.52`) because shadows and the forehead came up with the cheeks. Left cheek is the closest landmark to Android (`157,103,66` vs `174,114,59`, dGR `0.001`).

**Alternative (e5):** same cream bloom and emissive, key intensity `2.7`, ambient still `18,16,16`. Face mean `56.2` sat `0.608`. Under the band, closer to d10.

`P3-LOOK_round10.png` — e8 | e5, large bust + face. Looked at before saving. Eyes and hair highlights still amber on both.

| Landmark | e8 | Android | dGR | dBR |
|---|---|---|---|---|
| forehead | `145,102,66` | `100,57,26` | 0.13 | 0.20 |
| cheekL | `157,103,66` | `174,114,59` | 0.00 | 0.08 |
| cheekR | `151,99,64` | `85,56,38` | 0.00 | 0.02 |
| nose | `200,121,63` | `162,99,49` | 0.01 | 0.01 |
| lip | `165,110,67` | `137,87,45` | 0.03 | 0.08 |
| chin | `160,115,77` | `129,69,21` | 0.18 | 0.32 |
| jawL | `89,63,44` | `49,27,9` | 0.16 | 0.31 |
| jawR | `114,77,46` | `50,27,13` | 0.14 | 0.14 |
| neck | `83,63,46` | `104,58,23` | 0.20 | 0.33 |

Android face mean `68.1` sat `0.743`. Background `8,8,8`. Static GPU 60 s avg `0.0006%` max `0.0361%`.

**Live: e8 (best)** at 1280×800. No `look approved` yet. Phase 6 not started. A true ACES pass was not built.

Round 10 feedback (verbatim): Round 10 received. Developer decision: add real ACES tone mapping. Follow the attached P3-LOOK_ToneMap_Addendum.md: update the plan on this branch to v1.5, then run T1 and stop. Keep e8 or d10 live meanwhile (say which).

### Tone map T1 — Read and Check

Plan on this branch replaced with v1.5 from `C:\Users\test\Dev\zola-assets\plans\PHASE3_BUILD_PLAN.md`. SHA-256 `251b9e69f09cd3f4e2290e9bf8ee0af8dfe7c053d7e0d740c5ab8ba67665287d`. `git diff` is only `P3-D19`, the Track 4 tone-mapping item and exit criterion, lore-closeout / exit-checklist `P3-D19` references, and the version footer. Not committed (goes in the track implementation commit).

**Live meanwhile: e8** at 1280×800. No source changes except the plan and this progress document.

#### 1. `fxc.exe`

Present. Not BLOCKED.

| Path | File version |
|---|---|
| `C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe` | 10.0.26100.7705 (WinBuild.160101.0800) |
| `…\x86\fxc.exe`, `…\arm64\fxc.exe` | same kit |

Banner: `Microsoft (R) Direct3D Shader Compiler 10.1`. T2 will use the x64 binary. Intended command (not run): `fxc.exe /T ps_5_0 /E main /Fo AcesTonemap.cso AcesTonemap.hlsl`.

#### 2. Render target format

**8-bit.** Scene colour buffer, post-effect ping-pong, and swap chain all default to `SharpDX.DXGI.Format.B8G8R8A8_UNorm`.

Evidence, Helix 3.1.2 source:
- `DX11RenderBufferProxyBase.Format` defaults to `Format.B8G8R8A8_UNorm`.
- Colour buffer `Texture2DDescription.Format = Format`.
- `FullResPPBuffer = new PingPongColorBuffers(Format, width, height, …)`.
- WinUI `DX11SwapChainCompositionRenderBufferProxy.CreateSwapChainDescription` sets `Format = Format` with the comment "B8G8R8A8_UNorm gives us better performance".
- Maintainer on helix-toolkit#1743 (2022-04-15): no simple HDR / FP16 primary buffer.

Why it matters: values above 1 clip on the scene write, before ACES. Bloom already works on that clipped UNORM.

Helix does **not** let the post-effect chain use a float target on its own. `Format` is public, but colour, ping-pong, and swap chain share it. A WinUI composition swap chain needs `B8G8R8A8_UNorm`. Changing `Format` to `R16G16B16A16_Float` would also change the swap chain.

**Fallback for T2/T3:** a named look factor (working name `toneMapPreScale`, default 1, used only when the tone map is on) multiplies key / fill / rim / ambient / emissive before they hit the lights, so the 8-bit write stays under 1. The pass then applies `colour × 2^exposure` with `exposure` absorbing `−log2(preScale)` so the curve still sees the intended HDR range. Trade-off: fewer bits in the darks, possible banding in dark gradients. Do not replace the render host.

#### 3. Where the pass goes

`DefaultRenderHost.OnRender` (Helix 3.1.2):
1. Scene to `ColorBuffer`.
2. If FXAA, per-mesh post, or global effects exist: copy / resolve into `FullResPPBuffer.Current`.
3. `RenderType.PostEffect` nodes (we have none).
4. `RenderType.GlobalEffect` nodes in `Items` order — bloom is already one (`PostEffectBloomCore` ctor uses `RenderType.GlobalEffect`).
5. `RenderToBackBuffer`: built-in FXAA if `FXAALevel != None` (we do not set it; default off), then `CopyResource` to the swap-chain `BackBuffer`, then Present.

Add the tone-map `Element3D` in `EnsureLightsAndEnvironment` **after** `_bloom`. It must also be `RenderType.GlobalEffect`. Output is the ping-pong current target, same as bloom; Helix copies that to the back buffer.

#### 4. Lifetime

- Technique: `EffectsManager.AddTechnique` stores the `TechniqueDescription`. `DisposeAllResources` drops compiled techniques; `Reinitialize` rebuilds from that same dictionary, so a technique added once survives device loss. `PresenceView.Dispose` already disposes the effects manager.
- Attach: `NodePostEffectBloom.OnCreateRenderTechnique` / `OnCreateRenderCore`; `PostEffectBloomCore.OnAttach` gets passes and a sampler; `OnDetach` / `RemoveAndDispose` releases them. Mirror that. Extra RTVs must die in `OnDetach`.
- Device loss: `DX11SwapChainCompositionRenderBufferProxy.Present` raises `DeviceLost` on removed / reset / hung; Helix calls `DisposeAllResources` then `Reinitialize`. Fail closed if the technique or RTVs fail after that.
- Track 3 reload: `InvalidateScene` + `LoadAsync` clears `_host` only. Lights, bloom, and the tone-map element stay on `_view.Items`. F12 `ApplyLook` must push `exposure` / `toneMapEnabled` and `InvalidateRender` once, never every frame.
- Pause / resume: `ApplyRenderGate` already sets `RenderHost.IsRendering` from `_pauseReasons`. The pass must not call `InvalidateRender` by itself.

#### 5. Shader plan

- **Curve:** Krzysztof Narkowicz 2015 ACES Filmic fit (`a=2.51, b=0.03, c=2.43, d=0.59, e=0.14`, saturate). Same family Android engines label "ACES Filmic". Not the full Hill RRT+ODT (heavier, still not studio ACES).
- **Exposure:** `c * exp2(exposure)` before the curve. `exposure` is a look float. Android −1.84 is the T3 starting point; Helix equivalent includes the pre-scale fold-in.
- **Output:** Helix writes `B8G8R8A8_UNorm`, not `_SRGB`, and has no gamma pass. Write the filmic result as UNORM with no extra `LinearToSRGB`. Reuse bloom's screen-quad VS (`DefaultVSShaderDescriptions.VSMeshOutlineScreenQuad`), empty input layout, `TriangleStrip`, no depth, source-always blend. One `ShaderPass`; pixel shader from the embedded `.cso` via `IShaderByteCodeReader` or the `ShaderDescription` byte-array ctor.

#### 6. Flags

- Not BLOCKED. `fxc` is present. The 8-bit target is a design constraint; T2 uses the named pre-scale fallback.
- Do not replace `DefaultEffectsManager` from code-behind (XML leak warning). `AddTechnique` on the existing instance.
- `Zola.Client.csproj` may gain only the one `EmbeddedResource` line.
- `toneMapEnabled` default **false** in T2 so off is pixel-identical to e8 / d10.
- No ACES pass built in T1.

**Live: e8** at 1280×800.

### Tone map T2 — Build the Pass

Built behind `toneMapEnabled` (default **false** in `PresenceLook.cs`). Look values: `toneMapEnabled`, `exposure` (−8…8), `toneMapPreScale` (0.05…1, used only when the pass is on), `toneMapDither` (0…2, units of 1/255). Debug-only: `toneMapForceFail`, `toneMapBypass`.

**Compile (once, not a build step):**
- Command: `"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe" /T ps_5_0 /E main /Fo AcesTonemap.cso AcesTonemap.hlsl`
- `fxc` path: `C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe`
- Version: 10.0.26100.7705 (Direct3D Shader Compiler 10.1)
- `AcesTonemap.cso` SHA-256: `2a68b4ac470842946d2fce531a5b99b73654ab5f7d3ffdb3c31d7134eb9069f2` (1928 bytes)

`dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`: 0 warnings.

**Chosen pre-scale:** `0.35`. Scene values written before the pass (bypass: pre-scale on, curve off):

| Region | Peak (max channel / 255) | Pixel |
|---|---|---|
| eyes | 0.867 | 688, 332 |
| diamond | 0.875 | 640, 705 |
| hair highlight | 0.761 | 601, 52 |

All under 1.0. `S=0.45` still clipped (peak 1.0). Folded shader exposure at look `exposure=0` is `0 − log2(0.35) ≈ +1.51`.

**Checks:**
- [x] `toneMapEnabled = false` (d10): two off captures, and off after toggling the pass on then off — **max delta 0**. Pixel-identical to the rebuilt d10 without the curve. (No frozen round-9 d10 full-frame exists; `P3-LOOK_round9.png` is a composite.)
- [x] `toneMapEnabled = true`, exposure 0, S=0.35: ACES roll-off. Highlights on eyes / hair / diamond go cream and shrink; mid-tones drop (expected at exposure 0). vs e8: max delta 247, 237k pixels changed. `P3-LOOK_tonemap_t2.png` — e8 off | ACES on, bust + face. Looked at before saving.
- [x] Static GPU 60 s on: avg `0.0016%` max `0.0945%`.
- [x] Minimize → `paused (minimized)` / `paused (hidden)`; restore → `resumed`. F10: one `import started` (second `LoadAsync` coalesced, existing DebugReload), scene attached, pass still on (max delta 0 vs the ACES frame).
- [x] Forced failure: debug JSON `toneMapForceFail=true` loads `MissingTonemap.cso`. Log: `P3-LOOK: tone map unavailable — shader bytecode missing`. She still renders (force-fail frame is e8-bright, not black). HUD still paints. Switch left under `#if DEBUG`.
- [x] Build 0 warnings.

**Banding:** 6× nearest-neighbour crops of neck, jaw, and cheek (e8 vs ACES). The ACES darks are darker but still smooth. The only hard pixels are the existing mesh-grid dots, also present on e8. No new contour steps. Dither not applied. `toneMapDither` (shader Bayer ±N/255) is there if T3 needs it.

**Live: e8 + tone map on**, `toneMapPreScale=0.35`, `exposure=0`, dither 0, at 1280×800. `PresenceLook.cs` defaults stay off. No `look approved`. Phase 6 / T3 not started.

### Tone map T3-1 — Android lights + Helix exposure

Android colours and structure, Helix units. Key `(0.8, 0.6, 0.3)` = `204,153,77` intensity `4`; ambient `#232222` = `35,34,34`; fill stays e8 `80,60,22`; bloom/emissive stay e8. Tone map on. Same R9 landmarks and face-mean band 65–70 (Android `68.1` / `0.743`).

ACES remaps the viewport clear, so displayed black moved with exposure (pass 1: `E=−1.84` → `5,5,5`; `E=−1.0` → `13,13,13`). The clear is now inverted through Narkowicz and the 8-bit byte that displays closest to `#080808` is chosen. A `byte` loop here wrapped at 255 and froze the UI thread; the index is an `int`. `#if DEBUG` also applies the F12 JSON when the file is written, so retune works without window focus.

**Helix equivalent of Android −1.84:** look `exposure=−0.65` at `toneMapPreScale=0.28` (folded shader exposure `−0.65 − log2(0.28) ≈ +1.19`). Android −1.84 at these Helix intensities is far too dark (face mean `26.0`). Face mean lands in 65–70 at `E=−0.65…−0.55`.

**Pre-curve maxima (bypass, final S=0.28 I=4) — all under 1.0:**

| Region | Peak (max channel / 255) | Pixel |
|---|---|---|
| eyes | 0.8824 | 688, 332 |
| hair highlight | 0.7725 | 601, 52 |
| diamond | 0.8941 | 640, 706 |

**Rim `#F5A623` (`245,166,35`):** retried with the curve on. Face close-up has 23 white flecks (forehead / hair). Dropped. Mid `80,54,12` and low `40,27,6` did not fleck and added almost nothing on the face.

**Best (w1), live:** key `204,153,77` intensity `4` `(0,−0.55,−1)`; ambient `35,34,34`; fill `80,60,22`; rim off; e8 bloom/emissive; `toneMapEnabled=true`; `exposure=−0.65`; `toneMapPreScale=0.28`; dither `0`. Face mean `65.4` sat `0.585`. Landmark score `0.6043`.

**Alternative (w4):** same, rim `80,54,12`. Face mean `68.1` sat `0.577`. Score `0.6283`.

`P3-LOOK_tonemap_t3.png` — best | Android, large bust + face. Looked at before saving.

| Landmark | Win xy | Best w1 | Android xy | Android | dGR | dBR |
|---|---|---|---|---|---|---|
| forehead | 190,200 | `137,91,45` | 118,175 | `100,57,26` | 0.094 | 0.068 |
| cheekL | 160,330 | `126,75,32` | 60,250 | `174,114,59` | 0.060 | 0.085 |
| cheekR | 262,330 | `124,74,32` | 178,248 | `85,56,38` | 0.062 | 0.189 |
| nose | 210,275 | `165,106,40` | 126,200 | `162,99,49` | 0.031 | 0.060 |
| lip | 210,360 | `141,89,39` | 126,270 | `137,87,45` | 0.004 | 0.052 |
| chin | 210,412 | `113,74,37` | 126,318 | `129,69,21` | 0.120 | 0.165 |
| jawL | 155,448 | `80,48,27` | 78,348 | `49,27,9` | 0.049 | 0.154 |
| jawR | 250,420 | `113,65,30` | 148,360 | `50,27,13` | 0.035 | 0.006 |
| neck | 210,505 | `74,47,29` | 126,400 | `104,58,23` | 0.077 | 0.171 |

Background `7,7,7` (`#080808` ±1). No white flecks on w1. Diamond outline crisp. Face not blurred. 6× nearest-neighbour crops of neck, jaw, and cheek: smooth, mesh-grid dots only, no new contour steps. Dither not applied. Static GPU 60 s: avg `0.0013%` max `0.0770%`.

**Live: w1** at 1280×800. `PresenceLook.cs` defaults stay off. No `look approved`. Phase 6 not started.

### Tone map T3-2 — warmth, left key, softer hair

From w1 (ACES on, `E=−0.65`, `S=0.28`). Three variants. Same R9 landmarks.

**A (a2) warmth:** key `230,125,52` (more red, less green than `(0.8,0.6,0.3)`), fill `92,52,16`, direction still frontal `(0,−0.55,−1)`, intensity `4`. Face sat `0.623` (w1 `0.585`, Android `0.743`). Deeper amber `244,102,36` reached only `0.643` and went orange (forehead `150,72,34`, cheeks `139,60,28`). **Light colour alone cannot restore ~0.7 after ACES without going orange.** A saturation control in the tone-map shader would be the fix: one `fxc` recompile, new `.cso` SHA recorded. Not done this round.

**B (b7), live:** A plus key from the viewer's left and slightly above `(0.65,−0.70,−0.85)`. Fill dim on the far side `32,22,8` `(−0.95,−0.08,−0.28)`. Image-left cheek/jaw/shoulder come up; the right side falls into warm shadow (jawL `107,51,27` vs jawR `58,35,27`). Face mean `56.8` sat `0.559` — darker than A because the frontal fill-in is gone. 5A's `(−0.3,−0.8,−1)` lit the *wrong* side under this look; the +X key is what matches Android.

**C (c6):** B with key `3.4` and `E=−0.5`. Hair mean `65.4` (A `68.4`, w1 `69.7`). Side dreads go bronze; the crown is still yellow-gold, not Android's dark mass with cream only on tips and edges. Face mean `59.6` sat `0.517`.

`P3-LOOK_tonemap_t3_2.png` — A | B | C | Android, bust + face. Looked at before saving.

| Landmark | A a2 | B b7 | C c6 | Android |
|---|---|---|---|---|
| forehead | `145,81,37` | `139,76,37` | `137,77,41` | `100,57,26` |
| cheekL | `134,66,29` | `117,58,28` | `116,60,33` | `174,114,59` |
| cheekR | `132,66,29` | `102,52,28` | `103,54,33` | `85,56,38` |
| nose | `172,94,35` | `152,78,33` | `150,79,37` | `162,99,49` |
| lip | `150,79,35` | `121,62,32` | `120,64,36` | `137,87,45` |
| chin | `119,67,33` | `108,60,32` | `108,62,36` | `129,69,21` |
| jawL | `87,44,27` | `107,51,27` | `106,54,32` | `49,27,9` |
| jawR | `122,58,27` | `58,35,27` | `62,39,32` | `50,27,13` |
| neck | `79,43,29` | `61,36,27` | `64,39,32` | `104,58,23` |

**Flecks:** 0 near-white on A, B, and C face crops (same forehead scan as the hard limit). Background held `#080808` ±1 on all three.

**Live: B (b7)** at 1280×800. `PresenceLook.cs` defaults stay off. No `look approved`. Phase 6 not started.

### Tone map T3-3 — Android lighting structure

Developer-supplied Filament units do not transfer. This round rebuilds roles, colours, placement and ratios. No environment image, no reflections.

**Helix PBR ambient (does it multiply albedo?)** No. `psMeshPBR.hlsl` `main` ends with `color += emissive + vLightAmbient.rgb * RMA.r` — a flat add of the ambient colour × AO only. When there is no cube map, ambient also scales dielectric spec (`c_spec * vLightAmbient * AO`). It never multiplies albedo / `c_diff`. So `AmbientLight3D` cannot be Filament's "neutral light from all directions that reveals her gold textures". Pushing `ambientIntensity` to 2.5–6 washes her porcelain-gray (s1, s4, sat ~0.15–0.25). Live intensity is 1.2: high enough to sit in the look, low enough that the BRDF (key + point rim) still reads the textures.

**Emissive:** GLB `materials[0].emissiveFactor` is `[1,1,1]` with an `emissiveTexture`. Android used the GLB as-is. Our e8 look was `2.05 / 2.0 / 1.9` (~2.0–2.2× that factor). Live uses `1,1,1`.

**Sat shader:** already compiled this track. `AcesTonemap.cso` SHA-256 `619e6be73c1455bc6ef3896ff82d517fb6aee7ceef88c96b78b10c64a603bb16`, 2040 bytes. Post-curve `luma + Color.b * (mapped − luma)`; `Color.b = 1` is identity (`mapped`). Off-identical holds by that identity (default `toneMapSaturation = 1`). Structure-only (s3, sat 1.0) face sat `0.404` vs Android `0.743`, so sat 1.35 is on for the live look. 1.65–1.75 recovered sat toward ~0.58–0.62 but went orange.

**New look values** (defaults leave the shipped look unchanged): `ambientIntensity` 0–16 default 1; `rimUsePoint` default false; `rimX/Y/Z`, `rimRange`, `rimIntensity` (point off at 0); `modelPitchDegrees` default 0; `renderEnvironmentMap` default true. JSON keys validated, F12 / file-watch.

**Mapped structure (live s6):**

| Android role / value | ours | mapped? |
|---|---|---|
| Uniform ambient `#232222` @ 1000, no env image, no reflections | `AmbientLight3D` `#232222` × `ambientIntensity` 1.2; `renderEnvironmentMap=false`; `useIrradianceMap=false` | Colour and "no env" yes. Strength partial: Helix ambient is a flat add, not albedo lighting, so 1000 cannot be the dominant texture light |
| Key directional `(0.8, 0.6, 0.3)` @ 2.5, "minimal; ambient carries the scene" | `204,153,77` (= that colour), `keyIntensity` 1.5 (was 4), dir `(0,−0.4,−1)` | Colour yes. Role yes (minor). Helix needs this BRDF light because ambient cannot carry the textures |
| Rim point `#F5A623` @ 500 at `(−0.47, +0.35, −0.6)` on a 0.5-tall model | `PointLight3D` `245,166,35`, world `(−1.785, 1.329, −2.279)`, range 8, intensity 3.5. Bust height 1.899 → scale 3.798 | Role, colour, placement yes (viewer's left, behind, above). Units remapped |
| Head pitch 10° about X | `modelPitchDegrees` 10 | Yes |
| Camera slightly below, looking up | `cameraY −0.12`, `lookY 0.32` (was `0.05` / `0`) | Yes |
| ACES Filmic, exposure −1.84 | ACES on, `E=−0.65`, `S=0.28` (Helix fold of −1.84 from T3-1) | Yes |
| GLB emissive as-is | `emissive` `1,1,1` (was ~2.2×) | Yes |
| Fill (none in the lock) | fill `0,0,0` | Yes |
| Saturation ~0.74 | post-curve `toneMapSaturation` 1.35 → face sat `0.503` | Partial; higher sat oranges |

**Flecks:** 55 near-white on the s6 face crop (same forehead scan). They sit in the point-rim hair/forehead gleam, not as random sparkle. s3 (sat 1) had 60.

**Framing:** 10° pitch + lowered camera holds at 900×640, 1280×800, and maximized (1920×1009). Whole bust, base inside the window, diamond about two-thirds down, room below for Phase 6. HUD and dock stay clear.

`P3-LOOK_tonemap_t3_3.png` — s6 | Android, bust + face. Looked at before saving.

| Landmark | s6 live | Android |
|---|---|---|
| forehead | `41,35,35` | `100,57,26` |
| cheekL | `79,51,32` | `174,114,59` |
| cheekR | `73,48,33` | `85,56,38` |
| nose | `110,69,35` | `162,99,49` |
| lip | `109,63,30` | `137,87,45` |
| chin | `121,74,34` | `129,69,21` |
| jawL | `72,47,31` | `49,27,9` |
| jawR | `149,102,49` | `50,27,13` |
| neck | `57,41,32` | `104,58,23` |

Face mean `60.9` sat `0.503` (Android `68.1` / `0.743`). Background `#080808` ±1.

**Live: s6** at 1280×800. `PresenceLook.cs` defaults stay off. No `look approved`. Phase 6 not started.

### Tone map T3-4 — even irradiance vs B fallback

T3-3's flat ambient cannot copy "ambient carries the scene". Kept ACES, sat control, 10° pitch, camera looking up, and key colour `(0.8, 0.6, 0.3)` on E. Dropped dominant flat ambient and the point rim.

New look value `evenLightIntensity` (0–16, default 0). Six `DirectionalLight3D` on ±X ±Y ±Z, colour `#232222`, scaled by that intensity, `IsRendering` off at 0. Fill / directional rim / point rim turn off while the six are on so Helix stays inside the light budget. They hit the PBR BRDF (`NdotL * c_diff`), so they multiply albedo the way Android's IBL does.

**E (e4):** even 6.0, flat `ambientIntensity` 0.5, key `204,153,77` I=1.0 from the viewer's left `(0.65,−0.70,−0.85)`, e8 emissive, no env, `E=−0.35`, sat 1.3. Face mean `69.6` sat `0.625`. Flecks **0**. Gold comes from the textures. Hair goes wet/specular (six spec lobes) and the face is more even, more bronze.

**F (f1), live:** T3-2 B lights (key `230,125,52` I=4 left, fill `32,22,8`, amb `#232222` × 1, rim off) plus sat 1.25, pitch 10°, camera `Y=−0.12` / `lookY=0.32`, e8 emissive. `E=−0.65` `S=0.28`. Face mean `67.2` sat `0.641`. Flecks **0**. f2/f3 pushed sat toward 0.71 but the chest went orange.

`P3-LOOK_tonemap_t3_4.png` — E | F | Android, bust + face. Looked at before saving.

| Landmark | E e4 | F f1 live | Android |
|---|---|---|---|
| forehead | `28,20,17` | `28,27,27` | `100,57,26` |
| cheekL | `119,71,20` | `173,99,36` | `174,114,59` |
| cheekR | `78,45,16` | `84,43,26` | `85,56,38` |
| nose | `119,69,21` | `156,78,26` | `162,99,49` |
| lip | `140,87,33` | `144,63,21` | `137,87,45` |
| chin | `155,103,46` | `179,95,29` | `129,69,21` |
| jawL | `88,48,16` | `104,47,22` | `49,27,9` |
| jawR | `153,102,52` | `179,95,31` | `50,27,13` |
| neck | `103,71,45` | `48,32,25` | `104,58,23` |

**E is not worth switching to** as the live look. The six-axis idea is the right Helix stand-in for Android IBL (albedo-lit, no flecks, brightness can match), but the hair picks up plastic spec and she loses B's cheek modeling. F is the better portrait and cheekL `173,99,36` sits on Android `174,114,59`.

**Live: F (f1)** at 1280×800. `PresenceLook.cs` defaults stay off. No `look approved`. Phase 6 not started.

### T3-4 process fix — complete replace, no inherit

The live window was glossy orange with weak eye/diamond glow. That **did** match the uncropped F full frame (`r9f1-full.png`). It did **not** match the F bust/face we showed: those were cropped (`430,18,420,770` and `500,90,280,400`) and scaled into the compose, which hid the orange cast.

Round 8 metallic was **not** still on. Effective (and F JSON) had `metallicFactor=1`, `roughnessFactor=1`, `useRoughnessMetallicMap=true`. The orange gloss is B's key `230,125,52` @ 4 plus sat 1.25, ACES, and 7B bloom.

**Inherit leftover vs recorded F** (only keys that differed after replaying defaults → E sweep → last partial F JSON):

| key | inherit effective (before reset) | recorded F / complete F |
|---|---|---|
| `renderEnvironmentMap` | `false` (left from E) | not in F JSON; PresenceLook default `true` |

Every other F key was already in the last JSON. Missing keys (`cameraX/Z`, `lookX/Z`, `fov`, `rimX/Y/Z`, `rimRange`, `rimIntensity`, `reflectanceFactor`, `useIrradianceMap`) were already at PresenceLook defaults.

**Process fix:** F12 now `TryReplaceJson` from `CreateDefault()` and rejects any missing key. Apply writes `%LOCALAPPDATA%\ZolaClient\debug\presence-look.effective.json` and logs `fingerprint=<sha256>`. Scripts reset-to-defaults then write every key.

**Live F** re-applied as a complete JSON from that reset. Raw client-area capture (1280×800, no crop/scale): `P3-LOOK_tonemap_t3_4_F_raw.png`. Fingerprint `f3b708800cfe7aba21b8940739bff345834cd2b061cf1c22e39083e8eaa551cf`.

No further tuning. Defaults unchanged. Phase 6 not started.

### Restore 6A (developer-approved base)

Later rounds drifted from the last approved live frame. 6A restored exactly as a complete replace from defaults. Tone map, sat, pitch, lowered camera, point rim, and even lights stay in code, switched off.

Recorded 6A: round-3 ambient `14,14,16`, fill `32,28,24` `(0.6,−0.2,−0.5)`, env `14/18, 14/16, 14+1`; key `255,238,155` @ `2.8` frontal `(0,−0.55,−1)`; rim off; emissive `2.2, 2.1, 1.85`; bloom `0.72/0.52/0.16`, 3 passes, `1.05/1.0/0.85/0.85`; tone map off; metallic/roughness/map at defaults; camera and pitch at defaults.

Raw client-area capture: `P3-LOOK_6A_raw.png`. Looked at before saving. Fingerprint `3edae24c54953dbf1f18af1d020c688c0a36f2aee7a2b059c665be0d61c73013`.

**Live: 6A** at 1280×800. Defaults unchanged. No `look approved`. Phase 6 not started.

Developer correction: home base is T3-1 best (**w1**), not 6A. That is the frame called close (“contrast might be too high”).

### Restore w1-home (T3-1 best)

Reconstructed w1’s **effective** live config (not only recorded keys). T3-1 apply was inherit-era: `t3-run3.ps1` started each candidate from `New-LookT3` (`7B → D10 → E8 → T3`) then overlaid w1. Missing keys stayed at whatever was already live, or at PresenceLook defaults if the key did not exist yet.

**Recorded w1:** key `204,153,77` ×4 frontal `(0,−0.55,−1)`; ambient `#232222` = `35,34,34`; fill `80,60,22`; rim off; e8 bloom and emissive; ACES on; `E=−0.65`; `toneMapPreScale=0.28`; dither `0`; no sat (identity `1.0`); no pitch; default camera.

**Inherited from the 7B→D10→E8→T3 chain (live at that moment):**

| key | value | source |
|---|---|---|
| fill direction | `(0.8,−0.2,−0.4)` | 7B / W1 |
| env cube | `14/18, 14/16, 14+1` | 7B; e8/d10 kept round-3 dim (28/36 probe was dropped) |
| metallic / roughness / map | `1` / `1` / on | 7B; d10/e8 reported map on |
| emissive | `2.05, 2.0, 1.9, 1` | e8 (A from 7B) |
| bloom | `0.72/0.52/0.16`, 3, `1.05/1.0/0.85`, sat `0.25` | 7B stack + e8 sat |
| rimDX/DY/DZ | `0.55, −0.18, 0.65` | T3; unused because rim colour is `0,0,0` |
| toneMapEnabled / bypass / fail | true / false / false | T3 |

**Did not exist at T3-1** (PresenceLook / then-hardcoded defaults, identity):

| key | value |
|---|---|
| toneMapSaturation | `1.0` |
| modelPitchDegrees | `0` |
| camera / look / fov | `(0, 0.05, 3.15)` / `(0, 0, −3.372)` / `35` |
| ambientIntensity | `1` (preScale-only then) |
| evenLightIntensity | `0` |
| rimUsePoint / rimX/Y/Z / rimRange / rimIntensity | false / `0` / `4` / `0` |
| renderEnvironmentMap | `true` (hardcoded true) |
| reflectanceFactor | `0.5` |
| useIrradianceMap | `false` |

**Unsure (no visual effect expected):**

- `rimDX/DY/DZ` — T3 hashtable had `0.55, −0.18, 0.65`; PresenceLook default is `0.15, −0.25, 1`. Rim colour is black either way.
- `reflectanceFactor` / `useIrradianceMap` — not look keys yet; used later PresenceLook defaults (`0.5` / `false`), which match Helix PBR defaults at the time.

Applied as a complete replace from `CreateDefault()`. Saved `%TEMP%\p3look\w1-home.json` (copy in `%LOCALAPPDATA%\ZolaClient\debug\`). Raw client-area capture (1280×800, no crop/scale): `P3-LOOK_w1_home_raw.png`. Looked at before saving. Fingerprint `dc7c5856c13e714322384090f589c4e05025b88edaaa99b70bf3052bdce531cd`.

**Live: w1-home** at 1280×800. Defaults unchanged. No `look approved`. Phase 6 not started.

### Experiment U (unlit + sRGB ACES)

Developer finding: Android’s look is not lighting-driven. Exposure is effectively 0.1 (`setExposure(−1.84)` clamped). Light is one uniform neutral ambient, negligible key, no bloom. Pipeline: albedo sRGB→linear × gain, ACES, linear→sRGB. Shading is baked in the albedo. Predicted forehead ≈ `97,53,23` vs Android `100,57,26`.

**Unlit (`unlitMode`, default false):** Helix `DiffuseMaterialCore`, albedo × white, `EnableUnLit=true`. Lights, bloom and rim `IsRendering=false` in this mode; nothing removed. `DiffuseMaterial` has no emissive map, so the emissive texture is not bound (eyes/diamond still read from baked albedo).

**Morphs still work.** Ctrl+Shift+F9 blink: both lids close, log `debug blink on`, bust max-delta 246 / 6640 px. F11 morph 0 `BlinkLeft`: left lid closes, 3515 px. F11 morph 8 `JawOpen`: mouth opens, 30704 px. Reset to Neutral.

**Tone-map shader** (one `fxc` recompile):

- Command: `"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe" /T ps_5_0 /E main /Fo AcesTonemap.cso AcesTonemap.hlsl`
- SHA-256 `e49c022f4b28e948fe60d26ad33a98b40149f19d0f5fc21d810e9de1d8400480`, 2744 bytes
- `srgbDecode` / `srgbEncode` / `toneMapGain` (default 1). On: `sRGBtoLinear(input) × gain`, ACES, `linearToSRGB`.
- Switches off: existing path. Identity vs prior w1-home bust crop: **max delta 0** (full client differed only in the HUD clock).

**U live** (complete replace from defaults; camera/pitch stay default): `unlitMode=true`; `srgbDecode`/`srgbEncode` on; `toneMapGain=4.4`; `exposure=0`; `toneMapPreScale=1`; ACES on; sat 1; dither 0.

Raw 1280×800: `P3-LOOK_U_raw.png`. Looked at before saving.

| sample | xy | U | predicted / Android |
|---|---|---|---|
| forehead | 620,218 | `87,52,25` | ≈ `97,53,23` / `100,57,26` |
| cheek | 590,348 | `87,41,8` | — |
| chest | 640,620 | `133,68,14` | — |

Fingerprint `301635475cc103533fb020cde5ac9444558a5ddeee60e67a986e4578a6ac9e1c`.

**Live: U** at 1280×800. PresenceLook defaults unchanged (`unlitMode` false). No `look approved`. Phase 6 not started.

Developer: U reads like Android. U is the new home. Saved `%TEMP%\p3look\U-home.json` (copy in `%LOCALAPPDATA%\ZolaClient\debug\`).

### U-home + mipmaps + sRGB clear

**GLB sampler:** one sampler, all four textures. `magFilter=9729` LINEAR, `minFilter=9987` LINEAR_MIPMAP_LINEAR. Images are 2048×2048 JPEG (albedo, normal, emissive, metallic-roughness).

**Helix already generates mipmaps.** Live GPU after attach (and Helix `TextureLoader` auto-gen): each map `2048×2048`, **12 mips**, `R8G8B8A8_UNorm`, `GenerateMipMaps`. `TextureModel.TextureInfo.GenerateMipMaps=true`. Disable-gen path is 1 mip. No load-path change — enabling again would be a no-op. Face 1:1 before/after (`P3-LOOK_U_face_before.png` / `P3-LOOK_U_face_after.png`, 280×400 unscaled) is the same on the dots; the face is on mip 0.

**Anisotropy:** Helix default `DiffuseMaterialCore.DiffuseMapSampler` / `PBR SurfaceMapSampler` is `Filter=MinMagLinearMipPoint`, **MaximumAnisotropy=4**, minLOD 0, maxLOD inf. That is **not** the GLB’s linear-mipmap-linear (mip filter is point). Left unchanged this step.

**Clear:** old ACES-only picker left the displayed field at `17,17,17` (`#111111`, the lifted “about #101010”). Picker now runs the same pipeline as the shader when `srgbDecode`/`srgbEncode` are on. After: background `7,7,7` (`#080808` ±1) at 20,400 and 100,100.

Raw: `P3-LOOK_U_mip_raw.png`. Looked at before saving. Fingerprint still `301635475cc103533fb020cde5ac9444558a5ddeee60e67a986e4578a6ac9e1c` (look JSON unchanged).

**Live: U-home** at 1280×800. Defaults unchanged. No `look approved`. Phase 6 not started. FXAA next if the dots still need it.

### U Step 2 — mip LOD bias + linear mip filter

Helix exposes the albedo sampler: `DiffuseMaterialCore.DiffuseMapSampler` and `PBRMaterialCore.SurfaceMapSampler` are `SamplerStateDescription` (Filter, `MipLodBias`, anisotropy, wrap, min/max LOD). Phase 7 1024² was not used.

**Look value:** `mipLodBias`, default `0`, validated `0–2`. ApplyLook copies the current albedo sampler, sets `Filter=MinMagMipLinear` (trilinear; was `MinMagLinearMipPoint`) and `MipLodBias` from the look. Live U uses the unlit `DiffuseMapSampler`; PBR `SurfaceMapSampler` is set the same so a later unlit-off switch is not stale. Anisotropy stays 4. IBL / displacement samplers untouched.

**Live apply:** complete U from reset + `mipLodBias=0.75`. Attach log (defaults, before F12): `Filter=MinMagMipLinear mipLodBias=0 anisotropy=4`. Effective after apply includes `mipLodBias=0.75`.

Raw 1280×800: `P3-LOOK_U_bias_raw.png`. 1:1 face (500,90,280,400, unscaled): `P3-LOOK_U_bias_face_before.png` / `P3-LOOK_U_bias_face_after.png`. Looked at before saving. Background still `7,7,7`. Forehead `87,51,25` @ 620,218 (was `87,52,25`). Cheek `90,42,8` @ 590,348.

Fingerprint `c48cabd35aebe84fe4c92d820da1c93260c1052df006ac775a2c740a44c7e5b0`.

**Live: U-home + mipLodBias 0.75** at 1280×800. PresenceLook default `mipLodBias` stays 0. No `look approved`. Phase 6 / 7 not started. FXAA not this step.

### Look approved

Developer judgement (verbatim): "dark skin carrying gold from her own texture, white-gold eyes, glowing diamond and lit hair tips; dots softened; reads like Android."

Approved values written into `PresenceLook.cs` defaults (cold start, no F12):

| key | default |
|---|---|
| `unlitMode` | `true` |
| `srgbDecode` / `srgbEncode` | `true` |
| `toneMapEnabled` | `true` |
| `toneMapGain` | `4.4` |
| `mipLodBias` | `0.75` |
| `exposure` | `0` |
| `toneMapPreScale` | `1` |
| `toneMapSaturation` | `1` |
| `toneMapDither` | `0` |
| camera / look / fov | `(0, 0.05, 3.15)` / `(0, 0, −3.372)` / `35` |
| `modelPitchDegrees` | `0` |

Lights, bloom, emissive and env cube stay at their prior PresenceLook defaults and stay unused (`unlitMode` gates them off). Nothing removed.

Attach log: `Filter=MinMagMipLinear mipLodBias=0.75 anisotropy=4`. CreateDefault fingerprint `22cd6f0acac053feb1a390346dc63ef74bd2a2cfb16ee9119e003a230df3971c`.

Raw from defaults (1280×800): `P3-LOOK_approved_raw.png`. Looked at before saving. Samples match the approved U+bias frame:

| region | xy | sample |
|---|---|---|
| cheek | 590,348 | `90,42,8` |
| hair | 660,90 | `169,102,35` |
| chest | 640,620 | `135,66,14` |
| forehead | 620,218 | `87,51,25` |
| background | 20,400 | `7,7,7` |

**Live: approved look from defaults** at 1280×800. Phase 6 / 7 not started.

## Finish addendum (`P3-D20` / `P3-D21`)

### Step 0 — Plan v1.6

Replaced `zola-architecture/lore/build-plans/PHASE3_BUILD_PLAN.md` from `C:\Users\test\Dev\zola-assets\plans\PHASE3_BUILD_PLAN.md`. SHA-256 `8d143a8f68bee787b683f3831b9e5ff4b3f7029d53eacfdf809d64d0e842db71` (matched).

Committed HEAD is still v1.4 (`4609c69`). Working-tree v1.5 (SHA `251b9e69…`) was overwritten by this replace. The v1.6 surface vs that v1.5 is `P3-D20`, `P3-D21`, Track 4 exit criteria, Track 5 particle-field and gain bullets, `S30`, `P3-D21` references, and the version footer. Goes in the implementation commit.

### Step 1 — Backdrop and decoration (`P3-D21`)

Nothing was started: no `PresenceBackdrop.cs`, no glow quad, no floor rings, no corner brackets, no particle layer.

Removed unused tokens only:

- `ZolaLayerDecoration` (never referenced; HUD stays `ZolaLayerHud` = 10)
- `ZolaPresenceAmber` / `ZolaPresenceAmberBrush` (particle colour; unused)

Approved look unchanged.

### Step 2 — Overlay opacity 0.94

`ZolaOverlayBrush` Opacity `0.88` → `0.94`. Nothing else. Raw: `P3-LOOK_overlay_094_1280.png` (1280×800) and `P3-LOOK_overlay_094_900.png` (900×640), overlay open. Looked at before saving. Right-hand HUD still reads through the header at 0.94.

**Live: approved look, overlay open, opacity 0.94** at 1280×800. Waiting on "keep" / "more opaque" / "less opaque". Steps 3–4 not started.

Developer: **keep**. Overlay opacity stays `0.94`.

### Step 3 — Memory (2048², mip bias 0.75)

Cold launch, no `presence-look.json`. Import log `load duration` is the worker import; wall is process start → first 3D frame. Rest is 20 s after first frame.

| | Working set | Private bytes |
|---|---|---|
| Import before | 213,147,648 (203 MB) | — |
| Import after | 962,977,792 (918 MB) | — |
| Peak during load | 1,052,942,336 (1004 MB) | 984,412,160 (939 MB) |
| Cold rest | 848,560,128 (809 MB) | 778,018,816 (742 MB) |

Cold load time: **906 ms** import / **2388 ms** wall.

Cold rest **809 MB < 900 MB** → 1024² comparison not run. Texture size stays 2048².

P3-RENDER soak (6 × `Ctrl+Shift+F10`, 30 s apart, then 2 min idle). First F10 in each run did not attach (hotkey miss); reloads 2–6 did.

**Before KC11 Dispose**

| Sample | Working set | Private bytes |
|---|---|---|
| Cold rest | 848,560,128 (809 MB) | 778,018,816 (742 MB) |
| After 1 | 853,815,296 (814 MB) | 782,897,152 (747 MB) |
| After 2 | 1,137,577,984 (1085 MB) | 1,063,231,488 (1014 MB) |
| After 3 | 1,196,761,088 (1141 MB) | 1,133,658,112 (1081 MB) |
| After 4 | 1,396,469,760 (1332 MB) | 1,328,152,576 (1267 MB) |
| After 5 | 1,843,585,024 (1758 MB) | 1,792,667,648 (1710 MB) |
| After 6 | 2,024,292,352 (1931 MB) | 1,968,791,552 (1878 MB) |
| Idle 2 min | 2,027,610,112 (1934 MB) | 1,971,556,352 (1880 MB) |

Idle vs cold rest: **+1124 MB (+138.9%)**.

Helix: `SceneNode` is `IDisposable` (`GroupNodeBase.OnDispose` / `DisposeObject`). `TextureModel`, `MaterialCore`, and `HelixToolkitScene` have no `Dispose` in the 3.1.2 XML. Applied the pre-authorized KC11 call: after `_host.Clear(true)`, `Dispose()` the detached `_modelRoot`.

**After KC11 Dispose**

| Sample | Working set | Private bytes |
|---|---|---|
| Cold rest | 847,032,320 (808 MB) | 777,846,784 (742 MB) |
| After 1 | 851,439,616 (812 MB) | 779,997,184 (744 MB) |
| After 2 | 1,130,225,664 (1078 MB) | 1,054,298,112 (1005 MB) |
| After 3 | 1,198,395,392 (1143 MB) | 1,138,151,424 (1085 MB) |
| After 4 | 1,464,610,816 (1397 MB) | 1,397,407,744 (1333 MB) |
| After 5 | 1,861,976,064 (1776 MB) | 1,793,814,528 (1711 MB) |
| After 6 | 1,979,207,680 (1888 MB) | 1,922,904,064 (1834 MB) |
| Idle 2 min | 1,982,926,848 (1891 MB) | 1,926,688,768 (1837 MB) |

Idle vs cold rest: **+1083 MB (+134.1%)**. Node `Dispose` did not stop the climb; the 2048² maps have no `Dispose`.

### Step 4 — Inventory of disabled experiment paths

Waiting on keep / remove. Recommendations below.

| Path | What it does | Approved look | Lines | Recommendation |
|---|---|---|---|---|
| Lit path (`unlitMode=false`): key, fill, ambient, env cube, bloom | Helix lights + `PostEffectBloom` + env DDS | Off (`unlitMode=true`; lights/bloom `IsRendering=false`; env `SkipRendering=true`) | `PresenceLook.cs` 24–93, 183–226; `PresenceView.cs` 668–718, 844–961, 989–994, 1421–; `CreateWarmCubeDds` | **Remove.** Not used by the approved look or Track 5. |
| Directional rim | Third directional from behind | Off (unlit; rim colour unused) | `PresenceLook.cs` 41–46, 199–204; `PresenceView.cs` 680, 883–901 | **Remove.** |
| Point rim | `PointLight3D` stand-in for Android rim | Off (`rimUsePoint=false`) | `PresenceLook.cs` 49–54, 206–211; `PresenceView.cs` 682–688, 903–921 | **Remove.** |
| Six-light even | Axis directionals as IBL stand-in | Off (`evenLightIntensity=0`) | `PresenceLook.cs` 66–72, 214; `PresenceView.cs` 695–706, 871, 923–946 | **Remove.** Experiment E. |
| `toneMapSaturation` | Post-ACES sat; 1 is identity | Unused (default 1) | `PresenceLook.cs` 105, 242, 278; `PresenceView.cs` 1086; `PostEffectToneMap.cs` 71–79, 253–260, 363; `AcesTonemap.hlsl` sat | **Remove.** Track 5 maps glow to **gain**, not sat. |
| `modelPitchDegrees` | Rotate bust about X | Unused (0) | `PresenceLook.cs` 55, 212; `PresenceView.cs` 838–842 | **Remove.** |
| Camera / look / fov | Fixed framing | **Used** at defaults `(0, 0.05, 3.15)` / `(0, 0, −3.372)` / `35` | `PresenceLook.cs` 16–22, 175–181; `PresenceView.cs` 829–834 | **Keep.** This is the approved frame. |
| `metallicFactor` / `roughnessFactor` / `useRoughnessMetallicMap` / `reflectanceFactor` / `useIrradianceMap` | PBR levers | Off (PBR block only when `!unlit`) | `PresenceLook.cs` 95–99, 227–; `PresenceView.cs` 970–987 | **Remove.** |
| `emissiveR/G/B/A` | PBR emissive scale | Off (`DiffuseMaterial` has no emissive) | `PresenceLook.cs` 74–77, 215–218; `PresenceView.cs` 634–641, 973–977 | **Remove.** |
| `toneMapPreScale` | Scales lights when ACES is on; folds into `exposure − log2(preScale)` | Set to **1** (identity). Lights are off, so only the fold remains, and that fold is 0. | `PresenceLook.cs` 103, 240; `PresenceView.cs` 836, 1194–1238, 1084, 1104 | **Remove.** Approved pipeline does not need it; `exposure` already feeds the shader. |
| `exposure` | Shader exposure (folded) | Used; value **0** | `PresenceLook.cs` 102, 239; `PresenceView.cs` 1084, 1236–1238; `AcesTonemap.hlsl` | **Keep.** Tone-map pass stays; fail-closed / identity at 0. |
| `toneMapDither` | Bayer dither | Unused (0) | `PresenceLook.cs` 104, 241; `PresenceView.cs` 1085 | **Remove.** |
| `toneMapForceFail` / `toneMapBypass` | DEBUG fail-closed / bypass | Off | `PresenceLook.cs` 248–250, 280–282; `PresenceView.cs` 1057–1074, 1201–1226 | **Keep** under `#if DEBUG`. Fail-closed path. |
| `unlitMode` + unlit material | Albedo × white, `EnableUnLit` | **On** | `PresenceLook.cs` 110, 245; `PresenceView.cs` 634–641, 837, 963–966 | **Keep.** Approved look. |
| `srgbDecode` / `srgbEncode` / `toneMapGain` / ACES pass | sRGB → linear × gain → ACES → sRGB | **On** (gain 4.4) | Shader + `PostEffectToneMap.cs`; `PresenceView.cs` 1055–1128 | **Keep.** `P3-D20`; Track 5 maps mode glow onto gain. |
| `mipLodBias` + linear mips | Soften painted dots | **Used** (0.75) | `PresenceLook.cs` 111, 246; `PresenceView.cs` 1004–1024 | **Keep.** Approved look. |
| `toneMapEnabled` | Gates the ACES pass | **On** | `PresenceLook.cs` 101, 238; `PresenceView.cs` 1215–1228 | **Keep.** Tone-map pass stays. |
| F8 texture-size | Planned `Ctrl+Shift+F8` 2048/1024 | Not implemented | G-DEBUG / Phase 2 note only | **Remove the plan.** 1024 was optional and not warranted. |
| F9 debug blink | `Ctrl+Shift+F9` both lids | Debug only | `MainWindow.xaml.cs` 1082, 1100–1104; `PresenceView.cs` 369–381 | **Keep** `#if DEBUG`. Phase 8 A15 / Track 3. |
| F10 debug reload | `Ctrl+Shift+F10` `InvalidateScene` + double `LoadAsync` | Debug only | `MainWindow.xaml.cs` 1083, 1106–1109; `PresenceView.cs` 277–297, 383–388 | **Keep** `#if DEBUG`. Phase 8 / soak. |
| F11 debug morph | `Ctrl+Shift+F11` step morphs | Debug only | `MainWindow.xaml.cs` 1084, 1112–1116; `PresenceView.cs` 479– | **Keep** `#if DEBUG`. Phase 8 A15. |
| F12 look JSON + file watch | `Ctrl+Shift+F12` / watcher complete replace | Debug only | `MainWindow.xaml.cs` 1085–1086, 1118–1122; `PresenceView.cs` 390–470, 507–524; `PresenceLook.cs` 263–293 | **Keep** `#if DEBUG`. JSON never in Release. |

Developer decisions applied. Overlay 0.94 kept. Exposure removed (gain is the only brightness). `unlitMode` switch removed (one path). `toneMapBypass` dropped; `toneMapForceFail` kept. `srgbDecode` / `srgbEncode` / `toneMapEnabled` are no longer JSON keys (pipeline is baked; fail-closed if the technique cannot load). F8 plan removed.

### Step 3 — Reload GC diagnostic (debug-only, no product change)

`#if DEBUG` after each attach: LOH compact + `GC.Collect` + `WaitForPendingFinalizers` + `GC.Collect`, then working set, private bytes, `GC.GetTotalMemory(true)`. WeakReferences on retiring `TextureModel`s and scene roots. 6 × F10, 30 s apart (an extra n=7 arrived from an overlapping F10).

| n | retiredTex / aliveTex | retiredRoot / aliveRoot | working set | private bytes | gcTotal |
|---|---|---|---|---|---|
| 1 | 0 / 0 | 0 / 0 | 929,419,264 | 843,366,400 | 79,699,216 |
| 2 | 5 / 2 | 1 / 0 | 1,262,231,552 | 1,180,598,272 | 159,944,232 |
| 3 | 10 / 2 | 2 / 0 | +~150 MB | +~150 MB | ~159.8 MB |
| 4 | 15 / 2 | 3 / 0 | +~150 MB | +~150 MB | ~159.8 MB |
| 5 | 20 / 2 | 4 / 0 | +~150 MB | +~150 MB | ~159.8 MB |
| 6 | 25 / 2 | 5 / 0 | +~150 MB | +~150 MB | ~159.8 MB |
| 7 (extra) | 30 / 2 | 6 / 0 | 2,103,271,424 | 2,010,136,576 | 159,824,312 |

Managed heap is flat after the first real reload (~160 MB). Roots always die (`aliveRoots=0`). Exactly 2 `TextureModel`s stay alive while retired count grows — interned current maps, not an accumulating managed leak. Native working set / private still climb ~150 MB per reload.

**Verdict: not a managed leak. No product fix.** The native climb is inside Helix's GPU / texture cache (`ITextureResourceManager` exposes `Register` only; `TextureModel` has no `Dispose`). Options if a later track needs them: (1) keep F10 debug-only, no production reload; (2) hold Helix's shared texture proxy and `Detach` if that API is public and stable; (3) recreate `EffectsManager` on reload (nuclear). Do not poke private Helix members.

### Step 4 — Inventory applied

Removed: lit path (key, fill, ambient, env cube, bloom); both rims; even lights; PBR and emissive levers; saturation; dither; pitch; `toneMapPreScale`; exposure; `unlitMode` switch; `GlbTextureLocator`; unimplemented F8 plan; `toneMapBypass`.

Kept: approved pipeline (sRGB decode × gain → ACES → sRGB encode), gain, mip bias, camera / FOV, `SessionLockWatcher`, fail-closed tone map, `#if DEBUG` F9–F12 and `toneMapForceFail`.

Shader: one `fxc` recompile. `AcesTonemap.cso` SHA-256 `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3` (1948 bytes; was `e49c022f4b28e948fe60d26ad33a98b40149f19d0f5fc21d810e9de1d8400480`, 2744 bytes).

**Lines removed (working tree before → after):**

| File | Before | After | Δ |
|---|---|---|---|
| `PresenceView.cs` | 1564 | 1157 | −407 |
| `PostEffectToneMap.cs` | 444 | 270 | −174 |
| `GlbTextureLocator.cs` | 223 | deleted | −223 |
| `PresenceLook.cs` | full experiment surface (~300+) | 274 | slimmed to camera / gain / mip + DEBUG force-fail |
| `AcesTonemap.hlsl` | exposure / sat / dither / flags | 57 | approved pipeline only |

Known numeric drop: **804 lines** from `PresenceView` + tone-map core + `GlbTextureLocator`, plus the look-file and shader slims.

### Verify (after cleanup)

`dotnet build … -r win-x64`: **0 warnings, 0 errors.**

Cold start, no `presence-look.json`. Raw 1280×800 vs `P3-LOOK_approved_raw.png`:

| Compare | max | mean | changed |
|---|---|---|---|
| Full frame | 248 | 0.0828 | 691 |
| Bust crop (500, 90, 280, 400) | **0** | 0 | 0 |

Full-frame delta is the HUD clock (approved `14:08:07` vs cold `15:45:55`) and session id. Look is identical.

Background displayed `7,7,7` at (20,8), (20,400), (20,700) — same invert of token `#080808` as the approved raw. Token is still `ZolaBackground` `#080808`.

New defaults fingerprint (DEBUG, includes `toneMapForceFail=false`): `4392a2e0d851dc1e962c4ac5bfedf837e51c1645ed18d8bb044388fe346e83d8`. Old `22cd6f0a…` was the full experiment key set.

Static GPU (60 s, 1 s, sum of `GPU Engine(pid_*)\Utilization Percentage`): **avg 0.0012, max 0.0727**. Under the 1% budget.

Cleanup accepted.

### S31 — Helix native texture memory on reload (for lore closeout)

Developer accepted: **no managed leak**; native growth is inside Helix's texture registration on **reload only**. **No fix in this track.**

Evidence (debug-only forced GC after each F10 attach; 6 reloads, 30 s apart):

- `gcTotal` flat after the first real reload at **~160 MB** (n=2 `159,944,232` … n=7 `159,824,312`).
- Old scene roots collected every time (`aliveRoots=0` as `retiredRoots` grew 0→6).
- Exactly **two** interned `TextureModel`s stay alive (`aliveTextures=2`) while `retiredTextures` grew 5→30 — current maps, not an accumulating managed leak.
- Native working set / private still climb **~150 MB per scene reload** (n=2 `1,262,231,552` / `1,180,598,272` → n=7 `2,103,271,424` / `2,010,136,576`).

Helix 3.1.2: `ITextureResourceManager` exposes `Register` only; `TextureModel` has no `Dispose`.

Options (not taken here):

1. **F10 stays debug-only** — no production reload path.
2. Hold a **public shared-texture proxy** and `Detach` if that API is public and stable.
3. **Recreate `EffectsManager`** on reload (nuclear).

Ordinary lock, sleep and minimize **reuse the scene**, so production exposure is limited to genuine renderer failures.

**Live: approved look from defaults** at 1280×800. Overlay opacity 0.94. One unlit + ACES path.

## Phase 8 — Smoke Test

Scripts in `%TEMP%\p3look-smoke\` (outside the repo). Amended by the finish addendum: no backdrop / particles / brackets / bloom / glow steps; A14 cold start with no debug JSON; A15 morphs on the unlit material. Part B “final look” = approved on black.

Cold launch pid 23704 (`jsonPresent=False`). Fallback relaunch pids 6304 / 22460 (GLB missing) then restore 17872 / 13140. Client left at **1280×800**. Hermes HTTP 401 on typed turns is the environment API key, not a client BLOCK — the shell still went Thinking → Idle / error notice.

### Part A

| # | Result | Evidence |
|---|---|---|
| A1 | PASS | Cold 1280×800, first 3D frame `15:52:03.078`, PNG after 6 s. Approved look on black; dock hidden; notice `Session ready.` still up (resize at `15:52:04` reset the 4 s hold). Displayed background `7,7,7` at (20,8) and (20,400). `P3-LOOK_smoke_A1.png`. |
| A2 | PASS | Pointer in the bottom zone: dock shown, Mode `VOICE` 48×48. Pointer away: dock hides (`P3-LOOK_smoke_A2_hidden.png` / `A10_restored`). SetCursorPos-only click at the Mode seat left `VOICE` unchanged (IsHitTestVisible=false). An earlier click after Nudge revealed the zone then hit Mode (`VOICE`→`TEXT`) — script race, not a product fail. Deactivate/reactivate with the pointer in the zone: dock shown at once. `P3-LOOK_smoke_A2_shown.png`, `P3-LOOK_smoke_A2_hidden.png`, `P3-LOOK_smoke_A2_reactivate.png`. |
| A3 | PASS | Tab into dock: focus `SessionsButton` with a visible ring; still focused after 3 s. Tab out: focused id empty; dock hides. `P3-LOOK_smoke_A3_focus.png`, `P3-LOOK_smoke_A3_out.png`. |
| A4 | PASS | Long Text turn, pointer away: dock stayed up, Cancel `vis=True en=True 48×48`. After click: `15:58:29.697` `mode=Idle`, status `Interrupted.` Overlay open keeps the dock (A5). Overlay closed: dock hides. `P3-LOOK_smoke_A4_during.png`, `P3-LOOK_smoke_A4_after.png`, `P3-LOOK_smoke_A4_hidden.png`. |
| A5 | PASS | Conversation overlay open: dock stays visible. UIA `overlay=True`. `P3-LOOK_smoke_A5.png`. |
| A6 | PASS | Fine state: `DetailText` hidden / empty, status `Session ready.` Resume: no `Loading earlier` UIA (too brief to catch); session id changed `760405300` → `e9b0e5fd`. After resume, notice faded. `P3-LOOK_smoke_A6_after.png`. |
| A6b | PASS | Hermes 401 produced a sticky notice + `DetailText` (`The turn ended with an error.` / API key). `P3-LOOK_smoke_A12_typed.png`. A6b script then ran from post-Cancel `Interrupted.`; Ctrl+Space → `15:59:19` Listening, status `Session ready.`; next submit `Responding…` with `DetailText` cleared. `P3-LOOK_smoke_A6b_error.png`, `P3-LOOK_smoke_A6b_after_wake.png`, `P3-LOOK_smoke_A6b_after_ack.png`. |
| A7 | PASS | 900×640, overlay open: notice `Session ready.` at 277,597 82×18, composer X=589 — centred in the remaining band, clear of the overlay. `P3-LOOK_smoke_A7_900.png`. |
| A8 | PASS | Composer focused: amber underline, no system-accent. Crop 833,675 360×48. `P3-LOOK_smoke_A8.png`, `P3-LOOK_smoke_A8_full.png`. |
| A9 | PASS | Static GPU, 60 s, 1 s, sum of `GPU Engine(pid_23704*)\Utilization Percentage` (26 instances): **avg 0.0013, max 0.0771**. Under 1%. |
| A9b | PASS | After dock reveal/hide and a notice fade, 60 s same method: **avg 0.0007, max 0.0414**. No leftover loop. |
| A10 | PASS | Minimized 30 s: `16:03:48.623` `paused (minimized)` / `paused (hidden)`; `16:04:19.463` `resumed (minimized)` / `resumed (hidden)`. GPU while minimized **avg 0.0009, max 0.0268**. Bust after restore. `P3-LOOK_smoke_A10_restored.png`. |
| A11 | PASS | F10 `16:00:15.472` `import started` + `16:00:15.475` `load coalesced` + `16:00:15.873` first 3D frame. F11 `16:00:21.357` morph 2 BlinkBoth (both lids closed). Fallback: GLB renamed, UIA `PRESENCE UNAVAILABLE`, log `presence unavailable — GLB missing`; name restored, first 3D frame again. `P3-LOOK_smoke_A11_after_f10.png`, `P3-LOOK_smoke_A11_blink.png`, `P3-LOOK_smoke_A11_fallback.png`, `P3-LOOK_smoke_A11_restored.png`. |
| A12 | PASS | Typed send: `15:58:20` Thinking → `15:58:24` Idle; composer `focus=True` `en=True` after. Cancel mid-turn → Interrupted. Resume painted the stored session (`e9b0e5fd`). Hermes 401 on the bodies is environment. `P3-LOOK_smoke_A12_typed.png`, `P3-LOOK_smoke_A12_resume.png`. |
| A13 | PASS | 900×640 PNG 900×640; 1280×800 PNG 1280×800; maximized `GetWindowRect` **1936×1048**, PNG **1936×1048**. Bust fully inside; HUD clear. First 900/1280 pair had leftover BlinkBoth; replaced after Neutral. `P3-LOOK_smoke_A13_900x640.png`, `P3-LOOK_smoke_A13_1280x800.png`, `P3-LOOK_smoke_A13_maximized.png`. |
| A14 | PASS | Same cold start as A1; no `%LOCALAPPDATA%\ZolaClient\debug\presence-look.json`. Vs `P3-LOOK_approved_raw.png`: bust crop (500,90,280,400) **max 0 / mean 0 / changed 0**; full-frame max 248 / mean 0.094 (clock + session id only). Background `7,7,7` (invert of token `#080808`). `P3-LOOK_smoke_A14.png`. |
| A15 | PASS | Unlit material. F11 0 BlinkLeft (viewer-right lid), 1 BlinkRight (viewer-left lid), 2 BlinkBoth, 8 JawOpen, 14 TeethFV — each deforms the right feature. Crops 500,90 280×400. `P3-LOOK_smoke_A15_00_BlinkLeft.png`, `P3-LOOK_smoke_A15_01_BlinkRight.png`, `P3-LOOK_smoke_A15_02_BlinkBoth.png`, `P3-LOOK_smoke_A15_08_JawOpen.png`, `P3-LOOK_smoke_A15_14_TeethFV.png`. |

### Part B — Developer, by hand

| # | Result | Evidence |
|---|---|---|
| B1 Final look | PASS | Developer. Approved look on black, no backdrop. |
| B2 Dock feel | PASS | Developer, including the P3-D17 footprint reveal. |
| B3 Reduced motion | PASS | Developer. |
| B4 Lock | PASS | Developer. |
| B5 Voice run-through | PASS | Developer. |

Developer: `smoke test passed` (2026-09-28). Also asked to hide the WinUI `Ctrl+Space` accelerator tooltip (`RootGrid.KeyboardAcceleratorPlacementMode=Hidden`); the hotkey still works.

### Part C

Stopped serve python **7748** (listen `127.0.0.1:60923`) and parent **7152** (`python -m hermes_cli.main -p zola serve --isolated`). Did not stop `Zola.Client` pid **16324**.

- UIA: `LinkText` = **OFFLINE**; `SessionText` still **SESSION 365d43b3**; status sticky `Backend unreachable. The remote party closed the WebSocket connection without completing the close handshake.`; `DetailText` visible (`hermes serve is not reachable…`); Composer / Mic / Mode disabled; window still open.
- Log: `09:15:29.325` `fact unreachable=true` then `mode=Dormant link="OFFLINE"`.

`P3-LOOK_smoke_C.png`

**Result:** `smoke test passed`. Developer: `proceed to closeout` (2026-09-28).

### P3-D17 amendment (developer decision, Phase 8)

Smoke finding: the dock jittered near its edge, and the full-width `DockRevealZoneHeight` (120) strip revealed it from the bottom-left and bottom-right corners.

Developer rule:

- Reveal region is the dock's own layout bounds (measured while hidden), inflated by token `DockRevealMargin` (12). `DockRevealZoneHeight` is removed.
- Decide by pointer position on root `PointerMoved` against that rectangle. Do not use the dock's enter/exit events (hit-testing toggles while hidden and flip-flops).
- Idempotent: start a fade only when the target state changes; never restart one already heading to the same state. The hide timer starts once on leave; re-entering cancels it.
- Hysteresis: once visible, stay visible until the pointer is outside the inflated rectangle, then `DockHideDelaySeconds`.
- Keyboard focus, an open panel and `_streaming` still force it visible. Hidden is still opacity 0 plus no hit-testing.

Logged as `P3-LOOK: dock shown` / `P3-LOOK: dock hidden` in `display-state.log` only on a real target change. Hermes 401s remain the environment API key; the developer will fix that before Part B.

`dotnet build … -r win-x64` after the amendment: **0 warnings, 0 errors.**

Re-run of A2–A5, A2b and A9b in this session: **NEEDS-HUMAN.** `SetCursorPos` returns false and the cursor stays at a fixed screen point (`339,350`); Tab also never entered the dock. Input injection is locked (not a product fail). Layout probe while the pointer could be read: dock host `~490,714 301×62` at 1280×800 (centred, above the 24 px margin) — the full-width strip is gone. Part B should include A2 / A2b by hand: hover only the pill (not the bottom-left/right corners), and slowly cross the edge — one show and one hide per crossing.

Developer: hide the WinUI `Ctrl+Space` accelerator tooltip (`RootGrid.KeyboardAcceleratorPlacementMode=Hidden`). The hotkey still works.

## Closeout

- Tests: N/A (no automated suite).
- `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`: 0 warnings, 0 errors (closeout 9a).
- `hermes-agent` `git status` clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- No debug JSON, `%TEMP%\p3look-smoke\` scripts, or Android reference PNGs staged. Diagnostic `P3-LOOK_smoke_A2_probe.png` moved to `%TEMP%\p3look-smoke\`. No new images under `windows-client/`.
- Packages unchanged from Track 3: `HelixToolkit.SharpDX.Assimp` 3.1.2, `HelixToolkit.WinUI.SharpDX` 3.1.2, `Microsoft.WindowsAppSDK` 2.5.1, `Microsoft.Windows.SDK.BuildTools` 10.0.26100.4654, `System.Management` 9.0.4. One `EmbeddedResource` line for `AcesTonemap.cso` (`P3-D19`).
- No lore file updates (G-LORE-SCOPE).

### Android pipeline (root cause)

Android's look is not lighting-driven. Helix PBR plus key/fill/rim/bloom produced orange skin, mesh flecks, and no highlight headroom. Android's path is unlit albedo: sRGB→linear × gain, ACES Narkowicz, linear→sRGB; shading is baked in the texture. Experiment U implemented that path (`EnableUnLit`, gain 4.4, mip LOD bias 0.75) and is the approved look (`P3-D20`).

### Process lessons

1. **Raw live captures only.** Tuning judgements used live client-area rasters written from the running window, not chat-embedded, cropped, or scaled screenshots.
2. **Complete configurations from reset.** Every look replace started from `CreateDefault()` with the full required-key set. Partial merges of leftover experiment keys were not used for live variants.

### Look approved

Developer judgement (verbatim): "dark skin carrying gold from her own texture, white-gold eyes, glowing diamond and lit hair tips; dots softened; reads like Android."

**Backdrop: deferred (`P3-D21`).**

Approved cold-start defaults after inventory (DEBUG fingerprint `4392a2e0d851dc1e962c4ac5bfedf837e51c1645ed18d8bb044388fe346e83d8`):

| key | default |
|---|---|
| `cameraX` / `cameraY` / `cameraZ` | `0` / `0.05` / `3.15` |
| `lookX` / `lookY` / `lookZ` | `0` / `0` / `−3.372` |
| `fov` | `35` |
| `toneMapGain` | `4.4` |
| `mipLodBias` | `0.75` |
| `toneMapForceFail` | `false` (`#if DEBUG` only) |

Reference samples (1280×800, `P3-LOOK_approved_raw.png`):

| region | xy | sample |
|---|---|---|
| cheek | 590,348 | `90,42,8` |
| hair | 660,90 | `169,102,35` |
| chest | 640,620 | `135,66,14` |
| forehead | 620,218 | `87,51,25` |
| background | 20,400 | `7,7,7` (invert of token `#080808`) |

Pipeline: unlit `DiffuseMaterialCore` `EnableUnLit`; sRGB decode × gain → ACES Narkowicz → sRGB encode; `MinMagMipLinear` + `mipLodBias` 0.75. Overlay opacity **0.94**.

### Inventory decisions

Applied (Step 4): removed the lit path, rims, even lights, PBR/emissive levers, saturation, dither, pitch, pre-scale, exposure, `unlitMode` switch, `GlbTextureLocator`, unimplemented F8, `toneMapBypass`. Kept the approved pipeline, gain, mip bias, camera/FOV, `SessionLockWatcher`, fail-closed tone map, `#if DEBUG` F9–F12 and `toneMapForceFail`. Overlay 0.94 kept.

### Texture, memory, disposal

| Measure | Value |
|---|---|
| Texture size | **2048²** (1024² not run; cold rest 809 MB < 900 MB) |
| Cold load | **906 ms** import / **2388 ms** wall |
| Peak WS during load | 1,052,942,336 (**1004 MB**) |
| Cold rest | WS 848,560,128 (**809 MB**) / private 778,018,816 (742 MB) |
| Soak without `Dispose` | idle +1124 MB vs cold rest |
| Soak after KC11 `SceneNode.Dispose` | idle +1083 MB vs cold rest |
| Explicit disposal | **not added** — node `Dispose` did not stop the native climb; `TextureModel` has no `Dispose` |
| S31 | not a managed leak; native ~150 MB/reload inside Helix texture registration; F10 stays debug-only |

### ACES (`P3-D19`)

- Compile: `"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe" /T ps_5_0 /E main /Fo AcesTonemap.cso AcesTonemap.hlsl`
- `.cso` SHA-256 `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3` (1948 bytes)
- T2 identity vs prior bust crop: max delta 0 with the pass off. Inventory removed the off switch; the approved pipeline stays on.
- Failure disables the pass and logs `P3-LOOK: tone map unavailable — …`.
- No package or MSBuild compile step.

### Smoke

HUMAN-RUN passed 2026-09-28 (Part A A1–A15, Part B B1–B5, Part C fail-closed OFFLINE). See Phase 8.

### Figures

| Measure | Value |
|---|---|
| Static GPU 60 s (A9) | avg **0.0013%**, max 0.0771% |
| After dock/notice fades (A9b) | avg 0.0007%, max 0.0414% |
| Minimized 30 s (A10) | avg 0.0009%, max 0.0268% |
| After inventory cleanup | avg 0.0012%, max 0.0727% |
| Dock | `DockRevealMargin` 12; `DockHideDelaySeconds` 2; `DockFadeMilliseconds` 180 |
| Notice | `NoticeHoldSeconds` 4; sticky on unreachable / switch / history / last-turn error |
| Overlay | opacity 0.94 |
| Mantra indent | `100,0,0,0` |
| Glyphs | Voice/Text `U+E8AB`, Sessions `U+E81C` |

### Final file list

New:
- `windows-client/Zola.Client/Presence/PostEffectToneMap.cs`
- `windows-client/Zola.Client/Presence/PresenceLook.cs`
- `windows-client/Zola.Client/Presence/Shaders/AcesTonemap.hlsl`
- `windows-client/Zola.Client/Presence/Shaders/AcesTonemap.cso`
- `zola-architecture/lore/prompts/progress/P3-LOOK_Progress.md`
- progress PNGs `P3-LOOK_*.png` (tuning rounds, overlay, approved raw, Phase 8 smoke A1–A15 / C)

Deleted:
- `windows-client/Zola.Client/Presence/GlbTextureLocator.cs`

Modified:
- `windows-client/Zola.Client/MainWindow.xaml`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `windows-client/Zola.Client/Presence/PresenceView.cs`
- `windows-client/Zola.Client/Themes/ZolaTokens.xaml`
- `windows-client/Zola.Client/Zola.Client.csproj`
- `zola-architecture/lore/build-plans/PHASE3_BUILD_PLAN.md` (v1.6 in this implementation commit)

Already on `main` (Phase 1): plan v1.4 at `4609c697937d2a5300897ec4575c02b38357f720`.

### Exit criteria (PHASE3_BUILD_PLAN.md Track 4 v1.6)

- ✅ MET — Look values are named constants in `PresenceLook.cs` (`DefaultToneMapGain` 4.4, `DefaultMipLodBias` 0.75, camera/look/fov, ACES Narkowicz constants). Unlit + sRGB/ACES is the only path.
- ✅ MET — Developer judgement recorded verbatim: "dark skin carrying gold from her own texture, white-gold eyes, glowing diamond and lit hair tips; dots softened; reads like Android." Cheek/hair/chest samples recorded above.
- ✅ MET — No backdrop geometry (`P3-D21`). Displayed background samples `7,7,7` (invert of token `#080808`).
- ✅ MET — No corner brackets and no particles. Particle field moves to Track 5.
- ✅ MET — Dock: one decider `UpdateDockVisibility` (`P3-D17`, footprint + `DockRevealMargin` 12). Notice: one decider `UpdateNoticeVisibility` (`P3-D18`). Existing `StatusText`/`DetailText` writers unchanged (diff: flags and readers only).
- ✅ MET — Shell polish: composer amber underline, overlay 0.94, notice readable at 900 px with overlay open, Switch/History glyphs, mantra indent 100.
- ✅ MET — Look JSON read only under `#if DEBUG`; `presence-look.json` is not committed.
- ✅ MET — ACES pass (`P3-D19`): T2 off-path identical to before; failure disables and logs; `.hlsl`/`.cso` committed with compile command and SHA; no package/build-step; static GPU ≤ 1% with it on.
- ✅ MET — Reload memory re-measured at 2048². KC11 `Dispose` did not stop the native climb; explicit disposal not added (S31).
- ✅ MET — Texture stays 2048². Cold rest 809 MB, peak 1004 MB, load 906 ms / 2388 ms wall.
- ✅ MET — Inventory of disabled experiment paths listed, keep/remove applied, no dead switches left without a recorded reason.
- ✅ MET — Static GPU with approved look avg 0.0013% over 60 s (≤ 1%). Lazy rendering holds after dock/notice fades.
- ✅ MET — `hermes-agent` clean at `345cd2b0`.
- ✅ MET — `dotnet build … -r win-x64` 0 warnings.
- ✅ MET — HUMAN-RUN smoke passed (2026-09-28).

### SHAs

- Plan v1.4 commit on `main`: `4609c697937d2a5300897ec4575c02b38357f720`
- Implementation commit: `624dd20268de392e6969284aac4bec515944fa69`
- Merge SHA on `main`: `c8f666251deacaf0fcb6a714594abf44da2e931b`


