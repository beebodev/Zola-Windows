# P3-STATE Progress — Display-State Authority + Carry-over

## Branch

- Branch: `p3-state-display-authority`
- Base SHA: `5994e8bc4e1167c59304ec4b2317f8c9ed9ac94f` (plan commit; branch point)
- Plan commit SHA: `5994e8bc4e1167c59304ec4b2317f8c9ed9ac94f`
- Recorded HEAD before the plan commit: `4d5a60d23dcc6a2157a01a6b1064df1271f05ff5` (`audit: record P3PRE merge SHA`), a direct successor of the expected P3PRE merge `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`
- Plan source SHA-256: `9ccf90f786220f11c29c05b5dbfb70c65945bf43f4281e1954527b191eeeac29` (matched)
- Prompt: P3-STATE v1.1

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Plan Commit, Branch, and Progress Document | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: ZolaDisplayState model | COMPLETE |
| 4 | Build: Wire MainWindow + carry-over | COMPLETE |
| 5 | Smoke Test | COMPLETE |
| 6 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** This track changes only `ZolaDisplayState.cs` (new), `MainWindow.xaml.cs` (assign-only `ApplyVoiceChrome`, model construction, `NoteTurnActivity` lines, one `Dispose` on close), `VoiceController.cs` (P3-D15 carry-over; folder constants `internal` only if required), `VOICE_CONFIG.md` (three tuning-log rows), `PHASE3_BUILD_PLAN.md` (Phase 1, committed on `main`), and this progress document.
- **G-ARCH:** The build plan is truth. A conflict with the codebase that affects a task is a stop, not a silent deviation.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No XAML, no `ChatSocket.cs`, `SessionCatalog.cs`, `HermesProcessManager.cs`, `HermesLaunchResolver.cs`, `App.xaml(.cs)`, or `Zola.Client.csproj`, and no package changes.
- **G-COMMENT:** One `// P3-STATE: [one-line rationale] — P3-D0X` comment per logically distinct changed block.
- **G-STOP:** Stop after each phase and wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-LORE-SCOPE:** `ROADMAP.md`, `DESIGN_DECISIONS.md`, and `OPEN_QUESTIONS.md` are out of scope, including closeout. `VOICE_CONFIG.md` is not a lore file.
- **G-NO-CROSS-SCOPE:** Android Zola, Ava, and the P3PRE spike folder are out of scope.
- **G-ONE-AUTHORITY:** `ZolaDisplayStateModel` is the only code that decides the voice label, mic line, mode word, mic-button enablement/content, mode-button enablement, and `PresenceMode`. `VoiceController` keeps listeners, RPCs, transcript-to-submit, `Resting`, and `CanStartCapture`.
- **G-VERBATIM:** Label strings and priority branches are copied exactly from Audit 01 §3. `PresenceMode` uses the `P3-D04` v1.1 order, which differs from the voice-label order.
- **G-CONST:** Every string, threshold, interval, and log tag this track adds is a named constant. Label strings stay as `private const string` literals copied verbatim.

## Discrepancies

Discrepancies: none at start. Phase 2 found no conflict with the plan. `ApplyVoiceChrome` still matches Audit 01 §3 line for line. `Speaking` and `_streaming` overlap from `message.start` until `FinishTurn`.

Option B re-run of steps 5–7 (2026-09-24). Developer reported `smoke test passed` again: all expected behaviors were shown, and step 7 chrome (composer/mic/mode disabled, window stayed open) is confirmed.

- Step 5: Text-mode Cancel left `Thinking` in ~2 s (13:34:34 → 13:34:36).
- Step 6: New session logged only `switchInFlight` true/false. Resume logged `switchInFlight` and `historyPending` true/false. No `Thinking`/`Speaking` carried across. No `Reconnecting voice…` display-state line because the window was still in Text mode (`Mic: off` outranks reconnect).
- Step 7: serve tree 8296/16480 stopped. Parent of 8296 was leftover Phase 4 pid 18156, not client 16608 (this window attached). Client 16608 stayed up. Log: `fact unreachable=true` and `mode=Dormant`.

## Phase 2 understanding

### 1. Verbatim tables

`ApplyVoiceChrome` (`MainWindow.xaml.cs` 316–394) matches Audit 01 §3 line for line, including comments. No difference.

Voice-label priority (first match):

1. `!IsAvailable && Mode == text` → `"Voice unavailable"` or `"Voice unavailable — " + details`
2. `Mode == text` → `"Text mode"`
3. `_streaming` → `"Thinking"`
4. `Speaking` → `"Speaking"`
5. `RecorderState == StateTranscribing` → `"Transcribing"`
6. `CaptureActive || RecorderState == StateListening` → `"Listening"`
7. else → `"Idle"`

Mic-line priority (first match):

1. mode is not voice, or `!IsAvailable` → `"Mic: off"`
2. `CaptureActive` → `"Mic: recording"`
3. `_streaming || Speaking` → `"Mic: listening for interruptions"`
4. `_switchInFlight || _historyPending` → `"Reconnecting voice…"`
5. `WakeUnavailable || WakeHeldElsewhere` → `"Wake word unavailable"`
6. `Resting && WakeArmed && WakePaused` → `"Wake listening paused"`
7. `Resting && WakeArmed && !WakePaused` → `"Mic: listening for \"Hey Zola\""`
8. else → `"Mic: off"`

Buttons: `ModeButton.Content` is `"Voice"` or `"Text"` from `Mode`. `ModeButton.IsEnabled` is `!_unreachable && !_modeSwitching && SessionId` set. `MicButton.IsEnabled` is `CanStartCapture`. `MicButton.Content` is `"Listening"` if `CaptureActive`, else `"Mic"`.

### 2. Input facts

Window fields (`MainWindow.xaml.cs`):

- `_sessionReady`: true `OnSessionReady` 132; resume success 803. False: `ConnectAsync` catch 101; `ShowUnreachable` 585; `OnNewSessionClick` 740; `OnSessionItemClick` 785; new-session catch `stillLive` 754; resume catch `keepCurrent` 818.
- `_streaming`: true `SubmitTurnAsync` 167 (when not already streaming), `OnSubmitAcknowledged` 404, `OnMessageStarted` 478. False: failed submit 188, `FinishTurn` 529 and 551, `ShowUnreachable` 584, `ClearTranscript` 888.
- `_unreachable`: true only `ShowUnreachable` 583.
- `_switchInFlight`: true `OnNewSessionClick` 738, `OnSessionItemClick` 783. False: new-session `finally` 762, resume success 804, resume `finally` 826.
- `_historyPending`: true `OnSessionItemClick` 784. False: `OnNewSessionClick` 739, resume success 802, resume catch 817.
- `_modeSwitching`: true `OnModeClick` 267. False: `OnModeClick` `finally` 296.

`_backend.WebSocketPermitted` is a getter on `HermesProcessManager` (line 48): `HealthPassed && SessionToken set && Port > 0`. Nothing assigns it.

`_chat.SessionId` is written in `ChatSocket.cs`: cleared at 144, set from the greet at 205.

`VoiceController` properties:

- `Mode`: default `ModeVoice` 146. `EnterTextModeAsync` 314 `ModeText`. `EnterVoiceModeAsync` 327 `ModeVoice`. `MarkUnavailable` 1568 `ModeText`.
- `IsAvailable`: default false. Set 246 from the status probe. `MarkUnavailable` 1564 sets false.
- `UnavailableDetails`: default `""` 150. Set 247 and `MarkUnavailable` 1565.
- `Speaking`: only `SetSpeaking` 814. True from `OnTurnStarted` 385 when `ClockEligible`. False from `OnTurnStarted` 375 (not eligible), `OnTurnCompleted` 416 (not eligible), `OnFollowUpTimerAsync` 758, and `CancelFollowUp` 788.
- `RecorderState`: default `StateIdle` 154. `EnterTextModeAsync` 316 `StateIdle`. `StartCaptureAsync` 537 `StateListening` when idle. `OnVoiceStatus` 622 from `voice.status`.
- `CaptureActive`: default false. True `StartCaptureAsync` 532 and `OnVoiceStatus` 639 (listening or transcribing). False: `EnterTextModeAsync` 315, idle status 625, `MarkUnavailable` 1569.
- `WakeUnavailable`: cleared `ArmWakeAsync` 1124 and 1191, `BumpConnectionGeneration` 1274, `DisarmWakeAsync` 1542. Set true 1204 and from `wake.status` 1429.
- `WakeHeldElsewhere`: cleared 1123, 1190, 1274, 1541. Set true 1220 and from `wake.status` 1428.
- `Resting`: getter only, 180–194. Not stored.
- `WakeArmed` / `WakePaused`: confirmed replies in `ArmWakeAsync` 1188–1189, pause 1334, resume 1375, `wake.status` 1426–1427, `OnWakeDetected` 1451 (`WakePaused = true`), and the clear sites 1245–1246, 1258–1259, 1272–1273, 1539–1540.
- `CanStartCapture`: getter only, 197–203. Not stored. `SetCaptureGate` 214–225 is the only writer of `SessionReady`, `BackendReachable`, and `TurnRunning`, and it raises `StateChanged`.

### 3. Overlap

Confirmed. `OnMessageStarted` sets `_streaming = true` (478) and then calls `OnTurnStarted` (480). When `ClockEligible` (`Mode == voice && _ttsOn == true`, 469), `OnTurnStarted` calls `SetSpeaking(true)` (385). `_streaming` stays true until `FinishTurn`. `Speaking` stays true until the follow-up timer (758) or `CancelFollowUp` (788). The two are both true from `message.start` until `FinishTurn`. That matches `P3-D04` v1.1.

### 4. Recovery paths

- (a) `OnInterruptAcknowledged` 455 calls `FinishTurn("interrupted")`, which sets `_streaming = false` at 529.
- (b) `ClearTranscript` 888 sets `_streaming = false`. Callers: `OnNewSessionClick` 741 and resume success 796.
- (c) `CancelFollowUp` 788 calls `SetSpeaking(false)`. New session and resume reach it through `OnSessionReady` 111 → `VoiceController.OnSessionReady` 460 (`"session-ready"`).
- (d) `ShowUnreachable` 583 sets `_unreachable = true` and also clears `_streaming` at 584.

### 5. Call sites

`ApplyVoiceChrome` is called from `UpdateChrome` 686 and from the constructor subscription `_voice.StateChanged += () => Dispatch(ApplyVoiceChrome)` (44).

`UpdateChrome` is called from: `Composer.TextChanged` 57; `ConnectAsync` catch 103; `OnSessionReady` 128 and 135; `SubmitTurnAsync` 172 and its catch 193; `SyncVoiceAsync` catch 215; `ToggleVoiceCaptureAsync` catch 253; `OnModeClick` 268, 289, and `finally` 297; `OnVoiceChatEnded` 306; `OnVoiceStatusMessage` 313; `OnSubmitAcknowledged` 413; `OnCancelClick` catch 440; `OnInterruptAcknowledged` when not interrupted 450; `OnMessageStarted` 482; `FinishTurn` 541 and 559; `ShowUnreachable` 590; `OnNewSessionClick` 743 and `finally` 763; `OnSessionItemClick` 787, resume success 807, and `finally` 827.

`OnMessageDelta` and `OnRouted` do not call `UpdateChrome`.

Constructor `Dispatch` subscriptions: `StateChanged` 44, `TranscriptReady` 45, `VoiceChatEnded` 46, `StatusMessage` 47, `SessionReady` 48, `SubmitAcknowledged` 49, `MessageStarted` 50, `MessageDelta` 51, `MessageCompleted` 52, `InterruptAcknowledged` 53, `Routed` 54, `Unreachable` 55. `_backend.StateChanged` uses `DispatcherQueue.TryEnqueue(Render)` at 56 and does not call `ApplyVoiceChrome`.

### 6. Logging

`TimelineClientFolder = "ZolaClient"` and `TimelineLogFolder = "logs"` are `private const string` at `VoiceController.cs` 74–75. `TimelineLogFile = "voice-timeline.log"` is also `private const string` at 76. `WriteTimeline` 1100–1111 builds `%LOCALAPPDATA%\ZolaClient\logs` and swallows write failures. The two folder constants must become `internal` so `ZolaDisplayStateModel` can share that folder. The log file name stays private.

### 7. Carry-over

`EchoContainmentRatio` (49), `EchoMinWords` (51), and `EchoPhraseWords` (52) are declaration-only. A search of `windows-client` finds no other hits. Comments:

```
// P2-SPEAK: follow-up echo uses a tail bag-of-words check plus a short phrase run; 80% missed an STT split of unless — P2-D12
// P2-WAKE: drop a follow-up only when a ≥3-word in-order run is ≥0.60 of it and ends near her last spoken words — P2-D12
```

Those are lines 48 and 55. The live rule they describe is `P2-D14`.

### 8. Flags

None. No source files were modified.

## Phase 3 build

`ZolaDisplayState.cs` is not referenced by `MainWindow`. The constructor is `internal` because `VoiceController` is internal (`CS0051` if the constructor is public). It sets `Current` to the P2 XAML defaults (`Idle`, `Mic: off`, `Voice`, both buttons disabled, `Mic`, `Dormant`), does not call `SetCaptureGate`, and does not recompute. The first `UpdateWindowFacts` always writes `display-state.log`. Later `Changed` events fire only when the record differs. The model subscribes to no `VoiceController` or socket events. One `DispatcherQueueTimer` is created in the constructor; elapsed time uses `Environment.TickCount64`; the S26 warning is once per streaming generation; `Dispose` stops the timer. `TimelineClientFolder` and `TimelineLogFolder` are `internal`.

`dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`: 0 warnings, 0 errors.

Voice label (Audit 01 §3 order): unavailable text → `Text mode` → `Thinking` (`streaming`) → `Speaking` → `Transcribing` → `Listening` → `Idle`.

Mic line (Audit 01 §3 order): not voice or unavailable → `Mic: off`; `CaptureActive` → `Mic: recording`; streaming or `Speaking` → `Mic: listening for interruptions`; `switchInFlight` or `historyPending` → `Reconnecting voice…`; wake unavailable or held → `Wake word unavailable`; resting, armed, paused → `Wake listening paused`; resting, armed, not paused → `Mic: listening for "Hey Zola"`; else → `Mic: off`.

`PresenceMode` (`P3-D04` v1.1): unreachable or not backend-reachable → `Dormant`; switch or history → `Idle`; `Speaking` → `Speaking`; streaming → `Thinking`; transcribing → `Listening`; capture or listening → `Listening`; text mode or unavailable → `Idle`; else → `Idle`. `Alert` is never produced.

## Phase 4 build

`ApplyVoiceChrome` is assign-only:

```csharp
_display.UpdateWindowFacts(
    _sessionReady,
    _backend.WebSocketPermitted && !_unreachable,
    _streaming,
    _switchInFlight,
    _historyPending,
    _modeSwitching,
    _unreachable,
    !string.IsNullOrEmpty(_chat.SessionId));
var s = _display.Current;
VoiceStateText.Text = s.VoiceLabel;
MicIndicatorText.Text = s.MicLine;
ModeButton.Content = s.ModeWord;
ModeButton.IsEnabled = s.ModeButtonEnabled;
MicButton.IsEnabled = s.MicButtonEnabled;
MicButton.Content = s.MicButtonContent;
```

The window no longer calls `SetCaptureGate`. The only call site is `ZolaDisplayStateModel.UpdateWindowFacts`. `EchoContainmentRatio`, `EchoMinWords`, and `EchoPhraseWords` are gone from `windows-client`. The two echo comments now cite `P2-D14`. The three `VOICE_CONFIG.md` result cells are `Removed (P3-STATE)`; `git diff` shows no other change in that file.

`dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`: 0 warnings, 0 errors.

Launch pid `18156`. First `display-state.log` line, from the first `UpdateWindowFacts`:

`2026-09-24T13:12:22.1587448-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle`

The process was stopped after that line so the smoke launch can start clean.

## Phase 5 smoke test

HUMAN-RUN. Machine setup per `P2-D16`: lid open, mic input 100, enhancements on, speakers about 15.

Launched from a fresh shell: `windows-client\Zola.Client\bin\Debug\net9.0-windows10.0.19041.0\win-x64\Zola.Client.exe`. Process id `18344`. `display-state.log` is being written at `%LOCALAPPDATA%\ZolaClient\logs\display-state.log`.

Developer reported `smoke test passed` (2026-09-24). No `thinking with no events` line appears. The on-screen label criterion is accepted on that report. The log does **not** fully match steps 5–7 as written; see Discrepancies.

### 1. Cold launch (pid 18344)

```
2026-09-24T13:17:12.8497067-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle
2026-09-24T13:17:12.8594507-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle
2026-09-24T13:17:14.4993522-07:00 P3-STATE: display state voice="Idle" mic="Mic: listening for "Hey Zola"" mode=Idle
```

Log mode `Idle`. Mic line `Mic: listening for "Hey Zola"`.

### 2. Voice turn

Labels walk Listening → Transcribing → Thinking → Speaking → Idle. Log modes walk Listening → Thinking → **Speaking** (label still `Thinking`) → Idle.

```
2026-09-24T13:18:16.7702264-07:00 P3-STATE: display state voice="Listening" mic="Mic: recording" mode=Listening
2026-09-24T13:18:19.9278155-07:00 P3-STATE: display state voice="Transcribing" mic="Mic: recording" mode=Listening
2026-09-24T13:18:25.6850125-07:00 P3-STATE: display state voice="Thinking" mic="Mic: listening for interruptions" mode=Thinking
2026-09-24T13:18:25.7717119-07:00 P3-STATE: display state voice="Thinking" mic="Mic: listening for interruptions" mode=Speaking
2026-09-24T13:18:28.4206657-07:00 P3-STATE: display state voice="Speaking" mic="Mic: listening for interruptions" mode=Speaking
2026-09-24T13:18:32.9892207-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle
```

### 3. Barge-in and follow-up

A later spoken turn again returns to Idle. Follow-up capture appears as Listening then back to the resting mic line.

```
2026-09-24T13:19:22.1892073-07:00 P3-STATE: display state voice="Thinking" mic="Mic: listening for interruptions" mode=Thinking
2026-09-24T13:19:22.2556064-07:00 P3-STATE: display state voice="Thinking" mic="Mic: listening for interruptions" mode=Speaking
2026-09-24T13:19:23.7824843-07:00 P3-STATE: display state voice="Speaking" mic="Mic: listening for interruptions" mode=Speaking
2026-09-24T13:19:30.2588179-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle
2026-09-24T13:19:31.0408803-07:00 P3-STATE: display state voice="Listening" mic="Mic: recording" mode=Listening
```

### 4. Text mode

Label `Text mode`, mic off, log `Idle`. Typed send: `Idle → Thinking → Idle`. Then Voice again.

```
2026-09-24T13:20:11.4691826-07:00 P3-STATE: display state voice="Text mode" mic="Mic: off" mode=Idle
2026-09-24T13:20:22.2180900-07:00 P3-STATE: display state voice="Text mode" mic="Mic: off" mode=Thinking
2026-09-24T13:20:31.0000132-07:00 P3-STATE: display state voice="Text mode" mic="Mic: off" mode=Idle
2026-09-24T13:20:54.0537615-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle
2026-09-24T13:20:54.6120421-07:00 P3-STATE: display state voice="Idle" mic="Mic: listening for "Hey Zola"" mode=Idle
```

### 5. Cancel (Option B re-run, Text mode)

```
2026-09-24T13:34:14.6102250-07:00 P3-STATE: display state voice="Text mode" mic="Mic: off" mode=Idle
2026-09-24T13:34:34.1313975-07:00 P3-STATE: display state voice="Text mode" mic="Mic: off" mode=Thinking
2026-09-24T13:34:36.1911900-07:00 P3-STATE: display state voice="Text mode" mic="Mic: off" mode=Idle
```

`Thinking` at 13:34:34, left `Thinking` at 13:34:36 after the interrupt ack. No `Speaking`.

### 6. New session / Resume (Option B re-run)

New session (only `switchInFlight`; still Text mode, so no `Reconnecting voice…` display-state line):

```
2026-09-24T13:35:02.2203520-07:00 P3-STATE: fact switchInFlight=true
2026-09-24T13:35:02.3385231-07:00 P3-STATE: fact switchInFlight=false
```

Resume (`switchInFlight` and `historyPending`):

```
2026-09-24T13:35:23.4202244-07:00 P3-STATE: fact switchInFlight=true
2026-09-24T13:35:23.4205332-07:00 P3-STATE: fact historyPending=true
2026-09-24T13:35:23.5578280-07:00 P3-STATE: fact switchInFlight=false
2026-09-24T13:35:23.5580789-07:00 P3-STATE: fact historyPending=false
```

No `Thinking` or `Speaking` between those bursts. Earlier first-run Voice-mode reconnects at 13:23:09 and 13:23:33 did show `Reconnecting voice…` / `Idle`.

### 7. Kill serve (Option B, machine)

Serve 8296/16480 stopped. Client 16608 stayed running. Parent of 8296 was 18156, not 16608.

```
2026-09-24T13:35:40.3239690-07:00 P3-STATE: fact unreachable=true
2026-09-24T13:35:40.3244083-07:00 P3-STATE: display state voice="Text mode" mic="Mic: off" mode=Dormant
```

### 8. Relaunch

```
2026-09-24T13:25:15.2169319-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle
2026-09-24T13:25:15.2263759-07:00 P3-STATE: display state voice="Idle" mic="Mic: off" mode=Idle
2026-09-24T13:25:15.9308066-07:00 P3-STATE: display state voice="Idle" mic="Mic: listening for "Hey Zola"" mode=Idle
```

Matches step 1.

**Result:** `smoke test passed` (2026-09-24), including Option B re-run of steps 5–7 and developer confirmation of step 7 chrome. Labels unchanged. No `thinking with no events` line. No patch.

## Closeout

- Tests: N/A (no automated suite).
- `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`: 0 warnings, 0 errors.
- `hermes-agent` `git status` clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- No lore file updates (G-LORE-SCOPE).

### Final file list

New:
- `windows-client/Zola.Client/ZolaDisplayState.cs`
- `zola-architecture/lore/prompts/progress/P3-STATE_Progress.md`
- `zola-architecture/lore/build-plans/PHASE3_BUILD_PLAN.md` (plan commit on `main`, Phase 1)

Modified:
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `windows-client/Zola.Client/VoiceController.cs`
- `zola-architecture/identity/VOICE_CONFIG.md`

### Exit criteria (PHASE3_BUILD_PLAN.md Track 1)

- ✅ MET — `ApplyVoiceChrome` is assign-only from `ZolaDisplayState` (no `if`/`else` on voice or window facts).
- ⚠️ PARTIAL — voice-label and mic-line literals are derived only in `ZolaDisplayState.cs`. `MainWindow.xaml` still has the initial `Text="Idle"` and `Text="Mic: off"` attributes (G-NOCHANGE; acknowledged in Phase 4).
- ✅ MET — `PresenceMode` follows `P3-D04` v1.1 on `Current`. Nothing consumes it except the display-state log.
- ✅ MET — `EchoContainmentRatio`, `EchoMinWords`, and `EchoPhraseWords` are gone; the live-rule comments cite `P2-D14`; the three `VOICE_CONFIG.md` rows read `Removed (P3-STATE)`.
- ✅ MET — `display-state.log` writes `P3-STATE: display state …` on first update and every record change, and writes `fact` lines for `unreachable` / `switchInFlight` / `historyPending` even when the record stays equal.
- ✅ MET — Cancel ack → `FinishTurn` clears `_streaming`; `ClearTranscript` clears `_streaming` on new session and resume; `CancelFollowUp` clears `Speaking`; the S26 warning logs only and does not change the mode.
- ✅ MET — `hermes-agent` clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- ✅ MET — `dotnet build … -r win-x64` passed with 0 warnings.
- ✅ MET — HUMAN-RUN smoke passed (2026-09-24), including Option B re-run of Cancel, New session/Resume, and kill-serve `Dormant`.

### SHAs

- Plan commit on `main`: `5994e8bc4e1167c59304ec4b2317f8c9ed9ac94f`
- Implementation commit: `104698ba10cffd3f12bcedd8e983ae1334520923`
- Merge SHA on `main`: `2fb98126eed05561c86b7b3e67ed454b0e7ef331`
