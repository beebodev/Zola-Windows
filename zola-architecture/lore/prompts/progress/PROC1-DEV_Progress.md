# PROC1-DEV Progress

**Prompt:** `PROC1-DEV_Prompt_v1.1.md`  
**Prompt SHA-256:** `fdd93fc4756053040ec2cdf8978231c553ccaf80efc4f5780e12ffaf70b0c095` (verified match)  
**Plan:** `PROC1_BUILD_PLAN.md` v1.2 — Track PROC1-DEV, including "The window between ID and DEV"  
**Base:** `origin/main` @ `cfc0d353f385e6d805c0b596b86ddee92eb566d3`

## Locations

| Item | Value |
|------|-------|
| Live checkout | `C:\Users\test\Dev\zola-windows` (read-only until Phase 8) |
| Track worktree | `C:\Users\test\Dev\zola-windows-proc1-dev` |
| Work branch | `proc1-dev` |
| Stable | `C:\Users\test\Zola\stable\proc1-id\` (`current.txt` = `proc1-id`) |
| hermes-agent pin | `345cd2b057a452236de401d3534b8502a7465e8d` |

## Phase table

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Setup, baselines, facts | DONE | Accepted |
| 2 Design proposal | DONE | STOP — Brian's decisions recorded |
| 3 Implement | DONE | Accepted, with three exceptions applied in Phase 4 |
| 4 Review fixes | DONE | Accepted |
| 4b Credential and pairing | DONE | Accepted. Model sign-in is in providers |
| 5 Create the dev profile | DONE | Profile created. First auth add did not persist the pool |
| 6 First dev session | | |
| 7 Commit and merge | | |
| 8 Live checkout sync | | |
| 9 Promotion decision | | |
| 10 Closeout | | |

## Phase 1 — Setup, baselines, facts

### 1. Prompt / live / tag / hermes / stable running

| Item | Value |
|------|-------|
| Prompt SHA-256 | `fdd93fc4756053040ec2cdf8978231c553ccaf80efc4f5780e12ffaf70b0c095` — MATCH |
| Live branch | `main` |
| Live HEAD | `cfc0d353f385e6d805c0b596b86ddee92eb566d3` (`docs: record PROC1-ID closeout`) |
| Live status | clean; `main` == `origin/main` (no fetch; local refs already equal) |
| Tag `proc1-id` | annotated tag object `5b18111490d6d238a3c040f5b8a016302db6856d`; peels to `c8bc87724f6ffe4586a808678530ca88af96daaf` `Merge branch 'proc1-id'` |
| hermes-agent | `C:\Users\test\Dev\hermes-agent`, detached HEAD at pin; `git status --porcelain` empty |
| Stable client | **running** pid **23348**, path `C:\Users\test\Zola\stable\proc1-id\Zola.Client.exe`, started 2026-11-12 08:23:43. Serve command line includes `-p zola serve --isolated`. Watcher and `zola-phone` are up. Not started or stopped by this track. |

Live checkout rechecked after the worktree create: still `main`, clean, same SHA.

### 2. Worktree

Created: `git worktree add -b proc1-dev C:\Users\test\Dev\zola-windows-proc1-dev origin/main`.  
Worktree HEAD `cfc0d353f385e6d805c0b596b86ddee92eb566d3`, tracking `origin/main`.  
Live checkout unchanged. Leftover folders `zola-windows-proc1-id` and `zola-windows-proc1-stable` are still on disk from prior tracks; not used.

### 3. Baselines (worktree; stable Zola running)

| Suite | Command | Result | Floor |
|-------|---------|--------|-------|
| Client build | `dotnet build windows-client\Zola.Client\Zola.Client.csproj -c Release` | succeeded (0 errors, 2 CS8604 warnings in `VoiceController.cs`) | — |
| Checks | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` | **295 PASS / 0 FAIL**, exit 0. Coverage includes identity rows 24/24 | 295 |
| zola_workspace | venv `python -m unittest discover -s tests -t tests` (`PYTHONPATH`=hermes-agent) | **582 OK** (184.237s) | 582 |
| zola_memory | discover `-s tests -t .` | **162 OK** (29.752s) | 162 |
| zola_tools | discover `-s tests -t .` | **44 OK** (0.099s) | 44 |
| zola_tts | discover `-s tests -t .` | **8 OK** (0.378s) | 8 |
| zola_phone | discover `-s tests -t .` | **71 ran, 2 FAIL** (70.134s). See note | 71 with Zola closed |
| Kotlin | `android-companion\gradlew.bat testDebugUnitTest assembleDebug --offline` (`JAVA_HOME`=Android Studio JBR, `ANDROID_HOME`=`%LOCALAPPDATA%\Android\Sdk`) | **98** unit (15+39+30+14), 0 fail/error/skip; assembleDebug OK | 98 |
| Stable scripts | `tools\stable\Test-StableScripts.ps1` | **54 PASS / 0 FAIL** | 54 |

Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`.

**Phone note (expected while stable is up).** `test_f4_second_process_refuses_the_pipe_and_mutex` (`first.poll()` returned 2) and `test_isolation_on_the_real_startup_path` (no `zola_phone.start` log). Stable holds `Local\ZolaPhone`. G-NO-RESTART: Zola was not closed. Same two tests as PROC1-ID Phase 1. The closed-Zola floor of 71 OK is not claimed for this run.

**Stable scripts.** `prestable-head-differs-warning` passed with Zola running. The suite now includes `testmode-prepare-ignores-real-zola`.

### 4. Path inventory (SOURCE, file:line)

Every persistent location below is hardcoded to the live stable world. Nothing in the client reads a build role when it builds a path. Classification:

- **Role-bound today, stable literals.** These are the locations W1 has to take from one authority.
- **Shared by design.** The single-instance status file, and the Deepgram key the plugin reads.
- **Follows the profile directory.** Watcher and phone output logs are under whatever `ProfileDirectory` is.

Startup order in `OnLaunched` (`App.xaml.cs:26–97`), after the lock is held: role line (`IdentityLog` → `supervisor.log`) → status file → `DumpPruner` → `HermesProcessManager` → phone secret → watcher and phone objects → window → watcher start, phone start, backend start. The role line, the status file, and the dump prune run before any profile check. `Directory.CreateDirectory(ProfileDirectory)` is later, inside backend start (`HermesProcessManager.cs:100–101`).

| Site | Path | Holds | Access | Class |
|------|------|-------|--------|-------|
| `HermesProcessManager` ctor `HermesProcessManager.cs:40–44` | `%LOCALAPPDATA%\hermes\profiles\` + `ZolaServeCommand.ProfileName` (`"zola"`) | profile directory | read the string in the ctor; **write** `CreateDirectory` at start (`:101`); read `SOUL.md` at `:538` | role-bound |
| `ZolaServeCommand.ProfileName` `HermesLaunchResolver.cs:109` | the name `zola` | serve `-p` argument (`HermesProcessManager.cs:245–246`) | passed to the child | role-bound |
| `HermesProcessManager` spawn `HermesProcessManager.cs:254` | same profile directory | `HERMES_HOME` for serve | env on the child | role-bound |
| `PythonStart.Build` `PythonStart.cs:30–34` | `profileDirectory` and `profileDirectory\plugins` | `HERMES_HOME` and `PYTHONPATH` for watcher (`zola_workspace.watcher`) and phone (`zola_phone`) | env on the child | follows profile |
| `SupervisedPython` `SupervisedPython.cs:37` | `profileDirectory\logs\` + `zola_watcher.out.log` or `zola_phone.out.log` (`SupervisionConstants.cs:40–41`) | watcher and phone stdout/stderr | write | follows profile |
| `VoiceController.RecordWakeModelLanding` `VoiceController.cs:4413–4418` | `%LOCALAPPDATA%\hermes\profiles\zola\cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01\tokens.txt` (`WakeModelRelativePath` at `:225`) | wake-word token file presence, written into the timeline as a path or `missing` | read | role-bound (literal `zola`) |
| `VoiceController.WriteTimeline` `:3643–3645` | `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` | one line per spoken turn | write | role-bound |
| `ServerRequestBroker.WriteLogCore` `:866–869` | `%LOCALAPPDATA%\ZolaClient\logs\server-requests.log` | approval / clarify / code-read events | write | role-bound |
| `ChatSocket.WriteToolRiskLog` `:831–836` | `%LOCALAPPDATA%\ZolaClient\logs\tool-events.log` | tool risk lines | write | role-bound |
| `ZolaDisplayState.WriteDisplayLog` `:603–609` | `%LOCALAPPDATA%\ZolaClient\logs\display-state.log` | display-state facts | write | role-bound |
| `MainWindow.WriteDockLog` `MainWindow.xaml.cs:3094–3100` | same `display-state.log` | dock lines | write | role-bound |
| `MainWindow.CodeRead.WriteCodeLog` `MainWindow.CodeRead.cs:72–76` | `%LOCALAPPDATA%\ZolaClient\logs\code-read.log` | code-read UI log | write | role-bound |
| `ProactiveSpeechSession.WriteLogFile` `Speech\ProactiveSpeechSession.cs:303–308` | `%LOCALAPPDATA%\ZolaClient\logs\proactive.log` | proactive speech lines | write | role-bound |
| `SupervisionLog.WriteLine` `Supervision\SupervisionLog.cs:61–68` | `%LOCALAPPDATA%\ZolaClient\logs\supervisor.log` | supervisor, identity, and drift lines | write (create directory) | role-bound |
| `ServeStderrLog` default `ServeStderrLog.cs:28–34`, used by serve `HermesProcessManager.cs:20` | `%LOCALAPPDATA%\ZolaClient\logs\serve-stderr\serve-stderr.log` | serve stderr | write | role-bound |
| `DumpPruner.PruneOnStartup` `DumpPruner.cs:10–13` | `%LOCALAPPDATA%\ZolaClient\dumps` | expired dump files | delete when present; no create if absent | role-bound |
| `DriftChecker.TryWritePackagesCapture` `Identity\DriftChecker.cs:231–239` | `%LOCALAPPDATA%\ZolaClient\logs\drift-pip-freeze-<timestamp>.txt` | pip-freeze capture when packages drift (stable role only starts the check) | write | role-bound |
| `PresenceView.WriteLog` `Presence\PresenceView.cs:1118–1124` | `%LOCALAPPDATA%\ZolaClient\logs\presence.log` | presence log | write | role-bound |
| `PresenceView` look watcher / reload / effective dump `:424–427`, `:469–473`, `:511–515` | `%LOCALAPPDATA%\ZolaClient\debug\presence-look.json` (read), `presence-look.effective.json` (write) | debug look | read and write | role-bound, **DEBUG only** (`#if DEBUG`) |
| `PresenceAnimator.DebugPath` `:411–417`, used at `:290` and `:298` | `%LOCALAPPDATA%\ZolaClient\debug\presence-life.defaults.json` (write), `presence-life.json` (read) | debug life | read and write | role-bound, **DEBUG only** |
| `InstanceStatusFile.DefaultPath` `Identity\InstanceStatusFile.cs:11–15` with `IdentityConstants.cs:7–8` | `%LOCALAPPDATA%\Zola\run\instance.json` | role, tag, pid, exe, started_at | write after the lock is held; read by a refusing instance | **shared by design** (one Zola) |
| Deepgram key (plugin, not the client) `hermes-plugins/zola_tts/deepgram_tts.py:22` | `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` | API key file | read | **shared by design** (D5) |

`IdentityConstants.MutexName` is `Local\ZolaClient` (`IdentityConstants.cs:6`). That is a mutex name, not a directory.

No other `SpecialFolder.LocalApplicationData` use in `windows-client/Zola.Client`. `ZOLA_HERMES_PYTHON` and `ZOLA_HERMES_ROOT` (`HermesLaunchResolver.cs:34`, `:70`) select the Hermes checkout, not a data root.

`Zola.Client.Checks/DriftDryRun.cs:29–34` defaults its `--profile` argument to `profiles\zola`. That is a checks tool, not the running client.

#### Process scan for a running serve

| Site | What it matches | Profile check |
|------|-----------------|---------------|
| `HermesProcessManager.FindDedicatedServeAsync` `HermesProcessManager.cs:482–515` | WMI `CommandLine LIKE '%--isolated%'`, then `ZolaServeCommand.IsDedicatedServe` | the hardcoded `zola` flag only |
| `HermesProcessManager.Supervision.FindDedicatedServePids` `HermesProcessManager.Supervision.cs:109–125` | same query and same `IsDedicatedServe` | same. Used by `KillGenerationForRestart` (`:47–50`) and `IsServeProcessAlive` (`:62`) |
| `TtsPlaybackMonitor.DiscoverServePidByCommandLine` `Presence\TtsPlaybackMonitor.cs:628–654` | `python.exe` whose command line contains `hermes_cli.main`, `serve`, and `--isolated`. Returns the first hit | **none** |
| `ChildPidLookup` `Supervision\ChildPidLookup.cs:149–150` | children by `ParentProcessId` | none; not a serve-identity scan |

`IsDedicatedServe` (`HermesLaunchResolver.cs:113–131`) requires all of: `serve`, `--isolated`, `127.0.0.1`, and `ProfileFlag`.

`ProfileFlag` (`HermesLaunchResolver.cs:141–142`):

```
(?:^|\s)(?:-p|--profile)(?:=|\s+)zola(?:\s|$)
```

IgnoreCase. Checked against sample command lines: `-p zola` and `--profile=zola` match. `-p zola-dev`, `--profile=zola-dev`, and `--profile zola-dev` do not. The token `zola` has to end on whitespace or end-of-string, so the hyphen in `zola-dev` keeps it out.

Consequence for W4b: discovery, attach, and kill-before-restart are aimed at the literal profile `zola`. A process whose flag is `-p zola-dev` is invisible to them. A dev build that still used this code would attach to and kill a stable `-p zola` serve, and would miss its own serve. The playback monitor will take the first isolated `hermes_cli.main serve` it sees, whichever profile that is. None of the scans read `HERMES_HOME`.

### 5. Hermes profile facts (pin `345cd2b`, SOURCE)

**How serve picks a profile.** `hermes_cli/main.py` `_apply_profile_override` (`:508–556`) runs before other Hermes imports.

- It scans argv for `-p` / `--profile` / `--profile=` (`_scan_profile_flag`, `:419–446`). A name must match `^[a-z0-9][a-z0-9_-]{0,63}$` (`:401`). `zola-dev` matches.
- When a flag is present, `resolve_profile_env` (`hermes_cli/profiles.py:1789–1813`) computes the directory and **assigns `HERMES_HOME` to that directory**, replacing whatever was already in the environment.
- The root used for that computation: if `HERMES_HOME` is already set and its parent folder is named `profiles`, the root is the grandparent. Otherwise the root is the existing `HERMES_HOME`, or the platform default when the variable is unset. On Windows the platform default is `%LOCALAPPDATA%\hermes` (`hermes_constants.py:45–51`).
- So if the client passed `HERMES_HOME=...\profiles\zola-dev` and `-p zola`, Hermes would set `HERMES_HOME` to `...\profiles\zola` (the `-p` name), and exit 1 if that directory is missing (`FileNotFoundError`, `main.py:540–544`). The flag and the variable are forced onto the same directory. They cannot stay in disagreement once `-p` is present.
- When **no** flag is present and `HERMES_HOME` already points at a child of a `profiles` folder, the function returns immediately and keeps that value (`main.py:518–520`). The sticky `active_profile` file is not read on that path. Zola's serve spawn always passes `-p`, so the sticky file is not what selects the profile.

**Creating a profile.** `-p` accepts any existing directory that is not tombstoned (`profiles.py:1811–1812`; tombstone is `profiles\.deleted\<name>`, `hermes_constants.py:254–259`). A Hermes `profile create` command is not required. A plain folder is enough for the flag to resolve.

`hermes profile create` (`profiles.py:830–900`) is what seeds a full layout: `_PROFILE_DIRS` = `memories`, `sessions`, `skills`, `skins`, `logs`, `plans`, `workspace`, `cron`, `home` (`:29`); a placeholder `.env`; `SOUL.md`; and, with no clone source, `_seed_model_config`.

On later `load_config`, `ensure_hermes_home` (`hermes_cli/config.py:634–648`) refuses a missing or tombstoned named profile (`assert_named_profile_home_live`). When the directory already exists it creates `cron`, `sessions`, `logs`, `logs/curator`, `memories`, `pairing`, `hooks`, `image_cache`, `audio_cache`, `skills` (`_HERMES_HOME_SUBDIRS`, `:629–631`) and writes a default `SOUL.md` when that file is missing (`config_home.py:43–62`). It does not create the profile directory itself, and it does not write `config.yaml`.

**Plugins.** Both a folder and a config key.

- Directory scan: `$HERMES_HOME/plugins/` (`plugins_discovery.py:151–153`), manifests `plugin.yaml` / `plugin.yml` (or `plugin.json`). Bundled plugins under the Hermes checkout are scanned too.
- Enable gate: `plugins.disabled` wins; then `plugins.enabled` is an allow-list (`plugins_discovery.py:80–99`, `gate_manifest` `:173–218`). A user plugin whose name is absent from `plugins.enabled` is skipped. Bundled backends load on their own.
- Exclusive plugins (memory providers) are not turned on by `plugins.enabled`. The comment in `gate_manifest` says they activate via `<category>.provider`. The live profile sets `memory.provider: zola_memory`.
- `zola_phone` is not in `plugins.enabled`. The client starts it as `python -m zola_phone` with `PYTHONPATH` = `<profile>\plugins` + Hermes root (`PythonStart.cs:33–34`). The package has to be on that path. It is a process module, not an enabled Hermes plugin entry.

### 6. Model sign-in (names only; no secret file opened)

Live `config.yaml` `model.provider` is `openai-codex`. `model.default` is `gpt-5.6-terra`. `model.base_url` is present; the value was not recorded. There is no `.env` in the profile. `auth.json` is present in the profile (4141 bytes). `%LOCALAPPDATA%\hermes\auth.json` (the global root store) is absent. `.anthropic_oauth.json` is absent.

`openai-codex` is OAuth, not an API key. Source lists it with the single-use refresh providers (`hermes_cli/auth_oauth_grants.py:19–25`: `anthropic`, `openai-codex`, `xai-oauth`). Redeeming the refresh token rotates the pair and revokes the old one (`refresh_token_reused` / `invalid_grant`). `agent/credential_pool.py:706–710` names `nous`, `openai-codex`, and `xai-oauth` as rotating on refresh, and writes the new chain back to the store the grant was resolved from. Two profiles that share one copy can invalidate each other. A profile that reads the live file in place and then refreshes writes the new token back.

`read_credential_pool` (`hermes_cli/auth.py:858–882`): the profile's own `credential_pool` entries win. When the profile has zero entries for a provider, the global-root `auth.json` is a read-only fallback. On this machine that root file is absent, so the live grant has nowhere to sit except the profile `auth.json`. The file was not opened.

When the credential is missing:

- Interactive `hermes` chat (`cmd_chat`, `main.py:1694–1700`) calls `_first_run_setup_guard`: a TTY offers `hermes setup`; no TTY exits 1 (`:1611–1640`).
- `serve` does not call that guard. The serve parser (`hermes_cli/subcommands/dashboard.py`) shares `cmd_dashboard` and has no setup prompt.
- A Codex refresh with no refresh token ends in `codex_auth_missing_refresh_token`, `relogin_required` (`auth.py:1774–1775`).
- The pool fallback described above is the only cross-location read. It does not point at `profiles\zola` by name. It points at the Hermes root `auth.json`, which is a different directory from the Zola profile.

### 7. Google facts (SOURCE; token file not opened)

Connection is `python -m zola_workspace.setup` (`hermes-plugins/zola_workspace/setup.py`). `--client-json` is the Desktop OAuth client JSON. Omit it only to repeat setup from `client_id` / `client_secret` already inside the DPAPI store (`auth.py:704–721`). The recorded invocation path, from `P8-CONNECT_Progress.md`, is `C:\Users\test\Documents\zola-oauth\client-secret_zwindows.json`. That file is present (409 bytes). It was not opened. Setup reads `client_id` and `client_secret` from the JSON (`installed` or `web`), then Google's browser consent chooses the account (`auth.py:415–424`, `:656–721`). The JSON is the app client. The account is whichever Google account finishes consent.

Token path: `get_hermes_home() / "zola_workspace" / "token.dpapi"` (`auth.py:26–27`, `:227–236`). Under the live profile that file exists (926 bytes). Contents were not opened, printed, or hashed.

Empty store: `load_token_record` returns `None` when the file is missing (`:342–343`). `store_status` then reports `connected: False` and `needs_reconnect: "missing_store"` (`:371–375`). `refresh_access_token` raises `RuntimeError("missing_store")` (`:761–763`). There is no second path, no read of another profile, and no Windows Credential Manager API. The blob is DPAPI `CryptProtectData` of that one file (`:294–301`), user scope, `optionalEntropy=None`.

The refresh lock name is `Local\ZolaOAuthRefresh` (`auth.py:37`). One name for every profile of this Windows user. That is a shared mutex, not a shared token.

A dev profile needs: `HERMES_HOME` (and `-p`) pointed at `zola-dev`, the same client JSON passed to setup, and Brian completing consent as the test account. An empty `zola-dev\zola_workspace\token.dpapi` stays "not connected".

### 8. Phone facts

**Tools when `zola-phone` is down.** Phone tools are registered by `zola_workspace` (`__init__.py:205–213`: `phone_read_texts`, notifications, `phone_read_code`), which is in `plugins.enabled`. They are not registered by the `zola_phone` plugin entry. `phone_client.call` (`phone_client.py:20–33`) catches a failed pipe open and returns `phone_unavailable` / `no_connection`. The sentence is "I can't reach your phone right now." (`phone_tools.py:50`). There is no fallback store (`phone_tools.py:5–6`). If `zola_phone` cannot be imported, the same exception path applies.

**Could a dev serve reach a stable `zola-phone`?**

| Name | Value | Source |
|------|-------|--------|
| Pipe | `\\.\pipe\ZolaPhone` | `contracts/phone_protocol.json` `pipe_name` |
| Mutex | `Local\ZolaPhone` | `zola_phone/__main__.py:16`. Second process returns `EXIT_ALREADY_RUNNING` (`:55–56`) |
| Listen port | `47821` | protocol `listen_port` |
| Launch secret | env `ZOLA_PHONE_LAUNCH_SECRET`, removed from the phone environment after read (`__main__.py:49–51`). The client mints 32 random bytes per launch (`App.xaml.cs:65`) and passes it to serve and to phone | |
| Requests that require the secret | `code.arm`, `code.disarm`, `code.redeem`, `diagnostic_read`, `pairing.start`, `read_code`, `read_history`, `read_notifications` | protocol `local_requests` |
| Request that does not | `status` | same |

A wrong secret gets `reason=unauthorized` (`runtime.py:236–246`). Message reads need the secret of the phone process that holds the pipe. `status` does not.

`Local\ZolaClient` (`IdentityConstants.MutexName`) is the client single-instance lock. A second Zola client does not start while one is running, so a dev client and the stable client are not up together. The phone mutex and the pipe name are not role-specific (that split is out of scope). The phone process also exits when its parent pid is gone (`__main__.py:35–46`).

**fake_phone.** `hermes-plugins/zola_phone/tools/fake_phone.py` is a websocket client. It requires `--home`, `--host`, `--port`, and `--code`, and it pairs to a listener that is already running (`:274–282`). It generates its own key under `--home` and does not read the live PC key. It does not replace `zola-phone` or the named pipe. **No**: it cannot serve an interactive dev session on its own. Evidence is that entry point.

### 9. Deepgram

`deepgram_tts.py:22` sets `KEY_PATH` to `C:\Users\test\AppData\Local\ZolaClient\secrets\deepgram_api_key`. The module docstring says the key is read from that file and never from the environment (`:3–4`). `read_key` (`:37–45`) reads the file. The live secrets directory contains that filename. The file was not opened.

The client sets no Deepgram variable. Serve's environment is `HERMES_HOME`, `HERMES_DASHBOARD_SESSION_TOKEN`, `PYTHONUNBUFFERED`, `ZOLA_PHONE_LAUNCH_SECRET` when non-empty, `PYTHONPATH`, and `PYTHONFAULTHANDLER` (`HermesProcessManager.cs:254–262`). Live `config.yaml` runs the script as a TTS command provider:

`tts.provider=deepgram`, and `tts.providers.deepgram.command` is the Hermes venv `python.exe` plus `...\profiles\zola\zola-tts\deepgram_tts.py` with `{input_path} {output_path} {model} {speed}`.

That command is a child of serve, so it inherits serve's environment. The script still takes the key from the hardcoded file. The profile copy is `profiles\zola\zola-tts\deepgram_tts.py` (5596 bytes).

### 10. Live config facts (names and sizes only)

`config.yaml` top-level keys: `model`, `agent`, `approvals`, `plugins`, `_config_version`, `memory`, `stt`, `tts`, `voice`, `security`, `wake_word`, `platform_toolsets`, `known_plugin_toolsets`, `skills`, `desktop`, `proactive`.

Recorded settings (identifiers only): `model.provider=openai-codex`, `model.default=gpt-5.6-terra`, `plugins.enabled=zola_tools,zola_workspace`, `memory.provider=zola_memory`, `tts.provider=deepgram`. No value that looked like a key, token, or secret was printed. `auth.json`, `token.dpapi`, and the Deepgram key file were not opened.

Profile root (`%LOCALAPPDATA%\hermes\profiles\zola`), names only:

- Files: `.codex_gpt55_autoraise_notice`, `.skills_prompt_snapshot.json`, `.update_check`, `auth.json`, `auth.lock`, `config.yaml`, six `config.yaml.bak-*` files, `context_length_cache.yaml`, `essay_draft.txt`, `models_dev_cache.etag`, `models_dev_cache.json`, `proactive.db` (0 bytes), `projects.db`, `SOUL.md`, `SOUL.md.bak-P4-VOICE-20261001-091115`, `state.db`, `state.db-shm`, `state.db-wal`, two `state.db.*.lock` files, `zola_memory.db` (0 bytes).
- Directories: `.curator_backups`, `audio_cache`, `backups`, `cache`, `cron`, `desktop`, `hooks`, `image_cache`, `logs`, `memories`, `pairing`, `phone`, `plugins`, `proactive`, `runtime`, `sessions`, `skills`, `state`, `zola-tts`, `zola_memory`, `zola_workspace`.
- Not at the root: `MEMORY.md`, `USER.md`, `.env`.

`plugins\` children: `zola_memory`, `zola_phone`, `zola_tools`, `zola_workspace`. `zola_phone` is on disk and is not in `plugins.enabled`. `zola-tts\deepgram_tts.py` is present. `zola_workspace\token.dpapi` is present.

`%LOCALAPPDATA%\ZolaClient\` children: `debug`, `dumps`, `logs`, `secrets`.

Nothing under the live profile or `ZolaClient\` was written. No Zola process was started or stopped.

### Facts that change the shape of Phase 2 (recorded, not decided)

1. **Phone tools are part of `zola_workspace`.** Leaving `zola_phone` out of the dev profile removes the process module. The tools still register, and with no pipe they say "I can't reach your phone right now." A spoken "not available in dev" is a separate change from omitting the plugin.
2. **Serve discovery is hardcoded to `zola`, and that pattern does not match `zola-dev`.** Dev using today's scan would target a stable serve. The playback monitor has no profile check at all.
3. **`-p` overwrites `HERMES_HOME`.** Passing both, and passing the same profile name in both, is what keeps them from diverging.
4. **The model grant is single-use OAuth in the profile `auth.json`.** A shared copy or an in-place read can rotate the live token. Phase 2 item 5 is Brian's decision; the source evidence is in section 6.
5. **fake_phone cannot stand in for `zola-phone`.**

## Phase 1 complete

Accepted. Brian, verbatim: "Go with Claude's recommendations."

## Phase 2 — Design proposal

No client, plugin, or tool source is edited in this phase. Decisions below are the ones Brian sent for this phase.

| Decision | Choice |
|----------|--------|
| Model sign-in | (a) Own Codex sign-in in `zola-dev\auth.json`. Same account, new grant. No copy, no in-place read. |
| Fail-closed pop-up | One fixed sentence per reason. Title `Zola`. |
| Copied from live | `config.yaml` and `SOUL.md` only, byte copy, hashes listed. |
| Phone | Client never starts `zola-phone` in dev. Tools stay in `zola_workspace` and answer "I can't reach your phone right now." No plugin change. `zola_phone` stays out of the dev profile. The plan's "not available in dev" is met by that reply. SM-DEV5 passes on it. |
| fake_phone | No. |
| Access observation | Process Monitor, only if Brian approves the download from Microsoft Sysinternals and an administrator run for the Phase 6 session. Capture deleted afterwards. |
| Discovery | Profile-flag match takes this build's profile name. Playback monitor gets the same check. |

### 1. Path authority (W1)

One class, `ClientPaths`, built once in `OnLaunched` immediately after `BuildRole.Resolve`. Every persistent location from Phase 1 item 4 is a property of that object. Call sites stop calling `SpecialFolder.LocalApplicationData` and stop embedding `ZolaClient` or a profile name.

| Property | Stable | Dev |
|----------|--------|-----|
| `ProfileName` | `zola` | `zola-dev` |
| `ProfileDirectory` | `%LOCALAPPDATA%\hermes\profiles\zola` | `%LOCALAPPDATA%\hermes-dev\profiles\zola-dev` (D4 amendment, Phase 6c; the name stays `zola-dev`) |
| `ClientDataRoot` | `%LOCALAPPDATA%\ZolaClient` | `%LOCALAPPDATA%\ZolaClient-dev` |
| `LogsDirectory` | `ClientDataRoot\logs` | same shape |
| `DumpsDirectory` | `ClientDataRoot\dumps` | same shape |
| `TimelineDirectory` | `LogsDirectory` (today's timeline, display-state, tool-events, code-read, proactive, presence, and supervisor files) | same shape |
| `DebugDirectory` | `ClientDataRoot\debug` | same shape |
| `SecretsDirectory` | `ClientDataRoot\secrets` | `ZolaClient-dev\secrets` (empty; not the live key) |
| `DeepgramKeyPath` | `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` | the same path, marked read-only |

Serve gets `ProfileName` as `-p` and `ProfileDirectory` as `HERMES_HOME`. Watcher and phone output logs stay under `ProfileDirectory\logs`. The status file stays `%LOCALAPPDATA%\Zola\run\instance.json` inside `InstanceStatusFile` only.

D4 amendment, Phase 6c. Brian's verbatim approval: "Approved." Option (a): the profile name stays `zola-dev`. The Hermes root for dev is `%LOCALAPPDATA%\hermes-dev`, so the dev profile is `%LOCALAPPDATA%\hermes-dev\profiles\zola-dev`. The stable path plan is unchanged. The dev root-auth check is `%LOCALAPPDATA%\hermes-dev\auth.json`. A dev profile that resolves under the native `%LOCALAPPDATA%\hermes` refuses. `Move-DevProfile.ps1` moved `hermes\profiles\zola-dev` to that directory after Brian closed stable. The move hashes matched.

A source check fails if any file under `windows-client/Zola.Client/` other than `ClientPaths.cs`, `Identity\InstanceStatusFile.cs`, and `Identity\IdentityConstants.cs` uses `SpecialFolder.LocalApplicationData` or the literal `ZolaClient`. Profile names `zola` and `zola-dev` as path segments live only in `ClientPaths.cs`. `IdentityConstants.MutexName` (`Local\ZolaClient`) stays, because it is the one shared mutex, not a directory.

### 2. Fail-closed start (W2)

One order for both roles, so a dev refusal cannot write:

1. Take `Local\ZolaClient` (unchanged PROC1-ID). On refusal, the existing pop-up, then exit. No path write.
2. Resolve the role.
3. Build `ClientPaths`.
4. Dev only: run validation. On failure, pop-up, release the lock, exit. Nothing written: no identity line, no status file, no dump prune, no profile create, no Hermes, no watcher, no phone, no window.
5. Only then: identity log line, status file, `DumpPruner`, Hermes manager, watcher, and (stable only) phone.

Stable skips step 4. Stable still writes the same files to the same paths. The identity line moves to after the plan exists, which does not change those paths.

Validation, in order, first failure wins:

| Check | Failure |
|-------|---------|
| `ProfileDirectory` exists, is a directory, and its link-resolved path is `%LOCALAPPDATA%\hermes\profiles\zola-dev` | missing, or not the dev profile (including the live profile) |
| Every plan path, after resolving links, is under `profiles\zola-dev` or `ZolaClient-dev`, except the exact `DeepgramKeyPath` | a path points at the live profile or `ZolaClient\` |
| No plan path, and no ancestor of it, is a junction or symbolic link whose target is inside `profiles\zola` or `ZolaClient\` | a link into a live root. The Deepgram file itself must not be a reparse point |
| `ProfileDirectory\plugins\zola_phone` does not exist | phone plugin present |
| Dev has its own `openai-codex` credential, or `%LOCALAPPDATA%\hermes\auth.json` does not exist | no dev credential while the Hermes root store exists |

The credential check opens only `zola-dev\auth.json`. It counts `credential_pool["openai-codex"]` entries and logs the count. It does not log a token, a label, or any other value. The root file is an existence check only. It is never opened. `profiles\zola\auth.json` is never opened. A missing or unreadable dev `auth.json` counts as no credential. Today the root file is absent, so a dev profile with no sign-in yet is allowed to start. After a root store appears, dev refuses until `zola-dev\auth.json` has at least one `openai-codex` entry. That is what blocks the pool fallback in `read_credential_pool`.

Pop-up title is `Zola`, same `MessageBoxW` as PROC1-ID (`NativeMessageBox`). The lock is released before exit.

Exact text:

1. Missing folder: `This dev build can't confirm it's using the dev profile, so it won't start. The zola-dev folder is missing.`
2. Any other folder, including the live profile: `This dev build can't confirm it's using the dev profile, so it won't start. The profile is not zola-dev.`
3. A plan path outside the dev roots: `This dev build can't confirm it's using the dev profile, so it won't start. A path points at the live profile or ZolaClient.`
4. A junction or symbolic link into a live root: `This dev build can't confirm it's using the dev profile, so it won't start. A path is a link into the live profile or ZolaClient.`
5. `plugins\zola_phone` present: `This dev build can't confirm it's using the dev profile, so it won't start. The dev profile contains the phone plugin.`
6. No dev model credential while the Hermes root `auth.json` exists: `This dev build can't confirm it's using the dev profile, so it won't start. Dev has no model sign-in of its own, and a shared Hermes sign-in is present.`

### 3. Backend discovery (W4b)

`ZolaServeCommand.IsDedicatedServe` takes this build's `ProfileName`. `ProfileFlag` becomes:

```
(?:^|\s)(?:-p|--profile)(?:=|\s+){escaped profile name}(?:\s|$)
```

The profile name is `Regex.Escape`'d. The same end boundary stays, so `zola` and `zola-dev` do not match each other in either direction.

`FindDedicatedServeAsync`, `FindDedicatedServePids`, and `TtsPlaybackMonitor.DiscoverServePidByCommandLine` all use that match. Where the process environment can be read (same user, `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`), `HERMES_HOME` must equal this build's `ProfileDirectory`. A readable `HERMES_HOME` that disagrees excludes the process. An unreadable environment leaves the command-line match in force.

A serve whose profile flag is the other name is not attached and not killed. One supervisor line per pid: `other_profile pid=<n> profile=<flag> action=ignored`. The command line is not logged.

### 4. Hermes profile selection

Dev serve, the watcher, and the drift check (stable only) all receive the same `ClientPaths` values.

Dev serve arguments: `-p zola-dev`, and `HERMES_HOME` set to `ProfileDirectory` before the process starts. Hermes then reassigns `HERMES_HOME` from `-p` (`main.py:552`). Because both name `zola-dev`, the reassignment is the same directory. The watcher uses `PythonStart`, which sets `HERMES_HOME` to that same directory and does not pass `-p`. Drift runs only for stable and keeps receiving the stable profile directory.

### 5. Model sign-in (option a)

Brian runs this himself, in his own window, after `New-DevProfile` has created `zola-dev` and before any dev Zola is started. Stable stays running. Cursor does not run the command, does not see the password, and does not record the device code or any token.

```
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes\profiles\zola-dev'
& 'C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe' -m hermes_cli.main -p zola-dev auth add openai-codex --type oauth
```

`-p zola-dev` is what selects the profile (`auth_commands.py:223–231`, `auth_codex.py:845–869`). The command prints a URL, `https://auth.openai.com/codex/device`, and a device code. Brian opens that URL and signs in to the same Codex account. The login function returns tokens to the caller and does not write `~/.codex/`. `auth add` stores the new grant with `pool.add_entry` under the active `HERMES_HOME`, which `-p` has set to `zola-dev`. The file is `zola-dev\auth.json`. `--type oauth` matches the default for this provider; it is written out so the command cannot fall through to an API-key prompt.

Before Brian presses Enter, record SHA-256 of `%LOCALAPPDATA%\hermes\profiles\zola\auth.json` and whether `%LOCALAPPDATA%\hermes\auth.json` exists. After the command prints `Added openai-codex OAuth credential`, hash the live file again and check the root file again. Pass: the live hash is unchanged, and the root file is still absent. Also record that `zola-dev\auth.json` exists and that `credential_pool["openai-codex"]` has a count of at least one. No token, label, or file contents.

Immediately after that, with stable still running, Brian asks it one ordinary question that does not send mail, send a text, or change the calendar. Stable answers as it does today. That shows the new grant did not revoke the live one.

`New-DevProfile` does not copy `auth.json` and does not create one.

### 6. Google (W3)

Nothing from the live token store is copied. `zola-dev\zola_workspace\` starts without `token.dpapi`. The OAuth client JSON stays at `C:\Users\test\Documents\zola-oauth\client-secret_zwindows.json`. It is the app client. The account is chosen in Google's window.

In SM-DEV3 Brian runs, himself:

```
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes\profiles\zola-dev'
& 'C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe' -m zola_workspace.setup --client-json 'C:\Users\test\Documents\zola-oauth\client-secret_zwindows.json'
```

He types the test-account password in Google's window. Setup writes `zola-dev\zola_workspace\token.dpapi` only (`auth.py:227–236`, `:704–721`).

The no-fallback test uses a temp `HERMES_HOME` with no token file: `load_token_record` returns none, `store_status` reports `connected: false` and `needs_reconnect: missing_store`, and the test's opened paths do not include `profiles\zola`. A source check requires the store path to be `get_hermes_home() / zola_workspace / token.dpapi` with no other profile segment.

### 7. No phone (W4)

A dev role does not construct `PhoneProcess` and does not call `Start`. It does not set `ZOLA_PHONE_LAUNCH_SECRET` on serve. Stable is unchanged.

`zola_phone` is not copied into `zola-dev`. Phone tools stay registered by `zola_workspace` (`__init__.py` registers `phone_read_texts`, notifications, and `phone_read_code`). With no pipe they return `no_connection`. The sentence is `I can't reach your phone right now.` (`phone_tools.py:50`). Unknown reasons, including `unauthorized`, use that same sentence (`phone_tools.py:180`). That sentence is the "not available in dev" behaviour. SM-DEV5 passes when Zola says it and does not claim to have checked texts. No `zola_phone` process, pipe connection, or phone log line.

If a stable `zola-phone` were still running, the pipe is `\\.\pipe\ZolaPhone` and the mutex is `Local\ZolaPhone`. `read_history`, `pairing.start`, `read_code`, and `code.redeem` require the launch secret (`runtime.py:241–246`; protocol `local_requests`). Dev does not have stable's secret, so `_secret_ok` fails and the phone returns `reason=unauthorized`. `status` does not require the secret. Text and notification reads go through `read_history` and `read_notifications`, which do.

fake_phone is not offered.

### 8. Deepgram (W5)

Environment variable: `ZOLA_DEEPGRAM_KEY_PATH`.

`deepgram_tts.py` reads that variable. When it is unset or empty, the path is today's file: `C:\Users\test\AppData\Local\ZolaClient\secrets\deepgram_api_key`. Stable does not set the variable, so stable keeps today's file. The dev client sets the variable to that same path on the serve process. The script still does not print the key.

### 9. Dev tools (W6)

`tools/dev/New-DevProfile.ps1`

Creates `%LOCALAPPDATA%\hermes\profiles\zola-dev` and `%LOCALAPPDATA%\ZolaClient-dev` (`logs`, `dumps`, `debug`, `secrets`). Refuses when `zola-dev` already exists unless `-Replace` is passed. `-Replace` deletes only those two confirmed dev folders, and only when `Local\ZolaClient` is free and no `Zola.Client.exe` is running. Any target whose resolved path is inside `profiles\zola` or `ZolaClient\`, or that passes through a junction or symlink into either, is refused before a write.

Byte-copied from the live profile, and only these:

| File | Why |
|------|-----|
| `config.yaml` | Provider, plugin enable list, memory provider, and TTS command. `plugins.enabled` is `zola_tools,zola_workspace`. `memory.provider` is `zola_memory`. |
| `SOUL.md` | Zola's identity file, approved for this copy. |

The script prints SHA-256 of each source and each destination. It does not print file contents.

Invented seed, written only under `zola-dev\memories\`. Entries use zola_memory's delimiter, a newline, `§`, a newline (`store.py:40`). No real names.

`memories\USER.md`:

```
[identity] The user's name is Casey Quinn.
§
[home] Casey lives in the made-up town of Northglass.
```

`memories\MEMORY.md`:

```
[person] Jordan Hale is Casey's invented neighbour and keeps bees.
§
[fact] Casey's favourite colour is slate.
§
[project] The demo codename is Paper Kite.
```

Left empty, and never copied from live: `auth.json`, `.env`, `sessions\`, `skills\`, `plugins\` (filled afterwards by sync), `pairing\`, `phone\`, `zola_workspace\token.dpapi`, `state.db`, `projects.db`, `proactive.db`, `zola_memory.db`, backups, caches, logs, and every other live file. `ZolaClient-dev\secrets` is empty.

`tools/dev/Sync-DevPlugins.ps1 -From <worktree>`

Copies `hermes-plugins/zola_workspace`, `zola_memory`, and `zola_tools` into `zola-dev\plugins\`, and `hermes-plugins/zola_tts/deepgram_tts.py` into `zola-dev\zola-tts\deepgram_tts.py`. It does not copy `zola_phone`. Comparison rules match the stable maps: recursive file hashes, the named exclude `zola_memory/l6_hold_guard.py`, and `tts_rel` `zola-tts/deepgram_tts.py`. The target is refused when it resolves into `profiles\zola` or passes through a link into a live root. `-Replace` on either script follows the same running-Zola and dev-folder rules.

`tools/dev/Test-DevIsolation.ps1`

While dev runs: the dev serve command line contains `-p zola-dev`, the dev watcher and serve environments have `HERMES_HOME` ending in `profiles\zola-dev`, no `zola-phone` process is running, and no dev pid has a command line containing `-p zola` as a finished token. Open-handle evidence is the Process Monitor capture below. The script does not download a second tool.

After dev closes: SHA-256 maps of the live profile and of `ZolaClient\` match the maps taken before the session. The shared Deepgram key is the only allowed content exception, and only if its hash is unchanged (it is read, not written).

**Process Monitor (Phase 6, only with Brian's approval).** Download from Microsoft Sysinternals, run as administrator for that session, then delete the capture. Filter: Path contains `\hermes\profiles\zola\` and does not contain `\hermes\profiles\zola-dev\`, or Path contains `\ZolaClient\` and does not contain `\ZolaClient-dev\`. Process is the smoke `Zola.Client.exe` under `%TEMP%\proc1-dev-smoke\` and the `python.exe` children of that process. Review columns: Process Name, PID, Operation, Path, Result. The Detail column is not kept. No file contents. Pass: no dev process has a successful CreateFile, ReadFile, or WriteFile under those live roots, except a read of `\ZolaClient\secrets\deepgram_api_key` if speech uses Deepgram. The capture file is deleted before the phase closes.

### 10. Stable unchanged (G-STABLE-SAME)

A check builds `ClientPaths` for the stable role and compares each full path, as a string, with this list:

| Plan field | Today's path |
|------------|----------------|
| Profile directory | `%LOCALAPPDATA%\hermes\profiles\zola` |
| Profile name | `zola` |
| Client data root | `%LOCALAPPDATA%\ZolaClient` |
| Logs | `%LOCALAPPDATA%\ZolaClient\logs` |
| Supervisor log | `%LOCALAPPDATA%\ZolaClient\logs\supervisor.log` |
| Serve stderr | `%LOCALAPPDATA%\ZolaClient\logs\serve-stderr\serve-stderr.log` |
| Voice timeline | `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` |
| Display state | `%LOCALAPPDATA%\ZolaClient\logs\display-state.log` |
| Tool events | `%LOCALAPPDATA%\ZolaClient\logs\tool-events.log` |
| Code read | `%LOCALAPPDATA%\ZolaClient\logs\code-read.log` |
| Proactive | `%LOCALAPPDATA%\ZolaClient\logs\proactive.log` |
| Presence | `%LOCALAPPDATA%\ZolaClient\logs\presence.log` |
| Drift capture directory | `%LOCALAPPDATA%\ZolaClient\logs` |
| Dumps | `%LOCALAPPDATA%\ZolaClient\dumps` |
| Debug | `%LOCALAPPDATA%\ZolaClient\debug` |
| Wake token | `%LOCALAPPDATA%\hermes\profiles\zola\cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01\tokens.txt` |
| Watcher output | `%LOCALAPPDATA%\hermes\profiles\zola\logs\zola_watcher.out.log` |
| Phone output | `%LOCALAPPDATA%\hermes\profiles\zola\logs\zola_phone.out.log` |
| Status file | `%LOCALAPPDATA%\Zola\run\instance.json` |
| Deepgram key | `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` |

The dev plan is a second assertion: the same fields with `zola-dev` and `ZolaClient-dev`, except the status file and the Deepgram key, which stay on the shared paths above.

### 11. Tests

- Dev path plan contains no live profile path and no `ZolaClient\` path except the Deepgram key.
- Source check: every call site uses `ClientPaths`, with the two documented exceptions.
- Dev start with `zola-dev` missing, with the profile pointed at the live folder, and with a plan path outside the dev roots: the matching pop-up text, and both roots unchanged.
- Dev start with no `openai-codex` entry while a temp Hermes-root `auth.json` exists: pop-up 6, live `auth.json` not opened.
- Empty Google store reports not connected, and the store path is only under that `HERMES_HOME`.
- Discovery: a `-p zola` serve is not attached or killed by a dev plan, a `-p zola-dev` serve is not attached or killed by a stable plan, `zola` does not match `zola-dev`, and the playback monitor ignores the other profile.
- A failed dev start writes nothing under the dev roots or the live roots.
- A junction from a dev path into the live profile is rejected by startup validation and by both dev scripts.
- `-Replace` refuses while `Local\ZolaClient` is held, and refuses any folder that is not the dev profile or `ZolaClient-dev`.
- Dev role does not start `zola-phone`. A read, pairing, and code-redeem request without the phone's secret is `unauthorized`.
- With `ZOLA_DEEPGRAM_KEY_PATH` unset, the key path equals today's path.
- `New-DevProfile` and `Sync-DevPlugins` refuse a live target and do not copy `auth.json`, tokens, sessions, databases, phone keys, pairing files, or `zola_phone`.
- Stable path plan equals the list in section 10.

## Phase 2 complete

STOP. Waiting for review before Phase 3. Review accepted with three additions. Those additions are in Phase 3.

## Phase 3 — Implement

Worktree only. Live checkout stayed on `main` at `cfc0d353f385e6d805c0b596b86ddee92eb566d3`, clean. Stable pid 23348 was still running at the end of the phase (started 2026-11-12 08:23:43). It was not started, stopped, or killed. No dev profile was created under the real `%LOCALAPPDATA%`. No commit.

### Review additions

1. After the byte copy of `config.yaml`, `New-DevProfile` rewrites only values whose text is under the live profile or `ZolaClient\`. The replacement is the matching prefix: `profiles\zola` to `profiles\zola-dev` (and the slash form), and `ZolaClient` to `ZolaClient-dev`. The boundary is strict, so `zola` does not match `zola-dev` and `ZolaClient` does not match `ZolaClient-dev`. Each change is printed as `config.yaml path before=` and `config.yaml path after=` (paths only). A path that lands in a live root only after a junction is resolved, and whose text does not contain the live root, cannot be mapped: the script refuses, deletes the partial dev tree, and leaves no config pointing at live. `Sync-DevPlugins` also places `zola_tts/deepgram_tts.py` at `zola-dev\zola-tts\deepgram_tts.py`.
2. The missing-folder sentence ends with `Set it up with tools\dev\New-DevProfile.ps1.`
3. All seven refusal sentences live in `windows-client/Zola.Client/Identity/DevProfileRefuse.cs`. A check asserts the seven values are distinct and that each `DevProfileFailure` maps to exactly one of them.

### Refusal sentences

Title `Zola` (`IdentityConstants.RefuseTitle`).

1. Missing folder: `This dev build can't confirm it's using the dev profile, so it won't start. The zola-dev folder is missing. Set it up with tools\dev\New-DevProfile.ps1.`
2. Not the dev profile: `... The profile is not zola-dev.`
3. A plan path points at live: `... A path points at the live profile or ZolaClient.`
4. A link into live: `... A path is a link into the live profile or ZolaClient.`
5. Phone plugin present: `... The dev profile contains the phone plugin.`
6. No own model sign-in while a shared Hermes sign-in exists: `... Dev has no model sign-in of its own, and a shared Hermes sign-in is present.`
7. Settings point at live: `... Its settings point at the live profile.`

### Startup

Both roles still take `Local\ZolaClient` first. Then the role is resolved and `ClientPaths` is built. Dev runs validation before `ClientPaths.Install`. A failure shows the sentence, releases the lock, and exits. Nothing is written, because log writers no-op until `Install`. Stable skips validation. The identity line, the dev credential count, the status file, `DumpPruner`, and `HermesProcessManager` run only after that. Dev does not mint a phone secret, does not construct `PhoneProcess`, and does not start `zola-phone`. The watcher still starts. Drift stays stable-only.

Validation, first failure wins: the profile directory exists and its link-resolved path is `%LOCALAPPDATA%\hermes\profiles\zola-dev`; every plan path is lexically under `profiles\zola-dev` or `ZolaClient-dev` except the exact Deepgram key; no plan path or ancestor is a junction or symlink into the live profile or `ZolaClient\`, and the Deepgram file itself is not a reparse point; `plugins\zola_phone` is absent; dev has its own `openai-codex` entry or `%LOCALAPPDATA%\hermes\auth.json` does not exist (that root file is `File.Exists` only); `config.yaml`, when present, contains no path into the live roots. A missing config is not a failure.

Serve discovery matches this build's profile name. `zola` does not match `zola-dev`. `TtsPlaybackMonitor` uses the same match. Another profile is not attached and not killed. Dev serve gets `ZOLA_DEEPGRAM_KEY_PATH` set to the shared key path. Stable does not set it. With the variable unset or empty, `deepgram_tts.py` still uses today's path.

`New-DevProfile` copies `config.yaml` and `SOUL.md` only, records both hashes, rewrites the config, and writes the invented `USER.md` and `MEMORY.md`. It does not create `auth.json`. `-Replace` refuses while Zola is running and refuses a destination that is not the dev profile or `ZolaClient-dev`.

### Counts (worktree; stable Zola running)

| Suite | Command | Result | Floor |
|-------|---------|--------|-------|
| Client build | `dotnet build windows-client\Zola.Client\Zola.Client.csproj -c Release` | succeeded, 0 errors, 2 CS8604 in `VoiceController.cs` (1698,31). Same warning as Phase 1; the line moved when the timeline path constants left that file | — |
| Checks | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` | **313 PASS / 0 FAIL**, exit 0. Identity rows 42/42 (Phase 1 was 24/24) | 295 |
| zola_workspace | venv `python -m unittest discover -s tests -t tests` | **582 OK** (102.814s) | 582 |
| zola_memory | discover `-s tests -t .` | **162 OK** (13.913s) | 162 |
| zola_tools | discover `-s tests -t .` | **44 OK** (0.024s) | 44 |
| zola_tts | discover `-s tests -t .` | **9 OK** (0.072s). The new test is the unset/empty Deepgram env | 8 |
| zola_phone | discover `-s tests -t .` | **71 ran, 2 FAIL** (34.142s). Same two tests as Phase 1. Floor not claimed | 71 with Zola closed |
| Kotlin | `android-companion\gradlew.bat testDebugUnitTest assembleDebug --offline` | **98** unit (15+39+30+14), 0 fail/error/skip; assembleDebug OK. Tasks were up to date; no Kotlin source changed | 98 |
| Stable scripts | `tools\stable\Test-StableScripts.ps1` | **54 PASS / 0 FAIL** (summary line) | 54 |
| Dev tools | `tools\dev\Test-DevTools.ps1` | **10 PASS / 0 FAIL**. Includes the rewrite, the unmapped refusal, sync of `deepgram_tts.py` to `zola-dev\zola-tts\`, and the two behavior tests | — |

The startup scan, the one-to-one sentence map, the junction refusal, and the "writes nothing" checks are in the Checks 313.

Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-DEV_Phase3.diff` (UTF-8, no BOM). New files are in the diff. Checked against `git status --porcelain`. Nothing is staged.

## Phase 3 complete

STOP. Waiting for review before Phase 4. Review accepted, with three exceptions. Those exceptions are Phase 4.

## Phase 4 — Review fixes

Worktree only. Live checkout stayed clean. Stable pid 23348 was still running at the end of the phase (started 2026-11-12 08:23:43). It was not started, stopped, or killed. No commit.

### Profile match

`ProcessEnvironmentReader` is removed. Attach, kill, and playback use the exact `-p` or `--profile` token only. `zola`, `zola-dev`, and `zola-devx` do not match each other. `--profile=zola` is `zola`. Another profile is logged once and is not attached and not killed. The dev client still sets `HERMES_HOME` on the serve it starts. It does not read another process's environment.

### Shared Deepgram key

A config value that is the shared key path `ZolaClient\secrets\deepgram_api_key` is left unchanged and reported as `kept (shared, D5)`. Other live paths are still rewritten. The startup scan ignores that same key path, so a kept key does not refuse the dev start. Any other `ZolaClient` path in config still refuses.

### `-Replace`

`New-DevProfile` and `Sync-DevPlugins` both call `Test-ZolaClientOrServeRunning`. With no probe it refuses while `Local\ZolaClient` is held, a `Zola.Client` process exists, `dotnet` is running `Zola.Client.csproj`, or a command line is `hermes_cli.main` with `serve`. A test injects the probe: `{ $true }` refuses and leaves the dev canary, `{ $false }` replaces even while the stable client is running.

### Counts (worktree; stable Zola running)

| Suite | Result | Floor |
|-------|--------|-------|
| Client Release build | succeeded, 0 errors, 2 CS8604 in `VoiceController.cs` (1698,31) | — |
| Checks | **314 PASS / 0 FAIL**, exit 0. Identity rows 43/43 | 295 |
| zola_workspace | **582 OK** (99.960s) | 582 |
| zola_memory | **162 OK** (15.684s) | 162 |
| zola_tools | **44 OK** (0.035s) | 44 |
| zola_tts | **9 OK** (0.173s) | 8 |
| zola_phone | **71 ran, 2 FAIL** (29.785s). Same two tests. Floor not claimed | 71 with Zola closed |
| Kotlin | **98** unit (15+39+30+14), 0 fail/error/skip; assembleDebug OK | 98 |
| Stable scripts | **54 PASS / 0 FAIL** | 54 |
| Dev tools | **12 PASS / 0 FAIL**. Includes the kept key report and the injected probe | — |

Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-DEV_Phase4.diff` (UTF-8, no BOM). New files are in the diff. Checked against `git status --porcelain`. Nothing is staged.

## Phase 4 complete

STOP. Waiting for review before Phase 5. Review accepted.

## Phase 5 — Create the dev profile

Stable pid 23348 stayed running (started 2026-11-12 08:23:43). No Zola was started or stopped. `New-DevProfile.ps1` then `Sync-DevPlugins.ps1 -From C:\Users\test\Dev\zola-windows-proc1-dev`. Neither used `-Replace`.

### Copied from live

Only `config.yaml` and `SOUL.md`. Copy hashes matched:

| File | SHA-256 |
|------|---------|
| config.yaml | `f5b4829410e4c89feb2832cfffab02ebfa978bdc283cdf65e490b15e33c938c3` |
| SOUL.md | `11e84261d6379c97164163e4927f6d60fb07d34070d03cf3004ccaa28da65ac5` |

The config path rewrite ran after that copy, so the file now in `zola-dev` is the rewritten copy. SOUL.md was not rewritten.

### config.yaml rewrite

One path. The shared key path is not in this config, so there is no `kept (shared, D5)` line.

- before: `C:\Users\test\AppData\Local\hermes\profiles\zola\zola-tts\deepgram_tts.py`
- after: `C:\Users\test\AppData\Local\hermes\profiles\zola-dev\zola-tts\deepgram_tts.py`

### Layout

`zola-dev` has 61 files. `ZolaClient-dev` has the empty directories `logs`, `dumps`, `debug`, and `secrets`.

| Path | Files | Bytes |
|------|-------|-------|
| config.yaml | 1 | 4878 |
| SOUL.md | 1 | 10587 |
| memories | 2 | 258 |
| plugins\zola_memory | 12 | 234959 |
| plugins\zola_tools | 3 | 17353 |
| plugins\zola_workspace | 41 | 799276 |
| zola-tts\deepgram_tts.py | 1 | 5875 |

No `auth.json`, `.env`, `token.dpapi`, `plugins\zola_phone`, `pairing`, or `phone` directory. Sync reported `synced 57` (the three plugins and `deepgram_tts.py`). `l6_hold_guard.py` is not present. The workspace plugin's phone tool sources are the repo copies, not live phone data.

### Invented seed

PowerShell 5.1 read the literal `§` in `DevCommon.psm1` as two characters, so the first write used `Â§`. The module and the tool test now build the delimiter with `[char]0x00A7`. The two files were rewritten in place. They match `\n§\n` (UTF-8 `C2 A7`):

`memories\USER.md` (100 bytes):

```
[identity] The user's name is Casey Quinn.
§
[home] Casey lives in the made-up town of Northglass.
```

`memories\MEMORY.md` (158 bytes):

```
[person] Jordan Hale is Casey's invented neighbour and keeps bees.
§
[fact] Casey's favourite colour is slate.
§
[project] The demo codename is Paper Kite.
```

### Live roots

Hash maps before and after the two scripts: profile 911 files, `ZolaClient` 25 files, delta 0. Sixteen files were not byte-compared because stable has them open. Both maps record them as locked, and the locked set did not change:

`state.db`, `state.db-shm`, `state.db-wal`, `logs\.__agent.lock`, `logs\.__errors.lock`, `logs\.__gui.lock`, `logs\zola_memory.log`, `logs\zola_phone.log`, `logs\zola_watcher.log`, `logs\zola_workspace.log`, `proactive\proactive.db`, `proactive\proactive.db-shm`, `proactive\proactive.db-wal`, `zola_memory\zola_memory.db`, `zola_memory\zola_memory.db-shm`, `zola_memory\zola_memory.db-wal`.

These are the serve's database and log files. This is partial evidence. The full byte check is Phase 6, with stable closed.

### Sign-in, before Brian runs it

`profiles\zola\auth.json` was not opened. SHA-256 `42af782dfec7f1ad7aab232960d969f94980c71f7adf2a711c60594aaf0276dc`, 4141 bytes. The hash is the same after the profile create. `%LOCALAPPDATA%\hermes\auth.json` is absent. `zola-dev\auth.json` does not exist.

### Sign-in, after Brian ran it

Brian reported the line `Added openai-codex OAuth credential`. Stable, still running, answered one ordinary question normally, with no issues. No mail, text, or calendar change was requested.

After-checks, 2026-11-12:

| Check | Result |
|-------|--------|
| Live `profiles\zola\auth.json` SHA-256 | `42af782dfec7f1ad7aab232960d969f94980c71f7adf2a711c60594aaf0276dc`, 4141 bytes. Unchanged. File not opened. |
| `%LOCALAPPDATA%\hermes\auth.json` | Absent. `%USERPROFILE%\.hermes\auth.json` is also absent. Neither file was opened. |
| `zola-dev\auth.json` `credential_pool["openai-codex"]` | **Count 0.** The key `credential_pool` is absent. `providers` is an empty object. `active_provider` is `openai-codex`. The file is 131 bytes, written 2026-11-12 10:26:19. |

The count check does not pass. The success line is printed after the in-memory pool add. For a single-use provider the pinned Hermes refuses to write a profile-local pool row when the profile does not already own one, and it does not create the root file either. The profile file only records the active provider.

The same command also created empty Hermes directories under `zola-dev` (`audio_cache`, `backups`, `cache`, `cron`, `hooks`, `image_cache`, `logs`, `pairing`, `sessions`, `skills`). `pairing` has no files. Two files were added: `backups\config\config.yaml.good.20261112-102454` (4878 bytes, the dev config) and `cache\oauth_heal_clean.json` (211 bytes, not opened).

## Phase 5 complete

STOP. The profile exists. The live auth hash is unchanged, the root auth file is absent, and the dev pool count is 0. Waiting for review before Phase 6.

## Model sign-in

Brian ran `hermes -p zola-dev model`, chose OpenAI Codex, declined the `~/.codex` import, finished the device sign-in, and picked a model. Stable answered one ordinary question normally. Stable pid 23348 was still running (started 2026-11-12 08:23:43).

After-checks, 2026-11-12:

| Check | Result |
|-------|--------|
| Live `profiles\zola\auth.json` SHA-256 | `42af782dfec7f1ad7aab232960d969f94980c71f7adf2a711c60594aaf0276dc`, 4141 bytes. Unchanged. File not opened. |
| `%LOCALAPPDATA%\hermes\auth.json` | Absent. |
| `%USERPROFILE%\.hermes\auth.json` | Absent. |
| `zola-dev\auth.json` `providers` / `openai-codex` | Present. The value is an object. 2208 bytes. No values read. |
| `credential_pool` / `openai-codex` | Length 0. The `credential_pool` key is absent. |
| Startup scan on dev `config.yaml` | No profile marker, no `ZolaClient` marker, no absolute path under the live profile or `ZolaClient\`. |
| Changed paths | None. |
| Changed config keys | `model.default` only. The file was rewritten (4878 bytes to 3712, written 2026-11-12 15:10:19). |
| `pairing` | Directory exists. 0 files. |
| `phone` | Directory absent. |
| Stable pid | 23348, `Zola.Client`, started 2026-11-12 08:23:43. |

## Phase 4b — Claude's review

Worktree only. Live checkout stayed clean. Stable was not started, stopped, or killed. No commit.

A dev credential is a `providers.openai-codex` object or a `credential_pool.openai-codex` row. The check uses presence only: an object counts as one, and a pool array counts by length. Token text is not read. A null block and an empty pool count as zero. A dev start still refuses with the existing no-model-sign-in sentence when that count is zero and `%LOCALAPPDATA%\hermes\auth.json` exists.

`zola-dev\pairing` or `zola-dev\phone` with any file, including a nested file, refuses. An empty folder is allowed. The new sentence is: "This dev build can't confirm it's using the dev profile, so it won't start. The dev profile contains phone pairing files."

### Counts (worktree; stable Zola running)

| Suite | Result | Floor |
|-------|--------|-------|
| Client Release build | succeeded, 0 errors, 2 CS8604 in `VoiceController.cs` (1698,31) | — |
| Checks | **321 PASS / 0 FAIL**, exit 0. Identity rows 50/50 | 295 |
| zola_workspace | **582 OK** (130.673s) | 582 |
| zola_memory | **162 OK** (19.080s) | 162 |
| zola_tools | **44 OK** (0.057s) | 44 |
| zola_tts | **9 OK** (0.340s) | 8 |
| zola_phone | **71 ran, 2 FAIL** (57.915s). Same two tests. Floor not claimed | 71 with Zola closed |
| Kotlin | **98** unit (15+39+30+14), 0 fail/error/skip; assembleDebug OK. Tasks were up to date | 98 |
| Stable scripts | **54 PASS / 0 FAIL** | 54 |
| Dev tools | **12 PASS / 0 FAIL** | — |

Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-DEV_Phase4b.diff` (UTF-8, no BOM). New files are in the diff. Checked against `git status --porcelain`. Nothing is staged.

## Phase 4b complete

STOP. Review accepted.

## model.default before Phase 6

Read-only. Nothing was written.

| Source | `model.default` |
|--------|-----------------|
| Dev backup `config.yaml.good.20261112-102454` | `gpt-5.6-terra` |
| Current dev `config.yaml` | `gpt-5.6-terra-900k` |
| Live `profiles\zola\config.yaml` | `gpt-5.6-terra` |

The backup is 4878 bytes and the current file is 3712 bytes (1166 bytes smaller). Both parse to 61 keys. The only key whose value differs is `model.default` (`gpt-5.6-terra` before, `gpt-5.6-terra-900k` after). Every other key and value matches, so the rest of the shrink is comments or formatting. The model name itself is 5 bytes longer.

Current dev `model.default` differed from stable. Brian then said to set dev back to `gpt-5.6-terra`.

The current file was copied to `config.yaml.bak-PROC1-DEV-20261112-153527` in the same folder (3712 bytes, `gpt-5.6-terra-900k`). The live file was then changed by replacing that one token. It is 3707 bytes. A byte compare with the backup differs only by those five characters. A key-by-key compare differs only in `model.default`, now `gpt-5.6-terra`, the same as stable. The startup scan finds no live path. Live `profiles\zola\auth.json` is still SHA-256 `42af782dfec7f1ad7aab232960d969f94980c71f7adf2a711c60594aaf0276dc`, 4141 bytes.

## Phase 6 — First dev session

Smoke build: `%TEMP%\proc1-dev-smoke\`. `dotnet build` Release, win-x64, 0 errors, the same CS8604 at `VoiceController.cs` (1698,31). WinUI check: `Zola.Client.pri`, `App.xbf`, `MainWindow.xbf`, `Themes\ZolaTokens.xbf`. Those are the three `.xaml` files. `Zola.Client.exe` is present.

Stable pid 23348 was still running after the build (started 2026-11-12 08:23:43). It was not closed. Process Monitor is downloaded to `%TEMP%\proc1-dev-procmon\` and has not been started. The before hash maps and SM-DEV1 are waiting for Brian to close stable.

Brian then closed stable. Confirmed before the hash maps: pid 23348 is gone, `Local\ZolaClient` and `Local\ZolaPhone` are free, and no `Zola.Client`, serve, or phone process is running.

Before hash maps, full byte hashes, nothing locked, no file outside its root:

| Root | Files | Map |
|------|------:|-----|
| `profiles\zola` | 914 | `%TEMP%\proc1-dev-maps\before-profile.clixml` |
| `ZolaClient` | 27 | `%TEMP%\proc1-dev-maps\before-client.clixml` |

`profiles\zola\auth.json` still matches the Phase 5 hash. Dev profile before the rename: 71 files, `%TEMP%\proc1-dev-maps\before-dev.clixml`. `ZolaClient-dev` exists and has 0 files, `%TEMP%\proc1-dev-maps\before-client-dev.clixml`.

Process Monitor is `Procmon64.exe`, started with administrator rights before the first dev start. Backing file `%TEMP%\proc1-dev-procmon\proc1-dev.pml`. Filter: process name `Zola.Client.exe` or `python.exe`; path contains `\hermes\profiles\zola\` or `\ZolaClient\`; path excludes `\hermes\profiles\zola-dev\` and `\ZolaClient-dev\`. Drop filtered events is on. The open capture has 0 events, which is the idle state before the smoke start. Review will keep the smoke exe under `%TEMP%\proc1-dev-smoke\` and its `python.exe` children, and will not keep Detail.

SM-DEV1 is set up: `profiles\zola-dev` is renamed to `profiles\zola-dev.off`. Waiting for Brian to start `%TEMP%\proc1-dev-smoke\Zola.Client.exe`.

SM-DEV1 pass. Brian started the smoke exe at 08:16:21. The pop-up he read back is the missing-folder sentence. After that start, all four roots match their before maps: live profile 914 files, `ZolaClient` 27, `zola-dev.off` 71, `ZolaClient-dev` 0 files. Nothing locked. The smoke folder has no file written at or after 08:16. The capture still has 0 events. The profile is renamed back to `zola-dev`. The smoke process pid 25544 was still up on the pop-up, holding `Local\ZolaClient`, when the profile was renamed back.

SM-DEV2 pass. Brian started the smoke exe again at 08:22:22, pid 12488. `ZolaClient-dev\logs\supervisor.log` (477 bytes, written 08:22:24) contains `identity role=dev why=missing tag=`, `identity dev_model_credentials openai-codex=1`, and `identity status_write ok`. Serve launcher pid 7928 and child pid 10676: command line is `hermes_cli.main -p zola-dev serve --isolated` on `127.0.0.1`. The child `HERMES_HOME` is `profiles\zola-dev`, and `ZOLA_DEEPGRAM_KEY_PATH` is the shared `ZolaClient\secrets\deepgram_api_key`. Watcher launcher pid 4520 and child pid 10640 run `zola_workspace.watcher`. The child `HERMES_HOME` is `profiles\zola-dev` and `PYTHONPATH` is that profile's `plugins` plus the Hermes checkout. No `zola-phone` process, no phone plugin, no phone log, and `Local\ZolaPhone` is free. No phone launch secret is set on the serve or watcher child. Brian asked what she remembers. She answered: "You're Casey Quinn. You live in Northglass, and your favourite colour is slate." Those three facts are in `zola-dev\memories\USER.md` and `MEMORY.md`. Live `auth.json` still matches the Phase 5 hash. Live `ZolaClient\logs\supervisor.log` was last written at 08:05:24, when stable closed. The capture still has 0 events. Dev stays running for SM-DEV3.

Google is not connected from the app window. Before Brian runs setup, the live token file `profiles\zola\zola_workspace\token.dpapi` is 926 bytes, SHA-256 `afa0f744a8d9db8a66cb0c21732fe93dc9d62d7091395eab860368b88197064e`. It was not opened. `zola-dev\zola_workspace\token.dpapi` does not exist. The client JSON is present at `C:\Users\test\Documents\zola-oauth\client-secret_zwindows.json` (409 bytes, not opened). The synced `auth.py` and `setup.py` match the worktree source. The dev `plugins` directory is not a link. Process Monitor is still running, the capture has 0 events, and its filter includes process name `python.exe`, so the setup process is in the capture. Setup does not print the account. The running serve already has `HERMES_HOME` set to `zola-dev` and reads the store on the next token load, so no client or serve restart is required. Waiting for Brian to run the commands below.

Setup after-checks, 08:36. Brian reported the test account is set up and shows connected in the app. Recorded as test account confirmed by Brian. The live token file is still 926 bytes, last written 2026-10-16 07:20:47, SHA-256 unchanged. It was not opened. `zola-dev\zola_workspace\token.dpapi` exists, 926 bytes, written 2026-11-13 08:35:19. Size only; it was not opened or hashed. Process Monitor is still running and the capture still has 0 events, so no access to the live roots was recorded. Dev stays running.

SM-DEV3 create did not happen. Brian asked her to create the test event. She answered: "I can't create it from here: the calendar connector is read-only, and this session's browser automation isn't installed." Source agrees. The only calendar tool is `calendar_query` (`gcal.py:1`, `gcal.py:27`, registered in `__init__.py:157–164`). The required calendar scope is `calendar.readonly` (`auth.py:125`, `auth.py:140–145`). There is no create-event tool. `zola-dev\logs\agent.log` contains the name `calendar_query` once. No calendar text was read out of the log. STOP. Creating the event would be a new decision. Dev is still running. Process Monitor was not stopped.

Plan deviation, recorded from Claude: calendar is read-only by design (Phase 8), so there is no calendar write to test. SM-DEV3 is replaced by existing capabilities only.

SM-DEV3a (read): Brian creates "PROC1-DEV marker" on the test account's calendar in the browser and asks dev Zola "What's on my calendar tomorrow?". Pass: she names the marker, and Brian confirms his real calendar has no such event.

SM-DEV3b (write): Brian asks dev Zola to draft an email to himself, subject "PROC1-DEV test draft", and not to send it. The draft tool is `gmail_draft` (`gmail.py:33`). The send tool is `gmail_send_draft` (`gmail.py:34`). Pass: the draft is in the test account's Gmail Drafts and not in the real account's Drafts, and the dev log shows `gmail_draft` with no `gmail_send_draft`. Log event names only.

Before those asks, `zola-dev\logs\agent.log` contains `calendar_query` 3 times, `gmail_draft` 0, `gmail_send_draft` 0. Process Monitor is still running. Waiting for Brian's 3a and 3b results. SM-DEV4 follows those results.

SM-DEV3a result. Brian's report of what she said: "You have PROC1-Dev marker at noon tomorrow, for one hour." She named the marker. `zola_workspace.log` events, names and counts only: `calendar_query` `state=complete count=1`, and two `calendar_query` `state=no_match count=0`. His confirmation that the real calendar has no such event is not in this report.

SM-DEV3b result. She said the draft was drafted and not sent, subject "PROC1-DEV test draft", with no body. The address she named is not recorded. Brian said the draft shows up on the account. He did not say whether it is absent from the real account's Drafts. `agent.log` contains `gmail_draft` and does not contain `gmail_send_draft`. `zola_workspace.log` has `send_gate decision=prepared` and `send_gate decision=reviewed`. `prepared` is the draft write (`gmail.py:691`). `reviewed` is the reply covering that draft (`send_gate.py:743–765`). There is no `decision=sent`.

SM-DEV4 before snapshot, counts and times only. Dev `facts` 5, active 5, episodes 1. Dev `zola_memory.db` 184320 bytes, 08:50:10. Dev wal 61832 bytes, 08:59:05. Dev `memories\USER.md` 100 bytes and `MEMORY.md` 158 bytes, both 2026-11-12 10:15:46. Live `facts` 20, active 20, episodes 53. Live `zola_memory.db` 278528 bytes, 2026-11-12 15:21:09. That live count was a read-only open by the Hermes venv `python.exe`. The open Procmon header still says 0 events. A string scan of the backing file finds `\hermes\profiles\zola\` only in `zola_memory.db` names, and no `\ZolaClient\` path. Process Monitor stays running.

SM-DEV3a pass. Brian confirmed his real calendar has no PROC1-Dev marker. It is only on the test account. SM-DEV3b pass. Brian confirmed the real account has no draft. The test-account draft and the log events are recorded above.

SM-DEV4 pass. She answered "I'll remember that." Dev active facts went from 5 to 6, episodes from 1 to 2. Dev `zola_memory.db` was written at 09:09:17 (still 184320 bytes). Dev wal grew from 61832 bytes at 08:59:05 to 65952 bytes at 09:10:11. Dev `memories\USER.md` grew from 100 bytes to 138 bytes at 09:10:09. Dev `MEMORY.md` is unchanged, 158 bytes. Fact text was not read. Live `zola_memory.db` is still 278528 bytes, 2026-11-12 15:21:09. Live wal is still 4152 bytes at that same time. Live `USER.md` and `MEMORY.md` are unchanged. Live shm is 32768 bytes with mtime 09:02:31, from the earlier read-only row count, before this fact. The live fact count was not opened again.

SM-DEV5 pass. Brian asked whether he had any new texts. She answered: "I can't reach your phone right now, so I can't tell." That begins with the no-connection sentence in `phone_tools.py:50` and does not claim she checked. No `zola-phone` process. `Local\ZolaPhone` is free. No pipe with Zola in the name. `zola_phone.log` and `zola_phone.out.log` are absent. `zola_workspace.log` has one tool line, `zola_workspace.phone_read tool=phone_read_notifications state=incomplete reason=no_connection count=0`. Dev pid 12488 is still running. Process Monitor is still running.

SM-DEV6 pass. Brian clicked the stable shortcut. The pop-up he read is `Zola (dev) is already running. Close it before starting another.` (`IdentityConstants.RefuseDevText`). The only `Zola.Client` still running is the smoke exe, pid 12488, started 08:22:22. Its serve and watcher children are still the dev ones. `Test-DevIsolation.ps1 -Mode WhileRunning` printed `while-running command lines match zola-dev`, exit 0. Live profile versus the before map: 914 files, one difference, `zola_memory/zola_memory.db-shm`, mtime 09:02:31, which is the earlier read-only row count, before this click. `ZolaClient` matches the before map, 27 files. Live `auth.json` hash is unchanged. The refusing stable wrote nothing. Dev stays running. Process Monitor stays running.

Brian closed dev. Confirmed gone at 09:20:16: no `Zola.Client`, no serve, no phone, both mutexes free. Dev had started at 08:22:22.

After hash maps: live profile 914 files, one difference, `zola_memory/zola_memory.db-shm`, mtime still 09:02:31. `ZolaClient` 27 files, no difference. `Test-DevIsolation.ps1 -Mode AfterClose` on the profile map printed `changed zola_memory/zola_memory.db-shm` and exited 1. The same check on `ZolaClient` printed `after-close hashes match`, exit 0.

Process Monitor, after a clean stop: 519 events. No `WriteFile` under the live roots. The smoke client, pid 12488, opened `ZolaClient\secrets` and `ZolaClient\secrets\deepgram_api_key`. The dev serve child, pid 10676, parent 7928, opened and read `profiles\zola\runtime\active_sessions.json` 11 times and opened and locked `profiles\zola\runtime\active_sessions.lock` 11 times. Those two files still match the before map. The row-count python, pid 25956, parent powershell 4760, read `profiles\zola\zola_memory\zola_memory.db` and its wal and shm, and `SetEndOfFileInformationFile` on the shm succeeded. That is the hash difference. Other `python.exe` processes also opened the Deepgram key; the filter included every `python.exe`, and their parents are not all the smoke client. The capture file was deleted after this review. Stable was not started. The experience check was not asked. STOP. The dev serve opened the live profile's runtime session files, which is outside the Deepgram-key exception.

Phase 6 findings accepted as STOP items. Read-only investigation, Hermes pin `345cd2b`. No Hermes change. The sweep is `release_orphaned_leases` (`active_sessions.py:634–656`), called from the serve reaper every 300s (`server.py:354`, `server.py:361–371`, `session_reaper.py:186`). `get_default_hermes_root` stays `%LOCALAPPDATA%\hermes` while `HERMES_HOME` is a profile under that root (`hermes_constants.py:165–180`), so the sweep reads every profile's `runtime\active_sessions.json`. If that file exists, `_FileLock` opens the lock with `a+b` (`active_sessions.py:202–203`). The JSON is rewritten when this process drops its own orphaned leases (`active_sessions.py:627–630`). Recommendation: a separate Hermes root, for example `%LOCALAPPDATA%\hermes-dev`, which `resolve_profile_env` already treats as the launch root (`profiles.py:1800–1813`). A read-only exception is not available: the lock create and the conditional JSON rewrite are write paths. The live row count was `mode=ro` without `immutable=1`, from the check's python pid 25956, and that process extended the shm. The design line is in `Test-DevIsolation.ps1` and is not implemented. The experience check waits until isolation passes. Stable was started by Brian after the STOP.

## Phase 6c — separate Hermes root

D4 amendment recorded above. Hermes pin `345cd2b`. No Hermes source change. Stable stayed running. Nothing was launched. `Move-DevProfile.ps1` was not run against the live profile.

Native-root inventory, dev serve with `HERMES_HOME` at `%LOCALAPPDATA%\hermes-dev\profiles\zola-dev`. `get_default_hermes_root` then returns `%LOCALAPPDATA%\hermes-dev` (`hermes_constants.py:173–179`), so its callers read and write that root, not the native one. The serve sweep is `release_orphaned_leases` (`active_sessions.py:634–656`), every 300s. It can create `active_sessions.lock` and rewrite the JSON under the homes of that root only. No write into the native root remains on the serve path, so implementation continued.

Reads that still name the native install tree, and do not write it: `configure_windows_stdio` checks `%LOCALAPPDATA%\hermes\git` and `hermes-agent\venv\Scripts` (`stdio.py:93–120`) on every Windows start, including serve. A shell lookup may check `hermes\git\...\bash.exe` (`tools\environments\local.py:364–379`). Backup import, uninstall, and the unset-`HERMES_HOME` fallback are not the dev serve.

Client: dev profile and dev root auth use `hermes-dev`. Validation refuses when the resolved profile is under the native `hermes` directory. Stable paths are the same assertions as before, including `hermes\auth.json` for the stable root-auth property.

Scripts: `New-DevProfile`, `Sync-DevPlugins`, and `Test-DevIsolation` use `hermes-dev\profiles\zola-dev` and refuse a destination under the native `hermes` directory. `Move-DevProfile.ps1` refuses while any Zola runs, moves `hermes\profiles\zola-dev` to the new profile, checks file hashes, and removes the old folder. After that check it retargets `config.yaml` prefixes from the old profile directory to the new one, and lists any other file that still contains the old prefix without changing it. `Invoke-LiveSqliteReadOnly` opens live SQLite only with `mode=ro&immutable=1`, and only a `select`, and refuses while stable is running. AfterClose stays hash-only.

Scratch check, not the live profile: with `HERMES_HOME` under a scratch `hermes\profiles\zola`, `get_default_hermes_root` is that scratch `hermes` and `release_orphaned_leases` does not touch scratch `hermes-dev`. With `HERMES_HOME` under scratch `hermes-dev\profiles\zola-dev`, the root is `hermes-dev` and the scratch native JSON is unchanged.

| Suite | Result | Floor |
|-------|--------|------:|
| Checks | **322 PASS / 0 FAIL**, exit 0. Identity rows 51/51 | 295 |
| `Test-DevTools.ps1` | **16 PASS / 0 FAIL**, exit 0 | |

Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-DEV_Phase6c.diff` (UTF-8, no BOM). New files are in the diff. Checked against `git status --porcelain`. Nothing is staged. Plugin suites were not rerun; this phase does not change them. The experience check waits. After review: Brian closes stable, then `Move-DevProfile.ps1`, then the Phase 6 session again.

Move, after Brian closed stable. No Zola process and both mutexes free. `Move-DevProfile.ps1` exited 0. `move hashes match`. `config retarget count=1`. The old `hermes\profiles\zola-dev` is gone. The new profile has 496 files. Live profile stayed 914 files, `ZolaClient` stayed 27, both diffs 0. Live `auth.json` hash is unchanged. `config.yaml` names the new profile directory and does not name the old one. Files that still contain the old directory prefix, not rewritten: `config.yaml.bak-PROC1-DEV-20261112-153527`, `state.db`, five `backups/config/config.yaml.good.*` files, and the plugin `__pycache__` files. Smoke rebuilt to `%TEMP%\proc1-dev-smoke\` (0 errors, the same CS8604). WinUI files present. The new binary contains `hermes-dev` and does not contain `hermes\profiles\zola-dev`. Session-before maps: `%TEMP%\proc1-dev-maps\6c-session-before-profile.clixml` and `6c-session-before-client.clixml`.

## Phase 6 rerun — hermes-dev

Brian: "All checks passed. The pop up message was the same as before." SM-DEV1 was not repeated. The pop-up is the same sentence as SM-DEV6, `Zola (dev) is already running. Close it before starting another.` Dev serve start `2026-11-13T10:12:06`, watcher stop `2026-11-13T10:16:09`. `supervisor.log` has `identity role=dev` at `10:12:05`. This session's wake-model path is `hermes-dev\profiles\zola-dev`. No phone line in the dev logs. The old `hermes\profiles\zola-dev` folder is still absent.

`Test-DevIsolation.ps1 -Mode WhileRunning` was not run: both mutexes were already free when the check started. The capture, taken while dev was running, shows the smoke exe pid 14512, a serve with `-p zola-dev` (pid 13948, child 21684), and no `-p zola` serve. No `zola_phone` process. `HERMES_HOME` is not on those command lines. Those command lines do not name the live profile or the vacated folder.

After maps: live profile 914 files, `ZolaClient` 27 files. `Test-DevIsolation.ps1 -Mode AfterClose` printed `after-close hashes match` for each, exit 0. `%LOCALAPPDATA%\hermes\auth.json` is absent. No file under the native `hermes` directory, outside `profiles\zola`, was written between 10:11 and 10:17.

Process Monitor, 179 events, then deleted. No `WriteFile`. No event under `profiles\zola` or the vacated `profiles\zola-dev`. The smoke client opened `ZolaClient\secrets` and `ZolaClient\secrets\deepgram_api_key`. Twelve python processes, each a descendant of serve pid 21684, read that same key once. The stable shortcut process, `Zola\stable\proc1-id\Zola.Client.exe` pid 28460, has no file event in the capture. Stable has not been started again. The experience check has not been asked.

## Phase 6 rerun — 12 minute sweep

The 10:12 session was about 4 minutes, so the 300 s lease sweep did not run. Brian will give the experience check after this longer run. Stable was closed. Before maps, 914 and 27 files: `%TEMP%\proc1-dev-maps\6c-long-before-profile.clixml` and `6c-long-before-client.clixml`. Process Monitor is running. The filter includes the whole native `\hermes\` tree, `\ZolaClient\`, and `hermes-dev\profiles\zola-dev\runtime\active_sessions`, and excludes `\ZolaClient-dev\`. Dev started `2026-11-13T10:50:31`. Smoke pid 11920. Serve `-p zola-dev`, launcher pid 2000, child pid 2700. `identity role=dev` at `10:50:30`. Watcher stop `2026-11-13T11:07:13`. At `11:03:18`, `Test-DevIsolation.ps1 -Mode WhileRunning` printed `while-running command lines match zola-dev`, exit 0. Brian clicked the stable shortcut. The pop-up was `Zola (dev) is already running. Close it before starting another.` The stable process `Zola\stable\proc1-id\Zola.Client.exe` pid 19940 had no file event in the capture.

Serve pid 2700 locked and read `hermes-dev\profiles\zola-dev\runtime\active_sessions.lock` and `active_sessions.json` at 10:51:06 (startup), then at 10:55:34, 11:00:34, and 11:05:34. No `WriteFile`. The capture has 184 events. No event under `%LOCALAPPDATA%\hermes\`. Dev access under `ZolaClient\` is the shared Deepgram key only, reads. No dev writes. After maps at 11:08:49: live profile 914 files, `ZolaClient` 27 files. Both `Test-DevIsolation.ps1 -Mode AfterClose` runs printed `after-close hashes match`, exit 0. No file under the native `hermes` directory changed between 10:50 and 11:10. Live SQLite was not opened. The capture was deleted. Stable started `2026-11-13T11:15:25`, `identity role=stable`, tag `proc1-id`, drift `components=none`. Serve `-p zola` at `11:15:26`. No Application Error for python or Zola between 10:50 and 11:21. Experience check, Brian's words: "I can try things in a dev Zola with made-up data and my test Google account, and my real Zola, data and phone aren't touched."

## Phase 7 — Commit and merge

**Brian go-ahead (verbatim):** "proceed to commit and merge"

### Step 1 — implementation commit

| Item | Value |
|------|-------|
| Implementation commit | `07c1d4a58cf2952a47dcc945dd91af679a0c9e13` |
| Message | `feat(PROC1-DEV): dev profile and client data root, fail closed, test-only Google, no phone in dev — PROC1-D4/D5/D6/D13/D14` |
| Files | `windows-client/Zola.Client/` (+ClientPaths, Identity dev validation), `windows-client/Zola.Client.Checks/`, `hermes-plugins/zola_tts/deepgram_tts.py` and its test, `tools/dev/*`, this progress doc |

`origin/main` is still the Phase 1 base `cfc0d353f385e6d805c0b596b86ddee92eb566d3`. It has not moved.

### Step 2 — fetch

`origin/main` had not moved. Still `cfc0d353f385e6d805c0b596b86ddee92eb566d3`.

### Step 3 — merge

| Item | Value |
|------|-------|
| Merge commit | `2e9bc4a037be4c57eba5d20c45569e92aa66e686` |
| Strategy | `git checkout --detach origin/main`; `git merge --no-ff proc1-dev` |
| Diff | 37 paths. Client, checks, `hermes-plugins/zola_tts/deepgram_tts.py` and `tests/test_deepgram_tts.py`, `tools/dev/*`, this progress doc. Nothing else. |

### Merge record

D4 amendment. Brian's verbatim approval: "Approved." The dev profile name stays `zola-dev`. The dev root is `%LOCALAPPDATA%\hermes-dev`, so the profile is `%LOCALAPPDATA%\hermes-dev\profiles\zola-dev`. Stable paths stay `%LOCALAPPDATA%\hermes\profiles\zola` and `%LOCALAPPDATA%\ZolaClient\`.

SM-DEV3 plan deviation. Calendar is read-only by design, so the create-event smoke was not run. It was replaced by 3a, a read of the test-account marker "PROC1-DEV marker", and 3b, a draft titled "PROC1-DEV test draft" that was not sent. Brian confirmed neither was on the real account.

Phase 6, first session. SM-DEV1 through SM-DEV6 passed, with SM-DEV3 as 3a and 3b. The dev serve opened the live profile's `active_sessions.json` and `.lock`. That was accepted as the STOP that led to the separate Hermes root. The live profile differed only in `zola_memory.db-shm` from a `mode=ro` open without `immutable=1`.

Phase 6, short rerun at 10:12. About four minutes, so the 300 s sweep did not run. Pop-up was the same dev-already-running sentence. Live roots were byte-identical. Deepgram key reads only.

Phase 6, longer run. Serve start `2026-11-13T10:50:31`, watcher stop `2026-11-13T11:07:13`. Serve pid 2700 locked and read `hermes-dev\profiles\zola-dev\runtime\active_sessions.lock` and `active_sessions.json` at 10:51:06, 10:55:34, 11:00:34, and 11:05:34. No `WriteFile`. 184 capture events. No event under `%LOCALAPPDATA%\hermes\`. `ZolaClient\` access was the shared Deepgram key, reads only. While-running printed `while-running command lines match zola-dev`. After-close hashes matched, 914 and 27 files. Stable start `2026-11-13T11:15:25`, `identity role=stable`, drift `components=none`. A later stable start is in the log at `2026-11-13T11:34:56`, same role and drift. Experience check, Brian's words: "I can try things in a dev Zola with made-up data and my test Google account, and my real Zola, data and phone aren't touched."

### Step 4 — suites on the merged tip

Phone close (crash-watch): `ZolaClient\logs\supervisor.log` phone `event=stop` `2026-11-13T11:41:43.2561828-08:00`, watcher `event=stop` `2026-11-13T11:41:43.2796404-08:00`. Both mutexes free at 11:42:31. No Zola process.

| Suite | Result | Floor |
|-------|--------|------:|
| Checks | **322 PASS / 0 FAIL**, exit 0. Identity 51/51 | 295 |
| Stable scripts | **54 PASS / 0 FAIL** (summary line) | 54 |
| Dev tools | **16 PASS / 0 FAIL** | |
| zola_workspace | **582 OK** | 582 |
| zola_memory | **162 OK** | 162 |
| zola_tools | **44 OK** | 44 |
| zola_tts | **9 OK** | 8 |
| zola_phone (Zola closed) | **71 OK** | 71 |
| Kotlin | **98** (15+39+30+14), 0 fail/error/skip; assembleDebug succeeded | 98 |

Stable had not been started again when this was written.

## Phase 7 complete

## Phase 8 — Live checkout sync

| Item | Value |
|------|-------|
| Eligibility | live checkout on `main`, clean |
| Before | `cfc0d353f385e6d805c0b596b86ddee92eb566d3` |
| After | `af21227b5964912726f505caee8c9bf87ef300b1` (`git pull --ff-only origin main`) |

Tag `proc1-dev` points at the merge `2e9bc4a037be4c57eba5d20c45569e92aa66e686`. The branch `proc1-dev` is deleted locally and on origin. The worktree stays until Phase 9 ends.

## Phase 9 — Promotion decision (step 1)

Promoting tag **`proc1-dev`** means running `Promote-Stable.ps1` so Brian's everyday shortcut Zola becomes the merged `main` tip. That tip is everything merged so far (PR-D09): PROC1-STABLE, PROC1-ID, and PROC1-DEV.

**In plain words:**
- The new path code then runs in the everyday Zola.
- A stable build still resolves today's paths: `%LOCALAPPDATA%\hermes\profiles\zola` and `%LOCALAPPDATA%\ZolaClient\` (G-STABLE-SAME). It does not switch to `hermes-dev` or `ZolaClient-dev`.
- The dev root `%LOCALAPPDATA%\hermes-dev\profiles\zola-dev` is used only by a dev-role build.
- Either way, the dev isolation rules switch on for the next track: synthetic data by default, and dev testing never uses the live profile.
- Until a promote, the shortcut stays `proc1-id`.

Awaiting Brian's verbatim decision: promote `proc1-dev` now, or decline.

**STOP — Phase 9 step 1.**

## Phase 9 steps 2–end

**Brian decision (verbatim):** "Promote proc1-dev"

**Plugin copy (verbatim):** "Yes, copy that file." The switch-time comparison matched Prepare: added none, removed none, changed `zola-tts/deepgram_tts.py` only. That file was copied.

### Prepare

Zola was already closed (no client, both client mutexes free). Outgoing from `current.txt`: `proc1-id`. Tag commit `2e9bc4a037be4c57eba5d20c45569e92aa66e686`. Release build 0 errors, the same CS8604. `assembleDebug` succeeded. Staging `C:\Users\test\Zola\stable\_staging\proc1-dev`: 103 files, 102,435,496 bytes. WinUI check OK (`App.xbf`, `MainWindow.xbf`, `Themes\ZolaTokens.xbf`, `Zola.Client.pri`). `Zola.Client.exe`, both Rajdhani fonts, and `Assets\Presence\zola.glb` present. Client build hash `480ffbdb34e00f3fdc7da86c94db9f7dda3ca52435781f42965da7878aaf463b`. The temp build folder was removed after a too-long-path delete; it is gone.

### Switch

Pre-check `2026-11-13T11:55:11`: no Zola process, `Local\ZolaClient`, `Local\ZolaPhone`, and `Local\ZolaWatcher` free. `Promote-Stable.ps1 -Switch -Tag proc1-dev -ApprovedPluginCopy` exited 0.

| Item | Value |
|------|-------|
| Promoted at | `2026-11-13T11:56:37.3711236-08:00` |
| Stable folder | `C:\Users\test\Zola\stable\proc1-dev\` |
| `current.txt` | `proc1-dev` |
| Backup | `C:\Users\test\Zola\stable\backups\proc1-dev-20261113-115531` (901 files, 48,876,398 bytes) |
| Outgoing | stable-tag `proc1-id`, folder `C:\Users\test\Zola\stable\proc1-id` |
| Incoming | stable-tag `proc1-dev`, commit `2e9bc4a037be4c57eba5d20c45569e92aa66e686` |
| Databases | 5, each `integrity_check` OK, schema version 0 |
| Drill | PASS — databases=5, files=823, credentials=5; scratch deleted |
| build-role.json | role=stable tag=proc1-dev commit=`2e9bc4a` manifest=`stable-manifest.json` |
| Shortcuts | Desktop and Start Menu `Zola.lnk` → `C:\Users\test\Zola\stable\proc1-dev\Zola.Client.exe`, working directory that folder |

### Shortcut start

Brian: "desktop is open. Voice sounds normal."

Start `2026-11-13T11:58:55`. Exe `C:\Users\test\Zola\stable\proc1-dev\Zola.Client.exe` pid 23612. Serve `-p zola` (launcher 25984, child 23248). `ZolaClient\logs\supervisor.log`:

```
identity role=stable why=ok tag=proc1-dev
drift completed=true components=none
```

This start's wake-model path is `%LOCALAPPDATA%\hermes\profiles\zola`. Logs written since the start are under `ZolaClient\logs\` only. No `ZolaClient-dev` log was written, and those stable logs do not name `hermes-dev`.

## Phase 10 — Closeout

Docs-only record on `main`. Dev isolation rules are on for the next track.

| Item | Value |
|------|-------|
| Implementation | `07c1d4a58cf2952a47dcc945dd91af679a0c9e13` |
| Merge | `2e9bc4a037be4c57eba5d20c45569e92aa66e686` |
| Tag | `proc1-dev` → merge |
| Dev profile | `zola-dev`, created 2026-11-12, moved to `%LOCALAPPDATA%\hermes-dev\profiles\zola-dev` on 2026-11-13 |
| Dev client data | `%LOCALAPPDATA%\ZolaClient-dev` |
| Model sign-in | option (a), openai-codex |
| Google in dev | test account, connected 2026-11-13 |
| Phone in dev | none |
| Isolation | PASS — live roots byte-identical on the longer run |
| Suites | Checks 322/0 · scripts 54/0 · dev tools 16/0 · workspace 582 · memory 162 · tools 44 · tts 9 · phone 71 · Kotlin 98 |
| SM-DEV1–6 | pass; SM-DEV3 was 3a read and 3b unsent draft |
| Experience check | "I can try things in a dev Zola with made-up data and my test Google account, and my real Zola, data and phone aren't touched." |
| Crash watch | 2 `python.exe` Application Error events since 2026-11-09 13:23:08: 2026-11-12 10:36:04 (`python312.dll`, `0xc0000005`) and 2026-11-12 10:47:32 (`sqlite3.dll`, `0xc0000005`). None on 2026-11-13. |

Deliberate closes and starts on 2026-11-13: dev watcher stop 11:07:13; stable start 11:15:25; stable start 11:34:56; phone and watcher stop 11:41:43; switch 11:56:37; shortcut start 11:58:55.


