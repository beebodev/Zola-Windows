# WINH03 Audit 06 — Domain Synthesis (not a path decision)

Pinned tag: `v2026.9.14`
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

This restates WINH02's "Unknown until WINH03" items. No path is recommended. Standing risk `WINH02-AUD-02` (un-semvered JSON-RPC contract) is carried, not re-investigated.

---

## Path A — Fork / re-theme `apps/desktop`

| Unknown from WINH02 | Status | Answer |
|---|---|---|
| End-to-end `prompt.submit` → tools → `message.complete`; UI if sidecar dies mid-tool | **Resolved** (static) / **partially `[UNVERIFIED]`** for UI | Chain in `WINH03-AUD-02`. Sidecar kill: tool-call row may be in `state.db`; live deltas gone; resume is cold (`WINH03-AUD-09`). What Desktop paints after `taskkill` mid-tool: `[UNVERIFIED]`. |
| `state.db` vs `_sessions`; `session.resume` after crash; `session.interrupt` for barge-in | **Resolved** | Resume reloads durable transcript, new runtime (`WINH03-AUD-09`). Interrupt is `request_hard_interrupt` (`WINH03-AUD-07`); syscall-blocked tool return timing `[UNVERIFIED]`. |
| How much of Electron main is load-bearing for local-only Windows | **Partially resolved** | Spawn+loopback WS: `backend-command.ts` + `start_server` (`WINH03-AUD-01`, `WINH02-AUD-09`). SSH/cloud/registry live in the same `electron/main.ts` bundle — deleting them is a compile/split problem, not required at runtime for local sidecar. No new evidence that local spawn *calls* SSH. |

Fail-closed: Path A inherits Surface 3 default (`WINH03-AUD-05` / `AUD-08`) unless the fork sends `session.interrupt` on close and/or sets sidecar orphan env. Desktop does **not** set `close_on_disconnect` on main chats.

`WINH02-AUD-02` still applies to a branded fork.

---

## Path B — Fresh Windows client against JSON-RPC / `apps/shared`

| Unknown from WINH02 | Status | Answer |
|---|---|---|
| Minimum method/event/request subset | **Resolved** | `WINH03-AUD-12`: `approval` (300s then deny if unimplemented), `clarify` (3600s), `sudo` (120s); GUI bridges optional. Events: `message.delta` / `message.complete` / `tool.*`. |
| `apps/shared` outside npm workspace | **Resolved** | `file:` dependency, same as Desktop/web (`WINH03-AUD-13`). Still `0.0.0` (`WINH02-AUD-02`). |
| Reconnect after sleep/wake or killed sidecar | **Resolved for design; wake timing `[UNVERIFIED]`** | Live process: `session.events.since` + 512-event ring (`WINH03-AUD-09`). Dead process: cold `session.resume` from `state.db`, new epoch. Desktop has `powerMonitor` resume; serve has no OS-sleep handler (`WINH03-AUD-11`). |
| Session identity / single authority | **Resolved enough for WINH00** | Live id vs `session_key` (stored). One live turn per session (`running`). Disconnect authority is the **orphan reaper**, not the client, unless the client interrupts first (`WINH03-AUD-05`). |
| Process to launch | **Resolved** | `hermes serve --host 127.0.0.1 --port 0` only (`WINH03-AUD-01`). Does not expose OpenAI `/v1`. |

Fail-closed: same as A — client must not rely on socket drop (`WINH03-AUD-08`).

---

## Path C — OpenAI-compatible HTTP API only

| Unknown from WINH02 | Status | Answer |
|---|---|---|
| Does `hermes serve` expose OpenAI API? | **Resolved: no** | `WINH03-AUD-01`. Path C needs `hermes gateway` + `API_SERVER_ENABLED`. **Cannot share** the Desktop sidecar process with Path B. |
| `/v1/chat/completions` + `/api/sessions` resume vs `session.resume` | **Still unresolved (out of this prompt's Surface 3 trace)** | JSON-RPC resume is cold DB reload (`WINH03-AUD-09`). API-server session/run objects were not traced end-to-end here. Needs a live or code trace of `api_server` `/api/sessions` vs `state.db` if WINH00 considers Path C. |
| Tool progress / approvals on this wire | **Partially resolved by WINH02; not re-traced** | SSE `hermes.tool.progress`; unattended approval mode default **deny** (`approval_context.py` L280–284). No `approval` server→client request on Surface 1. |
| `API_SERVER_KEY` vs dashboard token | **Resolved** | Different processes, different secrets (`WINH03-AUD-01`). Key is env/config; dashboard token is process-ephemeral (`WINH02-AUD-04`). |

Fail-closed: Surface 1 **matches** Zola's lens (`WINH02-AUD-12`, confirmed `WINH03-AUD-05` comparison). Cost: two-process model if Zola also wants Desktop-equivalent JSON-RPC features.

---

## Path D — ACP stdio

| Unknown from WINH02 | Status | Answer |
|---|---|---|
| ACP request trace vs Desktop | **Not traced in WINH03** (prompt scoped Surface 3 + disconnect + serve/gateway) | Still only relevant if WINH00 considers an editor host. `WINH02-AUD-05` stands. `cancel()` exists; stdio death tears down the process (no 600s detached turn). |

---

## Cross-cutting WINH02 list (prompt footer)

1. **Full turn named functions** — resolved: `Zola_WINH03_Audit_02_RequestTrace.md` / `WINH03-AUD-02`.
2. **Mid-turn disconnect / cancel authority** — resolved as **Surface 3 default fail-open**; client interrupt-before-close approximates fail-closed with a delivery race (`WINH03-AUD-05`–`08`). Surface 1 remains fail-closed.
3. **Session resume after process death** — resolved: durable transcript in `state.db`; live `_sessions` lost; `session.events.since` is in-process only (`WINH03-AUD-09`). `taskkill /F` integrity `[UNVERIFIED]` (`WINH03-AUD-10`).
4. **Path B vs C process** — resolved: **cannot share one process** (`WINH03-AUD-01`).
5. **Minimum server→client requests** — resolved: `WINH03-AUD-12`. Missing handlers time out (defaults), they do not hang forever unless clarify timeout is unlimited.

---

## Standing facts carried into WINH00 (not new)

- `WINH02-AUD-02` HIGH — JSON-RPC un-semvered; any Path A/B packaged client.
- `WINH02-AUD-11` — fork vs `apps/shared` cost.
- `WINH01-AUD-05` — Desktop E2E disabled on Windows.

No path is recommended here.
