# WINH06 Phase 3 — Tool, Plugin & MCP Capability Acquisition

Hermes pin: `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.
Labels: `[MECHANISM]` / `[RISK]` / `[ABSENT]` / `[UNVERIFIED]`.
No Zola Document of Truth for this domain.

---

## 1. Can the agent add a tool / plugin / MCP server at runtime without a human editing config?

### WINH06-AUD-09 — `[MECHANISM]` — MEDIUM — `tools/setup_mcp_tool.py` L1–32, L20–72

Desktop-sourced sessions get `setup_mcp` (`desktop_ui` toolset). The tool does **not** write `mcp_servers` itself. It blocks on the gateway's clarify-style bridge: TUI emits `mcp.setup.request`, the desktop renderer runs catalog install / enable / OAuth, and answers `mcp.setup.respond` (module docstring L1–9). Actions: `install` / `enable` / `authorize` (L17). Schema text L70–72: "Never hand-edit mcp_servers config for them — always use this tool."

Authority on this path **is** a human consent card. That is a meaningful control, not an omission.

If `callback is None` (CLI / non-desktop), the tool errors and **instructs the model to use the terminal** (L29–32):

> `setup_mcp is only available in the Hermes desktop app. Use the terminal instead: \`hermes mcp install <name>\` …`

### WINH06-AUD-10 — `[RISK]` — HIGH — `tools/setup_mcp_tool.py` L8–9, L29–32; `hermes_cli/mcp_config.py` `cmd_mcp_add` L587+; `hermes_cli/subcommands/mcp.py` L74–76

The documented non-desktop path is the agent running `hermes mcp install <name>` or `hermes mcp add` via `terminal`. Those CLI commands write `mcp_servers` into `config.yaml` (`cmd_mcp_add` L587–617; catalog `install` in `mcp_config.py` L1041–1048). Searched `tools/approval_detection.py` for `hermes mcp` / `hermes config` / `hermes plugins`: **no matches**. `detect_hardline_command` (L174+) does not treat those CLIs as hardline.

So: desktop has a human card; terminal/CLI surfaces let the agent add an MCP by invoking the same operator CLI the human would type, without that card. A human *restart or `/reload-mcp`* may still be required to attach the tools to the live session (WINH06-AUD-16).

### WINH06-AUD-11 — `[MECHANISM]` — MEDIUM — `hermes_cli/plugins_cmd.py` `cmd_install` L683–696; `tui_gateway/methods_tools.py` `_plugins_install` L1407–1417; `hermes_cli/plugins_discovery.py` `gate_manifest` L173–218

Plugins are **not** registered by an agent tool. Install surfaces:

- CLI: `hermes plugins install` (`cmd_install`) — git clone from catalog name, Git URL, or `owner/repo`. Catalog hits pin a reviewed SHA; custom sources print "unreviewed."
- JSON-RPC: `plugins.manage` action `install` (`methods_tools.py` L1441–1447) calls `dashboard_install_plugin` (L1703+) — TUI / dashboard, not the model.
- Discovery dirs (`hermes_cli/plugins.py` L1–8): bundled `plugins/<name>/`, user `~/.hermes/plugins/<name>/`, optional project `./.hermes/plugins/` behind `HERMES_ENABLE_PROJECT_PLUGINS`, pip entry-points `hermes_agent.plugins`.

User plugins are **opt-in**: `gate_manifest` L213–218 skips anything not in `plugins.enabled` (unless bundled backend/platform special-cases). Enable/disable is `hermes plugins enable` or RPC `plugins.toggle` (`methods_tools.py` L1394–1404), which writes config.

Install-time scan: `tools/plugin_guard.py` L1–8 applies the skills_guard engine; `dangerous` is blocked and `--force` does not override. Capability consent (`hermes_cli/plugin_capabilities.py` L1–46) gates `tools.override`, LLM provider/model overrides, platform actions — only ids that already have an enforcing surface.

### WINH06-AUD-12 — `[ABSENT]` — MEDIUM — searched `tools/*_tool.py` for `plugin_manage` / `setup_plugin` / `install_plugin`

No agent tool registers a plugin. The agent can still `terminal` `hermes plugins install …` (same hardline gap as AUD-10). Dropping a `plugin.yaml` + `__init__.py` under `~/.hermes/plugins/` via `write_file` would be discovered on the next `discover_plugins` sweep, but `gate_manifest` still requires `plugins.enabled` — and that list lives in `config.yaml`, which `write_file` refuses (Phase 4). So directory-drop alone does not enable a plugin without a config change.

First-party (bundled) vs third-party: bundled backends auto-load (`gate_manifest` L205–208); user/catalog/git plugins need `plugins.enabled`. MCP third-party servers are config `mcp_servers` entries (stdio command or URL), not the plugin loader.

---

## 2. What authority gate sits in front of that path?

| Path | Gate | Same as skills `write_approval`? |
|---|---|---|
| `setup_mcp` (desktop) | Human consent card via gateway bridge | No — separate, stronger on this surface |
| `hermes mcp install/add` via terminal | None specific; ordinary terminal approval if the command matches a dangerous pattern (these CLIs do not) | No |
| `hermes plugins install` / `plugins.manage` | Human CLI prompt or TUI; `plugin_guard` scan; kill list; `plugins.enabled` opt-in; capability consent for declared caps | No |
| `skill_manage` (Phase 2) | `skills.write_approval` default False | n/a here |
| Lazy PyPI install (`tools/lazy_deps.py`) | `security.allow_lazy_installs` default **True** (`config_defaults.py` L1637–1640) | No |

MCP save/spawn has an additional **content** filter, not an approval prompt: `hermes_cli/mcp_security.py` `validate_mcp_server_entry` (shell interpreters, egress/exfil, persistence, June 2026 IOC substrings). Applied at save (`mcp_config`) and at spawn (`tools/mcp_tool_config.py` `_filter_suspicious_mcp_servers` L291–304). Narrow shape-check, not a human gate.

---

## 3. Isolation / sandboxing of newly-acquired capability

### WINH06-AUD-13 — `[RISK]` — HIGH — `hermes_cli/plugins.py` `PluginContext.register_tool` L460–502; `tools/mcp_tool_server_run.py`; `tools/plugin_guard.py` L3–4

Once registered:

- **Plugins** load in-process. `register_tool` writes into the global `tools.registry` (L480–491). Docstring of `plugin_guard.py` L3–4: "Plugins run in-process but are *expected* to read their own env keys, call provider APIs and spawn subprocesses." No process boundary, no extra permission scope, no resource limit specific to "just installed." Overriding a built-in tool requires `plugins.entries.<id>.allow_tool_override` (L465–478) — that is the only privilege split found.
- **MCP servers** run as long-lived stdio/HTTP tasks (`MCPServerRunMixin` in `mcp_tool_server_run.py`). That is a process boundary for stdio children, but they execute as the same OS user with whatever command the config specified (`npx`, a binary, a URL). No Hermes sandbox layer unique to newly added servers was found (searched `mcp_tool*.py` for cgroup/seccomp/docker wrapping of MCP children: none).
- **Lazy deps** (`tools/lazy_deps.py` `_allow_lazy_installs` L324–332) pip-install into the active venv on first use of an optional backend. Default allowed. That mutates the runtime's package set, then those imports run in-process.

Newly acquired capability runs with the same privileges as the rest of the agent.

---

## 4. Discoverability of what is currently installed

### WINH06-AUD-14 — `[ABSENT]` — MEDIUM — `tui_gateway/methods_tools.py` L232–235, L1388–1417; `tools/skills_tool.py`; `hermes_cli/mcp_config.py` `cmd_mcp_list`

Independent registries / commands:

| Kind | Operator surface | Agent surface |
|---|---|---|
| Tools (by toolset) | JSON-RPC `tools.list` (`methods_tools.py` L235) | Model sees `get_tool_definitions()` (`model_tools.py` L212) |
| Plugins | `plugins.list` / `hermes plugins list` | None dedicated; some tools tell the model to run `hermes plugins list` |
| MCP servers | `hermes mcp list`; session info `mcp_servers` (`tui_gateway/server.py` L2122–2125) | `setup_mcp` / terminal CLI |
| Skills | `hermes skills list`; agent `skills_list` | `skills_list` / `skill_view` |

No single command, endpoint, or file lists skills + tools + plugins + MCP together. The profile editor snapshot (`tui_gateway/contracts/profiles_vault_complete_foreign_subagents.py` L256) comes closest ("soul, model pin, skills, toolsets, MCP servers") but is a profile-editor payload, not a live capability inventory, and still omits the plugin registry as a first-class combined list.

An operator must check multiple independent registries.

---

## 5. Related acquisition vectors (not plugin/MCP install APIs)

### WINH06-AUD-15 — `[MECHANISM]` — MEDIUM — `tools/lazy_deps.py` L324–332; `config_defaults.py` L1637–1640

Optional backends (TTS, STT, vision extras, some platform SDKs) lazy-install PyPI packages when first used, unless `security.allow_lazy_installs: false`. Default is True. This is capability acquisition (new native code in the venv) without a human editing config, gated only by that boolean and whatever confirmation `_allow_lazy_installs` callers add per-feature.

### WINH06-AUD-16 — `[UNVERIFIED]` — LOW — `tui_gateway/methods_slash.py` `_mirror_reload_mcp` L320–322; `methods_tools.py` `reload.mcp` L272+

`/reload-mcp` reloads MCP servers from `config.yaml` and may invalidate the prompt cache (`approvals.mcp_reload_confirm` default True, L262–268). Whether a `hermes mcp install` run **from the agent's terminal tool in a live `hermes serve` session** automatically attaches new tools without `/reload-mcp` depends on runtime process layout (gateway vs CLI vs desktop). Searched for an automatic post-install reload hook in `setup_mcp_tool.py` and `mcp_config.py`: the CLI writes config; live attach is documented as `/reload-mcp`. Desktop `setup_mcp` REST flow may reload inside the renderer — that path was not executed in this static checkout.
