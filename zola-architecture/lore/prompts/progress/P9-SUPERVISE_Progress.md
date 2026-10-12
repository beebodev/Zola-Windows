# P9-SUPERVISE Progress — Backend supervision

## Branch

- Work branch: `p9-supervise` (created from the plan-merge tip; not pushed)
- Base `main` before the plan commit: `efa46d310b61409689d8e28d38cb7279330a6b05` (`main` = `origin/main` after fetch)
- Plan commit: `d3f62cfaed970a69ff5cfc75f156e173411851f2` (`docs: Phase 9 build plan (Proactive Foundation)`)
- Plan merge on `main`: `19eaebcd755418985943d6140e01d97ad06f8ca0` (`Merge branch 'p9-build-plan'`)
- `p9-build-plan` deleted locally; it was never pushed
- After push: `main` = `origin/main` = `19eaebcd755418985943d6140e01d97ad06f8ca0`
- `p9-supervise` HEAD: `19eaebcd755418985943d6140e01d97ad06f8ca0`
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (porcelain empty; `chore(release): v0.21.3 (v2026.9.14)`)
- Prompt file: `C:\Users\test\Dev\zola-spikes\prompts\P9-SUPERVISE_Prompt_v1.2.md`
  SHA-256 `AEAC67208B83064502A3FCA30AC302DCEDB2A7D22391D701B59A9646D30918EE` (29,009 bytes)
- This Phase 1 message contained the prompt body and no separate comparison digest. The SHA above is the canonical file, hashed 2026-10-09.
- Scratch: `C:\Users\test\Dev\zola-spikes\p9-supervise\` deleted at closeout 2026-10-12. It held the auto-continue config backup and `connect-fail.log`. `C:\Users\test\Dev\zola-spikes\p9-fix-tts\` was not deleted. It stays until P9-FIX-TTS moves the Deepgram script into the repo.

### Build plan hashes (verified before commit)

- On disk (CRLF, 874 lines, 59,633 bytes): SHA-256 `a57d22feabf9f0a8c07ed57cbb88d55128aaa786fd8598e4d7cb7716b29eebbd`
- `core.autocrlf` = `true` (not changed)
- `.gitattributes` has no `*.md` rule (only `*.ttf binary` and `*.glb binary`, comment `P3-SHELL — P3-D12`)
- Staged blob SHA-256 `d30d951ac60a857517466299ec3bd724f57d0dccec28831ded5df0bf925f455a` (LF, 58,759 bytes)
- Staged blob id `aea3205fb0284ccfa0123b6b0900056d1cd3bf9e`
- File was not edited, reformatted, or re-saved

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Commit the build plan, then branch | COMPLETE |
| 2 | Grounding (read-only) | COMPLETE |
| 3 | Proposal → STOP | COMPLETE — verdicts recorded below |
| 4 | Implement | COMPLETE |
| 5 | Review checkpoint | COMPLETE — four review fixes applied |
| 6 | Deploy, WER setting, smoke | COMPLETE — smoke test passed 2026-10-12 |
| 7 | Closeout | IN PROGRESS — exit table written; stopped before the implementation commit |

## Guardrails (summary)

- G-SCOPE: `windows-client/Zola.Client/**` (process management, supervision, the gap, stderr logging, dump pruning if approved), a client test project only if approved at the Phase 3 STOP, this progress doc, and the Phase 1 build-plan commit. WER is a machine setting outside the repo. No `hermes-plugins/**` change unless Phase 2 finds a reason and Phase 3 approves it.
- G-ARCH: the build plan and P9-D02 are truth. A contradiction stops and is reported. A new decision point stops for Brian.
- G-PATTERN: read every file in full before changing it.
- G-NOCHANGE: no `hermes-agent` edits; no plugin, `SOUL.md`, identity, lore, or build-plan edits beyond the Phase 1 byte-for-byte commit; no live-profile edits unless approved; no NuGet or pip installs unless approved at a STOP; no Google calls.
- G-DELIBERATE: only an unexpected exit restarts serve.
- G-FAIL-CLOSED-GAP: invalidate capture and pending transcript, stop playback, and block input before any restart.
- G-NO-AUTHORITY-CARRYOVER: a restart creates no Brian authority and does not replay an earlier prompt.
- G-UNREACHABLE: loss of connectivity fails closed immediately. A running serve is not killed or restarted unless the approved Phase 3 policy says so.
- G-GENERATION: callbacks carry a generation id; a stale generation is logged and ignored.
- G-NO-LOOP: restart policy is a pure class with an injected clock. After the limit, no automatic retry.
- G-PRIVACY: dumps and the stderr log stay out of the repo, this doc, commits, and chat. Report names, sizes, and timestamps only.
- G-COMMENT: `// P9-SUPERVISE: <why> — P9-D02`. Named constants for every number.
- G-STOP / G-CLOSEOUT: stop after every phase. Closeout only on "proceed to closeout".
- G-LORE-SCOPE: no lore edits, including at closeout.
- G-LIVE: live smoke steps run one at a time; Cursor never injects turns or speaks for Brian.

## SV-G1 — Exit paths

Read 2026-10-09. No source files changed. Line numbers are the current tree.

After `NoteReady` (`HermesProcessManager.cs` 447–458) the process `Exited` handler stays attached, but it only completes the startup tasks (`ready.TrySetCanceled`, `blocked.TrySetResult`, 251–256). Those tasks are already finished, so a later exit does not change status, does not read `ExitCode`, and does not call `StartAsync`. `App.xaml.cs` 20–24 starts serve once and calls `Shutdown` on window close. Nothing calls `StartAsync` again. AUD-01/02 still match.

The client tells "unexpected" from "deliberate" only by `_shutdown` (`HermesProcessManager.cs` 20, 95–112). `Shutdown` sets that flag before it tree-kills, and only if `OwnsProcess`. There is no client-initiated restart today. Exit code is not consulted after ready. A supervisor has to treat "the client set the deliberate flag before the death" as the signal. Exit code alone cannot separate `Process.Kill` from an external terminate (both are a killed process). A native crash is the one distinctive code if it is read: `0xC0000005` (−1073741819).

| How serve ends after ready | What fires, in order | What the client can see | Unexpected? |
|---|---|---|---|
| Native crash (`c0000005`) | Child `python.exe` dies. The spawned `Process` is the venv shim (baseline parent PID 33972, child 5996). The shim usually exits with the child, so `Exited` (251–256) runs and is a no-op. Within one health period, `WatchHealthAsync` (`ChatSocket.cs` 538–561) calls `Fault` (781–815). `ShowUnreachable` (`MainWindow.xaml.cs` 1039–1058). | No exit code today. Health failure reason `GET /api/health failed`. `_shutdown` is false. | Yes |
| Python exception / non-zero exit | Same `Exited` no-op, then the health watch. Stderr may get one `[gateway-crash]` line (`tui_gateway/server.py` 54–66) before the process ends. Full traceback goes to the profile `logs/tui_gateway_crash.log`, not the client. | Same as a crash, unless the new handler reads `ExitCode`. `_shutdown` false. | Yes |
| Killed externally | Same as a crash. `Exited` no-op, then health `Fault`. | `_shutdown` false. No exit code published. | Yes |
| Killed by the client (window close) | `MainWindow` `Closed` (238–263) disposes the socket first (`ChatSocket.Dispose` 378–399 cancels `_lifetime`). The read loop treats that cancel as not a failure (524–527). Then `App` `Closed` calls `Shutdown` (22), which sets `_shutdown` and tree-kills only an owned child (121–125). `Exited` runs and is a no-op. | `_shutdown` true. `OwnsProcess` false means `Shutdown` does not kill (114–117); an attached serve is left running. | No. Must not restart and must not count. |
| Socket drops, process still alive | `ReadLoopAsync` sees Close, `WebSocketException`, or `IOException` (500–534) and calls `Fault` immediately. `WatchHealthAsync` keeps polling and exits only if health itself fails (560–561). `Fault` latches `_faulted` (789–791), so a later health success does not clear the outage. The process is not killed. | Reason text such as `the socket closed`. `ServeProcessId` still set. `GET /api/health` may still be ok. | Not an exit. G-UNREACHABLE: fail closed now. Do not kill or restart unless the Phase 3 policy says so. |
| Alive, not answering | An RPC uses `faultOnTimeout: true` and `Fault`s after 45s (`RpcTimeoutMs` 10, `CallAsync` 433–442). A hung `GET /api/health` hits the 5s `HttpClient` timeout (`HermesProcessManager.cs` 18); `ProbeHealthAsync` returns false (384–386); the watch then `Fault`s. Worst case about 2s poll (`HealthIntervalMs` 11) plus 5s. | `the request was not answered` or `GET /api/health failed`. Process still listed. | Not an exit. Same unreachable rule. |
| Attach, then the attached process dies | `AttachAsync` (149–181) sets `OwnsProcess = false` and stores no `Process`, so there is no `Exited` handler. Detection is the health watch only. | Health failure. `_shutdown` false. This window did not spawn it. | Unexpected for the UI, but this window must not have killed it. Spawning a replacement is only safe once the old process is actually gone. |

Cheap health check: `GET /api/health` is already the gate. Unauthenticated (`ProbeHealthAsync` 362–378). `ok: true` and `auth_required` are the fields. `HermesProcessManager.CheckHealthAsync` (53–63) and the 2s watch are the callers. No second ping exists. The watch stops itself on the first failure (`return` at 561), so it does not reconnect.

Attached vs spawned matters for G-DELIBERATE: only an owned child is killed on close. A restart policy that only listens to `Exited` misses an attached process and misses "socket dead, process alive."

## SV-G2 — Restart sequence

What exists today, and is not chained to an exit:

1. Token. `DashboardSessionToken.Mint` in `SpawnAsync` (185–208) sets `HERMES_DASHBOARD_SESSION_TOKEN`. After health, the client prefers the token from `GET /` (`ReadServedTokenAsync`, 329–339). A dead child with a different token is refused (331–336).
2. Spawn. `python -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0` (196–207). `HERMES_DESKTOP`, `HERMES_WEB_DIST`, and `HERMES_SERVE_HEADLESS` are removed (211–213).
3. Ready. `HERMES_BACKEND_READY port=N` (`ReadySentinel` 509–510) from either stdout or stderr (`OnLine` 220–250). Hermes writes that line to real fd 1 (`web_server_lifecycle.py` `_write_machine_sentinel_line` 402–416) because `tui_gateway/server.py` 185–188 points `sys.stdout` at stderr. Budget 90s (`ReadyTimeoutMs` 13). Failure calls `Shutdown` (298), which sets `_shutdown` and kills the child. That failure path is a deliberate kill of the attempt, not an unexpected exit.
4. Health. `WaitForHealthAsync` polls up to 45s every 500ms (343–359). `auth_required: true` refuses the socket (322–327).
5. Socket. `MainWindow.Render` (272–287) calls `ConnectAsync` once (`_connectStarted`). `ChatSocket.StartAsync` (112–116) is `OpenAsync("session.create")`. `WebSocketPermitted` (51) requires health, token, and port. `OpenAsync` (157–258) aborts the previous socket, sets `_suppressFault` around that abort (183–219), then `session.create`.
6. Which session. Startup always `session.create` (new runtime id and a new stored id). `ResumeStoredAsync` (124–131) is `session.resume` with the stored id and is used only when Brian picks a row (`MainWindow.xaml.cs` 1961). `Fault` does not clear `SessionId` or `StoredSessionId` (they are cleared only inside a later `OpenAsync`, 187–188). So the last stored id is still on the socket object after the outage. The Track 1 exit criteria say the session is re-attached. The method that does that is `ResumeStoredAsync`. `session.create` would open a new conversation and leave the old one only on disk. Resume can fail (no stored id yet, resume error, agent-build timeout). That is a failed attempt.
7. Voice re-arm. `OnSessionReady` (312–334) calls `SyncVoiceAsync` → `SyncVoiceAndWakeAsync` (`VoiceController.cs` 1549–1562): `voice.toggle` status, `on` if needed, `tts` if off, then wake arm. It is not called from `ShowUnreachable`. `OnSessionReady` also calls `OnSessionReady` on the controller (1771–1776), which invalidates any outstanding capture. That is a second invalidation, after the gap one. It must not be the first.
8. Presence during the gap. Already Dormant and link `OFFLINE` when `_unreachable` or the backend is not reachable (`ZolaDisplayState.cs` 436–438, 477–479). `LOCAL LINK • RECONNECTING` is only session switch / history load (481–483).

Where an attempt fails: resolver miss (`Fail` 73–76), ready timeout or early exit (282–301), health fail (315–319), `auth_required` (322–327), token mismatch on a dead child (331–336), `/api/ws` connect fail (211–216), `session.resume` / `session.create` not answered (237–245). `Fail` clears health, token, and `ServeProcessId` (461–466) and leaves the WebSocket gate closed. A restart that never reaches ready counts as an attempt (G-NO-LOOP).

Auto-continue (report only). `tui_gateway/session_auto_continue.py` `_maybe_schedule_auto_continue` (57–120) runs on `session.resume` when a turn marker exists, `desktop.auto_continue` is on (default true), the marker is younger than 15 minutes, and attempts are under 2 (`_auto_continue_config` 21–31). It starts a background thread that emits `status.update` "Resuming interrupted turn…", `message.start`, and `_run_prompt_submit` of `_auto_continue_note` (49–54) plus the original prompt. That is a model turn Hermes starts by itself. The reply is a normal `message.*` stream. `MainWindow.OnMessageStarted` (897–923) calls `VoiceController.OnTurnStarted` (1643–1679). In Voice mode with TTS on, `ClockEligible` (1788) sets `Speaking` true. Hermes then speaks the reply through the same TTS path as any other turn. The client never reads `display_kind`. `OnRouted` (1024–1036) would show the status line if `_unreachable` is already clear. P9-FIX-ARM: this path is not a client `prompt.submit`, so it has no origin ticket (`P9-FIX-ARM_Progress.md` exit row: crash replay gets no ticket; process memory does not survive a restart). A Workspace call logs `origin_unknown`. Send authorization is process-local (`P8-D06`). This track must not recreate either. Whether the client shows or speaks that replay is a Phase 3 decision. Not chosen here.

Generations (G-GENERATION). These can fire after a replacement is already ready:

| Source | Where | Can it arrive late? |
|---|---|---|
| `Process.Exited` | `HermesProcessManager.cs` 251–256 | Yes. The handler closes over that process's startup tasks. A new handler must no-op unless the generation matches. |
| stdout/stderr `OnLine` | 220–250 | Yes. Buffered lines, including a late `HERMES_BACKEND_READY`, can arrive after the next process has started. EOF delivers a null line. |
| In-flight `GET /api/health` | `ProbeHealthAsync` 362–378, watch 538–561 | Yes. The probe captures a URL at start. Completing it after `Port` changes must not `Fault` the new generation. |
| `ReadLoopAsync` close/error | `ChatSocket.cs` 500–534, `Fault` 781–815 | Yes. `OpenAsync` clears `_suppressFault` at 219, before the old loop has necessarily finished. Today `_faulted` latches forever, so the late close is ignored and so is every later real failure. A restart has to reset that latch per generation and ignore the old one. |
| `CallAsync` timeout | 433–442 | Yes. A 45s RPC from generation N can `Fault` after N+1 is up. |
| `message.*`, `voice.*`, `wake.detected`, `tool.*`, server requests | `DispatchEvent` 633–759 | Yes, for a frame already read. Foreign `session_id` is dropped (642–646). Empty session id is not. A `voice.transcript` has no serve generation. |
| UI queue: `OnTranscriptReady`, `ShowUnreachable`, `OnMessageStarted` | `MainWindow.xaml.cs` 208, 220, 627 | Order is enqueue order. A transcript queued before `ShowUnreachable` still runs `SubmitTurnAsync` while `_unreachable` is false (444–450). |
| Follow-up timer and `ReleasePendingStartAsync` | `VoiceController.cs` 2376–2398, pending release after idle | The follow-up generation (`BumpFollowUpGeneration` 2675–2678) is not a serve generation. A timer armed before the crash can `StartCapture` on the new socket. |
| Playback poll | `TtsPlaybackMonitor.cs` `RefreshOwnershipRoots` 526–544 | The root pid is re-read from `ServeProcessId`. A late bout-stopped from the old ffplay can change `Speaking` on the new session. |
| `StateChanged` | `HermesProcessManager.Publish` 469–474 | No generation. `MainWindow.Render` (272–287) starts the socket only once. |

The generation id has to be stored on the process, the stdout/stderr handlers, the socket, the health watch, and every UI callback that changes capture, status, or the restart counter. A mismatch is logged and ignored.

## SV-G3 — The gap

Today, on `Unreachable` → `ShowUnreachable` (1039–1058):

- Sets `_unreachable`, clears `_streaming` and `_sessionReady`, calls `AbandonPendingQuestion("unreachable")` (`VoiceController.cs` 541–556), clears tool activity, sets the status line, calls `UpdateChrome` (1806–1848).
- `AbandonPendingQuestion` clears the question-speech token and `QuestionSpeaking`. It does not call `InvalidateCapture` (2402–2436).
- `UpdateChrome` disables the composer, Send, Cancel, Stop, sessions, and new-session. `SetAwaitingAnswer` becomes false (1812). `ApplyVoiceChrome` (714–725) passes `BackendReachable: false` into `SetCaptureGate` (1017–1028), so a new capture cannot start (`CanStartCapture` 413).
- An open capture stays `Accepting`. A deferred follow-up / clarify pending start stays pending. `_pendingTranscriptAt` (2183) is not cleared.
- `OnTranscriptReady` (627–651) does not check `_unreachable`. It answers a bound clarify or calls `SubmitTurnAsync`. `SubmitTurnAsync` (444–450) does check `_unreachable` and `_sessionReady`, but only when it runs. A transcript already queued on the UI thread runs first and submits. That is the AUD-04 hole.
- Clarify and approval cards are broker state. `ShowUnreachable` does not close them. A reviewed Gmail draft and its send authorization live in serve memory (`P8-D06`) and die with the process. The client does not have a copy to replay. G-NO-AUTHORITY-CARRYOVER is already true for that state, as long as this track does not recreate it.
- Playback. Presence mode becomes Dormant before the Speaking branch (`ZolaDisplayState.cs` 436–446), and the link becomes `OFFLINE` (477–479). `ShowUnreachable` does not clear `VoiceController.Speaking` and does not call `StopSpeakingAsync` or `TtsPlaybackMonitor.StopMonitoring`. The Stop button hides because `_unreachable` is set (1837–1838). If the process is dead, ffplay dies with it. If the process is alive and only the socket is down, audio keeps playing.
- The VOICE label does not look at `_unreachable` (`ZolaDisplayState.cs` 341–374). It can still say LISTENING or SPEAKING. The mic line can still say `Mic: recording` while `CaptureActive` (398–400).

What Brian sees and hears today: notice text `Backend unreachable. …`, detail `hermes serve is not reachable. This window will not keep waiting.` (`ShowUnreachable` 1054–1057), HUD link OFFLINE, presence Dormant, composer disabled. He can still see a listening/speaking label. He hears nothing further if the process died. He can keep hearing the current reply if the process is still alive.

The first gap actions, before any restart await, have to be synchronous on the same path that admits transcripts:

1. Latch the outage and bump the serve generation so a transcript already in `OnVoiceTranscript` (`VoiceController.cs` 2089–2236) fails `TranscriptAdmission.Decide` (`TranscriptAdmission.cs` 67–96: gated, or `Cancelled` / no owner).
2. `InvalidateCapture` (2402) so the outstanding capture and a follow-up/echo pending start are dropped. `Cancel` discards follow-up and echo pending (`CaptureLifecycle.cs` 383–386). Clarify pending is kept by that method (385); the gap path has to `DiscardPending` as well (278–291).
3. Clear `_pendingTranscriptAt` and do not raise `TranscriptReady` for this generation. `OnTranscriptReady` / `SubmitTurnAsync` must refuse a stale generation even if already queued.
4. `AbandonPendingQuestion`, and stop local playback: `SetSpeaking(false)` (2689) plus `TtsPlaybackMonitor.StopMonitoring` (126). A `voice.record stop` or `voice.toggle off` is best-effort only after the local invalidate, because the socket may already be dead. Those RPCs must not be required for the fail-closed result.
5. Only then start the restart. A transcript captured before or during the gap is never passed to `prompt.submit` on the new process.

## SV-G4 — WER local dumps

`[EXT]` Microsoft Learn, "Collecting User-Mode Dumps" (https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps), read 2026-10-09:

- Not enabled by default. Enabling requires administrator privileges.
- Key: `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps`.
- Per-application override: a subkey named for the exe, e.g. `...\LocalDumps\python.exe`. WER reads the global values, then the exe subkey overrides them.
- `DumpFolder` (`REG_EXPAND_SZ`), default `%LOCALAPPDATA%\CrashDumps`. A custom folder needs an ACL that lets the crashing process write.
- `DumpCount` (`REG_DWORD`), default 10. Oldest file is replaced after the cap. This is a count, not an age.
- `DumpType` (`REG_DWORD`): 0 custom, 1 mini (default), 2 full.
- `CustomDumpFlags` applies only when `DumpType` is 0. Default `0x121` (`MiniDumpWithDataSegs | MiniDumpWithUnloadedModules | MiniDumpWithProcessThreadData`).
- The page documents HKLM only. It does not say HKCU is honored. This machine: HKCU `LocalDumps` absent; HKLM key present with no default values; subkeys only `EADesktop.exe`, `EALauncher.exe`, `ErrorReporter.exe` (`DumpFolder` `%LOCALAPPDATA%\CrashDumps`, `DumpCount` 10, `DumpType` 1). No `python.exe` subkey (Phase 1 baseline).

Faulting image. P9PRE Audit 01 §6 and `P7-FORENSIC-SERVE_Findings.md` 28–29: faulting application name `python.exe`, path the uv CPython `...\uv\python\cpython-3.12-windows-x86_64-none\python.exe`, exception `c0000005`. The client `Process` object is the venv shim, also named `python.exe`. A `LocalDumps\python.exe` key matches on the file name, not the full path. It catches every other `python.exe` on this machine, including the Blender MCP interpreters that were running at the Phase 1 baseline. Their dumps would land in the same folder and can hold whatever those processes had in memory. The folder stays private; the key cannot be limited to Hermes.

Proposal (Phase 3 decides; any `reg add` is Brian's, elevated):

- Folder: `%LOCALAPPDATA%\ZolaClient\dumps` (`C:\Users\test\AppData\Local\ZolaClient\dumps`).
- ACL, Brian's account only (icacls shows that account as `DESKTOP-VRB5NB9\test`):

```
mkdir "%LOCALAPPDATA%\ZolaClient\dumps"
icacls "%LOCALAPPDATA%\ZolaClient\dumps" /inheritance:r
icacls "%LOCALAPPDATA%\ZolaClient\dumps" /grant:r "%USERNAME%:(OI)(CI)F"
```

- `DumpCount` = 3, `DumpType` = 1 (mini). Full dumps (`DumpType` 2) hold the whole process, including tokens and conversation text. Mini is the recommendation unless Brian approves full.
- Registry, admin:

```
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpFolder /t REG_EXPAND_SZ /d "%LOCALAPPDATA%\ZolaClient\dumps" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpCount /t REG_DWORD /d 3 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpType /t REG_DWORD /d 1 /f
```

- 14-day deletion is not a WER feature. Proposal: the client, on startup, deletes files in that folder older than a named retention constant (14 days), and never follows a junction out of the folder. A manual delete is the alternative. No scheduled task.
- Verification later is a registry read and the ACL. No native crash is induced.

## SV-G5 — stderr

Today both pipes are redirected (`HermesProcessManager.cs` 193–194) and drained (`BeginOutputReadLine` / `BeginErrorReadLine`, 278–279) into `OnLine` (220–247). Lines are appended to an in-memory `StringBuilder` capped at 16,000 characters, and that buffer is shown only if startup fails (290–300). After ready, lines are still drained and then discarded. An undrained redirected pipe can block the child once the OS buffer fills. The current drain prevents that. A file writer has to keep draining on the same callbacks.

Where Hermes actually writes, from the pin (no second serve was started; the live client already owns the pipes):

- Normal Python logs go to files under the profile `logs/` (`agent.log`, `errors.log`, and `gui.log` because `serve` uses logging mode `gui`). `hermes_logging.py` `setup_logging` (163–217) uses rotating files, not stderr. Stderr console logging is only `setup_verbose_logging` (220–232), and the client does not pass `--verbose`.
- `tui_gateway/server.py` 185–188 assigns `sys.stdout = sys.stderr`, so a later `print()` hits the stderr pipe. The ready sentinel does not: it is `os.write(1, ...)` (`web_server_lifecycle.py` 402–416).
- The startup line `Hermes backend listening on 127.0.0.1:<port>` is a `print` (`web_server.py` 1271–1274) and therefore lands on stderr.
- uvicorn is created at `log_level="warning"` (`web_server.py` 1175–1187). Warning and error lines use uvicorn's stderr handler. Access lines are info and are not emitted at that level.
- An unhandled exception writes one stderr line `[gateway-crash] <type>: <first line of the message>` (`server.py` 63–66). That first line can contain request text if the exception message does. The traceback itself goes to `logs/tui_gateway_crash.log`.
- Plugin debug on stderr runs only when `HERMES_PLUGINS_DEBUG=1` (`hermes_cli/plugins.py` 83–106). The client does not set it.

Categories a normal start puts on stderr: the listening line, uvicorn warnings, Python warnings, and (only on a Python crash) the one gateway-crash summary line. No prompt, reply, or email body is written by those normal paths. The crash line is the one that might quote user text, which is why the file is treated as sensitive anyway.

Proposal: `%LOCALAPPDATA%\ZolaClient\logs\serve-stderr.log`, rotating, with named constants for max bytes, file count, and retention days. The existing log folder ACL is not Brian-only. `icacls` on `C:\Users\test\AppData\Local\ZolaClient\logs` shows inherited Full control for `NT AUTHORITY\SYSTEM`, `BUILTIN\Administrators`, and `DESKTOP-VRB5NB9\test`. A dedicated stderr directory should drop inheritance and grant only `%USERNAME%:(OI)(CI)F`, same shape as the dump folder.

## SV-G6 — ProcessSupervisor

One supervisor per named process, own counters, own generation. Serve is the only caller in this track. Track 3 constructs a second instance named for the watcher and does not touch serve's object.

Suggested shape (pure policy separate from process I/O):

- `RestartPolicy` with an injected clock. States the Phase 3 table will name. `NoteUnexpectedExit(time) -> attempt | terminal`. `NoteDeliberateStop()` never consumes an attempt. `NoteReady(time)` does not clear the window; only a manual reset does. `Reset(time)` clears the terminal state. After the limit, every further `NoteUnexpectedExit` returns terminal and does not ask for a spawn.
- `ProcessSupervisor` holds the name, the generation, the policy, and the deliberate flag. `Start` bumps the generation and returns it. Every exit, ready, socket, and health callback takes that generation and returns immediately on a mismatch (logged). `StopDeliberate` sets the flag before any kill. `NoteReady` records ready for that generation. An exit before ready still counts as an attempt when the exit was not deliberate.

`HermesProcessManager` keeps spawn, token, ready sentinel, and health. It asks the supervisor whether an unexpected exit or a failed ready may spawn again. It does not own the counter. Window close calls `StopDeliberate` then the existing `Shutdown`. Track 3's watcher would call the same supervisor methods with a different name and its own start/ready/stop functions.

G-UNREACHABLE stays a separate decision from the exit policy: socket loss with the process alive fails closed and does not call `NoteUnexpectedExit` unless the approved policy says to kill and replace.

## SV-G7 — Client tests

No xUnit or MSTest project. `windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj` is a `net9.0` console exe with no `PackageReference`. It compiles pure sources by `Compile Include` link (`CaptureLifecycle.cs`, `TranscriptAdmission.cs`, and other WinUI-free files). `Zola.Client.csproj` itself references Helix and the Windows App SDK; those are already restored and are the wrong place for a policy test.

Smallest proposal: a pure `RestartPolicy` (and a small gap/generation fake) linked into `Zola.Client.Checks`, same pattern as voice authority. That needs no NuGet restore and no new package (`P2-D17`). An xUnit project would be a new package restore and needs a STOP approval. Not proposed unless Brian asks for it.

Tests to run there:

- Rolling window: 3 unexpected exits inside 10 minutes are attempts; a 4th is terminal; an exit just outside the window is allowed again. Clock is injected.
- `NoteDeliberateStop` never increments and never enters the terminal state.
- A ready timeout or failed spawn counts as an attempt.
- After the limit, further exits do not request a spawn. `Reset` clears it.
- Gap order with fakes: invalidate, drop pending transcript, stop playback, block input, and only then `Start`.
- A callback stamped with generation N, delivered after N+1 is ready, does not change status, capture, or the counter.
- Socket loss with the process still "alive" takes the unreachable path and does not kill unless the approved policy says so.
- A reconnect does not submit a transcript that was admitted under the old generation.

## Phase 2 notes

- Lore read for the binding lines: `P2-D17` (`DESIGN_DECISIONS.md` 383–389), `P4-D25` (760–761), `P8-D02` (1343–1370), `P8-D06` (1412–1438), `S51` (`OPEN_QUESTIONS.md` 290–304), `S69` (400), `S70` (402). No lore edit.
- No scratch process was started. The live client already owns serve's pipes, and a second serve was not spawned.
- Code and the P9PRE audit agree on the behavior. The audit's "nothing subscribes after ready" is slightly tighter than the code: the startup `Exited` handler remains connected and becomes a no-op. Behavior is unchanged: no restart.

## Phase 3 proposal

Written 2026-10-09. No source files modified. Live `config.yaml` was read and not edited. Nothing below is applied until Brian's verdicts.

Named constants for the whole proposal:

| Constant | Value |
|---|---|
| `RestartLimit` | 3 |
| `RestartWindow` | 10 minutes, rolling |
| `RestartBackoffSeconds` | 2 |
| `ReconnectAttemptLimit` | 5 |
| `ReconnectSpacingSeconds` | 5 |
| `ReconnectBudgetSeconds` | 30 |
| `ServeStderrMaxBytes` | 1,048,576 |
| `ServeStderrMaxFiles` | 3 |
| `ServeStderrRetentionDays` | 14 |
| `DumpCount` | 3 |
| `DumpType` | 1 (mini) |
| `DumpRetentionDays` | 14 |

### 1. Restart policy

One `RestartPolicy` per supervised name, injected clock, generation on every row. Serve is the only name wired in this track.

| State | Generation | Event | Next | Restarts left |
|---|---|---|---|---|
| Running | G | Unexpected exit of G (crash, external kill, Python exit) | BackingOff | 2, then 1, then 0 |
| BackingOff | G | `RestartBackoffSeconds` elapsed, and the rolling window still has room | Restarting, spawn G+1 | unchanged (the exit already counted) |
| Restarting | G+1 | Ready sentinel, health, socket, `ResumeStoredAsync` all succeed | Running | unchanged |
| Restarting | G+1 | Spawn, ready, health, socket, or resume fails | BackingOff if any restarts remain, otherwise KeepsFailing | the failed spawn already counted as the attempt that opened G+1 |
| Running | G | App shutdown, or any kill the client set as deliberate before the kill | StoppedDeliberately | unchanged, and this exit is not stored in the window |
| KeepsFailing | any | Further exits, failed health, or stale callbacks | KeepsFailing | 0, no spawn |
| KeepsFailing | — | Brian quits and opens Zola again | Running on a new supervisor | 3 |
| any | — | Callback whose generation is not the current one | same state | unchanged; the callback is logged and ignored |

An attempt is an unexpected exit after ready, a spawn that never becomes ready, or the hung tree-kill below. A socket reconnect while health is OK does not count. After three attempts in the rolling 10 minutes, the state is KeepsFailing and no automatic retry runs. Closing the client drops the in-memory counters. The status line in that state tells Brian to open Zola again. There is no in-app Try again button in this proposal.

Before every spawn, the client tree-kills the previous generation:

- Owned serve: `Process.Kill(entireProcessTree: true)` on the shim the client started (venv `python.exe`). That tree is the shim, the uv CPython child, and ffplay.
- If the CPython child has been reparented because the shim already exited, kill the process that `ZolaServeCommand.IsDedicatedServe` matches and whose start belongs to that generation. Blender MCP `python.exe` processes do not match that command line.
- Attached serve (`OwnsProcess` false): window close still does not kill it. If that PID is already dead, spawn an owned serve. If it is alive and health is failing, the hung row below tree-kills it and counts a restart. If it is alive and health is OK, the client only reconnects the socket.

Smoke R1 and R2 kill the real interpreter, not the shim. Cursor identifies it as the `python.exe` whose parent PID is the shim (`HermesProcessManager`'s process id, image under `hermes-agent\.venv\Scripts\python.exe`) and whose executable path contains `\uv\python\cpython`. The Phase 1 baseline pair was shim 33972 and child 5996.

### 1a. Unreachable policy

Health check remains `GET /api/health` (`HermesProcessManager.ProbeHealthAsync`). A running serve is killed only on the hung row.

| State | Generation | Event | Next | Counts against `RestartLimit`? |
|---|---|---|---|---|
| Connected | G | Socket lost, process alive, health OK | Fail closed immediately, then UnreachableReconnecting | No |
| UnreachableReconnecting | G | Health still OK, `/api/ws` opens, `ResumeStoredAsync` succeeds, inside the budget | Connected, same process, same G | No |
| UnreachableReconnecting | G | Health fails while the process is alive | Tree-kill G, then the restart table (BackingOff) | Yes |
| Connected | G | Health fails while the process is alive (hung) | Tree-kill G, then the restart table | Yes |
| UnreachableReconnecting | G | 5 attempts made, or 30 seconds elapsed, and health is still OK | KeepsFailing; the process is left running | No |
| Connected | G | Process already gone | Restart table, unexpected exit | Yes |

Reconnect attempts are spaced `ReconnectSpacingSeconds` apart and stop when `ReconnectAttemptLimit` or `ReconnectBudgetSeconds` is reached, whichever comes first. Each attempt probes health, then opens the socket and calls `ResumeStoredAsync`. A successful reconnect re-arms voice with `SyncVoiceAndWakeAsync` and does not restore a capture, a pending transcript, or a clarify answer from before the loss. A stale socket-closed from generation G after G+1 is ready does not start this table.

### 2. Gap behavior

On the thread that reads the socket, before any await and before a restart or reconnect:

1. Latch the outage and bump the generation the admit path checks. `OnVoiceTranscript` (`VoiceController.cs` 2089) and `SubmitTurnAsync` (`MainWindow.xaml.cs` 444) both refuse a transcript whose generation is not current.
2. `InvalidateCapture` (`VoiceController.cs` 2402) with reason `backend-unreachable`, then `CaptureLifecycle.DiscardPending` (`CaptureLifecycle.cs` 278) so a deferred clarify start is dropped too.
3. Clear the pending-transcript timestamp so a `TranscriptReady` already queued on the UI thread does not call `prompt.submit` or `AnswerClarify`.
4. `AbandonPendingQuestion("unreachable")` (`VoiceController.cs` 541).
5. Stop the local speaking flag (`SetSpeaking(false)`) and force the playback monitor inactive.
6. Stop audio, per section 5.
7. Status line and presence, then chrome. Composer, Send, mic, and clarify answers stay blocked.

Status line while restarting or reconnecting: `Zola's backend stopped. Restarting…`

Status line in KeepsFailing: `Zola's backend keeps failing. Restart Zola to try again.`

Presence mode stays Dormant. Link label stays `OFFLINE`. The voice label becomes `Offline` for the whole gap so it does not keep saying Listening or Speaking.

### 3. Crash replay

Recommended, for Brian to accept or replace: after every successful restart or reconnect, call `ResumeStoredAsync` with the stored id `Fault` leaves on the socket, and set `desktop.auto_continue.enabled` to false in the live profile.

The other rows stay available:

| Option | What Brian gets |
|---|---|
| (a) Leave Hermes as it is | `session.resume` with the pin default (enabled) starts a model turn by itself when a fresh crash marker exists. The client shows that turn and, in Voice mode with TTS on, speaks it. |
| (b) Show, do not auto-speak | The Hermes turn still runs. The client paints `message.*` and does not speak a reply that arrives before Brian's next turn. |
| Recommended | Resume the stored session, and disable auto-continue. The conversation comes back. Hermes does not re-submit the interrupted prompt. No origin ticket is minted. |
| (d) `session.create` | A new empty conversation. The old one stays on disk until Brian picks it in the session list. |

Live file: `C:\Users\test\AppData\Local\hermes\profiles\zola\config.yaml`. It has no `desktop:` key (file ends at the `skills.disabled` list, line 123). Effective config is that file deep-merged over the pin defaults (`hermes_cli/config.py` `_deep_merge`, 1498–1513). The pin default is `hermes_cli/config_defaults.py` 2333 and 2363–2370:

```yaml
desktop:
  auto_continue:
    enabled: true
    freshness_minutes: 15
    max_attempts: 2
```

Before: the live file does not contain `desktop` or `auto_continue`. The running value of `desktop.auto_continue.enabled` is the default `true`.

After, appended only after approval, under P4-D25 (backup the file into the scratch folder first; apply in Phase 6 after the old serve is gone and before the new client starts):

```yaml
# P9-SUPERVISE: do not re-submit an interrupted turn when a session is resumed — P9-D02
desktop:
  auto_continue:
    enabled: false
```

`freshness_minutes` and `max_attempts` stay at the pin defaults because a one-leaf override deep-merges.

What else this key changes. `_maybe_schedule_auto_continue` (`session_auto_continue.py` 57–73) runs from `session.resume` on the cold and eager paths (`methods_session.py` 780 and 834). That includes Brian picking a row in the session list after an app restart, not only a crash restart. With `enabled` false, a fresh crash marker is cleared and the recovered partial transcript is what resume shows. No model turn starts. `session.create` does not consult the key. Queued-prompt drain and busy-submit in the same module do not consult it. `agent.gateway_auto_continue_freshness` is a different setting and is unchanged. A marker that already has `auto_continue: false` (mailbox-owned) was already skipped.

### 4. WER

Microsoft Learn, "Collecting User-Mode Dumps" (https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps), read 2026-10-09: enabling LocalDumps requires administrator privileges under HKLM. The page says a custom `DumpFolder` must have an ACL that allows the crashing process to write, and that a service crash is written using that service account's profile (`System32\Config\SystemProfile` for System, `ServiceProfiles` for Network and Local Services). Zola's `python.exe` is an interactive user process, so the writer that must be able to create the file is the user account `DESKTOP-VRB5NB9\test`. The page does not say the interactive dump is written as SYSTEM. `NT AUTHORITY\SYSTEM` is granted as well because WerSvc runs as SYSTEM and participates in collection; if this Windows build has WerFault write the file as SYSTEM, a user-only folder would fail.

Folder: `C:\Users\test\AppData\Local\ZolaClient\dumps`. Inheritance removed. Only the user and SYSTEM.

Brian runs the admin `reg add`. Cursor can create the folder and ACL without elevation.

```
mkdir "C:\Users\test\AppData\Local\ZolaClient\dumps"
icacls "C:\Users\test\AppData\Local\ZolaClient\dumps" /inheritance:r
icacls "C:\Users\test\AppData\Local\ZolaClient\dumps" /grant:r "DESKTOP-VRB5NB9\test:(OI)(CI)F"
icacls "C:\Users\test\AppData\Local\ZolaClient\dumps" /grant:r "NT AUTHORITY\SYSTEM:(OI)(CI)F"
```

```
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpFolder /t REG_EXPAND_SZ /d "C:\Users\test\AppData\Local\ZolaClient\dumps" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpCount /t REG_DWORD /d 3 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpType /t REG_DWORD /d 1 /f
```

`DumpType` 1 is a mini dump. The key matches every `python.exe` on the machine, including Blender MCP. The client deletes files in this folder older than `DumpRetentionDays` on startup and does not follow a junction out of the folder. WER's own `DumpCount` only caps the count at 3.

Optional, off unless Brian explicitly approves it as an exception to "never induce a native crash": Cursor starts one throwaway `python.exe` from `C:\Users\test\Dev\zola-spikes\p9-supervise` that faults with an access violation. That process is not Hermes and not the live profile. Cursor then reports the new dump's file name, size, and timestamp only, and deletes that dump. No Zola process is killed.

### 5. Playback while serve is alive

ffplay is a child of serve. `tools/voice_mode.py` `stop_playback` (949–961) runs inside serve: it `terminate()`s the active player subprocess and calls `sounddevice.stop()`. `_tts_stream_stop` (`methods_voice.py` 117–134) calls it. `voice.toggle` action `off` reaches that through `_set_voice_tts(False)` (652–657). That RPC needs an open socket.

While the socket is down, the client cannot call it. Two local facts:

- ffplay can be stopped from the client. `TtsPlaybackMonitor.IsHermesOwned` (354–394) already walks at most two parents from an `ffplay` audio-session PID up to the serve root. The gap kills those owned ffplay PIDs. That does not kill serve.
- WAV playback on Windows tries in-process `sounddevice` first (`play_audio_file`, 1098–1100; `_sounddevice_output_allowed` is true off macOS). That audio has no PID the client can kill. It stops when `stop_playback` runs, or when the python process is tree-killed.

Proposal: kill owned ffplay during the gap; clear the local Speaking flag immediately. On the hung path, the tree-kill stops both ffplay and sounddevice. On the socket-loss path, the first successful reconnect sends `voice.toggle` action `tts` only if a dedicated stop is unavailable: the existing stop that actually calls `stop_playback` is toggle-off's `_set_voice_tts(False)`, which also clears `HERMES_VOICE_TTS`. The client then sends `tts` again so spoken replies stay on, the same restore `StopSpeakingAsync` already does, and it does this before it applies `message.*` from the resumed session. In-process audio can continue until that reconnect RPC.

### 6. stderr

Directory `C:\Users\test\AppData\Local\ZolaClient\logs\serve-stderr\`, inheritance removed, grant only `DESKTOP-VRB5NB9\test:(OI)(CI)F`. The client writes this file as that user, so SYSTEM is not required here. Rotate at `ServeStderrMaxBytes`, keep `ServeStderrMaxFiles`, delete files older than `ServeStderrRetentionDays`. Keep draining the pipe so serve cannot block on a full stderr buffer.

Normal categories from the pin (Phase 2): the listening line, uvicorn warnings, Python warnings, and on a Python crash one `[gateway-crash]` summary line whose text can quote an exception message. Treat the file as sensitive.

### 7. ProcessSupervisor

`RestartPolicy` is pure and clock-injected. `ProcessSupervisor` holds the process name, the generation, the deliberate flag, and one policy. `Start` bumps the generation. Exit, ready, socket, and health callbacks carry that generation and return on a mismatch. `StopDeliberate` is set before any kill the client intends. `HermesProcessManager` keeps token, spawn, sentinel, and health, and asks the supervisor whether a spawn is allowed. Track 3 builds a second supervisor named for the watcher. It does not share serve's counters.

### 8. Tests

Link the pure policy into `Zola.Client.Checks` (existing console exe, no new package, no NuGet restore). Tests: rolling window and the 4th exit; deliberate exits; a failed ready counts; terminal state; manual reset via a new policy instance; gap order (invalidate, drop transcript, stop playback flag, block input, then start); stale generation N after N+1 is ready; socket loss with health OK does not count a restart and submits nothing old; health failure while the process is alive consumes one restart; reconnect budget exhaustion enters KeepsFailing without a spawn.

### 9. Risks

- The hung path kills an attached serve this window did not spawn. Window close still does not.
- `desktop.auto_continue.enabled: false` also changes session-list resume, as section 3 says.
- `LocalDumps\python.exe` covers every Python on the machine.
- In-process sounddevice audio can continue until the reconnect RPC.
- Killing the CPython child in R1/R2 should also end the shim. If the shim stays up, the supervisor still tree-kills it before the next spawn.
- This does not diagnose `S51`.

## Brian's verdicts

Recorded verbatim from the Phase 4 proceed message.

1. Restart policy: approved as proposed (3 in a rolling 10 minutes, 2 s backoff, quit and reopen clears
   KeepsFailing, tree-kill the previous generation before every spawn, smoke kills the CPython child).
2. Unreachable policy: approved with two changes.
   a. Fail closed on the first health failure, but declare "hung" and tree-kill only after
      HungHealthFailureLimit consecutive failed probes (3, about 20 s). Named constant.
   b. When reconnects are exhausted (5 attempts / 30 s) with health OK, tree-kill and restart, counting
      against RestartLimit. Do not leave that process running.
3. Generations: keep two counters. Process generation bumps on every spawn. Connection epoch bumps on
   every connectivity loss, including socket-only loss on the same process. Transcript admission,
   SubmitTurnAsync and clarify answers refuse anything from an earlier connection epoch. Both counters
   are thread-safe (Interlocked or equivalent); show where each is bumped and checked.
4. Gap behavior and status text: approved as proposed.
5. Crash replay: the recommended option. Resume the stored session, and set
   desktop.auto_continue.enabled: false in the live config.yaml exactly as shown, applied in Phase 6
   with a backup.
6. Playback: approved. After a reconnect, restore the TTS state Brian had before the loss; do not force
   it on.
7. WER: approved as proposed (user + SYSTEM ACL, mini dumps, count 3, client prunes after 14 days).
   I will run the reg add commands myself.
8. Scratch crash test: approved as an exception to "never induce a native crash." One throwaway
   python.exe from the scratch folder only, report name/size/timestamp, then delete the dump.
9. stderr log: approved as proposed.
10. Tests: approved, linked into Zola.Client.Checks, no new packages. Add tests for 2a, 2b and 3.

Verdicts 2a, 2b, and 3 replace the proposal rows that tree-killed on the first health failure, left a process running after reconnect exhaustion, and used one generation counter. Verdict 5's `config.yaml` edit is Phase 6, not Phase 4. Verdict 7's `reg add` is Brian's, in Phase 6. Verdict 8's scratch crash is Phase 6.

### Where the two counters move

Process generation (`ServeGenerations.BumpProcessGeneration`, `Interlocked.Increment`):

- Bumped at the start of `HermesProcessManager.SpawnAsync`, before the child is published, and at the start of `AttachAsync`.
- Checked in the `Exited` handler (`IsCurrentProcess`), in `ChatSocket.Fault` (stale fault returns), and in `ProcessSupervisor.NoteLoss` (stale loss is logged and ignored).

Connection epoch (`ServeGenerations.BumpConnectionEpoch`, `Interlocked.Increment`):

- Bumped in `OutageGap.Apply`, which `ProcessSupervisor.NoteLoss` calls on every connectivity loss that passes the stale check, including a socket-only loss on the same process.
- Checked in `VoiceController.OnVoiceTranscript` before admission, in `MainWindow.OnTranscriptReady` before a clarify answer, and in `MainWindow.SubmitTurnAsync` before `prompt.submit`. `ChatSocket.Fault` also ignores a fault whose captured epoch is no longer current. `ConnectionEpochGuard.Allows` is equality. Epoch 0 is the first connection, not "none".

## Phase 4

Implemented on `p9-supervise` (no commit). Client builds with 0 warnings and 0 errors.

- `RestartPolicy` is pure and takes the clock from the caller. `ProcessSupervisor` runs the loop. `HermesProcessManager` owns the policy and the two counters, tree-kills before a replacement spawn, and does not use `Shutdown()` for a failed start.
- First health failure fail-closes. The third consecutive failed probe (`HungHealthFailureLimit` = 3, spaced by `HungProbeSpacingSeconds` = 10) tree-kills and counts. Five reconnects or 30 seconds with health still OK tree-kills and counts. A dead process restarts after `RestartBackoffSeconds` = 2 and does not wait out the hung count.
- Gap order is `OutageGap.Apply`: bump epoch, invalidate capture, drop the pending transcript, stop local speech and owned ffplay, block input. Status text is the approved restarting and keeps-failing lines. Voice label is `Offline` while unreachable. Presence stays Dormant and the link stays `OFFLINE`.
- Recovery calls `ResumeStoredAsync` when a stored id exists, otherwise `session.create`. TTS is restored from the snapshot taken at the loss, before `session.resume`, and the post-resume sync does not force TTS on. The live `config.yaml` edit is not applied.
- stderr goes to `%LOCALAPPDATA%\ZolaClient\logs\serve-stderr` (rotate at 1 MiB, 3 files, 14 days, user-only ACL). Startup deletes dump files in `%LOCALAPPDATA%\ZolaClient\dumps` older than 14 days and does not follow junctions. No registry change.

## Test results

Client checks, final tree: 0 failed. Coverage: lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 17/17.

Supervision rows include 2a (first two health failures do not kill; the third tree-kills and counts), 2b (five reconnects, and a 30 second budget, tree-kill and count; socket loss does not count until that kill), and 3 (independent bumps, an earlier epoch is refused, a socket-only loss bumps only the epoch, a stale process generation is not current).

Plugin suites, unchanged sources: zola_workspace 177 OK, zola_memory 117 OK, zola_tools 44 OK. The workspace run must use the tests directory as the unittest top, because those modules import siblings by bare name. A first run with the plugin directory as top reported 111 and 2 import errors; that was the runner layout, not a suite change. The rerun was 177 OK.

`hermes-agent` HEAD `345cd2b057a452236de401d3534b8502a7465e8d`, porcelain empty.

Not done in this phase: WER `reg add`, the scratch crash, and the live `config.yaml` backup and edit.

## Phase 5

Review fixes applied. No commit.

1. `ServeStderrLog.EnsureAcl` keeps `_aclApplied` false unless both `icacls` calls exit 0. A nonzero exit, a missing process, or a timeout does not write the stderr file. The pipe is still drained. One `supervisor proc=serve event=stderr_acl_failed` line is written. A later failure does not log again.
2. `ConnectStoredOrNewAsync` no longer clears `_unreachable` before the session exists. `OnSessionReady` clears it only when the ready event's connection epoch is still current. A resume that returns without a session id, or throws, leaves the outage state and status line in place.
3. After a socket-only loss the process generation stays the same and the connection epoch bumps. A capture that was Accepting is cancelled in the gap (`backend-unreachable`), so it is `Cancelled`. A `voice.transcript` stamped with the new epoch passes `ConnectionEpochGuard` and is refused by `TranscriptAdmission` with reason `cancelled`.
4. `SupervisionLog.Write` and `Format` take the process name. Serve passes `SupervisionConstants.ProcServe`.

(a) `KillGenerationForRestart` and `IsServeProcessAlive` act on every dedicated Zola serve on the machine, consistent with the existing one-serve attach model (P1-D01).

(b) The reusable part for Track 3 is `RestartPolicy`. `ProcessSupervisor` is serve-specific, and Track 3 builds a watcher supervisor on the same policy (deviation from the plan's wording, accepted).

## WER setting as applied

Folder created and ACL applied 2026-10-10. Brian ran the three `reg add` commands. Read back 2026-10-10 15:51 local:

- Folder: `C:\Users\test\AppData\Local\ZolaClient\dumps`
- ACL, inheritance removed: `NT AUTHORITY\SYSTEM:(OI)(CI)(F)` and `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only
- `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe`
  - `DumpFolder` `REG_EXPAND_SZ` `C:\Users\test\AppData\Local\ZolaClient\dumps`
  - `DumpCount` `REG_DWORD` `0x3`
  - `DumpType` `REG_DWORD` `0x1`
- `HKCU\...\LocalDumps\python.exe`: absent

Verdict 8 scratch crash, 2026-10-10 15:53 local. One throwaway `python.exe` from `C:\Users\test\Dev\zola-spikes\p9-supervise`, not the live serve (client 8984, shim 33820, child 38008 stayed up). Dump `python.exe.21768.dmp`, 1991744 bytes, written 2026-10-10 15:53:06. Deleted. The dumps folder was empty afterward. Dump contents were not read.

The commands Brian ran:

```
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpFolder /t REG_EXPAND_SZ /d "C:\Users\test\AppData\Local\ZolaClient\dumps" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpCount /t REG_DWORD /d 3 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe" /v DumpType /t REG_DWORD /d 1 /f
```

## Smoke results

Cursor-run steps, 2026-10-10 afternoon. Human steps V1–V4 not started.

Live `config.yaml` was backed up to `C:\Users\test\Dev\zola-spikes\p9-supervise\config.yaml.bak-before-auto-continue` (4166 bytes, prefix unchanged) and then the approved `desktop.auto_continue.enabled: false` block was appended. No `freshness_minutes` or `max_attempts` were written. No Zola client and no dedicated serve were running at the edit.

An idle draft is not a database row until the first prompt (Hermes `session.create`). Resuming that key returns "session not found". The first two launches treated that as a failed reconnect, tree-killed about every 30 seconds, and reached `keeps_failing` without further kills. `ConnectStoredOrNewAsync` now falls back to `session.create` only for that error. The runs below are after that fix, on a new client process.

R1. Killed CPython child 6844 (parent shim 33044) at 14:50:23. Log: `supervisor proc=serve event=restart restarts=1 generation=1`. Replacement: shim 32284 parent client 9812, CPython child 36572 parent 32284, start 14:50:27. Display returned to connected and listening. No second restart in the next 20 seconds.

R2. Same client 9812, still inside the window.
- 14:51:09 killed 36572 → `event=restart restarts=2 generation=2`. Next child 3644.
- 14:51:19 killed 3644 → `event=restart restarts=3 generation=3`. Next child 19092.
- 14:51:29 killed 19092 → `event=keeps_failing restarts=4 generation=4`. No serve process remained. The client stayed open and the link went offline.

R3. WM_CLOSE of client 9812. No serve left, and no restart line. Relaunch at 14:52:12: client 29348, shim 27656, CPython 18988. Display connected. No supervisor lines after the relaunch (new policy, not terminal).

R4. WM_CLOSE of that healthy client at 14:52:29, while it was listening. Client exited. Serve count was 0 six seconds later. No new supervisor lines. No failing state.

R5. `%LOCALAPPDATA%\ZolaClient\logs\serve-stderr\serve-stderr.log`, 614 bytes, last write 2026-10-10 14:52:16. Directory ACL is `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only. Rotation was not forced live.

R6. Covered by unit tests only. No live hang was induced.

Armed check after R4, client closed, read-only: `state_meta` heartbeat 0, loop 0, goal 0. `cron/jobs.json` absent.

V1, 15:15:10. Brian was in a wake capture (listening since 15:14:54). Killed CPython 35424. Capture cancelled `reason=backend-unreachable`. Log: `supervisor proc=serve event=restart restarts=1 generation=1`. Replacement child 38008 at 15:15:14. Link returned at 15:15:18. No `prompt.submit` of that turn. The local recording latch stayed up because the dead process never sent idle, so the window kept showing Listening / Mic: recording and a later wake was ignored (`wake ignored: capture` at 15:16:34). The gap now clears `CaptureActive` and `RecorderState`, and a settled recover with no idle does the same. That fix is not in the running process.

V2. After Voice→Text→Voice, wake at 15:40:29 admitted a 31-character voice transcript at 15:40:38. Client turn timing: kind=voice, submit-to-complete 18316 ms. Gateway turn finished 15:40:57, status on the session started at the 15:15 restart. No `prompt.submit` between the 15:15:10 kill and that turn. No `auto_continue` or `origin_unknown` line in that interval.

V3. Typed turn 2 finished 15:42:51 on the same restarted session. Client timing at 15:43:06: kind=typed, submit-to-complete 25165 ms, tools=2, approval=0. Gateway status=complete, error_retained=False, duration=25.2s.

V4. After the 15:15:10 kill, Hermes did not run an auto-continue turn. No "Resuming interrupted" line, no `auto_continue` line, and no `origin_unknown` line in agent, gui, workspace, or errors logs through the V3 turn. The pre-kill capture was cancelled and was not submitted. `desktop.auto_continue.enabled` is false.

Brian's reply, verbatim: smoke test passed.

Armed check after that reply, read-only: `state_meta` heartbeat 0, loop 0, goal 0. `cron/jobs.json` absent.

Review fixes after that smoke, still in Phase 6. Same-generation reconnect sends `voice.record` stop before wake is re-armed. The tick clears the recording latch only when the capture is settled, not outstanding, and not `HermesBusyUntilIdle`. `session not found` falls back to a new session; any other resume error stays a failed reconnect. Client build 0 warnings. Checks supervision 26/26, full coverage line all passed. Plugins: workspace 177, memory 117, tools 44. Redeploy for V1b follows.

V1b, 15:58:49 kill of CPython 16796 during a wake capture. Restart `restarts=1 generation=1`, replacement child 34148. Capture cancelled `backend-unreachable`. Latch cleared (`capture=false`); mic returned to listening for Hey Zola at 15:58:59 without a mode toggle. Wake at 15:59:29 admitted a 31-character transcript at 15:59:36. Turn 1 finished 15:59:52, `status=complete`, `submit_to_first_audio_ms` empty. A second voice turn finished 16:00:18, also with empty `submit_to_first_audio_ms`. The earlier spoken voice turn on the previous process (15:41:01) had `submit_to_first_audio_ms=22461`.

TTS finding: silence is a bug, not the approved restore. Before the kill, the fresh serve had `HERMES_VOICE_TTS` unset, so the normal sync sends `voice.toggle tts` and `_ttsOn` becomes true. The gap snapshots that as `TtsBeforeGap`. On the new process, `RestoreSpeechBeforeResumeAsync` runs before session resume and toggles TTS while voice mode is still off. Hermes rejects that toggle (`enable voice mode first`) and does not set `HERMES_VOICE_TTS`. `SyncVoiceModePreservingTtsAsync` then turns voice on and, by verdict 6, does not force TTS. The new process stays silent. No code change and no redeploy in this step.

TTS restore fix, redeployed 2026-10-10 16:43. Speech was on before the 15:58:49 kill. Restore ran before voice mode was on. Hermes refused the switch. The later voice-on did not force TTS. Both post-restart turns had no audio. The 15:41 turn did. The fix turns voice on first, then sets TTS to the saved target. Off stays off. A null snapshot does not force TTS off. A new process skips the leftover-audio stop. A same-process reconnect stops leftover audio only after voice is on. A mismatch logs `event=tts_restore_mismatch` and retries once. Client build 0 warnings, 0 errors. Checks supervision 31/31. Plugins: workspace 177, memory 117, tools 44. WM_CLOSE of client 9192; shim 34452 and child 34148 exited. New window: client 6512, parent 28584, start 16:43:38; shim 19524, parent 6512; CPython 23532, parent 19524; both started 16:43:39. One dedicated Zola serve. V1b, S1, N1, and N2 are pending. Phase 6 is not complete.

V1b retry, 2026-10-12 11:09:23 kill of CPython 23532 during a wake capture. Same client 6512, no app restart. Supervisor `event=restart restarts=1 generation=1` at 11:09:25. Replacement shim 22356, CPython 16344, both started 11:09:27. Wake at 11:10:00 admitted a 35-character transcript at 11:10:09. Turn finished 11:10:53. Client timing at 11:11:08: kind=voice, tools=3, `submit_to_first_audio_ms` empty. Hermes started Edge TTS three times from 11:10:51 to 11:10:54. Each attempt failed with HTTP 403 and no audio file was saved. The last saved Edge audio in this log is 2026-10-10 15:40:59. Silence is the speech provider refusing the request, not a missed TTS restore and not a stale client.

Brian's verdict on that V1b, verbatim: "She did respond after restart and wrote the calendar events, but couldn't speak them. I think this one is good." The timeline between `wake.start` at 11:09:44 and `wake.detected` at 11:10:00 has no mode change. The 35-character transcript was admitted and the turn finished `status=complete` with tools=3 on the replacement serve. Supervisor logged no `event=tts_restore_mismatch`. The voice timeline has no `voice.toggle status` line for this restore. The restarted serve still called Edge TTS at 11:10:51, which is the spoken-reply path, and Edge returned 403. The latch fix held: no mode toggle was required. S1 and N2 stay on hold until speech works.

N1, no kills, same client 30100. First wake 11:43:28 admitted a 41-character transcript at 11:43:35. Second wake 11:44:32 admitted a 27-character transcript at 11:44:38. No `wake ignored` line in that window. Each capture left recording when the transcript settled. Both replies had empty `submit_to_first_audio_ms`. Edge TTS was requested and returned 403. After each silent reply, speaking cleared, wake was armed again, and a follow-up listen opened and then idled (`follow-up-idle` at 11:44:17 and 11:45:56) with `wake.resume`. The mic was not stuck on Listening. Brian's verdict, verbatim: N1 passed.

Deepgram TTS is a separate maintenance step, not part of the P9-SUPERVISE commit. The script is `C:\Users\test\Dev\zola-spikes\p9-fix-tts\deepgram_tts.py`. The key file is `C:\Users\test\AppData\Local\ZolaClient\secrets\deepgram_api_key` (Notepad had saved `deepgram_api_key.txt`; renamed to the approved path). It is not in the profile `.env` and not in `env_passthrough`. Residual: the agent's terminal runs as the same user and can still read that file. A guard row is deferred to P9-FIX-TTS. Standalone test exit 0, mp3 8064 bytes. Backup `C:\Users\test\Dev\zola-spikes\p9-fix-tts\config.yaml.bak-before-deepgram`, 4307 bytes. At pin `345cd2b`, `type`, `command`, and `output_format` are the keys the command provider reads (`tts_command_provider.py` 234–236, 261, 314). Unquoted placeholders go through `list2cmdline`, which leaves a space-free path unquoted, so the applied command quotes `{input_path}` and `{output_path}`. `{speed}` is not passed. Applied 2026-10-12 12:57. WM_CLOSE of client 30100. New window: client 38900, parent 32252, start 12:57:28; shim 6336, parent 38900; CPython 5328, parent 6336; both started 12:57:29. One dedicated Zola serve. Spoken reply 2026-10-12 13:41. Turn finished `status=complete`. Hermes logged `Generating speech with command TTS provider 'deepgram'` and saved an mp3 of 26928 bytes. Client timing `submit_to_first_audio_ms=15941`. Brian heard the new voice.

S1, 2026-10-12 13:44:12 kill of CPython 4168 during a wake capture. Same client 21592. Supervisor `event=restart restarts=1 generation=1` at 13:44:14. Replacement shim 36664, CPython 400. Capture cancelled `backend-unreachable`. `wake.start` at 13:44:21, `wake.detected` at 13:44:42, no mode change between them. A 5-character transcript was admitted at 13:44:47. Turn finished 13:44:51, `status=complete`. Deepgram saved an mp3 of 6336 bytes. Client timing `submit_to_first_audio_ms=4628`. Playback monitor cleared speaking at 13:44:54.

N2 was replaced. Barge-in stays off (P4). The wake word is ignored while she speaks. The replacement checks are N2a (wake mid-reply is ignored, she keeps speaking), N2b (after she finishes, follow-up opens or wake works again), and N2c (Stop speaking kills the Deepgram ffplay, Speaking clears, wake re-arms).

N2a accepted. Brian, verbatim: the wake word during speech did nothing, she kept talking, nothing got stuck. The detector did not register a phrase over playback, so no wake event reached the client. The user-visible result matches the design (no barge-in, P4/S36). No retry. Playback bout 13:48:39.751 to 13:48:59.880, ffplay pid 31352, ended on its own. No `wake ignored` line and no capture during that bout.

N2b met. `follow_up_release rule=monitor` bout_stop 13:49:00.382, capture gen=7 FollowUp listening 13:49:01, idle 13:49:17, `wake.resume reason=follow-up-end`, paused=false. Playback monitor stop 13:49:00.385, `speakingPlaybackArmed cancelled reason=mode`.

N2c, 2026-10-12 14:08:08. `stop_speaking requested` while `speech=true`. Playback had started at 14:07:59.100 (Deepgram mp3 126576 bytes). Hermes logged `Audio playback interrupted` at 14:08:08.020, then `No audio player available` for that same file. Owned ffplay pid 31840 left with `inactiveLeadMs=none` at 14:08:08.077 (no Inactive lead). `speakingPlaybackArmed cancelled reason=mode` at 14:08:08.019. Reconcile at 14:08:08.018 has `speaking=false`. Follow-up cancelled `fireOrCancel=stop-speaking`. `wake.resume reason=speaking-end`, then `stop_speaking step=wake_rearm` and `wake.start` `ok=True started=True` at 14:08:08.109. `stop_speaking done` at 14:08:08.110. TTS restored `tts=True`.

Brian's reply, verbatim: smoke test passed.

Registry read back again 2026-10-12 11:32 local. `HKLM\...\LocalDumps\python.exe` is unchanged: `DumpFolder` `REG_EXPAND_SZ` `C:\Users\test\AppData\Local\ZolaClient\dumps`, `DumpCount` `REG_DWORD` `0x3`, `DumpType` `REG_DWORD` `0x1`. HKCU key still absent. Verdict 8 scratch crash run again from `C:\Users\test\Dev\zola-spikes\p9-supervise`, not the live serve. Exit `-1073741819`. Dump `python.exe.7940.dmp`, 1994224 bytes, written 2026-10-12 11:33:23. Deleted. The dumps folder was empty afterward. Dump contents were not read. Live window at that time stayed up: client 30100 (started 11:17:31), shim 36744, CPython 31116.

TTS provider choice is a separate maintenance step, not a P9-SUPERVISE code change. `edge-tts` was not upgraded. Brian later chose the Deepgram command provider. That switch is recorded in the closeout section and is not part of the implementation commit.

## Closeout record

Stopped 2026-10-12 before the implementation commit, for review. Nothing in this section has been committed.

Phase 6 fixes made after the first smoke, then re-verified live on V1b, S1, N1, and N2a–c:

- `session not found` falls back to `session.create`. Any other resume error still counts as a failed reconnect.
- The recording latch clears on a settled outage with no idle, and a same-generation reconnect sends `voice.record` stop before wake is re-armed.
- TTS restore runs only after voice mode is on, then reads `voice.toggle` status and retries a mismatch once. A new process does not stop leftover audio. A null snapshot does not force TTS off.

N2 corrected scope. Voice barge-in stays disabled by design (P4 / S36). The wake word is ignored while she speaks. N2a: Brian, verbatim, the wake word during speech did nothing, she kept talking, nothing got stuck. The detector did not register a phrase over playback, so no wake event reached the client. N2b: the follow-up listen opened after she finished. N2c: Stop speaking cut the Deepgram ffplay, Speaking cleared, and wake re-armed.

WER. HKLM `LocalDumps\python.exe` read back at this closeout: `DumpFolder` `REG_EXPAND_SZ` `C:\Users\test\AppData\Local\ZolaClient\dumps`, `DumpCount` `REG_DWORD` `0x3`, `DumpType` `REG_DWORD` `0x1`. HKCU key absent. Folder ACL is `NT AUTHORITY\SYSTEM:(OI)(CI)(F)` and `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only. The verdict-8 scratch crash wrote `python.exe.7940.dmp`, 1994224 bytes, 2026-10-12 11:33:23. Deleted. The dumps folder was empty at closeout. Dump contents were not read. No `*.dmp` in the repo.

TTS maintenance, separate from this commit. Edge TTS has returned HTTP 403 since 2026-10-10 (`rany2/edge-tts` #490). `edge-tts` was not upgraded. The live config uses the Deepgram command provider, Aura-2 Thalia, as a temporary voice. Backup: `C:\Users\test\Dev\zola-spikes\p9-fix-tts\config.yaml.bak-before-deepgram` (4307 bytes). The key file is `C:\Users\test\AppData\Local\ZolaClient\secrets\deepgram_api_key`. That folder's ACL is `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only. Residual: the agent's terminal runs as the same user and can still read that path. The guard row belongs to P9-FIX-TTS. `C:\Users\test\Dev\zola-spikes\p9-fix-tts\deepgram_tts.py` stays in that scratch folder. It is not committed and it was not deleted.

Scratch deleted at this closeout: `C:\Users\test\Dev\zola-spikes\p9-supervise\` only. `p9-fix-tts` is still there.

Closeout verification, 2026-10-12:

- Client build: 0 warnings, 0 errors.
- `Zola.Client.Checks`: supervision 31/31. Coverage line all passed.
- Plugins, sources unchanged: workspace 177, memory 117, tools 44.
- `hermes-agent` HEAD `345cd2b057a452236de401d3534b8502a7465e8d`, porcelain empty.
- Armed, read-only: `state_meta` heartbeat 0, loop 0, goal 0. `cron/jobs.json` absent.
- `serve-stderr.log` 1084 bytes, last write 2026-10-12 13:44:19. Directory ACL is `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only.
- No lore edit other than this progress doc. No plugin diff. No `hermes-agent` diff.

### File list for the implementation commit (not yet made)

New:

- `windows-client/Zola.Client.Checks/SupervisionChecks.cs`
- `windows-client/Zola.Client/HermesProcessManager.Supervision.cs`
- `windows-client/Zola.Client/MainWindow.Supervision.cs`
- `windows-client/Zola.Client/Supervision/DumpPruner.cs`
- `windows-client/Zola.Client/Supervision/OutageGap.cs`
- `windows-client/Zola.Client/Supervision/ProcessSupervisor.cs`
- `windows-client/Zola.Client/Supervision/RecordingLatch.cs`
- `windows-client/Zola.Client/Supervision/RestartPolicy.cs`
- `windows-client/Zola.Client/Supervision/ResumeReconnect.cs`
- `windows-client/Zola.Client/Supervision/ServeGenerations.cs`
- `windows-client/Zola.Client/Supervision/ServeStderrLog.cs`
- `windows-client/Zola.Client/Supervision/StderrAcl.cs`
- `windows-client/Zola.Client/Supervision/SupervisionConstants.cs`
- `windows-client/Zola.Client/Supervision/SupervisionLog.cs`
- `windows-client/Zola.Client/Supervision/TtsRestore.cs`
- `zola-architecture/lore/prompts/progress/P9-SUPERVISE_Progress.md`

Modified:

- `windows-client/Zola.Client.Checks/Program.cs`
- `windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj`
- `windows-client/Zola.Client/App.xaml.cs`
- `windows-client/Zola.Client/ChatSocket.cs`
- `windows-client/Zola.Client/HermesProcessManager.cs`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `windows-client/Zola.Client/Presence/PresenceAnimator.cs`
- `windows-client/Zola.Client/Presence/PresenceView.cs`
- `windows-client/Zola.Client/Presence/TtsPlaybackMonitor.cs`
- `windows-client/Zola.Client/VoiceController.cs`
- `windows-client/Zola.Client/ZolaDisplayState.cs`

Not in that commit: the Deepgram script, its config backup, the live `config.yaml`, the secrets file, and WER dumps.

### Exit table

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | SV-G1–G7 answered; STOP verdicts recorded verbatim | ✅ MET | Grounding sections above. Phase 3 verdicts 1–10 recorded verbatim. |
| 2 | Client builds; plugin suites unchanged and passing | ✅ MET | Build 0/0. Checks supervision 31/31. Workspace 177, memory 117, tools 44. No plugin diff. |
| 3 | Idle kill restarts once (R1); 4 kills in 10 minutes is terminal (R2) | ✅ MET | R1 `event=restart restarts=1`. R2 restarts 2 and 3, then `event=keeps_failing restarts=4` and no serve left. |
| 4 | Kill mid-capture drops the capture; voice and typed turns work after (V1–V3) | ✅ MET | V1 capture cancelled `backend-unreachable`, no submit of that turn. V2 voice answered. V3 typed answered. Latch and TTS-order fixes re-checked on V1b, S1, N1, N2a–c. |
| 5 | WER by registry and ACL; stderr exists and rotates | ✅ MET | HKLM keys and ACL read back. `python.exe.7940.dmp` (1994224 bytes) deleted. Stderr file 1084 bytes, Brian-only ACL. Rotation is the named-cap check, not a live fill. |
| 6 | Crash replay has no Brian authority | ✅ MET | Verdict 5 set `desktop.auto_continue.enabled: false`. V4: no auto-continue turn and no `origin_unknown` line, because no replay ran. |
| 7 | Deliberate exits never restart | ✅ MET | R4: WM_CLOSE while listening. Serve gone. No restart line and no failing state. |
| 8 | Stale generation changes nothing | ✅ MET | Checks: stale process generation is not current; an earlier connection epoch is refused. |
| 9 | Alive-but-unreachable fails closed | ✅ MET | Checks: first health failures stay fail-closed; the third tree-kills; socket loss does not count until the kill. R6 was not forced live. |
| 10 | No hermes-agent, plugin, or lore change; no dump in the repo; nothing armed | ✅ MET | Hermes porcelain empty at `345cd2b`. No plugin diff. Lore untouched except this progress doc. No `*.dmp` in the repo. Heartbeat 0, loop 0, goal 0. `cron/jobs.json` absent. |

Approved live-config edits sit outside the commit: `desktop.auto_continue.enabled: false`, and the temporary Deepgram TTS block. N2's scope is the P4 / S36 rule: barge-in stays off, the wake word is ignored during speech, and Stop speaking is what cuts audio (N2c).

All criteria met: YES

Stopped before the first commit. No implementation SHA. No merge SHA.

## Discrepancies

- Phase 1 porcelain was exactly the untracked build plan. The conversation-start status snapshot also listed plugin sources, client build outputs, and other progress files; those were not present in `git status --porcelain` at execution time.
- A `git fetch` was issued once with the shell still in `C:\Users\test\Dev\hermes-agent` (cwd carried over). It updated that repo's remote-tracking refs only. HEAD stayed `345cd2b057a452236de401d3534b8502a7465e8d` and porcelain stayed empty. No Hermes file was edited. The required fetch was then run in `zola-windows`.

## Phase 1 baseline (2026-10-09, local evening)

### Processes

Zola client and its serve are running. Other `python.exe` processes are Blender MCP helpers, not serve.

| Role | PID | Parent PID | Start (local) | Command (truncated) |
|---|---:|---:|---|---|
| Zola client | 28104 | 17988 | 2026-10-09 14:45:08 | `windows-client\Zola.Client\bin\Debug\net9.0-windows10.0.19041.0\Zola.Client.exe` |
| serve launcher | 33972 | 28104 | 2026-10-09 14:45:11 | `hermes-agent\.venv\Scripts\python.exe -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0` |
| serve child | 5996 | 33972 | 2026-10-09 14:45:11 | same `-m hermes_cli.main -p zola serve` via `cpython-3.12` |

### Client log folder

`C:\Users\test\AppData\Local\ZolaClient\logs` (`%LOCALAPPDATA%\ZolaClient\logs`). Names and sizes only.

| Name | Bytes | Last write (UTC) |
|---|---:|---|
| `aud37-verify-offset.txt` | 8 | 2026-10-01 00:05:45 |
| `display-state.log` | 1,151,371 | 2026-10-09 21:50:42 |
| `p4feedback-smoke-offset.txt` | 8 | 2026-10-01 00:26:08 |
| `presence.log` | 69,450,360 | 2026-10-10 01:12:53 |
| `presence.log.bak-d2` | 118,335 | 2026-09-28 17:19:21 |
| `presence.log.bak-d2b` | 1,324 | 2026-09-28 17:41:02 |
| `presence.log.bak-ref` | 1,324 | 2026-09-28 17:41:34 |
| `server-requests.log` | 38,172 | 2026-10-09 21:50:23 |
| `tool-events.log` | 78 | 2026-10-01 00:28:16 |
| `voice-timeline.log` | 1,339,434 | 2026-10-09 21:50:57 |

### WER LocalDumps (read-only)

- `HKCU\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps`: absent. `python.exe` under HKCU: absent.
- `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps`: present. No DumpFolder, DumpCount, or DumpType values on the key itself.
- `python.exe` under HKLM: absent.
- Existing per-executable subkeys (not `python.exe`):

| Subkey | DumpFolder | DumpCount | DumpType |
|---|---|---:|---:|
| `EADesktop.exe` | `C:\Users\test\AppData\Local\CrashDumps` | 10 | 1 |
| `EALauncher.exe` | `C:\Users\test\AppData\Local\CrashDumps` | 10 | 1 |
| `ErrorReporter.exe` | `C:\Users\test\AppData\Local\CrashDumps` | 10 | 1 |
