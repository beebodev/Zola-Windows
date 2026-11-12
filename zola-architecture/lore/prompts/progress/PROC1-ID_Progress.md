# PROC1-ID Progress

**Prompt:** `PROC1-ID_Prompt_v1.1.md`  
**Prompt SHA-256:** `8abcbf22682a99922e317d38a36b0790b63fca93557e21f01c62abd6fc9565bd` (verified match)  
**Plan:** `PROC1_BUILD_PLAN.md` v1.2 â€” Track PROC1-ID  
**Base:** `origin/main` @ `54a477f03ca9d27ef5b779c1ba1b72292fdad8bf`

## Locations

| Item | Value |
|------|-------|
| Live checkout | `C:\Users\test\Dev\zola-windows` (read-only until Phase 8) |
| Track worktree | `C:\Users\test\Dev\zola-windows-proc1-id` |
| Work branch | `proc1-id` |
| Stable | `C:\Users\test\Zola\stable\fix-s51f\` |
| Active backup | `fix-s51f-20261110-091644` |
| hermes-agent pin | `345cd2b057a452236de401d3534b8502a7465e8d` |

## Phase table

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Setup, baselines, facts | DONE | STOP |
| 2 Design proposal | DONE | STOP â€” awaiting Brian/Claude approval |
| 3 Implement | DONE | STOP â€” diff + suite counts |
| 4 Review fixes | DONE | Phase4 + Phase4c |
| 5 Drift dry run | DONE | STOP â€” packages DRIFT |
| 6 Pre-merge smoke | DONE | SM-ID + 6b diagnose |
| 7 Commit and merge | | |
| 8 Live checkout sync | | |
| 9 Promotion decision | | |
| 10 Closeout | | |

## Phase 1 â€” Setup, baselines, facts

### 1. Prompt / live / tag / hermes / stable running

| Item | Value |
|------|-------|
| Prompt SHA-256 | `8abcbf22682a99922e317d38a36b0790b63fca93557e21f01c62abd6fc9565bd` â€” MATCH |
| Live branch | `main` |
| Live HEAD | `54a477f03ca9d27ef5b779c1ba1b72292fdad8bf` |
| Live status | clean; `main` == `origin/main` |
| Tag `proc1-stable` | annotated; peels to `5db407f805f99898d83a1e9221532d1d158c99a8` (on origin) |
| hermes-agent | detached HEAD at pin; `git status --porcelain` empty |
| Stable client | **running** pid **18192**, path `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe`, started 2026-11-10 10:27:04 |

### 2. Worktree

Created: `git worktree add -b proc1-id C:\Users\test\Dev\zola-windows-proc1-id origin/main`.  
Worktree HEAD `54a477fâ€¦`. Live checkout unchanged after create (`main` clean @ same SHA).  
Note: leftover folder `C:\Users\test\Dev\zola-windows-proc1-stable` still on disk from prior track (Cursor lock); not used.

### 3. Baselines (worktree; Zola running from stable)

| Suite | Command | Result | Floor |
|-------|---------|--------|-------|
| Client build | `dotnet build windows-client\Zola.Client\Zola.Client.csproj -c Release` | succeeded (0 errors, 2 nullability warnings) | â€” |
| Checks | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` | **271 PASS / 0 FAIL** | 271 |
| zola_workspace | venv `python -m unittest discover -s tests -t tests` (`PYTHONPATH`=hermes-agent) | **582 OK** (166.754s) | 582 |
| zola_memory | discover `-s tests -t .` | **162 OK** | 162 |
| zola_tools | discover `-s tests -t .` | **44 OK** | 44 |
| zola_tts | discover `-s tests -t .` | **8 OK** | 8 |
| zola_phone | discover `-s tests -t .` | **71 ran, 2 FAIL** (expected with Zola running): `test_f4_second_process_refuses_the_pipe_and_mutex`, `test_isolation_on_the_real_startup_path` | 71 |
| Kotlin | `android-companion\gradlew.bat testDebugUnitTest assembleDebug --offline` (`JAVA_HOME`=Android Studio JBR, `ANDROID_HOME`=`%LOCALAPPDATA%\Android\Sdk`) | **98** unit, 0 fail/error/skip; assembleDebug OK | 98 |
| Stable scripts | `tools\stable\Test-StableScripts.ps1` | **44 PASS / 1 FAIL** â€” see discrepancy below | 45 |

**Discrepancy (report only):** `prestable-head-differs-warning` FAIL (`text`). While everyday Zola is running, `Resolve-OutgoingForPrepare` prefers `Get-ObservedPreStableLaunch` over `PROC1_TEST_PRESTABLE_JSON`, so synthetic Prepare records the live process (parent `Explorer.EXE`, checkout HEAD = live/`RepoRoot` `54a477fâ€¦`). Restore then sees recorded head == `-LiveCheckout` HEAD â†’ no `WARNING: live checkout HEAD now differs`, and `Fallback launch command` is the parent command line (`C:\WINDOWS\Explorer.EXE`), not the env JSON `dotnet runâ€¦`. Floor 45 assumed Zola closed (env JSON path). Not fixed in Phase 1.

### 4. Startup facts

**Before `OnLaunched` first line**

- WinUI generated entry constructs `App` and calls `App()` (`App.xaml.cs:15â€“18`): only `InitializeComponent()` â€” loads `App.xaml` resources (`XamlControlsResources`, `Themes/ZolaTokens.xaml`). No file write under `%LOCALAPPDATA%\ZolaClient\`, no profile path open, no process start.
- `App` fields: `_phoneSecret = ""` and null refs only (`App.xaml.cs:9â€“13`). No static constructor on `App`.
- `MainWindow` is not constructed until `OnLaunched`. No `MainWindow` static ctor that runs earlier for this path.
- XAML-generated `Main` is the WinUI/SDK host entry (no hand-written `Program.cs`); it bootstraps the XAML application and then `OnLaunched`.

**`OnLaunched` order today** (`App.xaml.cs:21â€“44`)

1. `DumpPruner.PruneOnStartup()` â€” first statement  
2. `new HermesProcessManager()`  
3. generate `_phoneSecret`; assign `PhoneLaunchSecret`  
4. `new WatcherProcess(ProfileDirectory)`  
5. `new PhoneProcess(ProfileDirectory, â€¦)`  
6. `new MainWindow(â€¦)`  
7. subscribe `Closed` â†’ stop phone/watcher, `Shutdown` backend  
8. `_window.Activate()`  
9. `_watcher.Start()`; `_phone.Start()`  
10. `_ = StartBackendAsync()` (`StartAsync` on backend)

**First opens under `%LOCALAPPDATA%\ZolaClient\`**

| Site | When | Path / action |
|------|------|----------------|
| `DumpPruner.PruneOnStartup` `DumpPruner.cs:10â€“33` | First line of `OnLaunched` | `%LOCALAPPDATA%\ZolaClient\dumps` â€” enumerate/delete expired files (no create if absent) |
| `SupervisionLog.Write` `SupervisionLog.cs:56â€“64` | First supervisor event (watcher/phone/serve spawn) | `â€¦\ZolaClient\logs\supervisor.log` â€” `CreateDirectory` + append |
| `ServeStderrLog` `ServeStderrLog.cs:31+` | Supervised Python stdout/stderr | `â€¦\ZolaClient\logs\` (proc output files) |
| Other later | After window/voice/chat | `voice-timeline`, code-read logs, presence, etc. under `ZolaClient\` |

`HermesProcessManager` ctor (`HermesProcessManager.cs:40â€“44`) sets `ProfileDirectory` to `%LOCALAPPDATA%\hermes\profiles\zola` (not ZolaClient) before watcher/phone start.

### 5. Identity facts

| Item | Fact |
|------|------|
| Stable `Zola.Client.dll` ProductVersion | `1.0.0+74941cf72f1e00bb979a9f29ec13aa03fa6b4666` (`FileVersion` `1.0.0.0`) â€” git commit suffix present |
| csproj | No explicit `Version` / `InformationalVersion` / `IncludeSourceRevisionInInformationalVersion`; SDK default embeds `+<SourceRevisionId>` |
| Own folder | `AppContext.BaseDirectory` used today (`HermesLaunchResolver.cs:76`, `PresenceView.cs:531`). Stable shortcut â†’ exe directory under `stable\fix-s51f\`. `dotnet run` â†’ build output under `bin\â€¦\`. |

### 6. Notice facts (S51F lost-request)

| Item | Fact |
|------|------|
| Text constant | `SupervisionConstants.LostTurnNoticeText` (`SupervisionConstants.cs:25`) |
| Decision | `LostTurnNotice.Decide` (`LostTurnNotice.cs`) |
| UI apply | `MainWindow.TryApplyLostTurnNotice` â†’ `AddBubble("System", LostTurnNoticeText, â€¦)` (`MainWindow.xaml.cs:1334â€“1368`) |
| Speak? | Conversation **System** bubble only â€” does not call TTS for this line |
| Before serve healthy? | Path is turn/supervision driven on an existing `MainWindow`; it is **not** a startup notice and assumes the window already exists. Separate dock `StatusText` / `UpdateNoticeVisibility` (`MainWindow.xaml.cs:3168+`) is the non-blocking status strip (also needs the window). |

### 7. Pop-up facts

- No `MessageBoxW` (or other modal) in the client today. Existing `user32` P/Invokes are cursor/`ScreenToClient` only (`MainWindow.xaml.cs:3285â€“3289`).
- A refusing instance can P/Invoke `MessageBoxW` before any `Window` exists, then exit via `Environment.Exit` / process return without constructing `MainWindow` or starting Hermes â€” **not implemented yet**; available Win32 approach for Phase 2.

### 8. Drift facts (`StableCommon.psm1`)

**`Get-HermesStateDigest`** (`StableCommon.psm1:837â€“850`)

| Field | Command / join | Digest |
|-------|----------------|--------|
| `head` | `git -C $HermesRoot rev-parse HEAD 2>$null` | raw string (not digested) |
| `local_edit_digest` | `git -C $HermesRoot status --porcelain 2>$null` then `-join "`n"` | `Get-DigestOfText` |
| `pip_freeze_digest` | if venv python exists: `& $py -m pip freeze 2>$null` then `-join "`n"`; else `''` | `Get-DigestOfText` |

**`Get-DigestOfText`** (`826â€“834`): UTF-8 bytes of the string as-is (no forced trailing newline beyond what `-join` produced) â†’ SHA-256 â†’ lowercase hex without dashes.

**On `git` / `pip` failure today:** `2>$null` hides stderr; failed/empty capture still hashes (empty string digest looks like â€œno editsâ€). Exit codes are not checked.

**Plugin hashes:** per-file `Get-FileSha256Hex` = `Get-FileHash -Algorithm SHA256` lowercase (`107â€“109`). Maps: `Get-PromotionsPluginHashMap` / `Get-LivePluginHashMap` (`243â€“279`) with `Compare-PluginSets` (`282+`).

**Timings on this PC (read-only, once):**

| Command | Elapsed |
|---------|---------|
| `git -C hermes-agent status --porcelain` | **153 ms** |
| `hermes-agent\.venv\Scripts\python.exe -m pip freeze` | **1892 ms** |

## Phase 1 complete

Phase 1 STOP cleared: reviewed and accepted; Phase 2 go-ahead with W4 isolation + AddBubble drift placement.

## Phase 2 â€” Design proposal (no edits)

**Brian go-ahead (verbatim, 2026-11-10):** Phase 1 reviewed and accepted; proceed to Phase 2 with two additions â€” (1) fix script-test isolation bug (W4) so test-mode Prepare never looks at real processes; inject prestable launch via parameter; refuse TestMode without it; add test that injected launch wins while a real `Zola.Client.exe` is running; audit other test-mode paths; restore floor â‰¥45 / 0 failures with Zola running; (2) drift notice via existing `AddBubble("System", â€¦)` on UI thread after activate; confirm no serve/Hermes/speech dependency; if window closes before drift finishes, post nothing and show no error.

### 1. Lock (W2)

| Item | Proposal |
|------|----------|
| Mutex name | `Local\ZolaClient` â€” one name for every build (stable and `dotnet run` / dev refuse each other) |
| Scope | **`Local\` = one Windows sign-in session**, not machine-wide. Plan wording "machine-wide" is **corrected to "per Windows session"**. D7 = one Zola in Brian's desktop session. |
| Cross-session | Another Windows user has a separate `%LOCALAPPDATA%` (separate profile, client data, and `Local\` mutex namespace). Nothing in Zola today uses a `Global\` single-instance lock; phone/watcher already use `Local\`. Shared machine paths (e.g. hermes-agent checkout) are not a second-session UI lock. **No change to per-session scope.** |
| Where taken | **First statement of `OnLaunched`**, before `DumpPruner.PruneOnStartup()` (Phase 1: DumpPruner is the first disk touch under `ZolaClient\`). Not earlier: `App()` only `InitializeComponent()` (no data paths). |
| Abandoned mutex | If the previous holder crashed, `WaitOne` / create-with-ownership treats the mutex as **abandoned â†’ acquire and continue** (do not refuse). |
| Lifetime | Hold for the process life; release/dispose on clean exit (`Closed` / process teardown). OS releases on crash. |

### 2. Status file (W2)

| Item | Proposal |
|------|----------|
| Path | `%LOCALAPPDATA%\Zola\run\instance.json` (outside `%LOCALAPPDATA%\ZolaClient\` and outside the Hermes profile â€” ready for PROC1-DEV) |
| Contents (no secrets) | `role`, `tag` (nullable for dev), `pid`, `exe` (full path), `started_at` (ISO-8601 offset) |
| Write | After lock acquired, **atomic** write (temp + replace). |
| Delete | On clean exit. |
| Stale | If mutex is free, **ignore** any leftover file (crash residue); do not refuse from the file alone. |

**For Brian's approval:** status-file location `%LOCALAPPDATA%\Zola\run\instance.json`.

### 3. Refusal (W2)

| Case | Title | Text |
|------|-------|------|
| (a) Readable status | `Zola` | `Zola (stable, {tag}) is already running.` â€” if role is `dev` or tag missing: `Zola (dev) is already running.` |
| (b) No / unreadable status | `Zola` | `Another Zola is already running.` |

Mechanism: Win32 `MessageBoxW` (P/Invoke) before any window; one `Debug.WriteLine` / debug-output line with the same summary; `Environment.Exit(0)` (or non-zero refuse code â€” propose **exit 0** so shells don't look like a crash). **Nothing else runs** (G-BEFORE-DATA / G-NEVER-TOUCH-FIRST).

**For Brian's approval:** the two body strings above (title `Zola`).

### 4. Role (W1)

**`build-role.json`** (beside the exe, written by Switch into staging):

```json
{
  "role": "stable",
  "tag": "fix-s51f",
  "commit": "<full git sha of the promoted tag>",
  "manifest": "stable-manifest.json"
}
```

**Client decides `stable` iff:** file present beside `AppContext.BaseDirectory`, JSON parses, `role == "stable"`, and `commit` equals the git SHA embedded in the build (`FileVersionInfo.ProductVersion` after `+`, Phase 1: stable DLL already has `1.0.0+74941cfâ€¦`). **Otherwise `dev`**, with one log line naming why: `missing` | `unreadable` | `role` | `commit_mismatch` | `no_embedded_commit`.

Phase 1 found an embedded commit â€” **no alternate needed**. If embed were ever absent â†’ treat as `dev` and log `no_embedded_commit` (fail closed for "stable").

**Exposure:** one read-only `BuildRole` (or equivalent) resolved once at startup after the lock; only **W3** branches on `stable` in this track.

### 5. Drift (W3)

**Compared (stable only):** Hermes HEAD; Hermes local-edit digest; package (`pip freeze`) digest; installed plugin hashes (same comparison set as promotion). **`config.yaml` not compared.**

**One authority:** Switch records in `stable-manifest.json`:

- `plugin_compare_rules` â€” maps, structural excludes, named excludes (the script's own lists)
- `digest_algorithms` â€” e.g. `{ "hermes_local_edit": "v2-content", "pip_freeze": "v1-pip-freeze" }`

Client applies **only** rules/algorithms from the manifest. Unknown algorithm or missing rules â†’ **drift check not completed** (log reason; no notice).

**Digest v2 (`hermes_local_edit` = `v2-content`):** sorted entries from `git status --porcelain=v1 -z --untracked-files=all`; for each path, status code + SHA-256 of current file bytes (or token `deleted`). v1 porcelain-text hash is retired for new promotions. **`pip_freeze` stays `v1-pip-freeze`** (UTF-8 SHA-256 of joined freeze text, matching today's join rules once fail-closed).

**Fail closed:** nonzero exit, timeout, or missing `git`/`pip` â†’ that digest is **not completed**, never hash of empty output. In Switch, stop with the reason **before any live change**.

**C#:** same algorithms byte-for-byte vs `StableCommon.psm1` on a shared fixture (checked in tests).

**Scheduling:** after `_window.Activate()`, start drift work **off the UI thread**; **total time limit 10 seconds** (Phase 1: porcelain ~153 ms, pip freeze ~1892 ms; headroom for plugin hashing). Dev builds **do not** run the check.

**Notice placement (Brian addition):** use existing **`AddBubble("System", text, mine: false)`** (S51F lost-request path), marshalled with `Dispatch(() => â€¦)` onto the UI thread after the window is activated.

| Property | Confirmation |
|----------|----------------|
| Serve healthy? | **No dependency** â€” bubble is local UI only (`AddBubble` â†’ `Transcript`), same as S51F |
| Sent to Hermes? | **No** â€” no socket/chat send |
| Spoken? | **No** â€” not `noteSpoken` / TTS; System bubble only |
| Wording (Brian approval) | `Zola's installed parts have changed since this build was promoted.` |
| Once per launch | Yes |
| Decision site | One testable pure function: drift result â†’ `{ PostNotice: bool, Components: [â€¦] }`; UI posts only if `PostNotice` and window still live |

**If the window closes before the drift check finishes:** do not post; swallow/cancel; **no error UI and no exception dialog** (G-FAIL-OPEN-DRIFT).

Log line (fields only): components among `hermes_head`, `hermes_local_edits`, `packages`, `plugins` (+ plugin file count when plugins drift).

### 6. W4 script changes

- Switch writes `build-role.json` and updates manifest with `plugin_compare_rules` + `digest_algorithms` into staging **before** the move.
- Both role file and those manifest fields are **excluded from `client_build_hash` and staging recheck** (like the manifest today).
- All-or-nothing put-back covers them.
- Restore to an outgoing stable folder leaves that folder's role file as promoted.
- Digests: v2 local-edit + fail-closed git/pip in script and client.

### 6b. W4 script-test isolation (Brian addition)

**Bug:** `Resolve-OutgoingForPrepare` calls `Get-ObservedPreStableLaunch` (real `Win32_Process`) **before** falling back to `PROC1_TEST_PRESTABLE_JSON`, so a running stable Zola poisons synthetic Prepare (`Explorer.EXE` launch, head = live HEAD) and breaks `prestable-head-differs-warning`.

**Design:**

1. Add Prepare parameter **`-TestPreStableLaunch`** (object/hashtable: `launch_command`, `checkout`, `branch`, `head`, `client_exe`) â€” replaces env JSON as the sole TestMode source.
2. In **`-TestMode`**: **never** call `Get-ObservedPreStableLaunch`. Require `-TestPreStableLaunch` whenever outgoing would be `pre-stable`; if missing â†’ throw (`TestMode requires -TestPreStableLaunch`).
3. Non-TestMode: keep observing the real process as today.
4. **Also harden** `Assert-ZolaNotRunning` / `Get-ZolaRunningStatus`: in TestMode (Promote/Restore), **require** `-RunningZolaProbe`; if Probe is null â†’ throw (never fall through to real CIM / `Local\ZolaPhone` / `Local\ZolaWatcher`). Drills already skip the running check â€” unchanged.
5. Remove reliance on `PROC1_TEST_PRESTABLE_JSON` (or keep only as deprecated alias that feeds the same parameter in tests during transition â€” prefer parameter-only).
6. **New test** `testmode-prepare-ignores-real-zola`: with a real `Zola.Client.exe` allowed to be running (G-NO-RESTART: do not start/stop), TestMode Prepare + injected launch records **injected** `head` / `launch_command` on the prepare/backup outgoing â€” not the live exe / Explorer parent.
7. Restore floor: **â‰¥ 45 PASS, 0 FAIL**, with Zola running.

#### Test-mode isolation audit (what was checked)

| Path | Real process / mutex / live profile / Desktop-Programs? | Verdict |
|------|---------------------------------------------------------|---------|
| `Get-ObservedPreStableLaunch` via Prepare `Resolve-OutgoingForPrepare` | Real `Zola.Client` + parent command line; git HEAD of `-LiveCheckout` (default live checkout) | **BUG â€” must not run in TestMode** |
| `Get-ZolaRunningStatus` without Probe | Full CIM process scan + default `Local\ZolaPhone` / `Local\ZolaWatcher` | **Harden â€” TestMode must require Probe** |
| `Assert-ZolaNotRunning` on Promote Switch / non-drill Restore | Uses Probe when passed; if Probe omitted â†’ real scan | **Harden as above** |
| Restore **Drill** | Skips `Assert-ZolaNotRunning` (`-not $isDrill`) | OK (no process read) |
| Switch â†’ drill Restore invocation | Does not pass Probe; OK because drill skips check | OK |
| `Assert-TestModeSafeRoot` on StableRoot / ProfileRoot / DesktopDir / ProgramsDir | Refuses paths under live stable, live profile, real Desktop/Programs, live checkout, etc. | OK â€” tests pass scratch dirs |
| Test harness `Get-CommonPromoteArgs` | Scratch Profile/Desktop/Programs/Stable; `TestMode=$true` | OK |
| `Set-PrestableEnv` / `PROC1_TEST_PRESTABLE_JSON` | Only used when observation returns null â€” defeated when Zola runs | **Replace with `-TestPreStableLaunch`** |
| `refuse-held-mutex-detect` | Calls `Get-ZolaRunningStatus -MutexNames @(...)` **without Probe** â†’ still scans real processes; PASSes coincidentally if Zola is up | **Tighten test** to Probe/mutex-only so it asserts the test mutex, not a live client |
| `HermesRoot` in tests | Real `C:\Users\test\Dev\hermes-agent` (pin) for sqlite tool + digests | **Intentional read-only**; not the live profile tree |
| Live profile `%LOCALAPPDATA%\hermes\profiles\zola` | Not used as ProfileRoot in TestMode (scratch + safe-root assert) | OK |
| Real Desktop / Programs | Defaults blocked by TestMode safe-root; tests inject scratch | OK |
| `LiveCheckout` git reads in Restore prestable warning | Worktree/live git HEAD compare â€” not a process read | OK once outgoing head comes from injection |

### 7. Tests (one line each)

| Plan ID area | Test |
|--------------|------|
| Source order | `OnLaunched` lock before `DumpPruner`, `HermesProcessManager`, `WatcherProcess`, `PhoneProcess`, `MainWindow` |
| Second instance | Helper process + test mutex name + test status path; refuse text names holder from status |
| Abandoned mutex | Reclaimed (acquire, not refuse) |
| Stale status | Free mutex + leftover file â†’ ignore file, start |
| Refuse writes nothing | Scratch folders unchanged |
| Role | none â†’ dev; valid â†’ stable; commit mismatch â†’ dev; unreadable â†’ dev |
| Drift | no drift; each component alone; added + removed plugin file; missing rules / unknown algorithm â†’ not completed; time limit â†’ not completed; C# digests == PowerShell on same fixture |
| v2 digest | second edit to already-modified file changes digest; untracked content change changes it; fake git/pip nonzero + timeout â†’ not completed (never empty hash); Switch stops before live change |
| Notice | drift â†’ `AddBubble("System", â€¦)` exactly once; not speech; serve not healthy; "not completed" / "no drift" â†’ nothing; closed window before finish â†’ nothing / no error |
| W4 promotion | role file + rules written; excluded from hashes; put back on injected failure |
| W4 isolation | TestMode Prepare uses injected launch while real `Zola.Client.exe` is running; script suite â‰¥45 / 0 FAIL with Zola up |

## Phase 2 complete

Phase 2 STOP cleared. Brian (verbatim): "Go with Claude's versions". Claude's wording and isolation gaps adopted; plan "machine-wide" â†’ "per Windows session" recorded (plan file not edited).

## Phase 3 â€” Implement

### Approvals applied
- Refusal: Claude versions with "Close it before starting another."
- Drift: "Zola's installed parts have changed since this build was promoted ({components})." Labels: Hermes code / Python packages / plugins; log keeps keys + plugin file count.
- Status file: %LOCALAPPDATA%\Zola\run\instance.json
- Isolation: TestMode requires -RunningZolaProbe and -TestPreStableLaunch; mutex detect uses injected probe; new tests pass with real Zola running.

### Suite counts (Zola running pid 18192)

| Suite | Result |
|-------|--------|
| Client build | OK (0 errors) |
| Checks | **284 PASS / 0 FAIL** (271 prior + 13 identity) |
| Stable scripts | **49 PASS / 0 FAIL** (floor 45; Zola running) |
| zola_workspace | 582 OK |
| zola_memory | 162 OK |
| zola_tools | 44 OK |
| zola_tts | 8 OK |
| zola_phone | 71 ran, 2 FAIL expected (mutex) |
| Kotlin | 98 / 0 fail; assembleDebug OK |

Live checkout clean on main; hermes at pin.

**STOP â€” end of Phase 3.** Diff: C:\Users\test\Dev\zola-spikes\prompts\PROC1-ID_Phase3.diff.


## Phase 4 â€” Review fixes

Claude reviewed Phase3.diff. Applied exactly:

1. **Lock literally first** â€” OnLaunched first statement is SingleInstanceLock.TryAcquire; BuildRole.Resolve only after owned. Refusal path needs no role (reads holder status only). Acquire and status write are split; source-order check requires mutex acquire first.
2. **Persistent log** â€” SupervisionLog.WriteLine / IdentityLog â†’ %LOCALAPPDATA%\ZolaClient\logs\supervisor.log. Fields: identity role=â€¦ why=â€¦ tag=â€¦, identity status_write ok|failed reason=â€¦, drift completed=true components=none|<keys> [plugin_files=<n>], drift completed=false reason=â€¦. Refusing instance: Debug.WriteLine only; writes nothing. Check covers outcomes + refuse writes none.
3. **Status write canâ€™t crash startup** â€” TryWriteStatus catches; logs failed; keeps lock.
4. **Atomic write** â€” File.Move(tmp, path, overwrite: true).
5. **Release after children exit** â€” Quote: HermesProcessManager.Shutdown already Kill + WaitForExit(5000). SupervisedPython.KillChild (watcher/phone via StopDeliberate) previously did **not** wait; now Kill + WaitForExit(5000). If still alive: identity release_after_wait child=<phone|watcher|serve> alive=true, then release anyway. Closed-handler check: phone â†’ watcher â†’ serve â†’ lock Dispose.
6. **One Hermes root** â€” drift uses HermesLaunchResolver.TryResolve; no hard-coded C:\Users\test\Dev\hermes-agent. Unresolved â†’ drift completed=false reason=hermes_root.

### Suite counts (Zola pid 18192)

| Suite | Result |
|-------|--------|
| Client build | OK (0 errors) |
| Checks | **288 PASS / 0 FAIL** (identity 17/17) |
| Stable scripts | **49 PASS / 0 FAIL** |
| zola_workspace | 582 OK |
| zola_memory | 162 OK |
| zola_tools | 44 OK |
| zola_tts | 8 OK |
| zola_phone | 71 ran, 2 FAIL expected (mutex) |
| Kotlin | **98** / 0 fail; assembleDebug OK |

Live checkout clean on main; hermes at pin.

**STOP â€” end of Phase 4.** Diff: C:\Users\test\Dev\zola-spikes\prompts\PROC1-ID_Phase4.diff.


## Phase 5 â€” Drift dry run (read-only, Zola kept running)

Harness: dotnet run --project windows-client/Zola.Client.Checks â€” --drift-dry-run (DriftDryRun.cs). Not the client app.
Manifest C:\Users\test\Zola\stable\fix-s51f\stable-manifest.json predates W4 â†’ injected script plugin_compare_rules; **hermes_local_edit compared with v1-porcelain** (algorithm it was made with). Live profile + hermes-agent + venv; read-only. Zola pid 18192 stayed up.

### Components (manifest vs computed, first 12)

| Component | Result | Manifest | Computed |
|-----------|--------|----------|----------|
| hermes_head | match | 345cd2b057a4 | 345cd2b057a4 |
| hermes_local_edits (v1-porcelain) | match | e3b0c44298fc | e3b0c44298fc |
| packages (v1-pip-freeze) | **DRIFT** | a4ac7e1e074d | e8e2b4a9c302 |
| plugins | match (drift_files=0) | 709980694f85 | 709980694f85 |

### Digests
- **v2 local-edit (next promotion would record):** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- v1 local-edit (this comparison): same e3b0c442â€¦ (v1==v2; no algorithm-only diff)

### Timing
| Command | ms |
|---------|----|
| git rev-parse HEAD | 252 |
| v1 local-edit (git status --porcelain) | 257 |
| v2 local-edit (porcelain=v1 -z --untracked-files=all) | 274 |
| pip freeze | 1950 |
| plugin hash walk | 37 |
| DriftChecker.Run | 2469 |
| **total** | **5410** |

**STOP finding (not a fix):** packages pip-freeze digest differs from the fix-s51f manifest. hermes_head, hermes_local_edits (v1), and plugins match.

**STOP â€” end of Phase 5.**


## Phase 5 follow-up â€” packages drift cause (read-only)

### 1. Digests (full)

| Source | Digest |
|--------|--------|
| Manifest `pip_freeze_digest` | `a4ac7e1e074d77bcd708fcb2d60f2b7b72fb95d8a55cb573d51fd1a71ddc883d` |
| Script `Get-PipFreezeDigest` (StableCommon.psm1) | `e8e2b4a9c302628ad8bd0b793a2df1c9951e4d8e7ed2ff3a4d9e787d62538404` |
| C# `HermesDigests.PipFreezeDigest` | `e8e2b4a9c302628ad8bd0b793a2df1c9951e4d8e7ed2ff3a4d9e787d62538404` |

Script **equals** C#; both **differ** from the manifest â†’ decision tree item 3 (not item 2 / algorithm diverge). Item 2 temp captures were not created.

### 3. â€œPackages changed?â€ path

- `*.dist-info` modified after **2026-11-10 09:16:00**: **none** (101 dist-info total; newest `pypdf-6.19.0.dist-info` at 2026-10-08).
- Other top-level `site-packages` entries after that time: **none**.
- Recursive files under `site-packages` after that time: **none**.

**Cause (not package churn):** current PS/C# join keeps a trailing LF from `pip freeze` stdout. Hashing the same joined text **without** that trailing LF yields exactly the manifest digest `a4ac7e1eâ€¦`. Phase 5 â€œpackages DRIFTâ€ is a **trailing-newline normalization** mismatch vs the promoted digest, not a site-packages change after promotion.

### Auto-install?

- **Zola client:** no `pip install` / `uv pip` in the client process path.
- **Hermes:** `tools/lazy_deps.py` can install into the venv when `security.allow_lazy_installs` is true (`install_specs` / `ensure`). Profile `config.yaml` has `security.allow_lazy_installs: false` (~line 87), so lazy installs are blocked for this profile.

### Proposed change (Phase 4/5 list â€” **not implemented**)

1. Switch saves the pip freeze text as `_promotions\<tag>\pip-freeze.txt`.
2. When that file exists, the drift check reports which packages were added, removed, or changed.

**STOP â€” end of Phase 5 follow-up.**


## Phase 4c â€” v1 digest restore + pip-freeze.txt

Cause accepted: W4 fail-closed capture kept trailing LF; v1 digests silently changed. Fixed:

1. **v1 unchanged:** ConvertTo-V1JoinedText / HermesDigests.JoinAsV1CommandOutput TrimEnd LF so 1-pip-freeze and 1-porcelain match proc1-stable Get-DigestOfText on (cmd lines) -join "\n", fail-closed capture kept.
2. **Golden tests:** PS loads git show proc1-stable:tools/stable/StableCommon.psm1 in an isolated process; C# asserts join+hash; v2 stable across runs.
3. **Switch** writes _promotions\<tag>\pip-freeze.txt; drift logs drift packages added=â€¦ removed=â€¦ changed=â€¦ when that file exists; notice text unchanged.

### Suite counts (Zola running)

| Suite | Result |
|-------|--------|
| Client build | OK |
| Checks | **291 PASS / 0 FAIL** (identity 20/20) |
| Stable scripts | **52 PASS / 0 FAIL** |
| zola_workspace | 582 OK |
| zola_memory | 162 OK |
| zola_tools | 44 OK |
| zola_tts | 8 OK |
| zola_phone | 71 ran, 2 FAIL expected |
| Kotlin | **98** / 0; assembleDebug OK |

### Phase 5 dry-run re-run (after 4c)

| Component | Result | Manifest (12) | Computed (12) |
|-----------|--------|---------------|---------------|
| hermes_head | match | 345cd2b057a4 | 345cd2b057a4 |
| hermes_local_edits (v1) | match | e3b0c44298fc | e3b0c44298fc |
| packages (v1-pip-freeze) | match | a4ac7e1e074d | a4ac7e1e074d |
| plugins | match | 709980694f85 | 709980694f85 |

Total dry-run ~5709 ms. All four match.

**STOP â€” end of Phase 4c.** Diff: C:\Users\test\Dev\zola-spikes\prompts\PROC1-ID_Phase4c.diff.


## Phase 6 â€” Pre-merge smoke (Brian present)

Smoke build: %TEMP%\proc1-id-smoke from worktree (pri + App/MainWindow/ZolaTokens xbf). Drift copy: %TEMP%\proc1-id-smoke-drift (both deleted after SM-ID5).

### SM-ID1 â€” PASS
- Brian: first smoke kept answering; refuse pop-up: Zola (dev) is already running. Close it before starting another.
- One Zola.Client (smoke); refuse exited; status = holder pid; log only first-instance identity lines.

### SM-ID2 â€” PASS (after path correction)
- First attempt used live checkout zola-windows (no lock) â†’ both ran; not a product fail.
- Retry from zola-windows-proc1-id: same refuse pop-up; smoke unaffected.
- After smoke close: status/watcher/phone gone within 15 s (~24 ms at first sample).

### SM-ID5 â€” PASS
- Notice once in conversation history (System bubble).
- supervisor.log fields:
  - identity role=stable why=ok tag=proc1-id-smoke-drift
  - identity status_write ok
  - drift completed=true components=packages,plugins plugin_files=1
- Note: log also listed packages (resolver/path timing); plugin_files=1 met. Notice unchanged wording path for plugins.

### Crash watch
| Event | Time |
|-------|------|
| stable close | 2026-11-10T14:46:13-08:00 |
| smoke close | 2026-11-10T15:07:27-08:00 |
| stable start (fix-s51f) | process 15:14:27; recorded 15:15:15 |
| stable extras via shortcut | 15:15:45, 15:15:58 â€” expected: fix-s51f has no lock |

### Experience check (Brian, verbatim)
> If I start Zola twice, the second one tells me which Zola is already running and leaves her alone.

(Applies to smoke/branch lock behavior; current stable fix-s51f still allows multi-open until promotion.)

**STOP â€” end of Phase 6.**

## Phase 6 pre-merge explanations (read-only) â€” STOP

### Deviation
SM-ID2 was first attempted from the live checkout `C:\Users\test\Dev\zola-windows` (against the prompt; that build has no `Local\ZolaClient` lock). Both ran. Retry from `zola-windows-proc1-id` refused correctly.

### 1. SM-ID5 packages in `components=packages,plugins`
- Package digest: `Get-HermesStateDigest -HermesRoot C:\Users\test\Dev\hermes-agent` â†’ `pip_freeze_digest` via `Get-PipFreezeDigest` / `ConvertTo-V1JoinedText` (v1-pip-freeze TrimEnd) = `a4ac7e1e074d77bcd708fcb2d60f2b7b72fb95d8a55cb573d51fd1a71ddc883d`.
- Algorithms: `Get-DigestAlgorithmsObject` â†’ `hermes_local_edit=v2-content`, `pip_freeze=v1-pip-freeze` (local digest from same call, v2).
- Only change intended: one `plugins_tag` hash flip (`plugins/zola_workspace/address_hash.py`).
- `pip-freeze.txt`: **not present** in smoke-drift (only `stable-manifest.json` + `build-role.json` written).
- Repro of that fixture today: `DriftChecker.Run` â†’ `packages=False`, `plugins=True`, `plugin_files=1`.
- **Cause: false positive in the clientâ€™s package check** (fixture was not wrong). STOP â€” defect.

### 2. Double-start timelines
See agent STOP report (15:15 fix-s51f extras + live SM-ID2). Agent closed nothing.

### 3. Data check
Live profile `%LOCALAPPDATA%\hermes\profiles\zola`:
| DB | PRAGMA integrity_check (mode=ro) |
|----|----------------------------------|
| state.db | OK |
| zola_memory\zola_memory.db | OK |
| proactive\proactive.db | OK |
| zola_workspace\taint.sqlite | OK |
Crashes since 14:00 (Application Error / .NET Runtime for Zola.Client.exe or python.exe): **none**.

## Phase 6b â€” packages false-positive diagnose (STOP)

### Times (Brian)
| Event | Time |
|-------|------|
| stable (37296) phone/watcher stop | 16:02:26 |
| drift smoke identity | 16:03:29.92 tag=proc1-id-smoke-drift |
| serve start | 16:03:32.82 |
| drift completed packages,plugins + packages_capture | 16:03:34.12 |
| drift smoke phone/watcher stop | 16:04:26 |
| stable restart (pid 6104) serve start | 16:04:30â€“31 |

### Capture vs harness
- Capture: `drift-pip-freeze-20261110-160334.txt` (deleted after compare). Harness: Cursor `Invoke-ExternalTextCapture` before Brian run.
- Line count: both 100. Endings: both CRLF, both end with CRLF.
- Capture file had UTF-8 **BOM** (from `File.WriteAllText(..., Encoding.UTF8)`); harness file no BOM. Digest path uses process stdout (no BOM).
- Diff: capture has `-e git+https://github.com/NousResearch/hermes-agent.git@345cd2b0â€¦#egg=hermes_agent`; harness had `hermes-agent==0.21.3`. Digests ff8e0f9eâ€¦ vs a4ac7e1eâ€¦ (manifest).

### Cause
Inherited **PYTHONPATH**. When `PYTHONPATH` includes `C:\Users\test\Dev\hermes-agent`, `pip freeze` emits `hermes-agent==0.21.3`. When unset (Explorer-launched Zola), it emits the editable `-e git+â€¦` line. Fixture digests were taken from Cursor (PYTHONPATH set) â†’ a4ac; client freeze from Explorer â†’ ff8e â†’ false packages component.

### Proposed fix (not implemented)
Make script + client run `python -m pip freeze` the same way:
- Executable: `{hermesRoot}\.venv\Scripts\python.exe`
- Args: `-m pip freeze`
- WorkingDirectory: `{hermesRoot}` (explicit)
- Environment: start from a clean block or clear `PYTHONPATH` / `PIP_*` / `VIRTUAL_ENV` (and do not inherit ambient PYTHONPATH); keep PATH enough for git if needed for editable reporting â€” or pin a defined env so VCS vs version form is stable
- Decode stdout as UTF-8 **without BOM** in both (C#: set `StandardOutputEncoding = new UTF8Encoding(false)`; PS: `ReadAllText` with `UTF8Encoding(false)`)

**v1 / fix-s51f:** clearing PYTHONPATH changes current freeze to ff8e0f9eâ€¦, which **does not match** fix-s51f manifest `a4ac7e1eâ€¦`. Needs a **version decision** (new pip-freeze algo / re-promote) before shipping the normalization as the default v1 digest.

### Diagnostic shipped
`packages_capture` file + `drift packages_capture=` log line; identity check added (21 identity rows).

**STOP â€” end of Phase 6b.**

## Phase 6b â€” implement v2-pip-freeze-clean (Claude decision)

Cause accepted: inherited PYTHONPATH. Decision: new algorithm name; v1 not reproduced in client.

### Algorithms
- `digest_algorithms.pip_freeze` = **v2-pip-freeze-clean** (PS `Get-PipFreezeDigestV2` + C# `HermesDigests.PipFreezeDigest`): `{hermesRoot}\.venv\Scripts\python.exe -m pip freeze`, WD=hermesRoot; env = inherited minus PYTHONPATH/PYTHONHOME/PYTHONSTARTUP/PYTHONUSERBASE/VIRTUAL_ENV/PIP_*/PYTHONNOUSERSITE, plus PYTHONUTF8=1; UTF-8 no BOM; join as v1 (LF, no trailing LF).
- `v2-content` local edits: `git -C hermesRoot` from WD=hermesRoot; GIT_* stripped. Name unchanged.
- Client knows only v2 names. Manifest v1-pip-freeze / v1-porcelain â†’ completed=false reason=`unsupported_algorithm:<name>` (never drift). v1 golden tests remain in script only.
- Switch writes v2 algo + `pip-freeze.txt` from same capture; diagnostic capture BOM-free.

### Suite counts (Zola pid 6104 left running)

| Suite | Result |
|-------|--------|
| Client build | OK |
| Checks | **295 PASS / 0 FAIL** (identity 24/24) |
| Stable scripts | **54 PASS / 0 FAIL** |
| zola_workspace | 582 OK |
| zola_memory | 162 OK |
| zola_tools | 44 OK |
| zola_tts | 8 OK |
| zola_phone | 71 ran, 2 FAIL expected (mutex) |
| Kotlin | **98** / 0 fail; assembleDebug OK |

### Dry-run (parent PYTHONPATH set)

| Source | v2-pip-freeze-clean digest |
|--------|----------------------------|
| Script `Get-PipFreezeDigestV2` | `ff8e0f9e1ee624ecb647cd9b53ee741fb701ae494acb7e56e72de14e4a1e8b75` |
| C# `HermesDigests.PipFreezeDigest` | `ff8e0f9e1ee624ecb647cd9b53ee741fb701ae494acb7e56e72de14e4a1e8b75` |

Equal. v1-pip-freeze manifest â†’ packages not-completed `unsupported_algorithm:v1-pip-freeze`; other components match under v2 algos (head/local/plugins).

### SM-ID5 (Brian) — PASS
| Event | Time |
|-------|------|
| drift smoke identity | 2026-11-11T09:22:28.89 tag=proc1-id-smoke-drift |
| drift completed | 2026-11-11T09:22:40.09 `components=plugins plugin_files=1` |
| stable restart | pid 28956 @ 09:23:21 fix-s51f |

- No `packages_capture` line; no `drift-pip-freeze-*.txt` written.
- Notice path: plugins only (`(plugins)`).
- Smoke copy deleted after verify.

Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-ID_Phase6b.diff`

**STOP — end of Phase 6b implement.**


## Phase 7 — Commit and merge

**Brian go-ahead (verbatim, 2026-11-11):** "proceed to commit and merge"

### Step 1 — implementation commit

| Item | Value |
|------|-------|
| Implementation commit | `471c5f789ea10537b556092fd231443131c04816` |
| Message | `feat(PROC1-ID): build role, single-instance refusal, stable drift warning — PROC1-D7/D13` |
| Files | `windows-client/Zola.Client/` (+Identity), `windows-client/Zola.Client.Checks/`, `tools/stable/*`, this progress doc |

### Step 2 — fetch / origin/main

`origin/main` still at Phase 1 base `54a477f03ca9d27ef5b779c1ba1b72292fdad8bf` (unchanged). Proceed.

### Step 3 — merge

| Item | Value |
|------|-------|
| Merge commit | `c8bc87724f6ffe4586a808678530ca88af96daaf` |
| Strategy | `git checkout --detach origin/main`; `git merge --no-ff proc1-id` |
| `git diff --stat origin/main..HEAD` | 26 real repo paths only: `tools/stable/*` (4), `windows-client/Zola.Client/**` (+Identity), `windows-client/Zola.Client.Checks/**`, this progress doc. No `--no-index` / NUL headers. |

### Step 4 — suites on merged tip + crash-watch

**Close (crash-watch):** phone `event=stop` **2026-11-11T09:46:37.5682143-08:00**; watcher `event=stop` **2026-11-11T09:46:37.5899925-08:00**; client gone **09:46:40.779**. Watcher wait: gone by **09:46:42.556** (`Local\ZolaWatcher` FREE) — continue.

| Suite | Result |
|-------|--------|
| Checks | **295 PASS / 0 FAIL** (identity 24/24) |
| Stable scripts | **54 PASS / 0 FAIL** |
| zola_workspace | **582 OK** |
| zola_memory | **162 OK** |
| zola_tools | **44 OK** |
| zola_tts | **8 OK** |
| zola_phone (Zola closed) | **71 OK** |
| Kotlin | **98** / assembleDebug OK |

**Restart (crash-watch):** stable `Zola.Client.exe` pid **2132** CreationDate **2026-11-11 09:49:03**; watcher/phone `job_assigned` **09:49:05**.

### Step 5 — push main + tag

| Item | Value |
|------|-------|
| Merge (tagged) | `c8bc87724f6ffe4586a808678530ca88af96daaf` |
| Tag | annotated `proc1-id` |

### Step 5 (completed) — push

| Item | Value |
|------|-------|
| Pushed | `origin/main` = `38d0de81c9037d6736f6513f680b2d3aafd6dbcd` (docs on merge) |
| Merge (tagged) | `c8bc87724f6ffe4586a808678530ca88af96daaf` |
| Tag | annotated `proc1-id` → merge commit; pushed `refs/tags/proc1-id` |
| Diff re-check before push | 26 real repo paths only (allowed) |

### Step 6 — delete branch / keep worktree

| Item | Value |
|------|-------|
| Branch delete | `git push origin --delete refs/heads/proc1-id`; local `git branch -D proc1-id` |
| Worktree | **kept** until Phase 9 ends (`C:\Users\test\Dev\zola-windows-proc1-id`) |

## Phase 7 complete

## Phase 8 — Live checkout sync

| Item | Value |
|------|-------|
| Eligibility | live on `main`, clean; client under `stable\fix-s51f\` (pid 2132) |
| Before | `54a477f03ca9d27ef5b779c1ba1b72292fdad8bf` |
| After | `38d0de81c9037d6736f6513f680b2d3aafd6dbcd` (`git pull --ff-only origin main`) |

## Phase 8 complete

## Phase 9 — Promotion decision (step 1)

Promoting tag **`proc1-id`** means running `Promote-Stable.ps1` so Brian's everyday shortcut Zola becomes the merged `main` tip that carries PROC1-ID (PR-D09: everything merged into main so far).

**In plain words:**
- **On:** the single-instance lock (one Zola at a time), build role (`stable` via `build-role.json`), and the non-blocking drift warning at startup.
- **Not changed by this promote:** live profile data, installed plugins (plugin diff expected equal), Hermes pin, companion/Kotlin.
- Until promote, everyday Zola stays **fix-s51f** (no lock / no ID drift path). The "one build at a time" rule stays **off** until a promote lands ID (plan, Transition).

Awaiting Brian's verbatim decision: promote `proc1-id` now, or decline.

**STOP — Phase 9 step 1.**

## Phase 9 steps 2–6

**Brian decision (verbatim):** "Promote proc1-id"

### Step 2 — Prepare / Switch / shortcut start

**Prepare:** tag `c8bc877…`; WinUI OK (`App.xbf`, `MainWindow.xbf`, `Themes\ZolaTokens.xbf`, `Zola.Client.pri`); staging 103 files / 102397892 bytes; `client_build_hash=76b387a88…ad3f`; assembleDebug OK; plugin equal; worktree removed; live/profile unchanged.

**Close (crash-watch):** clear **2026-11-12T07:43:40** (after leftover backends cleared); phone suite **71 OK**.

**Switch SUCCESS:** stable=`C:\Users\test\Zola\stable\proc1-id`; backup `proc1-id-20261112-074434`; drill PASS; outgoing fix-s51f → incoming proc1-id; DBs integrity ok.

| Field | Value |
|-------|--------|
| build-role.json | role=stable tag=proc1-id commit=c8bc87724f6ffe4586a808678530ca88af96daaf |
| digest_algorithms | hermes_local_edit=v2-content, pip_freeze=v2-pip-freeze-clean |
| pip-freeze.txt | written under `_promotions\proc1-id\` (100 lines, no BOM) |

**Shortcut start (crash-watch):** pid 21240 @ 07:47:18
```
identity role=stable why=ok tag=proc1-id
drift completed=true components=none
```
SM-S2: exe under `stable\proc1-id\`; serve HERMES_HOME=live profile; ZOLA_HERMES_ROOT=hermes-agent.

### Step 3 — SM-ID3

| Order | Result |
|-------|--------|
| stable → `dotnet run` | PASS — popup `Zola (stable, proc1-id) is already running…`; stable unaffected |
| close stable (07:54:24 stop) → `dotnet run` → shortcut | PASS — popup `Zola (dev) is already running…`; then close dev (08:00:35 stop); shortcut restart |

**Stable restart after SM-ID3:** pid 15300 @ 08:01:41; identity/drift again `role=stable why=ok tag=proc1-id` / `components=none`.

### Step 4 — SM-ID4

Scratch manifest flip `plugins/zola_workspace/address_hash.py`; DriftChecker: plugins=True plugin_files=1.
**Notice text (exact):** `Zola's installed parts have changed since this build was promoted (plugins).`
Nothing live changed; scratch deleted.

### Step 5 — Crash watch

- `python.exe` Application Error (1000) since 2026-11-09 13:23:08: **none**
- Deliberate closes/starts: Prepare-era close 07:43:40; Switch start 07:47:18; SM-ID3 close 07:54:24; SM-ID3 restart 08:01:41; intermediate order-2 close 08:00:35

### Step 6 — Exit criteria (PROC1-ID)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Build role stable/dev | ✅ | build-role + identity logs |
| Single-instance lock refuses and names holder (both orders) | ✅ | SM-ID3 |
| Manifest drift notice (non-blocking) | ✅ | SM-ID4 notice text; live start components=none |
| Switch writes role + rules + digests | ✅ | build-role, digest_algorithms, plugin_compare_rules |
| "One build at a time" active after ID promote | ✅ | promoted proc1-id |
| Suites / smokes | ✅ | Phase 7 suites; SM-ID1/2/5 earlier; SM-ID3/4 here |

**STOP — end of Phase 9.**

## Phase 10 — Closeout

### Promotion record

| Item | Value |
|------|-------|
| Brian decision (verbatim) | "Promote proc1-id" |
| Promoted at | 2026-11-12T07:45:41.6675413-08:00 |
| Stable folder | `C:\Users\test\Zola\stable\proc1-id\` |
| `current.txt` | `proc1-id` |
| Backup folder | `C:\Users\test\Zola\stable\backups\proc1-id-20261112-074434` |
| Drill | PASS — databases=5, files=822, credentials=5 hash-checked; scratch deleted |
| Plugin comparison | equal=True (no plugin copy) |
| Outgoing (backup) | kind=`stable-tag` tag=`fix-s51f` folder=`C:\Users\test\Zola\stable\fix-s51f` |
| Incoming | kind=`stable-tag` tag=`proc1-id` commit=`c8bc87724f6ffe4586a808678530ca88af96daaf` |
| Restore target on disk | `C:\Users\test\Zola\stable\fix-s51f\` **kept** (outgoing release; restore target) |

### SHAs

| Item | SHA |
|------|-----|
| Implementation | `471c5f789ea10537b556092fd231443131c04816` |
| Merge | `c8bc87724f6ffe4586a808678530ca88af96daaf` |
| Tag | `proc1-id` → merge |
| main (pre-closeout docs) | `ddb29b588339224515b99bdb4a0106b64bfb7b82` |

### Suites (merged tip, Phase 7)

Checks **295**/0 · scripts **54**/0 · workspace 582 · memory 162 · tools 44 · tts 8 · phone **71** OK · Kotlin 98

### Smokes

SM-ID1 PASS · SM-ID2 PASS · SM-ID3 PASS (both orders) · SM-ID4 PASS · SM-ID5 PASS (Phase 6b plugins-only re-run PASS)

Experience (Brian, verbatim): "If I start Zola twice, the second one tells me which Zola is already running and leaves her alone."

"One build at a time" rule: **on** (lock-aware `proc1-id` is the promoted stable).

Crash watch: **0** python.exe crashes since 2026-11-09 13:23:08.

**STOP — PROC1-ID COMPLETE (await Claude's review).**
