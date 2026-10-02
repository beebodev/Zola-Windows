# P5PRE Audit 04 — S38 listen-to-think latency (static map)

Static only. No timings and no tuning. Numbers are Phase 6 L3.

Effective voice capture uses `voice.record` → `start_continuous` (`tui_gateway/methods_voice.py` 747–753). The live profile sets `voice.silence_duration` to 1.5. The code default is 3.0 (`hermes_cli/voice.py` 336, `tools/voice_mode.py` 35).

---

## 1. Stages from "Brian stops talking" to "Thinking"

| Stage | Code | Log line that timestamps it | Measurable today |
|---|---|---|---|
| Silence wait (1.5 s) | `AudioRecorder._should_auto_stop` (`tools/voice_mode.py` 674–682). Starts the timer on the first quiet block after speech is confirmed. Fires when `now - _silence_start >= _silence_duration`. | Hermes `logger.info`: `Silence detected (%.1fs), auto-stopping`. Not written to `voice-timeline.log`. | **UNMEASURABLE without new logging** in the client logs. The Hermes line exists in code. Whether that logger is written to a file this audit can read is **UNVERIFIED** until L3 looks for the serve log. A fix would add `silence_start` and `silence_fire` on `voice-timeline.log`. |
| Capture stop | `AudioRecorder.stop` (800–820), called from `_continuous_on_silence` (`hermes_cli/voice.py` 485–486), which first emits status `transcribing`. | Hermes: `Voice recording stopped (%.1fs, %d samples)`. Client: `display-state.log` voice label changes to `Transcribing` when `voice.status` `transcribing` updates the chrome (`ZolaDisplayState.cs` 365, logged at 518–524 as `P3-STATE: display state voice="..." ...`). | The display-state label change is measurable and is the client-visible end of capture. It includes the silence wait. It is not a separate silence-versus-stop split. |
| WAV write | `AudioRecorder._write_wav` (`voice_mode.py` 840–842), called from `stop`. | Hermes: `WAV written: %s (%d bytes)`. No client line. | **UNMEASURABLE without new logging** on the client. Same Hermes-file caveat as the silence line. A fix would add `wav_written bytes=` on `voice-timeline.log`. |
| Whisper load (cold) and inference | `transcribe_recording` (`voice_mode.py` 852–858) → `transcribe_audio` → `_load_local_whisper_model` (`tools/transcription_local.py` 123–143). Load is once per process unless idle-unload is set. Default `unload_after_idle_seconds` is 0 (never), `config_defaults.py` 1095. | No start/end log on the load or the `transcribe` call was found on this path. | **UNMEASURABLE without new logging.** A fix would add `whisper_load_start` / `whisper_load_end` and `whisper_infer_start` / `whisper_infer_end`. Cold versus warm is inferred in L3 only by whether the first turn after launch is much slower (S23). |
| Transcript delivered to the client | `_continuous_on_silence` calls `on_transcript` (`hermes_cli/voice.py` 504–505). The RPC emits `voice.transcript`. The client logs it in `OnVoiceTranscript`. | `voice-timeline.log`: `transcript len={0} filtered={1} stop={2} nospeech={3} bound={4} capture_start={5} capture_stop={6} duration_s={7}` (`VoiceController.cs` 175–176, written at 2019). Text is not logged (P4-D18). | **Measurable.** `capture_start` / `capture_stop` / `duration_s` bracket the whole capture, including the silence wait. The line's timestamp is delivery to the client, which is after Whisper. |
| Submit | Unbound speech calls `SubmitTurnAsync` (`MainWindow.xaml.cs` 394–407) → `ChatSocket` `prompt.submit` (`ChatSocket.cs` 279–285). A bound clarify does not submit (P4-D14). | `server-requests.log` is the clarify broker only (`ServerRequestBroker.cs`). `prompt.submit` is not written to `voice-timeline.log`. | **UNMEASURABLE without new logging** as its own line. A fix would add `prompt.submit` on `voice-timeline.log`. L3 can bound it between the transcript line and the first `message.start` proxy below. |
| First server event | `message.start` is handled in `ChatSocket.cs` (630) and opens the assistant bubble in `MainWindow` (`OnMessageStarted`, around 848). | No dedicated client line for `message.start`. | **UNMEASURABLE without new logging** as its own line. A fix would add `message.start`. The next row is the practical proxy. |
| HUD shows Thinking | `ZolaDisplayState` sets the voice label to `Thinking` when the turn is streaming and she is not speaking (357, 457). | `display-state.log`: `P3-STATE: display state voice="Thinking" mic="..." mode=Thinking ...` (format at line 60, written at 518–524). | **Measurable.** This is the presence change the criterion names. It fires when streaming becomes true, which is `message.start`, not when the first token is painted. Time from submit to first token is not separately logged. |

The silence wait is inside the capture window. `duration_s` on the transcript line is capture length, not listen-to-think. Listen-to-think is the timestamp of that transcript line through the `display-state.log` Thinking line, plus the 1.5 s that is inside the capture and cannot be split out from client logs alone.

**P5PRE-AUD-17** [GAP] MEDIUM — `voice-timeline.log` and `display-state.log` can time capture delivery and the Thinking label. They cannot split silence wait, WAV write, Whisper load, Whisper inference, `prompt.submit`, or `message.start`. Those six need the log lines named above. This audit does not add them. S38 stays measure-only.

**P5PRE-AUD-18** [MATCH] — The path is one sequence: VAD silence → `rec.stop` (WAV) → `transcribe_recording` → `voice.transcript` → `prompt.submit` → `message.start` → display label `Thinking`. No second client-side transcriber.

---

## 2. Effective Whisper config

Profile `stt` (read-only): provider `local`, model `base`. The profile does not set `stt.local.device` or `stt.local.compute_type`.

Defaults (`hermes_cli/config_defaults.py` 1084–1096): `stt.local.model` `base`, `vad` true, `unload_after_idle_seconds` 0. No `device` or `compute_type` key in that block.

The loader (`tools/transcription_tools.py` 322–324) calls `_load_local_whisper_model` with `local_cfg.get("device", "auto")` and `local_cfg.get("compute_type", "auto")`. On this pin that is `device="auto"`, `compute_type="auto"` (`transcription_local.py` 123–143). `auto` tries the requested device first and falls back to CPU `int8` only on a CUDA library error, or forces CPU `int8` on Apple Silicon. This is not Apple Silicon.

`identity/VOICE_CONFIG.md` records this machine as having no CUDA, with the P2 load landing on CPU. That is the documented machine fact. The live process's actual device and compute type are **UNVERIFIED** until a load is observed; the config does not pin them, and nothing in this audit loads the model. No GPU is configured. `auto` may still attempt CUDA inside faster-whisper before falling back.

**P5PRE-AUD-19** [MATCH] — Effective STT is local faster-whisper, model `base`, device and compute type `auto` (not pinned). Idle unload is off, so a cold load is once per serve process (S23), not once per turn.
