# P2-SPEAK Progress — Track 2: Spoken Replies and Follow-up

## Branch

- Branch: `track2-spoken-replies`
- Base SHA: `1331e8da48f5592706e2f48e65246277981e69aa` (`docs: record P2-VOICE merge SHA on main`)
- Plan: `PHASE2_BUILD_PLAN.md` v1.1

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read, Understand, and Probe | COMPLETE |
| 3 | Build: Spoken Replies On, and Barge-in While Speaking | COMPLETE |
| 4 | Build: Simulated Playback Clock, Speaking Gate, and Follow-up Window | COMPLETE |
| 5 | Smoke Test and Tuning | COMPLETE |
| 6 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Turn on Hermes spoken replies in Voice mode without blind-flipping `voice.toggle action=tts`; handle barge-in while Zola speaks; add the simulated-playback follow-up window and gate the mic while she is estimated to be speaking. No wake word, no client audio, no `/api/audio/*`, no `hermes-agent` edits. Profile keys stay unchanged unless a smoke-test tuning step explicitly allows one.
- **G-ARCH:** Build plan is truth. Stop and flag conflicts; do not silently deviate.
- **G-PATTERN:** Read every relevant file in full before any change. No changes from partial reads or memory.
- **G-NOCHANGE:** Edits limited to the files named in the current phase. Track 1 behavior, the event-driven assistant bubble lifecycle, typed chat, Cancel, and Sessions stay as merged on `main`.
- **G-COMMENT:** Every changed line or block carries `// P2-SPEAK: [rationale] — P2-D0X` (XAML comment form in markup). Do not comment unchanged lines.
- **G-STOP:** Stop after each phase and wait for that phase's explicit proceed message.
- **G-CLOSEOUT:** Closeout begins only on the explicit message "proceed to closeout".
- **G-LORE-SCOPE:** Do not add, resolve, or update `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, or any project state-audit document in this track, including closeout.
- **G-NO-CROSS-SCOPE:** Android Zola and Ava voice stacks are out of scope. Do not read, cite, or build against them.
- **G-DEPS:** Never run `pip`, `uv`, or any installer without the developer's explicit approval of the exact command. `security.allow_lazy_installs: false` is set, so Hermes requirement checks are safe. A missing package is reported, never worked around.
- **G-CONST:** Every JSON-RPC method, action, payload field, state, timing, and threshold this track adds is a named constant.
- **G-ONE-OWNER:** Speaking-state estimation, follow-up timing, capture gating, and interruption handling live in `VoiceController.cs`. `MainWindow.xaml.cs` only forwards turn events and renders what the controller reports.

## Discrepancies

None at start. Documents of truth read before Phase 1: `PHASE2_BUILD_PLAN.md` v1.1 (Grounding summary, `P2-D03`, `P2-D06`, `P2-D07`, `P2-D08`, `P2-D12`, Track 2), `P2-VOICE_Progress.md` (barge-in floor 200 / trigger 600 / ~240 ms sustain, running-turn `prompt.submit`, Phase 1 bubble-defect fix), `VOICE_CONFIG.md` (live keys and Latitude 7430 mic setup), `Zola Master Architecture Plan.md` (§3 Current Sequential Model, §11, Speech Authority Constraint), WINH09 Audit 03 (`AUD-06`, `AUD-08`) and Audit 05 (`AUD-16`; that finding is not in Audit 03), `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`. HEAD on `main` matched `1331e8da48f5592706e2f48e65246277981e69aa` and the working tree was clean.

Developer-approved Phase 4 addition: a runaway-loop guard in `VoiceController`. If 3 consecutive spoken turns end interrupted by a `voice.interrupted` trip with no normally-completed turn in between, call `EnterTextModeAsync()` and show "Voice paused: Zola may be hearing herself — check that the lid is open and review mic/speaker setup." Reset the counter on any completed turn, typed submit, or mode change. Threshold is a named constant. Tag `// P2-SPEAK: … — P2-D12`. Phase 5 smoke includes closing the lid and confirming the guard stops the loop within 3 turns.

Developer-approved echo guard: for a follow-up capture only, if the transcript's normalized words (lowercase, no punctuation) look like Zola's previous tail, drop it, write it to the timeline log, and show "Ignored: that sounded like Zola's own voice." Smoke retune: containment 0.60 of the last 20 spoken words when the transcript has at least 3 words, or any 4-word phrase from the transcript in that tail. The original 80% / last-20 bag-of-words missed Whisper splitting `unless` into `and less` (6/8 = 75%). After an ignored tail, reopen the follow-up capture so the spent echo does not consume the listen window; cap at 3 reopens. Thresholds are named constants. Tag `// P2-SPEAK: … — P2-D12`.

Smoke-test finding (no timing change from the 12:35:47 note): on long replies the follow-up capture starts before playback ends, captures Zola's last words, and the new turn clips her tail. That is the `P2-D06` underestimate. Clock now adds `newSentences × PerSentenceOverheadSeconds` beside `newWords / EstimatedWordsPerSecond`. A first fit of `PerSentenceOverheadSeconds = 3.0` made long-reply predicted gaps about +23 s, and the barge-in listener is already closed in that gap. The six runs fit a fixed startup cost plus a small per-sentence cost instead: `FirstSentenceLatencySeconds = 3.3`, `PerSentenceOverheadSeconds = 0.5`, `FollowUpMarginSeconds = 2.0`, `EstimatedWordsPerSecond = 2.5`.

Known semantic limitation, confirmed in source, not a Track 2 code change. Two actions latch `SPEECH_INTERRUPTED_NOTE` the same way. A typed Send during playback starts a new turn, and `_tts_stream_begin` calls `_tts_stream_stop()` with the default `user_barge=True` before the new speech starts (`methods_voice.py` 106, 117–130; `prompt_turn.py` 183–187). Cancel during speech calls `session.interrupt`, whose first line is that same `_tts_stream_stop()` default (`methods_session.py` 1997). `_prepare_turn_input` then takes the latch and prepends the note to the next turn (`prompt_turn.py` 509–511). Hermes cannot tell "the user typed a new message" or "the user pressed Cancel" from "the user spoke over me", so the next reply may act as if Zola was talked over. `voice.toggle off` passes `user_barge=False` and does not latch. This will be filed at the lore closeout. No client handling is added.

## Phase 2 probe results

Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`. `HERMES_HOME` was the Zola profile. Working directory was `hermes-agent`.

| Probe | Result |
|---|---|
| `import edge_tts` | success, `edge_tts` 7.2.7 |
| `check_tts_requirements()` | `True` |
| configured TTS provider | `edge` |
| `resolve_streaming_provider` | `None` (Edge has no chunked streamer; playback is `_SyncSentencePipeline`) |
| default output device | `Speakers (Realtek(R) Audio)` |

`hermes-agent` `git status` after the probes: clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

## Phase 2 understanding

`voice.toggle` replies include `tts` from `_voice_status_payload` (`methods_voice.py` 301–306): `"tts": _voice_tts_enabled()`, which is true only when `HERMES_VOICE_TTS` is `"1"`. `action=status` reports it and changes nothing. `action=on` sets `HERMES_VOICE=1` and does not change `tts`. `action=off` sets `HERMES_VOICE=0`, stops a continuous capture, and calls `_set_voice_tts(False)`, which sets `tts` false and cuts live speech with `user_barge=False`. `action=tts` flips the flag, and only when voice mode is already on (otherwise error 4014). The client `RpcReply` does not read `tts` yet, and `SyncVoiceModeAsync` never sends `action=tts`.

For Edge, one spoken turn:

1. `message.start` is emitted before the turn thread prepares voice (`prompt_turn.py` 820).
2. `_start_turn_voice` starts `stream_tts_to_speaker` and arms the full-duplex listener (`prompt_turn.py` 183–191).
3. Each `message.delta` is queued to that speaker and then emitted (`prompt_turn.py` 529–531). The first delta does not start audio. `SentenceChunker` waits for a sentence boundary (`tts_streaming.py` 72–91, minimum 20 characters).
4. `_SyncSentencePipeline` synthesizes sentence n+1 while sentence n plays (`tts_tool_speaker.py` 75–80, 115–122). Sentences are back to back except for the synthesis of the first one and any later sentence that is not ready when the previous file ends.
5. `message.complete` is emitted before the end-of-text sentinel (`prompt_turn.py` 848, then `_finish_turn` at 858 puts `None` at 740–741). Playback of the queued tail continues inside `sync_pipeline.close()`, and `tts_done` is set only after that join (`tts_tool_speaker.py` 348–353). `message.complete` can arrive while speech is still playing.

Barge-in during playback. The listener stays armed while a session is running, TTS is pending (`_fd_tts_pending`), or `is_audio_output_active()` is true (`methods_voice.py` 180–182). For Edge, `play_audio_file` holds that flag for each sentence (`voice_mode.py` 984–988), and `_fd_tts_pending` covers the gaps between sentences until `close()` returns. It disarms on the next loop check after all three are false, then the input stream closes. That is about one 30 ms block after the last sentence, not a long tail. During playback the trigger is `max(quiet_floor × multiplier, PLAYBACK_MIN_TRIGGER)` with `PLAYBACK_MIN_TRIGGER = 1500` (`voice_mode.py` 1351–1352, 1276). Floor 200 × 3 is 600, so playback uses 1500. A grace of `barge_in_grace_seconds` (default 0.5 s, 500 ms) suppresses the trip only when playback starts after a gap of more than about 1 s (`voice_mode.py` 1333–1364). The ~240 ms sustain rule is unchanged (8 of the last 10 blocks of 30 ms).

`voice.record start` does not look at the full-duplex listener. `start_continuous` opens its own input stream (`hermes_cli/voice.py` 351–378). If that stream opens, there are two captures, and the reply is `{status: "recording"}`, not busy. Busy is only a continuous loop that is already stopping. The Speaking gate must stay closed until the follow-up timer, and the timer must not fire while TTS is still pending. `FollowUpMarginSeconds` is that margin. The listener does not linger after playback, so no second wait is required beyond the estimate plus that margin. A short estimate is what would open `voice.record` while the listener and the speakers are still active.

A typed Send during playback starts a new turn, which cuts the previous pipeline and latches the interruption note, as recorded above. Cancel calls `session.interrupt`, whose first line is `_tts_stream_stop()` (`methods_session.py` 1997), so speech stops. No client workaround is added.

`voice.toggle action=off` stops a live capture and cuts in-flight speech without the interruption latch. `EnterTextModeAsync` already sends that action. No second `tts` call is added.

## Phase 3

`RpcReply.Tts` is read from `voice.toggle` replies. `SyncVoiceModeAsync` sends `action=tts` only when the status just read has `tts == false`. If voice mode was off, it sends `on`, reads `status` again, and only then may send `tts`. A flip that does not come back `tts: true` is shown as "Spoken replies did not turn on." and logged. Nothing further is sent. `voice.interrupted` clears `Speaking` and shows "Voice interrupted." The follow-up timer is not built yet. Cancel and a typed Send still latch the interruption note, as recorded above.

`dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors.

Before the listen re-run, source confirmed both playback facts. `play_audio_file` brackets `mark_audio_output_active(True)` / `False` around the ffplay call (`voice_mode.py` 984–988), and the listener uses `is_audio_output_active` as its playback phase (`methods_voice.py` 189, `voice_mode.py` 1351–1352). `stop_playback` terminates the ffplay process stored by `_run_system_player` (`voice_mode.py` 949–957, 1073–1075). Barge-in, a typed Send, Cancel, and Text mode all reach that function (`methods_voice.py` 232–236 and 117–134, `methods_session.py` 1997, `methods_voice.py` 656).

`ffplay` was missing. Developer approved `winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements`. It installed ffmpeg 9.0.2. A fresh shell loaded User and Machine PATH. `ffplay` resolved to `%LOCALAPPDATA%\Microsoft\WinGet\Links\ffplay.exe`, linking to the package `bin\ffplay.exe`. Recorded in `VOICE_CONFIG.md`. Requires restart of client/serve after install.

The old Zola client and Zola `hermes serve` processes were stopped. The client was launched from that fresh shell and spawned a new serve. Voice mode reached `Session ready.` A typed "Say hello in one sentence" finished, Edge saved a 12,528-byte mp3, and an `ffplay` process started. About one second later the log recorded `Audio playback interrupted`, then `WARNING tools.voice_mode: No audio player available`, then a listener WAV. A second run, with the client left open until after that window, did the same: `ffplay` pid 22260, interrupt at 1.1s, the same warning, then a WAV. That warning is the fallthrough after `stop_playback` terminates ffplay (`voice_mode.py` 1078–1104), not the missing-player failure. The earlier missing-player line had no `ffplay` process and no interrupt line. Text mode from the first local check still stands: `tts: false` and no `Generating speech` line. The test client and the spawned serve were closed afterward. `hermes-agent` was not modified.

Phase 3 is blocked on self-interruption. Both hello runs cut playback about 1.1 s after it started with nobody speaking. `logging.level: DEBUG` is set only while a bleed run is in progress.

The laptop lid was closed for (a), (b), and (e). That is what caused those self-trips: the built-in array mic is in the lid bezel, so a closed lid puts it against the chassis near the speakers.

| Config | Lid | Mic | Enhancements | Speaker | Floor | Trigger | Peak bleed RMS | Self-trip | Self-transcribed turns |
|---|---|---|---|---|---|---|---|---|---|
| (a) | closed (cause) | 100 | off | 35 | 200 | 1500 | 9635 | 0.93 s | 0 |
| (b) | closed (cause) | 100 | on | 35 | 200 | 1500 | 3952 | 1.35 s | 0 |
| (c), (d) | skipped | | | | | | | | |
| (e) | closed (cause) | 100 | on | 20 | 419 | 1500 | 3573 | 7.23 s | 0 |
| (f) | open | 100 | on | 15 | 284 | 1500 | 1289 | none (15 s clean) | 0 |

Configurations (c) and (d) are skipped: lowering the mic input scales the voice and the speaker bleed together. No closed-lid built-in-mic setting gave zero self-trips.

Configuration (f), lid open, input 100, enhancements on, speaker volume 15. Playback-phase floor 284, trigger 1500. Peak bleed RMS 1289. No self-trip in 15 s of playback. Self-transcribed turns before Text mode: 0.

Required-setup generation-phase interruption check at normal volume (enhancements on): 3 of 3 generation trips (rms 5077, 1224, 2844). Speech peak RMS 5077. Phase 3 is unblocked. `logging.level` was removed after the run.

## Phase 4

The simulated playback clock, speaking gate, follow-up timer, timeline log, and runaway-loop guard live in `VoiceController.cs`. `MainWindow.xaml.cs` forwards `OnTurnStarted`, `OnTurnDelta`, `OnTurnCompleted`, and `OnTypedSubmit` only. Word count is cumulative over the accumulated reply after fences and marks are stripped. `followUpGeneration` is checked when the timer fires and again immediately before each `voice.record start`, including after `await`.

`dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors.

Local check: typed "Tell me four short sentences about the moon." Voice state showed Speaking, then a follow-up capture with Mic: recording. Timeline: start 12:35:33, complete 12:35:35, estimatedEnd 12:35:46, delay 11.708s, fire 12:35:47, words 29, followUpStarted True. About 7 s later a `voice.transcript` arrived and started a second spoken turn. Developer confirms that transcript was his own speech, not self-transcription. No timing change. The client was closed afterward. `hermes-agent` was not modified.

## Phase 5

Client rebuilt with 0 warnings and launched (pid 9308). Window showed Voice, Idle, Mic: off, and "Session ready."

Smoke test failed: self-transcribed bubbles on a long reply. Other spoken steps passed. The follow-up still opened near the tail; Whisper submitted `and less you explicitly share or connect them.` as the next user turn (session `0dffbb1a`, 14:35:33, 4.0 s recording). That is Zola's closing clause with `unless` heard as `and less`. Six of eight normalized words sat in the last-20 tail (75%), below the original 80% echo threshold, so the guard did not drop it. The new turn clipped her remaining speech.

One earlier tail on the same session was dropped correctly at 14:34:15 (`echo-ignored words=hillier wetter and its network has historically been more fragmented though it s been expanding fast`).

Clock for that 81-word / 7-sentence reply: start 14:34:46.3, complete 14:34:51.0, estimatedEnd 14:35:26.0, follow-up fire 14:35:28.0, record start 14:35:28.2, silence 14:35:32.3. Speech was still in the 4.0 s capture, so the estimate plus 2.0 s margin was a few seconds early. `FollowUpMarginSeconds` is now 3.0. Echo guard retune: containment 0.60, ignore bag-of-words below 3 words, and drop if any 4-word phrase from the transcript sits in the last 20 spoken words. That 8-word tail is 75% contained and contains `you explicitly share or`.

Re-run found the echo drop working, but the spent echo capture ended the follow-up window and returned to Idle, so the developer had to press Mic. After an ignored tail the client now reopens follow-up listen (0.5 s delay, at most 3 reopens) instead of cancelling the window. Developer confirms that reopen is better.

Developer reported **smoke test passed** after that reopen. Required setup remains (f). Final clock: `EstimatedWordsPerSecond = 2.5`, `FirstSentenceLatencySeconds = 3.3`, `PerSentenceOverheadSeconds = 0.5`, `FollowUpMarginSeconds = 3.0`. Echo guard plus reopen is how a long-reply tail is kept from becoming a user turn without eating the next listen. Closeout waits on "proceed to closeout".

## Follow-up measurement table

An early follow-up start is worse than a late one: `voice.record` while the barge-in listener is still armed opens a second capture. Developer reported smoke passed after the echo guard and reopen. Long replies can still fire on the tail; that capture is ignored and listen is reopened, so it does not become a user bubble and does not require the Mic button.

| Reply | Gap category | Self-transcription | User bubbles from that utterance | Follow-up answered | Timeline log |
|---|---|---|---|---|---|
| Short | developer pass | no (final) | 1 | yes | smoke pass |
| Medium | developer pass | no (final) | 1 | yes | smoke pass |
| Long | early tail possible; echo + reopen | no (final; first run submitted the tail) | 1 (final) | yes | 14:34:15 echo-ignored; 14:35:33 miss; reopen confirmed better |
| Tool-using | developer pass | no (final) | 1 | yes | smoke pass |
| Five-reply run | developer pass | no (final) | 1 each | yes | smoke pass |

## Barge-in success count

Developer reported the spoken-reply and interruption steps passed. Generation-phase check under (f) was 3 of 3 before Phase 4. Playback-phase barge-in uses trigger 1500; lid-open (f) is required.

## Final tuned constants

`EstimatedWordsPerSecond = 2.5`, `FirstSentenceLatencySeconds = 3.3`, `PerSentenceOverheadSeconds = 0.5`, `FollowUpMarginSeconds = 3.0`, `FollowUpMaxDelaySeconds = 90`. Echo: `EchoContainmentRatio = 0.60`, `EchoLookbackWords = 20`, `EchoMinWords = 3`, `EchoPhraseWords = 4`, `EchoReopenLimit = 3`, `EchoReopenDelaySeconds = 0.5`.

Old values from the first six-run fit: `EstimatedWordsPerSecond = 2.5`, `FirstSentenceLatencySeconds = 1.0`, `PerSentenceOverheadSeconds = 3.0`, `FollowUpMarginSeconds = 1.0`. That fit kept every estimate from going early by charging 3.0 s per sentence, but it predicted +23 s gaps on the long replies. The barge-in listener is already closed during that gap, so speech in it is lost. The six runs instead look like a fixed first-sentence startup plus a small per-sentence cost. New predicted gap is `old estimate + (3.3 − 1.0) + sentences × 0.5 + 2.0 − actual ffplay-gone time`.

| Run | Words | Sentences | estimatedSpeechEnd (old clock) | Actual playback end (ffplay gone / last playback VAD) | Old error (estimate − actual) | Old predicted (2.5 wps + 3.0 s/sentence) | New predicted gap (estimate + margin − actual) |
|---|---|---|---|---|---|---|---|
| S1 (contaminated; leftover Constitution turn, not Japan) | 56 | 2 | 14:20:18.896 | 14:20:22 / 14:20:21.058 | −3.1 s | +2.9 s | +2.2 s |
| S2 short | 1 | 1 | 14:20:31.232 | 14:20:34 / 14:20:32.598 | −2.8 s | +0.2 s | +2.0 s |
| M1 medium | 41 | 4 | 14:20:59.725 | 14:21:03 / 14:21:02.157 | −3.3 s | +8.7 s | +3.0 s |
| M2 medium | 37 | 4 | 14:21:26.218 | 14:21:32 / 14:21:30.847 | −5.8 s | +6.2 s | +0.5 s |
| L1 long | 145 | 10 | 14:22:38.175 | 14:22:45 / 14:22:43.087 | −6.8 s | +23.2 s | +2.5 s |
| L2 long | 121 | 10 | 14:23:44.874 | 14:23:52 / 14:23:50.847 | −7.1 s | +22.9 s | +2.2 s |

Sentence count is unique Edge sentence files. All six new predicted gaps are ≥ 0 and ≤ ~3 s. After smoke, `FollowUpMarginSeconds` is 3.0. Long replies can still open on the tail; echo-ignore plus reopen keeps that from becoming a user turn.

## Closeout

- `dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors.
- Existing tests: N/A. This project has no automated test suite.
- `hermes-agent` `git status` is clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- No lore files were updated (`ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`).
- Feature commit SHA: (recorded after merge)
- Merge commit SHA on `main`: (recorded after merge)

## Files

### Created this track

- `zola-architecture/lore/prompts/progress/P2-SPEAK_Progress.md`

### Modified this track

- `windows-client/Zola.Client/VoiceController.cs`
- `windows-client/Zola.Client/ChatSocket.cs`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `zola-architecture/identity/VOICE_CONFIG.md`
