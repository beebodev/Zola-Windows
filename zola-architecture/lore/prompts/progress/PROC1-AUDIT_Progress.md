# PROC1-AUDIT Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\PROC1-AUDIT_Prompt_v1.1.md`  
**Prompt SHA-256:** `94f130a0e81abb6a56a73d0bfd00ce5ab53c550bcaffed0b1295dbe0dc1d542f` (verified)  
**SOP:** v3.0 (transition) — target-state rules quoted in the prompt (stable folder, isolation, one-build-at-a-time, PR-D01 test gate, lore files)  
**Guardrails:** G-READONLY · G-NO-TESTS · G-NO-RESTART · G-SECRETS · G-PRIVACY · G-EVIDENCE · G-SCOPE · G-STOP · G-MERGE

---

## Worktree

| Field | Value |
|---|---|
| Live checkout | `C:\Users\test\Dev\zola-windows` |
| Audit worktree | `C:\Users\test\Dev\zola-windows-proc1-audit` |
| Branch | `proc1-audit` |
| Base SHA | `9d6458432c9e56e9a69f2f616e3da727acedfe10` (`main` = `origin/main`) |
| Tag (stable) | `fix-s51f` → peel `74941cf72f1e00bb979a9f29ec13aa03fa6b4666` (ancestor of base; base is +1 docs commit) |
| Output folder | `zola-architecture/audit/proc1/` |
| hermes-agent | `C:\Users\test\Dev\hermes-agent` @ `345cd2b057a452236de401d3534b8502a7465e8d` (clean, detached `v2026.9.14`) |

---

## Phase table

| Phase | Status | Notes |
|---|---|---|
| 1 Setup and inventory plan | **DONE** | Worktree created; DoT read; inventory plan below |
| 2 Investigation | **DONE** | Five docs in `zola-architecture/audit/proc1/` |
| 3 Synthesis | **DONE — STOP** | `PROC1_SYNTHESIS.md`; Brian facts recorded |
| 4 Closeout | pending | Only on "proceed to commit and merge" |

---

## Phase 1 — Setup record

### 1. Prompt and live checkout (read-only)

| Check | Result | Evidence |
|---|---|---|
| Prompt SHA-256 | MATCH | `Get-FileHash` → `94F130A0E81ABB6A56A73D0BFD00CE5AB53C550BCAFFED0B1295DBE0DC1D542F` |
| Live branch | `main` | `git rev-parse --abbrev-ref HEAD` |
| Live HEAD | `9d6458432c9e56e9a69f2f616e3da727acedfe10` | `git rev-parse HEAD` |
| `main` == `origin/main` | YES (equal) | both `9d64584…` |
| `git status` (live) | clean, `main...origin/main` | no short status lines |
| Tag `fix-s51f` local | YES (annotated) | `git show-ref --tags` / `git tag -l "*s51*"` → `fix-s51f`; peel `74941cf…` |
| Tag `fix-s51f` on origin | YES | `git ls-remote --tags origin "*s51*"` → `refs/tags/fix-s51f` |
| Tag vs main | tag is ancestor of main; main = tag + 1 (`docs: record S51F-FIX merge SHA`) | `git merge-base --is-ancestor` exit 0; `rev-list --count` = 1 |
| hermes-agent pin | MATCH + clean | HEAD `345cd2b…`; `git status` → nothing to commit, working tree clean; detached at `v2026.9.14` |

### 2. Worktree create + live unchanged

- Created: `git worktree add -b proc1-audit C:\Users\test\Dev\zola-windows-proc1-audit 9d6458432c9e56e9a69f2f616e3da727acedfe10`
- Audit HEAD/branch: `proc1-audit` @ `9d64584…`
- Created: `zola-architecture/audit/proc1/`
- Created: this progress doc
- **Live after create (unchanged):** branch `main`, HEAD `9d64584…`, status clean `main...origin/main`

### 3. Document of Truth — read status

| Doc | Location | Status |
|---|---|---|
| SOP `Phase_SOP_Generic.md` v3.0 | Claude's project (named in prompt) | **NOT FOUND** on disk under `zola-windows`, `zola-spikes`, or `.claude/projects` (same gap noted in P6-LORE / P8-LORE). Target-state rules used from prompt quotes. |
| `claude/PROCESS_DECISIONS.md` (PR-D01–D09) | Claude's project | **NOT FOUND** on disk. PR-D01 / PR-D02 text used from prompt quotes. |
| `DESIGN_DECISIONS.md` | `zola-architecture/lore/` | Read (cited decisions: P9-D02, P10-D12, P8-D06, P2-D04, R1, P6-D11, P4-D25) |
| `OPEN_QUESTIONS.md` | `zola-architecture/lore/` | Read (header + open items; process-isolation questions may appear later) |
| `ROADMAP.md` | `zola-architecture/lore/` | Read (phases through current; hermes pin recorded) |
| `S51F-FIX_Progress.md` | `zola-architecture/lore/prompts/progress/` | Read (launch evidence, TEMP NOT_FOUND, suite commands/counts, phone mutex) |
| `VOICE_CONFIG.md` | `zola-architecture/identity/` | Read (live profile keys; Deepgram key path name; TTS command path) |
| Live profile structure | `%LOCALAPPDATA%\hermes\profiles\zola\` | OBSERVED names only (dirs/files listed; contents not opened for secrets) |

---

## Inventory plan (Phase 2 sources)

Findings are **not** written here — only what will be inspected and why.

### `PROC1_01_Launch_and_Stable.md`

| Source | Why |
|---|---|
| `windows-client/Zola.Client/HermesLaunchResolver.cs` | Hermes root / Python search order; `ZOLA_HERMES_ROOT`; explains TEMP NOT_FOUND |
| `windows-client/Zola.Client/HermesProcessManager.cs` | How serve is started, `HERMES_HOME`, attach-to-running behavior |
| `windows-client/Zola.Client/Supervision/PythonStart.cs`, `SupervisedPython.cs`, `ProcessSupervisor.cs` | Child start plan (P10-D12 / P9-D02); watcher & phone spawn |
| `windows-client/Zola.Client/WatcherProcess.cs`, `PhoneProcess.cs` | Watcher/phone launch command lines and env |
| `windows-client/Zola.Client/App.xaml.cs`, `MainWindow.xaml.cs` | Client entry / startup sequence |
| `windows-client/Zola.Client/Zola.Client.csproj` | Build/publish settings, RID, self-contained vs FDD |
| Desktop / Startup shortcut targets (names+targets only); running `Zola.Client` image path if present | How everyday Zola is actually launched (OBSERVED) |
| `S51F-FIX_Progress.md` (TEMP build, resolve_failed) | Recorded evidence of `%TEMP%` Release build NOT_FOUND |
| `DESIGN_DECISIONS.md` P9-D02, P10-D12 | Supervision and phone-process contract |
| `C:\Users\test\Dev\hermes-agent` layout + `.venv` (names only) | Shared runtime outside client folder; pin/venv change risk |
| Memory / proactive / session store schema mentions in `hermes-plugins/zola_memory`, `proactive_store.py`, Hermes `state.db` docs | Rollback SAFE/UNSAFE/UNVERIFIED per store |

### `PROC1_02_Data_and_Credentials.md`

| Source | Why |
|---|---|
| Live profile tree names under `%LOCALAPPDATA%\hermes\profiles\zola\` | Persistent locations present today (structure only) |
| `VOICE_CONFIG.md` + profile `config.yaml` **key names only** | STT/TTS/wake keys; Deepgram command path; key file path name |
| `%LOCALAPPDATA%\ZolaClient\` (names only) | Client-side secrets/dumps paths |
| `hermes-plugins/zola_workspace/{auth,taint,gmail,gcal,drive,google_http,setup,launch_secret,phone_client,proactive_store,watcher}.py` | Google tokens, DPAPI paths, ports/pipes, proactive DB |
| `hermes-plugins/zola_memory/{store,provider,consolidate,…}.py` | Memory DB path under `HERMES_HOME` |
| `hermes-plugins/zola_phone/{__main__,runtime,wire}.py` | Phone pairing/listen; mutex; pipe |
| `hermes-plugins/zola_tts/` + profile `zola-tts/` | TTS script and key loading |
| `windows-client/Zola.Client/{DashboardSessionToken,PhonePipe,ChatSocket,ServerRequestBroker}.cs` | Local ports/pipes/sockets the client opens |
| `DESIGN_DECISIONS.md` P8-D06, P10-D12, R1 | Send gate, phone-only route, code-voice path |
| Action tools: gmail send, calendar write, drive, phone send/tools | Action-to-authority trace (credential → account/device) |

### `PROC1_03_Single_Instance.md`

| Source | Why |
|---|---|
| `hermes-plugins/zola_phone/__main__.py` | Phone mutex (suite failures while Zola running) |
| `hermes-plugins/zola_workspace/watcher.py` | `Local\ZolaWatcher` mutex |
| Client supervision + `HermesProcessManager` attach path | Second-client / second-serve behavior |
| Ranker mutex refs (`Local\ZolaRanker`), OAuth refresh mutex | Other single-instance locks |
| `PhonePipe.cs` / phone pipe name `\\.\pipe\ZolaPhone` | Pipe contention risk |
| Port 47821 (and env override) | Bind contention |
| `S51F-FIX_Progress.md` phone suite mutex note | Recorded live-instance dependence |

### `PROC1_04_Test_Runner.md`

| Source | Why |
|---|---|
| `S51F-FIX_Progress.md` suite table | Exact commands, counts, durations (G-NO-TESTS — records only) |
| Phase 10 progress docs (`P10-*-Progress.md`) where they record suite floors | Earlier recorded commands/counts |
| `hermes-plugins/*/tests/` | Suite locations and what they import/touch |
| `windows-client/Zola.Client.Checks/` | Client check runner entry and suites |
| `android-companion/` + `local.properties` (gitignored; path presence only) | Kotlin suite prerequisites |
| Mutex / live-profile references inside tests | Live-instance and real-data risk |

### `PROC1_05_Lore_Files.md`

| Source | Why |
|---|---|
| `zola-architecture/lore/` layout (root + `build-plans/` + `prompts/progress/`) | Where new lore files would fit |
| `S51F-FIX_Progress.md`, `zola-architecture/audit/s51-crash/`, `OPEN_QUESTIONS.md` | Known-issue seeds (titles/refs only) |
| `C:\Users\test\Dev\zola-spikes\speech-baseline\` + `zola-architecture/audit/` speech-related docs if any | Speech-baseline / scenario seeds |
| Phase 10 + S51F progress smoke/experience sections | Scenario library seeds |
| Build plans / progress docs referencing SOP v2.2 | Templates/sections needing v3 update |

---

## Guardrails summary (active)

- **Write only** audit docs + this progress doc in the audit worktree.
- **No** tests, builds, restarts, profile/config/env/registry changes.
- **Secrets/privacy:** names, paths, sizes, owners, which code reads — never values or row contents.
- **Evidence labels:** SOURCE / OBSERVED / INFERENCE; UNVERIFIED when a launch or test would be required.
- **Stop** at end of each phase; commit/merge only on explicit proceed.

---

## Notes / out-of-scope observations

- `Phase_SOP_Generic.md` and `claude/PROCESS_DECISIONS.md` remain off-disk; inventory and gap analysis will rely on prompt-quoted target state plus in-repo lore. If Brian can place copies in the worktree later, Phase 2/3 can cite them directly.
- Startup folder and Desktop had no `*Zola*` shortcut names in a quick OBSERVED listing at Phase 1; Phase 2 will widen the search (Start Menu, pinned, running process path) without launching anything.
- Live profile top-level names observed (structure only): `config.yaml`, `auth.json`, `memories`, `sessions`, `state.db*`, `zola_memory*`, `zola_workspace`, `proactive*`, `phone`, `pairing`, `plugins`, `zola-tts`, `logs`, `backups`, etc.

*End of Phase 1. Awaiting proceed to Phase 2.*

---

## Phase 2 — Investigation (STOP)

Written under `zola-architecture/audit/proc1/`:

| Doc | One-paragraph summary |
|---|---|
| `PROC1_01_Launch_and_Stable.md` | Everyday Zola is Debug `Zola.Client.exe` under the live checkout `bin\`; Hermes via sibling/`ZOLA_HERMES_ROOT`; profile hard-coded to `profiles\zola`; TEMP build NOT_FOUND explained; shared hermes+venv risk; rollback by tag alone **UNSAFE** for `proactive.db` schema 8. |
| `PROC1_02_Data_and_Credentials.md` | Full path/credential table; Google `token.dpapi` + phone `pc_key.bin` under profile; Deepgram key **escapes** via hard-coded `ZolaClient\secrets`; action-to-authority: different `HERMES_HOME` alone does not help while client hard-codes `zola`; Deepgram still hits real key even with a new home. |
| `PROC1_03_Single_Instance.md` | No client mutex; phone/watcher/ranker/OAuth mutexes; second client can attach to serve; phone suite mutex is the live conflict; nothing says stable vs dev. |
| `PROC1_04_Test_Runner.md` | Seven recorded suites/commands/floors from S51F; no one-command gate; `zola_phone` fails 2 tests while stable runs; FAIL vs INFRA not modeled. |
| `PROC1_05_Lore_Files.md` | Four v3 lore files missing; proposed root paths; seeds from S51/S51F/OQ/P10/speech-baseline; SOP v2.2 wording list in build plans. |

### Open questions for Brian (union)

1. Everyday launch method (Explorer / VS / other)?
2. Framework-dependent folder vs self-contained for first stable?
3. Shared `hermes-agent` for first stable, or own copy day one?
4. Live Google token = real everyday account (yes/no)?
5. Shared Deepgram key OK early, or per-profile from first cut?
6. Dev profile name/root preference (`profiles\zola-dev` vs elsewhere)?
7. Ever run two Zola windows on purpose?
8. Refuse signal: modal / console / both?
9. Phone mutex tests: INFRA-skip while stable up, or stop stable for gate?
10. Kotlin gate: `testDebugUnitTest` only, or also `assembleDebug`?
11. New lore files: root siblings vs `lore/process/`?
12. Speech-baseline: cite spikes vs copy into known-issues?

### Live checkout check (Phase 2 end)

Read-only only in live tree. Worktree holds new audit docs + this progress update. No tests/builds/restarts.

*End of Phase 2. Awaiting proceed to Phase 3.*

---

## Phase 3 — Synthesis (STOP)

Wrote `zola-architecture/audit/proc1/PROC1_SYNTHESIS.md`.

### Brian facts recorded (verbatim / yes-no)

- Launch: PowerShell `dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj`; prefers an executable.
- Live Google token = real everyday account: **Yes**.
- Two windows on purpose: **No**.

### Synthesis highlights

- **Top-ranked risk (R1):** everyday `dotnet run` rebuilds from whatever is in the live checkout (branch / uncommitted).
- Hard isolation lines: Google token + phone pairing. Cost-only if shared: Deepgram key + Hermes `auth.json`.
- Known-issue seed: ~280 MB `presence.log`.
- Stable preference: Release executable + shortcut (D1-A).
- Recommendations D1–D12 with trade-offs in the synthesis.
- Serious list: no new privacy/security leak; process coupling called out separately.
- Suggested waves W1–W6 with stable folder first.

*End of Phase 3. Awaiting "proceed to commit and merge" for Phase 4.*
