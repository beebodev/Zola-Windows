# P2-VOICE Progress — Track 1: Voice Core

## Branch

- Branch: `track1-voice-core`
- Plan-commit SHA on `main`: `c8c83f7dcf146c2626d18adc840c0fad645f6903`
- Base SHA (branch created from the plan-commit): `c8c83f7dcf146c2626d18adc840c0fad645f6903`
- Build-plan v1.1 commit on `track1-voice-core`: `791769362190fa7b50058f13c692fb360a19e1b5`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Commit Build Plan, Branch, and Progress Document | COMPLETE |
| 2 | Read, Understand, and Probe Dependencies | COMPLETE |
| 3 | Profile Config, VOICE_CONFIG.md, and Approved Dependencies | COMPLETE |
| 4 | Build: Event Plumbing and VoiceController | COMPLETE |
| 5 | Build: UI Wiring (Mic, Hotkey, Mode Toggle, Indicator, Submit) | COMPLETE |
| 6 | Smoke Test | COMPLETE |
| 7 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Commit the Phase 2 build plan unchanged; write the Track 1 `stt` / `tts` / `voice` keys into the live Zola profile and `VOICE_CONFIG.md`; install missing Python voice dependencies only after an explicit approval of the exact command; add voice input to the Windows client over the existing `/api/ws` (event plumbing, `VoiceController`, mic, `Ctrl+Space`, Voice/Text toggle, indicator, one submit path). No spoken replies, follow-up listening, wake word, client-side audio, or `/api/audio/*`. `hermes-agent` is read-only.
- **G-ARCH:** Build plan is truth. Stop and flag conflicts; do not silently deviate.
- **G-PATTERN:** Read every relevant file in full before any change. No changes from partial reads or memory.
- **G-NOCHANGE:** Edits limited to the files and lines described in the current task. Phase 1 chat, cancel, unreachable state, sessions, and process lifecycle stay unchanged.
- **G-COMMENT:** Every changed line or block carries `// P2-VOICE: [rationale] — P2-D0X` (XAML comment form in markup; one-line prose note per block in `VOICE_CONFIG.md`). Do not comment unchanged lines.
- **G-STOP:** Stop after each phase and wait for that phase's explicit proceed message.
- **G-CLOSEOUT:** Closeout begins only on the explicit message "proceed to closeout".
- **G-LORE-SCOPE:** Do not add, resolve, or update `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, or any project state-audit document in this track, including closeout. Committing `PHASE2_BUILD_PLAN.md` in Phase 1 is not a lore edit.
- **G-NO-CROSS-SCOPE:** Android Zola and Ava voice stacks are out of scope. Do not read, cite, or build against them.
- **G-DEPS:** Never run `pip`, `uv`, or any installer, and never trigger a Hermes lazy-install, without the developer's explicit approval of the exact command. Import probes are allowed.
- **G-CONST:** Every JSON-RPC method name, event type string, payload field name, and timing value added to C# is a named constant.

## Discrepancies

None at start. Documents of truth read before Phase 1: `PHASE2_BUILD_PLAN.md` (Grounding summary, `P2-D01`–`P2-D11`, Track 1), `Zola Master Architecture Plan.md` (Vocal Computing, §3 Current Sequential Model, §12, External API Strategy Tier 1 Windows Track note), `PHASE1_BUILD_PLAN.md` (`P1-D01`, `P1-D02`, `P1-D04`), `P1-CLIENT_Progress.md`, `P1-SESSION_Progress.md`, `P1-MEMORY_Progress.md`, WINH09 Audit 03 and Audit 06, `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`. HEAD on `main` matched `8964bdce9a7361e3887a43b3dd381f5f979e9a64` and the only working-tree change was untracked `PHASE2_BUILD_PLAN.md`.

Phase 2 flags (phase stopped BLOCKED; no client source changed):

1. **Unapproved lazy install (G-DEPS).** `stt.provider` is unset in the live profile, so `check_voice_requirements()` → `_get_provider` → `_detect_local_backend` calls `_try_lazy_install_stt()` → `tools.lazy_deps.ensure("stt.faster_whisper")` when faster-whisper is missing. `security.allow_lazy_installs` is true. That probe installed into the Hermes venv, without an approved command: `faster-whisper==1.2.1`, `sounddevice==0.5.5`, `numpy==2.4.3` (the `stt.faster_whisper` pin list). Imports failed before that call and succeed after it. `hermes-agent` `git status` stayed clean because `.venv` is gitignored.
2. **Running-turn `prompt.submit` is not a refusal (G-ARCH).** The track prompt says to hold a transcript when a submit would be refused and send it after `message.complete`. Source does not refuse. Default `display.busy_input_mode` is `interrupt`. The agent sets `_supports_active_turn_redirect` true, so a text submit while `session["running"]` is true tries `agent.redirect()` and returns `{status: "redirected"}`. If redirect declines, the text is queued, the live turn is interrupted, and the reply is `{status: "queued"}`. `running` becomes false in the turn thread's `finally`, after `message.complete`. `_run_post_turn_followups` then drains the queue. `PER_SESSION_EXCLUSIVE_SUBMIT` is the cross-process lease flag, not this busy path. A same-process lease miss is error 4090 before the busy handler, and only when this runtime does not already hold the slot. Submitting immediately and also holding for a second submit would send the transcript twice. Redirect can fold the interjection into the live turn instead of starting a new one.

Phase 1 defect: each new turn cleared the previous assistant bubble (typed and spoken). Fixed in P2-VOICE with developer approval. Typed follow-ups now keep earlier replies on screen.

## Dependency probe

Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`. `ZOLA_HERMES_PYTHON` was unset. The checkout venv exists, so PATH was not used. `HERMES_HOME` was `C:\Users\test\AppData\Local\hermes\profiles\zola`. Working directory was `C:\Users\test\Dev\hermes-agent`.

| Probe | Before the requirements call | After `check_voice_requirements()` |
|---|---|---|
| `import sounddevice, numpy` | `ModuleNotFoundError: No module named 'sounddevice'` | success |
| `sounddevice.query_devices()` default input | not reached | `Microphone Array (Realtek(R) Au` (PortAudio's name is truncated) |
| `sounddevice.query_devices()` default output | not reached | `Speakers (Realtek(R) Audio)` |
| `import faster_whisper` | `ModuleNotFoundError: No module named 'faster_whisper'` | success (`faster-whisper==1.2.1`) |
| `check_voice_requirements()` | this call lazy-installed, then returned `{'available': True, 'audio_available': True, 'stt_available': True, 'missing_packages': [], 'details': 'Audio capture: OK\nSTT provider: OK (local faster-whisper)', 'environment': {'available': True, 'warnings': [], 'notices': []}}` | same shape; not re-run, because a second call is unnecessary once the packages import |
| `lazy_deps.feature_install_command("stt.faster_whisper")` | `uv pip install 'faster-whisper==1.2.1' 'sounddevice==0.5.5' 'numpy==2.4.3'` | unchanged |
| same, `venv_pip=True` | `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m pip install 'faster-whisper==1.2.1' 'sounddevice==0.5.5' 'numpy==2.4.3'` | unchanged |
| `security.allow_lazy_installs` | `True` (default; the live `config.yaml` has no `security` section) | unchanged |

Approved install command: none. The packages above were installed by the probe's lazy path, not by an approved command.

`hermes-agent` `git status` after the probes: clean. `.venv` and `__pycache__` are gitignored.

## Phase 2 understanding

Event frame (`tui_gateway/server.py` `_event_frame`): `{"jsonrpc": "2.0", "method": "event", "params": {"type": <event>, "session_id": <sid>, "payload": <dict>}}`. The `payload` key is omitted when the payload is `None`.

- `voice.status` payload: `{state: str}` (`listening`, `transcribing`, `idle`, and any other recorder state).
- `voice.transcript` payload: `text` optional, `stop_phrase` optional, `typed` optional, `no_speech_limit` optional. Variants emitted by `methods_voice.py`: `{text}`, `{stop_phrase: true, text}` (spoken stop, or full-duplex stop), `{stop_phrase: true, typed: true}` with no `text` for a typed stop (`_typed_stop_phrase_response` emits that and returns `{voice_stopped: true}`), `{no_speech_limit: true}`.
- `voice.interrupted`: no payload.
- `wake.detected` payload: `{phrase: str, profile: str | null, start_new_session: bool}`.

`voice.record action=stop` calls `stop_continuous(force_transcribe=True)` and returns `{status: "stopped"}`. The client then gets `voice.status` `transcribing`, then either a transcript or nothing, then `voice.status` `idle`. If the user said nothing, `rec.stop()` yields no WAV, `_turn_transcript` returns no text, and no `voice.transcript` is emitted for that one stop. `no_speech_limit` fires only on the third consecutive silent cycle (`_CONTINUOUS_NO_SPEECH_LIMIT = 3`). With `auto_restart=False`, `start_continuous` does not reset that counter.

`Ctrl+Space` is not handled. `OnComposerKeyDown` handles Enter only. `MainWindow.xaml` has no keyboard accelerator.

`CallAsync` is private. `SessionId` is already a public getter. A Phase 4 public send wrapper still has to be added. `RpcReply` is a private nested record.

Submit path today is `MainWindow.OnSendClick`: trim the composer; return when the session is not ready, a turn is streaming, the backend is unreachable, or the text is empty; clear the composer; `AddBubble("You", text)`; set streaming; status `Sending…`; `ChatSocket.SubmitAsync`. The factored method `SubmitTurnAsync(string text)` should own the bubble, the streaming flags, `SubmitAsync`, and the two catch paths. The Send handler keeps the composer read and clear, then calls it. `TranscriptReady` calls the same method and does not clear the composer. Developer decision after Phase 2: transcripts submit immediately, including during a running turn. There is no client-side hold.

## Phase 2 resolution

The developer kept the lazy-installed packages and chose immediate submit. No further install command was approved. Phase 2 is complete on that decision. v1.1 of the build plan records the same rules (`P2-D10`, `P2-D12`) and was committed on this branch as `791769362190fa7b50058f13c692fb360a19e1b5`. Nothing in v1.1 conflicted with Phases 1–2.

## Phase 3

`pip check` on `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`: `No broken requirements found.`

Live `config.yaml` before this phase had `model`, `agent`, `_config_version`, and `memory` only, plus the existing comments. Appended, without changing those keys:

```yaml
stt:
  provider: local
  local:
    model: base
tts:
  provider: edge
  edge:
    voice: en-US-AriaNeural
voice:
  silence_duration: 1.5
  barge_in: true
  stop_phrases: ["stop"]
  thinking_sound: true
security:
  allow_lazy_installs: false
```

`security.allow_lazy_installs: false` is the developer-approved addition that v1.1 also puts on the Track 1 key list (`P2-D10`).

Verification, same interpreter and `HERMES_HOME` as Phase 2, after the key was false:

- `load_config()` reports `allow_lazy_installs` false.
- `_get_provider(_load_stt_config())` returned `local`.
- `check_voice_requirements()`: `available`, `audio_available`, and `stt_available` all true. Details: `Audio capture: OK` / `STT provider: OK (local faster-whisper)`.
- `_load_local_whisper_model("base", device="auto", compute_type="auto")` loaded in 12.805 seconds on device `cpu`, compute type `int8_float32`.

Approved install command: none. Packages accepted after the Phase 2 lazy-install: `faster-whisper==1.2.1`, `sounddevice==0.5.5`, `numpy==2.4.3`.

`dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors. No client files changed. `hermes-agent` `git status` was clean at the pinned commit `345cd2b057a452236de401d3534b8502a7465e8d`.

## Phase 4

`DispatchEvent` now routes `voice.status`, `voice.transcript`, `voice.interrupted`, and `wake.detected`. The session-id filter and the `message.*` / `status.update` / `error` cases are unchanged. `wake.detected` is parsed and nothing subscribes. There is no client-side transcript hold.

`dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors. `hermes-agent` git status was clean.

Busy-submit events, read before wiring (`agent.redirect` in `agent/interrupt_control.py`, `_handle_busy_submit` / `_drain_queued_prompt` in `tui_gateway/session_auto_continue.py`, `_run_prompt_submit` in `tui_gateway/prompt_turn.py`):

- `{status:"redirected"}`: `agent.redirect` keeps the same turn. The gateway does not emit `message.start` for that submit. The open turn may keep sending `message.delta`, then one `message.complete`. On this profile the first branch is Codex `request_steer` when that method exists; success is still the same turn. If redirect returns false, the submit falls through to the queued path instead.
- `{status:"queued"}`: the text is queued and the live turn is interrupted. That turn emits `message.complete` first. `running` is cleared in the turn thread's `finally`. `_run_post_turn_followups` then drains the queue, and `_run_prompt_submit` emits a new `message.start`. The new start is after the previous complete on the same socket, so it does not arrive into an already-open assistant bubble if the client finalizes on `message.complete` before handling the later `message.start`.

## Phase 5

`MainWindow` has one `VoiceController`. Send and `TranscriptReady` both call `SubmitTurnAsync`. The typed Send guard still returns while a turn is streaming. A transcript during a running turn adds the You bubble and does not clear the open assistant bubble. `redirected` keeps streaming into that bubble. `queued` still ends it on `message.complete`, and the next `message.start` opens the next bubble.

Redirect display split was not implemented. `OnMessageCompleted` passes the `message.complete` text into `FinishTurn`, and `StyleLive` sets the live bubble's body to that text whenever it is non-empty. `ChatSocket.FinalText` treats `text` / `rendered` as the whole bubble, not another delta. A closed prefix bubble plus a new bubble overwritten with that full text would show the prefix twice.

`Ctrl+Space` is a `KeyboardAccelerator` on the window's root grid. `Window` has no `KeyboardAccelerators` collection in this WinUI build.

`dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors.

Local check: the window reached "Session ready." with voice state Idle and Mic: off. Switching to Text made `voice.toggle status` return `enabled: false` (available, audio, and stt all true). Switching back showed Idle and `enabled: true`. The client was then closed. `hermes-agent` stayed clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

## Phase 6

Client built with 0 warnings and launched. Window showed Voice, Idle, Mic: off, and "Session ready." The mic button was enabled. The redirected display split was not implemented.

Smoke test failed at step 5: speaking over a running turn did not interrupt it. Steps 6–8 and the cancel / kill-serve checks were not run. The window was still on session `40995fb9`, Voice, Idle, Mic: off, "Session ready."

`agent.log` for that session (INFO only; barge-in lines are DEBUG and were absent):

- Every prompt in the session was preceded by a push-to-talk recording. None was a typed send.
- The preamble turn was itself a recording (`Can you recite the preamble of the US Constitution?`). It finished `status=complete`, `duration=3.0s`, `response_len=327`. No second recording or prompt landed during those 3 seconds.
- First utterance: silence at 09:25:55, prompt accepted at 09:26:02, about 7s, including the `base` model load that started at 09:25:56. Later utterances were about 1.7s from silence detection to prompt accept (09:26:34→09:26:36, 09:27:29→09:27:31, 09:29:03→09:29:05, 09:31:24→09:31:26).

Diagnostic: `logging.level` was unset (default INFO), set to `DEBUG` for this run, then removed. Serve was restarted afterward so the process is back on INFO. No client or hermes-agent source was changed.

Debug session `732e232c`, three turns:

- 09:36:47 typed story. Floor calibrated at 200 (pct90=101, 15 blocks, multiplier 3), so the generation trigger was 600. Speech reached RMS 2567 but the 8-of-10-block window never filled (best 5/8). No trip. The turn ended `interrupted_during_api_call` at 09:37:10 (23.4s) with no barge-in line.
- 09:37:19 push-to-talk, transcript `Actually, just give me one sentence.` The log does not print `peak_rms` on a successful capture (`peak_rms` is a stderr breadcrumb, and only when `HERMES_VOICE_DEBUG=1`). That capture did confirm speech in 0.31s against the silence threshold of 200. The following turn calibrated floor 233, trigger 600, and reached only 4/8 before it finished complete in 3.1s.
- 09:37:48 push-to-talk, then speech over the running turn. Floor 200 (pct90=74), trigger 600. Peaks included 4197, 2873, and 2807, in bursts of a few 30ms blocks. It tripped at 09:38:54 (`TRIPPED (generation)`, window 8/10, rms 991). Whisper kept 1.5s of that clip. The steered text was `Hello?`. The turn was inside `clarify` (115s) and only took the steer at 09:39:55, then ended `interrupted_by_user` with no reply text.

No `playback started`, no `TTS CUT`, no `Full-duplex listener failed`, no `voice interjection interrupt failed`. Calibration always collected the full 15 quiet blocks, so the thinking sound was not in the calibration input. A lower `barge_in_threshold_multiplier` cannot move the generation trigger below 400, and the 240ms sustain window is not a config key. `thinking_sound: false` does not match these lines. No config-only change was applied.

Hermes-side constraint, not a Track 1 defect. The full-duplex listener calibrates a quiet-room floor (measured at 200) and trips only when about 240 ms of audio stays above floor × `voice.barge_in_threshold_multiplier` (200 × 3 = 600) for 8 of the last 10 blocks. That sustain rule is hardcoded in Hermes. At Windows input volume 43 the speech peaks were loud enough in spikes and still missed the sustain window. Raising the Latitude 7430 microphone volume from 43 to 100 and turning audio enhancements off made barge-in trip at a normal speaking volume. The client indicator and submit path were already doing their job.

Retest on the Latitude 7430 after the volume change: barge-in tripped 4 of 4 at a normal speaking volume. Session `1f3afd1f` then shows five essay prompts, each interrupted, plus a second copy of the Super Bowl correction. Each spoken correction was accepted only after the essay turn had already finished `status=interrupted`. There was no `/steer` delivery. `prompt.submit` for those corrections was a normal new turn (`status: streaming`), not `redirected` or `queued`.

The You bubbles are in spoken order. The only assistant text left on screen is the last reply, and it sits under the first You bubble and above every later You bubble. Earlier assistant text was replaced. The transcript does not read as question, answer, question, answer. One correction, "Actually, just tell me who won the last Super Bowl.", is on screen twice.

Diagnostic, no source change. The duplicate is two sequential full-duplex captures. `recording_20260923_095236.wav` (4.4s) and `recording_20260923_095246.wav` (5.6s) were each transcribed and each accepted as `chars=51`, with an `interrupt_abort` before each. Neither wav was preceded by `Voice recording started`, so they are not push-to-talk. The client has one `SubmitTurnAsync` per `TranscriptReady`. The second capture is the listener `_start_turn_voice` armed for the new turn that the first correction started. `voice.transcript` and `voice.interrupted` are not in the INFO log. The client does not persist its status line.

The overwrite is not special to the running-turn path. `FinishTurn` left `_live` set. The next submit, typed or spoken, set `_turnFinalized` false, and `OnMessageStarted` then cleared that bubble. `message.complete` now styles the bubble and sets `_live` null. `message.start` calls `AddLiveBubble` when `_live` is null, and clears the open bubble only when a second `message.start` arrives before `message.complete`. A `redirected` submit still has no `message.start`, so it keeps the open bubble. The developer confirmed the second Super Bowl line was spoken again during the silent web-search turn, so that capture stays. No transcript is dropped.

## Measured speech-to-text delay

First utterance about 7s, including model load. Later utterances about 1.7s from silence detection to the prompt being accepted. Not a pass/fail number.

The developer reported the smoke test passed after the bubble fix. That covers the step 5 re-run and the regression checks: two typed follow-ups stay visible in question, answer, question, answer order; Cancel mid-stream; resume paints history once.

## Closeout

- `dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors.
- Existing tests: N/A. This project has no automated test suite.
- `hermes-agent` `git status` is clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- `python.exe -m pip check`: `No broken requirements found.`
- No lore files were updated (`ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`).
- Feature commit SHA and the merge commit SHA on `main` are recorded in the docs commit after the merge.

## Files

### Created this track

- `windows-client/Zola.Client/VoiceController.cs`
- `zola-architecture/identity/VOICE_CONFIG.md`
- `zola-architecture/lore/prompts/progress/P2-VOICE_Progress.md`

### Modified this track

- `windows-client/Zola.Client/ChatSocket.cs`
- `windows-client/Zola.Client/MainWindow.xaml`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `zola-architecture/lore/prompts/progress/P2-VOICE_Progress.md`
- `zola-architecture/lore/build-plans/PHASE2_BUILD_PLAN.md` (v1.1 commit already on this branch)
