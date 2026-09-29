# P3-LIFE Progress — Procedural Life

## Branch

- Branch: `p3-life-procedural`
- Base SHA: `819c51b0fab8b5dafb8256fa02a558236191db7a` (plan v1.7 commit; branch point)
- Plan v1.7 commit SHA: `819c51b0fab8b5dafb8256fa02a558236191db7a`
- Recorded HEAD before the plan commit: `0c1894d1fad759f06c97df7c426c1c548715f3e0` (`docs: record P3-LOOK merge SHA`), a direct successor of P3-LOOK merge `c8f666251deacaf0fcb6a714594abf44da2e931b`
- Plan source SHA-256 (v1.7): `8b3df9dbb024de0aefaeaf97160b9162c2695041660f30b514a0f4de5752c9c3` (matched)
- Prompt: P3-LIFE v1.1

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Plan v1.7, Branch, and Progress Document | COMPLETE |
| 2 | Read and Report | COMPLETE |
| 3 | Build: Animator Skeleton | COMPLETE |
| 4 | Build: Eyes, Expression, Brightness, Stagger, Dormant | COMPLETE |
| 5 | Build: Speaking Mouth | COMPLETE |
| 5b | Build: TtsPlaybackMonitor | COMPLETE |
| 6 | Tuning Rounds | COMPLETE — life approved (Round 5 Alert) |
| 7 | Particle Field | COMPLETE — particles dropped |
| 8 | Smoke Test | COMPLETE |
| 9 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** `PresenceAnimator.cs`, `PresenceLife.cs`, controller classes, `PostEffectToneMap.cs` (gain multiplier only), `PresenceView.cs` (host animator; no look changes), `MainWindow.xaml.cs` (wire animator, DEBUG life hooks; Phase 7 particles), `VoiceController.cs` only if Phase 2 needs a one-line accessibility widen of `FirstSentenceLatencySeconds`, Phase 7 particle files/tokens/XAML, this progress document, and the Phase 1 plan replacement. No `ZolaDisplayState`, `PresenceLook`, `MorphTarget`, shader, GLB, packages, or image files under `windows-client/`. **Amended Phase 3-D2 (developer-approved):** `AcesTonemap.hlsl`/`.cso`, `PostEffectToneMap.cs` Color.rgb, `PresenceView.cs` invert removal, `PresenceLook.cs` invert-only constants. Amends the P3-D19/P3-D20 mechanism for the background only; bust look unchanged. **Amended Phase 5b (developer-approved):** `Presence/TtsPlaybackMonitor.cs`, `Presence/AudioSessionInterop.cs` (display-only session presence), `HermesProcessManager` one-line read-only serve-process accessor, animator/mouth wiring, new `PresenceLife` mouth keys. P2-D01 display-only: observe Hermes-owned player session presence; no audio data, level, or capture.
- **G-ARCH:** The build plan is truth. A conflict that affects a task is a stop.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** Tracks 1–4 behaviour stays, including load order, `LoadAsync` coalescing, generations, pause/resume, lock reuse, fallback, the approved look, tone-map fail-closed, and dock/notice rules.
- **G-ONE-WRITER:** `PresenceAnimator` is the only `SetWeight` / `WeightUpdated()` / gain-multiplier writer. Controllers return values. F11 routes through the animator. Nothing writes the bust node transform.
- **G-STILL-FRAME:** `IDLE` at rest is pixel-identical to `P3-LIFE_reference_raw.png` on bust-covered pixels (max delta 0), plus ≥4 field samples exactly `#080808`. Capture only after settled **and** presented. Named HUD exclusions: **TimeText** `(1142, 110, 42, 35)` (to 1183,144) and **SessionText** `(24, 684, 140, 22)` (to 163,705).
- **G-COMMENT:** One `// P3-LIFE: … — P3-D0X/P3-D1X/P3-D22` (XAML: `<!-- P3-LIFE: … -->`) per logically distinct changed block.
- **G-STOP:** Stop after each phase and after every tuning round. Wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-LORE-SCOPE:** `ROADMAP.md`, `DESIGN_DECISIONS.md`, and `OPEN_QUESTIONS.md` are out of scope, including closeout. The Phase 1 plan replacement is a plan commit, not a lore update.
- **G-NO-CROSS-SCOPE:** Android Zola, Ava, and the P3PRE spike folder are out of scope. Do not open the Android project.
- **G-KEYS:** Full KC10 surface; Android values are defaults, not limits; unused keys default to 0 / off; ranges span the meaningful domain.
- **G-VALUES:** Animation values as named constants in `PresenceLife.cs` with named ranges. Particle UI values in `ZolaTokens.xaml`. No number literals in code bodies.
- **G-RESTRAINT:** She is the subject. Prefer calmer. No breathing, head, or bust motion.
- **G-BUDGET:** Nothing renders while nothing changes. Idle GPU with idle life on ≤ 10% over 60 s (A7 method); expected near static ≤ 1% without breathing. Tick or render at rest → BLOCKED.
- **G-DEBUG:** Life reload and forced mode under `#if DEBUG`. Life JSON uses the P3-LOOK all-or-nothing contract. JSON never read in Release and never committed.
- **G-FEEDBACK-SCOPE:** Tuning changes values, not scope.
- **G-DEPS:** None.

## Phase 1

Working tree was clean on `main`. Pulled; already up to date. HEAD before the plan commit: `0c1894d1fad759f06c97df7c426c1c548715f3e0` (matches the prompt).

First hash of `C:\Users\test\Dev\zola-assets\plans\PHASE3_BUILD_PLAN.md` was `d00449e51bf49a3d3c5b97d09b4326922321e24cc9d8c89b2eee93cfcdb3b83f` (not the prompt). Stopped BLOCKED. Developer Option B: the matching file was put in place. Re-verified SHA-256 `8b3df9dbb024de0aefaeaf97160b9162c2695041660f30b514a0f4de5752c9c3`.

`git diff` against the committed v1.6 file showed only the v1.7 surface: Overview Track 5 row; `P3-D04` v1.7 Dormant starting values; `P3-D05` struck lean/breathing plus brightness; `P3-D09` measured text and cadence table; new `P3-D22`; Track 5 replaced in full (ownership, animation contract, reduced-motion table, key surface, exit criteria); lore closeout `P3-D22` range, Track 5 values, dock fold-in, code tidy, `S24`/`S27` wording; exit checklist (`P3-D22`, `S24`–`S30`, Track 5 line, gain-multiplier writes); deferrals; complexity-legend Track 5 risk; version footer.

Committed on `main` and pushed. Branch `p3-life-procedural` created from that commit. No client source files modified.

## Phase 2 findings

Read in full: every file under `Presence/` (`PresenceView.cs`, `PresenceLook.cs`, `PostEffectToneMap.cs`, `MorphTarget.cs`, `SessionLockWatcher.cs`, `AcesTonemap.hlsl`), `MainWindow.xaml(.cs)`, `ZolaDisplayState.cs`, `VoiceController.cs` (latency clock and `SetSpeaking`), `Themes/ZolaTokens.xaml`, plan v1.7 Grounding + `P3-D03`/`D04`/`D05`/`D09`/`D14`/`D16`/`D19`/`D20`/`D22` + Track 5, Audit 02 §3, Audit 04 §1b, SYNTHESIS `P3PRE-AUD-09`/`-16`/`-26`, P3-RENDER / P3-LOOK progress, lore files (no edits), architecture §3–§9, §19, §23, §25.

### 1. Rendering on demand

Today a 3D frame is requested with `Viewport3DX.RenderHost.InvalidateRender()` (`PresenceView.ApplyLook`, `ApplyRenderGate` on resume). `RenderHost.IsRendering` is true whenever the scene is Ready and `_pauseReasons` is empty; Helix still lazy-renders. P3-LOOK / P3-RENDER A7 static GPU avg **0.0013% / 0.0010%** with that gate, so `IsRendering = true` is not a 60 fps loop.

`SetWeight` only sets `_weightsDirty`. `ApplyWeights()` calls `_morph.WeightUpdated()` and does **not** call `InvalidateRender`. F11 morphs are visible, so `WeightUpdated()` alone dirties Helix and produces a frame while `IsRendering` is true.

The animator will commit once per tick: write changed weights, one `WeightUpdated()`, write the multiplier if it changed, then **one** `InvalidateRender()` (needed for gain; morphs already dirty). At rest the tick source stops, so nothing invalidates and GPU stays at the static floor.

Evidence nothing renders continuously now: A7/A9 method, tick does not exist yet, no `CompositionTarget.Rendering` loop (one-shot `OnFirstShellRender` unsubscribes). HUD `_clockTimer` is 1 Hz text only.

### 2. Tick source (KC5)

`DispatcherQueueTimer` on the same UI `DispatcherQueue` as `PresenceView` (`_dispatcher` / `MainWindow.DispatcherQueue`). Started only while a blink, unsettle ease/spring, or `SPEAKING` mouth/pulse is active; stopped otherwise. Next blink is `Interval` to the due time on that same timer, not a second timer type.

Pause/resume: hook `PresenceView.PauseRendering` / `ResumeRendering` (minimize, hidden, lock, suspend). No second `AppWindow` / lock path. On pause: stop the timer. On resume: read current `PresenceMode`, discard expired blink/mouth/stagger, set channels to the current state, schedule only future work, no replay.

### 3. Gain multiplier

`PostEffectToneMap.Gain` → `NodePostEffectToneMap` → `PostEffectToneMapCore._gain`, uploaded as `Color.a` (`// P3-LOOK: Color.a is gain`). The core setter is a plain assign (no `SetAffectsCanRenderFlag`). Look reload writes `_toneMap.Gain = _look.ToneMapGain` then `InvalidateRender`.

Phase 3 adds a runtime **multiplier** (default 1.0) on `PostEffectToneMap` only. Effective shader gain = look gain × multiplier. `PresenceLook` is untouched. Animator is the only multiplier writer. A change calls `InvalidateRender` once.

Fail-closed (`_toneMap` null / `EffectEnabled` false / `P3-LOOK: tone map unavailable`): skip multiplier writes and log once (same `_toneMapUnavailableLogged` pattern).

**Flag:** `ApplyToneMappedClear` inverts displayed `#080808` using `_look.ToneMapGain` only. When the multiplier is not 1.0, the field will drift unless the invert uses effective gain. IDLE stays 1.0 (G-STILL-FRAME). Phase 3/4 should re-pick the clear from `lookGain × multiplier` without changing look defaults.

### 4. `SetWeight` / `WeightUpdated` sites (G-ONE-WRITER)

All in `PresenceView.cs` today:

| Site | What |
|---|---|
| `SetWeight` | `_morph.SetWeight((int)target, clamped)` |
| `ApplyWeights` | `_morph.WeightUpdated()` |
| `DebugBlink` / `OnDebugBlinkReset` | BlinkBoth 1 then 0 |
| `DebugMorphStep` / `ResetAllWeights` | F11: one index at 1, or all 0 |

Search: no other `SetWeight` / `WeightUpdated`. Phase 3 moves the Helix calls into `PresenceAnimator` only. F9/F11 become animator debug overrides. `PresenceView.SetWeight` / `ApplyWeights` go away.

### 5. `ZolaDisplayState`

`Changed` is `Action?`, raised from `Recompute()` when the record differs. `Recompute` runs from `UpdateWindowFacts`, which `ApplyVoiceChrome` calls on the UI thread (`VoiceController.StateChanged` → `Dispatch` → `DispatcherQueue.TryEnqueue`). Animator can subscribe to `_display.Changed` and read `_display.Current.PresenceMode` with **no change** to `ZolaDisplayState.cs`.

### 6. `FirstSentenceLatencySeconds` and mouth onset

- **Where:** `VoiceController.cs` line 43, `private const double FirstSentenceLatencySeconds = 3.3`.
- **Readable as is:** no. Exact one-line change: `private const` → `internal const`.
- **What it measures (`P2-D15`):** TTS startup / first-sentence cost on the simulated playback clock. `OnTurnStarted` sets `_estimatedSpeechEnd = now + 3.3s` and `SetSpeaking(true)` in the same call when `ClockEligible` (Voice mode and tts on). Deltas extend the end; follow-up waits until that estimate plus margin. It is not an audio-device timestamp (`P2-D01`).

**Trace (voice turn 2026-09-28, 58 words):**

| Event | Timestamp |
|---|---|
| HUD `mode=Thinking` (submit / `_streaming`) | `09:13:00.293` |
| Timeline `start=` / `OnTurnStarted` / `mode=Speaking` | `09:13:00.309` |
| `message.complete` / `complete=` / HUD `voice="Speaking"` | `09:13:03.305` |
| `SPEAKING` + 3.3 s (mouth onset) | `09:13:03.609` |
| Timeline `estimatedEnd=` | `09:13:28.809` |
| First-audio / ffplay | **not observable in the client** |

Latency is **not** spent before `SPEAKING`. `SPEAKING` starts at `message.start`, 16 ms after Thinking. `SPEAKING` + `FirstSentenceLatencySeconds` is the right audible-onset estimate with signals the client already has. Not BLOCKED.

### 7. Reduced motion

Track 4: one `UISettings _uiSettings = new()` on `MainWindow`. Dock fade and notice fade read `_uiSettings.AnimationsEnabled` at the moment of the fade (snap if false). There is **no** `AnimationsEnabledChanged` subscription yet.

Animator reuses that same instance (constructor/property from `MainWindow`), and subscribes to `AnimationsEnabledChanged` so a live toggle snaps channels on the next tick (KC9). No second `UISettings`.

### 8. Debug keys (after P3-LOOK inventory)

| Key | Hook |
|---|---|
| Ctrl+Shift+F9 | debug blink |
| Ctrl+Shift+F10 | scene reload |
| Ctrl+Shift+F11 | morph step |
| Ctrl+Shift+F12 | look JSON reload |

Free: F1–F8. Propose:

| Key | Hook |
|---|---|
| Ctrl+Shift+F6 | write `presence-life.defaults.json` |
| Ctrl+Shift+F7 | life reload (`presence-life.json`) |
| Ctrl+Shift+F8 | forced mode cycle (Idle → Listening → Thinking → Speaking → Alert → Dormant → off) |

### 9. Blink closure (F11 index 2 at 1.0)

Crops from the approved unlit look, F11 step 2 @ 1.0 (P3-LOOK A15; copied to this folder; looked at this phase):

- `P3-LIFE_blink_both.png` — both lids closed, no sclera gap, no lid intersection.
- `P3-LIFE_blink_left.png` / `P3-LIFE_blink_right.png` — her-left / her-right only (viewer-right / viewer-left), for the mix keys.

`Blink both` alone is enough. Not BLOCKED.

### 10. Approved raw frame (G-STILL-FRAME)

- File: `zola-architecture/lore/prompts/progress/P3-LOOK_approved_raw.png` (1280×800 client area).
- Look fingerprint (DEBUG): `4392a2e0d851dc1e962c4ac5bfedf837e51c1645ed18d8bb044388fe346e83d8`.
- Capture: `GetClientRect` + `ClientToScreen`, window's real client bounds on its monitor, no crop/scale for the full frame. Bust compare: crop `(500, 90, 280, 400)`, max-delta 0 vs the approved raw (clock/session id ignored on the full frame).
- Settled and presented: wait until every channel reports settled (epsilon snap, multiplier exactly 1.0) **and** Helix `OnRendered` has fired for that commit (log both: `P3-LIFE: settled` then `P3-LIFE: presented`). Capture only after the presented log. Never one frame early.

### 10b. Key surface vs KC10

JSON groups use `MorphTarget` and `PresenceMode` names. Particles wait for Phase 7.

| Group | Keys | Count |
|---|---|---|
| `blink` | global: `closeMs`, `openMs`, `mixBlinkLeft`, `mixBlinkRight`, `mixBlinkBoth`, `asymmetryChance`, `asymmetryRatio`; per mode ×6: `enabled`, `intervalMinMs`, `intervalMaxMs`, `depth`, `lidRest` | 7 + 30 = **37** |
| `expression` | per mode, every owned index: 3–14 except `SPEAKING` 3–7 | 12×5 + 5 = **65** |
| `brightness` | per mode: `multiplier`, `pulseAmplitude`, `pulsePeriodMs` | **18** |
| `transition` | `eyesDelayMs`, `brightnessDelayMs`, `expressionDelayMs`, `expressionEaseMs`, `expressionCurve`, `brightnessEaseMs`, `brightnessCurve`, `lidEaseMs`, `lidCurve` | **9** |
| `mouth` | 16 scalars (onset, step, closure, jaw, bands, viseme chances) + per index 8–14: `rest`, `stiffness`, `damping` | 16 + 21 = **37** |
| `engine` | `tickIntervalMs`, `weightEpsilon`, `multiplierEpsilon`; DEBUG `randomSeed` | **4** DEBUG / **3** Release |
| **Total (no particles)** | | **170** DEBUG / **169** Release |

KC10 misses (add so they are not literals):

| Key | Default | Why |
|---|---|---|
| `blink.curve` | `linear` | KC2 close/open are linear |
| `engine.springSubstepMs` | `4` | KC3 integrate ≤ 4 ms |

`FirstSentenceLatencySeconds` stays on `VoiceController`, not in the life file.

### 11. Flags (none BLOCK Phase 3)

- Clear invert vs multiplier (item 3): handle when brightness leaves 1.0.
- `FirstSentenceLatencySeconds` is `private`: one-line `internal const` in Phase 3.
- Particle fill `#C4A882` is not a token; `#E8DDD0` is `ZolaTextPrimary`. Phase 7 adds a token for `#C4A882`.
- `ROADMAP.md` still says Phase 3 is not started (G-LORE-SCOPE: no edit).
- Architecture §3/§5/§25 still describe breathing, saccade, and chest glow; `P3-D22` drops them. Plan wins.

## Phase 3 — Animator Skeleton — COMPLETE

Skeleton is in: `PresenceLife` (full KC10 + `blink.curve` + `engine.springSubstepMs`), controller stubs, `PresenceAnimator` (composition, tick, pause/resume, rebind, fallback no-op, epsilon snap, F9/F11, F6/F7/F8), tone-map multiplier, PresenceView host (one Helix `SetWeight` in the animator), MainWindow wiring (`AnimationsEnabledChanged` on the existing `UISettings`, F6–F8), VoiceController `FirstSentenceLatencySeconds` `internal const`.

`BrightnessController` eases the configured per-mode multiplier over `transition.brightnessEaseMs` / `brightnessCurve` (no pulse). Weights stay 0 at rest. Tick never starts at rest.

### Phase 3-D2 — tone-map composites the token field (amends P3-D19/P3-D20, background only)

Developer approved Option D after rejecting A/B/C. Scene clear A=0; bust writes A=1; `AcesTonemap` outputs `lerp(ZolaBackground, toneMapped(rgb), sceneAlpha)` with output A=1. CPU invert removed.

**`#080808` source:** `ZolaBackground` token only (`Themes/ZolaTokens.xaml`). Pushed as `PostEffectToneMap.TokenBackground` → shader `Color.rgb`. Last-resort `_tokenBackground` fallback `FromArgb(255,8,8,8)` comments that it mirrors the token. `PresenceLook.DisplayBlackByte` and `AcesA`–`AcesE` (and `ByteMin`/`ByteMax`) deleted.

**fxc (once, installed SDK only):**
`"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe" /T ps_5_0 /E main /Fo AcesTonemap.cso AcesTonemap.hlsl`

| | SHA-256 | bytes |
|---|---|---|
| Old CSO | `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3` | 1948 |
| New CSO | `89aa36150afc317544377d8b4b7235ea7b70f19da540cebe3ca5acefc3c298c8` | 2024 |

csproj `EmbeddedResource` line unchanged.

**Look defaults fingerprint (DEBUG):** still `4392a2e0d851dc1e962c4ac5bfedf837e51c1645ed18d8bb044388fe346e83d8` (old = new). Invert constants were never JSON keys; F12 key set is unchanged (`camera*` / `look*` / `fov` / `toneMapGain` / `mipLodBias` / DEBUG `toneMapForceFail`). F12 with that set logged `look applied fingerprint=4392a2e0…`.

**Step 0 scene-alpha dump (deleted before any commit):** staging readback of the ping-pong scene target at 1280×800. Logged `P3-LIFE: scene-alpha size=1280x800 bust=1 hair=1 edge=0 field=0` (bust centre 640,290; hair tip 568,90; silhouette neighbour 567,90; field 60,500). No fractional alpha. Dump code removed from `PostEffectToneMap.cs`.

**Fail-closed:** `toneMapForceFail=true` → `P3-LOOK: tone map unavailable — shader bytecode missing`. Viewport clear is opaque `_tokenBackground`. Four field samples `#080808` A=255. Bust still draws (face 77,43,14 without ACES). HUD still paints.

### G-STILL-FRAME after D2

Reference: `P3-LIFE_reference_raw.png` (1280×800, IDLE at rest, dock hidden). Compare against `P3-LOOK_approved_raw.png` using its field mask (`#070707` → must be `#080808`; every other pixel max delta 0).

Clock text excluded, named **TimeText** bounds `(1142, 110, 42, 35)` (to 1183,144). **SessionText** bounds `(24, 684, 140, 22)` (to 163,705) — measured from the footer session line in `P3-LIFE_reference_raw.png` (glyph band 25–127 × 689–698, padded so `SESSION —` and an 8-character id both sit inside). Bust-covered pixels vs approved: **max 0**. Four field samples `(60,500)`, `(1180,420)`, `(220,620)`, `(1080,220)`: all **`#080808`**.

From here on, G-STILL-FRAME means: bust-covered pixels max delta 0 against `P3-LIFE_reference_raw.png`, plus ≥4 field samples exactly `#080808`, excluding **TimeText** and **SessionText**.

### Multiplier sweep (Idle.multiplier via F7; look gain 4.4)

Field samples exactly `#080808` at every value. Face (640,290) scales. Crops: `P3-LIFE_d2_crop_m0.50.png`, `P3-LIFE_d2_crop_m1.60.png`.

| Multiplier | Face 640,290 | Field |
|---|---|---|
| 0.50 | 134,62,12 | `#080808` |
| 0.75 | 163,85,19 | `#080808` |
| 0.85 | 172,93,22 | `#080808` |
| 1.00 | 182,104,25 | `#080808` |
| 1.10 | 188,110,28 | `#080808` |
| 1.15 | 191,113,29 | `#080808` |
| 1.60 | 208,137,39 | `#080808` |

Mid-ease 1.00 → 0.50 (`brightnessEaseMs` 600, `easeInOut`): field `#080808` at 150 / 300 / 450 ms; face 181,102,25 → 173,94,22 → 166,87,20.

### Verify checklist

- [x] Defaults file every key. F6 `wrote defaults keys=173`. Groups: blink 38, expression 65, brightness 18, transition 9, mouth 38, engine 5 DEBUG (4 Release). Total **173 DEBUG / 172 Release**.
- [x] Defaults copied to `presence-life.json` apply with fingerprint `dd90e06b8fa371087e92611790b75cf429519e2968f8364989a752343f1c04ef` (same on restore).
- [x] D2 reference: field mask `#070707`→`#080808`; bust-covered max 0 vs approved; four field samples `#080808`. Saved `P3-LIFE_reference_raw.png`.
- [x] Multiplier sweep 0.50 / 0.75 / 0.85 / 1.00 / 1.10 / 1.15 / 1.60: field `#080808`. Crops at 0.50 and 1.60.
- [x] Mid-ease ≥3 frames: field `#080808` in each.
- [x] Fail-closed: opaque `#080808`, she renders, HUD paints. F12 restore fingerprint `4392a2e0…`.
- [x] Static GPU 60 s avg **0.0011** max **0.0669**. Last `tick started` was during the ease; none during the GPU window. Tick stopped at rest.
- [x] F11 `debug morph 0 BlinkLeft` then Neutral 15. Helix `_morph.SetWeight` only in `PresenceAnimator.SetWeight`. `PresenceView` has no `SetWeight` / `ApplyWeights`.
- [x] F10: one `import started`, one `load coalesced`, `P3-LIFE: rebound`. Bust max delta 0.
- [x] GLB rename: `presence unavailable — GLB missing`, no exception, `tick-started-count=0`. Restored; rebound.
- [x] Life reload: valid fingerprint; missing `engine.tickIntervalMs` rejected by name; `closeMs` 999999 rejected `out of range`.
- [x] F8 Idle→Listening→Thinking→Speaking→Alert→Dormant→off. HUD `VoiceStateText` stayed IDLE; display log `mode=Idle` unchanged.
- [x] Minimize `paused (minimized)` / restore `resumed (minimized)`.
- [x] `dotnet build … -r win-x64` Debug and Release: 0 warnings.

### Key reference (tuning map)

Ranges: weights/chances `0–1`; ms `0–120000` except onset `-10000–10000`, pulse period `1–120000`, tick `1–1000`, spring substep `1–16`; multiplier `0–8`; pulse amp `0–2`; stiffness `1–20000`; damping `0.01–20`; epsilon `0–1`; scale `0–2`; seed `0–int.Max`; curves `linear` / `easeOut` / `easeInOut`.

**blink** (38)

| Key | Default | What |
|---|---|---|
| `closeMs` / `openMs` | 120 / 180 | Lid close / open duration |
| `curve` | linear | Close/open easing |
| `mixBlinkLeft` / `Right` / `Both` | 0 / 0 / 1 | Mix into the three blink morphs |
| `asymmetryChance` / `asymmetryRatio` | 0 / 0.85 | One-lid blinks |
| `{Mode}.enabled` | true except Dormant false | Blinks on/off |
| `{Mode}.intervalMinMs` / `MaxMs` | 3000–8000; Thinking 2000–4500 | Time between blinks |
| `{Mode}.depth` | 1; Thinking 0.4 | How far the lids go |
| `{Mode}.lidRest` | 0; Dormant 0.3 | Resting lid pose |

**expression** (65) — per mode, owned morphs (3–14 except Speaking 3–7). Default 0 except Listening `BrowRaise` 0.4; Thinking `BrowFurrow` 0.15; Alert `WideAlertEyes` 0.9, `BrowRaise` 0.6, `NostrilFlare` 0.4, `WideEE` 0.4.

**brightness** (18)

| Key | Default | What |
|---|---|---|
| `Idle.multiplier` | 1.0 | Rest gain scale |
| `Listening` / `Thinking` / `Speaking` / `Alert` / `Dormant` | 1.1 / 0.75 / 1.0 / 1.6 / 0.5 | Mode gain scale |
| `{Mode}.pulseAmplitude` | 0; Speaking 0.15 | Sinusoid on multiplier |
| `{Mode}.pulsePeriodMs` | 1200 | Pulse period |

**transition** (10): `eyesDelayMs` 0, `brightnessDelayMs` 450, `expressionDelayMs` 850, `expressionEaseMs` 300 `easeOut`, `brightnessEaseMs` 600 `easeInOut`, `lidEaseMs` 600 `easeInOut`, `speakingHoldsThinkingUntilOnset` true.

**mouth** (38): onset 0, step 90–140, closureChance 0.2, level 0.25–1, jawBase 0.1, jawRange 0.25, midScale 0.25, bandLowMax 0.2, bandMidMax 0.6, midOpenScale 0.15, wideEeScale 0.6, roundOo 0/0, teeth 0.15/0.25. Per index 8–14: rest 0; Jaw stiffness/damping 400/1; OpenAH, MidOpenEhUh, ClosedMBP 200/1; RoundOOW, WideEE, TeethFV 1500/0.5.

**engine**: `tickIntervalMs` 16, `weightEpsilon` 0.0005, `multiplierEpsilon` 0.0005, `springSubstepMs` 4, DEBUG `randomSeed` 0.

## Tuning log

| Round | Fingerprint | What changed | Developer feedback (verbatim) |
|---|---|---|---|
| 1 | `90a0223815781ca88a6e08280d95970d1cd85ad50d01a991fcc557a7d5dd0a08` | Proposed speaking-only tick 33 ms; not applied (would need a new key). Speaking GPU 16 vs 33 recorded. | *(no decision yet)* |
| 2 | `6090f8ad338c8187d75fd7ce3e28df2078989c350e88b2e19283637c556bdeea` | `mouth.mouthOnsetOffsetMs` 0 → **-3000** | "Lips aren't moving until about 3 seconds after voice starts. Sometimes the lips don't stop moving until about 5 seconds after speech has completed." |
| 3 | `3efe033cd1baa0634ee5673ff5674f2383b60bab972713098f878dc413d5786a` | `mouth.mouthOnsetOffsetMs` -3000 → **-1500** (onset ≈ SPEAKING+1.8 s). Stop still needs scope. | "Now speech starts as soon as I hit enter in the text box. No audio has started. Also, the ending still continues for about 4 seconds now." |

## GPU table

| Condition | Avg % | Max % | Notes |
|---|---|---|---|
| Idle | 0.0011 | 0.0669 | 60 s, 1 s, sum of `GPU Engine(pid_24252*)\Utilization Percentage`. Tick stopped. D2 composite. |
| Idle (blinks on) | 2.4014 | 13.3320 | 60 s, 1 s, sum of pid GPU Engine instances. 11 blinks. Phase 4. |
| Idle (blinks + particles) | 4.7430 | 15.2416 | Phase 7 timer path (historical; particles dropped). |
| Idle (blinks, particles dropped) | 2.2725 | 12.7560 | Phase 7 drop verify, 60 s. At pre-particle level. |
| Dormant | 0.0005 | 0.0315 | 60 s at rest, lids 0.30, tick stopped. |
| Transitions | | | |
| Speaking | 34.1884 | 38.5253 | Phase 5, 60 s forced speaking after onset (mouth + pulse), tick 16. Exempt. |
| Speaking (tick 16) | 35.5249 | 40.1462 | Phase 6 round 1, pid 16696, 60 s. |
| Speaking (tick 33) | 33.5560 | 36.3785 | Phase 6 round 1, global `engine.tickIntervalMs` 33 (proxy). |
| Minimized | 0.0000 | 0.0000 | Phase 7, 15 s while minimized (particles paused). |
| Locked | | | |

## Discrepancies or flags

Phase 3 is **COMPLETE**. Option D (Phase 3-D2) composites the `ZolaBackground` token in `AcesTonemap` so the field is exact `#080808` at any gain or multiplier. Invert removed. Scene-alpha dump logged 1,1,0,0 then deleted.

Key count after Phase 5b was **177 DEBUG / 176 Release**. Phase 6 Round 1 adds `mouth.<JawOpen…TeethFV>.gain` (×7), `mouth.releaseStiffnessScale`, and `engine.speakingTickIntervalMs` → **186 DEBUG / 185 Release**. Defaults fingerprint `9b89fc9c23e5b5d3747f6c4aff0e9453a3b15383ca722e78877afef31f1ddb12`. `mouth.mouthOnsetOffsetMs` remains “delay after detected playback” (range ±300 ms; effective delay clamped ≥ 0; default **0**).

`ROADMAP.md` still says Phase 3 is not started (G-LORE-SCOPE: no edit).

## Phase 4 — Eyes, Expression, Brightness, Stagger, Dormant — COMPLETE

Controllers and animator: irregular blinks (same `DispatcherQueueTimer`, long one-shot to the next due, 16 ms while closing/opening), thinking half-blinks, dormant lids at rest 0.30 with blinks off, per-mode expression ease, brightness ease plus Speaking pulse, stagger 0 / 450 / 850 (bypassed when reduced), reduced motion live via the existing `UISettings`. Mouth stays the Phase 3 stub.

### Invert-only deletion (search confirmation)

Grep of `PresenceLook.cs` and `PresenceView.cs`: **0 references** to `DisplayBlackByte`, `AcesA`–`AcesE`, and every other invert-only constant or method. Client C# is also 0. `AcesA`–`AcesE` / `AcesFilmic` / `SrgbToLinear` remain only in `AcesTonemap.hlsl` as the tone-map curve (not invert).

Removed from **`PresenceLook.cs`:** `DisplayBlackByte`, `AcesA`, `AcesB`, `AcesC`, `AcesD`, `AcesE`, `ByteMin`, `ByteMax`.

Removed from **`PresenceView.cs`:** `ApplyToneMappedClear`, `PickDisplayedBlackClear`, `InverseAcesFilmic`, `AcesFilmic`, `SrgbToLinear` / `LinearToSrgb` (and the 1-channel helpers), `UnitToByte`, `FoldedExposure`, `EffectiveToneMapGain`.

### G-STILL-FRAME named exclusions (from here on)

| Name | Bounds (x, y, w, h) | Inclusive to |
|---|---|---|
| TimeText | `(1142, 110, 42, 35)` | 1183,144 |
| SessionText | `(24, 684, 140, 22)` | 163,705 |

Idle at rest vs `P3-LIFE_reference_raw.png`: bust crop `(500, 90, 280, 400)` **max 0**; outside the two rects **diffs 0**; four field samples **`#080808`**. Captures: `P3-LIFE_p4_Idle_raw.png` / `_crop.png`.

### Verify checklist

- [x] **Blink log (60 s IDLE):** 11 blinks. Logged `intervalMs` 3160–7782, all inside 3000–8000. Start-to-start deltas match the logged interval within timer jitter (e.g. 5047 logged / 5063 wall). Close ~123–140 ms vs 120; open ~186–202 ms vs 180 (± one to two 16 ms ticks — log is the first tick after elapsed ≥ duration).
- [x] **Forced THINKING:** intervals 2279, 2554, 3003, 3026, 3532, 4336 (all 2000–4500). `blink closed weight=0.400000006 peak=0.400000006` (not 1.0). Furrow 0.15, multiplier 0.75.
- [x] **Each forced mode settled** (raw 1280×800 + bust crop + logged weights/multiplier). Speaking is pulse-only (never settled; crop taken during pulse). Field samples `#080808` in every capture.

  | Mode | Weights (0–14) | Multiplier | Files |
  |---|---|---|---|
  | Idle | all 0 | 1 | `P3-LIFE_p4_Idle_*` G-STILL-FRAME max 0 |
  | Listening | BrowRaise 0.4 | 1.1 | `P3-LIFE_p4_Listening_*` |
  | Thinking | BrowFurrow 0.15 | 0.75 | `P3-LIFE_p4_Thinking_*` |
  | Speaking | (pulse; mouth Phase 5) | ~1 ± 0.15 | `P3-LIFE_p4_Speaking_*` |
  | Alert | WideAlertEyes 0.9, BrowRaise 0.6, NostrilFlare 0.4, WideEE 0.4 | 1.6 | `P3-LIFE_p4_Alert_*` |
  | Dormant | BlinkBoth 0.30 | 0.5 | `P3-LIFE_p4_Dormant_*` |

- [x] **Stagger:** Idle→Listening eyes t=0, brightness t=462, expression t=851. Mid-stagger Listening→Thinking at ~200–540 ms: `stagger restart` from current values (no jump); new eyes/brightness/expression at 0 / 478 / 854.
- [x] **DORMANT at rest:** lids 0.30, no blinks after settle, `tick stopped`, GPU 60 s avg **0.0005** max **0.0315**.
- [x] **Non-Android keys:** Listening `SquintEyes` 0.3 + `mixBlinkLeft`/`Right` 1 / `mixBlinkBoth` 0. Settled `weights=0,0,0,0.300000012,0,0.400000006,…`. Blink closed `mix=1,1,0` (indices 0/1, not Both). Crops `P3-LIFE_p4_nonandroid_*` plus a blink-closed crop. Restored defaults fingerprint `dd90e06b8fa371087e92611790b75cf429519e2968f8364989a752343f1c04ef`.
- [x] **Seeded blinks:** `randomSeed` 42, two 60 s runs after F7. Interval sequences identical (12/12): 6341, 3704, 3627, 5614, 3842, 4313, 6622, 5565, 3868, 6807, 4173, 4286.
- [x] **Real modes (no forced):** One voice turn, submit `hi` while still Listening. Display `Listening` (11:19:55.673) → `Thinking` (11:19:57.436) → `Speaking` (11:19:57.467 / voice label 11:19:59.837) → `Idle` (11:20:05.079). Presence Listening settled BrowRaise 0.4, then `stagger restart` Thinking→Speaking from current values, then Idle. No `forced mode` in that window. Driven by `ZolaDisplayState`.
- [x] **Idle GPU 60 s with blinks:** avg **2.4014** max **13.3320** (≤ 10% avg). Between blinks the 16 ms repeating tick is not running: after `blink open` / `settled` / `presented` at 11:07:36.705 the next presence line is `blink start` at 11:07:41.452 (4.75 s log gap, no `presented` flood). The same timer stays as a one-shot to the next due; `tick stopped` is logged only when nothing is scheduled (Dormant 11:04:56.738).
- [x] **Reduced motion live (KC9, row by row):** Windows Settings → Accessibility → Animation effects toggled via UIA (`SystemSettings_Accessibility_IsAnimationsEnabled_ToggleSwitch`). Log `reduced on blink=animated expression=snap brightness=snap pulse=off lids=snap stagger=bypass` then `reduced off` with the inverse.
  - Blink animated: `blink start intervalMs=7212` at 11:20:12.873 while reduced on.
  - Expression snap / brightness snap / stagger bypass: Idle→Listening all **t=0**, settled immediately at multiplier 1.1 (11:13:31.918).
  - Pulse off: forced Speaking while reduced **settled** at 11:20:21.664 (`multiplier=1`); pulse-on Speaking never settles.
  - Dormant lids snap: settleMs=223 vs ease 600 (11:20:22.510, BlinkBoth 0.30).
  - Speaking mouth / particles: Phase 5 / Phase 7, not this phase.
- [x] `dotnet build … -r win-x64` Debug and Release: **0 warnings**.

Phase 4 accepted. The `settleMs=223` row above is corrected in the follow-up.


## Phase 4 follow-up — reduced-motion Dormant lids `settleMs=223`

Logging artifact, not lid ease. `p4-gaps.ps1` computed `$ms = ($dsStamp - $tDorm).TotalMilliseconds` from the script's `Get-Date` (taken before `Send-Accel`) against the client log stamp. The presence log is one tick (0.70 ms). No `BlinkController` change.

```
2026-09-28T11:20:22.5093655-07:00 P3-LIFE: forced mode Dormant
2026-09-28T11:20:22.5095986-07:00 P3-LIFE: stagger eyes t=0
2026-09-28T11:20:22.5097783-07:00 P3-LIFE: stagger brightness t=0
2026-09-28T11:20:22.5099366-07:00 P3-LIFE: stagger expression t=0
2026-09-28T11:20:22.5100676-07:00 P3-LIFE: settled mode=Dormant weights=0,0,0.300000012,0,0,0,0,0,0,0,0,0,0,0,0 multiplier=0.5
```

## Phase 5 — Speaking Mouth — COMPLETE

`MouthController` (KC3): synthetic L every 90–140 ms, viseme band blend, closed-form springs (substep 4 ms), onset at `FirstSentenceLatencySeconds` + `mouthOnsetOffsetMs`, reduced-motion rest, pause/resume from current weights. Expression owns 3–7 while speaking; mouth owns 8–14 until ease-out handover.

### Developer-approved amendment to P3-D14 / P3-D22

When `SPEAKING` begins and the onset estimate is still in the future, the animator keeps presenting the THINKING targets: expression, brightness multiplier, THINKING blink interval and depth, and no pulse. If the previous look was not THINKING, it transitions to THINKING with the normal stagger. At the onset estimate it runs the normal SPEAKING transition (stagger, brightness 1.0, pulse on, mouth on). `ZolaDisplayState` and `PresenceMode` are unchanged — animator timing only, like the mouth delay. Resume, reduced motion, and handover rules apply; in reduced motion the switch at onset is instant. If SPEAKING ends or the mode changes before onset, the pending hold is cancelled and the new mode runs normally. Forced-mode SPEAKING uses the same hold. Key: `transition.speakingHoldsThinkingUntilOnset` (true).

### Verify checklist

- [x] **Forced SPEAKING:** hold `onsetMs=3300` at 11:32:56.937, settled `mode=Speaking look=Thinking` furrow 0.15 multiplier 0.75, onset 11:33:00.253, then 22 mouth steps. `STEP_MS min=109 max=156` (max is one 16 ms tick past 140). Three crops: `P3-LIFE_p5_speak1/2/3_raw.png` + `_crop.png`.
- [x] **Real spoken turn:** typed `hi` in Voice mode. Hold 11:38:56.976 → settled look=Thinking 11:38:58.083 → onset 11:39:00.277 (~3.30 s) → 16 mouth steps → display Idle 11:39:05.886, settled Idle weights all 0. Bust crop vs `P3-LIFE_reference_raw.png` **max 0**. Captures `P3-LIFE_p5_idle_after_raw.png` / `_crop.png`. Full-frame outside TimeText/SessionText had 14 px at 1274,795–1279,799 after the dock hid (not the bust).
- [x] **Frame-rate independence:** `randomSeed` 42. Tick 16 ms vs 33 ms L prefix **23/23** identical (16 ms then ran longer: 28 steps vs 23). Script `SEED_COMPARE n=25 match=24` was polluted by `Write-Output` inside the collector; the log is the source.
- [x] **Handover (KC4):** F8 is forward-only, so Alert→Speaking is not adjacent. Verified adjacent **Speaking→Alert**: 64 `wideEe=` samples, maxDelta 0.0846, first 0.0946 last 0.2515 (ease toward Alert 0.4, no jump). Mode change during ease-out (Alert→Dormant): 6 `wideEe=` lines, no jump.
- [x] **Pause during SPEAKING:** restore-while-speaking (forced): last step 11:33:46.753, `paused (minimized)` 11:33:46.778 `tick stopped`, `resumed` 11:33:51.797, fresh `mouth step L=0.996711314` from current weights (jaw still ~0.238), `onsetLines=1` (no replayed onset). Minimize longer than the reply (real `hi`): onset 11:41:47.295, paused 11:41:47.791, display Idle 11:41:51.183 while minimized, restore 11:42:07.804 settled `mode=Listening` (follow-up capture), `stepsTotal=4` = steps before, `onsetLines=1`.
- [x] **Barge-in / Cancel before onset:** Cancel 480 ms after hold (11:38:54.130 → 11:38:54.610 `speaking hold cancelled reason=mode`). Display Speaking→Idle. Settled Idle all 0. No `speaking onset`.
- [x] **Speaking GPU 60 s:** avg **34.1884** max **38.5253** (pid 23668, 1 s, sum of GPU Engine instances). Exempt.
- [x] **Reduced motion:** `mouthSteps=0`. Hold still `look=Thinking` multiplier 0.75; at onset settled `mode=Speaking` multiplier **1** (pulse off) 11:33:34.147 → 11:33:34.149.
- [x] **Hold extras (developer):** real Voice turn held THINKING from SPEAKING start to onset, then SPEAKING stagger + mouth; barge-in before onset (above); Text-mode `hi` 11:39:27.564 Thinking → 11:39:29.333 Idle, `voice="Text mode"`, `TEXT_HOLD_LINES 0 TEXT_ONSET_LINES 0`.
- [x] `dotnet build … -r win-x64` Debug and Release: **0 warnings**. F6 `wrote defaults keys=174`.

Phase 5 accepted. Follow-ups and Phase 6 round 1 below.

## Phase 5 follow-ups (before Phase 6)

### 1. Handover expression → mouth (index 13)

Via life reload set `expression.Thinking.WideEE` = 0.3 (SPEAKING holds THINKING until onset). Forced SPEAKING. Defaults restored afterwards; fingerprint matched.

```
2026-09-28T12:41:22.3459001-07:00 P3-LIFE: settled mode=Speaking look=Thinking weights=…,0.300000012,… multiplier=0.75
LAST_EXPR_OWNED_13 0.300000012
2026-09-28T12:41:25.1032962-07:00 P3-LIFE: speaking onset
FIRST_MOUTH_OWNED_13 0.300000012
HANDOVER_DELTA 0.000000
POST 12:41:25.108 wideEe=0.300000012
POST 12:41:25.135 wideEe=0.207123086
POST 12:41:25.165 wideEe=0.0974621996
POST 12:41:25.196 wideEe=0.0640921891
POST 12:41:25.212 wideEe=0.0690585971
POST 12:41:25.244 wideEe=0.0698247179
```

First mouth-owned value equals last expression-owned (Adopt). Restored fingerprint `90a0223815781ca88a6e08280d95970d1cd85ad50d01a991fcc557a7d5dd0a08` MATCH. Also logs `wideEe=` while `_mode == Speaking` (hold), not only Alert/mouth-owned.

### 2. Spring settle times at tick 16 vs 33 (±5%)

Same seed 42, first step L=0.793306291, WideEE asymptote L×0.25×0.6 = 0.1190. Closed-form springs, `springSubstepMs` 4.

| Metric | tick 16 | tick 33 | Δ |
|---|---|---|---|
| Interpolated 90% rise | **56.0 ms** | **61.2 ms** | **9.3%** |
| Observed timer gap (avg) | 31.2 ms | 46.6 ms | (dispatcher jitter over the set interval) |
| First \|err\|≤0.01 cross | 60 ms | 140 ms | misleading — 33 ms samples the overshoot before re-entering the band |

L step sequence already matched 23/23 in Phase 5. Rise-to-90% is the fair settle compare; it is slightly outside ±5% under wall-clock timer jitter. Physics uses 4 ms substeps of the closed form, so the continuous trajectory is not tick-sliced.

## Phase 6 — Tuning Rounds

### Round 1 — mouth shape + end-tail + speaking tick (applied)

**Developer feedback (screen recording):** mouth reads as a wide rectangular slot (opens too wide); ending runs long (~0.3 s active after audio, then ~0.6 s settle).

#### Before tuning — end-tail (`GetState`)

Polled `IAudioSessionControl::GetState` on owned ffplay sessions. Per segment logged Active→Inactive and session disappear.

| Metric | n | min | median | max |
|---|---|---|---|---|
| Inactive → session gone (`inactiveLeadMs`) | 4 | 64 ms | 93 ms | 124 ms |

Inactive consistently precedes disappear by ~1–2 polls @ 20 Hz. **Adopted:** `SegmentStopped` now fires on owned session **Inactive** (ownership rules unchanged). Saving ≈ **64–124 ms** (median ~93 ms) vs waiting for session removal.

#### Missing keys (G-KEYS) — added

| Key | Default | Role |
|---|---|---|
| `mouth.<8–14>.gain` | 1.0 | output multiplier after mapping (per morph) |
| `mouth.releaseStiffnessScale` | 1.0 | multiplies spring stiffness of 8–14 while targets head to rest after SegmentStopped / release |
| `engine.speakingTickIntervalMs` | 16 | tick while mouth or speaking pulse is changing; idle blinks keep `tickIntervalMs` 16 |

Key count **186 DEBUG / 185 Release**.

#### Calibration sheet

Each mouth morph (JawOpen…TeethFV) alone at 0.25 / 0.5 / 1.0 via life reload (`expression.Idle.*`, Idle blink off). Raw 1:1 bust crops (280×400) tiled 7×3, labelled. **21/21 unique** crops. Sheet: `P3-LIFE_p6_mouth_calibration.png`. Defaults restored, then Round 1 re-applied.

#### Speaking tick 16 vs 33 (real TTS, 15 s GPU Engine sum-of-pid)

| `speakingTickIntervalMs` | Avg % | Max % |
|---|---|---|
| 16 | 11.93 | 34.93 |
| 33 | 30.30 | 40.17 |

15 s windows are sensitive to Armed/hold vs Active mouth; earlier Phase 6 proxy (global tick 60 s) was 35.5% @16 vs 33.6% @33. Split key is implemented; Round 1 sets speaking tick to **33**.

#### Applied config (from defaults)

| Key | Value |
|---|---|
| `mouth.jawBase` | 0.04 |
| `mouth.jawRange` | 0.14 (max jaw 0.18) |
| `mouth.wideEeScale` | 0.2 (from 0.6) |
| `mouth.teethWeight` | 0.12 (from 0.25) |
| `mouth.ClosedMBP.gain` | 0.6 |
| `mouth.roundOoChance` | 0.15 |
| `mouth.roundOoWeight` | 0.2 |
| `mouth.releaseStiffnessScale` | 2.5 |
| `engine.speakingTickIntervalMs` | 33 |

**Fingerprint:** `13e2c2c2d00cac8986f486a74ed3f889c7b08eda1cc5ae1cebc9f597d99276d8`

| Round | Fingerprint | What changed | Developer feedback (verbatim) |
|---|---|---|---|
| 1 (tick-only note) | `90a02238…dd0a08` | Proposed speaking-only tick; not applied then | *(historical)* |
| 1 (mouth) | `13e2c2c2…9276d8` | End-tail Inactive stop; gain/releaseScale/speakingTick keys; jaw/wideEe/teeth/oo/ClosedMBP.gain/releaseScale/tick33 | "start and end timing are now correct. The mouth still opens too wide, both vertically and horizontally." |

### Round 2 — narrower open (candidate B applied)

**Developer feedback (verbatim):** start/end timing correct; mouth still opens too wide vertically and horizontally. Calibration: jaw 0.25 already clear; open shapes (except Round OO) span full lip width → reduce opens, lean on Round OO, lower level range.

#### Candidates (from Round 1; only listed keys change)

| | A moderate | B subtle | C minimal |
|---|---|---|---|
| jawBase / jawRange | 0.02 / 0.10 | **0.02 / 0.07** | 0.01 / 0.05 |
| OpenAH / MidOpenEhUh / TeethFV gain | 0.6 / 0.6 / 0.5 | **0.4 / 0.4 / 0.3** | 0.3 / 0.3 / 0.0 |
| ClosedMBP.gain | 0.6 | **0.6** | 0.5 |
| wideEeScale | 0.1 | **0.0** | 0.0 |
| roundOoChance / Weight | 0.25 / 0.3 | **0.3 / 0.35** | 0.35 / 0.4 |
| levelMin / levelMax | 0.15 / 0.8 | **0.1 / 0.7** | 0.1 / 0.6 |

#### Comparison sheet

Composed settled display weights (mapping × gain) at rest, Lmin, Lmid, Lmax, closure, roundOO for A/B/C. Nose→chin crops `(540,280,240,230)` 1:1 tiled, labelled with candidate, pose, and 8–14 weights. **15/18 unique** (3 rests identical; A/B closure both ClosedMBP display 0.6). Sheet: `P3-LIFE_p6_r2_candidates.png`.

#### Applied live: candidate B

**Fingerprint:** `15f68abb8db8028f43aa598da66146de79d258ea70d6a255350ff126eda0107e`

| Round | Fingerprint | What changed | Developer feedback |
|---|---|---|---|
| 2 | `15f68abb…0107e` | Candidate B (narrower jaw/opens, Round OO lean, lower L range) | "B is the base; no grimace, reads as speech." |

### Round 3 — syllable rate + quieter pulse (from B)

**Developer feedback (verbatim):** B is the base; no grimace, reads as speech.

**Applied (complete config from B; only these keys change):**

| Key | Was (B) | Now |
|---|---|---|
| `mouth.stepMinMs` / `stepMaxMs` | 90 / 140 | **150 / 250** |
| `brightness.Speaking.pulseAmplitude` | 0.15 | **0.05** |

**Fingerprint:** `ca72eb1a7b26cdd6459e8754f1c016b48c320b552a2c39e88b3367c63841ef91`

| Round | Fingerprint | What changed | Developer feedback |
|---|---|---|---|
| 3 | `ca72eb1a…41ef91` | step 150–250; Speaking pulseAmplitude 0.05 | "the slower steps read better; the mouth is now slightly too subtle." |

### Round 4 — slightly more open (from Round 3)

**Developer feedback (verbatim):** slower steps read better; mouth slightly too subtle. Keep everything that narrows the shape (wideEeScale 0, Round OO, ClosedMBP).

**Applied (complete config from Round 3; only these keys change):**

| Key | Was (R3) | Now |
|---|---|---|
| `mouth.jawRange` | 0.07 | **0.10** |
| `mouth.levelMax` | 0.7 | **0.85** |
| `mouth.OpenAH.gain` / `MidOpenEhUh.gain` | 0.4 / 0.4 | **0.5 / 0.5** |

**Fingerprint:** `c4ca56fea2202391d7f14da2e35d787537803e14d8905a326a293521f3f3ffc3`

**Note (no code change):** latest recording — mouth motion ~1 s after audible speech on the final sentence. Suspected cause: trailing silence inside the sentence MP3 (ffplay session still Active). Segment logs from replies after Round 3 (`08:07`–`08:08`):

| Segment window | Duration |
|---|---|
| 08:07:01.070 → 08:07:19.628 | **18558 ms** |
| 08:07:24.471 → 08:07:27.345 | **2874 ms** |
| 08:08:07.093 → 08:08:26.815 (last bout’s last segment) | **19722 ms** |

SegmentStopped follows `GetState` Inactive; any trailing silence while the session stays Active will keep the mouth generating until Inactive.

| Round | Fingerprint | What changed | Developer feedback |
|---|---|---|---|
| 4 | `c4ca56fe…f3ffc3` | jawRange 0.10; levelMax 0.85; OpenAH/Mid gain 0.5 | **Approved mouth baseline.** No Round 5. |

**Approved mouth baseline:** Round 4 live config (`c4ca56fe…f3ffc3`). Mouth shape/rate tuning closed.

**Modes (developer judgement):** Idle, Listening, Thinking, Speaking, and Dormant approved as they are. Alert was startled → Round 5; then approved as attentive.

### Round 5 — Alert only (from Round 4 / approved modes)

**Developer feedback (verbatim):** Idle, Listening, Thinking, Speaking and Dormant approved as they are. Alert reads as startled (mouth parted, eyes too wide, too bright).

**Applied (complete config from current; only ALERT keys change):**

| Key | Was | Now |
|---|---|---|
| `expression.Alert.WideAlertEyes` | 0.9 | **0.35** |
| `expression.Alert.BrowRaise` | 0.6 | **0.3** |
| `expression.Alert.NostrilFlare` | 0.4 | **0.1** |
| `expression.Alert.WideEE` | 0.4 | **0** (mouth closed) |
| `brightness.Alert.multiplier` | 1.6 | **1.25** |

**Fingerprint:** `ef3c2c6eb9894a4fb83d473ba69bfba6e88e44f4ab4da69d88c3585510189777`

**Note:** ALERT has no Windows trigger yet (`S25`); these are placeholder-safe values, to be revisited when a real alert source exists.

| Round | Fingerprint | What changed | Developer feedback |
|---|---|---|---|
| 5 | `ef3c2c6e…189777` | Alert eyes/brows/flare/WideEE/brightness down | "Alert reads as attentive, not startled." |

**Life approved (developer, verbatim):** blinks and expressions feel natural in every mode, the mouth follows her voice with restrained, natural movement, and she stays composed. Alert reads as attentive, not startled.

**Approved life fingerprint:** `ef3c2c6eb9894a4fb83d473ba69bfba6e88e44f4ab4da69d88c3585510189777` (Round 4 mouth + Round 5 Alert). Live config is the baseline.

```
=======
PHASE 6 COMPLETE — LIFE APPROVED
Awaiting "proceed to" Phase 7 (Particle Field).
=======
```

## Phase 7 — Particle Field — DROPPED

**Life defaults baked** (Phase 6 closeout): Round 4 mouth + Round 5 Alert written into `PresenceLife.CreateDefault()`.

### Developer decision (verbatim)

> I'm almost thinking that we don't need the particles. Zola's image speaks for itself.

**Particles dropped.** Removed `PresenceParticleLayer`, the MainWindow host, all `ZolaParticle*` / `ZolaLayerParticles` / `ZolaPresenceAmber` tokens, `AttachParticles` wiring, and every `particles.*` life key. No dead switches remain.

### P3-D22 float amendment — superseded

The Phase 7 float-design amendment to `P3-D22` (rise/sway/wrap Composition Forever; Stopwatch/UI timer flagged as KC11 deviation) is **superseded** by the drop decision above. It is historical only.

### Composition finding — note for S30

On this WinUI + Helix SharpDX surface, Composition Forever keyframe animations do not advance. Recorded for `S30` (any future animated decoration / backdrop):

| API | Result |
|---|---|
| `AnimationController.Progress` setter (phase seek) | Access-violates; kills the process |
| Negative `DelayTime` | `ArgumentException: The parameter is incorrect` |
| `CompositionPropertySet.StartAnimation("t", Forever)` | Starts; `t` never advances |
| Forever on ElementVisual `Translation` / `Offset` / `Opacity`, and on `ShapeVisual.Offset` via `SetElementChildVisual` | `StartAnimation` succeeds; controller `PlaybackRate=1`; **`Progress` stays 0**; property unchanged |

### Post-drop verify

| Check | Result |
|---|---|
| `dotnet build … -r win-x64` Debug + Release | **0 warnings** |
| Key count | **186 DEBUG** (`wrote defaults keys=186`); Release **185** (no `engine.randomSeed`) |
| Defaults fingerprint | `ef3c2c6eb9894a4fb83d473ba69bfba6e88e44f4ab4da69d88c3585510189777` (matches Phase 6 life-approved) |
| `defaultsHasParticles` | **False** |
| G-STILL-FRAME vs `P3-LIFE_reference_raw.png` | Bust crop **max 0**; four field samples **`#080808`**. Captures `P3-LIFE_drop_idle_raw.png` / `_crop.png`. Outside named exclusions: 24 px at x=1140–1141 (1 px left of TimeText box) + 36 px dock foot — same class as prior HUD/dock residuals, not bust. |
| Idle GPU 60 s (blinks, no particles) | **avg 2.2725** / max 12.7560 — at pre-particle level (Phase 4 was 2.4014) |

```
=======
PHASE 7 COMPLETE — PARTICLES DROPPED
=======
```

### Round 1 verify (historical — timer path, superseded by drop)

| Check | Result |
|---|---|
| Captures 900×640, 1280×800, maximized | `P3-LIFE_p7_900x640.png`, `_1280x800.png`, `_maximized.png` |
| Idle GPU 60 s (blinks + particles) | **avg 4.74%** / max 15.24% — under 10% |

**Defaults fingerprint (timer-era particles):** `c17820163e215b0977d6422d67c7589ea9ac66e7943954f64b02e72fa229a176`

### Deferred (S17 — lore closeout)

**Mouth cannot see in-sentence pauses or trailing silence in a sentence MP3.** Session presence only knows when ffplay’s audio session is Active; the synthetic level keeps stepping while the session stays Active. Effects: (1) mouth stays evenly busy through commas and breaths; (2) motion continues ~1 s after audible speech ends (segment logs after Round 3: last bout’s last segment **19722 ms**). Both need a real per-sentence audio signal — a client-side scan of the MP3 ffplay is playing (envelope and silences), or Hermes playback lifecycle events — replacing the synthetic level. **Deferred past Phase 3**; record into `S17` at lore closeout.

### Round 1 (historical) — proposed: speaking-only tick 33 ms

**Proposal:** `tickIntervalMs` 33 during SPEAKING only; idle blinks stay at 16. Reason: speaking mouth+pulse dominates GPU; idle should stay near the static floor between blinks.

**Scope note (resolved in Round 1 mouth pass):** split implemented as `engine.speakingTickIntervalMs` (see above).

**Speaking GPU (global tick as proxy), 60 s, pid 16696:**

| Setting | Avg % | Max % |
|---|---|---|
| `tickIntervalMs` 16 | 35.5249 | 40.1462 |
| `tickIntervalMs` 33 | 33.5560 | 36.3785 |

Δ avg ≈ −2.0 pp (−5.5%).

### Round 2 — mouth onset / release vs audible speech

**Developer feedback (verbatim):** "Lips aren't moving until about 3 seconds after voice starts. Sometimes the lips don't stop moving until about 5 seconds after speech has completed."

**Diagnosis — late start:** Mouth (and the THINKING hold) wait `FirstSentenceLatencySeconds` (3.3 s) + `mouthOnsetOffsetMs` (was 0) after `SPEAKING`. If audible TTS is earlier than that estimate, lips lag by about that gap. No audio timestamp on Windows (`P2-D01`).

**Diagnosis — late stop:** Mouth steps while `PresenceMode == SPEAKING`. `Speaking` clears only when the follow-up timer fires: remaining estimate after `message.complete` **plus `FollowUpMarginSeconds` (3.0)** in `VoiceController`. Spring ease-out after `Release` is ~0.2 s, not seconds. So overrun is the speech clock / follow-up margin, not the mouth springs. No life key releases the mouth before `Speaking` clears; fixing that needs a VoiceController change or a new release-offset / decouple (scope).

**Applied this round:** `mouth.mouthOnsetOffsetMs` = **-3000** → onset delay 300 ms after `SPEAKING` (hold still applies for 300 ms). Fingerprint `6090f8ad338c8187d75fd7ce3e28df2078989c350e88b2e19283637c556bdeea`.

**Please try a voice turn** and say whether lips now track the start of audible speech. If still late/early, we can nudge the offset (e.g. -2800 / -3300). For the stop, say whether you want a scope amendment (e.g. clear mouth at estimated end without the 3 s follow-up margin, or a `mouthReleaseOffsetMs`).

### Round 3 — onset too early; stop still late

**Developer feedback (verbatim):** "Now speech starts as soon as I hit enter in the text box. No audio has started. Also, the ending still continues for about 4 seconds now."

**-3000 was too early:** effective onset became SPEAKING+0.3 s, so lips moved on Enter / stream start before TTS audio.

**Applied this round:** `mouth.mouthOnsetOffsetMs` = **-1500** → onset ≈ **SPEAKING + 1.8 s** (between the too-late 3.3 s and the too-early 0.3 s). Fingerprint `3efe033cd1baa0634ee5673ff5674f2383b60bab972713098f878dc413d5786a`.

**Late stop (unchanged):** Mouth follows `Speaking`. That flag stays true until estimated speech end **+ `FollowUpMarginSeconds` (3.0)**. ~4 s after audible end ≈ that margin plus a bit of estimate error. Springs are not the cause.

**Scope amendment needed for stop (not applied):** e.g. expose `EstimatedSpeechEnd` from `VoiceController` and `Release` the mouth when that time is reached, while leaving `Speaking` / follow-up mic window as today — or reduce/remove the 3 s margin from the mouth only. Reply `approve mouth release at estimate` (or similar) to authorize that VoiceController + animator change.

**Superseded by Phase 5b:** mouth onset/release now follow Hermes TTS playback presence (`TtsPlaybackMonitor`). Round 2/3 `mouthOnsetOffsetMs` estimate nudges (−3000 / −1500) are obsolete; defaults restored to **0** (delay after detected playback). Mouth shape tuning resumes in Phase 6 after 5b.

## Phase 5b — TtsPlaybackMonitor — COMPLETE

### Developer decisions (binding)

- **P2-D01 amendment (display only):** client may observe presence of audio sessions belonging to Hermes’s own player processes. No audio data, no level, no capture.
- **Peak meter dropped:** QI of the peak IID succeeds; reported peak is always 0. Recorded as an S17 note (not used).
- **S17 partially resolved.** Session presence gates onset/release; synthetic level still cannot see in-sentence pauses or trailing MP3 silence. One deferred item for lore closeout: see Phase 6 “Deferred (S17 — lore closeout)”.
- **Scope:** `Presence/TtsPlaybackMonitor.cs` + `Presence/AudioSessionInterop.cs`; `MainWindow.xaml.cs` wiring; `PresenceAnimator` / `MouthController`; new `PresenceLife` keys; `HermesProcessManager` at most a one-line read-only serve identity accessor. No `VoiceController` / `ZolaDisplayState` / `PresenceMode` / Hermes / RPC changes.

### Contract

| Member | Role |
|---|---|
| `IsAvailable` | init OK and ownership roots established |
| `IsSegmentActive` | owned ffplay session exists right now |
| `IsBoutActive` | bridged speaking stretch (gaps &lt; `releaseDebounceMs`) |
| Events | `SegmentStarted` / `SegmentStopped` / `BoutStarted` / `BoutStopped` |
| `StartMonitoring` / `StopMonitoring` | only while SPEAKING pipeline armed → released |

Poll at `mouth.playbackPollHz` (default **20**), off UI thread; events marshalled to UI. No `IAudioSessionNotification`. Ownership: `HermesProcessManager` launched PID (authoritative); command-line discovery only if client did not launch serve (logged). Parent-chain ≤ 2 hops; create-time ≥ serve-start; never match a Hermes the client is not connected to.

### Mouth state machine

`Idle → Armed → Active ⇄ Releasing → Idle` (`MouthSpeakPhase`; concept **SpeakingPlaybackArmed** — THINKING look until bout; `PresenceMode` untouched).

- SPEAKING begins → Armed (`StartMonitoring`); THINKING look; no mouth motion.
- First `BoutStarted` + `mouthOnsetOffsetMs` (default 0, ± ±300, clamp ≥ 0 elapsed) → Active: SPEAKING transition, brightness pulse, mouth.
- While Active: new synthetic targets only while `IsSegmentActive`. Segment stop → generate off, springs settle to rest. Segment start → resume from current weights.
- `BoutStopped` with SPEAKING still on → mouth at rest; `mouth.speakingPauseShowsThinking` (default **false**) keeps SPEAKING look or returns to armed THINKING.
- Armed may last indefinitely (“no audio yet” is never a failure).
- Forced release (cancel bridge): Cancel / `voice.interrupted`, SPEAKING clear, pause, scene reload/loss, monitor disposal.
- Brightness pulse stays on SPEAKING look from Active; not gated per segment.
- Fail-closed: monitor available with ownership → else today’s estimate (`SPEAKING` + `FirstSentenceLatencySeconds` + offset), logged once → SPEAKING clear always releases.

### Keys (defaults)

| Key | Default | Notes |
|---|---|---|
| `mouth.playbackPollHz` | 20 | 1–60 |
| `mouth.releaseDebounceMs` | 450 | bout release debounce |
| `mouth.speakingPauseShowsThinking` | false | mid-bout pause look |
| `mouth.mouthOnsetOffsetMs` | 0 | delay after detected playback; ±300 |

### Verify evidence

**3 multi-sentence turns** (post bout→Active tick fix, `2026-09-28T15:22`–`15:23`):

| Metric | n | min | median | max |
|---|---|---|---|---|
| Mouth Active − first owned segment start | 3 | **1 ms** | **2 ms** | **2 ms** |
| Mouth generate-off − segment stop | 6 | **0 ms** | **1 ms** | **1 ms** |
| Armed hold until first segment | 3 | 2361 ms | 3176 ms | 3176 ms |

Target “within one poll + one tick” (50 ms @ 20 Hz + ~16 ms): **pass**. Bridged inter-sentence gaps logged (~61–124 ms). Zero mouth generate / onset events before first owned segment (`preAudioMouthEvents=0`).

**Slow / Armed hold:** Armed THINKING for 2.3–3.2 s on multi turns; longer tool-style holds supported by design (no timeout).

**Mid-reply pause:** `speakingPauseShowsThinking=false` → `speaking pause keeps speaking look` (multi turns). `=true` + debug segment override → `speaking pause shows thinking` (`15:32:13`).

**Barge-in:** mid-sentence new submit → `speakingPlaybackArmed cancelled` immediate (`BARGE cancelled=True`).

**Foreign ffplay:** `playback ownership reject foreign ffplay` while owned Hermes TTS also playing (`15:40:46+`; once-per-episode after spam fix).

**Serve restart:** ownership root `21268` → **`23060`** (`source=HermesProcessManager`); no stale match after client relaunch.

**Forced monitor-init failure (Ctrl+Shift+F3):** `playback monitor fallback estimate (unavailable)` once; `speakingPlaybackArmed estimate onsetMs=3300`.

**Monitor stop:** only after SPEAKING clear / release (`playback monitor stop` paired with mode cancel). CPU while polling ~20–27% of one core over 5 s sample (poll thread + UI). Idle GPU after settle: avg **2.65%** / max 13.3% over 5 s (A7-style sum-of-pid GPU Engine) — not a resting tick loop; still-frame bust unchanged.

**G-STILL-FRAME** after speaking (look reload + life defaults, dock hidden): bust vs `P3-LIFE_reference_raw.png` **max 0**; four field samples `#080808`. Captures `P3-LIFE_p5b_idle_after_raw.png` / `_crop.png`. Outside exclusions: 32 edge px at bottom (dock hide), not bust.

**Build:** Debug `-r win-x64` **0 warnings**. Phase 5b window: **0** presence WARN/Exception lines.

### S17 notes (closed enough for 5b)

1. Peak meter: QI ok, peak always 0 → dropped.
2. **Deferred past Phase 3 (lore closeout):** mouth cannot see in-sentence pauses or trailing silence in a sentence MP3; needs per-sentence envelope scan or Hermes lifecycle events to replace the synthetic level. Full text under Phase 6 “Deferred (S17 — lore closeout)”.
3. Managed `IAudioSessionNotification` AV’d in probes → poll-only authority.

### Files

- `Presence/TtsPlaybackMonitor.cs`, `Presence/AudioSessionInterop.cs` (new)
- `Presence/PresenceAnimator.cs`, `MouthController.cs`, `PresenceLife.cs`, `PresenceView.cs`
- `MainWindow.xaml.cs` (wire + DEBUG F3/F4)
- `HermesProcessManager.cs` (`ServeProcessId` accessor only)

```
=======
PHASE 5b COMPLETE
Mouth tuning resumes in Phase 6 after this.
=======
```

## Phase 8 — Smoke Test — COMPLETE

Plan exit criteria (`PHASE3_BUILD_PLAN.md` Track 5 smoke). Particles are **dropped** (Phase 7); no particle checks.

### Pre-smoke (agent)

- [x] Particles removed; build Debug + Release **0 warnings**
- [x] Life fingerprint `ef3c2c6e…189777`; keys **186 DEBUG / 185 Release**
- [x] G-STILL-FRAME bust max 0; field `#080808`
- [x] Idle GPU 60 s avg **2.27%** (≤ 10%; at pre-particle level)

### HUMAN-RUN

**Developer (verbatim):** smoke test passed.

Checklist covered: 2-minute idle; "Hey Zola" + question (Listening / Thinking / Speaking); barge-in, Cancel, Text mode; kill serve → Dormant; reduced motion live; Phase 2 combined smoke + lock/unlock + sleep/wake; overall presence judgement.

### Proposed open question — S32 (for lore closeout)

**S32 — Voice active while Windows is locked (security/privacy)**

During smoke (lock/unlock), the developer observed that Zola responds to voice while Windows is at the lock screen. This is **pre-existing P2 behaviour** (the voice pipeline runs in Hermes), not caused by Track 5.

Options (not decided here):

1. Pause the wake word on lock.
2. Restrict replies while locked.
3. Keep deliberately.

File into `OPEN_QUESTIONS.md` at Phase 3 lore closeout (G-LORE-SCOPE: not this track).

```
=======
PHASE 8 COMPLETE — SMOKE PASSED
=======
```

## Closeout

- Tests: N/A (no automated suite).
- `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`: Debug + Release **0 warnings**, 0 errors (closeout).
- `hermes-agent` `git status` clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- No debug JSON, no `presence-life.json`, no new images under `windows-client/`. Progress PNGs stay under `zola-architecture/lore/prompts/progress/`.
- Packages unchanged from Track 4. No new NuGet packages.
- No lore file updates (G-LORE-SCOPE). Proposed `S32` recorded above for Phase 3 lore closeout; Composition Forever note for `S30` in Phase 7; deferred S17 mouth-envelope note in Phase 6.

### Life approved

Developer judgement (verbatim, Phase 6): blinks and expressions feel natural in every mode, the mouth follows her voice with restrained, natural movement, and she stays composed. Alert reads as attentive, not startled.

**Approved life fingerprint:** `ef3c2c6eb9894a4fb83d473ba69bfba6e88e44f4ab4da69d88c3585510189777` (Round 4 mouth + Round 5 Alert). Live config is the baseline baked into `PresenceLife.CreateDefault()`.

### Particles

**Dropped.** Developer (verbatim, Phase 7): "I'm almost thinking that we don't need the particles. Zola's image speaks for itself."

`PresenceParticleLayer`, host, tokens, and all `particles.*` keys removed. P3-D22 float amendment superseded.

### Key surface

| Config | Keys |
|---|---|
| DEBUG | **186** (`wrote defaults keys=186`; includes `engine.randomSeed`) |
| Release | **185** |

Every morph index per mode, blink, brightness, mouth, timing, spring, and engine key is exposed (KC10). Unused defaults are 0 / off.

### Final tuned values (named constants in `PresenceLife.cs`)

| Area | Defaults (summary) |
|---|---|
| Blink | close 120 / open 180 ms; interval 3000–8000; Thinking 2000–4500 half-blink depth 0.4; mix Both=1; Dormant lid rest 0.3 |
| Expression | Listening brow 0.4; Thinking furrow 0.15; Alert WideEyes 0.35 / BrowRaise 0.3 / NostrilFlare 0.1 / WideEE 0; ease 300 ms |
| Brightness | Idle 1.0 / Listening 1.1 / Thinking 0.75 / Speaking 1.0 / Alert 1.25 / Dormant 0.5; Speaking pulse amp 0.05 period 1200 ms; ease 600 ms; stagger eyes 0 / brightness 450 / expression 850 ms |
| Mouth | TTS session presence gate (`TtsPlaybackMonitor`); step 150–250 ms; jawBase 0.02 / jawRange 0.10; levelMax 0.85; OpenAH/MidOpen gains 0.5; ClosedMBP 0.6; TeethFV 0.3; releaseStiffnessScale 2.5; poll 20 Hz; releaseDebounce 450 ms |
| Engine | tick 16 ms idle / **33 ms speaking**; spring substep 4 ms; weight/multiplier ε 0.0005 |
| Particles | **dropped** |

### Figures

| Measure | Value |
|---|---|
| G-STILL-FRAME (IDLE rest vs `P3-LIFE_reference_raw.png`) | bust crop **max 0**; four field samples `#080808` |
| Idle GPU 60 s (blinks, no particles) | avg **2.2725%** / max 12.7560 — ≤ 10% (`P3-D09`) |
| Speaking GPU 60 s (tick 33 ms) | avg ~33.6% (recorded Phase 6) |
| Defaults fingerprint | `ef3c2c6e…189777` |

### Background invert (Phase 3-D2 amendment)

Scene clear A=0; bust A=1; `AcesTonemap` `lerp(ZolaBackground, toneMapped(rgb), sceneAlpha)` output A=1. CPU invert removed. Bust look unchanged from P3-LOOK.

### Mouth / S17

Session presence gates onset/release (`TtsPlaybackMonitor` + `AudioSessionInterop`). Peak meter dropped (always 0). **Deferred past Phase 3:** mouth cannot see in-sentence pauses or trailing silence in a sentence MP3 — needs envelope scan or Hermes lifecycle events (record into `S17` at lore closeout).

### Final file list

New:
- `windows-client/Zola.Client/Presence/PresenceAnimator.cs`
- `windows-client/Zola.Client/Presence/PresenceLife.cs`
- `windows-client/Zola.Client/Presence/TtsPlaybackMonitor.cs`
- `windows-client/Zola.Client/Presence/AudioSessionInterop.cs`
- `windows-client/Zola.Client/Presence/Controllers/BlinkController.cs`
- `windows-client/Zola.Client/Presence/Controllers/BrightnessController.cs`
- `windows-client/Zola.Client/Presence/Controllers/ExpressionController.cs`
- `windows-client/Zola.Client/Presence/Controllers/ModeTransitionCoordinator.cs`
- `windows-client/Zola.Client/Presence/Controllers/MouthController.cs`
- `zola-architecture/lore/prompts/progress/P3-LIFE_Progress.md`
- progress PNGs `P3-LIFE_*.png` (reference, tuning, Phase 5b, drop verify)

Modified:
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `windows-client/Zola.Client/HermesProcessManager.cs` (`ServeProcessId` accessor only)
- `windows-client/Zola.Client/VoiceController.cs` (`FirstSentenceLatencySeconds` accessibility)
- `windows-client/Zola.Client/Presence/PostEffectToneMap.cs` (gain multiplier + invert lerp)
- `windows-client/Zola.Client/Presence/PresenceView.cs` (host animator; invert removal)
- `windows-client/Zola.Client/Presence/PresenceLook.cs` (invert-only constants removed)
- `windows-client/Zola.Client/Presence/Shaders/AcesTonemap.hlsl` / `.cso` (scene-alpha lerp)

Deleted (never shipped on `main`; dropped before commit):
- `PresenceParticleLayer.cs` and all particle host / token / life-key surface

Already on `main` (Phase 1): plan v1.7 at `819c51b0fab8b5dafb8256fa02a558236191db7a`.

### Exit criteria (`PHASE3_BUILD_PLAN.md` Track 5 v1.7)

- ✅ MET — `PresenceAnimator` is the only `SetWeight` / gain-multiplier writer; no node transforms.
- ✅ MET — Controllers read `ZolaDisplayState` only; `FirstSentenceLatencySeconds` is the one read-only VoiceController constant.
- ✅ MET — IDLE at rest pixel-identical to reference (bust max 0; field `#080808`).
- ✅ MET — Full key surface (186 DEBUG / 185 Release); key reference in progress.
- ✅ MET — Handover continuity ALERT → SPEAKING → ALERT (WideEE Adopt; Phase 5).
- ✅ MET — Pause during SPEAKING then resume: nothing replayed (animator pause/resume).
- ✅ MET — Mode transitions follow Audit 04 §1b in smoke (developer-passed).
- ✅ MET — Idle GPU ≤ 10% (avg 2.27% over 60 s with blinks; particles dropped).
- ✅ MET — Minimized / occluded / locked / DORMANT at rest: smoke covered lock/unlock and sleep/wake.
- ✅ MET — Reduced motion toggled live (smoke).
- ✅ MET — Final blink/expression/brightness/mouth values recorded; **particles dropped** with developer approval verbatim.
- ✅ MET — `hermes-agent` clean at `345cd2b0`.
- ✅ MET — `dotnet build … -r win-x64` 0 warnings (Debug + Release).
- ✅ MET — HUMAN-RUN smoke passed (developer: "smoke test passed").

### Proposed for Phase 3 lore closeout (not filed here)

| ID | Note |
|---|---|
| S17 | Update: session presence gates mouth; deferred envelope / trailing-silence signal |
| S30 | Composition Forever does not advance on this WinUI + Helix surface (Phase 7 table) |
| S32 | Voice active while Windows is locked — pause wake / restrict replies / keep deliberately |

### SHAs

- Plan v1.7 commit on `main`: `819c51b0fab8b5dafb8256fa02a558236191db7a`
- Implementation commit: `8e4045f377fda3e995b354802562ffe53f6f62e7`
- Merge SHA on `main`: `8a00f6e87c68d28231d9ba1fc9ec1f4d29de1f40`

