# SPEECH-PRE Audit 02 — How she speaks today

Hermes pin `345cd2b…`. Labels: **EVIDENCE** / **INFERENCE** / **UNRESOLVED**. Findings `SPEECHPRE-AUD-NN`.

Against: A07 §10, P4-D18, P7-D06, P7-D07, D7(a), R1.

---

## 1. Ordinary voice reply sequence

| Step | Process / thread | Evidence |
|------|------------------|----------|
| Turn arms TTS | serve; `_start_turn_voice` → `_tts_stream_begin` | `prompt_turn.py:183–187`; begin only if `HERMES_VOICE_TTS=1` (`methods_voice.py:95–114`) |
| Model deltas | serve turn thread | `_stream` puts str delta on `st.tts_queue`, then `_emit("message.delta")` (`prompt_turn.py:523–531`) |
| Sentence split | TTS consumer thread | `SentenceChunker`: `.!?`+ws or blank line; `min_len=20`; strips `<think>` (`tts_streaming.py:62–96`) |
| Deepgram path | sync (non-streaming) | `resolve_streaming_provider` → None → `_SyncSentencePipeline` (`tts_tool_speaker.py:278–325`, `101–122`) |
| Synth per sentence | command provider subprocess | `tts.providers.deepgram.type: command` → `deepgram_tts.py` → temp `.mp3` (`tts_tool.py:323–330`; TEMPLATE `VOICE_CONFIG.md:12–33`) |
| Playback | new `ffplay` per sentence | `play_audio_file` → `ffplay -nodisp -autoexit` (`voice_mode.py:1053–1063`) |
| Last sentence | after text complete | `_finish_turn` puts `None` sentinel; `close()` finishes queued play (`prompt_turn.py:740–741`; `tts_tool_speaker.py:343–353`) |
| Client clock | UI thread / VC | `OnTurnStarted` estimate; deltas extend; `OnTurnCompleted` arms follow-up (`VoiceController.cs:1885–1998`) |
| Follow-up mic | after bout + quiet | Monitor bout end + 450 ms debounce + 0.5 s quiet → `StartCaptureAsync(FollowUp)` (`VoiceController.cs:2641–2663`, `3070–3303`; `PresenceLife` debounce 450) |

**Gaps between sentences:** created by per-sentence synth+play (new temp file + new ffplay). Long pauses = wait for next Deepgram command job, worst on the final sentence (SPEECH_DECISIONS SP-D03 context; EVIDENCE of mechanism above).

**SPEECHPRE-AUD-01 [RISK] HIGH** — Premature listening mechanism: follow-up opens on monitor silence (~450 ms + 0.5 s), not exact end of her full reply. Matches Known context / SP-D08. Files: `VoiceController.cs` follow-up release; `TtsPlaybackMonitor.cs` bout logic.

---

## 2. “Speaking” / “finished” signals

| Signal | Producer | Derivation | Consumers |
|--------|----------|------------|-----------|
| `_speakingEstimate` / `Speaking` | `VoiceController` | Clock from turn start/deltas; held while `_replyReleaseArmed` | HUD, presence Speaking, Stop button (`CanStopSpeaking`) |
| Playback **segment** | `TtsPlaybackMonitor` | Owned ffplay session Active | Mouth (`PresenceAnimator`) |
| Playback **bout** start/stop | Monitor; bout ends after `ReleaseDebounceMs` (450) without segment | Follow-up / question_release; proactive `NotePlayback`; mouth |
| Forced bout stop | `ForceInactiveLocked` / `TakeForcedRelease` | Estimate fallback (`FollowUpRuleForcedEstimate`) | Follow-up open without natural rule-1 |
| `mark_audio_output_active` | Hermes `play_audio_file` | Process-local | Hermes barge only (off in Zola) |
| `voice.interrupted` | Hermes `_fd_trip` | Barge (profile `barge_in: false`) | Client interrupt path |
| Proactive echo “finished” | `SpeechEchoGuard.NoteCompleted` | Bout stop + `EchoTailSeconds=2` | Capture refuse |

**P7-D06 [MATCH]:** estimate cannot open while monitor still reports bout (`HandBackActiveBoutOrAllowEstimateAsync`).

**SPEECHPRE-AUD-02 [GAP] MEDIUM** — No client-visible “exact end of playback” from the device clock. Monitor watches ffplay under serve PID (`TtsPlaybackMonitor.cs`), not `IAudioClock`.

---

## 3. Unprompted path + D7(a) vs A11

| Item | Evidence |
|------|----------|
| Delivery | `ProactiveSpeechSession` / `ProactiveDeliveryCoordinator`: claim → speech_started → `voice.tts` (`ProactiveSpeechSession.cs:3–13,206–252`) |
| Speak RPC | `ChatSpeechGateway.SpeakAsync` → `voice.tts` (`ChatSpeechGateway.cs:84–86`; Hermes `methods_voice.py:765–775`) |
| D7(a) | No follow-up arm on proactive path; ordinary follow-up only from `OnTurnCompleted` |
| 2 s echo tail | `SpeechConstants.EchoTailSeconds = 2`; `SpeechEchoGuard.AllowsCapture` (`SpeechEchoGuard.cs:64–88`; VC refuse `2044–2048`) |

**vs A11:** A11 = single engagement delivery/acknowledgement semantics. D7(a) = no auto follow-up after unprompted. Complementary. As-built P9 records playback outcomes via monitor (`delivered` / `delivery_uncertain`).

**SPEECHPRE-AUD-03 [MATCH] LOW** — Unprompted lines use the same Hermes `voice.tts`/ffplay path as clarify questions; D7(a) enforced by not arming follow-up + echo tail.

---

## 4. Code-read path (R1 / ARCH-36)

| Claim | Evidence |
|-------|----------|
| Voice | `CodeReadConstants.VoiceName = "Zira"` (`CodeReader.cs:17–18`) |
| Local only | System.Speech → MemoryStream WAV → winmm `PlaySound`; no file/network/`voice.tts` (`LocalCodeVoice.cs:6–8,137–167`) |
| Value never logged | Ids/outcomes only; wiped after speak (`CodeReader.cs:10–12,304,411–416`) |
| Collision | One active run (`busy`); mic refused while latch; PTT/Stop cancels read |

**SPEECHPRE-AUD-04 [MATCH]** — Codes stay off cloud TTS. **[RISK] LOW** — Zira/winmm and Hermes/ffplay can share the default render device concurrently (no exclusive lock) — INFERENCE for audible collision under owner cutover.

---

## 5. Other sound paths (bypass risk for new owner)

| Path | Owner | Trigger | Bypass risk |
|------|-------|---------|-------------|
| Ordinary reply TTS | serve `stream_tts_to_speaker` + ffplay | Voice TTS on + deltas | Primary path to replace |
| Clarify / unprompted | Client → `voice.tts` | Clarify / proactive | Same ffplay; must route to owner |
| Code Zira | `LocalCodeVoice` | `code_read` | Separate speaker (R1 keep) |
| Beeps | Hermes `_play_beep` | record start/stop | Off (`beep_enabled: false`, S51F-D03) |
| Thinking sound | `start_thinking_sound` | Turn start | Off (`thinking_sound: false`, S51F-D01) |
| Lost-request | UI text only | Unreachable + in-flight | No audio (`LostTurnNotice`) |
| Heartbeat / review.summary | Hermes extras | Background | Text/complete paths; A01 Q1 risk if they speak |

**SPEECHPRE-AUD-05 [RISK] HIGH** — `voice.tts` does **not** check `HERMES_VOICE_TTS` (`methods_voice.py:765–775`; P4-ASK progress). Disarming turn TTS alone does not silence proactive/clarify unless client stops calling or owner owns those speaks.

---

## 6. Stopping

| Action | Effect |
|--------|--------|
| Stop speaking | Cancel follow-up + `voice.toggle off` (cuts TTS) then restore on/tts/wake (`VoiceController.cs:1192–1346`) |
| Esc | Routes to Stop if `CanStopSpeaking`; refuses while `QuestionSpeaking` |
| Mic while speaking | Starts Manual capture; **does not** stop TTS (KI-S51F-MIC) |
| New turn | Hermes `_tts_stream_begin` stops previous pipeline |
| Client close | VC Shutdown cancels follow-up/capture; does not itself kill ffplay (serve teardown separate) |

**SPEECHPRE-AUD-06 [RISK] MEDIUM** — Mic-while-speaking does not stop playback (open KI-S51F-MIC). Unprompted Stop unavailable (KI-S51F-STOP).

---

## 7. Output device

| Topic | Label | Evidence |
|-------|-------|----------|
| Device choice | EVIDENCE | `ffplay` argv has no device id — OS default (`voice_mode.py:1060`) |
| Stream lifetime | EVIDENCE | New ffplay per sentence (open/close between sentences) |
| Monitor bind | EVIDENCE | `GetDefaultAudioEndpoint(Render, Multimedia)` once (`AudioSessionInterop.cs:96–100`) |
| Default-device / BT change | INFERENCE | No re-bind on endpoint change → missed Active / early bout |
| First/last word cut on BT | INFERENCE | Per Part G addendum hypotheses; Windows path has no WSL-style pad; KI-S51F-CLIP open |

**SPEECHPRE-AUD-07 [GAP] MEDIUM** — No Bluetooth-aware hold or stream-keep; Part G never ran (Phase 10).
