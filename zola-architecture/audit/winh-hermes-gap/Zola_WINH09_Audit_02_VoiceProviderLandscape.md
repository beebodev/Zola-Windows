# WINH09 Audit 02 — TTS/STT Provider Landscape: Does Hermes Cover Tier 1?

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Master Plan **External API Strategy → Tier 1** (Speech Recognition current Deepgram; Conversational Voice/Live Speech current Gemini Live, future ElevenLabs/Cartesia/PlayAI). Provider Abstraction Philosophy cited from WINH07, not re-derived.

---

## Direct answer (developer question)

**Zola-Windows does not need to integrate ElevenLabs from scratch.** Hermes already has a built-in ElevenLabs TTS handler (`tts.provider: elevenlabs`) with voice id + model in config, a file `synthesize` path, and a **chunked streaming** speaker path (`ElevenLabsStreamer`). STT can use ElevenLabs Scribe (`stt.provider: elevenlabs`). Set `ELEVENLABS_API_KEY` and config — no separate Windows SDK.

**Cartesia and Deepgram are not Hermes built-ins.** They do not appear in `_BUILTIN_NAMES` for TTS or STT. Adding either is a **plugin** (`PluginContext.register_tts_provider` / `register_transcription_provider`) or a **`type: command`** `config.yaml` entry (external CLI, no Python class). Tests already use `"cartesia"` as a *plugin-name example*, not a shipped provider.

**Gemini Live is not covered.** Hermes’s optional full-duplex mode is **OpenAI GPT-Live** (`voice.voice_chat_mode: gpt-live`, `tools/voice_live.py`), not Vertex Gemini Live. Default voice chat is **chained** STT → Hermes turn → TTS (`voice_chat_mode: chained`).

**Practical Windows default:** use Hermes’s registry (Edge TTS is the default `tts.provider`; local faster-whisper / Groq / OpenAI / ElevenLabs for STT). Bring Cartesia/Deepgram/Gemini Live only if product quality requires those vendors — as a plugin or a Zola-side adapter, not because Hermes lacks *any* Tier-1-shaped voice I/O.

---

## 1. TTS provider registry (verified)

**Built-ins** (`agent/tts_registry.py` `_BUILTIN_NAMES` L25–28; kept in sync with `tools/tts_tool.py` `BUILTIN_TTS_PROVIDERS`, defined at `tools/tts_command_provider.py` L269–271):

`edge`, `elevenlabs`, `openai`, `minimax`, `xai`, `mistral`, `gemini`, `neutts`, `kittentts`, `piper`, `deepinfra`.

Default: `tts.provider: "edge"` (`hermes_cli/config_defaults.py` L1005–1008). ElevenLabs block: `voice_id`, `model_id` (L1013–1016).

**ABC:** `agent/tts_provider.py` `TTSProvider.synthesize` L44–56 is required; `stream()` L58–73 **defaults to `NotImplementedError`** — dispatcher then falls back to synthesize + read-whole-file.

**ElevenLabs actual surface:**

- **Batch/file:** `tools/tts_tool_providers.py` `_generate_elevenlabs` L219–229 — `client.text_to_speech.convert` with `voice_id`, `model_id`, opus or mp3 to a file.
- **Streaming (speaker / voice mode):** separate registry `tools/tts_streaming.py` `@register("elevenlabs")` `ElevenLabsStreamer` L173–193 — chunked HTTP `pcm_24000`, `streaming_model_id` / `model_id`. Used by `stream_tts_to_speaker` (`tools/tts_tool_speaker.py`).
- **Not** the full ElevenLabs product (no voice-cloning console, no all models, no pronunciation dictionaries) through `TTSProvider`. Voice **selection** and **model** for synthesis **are** reachable via config.

Built-in ElevenLabs does **not** implement `TTSProvider.stream()` on the plugin ABC; streaming is the parallel `StreamingTTSProvider` class. `tts.streaming.provider: auto` prefers elevenlabs → gemini → openai → xai (`tts_streaming.py` L142–144). Edge has **no** chunked-PCM streamer (comment L143).

**Label:** `[PARTIAL]` `WINH09-AUD-01` (MEDIUM) — ElevenLabs TTS is a real built-in (file + speaker streaming); ABC `stream()` is not implemented for that vendor; catalog is a subset of the vendor API.

---

## 2. STT / transcription registry (verified)

**Built-ins** (`agent/transcription_registry.py` L23–25; `tools/transcription_common.py` `BUILTIN_STT_PROVIDERS` L45–46):

`local`, `local_command`, `groq`, `openai`, `mistral`, `xai`, `elevenlabs`, `deepinfra`.

**Cartesia / Deepgram:** grep of Hermes `*.py` at this pin — **no** production provider named `deepgram` or `cartesia` except tests using `cartesia` as a fake plugin name (`tests/tools/test_tts_plugin_dispatch.py`). Accurate: **absent from built-ins**.

**How to add one:**

| Path | Where | Code? |
|---|---|---|
| `stt.providers.<name>: type: command` | `tools/transcription_command.py` L31–41; dispatch `transcription_tools.py` ~L473 | No Python class; CLI/curl template |
| `PluginContext.register_transcription_provider` | `hermes_cli/plugins.py` L1057–1061 → `agent.transcription_registry` | Yes — subclass `TranscriptionProvider.transcribe` (`agent/transcription_provider.py` L19–30, **file-based**) |
| Same for TTS | `register_tts_provider` L1051–1056; `tts.providers.<name>: type: command` (`tts_command_provider.py` L1–3) | Built-in name always wins; command wins over plugin |

ABC `transcribe(file_path, ...)` is **batch file**, not a streaming WebSocket STT API. A Deepgram live stream would need a plugin that still ends in a file envelope, or a new code path outside this ABC.

**Label:** `[PARTIAL]` `WINH09-AUD-02` (MEDIUM) — swappable STT registry exists; Deepgram/Cartesia not shipped; add via command/plugin (file STT, not live streaming STT).

---

## 3. Config-only swap (Provider Abstraction, voice)?

For any **built-in** name: `tts.provider` / `stt.provider` in `config.yaml` (or `config.set`). No code change. Built-in always wins over plugin of the same name (`tts_registry.py` L6–8, L31–36). Command-type same name wins over plugin (`plugins.py` L1054–1055).

STT unset = autodetect ladder (`config_defaults.py` L1074–1078), not a stored provider. TTS default is explicitly `"edge"`.

This matches the *voice* application of Provider Abstraction: backends are named and replaceable. It does **not** make Gemini Live or Deepgram streaming appear without a plugin/new mode.

**Label:** `[MATCH]` `WINH09-AUD-03` (LOW) — built-in TTS/STT names swap by config.

---

## 4. Cost / latency / streaming metadata?

`TTSProvider` exposes `list_voices`, `synthesize`, optional `stream`/`warm`/`release` — **no** latency, cost, or “streaming capable” flags on the ABC.

Operator-visible streaming choice is **config**, not a catalog: `tts.streaming.provider` (`auto` vs pin). `_PROVIDER_PRIORITY` is a hard-coded UX list (L142–144). xAI has `optimize_streaming_latency` as a **request knob** (`tts_tool_providers.py` L45, L309), not a comparable capability table.

`TranscriptionProvider` has no streaming/latency fields; `transcribe` is file I/O.

Choosing a voice-first provider is **try-and-measure**, except the documented auto-stream priority for four vendors.

**Label:** `[PARTIAL]` `WINH09-AUD-04` (MEDIUM) — streaming exists as a separate speaker registry + config pin; no provider-level latency/cost metadata for product selection.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH09-AUD-01 | PARTIAL | MEDIUM | `tts_registry.py` L25–28; `tts_tool_providers.py` L219–229; `tts_streaming.py` L173–193 | ElevenLabs built-in file + PCM streamer; ABC `stream()` still default-unimplemented |
| WINH09-AUD-02 | PARTIAL | MEDIUM | `transcription_registry.py` L23–25; `transcription_command.py` L31–41 | No Cartesia/Deepgram built-in; command or plugin (file STT) |
| WINH09-AUD-03 | MATCH | LOW | `config_defaults.py` L1008; `plugins.py` L1051–1061 | Built-in `tts.provider` / `stt.provider` swap by config |
| WINH09-AUD-04 | PARTIAL | MEDIUM | `tts_provider.py` L58–73; `tts_streaming.py` L142–159 | No latency catalog; `streaming.provider` auto/pin only |
