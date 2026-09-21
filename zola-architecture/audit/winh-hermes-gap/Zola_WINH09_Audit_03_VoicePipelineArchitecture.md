# WINH09 Audit 03 — Voice Pipeline Architecture: Sequential Model & Latency

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Master Plan **§3 Current Sequential Model only** — STT → Reasoning → TTS. Long-Term Streaming Model is **not scored**.

---

## 1. Live-voice turn end to end (chained default)

Default `voice.voice_chat_mode: "chained"` (`config_defaults.py` L1132).

```
voice.toggle action=on     → HERMES_VOICE=1   # methods_voice.py L627–629
voice.record action=start  → start_continuous  # hermes_cli/voice.py L331
     VAD silence stop      → WAV
     transcribe_recording  → tools/voice_mode.py L852 → transcribe_audio (file STT)
     _vr_transcript        → _emit("voice.transcript")  # methods_voice.py L685–686
Desktop/TUI client (not the gateway) typically prompt.submit(text)
     methods_prompt.prompt.submit → prompt_turn._run_prompt_submit   # same path as typed chat
     _start_turn_voice / token deltas → tts_queue → stream_tts_to_speaker
     speaker via sounddevice (tts_tool_speaker.py)
```

Gateway **does not** auto-`prompt.submit` the transcript; it emits `voice.transcript` (`contracts/events.py`). Reasoning is the **normal** `prompt_turn.py` loop (`WINH03-AUD-02`), not a separate agent.

Optional **GPT-Live** path (`tools/voice_live.py` L1–20): renderer WebRTC ↔ OpenAI `/v1/live/sessions` (`hermes_cli/web_routers/audio.py` `POST /api/audio/voice-live/session` L177–197). Live model owns mic/speaker; each `session.delegation.created` becomes `prompt.submit` with `surface: voice-live`. That is a **second** pipeline (full-duplex vendor voice + Hermes as tool backend), not chained STT.

**Label:** `[PARTIAL]` `WINH09-AUD-05` (MEDIUM) — chained mode is STT → same `prompt_turn` → TTS; STT result re-enters via client `prompt.submit`, not an in-process call. GPT-Live is a separate OpenAI duplex mode.

---

## 2. Streaming vs batch at each stage

**STT (chained):** `start_continuous` is VAD-driven **utterance capture** (`voice.py` L331–341, `silence_duration` default 3.0s). Then `transcribe_recording` sends a **WAV file** (`voice_mode.py` L852–858). `TranscriptionProvider.transcribe(file_path)` (`transcription_provider.py` L27–30). **No partial transcripts while speaking.** Local STT uses Silero VAD to *split* the file (`config_defaults.py` stt.vad L1088–1092), still after capture.

**TTS (chained, voice TTS on):** `methods_voice.py` L88–109 — token deltas feed `stream_tts_to_speaker` (sentence buffer). If the configured provider has a `StreamingTTSProvider` (`ElevenLabsStreamer` etc.), audio starts **per sentence** before the full reply. Else fallback whole-reply `speak_text`. Edge (default TTS) is **not** in the chunked-PCM list — likely sentence-or-whole synthesize, not PCM stream.

Maps to Zola’s **current** sequential model: wait for an utterance, then reason, then speak (with optional sentence-level TTS overlap). Not long-term partial-STT.

**Label:** `[PARTIAL]` `WINH09-AUD-06` (MEDIUM) — STT is batch-after-VAD; TTS can stream sentences when a streamer exists.

---

## 3. `voice-live` client surface and `voice_live_context`

**Verified, correcting the pre-audit “only a flag” reading.**

`methods_prompt.py` L541 `_CLIENT_SURFACES = {"hud", "voice-live"}`; L586–588 stores `session["voice_live_context"]` = first 6000 chars of `voice_context` **only if** `surface == "voice-live"`. Off-surface, context is cleared (tests `test_voice_context_ignored_off_the_live_surface`).

**What the text does:** `_hud_surface_note` (`session_notifications.py` L683–692) → `tools/voice_live.py` `voice_live_turn_note` L84–90. Prepended to **model input** (`prompt_turn.py` `_prepend_note` L513) as a spoken-delegation contract + optional recent transcript. **Not** barge-in detection. **Not** the audio transport.

**Separate integration:** `voice.voice_chat_mode: gpt-live` + `POST /api/audio/voice-live/session` **is** a full-duplex WebRTC session with OpenAI (`voice_live.py` L9–16). The flag and the Live session work together: renderer holds WebRTC; Hermes turn gets `voice_context` so “yes”/corrections have spoken history.

Default mode remains **chained**. GPT-Live is opt-in, billed on the OpenAI key (`voice_live.py` L20).

**Label:** `[PARTIAL]` `WINH09-AUD-07` (MEDIUM) — `voice_live_context` is prompt metadata for gpt-live delegations; GPT-Live itself is real duplex (OpenAI, not Gemini). Chained mode does not use that transport.

---

## 4. Barge-in during TTS (existence, not Living Voiceprint mechanics)

Living Voiceprint §1 excludes barge-in *mechanics*; this item only asks whether interruption **exists**.

`_tts_stream_stop(user_barge=True)` (`methods_voice.py` L117–134): sets stop event, `mark_speech_interrupted()` (`tts_streaming.py` L51–53). Next `prompt_turn` `_prepare_turn_input` L509–511 pops the latch (`take_speech_interrupted`, TTL 120s) and prepends `SPEECH_INTERRUPTED_NOTE`: *“the user interrupted your previous spoken reply before it finished.”*

Triggers: new turn barging the previous TTS pipeline (L106 `_tts_stream_stop` before a new `_tts_stream_begin`); full-duplex listener trip (`_full_duplex_listener` L173–196) when `voice.barge_in` is not disabled (default True, L158–161); `prompt.submit` `interrupted` param (`methods_prompt.py` L555–558); session keypress (`methods_session.py` ~1997). `user_barge=False` for `/voice off` so mode changes do not latch the note (L119).

**Label:** `[MATCH]` `WINH09-AUD-08` (MEDIUM) — barge-in cuts TTS and latches a next-turn model note. (Mechanics/policy of *multi-speaker* barge-in remain out of scope.)

---

## 5. One mic / one speaker per process vs WINH02 surfaces

`methods_voice.py` L1–2, L88–89: process-global voice state; one streaming TTS pipeline. `HERMES_VOICE` is **env**, never `config.yaml` (L16–17) so a prior session cannot auto-start REC.

**Implications:**

- Surfaces 2+3 (dashboard `/api/ws` + JSON-RPC) that share **one** `hermes serve` process share **one** mic and **one** speaker. Two Desktop windows / TUI + dashboard cannot both own capture. Wake has a single owner transport (`wake.start` vs `wake_owned` busy, L713–714).
- Surface 1 HTTP API and Surface 4 ACP are **other processes** — they do not share this mic; they also do not get `voice.record` unless they speak the JSON-RPC voice methods against the serve process.
- WINH03: Path B/C cannot share one spawned process — voice mode lives in the **serve** sidecar topology (WINH02 Path A/B), not in a second gateway process.

**Nuance:** default `voice.client_direct: True` (`config_defaults.py` L1144–1146) lets Desktop remote clients call STT/TTS **on the client** (credentials fetched over authenticated REST) instead of capturing on the `hermes serve` PID. Wake detection still has a single owner transport (`methods_voice.py` L309–312: first `wake.start` owns the mic until stop; on detection it emits `wake.detected` and **the client** opens capture).

Voice is viable on JSON-RPC **if** the Windows client owns capture (Desktop `client_direct` pattern) or is the sole process using `voice.record` on that sidecar. It is **not** viable as N independent `voice.record` clients against one Hermes PID. A headless sidecar with no local mic still needs the Windows app to capture locally and `prompt.submit` text — gateway `voice.record` would otherwise bind the wrong machine’s device.

**Label:** `[RISK]` `WINH09-AUD-09` (MEDIUM) — process-global mic/speaker (and single wake owner) conflicts with multi-client use of one `hermes serve` (WINH02 Surfaces 2/3). `client_direct` is an escape hatch if the Windows client owns capture. Cite WINH08 topology only as context; not re-derived.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH09-AUD-05 | PARTIAL | MEDIUM | `methods_voice.py`; `voice.py` L331; `prompt_turn.py` | Chained: VAD → file STT → `voice.transcript` → client `prompt.submit` |
| WINH09-AUD-06 | PARTIAL | MEDIUM | `voice_mode.py` L852; `tts_tool_speaker.py`; `tts_streaming.py` | STT batch after silence; TTS sentence-stream if streamer exists |
| WINH09-AUD-07 | PARTIAL | MEDIUM | `methods_prompt.py` L586–588; `voice_live.py` L1–20, L84–90 | Context is a prompt note; GPT-Live WebRTC is a separate OpenAI duplex mode |
| WINH09-AUD-08 | MATCH | MEDIUM | `methods_voice.py` L117–134; `tts_streaming.py` L51–60 | Barge-in stops TTS and latches next-turn interrupt note |
| WINH09-AUD-09 | RISK | MEDIUM | `methods_voice.py` L1–2, L16–17 | One mic/speaker per process; JSON-RPC voice assumes that topology |
