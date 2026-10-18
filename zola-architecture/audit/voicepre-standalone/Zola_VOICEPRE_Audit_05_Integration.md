# VOICEPRE Audit 05 — Authority and proactive integration

P7 admission is on committed `main` (`TranscriptAdmission.cs` hash matches). P9 speech is overlay-only and still in smoke. Findings about P9 say so. Hermes reasoning, tools, and memory stay where they are; this audit does not redesign them.

## 1. Behavior by state

Facts for proactive speech are assembled in the overlay `MainWindow` and denied in `ProactiveDeliveryCoordinator.LocalGate` (`ProactiveDeliveryCoordinator.cs` L454–502). Transcript admission is a different function (`TranscriptAdmission.Decide`).

| State | Capture / admit | Speech out | Proactive claim (overlay) |
|---|---|---|---|
| Idle, Voice, resting | Wake armed. No STT. | Silent until a turn. | Allowed only if also idle 20 s, quiet hours clear, and the later snapshot gates pass (`Idle` L510–524, `IdleSeconds` = 20). |
| Generating | No new unbound voice capture (`P7-D04`). | TTS may start per sentence before the turn ends. | Deny `turn`. |
| Reply playback | Follow-up not opened while the bout is active (`P7-D06`). | ffplay per sentence. | Deny `playback` (`Speaking`). |
| Question playback | Capture waits until the question bout ends. Stop speaking is refused while `QuestionSpeaking` (`VoiceController` stop path). | Question text via `voice.tts`. | Deny `clarify` (`AwaitingAnswer` or `QuestionSpeaking`). |
| Awaiting clarification | Only the bound capture may answer (`P7-D05`). | She has asked. | Deny `clarify`. |
| Awaiting send approval | Typed/voice passphrase is the P8 send gate, not this capture. | Unrelated. | Snapshot `reviewed_draft` denies. A voice interrupt must not be treated as a decision on the draft. |
| Proactive playback | `SpeechEchoGuard` refuses a non-PTT capture during the line and for 2 s (`SpeechEchoGuard.cs` L64–88). | `voice.tts` of a fixed line. No follow-up is armed (progress D7). | One reservation. |
| Text / muted | Wake and capture refused. | TTS off for the mode. | Deny `text_mode`. |
| Locked / suspended | `P4-D02`: pause, stop, cancel, refuse. | Cut. Not resumed. | Deny `locked` / `suspended`. |
| Disconnected | Epoch guard drops stale transcripts (`VoiceController.cs` L2299–2303). | Outage forces the monitor inactive. | Deny `backend_down`. |
| Recovering | No admit until a new Accepting capture. Recovery timeouts never admit (`P7-D03`). | Hermes TTS lease is whatever the new process loaded. | `proactive.recover` once; failure denies. Uncertain rows are not spoken again. |

## 2. Stop sound, cancel generation, cancel a tool

| Gesture | Sound | Model turn | Tools / external effects |
|---|---|---|---|
| Stop speaking (`P4-D29`) | `voice.toggle off` then `on`, which calls `_tts_stream_stop(user_barge=False)` and `stop_playback`. Follow-up capture is invalidated first. | Not interrupted. | Not recalled. |
| Cancel | Separate `session.interrupt`. | Interrupted. | A tool that already ran (a sent draft, a write) is not undone. `S21`: typed Cancel during speech can still latch Hermes's interrupted note. |
| Barge `_fd_trip`, if it were on | Cuts TTS. Interrupts **all** running agents only in the generation phase (`methods_voice.py` L237–243). | Sometimes. | Same: no rollback. |
| Lock gate | Stops speech without the interrupt latch (`P4-D02`). | The turn is not cancelled by the audio gate. | Unchanged. |

An audio interruption is not a recall of a send. `P8` sends that have left the machine stay sent. Ambient speech must not be wired to those gates.

## 3. Ids and the single admission authority

| Id | Who mints it | What breaks without it |
|---|---|---|
| Client capture generation | `CaptureLifecycle` | Late transcripts cannot be tied to a dead capture. Hermes does not send one (`S53`). |
| Clarify request id | Server-request broker, copied onto the clarify capture | `P7-D05` would fall back to "newest question", which was removed. |
| Connection epoch | Chat socket | A transcript from the previous serve could be admitted (`P9-SUPERVISE` guard). |
| Session id | Hermes session on the socket | A foreign session's words would submit here. |
| Proactive `attempt_id` | Store, purpose `speech` | A late outcome could close the wrong row. Overlay only. |

**VOICEPRE-AUD-03** [MATCH] — `P7-D01`. `TranscriptAdmission.Decide` is the only admit/drop of a voice transcript. `MainWindow` does not re-decide. Echo can reject only. The overlay adds a **second** authority for unprompted speech (`ProactiveDeliveryCoordinator`), which does not admit user transcripts. That split is correct as long as continuous listening does not start calling `prompt.submit` from the proactive poller.

## 4. Continuous capture versus the P9 "no capture" gate

[CODE] Overlay `LocalGate` (`ProactiveDeliveryCoordinator.cs` L476–478):

```
if (facts.Capture)
    return ReasonCapture;
```

`Capture` is `CaptureActive`, which is true from a successful `voice.record` until recorder `idle` (`VoiceController.OnVoiceStatus` L2263–2281). A mic that never closes would deny every proactive line.

**VOICEPRE-AUD-13** [RISK] MEDIUM — `P9` single-delivery rule, SYM-04. The gate is doing two jobs: "Brian is in a turn" and "the mic happens to be open." Deleting it would let a proactive line start over him. Keeping it unchanged makes wake-free listening and proactive speech mutually exclusive. The replacement has to be "active user speech or an open turn," not "a stream exists." This code is uncommitted. Committed `main` has no coordinator, so the conflict appears when P9-SPEAK lands, not before.

Idle stamps (composer, wake, PTT, submit, turn, bout stop) already hold proactive speech for 20 s. Those should stay. They are not a substitute for the capture split above.

## 5. Autonomous speech and echo

Overlay path: claim → `speech_started` → revalidate → `voice.tts` → wait for a bout → `delivered` only on a clean end. Forced stop, missing monitor, no bout in 15 s, no clean end in 60 s, or a second bout become `delivery_uncertain` and are not retried as speech (progress G-PENDING-OUTCOME; `SpeechConstants` L9–10, L15). `speak_enabled` was left true during an unfinished smoke. That is an operational fact, not a design change.

She does not open a follow-up after a proactive line. The echo guard is the exact phrase plus a 2 s tail. A continuous recognizer that stays in Accepting would still need the P7 echo rule, because the 2 s tail is shorter than a slow Deepgram sentence and does not cover her reply voice.

Forced stop, uncertain delivery, retry of the **store** call, and recover-on-startup are already specified. A new audio owner has to keep those outcomes, or a killed player will be stored as `delivered`.

## 6. Avatar, HUD, health

`TtsPlaybackMonitor` is the mouth and the follow-up clock. It believes Hermes-owned **ffplay**. A client player, a WASAPI render stream, or sounddevice playback will not create those sessions.

| Surface | If audio ownership moves |
|---|---|
| Mouth / lip timing | Needs a new "audible now" signal from the real player. Segment boundaries would be PCM or buffer underruns, not process exit. |
| Follow-up release | Must use that same signal. Leaving the ffplay monitor in place would open the mic at the wrong time. |
| Proactive delivered vs uncertain | `NotePlayback` treats a clean bout stop as completion. A different player without a forced-release flag will mark cut-off speech as delivered (`S70` gets worse). |
| HUD Voice row | Overlay reads mode, wake, speaking, and TTS restore from the voice controller. It does not name the provider. A helper crash has to show unavailable, not "ready". |
| Health | Watcher health is a separate poll. It does not prove the mic is open. |

## 7. Decision impact

| Decision | If A (config only) | If B (Hermes voice patch) | If C (Zola-owned audio) | Invariant to keep | Rollback |
|---|---|---|---|---|---|
| C3 / P2-D01 | No amendment. Does not meet the request. | Device handle stays in serve. Amendment only if the patch is allowed despite `P2-D10` ("Hermes source is never edited") and the `S56` no-fork preference. | **Amendment required.** Name the new owner (client or helper) and how Hermes is stopped from opening the mic. | One owner. No second `sounddevice` stream. | Config flag back to Hermes capture; helper not started. |
| P4-D28 / P5-D08 | Stays false. | Replace "barge_in false" with a state-aware listener: trip on reply playback, do not trip on an open clarify, do not latch `voice.interrupted` for an answer. | The Hermes flag stays false so the old listener cannot also run. | Spoken clarify is not an interruption. | Flag false and the old client. |
| P7-D01–D05 | Unchanged, and they reject a barge transcript. | Add a capture kind for an interrupting utterance that is admitted **after** the turn is cancelled, still one authority. | Same authority. The helper emits candidates; the client still decides. | Cancelled and unbound transcripts stay dropped. | Old `Decide` order. |
| P7-D06 / P4-D18 | Unchanged. | Pre-roll on `voice.record` does not remove the monitor. | Monitor must follow the new player or the first-word fix regresses. | Do not listen on an estimate while audio is active. | Old ffplay monitor. |
| P7-D07 | Unchanged. | Still defense only. | Still defense only. Acoustic rejection is extra, not a new admit rule. | Echo never admits. | — |
| P4-D02 / P4-D07 | Unchanged. | A patch must not resume wake over an in-flight stop (`S52`). | Lock and Text must close the helper stream. Voice does not approve commands. | Fail closed. No voice approval of tools. | Helper exits on lock. |
| P9 delivery (not locked in `DESIGN_DECISIONS.md`; build-plan track, uncommitted) | N/A | Capture-active must be split before anyone turns on a long-lived record. | Same split, and `delivered` must mean the new player finished. | One unprompted speaker. Uncertain is not retried as speech. | `speak_enabled` false. |
| S19 / §12 | Still deferred. | A patch that only adds barge-in does **not** implement this. | Still needs an explicit attention state. Owning the mic does not decide the addressee. | Ambient text is not a turn, a memory, or a send. | Ambient state discards. |

No amendment is made by this audit.
