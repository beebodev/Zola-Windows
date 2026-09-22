# P1-CLIENT Progress — Track 1: Client/Process Scaffold

## Branch

- Branch: `track1-client-scaffold`
- Base SHA: `8bc3a3ca46f32f66a58558a7d271faabf609284c`
- Feature commit SHA: `b204830261c29f2a45ef2d327df2e00702daca9f`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Project Scaffold and Process Lifecycle | COMPLETE |
| 4 | Build: Chat UI and /api/ws Streaming | COMPLETE |
| 5 | Smoke Test | COMPLETE |
| 6 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** New WinUI 3 client in `windows-client/Zola.Client/` only: process lifecycle for `hermes serve` under a dedicated Zola profile, health-check, clean shutdown, and `/api/ws` chat streaming with cancel. `hermes-agent` is read-only. Tracks 2–6 are out of scope.
- **G-ARCH:** Build plan is truth. Stop and flag conflicts; do not silently deviate.
- **G-PATTERN:** Read every relevant file in full before any change. No changes from partial reads or memory.
- **G-NOCHANGE:** Edits limited to `windows-client/Zola.Client/` and this progress document. No `hermes-agent` changes. No other `zola-windows` files.
- **G-COMMENT:** Every changed line or block commented `// P1-CLIENT: [one-line rationale] — P1-D01`. Do not comment unchanged lines.
- **G-STOP:** Stop after each phase and wait for that phase's explicit proceed message.
- **G-CLOSEOUT:** Closeout begins only on the explicit message "proceed to closeout".
- **G-LORE-SCOPE:** Do not add, resolve, or update `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, or any project state-audit document in this track, including closeout.

## Discrepancies

None at start. Documents of truth read before Phase 1: `PHASE1_BUILD_PLAN.md` (Track 1, `P1-D01`, `P1-D02`), `Zola Master Architecture Plan.md` Section 19, `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`. HEAD on `main` matched `8bc3a3ca46f32f66a58558a7d271faabf609284c` before the branch was created. Working tree was clean.

Phase 2 clarifications (not blockers — existing Hermes mechanisms, to be used as-is in later phases):

1. Opening `/api/ws` does not mint a session. The client sends JSON-RPC `session.create` on that socket; the server returns `session_id` (runtime) and `stored_session_id`. The DB row is created on the first `prompt.submit`, not at connect time. This corrects the Build Plan's "implicit on socket open / no session id" wording. There is still no REST create endpoint.
2. A named profile is not isolated unless `--isolated` is passed. Without it, `hermes serve -p <name>` re-execs onto the machine-level default server (`-p default`) and only preselects the profile. `HERMES_HOME` is trusted against the sticky `active_profile` file only when the path's parent directory is named `profiles`.
3. Loopback `/api/ws` still requires `?token=`. Hermes does not print that token on the `HERMES_BACKEND_READY` line and does not write it into the profile directory. The spawning parent mints it and passes `HERMES_DASHBOARD_SESSION_TOKEN` in the child environment (`hermes_cli/web_server.py` `_resolve_session_token`). Headless `GET /` then echoes it as `window.__HERMES_SESSION_TOKEN__` when the auth gate is off. `GET /api/health` is the unauthenticated readiness probe.

Phase 3 verification (local run, not the Phase 5 smoke test):

- Launch is `python -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0` with `HERMES_HOME` set to `%LOCALAPPDATA%\hermes\profiles\zola`. Port 0 is used because 9119 was already held by a different `hermes serve` (no `--isolated`, not the zola profile). The ready sentinel supplied the bound port.
- `SOUL.md`, `sessions\`, and `state.db` were created under that profile directory. The client did not write identity text.
- `GET /api/health` returned `{"ok":true,"auth_required":false}` before the WebSocket gate opened. `/api/ws` was not connected.
- The listen socket was `127.0.0.1` only. A connect to the machine's LAN address on that port failed.
- Closing the window that spawned the process tree-killed it. A second window that attached left the process running. The pre-existing serve on 9119 was not killed.

Phase 4 local check (not the Phase 5 smoke test):

- After `GET /api/health`, the window opened `ws://127.0.0.1:<port>/api/ws?token=…`, sent `session.create` once, and showed `session <id> · stored <id>` before the composer enabled.
- `prompt.submit` left the status on "Responding…" and did not paint that acknowledgement as the assistant reply. With no inference provider configured, the turn ended in `message.complete` status `error`: an Error badge, the provider message in the bubble, and the composer usable again. `error` events stayed on the detail line.
- Killing the isolated serve made the window show "Backend unreachable." and disable input. Closing the owner window tree-killed the serve. The pre-existing serve on 9119 was not killed.
- After OpenAI/ChatGPT login was configured for this profile (`gpt-5.6-terra`), the same window was checked again. While status was still "Responding…", the assistant text grew (4, then 76, then 107, then 131 characters) and then the turn ended at "Session ready." with no Error badge. The text was the requested word list. A second `prompt.submit` on the same session (`history=2`, same stored session) replied `marigold`. Cancel during a later in-flight reply (text already growing) settled to "Interrupted." with one badge; the partial text stayed at 72 characters for the next 12 seconds. The server recorded that turn as `status=interrupted`.

Phase 5: developer reported "smoke test passed" (connected Zola profile, live "hello" stream, follow-up context, mid-stream cancel, unreachable state, no orphan serve, localhost-only bind).

## Closeout

- `dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings before the feature commit.
- No automated test suite for this project.
- Feature commit SHA: `b204830261c29f2a45ef2d327df2e00702daca9f`
- Merge commit SHA on `main`: recorded after the merge.

## Files

### Created this track

- `zola-architecture/lore/prompts/progress/P1-CLIENT_Progress.md` (Phase 1)
- `windows-client/Zola.Client/Zola.Client.csproj`
- `windows-client/Zola.Client/app.manifest`
- `windows-client/Zola.Client/App.xaml`
- `windows-client/Zola.Client/App.xaml.cs`
- `windows-client/Zola.Client/MainWindow.xaml`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `windows-client/Zola.Client/HermesLaunchResolver.cs`
- `windows-client/Zola.Client/HermesProcessManager.cs`
- `windows-client/Zola.Client/DashboardSessionToken.cs`
- `windows-client/Zola.Client/ChatSocket.cs`
- `windows-client/Zola.Client/.gitignore`

### Modified this track

- `zola-architecture/lore/prompts/progress/P1-CLIENT_Progress.md` (Phase 2 through closeout)
- `windows-client/Zola.Client/HermesProcessManager.cs` (Phase 4 health probe for the open socket)
- `windows-client/Zola.Client/MainWindow.xaml` (Phase 4 chat surface)
- `windows-client/Zola.Client/MainWindow.xaml.cs` (Phase 4 turn UI)
