# ZW Phase 7 Build Plan
## Voice She Can Trust: Transcript Authority, Conversational Clarify, Measured Latency, Voice Prose

**Base branch:** `main`
**Base SHA:** `c25899111c68ea37798c08f08aebdeee6653725a` (`main` tip after the P7PRE closeout).
Record the actual tip at plan commit. Each track records the actual HEAD it branches from.
**Audit:** P7PRE. Audit content `044fe10a857edc364b0fa69cd2f72be5f45067d8`, merged at
`3e87e7c47ed2eee4a26f53dc9c4bba7d6f16b1ee`. Documents are in `zola-architecture/audit/p7pre-phase7/`.
26 findings: 4 HIGH, 11 MEDIUM, 3 LOW, 8 MATCH. LEADs: 5 confirmed, 2 partly.
**Decisions:** P7-D01–D13, locked 2026-10-05 (Brian: "approved."; S34: "Yes. keep S34"). Full text
in **Appendix A**.

**Theme:** Make voice trustworthy before making it faster or richer. This phase:
- gives the client **one authority** that decides whether a transcript is Brian's words, so that
  Zola's own speech can never become his turn (`S45`; `S37` closes into it);
- makes a single clarify question in Voice mode **conversational**, with no card and the choices
  spoken (`S44`);
- **measures and then fixes** the largest proven cause of the wait between Brian finishing and
  Zola speaking (`S38`);
- checks Hermes's voice-live note against Zola's Edge setup, and adopts it only if it fits
  (`S34`; cuttable).

This phase does **not**:
- edit Hermes (`hermes-agent` stays read-only at `v2026.9.14` / `345cd2b0…`);
- install anything without an explicit developer approval at a STOP (`P2-D17`);
- turn barge-in on (`P4-D28` stands; `S36` stays upstream-gated);
- change approvals (`P4-D07`, `P4-D27` stand);
- change the Whisper model, beam size or `silence_duration` without new evidence (P7-D10);
- un-anchor or re-scope the echo matcher (P7-D07);
- clean memory (P7-D11);
- touch `S46`–`S50`, `S35` scopes, `S40`, `S28`, `S39` or `S21`.

---

## Phase 7 Overview

| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 (`P7-VOICEAUTH`) | Transcript authority | Grounding of the Hermes capture lifecycle; one admission authority in `VoiceController`; cancel = invalidate + stop; serialized captures with a proven end; turn-running and clarify rules; the monitor outranks the estimate; drop logging; a dependency-free check project for the pure logic | Medium-Large |
| 2 (`P7-CLARIFY`) | Clarify by voice | A single clarify question in Voice mode has no card and no panel opening, and the choices are spoken; batch and multi-select keep the card; mode switches mid-question; Text mode and approvals unchanged | Medium |
| 3 (`P7-LATENCY`) | Measure, then fix | Per-turn stage timing (client logs + existing Hermes logs); the STT gap probe (AUD-26); the investigation of tool use on simple questions (AUD-25); STOP; fix the largest proven cause; remeasure | Medium |
| 4 (`P7-VOICEPROSE`) | Voice prose (cuttable) | Capture and evaluate the exact `voice_live_turn_note`; STOP; adopt for admitted voice turns only, or reject | Small-Medium |

**Sequencing rule:** strictly **1 → 2 → 3 → 4**. Each track merges and passes its smoke test before
the next begins.
- Track 1 is first. Nothing else is trustworthy until her voice cannot become Brian's turn.
- Track 2 depends on Track 1. A cardless clarify answer is only safe if the answer capture is
  provably Brian's (P7-D09, depends on D01–D06).
- Track 3 follows. Its timing logs also give Track 4 its latency check.
- Track 4 is last and **cuttable**. If the phase runs long, it moves to the defers table at the
  lore closeout, with its grounding results recorded.

**Build command (client tracks):** `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`.
**Check command (Track 1 onward):** `dotnet run --project windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj`
(introduced in Track 1; see the cross-cutting section).
**Plugin test command (Track 3, only if a plugin changes):**
`C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m unittest discover -s hermes-plugins\<plugin>\tests -t hermes-plugins\<plugin>`.

Smoke tests on the live client remain the acceptance criteria. Cursor does every non-interactive
step and reads every log. Brian only speaks or types the scripted turns and judges tone, accuracy
and feel. Cursor never injects turns. Live steps run one at a time (G-LIVE). Before any voice step,
Cursor confirms with Brian that the external dictation tool is off and that the P2-D16 setup holds
(lid open, mic 100, enhancements ON, speakers about 15).

---

## Grounding summary (established by P7PRE; cite, do not re-derive)

**The echo path (Audit 01, 02, 07)**
- `CancelFollowUp` (`VoiceController.cs` L2128–2157) clears the window's flags but **never** sends
  `voice.record stop`. Typed submit, Stop speaking, mode change and session ready all leave Hermes
  recording (AUD-02). Only the system gate stops the capture.
- That orphan capture hears her next reply. Its transcript arrives with `_followUpCaptureStarted` and
  `_followUpEchoPending` false, so the echo check (L1940) is skipped. `TranscriptReady` →
  `MainWindow.SubmitTurnAsync` (L394–430) then submits it as a whole turn, or mid-turn as a busy
  `interrupt` redirect (`User correction during the turn:`, `agent/turn_iteration_prep.py`
  L318–325) (AUD-05, AUD-09).
- Reproduced live twice (L-3 Runs A and B, session `20261005_192949_1f4302`): whole-turn echoes,
  overlap ratio 1.000. It also explains E1 and E2 (session `20261004_213345_e1ca3d`).
- `voice.record stop` always force-transcribes. A cancel without a transcript exists only on
  non-RPC paths (`/voice off`, `voice.toggle` off) (AUD-01).
- Hermes `voice.transcript` carries **no capture ID** (`events.py` L617–623). Client-driven
  records use `auto_restart=False` (`methods_voice.py` L752). The client's capture-window
  bookkeeping can be stale against Hermes's real recording (AUD-23, L-3 Run B).
- Today there are several partial deciders and no single authority (AUD-08): Hermes filters, the
  `OnVoiceTranscript` gate/stop/no-speech/echo checks, `MainWindow.OnTranscriptReady` routing, and
  Hermes busy handling.

**The echo matcher (H-2)**
- End-anchored, last 20 words, ≥3-word run, ≥60%. Drop rates: head-4/8 and middle-8 0/31; tail-8
  31/31; Brian quoting her last 6 words 31/31; synthetic genuine utterances 0/10 (AUD-03).
- The haystack is the streamed text, not the Edge-spoken text (AUD-04).

**Release timing (Audit 05)**
- Follow-up releases: monitor 196/205 (95.6%); `no_bout_estimate` 6; `forced_estimate` 3.
  3 of the 6 `no_bout_estimate` releases fired before a later monitor `bout_stop` on the same reply,
  so a capture opened while she was still speaking (AUD-20, AUD-21).
- `TtsPlaybackMonitor` release debounce is 450 ms; quiet 0.5 s; startup window 5.3 s (`P4-D18`).

**Clarify (Audit 03, L-4)**
- The voice clarify path works live: question spoken → monitor release → bound capture → answer →
  verbal reply (AUD-24).
- The echo guard runs on **bound** clarify captures (L895–897). Two residual risks remain: unbound
  transcripts route to the newest open clarify (`MainWindow` L585–593), and short answers can
  miss the guard (AUD-12).
- Batch answers depend on `_requestCards` (`BatchHasUnansweredRows`, L1557–1559) (AUD-13).
  Choices are never spoken (`VoiceController` L656–667) (AUD-14). Panel auto-open:
  `EnsureConversationOpen` (L1621–1632).
- On the Zola broker path, a spoken free-text answer is accepted as a raw string. Only the typed
  gateway path coerces it to an index or label (`clarify_gateway.py` L162–184).
- `voice.stop_phrases = ["stop"]`. Exact "stop" ends the voice chat and skips an open clarify.
  "Never mind", "skip" and "cancel" reach her as answer text.

**Latency (Audit 04, 06, 07)**
- Median EoS → first audio ≈ 8.6 s: silence 17%, STT 21%, submit + prefetch under 1%, model +
  sentence + Edge + playback 62% (AUD-16).
- L-2.3 (warm, no tools): about 10.1 s, of which the model is about 51%.
- L-2.1 (cold, tools) and L-2.2 (an approval card) were much slower.
- Simple questions ran tools: Tokyo time used `skill_view` + `terminal`; cups in a quart used
  `terminal` + approval `srq-8cce60bcb55f`. `calculate` was never called. Submit → card took
  about 5.7 s (AUD-25).
- Live warm WAV → `Transcribed` takes about 1.66–2.0 s; the H-1 harness infer takes about 0.75 s
  on clips of similar length. **Unexplained** (AUD-26).
- cpu/int8 and language pinning make no difference. `beam_size` and `cpu_threads` are not config
  keys (AUD-17, AUD-22). Pause data for a silence decision is unavailable (AUD-18).
- Hermes `agent.log` already has `Silence detected`, `WAV written`, `Transcribed`,
  `tui prompt accepted`, API latency and Edge `TTS saved`. `presence.log` has `playback bout start`.
- Background-review skills `communication/everyday-assistance` and
  `communication/conversation-memory` were created and kept in Phase 6. `everyday-assistance` §1
  concerns time lookups. They are a candidate driver for AUD-25 (Track 3 checks).

**Voice prose (Audit 05)**
- `SentenceChunker` (`min_len=20`) and `_strip_markdown_for_tts` are not configurable.
- `surface: "voice-live"` sets `client_surface`/`voice_live_context` and adds a per-turn model note
  (`voice_live.py` L73–90). There is no other model or tool change on the chained path. The client
  doesn't send it today.
- A plugin hook has no voice flag (AUD-19). Phase 4 found the note says a voice model
  "paraphrases" her text, which is false for Edge.

---

## Decisions Resolved in This Build Plan

Summaries below. **Appendix A** is verbatim from `claude/PHASE7_DECISIONS.md` and governs if a
summary differs. The track sections cite these IDs.

**Phase 7 invariant.** A voice transcript is not Brian merely because Hermes transcribed microphone
audio. The client admits it as Brian only when the current conversational and capture state
authorizes that input. Cancelled, stale, unbound or state-incompatible transcripts fail closed and
are never replayed. Content similarity to Zola is a secondary defense only.

**How the invariant is applied (v1.1; Appendix A is unchanged).** A transcript becomes Brian's
input only when the client can **prove** it came from a currently authorized capture opportunity.
The absence of contrary evidence is not proof. **Ambiguous** transcripts fail closed, alongside
cancelled, stale, unbound and state-incompatible ones. Ambiguity is the core risk, because Hermes
supplies no capture ID.

- **P7-D01 — One admission authority.** `VoiceController` decides. Check order: capture ownership
  and lifecycle → turn state and clarify binding → content echo check (reject-only).
- **P7-D02 — Cancel invalidates, then stops (revises P2-D05).** The forced transcript from that
  stop is inadmissible.
- **P7-D03 — One capture at a time, with a proven end.** The terminal Hermes states are proven at
  Track 1 grounding, then frozen. "Idle" is not assumed terminal. A transcript with no accepting
  owner is dropped. A recovery timeout never admits a transcript after the fact.
- **P7-D04 — No unbound transcripts during a running turn (revises P2-D12).** Dropped, never held.
  Typed submits are unchanged.
- **P7-D05 — Only the bound clarify capture answers a clarify (revises P4-D14 in part).** The
  newest-clarify fallback for unbound transcripts is removed. Typed composer answers are unchanged.
- **P7-D06 — The monitor outranks the estimate.** A fallback release can't create an accepting
  capture while the monitor reports her speaking. Monitor release is unchanged. S37 closes into
  this decision.
- **P7-D07 — The echo matcher is defense only.** It stays as is (P2-D14).
- **P7-D08 — Drops are logged, not announced.** The capture-window logging is fixed (AUD-23).
- **P7-D09 — Clarify in Voice mode (revises P4-D13).** A single question has no card and no panel,
  and its choices are spoken. Batch and multi-select keep the card. "Stop" is unchanged. Text mode
  and approvals are unchanged.
- **P7-D10 — Latency: measure → STOP → fix → remeasure.** Tool use on simple questions is
  investigated first. No Whisper, beam or silence changes without new evidence.
- **P7-D11 — No memory cleanup.**
- **P7-D12 — voice-live is checked before it is adopted.** Sentence streaming stays. Last track,
  cuttable.
- **P7-D13 — Track order 1 → 2 → 3 → 4.** A Hermes capture ID is filed upstream.

### Cross-cutting

**Client changes and the dependency-free check project (Track 1 onward).**
- The client has no automated tests. The admission rules are exactly the logic that needs them.
- Track 1 puts the **pure** decision logic in WinUI-free source files under
  `windows-client/Zola.Client/Voice/`, for example `TranscriptAdmission.cs` and
  `CaptureLifecycle.cs` (no UI types, no I/O, no clock reads; time is passed in).
- A new console project, `windows-client/Zola.Client.Checks/`, compiles those same files by link
  (`<Compile Include="..\Zola.Client\Voice\*.cs" Link=...>`). Hand-written assertions return a
  non-zero exit code on failure. It uses **no NuGet packages** beyond the .NET SDK, so it is not an
  install.
- If grounding shows the SDK console template would pull a package, stop and report.
- The check project is not part of the client build or the published app.
- Brian may choose MSTest instead at the Track 1 STOP. That would be an approved install under
  `P2-D17`.

**Live-profile edits** (`SOUL.md`, `config.yaml`, any skill or plugin change) follow P4-D25:
1. Back up first.
2. Propose the exact text, diff or hashes at a STOP.
3. Apply only after developer approval.
4. Mirror into `identity/` (or the repo source for plugins, with a per-file SHA-256 table).

Backups are deleted at each track's closeout after merge (P6-D11).

**Deploys.** A client change is live only after a rebuild and a full restart. Cursor verifies that
the old client process exited and that exactly one `hermes serve` (the new one) is running, by PID
and start time (Phase 6 lesson: a stale serve kept old modules loaded).

**Privacy (all tracks).** Cursor may read logs, `state.db` (read-only) and memory locally. Repo
documents carry only counts, lengths, IDs, hashes, timings, reasons and scripted test text. **Log
lines never contain transcript or reply text**: lengths, generations, kinds and reasons only.

**Logging (named constants, no magic strings):**
- every capture lifecycle transition: `capture start`, `capture accept`, `capture cancel`,
  `capture stop_sent`, `capture settle signal=…`, `capture recover_timeout`, each with `gen=` and
  `kind=`;
- every transcript decision: `transcript admit kind=… gen=… len=…` or
  `transcript drop reason=… gen=… len=…`.

**Brian's verdicts are recorded in his own words.**

---

## Track 1 — Transcript Authority (`P7-VOICEAUTH`)

### Problem
Zola's own speech becomes Brian's words. The mechanism is proven (AUD-02, AUD-09):
1. A cancel clears client flags but leaves Hermes recording.
2. The orphan capture hears her.
3. Its transcript arrives with the echo check switched off, and is submitted as a whole turn or as a
   mid-turn redirect.

There is no single authority for "this is Brian" (AUD-08). Hermes provides no capture ID (5.1a). A
fallback-timer capture can open while she is still speaking (AUD-20). The content matcher cannot
close any of this (H-2).

### Files to read
- Client: `windows-client/Zola.Client/VoiceController.cs`. Focus on:
  - `StartCaptureAsync` L1698–1802, `RecordAsync` L1820–1847, `StopCaptureAsync` L1804–1818;
  - `OnVoiceStatus` L1875–1897, `OnVoiceTranscript` L1908–1984;
  - `CancelFollowUp` L2128–2157, `OnTypedSubmit` L1675–1679, `OnTurnStarted` L1560–1598,
    `OnTurnCompleted` L1629–1673;
  - `ArmReplyFollowUpRelease` / `RunReplyFollowUpReleaseAsync` L2193–2491, `OnFollowUpTimerAsync`
    L2103–2126, `ReopenFollowUpAfterEchoAsync` L2042–2065;
  - `OpenClarifyAnswerCaptureAsync` L858–910, `HandleWakeDetectedAsync` L3249–3290, the gate paths
    L1179–1209, the Stop speaking path around L1059.
- Client: `MainWindow.xaml.cs` (`OnTranscriptReady` L562–632, `SubmitTurnAsync` L394–430, the
  typed-submit call L386, the mic toggle L461–497); `Presence/TtsPlaybackMonitor.cs` (bout
  start/stop, active-bout query); `ChatSocket.cs` (voice events).
- `hermes-agent` (read-only): `tui_gateway/methods_voice.py` (`voice.record` L704–760, `_vr_*`
  callbacks L685–702, `_end_voice_chat` L51–61); `hermes_cli/voice.py` (`start_continuous`,
  `stop_continuous`, `_continuous_on_silence`, stop-phrase handling); `tools/voice_mode.py`
  (`AudioRecorder` stop and cancel, VAD, max length); `tui_gateway/events.py` (the
  `VoiceTranscriptPayload` and voice status payloads).
- `zola-architecture/audit/p7pre-phase7/` Audits 01, 02, 05, 07 and the SYNTHESIS (5.1, 5.1a).

### Changes

**Phase 1:** commit the build plan (SOP v2.2 Stage 3: Claude places it, Cursor verifies the disk
and blob SHAs, then commits, merges `--no-ff` and branches `p7-voiceauth`).

**Phase 2: grounding (read-only, plus scratch-only harnesses).** Every item gets a `[CONFIRMED]` /
`[REFUTED]` answer with file and lines. Scratch folder: `C:\Users\test\Dev\zola-spikes\p7-voiceauth\`.
- **VA-G1 — The terminal set (P7-D03).** List every Hermes event or state that can settle a
  client-started capture: a text transcript, an empty or filtered transcript, `no_speech_limit`, a
  stop-phrase transcript, each `voice.status` value (including `idle` and `transcribing`), max
  length, a recorder error, `voice.record` returning `busy` or an error, and a socket drop. For
  **each**, prove from code whether a text transcript can still arrive afterwards for the same
  capture. Then propose the frozen terminal set.
  **Rule:** a signal may be classified as terminal **only if** grounding proves that no
  transcript attributable to that capture can arrive after it. A candidate signal that can't be
  proven is **not** terminal, and it cannot authorize the next accepting capture. If no adequate
  terminal set can be proven, that is a G-ARCH STOP. Never make the state machine "work" around a
  fuzzy lifecycle.
- **VA-G2 — Stop with nothing recording.** What `voice.record stop` returns, and whether any
  transcript follows, when the capture already ended on VAD silence, and when it never started.
- **VA-G3 — Stop racing silence.** Can one capture produce two transcripts (a silence-triggered
  transcribe in flight, then `force_transcribe` from the stop)? Is there a lock?
- **VA-G4 — Stop phrases from an inadmissible capture.** Hermes acts on a spoken "stop" before the
  client sees it: `_end_voice_chat` turns voice and TTS off. If the client judges that transcript
  inadmissible (for example, Zola's own "stop" from an orphan), what must the client do to restore
  Voice state without ending the chat, and does the existing `ResyncAfterStopAsync` cover it?
- **VA-G5 — The status sequence.** The exact `voice.status` sequence Hermes emits for one capture,
  for each ending (silence, client stop, no speech, max length). This is what the lifecycle reads.
- **VA-G6 — One submit path.** Confirm that `OnVoiceTranscript` → `TranscriptReady` →
  `MainWindow.OnTranscriptReady` is the only route from a voice transcript to `prompt.submit` or a
  clarify answer. List any other route.
- **VA-G7 — Reconnect.** What happens to an in-flight capture and its transcript on socket loss,
  `session-ready` or a connection-generation bump?
- **VA-G8 — Monitor query.** Can `TtsPlaybackMonitor` answer "is a bout active now?" synchronously
  for the release paths? What does it report when it is unavailable?
- **VA-G9 — The check project.** Confirm a console project linking WinUI-free files builds with
  the SDK alone (no package restore beyond the SDK).
- **VA-G10 — Clarify turn state.** From the logs of the known-good P7PRE L-4 sequence (and the code),
  record `TurnRunning`, `_streaming` and the broker state at each step: clarify opens, question
  spoken, answer capture, transcript, broker answer, reply resumes. Then freeze whether a clarify
  answer actually happens during a "running" turn. The admission rule is written in terms of the
  bound request either way (see `TranscriptAdmission`).
- **VA-G11 — Cancel without a transcript.** Is there an RPC-reachable way to end a Hermes capture
  **without** producing a transcript? Audit 01 found that `stop_continuous()` without
  `force_transcribe` (`rec.cancel`) runs on `voice.toggle` off. Ground `voice.toggle off` → `on`
  as a capture cancel, and list every side effect:
  - TTS cut, and whether `SPEECH_INTERRUPTED_NOTE` is latched (P4-D29 uses this path without a
    latch);
  - the wake detector;
  - voice mode and `ResyncAfterStopAsync`;
  - any turn effect.

  If it is clean, it is a candidate mechanism for P7-D02's stop and for the recovery reset. It
  would replace "stop, then drop the forced transcript" with "cancel, and no transcript exists".
  P7-D02 names `voice.record stop`, so switching to this mechanism is a **developer decision at
  the Phase 3 STOP**, not a Cursor choice.

A REFUTED item that a decision depends on is a **G-ARCH STOP**. Never adapt silently.

**Phase 3: STOP.** Report VA-G1–G11, the **frozen terminal set**, and a proposed state table
(states, events, transitions, and the admission verdict in each state). Also report the exact
recovery-timeout value with its basis (for example, max recording length + the transcribe budget
observed in logs), the log line formats, and the check list. Brian and Claude review it, and
Brian's verdicts are recorded verbatim.

**Phase 4: implementation (after approval).**

**`windows-client/Zola.Client/Voice/CaptureLifecycle.cs` (new, pure):**
- One record per client-owned capture: a monotonically increasing `Generation`, a `Kind` (`Wake`,
  `Manual`, `FollowUp`, `EchoReopen`, `Clarify(id)`), and a `State`:
  - `Starting`;
  - `Accepting`;
  - `Cancelled` (invalidated, stop pending or sent);
  - `Settled`.
- At most **one** outstanding (non-`Settled`) capture.
- A new capture may be created only when there is no outstanding capture, or the outstanding one
  is `Settled`.
- Transitions are driven only by the frozen terminal set (VA-G1) and the client's own actions.
- **Recovery:** after `CaptureSettleTimeoutSeconds` (a named constant, value set at the STOP) a
  non-settled capture becomes `Settled` with `signal=recover_timeout`. It **never** changes the
  verdict on a transcript that already arrived or arrives later for that generation (P7-D03).
- **Recovery restores operability, not provenance.** A timed-out Hermes capture might still
  emit a transcript that would look like the next capture's. So after `recover_timeout`, **no
  new capture becomes `Accepting`** until one of two things happens:
  - a Hermes reset proven at grounding (for example the VA-G11 cancel, if approved) guarantees
    the old capture can emit nothing more;
  - or the late-transcript window proven at VA-G1–G3 has passed.

  If neither can be proven, that is a G-ARCH STOP. The timeout must never become a back door
  around the proven-end rule.

**`windows-client/Zola.Client/Voice/TranscriptAdmission.cs` (new, pure):**
- `Decide(transcriptFacts, lifecycleSnapshot, turnRunning, clarifyBinding, gate, mode)` returns
  `Admit(kind, clarifyId?)` or `Drop(reason)`.
- Reasons are named constants: `no_owner`, `cancelled`, `settled`, `turn_running_unbound`,
  `clarify_not_active`, `gated`, `mode_text`, `echo`.
- Order (P7-D01):
  1. gate / mode;
  2. owner exists and is `Accepting`;
  3. **Capture authority, not the generic turn flag (D04, D05):**
     - a `Clarify(id)` capture is eligible only if `id` is the currently open broker request for
       this session, whatever the generic running-turn flag says. The agent opened that input
       slot explicitly;
     - any other clarify binding (closed, foreign, stale) → `Drop(clarify_not_active)`;
     - an ordinary `Wake` / `Manual` / `FollowUp` / `EchoReopen` capture whose transcript arrives
       while a turn is running → `Drop(turn_running_unbound)`.

     VA-G10 confirms the observed sequence. The rule doesn't depend on `TurnRunning` being true
     or false during a clarify;
  4. the content echo check runs last and can only turn `Admit` into `Drop(echo)` (D07, unchanged
     rule).
- Stop-phrase and no-speech transcripts go through the same ownership test. An inadmissible stop
  phrase triggers the VA-G4 restore, never `VoiceChatEnded`.

**`VoiceController.cs`:**
- Every capture start goes through the lifecycle:
  - `StartCaptureAsync` refuses or defers while a capture is outstanding;
  - wake, mic, follow-up, echo-reopen and clarify each pass their `Kind`.
- **Cancel = invalidate, then stop (D02).**
  - `CancelFollowUp` and every path that can leave Hermes recording (typed submit, Stop speaking,
    mode change, session ready, turn start) mark the outstanding capture `Cancelled` **first**,
    then send `voice.record stop` if Hermes may still be recording.
  - The gate path keeps its existing stop, now through the same method.
  - One private method does this. There is no second cancel path.
- `OnVoiceTranscript` calls `TranscriptAdmission.Decide` and acts only on its verdict:
  - `Admit` raises `TranscriptReady` (with the clarify id for `Clarify`);
  - `Drop` logs the reason (P7-D08) and does nothing else, apart from the VA-G4 restore.
  - The existing echo-ignored notice and echo-reopen behavior stay **only** for the
    `Drop(echo)` follow-up case, as today.
- **The monitor outranks the estimate (D06).** In the reply release paths, a `no_bout_estimate` or
  `forced_estimate` release that finds the monitor reporting an active bout **does not open a
  capture**. It hands the release back to the monitor's bout stop (the same quiet rule as
  `P4-D18`). If the monitor is **unavailable**, today's estimate behavior stays unchanged. The
  monitor-driven release is untouched. The same rule applies to `question_release`.
- `OnTurnStarted` / `OnTurnCompleted` keep their window bookkeeping. Each capture's own window
  times move into the lifecycle record, so the transcript log line reports the owning capture's
  times or `owner=none` (fixes AUD-23).
- Comment tags: `// P7-VOICEAUTH: <rationale> — P7-D0X`.

**`MainWindow.xaml.cs`:**
- `OnTranscriptReady` no longer routes an unbound transcript to the newest open clarify. Remove
  L585–593 (D05).
- An admitted unbound transcript goes to `SubmitTurnAsync` as today. A bound one goes to
  `ApplyVoiceClarifyAnswer`, as today.
- The typed composer path (P4-D09) is unchanged.
- No other change. MainWindow does not re-decide admission (one authority).

**`windows-client/Zola.Client.Checks/` (new, per the cross-cutting rule).** Checks cover:
- each LEAD-1 cancel reason, with the forced transcript dropped;
- stop with nothing recording (VA-G2): the next genuine capture's transcript is admitted;
- a stop/silence race (VA-G3) as grounded;
- a transcript after a proven terminal signal behaves exactly as the frozen terminal contract
  says. If a late prior-generation transcript remains possible after a signal, that signal is not
  terminal, and implementation stops (G-ARCH). There is no "best guess" attribution;
- after `recover_timeout`, no capture becomes `Accepting` until the proven reset or window
  condition holds;
- `TurnRunning` + unbound → drop; `TurnRunning` + active clarify → admit; closed clarify → drop;
- a fallback release with an active bout → no capture; monitor unavailable → today's behavior;
- recovery timeout → `Settled`, with no retroactive admit;
- the echo check runs last and only rejects;
- an inadmissible stop phrase → restore, not end;
- gate and Text mode → drop.

**No profile, `SOUL.md`, Hermes or plugin changes in this track.**

**Phase 5: STOP.** Report the diff summary, the check output, the build output, and the proposed
smoke script. Then deploy (rebuild and restart, verifying processes).

**Phase 6: smoke.**

### Exit criteria
- [ ] VA-G1–G9 answered with evidence. The frozen terminal set and Brian's STOP verdicts are
      recorded.
- [ ] The build passes. All checks pass, including every case listed above.
- [ ] CURSOR-RUN code check: exactly one method sends a cancel-stop, and every cancel path calls
      it. `MainWindow` contains no admission logic. The newest-clarify fallback is gone. There is
      no second submit route (VA-G6).
- [ ] HUMAN-RUN smoke in Voice mode, one step at a time, neutral content. Cursor reads
      `voice-timeline.log`, `agent.log` and `state.db` (read-only) after each step:
  - **S1 (L-3 Run A again):** a spoken question, then Brian types the next prompt right after the
    beep. The logs show `capture cancel` → `stop_sent` → `transcript drop reason=cancelled`. No
    extra user message in `state.db`. No `User correction during the turn`.
  - **S2 (L-3 Run B again):** Brian types right at or just before the beep. Same expectations.
  - **S3:** Stop speaking mid-reply. No follow-up opens. Any transcript that arrives is dropped
    with a reason.
  - **S4 (no regression):** three ordinary voice exchanges: "Hey Zola" → question → reply → answer
    after the beep. Each follow-up answer is admitted and submitted once. An instant answer right
    after the beep behaves as before (`P4-D18`, residual ~1 s clip noted, not a fail).
  - **S5:** a voice clarify (the L-4 script). The bound answer is admitted and answers the request.
  - **S6:** switch to Text mode during a follow-up capture, then back to Voice. No stray user turn.
  - **S7 (`P4-D02` regression):** lock the PC during a follow-up capture, then unlock. Nothing is
    submitted; Voice state is restored as before.
- [ ] CURSOR-RUN across the whole smoke window: zero admitted transcripts whose owner was
      cancelled, settled or absent. Every drop has a reason. The count of `no_bout_estimate` /
      `forced_estimate` releases is reported. For each one, the logs show no capture opened during
      an active bout.
- [ ] CURSOR-RUN memory check: the user turns in `zola_memory` pending or consolidation logs match
      the scripted turns exactly (counts only).
- [ ] `hermes-agent` clean at the pin. Live profile hashes (`config.yaml`, `SOUL.md`, `plugins/**`)
      unchanged.

**Complexity:** Medium-Large
**Primary risk:** the lifecycle drops Brian's real speech. (The opposite failure, a late
transcript misattributed to a newer capture, is prevented by the VA-G1 proof rule and the
recovery rule; if it can't be prevented, the track stops instead.) Either a terminal signal is misread (a
capture is treated as still outstanding, so the next real capture can't start or its transcript is
judged `no_owner`), or the D06 hand-back to the monitor leaves no capture open after a reply.
Mitigations:
- VA-G1–G5 grounding before any code;
- the checks for "stop with nothing recording" and the hand-back;
- S4 as a hard no-regression gate.

If S4 loses a genuine answer, stop and report. Don't loosen admission.

---

## Track 2 — Clarify by Voice (`P7-CLARIFY`)

### Problem
In Voice mode, every clarify opens the conversation panel and shows a card (`EnsureConversationOpen`
L1621–1632). Brian wants voice clarify to be purely conversational (S44). The choices are never
spoken (AUD-14), so simply removing the card would hide them. Batch answers depend on the card
(AUD-13). After Track 1, the answer capture is provably Brian's (P7-D01–D06), which this track
relies on.

### Files to read
- `MainWindow.xaml.cs`: clarify show/build/answer/collapse (L1096–1224, L1227–1436), batch
  (L1528–1607), `EnsureConversationOpen` (L1621–1632), `OnTranscriptReady` (post-Track 1), the
  stop-phrase skip (L544–555), the composer answer path (P4-D09), the approval card (L1136–1163,
  L1439–1525; read only, to confirm it is untouched).
- `VoiceController.cs`: `SpeakQuestionAsync` (L564–671), `RememberSpokenEcho` (L2595–2612), the
  clarify capture (L858–910).
- `ServerRequestBroker.cs` (`ClarifyOpened`, answer, skip, cancel, timeout).
- `ZolaDisplayState.cs` (`Waiting for your answer`, L326–353).
- `hermes-agent` (read-only): the clarify request shape (`server.py` L1325–1341,
  `tools/clarify*`), `clarify_gateway.py` L162–184 (answer coercion, for reference only).
- `zola-architecture/audit/p7pre-phase7/Zola_P7PRE_Audit_03_ClarifyVoice.md`; the Track 1 progress
  doc.

### Changes

**Phase 2: grounding (read-only).**
- **CL-G1 — Classification.** How the client can tell a single question from a batch
  (`questions[]`) or multi-select request at receipt time.
- **CL-G2 — Choice answers.** Confirm that a spoken answer naming a choice in free words ("the
  green one", "the second one") is sent as a raw string on the Zola broker path, and that the model
  receives it unchanged (there is no index coercion on this path).
- **CL-G3 — Record line.** What the conversation shows today after an answer. Propose the cardless
  equivalent: a read-only "question + You answered: …" record added to the conversation, **without**
  opening the panel. The record is **client presentation state only**. It must not generate a
  `prompt.submit`, another Hermes message, another `sync_turn`, or another memory candidate.
  Brian's answer already reaches Hermes once, as the clarify result. Confirm in code that the
  existing collapsed "You answered" record (P4-D08) is presentation-only too.
- **CL-G4 — Mode switches.** The behavior today and the needed behavior when the mode changes while
  a single question is open:
  - Voice → Text: the card must appear (rendered on demand) so Brian can click or type;
  - Text → Voice while a card is showing: the card stays, and no re-speak.
- **CL-G5 — The echo haystack.** Today the spoken question is remembered for the echo check. If the
  choices are spoken, should they be in the haystack? An answer that repeats a multi-word choice
  could be dropped as an echo. Report the risk with H-2-style offline checks over synthetic
  choices. Then propose: question only, or question + choices.
  - Note: Track 1 D06 already prevents a capture opening while the question is still playing.

**Phase 3: STOP.** Report CL-G1–G5, plus the exact spoken template for choices. Default draft:

> "{question} Is it {A}, {B}, or {C}?"

Speak the "(Recommended)" marker as a label or drop it (Brian's call). Also report the record-line
format and the haystack choice. Brian approves; his verdicts are recorded verbatim.

**Phase 4: implementation.**
- **`MainWindow.xaml.cs`:**
  - In Voice mode, for a **single** question (not batch, not multi-select): do not build or show
    the card, and do not call `EnsureConversationOpen`. The broker still owns the request (no
    change to its authority, timeout, skip or cancel).
  - On answer, skip, cancel or timeout, add the approved read-only record line and the existing
    notice, without opening the panel.
  - Batch and multi-select keep today's card and panel behavior in Voice mode.
  - Mode switches follow CL-G4.
  - Approvals: no change.
- **`VoiceController.cs`:** `SpeakQuestionAsync` speaks the approved template with the choices when
  present. The haystack content follows the CL-G5 decision. Everything else is unchanged
  (question-only release, the clarify capture, D05 binding).
- **`ZolaDisplayState.cs`:** no change expected. "Waiting for your answer" still shows. If the HUD
  needs to point to the panel only when a card exists, propose it at the STOP.
- Checks: extend `Zola.Client.Checks` with the template builder and classification (pure helpers).
- Comment tags: `// P7-CLARIFY: <rationale> — P7-D09`.

**No profile, Hermes or plugin changes.**

### Exit criteria
- [ ] CL-G1–G5 answered. Template, record line and haystack choice approved; verdicts recorded.
- [ ] The build passes; checks pass.
- [ ] HUMAN-RUN, Voice mode:
  - **C1:** a single question with three choices. No card, the panel stays closed, Brian hears the
    choices, and answers by voice in free words. The broker shows `answered`; her reply uses the
    choice; the record line appears in the conversation.
  - **C2:** a single free-text question (no choices). The same, with no choice list spoken.
  - **C3:** a single question answered by **typing** in the composer while in Voice mode (P4-D09).
    It answers the open request.
  - **C4:** "never mind" spoken as the answer. It reaches her as an answer, and she handles it
    naturally (Brian's words). No new command behavior.
  - **C5:** a batch or multi-select request (ask her to ask two things at once). The card shows as
    today and works.
  - **C6:** Voice → Text while a single question is open. The card appears, and a click answers it.
  - **C7 (control):** an approval request still shows its card and opens the panel (P4-D07).
- [ ] HUMAN-RUN, Text mode: a clarify shows the card exactly as before (P4-D08).
- [ ] CURSOR-RUN: `server-requests.log` shows each request's lifecycle. No clarify answer comes from
      an unbound transcript (Track 1 D05 holds).
- [ ] CURSOR-RUN: for C1–C6, `state.db` and `zola_memory` show the answer once, as the clarify
      result only. No extra user message, no extra `sync_turn` or pending turn from the record line
      (counts only).
- [ ] `hermes-agent` clean; live profile hashes unchanged.

**Complexity:** Medium
**Primary risk:** a cardless question becomes unanswerable or invisible. A mode switch, timeout or
skip leaves the broker request open with nothing on screen to answer it, or the spoken choices get
Brian's verbatim choice answer dropped by the echo check. Mitigations: CL-G4 and CL-G5, plus C3 and
C6.

---

## Track 3 — Measure, Then Fix (`P7-LATENCY`)

### Problem
The felt wait from Brian finishing to Zola speaking is about 8.6 s at the median, and much longer
when tools run (AUD-16). The largest share (62%) is after submit, and it is under-instrumented.
Simple questions run tools, and one raised an approval card (AUD-25). Live speech-to-text is about
0.9–1.3 s slower than the same model in a harness, for no known reason (AUD-26). Brian chose
**measure and fix**.

### Files to read
- Client: `ChatSocket.cs` (`message.start`, `message.delta`, `message.complete` dispatch),
  `MainWindow.xaml.cs` (`SubmitTurnAsync`), `VoiceController.cs` (`OnVoiceTranscript`, the timeline
  logging), `Presence/TtsPlaybackMonitor.cs` (bout start).
- `hermes-agent` (read-only): `tools/transcription_tools.py` (`transcribe_recording` and its call
  path), `tools/transcription_local.py`, `tools/voice_mode.py` (WAV write), `hermes_cli/voice.py`
  (`_continuous_on_silence`), `tui_gateway/prompt_turn.py` (turn start to first delta), the
  `agent.log` lines named in the grounding summary.
- Live profile (read-only): `SOUL.md`, `skills/communication/everyday-assistance/`,
  `skills/communication/conversation-memory/`, `plugins/zola_tools/`.
- `zola-architecture/audit/p7pre-phase7/` Audits 04, 06, 07 and SYNTHESIS 5.4.

### Changes

**Phase 2: instrument (client logging only) and probe.**
- **Client per-turn timing.** One `turn_timing` line per turn, with ms deltas from `prompt.submit`:
  `first_delta`, `first_sentence_end` (the first delta that completes a chunker sentence: same
  boundary regex, `min_len=20`), `complete`, `first_audio` (monitor bout start), plus the voice
  transcript arrival time. Named constants; no text.
- **Join with Hermes logs.** A scratch script joins the client timing with `agent.log`:
  `Silence detected` (EoS = minus `silence_duration`), `WAV written`, `Transcribed`,
  `prompt accepted`, API latency, `TTS saved`. It produces the P7PRE Q1a table per turn. **No
  Hermes edit.**
- **LT-G1 (AUD-26).** In scratch, call Hermes's **exact** live entry point
  (`transcribe_recording` path, live config) on WAVs from:
  - the repo's `P4-VOICE_samples` (synthetic);
  - six new scripted recordings by Brian (the P7PRE L-1 lines), deleted at closeout.

  If this gives about 0.75 s, the gap is in-process (contention inside `serve`). Report the
  candidate sources: the wake detector, the presence/TTS threads, CPU frequency, `cpu_threads`. If
  it gives about 1.7 s, find which step inside the call costs it. No fix in this phase.
- **LT-G2 (AUD-25).** Over the last 30 days of `agent.log` / `state.db` (read-only), tabulate the
  tool calls on turns where the user message is a short factual question. Report counts by tool,
  and whether an approval followed. Then check the likely drivers:
  - the `everyday-assistance` skill text (§1, time lookups);
  - the `SOUL.md` "Doing math" scope (arithmetic only, not conversions);
  - the time context she already has (P6-TIME: local time only, so other zones need a conversion);
  - whether `skill_view` precedes the terminal call.
- **LT-G3 (pauses, for the future silence decision only).** Offline in scratch, measure the
  within-utterance pause lengths in Brian's six recordings plus three free-speech recordings. Report
  the distribution. **No change** to `silence_duration` in Phase 7 (P7-D10).
- **Baseline run (HUMAN-RUN).** A fixed script of 8 voice turns, in a new session, warm:
  - two simple factual questions (one time zone, one unit conversion);
  - two conversational questions;
  - one arithmetic question;
  - one memory recall;
  - two short follow-ups after the beep.

  Record the per-turn table and the medians.

**Phase 3: STOP (attribution).** Report:
- the baseline table, with stage shares;
- LT-G1, LT-G2 and LT-G3;
- a ranked list of fix candidates, each with its measured or bounded saving, risk, and change type.

Candidates already known (none chosen):
- `SOUL.md` guidance: answer common knowledge, unit conversions and time-zone questions directly;
- extending the bounded `calculate` (`zola_tools`) with unit conversion (P6-D08 contract: no code,
  fail closed);
- an edit to the `everyday-assistance` skill (Brian's call; the skill was kept at the Phase 6
  closeout);
- adding a UTC offset to the time context so she can convert zones in her head;
- an in-process STT fix, if LT-G1 finds one reachable without a Hermes edit or an install.

Brian chooses. His verdict is recorded verbatim. A choice that needs an install, a Hermes edit or
a Whisper/beam/silence change is out of Phase 7 (P7-D10), and is filed instead.

**Phase 4: implement the chosen fix.** Follow P4-D25 for `SOUL.md`, skills and plugins, and the
plugin rules from Phase 6 for `zola_tools` (repo source canonical; unit tests; per-file hash
table). Comment tags: `P7-LATENCY: … — P7-D10`.

**Phase 5: remeasure.** Rerun the same 8-turn script, plus the AUD-25 pair (Tokyo time, cups in a
quart). Produce a before/after table. The pass bar is the **causal target**, not the aggregate:
- the proven cause no longer happens on the targeted controls (for example, no tool call and no
  approval card on the simple questions);
- the directly attributable stage or cost is removed or reduced on those turns (for example,
  submit → first audio on the cups turn);
- answers stay correct (Brian judges every turn);
- the conversational and memory turns show no behavior change.

Aggregate EoS → first-audio medians are **reported as an observed outcome**, with the observed
noise stated. They are not required to improve when model or API variance dominates over 8 turns.

### Exit criteria
- [ ] The `turn_timing` line exists. The join script and the baseline table are recorded. The
      EoS → first-audio median and each stage's share are reported.
- [ ] LT-G1 settles AUD-26 as in-process or in-call, with evidence. If it is still unexplained,
      the reason is stated.
- [ ] LT-G2 tool table and driver findings are recorded. LT-G3 pause distribution is recorded
      (silence unchanged).
- [ ] Brian's STOP choice is recorded verbatim, and the fix is implemented under its rules
      (P4-D25, plugin tests if a plugin changes).
- [ ] HUMAN-RUN remeasure: the causal-target pass bar is met on the targeted controls. The aggregate
      before/after table is reported, with its noise. Brian's words on how the wait feels are
      recorded.
- [ ] Scratch recordings are deleted at closeout. Backups are deleted after merge (P6-D11).
- [ ] `hermes-agent` clean. Profile changes are limited to those approved at the STOP.

**Complexity:** Medium
**Primary risk:** a fix that "works" on the script but changes her behavior elsewhere. For
example, direct-answer guidance makes her answer things she should look up, or skip a tool she
needs. Mitigations:
- the remeasure includes the conversational and memory turns;
- Brian judges correctness on every turn;
- the fix is the narrowest that addresses the measured cause.

---

## Track 4 — Voice Prose (`P7-VOICEPROSE`, cuttable)

### Problem
Zola's replies are shaped for speech only through `SOUL.md` "How I talk out loud", which applies to
typed replies too (`S34`, `P4-D20`). Hermes can mark a turn as spoken (`surface: "voice-live"`),
which adds a per-turn model note. That note was written for a different pipeline, where a voice
model paraphrases the text (Phase 4 note; AUD-19). Sentence streaming is the right synthesis design
(P7-D12).

### Files to read
- `hermes-agent` (read-only): `tools/voice_live.py` (L73–90), `tui_gateway/methods_prompt.py`
  (L541–588), `tui_gateway/session_notifications.py` (L690–703), and wherever `client_surface` /
  `voice_live_context` are read.
- Client: `ChatSocket.cs` (`SubmitAsync`), `MainWindow.xaml.cs` (`SubmitTurnAsync`).
- Live `SOUL.md` ("How I talk out loud").
- `zola-architecture/audit/p7pre-phase7/Zola_P7PRE_Audit_05_ChunkingEstimate.md`.

### Changes

**Phase 2: grounding (read-only).**
- **VP-G1.** Quote the exact `voice_live_turn_note` text at `345cd2b0`. Go through every
  instruction in it against Zola's setup: chained STT → model → Edge reading her exact text. Mark
  each instruction as true, false or harmful.
- **VP-G2.** List **every** effect of sending `surface: "voice-live"`: prompt text, history and
  persistence (is the note stored in `api_content`, and what is its token cost per turn?),
  `client_surface` consumers, tools, model routing, and memory hooks (what `zola_memory`
  `sync_turn` / `pre_llm_call` see).
- **VP-G3.** Whether any client → model voice signal exists at this pin that would let Zola's own
  plugin add a Zola-written voice note, without the Hermes note and without a Hermes edit (AUD-19
  says none is known; confirm or refute).

**Phase 3: STOP.** The options:
- (a) adopt the note as is, for admitted **voice** turns only;
- (b) reject it, leaving shaping in `SOUL.md`, and record the reasons;
- (c) a VP-G3 path, if one exists.

Brian decides; his verdict is recorded verbatim. **(a) is not allowed if VP-G1 finds a false or
harmful instruction that can't be countered.** Countering it with a `SOUL.md` line is itself a
P4-D25 proposal at this STOP.

**Phase 4 (only if (a) or (c)):** `ChatSocket.SubmitAsync` takes a voice flag. `SubmitTurnAsync`
passes it only for transcripts admitted by Track 1's authority. Typed turns are unchanged. Comment
tag: `P7-VOICEPROSE: … — P7-D12`.

**Phase 5: smoke (only if (a) or (c)).** Ten voice turns with the note and ten without, on the same
script, in an order Brian doesn't know (Cursor toggles it between runs with a build flag or a
config constant, never by injecting turns). Brian judges how each reply sounds spoken, in his own
words. Cursor reports first-token latency with and without (Track 3 timing) and the prompt-cost
delta.

### Exit criteria
- [ ] VP-G1–G3 recorded, with the note text quoted and judged instruction by instruction.
- [ ] Brian's STOP verdict recorded verbatim.
- [ ] If adopted: the build passes; only admitted voice turns carry the surface (CURSOR-RUN code
      check and log check); the blind listening result and the latency/cost deltas are recorded;
      Brian accepts.
- [ ] If rejected: the reasons are recorded for the lore closeout, and no client change is made.
- [ ] `hermes-agent` clean.

**Complexity:** Small-Medium
**Primary risk:** the note makes her worse. She writes looser text because she believes a
downstream voice will fix it, and Edge reads it word for word. Mitigations: the VP-G1 line-by-line
check, and the blind A/B.

---

## Phase 7 Lore Closeout

After all tracks are merged to `main` (or Track 4 is cut):

### DESIGN_DECISIONS.md
- Record P7-D01 through P7-D13 under "Phase 7 — Voice She Can Trust", with Appendix A condensed in
  house style and Brian's verdicts quoted.
- Annotate:
  - `P2-D05`: **revised by P7-D02** (a transcript from a cancelled capture is dropped);
  - `P2-D12`: **revised by P7-D04** (no mid-turn voice submits; one admission authority, P7-D01);
  - `P2-D14`: unchanged; defense only (P7-D07);
  - `P4-D13`: **revised by P7-D09** (choices spoken; no card for a single question in Voice mode);
  - `P4-D14`: **revised in part by P7-D05** (no newest-clarify fallback);
  - `P4-D18`: preserved; the monitor outranks the estimate (P7-D06);
  - `P4-D20`, `P4-D24`: per the Track 4 outcome.
- Record the frozen terminal set (Track 1) as an execution note.

### OPEN_QUESTIONS.md
- `S45`: **RESOLVED** by `P7-VOICEAUTH`. Note the mechanism (orphan capture), the authority, and
  the smoke evidence.
- `S37`: **RESOLVED** (closed into P7-D06), with the fallback-release counts.
- `S44`: **RESOLVED** by `P7-CLARIFY` for single questions. Batch and multi-select by voice is filed
  as a new OQ if Brian still wants it.
- `S38`: **updated**, not resolved unless Brian says so. Record the baseline and after tables, the
  fix made, AUD-26's outcome, and the pause distribution for a future silence decision.
- `S34`: resolved or annotated per Track 4.
- `S36`: annotate that the "echo → ignore" part of its policy is now the P7 authority.
  Barge-in itself stays upstream-gated.
- New OQs:
  - a Hermes capture correlation ID (upstream);
  - smaller Whisper models (a `P2-D17` install decision, with candidate sizes);
  - `silence_duration` with the pause data;
  - any LT-G2 driver left unaddressed.

### ROADMAP.md
- Mark Phase 7 COMPLETE, with the plan, track and merge SHAs.
- Add a Phase 8 stub. Scope is the developer's call. Likely candidates: memory round two (`S46`,
  P6-D01 migration, `S48`–`S50`), then `S35` scopes, `S40`, `S28`.

### identity/
- `SOUL.md` and `VOICE_CONFIG.md` match the live profile, plus any skill or plugin hash tables from
  Track 3.

---

## Phase 7 Exit Checklist
- [ ] Track 1 (`P7-VOICEAUTH`) merged. Terminal set frozen; checks pass; S1–S7 pass; zero
      admitted orphan transcripts; every drop logged with a reason.
- [ ] Track 2 (`P7-CLARIFY`) merged. C1–C7 pass; Text mode unchanged; approvals unchanged.
- [ ] Track 3 (`P7-LATENCY`) merged. Baseline and after tables recorded; the chosen fix meets its
      pass bar; AUD-26 settled or explained.
- [ ] Track 4 (`P7-VOICEPROSE`) merged, or cut with its grounding recorded.
- [ ] No `hermes-agent` edits; `git status` clean at `345cd2b0…` after each track.
- [ ] No installs, unless explicitly approved at a STOP and recorded.
- [ ] Live-profile changes limited to those approved at STOPs, each mirrored, with backups deleted
      at track closeout.
- [ ] All new constants are named (`CaptureSettleTimeoutSeconds`, admission reasons, log prefixes,
      the spoken-choice template). No magic strings. No transcript or reply text in any log or repo
      document.
- [ ] The client builds, and `Zola.Client.Checks` passes on `main` after all merges. Plugin tests
      pass if a plugin changed.
- [ ] Smoke test after each track boundary.
- [ ] `DESIGN_DECISIONS.md`: P7-D01–D13 recorded with annotations.
- [ ] `OPEN_QUESTIONS.md`: S45, S37, S44 resolved; S38/S34/S36 annotated; new OQs filed.
- [ ] `ROADMAP.md`: Phase 7 COMPLETE; Phase 8 stub added.

---

## What Phase 7 Explicitly Defers

| Item | Reason | When |
|---|---|---|
| Hermes capture correlation ID on `voice.transcript` | Needs a `hermes-agent` edit; the client lifecycle is enough (P7-D03) | Upstream |
| Barge-in / talk-over (`S36`) | Upstream-gated (`P5-D08`); `voice.barge_in: false` stands | When upstream O2 exists |
| Un-anchoring or re-scoping the echo matcher | Content can't establish provenance; quote false positives (H-2, P7-D07) | Only with new evidence |
| Spoken haystack (Edge-normalized text) | Content defense only; low value after provenance (AUD-04) | Future, if echo drops recur |
| Batch / multi-select clarify by voice | Needs a voice protocol for several answers (AUD-13) | New OQ, if Brian wants it |
| Smaller or English-only Whisper models | Download = install (`P2-D17`); measure first (P7-D10) | A future decision with Track 3 data |
| `beam_size`, `cpu_threads` | Not config keys; a Hermes edit (AUD-17) | Upstream, or not at all |
| Shorter `silence_duration` | Cutoff risk; pause data gathered only (AUD-18) | A future decision with LT-G3 data |
| Whisper warm-up at serve start (`S23`) | Hermes-side | Upstream, or a future decision |
| Whole-line synthesis | Slower first audio; sentence streaming is right (P7-D12) | Not planned |
| Memory cleanup of probe turns | All consolidated into nothing (P7-D11) | Not needed |
| `S46`–`S50`, the P6-D01 migration | Memory round two needs real use first | Phase 8 candidate |
| `S35` session/always scopes, `S40`, `S28`, `S39`, `S21`, `S33`, `S17`, `S26` | Not in Phase 7 scope | Later phases |

---

## Complexity Legend

| Track | Complexity | Primary Risk |
|---|---|---|
| 1 — `P7-VOICEAUTH` | Medium-Large | The lifecycle drops Brian's real speech (a misread terminal signal, or the D06 hand-back opens no capture) |
| 2 — `P7-CLARIFY` | Medium | A cardless question becomes unanswerable or invisible, or a spoken-choice answer is dropped as an echo |
| 3 — `P7-LATENCY` | Medium | A fix that helps the script but changes her behavior elsewhere |
| 4 — `P7-VOICEPROSE` | Small-Medium | The note makes her text looser because she expects a paraphrasing voice |

---

## Appendix A — Locked Decisions (verbatim from `claude/PHASE7_DECISIONS.md`, 2026-10-05)

**Brian's verdicts (verbatim):**
- On the full decision set, including the revisions to P2-D05, P2-D12, P4-D13 and P4-D14:
  **"approved."**
- On S34: **"Yes. keep S34"**

**Phase 7 invariant:** A voice transcript is not Brian merely because Hermes transcribed microphone
audio. The Windows client admits it as Brian only when the current conversational and capture state
authorizes that input. Cancelled, stale, unbound or state-incompatible transcripts fail closed and
are never replayed later. Content similarity to Zola is a secondary defense only.

#### P7-D01: One transcript-admission authority
`VoiceController` is the single authority that decides whether a transcript is Brian's input. A
transcript is admitted only when the current capture state authorizes it. Content resemblance to
Zola can reject a transcript; it can never admit one. The check order is: capture ownership and
lifecycle → turn state and clarify binding → content echo check (reject-only, including clarify
answers).
- Evidence: AUD-08, Audit 01 §10–11.

#### P7-D02: Cancel invalidates, then stops (revises P2-D05)
Every intentional client cancellation invalidates the current capture generation **before**
Hermes is told to stop. `CancelFollowUp` and every other cancel path that can leave Hermes
recording (typed submit, Stop speaking, mode change, session ready) issue `voice.record stop`. The
forced transcript from that stop belongs to the cancelled generation and is inadmissible.
- **Revises P2-D05** ("every voice transcript is sent immediately"): a transcript from a cancelled
  capture is dropped.
- Evidence: AUD-01, AUD-02, AUD-09, L-3.

#### P7-D03: One capture at a time, with a proven end
Only one client-owned capture may be outstanding. A new capture cannot accept speech until the
previous client-owned capture has reached a **proven terminal Hermes state**. The VOICEAUTH track's
grounding step enumerates every Hermes event or state that can settle a client-started capture,
proves whether a text transcript can still arrive after each one, and then freezes the terminal
set. "Idle" is not assumed terminal until proven. A transcript received with no accepting capture
owner is dropped. A bounded recovery timeout may clear a stuck lifecycle, but it never
retroactively admits a transcript.
- Why: with no capture ID, "drop the next transcript after a stop" can drop Brian's real speech if
  the cancelled capture had already ended on silence.
- Future (upstream, not Phase 7): a Hermes-issued capture correlation ID.
- Evidence: 5.1a, AUD-23.

#### P7-D04: No unbound transcripts during a running turn (revises P2-D12)
During `TurnRunning`, an ordinary unbound transcript is inadmissible. It is dropped, never held or
replayed. No genuine input is lost: with `voice.barge_in: false`, Brian cannot start a capture
during a turn (wake requires Resting, and the mic button and hotkey require `!TurnRunning`).
- **Revises P2-D12** ("running-turn `prompt.submit` is accepted; the client submits once and never
  holds"): mid-turn voice submits stop. Typed submits are unchanged.
- Evidence: AUD-05, E2.

#### P7-D05: Only the bound clarify capture answers a clarify (revises P4-D14 in part)
A transcript may answer a clarify only if it comes from the active clarify-answer capture bound to
that request. The fallback that lets an unbound transcript answer the newest open clarify is
removed. Typed answers through the composer (P4-D09) are unchanged.
- Evidence: AUD-12, Audit 03.

#### P7-D06: The playback monitor outranks the estimate
A fallback or estimate release cannot create an accepting capture while the playback monitor
reports Zola still speaking. Monitor-driven release remains authoritative and unchanged (P4-D18
preserved). **S37 closes into this decision.** Acceptance: if an estimate release fires while she
is still audible, her speech cannot become admitted Brian input.
- Why: A + B alone miss this case. The turn is already complete (`TurnRunning` false) while her
  audio continues, so a fallback capture would otherwise be a current, owned capture.
- Evidence: AUD-20, AUD-21, Audit 05 §7.

#### P7-D07: The echo matcher is defense-in-depth only
`IsEchoOfLastReply` stays as is: end-anchored, follow-up and clarify captures, P2-D14 unchanged. It
can reject only. No un-anchoring in Phase 7 (H-2: quote false positives).

#### P7-D08: Drops are logged, not announced
Every dropped transcript gets a log line with the reason and length (never text). No on-screen
notice, since Brian said nothing. The capture-window bookkeeping is fixed so log lines describe the
capture that produced the transcript (AUD-23).

#### P7-D09: Clarify in Voice mode (revises P4-D13)
In Voice mode, a **single** clarify question is asked conversationally, with no card and no
automatic panel opening. If it has choices, she speaks the choices (**revises the P4-D13
amendment** "question only, never the choice list"). Batch (`questions[]`) and multi-select keep
the visual card in Phase 7. Exact "stop" keeps its current meaning; no new command words ("skip" or
"never mind" reach her as ordinary answers). Text-mode clarify is unchanged (P4-D08, P4-D09).
Approvals stay visual and manual (P4-D07, P4-D27).
- Depends on P7-D01–D06: the answer capture must be Brian-only.
- Evidence: AUD-12–15, AUD-24, Audit 03.

#### P7-D10: Latency is measure → STOP → fix → measure again
First add the missing stage timing: `prompt.submit` → first model token → first speakable sentence
→ Edge synthesis start and end → playback; Whisper infer start and end (AUD-26); and
within-utterance pause lengths (for a future silence decision). Investigate unnecessary tool use on
simple questions first (AUD-25). At the STOP, choose and implement the largest proven, safely
addressable cause within Phase 7, then measure again. No changes to the Whisper model, beam size or
silence duration without new evidence.
- Candidates noted (not chosen): `SOUL.md` guidance to answer common knowledge and conversions
  directly; extending the bounded `calculate` tool to unit conversion.

#### P7-D11: No memory cleanup
The 10 probe pending rows (7 tagged `LIVE-PROBE-CONTAMINATION`) were consolidated into nothing,
with zero episodes. E1 and E2 stay in `state.db` as conversation history and forensic evidence
(P5-D10).

#### P7-D12: voice-live is checked before it is adopted
Track 4 starts by capturing the exact `voice_live_turn_note` at `345cd2b0` and evaluating every
instruction against Zola's chained Edge setup. Phase 4 found it says a voice model "paraphrases"
her text, which is false for Edge. Adoption, editing or rejection is decided at a STOP. Sentence
streaming stays; no whole-line synthesis. Last track, explicitly cuttable.

#### P7-D13: Track order
VOICEAUTH (S45 + S37) → CLARIFY (S44) → LATENCY (S38) → VOICEPROSE (S34). A Hermes capture
correlation ID is filed as a future upstream improvement.

---

*Phase 7 Build Plan version 1.1 (v1.1: ChatGPT review, all five points adopted:*
*- a terminal signal needs proof that no later transcript can come; there is no best-guess attribution;*
*- clarify admission is defined by the bound request, not the turn flag (VA-G10);*
*- recovery restores operability only, and no capture accepts until a proven reset or window;*
*- the cardless record line is presentation only;*
*- Track 3 passes on the causal target, with aggregates reported.*
*The invariant has an "ambiguous fails closed" reading; Appendix A is unchanged. Claude added*
*VA-G11, cancel without a transcript via `voice.toggle`, as a STOP decision.)*
*Created 2026-10-05*
*Base SHA: `c25899111c68ea37798c08f08aebdeee6653725a` (record the actual tip at plan commit)*
*Prerequisite audit: P7PRE — audit content `044fe10a857edc364b0fa69cd2f72be5f45067d8`, merge `3e87e7c47ed2eee4a26f53dc9c4bba7d6f16b1ee`*
*All Phase 7 decisions locked before the plan was written (developer approval 2026-10-05; full text in Appendix A).*
*Next step: Claude places it in `zola-architecture/lore/build-plans/` (uncommitted, SHA verified)
→ Track 1 Phase 1 commits it on `main` (SOP v2.2 Stage 3), then `P7-VOICEAUTH` begins.*
