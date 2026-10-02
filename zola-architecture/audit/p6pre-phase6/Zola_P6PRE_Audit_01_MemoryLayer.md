# P6PRE Audit 01 — Hermes Memory Layer (as Zola-Windows runs it)

**Audit:** P6PRE · **Pin:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`)  
**Live effective:** `memory.provider: ""` (default); built-in MEMORY.md/USER.md on; budgets 4400/4000 (profile).  
**Labels against:** C4, S14, P4, P5-D03–P5-D06.

---

## Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-01 | [MATCH] | — | `plugins/memory/__init__.py` L1–7, L92–106; `plugins/plugin_loader.py` L28–33 | A provider under `$HERMES_HOME/plugins/<name>/` loads without editing hermes-agent (confirms P5PRE AUD-11). |
| P6PRE-AUD-02 | [MATCH] | — | `agent/agent_init.py` L1247–1286; `agent/system_prompt.py` L460–485 | Built-in MEMORY.md/USER.md stay active beside an external provider; both can be disabled via `memory.memory_enabled` / `user_profile_enabled`. |
| P6PRE-AUD-03 | [MATCH] | — | `agent/turn_context.py` L81–94, L762–790; `agent/memory_manager.py` L266–280 | Prefetch enters the **user turn** via `<memory-context>` fence (`build_memory_context_block`); skipped on `is_trivial_prompt`. |
| P6PRE-AUD-04 | [GAP] | LOW | `agent/memory_manager.py` L32, L290–299; `agent/agent_init.py` L1275 | External prefetch timeout is hardcoded **8.0 s**; no `config.yaml` key. On expire: empty context + WARNING; stuck provider skipped until return. |
| P6PRE-AUD-05 | [MATCH] | — | `agent/inline_tool_executors.py` L114–133; `agent/memory_manager.py` L738–774 | Successful built-in `add`/`replace`/`remove` can be mirrored after file write via `notify_memory_tool_write` → `on_memory_write` (with `old_text` + provenance). |
| P6PRE-AUD-06 | [RISK] | MEDIUM | `agent/agent_init.py` L1267–1272; loss table Q9 | With `memory.provider: ""` there is **no** MemoryManager — mirror/prefetch/hooks are offline. Even with a provider, several write paths bypass notify (approve, journey, review fork, manual edit). |
| P6PRE-AUD-07 | [RISK] | MEDIUM | Q6 inventory; `agent/background_review.py`; `learning_mutations.py` | Multiple durable/memory-like writers exist; with defaults the primary fact path is the `memory` tool (+ optional background review). Duplicate-path risk rises if a provider also exposes write tools. |

---

## 1. Provider resolution and profile load

**Config:** `memory.provider` (default `""`) — `hermes_cli/config_defaults.py` L1215–1228.

**Init:** `agent/agent_init.py` L1267–1286 — empty → `_memory_manager = None`; non-empty → `load_memory_provider` → `add_provider` → `initialize_all`. One external provider only (`agent/memory_manager.py` L3–4).

**Discovery precedence** (first wins; bundled before user) — `plugins/memory/__init__.py` L1–7, L92–106:

1. Bundled `plugins/memory/<name>/`
2. **Profile** `$HERMES_HOME/plugins/<name>/` (`plugin_loader.user_plugins_dir` L28–33)
3. Project `./.hermes/plugins/<name>/` if `HERMES_ENABLE_PROJECT_PLUGINS`
4. Entry points `hermes_agent.memory_providers`

**Layout:** `$HERMES_HOME/plugins/<name>/__init__.py` (+ optional `plugin.yaml`, `cli.py`, …). Dir must mention `MemoryProvider` or `register_memory_provider` (L62–71). Example `plugin.yaml` (holographic): `name`, `version`, `description`, `hooks: [on_session_end]`.

**P6PRE-AUD-01 [MATCH]** with P5PRE AUD-11 / S42 note: profile provider without hermes-agent edits.

---

## 2. Built-in store beside external provider

Built-in load is independent of provider (`agent_init.py` L1247–1265). System prompt joins built-in blocks + external `system_prompt_block()` (`system_prompt.py` L460–485).

| Key | Effect |
|-----|--------|
| `memory.memory_enabled: false` | No MEMORY.md injection/writes |
| `memory.user_profile_enabled: false` | No USER.md |
| Both false | Built-in `memory` tool not registered (`tools/memory_tool.py` `check_memory_requirements` L222–234); external tools can still inject if toolset allows |

**P6PRE-AUD-02 [MATCH]** with C4 (files remain the live store unless both flags off) and S14 (provider can sit beside files).

---

## 3. Prefetch → model input

```266:280:agent/memory_manager.py
def build_memory_context_block(raw_context: str) -> str:
    ...
    return (
        "<memory-context>\n"
        "[System note: The following is recalled memory context, "
        "NOT new user input. Treat as authoritative reference data — "
        "this is the agent's persistent memory and should inform all responses.]\n\n"
        f"{clean}\n"
        "</memory-context>"
    )
```

- Prefetch at turn start: `turn_context.py` L762–790; stamped into user `api_content` L81–94.
- **Not** in the frozen system-prompt MEMORY/USER snapshot.
- Cache: system built-in block frozen at `load_from_disk`; prefetch changes **current user** bytes each substantive turn; historical `api_content` replayed as sent.
- Skipped: empty, `/…`, trivial greets (`memory_provider.py` L66–72; `turn_context.py` L781–782). Also skipped when `_memory_manager` is None (Zola live).

**P6PRE-AUD-03 [MATCH]** with S14 relevance-retrieval shape (when a provider is active).

---

## 4. Prefetch timeout and queue

| Item | Value |
|------|-------|
| Default | **8.0 s** (`_EXTERNAL_PREFETCH_TIMEOUT_S`, `memory_manager.py` L32) |
| Config key | **None** — `MemoryManager()` constructed with no override (`agent_init.py` L1275) |
| On expire | `""` for that provider; WARNING; stuck thread kept; later turns skip until return (L427–433) |
| `queue_prefetch_all` | After completed non-interrupted turn (`run_agent.py` L901–904), non-trivial only, background executor |
| Contract | `queue_prefetch` pre-warms; next `prefetch` returns cached (`memory_provider.py` L111–117) — provider must implement |

**P6PRE-AUD-04 [GAP]** — no profile knob for the 8 s bound.

---

## 5. `on_memory_write`

| Item | Evidence |
|------|----------|
| Actions | `add`, `replace`, `remove` (`memory_manager.py` L738, L765–766) |
| Metadata | `old_text` from op; provenance via `_build_memory_write_metadata` (`write_origin`, `session_id`, `tool_name`, …) L769–772 |
| Ordering | **After** successful file write (`inline_tool_executors.py` L114–133) |
| Sync | Synchronous on tool thread (`on_memory_write` → `_each_provider`) |
| Fail closed | Non-JSON / `success≠true` / `staged` → no notify (L741–760) |

Legacy providers without a `metadata` parameter get action/target/content only (`_provider_memory_write_metadata_mode` L712–718).

**P6PRE-AUD-05 [MATCH]** — contract supports single model-facing write path mirroring.

---

## 6. Durable / memory-like write inventory (Zola defaults)

| Path | Active? | What / where / when |
|------|---------|---------------------|
| Built-in `memory` tool | **Yes** | MEMORY.md / USER.md on model call |
| Background review | **Yes** (~every `nudge_interval` 10 turns) | May call `memory` / `skill_manage`; fork `skip_memory=True` → **no** notify |
| Curator | Optional scheduled | Skills, not MEMORY.md |
| insights / learning_graph | Read-ish | No auto MEMORY write |
| learning_mutations / journey | User-initiated | Direct file write — **bypasses** notify |
| title_generator | Yes | Session title only |
| Context compression | Yes | Transcript handoff; no MEMORY.md |
| Skill self-authoring | Yes | Skill trees |
| `/memory approve` | Only if `write_approval` (default false) | Apply path **no** notify |
| External provider tools / sync | **No** | Requires `memory.provider` |

**P6PRE-AUD-07 [RISK]** against “one authority / no duplicate execution paths” when a provider adds write tools beside the memory tool.

---

## 7. `agent_context`

Documented: `primary` / `subagent` / `cron` / `flush` (`memory_provider.py` L97–100).  
**Actually passed:** always `"primary"` (`agent_init.py` L1199–1204). Subagents use `skip_memory=True` (no provider). Cron uses `platform="cron"` with `agent_context` still `"primary"`.

Zola Windows `tui_gateway`: primary agent, typically `platform` tui/desktop resolution; with empty provider, no manager.

---

## 8. Threading

| Work | Thread |
|------|--------|
| External prefetch | `spawn_context_thread` + join(timeout) |
| sync / queue_prefetch / session boundary | Single-worker background executor + `ctx_bound` |
| memory tool + notify | Turn/tool thread |

Providers **must** use `spawn_context_thread` / `ctx_bound` (`memory_provider.py` L21–33) or workers land on the wrong profile.

---

## 9. Memory tool as sole model-facing write path

**Shape is possible** if:

1. Profile provider with `get_tool_schemas() → []` (or read-only tools)
2. `memory.provider` set; built-in flags left on
3. Provider implements `on_memory_write` for `add`/`replace`/`remove` (+ `old_text`)
4. Provider does not auto-extract / `sync_turn`-write facts

**Happy path:**

```
Brian states lasting fact → SOUL "What I remember" → model calls memory
  → MemoryStore file write (memory_tool_store)
  → notify_memory_tool_write (inline_tool_executors L126)
  → on_memory_write → provider store
  → end-of-turn queue_prefetch_all
  → next turn prefetch_all → user <memory-context>
```

**Loss points (not exhaustive):** empty provider (Zola today); failed/staged writes; `/memory approve` and journey bypass; review fork without manager; swallowed provider exceptions; prefetch timeout; trivial prompts skip recall; interrupted turns skip queue; provider `sync_turn`/`on_session_end` as second writers.

**P6PRE-AUD-06 [RISK]** — live profile has no manager; full fidelity needs closing bypasses.

---

## 10. Authority: files vs store

| Model | Host support |
|-------|----------------|
| Files SoT + store as derived index | **Matches** one-way notify bridge |
| Store SoT + files off | Supported (`memory_*_enabled: false`) |
| Store SoT + files still written | Dual-authority hazard |
| Provider write-back into MEMORY.md | No host path; fights frozen snapshot, drift guard, budgets |

For S14 “store becomes SoT and projects into MEMORY.md”: projection writer would be a **second writer** unless the memory tool stops owning those files.

---

## Lore labels

| Decision | Status |
|----------|--------|
| C4 | Built-in files still the live store with defaults; extension via provider is available |
| S14 | Pluggable layer + prefetch fence match the relevance-retrieval substrate |
| P4 | Local profile storage; cloud providers not activated |
| P5-D03–D06 | Still governed by SOUL + memory tool; provider text can compete (see Audit 02) |
