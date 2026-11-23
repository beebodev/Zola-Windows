# SPEECH-PRE Audit 07 — Conversation boundary (port later)

Against: SP-D10; one authority per responsibility. Nuplex direction = background for Q3 only.

---

## 1. Narrowest boundary

**Zola → conversation layer**

| Message | Existing type/RPC |
|---------|-------------------|
| Reply text streaming | `message.delta` |
| Reply text complete | `message.complete` |
| Turn start | `message.start` |
| Cancel / stop speaking | `session.interrupt` / stop path (`voice.toggle off` today) |
| Tool activity | `tool.start` / `tool.complete` |
| Unprompted speak request | Today `voice.tts` via proactive session — must move behind same speak interface |
| Code-read | Local Zira — exclude or separately own (R1) |

**Conversation layer → Zola**

| Message | Mapping |
|---------|---------|
| Candidate Brian words + capture metadata | Client-local into `CaptureLifecycle` + `TranscriptAdmission` (not Hermes `voice.transcript` after cutover) |
| Admitted turn | `TranscriptReady` → `prompt.submit` |
| Clarify-bound answer | `Admit(ClarifyId)` → `ApplyVoiceClarifyAnswer` |
| She has finished / outcomes | New IPC events (`safe_to_listen`, released outcomes); consumers: follow-up, presence |
| Cancel / no-speech / failure | Existing lifecycle cancel reasons |

SP-D10: Brian’s words in; her reply text, “she has finished,” outcomes out.

---

## 2. Brian’s own wording (send approval / save-phrase)

| Step | Evidence |
|------|----------|
| Passphrase | `send_gate.py:23–24` `PASSPHRASE_TOKENS`; `passphrase_match` `:131–138` |
| Authorize | `on_pre_llm_call` uses `user_message` (`:614–641`) |
| Source | `TurnRecord.user_message` from submitted turn (`turn_context.py`) |
| Client | Admitted transcript → `SubmitTurnAsync` → `prompt.submit` |
| Save-phrase | `guards.py` `SAVE_INTENT_PHRASES` / `_user_message_for_turn` |

| Label | Finding |
|-------|---------|
| **[MATCH]** | Spoken send approval and save-phrase read **admitted submitted text on the Zola/Hermes turn record**, not TTS or spike-internal STT stores |
| **[GAP]** | After cutover, any submit that skips `TranscriptAdmission` breaks SP-D10 |
| **[RISK]** | Conversation layer rewrite/normalize before hand-off, or dual-fire with live `voice.transcript`, feeds wrong string to passphrase |

**SPEECHPRE-AUD-22 [MATCH]** — Wording authority is Zola-side admitted text (P8-D06 / P8-D09).

---

## 3. Listening vs speaking separation (facts/seams)

- Spike already splits `AudioOwner` vs `Listener`; coupling via `SpeakingGate(speaking=…)`.
- Listener can take `gate=None` (always open) — seam for listen-only / later wake listener.
- Speak-only: owner without feeding Listener.
- **INFERENCE (seam):** later wake-listener must reuse same process or accept second mic consumer — device exclusivity is the hard constraint.
- Background only: Nuplex may later own conversation; local listen may become wake-only — no finding.

---

## 4. Hard wires that make swap a rebuild

| Hard wire | Why |
|-----------|-----|
| All capture via `voice.record` / `wake.*` (`VoiceController`) | Assumes Hermes state machine |
| Transcript ingress only `voice.transcript` | Dual path if left live |
| Speaking presence = ffplay under serve PID (`TtsPlaybackMonitor`) | Mouth tied to serve playback |
| Follow-up timing from monitor debounce | Must retarget to `safe_to_listen` |
| Proactive via `voice.tts` | Bypasses owner unless routed |
| Code-read Zira | Second speaker |
| CaptureLifecycle Hermes status strings | Assumes serve recorder |
| Deepgram profile TTS | Owner fights serve audio if not disarmed |

**SPEECHPRE-AUD-23 [RISK] HIGH** — Without retiring/gating Hermes voice RPCs and ffplay-monitor listen authority, cutover is a control-plane rebuild, not a port of the spike interface.
