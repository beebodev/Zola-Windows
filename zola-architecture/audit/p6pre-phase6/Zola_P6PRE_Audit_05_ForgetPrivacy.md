# P6PRE Audit 05 — Forget, Storage, Privacy

**Audit:** P6PRE · Pin `345cd2b0…`  
**Labels against:** C8→P5-D10, S14, H4 (deferred), ethics arch.

---

## Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-26 | [MATCH] | — | `memory_tool.py`; DESIGN_DECISIONS P5-D10 | Forget removes the entry from MEMORY.md or USER.md; `state.db` stays (P5-D10). |
| P6PRE-AUD-27 | [RISK] | HIGH | `holographic/__init__.py` L185–191; P-2 | With holographic, memory-tool replace/remove do **not** clear the SQLite store (LEAD-2). |
| P6PRE-AUD-28 | [GAP] | MEDIUM | `memory_manager.py` L738–772; holographic | `on_memory_write` can distinguish `replace` vs `remove`, but holographic ignores both; no superseded/forgotten states in store. |
| P6PRE-AUD-29 | [MATCH] | — | holographic store; `backup.py` | Provider DB lives under HERMES_HOME; covered by Hermes backup; holographic path is local-only. |
| P6PRE-AUD-30 | [MATCH] | — | filesystem / SQLite | No encryption at rest for MEMORY.md, USER.md, or `state.db` (H4 deferred). |

---

## 1. Today’s forget (E2E)

1. Brian asks to forget / she decides to remove.
2. Model calls `memory` tool `remove` or `replace` with `old_text`.
3. Entry removed/updated in the file that holds it (`MEMORY.md` or `USER.md`).
4. `state.db` transcripts and stored prompts **unchanged**.

**P5-D10 confirmed** (P6PRE-AUD-26). SOUL covers save/update; forget procedure is tool behavior + conventions, not a separate API.

---

## 2. External provider + forget paths

| Path | Reaches holographic store? |
|------|----------------------------|
| memory-tool `add` | Yes (mirror) |
| memory-tool `replace` (correction) | **No** — old fact remains (P-2) |
| memory-tool `remove` (forget) | **No** — old fact remains (P-2) |
| `fact_store(action='remove')` | Yes (by `fact_id`) — separate model tool |
| Direct “forget my car” without tool | No automatic cascade |

**LEAD-2 confirmed** (P6PRE-AUD-27). Manager *would* forward replace/remove with `old_text`; holographic’s legacy handler drops them.

---

## 3. Fail-closed requirements for any new store

From evidence (requirements only):

- Removal by **content match** (`old_text`), by **id**, and by **entity** (with link/cascade cleanup).
- Removal or unlink of **derived** records (episodes mentioning the fact) if episodes exist.
- **Index cleanup** (FTS/vector) must succeed with the logical delete, or fail closed.
- Transcript policy remains P5-D10 unless a later decision changes it.

### 3a. Correction ≠ forget

| | Correction | Forget |
|---|------------|--------|
| Memory tool today | `replace` | `remove` |
| Distinguishing in `on_memory_write` | **Yes** — different `action` (+ `old_text`) | Same |
| Holographic today | Neither applied | Neither applied |
| Represent superseded vs forgotten | **No** in holographic — overwrite or hard delete only | — |

Facts for decision later; exact P6 semantics not chosen here (P6PRE-AUD-28).

---

## 4. Location, backup, network

| Store | Location | Backup | Network |
|-------|----------|--------|---------|
| MEMORY.md / USER.md | `$HERMES_HOME/memories/` | Yes (home walk) | No |
| holographic `memory_store.db` | `$HERMES_HOME/` | Yes (`_QUICK_STATE_FILES` + walk) | No |
| `backup_paths()` extras | Absolute under home only | If under home | Must work offline |
| Cloud providers (honcho, mem0, …) | Vendor | Vendor | Yes if activated — **not** live |

**P6PRE-AUD-29 [MATCH]** for local holographic/builtin. Inputs for P4 “local only” revision: activating a cloud provider would introduce network + retention; holographic/builtin stay on-box.

---

## 5. Encryption at rest

- MEMORY.md / USER.md: plaintext UTF-8.
- `state.db`: standard SQLite (not encrypted by Hermes).
- **H4 deferred** — no change (P6PRE-AUD-30).
