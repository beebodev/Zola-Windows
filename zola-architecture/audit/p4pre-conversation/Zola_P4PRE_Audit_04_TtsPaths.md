# P4PRE Audit 04 — TTS Providers, Keys, and Playback Paths (S22)

**Audit ID:** P4PRE  
**Scope:** S22 — Voice naturalness (pacing and inflection)  
**Sources:** Hermes `345cd2b…` + venv `edge_tts` 7.2.7; Windows client `TtsPlaybackMonitor` / `VoiceController` P2-D15; live profile Phase 1  
**Labels against:** `P2-D03`, `P2-D10`, `P2-D15`, `P2-D17`, `P3-D23`; Identity §3–§4; Privacy Plan §5 / §7 (cloud third parties)

---

## Finding summary (this document)

| ID | Label | Severity | Scope | Summary |
|----|-------|----------|-------|---------|
| P4PRE-AUD-20 | [MATCH] | — | [S22] | Live profile Edge `en-US-AriaNeural`; matches `P2-D03` / `VOICE_CONFIG.md` |
| P4PRE-AUD-21 | [GAP] | MEDIUM | [S22] | Hermes Edge path passes only `voice` + derived `rate`; not `pitch`/`volume` |
| P4PRE-AUD-22 | [MATCH] | — | [S22] | Command provider can invoke `edge-tts` CLI with `--pitch`/`--rate`/`--volume` without editing Hermes |
| P4PRE-AUD-23 | [MATCH] | — | [S22] | Current Edge + per-sentence `ffplay` is **P3-D23 PASS** |
| P4PRE-AUD-24 | [RISK] | HIGH | [S22] | Streaming / sounddevice playback is **P3-D23 BREAK** (monitor filters `ffplay` only) |
| P4PRE-AUD-25 | [RISK] | MEDIUM | [S22] | Any Edge `speed` ≠ 1.0 or provider change invalidates P2-D15 constants |
| P4PRE-AUD-26 | [GAP] | MEDIUM | [S22] | No client RPC for true end-of-playback (S17); estimate remains for follow-up when monitor unavailable |
| P4PRE-AUD-27 | [MATCH] | — | [S22] | `security.allow_lazy_installs: false` — ElevenLabs/Piper need explicit install approval (`P2-D10`/`P2-D17`) |
| P4PRE-AUD-28 | [GAP] | LOW | [S22] | No dedicated voice-mode system-prompt slot; shaping = SOUL/identity only for Edge |
| P4PRE-AUD-29 | [RISK] | LOW | [S22] | Per-sentence synthesis can flatten cross-sentence intonation (chunking) |

---

## 1. Provider inventory

Built-ins: **edge, elevenlabs, openai, deepinfra, minimax, xai, mistral, gemini, neutts, kittentts, piper** + **`tts.providers.<name>` command** + **plugins**.

Global keys (defaults from Hermes source / `cli-config.yaml.example`):

| Dotted path | Default | Notes |
|-------------|---------|-------|
| `tts.provider` | `edge` | |
| `tts.speed` | `1.0` | tool clamp ~0.25–4.0 |
| `tts.streaming.provider` | unset | `auto` → elevenlabs→gemini→openai→xai |
| `tts.providers.<name>.{type,command,voice,model,speed,format,timeout,…}` | timeout 120, format mp3, max_text 5000 | command provider |

| Provider | Config keys (high-signal) | Key / package | Local/cloud | Usable today (no installs) | **P3-D23** |
|----------|---------------------------|---------------|-------------|----------------------------|------------|
| **edge** | `tts.edge.voice`, `tts.edge.speed`→rate, `tts.edge.max_text_length` | `edge-tts==7.2.7`; no API key | cloud (MS) | **YES** if serve PATH has **ffplay** | **PASS** |
| **elevenlabs** | `voice_id`, `model_id`, `streaming_model_id`, `base_url`, `wss_url` | `elevenlabs==1.59.0`; `ELEVENLABS_API_KEY` | cloud | **NO** (pkg+key absent; lazy off) | sync **PASS**; stream **BREAK** |
| **openai** / nous gateway | `model`, `voice`, `speed`, `base_url`, `api_key`, `language` | openai SDK; audio key | cloud | keys absent | stream **BREAK**; sync **PASS** |
| **deepinfra** | `model`, `voice`, `base_url` | `DEEPINFRA_API_KEY` | cloud | NO | **PASS** if MP3+ffplay |
| **minimax** | `region`, `model`, `voice_id`, `speed`, `vol`, `pitch`, … | `MINIMAX_API_KEY` | cloud | NO | **PASS** (MP3) |
| **xai** | `voice_id`, `language`, `speed`, `auto_speech_tags`, `optimize_streaming_latency`, … | `XAI_API_KEY` | cloud | NO | stream **BREAK** |
| **mistral** | `model`, `voice_id`, `base_url` | `mistralai`; `MISTRAL_API_KEY` | cloud | NO | **PASS**/ADAPT |
| **gemini** | `model`, `voice`, `audio_tags`, `persona_prompt_file` | `GEMINI_API_KEY`/`GOOGLE_API_KEY` | cloud | NO | stream **BREAK** |
| **neutts** | `ref_audio`, `ref_text`, `model`, `device` | `neutts` (+espeak); not in lazy_deps | local | NO | ADAPT |
| **kittentts** | `model`, `voice`, `speed`, `clean_text` | GitHub wheel; not lazy | local | NO | ADAPT |
| **piper** | `voice`, `voices_dir`, `use_cuda`, `length_scale`, `noise_*`, `volume`, … | `piper-tts`; not lazy | local | NO | ADAPT/BREAK if WAV→sounddevice |
| **command** | `tts.providers.<name>.*` | user CLI | either | if CLI present | **PASS** if child ffplay-visible |
| **plugin** | plugin-defined | plugin | either | if registered | ADAPT |

Phase 1 machine: `edge_tts` YES; `sounddevice` YES; `elevenlabs`/`piper`/`neutts`/`kittentts` NO; API keys above **absent**; `ffplay`/`ffmpeg` at WinGet Links (Gyan 9.0.2) but **not** on audit-shell PATH (serve inherits user PATH at launch — P2-D16).

**P4PRE-AUD-20 [MATCH] [S22]** — Profile `tts.provider: edge` / `en-US-AriaNeural`.  
**P4PRE-AUD-27 [MATCH] [S22]** — Lazy installs disabled; premium/local providers need explicit approval.

---

## 2. Edge specifically

### What Hermes passes

```python
# tools/tts_tool_providers.py ~196–204 (_generate_edge_tts)
kwargs = {"voice": edge_config.get("voice", DEFAULT_EDGE_VOICE)}
if speed != 1.0:
    kwargs["rate"] = f"{round((speed - 1.0) * 100):+d}%"
await edge_tts.Communicate(text, **kwargs).save(output_path)
```

### What installed `Communicate` accepts (edge_tts 7.2.7)

`text`, `voice`, `rate="+0%"`, `volume="+0%"`, `pitch="+0Hz"`, plus boundary/connector/proxy/timeouts. Validation: rate/volume `^[+-]\d+%$`, pitch `^[+-]\d+Hz$`.

| Knob | Reachable without editing Hermes? |
|------|-----------------------------------|
| rate | **YES** — `tts.edge.speed` or `tts.speed` (1.1 → `+10%`) |
| pitch / volume | **NO** via built-in Edge provider |
| pitch/volume via command provider | **YES** — configure `tts.providers.*` with `edge-tts` CLI `--pitch`/`--rate`/`--volume` and `{input_path}`/`{output_path}`/`{voice}` |

**SSML:** edge-tts escapes `& < >` and does not offer a Hermes SSML authoring path. Bracket “audio tags” are **not** rewritten for Edge (Gemini/xAI only) — Edge would speak them literally.

**P4PRE-AUD-21 [GAP] MEDIUM [S22]** — pitch/volume unused by built-in path.  
**P4PRE-AUD-22 [MATCH] [S22]** — command provider is the config-only pitch path.

---

## 3. Playback path under `hermes serve` Voice mode

Entry: `methods_voice._tts_stream_begin` → `stream_tts_to_speaker`; fallback `voice.tts` → `_speak_text_with_barge` → `speak_text`.

| Provider class | Synthesis unit | Format | Who plays | Inter-sentence gap |
|----------------|----------------|--------|-----------|--------------------|
| **Edge (current)** | Per sentence (`SentenceChunker`, min 20 chars, `.!?`) | MP3 temp | Child **ffplay** via `_run_system_player` / `play_audio_file` | No intentional sleep; lore median ~**110 ms** residual |
| Sync file providers (EL sync, minimax, …) | Per sentence / chunk by max_text | MP3 (typical) | ffplay | Similar |
| Streaming (EL/OpenAI/Gemini/xAI when registered + creds) | Chunk stream after sentence ready | PCM int16 mono 24 kHz | **sounddevice** `OutputStream` in serve process (Windows) | Persistent stream — not ffplay |
| Piper / local WAV paths | File | WAV | may use sounddevice or convert | Monitor impact varies |

---

## 4. Effect on `TtsPlaybackMonitor` (`P3-D23`)

Monitor: owned **ffplay** sessions under Hermes serve PID ancestry; polls `IAudioSessionControl::GetState` on **render** endpoint (`AudioSessionInterop` `DataFlowRender`). Bout release debounce **450 ms** (`PresenceLife.DefaultReleaseDebounceMs`).

| Playback path | Sees start/stop? | Bridge 450 ms | Classification |
|---------------|------------------|---------------|----------------|
| Edge per-sentence ffplay | Yes | Appropriate for short gaps | **PASS** |
| Other MP3→ffplay children of serve | Yes | Same | **PASS** |
| sounddevice / PortAudio in serve | **No** (name filter `ffplay` only) | N/A | **BREAK** — need new signal or monitor rewrite |
| Persistent render stream Active through silence | Would break Inactive-based release if ever matched | — | **BREAK** |
| Capture sessions | Not enumerated (render-only) | — | N/A |

**P4PRE-AUD-23 [MATCH] [S22]** — Edge+ffplay PASS.  
**P4PRE-AUD-24 [RISK] HIGH [S22]** — Streaming/sounddevice BREAK for mouth timing / S17 onset.

---

## 5. Effect on `P2-D15` / follow-up timing

```csharp
// VoiceController.cs ~42–45
EstimatedWordsPerSecond = 2.5;
FirstSentenceLatencySeconds = 3.3;
PerSentenceOverheadSeconds = 0.5;
FollowUpMarginSeconds = 3.0;
```

| Change | Invalidates |
|--------|-------------|
| Edge `speed` ≠ 1.0 | WPS, sentence duration, follow-up |
| Provider switch | FirstSentenceLatency, WPS, overhead (fitted Edge+ffplay) |
| Streaming PCM | Onset model + monitor path |

**Hermes end-of-playback event for client?** Internal `tts_done_event` / `mark_audio_output_active` only — **no** `voice.tts.done` RPC. Client uses ffplay Inactive + 450 ms bout (`P3-D23`). Trailing silence inside MP3 still moves mouth after audible end (S17 lore).

**P4PRE-AUD-25 [RISK] MEDIUM [S22]**  
**P4PRE-AUD-26 [GAP] MEDIUM [S22]**

---

## 6. Barge-in and echo per path

| Path | Barge-in | `SPEECH_INTERRUPTED_NOTE` |
|------|----------|---------------------------|
| Edge sync sentences | `stop_event` skips queue; `stop_playback` kills ffplay | Latched on `_fd_trip` / `_tts_stream_stop(user_barge=True)` |
| Streamers | Stop mid-prefetch; PortAudio stop | Same latch / TTL 120 s |
| `/voice off` | — | `user_barge=False` — no latch |

Behaviour is shared at the stream-stop layer; playback mechanism differs.

---

## 7. Text shaping before speech

`tts_text_normalize.prepare_spoken_text`: strip think/verifier → markdown → symbols/units → whitespace → flatten newlines; optional max chars.

Voice stream: strip markdown then `SentenceChunker` — boundary `(?<=[.!?])(?:\s|\n)|(?:\n\n)`, `min_len=20` **hardcoded**. No config for larger chunks. Long-form tool path splits by provider `max_text_length` only.

**P4PRE-AUD-29 [RISK] LOW [S22]** — Each sentence synthesized alone loses cross-sentence intonation; hearable in Phase 6 `chunk_*` comparison.

---

## 8. Reply-style shaping (option 2) without Hermes edit

| Slot | Works? |
|------|--------|
| Profile `SOUL.md` | **YES** — pacing, brevity, spoken style |
| Identity / AGENTS / persona files | YES |
| Dedicated voice-mode system-prompt slot | **No** found |
| Gemini/xAI audio-tag rewrite | **No Edge equivalent** |

**P4PRE-AUD-28 [GAP] LOW [S22]**

---

## 9. Latency to first audio (from source)

| Path | First audio |
|------|-------------|
| Edge sync | After first sentence synth + ffplay start (lore ~2.3–3.2 s typical; P2-D15 uses 3.3 s) |
| True streamers | Playback starts on **first PCM chunk** of sentence one |
| Whole-file `speak_text` | Full synth then play |

Measured Edge latency: Phase 6 spike.

---

## 10. ElevenLabs specifically

| Item | Value |
|------|-------|
| Package | `elevenlabs==1.59.0` (`tts-premium` / lazy_deps `tts.elevenlabs`) |
| Key | `ELEVENLABS_API_KEY` (absent) |
| Sync | convert → opus/mp3 → `play_audio_file` (ffplay) |
| Stream | `pcm_24000`, flash/stream model → sounddevice |
| Reopens | `P2-D03` / `P2-D17`; retune `P2-D15`; stream path **P3-D23 BREAK** |

Report only — install/key is a developer decision.

---

## 11. Options table (no recommendation)

| Option | Touches | Installs / keys | Playback | **P3-D23** | **P2-D15** / **S17** |
|--------|---------|-----------------|----------|------------|----------------------|
| **1 — Edge voice and rate** | Profile `tts.edge.voice` / `tts.edge.speed` or `tts.speed`; `VOICE_CONFIG.md` | None | ffplay per sentence | **PASS** | **ADAPT** — retune WPS/overhead if speed≠1.0 |
| **1b — Edge pitch/volume via command provider** | `tts.providers.*` + `tts.provider` name; CLI from venv | None if edge-tts already present | MP3→ffplay if command writes file then play | **PASS** if ffplay child of serve | **ADAPT** same as rate |
| **2 — Reply-style shaping** | `SOUL.md` / identity (profile, not Hermes source) | None | Unchanged Edge | **PASS** | **ADAPT** if sentence count/length shifts |
| **3 — ElevenLabs (or other streamer)** | Profile provider + key; may need package install | `elevenlabs` + `ELEVENLABS_API_KEY` | sync ffplay **or** stream sounddevice | sync **PASS** / stream **BREAK** | **BREAK**/retune; S17 needs new signal if stream |
| **3b — Local neural (Piper)** | Profile + manual `piper-tts` (not lazy) | Piper install + voice models | WAV→sounddevice or convert | **ADAPT**/BREAK | **BREAK** retune |

Privacy Plan §5 / §7: Edge and ElevenLabs are **cloud third parties**; Piper is local. Identity §3–§4: style profile feedback loop can use SOUL shaping without provider change.

---

## Architecture labels

| Expectation | Verdict |
|-------------|---------|
| `P2-D03` Edge default | **[MATCH]** AUD-20 |
| `P2-D10` / `P2-D17` no auto installs | **[MATCH]** AUD-27 |
| `P2-D15` estimate | **[RISK]** AUD-25 under rate/provider change |
| `P3-D23` ffplay monitor | **[MATCH]** AUD-23 for Edge; **[RISK]** AUD-24 for streamers |
| Identity §3–§4 | Shaping option 2 available via SOUL |
| Privacy §5 / §7 | Cloud providers = third parties — decision input |

---
