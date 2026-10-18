# VOICEPRE Audit 03 — Echo control and continuous-audio feasibility

Against `S36` first-word retention and P7 echo/admission. No capture was opened. No enhancement setting was read.

## 1. What "echo protection" actually is

It is not acoustic cancellation.

| Mechanism | Stage | What it can do | What it cannot do |
|---|---|---|---|
| `IsEchoOfLastReply` | After STT, before admit | Drop a follow-up or clarify transcript that is a ≥3-word, ≥0.60, end-anchored run of the last 20 spoken words (`VoiceController.cs` L3426–3454). Runs only if follow-up/clarify flags are set (L2311–2312). | Stop the microphone from hearing her. Drop 1–2 word echoes. Drop a quote of an earlier sentence. |
| `SpeechEchoGuard` | Before capture, and as an exact substring | Overlay only. Refuses a non-PTT capture while the proactive phrase is queued, playing, or inside 2 s after completion (`SpeechEchoGuard.cs` L64–88, `EchoTailSeconds` = 2). Drops a transcript that contains that exact phrase (L54–61). | Cover ordinary replies. Survive a paraphrase. Exist on committed `main`. |
| Playback mute of the mic | — | **Not found** on the Zola record path. | — |
| Amplitude gate | Hermes barge detector only | RMS trigger while barge-in is on (`voice_mode.py` L1350–1353). Off today. | Distinguish her voice from Brian when both are loud. |
| Windows endpoint AEC | OS capture APO, if the app opens the mic in a mode that enables it | Hermes uses `sounddevice` `InputStream` with no AEC reference call in the record or barge paths searched. Whether the default Windows enhancement is in that stream is UNKNOWN. | Be assumed from "enhancements on" in a 2026-09 note. |

**VOICEPRE-AUD-09** [RISK] HIGH — SYM-01, `P2-D14`, `P7-D07`, `P7-D06`.

Candidate paths, not a verdict:

1. [CODE] Follow-up is Accepting and the transcript is shorter than 3 words, or it is not the tail of the haystack. Admission then treats it as Brian.
2. [CODE] Bout ends when owned ffplay is gone for 450 ms (`PresenceLife.DefaultReleaseDebounceMs`). Command TTS can still be synthesizing the next sentence (`tts_tool_speaker.py` L75–126). After bout stop plus 0.5 s quiet, `voice.record` opens. The next sentence plays into an Accepting capture. [HISTORY] `P9-STORE_Progress.md` records this shape after the Deepgram switch (a 116-character transcript admitted). That note is one occurrence, not a current rate.
3. [CODE] Proactive exact-phrase guard does not apply to reply TTS, and it is not on `main`.
4. [INFERENCE] Speaker bleed louder than the user's voice, the closed-lid case in `P2-D16`, could still feed path 1 if the mic and speakers are the built-in pair. Today's endpoint and enhancement state are UNKNOWN, so this is not established.

Existing protections are the text matcher, the "do not open follow-up while the bout is active" rule, and barge-in being off so she is not transcribed by the full-duplex listener during playback. A failure still occurs if the bout flag drops between sentences or the matcher misses. **Cause of the reports dated 2026-10-18 is UNRESOLVED.**

## 2. Can the playback monitor supply samples?

[CODE] No. `TtsPlaybackMonitor` records session Active/Inactive for owned ffplay pids (`TtsPlaybackMonitor.cs` L8, L254–312, L438–495). It does not read PCM, RMS, or a render timestamp. `P3-D23` forbids audio data on that path.

A reference signal would have to come from somewhere else:

- The process that calls `play_audio_file` already has the file. Hermes does not hand that waveform to the client.
- WASAPI loopback on the render endpoint, if the capturer opens it.
- `IAcousticEchoCancellationControl::SetEchoCancellationRenderEndpoint`, if the capture endpoint exposes the interface (see §3).

None of these are wired.

## 3. Windows endpoint AEC and a software AEC candidate

### Windows

[EXT] Read 2026-10-18.

- `IAcousticEchoCancellationControl` — https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nn-audioclient-iacousticechocancellationcontrol — minimum client build 22621. This PC is build 26200, so the **OS** is new enough. The interface is obtained from `IAudioClient::GetService` after `Initialize`. `E_NOINTERFACE` means this endpoint does not let the app choose the reference, even if some AEC exists. `SetEchoCancellationRenderEndpoint` takes the render endpoint id.
- Windows 11 APO model — https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/windows-11-apis-for-audio-processing-objects — AEC needs a mic stream and a render reference. The engine can switch the reference when the render device changes. A private driver reference often works only for the integrated codec, not USB or Bluetooth.
- Voice Capture DSP (`CLSID_CWMAudioAEC`) — https://learn.microsoft.com/en-us/windows/win32/medfound/voicecapturedmo — older DMO. Modes include single-channel AEC and array-plus-AEC (`AEC_SYSTEM_MODE`, https://learn.microsoft.com/en-us/windows/win32/api/wmcodecdsp/ne-wmcodecdsp-aec_system_mode). It wants to own capture and render indexes. It is not what `sounddevice` opens.

[EXT] NAudio commit `688c029` (2026-06-27, https://github.com/naudio/NAudio/commit/688c029df500a673cb38b438a07f7fd7f2832af0) reports that the AEC control is often absent unless the stream category is communications. That is a third-party note, not a Microsoft guarantee. It matches the risk: opening "the default mic" does not mean AEC is in the graph.

Unverified on this machine: whether Realtek, USB Audio 2.0, or the Bluetooth endpoint implements the control; whether enhancements are on; whether ffplay's render endpoint is the one AEC would reference. A headset that never plays Zola into the room removes acoustic echo without any of this. A speaker in a shop does not.

### WebRTC APM (AEC3)

[EXT] https://webrtc.googlesource.com/src/+/refs/heads/main/modules/audio_processing/aec3/echo_canceller3.h read 2026-10-18. `EchoCanceller3` takes 10 ms band-split frames, 16/32/48 kHz, and a render reference through `AnalyzeRender` which may run beside capture processing. Capture is `AnalyzeCapture` / `ProcessCapture`. The caller must supply **what was played**, in time with the mic. Far-end delay, device rate, and a second clock are the integration cost.

Not in the Zola or Hermes dependency set (static: no WebRTC package in the client project; Hermes playback is ffplay). Adding it means a native library, a format bridge from mp3/ffplay **or** a player that can tap PCM, and a delay estimate. It does not know who Brian is talking to. Double-talk (both speaking) is the case AEC is built for, and it still leaves a residual a transcriber can hear.

No claim that either candidate works on this Latitude until the proof in Audit 07.

## 4. One stream for VAD, a rolling buffer, and STT

[CODE] Today there is no such stream in the client. Hermes opens a **new** purpose-built stream per mode (wake, record, or barge) and they are not supposed to overlap. `voice.record` has no ring buffer. The barge listener has a 1200 ms deque and then throws the rest away after one utterance.

For each option, the buffer has to live with the single owner:

| Option | Where the rolling buffer would live | Competing mic? |
|---|---|---|
| A. Config / plugin | Nowhere available. No hook inserts a deque in front of `AudioRecorder`. | Wake and record already take turns. A second listener is the thing the wake module warns against. |
| B. Hermes patch | Inside `AudioRecorder`, before `_recording` flips, plus the existing FD deque if barge stays. One PortAudio stream. | Must keep wake paused or fold wake into the same stream. |
| C. Client or helper | In that process, in front of VAD and STT. Hermes must not also open `sounddevice`. | `P2-D01` is the conflict. Suppression of Hermes capture is mandatory. |

A persistent stream can feed VAD and a 1–2 s pre-roll without a second open. It cannot, by itself, decide that the speech was for Zola, and it must not forward every VAD hit to `prompt.submit`.

## 5. Double-talk, bleed, noise, and devices

Speech VAD is not addressee detection and not echo cancellation.

- **Double-talk.** Brian talks over her. AEC or a reference mute tries to remove her. The remaining audio should be his. The barge detector instead looks for "louder than the room" and then transcribes the whole clip, including whatever bleed remains. With barge-in off, double-talk is ignored until she is finished and a follow-up starts, which is why the first words are late (SYM-02) and why talk-over does not work (SYM-03).
- **Speaker bleed.** `P2-D16` [HISTORY]: closed lid, bleed RMS about 9600 versus user voice 2800–4200. Enhancements off made barge-in self-trip. Those numbers are not a current measurement.
- **Music, TV, shop.** The record VAD ends on silence (`silence_duration` 1.5 s in the canonical profile). It will capture a loud shop the same way it captures Brian, then Whisper will emit words. Nothing in the Windows admission path asks "was that addressed to Zola?"
- **Device switch.** ffplay uses the default render device. A Bluetooth headset and a USB mic are different clocks. Endpoint AEC that only references the integrated codec will not see headset playback. The monitor's ffplay walk does not follow a device change; it only cares that a process exists.
- **Headset versus speaker.** A headset that contains the playback removes the room echo. It does not fix pre-roll, admission, or wake-free policy. Hardware can shrink SYM-01 and cannot repair SYM-02's missing buffer or SYM-03's disabled trip.

## 6. Latencies that must stay separate

No new timestamps were subtracted. Clocks below are whatever the writer used. They are not combined across turns.

| Interval | Start event | End event | What exists | Source | Limitation |
|---|---|---|---|---|---|
| Text → first audible | Not logged as its own edge | Monitor bout start is the closest client event | [HISTORY] P7 Edge: EoS→first audio median 9534 ms, n=7, shares in S38. One Deepgram `submit_to_first_audio_ms=4628` on 2026-10-12. | `P7-LATENCY_Progress.md`; `P9-SUPERVISE_Progress.md` | Edge path. The Deepgram figure is one turn and includes the model. |
| Inter-sentence audio gap | ffplay exit | next ffplay audible | Monitor can see segment stop/start and a bridged gap under 450 ms. A longer hole becomes a bout stop. | `TtsPlaybackMonitor.cs` L460–494 | No sample clock. Not read from `presence.log`. |
| Stop playback | `stop_playback` / ffplay kill | process gone | Code path only | `voice_mode.py` player; Stop speaking in `VoiceController` | No current timing. |
| Utterance endpoint | last speech sample | `silence_duration` met (1.5 s canonical) | [HISTORY] P7 pauses inside clips: median 120 ms, max 1360 ms, 0 at ≥1500 ms (`S59`) | `P7-LATENCY` | Not a current shop measurement. |
| STT | WAV ready | transcript callback | [HISTORY] warm Whisper base 1562–1847 ms (`P5-D09`); in-call ~1.6 s vs standalone ~1.0 s (`S38`) | P5PRE / P7 | Local file STT, not streaming. |
| Model | `prompt.submit` | first token / first sentence | [HISTORY] largest share of the Edge wait; tools 17.8 s vs 5.4 s submit→first audio | `S38`, `S54` | Not retaken on the current model or voice. |

Text-to-first-audio and inter-sentence gaps are **not** observable as a current distribution. The missing events are listed in Audit 02. Medians above stay historical. The single Deepgram number stays a single sample.

**VOICEPRE-AUD-07** is the first-word gap: endpoint latency and STT latency are not the pre-roll hole. Pre-roll is audio discarded before record starts. Endpoint and STT happen after he stops.
