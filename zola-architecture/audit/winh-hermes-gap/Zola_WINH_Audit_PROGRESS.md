# Zola WINH Hermes Gap Analysis — Progress

Shared across the entire WINH series (WINH01–11 + WINH00). Later prompts extend this file; they must not replace the Hermes pin recorded here.

## Hermes pin (set once by WINH01 — do not change)

- Release tag: `v2026.9.14`
- Marketing version: Hermes Agent v0.21.3 (`pyproject.toml` `[project].version = "0.21.3"`)
- Commit SHA: `345cd2b057a452236de401d3534b8502a7465e8d`
- Annotated tag object: `7a963716b81be13ba513d4f127633b7da493aff2` (type `tag`; peels to the commit above)
- Tag creator date (local git): 2026-09-14 09:04:09 -0700
- GitHub release published: 2026-09-14T16:04:14Z
- GitHub release flags: `draft: false`, `prerelease: false` (confirmed via `https://api.github.com/repos/NousResearch/hermes-agent/releases/latest`)
- Clone path (external, not in this repo): `C:\Users\test\Dev\hermes-agent`
- Checkout state: detached HEAD at `v2026.9.14`

### Five most recent local tags (by `git tag --sort=-creatordate`)

1. `v2026.9.14` — 2026-09-14 09:04:09 -0700 — Hermes Agent v0.21.3 (v2026.9.14)
2. `v2026.9.11` — 2026-09-11 12:20:28 -0700 — Hermes Agent v0.21.2 (v2026.9.11) — The state.db Patch Release
3. `v2026.9.7` — 2026-09-07 15:16:56 -0700 — Hermes Agent v0.21.1 (2026.9.7)
4. `v2026.8.31` — 2026-08-31 12:29:39 -0700 — Hermes Agent v0.21.0 (2026.8.31)
5. `v2026.8.27` — 2026-08-27 05:06:48 -0700 — Hermes Agent v0.20.6 (2026.8.27)

Cross-check: GitHub Releases list and `/releases/latest` both name `v2026.9.14` as the latest published non-prerelease. The series audits this tag, not `main` (`main` at clone time was `bb359ec5c1d5da6a66f00ee11f0ad7a86defaee2`).

## Zola-Windows branch

- Shared branch: `winh-hermes-audit`
- Created from: `main` at `4ff1abf2cf20c4a1bdcdb59ea99fd8eaabb66cb3`
- Output directory: `zola-architecture/audit/winh-hermes-gap/`

WINH01 setup note: this workspace had no `.git` when the prompt started. `main` was initialized with the existing `zola-architecture/` documents (clean tree), then `winh-hermes-audit` was created from that `main`. The sibling path `C:\Users\test\Dev\hermes-agent` existed as an empty directory and was cloned from `https://github.com/NousResearch/hermes-agent` (not added as a submodule, not copied into this repo).

## Series phase table

- WINH01 — Setup, Repo Map, Native Windows Runtime — COMPLETE
- WINH02 — Hermes Integration Surface Inventory & Desktop Reference Architecture — COMPLETE
- WINH03 — Integration Request Trace & Operational Contract — COMPLETE
- WINH04 — Memory & Skills — PENDING
- WINH05 — Self-Improvement & Capability Acquisition — PENDING
- WINH06 — Authority, Governance & Routing — PENDING
- WINH07 — Tool Calling, Subagents & Scheduled Automation — PENDING
- WINH08 — Voice Pipeline & Voice Identity — PENDING
- WINH09 — Messaging Surfaces — PENDING
- WINH10 — Windows Security & Deployment — PENDING
- WINH11 — Relational Intelligence & Model Provider Flexibility — PENDING
- WINH00 — Synthesis + Closeout — PENDING

WINH00 is the only prompt that merges or closes the branch.

## Guardrails (entire series)

- G-SCOPE: Diagnostic audit only. Read Hermes at `C:\Users\test\Dev\hermes-agent` (pinned tag) and the Zola-Windows documents listed in each prompt. Produce findings only under `zola-architecture/audit/winh-hermes-gap/`.
- G-NOCHANGE: Zero source modifications in Hermes. Zero modifications in Zola-Windows outside this output directory.
- G-QUALITY: Every finding names a specific file, directory, function, config key, or line in tag `v2026.9.14`. If docs and code conflict, report both.
- G-CLOSEOUT: Deferred to WINH00. This series does not merge, push a final state, or delete the branch until WINH00.

## Repo map (WINH01 Phase 2)

Later prompts should start here:

- [Zola_WINH01_Audit_01_RepoMap.md](./Zola_WINH01_Audit_01_RepoMap.md)

Windows runtime findings:

- [Zola_WINH01_Audit_02_WindowsRuntime.md](./Zola_WINH01_Audit_02_WindowsRuntime.md)

## Integration surfaces (WINH02 Phase 2–4)

- [Zola_WINH02_Audit_01_SurfaceInventory.md](./Zola_WINH02_Audit_01_SurfaceInventory.md)
- [Zola_WINH02_Audit_02_DesktopReference.md](./Zola_WINH02_Audit_02_DesktopReference.md)
- [Zola_WINH02_Audit_03_PreliminaryPaths.md](./Zola_WINH02_Audit_03_PreliminaryPaths.md)

WINH02 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (matches the pin above). No re-clone, no new branch, no re-pin.

Preliminary paths named for WINH00 (no decision in this prompt): (a) fork/re-theme `apps/desktop`; (b) fresh native Windows client against the JSON-RPC/WebSocket gateway; (c) client against the OpenAI-compatible HTTP API only; (d) ACP stdio adapter (IDE-shaped, not a standalone Windows shell).

## Operational contract (WINH03 Phase 2–7)

- [Zola_WINH03_Audit_01_ProcessModel.md](./Zola_WINH03_Audit_01_ProcessModel.md)
- [Zola_WINH03_Audit_02_RequestTrace.md](./Zola_WINH03_Audit_02_RequestTrace.md)
- [Zola_WINH03_Audit_03_DisconnectReconciliation.md](./Zola_WINH03_Audit_03_DisconnectReconciliation.md)
- [Zola_WINH03_Audit_04_SessionDurability.md](./Zola_WINH03_Audit_04_SessionDurability.md)
- [Zola_WINH03_Audit_05_MinimumClientCapabilities.md](./Zola_WINH03_Audit_05_MinimumClientCapabilities.md)
- [Zola_WINH03_Audit_06_Synthesis.md](./Zola_WINH03_Audit_06_Synthesis.md)

WINH03 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match). Process model: Path B (`hermes serve`) and Path C (`hermes gateway` + API server) cannot share one spawned process. Disconnect/fail-closed: Surface 3 default is fail-open for healthy detached turns (20s grace, 600s activity freshness); Surface 1 SSE interrupt remains fail-closed.

## Running findings list

- WINH01-AUD-01 — [PARTIAL] — MEDIUM — `README.md` L43-45; `website/docs/user-guide/windows-native.md` L85-102 — Native Windows is a first-class install path, but the project's own feature matrix does not claim full Linux/macOS parity.
- WINH01-AUD-02 — [GAP] — HIGH — `tools/lazy_deps.py` `_unsupported_feature_reason` L341-343; `pyproject.toml` L387-392 — Matrix E2EE (`python-olm`) is explicitly unsupported on native Windows; docs tell users to use WSL.
- WINH01-AUD-03 — [RISK] — MEDIUM — `website/docs/user-guide/windows-native.md` L99-102 vs `hermes_cli/web_server_chat.py` L26-33 and `hermes_cli/win_pty_bridge.py` — Dashboard `/chat` docs still say POSIX-PTY / WSL-only; this tag ships a ConPTY `WinPtyBridge`. Docs and code conflict.
- WINH01-AUD-04 — [RISK] — MEDIUM — `.github/workflows/tests.yml`; `.github/workflows/tests-os.yml`; `.github/workflows/ci.yaml` L73-92 — Default pytest suite is Linux-only. Windows CI runs only `@pytest.mark.windows_only` tests, not the full suite.
- WINH01-AUD-05 — [RISK] — MEDIUM — `.github/workflows/ci.yaml` L123-139; `.github/workflows/e2e-desktop.yml` L18-23 — Desktop Playwright E2E is Linux-only and currently hard-disabled (`if: false`).
- WINH01-AUD-06 — [GAP] — LOW — `native/fts5_cjk/build.sh` L1-19 — CJK FTS5 tokenizer builds a `.so` with `gcc`; no Windows/MSVC path in this tag.
- WINH01-AUD-07 — [PARTIAL] — MEDIUM — `tools/environments/local.py` `_find_bash` / `_windows_bash_candidates` L364-413 — Native Windows shell execution goes through Git Bash (`bash.exe`), not cmd/PowerShell; documented as the POSIX-compat strategy.
- WINH01-AUD-08 — [MATCH] — LOW — `scripts/install.ps1`; `pyproject.toml` L19-141; `website/docs/user-guide/windows-native.md` L66-79 — Default native install is `uv` plus CPython 3.11 wheels plus PortableGit/Node; no Visual Studio Build Tools required for the core path.
- WINH01-AUD-09 — [RISK] — LOW — `tests/install/KNOWN_FAILURES.md` — No in-repo `KNOWN_ISSUES.md`. The only tracked Windows issues file is historical installer/updater known-failures, not live bugs.
- WINH02-AUD-01 — [MATCH] — MEDIUM — `tui_gateway/server.py` L85; `tui_gateway/AGENTS.md` L19–30, L53–57; `apps/desktop/src/api/client.ts` L28–37 — JSON-RPC gateway is the only surface that already carries the full first-party agent-loop contract and is exercised by Desktop, TUI, and dashboard `/api/ws`.
- WINH02-AUD-02 — [RISK] — HIGH — `tui_gateway/AGENTS.md` L1–4; `apps/shared/package.json` L2–4 (`version: 0.0.0`); `apps/shared/src/gateway-contract.openrpc.json` L3–5 (`version: "1"`); `gateway-contract.generated.ts` L1–3 — internal, generated, un-semvered contract. A packaged Zola client cannot detect a breaking Hermes update from version numbers alone.
- WINH02-AUD-03 — [PARTIAL] — MEDIUM — `gateway/platforms/api_server.py` L1–6; `website/docs/user-guide/features/api-server.md` L7–9, L109–112; `api_server_openai_routes.py` L668; `api_server_runs.py` L862–883 — public OpenAI-compatible API with streaming, tool progress, and stop; missing the first-party RPC catalog Desktop actually uses.
- WINH02-AUD-04 — [PARTIAL] / [GAP] / [RISK] — MEDIUM — `hermes_cli/web_routers/chat_ws.py` L555–574; `hermes_cli/web_server_chat.py` L26–28; `hermes_cli/web_server.py` L304–311 — dashboard hosts Surface 3 at `/api/ws` and a PTY embed at `/api/pty`; session token is process-ephemeral.
- WINH02-AUD-05 — [PARTIAL] / [GAP] — MEDIUM — `acp_adapter/server.py` L1, L613–628; `website/docs/user-guide/features/acp.md`; `website/docs/reference/toolsets-reference.md` L97 — public ACP stdio for IDEs; `hermes-acp` toolset drops cron and other product tools; not a Windows desktop product surface.
- WINH02-AUD-06 — [GAP] — LOW — `mcp_serve.py` L1–7, L309–314, L721 — MCP messaging-conversation bridge, not an agent chat loop.
- WINH02-AUD-07 — [GAP] — LOW — `gateway/platforms/webhook.py` L1–3, L154, L198–224 — inbound HMAC webhook receiver; Zola cannot call into it as a client.
- WINH02-AUD-08 — [MATCH] — MEDIUM — `apps/desktop/src/api/client.ts` L28–37; `apps/desktop/README.md` L101–103; `apps/desktop/src/AGENTS.md` L6–10 — official Desktop uses Surface 3 JSON-RPC over `/api/ws` via `JsonRpcGatewayClient`.
- WINH02-AUD-09 — [MATCH] / [PARTIAL] — MEDIUM — `apps/desktop/electron/backend-command.ts` L18–21; `apps/desktop/electron/main.ts` L1418–1428; README L90–138 — Desktop launches a `hermes serve` sidecar and can instead attach to a remote/existing gateway.
- WINH02-AUD-10 — [PARTIAL] — MEDIUM — `apps/shared/src/json-rpc-gateway.ts` L27, L121–127, L142; `apps/shared/src/reconnect-backoff.ts`; `tui_gateway/session_lifecycle.py` L380–394, L568–594 — reconnect/replay exist; mid-turn disconnect interrupt is deferred.
- WINH02-AUD-11 — [PARTIAL] — MEDIUM — `LICENSE` (MIT); `apps/desktop/package.json` L2–7; `apps/desktop/src/i18n/en.ts` L3286, L3309; `apps/shared/` vs `apps/desktop/src/` — transport is separable; UI/i18n/productName are Hermes-coupled.
- WINH02-AUD-12 — [RISK] — MEDIUM — `api_server_openai_routes.py` L697–698 vs `tui_gateway/session_lifecycle.py` L380–394, L568–594 — SSE disconnect fail-closes (interrupt); JSON-RPC `client_gone` defers interrupt. Two surfaces disagree on who owns a mid-turn disconnect. Restated with mechanism in WINH03-AUD-05 / WINH03-AUD-08.
- WINH03-AUD-01 — [GAP] — MEDIUM — `hermes_cli/subcommands/dashboard.py` L48–59; `hermes_cli/main.py` `cmd_dashboard` L2543–2590 / `cmd_gateway` L1769–1775; `web_server.py` `start_server` L1365–1385 (no API_SERVER); `gateway/run.py` `start_gateway` L5195 — `hermes serve` does not start the OpenAI API; `hermes gateway` does not bind `/api/ws`. Path B and Path C cannot share one spawned process.
- WINH03-AUD-02 — [MATCH] — LOW — `tui_gateway/methods_prompt.py` L544–662; `prompt_turn.py` `_run_prompt_submit` / `_invoke_agent`; `conversation_loop.py` `run_conversation` L1573; `turn_api_call.py` `perform_api_call` L61; `turn_tool_round.py` `run_tool_round` L45; `run_agent.py` `_execute_tool_calls` L1273 — one JSON-RPC turn traced as a named-function chain.
- WINH03-AUD-03 — [MATCH] — LOW — `prompt_turn.py` `_complete_turn_payload` L634–651 / emit L848; `tui_gateway/contracts/events.py` L164–184 — `message.complete` carries full `text` plus `usage`/`status`, not a bare done signal.
- WINH03-AUD-04 — [PARTIAL] — MEDIUM — `tui_gateway/server.py` `_emit_approval_request` L709–732; `approval_context.py` `_get_approval_timeout` L239–248 — approval blocks the turn thread on the queue (default 300s); JSON-RPC dispatcher can still read `session.interrupt`.
- WINH03-AUD-05 — [RISK] — HIGH — `tui_gateway/server.py` L122–140 (grace default 20s, activity stale default 600s); `session_lifecycle.py` L507–572; `config_defaults.py` L949–955 — Surface 3 default keeps a healthy detached turn running (“an active turn runs to completion”); not an immediate interrupt.
- WINH03-AUD-06 — [PARTIAL] — MEDIUM — `methods_session.py` L337 `close_on_disconnect`; `session_lifecycle.py` L653–654 vs L390 `_interrupt_session_turn`; `ChatSidebar.tsx` L94–99 — no interrupt-on-disconnect RPC; `close_on_disconnect` reaps without calling `_interrupt_session_turn`. Desktop main chats do not set the flag.
- WINH03-AUD-07 — [PARTIAL] / [UNVERIFIED] — MEDIUM — `session.interrupt` → `_interrupt_session_turn` (`methods_session.py` L1995; `session_lifecycle.py` L390–432) — client interrupt-then-close can approximate Surface 1 if the frame is read; unread-frame race `[UNVERIFIED]`.
- WINH03-AUD-08 — [RISK] — HIGH — restates WINH02-AUD-12: Surface 3 default is structurally fail-open; fail-closed requires client `session.interrupt` and/or sidecar env (`HERMES_TUI_WS_ORPHAN_ACTIVITY_STALE_S=0` with grace > 0), not socket-drop alone.
- WINH03-AUD-09 — [PARTIAL] — MEDIUM — `tui_gateway/server.py` `_sessions` L85 vs `hermes_state_sessions.py`; `methods_session.py` `_resume_cold` L762–780; `event_replay.py` L26–28 — process crash loses live runtime and the 512-event ring; `session.resume` reloads durable transcript and builds a new agent.
- WINH03-AUD-10 — [UNVERIFIED] — MEDIUM — Windows `taskkill /F` / Desktop `forceKillProcessTree` vs `state.db` WAL (`hermes_state_wal.py`); `startup_orphan_sweep` (`config_defaults.py` L957–963) — resume-after-hard-kill integrity not settled by static reading.
- WINH03-AUD-11 — [PARTIAL] — LOW — Desktop `powerMonitor.on('resume')` (`apps/desktop/electron/main.ts` L6846–6847); no serve-side OS-sleep handler; loopback WS ping disabled (`config_defaults.py` L945–948) — sleep/wake misfire of the orphan timer is `[UNVERIFIED]`.
- WINH03-AUD-12 — [RISK] — MEDIUM — `tui_gateway/contracts/server_requests.py`; `_ask` L1306; approval 300s / clarify 3600s / sudo 120s — missing handlers time out then skip/deny at defaults; clarify `timeout <= 0` can wait forever.
- WINH03-AUD-13 — [MATCH] — LOW — `apps/desktop/package.json` L95 and `web/package.json` L18 `"@hermes/shared": "file:…"` — consumable outside the Hermes workspace via a relative `file:` dependency; still un-semvered (`WINH02-AUD-02`).
