# SPEECH-PRE Audit 03 — How she listens today

Against: A07 §§2–5, P2-D01, P2-D04, P2-D06, P7-D01–D05, P4-D28.

---

## 1. Capture starts → admitted transcript

`CaptureKind`: Wake, Manual, FollowUp, EchoReopen, Clarify (`CaptureLifecycle.cs:13–20`).

All starts: `StartCaptureAsync` → `voice.record` start (`VoiceController.cs:2033–2218`).

| Trigger | Kind | Mic owner |
|---------|------|-----------|
| `wake.detected` → `HandleWakeDetectedAsync` | Wake | Idle: serve wake PortAudio. Record: serve `AudioRecorder` |
| Mic button / Ctrl+Space | Manual | Same record path; wake paused |
| Follow-up after release | FollowUp | Same |
| Echo drop → reopen (0.5 s, max 3) | EchoReopen | Same |
| After clarify question bout | Clarify (`srq-*`) | Same |

Path: PortAudio → silence stop → WAV → faster-whisper → `voice.transcript` → `ChatSocket` → `OnVoiceTranscript` → `TranscriptAdmission.Decide` → `TranscriptReady` → `SubmitTurnAsync` / clarify bind (`MainWindow.xaml.cs:725–755`).

**SPEECHPRE-AUD-08 [MATCH]** — P2-D01: physical mic is Hermes serve; client is RPC driver only.

---

## 2. Wake word

| Fact | Evidence |
|------|----------|
| Process | Serve; RPCs `wake.start/stop/pause/resume` (`methods_voice.py:309–543`) |
| Live config | Sherpa, `"hey zola"`, `capture: local` (`VOICE_CONFIG.md` / DESIGN_DECISIONS P2-D04) |
| Holds mic | Yes while armed (local InputStream); pause releases (`wake_word.py:521–526`) |
| Handoff | Detect → pause → `wake.detected` → client `StartCaptureAsync(Wake)` → `voice.record` |

**If owner holds the mic (P7-D01 one listening path):**

**SPEECHPRE-AUD-09 [GAP] HIGH** — Hermes local wake + local record cannot open a second PortAudio device (`wake_word.py:6–8`). Owner must either (a) stream PCM via `wake.feed` / `capture: client`, or (b) run phrase detect and synthesize the wake→capture contract. Admission still needs Accepting lifecycle tied to that capture.

---

## 3. End of Brian’s speech / first words

| Setting | Live Zola | Code default |
|---------|-----------|--------------|
| `silence_duration` | **1.5 s** (lore) | 3.0 s Hermes default |
| Pre-roll on `voice.record` | **None** | `listen_for_speech(pre_roll_ms=…)` unused |
| Beep before samples | Gated off (S51F-D03) | Would play before `rec.start` |
| No-speech wait | 15 s `_max_wait` | |

Compare SB baseline (by reference, `SPEECH_BASELINE_RESULTS.md`): clipped openings / first-word misses already observed; mechanism here has no pre-roll — matches spike motivation for 500 ms gate-blocked pre-roll.

**SPEECHPRE-AUD-10 [RISK] MEDIUM** — No pre-roll + beep-before-open history → first-word clip (KI-S51F-CLIP; SB). Owner’s 500 ms pre-roll is the intended fix (spike rule).

---

## 4. TranscriptAdmission

Order (`TranscriptAdmission.Decide`, `57–117`): gated → modeText → !HasOutstanding → Cancelled → Settled → !Accepting → ClarifyNotActive → TurnRunningUnbound → Echo → **Admit**.

Hermes-coupled signals that need a new source if owner captures:

| Dependency | Why |
|------------|-----|
| `voice.status` listening → Accepting | Proves `start_continuous` (P7-D03) |
| `voice.transcript` settles owner | No capture correlation ID |
| `voice.record stop` on cancel | P7-D02 |
| Echo eligibility flags | Tied to Hermes capture window |

**SPEECHPRE-AUD-11 [GAP] HIGH** — Owner capture must emit equivalent ownership signals (or a capture id) so Accepting ↔ transcript correlation holds; else a second transcript path risks breaking P7-D01.

---

## 5. Clarify (P7-D05, P7-D09)

Speak question → bout → `ArmClarifyAnswerCapture(id)` → `StartCaptureAsync(Clarify, id)` → Admit only if open+session match → `ApplyVoiceClarifyAnswer`. No-answer fires quiet panel once.

**Owner must provide:** capture tagged with same `srq-*`; validity; Accepting-window transcript; cancel/settle for no-answer.

**SPEECHPRE-AUD-12 [MATCH]** — Binding is on Zola side via ClarifyId; owner supplies tagged capture + text only.

---

## 6. Lock, Text mode, one build

| Control | Behaviour |
|---------|-----------|
| Lock (P4/S32) | Cancel capture/follow-up; `voice.toggle off`; `wake.stop`; refuse new wake/capture/submit |
| Text mode | Invalidate+stop; disarm wake; admission `mode_text` drop |
| One build | `Local\ZolaClient` mutex; second instance exits before serve/mic |

**SPEECHPRE-AUD-13 [MATCH]** — Lock and Text already fail closed for mic. Owner must honour the same gates.

---

## 7. Serve audio threads / S51 Group A

Threads: PortAudio stream callback; wake-word daemon; silence-stop; TTS/thinking/barge (barge off); `voice.tts` speak thread. `AudioRecorder` keeps InputStream across recordings.

| Label | Content |
|-------|---------|
| EVIDENCE | Group A dumps: PortAudio stream thread; libportaudio + sherpa-onnx loaded (S51 dump analysis) |
| UNRESOLVED | Input vs output stream |
| INFERENCE | Retiring Hermes-local InputStream (wake+record) into an owner would remove that serve crash surface — not proven |

**SPEECHPRE-AUD-14 [RISK] MEDIUM** — KI-S51-PA mitigated/watching; moving mic out of serve is relevant evidence (Known context), not a decision.
