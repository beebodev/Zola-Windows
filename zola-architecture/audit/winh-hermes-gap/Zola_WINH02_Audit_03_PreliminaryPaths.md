# WINH02 Audit 03 — Preliminary Integration Paths

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

This document does **not** recommend a path. WINH00 records the decision. Each path below is one the Phase 2–3 evidence can support as realistic. Paths that the evidence rules out as a **primary** Windows-client integration (MCP serve, inbound webhooks, dashboard `/api/pty` as the sole chat API) are listed only under "Not a primary path."

Supporting and complicating findings refer to `Zola_WINH02_Audit_01_SurfaceInventory.md` and `Zola_WINH02_Audit_02_DesktopReference.md`.

---

## Path A — Fork / re-theme `apps/desktop`

**What it is:** Keep the Electron + React desktop shell, replace Hermes branding/copy, point the same sidecar + JSON-RPC stack at a Zola-named product.

**Findings that support this path**

- `WINH02-AUD-08` `[MATCH]` — Desktop already speaks the richest agent-loop surface (JSON-RPC over `/api/ws`).
- `WINH02-AUD-09` `[MATCH]` — Sidecar `hermes serve --host 127.0.0.1 --port 0` plus Windows tree-kill already exist (`backend-command.ts`, `main.ts`).
- `WINH02-AUD-10` `[PARTIAL]` — Reconnect, replay (`session.events.since`), and backoff are implemented, not hypothetical.
- `WINH02-AUD-11` — MIT license (`LICENSE`) legally allows fork, copy, and rebrand with notice retained.
- `WINH02-AUD-01` `[MATCH]` — The JSON-RPC catalog already includes streaming, tool events, interrupt, and multi-session identity.

**Findings that undermine or complicate this path**

- `WINH02-AUD-11` `[PARTIAL]` — `productName: "Hermes"`, Nous authorship, and i18n catalogs ("Setting up Hermes Agent") are product-coupled. Electron `main.ts` also owns Hermes remote/SSH/cloud/registry behavior. A re-theme is not a CSS swap.
- `WINH02-AUD-02` `[RISK]` HIGH — Forking the client does not create a versioned contract. The generated OpenRPC version stays `"1"`; `@hermes/shared` stays `0.0.0`. A Zola-branded fork still silently tracks Hermes RPC drift.
- `WINH02-AUD-10` / `WINH02-AUD-12` — Mid-turn disconnect is deferred-interrupt on this surface. Zola's fail-closed lens is not obviously satisfied without extra design.
- WINH01 leftover: Desktop Playwright E2E is Linux-only and hard-disabled (`WINH01-AUD-05`). A Windows-product fork inherits an unproven E2E story on the target OS.

**Unknown until WINH03**

- End-to-end request trace: `prompt.submit` → model → tools → `message.complete`, including what the UI shows if the sidecar dies mid-tool.
- Operational contract: session identity in `state.db`, what `session.resume` after a crash actually restores, and whether `session.interrupt` is synchronous enough for a voice barge-in.
- How much of Electron main is load-bearing for local-only Windows (can SSH/cloud/registry be deleted without breaking spawn + `/api/ws`).

---

## Path B — Fresh native Windows client against the JSON-RPC / WebSocket gateway

**What it is:** Build a Zola-branded Windows UI (WinUI, WPF, or a new Electron/WebView shell) that vendors or reimplements the `apps/shared` client (`JsonRpcGatewayClient` + generated contract) and optionally copies Desktop's sidecar spawn (`serveBackendArgs`) without taking the Hermes React UI.

**Findings that support this path**

- `WINH02-AUD-01` `[MATCH]` — Same contract Desktop uses: `prompt.submit`, `message.delta`, `tool.start`, `session.interrupt`, `_sessions`.
- `WINH02-AUD-08` `[MATCH]` — `apps/shared` is already the framework-agnostic client; Desktop is one consumer, dashboard is another (`tui_gateway/AGENTS.md` L29–30).
- `WINH02-AUD-09` `[MATCH]` — Sidecar spawn is a small, tested helper (`serveBackendArgs` returns a four-token argv). A new client can copy that without forking React.
- `WINH02-AUD-11` `[PARTIAL]` — Phase 3's own conclusion: connection logic lives in `apps/shared` and is separable from UI. This path is the one that conclusion describes as cheaper than re-theming.
- `WINH02-AUD-04` `[PARTIAL]` — Connecting to `/api/ws` on `hermes serve` is exactly what Desktop does; the dashboard SPA is not required (`HERMES_SERVE_HEADLESS=1`).

**Findings that undermine or complicate this path**

- `WINH02-AUD-02` `[RISK]` HIGH — No published SDK, package `0.0.0`, OpenRPC `version: "1"`. A packaged Zola build can break on `hermes update` without a version gate. Mitigations (pin a Hermes tag; ship Hermes as a sidecar at a known SHA; probe methods at connect time) are design work, not existing mechanism.
- `WINH02-AUD-02` / `tui_gateway/AGENTS.md` L1–4 — The catalog is explicitly internal ("three consumers"). Nous can change methods without a third-party stability promise.
- `WINH02-AUD-12` `[RISK]` — Client-gone handling is deferred interrupt. A new client that assumes "socket drop stops the agent" would be wrong.
- `WINH02-AUD-04` `[RISK]` — Auth is a process session token (or loopback exemption), not a long-lived pairing document. A client that does not spawn the sidecar must invent pairing against whatever `hermes serve` is already running.
- Approvals, sudo, clarify, vault, and desktop read/act bridges are **server→client requests** on this wire (`tui_gateway/AGENTS.md` L21–28). A "thin" client that only implements `prompt.submit` + `message.delta` would stall the agent on the first approval. Completeness of that request catalog is a WINH03 concern.

**Unknown until WINH03**

- Minimum method/event/request subset a non-Hermes UI must implement before a real turn completes (especially approvals and slash commands).
- Whether `apps/shared` can be consumed from outside the npm workspace (it is `"private": true`) or must be vendored as source.
- Exact reconnect replay guarantees after a Windows sleep/wake or a killed `hermes serve` child.
- How session identity should map onto Zola's "single authority" (Desktop already runs one socket per profile plus a primary; who owns the live turn).

---

## Path C — Client against the OpenAI-compatible HTTP API only

**What it is:** Treat Hermes as a local OpenAI-compatible backend (`API_SERVER_ENABLED`, `http://127.0.0.1:8642/v1`, `API_SERVER_KEY`). Zola's Windows UI is an OpenAI chat client (optionally with Hermes extensions: `hermes.tool.progress`, `/v1/runs`, `/api/sessions`).

**Findings that support this path**

- `WINH02-AUD-03` `[PARTIAL]` — Documented for third-party frontends (`api-server.md` L7–9). Streaming, tool-progress SSE, and `POST /v1/runs/{run_id}/stop` exist.
- `WINH02-AUD-03` — `GET /v1/capabilities` is a real feature-discovery endpoint, unlike JSON-RPC's literal `"1"`.
- `WINH02-AUD-12` — SSE client disconnect **interrupts** the agent (`api_server_openai_routes.py` L697–698). Closer to Zola's fail-closed lens than JSON-RPC `client_gone`.
- No dependency on `@hermes/shared`, Electron, or the internal RPC catalog.

**Findings that undermine or complicate this path**

- `WINH02-AUD-03` `[PARTIAL]` — First-party Desktop/TUI/dashboard do **not** use this API for the product chat UI. Zola would be a third-party-shaped client, not following the official desktop reference.
- `WINH02-AUD-01` vs `WINH02-AUD-03` — Approvals, slash catalog, session replay, server→client requests, and `gateway.ready` skin/session protocol live on JSON-RPC, not on `/v1/chat/completions`.
- `WINH02-AUD-03` `[RISK]` — Hermes extensions (`hermes.tool.progress`, `/v1/runs`) are not OpenAI-versioned. Capability bits help but are not a semver.
- `WINH02-AUD-09` — Desktop's sidecar is `hermes serve` (dashboard/JSON-RPC host), not `hermes gateway` (which is what starts the API server per `api-server.md` L31–39). A Path C client must start or assume a **different** Hermes process than the official desktop app, unless later evidence shows `serve` also exposes `/v1/*` (not established in this prompt; WINH03).
- Concurrent-run cap (`max_concurrent_runs`) is an operational limit a voice-first client might hit (`api_server.py` L1164–1168).

**Unknown until WINH03**

- Whether `hermes serve` (Desktop's sidecar) exposes the OpenAI API on the same port, or only `hermes gateway` does. That single fact decides whether Path C can share Desktop's process model.
- Whether `/v1/chat/completions` plus `/api/sessions` can resume a crashed turn the way `session.resume` + `session.events.since` can.
- How tool progress, memory writes, and approvals appear on this wire compared to JSON-RPC (the SSE event is `hermes.tool.progress`; approval UX is unspecified here).
- Auth lifetime of `API_SERVER_KEY` vs dashboard session token for a packaged install.

---

## Path D — ACP stdio adapter (IDE-shaped, not a standalone Windows shell)

**What it is:** Zola hosts or embeds Hermes as an ACP agent (`hermes acp` / `hermes-acp`), or Zola itself becomes an ACP client talking stdio JSON-RPC. Included because the evidence shows a real, documented, versioned-via-ACP public protocol — not because it looks like a Windows product app.

**Findings that support this path**

- `WINH02-AUD-05` `[PARTIAL]` — Public docs, streaming `session_update`, tool calls, `cancel()`, `SessionManager`, ACP `0.9.0` pin.
- Auth handshake is specified (`acp_adapter/auth.py`).

**Findings that undermine or complicate this path**

- `WINH02-AUD-05` `[GAP]` as a Windows **product** surface — ACP is what editors spawn. Zola-Windows is specified as a desktop client, not an editor plugin.
- `hermes-acp` toolset drops `cronjob` and other product tools (`toolsets-reference.md` L97). Self-improvement / scheduled automation (later WINH prompts) would start from a reduced toolset.
- Stdio is one process pair, not a reconnectable WebSocket with `session.events.since`.

**Unknown until WINH03**

- Only relevant if WINH00 even considers an editor-host architecture. Request trace would be ACP `session/prompt` → Hermes turn → `session_update`, which is a different operational contract than Desktop's.

---

## Not a primary path (evidence already sufficient)

| Candidate | Why it is not a primary Windows-client integration | Finding |
|---|---|---|
| Dashboard `/api/pty` | Byte pipe to `hermes --tui` / xterm.js; not a structured agent API | `WINH02-AUD-04` `[GAP]` |
| `hermes mcp serve` | Messaging-conversation bridge for other MCP clients; no agent token stream | `WINH02-AUD-06` `[GAP]` |
| Inbound webhooks | Hermes is the HTTP **server**; Zola would be posting events in, not driving a session | `WINH02-AUD-07` `[GAP]` |

These can still appear as **secondary** features later (Zola posting a webhook, or exposing MCP). They do not replace a chat/voice client contract.

---

## Cross-cutting unknowns for every remaining path (WINH03)

WINH03 is titled "Integration Request Trace & Operational Contract." Regardless of which path WINH00 picks, the following are not settled by WINH02:

1. One full turn on the chosen wire: user text in → tokens out → tool events → terminal/file side effects → final message, with named functions.
2. Mid-turn disconnect and mid-turn cancel: which authority wins (agent, client, `state.db`), and whether the result is fail-closed or deferred (`WINH02-AUD-12`).
3. Session resume after process death: what is durable vs in-memory (`_sessions` vs sqlite).
4. For Path B/C: the exact process Zola must launch (`hermes serve` vs `hermes gateway` vs both) and which ports/auth secrets that process requires.
5. For Path A/B: the minimum server→client request set that must be implemented so the agent does not block forever on `approval` / `clarify` / `sudo`.

No path is recommended here.
