# Zola P8PRE Audit 01 — Plugin Tool Path

**Date:** 2026-10-07  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `7d2a1e71ca7cc5d12afa901738eca47ee8b5ecee`  
**Labels vs:** `S16`, `P6-D03`, `P6-D08`, `P6-D09`, `A9`

---

## 1. Registration

`PluginContext.register_tool` at `hermes_cli/plugins.py` L460–502:

```python
def register_tool(
    self, name: str, toolset: str, schema: dict, handler: Callable,
    check_fn: Callable | None = None, requires_env: list | None = None, is_async: bool = False,
    description: str = "", emoji: str = "", override: bool = False,
) -> Optional[PluginRegistration]:
```

A plugin may also register: approval transport, CLI commands, slash commands, context engine/reference, memory provider, dashboard auth, gateway platform, auxiliary tasks, redaction patterns, hooks, middleware, system prompt sections, skills, secret sources (`plugins.py` L434–1084 area).

One plugin may call `register_tool` repeatedly with different `name`/`toolset` values — no one-toolset-per-plugin limit. `zola_tools` registers one tool (`calculate` / toolset `zola_tools`) in `hermes-plugins/zola_tools/__init__.py` L140–149. Loader invokes `register(PluginContext(...))` in `plugins_loader.py` L310–317.

**LEAD-1: CONFIRMED** — same path, no hermes-agent edit required.

---

## 2. Enablement

| Step | Fact |
|------|------|
| Install | Profile `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_tools\` (mirrored from `hermes-plugins/zola_tools/`) |
| Plugin enable | `plugins.enabled: [zola_tools]` in live `config.yaml` |
| Toolset for TUI | Plugin toolsets default **on** via `_enabled_plugin_toolsets` (`hermes_cli/tools_config.py` L532–539); TUI loads via `_get_platform_tools(cfg, "cli", ...)` (`tui_gateway/server.py` L1854–1888). Agent platform string is `"tui"` (L1415–1419); config key is `"cli"`. |
| Cron | `_resolve_cron_enabled_toolsets` → `_get_platform_tools(cfg, "cron")` (`cron/scheduler.py` L416–438) |
| Background review | Inherits parent toolsets but **dispatch whitelist** (`agent/background_review.py` L1025–1065) excludes arbitrary plugin tools unless `auxiliary.background_review.extra_tools` |
| Subagents | Child ⊆ parent toolsets (`tools/delegate_tool.py` L202–240; `delegate_tool_toolsets.py` L68–114) |

A Workspace toolset can be enabled for `cli` (TUI) and omitted from `cron` after it is marked known for that platform (`known_plugin_toolsets`). Background review already blocks dispatch unless listed. Subagents can inherit if the parent has the toolset.

---

## 3. Handler contract

| Aspect | Fact |
|--------|------|
| Args | `args: dict` |
| `**kwargs` on model→handler path | `task_id`, `session_id`, and either `user_task` or (for `execute_code`) `enabled_tools` — `model_tools.py` L811–817. **Not** `platform`, `parent_session_id`, or approval callbacks. |
| Sync/async | Sync by default; `is_async=True` bridged (`registry.dispatch`) |
| Timeout | Sequential tool deadline in `tool_executor`; plugin hook timeout `plugins.hook_callback_timeout` (default 30s) |
| Result size | Default truncate/spill at `DEFAULT_RESULT_SIZE_CHARS = 100_000` (`tools/budget_config.py` L13); turn budget 200_000 (L14) |
| Raise | Caught → `tool_error` JSON string; agent continues |

---

## 4. Who is calling

`zola_memory.forget.is_brian_conversation` (`forget.py` L65–66, L252–254): platform in `{"tui"}` and empty `parent_session_id`. Set on the memory provider from agent kwargs (`provider.py` L101–103).

A **`register_tool` handler cannot read those facts from `**kwargs`** on the standard dispatch path. Workarounds (session→agent lookup, shared helper) are not first-class.

---

## 5. Schema visibility

`forget_memory` omits schemas via memory-provider `get_tool_schemas()` when not Brian (`provider.py` L160–167) — not available to ordinary `register_tool` plugins. Plugin mechanisms: `check_fn` (omit when false), `platform_toolsets` / `disabled_toolsets`, `pre_tool_call` block (schema still visible).

---

## 6. Hooks as defense in depth

`pre_tool_call` can return `{"action": "block", "message": "..."}` (`plugins.py` L1853–1882). Hooks receive full `args` — for `terminal`, that includes `command`. A Zola hook could pattern-match token paths or `googleapis.com` hosts. Bypass: other tools (`execute_code`, file write + run), MCP, child agents, or any path that never goes through `handle_function_call`. Fact: defense-in-depth, not airtight. Timed-out `pre_tool_call` fails closed (L1684–1687).

---

## 7. Logging

| Location | Holds |
|----------|--------|
| `$HERMES_HOME/logs/zola_tools.log` | Metadata only (ok/error/lengths/ms) — never expression/result |
| `agent.log` | Tool name + duration + char count (full result only if verbose DEBUG) |
| `state.db` | Full tool args (assistant tool_calls) and tool result content |
| Trajectory (if enabled) | Args + results |
| Client `tool-events.log` | Risk metadata only (`name`, `risk`) — not args/results |
| Live wire `tool.start`/`tool.complete` | Args + result to client |

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-01 | [MATCH] | — | `zola_tools` proves `plugin.yaml` + `register_tool` path with no hermes-agent edit (`S16`, `P6-D08`). |
| P8PRE-AUD-02 | [MATCH] | — | Live enablement matches P6-CALC: `plugins.enabled` + default-on plugin toolset for `cli`. |
| P8PRE-AUD-03 | [GAP] | MEDIUM | Tool handlers lack `platform` / `parent_session_id` in kwargs; a plugin can still record them from `pre_llm_call` (sees both) into session-keyed state for handlers (see Audit_02 §9b). |
| P8PRE-AUD-04 | [RISK] | MEDIUM | `state.db` and live tool events persist full tool args/results; plugin metadata-only logging cannot prevent that. |
| P8PRE-AUD-05 | [MATCH] | — | `pre_tool_call` can block and sees terminal `command` (P6-D09 guard precedent). |
| P8PRE-AUD-06 | [GAP] | LOW | `PluginContext.register_tool` does not expose `max_result_size_chars`; Workspace tools inherit 100k default. |

## LEAD-1

**Confirmed** (P8PRE-AUD-01).
