# S51M-FIX — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\S51M-FIX_Prompt_v1.1.md`  
**Prompt SHA-256 (verified):** `b1176e93d868201b415535e9236564f0ab6586b46247f180a6953b6a3c076940`  
**Started:** 2026-11-13  
**SOP:** v3.0 · PROC1-STABLE/ID/DEV/GATE merged

---

## Repositories

| Repo | Branch | HEAD | Notes |
|------|--------|------|-------|
| `zola-windows` (live) | `main` | `a68cb846f315d5469f7a06ca538161c2be1b89e1` | clean; = `origin/main` |
| `zola-windows-s51m-fix` | `s51m-fix` | `a68cb846f315d5469f7a06ca538161c2be1b89e1` | worktree from `origin/main` |
| `hermes-agent` | detached pin | `345cd2b057a452236de401d3534b8502a7465e8d` | clean, read-only |

**Tag `proc1-gate`:** annotated tag object; tagged commit `ceb0476f31c5a12b82bcdcbc26fb7bb2d8f6744f` (matches prompt `ceb0476…`).  
**Stable:** `Zola.Client` running from `C:\Users\test\Zola\stable\proc1-dev\` (pid observed at Phase 1 start).

**Discrepancies:** none at setup.

---

## Guardrails (summary)

G-SCOPE · G-PRIVACY · G-NO-LIVE · G-REPRO · G-NO-RESTART · G-GATE · G-STOP · G-MERGE

---

## Phase status

| Phase | Status |
|-------|--------|
| 1 Confirm the cause | **approved** (Claude + developer) |
| 2 Fix design | **approved** — Brian D1=(A); Claude approved |
| 3 Implement | approved (core fix right; Phase 4 review fixes) |
| 4 Review fixes | **STOP** — closed-by-state, coalesce, tests, base-fail proof, regenerated diff |
| 5 Dev smoke / gate | not started |
| 6 Commit and merge | not started |
| 7 Promotion | not started |

---

## Phase 1

### 1. Setup (EVIDENCE)

- Prompt SHA verified: `b1176e93…076940`.
- Live checkout: `main` @ `a68cb84…`, `git status` clean, `main` = `origin/main`.
- `hermes-agent` clean at pin `345cd2b0…`.
- Worktree created: `C:\Users\test\Dev\zola-windows-s51m-fix` branch `s51m-fix`.
- Stable running from `stable\proc1-dev\` (confirmed via process path).

### 2. Hermes shutdown path (SOURCE)

*Refined with [Hermes shutdown SOURCE](f7a4f617-29e9-42e5-bb22-8d877bd8b7b3).*

**TUI reaper / WS-orphan / serve-exit teardown (the crash path)**

```
[reaper / Timer / atexit thread T]
  _teardown_popped_session
    optional join turn thread ≤ 5s
  _teardown_session → _finalize_session
    plugin invoke_hook("on_session_end")   # NOT MemoryProvider
    agent.commit_memory_session(history)   # → MemoryProvider.on_session_end  [1st]
    db.end_session / slash_worker.close / …
    agent.close()
      shutdown_memory_provider             # _memory_provider_shutdown not set by commit
        MemoryManager.on_session_end       # → MemoryProvider.on_session_end  [2nd]
        shutdown_all → drain ≤5s → p.shutdown()
```

That **double** `MemoryProvider.on_session_end` on one teardown explains the paired log lines (e.g. Nov-12 `message_count=67` then `message_count=0`): first from `commit_memory_session` with history, second from `shutdown_memory_provider` with empty/default messages — **SOURCE**, not two agents.

**Close sequence on the provider**

1. `ZolaMemoryProvider.shutdown`: under **`self._lock` only** → `forget.clear_hold_meta` (**outside** `store.locked`) → `store.release_lock(conn)` → **`conn.close()`** → `_conn = None` (`provider.py` ~346–360).
2. Does **not** take `store.locked(conn)` before close.

**Other `on_session_end` callers**

| Caller | Thread | Then shutdown? |
|--------|--------|----------------|
| TUI `_finalize_session` → `commit_memory_session` | reaper / Timer / atexit | later yes, via `close` (2nd end + shutdown) |
| `shutdown_memory_provider` | same / CLI / gateway exit | **yes** (`shutdown_all`) |
| Soft agent-cache eviction | daemon `agent-cache-idle-*` / pressure | **no** — `commit` + `release_clients` only |
| `commit_session_boundary_async` (`/new`) | mem-sync worker: end→switch | **no** |
| Gateway `_cleanup_agent_resources` | worker / off-loop | **yes** (after `flush_pending` ≤10s) |
| CLI / oneshot exit | atexit | **yes** (after `flush_pending` ≤10s) |

**Waits:** CLI/gateway exit flush mem-sync ≤10s then drain ≤5s before `p.shutdown`. **TUI reaper path has no memory barrier** between 1st `on_session_end` (commit) and `close`/`shutdown` — only non-memory finalize work. Soft-evict never closes the store.

**Reaper timing (SOURCE)**

| Mechanism | Interval / idle rule |
|-----------|----------------------|
| TUI idle reaper | scan every **`_REAPER_SCAN_S = 300`s**; idle if transport dead, not running/pending/delegating, and last_active **and** created_at both older than **`_SESSION_TTL_S` default 6h** |
| WS-orphan reap | grace default **20s**; Timer → `_reap` → teardown |
| Gateway agent-cache idle | every **300s** (after 60s); idle TTL default **3600s**; soft only |

**Providers / connections per serve process (SOURCE)**

- At most **one external** provider per `AIAgent` / `MemoryManager` (`memory_manager.py`).
- Created at agent init when `memory.provider` is set (`agent_init.py`).
- One agent per live TUI session ⇒ **≈ one provider (one SQLite connection) per live session** with memory enabled; multiple live sessions ⇒ multiple connections to the same profile DB file (cross-process lease via meta).

### 3. Every use of `provider._conn` (SOURCE)

*Refined with [zola_memory conn SOURCE](fb7433c2-230e-4463-9ada-106043bc1bdc). Full call-site table lives there; summary below.*

**Locking primitives**

- `store.locked(conn)`: RLock keyed by `id(conn)`; **creates a new lock if entry missing** (`store.py` ~129–138).
- `store.release_lock(conn)`: pops lock entry (`store.py` ~141–144).
- `shutdown` calls `release_lock` then `close` under `self._lock` only — consolidator later `store.locked(conn)` can get a **fresh empty lock** on a closed connection → race.
- **Consolidate never takes `provider._lock`.**

**Module state in `consolidate.py` (SOURCE)**

| Symbol | Role |
|--------|------|
| `_running` / `_coalesce` | process-global single-flight; coalesce = **trigger string only**, not a provider |
| `_instance_id` | lease owner UUID (process-lifetime; reset in tests) |
| `_attempt_counts` | fingerprint → attempts (single-runner assumption) |
| Quiet timer | **once per process**; closure captures **first** provider forever. After that `_conn is None`, loop `continue`s — **never serves provider B**. B’s `start_quiet_timer` is a no-op. |
| A in flight + B requests | `_coalesce` overwritten; runner still calls `run_consolidation(A, …)`. After A shutdown, work runs against dead A. Shutdown does **not** stop timer / join runner / clear `_running`. |

**Lease (SOURCE)**

- TTL `CONSOLIDATE_LEASE_TTL_S = 60`; acquire/renew/release under `store.locked` + `BEGIN IMMEDIATE`.
- Process death / AV mid-hold: lease left until expiry; next process `busy` until then. Same `_instance_id` can re-enter. Pending rows survive unless `_commit` succeeded.

**LLM vs locks:** `_build_model_input`, `validate_episodes`, and `llm.complete_structured` run **outside** `store.locked` (lease still held in meta). `_commit` is locked.

**Connection-use table (shutdown-sensitive + unlocked reads)**

| Site | Thread | Locks | After shutdown started? | Inside `store.locked`? |
|------|--------|-------|-------------------------|------------------------|
| `provider.shutdown` close | reaper / teardown | `self._lock` only | is shutdown | **no** |
| `forget.clear_hold_meta` in shutdown | same | `self._lock` | yes | **NO** |
| quiet timer `count_pending` | `zola-consolidate-timer` | `store.locked` | yes (stale first provider) | yes when conn non-null |
| lease acquire/renew/release | `zola-consolidate` | `store.locked` | **yes** (local conn ref) | yes |
| sanitize + list pending | `zola-consolidate` | `store.locked` | **yes** | yes |
| **`_build_model_input`** | `zola-consolidate` | **none** | **yes** | **NO** |
| **`validate_episodes`** | `zola-consolidate` | **none** | **yes** | **NO** |
| LLM call | `zola-consolidate` | none | yes | n/a |
| `_commit` + ROLLBACK/finally | `zola-consolidate` | `store.locked` | **yes** | yes |
| `prefetch` / retrieve | caller | `self._lock` + `store.locked` | raced if null-check loses | yes |
| `sync_turn` / turn sanitize / file_check | turn | `self._lock` + locked where noted | if conn set | mostly yes |
| forget `search_candidates` / `entities_matching` / `_facts_naming` | tool handler | `provider._lock` only | if conn set | **NO** (large scans) |
| `load_hold_meta_safe` / initial proactive `meta_get` | hooks / tool | often none / provider lock | if conn set | **NO** |
| `time_context` last-interaction | pre_llm | `store.locked` (no provider lock) | if still registered | yes |

### 4. Log sequence at the two Nov-12 crashes (MEASURED, fields only)

**Crash A — ~10:36:04 `python312.dll+0x3b1ff`**

```
10:36:03.915 on_session_end message_count=110
10:36:03.917 lease acquired
10:36:03.918 lease released
10:36:03.919 on_session_end message_count=110
10:36:03.920 lease acquired
—— no consolidate end, no shutdown log ——
10:36:25 store_open pid=25000   (restart)
```

Pattern: session_end → consolidate start (lease) → crash before end. **FIT.**  
Paired `on_session_end` lines match TUI finalize `commit_memory_session` then `close`→`shutdown_memory_provider` (**SOURCE** §2).

**Crash B — ~10:47:32 `sqlite3.dll+0xc9310`**

```
10:47:32.445 on_session_end message_count=67
10:47:32.450 lease acquired
10:47:32.451 on_session_end message_count=0
—— no lease release / consolidate end / shutdown ——
10:47:51 store_open pid=24216
```

Same minute earlier (survived race): `10:47:06` and `10:47:15` show session_end → lease → shutdown → consolidate `ok=false` turns=0. **Crash B FIT** for the 10:47:32 subsequence. Second `on_session_end` with `message_count=0` = shutdown path’s second fire (**SOURCE**).

**Historical `0x3b1ff` (10) + sqlite (3) from S51 audit + Nov-12 (2)** — minute-window field scan vs `zola_memory.log`:

| Class | Fit race (end+lease, no cons end) | Partial | No fit | No data |
|-------|-----------------------------------|---------|--------|---------|
| `0x3b1ff` (10 listed) | 6 | 3 | 1 | 0 |
| sqlite (3 listed) | 0 | 2 | 1 | 0 |
| Nov-12 (2) | 1 (+1 partial same-minute noise) | 1 | 0 | 0 |

Faulthandler findings file (`claude/S51_FAULTHANDLER_FINDINGS_2026-11-13.md`) not found on disk this session; prompt quotation used for stack attribution. **MEASURED** stacks from Phase 1 repro match the same sites (`try_pending_sanitize`/`meta_get`, `_release_lease`, `_acquire_lease`/`meta_set`, `_commit`/`sanitize_after_erase`).

### 5. When the race does not crash (MEASURED, counts only; since ~2026-10-30)

| Outcome | Count |
|---------|------:|
| `consolidate … ok=true` (all triggers) | 78 |
| `consolidate … ok=false` | 45 |
| `on_session_end` | 57 |
| `shutdown` | 29 |
| `shutdown` while lease held | **44** |
| `session_end` ok=true | **1** |
| `session_end` ok=false | 21 (mostly `turns=0 attempt=0`) |
| `initialize` ok=true / false | 38 / 3 |
| `quiet` ok=true | 40 |
| `ProgrammingError` / closed-database strings in memory log | **0** (exceptions likely swallowed) |
| `consolidate.giveup` (Oct–Nov lines) | 1541 (lifetime-ish; not all from this race) |

**INFERENCE for D1:** pending work often finishes later via **`initialize`** (new agent/provider) or **`quiet`**, not via the dying session’s `session_end` run. Quiet-timer pin to first provider means **after first provider death, quiet may never drive a later provider** until process restart — “finish later” is not always true in-process.

**Item 7:** live copy showed **`pending_turns = 0`** and lease clear — no stranded pending at this snapshot. Does not prove every historical race recovered; only that nothing is pending now.

### 6. Reproduce (MEASURED, scratch only)

- Script: `%TEMP%\s51m-fix-phase1\repro_shutdown_race.py` (subprocess per iter, `PYTHONFAULTHANDLER=1`, fake LLM, scratch `HERMES_HOME`).
- **Result ~2 min:** `n=69`, **`av=9`**, `clean=60`, `worker_exc=0`, `shutdown_exc=0`, exit parent 0.
- AV exit `0xC0000005`. Stacks: consolidator in SQLite (`meta_get`/`meta_set`/`_release_lease`/`try_pending_sanitize`/`sanitize_after_erase`) concurrent with `provider.shutdown` → `conn.close()`.
- **Cause confirmed and reproduced.**

### 7. Live database health (MEASURED, copy only; G-PRIVACY)

| Field | Value |
|-------|-------|
| Close confirmed | **2026-11-13 16:41:14** (`Zola.Client` absent) |
| Source | `%LOCALAPPDATA%\hermes\profiles\zola\zola_memory\` (`zola_memory.db` + `-wal` + `-shm`) |
| Scratch | `%TEMP%\s51m-fix-db-20261113-164114` (deleted after) |
| `PRAGMA integrity_check` | **ok** |
| `PRAGMA quick_check` | **ok** |
| `pending_turns` | **0** |
| Lease owner set | **no** (empty) |
| Lease expires_at | empty |
| `sanitize_pending` | `0` |

**Row counts (tables):** entities 24; entity_aliases 2; episodes 54; episode_entities 46; episode_fact_refs 24; facts 20; fact_history 5; pending_turns 0; tombstones 44; meta 9; plus FTS shadow tables (entities_fts 26, episodes_fts 54, facts_fts 20, and their `_content`/`_data`/`_docsize`/`_idx`/`_config` siblings as listed in the probe).

No row content printed. Scratch removed: **confirmed absent**.

**Start time:** **2026-11-13 17:25:01** — `Zola.Client` pid 12432 from `stable\proc1-dev\` (Brian started; agent confirmed).

### 8. Timing (MEASURED, scratch)

Locked-section samples (n=1..50 pending):

| Block | Worst observed |
|-------|----------------|
| `list_pending` | ~0.3 ms |
| `try_pending_sanitize` | ~0.06 ms |
| lease acquire+release | **~3.3 ms** |
| `_build_model_input` (today unlocked) | ~0.2 ms on scratch |
| `run_consolidation` empty-episode path | ~18 ms |

**INFERENCE:** under the Phase-2 ordering rule, shutdown waits only while another thread holds `store.locked(conn)`. Worst locked section in production is **`_commit`’s transaction** (not fully timed with a successful large commit this pass; empty path and lease cycle are milliseconds). LLM time is outside the lock today and must stay outside after the fix.

---

## STOP — Phase 1

Items **1–8** complete. Cause **confirmed** (SOURCE) and **reproduced** (9 AV / 69 runs). Progress doc ready for Claude review.

Close **16:41:14** / start **17:25:01** recorded. Await Claude review before Phase 2.

---

## Phase 2 — Fix design (STOP; Brian decides D1)

*Additions from Phase-2 brief: giveup first; scope = item-3 background + quiet + `clear_hold_meta`; forget/tool unlocked reads = known issue only; no Hermes double-end change; quiet/runner follow live provider; D1 A/B with item-5 numbers + init/prefetch/retrieval; time successful `_commit`; history verdict stays measured.*

### Giveup (answer first) — MEASURED + SOURCE

**What `consolidate.giveup` does to pending turns: it leaves them.**  
SOURCE (`consolidate.py` ~458–468): after `attempt > CONSOLIDATE_MAX_ATTEMPTS` it logs `consolidate.giveup` (`attempts`, `pending_count`) and returns `False` unless `trigger == "initialize"` (which resets the in-memory attempt counter and retries once). It does **not** delete pending rows and does **not** mark them. Pending stay in `pending_turns` until a later successful `_commit` (or an intentional empty-episode commit).

**Distinct giveup events (fingerprints) from the live log** — contiguous runs with the same `pending_count`, split on gap >90s or count change (1541 giveup lines → **4 fingerprints**):

| Date | Fingerprints | Turns involved (`pending_count` sum) | Detail |
|------|-------------:|-------------------------------------:|--------|
| 2026-10-08 | 1 | 3 | pc=3, 2 log lines |
| 2026-11-05 | 2 | 6 | pc=4 (118 lines); pc=2 (816 lines) |
| 2026-11-06 | 1 | 1 | pc=1 (605 lines) |
| **Total** | **4** | **10** | |

**Giveups after closed/replaced-connection failures:** **0 of 4.**  
Each series is preceded by consolidate `ok=false` with the same `turns=pending_count` and climbing `attempt` 1…5 — normal LLM/validate failures. Zero `ProgrammingError` / closed-database strings in the memory log (exceptions on the runner are often swallowed). No series matches a closed-connection failure pattern.

**Turns dropped without becoming episodes?**  
- **By giveup: no.** Giveup never deletes pending.  
- **After giveup:** every series later had a successful consolidate that cleared that backlog (often via `quiet`; sometimes into `episodes=0`, which is intentional empty commit — still not a silent drop).  
- **By the shutdown race:** pending are not deleted by close; live snapshot after Phase-1 close had `pending_turns=0`. An AV mid-statement can abort a run; rows survive unless `_commit` already committed. Mid-`_commit` is one SQLite transaction (episodes + pending deletes) — no partial “episode without delete” path in source.  
- **Residual risk (not giveup):** if a closed-connection error were counted as an attempt, a fingerprint could burn to giveup while the store was only temporarily dead. **Fix requirement (plain):** a “store closed” stop and closed-connection errors **must never count as attempts**.

### 1. Ordering rule (design)

Claude’s shape, confirmed, with scope from the Phase-2 brief:

1. Under `self._lock`, set `self._conn = None` (and a closed flag if useful) so new work sees no live connection.  
2. Take `store.locked(old_conn)` — waits for any in-progress protected block.  
3. Close the connection **while holding that lock**.  
4. `release_lock(old_conn)` only after close.  
5. `clear_hold_meta` runs **inside** that same locked block (today it runs unlocked under `self._lock` only — in scope to fix).

**Helper:** every background DB access (consolidate runner, lease acquire/renew/release, sanitize retry, quiet timer, `_build_model_input`, `validate_episodes`, commit/ROLLBACK/finally) goes through one helper: acquire `store.locked(conn)` → assert `provider._conn is conn` (still live) → else stop with outcome **`store_closed`**. Log once (fields only). **Not** an error; **not** an attempt.

**Coverage vs Phase-1 conn table**

| Site | Covered? |
|------|----------|
| quiet timer `count_pending` | yes (helper + live-provider register) |
| lease acquire/renew/release | yes |
| sanitize + list pending | yes |
| `_build_model_input` / `validate_episodes` | yes — full cursor read inside helper |
| LLM call | n/a (no DB); stays **outside** lock |
| `_commit` + ROLLBACK/finally | yes |
| `clear_hold_meta` in shutdown | yes (moved into locked close) |
| prefetch / sync_turn / on_turn (hold `self._lock`) | shutdown holds `self._lock` first → these wait or see `_conn is None`; no new race with close |
| forget/tool scans that hold **only** `provider._lock` | **safe from close** (serialized by `self._lock`), but **not** serialized with consolidator transactions → **known issue; do not fix this track** |

**No new deadlock:** lock order is always `self._lock` then `store.locked(conn)` on shutdown; background never takes `self._lock`. Reaper waits on `store.locked` only while a consolidator holds a short DB block (not during LLM). LLM remains outside the lock.

**Hermes double `on_session_end`:** do **not** change Hermes. Provider-side: `on_session_end` / `shutdown` safe if called twice and after shutdown (`_conn is None` → no-op consolidate; second shutdown no-op).

**Quiet timer / runner (minimal fix, required for D1-A):**  
- Register/unregister the **current** provider on `initialize` / `shutdown` (or look up the live provider each tick). Timer must not stay pinned to the first provider.  
- On shutdown with a run in flight: runner sees `store_closed`, stops cleanly, clears `_running`; a later trigger on the new provider can start (`_coalesce` / `_running` work for the live provider).  
- Coalesce stores enough to target the live provider (provider ref or lookup), not only a trigger string against a dead closure.

### 2. D1 — framed for Brian (item-5 numbers)

**What happens today (Phase 1 item 5, ~last two weeks, counts only):**

| Outcome | Count |
|---------|------:|
| consolidate `ok=true` (all triggers) | 78 |
| consolidate `ok=false` | 45 |
| `on_session_end` | 57 |
| `shutdown` | 29 |
| `shutdown` while lease held | **44** |
| `session_end` consolidate `ok=true` | **1** |
| `session_end` `ok=false` | 21 (mostly `turns=0 attempt=0`) |
| `initialize` `ok=true` / `false` | 38 / 3 |
| `quiet` `ok=true` | 40 |

So ending-session consolidate almost never finishes successfully on the dying provider; recovery is mostly **`initialize`** and **`quiet`** later.

**(A) Stop cleanly, finish later**

- Shutdown waits only for the current protected DB block. Worst measured successful `_commit` on scratch: **~6 ms** (20–50 pending / 3–8 episodes; n successful samples 6.05 ms and 5.39 ms). Lease cycle ~3.3 ms. LLM stays outside the wait.  
- Ending session’s pending stay on disk; next `initialize` / quiet / session_end on a **live** provider consolidates them (quiet/runner fix required so “later” is real in-process).  
- **(A) close/reopen for Brian:** last session’s pending remain until a later trigger. On reopen, `initialize` opens the store synchronously (`elapsed_ms=9` on 2026-11-13 17:25:17) and **signals** consolidate asynchronously (`request_consolidate` — non-blocking). First-question **prefetch** runs later, on the first turn (`turn_context` → `prefetch_all`), after agent `initialize_all` has returned. Prefetch reads **episodes only** (`retrieve.retrieve_episodes`); **unconsolidated pending do not affect retrieval**. So: store open finishes before first prefetch; backlog consolidate may still be in flight during that question, but it does not change what prefetch returns until episodes are committed.  
- Crash / hard kill: same as today for pending survival; no wait.

**(B) Let it finish, with a cap**

- Cap: **`CONSOLIDATE_LLM_TIMEOUT_S + 5s` = 35s** (one LLM budget plus small DB margin). Shutdown joins the consolidator up to that cap, then falls back to (A).  
- What waits: the TUI reaper / teardown thread (and on serve exit, whatever calls `shutdown_all`). Hermes already drains mem-sync ≤10s and shutdown drain ≤5s around provider shutdown on some paths; this wait is **additional** on the reaper path that today has no memory barrier.  
- If the client terminates serve **before** the cap: process dies; in-flight consolidate aborts; pending that were not committed stay pending (same as crash). Cap does not help a killed process.  
- Brian would notice: slightly longer session teardown when consolidate is mid-LLM; memories from that session more often land before reopen when the wait succeeds.

**Recommendation (marked as recommendation):** choose **(A)** plus the quiet/runner live-provider fix. Item 5 shows `session_end` almost never completes on the dying provider anyway (`ok=true` = 1); recovery already depends on later triggers. Waiting up to 35s on the reaper for a rare win is poor fit for TUI teardown and does not help client kill. (A) matches “pending survive; finish later” if and only if quiet/runner follow the live provider.

### 3. Lease after abandoned run

In the same `store.locked` block before close: if this process’s `_instance_id` owns the lease, clear lease meta (`owner` / `expires_at`). Next consolidator (same or new process) is not blocked for up to `CONSOLIDATE_LEASE_TTL_S` (60s) by a zombie lease from a clean shutdown. Process crash / AV still relies on TTL expiry (unchanged).

### 4. Regression tests (design)

- Deterministic unsafe-ordering detector (hook/event: close while another thread holds protected block) — fails on base commit.  
- Shutdown during paused fake LLM → old worker makes no further DB calls, consumes **no** attempt, cannot touch replacement provider.  
- Repeated shutdown (×2); worker waiting on lock when shutdown starts.  
- Recovery via real lifecycle: A shuts with pending; B opens same scratch DB; pending consolidate via initialize/quiet/session_end (not hand-called).  
- Atomic commit: no loss/duplication after abort + retry.  
- Subprocess faulthandler stress with timeout; report median/max shutdown ms; fail on any AV.  
- Pending survive abort; next run consolidates.  
- `store_closed` logged once; **not** counted as attempt; closed-connection errors same.  
- Lease not stuck after clean shutdown.  
- No-deadlock timeout.  
- Existing `zola_memory` suite still passes.

**Existing tests that touch these paths:** `test_episodes_phase4` (giveup, consolidate, quiet); `test_zola_memory` / forget suites (shutdown, initialize); registry switch tests.

### 5. Dev smoke design

Brian closes stable → detector → `Sync-DevPlugins` → start **dev** Zola → short invented-fact conversation → end session (new chat or idle reap; if reap is hours, use `/new` or session switch so teardown runs without waiting 6h) → new session → ask for the invented fact → close dev. Log fields only: consolidate finish or `store_closed`, shutdown `ok`, no serve crash; recall of invented fact. No live data.

### 6. Files / floors

| File | Change |
|------|--------|
| `provider.py` | ordered shutdown; register/unregister quiet; idempotent end/shutdown; `clear_hold_meta` under lock |
| `consolidate.py` | helper; `store_closed`; attempt policy; quiet live provider; runner/`_running`/`_coalesce` |
| `store.py` | lock/close ordering support if needed (`release_lock` after close only from provider) |
| `forget.py` | only if `clear_hold_meta` call site moves (no behaviour change) |
| `tests/` | new regression + stress |
| `floors.json` | raise `zola_memory.min_passed` from **162** by the new test count |
| this progress doc | Phase 2–7 |

### Successful `_commit` timing (MEASURED, scratch)

| Sample | Pending turns | Episodes | `_commit` ms |
|--------|--------------:|---------:|-------------:|
| 1 | 12 | 3 | **6.05** |
| 2 | 50 | 8 | **5.39** |

Worst wait shutdown sees under (A) for a protected commit block: **~6 ms** on this hardware (LLM not included; stays outside lock).

### Historical crash verdict (unchanged)

| Class | Fit | Partial | No fit |
|-------|----:|--------:|-------:|
| `0x3b1ff` | 6 | 3 | 1 |
| sqlite | 0 | 2 | 1 |

The final report **must not** claim every historical crash is explained.

### Known issue (recorded, not fixed)

Forget/tool reads that hold only `provider._lock` are safe from connection close (shutdown holds `self._lock`) but are **not** serialized with the consolidator’s transactions.

---

## STOP — Phase 2

Design + giveup answer + D1 framing complete. **No fix code written.**  
Await **Brian’s D1 decision (verbatim)** and Claude’s review before Phase 3.

---

## Phase 3 — Implement (STOP)

**Brian D1 (verbatim):** `(A) Approved`

### Implemented

- Ordered shutdown (D1=A): null `_conn` under `self._lock` → `store.locked` → `clear_hold_meta` + lease release-if-ours → `close` → `release_lock`.
- `_db(provider)` helper for all consolidator/quiet/lease DB access; `StoreClosed` / closed-conn errors → `zola_memory.store_closed` once, **not** an attempt.
- Lease holder tracked as `id(provider)`; `release_lease_if_held_by` only clears when this provider’s run holds it.
- Quiet timer: live-provider registry; pick **oldest registered** provider with live `_conn` and not `_shutting_down`.
- `on_session_end` / `shutdown` safe if called twice or after shutdown.
- Lock order: consolidator never takes `provider._lock` (always provider → store on shutdown path).

### Known issues (recorded, not fixed)

1. Forget/tool reads that hold only `provider._lock` are not serialized with consolidator transactions.
2. Retrieval reads finished memories only, so the newest turns are searchable only after consolidation (a short catch-up after reopening).

### Stress test (same N=69)

| | BEFORE | AFTER |
|--|-------:|------:|
| n | 69 | 69 |
| av (0xC0000005) | **9** | **0** |
| clean | 60 | 69 |
| worker_exc / shutdown_exc / timeout | 0 | 0 |
| shutdown_ms median | 3.003 | 3.370 |
| shutdown_ms max | 9.280 | 8.946 |
| elapsed_s | 99.8 | 70.1 |

### Unit tests

- New: `tests/test_s51m_shutdown.py` (8 tests).
- `zola_memory` suite: **170** passed (floor raised 162 → 170).

### Gate

```
zola_memory PASS 170; all others PASS except zola_phone INFRA
OVERALL INFRA exit=2 — one or more suites INFRA — uncommitted changes
commit a68cb84… dirty=True
result: %TEMP%\zola-test-gate\20261113-202058\result.json
```

### Diff

`C:\Users\test\Dev\zola-spikes\prompts\S51M-FIX_Phase3.diff` (UTF-8).

### Files touched

| File | Role |
|------|------|
| `consolidate.py` | helper, lease holder, quiet live providers, store_closed |
| `provider.py` | ordered shutdown, register/unregister, idempotent end |
| `log.py` | `LOG_EVENT_STORE_CLOSED` |
| `tests/test_s51m_shutdown.py` | new |
| `tests/test_episodes_phase4.py` | `_commit` signature |
| `floors.json` | 162 → 170 |
| this progress doc | Phase 3 |

Historical crash verdict unchanged: `0x3b1ff` 6/3/1, sqlite 0/2/1 — not every historical crash is explained.

---

## STOP — Phase 3

Fix implemented. Stress before/after reported. Await Claude review (Phase 4) before further changes.

---

## Phase 4 — Review fixes (STOP)

### Line endings

| File | index | worktree (after normalize) |
|------|-------|----------------------------|
| consolidate/provider/log/test_episodes | `i/lf` | `w/lf` |
| `core.autocrlf` | `true` | commit stores **LF** (unchanged from HEAD) |

`git diff --stat` (content, not whole-file noise): consolidate ~541 lines touched; log +1; provider ~40; test_episodes ±6. Phase 3 review diff’s whole-file rewrites were from a bad regenerator (CRLF WT vs LF index written without newlines). Regenerated Phase 4 diff is plain `git diff`.

### Fixes

- Closed detection by **state** (`_shutting_down` or `_conn` gone/replaced), not `ProgrammingError`/`InterfaceError` type.
- `store_closed` once per provider lifecycle (cleared on `register_live_provider`).
- Coalesce: clear `_coalesce_provider` after read; fall back to `_pick_live_provider()`; stop if none live.

### Tests

- ProgrammingError on live provider → attempt counted.
- Two mid-run shutdowns → two `store_closed`.
- Replacement via background `initialize` only; wait pending=0; 1 episode.
- Shutdown-during-LLM: `_db` yields after arm = 0.
- Worker blocked on `store.locked` → `StoreClosed`, no attempt.
- Bounded stress in suite (N=20, <60s).

### Base-commit failures (scratch copy of HEAD `consolidate`/`provider`/`log` + new tests)

| Test | On base |
|------|---------|
| `test_shutdown_waits_for_store_lock_then_closes` | **FAIL** (`ProgrammingError: closed database` in holder; `released.wait` False) |
| `test_unsafe_close_ordering_detected_on_hooks` | **FAIL** (`[True] != [False]`) |
| `test_bounded_stress_no_access_violation` | **FAIL** (`av=5 n=20`) |

### Suite / stress / floor

- `zola_memory`: **174** PASS; floor **174**.
- N=69 after: **av=0**, clean=69, shutdown_ms median 5.2 / max 16.7.

### Gate

```
zola_memory PASS 174; all others PASS except zola_phone INFRA (Zola up)
OVERALL INFRA exit=2 — uncommitted changes
result: %TEMP%\zola-test-gate\20261114-103347\result.json
```

### Diff

`C:\Users\test\Dev\zola-spikes\prompts\S51M-FIX_Phase4.diff` (plain `git diff`, UTF-8, LF).

---

## STOP — Phase 4

Review fixes done. Await merge/Phase 5 instructions.

---

## Phase 5 — Teardown path (SOURCE) + Brian smoke (in progress)

### Ordinary action that hits real TUI teardown + `provider.shutdown`

**Answer: New Conversation (or Resume another session) in the client — not slash `/new`, not app close, not 6h idle.**

| Candidate | Hits `_finalize_session` → `commit` → `close` → `shutdown`? | Notes |
|-----------|:---:|-------|
| Slash `/new` / session switch via `commit_session_boundary_async` | **No** | `on_session_end` only; no `shutdown` (Phase 1 table) |
| **New Conversation / Resume other session** | **Yes** | Client `Abort` old WS → park `_detached_ws_transport` → `_schedule_ws_orphan_reap` (~20s grace) → `_teardown_popped_session(..., end_reason=ws_orphan_reap)` while serve stays up |
| Close Zola client | Unreliable | `HermesProcessManager` Kill+Wait; process death often skips graceful atexit teardown |
| Serve atexit `tui_shutdown` | Rare on Zola path | Needs graceful serve exit; client close does not guarantee it |
| 6h TUI idle reaper | Yes but rejected | `_SESSION_TTL_S` default 6h — not acceptable for smoke |

**SOURCE:** `ChatSocket.OpenAsync` Aborts previous socket before `session.create`/`session.resume` (`ChatSocket.cs`). Desktop does not set `close_on_disconnect`. `_close_sessions_for_transport` parks + `_schedule_ws_orphan_reap` (`session_lifecycle.py`); grace default **20s** (`server.py` `_WS_ORPHAN_REAP_GRACE_S`). Reap → `_teardown_popped_session` → finalize → double `on_session_end` + `shutdown`.

**Nov-12 FIT (Crash B):** `10:46:39` `client_disconnect` + `detached_sessions=1` + new WS/agent; `10:47:06` / `10:47:15` / `10:47:32` `on_session_end`×2 + `shutdown` (~20–27s later) matching orphan reap; `10:47:44` serve restart after crash mid-teardown.

### Brian — do this before you start (exact)

1. **Close stable Zola completely** (quit the app). Do not start anything yet. Say when it is closed (or just close — agent detects and syncs).
2. After sync confirmation, start **dev** only:
   `dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj`
   (Debug → `hermes-dev` / `zola-dev`. Do **not** reopen stable.)
3. Invent a one-off fact (not real), tell Zola, get a short reply. Wait until the turn is fully idle.
4. Click **New Conversation** (UI). **Do not** use slash `/new`. **Do not** quit the app.
5. **Wait ≥30 seconds** (WS-orphan grace ~20s + teardown) with the new empty session open. Serve must stay up.
6. In the new session, ask about the invented fact. Report whether she recalls it (your words).
7. Close **dev** when done. Do not start stable until the gate `-Promote` finishes (agent runs that with stable still closed).

**Pass (field-only):** `on_session_end` ×2 → consolidate start or lease → `shutdown ok=true` → consolidate end or `store_closed`; no serve crash; next-session initialize consolidation commits pending; recall. Agent reports shutdown duration from the log.

**Order remaining:** close stable → Sync-DevPlugins → Brian starts / smoke → close dev → gate `-Promote` (expect DIRTY exit 3) while stable closed → Brian starts stable → experience check → record every close/start time.


### Timeline (Phase 5)

| Event | Local time |
|-------|------------|
| Stable close (0 client / 0 serve) | 2026-11-15 **13:04:16** |
| Sync-DevPlugins `-From` worktree `-Replace` (57 files; provider/consolidate/log SHA match) | 2026-11-15 **13:04:37** |
| Dev start (plugin discovery / WS accept) | 2026-11-15 **13:06:17** / **13:06:19** |
| New Conversation (WS disconnect + detached) | 2026-11-15 **13:14:22** |
| Orphan teardown + `shutdown` | 2026-11-15 **13:14:42** |
| Dev close (confirmed 0/0) | 2026-11-15 **13:15:25** (Brian: closed; agent confirm) |
| Gate `-Promote` | 2026-11-15 **13:15:53** → **13:24:15** |
| Stable start (`proc1-dev` pid 21020) | 2026-11-15 **13:25:03** |

### Experience check (Brian, verbatim)

> When a conversation ends, Zola doesn't crash, and what I told her is still remembered next time.

### Dev smoke — PASS (field-only)

**Brian (verbatim):** She recalled that I used to be an astronaut.

**Log sequence (hermes-dev `zola_memory.log`):**

```
13:14:22.511 store_open pid=24000
13:14:22.516 consolidate.lease acquired
13:14:33.828 consolidate trigger=initialize turns=1 episodes=1 ok=true elapsed_ms=11311
13:14:42.306 on_session_end message_count=4
13:14:42.309 consolidate.lease acquired
13:14:42.317 on_session_end message_count=4
13:14:42.319 shutdown ok=true
13:14:43.739 store_closed ok=true trigger=session_end
13:14:45.102 consolidate trigger=session_end turns=1 episodes=0 ok=true elapsed_ms=1355
```

| Check | Result |
|-------|--------|
| `on_session_end` ×2 → lease → `shutdown ok=true` → `store_closed` / consolidate end | **PASS** |
| Next-session `initialize` commits pending (turns=1 episodes=1) before orphan teardown | **PASS** |
| Serve crash (same pid 24000; no rediscovery mid-session) | **none** |
| Recall | **PASS** (Brian) |
| **Shutdown duration** (1st `on_session_end` → `shutdown ok=true`) | **13 ms** (42.306 → 42.319) |

### Gate `-Promote` (stable closed)

```
OVERALL DIRTY exit=3 — uncommitted changes in the working tree
all suites PASS (memory 174, phone 72, assemble_debug 1, …)
commit a68cb84… dirty=True
result: %TEMP%\zola-test-gate\20261115-131553\result.json
```

---

## STOP — Phase 5

Dev smoke PASS (real WS-orphan teardown; shutdown **13 ms**; recall PASS). Gate `-Promote` DIRTY exit 3 (all suites PASS). Experience check recorded. Timeline complete. Await Phase 6 / merge instructions.

---

## Phase 6 — Commit and merge

Progress doc UTF-8 cleaned before commit (removed BOM; repaired double-encoded punctuation across the whole file). Other diff files audited: no mojibake.

**Brian go-ahead (verbatim):** commit and merge

### Commit

| Item | Value |
|------|-------|
| Branch | `s51m-fix` |
| SHA | `7b07c70e5e666c0831c6db86d4822ed775833895` |
| Message | `fix(S51M): close memory store only after background work stops — S51 0x3b1ff/sqlite crash class` |
| Files (7) | `consolidate.py`, `log.py`, `provider.py`, `test_episodes_phase4.py`, `test_s51m_shutdown.py`, `floors.json`, `S51M-FIX_Progress.md` |

### Zola closed

| Event | Time |
|-------|------|
| Closed (confirmed 0 client / 0 serve) | 2026-11-16 **07:07:27** |

### Gate on committed tip (`-Promote`, Zola closed)

Result: `%TEMP%\zola-test-gate\20261116-070735\result.json`  
**OVERALL PASS exit=0**. Commit before=after `7b07c70…` dirty=False. Overrides all false.

### Merge

Fast-forward `main` ← `s51m-fix` in live checkout. Merged tip = `7b07c70…`. Pushed `origin/main`.

### Gate on merged tip (`-Promote`, Zola still closed)

Result: `%TEMP%\zola-test-gate\20261116-071626\result.json`  
**OVERALL PASS exit=0**. Commit before=after `7b07c70…` dirty=False. Overrides all false.

### Tag

Annotated tag **`fix-s51m`** → `7b07c70e5e666c0831c6db86d4822ed775833895` (pushed).

Zola kept closed for Phase 7 promotion decision.

---

## Phase 7 — Promotion report (await Brian's decision)

### What promoting `fix-s51m` changes for everyday Zola

Stable today is **`proc1-dev`**. Promoting `fix-s51m` replaces that Release build with one built from tag `fix-s51m` (`7b07c70…` on `main`). Everyday Zola then runs the S51M memory shutdown fix: when a conversation ends (WS-orphan teardown), serve no longer races consolidator vs `provider.shutdown`, so the Nov-12 crash class (`0x3b1ff` / sqlite AV) is closed on that path; pending turns survive and consolidate later.

Also on `main` since `proc1-dev` (already merged earlier, not yet in the stable folder): PROC1-DEV closeout docs, PROC1-GATE (test gate tooling), and related docs commits. The **client/tools** in the new stable folder therefore pick up everything from `proc1-dev` → `fix-s51m`. The **live plugin copy** for this promotion is expected to touch only `zola_memory` runtime files (tests are not mirrored).

### Plugin files expected to differ (live profile mirror)

Compared to current live `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\`:

| File | Role |
|------|------|
| `consolidate.py` | ordered shutdown helper, lease-by-provider, quiet live registry, `store_closed` |
| `provider.py` | null-conn then wait `store.locked` then close |
| `log.py` | `STORE_CLOSED` event |

`store.py` / `forget.py` match live already. New tests stay in the repo only.

### Decision

**Brian (verbatim):** `[promote fix-s51m]`

Plugin diff from Prepare matched exactly:
`plugins/zola_memory/consolidate.py`, `provider.py`, `log.py` — Brian's verbatim `[promote fix-s51m]` is the `-ApprovedPluginCopy` approval.

### Prepare

| Item | Value |
|------|-------|
| Start / end | 2026-11-16 **07:39:25** → **07:41:10** |
| Tag commit | `7b07c70e5e666c0831c6db86d4822ed775833895` |
| Client build hash | `6f1bff9439c314eedbbb3b0d4b5e25480ef31ddf31c702d60d0d81f2cbf902d4` |
| Plugin compare | changed only the three `zola_memory` files above |

### Switch

| Item | Value |
|------|-------|
| Promoted | 2026-11-16 **07:42:36** (exit 0) |
| Stable folder | `C:\Users\test\Zola\stable\fix-s51m\` |
| `current.txt` | `fix-s51m` |
| Backup | `C:\Users\test\Zola\stable\backups\fix-s51m-20261116-074136` |
| Drill | PASS — databases=5, files=823, credentials=5; scratch deleted |
| Outgoing | `proc1-dev` |
| Plugins copied | consolidate.py, provider.py, log.py (live SHA match tip) |

### Shortcut start + stable smoke

| Item | Value |
|------|-------|
| Client start | 2026-11-16 **07:43:35** pid 5396 `…\stable\fix-s51m\Zola.Client.exe` |
| Serve start (crash watch restart) | 2026-11-16 **07:43:37** / supervisor serve start **07:43:38** (launcher 18288, child 25956) |
| Identity | `role=stable why=ok tag=fix-s51m` |
| Drift | `completed=true components=none` |
| Memory | `store_open` + `initialize ok=true`; profile `-p zola` (not hermes-dev) |

### Crash watch — every `python.exe` Application Error since 2026-11-09 13:23:08

Count: **28**. Offsets shown.

| Time (local) | Module | Exception | Fault offset | PID |
|--------------|--------|-----------|--------------|-----|
| 2026-11-12 10:36:04 | python312.dll | 0xc0000005 | 0x3b1ff | 13640 |
| 2026-11-12 10:47:32 | sqlite3.dll | 0xc0000005 | 0xc9310 | 25000 |
| 2026-11-13 16:25:46–16:28:06 | python312.dll | 0xc0000005 | mostly 0x3b1ff (10 events; one 0x47e64) | cluster |
| 2026-11-13 20:04:21–20:05:50 | python312.dll / sqlite3.dll | 0xc0000005 | 0x3b1ff / 0x47e64 / 0xc92b0 (9 events) | cluster |
| 2026-11-14 10:30:00–10:30:46 | python312.dll | 0xc0000005 | 0x3b1ff / 0x47e64 (5 events) | cluster |
| 2026-11-14 16:22:00 | python312.dll | 0xc0000005 | 0x3b1ff | 22692 |
| 2026-11-15 12:54:46 | python312.dll | 0xc0000005 | 0x3b1ff | 13920 |

Nov-13 afternoon/evening and Nov-14 10:30 clusters align with S51M Phase 3/4 scratch stress (before-fix AVs). Nov-12 pair = the motivating live crashes. Nov-14 16:22 and Nov-15 12:54 = live serve (supervisor stale/restart). Full TSV: `%TEMP%\s51m-crashes.tsv`.

### Deliberate closes / starts this track

| Event | Time |
|-------|------|
| Stable close (Phase 5) | 2026-11-15 13:04:16 |
| Dev start / close (smoke) | 13:06:17 / 13:15:25 |
| Stable start (experience) | 13:25:03 |
| Stable close (Phase 6) | 2026-11-16 07:07:27 |
| Promote Switch | 07:42:36 |
| Stable start (promoted) | 07:43:35 — crash watch restart |

### Verdict (required wording)

The shutdown race is fixed and the crash watch has restarted; longer observation decides whether it accounts for all historical 0x3b1ff/sqlite crashes (history fit: `0x3b1ff` 6/3/1, sqlite 0/2/1).

---

## Closeout

### Live checkout sync

| Item | Value |
|------|-------|
| Live | `C:\Users\test\Dev\zola-windows` on `main` |
| Tip | `2b10f10…` (docs record) + implementation `7b07c70…`; matches `origin/main` after closeout commit |

### Worktree / branch

| Item | Value |
|------|-------|
| Worktree remove | OK — C:\Users\test\Dev\zola-windows-s51m-fix gone |
| Branch delete | local s51m-fix deleted (was 7b07c70) |
| Remote branch | never pushed |


---

---

## Post-closeout note — live crash stacks on old code (2026-11-16)

Read-only. Two Application Errors after the Nov-12 motivating pair, still on unfixed `zola_memory`, with faulthandler in `%LOCALAPPDATA%\ZolaClient\logs\serve-stderr\serve-stderr.log`.

### Crash-watch counting rule (from now)

Count only `python.exe` Application Errors whose faulting PID appears as `supervisor proc=serve … child_pid=<pid>` in `%LOCALAPPDATA%\ZolaClient\logs\supervisor.log`. List stress/test/unknown crashes separately.

### A — 2026-11-14 16:22:00 pid=22692 (`python312.dll+0x3b1ff`)

Serve child: `2026-11-13T17:25:04` `child_pid=22692`.

**Crashing thread** (`serve-stderr` ~L400–409): consolidator `_runner` → `run_consolidation` → `try_pending_sanitize` → `store.meta_get` (store.py:466).

**Teardown thread** (~L438–453): Timer `_reap` → `_teardown_popped_session` → `agent.close` → `shutdown_memory_provider` → `provider.shutdown` (provider.py:359).

**zola_memory fields (~1 min before):**
```
16:21:41 store_open pid=22692
16:21:59.920 on_session_end message_count=65
16:21:59.920 consolidate.lease acquired ok=true
16:21:59.920 consolidate.lease released ok=true
16:21:59.926 on_session_end message_count=65
16:21:59.926 consolidate.lease acquired ok=true
```
No `shutdown ok=` before the AV (dies mid-shutdown).

**Fit:** **yes** — consolidator in SQLite + teardown `shutdown`.

### B — 2026-11-15 12:54:46 pid=13920 (`python312.dll+0x3b1ff`)

Serve child: `2026-11-14T16:22:11` `child_pid=13920` (replacement after crash A).

**Crashing thread** (`serve-stderr` ~L590–599): consolidator `_runner` → `run_consolidation` → `_release_lease` → `store.meta_set` (store.py:471).

**Teardown thread** (~L608–630): same `_reap` → … → `provider.shutdown` (provider.py:363, logging `shutdown` event via `write_event`).

**zola_memory fields (~1 min before):**
```
12:54:27 store_open pid=13920
12:54:46.455 on_session_end message_count=25
12:54:46.462 on_session_end message_count=0
12:54:46.462 consolidate.lease acquired ok=true
```
No `shutdown ok=` before the AV; next line is `12:55:08 store_open pid=29536` (restart).

**Fit:** **yes** — consolidator in SQLite + teardown `shutdown`.

### Crash-watch recount since 2026-11-09 13:23:08

| Class | Count | Events |
|-------|------:|--------|
| **Live serve-child** | **3** | 2026-11-12 10:47:32 pid=25000 sqlite3+0xc9310; 2026-11-14 16:22:00 pid=22692 0x3b1ff; 2026-11-15 12:54:46 pid=13920 0x3b1ff |
| Stress / test / unknown | 25 | Nov-13 16:25–16:28 and 20:04–20:05 clusters; Nov-14 10:30 cluster; Nov-12 10:36:04 pid=13640 (matched `store_open` but not a logged serve `child_pid`) |

### Promotion wording (Brian, verbatim)

`[promote fix-s51m]`

## STOP — S51M-FIX COMPLETE

