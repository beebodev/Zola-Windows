# P7-FORENSIC-SERVE — Findings (read-only)

**Date:** 2026-10-06  
**Scope:** Two hermes-serve losses during P7-VOICEAUTH smoke. No code/config changes; no repro hammering.  
**Hermes pin:** `345cd2b057a452236de401d3534b8502a7465e8d`  
**Client:** Track 1 binary (Phase 6 deploy EXE 08:38:48) for both losses.

---

## Verdict summary

| Loss | Cause | Track-1-related | Confidence |
|---|---|---|---|
| **(a)** ~08:48:12 | Native **APPCRASH** (`0xc0000005`) in uv `python.exe` / `python312.dll` (serve child PID **3992**). WS 1006 flaps earlier were session reconnects, not the death. Client restarted **after** the crash. | **No** (pre-existing native crash class; no Track-1 stop/cancel in the window) | **High** |
| **(b)** ~10:52:31 | Native **APPCRASH** (`0xc0000005`) in uv `python.exe` / `ntdll.dll` (serve child PID **18340**, started 08:48:49 under client 9228), during silence auto-stop → client `voice.record stop` (force-transcribe) → immediate `_resume_voice_wake` while silence-path STT still in flight. No Python traceback; process gone mid-Mars turn. | **Indirect / unknown as sole cause** — Track 1 increased how often Accepting + typed-submit sends stop; the crash is in Hermes/native audio stack, not client Kill | **Medium-High** (timeline + code race proven; exact native frame unknown without dump analysis) |

**Controlled repro of (b):** not run. Evidence from steps 1–3 is sufficient to file an upstream race note; hammering stop/start deferred pending approval.

---

## Loss (a) — 08:47:30–08:48:35 → client 9228

### How serve ended

Windows Application log:

```
2026-10-06 08:48:12  Application Error Id=1000
  Faulting application: ...\uv\python\cpython-3.12-windows-x86_64-none\python.exe
  Faulting module: python312.dll
  Exception code: 0xc0000005
  Faulting process id: 0xF98 (= 3992)
  Process start time (FILETIME → local): 2026-10-06 08:39:00
```

WER follow-up Id=1001 @ 08:48:18 (bucket `1390635367873966451`).

**PID 3992** matches Phase 6 deploy record: uv cpython child of serve parent 19676, started **08:39:00** (`P7-VOICEAUTH_Progress.md` Deploy record).

No Python `Traceback` / `ERROR` in `agent.log` or `errors.log` at the crash. Last agent line before death:

```
2026-10-06 08:48:06,101 INFO run_agent: OpenAI client closed (agent_close, ...)
```

Next agent lines are a **fresh serve bootstrap** (plugin registration) @ **08:48:50**.

Stderr/stdout from `HermesProcessManager` are redirected in-memory only for the ready sentinel (`HermesProcessManager.cs` ~L218–279); **not persisted** to disk. No OOM event found.

### Who started the shutdown

| Actor | Evidence |
|---|---|
| **Serve exited on its own** | APPCRASH at 08:48:12 while client **19612** still alive |
| Client Kill | Only on window close: `App.xaml.cs` L22 `_window.Closed → _backend.Shutdown()` → `HermesProcessManager.Shutdown` `child.Kill(entireProcessTree: true)` (`HermesProcessManager.cs` L119–125). That path runs when Brian closed 19612 to open 9228 **after** the crash |
| WS 1006 @ 08:47:30 / 08:47:46 / 08:47:52 | `reason=client_disconnect(code=1006)` with immediate `ws accepted` — **session flaps**, serve stayed up (wake.start after each) |

Client timeline after crash:

```
2026-10-06T08:48:18.737  wake reconcile unreachable Backend unreachable
2026-10-06T08:48:35.299  wake reconcile unreachable Backend unreachable
2026-10-06T08:48:48.884  display … link="OFFLINE"   ← new client 9228
2026-10-06T08:48:52.323  link CONNECTED
2026-10-06T08:48:54.184  wake.start ok
```

### Track 1 relation

None in the crash window: no `voice.record`, no Track-1 cancel. Wake was listening after the 08:47:52 session flap. Same `0xc0000005` / `python312.dll` class appears **three times on 2026-10-05** (before Track 1 deploy).

---

## Loss (b) — S1b attempt 1 ~10:52:30–10:52:37

### How serve ended

Windows Application log:

```
2026-10-06 10:52:31  Application Error Id=1000
  Faulting application: ...\uv\python\cpython-3.12-windows-x86_64-none\python.exe
  Faulting module: ntdll.dll
  Exception code: 0xc0000005
  Faulting process id: 0x47A4 (= 18340)
  Process start time (FILETIME → local): 2026-10-06 08:48:49
```

WER Id=1001 @ 10:52:38. Loaded modules in `Report.wer` include `MMDevAPI.DLL`, `AUDIOSES.DLL`, `wdmaud.drv`, `WINMM.dll` (audio stack present). No dump symbolization performed this track.

**PID 18340** start **08:48:49** = uv child of mid-smoke client **9228** (client start 08:48:48; plugin bootstrap 08:48:50).

Agent log (no `Transcribed` for the follow-up WAV; no traceback; abrupt gap → relaunch):

```
2026-10-06 10:52:24,483 INFO tools.voice_mode: Voice recording started ...
2026-10-06 10:52:30,281 INFO tools.voice_mode: Silence detected (1.5s), auto-stopping
2026-10-06 10:52:30,284 INFO tools.voice_mode: Voice recording stopped (5.8s, ...)
2026-10-06 10:52:30,291 INFO tools.voice_mode: WAV written: ...\recording_20261006_105230.wav
2026-10-06 10:52:30,845 INFO tools.wake_word: wake word: opening microphone device=...
2026-10-06 10:52:30,864 INFO tui_gateway.server: tui prompt accepted: ... kind=user chars=19
2026-10-06 10:52:31,268 INFO ... agent.turn_context: ... msg='And one about Mars.'
2026-10-06 10:54:31,296 INFO hermes_cli.plugins: Plugin 'browser-browser-use' registered ...
```

Client voice-timeline / display:

```
2026-10-06T10:52:30.841  Accepting→Cancelled typed-submit; capture stop_sent
2026-10-06T10:52:30.867  capture cancel turn-start; capture stop_sent  (second stop RPC)
2026-10-06T10:52:30.284  display Transcribing   ← silence path
2026-10-06T10:52:30.847  display Thinking       ← typed Mars
2026-10-06T10:52:37.047  fact unreachable=true; link OFFLINE
```

### Who started the shutdown

| Actor | Evidence |
|---|---|
| **Serve crashed (native)** | APPCRASH 10:52:31; client 9228 remained until later forensic relaunch @ 10:54 |
| Client Kill | Not in this window — Kill only on `Closed` (`App.xaml.cs` L22). Relaunch at 10:54 was the approved S1b recovery (`Stop-Process` then `dotnet run`), **after** the crash |
| Client stop RPC | Did send `voice.record stop` (Track-1 cancel path) — that is the **trigger context**, not `Process.Kill` |

### Hermes race at `345cd2b0` (stop while silence auto-stopping / transcribing)

**Gateway stop** (`tui_gateway/methods_voice.py`):

```721:725:tui_gateway/methods_voice.py
        if action == "stop":
            from hermes_cli.voice import stop_continuous
            stop_continuous(force_transcribe=True)
            _resume_voice_wake()
            return _ok(rid, {"status": "stopped"})
```

**Silence path** (`hermes_cli/voice.py` `_continuous_on_silence` ~L466–515): under lock confirms active → **releases lock** → `on_status("transcribing")` → `rec.stop()` → `_turn_transcript(...)` (Whisper) → later `_deactivate` / idle. `_continuous_active` stays **True** until halt/deactivate **after** STT.

**Forced stop** (`stop_continuous` ~L388–427): under lock sets `_continuous_active = False`, then outside lock may call `rec.stop()` again and start `_finish_forced_stop` on a daemon thread; returns while STT may still run on the silence thread.

**AudioRecorder.stop** (`tools/voice_mode.py` L799–820): second `stop()` is Python-safe (`if not self._recording: return None`). The dangerous overlap is:

1. Silence thread has finished `rec.stop()` / WAV write and is inside `_turn_transcript` (or about to), **or** still sharing the live PortAudio InputStream lifecycle.
2. Client `voice.record stop` runs `stop_continuous(force_transcribe=True)` then **immediately** `_resume_voice_wake()` → wake opens a **second** mic device (`wake word: opening microphone` @ 10:52:30.845) while STT/audio still in flight.
3. Native AV in `ntdll.dll` @ 10:52:31; no `Transcribed` line for `recording_20261006_105230.wav`.

Client also issued a **second** `stop_sent` on `turn-start` (~26 ms later). After the first stop clears `_continuous_active`, the second `stop_continuous` is a no-op (`voice.py` L399–400).

**Can it raise / hang / kill?** Python exceptions in the silence callback are logged (`voice_mode.py` `_safe_cb`); they do not explain APPCRASH. A native fault in PortAudio / Whisper / runtime **can kill the process** without a traceback — matching (b).

### Contrast: S1b attempt 2 (survived)

```
10:57:43,360 Voice recording started
10:57:49,306 Voice recording stopped   ← no "Silence detected" line
10:57:49,312 WAV written
10:57:49,317 wake word: opening microphone
10:57:49,570 faster_whisper: Processing audio ...
10:57:50,574 Transcribed recording_20261006_105749.wav ...
```

Client stop won the recorder **before** silence auto-stop; force-transcribe owned the WAV; wake resumed; STT completed. Same stop→wake pattern, different interleaving — consistent with a race, not a deterministic Track-1 logic bug.

---

## Earlier history (pre–Phase 7)

**Windows Application Error Id=1000, `python.exe`, since 2026-09-01: 5 total**

| Time (local) | Module | Notes |
|---|---|---|
| 2026-10-05 11:13:49 | python312.dll | Pre–Track-1; agent continues with session flap then later plugin rediscovery @ 11:14:35 |
| 2026-10-05 12:06:34 | python312.dll | Pre–Track-1; plugin rediscovery @ 12:07:11 |
| 2026-10-05 19:28:51 | python312.dll | Pre–Track-1 / evening baseline era; plugin rediscovery @ 19:29:47 |
| 2026-10-06 08:48:12 | python312.dll | Loss **(a)** |
| 2026-10-06 10:52:31 | ntdll.dll | Loss **(b)** |

**Serve disappearances (APPCRASH → dead child): 3 before Phase 7 deploy on 2026-10-05, plus (a) and (b).**  
`Plugin discovery complete` markers are far more numerous (ordinary client relaunches / attaches) and are **not** used as crash counts.

No matching Python traceback series for these five APPCRASHes in `errors.log`.

---

## S1–S8 and S1b attempt 2 after 10:54

| Check | Result |
|---|---|
| S1–S8 (session `b2d93629` / `20261006_084852_f8a7fa` on PID 9228) | Ran **after** loss (a) recovery; **no** APPCRASH / serve death through S8 |
| S1b attempt 1 | Loss **(b)** |
| S1b attempt 2 (session `4bea92b2` / `20261006_105433_533d74`, client 18452) | **PASS**; serve stayed up |
| `agent.log` / `errors.log` after 10:54 | **No** `Traceback` / `ERROR` / `CRITICAL` lines in the 10:54–11:x window (WARN-only: registry checks, mic-silence) |

---

## Client kill / restart paths (reference)

| Path | File:line | When |
|---|---|---|
| Window close → Shutdown → Kill tree | `App.xaml.cs` L22; `HermesProcessManager.cs` L99–125, L476–483 | Only if this window **OwnsProcess** |
| Spawn failure / timeout Shutdown | `HermesProcessManager.cs` L282–298 | Start path only |
| Attach existing serve | `HermesProcessManager.cs` L149–157 | **Never** kills on close |

No Track-1 code adds process kill/restart. Timeline `capture stop_sent` is RPC only (`VoiceController.SendRecordStopAsync` ~L2364).

---

## Recommendation

| Item | Action |
|---|---|
| Loss (a) | **Upstream note** — intermittent native crash of uv CPython serve child (`python312.dll` AV), seen on 2026-10-05 before Track 1; capture WER dumps / enable Hermes stderr file logging on spawn |
| Loss (b) | **Upstream note** — race: `voice.record stop` → `stop_continuous(force_transcribe=True)` then `_resume_voice_wake()` while `_continuous_on_silence` may still be in `rec.stop` / `_turn_transcript`; serialize wake resume until silence/forced-stop pipeline reaches idle; optionally defer wake resume until STT thread joins |
| Track 1 / Track 2 client | **None required for correctness of admission** (S1b-2 proved cancel-drop). Optional later **client guard**: coalesce double stop (typed-submit + turn-start); do not treat as Track-2 scope unless clarifying also hits the same stop/wake race |
| Repro | **Not run.** One controlled (b) repro only after explicit approval |

---

## Artifacts consulted

- `%LOCALAPPDATA%\hermes\profiles\zola\logs\agent.log`, `errors.log`, `gui.log`
- `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log`, `display-state.log`
- Windows Event Viewer → Application (Id 1000/1001)
- WER `ReportArchive\AppCrash_python.exe_*` for (a) and (b)
- `hermes-agent` @ `345cd2b0`: `hermes_cli/voice.py`, `tui_gateway/methods_voice.py`, `tools/voice_mode.py`
- `windows-client/Zola.Client/HermesProcessManager.cs`, `App.xaml.cs`, `VoiceController.cs`
