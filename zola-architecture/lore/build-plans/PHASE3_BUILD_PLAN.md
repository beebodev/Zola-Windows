# ZW Phase 3 Build Plan
## Presence UI — Zola's 3D Presence, Obsidian HUD, Dock, and Conversation on Demand

**Base branch:** `main`
**Base SHA:** `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`. This is the P3PRE audit merge. This plan's own
commit will move `main` ahead of it, and each track records the actual HEAD it branches from.
**Audit:** P3PRE, merged at `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`. The documents are in
`zola-architecture/audit/p3pre-presence-ui/` (26 findings: 8 HIGH, 10 MEDIUM, 2 LOW).
**Theme:** New-feature work. This phase replaces the Phase 1 chat layout with Zola's presence:
- the canonical GLB, rendered natively in 3D with Helix Toolkit, at the centre of a full
  obsidian window;
- a restrained HUD that shows only true state;
- a dock;
- the conversation, which opens on demand.

Her face and glow respond to the real Phase 2 voice states through **one** display-state
authority. Every Phase 1 and Phase 2 behaviour survives the move.

This phase does **not**:
- change the voice pipeline;
- add HUD data sources that do not exist yet (attention, momentum, emotion, system health,
  location);
- re-author the GLB;
- attempt audio-driven lip-sync (`S17`).

---

## Phase 3 Overview

| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 (`P3-STATE`) | Display-state authority + carry-over | Extract the voice/mic label derivation from `MainWindow.ApplyVoiceChrome` into one `ZolaDisplayState` model that also yields `PresenceMode`; remove the three dead echo constants. No visual change. | Small-Medium |
| 2 (`P3-SHELL`) | Obsidian shell | Visual tokens + Rajdhani fonts; fixed dark theme; full-presence layout (presence host placeholder, HUD overlay, dock, conversation overlay, sessions panel); every existing control re-homed | Medium-Large |
| 3 (`P3-RENDER`) | 3D presence | Helix packages + GLB asset; `PresenceView` renders the bust (PBR material, camera, environment lighting); morph index map; render-on-demand; pause/resume; fail-closed fallback | Medium-Large |
| 4 (`P3-LOOK`) | Fidelity | Lighting contrast, rim/specular, bloom, emissive; in-scene background glow and floor rings; XAML particles and corner brackets; texture-size test. Judged against the Android reference | Medium |
| 5 (`P3-LIFE`) | Procedural life | `PresenceMode` → expression, blink, breathing, speaking mouth, lean, staggered transitions, dormant look, reduced motion; the ≤10% idle GPU budget | Medium-Large |

**Sequencing rule:** strictly **1 → 2 → 3 → 4 → 5**. Each track merges before the next one
begins. Tracks 2–5 all modify `MainWindow.xaml(.cs)` and/or the presence files. Track 4 comes
before Track 5 because the doc requires static visual parity before animation (§2: "If the
still frame does not feel like Zola, motion will not fix it"). Do not run tracks in parallel.

**Build command (all tracks):** `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`.
Use `-r win-x64`, not `-p:Platform=x64`. The spike showed that the platform form fails the
WinUI markup compiler (`WMC1509`/`WMC9999`) once Helix is referenced (Audit 03 §1).
**Test command (all tracks):** none. This project has no automated test suite. The smoke tests
are the acceptance criteria.

---

## Grounding summary (established by P3PRE; cite, do not re-derive)

- **Engine (`P3PRE` Q-A: Full).** Set A was tested on this exact stack
  (`Microsoft.WindowsAppSDK 2.5.1`, `net9.0-windows10.0.19041.0`, unpackaged):
  `HelixToolkit.WinUI.SharpDX 3.1.2` and `HelixToolkit.SharpDX.Assimp 3.1.2`. There were no
  restore warnings and no App SDK downgrade. The rendering acceptance rows R1–R7 all pass. R8:
  continuous animation runs at 16.76 ms average and 16.85 ms p95.
- **Constructing the viewport.** Declaring `Viewport3DX` in XAML crashes WinUI
  (`0xc000027b`). Constructing it in code works (`P3PRE-AUD-19`).
- **Import.** `HelixToolkit.SharpDX.Assimp.Importer.Load(string)`. Cold load is 673–1092 ms and
  warm load 343 ms. The scene is a `GroupNode` → `BoneSkinMeshNode` holding 15 weights.
- **Morphs.**
  - Weights are set with `BoneSkinMeshNode.SetWeight(int, float)` and pushed with
    `WeightUpdated()`.
  - Names are **not** imported. The index order is the K3 order below.
  - Normal deltas are applied (`MorphTargetVertex.deltaNormal`, R5).
- **Material.** The importer creates `PhongMaterialCore`, which ignores the environment map and
  the metallic-roughness texture (`P3PRE-AUD-21`).
  - A hand-built `PBRMaterialCore` gets `AlbedoMap`, `NormalMap` and `EmissiveMap` from the
    imported Phong maps.
  - Its `RoughnessMetallicMap` is GLB `Image_1`: G is roughness (mean 92), B is metallic
    (mean 0), R is unused.
  - `RenderAmbientOcclusionMap = false`.
- **Environment lighting.** `EnvironmentMap3D.Texture` takes a procedural cube in memory.
  `SkipRendering = true` keeps it for lighting without drawing it as the background.
- **Background.** `Viewport3DX.BackgroundColor = #FF080808`. A transparent viewport does
  **not** show XAML behind it (`P3PRE-AUD-25`). Anything behind the bust must live inside the
  3D scene. XAML placed *above* the viewport renders correctly.
- **Camera.** The rendered bust sits near the origin, not at the glTF translation −1.75
  (`P3PRE-AUD-20`). The spike frame was camera `(0, 0.05, 3.15)`, look `(0, 0, −3.372)`,
  FOV 35°. It kept the bust centred and the face in view at 1280×720, 1600×900, 1920×1080
  and 900×700.
- **Lighting baseline (L9).** Ambient `#FF5A4628`; key `#FFFFDCAA` at direction
  `(−0.3, −0.8, −1)`; fill `(180,120,60)` at `(0.6, −0.2, −0.5)`.
  - Hue is close to the Android reference.
  - The remaining gap is contrast: too much ambient and fill against the key, almost no
    cream-white rim or specular highlight, and bloom off.
  - `PostEffectBloom` exists but is unused. Its properties are `ThresholdColor`,
    `NumberOfBlurPass`, `BloomExtractIntensity`, `BloomPassIntensity`,
    `BloomCombineIntensity` and `BloomCombineSaturation`.
  - No sRGB/gamma property exists. An offline sRGB encode was tried and rejected.
- **Emissive.** One near-black, scattered emissive map (peak 31/255). No region can be isolated
  (`P3PRE-AUD-16`). Most of the visible gold comes from base colour plus lighting.
- **Cost.**
  - Static: CPU about 2%, GPU about 0.1% (Helix renders lazily).
  - Continuous 60 fps animation: CPU 1.8%, GPU **34.5%** on the Iris Xe (`P3PRE-AUD-26`).
  - Minimized: CPU 0.4%, GPU about 0%, and the view restores cleanly.
  - Working set: 168 MB → 671 MB once the model loads (`P3PRE-AUD-24`).
  - Lock/unlock recovery is **unverified**.
- **Hotkey.** `Ctrl+Space` on the root `Grid` fires while the viewport has focus
  (`P3PRE-AUD-22`).
- **Fonts.** `ms-appx:///Fonts/<file>.ttf#<Family>` renders in the unpackaged app. **Correction to
  Audit 03 §10 / Audit 07:** every line in `shots/fonts.png`, both "ZOLA" wordmarks included,
  is **Segoe UI fallback**. The absolute-path form failed silently. Only the "ZOLA ms-appx"
  line in `shots/font-msappx.png` is real Rajdhani. Every font-bearing track must therefore
  confirm the typeface **by eye**, never from the assignment succeeding.
- **Reduced motion.** `UISettings.AnimationsEnabled` plus `AnimationsEnabledChanged`.
- **Display-state sources.** `ApplyVoiceChrome` (`MainWindow.xaml.cs` 316–394) is the only
  label derivation. Its window-owned inputs are:
  - `_streaming`
  - `_unreachable`
  - `_switchInFlight`
  - `_historyPending`
  - `_modeSwitching`
  - `_sessionReady`
  - `_backend.WebSocketPermitted`

  The label and mic-line priority tables are in Audit 01 §3. The state-transition matrix is in
  Audit 04 §1b.

**K3 morph index order (named constants, no inline numbers):**
0 Blink left · 1 Blink right · 2 Blink both · 3 Squint Eyes · 4 Wide / alert Eyes ·
5 Brow raise · 6 Brow furrow / concern · 7 Nostril flare · 8 Jaw open · 9 Open AH ·
10 Mid-open EH/UH · 11 Closed M/B/P · 12 Round OO/W · 13 Wide EE/ smile-adjacent ·
14 Teeth showing F/V.

**K7 visual tokens.** Values only, extracted from the Android source with the developer's
approval. The full table, with citations, is in the P3PRE prompt K7 and Audit 07.
- **Colours:**
  - background `#080808`
  - amber primary `#FFD37A`
  - amber muted `#8A6A2A`
  - amber dark `#5A4820` (decorative only)
  - alert glow `#FFE7A5`
  - presence amber `#FFD05A` (particles)
- **Type:** every text style is Rajdhani. The rows are wordmark, tagline, mantra, section
  header, row label, right-panel header, right-panel value, time and footer, with sizes,
  `CharacterSpacing` and line heights as in Audit 07's type table.

**Canonical assets (outside the repo until Track 2/3 commit them, with SHA-256):**
- `C:\Users\test\Dev\zola-assets\zola.glb`:
  `1edf2bf5898528fd405cd3131fcf75548c6d5d1e893501467c65845b5d7a054b`.
  A June 2026 variant with empty mouth morphs exists. It is **not** canonical.
- `fonts\rajdhani_regular.ttf`: `f0ba67d6…4d2e`.
- `fonts\rajdhani_semibold.ttf`: `5fd51c13…eb0cd`.
- `android_hud_reference.png`: `8493a1ae…647c`. This is the fidelity target.
- `zola_concept_reference.png`: `71392aa9…3e6e`. This is the layout and HUD concept.

---

## Decisions Resolved in This Build Plan

All decided by Brian on 2026-09-24 after the P3PRE review.

**P3-D01 — The GLB replaces the SVG as Zola's canonical visual on Windows.**
`zola.glb` (SHA above) is the presence. `zola_presence_ui_reference.svg` does not exist in
this repo and is not a target.

These parts of `Zola_Presence_UI_Architecture.md` are superseded for Windows:
- the rules that take coordinates from the SVG;
- the "no realistic 3D model / no full character rig" non-goals;
- the Compose/Canvas mechanics.

Everything else still binds:
- presence-first and voice-first design;
- the state-down pipeline;
- one adapter boundary;
- scoped render state;
- procedural local animation;
- restraint;
- reduced motion;
- performance discipline.

The lore closeout adds a Windows Track note to that doc. Resolves P3PRE K1.

**P3-D02 — Engine: Helix Toolkit 3.1.2 (Set A), native in-process.**
- **Packages:** `HelixToolkit.WinUI.SharpDX 3.1.2` and `HelixToolkit.SharpDX.Assimp 3.1.2`.
  Plan approval is the developer's approval of exactly these two `dotnet add package`
  commands, run in Track 3 only. Any other package, version or transitive change beyond what
  restore pulls for these two is a BLOCKED stop.
- **Rules:**
  - `Viewport3DX` is constructed in code, never in XAML (`P3PRE-AUD-19`).
  - The imported Phong material is replaced by a `PBRMaterialCore` built from the GLB's own
    four textures (`P3PRE-AUD-21`).
  - The metallic-roughness image is located by parsing the GLB JSON chunk
    (`materials[0].pbrMetallicRoughness.metallicRoughnessTexture` → texture → image →
    bufferView), never from a hard-coded byte offset.
- **Ruled out:** WebView2 + three.js, and Unity. Neither was needed, because Q-A was Full.

**P3-D03 — One display-state authority: `ZolaDisplayState`.**
A new `ZolaDisplayStateModel` class is the **only** place that turns runtime facts into:
- the voice-state label;
- the mic-indicator line;
- the Voice/Text mode word;
- mic-button enablement and content;
- `PresenceMode`.

Where its inputs come from:
- It reads `VoiceController`'s public properties.
- The window pushes its own facts into it through **one** method,
  `UpdateWindowFacts(...)`, the same pattern as today's `SetCaptureGate`.

What it produces:
- One immutable `ZolaDisplayState` record, plus a `Changed` event.
- `MainWindow`, the HUD and `PresenceView` only read that record. `ApplyVoiceChrome` becomes
  pure rendering.

What it must not do:
- It does not own RPCs.
- `VoiceController` keeps sole ownership of listeners, `voice.*` / `wake.*` and
  transcript-to-submit (`P2-D12`).
- `VoiceController.Resting` stays in the controller. It is a wake-acceptance rule, not a label.

The label and mic-line priority orders are exactly Audit 01 §3. Track 1 changes no string and
no ordering. Resolves `P3PRE-AUD-04` and P3PRE Q-B (Option 1: "a type the controller layer
owns").

**P3-D04 — `PresenceMode` values and mapping (Windows Track addition: `DORMANT`).**
The modes are `IDLE`, `LISTENING`, `THINKING`, `SPEAKING` and `ALERT` (the doc's five), plus
**`DORMANT`**, a Windows addition.

`ZolaDisplayStateModel` maps them in this priority order (first match wins):

| # | Condition | PresenceMode |
|---|---|---|
| 1 | backend unreachable (`_unreachable` or `!WebSocketPermitted`) | `DORMANT` |
| 2 | `_switchInFlight` or `_historyPending` (reconnect or session switch) | `IDLE` (the HUD mic line already says "Reconnecting voice…") |
| 3 | `VoiceController.Speaking` | `SPEAKING` (an estimate, `P2-D08`/`P2-D15`) |
| 4 | `_streaming` | `THINKING` |
| 5 | `RecorderState == transcribing` | `LISTENING` |
| 6 | `CaptureActive` or `RecorderState == listening` | `LISTENING` |
| 7 | Text mode, or voice unavailable | `IDLE`. She is present but not listening; the mic line says off |
| 8 | else | `IDLE` |

*v1.1 ordering rules (peer review, confirmed against Audit 01 §3 and Audit 04 §1b):*
- **Text mode is checked last**, so a typed turn still shows `THINKING`. Text mode only
  describes *how Brian talks to her*, not what she is doing. In Text mode, `Speaking` is always
  false (spoken replies are off), so it can never produce `SPEAKING`.
- **`Speaking` outranks `_streaming`.** The two overlap for most of every spoken turn:
  - `Speaking` is set on `message.start` (`OnTurnStarted`, when the playback clock is eligible);
  - `_streaming` stays true until `FinishTurn`.

  With `_streaming` first, she would look like she is thinking while audibly talking. So the
  presence reads `THINKING` from submit until `message.start`, then `SPEAKING` until the
  playback-clock estimate ends. Track 5 delays the mouth by the P2 first-sentence latency.
- **The voice-state label keeps its P2 priority unchanged** (`_streaming` before `Speaking`,
  Audit 01 §3). During a streaming spoken reply, the HUD voice line can therefore read
  "THINKING" while the presence shows `SPEAKING`. This is a known, documented difference
  between two outputs of the **same** model, not a second authority. Aligning the label is a
  P2 behaviour change and is out of scope.

`ALERT` has no Windows source (Audit 04). It is defined and mapped in Track 5 but never
produced this phase.

Why `DORMANT` exists: fail closed. She must never look available when the backend is
unreachable. It is the only mode added. `DORMANT` is visually distinct from `IDLE`:
- lowered lids, and a steady, reduced glow;
- **no** blinking, breathing, head motion or particle drift.

That also costs about 0% GPU while disconnected. Resolves P3PRE Q-H/Audit 04's `NO MODE` and
`AMBIGUOUS` rows.

**Stale-state recovery (display only; the pipeline is not changed).** The model guarantees
these, using the existing runtime facts:
- A confirmed backend disconnect always yields `DORMANT`, because priority 1 overrides
  everything.
- Cancel clears `THINKING` when the existing interrupt acknowledgement runs `FinishTurn`.
- A session switch or resume cannot carry the previous session's `THINKING` or `SPEAKING`:
  `ClearTranscript` clears `_streaming`, and `CancelFollowUp` clears `Speaking`. Track 1 verifies
  both paths.

There is **no blind timeout**. If `_streaming` stays true with no socket event for
`StaleThinkingWarnSeconds` (120), the model logs `P3-STATE: thinking with no events for Ns
(S26)` once. The presence keeps showing `THINKING`, because hiding real work would be dishonest.
The root cause stays `S26`.

**P3-D05 — Model gaps: approximate what the asset supports, defer the rest.**
Built from the morph targets and the node transform:
- **Blink:** index 2, with occasional 0/1 asymmetry.
- **Expression:** indices 3, 4, 5, 6 and 13.
- **Speaking mouth:** 8 plus visemes 9–13.
- **Lean and head micro-turn:** whole-node rotation. This stands in for eye drift.
- **Breathing:** a glow-level pulse through bloom intensity and `EmissiveColor`. It is not
  chest-only, which cannot be isolated (`P3PRE-AUD-16`).

Not built this phase:
- micro-saccade, which needs separate eye geometry;
- per-strand hair shimmer, which needs a hair mesh;
- pixel-projection and hologram layers, which need geometry;
- a negative mouth curve and eye softness, which have no targets.

These are filed as `S24` (asset rework). Resolves P3PRE Q-C and Q-K.

**P3-D06 — The HUD shows only true state; everything else is hidden.**
Shown:

| Element | Source | Honest wording |
|---|---|---|
| Voice block | `ZolaDisplayState.VoiceLabel` and `ZolaDisplayState.MicLine` | One header, "VOICE"; two value lines: "• " + voice label, then the mic line. **Never titled "ATTENTION".** *(v1.2: one block instead of separate VOICE and MIC headers, because the mic line already starts with "Mic:".)* Values are rendered upper-case at display time, as on Android. That is presentation only; the model's strings are unchanged. |
| Time | local clock, refreshed on the minute | Header "TIME"; value `HH:mm` |
| Session | `ChatSocket` runtime session id (short form) | Header "SESSION" |
| Link | `ZolaDisplayState.LinkLabel` *(v1.2, added to the model so the window does not derive connection state)* | First match: unreachable or backend not reachable → "OFFLINE"; switch in flight or history pending → "LOCAL LINK • RECONNECTING"; session ready → "LOCAL LINK • CONNECTED"; else "LOCAL LINK • CONNECTING". It must **not** say "encrypted": the link is loopback `ws://` |
| Notices | the existing `StatusText` / `DetailText` content | A notice line above the dock that collapses when empty |

Hidden this phase, because no source supports them:
- attention level and its bar;
- system status OPTIMAL;
- conversational momentum;
- emotional tone;
- environment;
- obsidian-mode status;
- version;
- encrypted connection;
- the location block;
- the Core Systems list, whose rows have no actions.

These are filed as `S25`. Resolves P3PRE Q-E and `P3PRE-AUD` rows marked [RISK] in Audit 05.

**P3-D07 — Identity text is kept, as an explicit exception to §14.**
These items carry no runtime state. They are kept as Zola's identity, not as status claims:
- the "ZOLA" wordmark;
- the tagline "PERSISTENT CONVERSATIONAL INTELLIGENCE", on **three** lines
  ("PERSISTENT" / "CONVERSATIONAL" / "INTELLIGENCE"), as on Android *(v1.3)*;
- the five mantra lines "I AM HERE. / I AM LISTENING. / I UNDERSTAND. / I REMEMBER. /
  I PROTECT.";
- the "OBSIDIAN INTERFACE" label.

The copy is exactly the Android copy. *(v1.3, developer decision after the Track 2 review.)* The
layout follows Android: the mantra is indented from the identity column's left edge by the token
`ZolaMantraIndent`, and the space to its left, where Android draws a decorative waveform, is
**reserved and left empty**. A decorative waveform would look like a live audio reading, so it is
not drawn. Track 5 evaluates filling that space with a **real** mic-input meter. It may do so only
if `VoiceController` already exposes an input level without any voice-pipeline change. Otherwise
the space stays empty and the meter is filed as `S27`. Resolves P3PRE Q-L.

**P3-D08 — Visual tokens, fonts and scale.**
- **Tokens:** the K7 colour values, verbatim, as `Color` + `SolidColorBrush` resources in one
  `Themes/ZolaTokens.xaml` `ResourceDictionary`, merged in `App.xaml`. Every text style is a
  `Style` there. No inline colours or font sizes anywhere else.
- **Font:** the wordmark is **Rajdhani SemiBold**, which is what shipped on Android. Orbitron
  is not committed.
- **Scale:** type scale **S = 2** (every K7 `sp` size × 2, in effective pixels).
  `CharacterSpacing` uses the K7 conversions, which do not depend on scale. Geometry (dock
  48 × 48 buttons, 24-px icons, 0.5-px dividers) uses the K7 `dp` values 1:1 as effective
  pixels.
- **Muted amber (3.98:1)** is used only for section and right-panel headers, at ≥14 px. It is
  never used for values.
- **Conversation tokens (v1.2):** long-form reading text uses `ObsidianTextPrimary #E8DDD0`
  (contrast 14.96) and bubbles use `ObsidianSurface #141414`. Both are Android `Color.kt:16–18`
  values listed in K7. User bubbles get an amber-muted border, assistant bubbles an amber-dark
  border, and "Interrupted" is badged in amber muted. **The one colour not taken from Android** is
  `ZolaErrorColor #D9534F`, used only for the error badge and the error bubble border, because
  errors must read as errors. Bubble maximum width is a token (`ZolaBubbleMaxWidth = 380`),
  replacing the hard-coded 720.
- **Theme:** the window forces a dark theme (`RequestedTheme = Dark`). Chat bubbles stop
  reading system theme brushes (`BubbleBrush`, Audit 07).
- **Font files:** `rajdhani_regular.ttf` and `rajdhani_semibold.ttf` are committed under
  `windows-client/Zola.Client/Fonts/` with `OFL.txt`, which OFL 1.1 requires. The licence text
  is fetched with the single pre-approved command in Track 2.

Resolves P3PRE Q-M and Q-N.

**P3-D09 — Idle performance budget: ≤ 10% GPU on the Latitude 7430.**
- **What is measured:** in the `IDLE` mode with idle life running (blink, breathing, micro-turn,
  bloom on), over 60 s, summed GPU-engine utilization for the client process must average
  **≤ 10%**. Measured the Audit 03 way, at the default window size.
- **Principle (v1.1): render only as often as the current motion needs.** One scheduler, with
  an adaptive cadence:

  | Activity | Cadence |
  |---|---|
  | Nothing changing | no render |
  | Slow glow breathing only | low rate (start at 10 fps, tune down if it still reads smooth) |
  | Blink in progress (~250 ms) | up to 60 fps for its duration |
  | Head micro-turn in progress | up to 30 fps for its duration |
  | Mode transition | up to 60 fps for its duration |
  | `SPEAKING` | up to 60 fps |
  | `DORMANT`, minimized, occluded, locked | no render |

  30 fps is a ceiling for idle motion, not a target.
- **Available levers:**
  - the cadence table above;
  - bloom pass count;
  - texture size (Track 4);
  - pausing entirely when minimized, occluded or locked.
- **If the levers fail:** if ≤ 10% cannot be met after trying them, Track 5 stops BLOCKED with
  the measurements. It does not ship over budget. The budget does not apply while `SPEAKING`
  or during transitions; those readings are recorded, not scored.

Resolves P3PRE Q-O and `P3PRE-AUD-26`.

**P3-D10 — Location is not shown.** There is no Windows source. The privacy plan says current
location is transient and precise history is not retained, and a place name would need an
online lookup. It is hidden with no API added. Resolves P3PRE Q-J.

**P3-D11 — Layout: full presence, conversation on demand.**
The layout has these layers, back to front:
1. **Presence** (Track 3 `PresenceView`): fills the window; the bust is centred.
2. **Decoration** (Track 4): XAML corner brackets and the particle layer.
3. **HUD**:
   - left top: identity block;
   - left bottom: "OBSIDIAN INTERFACE", then the link and session lines;
   - right top: the VOICE block (header, voice label, mic line; `P3-D06` v1.2), divider, TIME
     *(v1.3 wording fix)*.
4. **Notice line**, directly above the dock.
5. **Dock**, bottom centre; *(v1.4)* hidden until needed, per `P3-D17`:
   - **Voice/Text** (`ModeButton`)
   - **Mic** (`MicButton`)
   - separator
   - **Conversation**: opens the overlay
   - **Sessions**: opens the sessions panel
   - **Cancel**: visible only while a turn runs
6. **Conversation overlay**:
   - a right-side panel over the presence, about 440 px wide, `#080808` at 0.88 opacity, with
     an amber-dark border;
   - it holds `TranscriptScroll`/`Transcript`, the `Composer`, `SendButton` and a close
     button;
   - Esc closes it;
   - the transcript keeps filling while it is hidden;
   - *(v1.3, Track 2 smoke finding)* after a **typed** send, focus returns to `Composer` when
     the turn ends, but only if the overlay is still open. Closing the overlay, opening
     sessions, or switching mode cancels the return. Voice turns never move focus.
7. **Sessions panel**: a left-side panel in the same style, containing today's `SessionPanel`
   content.

Dock icons are `FontIcon` glyphs from Segoe Fluent Icons, in amber primary. No new icon asset.
*(v1.2)* Each dock button's content is a glyph above a named label `TextBlock`, for example
`ModeButtonLabel` and `MicButtonLabel`. `ApplyVoiceChrome` sets the label `Text` from
`ZolaDisplayState` instead of replacing `Button.Content`, so the icon survives. The button
`x:Name`s are unchanged.

Window: initial size 1280×800, **minimum 900×640**. No title-bar customization this phase.

Every control named in Audit 01 §1 keeps its `x:Name`, so the code-behind references
(Audit 01 §5) stay valid. Resolves `P3PRE-AUD-02`, `-05`, `-06` and P3PRE Q-G/Q-I.

**P3-D12 — Asset storage.**
- `zola.glb` goes in plain git at `windows-client/Zola.Client/Assets/Presence/zola.glb`,
  copied to output as `Content`. The SHA-256 is verified at commit.
- A `.gitattributes` marks `*.glb` and `*.ttf` `binary`.
- No Git LFS. The file is 34 MB, under GitHub's limits, and rarely changes.

Resolves P3PRE Q-D and `P3PRE-AUD-17`.

**P3-D13 — Fidelity is judged by the developer against `android_hud_reference.png`.**
- Track 4 tunes lighting, rim/specular, bloom and emissive, starting from L9.
- The background glow and floor rings are in-scene geometry, because transparency does not
  work.
- Particles and corner brackets are XAML above the viewport.
- Acceptance is the developer's side-by-side judgement ("reads as Zola"), backed by logged
  sample colours. It is not a numeric threshold.

The texture-size test compares 2048² against 1024², side by side:
- if the developer cannot tell them apart in normal viewing, 1024² ships; this is expected to
  cut the model's memory substantially;
- otherwise 2048² stays.

Both outcomes are pre-authorized.

**P3-D14 — Speaking mouth is procedural and honestly an estimate.**
*(v1.1)* The mouth starts `FirstSentenceLatencySeconds` after `SPEAKING` begins, reading
`VoiceController`'s existing constant (exposed read-only, not duplicated), so the lips do not
move before her voice. When speech ends, the mouth eases back to the base expression rather
than snapping to zero.
There is no audio amplitude on Windows (`P2-D01`). While `PresenceMode == SPEAKING`:
- a viseme cycler drives `Jaw open` at 0.10–0.35 plus one of indices 9–13;
- the target is re-picked every 90–140 ms with spring smoothing;
- it stops when `Speaking` clears.

A code comment says this follows the `P2-D15` estimate, not the sound. Real amplitude would come
from `S17` (speaker metering), which stays deferred.

**P3-D15 — Carry-over: remove dead echo constants.**
- Delete `EchoContainmentRatio`, `EchoMinWords` and `EchoPhraseWords` (`VoiceController.cs`
  49, 51, 52).
- Fix the stale comments above them (48, 55), which cite `P2-D12` for the live rule. The live
  rule is `P2-D14`.
- In `VOICE_CONFIG.md`, change those three tuning-log rows from "No longer used" to
  "Removed (P3-STATE)".

Behaviour is unchanged.

**P3-D17 — The dock is hidden until needed (v1.4, developer decision 2026-09-25).**
The dock fades in when any of these is true, and fades out `DockHideDelaySeconds` (2) after none
is:
- the pointer is inside the bottom reveal zone (`DockRevealZoneHeight`, a token);
- keyboard focus is inside the dock (Tab still reaches it while hidden);
- the conversation overlay or the sessions panel is open;
- a turn is running (`_streaming`), so Cancel is always one click away.

Rules:
- Hidden means opacity 0, not `Collapsed`, so Tab and automation still reach the buttons.
- The fade runs over `DockFadeMilliseconds`; with reduced motion it is instant.
- Exactly one method decides dock visibility.
- No button, handler or `x:Name` changes.

**P3-D18 — The notice line fades; problems stay (v1.4, developer decision 2026-09-25).**
The notice line (`StatusText` / `DetailText`) is presentation-only here. No message text and none
of the existing writers change.
- A new or changed message shows, then fades after `NoticeHoldSeconds` (4).
- The line stays up while something is actually wrong or in progress, the "sticky" condition:
  - unreachable;
  - switch in flight;
  - history pending;
  - or the last turn ended in an error, until the next turn starts.
- `DetailText` (the session/stored detail) is shown **only** while the sticky condition is true.
  The session id is already in the HUD.
- When the conversation overlay is open, the notice line is centred in the space the overlay does
  not cover. This fixes the 900-px overlap.
- Exactly one method decides notice visibility. It is triggered by a text-changed callback on the
  two `TextBlock`s plus `UpdateChrome`, so none of the 25+ existing writers is touched.

**P3-D16 — No `hermes-agent` edits; no Python installs.** Carries forward `P2-D10`/`P2-D17`.
Phase 3 is client-only. `git status` in `C:\Users\test\Dev\hermes-agent` must be clean at every
closeout.

---

## Track 1 — Display-State Authority + Carry-over (`P3-STATE`)

### Problem
The voice-state label and the mic line are derived inside `MainWindow.ApplyVoiceChrome`
(`MainWindow.xaml.cs` 316–394) from a mix of `VoiceController` properties and window fields.
A presence view that mapped `PresenceMode` from the same facts would be a second authority
(`P3PRE-AUD-04`; doc §4, §18; `P2-D12`). Three dead constants remain in `VoiceController.cs`
(Audit 06).

### Files to read
- `windows-client/Zola.Client/MainWindow.xaml.cs`, in full. Focus:
  - `ApplyVoiceChrome` 316–394;
  - `UpdateChrome` ~674–686;
  - every writer of `_streaming`, `_unreachable`, `_switchInFlight`, `_historyPending`,
    `_modeSwitching` and `_sessionReady` (Audit 01 §3).
- `windows-client/Zola.Client/VoiceController.cs`, in full. Focus:
  - public properties 146–212;
  - `SetCaptureGate` 214–225;
  - `CanStartCapture` 197–203;
  - `Resting` 180–194;
  - constants 40–60.
- `zola-architecture/audit/p3pre-presence-ui/Zola_P3PRE_Audit_01_ClientSurfaceMap.md` §3, and
  `…Audit_04_ArchitectureMap.md` §1 and §1b.
- `zola-architecture/identity/VOICE_CONFIG.md` (tuning log).

### Changes

**`windows-client/Zola.Client/ZolaDisplayState.cs` (new):**
- `enum PresenceMode { Idle, Listening, Thinking, Speaking, Alert, Dormant }`.
- `sealed record ZolaDisplayState(...)` with these fields:
  - `VoiceLabel`
  - `MicLine`
  - `ModeWord`
  - `MicButtonEnabled`
  - `MicButtonContent`
  - `ModeButtonEnabled`
  - `PresenceMode`
- `sealed class ZolaDisplayStateModel`:
  - ctor takes `VoiceController`;
  - `UpdateWindowFacts(bool sessionReady, bool backendReachable, bool streaming, bool switchInFlight, bool historyPending, bool modeSwitching, bool unreachable, bool hasSessionId)`;
  - `Current`;
  - `event Action? Changed`.
- `Recompute()` applies:
  - the voice-label and mic-line priorities **verbatim** from Audit 01 §3 (every string
    identical);
  - the `PresenceMode` table in `P3-D04`;
  - the mode word and button rules from `ApplyVoiceChrome` 390–393.
- It raises `Changed` only when the record differs.
- It calls `VoiceController.SetCaptureGate(...)` exactly as `ApplyVoiceChrome` does today, so the
  mic gate keeps one writer.
- Every string and condition is a named constant. Tag: `// P3-STATE: … — P3-D03`
  (`P3-D04` on the mode table).

**`MainWindow.xaml.cs`:**
- Construct one `ZolaDisplayStateModel`.
- `ApplyVoiceChrome` becomes:
  1. push the window facts;
  2. read `Current`;
  3. assign the four existing controls (`VoiceStateText`, `MicIndicatorText`, `ModeButton`,
     `MicButton`).
- It contains **no conditions** on voice facts.
- `VoiceController.StateChanged` still dispatches `ApplyVoiceChrome` (Audit 01 §4). No new
  threading paths.
- Tag: `// P3-STATE: … — P3-D03`.

**`VoiceController.cs`:**
- Carry-over per `P3-D15`. No other change.
- Tag: `// P3-STATE: … — P3-D15`.

**`zola-architecture/identity/VOICE_CONFIG.md`:** the three tuning-log rows per `P3-D15`.

### Exit criteria
- [ ] `ApplyVoiceChrome` contains no `if`/`else` on voice or window facts; it only assigns from
      `ZolaDisplayState` (verified by reading the diff).
- [ ] A search of `windows-client` for the voice-label and mic-line string literals finds them
      only in `ZolaDisplayState.cs`.
- [ ] `PresenceMode` is computed per `P3-D04` and exposed on `Current`. Nothing consumes it yet.
- [ ] `EchoContainmentRatio`, `EchoMinWords` and `EchoPhraseWords` are gone; the comments cite
      `P2-D14`; the three `VOICE_CONFIG.md` rows read "Removed (P3-STATE)".
- [ ] Log line `P3-STATE: display state …` (debug) on every `Changed`, printing the voice label,
      the mic line and the presence mode, so the smoke run can read the transitions. Also log
      every `UpdateWindowFacts` call that changes `unreachable`, `switchInFlight` or
      `historyPending`, including failure and recovery paths, even if the record then
      compares equal.
- [ ] The stale-state recovery paths in `P3-D04` are verified by reading the code: Cancel
      acknowledgement, `ClearTranscript` on new session and resume, and `CancelFollowUp`. The
      stale-thinking warning log exists and does not change the mode.
- [ ] `hermes-agent` `git status` clean.
- [ ] `dotnet build … -r win-x64` passes with 0 warnings.
- [ ] Smoke test (HUMAN-RUN, labels plus log). Every label must read exactly as before:
  1. Cold launch: `Mic: listening for "Hey Zola"`; log mode `Idle`.
  2. "Hey Zola", ask a question. Labels walk Listening → Transcribing → Thinking → Speaking →
     Idle; log modes Listening → Thinking → Speaking → Idle.
  3. Barge-in once; follow-up once.
  4. Text mode: label "Text mode", mic off, log `Idle`. **Type a question in Text mode:** log
     `Idle → Thinking → Idle`, mic stays off, no speech. Return to Voice.
  4b. Voice turn with a spoken reply: the log shows `Thinking` until `message.start`, then
     `Speaking` while she talks, while the voice label keeps its P2 order (it may read
     "Thinking" during streaming). Both are recorded.
  5. New session and Resume: "Reconnecting voice…" appears, then resting.
  6. Kill the serve process: controls disabled, log `Dormant`.

**Complexity:** Small-Medium
**Primary risk:** a silent change in label priority. (The presence-mode order in `P3-D04`
deliberately differs from the label order; the label order must not move.) For example, `Reconnecting voice…` loses to
`Mic: off` because an input fact was pushed late: `_switchInFlight` is set inside
`OnNewSessionClick` before `UpdateChrome` runs, and must still be pushed before `Recompute`. The
verbatim-strings search and the reconnect smoke step exist for this.

---

## Track 2 — Obsidian Shell (`P3-SHELL`)

### Problem
The window is a theme-following chat column with a permanent composer and a header
(`P3PRE-AUD-02`, `-06`). There are no tokens, fonts or HUD. The doc requires the presence at the
centre, a contextual dock, and panels that orbit the presence (§14–§16).

### Files to read
- `MainWindow.xaml` and `MainWindow.xaml.cs` (as merged by Track 1), in full.
- `App.xaml` and `App.xaml.cs`.
- `Zola.Client.csproj`.
- `ZolaDisplayState.cs`.
- Audit 01 (all), Audit 05 §1–§3, and Audit 07.
- `C:\Users\test\Dev\zola-assets\zola_concept_reference.png` and `android_hud_reference.png`
  (layout reference only).

### Changes

**Pre-approved commands (this track only), run from `windows-client\Zola.Client\`:**
```
Copy-Item C:\Users\test\Dev\zola-assets\fonts\rajdhani_regular.ttf  Fonts\rajdhani_regular.ttf
Copy-Item C:\Users\test\Dev\zola-assets\fonts\rajdhani_semibold.ttf Fonts\rajdhani_semibold.ttf
Invoke-WebRequest https://raw.githubusercontent.com/google/fonts/main/ofl/rajdhani/OFL.txt -OutFile Fonts\OFL.txt
```
- Verify both fonts' SHA-256 against the Grounding summary.
- If the `OFL.txt` download fails, or its text is not SIL OFL 1.1 naming Rajdhani's copyright
  holder, stop BLOCKED. No other source may be used.

**`.gitattributes` (new, repo root):** `*.ttf binary`, `*.glb binary`. Tag in a comment:
`P3-SHELL — P3-D12`.

**`Zola.Client.csproj`:** add both `Fonts\*.ttf` and `Fonts\OFL.txt` as `Content` with
`CopyToOutputDirectory=PreserveNewest`. Change nothing else.

**`Themes/ZolaTokens.xaml` (new) + `App.xaml`:**
- Every K7 colour as a `Color` plus a `…Brush`.
- The type styles from Audit 07's table at S = 2, all Rajdhani, via
  `ms-appx:///Fonts/<file>.ttf#<Family>`.
- Dock and panel geometry constants.
- Merged in `App.xaml` after `XamlControlsResources`.
- Tag: XAML comment `P3-SHELL — P3-D08`.

**`MainWindow.xaml` / `.cs`:**
- Restructure per `P3-D11`:
  - the root `Grid` keeps the `Ctrl+Space` accelerator;
  - `RequestedTheme="Dark"`;
  - background `ZolaBackgroundBrush`.
- A named `PresenceHost` `Grid` in the presence layer, empty this track.
- The HUD per `P3-D06`/`P3-D07`, bound to `ZolaDisplayState` (voice and mic lines), the clock, and
  the session/link lines.
- The dock, conversation overlay and sessions panel per `P3-D11`.
- Every existing `x:Name` is kept. `StatusText`/`DetailText` move to the notice line.
- `BubbleBrush` and the bubble factory use token brushes only, with no theme brushes.
- The title header and the permanent composer row are removed. The composer lives in the
  overlay.
- `AppWindow.Resize(1280, 800)` plus a 900×640 minimum.
- No new behaviour logic: open and close are visibility toggles, and all actions call the
  **existing** handlers.
- The conversation overlay width is `min(ConversationOverlayMaxWidth = 440,
  ConversationOverlayMaxFraction = 0.45 × window width)`.
- Tag: `// P3-SHELL: … — P3-D0X`.

### Exit criteria
- [ ] Every control in Audit 01 §1 still exists with the same `x:Name` and the same handler
      (verified by listing names before and after).
- [ ] Every behaviour in Audit 01 §2 still works (smoke).
- [ ] No colour, font family or font size is set outside `ZolaTokens.xaml` (search the XAML and
      `.cs`).
- [ ] No hidden HUD element from `P3-D06` appears. No text says "ENCRYPTED", "OPTIMAL",
      "ATTENTION", "CALM" or a location.
- [ ] Font files SHA-verified. `OFL.txt` committed alongside them.
- [ ] `hermes-agent` clean.
- [ ] `dotnet build … -r win-x64` passes with 0 warnings.
- [ ] Smoke test (HUMAN-RUN):
  1. **Typeface check by eye:** the wordmark and HUD read as Rajdhani (narrow, squared letters,
     as in `font-msappx.png`), **not** Segoe UI. Screenshot beside `android_hud_reference.png`.
  2. The full Phase 2 combined smoke from `PHASE2_BUILD_PLAN.md` Exit Checklist:
     - cold launch, "Hey Zola", spoken answer;
     - barge-in;
     - follow-up;
     - timeout, then wake again;
     - Text mode typed turn, silent;
     - Resume;
     - relaunch from the shortcut.
  3. Conversation overlay:
     - open it, type and Send, see bubbles;
     - close it during a spoken turn;
     - reopen it: bubbles are complete;
     - Esc closes it.
  4. Cancel is visible in the dock only while a turn runs, and it stops the turn.
  5. The sessions panel opens, and New session and Resume work.
  6. Kill the serve process: link line "OFFLINE", composer/mic/mode disabled.
  7. Resize to 900×640: no HUD element overlaps another; the dock stays reachable.
  8. **With the conversation overlay open** at 900×640, 1280×800 and 1920×1080: the dock stays
     reachable and uncovered, and the overlay leaves the bust's face at least partly visible.
     At narrow widths the overlay width is `min(440, 45% of window width)`, a named constant.
     Screenshot each.

**Complexity:** Medium-Large
**Primary risk:** a broken code-behind reference after the XAML restructure
(`P3PRE-AUD-05`). A renamed or removed element compiles, fails at runtime (a null reference in a
handler), or silently stops a behaviour, for example `ScrollToEnd` on a collapsed viewer. Keeping
every `x:Name` and running the full Phase 2 combined smoke exist for this.

---

## Track 3 — 3D Presence (`P3-RENDER`)

### Problem
There is no presence renderer. The spike proved the approach, but it was throwaway code outside
the repo.

### Files to read
- `MainWindow.xaml(.cs)`, `ZolaDisplayState.cs`, `Themes/ZolaTokens.xaml`, `Zola.Client.csproj`
  (as merged by Track 2).
- `…Audit_03_HelixSpike.md` in full, with Lighting / fidelity.
- `…Audit_02_GlbCapabilityMap.md` §1 (texture assignment).
- The spike source in `C:\Users\test\Dev\zola-spikes\p3pre-helix\`, **reference only**. Do not
  copy files wholesale. Re-implement to this plan's structure.

### Changes

**Pre-approved commands (this track only), run from `windows-client\Zola.Client\`:**
```
dotnet add package HelixToolkit.WinUI.SharpDX --version 3.1.2
dotnet add package HelixToolkit.SharpDX.Assimp --version 3.1.2
Copy-Item C:\Users\test\Dev\zola-assets\zola.glb Assets\Presence\zola.glb
```
- Verify the GLB's SHA-256 (`1edf2bf5…054b`). A mismatch is BLOCKED.
- Record any `NU1xxx` output. If there is a warning or an App SDK version change, stop BLOCKED.

**`Zola.Client.csproj`:** the `Assets\Presence\zola.glb` `Content` item plus the two package
references added by the commands.

**`Presence/PresenceView.cs` (new, `UserControl` built in code):**
- Constructs `Viewport3DX` in code (`P3PRE-AUD-19`):
  - `BackgroundColor` from the `ZolaBackground` token (`#080808`), read from resources, not a
    literal *(v1.3)*;
  - camera per the Grounding summary;
  - FXAA left at default unless Track 4 changes it.
- `LoadAsync()` imports `ms-appx`-resolved `Assets/Presence/zola.glb` **off the UI thread**. It
  then:
  - builds a `PBRMaterialCore` per `P3-D02`, finding `Image_1` by parsing the GLB JSON;
  - applies the L9 baseline lights and a procedural environment cube with
    `SkipRendering = true`;
  - verifies `MorphTargetWeights.Length == 15` before enabling morphs.
- `SetWeight(MorphTarget target, float w)`:
  - `MorphTarget` is an enum in K3 order (`P3-D02`);
  - it clamps `w` to 0–1;
  - it batches, then calls `WeightUpdated()` once per frame.
- Rendering stays lazy (on demand):
  - `PauseRendering()` / `ResumeRendering()` for minimize and occlusion, from
    `AppWindow.Changed` / visibility;
  - session lock/unlock handling that pauses on lock and resumes and re-validates on unlock.
    *(v1.3)* `Microsoft.Win32.SystemEvents.SessionSwitch` may need a package that WinUI apps
    do not reference. If it is not available without a new package, use
    `WTSRegisterSessionNotification` plus a window subclass (`SetWindowSubclass`) for
    `WM_WTSSESSION_CHANGE`, through P/Invoke. No new package either way.
- **Failure handling (v1.1)**:

  | Failure | Handling |
  |---|---|
  | GLB missing, unreadable or fails import | Static fallback: `#080808` with one centred line, "PRESENCE UNAVAILABLE", in the muted header style *(v1.3: replaces a centred wordmark, which would duplicate the HUD's)*. Logged `P3-RENDER: presence unavailable — <reason>` |
  | Morph weight count ≠ 15 | Static fallback (never drive the wrong targets) |
  | Recoverable device loss (lock, sleep, driver reset) | Recreate or reinitialize rendering and reload the scene, then log `P3-RENDER: device recovered` |
  | Unrecoverable renderer failure, process still healthy | Static fallback |
  | Native crash that takes down the process | Not catchable. The track stops **BLOCKED** and reports; no workaround. |

  The static fallback cannot catch every GPU or native failure, and the plan does not promise
  that it does.
- `LoadAsync()` is guarded: it is idempotent and serialized, so concurrent calls (for example,
  unlock and resume firing together) coalesce into one load. The import runs off the UI
  thread. **Attaching the imported scene to the viewport, and every scene-graph mutation, happen
  on the UI thread** through the dispatcher.
- No `PresenceMode` consumption yet (Track 5).
- Tag: `// P3-RENDER: … — P3-D02`.

**`Presence/MorphTarget.cs` (new):** the K3 enum plus one comment line citing `P3-D02`.

*(v1.3)* Two helper files are allowed, so `PresenceView` stays readable:
- `Presence/GlbTextureLocator.cs`: the GLB JSON walk to `Image_1` (`P3-D02`);
- `Presence/SessionLockWatcher.cs`: lock/unlock and suspend/resume notifications (the same
  window subclass can receive `WM_POWERBROADCAST`).

Presence log lines go to `%LOCALAPPDATA%\ZolaClient\logs\presence.log`, the same folder as the
display-state log.

**`MainWindow.xaml.cs`:** create `PresenceView` into `PresenceHost` and call `LoadAsync` after
the window shows. Nothing else.

### Exit criteria
- [ ] The bust renders centred on `#080808` with the four textures, as in the L9 baseline, at
      launch and at 900×640, 1280×800 and maximized *(v1.3: maximized replaces a 1920×1080
      resize, which spans monitors on a multi-monitor setup)*.
- [ ] A debug-only command (behind `#if DEBUG`, not in the dock) sets `Blink both` = 1, then
      resets. The face deforms and returns to neutral.
- [ ] Deleting the GLB from the output folder gives the static fallback plus the log line, and
      voice and chat still work.
- [ ] The first frame does not block the UI thread. Log the load duration; the window paints
      the HUD before the bust appears. Scene attachment happens on the UI thread (verified in
      the diff).
- [ ] Two rapid `LoadAsync` calls (a debug-only trigger) result in exactly one load (log).
- [ ] Memory recorded: working set before and after model load (the `P3PRE-AUD-24` baseline was
      671 MB).
- [ ] GPU with the static bust averages ≤ 1% over 60 s (lazy rendering holds).
- [ ] `Ctrl+Space` works with the presence focused and with the conversation overlay focused.
- [ ] `hermes-agent` clean. Package references are exactly the two above.
- [ ] `dotnet build … -r win-x64` passes with 0 warnings.
- [ ] Smoke test (HUMAN-RUN):
  1. The bust looks like the L9 spike shot (`shots/L9-pbr-lit.png`).
  2. Minimize 30 s → restore: it renders.
  3. **Lock the PC (Win+L), wait 1 min, unlock:** the bust renders and there is no crash. This
     is the first real test of lock/unlock (P3PRE left it unverified).
  4. **Sleep for 1 min, then wake:** the bust renders.
  5. The Phase 2 combined smoke, abbreviated (wake, answer, barge-in, Text mode, Resume), still
     passes.

**Complexity:** Medium-Large
**Primary risk:** device loss on unlock or wake. P3PRE could not observe unlock. If Helix's
DirectX device is removed during lock or sleep and not recreated, the presence freezes or the
process faults. That would take down voice too, since it is the same process. The fail-closed
fallback and the explicit lock and sleep smoke steps exist for this. A fault that crashes the
process is BLOCKED, not patched around.

---

## Track 4 — Fidelity (`P3-LOOK`)

### Problem
The L9 baseline hue is close, but contrast, rim light and bloom are not
(`P3PRE-AUD-18`; Audit 03 Lighting / fidelity). The reference's background glow, floor rings,
particles and corner brackets do not exist.

### Files to read
- `Presence/PresenceView.cs`, `MainWindow.xaml(.cs)`, `Themes/ZolaTokens.xaml`.
- Audit 03 Lighting / fidelity, and Audit 04 §6 (2D elements).
- `android_hud_reference.png` (fidelity target) and `zola_concept_reference.png`.

### Changes

**`Presence/PresenceView.cs`**, lighting as named constants in one
`Presence/PresenceLook.cs` (new):
- Cut ambient and fill relative to the key, so the face, neck and shoulder sides fall into
  shadow.
- Add a warm rim/back light for cream-white edges on the cheekbones, collarbones and hair tips.
- `PostEffectBloom` on, with a threshold that catches the eyes, chest diamond, centre line and
  bright hair.
- Tune `EmissiveColor`.
- Tuning is iterative, with the developer in the loop. Each iteration logs its values and a
  screenshot beside `android_hud_reference.png`.

**In-scene background:**
- A large emissive quad behind the bust with a procedural warm radial-gradient texture, generated
  in code, with no image file (`P3PRE-AUD-25`).
- A floor disc under the bust with procedural concentric amber rings.
- Both use K7 amber values and are kept dim, per §19 restraint.

**XAML decoration layer** (between the presence and the HUD):
- Corner brackets from `ZolaAmberMutedBrush`, as in the Android screenshot.
- A particle layer: at most 40 small `Ellipse`s in `ZolaPresenceAmberBrush` at 0.2–0.5 opacity,
  in fixed positions this track (drift comes in Track 5). The cap of 40 is a named constant
  (§23).

**Texture-size test (`P3-D13`):**
- Produce a 1024² variant of the four textures at load time in a debug build (downscale in
  memory, no new files), and show 2048² vs 1024² side by side.
- The developer picks. If 1024² is chosen, the load-time downscale ships behind a named
  constant. The GLB file is not modified.
- Record the working-set difference.

**Dock and notice (v1.4):** implement `P3-D17` and `P3-D18` in `MainWindow.xaml(.cs)` and
tokens.

**Iteration aid (v1.4):** a `#if DEBUG` hook reloads the look values from
`%LOCALAPPDATA%\ZolaClient\debug\presence-look.json` without a rebuild, so tuning rounds are
fast. The approved values are then written into `PresenceLook.cs` as constants. The JSON file
is never read in Release builds and is never committed.

**Memory after reloads (v1.4, from Track 3):** the resting working set is about 1.3 GB after
reloads, versus about 790 MB cold. Re-measure it with the texture-size decision, and decide with
numbers whether explicit disposal of the old scene on reload is worth adding.

**Shell polish carried from the Track 2 review (v1.3):**
- the `Composer` focus underline still uses the system accent; restyle it with the amber tokens;
- the conversation overlay's 0.88 opacity lets the HUD show through under its header; tune it
  against the rendered bust;
- at 900 px the overlay covers the right end of the notice line; the notice line must stay
  readable when the overlay is open;
- the Voice/Text (`E8D4`) and Sessions (`E8A5`) glyphs do not match their names; choose glyphs
  that do;
- `ZolaMantraIndent` 124 sits further right than Android; tune it to match (about 100 is
  expected);
- corner brackets (already listed above).

Tag: `// P3-LOOK: … — P3-D13`.

### Exit criteria
- [ ] Every lighting, bloom, emissive and background value is a named constant in
      `PresenceLook.cs`.
- [ ] Developer judgement recorded verbatim: the still frame "reads as Zola" beside
      `android_hud_reference.png`. The progress doc records the final values plus the same
      cheek, hair and chest samples as Audit 03 for reference, without pass/fail numbers.
- [ ] Background glow and floor rings are in-scene; the window background outside them stays
      `#080808`.
- [ ] Particles ≤ 40; brackets use tokens. The decoration layer sits between the presence and
      the HUD (`ZolaLayerDecoration`, between 0 and 10) and is not hit-testable.
- [ ] *(v1.4)* The dock follows `P3-D17` and the notice line follows `P3-D18`. Each has exactly
      one deciding method (search). No existing `StatusText`/`DetailText` writer changed (diff).
- [ ] *(v1.4)* The shell polish list is done: composer accent, overlay opacity, notice at 900 px,
      dock glyphs, mantra indent.
- [ ] *(v1.4)* The debug look-reload reads its JSON only under `#if DEBUG`, and the JSON is not
      committed.
- [ ] *(v1.4)* Reload memory re-measured with the chosen texture size; the explicit-disposal
      decision recorded with numbers.
- [ ] Texture decision recorded with the final working set, the **peak** working set during
      load, and the load time, for both 2048² and 1024². An in-memory downscale can raise
      peak memory and load time even when final memory falls.
- [ ] Static GPU with bloom on (nothing moving) is recorded. Lazy rendering must still hold at
      ≤ 1%.
- [ ] `hermes-agent` clean.
- [ ] `dotnet build … -r win-x64` passes with 0 warnings.
- [ ] Smoke test (HUMAN-RUN): the side-by-side above, plus the abbreviated Phase 2 smoke.

**Complexity:** Medium
**Primary risk:** bloom and the extra lights make the static frame cost GPU continuously, if the
post-effect forces continuous rendering. That would break `P3-D09` before any animation exists.
The static-GPU criterion catches it here, where the fix is local.

---

## Track 5 — Procedural Life (`P3-LIFE`)

### Problem
The presence is a still frame. The doc requires state-driven, restrained procedural life (§3,
§5, §7, §8, §9) within a desktop-appropriate budget (`P3-D09`).

### Files to read
- `Presence/PresenceView.cs`, `Presence/PresenceLook.cs`, `ZolaDisplayState.cs`,
  `MainWindow.xaml(.cs)`.
- `Zola_Presence_UI_Architecture.md` §3–§9 and §23.
- Audit 02 §3 (morph → behaviour map) and Audit 04 §1b (transition matrix).

### Changes

**`Presence/PresenceAnimator.cs` (new):** the only writer of morph weights and node transforms.
It reads `ZolaDisplayState.PresenceMode` through the model's `Changed` event, and never reads
voice or window facts directly (`P3-D03`).
- **Per-frame composition (v1.1).** Controllers never write weights. Each frame, in this fixed
  order:
  1. **Base expression:** `ExpressionController` gives the target weights for the current
     mode.
  2. **Channels:** blink, mouth, breathing and head motion each compute their own
     contribution.
  3. **Compose:** shared targets are resolved by an ownership table:
     - `MouthController` exclusively owns indices 8–14 while `SPEAKING` (the base expression's
       `Wide EE` is ignored meanwhile);
     - `BlinkController` owns indices 0–2 and adds to the base;
     - the base owns 3–7 except where a channel is declared owner;
     - head motion owns the node transform;
     - breathing owns glow and bloom only.
  4. **Smooth:** transitions and springs per the coordinator.
  5. **Commit:** set every changed weight and transform, then call `WeightUpdated()` once.

  When `SPEAKING` ends, ownership of 8–14 returns to the base expression through smoothing, not
  a snap.
- **Controllers** (one class each, in `Presence/Controllers/`, named per §5, sharing no state):
  - `BlinkController`:
    - `Blink both` on a random 2500–7500 ms interval; about 150 ms close, 100 ms open;
    - occasional left/right asymmetry;
    - suppressed in `Listening` (longer intervals) and `Dormant`;
    - blink suppression is a timer rule (`P3PRE-AUD-09`).
  - `BreathingController`:
    - an asymmetric sine, 40% inhale / 60% exhale, at the §5 mode rates;
    - **none in `Dormant`** (a steady reduced glow; `P3-D04`);
    - output drives bloom intensity and `EmissiveColor` within small bounds (`P3-D05`);
    - never whole-body scale;
    - a deeper breath every 30–40 s.
  - `ExpressionController` — mode → weights. These are the starting values; the developer tunes
    them in smoke and the final values are recorded:

    | Mode | Weights |
    |---|---|
    | Idle | all 0, `Wide EE` 0.05 |
    | Listening | `Wide/alert` 0.35, `Brow raise` 0.15 |
    | Thinking | `Brow furrow` 0.35, `Squint` 0.15 |
    | Speaking | Idle weights plus the mouth cycler |
    | Alert | `Wide/alert` 0.8, `Brow furrow` 0.5 (defined, unused, `P3-D04`) |
    | Dormant | `Squint` 0.25, steady glow at 40%; no blink, breathing or head motion |

  - `MouthController` per `P3-D14`.
  - *(v1.4, Track 3 finding)* `BlinkLeft` / `BlinkRight` are **her** left and right, the
    anatomical convention (`BlinkLeft` closes the eye on the viewer's right). Asymmetric blinks
    use them as-is; do not swap them.
  - `HeadMotionController`:
    - Listening: a forward pitch of 2°, spring-smoothed (attention lean);
    - an idle micro-turn of ±1.5° yaw every 8–15 s, standing in for saccade (`P3-D05`).
  - `ModeTransitionCoordinator` staggers each change:
    - eyes 150–250 ms;
    - breathing 400–600 ms;
    - expression 700–1000 ms (§8).
  - Particle drift, slow and within the cap.
- **Rendering budget (`P3-D09`):**
  - one animation tick source;
  - 30 fps when idle; 60 fps only during transitions and `Speaking`;
  - invalidate only when a value changed;
  - pause entirely when minimized, occluded or locked.
- **Reduced motion:** honour `UISettings.AnimationsEnabled` and `AnimationsEnabledChanged` live:
  - no particle drift, no micro-turn, no mouth cycling;
  - breathing reduced to a slow glow, at the lowest cadence in `P3-D09` and still within the
    idle budget;
  - blinks stay;
  - transitions become instant (§23).
- Tag: `// P3-LIFE: … — P3-D0X`.

### Exit criteria
- [ ] `PresenceAnimator` is the only code that calls `SetWeight` or changes node transforms
      (search).
- [ ] No controller reads `VoiceController` or window fields; only `ZolaDisplayState` (search).
- [ ] Mode changes follow Audit 04 §1b in the smoke log: every transition enters and exits, and
      nothing stays stuck after Cancel, a turn error, a stop phrase or reconnect.
- [ ] **Idle GPU ≤ 10%** averaged over 60 s in `Idle` with idle life on (`P3-D09`). If not met
      after the levers → BLOCKED with measurements. Speaking and transition readings are
      recorded.
- [ ] Minimized, occluded and locked: GPU about 0%.
- [ ] Reduced motion toggled live changes behaviour as specified.
- [ ] Final expression weights, breathing amplitude and mouth cycler ranges recorded.
- [ ] `hermes-agent` clean.
- [ ] `dotnet build … -r win-x64` passes with 0 warnings.
- [ ] Smoke test (HUMAN-RUN):
  1. Watch 2 minutes idle: blinks are irregular, breathing is visible but calm, and there is an
     occasional small head turn. It must not look busy (§19).
  2. "Hey Zola" plus a question: Listening lean, then Thinking furrow, then the Speaking mouth
     moves while she talks and stops within about 1 s of the estimate ending.
  3. Barge-in, Cancel, Text mode: the presence settles to Idle each time.
  4. Kill the serve process: Dormant (dim, still, lids lowered).
  5. Reduced motion on (Windows Settings → Accessibility → Animation effects off): the reduced
     behaviour appears without a restart.
  6. The full Phase 2 combined smoke plus lock/unlock and sleep/wake.
  7. The developer judges the overall presence against the doc's §25 motion questions.

**Complexity:** Medium-Large
**Primary risk:** blowing the budget. Idle life at 60 fps costs about 34.5% GPU (`P3PRE-AUD-26`).
If the tick source drives full-rate rendering, or bloom forces continuous rendering, idle cost
exceeds `P3-D09`. The budget is measured before the track can close. The track stops BLOCKED
rather than shipping over budget.

---

## Phase 3 Lore Closeout

After all five tracks are merged to `main`:

### DESIGN_DECISIONS.md
- Add a "Phase 3 — Presence UI" section recording `P3-D01` through `P3-D18`, with the final
  tuned values:
  - Track 4: lighting, bloom and texture size;
  - Track 5: expression weights, breathing, mouth cycler and idle frame rate;
  - the measured idle GPU and memory.
- Annotate `P2-D08`: the voice-state indicator is now derived by `ZolaDisplayState` (`P3-D03`).
  The strings are unchanged.

### OPEN_QUESTIONS.md
- **File `S24` — GLB asset rework.** Separate eye geometry (saccade), a hair mesh (strand
  shimmer), projection geometry, a chest emissive region (chest-only breathing), a frown/negative
  mouth target, and an eye-softness target (`P3PRE-AUD-10`–`16`). Any rework must keep the 15
  targets and their order, or update `MorphTarget.cs`.
- **File `S25` — HUD data sources.** Attention level, conversational momentum, emotional tone,
  system health, environment, version, and the dock and Core Systems destinations (Memory,
  Environment, Awareness, Behavior, Security, Systems, Settings, Account). Each needs a real
  source first (`P3-D06`).
- **File `S26` — A missing `message.complete` leaves the turn "Thinking".** `_streaming` never
  clears (Audit 04 §1b), and the presence stays in `THINKING`. This is a Phase 1 behaviour made
  more visible by Phase 3.
- **Update `S17`:** an end-of-playback or speaker-meter signal would also give real mouth
  amplitude (`P3-D14`).
- **File `S27` — Mic-input meter in the identity block (v1.3).** Only if Track 5 could not
  fill the reserved space honestly (`P3-D07`).
- **File `S28` — Session UI retirement (v1.3).** The developer expects his memory system to
  make sessions unnecessary. When it does, remove the SESSION HUD line and the Sessions dock
  button together.
- **File `S29` — Markdown rendering in chat bubbles (v1.3).** Bubbles are plain text, so fenced
  code, lists and links show as raw markdown. This predates Phase 3.
- `S13`, `S16`, `S18`–`S23` unchanged.

### ROADMAP.md
- Mark Phase 3 COMPLETE with the plan and track merge SHAs, the P3PRE audit
  (`c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`), and the machine notes (idle GPU, memory).
- Phase 4 stub with candidates only: `S17`, `S22`, `S16`, `S20`, `S24`, `S25`, `S13`, `S12`.

### Zola_Presence_UI_Architecture.md (named explicitly in scope for the lore-closeout prompt only)
- Add a `> **Windows Track:**` note under "Canonical Visual Direction" citing `P3-D01`
  (GLB replaces the SVG; Helix 3D).
- Add a note under §4 `PresenceMode` citing `P3-D04` (`DORMANT`).
- Add a note under §14 citing `P3-D06`/`P3-D07` (true state only; the identity exception).

---

## Phase 3 Exit Checklist

- [ ] Track 1 (`P3-STATE`) merged. One display-state authority; labels unchanged; carry-over
      removed.
- [ ] Track 2 (`P3-SHELL`) merged. Obsidian shell, tokens, Rajdhani confirmed by eye, every
      Phase 1/2 behaviour intact.
- [ ] Track 3 (`P3-RENDER`) merged. The bust renders; fail-closed fallback; lock/unlock and
      sleep/wake verified.
- [ ] Track 4 (`P3-LOOK`) merged. The developer's fidelity judgement recorded; static GPU ≤ 1%.
- [ ] Track 5 (`P3-LIFE`) merged. Procedural life; idle GPU ≤ 10%; reduced motion honoured.
- [ ] One authority: the voice label, mic line and `PresenceMode` are derived only in
      `ZolaDisplayState.cs`. Morph and transform writes happen only in `PresenceAnimator.cs`.
- [ ] No UI design literals (colours, font families, font sizes, spacing) outside
      `ZolaTokens.xaml`. No lighting, bloom or emissive literals outside `PresenceLook.cs`.
      Texture dimensions, animation parameters, camera values, timing values, thresholds,
      weights and RPC names are named constants in their own files; that is still required, but
      they are not tokens.
- [ ] No HUD text claims state the client cannot prove (no ENCRYPTED, OPTIMAL, ATTENTION, CALM
      or location).
- [ ] `P2-D01` holds: the client opens no audio device. Helix renders only; the client does no
      audio capture or playback.
- [ ] Exactly one submit path (`SubmitTurnAsync`), unchanged.
- [ ] No file in `C:\Users\test\Dev\hermes-agent` modified. No Python installed.
- [ ] Package references are exactly those from Phase 2 plus the two Helix packages.
- [ ] `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` passes on `main`
      after all merges.
- [ ] Combined smoke on `main` after Track 5, on the Latitude 7430, following `P2-D16` setup
      (lid open, and so on):
  1. Cold launch from the shortcut. The presence appears; the HUD reads true state.
  2. "Hey Zola" question → spoken answer, with Listening → Thinking → Speaking presence.
  3. Barge-in.
  4. Follow-up.
  5. Timeout, then wake again.
  6. Text mode typed turn in the conversation overlay (silent); back to Voice.
  7. Resume an older session from the sessions panel.
  8. Lock/unlock and sleep/wake; the presence and voice recover.
  9. Kill the serve process: Dormant plus "OFFLINE".
  10. Relaunch.
  11. 2 minutes idle: GPU ≤ 10%, nothing busy.
- [ ] `DESIGN_DECISIONS.md` has `P3-D01`–`P3-D18`, and `P2-D08` is annotated.
- [ ] `OPEN_QUESTIONS.md` has `S24`–`S26` and `S28`–`S29` filed (plus `S27` if needed) and
      `S17` updated.
- [ ] `ROADMAP.md` marks Phase 3 COMPLETE and has the Phase 4 stub.
- [ ] The presence UI doc has its Windows Track notes.

---

## What Phase 3 Explicitly Defers

| Item | Reason | When |
|---|---|---|
| Micro-saccade, hair strand shimmer, pixel-projection and hologram layers, chest-only breathing, frown and eye-softness expressions | The asset lacks the geometry or targets (`P3-D05`) | `S24` |
| Attention, momentum, emotional tone, system health, environment, version and encrypted-link HUD readouts | No source supports them (`P3-D06`) | `S25` |
| Memory, Environment, Awareness, Behavior, Security, Systems, Settings and Account panels (the dock and Core Systems list) | No client actions or backends exist | `S25` |
| Location block | No source; privacy plan; would need a network lookup (`P3-D10`) | Revisit with `S25` |
| Audio-driven lip-sync and precise speaking end | No amplitude signal; client plays no audio (`P3-D14`) | `S17` |
| `ALERT` mode being produced | No urgency or security signal on Windows | With `S25` |
| Orbitron wordmark | Rajdhani chosen (`P3-D08`) | Not planned |
| Decorative waveform | It would look like a live audio reading; the space is reserved (`P3-D07` v1.3) | A real meter in Track 5, or `S27` |
| Markdown rendering in bubbles | Pre-existing plain-text bubbles | `S29` |
| Title-bar customization | Not needed for v1 of the shell | Future client polish |
| Persisted Voice/Text mode, window size and panel state | Still no client settings store | Future client-settings work |
| Stuck "Thinking" on a missing `message.complete` | Pre-existing Phase 1 behaviour | `S26` |
| Global hotkey | Unchanged | `S18` |
| GLB re-authoring | Out of scope | `S24` |

---

## Complexity Legend

| Track | Complexity | Primary Risk |
|---|---|---|
| 1 — Display-state authority (`P3-STATE`) | Small-Medium | Label priority silently changes when a window fact is pushed late |
| 2 — Obsidian shell (`P3-SHELL`) | Medium-Large | A code-behind reference breaks after the XAML restructure |
| 3 — 3D presence (`P3-RENDER`) | Medium-Large | DirectX device loss on unlock or wake, unverified by P3PRE |
| 4 — Fidelity (`P3-LOOK`) | Medium | Bloom or lights force continuous rendering, raising static GPU |
| 5 — Procedural life (`P3-LIFE`) | Medium-Large | Idle animation exceeds the 10% GPU budget |

---

*Phase 3 Build Plan version 1.4*
*v1.4 (2026-09-25, before Track 4): `P3-D17` dock hidden until needed; `P3-D18` notice line fades,
problems stay; Track 4 adds dock/notice, a debug look-reload aid, and the reload-memory
re-measure; Track 5 notes her-left blink convention. Track 3 merged at
`f61e1ae014bdf22bc0cab04e128bd93f0ffdebe5`.*
*v1.3 (2026-09-24, before Track 3): `P3-D07` three-line tagline, mantra indent and reserved
waveform space; `P3-D11` voice-block wording and composer focus return; Track 3 background from
the token, lock/unlock without a new package, "PRESENCE UNAVAILABLE" fallback, two helper
files, presence log, maximized instead of 1920×1080; Track 4 shell polish from the Track 2
review; `S27`–`S29` for the lore closeout. Track 2 merged at
`b8bf6a15c8b806bca0fea499dbcfce0535e92932`.*
*v1.2 (2026-09-24, before Track 2): the HUD voice block merges the VOICE and MIC headers; `LinkLabel`
added to `ZolaDisplayState`; conversation tokens plus one non-Android error colour; dock label
TextBlocks. Track 1 merged at `2fb98126eed05561c86b7b3e67ed454b0e7ef331`.*
*v1.1 (peer review, 2026-09-24): P3-D04 order (Speaking > streaming; Text mode last) plus
stale-state recovery and DORMANT stillness; P3-D09 adaptive cadence; P3-D14 mouth onset and
ease-out; Track 3 failure table, guarded LoadAsync, UI-thread scene attach; Track 5 composition
pipeline and ownership; overlay width at narrow sizes; texture peak memory and load time;
literal-scope clarification.*
*Created 2026-09-24*
*Base SHA: `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63` (P3PRE audit merge; tracks record their actual branch point)*
*Prerequisite audit: P3PRE — `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`*
*All Phase 3 decisions locked before the plan was written (Brian, 2026-09-24).*
*Next step: commit this build plan to `zola-architecture/lore/build-plans/` on `main`,*
*then begin the tracks strictly in order 1 → 2 → 3 → 4 → 5.*
