# WINH02 Audit 01 — Hermes Integration Surface Inventory

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`
Clone path (external): `C:\Users\test\Dev\hermes-agent`

Selection audit, not pass/fail. Labels: `[MATCH]` credible primary candidate; `[PARTIAL]` usable with a named limitation; `[GAP]` exists but not usable as Zola's primary integration point; `[RISK]` a named danger of relying on the surface. A surface may carry more than one label.

Zola evaluation lenses (Master Architecture Plan: centralized authority, L1056 / L1162; "Final authority determines response behavior," L1124; fail-closed when uncertain): if a client disconnects mid-turn, does a named authority resolve the ambiguity, or is the system left undefined?

The six candidate surfaces are those named in `Zola_WINH01_Audit_01_RepoMap.md` ("HTTP / WebSocket / RPC API surface"). Each subsection answers the eight Phase 2 questions from the actual entry point, not the docstring that named it.

---

## Surface 1 — OpenAI-compatible HTTP API

**Entry:** `gateway/platforms/api_server.py` (`APIServerAdapter`); route table in `_http_route_table`; Chat Completions / Responses streaming in `gateway/platforms/api_server_openai_routes.py`; run control in `gateway/platforms/api_server_runs.py`.

### 1. Transport / protocol

HTTP REST over aiohttp. OpenAI-compatible paths (`/v1/chat/completions`, `/v1/responses`, `/v1/models`) plus Hermes-native paths (`/v1/capabilities`, `/api/sessions`, `/v1/runs`, `/api/jobs`, `/health*`). Module docstring (`api_server.py` L1–6): default bind `http://localhost:8642/v1`. Streaming uses Server-Sent Events (`text/event-stream`). Multiplex prefix `/p/<profile>/...` when `gateway.multiplex_profiles` is on.

### 2. Public / versioned vs internal

Documented as a **public third-party interface**. `website/docs/user-guide/features/api-server.md` L7–9: "The API server exposes hermes-agent as an OpenAI-compatible HTTP endpoint. Any frontend that speaks the OpenAI format — Open WebUI, LobeChat, LibreChat, NextChat, ChatBox, and hundreds more — can connect to hermes-agent and use it as a backend." Feature discovery exists at `GET /v1/capabilities` (`api_server.py` L86 route table). There is **no independent Hermes API semver** on the adapter itself; compatibility is claimed via the OpenAI shapes plus documented Hermes extensions.

### 3. Authentication / pairing

Bearer token `API_SERVER_KEY`. Resolved in `APIServerAdapter.__init__` (`api_server.py` L1135) and enforced at request time (L1348–1360: `"Invalid gateway API key (API_SERVER_KEY)"`). Startup guard `_api_key_is_strong_enough` (L3844–3897) refuses to start without a usable key when the bind is non-loopback. CORS via `API_SERVER_CORS_ORIGINS`.

### 4. Streaming partial responses

Yes, when the client sets `"stream": true`. Chat Completions emit standard `chat.completion.chunk` SSE frames. Documented in `website/docs/user-guide/features/api-server.md` L109–112. Code: `api_server_openai_routes.py` writes SSE frames including `event="hermes.tool.progress"` (L668). Responses API uses OpenAI event types (`response.output_text.delta`, etc.) per the same doc page.

**Labelled unverified by running the server:** whether a given OpenAI frontend actually renders `hermes.tool.progress` (that is a client concern). The server does emit the event.

### 5. Tool-execution events separate from the final response

Yes, for streaming Chat Completions: SSE event type `hermes.tool.progress` (`api_server_openai_routes.py` L521, L668). Docs (api-server.md L112): "Hermes emits `event: hermes.tool.progress` to provide tool-start visibility without polluting persisted assistant text." The `/v1/runs/{run_id}/events` SSE (route table `run_events_sse`) is a second, run-oriented event stream.

### 6. Interrupt / cancel of an in-flight request

Yes: `POST /v1/runs/{run_id}/stop` → `_handle_stop_run` in `api_server_runs.py` L862–883, which calls `request_hard_interrupt(agent, "Stop requested via API")`. Mid-stream client disconnect also interrupts: `api_server_openai_routes.py` L697–698 (`"SSE client disconnected; interrupted agent task"`); session SSE at `api_server.py` L3241–3242. Helper `_reap_disconnected_agent_processes` default source is `"api_server_sse_disconnect"` (`api_server.py` L555–556). **Fail-closed on this surface:** a vanished SSE client does not leave the agent running unbound.

### 7. Multiple concurrent sessions

Deliberately supported, with a cap. `APIServerAdapter` tracks `_active_run_agents` (run_id-keyed) and `_inflight_agent_runs`; `max_concurrent_runs` is read from `config.yaml` `gateway.api_server.max_concurrent_runs` (`api_server.py` L1164–1168; `0` disables the cap). Session identity for the OpenAI paths is a gateway session key plus `/api/sessions`; `/v1/runs` has its own `run_id`. Concurrent runs on the same `session_id` are acknowledged in the stop handler comment (api_server_runs.py L880–882: reap is epoch-gated so a concurrent run on the same session keeps its own processes).

### 8. In-repo first-party callers

No first-party GUI in this repo speaks this API as its chat transport. Documented third-party targets are Open WebUI / LobeChat / etc. (`api-server.md` L9). In-tree use is the gateway platform adapter itself plus tests under `tests/` / `evals/`. Desktop and the dashboard do **not** use `/v1/chat/completions` for the product chat UI (they use Surface 3).

**Labels:** `[PARTIAL]` `[RISK]`
- `[PARTIAL]` — public, documented, streaming, tool-progress, and cancel all exist; it is a real third-party integration point. Limitation: the first-party Desktop/TUI contract (sessions, approvals, slash commands, reconnect replay) lives on Surface 3, not here. A Zola client that used only this API would have to design around the missing first-party RPC catalog.
- `[RISK]` — OpenAI compatibility is a shape claim, not a versioned Hermes contract. Hermes-specific events (`hermes.tool.progress`, `/v1/runs`) can change without an OpenAI version bump. Capability bits exist (`GET /v1/capabilities`) but there is no client-detectable semver for the Hermes extensions.

**Finding:** `WINH02-AUD-03`

---

## Surface 2 — Dashboard FastAPI + WebSocket

**Entry:** `hermes_cli/web_server.py` (FastAPI `app`); chat transports in `hermes_cli/web_routers/chat_ws.py`; PTY spawn in `hermes_cli/web_server_chat.py`. SPA in `web/`. Started by `hermes dashboard` / `hermes serve`.

This surface is **two transports sharing one HTTP server**, not one protocol.

### 1. Transport / protocol

- **HTTP REST** for dashboard APIs (sessions, cron, skills, memory, MCP, status, …) under `/api/`.
- **`/api/pty` WebSocket** — a byte pipe to a spawned `hermes --tui` child behind a PTY. `web_server_chat.py` L26–28: "spawns `hermes --tui` behind a pseudo-terminal and forwards bytes + resize escapes to xterm.js." POSIX: `pty_bridge`; native Windows: `win_pty_bridge` (ConPTY).
- **`/api/ws` WebSocket** — JSON-RPC sidecar to the same `tui_gateway.dispatch` surface Ink uses over stdio. `chat_ws.py` L555–565: `gateway_ws` calls `tui_gateway.ws.handle_ws`. This is Surface 3 tunneled through the dashboard process, not a distinct RPC catalog.

### 2. Public / versioned vs internal

Internal to Hermes's own web UI / Desktop backend. `web_server.py` L304–307: the session token "is injected into the SPA HTML so only the web UI can use it." `tui_gateway/AGENTS.md` L3–4: "tui_gateway is ALSO the backend the Desktop app and the dashboard `/chat` talk to — changes here have three consumers." No public "Dashboard API vN" doc for third-party clients was found. The user-facing docs describe using the dashboard in a browser, not integrating against it.

### 3. Authentication / pairing

Dashboard session token: `HERMES_DASHBOARD_SESSION_TOKEN` or a fresh `secrets.token_urlsafe(32)` per process (`web_server.py` L307–311). Header `X-Hermes-Session-Token` (L312). Injected into `index.html` as `window.__HERMES_SESSION_TOKEN__` (`web_server_dashboard.py` L96, L115, L145–146). Loopback binds may skip the token (`_desktop_loopback_auth_exempt` / `_LOOPBACK_HOSTS`); non-loopback and OAuth-gated binds require it. `/api/ws` additionally stamps `auth_identity` for privileged RPCs (`chat_ws.py` L567–573).

### 4. Streaming partial responses

- `/api/ws`: yes — same as Surface 3 (`message.delta` / `reasoning.delta` / `thinking.delta`; see `tui_gateway/ws.py` L75 `_STREAMING_EVENT_TYPES`).
- `/api/pty`: the PTY streams terminal bytes, not structured token events. Any "streaming" is Ink rendering inside the PTY. That is not a client-consumable token stream.

### 5. Tool-execution events

- `/api/ws`: yes — Surface 3 `tool.start` / `tool.generating` / `tool.complete`.
- `/api/pty`: the PTY child can publish structured frames to `/api/pub`; the dashboard fans them to `/api/events` (`chat_ws.py` L577–581). That feed is for the React sidebar, not a standalone client contract. A client speaking only PTY bytes does not get a typed tool-event API.

### 6. Interrupt / cancel

- `/api/ws`: Surface 3 `session.interrupt`.
- `/api/pty`: no structured cancel RPC on the PTY socket itself. Interrupt would be whatever the Ink TUI binds to a key inside the PTY (not a client-callable method on this socket). Closing the PTY WebSocket recycles the terminal session (`web_server_chat.py` L52–54 stalled-input path). **Not confirmed by running the server** whether a PTY close mid-turn interrupts the agent or orphans it.

### 7. Multiple concurrent sessions

The FastAPI server accepts multiple WebSockets. `/api/pty` uses `PtySessionRegistry` (`web_server.py` L142 comment: concurrent `/api/pty` connections; `web_server_chat.py` imports `PtySessionRegistry`). `/api/ws` session identity is Surface 3's `_sessions` dict. Multiple dashboard tabs can attach; whether that is a product feature or merely not prevented is mixed: the registry exists (deliberate for PTY), while session-token auth is one process-wide secret (not per-user accounts).

### 8. In-repo first-party callers

- Browser SPA in `web/` (dashboard Chat tab).
- Desktop does **not** embed the dashboard UI. `apps/desktop/src/AGENTS.md` L11–15: it spawns headless `hermes serve` (`HERMES_SERVE_HEADLESS=1`) and talks JSON-RPC; "The desktop has **no build/runtime dependency on the dashboard frontend**." It does use the same `/api/ws` path on that headless server (Surface 3 over the dashboard process).
- PTY Chat tab: first-party web UI only.

**Labels:** `[PARTIAL]` `[GAP]` `[RISK]`
- `[PARTIAL]` — `/api/ws` is a real, exercised JSON-RPC path (same catalog as Surface 3). A Zola client that connected here would be using Surface 3, not a distinct dashboard API.
- `[GAP]` — `/api/pty` is a terminal embed, not a structured agent client API. The FastAPI REST surface is the dashboard's own UI backend, not a documented third-party agent loop.
- `[RISK]` — session token is ephemeral per process unless `HERMES_DASHBOARD_SESSION_TOKEN` is pinned (`web_server.py` L305–307). A packaged client that treated this token as a stable pairing secret would break on every backend restart.

**Finding:** `WINH02-AUD-04`

---

## Surface 3 — TUI / Desktop JSON-RPC gateway

**Entry:** `tui_gateway/server.py` (facade, `_sessions` at L85); methods in `tui_gateway/methods_*.py`; events in `tui_gateway/contracts/` + `event_publisher.py`; WebSocket adapter `tui_gateway/ws.py`; TypeScript client `apps/shared/src/json-rpc-gateway.ts` (`JsonRpcGatewayClient`).

### 1. Transport / protocol

JSON-RPC, peer-to-peer, two transports for the same catalog:

- **Newline-delimited JSON-RPC over stdio** — Ink TUI (`hermes --tui`). `tui_gateway/AGENTS.md` L19–21: "Newline-delimited JSON-RPC over stdio, peer-to-peer: client→server method calls, server→client **requests** … and server→client `event` notifications."
- **JSON-RPC over WebSocket** — Desktop and dashboard `/api/ws`. Same AGENTS.md L29–30: "Desktop reaches the same server over WebSocket via `apps/shared` (`JsonRpcGatewayClient`, `onRequest`)."

Wire is declared in Python (`tui_gateway/contracts/`) and generated to `apps/shared/src/gateway-contract.generated.ts` + `gateway-contract.openrpc.json` by `scripts/gen_gateway_contracts.py`.

### 2. Public / versioned vs internal

**Internal to Hermes's own clients.** `tui_gateway/AGENTS.md` L1–4: "the TUI and its JSON-RPC backend" / "tui_gateway is ALSO the backend the Desktop app and the dashboard `/chat` talk to — changes here have three consumers." OpenRPC `info.title` is `"Hermes TUI/Desktop gateway"` and `info.version` is the literal string `"1"` (`apps/shared/src/gateway-contract.openrpc.json` L3–5). `@hermes/shared` is `"private": true, "version": "0.0.0"` (`apps/shared/package.json` L2–4). Generated TS file header: "DO NOT EDIT" (`gateway-contract.generated.ts` L1–3). This is a generated in-repo contract, not a published versioned SDK.

### 3. Authentication / pairing

Stdio TUI: process-pair (no token); the Node renderer is a child of `hermes --tui`.

WebSocket: dashboard session token / ticket / SSH owner nonce as on Surface 2 (`chat_ws.py` `_ws_auth_reason`; `web_server.py` session token). Desktop mints `HERMES_DASHBOARD_SESSION_TOKEN` for the sidecar it spawns (`web_server.py` L304–306). Loopback may be exempt. Privileged RPCs (e.g. `browser.controller.register`) use the stamped `auth_identity` (`chat_ws.py` L567–569).

### 4. Streaming partial responses

Yes. Chat path: `prompt.submit` → `message.delta` / `message.complete` (`tui_gateway/AGENTS.md` L53; emit in `tui_gateway/prompt_turn.py` L531). `tui_gateway/ws.py` L75 treats `message.delta`, `reasoning.delta`, `thinking.delta` as streaming event types.

### 5. Tool-execution events

Yes, as first-class events: `tool.start` / `tool.generating` / `tool.complete` (`tui_gateway/AGENTS.md` L54; `tui_gateway/tool_progress.py` L1, L252). Approvals are server→client **requests** (`approval`), not events — the agent blocks until the client answers (`tui_gateway/AGENTS.md` L21–28, L55).

### 6. Interrupt / cancel

Yes: JSON-RPC method `session.interrupt` (`tui_gateway/methods_session.py` L1995–2023; contract `tui_gateway/contracts/sessions.py` L511). Implementation `_interrupt_session_turn` in `tui_gateway/session_lifecycle.py` L390–429 calls `request_hard_interrupt` on the in-process agent. WebSocket disconnect does **not** interrupt immediately: the session is parked on `_detached_ws_transport` (`session_lifecycle.py` L380–387) and a `client_gone` path defers interrupt while "turn activity [is] fresh" (L568–594). **Fail-closed is delayed**, not immediate. Exact grace timing and whether a mid-turn tool keeps running until the reaper fires is a runtime behavior — **not confirmed by running the server**; WINH03 should trace it.

### 7. Multiple concurrent sessions

Deliberate. In-process map `_sessions: dict[str, dict] = {}` (`tui_gateway/server.py` L85). Product methods `session.list` / `session.resume` (`tui_gateway/AGENTS.md` L57). Desktop renderer comment in `apps/desktop/src/store/gateway.ts` L18–26: concurrent sockets per profile so background sessions keep painting. `session.interrupt` is scoped to one `session_id` (methods_session.py L2006–2016; server_requests.py L195: must not touch other sessions' open requests).

### 8. In-repo first-party callers

- Ink TUI: `ui-tui/` over stdio (`tui_gateway/AGENTS.md` process model).
- Desktop: `apps/desktop/src/api/client.ts` `HermesGateway extends JsonRpcGatewayClient` (L28–37); boot in `apps/desktop/src/app/gateway/hooks/use-gateway-boot.ts`; store in `apps/desktop/src/store/gateway.ts`.
- Dashboard Chat tab: `/api/ws` → `handle_ws` (`chat_ws.py` L561–574).

This is the only surface with three in-repo interactive clients.

**Labels:** `[MATCH]` `[RISK]`
- `[MATCH]` — richest agent-loop contract in this tag: streaming tokens, tool lifecycle, approvals, interrupt, multi-session identity, reconnect replay (`session.events.since`). First-party Desktop already solves connection, sidecar spawn, and reconnect against it.
- `[RISK]` — documented as internal to TUI/Desktop/dashboard. Generated contract version `"1"` and package `0.0.0` give a packaged Zola client no independent way to detect a breaking Hermes update. Replay epoch (`replay_epoch` on `gateway.ready`) detects **process identity**, not protocol version (`json-rpc-gateway.ts` L121–127).

**Findings:** `WINH02-AUD-01`, `WINH02-AUD-02`

---

## Surface 4 — ACP (Agent Client Protocol)

**Entry:** `acp_adapter/server.py` (module docstring L1: "exposes Hermes Agent via the Agent Client Protocol"); CLI `acp_adapter/entry.py` (`hermes acp` / `hermes-acp` / `python -m acp_adapter`); sessions in `acp_adapter/session.py`; events in `acp_adapter/events.py`.

### 1. Transport / protocol

JSON-RPC over **stdio**, using the `agent-client-protocol` Python package (`pyproject.toml` extra `acp`, `agent-client-protocol==0.9.0`). `acp_adapter/entry.py` L1–8, L32: stdout is reserved for ACP JSON-RPC; logging goes to stderr. This is the ACP standard wire, not Hermes's TUI JSON-RPC catalog.

### 2. Public / versioned vs internal

Documented as a **public IDE integration**. `website/docs/user-guide/features/acp.md` describes pointing ACP-compatible plugins at `hermes acp` / `hermes-acp`. Protocol versioning is ACP's (`agent-client-protocol==0.9.0`), not a Hermes-native semver. Hermes advertises implementation metadata via `InitializeResponse` (`acp_adapter/server.py` imports).

### 3. Authentication / pairing

ACP handshake auth methods from `acp_adapter/auth.py`: `build_auth_methods()` (L30–50). If a runtime provider is configured, an `AuthMethodAgent` named `{provider} runtime credentials` is advertised; a `TerminalAuthMethod` `hermes-setup` (`args=["--setup"]`) is always advertised for first-run. Pairing is "spawn this stdio agent," not a network token.

### 4. Streaming partial responses

Yes, via ACP `session_update` notifications. `acp_adapter/events.py` L1–6: AIAgent callbacks are bridged onto `conn.session_update()`. Token text uses `agent_message_chunk` / `update_agent_message_text` (`acp_adapter/server.py` L102, L803; `events.py` L133). Thought stream: `agent_thought_chunk`.

### 5. Tool-execution events

Yes. `acp_adapter/tools.py` `build_tool_start` / `build_tool_complete`; ACP `ToolCallStart` / `ToolCallProgress`. `events.py` `make_tool_progress_cb`. Todo results can also emit ACP `plan` updates (`events.py` L27–31).

### 6. Interrupt / cancel

Yes: `HermesACPAgent.cancel` (`acp_adapter/server.py` L613–628) sets `state.cancel_event` and `request_hard_interrupt(state.agent)` under `runtime_lock`. Closing stdio (IDE kills the subprocess) tears down the process; **whether in-flight tools are reaped on a half-closed stdio** is **not confirmed by running the adapter**.

### 7. Multiple concurrent sessions

Deliberate inside one ACP connection: `SessionManager` (`acp_adapter/session.py` L151, `create_session` L167) keyed by ACP `session_id`. `resume_session` / `load_session` / `fork_session` exist (`server.py` L589–639). Typical deployment is one IDE ↔ one stdio process; multiple sessions are ACP sessions in that process, not multiple network clients. Prompt execution uses a thread pool with `contextvars.copy_context()` so concurrent sessions do not share ContextVars (`server.py` L720–723).

### 8. In-repo first-party callers

No in-repo GUI calls ACP. Callers are external ACP hosts (Zed, Buzz Desktop, etc. per `website/docs/integrations/buzz.md` and `acp.md`). In-tree: `hermes acp` launcher + tests.

**Labels:** `[PARTIAL]` `[GAP]`
- `[PARTIAL]` — real, documented, versioned-via-ACP protocol with streaming, tool calls, and cancel. Limitation: `hermes-acp` toolset is IDE-curated. `website/docs/reference/toolsets-reference.md` L97: drops `clarify`, `cronjob`, `image_generate`, `text_to_speech`, `computer_use`, Home Assistant tools, and kanban tools. Stdio process model is what IDEs spawn, not what a standalone Windows product window typically speaks.
- `[GAP]` as Zola's **primary Windows-client** integration point: Zola-Windows is a desktop product, not an editor plugin. ACP does not replace a GUI client; it would make Zola an ACP host or an ACP agent inside someone else's editor.

**Finding:** `WINH02-AUD-05`

---

## Surface 5 — MCP server (`hermes mcp serve`)

**Entry:** `mcp_serve.py` (module docstring L1–7).

### 1. Transport / protocol

MCP over **stdio** (`MCPServer.run_stdio_async()`, `mcp_serve.py` L27–28, L721). Client config quoted in the docstring: `{"mcpServers": {"hermes": {"command": "hermes", "args": ["mcp", "serve"]}}}`.

### 2. Public / versioned vs internal

Documented as a **bridge for other MCP clients** (Claude Code, Cursor, Codex) to Hermes **messaging conversations**, not as Hermes's own agent chat API. Docstring L3–5: "list conversations, read history, send messages, poll live events, and manage approvals. Matches OpenClaw's 9-tool channel bridge surface plus the Hermes-specific channels_list."

### 3. Authentication / pairing

Process spawn (stdio). No network token. The process reads Hermes home / `state.db` (`_hermes_home`, `_get_session_db`). Whoever can spawn `hermes mcp serve` as that user can read/send messaging conversations.

### 4. Streaming partial responses

No agent-token stream. Event delivery is **poll / wait**: `EventBridge.poll_events` / `wait_for_event` (`mcp_serve.py` L309–314). `wait_for_event` takes `timeout_ms` (default 30000). This is conversation-event polling, not `message.delta`.

### 5. Tool-execution events

The MCP **tools** are the API (`conversations_list`, `conversation_get`, send, poll, approvals — L468+). They do not expose Hermes-agent `tool.start` for an in-process AIAgent turn. Approvals on messaging conversations are a separate `list_pending_approvals` / `respond_to_approval` (L328–333).

### 6. Interrupt / cancel

No in-flight agent-turn cancel. There is no `session.interrupt` equivalent because this server does not run the agent loop. Stopping the MCP subprocess stops the bridge.

### 7. Multiple concurrent sessions

The bridge lists many messaging conversations (`session_key`). That is Hermes gateway conversation identity, not MCP-client sessions. One stdio MCP client is the typical caller. Concurrent MCP clients against one `state.db` were **not verified by running the server**.

### 8. In-repo first-party callers

No in-repo GUI. Intended callers are external MCP hosts. In-tree: CLI `hermes mcp serve` + tests.

**Labels:** `[GAP]`
- Exists and is real, but it is a **messaging-conversation MCP bridge**, not an agent-loop client API. Zola could not use it as the primary "talk to the cognitive core" surface.

**Finding:** `WINH02-AUD-06`

---

## Surface 6 — Messaging webhooks

**Entry:** `gateway/platforms/webhook.py` (`WebhookAdapter`); also per-platform inbound adapters under `gateway/platforms/` and `plugins/platforms/` (Telegram, Slack, etc. — WINH01 repo map item 6).

### 1. Transport / protocol

Inbound HTTP POST. `webhook.py` L1–3, L154: "Generic webhook receiver that triggers agent runs from HTTP POSTs." Routes: `POST /webhooks/{route_name}` and `POST /p/{profile}/webhooks/{route_name}` (L222–224). This is a **receiver**, not a client-callable agent RPC.

### 2. Public / versioned vs internal

User-configurable inbound integration (GitHub, GitLab, Svix/AgentMail, generic HMAC). Documented as something that **calls Hermes**, not something Hermes's GUI clients call. No third-party "webhook client SDK" for driving a chat UI.

### 3. Authentication / pairing

HMAC. `webhook.py` L74–81 (`_hmac_str_equal`, `_hex_hmac`); Svix-compatible signatures L128–148. Route start fails closed if a route has no secret (L198: `"Route '{name}' has no HMAC secret"`). `INSECURE_NO_AUTH` is refused on non-loopback binds (L201). Timestamp window on generic HMAC V2 (L7, L131).

### 4. Streaming partial responses

No client stream. The HTTP handler validates, then triggers an agent run. The POST caller gets an HTTP response, not token deltas. (Whether the HTTP response waits for the full run or returns 202 is **not confirmed here without tracing a live request** — WINH03 if this path is ever reconsidered.)

### 5. Tool-execution events

None to the webhook caller. Tool activity stays inside the agent/gateway.

### 6. Interrupt / cancel

No client cancel API on this surface. The caller is the event source, not a session owner.

### 7. Multiple concurrent sessions

Concurrent POSTs can fire concurrent agent runs (subject to gateway run limits). There is no client session object for a Windows UI to hold. Idempotency cache is mentioned in the module docstring (L7).

### 8. In-repo first-party callers

No in-repo GUI posts to `/webhooks/...` as a chat client. Callers are external services. In-tree: gateway adapter + tests.

**Labels:** `[GAP]`
- Real inbound trigger. Zola cannot use it as the primary integration point because Zola would need to **call into** Hermes and receive a streamed turn, not wait to be POSTed at.

**Finding:** `WINH02-AUD-07`

---

## Cross-surface comparison (selection, not a decision)

| Surface | Documented audience | Streamed tokens | Tool events | Cancel | First-party GUI caller | Primary-candidate label |
|---|---|---|---|---|---|---|
| OpenAI HTTP API | Third-party frontends | SSE chunks + `hermes.tool.progress` | Yes | `POST /v1/runs/{id}/stop`; SSE disconnect interrupts | None (external Open WebUI etc.) | `[PARTIAL]` |
| Dashboard FastAPI | Hermes web UI / Desktop sidecar host | `/api/ws` yes; `/api/pty` bytes only | `/api/ws` yes | `/api/ws` yes; PTY unclear | `web/` SPA; Desktop uses `/api/ws` only | `[PARTIAL]` / `[GAP]` for PTY |
| TUI/Desktop JSON-RPC | Internal (TUI, Desktop, dashboard `/chat`) | `message.delta` | `tool.start` | `session.interrupt` (WS disconnect deferred) | TUI, Desktop, dashboard | `[MATCH]` |
| ACP stdio | Public IDE protocol | `session_update` chunks | ACP tool calls | `cancel()` | None in-repo | `[PARTIAL]` / `[GAP]` for Windows product shell |
| MCP serve | Other MCP clients, messaging bridge | No agent stream (poll) | N/A (bridge tools) | N/A | None | `[GAP]` |
| Webhooks | Inbound HMAC POSTs | No | No | No | None | `[GAP]` |

**Authority / fail-closed lens:** Surface 1 interrupts on SSE disconnect (`api_server_openai_routes.py` L697–698). Surface 3 parks the session and may defer interrupt (`session_lifecycle.py` `client_gone`). Those two answers cannot both be "the" authority for "what happens if the Windows client dies mid-turn" without an explicit choice. That inconsistency is `WINH02-AUD-12`.

---

## Findings this document

- `WINH02-AUD-01` — `[MATCH]` — MEDIUM — `tui_gateway/server.py` L85; `tui_gateway/AGENTS.md` L19–30, L53–57; `apps/desktop/src/api/client.ts` L28–37 — JSON-RPC gateway is the only surface that already carries the full first-party agent-loop contract and is exercised by Desktop, TUI, and dashboard `/api/ws`.
- `WINH02-AUD-02` — `[RISK]` — HIGH — `tui_gateway/AGENTS.md` L1–4; `apps/shared/package.json` L2–4 (`version: 0.0.0`); `apps/shared/src/gateway-contract.openrpc.json` L3–5 (`version: "1"`); `gateway-contract.generated.ts` L1–3 — internal, generated, un-semvered contract. A packaged Zola client cannot detect a breaking Hermes update from version numbers alone.
- `WINH02-AUD-03` — `[PARTIAL]` — MEDIUM — `gateway/platforms/api_server.py` L1–6; `website/docs/user-guide/features/api-server.md` L7–9, L109–112; `api_server_openai_routes.py` L668; `api_server_runs.py` L862–883 — public OpenAI-compatible API with streaming, tool progress, and stop; missing the first-party RPC catalog Desktop actually uses.
- `WINH02-AUD-04` — `[PARTIAL]` / `[GAP]` / `[RISK]` — MEDIUM — `hermes_cli/web_routers/chat_ws.py` L555–574; `hermes_cli/web_server_chat.py` L26–28; `hermes_cli/web_server.py` L304–311 — dashboard hosts Surface 3 at `/api/ws` and a PTY embed at `/api/pty`; token is process-ephemeral.
- `WINH02-AUD-05` — `[PARTIAL]` / `[GAP]` — MEDIUM — `acp_adapter/server.py` L1, L613–628; `website/docs/user-guide/features/acp.md`; `website/docs/reference/toolsets-reference.md` L97 — public ACP stdio for IDEs; `hermes-acp` toolset drops cron and other product tools; not a Windows desktop product surface.
- `WINH02-AUD-06` — `[GAP]` — LOW — `mcp_serve.py` L1–7, L309–314, L721 — MCP messaging-conversation bridge, not an agent chat loop.
- `WINH02-AUD-07` — `[GAP]` — LOW — `gateway/platforms/webhook.py` L1–3, L154, L198–224 — inbound HMAC webhook receiver; Zola cannot call into it as a client.
- `WINH02-AUD-12` — `[RISK]` — MEDIUM — `api_server_openai_routes.py` L697–698 vs `tui_gateway/session_lifecycle.py` L380–394, L568–594 — SSE disconnect fail-closes (interrupt); JSON-RPC `client_gone` defers interrupt. Two surfaces disagree on who owns a mid-turn disconnect.
