# WINH09 Phase 6 — Synthesis: Voice Pipeline & Voice Identity

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Document of Truth: Master Plan §3 Current Sequential Model only (not Long-Term Streaming), §12 Conversational Attention Authority, External API Strategy Tier 1, `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` (capability requirements, not Android libraries). Cross-refs: WINH02 surfaces, `WINH03-AUD-02`, WINH08 topology (cite, not re-derived).

Source: Audit_02 VoiceProviderLandscape, Audit_03 VoicePipelineArchitecture, Audit_04 VoiceIdentity, Audit_05 ConversationalAttentionAuthority.

Section 5 questions are not resolved here.

---

## Section 1 — Finding Summary Table

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH09-AUD-01 | PARTIAL | MEDIUM | `tts_registry.py` L25–28; `tts_tool_providers.py` L219–229; `tts_streaming.py` L173–193 | ElevenLabs built-in file + PCM streamer; ABC `stream()` still default-unimplemented |
| WINH09-AUD-02 | PARTIAL | MEDIUM | `transcription_registry.py` L23–25; `transcription_command.py` L31–41 | No Cartesia/Deepgram built-in; command or plugin (file STT) |
| WINH09-AUD-03 | MATCH | LOW | `config_defaults.py` L1008; `plugins.py` L1051–1061 | Built-in `tts.provider` / `stt.provider` swap by config |
| WINH09-AUD-04 | PARTIAL | MEDIUM | `tts_provider.py` L58–73; `tts_streaming.py` L142–159 | No latency catalog; `streaming.provider` auto/pin only |
| WINH09-AUD-05 | PARTIAL | MEDIUM | `methods_voice.py`; `voice.py` L331; `prompt_turn.py` | Chained: VAD → file STT → `voice.transcript` → client `prompt.submit` |
| WINH09-AUD-06 | PARTIAL | MEDIUM | `voice_mode.py` L852; `tts_tool_speaker.py`; `tts_streaming.py` | STT batch after silence; TTS sentence-stream if streamer exists |
| WINH09-AUD-07 | PARTIAL | MEDIUM | `methods_prompt.py` L586–588; `voice_live.py` L1–20, L84–90 | Context is a prompt note; GPT-Live WebRTC is a separate OpenAI duplex mode |
| WINH09-AUD-08 | MATCH | MEDIUM | `methods_voice.py` L117–134; `tts_streaming.py` L51–60 | Barge-in stops TTS and latches next-turn interrupt note |
| WINH09-AUD-09 | RISK | MEDIUM | `methods_voice.py` L1–2, L16–17, L309–312 | One mic/speaker per process; JSON-RPC voice assumes that topology |
| WINH09-AUD-10 | GAP | HIGH | searched agent/tools/tui_gateway; `transcription_cloud.py` L260, L318 | No speaker-identity / embedding tracker |
| WINH09-AUD-11 | GAP | HIGH | same search | No voice enrollment (ambient or formal) |
| WINH09-AUD-12 | RISK | MEDIUM | `transcription_provider.py`; `voice_live.py`; WINH02 surfaces | On-device identity would not be structurally enforced |
| WINH09-AUD-13 | GAP | MEDIUM | `methods_prompt.py` prompt.submit | Turns are single-author for voice; no speaker field |
| WINH09-AUD-14 | GAP | HIGH | `config_defaults.py` L1161–1178; `methods_voice.py` L309–312 | Wake-word is the primary gate, not directed-speech |
| WINH09-AUD-15 | GAP | MEDIUM | wake engines; no confidence tiers in voice state machine | Activation is binary |
| WINH09-AUD-16 | PARTIAL | MEDIUM | `methods_voice.py` L747–752, L685–687 | After capture, wake re-arms; no continuation window |

**Counts:** 16 findings — **3 HIGH**, **12 MEDIUM**, **1 LOW**.

HIGH: AUD-10, AUD-11, AUD-14. MEDIUM: AUD-01, 02, 04, 05, 06, 07, 08, 09, 12, 13, 15, 16. LOW: AUD-03.

---

## Section 2 — What Hermes covers as-is (voice pipeline / voice identity)

**Direct answer to the developer question (restated from Audit_02):** Zola-Windows does **not** need to integrate ElevenLabs from scratch. Hermes already ships ElevenLabs TTS (`tts.provider: elevenlabs`, file convert + `ElevenLabsStreamer` PCM) and ElevenLabs Scribe STT. Cartesia and Deepgram are **not** built-ins; add them with `type: command` in `config.yaml` or a plugin class. Gemini Live is **not** Hermes’s live mode — that is OpenAI GPT-Live (`voice.voice_chat_mode: gpt-live`). Default chained mode (STT → Hermes turn → TTS) already matches Master Plan §3’s *current* sequential model.

**Provider abstraction (voice).** Built-in names swap by config (`WINH09-AUD-03`). ElevenLabs’s full vendor catalog is not on the ABC (`WINH09-AUD-01`). There is no latency/cost metadata table (`WINH09-AUD-04`). STT ABC is file-based (`WINH09-AUD-02`).

**Pipeline.** Chained live voice: VAD utterance → WAV → `transcribe_recording` → `voice.transcript` → **client** `prompt.submit` into the same `prompt_turn.py` loop as typed chat (`WINH09-AUD-05`). STT waits for silence; TTS can start per sentence when a streamer exists (`WINH09-AUD-06`). `voice_live_context` is a 6000-char model note, not the audio bus; GPT-Live is a separate OpenAI WebRTC path (`WINH09-AUD-07`). Barge-in exists: cut TTS, latch `SPEECH_INTERRUPTED_NOTE` for the next turn (`WINH09-AUD-08`). One mic and one speaker per process, plus a single wake-owner transport (`WINH09-AUD-09`). `voice.client_direct` lets a Desktop-style client run STT/TTS locally instead of capturing on the sidecar PID.

**Voice identity.** Hermes has **no** in-session speaker tracker, enrollment, embedding pool, or per-utterance speaker field (`WINH09-AUD-10`, `11`, `13`). Optional cloud STT `diarize` flags are off by default and do not feed session identity. That is a capability gap, not “missing CampPlus.”

**Attention authority (§12).** Wake-word (or PTT / `/voice on`) is the primary gate (`WINH09-AUD-14`). No high/medium/low addressee confidence (`WINH09-AUD-15`). Gateway `auto_restart=False` plus `_resume_voice_wake` after capture means the next utterance typically needs wake or another `voice.record` (`WINH09-AUD-16`).

---

## Section 3 — What needs a Zola-built adapter layer

For each `[PARTIAL]` or `[MATCH]`-with-caveats: wrap Hermes rather than replace it.

| ID | Wrap | Adapter owns |
|---|---|---|
| AUD-01 / AUD-03 | Built-in `tts.provider` / ElevenLabs file + `ElevenLabsStreamer` | Pin provider + voice/model in config; do not fork an ElevenLabs SDK unless quality/latency demands it (WINH00 Q1) |
| AUD-02 | `stt.provider` + `register_transcription_provider` / `type: command` | Only if Windows requires Deepgram/Cartesia streaming STT: plugin (still file ABC) or a client-side streamer that submits text |
| AUD-04 | `tts.streaming.provider` auto/pin | Product choice of Edge vs ElevenLabs vs streamer list; measure latency outside Hermes |
| AUD-05 / AUD-06 | Gateway `voice.*` + `prompt.submit` + `stream_tts_to_speaker` | Windows client: VAD/capture (or `client_direct`), map `voice.transcript` → `prompt.submit`, speak deltas. Accept batch STT as §3 current model |
| AUD-07 | `voice_live_context` note; optional `gpt-live` | Do not treat the note as Gemini Live. Only enable GPT-Live if WINH00 Q2 says duplex is in scope |
| AUD-08 | `_tts_stream_stop` / `mark_speech_interrupted` | Keep barge-in; Windows owns mic policy. Multi-speaker barge-in mechanics remain out of this document’s scope |
| AUD-09 | JSON-RPC voice methods | Own capture in the Windows process; do not share `voice.record` across N clients of one `hermes serve`. Prefer Path A/B sidecar + local mic (`WINH02`/`WINH03`) |
| AUD-16 | Client re-`voice.record` after a turn | If Windows wants a continuation window, implement it in the client (keep listening after TTS) — Hermes will not |

`WINH09-AUD-03` and `WINH09-AUD-08` are matches: adapter is config and client wiring, not a replacement module.

---

## Section 4 — What must be built from scratch

Phase 4 (Voice Identity) is **near-total scratch work** if the Living Voiceprint *capabilities* are in scope for this integration. That is not softened: Hermes has nothing to wrap for speaker tracking or enrollment. Android `CampPlus` / sherpa-onnx / `AudioRecord` are implementation choices Windows would not copy anyway; the missing **capabilities** are:

| ID | Capability | Why scratch | Finding |
|---|---|---|---|
| In-session speaker tracking | Who is speaking, continuously, during a session | No embedding store, tracker, or `SpeakerEvent` equivalent | AUD-10 |
| Enrollment (ambient or formal) | Register a voice; UNKNOWN-cluster gate | Single-user/single-mic by design | AUD-11 |
| On-device-only voiceprint invariant | Embeddings never leave the machine | No tracker today; cloud STT/Live + remote gateway would leak audio/identity unless Windows owns local embeddings and never uploads them | AUD-12 (constraint on whatever is built) |
| Per-utterance speaker field / room model | Turn attributed to a speaker | `prompt.submit` is one `user` text; `_turn_author` is bot-relay, not voice | AUD-13 |
| Directed-speech detection | “Was that meant for Zola?” without a wake word | Wake is the primary gate | AUD-14 |
| Addressee confidence tiers | High / medium clarify / low ignore-or-retain | Binary wake | AUD-15 |

If WINH00 defers voice identity the way environmental awareness was deferred, these gaps stay findings of record but drop out of the build plan — that is Question 3, not resolved here.

Deepgram/Cartesia/Gemini Live as *named vendors* are not scratch *voice I/O* (Hermes already speaks and hears). They are scratch only if the product insists on those vendors’ live streaming APIs rather than Hermes’s file STT + built-in TTS.

---

## Section 5 — Open questions for WINH00

Do not resolve these here.

1. **Provider choice.** Given Audit_02: does Zola-Windows use Hermes’s built-in ElevenLabs TTS as-is (or Edge as the free default), or is a specific voice quality/latency requirement strong enough to warrant a custom Cartesia/Deepgram plugin from day one?

2. **Full-duplex transport.** Is native full-duplex audio (Gemini-Live-style) actually a Windows-track requirement, given Master Plan §3’s current model is STT → Reasoning → TTS? Hermes’s GPT-Live is OpenAI, not Gemini, and chained mode already matches the current sequential model. If duplex is only a zola-main/Android detail, `WINH09-AUD-07` is a non-issue for Windows, not a gap to close.

3. **Voice identity scope.** Phase 4 is a near-total capability gap (`WINH09-AUD-10`–`13`). Is a Windows-native voiceprint system in scope for this integration at all, or is it deferred the way environmental awareness was for the whole series? If deferred, record it under “Recorded scope decisions” so WINH10–12 / WINH00 do not re-raise it.

4. **Process topology vs voice.** `WINH09-AUD-09` (one mic/one speaker per process, single wake owner) plus `WINH08` subagent/surface routing and WINH02/03 paths: does that narrow the Windows client to a single JSON-RPC owner of capture (Desktop-style Path A/B, likely `client_direct` / local mic), and rule out N dashboard+TUI voice clients against one `hermes serve`? Surface 1 HTTP and Surface 4 ACP still do not carry this voice state machine unless they speak the gateway voice methods.
