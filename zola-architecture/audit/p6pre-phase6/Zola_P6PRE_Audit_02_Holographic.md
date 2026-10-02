# P6PRE Audit 02 — Holographic Provider vs Zola Needs

**Audit:** P6PRE · **Pin:** `345cd2b057a452236de401d3534b8502a7465e8d`  
**Sources:** `plugins/memory/holographic/*`, `plugins/memory/query_rewrite.py`  
**Live:** holographic **not** active (`memory.provider: ""`).

---

## Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-08 | [RISK] | HIGH | `holographic/__init__.py` L185–191 | `on_memory_write` mirrors **add only**; replace/remove leave SQLite copies (LEAD-2; confirmed P-2). |
| P6PRE-AUD-09 | [RISK] | MEDIUM | `holographic/__init__.py` L156–165; `memory_provider.py` L111–117 | `prefetch` searches synchronously; no `queue_prefetch` (LEAD-3). |
| P6PRE-AUD-10 | [RISK] | HIGH | `holographic/__init__.py` L142–154, L167–168 | Dual model-facing write paths (`memory` + `fact_store`); empty-store prompt says “proactively add” (LEAD-5). |
| P6PRE-AUD-11 | [RISK] | MEDIUM | `holographic/__init__.py` L230–254 | `auto_extract` stores raw user text ≤400 chars by regex category (LEAD-6). |
| P6PRE-AUD-12 | [MATCH] | — | `store.py` L101–135; `__init__.py` L130–135 | DB is profile-local SQLite under `HERMES_HOME` (`memory_store.db`); no network client. |
| P6PRE-AUD-13 | [GAP] | HIGH | holographic plugin | No episode/event model — facts only. |
| P6PRE-AUD-14 | [GAP] | MEDIUM | `__init__.py` L161–162; `store.py` L20–21 | `created_at`/`updated_at` exist but are **not** shown in prefetch text. |
| P6PRE-AUD-15 | [MATCH] | — | `store.py` L13, L161–190 | Stable `fact_id` AUTOINCREMENT; real DELETE on remove; update keeps ID (no history). |
| P6PRE-AUD-16 | [RISK] | MEDIUM | P-1 harness | Warm prefetch ~2 ms at 2,000 facts; inserts slow (HRR bank rebuild); SNR warnings at dim=1024/~2k items. |

---

## 1. Schema and DB path

Tables (`store.py` L11–71): `facts`, `entities`, `fact_entities`, `memory_banks`, FTS5 `facts_fts` + AI/AD/AU triggers, indexes on trust/category/name.

Default path: `get_hermes_home() / "memory_store.db"` with `$HERMES_HOME` expansion (`__init__.py` L131–135). Inside the profile when HERMES_HOME is the profile.

---

## 2. Entity resolution

- Regex extract: Capitalized Multiwords, quotes, `aka` (`store.py` L75–78, L216–224).
- Resolve by name/alias or create; M2M link to facts.
- **No** entity-row merge; `aliases` not written by extract.
- Multi-entity facts: yes. Address by entity: `probe`/`related` by **name string**, not `entity_id`.

---

## 3. Retrieval

| Method | Mechanism |
|--------|-----------|
| search | FTS5 → Jaccard + HRR rerank → trust weight |
| probe / related / reason | HRR compositional; FTS fallback without NumPy |
| contradict | NumPy only |

**Prefetch:** sync `search(..., limit=5)` (`__init__.py` L156–165). No `queue_prefetch`. Manager timeout 8 s. `query_rewrite.py` is **not** wired.

**P-1 (scratch, NumPy present, HRR path):**

| n | init ms | cold prefetch ms | warm median / p95 / max ms | add median ms | DB bytes |
|---|---------|------------------|----------------------------|---------------|----------|
| 50 | 28.4 | 3.1 | 1.6 / 2.9 / 3.5 | 7.7 | 4,096 |
| 500 | 17.5 | 3.7 | 1.9 / 3.2 / 4.2 | 26.7 | 2,342,912 |
| 2,000 | 17.5 | 4.7 | 2.0 / 2.7 / 3.2 | 61.1 | 9,584,640 |

2,000-fact insert+query ≈ 120 s → **5,000 not run** (30 s gate). HRR capacity warnings from ~n=1949 (dim=1024).

---

## 4. Trust / feedback

helpful +0.05 / unhelpful −0.10; clamp [0,1]. Retrieval filters `min_trust` (default 0.3). **No** auto-delete; low trust only excluded at query. `retrieval_count` unused.

---

## 5. LEAD outcomes (this doc)

| LEAD | Status | Evidence |
|------|--------|----------|
| LEAD-2 | **Confirmed** | Code L185–191; P-2: after replace/remove, old fact_id=1 still in store |
| LEAD-3 | **Confirmed** | Sync search in prefetch; no queue_prefetch |
| LEAD-5 | **Confirmed** | `fact_store` schemas + proactive system_prompt_block |
| LEAD-6 | **Confirmed** | `add_fact(content[:400], category=…)` |

---

## 6 / 6a. Remove, update, stable IDs

- Remove/update by **`fact_id` only** (hard DELETE / in-place UPDATE).
- No remove-by-content/entity via mirror path.
- IDs survive restart; update keeps ID; **no** superseded history — overwrite only.
- Exclusion via trust threshold, not a forgotten/superseded state.

---

## 7–8. Episodes and time

- **Episodes:** none (P6PRE-AUD-13).
- **Time:** columns exist; prefetch shows `- [{trust}] {content}` only (P6PRE-AUD-14).

---

## 9. Injected text (quotes)

**system_prompt_block** (empty store):

```text
# Holographic Memory
Active. Empty fact store — proactively add facts the user would expect you to remember.
Use fact_store(action='add') to store durable structured facts about people, projects, preferences, decisions.
Use fact_feedback to rate facts after using them (trains trust scores).
```

**prefetch:**

```text
## Holographic Memory
- [{trust:.1f}] {content}
```

---

## 10. Score table

| Need | Verdict | Evidence |
|------|---------|----------|
| Entity facts | adapt | Free-text + regex entities |
| Subject (not kind) routing | adapt | Categories exist; no subject ACL; P5 #12 still a concern |
| Episodes | does not fit | No model |
| Per-turn relevance in latency budget | adapt | Warm prefetch ≪ S38; inserts/HRR capacity are the costs |
| Time on records | adapt | DB yes; model-facing prefetch no |
| Stable IDs | fits | `fact_id` |
| Correction ≠ forget | adapt | Tools differ; mirror loses both |
| Forget reaches every copy | does not fit | LEAD-2 |
| Memory tool only model write | does not fit | `fact_store` + auto_extract |
| Local only | fits | Profile SQLite |
| No third-party retention | fits | Local |

---

## Requirements if kept vs Zola-owned (not a choice)

**Holographic as-is / adapted in a Zola-owned plugin copy (no hermes-agent edit):**
- Fix `on_memory_write` for replace/remove (+ metadata / `old_text`)
- Suppress or rewrite `system_prompt_block` / optionally hide `fact_store` writes (`get_tool_schemas` read-only or `[]`)
- Implement `queue_prefetch` if sync search ever grows past budget
- Add episodes / supersession / forget-everywhere if S14 requires them (as-is cannot)
- Watch HRR dim vs fact count

**Zola-owned provider:**
- Satisfy `MemoryProvider` ABC; use `hermes_home`; one external provider
- Choose authority model (Audit 01 Q9–Q10)
- Local-only if P4 revisits that way
- Episode writer + forget fail-closed + conditional time (other audits)

**Do not recommend** holographic vs Zola-owned here — options for synthesis §5.2.
