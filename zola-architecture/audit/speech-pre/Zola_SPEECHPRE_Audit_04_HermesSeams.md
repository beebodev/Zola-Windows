# SPEECH-PRE Audit 04 — Supported Hermes integration points (VD-1)

Hermes pin `345cd2b057a452236de401d3534b8502a7465e8d`. No Hermes edit proposed. Labels [MATCH]/[GAP]/[RISK].

---

## 1. Disarm Hermes TTS while client still receives reply text

| Mechanism | Evidence | Label |
|-----------|----------|-------|
| Runtime `HERMES_VOICE_TTS` via `voice.toggle` action `tts` / off | `_tts_stream_begin` returns `None` when TTS off (`methods_voice.py:95–98`); deltas still `_emit("message.delta")` (`prompt_turn.py:523–531`) | **[MATCH]** for turn streaming TTS |
| Profile cannot permanently “TTS off, deltas on” as a single key | Flags are runtime env, not config.yaml (`methods_voice.py:16`) | **[RISK]** LOW — session must keep TTS off after sync; client `SyncVoice*` historically re-enables TTS |
| `voice.tts` RPC ignores `HERMES_VOICE_TTS` | Always starts `_speak_text_with_barge` (`methods_voice.py:765–775`) | **[RISK] HIGH** — SPEECHPRE-AUD-05 |

**Missing for a full disarm:** a supported way to make `voice.tts` a no-op while keeping reply text (without Hermes edit). Workaround without edit: client stops calling `voice.tts` and owns those speaks.

---

## 2. Disarm Hermes mic and wake so serve never opens capture

| Mechanism | Evidence | Label |
|-----------|----------|-------|
| Never call `wake.start` / `voice.record`; Text mode / lock already stop | Client `DisarmWakeAsync`, `EnterTextModeAsync` | **[MATCH]** if client + owner never arm Hermes capture |
| `wake_word.enabled: false` in profile | Hermes won’t accept start when disabled | **[MATCH]** profile option |
| `voice.toggle off` stops continuous | `stop_continuous` (`methods_voice.py:640–648`) | **[MATCH]** |
| Serve may still open mic if anything calls wake/record | Wake daemon holds InputStream when armed | **[RISK]** — dual-open if owner and Hermes both active |

**SPEECHPRE-AUD-15 [MATCH]** — Supported path: profile wake off + client never starts Hermes capture + voice mode strategy that never opens PortAudio input. **[GAP]** — no single “audio_owner_active” RPC that guarantees serve never opens devices.

---

## 3. Reply text deltas + complete + turn/reply id

| Item | Evidence | Label |
|------|----------|-------|
| Deltas | `message.delta` `{text}` (+ optional `rendered`) (`prompt_turn.py:526–531`; `ChatSocket.cs:717–721`) | **[MATCH]** |
| Complete | `message.complete` (`ChatSocket.cs:724–727`) | **[MATCH]** for reply-text-complete |
| Turn/reply id on delta | Payload is text only; session via emit sid; no stable `reply_id` on deltas | **[GAP] MEDIUM** — SPEECHPRE-AUD-16 |
| Client accumulation | VC accumulates reply for echo haystack; no Cartesia-style context id | — |

Owner can mint its own reply ids from session/turn boundaries when complete arrives; correlating mid-stream late audio needs a client-assigned id (spike pattern).

---

## 4. Tool-call events / pre-tool acknowledgement (S51F-D02)

| Item | Evidence | Label |
|------|----------|-------|
| Events | `tool.start`, `tool.complete`, `tool.generating` (`ChatSocket.cs:44–47`; MainWindow handlers) | **[MATCH]** |
| Spoken ack without Hermes edit | Client can speak fixed/own-words on `tool.start` via owner (or today `voice.tts`) once TTS path is owned | **[MATCH]** — no Hermes change required for the event seam |
| Content of ack | S51F-D02: her own words / SOUL — product, not Hermes RPC | INFO |

**SPEECHPRE-AUD-17 [MATCH]** — Tool events visible; spoken pre-tool ack can be produced client-side once owner speaks.

---

## 5. Submit admitted transcript as voice vs typed

| Item | Evidence | Label |
|------|----------|-------|
| Same RPC | Both paths `prompt.submit` (`MainWindow` / `ChatSocket.cs:310–316`) | **[MATCH]** |
| Voice mode differences | SOUL speaking rules when Hermes voice mode on; clarify UI bind is client-side | **[MATCH]** / product |
| Origin ticket | `zola_workspace` wrap of `prompt.submit` (P9-FIX-ARM) | Must keep |

**SPEECHPRE-AUD-18 [MATCH]** — One submit path; owner must feed admission → same `prompt.submit`.

---

## 6. Cancel turn / late emissions

| Item | Evidence | Label |
|------|----------|-------|
| Cancel | `session.interrupt` → `_tts_stream_stop` then interrupt agent | **[MATCH]** |
| After cancel | May still see late deltas/complete depending on race; client FinishTurn interrupted | **[RISK]** LOW — owner must drop late TTS by reply id (spike rule) |
| Stop speaking | `voice.toggle off` cuts TTS without latch (`user_barge=False`) | **[MATCH]** for cut |

---

## 7. Still makes sound / opens mic with TTS+mic “disarmed”

| Path | With turn TTS off + no wake/record | Label |
|------|--------------------------------------|-------|
| `voice.tts` | Still speaks | **[RISK]** AUD-05 |
| Beeps / thinking | Off in TEMPLATE | **[MATCH]** gated |
| Heartbeat / loop turns | Can produce `message.complete` (WINH07 / A01 Q1) | **[RISK]** MEDIUM — SPEECHPRE-AUD-19: if client re-enables TTS for those, they speak; if TTS stays off, text only |
| Gateway auto-TTS / messaging platforms | Not the Windows `/api/ws` ordinary path | INFO |
| Code Zira | Separate | Keep (R1) |

---

## Summary matrix (for synthesis)

| Seam | Label |
|------|-------|
| TTS disarm (turn stream) | MATCH |
| TTS disarm (`voice.tts`) | RISK |
| Mic+wake disarm | MATCH (ops) / GAP (no single guarantee RPC) |
| Reply deltas | MATCH |
| Reply complete | MATCH |
| Reply id on wire | GAP |
| Tool events | MATCH |
| Voice submit | MATCH |
| Cancel | MATCH |
| Residual sound | RISK (`voice.tts`, heartbeat if TTS on) |
