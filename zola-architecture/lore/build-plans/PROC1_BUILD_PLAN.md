# Zola-Windows PROC1 Build Plan
## First process track: stable build, build identity, dev isolation, test gate, lore files

**Base branch:** `main`
**Base SHA:** record at plan commit (`c396906adb5393018e6297ee9aa97836e2a26e79` or later).
**Audit:** PROC1 (audit `659025cf7647abb6ce723692ae852401a2901ecd`, merge `9c7059a5c5e2426a241803914ecd7c35ae067afc`;
`zola-architecture/audit/proc1/`, especially `PROC1_SYNTHESIS.md`).
**Decisions:** PROC1-D1–D14, approved by Brian 2026-11-09 ("approved"). Full text: Claude's project
`claude/PROC1_DECISIONS.md`. SOP v3.0 decisions PR-D01–D09.
**Theme:** separate Brian's everyday Zola from development. Today he launches with `dotnet run` against the live working
tree, so every launch rebuilds whatever is checked out, and every copy of the client uses his real profile (real Google
account, real phone pairing, real memories). This plan builds the infrastructure SOP v3 depends on. No new Zola
capability. No Hermes source change (2026-10-06 no-fork decision).

**SOP:** v3.0 under its transition rules. This plan is the first process track; it runs in the full lane. As each
track below merges, the SOP rules that depend on it switch on for the **next** track (table at the end).

---

## Overview

Five tracks, run one at a time in order (PR-D05). Each is its own branch, prompt, verification and merge.

| Track | Name | Scope | Complexity |
|-------|------|-------|------------|
| PROC1-STABLE | Stable folder, promotion, backup, restore | Scripts under `tools/stable/`; one user environment variable (approved); a shortcut; docs | Medium |
| PROC1-ID | Build identity and single-instance refusal; manifest check | Windows client (startup); checks | Medium |
| PROC1-DEV | Dev profile, fail closed; Google test-only; no real phone | Windows client (profile and data roots); plugin path for the Deepgram key (read-only change); checks | Medium-Large |
| PROC1-GATE | One-command test gate (PR-D01) | `tools/test-gate/`; docs | Medium |
| PROC1-LORE | Four lore files, seeds, template wording | `zola-architecture/lore/`; templates | Small |

**Sequencing rule:** STABLE first (Brian's Zola and the crash watch must stop depending on the working tree), then ID,
then DEV (needs the build identity), then GATE, then LORE. A later track doesn't start until the previous one has merged.

**Working-copy rule (all tracks):** Cursor works in a separate git worktree, never in the live checkout
`C:\Users\test\Dev\zola-windows`, which stays on `main`, clean, until Brian has switched to the stable shortcut. After that
the live checkout is a normal dev tree again, but no plugin code is copied from it into the live profile except by
promotion (D13).

---

## Decisions resolved in this build plan (summary)

- **D1** Stable folder with a Release build (`Zola.Client.exe`) and a shortcut named Zola; always finds Hermes; `dotnet run` is dev-only.
- **D2** Framework-dependent build.
- **D3** Stable shares `C:\Users\test\Dev\hermes-agent` and its venv for now; no Hermes or package change without
  Brian's approval.
- **D4** Dev profile `zola-dev`; a dev build that can't confirm it is dev refuses to start.
- **D5** Dev shares the Deepgram and LLM-provider keys for now (cost and quota only).
- **D6** No real phone in dev.
- **D7** A second Zola refuses with a pop-up naming the running build; the lock is taken before any data is opened or
  Hermes attached; it never closes the first.
- **D8** INFRA is not a pass; every merge needs a clean full run on the exact commit.
- **D9** Kotlin unit tests in the gate; `assembleDebug` at promotion.
- **D10/D11** Lore files beside the existing root files; speech baseline referenced, not copied.
- **D12** Consistent backup and a tested restore at every promotion; restore loses data stored since that promotion and
  can't undo sends.
- **D13** Plugin code reaches the live profile only through promotion, permanently; stable manifest recorded at
  promotion and checked at startup.
- **D14** Dev uses only the test Google account or has Google off; never falls back to the live token.

---

## Track PROC1-STABLE

### Problem
PROC1_01: everyday Zola = Debug build of the live working tree via `dotnet run`. A Release build outside the repo can't
find Hermes (`ZOLA_HERMES_ROOT` unset; S51F `%TEMP%` failure; the resolver's parent walk from a folder outside `Dev\`
never reaches `Dev\hermes-agent`). Plugins run from the live profile's `plugins\` mirror, not from the repo (D13).
Tag-only rollback is unsafe (`proactive.db` schema 8).

### What it builds (scripts only; no client, plugin, Hermes or Kotlin code change)
- **Stable root:** `C:\Users\test\Zola\stable\` (proposed; Cursor confirms it is outside every repo, worktree and
  Cursor workspace, **and not inside a OneDrive or other cloud-synced folder**, because backups hold credential files).
  One folder per promotion: `stable\<tag>\` (client build), `stable\current.txt` naming the active tag, and
  `stable\backups\<tag>-<yyyyMMdd-HHmmss>\`. Backups are kept (no automatic deletion in this track).
- **Executable:** stays `Zola.Client.exe` (no csproj or assembly rename). The shortcut is named **Zola**.
- **Every script takes its roots as parameters** (`-StableRoot`, `-ProfileRoot`, `-ClientDataRoot`) with the live paths as
  defaults. Tests always pass scratch roots and the scripts' test mode refuses any root that resolves to a live path.
  Scripts run in Windows PowerShell 5.1 (no Pester or module install required) and are started with
  `powershell -NoProfile -ExecutionPolicy Bypass -File …`.
- **SQLite work** (online backup, `PRAGMA integrity_check`, `PRAGMA user_version`/schema reads) goes through one small
  Python helper `tools/stable/sqlite_tool.py` run by the Hermes venv's Python, standard library only (`sqlite3.backup`).
  No package install. It prints counts, versions and OK/FAIL only, never rows.
- **`tools/stable/Promote-Stable.ps1`, two steps** (v1.1: keeps Brian's Zola down only for the short part):
  - **`-Prepare -Tag <tag>`** (may run while Zola is running; touches nothing live):
    1. Verify the tag exists locally and on origin and is an ancestor of `origin/main`.
    2. Build it in a temporary worktree outside the live checkout: `dotnet publish` Release, win-x64,
       framework-dependent (D2) into `stable\_staging\<tag>\`. Run the Kotlin `assembleDebug` check there (D9).
    3. Record the client build hash (SHA-256 over the published file list) and the tag's `hermes-plugins/zola_*` and
       `hermes-plugins/zola_tts/deepgram_tts.py` file hashes into the staging folder, and report (read-only) whether the
       live plugin set differs, so any plugin decision is made before Zola is closed. Remove the temporary worktree.
  - **`-Switch -Tag <tag>`** (Zola must be closed; refuses if `Zola.Client.exe`, a `-p zola serve` Python, the watcher
    or `zola-phone` is running, or if `Local\ZolaPhone` / `Local\ZolaWatcher` is held; never stops anything itself):
    1. **Recheck the staging (v1.2):** Prepare and Switch can be hours apart. The staging folder's file hashes must still
       match Prepare's record, the tag must still resolve to the same commit, and the tag's plugin hashes must be
       unchanged. Any difference: refuse and re-run Prepare.
    2. **Backup (D12, v1.1 scope):** the **whole live profile except `logs\` and `cache\`**, so no store is missed
       (`sessions\`, `cron\`, `skills\`, `memories\`, `SOUL.md`, `MEMORY.md`, `auth.json`, `phone\`, `pairing\`,
       `zola-tts\`, `plugins\` …). Every `.db`/`.sqlite` file (`state.db`, `zola_memory\zola_memory.db`,
       `proactive\proactive.db`, `zola_workspace\taint.sqlite`, any other found) is copied with the SQLite online
       backup, not a file copy; `-wal`/`-shm` files are not copied. Credential files (`token.dpapi`, `auth.json`,
       `phone\*`) are copied as files, never opened or printed. `integrity_check` on every database copy; a
       `backup-index.json` lists every file with size and SHA-256 and each database's schema version.
       **The backup belongs to the outgoing release (v1.2).** It is taken before the incoming tag takes over, so
       `backup-index.json` records both: `outgoing` (the stable tag and folder that was active, or, for the first
       promotion, the verified pre-stable launch: Brian's `dotnet run` command, the live checkout path, branch and HEAD,
       and the running client's executable path observed before Zola was closed) and `incoming` (the tag being
       promoted). It also records the outgoing state at backup time: Hermes HEAD, local-edit digest, package digest,
       live plugin hashes, `config.yaml` hash, and the current shortcut targets and `current.txt`.
    3. **Restore drill (D12, v1.1: part of every promotion, before anything live changes):** run `Restore-Stable` against
       a scratch target under `%TEMP%`; databases must pass `integrity_check` with matching schema versions and every
       restored file must match `backup-index.json`. Credential files are **not** copied into the scratch target (hash
       check of the backup copy only). **A drill writes only under its target (v1.2): it never touches the real
       shortcuts, `current.txt` or any folder under the stable root.** The scratch target is deleted afterwards. A
       failed drill stops the switch.
    4. **Plugins (D13):** compare the live profile's `plugins\zola_*` and `zola-tts\deepgram_tts.py` with the tag's
       hashes from Prepare (ignore `__pycache__` and `*.pyc`). If they differ, list the files (added / removed /
       changed) and STOP for Brian's approval before copying. Copy only on approval.
    5. **Stable manifest (D13):** `stable\<tag>\stable-manifest.json` — tag and commit, client build hash, Hermes HEAD
       and a digest of `git status --porcelain` (local edits), Python package set digest (`pip freeze`), per-plugin file
       hashes, `config.yaml` hash, backup folder name, the commit of the promotion scripts used, and the time. No secret
       values.
    6. Move `_staging\<tag>\` to `stable\<tag>\`; update `current.txt`; create or update the Desktop and Start-menu
       shortcut **Zola** → `stable\<tag>\Zola.Client.exe` (working directory `stable\<tag>\`). The Desktop path comes
       from the Windows known-folder API (Brian's Desktop may be OneDrive-redirected; a shortcut file there is fine).
    7. **All-or-nothing (v1.2):** steps 4–6 are one unit. If anything fails after the first live change (a plugin copy,
       the folder move, `current.txt` or a shortcut), the switch puts back the outgoing plugins (from the backup), the
       outgoing shortcuts and `current.txt` (recorded in step 2; a shortcut that didn't exist is removed), and moves the
       folder back to staging; it then verifies each by hash and reports what failed. Nothing is left half-switched.
    8. Refuses to overwrite an existing `stable\<tag>\` (a re-promotion of the same tag is a later decision).
- **Hermes discovery (D1):** one **user** environment variable `ZOLA_HERMES_ROOT=C:\Users\test\Dev\hermes-agent`, set
  once with Brian's approval of the exact value. `ZOLA_HERMES_PYTHON` is **not** set (v1.1): the resolver already uses
  `{root}\.venv\Scripts\python.exe` when it exists (`HermesLaunchResolver` L31–64). Notes: the variable reaches only
  processes started after it is set (new Explorer launches and new shells); it also applies to dev `dotnet run`
  launches, which resolve the same checkout anyway (D3). The previous value (expected: unset) is recorded.
- **`tools/stable/Restore-Stable.ps1 -Backup <folder> [-Target <root>] [-IncludeCredentials]`** (Zola closed for a live
  target): prints the D12 warning and which release the backup belongs to (its `outgoing` entry), requires typing the
  backup folder name to confirm, then restores the backed-up profile files (databases via SQLite backup into place) and
  the outgoing plugin set from the backup. **v1.2:** it returns Brian to the **outgoing** release, never the incoming
  one: `current.txt` and the shortcuts point at the outgoing tag's folder. If the outgoing release is the pre-stable
  launch (first promotion), it removes the Zola shortcuts, marks `current.txt` as "none", and prints the recorded
  fallback launch command. With `-Target` it writes only under the target. **v1.1 (needs Brian's verdict):** by default it does **not** restore credentials and
  pairing (`token.dpapi`, `auth.json`, `phone\`); `-IncludeCredentials` does. Reason: a code rollback doesn't change
  who Zola is signed in as or which phone is paired, and putting back older sign-in or pairing state can break the
  Google sign-in, the model sign-in or the phone link. Before restoring into the live profile it compares current Hermes
  HEAD, local-edit digest and package digest with the outgoing state recorded in the backup; on a difference it says which and requires a
  second confirmation (restore can't roll Hermes back; D3).
- **`tools/stable/README.md`:** how to prepare, switch, roll back and drill; what a restore loses (D12); how to go back
  to `dotnet run` in an emergency.

### Emergency fallback (first promotion)
If the stable build misbehaves at its first launch, Brian closes it and starts Zola the old way (`dotnet run` from the
live checkout, which still holds the same code). Nothing in this track deletes that path. The verified pre-stable launch
is recorded as the first backup's `outgoing` release (v1.2), so a restore from that backup returns to it. The shortcut
can be deleted; the environment variable is harmless to the old path.

### First promotion
- Promote `fix-s51f` (Brian approved it as stable, 2026-11-09). The switch changes Brian's everyday build, so it runs only
  after Brian's verbatim go-ahead. Prepare runs while he uses Zola; then Brian closes Zola; Cursor runs the switch;
  Brian starts Zola from the shortcut. **Crash watch:** continues; the close and the relaunch are logged in the progress
  doc (same source, Release instead of Debug client; serve, Hermes, plugins and config unchanged).
- The promotion runs the scripts from this track's worktree branch (their commit is recorded in the manifest). The
  stable folder does not depend on the scripts after the switch.

### Tests
- Script checks (plain PowerShell test script; scratch roots only; no real Zola launched): refuses while a Zola-like
  process or a held test mutex is present (detection made injectable for the test); refuses an unknown tag and a tag not
  on `origin/main`; refuses a live root in test mode; backup covers every file in a synthetic profile except `logs\`
  and `cache\`, uses SQLite backup for every database (including one in WAL mode with unflushed writes) and its copies
  pass `integrity_check`; manifest has every field and no secret value; plugin-diff STOP fires on an added, a removed
  and a changed file and not on `__pycache__`; restore drill passes on a scratch target and fails on a corrupted backup;
  `Restore-Stable` refuses without the typed confirmation; credentials are skipped without `-IncludeCredentials`;
  Hermes-mismatch warning fires; `-Switch` refuses an existing `stable\<tag>\`.
- v1.2: `backup-index.json` records `outgoing` and `incoming` correctly for a first promotion (pre-stable) and for a
  later one (stable tag to stable tag); restore points the shortcut and `current.txt` at the outgoing tag, or removes
  the shortcut and prints the fallback command for a pre-stable outgoing release; a drill with `-Target` leaves the real
  shortcut files, `current.txt` and the stable root byte-for-byte unchanged; `-Switch` refuses when a staged file, the
  tag commit or a tag plugin hash changed after Prepare; a failure injected at the shortcut update, after the plugins
  were copied, leaves plugins, shortcuts and `current.txt` exactly as before the switch (verified by hash) and the
  folder back in staging.
- All existing suites at or above the S51F floors (Checks 271, workspace 582, memory 162, tools 44, tts 8, phone 71,
  Kotlin 98), phone suite with Zola closed.

### Smoke and experience
- **SM-S1 (Brian):** start Zola from the shortcut. Wake word, a question, a follow-up; a calendar or email read; the
  phone link works. No PowerShell needed.
- **SM-S2 (Cursor):** the running client's executable path is under `stable\fix-s51f\`; serve uses the live profile;
  `ZOLA_HERMES_ROOT` resolved; supervision log normal.
- **SM-S3 (Cursor, v1.1, no change to the live checkout):** the shortcut target and the running executable are outside
  every repo and worktree; the stable folder holds no project or source files; the stable folder's file hashes are
  unchanged after a fresh `dotnet build` in the track worktree.
- **Experience check (Brian):** "I start Zola from a shortcut, and she works the same as before."

### Exit criteria
- [ ] Stable folder built from `fix-s51f`; shortcut works; Brian no longer uses `dotnet run` for daily use.
- [ ] Backup taken and restore drill passed on a scratch target; manifest recorded.
- [ ] Plugin set confirmed equal to the tag or updated with Brian's approval.
- [ ] Env var set to the approved value only.
- [ ] Tests and suites pass; smoke and experience check pass.

---

## Track PROC1-ID

### Problem
PROC1_03: no client single-instance lock; a second client starts watcher and phone and may attach to the running serve
or spawn a second serve on the same databases. Nothing identifies stable vs dev. D13 needs a startup manifest check.

### Changes (client)
- **Build role:** the client knows whether it is `stable` or `dev`. Stable: a role file written by the promotion
  script beside the exe (`build-role.json`: role, tag, manifest path). Anything else (including `dotnet run`) is `dev`.
  No role file → dev.
- **Single-instance lock (D7):** first thing in `App.OnLaunched`, before any process manager, profile path, watcher,
  phone or serve discovery: a machine-wide named mutex `Local\ZolaClient` plus a small status file (role, tag, pid,
  exe path). If held, show a modal naming the running build ("Zola (stable, fix-s51f) is already running.") and exit.
  Never kills or signals the running build. Console line as well.
- **Manifest check (D13):** a stable build at startup compares Hermes HEAD + local-edit digest, package-set digest and
  plugin hashes against its manifest, off the UI thread with a time limit; on drift, a visible, non-blocking notice
  ("Zola's installed parts have changed since this build was promoted.") and a log line naming which component. Never
  blocks start (fail open for availability; this is a warning, not a permission). Wording approved by Brian.
- Promotion script writes `build-role.json` (small STABLE-script follow-up in this track).

### Transition (v1.2)
- **The refusal only works when both builds have the lock.** The first stable build (`fix-s51f`) has none, so a
  lock-aware dev build would find no holder and start beside it. The "one build at a time" rule is therefore active only
  once a lock-aware build is the stable one: the track ends with Brian's decision on an early promotion of the ID merge
  tag (PR-D09: it promotes everything merged so far), run with the STABLE scripts. Until then, Brian closes stable
  before any dev launch, as today.
- **Smoke both launch orders** after that promotion: stable first, then dev (dev refuses and names stable); dev first,
  then stable from the shortcut (stable refuses and names dev). In both, the first build keeps running.

### Tests
- Lock taken before any data or Hermes access (source-order test like the S51F gap-order lesson); second start
  refuses and names the holder; abandoned mutex after a crash is reclaimed; manifest drift per component; no role file →
  dev.

### Smoke
- Start stable, then try `dotnet run`: refusal pop-up names stable; stable keeps running, mid-reply if possible.
- Edit a scratch plugin hash in a copy of the manifest (test target only): drift notice appears.

---

## Track PROC1-DEV

### Problem
PROC1_02: profile hard-coded to `zola`; Deepgram key and client logs outside `HERMES_HOME`; Google token and phone keys
real. Action trace: with a separate home, Google and phone are cut off; without it, dev reaches the real account.

### The window between ID and DEV (v1.2)
After PROC1-ID merges and before PROC1-DEV merges, a build labelled `dev` still uses the live profile, the real Google
token and the real phone; the label gives no isolation. In that window a dev launch is allowed only for a track's
smoke tests, with Brian present and stable closed, under the same rules as today's live smoke tests (real sends and
writes only on his explicit request). Nothing in the ID track may describe a dev build as isolated. The isolation
rules switch on only when PROC1-DEV's isolation check passes.

### Changes
- **Profile by role (D4):** stable → `profiles\zola`; dev → `profiles\zola-dev`. Dev resolves every persistent path
  under `zola-dev` and under a dev client-data root (`%LOCALAPPDATA%\ZolaClient-dev\` for logs, dumps, debug). Before
  launching anything, a dev build confirms its profile resolves to `zola-dev` and that no path in its plan points into
  `profiles\zola` or `ZolaClient\` (except the shared Deepgram key, D5); otherwise it refuses to start (fail closed).
- **Google (D14):** dev's `zola-dev` profile holds only the **test Google account's** token (Brian runs the setup with
  the test account), or Google tools are off in dev. A dev build never reads `profiles\zola\zola_workspace\token.dpapi`;
  a test asserts the dev token path and that an empty dev store means "not connected", never the live token.
- **Phone (D6):** in dev, `zola-phone` is not started and phone tools report "not available in dev". Cursor checks
  whether fake_phone can serve an interactive dev session; if yes, it may be offered as an opt-in, recorded at the
  STOP.
- **Deepgram (D5):** `deepgram_tts.py` reads its key path from an environment variable with the current path as the
  default, so behaviour is unchanged for stable; dev passes the same path for now. (Prepares per-profile keys later.)
- **Synthetic data:** a minimal synthetic `zola-dev` seed (invented people and memories, no real names) created by a
  script; no copy of live data.
- **Isolation check (SOP):** Cursor runs it with dev running: every resolved path under the dev roots; the live token
  unreachable; a test calendar write and memory write land only in dev or the test account; no phone process; starting
  stable while dev runs refuses (PROC1-ID).

### Tests
- Path plan for dev contains no live path; fail-closed start when the profile can't be confirmed; Google no-fallback;
  phone off in dev; Deepgram env default unchanged for stable.

### Smoke
- Dev session with the test Google account: read and create a test calendar event (test account only, confirmed in its
  calendar); memory write lands in `zola-dev`; stable's databases unchanged (hash before and after).

---

## Track PROC1-GATE

- `tools/test-gate/Run-TestGate.ps1`: runs every suite (the seven in PROC1_04), reports each separately (passed, failed,
  skipped, count), records the commit SHA, fails on a missing, unavailable or zero-test suite, exits nonzero on any FAIL
  or INFRA, never excludes a suite silently. INFRA = tooling or environment (missing SDK, venv, live mutex held); FAIL =
  assertions. INFRA is not a pass (D8).
- Floors file (`tools/test-gate/floors.json`) with the current counts; a count below floor is FAIL.
- Phone suite: if `Local\ZolaPhone` is held, report INFRA "stable is running; close Zola for a clean run".
- Kotlin unit tests in the default run; `-Promote` adds `assembleDebug` (D9).
- Output: a summary table plus a machine-readable result file under `%TEMP%` (not committed).
- Tests: a fake suite that fails, one with zero tests, one missing, one INFRA → each classified correctly.

## Track PROC1-LORE

- Create `KNOWN_ISSUES.md`, `SCENARIO_LIBRARY.md`, `EXPERIENCE_LOG.md`, `FAST_LANE_LOG.md` beside the existing lore root
  files (D10), each with a header explaining its use under SOP v3.
- Seed `KNOWN_ISSUES.md` from PROC1_05 and `claude/S51F_FIX_CLOSED.md`: admit→submit gap, self-echo, mic button not
  interrupting, Stop Speaking on unprompted lines, clipped opening words, `0x3b1ff`/sqlite crash classes,
  `presence.log` ~280 MB, P10 leftover worktrees, S100 items. Each with severity and a "serious?" flag (PR-D03).
- Seed `SCENARIO_LIBRARY.md` with the S51F SM1–SM3 and experience checks, PROC1 smoke tests, and references to the
  speech-baseline items (D11).
- Update templates that still say SOP v2.2 Stage 3 (list from PROC1_05).
- S51 status in `KNOWN_ISSUES.md` reflects the crash-watch result at the time this track runs.

---

## SOP rules switched on as tracks merge

| After | Switches on for the next track |
|-------|--------------------------------|
| PROC1-STABLE | Stable promotion via the script only; D12 backup at every promotion; D13 plugin rule |
| PROC1-ID | "One build runs at a time" refusal, once a lock-aware build has been promoted to stable (see PROC1-ID "Transition") |
| PROC1-DEV | Dev isolation rules; synthetic data by default; dev testing never uses the live profile |
| PROC1-GATE | PR-D01 one-command gate before every merge |
| PROC1-LORE | Stage 0 reads `KNOWN_ISSUES.md` and `EXPERIENCE_LOG.md`; fast-lane log in use; scenario library grows at lore closeout |

## Explicitly deferred

| Item | Reason | When |
|------|--------|------|
| Own Hermes copy for stable | D3: share for now; manifest drift warning covers it | When drift or a Hermes update makes it worth it |
| Self-contained build | D2 | Not planned |
| Per-profile Deepgram and LLM keys | D5 | When quota or cost matters |
| Android emulator for dev phone tests | D6 | When a track needs end-to-end phone testing |
| Role-specific phone mutex/pipe names | D8 permanent fix | With a phone track |
| GitHub Actions | PR-D01 follow-up | After the local gate |
| `presence.log` rotation | Known issue, not a process item | Scheduled from KNOWN_ISSUES |

*PROC1 Build Plan version 1.2 — 2026-11-09 (v1.2 after ChatGPT's review: the backup belongs to the outgoing release and
restore returns to it; staging rechecked at switch; all-or-nothing switch; drill never touches the real shortcut or
`current.txt`; ID/DEV transition rules. v1.1 revised v1.0 after Claude's review: two-step promotion, whole-profile backup,
restore drill inside every promotion, credentials not restored by default, `ZOLA_HERMES_PYTHON` not set, SM-S3 without
touching the live checkout, scratch-root tests). Decisions locked before the plan (Brian, 2026-11-09). Next: PROC1-STABLE
prompt.*
