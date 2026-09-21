# WINH02 Audit 02 — Desktop App Reference Architecture

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`
Clone path (external): `C:\Users\test\Dev\hermes-agent`

Read: `apps/desktop/` (README, Electron main process, backend spawn, renderer gateway) and `apps/shared/` (JSON-RPC client + generated contract). This is a reference-architecture study of Hermes's first-party Electron app, not a decision about whether Zola should fork it.

---

## 1. Which Phase 2 surface does official Desktop actually use?

**Answer:** Surface 3 — TUI/Desktop JSON-RPC — transported over the dashboard process's `/api/ws` WebSocket. Desktop does not speak the OpenAI HTTP API, ACP, MCP, or webhooks for chat.

Connection-establishing code:

- Renderer client: `apps/desktop/src/api/client.ts` L28–37 — `class HermesGateway extends JsonRpcGatewayClient` from `@hermes/shared`.
- Shared transport: `apps/shared/src/json-rpc-gateway.ts` (`JsonRpcGatewayClient.connect`).
- Boot / reconnect: `apps/desktop/src/app/gateway/hooks/use-gateway-boot.ts` (imports `reconnectBackoffDelayMs`); store routing `apps/desktop/src/store/gateway.ts` (multi-profile sockets, L18–26).
- URL shape (tests as evidence of the live path): `apps/desktop/electron/ssh-isolated-keepalive.test.ts` L63, L108 — `ws://127.0.0.1:<port>/api/ws?token=...`.

`apps/desktop/README.md` L101–103: "Hermes Agent runs as a headless `hermes serve` process and exposes the `tui_gateway` JSON-RPC/WebSocket API. The renderer connects through `apps/shared`, which is also used by the browser dashboard."

`apps/desktop/src/AGENTS.md` L6–10: "Electron + React + nanostores talking to a `tui_gateway` backend over JSON-RPC (`requestGateway(method, params)`); transport lives in … `apps/shared` (`JsonRpcGatewayClient` + WS URL helpers)."

**Labels:** `[MATCH]` — the official desktop client already picked Surface 3. That is evidence, not a Zola decision.

**Finding:** `WINH02-AUD-08`

---

## 2. Does Desktop launch the Python agent, or connect to a separate `hermes` install?

**Both, in a defined order.** Local mode launches and manages a sidecar `hermes serve` child. Remote/cloud mode connects to a separately running gateway. First-run can also install Hermes or attach to an existing one.

Process-management code:

- Canonical argv: `apps/desktop/electron/backend-command.ts` `serveBackendArgs()` L18–21 — `['serve', '--host', '127.0.0.1', '--port', '0']` (optional `--profile <name>` prefix). Port `0` means the OS assigns a loopback port.
- Legacy fallback: same file `dashboardFallbackArgs()` L30–37 rewrites `serve` → `dashboard --no-open` when the resolved runtime predates `serve` (`apps/desktop/src/AGENTS.md` L17–21; `electron/main.ts` comments around L2585).
- Lifecycle object: `apps/desktop/electron/main.ts` L1418–1428 `createLocalBackendLifecycle` — `stopChild` calls `stopBackendChildImpl` with `forceKillProcessTree` on Windows (`IS_WINDOWS`).
- README L90–117: packaged app can install the runtime into `HERMES_HOME` (`%LOCALAPPDATA%\hermes` on Windows); resolution ladder is env root → source checkout → managed install → `hermes` on PATH → system Python → bootstrap installer.
- README L133–138: when no local runtime or saved remote exists, first-run offers **Connect to existing Hermes** before the local installer.
- Messaging gateway is **not** the same process: `apps/desktop/src/AGENTS.md` L23–24 — `serve` dies with the app; the messaging gateway is spawned detached via `/api/gateway/*` and must not be re-parented under the backend.

A Windows Zola client **could** do the same thing: spawn `hermes serve --host 127.0.0.1 --port 0`, read the bound port, connect to `/api/ws` with the session token the serve process expects (`HERMES_DASHBOARD_SESSION_TOKEN`, `web_server.py` L304–311). That pattern is already implemented in this tag. Whether Zola *should* bundle/spawn Hermes is out of scope here.

**Labels:** `[MATCH]` — sidecar spawn is real, tested (`backend-command.test.ts` L7–12), and documented. `[PARTIAL]` — Desktop is not spawn-only; remote attach is a first-class path, so "the desktop always owns the Python process" is false.

**Finding:** `WINH02-AUD-09`

---

## 3. Backend disconnect / crash mid-session

Reconnect and error handling **were found**. They are split across the shared client, the renderer boot hook, and Electron process teardown.

**Client reconnect / replay (renderer):**

- `apps/shared/src/json-rpc-gateway.ts`: `replay` option defaults true (L27, L142); after reconnect it fetches `session.events.since`; `replayEpoch` from `gateway.ready` detects a new backend process so seq watermarks are not reused across process deaths (L121–127).
- `apps/shared/src/reconnect-backoff.ts`: exponential backoff with full jitter, default base 300 ms, cap 15 s (L27–28, L39+). Used by Desktop `use-gateway-boot.ts` and `store/gateway.ts` L727.
- `HermesGateway` closed/connect error strings (`client.ts` L31–34): `"Hermes gateway connection closed"` / `"Could not connect to Hermes gateway"`.
- `prompt.submit` ack timeout is 1_800_000 ms so a long turn is not mistaken for a dead socket (`client.ts` L18–26, L24–26).

**Process crash (Electron main):**

- `localBackendLifecycle.stopChild` / `waitForExit` (`main.ts` L1418–1424).
- Windows tree-kill via `forceKillProcessTree` passed into `stopBackendChildImpl` (L1421).
- Comment at `main.ts` L1677: respawn of `hermes serve` children is rate-limited so a broken boot cannot tight-loop.

**Server-side mid-turn disconnect (the Surface 3 contract Desktop relies on):**

- `tui_gateway/session_lifecycle.py` parks a dropped WS session on `_detached_ws_transport` (L380–387). `client_gone` may **defer** interrupt while turn activity is fresh (L568–594), then interrupt and reap. This is the opposite of the OpenAI API's immediate SSE-disconnect interrupt.

**What was not verified by running the app:** whether a crash mid-tool-call always leaves `state.db` consistent; whether the user sees a replayed partial turn or a blank composer; whether Windows `taskkill` of the tree always wins over a stuck ConPTY child. Those are WINH03 / runtime questions. The code paths exist; the UX outcome of each edge is not confirmed here.

**Labels:** `[PARTIAL]` — reconnect + replay + process teardown exist and are substantial. Limitation: mid-turn client-gone is deferred-interrupt, not fail-closed-immediate. A Zola client copying this path inherits that ambiguity unless WINH03 shows the grace window is tight enough to count as fail-closed.

**Finding:** `WINH02-AUD-10`

---

## 4. Could `apps/desktop` realistically be forked and re-themed as a Zola Windows client?

**Legally yes (MIT). Practically: connection logic is separable; the product UI is not a thin skin.**

Basis:

**License.** Root `LICENSE` is MIT (Copyright 2025 Nous Research). `apps/desktop/README.md` L7 badges the same MIT license. Forking/rebranding is permitted with copyright notice retained.

**Language / structure.**

| Layer | Location | Coupled to Hermes branding? |
|---|---|---|
| JSON-RPC client, reconnect, generated contract | `apps/shared/` (`JsonRpcGatewayClient`, `gateway-contract.generated.ts`, `reconnect-backoff.ts`) | No product chrome. Package name `@hermes/shared` is the main coupling. |
| Sidecar spawn, Windows tree-kill, port 0, remote SSH | `apps/desktop/electron/` (`backend-command.ts`, `backend-child`, `main.ts`) | Process names/`hermes serve` argv; otherwise reusable spawn logic. |
| Chat UI, routes, panes, transcript | `apps/desktop/src/` (React + nanostores + `@assistant-ui/react`) | Yes. |
| Product identity | `apps/desktop/package.json` L2–7: `"name": "hermes"`, `"productName": "Hermes"`, `"description": "Native desktop shell for Hermes Agent."`, `"author": "Nous Research"` | Yes. |
| Copy | `apps/desktop/src/i18n/en.ts` (e.g. L3286, L3309: "Setting up Hermes Agent" / "Let's get you setup with Hermes Agent"); parallel strings in `zh.ts`, `ja.ts`, `ru.ts`, `ar.ts`, `zh-hant.ts` | Yes — branding is in the i18n catalogs, not a single theme file. |
| Skin / theme on the wire | `tui_gateway/AGENTS.md` L60: `gateway.ready` carries skin data; `apps/shared` exports `./skin` | Hermes skin payload from the backend. |

`apps/desktop/src/AGENTS.md` L11: "The desktop has **no build/runtime dependency on the dashboard frontend**" — UI and dashboard SPA are already separate. Connection logic (`apps/shared`) is already separate from UI (`apps/desktop/src`). Electron main (`electron/main.ts`) is a large orchestration file (thousands of lines; remote SSH, media protocol, backend claims) that knows Hermes profile/registry/cloud concepts.

Forking would mean: keep `apps/shared` + a subset of `electron/` spawn/teardown; replace or rewrite `src/` routes, i18n, `productName`, auto-update copy, onboarding that installs "Hermes Agent", and any UI that assumes Hermes slash/skin/cloud. That is closer to "new app that vendors the shared client and copies spawn helpers" than "re-theme the existing app."

Building fresh against `apps/shared` avoids dragging Electron main's remote-registry/SSH/cloud surface and the Hermes i18n catalogs. It still requires a TypeScript consumer of a `private` `0.0.0` workspace package (or a vendored copy of the generated contract).

**Labels:** `[PARTIAL]` — MIT + separable transport. Limitation: UI, i18n, `productName`, onboarding, and Electron main are Hermes-product-coupled enough that a re-theme is not cheaper than a new Windows shell on `apps/shared` by any evidence in this tag.

**Finding:** `WINH02-AUD-11`

---

## 5. Is `apps/shared` / the generated TypeScript contract independently versioned?

**No independent client-detectable contract version that would survive a Hermes update.**

Evidence:

- `@hermes/shared` `package.json`: `"private": true`, `"version": "0.0.0"` (L2–4). Not published to npm as a versioned SDK in this tag.
- `apps/shared/src/gateway-contract.generated.ts` L1–3: "GENERATED by `scripts/gen_gateway_contracts.py` from `tui_gateway/contracts` — DO NOT EDIT." Regenerated from Python; drift is a test failure (`tests/tui_gateway/contracts/test_generated.py`, cited in `tui_gateway/AGENTS.md` L40–41).
- OpenRPC `info.version` is the string `"1"` (`gateway-contract.openrpc.json` L4), not Hermes `0.21.3` and not a changelog-backed semver.
- `JsonRpcGatewayClient` tracks `replayEpoch` for **process instance** identity after reconnect (`json-rpc-gateway.ts` L121–127), not protocol compatibility.
- Desktop app `package.json` version is `"0.17.2"` (`apps/desktop/package.json` L4) — a different number from Hermes Agent `0.21.3`. Two first-party version fields already diverge.

A packaged Zola install that bundled `@hermes/shared` (or a generated client) against a later `hermes serve` could load, connect, and fail on unknown methods / extra-forbid param keys (`tui_gateway/AGENTS.md` L36–38: dispatcher rejects unknown param keys with `4000`) without any version check firing first. Feature discovery on this surface is "call the method and see," plus whatever `gateway.ready` carries (skin, not a contract semver).

The OpenAI API surface is in better shape for detection (`GET /v1/capabilities`) but Desktop does not use it.

**Labels:** `[RISK]` — this is the packaged-client silent-break hazard. Same underlying fact as `WINH02-AUD-02`; recorded here because Phase 3 question 5 asked it of the shared library specifically.

**Finding:** `WINH02-AUD-02` (cross-referenced; no duplicate ID)

---

## Desktop vs a hypothetical Zola client (facts only)

What Desktop already solves that a Zola client would otherwise build:

- Spawn/stop `hermes serve` on loopback with an ephemeral port (`backend-command.ts`).
- Windows process-tree kill (`main.ts` `forceKillProcessTree`).
- JSON-RPC WebSocket client with heartbeat, replay, and jittered reconnect (`apps/shared`).
- Multi-session / multi-profile sockets (`store/gateway.ts`).
- First-run: install runtime or attach remote (README L32–33, L133–138).

What Desktop does **not** give a Zola client for free:

- A stable, versioned public SDK.
- A skin-only fork of the React UI.
- Fail-closed-immediate mid-turn disconnect (JSON-RPC `client_gone` defers).
- Identity/branding isolation.

---

## Findings this document

- `WINH02-AUD-08` — `[MATCH]` — MEDIUM — `apps/desktop/src/api/client.ts` L28–37; `apps/desktop/README.md` L101–103; `apps/desktop/src/AGENTS.md` L6–10 — official Desktop uses Surface 3 JSON-RPC over `/api/ws` via `JsonRpcGatewayClient`.
- `WINH02-AUD-09` — `[MATCH]` / `[PARTIAL]` — MEDIUM — `apps/desktop/electron/backend-command.ts` L18–21; `apps/desktop/electron/main.ts` L1418–1428; README L90–138 — Desktop launches a `hermes serve` sidecar and can instead attach to a remote/existing gateway.
- `WINH02-AUD-10` — `[PARTIAL]` — MEDIUM — `apps/shared/src/json-rpc-gateway.ts` L27, L121–127, L142; `apps/shared/src/reconnect-backoff.ts`; `tui_gateway/session_lifecycle.py` L380–394, L568–594 — reconnect/replay exist; mid-turn disconnect interrupt is deferred.
- `WINH02-AUD-11` — `[PARTIAL]` — MEDIUM — `LICENSE` (MIT); `apps/desktop/package.json` L2–7; `apps/desktop/src/i18n/en.ts` L3286, L3309; `apps/shared/` vs `apps/desktop/src/` — transport is separable; UI/i18n/productName are Hermes-coupled.
