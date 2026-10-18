# VOICEPRE Audit 08 — Evidence reconciliation

Rechecked 2026-10-18 after Audits 01–07 were drafted. No application test was run.

## Scopes still stable

Overlay hashes match Audit 01. Nothing in the voice list changed during the write:

| File | Overlay SHA-256 prefix |
|---|---|
| `VoiceController.cs` | `0136876FF16DE9A6` |
| `ChatSocket.cs` | `B339E54B56FBE130` |
| `MainWindow.xaml.cs` | `E63317A2CF55A400` |
| `CaptureLifecycle.cs` | `D8B95D69E6E9DC0E` (same as committed) |
| `TranscriptAdmission.cs` | `BCCE33FA242E496E` (same) |
| `ClarifySpeech.cs` | `5F6D6760F2052B4A` (same) |
| `TtsPlaybackMonitor.cs` | `763178A261879FB3` |
| `SpeechEchoGuard.cs` | `8176EC4E5EEEF4BF` (committed absent) |
| `ProactiveDeliveryCoordinator.cs` | `210FFF3AC901257C` (absent) |
| `ProactiveSpeechSession.cs` | `2D94F6F23C2CDA30` (absent) |
| `speech.py` | `D4414DD9E59FB857` (absent) |
| `P9-SPEAK_Progress.md` | `BFB7E79C2936ED91` (absent) |
| `VOICE_CONFIG.md` | `0CACE932C857B57F` (same) |

Primary checkout still `p9-speak` at `03a3a1f`. Hermes still clean at `345cd2b`. Android still `zola-main` at `a139ccac`. Worktree `voicepre-audit` contains only this untracked audit directory.

The evidence stabilized. No version-dependent split was required.

## What is established

- Hermes owns the mic and the speaker. The client does not open them. The full-duplex listener is off when `barge_in` is false, and the documented profile value is false.
- `voice.record` has no pre-roll and beeps before it records. There is no capture id and no cancel RPC.
- `_fd_trip` does not look at a clarification, latches an interruption, and the current admission rules drop a transcript that has no Accepting owner.
- Echo control is a text rule with a 3-word floor, plus an uncommitted exact-phrase guard for proactive lines. The playback monitor sees ffplay presence, debounce 450 ms, not samples.
- Live TTS is the Deepgram command provider, Aura-2 Pandora, speed 0.95, one mp3 and one ffplay per sentence. Edge numbers are historical.
- Wake-free directed speech is specified in Master Plan §12 and not implemented. Android directedness gates proactive delivery, not incoming STT.
- P9 speech is uncommitted and mid-smoke. Its "capture active" deny conflicts with a mic that stays open.

## What is plausible and untested

- SYM-01 is the inter-sentence bout gap and/or the short-echo hole. The code can do both. `P9-STORE` saw the gap once after the provider switch. Brian's 2026-10-18 report does not identify which path.
- SYM-02 is the pre-beep / no-pre-roll hole. Other cuts (endpoint, device, late follow-up) are not ruled out.
- SYM-05 gaps are the per-file ffplay restart plus command latency. Size and how often he hears them are not measured on Aura-2.
- Windows AEC or WebRTC AEC3 might reject her voice if the owner has a render reference. This machine's endpoints were not queried for the AEC interface.

## What is not claimed

- A current reproduction of any symptom.
- A native-crash cause (`S51`).
- That latest upstream Hermes already contains the patch in option B.
- That enhancements are on, or that the USB audio device is the microphone.
- That P9-SPEAK passed.

## Leads

| Lead | Outcome | Evidence |
|---|---|---|
| LEAD-01 P5PRE-AUD-14, `_fd_trip` is not clarify-aware | Confirmed | `methods_voice.py` L219–246, re-read |
| LEAD-02 P5PRE-AUD-15, `voice.record` has no pre-roll | Confirmed | `hermes_cli/voice.py` L331–378 |
| LEAD-03 P5PRE-AUD-16, no plugin hook | Confirmed | Arm is `barge_in` plus two numbers only |
| LEAD-04 P5 feasibility NO | Partial | Still true for config and for a bare flag flip. It does not forbid a Hermes patch or a new audio owner. `P5-D08` remains the locked reading until amended. |
| LEAD-05 P7 closed "her speech became his turn" (S45) | Partial | The admission authority exists and blocks the old unbound path. SYM-01 says a path still gets through. The closeout is not a current proof. |
| LEAD-06 P9-STORE inter-sentence self-echo | Partial | One historical occurrence plus the 450 ms debounce still in code. Not re-run. |
| LEAD-07 Edge S-tts ≈ 2 s and EoS median 9534 ms | Historical | Provider is no longer Edge. |
| LEAD-08 P2-D16 Latitude setup | Partial | WMI still says Latitude 7430 and Windows 11 build 26200. Levels, enhancements, and the active endpoint were not read. A USB audio device is present. |
| LEAD-09 WINH09 no directed-speech implementation | Confirmed | Still no Windows addressee gate. |
| LEAD-10 S56 "keep the current way" | Unchanged as a decision | This study was asked for. It does not amend S56. |

## Call chains re-checked

Device open, barge arm, `_fd_trip`, `voice.record`, `TranscriptAdmission.Decide`, bout debounce, command TTS, and `SentenceChunker` were read at the lines cited in Audits 02 and 03. Android `ListeningService` L191–231, `DirectednessEvaluator.evaluate` L42–72, `ProactiveDeliveryCoordinator.buildDeliveryPlan` L274, and the Deepgram `SKIPPED_SPEAKING` / 220 ms guard were checked against the tree or HEAD. Duplicate findings were merged: the flag-flip problem is AUD-06, the deliberate absence is AUD-05, the echo hole is AUD-09.

## External references

| Claim | URL | Read | Limit |
|---|---|---|---|
| `IAcousticEchoCancellationControl`, OS build ≥ 22621 | https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nn-audioclient-iacousticechocancellationcontrol | 2026-10-18 | Endpoint support on this PC not tested. `E_NOINTERFACE` is a documented result. |
| AEC needs a render reference; integrated-only private refs miss USB/Bluetooth | https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/windows-11-apis-for-audio-processing-objects | 2026-10-18 | Driver behavior unverified. |
| Voice Capture DSP modes | https://learn.microsoft.com/en-us/windows/win32/medfound/voicecapturedmo and the `AEC_SYSTEM_MODE` page | 2026-10-18 | Not what `sounddevice` opens. |
| Communications category often required before the AEC control appears | https://github.com/naudio/NAudio/commit/688c029df500a673cb38b438a07f7fd7f2832af0 (2026-06-27) | 2026-10-18 | Third-party, not Microsoft. |
| WebRTC AEC3 render/capture split, 10 ms frames | https://webrtc.googlesource.com/src/+/refs/heads/main/modules/audio_processing/aec3/echo_canceller3.h | 2026-10-18 | Not a dependency. No on-machine run. |

## Writes

Only `zola-architecture/audit/voicepre-standalone/*.md` in the audit worktree. No source, config, dependency, or process change.
