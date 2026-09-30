# P4-ASK Progress — Spoken Questions and Answers

## Branch

- Branch: `p4-ask`
- Base commit SHA (`main` HEAD at branch): `24bfee5ff605d72a1e07f090f0088e8140878d91` (`docs: record P4-REQUEST merge SHA`)
- Plan on `main`: `PHASE4_BUILD_PLAN.md` v1.1 — SHA-256 `d98b3e6c87457266c8c2d06fc57a771cb1c56977790198fa2020429a5216616e` (54,285 bytes; verified matched; not re-committed)
- Prompt version: 1.1 (2026-09-30)
- Hermes HEAD verified Phase 2: `345cd2b057a452236de401d3534b8502a7465e8d` (clean)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Transcript Routing (`P4-D14`) | COMPLETE |
| 4 | LIVE PROBE: Barge Listener (developer decision) | COMPLETE — Option A chosen |
| 5 | Build: Speak the Question and Listen (`P4-D13`) | COMPLETE |
| 6 | Build: Honest Waiting State (`P4-D15`) | COMPLETE |
| 7 | Smoke Test | COMPLETE |
| 8 | Closeout | COMPLETE |

## Closeout SHAs

- Implementation commit: `7d0d81fcd8283234a62ed54a3f0acaf15fb3d46c`
- Merge SHA on main: 95578b10843feed473b83482c30e199bb909aa61
- Final main tip: recorded in closeout final message (this docs commit on main)

## Final file list

**New:**
- `zola-architecture/lore/prompts/progress/P4-ASK_Progress.md`

**Modified:**
- `windows-client/Zola.Client/VoiceController.cs`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `windows-client/Zola.Client/ZolaDisplayState.cs`
- `windows-client/Zola.Client/ServerRequestBroker.cs` (read-only SessionId / late-drop log helpers)
- `windows-client/Zola.Client/Presence/PresenceView.cs` (bout forward)
- `windows-client/Zola.Client/Presence/PresenceAnimator.cs` (bout re-raise; Phase 5 approved smallest forward path)
- `zola-architecture/identity/VOICE_CONFIG.md` (`voice.barge_in: false` / P4-D25)

**Live profile (not in git):** `voice.barge_in: false`; backup `config.yaml.bak-P4-ASK-20260930-102716`

## Phase 4 decision

**Option A** — profile `voice.barge_in: false` (P4-D25), then client speak + clarify-answer capture (P4-D13/D14). C11 = talk-over does not interrupt; Cancel still stops a live streaming turn.

## Exit criteria (PHASE4_BUILD_PLAN.md Track 3)

| Criterion | Result | Evidence |
|---|---|---|
| Voice clarify spoken; capture after playback; voice answer → card + spoken reply | ✅ MET | C1 / C1 reconfirm |
| Choices spoken as "Options:…"; "the second one" uses second choice | ✅ MET *(changed by developer 2026-09-30 / P4-D13 amend)* | Speak question only; C2 free-form voice answer used by Hermes |
| "stop" → Skip | ✅ MET | C3 |
| Late answer after Cancel → drop + notice; no prompt.submit | ✅ MET | C4 (+ closed-id stash fix) |
| Echo / silence → no self-answer | ✅ MET | C5 |
| Waiting HUD + LISTENING/IDLE; no 120s stale | ✅ MET | C6 |
| Lock while open; typed answer after unlock | ✅ MET | C7 |
| Normal voice turn → prompt.submit | ✅ MET | C10 |
| Build passes | ✅ MET | closeout build |
| Smoke Part B | ✅ MET | C1–C12 + Part C |

### Track checks

| Check | Result |
|---|---|
| One `TranscriptReady` handler | ✅ MET (VC raise + MW `OnTranscriptReady`) |
| No `prompt.submit` while clarify open | ✅ MET (bound/unbound clarify branches before SubmitTurn) |
| `voice.tts` only from `VoiceController` | ✅ MET (`MethodTts` / `SpeakQuestionAsync` only) |
| One `TtsPlaybackMonitor` | ✅ MET (`PresenceAnimator` L103) |
| No answer text in client logs | ✅ MET (Part C) |
| hermes-agent clean at `345cd2b0…` | ✅ MET |
| `git diff` vs main only G-SCOPE files | ✅ MET (listed above; PresenceAnimator = approved bout forward) |

## Exit-criteria table (closeout)

(See table above.)


## Guardrails summary

- **G-SCOPE:** Only `VoiceController.cs`, `MainWindow.xaml.cs`, `ZolaDisplayState.cs`, `Presence/PresenceView.cs` (expose existing `TtsPlaybackMonitor` bout signal only; flag exact change at Phase 2 stop), optional read-only query on `ServerRequestBroker.cs` (flag first; no state-machine changes), live profile `voice.barge_in: false` only if Option A at Phase 4 STOP (P4-D25), `VOICE_CONFIG.md` only with Option A, and this progress doc.
- **G-ARCH:** Build plan is truth; stop on conflict. **K2 is a known plan conflict** — Phase 4 measures it; do not design around it before the developer Option A–D decision.
- **G-PATTERN:** Read every relevant file in full before changing it. No partial reads or memory of prior phases.
- **G-NOCHANGE:** No `ChatSocket.cs`; no `ServerRequestBroker` state machine; no `TtsPlaybackMonitor` internals; no `PresenceAnimator` / render pipeline; no `SessionLockWatcher`, process/session managers, `App.xaml(.cs)`, csproj, `SOUL.md`, other profile keys, or hermes-agent edits.
- **G-COMMENT:** One `// P4-ASK: [rationale] — P4-D1X` per logically distinct changed block.
- **G-STOP:** Stop after each phase; wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-LORE-SCOPE:** No lore file updates (`ROADMAP`, `DESIGN_DECISIONS`, `OPEN_QUESTIONS`, etc.), including closeout. `PHASE4_BUILD_PLAN.md` not edited.
- **G-NO-CROSS-SCOPE:** Android Zola, Ava, Hermes TUI/Desktop UI, and P4PRE spikes are out of scope.
- **G-ONE-AUTHORITY:** `VoiceController` sole owner of `voice.*` / `wake.*` and question speech; one `TranscriptReady` handler (clarify answer or `SubmitTurnAsync`); broker sole responder; `ZolaDisplayState` sole display authority; one `TtsPlaybackMonitor` (forwarded, never duplicated).
- **G-FAIL-CLOSED:** Late clarify-answer transcript for non-Open id → drop + log, never submit; while gated → no speech, no capture; if speech-end unknown → `P2-D15` estimate; if estimate missing → no capture (card still typed).
- **G-CONST:** Every new string, timeout, margin and tag is a named constant.
- **G-DEPS:** No installs of any kind.
- **G-PRIVACY:** Spoken answer text never logged; `voice-timeline.log` / `server-requests.log` record transcript length only; question text may be logged.

## Discrepancies and flags

- **K2 confirmed (not BLOCKED):** plan conflict is real; Phase 4 probe required before speech/capture code. Do not design around it until Option A–D.
- **PresenceView / monitor forward (Phase 5):** see Developer notes for Phase 5 §1 (approved thin `PresenceAnimator` pass-through).
- **Broker read-only query (flag first):** `ClarifyView` has no `SessionId`. Pre-capture recheck needs "id belongs to current session". Propose additive `TryGetSessionId(string id)` or add `SessionId` to `ClarifyView` (read-only; no state-machine change). Defer until Phase 5 unless Phase 3 needs it (Phase 3 can use `GetState` + `NewestOpenClarify(current)` without session-of-id).
- **Batch voice (K7):** spoken transcript fills first unanswered row only; does not send — record as batch interpretation of P4-D14.
- Effective config reminder: profile **and** `config_defaults.py` (P4-REQUEST lesson).

## Phase 2 understanding

Hermes HEAD re-verified: clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

### 1. K2 verification (STOP) — confirmed; probe still runs

**(a) Armed at turn start; live during clarify wait — YES.**  
`prompt_turn.py` `_start_turn_voice` L183–191: if voice mode on and `voice.barge_in` not false → `_arm_full_duplex_listener()`.  
`methods_voice.py` `_full_duplex_listener` L173–182: `_should_stop` is false while `_any_session_running()` **or** `_fd_tts_pending()` **or** `is_audio_output_active()`. A turn blocked in clarify is still running → listener stays live for the whole wait.

**(b) Trip phases (`_fd_trip` L219–246):**  
- Always: `mark_speech_interrupted()` (S21 latch), cut streaming TTS + fallback speak pipelines, `stop_playback()`, emit `voice.interrupted`.  
- **`playback`:** no `agent.interrupt()`.  
- **`generation` (else):** also `agent.interrupt()` on every running session agent (L237–243).

**(c) After `agent.interrupt()` during clarify:**  
`InterruptControlMixin.interrupt` (`agent/interrupt_control.py` L93–189) sets `_interrupt_requested` and per-thread `set_interrupt` — **does not** call `_clear_pending` / `server_requests.cancel`.  
Clarify wait is `server_requests.send` → `req.event.wait` (`server_requests.py` L101–123); Event.wait does **not** poll the interrupt flag.  
`clarify` is in `_NEVER_PARALLEL_TOOLS` (`tool_dispatch_helpers.py` L28) → runs inline on the agent thread (`tool_executor.py` L841–842), so the sequential interrupt-poll wait loop does **not** abandon it mid-wait.  
- **(i) Client later answers:** `resolve_response` sets the event → clarify returns the answer. Interrupt flag remains. On the next loop iteration, `begin_iteration` sees `_interrupt_requested` and breaks with `_turn_exit_reason = "interrupted_by_user"` (`agent/turn_iteration_prep.py` ~L330–335; `conversation_loop.py` ~L1514–1516). So even a successful clarify answer after a generation-phase barge trip is expected to leave the turn **interrupted** rather than producing a normal post-clarify reply — **live probe must confirm**. SPEECH latch / `SPEECH_INTERRUPTED_NOTE` may still affect a following turn (`prompt_turn.py` L509–511).  
- **(ii) Client does not answer:** wait continues until clarify timeout → `request.cancel` reason `timeout` (L118–119). Barge trip alone does **not** emit `request.cancel`.  
`request.cancel` from interrupt only via `_clear_pending` → `server_requests.cancel` (`server.py` L1385–1389), which is the **`session.interrupt` / `_interrupt_session_turn`** path (`session_lifecycle.py` ~L390–429) — not `_fd_trip`. Late answers after cancel are dropped (`resolve_response` when id absent from `_open`).

**(d) Effective `voice.barge_in`:** profile `config.yaml` L65–67 has `voice.barge_in: true`. Defaults `config_defaults.py` L1126/L1152 also `True`. **Effective = true.**

**(e) Stop listener during a running turn besides barge_in false / voice off?** `_should_stop` also true when no session running **and** no pending TTS **and** no audio output — i.e. turn fully idle. No other config switch. `voice.toggle off` clears voice mode → stop. Cutting TTS alone does not stop the listener while the session is still running (clarify wait).

**K2 is not materially wrong.** Phase 4 probe still required.

### 2. `voice.tts` path

- **Playback:** `_speak_text_with_barge` → `hermes_cli.voice.speak_text` → streaming or `_speak_whole_file` → `play_audio_file` (`voice_mode.py` L980+), which brackets `mark_audio_output_active` and uses system players including **`ffplay` as child of serve** (L1060). **`TtsPlaybackMonitor` should see it** (owned ffplay under serve pid).
- **`HERMES_VOICE_TTS`:** `_voice_tts_enabled()` (`methods_voice.py` L47–48) gates turn streaming TTS paths. The **`voice.tts` RPC itself (L765–775) does not check it** — it always starts `_speak_text_with_barge` and returns. Client must still refuse when local speech-off (K9).
- **Barge vs streaming TTS:** `_speak_text_with_barge` registers a stop/done pair in `_fd_speak_pipelines`, arms the barge listener (L262–279), and trip/`stop_playback` can cut it. It does not queue behind turn TTS; it is a parallel speak pipeline.
- **Return:** `_ok(rid, {"status": "speaking"})` immediately (L775); speak runs on a daemon thread.
- **End-of-playback event:** none on the wire. Release = monitor bout-stop (or estimate fallback).

### 3. Monitor forwarding

**Smallest PresenceView change:**  
- `PresenceAnimator`: re-raise `_playback.BoutStarted` / `BoutStopped` as public events; expose `bool PlaybackMonitorAvailable => _playback is { IsAvailable: true }`.  
- `PresenceView`: forward those events + property to `MainWindow` (same pattern as `AttachPlaybackMonitor`).  
- `MainWindow` → `VoiceController.NotePlaybackBoutStarted()` / `NotePlaybackReleased()` (names TBD).  
Threading: monitor already `Raise`s on the UI `DispatcherQueue` (`TtsPlaybackMonitor`).

**Availability:** `TtsPlaybackMonitor.IsAvailable` when `_comReady && _rootPid > 0` (L653–667); serve pid via `AttachPlaybackMonitor`; polling thread after `StartMonitoring`. **Important:** animator starts the monitor in `BeginSpeakingPipeline` when display enters **Speaking** (`PresenceAnimator` ~L448–449), not at window attach. Phase 5 must ensure question speech drives Speaking / starts monitoring (or rule 3 estimate applies). No new detection.

**Startup delay:** client poll ~50 ms at 20 Hz after owned ffplay appears; Hermes Edge synth latency dominates. Size Phase 5 rule-2 window as **`FirstSentenceLatencySeconds` (3.3) + margin** (propose +1.0 → **4.3 s**), measured live in Phase 5/smoke.

**Bout confusion:** turn streaming TTS can produce bouts. Identify the question bout as: **first bout that starts after `voice.tts` returns while no reply-speech bout is already active for this question token** (rule 1). If a prior reply bout is still active, wait for it to stop before arming question-bout association (or treat as unobservable → estimate). Probe/Phase 5 must log bout start times vs `voice.tts` return.

### 4. Capture attribution (K3)

Propose on `VoiceController`:
- Field `_clarifyCaptureId` (nullable `srq-*`) + generation; set when opening a clarify-answer `voice.record start`.
- Extend `TranscriptReady` to `Action<string text, string? boundClarifyId>?` (or a small args type): when the transcript ends **this** capture, raise with that id; clear the field.
- Barge-listener / wake / ordinary follow-up transcripts: raise with `boundClarifyId: null` → "other capture" under P4-D14.
- Gate drop / stop-phrase / no-speech / echo paths unchanged (no raise, or stop path before raise).

### 5. P4-D14 branch

**Current handler** (`MainWindow.xaml.cs` L179–188):

```csharp
_voice.TranscriptReady += text => Dispatch(() =>
{
    if (_voice.VoiceGated)
    {
        _voice.NoteGateRefusal(VoiceController.GateRefuseVoiceSubmitReason);
        return;
    }

    _ = SubmitTurnAsync(text);
});
```

**Proposed order after Phase 3:**
1. Gate refusal (unchanged).  
2. If `boundClarifyId` present: `GetState(id)==Open` → answer (single `AnswerClarify` / batch `FillFirstUnansweredBatchRow`); else drop + log `late_answer_dropped` + notice; **never** `SubmitTurnAsync`.  
3. Else if `HasOpenClarify(currentSession)` → answer `NewestOpenClarify(current)` the same way (**enabled on purpose for Phase 4 probe / Option D**).  
4. Else `SubmitTurnAsync(text)`.

**Stop phrase (K6):** in `VoiceController.OnVoiceTranscript` when `IsStopPhrase`: if MainWindow/broker reports open clarify for current session → `SkipClarify(id)` (call from MW on `VoiceChatEnded` or before, via a small VC→MW hook / MW listens and skips). Then existing `CancelFollowUp` + `VoiceChatEnded` + `ResyncAfterStopAsync`. Prefer: MW handles skip on stop by checking broker when receiving stop — but stop currently never raises `TranscriptReady`. Cleanest: VC raises a stop event or MW hooks `VoiceChatEnded` and if clarify open → `SkipClarify(NewestOpenClarify)`. Record: implement skip in MW on `VoiceChatEnded` when clarify open (K6), after verifying Hermes already ended voice chat.

### 6. Display (P4-D15)

**Voice-label priority today** (`ZolaDisplayState.Recompute` L187–217): unavailable → Text mode → `_streaming` Thinking → Speaking → Transcribing → Listening → Idle.  
**Mic line:** gated line **first** (L221–232) — locked / sleeping; then ungated branches.  
**"Waiting for your answer":** insert on voice-label path when `VoiceController.AwaitingAnswer`, **after** Text/unavailable checks, **before** Thinking — but **mic gated line still wins** (no change to mic priority). While awaiting, do not show Thinking for the open clarify wait (even if `_streaming`).  
**PresenceMode while awaiting:** `LISTENING` if `CaptureActive` (or listening recorder); else `IDLE`; **never THINKING**.  
**Stale clock:** today starts whenever `_streaming` (L157–165). While `AwaitingAnswer`, stop/reset clock each tick or don't start — no 120 s warn.  
**Authority:** `MainWindow` sets `VoiceController.SetAwaitingAnswer(bool)` from broker open-clarify-for-current; `ZolaDisplayState` reads only `_voice.AwaitingAnswer` (P3-D03).

### 7. Echo guard

`RememberSpokenEcho` / haystack (`VoiceController` L1371+); echo check only when `echoEligible = _followUpCaptureStarted || _followUpEchoPending` (L1104–1105).  
Spoken question must call `RememberSpokenEcho(spokenText)` (or shared helper) after `voice.tts`.  
Clarify-answer capture **must be echo-eligible** (set the same flags as follow-up, or a dedicated `_clarifyEchoPending`) so her question words are dropped.

### 8. Probe plan (Phase 4)

Non-interactive: build, spawn launch, Voice+speech on, reset P2-D13 via Text/Voice toggle.  
**P1/P2:** developer wake+clarify city prompt; card appears (not spoken); speak one city; wait 30 s. Cursor logs from `voice-timeline.log`, `server-requests.log`, Hermes `agent.log`/`gui.log`: `voice.interrupted` (+phase if present), transcript length, `answered … len=N`, `request.cancel`, clarify tool result, `tui turn finished status=…`, spoken reply?, SPEECH note on follow-up. Report Hermes vs client routing separately.  
**P3:** same clarify; type the city; say nothing — expect Track 2 complete path.  
Then options A–D decision block.

### 9. Flags

- No BLOCKED conflicts for Phase 3 routing build.  
- K2 → Phase 4 decision before Phase 5 speech/capture.  
- PresenceView forward + optional broker `SessionId` query flagged above.  
- Lore: P3-D23 control-input amendment deferred to Phase 4 lore closeout.

## Developer notes for Phase 5 (recorded 2026-09-30; apply in Phase 5)

1. **K4 correction:** `TtsPlaybackMonitor` is owned by `PresenceAnimator` (`AttachPlaybackMonitor` ~L90), not `PresenceView`. **Approved G-NOCHANGE exception:** thin additive pass-through in `PresenceAnimator` — re-raise `BoutStarted`/`BoutStopped` and expose monitor availability — no change to animator behaviour, mode logic, or when monitoring starts/stops. `PresenceView` forwards to `MainWindow`; one monitor only.

2. **Monitor runs only in the Speaking pipeline:** drive it by having `VoiceController` report question playback as speaking (`QuestionSpeaking` fact feeding the existing Speaking/display path) so the animator starts the monitor through its normal path. Hold `QuestionSpeaking` until the release rule fires (monitor release, else estimate per rules 2/3) — do **not** let the estimate drop Speaking while an observed bout is still running.

3. **Forced releases:** `TtsPlaybackMonitor.ForceInactiveLocked(reason)` produces a synthetic release (stop/pause/dispose/unbind). The forwarded bout-stopped must carry whether it was forced. A forced release is **never** a rule-1 release — treat as "playback unobservable" (rule 2 estimate) unless the pending-question token was invalidated, in which case abandon.

4. **K2 source result:** after a generation-phase barge trip, answering the clarify returns the tool but `begin_iteration` exits `interrupted_by_user`. **Option D is expected to fail;** Phase 4 probe confirms live.

## Phase 3 notes

**Before** (`MainWindow.xaml.cs`): gate → `SubmitTurnAsync` only.

**After:** `OnTranscriptReady(text, boundClarifyId)`:
1. Gate refuse
2. Bound id → Open? `ApplyVoiceClarifyAnswer` : late drop + dual log + notice (never submit)
3. Unbound + open clarify → `NewestOpenClarify` answer (enabled for Phase 4 probe / Option D)
4. Else `SubmitTurnAsync`

**VoiceController:** `TranscriptReady` is `Action<string, string?>`; `ArmClarifyAnswerCapture` + pending/active bind on successful `voice.record start`; stop → MW `SkipClarify` on `VoiceChatEnded`. No question speech this phase.

**Broker:** `NoteLateAnswerDropped` (length only). Batch voice = fill first unanswered row (K7).

## Phase 4 probe evidence

**Setup:** DEBUG spawn launch 09:51:29; wake armed; Text↔Voice toggle before P2; `voice.barge_in: true` (profile). Phase 3 unbound routing enabled. No question speech / no clarify-answer capture (Phase 5 not built).

### P1 (spoken city; card silent) — 2026-09-30

| Check | Result | Evidence |
|---|---|---|
| Card shown | yes | `srq-0e4569d8df37` received/shown **09:54:09** |
| City in card text box | yes (developer) | **"You answered: Seattle" after Send** — see dictation note below; **not** Zola |
| `voice.interrupted` (client timeline) | **no line** | `CancelFollowUp` only timelines when `_followUpArmed`; clarify wait had no follow-up → no cancel line even if event arrived |
| `voice.transcript` / Phase 3 `answered` | **no** | no `answered` until Skip (`text_or_len=skip` **09:57:13**) |
| Hermes FD WAV / transcribe | yes | WAV **09:54:57** (31.2 s audio); VAD removed ~26 s; `Transcribed … via local whisper` **09:54:58** |
| Barge `voice.transcript` destination | **nowhere on client** | `_deliver_fd_transcript` only emits when transcript strip non-empty; no client `voice.transcript` / no Phase 3 `answered`; empty/VAD-stripped result → no emit |
| `request.cancel` | no | — |
| Turn outcome on Skip | `interrupted_by_user` | agent **09:57:13.661**; gui `tui turn finished status=interrupted` **09:57:13.690** (191.4 s) |

### P2 (repeat spoken) — consistent

| Check | Result | Evidence |
|---|---|---|
| Card shown | yes | `srq-285b90666144` **09:58:44** |
| City in card text box | yes (developer) | same as P1 — **Windows dictation**, not Zola (see below) |
| `voice.interrupted` client timeline | **no line** | same as P1 |
| Hermes FD WAV / transcribe | yes | WAV **09:58:53** (~6.9 s); VAD removed most; transcribed **09:58:54**; **no** `_deliver_fd_transcript` / no client delivery |
| Broker `answered` while open | **no** | still open until P3 typed Send |

### P3 (typed Send; say nothing) — broker OK, turn interrupted

| Check | Result | Evidence |
|---|---|---|
| Typed answer via Track 2 | yes | `answered … text_or_len=8` **10:02:21.763** |
| Clarify tool completed | yes | agent `tool clarify completed` |
| Turn outcome | **interrupted** | `Turn ended: reason=interrupted_by_user` **10:02:21.796**; `tui turn finished status=interrupted` **10:02:21.837**; `response_len=0` |
| Reply spoken / city lunch | **no** | no reply |
| SPEECH note on follow-up | not probed | — |

### Developer observation — card text was Windows dictation (not Zola)

In P1/P2 the spoken city appeared in the card's text box and the developer pressed Send ("You answered: Seattle"). **No client code fills a single-clarify free-text box** (only `FillFirstUnansweredBatchRow` for batch). **No `voice.transcript` reached the client.** The text therefore came from **Windows dictation (Voice Access / voice typing)** into the focused field, not from Zola barge routing or Phase 3. The **`interrupted_by_user` outcome still stands**: Hermes's barge listener tripped on the same speech (FD WAV + whisper at the times above; `_fd_trip` → `agent.interrupt()` latch; INFO logs do not print the trip itself — those messages are `logger.debug`).

### `voice.interrupted` timestamps (P1/P2)

| What | Timestamp | Notes |
|---|---|---|
| P1 FD activity (proxy for trip) | **09:54:57–09:54:58** | WAV write + whisper; `_fd_trip` emit is DEBUG-only → **no INFO `voice.interrupted` line in agent/gui** |
| P1 client `voice.interrupted` | **not logged** | absent from `voice-timeline.log` (and no other client log hit) |
| P1 turn end (Skip) | **09:57:13.661** | `interrupted_by_user` (latch already set earlier) |
| P2 FD activity (proxy) | **09:58:53–09:58:54** | same pattern |
| P2 client `voice.interrupted` | **not logged** | absent |
| P3 turn end (typed answer) | **10:02:21.796** | `interrupted_by_user` after clarify tool returned |

### Where the barge transcript went

Hermes full-duplex path: trip → cut TTS / `agent.interrupt()` (generation) → emit `voice.interrupted` → then `transcribe_recording(wav)` → if non-empty, `_deliver_fd_transcript` → `voice.transcript` on the wire. For P1/P2: transcription ran, but **no non-empty transcript was delivered to the client** (VAD removed most of the clip / empty strip). So the barge listener **heard and transcribed**, latched interrupt, and **dropped the transcript before client delivery**.

### Measured (one paragraph)

With `barge_in: true`, speaking a city while a clarify card is open does **not** produce a client `voice.transcript` or broker `answered` (P1/P2). Hermes's FD listener still records/transcribes during the wait and latches `interrupted_by_user`, but empty/VAD-stripped transcripts never reach `_deliver_fd_transcript`. City text in the card box was **Windows dictation**, not Zola. Typing Send answers the clarify (`answered len=8`), but the turn still exits `interrupted_by_user` with no reply.

### Cursor's read of the evidence

- **Option D — not viable.** No delivered barge transcript for routing; even if one arrived, source + live show `interrupted_by_user` after answer.  
- **Option A — supported.** Need our own capture after speech; barge-in off removes the FD latch that poisons the turn.  
- **Option B — supported.** Speak question, typed/click answers only; keeps barge for reply cut-in but avoids answer-via-barge.  
- **Option C — unsupported / not recommended without more proof.** Probe did not show clean post-answer reply under barge; toggle races unmeasured.

### Decision (2026-09-30)

**Option A chosen** — profile `voice.barge_in: false` (P4-D25), then client speak + clarify-answer capture per P4-D13/D14.

### Smoke amendments (from Option A)

- **C11 becomes:** talk over a long reply → she is **NOT** interrupted (barge-in intentionally off); **Cancel** still stops her.
- **Precondition:** Windows dictation (Voice Access / voice typing) is **off** during Phase 7, so the only voice path is Zola's.

## Phase 5 notes

### Profile apply (2026-09-30) — `voice.barge_in: false`

- **Backup:** `config.yaml.bak-P4-ASK-20260930-102716`
- **Live:** `barge_in: false` (diff vs backup: that line only)
- **VOICE_CONFIG.md:** recorded (key/value/date/`P4-D25`/Option A/backup/developer-approved)
- **Serve restart:** not strictly required for next arm (mtime-cached `_voice_cfg_dict`); already-running FD listener not stopped by flip. **Recommend restart** before smoke; spawn launch gets a fresh serve.

### Speak / listen (Option A)

- **`SpeakQuestionAsync`:** refuse gated / Text / speech-off; build spoken text (**question only** — never choices; batch first + "…more on screen" when more rows); `voice.tts`; echo haystack = spoken text only; `question_spoken id=… chars=N` (= question length); hold `QuestionSpeaking`→`Speaking` so animator starts the monitor.
- **P4-D13 amend (developer 2026-09-30, lore closeout):** spoken "Options: A, B, or C" form too formal. Speak question text ONLY for single and multi-select; choice buttons on the card unchanged. Removed `SpokenOptions*` / `AppendSpokenChoices`. C1 functionally PASS before amend; re-C1 confirms question-only speech, then continue C2+.
- **Track 5 note (progress only — P4-D20 speech shaping):** In voice conversation, ask open questions plainly; don't offer suggested answers unless the user needs to pick from a real list.
- **Track 5 note (progress only — P4-D20, developer 2026-09-30 after C3):** On clarify skip / spoken "stop", her follow-up must stay conversational (e.g. "Got it" / "I understand — maybe we can pick this up later"), not clinical ("You didn't provide one"). Skip routing itself is client-correct (`answered … skip`); wording is Hermes reply shaping, out of P4-ASK scope.
- **Release rules** (`WaitForQuestionReleaseThenCaptureAsync`): monitor bout stop = authoritative (never timer while bout active); no bout in `FirstSentenceLatency+1.0` (4.3 s) → estimate; monitor unavailable → estimate; forced bout-stop → estimate (never rule-1). Log `question_release rule=…`.
- **Rule-1 race fix (2026-09-30 review):** `_questionBoutStoppedTcs` is created at arm with `_questionBoutStartedTcs` (never null while token current); `NotePlaybackBoutStarted` only signals started (does not recreate stopped TCS). Once bout started, exits are natural stop / forced estimate / invalidation only — no null→estimate timer path.
- **Pending token invalidation:** request closed, session change, unreachable, Text mode, voice gated, newer clarify, tts failed. Log `question_abandoned`. Abandon does not stop TTS.
- **Pre-capture recheck:** token current; `GetState==Open`; session matches; not gated; Voice mode; speech on. Else skip + log; no submit.
- **Capture:** `ArmClarifyAnswerCapture` + follow-up path with echo eligible; Phase 3 routing answers.
- **Monitor forward:** `PresenceAnimator` re-raises `PlaybackBoutStarted` / `PlaybackBoutStopped(forced)`; `PresenceView` exposes; MainWindow → `NotePlaybackBout*`. One monitor only.
- **Broker:** `ClarifyView.SessionId` + `TryGetSessionId` (read-only).
- **MainWindow:** speak once per id after card Open (`_spokenClarifyIds`); re-shows stay silent.
- **Build:** pass.

### Quoted — release rules / token / recheck / monitor

**Arm (both TCS):**

```480:488:windows-client/Zola.Client/VoiceController.cs
    private void ArmQuestionBoutWait()
    {
        _questionBoutArmed = true;
        _questionBoutStarted = false;
        _questionBoutActive = false;
        // P4-ASK: both TCS live for the token lifetime so rule-1 never races a null stopped wait — P4-D13
        _questionBoutStartedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        _questionBoutStoppedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
    }
```

**OnPlaybackBoutStarted (no recreate):**

```370:381:windows-client/Zola.Client/VoiceController.cs
    public void NotePlaybackBoutStarted()
    {
        if (!_questionBoutArmed)
        {
            return;
        }

        _questionBoutStarted = true;
        _questionBoutActive = true;
        // P4-ASK: stopped TCS was created at arm; do not recreate (waiter may already be awaiting it) — P4-D13
        _questionBoutStartedTcs?.TrySetResult(true);
    }
```

**Rule-1 wait (startup winner)** — await stopped only; no null→estimate:

```614:658:windows-client/Zola.Client/VoiceController.cs
                if (winner == startedWait && _questionBoutStarted)
                {
                    // P4-ASK: rule 1 — bout started; exits are natural stop, forced estimate, or invalidation only — P4-D13
                    var stoppedTcs = _questionBoutStoppedTcs
                        ?? throw new InvalidOperationException("question bout stopped TCS missing while bout started");
                    bool forced;
                    try
                    {
                        forced = await stoppedTcs.Task.ConfigureAwait(false);
                    }
                    // ... natural → rule=monitor; forced → forced_release_estimate; cancel → return
                }
```

**Rule-1 wait (late bout inside rule-2 estimate):**

```678:719:windows-client/Zola.Client/VoiceController.cs
                        if (_questionBoutStarted)
                        {
                            // P4-ASK: late bout → rule 1; wait for stop (never timer while active) — P4-D13
                            var stoppedTcs = _questionBoutStoppedTcs
                                ?? throw new InvalidOperationException("question bout stopped TCS missing while bout started");
                            bool forced;
                            try
                            {
                                forced = await stoppedTcs.Task.ConfigureAwait(false);
                            }
                            // ... same exits; never break without awaiting stop
                        }
```

Invalidation — `AbandonPendingQuestion` / `AbandonPendingQuestionIfId` from gate close, Text mode, `RequestClosed`, `ClearTranscript` (session_change), `ShowUnreachable`.

Pre-capture — `OpenClarifyAnswerCaptureAsync` + `ConfigureQuestionSpeech` callback (`GetState` + `TryGetSessionId`).

Monitor — `PresenceAnimator.PlaybackBoutStarted` / `PlaybackBoutStopped(bool forced)`; `_forwardForcedBoutStop` before `StopMonitoring`.

### Done checklist

- [x] One spoken question per clarify id; re-shows don't speak; gated / Text / speech-off refuse
- [x] Three release rules; pending-token invalidation; pre-capture recheck
- [x] Monitor forwarding additive (`PresenceAnimator` + `PresenceView`)
- [x] Build passes
- [x] Option A profile `barge_in: false` + `VOICE_CONFIG.md`

## Phase 6 notes

### Before (voice-label priority)

unavailable(+details) → Text mode → **Thinking** (`_streaming`) → Speaking → Transcribing → Listening → Idle

### After (voice-label priority)

unavailable(+details) → Text mode → **Waiting for your answer** (`AwaitingAnswer`) → Thinking → Speaking → Transcribing → Listening → Idle

Mic gated line unchanged (still first). No new `PresenceMode` value.

### Presence while awaiting

Speaking still wins (question TTS / monitor). Else: capture/listening/transcribing → `Listening`; else `Idle`. **Never `Thinking`** while `AwaitingAnswer`.

### Wiring

- `VoiceController.AwaitingAnswer` + `SetAwaitingAnswer` (raises `StateChanged`)
- `MainWindow.UpdateChrome`: `SetAwaitingAnswer(!_unreachable && HasOpenClarify(current))`
- Stale timer: stopped while awaiting; tick resets activity; no 120 s warn during wait

### Done checklist

- [x] Priority chain quoted before and after
- [x] No new `PresenceMode` value
- [x] Build passes

## Smoke evidence tables

### Part A (CURSOR-RUN) — 2026-09-30

- Build: pass (`Debug` / `win-x64`)
- hermes-agent: clean at `345cd2b057a452236de401d3534b8502a7465e8d`
- Live profile: `voice.barge_in: false`
- Spawn launch: client PID 5000; serve parent = client (SPAWNED) at **2026-09-30T10:45:15-07:00**
- Log watermark: `$env:TEMP\p4ask-smoke-watermark.json`
- Preconditions noted: Windows dictation OFF; C11 = not interrupted when talking over reply (Option A); Cancel still stops
- G-ONE-AUTHORITY:
  - one `TranscriptReady` handler (`MainWindow` L201 → `OnTranscriptReady`)
  - `SubmitTurnAsync` from transcript only in no-clarify branch (`OnTranscriptReady` L590 after bound/unbound clarify branches)
  - `voice.tts` only via `VoiceController.MethodTts` / `SpeakQuestionAsync`
  - one `new TtsPlaybackMonitor(` (`PresenceAnimator` L103)
  - no new `session.interrupt` in ASK path (Cancel still uses existing ChatSocket path; gate close never interrupts)
- Constant: `WaitingForAnswerLabel = "Waiting for your answer"`

### Part B interactive

| # | Result | Evidence |
|---|---|---|
| C1 | **PASS** (retry 3, ~10:58) | `question_spoken` → `rule=monitor` → `answered … len=8`; clarify completed; turn `status=complete`; Seattle lunch reply. **Functionally PASS recorded before speak-amend.** |
| C1 reconfirm | **PASS** (~11:12) | `srq-0d50321258f0`; `chars=22` (was ~87 with Options); monitor release; answered len=15; Seattle lunch search; turn `status=complete` |
| C2 | **PASS** (~11:19) | `srq-524965009422`; `chars=23` (question only); monitor; answered len=6 by voice; clarify completed; turn `status=complete` + Edge TTS reply |
| C3 | **PASS** (~11:24) | `srq-4ed468e7b1b8`; `answered … skip`; clarify completed; turn `status=complete`; wake.resume (follow-up-end / capture-idle) |
| C4 | **PASS** (retry, ~11:36) | Cancel → `cancelled … interrupted`; late speech → `late_answer_dropped id=srq-0c2ab0f167d2 len=1` (timeline + server-requests); no `prompt.accept` for that utterance |
| C5 | **PASS** (~11:39) | `srq-6829c48505f6` shown; no `answered`; release + capture idle; HUD `Waiting for your answer`; no self-answer |
| C5b | **PASS** (~11:46) | `srq-3e086e7d38c3`; `question_abandoned … reason=request_closed` mid-speak; `cancelled … interrupted`; no release/capture for that id. Note: first season wake was wrongly `late_answer_dropped` vs prior C5 id — fixed stash-only-on-interrupt + clear on wake capture. |
| C5c | **PASS** (~11:54) | `srq-5b8f7958ef90 chars=456`; `question_release rule=monitor` (~29s bout); Hermes `Voice recording started` 0.6s after release; answered; turn complete |
| C6 | **PASS** (from C5/C5c) | HUD `Waiting for your answer`; presence `Listening` during answer capture then `Idle`; no `stale` lines in display-state today |
| C7 | **PASS** (~11:57) | `srq-dde41812a75e`; gate close on lock (record stop + toggle off + wake.stop); unlock restore; typed `answered … len=5`; turn complete; no voice answer while locked |
| C8 | **PASS** (~12:00) | `srq-6db56135b058 chars=52` (first Q + more-on-screen); voice transcript ~11:59:48 then `answered … len=18` only at 12:00:10 (fill-only then on-screen complete); turn complete |
| C9 | **PASS** (~12:02) | `srq-326f084ca306` shown + typed `answered … len=4`; **no** `question_spoken`; turn `status=complete` |
| C10 | **PASS** (~12:03) | wake → `What time is it?` → `status=complete` + Edge TTS; server-requests empty (no clarify) |
| C11 | **PASS** (talk-over + C11b) | Talk-over: `status=complete` (not barge-cut). Cancel while streaming: `status=interrupted` / `interrupted_during_api_call` + `Audio playback interrupted` (~13:49:34). Note: Cancel is streaming-only; post-complete TTS has no Cancel (Text toggle stopped that case earlier). |
| C12 | **PASS** (~13:51) | `srq-4b879f85bfab` approval shown; `answered … deny`; **no** `question_spoken`; probe file absent; turn `status=complete` |

### Part C (CURSOR-RUN) — 2026-09-30

- Privacy: no smoke answer words (Seattle / Mars / apple / etc.) in `server-requests.log`, `voice-timeline.log`, or `display-state.log`; answers logged as `text_or_len=N` / `skip` / `deny` only.
- P2-D13: no self-interrupt / “Voice paused” trips in `voice-timeline.log` during this smoke.
- Live profile: `voice.barge_in: false` (unchanged).

**C1 FAIL (2026-09-30 ~10:47):** natural bout mislabeled `forced_release_estimate` (stale flag); capture late; answer discarded too-quiet. Fixed forced-flag.
**C1 FAIL retry (2026-09-30 ~10:52):**
- Release: `rule=monitor` ✓; capture opened; Hermes transcribed 3.1s answer; client `voice.transcript`
- **No `answered`** until Skip at 10:54:38 — Seattle appeared in the card text box only
- Root cause: Hermes always wires clarify as `questions[]` → client `IsBatch=true` → voice path only `FillFirstUnansweredBatchRow` (K7) and **never submitted**
- **Fix:** after fill, if no unanswered rows remain (one-question batch), `AnswerBatch` automatically. Multi-question still fill-only until complete (C8).

**C1 PASS (2026-09-30 ~10:58):** `srq-eae58cd67154`; monitor release; answered len=8; turn complete + spoken lunch reply.

**P4-D13 speak-amend (developer 2026-09-30):** speak question only (no Options template); rebuild + re-C1, then C2 with free-form voice answer.