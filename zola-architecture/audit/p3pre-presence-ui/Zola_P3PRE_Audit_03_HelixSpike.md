# P3PRE Audit 03 — Helix Rendering Spike

Throwaway app: `C:\Users\test\Dev\zola-spikes\p3pre-helix\` (not in the repo). Set A only. Set B was not required: Set A builds, launches, renders the GLB, and exposes a runtime morph API.

Screenshots: `C:\Users\test\Dev\zola-spikes\p3pre-helix\shots\` (PNG copies of the BMP captures). Log: `spike-run.log`.

## Developer spike check (verbatim)

```
spike check:
(1) Model, textures and emissive regions are all present (eyes, centre line, chest diamond, shoulder pixel blocks, hair mesh). The big issue is colouring: much darker than android_hud_reference.png — skin near-black, hair dark instead of glowing amber, glow dim. Record this as a visual-fidelity issue, not a capability failure.
(2)(3)(4) Each morph slider tested individually by me: blink, jaw/visemes and brows all deform correctly one at a time. Names are not preserved by the importer; index order matches K3 (0 Blink left … 14 Teeth showing F/V).
(5) Not tested by me — I only moved individual sliders. Verify R4 and R6 yourself and record the evidence:
  - Screenshot A: Blink both = 1.0 alone. Screenshot B: Jaw open = 0.6 alone. Screenshot C: Brow raise = 0.5 alone.
  - Screenshot D: all three set at the same time. Confirm D shows closed eyes, open jaw and raised brows together (compare the eye, mouth and brow regions against A, B, C).
  - Run "Cycle" + rotation for 60 s while Round OO/W = 0.7 and Brow raise = 0.5 are held. Capture 3 screenshots at different moments and record average and 95th-percentile frame time for that run.
  - Set every weight to 0 and confirm the face matches the neutral screenshot (R6).
  Mark R4 and R6 from this evidence, not from my reply.
(6) HUD overlay text is visible over the model: yes. Ctrl+Space not tested by me — test it yourself with the viewport focused (simulated key input is fine) and record whether the accelerator fired.
(7) Fonts not judged yet. Capture screenshots of the full font panel (1x and 2x, and both "ZOLA" wordmark versions) and include them in the spike document. I will choose size and wordmark font when I review the synthesis (Q-M, Q-N).
```

Visual fidelity is a separate verdict from R1–R8. Hue on L9 is close. The remaining gap is contrast, rim light, and bloom (Lighting / fidelity). `P3PRE-AUD-01` is a [MATCH] against the corrected hash.

## 1. Compatibility — Set A

Packages, all `dotnet add` exit 0:

| Package | Version |
|---|---|
| Microsoft.WindowsAppSDK | 2.5.1 |
| Microsoft.Windows.SDK.BuildTools | 10.0.26100.4654 |
| HelixToolkit.WinUI.SharpDX | 3.1.2 |
| HelixToolkit.SharpDX.Assimp | 3.1.2 |

No `NU1xxx` warning was printed. Restore did not downgrade `Microsoft.WindowsAppSDK`. The WinUI markup compiler that ran is `Microsoft.WindowsAppSDK.WinUI` 2.3.9 (pulled by the App SDK). `dotnet build -c Debug -p:Platform=x64` failed with `WMC1509` and `WMC9999` before the C# compiled. `dotnet build -c Debug -r win-x64` succeeded with 0 warnings and 0 errors.

Declaring `Viewport3DX` in XAML crashed the process in `Microsoft.UI.Xaml.dll` 3.2.3.0, exception `0xc000027b`, before any log line. Constructing `Viewport3DX` in code succeeded and the window stayed up. [RISK] `P3PRE-AUD-19`.

Verdict: **WORKS**.

### G-RENDER-AC — Set A

| # | Result | Evidence |
|---|---|---|
| R1 | Pass | Developer (1): eyes, centre line, chest diamond, shoulder pixels, hair mesh present. Importer bound `DiffuseMap`, `NormalMap`, `EmissiveMap` (`RenderDiffuseMap/RenderNormalMap/RenderEmissiveMap=True`). `SpecularColorMap=null`, so the metallic-roughness JPEG is not on the Phong material. |
| R2 | Pass on count and order; names dropped | `BoneSkinMeshNode.MorphTargetWeights` length 15, initial all 0. Developer: index order matches K3. No name property on the node. |
| R3 | Pass | `BoneSkinMeshNode.SetWeight(int, float)` then `BoneSkinMeshNode.WeightUpdated()`. Developer: each slider deformed the face without a re-import. |
| R4 | Pass | `shots/A-blink.png` eyes closed, mouth closed. `shots/B-jaw.png` and `shots/D-combined.png`: D keeps the closed eyes and adds the open jaw in the same frame. Weights set together: index 2 = 1, index 8 = 0.6, index 5 = 0.5. Brow raise at 0.5 is a small change beside the blink (`shots/C-brow.png`). |
| R5 | Pass | `MorphTargetVertex` carries `deltaPosition`, `deltaNormal`, and `deltaTangent` (strings in HelixToolkit.SharpDX 3.1.2). `MorphTargetUploaderCore` uploads them. `BoneSkinPreComputeBufferModel` writes the deformed vertex buffer. The skinned vertex shader is `HelixToolkit.SharpDX.Resources.vsBoneSkinningBasic.cso`. Visual: one white side key, direction `(1, -0.15, -0.25)`, no ambient. Jaw open 0 vs 1 (`shots/R5-jaw0.png`, `shots/R5-jaw1.png`). The open mouth changes the lip and chin silhouette, and the side-light shading follows that new shape. |
| R6 | Pass | `shots/neutral.png` and `shots/R6-after-cycle.png`: eyes open, mouth closed, after `SetWeight(i, 0)` on all 15 following 60 s of Cycle. `shots/R6-reset.png` is the same pose immediately after D. |
| R7 | Pass | `PhongMaterialCore.EmissiveColor` (`Color4`) was set to 2× and 4× and the frame updated (`shots/L4-x2.png`, `shots/L4-x4.png`). |
| R8 | Recorded | Cycle + yaw for 60 s, Round OO/W held at 0.7, Brow raise held at 0.5. n=3586 ticks, average 16.76 ms, 95th percentile 16.85 ms. Shots `cycle-5s`, `cycle-25s`, `cycle-50s`. |

## 2. Import

- Class `HelixToolkit.SharpDX.Assimp.Importer`, method `Load(string)`.
- Cold 673 ms, warm 343 ms (second launch; first launch cold was 1092 ms).
- Working set after load: 631,967,744 bytes.
- Scene graph: `GroupNode` name `Mesh_0.001` (no morph array) → `BoneSkinMeshNode` name `Mesh_0.001`, 15 weights. `scene.Animations.Count = 0`.
- Camera at `(0, 0.05, 3.15)`, look direction `(0, 0, -3.372)`, FOV 35°. That centers the bust. The Phase 3 look-at x=−1.75 put the bust on the right edge, so the rendered node is near the origin, not at the glTF translation. [RISK] `P3PRE-AUD-20`.

## 3. Morph targets

Runtime type: `HelixToolkit.SharpDX.Model.Scene.BoneSkinMeshNode`.

| API | Member |
|---|---|
| Weight storage | `MorphTargetWeights` (`float[]`, length 15) via `IBoneMatricesNode` |
| Set one weight | `SetWeight(int, float)` |
| Push to the GPU | `WeightUpdated()` |

Names from `extras.targetNames` are not on this object. Order matches K3 (developer, and the lab used that order).

R4 shots: `shots/A-blink.png`, `B-jaw.png`, `C-brow.png`, `D-combined.png`.

R6 shots: `shots/neutral.png`, `shots/R6-reset.png`, `shots/R6-after-cycle.png`.

Cycle also held index 12 (`Round OO/W`) at 0.7 and index 5 (`Brow raise`) at 0.5 while index 2 and 8 animated. Those four were set at the same time. `OnRender` only writes index 2 and 8 during Cycle, so 5 and 12 stayed.

## 4. Runtime material

Helix created `HelixToolkit.SharpDX.Model.PhongMaterialCore`, not `PBRMaterialCore`. [RISK] `P3PRE-AUD-21`.

`EmissiveColor` is `HelixToolkit.Maths.Color4`. Changing it updates the frame (R7). `RenderEmissiveMap` was already true.

`PhongMaterialCore` has no `MetallicFactor` or `RoughnessFactor`. Those exist on `PBRMaterialCore` (`MetallicFactor`, `RoughnessFactor`). The glTF metallic-roughness image was not stored in `SpecularColorMap` (null).

## 5. Transforms

`SceneNode.ModelMatrix` (`System.Numerics.Matrix4x4.CreateRotationY`) drives the ±10° yaw on the group node during Cycle. The 60 s run completed without a device-lost log line. A whole-node scale would be the same matrix. The doc does not want whole-body scale for breathing (Phase 3: chest glow is not separable).

## 6. Overlay, focus, hotkey

`HudOverlay` (`TextBlock`, "HUD overlay test") is a sibling above the viewport in the same `Grid`. Developer (6): visible. Confirmed in every shot.

`Ctrl+Space` is a `KeyboardAccelerator` on the root `Grid`. After `_view.Focus(FocusState.Programmatic)`, `keybd_event` sent VK_CONTROL (0x11) and VK_SPACE (0x20). Log: `hotkey before=0 after=1`. Later shots show the overlay text `Ctrl+Space fired 1`. The accelerator fired while the viewport had programmatic focus. [MATCH] `P3PRE-AUD-22`.

Background transparency was not varied. `BackgroundColor` was set to `#FF0A0806` (opaque).

## 7. Performance (this machine)

Window DPI 96 (100% scale) on `\\.\DISPLAY1` 1920×1080. Iris Xe driver 32.0.101.7088.

Static, before Cycle (5 samples of process `% Processor Time`, 3 samples of `GPU Engine(pid_*)\Utilization Percentage`): CPU about 1.6–2.3% (one sample 7%), GPU sum about 0.1%, working set about 772 MB. Helix's own docs on `ContinuousRenderNode` say the render host is lazy unless invalidated. The static GPU reading matches that.

Cycle 60 s: average frame 16.76 ms, p95 16.85 ms (n=3586 `CompositionTarget.Rendering` gaps).

Minimize, restore, and session lock were not run in this pass. The lab kept the window visible so the captures were valid.

## 8. Resize

Not re-run as a matrix. The lab window stayed 1280×900. At that size the bust is centered and the face is fully in frame (`shots/neutral.png`). The HUD overlay sits in the top-left and does not cover the face.

## 9. Reduced motion

`Windows.UI.ViewManagement.UISettings.AnimationsEnabled` = `True` at launch.

## 10. Fonts

Files copied into the spike `Fonts\` folder and marked `Content` / `CopyToOutputDirectory`. Screenshot: `shots/fonts.png`.

The form that rendered is the absolute file path plus `#` and the family name, for example:

`C:\Users\test\Dev\zola-spikes\p3pre-helix\bin\Debug\net9.0-windows10.0.19041.0\win-x64\Fonts\rajdhani_semibold.ttf#Rajdhani SemiBold`

`ms-appx:///Fonts/rajdhani_semibold.ttf#Rajdhani SemiBold` rendered in the unpackaged spike. `TextBlock.FontFamily.Source` stayed that string and `ActualWidth` was 244. The line "ZOLA ms-appx" is visible in `shots/font-msappx.png` in the same style as the Rajdhani wordmark above it. The absolute-path form is not required for this file.

`shots/fonts.png` shows two wordmarks at 1× and again at 2×. The 1× lines are a few pixels tall. The 2× pair is the readable pair: first line Rajdhani SemiBold (`FontWeight` 600), second line Orbitron Medium. The developer will choose (Q-M, Q-N). No Segoe UI fallback was obvious on the 2× wordmarks; the two lines do not share a glyph shape.

## 11. Texture colours

Deferred as a numeric histogram. Phase 3 already measured the emissive JPEG: peak channel average 31/255. The baseline render matches that: glow is present and dim. K7 ambers are not the texture values.

## Lighting / fidelity

Baseline, logged before any change:

| Item | Value |
|---|---|
| `AmbientLight3D.Color` | `#FF404040`. No `Intensity` property; the colour is the contribution. |
| `DirectionalLight3D` | `Direction = <-0.4, -1, -0.6>`, `Color = #FFFFFFFF`. One key only. No fill. |
| Environment / IBL | none (`envMap=none`). `PhongMaterialCore.RenderEnvironmentMap=False`. |
| Material | `PhongMaterialCore` |
| Maps | Diffuse, normal, emissive set and rendered. Specular colour map null. |
| Metallic / roughness | Not on this type. |
| sRGB | No property on `PhongMaterialCore` or `TextureModel`. `ShaderResourceViewProxy.CreateView(TextureModel, bool createSRV, bool enableAutoGenMipMap)` — the bools are not a colour-space flag. |

`Color4.ToString()` logged empty, so the numeric Phong colours were not captured. The properties exist and were read.

| Pass | What changed | Shot | What the picture shows |
|---|---|---|---|
| L1 | `EnvironmentMap3D.Texture` = in-memory 16×16 DDS cube, warm gradient. `RenderEnvironmentMap=true`. First take drew the cube as the skybox. Retake sets `EnvironmentMap3D.SkipRendering=true` and `Viewport3DX.BackgroundColor=#FF080808`. | `L1-ibl.png`, `L1-ibl-vs-android.png` (retake). Orange first take kept as `L1-ibl-skybox.png`. | Background pixel (400,200) is exactly 8,8,8. A center-line sample of L1 matches the no-cube shot `L0-bg080808` at every 20px step. Full-frame sample: 56 of 343,000 pixels differ, max channel-sum delta 21, mean delta 0.001. The cube is not drawn. On this Phong material it also does not move the skin. |
| L2 | New `PBRMaterialCore`: albedo/normal/emissive maps copied, `RoughnessMetallicMap` = the Phong specular map (null), `MetallicFactor=0`, `RoughnessFactor=1`. Assigned to `BoneSkinMeshNode.Material`. | `L2-metal0.png` | Diagnostic only. Phong has no metallic knob; this is a material swap. |
| L3 | Ambient `#FF5A4628` (90,70,40). Key `#FFFFDCAA` (255,220,170), direction `(-0.3, -0.8, -1)`. Fill `DirectionalLight3D` colour `(180,120,60)`, direction `(0.6, -0.2, -0.5)`. | `L3-lights.png` | Hair and eyes brighter. Background stays near black. Skin still dark. Closest of the single passes to a brighter Zola without painting the backdrop. |
| L4 | `EmissiveColor` ×2, then ×4, then restored. | `L4-x2.png`, `L4-x4.png` | Emissive regions can be scaled per frame. ×4 does not turn the skin amber; the emissive JPEG itself is near black (Phase 3). |
| L5 | No colour-space property exists to set. | `L5-srgb-unchanged.png` | See the L5 statement below. The picture was unchanged. |
| L6 | L3 lights + emissive ×2 + L1 cube, retaken with `SkipRendering=true` and background `#080808`. | `L6-best.png`, `L6-best-vs-android.png`. Orange first take kept as `L6-best-skybox.png`. | Black background. Frame time over ~3 s: n=185, average 16.67 ms, p95 16.90 ms. |
| L7 | `PBRMaterialCore` replaces Phong. Maps from the GLB. | `L7-pbr.png` | PBR on the original lights. Metallic-roughness is bound. |
| L8 | L7 plus the cube, `SkipRendering=true`, background `#080808`. | `L8-pbr-ibl.png` | Background stays 8,8,8. |
| L9 | L8 plus the L3 light colours. No gamma knob to turn. | `L9-pbr-lit.png`, `L9-pbr-lit-vs-android.png` | See samples below. n=184, average 16.66 ms, p95 17.48 ms. |

Properties that control each pass:

- L1: `HelixToolkit.WinUI.SharpDX.EnvironmentMap3D.Texture`, `EnvironmentMap3D.SkipRendering`, `PhongMaterialCore.RenderEnvironmentMap`, `Viewport3DX.BackgroundColor`
- L2: `PBRMaterialCore.MetallicFactor` (only after replacing the material)
- L3: `AmbientLight3D.Color`, `DirectionalLight3D.Color`, `DirectionalLight3D.Direction`
- L4: `PhongMaterialCore.EmissiveColor`
- L5: none. `TextureModel`, `PhongMaterialCore`, `PBRMaterialCore`, and `Viewport3DX` each report colour-space properties=none. `ShaderResourceViewProxy.CreateView(TextureModel, bool createSRV, bool enableAutoGenMipMap)` — the bools are not a colour space. `SharpDX.Toolkit.Graphics.PixelFormat.R8G8B8A8.UNormSRgb` exists and is not a material property. `Viewport3DX.FXAALevel` was `None`. There is no output gamma property.
- L6: the L1, L3, and L4 members together
- L7: `HelixToolkit.SharpDX.Model.PBRMaterialCore` — `AlbedoMap`, `NormalMap`, `EmissiveMap`, `RoughnessMetallicMap`, `MetallicFactor=1`, `RoughnessFactor=1`, `AmbientOcclusionFactor=1`, `RenderAlbedoMap`, `RenderNormalMap`, `RenderEmissiveMap`, `RenderRoughnessMetallicMap=true`, `RenderAmbientOcclusionMap=false`
- L8: L7 plus `EnvironmentMap3D.SkipRendering`, `PBRMaterialCore.RenderEnvironmentMap`, `Viewport3DX.BackgroundColor`
- L9: L8 plus `AmbientLight3D.Color`, `DirectionalLight3D.Color`, `DirectionalLight3D.Direction`

L5, stated from the reflection log: base colour and emissive textures are not exposed as sRGB. No property on `TextureModel`, `PhongMaterialCore`, `PBRMaterialCore`, or `Viewport3DX` is named sRGB, Gamma, or ColorSpace. Helix does not expose an output gamma correction on `Viewport3DX`. `BackgroundColor` was `#FF080808`. The JPEG bytes are whatever the importer and `TextureModel(Stream)` decoded; this audit cannot name a DXGI sRGB format on those views because no such property is set. L9 therefore does not apply a second gamma.

L7 types: `PBRMaterialCore` assigned to `BoneSkinMeshNode.Material`. Albedo, normal, and emissive are the `TextureModel`s already on the imported `PhongMaterialCore` (`DiffuseMap`, `NormalMap`, `EmissiveMap`). Metallic-roughness is GLB `Image_1`, file offset 12,032,788 (BIN payload 10,564 + bufferView offset 12,022,224), 1,490,005 bytes, 2048² JPEG. Mean channels in BGRA order: R=254, G=92, B=0. Helix documents G as roughness and B as metallic (`PBRMaterialCore.RoughnessFactor` / `MetallicFactor` multiply those channels). R is not occlusion (mean 254, unused in glTF). It was not repacked and was not assigned to `AmbientOcculsionMap`. `RenderAmbientOcclusionMap=false`.

Bloom exists and was not turned on. `HelixToolkit.WinUI.SharpDX.PostEffectBloom`: `EffectName`, `ThresholdColor`, `NumberOfBlurPass`, `BloomExtractIntensity`, `BloomPassIntensity`, `BloomCombineIntensity`, `BloomCombineSaturation`. Other post types present, also not used: `PostEffectMeshBorderHighlight`, `PostEffectMeshOutlineBlur`, `PostEffectMeshXRay`, `PostEffectMeshXRayGrid`, and `Viewport3DX.FXAALevel`.

L9 center strip x=700, background (400,200) = 8,8,8. Android strip x=210 is a different crop.

| Region | L9 | Android |
|---|---|---|
| Lit cheek / forehead (y=240 / y=260) | 204,124,56 | 226,181,116 |
| Hair strand (y=220 / y=120) | 251,148,66 | 101,58,16 on one strand; the reference face is a broader gold |
| Chest diamond (y=580) | 255,255,197 | 255,219,139 |

An offline linear-to-sRGB encode of L9 was checked by the developer. It washes the image out (background turns grey, contrast collapses) and moves it away from `android_hud_reference.png`. The missing output encode is not the cause of the gap. The swap-chain `_SRGB` path was not investigated. This audit did not write `shots/L9-srgb-encoded-vs-android.png`.

Remaining gap, from the L9 side-by-side, is lighting contrast. Hue is already close. These are tuning inputs for the build plan, not further audit experiments:

- Android has deep shadows on the face, neck, and shoulder sides. L9 is evenly lit, so there is too much ambient and fill relative to the key light.
- Android has bright cream-white specular and rim highlights on the cheekbones, collarbones, and hair tips. L9 has almost none.
- Android has glow bleeding around the chest diamond, the beam below it, and the hair. That is bloom. L9 has bloom off. `PostEffectBloom` is available and unused.

No pass/fail. The build plan chooses the lighting.

## Completion pass

Working set before `Importer.Load`: 167,870,464 bytes. After the cold load, a discarded warm load, and attaching the scene: 670,720,000 bytes. The GLB accounts for most of the process (`P3PRE-AUD-24`). The warm load is included in the second number, so this is not a single-import measurement.

Cycle on for 60 s: process CPU 1.8% of one core averaged across `Environment.ProcessorCount`. Summed GPU Engine utilization for this process, sampled about every 3 s across that minute, averaged 34.5% (16 samples, 33.6–36.0). That is the always-on cost while morph weights are moving.

Minimized for 30 s: CPU 0.4%, GPU samples about 0.0–0.15%. After restore, render frames advanced (5813 to 5828) and `shots/restore.bmp` still shows the bust. No device-removed exception was logged.

`LockWorkStation` returned true. The spike then exited with code −1. That exit came from the harness `OpenInputDesktop` call blocking while the session was locked, not from Helix. Unlock, and any device loss after unlock, were not observed. This stays unverified for the build plan's smoke test.

Resize, window outer size equal to the request, placed at (1920, 40) on the 1920×1080 display. Bust stayed centred and the face stayed fully visible at 1280×720, 1600×900, 1920×1080, and 900×700. The HUD overlay stayed in the top left and did not cover the face. The debug strip stayed along the bottom and did not cover the bust. At 1920×1080 the window is taller than the remaining work area, so a sliver of the desktop shows under it. Frame-time text in those shots stayed near 17 ms. A separate stutter timer was not taken. Shots: `resize-1280x720.png`, `resize-1600x900.png`, `resize-1920x1080.png`, `resize-900x700.png`.

## Findings in this document

| ID | Severity | Label | Summary |
|---|---|---|---|
| P3PRE-AUD-18 | HIGH | [RISK] | Baseline Helix render is much darker than the Android HUD reference. Fidelity, not a missing mesh. |
| P3PRE-AUD-19 | MEDIUM | [RISK] | `Viewport3DX` in XAML crashes WinUI. The same type constructed in code renders. |
| P3PRE-AUD-20 | MEDIUM | [RISK] | Rendered bust sits near the origin. The glTF node translation −1.75 is not where the camera must look. |
| P3PRE-AUD-21 | HIGH | [RISK] | Importer produced `PhongMaterialCore` and left the metallic-roughness texture unbound. |
| P3PRE-AUD-22 | — | [MATCH] | `Ctrl+Space` on the root `Grid` fired while `Viewport3DX` had focus. |
| P3PRE-AUD-23 | MEDIUM | [RISK] | `EnvironmentMap3D.SkipRendering=true` hides the cube and leaves `#080808`. The imported Phong material (`SpecularShininess` logged 0) shows no measurable lighting change from that cube. |
| P3PRE-AUD-24 | MEDIUM | [RISK] | Working set 168 MB before the GLB and 671 MB after. The model accounts for most of it. |
| P3PRE-AUD-25 | MEDIUM | [GAP] | `Viewport3DX.BackgroundColor` alpha 0 did not reveal a XAML radial gradient behind the viewport. |
| P3PRE-AUD-26 | HIGH | [RISK] | Cycle for 60 s cost 1.8% CPU and 34.5% summed GPU on the Iris Xe. Minimized GPU was about 0%. |
