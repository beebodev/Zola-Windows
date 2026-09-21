# WINH04 Audit 01 — Memory Storage & Ownership Mapping

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola lenses: `Zola Memory Hierarchy Architecture.md` (layers 0–6, authority order, promotion) and `Zola_Architecture_Memory_Agency.md` (write pipeline, salience, consolidation). The Windows/Hermes track **supersedes** two agency principles — facts belonging to entities rather than users, and “no agent writes memory directly” — so those absences are **not** labeled `[GAP]`/`[RISK]` here. They are recorded as factual context.

Related later docs: Privacy/retention (`Zola_WINH04_Audit_02_PrivacyRetentionAccess.md`); hierarchy reconciliation (`Zola_WINH04_Audit_04_HierarchyReconciliation.md`).

---

## 1. Hermes memory tiers mapped to Zola’s hierarchy

Hermes does not implement Zola’s seven-layer model. It ships a **built-in two-file prompt snapshot**, a **session transcript database**, and **at most one optional external provider**. Mapping is analogical, not structural.

### 1.1 Built-in curated files — `$HERMES_HOME/memories/`

Mechanism: `tools/memory_tool.py` L1–4, L38–40 (`get_memory_dir` → `get_hermes_home() / "memories"`). Store: `tools/memory_tool_store.py` `MemoryStore`. Targets:

| Hermes target | File | Config | Char budget (default) |
|---|---|---|---|
| `memory` | `MEMORY.md` | `memory.memory_enabled` | `memory.memory_char_limit` = 2200 (`hermes_cli/config_defaults.py` L1215–1223) |
| `user` | `USER.md` | `memory.user_profile_enabled` | `memory.user_char_limit` = 1375 |

Entries are `§`-delimited (`ENTRY_DELIMITER` in `memory_tool_store.py` L23). Both files enter the system prompt as a **frozen snapshot at session start**; mid-session writes hit disk but do not refresh the prompt (`memory_tool.py` L2–4).

**Zola mapping:** this is closest to a **collapsed Layer 4 + Layer 5** dump injected as if it were Layer 0 context.

- `USER.md` is a single “who the user is” profile (`MEMORY_BLOCK_HEADERS["user"]` L20–21). Zola Layer 5 requires **context-scoped** behavioral preferences (`Zola Memory Hierarchy Architecture.md` §1 Layer 5: “must not flatten the user into a single universal personality profile”). USER.md has no context key.
- `MEMORY.md` is “your personal notes” — agent-curated durable prose. Zola Layer 4 is structured canonical facts with entity relationships. MEMORY.md has no schema beyond a string list and a char cap.
- There is **no** Layer 3 episodic episode object (topic/themes/importance/recall-triggers/summary). There is **no** Layer 6 reflective consolidation product distinct from the same two files.

**Label:** `[PARTIAL]` — durable prompt-memory exists; it is not typed into Zola layers. Finding `WINH04-AUD-01`.

### 1.2 Session transcript — `state.db`

Mechanism: `hermes_state.py` / `hermes_state_sessions.py` (WINH03 session durability). Full turn history is persisted. Compaction stubs point the model at `session_search` (`agent/context_compressor.py` L824, L834). `session_search` tool: `tools/session_search_tool.py`, inline dispatch `agent/inline_tool_executors.py` L96–103.

`conversation_compression.py` L3265 calls `agent.commit_memory_session(messages)` on compression — that is a **provider hook**, not a promotion into MEMORY.md.

**Zola mapping:**

- The in-flight message list ≈ **Layer 0 / Layer 1** (current + recent turns).
- Durable `state.db` transcript ≈ a **raw Layer 2 log**, not Zola Session Memory (which wants topic summary, active goals, paused branches, return anchors — Hierarchy §1 Layer 2).
- Searchable past sessions are **raw transcripts**, not Layer 3 episodes. Hierarchy Layer 3 is explicit: “summarized, searchable episodes with metadata — **not raw transcripts**.”

**Label:** `[PARTIAL]` for Layers 0–2 working context; `[GAP]` for Layer 3 as specified. See Phase 5.

### 1.3 Plugin backends (one at a time)

`agent/memory_provider.py` L1–4: plugins under `plugins/memory/<name>/`, activated by `memory.provider`; **only one external provider**. Built-in MEMORY.md/USER.md **stays on** (`hermes_cli/subcommands/memory.py` L16–18).

Lifecycle (`memory_provider.py` L4): `initialize` → `system_prompt_block` / `prefetch` / `sync_turn` per turn → tool dispatch → `shutdown`, plus optional `on_*` hooks. `MemoryManager` (`agent/memory_manager.py`) owns the loop.

Three structurally distinct backends examined:

| Backend | Store | Distinct structure |
|---|---|---|
| **Built-in file** (always on) | `$HERMES_HOME/memories/MEMORY.md`, `USER.md` | Bounded `§` entries, char budgets, frozen prompt snapshot |
| **Holographic** (`plugins/memory/holographic/`) | Local SQLite `$HERMES_HOME/memory_store.db` (`store.py` L100–103) | `facts` + `entities` + `fact_entities`; `trust_score`; FTS5; optional HRR vectors; `temporal_decay_half_life` default **0** (`__init__.py` L4, L139) |
| **Honcho** (`plugins/memory/honcho/`) | Cloud Honcho workspace | User/AI **peers**, dialectic observations, identity mapping for gateway users (`README.md` Identity Mapping) |
| **Hindsight** (`plugins/memory/hindsight/`) | Cloud API, local embedded, or local HTTP | Knowledge graph + entity resolution (`README.md` L1–3) |

**Zola mapping:** holographic facts/entities resemble a **local Layer 4 graph** but only when `memory.provider = holographic`. Honcho peers are **user/AI identity modeling**, not a world-graph of people/places/things. Hindsight is an external graph. None of these is the default (`memory.provider` default `""` at `config_defaults.py` L1228).

**Label:** optional plugin ≈ `[PARTIAL]` Layer 4 **if enabled**; default Hermes has none of that graph.

### 1.4 Skills (not fact-memory)

`$HERMES_HOME/skills/` is procedural memory (SKILL.md packages). Confirmed separate in Phase 4 (`WINH04-AUD-08`). Zola Hierarchy does not treat skills as a numbered layer; Memory Agency’s “procedural” analog is closest to Layer 6-style lessons, but Hermes skills are a **different store**, not a promotion from facts.

---

## 2. Scope besides “the one configured user” (factual — not a finding)

**Default built-in store:** profile-scoped via `HERMES_HOME` (`memory_tool.py` L38–40). Two files, one user profile, no entity objects. Entries are opaque strings. There is no stored type for “a specific person, place, or thing distinct from the user.”

**Holographic (optional plugin):** `entities` table (`store.py` L25–31: `entity_id`, `name`, `entity_type`, `aliases`) linked through `fact_entities`. Facts can attach to named entities. This is the only examined **local** mechanism that resembles Zola’s entity-as-object. It is **not** default.

**Honcho (optional plugin):** `peerName` / `aiPeer` and gateway runtime-ID → peer mapping (`honcho/README.md` Identity Mapping). Peers are **users and the AI**, including multi-user gateway collapse/alias. That is multi-user identity, not a world graph of the user’s wife/car/shop as first-class memory objects.

**Hindsight (optional plugin):** vendor knowledge graph with entity resolution — **[UNVERIFIED]** as to whether those entities are Zola-shaped people/places/things vs document chunks; not inspected beyond README.

**Superseded principle:** absence of entity-scoping on the default path is **not** `WINH04-AUD-*`. It is context for Phase 5 and WINH00: default Hermes memory is **user/profile-scoped files**, not an entity graph.

---

## 3. Who can trigger a memory write

### 3.1 Primary path — agent tool `memory`

`tools/memory_tool.py` `memory_tool()` L172–205:

1. Resolve `MemoryStore` (missing store → tool error L179).
2. Optional `operations` batch, else `add` / `replace` / `remove`.
3. `_background_delete_gate` — background review **must not** `replace`/`remove` unattended (L148–169 stages or denies).
4. `_apply_write_gate` → `tools/write_approval.py` `evaluate_gate(MEMORY)` (inline prompt or stage; default **off**).
5. `MemoryStore.add` / `replace` / `remove` / `apply_batch` (`memory_tool_store.py` L237–274) → `_mutate` → `atomic_write_text` (L422).

After a successful (non-staged) write, `MemoryManager.notify_memory_tool_write` (`memory_manager.py` L751+) **mirrors** `add`/`replace`/`remove` to the external provider (`_MIRRORED_MEMORY_ACTIONS` L738; fail-closed on non-JSON / `staged` L741–749). `on_memory_write` L720–734 skips the builtin provider (it is the source).

This is the path the Windows track **intentionally** gives Hermes: the core agent loop writes memory. Not a finding against the superseded “no agent writes” rule.

### 3.2 Parallel path — provider `sync_turn` / session hooks (not `memory` tool)

`MemoryManager` runs `sync_turn` **off the conversation thread** because providers may block for minutes (`memory_manager.py` L485–503). Providers also get prefetch, session-end, and compression `commit_memory_session` (`conversation_compression.py` L3265).

Honcho’s design is automatic observation of user/AI turns into the cloud workspace (`honcho/README.md` observation / `SessionPeerConfig`). Hindsight similarly extracts into its bank. Holographic can `auto_extract` (default **false**, `__init__.py` L4).

These writes **do** go through the agent process (MemoryManager is inside `run_conversation`), but they **do not** go through `memory_tool` / `MemoryStore` / char budgets / threat scan / write_approval.

**Label:** `[RISK]` — a second write authority for durable facts. Finding `WINH04-AUD-02`. This is **not** the superseded “agent must not write”; it is “one authority per responsibility” against **plugin auto-extract bypassing the gated built-in store**.

### 3.3 Subagents

Holographic `MemoryStore` comment (`store.py` L92–95): main agent + every `delegate_task` subagent share one SQLite connection. Subagents that receive memory tools write the **same** DB. Still inside the agent tool dispatcher — not an out-of-process writer.

### 3.4 CLI / human

- `hermes memory reset` (`hermes_cli/main_agent_cmds.py` `_cmd_memory_reset` L21–56): unlinks `MEMORY.md` and/or `USER.md` after typing `yes`. Wipe, not a fact write.
- `hermes memory setup|status|off`: provider config only (`subcommands/memory.py`).
- Manual/OS edit of the markdown files: `MemoryStore` **drift guard** refuses a later tool write that would not round-trip (`memory_tool_store.py` `_drift_error` L36–40). That is integrity-adjacent, not an access-control boundary.

### 3.5 Plugins writing *without* the agent process

No examined backend opens a daemon that writes Hermes memory while the agent is not running. Cloud providers persist **on their side** after `sync_turn` during a live session. MCP messaging (`mcp_serve.py`) does **not** expose MEMORY.md (WINH02-AUD-06; `hermes_tools_mcp_server.py` L40 explicitly omits `memory`).

**Not a `[RISK]` of “plugin writes with the agent fully out of the loop”** on evidence in this tag. The live-session `sync_turn` bypass remains `WINH04-AUD-02`.

---

## 4. Write-classification vs Memory Agency (factual)

`Zola_Architecture_Memory_Agency.md` Memory Write Pipeline requires source, scope, authority, freshness, and a Durable Write Authority decision before a fact lands. Hermes `memory_tool` writes a **string**. Optional `write_approval` (`config_defaults.py` L1221 `memory.write_approval: False`) is a **human delay**, not DWA classification. No salience scorer, no visibility scope, no promotion from session → canonical.

That gap is labeled in Phase 3/5 (`WINH04-AUD-11`), not as a restatement of the superseded agency exception.

---

## Context for Phase 5 (not findings)

- Default Hermes = two prompt files + raw `state.db` + optional one plugin.
- Entity objects exist only in optional plugins (holographic local; Honcho peers; Hindsight graph).
- Hermes owning memory R/W is accepted. Dual write paths (tool vs `sync_turn`) are not covered by that exception.
