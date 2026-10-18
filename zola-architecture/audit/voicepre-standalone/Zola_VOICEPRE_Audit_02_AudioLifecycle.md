# VOICEPRE Audit 02 — Audio lifecycle, barge-in, and TTS pacing

Static trace of the committed client, the P9 overlay where it differs, and Hermes at `345cd2b`. No process was started. Edge timings are [HISTORY]. The live provider is the Deepgram command path from Audit 01.

## Caller chains checked

| Chain | Location |
|---|---|
| Device open | Hermes `methods_voice.py` module note L1–4; `voice.record` L703–756; `wake_word.py` capture; `voice_mode.py` `full_duplex_listen` L1378–1419 and `AudioRecorder._ensure_stream` |
| Arm / disarm | `_arm_barge_listener_if_enabled` L158–161; `_should_stop` L180–182; `prompt_turn.py` arms from the turn start (prior audits cite L183–191; the gate itself is the method above) |
| Trip | `_fd_trip` L219–246; `_deliver_fd_transcript` L249–259 |
| Record | `start_continuous` / `stop_continuous` `hermes_cli/voice.py` L331–457; silence path L466–515 |
| Admission | `TranscriptAdmission.Decide` `TranscriptAdmission.cs` L57–118; `VoiceController.OnVoiceTranscript` L2297–2388 |
| Playback observe | `TtsPlaybackMonitor.ApplySegmentSample` L438–495 |
| TTS | `SentenceChunker` `tts_streaming.py` L67–96; `resolve_streaming_provider` L147–159; `_text_to_speech_single` `tts_tool.py` L317–330; `_generate_command_tts` `tts_command_provider.py` L309–342; `_SyncSentencePipeline` `tts_tool_speaker.py` L75–126; `_system_player_candidates` `voice_mode.py` L1053–1063 |

`CaptureLifecycle.cs` and `TranscriptAdmission.cs` match across scopes. Overlay `VoiceController.cs` adds the proactive echo refuse inside `StartCaptureAsync` (about L2002–2007) and `RememberProactivePhrase`. It does not change `OnVoiceTranscript` admission order.

## 1. Who opens each device

[CODE] `methods_voice.py` L1–4: one mic and one speaker per Hermes process. The Windows client does not open a capture or render stream (`P2-D01`). `TtsPlaybackMonitor` (`TtsPlaybackMonitor.cs` L8, L254–312) only watches audio-session state of ffplay processes whose parent walk reaches the serve pid (hops ≤ 2, L418–431). It reads no samples (`P3-D23`).

| Device | Opener | Thread | When | Multiplicity |
|---|---|---|---|---|
| Wake mic | `WakeWordDetector` `sd.InputStream` | daemon `wake-word` | `wake.start` while Voice mode is resting | One owner. A second start returns in-use. Paused for `voice.record`. |
| Utterance mic | `AudioRecorder._ensure_stream` | PortAudio callback | `voice.record start` → `start_continuous` | One `_continuous_recorder`. Stream kept between captures. |
| Barge mic | `full_duplex_listen` `sd.InputStream` | daemon `voice-full-duplex` | Only if `voice.barge_in` is not false | Process-global. Arm is idempotent. |
| Speaker | `play_audio_file` → `ffplay` on Windows (`_system_player_candidates` L1056–1060) | `tts-sync-play` | Each synthesized file | One `_active_playback`. `stop_playback` kills it. |

Wake's own comment says two input streams on one device are unreliable. With barge-in off, the Zola path pauses wake before record and does not arm the full-duplex stream, so one capture stream is the designed state. The full-duplex listener does **not** pause wake. Turning barge-in on would add a second mic stream beside wake.

`voice.client_direct` (`config_defaults.py` near L1146; `voice_client_config.py` L10–39) is the HTTP `/api/audio` desktop relay. `P2-D01` forbids that route. It is not a Zola capture seam.

**VOICEPRE-AUD-01** [MATCH] — `P2-D01` / `C3`. Hermes owns the devices. The client drives `voice.*` / `wake.*` and only observes ffplay presence.

## 2. What arms full-duplex detection

[CODE] `_arm_barge_listener_if_enabled` (`methods_voice.py` L158–161) arms only when voice mode is on and `voice.barge_in` is not false. The lookup default is `True` (`dict.get("barge_in", True)`). Code defaults (`config_defaults.py` L1152 area): `barge_in` true, `barge_in_grace_seconds` 0.5, `barge_in_threshold_multiplier` 3.0.

The profile documents `false` (`P4-D28`, `VOICE_CONFIG.md`). While that remains the effective value, this arm does not run.

**VOICEPRE-AUD-02** [MATCH] — `P4-D28`. The listener is config-gated. False means it is not armed. This matches the decision.

**VOICEPRE-AUD-05** [GAP] HIGH — SYM-03, `S36`, `P4-D28`, `P5-D08`. Talk-over is deliberately absent. The feasibility gate on this pin was NO, and it still holds for a flag flip. Restoring it is an open request, not a bug against the locked flag. The flag stays false until an amendment names a listener that can tell a reply from a clarification.

When armed, `full_duplex_listen` (`voice_mode.py` L1378–1393) uses:

| Knob | Value in code | Meaning |
|---|---|---|
| Block | 30 ms | `SAMPLE_RATE * 0.03` |
| `sustained_ms` | 300 | Trip needs 80% of that window (`trip_needed`, L1308) |
| `calibration_ms` | 450 | Quiet-room floor before playback |
| `grace_ms` | 500 from `barge_in_grace_seconds` 0.5 | Suppresses the start of playback after a gap of more than about 1 s (`_track_playback` L1333–1338, 33 blocks) |
| `pre_roll_ms` | 1200 | Deque kept only on this listener |
| `endpoint_silence_ms` | 1250 | After the trip, quiet ends the clip |
| `max_utterance_ms` | 30000 | Cap |
| `PLAYBACK_MIN_TRIGGER` | 1500 RMS | Floor while `is_audio_output_active` |
| `TRIGGER_CEILING` | 4000 | Noisy rooms cannot raise the trigger past this |
| `DEFAULT_BARGE_MULTIPLIER` | 3.0 | Quiet floor times multiplier; playback uses at least 1500 |
| `SILENCE_RMS_THRESHOLD` | 200 | Also the record silence default |

Playback versus generation: `is_playing` is the speaker ref-count, not an estimate. During generation the trigger is the quiet floor times the multiplier. During playback the floor is held and the trigger is clamped up to 1500 so bleed alone should not trip (`L1270–1277`, `feed` L1350–1353). The listener stays armed until voice mode is off or nothing is running, no TTS pipeline is pending, and no speaker output is active (`_should_stop` L180–182). Pending TTS covers the gap between sentence files.

There is no clarify check on the arm.

## 3. What `_fd_trip` does

[CODE] `methods_voice.py` L219–246.

| Effect | Detail |
|---|---|
| Latch | `mark_speech_interrupted()` (TTL 120 s in `tts_streaming.py`) |
| Stop streaming TTS | `_tts_stream_stop(user_barge=True)` |
| Stop fallback speaks | Sets every `_fd_speak_pipelines` stop event |
| Stop the player | `stop_playback()` |
| Interrupt sessions | `agent.interrupt()` on **every** running session, only when `phase != "playback"` |
| Emit | `voice.interrupted` with no payload |
| Clarify | **Not inspected.** No request id, no question state. |

After the trip the same thread keeps the pre-roll and records until endpoint silence, then `transcribe_recording` and `_deliver_fd_transcript` (`L192–197`, L249–259). The transcript payload is `{"text": ...}` or a stop-phrase variant. No capture id.

Client `OnVoiceInterrupted` (`VoiceController.cs` L2575–2590) invalidates the current capture and then stops it (`P7-D02`). At three consecutive interrupts it enters Text mode (`P2-D13`). The comment at L2589 still says the interjection is submitted by the existing path. The code under it does not open a capture. `OnVoiceTranscript` admits only an Accepting owned capture (`TranscriptAdmission.cs` L78–107). A full-duplex transcript has no client owner, so it is dropped `no_owner`. If a turn is still running and the capture is not a bound clarify, it is dropped `turn_running_unbound` (`P7-D04`).

**VOICEPRE-AUD-06** [RISK] HIGH — SYM-03 against `P7-D01`, `P7-D04`, `P4-D28`, `S36`. Re-enabling `barge_in` restores a trip that cuts audio, latches an interruption, and does not look at an open clarification. The words that caused the trip are not admitted by current P7 logic. Talk-over and "keep the interrupting sentence as the next turn" are separate, and the second one fails closed today.

## 4. `voice.record` start and stop

[CODE] `methods_voice.py` L703–756 and `hermes_cli/voice.py` L331–457.

| Question | Answer |
|---|---|
| Actions | `start` and `stop` only. Anything else is error 4019. |
| Cancel RPC | **Not present.** `S53` stands. |
| Start | Beep 880 Hz **before** `rec.start` (`voice.py` L374–378). Then status `listening`. Returns `recording`, or `busy` if a stop/transcribe is in progress. `auto_restart=False`. |
| Stop | Always `stop_continuous(force_transcribe=True)`, then `_resume_voice_wake()` immediately (`methods_voice.py` L721–725). |
| Discard | `voice.toggle off` calls `stop_continuous()` with the default `force_transcribe=False`, which `cancel()`s the buffer (`voice.py` L424–426). That is not the record-stop path. |
| Silence order | `transcribing` → stop WAV → double beep → transcript callback → deactivate → `idle` (`L485–534`). |
| Forced-stop order | `transcribing` → sync `rec.stop` → background transcript → double beep → `idle` (`L411–422`, L430–457). |
| Late transcript | Payload is text only (`VoiceTranscriptPayload` has `text`, `stop_phrase`, `typed`, `no_speech_limit`). No capture id. The client binds by "the one Accepting generation", which is why cancel must happen before stop (`P7-D02`). |
| Pre-roll | **None** on this path. Frames accumulate only while `_recording` is true. The 1200 ms deque belongs to `full_duplex_listen` and the unused `listen_for_speech`. |

**VOICEPRE-AUD-07** [GAP] HIGH — SYM-02, `S36` (e), `P4-D18` residual. Speech that starts before the beep, or in the quiet window before `voice.record`, is not in the WAV. This is the historical pre-beep clip. It is a candidate for SYM-02. It is not proof that every current clip is that bug. Other candidates (endpoint cut, device handoff, a follow-up that opens late) are not separated by static reading.

**VOICEPRE-AUD-08** [GAP] MEDIUM — `S53`, `S52`. No correlation id. Stop always transcribes and then resumes wake even if silence-path STT is still inside `rec.stop` (the P7 forensic race). A true cancel that drops audio and waits for idle does not exist on this pin.

## 5. From capture to admit, clarify, or busy turn

[CODE] `OnVoiceTranscript` (`VoiceController.cs` L2297–2348) snapshots the lifecycle, then `TranscriptAdmission.Decide`.

Order (`TranscriptAdmission.cs` L68–117): gated → text mode → no outstanding capture → cancelled → settled → not Accepting → clarify id not open → turn running on a non-clarify capture → echo flag → admit.

| Arrival | Result under current rules |
|---|---|
| Follow-up or clarify, Accepting, turn idle or clarify-bound | Admit. Clarify answers the bound request (`P7-D05`). Others `prompt.submit`. |
| Unbound transcript while `TurnRunning` | Drop `turn_running_unbound`. Typed submit is a different path and still works (`P7-D04`). |
| Full-duplex barge transcript | No Accepting owner. Drop `no_owner`. |
| Transcript after `InvalidateCapture` | Drop `cancelled`, including the forced transcript from the stop (`P7-D02`). |
| Echo flag true | Drop `echo`. The matcher cannot admit (`P7-D07`). |

Echo is computed only when `_followUpCaptureStarted` or `_followUpEchoPending` (`VoiceController.cs` L2311–2312). Those flags are set for follow-up, echo-reopen, and clarify (`L1051–1053`, `L2164–2166`, `L2831–2833`). Wake and manual captures do not set them, so `IsEchoOfLastReply` does not run. `P2-D14` already scoped the matcher to follow-up captures. Wake-during-playback was observed not to fire in the P9-SUPERVISE N2a note [HISTORY]; it is not the main candidate.

`IsEchoOfLastReply` (`L3426–3454`): under 3 words never drops; the run must be ≥0.60 of the transcript and end near the last 20 haystack words. A short echo, or her earlier sentence rather than the tail, is admitted if a follow-up is Accepting.

A restored barge transcript would **not** be admitted unless a new capture kind is Accepting at that moment and `TurnRunning` is false (or it is the bound clarify). Opening that capture during the turn would violate `P7-D04` as written. So a barge-in restoration has to amend the admission rule, not only the Hermes flag.

## 6. What proves playback is finished

| Signal | Proves | Does not prove |
|---|---|---|
| `TtsPlaybackMonitor.IsBoutActive` | An owned ffplay session was present, then absent for `ReleaseDebounceMs` 450 (`PresenceLife.cs` L92; `ApplySegmentSample` L485–494) | That the last sample was heard, or that the next sentence will not start |
| Segment stop | One ffplay entered Inactive or exited | End of the reply |
| Bridged gap log | A new owned ffplay appeared while the bout was still inside the debounce | A measured acoustic gap |
| `voice.status idle` | The **recorder** finished | Playback |
| `is_audio_output_active` | Hermes's own player ref-count | Not exposed as a client event |
| `P2-D15` estimate | A clock (`FirstSentenceLatencySeconds` 3.3, 2.5 words/s, 0.5 s per sentence, margin 5.0) | Audible end. Fallback only (`P7-D06`) |

**VOICEPRE-AUD-04** [MATCH] — `P7-D06` / `P4-D18`. An estimate release does not open a capture while the monitor reports a bout. Monitor-unavailable falls back to the estimate. The constants are still in `VoiceController.cs` L46–58. Follow-up quiet after a real bout stop is 0.5 s (`FollowUpPostBoutQuietSeconds`).

**VOICEPRE-AUD-11** [GAP] MEDIUM — `S70`, `S17`, SYM-05. Hermes emits no playback-completed event. The client infers it from ffplay process presence. `voice.tts` returns when speech is **accepted**, not when it finishes (`methods_voice.py` `voice.tts`). A read-back can be marked reviewed while audio is still going (`S70`).

After an interrupt, leftover speech is stopped inside Hermes by the stop event, `stop_playback`, and skipping queued sentences in `_SyncSentencePipeline._drain` when the stop is set (`tts_tool_speaker.py` L115–122). The client Stop path uses `voice.toggle off` then `on` so the latch is not set (`P4-D29`). That kills the player. It does not cancel the model turn or a tool (`StopSpeakingAsync` around L1165–1232).

If the monitor ends the bout during a synthesis gap longer than 450 ms, the next ffplay is a **new** bout. Follow-up may already be open. That is a self-echo candidate, not a cancellation bug (Audit 03).

## 7. Historical failures, current mitigations, remaining risks

| Historical | Mitigation now in source | Still open |
|---|---|---|
| Clarify answer latched "Interrupted" | `barge_in: false` (`P4-D28`) | Talk-over stays off (SYM-03) |
| Her speech became a user turn (S45) | P7 admission, cancel-before-stop, no unbound mid-turn, monitor hand-back | SYM-01 says it still happens. The matcher and the bout gap can still admit it. Cause of the current cases is UNRESOLVED. |
| Lost first words (AUD-37) | Bout-stop plus 0.5 s quiet instead of a pure estimate | No pre-roll. Beep before record. SYM-02 UNRESOLVED as to which path. |
| Self-interrupt loop with lid closed | Barge-in off, so `P2-D13` does not see trips | Returns if barge-in returns without a better echo path |
| Edge 403 and slow first audio | Live provider switched to Deepgram command (P9-FIX-TTS) | Per-sentence file playback remains. Current gap size UNRESOLVED (SYM-05). |
| Native crash during stop/wake overlap (S51/S52) | Not fixed on this pin | Out of scope to diagnose. Any new capture loop must not resume wake over an in-flight stop. |

Static reading cannot name a native crash cause. None is claimed.

## TTS pacing trace (configured provider)

Against `S34`, `S38`, `S55`, `S70`, SYM-05.

Live `tts.provider=deepgram` is not in `BUILTIN_TTS_PROVIDERS` (`tts_command_provider.py` L269–271) and not in `_PROVIDER_PRIORITY` (`tts_streaming.py` L144: elevenlabs, gemini, openai, xai). `resolve_streaming_provider` returns None for a provider with no chunked PCM class (`L147–159`; tests assert Edge is None). The dispatcher then uses `_SyncSentencePipeline`.

```
model delta
  → tts queue (turn stream)
  → SentenceChunker.feed (min_len 20, boundaries .!? + whitespace or a blank line)
  → sentence held until min_len, or flush at end of stream / idle
  → one synthesis thread calls text_to_speech_tool
  → _generate_command_tts writes the sentence to a temp file, runs the command, waits for an mp3
  → playback thread play_audio_file → ffplay -nodisp -autoexit, one process, to completion
  → next queued sentence (lookahead 2: sentence n+1 may synthesize while n plays)
  → end-of-stream None sentinel → chunker.flush → pipeline close
```

Queue ownership: one synth executor, one play thread, queue bound 2 (`tts_tool_speaker.py` L83–93). Playback does not overlap. Synthesis of the next sentence can overlap playback of the current one. Each sentence starts a new ffplay (`L120–122`, `voice_mode.py` L1066–1076). There is no shared PCM clock and no leftover-audio API beyond `stop_playback`.

Stages that can delay **first** speech, kept separate:

| Stage | What it waits for | Evidence it is the Deepgram path | Measured now |
|---|---|---|---|
| Model / tools | Tokens, and tool rounds before a speakable sentence | Not TTS. S38 / S54 [HISTORY]: tools were the largest Edge-era share. | Not measured on Aura-2 |
| Chunk wait | First boundary with ≥20 characters, or end-of-stream flush | `SentenceChunker` L72–96. P7 baseline: 6/8 Edge replies spoken only on flush [HISTORY]. | Same chunker, new provider |
| Command synthesis | HTTP to Deepgram and the script writing the mp3, for that sentence only | `_generate_command_tts` L309–342. Timeout default 120 s. | Not measured as a stage |
| Queue wait | Previous sentence still in the play queue | Lookahead 2. First sentence has no previous play. | — |
| Player start | `Popen(ffplay)` after the file exists | L1066–1076 | Not measured |
| Hearable onset | Device buffer after ffplay starts | No client sample clock | Not measured |

Stages that can open a **later** gap:

| Stage | Mechanism |
|---|---|
| Inter-sentence player restart | ffplay exits at end of file; next ffplay starts only after the mp3 exists. If synth of n+1 finished during n, the gap is process startup plus device buffer. If synth is slower than playback, the gap includes the rest of the request. |
| Monitor debounce | 450 ms with no owned ffplay ends the bout (`PresenceLife` L92). A longer synth gap is a bout stop, then 0.5 s quiet, then a follow-up capture, while a later sentence may still be coming. |
| Markdown / short sentences | Chunker can emit many short files. More files means more startups. `S34` left this in place. |
| Flush | A one-sentence reply is not spoken until the model finishes (`chunker.flush`). That wait is model time plus one synth, not a split-sentence gap. |

**VOICEPRE-AUD-12** [RISK] MEDIUM — SYM-05, `S34`, `S55`, `S70`. The configured path is sequential file synthesis and a new ffplay per sentence. That structure can delay the first word until the first sentence is fully synthesized, and can open a silent gap between sentences. P7's Edge shares (S-tts ≈ 2.0 s, S-play ≈ 1.5%) do **not** transfer. One Deepgram sample on 2026-10-12, `submit_to_first_audio_ms=4628` (`P9-SUPERVISE`), is a single turn and mixes model time with synth and player start. Current frequency and size of the gaps are UNRESOLVED.

Do not attribute the wait to Deepgram alone or to the chunker alone. The missing events are: first speakable sentence ready, command start, command end, ffplay process start, first audible sample, ffplay exit, next ffplay start. The monitor has bout and segment edges only.

**VOICEPRE-AUD-14** [RISK] LOW — `P2-D09`, `P2-D03`, `P4-D19`. `VOICE_CONFIG.md` still tells a restorer to set `tts.provider: edge` and Sonia. The live file, keys read 2026-10-18, selects `deepgram` / `aura-2-pandora-en` / speed `0.95`. `P9-FIX-TTS` recorded the switch and did not update that canonical block (`P9-SPEAK` discrepancy). Applying the canonical block would put Edge back. Edge timings must not be quoted as the current voice.

## Completeness

The required chains (device, arm, trip, record, admission, cancellation, TTS) are cited above with line ranges. Plugin code cannot replace `_fd_trip` or add pre-roll; the only barge switches are `voice.barge_in` and the two numeric keys (`methods_voice.py` L160, L208–216). That is the same seam P5PRE called missing, re-read on this pin.
