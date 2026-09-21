# WINH09 Audit 05 — Conversational Attention Authority (Directed-Speech Detection)

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Master Plan **§12 Conversational Attention Authority** — reserved from WINH07. Wake words are a **fallback**; primary is “was that speech meant for me” from context. Attention Dampening §9/9a remains series-excluded (INFO only if encountered).

---

## 1. Wake-word-free directed-speech detection

Hermes voice activation is a **literal wake-word (or equivalent) gate**, not a directed-speech classifier.

- Config is **top-level** `wake_word.enabled` default **False** (`config_defaults.py` L1161–1178). Engines: `openwakeword` (default) / `sherpa` / `porcupine`. Phrase label `"hey hermes"` (L1173); openWakeWord model `hey_hermes` (L1184).
- Gateway: `wake.start` / `wake.stop` (`methods_voice.py` L449+). Process-global detector, one mic; first eligible transport owns it (L309–312). On detection Hermes emits `wake.detected`; **the client** opens a session and its own capture — the gateway does not score addressee intent. Env `HERMES_VOICE` is the voice-mode flag (never yaml, L16–17).
- Hands-free is: keyword → client capture → file STT. **Not** “always listen and score whether speech was meant for me.”
- No search hits for directed-speech, addressee detection, “meant for me,” gaze, or conversational-attention scoring in the voice stack. Pause timing exists only as **VAD `silence_duration`** (default 3.0s, `voice` L1151) to end an utterance, not to score addressee.

A wake word satisfies §12’s **fallback**, not the primary requirement. Labeling this `[MATCH]` would be incorrect.

**Label:** `[GAP]` `WINH09-AUD-14` (HIGH) — activation is wake-word (or push-to-talk / toggle) only; no context-based directed-speech detection.

---

## 2. Confidence-tiered outcomes

§12: high → process; medium → lightly clarify; low → ignore or silently retain.

Hermes wake/voice is **binary**: keyword fired → listen/transcribe; else stay idle. OpenWakeWord/porcupine may have internal detector scores, but they are **not** mapped to three product outcomes (no medium “did you mean me?” turn; no silent retain of off-address speech for later).

STT may return text confidence from some vendors; that is **transcription quality**, not addressee confidence.

**Label:** `[GAP]` `WINH09-AUD-15` (MEDIUM) — no graduated addressee confidence; wake is on/off.

---

## 3. Continuation without re-invocation

After a turn, does the user need another wake word?

**Two different surfaces:**

**CLI / classic voice loop** (`tools/voice_mode.py` / `config.yaml` `wake_word.start_new_session`): can keep a session; wake may re-arm each utterance depending on `start_new_session` (default **True** at L1178 — a new session per wake). Continuation without wake is **not** the default CLI story.

**JSON-RPC gateway (Windows-relevant):** `voice.record` uses `start_continuous(..., auto_restart=False)` (`methods_voice.py` L747–752 — record-once per start). `_vr_transcript` (L685–687) emits the transcript then `_resume_voice_wake()` — that re-arms **wake listening** as soon as capture ends, not a free-running STT continuation window. Desktop-style path: `wake.detected` → client capture → one utterance → STT → client `prompt.submit` → TTS → **wake listening again** unless the client immediately re-calls `voice.record`. That is **re-invocation per turn**, not a §12 continuation window.

`voice.barge_in` + `_full_duplex_listener` can interrupt TTS while already in a voice turn; it does not keep the mic in “addressed conversation” after the turn completes without a new wake.

Push-to-talk / `voice.record` without wake: client can start recording again without a keyword — that is **client UX**, not Hermes addressee logic.

**Label:** `[PARTIAL]` `WINH09-AUD-16` (MEDIUM) — gateway default re-arms wake after the turn (`auto_restart=False` + `_resume_voice_wake`); no first-class continuation window. Client could omit wake and re-`voice.record` (not §12).

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH09-AUD-14 | GAP | HIGH | `config_defaults.py` L1161–1178; `methods_voice.py` L309–312, `wake.start` | Wake-word is the primary gate, not directed-speech |
| WINH09-AUD-15 | GAP | MEDIUM | wake engines; no confidence tiers in voice state machine | Activation is binary |
| WINH09-AUD-16 | PARTIAL | MEDIUM | `methods_voice.py` `auto_restart=False`; `_resume_voice_wake` | After a turn, wake re-arms; no continuation window |
