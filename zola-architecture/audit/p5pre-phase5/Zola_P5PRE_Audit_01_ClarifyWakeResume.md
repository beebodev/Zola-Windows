# P5PRE Audit 01 — Clarify wake / mic resume (S41)

**Audit ID:** P5PRE
**Scope:** S41 — wake and mic not restored after a spoken clarify until a Text↔Voice toggle
**Sources:** Windows client at `6494aca…` (`p5pre-audit`). Hermes pin not required for this trace.
**Labels against:** `P2-D12` (one wake authority; `Resting` re-checked after every await), `P4-D14` (one transcript consumer routes clarify answers), `P4-D15` (HUD while waiting).

Static trace only. Live confirmation is Phase 6 L1.

---

## Finding summary (this document)

| ID | Label | Severity | File | Summary |
|---|---|---|---|---|
| P5PRE-AUD-01 | [RISK] | HIGH | `VoiceController.cs` `OnVoiceTranscript` L1954–1972; `OnVoiceStatus` L1867–1881; `OnTurnCompleted` L1619–1656 | Spoken clarify answer sets `_followUpTranscriptSeen` without `OnTurnStarted`. The reply follow-up's silence then skips `CancelFollowUp`, so `Resting` stays false and `wake.resume` is never sent. |
| P5PRE-AUD-02 | [GAP] | MEDIUM | `VoiceController.cs` `ReconcileWakeRestingAsync` L2956–3030; `ResumeWakeAsync` L3072–3090 | Early returns at `!WakeArmed`, generation mismatch, and `!Resting` inside resume are unlogged. A converged "not resting, already paused" return also logs nothing. |
| P5PRE-AUD-03 | [MATCH] | — | `MainWindow.xaml.cs` `OnTranscriptReady` L562–596 | Bound clarify transcripts answer the open request and return. They do not call `SubmitTurnAsync`. |
| P5PRE-AUD-04 | [MATCH] | — | `VoiceController.cs` `ReconcileWakeRestingAsync` L2956–2998; `EnterTextModeAsync` / `EnterVoiceModeAsync` L1474–1524 | One method owns `wake.pause` / `wake.resume`. Text→Voice recovers by `CancelFollowUp` plus a fresh `ArmWakeAsync`. |

---

## 1. Every input to `Resting`

`Resting` is this conjunction. `WakePaused`, `AwaitingAnswer`, and `VoiceGated` are not inputs. A gated machine can still be `Resting`; resume is refused later (`P4-D02`).

```350:364:windows-client/Zola.Client/VoiceController.cs
    public bool Resting
    {
        get
        {
            // P2-WAKE: Resting never depends on WakePaused, so a detect can still start a capture — P2-D12
            return Mode == ModeVoice
                && IsAvailable
                && SessionReady
                && BackendReachable
                && !TurnRunning
                && !Speaking
                && !CaptureActive
                && !_followUpArmed
                && !_followUpCaptureStarted;
        }
    }
```

`Speaking` is `_speakingEstimate || _replyReleaseArmed` (L314).

| Flag | Set true | Set false |
|---|---|---|
| `Mode == ModeVoice` | Field init L293 (`ModeVoice`). `EnterVoiceModeAsync` L1513. | `EnterTextModeAsync` L1492 (`ModeText`). `MarkUnavailable` L3306 (`ModeText`). |
| `IsAvailable` | `ExecuteStopSpeakingAsync` status L1106. Gate-open status L1315. `SyncVoiceModeAsync` L1416. | `MarkUnavailable` L3302 (also forces Text mode). A failed or unavailable status in `SyncVoiceModeAsync` L1411–1421 calls `MarkUnavailable`. |
| `SessionReady` | `SetCaptureGate` L910, from `ZolaDisplayState.UpdateWindowFacts` L157. | Same assignment, when the window passes false. |
| `BackendReachable` | `SetCaptureGate` L911. | Same assignment, when the window passes false. |
| `TurnRunning` | `SetCaptureGate` L912, when the window's `streaming` fact is true. | Same assignment, when streaming is false. |
| `Speaking` (`_speakingEstimate`) | `SetSpeaking(true)`: question speak L591; turn start L1587. Direct assign L2191 inside `ArmReplyFollowUpRelease`. | `SetSpeaking(false)`: `EndQuestionSpeaking` L643; turn start when the clock is ineligible L1577; stop-speaking complete L1628; ineligible clock on complete L1638; `OnFollowUpTimerAsync` L2094; `CancelFollowUp` L2140. |
| `Speaking` (`_replyReleaseArmed`) | `ArmReplyFollowUpRelease` L2184, called from a complete turn L1653. | `ClearReplyFollowUpRelease` L2215, called from `OnTurnStarted` L1560, `CancelFollowUp` L2122, and each successful reply-release open (L2291, L2342, L2420, L2469). |
| `CaptureActive` | `StartCaptureAsync` L1771. `OnVoiceStatus` when state is listening or transcribing L1885. | `OnVoiceStatus` idle L1869. `EnterTextModeAsync` L1493. `MarkUnavailable` L3307. |
| `_followUpArmed` | `OpenClarifyAnswerCaptureAsync` L885 and L894. `OnTurnCompleted` on `"complete"` L1650. | `OnTurnStarted` L1564. `CancelFollowUp` L2129. |
| `_followUpCaptureStarted` | `StartCaptureAsync` when `requiredGeneration` is not null L1784–1786 (clarify capture and reply follow-up). | `OnTurnStarted` L1565. Echo ignore L1939 (this one only). `CancelFollowUp` L2131. |

`SetCaptureGate` (L902–915) is the only writer of `SessionReady`, `BackendReachable`, and `TurnRunning`. It always calls `ReconcileWakeRestingAsync` with `"turn-start"` or `"turn-end"`.

`_followUpTranscriptSeen` is **not** a `Resting` input. It gates whether a silent follow-up capture is allowed to call `CancelFollowUp`. Writers:

| | Lines |
|---|---|
| Set false | `OpenClarifyAnswerCaptureAsync` L887. `OnTurnStarted` L1566. |
| Set true | `OnVoiceTranscript` L1954, for every non-empty, non-echo transcript, before `CancelFollowUp`. |

`CancelFollowUp` does not touch it. `OnTurnCompleted` does not touch it.

---

## 2. Clarify-answer capture lifecycle

### Open

`MainWindow.OnClarifyOpened` (L1096–1132) builds the card, then in Voice mode calls `SpeakQuestionAsync` once per id.

`SpeakQuestionAsync` (L554–609) refuses when gated, not Voice, speech off, or the question text is empty. Otherwise it calls `CancelFollowUp("question-speak")`, speaks `voice.tts`, and waits in `WaitForQuestionReleaseThenCaptureAsync`.

`OpenClarifyAnswerCaptureAsync` (L848–899) then:

1. Skips (logged) if the question token is stale, the gate is closed, mode is not Voice, speech is off, or the broker no longer has that id open. Those skips call `ClearPendingQuestionToken` and do **not** set `_followUpArmed`, except the stale-token skip which returns before that clear.
2. Calls `ArmClarifyAnswerCapture(id)` (L884).
3. Sets `_followUpArmed = true`, `_followUpEchoPending = true`, `_followUpTranscriptSeen = false` (L885–887).
4. Clears the question token and ends question speaking (L892–893), then sets `_followUpArmed = true` again (L894).
5. `await StartCaptureAsync(generation)` (L895). Success sets `CaptureActive` and `_followUpCaptureStarted` (L1771, L1786) and copies the id into `_activeClarifyCaptureId` (L1777).
6. If `CaptureActive` is still false, `CancelFollowUp("clarify-capture-failed")` (L896–898).

### Transcript routing (`P4-D14`)

`OnVoiceTranscript` (L1953–1972) binds `_activeClarifyCaptureId`, or `_closedClarifyCaptureId` if the live id is already gone, then calls `CancelFollowUp("voice.transcript")`, then raises `TranscriptReady`.

`MainWindow.OnTranscriptReady` (L562–596):

- A bound id that is still `Open` → `ApplyVoiceClarifyAnswer` → `AnswerClarify` / batch send. **Return. No `SubmitTurnAsync`.**
- A bound id that is no longer open → late-drop log (length only). **Return. No submit.**
- No bound id, but a clarify is open for this session → answer the newest. **Return.**
- Otherwise → `SubmitTurnAsync` (a normal turn, which calls `OnTurnStarted`).

`AUD-03 [MATCH]`. The answer path is the `P4-D14` branch. It does not start a turn, so `OnTurnStarted` does not run.

The broker send is `ServerRequestBroker.AnswerClarify` (L320–321) → `ClaimAndSendAsync`. Close raises `RequestClosed` → `OnRequestClosed` → `AbandonPendingQuestionIfId` (MainWindow L1166–1169). By then `OpenClarifyAnswerCaptureAsync` has already cleared the question token (L892), so abandon often no-ops on the speak token. The transcript path has already cancelled the follow-up.

### Reply that follows

The clarify tool returns inside the **same** Hermes turn. `message.complete` hits `FinishTurn` → `OnTurnCompleted("complete")` (MainWindow L949–962, VoiceController L1619–1656). That sets `_followUpArmed = true` again (L1650), arms reply release, and reconciles `"follow-up-armed"`. It does not clear `_followUpTranscriptSeen`.

`RunReplyFollowUpReleaseAsync` logs `follow_up_release …` and, on a successful open, calls `ClearReplyFollowUpRelease` then `OnFollowUpTimerAsync` (L2469–2470 and the estimate twins). `OnFollowUpTimerAsync` starts another `StartCaptureAsync(generation)`, which sets `_followUpCaptureStarted` again.

### End-path table

"Flags cleared" means the `CancelFollowUp` / `OnTurnStarted` writes that drop `_followUpArmed` and `_followUpCaptureStarted`. `Speaking` is cleared by the same `CancelFollowUp` (`SetSpeaking(false)` L2140) unless noted. Final `Resting` is what this code computes after that path has finished **and** the reply follow-up window has gone silent, which is the S41 observation. `TurnRunning` is still an input: it is false only after the window reports streaming false.

| End path | Flags cleared | `ReconcileWakeRestingAsync` | Final `Resting` |
|---|---|---|---|
| **Answered** (non-empty transcript, clarify still open) | Yes, immediately: `CancelFollowUp("voice.transcript")` L1970. `_followUpTranscriptSeen` set **true** L1954 and not cleared. Reply complete sets `_followUpArmed` true again L1650. Silence idle does **not** cancel (see AUD-01). | `"follow-up-end"` at the answer (L2142). `"follow-up-armed"` at reply complete (L1656). `"capture-idle"` when the reply follow-up goes idle (L1881). **Not** `"follow-up-end"` for that silence. | **false.** `_followUpArmed` and `_followUpCaptureStarted` stay true. HUD falls through to `Idle` / `Mic: off` (`ZolaDisplayState` L372–373, L422–424). |
| **Cancelled** (card close, `request.cancel`, including timeout) | `OnRequestClosed` → `AbandonPendingQuestionIfId` (L513–527) clears the capture ids. It does **not** call `CancelFollowUp` once the question token is already gone. A later non-empty transcript still cancels via `"voice.transcript"`. A silent capture cancels via `"follow-up-idle"` only if `_followUpTranscriptSeen` is false. Turn interrupt calls `OnTurnCompleted("interrupted")` → `CancelFollowUp("interrupted")` L1660. | `"follow-up-end"` if `CancelFollowUp` runs. Otherwise only `"capture-idle"`. | **true** if `CancelFollowUp` ran and the turn is no longer streaming. **false** if the capture ids were cleared but the armed flags were not, and no later cancel runs. |
| **Timed out** | Same as cancelled. Hermes `request.cancel` reason `timeout` is `ChatSocket` L681 → broker `OnCancel` L199. No extra voice cancel. | Same as cancelled. | Same as cancelled. A timeout **before any answer transcript** leaves `_followUpTranscriptSeen` false (it was cleared at L887), so the silent idle **does** call `CancelFollowUp("follow-up-idle")`. That case can return to `Resting`. |
| **Echo-ignored** | Does not set `_followUpTranscriptSeen` (return is before L1954). Clears `_followUpCaptureStarted` only (L1939). Limit calls `CancelFollowUp("echo-ignored-limit")` L1944. Otherwise reopens via `ReopenFollowUpAfterEchoAsync`. | None on a single ignore. `"follow-up-end"` on the limit. Reopen then `"capture-idle"` or a later cancel. | **false** while reopen is in flight (`_followUpArmed` still true). **true** after the limit cancel, once the turn is not streaming. |
| **Capture failed** | `CancelFollowUp("clarify-capture-failed")` L898, or `"follow-up-record-failed"` from `StartCaptureAsync` L1744 / L1761. | `"follow-up-end"`. | **false** while the clarify turn is still streaming (`TurnRunning`). **true** after that turn ends if nothing re-arms follow-up. |
| **Gated** | Open skips before arming if already gated (L856–860), no flag clear needed. Gate close calls `CancelFollowUp(GateCancelReason)` (`"system-gate"`) at L1172. | `"follow-up-end"`. Resume is then refused: `RefuseIfGated("wake-reconcile-resume")` L2993, which **does** log. | `Resting` can be **true** (gate is not an input) while resume is refused. Ungate uses `wake.start`, not `wake.resume` (`P4-D02`). |
| **Text toggle** | `EnterTextModeAsync` → `CancelFollowUp("mode-text")` L1480. Then `Mode = ModeText` L1492, `CaptureActive = false` L1493. | `"follow-up-end"`, then `DisarmWakeAsync` (wake not armed, so a later reconcile returns at L2979). | **false** in Text (`Mode`). Coming back is the next row. |
| **Voice toggle (the recovery)** | `EnterVoiceModeAsync` does not itself clear follow-up; Text mode already did. `BumpConnectionGeneration` L1511 sets `WakeArmed = false` (L3277). | No `"follow-up-end"` of its own. `SyncVoiceAndWakeAsync` → `ArmWakeAsync` (L1458–1470) starts wake fresh. | **true** after arm, if the other inputs are clear. This is a new `wake.start`, not `wake.resume`. |
| **Session switch** | `OnSessionReady` → `CancelFollowUp("session-ready")` L1675. `ClearTranscript` also calls `AbandonPendingQuestion("session_change")` (MainWindow L1905), which does not by itself cancel follow-up. A new socket bumps generation and clears `WakeArmed` (`OnSessionReady` L1673, and `BumpConnectionGeneration` on the socket path). | `"follow-up-end"`. A reconcile that runs after the generation bump returns at L2979 because `!WakeArmed` (unlogged, AUD-02). The new session arms again through the existing sync. | **true** on the new session after arm, if follow-up was cancelled. |
| **Stop speaking** | `ExecuteStopSpeakingAsync` → `CancelFollowUp("stop-speaking")` L1049. Hidden while `QuestionSpeaking` (L321–322), so it does not apply during the spoken question. On the reply, a stopped turn's complete calls `SetSpeaking(false)` and reconciles `"stop-speaking-complete"` **without** re-arming follow-up (L1626–1633). | `"follow-up-end"` from the cancel, then `"stop-speaking-complete"`. | **true** after the turn is not streaming. Stop does not leave the S41 stuck flags. |

---

## 3. LEAD — `_followUpArmed` left true because the answer is not a new turn

**Refuted as the immediate post-answer state. Confirmed as the state after the reply follow-up goes silent, through a different flag.**

The lead is right that `OpenClarifyAnswerCaptureAsync` sets `_followUpArmed = true` directly (L885 and L894), and that the full clear in `OnTurnStarted` (L1555–1574) does not run for a clarify answer (`AUD-03`).

It is wrong that the answered path therefore leaves `_followUpArmed` true. Every non-empty transcript calls `CancelFollowUp("voice.transcript")` **before** `TranscriptReady` (L1970–1972). That sets both armed flags false (L2129–2131) and reconciles `"follow-up-end"`.

What the answer **does** leave true is `_followUpTranscriptSeen` (L1954). The only clears of that flag are the clarify capture open (L887, which already ran) and `OnTurnStarted` (L1566, which does not run). `OnTurnCompleted` re-arms `_followUpArmed` (L1650) and does not reset the seen flag.

The reply follow-up then starts a capture (`_followUpCaptureStarted = true`). When that capture goes idle with no new transcript:

```1867:1881:windows-client/Zola.Client/VoiceController.cs
        if (RecorderState == StateIdle)
        {
            CaptureActive = false;
            NoteCaptureWindowStopped();
            if (_followUpCaptureStarted && !_followUpTranscriptSeen)
            {
                _followUpEchoPending = true;
                CancelFollowUp("follow-up-idle");
            }

            _ = ReconcileWakeRestingAsync("capture-idle");
        }
```

`_followUpTranscriptSeen` is already true, so `CancelFollowUp("follow-up-idle")` is skipped. Both armed flags stay true. `Resting` stays false. `capture-idle` reconcile sees "not resting, and wake already paused" and treats that as converged (L3007–3011). No `wake.resume`. No error line.

`follow_up_release` itself does not clear `_followUpArmed`. It clears `_replyReleaseArmed` and then opens the follow-up capture. The clear that should run when that capture ends in silence is the one this condition skips. So the release log can be present and `wake.resume` absent, which matches the Phase 6 note in `P4-VOICE_Progress.md` (follow_up_release at 09:59:16, no later `wake.resume`).

A normal follow-up that the user answers does not hit this, because that transcript is a new `prompt.submit` and `OnTurnStarted` clears the seen flag. The stuck path is specific to a transcript consumed inside the same turn. Spoken clarify is that path (`P4-D14`).

**`P2-D12`:** the wake owner is behaving as written. It will not resume while `Resting` is false. The defect is the `Resting` inputs left behind, not a second pause/resume caller. A fix belongs in this one controller (clear the seen flag when a transcript is consumed without a new turn, or do not let that flag suppress the next follow-up's idle cancel).

**`P4-D15`:** after the reply follow-up has gone idle, `AwaitingAnswer` is already false (the clarify is closed). Presence is `Idle` (L373) and the mic line is `Mic: off` (L424), because the listening line requires `Resting && WakeArmed && !WakePaused` (L418–420). That is the reported HUD.

---

## 4. `ReconcileWakeRestingAsync` early returns on the clarify path

```2978:3021:windows-client/Zola.Client/VoiceController.cs
                if (!WakeArmed || generation != Volatile.Read(ref _connectionGeneration))
                {
                    return;
                }
                // ... pause if !Resting && !WakePaused; resume if Resting && WakePaused ...
                    if (!WakeArmed || generation != Volatile.Read(ref _connectionGeneration))
                    {
                        return;
                    }

                    var converged = (Resting && !WakePaused) || (!Resting && WakePaused);
                    // ...
                    if (converged && !pending)
                    {
                        return;
                    }
            // ...
            WriteTimeline("wake reconcile not converged");
```

| Exit | Can it fire on the clarify path? | Logged? |
|---|---|---|
| Coalesce while busy (L2961–2964) | Yes, if question-end, turn-end, and follow-up-end overlap. The holder retries from `finally` (L3026–3028). | No. Pass 2+ logs `wake reconcile pass=`. |
| `!WakeArmed` or generation mismatch (L2979 and L3002) | Yes on Text toggle, session switch, or `MarkUnavailable`, because those bump generation and clear `WakeArmed`. Not the steady Voice clarify path. | **No.** |
| Gate refusal (L2993–2995) | Only when `Resting && WakePaused` and the gate is closed. | **Yes:** `gate refuse wake-reconcile-resume` via `RefuseIfGated` L1390. |
| Converged return (L3007–3011) | **Yes. This is the S41 exit.** After the skipped idle cancel, `Resting` is false and `WakePaused` is true. | **No.** |
| Not converged after 3 passes (L3021) | Only if pause/resume never reaches the matching pair. | **Yes:** `wake reconcile not converged`. |
| `ChatUnreachableException` (L3014–3017) | If the socket dies mid-reconcile. | **Yes.** |
| `ResumeWakeAsync` re-check `!Resting \|\| !WakeArmed \|\| !WakePaused` (L3087–3089) | Yes if `Resting` flips false after the outer check, or wake is not actually paused. | **No.** A generation mismatch just above it logs `stale wake reply` (L3083). |
| `ResumeWakeAsync` `RefuseIfGated` (L3075) | Same as the outer gate check. | **Yes.** |
| `wake.resume skipped after await` (L3101) | If `Resting` became false during the RPC. | **Yes.** |

`AUD-02 [GAP]`. An unlogged converged return is enough to explain "no `wake.resume`" with no error. The S41 path uses that return. The `!WakeArmed` returns are a second, separate silence, used by the Text toggle and by session switch.

---

## 5. Why Text→Voice recovers it

`EnterTextModeAsync` (L1474–1503):

1. `AbandonPendingQuestion("text_mode")`.
2. `CancelFollowUp("mode-text")` — clears `_followUpArmed` and `_followUpCaptureStarted`, clears reply-release, `SetSpeaking(false)`, reconciles `"follow-up-end"`.
3. `voice.toggle` off, `DisarmWakeAsync`, `BumpConnectionGeneration` (`WakeArmed = false`), `Mode = ModeText`, `CaptureActive = false`.

`EnterVoiceModeAsync` (L1506–1524):

1. `BumpConnectionGeneration` again.
2. `Mode = ModeVoice`.
3. `SyncVoiceAndWakeAsync` → `SyncVoiceModeAsync` then `ArmWakeAsync` (L1458–1470).

Recovery is a new arm, not `wake.resume` of the paused detector. `AUD-04 [MATCH]` with `P2-D12`: the toggle does not add a second wake owner. It exits through `CancelFollowUp` and re-enters through `ArmWakeAsync`.

`_followUpTranscriptSeen` is still true after the toggle. That does not matter until the next follow-up capture. The next user turn calls `OnTurnStarted`, which clears it (L1566).

---

## 6. What `voice-timeline.log` cannot show today

Do not add these. A fix track would need them to confirm AUD-01 from the log alone:

1. On every `ReconcileWakeRestingAsync` decision, one line with `reason`, `Resting`, and each input: `Mode`, `IsAvailable`, `SessionReady`, `BackendReachable`, `TurnRunning`, `Speaking`, `CaptureActive`, `_followUpArmed`, `_followUpCaptureStarted`, `_followUpTranscriptSeen`, `WakeArmed`, `WakePaused`.
2. A line when the idle handler skips `CancelFollowUp` because `_followUpTranscriptSeen` is already true while `_followUpArmed` or `_followUpCaptureStarted` is true (`OnVoiceStatus` L1873).
3. A line on the unlogged returns at L2979, L3002, and `ResumeWakeAsync` L3087, naming which predicate failed.
4. The existing `follow_up_release` line does not include `_followUpTranscriptSeen`. Add it there too, so a release that later fails to resume can be tied to the flag without inferring it.

Until those exist, L1 can still **support** AUD-01 if the log shows, in order: clarify answer transcript, `follow_up_release`, follow-up capture start, capture idle, and no `follow-up-idle` / no `wake.resume`. It cannot show the flag values themselves.

---

## LEAD disposition

| Lead | Result |
|---|---|
| `OpenClarifyAnswerCaptureAsync` sets `_followUpArmed` directly, and a clarify answer does not start a turn | **Confirmed** (L885, L894; `OnTranscriptReady` returns before `SubmitTurnAsync`). |
| Those armed flags are therefore still true after the answer is consumed | **Refuted.** `CancelFollowUp("voice.transcript")` clears them before `TranscriptReady`. |
| The later reply follow-up clears them on every ending | **Refuted for the silent ending.** `follow_up_release` opens the capture. The idle ending calls `CancelFollowUp` only when `_followUpTranscriptSeen` is false. The clarify answer left it true. |
