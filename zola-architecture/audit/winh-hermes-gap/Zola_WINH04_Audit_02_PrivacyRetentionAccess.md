# WINH04 Audit 02 — Privacy, Retention, Deletion, Sensitivity, Access, Integrity

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Requirements extracted **first** from `Zola_Architecture_Memory_Ethics_and_Privacy.md` and `Zola Privacy and Data Ownership Plan.md` (abstract rules only — Android/sensor/camera mechanisms skipped). Hermes checked second.

The memory-agency exception does **not** cover this document.

---

## A. Requirement inventory (Zola docs)

### A.1 Ethics — `Zola_Architecture_Memory_Ethics_and_Privacy.md`

| ID | Requirement | Doc location |
|---|---|---|
| E-SCOPE | Every memory write **must** assign a visibility scope at write time; missing scope is an architecture violation | Memory Visibility Scopes |
| E-TAX | Scopes: `PRIVATE_TO_USER`, `PRIVATE_TO_ZOLA`, `HOUSEHOLD_OK`, `PUBLIC_OK`, plus more-restrictive output rules (`NEVER_SPEAK_ALOUD` in later sections) | Scope Taxonomy |
| E-SACRED | Hardcoded sacred categories (health/medical, financial stress, legal, relationship conflict, grief, abuse/trauma, addiction, workplace HR, security credentials) get **minimum** `PRIVATE_TO_USER`; never proactive | Sacred Memory Classes |
| E-USER-SACRED | User may designate any fact `userDesignatedSacred: true`; persists; Zola does not auto-remove | User-Designated Sacred Facts |
| E-R2 | Sacred facts never enter output unless user-initiated | Sacred Memory Governance R2 |
| E-AGE | Age thresholds for elevated justification (sacred 30d, PRIVATE_TO_USER 60d, emotional 14d, PRIVATE_TO_ZOLA never surfaced) | Age thresholds table |
| E-CTX | Context isolation: work vs home vs shop — facts appropriate in one context are not automatically appropriate in another | Context Contamination Prevention |
| E-COLLECT | Privacy at collection, write, retrieval, **and** output layers (paired with Privacy Plan core philosophy) | Ethics principles + Privacy Plan Core Philosophy |

### A.2 Privacy Plan — `Zola Privacy and Data Ownership Plan.md` (abstract only)

Skipped as Android/perception-specific: facial recognition, cameras, wearables, environmental activity, household sensors, monitoring-control UI for zones. Those sit in the 2026-09-21 Environmental Awareness deferral.

| ID | Requirement | Doc location |
|---|---|---|
| P-CAT | Every held category has purpose, retention window, deletion path, consent tier; no purpose → not collected | §1 Important Principle L135 |
| P-CONSENT | Highest-sensitivity categories need explicit separate consent, **disabled by default** | §2 / Tier 1 L73, L151 |
| P-RET | Automatic retention windows from last meaningful update; must not persist past window without logged user extension | §3 Retention Enforcement L236–241 |
| P-RET-TABLE | Category-specific windows (e.g. session memory: session + 24h / max 7 days; interaction logs 90d / 1y; financial **not retained**; episodic indefinite with decay) | §3 tables L194–234 |
| P-DEL-TYPES | User record delete; category-level delete; retention-expiration delete; full-profile delete | §4 Deletion Types L255–263 |
| P-CASCADE | Deletion not complete until all layers, caches, derived records, and indexes are cleared | §4 Cascade L265–273 |
| P-GHOST | Ghost memories (deleted record reappears from a secondary store) are a trust violation | §4 Ghost memories L292; also L597 |
| P-UI | Memory browser (episodic, canonical, preferences individually viewable **and** deletable); forget controls; inventory by sensitivity; retention visibility; audit log of writes/deletes/transmits | §6 Required User-Facing Capabilities L365–383 |
| P-EXPLAIN | On request: what data, why stored, where held, how long, how to delete | §6 Explanation L387–395 |
| P-3P | Third-party providers: defined retention; no stranding when provider replaced; prompts not retained for training without consent | §7 L414–447 |
| P-GUARANTEE | Forget means deleted, not suppressed/demoted/archived; confirmed and logged | Principles L565–567 |

---

## 1. Retention

**Hermes built-in:** no TTL, no expiry, no rolling window. Grep of `tools/memory_tool.py` + `tools/memory_tool_store.py` for `retention` / `ttl` / `expiry` / `expire`: **no matches**. Bound is **character count**, not time (`config_defaults.py` L1222–1223). `MemoryStore.add` refuses over-budget writes (`memory_tool_store.py` L248–253) and asks the model to consolidate — that is a size cap, not P-RET.

**`state.db` transcripts:** WINH03 established durable session history. No WINH04 evidence of a 24h/7d session-memory window matching P-RET-TABLE “Session memory.” `[UNVERIFIED]` whether any vacuum/prune job deletes old sessions by age; no such job found in the memory tool path.

**Holographic:** `temporal_decay_half_life` default **0 = disabled** (`plugins/memory/holographic/__init__.py` L4, L139; `retrieval.py` L39). When set, it **down-weights retrieval scores** (`retrieval.py` L71, `_temporal_decay` L206) — it does **not** delete rows. That is decay-of-salience, not P-RET deletion.

**Honcho / Hindsight:** retention is the vendor’s cloud policy. Hermes config does not enforce Zola windows. P-3P “must not depend on a provider’s retention to work” is relevant if Zola enables these.

**Against:** P-RET, P-RET-TABLE, E-AGE (age thresholds assume facts still exist but surface rules change — Hermes has neither expiry nor age-gated surfacing).

**Label:** `[GAP]` `WINH04-AUD-03` (HIGH). Optional holographic score decay is `[PARTIAL]` `WINH04-AUD-13` (LOW) against Hierarchy decay, not against Privacy Plan deletion.

---

## 2. Deletion

**Per-entry (built-in):** `memory` tool `action=remove` with `old_text` substring (`memory_tool.py` L172–205; `MemoryStore.remove` L270–274). The agent (or a human via `/memory` pending replay) can delete one `§` entry if they know a unique substring. There is **no** stable fact ID in MEMORY.md.

**Wipe:** `hermes memory reset` (`hermes_cli/subcommands/memory.py` L27–32; `_cmd_memory_reset` L21–56) unlinks `MEMORY.md` and/or `USER.md`. Confirm `yes` unless `--yes`. Does **not** touch `state.db`, plugin DBs, Honcho/Hindsight clouds, or skill files.

**Background review:** `_background_delete_gate` (`memory_tool.py` L148–169) **blocks unattended** replace/remove; stages for `/memory pending` or denies if staging fails. Adds remain available.

**Holographic:** `MemoryStore.remove_fact(fact_id)` (`holographic/store.py` L181–188) — ID-level delete in that plugin only.

**Category-level delete (P-DEL-TYPES):** no sensitivity categories → nothing to bulk-delete by “health” vs “canonical.”

**Cascade (P-CASCADE / P-GHOST):** builtin remove/reset does not notify indexes in `state.db` (the conversation that created the fact remains). `notify_memory_tool_write` mirrors `remove` to the **active** external provider (`memory_manager.py` L738) **if** the builtin tool succeeded — it does **not** search leftover providers after `hermes memory off`, nor session transcripts. Reset CLI unlinks files **without** going through `notify_memory_tool_write`.

**Against:** P-DEL-TYPES (partial record delete + partial full wipe; no category delete; no retention-expiration delete), P-CASCADE, P-GHOST, P-UI forget/browser, P-GUARANTEE (reset is delete of files; per-entry remove is not logged — see §5).

**Label:** `[PARTIAL]` `WINH04-AUD-04` (MEDIUM).

---

## 3. Sensitivity classification

**Built-in:** entries are undifferentiated strings. `_scan_memory_content` (`memory_tool_store.py` L26–29) runs `first_threat_message(..., scope="strict")` for injection/exfil patterns because memory enters the system prompt. That is a **threat scan**, not E-SACRED / P-CAT.

No visibility-scope field. No `userDesignatedSacred`. No health/financial/legal tags. USER.md vs MEMORY.md is “profile vs notes,” not sensitivity.

**Holographic:** `category TEXT DEFAULT 'general'` and `tags` (`store.py` L15–16). Free-text, not the sacred taxonomy.

**Honcho:** user-modeling observations — no Hermes-side sacred-class gate found in this audit.

**Against:** E-SCOPE, E-TAX, E-SACRED, E-USER-SACRED, E-R2, P-CAT, P-CONSENT.

**Label:** `[GAP]` `WINH04-AUD-05` (HIGH).

---

## 4. Access control

**Profile boundary:** `HERMES_HOME` isolates files per profile. That is OS-user + directory, not Zola scopes.

**Who can read MEMORY.md / USER.md:**

| Actor | Can read? | Evidence |
|---|---|---|
| Core agent (system prompt snapshot) | Yes — injected at session start | `memory_tool.py` L2–4 |
| Same-instance tools (`read_file`, `terminal`) | Yes if they open `$HERMES_HOME/memories/` | No ACL in MemoryStore; files are ordinary markdown |
| Subagents with memory/file tools | Yes (shared holographic conn; file tools) | `holographic/store.py` L92–95 |
| Messaging platforms (Telegram, etc.) | Indirect: same agent prompt includes memory | Gateway runs AIAgent; not a separate ACL |
| `mcp_serve.py` MCP clients | **Not** MEMORY.md — messaging conversation bridge | WINH02-AUD-06; `mcp_serve.py` purpose |
| Codex `hermes_tools` MCP | **Explicitly omits** `memory` | `agent/transports/hermes_tools_mcp_server.py` L40 |
| Other Hermes profiles | No, unless they share `HERMES_HOME` / Honcho workspace | Honcho `workspace` is shared across profiles in that workspace (`honcho/README.md` L192) |
| External MCP attached **as tools of this agent** | Can call whatever tools the agent has; if file tools exist, they can read the memories dir | No memory-specific permission object |

There is **no** `PRIVATE_TO_ZOLA` (never surface) vs `PRIVATE_TO_USER` (surface only when user is alone). Frozen prompt injection means **every** consumer of that session’s system prompt sees the full MEMORY.md+USER.md snapshot — messaging included.

Honcho workspace sharing: “all profiles in the same workspace can see the same user identity and related memories” (README L192). That is a **wider** read set than “this Hermes instance,” not a tighter one.

**Against:** E-SCOPE/E-TAX (output-layer privacy), E-CTX, Ethics “technical permission ≠ ethical permission,” Privacy Plan collection/write/retrieval/output enforcement.

**Label:** `[GAP]` `WINH04-AUD-06` (HIGH). MCP omitting the memory tool is a narrow `[MATCH]` for that one surface, not a substitute for scopes.

---

## 5. Integrity / audit trail

**Built-in files:** `atomic_write_text` (`memory_tool_store.py` L422). Drift guard refuses tool writes that would clobber foreign edits (`_drift_error` L36–40) and mentions a bak path. That is **write safety**, not an audit log of who/what/when changed a fact.

No append-only history of MEMORY.md entries. No actor field. `replace`/`remove` mutate in place.

**Holographic:** `created_at` / `updated_at` timestamps (`store.py` L20–21). No actor. Updates overwrite `content`. FTS delete triggers exist for index consistency (L53–58), not a user-facing audit.

**Skills (contrast):** `tools/skill_ledger.py` append-only JSONL with before/after blobs (`skills.ledger` default True, `config_defaults.py` L1377–1381). **Fact-memory has no equivalent.**

**Write-approval pending store:** `write_approval.py` `stage_write` L73–82 writes `pending/<subsystem>/<id>.json` with `created_at` and payload — only when the gate is **on**. Default `memory.write_approval: False`. Pending files are not a durable history of **committed** edits.

**Against:** P-UI audit log; P-GUARANTEE “confirmed and logged”; P-RET extension must be logged (n/a because no windows); Ethics write metadata (source/scope/authority/freshness from Memory Agency — labeled `WINH04-AUD-11`).

**Label:** `[GAP]` `WINH04-AUD-07` (MEDIUM).

---

## 6. User-facing control (Privacy Plan §6)

Hermes CLI: `hermes memory status|setup|off|reset`. Agent tool: add/replace/remove. Desktop/TUI may surface `/memory pending` when the gate is on.

Missing vs P-UI: inventory **by sensitivity tier**; browser of episodic vs canonical vs preference **as distinct record types**; consent matrix; retention window display; audit-log request. Forget of “this fact” depends on the model choosing `remove` with the right substring, or the user wiping the whole file.

**Label:** folded into `WINH04-AUD-04` (deletion UX) and `WINH04-AUD-14` (inventory/audit/retention visibility).

---

## Finding summary (this document)

| ID | Label | Sev | Requirement |
|---|---|---|---|
| WINH04-AUD-03 | [GAP] | HIGH | P-RET / P-RET-TABLE / E-AGE — no time retention on builtin memory |
| WINH04-AUD-04 | [PARTIAL] | MEDIUM | P-DEL-TYPES / P-CASCADE / P-UI forget — substring remove + file wipe; no cascade |
| WINH04-AUD-05 | [GAP] | HIGH | E-SCOPE / E-SACRED / P-CAT — no sensitivity or visibility scope |
| WINH04-AUD-06 | [GAP] | HIGH | E-TAX output rules / access — instance-wide prompt injection; no scopes |
| WINH04-AUD-07 | [GAP] | MEDIUM | P-UI audit / integrity — MEMORY.md has no edit history |
| WINH04-AUD-13 | [PARTIAL] | LOW | Hierarchy decay analog — holographic score decay default off |
| WINH04-AUD-14 | [GAP] | MEDIUM | P-UI inventory, retention visibility, audit-log access |
