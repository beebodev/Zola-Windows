# WINH04 Audit 04 — Memory Hierarchy Reconciliation

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source of structure: `Zola Memory Hierarchy Architecture.md` (real layers 0–6 plus authority, read/write, promotion, decay, consolidation, topic stack, weighting, injection). Perception-only sensor/event-bus content is out of series scope; platform-agnostic rule from `Zola_Architecture_Perception_Memory.md` is included once: **observations are not facts** and must earn promotion.

Hermes mapping from `Zola_WINH04_Audit_01_StorageOwnership.md`. Entity-vs-user ownership is **not** scored (superseded). Everything else is.

---

## Layer 0 — Immediate Turn Context

**Zola:** current utterance, system state, tool results, response contract; expires after the response; must not write durable memory without write authority (`Hierarchy` §1 Layer 0).

**Hermes:** in-flight `messages` in `run_conversation` / JSON-RPC turn (WINH03 request trace). Tool results live in the same list. Frozen MEMORY.md snapshot is **also** in the system prompt — that is Layer 4/5 material injected as if it were Layer 0 (injection rules conflict; see Injection below).

**Score:** `[PARTIAL]` — working turn context exists; durable memory is mixed into the same prompt rather than gated by DWA. Mechanism: conversation loop + `memory_tool.py` L2–4 frozen snapshot.

---

## Layer 1 — Short-Term Conversational Memory

**Zola:** recent turn window; active entities/topic/subtopic; open loops; emotional tone; task state; volatile; decays unless promoted (`Hierarchy` §1 Layer 1).

**Hermes:** the recent messages still in the model context window. `todo_list` tool is a task-state sidecar (`turn_tool_round.py` housekeeping tools). No first-class “active entity / open loop / emotional tone” objects. Compaction elides old turns with `session_search` recovery pointers (`context_compressor.py` L824–834) — that **drops** Layer 1 rather than promoting it.

**Score:** `[PARTIAL]` — message window + todos. Missing structured Layer 1 fields. Mechanism: in-memory transcript; `tools` todo; compressor.

---

## Layer 2 — Session Memory

**Zola:** session topic summary, active goals, decisions, paused branches, return anchors; may survive interruption; **must not automatically become permanent** (`Hierarchy` §1 Layer 2). Session boundaries themselves live in a different doc (out of this prompt except as content definition).

**Hermes:** `state.db` holds the **full transcript** (WINH03 durability). That survives crash/resume. It is not a session **summary object**. Topic stack / return anchors: **absent** (`Hierarchy` §8).

Honcho session summaries (plugin README) are a vendor Layer-2 analog **if** Honcho is enabled.

**Score:** `[PARTIAL]` — durable session log, not Session Memory as specified. Mechanism: `hermes_state_sessions.py` / `state.db`. `[GAP]` for topic stack / return anchors (`WINH04-AUD-01` covers the collapsed-tier problem; topic stack called out here as absence).

---

## Layer 3 — Episodic Memory

**Zola:** summarized searchable **episodes with metadata** (topic, themes, importance, recall triggers, summary) — **not raw transcripts** (`Hierarchy` §1 Layer 3). Privacy Plan: episodic indefinite with decay; user-deletable at record level.

**Hermes:** `session_search` over past session text. Compression may produce auxiliary summaries for the **current** context, not a durable episode store. No episode schema.

Honcho/Hindsight may store narrative conclusions — optional, vendor-shaped, not default.

**Score:** `[GAP]` — no episode objects on the default path. `session_search` is transcript retrieval, which Hierarchy explicitly rejects as the Layer 3 form.

---

## Layer 4 — Structured Canonical Memory

**Zola:** durable facts and relationships; highest factual authority; protected by Durable Write Authority; weaker layers must not overwrite it (`Hierarchy` §1 Layer 4, §2, §4 DWA).

**Hermes default:** `MEMORY.md` `§` strings + `USER.md` profile. No relationship graph, no fact IDs, no DWA. Char budget is the only protection against growth.

**Hermes optional:** holographic `facts` + `entities` + `trust_score` (`plugins/memory/holographic/store.py` L12–37); Hindsight knowledge graph; Honcho peer cards.

**Score:** `[PARTIAL]` default (unstructured notes approximating canonical dump); `[PARTIAL]` holographic **if enabled**. `[GAP]` for DWA and “no weaker layer overwrites” (`WINH04-AUD-11`). Plugin `sync_turn` can write a parallel store (`WINH04-AUD-02`).

---

## Layer 5 — Behavioral and Preference Memory

**Zola:** **context-scoped** interaction preferences; must not flatten the user into one personality (`Hierarchy` §1 Layer 5).

**Hermes:** `USER.md` is one block titled “USER PROFILE (who the user is)” (`memory_tool_store.py` L20–21). No context key. Honcho “behavior patterns” per AI peer (README) are optional and still not Zola context-scopes (shop vs architecture).

**Score:** `[PARTIAL]` — a preference/profile file exists; it is globally flattened. Mechanism: USER.md via `memory` tool target `user`.

---

## Layer 6 — Reflective and Consolidated Memory

**Zola:** lessons/patterns from a **consolidation phase**, not casual capture; compact; must never override direct instructions (`Hierarchy` §1 Layer 6, §7 Consolidation).

**Hermes:** the same MEMORY.md the model edits when nudged (`memory.nudge_interval` default 10, `config_defaults.py` L1225). Background review can **add** (not unattended-delete). That is agent journaling, not a separate consolidator with defined inputs/outputs (Hierarchy §7: consolidation inputs/outputs).

Skills (`created_by: agent`) are procedural lessons in another store — closest **product** analog to “earned capability,” not Layer 6 fact-memory.

**Score:** `[GAP]` as a distinct memory layer. Nudge + MEMORY.md is casual capture into Layer 4-ish notes.

---

## Memory authority order (`Hierarchy` §2)

Zola order (high to low, abbreviated): user-stated / current turn / … / Layer 4 canonical / Layer 2 session / Layer 3 episodic / Layer 5 behavioral / Layer 6 reflective.

**Hermes:** no ranked recall pipeline. Frozen MEMORY.md+USER.md is always in the prompt (high injection, not high *authority with conflict rules*). Session search is on-demand. Plugins inject `system_prompt_block` / prefetch (`memory_provider.py` L4). `MemoryManager.sanitize_context` strips fence spoofing (`memory_manager.py` L171–175) — injection hygiene, not authority order.

**Score:** `[GAP]` `WINH04-AUD-11` (shared with DWA / write metadata).

---

## Read path / injection (`Hierarchy` §3, §10)

Zola: evaluate by relevance, authority, freshness, scope; do not dump the world model; good injection is selective.

**Hermes:** dump the **entire** bounded MEMORY.md+USER.md into the system prompt every session (`memory_tool.py` L2–4). Char limits (2200/1375) are the only selectivity. Plugin prefetch may add more.

**Score:** `[PARTIAL]` — bounded dump, not criterion-based injection. Conflicts with §10 “Bad Injection.”

---

## Write classification & DWA (`Hierarchy` §4; Agency write pipeline)

Zola: classify writes; Durable Write Authority for canonical; weak memory must not clobber strong.

**Hermes:** `memory_tool` add/replace/remove strings; optional human `write_approval` (default off). No classifier. No source/scope/authority/freshness metadata on entries.

**Score:** `[GAP]` `WINH04-AUD-11`.

---

## Promotion rules (`Hierarchy` §5)

Short-term → session → episodic → reflective; any layer → canonical only via DWA.

**Hermes:** no promotion state machine. Compression **elides** (with search pointer); it does not promote. `commit_memory_session` notifies plugins. Model may copy a fact into MEMORY.md if it chooses.

**Score:** `[GAP]` `WINH04-AUD-01` / `WINH04-AUD-11`.

---

## Decay rules (`Hierarchy` §6)

Per-layer decay (Layer 0 immediate; Layer 4 slow; etc.). Privacy Plan adds **deletion** at window end.

**Hermes builtin:** no time decay. Holographic retrieval half-life default 0 (`WINH04-AUD-13`). Char pressure forces **model-driven** delete/replace, which can drop high-authority facts to make room — opposite of Layer 4 protection.

**Score:** `[GAP]` default; `[PARTIAL]` holographic scores only.

---

## Consolidation phase (`Hierarchy` §7)

**Hermes:** memory nudge + optional background review add; curator is **skills**, not facts. No consolidation job with Hierarchy’s inputs/outputs.

**Score:** `[GAP]`.

---

## Topic stack (`Hierarchy` §8)

**Hermes:** none found (no return-anchor stack). Compaction/session_search is not a stack.

**Score:** `[GAP]` (no separate finding ID; rolled into `WINH04-AUD-01` as missing Layer 2 structure).

---

## Emotional / importance weighting (`Hierarchy` §9)

**Hermes builtin:** none. Holographic `trust_score` / `helpful_count` (`store.py` L17–19, `record_feedback` L202) is retrieval trust, not emotional importance.

**Score:** `[GAP]` default; `[PARTIAL]` holographic trust if enabled.

---

## Perception-agnostic formation (`Perception Memory` core)

**Zola (in-scope extract):** observations are not facts; they carry confidence + timestamp; they must earn promotion through layers or they pollute long-term truth (`Zola_Architecture_Perception_Memory.md` Vision + Core Philosophy). Sensor/event-bus machinery is out of series scope.

**Hermes:** the `memory` tool will persist whatever string the model writes (after threat scan + char budget). No observation-vs-fact type, no confidence, no promotion gate. Frozen prompt then treats that string as durable truth.

**Score:** `[GAP]` against “observations are not facts” / earned promotion. Same structural hole as DWA (`WINH04-AUD-11`). Not a perception-stack finding.

---

## Entity objects (factual, not scored)

Default: none. Holographic `entities` table: yes, optional. Honcho peers: user/AI identity, not world graph. See Audit 01 §2.

---

## Compact scorecard

| Zola concept | Hermes default | Optional plugin | Label |
|---|---|---|---|
| Layer 0 turn context | In-flight messages | — | [PARTIAL] |
| Layer 1 short-term | Context window + todos | — | [PARTIAL] |
| Layer 2 session memory | Raw `state.db` transcript | Honcho session summaries | [PARTIAL] / [GAP] structured fields |
| Layer 3 episodic | `session_search` on transcripts | Honcho/Hindsight narrative | [GAP] |
| Layer 4 canonical | MEMORY.md strings | Holographic/Hindsight graph | [PARTIAL] |
| Layer 5 behavioral | USER.md flat profile | Honcho behavior patterns | [PARTIAL] |
| Layer 6 reflective | Same MEMORY.md | — | [GAP] |
| Authority order | None | — | [GAP] |
| DWA / write class | None (`write_approval` is human delay) | — | [GAP] |
| Promotion | None | — | [GAP] |
| Time decay / retention delete | None | Holographic score decay | [GAP] / [PARTIAL] |
| Topic stack | None | — | [GAP] |
| Selective injection | Full file dump (char-capped) | Provider prefetch | [PARTIAL] |
| Observation≠fact | None | — | [GAP] |
