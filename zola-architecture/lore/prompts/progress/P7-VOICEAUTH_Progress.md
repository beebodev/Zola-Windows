# P7-VOICEAUTH Progress — Transcript Authority

## Branch

- Work branch: `p7-voiceauth`
- Plan branch (deleted after merge): `p7-plan`
- Plan commit SHA: `b5583f97c3e13870abc5d483ec23566458cd828e` (`docs: Phase 7 build plan v1.1 (P7-D01–D13)`)
- Plan merge SHA (= `p7-voiceauth` base): `ffef6f050a3fd6a8092d77fc055370296e2b522b` (`Merge branch 'p7-plan'`)
- Plan on-disk SHA-256 (CRLF, 63,266 bytes): `87d83357c5ed1111eab4b094be68eda351a1e55e55d8977f0b18d05d678bbe19`
- Plan staged/blob SHA-256 (LF, 62,278 bytes): `74c95979e953de5a0289d1216e31e161f22812b56e58a789616033257b31298b`
- `git ls-files --eol` at stage: `i/lf w/crlf` for `PHASE7_BUILD_PLAN.md`
- Prompt: `P7-VOICEAUTH_Prompt_v1.1.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P7-VOICEAUTH_Prompt_v1.1.md`)
- Prompt SHA-256 (on-disk, 40,523 bytes): `faa769f061d421b5cb38128964b93b526ac2fa843360013e51697ca113668d51`
  - Developer-supplied SHA for comparison: **not provided in the Phase 1 prompt message**; recorded computed on-disk value above.
- Base `main` before plan: `c25899111c68ea37798c08f08aebdeee6653725a` (P7PRE closeout metadata)
- Hermes HEAD (Phase 1–2): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`); `git status --porcelain` empty

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Commit the Build Plan, then Branch | COMPLETE |
| 2 | Ground the Capture Lifecycle | COMPLETE |
| 3 | STOP: Approve the Lifecycle Contract | COMPLETE |
| 4 | Wave A: Pure Logic and Checks | COMPLETE |
| 5 | Wave B: Wire the Authority into the Client | COMPLETE |
| 6 | Deploy (rebuild and restart) | COMPLETE |
| 7 | Smoke Test | COMPLETE — smoke test passed (incl. S1b) |
| 8 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** New `Voice/CaptureLifecycle.cs`, `Voice/TranscriptAdmission.cs`, `Zola.Client.Checks/`, this progress doc; modify `VoiceController.cs`, limited `MainWindow.xaml.cs` (newest-clarify removal + broker query), optional `TtsPlaybackMonitor` read-only query, `.gitignore` for Checks bin/obj if needed; commit plan byte-for-byte in Phase 1 only. No live-profile / SOUL / config / plugin / Hermes edits.
- **G-ARCH:** Build plan + P7-D01–D08 are truth; terminal signals only when proven; recovery never admits; cancel mechanism A vs B is a Phase 3 developer decision.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No hermes-agent edits; no ChatSocket / ServerRequestBroker / ZolaDisplayState / HermesProcessManager / XAML; no lore edits this track; Android out of scope.
- **G-ONE-AUTHORITY:** One admission method (`TranscriptAdmission.Decide`); one cancel method; MainWindow never re-decides admission.
- **G-NO-INSTALL:** Checks project is SDK-only, no NuGet; stop if restore pulls packages (VA-G9).
- **G-COMMENT:** `// P7-VOICEAUTH: <rationale> — P7-D0X` per distinct changed block.
- **G-CONST:** Named constants for timeouts, reasons, kinds, signals, log prefixes.
- **G-PRIVACY:** No transcript/reply text in logs, progress, or real-use fixtures; lengths/IDs/kinds/reasons only. Replace `echo-ignored words=…`.
- **G-LIVE:** Live steps one at a time; Cursor never injects turns.
- **G-STOP / G-CLOSEOUT:** Stop after each phase; closeout only on “proceed to closeout”.
- **G-LORE-SCOPE:** No lore edits (including closeout). S45/S37 at Phase 7 lore closeout later.
- **G-NO-CROSS-SCOPE:** No Android Zola.

## Discrepancies

none

## Phase 6 process note (from Phase 3)

Confirm the two `python.exe` serve processes are parent and child (uv launcher plus venv python), not two serves.

## Phase 1 baseline (processes and logs)

Recorded 2026-10-06 ~07:08 local.

| Process | PID | Start time | Notes |
|---|---|---|---|
| `dotnet.exe` (run Zola.Client) | 9748 | 2026-10-05 19:29:15 | parent runner |
| `Zola.Client.exe` | 20468 | 2026-10-05 19:29:35 | client |
| `python.exe` (hermes serve, venv) | 16456 | 2026-10-05 19:29:38 | `-m hermes_cli.main -p zola serve --isolated` |
| `python.exe` (hermes serve, uv) | 12352 | 2026-10-05 19:29:38 | same serve command line |

| Log | Bytes | Last write |
|---|---|---|
| `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` | 823,024 | 2026-10-06 07:05:01 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\agent.log` | 4,268,626 | 2026-10-06 07:07:52 |

---

## VA-G1–G11 answers (Phase 2)

Hermes pin verified: `345cd2b057a452236de401d3534b8502a7465e8d`, porcelain empty. Client on `p7-voiceauth` @ `ffef6f05…`. Path note: voice event contracts live at `tui_gateway/contracts/events.py` (not `tui_gateway/events.py`).

### VA-G1 — The terminal set (P7-D03)

**Rule applied:** terminal only if no `voice.transcript` attributable to that capture can follow.

| Candidate | Verdict | Proof |
|---|---|---|
| Non-empty text transcript | **[CONFIRMED] terminal for admission** | Delivered via `on_transcript` only when text non-empty (`hermes_cli/voice.py` 504–505, 440–441). Gateway: `methods_voice.py` 748, 685–687. With `auto_restart=False` (752), loop goes to `_rearm` → `_deactivate` → idle (532–534). At most one deliverable transcript (VA-G3). |
| Empty / filtered (no wire event) | **[REFUTED] as wire terminal** | `_transcribe_wav` returns `None` for empty/hallucination (`voice.py` 174–197); `if transcript:` skips emit (504–505). Capture still ends via `_deactivate` → **idle**. |
| `no_speech_limit` transcript | **[CONFIRMED] terminal** | `on_silent_limit` → `_vr_transcript({"no_speech_limit": True})` (`methods_voice.py` 749; `voice.py` 506–514). Loop sets `_continuous_active=False` before signal (508–510). |
| Stop-phrase transcript | **[CONFIRMED] terminal** | `_vr_on_stop_phrase` → `_end_voice_chat` then `{stop_phrase, text}` (`methods_voice.py` 690–694). Loop already halted (508–513). `_turn_transcript` returns deliverable text `None` for stop phrases (`voice.py` 268–272) so no second text emit. |
| `voice.status` `listening` | **[REFUTED] terminal** | Start/rearm only (`voice.py` 384, 545). Transcript can follow. |
| `voice.status` `transcribing` | **[REFUTED] terminal** | Before STT (`voice.py` 485, 413). Transcript / no_speech / stop can follow. |
| `voice.status` `idle` | **[CONFIRMED] terminal** | After finish/halt/deactivate/cancel (`voice.py` 457, 513, 205). Cancel discards buffer — no transcript (`424–427`). Force path delivers any transcript **before** idle (`430–448`). After idle, `_continuous_active` is false; further `stop_continuous` no-ops (`398–400`). **Also required before the next capture may become Accepting** — see critical note below. |
| RPC `recording` / status name `recording` | **[REFUTED]** | RPC result only (`methods_voice.py` 756), not a `voice.status` event. Continuous status strings are only `listening` / `transcribing` / `idle` (`contracts/events.py` 611–634). |
| Max-length end | **[REFUTED] as distinct terminal** | Cap trips same auto-stop → `_continuous_on_silence` (`voice_mode.py` 687–689). Same sequence as VAD silence. Default cap **120.0 s** (`methods_voice.py` 739). |
| Recorder start error | **[CONFIRMED] terminal for that start** | `rec.start` failure → `_deactivate()` + raise (`voice.py` 378–383); gateway `5025` (`methods_voice.py` 757–762). No transcript from that attempt. |
| `voice.record` start → `busy` | **[REFUTED] terminal for a prior in-flight capture** | `start_continuous` returns `False` when `_continuous_stopping` (`voice.py` 355–357); RPC `busy` (`754–756`). Prior force-transcribe may still emit. |
| Socket drop | **[REFUTED] terminal** | WS teardown does not call `stop_continuous` / `_end_voice_chat`. Process-global loop can keep recording and emit toward `_voice_event_sid`. |

**Critical operability proof:** after a text transcript with `auto_restart=False`, `_rearm_after_turn` may wait on TTS up to **60 s** before `_deactivate`/`idle` (`voice.py` 524–534). During that window `_continuous_active` remains true, so `start_continuous` returns `True` as a no-op (“already active”, `352–354`) without opening a fresh capture. Therefore **idle is required before the next capture may become `Accepting`**, even when admission already settled on a transcript.

**L-3/L-4 corroboration (voice-timeline, session `20261005_192949_1f4302`):** Run A/B show transcript then follow-up-idle; L-4 clarify shows `question_release rule=monitor` then bound transcript `bound=srq-702897de9735` (VT ~L4834–4927). Stale window on echo line matches AUD-23 (L4896 reuses prior capture_start/stop).

### VA-G2 — Stop with nothing recording

**[CONFIRMED]** `voice.record` stop always: `stop_continuous(force_transcribe=True)` + `_resume_voice_wake()` + `{"status":"stopped"}` (`methods_voice.py` 721–725).

| Case | RPC | Later transcript/status? |
|---|---|---|
| (a) Already ended (idle, `_continuous_active=False`) | `stopped` | `stop_continuous` early-return (`voice.py` 398–400) — **no** further status/transcript from stop |
| (a′) Still mid-silence-transcribe | `stopped` | Race: silence may abort delivery if active cleared (`499–501`); force path may emit 0 or 1 transcript then idle |
| (b) Never started | `stopped` | Same early-return; no events |

### VA-G3 — Stop racing silence

**[CONFIRMED]** At most one delivered transcript per capture; dual-deliver prevented by lock + recorder.

- `_continuous_lock` + `_continuous_active` at silence entry (`475–478`) and post-STT (`498–501`)
- `stop_continuous` clears active and swaps callbacks to `_NO_CALLBACKS` under lock (`398–406`)
- `AudioRecorder.stop` second call while not recording → `None` (`voice_mode.py` 801–803)
- Worst case: **lost** transcript (silence aborted after stop cleared active), not two

### VA-G4 — Inadmissible stop phrase

**Hermes spoken stop** (`methods_voice.py` 690–694): `_end_voice_chat(stop_loop=False, stop_tts=True)` then stop-phrase transcript.

`_end_voice_chat` (`51–60`): sets `HERMES_VOICE=0`, `HERMES_VOICE_TTS=0`; optional loop cancel; optional `_tts_stream_stop(user_barge=False)` — **no** `mark_speech_interrupted` latch.

**Turns off:** voice mode env, TTS env, live TTS stream/playback. Does **not** end the chat/session. Does **not** re-call `stop_continuous` (loop already halted).

**Client today** (`VoiceController.cs` 1920–1926): every stop phrase → `CancelFollowUp` → `VoiceChatEnded` → `ResyncAfterStopAsync` (sync on/tts via `SyncVoiceModeAsync` 2067–2084). **No** inadmissible gate today.

**[CONFIRMED]** `ResyncAfterStopAsync` restores Voice (status → on → tts if needed) **without** `voice.toggle off`, so it does **not** take the S21 latch path from the client.

**[REFUTED]** that today's path is sufficient for an *inadmissible* stop: it always raises `VoiceChatEnded` (MainWindow skips open clarify, 544–559). Inadmissible restore must **skip** `VoiceChatEnded` and only run the resync (VA-G4 restore).

### VA-G5 — Status sequences (`auto_restart=False`)

| Ending | Sequence |
|---|---|
| VAD silence → text | `listening` → `transcribing` → `voice.transcript{text}` → (possible TTS wait ≤60s) → `idle` |
| VAD silence → empty | `listening` → `transcribing` → (no transcript) → `idle` |
| 3rd empty → limit | `listening` → `transcribing` → `voice.transcript{no_speech_limit}` → `idle` |
| Client stop | RPC `stopped` → `transcribing` → optional transcript/stop/no_speech → `idle` |
| Max length | Same as VAD silence (no distinct event) |
| Spoken stop | `listening` → `transcribing` → `_end_voice_chat` → `voice.transcript{stop_phrase,text}` → `idle` |
| Cancel (toggle off) | `idle` (no `transcribing`; buffer discarded) |

### VA-G6 — One submit path

**[CONFIRMED]** Only route: `ChatSocket` `voice.transcript` → `VoiceController.OnVoiceTranscript` → `TranscriptReady` → `MainWindow.OnTranscriptReady` → `SubmitTurnAsync` / `ApplyVoiceClarifyAnswer`.

Evidence: VC 296, 1981–1984; MW 202, 562–596. Stop phrase / no-speech / gated / echo do not raise `TranscriptReady`. Typed composer and clarify UI cards are non-voice routes (unchanged).

### VA-G7 — Reconnect

**[CONFIRMED]** `OnSessionReady` bumps `_connectionGeneration` and `CancelFollowUp("session-ready")` (VC 1682–1687) — **does not** `voice.record stop`.

**[CONFIRMED]** Old aborted socket cannot deliver into the new ReadLoop (`ChatSocket` binds socket at loop start).

**[CONFIRMED]** `OnVoiceTranscript` does **not** check `_connectionGeneration` — a late Hermes transcript on the **new** socket can still raise `TranscriptReady` today (P7 must drop via lifecycle).

**[REFUTED]** that socket drop is a Hermes terminal (VA-G1).

### VA-G8 — Monitor query

**[CONFIRMED]** Synchronous queries already exist; **no TtsPlaybackMonitor change proposed**.

- `TtsPlaybackMonitor.IsAvailable` / `IsBoutActive` (monitor 50–66)
- `PresenceAnimator.PlaybackMonitorAvailable` / `PlaybackBoutActive` (animator 92–95)
- Wired via `ConfigureQuestionSpeech` (MW 180–193); used in question/reply release paths (VC 701, 2215–2216, 2286)

When unavailable: availability false → bout active false → today's estimate / `monitor_unavailable` paths.

### VA-G9 — Check project

**[CONFIRMED]** Scratch harness at `C:\Users\test\Dev\zola-spikes\p7-voiceauth\va-g9-check\`: SDK console `net9.0`, `<Compile Include … Link=…>` of a WinUI-free `.cs` file.

- `dotnet restore`: “Restored … (in 58 ms)”
- `project.assets.json`: `"libraries": {}`, `"projectFileDependencyGroups": { "net9.0": [] }` — **no NuGet packages downloaded**
- `dotnet run` output: `va-g9=5`

Default tooling for Phase 4: dependency-free console (not MSTest).

### VA-G10 — Clarify turn state

**[CONFIRMED]** Clarify answer capture commonly runs while the turn is still “running”.

| Step | `TurnRunning` / `_streaming` | Broker | Evidence |
|---|---|---|---|
| Clarify opens (mid-turn) | typically **true** | Open | MW `OnClarifyOpened`; broker Open |
| Question spoken | **true** if turn waiting | Open | `SpeakQuestionAsync`; HUD `AwaitingAnswer` |
| Answer capture opens | **true** | Open (recheck L887) | `OpenClarifyAnswerCaptureAsync` bypasses `CanStartCapture`/`!TurnRunning` (L905) |
| Transcript / answer | **true** | Open → Answered | `ApplyVoiceClarifyAnswer` → `AnswerClarify` |
| Reply completes | → **false** on FinishTurn | closed | `OnMessageCompleted` |

L-4 VT: `question_release rule=monitor id=srq-702897de9735` then bound transcript. Admission must key the **bound open request**, not `!TurnRunning` (plan v1.1 / P7-D05).

Broker query already wired: `ConfigureQuestionSpeech` → `GetState(id)==Open` and session match (MW 182–192). Phase 5 may keep this shape or widen to `(sessionId, clarifyId)`.

### VA-G11 — Cancel without a transcript (report only)

**[CONFIRMED]** `voice.toggle` off calls `stop_continuous()` with default `force_transcribe=False` → `rec.cancel()` discards buffer (`methods_voice.py` 639–648; `voice.py` 424–427).

| Side effect | Off→on cycle |
|---|---|
| Capture | Cancelled; **no** force STT |
| TTS cut | Yes, via `_set_voice_tts(False)` → `_tts_stream_stop(user_barge=False)` |
| `SPEECH_INTERRUPTED_NOTE` | **Not** latched (`user_barge=False`, `methods_voice.py` 125–130) |
| Wake | Idle → `_resume_voice_wake` when status callbacks still installed |
| Flags after off | `HERMES_VOICE=0`, `HERMES_VOICE_TTS=0` |
| Flags after on | `HERMES_VOICE=1`; TTS stays **0** until separate tts toggle |
| Running turn | **Not** interrupted (no `agent.interrupt` on this path) |
| Transcript after cancel | Normally none; silence mid-STT drops if active cleared (`499–501`) |
| Cycle duration | Not fixed in source (beeps 880 Hz start / 660×2 stop only) |

**Compare to `voice.record` stop:** always `force_transcribe=True`; keeps voice mode on; emits `transcribing` then optional transcript then `idle`.

**Call-site equivalence vs P7-D02 (G-ARCH bar):**

| Call site | A (`record stop` + drop) | B (toggle off→on) | Equivalent? |
|---|---|---|---|
| Typed submit / CancelFollowUp orphan | Stops mic; may force one dropped transcript; voice/TTS stay on | Cancels mic; **cuts TTS**; flips voice off then on; TTS must be restored | **No** |
| Turn start | Same as A | Would cut TTS at turn start | **No** |
| OnSessionReady | Stop orphan | Mode flip during session setup | **No** |
| Stop speaking | Appendix A names record stop; today already uses off→on for TTS cut | Same as today's Stop path for cancel | Different purpose (TTS cut vs capture cancel) |
| Gate close | Already record stop then toggle off | B alone omits the ordered gate sequence | **No** |
| Mode → Text | record stop then off | Off alone cancels | Partial; still not “stop-only” |

**Recommendation:** **A**. B fails “equivalent to a capture cancel at every call site, apart from suppressing transcription.” Draft upstream note for `voice.record cancel` (see proposals §2).

---

## Phase 2 proposals (for Phase 3 STOP approval)

### 1. Frozen terminal set

**Include (settle ownership / admission lifecycle):**
1. `voice.transcript` with non-empty `text` (normal)
2. `voice.transcript` with `stop_phrase: true`
3. `voice.transcript` with `no_speech_limit: true`
4. `voice.status` `{state:"idle"}` — proven end; **required before next `Accepting`**

**Exclude:** `listening`, `transcribing`, empty/filtered (no wire event), max-length (not distinct), RPC `busy`/`recording`/`stopped`, socket drop, `"recording"` as status.

**Operability latch:** `HermesBusyUntilIdle` set on successful start (`listening`); cleared on `idle`. No new capture becomes `Accepting` while the latch is held (covers post-transcript TTS wait no-op start).

### 2. Cancel mechanism

- **(A) Default / recommended:** invalidate → `voice.record stop` → drop forced transcript (`reason=cancelled`). Matches P7-D02 / Appendix A.
  - Risk: forced transcript must never admit; stop-with-nothing is a no-op (VA-G2) so next genuine capture still works.
  - Protection: Cancelled state before stop; admission order; HermesBusyUntilIdle until idle.
- **(B) Not recommended:** VA-G11 toggle off→on. Fails G-ARCH equivalence (TTS cut, mode/TTS flags, turn-start/session-ready side effects). See table above.

**Upstream note (file with A):**
> Add `voice.record cancel`, which ends the active recording without transcription and emits an unambiguous terminal event or correlation token.

### 3. State table (proposal)

**States:** `Starting`, `Accepting`, `Cancelled`, `Settled`. At most one non-`Settled` capture. Kinds: `Wake`, `Manual`, `FollowUp`, `EchoReopen`, `Clarify(id)`.

**Lifecycle (state × event → next):**

| State | Event | Next | Notes |
|---|---|---|---|
| (none) | client start (kind) | Starting | if Settled/none + may start |
| Starting | `listening` | Accepting | set HermesBusyUntilIdle |
| Starting | start `busy` / error | Settled | signal=`start_failed`; clear pending clarify/follow-up per kind |
| Starting | client cancel | Cancelled | then Hermes stop (A) |
| Accepting | client cancel | Cancelled | invalidate first, then stop (A) |
| Accepting | transcript (text/stop/no_speech) | Settled | admission decided here; still wait idle for next Accepting |
| Accepting | `idle` (no prior transcript) | Settled | empty end |
| Cancelled | transcript | Settled | always Drop(cancelled); stop-phrase → VA-G4 restore only |
| Cancelled | `idle` | Settled | |
| any non-Settled | `recover_timeout` | Settled | signal=`recover_timeout`; never admits; see recovery |
| Settled | `idle` | Settled | clear HermesBusyUntilIdle |
| Settled | late transcript | Settled | Drop(settled) / Drop(no_owner) |

**Admission verdict by lifecycle snapshot (after gate/mode):**

| Owner state | Verdict |
|---|---|
| none / Settled / Cancelled | Drop(`no_owner` / `settled` / `cancelled`) |
| Starting | Drop(`no_owner`) — not yet Accepting |
| Accepting | continue to authority checks |

**Admission check order (P7-D01):**
1. gate → Drop(`gated`); mode Text → Drop(`mode_text`)
2. owner exists and is `Accepting`
3. Capture authority: `Clarify(id)` only if broker says `id` open for this session (ignore generic TurnRunning); other clarify binding → Drop(`clarify_not_active`); ordinary kinds while TurnRunning → Drop(`turn_running_unbound`)
4. Echo predicate last: can only change Admit → Drop(`echo`)

**Stop phrases:** admission first (ownership → authority → echo). Only **Admit** runs stop semantics (`VoiceChatEnded`, clarify skip). Inadmissible → VA-G4 restore only; never `VoiceChatEnded`.

**Start requests while another generation is outstanding (not Settled) or HermesBusyUntilIdle:**

| Kind | Policy | User-visible | Release / expiry |
|---|---|---|---|
| Wake | **Reject** | Timeline `start_rejected kind=wake reason=busy`; wake resumes after settle (no second capture) | — |
| Manual (mic/hotkey) | **Reject** if Starting/Accepting/Cancelled; mic-stop while Accepting remains user stop (cancel+stop), not a start | Status: keep existing busy/active chrome; timeline `start_rejected kind=manual reason=busy` | — |
| FollowUp | **Defer** (at most one pending) | Timeline `start_deferred kind=follow_up`; must not silently vanish | Released on outstanding → Settled **and** HermesBusyUntilIdle cleared; revalidate gate/mode/!TurnRunning/Voice; expire `PendingStartExpirySeconds=5`; on expiry log `start_expired kind=follow_up` + reconcile wake |
| EchoReopen | **Defer** (same single pending slot; newer supersedes older pending of same class) | Timeline `start_deferred kind=echo_reopen` | Same release/revalidate/expiry as FollowUp |
| Clarify(id) | **Supersede** outstanding: cancel outstanding first, then **defer** clarify start until Settled+idle | Timeline `start_supersede` + `start_deferred kind=clarify`; never silent loss | Released on Settled+idle; revalidate broker still Open for id + session + Voice; expire `ClarifyPendingStartExpirySeconds=15`; on expiry log + abandon token (existing clarify skip paths) |

Invalid/impossible pairs (e.g. Admit while Cancelled, Accepting while two owners, start while Accepting without policy row): **fail-closed** — Drop/log/`start_rejected`; never transition to Accepting.

### 4. Recovery rule

- **`CaptureSettleTimeoutSeconds = 180`**
  - Basis: default `max_recording_seconds` **120** (`methods_voice.py` 739) + **60** STT budget (live warm WAV→Transcribed median ~1.66 s / H-1 ~0.75 s per P7PRE; local whisper CLI timeout can be much higher — 60 s is the operability budget, not the HTTP ceiling).
- On timeout: outstanding → `Settled` with `signal=recover_timeout`. **Never** changes admission (late transcripts Drop).
- After `recover_timeout`: no new `Accepting` until **idle** is observed **or** `LateTranscriptGuardSeconds = 60` elapses after a best-effort `voice.record stop` sent at recovery. During the guard, transcripts Drop(`settled`).

### 5. Inadmissible stop-phrase restore (VA-G4)

On Drop of a stop-phrase transcript (any drop reason): call the same restore as `ResyncAfterStopAsync` / `SyncVoiceModeAsync` (status → on → tts if needed); **do not** raise `VoiceChatEnded`; **do not** skip clarify. Gate refuse still applies (existing). No S21 latch (no toggle off on this path).

### 6. D06 hand-back

In reply and question release paths, when rule is `no_bout_estimate` / `forced_estimate` / `forced_release_estimate` (or estimate branch of `question_release`) **and** monitor available **and** bout active now: **do not** open capture. Hand back to monitor bout-stop + existing quiet rule (`P4-D18`). Bound wait: wait for bout stop up to `D06HandbackMaxSeconds = 120`, then if still active → **no capture** (log `handback_timeout`; never estimate-open during active bout). Monitor unavailable → today's estimate behavior unchanged. Monitor-driven release path untouched.

### 7. Log line formats (named constants; lengths/IDs only)

| Event | Format |
|---|---|
| Lifecycle transition | `capture lifecycle gen={g} kind={k} from={s} to={s} signal={sig}` |
| Start rejected/deferred/expired/supersede | `capture start_{rejected\|deferred\|expired\|supersede} kind={k} reason={r} gen={g}` |
| Cancel | `capture cancel gen={g} kind={k} reason={r}` then `capture stop_sent gen={g}` (A) |
| Recovery | `capture recover_timeout gen={g}` / `capture late_guard begin\|end gen={g}` |
| Admission Admit | `transcript admit gen={g} kind={k} clarify={id\|none} len={n} owner_window=…` |
| Admission Drop | `transcript drop reason={r} gen={g\|none} kind={k\|none} len={n} owner={window\|none}` |
| Replace `echo-ignored words=…` | `transcript drop reason=echo gen={g} kind={k} len={n}` (plus existing notice/reopen behavior for follow-up Drop(echo) only) |
| VA-G4 restore | `stop_phrase restore inadmissible reason={r}` |
| D06 hand-back | `follow_up_release handback_active_bout rule={r}` / `question_release handback_active_bout rule={r}` |

### 8. Check list (exhaustive over approved tables)

Phase 4 checks must cover every row of: lifecycle state×event, admission classes, start-request rows (reject/defer/supersede/release/revalidate/expiry), invalid pairs fail-closed, stop-phrase admit vs restore, plus plan list:

- each cancel reason → forced transcript Drop(`cancelled`)
- VA-G2 stop-with-nothing → next genuine admit
- VA-G3 race as grounded (≤1 transcript; cancelled drops)
- recover_timeout → Settled, no retroactive admit; no Accepting until idle/guard
- TurnRunning + unbound → drop; TurnRunning + active clarify → admit; closed clarify → drop
- fallback + active bout → no capture; monitor unavailable → today's behavior
- echo last and reject-only
- inadmissible stop → restore, not end
- gate / Text mode → drop

Coverage line example: `lifecycle rows N/N, admission rows N/N, start rows N/N, invalid pairs N/N, stop_phrase rows N/N`.

### 9. Check tooling

**Default:** dependency-free console project (VA-G9 proven). MSTest only if Brian chooses at Phase 3 (would be an approved install).

---

## Cancel paths inventory (Phase 5 wiring targets)

Must call one cancel method (invalidate → A stop): `CancelFollowUp` sites that leave Hermes recording, `OnTypedSubmit`, Stop speaking (after/with existing TTS off path — still invalidate+record stop if CaptureActive), mode→Text, `OnSessionReady`, turn start (today bumps gen without CancelFollowUp/stop), gate close (replace its record stop with the shared method), `voice.interrupted`, `app-close` / Shutdown, and any other Phase-2-found orphan path.

---

## Brian's STOP verdicts (Phase 3 — verbatim)

> Phase 3 verdicts (Brian, with Claude's review; record verbatim):
> Terminal set: approved as proposed (transcript text / stop_phrase / no_speech_limit settle admission; idle required before the next Accepting).
> Cancel mechanism: A. File the upstream voice.record cancel note in the progress doc.
> State table, start-request policy, stop-phrase ordering, invalid pairs fail-closed: approved, with these amendments:
> listening proves a fresh capture. Starting → Accepting only on the listening event after our own start. Add StartListeningTimeoutSeconds = 3: no listening in time → log start_no_listening, cancel (A), wait for idle, then handle the request per its start-policy row (follow-up/clarify: still deferred within their expiry; wake/manual: rejected). Before building, confirm every "listening" emit site in hermes_cli/voice.py and methods_voice.py (expected: start_continuous only on our auto_restart=False path) and record it.
> Recovery: keep CaptureSettleTimeoutSeconds = 180 as the backstop. Remove LateTranscriptGuardSeconds. After recover_timeout, the next capture becomes Accepting only on its own listening (amendment 1). No extra guard.
> voice.tts behavior: record in the state table that speak_text cancels and restarts an active recorder with no status events. The capture stays Accepting; nothing depends on a status change there.
> Correction to record: the up-to-60 s idle delay applies only when a voice.tts (speak_text) playback is in flight (_tts_playing is only cleared in speak_text). Streamed reply TTS doesn't touch it, so normal turns get idle right after the transcript.
> Recovery, VA-G4 restore, D06 hand-back (120 s bound, no capture on timeout), log formats, check list: approved. Add check rows for amendments 1–3.
> Check tooling: dependency-free console (no MSTest).
> Phase 6 note: confirm the two python.exe serve processes are parent and child (uv launcher plus venv python), not two serves.

### Listening emit-site confirmation (pre-build, amendment 1)

| Site | File:line | Emits `listening`? | On Zola path (`auto_restart=False`)? |
|---|---|---|---|
| After successful `rec.start` in `start_continuous` | `hermes_cli/voice.py:384` | Yes | **Yes** — this is the only listening emit for `voice.record start` |
| After rearm restart in `_rearm_after_turn` | `hermes_cli/voice.py:545` | Yes | **No** — only when `auto_restart=True`; gateway sets `auto_restart=False` (`methods_voice.py:752`) so this path `_deactivate`s instead (`voice.py:532–534`) |
| `methods_voice.py` | `_vr_on_status` at 697–700 | Forwards whatever `on_status` sends | Does not originate `listening` |

**Confirmed:** on Zola's client-driven path, `listening` is emitted only from `start_continuous` after our own start.

### Upstream note (filed — cancel mechanism A)

> Add `voice.record cancel`, which ends the active recording without transcription and emits an unambiguous terminal event or correlation token.

### Correction recorded (idle delay)

The up-to-60 s idle delay in `_rearm_after_turn` applies only when `voice.tts` / `speak_text` playback is in flight (`_tts_playing` cleared only in `speak_text`, `hermes_cli/voice.py:658–672`). Streamed reply TTS does not touch `_tts_playing`, so normal turns reach `idle` right after the transcript.

## Frozen terminal set / approved state table (Phase 3)

**Terminal set (approved):**
1. `voice.transcript` text / `stop_phrase` / `no_speech_limit` — settle admission for that generation
2. `voice.status` `idle` — proven end; next capture becomes `Accepting` only on **its own** `listening` after our start
3. `StartListeningTimeoutSeconds = 3` — no `listening` → `start_no_listening`, cancel (A), wait idle, then start-policy (follow-up/clarify stay deferred within expiry; wake/manual rejected)
4. `speak_text` pause/resume: no status events; capture stays `Accepting`
5. Cancel mechanism **A**; `CaptureSettleTimeoutSeconds = 180`; **no** `LateTranscriptGuardSeconds`
6. Start-request policy, stop-phrase ordering (admission first), invalid pairs fail-closed — as Phase 2 proposal with amendments above
7. VA-G4 restore, D06 hand-back (120 s), log formats, check list — approved
8. Tooling: dependency-free console

## Phase 4 contract-conformance STOP (verbatim)

> Not "proceed to phase 5" yet. Phase 4 has two contract-conformance bugs (Claude ran your checks plus two probes; checks pass, probes fail):
> Deferred starts are never released when a transcript precedes idle. ApplyTranscript → ForceSettle sets no release, and ApplyIdle with !_hasOutstanding only releases under _awaitingIdleBeforePendingRelease. Repro: FollowUp start → listening → Clarify start (SupersededAndDeferred) → forced transcript → idle ⇒ ReleasePendingNow=false at both steps, and the pending clarify expires at +15 s. The same happens for any deferred FollowUp/EchoReopen behind a capture that ends in a transcript.
> The approved operability latch (HermesBusyUntilIdle, Phase 2 proposal §1) is not implemented. Repro: Wake start → listening → transcript → EchoReopen start before idle ⇒ Began (should defer); then the old capture's idle ⇒ the new Starting capture is force-settled, and the start is lost with no retry.
> Fix, exactly (approved at this STOP; record verbatim):
> Add the latch: set when a capture goes Starting → Accepting (listening); cleared by any idle, and by recover_timeout (backstop; the next Accepting still requires its own listening).
> BeginStart treats "outstanding non-Settled or latch held" as busy, using the approved policy rows (Wake/Manual reject; FollowUp/EchoReopen defer; Clarify: cancel first if a capture is outstanding, then defer; if only the latch is held, just defer).
> ApplyIdle: clear the latch; if there is no outstanding capture and a pending start exists, return ReleasePendingNow=true (the wiring revalidates on release).
> idle while Starting is stale (from the previous loop; a failed start reports through the RPC, not idle): clear the latch, stay Starting, and keep waiting for listening or StartListeningTimeoutSeconds. Do not settle.
> Fold _awaitingIdleBeforePendingRelease into the latch if they duplicate (one mechanism).
> New checks, counted in the coverage line: both repros above (now released or deferred); latch set on listening and cleared on idle; recover clears the latch; idle-in-Starting ignored; start while latched per kind; pending released on idle after a transcript-settle; release revalidates (expired pending not started).
> Also carry these into Phase 5 wiring (and show them at the Phase 5 STOP):
> Decide admission on the snapshot taken before ApplyTranscript changes state.
> clarifyRequestOpenForSession must be computed for snapshot.ClarifyId (the bound id) and the current session, never "any clarify open".
> On ReleasePendingNow, revalidate gate, mode, !TurnRunning (non-clarify) and broker-open (clarify) before TryReleasePending. On expiry, reconcile wake as approved.

**Fix applied:** `HermesBusyUntilIdle` latch implemented; `_awaitingIdleBeforePendingRelease` removed; idle-in-Starting no longer settles.

## Phase 4 stuck-latch STOP (verbatim)

> Not "proceed to phase 5" yet. Claude reran his repros (both pass, and so do all your checks) and found one new liveness hole from the latch fix (record verbatim; approved at this STOP):
> Stuck latch. The latch is cleared only by idle or by recover_timeout, and recover_timeout runs only while _hasOutstanding. After a transcript-settle (no outstanding, latch held), a lost idle (for example a reconnect between transcript and idle; Cancel returns early with no stop, so Hermes never emits another idle) leaves the latch held forever. Repro: Wake → listening → TranscriptText → Cancel("session-ready") (NeedsHermesStop=false) → Tick to +1 h → BeginStart(Wake) = Rejected, latch=True. Zola is deaf until app restart.
> Fix, exactly:
> Add LatchIdleTimeoutSeconds = 65 (Hermes's longest TTS wait of 60 s, plus margin). When the latch is held and no capture is outstanding, arm a latch deadline. On expiry in Tick: clear the latch, log capture latch_recover, and set ReleasePendingNow if a pending start exists (the wiring revalidates). A later idle is a harmless no-op.
> Add CancelSettleTimeoutSeconds = 30. When a capture enters Cancelled (stop sent), its settle deadline is now + 30 s instead of 180 s. On expiry, settle as recover_timeout (same rules: never admits; the next Accepting needs its own listening). Keep 180 s for Starting/Accepting.
> New checks, counted in the coverage line: the stuck-latch repro now recovers at +65 s (wake begins after); latch_recover releases the pending start; a late idle after latch_recover is a no-op; a Cancelled capture with no idle settles at +30 s; Accepting still uses 180 s; after either recovery, a transcript before the next listening is dropped.

**Fix applied:** `LatchIdleTimeoutSeconds = 65`, `CancelSettleTimeoutSeconds = 30`; pending-start expiry is deferred while the latch is held so a deferred start can still release on `latch_recover`.

### Phase 5 wiring checklist (carry forward)

1. **Admission snapshot:** call `TranscriptAdmission.Decide` on the snapshot **before** `ApplyTranscript` changes state.
2. **Clarify open query:** `clarifyRequestOpenForSession` for `snapshot.ClarifyId` + current session only — never “any clarify open”.
3. **Pending release:** on `ReleasePendingNow`, revalidate gate, mode, `!TurnRunning` (non-clarify), broker-open (clarify) before `TryReleasePending`. On expiry, reconcile wake as approved.

## Check list and results (Phase 4)

Command: `dotnet run --project windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj`

Result: **PASS** (exit 0) after latch fix.

```
coverage: lifecycle rows 22/22, admission rows 13/13, start rows 9/9, invalid pairs 6/6, stop_phrase rows 4/4, amendments 7/7, latch rows 18/18
```

Repro checks (now PASS):
- `repro_clarify_deferred_released_after_transcript_idle`
- `repro_echoreopen_deferred_while_latched`
- `repro_stuck_latch_recovers_at_65s`

`project.assets.json`: `"libraries": {}`, `"net9.0": []` — no NuGet packages.

## Build output summary (Phase 4)

Command: `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`

Result: **Build succeeded.** 0 Warning(s), 0 Error(s). New `Voice/*.cs` compiled via SDK globbing. `VoiceController.cs` / `MainWindow.xaml.cs` unchanged.

## Purity scan (Phase 4)

Command: `Select-String` for `Microsoft.UI|Windows.|System.IO|DateTime.Now|DateTimeOffset.Now` on both pure files.

Result: **no matches** on `CaptureLifecycle.cs` and `TranscriptAdmission.cs`.

## Phase 5 notes (Brian, with Claude's review — verbatim)

> Stuck-latch fix verified independently (recovers at +65 s; Cancelled settles at +30 s).
> Record as a self-initiated deviation, accepted: "pending-start expiry paused while the latch is held". Accepted because TryReleasePending still rejects an expired start on release (verified: a follow-up deferred at +4 s is rejected as expired at the +68 s latch_recover).
> At the Phase 5 STOP, show explicitly:
> admission decided on the snapshot before ApplyTranscript;
> the clarify-open check scoped to snapshot.ClarifyId and the current session;
> revalidation on every ReleasePendingNow (gate, mode, !TurnRunning for non-clarify, broker-open for clarify) before TryReleasePending;
> where Tick is driven from (timer cadence; the UI-thread/lock model, so lifecycle calls are never concurrent);
> the G-ONE-AUTHORITY search results.

**Self-initiated deviation (accepted):** pending-start expiry is paused while `HermesBusyUntilIdle` is held.

## Phase 5 STOP wiring fixes (Brian / Claude — approved at STOP; verbatim)

> Three wiring fixes (approved at this STOP; record verbatim):
> Discard stale pending starts.
> (a) Add a pure CaptureLifecycle.DiscardPending(reason) that logs capture start_discarded kind=… reason=….
> (b) Cancel(...) discards a pending FollowUp/EchoReopen (it belongs to the cancelled window). A pending Clarify is kept; it is governed by broker revalidation.
> (c) ReleasePendingStartAsync calls DiscardPending on every revalidation failure (gate/mode/availability, turn, clarify), instead of logging "expired" and leaving it queued.
> Keep P2-D06's stale guard. PendingStart records the follow-up generation at deferral time. Release passes that generation to StartCaptureAsync (not the current one), so the existing generation check rejects a stale follow-up.
> Deferred is not failure. StartCaptureAsync returns its StartDisposition (or an equivalent outcome). OpenClarifyAnswerCaptureAsync and any other caller that checks CaptureActive after a start treat Deferred/SupersededAndDeferred as pending: no clarify-capture-failed, no cancel or stop. Only Rejected or an RPC failure is a failure.
> Checks: add rows for DiscardPending, Cancel discarding a pending FollowUp/EchoReopen but keeping Clarify, and the deferral generation carried on PendingStart (counted in coverage).
> Phase 7 addition: during S4, confirm from voice-timeline.log that no wake resume happens at turn start (OnTurnStarted → InvalidateCapture → CancelFollowUp → SetSpeaking(false) churn).
> Accepted as-is, for the record: InvalidateCapture sends stop on latch or recorder-state hints as well as outstanding captures (a stop on idle Hermes is a no-op, VA-G2).

**Accepted as-is:** `InvalidateCapture` may send stop on latch / recorder-state hints (idle Hermes stop is a no-op, VA-G2).

## Phase 5 STOP — release handoff bug (Brian / Claude — approved at STOP; verbatim)

> Critical: released pending starts never send voice.record start. ReleasePendingStartAsync calls TryReleasePending (which runs BeginFresh; the capture is now Starting/outstanding), then StartCaptureAsync, which calls BeginStart again. That sees the outstanding capture as busy and re-defers (FollowUp/EchoReopen) or supersede-cancels (Clarify). Repro against the current lifecycle: FollowUp → listening → TranscriptText → EchoReopen Deferred → idle (release) → TryReleasePending = Began/Starting → BeginStart(EchoReopen) = Deferred → at +7 s start_no_listening … start_discarded. Impact: every echo-reopen (P2-D14) and every deferred follow-up or clarify answer silently never listens.
> Fixes:
> Split StartCaptureAsync into (a) the lifecycle decision (BeginStart) and (b) SendRecordStartAsync(beginResult, kind, generation, clarifyId): wake pause, the RPC, the success/failure handling, and the existing post-await generation checks. Normal starts run (a) then (b). The release path runs revalidation → the generation-staleness check (P2-D06) before TryReleasePending → TryReleasePending → (b) only. Never call BeginStart twice for one start.
> Every exit after Began settles the lifecycle. Add pure CaptureLifecycle.MarkStartSent(gen) (called immediately before the record-start RPC) and AbortUnsentStart(gen, reason) (Starting and not sent → Settled immediately, no stop, no latch). Cancel on a Starting capture whose start was not sent settles immediately (no stop, no 30 s wait). In (b):
> stale generation before the RPC → AbortUnsentStart;
> stale generation after the RPC (Hermes may be recording) → the one cancel method (invalidate + stop);
> busy/error → NoteStartRpcFailed (as now).
> Checks (pure, counted in coverage): release handoff (TryReleasePending Began → no second BeginStart path exists; assert via an API that takes the release result); AbortUnsentStart → Settled, latch not set, a wake start begins immediately after; Cancel on Starting-unsent settles immediately; Cancel on Starting-sent → Cancelled with stop.
> Code-walk table at the STOP: every return in StartCaptureAsync/(a)/(b) and ReleasePendingStartAsync, with the lifecycle state it leaves behind (must never be "Starting with no RPC in flight" or "Hermes recording with no Cancelled owner").

## Phase 5 STOP — wiring review

### Diff summary (plain English)

| File | Change |
|---|---|
| `Voice/CaptureLifecycle.cs` | Pure lifecycle + latch; `DiscardPending`; Cancel drops FollowUp/Echo pending (keeps Clarify); `PendingStart.FollowUpGeneration` |
| `Voice/TranscriptAdmission.cs` | (from Phase 4) pure admission |
| `VoiceController.cs` | Lifecycle wire; admit before ApplyTranscript; Release discards on revalidate fail; release uses deferral gen; `StartCaptureAsync`→`StartDisposition`; clarify treats Deferred as pending |
| `MainWindow.xaml.cs` | Removed unbound→newest-clarify; broker query remains id+session scoped |
| `Zola.Client.Checks/` | Exhaustive tables + wiring rows 5/5 |

### Explicit STOP items

1. **Admission before ApplyTranscript:** `OnVoiceTranscript` snapshots `_lifecycle.Snapshot()`, calls `TranscriptAdmission.Decide(...)`, then `ApplyTranscript`.
2. **Clarify-open scoped:** `clarifyOpen = snap.Kind == Clarify && _clarifyCaptureStillValid(snap.ClarifyId)` — MainWindow delegate checks `GetState(id)==Open` and session == `_chat.SessionId`.
3. **ReleasePendingNow revalidation:** `ReleasePendingStartAsync` checks gate/mode/available, `!TurnRunning` for non-clarify, broker-open for clarify; on failure **`DiscardPending`** (not leave queued); then `TryReleasePending`. Expiry → wake reconcile. Release uses **deferral-time** `FollowUpGeneration` (P2-D06).
4. **Tick:** `System.Threading.Timer` every **1000 ms** → `OnLifecycleTick` → `lock (_lifecycleGate) { Tick }`. All lifecycle mutations take `_lifecycleGate`. No UI-thread affinity required; never concurrent lifecycle calls.
5. **G-ONE-AUTHORITY:**
   - `TranscriptAdmission.Decide`: **one** site (`VoiceController.cs` OnVoiceTranscript).
   - Cancel: **`InvalidateCapture` / `InvalidateAndStopCaptureAsync`** — typed submit, session ready, app close, turn start, stop speaking, gate, mode-text, mic stop, interrupt, question-speak, echo-limit, clarify-fail, turn non-complete.
   - MainWindow: **no** admission logic; newest-clarify fallback **gone** from `OnTranscriptReady`.
   - VA-G6: voice → submit still only `TranscriptReady` → `OnTranscriptReady`.

### Checks / build (after release-handoff fix)

- Checks: PASS — `coverage: lifecycle rows 22/22, admission rows 13/13, start rows 9/9, invalid pairs 6/6, stop_phrase rows 4/4, amendments 7/7, latch rows 18/18, wiring rows 9/9`
- Build: succeeded to `%TEMP%\zola-p7-build-verify2`, 0 Warning(s), 0 Error(s).
- No deploy yet.

### Code-walk — StartCaptureAsync / SendRecordStartAsync / ReleasePendingStartAsync

| Exit | Lifecycle left behind |
|---|---|
| **StartCaptureAsync (a)** | |
| gated / no session / stale gen (before BeginStart) | unchanged (Settled or prior) |
| BeginStart → Rejected | unchanged busy/reject; no new Starting |
| BeginStart → Deferred / SupersededAndDeferred | pending queued; prior Cancelled if supersede (+ stop if NeedsHermesStop) |
| BeginStart → Began → (b) | see SendRecordStartAsync |
| **SendRecordStartAsync (b)** | |
| stale / wake-stale after pause (before MarkStartSent) | `AbortUnsentStart` → **Settled**, no latch, no stop |
| MarkStartSent + RPC busy/error | `NoteStartRpcFailed` → **Settled**, no latch |
| stale after RPC | `InvalidateAndStop` → **Cancelled** (+ stop) then settle path |
| RPC ok | **Starting** + `_startSent`, waiting for `listening` |
| **ReleasePendingStartAsync** | |
| no pending / revalidate fail / stale gen (before release) | `DiscardPending` → no outstanding; pending cleared |
| TryReleasePending not Began (expired) | pending cleared; Settled |
| TryReleasePending Began → (b) only | same as SendRecordStartAsync rows (never second BeginStart) |

### Smoke script (Phase 7) — expected log lines

| Step | Expect |
|---|---|
| S1/S2 typed during follow-up | `capture cancel` → `capture stop_sent` → `transcript drop reason=cancelled` (S1 hit Starting; S1b proves Accepting→forced drop) |
| S1b cancel while Accepting | FollowUp Accepting before cancel; `typed-submit` → stop_sent; `transcript drop reason=cancelled` → idle → Settled; +1 wake user +1 typed user only |
| S3 Stop speaking | cancel/stop; drops if any transcript; no follow-up open |
| S4 ordinary follow-ups | `transcript admit` + submit once each; **also confirm no wake resume at turn start** (`OnTurnStarted` → `InvalidateCapture` → `CancelFollowUp` → `SetSpeaking(false)` churn) in `voice-timeline.log` |
| S5 voice clarify | `transcript admit` with clarify id; `server-requests` answered |
| S6 mode Text during follow-up | cancel/stop; no stray user turn |
| S7 lock gate | gate cancel/stop; nothing submitted |
| S8 genuine stop | `transcript admit` then Voice chat ended / resync |

## Phase 6 notes (Brian, with Claude's review — verbatim)

> the release handoff fix was verified independently. The repro now gives Deferred → idle release → Began (once) → MarkStartSent → listening → Accepting; AbortUnsentStart → Settled with no latch and no stop, and a wake starts immediately; Cancel on Starting-unsent settles immediately. Checks: coverage including wiring 9/9 confirmed.
> Phase 6 reminders: the client must be fully closed first (bin\ was locked). Confirm whether the two python.exe serve processes are parent and child (uv launcher plus venv python), not two serves. Record PIDs and start times before and after.

## Deploy record

### Before close (Phase 1 baseline still running)

| Process | PID | Start | Parent | Notes |
|---|---|---|---|---|
| `dotnet.exe` (run Zola.Client) | 9748 | 2026-10-05 19:29:15 | — | |
| `Zola.Client.exe` | 20468 | 2026-10-05 19:29:35 | 9748 | |
| `python.exe` (venv) | 16456 | 2026-10-05 19:29:38 | 20468 | `-m hermes_cli.main -p zola serve --isolated` |
| `python.exe` (uv cpython) | 12352 | 2026-10-05 19:29:38 | **16456** | same serve cmdline |

**Serve parent/child:** confirmed — 12352's parent is 16456 (venv python → uv cpython child). Not two independent serves.

### Close

Stopped 9748 / 20468. Verified baseline PIDs **9748, 20468, 16456, 12352 all exited**. No leftover `Zola.Client` / hermes serve.

### Build

- Command: `dotnet build windows-client/Zola.Client/Zola.Client.csproj -c Debug` (then `--no-incremental` for deploy timestamp)
- Output: `windows-client/Zola.Client/bin/Debug/net9.0-windows10.0.19041.0\Zola.Client.exe` (+ `.dll`)
- EXE/DLL LastWriteTime: **2026-10-06 08:38:48** local
- Result: Build succeeded, 0 Warning(s), 0 Error(s)

### After relaunch (`dotnet run --project …\Zola.Client.csproj --no-build`)

| Process | PID | Start | Parent | Notes |
|---|---|---|---|---|
| `dotnet.exe` (run) | 2748 | 2026-10-06 08:38:58 | — | |
| `Zola.Client.exe` | 19612 | 2026-10-06 08:38:59 | 2748 | after build timestamp |
| `python.exe` (venv) | 19676 | 2026-10-06 08:39:00 | 19612 | serve |
| `python.exe` (uv cpython) | 3992 | 2026-10-06 08:39:00 | **19676** | serve child |

**Serve parent/child after:** confirmed again (3992 ← 19676). Exactly one client + one serve pair.

### Live log evidence (new binary)

`voice-timeline.log` after offset 823024 includes:
- `wake reconcile noop …`
- `wake.start attempt=1 … ok=True started=True`

### Smoke baseline log offsets (Phase 7)

| Log | Bytes | mtime |
|---|---|---|
| `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` | **823780** | 2026-10-06 08:39:15 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\agent.log` | **4299146** | 2026-10-06 08:39:16 |

## Smoke results

### Phase 7 notes (Brian — verbatim)

> In S1, confirm that the new capture lifecycle … / transcript admit|drop … lines appear (first live evidence of the new authority). During S4, also check that no wake resume happens at turn start.

**S1 extra gate:** first live evidence of `capture lifecycle …` and `transcript admit|drop …` in `voice-timeline.log`.  
**S4 extra gate:** no `wake.resume` at turn start (`OnTurnStarted` → invalidate → `CancelFollowUp` → `SetSpeaking(false)` churn).

### Part A — pre-smoke

| Check | Status |
|---|---|
| External dictation tool off | **Yes** (Brian 2026-10-06 ~10:53) |
| P2-D16 setup holds | **Yes** (Brian 2026-10-06 ~10:53); see mic-silence note below |
| Voice mode on | **yes** — wake listening after reconnect |
| New session open | **yes** — Brian: `session: b2cd93629` (log/UI short id `b2d93629`) |
| `state.db` agent session row | bound on first turn → `20261006_084852_f8a7fa` |
| `state.db` user-message count (this session) | **0** at Part A freeze; **16** after S1–S8 |
| `zola_memory.pending_turns` count | **0** at Part A freeze; **11** after S1–S8 |
| Smoke log baseline `voice-timeline.log` | 823780 (Phase 6); **S1 window start offset: see below** |
| Smoke log baseline `agent.log` | 4299146 (Phase 6) |

**Mic-silence warnings (08:49–08:52):** `agent.log` `tools.wake_word` WARN `mic delivers only silence (peak<=10 for 10s)` on `Microphone Array (Realtek(R) Au` (MME) at **08:49:23**, **08:50:44**, **08:51:14**, **08:52:02**, **08:52:41** (interleaved with `mic audio detected - stream healthy`). Post-reconnect wake path; did not block S1+.

**Mid-smoke client restart (PID 9228 @ 08:48:48, same Phase 6 build EXE 08:38:48):** After Part A still showed deploy client **19612** / serve **19676→3992**, Brian opened the new smoke session. Logs show rapid WS flaps (`client_disconnect` 1006 @ 08:47:30 / 08:47:46 / 08:47:52) under that process, then `wake reconcile unreachable Backend unreachable` @ **08:48:18** and **08:48:35**, then fresh **Zola.Client 9228** @ **08:48:48** with a new serve bootstrap (plugin registration @ 08:48:50). Smoke S1+ ran entirely on **9228** (same build; not a rebuild).

**S1 log window start:** `voice-timeline.log` @ **827195**; `agent.log` @ **4316014**.

### S1 — PASS

- UI session (actual): `b2d93629` (Brian wrote `b2cd93629`; log uses `b2d93629`)
- Agent session: `20261006_084852_f8a7fa`
- Voice window: offset 827195 → 837191

| Expect | Actual |
|---|---|
| First live `capture lifecycle` / `transcript admit\|drop` | **Yes** — Wake lifecycle + `transcript admit`; FollowUp `capture cancel` / later `transcript drop reason=echo` |
| `capture cancel` → stop (typed during follow-up) | **Yes** — gen=2 FollowUp `Starting→Cancelled` `reason=typed-submit` → `capture stop_sent` (~187 ms after start; still Starting, so no late transcript) |
| `transcript drop reason=cancelled` | **N/A** — no transcript after cancel (cancel before Accepting) |
| No extra user message / no User correction | **Yes** — users=2 (wake+typed), assistants=2; no `User correction` |
| `pending_turns` | 2 (matches scripted turns) |

**S2 log window start:** voice **837191**, agent **4324505**.

### S2 — PASS

Voice window: 837191 → 844087.

| Expect | Actual |
|---|---|
| Type at/before beep cancels follow-up | **Pre-beep:** typed whales @ 08:56:41.55; FollowUp gen=6 only started @ 08:56:54 (after that turn). No `typed-submit` cancel needed |
| No stray voice user turn | **Yes** — FollowUp Accepting→Settled idle; no `transcript admit` on gen=6 |
| Message delta | users 2→**4**, asst 2→**4** (+dolphins wake + whales typed); `pending_turns` **4** |
| User correction | none |

**S3 log window start:** voice **844087**, agent **4330675**.

### S3 — PASS

Voice window: 844087 → 849057.

| Expect | Actual |
|---|---|
| Stop speaking mid-reply | `stop_speaking requested` @ 08:58:36; playback interrupted |
| No follow-up opens | **Yes** — `cancel_follow_up` with `followUpStarted=False`; no FollowUp `capture lifecycle … Starting` after stop |
| Transcripts dropped if any | None after stop (no admit/drop needed) |
| Message delta | users/asst 4→**5** (lighthouse turn only); `pending_turns` **5** |

**S4 log window start:** voice **849057**, agent **4335099**.  
S4 also: confirm **no `wake.resume` at turn start** (only skipped/noop reconcile).

### S4 — PASS (hard gate)

Voice window: 849057 → 876569.

| Expect | Actual |
|---|---|
| Follow-up answers admitted + submitted once each | **7** `transcript admit` = **7** `prompt accepted`; **0** drops |
| No genuine answer dropped / follow-up failed to open | **None**; FollowUp gens 9–14 all Starting→Accepting→admit |
| Instant-at-beep | gen=14 admit len=9 (`One more.`) — opens/listens/admits (known ~1 s clip not a fail) |
| No `wake.resume` at turn start | **Confirmed** — only `wake.resume reason=follow-up-end` @ end of block; **zero** `turn-start` resume lines in window |
| Message delta | users 5→**12** (+7); `pending_turns` **7** |

Note: after the first Hey Zola, later prompts were chained as FollowUp captures (one wake.detected in S4). Still satisfies admit-once hard gate.

**S5 log window start:** voice **876569**, agent **4363534**.

### S5 — PASS

Voice window: 876569 → 883795.

| Expect | Actual |
|---|---|
| Voice clarify path | Clarify gen=17 `Clarify(srq-8bfcf564d717)` Starting→Accepting→Settled |
| Bound admit | `transcript admit … clarify=srq-8bfcf564d717 len=20` bound=srq-8bfcf564d717 |
| `server-requests.log` answered | `answered id=srq-8bfcf564d717 method=clarify session_id=b2d93629` |
| AUD-33 plain text | **No** — real clarify used |

**S6 log window start:** voice **883795**, agent **4370163**.

### S6 — PASS

Voice window: 883795 → 887356.

| Expect | Actual |
|---|---|
| Fun-fact wake admit | gen=19 Wake admit len=19 → one `prompt accepted` |
| Mode → Text after beep | `mode=text` @ 09:53:23; then wake re-arm on Voice restore |
| No stray user turn | **Yes** — users 13→**14** only; no FollowUp admit after switch |

**S7 log window start:** voice **887356**, agent **4374579**.

### S7 — PASS

Voice window: 887356 → 891905.

| Expect | Actual |
|---|---|
| Lock during/after Peru turn | `gate fact: locked=true` → cancel follow-up → toggle off → wake.stop |
| Nothing submitted while gated | **Yes** — only Peru wake admit; no post-lock `prompt accepted` / FollowUp admit |
| Unlock restores voice | gate opened → toggle on/tts → wake re-arm `ok=True` |
| Message delta | users 14→**15** (Peru only) |

**S8 log window start:** voice **891905**, agent **4378447**.

### S8 — PASS

Voice window: 891905 → 896608.

| Expect | Actual |
|---|---|
| Count wake admit | gen=21 Wake admit len=19 |
| Genuine “stop” after beep | gen=22 FollowUp transcript `stop=true` → **`transcript admit`** len=4 |
| Voice chat ends / wake restored | `fireOrCancel=voice.transcript followUpStarted=False`; display → Idle + “Hey Zola”; `wake.resume reason=capture-idle` |

### Part C — whole smoke window (offsets 827195 → 896608)

| Check | Result |
|---|---|
| Zero admits with cancelled/settled/absent owner | **Yes** — 16 admits; **1** drop (`reason=echo` only, S1 post-typed TTS) |
| `no_bout_estimate` / `forced_estimate` / fallback question_release | **1** `no_bout_estimate` (S8); **0** `forced_estimate`; **1** `question_release rule=monitor` (S5 clarify). Estimate did **not** open capture during bout — monitor fired after `bout_stop`, then FollowUp start |
| `zola_memory` pending | **11** pending rows all `session_id=20261006_084852_f8a7fa` (users=16; extras include skill/tool turns not all held as pending) |
| `hermes-agent` | HEAD `345cd2b0…`, porcelain **empty** |
| Live profile | No track edits; `config.yaml` / `SOUL.md` hashes recorded at close of smoke (unchanged by this track) |

**Verdict (S1–S8): smoke test passed.** S1b added before closeout (forced-transcript drop not yet live-proven).

### Added smoke — S1b (Brian / Claude — record verbatim)

> Not "proceed to closeout" yet. One added smoke step (Brian, with Claude's review; record verbatim):
> S1b — cancel while Accepting (the E1/E2 path). S1 cancelled at Starting (+187 ms), and S2 typed pre-beep, so the forced-transcript drop is not yet proven live. Brian: "Hey Zola, tell me a fact about the moon." After the follow-up beep, he waits ~2 s, starts speaking ("um, actually let me type this…"), and while still speaking types and sends "And one about Mars."
> Expect:
> the FollowUp capture went Accepting before the cancel;
> capture cancel reason=typed-submit from Accepting → capture stop_sent;
> Hermes transcribing → a voice.transcript → transcript drop reason=cancelled → idle → Settled;
> state.db: +1 user (the moon question via wake) +1 user (the typed Mars line) only, with no user message containing the spoken fragment, and no User correction during the turn.
> If Hermes returns no transcript (empty audio), record that, and have Brian repeat once, speaking a bit longer before sending.
> Also record, for Part A:
> Brian's confirmation (dictation tool off; P2-D16 setup) — he will reply;
> the mic-silence warnings at 08:49–08:52;
> the reason for the mid-smoke client restart (PID 9228 @ 08:48:48, same build).

**S1b log window start (attempt 1):** `voice-timeline.log` @ **896608**; `agent.log` @ **4387773**.  
**S1b `state.db` baseline (session `20261006_084852_f8a7fa`):** users=**16**, assts=**19**, User-correction-like=**0**.

### S1b attempt 1 — INCOMPLETE (no forced transcript; Hermes unreachable after)

Voice window: 896608 → 904114. Part A confirmations: dictation **Yes**, P2-D16 **Yes**.

| Expect | Actual |
|---|---|
| FollowUp Accepting before cancel | **Yes** — gen=24 Starting→Accepting (@10:52:24.48) then Accepting→Cancelled typed-submit (@10:52:30.84) |
| `typed-submit` → `capture stop_sent` | **Yes** |
| `transcript drop reason=cancelled` | **No** — no `voice.transcript` for gen=24. Hermes wrote WAV `recording_20261006_105230.wav` (5.8s) on silence auto-stop, then client stop; no Transcribed line; Cancelled→Settled on `idle` |
| state.db +1 moon +1 Mars only | **Yes** — users 16→**18**, assts 19→**20**; flags moon+mars only; User-correction-like=**0** |
| Hermes health | Serve pair **gone** after Mars turn start (@10:52:31); client still 9228 with `backend=false` @10:52:37 |

**Action:** one protocol repeat (speak longer before send). Restart client+serve (same Phase 6 build) required first.

**Relaunch for attempt 2 (same build EXE 08:38:48):** stopped orphaned 9228; `dotnet run --no-build` → Zola.Client **18452** @ 10:54:29, serve **3052→25004** (parent/child confirmed).

**S1b attempt 2 log window start:** voice **904870**, agent **4415612**.  
*(Note: relaunch opened a new UI session `4bea92b2` / agent `20261006_105433_533d74` — attempt 2 measured there; old smoke session users stayed at 18.)*

### S1b attempt 2 — PASS (E1/E2 forced-transcript drop)

Voice window: 904870 → 912170. Client **18452**, serve **3052→25004**.

| Expect | Actual |
|---|---|
| FollowUp Accepting before cancel | **Yes** — gen=2 Starting→Accepting (@10:57:43.36) then Accepting→Cancelled `typed-submit` (@10:57:49.30) |
| `typed-submit` → `capture stop_sent` | **Yes** |
| Hermes transcript → `transcript drop reason=cancelled` → Settled | **Yes** — transcript len=30 while Cancelled → `transcript drop reason=cancelled gen=2` → Settled on `transcript` |
| state.db +1 wake +1 typed only; no spoken fragment; no User correction | **Yes** — session `20261006_105433_533d74` users=**2** / assts=**2** (moon + Mars flags only); corr=**0** |

**S1b verdict: PASS.** Part A dictation/P2-D16 confirmed Yes/Yes; mic-silence + mid-smoke restart reasons recorded above.

**Verdict: smoke test passed** (S1–S8 + S1b).

## Phase 8 — Closeout

### Pre-verification record (Brian / closeout — verbatim where marked)

**Part A (Brian, verbatim):** dictation tool off: "Yes"; P2-D16 setup unchanged: "Yes".

**Mid-smoke client restart:** PID **9228** @ 08:48:48, same P7 build (EXE LastWriteTime 08:38:48). Reason (from logs): after Part A still showed deploy client 19612, rapid WS `client_disconnect` 1006 flaps @ 08:47:30 / 08:47:46 / 08:47:52, then `wake reconcile unreachable Backend unreachable` @ 08:48:18 and 08:48:35; fresh client 9228 + serve bootstrap @ 08:48:48–50. Smoke S1–S8 ran on 9228.

**S1b relaunch:** after attempt-1 serve death, client relaunched (same build) → Zola.Client **18452** @ 10:54:29, serve **3052→25004**. Attempt 2 on new session **UI `4bea92b2` / agent `20261006_105433_533d74`** (old smoke session users stayed at 18).

**Mic-silence warnings 08:49–08:52:** observed in `agent.log` (`tools.wake_word` WARN `mic delivers only silence (peak<=10 for 10s)` at 08:49:23, 08:50:44, 08:51:14, 08:52:02, 08:52:41). **Not caused by Track 1** — wake-device / PortAudio input health on the post-reconnect path; Track 1 did not change Hermes, wake config, or live profile.

**S1b result:** cancel from Accepting (gen=2, typed-submit) → stop_sent → transcript drop reason=cancelled (len=30) → Settled; state.db +1 moon +1 Mars only.

### 8a — Verify

| Check | Result |
|---|---|
| `dotnet build` Zola.Client Debug | **PASS** — 0 Warning(s), 0 Error(s) |
| `dotnet run` Zola.Client.Checks | **PASS** — exit 0; coverage lifecycle 22/22, admission 13/13, start 9/9, invalid 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9 |
| Exit Criteria Verification | see table below |

### 8b — hermes-agent + live profile

| Check | Result |
|---|---|
| hermes-agent HEAD | `345cd2b057a452236de401d3534b8502a7465e8d` |
| hermes-agent porcelain | **empty** |
| Live profile (closeout hashes; track made no edits) | `config.yaml` SHA-256 `7BA2E676A04FF92047C8D711FCB022BE8A532B11BAAC6F74B08986744E704570`; `SOUL.md` SHA-256 `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49`; `plugins/**` aggregate SHA-256 `82db44e1e51dce2d6adf0694210dc4391db2efc97b250f3ebd83e14f6a1b630d` |

### Exit Criteria Verification (PHASE7_BUILD_PLAN.md Track 1)

| Criterion | Verdict | Evidence |
|---|---|---|
| VA-G1–G9 answered; frozen terminal set + STOP verdicts recorded | ✅ MET | Progress VA-G1–G11 + Phase 3 STOP; terminals: transcript text / stop_phrase / no_speech_limit settle admission; idle required before next Accepting; cancel **A** |
| Build passes; all checks pass (listed cases) | ✅ MET | Build 0/0; Checks PASS coverage incl. wiring 9/9 |
| CURSOR-RUN: one cancel-stop path; MainWindow no admission; newest-clarify gone; one submit route (VA-G6) | ✅ MET | `InvalidateCapture` + `SendRecordStopAsync` (wrapper `InvalidateAndStopCaptureAsync`; `OnTurnStarted` same pair inline); `TranscriptAdmission.Decide` only in `VoiceController.OnVoiceTranscript`; MainWindow newest-clarify removed (P7-D05 comment); no second submit |
| HUMAN-RUN S1 | ⚠️ PARTIAL | S1: cancel→stop_sent from Starting (+187 ms); drop N/A; no extra user / no User correction. Full Accepting→drop chain in **S1b** ✅ |
| HUMAN-RUN S1b (added; E1/E2) | ✅ MET | Accepting gen=2 typed-submit → stop_sent → `transcript drop reason=cancelled` len=30 → Settled; +1 moon +1 Mars only (session `20261006_105433_533d74`) |
| HUMAN-RUN S2 | ✅ MET | Pre-beep typed; no stray voice user turn; users 2→4 |
| HUMAN-RUN S3 | ✅ MET | Stop speaking; no follow-up open; no late transcript |
| HUMAN-RUN S4 (hard gate) | ✅ MET | 7 admits = 7 prompt accepted; no wake.resume at turn start |
| HUMAN-RUN S5 | ✅ MET | Clarify bound admit + server-requests answered |
| HUMAN-RUN S6 | ✅ MET | Mode Text during follow-up; no stray user turn |
| HUMAN-RUN S7 | ✅ MET | Lock cancel; nothing submitted; unlock restores |
| Prompt S8 (stop-phrase admit + voice chat end) | ✅ MET | FollowUp `stop=true` → admit; wake restored |
| Whole-window: zero bad admits; drops reasoned; estimate/bout | ✅ MET | 16 admits S1–S8; drops: echo (S1) + cancelled (S1b); 1× no_bout_estimate no mid-bout capture |
| Memory pending/consolidation counts vs scripted | ⚠️ PARTIAL | pending_turns=11 vs users=16 on smoke session (skill/tool/consolidation extras); recorded at Part C; no bad voice admits |
| hermes-agent clean at pin; live profile unchanged | ✅ MET | HEAD `345cd2b0…`, porcelain empty; hashes above; no track profile edits |

**All blocking criteria met (PARTIAL items acknowledged at smoke / closeout).** Smoke S1–S8 + S1b: **PASS**.

### Upstream note (lore-closeout input — P7-D13)

Filed for later lore closeout (no Hermes edit this track):

1. **No `voice.record cancel` today.** Mechanism A uses `voice.record stop`, which force-transcribes. Upstream ask (Phase 3, verbatim):  
   > Add `voice.record cancel`, which ends the active recording without transcription and emits an unambiguous terminal event or correlation token.
2. **No capture ID on `voice.transcript`.** Wire carries only `text` / `stop_phrase` / `typed` / `no_speech_limit`. Client ownership is generation + lifecycle state; AUD-23 window times alone are insufficient. Upstream: add a capture/correlation id on start and on every transcript/status terminal for that capture.

### Final file list (8d)

**New:**
- `windows-client/Zola.Client/Voice/CaptureLifecycle.cs`
- `windows-client/Zola.Client/Voice/TranscriptAdmission.cs`
- `windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj`
- `windows-client/Zola.Client.Checks/Program.cs`
- `windows-client/Zola.Client.Checks/.gitignore`
- `zola-architecture/lore/prompts/progress/P7-VOICEAUTH_Progress.md`

**Modified:**
- `windows-client/Zola.Client/VoiceController.cs`
- `windows-client/Zola.Client/MainWindow.xaml.cs`

**Not modified:** `TtsPlaybackMonitor.cs`, ChatSocket, ServerRequestBroker, hermes-agent, live profile, lore (except this progress doc).

### Closeout SHAs

| Item | SHA |
|---|---|
| Plan commit | `b5583f97c3e13870abc5d483ec23566458cd828e` |
| Plan merge (= p7-voiceauth base) | `ffef6f050a3fd6a8092d77fc055370296e2b522b` |
| Implementation (8e) | `f34bd9bee4b9f4faa67655e845c1b05f61389ad4` |
| Merge on main (8h `--no-ff`) | *(filled after 8h)* |
| Final main HEAD (after 8i metadata) | *(filled after 8i)* |
