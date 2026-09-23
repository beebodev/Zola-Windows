P2-VOICE: record the live profile speech and voice keys — P2-D09

Zola's speech-to-text, spoken-reply voice, and capture timing live in the Hermes profile outside this repo, at `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`. Reapply this block to restore them. Hermes deep-merges each section over its defaults, so keys that are not listed stay at their defaults. `hermes serve` reads the file on launch.

```yaml
# P2-VOICE: local speech-to-text, Edge replies, and a shorter end-of-speech pause — P2-D09
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
# P2-VOICE: Hermes must not install packages during a probe or a turn — P2-D10
security:
  allow_lazy_installs: false
```

`stt.provider: local` is set on purpose. With the provider unset, Hermes tries local speech-to-text and then falls through to a cloud provider. An explicit `local` turns that fallback off, so audio stays on this PC (`P2-D02`).

- `stt.provider`: `local` selects faster-whisper and disables the cloud fallback (`P2-D02`).
- `stt.local.model`: `base` is the starting on-device model. This machine has no CUDA, so it runs on CPU (`P2-D02`, `P2-D09`).
- `tts.provider`: `edge` is the free spoken-reply engine. Track 1 writes the key; Track 2 is what turns speech on (`P2-D03`, `P2-D09`).
- `tts.edge.voice`: `en-US-AriaNeural` is the default Edge voice (`P2-D03`, `P2-D09`).
- `voice.silence_duration`: `1.5` seconds of quiet after speech ends a capture. The Hermes default of 3.0 is too slow for a conversation (`P2-D09`).
- `voice.barge_in`: `true` leaves Hermes's interruption listener on during a turn (`P2-D09`).
- `voice.stop_phrases`: `["stop"]` ends the voice exchange when that is the whole utterance (`P2-D09`).
- `voice.thinking_sound`: `true` plays Hermes's thinking sound during a Voice-mode turn (`P2-D09`).
- `security.allow_lazy_installs`: `false` stops Hermes from installing packages during a probe or a turn. A missing dependency shows up as a requirement hint (`P2-D10`).

## Dependencies

Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`.

Before the Phase 2 requirements probe, `sounddevice`, `numpy`, and `faster_whisper` did not import. That probe lazy-installed `faster-whisper==1.2.1`, `sounddevice==0.5.5`, and `numpy==2.4.3`. Installed by Hermes lazy-install during P2-VOICE Phase 2; accepted by developer after the fact. Phase 3 installed nothing further.

`python.exe -m pip check` reported: `No broken requirements found.`

Loading the `base` model through `tools.transcription_local._load_local_whisper_model` took 12.805 seconds and chose device `cpu`, compute type `int8_float32`.

P2-SPEAK: Edge writes mp3, and Windows playback looks up ffplay on PATH — P2-D03

`ffplay` version `9.0.2-full_build-www.gyan.dev`. Installed with `winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements`. Resolved path: `%LOCALAPPDATA%\Microsoft\WinGet\Links\ffplay.exe`, linking to `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffplay.exe`. Requires restart of client/serve after install. A process that is already running keeps its old PATH.

## Machine setup (Latitude 7430)

P2-SPEAK: configuration (f) is the required setup for spoken replies and barge-in — P2-D12

Required: laptop lid open, built-in microphone input 100, Windows audio enhancements on, speaker volume 15. Playback-phase floor 284, trigger 1500, peak speaker-bleed RMS 1289. Fifteen seconds of playback did not self-trip.

A closed lid causes speaker bleed louder than the user's voice and a self-interruption loop. The built-in array mic is in the lid bezel, so a closed lid puts it against the chassis near the speakers. That is what caused the self-trips in configurations (a), (b), and (e). Track 1's 4/4 barge-in count was measured with enhancements off; the required setup now keeps enhancements on.

Spoken replies on this machine play through the ffplay recorded under Dependencies. The client and `hermes serve` have to be started again after that install so the serve inherits the new PATH.

## Tuning log

| Tunable | Current value | Date | Smoke-test result |
|---|---|---|---|
| `stt.local.model` | `base` | 2026-09-23 | passed |
| `tts.edge.voice` | `en-US-AriaNeural` | 2026-09-23 | passed |
| `voice.silence_duration` | `1.5` | 2026-09-23 | passed |
| `EstimatedWordsPerSecond` | `2.5` | 2026-09-23 | passed. Unchanged. Word rate from the six silent replies. |
| `FirstSentenceLatencySeconds` | `3.3` | 2026-09-23 | passed. Was 1.0. Fixed startup cost. |
| `PerSentenceOverheadSeconds` | `0.5` | 2026-09-23 | passed. Was 3.0; that first fit predicted +23 s gaps. |
| `FollowUpMarginSeconds` | `3.0` | 2026-09-23 | passed. Was 2.0 after a long-reply tail capture. |
| `EchoContainmentRatio` | `0.60` | 2026-09-23 | passed. Was 0.80; Whisper `unless` → `and less` (6/8 = 75%). |
| `EchoLookbackWords` | `20` | 2026-09-23 | passed. Last 20 spoken words of the previous reply. |
| `EchoMinWords` | `3` | 2026-09-23 | passed. Bag-of-words skipped for 1–2 word follow-ups. |
| `EchoPhraseWords` | `4` | 2026-09-23 | passed. Drop if any 4-word phrase sits in that tail. |
| `EchoReopenLimit` | `3` | 2026-09-23 | passed. Reopen follow-up listen after an ignored tail. |
| `EchoReopenDelaySeconds` | `0.5` | 2026-09-23 | passed. Pause before `voice.record` starts again. |

The first six-run fit kept `EstimatedWordsPerSecond = 2.5` and charged `PerSentenceOverheadSeconds = 3.0` so no estimate was earlier than ffplay exit. That failed `P2-D06`: long replies were predicted +23 s late, and the barge-in listener is already closed in that gap. The same six runs fit a fixed startup plus a small per-sentence cost: `FirstSentenceLatencySeconds = 3.3`, `PerSentenceOverheadSeconds = 0.5`, `FollowUpMarginSeconds = 2.0`. Recomputed gaps (estimate + margin − actual ffplay-gone): S1 +2.2 s, S2 +2.0 s, M1 +3.0 s, M2 +0.5 s, L1 +2.5 s, L2 +2.2 s.

Smoke then failed on a long reply: follow-up at 14:35:28 captured `and less you explicitly share or connect them.` (75% of those words were already in the last 20). Margin is now 3.0. Echo containment is 0.60, with a 4-word phrase match, so that tail is dropped even when Whisper splits a word. A later run showed the drop working but then Idle ate the listen window; ignored tails now reopen follow-up capture up to 3 times. Developer reported smoke test passed after that reopen.
