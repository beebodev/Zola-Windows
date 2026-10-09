# Zola P9PRE Audit 08 — Harness Probes

**Date:** 2026-10-09  
**Scratch:** `C:\Users\test\Dev\zola-spikes\p9pre\`  
**Interpreter:** `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`  
**Live profile:** not used. `HERMES_HOME` was a scratch directory on every run. No `hermes serve`, gateway, cron ticker, or client. No model call. No network from the stubs.

Pre-synthesis re-hash (same files as Phase 1, token store excluded): `config.yaml`, `SOUL.md`, `MEMORY.md`, `USER.md`, and every file under `plugins/` matched the Phase 1 hashes. `.env` still missing. Not BLOCKED.

Token store: `token.dpapi` size 926, mtime `2026-10-07T22:58:24.2521851Z`. Unchanged from Phase 1. Contents not read.

---

## H-1 / H-2 — Load count and a daemon thread

**Command:** `python C:\Users\test\Dev\zola-spikes\p9pre\run_h1.py`  
**HERMES_HOME:** `C:\Users\test\Dev\zola-spikes\p9pre\h1`  
**Config:** `plugins.enabled: [p9stub]` only.  
**Stub:** `register` appends pid, thread, time, and a short stack. With `P9_STUB_THREAD=1` it takes `msvcrt.LK_NBLCK` on `stub.lock` and starts a daemon that writes three heartbeats.

First process (pid 7348), 2026-10-09, log timestamps `t=1791575420.148` and `t=1791575420.378`:

- `discover_plugins()` once: one `register`, one heartbeat thread (`beat i=0`, `i=1`).
- `discover_plugins()` again with no force: no second `register`.
- `discover_plugins(force=True)`: `register` ran again and a second heartbeat started (`beat i=0`). The log has no `lock-busy` line. The in-process `msvcrt` lock did not stop the forced reload.

Stack frames on every line: `run_h1.py` → `hermes_cli/plugins.py` → `hermes_cli/plugins_loader.py` → stub `__init__.py`.

**Two processes:** `python run_h2_two.py` (clears the log, starts two `run_h1.py`). Exit codes 0, 0. Pids 2964 and 33592 both logged `register` at `t=1791575462.147`, and both logged heartbeats. Forced reload registered both again at `t=1791575462.425` and `t=1791575462.427`. No `lock-busy` line. Two processes each ran `register`. The stub lock did not collapse them to one watcher.

**Not run offline, and why:** the cron ticker starts only inside serve when `HERMES_DESKTOP=1` (audit 02). Background review is an in-process agent fork, not a second loader. Neither was started. Subagent toolset resolution was not called; it needs a session.

---

## H-3 — Accessor shape

**Command:** `python C:\Users\test\Dev\zola-spikes\p9pre\run_h3.py`  
**HERMES_HOME:** `C:\Users\test\Dev\zola-spikes\p9pre\h3` (import only).

`PluginLlm.complete` signature has no `tools` parameter. `complete_structured` adds `instructions`, `input`, `json_schema`, `json_mode`, `schema_name`. `_host_kwargs` source does not contain the identifier `tools` (`HOST_KWARGS_HAS_TOOLS False`).

A fake transport was not injected. `call_llm` is not a constructor argument of `PluginLlm`. Phase 6 Q2 stays on the code reading in audit 05: `_host_kwargs` omits `tools`, and `call_llm`'s default is `None`.

---

## H-4 — Second writer

**Commands:**

- `python run_h4.py` — `store.open_store` on `C:\Users\test\Dev\zola-spikes\p9pre\h4` (empty scratch, not the live store).
- Two threads, each a new connection, `timeout=0.2`, 20 inserts.
- Two processes `run_h4_child.py` pA and pB, 30 inserts each, `timeout=0.2`.
- Then `run_h4_hold.py` (`BEGIN IMMEDIATE`, sleep 2s) overlapping `run_h4_child.py pC`.

**Results:**

- `journal_mode` = `wal`.
- `busy_timeout` on the `open_store` connection = `5000` (Python's `sqlite3.connect` default timeout is 5 seconds; `open_store` does not pass `timeout`).
- `store.py` `_checkpoint_truncate_or_defer` sets `PRAGMA busy_timeout=50` only around `wal_checkpoint(TRUNCATE)` (L416).
- Thread errors: none. Rows after threads: 40.
- pA `ok 30 locked 0`. pB `ok 30 locked 0`.
- While the hold transaction was open: `pC first_error database is locked`, then `ok 25 locked 5`.

Short concurrent commits on WAL did not error. A writer that holds `BEGIN IMMEDIATE` makes the other connection raise `database is locked` when its timeout (0.2s) expires.

---

## H-5 — Clock jump

**Command:** `python run_h5.py`

Rule: flag when wall delta minus monotonic delta is greater than 2 seconds.

Three real 50ms sleeps: `real [None, None, None]`.  
Simulated inputs (wall +30s, monotonic +0.05s): `simulated jump wall_delta=30.000 mono_delta=0.050`.

No machine sleep was performed.
