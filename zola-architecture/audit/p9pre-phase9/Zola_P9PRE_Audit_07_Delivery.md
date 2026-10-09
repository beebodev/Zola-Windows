# Zola P9PRE Audit 07 — Proactive Delivery and the HUD

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Labels vs:** `A2`, `P2-D01`, `P3-D06`, `P4-D01`, `P4-D02`, `P4-D29`, `P7-D01`–`P7-D04`, `S25`, `S26`, `S70`

---

## 1. Events the client accepts (LEAD-6)

`ChatSocket.DispatchEvent` (`ChatSocket.cs` L633–758) handles: `message.start`, `message.delta`, `message.complete`, `status.update` (status line, not the bubble), `error`, voice status, voice transcript, voice interrupted, wake, `request.cancel`, `tool.start`, `tool.complete`, `tool.generating`, `tool.output.risk`. The default branch returns without appending (`L756–758`). `reasoning.delta` is explicitly dropped. There is no `review.summary` case. A heartbeat `status.update` (`session_notifications.py` L222, `kind: heartbeat`) would hit the status line if the session id matches. It is not spoken by that branch.

`A2` names extra speech paths the architecture accepts: `review.summary`, child-session completes, heartbeat events. The client code speaks from `message.*` completion and from its own `voice.tts` calls, not from an unrecognized event type.

**LEAD-6: CONFIRMED.** `PluginContext.emit` (`hermes_cli/plugins.py` L955–974) publishes `<plugin_key>:<event>` on the in-process plugin bus. It does not call `tui_gateway.server._emit`. The server does emit events the client did not start: `review.summary` (`tui_gateway/server.py` L1004–1006), `status.update` with `kind` heartbeat / loop / process, `subagent.complete`, and session-less broadcasts (`skin.changed`, `cron.changed`, `session.reclaimed`, others). The client switch has no case for `review.summary` or `subagent.complete`, so those are dropped (L756–758).

**P9PRE-AUD-36 [GAP] HIGH** — a plugin cannot push an event the client will speak. `emit` stays in-process. `A2`'s extra paths are gateway events; the client drops unknown types. `S66`.

---

## 2. Delivery shapes

**(a) Client poll + template.** `voice.tts` (`tui_gateway/methods_voice.py` L765–775) requires `text`, starts `_speak_text_with_barge` on a daemon thread, and returns `{status: speaking}`. The client already calls it for clarify questions (`VoiceController.cs` L646–648) after it has checked Voice mode and TTS on (L610–620). `TtsPlaybackMonitor` (`TtsPlaybackMonitor.cs` L7–8) watches owned ffplay sessions for presence. It does not report completion to serve (`S70`). Playback ownership is the client's monitor plus Hermes's speaker thread. `P2-D01`: the client owns the microphone; TTS is Hermes's voice path invoked by RPC.

**(b) Synthetic model turn.** `_run_prompt_submit` (`prompt_turn.py` L796) is how heartbeat and /loop enter the session agent (audit 02, AUD-21). On Zola's serve that agent is `platform == "tui"` with no parent, so `is_brian_turn` is true and Workspace tools are allowed (`P8-D02`). `prompt.submit` is a separate client RPC (`methods_prompt.py` L544+). Heartbeat does not use that RPC. A client-supplied `_turn_author` on `prompt.submit` is refused. The prompt is stored as a user turn through `_admit_prompt_turn`. Pending rows and episodes are written from user/assistant text by `zola_memory`.

**P9PRE-AUD-37 [RISK] HIGH** — a synthetic turn on the TUI agent can pass the Brian-only gate and can be stored as a user turn. `P8-D02`, `P7-D01` is about transcripts, not about this prompt path. The prompt path has no "this text is not Brian" flag.

**(c) Next turn only.** `prefetch` and `pre_llm_call` context already inject into the user message (audit 06). No new socket event. Nothing is spoken until Brian talks. Lock and quiet hours do not apply to text that waits.

---

## 3. What can block speech

| Condition | Where it lives |
|-----------|----------------|
| Windows lock | `SessionLockWatcher` WTS lock (`SessionLockWatcher.cs` L17, L84). Display: mic paused (`ZolaDisplayState.cs` L380–382). `P4-D01` / `P4-D02`. |
| Backend down | `ShowUnreachable`; capture gate `BackendReachable=false` (audit 01). |
| Text mode | `VoiceController` refuses TTS questions when `Mode != ModeVoice` (L610–614). Admission drops `ModeText` (`TranscriptAdmission.cs` L73–76). |
| Open capture / turn / clarify | admission: no outstanding capture, cancelled, settled, turn running unbound, clarify not active (L78–108). |
| Playback | `TtsPlaybackMonitor` bout/segment flags; follow-up waits for quiet after a bout (`VoiceController` reply-release comments, `P4-D18`). |
| Reviewed draft | in serve memory (`send_gate.py`). The client does not read it before `voice.tts`. |
| Minimized window | `ZolaDisplayState.UpdateWindowFacts` records window facts (audit 01). Not a `voice.tts` check. |

`voice.tts` itself does not check the lock. The clarify caller checks mode. A new caller could invoke the RPC without those checks. The RPC is on the local socket, which requires the dashboard token.

---

## 4. Her voice and the next listen

`TranscriptAdmission.Decide` drops echo after the lifecycle checks (`L110–112`). `IsEchoOfLastReply` (`VoiceController.cs` L3196–3220) compares the transcript to `_echoHaystack` or `_accumulatedReply`. The haystack is filled from the last reply accumulation (`L3188–3193`), which is the model reply path. A `voice.tts` call that does not update `_echoHaystack` leaves echo detection aimed at the previous reply.

Unprompted speech does not by itself open a capture. Admission drops transcripts with no outstanding capture (`NoOwner`). A follow-up listen armed after unprompted speech would be a new capture; echo safety then depends on the haystack matching what was just spoken.

**P9PRE-AUD-38 [RISK] MEDIUM** — echo rejection is tied to the last accumulated reply, not to every `voice.tts` text. `P7-D01`. `S70` still has no completion signal, so "he heard it" is not knowable.

---

## 5. Presence

The client knows lock (WTS), window focus facts (`UpdateWindowFacts`), and whether the socket is up. `GetLastInputInfo` is not referenced in the client files searched. Idle time is **UNCONFIRMED** in this tree. `[EXT]` for that API was not fetched.

---

## 6. Quiet hours

Phase 1 effective config has no quiet-hours key. `time_context` can name "now" and the zone. No gate reads a start/end hour.

---

## 7. HUD

Visible slots in `MainWindow.xaml`: a HUD layer (L33–35), `StatusText` (L93), a session label (`SESSION` / `SESSION —`, `MainWindow.xaml.cs` L59–60). Presence mode includes `Dormant` when unreachable (audit 01). `P3-D06`: the HUD needs a real source. `workspace_status` is a tool result, not a HUD binding found in this pass. Watcher health is not a field. The honest signals today are socket health (backend up/down) and, if a file or tool exposed it, poll time and `needs_reconnect` from `store_status` (audit 03). The client does not read `store_status` on a timer.

**P9PRE-AUD-39 [GAP] MEDIUM** — no observed watcher-health source on the HUD. `S25`, `P3-D06`. Backend-down is already shown (audit 01, AUD-03).

Spoken "how's the email watcher?" would be a tool or an injection. The same function that fills the HUD can fill either. No such function exists.

---

## 8. Eligibility versus permission

Eligibility (important, matched, not yet delivered) can be computed where the queue lives, from stored ids and a clamped label (audit 05 section 7). Permission (lock, capture, playback, turn, clarify, draft, quiet hours, Text mode) lives mostly in the client process. Those are different processes today. An item can stay eligible while permission is false only if "told" is not set when ranking finishes or when a speak attempt is refused. Nothing sets "told" today. The risky pattern that does exist is `send_gate`'s in-memory auth: a claim that dies with the process, which fails closed for **sending mail**, not for speech.

---

## 9. One final gate

No component both claims a queue row and sees live client state. The client sees lock, capture, playback, mode, and window. Serve sees the turn, the clarify request, and the reviewed draft. `voice.tts` starts speech and returns `speaking` without a claim token. Two overlapping speaks are not prevented inside `methods_voice.py` L774 (each call starts a thread).

**P9PRE-AUD-40 [GAP] HIGH** — there is no single place that atomically claims an item, checks live speech state, starts speech, and records started versus completed. `S70`, `P4-D01`, `A2`.
