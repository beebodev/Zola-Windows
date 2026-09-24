# P3PRE Audit — Synthesis

Phases 2–7, plus the lighting correction on L9. Questions are facts for each option. Nothing here is a decision.

## 1. Finding summary

| ID | Severity | File/asset/package | Finding summary |
|---|---|---|---|
| P3PRE-AUD-01 | — | `android_hud_reference.png` | [MATCH] SHA-256 `8493a1ae…647c`. An earlier prompt copy expected `c47e…`. |
| P3PRE-AUD-02 | MEDIUM | `MainWindow.xaml` | [GAP] Composer and header are permanent, not a dock. |
| P3PRE-AUD-03 | — | `SubmitTurnAsync` | [MATCH] One submit path. |
| P3PRE-AUD-04 | HIGH | `ApplyVoiceChrome` | [RISK] Voice and mic labels are derived in the window. |
| P3PRE-AUD-05 | MEDIUM | `MainWindow.xaml.cs` | [RISK] Transcript and chrome are hard-wired to named elements. |
| P3PRE-AUD-06 | LOW | window 960×720 | [GAP] Theme-following window. No obsidian tokens or custom fonts. |
| P3PRE-AUD-07 | — | `zola.glb` | [MATCH] K3 inventory. |
| P3PRE-AUD-08 | — | morph names | [MATCH] Blink, jaw, visemes. |
| P3PRE-AUD-09 | LOW | morphs | [GAP] No blink-suppression target. |
| P3PRE-AUD-10 | MEDIUM | morphs | [GAP] No negative mouth curve. |
| P3PRE-AUD-11 | MEDIUM | morphs | [GAP] No `eyeSoftness` target. |
| P3PRE-AUD-12 | MEDIUM | morphs | [GAP] No projection geometry. |
| P3PRE-AUD-13 | HIGH | mesh | [GAP] No separate eyes for drift. |
| P3PRE-AUD-14 | HIGH | mesh | [GAP] No hair mesh for strand shimmer. |
| P3PRE-AUD-15 | HIGH | mesh | [GAP] No pixel-projection geometry. |
| P3PRE-AUD-16 | HIGH | emissive map | [RISK] One near-black emissive map. Chest glow is not a separate region. |
| P3PRE-AUD-17 | — | git | [MATCH] 34 MB, under GitHub's limit. No LFS. |
| P3PRE-AUD-18 | HIGH | Helix baseline | [RISK] First render much darker than the Android reference. Fidelity, not a missing mesh. L9 later closed the hue gap; contrast remains (section 2). |
| P3PRE-AUD-19 | MEDIUM | `Viewport3DX` | [RISK] XAML construction crashes. Code construction renders. |
| P3PRE-AUD-20 | MEDIUM | camera | [RISK] Bust renders near the origin, not at the glTF translation. |
| P3PRE-AUD-21 | HIGH | importer | [RISK] Phong material. Metallic-roughness was unbound until the spike built `PBRMaterialCore` by hand. |
| P3PRE-AUD-22 | — | accelerator | [MATCH] `Ctrl+Space` fired with the viewport focused. |
| P3PRE-AUD-23 | MEDIUM | environment map | [RISK] `SkipRendering` hides the cube. The imported Phong material showed no measurable light from it. |
| P3PRE-AUD-24 | MEDIUM | spike working set | [RISK] 168 MB before the GLB, 671 MB after. The model is most of that. |
| P3PRE-AUD-25 | MEDIUM | viewport background | [GAP] Alpha 0 on `BackgroundColor` did not show XAML behind the viewport. |
| P3PRE-AUD-26 | HIGH | Cycle 60 s on Iris Xe | [RISK] Continuous animation cost 1.8% CPU and 34.5% summed GPU. Static and minimized GPU were about 0%. |

## 2. Build plan implications

`P3PRE-AUD-02`: the presence layout has to take the composer off the permanent column and show it from the dock. `P3PRE-AUD-04`: one derivation has to own the voice label, the mic line, and `PresenceMode`, or the presence view will invent a second one. `P3PRE-AUD-05`: those named elements cannot stay the only writers once the chrome moves. `P3PRE-AUD-06`: the window size, theme, and type have to come from the token dictionary.

`P3PRE-AUD-09` through `P3PRE-AUD-15`: blink suppression, a negative mouth, eye softness, saccade, hair shimmer, and pixel projection are not on this asset. The plan either drops them, fakes them with weights and a node transform, or changes the GLB. `P3PRE-AUD-16`: chest-only breath cannot key a separate mesh region.

`P3PRE-AUD-18` and the L9 side-by-side: hue is close after PBR plus the L3 lights. The remaining gap is contrast. Android has deep shadows on the face, neck, and shoulder sides; L9 is evenly lit (too much ambient and fill against the key). Android has cream-white specular and rim light on the cheekbones, collarbones, and hair tips; L9 has almost none. Android blooms around the chest diamond, the beam, and the hair; L9 left `PostEffectBloom` off. An offline linear-to-sRGB encode washed L9 out and is not the cause. These are tuning inputs.

`P3PRE-AUD-19`: construct `Viewport3DX` in code. `P3PRE-AUD-20`: frame the bust where it renders, not at translation −1.75. `P3PRE-AUD-21`: the plan needs an explicit `PBRMaterialCore` with the four GLB textures. The importer will not do that. `P3PRE-AUD-23`: a hidden environment map does not light the Phong material.

`P3PRE-AUD-24`: budget the GLB. The empty WinUI plus Helix viewport was 168 MB; after the load the process was 671 MB. `P3PRE-AUD-25`: a radial glow or floor ring behind the bust was not visible through `BackgroundColor` alpha 0. Those have to be drawn in the scene, or by some clear path other than that property.

`P3PRE-AUD-26`: an always-on idle animation at this weight rate costs 1.8% CPU and 34.5% summed GPU on the Iris Xe, while a minimized window drops to about 0% GPU. Q-O lists the levers. The plan has to pick a budget before presence animation runs continuously.

Unlock after `LockWorkStation`, and any device loss after that unlock, were not observed. The spike exited −1 because the harness `OpenInputDesktop` call blocked while the session was locked, not because Helix failed. The build plan's smoke test still has to cover lock and unlock.

HUD rows marked **none** or [RISK] in Audit 05 cannot be drawn as if they were true. OPTIMAL, ENCRYPTED, CALM, and ATTENTION have no supporting source.

## 3. Pre-work

Before a presence track starts: choose Set A as the package set or revisit it (Q-A is Full capability on the tests that were run); extract the voice-label derivation out of `ApplyVoiceChrome` (Q-B); decide GLB storage (Q-D); decide which HUD and dock rows are hidden (Q-E, Q-F); if fonts are committed, ship the OFL text with them (Q-M). `ms-appx:///Fonts/<file>.ttf#<family>` rendered in the unpackaged spike. No asset commit was made by this audit. The GLB stays in `zola-assets`.

## 4. Assumptions confirmed

`P3PRE-AUD-03`, `P3PRE-AUD-07`, `P3PRE-AUD-08`, `P3PRE-AUD-17`, `P3PRE-AUD-22`. K3 morph order. K7 contrast numbers. `Ctrl+Space`. Shared submit path. File size under the GitHub limit.

## 5. Open questions

**Q-A.** Set A (Helix Toolkit WinUI SharpDX 3.1.2 and Assimp 3.1.2) rendered and drove morphs. Set B was not installed. R1 textures present (metallic-roughness unbound on the imported Phong material, bound when the spike built PBR). R2 count and order match; names are not on the node. R3 weights set. R4 combined morphs pass. R5 passes: `MorphTargetVertex` carries `deltaNormal`, and a side-key shot of Jaw open 1 versus 0 shows the lip and chin shading follow the new shape (`shots/R5-jaw0.png`, `shots/R5-jaw1.png`). R6 reset passes. R7 hotkey passes. R8 frame time was recorded (Cycle about 16.8 ms; L9 16.66 ms average, 17.48 ms p95). R1–R7 are met, so this is **Full capability**. Technical verdict: the stack renders and animates, including morph normals. Fidelity verdict, separate: hue is close; contrast, rim light, and bloom are not. WebView2, three.js, and Unity were not measured.

**Q-B.** The derivation can move into `VoiceController`, into a type the controller owns, or stay one method the window and the presence both call. Audit 04 lists the window fields that method still needs. Two independent mappings would be a second derivation (`P3PRE-AUD-04`).

**Q-C.** Eye drift, hair shimmer, and projection geometry are absent (`P3PRE-AUD-13`, `14`, `15`). Options are drop, approximate (a node yaw is the only lean the spike tried; weights cannot move eyes inside the head), or change the asset.

**Q-D.** The file is 33,972,240 bytes. GitHub's hard limit is 100 MB. The repo has no `.gitattributes` and no LFS (`P3PRE-AUD-17`). Plain git can hold it. LFS was not set up.

**Q-E.** Elements with source **none** are listed in Audit 05. §14 says hide an element that does not communicate state. Deferring one with a placeholder would show a claim the client cannot support. That choice is open.

**Q-F.** Memory, Environment, Awareness, Behavior, Security, Systems, Settings, and Account have no client action. Conversation routes to `prompt.submit`. Voice routes to the mode toggle. Concept-dock glyphs are UNVERIFIED.

**Q-G.** Every Phase 2 control has a home in Audit 05 §3. None are stranded.

**Q-H.** K5 still holds: no speech amplitude, transcript on demand, composer from the dock. Nothing in the findings says those three should change. The portrait reference on a landscape window is Q-I, not a change to K5.

**Q-I.** The client window is 960×720 with no minimum (`P3PRE-AUD-06`). The reference image is 420×901, portrait. The spike resize matrix, outer window equal to the request, on a 1920×1080 display: 1280×720, 1600×900, 1920×1080, and 900×700. The bust stayed centred and the face stayed fully visible at all four. The top-left HUD overlay did not cover the face. The bottom debug strip did not cover the bust. At 1920×1080 the window is taller than the work area, so a sliver of the desktop shows under it. No size in this set cropped the face, so a collapse threshold was not measured. The client still has no minimum.

**Q-J.** Android shows coordinates and "SNOHOMISH - WASHINGTON". The client has no location source. The privacy plan treats current location as transient context and does not retain precise history by default. Showing the block needs a permission and, for a place name, a lookup that can leave the machine. Hiding it needs no new API.

**Q-K.** The emissive image is one map, peak about 31/255, and the chest is not a separate material (`P3PRE-AUD-16`). A chest-only breath is not available as a mesh region. Glow strength on L9 is `PBRMaterialCore.EmissiveColor` for the whole material, or `PostEffectBloom` for the bright pixels. Those are different mechanisms. Which one is acceptable is open.

**Q-M.** K7 tokens and contrast in Audit 07 match the prompt. The spike drew both wordmarks at 2×: Rajdhani SemiBold and Orbitron Medium. The developer has not chosen. OFL 1.1 name ID 13 is on all four files; committing them requires the licence text beside them. The `Presence*` colours were for the SVG. They do not recolour the GLB.

**Q-N.** K7 sizes are phone `sp`. On the capture display, DPI was 96 (100%). At 1× the font panel is a few pixels tall. At 2× the wordmarks are readable. Scale S is not chosen. Muted amber is 3.98:1, below WCAG AA 4.5:1 for small text. Whether that stays acceptable at the chosen S is open.

**Q-L.** The wordmark, tagline, five-line statement, and "OBSIDIAN INTERFACE" carry no runtime state. §14 says hide elements that do not communicate state. Keeping them is an identity exception. Dropping them removes the branding the Android image shows. Not chosen.

**Q-O.** Always-on idle animation, facts only. With Cycle running for 60 s on the Iris Xe (driver 32.0.101.7088), process CPU was 1.8% and summed GPU Engine utilization for this process averaged 34.5%. The earlier Cycle frame time was 16.76 ms average and 16.85 ms at the 95th percentile (n=3586). Minimized for 30 s, CPU was 0.4% and GPU samples were about 0%. A static viewport in the first lab was about 0.1% GPU. Levers, not chosen: frame rate of the weight updates; render-on-demand (Helix does not keep drawing a static scene); pausing while the window is hidden, minimized, or locked (minimized was measured; locked was not); reduced motion (`UISettings.AnimationsEnabled` was true and was not wired to Cycle); texture size (the GLB maps are 2048² and were not scaled).
