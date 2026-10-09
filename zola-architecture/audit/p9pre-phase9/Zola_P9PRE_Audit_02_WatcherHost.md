# Zola P9PRE Audit 02 — Where the Watcher Can Live

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Labels vs:** `S7`, `S51`, `P8-D01`, `P8-D02`, `A5`, WINH08 scheduled-automation notes

No recommendation. Each host is a facts row.

---

## 1. How many times `register` runs (LEAD-1)

`discover_plugins` (`hermes_cli/plugins.py` L1575–1579) is idempotent: it joins any in-flight scan and calls `PluginManager.discover_and_load` once per process unless `force=True`. `hermes serve` calls it before the server starts (`hermes_cli/main.py` L2509–2511). The TUI toolset resolver can call it again (`tui_gateway/server.py` L1818–1819); the second call does not reload.

`VALID_HOOKS` (`plugins.py` L108–190) includes `on_session_start` / `on_session_end`, `pre_llm_call`, `pre_tool_call`, subagent start/stop, and others. There is no `serve_started` or `serve_stopping` name. `PluginContext.on_unload` (L413–420) runs when that plugin is unloaded. `PluginContext.spawn_task` (L422–432) schedules a coroutine on the **running** asyncio loop and cancels it on unload.

`zola_workspace` is on that general path (`plugins.enabled`). H-1: a second `discover_plugins()` did not call `register` again; `force=True` did.

`zola_memory` is `memory.provider`, not a row in `plugins.enabled`. Its `register` is invoked by `load_memory_provider` → `_load_provider_from_dir` → `collector.collect(mod.register)` (`plugins/memory/__init__.py` L273–276, L307–317). `_init_memory` calls that for every agent with `skip_memory` false (`agent/agent_init.py` L1267–1286). Cron jobs construct that agent with `skip_memory=False` and `platform="cron"` (`cron/scheduler.py` L2212–2214). Background review and subagents pass `skip_memory=True`. Each new TUI session agent therefore enters `zola_memory.register` again (`hermes-plugins/zola_memory/__init__.py` L59–76), which replaces the module-level provider and re-registers hooks. It does not start a thread today. `ZolaMemoryProvider.initialize` (`provider.py` L91–104) then runs with a `session_id`. `shutdown` (L338+) closes that session's connection.

**LEAD-1: PARTLY CONFIRMED.** A tool plugin's `register` runs once per process until `force=True`, and again in a second process (H-1, H-2). The memory provider's `register` runs once per memory-enabled agent, including a cron agent. Hermes does not offer a serve-lifetime hook; `on_unload` and `spawn_task` are the closest supported lifecycle, and `spawn_task` requires a running loop.

**P9PRE-AUD-18 [MATCH]** — general plugin load is once per process until `force=True`.  
**P9PRE-AUD-19 [GAP] MEDIUM** — no supported "serve started / serve stopping" hook for long-running plugin work. `S51` if the watcher is inside serve: a crash stops it with the process (audit 01).  
**P9PRE-AUD-43 [RISK] MEDIUM** — `zola_memory.register` runs per memory-enabled agent, including `platform="cron"`. A watcher started there would duplicate on each session and would also start inside a cron agent. `P8-D02`, `A5`.

---

## 2. Threads

No Zola plugin starts a daemon thread. Hermes itself starts daemon threads in the serve process (hosted-room startup, and the desktop cron ticker **only** when `HERMES_DESKTOP=1`). Zola's spawn removes that variable:

```211:213:windows-client/Zola.Client/HermesProcessManager.cs
        start.Environment.Remove("HERMES_DESKTOP");
        start.Environment.Remove("HERMES_WEB_DIST");
        start.Environment.Remove("HERMES_SERVE_HEADLESS");
```

The ticker gate is `hermes_cli/web_server.py` L194–219: the thread starts only if `HERMES_DESKTOP == "1"`. Zola's serve does not tick cron.

A plugin thread would share the process GIL, the serve interpreter, and any SQLite connections that plugin opens. `google_http` does not keep a shared `requests.Session` (audit 03). A session switch calls provider `shutdown` / `initialize`; a thread started in `register` would not be stopped by that. `/compress` is a session operation, not a process restart.

---

## 3. Single instance

Hermes's cron tick lock is `cron/scheduler.py` `_acquire_tick_lock` (L3503–3520): open `cron/.tick.lock`, `msvcrt.locking(..., LK_NBLCK, 1)` on Windows, `fcntl.flock` elsewhere. Contention skips the tick. That lock is for the ticker, not for an arbitrary plugin.

---

## 4. Cron (LEAD-2)

Schedule kinds in `cron/jobs.py`: `once`, `interval`, `cron` (L728–736, L1105–1117). Payload can be a prompt, a skill, or a script. `no_agent=True` requires a script (`jobs.py` L425, L1639–1640).

`cron/scheduler.py` `_run_no_agent_job` (L1251–1277) runs that script and returns before `run_agent` / `SessionDB` (`run_job` short-circuit L1968–1970). The docstring says "no AIAgent, no tokens."

**LEAD-2: PARTLY REFUTED.** At this pin a cron job can be a script with no model turn. WINH08's "every job is `run_conversation`" is not true of `no_agent`.

What still blocks it as Zola's watcher:

- Zola's serve does not start the ticker (section 2). The profile `cron/` directory has no job files (Phase 1).
- `approvals.cron_mode` is `deny` (pin default). The scheduler comment at L223 says `no_agent` jobs never reach a model, so that mode is about agent jobs.
- A script that imported `zola_workspace` would be a second Google caller outside the tool handlers (`P8-D01` / `P8-D02`). The toolset exclusion does not apply to a script that does not use tools.
- `P8-D02` removed the Workspace **toolset** from cron (`known_plugin_toolsets.cron` contains `zola_workspace`; `platform_toolsets` has no `cron` key). That stops the agent from seeing the tools. It does not stop a `no_agent` script.

**P9PRE-AUD-20 [RISK] HIGH** — `no_agent` is a real non-model job, and it is outside the Brian-only tool gate. It also does not run today, because this serve process does not tick cron.

---

## 5. Heartbeat and /loop

`_maybe_fire_tui_heartbeat_tick` (`tui_gateway/session_notifications.py` L198–223) and `_maybe_fire_tui_loop_tick` (L233–255) claim the **idle TUI session** and call `_run_prompt_submit` (`tui_gateway/prompt_turn.py` L796+) with the heartbeat or loop text. That is a model turn on the session's agent, not a plain-code poll. They do not fire with no session. They fire when the session is idle inside the serve process, which can be while the client is still connected or after it has detached; the code claims the session object, not the socket.

`_resolve_session_platform` (`tui_gateway/server.py` L1415–1419) returns `"tui"` unless `HERMES_DESKTOP=1`. Zola's spawn removes that variable (`HermesProcessManager.cs` L211–213), so the session agent is built with platform `tui`. `_make_agent` (`server.py` L2342–2363) does not pass `parent_session_id`. `pre_llm_call` then sees `platform` `tui` and an empty parent (`agent/turn_context.py` L674–685). `is_brian_turn` is true for that pair (`zola_workspace/turn_context.py` L99–115). The prompt text is the heartbeat prompt, not Brian's words. The poller keeps running while the session object is still registered after a socket detach.

**P9PRE-AUD-21 [RISK] HIGH** — a heartbeat or /loop on Zola's serve session is a live turn with `platform == "tui"` and an empty parent, so it passes `P8-D02`. They are not a watcher. `A5`.

Zola's profile does not show a heartbeat configuration in the keys read in Phase 1. The path exists in the pin.

---

## 6. Separate Zola process

`HermesProcessManager.SpawnAsync` already starts `hermes-agent\.venv\Scripts\python.exe` with `HERMES_HOME` set to the zola profile (`HermesProcessManager.cs` L185–209). A second process can use that same interpreter and the same user. DPAPI decryption in `auth.load_token_record` (`auth.py` L254–261) uses the user-scope protector already used by the plugin. No Hermes edit is required to import `zola_workspace` if `PYTHONPATH` includes the plugin directory (the client already prepends the hermes root, L498–504). The plugin's Google modules call `read_common.authorize`, which requires a turn record. A separate process has no `turn_context` record unless it forges one. Calling `google_http` and `auth.authorization_header` directly does not check Brian-only (audit 03 and 04).

The client would own lifetime the same way it owns serve: start, health, tree-kill on shutdown. Crash detection would be the same gap as `S51` unless the supervisor from audit 01 exists. Talk path to serve: `PluginContext.emit` (`hermes_cli/plugins.py` L955–974) publishes on the in-process plugin bus only. It does not call `tui_gateway.server._emit`. A file or SQLite queue is outside Hermes. The client already speaks JSON-RPC on `/api/ws` (`ChatSocket`).

---

## 7. Task Scheduler / service

Not started by Zola today. A scheduled task can run while the client is closed, which a serve-hosted watcher cannot (audit 01: the watcher dies with serve, and serve is started by the client). It runs in a session that may be locked or with no interactive user. `[EXT]` Microsoft Learn, `CryptProtectData` (read 2026-10-09): typically only a user with the same logon credential can decrypt, and decryption is usually on the same computer. `CRYPTPROTECT_LOCAL_MACHINE` binds to the computer instead of the user. A task running as a different account cannot decrypt a user-scope blob. The local fact is `auth.py` uses user-scope protection (P8-D04), not the machine flag. The cost that is already in lore: `P8-D02` assumes Brian is present for Workspace; a task runs when he is not.

---

## 8. Sleep (LEAD-9)

`SessionLockWatcher` covers WTS lock/unlock (client). `S33` records that Modern Standby on this laptop did not deliver a suspend signal. A timer loop can compare wall clock to `time.monotonic()` after the gap. Probe H-5 simulated a 30s wall jump against a 0.05s monotonic delta and flagged it. `[EXT]` `RegisterPowerSettingNotification` (winuser.h, read 2026-10-09) delivers power-setting changes to a window or a service handle. `[EXT]` `PBT_APMRESUMEAUTOMATIC` (read 2026-10-09) notifies that the system is resuming from sleep or hibernation and does not indicate that a user is present. The page does not mention Modern Standby. `S33` remains the local observation that this laptop did not deliver a suspend signal. The client does not call either API.

---

## Host facts

| Host | Starts | Stops | Survives serve crash | Survives client quit | Single instance today | Token | One authority |
|------|--------|-------|----------------------|----------------------|----------------------|-------|----------------|
| Plugin thread in serve | `register` or `spawn_task` after serve load | process exit; `on_unload` on plugin unload; `spawn_task` cancel on unload | no | no (client owns serve) | one per serve process; no cross-process lock of its own | in-process `auth.py` | inside `zola_workspace` only if it does not bypass `authorize` |
| `no_agent` cron script | when a ticker holds `cron/.tick.lock` | script exit | the ticker is not running in Zola's serve | no | tick lock | script would open the store itself | bypasses tool gate |
| Heartbeat /loop | idle TUI session poll | session end | no | no | session-scoped | n/a (model turn) | can look like a Brian turn |
| Separate process supervised by the client | client start, same pattern as serve | client shutdown | yes, if it is not the serve process | no, if the client is the supervisor | client would have to enforce it; cron lock is not reused automatically | same user, same DPAPI | second process is a second caller unless the only Google entry stays in `zola_workspace` |
| Task Scheduler / service | OS schedule, client closed | task settings | yes | yes | task settings | fails if the account is not the DPAPI user | runs with Brian absent (`P8-D02`) |

---

## 9. Addendum P9PRE-ADD-1 — Can a live turn arm heartbeat, /loop, or cron?

Read-only, 2026-10-09. No live model call. `state.db` opened with `mode=ro`.

The TUI agent loads `platform_toolsets.cli` (`tui_gateway/server.py` `_load_enabled_toolsets` L1854–1888). Coding `focus` is the only mode that replaces that list (`agent/coding_context.py` `toolset_selection` L319–322); the pin default mode is `auto`, which does not. The live list includes `cronjob`, `terminal`, `file`, and `delegation`. It does not include `code_execution`.

`evaluate_self_mod` (`guards.py` L581–588) runs only for `write_file`, `patch`, and `terminal`, and only when the text matches the plugin tree, the token store, `SOUL.md`, or the identity directory (`self_mod_hit` L558–566). `evaluate_terminal_google` (L569–578) runs only for `terminal`, and only when the command names a Google host, the token store, or `zola_workspace.setup`. `jobs.json`, `state.db`, `hermes cron`, and a heartbeat meta key match neither pattern.

| Path | What it can arm | P8 guards |
|------|-----------------|-----------|
| `cronjob_manage` (`tools/cronjob_tools.py` L1117–1140, toolset `cronjob` in `toolsets.py` L115–118) | Writes a cron job, including `no_agent` and `script` (`_HANDLER_FORWARDED_ARGS` L1111–1114). Not a heartbeat or /loop row. | Not one of the three guarded tool names. Open. |
| Slash tools (`/heartbeat`, `/loop`, `/goal`) | No model tool. `command.dispatch` is a client JSON-RPC method (`tui_gateway/server.py` L170, `methods_tools.py` L823). Handlers live on the interactive CLI (`cli_commands_mixin.py` `_handle_heartbeat_command` L2153–2178, `_handle_loop_command` L2279–2287). | Absent from the tool list. |
| A tool that writes `state_meta` | No tool under `tools/` calls `set_meta`. Heartbeat rows are `heartbeat:<session_id>` (`hermes_cli/heartbeat.py` `save_heartbeat` L119–128). Loop rows are `loop:<session_id>` (`hermes_cli/loops.py` L236, L286–296). Goal rows are `goal:<session_id>` (`hermes_cli/goals.py` L499). | No such tool. |
| `terminal` | Enabled. `hermes cron` is a real subcommand (`hermes_cli/subcommands/cron.py` L14–18). There is no `hermes heartbeat` or `hermes loop` subcommand. The same shell can run Python that calls `HeartbeatManager.set` (`heartbeat.py` L167–176) or SQL against `state.db` (`hermes_state.py` `set_meta` L1488–1498). | Guards do not match those commands. Open. |
| `write_file` / `patch` on `cron/jobs.json` | `file` is enabled. The jobs path is not in `self_mod_hit`. | Open for that file. |
| `execute_code` (`tools/code_execution_tool.py` L901, toolset `code_execution`) | Could run the same Python. | Not in the live CLI toolset list, so the turn does not receive the tool. |

Subagents are refused `cronjob_manage` (`tools/delegate_tool_toolsets.py` L20). The parent turn is not.

**Armed now.** `state_meta` keys `heartbeat:`, `loop:`, and `goal:`: 0 rows. `cron/jobs.json`: absent. `cron/` contains only `output`. `gateway_heartbeats`: 118 rows. That table is the process-liveness refresher (`tui_gateway/session_reaper.py` L335–377), not a `/heartbeat` prompt.

**P9PRE-AUD-45 [RISK] HIGH** — a live Zola turn can arm a session heartbeat or /loop through `terminal` (Python or SQL into `state_meta`), and can write cron jobs through `cronjob_manage`, `terminal` (`hermes cron`), or `write_file`. The P8 guards do not match those calls. A heartbeat or /loop then fires on this serve as `platform == "tui"` with an empty parent (AUD-21), so Workspace tools are allowed. `P8-D02`. Cron jobs do not tick in this setup: the client removes `HERMES_DESKTOP`, and the ticker starts only when that variable is `1` (audit 02 §2). A cron agent, if something else ticked it, would be `platform="cron"` (`cron/scheduler.py` L2214), which fails `is_brian_turn`. The open Workspace exposure is heartbeat and /loop. Nothing is armed in the profile today.

