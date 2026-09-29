# P4PRE Audit 03 — Clarify and Server-Request Protocol (S20)

**Audit ID:** P4PRE  
**Scope:** S20 — Client cannot answer Hermes clarify requests  
**Sources:** Hermes `345cd2b…`; Windows client `504ae76…`; live profile snapshot Phase 1  
**Labels against:** Conversational Attention §10–§11; Presence UI §16; Tool Authorization §1 / §3 (`A3`); `P2-D05`, `P2-D12`, `P3-D03`, `P3-D04`

---

## Finding summary (this document)

| ID | Label | Severity | Scope | Summary |
|----|-------|----------|-------|---------|
| P4PRE-AUD-11 | [MATCH] | — | [S20] | K4 confirmed: clarify is JSON-RPC server→client request `srq-*`; answer is response frame |
| P4PRE-AUD-12 | [GAP] | HIGH | [S20] | `ChatSocket` drops every server request; never answers clarify |
| P4PRE-AUD-13 | [RISK] | HIGH | [S20] | Effective clarify timeout 3600 s → long "Thinking" stall (matches S20 lore) |
| P4PRE-AUD-14 | [MATCH] | — | [S20] | Clarify tool enabled by default on coding/`hermes serve`; `check_clarify_requirements` always true |
| P4PRE-AUD-15 | [RISK] | HIGH | [X] | `approval` also dropped; dangerous commands deny after ~300 s (fail-closed) |
| P4PRE-AUD-16 | [GAP] | MEDIUM | [S20] | No `CLARIFICATION_PENDING` / HUD awaiting-answer; stuck `_streaming` / Thinking like S26 |
| P4PRE-AUD-17 | [GAP] | MEDIUM | [S20] | Client never reads `open_requests` on `session.resume` |
| P4PRE-AUD-18 | [MATCH] | — | [S20] | Protocol supports one generic server-request boundary (Desktop pattern) |
| P4PRE-AUD-19 | [RISK] | MEDIUM | [S20] | Voice transcripts during open clarify become busy `prompt.submit`, not clarify answers |

---

## 1. K4 confirmation — wire formats

**P4PRE-AUD-11 [MATCH] [S20]** — Clarify is a peer JSON-RPC **request** from server to client (`id` = `srq-<hex>`, `method` = `clarify`). The client answers with a **response** frame bearing the same `id` (no `clarify.respond` method). Source: `tui_gateway/server_requests.py` L55–57 (`ServerRequest.frame`).

### Single-question request

```json
{
  "jsonrpc": "2.0",
  "id": "srq-a1b2c3d4e5f6",
  "method": "clarify",
  "params": {
    "session_id": "<sid>",
    "question": "Which environment?",
    "choices": ["staging (Recommended)", "prod"],
    "multi_select": false
  }
}
```

### Multi-select

Same shape with `"multi_select": true` and `choices` present. Answer is still `{ "answer": "…" }` (may be a JSON-array string of labels depending on gateway coerce path).

### Batch (`questions[]`)

```json
{
  "jsonrpc": "2.0",
  "id": "srq-…",
  "method": "clarify",
  "params": {
    "session_id": "<sid>",
    "questions": [
      {"qid": "q0", "question": "Color?", "choices": ["red (Recommended)", "blue"], "multi_select": false},
      {"qid": "q1", "question": "Name?", "choices": null, "multi_select": false}
    ]
  }
}
```

Built in `server.py` `_clarify_block` (~1331–1335). `qid` = `q{index}` (`clarify_tool.py` ~132).

### Response frames (client → server)

| Kind | Example | Meaning of `""` |
|------|---------|-----------------|
| Single answer | `{"jsonrpc":"2.0","id":"srq-…","result":{"answer":"staging"}}` | N/A |
| Skip | `{"jsonrpc":"2.0","id":"srq-…","result":{"answer":""}}` | User skipped / walked away |
| Batch cancel-all | `{"jsonrpc":"2.0","id":"srq-…","result":{}}` (neither `answer` nor `answers`) | Cancel all |
| Batch final | `{"jsonrpc":"2.0","id":"srq-…","result":{"answers":{"q0":"red","q1":"Ada"}}}` | |

### `clarify.lock` (client→server RPC during batch)

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "clarify.lock",
  "params": {
    "request_id": "srq-…",
    "question_id": "q0",
    "answer": "staging"
  }
}
```

Result: `{"status":"ok","remaining":["q1"]}` or `{"status":"expired"}` (`methods_prompt.py` ~1102–1120).

### `request.cancel` (server→client **event**)

```json
{
  "jsonrpc": "2.0",
  "method": "event",
  "params": {
    "type": "request.cancel",
    "session_id": "<sid>",
    "payload": {"id": "srq-…", "method": "clarify", "reason": "timeout"}
  }
}
```

Reasons include `timeout | interrupted | shutdown | resolved | session_closed` (`contracts/server_requests.py` ~219–234).

---

## 2. Timeout

| Layer | Behaviour |
|-------|-----------|
| `resolve_clarify_timeout` | `clarify.timeout` if set → else `agent.clarify_timeout` → else **3600**; non-numeric → 3600; `<=0` = unlimited (`clarify_gateway.py` L259–269) |
| Live Zola profile | **no** `clarify.*` / `agent.clarify_timeout` → **3600 s** |
| On timeout | `request.cancel` reason `timeout`; tool gets empty `user_response` (skip semantics) on TUI path |
| Model | Empty = user skipped; schema prefers deciding; not the messaging-gateway `"[user did not respond…]"` string |

**P4PRE-AUD-13 [RISK] HIGH [S20]** — 3600 s is consistent with "she just sits there thinking": client `_streaming` stays true; `PresenceMode.Thinking`; stale-thinking warn at **120 s** (`ZolaDisplayState`) while clarify is silent. Distinct from `agent.session_stall_timeout` default 300 s.

---

## 3. While a `clarify` request is open

| Client action | Clarify request | New text fate | `SPEECH_INTERRUPTED_NOTE` |
|---------------|-----------------|---------------|---------------------------|
| (a) `prompt.submit` mid-turn | Busy path (`display.busy_input_mode` default **interrupt**) can hard-interrupt → `_clear_pending` → **cancel clarify** (`request.cancel` interrupted) | Steer / redirect / queue then interrupt — **not** a clarify answer | May latch if TTS stop uses default `user_barge=True` |
| (b) `session.interrupt` | **Cancelled** (`interrupted`) | N/A | TTS stop may latch |
| (c) WS drop / reconnect | Unanswered requests **survive** server-side; returned in `open_requests` on resume/activate/events.since | N/A | Unchanged |
| (d) Voice capture / transcript | Mic usable; transcript → `SubmitTurnAsync` → busy path | Steer/queue/interrupt — **not** clarify resolve | Barge-in latches note |

**P4PRE-AUD-19 [RISK] MEDIUM [S20]** — `P2-D05` "every transcript → `prompt.submit`" conflicts with clarify-answer routing unless a single authority redirects transcripts while a request is open.

Note: typed Send is blocked while `_streaming` (`MainWindow` ~242); voice transcripts still call `SubmitTurnAsync` during turn (~256–265).

---

## 4. Clarify tool enabled?

```233:235:C:\Users\test\Dev\hermes-agent\tools\clarify_tool.py
def check_clarify_requirements() -> bool:
    """Clarify tool has no external requirements -- always available."""
    return True
```

`clarify` is in Hermes core/coding toolsets. Live profile has no `platform_toolsets` / `disabled_toolsets` overrides → **enabled** for Zola `hermes serve`.

**P4PRE-AUD-14 [MATCH] [S20]**

---

## 5. `SERVER_REQUESTS` inventory

| Method | Params (core) | Timeout | On miss | In Zola coding toolset? |
|--------|---------------|---------|---------|-------------------------|
| **clarify** | question/choices/multi_select **or** questions[] | ~3600 (`<=0` unlimited) | Empty skip / batch partial+`timed_out` — **fail-open** to proceed | **Yes** |
| **approval** | request_id, command, description, choices, flags | ~**300 s** | **Deny fail-closed** | Via dangerous **terminal** — **yes risk** |
| sudo | (session_id) | 120 s | `""` skip | If terminal sudo |
| secret | env_var, prompt, … | 300 | `""` | Skills/setup |
| vault.unlock_prompt | backend, display_name | 120 | `""` | Browser vault |
| vault.save_login | origin, site | 180 | `""`/None | Browser vault |
| vault.code | site?, hint? | 180 | `""` | Browser vault |
| mcp.setup | server, action, reason | 600 | `""` | desktop_ui only (not default tui coding) |
| terminal.read / preview.read / preview.act / window.read / tour | various | 10–45 | `""` / structured unavailable | desktop_ui |

**P4PRE-AUD-15 [RISK] HIGH [X]** — Client drops `approval` the same way as clarify. Dangerous command waits ~300 s then **deny**. Report for developer: Phase 4 scope vs new open question. Aligns with Tool Authorization §1 Confirmed Send / §3 `A3` (Hermes gate exists; client must surface it).

---

## 6. What the client drops today

```500:504:windows-client/Zola.Client/ChatSocket.cs
            if (method is not null && root.TryGetProperty("id", out var requestId) && requestId.ValueKind == JsonValueKind.String)
            {
                // P1-CLIENT: srq- server requests share this socket and are not chat tokens — P1-D01
                Routed?.Invoke($"Ignored a server request ({method}). It was not treated as a chat message.");
                return;
            }
```

**P4PRE-AUD-12 [GAP] HIGH [S20]** — Explicit ignore; no response frame.

Effects:
- Does **not** clear `_streaming`.
- `PresenceMode` stays **Thinking** while turn running (`ZolaDisplayState` ~268–270).
- Stale-thinking clock (120 s without turn activity) **does** fire — same client symptom class as **S26** (missing `message.complete`).
- Observable difference vs S26: Hermes logs / `Routed` line may show `Ignored a server request (clarify)`; server still has open `srq-`; eventually `request.cancel` timeout. S26 has no open server request.

`ChatSocket.DispatchEvent` has no handlers for `tool.*` or `request.cancel`.

**P4PRE-AUD-16 [GAP] MEDIUM [S20]** — No awaiting-answer presence; Attention `CLARIFICATION_PENDING` / Presence UI §16 clarification prompts unimplemented.

---

## 7. Voice-mode: does she speak the question?

Clarify is a **server request**, not `message.delta`. Turn TTS queues from assistant deltas (`prompt_turn`); the tool question text is **not** automatically spoken.

| Option | Mechanism |
|--------|-----------|
| (i) Client `voice.tts` | `VoiceTtsParams`: `text`, optional `profile`. Hermes `methods_voice.py` ~765–775: starts `_speak_text_with_barge` thread; returns `{"status":"speaking"}`. Side effect: barge-in aware playback. |
| (ii) Hermes existing path | None found that auto-speaks clarify params |
| (iii) Show only | HUD / conversation card; no TTS |

Zola today: **neither** — request dropped before any surface.

---

## 8. Answer routing by voice

| Concern | Today | Future single-authority fit |
|---------|-------|-----------------------------|
| Transcript → turn | `VoiceController` → `TranscriptReady` → `MainWindow.SubmitTurnAsync` → `prompt.submit` (`P2-D05`) | While clarify open, **same** transcript path must route to response frame / `clarify.lock`, not a second submit path — ownership stays at MainWindow handler **or** VoiceController with one consumer |
| Stop phrase | Ends voice chat; does not specially cancel clarify | Cancel clarify only if interrupt path fires |
| Echo-guard (`P2-D14`) | Follow-up capture only | N/A until clarify TTS |
| After `request.cancel` | Client ignores event | Must tear down local awaiting state; late answer → Hermes `resolve_response` returns false (dropped) |

Do not create a parallel submit authority (`P2-D12`).

---

## 9. Choices and free text

- Up to 4 choices; UI concept includes **"Other (type your answer)"** (`clarify_tool.py`).
- Open-ended: omit `choices` → free text.
- Empty `answer` = skip.
- Free prose on a choice prompt can cancel clarify and route as normal message on some gateway paths (`clarify_gateway.py` ~163–184).
- Recommended label stripped from `user_response`.

Spoken mapping ("the second one" vs choice text): Hermes accepts free text; mapping is a **client** concern (no automatic ordinal resolver found in clarify tool).

---

## 10. PresenceMode / HUD while awaiting

`PresenceMode` enum: Idle, Listening, Thinking, Speaking, Alert, Dormant only (`P3-D04`). **No `CLARIFICATION_PENDING`.**

| Candidate | Fit |
|-----------|-----|
| `LISTENING` | Only if a capture is open |
| `IDLE` | Misleading while turn blocked on human |
| New mode | Would amend `P3-D04` — developer decision |
| Stay `THINKING` | Current accidental behaviour; dishonest vs Attention §10 |

HUD: need distinct voice label + mic line via `ZolaDisplayState` only (`P3-D03`). Presence UI §16 expects clarification prompts in Conversation Panel — **GAP**.

Follow-up capture (`P2-D06`/`P2-D15`): if she speaks the question via `voice.tts`, a follow-up window after speech would help spoken answers; if show-only, Text composer / choice UI is primary.

---

## 11. Text mode surface

Today: `OnSendClick` gated on `!_streaming` — **cannot** type an answer while clarify holds the turn. Composer disabled while streaming.

Needed (options, no choice): bubble or inline card with choice buttons; composer knows next Send answers the open `srq-` (Desktop skip-on-prose pattern) rather than starting a new prompt.

---

## 12. Reconnect / `open_requests`

Server includes `open_requests` on `session.resume` / `activate` / `events.since` when non-empty (`server.py` ~2787–2791). Shared TS re-delivers with `replayed: true`.

**Zola:** resumes with session id only — **does not parse `open_requests`**.

**P4PRE-AUD-17 [GAP] MEDIUM [S20]**

### 12b. Generic server-request boundary

| Question | Answer from source |
|----------|-------------------|
| (i) Protocol support | **Yes.** Peer JSON-RPC; `srq-*` ids; response `{id, result\|error}`; `request.cancel` + `open_requests` for every method. Contracts registry lists all methods. |
| (ii) Insertion point | `ChatSocket.Dispatch` string-id branch (~500–504): handle instead of ignore; raise event to MainWindow; one component owns open-request map by `id` — **not** duplicating `VoiceController` or `ZolaDisplayState` authority (feed display facts into `ZolaDisplayState`; route voice answers through existing transcript consumer). |
| (iii) JSON-RPC **error** vs no response | Shared TS unhandled → `-32601`. Hermes `resolve_response` treats error as settled/"never answered" style failure for the waiter (vs hang until timeout with **no** response — Zola's current path). Deterministic decline via error is available. |
| (iv) `apps/shared` TS | `onRequest` / `deliverRequest` / `deliverOpenRequests`; Desktop `SERVER_REQUEST_HANDLERS` map — reference only. |

**P4PRE-AUD-18 [MATCH] [S20]** — Protocol allows one boundary; clarify as first handler is viable without inventing a new wire format.

### 12c. Stale / wrong-request race table

| Scenario | Hermes | Stable identity | Client reject path (future) |
|----------|--------|-----------------|-----------------------------|
| A → `request.cancel` A → transcript/Send | Response for closed id dropped | `srq-*` | Ignore if local card gone / id not open |
| A → socket drop → reconnect → `open_requests` | Replay with locked `answers` | `srq-*` + `session_id` | Must rehydrate; Zola today never does |
| A open → B arrives (same session / child) | Multiple `_open` by id; oldest pending kind | `srq-*` | Key UI by id; never answer wrong id |
| A open → Voice↔Text switch | Clarify independent of voice mode | `srq-*` | Transcript must not `prompt.submit` if clarify open |
| A open → switch/resume other session | Cancel scoped by sid on interrupt; open_requests per sid | `session_id` + `srq-*` | Do not answer foreign session id |
| A → answer → duplicate Send/transcript | First settles; second dropped | `srq-*` | Clear local card when sending |
| A → `session.interrupt` → late answer | `_clear_pending` + cancel | `srq-*` | Late answer no-op |
| Batch: some `qid` locked → timeout → late lock | Partial locks survive; expired → `{status:expired}` | `srq-*` + `qid` | Honour `expired` |
| A arrives while speaking (barge-in open) | SPEECH note on next submit; interrupt may cancel clarify | `srq-*` | Do not treat barge-in transcript as clarify answer without handler |

---

## 13. Options table (no recommendation)

| Area | Options | Touches | Owner |
|------|---------|---------|-------|
| **Surface** | Inline HUD; conversation card (Desktop-like); voice-only TTS + spoken reply | `MainWindow` UI / `ZolaDisplayState` | Display: `ZolaDisplayState`; UI: MainWindow |
| **Answer routing** | Dedicated respond writer; composer answers when open; never use busy `prompt.submit` as answer | `ChatSocket` respond; `VoiceController` transcript consumer; MainWindow Send | One respond path; transcript still single consumer |
| **Speak question** | `voice.tts`; show-only; speak numbered choices | `voice.tts` RPC | VoiceController RPC owner |
| **Timeout** | Keep 3600; lower `agent.clarify_timeout` in profile; UI countdown; skip on timeout | Profile config (developer-approved); UI | Config outside client source |
| **Approval** | Handle with clarify in Phase 4; or file new open question | Same boundary as 12b | Same server-request owner |
| **Boundary** | Generic first (clarify as first handler) vs clarify-only | `ChatSocket` + MainWindow | Prefer protocol-shaped generic boundary (facts only) |

---

## Architecture labels

| Expectation | Verdict |
|-------------|---------|
| Attention §10 `CLARIFICATION_PENDING` | **[GAP]** AUD-16 |
| Attention §11 clarification/repair | **[GAP]** AUD-12 — cannot repair without answer path |
| Presence UI §16 clarification prompts | **[GAP]** AUD-16 |
| Tool Auth §1 / §3 `A3` | **[RISK]** AUD-15 approval drop |
| `P2-D05` immediate submit | **[RISK]** AUD-19 when clarify open |
| `P2-D12` / `P3-D03` / `P3-D04` | Gate/display must not create parallel authorities |

---
