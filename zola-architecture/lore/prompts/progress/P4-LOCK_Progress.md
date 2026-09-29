# P4-LOCK Progress — Lock and Sleep Gate

## Branch

- Branch: `p4-lock-gate`
- Recorded `main` HEAD before the plan commit: `e6d0d09f9355235d80ec98387ce8213c5ac9f9aa` (`audit: record P4PRE merge SHA`)
- Plan commit SHA (= base SHA): `5eb8fd94c69889701fe12809fc2b56b79644a8dc` (`docs: add Phase 4 build plan v1.1`)
- Plan source SHA-256: `d98b3e6c87457266c8c2d06fc57a771cb1c56977790198fa2020429a5216616e` (matched; 54,285 bytes; staged blob byte-identical to source)
- Prompt version: 1.0

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Plan Commit, Branch, and Progress Document | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: One Lock Watcher (`P4-D01`) | COMPLETE |
| 4 | Build: The Voice Gate (`P4-D02`, `P4-D03`) | COMPLETE |
| 5 | Build: Honest HUD Line (`P4-D05`) | COMPLETE |
| 6 | Smoke Test | COMPLETE — S4 ⚠️ PARTIAL (developer-acknowledged; not passed) |
| 7 | Closeout | COMPLETE |

## Closeout SHAs

- Implementation commit: `c01fe3b6725a3814a368d48c0d06a2da1d16305f` (`feat(P4-LOCK): voice gate on Windows lock and sleep — P4-D01..D05`)
- Merge SHA on main: `245d171ebd106f5af52190b63c7d18f866c5a923` (`Merge branch 'p4-lock-gate'`)
- Final main tip: recorded in closeout final message (this docs commit on main)

## Guardrails summary

- **G-SCOPE:** Changes only `PHASE4_BUILD_PLAN.md` (Phase 1 on `main`), `MainWindow.xaml.cs`, `Presence/PresenceView.cs`, `VoiceController.cs`, `ZolaDisplayState.cs`, and this progress document. `SessionLockWatcher.cs` unmodified unless Phase 2 proves a hoist need (flag first).
- **G-ARCH:** The build plan is truth. Conflicts that affect a task are a stop, not a silent deviation. P4-D02 speech-stop must be proven from Hermes source in Phase 2.
- **G-PATTERN:** Read every relevant file in full before changing it. No changes from partial reads or memory of earlier phases.
- **G-NOCHANGE:** No `ChatSocket.cs`, session/process managers, XAML, Themes, csproj, other Presence files, live Hermes profile, or package installs.
- **G-COMMENT:** One `// P4-LOCK: [one-line rationale] — P4-D0X` per logically distinct changed block.
- **G-STOP:** Stop after each phase; wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-LORE-SCOPE:** `ROADMAP.md`, `DESIGN_DECISIONS.md`, and `OPEN_QUESTIONS.md` are out of scope, including closeout. `PHASE4_BUILD_PLAN.md` is not edited after Phase 1. `VOICE_CONFIG.md` is not changed.
- **G-NO-CROSS-SCOPE:** Android Zola, Ava, and the P4PRE spike folder are out of scope.
- **G-ONE-AUTHORITY:** One `SessionLockWatcher` owned by `MainWindow`. One voice gate owned by `VoiceController` (sole `wake.*` / `voice.*` / capture owner). `ZolaDisplayState` alone derives HUD strings from `VoiceController` public properties. No second transcript-to-submit path.
- **G-FAIL-CLOSED:** Any gate-close failure keeps the gate closed; open only on explicit Unlocked/Resumed leaving both locked and suspended false. Never retry into open.
- **G-CONST:** Every new string, timeout, and interval is a named constant.
- **G-DEPS:** No installs of any kind.

## Phase 2 understanding

### 1. Speech-stop mechanism (P4-D02 STOP)

`voice.toggle` actions (Hermes `methods_voice.py` L667–669): `"status"`, `"on"`, `"off"`, `"tts"`. No TTS-only action name beyond `"tts"`.

| Candidate | (a) Stops playing audio? | (b) Cancels turn? | (c) Latches S21? | (d) Disarms wake / releases mic? | (e) Events + client today | (f) Restore speech |
|---|---|---|---|---|---|---|
| **`voice.toggle` `off`** | **Yes.** `_voice_toggle_mode` (L627–648) → `_set_voice_tts(False)` (L648) → `_tts_stream_stop(user_barge=False)` (L656): sets stream `stop` event, then `stop_playback()` which `terminate()`s active ffplay / `sd.stop()` (`voice_mode.py` L949–961). Also sets `HERMES_VOICE=0` and `stop_continuous()`. | **No.** Does not call `agent.interrupt` / `_interrupt_session_turn`. | **No.** `user_barge=False` skips `mark_speech_interrupted` (`methods_voice.py` L117–134). | **No wake lease change.** Does not call `wake.stop`/`wake.pause`. Mic release for wake is a separate `wake.pause` (L525–535). Continuous loop is stopped. Also stops the full-duplex barge listener (see below). | RPC returns status payload only. No `voice.interrupted` emit. Possible `voice.status` idle from continuous stop. Client: `ToggleAsync` result only; `Mode` unchanged unless `EnterTextModeAsync`. `OnVoiceStatus` idle does not leave Voice. Does **not** count toward P2-D13 (`OnVoiceInterrupted` only). | See Phase 4 restore note below. |
| **`voice.toggle` `tts`** (when TTS currently on) | **Yes** via `_set_voice_tts`. Voice mode (`HERMES_VOICE`) **stays on**. | **No** (from the toggle itself). | **No** (from this call). | **No.** Full-duplex barge listener **keeps running**. | Same TTS-cut path. | N/A — **must not use for the gate**. |
| **`voice.toggle` `on` / `status`** | No stop of current audio. | No. | No. | No. | Status / enable only. | `on` alone does **not** re-enable TTS. |
| **`session.interrupt`** (contrast) | **Yes.** `_tts_stream_stop()` default `user_barge=True` (`methods_session.py` L1997). | **Yes.** | **Yes.** | Not wake-specific. | Client Cancel path. | Must not use. |

**Named mechanism for the gate:** `voice.toggle` action **`off`**. Developer-accepted (Phase 2).

**Why not `voice.toggle tts` (developer addition):** `voice.toggle off` also stops Hermes's full-duplex barge-in listener. That listener keeps the mic live from utterance-submit to turn-complete and stops only when voice mode is off (`methods_voice.py` `_should_stop` ~L180–182: `not _voice_mode_enabled() or not (...)`). The TTS-only action leaves `HERMES_VOICE` on, so the barge listener would keep the mic live at the lock screen during generation; a trip would latch `SPEECH_INTERRUPTED_NOTE`, interrupt the turn, and emit a transcript (`_fd_trip` ~L219–246). **Gate speech-stop must be `off`, never `tts`.**

**Phase 4 restore sequence (developer addition):** `voice.toggle on` sets `HERMES_VOICE` only; TTS is separate. Restore = `on`, then `status`, then `tts` only if status shows `tts` off **and** the snapshot had speech on (P2-D03 status-first). Log each call and result.

**Phase 4 Mode guard (developer addition):** gate `voice.toggle off`/`on` replies and any resulting `voice.status` events must **not** change client `Mode` (no `EnterTextModeAsync`). Guarantees today: `Mode` is assigned only in `EnterTextModeAsync`, `EnterVoiceModeAsync`, and `MarkUnavailable`; `OnVoiceStatus` and `ToggleAsync` never assign `Mode`. Phase 4 must keep that invariant and point to it in code.

**P4-D02 STOP condition:** met — do **not** BLOCKED.

### 2. Paths that can open the mic or start a turn

| # | Path | File | Method / site | Line(s) | Gate check goes |
|---|---|---|---|---|---|
| 1 | `wake.detected` → capture | `VoiceController.cs` | `OnWakeDetected` → `HandleWakeDetectedAsync` → `StartCaptureAsync` | 1439–1468 | Top of `HandleWakeDetectedAsync` (refuse + log); also `StartCaptureAsync` |
| 2 | Mic button | `MainWindow.xaml.cs` → `VoiceController.cs` | `OnMicClick` → `ToggleVoiceCaptureAsync` → `ToggleCaptureAsync` → `StartCaptureAsync` | MW / VC | `StartCaptureAsync` (and/or `CanStartCapture` / `ToggleCaptureAsync`) |
| 3 | Ctrl+Space | `MainWindow.xaml.cs` | `OnVoiceHotkey` → same as mic | MW | Same as #2 |
| 4 | Follow-up timer → `voice.record` start | `VoiceController.cs` | `OnFollowUpTimerAsync` → `StartCaptureAsync` | VC | Top of `OnFollowUpTimerAsync`; cancel timer on gate-close |
| 5 | Echo reopen → `voice.record` start | `VoiceController.cs` | `ReopenFollowUpAfterEchoAsync` → `StartCaptureAsync` | VC | Top of `ReopenFollowUpAfterEchoAsync`; cancel on gate-close |
| 6 | Resting reconcile → `wake.resume` | `VoiceController.cs` | `ReconcileWakeRestingAsync` → `ResumeWakeAsync` | VC | Must not resume while gated |
| 7 | Wake capture recovery → `wake.resume` | `VoiceController.cs` | `RecoverWakeCaptureIfNeededAsync` → `ResumeWakeAsync` | VC | Same resume guard |
| 8 | `OnSessionReady` → voice+wake sync | `MainWindow.xaml.cs` | `OnSessionReady` → `SyncVoiceAsync` → `SyncVoiceAndWakeAsync` → `ArmWakeAsync` | MW / VC | Guard sync/arm while gated |
| 9 | Enter Voice mode → sync+arm | `MainWindow` / `VoiceController` | `OnModeClick` → `EnterVoiceModeAsync` | MW / VC | Update snapshot if gated; do not arm mic while gated |
| 10 | Transcript → submit | `VoiceController` → `MainWindow` | `OnVoiceTranscript` → `TranscriptReady` → `SubmitTurnAsync` | VC / MW | Drop while gated; belt-and-braces refuse voice submit |
| 11 | Typed submit | `MainWindow.xaml.cs` | `OnSendClick` → `SubmitTurnAsync` | MW | **Unaffected** (typed) |

### 3. Presence hoist

**Phase 3 done.** `MainWindow` owns the single `SessionLockWatcher` (after hwnd); forwards Locked/Unlocked/Suspending/Resumed to `PauseRendering` / `OnUnlockOrPowerResume` with `PresenceView.PauseLocked` / `PauseSuspended`, and to `VoiceController.SetSystemGate`. `PresenceView` no longer constructs or disposes the watcher; `OnUnlockOrPowerResume` is `internal`. `SessionLockWatcher.cs` unchanged.

Search: exactly one `new SessionLockWatcher(` — `MainWindow.xaml.cs:118`.

### 4. Threading and ordering

- Watcher events arrive on the **UI thread**.
- **`SetSystemGate` serialization:** Phase 3 stores facts only. Phase 4 adds the async queue (latest desired wins; open waits for close).

### 5. In-flight turn

Gate-close will `CancelFollowUp`; turn text still lands; speech stopped via `voice.toggle off` without cancelling the turn.

### 6. Mic-line priority

Gated line goes first (Phase 5). `VoiceController` now exposes `SystemLocked`, `SystemSuspended`, `VoiceGated` (Phase 3 stub).

### 7. Latch evidence (Part B)

Behavioural + absence of `SPEECH_INTERRUPTED_NOTE` on the next turn. S2b (below) also proves no barge trip while Thinking.

### 8. Flags

- No P4-D02 BLOCKED. Mechanism: **`voice.toggle off`** (never `tts`).
- Primary risk: `ReconcileWakeRestingAsync` / `OnSessionReady` sync behind the gate — Phase 4 guards.

## Phase 3 notes

- One watcher: `MainWindow.xaml.cs:118` (`_lockWatcher = new SessionLockWatcher(hwnd);`).
- Presence pause/resume paths unchanged in effect (`PauseRendering` / `OnUnlockOrPowerResume` / `_pauseReasons` / revalidate).
- `SetSystemGate` logs `gate fact: locked=… suspended=…` only; no voice RPCs yet.
- Build: pass.

## Phase 4 notes

### Fact-before-queue (developer constraint)

`SetLocked(bool)` / `SetSuspended(bool)` replace the two-argument `SetSystemGate`. Each method:

1. Updates `SystemLocked` or `SystemSuspended` **synchronously on the caller (UI) thread**
2. If facts are gated, sets `_gateHolding = true` immediately (guards never see an open window)
3. Logs `gate fact: locked=… suspended=…`
4. Raises `StateChanged`
5. **Then** increments `_gateEpoch` and enqueues `RunGateSequenceAsync`

The worker re-reads `SystemLocked` / `SystemSuspended` when it runs (latest desired state wins). Open waits for any in-flight close. `VoiceGated => SystemLocked || SystemSuspended || _gateHolding` so after unlock the HUD facts clear while holds refuse until open completes.

MainWindow never reads facts back to pass them in.

### Mode invariant (developer constraint)

Gate `voice.toggle off` / `on` / `status` / `tts` go only through `ToggleAsync`, which updates `_ttsOn` from the reply and **never assigns `Mode`**. `Mode` is assigned only in `EnterTextModeAsync`, `EnterVoiceModeAsync`, and `MarkUnavailable`. `OnVoiceStatus` does not change `Mode`. Gate-close comment documents this at the `voice.toggle off` step.

### Restore sequence

`on` → `status` → `tts` only if snapshot had speech and status shows tts off → **`ArmWakeAsync(fromGateOpen: true)`** (`wake.start` + existing retry). No `wake.resume`. Each step re-checks facts; aborts with `gate open aborted: re-gated` if re-locked. `_gateCloseCompleted = false` at open start so a mid-open relock re-runs close.

### Close sequence (updated)

snapshot (first of episode only) → cancel follow-up/echo → `voice.record stop` if open → `voice.toggle off` → **`wake.stop` (`DisarmWakeAsync`)** → `wake.status` verify; if `listening` still true, `DisarmWakeAsync` again (fail-closed).

### Snapshot

Taken only on the first close of a gated episode (`_gateSnapshotTaken`). Mode changes while gated may update it in place. Cleared only when open completes with both facts false. Second close logs `gate snapshot: retained`.

### Guard sites (final lines after Phase 4 fixes)

| # | Path | Guard |
|---|---|---|
| 1 | `HandleWakeDetectedAsync` | `RefuseIfGated` |
| 2–3 | `StartCaptureAsync` / `CanStartCapture` | refuse + `!VoiceGated` |
| 4 | `OnFollowUpTimerAsync` | `RefuseIfGated` |
| 5 | `ReopenFollowUpAfterEchoAsync` | `RefuseIfGated` |
| 6 | `ReconcileWakeRestingAsync` resume | `RefuseIfGated` |
| 7 | `ResumeWakeAsync` | `RefuseIfGated` (full gate; not used by open) |
| 8 | `SyncVoiceModeAsync` / `SyncVoiceAndWakeAsync` | `RefuseIfGated` |
| 9 | `EnterVoiceModeAsync` while gated | snapshot only |
| 10 | `OnVoiceTranscript` + MW TranscriptReady | drop / refuse |
| — | `ArmWakeAsync(fromGateOpen: false)` | full `RefuseIfGated` |
| — | `ArmWakeAsync(fromGateOpen: true)` | refuses iff `SystemLocked \|\| SystemSuspended` |
| — | `ResyncAfterStopAsync` | `RefuseIfGated` |

### Other

- No `session.interrupt` in the gate path.
- No global `_gateOpenRestoring` bypass.
- P2-D13: `_selfInterruptCount` only in `OnVoiceInterrupted`.
- Build: pass.

## Phase 4 implementation checklist (from Phase 2 + developer additions)

- [x] Gate-close: snapshot → cancel follow-up/echo → `voice.record stop` → **`voice.toggle off`** → **`wake.stop`** → `wake.status` verify; serialize; G-FAIL-CLOSED.
- [x] Gate-open: `_gateCloseCompleted=false` at start; `on` → `status` → conditional `tts` → `ArmWakeAsync(fromGateOpen)`; abort if re-gated; never replay audio.
- [x] Mode invariant; guards; transcript drop; P2-D13 unaffected.
- [x] Snapshot once per episode; mode change while gated updates in place.
- [x] `SetLocked` / `SetSuspended`; facts never lag the queue.

## Phase 5 notes

- Gated mic branch is first: `SystemLocked` → `"Mic: paused — Windows locked"`; suspended-only → `"Mic: paused — sleeping"`.
- `_lastGatedMicLine` in `ZolaDisplayStateModel` remembers the last gated string while `VoiceGated` is hold-only (facts false, open still running). Cleared when `VoiceGated` becomes false.
- Voice label, `PresenceMode`, mode word, and button rules unchanged.
- HUD mic strings only in `ZolaDisplayState.cs` (search quoted).
- Build: pass.

**Part C check (developer):** `display-state.log` shows no other mic line between unlock and the first `"listening for 'Hey Zola'"` line (gated string holds through open).

## Phase 6 smoke additions (developer)

**S2b — Lock while she is thinking** (after S2):

1. "Hey Zola, search the web and tell me today's top news story."
2. While HUD says Thinking (before she speaks), Win+L.
3. At the lock screen say loudly: "Stop. Zola, stop."
4. Wait 30 s. Unlock. Full reply text in conversation, not marked interrupted? (expect: yes, complete)

**Part C evidence for S2b:** `voice.toggle off` logged at gate close before her first TTS; no `voice.interrupted`, no `voice.transcript`, no `session.interrupt`; turn ends completed (not `interrupted_by_user`) in `agent.log` / `gui.log`.

**Part C evidence for S4 (developer addition):** the log shows `suspended=true` arriving before `locked=true` (or the reverse) and the gate never logs `gate opened` until both facts are false.

**S5b — Relock during unlock** (after S5):

1. Voice mode. Win+L. Wait 10 s.
2. Unlock, and IMMEDIATELY (within 1–2 s) Win+L again.
3. Wait 10 s. Say "Hey Zola, what time is it?" (expect: no answer)
4. Unlock. After 5 s: HUD listening, "Hey Zola" works.

**Part C evidence for S5b:** `gate open aborted: re-gated` or a close re-run after the open; final `wake.status` `listening=false` while locked; no `wake.detected` → capture while locked.

## Discrepancies and flags

- Phase 1: `core.autocrlf=true` checkout warning; staged blob verified byte-identical to plan source.
- hermes-agent: HEAD `345cd2b057a452236de401d3534b8502a7465e8d`, tag `v2026.9.14`, porcelain empty (Phase 1–7). Live profile `config.yaml` LastWriteTime unchanged since before this track (`2026-09-23T15:32:27`).
- Phase 2 accepted: `voice.toggle off`; never `tts` (full-duplex barge reason).
- **P4-D02 execution correction: `wake.pause` → `wake.stop`, developer-approved.** Reason: `voice.record stop` in Hermes calls `_resume_voice_wake()`, and `_wake_resume_if_owner` can retry `resume_listening` for up to 15 s when the mic is busy (`methods_voice.py` ~L347–375, ~L722) — that can reopen the mic after a `wake.pause`; after `wake.stop` the retry finds no detector and gives up. Open re-arms with `ArmWakeAsync` (`wake.start` + existing retry) only. (Plan exit text still says `wake.pause`; logs use `wake.stop`.)
- **Modern Standby (S4):** sleep delivers neither a WTS lock nor an APM suspend on the Latitude 7430 with "require sign-in on wake" off; voice is not gated during screen-off standby. Three sleep attempts (13:57, 14:07, 14:10); neither WTS lock nor `PBT_APMSUSPEND`/`RESUMEAUTOMATIC` reached this process; presence kept rendering 14:09–14:11, so the process stayed live. The Suspending/Resumed gate code is implemented and unexercised on this machine. Developer mitigation: set Windows to require sign-in on wake, so sleep produces a lock and the P4-D01/D02 lock gate applies. Candidate signals for a future track: `RegisterPowerSettingNotification` with `GUID_CONSOLE_DISPLAY_STATE` / `GUID_MONITOR_POWER_ON`, or `RegisterSuspendResumeNotification`. Not implemented (P4-D04 scope: no new detection APIs). For the Phase 4 lore closeout: file alongside S33 at raised priority. **S4 is not marked passed** — ⚠️ PARTIAL, developer-acknowledged.

## Smoke evidence tables (Phase 6)

### Part A (CURSOR-RUN) — 2026-09-29

- Build: pass
- hermes-agent: clean at `345cd2b057a452236de401d3534b8502a7465e8d`
- G-ONE-AUTHORITY: one `new SessionLockWatcher(` at `MainWindow.xaml.cs:118`; no `session.interrupt` in gate path (comment only); HUD mic strings only in `ZolaDisplayState.cs`; one `TranscriptReady` → submit path (VC raise + MW handler)
- Client launched: `…\win-x64\Zola.Client.exe` at **2026-09-29T13:39:54-07:00**
- Voice + wake armed: `voice-timeline.log` `wake.start … started=True` at **13:39:57.174**; `display-state.log` `mic="Mic: listening for "Hey Zola""` at **13:39:57.176**
- Log dir: `%LOCALAPPDATA%\ZolaClient\logs\` (`voice-timeline.log`, `display-state.log`, `presence.log`); Hermes `%LOCALAPPDATA%\hermes\profiles\zola\logs\` (`gui.log`, `agent.log`)

### Part B (HUMAN-RUN) — developer report 2026-09-29

| Step | Time | Human result | Notes |
|---|---|---|---|
| S1 | 13:48 | passed | — |
| S2 | 13:51 | passed | After "Did I interrupt you?": "No-you sent a new message after my reply finished." |
| S2b | 13:54 | passed | — |
| S3 | 13:56 | passed | — |
| S4 | 13:57; 14:07; 14:10 | **not passed** — ⚠️ PARTIAL (developer-acknowledged) | Device did **not** lock on sleep; wake went straight to desktop with no sign-in. No optional screen-dark "Hey Zola" result recorded. |
| S5 | 13:59 | passed | — |
| S5b | 14:00 | passed | — |
| S6 | 14:01 | passed | — |

Overall human verdict: **smoke test passed** for S1–S3, S5, S5b, S6; **S4 not passed** (acknowledged Modern Standby gap).

### Part C (CURSOR-RUN) — log evidence 2026-09-29

Logs: `%LOCALAPPDATA%\ZolaClient\logs\` + `%LOCALAPPDATA%\hermes\profiles\zola\logs\`  
`session.interrupt` in smoke window: **0** hits. `SPEECH_INTERRUPTED` / `interrupted_by_user` in smoke turns: **none**. `suspended=true` in `voice-timeline.log`: **0** (entire file).

#### S1 — Wake after lock (13:48) ✅

| Check | Evidence |
|---|---|
| Presence pause/resume | `presence.log` `P3-RENDER: paused (locked)` @ 13:48:44.502; `resumed (locked)` + `scene reused` @ 13:49:33.387 / 13:49:33.504 |
| Gate close | `gate fact: locked=true` → snapshot `mode=voice speech=true wakeArmed=true` → `voice.toggle off ok=true` → `wake.stop` → `wake.status listening=False` → `gate closed: done` @ 13:48:44.659 |
| No wake while locked | No `wake.detected` between 13:48:44.659 and 13:49:34.832 |
| HUD hold → listening | `display-state` mic `"Mic: paused — Windows locked"` @ 13:48:44.522; next mic line is `"Mic: listening for "Hey Zola""` @ 13:49:34.833 (no other mic string in between) |
| Gate open | `on` → `status` → `tts` → `wake.start … started=True` → `gate opened: done` @ 13:49:34.832 |

#### S2 — Lock while speaking (13:51) ✅

| Check | Evidence |
|---|---|
| Speech stop ≤1 s | Turn TTS @ 13:51:14.386; `gate closed: starting` @ 13:51:15.479; Hermes `Audio playback interrupted` @ 13:51:15.486 (~1.1 s from TTS save / ~0 within same second as gate) |
| Follow-up cancelled | `fireOrCancel=system-gate followUpStarted=False words=38` @ 13:51:15.481 |
| `voice.toggle off` + wake stop | `voice.toggle off ok=true enabled=False tts=False`; `wake.status listening=False` @ 13:51:15.621 |
| No `session.interrupt` | 0 matches in smoke window |
| Turn text kept | Saturn turn `Turn ended: reason=text_response(finish_reason=stop)` @ 13:51:14.361 (before lock); full reply already complete |
| Latch (no S21) | Next turn msg=`Did I just interrupt you?` @ 13:51:54.683 — no `SPEECH_INTERRUPTED` / `interrupted_by_user`; human: "No-you sent a new message after my reply finished." |
| Guards while closing | `gate refuse: wake-reconcile-resume` ×2 @ 13:51:15.482 |

#### S2b — Lock while thinking (13:54) ✅

| Check | Evidence |
|---|---|
| Lock during Thinking | `display-state` Thinking + `"Mic: paused — Windows locked"` @ 13:54:21.855; gate close @ 13:54:21.848 |
| `voice.toggle off` before reply TTS | Close: `voice.toggle off` @ 13:54:22.049; **no** `Generating speech` for this turn while locked; turn `status=complete` @ 13:54:26.594 |
| No barge / interrupt latch | No `voice.interrupted`, no `session.interrupt`; `Turn ended: reason=text_response(finish_reason=stop)` response_len=331 @ 13:54:26.570 |
| Wake stream closed on stop | Hermes `wake word: stream closed` @ 13:54:22.082 (with client `wake.stop`) |
| Restore | `gate opened: done` + `wake.start started=True` @ 13:55:12.779 |

#### S3 — Text mode (13:56) ✅

| Check | Evidence |
|---|---|
| Text + lock | `display-state` `voice="Text mode" mic="Mic: off"` then `"Mic: paused — Windows locked"` @ 13:56:19.902 |
| Snapshot text | `gate snapshot: mode=text speech=false wakeArmed=false` @ 13:56:19.896 |
| Open skips voice restore | `gate opened: skipped - snapshot text mode` @ 13:56:33.490; mic back to `"Mic: off"` then after mode switch `listening for "Hey Zola"` @ 13:56:37.789 |

#### S4 — Sleep (13:57; retests 14:07, 14:10) ⚠️ PARTIAL — developer-acknowledged (not passed)

| Check | Evidence |
|---|---|
| Human | **Not passed.** Developer confirms device did not lock on sleep; waking went straight to desktop with no sign-in. Attempts @ 13:57, 14:07, 14:10. |
| `suspended=true` / sleep pause | **ABSENT on all three attempts.** Zero `suspended=true` in `voice-timeline.log`. Zero `paused (suspended)` / `"Mic: paused — sleeping"`. |
| Attempt 3 (14:10) detail | No gate facts 14:08–14:11. Presence blinks continuous 14:09–14:11; `paused (minimized/hidden)` @ 14:11:26 only. Post-wake `wake.detected` @ 14:11:38. |
| Code | Suspending/Resumed → `SetSuspended` / gate close+open **implemented**; **unexercised** on this machine (Modern Standby; sign-in-on-wake off). |

Closeout: exit criterion sleep/wake recorded ⚠️ PARTIAL (see Exit-criteria table). Not marked passed.

#### S5 — Quick lock/unlock (13:59) ✅

| Check | Evidence |
|---|---|
| Close then open | Lock `gate closed: done` @ 13:59:51.513; unlock open starts @ 13:59:54.050; `wake.start` + `gate opened: done` @ 13:59:55.205 |
| Armed | `display-state` listening @ 13:59:55.206; `wake.detected` @ 13:59:57.630 |

#### S5b — Relock during unlock (14:00) ✅

| Check | Evidence |
|---|---|
| Close after open (re-run) | Open done @ 14:01:00.779; **59 ms later** `gate fact: locked=true` + full close (`wake.status listening=False`) @ 14:01:00.896 — satisfies "close re-run after the open" (no `gate open aborted` because open had finished) |
| No wake while locked | No `wake.detected` during 14:00:58–14:01:02 gated intervals; HUD `"Mic: paused — Windows locked"` @ 14:00:58.212 and 14:01:00.844 |
| Final restore | Unlock open done @ 14:01:03.621; listening HUD; `wake.detected` @ 14:01:06.689 |

#### S6 — Regression (14:01–14:02) ✅

| Check | Evidence |
|---|---|
| Barge-in | `fireOrCancel=voice.interrupted followUpStarted=False` @ 14:02:16.219; Hermes `Audio playback interrupted` @ 14:02:16.217; next turn includes user-interrupt note (normal barge path, not gate) |
| Follow-up without wake | `followUpStarted=True` @ 14:02:28.310 then `voice.transcript` / further follow-up @ 14:02:45.618; `wake.resume reason=follow-up-end` @ 14:02:59.639 |
| Mic / hotkey | Human pass; capture pause/resume pairs @ 14:03:03–14:03:11 |

### Part C verdict

| Step | Part C |
|---|---|
| S1 | ✅ |
| S2 | ✅ |
| S2b | ✅ |
| S3 | ✅ |
| S4 | ⚠️ PARTIAL — developer-acknowledged; **not passed** |
| S5 | ✅ |
| S5b | ✅ |
| S6 | ✅ |

**Phase 6 status: COMPLETE** with S4 acknowledged partial. Closeout authorized by `proceed to closeout`.

## Exit-criteria table (closeout)

Track 1 exit criteria from `PHASE4_BUILD_PLAN.md` (§ Lock and Sleep Gate):

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Exactly one `SessionLockWatcher` (constructor in `MainWindow`) | ✅ MET | `new SessionLockWatcher(` only at `MainWindow.xaml.cs:118`; `PresenceView` no longer constructs one |
| 2 | Presence pauses/resumes on lock, unlock, suspend, resume | ⚠️ PARTIAL | Lock/unlock: `P3-RENDER: paused (locked)` / `resumed (locked)` throughout smoke (e.g. S1 13:48:44 / 13:49:33). Suspend/resume presence path **unexercised** (no APM events on this machine) |
| 3 | Idle Voice → Win+L → no answer; no wake→submit while locked; gate closed + wake disarmed | ✅ MET | S1: no `wake.detected` while locked; `gate closed: done` + `wake.stop` + `wake.status listening=False` @ 13:48:44 (plan text said `wake.pause`; approved correction uses `wake.stop`) |
| 4 | Speaking → Win+L → speech stops ≤1 s; no follow-up while locked; text kept; no interrupt latch | ✅ MET | S2: TTS interrupt @ 13:51:15.486 with gate close; `followUpStarted=False`; next turn no S21 latch (human + agent log) |
| 5 | Unlock Voice → wake re-armed ≤3 s; Unlock Text → still Text, mic off | ✅ MET | S1 open+`wake.start` @ 13:49:34 (~1.4 s); S3 `gate opened: skipped - snapshot text mode`, mic off then mode restore |
| 6 | Sleep → gate closed across sleep; re-open only on Unlocked | ⚠️ PARTIAL — developer-acknowledged | Three sleep attempts; neither WTS lock nor `PBT_APMSUSPEND`/`RESUMEAUTOMATIC` reached this process (Modern Standby; Windows not requiring sign-in on wake); presence kept rendering 14:09–14:11. Suspending/Resumed gate code implemented, unexercised. **Not marked passed.** |
| 7 | HUD "Mic: paused — Windows locked" while locked | ✅ MET | `display-state` e.g. 13:48:44.522; held through open until listening @ 13:49:34.833 |
| 8 | Voice/Text, barge-in, follow-up, P2-D13 unchanged outside lock | ✅ MET | S6 barge `voice.interrupted`; follow-up without Hey Zola; S3 Text toggle; `_selfInterruptCount` only in `OnVoiceInterrupted` |
| 9 | No changes to `TtsPlaybackMonitor`, `PresenceAnimator`, render pipeline | ✅ MET | Diff only MW, PresenceView (watcher hoist), VoiceController, ZolaDisplayState, progress doc |
| 10 | Build passes | ✅ MET | `dotnet build … -r win-x64` — 0 errors, 0 warnings (closeout 7a) |
| 11 | Smoke Part B: L1b/L2/L3 + sleep/wake | ⚠️ PARTIAL | S1≈L1b, S2≈L2, S2b barge-while-thinking, S5/S5b, S6≈L3: ✅. Sleep/wake (S4): ⚠️ not passed (acknowledged) |

**Final files (this track):** `MainWindow.xaml.cs`, `Presence/PresenceView.cs`, `VoiceController.cs`, `ZolaDisplayState.cs`, `P4-LOCK_Progress.md` (+ `PHASE4_BUILD_PLAN.md` on `main` in Phase 1). `SessionLockWatcher.cs` unmodified.
