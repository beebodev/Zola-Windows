# Zola P8PRE Audit 09 — Harness and Live Probes

**Date:** 2026-10-07 (F4 H-1 re-run included)  
**Scratch:** `C:\Users\test\Dev\zola-spikes\p8pre\`  
**Interpreter:** `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`  
**Throwaway `HERMES_HOME`:** `...\p8pre\h1_home`

---

## H-1 — Stub plugin registration (F4 re-run)

**Entrypoint (same as serve):** `hermes_cli.plugins.discover_plugins(force=True)` → `get_plugin_manager().discover_and_load` → `plugins_loader` `register_fn(PluginContext(...))` (L310–317).

| Check | Result |
|-------|--------|
| Discovery | `p8pre_stub` loaded, `enabled: true` |
| Registry | `stub_read` / `stub_send` **present**, toolset `p8pre_stub` |
| Schemas (`registry.get_definitions({'stub_read','stub_send'})`) | See below |
| `cli` toolsets (TUI config key) | Includes `p8pre_stub` **by default** |
| `cron` toolsets | Includes `p8pre_stub` **by default** |
| `tui` key | `hermes-tui` + `p8pre_stub` |

**Schemas the model would see (stub tools):**

```json
[
  {"type":"function","function":{"name":"stub_read","description":"P8PRE stub read","parameters":{"type":"object","properties":{}}}},
  {"type":"function","function":{"name":"stub_send","description":"P8PRE stub send with approval","parameters":{"type":"object","properties":{"reason":{"type":"string"}}}}}
]
```

**Cron visibility:** Confirmed with registry + `_get_platform_tools(cfg, "cron")` containing `p8pre_stub`. Mechanism (`tools_config._enabled_plugin_toolsets`): plugin toolsets are on by default unless in `_DEFAULT_OFF_TOOLSETS` or **known** for that platform (`known_plugin_toolsets.<platform>`) and **absent** from the saved `platform_toolsets.<platform>` list.

**Config to remove from cron only:**

1. Ensure `known_plugin_toolsets.cron` includes `p8pre_stub` (written on save when Hermes knows the toolset), **and**
2. Omit `p8pre_stub` from `platform_toolsets.cron`.

Alternatively: `agent.disabled_toolsets: [p8pre_stub]` (all platforms).

**Background review:** Dispatch whitelist does not include arbitrary plugin tools unless `auxiliary.background_review.extra_tools` lists them (Audit_01).

**Subagents:** Child ⊆ parent toolsets; if parent has `p8pre_stub` and child inherits, subagent can get it (`delegate_tool_toolsets.py`).

Raw: `results/h1_rerun.json`.

---

## H-2 — Gate outcomes

Unchanged table: `off` / YOLO(import-time) open; manual/smart no-human closed. Fake callbacks did not grant in non-interactive harness.

---

## H-3 — Detector table (F6 expanded)

| Command shape | Flagged? | Pattern |
|---------------|----------|---------|
| `python -c` … Gmail | Yes | `-e/-c` flag |
| `curl` POST gmail | No | — |
| `Invoke-RestMethod` | No | — |
| Workspace skill script | No | — |
| `python <file>.py` | **No** | — |
| `powershell -File` | Yes | `-e/-c` flag |
| `python -m` | No | — |
| `execute_code` | N/A shell | Own `check_execute_code_guard`; toolset `code_execution` live |

---

## H-4 / H-5 / H-6

Unchanged (see prior probe results under scratch `results/`).

---

## L-1

**Skipped** — logs sufficed.

---

## Pre-synthesis re-hash

| File | Match Phase 1? |
|------|----------------|
| config.yaml / SOUL.md / plugins/* / MEMORY.md / USER.md | **yes** |
| .env | MISSING both times |
| CredMan probe | gone |

**Not BLOCKED.**
