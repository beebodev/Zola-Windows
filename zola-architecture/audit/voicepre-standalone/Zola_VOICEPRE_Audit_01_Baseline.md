# VOICEPRE Audit 01 — Baseline

Read-only setup for the standalone voice feasibility study. No live turn, no process start or stop, no source edit. Audit Markdown in this directory is the only write.

## Source scopes

Two scopes. The audit worktree does not contain the uncommitted P9 speech work.

| Scope | Path | Branch | HEAD | Dirty |
|---|---|---|---|---|
| Committed main (audit worktree) | `C:\Users\test\Dev\zola-windows-voicepre-audit` | `voicepre-audit` | `03a3a1fac02a7b6c18b745e6ac3be43b2cd3b090` | clean at creation |
| Execution overlay (read-only) | `C:\Users\test\Dev\zola-windows` | `p9-speak` | same `03a3a1f` | dirty and untracked P9 speech files |
| Hermes reference | `C:\Users\test\Dev\hermes-agent` | detached HEAD | `345cd2b057a452236de401d3534b8502a7465e8d` | clean |
| Android reference | `C:\Users\test\StudioProjects\ZolaAssistant` | `zola-main` (already checked out; not switched) | `a139ccacab596f12b95e2dd3eda14352bcb97836` | working tree deletes `speech/**`; untracked `sms/speech/` mirror |

Primary remote: `https://github.com/beebodev/Zola-Windows`. Local `main` and `p9-speak` both point at `03a3a1f` (`docs: record P9-SURFACE merge SHA`, 2026-10-16). The primary checkout was not switched. Worktree `voicepre-audit` was created from local `main` with no fetch. The branch and path did not exist beforehand.

Hermes `git describe --tags --always` is `v2026.9.14`. The annotated tag object is `7a963716b81be13ba513d4f127633b7da493aff2`; the commit it peels to is the pin above. No local Hermes diff.

### Applicable instructions

[DOC] No `AGENTS.md` in the Zola-Windows tree (root, `zola-architecture/`, `.cursor/`). Hermes has its own per-directory `AGENTS.md` files. They describe Hermes, not this product's audit rules. This audit follows the VOICEPRE prompt and the Zola lore authority order.

### Overlay hashes (SHA-256, first 16 hex)

Recorded 2026-10-18 before the phase documents. Rechecked in Audit 08.

| File | Overlay | Committed worktree |
|---|---|---|
| `windows-client/Zola.Client/VoiceController.cs` | `0136876FF16DE9A6` | `F070711BABD35035` |
| `windows-client/Zola.Client/ChatSocket.cs` | `B339E54B56FBE130` | `23495FA14BFCFB4E` |
| `windows-client/Zola.Client/MainWindow.xaml.cs` | `E63317A2CF55A400` | `81132AC02FB3098A` |
| `windows-client/Zola.Client/Voice/CaptureLifecycle.cs` | `D8B95D69E6E9DC0E` | same |
| `windows-client/Zola.Client/Voice/TranscriptAdmission.cs` | `BCCE33FA242E496E` | same |
| `windows-client/Zola.Client/Voice/ClarifySpeech.cs` | `5F6D6760F2052B4A` | same |
| `windows-client/Zola.Client/Presence/TtsPlaybackMonitor.cs` | `763178A261879FB3` | `035802317A761D58` |
| `windows-client/Zola.Client/Speech/SpeechEchoGuard.cs` | `8176EC4E5EEEF4BF` | absent |
| `windows-client/Zola.Client/Speech/ProactiveDeliveryCoordinator.cs` | `210FFF3AC901257C` | absent |
| `windows-client/Zola.Client/Speech/ProactiveSpeechSession.cs` | `2D94F6F23C2CDA30` | absent |
| `hermes-plugins/zola_workspace/speech.py` | `D4414DD9E59FB857` | absent |
| `zola-architecture/lore/prompts/progress/P9-SPEAK_Progress.md` | `BFB7E79C2936ED91` | absent |
| `zola-architecture/identity/VOICE_CONFIG.md` | `0CACE932C857B57F` | same |

`VoiceController.cs` overlay delta is the P9 proactive echo hook and idle stamps (about 64 added lines). Admission and capture-lifecycle sources are byte-identical across scopes.

## Documents of truth

| Document | Location | Version note |
|---|---|---|
| Master plan §12 | `zola-architecture/Zola Master Architecture Plan.md` | No version header. §12 read at lines 610–666. Target, not a locked build decision. |
| Conversational Attention | `zola-architecture/Zola Conversational Attention Architecture.md` | No version header. Target. |
| Conversational Continuity | `zola-architecture/Zola Conversational Continuity Architecture.md` | No version header. Target. |
| Streaming Cognition | `zola-architecture/Zola Streaming Cognition Architecture.md` | No version header. Target. |
| Privacy and Data Ownership | `zola-architecture/Zola Privacy and Data Ownership Plan.md` | No version header. |
| Presence UI | `zola-architecture/Zola_Presence_UI_Architecture.md` | No version header. |
| Distributed presence | `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` | v0.1, 2026-10-03, strawman. Proposals only. |
| Roadmap | `zola-architecture/lore/ROADMAP.md` | Pins Hermes `v2026.9.14` / `345cd2b`. Phase 9 is "scope is Brian's call". No Phase 10 or 11 heading. |
| Design decisions | `zola-architecture/lore/DESIGN_DECISIONS.md` | Living file. Phases 2–8 present. No Phase 9 decision section. |
| Open questions | `zola-architecture/lore/OPEN_QUESTIONS.md` | S19, S21, S34, S36, S38, S51–S53, S55, S56, S70 read in current wording. |
| Voice config | `zola-architecture/identity/VOICE_CONFIG.md` | Canonical copy still describes Edge Sonia. Live provider differs (below). |
| Build plans | `lore/build-plans/PHASE2_BUILD_PLAN.md` v1.1, `PHASE4` v1.1, `PHASE5` v1.2, `PHASE7` v1.1, `PHASE9` | Read for the cited decisions. |
| P9 progress | Overlay only: `lore/prompts/progress/P9-SPEAK_Progress.md`, plus committed `P9-FIX-TTS_Progress.md`, `P9-SUPERVISE_Progress.md`, `P9-STORE_Progress.md` | Progress is not a passed smoke. |

Prior audits used as leads, not as new proof: `audit/p5pre-phase5/` (barge-in, live probes, synthesis), `audit/p7pre-phase7/` (echo, chunking, forensic), `audit/winh-hermes-gap/Zola_WINH09_Audit_05_ConversationalAttentionAuthority.md`. P10PRE exists under `audit/p10pre-phase10/` and is context only.

### Authority conflicts recorded, not resolved

- Master Plan §12 and the Conversational Attention architecture want wake-free directed speech. `P2-D04` and `S19` still make "Hey Zola" the primary trigger. A desired future capability is not a violation of the deferral.
- `P4-D28` / `P5-D08` keep `voice.barge_in: false`. SYM-03 asks to restore talk-over. That is an open request (`S36`), not a license to flip the flag.
- `P2-D01` / `C3` give the microphone and speaker to the Hermes serve child. Option C would reverse that and needs an amendment. `S56` records Brian's 2026-10-06 preference to keep the current arrangement; this prompt reopens the study and does not amend the decision.
- `P2-D03` / `P4-D19` and `VOICE_CONFIG.md` still name Edge Sonia. The live profile and `P9-FIX-TTS` name Deepgram Aura-2 Pandora. Lore was not updated (`P9-SPEAK` discrepancy note).

## Decision status used by this audit

Current wording, not memory of another project.

| ID | Status | What it locks for this study |
|---|---|---|
| C3 | Locked, clarified by P2-D01 | One JSON-RPC voice owner. The serve child holds the device handle. |
| P2-D01 | Locked; P3-D23 display-only amendment | Client does not open an audio device and does not use `/api/audio/*`. |
| P2-D13 | Locked; side effect reduced by P4-D28 | Three `voice.interrupted` trips with no complete turn switch to Text mode. |
| P2-D14 | Locked; P7-D07 says defense only | End-anchored echo drop: under 3 words never dropped; run ≥3 and ≥0.60, near the tail. |
| P2-D16 | Locked as a machine requirement | Historical Latitude setup: lid open, mic 100, enhancements on, speakers ~15, ffplay on PATH. Not proof of today's levels. |
| P4-D02 | Locked | Lock/suspend pauses, stops, cancels, refuses. Fail closed. `voice.toggle off` for the gate, not `tts`. |
| P4-D14 | Revised in part by P7-D05 | Only the bound clarify capture answers a clarify. |
| P4-D18 | Locked; monitor outranks estimate (P7-D06) | Follow-up opens on bout stop plus quiet, estimate only as fallback. |
| P4-D28 | Locked; P5-D08 stands | `voice.barge_in: false`. |
| P4-D29 | Locked | On-screen Stop and Esc stop speech without the interrupt latch. |
| P5-D08 | Locked | S36 feasibility gate NO on the pinned APIs. Only an upstream clarify-aware listener plus pre-roll was scored as able to pass (a)(b)(e). |
| P7-D01–D08, D13 | Locked | One admission authority; cancel before stop; one capture; no unbound mid-turn transcript; bound clarify only; monitor outranks estimate; echo cannot admit; drops logged without text. |
| S19 | Open | Directed speech without a wake word is the long-term target. |
| S21 | Open | Typed Cancel during speech can still latch Hermes's interrupted note. |
| S34 | Open; Phase 7 track cut | Sentence chunker stays. Whole-line synthesis not adopted. |
| S36 | Open, upstream-gated | Talk-over, with clarify and first-word acceptance still unmet. |
| S38 | Open, updated | Listen-to-think measurements are Edge-era plus Whisper. Not resolved. |
| S51 | Open | Native serve crash class. Not diagnosed here. |
| S52 | Open | Stop-vs-silence race. No client guard shipped. |
| S53 | Open | No capture id. No `voice.record cancel`. |
| S55 | Open | Streaming TTS bake-off. Not selected. |
| S56 | Open study; 2026-10-06 preference was no fork | This audit is that study. It does not lock a new owner. |
| S70 | Open | No playback-completion signal. A cut-off read-back can still count as reviewed. |

NOT FOUND: no decision id in the requested set was missing from `DESIGN_DECISIONS.md` or `OPEN_QUESTIONS.md`.

## Current versus target

| | Current (static) | Target named by this prompt |
|---|---|---|
| Barge-in | Off by P4-D28. Full-duplex listener is not armed. | Talk-over stops a long reply without breaking a spoken clarification (SYM-03). |
| First words | `voice.record` starts after a beep and keeps no pre-roll. | Opening words of an answer are kept (SYM-02). Cause of the current clips is not established. |
| Echo | Text match after STT, and an uncommitted proactive phrase guard. | Zola's own speech is not admitted as Brian (SYM-01). |
| Attention | Wake word, mic button, or Ctrl+Space, then one utterance. | Continuous wake-free talk, quiet when speech is for someone else (SYM-04). |
| TTS | Live provider is Deepgram command, one file per sentence, ffplay. | Shorter time-to-first-audio and smaller gaps are a symptom to analyze (SYM-05), not a confirmed current measurement. |

## P9-SPEAK status

[DOC] `P9-SPEAK_Progress.md` (overlay only): Phases 1–6 complete, Phase 7 Deploy and smoke **IN PROGRESS**, Phase 8 closeout **PENDING**. `speak_enabled` was left true. The code is not on `main`.

The live `config.yaml` SHA-256 is `823DBD95C6D63EB66BE07182FAA82ACB5C48528A79F01109B6C4120560C74AFC` (4,850 bytes, mtime 2026-10-17 10:18 local). That matches the progress record of the `speak_enabled: true` edit. This audit did not read other profile keys.

P9-SPEAK is therefore **uncommitted, under smoke, not closed**. It is not evidence that proactive speech passed.

## TTS provider (keys only)

[CODE] + keys-only profile read, 2026-10-18. No command line, path, or credential was recorded.

| Key | Value |
|---|---|
| `tts.provider` | `deepgram` |
| `tts.providers.deepgram.type` | `command` |
| `tts.providers.deepgram.model` | `aura-2-pandora-en` |
| `tts.providers.deepgram.speed` | `0.95` |
| `tts.providers.deepgram.output_format` | `mp3` |
| `tts.edge.voice` | `en-GB-SoniaNeural` (still present; not the selected provider) |
| `tts.edge.speed` | `0.95` (still present) |

`VOICE_CONFIG.md` still says `tts.provider: edge`. Edge-era timings in P7-LATENCY are [HISTORY]. The code path to trace is the command provider, then ffplay.

`voice.barge_in` was not in the keys-only allowlist. The canonical file and the P9-SPEAK discrepancy note both still say `false`. The config hash matches a snapshot whose progress note says the only edit was `speak_enabled`.

## Tests that cover these paths (not run)

Committed `Zola.Client.Checks`: capture lifecycle rows (Starting/Accepting/Cancelled/Settled), admission rows (`gated`, `no_owner`, `turn_running_unbound`, `clarify_open_while_turn`, `echo_last_rejects`, `echo_cannot_admit`), stop-phrase and latch wiring. `TurnTiming` rows mirror `SentenceChunker`.

Overlay only: `SpeechChecks.cs` gate and reservation rows; `hermes-plugins/zola_workspace/tests/test_p9_speak.py` claim, echo-phrase, and outcome rows. Names are in the P9 evidence pass. None were executed.

Hermes has `tests/tools/test_voice_mode.py` and `tests/tools/test_tts_streaming.py`. Not run. They are not Zola acceptance tests.

## Logging allowlist (G-TIMING-LOGS)

Writers were inspected. No log file was read.

| Path | Writer | Verdict |
|---|---|---|
| `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` | `VoiceController.WriteTimeline` | **Mixed.** Lengths, reasons, and ids are the intent (`P7-D08`), but lines can include a TTS error string and `wake.detected phrase=`. Not read. |
| `%LOCALAPPDATA%\ZolaClient\logs\presence.log` | `PresenceView.WriteLog` from `TtsPlaybackMonitor` | Event names, pids, gap milliseconds. No reply text in the bout lines read in source. Allowlisted and **not read**; historical timings already live in progress docs. |
| `%LOCALAPPDATA%\ZolaClient\logs\proactive.log` | `ProactiveSpeechSession` / `SpeechDenyLog` | Attempt hash, outcome, reason, phrase index. Overlay only. Not read. |
| Hermes `zola_workspace.log` | `speech.py` `_log` | Same metadata shape. Not read. |
| `turn_timing` lines | `TurnTiming.Finalize` via the voice timeline | Stage durations. Treated as part of the mixed timeline file, so not read from disk. |

Historical measurement sources, all [HISTORY] or [DOC]: P5-D09 / S38 (Whisper 1562–1847 ms warm), P7-LATENCY baseline (Edge; EoS→first audio median 9534 ms, n=7), P4-VOICE trailing silence ~0.50 s, P4-FEEDBACK residual ~1 s clip, P9-SUPERVISE one Deepgram sample `submit_to_first_audio_ms=4628` (single turn, 2026-10-12). None of these are a current distribution.

## Hardware facts

Observed 2026-10-18 with WMI, no device setting changed.

| Fact | Value | Status |
|---|---|---|
| PC | Dell Latitude 7430 | Observed today. Same model as P2-D16. Not a confirmation of the old acoustic setup. |
| OS | Windows 11 Pro, build 26200 (`10.0.26200`) | Observed today. |
| Microphone model | — | UNKNOWN |
| Capture endpoint in use | — | UNKNOWN. Enumerated sound devices include USB Audio 2.0, Intel Smart Sound Bluetooth, Intel Smart Sound USB, and Realtek. Which one is default is not established. |
| Speaker or headset | — | UNKNOWN |
| Output endpoint | — | UNKNOWN |
| Speaker level | — | UNKNOWN. Historical "~15" is not today's measurement. |
| Mic distance | — | UNKNOWN |
| Room or shop | — | UNKNOWN |
| Windows audio enhancements / AEC | — | UNKNOWN. P2-D16 required them on. Not re-read. |

A USB audio device being present means the built-in lid mic is not a safe assumption.

## Questions that do not block this static audit

Listed again in the synthesis: which capture and render endpoints are default; enhancements on or off; speaker versus headset; quiet room versus shop; whether SYM-02 happens before the beep, during follow-up, or on wake; whether SYM-01 is a short reply, a later sentence, or a proactive line.
