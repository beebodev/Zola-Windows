# P3PRE Audit 04 — Windows Applicability Map

Re-read of `Zola_Presence_UI_Architecture.md` against Phase 2–4. K1: the GLB replaces the SVG. Android wave status is not a Windows score.

| § | Requirement | Windows + GLB status | Label | Evidence |
|---|---|---|---|---|
| 1 | Persistent entity presence | applies, different mechanism: one `BoneSkinMeshNode` in `Viewport3DX` | [GAP] | No presence renderer in `Zola.Client`. Spike renders the bust. |
| 2 | Static reconstruction from SVG | superseded by K1 | [MATCH] | K1. SVG file is not in this repo. |
| 3 | Procedural life: breath, lean, idle | applies, different mechanism: morph weights + node matrix | [GAP] | No breath or idle controller. Lean is a Y rotation (`P3PRE-AUD-20` framing). Chest-only breath is `P3PRE-AUD-16`. |
| 4 | State-down pipeline and `PresenceMode` | applies as written | [RISK] | `P3PRE-AUD-04`. Labels are derived in `ApplyVoiceChrome`, not in one adapter. |
| 5 | Blink, saccade, breath, mouth, expression, hair controllers | blink/jaw/brow: morphs. Saccade and hair: not achievable with current asset | [GAP] | `P3PRE-AUD-08`, `P3PRE-AUD-13`, `P3PRE-AUD-14`. |
| 6 | Four glow layers | not achievable with current asset as separate regions | [RISK] | One `EmissiveColor` on one Phong material (`P3PRE-AUD-16`, `P3PRE-AUD-21`). |
| 7 | Ambient state (particles, hair, eye glow, background pulse) | not achievable with current asset for hair/eyes-as-layers | [GAP] | No particle system. Eye glow is texels. |
| 8 | Staggered mode transitions | applies as written | [GAP] | No `PresenceMode` yet, so no stagger. |
| 9 | Eye system | blink and lid morphs apply. Drift does not. | [GAP] | `P3PRE-AUD-13`. Developer: blink works. |
| 10 | Mouth / visemes | morphs apply. Amplitude signal does not. | [GAP] | K5, `S17`. Targets exist (`P3PRE-AUD-08`). |
| 11 | Expression pose | partial morphs. No negative mouth curve, no eye softness. | [GAP] | `P3PRE-AUD-10`, `P3PRE-AUD-11`. |
| 12 | Hair energy | not achievable with current asset | [GAP] | `P3PRE-AUD-14`. |
| 13 | Pixel projection / hologram layers | not achievable as separate geometry | [GAP] | `P3PRE-AUD-15`. Pixels are in the textures. |
| 14 | Functional HUD | applies as written | [GAP] | No HUD. Sources are Phase 6. Hide elements with no state. |
| 15 | Contextual dock, text not the anchor | applies as written | [GAP] | `P3PRE-AUD-02`. Composer is permanent. |
| 16 | Context panels orbit the presence | applies as written | [GAP] | Sessions panel is a 300px column (`MainWindow.xaml` 49). |
| 17 | UI shows authoritative state | applies as written | [MATCH] | `P3PRE-AUD-03`. |
| 18 | One authority; UI does not reason | applies as written | [RISK] | `P3PRE-AUD-04`. |
| 19 | Visual restraint | applies as written | [GAP] | No heat signal on Windows to damp motion. |
| 20 | Desktop endpoint | applies, different mechanism: resizable WinUI window, not a phone canvas | [GAP] | `P3PRE-AUD-06`. Window 960×720, no minimum. |
| 21 | Layered package structure | applies, different mechanism: C# types, not Kotlin files | [GAP] | Nothing under a presence namespace. |
| 22 | Build waves | Android-only | [MATCH] | G-NO-CROSS-SCOPE. Not a Windows score. |
| 23 | Performance and reduced motion | applies, different mechanism: Helix/DirectX | [GAP] | See Q3 and Q5 below. |
| 24 | Cursor must read the SVG | superseded by K1 | [MATCH] | K1. |
| 25 | Validation | applies as written, with GLB as the still frame | [GAP] | Fidelity issue `P3PRE-AUD-18`. |

## 1. Where `PresenceMode` would be derived

`ApplyVoiceChrome` (`MainWindow.xaml.cs` 316–394) is the only place that turns facts into the voice-state label and the mic line. `VoiceController` owns the RPCs and `Resting` / `CanStartCapture`. A presence view that mapped `PresenceMode` by itself would be a second derivation (`P3PRE-AUD-04`).

Facts that live on the window and would have to be exposed or moved if one derivation served the label, the mic line, and the presence:

- `_streaming` (`MainWindow`)
- `_unreachable`
- `_switchInFlight`, `_historyPending`
- `_modeSwitching`
- `_sessionReady` (copied into `VoiceController.SessionReady` by `SetCaptureGate`)

Options, not a choice:

1. Move the priority in `ApplyVoiceChrome` into `VoiceController` (or a new type it owns) and have the window and the presence both read that result.
2. A `PresenceStateAdapter` that reads `VoiceController` plus the window fields above, and is the only writer of `PresenceMode`. The window stops computing labels from raw flags.
3. Leave the label in the window and have presence call the same method. That is still one method, but it stays UI-coupled.

## 1b. State-transition matrix

Doc modes used only as named: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ALERT`. No new mode is invented.

| State | Enter | Exit | Stuck? | PresenceMode |
|---|---|---|---|---|
| Wake armed | `VoiceController.ArmWakeAsync` after `SyncVoiceAndWakeAsync` | capture, turn, text mode, `BumpConnectionGeneration` | If `wake.start` never confirms, `WakeArmed` stays false and the mic line stays `Mic: off` (`ApplyVoiceChrome` 385–387). | `IDLE` |
| Wake detected | `ChatSocket` `wake.detected` → `OnWakeDetected` | `StartCaptureAsync` success, or ignored when `!Resting` (`HandleWakeDetectedAsync` 1459) | Ignored wakes log and return. A failed capture calls `RecoverWakeCaptureIfNeededAsync`. | `LISTENING` if a capture starts, else stays `IDLE` |
| Capture active | `voice.record` start sets `CaptureActive` (532) | `voice.status` idle (`OnVoiceStatus` 623–625) | If idle never arrives, `CaptureActive` stays true and the label stays `Listening`. | `LISTENING` |
| Transcribing | `voice.status` `transcribing` | idle or transcript | Same as capture: waits on `voice.status`. | `LISTENING` |
| Turn running | `message.start` / submit sets `_streaming` | `FinishTurn` | A missing `message.complete` leaves `_streaming` true (`Thinking`). Cancel calls `session.interrupt`. | `THINKING` |
| Speaking (estimate) | `OnTurnStarted` → `SetSpeaking(true)` when `ClockEligible` | follow-up timer fires `SetSpeaking(false)` (`OnFollowUpTimerAsync` 758) | If the timer is cancelled, `CancelFollowUp` also clears `Speaking` (788). | `SPEAKING` |
| Barge-in | `voice.interrupted` → `OnVoiceInterrupted` | status line; loop guard may call `EnterTextModeAsync` after 3 (743–748) | Count resets on complete, typed send, or mode change. | `LISTENING` if a new capture follows; otherwise `IDLE`. Not `ALERT`. |
| Follow-up capture | timer → `StartCaptureAsync` | transcript, idle, echo reopen, or `CancelFollowUp` | Failed `voice.record` calls `CancelFollowUp("follow-up-record-failed")` (513). | `LISTENING` |
| Follow-up idle / echo reopen | `OnVoiceStatus` idle with no transcript → `CancelFollowUp("follow-up-idle")`. Echo → `ReopenFollowUpAfterEchoAsync` | reopen limit `EchoReopenLimit` 3, or a real transcript | `CancelFollowUp` clears both follow-up flags (785–787). | `IDLE` after idle; `LISTENING` on reopen |
| Stop phrase | `OnVoiceTranscript` `IsStopPhrase` → `VoiceChatEnded`, `ResyncAfterStopAsync` | resync | A failed resync sets a status message only. | `IDLE` |
| Cancel | `OnCancelClick` → `session.interrupt` | `OnInterruptAcknowledged` → `FinishTurn("interrupted")` | Non-`interrupted` ack leaves the turn running and sets `StatusText` (449). | back to `IDLE` if the turn ends |
| Turn error | `message.complete` status `error` → `FinishTurn` | `_streaming` false, no follow-up (`OnTurnCompleted` else branch) | Does not stick. | `IDLE` |
| Socket reconnect | new `/api/ws` from new session or resume (`_switchInFlight`) | `SessionReady` | Mic line `Reconnecting voice…` while those flags are set (366–369). | `AMBIGUOUS` — no doc mode for reconnect |
| Serve killed | `ChatSocket.Fault` → `Unreachable` → `ShowUnreachable` | none in-session | Stays unreachable. Composer and mic stay disabled. | `NO MODE` |
| Unreachable | same | same | same | `NO MODE` |
| Session loading | `_historyPending` / `_switchInFlight` | resume dispatch or `finally` | `finally` clears `_switchInFlight` (824–827). | `AMBIGUOUS` |
| Text mode | `EnterTextModeAsync` or `MarkUnavailable` | `EnterVoiceModeAsync` | Stays until the user toggles, or voice is unavailable. | `NO MODE` — doc modes assume a presence, not a silent text fallback |
| Voice unavailable | `MarkUnavailable` forces `ModeText` | a later successful sync | Shown as `Voice unavailable`. | `NO MODE` |
| P2-D13 loop notice | 3× `voice.interrupted` → `EnterTextModeAsync` and `NoticeVoicePaused` | user returns to Voice | Does not auto-return. | `NO MODE` |

`ALERT` is not produced by any current Windows state. There is no threat, security, or urgency flag in the client.

## 2. `PresenceVisualState` fields

| Field | Windows signal today |
|---|---|
| `mode` | none. Would be derived as in Q1. |
| `speechAmplitude` | none. Client plays no audio (`P2-D01`). `Speaking` is a bool estimate. |
| `attentionConfidence` | none. |
| `cognitiveLoad` | none. |
| `environmentalNoise` | none. |
| `breathingRateHz` | none. Could be derived from mode once mode exists. |
| `glowIntensity` | none. |
| `manifestationDensity` | none. |
| `eyeLuminance` | none. |
| `attentionLean` | none. `Resting` is not a lean amount. |
| `pixelJitter` | none. |
| `mouthOpenness` | none. Viseme weights would be invented from `Speaking`. |
| `blinkSuppression` | none. Could be derived from mode. |
| `emotionalWarmth` | none. |
| `urgencySharpness` | none. |

## 3. Performance rules in Helix terms

| Doc rule | Windows reading | Measured? |
|---|---|---|
| Particle cap 40 | No particle system. Cap applies only if one is added in XAML, Composition, or Win2D. | No |
| Cache static paths | The GLB mesh is static GPU geometry. Morphs change a weight buffer, not a path rebuild. | Indirect: Cycle p95 16.85 ms |
| Scoped redraw | Helix lazy-renders until `WeightUpdated` or a matrix change. Static GPU sum ~0.1%. | Yes, Phase 4 |
| Blur radius constant | Not used. L1's cube painted the background; that is not a blur. | No |
| Offscreen glow at 75% | Not available as a Helix switch that was found. | No |
| Reduced motion | `UISettings.AnimationsEnabled` | Read once: true |
| 16 ms target | Cycle average 16.76 ms, p95 16.85 ms on Iris Xe | Yes |

## 4. Fonts

Name ID 13 (platform 3, UTF-16), all four files, same string: "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL". OFL 1.1 allows committing the files if the licence text ships with them. Install nothing.

Working `FontFamily` form: `<absolute path>\<file>.ttf#<family>` as in `Zola_P3PRE_Audit_03_HelixSpike.md` §10. `shots/fonts.png`.

## 5. Reduced motion

`Windows.UI.ViewManagement.UISettings.AnimationsEnabled` is the setting that was read (true). `UISettings.AnimationsEnabledChanged` exists on that type, so a running window can subscribe. The spike only read it at startup.

## 6. 2D elements outside the model

The reference shows particles, floor rings, corner brackets, dividers, the VU bar, and a warm radial glow. None of these are in the GLB.

| Mechanism | Fits | New package? |
|---|---|---|
| XAML shapes and brushes in the same `Grid` as the viewport | Overlay text already draws above the viewport. Brackets, dividers, and the VU bar fit here. | No. `Zola.Client.csproj` already has WinUI. |
| Composition visuals | Same process, no extra package. | No |
| Win2D | Particles and a radial glow are easier here. | Yes. Not in `Zola.Client.csproj`. Not installed for this audit. |

`Viewport3DX.BackgroundColor` with alpha 0 was tested over a magenta `RadialGradientBrush` ellipse (`shots/transparent.png`). The viewport stayed black. The gradient did not show through. A glow or floor ring behind the bust has to be drawn in the 3D scene, or the viewport clear has to be changed by some other means than this property. `P3PRE-AUD-25`.

## 7. Visual tokens

See `Zola_P3PRE_Audit_07_VisualTokens.md`.
