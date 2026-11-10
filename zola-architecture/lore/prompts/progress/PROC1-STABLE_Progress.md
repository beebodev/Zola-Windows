# PROC1-STABLE Progress

**Prompt:** `PROC1-STABLE_Prompt_v1.1.md`  
**Prompt SHA-256:** `8ea5e17720c4fc2b3955ceb96f303ac57a0bab18350898c53f8a271a79a5e598`  
**Plan:** `PROC1_BUILD_PLAN.md` v1.2  
**Plan CRLF SHA-256:** `783419a33bde988b797505914f86965136584cde5a7376e1cb3d3ca5effdf0b0`  
**Plan LF (staged blob) SHA-256:** `04079fbdf598899d75ba2cebe9a5251b46dfe77e2e3b5497f567c17008c7568d`

## Locations

| Item | Value |
|------|-------|
| Live checkout | `C:\Users\test\Dev\zola-windows` (read-only until Phase 8 step 7) |
| Track worktree | `C:\Users\test\Dev\zola-windows-proc1-stable` |
| Plan branch (Phase 1 only) | `proc1-build-plan` (deleted after merge) |
| Work branch | `proc1-stable` |
| Base SHA (plan merge on origin/main) | `396a60229490a32bdc03632bee2d269a32120b33` |
| Plan commit | `8a31d5a0d7f3a7f11cd459b8bce2f8390bc90882` (`docs: PROC1 build plan v1.2`) |
| Plan merge | `396a60229490a32bdc03632bee2d269a32120b33` |
| Proposed stable root | `C:\Users\test\Zola\stable\` |
| hermes-agent pin | `345cd2b057a452236de401d3534b8502a7465e8d` |

## Phase table

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Setup, worktree, plan commit, baselines, facts | DONE | Env-var approval recorded; set in Phase 5 |
| 2 Script design proposal | DONE | Claude review recorded; proceed to Phase 3 |
| 3 Implement scripts and tests | DONE | Claude Phase 3 review recorded; fixes in Phase 4 |
| 4 Review fixes | DONE | F1–F9 accepted; credential list confirmed |
| 4b Phase 4 review gaps | DONE | G1–G3 applied |
| 5 Env var + Prepare | DONE | Env set; Prepare fix-s51f OK; plugin diff = 3 zola_tools (CRLF) |
| 6 Switch | DONE | Switch SUCCESS (build staging); SM-S2 PASS |
| 7 Smoke / experience | DONE | SM-S1/S2/S3 + experience PASS |
| 8 Commit and merge | DONE | Merged; suites on tip PASS |

## Guardrails summary

G-SCOPE (repo: plan + `tools/stable/*` + this progress doc only); G-SCOPE (machine: stable root, one User env var, Zola shortcuts, `%TEMP%` only); G-LIVE-PROFILE; G-LIVE-CHECKOUT; G-NO-RESTART; G-SECRETS; G-PRIVACY; G-TEST-ROOTS; G-TESTS; G-ARCH; G-STOP; G-PROMOTE; G-MERGE; G-ROLLBACK.

## Discrepancies

1. **`PROC1_DECISIONS.md` not on disk** (lives in Claude’s project). **Resolved for pre-stable launch:** Brian’s fact 1 (verbatim, relayed 2026-11-09) matches observed process evidence — see Pre-stable launch below.
2. Remote branch `proc1-build-plan` never existed on origin (local-only); `git push origin --delete proc1-build-plan` reported "remote ref does not exist" (expected). Local branch deleted.

## Approvals and confirmations (after Phase 1 STOP)

**Env var (Brian, verbatim, 2026-11-09):** "I approve ZOLA_HERMES_ROOT = C:\Users\test\Dev\hermes-agent at User scope".
**Set Phase 5:** User=`C:\Users\test\Dev\hermes-agent` (read-back exact). Machine=empty. `ZOLA_HERMES_PYTHON` unchanged (User/Machine/Process empty).

**ANDROID_HOME (Phase 1 Kotlin run):** set for that process only. Re-check 2026-11-09: User=empty, Machine=empty. Process value may linger in a long-lived agent shell from Phase 1; not persisted. No change made.

**Pre-stable launch — Brian fact 1 (verbatim):** "I usually start Zola from powershell using: dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj, but it would probably be better to have an executable".

## Phase 1 — Setup record

### 1. Live checkout / tags / hermes

| Item | Value |
|------|-------|
| Live branch | `main` |
| Live HEAD | `9d6458432c9e56e9a69f2f616e3da727acedfe10` |
| Live status | clean; behind `origin/main` (docs + plan merge; expected) |
| `origin/main` at Phase 1 start (pre plan) | `c396906adb5393018e6297ee9aa97836e2a26e79` |
| Commits main was behind (docs only) | `659025c` docs PROC1 audit; `9c7059a` Merge proc1-audit; `c396906` docs record PROC1 audit merge SHA |
| Tag `fix-s51f` | annotated; tag object `b7edb6652333806b8588dc33a61e6b9ad22b2794`; commit `74941cf72f1e00bb979a9f29ec13aa03fa6b4666`; on origin; ancestor of `origin/main` |
| hermes-agent | clean at pin `345cd2b057a452236de401d3534b8502a7465e8d` |

### 2. Worktree

Created: `git worktree add -b proc1-build-plan C:\Users\test\Dev\zola-windows-proc1-stable origin/main`.  
Live checkout branch/HEAD/status unchanged after create.  
After plan merge: worktree on `proc1-stable` @ `396a602…`.

### 3. Plan commit

Byte-copied from spikes; CRLF and LF SHAs matched developer values; committed, merged `--no-ff`, pushed `HEAD:main`; `git diff --stat origin/main..HEAD` before push listed only the plan file.

### 5. Test baseline (Zola running; worktree)

| Suite | Command | Result | Floor |
|-------|---------|--------|-------|
| Client build | `dotnet build windows-client\Zola.Client\Zola.Client.csproj -c Release` | succeeded (0 errors, 2 nullability warnings) | — |
| Checks | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` | **271 PASS / 0 FAIL** | 271 |
| zola_workspace | venv `python -m unittest discover -s tests -t tests` (`PYTHONPATH`=hermes-agent) | **582 OK** | 582 |
| zola_memory | discover `-s tests -t .` | **162 OK** | 162 |
| zola_tools | discover `-s tests -t .` | **44 OK** | 44 |
| zola_tts | discover `-s tests -t .` | **8 OK** | 8 |
| zola_phone | discover `-s tests -t .` | **71 ran, 2 FAIL** (expected with Zola running): `test_f4_second_process_refuses_the_pipe_and_mutex`, `test_isolation_on_the_real_startup_path` | 71 |
| Kotlin | `android-companion\gradlew.bat testDebugUnitTest assembleDebug --offline` with `JAVA_HOME`=Android Studio JBR, `ANDROID_HOME`=`%LOCALAPPDATA%\Android\Sdk` (no `local.properties` written) | **98** unit, 0 fail/error/skip; assembleDebug OK | 98 |

### 6. Facts

**Stable root:** `C:\Users\test\Zola\` does **not** exist yet. Proposed `C:\Users\test\Zola\stable\` is outside live checkout, track worktree, hermes-agent, zola-spikes, Cursor workspace `C:\Users\test\Dev\zola-windows`, and not under `$env:OneDrive` / `OneDriveConsumer` (`C:\Users\test\OneDrive`); `OneDriveCommercial` unset; no Dropbox/Google Drive/iCloudDrive folders found.

| Known folder | Path |
|--------------|------|
| Desktop | `C:\Users\test\Desktop` |
| Start Menu | `C:\Users\test\AppData\Roaming\Microsoft\Windows\Start Menu` |
| Programs | `C:\Users\test\AppData\Roaming\Microsoft\Windows\Start Menu\Programs` |

**Env vars:** `ZOLA_HERMES_ROOT` and `ZOLA_HERMES_PYTHON` unset at User, Machine, and Process.

**Tooling:** `hermes_cli\main.py` and `.venv\Scripts\python.exe` exist; Python 3.12.14; sqlite3 3.53.1; Windows PowerShell 5.1.26100.9711; pwsh absent; .NET SDK 9.0.318; Pester 3.4.0 present (not required).

**Running (Zola up):**

| Process | PID | Path / notes |
|---------|-----|----------------|
| `dotnet.exe` (launcher) | 14596 | `dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj` |
| `Zola.Client.exe` | 48536 | `…\zola-windows\windows-client\Zola.Client\bin\Debug\net9.0-windows10.0.19041.0\Zola.Client.exe` |
| serve (venv) | 19824 | `python -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0` |
| serve (uv shim) | 13392 | same module args via uv python |
| watcher (venv) | 22152 | `python -m zola_workspace.watcher` |
| watcher (uv shim) | 37512 | same |
| zola-phone (venv) | 18628 | `python -m zola_phone` |
| zola-phone (uv shim) | 45048 | same |

Mutexes (OpenExisting, non-acquiring): `Local\ZolaPhone`=HELD, `Local\ZolaWatcher`=HELD.  
Other python: Blender MCP only (not Zola). Free on `C:` ≈ 233 GB (233,007,693,824 bytes).

**Pre-stable launch (outgoing for first backup):**

| Field | Value |
|-------|-------|
| Client exe (observed) | `C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\bin\Debug\net9.0-windows10.0.19041.0\Zola.Client.exe` (pid 48536) |
| Live checkout | `C:\Users\test\Dev\zola-windows` on `main` @ `9d6458432c9e56e9a69f2f616e3da727acedfe10` |
| Brian fact 1 (verbatim) | `dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj` (plus: would prefer an executable) |
| Observed launcher (pid 14596) | `"C:\Program Files\dotnet\dotnet.exe" run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj` |
| Match | **Yes** — Brian’s command and the running `dotnet` command line are the same path/args |

**Live profile** (`%LOCALAPPDATA%\hermes\profiles\zola\`): top-level names/sizes recorded in Phase 1 shell; DBs: `state.db` 22171648, `projects.db` 45056, `proactive\proactive.db` 2887680, `zola_memory\zola_memory.db` 253952, `zola_workspace\taint.sqlite` 12288, plus zero-byte stubs `proactive.db` / `zola_memory.db` at profile root; expected backup size excluding `logs\`/`cache\` ≈ 49.93 MB (52,353,011 bytes).

**Plugin mirror mapping** (source + P10 deploy records):

| Live path | Repo path | Evidence |
|-----------|-----------|----------|
| `plugins\zola_workspace\` | `hermes-plugins/zola_workspace/` (exclude tests/`__pycache__`) | P8-HARDEN / P8-CONNECT: "Copy (exclude `tests/`, `__pycache__/`) Repo `hermes-plugins/zola_workspace/` → `…\plugins\zola_workspace\`" |
| `plugins\zola_memory\` | `hermes-plugins/zola_memory/` | P6-STORE deploy copy rule |
| `plugins\zola_tools\` | `hermes-plugins/zola_tools/` | P6-CALC deploy copy rule |
| `plugins\zola_phone\` | `hermes-plugins/zola_phone/` | P10 deploy mirrors |
| `zola-tts\deepgram_tts.py` | `hermes-plugins/zola_tts/deepgram_tts.py` | P9-FIX-TTS: "Deploy is a one-file copy… outside `plugins\`"; live SHA matches |

Phase 1 compare vs worktree tip: workspace/phone equal; memory equal except repo-only test helper `l6_hold_guard.py` (not mirrored — P10-LORE); tools three files differ by newline only (live LF, repo CRLF; LF-normalized equal); deepgram equal SHA `7CD342E0…`.

### 7. Environment variable proposal

- **Set:** User-scope `ZOLA_HERMES_ROOT=C:\Users\test\Dev\hermes-agent`
- **Command:** `[Environment]::SetEnvironmentVariable('ZOLA_HERMES_ROOT', 'C:\Users\test\Dev\hermes-agent', 'User')`
- **Verify:** `[Environment]::GetEnvironmentVariable('ZOLA_HERMES_ROOT', 'User')` → exact value above
- **`ZOLA_HERMES_PYTHON`:** not set. `HermesLaunchResolver.cs` L31–64 prefers `ZOLA_HERMES_PYTHON` only if set and existing; otherwise `{root}\.venv\Scripts\python.exe` when present. L67–95 uses `ZOLA_HERMES_ROOT` first for the root.

## Crash-watch notes

Phase 1–2 did not close or start Zola (G-NO-RESTART).

## Phase 3 — Implementation

Files under `tools/stable/`: `Promote-Stable.ps1`, `Restore-Stable.ps1`, `StableCommon.psm1`, `sqlite_tool.py`, `README.md`, `Test-StableScripts.ps1`.

Script tests: **26 PASS / 0 FAIL** (`powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Test-StableScripts.ps1`).

Suites (Zola running; worktree tip):

| Suite | Result |
|-------|--------|
| Checks | 271 PASS |
| zola_workspace | 582 OK |
| zola_memory | 162 OK |
| zola_tools | 44 OK |
| zola_tts | 8 OK |
| zola_phone | 71 ran, 2 FAIL (expected mutex): `test_f4_second_process_refuses_the_pipe_and_mutex`, `test_isolation_on_the_real_startup_path` |
| Kotlin | 98 + assembleDebug OK |

`git status` scope: `tools/stable/*` + this progress doc only. Live checkout unchanged. hermes-agent clean at pin.

## Phase 2 — Script design

Proposal reported in the Phase 2 STOP message (no scripts written). Key design locks from developer addendum:

- Plugin comparison set = files the live mirror is meant to hold; test-only excludes are an **explicit named list** plus `tests\`, `__pycache__\`, `*.pyc`.
- Exact-byte compare (no line-ending normalization); tag-side bytes = Prepare worktree checkout under this machine’s `core.autocrlf` (`true` via `C:/Program Files/Git/etc/gitconfig`).
- Read-only dry-run today: **changed** only the three `zola_tools` newline files; nothing added/removed. Brian decides copy at Phase 5.
- Manifest records **both** post-switch live installed hashes and tag hashes (for PROC1-ID drift).

### Claude’s review (accepted into Phase 3 design)

1. **Tag plugin bytes outlive Prepare.** Prepare copies the comparison-set into `<StableRoot>\_promotions\<tag>\` (live layout, including `zola-tts\deepgram_tts.py`) before removing the temp worktree. Switch copies only from there. Staging recheck covers these files.
2. **Stable folder purity.** `.prepare-record.json` lives in `_promotions\<tag>\`, not `_staging`. `stable\<tag>\` holds only publish output + `stable-manifest.json`. `client_build_hash` covers publish output only. `_promotions\<tag>\` kept after switch as audit record.
3. **Pre-stable outgoing at Prepare.** Prepare observes running client exe, parent launch command, live checkout path/branch/HEAD into prepare-record; Switch copies into backup-index `outgoing`. If no running client and no `current.txt` → Prepare stops and asks.
4. **Added/removed/changed.** Plugin STOP lists all three. `-ApprovedPluginCopy` copies added, deletes removed, overwrites changed. Put-back restores everything vs step-2 snapshot (including re-creating deleted and removing added), hash-verified. Live files outside the comparison set are never touched.
5. **DB by header.** Any file under profile (outside logs/cache) whose first 16 bytes are `SQLite format 3\0` is a DB; skip G-SECRETS credential files; exclude `-wal`/`-shm`/`-journal`.
6. **Drill always cleans up.** Scratch deleted on pass or fail; report that it is gone; failure details fields-only.
7. **Pre-stable restore HEAD check.** Warn if live checkout HEAD differs from recorded outgoing HEAD.
8. **Running-Zola detection** also matches `dotnet` with `Zola.Client.csproj` in the command line.
9. **Extra tests:** Switch after Prepare worktree removed; tamper `_promotions` → recheck refuse; stable folder purity; added/removed/changed + full put-back; non-`.db` SQLite header backup; `-journal` excluded; scratch gone after failed drill; HEAD-differs warning.

## Phase 4 — Claude’s Phase 3 review (fixes applied)

Source: `PROC1-STABLE_Phase4_Fixes.md` SHA-256 `5ca95ca1dba5805cdd34bf60f57f885a9baa786e0f92cf94aa68731b3a641467`.

| ID | Fix |
|----|-----|
| F1 | Switch drill calls `Restore-Stable.ps1 -Drill`; drill verifies integrity + `user_version` + file/credential hashes |
| F2 | `sqlite_tool.cmd_backup` removes dest `-wal`/`-shm`/`-journal` before write |
| F3 | Live restore: refuse missing outgoing exe; pre-restore backup; displace extras; equalize plugins to snapshot |
| F4 | Put-back each step independently; verify all; `PUT-BACK INCOMPLETE` if any FAIL |
| F5 | Real `.lnk` byte save/restore; `-DesktopDir`/`-ProgramsDir`; TestMode refuses live Desktop/Programs |
| F6 | `-ApprovedPluginCopy` only if live diff lists equal prepare-record `plugin_diff` |
| F7 | Credential list expanded (`.env*`, `*.pem`, `credentials*`); live name scan reported at STOP |
| F8 | Backup stops at first sqlite error or integrity FAIL before live change |
| F9 | Manifest `promotion_scripts_digest` + `promotion_scripts_dirty` |

Script tests: **36 PASS / 0 FAIL**. Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-STABLE_Phase4_tools-stable.diff` (UTF-8).

### F7 credential scan (names/paths only)

**Top-level profile names:** `.curator_backups`, `audio_cache`, `backups`, `cache`, `cron`, `desktop`, `hooks`, `image_cache`, `logs`, `memories`, `pairing`, `phone`, `plugins`, `proactive`, `runtime`, `sessions`, `skills`, `state`, `zola-tts`, `zola_memory`, `zola_workspace`, `.codex_gpt55_autoraise_notice`, `.skills_prompt_snapshot.json`, `.update_check`, `auth.json`, `auth.lock`, `config.yaml`, (config.yaml.bak-*), `context_length_cache.yaml`, `essay_draft.txt`, `models_dev_cache.etag`, `models_dev_cache.json`, `proactive.db`, `projects.db`, `SOUL.md`, (SOUL.md.bak-*), `state.db`, `state.db-shm`, `state.db-wal`, `state.db.fts_rebuild.lock`, `state.db.quarantine.lock`, `zola_memory.db`. No `.env`.

**Name matches** (outside `logs\`/`cache\`): `phone\pc_key.bin`, `plugins\zola_phone\keys.py`, `plugins\zola_phone\__pycache__\keys.cpython-312.pyc`, `plugins\zola_workspace\launch_secret.py`, `plugins\zola_workspace\contracts\phone_test_keys.json`, `plugins\zola_workspace\__pycache__\launch_secret.cpython-312.pyc`, `skills\.archive\box\references\oauth-setup.md`, `skills\.archive\github\scripts\git-credential-token.py`, `zola_workspace\token.dpapi`.

**Final credential list (skipped from drill / G-SECRETS):** `auth.json`, `token.dpapi`, `*/token.dpapi`, `phone/*`, `.env*`, `*.pem`, `credentials*`.  
**Claude confirmed (Phase 4 review):** plugin code (`keys.py`, `launch_secret.py`), test fixture `phone_test_keys.json`, and archived skill files are **not** secrets.

## Phase 4b — Claude’s Phase 4 review (G1–G3)

F1–F9 accepted. Gaps applied before Phase 5:

| ID | Fix |
|----|-----|
| G1 | `Restore-Stable.ps1`: explicit `pre-restore-snapshot` branch restores profile/plugins then puts back `current.txt` + shortcut bytes (hash-verified); unknown `outgoing.kind` refuses before any change |
| G2 | Live restore FAIL line includes `pre_restore_backup=<name>`; README restore section documents partial restore / undo |
| G3 | `Test-StableScripts.ps1` tracks/deletes scratch every run; end-of-run asserts no `proc1-stable-test-*`, `zola-restore-drill-*`, `putback-*`, `restore-head-*` leftovers |

Script tests: **40 PASS / 0 FAIL**. Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-STABLE_Phase4b_tools-stable.diff` (UTF-8).

### G3 — “781 leftovers removed” report

Cleanup command (Phase 4 STOP follow-up) matched **only** these `%TEMP%` name patterns and deleted **781** items total:

| Pattern | Role |
|---------|------|
| `proc1-stable-test-*` | This track’s `New-ScratchRoot` fixtures |
| `zola-restore-drill-*` | Switch drill scratch (`Restore-Stable -Target`) |
| `dbg-*` | Ad-hoc Phase 4 debug dirs |
| `proc1-debug-*` | Debug script leftovers |
| `emptyarr-*` / `prep-*` / `out-*` | JSON serialization debug files |
| `putback-*` / `restore-head-*` | Test log files |

A pre-cleanup count of **`proc1-stable-test-*` + `zola-restore-drill-*` alone was 777**; the remaining **4** were among the debug/log patterns above.  
**Not matched / not touched:** `zola-s51f-*` or any other earlier-track prefix (5 `zola-s51f-*` folders still present in `%TEMP%` after Phase 4b).

## Phase 5  Env var + Prepare

**ZOLA_HERMES_ROOT (User):** `C:\Users\test\Dev\hermes-agent` (verified). Machine empty. `ZOLA_HERMES_PYTHON` unset all scopes.

**Prepare** `-Tag fix-s51f` (Zola kept running, pid 48536):
- Tag commit: `74941cf72f1e00bb979a9f29ec13aa03fa6b4666`
- Temp worktree: `%TEMP%\zola-stable-build-fix-s51f-20261110072209` @ that commit; removed after (exists=False)
- `dotnet publish` ? `C:\Users\test\Zola\stable\_staging\fix-s51f\` (succeeded; 2 nullability warnings)
- `assembleDebug`: BUILD SUCCESSFUL in 55s
- Staging: 102 files, 143568107 bytes; `client_build_hash=e8a551d0579d129e316196d5f3db1fc82d81fe10eb02ef377f8bb4f4878d114a`
- Plugin compare: equal=False; added=(none); removed=(none); changed=`plugins/zola_tools/calculator.py`, `plugins/zola_tools/plugin.yaml`, `plugins/zola_tools/__init__.py` (line endings)
- Live checkout unchanged: `main` @ `9d6458432c9e56e9a69f2f616e3da727acedfe10`, porcelain empty
- Live `plugins\` + `zola-tts\` hash map unchanged (before/after)

## Brian decisions (Phase 5 → 6)

**Brian, verbatim (2026-11-10):** "I will go with your recommended decisions."

Applies to these three recommendations:

1. **Plugin file list:** copy `plugins/zola_tools/calculator.py`, `plugins/zola_tools/plugin.yaml` and `plugins/zola_tools/__init__.py` from the tag (line endings only). Switch will use `-ApprovedPluginCopy`.
2. **Switch go-ahead:** run Phase 6 now.
3. **Restore credentials default (plan v1.2):** restore skips sign-ins and pairing (`token.dpapi`, `auth.json`, `phone\`) unless `-IncludeCredentials` is given; backups still contain them.

## Phase 6  Switch (in progress)

**Close (crash-watch):** Brian confirmed Zola closed. Verified 2026-11-10T08:01:06.7915553-08:00  no Zola.Client / serve / watcher / zola-phone; `Local\ZolaPhone`=FREE; `Local\ZolaWatcher`=FREE.

**zola_phone suite (Zola closed):** Ran 71 tests in 34.502s  **OK** (0 failures).

**Switch** `-Tag fix-s51f -ApprovedPluginCopy`: SUCCESS.
- Staging recheck: passed (tag commit, staging hashes, promotions hashes, client_build_hash).
- Backup: `C:\Users\test\Zola\stable\backups\fix-s51f-20261110-080208` (46,173,603 bytes).
- Drill: PASS (databases=5 files=822 credentials=5); scratch deleted.
- Plugins: copied the three `zola_tools` files (live hashes match promotions).
- `current.txt` = `fix-s51f`.
- Shortcuts ? `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe` (Desktop + Programs).
- Brian started from Desktop shortcut; SM-S2 below.

## Phase 6 — First launch failure (G-ROLLBACK)

Desktop shortcut target was correct: `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe`.
Brian: Zola does not open.

### Crash — Application Error (Event ID 1000) fields only; no dumps opened

| Time (local) | Faulting module | Module version | Exception |
|---|---|---|---|
| 2026-11-10T08:10:02.3692147-08:00 | `Microsoft.UI.Xaml.dll` | 3.3.0.0 (path under `Microsoft.WindowsAppRuntime.2_2.6.5.0_x64__8wekyb3d8bbwe`) | `0xc000027b` |
| 2026-11-10T08:10:16.3960121-08:00 | same | same | `0xc000027b` |
| 2026-11-10T08:11:08.4178844-08:00 | same | same | `0xc000027b` |
| 2026-11-10T08:11:11.7055332-08:00 | same | same | `0xc000027b` |

Faulting application: `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe` version 1.0.0.0. Not a Hermes `NOT_FOUND` (no client log written).

**G-ROLLBACK:** left `stable\fix-s51f\` and backup `fix-s51f-20261110-080208` in place. Asked Brian to start the old way: `dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj`. Plugins already copied (three `zola_tools` line-ending files only) remain; no Restore unless requested.

### Brian `dotnet run` relaunch (crash-watch)

| Process | Pid | Start (local) | Command |
|---|---|---|---|
| `dotnet.exe` (launcher) | 4872 | 2026-11-10 08:14:51 | `dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj` |
| `Zola.Client.exe` | 524 | 2026-11-10 08:15:19 | live Debug output under `windows-client\Zola.Client\bin\Debug\...` |
| watcher / phone / serve | (python) | 2026-11-10 08:15:21–08:15:22 | Hermes profile children started |

**Brian confirmation (2026-11-10):** old `dotnet run` launch still works.

**Brian decision:** Option 3 (investigate/republish), two steps. Step A below. Zola stays on `dotnet run` throughout; launch nothing.

### Step A — neutralize shortcuts; leave diagnosis tree

Removed `Zola.lnk` from Desktop and Programs (exists=False both). Left intact: `stable\fix-s51f\`, `current.txt`=`fix-s51f`, backup `fix-s51f-20261110-080208`, `_promotions\fix-s51f\`. No script changes. No Restore.

## Phase 6 — Step A diagnosis (read-only; no launch)

Temp worktree `%TEMP%\zola-stable-build-compare-20261110082057` @ `fix-s51f` / `74941cf72f1e00bb979a9f29ec13aa03fa6b4666`.
S51F-proven command: `dotnet build windows-client\Zola.Client\Zola.Client.csproj -c Release -r win-x64 -o %TEMP%\proc1-build-compare-20261110082057` — **succeeded** (2 nullability warnings). Worktree removed after. Compare dir **kept** for review (`%TEMP%\proc1-build-compare-20261110082057`).

Prepare used (do not change yet): `dotnet publish $csproj -c Release -r win-x64 --self-contained false -o $stagingDir` → became `stable\fix-s51f\`.

### File-name / size compare (`proc1-build-compare-…` vs `stable\fix-s51f\`)

Counts: build=103 files, stable=103 files.

**Only in build (proven `dotnet build -o`):**

| Rel | Size |
|---|---|
| `App.xbf` | 775 |
| `MainWindow.xbf` | 11168 |
| `Themes\ZolaTokens.xbf` | 7430 |
| `Zola.Client.pri` | 28408 |

**Only in stable (`dotnet publish` output + manifest):**

| Rel | Size |
|---|---|
| `DirectML.dll` | 18700224 |
| `Microsoft.Windows.AI.MachineLearning.dll` | 903464 |
| `onnxruntime.dll` | 21659280 |
| `stable-manifest.json` | 14387 |

**Same name, size differs:** `Zola.Client.pdb` only (build 197484 / stable 197496).

**Interesting patterns:** Bootstrap `Microsoft.WindowsAppRuntime.Bootstrap.dll` / `.Net.dll` present both sides, same sizes (394040 / 16696). No `*.winmd` in either. `Zola.Client.deps.json` same size (111533). Stable has **zero** `*.xbf` / `*.pri`.

### `Zola.Client.runtimeconfig.json` side by side (identical)

```json
{
  "runtimeOptions": {
    "tfm": "net9.0",
    "framework": {
      "name": "Microsoft.NETCore.App",
      "version": "9.0.0"
    },
    "configProperties": {
      "MVVMTOOLKIT_ENABLE_INOTIFYPROPERTYCHANGING_SUPPORT": true,
      "System.Reflection.Metadata.MetadataUpdater.IsSupported": false,
      "System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization": false,
      "CSWINRT_USE_WINDOWS_UI_XAML_PROJECTIONS": false
    }
  }
}
```

### Publish-affecting properties

From `windows-client\Zola.Client\Zola.Client.csproj` (no `Directory.Build.props` / `.targets` found in this tree or live checkout scan):

- `Platforms` = `x64`
- `RuntimeIdentifiers` = `win-x64`
- `WindowsPackageType` = `None`
- `Microsoft.WindowsAppSDK` = `2.5.1`
- **Not set:** `PublishTrimmed`, `PublishReadyToRun`, `SelfContained`, `WindowsAppSDKSelfContained`, `Platform` (singular)

CLI only on Prepare: `--self-contained false` (publish).

### S51F evidence that `dotnet build -o` output starts

From `S51F-FIX_Progress.md`:

- Proven command: `dotnet build windows-client\Zola.Client\Zola.Client.csproj -r win-x64 -c Release -o %TEMP%\zola-s51f-fix-client-build` (Phase 1 / Phase 6 suites: build OK).
- Launch from that folder: client pid **12192** from `%TEMP%\zola-s51f-fix-client-build`.
- Supervision log (same incident): `watcher`/`phone` `resolve_failed`; `serve` restart×3 then `keeps_failing` (no `event=start` / no pids) — client process was alive enough to run supervision; failure was Hermes `NOT_FOUND` from TEMP cwd, not a WinUI APPCRASH.

### Hypothesis

Prepare staged a `dotnet publish` tree that **omits** the WinUI compiled XAML/PRI files (`App.xbf`, `MainWindow.xbf`, `Themes\ZolaTokens.xbf`, `Zola.Client.pri`) which the S51F-proven `dotnet build -o` includes. Stable still has Bootstrap and identical `runtimeconfig.json`, so the process can start binding the framework, then dies in `Microsoft.UI.Xaml.dll` with `0xc000027b` when XAML resources are missing — matching the Event Log APPCRASHes of the Desktop-launched `stable\fix-s51f\Zola.Client.exe`. The earlier 2.5.1-vs-2.6.5 note is secondary: both trees would load the machine runtime; the decisive diff is missing `.xbf`/`.pri`. S51F pid **12192** from a `dotnet build -o` folder proves that build-style output gets past WinUI init (supervision ran; failure was Hermes path, not APPCRASH).

### Smallest Prepare change (not applied)

Replace Prepare’s `dotnet publish ... --self-contained false -o <staging>` with the S51F-proven `dotnet build <csproj> -c Release -r win-x64 -o <staging>` so staged files include the `.xbf`/`.pri` set. No other script edits in Step A.

**STOP — Step A complete.** Compare dir kept: `%TEMP%\proc1-build-compare-20261110082057`. Delete only after review.

## Phase 6c — Prepare uses `dotnet build` (Brian approved)

**Brian, verbatim:** "Approved"

**Change recorded:** the saved stable copy is now built with
`dotnet build <csproj> -c Release -r win-x64 -o <staging>`
instead of `dotnet publish … --self-contained false -o <staging>`, because publish left out the `.xbf` and `.pri` files and the Desktop copy crashed (`Microsoft.UI.Xaml.dll` / `0xc000027b`).

### Compare — new build vs today’s run folder

New build: `%TEMP%\proc1-build-compare-20261110082057` (`dotnet build -c Release -r win-x64 -o`).  
Run folder: `C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\bin\Debug\net9.0-windows10.0.19041.0\` (client pid 524).

- **Root files (ignore `.pdb`):** nothing missing from the new build vs the Debug run-dir root.
- **Recursive (ignore `.pdb`):** 119 paths only under Debug — `runtimes\**` (18) and nested `win-x64\**` (101) RID copies. Not required beside a `-r win-x64 -o` layout.
- **ONNX / DirectML:** Zola does **not** use the publish-only natives `DirectML.dll`, `onnxruntime.dll`, `Microsoft.Windows.AI.MachineLearning.dll`. Those are absent from the Debug run folder Zola uses today; client code has no DirectML/ONNX references. Both Debug and the new build carry `Microsoft.ML.OnnxRuntime.dll` / projection DLLs as WASDK dependents; everyday `dotnet run` does not load the three publish-only DLLs.

### Script changes

- `Promote-Stable.ps1`: Prepare runs `dotnet build … -o <staging>`; calls `Assert-StagingHasWinUiResources` (real + Synthetic).
- `StableCommon.psm1`: `Assert-StagingHasWinUiResources` requires `Zola.Client.pri`, `App.xbf`, `MainWindow.xbf`, `Themes\ZolaTokens.xbf` and throws naming any missing.
- `Test-StableScripts.ps1`: four new tests (refuse all missing / refuse partial xbf names / accept present / synthetic includes resources).
- `README.md`: documents `dotnet build` and the WinUI gate.

Diff (UTF-8): `C:\Users\test\Dev\zola-spikes\prompts\PROC1-STABLE_Phase6c_tools-stable.diff`

### Move broken copy aside (Zola kept on `dotnet run`; shortcuts stay removed)

| From | To |
|------|----|
| `stable\fix-s51f\` | `stable\_failed\fix-s51f-20261110-080208\` |
| `stable\_promotions\fix-s51f\` | `stable\_failed\fix-s51f-20261110-080208\_promotions\` |

`current.txt` = `none`. Backup `stable\backups\fix-s51f-20261110-080208` kept. Desktop/Programs `Zola.lnk` still absent.

### Tests

| Suite | Result |
|-------|--------|
| Script tests | **44 PASS / 0 FAIL** |
| Checks | **271 PASS / 0 FAIL** |
| zola_workspace | **582 OK** |
| zola_memory | **162 OK** |
| zola_tools | **44 OK** |
| zola_tts | **8 OK** |
| zola_phone | **71 ran, 2 FAIL** (expected with Zola running): `test_f4_second_process_refuses_the_pipe_and_mutex`, `test_isolation_on_the_real_startup_path` |
| Kotlin | **98** unit, 0 fail/error/skip; assembleDebug OK |

**STOP — Phase 6c.** Compare dirs `%TEMP%\proc1-build-compare-*` deleted after this STOP write.

## Phase 6d — XAML-derived WinUI resource check + Prepare re-run

**Script change:** `Get-ExpectedWinUiResourceRels` derives `.xbf` paths from `.xaml` under the tag’s `windows-client\Zola.Client\` (excluding `bin\`/`obj\`), unions with the minimum four (`Zola.Client.pri`, `App.xbf`, `MainWindow.xbf`, `Themes\ZolaTokens.xbf`). Prepare asserts that list. Synthetic `-SyntheticClientRoot` supports the same check. New test `refuse-extra-xaml-missing-xbf`: extra `ExtraPage.xaml` without `ExtraPage.xbf` → refuse naming it.

Script tests: **45 PASS / 0 FAIL**.

### Prepare `-Tag fix-s51f` (re-run; Zola stayed on `dotnet run` pid 524)

- **Tag commit:** `74941cf72f1e00bb979a9f29ec13aa03fa6b4666`
- **Build:** `dotnet build` succeeded (2 nullability warnings, 0 errors)
- **Staging:** 103 files, 102,352,868 bytes; `client_build_hash=c6e0031238ac55ba3ea7f8726f882ef682246d78424d03aa26d9ff55e25f713c`
- **WinUI resource check:** OK — checked `App.xbf`, `MainWindow.xbf`, `Themes\ZolaTokens.xbf`, `Zola.Client.pri`
- **assembleDebug:** BUILD SUCCESSFUL in 32s
- **Outgoing (prepare-record):** `kind=pre-stable`; `current_txt=null` (live `current.txt`=`none`); `launch_command` = `"C:\Program Files\dotnet\dotnet.exe" run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj`; `client_exe` = Debug output under live checkout (pid **524**); shortcuts null; checkout `main` @ `9d6458432c9e56e9a69f2f616e3da727acedfe10`
- **Plugin compare:** `equal=True` (added/removed/changed empty — the three `zola_tools` files already match live from the prior Switch)
- **Temp worktree:** removed (`exists=False`)
- **Live unchanged:** checkout `main` @ `9d645843…`, porcelain empty; live `plugins\` and `zola-tts\` hash maps unchanged

**STOP — awaiting Brian switch go-ahead after review.**

## Phase 6 — Switch (build-based staging; second attempt)

**Brian go-ahead (verbatim, 2026-11-10):** "Go ahead with the switch"

Staging: `client_build_hash=c6e0031238ac55ba3ea7f8726f882ef682246d78424d03aa26d9ff55e25f713c` (Prepare Phase 6d).

**Close (crash-watch):** Brian: "closed". Verified 2026-11-10T09:15:52.5663073-08:00 — no Zola.Client / serve / watcher / zola-phone; `Local\ZolaPhone`=FREE; `Local\ZolaWatcher`=FREE.

**zola_phone suite (Zola closed):** Ran 71 tests in 23.346s — **OK** (0 failures).

**Switch** `-Tag fix-s51f` (no `-ApprovedPluginCopy`; plugin set equal): **SUCCESS**.
- Staging recheck: passed.
- Backup: `C:\Users\test\Zola\stable\backups\fix-s51f-20261110-091644`.
- Drill: PASS (databases=5 files=822 credentials=5); scratch deleted.
- Plugins: unchanged (equal).
- `current.txt` = `fix-s51f`.
- Shortcuts → `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe` (Desktop + Programs).
- Stable includes `.xbf` / `Zola.Client.pri`; manifest `client_build_hash` matches Prepare.

Brian started from Desktop shortcut; SM-S2 below.

### SM-S2 (Desktop launch after Switch)

Brian: "Desktop app is up." Crash-watch relaunch 2026-11-10T09:20:45.0887130-08:00.

| Check | Result |
|-------|--------|
| Client exe under `stable\fix-s51f\` | **PASS** — pid **7088**, path `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe` (parent Explorer); started 09:19:32 |
| Desktop shortcut | → same exe |
| Serve live profile | **PASS** — `-p zola serve` (launcher_pid **10188** / child **13252**); live profile `%LOCALAPPDATA%\hermes\profiles\zola` present |
| `ZOLA_HERMES_ROOT` | User=`C:\Users\test\Dev\hermes-agent` (set Phase 5). Resolved in practice: serve/watcher/phone from that Hermes `.venv` (not TEMP `NOT_FOUND`) |
| Supervision log | **PASS / normal for this launch** — `phone` `job_assigned` 09:19:35.430 (launcher 22656 / child 23444); `serve` `event=start` 09:19:35.715 (launcher 10188 / child 13252). No `resolve_failed` / `keeps_failing` on this start. Watcher processes live (pids 7136 / 19220 @ 09:19:33); no `watcher` `job_assigned` line written for this generation (note only). |

## Phase 6 complete

Switch SUCCESS (build-based staging); SM-S2 PASS. Awaiting Phase 7 (Brian SM-S1 / experience) when ready.

**STOP — end of Phase 6.**

## Phase 7 — Smoke / experience

### SM-S3 (Cursor)

| Check | Result |
|-------|--------|
| Shortcut + running exe outside repos/worktrees | **PASS** — Desktop, Programs, and running client all `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe` (outside `zola-windows`, track worktree, hermes-agent, zola-spikes) |
| Stable folder holds no project/source files | **PASS** — 0 source-like matches under `stable\fix-s51f\` |
| Stable hashes unchanged after fresh worktree `dotnet build` | **PASS** — `dotnet build` Release win-x64 to `%TEMP%\proc1-sms3-build-*` succeeded; before/after 104 files, 0 missing/extra/changed; scratch removed |

### SM-S1 + experience (Brian)

**Brian, verbatim (2026-11-10):** "SM-S1 is passed.  All functions worked and starting the app from the shortcut feels teh same as before."

| Item | Result |
|------|--------|
| SM-S1 (wake, question, follow-up, calendar/email, phone) | **PASS** (Brian) |
| Experience check | **PASS** — Brian's words above (shortcut feels the same) |
| SM-S2 | PASS (Phase 6) |
| SM-S3 | PASS (this phase) |

### Crash watch (Phase 7 item 4)

Window: Application Error (Event ID 1000) since **2026-11-09 13:23:08** (S51F baseline relaunch).

**`python.exe` APPCRASH:** **none**.

**Deliberate events (not crashes):**

| Time (local) | Event |
|---|---|
| ~08:01 | Close (pre-Switch / first-attempt crash-watch) |
| ~08:14 | `dotnet run` relaunch (G-ROLLBACK; client pid 524 @ 08:15:19) |
| ~09:15 | Close (pre-Switch, build-based staging) |
| ~09:19 | Stable Desktop launch (`stable\fix-s51f\Zola.Client.exe` pid 7088) |

**`Zola.Client.exe` APPCRASH 08:10–08:11 — failed first stable build (publish missing `.xbf`/`.pri`); not the S51 `python.exe` class:**

| Time (local) | Pid | Module | Exception |
|---|---|---|---|
| 2026-11-10T08:10:02.3692147-08:00 | 0x959C (38299) | `Microsoft.UI.Xaml.dll` 3.3.0.0 | `0xc000027b` |
| 2026-11-10T08:10:16.3960121-08:00 | 0x65F8 (26104) | `Microsoft.UI.Xaml.dll` 3.3.0.0 | `0xc000027b` |
| 2026-11-10T08:11:08.4178844-08:00 | 0xB18C (45452) | `Microsoft.UI.Xaml.dll` 3.3.0.0 | `0xc000027b` |
| 2026-11-10T08:11:11.7055332-08:00 | 0x7478 (29816) | `Microsoft.UI.Xaml.dll` 3.3.0.0 | `0xc000027b` |

Faulting path for all four: `C:\Users\test\Zola\stable\fix-s51f\Zola.Client.exe` (publish-staged tree later moved to `_failed\`).

### Watcher `job_assigned` discrepancy (report only; no fix)

| Launch | Supervision events (names + times) |
|--------|-------------------------------------|
| Last launch before today (2026-11-09 ~16:16) | `phone` `job_assigned` 16:16:34.802; **`watcher` `job_assigned` 16:16:34.814**; `serve` `start` 16:16:35.198 |
| 08:14 `dotnet run` relaunch | `phone` `job_assigned` 08:15:23.287; **`watcher` `job_assigned` 08:15:23.323**; `serve` `start` 08:15:23.942 |
| 09:19 stable Desktop launch | `phone` `job_assigned` 09:19:35.430; `serve` `start` 09:19:35.715; **no `watcher` `job_assigned` line** (watcher processes were live) |

**Discrepancy:** earlier launches (including 08:15 and 16:16) wrote `watcher` `job_assigned`; the 09:19 stable launch did not. Not fixed in this track.

### Exit criteria (plan)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Stable folder built from `fix-s51f`; shortcut works; Brian no longer uses `dotnet run` for daily use | ✅ | `stable\fix-s51f\` + Desktop/Programs → that exe; SM-S1 from shortcut; experience PASS |
| Backup taken and restore drill passed on a scratch target; manifest recorded | ✅ | Backup `fix-s51f-20261110-091644`; drill PASS (db=5 files=822 cred=5); `stable-manifest.json` with `client_build_hash=c6e00312…f713c` |
| Plugin set confirmed equal to the tag or updated with Brian's approval | ✅ | Prepare/Switch plugin compare `equal=True` (no `-ApprovedPluginCopy`) |
| Env var set to the approved value only | ✅ | User `ZOLA_HERMES_ROOT=C:\Users\test\Dev\hermes-agent`; Machine empty; `ZOLA_HERMES_PYTHON` unset |
| Tests and suites pass; smoke and experience check pass | ✅ | Script tests 45/0; suites (Checks 271, workspace 582, memory 162, tools 44, tts 8, phone 71 closed OK, Kotlin 98); SM-S1/S2/S3 + experience PASS |

## Phase 7 complete

Smoke and experience checks pass. Progress record repaired (encoding + Phase 7 items).

Phase 7 STOP cleared by Phase 8 go-ahead.

## Phase 8 — Commit and merge

**Brian go-ahead (verbatim, 2026-11-10):** "proceed to commit and merge."

**Step 4 amendment (Brian, 2026-11-10):** when Brian closes Zola for the phone-suite run, check before running anything whether any watcher process (or `Local\ZolaWatcher`) is still present after the client exits. Wait up to 15 seconds, and report pids and times only. If the watcher is gone, continue normally. If it is still running: do not stop it, do not run the suite, and STOP with the evidence. In either case, quote the code that writes watcher `job_assigned`, with the condition under which it writes it, and explain why it may not have been written at 09:19. Fix nothing.

### Watcher `job_assigned` write path (quote; no fix)

From `windows-client/Zola.Client/Supervision/SupervisedPython.cs` (shared by watcher and phone):

```csharp
var assigned = false;
try
{
    _job ??= WatcherJob.CreateKillOnClose();
    assigned = WatcherJob.TryAssign(_job, child.Handle);
}
catch (InvalidOperationException)
{
    assigned = false;
}

// S51F-FIX: log launcher/child pids without delaying the spawn path — S51F-D06
ChildPidLookup.WriteEventAsync(
    _procName,
    assigned ? SupervisionConstants.EventJobAssigned : SupervisionConstants.EventJobAssignFailed,
    _supervisor.Policy.AttemptsInWindow(DateTimeOffset.Now),
    generation,
    child.Id);
```

**Condition for `event=job_assigned`:** `WatcherJob.TryAssign` returned true (child handle assigned to the KillOnClose job). If assign fails or `InvalidOperationException` is caught, the same call writes `job_assign_failed` instead — it does not skip the log line.

`ChildPidLookup.WriteEventAsync` is fire-and-forget (`Task.Run` → `SupervisionLog.Write`).

### Why 09:19 may lack a watcher `job_assigned` line (report only)

At 09:19:35 the log has `phone` `job_assigned` and `serve` `start`, and watcher processes were live (pids 7136 / 19220 @ 09:19:33), but there is **no** `watcher` `job_assigned` and **no** `watcher` `job_assign_failed` for that generation. Assign failure alone would still emit `job_assign_failed`. So the gap means the watcher spawn path either did not reach `WriteEventAsync`, or the async write did not land in `supervisor.log` for that launch — while phone's path did. Not fixed in this track.

### Step 1 — implementation commit

| Item | Value |
|------|-------|
| Implementation commit | `ed985f7357534f77a57da8f1c947c8efeca9b21e` |
| Message | `feat(PROC1-STABLE): stable folder promotion, backup and restore scripts — PROC1-D1/D2/D3/D12/D13` |
| Files | `tools/stable/*` (6) + this progress doc |

### Step 2 — fetch / origin/main

`origin/main` still at plan merge `396a60229490a32bdc03632bee2d269a32120b33` (unchanged since Phase 1). Proceed.

### Step 3 — merge

| Item | Value |
|------|-------|
| Merge commit | `5db407f805f99898d83a1e9221532d1d158c99a8` |
| Strategy | `git checkout --detach origin/main`; `git merge --no-ff proc1-stable` |
| `git diff --stat origin/main..HEAD` | only `tools/stable/*` (6) + this progress doc |

### Step 4 — suites on merged tip + watcher wait

**Close (crash-watch):** client already exited before phone suite. `supervisor.log`: `phone` `event=stop` **2026-11-10T10:16:29.5063172-08:00**; `watcher` `event=stop` **2026-11-10T10:16:29.5399867-08:00**.

**Watcher wait (amendment):** after client exit, polled up to 15s for watcher process / `Local\ZolaWatcher`. First sample **2026-11-10T10:17:39.0961382-08:00**: watcher_pids=[] starts=[] `Local\ZolaWatcher`=FREE. Watcher gone — continue. (Did not stop anything.)

| Suite | Result | Floor |
|-------|--------|-------|
| Checks | **271 PASS / 0 FAIL** | 271 |
| zola_workspace | **582 OK** (112.175s) | 582 |
| zola_memory | **162 OK** (16.786s) | 162 |
| zola_tools | **44 OK** | 44 |
| zola_tts | **8 OK** | 8 |
| zola_phone (Zola closed) | **71 OK** (44.815s) | 71 |
| Kotlin | **98** unit, 0 fail/error/skip; assembleDebug OK | 98 |

All at or above floors.

**job_assigned quote + 09:19 note:** see Phase 8 section above (no fix).
