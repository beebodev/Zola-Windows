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
    voice: en-GB-SoniaNeural
    speed: 0.95
agent:
  clarify_timeout: 300
approvals:
  mode: manual
voice:
  silence_duration: 1.5
  barge_in: false
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
- `tts.provider`: `edge` (built-in). Phase 6 command provider `sonia_cmd` was tried at `--pitch=+0Hz` then **restored** — first-audio median ~855–1030 ms worse than built-in (gate +300 ms); pitch dropped. Command block kept in progress notes / failed snapshot only.
- `tts.edge.voice`: `en-GB-SoniaNeural` at speed 0.95 (`P4-D19` + speed A/B; was Aria, then provisional Sonia 1.1).
- `tts.edge.speed` / command `--rate` (if command provider is re-enabled): **literal duplicate.** Hermes does **not** sync them — both must change together.
- `voice.silence_duration`: `1.5` seconds of quiet after speech ends a capture. The Hermes default of 3.0 is too slow for a conversation (`P2-D09`).
- `voice.barge_in`: `false` (`P4-D28`, applied under `P4-D25` / P4-ASK Option A). Was `true` under `P2-D09`; talking over her no longer interrupts (Cancel / "Hey Zola" after she finishes still work).
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

## Clarify timeout (P4-REQUEST)

P4-REQUEST: profile clarify wait before Hermes skips — P4-D10

| Field | Value |
|---|---|
| Key | `agent.clarify_timeout` |
| Value | `300` |
| Date | 2026-09-30 |
| Decision | `P4-D10` |
| Backup | `config.yaml.bak-P4-REQUEST-20260930-072643` (same folder as live `config.yaml`) |
| Approval | developer-approved |

Applied under `agent:` beside `reasoning_effort`. No serve restart required; Hermes reloads this on each clarify. No other profile key was changed in that edit.

## Voice: Sonia at 0.95 (P4-VOICE Round 1)

P4-VOICE: provisional spoken voice until live trial verdict — P4-D19

| Field | Value |
|---|---|
| Key | `tts.edge.voice` / `tts.edge.speed` |
| Value | `en-GB-SoniaNeural` / `0.95` (Edge `rate=-5%`; was provisional `1.1`) |
| Date | 2026-10-01 |
| Decision | `P4-D19` + speed A/B (pick C) |
| Backup | `config.yaml.bak-P4-VOICE-20261001-075403` (voice); `config.yaml.bak-P4-VOICE-speed-20261001-084653` (speed 1.1→0.95) |
| Approval | developer-approved (`apply voice`; speed A/B **pick C**) |

Diff vs first backup: Sonia + speed. Speed A/B: `1.1` → `0.95` only. Serve restarted after speed apply (`127.0.0.1:52894`).

**Live-trial verdict (2026-10-01):** Keep Sonia. 1.1 too fast. Speed A/B labels A=1.0, B=1.05, C=0.95 — **picked C (0.95)**. Deeper via Phase 6 pitch A/B (`0 / −2 / −4 / −6 Hz`). Husky texture (breathiness) not possible with Edge — future premium-voice item. Phase 6 command `--rate` must be `-5%` (literal duplicate of `tts.edge.speed` — both must change together).

## Command provider pitch baseline (P4-VOICE Round 3)

P4-VOICE: command-provider Edge for pitch control — P4-D21

| Field | Value |
|---|---|
| Key | `tts.provider` / `tts.providers.sonia_cmd` |
| Value | Tried `sonia_cmd` @ `--pitch=+0Hz`; **restored `edge`** (pitch dropped) |
| Date | 2026-10-01 |
| Decision | `P4-D21` — latency gate fail (median first-audio ~+0.85–1.0 s vs built-in; limit +300 ms) |
| Backup | `config.yaml.bak-P4-VOICE-cmd-20261001-094400` (pre-cmd); failed snapshot `config.yaml.bak-P4-VOICE-cmd-failed-20261001-122800` |
| Approval | developer-approved apply; auto-restore per Phase 6 latency rule |

**Rate sync note:** `--rate` in the command string is a **literal duplicate** of `tts.edge.speed` (0.95 → `-5%`). Hermes does not derive one from the other; both must be edited together.

**Outcome:** Pitch A/B **not run**. Final provider remains built-in Edge (Sonia 0.95). Developer may override (re-apply command provider) if they accept the latency.

## Barge-in off (P4-ASK Option A)

P4-ASK: disable Hermes full-duplex barge listener so clarify answers use the client capture — P4-D28 (applied under P4-D25) / Option A

| Field | Value |
|---|---|
| Key | `voice.barge_in` |
| Value | `false` |
| Date | 2026-09-30 |
| Decision | `P4-D28` (applied under `P4-D25`) / Option A |
| Backup | `config.yaml.bak-P4-ASK-20260930-102716` (same folder as live `config.yaml`) |
| Approval | developer-approved (`apply barge-in off`) |

Diff vs backup: one line (`barge_in: true` → `false`). No other profile key changed.

**Serve restart:** not strictly required for the next arm (`_voice_cfg_dict` / mtime-cached effective load). An already-running FD listener is not stopped by the flip. **Recommend restart** before Phase 5/smoke so no stale listener remains.

### Approvals mode (P4-REQUEST smoke retarget)

| Field | Value |
|---|---|
| Key | `approvals.mode` |
| Value | `manual` |
| Date | 2026-09-30 |
| Reason | Smoke B6: Hermes default merge is `smart` (auxiliary LLM auto-approved); force gateway cards |
| Backup | `config.yaml.bak-P4-REQUEST-approvals-manual-20260930-075913` |
| Approval | developer Option 1 after B6 FAIL |

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
| `tts.edge.voice` | `en-GB-SoniaNeural` | 2026-10-01 | P4-D19 kept; speed set via A/B |
| `tts.edge.speed` | `0.95` | 2026-10-01 | Speed A/B pick C (was 1.1 too fast; Edge rate=-5%) |
| `tts.provider` | `edge` | 2026-10-01 | P4-D21: `sonia_cmd` tried then restored — latency gate fail; pitch dropped |
| `voice.silence_duration` | `1.5` | 2026-09-23 | passed |
| `EstimatedWordsPerSecond` | `2.5` | 2026-09-23 | passed. Unchanged. Word rate from the six silent replies. |
| `EstimatedWordsPerSecond` | `2.5` | 2026-10-01 | P4-D22 refit on Sonia 0.95 — constants unchanged; the 2.5 wps estimate is conservative vs measured ~3.3–3.5 wps; fallback never early on bout-duration. |
| `FirstSentenceLatencySeconds` | `3.3` | 2026-09-23 | passed. Was 1.0. Fixed startup cost. |
| `FirstSentenceLatencySeconds` | `3.3` | 2026-10-01 | P4-D22 refit — unchanged (onset 3300 ms). |
| `PerSentenceOverheadSeconds` | `0.5` | 2026-09-23 | passed. Was 3.0; that first fit predicted +23 s gaps. |
| `PerSentenceOverheadSeconds` | `0.5` | 2026-10-01 | P4-D22 refit — unchanged. |
| `FollowUpMarginSeconds` | `3.0` | 2026-09-23 | passed. Raised 2.0 → 3.0 after a long-reply tail was still captured at 2.0 s, so the reopened listen window does not time out before the user can reply. |
| `FollowUpMarginSeconds` | `5.0` | 2026-10-01 | P4-D22: 3.0 → 5.0. Covers worst estimatedEnd lead **4.33 s** (M2) on Sonia 0.95 six-pack; fails late, not early. Lead table: S1 2.21, S2 2.59, M1 0.31, M2 **4.33**, L1 −1.73, L2 −42.46 (seconds; positive = estimate leads bout). Note: reply `forced_estimate` path still uses remaining only (no margin) — lore flag. |
| `StartupWindowSeconds` | `5.3` | 2026-10-01 | P4-D22 / K2: was 4.3; raised to ≥1.5× worst Edge first-audio (~3.49 s). |
| `EchoContainmentRatio` | `0.60` | 2026-09-23 | Removed (P3-STATE) |
| `EchoLookbackWords` | `20` | 2026-09-23 | last 20 spoken words across completed replies (rolling haystack kept). |
| `EchoMinWords` | `3` | 2026-09-23 | Removed (P3-STATE) |
| `EchoPhraseWords` | `4` | 2026-09-23 | Removed (P3-STATE) |
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
