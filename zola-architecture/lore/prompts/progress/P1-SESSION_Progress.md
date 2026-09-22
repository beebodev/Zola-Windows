# P1-SESSION Progress — Track 3: Session Wrap

## Branch

- Branch: `track3-session-wrap`
- Base SHA: `b42ff44a0ddc29c5b9c1d53d6791ce0a0620638f`
- Feature commit SHA: `96c8c2b10e3cca7425a27678c13050feacdb1803`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Session List and Resume | COMPLETE |
| 4 | Smoke Test | COMPLETE |
| 5 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Wrap Hermes's existing session HTTP API from the Windows client. In scope: list and resume via `GET /api/sessions` and `GET /api/sessions/{id}`, create a session by opening `/api/ws` with the id contract confirmed in Phase 2, a toggleable session list showing id and last-activity time, and resume across a client restart with prior turns replayed. Out of scope: Hermes-side session files, `apps/desktop/`, and Tracks 4–6.
- **G-ARCH:** Build plan is truth. Stop and flag conflicts; do not silently deviate.
- **G-PATTERN:** Read every relevant file in full before any change. No changes from partial reads or memory.
- **G-NOCHANGE:** Edits limited to the files and lines described in the current task.
- **G-COMMENT:** Every changed line or block carries `// P1-SESSION: [rationale] — P1-D04`. Do not comment unchanged lines.
- **G-STOP:** Stop after each phase and wait for that phase's explicit proceed message.
- **G-CLOSEOUT:** Closeout begins only on the explicit message "proceed to closeout".
- **G-LORE-SCOPE:** Do not add, resolve, or update `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, or any project state-audit document in this track, including closeout.

## Discrepancies

The prompt named base SHA `83405c34ea96a598e6bb6a32bd3d9137d078cee2` (Track 2's merge commit). `main` HEAD was `b42ff44a0ddc29c5b9c1d53d6791ce0a0620638f` (`docs: record P1-IDENTITY merge SHA on main`, one commit after that merge). Developer chose Option A: branch from current `main` and record `b42ff44a0ddc29c5b9c1d53d6791ce0a0620638f` as the base SHA.

Phase 2 handshake (not a blocker; this is the contract Phase 3 builds against):

1. A new session id is server-assigned. `/api/ws` takes `?token=` and no session id (`chat_ws.py` `gateway_ws` forwards to `tui_gateway.ws.handle_ws`). `session.create` with empty params (`tui_gateway/methods_session.py`) mints a runtime `session_id` (`uuid.uuid4().hex[:8]`) and a durable `stored_session_id` (`YYYYMMDD_HHMMSS_<6 hex>` from `new_session_id()`). The client does not generate either id. Track 1's `ChatSocket.StartAsync` already calls `session.create` once and stores both ids; `prompt.submit` and `session.interrupt` send the runtime `session_id`.
2. Opening the socket and `session.create` do not write a `sessions` row. `_ensure_session_db_row` inserts `stored_session_id` as the row `id` on the first `prompt.submit` (seeded history is the exception). `GET /api/sessions` therefore will not list a session until that first prompt. There is no create route on the dashboard router.
3. `GET /api/sessions` returns `{sessions, total, limit, offset}`. Default `limit=20`, `order=created` (by `started_at`), archived and hidden excluded. Each row includes `id` (the stored id) and computed `last_active` (unix seconds: freshest of `last_activity_at` and the latest message timestamp, else `started_at`), plus `title`, `preview`, `started_at`, `message_count`, `source`, `is_active`, `profile`. `system_prompt` and `model_config` are stripped unless `full=1`. `order=recent` sorts by chain last activity.
4. `GET /api/sessions/{id}` returns the `SessionDB.get_session` row (`sessions` columns, including `started_at` and `last_activity_at`) plus `profile`. It does not include messages or the computed `last_active` field. Prior turns are `GET /api/sessions/{id}/messages` (`role`, `content`, `timestamp`; default latest page of 500, returned oldest-first). `resolve_resume_session_id` follows a compression chain to the tip.
5. Resume is `session.resume` with `session_id` set to the stored id. The result's `session_id` is a new runtime id; later `prompt.submit` uses that runtime id. Routes are backed by `SessionDB` via `_open_session_db_for_profile`, not `gateway/session.py` `SessionStore`.
6. `GET /api/sessions` and `GET /api/sessions/{id}` are not public. Loopback auth accepts `X-Hermes-Session-Token` or `Authorization: Bearer` with the same dashboard token Track 1 already holds. `?token=` is not accepted on these GETs.

Phase 3: the session list is a collapsed panel beside the chat, opened with the Sessions button and closed with that button or Close. New session opens a fresh `/api/ws` and calls `session.create`; the stored id is shown immediately. Resume loads `GET /api/sessions/{id}/messages`, then `session.resume` with that stored id, paints the turns, and closes the panel before input is enabled. `dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded. No automated tests exist for this project. No Hermes-side files were changed.

Phase 4: developer reported "smoke test passed" (session listed with a last-activity time, prior turns visible before a new message, and a follow-up consistent with the earlier context).

## Closeout

- `dotnet build windows-client/Zola.Client/Zola.Client.csproj` passed.
- Existing tests: N/A. This project has no automated test suite.
- No lore files were updated.
- Feature commit SHA: `96c8c2b10e3cca7425a27678c13050feacdb1803`
- Merge commit SHA on `main`: recorded after the merge.

## Files

### Created this track

- `zola-architecture/lore/prompts/progress/P1-SESSION_Progress.md` (Phase 1)
- `windows-client/Zola.Client/SessionCatalog.cs` (Phase 3)

### Modified this track

- `zola-architecture/lore/prompts/progress/P1-SESSION_Progress.md` (Phase 2 handshake, Phase 3 status, closeout)
- `windows-client/Zola.Client/ChatSocket.cs` (Phase 3)
- `windows-client/Zola.Client/MainWindow.xaml` (Phase 3)
- `windows-client/Zola.Client/MainWindow.xaml.cs` (Phase 3)
