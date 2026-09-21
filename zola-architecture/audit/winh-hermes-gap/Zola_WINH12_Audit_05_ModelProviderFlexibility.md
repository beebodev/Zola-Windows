# WINH12 Audit 05 — Model Provider Flexibility

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Master Plan “Provider Abstraction Philosophy” (L1205–1213: do not tightly couple to LLM vendors or API-specific response formats) and Tier 1 **Conversational Models** (L1227–1229): `Current: Gemini. Future abstraction targets: Gemini, OpenAI, Anthropic, local models.`

This half is the **core reasoning model**, not WINH09 STT/voice. Cite `WINH06-AUD-25`; do not re-derive toolset-vs-model-id.

Pre-audit adapter list was **verified and corrected** against this tag.

---

## 1. Adapter breadth vs named targets

**Central identity:** `hermes_cli/providers.py` is the source of truth for provider ids, overlays, and transports (`HERMES_OVERLAYS` L29+, aliases L136–138, `TRANSPORT_TO_API_MODE` L156–159). `agent/provider_registry.py` is a **generic** plugin-registry class (TTS/browser/etc.), not the LLM vendor catalog.

**Verified adapter / transport files (this tag):**

| File | Role |
|---|---|
| `agent/gemini_native_adapter.py` | Native Gemini `generateContent` behind OpenAI-shaped `chat_completions` (module docstring L1–5) |
| `agent/anthropic_adapter.py` + `anthropic_message_convert.py` | Anthropic Messages |
| `agent/codex_responses_adapter.py` + `transports/codex.py` | OpenAI Codex / Responses API (`openai-codex`, `openai-api` overlays) |
| `agent/bedrock_adapter.py` + `transports/bedrock.py` | AWS Bedrock Converse |
| `agent/vertex_adapter.py` | Google Vertex (OAuth2/ADC overlay L89–93) |
| `agent/azure_identity_adapter.py` | Azure identity |
| `agent/moonshot_schema.py` | Kimi/Moonshot **tool-schema** sanitizer, not a separate chat loop |
| `agent/transports/chat_completions.py` | Default OpenAI Chat Completions (OpenRouter, custom, LM Studio, most aggregators) |
| `agent/transports/anthropic.py` | `api_mode=anthropic_messages` |
| `agent/plugin_llm.py` | **Host-owned LLM for trusted plugins** (`ctx.llm`), not the core turn loop |

`agent/models_dev.py` / `agent/model_metadata.py` back catalog/metadata (models.dev), not a fourth runtime.

**Master Plan named targets, natively, without a plugin:**

| Target | Reachable? | How |
|---|---|---|
| Gemini | Yes | `gemini_native_adapter.py`; catalog slugs `google/gemini-*` (`models_catalog_static.py`); Vertex overlay |
| OpenAI | Yes | `openai` / `openai-api` / `openai-codex` overlays; chat_completions or codex_responses |
| Anthropic | Yes | `anthropic` overlay `transport="anthropic_messages"` (providers.py L47) |
| Local models | Yes | §2 |

Hermes is **not** locked to Gemini. Default `config_defaults.py` `"model": ""` (L22) — empty until setup. Dashboard example copy uses Anthropic slugs (`web_server_config.py` L73). Breadth **exceeds** Zola’s four-name list (OpenRouter, Bedrock, xAI, Copilot, …).

**Label:** `[MATCH]` `WINH12-AUD-13` (MEDIUM) — Gemini, OpenAI, and Anthropic are first-party; core loop is not Gemini-locked. (Severity MEDIUM: this is a strength, not a miss.)

---

## 2. Local models

`agent/lmstudio_reasoning.py` is **not** a full local runtime. It maps Hermes reasoning-effort onto LM Studio’s allowed options (L1–6, `resolve_lmstudio_effort` L23–40). The actual path is OpenAI-compatible HTTP:

- Overlay `lmstudio`: `base_url_override="http://127.0.0.1:1234/v1"` (providers.py L41–42).
- Alias `custom` ← `ollama` (L136); `local` ← `vllm`, `llamacpp`, `llama.cpp`, `llama-cpp` (L137).
- `runtime_provider.py` L59–70: those aliases resolve to `custom` (OpenAI-shaped endpoint). `hermes_cli/models.py` has a dedicated Ollama catalog/probe (`_ollama_local_catalog`, L1471–1472, L1526+).

A user can point `provider: custom` (or `ollama` / `local`) at any OpenAI-compatible server (Ollama, llama.cpp, vLLM, LM Studio) with `base_url`. No cloud vendor required.

**Tool calling:** the core loop uses the same `chat_completions` transport and tool round (`WINH03-AUD-02` chain). `tools/schema_sanitizer.py` exists specifically because llama.cpp’s grammar converter is strict (file header). Local is not chat-only; tool calling is the same loop, with schema sanitization for strict backends.

`ollama-cloud` (`https://ollama.com/v1`) is a **cloud** overlay (providers.py L85) — distinct from local Ollama.

**Label:** `[MATCH]` `WINH12-AUD-14` (MEDIUM) — LM Studio is one local path among OpenAI-compat local servers (Ollama / vLLM / llama.cpp); full agent tool loop can run offline against that endpoint.

---

## 3. Switching mechanism

`WINH06-AUD-25`: `/model` is a human slash (`tui_gateway/model_switch.py`); toolsets do not change with model id. Confirmed.

This phase: **live mid-conversation, including provider.**

- `_RUNTIME_KEYS = ("model", "provider", "api_key", "base_url", "api_mode")` (model_switch.py L15).
- `_apply_model_switch` (L203–254) calls `hermes_cli.model_switch.switch_model`, then `_commit_agent_switch` **in-place** on the live agent (L231–238). Failed switch is a no-op (L183–191).
- Session pin: `session["model_override"]` with model **and** provider, base_url, api_key, api_mode (L242–245) — not process-global env (comment L239–241).
- `--once` snapshots/restores runtime (L17–22, L230).
- `--persist` writes config via `persist_model_selection` (L246–248).
- Custom named providers (e.g. `ollama-launch`) resolve from `config.yaml` `providers` (L215–227). Credentials come from that config / env, not from typing a key into `/model` as a secret prompt. A provider with **no** configured key will fail resolution rather than silently stay on the old vendor.

No restart required for a successful in-place switch. A new **session** is not required (`pin_session_override` keeps this session on the new runtime across `/new` rebuilds).

**Label:** `[MATCH]` `WINH12-AUD-15` (MEDIUM) — provider+model switch is live mid-conversation via `/model`; keys/base_url come from config. Caveat (not a new ID): toolsets still do not follow model id (`WINH06-AUD-25`).

---

## 4. API-response-format coupling

Zola: avoid coupling to API-specific response formats.

Hermes internal chat history is **OpenAI-shaped messages**. That is a chosen canonical format, not Gemini-native leaking through.

- `ProviderTransport` (`agent/transports/base.py` L1–4, L12–41): `convert_messages` → `convert_tools` → `build_kwargs` → `normalize_response` → `NormalizedResponse`.
- Registry (`transports/__init__.py` L17–18): `anthropic`, `codex`, `chat_completions`, `bedrock`.
- Gemini: native HTTP is an adapter **into** `chat_completions` so “the agent loop stays OpenAI-shaped” (`gemini_native_adapter.py` L1–5).
- Anthropic: `anthropic_message_convert.py` `convert_messages_to_anthropic` (used from `transports/anthropic.py` L45–52).
- `NormalizedResponse` may carry vendor-specific **replay** fields (`anthropic_content_blocks`, `bedrock_content_blocks`, `codex_reasoning_items` — `types.py` L82–87) so signatures/order survive. The turn loop consumes the normalized object, not raw Gemini JSON.

Turn-loop coupling is to Hermes’s OpenAI-like message list + `NormalizedResponse`, not to Gemini’s wire format. That matches the Provider Abstraction line for the reasoning model.

**Label:** `[MATCH]` `WINH12-AUD-16` (MEDIUM) — per-vendor convert/normalize into `NormalizedResponse`; Gemini native is a facade, not the internal schema.

---

## Finding table (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH12-AUD-13 | MATCH | MEDIUM | `providers.py` overlays; `gemini_native_adapter.py`; Anthropic/OpenAI transports | Named targets Gemini/OpenAI/Anthropic are native; not Gemini-locked |
| WINH12-AUD-14 | MATCH | MEDIUM | `lmstudio_reasoning.py`; `providers.py` L41–42, L136–137 | Local OpenAI-compat (LM Studio/Ollama/vLLM/llama.cpp) can run the tool loop |
| WINH12-AUD-15 | MATCH | MEDIUM | `model_switch.py` L15, L203–254; cite `WINH06-AUD-25` | Live `/model` switches provider+model mid-session |
| WINH12-AUD-16 | MATCH | MEDIUM | `transports/base.py`; `NormalizedResponse`; `anthropic_message_convert.py` | Wire formats convert into one internal representation |
