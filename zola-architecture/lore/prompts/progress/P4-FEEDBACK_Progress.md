# P4-FEEDBACK Progress — She Never Looks Stuck (+ Stop Speaking)

## Branch

- Branch: `p4-feedback`
- Base commit SHA (`main` HEAD at branch): `c0c678a957026d6cdbc55d7cbd1eb4b398c8108d` (`docs: record P4-ASK merge SHA`)
- Plan on `main`: `PHASE4_BUILD_PLAN.md` v1.1 — SHA-256 `d98b3e6c87457266c8c2d06fc57a771cb1c56977790198fa2020429a5216616e` (54,285 bytes; verified matched; not re-committed)
- Prompt version: 1.1 (2026-09-30)
- Hermes HEAD verified Phase 1–2: `345cd2b057a452236de401d3534b8502a7465e8d` (clean)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Tool Activity Line and Notices (`P4-D16`, `P4-D17`) | COMPLETE |
| 4 | Build: Stop Speaking, Closed-Id Fix, Transcript Logging (K1–K3) | COMPLETE |
| 5 | AUD-37 Reproduction (`P4-D18`) | COMPLETE — reproduced; fixed (monitor + seed + 0.5 s quiet) |
| 6 | Smoke Test | COMPLETE |
| 7 | Closeout | COMPLETE |

## Closeout SHAs

- Implementation commit: `5c3197ed0b7f16ac75c95ccb12dc04bac0a2a290` (`feat(P4-FEEDBACK): tool activity, visible notices, stop speaking — P4-D16..D18`)
- Merge commit: `044df5e3ab6ec7d6393e0ebfa915583782177c3c` (`Merge branch 'p4-feedback'`)
- Docs merge-SHA commit: *(pending 7h)*
- Hermes HEAD at closeout: `345cd2b057a452236de401d3534b8502a7465e8d` (clean)

## Guardrails summary

- **G-SCOPE:** `ChatSocket.cs`, `ZolaDisplayState.cs`, `MainWindow.xaml` / `.xaml.cs`, `VoiceController.cs`, optional `Themes/ZolaTokens.xaml` (flag first), live profile / `VOICE_CONFIG.md` only for an approved AUD-37 config fix, and this progress doc.
- **G-ARCH:** Build plan + K1–K3 are truth; stop and flag conflicts.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No `ServerRequestBroker.cs`; no `Presence/*` (including `TtsPlaybackMonitor` / `PresenceAnimator`); no `SessionLockWatcher`; no process/session managers; no `App.xaml(.cs)` / csproj; no `SOUL.md`; no hermes-agent edits; no profile keys except approved AUD-37.
- **G-COMMENT:** `// P4-FEEDBACK: [rationale] — P4-D1X` (K1 → `— P4-FB-STOP`, K2 → `— P4-D14`, K3 → `— P4-D18`).
- **G-STOP / G-CLOSEOUT:** Stop after each phase; closeout only on “proceed to closeout”.
- **G-LORE-SCOPE:** No lore updates this track (including closeout).
- **G-ONE-AUTHORITY:** `ZolaDisplayState` sole display authority; `VoiceController` sole `voice.*` / `wake.*`; Stop through Track 1 serialized gate worker; never `session.interrupt` / `voice.toggle tts` for Stop.
- **G-FAIL-CLOSED:** Missed `tool.complete` must not leave a stale activity line; Stop failure → availability same or quieter.
- **G-CONST / G-DEPS / G-PRIVACY:** Named constants; no installs; transcript logs length + `filtered` only (never text).

## Developer additions (K1–K3, verbatim from prompt)

### K1: Developer addition — "Stop speaking" control (on-screen only). Recorded for lore as a P4-D29 candidate.

*Why:* with `voice.barge_in: false`, talking over her no longer stops her. Cancel is shown only while the turn is streaming (`_streaming`). After `message.complete` she can still be **speaking** the reply through Hermes TTS, and there is no way to stop her except switching to Text mode (the `P4-ASK` C11 finding).

*Behaviour:*

- A **Stop** control is visible and enabled whenever she is speaking and not gated. That includes the spoken clarify question (`QuestionSpeaking`) and the reply after completion. Phase 2 proposes the exact "speaking" fact:
  - the `P2-D15` estimate (`Speaking`), OR'd with an active playback bout if that can be read without touching `Presence/*`;
  - prefer the existing `VoiceController` facts.
- It also has a keyboard shortcut (Phase 2 proposes one that is unused and not a text-editing key, e.g. `Esc` if free, when the composer has no focus or is empty).
- **While the turn is still streaming**, the existing **Cancel** keeps its meaning (it interrupts the turn). Phase 2 proposes whether Stop and Cancel are one dock button with two states or two controls. Either way:
  - Cancel = end the turn (existing behaviour, unchanged);
  - Stop = stop the voice only; the turn and its text are unaffected.
- **Action** (`VoiceController.StopSpeakingAsync`), through the Track 1 serialized worker:
  - stop current speech with **no S21 latch and no turn interrupt**, using the same `voice.toggle off` path the gate close uses;
  - then restore **exactly the prior availability**: voice mode on, and speech output on if it was on (`P2-D03`: read status, flip only if needed);
  - wake stays as it was (report whether `voice.toggle off` touches wake or capture);
  - cancel any pending follow-up (after Stop, she does not auto-listen; "Hey Zola" or the mic button works);
  - log every step.
- **Stop during the spoken clarify question:** her speech stops. Because the ffplay session ends, the monitor should release naturally, and the answer capture opens (rule 1) — "I heard you, go ahead". The token is **not** abandoned by Stop. Phase 2 confirms from `voice.toggle off` source that this release is natural, not forced. If `voice.toggle off` ends or blocks the capture path, report it.
- Refused while gated (the gate already silenced her). No-op if she isn't speaking.
- Never spoken, never voice-triggered (on-screen only; developer decision).

### K2: Developer addition — closed-clarify-id fix (`P4-ASK` review finding).

- `VoiceController._closedClarifyCaptureId` is stashed when a clarify-answer capture is cancelled, so a late answer gets dropped. It is cleared on a new question, on a new wake or mic capture, and when a transcript consumes it. **It is not cleared when a typed prompt starts a new turn.**
- Failing sequence:
  1. Cancel during the answer capture, and say nothing.
  2. Type a new prompt.
  3. Her reply finishes, and the follow-up capture opens.
  4. The spoken follow-up is bound to the stale closed id and dropped as a late answer.
- **Fix:** clear it in `OnTurnStarted` (any new turn, typed or voice), in addition to the existing clears.
- Keep the C4 late-drop behaviour: a transcript arriving **before** any new turn starts is still dropped.

### K3: P4-D18 transcript logging (already in the plan; restated). Log every `voice.transcript` the client receives to `voice-timeline.log`:

- length, `filtered` flag, stop-phrase / no-speech flags;
- capture window (start, stop, duration);
- whether it was bound (the `srq-*` id) or unbound;
- **never text**.

This includes transcripts with no client-opened capture. With barge-in off there should be none; report it if any appear. The `P4-ASK` probe was weakened by this log missing.

## Document of Truth (Phase 1 read)

- Plan Track 4 + P4-D16/D17/D18 + Visibility grounding (AUD-37/38/39) — read.
- Prior progress: `P4-LOCK`, `P4-REQUEST`, `P4-ASK` — present on `main`.
- Lore (`ROADMAP`, `DESIGN_DECISIONS`, `OPEN_QUESTIONS`) and audits 02/05 — present; spot-checked for AUD-37/38/39 and visibility. Full Phase 2 file reads still required before build.

## Live profile facts (Tracks 2–3; read-only this track unless AUD-37 fix)

- `agent.clarify_timeout: 300`
- `approvals.mode: manual`
- `voice.barge_in: false` (P4-ASK Option A)

## Phase 2 understanding report

Hermes clean at `345cd2b057a452236de401d3534b8502a7465e8d` (Phase 2 start). Client files read in full: `ChatSocket.cs`, `ZolaDisplayState.cs`, `MainWindow.xaml(.cs)`, `VoiceController.cs`, `Themes/ZolaTokens.xaml`. Hermes read-only: `events.py`, `tool_progress.py`, `methods_voice.py`, `voice_mode.py`, `hermes_cli/voice.py`, `config_defaults.py`, `prompt_turn.py`, `tts_tool_speaker.py`, `agent_callbacks.py`.

### 1. Tool events (K5)

**Contracts** (`tui_gateway/contracts/events.py`):
- `tool.start` → `ToolStartPayload`: **`tool_id: str`**, `name`, optional `context` / `args` / `args_text` / `preview` (~L237–250).
- `tool.complete` → `ToolCompletePayload`: **`tool_id: str`**, `name`, `duration_s`, `summary`, … (~L253–268).
- `tool.generating` → `ToolGeneratingPayload`: **`name` only — no `tool_id`** (~L271–277).
- `tool.output_risk` → includes `tool_id`, `name`, `risk`, `findings`, `redacted` (~L280+).

**Emitter** (`tool_progress.py`):
- `_on_tool_start` / `_on_tool_complete` use the same `tool_call_id` as `tool_id` (~L232–258) → **stable start→complete**.
- Nested/subagent: lifecycle comments reference `_mirror_subagent_to_child`; subagent progress uses `subagent.*` events (`_progress_subagent` ~L375+), not parent `tool.start/complete` on the TUI socket for child tools as the primary path. Parent-session tools on this socket are the agent’s own `tool.*` rows. Treat nested subagent tools as **not** reliable `tool.start/complete` on the Zola session socket unless mirrored; Phase 3 keys only what arrives with `tool_id`.

**`tool.generating`:** emitted from `agent_callbacks` as `_emit("tool.generating", sid, {"name": name})` (~L94) — provisional hint only (K5 invariant).

**Friendly-name map (named table for Phase 3):** tools seen in live zola agent log + plan:

| Hermes `name` | Display |
|---|---|
| `web_search` | Searching the web… |
| `terminal` | Running a command… |
| `skill_view` | Checking a skill… |
| `skills_list` | Checking skills… |
| `skill_manage` | Managing a skill… |
| `clarify` | *(no line — card shows)* |
| *(unknown)* | Working… |

**Client today:** `ChatSocket.DispatchEvent` drops all `tool.*` via `default:` (~L672–674) — AUD-38.

### 2. Display (P4-D16)

**Voice-label priority today** (`ZolaDisplayState` ~L212–247):
unavailable(+details) → Text mode → **Waiting for your answer** (`AwaitingAnswer`) → Thinking (`_streaming`) → Speaking → Transcribing → Listening → Idle.

**HUD:** `MainWindow.ApplyVoiceChrome` → `VoiceStateText` = voice label (~L650). **No separate activity string yet.**

**Live bubble:** `OnMessageStarted` creates/clears `_live`; `OnMessageDelta` appends to `_live.Body.Text` (~L728–771). Empty bubble exists while Thinking with no deltas — activity line will render there until first non-empty text (clear on first delta / non-empty body).

**Clear-all hooks to wire (Phase 3):** turn end (`FinishTurn` / `message.complete`), interrupt (`FinishTurn("interrupted")`), disconnect (`OnUnreachable` / socket fault), session switch (`ClearTranscript` / resume / new session). Today: stale clock via `NoteTurnActivity` on message + submit paths (~L138–144 display; MW calls on start/delta/ack).

**Waiting wins (K7):** `AwaitingAnswer` is above Thinking in the voice-label chain; clarify tool → no activity line (map). Activity must not override Waiting.

**PresenceMode:** stays THINKING while `_streaming` (tools), unless awaiting/Speaking rules apply (~L306–342).

### 3. Notices (P4-D17) — **choice: panel-header mirror**

| Fact | Evidence |
|---|---|
| Notice Z | `ZolaLayerNotice` = **20** (`ZolaTokens.xaml` L66) |
| Panel Z | `ZolaLayerPanel` = **40** (L68) |
| Notice placement | `NoticeHost` bottom-center, `ZolaNoticeMargin` 24,0,24,**96** (above dock) (`MainWindow.xaml` L81–102) |
| Panel | `ConversationOverlay` **Right** + Stretch, max width 440 / 45% (`MainWindow.xaml` L203–210; tokens L37–38) |

**Geometry:** At 900×640 and 1280×800, an open right panel covers a large fraction of the lower-center notice band (same failure as P4-REQUEST B9 / AUD-39). Maximized: panel still occludes center-bottom.

**Why not raise Z:** Putting notices at Z>40 would paint over the panel header, transcript, composer, and clarify/approval buttons. Even with `IsHitTestVisible=False`, text over interactive chrome is wrong; prompt says prefer mirror if raise would sit over interactive controls.

**Choice:** **mirror into the conversation panel header** (row 0 next to “CONVERSATION”). Keep bottom `NoticeHost` for when the panel is collapsed. No `ZolaTokens` layer value change required unless a header style token is missing (flag then).

### 4. Stop speaking (K1)

**(a) Visibility fact (existing VC facts only):**
```
StopVisible = ModeVoice && !VoiceGated && (Speaking || QuestionSpeaking)
```
- `Speaking` = P2-D15 estimate (set on turn start / question speak; cleared when estimate ends / cancel follow-up / gate).
- `QuestionSpeaking` = clarify TTS until release chain ends.
- Bout facts (`NotePlaybackBout*`) are only armed during question speak — **not** for ordinary reply ffplay. **Accuracy limit:** for post-complete reply speech, Stop visibility follows the **estimate**, which can lag or end before real audio (P4-ASK C11 experience). Do not widen into `Presence/*`.

**(b) Serialized worker:** Implement `StopSpeakingAsync` as a request into `RunGateSequenceAsync` (same lock / epoch pattern as gate). Worker order: if `SystemLocked || SystemSuspended` → refuse (gate owns silence). Else run stop-speaking steps. A concurrent gate close always wins (facts gated → CloseGate path).

**(c) `voice.toggle off` → restore (Hermes):**
- Speech: `_voice_toggle_mode(off)` → `stop_continuous` + `_set_voice_tts(False)` → `_tts_stream_stop(user_barge=False)` + `stop_playback()` (`methods_voice.py` ~L640–656, ~L117–134). **No S21 latch** when `user_barge=False`.
- Streaming pipeline: stop event set; consumer exits and drains queue (`tts_tool_speaker.py` ~L308–340). Client restore = `toggle on` + `tts` only if speech was on — does **not** call `_tts_stream_begin`. Turn’s `st.tts_queue` remains a dead sink; further `put(delta)` are not spoken. End fallback speaks only if `st.tts_queue is None` (`prompt_turn.py` ~L344–348) — **not** after a killed stream (queue object still non-null).
- Wake: toggle off tears continuous loop; gate open re-arms wake. Stop path should **snapshot and restore** wake/speech like gate open, without treating Stop as Text mode.
- Capture: toggle off does not equal `voice.record stop`; open capture may still finish. Cancel follow-up on Stop so she does not auto-listen.
- P4-D13 question: kill ffplay → natural bout stop → rule-1 release → capture opens; **do not** `AbandonPendingQuestion` on Stop.

**(d) Controls:** **Two dock controls.** Cancel unchanged (`_streaming` only). Stop separate (visibility fact above). Shortcut: **Esc when conversation + sessions panels are closed** (Esc already closes panels in `OnEscapeKey` ~L2237–2250); when panels closed, Esc → Stop. Composer focus: if Esc would conflict with IME, still OK (no text-editing Esc binding today).

**(e) Refuse / no-op:** gated → refuse + log; `!Speaking && !QuestionSpeaking` → no-op + log.

**(f) Stop while streaming (v1.1):** **Allowed.** Proven for the normal streaming-TTS path: `_set_voice_tts(False)` stops the consumer for good for this turn’s queue; restore does not re-arm mid-turn; next turn’s `_start_turn_voice` → `_tts_stream_begin` is fresh (~L183–187). **Caveat (document, do not fix architecture):** if streaming never started (`tts_queue is None`) and Stop restores TTS before turn end, the whole-reply fallback could still speak once — rare when Edge streaming works. F5b applies. **Corroboration:** [Phase 2 hermes tool/voice research](3965e3bf-b17e-4e55-999a-9274860ee3af) — `user_barge=False` does not latch `SPEECH_INTERRUPTED`; `_fd_speak_pipelines` per-thread stops are not set by TTS-off alone, but `_tts_stream_stop` still calls `stop_playback()` (kills ffplay) so clarify `voice.tts` / reply playback stops for P4-D13 monitor release.

### 5. K2 (`_closedClarifyCaptureId`)

| Op | Where |
|---|---|
| Write (stash) | `StashClosedClarifyCapture` from `CancelFollowUp` (interrupt-like reasons only), `AbandonPendingQuestionIfId` capture arm, StartCapture generation-mismatch after record |
| Clear | `ClearClosedClarifyCapture` on new `SpeakQuestionAsync`; wake/mic capture (`requiredGeneration is null`); after transcript consumes closed id |
| Read | `OnVoiceTranscript` binds `active ?? closed` |

**Gap:** `OnTurnStarted` (~L1298–1330) does **not** clear closed id → typed-turn failure sequence in K2. **Fix:** `ClearClosedClarifyCapture()` at start of `OnTurnStarted` (covers typed Send and voice turns that raise `message.start`). C4 preserved: late transcript before any new turn still sees closed id.

### 6. K3 / P4-D18 logging

Today: length only on some paths (gate refuse, echo-ignored words — privacy risk for echo; leave unless in scope). No systematic transcript line with window/`filtered`.

**Phase 4 plan:**
- Extend `VoiceTranscript` to parse Hermes `filtered` (voice_mode returns `filtered: true` on hallucination ~L867–869).
- Track capture window: timestamp on successful `voice.record` start; end on idle / transcript.
- Log every transcript (including empty+filtered, stop-phrase, no-speech):  
  `transcript len=N filtered=bool stop=bool nospeech=bool bound=srq-*|none capture_start=… capture_stop=… duration_s=…`  
  **Never text.**

### 7. AUD-37 plan

**Script (5 attempts):** Voice mode; prompt e.g. “Ask me a quick question about my weekend, but don’t use your clarify tool.” Developer answers within 2 s of her finishing. Dictation tool **off** (K4 — confirm before Phase 5).

**Per attempt log:** speech end (estimate / any bout if question); capture start/stop; transcript len + filtered; whether `prompt.submit` / turn followed; loss layer (no capture vs VAD vs filtered vs empty STT).

**Effective config (profile + defaults):**
| Key | Live profile | Default (`config_defaults.py`) |
|---|---|---|
| `voice.barge_in` | **false** | true (~L1152) |
| `voice.silence_duration` | 1.5 | 3.0 (~L1151) |
| `voice.silence_threshold` | (unset → default) | 200 (~L1150) |
| `stt.local.vad` | (unset → default) | true (~L1091) |
| `stt.local.vad_min_silence_ms` | (unset) | 500 (~L1092) |

Context (K4): AUD-37 seen with barge-in **on**; FD listener gone now.

### 8. Flags

- Echo-ignored timeline currently logs normalized words — pre-existing; K3 must not add answer text.
- `PresenceAnimator` bout forward exists from P4-ASK; Stop must not depend on new Presence APIs.
- No BLOCKED conflict for build phases; Stop-during-streaming **approved** per (f).

## AUD-37 evidence table and outcome

**K4:** Windows dictation / Voice Access confirmed **off** (2026-09-30 process scan count=0; developer confirmed).

**Script prompt:** `Ask me a quick question about my weekend, but don't use your clarify tool.`

| # | Speech end | Capture start/stop | Transcript len / filtered | prompt.submit? | Lost? / layer |
|---|---|---|---|---|---|
| 1 | estimate complete `14:51:40.623`; estimatedEnd `14:51:43.904`; follow-up fire `14:51:46.912` (no bout/monitor — plain reply speech) | start `14:51:48.008` → stop `14:51:57.795` (duration_s=9.787) | len=**33** filtered=**false** stop=false nospeech=false bound=none | **yes** — turn start `14:51:57.823` immediately after transcript | **no** |
| 2 | estimate complete `14:54:56.389`; estimatedEnd `14:55:02.006`; follow-up fire `14:55:05.008` | start `14:55:05.709` → stop `14:55:10.009` (duration_s=4.3; Hermes record 2.0s, silence 1.5s) | len=**5** filtered=**false** bound=none (Hermes: VAD removed 1.271s of 2.087s) | **yes** — `chars=5` at `14:55:10.036` | **no** (short but submitted; a later follow-up also submitted len=48) |
| 3 | estimate complete `14:56:45.229`; estimatedEnd `14:56:51.021`; follow-up fire `14:56:54.024` | Listening/`Voice recording started` `14:56:54.738` → silence stop `14:57:11.018` (**16.3 s** WAV) | **no client transcript line**; Hermes: VAD removed **00:16.280 / 00:16.280**; `Filtered Whisper hallucination: ''` | **no** — only initial typed `chars=74`; no answer submit | **yes — timing hypothesis** (answer likely before mic open; 16.3 s then noise-only → VAD correctly empty) |
| 4 | *(superseded by A/B)* | | | | |
| 5 | | | | | |

**Outcome: REPRODUCED (attempt 3)** — lost spoken answer with `voice.barge_in: false`.

**Initial loss read:** VAD deleted the entire 16.3 s capture; empty → hallucination filter; Hermes skips empty `voice.transcript` (`if transcript:`).

**`stt.local.vad: false` — REJECTED for now.** VAD off would let silent follow-up windows produce hallucinated prompts.

**Working hypothesis (capture timing):** follow-up opens ~3.7–4.1 s after `estimatedEnd` (P2-D15 estimate + `FollowUpMarginSeconds` 3.0), so an answer within 2 s of her finishing can land **before the mic opens**; attempt 3’s long clip then held only noise, which VAD correctly removed. (Reply TTS does not arm the P4-ASK playback bout — bout facts expected **n/a** unless a clarify question path is used.)

### Discriminating attempts (timing hypothesis)

| # | Protocol | Real speech end (bout if any) | estimatedEnd | Follow-up fire | Capture start/stop | K3 transcript | Hermes VAD-removed | Result |
|---|---|---|---|---|---|---|---|---|
| A | Answer **immediately** when her voice stops (ignore HUD) | **n/a** (no bout — ordinary reply TTS) | `15:07:44.180` | `15:07:47.186` (~3.0 s after estimatedEnd; ~8.1 s after complete `15:07:39.045`) | start `15:07:47.881` → stop `15:08:01.092` (duration_s=13.211; Hermes record 12.1 s) | len=**0** filtered=false **nospeech=true** bound=none | VAD removed **00:12.159** of ~12.1 s; `Filtered Whisper hallucination: ''` | **lost** (no answer submit; only typed chars=74) |
| B | Wait until HUD **Listening**, then answer | **n/a** (no bout) | `15:10:18.698` | `15:10:21.699` (~3.0 s after estimatedEnd; ~7.3 s after complete `15:10:14.430`) | start `15:10:22.401` → stop `15:10:30.396` (duration_s=7.994; Hermes record 6.2 s) | len=**37** filtered=**false** nospeech=false bound=none | VAD removed **00:01.990** of ~6.2 s (speech kept) | **captured** — `prompt accepted chars=37` at `15:10:30.406` |

**A/B result:** hypothesis **holds** — A lost, B captured. Timing (follow-up opens after P2-D15 estimate + 3.0 s margin), not bad VAD.

**Fix location (developer decision): Track 4 = P4-D18 fix.** Proposed at STOP before build (see design below). Alternatives deferred: Track 5 P2-D15-only refit is **not** the chosen path for this fix.

### P4-D18 design — follow-up on reply playback release (**amended** before build)

**Goal:** After `message.complete`, open the unbound follow-up capture when her **real** reply audio has finished (plus a short quiet gap), not when the P2-D15 estimate + `FollowUpMarginSeconds` elapses.

**Scope:** `VoiceController.cs`; reuse existing MainWindow → PresenceView bout pass-through. **No** new Presence APIs. Tag `— P4-D18`.

#### Amended rules

1. **Hold Speaking for the whole reply (monitor stay-alive).**  
   Display/presence `Speaking` = P2-D15 estimate flag **OR** `_replyReleaseArmed` (covers active reply bout + post-release quiet window). Drops only when the follow-up release rule fires, or on Stop / gate / turn change / CancelFollowUp. Same idea as P4-ASK `QuestionSpeaking` — prevents estimate ending → leave Speaking → `StopMonitoring` → forced bout → early/wrong open.

2. **Startup window after `message.complete`.**  
   Named constant: **`ReplyBoutStartupWindowSeconds = QuestionBoutStartupWindowSeconds` (4.3 s = FirstSentenceLatency 3.3 + 1.0)**, measured **from `message.complete`** (not turn start).  
   - Bout starts within window → monitor rule.  
   - No bout in window → `no_bout_estimate` (existing estimate + margin; late bout during estimate upgrades to monitor, as in question path).

3. **While any reply bout is active:** no estimate/fallback timer may open the follow-up. Only: natural stop + quiet window, forced stop → remaining estimate, or cancellation (Stop / gate / new turn / Text).

4. **Natural stop + quiet:** `FollowUpPostBoutQuietSeconds = 1.2`. New bout inside the window **restarts** the quiet wait.

5. **Forced release** (monitor stopped for pause/stop): remaining time to `_estimatedSpeechEnd` (floor 0), then open — same idea as question `forced_release_estimate`.

6. **Fallbacks:** monitor unavailable → `monitor_unavailable` + estimate + margin. Bout never ends → no follow-up (fail closed; cancel paths still clear). `_speechStoppedThisTurn` → no follow-up.

7. **Echo / gate / mode:** unchanged (P2-D14 echo eligible; gate/Text/speech-off/generation rechecks).

8. **Log:** `follow_up_release rule=monitor|no_bout_estimate|forced_estimate|monitor_unavailable` with times.

**Quiet (amendment 2):** `FollowUpPostBoutQuietSeconds = 0.5` (was 1.2; Probe2: debounce ~0.49 s already in bout stop; bridged gaps max 441 ms).

**Fix 1:** seed active bout at `message.complete` via `PlaybackBoutActive`; quiet-loop only opens on `RanToCompletion && !boutActive`.

**Build:** `dotnet build … -r win-x64` — 0 errors, 0 warnings.

### AUD-37 outcome (closed)

**Reproduced** (timing): follow-up opened after P2-D15 estimate + margin, so immediate answers landed before the mic.

**Fixed by P4-D18:** monitor release + seed active bout (fix 1) + **0.5 s** post-bout quiet (amendment 2).

**Verify (fix 2):** immediate 0–1/5 full (partials; bout→mic ~1.06 s); natural after beep **3/3 full**; long reply stay-alive pass (L1); no `quiet_restart` in that run; no self-capture.

**Residual:** immediate answers still lose ~1 s (quiet + record-start / beep). Deferred to barge-in return (pre-roll). Smoke answers after the beep unless a step says otherwise.

---

## Discrepancies and flags

- See Phase 2 §8. None blocking.
- K3 gap: empty Hermes results often never reach the client (`if transcript:`); attempt A did emit `nospeech=true` len=0.

## Phase 3 build notes (`P4-D16`, `P4-D17`)

**Priority chain (unchanged; quoted before = after):**
`unavailable(+details) → Text mode → Waiting for your answer → Thinking → Speaking → Transcribing → Listening → Idle`
(`ZolaDisplayState.cs` Recompute; Waiting still above Thinking. Activity is a separate `ActivityLine` field and is forced empty while `AwaitingAnswer`.)

**Friendly-name map:** named table `ToolActivityNames` in `ZolaDisplayState.cs` — `web_search` / `terminal` / `skill_view` / `skills_list` / `skill_manage` / `clarify`→null / else `Working…`.

**Clear-all hooks (`ClearToolActivity`):**
- turn end — `FinishTurn` complete/error path
- interrupt — `FinishTurn` interrupted path
- disconnect — `ShowUnreachable`
- session switch — `ClearTranscript`

Also: first reply text → `NoteReplyTextStarted` (hides line; set retained until clear-all); `tool.generating` provisional only; `tool.output_risk` → `tool-events.log` (name+risk).

**P4-D17:** panel-header mirror (`PanelNoticeHost` beside CONVERSATION); bottom `NoticeHost` hidden while panel open.

**Build:** `dotnet build … -r win-x64` — 0 errors, 0 warnings.

## Phase 4 build notes (K1–K3)

**K1 `StopSpeakingAsync`:** queued into `RunGateSequenceAsync` via `_stopSpeakingQueued` + `_gateEpoch`. Worker order: facts gated → close (marks stop done / supersedes restore) → else open hold → else `ExecuteStopSpeakingAsync`. Visibility: `CanStopSpeaking = ModeVoice && !VoiceGated && Speaking && !QuestionSpeaking` (developer decision: Stop not offered during clarify question TTS — `voice.toggle off` would mute the rest of the turn). Dock **STOP** + Esc when panels closed (Esc during `QuestionSpeaking` → no-op + `refused reason=question_speaking`). Steps: snapshot → `CancelFollowUp("stop-speaking")` (no `AbandonPendingQuestion`) → `voice.toggle off` → restore `on` + status + **tts restore only if snapshot speech was on** (P2-D03; not used to stop) → wake re-arm if needed. Logs: `stop_speaking requested | step=… | done | refused reason=…`. **No `session.interrupt` in the Stop path.** Fail-closed: gated refuse leaves availability unchanged (no restore attempted when already gated).

**K2:** `ClearClosedClarifyCapture()` at start of `OnTurnStarted` (typed Send and voice `message.start`). C4 unchanged: late transcript before any new turn still binds `_closedClarifyCaptureId` and drops.

**K3 / P4-D18 logging:** `VoiceTranscript.Filtered`; capture window on successful `voice.record` start / idle or transcript; every transcript →  
`transcript len=N filtered=bool stop=bool nospeech=bool bound=srq-*|none capture_start=… capture_stop=… duration_s=…` (never text).

**Build:** `dotnet build … -r win-x64` — 0 errors, 0 warnings.

**K4 (before Phase 5):** confirm external Windows dictation / Voice Access is **off**.

### Phase 4 review fix — `_speechStoppedThisTurn`

Stop-while-streaming was leaving the P2-D15 path live: `CancelFollowUp` cleared `Speaking`, but later deltas still extended the estimate and `OnTurnCompleted` still armed follow-up (auto-listen after a silent estimated end) even though Hermes will not speak the rest of that turn.

**Fix:** `_speechStoppedThisTurn` set in `ExecuteStopSpeakingAsync` after a successful Stop commit (`CancelFollowUp`); cleared in `OnTurnStarted`. While set: `OnTurnDelta` accumulates text only (no estimate re-arm / no `SetSpeaking(true)`); `OnTurnCompleted` skips follow-up and keeps `Speaking` false. Does not touch `QuestionSpeaking` / P4-D13.

**Quoted after change** (`VoiceController.cs`):

```
OnTurnStarted (~L1474–1510): ClearClosedClarifyCapture(); _speechStoppedThisTurn = false; … SetSpeaking(true) only when ClockEligible (new turn).
OnTurnDelta (~L1512–1539): if (_speechStoppedThisTurn) { accumulate counts; return; } else extend _estimatedSpeechEnd.
OnTurnCompleted (~L1541–1590): if complete && _speechStoppedThisTurn → SetSpeaking(false); RememberSpokenEcho; follow_up_skipped; return (no timer).
```

**Record only (no code):**
- **F7 (amended):** while she is asking a clarify question, Stop is hidden/disabled and Esc is a no-op (logs `question_speaking`); after she finishes, answering by voice works and she replies out loud. (Supersedes the prior F7 watch about Stop-during-question restore race — Stop is no longer offered in that window.)
- **Known edge:** a gate close during Stop snapshots `speech=off`, so speech stays off after unlock (quieter direction, allowed by G-FAIL-CLOSED).
- **Lore closeout candidate:** stopping only the question’s audio without muting the rest of the turn needs a Hermes per-utterance stop; same future item as barge-in (state-aware speech control).

**Developer decision (pre–Phase 5):** Stop is **not** offered while `QuestionSpeaking` (`CanStopSpeaking` requires `Speaking && !QuestionSpeaking`; refuse `reason=question_speaking`).

**Rebuild:** `dotnet build … -r win-x64` — 0 errors, 0 warnings.

## Smoke evidence tables

**Procedure amendments (2026-09-30):**
- Answer every follow-up / clarify capture **after the beep**, unless the step says otherwise.
- **F5:** her reply must be ≥ 6 sentences. Any `follow_up_release quiet_restart` in the whole smoke run is a finding.
- **F5 / F6:** also confirm Stop cleared reply release — no `follow_up_release` and no capture open after Stop.
- **F7 (amended):** Stop hidden while she asks; Esc no-op (`question_speaking`); spoken answer still works.
- **F11:** Cursor-only from F5–F10 logs (no interactive step).
- **F12:** skip normal voice turn (AUD-37 covered); keep clarify voice answer only.

| # | Result | Evidence |
|---|---|---|
| F1 | PASS · FINDING `quiet_restart` ×5 | Activity lines for skill/terminal/web; cleared on Speaking. **P4-D18 evidence:** 5× `quiet_restart` (gap_ms 60, 61, 64, 66, 126 → silence ≈ 0.51–0.62 s). All caught; single `rule=monitor` fired after the reply; no capture mid-reply. Quiet window required. Margin ≈ 0.33 s; keep **0.5 s**; telemetry stays. “Thank you” = Whisper hallucination filter |
| F2 | PASS (scenario not producible) | Concurrent starts observed (`Searching` then `Checking skills`); Hermes v2026.9.14 emits batch completions only after the whole batch finishes, in call order (`tool_executor.py` 1336–1337, 1367–1400). Blank until batch end = correct client for that wire order. **Lore note (do not edit lore this track):** Hermes batch-delayed completions. |
| F3 | PASS | Activity `Checking a skill…` @ 17:42:54 then cleared; Cancel → Hermes `interrupted_during_api_call` / status=interrupted @ 17:42:56; Idle with empty activity (no stale line) |
| F4 | PASS (after notice-routing fix) | Retest: bottom `NoticeHost` and panel-header mirror both show `Declined unsupported server request: tour`. Screenshots: `P4-FEEDBACK_F4_bottom_notice.png`, `P4-FEEDBACK_F4_panel_notice.png`. Fix: `ShowRequestNotice` → StatusText (`P4-D17`). |
| F5 | PASS (+ retest after wake reconcile) | Initial @ 17:58:00 OK. Retest post-complete Stop @ 18:08:09 (words=101); wake.start; `wake.detected` @ 18:08:15; Hermes listening. |
| F5b | PASS (after wake reconcile fix) | Mid-stream Stop @ 18:08:56; `wake.pause stop-speaking-complete` → `pass=2 reason=turn-end` → `wake.resume`; `wake.detected` @ 18:09:20. **Wake reconcile retest:** `pass=2` converged ×4, `not converged` ×0. |
| wake-retest normal | PASS | Follow-up → silence → `wake.resume capture-idle` @ 18:10:24 → `wake.detected` @ 18:10:26; Hermes listening. |
| F6 | PASS | Esc → `stop_speaking` @ 18:12:19 (words=52, fireOrCancel=stop-speaking, followUpStarted=False); done + wake.start; `wake.detected` @ 18:12:27. Same path as dock Stop. |
| F7 | PASS · FINDING Esc/panel → Track 5 | `question_spoken`/`question_release rule=monitor` id=srq-1b7c0a4fadd3 @ 18:14:35–40; answered len=7 @ 18:15:12; reply TTS. `CanStopSpeaking` excludes `QuestionSpeaking` (Stop correctly hidden). **FINDING (cosmetic / Track 5):** clarify opens the conversation panel, so Esc closes the panel first (~4.4s question window) and never reaches the `question_speaking` refuse path. Esc does **not** stop speech, cancel the turn, or hide Stop when it should be available. No closeout fix. |
| F8 | PASS | Idle Esc: no new `stop_speaking` after F6; dock hidden @ 18:18:15. Esc is a silent no-op when `!CanStopSpeaking` (no refuse line by design). |
| F9 | PASS | Lock mid-reply @ 18:19:41: `gate closed` / `fireOrCancel=system-gate`; HUD Idle + “Windows locked”. Unlock @ 18:19:50: gate open + wake; Idle “Hey Zola”; dock hidden @ 18:20:02 (Stop not offered). |
| F10 | PASS | Clarify `srq-0d22de27dfba` spoken then Cancel → `cancelled reason=interrupted` / `question_abandoned`. Typed turn @ 18:22:28. Follow-up transcript `len=42 bound=none` @ 18:22:46 → `fireOrCancel=voice.transcript` → Hermes prompt accepted chars=42. No `late_answer_dropped`. |
| F11 | PASS (Cursor) | F5–F10 window: all `transcript len=… filtered=… stop=… nospeech=… bound=… capture_start/stop duration_s=…` lines; no spoken text in `voice-timeline.log`. |
| F12 | PASS (skipped normal; clarify covered) | Normal voice covered by AUD-37 + wake-retest. Clarify-by-voice: F7 (`answered` + reply TTS) and F10 path. |

### Phase 6 code changes (decision IDs)

| Change | Decision ID | Where |
|---|---|---|
| `ShowRequestNotice` → StatusText + `UpdateChrome`; `_requests.Notice` + both `NoticeLateAnswer` sites; `_chat.Routed` unchanged | **P4-D17** | `MainWindow.xaml.cs` |
| Panel-header notice mirror (`PanelNoticeHost`) | **P4-D17** | `MainWindow.xaml` / `.xaml.cs` (Phase 3; exercised in F4) |
| Reply follow-up: monitor bout + seed active bout at complete; Speaking hold via `_replyReleaseArmed` (fix 1) | **P4-D18** | `VoiceController.cs`; `PresenceAnimator`/`PresenceView` `PlaybackBoutActive` forward |
| Quiet window 1.2→**0.5 s** + `quiet_restart gap_ms` telemetry (fix 2) | **P4-D18** | `VoiceController.cs` |
| Single-flight `ReconcileWakeRestingAsync` + post-await converge (cap 3; `pass=N` / `not converged`) | **P2-D12** / **P4-FB-STOP** | `VoiceController.cs` |

**Part C (Cursor):** Stop via serialized worker only (`_stopSpeakingQueued` → `ExecuteStopSpeakingAsync`); Stop uses `voice.toggle off` + tts **restore** (not stop-by-tts); no `session.interrupt` in Stop. Transcript privacy OK. Note: F10 Cancel (not Stop) produced Hermes `[Note: the user interrupted…]` on the next typed turn — expected for interrupt, not a Stop/P2-D13 trip.

**Lore closeout note (do not edit lore this track):** concurrent tool completions are batch-delayed by Hermes; the activity line shows the newest-started tool until the batch ends.

## Exit-criteria table (closeout)

From `PHASE4_BUILD_PLAN.md` Track 4 Exit criteria + K1–K3. Verified 2026-09-30 (Phase 7a). Build: PASS (0 warnings / 0 errors).

| Criterion | Result | Evidence |
|---|---|---|
| Costco → activity line ≤1 s per tool; clears on text; no stale-thinking during tools | ✅ MET | F1 |
| Overlapping tools: older line reappears (or scenario not producible + lore note); Cancel mid-tool clears line | ✅ MET | F2 PASS (not producible) + lore note; F3 PASS |
| Panel open + notice visible (screenshot) | ✅ MET | F4 after `ShowRequestNotice` / P4-D17; screenshots in progress folder |
| AUD-37: five attempts; fix or closed | ✅ MET | Reproduced; P4-D18 monitor+seed+0.5 s quiet; closed after verify |
| PresenceMode unchanged except activity (THINKING during tools) | ✅ MET | Activity is separate `ActivityLine`; Waiting still above Thinking |
| Build passes | ✅ MET | `dotnet build … -c Debug -r win-x64` 0W/0E (7a) |
| Smoke Part B | ✅ MET | F1–F12; findings acknowledged (F1 quiet_restart as D18 evidence; F2 lore; F7 Track 5) |
| **K1** Stop speaking (F5–F9) | ✅ MET | F5/F5b/F6/F8/F9; F7 Stop hidden while asking (amended) |
| **K2** closed-id (F10) | ✅ MET | F10 follow-up submitted, no `late_answer_dropped` |
| **K3** transcript logging (F11) | ✅ MET | Length/flags/window; never text |

### Track-level checks

| Check | Result | Evidence |
|---|---|---|
| One display authority for activity | ✅ | `ZolaDisplayState.BuildActivityLine` sole writer; MW renders only |
| Stop only through serialized gate worker | ✅ | `_stopSpeakingQueued` → `ExecuteStopSpeakingAsync` in `RunGateSequenceAsync` |
| No `session.interrupt` / `voice.toggle tts` as Stop mechanism | ✅ | Stop = `off` + restore; tts flip only restore |
| hermes-agent clean at `345cd2b0…` | ✅ | 7b: clean; HEAD `345cd2b057a452236de401d3534b8502a7465e8d` |
| No lore updates this track | ✅ | Lore notes recorded in progress only |

### Final file list

**New:**
- `zola-architecture/lore/prompts/progress/P4-FEEDBACK_Progress.md`
- `zola-architecture/lore/prompts/progress/P4-FEEDBACK_D18_Probe2.md`
- `zola-architecture/lore/prompts/progress/P4-FEEDBACK_F4_bottom_notice.png`
- `zola-architecture/lore/prompts/progress/P4-FEEDBACK_F4_panel_notice.png`

**Modified:**
- `windows-client/Zola.Client/ChatSocket.cs` — tool.* events (`P4-D16`)
- `windows-client/Zola.Client/ZolaDisplayState.cs` — activity line (`P4-D16`)
- `windows-client/Zola.Client/MainWindow.xaml` / `.xaml.cs` — HUD/bubble activity, notice mirror, `ShowRequestNotice`, Stop chrome (`P4-D16`/`P4-D17`/`P4-FB-STOP`)
- `windows-client/Zola.Client/VoiceController.cs` — Stop, K2, K3 logging, P4-D18 reply release, wake reconcile single-flight (`P4-FB-STOP`/`P4-D14`/`P4-D18`/`P2-D12`)
- `windows-client/Zola.Client/Presence/PresenceAnimator.cs` / `PresenceView.cs` — `PlaybackBoutActive` forward for D18 seed (additive; same pattern as P4-ASK bout forwards)

## Phase 7 closeout notes

- **7a:** Build 0/0; exit table above; F7 Esc/panel = Track 5 only (no STOP).
- **7b:** Hermes clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- **7c–7i:** follow commit / push / merge / SHA docs / cleanup below.