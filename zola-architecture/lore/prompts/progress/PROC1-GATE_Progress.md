# PROC1-GATE Progress

**Prompt:** `PROC1-GATE_Prompt_v1.1.md`  
**Prompt SHA-256:** `d3769fbf669d9ee70223600f639bcbbbf9e23b83722454e8178796ce5663d2c1` (verified match)  
**Plan:** `PROC1_BUILD_PLAN.md` v1.2 — Track PROC1-GATE  
**Base:** `origin/main` @ `2a98749f1f1a1fcd35b7b8d4391ef1c63e10ed4a`

## Locations

| Item | Value |
|------|-------|
| Live checkout | `C:\Users\test\Dev\zola-windows` (read-only until Phase 7) |
| Track worktree | `C:\Users\test\Dev\zola-windows-proc1-gate` |
| Work branch | `proc1-gate` |
| Stable | `C:\Users\test\Zola\stable\proc1-dev\` |
| hermes-agent pin | `345cd2b057a452236de401d3534b8502a7465e8d` |

## Phase table

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Setup, baselines, facts | DONE | Accepted |
| 2 Design proposal | DONE | Accepted with Brian's decisions |
| 3 Implement | DONE — STOP | self-tests + gate run (Zola up) |
| 4 Review fixes | | |
| 5 Clean run and isolation proof | DONE — STOP | -Promote DIRTY exit 3; phone 72; hash maps match |
| 6 Commit and merge | DONE — STOP | tip+merge PASS exit 0; tag `proc1-gate`; no promotion |
| 7 Live checkout sync and closeout | | |

## Phase 1 — Setup, baselines, facts

### 1. Prompt / live / tag / hermes / stable running

| Item | Value |
|------|-------|
| Prompt SHA-256 | `d3769fbf669d9ee70223600f639bcbbbf9e23b83722454e8178796ce5663d2c1` — MATCH |
| Live branch | `main` |
| Live HEAD | `2a98749f1f1a1fcd35b7b8d4391ef1c63e10ed4a` (`docs: record PROC1-DEV closeout`) |
| Live status | clean; `main` == `origin/main` |
| Tag `proc1-dev` | annotated tag object `deddb0510081decec81ae8270cd45b61ab800813`; peels to `2e9bc4a037be4c57eba5d20c45569e92aa66e686` `Merge branch 'proc1-dev'` |
| hermes-agent | `C:\Users\test\Dev\hermes-agent`, detached HEAD at pin `345cd2b057a452236de401d3534b8502a7465e8d`; `git status --porcelain` empty |
| Stable client | **running** pid **23612**, path `C:\Users\test\Zola\stable\proc1-dev\Zola.Client.exe`, started 2026-11-13 11:58:55. `current.txt` = `proc1-dev`. G-NO-RESTART: not started or stopped. |

Live checkout rechecked after worktree create: still `main`, clean, same SHA.

### 2. Worktree

| Item | Value |
|------|-------|
| Path | `C:\Users\test\Dev\zola-windows-proc1-gate` |
| Branch | `proc1-gate` (from `origin/main`) |
| HEAD | `2a98749f1f1a1fcd35b7b8d4391ef1c63e10ed4a` |
| Live checkout after create | unchanged (`main` @ `2a98749…`, clean) |

### 3. Live and dev access from tests (SOURCE, before any suite run)

**CRITICAL A — `zola_tts` Deepgram key / network — CLOSED**

- Production default key path is `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` (`deepgram_tts.py:24`).
- Tests patch `KEY_PATH` to a temp file and pop `ZOLA_DEEPGRAM_KEY_PATH` (`test_deepgram_tts.py:47–56`).
- Every `main()` path mocks `urllib.request.urlopen`; unmocked call raises `AssertionError("urlopen called")` (`test_deepgram_tts.py:72–82`).
- `test_unset_or_empty_env_uses_todays_key_path` only compares `resolve_key_path()` under a patched `KEY_PATH`; does not read the live file (`test_deepgram_tts.py:236–245`).
- **No live key read. No Deepgram HTTP.**

**CRITICAL B — workspace / memory / tools `HERMES_HOME` — CLOSED**

- **workspace:** tests set `HERMES_HOME` to temp and/or patch `get_hermes_home`; watcher/ranker mutexes overridden to `Local\ZolaWatcherTest` / `Local\ZolaRankerTest` / `Local\ZolaOAuthRefreshTest` (not live names).
- **memory:** every store suite sets `HERMES_HOME` to `mkdtemp`/`TemporaryDirectory`; `test_l6_hold_guard.py` uses `:memory:` only.
- **tools:** `_load_plugin_module` forces `HERMES_HOME` to temp.
- **No fallthrough to live profile found.**

**Tests that need stable Zola closed**

1. `IntakeTests.test_isolation_on_the_real_startup_path` (`test_p10_intake.py`) — spawns `-m zola_phone` → live `Local\ZolaPhone` / `\\.\pipe\ZolaPhone`
2. `IntakeTests.test_f4_second_process_refuses_the_pipe_and_mutex` — same live mutex/pipe

**Dev tools note:** one assert probes live `Local\ZolaClient` (WaitOne / OpenExisting); does not require Zola closed to pass, but probes the live client mutex.

**Checks caveat:** `--drift-dry-run` defaults profile to live `profiles\zola`; not part of default `RunAll`. Gate must not use that flag.

| Suite | Live profile | ZolaClient | hermes-dev / ZolaClient-dev | Live mutex/pipe | Network | Verdict |
|-------|--------------|------------|------------------------------|-----------------|---------|---------|
| Zola.Client.Checks | no (path strings / temp) | no | no | no | no | SAFE |
| Test-StableScripts | no (scratch) | no | no | private test mutex | no (synthetic) | SAFE |
| Test-DevTools | no (scratch LAD) | scratch only | scratch only | probes `Local\ZolaClient` | no | SAFE |
| zola_workspace | no | no | no | test mutex names | localhost only | SAFE |
| zola_memory | no | no | no | no | no | SAFE |
| zola_tools | no | no | no | no | no | SAFE |
| zola_tts | no | no key read | no | no | mocked only | SAFE |
| zola_phone | no (temp HERMES_HOME) | no | no | **YES live phone** (2 tests) | possible Tailscale bind in spawned phone | run with Zola up expected 2 FAIL |
| Kotlin unit | n/a | n/a | n/a | n/a | no | SAFE |

**Item 3 decision:** no suite reads live profile/client data or calls Deepgram/remote network from tests. Proceed to item 4 (run with Zola running; phone expected 2 FAIL).

### 4. Per-suite commands and one run (Zola running)

Shared Python interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe` (3.12.14).  
Shared for plugin suites today: `PYTHONPATH=C:\Users\test\Dev\hermes-agent` (set for these runs; G-CONTROLLED-ENV will clear inherited noise and set only what each suite needs).

| Suite | cwd | Command | Env needed today | Counts from | This run | Floor | s |
|-------|-----|---------|------------------|---------------|----------|-------|---|
| Zola.Client.Checks | repo root | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` | .NET SDK on PATH | console: one `PASS …` / `FAIL …` line per check; exit 0 iff `Failed==0`; coverage line at end | **322 PASS / 0 FAIL**, exit 0 | 322 | 35.2 |
| Stable scripts | repo root | `powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Test-StableScripts.ps1` | (none special); uses hermes venv internally for sqlite fixtures | console `PASS name` / `FAIL name`; `==== SUMMARY pass=N fail=M ====` | **54/0**, exit 0 | 54 | 227.6 |
| Dev tools | repo root | `powershell -NoProfile -ExecutionPolicy Bypass -File tools\dev\Test-DevTools.ps1` | (none special); wrapper already runs `dev_behavior_tests.py` once | same SUMMARY shape | **16/0**, exit 0 | 16 | 7.8 |
| zola_workspace | `hermes-plugins\zola_workspace` | `python -m unittest discover -s tests -t tests` | `PYTHONPATH`=hermes-agent | stderr/stdout: `Ran N tests in T`; `OK` or `FAILED (failures=…, errors=…)`; exit 0 on OK | **582 OK**, exit 0 | 582 | 107.3 |
| zola_memory | `hermes-plugins\zola_memory` | `python -m unittest discover -s tests -t .` | same | same | **162 OK**, exit 0 | 162 | 10.1 |
| zola_tools | `hermes-plugins\zola_tools` | `python -m unittest discover -s tests -t .` | same | same | **44 OK**, exit 0 | 44 | 0.3 |
| zola_tts | `hermes-plugins\zola_tts` | `python -m unittest discover -s tests -t .` | same | same | **9 OK**, exit 0 | 9 | 0.5 |
| zola_phone | `hermes-plugins\zola_phone` | `python -m unittest discover -s tests -t .` | same; clean PASS needs Zola closed | same; FAIL names on traceback headers | **71 ran, 2 FAIL**, exit 1 (expected with Zola up) | 71 closed | 32.4 |
| Kotlin unit | `android-companion` | `gradlew.bat testDebugUnitTest --offline` | `JAVA_HOME`=Android Studio JBR; `ANDROID_HOME`=`%LOCALAPPDATA%\Android\Sdk` | Gradle SUCCESS + JUnit XML under `app\build\test-results\testDebugUnitTest\` | **98** (15+39+30+14), 0 fail/error/skip | 98 | 61.8 (1st) |

**Phone failures (Zola up, expected):**  
`test_f4_second_process_refuses_the_pipe_and_mutex` (`first.poll()` → 2); `test_isolation_on_the_real_startup_path` (no `zola_phone.start` in log).

**`-t tests` vs `-t .` (discovery pitfall)**

| Suite | Correct `-t` | Wrong `-t` observed |
|-------|--------------|---------------------|
| zola_workspace | `tests` | `-t .` → Ran **516**, FAILED (errors=2, `ModuleNotFoundError: test_p8_read`); not silent zero |
| zola_memory / tools / tts / phone | `.` | memory `-t tests` still Ran **162 OK** on this tree (imports tolerate both) |
| empty/wrong start dir | — | empty importable `tests/` → `Ran 0 tests` / `NO TESTS RAN` / **exit 5**; missing start dir → `ImportError: Start directory is not importable` / exit 1 |

Gate must treat Ran 0 / `NO TESTS RAN` / exit 5 as not PASS (D8). Wrong workspace `-t` is FAIL (errors), not a silent pass.

**Failure / INFRA shapes (source + this run)**

| Shape | What it looks like |
|-------|--------------------|
| Test failure | unittest: `FAIL: …` + traceback + `FAILED (failures=N)`; Checks: `FAIL …` lines + exit 1; scripts: `FAIL name` + SUMMARY fail>0 |
| Collection / import error | unittest `ERROR:` / `ModuleNotFoundError`; exit ≠0 |
| Zero tests | `Ran 0 tests` / `NO TESTS RAN` / exit 5 |
| Missing prerequisite | missing `python`/venv; `dotnet` restore/`NETSDK*`; Gradle without `ANDROID_HOME`/JBR before tests; missing start dir ImportError |
| Crash before counts | non-zero exit, no `Ran N` / no SUMMARY / no coverage line → INFRA for the gate |
| Kotlin stale | **2nd run:** `testDebugUnitTest UP-TO-DATE`, 24 tasks up-to-date, ~2.5 s; XML mtimes **unchanged** (still 12:50:00). Gate must `--rerun-tasks` or delete `test-results` first (G-FRESH). XML path: `android-companion\app\build\test-results\testDebugUnitTest\TEST-*.xml` |

**Sample count lines (this run)**

```
Ran 582 tests in 105.217s
OK
==== SUMMARY pass=54 fail=0 ====
==== SUMMARY pass=16 fail=0 ====
coverage: … identity rows 51/51
Ran 71 tests in 31.345s
FAILED (failures=2)
```

Checks: pass count = number of `^PASS ` lines (322); no single total line besides coverage buckets.

### 5. Environment facts

| Variable | Cursor shell (Process) | Plain `powershell -NoProfile` child | User | Machine | Needed by |
|----------|------------------------|--------------------------------------|------|---------|-----------|
| PYTHONPATH | UNSET (set only for plugin runs) | UNSET | UNSET | UNSET | plugin unittest (`hermes-agent`) |
| PYTHONHOME | UNSET | UNSET | UNSET | UNSET | clear for G-CONTROLLED-ENV |
| VIRTUAL_ENV | UNSET | UNSET | UNSET | UNSET | clear; use explicit venv python |
| HERMES_HOME | UNSET | UNSET | UNSET | UNSET | tests set scratch; clear inherited |
| JAVA_HOME | `C:\Program Files\Android\Android Studio\jbr` | same (User) | set (JBR) | UNSET | Kotlin |
| ANDROID_HOME | UNSET (set for Kotlin runs) | UNSET | UNSET | UNSET | Kotlin (`%LOCALAPPDATA%\Android\Sdk` present) |
| ANDROID_SDK_ROOT | UNSET | UNSET | UNSET | UNSET | optional alias |
| DOTNET_ROOT | UNSET | UNSET | — | — | not required; `dotnet` on PATH |
| PIP_* | UNSET | UNSET | — | — | clear for G-CONTROLLED-ENV |

**Versions observed:** Python 3.12.14 (venv); dotnet 9.0.318; OpenJDK 21.0.10 (JBR); Android SDK at `%LOCALAPPDATA%\Android\Sdk`.

**Live checkout after Phase 1:** still `main` @ `2a98749…`, clean.  
**Worktree:** `proc1-gate` @ same SHA; only untracked progress doc `PROC1-GATE_Progress.md`.

---

## Phase 2 — Design proposal (no gate code written)

### A. `zola_phone` spawn (source) — G-NO-LIVE before any Zola-closed run

**Startup path** (`__main__.py` → `listen_forever`):

1. Acquire `Local\ZolaPhone` (`CreateMutexW` + `WaitForSingleObject(0)`).
2. `Engine(temp HERMES_HOME)` → `keys.load_or_create(home/phone)` creates a **new** `pc_key.bin` / empty peer (not the live pairing).
3. `create_pipe(\\.\pipe\ZolaPhone, first=True)` (contract `phone_protocol.json`).
4. Log `zola_phone.start`.
5. `listen_forever(engine, tailscale_ipv4, port, stop)` with `port = int(ZOLA_PHONE_LISTEN_PORT or 47821)`.

Both isolation tests set `ZOLA_PHONE_LISTEN_PORT=0` (`test_p10_intake.py:336`, `:852`).

**TCP / Tailscale (live check on this PC):**

| Check | Result |
|-------|--------|
| `tailscale ip -4` | returns `100.102.206.71` |
| `allowed_bind(that_ip, 0, 0)` | **True** → `bind_action` = **rebind** |
| Effect | `websockets.serve(handler, "100.102.206.71", 0)` binds a **TCP/WebSocket listener on the Tailscale IPv4 with an OS ephemeral port** |
| Contract port 47821 | **not** used while env is `0` |
| `allowed_bind(..., 8765, 8765)` | **False** → refuse (no serve) |

Also held: live mutex + live named pipe. Pipe uses `PIPE_REJECT_REMOTE_CLIENTS` (local only).

**Can Brian’s real paired phone connect / auth / exchange?**

| Step | Verdict |
|------|---------|
| Normal companion reconnect | Targets Tailscale **:47821**. Ephemeral port ≠ 47821 → **will not hit this listener** on the normal path. |
| TCP/WS if port were known | Listener is on the tailnet interface → **reachable in principle** from the phone’s network. |
| Authenticate / signed traffic | Temp home has **no** live `peer_state`; `paired_public=""` → signed frames → `bad-signature` (`wire.classify_raw`). |
| Pairing | No `pairing.start` in these tests → empty pairing code → pairing frames dropped (`pairing-expired` / bad MAC). Launch secret is test-only and only on the local pipe. |
| Send/receive useful data | **No.** |

**Cleanup on test end:** both tests `finally: proc.kill(); proc.wait(timeout=10)` (f4 also `time.sleep(0.4)`). Process death releases mutex, pipe handles, and the asyncio server. Gate timeout cleanup (job object / process tree) covers hung children. **No** explicit `stop.set()` before kill on the real startup path (kill is the release).

**Because a Tailscale TCP listener is opened while these tests pass with Zola closed:** propose the smallest test-only change **before any Zola-closed phone run**:

- In `test_isolation_on_the_real_startup_path` and `test_f4_second_process_refuses_the_pipe_and_mutex` only: set `ZOLA_PHONE_LISTEN_PORT=8765` instead of `0`.
- `allowed_bind` always refuses 8765 → `listen_forever` never calls `websockets.serve`.
- Mutex, pipe, `zola_phone.start` log, and second-process exit 2 are unchanged — what those tests prove stays the same.

**STOP for Brian’s approval of that change before any Zola-closed suite run.**

### B. Dev tools probe of live `Local\ZolaClient`

**Quoted assert** (`tools/dev/Test-DevTools.ps1` 146–163):

```powershell
Assert-That 'replace refuses while Zola is running and leaves the dev folder' {
    ...
    $mutex = New-Object System.Threading.Mutex($false, 'Local\ZolaClient')
    try { $created = $mutex.WaitOne(0) } catch { $created = $false }
    $result = New-DevProfileTree -LocalAppData $root -Replace
    ...
} finally {
    if ($created -and $null -ne $mutex) { $mutex.ReleaseMutex() }
    ...
}
```

**When stable is closed:** `WaitOne(0)` **can acquire** the live mutex (`$created=$true`). It is held for the whole `New-DevProfileTree -Replace` call (seconds), then `ReleaseMutex` in `finally`. That is a live mutex take — G-NO-LIVE conflict.

**Proposed smallest fix** (in scope): replace WaitOne with a **read-only** path:

1. Try `[Threading.Mutex]::OpenExisting('Local\ZolaClient')` and Dispose immediately (no WaitOne). If it opens → call `New-DevProfileTree -Replace` **without** a probe (production OpenExisting path in `DevCommon.Test-ZolaClientOrServeRunning`).
2. If OpenExisting fails (Zola closed) → call `New-DevProfileTree -Replace -RunningProbe { $true }` (same refuse semantics; already used by the sibling assert).

**File:** `tools/dev/Test-DevTools.ps1` only.  
**Still proves:** Replace refuses with reason `refusing: Zola is running` and leaves the canary when “Zola is running” is detected — via live OpenExisting when the mutex exists, or via the injected probe when it does not. Never acquires `Local\ZolaClient`.

### C. Zola-running detection (gate)

**Read-only, never acquire a mutex:**

1. Try `OpenExisting('Local\ZolaClient')` → Dispose immediately. If open → Zola (stable or dev) running.
2. Else try read `%LOCALAPPDATA%\Zola\run\instance.json` (`InstanceStatusFile.DefaultPath`). If present and `pid` is a live process whose image/path matches holder `exe` (or process name `Zola.Client`) → running.
3. Else optional: `Get-Process Zola.Client` and/or `dotnet` with `Zola.Client.csproj` in command line (same as DevCommon; still no mutex acquire).

**When running:** do **not** start `zola_phone`. Suite result **INFRA**, reason exactly like: `stable is running; close Zola for a clean run`. Other suites still run. Self-test: fake “held” detector → phone suite INFRA without spawning python phone tests.

Also keep the existing prompt rule: if somehow phone is attempted while `Local\ZolaPhone` is held → INFRA the same way (detect OpenExisting on `Local\ZolaPhone`, never WaitOne).

### D. Command line

`tools/test-gate/Run-TestGate.ps1 [-RepoRoot <path>] [-Promote] [-Only <suites>] [-UpdateFloors] [-Json <path>]`

- Windows PowerShell 5.1: `powershell -NoProfile -ExecutionPolicy Bypass -File …`
- `-Only` → overall **PARTIAL** (not a pass), exit 3 if otherwise clean
- `-Promote` adds `assembleDebug` row (D9)
- `-UpdateFloors`: only after complete run with every suite PASS (DIRTY allowed); never lowers; preserves skip allowances; atomic write; reports tree dirty
- Default `-RepoRoot` = repo containing the script

### E. Suite table (definitions file + `floors.json`)

| name | cwd | command | env add | timeout | parse / completion marker | INFRA when |
|------|-----|---------|---------|---------|---------------------------|------------|
| `client_checks` | RepoRoot | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` (**never** `--drift-dry-run`) | (dotnet on PATH) | 120 s | **completion:** coverage line `coverage: …`; **pass** = count `^PASS `; **fail** = count `^FAIL `; require exit 0, fail=0, pass≥floor, coverage present | missing dotnet; no coverage line; unparseable |
| `stable_scripts` | RepoRoot | `powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Test-StableScripts.ps1` | — | 720 s | marker `==== SUMMARY pass=N fail=M ====`; N/M from that line | no SUMMARY; script crash |
| `dev_tools` | RepoRoot | `powershell -NoProfile -ExecutionPolicy Bypass -File tools\dev\Test-DevTools.ps1` | — | 60 s | same SUMMARY shape | no SUMMARY |
| `zola_workspace` | `hermes-plugins\zola_workspace` | `{venv}\python.exe -m unittest discover -s tests -t tests` | `PYTHONPATH`=hermes-agent root | 360 s | marker `Ran N tests in …` **and** `OK` or `FAILED (…)`; N from Ran | no Ran/OK|FAILED; Ran 0 / `NO TESTS RAN` / exit 5; missing venv |
| `zola_memory` | `hermes-plugins\zola_memory` | discover `-s tests -t .` | same | 60 s | same | same |
| `zola_tools` | `hermes-plugins\zola_tools` | discover `-s tests -t .` | same | 60 s | same | same |
| `zola_tts` | `hermes-plugins\zola_tts` | discover `-s tests -t .` | same | 60 s | same | same |
| `zola_phone` | `hermes-plugins\zola_phone` | discover `-s tests -t .` | same; `needs_zola_closed=true` | 120 s | same; if Zola running → **skip run**, INFRA close-Zola | Zola up; mutex held; no marker |
| `kotlin_unit` | `android-companion` | `gradlew.bat testDebugUnitTest --offline --rerun` (task option) | `JAVA_HOME`=JBR; `ANDROID_HOME`=SDK | 240 s | fresh JUnit XML under `app\build\test-results\testDebugUnitTest\TEST-*.xml` (all mtimes ≥ run start); sum tests/failures/errors/skipped; Gradle SUCCESS | missing JBR/SDK; UP-TO-DATE without fresh XML; stale XML |
| `assemble_debug` | `android-companion` | `gradlew.bat assembleDebug --offline` (**only with `-Promote`**) | same | 120 s | `BUILD SUCCESSFUL` | missing SDK/JBR; BUILD FAILED |
| `gate_self` | RepoRoot | `powershell … -File tools\test-gate\Test-TestGate.ps1` | — | 120 s | SUMMARY from self-test runner | self-test fail → overall FAIL |

**Pinned `-s`/`-t`:** workspace `-s tests -t tests`; memory/tools/tts/phone `-s tests -t .`.

**Timeouts** = max(60 s, 3× Phase 1 wall): Checks 120; stable 720; dev 60; workspace 360; memory 60; tools 60; tts 60; phone 120; kotlin 240; assemble 120; self 120.

**`assembleDebug` measured (Phase 2):** `android-companion\gradlew.bat assembleDebug --offline` with JBR + SDK → **BUILD SUCCESSFUL in ~5.3 s**, exit 0 (`--offline` works).

### F. Classification

- **PASS:** exit success, completion marker present, counts parsed, failures=0, passed≥floor, skips ⊆ allowed_skips by **test id+reason**, not zero tests.
- **FAIL:** test failure/error, below floor, unexpected skip, zero tests / `NO TESTS RAN` / exit 5 with Ran 0.
- **INFRA:** missing tool/path, timeout, crash before marker, unparseable, suite/floor mismatch (whole run), phone while Zola/mutex held, stale Kotlin XML, missing coverage/SUMMARY/Ran line even if a pass count looks right.
- **Overall PASS** only if every suite PASS **and** tree clean **and** before/after commit record identical. Exit: 0 PASS, 1 any FAIL, 2 INFRA only, 3 all PASS but PARTIAL or DIRTY.

### G. Commit and environment record

Before and after: HEAD SHA, branch, porcelain tracked+untracked. HEAD or change-set drift → cannot overall PASS. DIRTY reported when porcelain non-empty. Per suite: interpreter/SDK path+version (Python, dotnet, JDK, Android SDK); hermes-agent HEAD + clean/dirty.

### H. Output

- Fixed-width table: suite, result, passed/failed/skipped, floor, seconds, reason.
- UTF-8 no BOM JSON under `%TEMP%\zola-test-gate\` + raw per-suite logs. Nothing in the repo.

### I. `floors.json`

Per suite: `min_passed`, `allowed_skips` (list of `{id, reason}`), `needs_zola_closed`. Starting floors from Phase 1 / tip: Checks 322, stable 54, dev 16, workspace 582, memory 162, tools 44, tts 9, phone 71, kotlin 98, gate_self = self-test count once known. G-COVERAGE exact match. `-UpdateFloors` per G-FLOORS.

### J. Timeout cleanup (G-TIMEOUT)

Own each suite under a Windows Job Object (or tracked root PID + descendants). On timeout: kill job/tree, keep logs, confirm no remaining PIDs from that tree before next suite. Never touch processes the gate did not start.

### K. Kotlin G-FRESH choice

**Use `testDebugUnitTest --offline --rerun`** (Gradle 8.13 task option; confirmed on `help --task testDebugUnitTest`). Prefer `--rerun` over `--rerun-tasks` so dependencies need not rebuild. Also **delete** `app\build\test-results\testDebugUnitTest\` immediately before the run so stale XML cannot satisfy the marker. After run: every `TEST-*.xml` must exist and `LastWriteTimeUtc >= runStart`. Missing/stale → INFRA.

`assembleDebug --offline` kept for `-Promote` only (measured OK).

### L. Explicit environment (G-CONTROLLED-ENV)

Start from inherited env; **remove** `PYTHONPATH`, `PYTHONHOME`, `VIRTUAL_ENV`, `PIP_*`, `HERMES_HOME`. Then set only from recorded constants (not inherited values):

| Suite | Set |
|-------|-----|
| plugin python | `PYTHONPATH` = `C:\Users\test\Dev\hermes-agent`; command uses `…\hermes-agent\.venv\Scripts\python.exe` |
| kotlin / assemble | `JAVA_HOME` = `C:\Program Files\Android\Android Studio\jbr`; `ANDROID_HOME` = `%LOCALAPPDATA%\Android\Sdk` |
| others | no extras beyond cleared set |

If a required path does not exist → that suite **INFRA**. Record paths + versions in the JSON result.

### M. Checks rules

Never pass `--drift-dry-run`. PASS requires: `^PASS` count ≥ floor, zero `^FAIL` lines, exit 0, **and** coverage line present.

### N. Gate self-tests (`Test-TestGate.ps1`, fake suites only)

As in prompt §7, plus: Zola-running detector forces phone INFRA without running phone; completion-marker missing → INFRA; Ran 0 / NO TESTS RAN / exit 5 → not PASS; `--rerun` freshness (stale XML cannot PASS); WaitOne absence is not a self-test of prod Zola — detector OpenExisting-only.

### O. README

How to run, PASS/FAIL/INFRA/PARTIAL/DIRTY, what to do on INFRA (close Zola for phone, install SDK, etc.).

### P. Files to add (Phase 3)

`tools/test-gate/Run-TestGate.ps1`, `Suites.psd1` (or `.json`), `floors.json`, `Test-TestGate.ps1`, `README.md`, progress doc. Phase 2 also approves test-only edits: `Test-DevTools.ps1` (WaitOne→OpenExisting/probe); and **if Brian approves** the two phone test env lines (`8765`).

---

**Phase 2 STOP.** Awaiting Claude review and Brian’s decisions on (1) phone `ZOLA_PHONE_LISTEN_PORT=8765` change before any Zola-closed run, and (2) DevTools WaitOne fix.

---

## Phase 3 — Implement

### Brian’s decisions (recorded)

Brian approved both test-only G-NO-LIVE changes: isolation tests use `ZOLA_PHONE_LISTEN_PORT=8765` (with comment + no-TCP assertion), and DevTools uses OpenExisting only (no WaitOne). Zola detection is OpenExisting on `Local\ZolaClient` or `Local\ZolaPhone` (access denied = running), checked immediately before the phone suite.

### Self-tests

`Test-TestGate.ps1`: **18 PASS / 0 FAIL** (also as `gate_self` in the full run).

### Gate run (Zola running, uncommitted tree)

Result JSON: `C:\Users\test\AppData\Local\Temp\zola-test-gate\20261113-131934\result.json`

| SUITE | RESULT | PASS | FAIL | SKIP | FLOOR | SEC | REASON |
|-------|--------|------|------|------|-------|-----|--------|
| client_checks | PASS | 322 | 0 | 0 | 322 | 18.821 | |
| stable_scripts | PASS | 54 | 0 | 0 | 54 | 221.582 | |
| dev_tools | PASS | 16 | 0 | 0 | 16 | 3.18 | |
| zola_workspace | PASS | 582 | 0 | 0 | 582 | 110.382 | |
| zola_memory | PASS | 162 | 0 | 0 | 162 | 8.177 | |
| zola_tools | PASS | 44 | 0 | 0 | 44 | 0.353 | |
| zola_tts | PASS | 9 | 0 | 0 | 9 | 0.402 | |
| zola_phone | INFRA | 0 | 0 | 0 | 71 | 0.005 | stable is running; close Zola for a clean run |
| kotlin_unit | PASS | 98 | 0 | 0 | 98 | 14.676 | |
| gate_self | PASS | 18 | 0 | 0 | 18 | 0.865 | |

**OVERALL INFRA, exit 2** — phone INFRA while Zola is up; tree also DIRTY (uncommitted). Exit 2 because INFRA is present (DIRTY alone would be exit 3).

### Untracked / dirty after Phase 3

Only intentional track files (no suite leftovers; no new ignore rules):

```
 M hermes-plugins/zola_phone/tests/test_p10_intake.py
 M tools/dev/Test-DevTools.ps1
?? tools/test-gate/
?? zola-architecture/lore/prompts/progress/PROC1-GATE_Progress.md
```

### Diff

`C:\Users\test\Dev\zola-spikes\prompts\PROC1-GATE_Phase3.diff` (UTF-8; checked against `git status --porcelain`).

---

**Phase 3 STOP.** Awaiting review.

---

## Phase 4 — Defect fixes

### Fixes landed

- Phone listen helper checks process **tree** (launcher + descendants); control test binds on `127.0.0.1` via venv `PYTHON`; netstat unavailable stays failure.
- Skip identity: unittest `-v` + `test_id ... skipped 'reason'`; Kotlin `<skipped>` from fresh XML; compare id+reason to `allowed_skips`; last `Ran N tests` match; `OK (skipped=N)` parsed.
- Kotlin: fresh XML + Gradle exited = marker (no BUILD SUCCESSFUL); XML failures → FAIL; Gradle fail with no fresh XML → INFRA. `assembleDebug` unchanged (PromoteOnly).
- Job object: CREATE_SUSPENDED → AssignProcessToJobObject → ResumeThread; breakaway with nested-job fallback; timeout terminates job; leftovers → INFRA. Parent-PID walk removed. Gradle `--no-daemon`.
- Self-tests E2E via `-SuiteFile`/`-FloorsFile`/`-RepoRoot` temp git repo (exit 0/1/2/3, mid-run drift, skip mismatch, timeout grandchild cleanup, UpdateFloors rules, PYTHONPATH clear, phone held).
- `needs_zola_closed` authority only in `Suites.psd1`; floors keep `min_passed` + `allowed_skips`. Phone INFRA reason names stable Zola vs zola-phone. Versions: dotnet / JBR java / Gradle / Python.

### Self-tests

`Test-TestGate.ps1`: **30 PASS / 0 FAIL** (`gate_self` floor = 30).

### `--no-daemon` time

| | Phase 3 (daemon) | Phase 4 (`--no-daemon`) |
|--|------------------|-------------------------|
| kotlin_unit | 14.676 s | 34.893 s |

Delta ≈ **+20.2 s** (~2.4×) for kotlin on this machine; assemble not in default run (PromoteOnly).

### Gate run (Zola running, uncommitted tree)

Result JSON: `C:\Users\test\AppData\Local\Temp\zola-test-gate\20261113-135935\result.json`

| SUITE | RESULT | PASS | FAIL | SKIP | FLOOR | SEC | REASON |
|-------|--------|------|------|------|-------|-----|--------|
| client_checks | PASS | 322 | 0 | 0 | 322 | 17.812 | |
| stable_scripts | PASS | 54 | 0 | 0 | 54 | 184.379 | |
| dev_tools | PASS | 16 | 0 | 0 | 16 | 3.885 | |
| zola_workspace | PASS | 582 | 0 | 0 | 582 | 95.843 | |
| zola_memory | PASS | 162 | 0 | 0 | 162 | 9.505 | |
| zola_tools | PASS | 44 | 0 | 0 | 44 | 0.326 | |
| zola_tts | PASS | 9 | 0 | 0 | 9 | 0.372 | |
| zola_phone | INFRA | 0 | 0 | 0 | 72 | 0.018 | stable Zola is running; close Zola for a clean run |
| kotlin_unit | PASS | 98 | 0 | 0 | 98 | 34.893 | |
| gate_self | PASS | 30 | 0 | 0 | 30 | 37.27 | |

**OVERALL INFRA, exit 2** — phone held while Zola is up (expected; Zola-closed phone is Phase 5). Tree DIRTY (uncommitted). Versions recorded: dotnet 9.0.318, Gradle 8.13, Python 3.12.14 (JBR java string fixed post-run for next invoke).

### Diff

`C:\Users\test\Dev\zola-spikes\prompts\PROC1-GATE_Phase4.diff`

---

**Phase 4 STOP.** Do not run phone with Zola closed yet (Phase 5).

---

## Phase 4b — Review fixes

### Fixes

- Unittest skip parse: Python 3.12 `-v` dotted id in parentheses; docstring line before `... skipped`; real-venv self-test; allowed id+reason PASS / wrong id FAIL; skip count ≠ identities → FAIL.
- `_process_tree_pids` fail-closed (no root-only fallback on query failure).
- Vacuous detector tests replaced by E2E `-ZolaRunningProbe` (false then true); marker proves phone did not run.
- `TEST OVERRIDES IN USE` + JSON `overrides` when `-SuiteFile`/`-FloorsFile`/`-ZolaRunningProbe`; default gate run has all false.
- UpdateFloors: refuse when any suite not PASS; raise preserves `allowed_skips` (manual JSON write).
- Phone floor unchanged at 72 (confirm in Phase 5). `gate_self` floor = 33.

### Self-tests

**33 PASS / 0 FAIL**

### Gate run (Zola up)

Result: `C:\Users\test\AppData\Local\Temp\zola-test-gate\20261113-141631\result.json`  
No `TEST OVERRIDES IN USE`. `overrides` all false.

| SUITE | RESULT | PASS | FLOOR | SEC | REASON |
|-------|--------|------|-------|-----|--------|
| client_checks | PASS | 322 | 322 | 18.1 | |
| stable_scripts | PASS | 54 | 54 | 166.6 | |
| dev_tools | PASS | 16 | 16 | 3.7 | |
| zola_workspace | PASS | 582 | 582 | 87.8 | |
| zola_memory | PASS | 162 | 162 | 7.3 | |
| zola_tools | PASS | 44 | 44 | 0.3 | |
| zola_tts | PASS | 9 | 9 | 0.4 | |
| zola_phone | INFRA | 0 | 72 | 0.0 | stable Zola is running |
| kotlin_unit | PASS | 98 | 98 | 30.9 | |
| gate_self | PASS | 33 | 33 | 42.6 | |

**OVERALL INFRA exit 2** (phone held; expected).

### Diff

`C:\Users\test\Dev\zola-spikes\prompts\PROC1-GATE_Phase4b.diff`

---

**Phase 4b STOP.** Before Phase 5.

---

## Phase 5 — Clean run and isolation proof

### Zola closed / restarted (Brian)

| Event | Time (local) |
|-------|----------------|
| Brian reported closed | 2026-11-13 ~14:58 (agent confirmed `2026-11-13T14:58:19-08:00`) |
| Detector after close | `Test-ZolaRunningForGate=False`; `Local\ZolaClient` free; `Local\ZolaPhone` free; no `Zola.Client` / `-m zola_phone` |
| Gate `-Promote` window | start `14:58:29` → end `15:06:21` |
| Brian restart | process start `2026-11-13T15:07:31-08:00` (pid 23628); agent confirmed `15:07:57` — detector held (`Local\ZolaClient` + `Local\ZolaPhone`) |

(Attempted hash maps while Zola was still up at 14:25 hit locked DB/log files; authoritative before maps were retaken after close.)

### Isolation hash maps (separate from Phase 1 source audit)

Maps under `%TEMP%\proc1-gate-maps\`. Full-byte SHA-256 via `Get-TreeHashMap` / `Compare-TreeHashMaps` (`tools/dev/DevCommon.psm1`). `Test-DevIsolation.ps1 -Mode AfterClose` on each pair.

| Root | Before files | After files | Diff | Isolation check |
|------|-------------:|------------:|------|-----------------|
| `%LOCALAPPDATA%\hermes\profiles\zola` | 914 | 914 | **0** | `after-close hashes match` exit 0 |
| `%LOCALAPPDATA%\ZolaClient` | 27 | 27 | **0** | `after-close hashes match` exit 0 |

**Verdict:** gate `-Promote` run did not change live profile or `ZolaClient` file hashes.

### Gate run (`-Promote`, Zola closed, no overrides)

Result JSON: `C:\Users\test\AppData\Local\Temp\zola-test-gate\20261113-145829\result.json`  
No `TEST OVERRIDES IN USE`. JSON `overrides`: all `false`.

| SUITE | RESULT | PASS | FAIL | SKIP | FLOOR | SEC |
|-------|--------|------|------|------|-------|-----|
| client_checks | PASS | 322 | 0 | 0 | 322 | 18.8 |
| stable_scripts | PASS | 54 | 0 | 0 | 54 | 201.6 |
| dev_tools | PASS | 16 | 0 | 0 | 16 | 3.2 |
| zola_workspace | PASS | 582 | 0 | 0 | 582 | 108.2 |
| zola_memory | PASS | 162 | 0 | 0 | 162 | 12.5 |
| zola_tools | PASS | 44 | 0 | 0 | 44 | 0.4 |
| zola_tts | PASS | 9 | 0 | 0 | 9 | 0.4 |
| zola_phone | PASS | **72** | 0 | 0 | 72 | 32.5 |
| kotlin_unit | PASS | 98 | 0 | 0 | 98 | 33.0 |
| assemble_debug | PASS | 1 | 0 | 0 | 1 | 16.4 |
| gate_self | PASS | 33 | 0 | 0 | 33 | 42.4 |

**OVERALL DIRTY, exit 3** (working tree dirty — uncommitted gate work). Every suite PASS including `zola_phone` and `assemble_debug`.

### Phone named tests (from suite log; `Ran 72` / `OK`)

| Test | Outcome |
|------|---------|
| `test_isolation_on_the_real_startup_path` | **ok** |
| `test_f4_second_process_refuses_the_pipe_and_mutex` | **ok** (first process still alive after second exits 2) |
| `test_listening_helper_finds_launcher_child_listener` | **ok** |

Phone count **72** = floor. After the suite: no `-m zola_phone` / gate-related python leftovers; `Local\ZolaPhone` free.

### Item 6 — experience check (Brian)

Brian ran the gate in a plain PowerShell window with Zola running (no `-Promote`):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\test\Dev\zola-windows-proc1-gate\tools\test-gate\Run-TestGate.ps1
```

Result JSON: `C:\Users\test\AppData\Local\Temp\zola-test-gate\20261113-150838\result.json`  
Import-Module unapproved-verb WARNING only (expected). No `TEST OVERRIDES IN USE`.

| SUITE | RESULT | PASS | FLOOR | SEC | REASON |
|-------|--------|------|-------|-----|--------|
| client_checks … gate_self (except phone) | PASS | (floors met) | … | … | |
| zola_phone | INFRA | 0 | 72 | 0.006 | stable Zola is running; close Zola for a clean run |
| assemble_debug | *(not run — PromoteOnly, no `-Promote`)* | | | | |

**OVERALL INFRA exit=2** — matches expectation with Zola up.

---

**Phase 5 STOP.**

---

## Phase 6 — Commit and merge

### Pre-merge polish (before commit)

- `Import-Module … -DisableNameChecking` (no unapproved-verb WARNING).
- Dirty tree called out on OVERALL even when primary result is INFRA/FAIL: `… - uncommitted changes in the working tree`.
- Self-tests **34 PASS / 0 FAIL**; `gate_self` floor = **34**; phone floor **72**.

### Commit

| Item | Value |
|------|-------|
| Branch | `proc1-gate` |
| SHA | `ceb0476f31c5a12b82bcdcbc26fb7bb2d8f6744f` |
| Message | Add PROC1-GATE one-command test gate with floors and isolation proofs. |
| Files (9) | `test_p10_intake.py`, `Test-DevTools.ps1`, `tools/test-gate/*` (6), `PROC1-GATE_Progress.md` |

### Zola closed (Brian)

| Event | Time |
|-------|------|
| Closed (confirmed) | `2026-11-13T15:20:51-08:00` — detector free; no `Zola.Client` |
| Restart | *(awaiting Brian)* |

### Before / after hash maps (4 roots)

Maps: `%TEMP%\proc1-gate-maps-p6\`. Clean before maps after close; after maps after both `-Promote` runs.

| Root | Before | After | Diff |
|------|-------:|------:|------|
| `hermes\profiles\zola` | 914 | 914 | **0** |
| `ZolaClient` | 27 | 27 | **0** |
| `hermes-dev\profiles\zola-dev` | 499 | 499 | **0** |
| `ZolaClient-dev` | 6 | 6 | **0** |

### Gate on committed tip (`-Promote`, Zola closed)

Result: `C:\Users\test\AppData\Local\Temp\zola-test-gate\20261113-152101\result.json`  
**OVERALL PASS exit=0**. Commit before=after `ceb0476…` dirty=False. Overrides all false. Phone 72; assemble_debug PASS; gate_self 34.

### Merge

Fast-forward `main` ← `proc1-gate` in live checkout `C:\Users\test\Dev\zola-windows` (same 9 files only).

### Gate on merged tip (`-Promote`, Zola still closed)

Result: `C:\Users\test\AppData\Local\Temp\zola-test-gate\20261113-152805\result.json`  
**OVERALL PASS exit=0**. Commit before=after `ceb0476…` dirty=False. Overrides all false.

### Tag

Annotated tag **`proc1-gate`** → `ceb0476f31c5a12b82bcdcbc26fb7bb2d8f6744f`. **No promotion.**

---

**Phase 6 STOP** (awaiting Brian restart time to record).
