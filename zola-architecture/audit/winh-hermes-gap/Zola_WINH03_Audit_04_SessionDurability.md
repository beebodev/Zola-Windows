# WINH03 Audit 04 — Session Resume and Durability

Pinned tag: `v2026.9.14`
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Surface 3 only (`_sessions` + `session.resume` / `session.events.since`). SQLite store: `hermes_state_sessions.py` / WAL helper `hermes_state_wal.py`. Related: `WINH01` ConPTY / process-tree-kill; `WINH02-AUD-10` reconnect replay.

---

## 1. What survives a `hermes serve` crash vs what lives only in `_sessions`

**In-process only (`tui_gateway/server.py` `_sessions` L85) — gone on process death:**

- Live UI `session_id` (runtime id, not the stored key)
- `transport` / WebSocket, `viewers`, slash-worker handle
- `running`, `_run_thread`, `_turn_cancel_requested`, inflight delta buffer
- Replay ring (`event_replay.py` `_REPLAY_BUFFER_MAX = 512` L26–28) and `replay_epoch` (process identity)
- Open server→client requests (`server_requests._open`)
- Parked `_detached_ws_transport` + orphan timers
- `close_on_disconnect`, leases until finalized to DB

**Durable (`state.db` via `hermes_state_sessions.py`):**

- Session row: `create_session` L367, `get_session` L737 — source, model, cwd, title, ended_at, message_count, …
- Transcript messages flushed during the turn (`AIAgent._flush_messages_to_session_db`; tool-call persist-before-execute in `turn_tool_round.py` L116–119)
- End reason when `_finalize_session` reaches `db.end_session` (`session_lifecycle.py` L270)

Empty drafts: `session.create` **does not** insert a row until first prompt (`methods_session.py` L356–371), except seeded/branch sessions.

Journal: default WAL (`hermes_state_wal.py` `resolve_journal_mode` L156–162), with filesystem fallbacks to DELETE. Crash recovery depends on SQLite replaying WAL on next open — **normal SQLite behavior**, not a Hermes-specific fsync guarantee for `taskkill /F`.

On **next** `hermes serve` start, `dashboard.startup_orphan_sweep` (`config_defaults.py` L957–963) can `end_session` tui/desktop rows left `ended_at IS NULL` by a dead process (`end_reason='startup_orphan_reap'`). Comment: the in-process grace timer dies with the process, so without this sweep rows stay phantom-active. Swept rows "stay resumable."

---

## 2. What `session.resume` restores after a restart

`methods_session.py` `@method("session.resume")` L837.

After a process restart there is **no live `_sessions` entry** for that stored id, so the fast path `_resume_reuse_live` (L676 — reattach existing runtime, cancel orphan reap) does **not** apply.

Default path `_resume_cold` L762–780:

- Loads transcript from DB (`ctx.restore()`) — **full stored conversation** (plus display projection), not a 512-event ring
- Builds a new in-memory record; **schedules** `AIAgent` build (`_schedule_agent_build`) — agent is **not** on the RPC response path (can take seconds)
- Returns messages + `info` + optional `auto_continue`
- Replay ring is empty (new process / new `replay_epoch`). `session.events.since` cannot replay the crashed turn's deltas; the client must use resume `messages` (and REST hydration if `defer_history`)

Other resume modes: `_resume_deferred` (ack first, hydrate in background), `_resume_lazy` (subagent watch, no agent), `_resume_eager` (synchronous agent build).

**Resume is not "replay recent events."** It is **reload durable transcript + new runtime**. Live-turn replay (`session.events.since`) only works against a **still-living** `hermes serve` process (Desktop reconnect / `JsonRpcGatewayClient` replay — `WINH02-AUD-10`).

Inflight failed-turn snapshot is retained on the **live** session for resume replay (`prompt_turn.py` L666–668). After process death that snapshot is gone unless it was flushed to DB.

---

## 3. Windows `taskkill` / process-tree-kill vs graceful stop

Desktop graceful stop: `stopBackendChildImpl` + Windows `forceKillProcessTree` (`WINH02-AUD-09`, `main.ts` L1418–1421). That is **tree kill**, not `hermes serve --stop`.

`hermes serve --stop` scans and SIGTERMs dashboard/serve processes (`dashboard.py` L39–45). On Windows, `gateway/run.py` L5257–5266 documents that asyncio signal handlers are `NotImplementedError`; gateway uses a planned-stop marker thread. **That comment is on `hermes gateway`, not `hermes serve`.** Serve is uvicorn/FastAPI; whether SIGTERM runs `_finalize_session` for every `_sessions` entry is a different stack.

`taskkill /F` (or Desktop force tree-kill of a stuck child): no Python `finally`, no `_finalize_session`, WAL may hold uncheckpointed frames. SQLite typically recovers WAL on next open; a torn write is possible. `startup_orphan_sweep` then ends phantom rows.

**Interaction with WINH01 ConPTY:** PTY Chat (`/api/pty`) is a child `hermes --tui`. Tree-kill of serve should kill PTY children if they are in the job/tree. JSON-RPC `/api/ws` turns are **threads inside serve**, not ConPTY processes. ConPTY (`WINH01-AUD-03`) does not change `state.db` flush for `/api/ws` turns.

**`[UNVERIFIED]`:** whether a Windows `taskkill /F` of the serve tree leaves `state.db` in a state `session.resume` always accepts vs SQLITE_CORRUPT / incomplete last message. A real test would: start `hermes serve`, `prompt.submit` a long `terminal` tool, `taskkill /F` the PID mid-tool, restart serve, `session.resume` the stored id, inspect last DB message vs expected.

---

## 4. Windows sleep / wake

**Server (`hermes serve`):** no `SetThreadExecutionState` / sleep notification handler was found in `tui_gateway/` or `hermes_cli/web_server.py`. A sleeping host freezes wall clocks and TCP. Possible misfires `[UNVERIFIED]` without running:

- WS ping: `dashboard.ws_ping_interval` / `ws_ping_timeout` default 20s **disabled on loopback** (`config_defaults.py` L945–948: "loopback always disables the protocol ping"). Desktop sidecar is `127.0.0.1` → pings off. Remote/non-loopback binds could drop on sleep.
- Orphan reaper uses `threading.Timer` + `time.perf_counter_ns` for compute-host freshness and `get_activity_summary` seconds — after wake, a stalled turn may look stale (600s) and get interrupted, or a Timer may fire in a burst. **Not tested in this tag as an OS-sleep suite.**

**Desktop client:** **does** handle sleep/wake. `apps/desktop/electron/main.ts` L22, L6846–6847: `powerMonitor.on('resume' | 'unlock-screen')`. Renderer reconnect / wake sweep: `store/gateway.ts` comments L23, L1711; tests `gateway-connection-lifecycle.test.ts` (force-redial after wake); `electron/remote-liveness.ts` L407–408. Transcript tail cache comments describe post-wake paint (`transcript-tail-cache.ts` L10–26).

So: **client** has a sleep/wake path; **sidecar process** does not have a dedicated sleep handler. Loopback JSON-RPC is less exposed to WS ping-on-sleep than a remote dashboard.

**Finding:** `WINH03-AUD-09` (durable vs live), `WINH03-AUD-10` (taskkill `[UNVERIFIED]`), `WINH03-AUD-11` (sleep/wake).
