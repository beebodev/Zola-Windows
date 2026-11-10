# PROC1_01 — Launch and Stable

**Audit:** PROC1 · Phase 2 · read-only  
**Prompt:** v1.1 · SHA-256 `94f130a0e81abb6a56a73d0bfd00ce5ab53c550bcaffed0b1295dbe0dc1d542f`

## Summary

Brian’s everyday Zola is a Debug `Zola.Client.exe` running from the live checkout’s `bin\` tree, not a separate stable folder. The client finds Hermes by walking cwd / BaseDirectory for a sibling `hermes-agent` (or `ZOLA_HERMES_ROOT`), always points serve/watcher/phone at the hard-coded live profile `%LOCALAPPDATA%\hermes\profiles\zola`, and shares one `hermes-agent` checkout + `.venv` with any other client on this PC. A copy built into `%TEMP%` without `ZOLA_HERMES_ROOT` cannot find Hermes (S51F-FIX). Rollback by “launch the previous tag” is **not** safe against current stores without a coordinated data+pin restore.

## Evidence

### 1. How everyday Zola is launched

| Item | Finding | Label |
|---|---|---|
| Running image | Pid **48536**, path `C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\bin\Debug\net9.0-windows10.0.19041.0\Zola.Client.exe` | OBSERVED |
| Command line | That path only (no extra args) | OBSERVED |
| Startup folder | No `*Zola*` / `*Hermes*` entries under user Startup | OBSERVED |
| Start Menu / Desktop `.lnk` | No dedicated Zola client shortcut found under Start Menu / Desktop / OneDrive Desktop (depth-limited); Recent has many `zola*` doc links, not a launch target | OBSERVED |
| Scheduled tasks | None matching `zola` / `Zola` / `Hermes` | OBSERVED |
| How it was built | Debug output under the repo (`bin\Debug\net9.0-windows10.0.19041.0\`); typical `dotnet build` / IDE F5 against the working tree. Exact Brian click-path (Explorer vs Visual Studio vs Cursor terminal) **UNVERIFIED** without asking him | INFERENCE + UNVERIFIED |

`App.OnLaunched` creates `HermesProcessManager`, mints a phone launch secret, starts watcher and phone, then `StartBackendAsync` (`App.xaml.cs` 21–43). SOURCE.

### 2. How the client finds Hermes and the profile

**Hermes root** — `HermesLaunchResolver.ResolveHermesRoot` (`HermesLaunchResolver.cs` 67–95):

1. `ZOLA_HERMES_ROOT` if it contains `hermes_cli\main.py`
2. Else walk parents of `Environment.CurrentDirectory` and `AppContext.BaseDirectory` for `hermes-agent` (or parent’s sibling `hermes-agent`) with the same marker

**Python** — `ResolvePython` (31–64): `ZOLA_HERMES_PYTHON` → `{hermesRoot}\.venv\Scripts\python.exe` → PATH `python.exe` (skipping WindowsApps).

**Profile** — hard-coded in `HermesProcessManager` ctor (40–44):

`%LOCALAPPDATA%\hermes\profiles\zola` (`SpecialFolder.LocalApplicationData` + `hermes\profiles\` + `ZolaServeCommand.ProfileName` = `"zola"`). Set as `HERMES_HOME` on serve spawn (245). SOURCE.

**S51F TEMP NOT_FOUND** — `S51F-FIX_Progress.md`: Release build to `%TEMP%\zola-s51f-fix-client-build`, `ZOLA_HERMES_ROOT` unset; discovery from TEMP cannot find sibling `hermes-agent` → watcher/phone `resolve_failed`, serve `keeps_failing`. From `C:\Users\test\Dev\zola-windows` the checkout is found. SOURCE (progress record).

Serve command shape (`HermesProcessManager.SpawnAsync` 234–244):  
`python -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0` with cwd = hermes root. SOURCE.

### 3. Runtime dependencies outside the client folder

| Dependency | Path / how found | Shared across client copies? |
|---|---|---|
| `hermes-agent` checkout | `C:\Users\test\Dev\hermes-agent` (sibling of repo; pin `345cd2b…`) | **Yes** — any client that resolves the same root |
| Hermes `.venv` | `{hermesRoot}\.venv\Scripts\python.exe` | **Yes** |
| `uv` | On PATH (`…\WinGet\…\uv.exe`) — OBSERVED present; used by Hermes tooling, not by client spawn directly | Shared machine tool |
| Live profile | `%LOCALAPPDATA%\hermes\profiles\zola\` | **Yes** — hard-coded name `zola` |
| Profile plugins mirror | `%LOCALAPPDATA%\hermes\profiles\zola\plugins\` (on `PYTHONPATH` for watcher/phone via `PythonStart`) | Shared with profile |
| Fonts / `zola.glb` | Copied beside exe (`Zola.Client.csproj` Content) | Per build output folder |
| Deepgram TTS script | Profile `zola-tts\deepgram_tts.py` (command in `VOICE_CONFIG.md` / live `config.yaml`) | Profile-scoped; script invokes absolute venv python |
| Deepgram key file | `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` (hard-coded in `deepgram_tts.py`) | **Yes** — escapes profile |
| `ffplay` | On PATH (`…\WinGet\Links\ffplay.exe`) — OBSERVED | Shared machine tool |
| Windows App SDK / .NET 9 | Framework-dependent unpackaged WinUI | Machine runtime |

### 4. Build / publish options (no build run)

SOURCE `Zola.Client.csproj`:

- `OutputType` WinExe; `net9.0-windows10.0.19041.0`; `Platforms` x64; `RuntimeIdentifiers` **win-x64**
- `WindowsPackageType` **None** (unpackaged)
- No `.pubxml` found under `windows-client`
- No `SelfContained` / `PublishSingleFile` properties set → default **framework-dependent**

S51F recorded:  
`dotnet build …\Zola.Client.csproj -r win-x64 -c Release -o %TEMP%\zola-s51f-fix-client-build` succeeded.

**What a `fix-s51f` folder copy would need to run identically (options / checklist, not a design):**

1. Built/published client bits + Content (fonts, GLB)
2. Discoverable Hermes: either live next to a tree that has sibling `hermes-agent`, or set `ZOLA_HERMES_ROOT` / `ZOLA_HERMES_PYTHON`
3. Same pin + venv packages the live profile expects
4. Live profile still at hard-coded `profiles\zola` unless client code changes
5. `ZolaClient` secrets/logs/dumps paths unchanged
6. `ffplay` on PATH; WinAppSDK / .NET 9 present
7. Phone firewall / Tailscale / pairing keys under the profile

### 5. Shared-Hermes risk (options only)

Stable and dev would both resolve `C:\Users\test\Dev\hermes-agent` unless separated. What can change under that checkout during dev:

| Change | Effect on stable |
|---|---|
| `pip` / `uv` install into `.venv` | Stable’s serve/watcher/phone pick up new packages immediately |
| Move Hermes pin / checkout files | Import/behavior drift or break for stable |
| Edit pinned Hermes source in place | Same |
| Plugin code under profile `plugins\` mirror | Shared with profile, not the checkout — but deploy mirrors from the repo |

**Options (not decisions):** separate Hermes checkout+venv per build; read-only stable Hermes copy; pin+hash gate before stable start; refuse start if hermes HEAD ≠ recorded pin.

### 6. Rollback as a question

Target assumption “rollback = launch previous tag” vs current data:

| Store | Schema / format | Older build vs current data | Verdict |
|---|---|---|---|
| `proactive.db` | `SCHEMA_VERSION = 8`; `_migrate` **raises** if `current > SCHEMA_VERSION` (`proactive_store.py` 309–311; P10-WATCH: “Old code cannot run on schema 8”) | Older tag that only knows schema ≤7 **refuses** current DB | **UNSAFE** |
| `zola_memory.db` | `SCHEMA_VERSION = 2`; migrate refuses newer (`store.py` 25, 162–164) | Safe only if live still at ≤2 and older code supports that version; forward migrations one-way | **UNSAFE** if future bump; today at 2 → **UNVERIFIED** for tags that predate v2 |
| Hermes `state.db` | Hermes-owned under profile | Format depends on hermes pin; older client+newer pin or reverse | **UNVERIFIED** (needs pin/tag matrix) |
| `token.dpapi` | `TOKEN_VERSION = 1` (`auth.py`) | Likely readable if blob shape unchanged | **UNVERIFIED** |
| Phone `pc_key.bin` / peer | DPAPI under `phone\` | Key material independent of client tag; protocol `contract_version` mismatches can break link | **UNVERIFIED** / protocol **UNSAFE** if contract diverges |
| `config.yaml` keys | Newer keys unknown to old Hermes may be ignored; removed defaults may reappear | Behavior drift | **UNVERIFIED** |
| hermes-agent pin + venv | Client from old tag + current pin | Mix can break | **UNSAFE** without matching pin |

P10-WATCH rollback note (SOURCE, progress): restore DB backup **and** old plugin mirror together; leaving new code migrates restored file forward again.

**Reliable rollback would need (inputs, not a design):** promotion-time backup of profile stores (at least `proactive.db`, `zola_memory.db`, `state.db`, tokens, phone keys, `config.yaml`), matching hermes pin+venv, and a client that still discovers that Hermes.

## Gaps against target state

| Target | Today | Gap |
|---|---|---|
| Stable in its own folder | Debug exe under working tree | No separate stable folder; everyday = editable tree |
| Dev isolated | Same profile + same Hermes | No isolation |
| Rollback = previous tag | Schema refuse-newer; shared pin | Tag alone is not a rollback |

## Open questions for Brian

1. How do you usually start Zola day to day (Explorer on the Debug exe, Visual Studio, a personal shortcut elsewhere, something else)?
2. Is a framework-dependent unpackaged folder acceptable for the first stable copy, or do you want self-contained publish?
3. Should the first stable folder keep sharing `C:\Users\test\Dev\hermes-agent`, or get its own copy from day one?
