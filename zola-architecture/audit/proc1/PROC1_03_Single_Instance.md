# PROC1_03 — Single Instance

**Audit:** PROC1 · Phase 2 · read-only  
**Prompt:** v1.1 · SHA-256 `94f130a0e81abb6a56a73d0bfd00ce5ab53c550bcaffed0b1295dbe0dc1d542f`

## Summary

There is **no** client-wide single-instance mutex. A second `Zola.Client` can start; it will try to attach to an existing dedicated serve or spawn another, and it will start its own watcher/phone — which then hit named mutexes and fail or contend. Phone (`Local\ZolaPhone`), watcher (`Local\ZolaWatcher`), ranker (`Local\ZolaRanker`), and OAuth refresh (`Local\ZolaOAuthRefresh`) are the process locks that exist today. None identify “stable vs dev,” and none make the second build announce which build is running.

## Evidence

### 1. Mutexes, pipes, ports, process checks

| Mechanism | Name / value | Owner | On conflict | SOURCE |
|---|---|---|---|---|
| Mutex | `Local\ZolaPhone` | `zola_phone.__main__._acquire` | return `EXIT_ALREADY_RUNNING` (2); also pipe `FILE_FLAG_FIRST_PIPE_INSTANCE` can fail → same exit | `__main__.py` 16–32, 54–67; `runtime.EXIT_ALREADY_RUNNING` |
| Named pipe | `\\.\pipe\ZolaPhone` | phone serve | first-instance flag | `phone_protocol.json` `pipe_name`; `serve.create_pipe` |
| TCP port | Tailscale **47821** (env `ZOLA_PHONE_LISTEN_PORT` override) | phone listen | bind fail / rebind rules | protocol `listen_port`; `__main__.py` 75 |
| Mutex | `Local\ZolaWatcher` | `watcher.acquire_instance` | WARN `already_running`, return False → exit 2 (progress) | `watcher.py` 41, 115–127 |
| Mutex | `Local\ZolaRanker` | ranker worker in serve | second worker logs `already_running`, clears flag | `ranker.py` 46; P9-RANK progress |
| Mutex | `Local\ZolaOAuthRefresh` | token refresh POST | wait up to 45s then `RefreshLockTimeout` | `auth.py` 37–40, 84–95 |
| Serve attach | process scan for dedicated `-p zola serve --isolated` | `HermesProcessManager` | **attach**, do not kill; “This window will not stop it.” | `HermesProcessManager.cs` 105–111, 181–188 |
| Client mutex | *(none found)* | — | Second client allowed | `App.xaml.cs` has no CreateMutex; grep of client `.cs` shows no instance mutex |

**Suite failure while Zola runs** (SOURCE `S51F-FIX_Progress.md` / P10-LORE):  
`test_f4_second_process_refuses_the_pipe_and_mutex`, `test_isolation_on_the_real_startup_path` — live client holds `Local\ZolaPhone` / pipe → 2 FAIL of 71.

### 2. Second client while one runs (from source)

SOURCE behavior (not launched for this audit — G-NO-RESTART):

1. Second `App.OnLaunched` starts **another** watcher and phone (`App.xaml.cs` 31–42).
2. Second phone: mutex/pipe → exit 2; client supervisor records phone failures (S51F patterns).
3. Second watcher: `Local\ZolaWatcher` → already_running / exit 2.
4. Second serve path: `FindDedicatedServeAsync` may **attach** to the first serve (`OwnsProcess = false`) rather than spawn — so two UI windows can share one backend. SOURCE attach message at L186–188.
5. If no dedicated serve is found, it may spawn another serve with `--port 0` (new port) but **same** `HERMES_HOME` → two writers on the same DBs (**UNVERIFIED** in practice; risky by construction).

Exact UX of two windows **UNVERIFIED** without launching a second client.

### 3. What “refuse and say which build is running” would need (options only)

Today nothing stamps stable vs dev. Options for a later design:

| Need | Option sketches |
|---|---|
| Self-identify | Env `ZOLA_BUILD_ROLE=stable|dev`; marker file under profile; mutex name suffix `Local\ZolaClient-stable` |
| Discover the other | Read holder of a well-known mutex; small status file with pid + role + exe path; named pipe status |
| Message | Second start prints role + path + pid of holder; **never** kills the first (matches target) |

### 4. Risks if a second instance runs today

| Risk | Why |
|---|---|
| Steal / block phone | Second phone loses mutex; first keeps device. Tests and a second “dev” phone both collide on 47821 / pipe |
| Steal watcher | Second watcher exits; first keeps polling — or reverse if first died without releasing (abandoned mutex → acquire) |
| Dual UI on one serve | Attach path shares backend; confusing ownership on close (attached window does not kill serve) |
| Dual serve same profile | If attach fails and both spawn: concurrent SQLite writers on `state.db` / `proactive.db` / `zola_memory.db` |
| OAuth refresh serialization | Mutex mitigates double refresh; timeout can surface as local failure |
| Kill | Client shutdown tree-kills **only** serve it owns; attached serve survives. Watcher/phone use parent-pid watch / job object — second client’s stop should not kill the first’s children if PIDs differ (**UNVERIFIED** edge cases with orphans historically recorded in P10) |

## Gaps against target state

| Target | Today | Gap |
|---|---|---|
| Starting a build while the other runs **refuses** and names which | Client allows second start; child mutexes fail quietly from UI POV | No cross-build refuse + identity |
| Never stops the running build | Attach/owned-kill rules exist for serve; not framed as stable/dev | Partial; orphans still a historical pain |

## Open questions for Brian

1. Have you ever intentionally run two Zola windows, or only hit this via tests / leftover processes?
2. Preference for the refuse signal: modal in the second UI, console-only, or both?
