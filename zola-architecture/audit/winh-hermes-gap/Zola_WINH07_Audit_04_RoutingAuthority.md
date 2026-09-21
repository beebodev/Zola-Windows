# WINH07 Audit 04 — Routing: One Authoritative Path Across Surfaces & Providers

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Core Architectural Principles — Single Authority Ownership, Provider Abstraction Philosophy; Agent Map Core Rule (“…or holds routing authority”). Surfaces are WINH02’s six candidates — this phase does not re-inventory them, only how a request is routed once it arrives.

`WINH06-AUD-25` covers the human `/model` switch surface; this phase asks where provider selection is *implemented*. `WINH03-AUD-05/08` cover mid-turn disconnect fail-open; this phase asks where an orphaned turn’s *output* can go. `WINH06-AUD-14` is the “no single inventory” pattern analog for discoverability.

---

## 1. Single component routing inbound requests to the correct session/agent?

**Zola / Agent Map:** one owner of routing authority. Subsystems do not independently resolve “which agent instance.”

**Surfaces 2 + 3 (dashboard `/api/ws` and JSON-RPC / Desktop) share one dispatcher:**

- Inbound: `tui_gateway/server.py` `dispatch` L844–877 binds the connection’s `Transport`, then `handle_request` L797–821.
- Method table: `_methods.get(method)` (L802). Unknown method → -32601.
- Session: handlers call `_sess_nowait` / `_sess` L1141–1172 — `_sessions.get(params["session_id"])`. Stale id → 4001 + warning log, **not** a new mint. Resume is a separate RPC (`methods_session.py` `_resume_reuse_live` L677–698) that reattaches transport (possibly into `FanoutTransport`).
- Prompt routing after lookup: `methods_prompt.py` `prompt.submit` L544+ uses that same sid’s session dict and `_run_prompt_submit`.

That is a **single in-process router for those two surfaces**. It is still not a named Routing Authority object; it is `dispatch` + `_sessions`.

**The other four WINH02 surfaces do not use that router:**

| Surface (WINH02) | Where routing actually happens |
|---|---|
| 1 — OpenAI-compatible HTTP | `gateway/platforms/api_server.py`: own aiohttp routes (`_handle_chat_completions`, `_handle_session_chat` L1548–1551). Session id for Open WebUI-style chat is `_derive_chat_session_id` L1012–1017 (`api-{sha256[:16]}` of system prompt + first user message). Does not call `tui_gateway.dispatch`. |
| 4 — ACP | `acp_adapter/server.py` `prompt` L781–786: `self.session_manager.get_session(session_id)` (`acp_adapter/session.py` `SessionManager`). Separate process/stdio; own claim/queue (`_claim_turn_or_queue` L807). |
| 5 — MCP serve | `mcp_serve.py` L1–7: stdio MCP tools over **messaging conversations**, not `_sessions`. |
| 6 — Webhook | `gateway/platforms/webhook.py` L1–8: HMAC route → rendered prompt → messaging `gateway.run` delivery. Independent of JSON-RPC sids. |

Messaging gateway sessions (`gateway/run.py`, `build_session_key` import ~L2092) are a **third** session namespace (platform user / chat id), not `_sessions`.

There is no component that all six call. Dashboard and JSON-RPC share one; API, ACP, MCP, and webhook each resolve independently. If two of those are live against what a human thinks is “one Zola,” Hermes does not elect a winner.

**Label:** `[GAP]` `WINH07-AUD-09` (HIGH) against routing authority. Shared `dispatch` covers Surfaces 2+3 only.

---

## 2. Provider / model routing — one place, or independent callers?

**Zola Provider Abstraction:** one owner of which backend handles a call; subsystems do not independently pick providers.

**Shared helper (not a single call site):** `hermes_cli/runtime_provider.py` `resolve_runtime_provider` L835–852 — documented ladder (disabled-provider guard → shortcuts → custom → local endpoint → auth → pool → OAuth → OpenRouter fallback).

**Independent callers of that helper (or of parent-runtime copies) at this pin:**

- Main turn / CLI / gateway agent build uses the resolved runtime for that session (session can then be switched by human `/model` — `WINH06-AUD-25`, `tui_gateway/model_switch.py`; not re-audited).
- **Background review:** `agent/background_review.py` `_resolve_review_runtime` L205–243. Default inherits parent with `routed=False`. If `auxiliary.background_review.{provider,model}` names another concrete model, it **calls `resolve_runtime_provider` itself** (L230–234) and sets `routed=True`. Failure falls back to parent (L241–243) with a debug log — the fork still runs, on a different model if config says so.
- **Delegation:** `config_defaults.py` `delegation.model` / `delegation.provider` L1230–1235 — children can override the parent; empty = inherit. Same resolution family, **separate config keys**, applied when `delegate_task` builds the child (not a shared arbiter that the main turn must approve per call).
- ACP `SetSessionModel` / `encode_model_choice` (`acp_adapter/model_catalog.py`, used from `acp_adapter/server.py`) is yet another switch path in the ACP process.

There is no runtime object that says “this session’s provider is X and no subsystem may differ.” Review and delegation are designed to differ.

**Label:** `[PARTIAL]` `WINH07-AUD-10` (MEDIUM) — one resolution *function*; main turn, background review, and delegation may each select a provider with no shared arbitration.

---

## 3. Fail-open orphaned turn — where can output go?

**Cite, do not restate:** `WINH03-AUD-05/08` — Surface 3 mid-turn disconnect defaults fail-open (healthy detached turn keeps running; 20s grace / 600s freshness; client must interrupt to fail-closed).

**New question:** once that orphaned turn completes, is there still exactly one output path?

**Observed at this pin:**

1. **Live WS gone:** session transport becomes `_DropTransport` (`server.py` L191–207, instance L207). `write()` returns `False` — frames are **not** delivered to stdout (comment L205–206: Desktop would log stale frames).
2. **Replay ring still stamps:** `write_json` L602–604 calls `_stamp_event` **before** `t.write(obj)`. `tui_gateway/event_replay.py` L26–28 `_REPLAY_BUFFER_MAX = 512`. A reconnecting client on the **same sid** can `session.events.since` and receive (some of) the orphaned turn, including `message.complete`, if it is still in the ring.
3. **Resume of an already-live session:** `_resume_reuse_live` L677–679 attaches the new client *alongside* existing streamers (`FanoutTransport`). Output of the still-running turn goes to whoever is attached **now**, which may be a different WS than the one that started it — same sid / same `session_key`, new peer. That is by design for “resume,” and it is also “delivered to a reconnected session that isn’t the socket that started it.”
4. **Completely clientless:** DropTransport swallows writes; transcript still lands in `state.db` (WINH03 durability). A later cold `session.resume` hydrates history — the user sees the completed assistant row after the fact. Not a random other sid.
5. **Notification / async-delegation completions:** `session_notifications.py` L51–64, L99 — events carry `origin_ui_session_id` / `session_key`; compression can rotate `AIAgent.session_id`. The poller maps back onto a live TUI tab. If the originating tab is gone, completion can surface on a **different live window that shares `session_key`** (comment L51: “the session that started the work”). That is session-key routing, not “discard.” It is not guaranteed to be the original client connection.
6. **Review fork after orphaned complete:** `_publish_review_summary` still fires; `background_review_callback` `_emit("review.summary", sid, …)` hits DropTransport (dropped) **and** the replay ring. A later attacher may see the review toast without having seen the turn live.

Output is **not** silently re-addressed to an unrelated sid in the code reviewed. It **is** dropped on the wire, retained in a 512-event ring, persisted in SQLite, and/or delivered to a later attacher of the same logical session — including a peer that did not start the turn. There is no governor that says “this completion may only return to the requesting transport.”

**Label:** `[RISK]` `WINH07-AUD-11` (MEDIUM) — orphaned complete is not a second random session, but DropTransport + replay + fan-out resume + session_key notification mapping mean output can land on a later/other client of the same slot, or nowhere on the wire.

---

## 4. Is routing authority documented / discoverable?

**Analog:** `WINH06-AUD-14` — no single capability inventory; understanding “what can this agent do” requires several files.

**Routing analog:** understanding “what decides where this request goes” requires at least:

- `tui_gateway/server.py` `dispatch` / `_sess_nowait` / `write_json`
- `tui_gateway/methods_prompt.py` + `prompt_turn.py`
- `tui_gateway/session_transports.py` FanoutTransport
- `tui_gateway/session_notifications.py` origin mapping
- `gateway/platforms/api_server.py` `_derive_chat_session_id` and HTTP routes
- `acp_adapter/session.py` `SessionManager`
- `mcp_serve.py`
- `gateway/platforms/webhook.py` + `gateway/run.py` `build_session_key`
- `hermes_cli/runtime_provider.py` + `agent/background_review.py` `_resolve_review_runtime` + `delegation.*` config

`tui_gateway/AGENTS.md` documents the JSON-RPC contract (WINH02), not a cross-surface routing authority. There is no `RoutingAuthority` type and no one file that lists the six inbound resolvers.

**Label:** `[GAP]` `WINH07-AUD-12` (MEDIUM) — no single reference point for routing authority (same pattern as `WINH06-AUD-14`).

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH07-AUD-09 | GAP | HIGH | `server.py` `dispatch` L844–877 vs `api_server.py` / `acp_adapter` / `mcp_serve.py` / `webhook.py` | Only Surfaces 2+3 share a dispatcher; four surfaces route alone |
| WINH07-AUD-10 | PARTIAL | MEDIUM | `runtime_provider.py` L835–852; `background_review.py` L205–243 | Shared ladder function; review/delegation may pick independently |
| WINH07-AUD-11 | RISK | MEDIUM | `_DropTransport` L191–207; `event_replay.py` L26–28; `methods_session.py` L677–679 | Orphaned output: drop / 512-ring / later attacher / session_key notify |
| WINH07-AUD-12 | GAP | MEDIUM | six inbound files (no single index) | Routing authority not discoverable in one place |
