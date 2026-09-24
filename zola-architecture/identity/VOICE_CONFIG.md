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
# P2-WAKE: sherpa "hey zola", local capture, this profile only — P2-D04
wake_word:
  enabled: true
  provider: sherpa
  phrase: "hey zola"
  capture: local
  surface: auto
  start_new_session: false
  profile_routing: false
  sensitivity: 0.6
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
- `wake_word.enabled`: `true` so Hermes will accept `wake.start` from Voice mode (`P2-D04`).
- `wake_word.provider`: `sherpa` is the keyword engine that can enroll a custom phrase. openWakeWord only ships `hey_hermes` (`P2-D04`).
- `wake_word.phrase`: `"hey zola"` is the only phrase this profile listens for (`P2-D04`).
- `wake_word.capture`: `local` pins the detector to the serve process mic. `auto` plus a `gui` surface would prefer client `wake.feed`, which this client does not send (`P2-D01`, `P2-D04`).
- `wake_word.surface`: `auto` lets the RPC `surface: "gui"` stamp the arm. Capture stays local because of the explicit `capture` key (`P2-D04`).
- `wake_word.start_new_session`: `false`. A wake continues the current conversation. The client ignores the payload flag (`P2-D04`).
- `wake_word.profile_routing`: `false` enrolls only this profile's phrase, not every other Hermes profile's `hey <name>` (`P2-D04`).
- `wake_word.sensitivity`: `0.6` is the Hermes default. Tunable in smoke (`P2-D04`).

Detection runs on-device. No audio leaves the PC for wake detection.

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

P2-WAKE: sherpa-onnx 1.13.4 plus the zipformer keyword model — P2-D04, P2-D10

Installed with the approved command `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m pip install 'sherpa-onnx==1.13.4' 'sentencepiece==0.2.2' 'sounddevice==0.5.5' 'numpy==2.4.3'`. `sounddevice` and `numpy` were already present from Track 1. New packages: `sherpa-onnx==1.13.4`, `sherpa-onnx-core==1.13.4`, `sentencepiece==0.2.2`.

The keyword model is not a pip package. `_ensure_sherpa_model` downloads it with `urllib.request.urlretrieve` on first engine build (not gated by `allow_lazy_installs`). URL: `https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01.tar.bz2`. Destination: `%LOCALAPPDATA%\hermes\profiles\zola\cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01`. Landed on first Phase 4 `wake.start`.

`pypinyin==0.55.0` is required by `sherpa_onnx.text2token` but missing from Hermes's `wake.sherpa` dependency list. Installed with the approved command `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m pip install 'pypinyin==0.55.0'`. `pip check` after that install: `No broken requirements found.`

## Tuning log

| Tunable | Current value | Date | Smoke-test result |
|---|---|---|---|
| `stt.local.model` | `base` | 2026-09-23 | passed |
| `tts.edge.voice` | `en-US-AriaNeural` | 2026-09-23 | passed |
| `voice.silence_duration` | `1.5` | 2026-09-23 | passed |
| `EstimatedWordsPerSecond` | `2.5` | 2026-09-23 | passed. Unchanged. Word rate from the six silent replies. |
| `FirstSentenceLatencySeconds` | `3.3` | 2026-09-23 | passed. Was 1.0. Fixed startup cost. |
| `PerSentenceOverheadSeconds` | `0.5` | 2026-09-23 | passed. Was 3.0; that first fit predicted +23 s gaps. |
| `FollowUpMarginSeconds` | `3.0` | 2026-09-23 | passed. Raised 2.0 → 3.0 after a long-reply tail was still captured at 2.0 s, so the reopened listen window does not time out before the user can reply. |
| `EchoContainmentRatio` | `0.60` | 2026-09-23 | Track 2 specified 0.80. Lowered 0.80 → 0.60 after Whisper `unless` → `and less` (6/8 = 75%). **No longer used** for matching after P2-WAKE review (bag-of-words at 0.60 drops real follow-ups). |
| `EchoLookbackWords` | `20` | 2026-09-23 | last 20 spoken words across completed replies (rolling haystack kept). |
| `EchoMinWords` | `3` | 2026-09-23 | Track 2 bag-of-words floor. **No longer used**; see `EchoMinContiguousWords`. |
| `EchoPhraseWords` | `4` | 2026-09-23 | Track 2 phrase match. **No longer used**. |
| `EchoContiguousRatio` | `0.80` | 2026-09-23 | Retired. |
| `EchoLongRunWords` | `5` | 2026-09-23 | Retired. |
| `EchoMinContiguousWords` | `3` | 2026-09-23 | Under 3 echo-words never dropped. |
| `EchoAnchoredRatio` | `0.60` | 2026-09-23 | Matched / transcript after digit-and-marker strip. |
| `EchoEndSlackWords` | `3` | 2026-09-23 | Minimum end slack. Actual slack is `max(3, ceil(0.25 × transcript words))`. |
| `EchoEndSlackRatio` | `0.25` | 2026-09-23 | Scales end slack with transcript length. |
| `EchoMaxGapWords` | `1` | 2026-09-23 | One unmatched word allowed inside the in-order run. |
| `SpokenDigitWeightFloor` | `1` | 2026-09-23 | Clock only. Token with digits counts as `max(1, digitCount)`. |
| `SpokenAbbrevWords` | `2` | 2026-09-23 | Clock only. a.m./p.m./am/pm. |
| `SpokenAcronymPerLetter` | `1` | 2026-09-23 | Clock only. All-caps 2–5 letter tokens (PDT, NFL, USA). |
| `EchoReopenLimit` | `3` | 2026-09-23 | passed. Reopen follow-up listen after an ignored tail. |
| `EchoReopenDelaySeconds` | `0.5` | 2026-09-23 | passed. Pause before `voice.record` starts again. |
| `wake_word.sensitivity` | `0.6` | 2026-09-24 | passed. 0 false wakes in 10 min of video audio, seated directly in front of the laptop. No tune. |

The first six-run fit kept `EstimatedWordsPerSecond = 2.5` and charged `PerSentenceOverheadSeconds = 3.0` so no estimate was earlier than ffplay exit. That failed `P2-D06`: long replies were predicted +23 s late, and the barge-in listener is already closed in that gap. The same six runs fit a fixed startup plus a small per-sentence cost: `FirstSentenceLatencySeconds = 3.3`, `PerSentenceOverheadSeconds = 0.5`, `FollowUpMarginSeconds = 2.0`. Recomputed gaps (estimate + margin − actual ffplay-gone): S1 +2.2 s, S2 +2.0 s, M1 +3.0 s, M2 +0.5 s, L1 +2.5 s, L2 +2.2 s.

Smoke then failed on a long reply: follow-up at 14:35:28 captured `and less you explicitly share or connect them.` (75% of those words were already in the last 20). `FollowUpMarginSeconds` was raised 2.0 → 3.0 so the reopened listen window does not time out first. Echo containment is 0.60, with a 4-word phrase match, so that tail is dropped even when Whisper splits a word. The timing estimate alone does not guarantee a clean start on long replies; the echo guard is load-bearing. Ignored tails reopen follow-up capture up to `EchoReopenLimit` (3) times. Developer reported smoke test passed after that reopen and confirmed no trailing speech became user input.

P2-WAKE smoke leaked Zola's spoken time (`2026.` and `408 p.m. Pacific Daylight Time.`) because echo compared only the latest reply, and the clock counted `4:08` / `p.m.` as one word each so follow-up opened on her tail. Final rule: rolling 20-word digit-stripped haystack; drop a follow-up only when an in-order run (at most one unmatched word) is ≥ 3 words, ≥ 0.60 of the transcript, and ends within `max(3, ceil(0.25 × transcript words))` of her last spoken words. Clock uses SpokenDigitWeight, SpokenAbbrevWords, and SpokenAcronymPerLetter. Developer reported the full Phase 5 checklist passed 2026-09-24: 0 false wakes in 10 min at sensitivity 0.6 (in front of the laptop); (a) France follow-up submitted; (b) time tail not captured; (c) Super Bowl list tail not captured. The offline `17` vs `seven` echo did not reproduce live.
