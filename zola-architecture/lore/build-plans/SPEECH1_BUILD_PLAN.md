# Zola-Windows SPEECH1 Build Plan
## One audio owner: Julia streaming, exact end of speech, local listening (immediate reply)

**Base branch:** `main`
**Base SHA:** `c504e64f508ead6c8aae08f06aedd58d62f7db1e` (after the SPEECH-PRE audit merge; Track T0 records the actual
tip at plan commit)
**Audit:** SPEECH-PRE — audit commit `8bdd4347445e68d8e89e21da1b415bb0e7426684`, merge
`b2b12854f25ca3e2fe96315144281f50fe855307`; synthesis
`zola-architecture/audit/speech-pre/Zola_SPEECHPRE_Audit_SYNTHESIS.md` (27 findings: 7 HIGH, 12 MEDIUM, 8 LOW)
**Decisions:** SP-D01 to SP-D19 and VD-1, VD-4 (`claude/SPEECH_DECISIONS.md`; Brian, 2026-11-23: "Let's go with your
suggestions.")
**Theme:** Zola stops hearing herself. One supervised audio owner process speaks her replies in Cartesia Julia as they
stream, knows from the sound card's clock exactly when she has finished, and only then opens a local listener that keeps
Brian's first words and knows quickly when he has stopped. Hermes stays the brain and never touches audio. **Not in this
phase:** talk-over (parked, SP-D10), idle wake-free listening (VD-2), listening after unprompted lines (SP-D13),
Bluetooth (SP-D15), situational tone (Phase 13).

*Plan version 1.1, 2026-11-23 (v1.0 same day, approved by Brian: "Let's do it."; v1.1 adjusts T0 only, from
ChatGPT's review of the T0 prompt: no per-site comment tags, a justified monitor adapter allowed for presence/UI,
invariant-based smoke, open-ended experience check). Author: Claude. Status: **approved**. Items marked "plan detail" are
Claude's choices inside the locked decisions; Brian approves them with the plan. Experience checks are drafted in
Brian's words for him to confirm or rewrite.*

---

## Overview

| Track | Name | Scope | Complexity |
|-------|------|-------|------------|
| T0 | Speech seam | Commit this plan; one client-side speech interface in front of today's Hermes voice calls; tests that pin today's behaviour. No behaviour change. | Small-Medium |
| T1 | Owner speaks | New supervised owner process; Julia streaming from reply deltas; `safe_to_listen` opens the follow-up mic; unprompted lines and clarify questions spoken by the owner; Stop/Esc; presence from owner events; Cartesia key and guards. Hermes still records Brian. | Large |
| T2 | Owner listens | Owner holds the mic: wake word, pre-roll, VAD, local Zipformer + Parakeet, endpointing; candidates into the one admission path; Hermes mic and wake word disarmed. | Large |
| T3 | Retire superseded paths | Remove estimate/monitor listen release, Hermes `voice.*` capture and `voice.tts` calls, Deepgram TTS; keep the echo matcher. | Medium |
| T4 | Baseline delivery | One natural baseline delivery (SP-D05); spoken pre-tool acknowledgement in her own words (S51F-D02); release verification. | Small |

**Sequencing rule:** strictly in order: T0 → T1 → T2 → T3 → T4. Each track merges before the next branch is created
(one active coding track, PR-D05). T1 must be live-verified on the dev build before T2 starts, because T2 depends on
the owner's process, IPC and `safe_to_listen` being proven.

---

## Decisions this plan builds on

Locked before this plan (`SPEECH_DECISIONS.md`); tracks cite them by ID.

| ID | Decision (short) |
|----|------------------|
| SP-D04 / SP-D11 | One owner for speaking and listening, as a separate supervised local process; hands candidates to the one admission authority |
| VD-1 | No Hermes source edits; Hermes TTS and mic disarmed through supported configuration and by never calling them |
| VD-4 | Speech-to-text local; mic audio never leaves the PC |
| SP-D09 | Julia (`273f9ef7-9fc2-4def-88bb-ab108c6249ca`), pinned `sonic-3.6-2026-08-27` |
| SP-D10 | Immediate reply only; talk-over parked; owner behind one interface (Brian's words in; her reply text, "finished" and outcomes out); Brian's wording stays Zola-side |
| SP-D12 | Owner runs "Hey Zola"; Hermes never opens the mic |
| SP-D13 | D7(a) unchanged: no follow-up listening after unprompted lines |
| SP-D14 | Stop and Esc cut owner playback at once; mic button unchanged |
| SP-D15 | Bluetooth out of scope; device change and loss end in explicit outcomes, never a hang |
| SP-D16 | Retire Deepgram/Pandora once Julia is proven; no fallback voice; Cartesia down = voice fails closed, shown in the app |
| SP-D17 | `safe_to_listen` is the only listen-release authority; local STT extended (Zipformer + Parakeet, Silero VAD, 500 ms pre-roll, 0.3 s / 2.5 s endpoint); echo matcher and 2 s proactive tail kept for now; reply ids, playback outcomes, drain-idle timeout new |
| SP-D18 | No refactor track; thin speech seam first, pinned by tests |
| SP-D19 | Mouth, speaking state and Stop availability driven by owner events |
| R1 / ARCH-36 | Codes only in local Zira, never through the owner or a cloud voice |
| P7-D01 | One admission authority (`TranscriptAdmission`); no second transcript path |

## Plan details (Claude's, approved with the plan)

**PD-01 — Where the owner's code lives.** A new top-level folder `speech-owner/` in the repo (Python 3.12), ported
from the spike's mechanism files only (`owner.py`, `wasapi/*`, `listener/{gate,vad,boundary,continuation,stt}`,
`adapters/{base,cartesia}.py`, `common/{clock,events}.py` — Audit 06 §4). Harness, replay, scoring and connection-guard
code stays in the spike. Every ported file keeps a header naming its spike source and SHA-256.

**PD-02 — Its own Python environment.** The owner runs from its own virtual environment, never the Hermes venv (the
spike's rule; keeps sherpa/onnxruntime/faster-whisper versions apart from Hermes). Packages pinned in
`speech-owner/requirements.lock`. Created by a setup script, not by Zola at runtime.

**PD-03 — Models.** STT, VAD and wake-word models live in one models folder outside the repo, shared read-only by the
stable and dev builds (models are not data), with a SHA-256 manifest checked at owner start; a mismatch fails closed.
Downloaded once by the setup script from the sources the spike recorded (`speech-spike-2\models\sha256.json`), with
Brian's approval at the track's install STOP (P2-D17).

**PD-04 — IPC.** A local named pipe between client and owner, patterned on `zola-phone`, with a **role-bound name**
(stable and dev never share a pipe). Messages are small JSON events with reply ids and capture ids. No audio crosses the
pipe.

**PD-05 — Data and keys by role.** The owner resolves logs and the Cartesia key under the running build's own data root
(`ZolaClient` or `ZolaClient-dev`), never a hard-coded stable path (fixes the pattern in SPEECHPRE-AUD-24 for the new
code; the Deepgram script is retired in T3). The key file is read inside the owner, never logged, never passed on a
command line.

**PD-06 — Reply ids.** The client mints a reply id at `message.start` (Hermes deltas carry none, SPEECHPRE-AUD-16) and
uses it for every delta, complete, cancel and playback event of that reply.

**PD-07 — Playback outcomes.** The owner reports each line as `completed` (drained + tail), `partial` (stopped; frames
played known), `failed` (synthesis, connection, device or drain-idle timeout) or `uncertain` (started but drain could
not be confirmed). The client maps them to A06 and to the proactive ledger (P9-D11).

---

## Track T0 — Speech seam

### Problem

Speaking and listening are hard-wired to Hermes voice RPCs and the ffplay playback monitor across `VoiceController.cs`
(4,447 lines), the proactive session and clarify paths (SPEECHPRE-AUD-23, AUD-27). Swapping the owner in directly would
be a rebuild of the control plane, not a port.

### Files to read

- `windows-client/Zola.Client/Voice/VoiceController.cs` (capture starts `~2033–2218`; follow-up release
  `~2641–2663`, `~3070–3303`; Stop `~1192–1346`; turn start/complete `~1885–1998`)
- `windows-client/Zola.Client/Voice/ChatSpeechGateway.cs` (existing `voice.tts` wrapper, `~84–86`)
- `windows-client/Zola.Client/Voice/ProactiveSpeechSession.cs`, `ProactiveDeliveryCoordinator.cs`
- `windows-client/Zola.Client/Voice/TtsPlaybackMonitor.cs`, `CaptureLifecycle.cs`, `TranscriptAdmission.cs`
- `windows-client/Zola.Client/MainWindow.xaml.cs` (transcript and clarify handling `~725–755`)
- `windows-client/Zola.Client.Checks/` (`SpeechChecks.cs` and the check runner)
- `tools/test-gate/Run-TestGate.ps1`, `Suites.psd1`, `floors.json`

### Changes

**Build plan commit (Phase 1 of the T0 prompt).** Per SOP v3 Stage 3: commit
`zola-architecture/build-plans/SPEECH1_BUILD_PLAN.md` on its own plan branch, verify on-disk and staged-blob SHA-256
against the prompt, merge `--no-ff`, then branch `sp1-t0`.

**New `windows-client/Zola.Client/Voice/SpeechEngine.cs` (interface) and `HermesSpeechEngine.cs` (today's
implementation).** One interface for everything that makes her speak or starts/stops listening:
- speaking: begin reply (reply id), reply text delta, reply text complete, speak one line (clarify question,
  unprompted line), stop speaking;
- listening: start capture (kind, clarify id), stop/cancel capture, wake arm/disarm/pause/resume;
- events out: speaking started, speaking finished (with outcome), capture state, transcript candidate.
`HermesSpeechEngine` forwards to exactly today's calls (`voice.tts`, `voice.record`, `wake.*`, `voice.toggle`) and
today's monitor/estimate signals, unchanged. `ChatSpeechGateway` is absorbed or wrapped, not duplicated.

**`VoiceController.cs`, `ProactiveSpeechSession.cs`, clarify speak path, `MainWindow.xaml.cs`:** replace direct Hermes
voice calls with calls on the interface. No logic change. Comments only where they explain a non-obvious constraint
(traceability comes from the inventory, the tests and the review diff). Presence or UI consumers of the playback monitor
may keep a narrow, justified adapter in T0 if moving them would change UI behaviour; listen-release consumers go through
the seam.

**Characterization checks (new, `Zola.Client.Checks`):** pin today's behaviour through the seam, at minimum:
follow-up opens only after the monitor bout + quiet rule; estimate cannot open while a bout is active (P7-D06);
clarify answer binds to the open question only; Text mode and lock drop captures; Stop speaking cancels follow-up and
cuts TTS; D7(a) refuses capture during the 2 s proactive tail; one capture outstanding at a time.

### Exit criteria

- [ ] Plan committed per Stage 3 with both hashes verified; `sp1-t0` branched from the plan merge
- [ ] No Hermes voice RPC is called anywhere except inside `HermesSpeechEngine` (CURSOR-RUN grep, listed in the
      progress doc)
- [ ] New characterization checks exist and pass; they also pass on `main` before the change (run recorded)
- [ ] `dotnet build` Release, 0 new warnings; `Run-TestGate.ps1` PASS with Zola closed
- [ ] Dev smoke (HUMAN-RUN, dev build): wake word, a long reply, follow-up answer, a clarify answered by voice,
      Stop speaking, one unprompted line — required orderings and invariants hold (e.g. follow-up never opens before
      the playback-finished condition) and log event names and fields are unchanged; anything not verified is listed
- [ ] Experience check (open question, Brian's words verbatim): *"Did anything feel different?"* — any difference is
      investigated against the no-behaviour-change goal

**Complexity:** Small-Medium
**Primary risk:** a call site missed in `VoiceController.cs` keeps calling Hermes directly, so T1's swap leaves a hidden
second speaking or listening path.

---

## Track T1 — Owner speaks

### Problem

Her reply is cut into sentences, each synthesized and played separately; gaps between them open the follow-up mic and
her next sentence becomes Brian's turn (SPEECHPRE-AUD-01). Nothing in Zola knows from the device clock when she has
finished (AUD-02). `voice.tts` ignores the TTS-off setting (AUD-05). Mouth and Stop depend on the ffplay monitor
(AUD-23).

### Files to read

- Everything in T0, plus the new seam
- `windows-client/Zola.Client/` supervision: `SupervisedPython.cs`, `PhoneProcess.cs`, `WatcherProcess.cs` (pattern
  for start, restart limits, latch, job object, role-bound paths)
- Presence: `PresenceAnimator` and the HUD speaking state; `AudioSessionInterop.cs`
- Profile template `VOICE_CONFIG.md` (TTS keys) and the client's voice-sync calls (`SyncVoice*`)
- Spike (read-only, source of the port): `C:\Users\test\Dev\zola-spikes\speech-spike-2\owner.py`,
  `wasapi\render.py`, `wasapi\mmcss.py`, `adapters\base.py`, `adapters\cartesia.py`, `common\clock.py`,
  `common\events.py`, `runs\phase2_eval\config_frozen.json`
- Hermes at pin `345cd2b…` (read-only): `methods_voice.py` (`HERMES_VOICE_TTS`, `voice.toggle`), `prompt_turn.py`
  (`message.delta` / `message.complete`)

### Changes

**New `speech-owner/` (PD-01, PD-02):** the speaking half only in this track:
- one WASAPI render stream per reply on the default device; Cartesia WebSocket with the pinned model; text fed as
  deltas arrive (flush on sentence ends and on reply complete);
- `playback_finished` from `IAudioClock` position ≥ frames written; `safe_to_listen` = finished + 220 ms;
  drain-idle failure timeout; reply ids; late audio for a cancelled reply dropped by id;
- stop: cancel playback at once, drop queued audio, report `partial` with frames played (PD-07);
- device change or loss during a reply: explicit `failed` outcome, re-open on the current default device for the next
  reply (SP-D15);
- Cartesia unreachable or auth error: `failed`, no fallback voice (SP-D16);
- events over the pipe (PD-04): `speaking_started`, `playback_finished`, `safe_to_listen`, `released` (outcome),
  `owner_ready`, `owner_error`.

**Client — `SpeechOwnerProcess.cs` (new):** supervised like `zola-phone` (start with the client, job object, restart
limits, latch, role-bound pipe and data root). Owner down → voice output fails closed; a Core Systems row "Voice" shows
it; a conversation line tells Brian once (no spoken fallback).

**Client — `OwnerSpeechEngine.cs` (new, implements the T0 interface for speaking):**
- begin reply at `message.start` (PD-06 reply id), forward `message.delta` text and `message.complete`;
- clarify questions and unprompted lines go to the owner's "speak one line"; the client no longer calls `voice.tts`
  (AUD-05);
- **listening stays on Hermes in T1**: the follow-up and clarify captures still use `voice.record`, but they open only
  on the owner's `safe_to_listen` (SP-D17), never on monitor silence or an estimate;
- D7(a) and the 2 s proactive echo tail stay as they are (SP-D13, SP-D17).

**Hermes TTS disarmed (VD-1):** `HERMES_VOICE_TTS` off through `voice.toggle` at session start and after every voice
re-sync, so Hermes never synthesizes; checked by a log assertion each turn. Deepgram configuration is left in place
until T3 but is never reached.

**Stop and Esc (SP-D14):** call the owner's stop; the line's outcome is recorded; Stop is available for unprompted
lines too (KI-S51F-STOP). Mic button while she speaks: unchanged.

**Presence (SP-D19):** mouth animation, HUD "Speaking" and `CanStopSpeaking` take `speaking_started` /
`released` from the owner. The ffplay monitor no longer drives listening; it may stay attached for comparison logging
only in this track.

**Keys and privacy (PD-05, SP-D16):** Cartesia key read from the role's `secrets\cartesia_api_key.txt` inside the
owner; Hermes tool guard rows extended to block the Cartesia key path and filename (same pattern as the Deepgram
rows). **Brian updates the privacy page to name Cartesia before any live use on stable** (SPEECHPRE-AUD-25); the dev
smoke may use Cartesia under the existing spike approval.

**Logging:** lengths, ids, outcomes and timings only — never reply text (P7-D08).

**Tests:** owner unit tests (pytest, new suite in `Suites.psd1` with a floor): drain + tail before `safe_to_listen`;
drain-idle timeout → `failed`; stop → `partial` with frames; late audio after cancel dropped; device loss →
`failed` then recovery; Cartesia error → `failed`, no retry storm; key never in logs. Client checks: follow-up opens only
on `safe_to_listen`; no `voice.tts` call anywhere; owner down → voice fails closed with one notice; presence follows
owner events.

### Exit criteria

- [ ] Hermes never synthesizes speech during the smoke (log evidence for every turn) and `voice.tts` is never called
- [ ] Follow-up capture opens only after `safe_to_listen`; no estimate or monitor release opens it (check + logs)
- [ ] Owner crash during a reply: client and Hermes keep running; voice fails closed; one notice; owner restarts within
      the supervision limits
- [ ] Codes still read in Zira, never through the owner (R1 check unchanged and passing)
- [ ] `Run-TestGate.ps1` PASS with Zola closed, including the new owner suite at its floor
- [ ] Dev isolation check (PR-D02): owner data root, pipe name and key path all resolve to the dev role
- [ ] Smoke (HUMAN-RUN, dev build, laptop speakers, ~25% volume):
  - 5 long replies with tool pauses (baseline-style questions): **0** of her sentences admitted as Brian's;
  - answer her right after she finishes, 5 times: the answer is captured (opening words may still be clipped — T2
    fixes pre-roll);
  - Stop mid-reply and on an unprompted line: silent at once, line recorded `partial`;
  - mouth moves while she speaks and stops when she stops;
  - CPU and memory of the owner and the client recorded during the smoke (no pass mark; baseline for T2)
- [ ] Experience checks (Brian to confirm wording): *"When she gives a long answer with pauses, she doesn't answer
      herself anymore." "She sounds like Julia, and she starts talking about as soon as the answer appears."*

**Complexity:** Large
**Primary risk:** a residual Hermes speech path (voice re-sync turning TTS back on, heartbeat or background completions)
makes two voices speak, or the follow-up still opens from a stale monitor release.

---

## Track T2 — Owner listens

### Problem

Hermes owns the mic for the wake word and recording (P2-D01, AUD-08); recording has no pre-roll, so first words are
clipped (AUD-10, KI-S51F-CLIP); end of speech waits a fixed 1.5 s of silence; admission depends on Hermes capture status
signals (AUD-11). The serve audio stream is where the S51 Group A crashes occurred (AUD-14).

### Files to read

- T0 and T1 files; `CaptureLifecycle.cs` (Accepting, cancel reasons, correlation), `TranscriptAdmission.cs` (order
  `~57–117`)
- Hermes at pin (read-only): `wake_word.py` (`~521–526`, `~6–8`), `methods_voice.py` (`wake.*`, `voice.record`,
  `~309–543`), profile `wake_word` keys
- Spike (read-only): `wasapi\capture.py`, `listener\__init__.py`, `gate.py`, `vad.py`, `boundary.py`,
  `continuation.py`, `stt.py`, `freeze_code_bind.json`, `SPEECH-SPIKE-2_Progress.md` (Phase 3 fixes)

### Changes

**`speech-owner/` — the listening half:**
- one WASAPI capture stream (RAW where available) held by the owner; QPC-mapped timestamps;
- **wake word (SP-D12):** sherpa keyword spotting for "hey zola" (today's model and phrase), running in the owner
  while idle; on detection, a Wake capture starts with pre-roll;
- captures of every kind (Wake, Manual, FollowUp, EchoReopen, Clarify) opened by client request with a client-minted
  **capture id**; follow-up and clarify captures only from `safe_to_listen` (T1);
- 500 ms pre-roll that never reaches into her playback; Silero VAD; provisional candidate after 0.3 s silence, merged
  if Brian resumes within 2.5 s (hold on in-window speech start); S1 streaming partials + S3 final, all local
  (SP-D17, VD-4); at most one candidate per capture; cancelled captures discard audio and emit nothing;
- mic loss or default-device change: discard the capture in progress, explicit `capture_failed`, reopen on the
  current default device into the state the gate should be in now (SP-D15);
- events: `wake_detected`, `capture_accepting(capture_id)`, `capture_candidate(capture_id, text, timings)`,
  `capture_ended(capture_id, reason)`, `capture_failed`.

**Client — `OwnerSpeechEngine.cs` listening:** capture requests go to the owner; `capture_accepting` replaces
Hermes's listening status as the Accepting signal; `capture_candidate` enters `CaptureLifecycle` and
`TranscriptAdmission` exactly as `voice.transcript` did — **the only route to `TranscriptReady`** (P7-D01). Clarify ids,
Text mode, lock (S32), mic button, hotkey and one-build rules unchanged in behaviour. Hermes's `voice.transcript` is
ignored and logged if it ever arrives (it shouldn't).

**Hermes mic and wake disarmed (VD-1, SP-D12):** profile `wake_word.enabled: false` in the template and the dev
profile; the client never calls `wake.*` or `voice.record`; a startup assertion logs if serve reports an open input
stream. Stable's live profile is changed only at promotion, by the promotion step, with Brian's approval.

**Tests:** owner: pre-roll never includes playback-time samples; one candidate per capture; cancel → no candidate;
resume within 2.5 s merges; device loss → `capture_failed` and recovery; wake detection on recorded fixtures (the
spike's tuning recordings are Brian's voice — use them **only** if Brian approves; otherwise synthetic fixtures).
Client: admission from owner candidates uses the same `Decide`; Hermes transcript ignored; clarify binding; lock/Text
drops.

### Exit criteria

- [ ] Serve never opens a capture device during the smoke (log assertion + process audio session check)
- [ ] Every admitted transcript came through `capture_candidate` → `TranscriptAdmission` (log evidence); zero from
      `voice.transcript`
- [ ] "Hey Zola" works from idle: 10 tries at Brian's seat, ≥ 9 detected; 10 minutes of normal room sound and a long
      reply produce no false wake (pass marks proposed, Brian confirms at the T2 STOP)
- [ ] Opening word kept on ≥ 9 of 10 immediate answers; mid-thought pauses (U9-style) not split, 0 of 3; median time
      from Brian stopping to his turn being submitted ≤ 1.2 s (spike measured 0.32 s)
- [ ] Spoken send approval ("Approved. Send it.") still works on the dev test account from owner STT (P8)
- [ ] Mic disabled and re-enabled mid-capture: explicit failure, recovery, no hang, no half-utterance submitted
- [ ] Owner + client memory and CPU recorded with Zola idle and during a conversation; client stays under its 900 MB
      cold-rest gate
- [ ] `Run-TestGate.ps1` PASS with Zola closed; dev isolation check passes
- [ ] Experience checks (Brian to confirm wording): *"I can answer her right away and she gets my first word." "If I
      pause to think mid-sentence, she waits for me." "Hey Zola works like it always did."*

**Complexity:** Large
**Primary risk:** wake-word accuracy or CPU in the owner falls short of today's Hermes wake word, or a capture-id
mismatch lets a late candidate through admission after a cancel.

---

## Track T3 — Retire superseded paths

### Problem

After T1 and T2, old paths remain wired: estimate and monitor listen release, Hermes `voice.*` capture calls, the
Deepgram TTS provider, profile keys, plugin and tests (AUD-21, AUD-23, AUD-26). Left in place they are a second path that
could come back to life.

### Files to read

- `HermesSpeechEngine.cs` (T0), `VoiceController.cs` follow-up and estimate code, `TtsPlaybackMonitor.cs`
- `hermes-plugins/zola_tts/deepgram_tts.py`, `hermes-plugins/zola_tts/tests/test_deepgram_tts.py`
- Profile template `VOICE_CONFIG.md`; `identity/VOICE_CONFIG.md`; guard rows for the Deepgram key
- `Suites.psd1` / `floors.json` (tts suite floor)

### Changes

- Remove the estimate releases, the 450 ms + 0.5 s quiet window and the monitor's role as listen authority (SP-D17).
  Keep the monitor only if another consumer still needs it after T1; otherwise remove it.
- Remove `HermesSpeechEngine` and every remaining Hermes `voice.*` / `wake.*` capture call; the seam keeps one
  implementation.
- Retire Deepgram TTS (SP-D16): provider config in the template, the `zola_tts` command script and its tests, the
  Deepgram key guard rows only if no other tool needs them (the Deepgram key file itself is left for Brian to delete;
  Deepgram STT was never used for listening). Lower the tts suite floor with a recorded reason (PR-D01: no silent
  exclusion).
- `identity/VOICE_CONFIG.md` and SOUL voice lines updated to Julia (needs Brian's approval of the wording, per A07
  §11 note).
- **Kept:** the echo matcher (P7-D07) and the 2 s proactive tail (SP-D17), Zira code reads (R1).

### Exit criteria

- [ ] No code path can open the mic or speak except through the owner (CURSOR-RUN grep for Hermes voice RPCs, ffplay
      monitor listen use, Deepgram TTS references; results in the progress doc)
- [ ] Characterization checks from T0 updated to the owner behaviour, all passing; no check deleted without a recorded
      reason
- [ ] `Run-TestGate.ps1` PASS with Zola closed; floors changed only with recorded reasons
- [ ] Dev smoke repeats the T1 and T2 smoke sets with the same results
- [ ] Experience check: *"Everything still works the same as after T2."*

**Complexity:** Medium
**Primary risk:** removing the monitor breaks a consumer nobody listed (proactive delivery ledger, presence timing), or
a test floor is lowered without evidence.

---

## Track T4 — Baseline delivery

### Problem

SP-D05 promises one natural baseline delivery; the pre-tool acknowledgement in her own words moved to the speech track
(S51F-D02). With streaming, text she writes before a tool call is spoken as it arrives, but whether she writes it, and
how her replies read aloud, are prompt and SOUL matters.

### Files to read

- SOUL speaking rules and the voice-mode guidance in the profile template
- T1's delta forwarding and flush points; `tool.start` handling in `MainWindow.xaml.cs`
- `claude/NUPLEX_SANDBOX_VS_ZOLA_2026-11-22.md` §"Where the sandbox is ahead" is **background only** for wording ideas
  (G-NO-CROSS-SCOPE: no code or rules copied)

### Changes

- SOUL/voice guidance: speech-shaped replies (short first sentence, no lists read aloud, numbers said the way a person
  says them), and a short line in her own words before a lookup that may take time; never a hard-coded phrase (Brian,
  2026-11-09). Wording drafted by Claude, approved by Brian before Cursor applies it.
- Owner flushes text at `tool.start` so a pre-tool line is spoken before the wait, not after.
- **Release verification for the phase** (below).

### Exit criteria

- [ ] SOUL/voice wording applied exactly as Brian approved
- [ ] On 5 questions that need a lookup, she says something in her own words before the wait at least 4 times, and the
      words vary (HUMAN-RUN, dev)
- [ ] Release verification passes (below)
- [ ] Experience check: *"She sounds like she's talking with me, not reading to me."*

**Complexity:** Small
**Primary risk:** prompt changes alter her non-voice behaviour (Text mode replies, clarify behaviour) — checked by the
scenario run.

---

## Release verification (SOP Stage 7)

On `main` with T0–T4 merged, dev build:
- `Run-TestGate.ps1` PASS with Zola closed.
- Scenarios: SC-S51F-SM1, SC-S51F-EXP-BEEP, SC-S51F-SM2 / EXP-LOST, SC-PROC1-S1, the privacy/dev-isolation scenarios,
  and every new scenario below.
- Integration checks: one 10-minute voice session mixing long replies with tool pauses, immediate answers, a clarify
  answered by voice, an unprompted line with Stop, a typed turn in Text mode, a code read in Zira, and an owner restart
  mid-session.
- Brian confirms the phase's experience checks together.
- **Before promotion to stable:** privacy page names Cartesia; stable profile changes (TTS off, wake word off in Hermes)
  applied by the promotion step; stable backup and restore drill as usual.

**New scenarios (added at lore closeout once passed):** no self-admission on long paused replies; opening word kept;
mid-thought pause not split; follow-up opens only after `safe_to_listen`; owner down fails closed with one notice;
"Hey Zola" from idle; spoken send approval from owner STT; Stop cuts an unprompted line; Cartesia unreachable fails
closed without a fallback voice. **Conditional:** first/last-word clipping on the laptop speakers, if Brian confirms
that's where he heard it (open question, SP-D15).

---

## Lore closeout (after all tracks merge)

**DESIGN_DECISIONS.md:** record SP-D01 to SP-D19, VD-1 and VD-4 as the speech track's decisions, with
supersession notes: P4-D18 and P7-D06 (listen-release role superseded by SP-D17), P2-D01 (mic and speaker move from
serve to the owner — SP-D11/SP-D12), P2-D02 (extended by SP-D17), P2-D14/P7-D07 (kept), P9-D14 (Pandora superseded by
SP-D09/SP-D16), D7(a) (unchanged, SP-D13), P4-D28 (still off; talk-over parked, SP-D10).
**OPEN_QUESTIONS.md:** S17 (precise end of playback) RESOLVED by T1; S77 (ordinary-reply echo) RESOLVED if the
release scenarios pass, else updated; S36 annotated (talk-over parked, SP-D10); S19, S1, S5 unchanged; S103 annotated
with the owner moving capture out of serve.
**KNOWN_ISSUES.md:** close KI-S51F-CLIP, KI-S51F-STOP and KI-S51F-ECHO if their scenarios pass; KI-S51F-MIC stays
(mic button unchanged, SP-D14); KI-S51-PA annotated (serve no longer opens audio devices); new issues filed with
severity.
**SCENARIO_LIBRARY.md:** the new scenarios above. **EXPERIENCE_LOG.md:** the phase's experience checks.
**ROADMAP.md:** speech track SP1 COMPLETE with track merge SHAs and tags; next: Phase 11 (P11PRE), per SP-D08.
**A07 as-built (§11):** updated through the SOP's lore path, not edited mid-track.

## Exit checklist

- [ ] T0 merged — seam in place, behaviour unchanged, characterization checks passing
- [ ] T1 merged — owner speaks Julia; follow-up only after `safe_to_listen`; Hermes never synthesizes
- [ ] T2 merged — owner holds the mic; Hermes never opens a capture device; one admission path
- [ ] T3 merged — superseded paths and Deepgram TTS removed; echo matcher kept
- [ ] T4 merged — baseline delivery approved by Brian; release verification passed
- [ ] No Hermes source change anywhere in the phase (VD-1): `hermes-agent` clean at the pin after every track
- [ ] No mic audio, transcript or reply text in any log; no key in any log, command line or repo file
- [ ] Stable and dev resolve separate owner data roots, pipes and keys (isolation check after T1 and T2)
- [ ] `Run-TestGate.ps1` PASS on `main` after the last merge
- [ ] Lore closeout complete as listed above; release tag `sp1-closed`

## What this phase explicitly defers

| Item | Reason | When |
|------|--------|------|
| Talk-over / barge-in, echo cancellation | Parked; mechanism didn't converge (SP-D10, `SPEECH_SPIKE_2_PAUSED.md`) | Later, on new evidence |
| Listening after unprompted lines (lift D7(a)) | SP-D13: after exact end of speech proves itself | Separate step after promotion |
| Idle wake-free listening, wake-word fallback, ambient rule | VD-2, VD-5, VD-3 open | Brian's call |
| Bluetooth tuning and measurements | Brian doesn't use Bluetooth (SP-D15) | Only if that changes |
| Retiring the echo matcher and the 2 s tail | Needs live evidence (SP-D17) | After release, on evidence |
| Situational tone | SP-D05 | Phase 13 |
| Speaker recognition, streaming cognition | A07 §7–§8 vision | Later phases |
| Mic button stopping her speech | Bound to talk-over (SP-D14) | With talk-over |
| A more personal spoken lost-request line | S51F follow-up; text line today | Later speech work |
| Opening-word STT policy (Zipformer ∪ Parakeet, hotwords) | Spike finding, untested | If T2 smoke shows misses |
| Conversation-layer port (e.g. Nuplex) | Provisional direction only | Own decision |
| Cartesia voice withdrawal policy | SP-D09 UNRESOLVED (Brian to ask Cartesia) | Outside the build |

## Complexity legend

| Track | Complexity | Primary risk |
|-------|------------|--------------|
| T0 — Speech seam | Small-Medium | A missed direct Hermes voice call survives the seam |
| T1 — Owner speaks | Large | A residual Hermes speech path or stale monitor release |
| T2 — Owner listens | Large | Owner wake word or capture-id handling falls short |
| T3 — Retire superseded paths | Medium | Removing the monitor breaks an unlisted consumer |
| T4 — Baseline delivery | Small | Prompt changes leak into non-voice behaviour |

---

*SPEECH1 Build Plan version 1.1 — created 2026-11-23.*
*Base SHA: `c504e64f508ead6c8aae08f06aedd58d62f7db1e` (T0 records the tip at plan commit).*
*Prerequisite audit: SPEECH-PRE — merge `b2b12854f25ca3e2fe96315144281f50fe855307`.*
*All decisions locked before the plan (SP-D01 to SP-D19). Next step: Brian approves the plan; Claude writes the T0
prompt, which commits this plan to `zola-architecture/build-plans/SPEECH1_BUILD_PLAN.md` on `main` before branching
`sp1-t0`.*
