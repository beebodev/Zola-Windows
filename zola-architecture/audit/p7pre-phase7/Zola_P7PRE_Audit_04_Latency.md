# P7PRE Audit 04 — S38: Where the Time Goes

**Pins:** client `7d77cb51`, Hermes `345cd2b0`. Prior map: `p5pre-phase5/Zola_P5PRE_Audit_04_ListenToThink.md`.  
**Labels:** `S38`, `S23`, `P2-D02`, `P2-D09`, `P5-D09`, `P5PRE-AUD-17`–`19`

---

## 1. Stages (Brian stops → first audio)

| # | Stage | Timed today? | Anchor |
|---|---|---|---|
| A | Silence wait (1.5 s) | Partial — fire time in `agent.log` `Silence detected` | `voice_mode.py` L674–682 |
| B | Capture stop | Partial — `Voice recording stopped` | same |
| C | WAV write | Hermes only — `WAV written` | L840–842 |
| D | Whisper cold load | Partial — `Loading faster-whisper…` | `transcription_tools.py` L321 |
| E | Whisper infer | Partial — `Transcribed …` after; warm med **1665 ms** WAV→line (534 chains) | L370–371 |
| F | Transcript to client | Yes — `voice-timeline` `transcript …` | VC L185–186 |
| G | `prompt.submit` | Hermes `tui prompt accepted`; med **19 ms** after Transcribed | — |
| H | Memory prefetch / time context | Partial — `zola_memory.log` no prefetch `elapsed_ms` | plugin |
| I | Model first token | **UNMEASURABLE** | need new log |
| J | First sentence (chunker) | **UNMEASURABLE** | `SentenceChunker` min_len=20 |
| K | Edge synth | **UNMEASURABLE** | — |
| L | First audio (ffplay bout) | Yes — `presence.log` `playback bout start`; med **5344 ms** after submit | monitor |

**Build would add** (examples): `vad silence_start/fire`, `whisper_infer_start/end ms=`, `prompt.submit`, `agent.turn first_token ms=`, `tts first_sentence`, `tts edge synth ms=`.

**P5PRE-AUD-17 update [MATCH]:** `Silence detected` / `WAV written` **are** in `logs/agent.log`.

### 1b. Live warm STT vs H-1 (L-2)

| Source | Audio duration (s) | Warm metric | Value |
|---|---:|---|---:|
| Phase-5 log splice (n=534 warm) | — | WAV→Transcribed median | **~1665 ms** |
| L-2.2 live | **4.1** | WAV→Transcribed | **1857 ms** |
| L-2.3 live | **5.7** | WAV→Transcribed | **2028 ms** |
| H-1 L1-1…L1-6 | **3.69–6.78** | warm `model.transcribe` median | **~0.75 s** |

L-2 warm durations sit in the same band as L-1 clips; longer audio does not explain the ~0.9–1.3 s gap vs H-1. During L-2 STT windows the wake stream was **closed** (reopened after Transcribed). `presence.log` shows only routine blink/present ticks — **no** logged wake/presence CPU-contention signal.

Library `faster_whisper: Processing audio` appears ~1.1–1.2 s after WAV written on L-2.2/L-2.3; Processing→Transcribed (~0.70–0.88 s) is near H-1. Full attribution still requires Hermes markers.

**Finding P7PRE-AUD-26** [GAP] MEDIUM — Live warm WAV→Transcribed vs H-1 warm infer is **UNEXPLAINED**. Instrumentation needed: `whisper_infer_start` / `whisper_infer_end` (ms) on the Hermes transcription path.

---

## 1a. EoS → first audible reply

**EoS definition:** `T_silence` (`Silence detected`) **− 1.5 s**. Accuracy: assumes last voiced sample immediately precedes the silence timer; trailing noise or early quiet mis-estimates. Last-voiced-sample-in-WAV: **UNMEASURABLE** today.

| Cumulative | Median | p95 |
|---|---:|---:|
| EoS → VAD trigger | **1500 ms** | 1500 |
| EoS → transcript ready | **~3289 ms** | ~3852 |
| EoS → `prompt.submit` | **~3289 ms** | ~3870 |
| EoS → first model token | — | UNMEASURABLE |
| EoS → first TTS audio | **~8633 ms** | ~30100 |

### Breakdown (% of median EoS→audio ≈ 8633 ms)

| Stage | ms | Share |
|---|---:|---:|
| Silence wait | 1500 | **17%** |
| STT (WAV+Whisper+RPC→submit) | ~1789 | **21%** |
| Submit + prefetch | &lt;20 | **&lt;1%** |
| Model + sentence + Edge + ffplay (submit→bout) | ~5344 | **62%** |

Cold Whisper (load line present): med WAV→Transcribed ~2569 ms vs warm 1665 ms (38 cold-classified).

**Finding P7PRE-AUD-16** [GAP] MEDIUM — Dominating bucket (62%) is under-instrumented (TTFT / first sentence / Edge).

---

## 2. Config levers (LEAD-6)

| Key | Effective | Default | Notes |
|---|---|---|---|
| `voice.silence_duration` | 1.5 | 3.0 | profile |
| `voice.silence_threshold` | 200 | 200 | default |
| `stt.local.model` | base | base | profile |
| `stt.local.device` | auto | *(no defaults entry)* | readable if YAML-set; code `get("device","auto")` |
| `stt.local.compute_type` | auto | *(no defaults entry)* | same |
| `stt.language` / `stt.local.language` | en / `""` | en / `""` | local empty → fall through to global `en` |
| `beam_size` | **5 hardcoded** | — | **no config key** |
| `stt.local.vad` | true | true | |
| `unload_after_idle_seconds` | 0 | 0 | |
| `cpu_threads` | library default | — | **not exposed** |
| Serve-start Whisper warm-up (S23) | none | — | first utterance pays cold |

**LEAD-6: PARTLY** — device/compute_type are optional YAML keys (not in defaults table); language pin exists; beam_size is **not** a config key.

**Finding P7PRE-AUD-17** [GAP] MEDIUM — `beam_size` / `cpu_threads` unreachable without Hermes edit.

---

## 3. Models present

| Present | Size |
|---|---|
| `Systran/faster-whisper-base` @ HF hub cache | **~282 MiB** |

| Not present (do not download) | Typical size |
|---|---|
| tiny.en | ~75 MiB |
| base.en | ~145 MiB |
| small.en | ~466 MiB |
| distil-small.en | ~166 MiB |

---

## 4. CPU

**12th Gen Intel Core i7-1265U** — 10 cores / 12 threads. `cpu_threads` not passed to `WhisperModel`.

---

## 5. Silence cutoff risk (B44)

Within-utterance pause distribution: **not available** from logs. Proxy: transcript `duration_s` (n=176) includes 1.5 s silence — p50 7.35 s, p95 22.76 s. WAVs ephemeral in `%TEMP%\hermes_voice\`.

**Finding P7PRE-AUD-18** [GAP] LOW — Cannot safely judge shortening silence without new VAD pause logging.

---

## 6. Model side

Provider/model: **openai-codex / gpt-5.6-terra**. TTFT unmeasurable. Zola adds: system+tools, `zola_memory` prefetch (often empty), time-context `pre_llm_call`, thinking sound.

---

## 7. Fix candidates (not choices)

| # | Candidate | Saving | Risk | Type | Verify |
|---|---|---|---|---|---|
| F1 | Pin `device=cpu`, `compute_type=int8` | 0–? ms (avoid CUDA false-start) | Future GPU | Profile | load line |
| F2 | `stt.local.language: en` | Est. 50–200 ms | Non-English | Profile | lang=en always |
| F3 | `beam_size: 1` | Est. STT ↓ | WER ↑ | **Hermes edit (out)** | H-1 |
| F4 | smaller/en model | Est. 30–50% warm STT | WER ↑ | Profile + **P2-D17** download | H-1 |
| F5 | silence 1.5→1.0 | **500 ms** | Cutoffs | Profile | pause histogram |
| F6 | S23 warm-up | ~cold first-turn | RAM | Hermes/feature | restart |
| F7 | Stage logging | 0 ms | Volume | Client/Hermes | L-2 |
| F8 | TTS/chunk (S34) | Part of 62% bucket | Quality | Hermes/Edge | bout med |
| F9 | Simple questions without tools (AUD-25) | L-2.2 submit→card ≈ **5.7 s** | Tool/SOUL policy | model/tools | L-2 |
| F10 | Close AUD-26 STT gap | ~0.9 s if live→H-1 | Need infer markers first | Hermes logs | H-1 vs live |

**Rank for effort:** model+TTS(+tools) bucket (62%) > STT (21%) > silence (17%). STT knobs are the only profile-reachable slice without installs; largest felt delay needs TTFT/TTS instrumentation first; tool-on-simple-Q (F9) is a separate post-submit lever.
