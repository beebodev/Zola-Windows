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

## Machine setup (Latitude 7430)

P2-VOICE: this laptop's microphone level decides whether barge-in can trip — P2-D12

The built-in microphone input volume was 43, with Windows audio enhancements on. At that level a normal speaking voice did not stay above Hermes's barge-in trigger long enough to trip. The volume is now 100, and audio enhancements are off. After that change, barge-in tripped on 4 of 4 tries at a normal speaking volume (2026-09-23).

## Tuning log

| Tunable | Current value | Date | Smoke-test result |
|---|---|---|---|
| `stt.local.model` | `base` | 2026-09-23 | |
| `tts.edge.voice` | `en-US-AriaNeural` | 2026-09-23 | |
| `voice.silence_duration` | `1.5` | 2026-09-23 | |
