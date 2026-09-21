# WINH01 Audit 01 — Hermes Repository Structure Map

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`
Clone path (external): `C:\Users\test\Dev\hermes-agent`

This is a map, not a findings document. Purposes below are inferred from each directory's own README / AGENTS.md / entry-point docstring / file names in this tag — not from marketing copy. WINH02-07 should use this file to locate code rather than guessing.

## Language and build system (confirmed)

- Primary language: Python 3.11 (`requires-python = ">=3.11,<3.14"` in `pyproject.toml` L15; `.python-version` contains `3.11`).
- Python package manager / lockfile: `uv` (`uv.lock` at repo root; installer and CI call `uv python install` / `uv sync` / `uv pip install`). `setup.py` still exists as a thin PEP 517 helper (`pyproject.toml` `[build-system]` comments at L404-408).
- Secondary language: TypeScript / Node.js for TUI, web dashboard, and Electron desktop. Root `package.json` is an npm workspaces root (`apps/*`, `ui-tui`, `ui-tui/packages/*`, `web`, `tests-js`). Engines: Node `^22.22.0 || ^24.11.0 || >=26.0.0`.
- Desktop GUI installer: Rust / Tauri 2 (`apps/bootstrap-installer/src-tauri/Cargo.toml` — crate `hermes-bootstrap`, binary name `Hermes-Setup`).
- Optional Nix packaging: `flake.nix` + `nix/`.
- Native C extension (optional session-search tokenizer): `native/fts5_cjk/` built with `gcc` via `build.sh`.
- "Native Windows" for this project therefore means: CPython 3.11 via `uv` wheels + a Node runtime + Git Bash for the terminal tool + (optional) Electron/Tauri binaries. It is not a compiled-from-source Windows port of a C/C++ agent.

There is no `CHANGELOG.md` in this tag. Release notes live on GitHub Releases and are mirrored into `website/` docs.

---

## Top-level directories (level 1)

### `.github/`
CI, issue/PR templates, reusable Actions. `AGENTS.md` is not here; workflow names and comments are the source. Subdirs: `actions/`, `ISSUE_TEMPLATE/`, `scripts/`, `workflows/`. Notable Windows-related workflows: `tests-os.yml` (windows-latest-32-core, `-m windows_only`), `installer-tests.yml` (PowerShell 5.1 + pwsh against `scripts/install.ps1`), `install-e2e-windows-run.yml`, `windows-venv-e2e.yml` (on-demand `wine2e/**` branches only), `lint.yml` job `windows-footguns` (runs on ubuntu, static scan). Orchestrator: `ci.yaml`.

### `acp_adapter/`
ACP (Agent Communication Protocol) adapter. Module docstring in `acp_adapter/__init__.py`: "ACP (Agent Communication Protocol) adapter for hermes-agent." Entry: `__main__.py`, `server.py`, `session.py`, `tools.py`, `auth.py`. Python extra: `acp` in `pyproject.toml` (`agent-client-protocol==0.9.0`).

### `agent/`
Core agent runtime. `agent/AGENTS.md`: "`run_agent.py` is the public facade: `AIAgent` is assembled from mixins... a turn is `agent/conversation_loop.py::run_conversation`." Subdirs:
- `lsp/` — language-server integration
- `monitoring/` — gateway health / metrics hooks
- `pet/` — pet/companion feature
- `proxy_sources/` — proxy configuration
- `secret_sources/` — secret backends (1Password / Bitwarden / vault; see also `vault_backends/`)
- `transports/` — model-call transports (`chat_completions.py` etc.; `providers/README.md` names `agent/transports/chat_completions.py::_build_kwargs_from_profile()`)
- `vault_backends/` — credential vault implementations
- `verify/` — verification helpers

Key files (not a complete list): `conversation_loop.py`, `agent_init.py`, `memory_manager.py`, `memory_provider.py`, `prompt_builder.py`, `system_prompt.py`, `curator.py`, `skill_commands.py`, `tool_executor.py`, `inline_tool_executors.py`, plus `turn_*.py` phase siblings.

### `apps/`
First-party applications. Subdirs:
- `desktop/` — Electron desktop app (`apps/desktop/README.md`: "The native desktop app for Hermes Agent... Available for macOS, Windows, and Linux." `package.json` `productName: Hermes`, scripts include `dist:win`).
- `shared/` — shared TS JSON-RPC/WebSocket client used by desktop and dashboard (`tui_gateway/AGENTS.md` and `web/AGENTS.md` both name `@hermes/shared`).
- `bootstrap-installer/` — Tauri "Hermes Setup" GUI installer that drives `scripts/install.ps1` (`Cargo.toml` description: "Hermes Setup — signed installer that drives scripts/install.ps1").

### `assets/`
Contains `banner.png` (referenced by root `README.md`).

### `contributors/`
Contributor metadata. Has `README.md` and `emails/`.

### `cron/`
Scheduled jobs. `cron/AGENTS.md`: "`cron/jobs.py` (job store) + `cron/scheduler.py` (tick loop; `scheduler_*.py` siblings)." Subdir: `scripts/`. Also documents kanban dispatcher coupling (kanban itself lives under `plugins/kanban/` and `hermes_cli/kanban*.py`).

### `docker/`
Container entrypoints (`entrypoint.sh`, `s6-rc.d/`, `cont-init.d/`). Complements root `Dockerfile` and `docker-compose.yml` / `docker-compose.windows.yml`.

### `evals/`
Evaluation harnesses and probes (browser_use, memory, providers, gateway, desktop_mcp_oauth, subagent_process_handoff, tool_search, etc.). Each subdir typically has its own README.

### `gateway/`
Messaging gateway. `gateway/AGENTS.md`: "`gateway/run.py` is the facade; adapters in `platforms/<name>.py` over `platforms/base.py`." Subdirs:
- `platforms/` — HTTP API server adapter (`api_server.py`), Signal, WhatsApp cloud, webhook, yuanbao, plus `ADDING_A_PLATFORM.md`. Telegram/Discord/Slack/etc. as **plugins** live under `plugins/platforms/`, not here.
- `relay/` — relay transport
- `builtin_hooks/` — always-registered gateway hooks
- `assets/` — static assets

### `hermes_cli/`
CLI, config, dashboard backend, subcommands. `hermes_cli/AGENTS.md`: "`cli.py` holds `HermesCLI`; behaviour lives in mixins..." Subdirs:
- `subcommands/` — `hermes <verb>` implementations (`gateway.py`, `skills.py`, `memory.py`, `cron.py`, `dashboard.py`, `setup.py`, `doctor.py`, ...)
- `web_routers/` — FastAPI routers for `hermes dashboard` / `hermes serve` (sessions, chat_ws, cron, skills, memory_providers, mcp, ...)
- `local_runtime/` — local runtime helpers
- `observability/` — tracing/metrics CLI
- `proxy/` — proxy commands
- `dashboard_auth/` — dashboard auth

Windows-specific files here include `stdio.py` (`configure_windows_stdio`), `win_pty_bridge.py` (ConPTY), `pty_bridge.py` (POSIX).

### `locales/`
YAML translation files (`en.yaml`, `zh.yaml`, `es.yaml`, ...).

### `native/`
Native extensions. Subdir `fts5_cjk/` — `README.md`: "unicode61 + CJK character bigrams... Build & install to `~/.hermes/lib/`." `build.sh` compiles `libfts5_cjk.so` with `gcc -shared -fPIC`.

### `nix/`
NixOS / home-manager modules (`hermes-agent.nix`, `desktop.nix`, `tui.nix`, `web.nix`, `python.nix`, ...).

### `optional-mcps/`
Catalog of optional MCP server definitions (airtable, linear, figma, grafana, ...). Not loaded by default.

### `optional-skills/`
Official skills shipped but **not** activated by default. `optional-skills/DESCRIPTION.md`: "not copied to `~/.hermes/skills/` during setup. They are discoverable via the Skills Hub." Categories include autonomous-ai-agents, blockchain, creative, devops, mcp, mlops, research, security, smart-home, software-development, web-development, etc.

### `plugin-catalog/`
YAML index of external/curated plugins (`README.md` present; files such as `snyk.yaml`, `touchdesigner.yaml`, `removed.yaml`).

### `plugins/`
In-tree plugins. `plugins/AGENTS.md` (root of this dir) plus `plugin_loader.py`. Subdirs:
- `memory/` — honcho, mem0, hindsight, holographic, supermemory, openviking, retaindb, byterover
- `model-providers/` — ProviderProfile plugins (openrouter, anthropic, nous, gemini, ollama-cloud, ...)
- `platforms/` — telegram, discord, slack, whatsapp, matrix, teams, feishu, dingtalk, wecom, email, sms, homeassistant, google_chat, irc, line, mattermost, photon, simplex, ntfy, raft, a2a, buzz
- `browser/`, `context_engine/`, `cron_providers/`, `dashboard_auth/`, `disk-cleanup/`, `google_meet/`, `hermes-achievements/`, `image_gen/`, `kanban/`, `observability/`, `security-guidance/`, `spotify/`, `teams_pipeline/`, `video_gen/`, `web/`

### `providers/`
Provider registry ABC. `providers/README.md`: "Registry and ABC for every inference provider... The **profiles themselves** live as plugins under `plugins/model-providers/<name>/`." Files: `base.py`, `__init__.py`.

### `scripts/`
Installers and maintainer scripts. Windows-relevant: `install.ps1`, `install.cmd`, `desktop-update.ps1`, `check-windows-footguns.py`, `desktop-update/`. Also `install.sh`, CI helpers under `ci/`, sandbox E2E under `sandbox/`.

### `skills/`
Bundled skills copied into `$HERMES_HOME/skills/` on install (`tools/skills_sync.py`, `skills/AGENTS.md`). Categories: apple (macOS-gated), autonomous-ai-agents, creative, devops, email, media, note-taking, productivity, research, social-media, software-development, web, plus `index-cache/`.

### `tests/`
Python tests mirrored roughly to production areas (`agent/`, `cron/`, `gateway/`, `hermes_cli/`, `tools/`, `install/`, `desktop/`, `plugins/`, ...). `tests/conftest.py` defines `windows_only` / `macos_only` markers.

### `tests-js/`
Vitest/TypeScript tests for installer known-failures, Node engine alignment, desktop entitlements, etc.

### `tools/`
Model-facing tools and the registry. `tools/AGENTS.md`: "`tools/registry.py` ... each `tools/*.py` calls `registry.register()` at import time; `model_tools.py` imports the registry." Subdirs:
- `environments/` — terminal backends: `local.py` (Git Bash on Windows), `docker.py`, `ssh.py`, `modal.py`, `daytona.py`, `singularity.py`, `vercel_sandbox.py`
- `computer_use/` — desktop control via cua-driver MCP (`website/docs/user-guide/features/computer-use.md` claims macOS, Windows, and Linux)
- `tool_gateway/` — Nous Tool Gateway client
- `wakewords/` — bundled `hey_hermes.onnx` / `.tflite` (`tools/wakewords/README.md`)
- `neutts_samples/` — TTS samples

Also: `delegate_tool.py` (subagents), `voice_mode.py` / `voice_live.py` / `wake_word.py`, `memory_tool.py`, `skills_tool.py`, `process_registry.py` (PTY via ptyprocess/pywinpty).

### `tui_gateway/`
JSON-RPC backend for TUI, Desktop, and dashboard `/chat`. `tui_gateway/AGENTS.md`: "Newline-delimited JSON-RPC over stdio... Desktop reaches the same server over WebSocket." Subdir `contracts/` (Pydantic wire models; generated TS/OpenRPC). Facade: `server.py`; methods in `methods_*.py` including `methods_voice.py`.

### `ui-tui/`
Ink/React terminal UI (`ui-tui/README.md`). Node package; spawned as `hermes --tui`.

### `web/`
Dashboard SPA (`web/README.md`, `web/AGENTS.md`). Vite + React. Backend is `hermes_cli/web_server.py` + `web_routers/`.

### `website/`
Docusaurus docs site (`website/README.md`, `docusaurus.config.ts`). User-facing Windows docs: `website/docs/user-guide/windows-native.md`, `windows-wsl-quickstart.md`.

---

## Top-level files that matter as modules (not directories)

These sit at repo root because they are the public Python facade:

- `run_agent.py` — `AIAgent` class facade (`agent/AGENTS.md`)
- `cli.py` — interactive CLI (`hermes_cli/AGENTS.md`)
- `model_tools.py` / `toolsets.py` — tool discovery + toolset dict
- `mcp_serve.py` — `hermes mcp serve` stdio MCP server (docstring: expose messaging conversations as MCP tools)
- `hermes_state*.py` — SQLite session store (`state.db`); FTS, WAL, repair
- `setup-hermes.sh`, `scripts/install.sh`, `scripts/install.ps1` — installers
- `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`

---

## Concern index (for WINH02-07)

### Persistent memory storage

- Built-in file store: `tools/memory_tool.py` (`MemoryStore`; `get_memory_dir()` → `get_hermes_home() / "memories"`; `MEMORY.md` + `USER.md`). Loaded at agent init by `agent/agent_init.py::_init_memory` (L1228+). Injected via `agent/system_prompt.py`.
- Session transcript / search DB: root `hermes_state*.py` → `$HERMES_HOME/state.db` (FTS5; optional CJK tokenizer in `native/fts5_cjk/`).
- Plugin backends: `plugins/memory/` (Honcho, mem0, Hindsight, holographic, supermemory, OpenViking, RetainDB, Byterover) orchestrated by `agent/memory_manager.py` + `agent/memory_provider.py`.
- CLI: `hermes_cli/subcommands/memory.py`.

### Skill creation / storage

- Bundled source: `skills/` (seeded into `$HERMES_HOME/skills/` by `tools/skills_sync.py`).
- Optional official source: `optional-skills/` via `tools/skills_hub_official.py`.
- Runtime / user / agent-created: `$HERMES_HOME/skills/` (`tools/skills_tool.py` L60: "all skills live in ~/.hermes/skills/").
- Lifecycle / curator: `agent/curator.py`, `tools/skill_usage.py`, CLI `hermes_cli/subcommands/skills.py` / `hermes_cli/subcommands/curator.py`.
- Slash invocation: `agent/skill_commands.py`.
- Authoring contract: `skills/AGENTS.md` (frontmatter `platforms:` OS gate).

### Tool registry / tool-calling

- Registry: `tools/registry.py` (`registry.register()`, `handle_function_call()`).
- Discovery consumer: `model_tools.py` (`discover_builtin_tools()`).
- Toolset membership: `toolsets.py` (`TOOLSETS`, `_HERMES_CORE_TOOLS`).
- Inline agent tools (todo, memory): `agent/inline_tool_executors.py` + `agent/tool_executor.py`.
- Plugin tools: `plugins/plugin_loader.py` (`ctx.register_tool`).

### Subagent delegation

- `tools/delegate_tool.py` plus siblings `delegate_tool_child_run.py`, `delegate_tool_dispatch.py`, `delegate_tool_registry.py`, `tools/async_delegation.py`.
- TUI/Desktop snapshot RPCs: `tui_gateway/AGENTS.md` (`subagent.list`, `subagent.tail`).
- Tests/evals: `evals/subagent_process_handoff/`, `evals/delegation_group_schema/`.

### Cron / scheduled automation

- `cron/jobs.py`, `cron/scheduler.py`, `cron/scheduler_*.py`, `cron/occurrences.py`, `cron/executions.py`.
- Tool: cronjob toolset (see `toolsets.py` / `tools/` cronjob module).
- CLI: `hermes_cli/subcommands/cron.py`.
- Related durable work queue: kanban under `plugins/kanban/` + `tools/kanban_tools.py` (documented in `cron/AGENTS.md`).

### Core agent loop / orchestration

- Facade: `run_agent.py` (`AIAgent`).
- Init: `agent/agent_init.py::init_agent`.
- Turn loop: `agent/conversation_loop.py::run_conversation` plus `agent/turn_*.py` phases (`turn_api_call.py`, `turn_tool_round.py`, `turn_finalizer.py`, ...).
- Gateway turn runner: `gateway/run.py` and `gateway/run_*.py`.
- TUI/Desktop loop host: `tui_gateway/server.py`.

### Voice input handling (wake word, transcription, TTS)

- Wake word: `tools/wake_word.py`, engines in `tools/wake_word_engines.py`, bundled models in `tools/wakewords/`, extra `[wake]` in `pyproject.toml` L231-244 (`openwakeword`, `onnxruntime`, `sherpa-onnx`, `pvporcupine`, `sounddevice`). Docs: `website/docs/user-guide/features/wake-word.md`.
- Voice mode / STT: `tools/voice_mode.py`, `tools/voice_live.py`, `tools/voice_mode_transcript.py`, extra `[voice]` (`faster-whisper`, `sounddevice`, `numpy`). CLI mixin: `hermes_cli/cli_voice_mixin.py`, `hermes_cli/voice.py`. Gateway: `gateway/run_voice.py`. TUI RPC: `tui_gateway/methods_voice.py`. Desktop: `apps/desktop/src/lib/voice-*.ts`, composer hooks.
- TTS: `tools/tts_tool_providers.py` / related tts tools; extras `edge-tts`, `tts-premium` (ElevenLabs), `mistral`.
- Platform voice messages (Telegram/Discord/Matrix): gateway tests under `tests/gateway/test_*voice*` and `plugins/platforms/discord/voice_mixer.py`.

### Messaging platform gateways

- Gateway process: `gateway/run.py`.
- In-tree adapters (non-plugin): `gateway/platforms/` (api_server, signal, webhook, whatsapp_cloud, yuanbao, bluebubbles, ...).
- Plugin adapters: `plugins/platforms/` — telegram, discord, slack, whatsapp, matrix, teams, feishu, dingtalk, wecom, email, sms, homeassistant, google_chat, irc, line, mattermost, photon, simplex, ntfy, raft, a2a, buzz.
- Adding a platform: `gateway/platforms/ADDING_A_PLATFORM.md`.

### User modeling / relationship tracking

- Honcho dialectic provider: `plugins/memory/honcho/` (`dialectic.py`, `session.py`, `README.md` — "AI-native cross-session user modeling with multi-pass dialectic reasoning"). Docs: `website/docs/user-guide/features/honcho.md`. Extra: `[honcho]`.
- Built-in user profile file: `USER.md` via `tools/memory_tool.py` / `agent/learning_graph.py`.
- No separate "relationship graph" package name was found at the top two levels; Honcho + USER.md are the in-tree user-model surfaces. Deeper analysis is WINH02+.

### Model provider abstraction

- Registry ABC: `providers/base.py` (`ProviderProfile`), `providers/__init__.py` (`register_provider`, `get_provider_profile`, `list_providers`).
- Profile plugins: `plugins/model-providers/` (actual, ai-gateway, alibaba, anthropic, azure-foundry, bedrock, copilot, custom, deepseek, gemini, huggingface, minimax, nous, openai-codex, ollama-cloud, openrouter, vertex, xai, zai, ...).
- Auth / picker: `hermes_cli/auth.py`, `hermes_cli/models.py`, `hermes_cli/runtime_provider.py`, `hermes_cli/subcommands/model.py`.
- Call path: `agent/transports/chat_completions.py` (profile hooks), `agent/auxiliary_client.py`, `run_agent.py`.

### Platform-specific code (Windows vs Linux/macOS)

Primary Windows conditionals / shims (not exhaustive; `sys.platform == "win32"` appears widely):

- `hermes_cli/stdio.py::configure_windows_stdio` — UTF-8 console (CP 65001)
- `hermes_cli/win_pty_bridge.py::WinPtyBridge` — ConPTY for dashboard `/chat`
- `hermes_cli/web_server_chat.py` L26-33 — selects WinPtyBridge vs PtyBridge
- `tools/environments/local.py::_windows_bash_candidates`, `_find_bash` — Git Bash discovery
- `tools/environments/local_gitbash_probe.py` — bash.exe probe
- `tools/file_tools_paths.py::_anchor` L149-154 — `ntpath` on win32
- `tools/process_registry.py` — pywinpty vs ptyprocess
- `tools/memory_tool.py` L18-28 — `fcntl` vs `msvcrt`
- `tools/lazy_deps.py::_unsupported_feature_reason` L341-343 — Matrix blocked on Windows
- `pyproject.toml` L111-141 — `tzdata`, `pywinpty`, `pywin32` under `sys_platform == 'win32'`; `ptyprocess` on non-Windows
- `scripts/install.ps1`, `scripts/install.cmd`
- `scripts/check-windows-footguns.py` (CI)
- `docker-compose.windows.yml`
- Docs: `website/docs/user-guide/windows-native.md`, `windows-wsl-quickstart.md`
- macOS-only bundled skills: `skills/apple/*` (`platforms: [macos]` in e.g. `skills/apple/imessage/SKILL.md`)

### HTTP / WebSocket / RPC API surface (note location only)

A separate client application could talk to Hermes through several in-tree surfaces (analysis deferred):

1. **OpenAI-compatible HTTP API** — `gateway/platforms/api_server.py` (docstring: `/v1/chat/completions`, `/v1/responses`, `/v1/models`, `/v1/capabilities`, `/api/sessions`, `/v1/runs`, `/api/jobs`, `/health*`; default `http://localhost:8642/v1`). Multiplex prefix `/p/<profile>/`.
2. **Dashboard FastAPI + WebSocket** — `hermes_cli/web_server.py` + `hermes_cli/web_routers/` + `hermes_cli/web_server_chat.py` (`/api/pty` WebSocket). SPA in `web/`.
3. **TUI/Desktop JSON-RPC** — `tui_gateway/server.py` (stdio JSON-RPC; Desktop uses WebSocket via `apps/shared`). Contracts: `tui_gateway/contracts/`, generated `apps/shared/src/gateway-contract.generated.ts`.
4. **ACP** — `acp_adapter/server.py` (Agent Communication Protocol).
5. **MCP server** — `mcp_serve.py` (`hermes mcp serve` stdio).
6. **Messaging webhooks** — per-platform adapters under `gateway/platforms/` and `plugins/platforms/` (Telegram, Slack, webhook.py, etc.).

Look next (if a later prompt needs a surface not listed): `hermes_cli/web_server_*.py` siblings, `tui_gateway/methods_*.py`, `gateway/platforms/api_server_*.py`.
