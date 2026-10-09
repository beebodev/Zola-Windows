# Zola P9PRE Audit 01 — Backend Supervision

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Labels vs:** `S51`, `S52`, `S69`, `P4-D01`, `P7-D01`–`P7-D04`, `P8-D06`

---

## 1. Today, after ready (LEAD-4)

`HermesProcessManager.SpawnAsync` treats an exit **before** `HERMES_BACKEND_READY` as a failed start. The `Exited` handler only completes the startup tasks:

```251:256:windows-client/Zola.Client/HermesProcessManager.cs
        child.Exited += (_, _) =>
        {
            // P1-CLIENT: an exit before the ready sentinel is a failed start, not an attach — P1-D01
            ready.TrySetCanceled();
            blocked.TrySetResult("hermes serve exited before HERMES_BACKEND_READY.");
        };
```

After `NoteReady` (`HermesProcessManager.NoteReady`, L447–458) nothing subscribes to a later exit. `Shutdown` (L95–140) tree-kills only a child this window spawned, and only when the window closes. `App.xaml.cs` L22–24 starts serve once and shuts it down on window close.

Detection after ready is the chat health watch, not the process exit event. `ChatSocket.WatchHealthAsync` (L538–577) polls `GET /api/health` every `HealthIntervalMs` = 2000 (`ChatSocket.cs` L11). A failed probe calls `Fault` (L781–815), which aborts the socket, fails pending RPCs with `ChatUnreachableException`, and raises `Unreachable`. `MainWindow.ShowUnreachable` (L1039–1058) sets `_unreachable`, clears tool activity, abandons a pending question, and sets the status line to the unreachable reason plus "hermes serve is not reachable. This window will not keep waiting."

Nothing calls `StartAsync` again. **LEAD-4: CONFIRMED.**

**P9PRE-AUD-01 [MATCH]** — `S51` assumes no automatic recovery. The code matches that: detect, show, do not restart.

---

## 2. What a restart would need

| Piece | What exists | Where |
|-------|-------------|--------|
| New token | `DashboardSessionToken.Mint` draws 32 random bytes and base64url-encodes them. Spawn puts that in `HERMES_DASHBOARD_SESSION_TOKEN`. After health, the client prefers the token echoed by `GET /` (`ReadServedTokenAsync`). | `DashboardSessionToken.cs` L10–15; `HermesProcessManager.SpawnAsync` L185–208, L329–339 |
| New port | `--port 0`. The ready line `HERMES_BACKEND_READY port=N` (`ReadySentinel`, L509–510) becomes `Port`. | `SpawnAsync` L204–207, L304–312 |
| Socket | `ChatSocket.OpenAsync` opens `/api/ws` only when `WebSocketPermitted` (health, token, port). A dead serve fails that gate (`ChatSocket.cs` L162). | `HermesProcessManager.WebSocketPermitted` L51 |
| Session | Startup uses `session.create` (`MainWindow` around L294). `ResumeStoredAsync` exists (`ChatSocket.cs` L124–129) and is used when Brian picks a row (`MainWindow` L1961). Unreachable does not resume. | |
| Voice | `VoiceController.SyncVoiceModeAsync` (L1485–1547) re-reads `voice.status` and turns voice on only when Mode is already Voice. It is not called from `ShowUnreachable`. | |
| Presence during the gap | `ZolaDisplayState` sets `PresenceMode.Dormant` and `LinkOfflineLabel` when `_unreachable` or the backend is not reachable (L436–438, L477–479). `LinkReconnectingLabel` is only for session switch / history load (L481–483). | |

Reusable paths: `SpawnAsync` (token, port 0, ready sentinel, health), `ChatSocket.ResumeStoredAsync` (stored id → new runtime id), `VoiceController.SyncVoiceAndWakeAsync` (L1549+), `ZolaDisplayState.UpdateWindowFacts`. None of them are chained to an unexpected exit.

**P9PRE-AUD-02 [GAP] HIGH** — no respawn, no backoff, no visible "backend keeps failing" state. `S51`.

---

## 3. Fail-closed voice and reviewed drafts

On unreachable:

- Composer, send, cancel, stop-speaking, sessions, and the mode button disable (`MainWindow.UpdateChrome` L1812–1838; `ZolaDisplayState` L429). New prompts and new captures cannot start: `SetCaptureGate` records `BackendReachable = false` (`VoiceController.SetCaptureGate` L1017–1028) and `UpdateWindowFacts` passes `WebSocketPermitted && !_unreachable` (`MainWindow.ApplyVoiceChrome` L717–719).
- A pending clarify question is abandoned (`ShowUnreachable` L1051 → `VoiceController.AbandonPendingQuestion` L541–556). That clears the question token. It does not call `InvalidateCapture` (L2401–2424). The only `Unreachable` subscriber is `ShowUnreachable` (`MainWindow` L220).
- Playback chrome follows Dormant, which is chosen before the Speaking branch (`ZolaDisplayState` L436–446). The stop button hides because `_unreachable` is set. There is no explicit playback-stop RPC on this path. Audio ownership stays with the serve process (`P2-D01`); when that process is dead, the device is released with it. The client `Speaking` flag is not cleared in `ShowUnreachable`.
- Lock/sleep (`P4-D01` / `P4-D02`) is a separate gate (`VoiceController.ApplyGateFactAndEnqueue` L1033+). Unreachable does not run that sequence.

`send_gate.py` keeps the reviewed draft and the single-use authorization in process dicts (`_pending`, `_auths`, `_snapshots`, L53–55). `clear_session` (L546–561) only drops those dicts. SQLite is read-only for user-row snapshots (`_user_rows`, L570–589, `mode=ro`). A dead serve drops the reviewed draft. A later send has no authorization left. That is fail-closed for `P8-D06`, and it is also state the phase cannot assume survives a restart.

**P9PRE-AUD-03 [MATCH]** — new input and presence fail closed while serve is down.  
**P9PRE-AUD-04 [RISK] MEDIUM** — an open capture is not invalidated, and `Speaking` is not cleared. A restart inside the same window would see a stale capture unless it resets `VoiceController` first. `P7-D01`–`P7-D04` admission rules are not re-run on this path.  
**P9PRE-AUD-05 [MATCH]** — `P8-D06` review state does not survive the process. `S52` (stop-vs-silence race) is unchanged: unreachable does not send `voice.record stop`.

---

## 4. Interrupted-turn note (`S69`)

The TUI crash path builds the note in `tui_gateway/session_auto_continue.py` `_auto_continue_note` (L49–54) and submits it as the continuation prompt (`_run_prompt_submit`, L114) after `session.resume` schedules it (`_maybe_schedule_auto_continue`, L57–78). Opening text:

`[System note: Your previous turn was interrupted mid-run — the app or its backend process stopped before the turn could finish. … The interrupted request was:]` plus the original prompt.

Pin default, not overridden in the profile: `desktop.auto_continue.enabled` true, `freshness_minutes` 15, `max_attempts` 2 (`config_defaults.py` L2363–2370; reader `_auto_continue_config` L21–31). A messaging-gateway twin exists in `gateway/run.py` `build_resume_recovery_note` (L998–1038): `[System note: The previous turn was interrupted by …]`. Zola's serve is the TUI path.

Memory guard (`P8-D09`): `guards._save_request_suffix` (`guards.py` L414–439) returns None unless every token before the save phrase is in `SAVE_LEAD_IN_WORDS` (L67–80: zola, hey, ok, okay, please, so, and, also, alright, oh). The note's first tokens (`system`, `note`, …) are not lead-ins, so a tainted save is blocked with `BLOCK_MESSAGE_MEMORY_SAVE_REQUEST` (`evaluate_memory_taint` L516–522).

Passphrase (`P8-D06`): `send_gate.passphrase_match` (L131–138) returns false when `INTERRUPTED_MARK` (`"previous turn was interrupted"`, L26) appears anywhere in the message.

**P9PRE-AUD-06 [MATCH]** — both gates fail closed on the note. `S69` stays open as a product decision; the code does not strip the prefix.

---

## 5. Restart storms

The client has no restart counter, backoff, or "keeps failing" presence. Hermes's `desktop.auto_continue.max_attempts` (2) limits replay of one interrupted prompt. It does not limit process restarts. `agent.restart_drain_timeout` and `restart_after_turn_timeout` (`config_defaults.py` L85–99) are Hermes shutdown drains, not a Zola supervisor.

**Covered by P9PRE-AUD-02.**

---

## 6. Crash evidence since Phase 7

Application log, event 1000, faulting application `python.exe`, exception `c0000005`. Read 2026-10-09. Faulting module names only:

| Time (local) | Module |
|--------------|--------|
| 2026-10-05 11:13:49 | `python312.dll` |
| 2026-10-05 12:06:34 | `python312.dll` |
| 2026-10-05 19:28:51 | `python312.dll` |
| 2026-10-06 08:48:12 | `python312.dll` |
| 2026-10-06 10:52:31 | `ntdll.dll` |
| 2026-10-08 09:40:06 | `python312.dll` |
| 2026-10-08 11:07:55 | `python312.dll` |

Each 1000 has a following 1001. Count of `python.exe` event 1000 from 2026-09-01 through 2026-10-04: **0**. That matches the `S51` "zero then five" window, plus two more on 2026-10-08. The 11:07:55 entry is the CONNECT-FIX process death. `S51`'s Phase 8 annotation says the progress doc did not classify that death as a new APPCRASH. The Application log does.

Stderr: `OnLine` (`HermesProcessManager.cs` L220–234) appends stdout and stderr into a 16,000-character `StringBuilder` used only if startup fails (L290–300). After ready, that buffer is not written to a file. Client logs under `%LOCALAPPDATA%\ZolaClient\logs\` are display, presence, voice timeline, and server-request logs, not Hermes stderr.

WER LocalDumps: `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps` exists with zero values. Subkeys are `EADesktop.exe`, `EALauncher.exe`, `ErrorReporter.exe`. No `python.exe` subkey. `HKCU\…\LocalDumps` is absent. `[EXT]` Microsoft Learn, "Collecting User-Mode Dumps" (read 2026-10-09): local dumps are not enabled by default; they require registry values under `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps`, with optional per-application subkeys. This machine's key has zero values and no `python.exe` subkey, so that feature is not configured for Hermes.

**P9PRE-AUD-07 [GAP] MEDIUM** — `S51` asked to persist stderr and enable local dumps. Neither is present.

---

## 7. Watcher interaction

A watcher inside this serve process stops when the process stops. The client can see that only as backend unreachable (`ShowUnreachable`, Dormant, link offline). It has no last-poll time, error class, or separate "watcher down" source. Health is `GET /api/health` `ok` (`ProbeHealthAsync` L362–378), which does not mention a watcher.

**P9PRE-AUD-08 [GAP] LOW** — honest "watcher down" needs an observed source the client does not have. `P3-D06` (HUD needs a real source) applies when that source is added.
