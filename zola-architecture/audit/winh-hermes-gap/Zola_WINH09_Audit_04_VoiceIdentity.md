# WINH09 Audit 04 — Voice Identity: Speaker Tracking & Enrollment

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` in full. **Capability requirements only** — not Android `CampPlus` / sherpa-onnx / `AudioRecord` as things Hermes must literally ship. Out of scope per that document §1 (and this phase): camera identity, cloud voiceprint sync as a product feature to implement, post-session diarization, barge-in mechanics.

---

## 1. Continuous in-session speaker tracking

**Requirement:** identify *who* is speaking during a session (embeddings, voiceprint, or equivalent), not treat all audio as one undifferentiated user.

**Search performed at this pin (Hermes tree, not exhaustive of every comment, but all production names):**

| Search | Result |
|---|---|
| `CampPlus`, `VoiceEmbeddingStore`, `LiveSessionIdentityTracker`, `SpeakerEvent`, `voiceprint` | **No hits** in `*.py` / `*.md` production paths |
| `speaker_id` | Piper TTS **output voice** (`neutts`/piper config), not listener identity |
| `diariz` | xAI STT `diarize` default **False** (`tools/transcription_cloud.py` L260); ElevenLabs Scribe `diarize` default **False** (`config_defaults.py` L1118, posted in `transcription_cloud.py` L318) — **STT vendor flags**, not a Hermes identity store, not wired into session turns |
| `speaker embedding`, `speaker tracking`, `enroll` (voice) | No embedding pool / UNKNOWN cluster gate |
| `openwakeword` / porcupine / sherpa wake | Wake-word **detection**, not speaker ID |

Hermes chained voice treats the mic as **one user**. GPT-Live likewise has no Hermes-side speaker field. There is **no** equivalent capability a Windows-native tracker could wrap.

**Label:** `[GAP]` `WINH09-AUD-10` (HIGH) — no in-session speaker identification / embedding tracker. Searched CampPlus, VoiceEmbeddingStore, LiveSessionIdentityTracker, SpeakerEvent, voiceprint, diarize (vendor flags only), speaker_id (TTS).

---

## 2. Enrollment (formal or ambient)

No register-this-voice flow, no ambient cluster that becomes a named speaker, no UNKNOWN-gate then enroll. Wake-word training (openWakeWord custom models, if any) is **keyword**, not biometric enrollment.

Hermes is **single-user / single-voice by design** for the agent loop: one session author, one `USER.md` profile, one mic.

**Label:** `[GAP]` `WINH09-AUD-11` (HIGH) — no formal or ambient voice enrollment.

---

## 3. Privacy / on-device (forward-looking, even with no tracker)

Living Voiceprint: embeddings stay on-device; never cloud-sync.

Hermes **would not structurally guarantee** that if a tracker were added naively:

- Default STT can be **cloud** (Groq, OpenAI, ElevenLabs, xAI) — raw audio leaves the machine (`TranscriptionProvider.transcribe` file upload).
- GPT-Live sends audio to OpenAI WebRTC.
- Gateway/dashboard can be remote (`WINH02` Surfaces 2/3); a future identity payload on those events would leave the device unless the Windows client owned capture+embeddings **before** JSON-RPC.
- Local STT (`stt.provider: local`) and local TTS (Edge, Piper, KittenTTS) **can** stay on-box, but that is **config**, not an invariant.

There is no existing voiceprint blob to leak today. Any Windows tracker must own: local embeddings, never attach them to `prompt.submit` / cloud STT, never persist them via memory providers that sync.

**Label:** `[RISK]` `WINH09-AUD-12` (MEDIUM) — no tracker yet; Hermes’s default cloud STT/Live + remote gateway make an on-device-only identity guarantee a **Windows-owned** constraint, not something the current architecture enforces.

---

## 4. Multi-speaker room / per-utterance speaker field

A Hermes turn is **one user text** + assistant reply. `prompt.submit` payload is `text` (and optional `voice_context` for gpt-live) — **no** `speaker_id` / `speaker_label` on the turn (`methods_prompt.py`). Session messages are role `user`/`assistant`/`system`, not room-attributed.

`_turn_author` exists (`methods_prompt.py` L565–568) but is a **messaging-surface** stamp (`tools/bot_relay.py` `DeliveryAuthor`) that clients cannot set (error 4124). It is not voice-biometric attribution.

xAI/ElevenLabs diarization, if enabled, would live inside a **transcript string**, not a first-class session field Hermes reasons over. Piper `speaker_id` is TTS.

**Label:** `[GAP]` `WINH09-AUD-13` (MEDIUM) — turn model is single-author for voice; no per-utterance speaker field.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH09-AUD-10 | GAP | HIGH | searched agent/tools/tui_gateway; `transcription_cloud.py` L260, L318 | No speaker-identity / embedding tracker |
| WINH09-AUD-11 | GAP | HIGH | same search | No voice enrollment (ambient or formal) |
| WINH09-AUD-12 | RISK | MEDIUM | `transcription_provider.py`; `voice_live.py`; WINH02 surfaces | On-device identity would not be structurally enforced |
| WINH09-AUD-13 | GAP | MEDIUM | `methods_prompt.py` prompt.submit | Turns are single-author; no speaker field |
