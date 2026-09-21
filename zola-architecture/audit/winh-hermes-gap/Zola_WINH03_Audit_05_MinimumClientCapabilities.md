# WINH03 Audit 05 — Minimum Viable Client Capability Set

Pinned tag: `v2026.9.14`
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Server→client **requests** (blocking questions), not events. Catalog: `tui_gateway/contracts/server_requests.py`. Send/wait: `tui_gateway/server_requests.py` `send` L101–123. Default one-string helper: `server.py` `_ask` L1306–1312 (timeout default **300s**; empty string on skip/timeout/cancel).

If the client never answers: `send` waits `timeout`, then `_emit_cancel` and returns `None` (or clarify batch `{answers, timed_out}`). **Default is not hang-forever.** `timeout=None` waits until answered or cancelled (`server_requests.py` L107).

---

## 1. Every server→client request type

| Request | Declared | Typical timeout | If client has no handler | How it is reached |
|---|---|---|---|---|
| `approval` | `server_requests.py` L94 | Queue-owned; `approvals.timeout` default **300s** (`approval_context.py` L239–248) | Timeout → timeout/deny path (`approval_prompt.py` L35–41, L133). Turn unblocks. | Dangerous/flagged **terminal** (and similar) tools. **Core agent loop** if those tools run — not optional chrome. |
| `clarify` | L58 | `get_clarify_timeout()` default **3600s**; `<= 0` = unlimited (`clarify_gateway.py` L272–277; `server.py` `_clarify_timeout_seconds` L1315–1322) | After timeout: empty / skip. **If configured unlimited, hang until answer or interrupt.** | `clarify` tool (`agent_callbacks.py` L106–107). Toolset-dependent. |
| `sudo` | L105 | **120s** (`agent_callbacks.py` L171) | Empty string → sudo fails closed for that prompt | `terminal` sudo password callback. Core terminal, not a plugin. |
| `secret` | L115 | `_ask` default **300s** (L165) | Skip object (`skipped: True`) | `skills_tool` secret capture — when a skill asks to store a secret. |
| `vault.unlock_prompt` | L124 | **120s** (L179–180) | Empty → unlock fails | External password-manager unlock. Vault-enabled only. |
| `vault.save_login` | L133 | **180s** (L184) | Empty → not saved | Vault save-login prompt. |
| `vault.code` | L142 | `_ask` default **300s** (L192) | Empty | Vault OTP/code. |
| `mcp.setup` | L152 | **600s** (L116–117) | Empty → setup skipped | Desktop GUI MCP consent/OAuth. |
| `terminal.read` | L164 | **30s** (L108) | Empty | Desktop/TUI GUI read of terminal buffer. |
| `preview.read` | L166 | **45s** (L109) | Empty | Desktop preview pane. |
| `window.read` | L168 | **30s** (L113) | Empty | Desktop native window list. |
| `preview.act` | L187 | **45s** (L111) | Empty | Desktop preview drive/annotate. |
| `tour` | L212 | `_tour_request` (see `server.py` L1376) | Empty / skip | Desktop onboarding tour (`tour_callback` L119). |

`request.cancel` is an **event** that withdraws an open request (`contracts/server_requests.py` L220), not a request the client must implement as a handler.

**Does a missing handler hang the turn?** At shipped defaults: **no, it waits then fails/skips** (approval 300s, clarify 3600s, sudo 120s, …). Hang-forever only if clarify timeout is configured `<= 0`, or a `send(..., timeout=None)` path is used (tests do this; production `_ask` passes a number).

---

## 2. Core vs optional (how "minimum" a client can be)

**Must implement for a real agent turn that uses the terminal (Zola-relevant):**

- **`approval`** — otherwise every flagged command blocks the turn thread up to 300s, then denies. A client that only handles `prompt.submit` + `message.delta` will look "stuck" then fail closed on the tool (deny), not crash. That is a bad UX but not a deadlock at default timeout.
- Streaming **events** (not requests): `message.delta`, `message.complete`, `tool.start` / `tool.complete` — required to show a turn; they do not block the agent if ignored (except UX).
- **`session.interrupt`** (client→server method) if Zola wants fail-closed on user barge-in / disconnect (`WINH03-AUD-07`).

**Triggered by core tools, not plugins:**

- `sudo` — native `terminal` sudo
- `clarify` — if the `clarify` tool is in the active toolset (dropped in `hermes-acp`; present on Desktop/TUI default)

**Only if those features are enabled / Desktop GUI tools run:**

- vault.* — vault backends configured
- `secret` — skill secret capture
- `mcp.setup`, `terminal.read`, `preview.*`, `window.read`, `tour` — Desktop GUI bridges (`agent_callbacks.py` L108–119). A headless WinUI client that never enables those callbacks will not receive them **unless** the agent still invokes those tools.

Minimum viable **non-Desktop** client: JSON-RPC connect + `session.create`/`resume` + `prompt.submit` + event handlers + **`approval` (and `approval.respond`)** + preferably `clarify` + `sudo`. Skip GUI bridges until those tools are in the toolset.

---

## 3. Can `apps/shared` be consumed outside the Hermes npm workspace?

**Yes, as a `file:` dependency, without publishing to npm.** It is `"private": true`, `"version": "0.0.0"` (`WINH02-AUD-02` — standing risk, not re-litigated).

Concrete mechanism already used in-tree:

- Desktop: `"@hermes/shared": "file:../shared"` (`apps/desktop/package.json` L95)
- Web dashboard: `"@hermes/shared": "file:../apps/shared"` (`web/package.json` L18)

A Zola repo can:

```json
"@hermes/shared": "file:../hermes-agent/apps/shared"
```

or vendor `apps/shared/src/` (especially `gateway-contract.generated.ts`, which is generated and `DO NOT EDIT`).

Root `package.json` `workspaces: ["apps/*", ...]` is how Hermes links it during `npm install` in the monorepo. An **external** project does not need to join that workspace; npm `file:` copies/links the package. TypeScript consumers import from the package `exports` (`apps/shared/package.json` `"."`: `./src/index.ts`).

**Caveats (not blockers to "can we depend"):**

- Pin a Hermes tag/SHA; `0.0.0` will not warn on breaking RPC (`WINH02-AUD-02`).
- Regenerated contract must match the `hermes serve` you spawn.
- `npm pack` of a private package is possible but not the in-tree pattern.

**Finding:** `WINH03-AUD-12` (request set), `WINH03-AUD-13` (`file:` consumption).
