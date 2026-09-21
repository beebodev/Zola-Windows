# WINH03 Audit 01 — Process Model Resolution

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

WINH02 asked whether Path B (JSON-RPC client against `hermes serve`) and Path C (OpenAI HTTP client) can share one spawned process. This document answers from CLI wiring, not from docs alone.

Related: `WINH02-AUD-09` (Desktop spawns `hermes serve`); `WINH02-AUD-03` (OpenAI API lives on the gateway adapter).

---

## 1. Does `hermes serve` start the OpenAI API server adapter?

**No.** Not under any configuration found in this tag.

`hermes serve` is an alias of `hermes dashboard` with `headless_backend=True`. Parser: `hermes_cli/subcommands/dashboard.py` L48–59 (`_configure_serve_parser` sets `func=cmd_dashboard`, `headless_backend=True`, `command="serve"`). Description L68–70: "the JSON-RPC/WebSocket gateway the desktop app and remote clients connect to."

Handler: `hermes_cli/main.py` `cmd_dashboard` L2543–2590 calls `hermes_cli.web_server.start_server(...)` with `headless=_headless_backend`. `start_server` (`web_server.py` L1365–1385) is the FastAPI dashboard: JSON-RPC/WS backend, optional SPA. Docstring L1379–1380: "JSON-RPC/WS backend, no UI build, no SPA mount (`HERMES_SERVE_HEADLESS`)."

`web_server.py` has **zero** references to `API_SERVER`, `/v1/chat/completions`, or `APIServerAdapter`. The OpenAI adapter is not imported or mounted on this process.

The dashboard can **start a separate messaging-gateway process** via REST (`web_server.py` routes `start_gateway` / `restart_gateway` → `hermes_cli.web_routers.ops`). That is a second OS process, not the serve process growing an API port. Desktop `src/AGENTS.md` (WINH02) already stated the messaging gateway is spawned detached via `/api/gateway/*` and must not be re-parented under `serve`.

**Label:** `[GAP]` against "Path C can ride the Desktop sidecar."

---

## 2. Does `hermes gateway` start the JSON-RPC / dashboard surface?

**No, not in-process.**

`hermes gateway` parser: `hermes_cli/subcommands/gateway.py` L39–40 — "Manage the messaging gateway (Telegram, Discord, …)". Handler: `hermes_cli/main.py` `cmd_gateway` L1769–1775 → `hermes_cli.gateway.gateway_command` → `gateway.run.start_gateway` (`gateway/run.py` L5195+).

`start_gateway` constructs `GatewayRunner` and runs messaging platform adapters (including `APIServerAdapter` when `API_SERVER_ENABLED` / platform config enables it). It does **not** call `web_server.start_server`. It does not bind `/api/ws`.

Docker/s6 can run a **second supervised service** `hermes dashboard` when `HERMES_DASHBOARD=1` (`website/docs/user-guide/docker.md`; `docker/s6-rc.d/dashboard/run`). That is still two processes in one container, not one process exposing both surfaces.

`gateway/run_startup.py` L666–668 imports `tui_gateway` for Group Chat workers. That is not the Desktop `/api/ws` listener.

**Label:** `[GAP]` against "Path B can ride `hermes gateway` alone."

---

## 3. Can a single process expose both surfaces simultaneously?

**Not as a supported process mode in this tag.** They are mutually exclusive entry points that share config/home, not one binary mode with a flag that mounts both listeners.

| Process | Command | Listener | Surfaces |
|---|---|---|---|
| Dashboard / Desktop sidecar | `hermes serve` / `hermes dashboard` | FastAPI, default `127.0.0.1:9119` (`--port 0` = OS assign) | JSON-RPC `/api/ws`, PTY `/api/pty`, dashboard REST. **No** `/v1/chat/completions`. |
| Messaging gateway | `hermes gateway run` (or installed service) | Per-adapter (API server default `127.0.0.1:8642`) | OpenAI HTTP API when enabled, webhooks, chat platforms. **No** Desktop JSON-RPC `/api/ws`. |

A host can run **both processes at once** (Desktop already does: serve sidecar + optional detached gateway). That is two PIDs, two ports, two auth secrets (`HERMES_DASHBOARD_SESSION_TOKEN` vs `API_SERVER_KEY`).

No config flag was found that makes `start_server` construct `APIServerAdapter`, or that makes `GatewayRunner` bind FastAPI `/api/ws`.

**Label:** `[GAP]` — Path B and Path C cannot share one spawned process.

---

## 4. What `serveBackendArgs()` actually launches

`apps/desktop/electron/backend-command.ts` L18–21:

```ts
return [...head, 'serve', '--host', '127.0.0.1', '--port', '0']
```

Against this tag that argv is:

1. Subcommand `serve` → `cmd_dashboard` with `headless_backend=True` (`dashboard.py` L59).
2. `start_server(host="127.0.0.1", port=0, headless=True)` (`main.py` L2580–2590).
3. Uvicorn/FastAPI on loopback, **ephemeral OS port** (not 9119, not 8642).
4. Surfaces that come up: `/api/ws` (Surface 3 JSON-RPC, `chat_ws.py` `gateway_ws`), `/api/pty`, other `/api/*` dashboard REST. SPA is not mounted.
5. Auth: process session token (`WINH02-AUD-04` / `web_server.py` L304–311), typically minted as `HERMES_DASHBOARD_SESSION_TOKEN` by Desktop.

It does **not** start `hermes gateway`. It does **not** bind the OpenAI API port.

---

## Label against "Path B and Path C can share one spawned process"

**No.** `[GAP]`

- Path B's process is `hermes serve` (JSON-RPC on an ephemeral loopback port).
- Path C's process is `hermes gateway` with `API_SERVER_ENABLED` (OpenAI HTTP on 8642 by default).
- Sharing requires **two** processes (what Desktop already does for messaging, not for the OpenAI API).

**Finding:** `WINH03-AUD-01`

---

## Ports / secrets a Windows client must launch (WINH02 cross-cutting unknown #4)

| Path | Process to spawn | Port | Auth |
|---|---|---|---|
| A / B | `hermes serve --host 127.0.0.1 --port 0` | OS-assigned loopback; discover from serve ready/log as Desktop does | `HERMES_DASHBOARD_SESSION_TOKEN` (or loopback exemption) |
| C | `hermes gateway` (foreground `run` or service) with API server enabled | `API_SERVER_PORT` / config default 8642 | `API_SERVER_KEY` (startup-guarded; `WINH02-AUD-03`) |
| A/B + messaging | serve **plus** detached `hermes gateway` via `/api/gateway/*` | both | both secrets |

`API_SERVER_KEY` is durable in `~/.hermes/.env` if the operator set it. Dashboard session token is process-ephemeral unless pinned (`WINH02-AUD-04`).
