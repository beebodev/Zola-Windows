# SPEECH-PRE Audit 09 — Tests, scenarios, refactor risk

---

## 1. Existing automated coverage

### Client checks (`windows-client/Zola.Client.Checks`)

Suite via `tools/test-gate/Run-TestGate.ps1` → `Suites.psd1` runs `dotnet run --project Zola.Client.Checks` (Release).

| Area | File | Approx. named checks (from `Speech`/`Code` registrations) |
|------|------|-------------------------------------------------------------|
| Proactive / echo / playback stamps | `SpeechChecks.cs` (~985 lines) | gate reasons; snapshot/turn claim; reviewed draft; final check before tts; one-at-a-time; quiet hours; stale snapshot; echo haystack + 2 s tail; phrase sets; HUD; stamps clear reservation; push-to-talk during tts → uncertain; crash after dispatch; stamp before/during speech_started; stamp during playback; later reply does not refresh echo tail; voice unavailable; … |
| Code-read / Zira isolation | `CodeChecks.cs` (~736 lines) | Code-read latch, logging hygiene, collision with voice paths |
| Supervision / lifecycle | `SupervisionChecks.cs` | Capture/epoch interactions |
| Dev/monitor | `DevChecks.cs` | Monitor-related fixtures |

Exact xUnit `[Fact]` count: N/A — custom `Speech("name", …)` runner. **EVIDENCE:** `SpeechChecks.cs` registers dozens of speech/proactive checks; admission/follow-up heavily covered in Checks + Program fixtures.

### Plugin tests

| Suite | File | Notes |
|-------|------|-------|
| `zola_tts` | `hermes-plugins/zola_tts/tests/test_deepgram_tts.py` | Fake key; Pandora model accept/refuse; no network |
| P9 speak | `hermes-plugins/zola_workspace/tests/test_p9_speak.py` | Proactive store/speech contracts |
| P8 send | `hermes-plugins/zola_workspace/tests/test_p8_send.py` | Passphrase `"Approved. Send it."` |

### Hermes pin tests

`tests/tools/test_voice_mode.py`, `test_tts_streaming.py` exist upstream; not Zola acceptance (prior audits).

### `Run-TestGate.ps1`

PROC1-GATE one-command gate: FAIL/INFRA/floors; imports `Suites.psd1` / `floors.json`; Hermes python from `Get-HermesRoot`; refuses promote evidence when overrides used.

---

## 2. Scenarios the track could affect

From Phase 1:

| Scenario | Affect? |
|----------|---------|
| SC-S51F-SM1 (wake/follow-up/clarify/no beeps) | **Yes** — core listen/speak |
| SC-S51F-EXP-BEEP | Keep beeps off |
| SC-S51F-SM2 / EXP-LOST | Failure UX while speech helper down |
| SC-PROC1-S1 | End-to-end voice |
| Privacy DEV* | Key/data roots if owner process |

### SB-01–SB-11 vs scenarios

Speech-baseline cases are **referenced** in `SCENARIO_LIBRARY` (PROC1-D11), not copied. **GAP:** no SC-* rows yet for each SB case (premature listening, clipped openings, paragraph pause, etc.). Track should add scenarios for: premature listening gone; opening word kept; mid-thought pause; exact EOS; BT first/last word (after Part G).

---

## 3. Likely-changed files — size / risk (PR-D06)

| File | Size | Lines | Responsibilities | Refactor-first? |
|------|------|-------|------------------|-----------------|
| `VoiceController.cs` | 173 KB | **4447** | Capture, follow-up, echo, wake, stop, estimates, clarify wire | **Yes — candidate** (PR-D06). Complexity is multi-authority in one type; speech track will rewire listen release + Hermes RPC assumptions |
| `MainWindow.xaml.cs` | 126 KB | 3333 | Transcript submit, clarify, tool HUD, turn finalize | **Maybe** — touch points limited; prefer thin seams over full refactor |
| `TtsPlaybackMonitor.cs` | 21 KB | 743 | ffplay bout ownership | Retire or demote for listen; mouth may keep |
| `CaptureLifecycle.cs` | 31 KB | 874 | Capture state machine | Extend for owner signals; complexity medium |
| `TranscriptAdmission.cs` | 5 KB | 165 | Single admit authority | Keep; small — **not** refactor-first |
| `ChatSocket.cs` | 44 KB | 1091 | Events | Add owner IPC elsewhere preferred |
| `ProactiveSpeechSession.cs` | 11 KB | 317 | Unprompted speak | Reroute speak to owner |
| `ProactiveDeliveryCoordinator.cs` | 17 KB | 597 | Claim/outcome | Outcome mapping |
| `SpeechEchoGuard.cs` | 2 KB | 90 | Proactive echo tail | May shrink if D7(a)/tail changed |

**SPEECHPRE-AUD-27 [RISK] HIGH** — `VoiceController.cs` (4447 lines) is the primary refactor-first candidate before or as wave-0 of the speech track (evidence: size + concentration of listen/speak/wake/follow-up authorities).

---

## 4. Tests the track would need (named, one line)

1. `Owner_SafeToListen_DoesNotOpenDuringDrain` — unit/offline: gate closed until drain+220 ms.
2. `Owner_PreRoll_NeverIncludesPlayback` — samples before `safe_to_listen` excluded.
3. `Admission_FromOwnerCapture_UsesSameDecide` — owner hand-off hits `TranscriptAdmission` once.
4. `HermesMicDisarmed_NoPortAudioOpen` — smoke: with owner armed, serve has no InputStream (scripted).
5. `VoiceTts_NotCalled_WhenOwnerSpeaks` — proactive/clarify use owner interface.
6. `ReplyId_DropsLateAudio` — cancel then late chunk ignored.
7. `Passphrase_UsesAdmittedText` — STT candidate ≠ submitted until admit (P8).
8. `CartesiaKey_GuardRows` — tools refuse secrets path (fake key).
9. `HelperDown_LostRequestOrFailClosed` — supervised restart latch; no dual Hermes mic.
10. **Scripted smoke only:** voice feel / Julia tone; timing median reply start; Bluetooth G1–G5 (Part G); wake “Hey Zola” under owner mic hold.
