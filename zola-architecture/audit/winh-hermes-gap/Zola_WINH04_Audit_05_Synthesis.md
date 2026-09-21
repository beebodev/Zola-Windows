# WINH04 Audit 05 — Domain Synthesis (this audit only)

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Not a WINH00 closeout. No integration path chosen. Memory-agency exception (entity-vs-user ownership; Hermes holds memory R/W) is **not** in the table below.

Documents: `Zola_WINH04_Audit_01_StorageOwnership.md` … `_04_HierarchyReconciliation.md`.

---

## Finding summary table

| ID | Label | Sev | One-line |
|---|---|---|---|
| WINH04-AUD-01 | [PARTIAL] | MEDIUM | Builtin MEMORY.md/USER.md + `state.db` + optional plugin do not implement Hierarchy layers 0–6 as distinct stores |
| WINH04-AUD-02 | [RISK] | MEDIUM | External provider `sync_turn` / session hooks persist memory outside `memory_tool` (second write authority) |
| WINH04-AUD-03 | [GAP] | HIGH | No time-based retention/expiry on builtin memory (char caps only) — Privacy Plan §3 |
| WINH04-AUD-04 | [PARTIAL] | MEDIUM | Per-entry `remove` + `hermes memory reset`; no cascade across plugin/`state.db` — Privacy Plan §4 |
| WINH04-AUD-05 | [GAP] | HIGH | No visibility scopes or sacred-category handling — Ethics Visibility Scopes / Sacred Memory Classes |
| WINH04-AUD-06 | [GAP] | HIGH | No access/output boundary: full snapshot in every session prompt; tools can read `$HERMES_HOME/memories/` |
| WINH04-AUD-07 | [GAP] | MEDIUM | MEMORY.md has no edit audit trail (atomic write + drift bak ≠ history) |
| WINH04-AUD-08 | [MATCH] | LOW | Skills live in a separate filesystem backend from fact-memory |
| WINH04-AUD-09 | [RISK] | MEDIUM | `skill_manage` create/edit default-on with `skills.write_approval: False` |
| WINH04-AUD-10 | [PARTIAL] | MEDIUM | Skill load errors are returned; runtime failure does not disable the skill |
| WINH04-AUD-11 | [GAP] | MEDIUM | No DWA, write classification, promotion, or per-fact source/scope/authority/freshness metadata |
| WINH04-AUD-12 | [GAP] | MEDIUM | No work/home/shop context isolation on stored facts — Ethics Context Contamination |
| WINH04-AUD-13 | [PARTIAL] | LOW | Holographic `temporal_decay_half_life` is retrieval weighting, default 0, not deletion |
| WINH04-AUD-14 | [GAP] | MEDIUM | No sensitivity inventory, retention-window UI, or memory audit-log access — Privacy Plan §6 |

Counts: **3 HIGH**, **9 MEDIUM**, **2 LOW**. (14 findings.)

---

## What Hermes covers as-is (memory / skills)

- **Durable agent notes and a user profile file**, profile-scoped under `$HERMES_HOME/memories/`, injected as a frozen system-prompt snapshot (`tools/memory_tool.py`, `tools/memory_tool_store.py`, `config_defaults.py` `memory.*`).
- **Bounded size** (2200 / 1375 chars) and a **strict threat scan** on content that will sit in the prompt.
- **Per-entry add/replace/remove** (substring match) plus **CLI wipe** (`hermes memory reset`).
- **Optional human gate** for memory and skills (`write_approval`) — real mechanism, **off by default**.
- **Background-review cannot silently delete** builtin memory (`_background_delete_gate`).
- **Session transcripts** in `state.db` with `session_search` recall after compaction (WINH03 + this audit).
- **One optional external memory provider** (Honcho / Hindsight / holographic / …) **plus** builtin, wired through `MemoryManager` / `MemoryProvider`.
- **Holographic (if chosen):** local SQLite facts, entity table, trust scores, ID-level `remove_fact`.
- **Skills package lifecycle:** bundled sync, optional/hub install, project-local trusted dirs, agent `skill_manage`, slash commands, curator archive (agent-created only, never delete), **skill ledger** with rollback (`skills.ledger` default True).
- **MCP messaging and Codex hermes-tools do not expose the `memory` tool** — a narrow read-boundary on those sockets, not a general ACL.

This is a capable **single-user agent notebook + skill library**. It is not Zola’s layered, scoped, retention-bounded memory architecture.

---

## What needs a Zola-built adapter layer

Work that **wraps** Hermes rather than replacing it:

1. **Turn `write_approval` on** for `memory` and `skills` in the Windows product config (adapter/policy, not a new store). Still not DWA — it only delays writes.
2. **Treat MEMORY.md / USER.md as an export surface**, not as Layer 4/5: adapter owns typed records and **projects** a char-budgeted snapshot Hermes can inject — or Zola stops using the builtin snapshot and injects via its own prompt builder (heavier; WINH00).
3. **Deletion orchestrator:** map “forget this fact” to (a) builtin `remove` or file rewrite, (b) provider `on_memory_write`/`remove`, (c) decision about `state.db` (transcript redaction is not in Hermes). Cascade is adapter work (`WINH04-AUD-04`).
4. **Provider policy:** default `memory.provider = ""` for Zola-Windows unless a vendor is explicitly chosen; Honcho workspace sharing is an access-control landmine (`WINH04-AUD-06`). `sync_turn` auto-extract should be treated as a **second writer** to box or disable (`WINH04-AUD-02`).
5. **Skills:** keep Hermes storage (`WINH04-AUD-08`); adapter should default `skills.write_approval: true` and decide whether curator LLM consolidate stays off (`DEFAULT_CONSOLIDATE` is already False).
6. **Skill fail-closed:** adapter/config can add names to `skills.disabled` when a skill errors; Hermes will not do that itself (`WINH04-AUD-10`).

---

## What must be built from scratch

Especially Phase 3 items with **no** Hermes mechanism — build-plan relevant:

| Capability | Why scratch | Finding |
|---|---|---|
| Visibility scopes + output governor | No field, no `PRIVATE_TO_ZOLA` path; prompt dump is all-or-nothing | AUD-05, AUD-06 |
| Sacred-category classifier + user-designated sacred flag | Threat scan ≠ health/finance/legal taxonomy | AUD-05 |
| Time retention + expiration deletion | Char limits only; holographic decay does not delete | AUD-03, AUD-13 |
| Memory edit audit log (who/when/what) | Contrast: skills **have** `skill_ledger`; facts do not | AUD-07, AUD-14 |
| Data inventory by sensitivity; retention visibility | CLI `memory status` is provider config, not a browser | AUD-14 |
| Context isolation (work vs home vs shop) | Single USER.md | AUD-12 |
| Durable Write Authority + promotion + episode store + Layer 6 consolidator + topic stack | Hierarchy layers are missing or collapsed | AUD-01, AUD-11 |
| Deletion cascade + ghost-memory prevention | Reset does not touch `state.db` or clouds | AUD-04 |

Do **not** build a second “entity ownership” plane to fight Hermes — that principle is superseded. If Zola later wants holographic-style entities, that is an **optional provider choice**, not a gap against the exception.

---

## Open questions for WINH00

1. **Does Zola-Windows keep Hermes builtin MEMORY.md as the live store**, or only as a compatibility projection from a Zola store? This choice drives almost every HIGH finding.
2. **Are Honcho/Hindsight allowed in the product?** If yes, P-3P (provider retention, stranding, workspace sharing) becomes a shipping constraint, not a plugin footnote.
3. **Session transcripts vs forget:** is redacting `state.db` in scope for Zola, or is “forget” defined as MEMORY.md only (weaker than P-CASCADE)?
4. **Skills governance vs WINH06:** stock `write_approval: False` is recorded (`AUD-09`); WINH06 should not rediscover it — decide default-on for Zola.
5. **Identity memory** (self-model, USER.md vs Zola personality docs) is **deferred to WINH05** — USER.md flattening (`Layer 5 [PARTIAL]`) will reappear there.
6. **Environmental perception → memory promotion** stays out of series (progress “Recorded scope decisions”); WINH00 should not reopen it inside Hermes gap analysis.

Standing earlier findings that still color this domain: WINH03 session durability (`state.db` vs live `_sessions`) is the Layer 2 log’s physical home; WINH02-AUD-06 MCP is not a memory API.
