# P6-EPISODES Progress — Episodes

## Branch

- Branch: `p6-episodes`
- Base `main` HEAD: `c99e21cbcbb2733068dea2b2197b9662dbbd2731` (contains P6-FORGET merge `7b8f030b611372b5d2c35f0c460455916e781384`)
- Prompt version: 1.1 (2026-10-04) against build plan v1.1
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P6-EPISODES_Prompt_v1.1.md`
  SHA-256 `f6aae3d4b62e67eabcd5b2c01ed31deac6ca1be6dfd808a12bd12fe76642512b` (31,880 bytes; matches developer-supplied hash, case-insensitive)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`); porcelain empty (detached HEAD — pre-existing; pin matches)

## Phase table

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document | COMPLETE |
| 2 | Grounding (E1–E10) | COMPLETE |
| 3 | Propose the Episode Contract | COMPLETE |
| 4 | Build and Test | COMPLETE (incl. 4b) |
| 5 | Propose the Live Changes | COMPLETE |
| 6 | Back Up, Deploy, Apply, Mirror, Verify | COMPLETE |
| 7 | Smoke Test | COMPLETE — accepted Brian + Claude (caveats recorded) |
| 8 | Closeout | IN PROGRESS |

## Guardrails summary

- **G-SCOPE:** Repo: `hermes-plugins/zola_memory/` (`pending.py`, `consolidate.py`, `retrieve.py`, provider wiring, store v2, forget cascade/G-ERASE, log, tests); this progress doc; `identity/` only if Phase 5 STOP approves SOUL. Live Phase 6 only after Phase 5: redeploy plugin; approved G-ERASE maintenance; optional SOUL. No expected `config.yaml` change. No client / approvals / zola_tools / time-context behavior / fact-index import rules / second writer / vector retrieval.
- **G-ARCH:** Build plan + Appendix A govern. Plugin LLM outside approved trust boundary or wrong profile context → STOP.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No `windows-client/**`; no `hermes-agent` edits; no hand edits to live `memories/`, `state.db`, `skills/`, `auth.json`, `.env`, `approvals.*`, `plugins/zola_tools/`; no lore / build-plan edits.
- **G-NO-INSTALL:** Standard library only.
- **G-ONE-WRITER / G-ONE-CONSOLIDATOR / G-PENDING-ID / G-NO-RECURSION / G-ENTITY-GROUNDING / G-BRIAN-ONLY / G-FORGET / G-ERASE / G-TRUTH / G-TRUST:** As in prompt (consolidator sole episode writer; module-level lock; opaque pending IDs; no retrieval→episode recursion; grounded entities; Brian `tui`+no parent + disposition keep; Track 4 APIs; physical erase proposal; stated times only; `_get_plugin_llm()` only).
- **G-PRIVACY / G-CONST / G-COMMENT / G-LIVE / G-STOP / G-CLOSEOUT / G-LORE-SCOPE / G-NO-CROSS-SCOPE:** Logs metadata only; named constants; Cursor never sends turns; closeout only on "proceed to closeout"; no lore edits; no Android Zola.

## Discrepancies

- Prompt Document of Truth cites `PHASE6_DECISIONS.md`; that file is a **project doc outside the repo** — discrepancy **accepted** (Brian, Phase 2→3). Inputs come from Track 3/4 progress docs + build plan.
- `hermes-agent` is at the required pin with empty porcelain but in **detached HEAD** (pre-existing). Read-only use continues; no checkout/edit.

## Phase 1 baseline tests

| Suite | Result |
|---|---|
| `zola_memory` | Ran 79 tests — OK |
| `zola_tools` | Ran 44 tests — OK |

## E1–E10 grounding table

| ID | Verdict | Evidence (file:lines) | One-line |
|---|---|---|---|
| E1 structured call | **[CONFIRMED]** | `hermes-agent/agent/plugin_llm.py` L460–474, L72–86, L402–408; `auxiliary_client.py` ~L5724/L5836–5841; `zola_memory/__init__.py` L31–38 | `complete_structured(*, instructions, input, json_schema/json_mode, …) -> PluginLlmStructuredResult`; JSON Schema via `response_format`; default timeout **30s** when `task` unset; optional `max_tokens`. Reach via `_get_plugin_llm()` → `ctx._plugin_context().llm`. No consolidator call sites yet. |
| E2 trust boundary | **[CONFIRMED] PASS** | Live `config.yaml` L1–4; probe under `HERMES_HOME=zola`: `_read_main_*` → `openai-codex` / `gpt-5.6-terra`; `_resolve_auto_route` → same | Matches P6-STORE G2. No overrides / no foreign `task` required for plain calls. |
| E3 background work | **[CONFIRMED]** | `memory_provider.py` L21–33 (`spawn_context_thread` / `ctx_bound`); `memory_manager.py` L480–518, L782–828 (`_SYNC_DRAIN_TIMEOUT_S=5`); Honcho isolation tests | Profile context via `spawn_context_thread`/`ctx_bound`. Manager sync worker already context-bound. Reference providers join in `shutdown()`. LLM from propagated thread OK; bare `Thread` is not. zola_memory owns **no** timer threads yet (consolidator will). |
| E4 prefetch contract | **[CONFIRMED]** | `memory_provider.py` L111–114; `memory_manager.py` L266–279, L32, L394–432; `turn_context.py` L90–94, L793–809, L1046–1107 | `prefetch` → `str`; fenced `<memory-context>`; appended to **current user** wire/`api_content`; external timeout **8.0s**; prior turns **replay** sidecar bytes (not re-prefetched). |
| E5 compress / session-end | **[CONFIRMED]** | `memory_manager.py` L674–709, L614–645; `conversation_compression.py` ~L2610–2647, L3263–3265; `run_agent.py` L857–872; F5 FIFO tests | `on_pre_compress` **inline** (no MM timeout; compress attempt ~120s ceilings). Memory `on_session_end` can fire on commit paths; shutdown path idempotent. Boundary: `on_session_end` then `on_session_switch` on same FIFO worker as late `sync_turn`. Drain orphan wait **5s**. |
| E6 processes | **[CONFIRMED]** | `store.py` L68–74 (WAL), L12–14/L84–93 (in-process RLock only); P6-STORE G6 dual-open note | Multiple processes can open live DB (serve + short-lived `AIAgent`). Client does not open store. **Cross-process consolidator guard needed** (module lock alone insufficient). |
| E7 turn shape / user time | **[CONFIRMED]** | T4: `run_agent.py` L875–901; redirect: `turn_iteration_prep.py` L318–324; timestamps: `message_metadata.py` L9–27, `turn_context.py` L568–570 | Sync `user_content` = original text (+ redirect suffix), **no** time stamp. `messages` carry `timestamp`. **Proposal:** pending `user_time` from `messages[persist_idx]["timestamp"]` or `_persist_user_message_timestamp` at `sync_all`; store redirect-augmented text as-is; skip interrupted (no sync). |
| E8 FTS/deletion | **[CONFIRMED]** | Scratch measure `e8_fts_delete_measure.py` (runtime SQLite) | See **E8 measurements** below. `secure_delete=ON` clears synthetic bytes from `.db`; baseline leave free-page survivors. Live backup still holds some FORGET-smoke byte remnants → supports one-time `VACUUM` at deploy. |
| E9 entities today | **[CONFIRMED]** | `store.py` L180–193; live backup counts 0/0; no INSERT writers; orphan DELETE only `forget.py` L606–617 | Tables exist, empty, unused for writes. **Proposal:** match `casefold()` exact on `entities.name` / `entity_aliases.alias`; create new only when grounded and no hit; persist evidence substrings. |
| E10 prefetch budget | **[CONFIRMED]** | `e10_prefetch_budget.py`: live backup + 200 synthetic episodes; FTS5 `MATCH` + `bm25` `LIMIT 3`; n=50 | median **0.065 ms**, p95 **0.069 ms** (well under 50 ms exit criterion / 8 s timeout). |

### E8 measurements (scratch; synthetic Quill/Alpine/A110/Cedar)

| Config | erase_ms | optimize_ms | checkpoint_ms | post `.db` needle hits | post `-wal` hits |
|---|---|---|---|---|---|
| baseline (no `secure_delete`) | 1.47 | — | — | **still present** (Quill/Alpine/A110/Cedar) | 0 (wal empty) |
| `secure_delete=ON` | 1.83 | — | — | **0** | 0 |
| `secure_delete` + FTS `optimize` + `wal_checkpoint(TRUNCATE)` | 2.45 | 0.73 | 0.96 | **0** | 0 |

Live offline backup (`sqlite3.backup` → scratch; never touched live file):

| Needle | Count |
|---|---|
| Tobias/Wren/Volvo/P1800/Mara/cello/Denver/Priya/Lund/bees | **0** |
| Dana / Okafor / Vespa | **2 / 2 / 2** |
| Rosa / marathons / paints | **6 / 16 / 23** |
| entities / entity_aliases / episodes / pending_turns | **0 / 0 / 0 / 0** |
| facts_active | **14** |

### E7 pending `user_time` proposal (for Phase 3)

At `sync_all` / provider `sync_turn`, resolve Brian’s send instant from the persisted user row `timestamp` (or `agent._persist_user_message_timestamp`), pass as an explicit field (not embedded in `user_content`). Store redirect-augmented user text as received. Interrupted turns never sync → never queued.

### E6 consolidator guard proposal (for Phase 3)

Module-level lock for in-process singleton **plus** a cross-process SQLite lock row / `BEGIN IMMEDIATE` lease (or OS lockfile under the profile) so serve + CLI probes cannot run two consolidators.

### E9 entity match proposal (for Phase 3)

`norm = strip+casefold`. Hit on `entities.name` or any alias → reuse `entity_id`. Else create with exact evidence name + model kind. Aliases added when grounded surface ≠ canonical name.

## Phase 2 acceptance (Brian + Claude, verbatim, 2026-10-04)

> Phase 2 accepted (Brian + Claude). Phase 3 must reflect:
> 1. E5: on_pre_compress must NOT run consolidation inline (no timeout there; a 30 s LLM call would stall compression). Pending turns are already queued per turn via sync_turn, so compression loses nothing; on_pre_compress only signals the background consolidator (non-blocking). Same for on_session_end/switch.
> 2. E6: cross-process guard = a lease row in meta (owner id + expiry) taken with BEGIN IMMEDIATE, renewed while running, expiring automatically (proposed 2× the LLM timeout) so a crashed consolidator never blocks future runs. Plus the module-level lock in-process.
> 3. E7: adopt — user_time from the persisted user message timestamp; redirect-augmented text stored as received; interrupted turns never queued.
> 4. E8 → G-ERASE: propose adoption with these numbers (secure_delete ≈ +0.4 ms per erase; optimize + checkpoint ≈ 1.7 ms — small enough to run synchronously inside the cascade commit path, so no logical/physical delay). One-time VACUUM at deploy after backup; re-scan expected 0 for Dana/Okafor/Vespa/Rosa/marathons/paints.
> 5. E9: adopt the entity match proposal, with G-ENTITY-GROUNDING enforced by the validator.
> Note: PHASE6_DECISIONS.md is a project doc, not in the repo — discrepancy accepted; inputs come from the Track 3/4 progress docs.
> proceed to phase 3

### Effective Phase 2→3 rulings

1. Lifecycle hooks **signal only** (never inline consolidate).
2. Cross-process **meta lease** + in-process module lock.
3. Pending `user_time` / redirect / interrupt rules adopted from E7.
4. **G-ERASE adopt** with sync cascade sanitization + deploy `VACUUM`.
5. Entity match + validator grounding adopted from E9.

## Proposed episode contract (Phase 3 STOP — nothing built)

### 1. Pending writer (`pending.py`)

**When:** only from provider `sync_turn`, and only when:
- `is_brian_conversation(platform, parent_session_id)` (tui, no parent), and
- `turn_disposition == "keep"`.

**Hold / drop (choose one):** **never write** held turns. Justification: Track 4 `turn_disposition` already returns `drop` for forget-hold / forget-intent / redirect-disposition drops, so a pending write gated on `keep` never queues them. Writing-then-flagging would risk consolidating after hold expiry without a second authority check. Column `forget_hold` stays `0` / unused on this path.

**Fields written:**
| Column | Source |
|---|---|
| `id` | new opaque UUID (G-PENDING-ID) |
| `session_id` | provider session id |
| `turn_index` | provider monotonic turn index for that session (ordering metadata only) |
| `user_text` | `user_content` as received (may include `\n\nUser correction during the turn: …`) |
| `assistant_text` | assistant content |
| `user_time` | ISO-8601 from persisted user message `timestamp` (E7), via `messages` / `_persist_user_message_timestamp` when available; if missing, omit write (fail closed — no undated pending) |
| `assistant_time` | assistant message `timestamp` when present; else wall clock at sync (ISO-8601, profile zone) |
| `consolidation_generation` | current meta generation at insert |
| `forget_hold` | `0` |
| `created_at` | now |

**Dedupe (G-PENDING-ID):** schema v2 adds `UNIQUE(session_id, turn_index)`. Insert uses `INSERT OR IGNORE` (or equivalent) so a repeated `sync_turn` for the same completed turn queues **one** row. Snapshots / `can_commit` / deletes operate on pending **ids**.

**Interrupted turns:** never reach `sync_turn` → never queued.

### 2. Triggers and singleton

**Constants:** `CONSOLIDATE_QUIET_MINUTES = 10`; `CONSOLIDATE_LLM_TIMEOUT_S = 30` (plugin structured default); `CONSOLIDATE_LEASE_TTL_S = 60` (2× LLM timeout); `CONSOLIDATE_MAX_ATTEMPTS = 5`.

**Triggers (all only enqueue / wake the consolidator — never run the LLM inline):**
| Trigger | Behavior |
|---|---|
| Quiet-gap timer | Module-level timer via `spawn_context_thread`: if pending rows exist and last Brian keep-write older than quiet gap → `request_consolidate("quiet")` |
| `initialize` | If pending backlog → `request_consolidate("initialize")` |
| `on_pre_compress` | **Waits for nothing.** Sets a coalesce flag / wakes consolidator thread via `request_consolidate("pre_compress")` and returns immediately. Never calls the LLM, never joins the consolidator (Brian E5 — a 30 s call would stall compression). Pending already queued per turn via `sync_turn`, so compression loses nothing. |
| `on_session_end` / `on_session_switch` | Same: **signal only**, return immediately. Idempotent; double-fire safe via coalesce flag. Never join LLM. |
| After pending write | Arm/reset quiet timer only (no immediate consolidate) |

**In-process:** module-level lock; at most one consolidator thread/task (`spawn_context_thread` / `ctx_bound` for LLM).

**Cross-process lease (meta, Brian E6):**
- Keys: `consolidate_lease_owner` (opaque process/instance id), `consolidate_lease_expires_at` (ISO-8601).
- Acquire: `BEGIN IMMEDIATE`; if no lease or expiry is before now, set owner + expiry = now + `CONSOLIDATE_LEASE_TTL_S` (60 s = 2× LLM timeout); commit. Else abort this run (`lease busy`).
- Renew periodically while LLM/commit runs (same IMMEDIATE write of expiry).
- Release on success/failure (clear keys) in `finally`.
- Crashed owner: lease expires automatically → next run may take it (never permanent block).

### 3. Model call (`consolidate.py`)

**Accessor:** only `_get_plugin_llm().complete_structured(...)`. If `llm_available` false → log, **not** an attempt; pending stays.

**Timeout:** `timeout=CONSOLIDATE_LLM_TIMEOUT_S` (30).

**JSON schema** (no fact-creating field):

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["episodes"],
  "properties": {
    "episodes": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["summary", "significance", "entities", "fact_refs", "source_turn_range", "event_time_basis", "open_items"],
        "properties": {
          "summary": { "type": "string", "minLength": 1, "maxLength": 800 },
          "significance": { "type": "string", "enum": ["decision", "plan", "event", "preference_change", "problem", "other"] },
          "entities": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["name", "kind"],
              "properties": {
                "id": { "type": ["string", "null"] },
                "name": { "type": "string", "minLength": 1, "maxLength": 120 },
                "kind": { "type": "string", "enum": ["person", "project", "vehicle", "place", "org", "other"] },
                "alias": { "type": ["string", "null"] }
              }
            }
          },
          "fact_refs": { "type": "array", "items": { "type": "string" } },
          "source_turn_range": {
            "type": "object",
            "additionalProperties": false,
            "required": ["start_pending_id", "end_pending_id"],
            "properties": {
              "start_pending_id": { "type": "string" },
              "end_pending_id": { "type": "string" }
            }
          },
          "event_time": { "type": ["string", "null"] },
          "event_time_basis": { "type": "string", "enum": ["stated", "unknown"] },
          "event_time_evidence": { "type": ["string", "null"] },
          "open_items": { "type": "array", "items": { "type": "string", "maxLength": 240 } }
        }
      }
    }
  }
}
```

Note: model-facing schema **omits** `system` (P6-D02 reserves it for a future structured system origin, never model prose). Validator still rejects any model-supplied `system` if present via loose parse. Stored column may later hold `system` from a non-model writer.

**Exact summarizer instruction text:**

```
You consolidate Brian's recent conversation turns into zero or more memory episodes for Zola.

Rules:
- Small talk, greetings, arithmetic, and passing chatter produce NO episode.
- One stretch of conversation may produce several episodes when they are distinct.
- Never record the content of a forget request or what was erased.
- Never create, invent, or rewrite lasting notebook facts. You may only reference existing fact IDs from the provided list.
- Do not create an episode merely because Zola restated or recalled something from memory context. Only something new that happened or was decided in the source turns justifies an episode.
- Open items and future plans belong in open_items on the episode they belong to — not as their own episodes.
- Entity names and aliases must appear exactly as written in the source turns or in the provided active facts (no expanding abbreviations or inventing canonical names).
- event_time: only when Brian used a time phrase in a user turn. Set event_time_basis to "stated" and set event_time_evidence to his exact phrase. Never infer times from when the message was sent. A future plan is not an event_time (use basis "unknown" and nulls). Prefer referencing existing fact_refs when an episode concerns a stored fact.
- source_turn_range must use pending turn ids from the input list.
- If nothing qualifies, return {"episodes": []}.
```

**Input format to the model** (structured text blocks, no live privacy leak in logs):
1. Pending turns in order: `pending_id`, `user_time`, `user_text`, `assistant_text`.
2. Entity list: `id`, `name`, `kind`, aliases[].
3. Active facts: `id`, `target`, `text`.

### 4. Validation (all-or-nothing)

- Parse against schema; any failure → failed attempt (pending kept).
- **Empty `[]`:** valid only when call succeeded and schema-valid → consume pending (intentional zero).
- **Any invalid episode in a non-empty list:** whole consolidation fails; **no** partial commit; **not** treated as `[]`.
- Rules: every plan rule + **G-ENTITY-GROUNDING** — each entity `name` and optional `alias` must (a) appear case-folded as a substring of some source user or assistant text in the snapshot range, or (b) equal (casefold) a provided active-fact text, or (c) equal (casefold) a provided entity list name/alias. Model-supplied `id` must match that list when present. `fact_refs` must be active ids; `source_turn_range` ids in snapshot and start≤end in pending order; significance/kind enums; summary length; `stated` ⇒ evidence non-empty and found verbatim case-folded in a source **user** turn in range; `unknown` ⇒ event_time and evidence null; reject `system` basis; reject unknown keys that create facts.

### 5. Stated-time resolution

Phrase table (case-folded match on evidence; resolve against that turn's `user_time` + Track 3 zone / DST):

| Phrase family | Resolution |
|---|---|
| today | date of turn |
| this morning / afternoon / evening | date of turn (daypart ignored for stored precision unless Brian also gave a clock) |
| tonight | date of turn (evening) |
| last night | previous calendar date |
| yesterday | −1 day |
| the day before yesterday | −2 days |
| N days ago | −N days (N integer) |
| last `<weekday>` | most recent past that weekday strictly before turn date |
| on `<weekday>` | if unambiguous past in last 6 days; else `unknown` |
| explicit month+day (optional year) | that date; if year omitted, nearest past/equal in turn's year rules |

Anything else → `unknown`. Stored `event_time` = **date only** (`YYYY-MM-DD`) unless Brian stated a clock time in the evidence (then ISO local). Future calendar results → `unknown`.

### 6. Commit

One `BEGIN IMMEDIATE` transaction after `can_commit(token)` (Track 4 API):
- Insert episodes (`recorded_at=now`; `source_session_id` / `source_turn_start` / `source_turn_end` from pending range; times from those pending rows).
- Upsert entities/aliases per E9 (`norm = strip+casefold` exact on `entities.name` / `entity_aliases.alias`; create only when grounded + no hit; persist evidence substring names).
- Insert `episode_entities`, `episode_fact_refs`.
- Insert FTS rows (schema v2).
- Delete consumed pending ids.
- Zero-episode success also deletes those pending ids.
- On `can_commit` false → discard, log `consolidate.discard reason=generation_or_ids`, no pending delete.

### 7. Retry

Exponential backoff; `CONSOLIDATE_MAX_ATTEMPTS = 5`; then `consolidate.giveup` (counts only); pending kept; **one** more try at next `initialize`. LLM unavailable ≠ attempt.

### 8. Retrieval (`retrieve.py` + `prefetch`)

**Schema v2 FTS:** `episodes_fts` on summary; `entities_fts` (or query entities/aliases tables + join) for name/alias hits.

**Query:** tokenize current user message (distinctive terms); `MATCH` query; join entity name hits; score `rank_score = -bm25(...)` (higher better); keep `rank_score > EPISODE_MIN_SCORE` with **`EPISODE_MIN_SCORE = 0.0`**; return up to `MAX_EPISODES_PER_TURN = 3`.

**Filters:** Brian conversations only; every candidate through `is_suppressed`; no current facts.

**Exact prefetch text block** (fenced by Hermes as `<memory-context>`):

```
[Episodes]
- {YYYY-MM-DD or "date unknown"} ({relative age or "date unknown"}): {summary}
```

Relative age via Track 3 `format_relative` at read time. Empty → `prefetch` returns `""`.

### 9. Forget reach

Track 4 cascade extended to delete matching `episodes_fts` / `entities_fts` rows (content=`delete` + rebuild/optimize as needed) and `entity_aliases` with entities. Unit byte-scan after cascade includes FTS/alias tables. Paraphrase still prefers `episode_fact_refs` (FORGET matcher limit).

### 10. G-ERASE — propose **adopt** (Brian numbers from Phase 2 acceptance)

| Step | Where | Cost (E8) |
|---|---|---|
| `PRAGMA secure_delete=ON` | every `open_store` connection | ≈ +0.4 ms/erase |
| FTS `optimize` on affected FTS tables | synchronously after committed cascade | part of ≈ 1.7 ms with checkpoint |
| `wal_checkpoint(TRUNCATE)` | same path, after optimize | bundled ≈ 1.7 ms |
| One-time `VACUUM` | Phase 6 deploy only, after backup, offline/maintenance | re-scan expect **0** hits for Dana/Okafor/Vespa/Rosa/marathons/paints |

No logical/physical delay: sanitization runs inside/immediately after the cascade commit path on the worker (not on Brian's turn wait beyond existing cascade).

### 11. Log events (no content)

| Event | Fields |
|---|---|
| `zola_memory.pending_write` | session_id, pending_id, turn_index, ok |
| `zola_memory.consolidate` | trigger, turns, episodes, ok, attempt, elapsed_ms |
| `zola_memory.consolidate.giveup` | attempts, pending_count |
| `zola_memory.consolidate.discard` | reason |
| `zola_memory.consolidate.lease` | action=acquired\|renewed\|released\|busy, ok |
| `zola_memory.retrieve` | candidates, returned, top_score, elapsed_ms |

### Schema v2 (store migration)

- `schema_version = 2`
- `UNIQUE(session_id, turn_index)` on `pending_turns`
- `episodes_fts` (summary); entity name/alias FTS or covering indexes as implemented
- meta keys for consolidate lease
- `PRAGMA secure_delete=ON` on open

## Approved live changes

### Phase 5 approval (Brian + Claude, verbatim, 2026-10-05)

> Phase 5 approved with clarifications (Brian + Claude). Claude verified all 7 changed-file repo hashes match the deploy table.
> 1 Redeploy: approved as listed.
> 2+3 Exact order: (a) client closed; backup DB via sqlite3.backup + plugin folder, record hashes → (b) deploy → (c) launch; confirm schema v2 migration logged, then close the client fully → (d) VACUUM, then PRAGMA wal_checkpoint(TRUNCATE) → (e) byte-scan an offline copy of the .db AND the -wal for Dana/Okafor/Vespa/Rosa/marathons/paints (expect 0); also confirm integrity_check = ok and fact/tombstone counts unchanged → (f) relaunch; G6 recheck. No turns sent.
> 4 SOUL: none — approved.
> 5 Rollback: client closed; restore plugin folder AND the DB backup together, and delete any zola_memory.db-wal / -shm beside the restored file before relaunch (stale WAL must not replay onto the backup).
> Note for lore: the pre-deploy DB backup contains previously forgotten synthetic content by necessity; retention policy is a closeout item.
> proceed to phase 6

### Effective rulings (recorded)

1. Redeploy as listed (7 replace/add).
2+3. Exact order (a)–(f) as quoted; no turns.
4. SOUL: none.
5. Rollback: plugin + DB together; delete `-wal`/`-shm` beside restored DB before relaunch.
6. Lore closeout item: pre-deploy DB backup retains forgotten synthetic bytes by necessity — retention policy TBD at closeout.

## Backup hashes

Backup dir: `C:\Users\test\Dev\zola-spikes\p6-episodes\backup\` (2026-10-05)

| Artifact | SHA-256 |
|---|---|
| `zola_memory.db` (sqlite3.backup API, pre-deploy schema 1) | `2ba77741a08f37de1ba7009a9c27fecaa0012166c930435875309f91d2b8ce80` (155,648 bytes; facts=14, tombs=16) |
| `plugins_zola_memory/__init__.py` | `99eb18f3bedd5cc8abc408233e33b3d7eb591b1293397b7c5f1836bb293cd550` |
| `plugins_zola_memory/provider.py` | `c1dae292eeddddac3eec5bda82d2d9adc0098b2e0f2df3483f1d13dd23f3d108` |
| `plugins_zola_memory/forget.py` | `8bb9de8b7d98e3750a7f10bc9a1b019e63d6d42b0c39fcfd32f5bdea91045afd` |
| `plugins_zola_memory/fact_index.py` | `49d321a3b371ff61f5763a9b79acf187ea64caec0d04ee54bbbab793ee1afc0e` |
| `plugins_zola_memory/log.py` | `d274baba8d9a696c95fffc3b2e43a50974739662c18ef8a8b735a356e876faca` |
| `plugins_zola_memory/time_context.py` | `c3b61942358cccec6db422b31b7200c8d743c095779b144db9b174bf105bbf9f` |
| `plugins_zola_memory/registry.py` | `86aa4da04d67ab911d569ab1d9774a86e1a36f75f9b1931d49ca3f0272ee771d` |
| `plugins_zola_memory/store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` |
| `plugins_zola_memory/llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` |

## Deployed-file hash table

Live path: `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\` — all MATCH repo:

| File | Live SHA-256 | Match |
|---|---|---|
| `__init__.py` | `99eb18f3bedd5cc8abc408233e33b3d7eb591b1293397b7c5f1836bb293cd550` | ✅ unchanged |
| `provider.py` | `e0fa313c221307070968019db15da3d85fb08d71b768dd7cb1f6198bd4622827` | ✅ REPLACE |
| `forget.py` | `e24b3a35c8118e4ae75e0b4371b7f26e9a4500c2b892e09e23c44101e37b688b` | ✅ REPLACE |
| `log.py` | `c21391e87a77d4efa977e5bfd9f74c996b37f6b9aa5af647c5e1cce584dc9717` | ✅ REPLACE |
| `store.py` | `2e57f8d126ea298834a7aee81eaf63070b9555ec5519b0884dd8698643c989ed` | ✅ REPLACE |
| `pending.py` | `5b7cf7410222754d709075962e633494c2895bd75c8f3d0b1c6455ecf27d2278` | ✅ ADD |
| `consolidate.py` | `26b5daf64e71cba4ae12d92188cda061340c71d1bc0e8f50de24f6d8cbb6d67a` | ✅ ADD |
| `retrieve.py` | `6fd6ba6bd5e634d9bad0a33862ca51814bcb576dfb5657a6f0d9e39d108540b7` | ✅ ADD |
| `fact_index.py` | `49d321a3b371ff61f5763a9b79acf187ea64caec0d04ee54bbbab793ee1afc0e` | ✅ unchanged |
| `time_context.py` | `c3b61942358cccec6db422b31b7200c8d743c095779b144db9b174bf105bbf9f` | ✅ unchanged |
| `registry.py` | `86aa4da04d67ab911d569ab1d9774a86e1a36f75f9b1931d49ca3f0272ee771d` | ✅ unchanged |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | ✅ unchanged |

### Schema v2 + G-ERASE maintenance

| Check | Result |
|---|---|
| Initialize log (clean serve) | ✅ `2026-10-05 07:31:20` and post-VACUUM relaunch `schema_version=2 fts_ok=true import_count=0` |
| Post-maintenance live DB | SHA `8bbea030ab9989f3a8322f318e35911fff11334196e0801bb09e43a8f1f47ec5` (184,320 bytes); WAL/SHM absent after TRUNCATE |
| `integrity_check` | ✅ `ok` |
| facts / tombstones | ✅ 14 / 16 unchanged |
| Byte-scan (Dana/Okafor/Vespa/Rosa/marathons/paints) on offline `.db` + `-wal` | ✅ all 0 after FTS rebuild + VACUUM + checkpoint (see Phase 6 notes) |

### Unchanged surfaces

| Surface | SHA-256 | Status |
|---|---|---|
| `config.yaml` | `7ba2e676a04ff92047c8d711fcb022be8a532b11baac6f74b08986744e704570` | unchanged |
| Live `SOUL.md` | `e2b932a9d10dd6b9267530737fe8e438c8003b74032aeb21004093fd89b24d52` | unchanged (no SOUL this track) |
| `zola_tools/__init__.py` | `a1ef8541406f1a9c199cc8c8ce1bb7c71e087f4c3eaa2151dac7b59f04c33513` | unchanged |
| `zola_tools/calculator.py` | `0f29f3fc1e1d5eac3d1e4cef0bcf6428ef6497ee2af61bd86503602be80fe680` | unchanged |
| `zola_tools/plugin.yaml` | `f329e9065493f766712a018df14541172282666ef516ad3d45781b56ae1d2216` | unchanged |
| `hermes-agent` | HEAD `345cd2b0…`, porcelain empty | clean |

## G6 recheck

Offline after: `C:\Users\test\Dev\zola-spikes\p6-episodes\g6-phase6-after\`  
Baseline (Track 4 / FORGET 7c-after): `C:\Users\test\Dev\zola-spikes\p6-forget\g6-7b-7c-after\`  
Capture CWD matched baseline: `hermes-plugins\zola_memory\tests`  
Allowlisted per-session line (only): `Conversation started:`

| Check | Result |
|---|---|
| Tool-name set vs Track 4 | ✅ identical (20 tools) |
| Provider schemas | ✅ `['forget_memory']` only (unchanged) |
| System prompt after stripping allowlisted `Conversation started:` | ✅ identical |
| Live load | ✅ `initialize ok=true schema_version=2`; no turns sent (G-LIVE) |
| Offline G6-after is a second short-lived agent | noted (not a second live-serve load) |

## Phase 6 notes

- (a) Client closed; sqlite3.backup of live DB + full plugin folder → backup hashes above. Pre-deploy backup is schema 1 / facts=14 / tombs=16 and **contains forgotten synthetic bytes by necessity** (lore closeout retention item).
- (b) Redeployed 7 files (REPLACE/ADD); all live hashes MATCH repo; unchanged runtime files still MATCH.
- (c) First post-deploy client launch logged `schema_version=1` because long-lived `hermes_cli.main -p zola serve --isolated` retained old imported modules after Zola.Client kill. Killed both serve PIDs + client, cleared live `__pycache__`, relaunched → `initialize ok=true schema_version=2`. DB already had v2 tables from the fresh plugin path once serve reloaded.
- (d)(e) Client/serve fully closed. `VACUUM` then `wal_checkpoint(TRUNCATE)`. First byte-scan still had **2× `paints`** in orphaned `facts_fts` shadow pages (prior FORGET free/index remnants). Ran `optimize`+`rebuild` on `facts_fts` / `episodes_fts` / `entities_fts`, then `VACUUM` + `wal_checkpoint(TRUNCATE)` again → offline `.db` and `-wal` scans **0** for all six needles; `integrity_check=ok`; facts=14 / tombs=16 unchanged.
- (f) Relaunched; initialize `schema_version=2`; G6 PASS vs Track 4 baseline; no turns.
- SOUL: none. Rollback path recorded: restore plugin + DB together; delete `-wal`/`-shm` before relaunch.

### Phase 6 acceptance (Brian + Claude, verbatim, 2026-10-05)

> Phase 6 accepted (Brian + Claude). Record for lore: (1) a stale hermes serve process kept old plugin modules loaded (logged schema v1) — deploys must verify every Hermes process restarted; (2) VACUUM alone left a token in facts_fts internal segments; FTS rebuild cleared it.
> Phase 7 additions:
> - Confirm (file:line) that the cascade's G-ERASE step runs FTS optimize on facts_fts as well as episodes_fts / entities_fts whenever it touches them.
> - Every Part D/E byte scan covers the .db and -wal, and reports facts_fts/episodes_fts/entities_fts separately if any hit appears.
> - Before Part B, confirm exactly one Hermes serve process is running the deployed modules (log shows schema_version=2 from the current PID).
> proceed to phase 7

### Lore closeout inputs (from Phase 6 acceptance)

1. **Stale hermes serve:** killing only `Zola.Client` can leave `hermes_cli.main -p zola serve --isolated` running with old imported plugin modules (logged `schema_version=1` after v2 deploy). Deploys must verify **every** Hermes process for the profile restarted before trusting initialize/migration logs.
2. **FTS after VACUUM:** `VACUUM` alone left a `paints` token in `facts_fts` internal segments; `INSERT INTO facts_fts(facts_fts) VALUES('rebuild')` (plus episodes/entities rebuild) cleared it. Retention policy for the pre-deploy backup (forgotten synthetic content) remains a closeout item.

## Phase 7 additions (recorded)

### G-ERASE FTS optimize (file:line) — confirmed

| Site | Evidence |
|---|---|
| Cascade calls sanitize after successful commit | `forget.py` L672–676: `_store.sanitize_after_erase(conn)` |
| Sanitize always optimizes **all three** FTS tables | `store.py` L290–303: `sanitize_after_erase` loops `("facts_fts", "episodes_fts", "entities_fts")` and runs `INSERT INTO {table}({table}) VALUES('optimize')` (errors swallowed per-table) |
| Checkpoint | `store.py` L304–313: `wal_checkpoint(TRUNCATE)` then PASSIVE fallback; `commit` in `finally` L314–318 |

**Ruling:** whenever a cascade commits successfully, G-ERASE runs FTS `optimize` on `facts_fts` **and** `episodes_fts` **and** `entities_fts` (unconditional on the three names — not gated on which table was touched). Deletes for each table remain in the cascade body (`forget.py` L538 facts_fts; L592–594 episodes_fts; L630–632 entities_fts).

### Part D/E byte-scan rule

Every Part D/E scan: whole-file `.db` **and** `-wal`; if any needle hit appears, also report SQL-visible hits for `facts_fts` / `episodes_fts` / `entities_fts` separately (helper: `zola-spikes/p6-episodes/phase7_byte_scan.py`).

### Pre–Part B serve check

| Check | Result |
|---|---|
| `Zola.Client` | PID **8828** (started 2026-10-05 07:32:51) |
| Hermes serve tree | **one** instance: PID **21940** (venv, parent=8828) → child PID **10868** (uv cpython, parent=21940); both created 07:32:52 |
| No other hermes serve | ✅ no additional serve trees |
| Deployed modules | initialize at **07:33:01,685** `ok=true schema_version=2 fts_ok=true import_count=0` (matches this serve start; later 07:33:14 / 07:33:29 initialize+shutdown are offline G6 agents, not live serve) |

## Latency table

Offline copy of live store + **200 synthetic episodes**; deployed `retrieve.retrieve_episodes` (`platform=tui`); **32** realistic synthetic queries (warm 5 first).

| Metric | Value |
|---|---|
| median | **1.272 ms** |
| p95 | **1.741 ms** (target &lt; 50 ms) ✅ |
| min / max | 0.354 / 2.386 ms |
| Scratch | `zola-spikes/p6-episodes/phase7/latency_scratch.db` |

Live prefetch `elapsed_ms` collected per smoke turn in Parts B–C (log `retrieve` events).

## Part A baselines (Cursor, pre-Brian)

| Item | Value |
|---|---|
| Log offset at Part A start | **64357** |
| Log offset after Part A (smoke window start) | **67976** (Part A offline latency wrote metadata-only `retrieve` events to the live log; no content; no turns) |
| `schema_version` | 2 |
| facts / tombstones / episodes / pending / entities | **14 / 16 / 0 / 0 / 0** |
| `USER.md` SHA-256 | `47a732a0b218936c9b465f6bb8ada34bcda4fe027660f000e9b139b4e7022d12` (2156 bytes) |
| `MEMORY.md` SHA-256 | `8264268512e5cc7a37fff847f523ca142c310dbf21bef30c2ad601ee3a5986eb` (236 bytes) |

## Smoke tables (blind / recall / forget / paraphrase-forget)

### Part B — session S1 `20261005_073256_a2d789`

**Consolidation:** quiet-gap at 08:01:14–08:01:49; `trigger=quiet turns=8 episodes=3 ok=true attempt=1 elapsed_ms=34601`. Pending after: **0**.

| # | Scripted item | Expected episode? | Created? | Entities | fact_refs | event_time / basis / evidence | Notes |
|---|---|---|---|---|---|---|---|
| 1–3 | Larkspur + LoRa + antennas | Yes (one) | ✅ EP `8c0294b9…` turns 1–3 | Project Larkspur (project) | 2 | `null` / `unknown` / `null` | antennas in `open_items` ✅; significance=`decision` |
| 4 | 17% of 2,340 | No | ✅ none | — | — | — | pending kept then discarded in consolidate |
| 5 | weather | No | ✅ none | — | — | — | same |
| 6 | Miata shop yesterday | Yes (with #7 as open_item) | ⚠️ EP `744f93eb…` turn 6 only | '89 Miata (vehicle) | 1 | `null` / `unknown` / `null` | **FAIL:** no `stated`/`yesterday`; timing belt not attached |
| 7 | timing belt next month | open_item of #6 | ❌ separate EP `204ec43a…` turn 7 | '89 Miata (vehicle) | 2 | `null` / `unknown` / `null` | **FAIL:** own episode (significance=`plan`); "next month" not used as event_time ✅ |
| 8 | thanks | No | ✅ none | — | — | — | |

**Gating vs prompt Pass criteria:**

| Criterion | Result |
|---|---|
| Larkspur decision episode with accurate summary; antennas as open_item | ✅ (Brian judges wording) |
| Miata shop visit episode; timing belt as open_item not separate episode | ❌ split into 2 episodes |
| Items 4–5 produce none | ✅ |
| Miata `event_time` = yesterday’s date, basis=`stated`, evidence=`yesterday` | ❌ `unknown` / null |
| Larkspur `event_time` = `unknown` | ✅ |
| "next month" never an `event_time` | ✅ |

**Side effects:** facts 14→**18** (4 MEMORY facts: Larkspur×2, Miata×2); `MEMORY.md` hash changed `82642685…` → `38c0917c…` (551 bytes); `USER.md` unchanged.

**Verdict: smoke test failed** at Part B (do not loosen; do not add a writer). Part C+ not started.

## Phase 7 notes

- Phase 6 acceptance + lore inputs recorded; G-ERASE optimize file:line confirmed; Part D/E scan helper ready.
- Part A latency PASS; pre–Part B serve = one tree, `schema_version=2`.
- Part B: quiet consolidation ran; **FAIL** — Miata/timing-belt split + missing `yesterday` stated time. STOP for Brian.
- Phase 7-DIAG (read-only) completed below — no code or live changes.

## Phase 7-DIAG (read-only, 2026-10-05)

Scope: explain Part B Miata failures. No code/live changes. Session S1 `20261005_073256_a2d789`. Pending rows deleted at consolidate; reconstructed from `state.db` messages + log pending IDs + sync_turn assistant lengths. Raw consolidator JSON **not persisted** (`plugin_llm.complete_structured` logs metadata only: 08:01:49, 3235 tokens).

### D1 — `yesterday` / `event_time`

**Pending turn 6 `user_time`:** **PRESENT** (not NULL).

| Item | Value |
|---|---|
| Pending id | `9987b63d-e4c8-45d6-bbb6-b8e4766d0878` |
| `state.db` user message timestamp | float `1791211837.5515141` (= 2026-10-05T14:50:37.551514Z) |
| `resolve_user_time` result | `'1791211837.5515141'` (stringified float) |
| Stored `episodes.source_user_time` | same string |
| `pending_missing_user_time` log | none for S1 |
| Content match | ✅ normalized key equals message: `oh, and i took the '89 miata to the shop yesterday.` |

**Why not ISO:** `pending.resolve_user_time` (`pending.py` L78–84) only calls `time_context.marker_iso` when `timestamp` is a `datetime`; Hermes persists message timestamps as **unix floats**, so the code takes `str(ts)` unchanged.

**Raw model output for Miata episode(s):** **UNAVAILABLE** (not logged). Post-validation stored fields:

| Episode | `event_time` | `event_time_basis` | `event_time_evidence` |
|---|---|---|---|
| turn 6 shop (`744f93eb…`) | `null` | `unknown` | `null` |
| turn 7 timing belt (`204ec43a…`) | `null` | `unknown` | `null` |

**Did validation/resolution change them?**

- If the model returned `basis=stated` + `evidence=yesterday`: evidence would match the user turn (`consolidate.py` L639–644); then `resolve_stated_time` → `_parse_iso('1791211837.5515141')` returns `None` (`consolidate.py` L821–833) → **soft-downgrade** to `unknown`/`null`/`null` at L654–657. Consolidation still commits (`ok=true`). Replaying with the same float: `resolve_stated_time("yesterday", float_str)` → `None`; with `marker_iso`/UTC ISO of that instant → `2026-10-04` ✅.
- If the model returned `basis=unknown` originally: stored fields unchanged by resolution.

**Exact step that produced `unknown` (confirmed sufficient cause):** `consolidate.resolve_stated_time` fails at `_parse_iso` on unix-float `user_time` (`consolidate.py` L724–726 / L821–833), then validate soft-downgrades (`L654–657`). Cannot prove whether the model also omitted `stated`/`yesterday` — raw JSON absent; summary text also dropped “yesterday”.

### D2 — Split

Raw model JSON **UNAVAILABLE**. Fields validation **preserves** for significance / open_items / turn range (mapped to `source_turn_*` at commit):

| Episode | significance | source_turn_range (pending ids) | open_items |
|---|---|---|---|
| Shop visit | **`event`** | start=end `9987b63d…` (turn 6) | `[]` |
| Timing belt | **`plan`** | start=end `67a96d64…` (turn 7) | `["Have the shop replace the '89 Miata's timing belt next month."]` |

**Was significance `"plan"` used for the split one?** **Yes** — stored `significance='plan'` on the turn-7 episode; validate only accepts enum values and does not rewrite significance (`SIGNIFICANCE_VALUES` includes `"plan"`, `consolidate.py` L33–35 / L88–90).

**Instruction conflict:** `SUMMARIZER_INSTRUCTIONS` L57 says open items/future plans belong in `open_items` on the parent episode — but the schema enum advertises `"plan"` as a first-class significance, inviting a separate plan episode.

### D3 — fact_refs

Consolidation snapshot: **2026-10-05T08:01:49-07:00** (= 15:01:49Z).

| Fact ID | target | `learned_at` / `indexed_at` (UTC) | vs snapshot |
|---|---|---|---|
| `23e99d43-8729-4707-a439-eed76d435e3f` | memory | 2026-10-05T14:49:22Z | before ✅ |
| `44f28fd5-6ef5-48c6-a9a5-4932dca0e0e7` | memory | 2026-10-05T14:49:37Z | before ✅ |
| `f8cbbe0c-5c5e-49ad-a860-abb7fcf803b1` | memory | 2026-10-05T14:50:43Z | before ✅ |
| `1eaf3ace-726a-4624-8519-c170f003ec6d` | memory | 2026-10-05T14:50:59Z | before ✅ |

| Episode | fact_refs |
|---|---|
| Larkspur `8c0294b9…` | `23e99d43…`, `44f28fd5…` |
| Miata shop `744f93eb…` | `f8cbbe0c…` |
| Timing belt `204ec43a…` | `f8cbbe0c…`, `1eaf3ace…` |

**Were the facts in the active-fact input?** **Yes** — all four were active before consolidate; `_build_model_input` lists every `state=active` fact (`consolidate.py` L506–511). Pre-existing non-smoke facts were also listed (14 prior + 4 new = 18).

### D4 — Model input block (reconstructed)

Assistant lines match sync_turn lengths from the log; `user_time` values match `resolve_user_time` on live message timestamps; `ENTITIES:` empty (pre-commit). Non-smoke ACTIVE_FACTS **texts** redacted below (IDs kept); unredacted spike copy: `zola-spikes/p6-episodes/phase7/diag/model_input_reconstructed_FULL.txt` (do not commit).

```
PENDING_TURNS:
- id=8424133b-8cce-4e99-b571-2cefc6b94ec1 user_time=1791211749.185312
  user: Hey, quick update on Project Larkspur, the garden irrigation controller I've been building.
  assistant: Got it. I'll remember Project Larkspur is your garden irrigation controller.
- id=1e60d7e7-2efb-4ab8-b53b-b25e2011b33e user_time=1791211773.0490816
  user: We decided to drop Wi-Fi and switch the sensors to LoRa radios. Range was the deciding factor.
  assistant: Right—LoRa for the sensors, not Wi‑Fi. Range made the call. I'll remember that.
- id=8b7ee1b6-eea4-4d49-9109-7341fcdd87af user_time=1791211790.2572935
  user: Still need to order the antennas, though.
  assistant: The antennas are still outstanding.
- id=947c8d56-61ca-4437-9d03-7ebb08d0120d user_time=1791211801.9561691
  user: Unrelated, but what's 17% of 2,340?
  assistant: 397.8
- id=2960b529-3969-4ed5-828d-3a0c8b46a83c user_time=1791211823.4247687
  user: The weather's been weird this week.
  assistant: It has. October's apparently trying a few different personalities at once.
- id=9987b63d-e4c8-45d6-bbb6-b8e4766d0878 user_time=1791211837.5515141
  user: Oh, and I took the '89 Miata to the shop yesterday.
  assistant: I'll remember the '89 Miata.
- id=67a96d64-4af1-4209-839a-d78980066971 user_time=1791211853.8592691
  user: The plan is to have them replace the timing belt next month.
  assistant: Timing-belt replacement for the Miata next month. I'll remember that.
- id=f5019cd4-cbcf-47f5-8a6e-b780dcc0e3cd user_time=1791211870.9549966
  user: That's it for now, thanks!
  assistant: Anytime.
ENTITIES:
ACTIVE_FACTS:
- id=05cdeb73-702e-40bb-8f5b-6aa92bfa5d5e target=user text=[REDACTED non-smoke fact, len=242]
- id=0e1fb237-4db7-40c7-a07a-b90547ebf119 target=user text=[REDACTED non-smoke fact, len=31]
- id=1687b46d-91f0-46f4-8ad4-f087b1a56e19 target=user text=[REDACTED non-smoke fact, len=194]
- id=1eaf3ace-726a-4624-8519-c170f003ec6d target=memory text=[car] The 1989 Miata is planned to have its timing belt replaced in November 2026.
- id=20c35349-df06-4bfb-8b27-91494c28dbe2 target=user text=[REDACTED non-smoke fact, len=265]
- id=23e99d43-8729-4707-a439-eed76d435e3f target=memory text=[project] Project Larkspur is Brian's garden irrigation controller project.
- id=44f28fd5-6ef5-48c6-a9a5-4932dca0e0e7 target=memory text=[project] Project Larkspur sensors use LoRa radios rather than Wi‑Fi; range was the deciding factor.
- id=450e1589-be30-42c5-aebc-47bfc9aacb84 target=user text=[REDACTED non-smoke fact, len=133]
- id=4dfdb19c-3b14-4eb1-ba16-834f4de729ba target=memory text=[REDACTED non-smoke fact, len=234]
- id=6e9a3c9f-f1f4-4d1f-8c8b-36e7f58cf4e7 target=user text=[REDACTED non-smoke fact, len=167]
- id=76ba176d-8497-4cc2-a91f-471b3b706d5b target=user text=[REDACTED non-smoke fact, len=127]
- id=843f4f1c-2e94-4925-9cd6-9f712e86f370 target=user text=[REDACTED non-smoke fact, len=219]
- id=9fe25847-7228-4156-850f-8d2caaba9151 target=user text=[REDACTED non-smoke fact, len=154]
- id=ba1edef8-e870-4eea-b2a1-9424e188b146 target=user text=[REDACTED non-smoke fact, len=199]
- id=c5f15c59-f2e7-4765-aa67-602d418f4a45 target=user text=[REDACTED non-smoke fact, len=189]
- id=d9bed5dd-0114-4b61-8784-2ae4b25d6427 target=user text=[REDACTED non-smoke fact, len=78]
- id=f7bfe61b-6c48-4ae0-8c0e-85429eab995b target=user text=[REDACTED non-smoke fact, len=74]
- id=f8cbbe0c-5c5e-49ad-a860-abb7fcf803b1 target=memory text=[car] Brian owns a 1989 Miata.
```

Note: every `user_time` in the input is a unix float string — the model sees non-ISO times; resolution also cannot parse them.

### Proposed smallest fixes (do not build)

| ID | Confirmed cause | Smallest fix (proposal only) |
|---|---|---|
| D1 | `resolve_user_time` stores unix floats; `_parse_iso` cannot parse them → stated times soft-downgrade to `unknown` | In `pending.resolve_user_time`, normalize numeric/`float`-string timestamps with `time_context.marker_iso(datetime.fromtimestamp(...))` (same as `datetime` branch). Optionally mirror accept in `_parse_iso`. Unit test: float timestamp + evidence `yesterday` → date yesterday. |
| D2 | Model emitted separate episode with `significance="plan"`; enum invites it despite open_items rule | (a) Remove `"plan"` from `SIGNIFICANCE_VALUES` / schema enum **or** keep it but add one concrete example in `SUMMARIZER_INSTRUCTIONS`: shop visit + “timing belt next month” → **one** episode, belt in `open_items`, not a second episode. (b) Prefer (a)+(example): smallest behavior change with least reliance on model luck. |
| D3 | Facts were present; refs OK — two Miata MEMORY facts may still nudge a split | Add one instruction line: multiple fact_refs about the same vehicle/event belong on **one** episode; do not split per fact. No fact-pipeline change. |

**PHASE 7-DIAG COMPLETE** — accepted; fixes built below.

### Phase 7-DIAG acceptance → 7-FIX (Brian + Claude, verbatim, 2026-10-05)

> 7-DIAG accepted (Brian + Claude). Build Phase 7-FIX (repo → redeploy per P4-D25):
> F1 Time normalization at the source: pending writer converts Hermes message timestamps (unix float/int, ISO string, or datetime) to ISO-8601 local with offset (Track 3 localize rules) for user_time AND assistant_time before storing. Unparseable → NULL (X4). This also fixes episodes.source_user_time (the recall "talked about" side would have shown "date unknown"). Tests MUST use Hermes' real message shape (role/content/timestamp as unix float) — add a fixture from the live messages structure.
> F2 No silent downgrade: when a stated phrase is in the approved table but resolution fails, keep the episode with basis unknown (unchanged behavior) but log zola_memory.consolidate.time_unresolved with a reason code (unparseable_user_time | phrase_not_in_table | future | other). Counts only.
> F3 Split: keep significance "plan". Add to the instruction text: "A plan, next step, or follow-up about the same thing as an event or decision in this stretch belongs in that episode's open_items, not in its own episode. A plan is its own episode only when nothing else in the stretch is about the same thing." Plus one worked example (synthetic, not the smoke wording): a car taken in for brakes + "they'll do the tires next week" → ONE episode, event + open_item.
> F4 The proposed fact_ref line ("don't split an episode per fact_ref") — approved.
> Rerun both suites; show the instruction diff and hashes at a STOP (7-FIX COMPLETE). Then, after approval: redeploy (all Hermes processes restarted, schema/log PID check), then cleanup + rerun:
>  C1 Brian (S1 conversation or new): "Forget everything about Project Larkspur and the Miata." → Cursor verifies: 4 MEMORY facts removed via memory tool, all 3 episodes erased by cascade (fact refs/terms), tombstones, byte scan .db + -wal clean.
>  C2 Brian reruns the S1 8-message script in a NEW conversation; 10-minute gap; blind table as before.

## Phase 7-FIX (repo only — not deployed)

### Instruction diff (`SUMMARIZER_INSTRUCTIONS`)

```diff
--- SUMMARIZER_INSTRUCTIONS (pre-7-FIX)
+++ SUMMARIZER_INSTRUCTIONS (7-FIX)
@@ -7,6 +7,9 @@
 - Never create, invent, or rewrite lasting notebook facts. You may only reference existing fact IDs from the provided list.
 - Do not create an episode merely because Zola restated or recalled something from memory context. Only something new that happened or was decided in the source turns justifies an episode.
 - Open items and future plans belong in open_items on the episode they belong to — not as their own episodes.
+- A plan, next step, or follow-up about the same thing as an event or decision in this stretch belongs in that episode's open_items, not in its own episode. A plan is its own episode only when nothing else in the stretch is about the same thing.
+- Example: Brian says he took the car in for brakes, then that they'll do the tires next week → ONE episode (the shop visit), with the tire work as an open_item — not a second episode.
+- Multiple fact_refs about the same thing belong on one episode; do not split an episode per fact_ref.
 - Entity names and aliases must appear exactly as written in the source turns or in the provided active facts (no expanding abbreviations or inventing canonical names).
```

### Code changes

| ID | Change |
|---|---|
| F1 | `pending.normalize_message_timestamp`; `resolve_user_time` / `resolve_assistant_time` normalize unix float/int, ISO string, datetime → local ISO with offset; unparseable → NULL |
| F2 | `resolve_stated_time_with_reason`; validate soft-downgrade logs `zola_memory.consolidate.time_unresolved reason=… count=1` |
| F3 | Instruction: plan→open_items rule + brakes/tires example; significance `"plan"` kept |
| F4 | Instruction: do not split an episode per fact_ref |

### Repo hashes (7-FIX)

| File | SHA-256 | bytes |
|---|---|---|
| `pending.py` | `9ff6156cd946c08bfd737edffc15c6dae2d865ab0c34ed332f48056dda854769` | 8151 |
| `consolidate.py` | `749fc086c821dd4b8bdcdfc1acd2e3370cf4b1e80c7e2a7337fe979cf6b0d8f3` | 38477 |
| `log.py` | `a274d356bbf0329804537ea642038edc27fa7a45a5763a1810e6d133a8f5ea0b` | 4091 |
| `tests/test_episodes_phase4.py` | `8db12063993b04080faa241ad09704dab8493aae81fb5e2565f550c15c452037` | 38834 |

### Suites

| Suite | Result |
|---|---|
| `zola_memory` | Ran **102** tests — OK |
| `zola_tools` | Ran **44** tests — OK |

Nothing deployed. Live profile untouched.

**PHASE 7-FIX COMPLETE** — approved and redeployed (below).

### 7-FIX approval (Brian + Claude, verbatim, 2026-10-05)

> 7-FIX approved (Brian + Claude). Claude verified hashes (pending 9ff6156c…, consolidate 749fc086…, log a274d356…) and that a Hermes unix-float user timestamp normalizes to 2026-10-05T07:50:37-07:00; instruction lines present.
> Proceed: redeploy (backup first; all Hermes processes restarted; confirm schema_version=2 + current PID in log; G6 recheck), then C1/C2…

### 7-FIX redeploy (2026-10-05)

Backup: `zola-spikes/p6-episodes/backup_7fix/` — DB `e6d1991f…` (192512 B; schema=2; facts=18; tombs=16; episodes=3); pre-FIX plugin hashes recorded.

| File | Live SHA-256 | Match repo |
|---|---|---|
| `pending.py` | `9ff6156cd946c08bfd737edffc15c6dae2d865ab0c34ed332f48056dda854769` | ✅ |
| `consolidate.py` | `749fc086c821dd4b8bdcdfc1acd2e3370cf4b1e80c7e2a7337fe979cf6b0d8f3` | ✅ |
| `log.py` | `a274d356bbf0329804537ea642038edc27fa7a45a5763a1810e6d133a8f5ea0b` | ✅ |

| Check | Result |
|---|---|
| All Hermes stopped before deploy | ✅ |
| Relaunch | `Zola.Client` PID **24400**; serve **21508→21984** (created 08:21:26) |
| Initialize | ✅ `schema_version=2 fts_ok=true import_count=0` (new serve) |
| G6 tools / provider | ✅ identical (`forget_memory` only) |
| G6 prompt | ⚠️ differs only by Part B smoke MEMORY facts (Larkspur×2, Miata×2) + allowlisted `Conversation started:` — expected until C1; not a plugin/SOUL delta |

### C1 cleanup (session `20261005_082138_15e223`)

Brian: "Forget everything about Project Larkspur and the Miata." She removed via **memory tool** (`reason=remove`); `forget_tool confirm=false` then returned 0 candidates.

| Check | Result |
|---|---|
| 4 MEMORY facts erased | ✅ `23e99d43…`, `44f28fd5…`, `f8cbbe0c…`, `1eaf3ace…` — `fact_erase reason=remove` |
| Episodes erased | ✅ **3** total via cascade **fact_refs**: remove `23e99d43` → `episode_rows=1` (Larkspur); remove `f8cbbe0c` → `episode_rows=2` (both Miata eps); the other two fact removes → `episode_rows=0` (already gone). Not term-only. |
| Entities / refs | ✅ 0 / 0 |
| Tombstones | 16 → **20** (+4) |
| facts | 18 → **14** |
| `MEMORY.md` | ✅ back to Part A `82642685…` (236 B); `USER.md` unchanged `47a732a0…` |
| Byte-scan after cascade (client still open) | ⚠️ free-page + WAL remnants (SQL-visible 0; FTS match 0) |
| Offline G-ERASE maintenance | FTS optimize+rebuild + `VACUUM` + `wal_checkpoint(TRUNCATE)` → `.db` and `-wal` **0** for Larkspur/LoRa/antennas/Miata/timing belt; `integrity_check=ok` |

### C2 re-smoke — session `20261005_082710_3be6ca` (7-FIX live)

**Consolidation:** quiet-gap 08:40:17–08:40:30; `trigger=quiet turns=8 episodes=2 ok=true attempt=1 elapsed_ms=13148`. Pending after: **0**.  
**`consolidate.time_unresolved`:** **none** in the C2 window.

#### Pending rows (consumed; `user_time` reconstructed = normalized ISO from Hermes unix float)

| turn | pending_id | user_time (ISO) |
|---|---|---|
| 1 | `cc752efc-f61c-44a1-a795-879fecc5b356` | `2026-10-05T08:28:43-07:00` |
| 2 | `1a5c09de-d33e-40f3-b618-d17826261e75` | `2026-10-05T08:28:57-07:00` |
| 3 | `3872bdad-c604-4f61-b8fd-d11ab2b3c1f5` | `2026-10-05T08:29:14-07:00` |
| 4 | `35d3887a-8abc-4153-83a1-0f18e3311f06` | `2026-10-05T08:29:24-07:00` |
| 5 | `2e0c712d-376a-4a2e-891f-26c0b79a2e43` | `2026-10-05T08:29:39-07:00` |
| 6 | `bfcdfa54-64fe-4dd5-a6de-8765d5b75e9f` | `2026-10-05T08:29:53-07:00` |
| 7 | `684a02ca-f3f4-47c1-93f8-aae3fe713de6` | `2026-10-05T08:30:04-07:00` |
| 8 | `43d9abd6-07a3-41e6-9303-07397152011d` | `2026-10-05T08:30:14-07:00` |

#### Blind table

| # | Scripted item | Expected episode? | Created? | Entities | fact_refs | event_time / basis / evidence | source_user_time | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | Larkspur intro | part of Larkspur | absorbed into EP1 (range starts turn 2) | — | — | — | turn1 ISO above | no solo episode |
| 2–3 | LoRa + antennas | Yes (one) | ✅ EP `bbe7265f…` turns **2–3** | Project Larkspur (project) | `8d03ecaa…`, `31e329a4…` | `null` / `unknown` / `null` | `2026-10-05T08:28:57-07:00` | open_items: Order the LoRa antennas; sig=`decision` |
| 4 | 17% of 2,340 | No | ✅ none | — | — | — | ISO above | |
| 5 | weather | No | ✅ none | — | — | — | ISO above | |
| 6–7 | Miata shop + timing belt | Yes (one; belt=open_item) | ✅ EP `eb1130fb…` turns **6–7** | '89 Miata (vehicle) | `56a85bd0…`, `867442fe…` | **`2026-10-04` / `stated` / `yesterday`** | `2026-10-05T08:29:53-07:00` | open_items: replace timing belt next month; sig=`event`; **not split** |
| 8 | thanks | No | ✅ none | — | — | — | ISO above | |

#### Gating vs Part B Pass criteria

| Criterion | Result |
|---|---|
| Larkspur decision episode; antennas as open_item | ✅ |
| Miata shop + timing belt as **one** episode (belt=open_item) | ✅ (was ❌ pre-7-FIX) |
| Items 4–5 produce none | ✅ |
| Miata `stated` / `yesterday` → yesterday’s date | ✅ `2026-10-04` |
| Larkspur `event_time` unknown | ✅ |
| "next month" never an `event_time` | ✅ |
| ISO `user_time` / `source_user_time` | ✅ all pending + both episodes |
| `time_unresolved` | ✅ none |

**Summaries (Brian judges; not committed as lore):**
1. *For Project Larkspur, Brian decided to drop Wi-Fi and switch the sensors to LoRa radios because range was decisive.* · open: Order the LoRa antennas.
2. *Brian took the '89 Miata to the shop yesterday; the timing belt is planned for replacement next month.* · open: Have the shop replace the timing belt next month. · happened: 2026-10-04 (stated: yesterday)

**C2 blind table STOP** — accepted; Part C + 7-ERASE-DIAG below.

### C1 acceptance note (Brian + Claude, 2026-10-05)

> C1 accepted as LOGICAL pass (Brian + Claude): erasure via fact_refs ✅, counts ✅. But G-ERASE FAILED automatically: bytes remained in .db/-wal after the cascade and needed a manual FTS rebuild + VACUUM. That is a defect against the approved G-ERASE (per-forget secure_delete + FTS optimize + wal_checkpoint(TRUNCATE), no logical/physical delay). Manual cleanup must not be used again during the smoke without reporting it as a failure.
> Run Part C now… In parallel, Phase 7-ERASE-DIAG… Propose the fix. Report with the C4 STOP. No code changes until approved; fix + redeploy must land before Part D.

### Part C baselines (pre-Brian, Cursor)

| Item | Value |
|---|---|
| Log offset | **90313** (`log_offset_part_c.txt`) |
| episodes / facts / tombs | **2 / 18 / 20** |
| `USER.md` | `47a732a0…` (2156) |
| `MEMORY.md` | `ee38fefe…` (583) — includes C2 smoke MEMORY facts |

## Phase 7-ERASE-DIAG (read-only)

### E-a — `PRAGMA secure_delete`

| Finding | Evidence |
|---|---|
| Set **per connection** in `store.open_store` | `store.py` L78–79: `PRAGMA secure_delete=ON` after connect |
| **Not** persisted in the DB file | Fresh RO `sqlite3.connect(…?mode=ro)` on live DB returns **`secure_delete=0`** (probed 2026-10-05) |
| Cascade connection | Provider `_conn` from `open_store` at initialize → **should be ON** for the live serve connection |
| Not logged | No `secure_delete` field on `forget_cascade` / sanitize events — **cannot prove from log** that the C1 cascade connection had ON |
| Other processes | Any raw/`mode=ro` opener (offline G6 `AIAgent`, ad-hoc scripts) gets default **OFF** unless they call `open_store` |

Scratch: connection with `secure_delete=ON` reports `(1,)`; second connection on same file reports `(0,)` until set.

### E-b — Did sanitize run on memory-tool remove?

| Path | Evidence |
|---|---|
| memory `remove` → `_notify_remove` → `forget.erase_fact` | `fact_index.py` L227–228 |
| `erase_fact` → `forget_cascade` | `forget.py` L708–721 |
| After successful `COMMIT`, `sanitize_after_erase(conn)` | `forget.py` L672–676 → `store.py` L290–318 |
| Same path for `forget_memory` tool | `forget_cascade` shared (`forget.py` ~L1109) |

**C1 log evidence:** four `forget_cascade reason=remove … ok=true` at 08:25:24 (one per MEMORY fact) — cascade completed; sanitize is **invoked** on that path but **emits no log line** (no sanitize/checkpoint event exists today). So: code path **yes**; runtime proof of optimize/TRUNCATE **missing**.

### E-c — `wal_checkpoint(TRUNCATE)` return

| Finding | Evidence |
|---|---|
| Return tuple not logged | `store.sanitize_after_erase` L306–308: reads `(busy, log, checkpointed)` but only uses `busy != 0` to fall back to **PASSIVE**; no `write_event` |
| Silent PASSIVE fallback | L307–308, L310–313 — busy/partial TRUNCATE becomes PASSIVE **without logging** |
| C1 context | Client/serve still open during cascades (PID tree alive at verify time). Second openers (RO probes, prior G6) possible |
| Scratch | Per-connection semantics confirmed; TRUNCATE while a second conn holds the file can leave WAL frames depending on SQLite reader state |

**C1 captured return:** **unavailable** (not logged). Inference: WAL still held Larkspur/Miata bytes immediately post-cascade ⇒ TRUNCATE did **not** fully clear the WAL (busy/partial and/or PASSIVE fallback).

### E-d — Where remnants lived

| Location | Evidence (C1 post-cascade, pre-manual cleanup) |
|---|---|
| SQL-visible tables | **0** hits (facts/episodes/pending/entities empty of needles; FTS MATCH 0) |
| `.db` whole-file | Larkspur 12, LoRa 6, antennas 4, Miata 14, timing belt 6 — **free pages / FTS shadow segments** (not queryable rows) |
| `-wal` | Larkspur 3, LoRa 3, antennas 2, Miata 19, timing belt 10 — **WAL frames** not truncated away |
| Cleared only by | Manual `optimize`+`rebuild` all FTS + `VACUUM` + `TRUNCATE` (reported as G-ERASE **failure**, not acceptable smoke maintenance) |

Unit-test gap: `test_cascade_clears_fts_and_bytes` closes the writer and checkpoints from a **fresh** connection after cascade (`test_episodes_phase4.py` ~L879–888) — stronger than production long-lived serve sanitize alone.

### Proposed fix (do not build until approved)

1. **Log G-ERASE telemetry (counts only):** in `sanitize_after_erase`, log e.g. `zola_memory.sanitize_after_erase` with `secure_delete=<0|1>`, `checkpoint_busy=`, `checkpoint_log=`, `checkpoint_frames=`, `fallback_passive=<bool>`, `fts_optimize_ok` counts. Fail closed visibility for E-a/E-c next time.
2. **FTS: `rebuild` when cascade deleted FTS rows** (not optimize-only): if `fts_rows > 0` (or always after successful erase), `INSERT INTO {fts}({fts}) VALUES('rebuild')` for each touched table (`facts_fts` / `episodes_fts` / `entities_fts`). Addresses free-page/segment tokens that `optimize` left (Phase 6 `paints` + C1). Keep sync; no VACUUM on the per-forget path.
3. **Checkpoint: no silent PASSIVE:** if `TRUNCATE` returns `busy != 0` or `log > checkpointed`, log WARNING and **retry TRUNCATE once**; if still busy, log `ok=false` reason=`checkpoint_busy` (still return from sanitize without raising — erase already committed) so smoke can gate on it. Do not hide PASSIVE.
4. **Tests:** whole-file byte scan on the **same long-lived connection** after cascade+sanitize (no close/reopen cheat); multi-connection busy case expects WARNING log; `secure_delete` asserted on provider conn before delete.
5. **Out of scope for per-forget:** one-time `VACUUM` remains deploy/maintenance only — must not be required after each forget if (2)+(3) hold.

**Approved as 7-ERASE-FIX** (Brian + Claude). Built below; **not deployed**.

### Part C script (Brian — NEW conversation S2)

1. `What did we decide about Project Larkspur?`
2. Associative (one at a time):  
   - `What did I settle on for the wireless setup in my garden watering gadget?`  
   - `Is there anything I still need to buy for that watering project?`  
   - `When was my old roadster last in for service?`  
   - `What maintenance is coming up for my convertible?`
3. `What's a good movie for tonight?`
4. Then **≥10 quiet minutes** (no Part D yet). Say **done** — Cursor verifies C4 (no restatement episodes; fact/USER/MEMORY hashes unchanged) and stops with C4 + erase-diag fix proposal.

## Part C table (recall)

Brian's verdicts (verbatim, closeout): C2 summary accuracy **"good"**; Part C answers 1–6 **"good"**.

Session: `20261005_082710_3be6ca` (continued S2; turns 9–14). `session_search`: **0** calls in agent.log Part C window.

| # | Question | Episode in prefetch? | Correct in top 3? | Irrelevant in top 3 | Score (live log) | She said "when"? | Brian |
|---|---|---|---|---|---|---|---|
| Q1 | What did we decide about Project Larkspur? | ✅ yes (`returned_len=225`; Larkspur ep) | ✅ Larkspur `bbe7265f…` only | none | `candidates=1 returned=1 top_score=1.0` | ❌ no ("when" not in answer; decision+open antennas only) | good |
| Q2 | …wireless setup in my garden watering gadget? | ❌ `returned_len=0` | ❌ | — | `candidates=0 returned=0 top_score=0` | — | good |
| Q3 | …still need to buy for that watering project? | ❌ `returned_len=0` | ❌ (1 candidate gated out) | — | `candidates=1 returned=0 top_score=0.0` | — | good |
| Q4 | When was my old roadster last in for service? | ❌ | ❌ | — | `candidates=0 returned=0 top_score=0` | — | good |
| Q5 | What maintenance is coming up for my convertible? | ❌ | ❌ | — | `candidates=0 returned=0 top_score=0` | — | good |
| Q6 | What's a good movie for tonight? | ✅ none — **no `<memory-context>`** | n/a | n/a | `candidates=0 returned=0 top_score=0` `returned_len=0` | — | good |

Her answers (for context; Brian unscored): Q1 LoRa decision+antennas (no when); Q2 LoRa/garden (from session history, not prefetch); Q3 order antennas; Q4 yesterday/Miata; Q5 timing belt next month; Q6 *Ford v Ferrari* (no memory block).

### Shared-word counts (4 associative × stored summaries)

Stopwords stripped; casefold. Summaries: Larkspur=`bbe7265f…`, Miata=`eb1130fb…`.

| Q | Query ∩ Larkspur summary | Query ∩ Miata summary |
|---|---|---|
| Q2 garden watering wireless | **0** `[]` | **0** `[]` |
| Q3 watering project buy | **1** `['project']` | **0** `[]` |
| Q4 roadster service | **0** `[]` | **0** `[]` |
| Q5 convertible maintenance | **0** `[]` | **0** `[]` |

Associative top-3: **0/4** (prefetch miss on all four; answers may still have been right from same-session history).

## Part C4 — no-recursion (post quiet gap)

Session `20261005_082710_3be6ca` (same as C2). Quiet consolidator: `09:11:33` `trigger=quiet turns=6 episodes=0 ok=true attempt=1 elapsed_ms=2614`.

| Check | Result |
|---|---|
| New episodes from Part C restatement / associative / movie | ✅ **none** (`episodes=0` on quiet run) |
| Episode count | ✅ still **2** (`bbe7265f…` Larkspur, `eb1130fb…` Miata) — both `source_session_id=20261005_082710_3be6ca` recorded at C2 consolidate |
| facts active | ✅ **18** (unchanged from Part C baseline) |
| `USER.md` | ✅ `47a732a0b218936c9b465f6bb8ada34bcda4fe027660f000e9b139b4e7022d12` (2156) |
| `MEMORY.md` | ✅ `ee38fefea7be8863692951a4bbae68a452d47178fc5e6d9e978076aed0bf4bb7` (583) |
| G-NO-RECURSION | ✅ PASS — retrieve/prefetch during Part C did not create restatement episodes |

## Phase 7-ERASE-FIX COMPLETE (not deployed)

Deferred physical sanitization: **APPROVED** (Brian). Repo-only; live plugin unchanged until redeploy approval.

### 1 — Log `secure_delete` + checkpoint tuple (no silent PASSIVE)

| Change | Detail |
|---|---|
| `zola_memory.store_open` | Every `open_store`: `pid`, `secure_delete`, `sqlite_version`, `fts_secure_delete` |
| `zola_memory.sanitize_after_erase` | `secure_delete`, `fts_mode`, `fts_ms`, `checkpoint_busy/log/frames`, `sanitize_pending`, `ok`, `elapsed_ms` |
| PASSIVE | **removed** — busy TRUNCATE → `meta.sanitize_pending=1` + WARNING `sanitize_retry action=defer` |

### 2 — FTS secure-delete or rebuild

| Runtime | Behavior |
|---|---|
| SQLite **3.53.1** (Hermes venv) ≥ 3.44 | On open: `INSERT INTO {fts}({fts}, rank) VALUES('secure-delete', 1)` for `facts_fts` / `episodes_fts` / `entities_fts`; `meta.fts_secure_delete=1`; after cascade: `optimize` + timed `fts_ms` |
| Older / secure-delete fails | `meta.fts_secure_delete=0`; after cascade: `rebuild` on touched FTS tables + timed `fts_ms` |

### 3 — Deferred physical sanitize (APPROVED)

| Hook | Trigger string |
|---|---|
| `on_turn_start` | `on_turn_start` |
| `file_check` | `file_check` |
| consolidator run | `consolidate` |

Logical erase remains immediate (SQL rows gone; no retrieval/recall). Physical: retry `wal_checkpoint(TRUNCATE)` until success; log each attempt + `action=success`.

**Critical fix found in build:** FTS `optimize`/`rebuild` left an open write transaction; TRUNCATE then returned `busy=1` **with no second reader**. Sanitize now **commits FTS DML before TRUNCATE**.

### 4 — C1 reader identification

| Question | Finding |
|---|---|
| Phase 6 dual Hermes process as C1 reader? | **No.** At cascade `08:25:24`, only live serve initialize `08:21:48` was open. Offline G6 `AIAgent` `08:22:02` initialize→shutdown already gone. Client does not open the store (E6). |
| What blocked physical erase? | (a) FTS `optimize`-only left shadow/free-page tokens in `.db` (same class as Phase 6 `paints`); (b) **open write txn after optimize** → TRUNCATE `busy=1` → silent **PASSIVE** left `-wal` frames. Not a second live process. |
| Dual PID tree | Venv parent + uv child is one logical agent; only the child opens `open_store`. |

### 5 — Tests

| Test | Covers |
|---|---|
| `test_cascade_clears_fts_and_bytes` | Long-lived provider conn; `secure_delete=1` + FTS secure-delete; cascade+sanitize; whole-file `.db` + `-wal` = 0; `sanitize_pending=0` |
| `test_truncate_busy_defers_then_retry_clears_bytes` | Second open reader → first attempt `sanitize_pending=1` + `action=defer`; close reader + `try_pending_sanitize` → `action=success`; byte scan 0 |

### Repo file hashes (7-ERASE-FIX)

| File | SHA-256 |
|---|---|
| `store.py` | `2868d2a3b089a410aa7c7851c699576afc0e69e7fba04a44b603b1f286f26021` |
| `forget.py` | `adc873c555a3b323821836984bb3ed6680e36c2de9b5c10bf743b1366f423ac7` |
| `log.py` | `75c08ef59171e930cf2763b8dc82481958027a35adb7b8d8887393337b940a33` |
| `provider.py` | `e292093763665b0a35e38c67166f84e372493d4f4016704f006217a15e76a18a` |
| `fact_index.py` | `8eae48cb2202e778b5ff86567cc1ace73ac7957116e98880b3e2ed2982ff93f4` |
| `consolidate.py` | `6ebd759fa4d4fa37b4ffb443d5e228bba4276ead23ec538c899a786248265fff` |
| `tests/test_episodes_phase4.py` | `1032744e20e8abda24536feb501f9a7005e4f6ec3694294cbd50780a69fcfec9` |

### Suites (post-fix)

| Suite | Result |
|---|---|
| `zola_memory` | Ran **103** tests — OK |
| `zola_tools` | Ran **44** tests — OK |

**7-ERASE-FIX COMPLETE** — approved and redeployed (below).

### 7-ERASE-FIX redeploy (2026-10-05)

Backup: `zola-spikes/p6-episodes/backup_7erase_fix/` — DB `0877d962…` (192512 B); pre-deploy plugin folder stamped `plugins_zola_memory_20261005_092357`.

| File | Live SHA-256 | Match repo |
|---|---|---|
| `store.py` | `2868d2a3…` | ✅ |
| `forget.py` | `adc873c5…` | ✅ |
| `log.py` | `75c08ef5…` | ✅ |
| `provider.py` | `e2920937…` | ✅ |
| `fact_index.py` | `8eae48cb…` | ✅ |
| `consolidate.py` | `6ebd759f…` | ✅ |

| Check | Result |
|---|---|
| All Hermes stopped before deploy | ✅ (Client 13200; serve 17388→18972) |
| Relaunch | `Zola.Client` PID **396**; serve **17372→9912** |
| `store_open` | ✅ `pid=9912 secure_delete=1 sqlite_version=3.53.1 fts_secure_delete=true` (09:24:14) |
| Initialize | ✅ `schema_version=2 fts_ok=true import_count=0` (same PID) |
| G6 tools / provider | ✅ identical (`forget_memory` only) |
| G6 prompt | ⚠️ differs only by C2 smoke MEMORY facts (Larkspur×2, Miata×2) + allowlisted `Conversation started:` — expected; not a plugin/SOUL delta |

## Part D STOP (session `20261005_092409_665712`)

Brian note: **D1 — she didn't ask which.** Confirmed in transcript.

### Pre-D kinds (targets)

| Target | notebook facts | episodes | pending |
|---|---|---|---|
| Larkspur / LoRa / antennas | 2 MEMORY (`8d03ecaa…`, `31e329a4…`) | 1 (`bbe7265f…`) | 0 |
| Miata / timing belt | 2 MEMORY (`56a85bd0…`, `867442fe…`) | 1 (`eb1130fb…`) | 0 |

### D1 — "Forget what I told you in that update earlier today." / "The car stuff."

| Step | Result |
|---|---|
| `forget_memory confirm=false` | ✅ `candidate_count=4 group_count=2` (Larkspur group + Miata group; `ask_brian=true`) at 09:27:47 |
| She asks which? | ❌ **did not ask** (Brian) — proceeded to erase |
| Path taken | **memory-tool `remove` → cascade** on **Larkspur** facts first (09:27:57): `8d03ecaa` → `episode_rows=1`; `31e329a4` → `episode_rows=0` |
| `forget_memory confirm=true` | ❌ `unbound_targets` — `target_ids=[bbe7265f…]` only (episode) after facts already removed; not from latest candidate list |
| Brian "The car stuff." | After she already said Done; then **memory-tool `remove`** Miata facts (09:29:12) `56a85bd0` → `episode_rows=1`; `867442fe` → 0 — and she **re-added** Larkspur MEMORY notes |
| Expected path | `forget_memory confirm=false` (2 groups) → ask → `confirm=true` with **Miata** IDs only | **FAIL** |

Sanitize (each cascade): `secure_delete=1 fts_mode=secure-delete checkpoint_busy=0 checkpoint_log=0 checkpoint_frames=0 sanitize_pending=0 ok=true`.

### D2 — paraphrase "sprinkler-controller radio choice"

| Check | Result |
|---|---|
| Summary ≠ source wording | summary-only: `because`, `brian`, `decisive`; source-only samples: `antennas`, `garden`, `irrigation`, `order`, …; forget phrasing shares **0** terms with summary (`sprinkler`/`radio`/`choice` absent from both) |
| Path | **memory-tool replace/remove** (strip LoRa/antennas; keep irrigation-controller line) — not `forget_memory confirm=true` |
| `forget_memory confirm=false` | ran after; `group_count=2 ask_brian` — again **no ask / no confirm=true** |
| Recall "decide about Larkspur?" | prefetch **0**; answer: forgot radio choice; still recalls irrigation controller |
| "Did I go with LoRa?" | prefetch **0**; "I don't know — you asked me to forget that choice." |
| Episode | ✅ gone (episodes=0) |
| Survivor notebook fact | ⚠️ `fe226252…` active: `[project] Project Larkspur is Brian's garden irrigation controller.` — **P6-D06 survivor vs full forget expectation** |

### D3 — byte scans (no manual VACUUM/rebuild)

| Surface | Larkspur | LoRa | antennas | Miata | timing belt |
|---|---|---|---|---|---|
| Offline `.db` (sqlite3.backup) | **3** | 0 | 0 | 0 | 0 |
| Live `-wal` | **3** | 0 | 0 | 0 | 0 |
| FTS MATCH | `facts_fts` Larkspur=**1**; episodes/entities 0 | 0 | 0 | 0 | 0 |
| `sanitize_pending` | **0** | | | | |

Miata/LoRa/antennas/timing-belt physical: clean. Larkspur hits = survivor fact (not free-page remnant from erase).

### Counts after Part D

| Metric | Value |
|---|---|
| episodes / pending | **0 / 0** |
| facts active / tombs | **15 / 26** |
| `USER.md` | unchanged `47a732a0…` |
| `MEMORY.md` | `3d66334b…` (311 B) — family + survivor Larkspur line |

### Episode-only `forget_memory` track

**Not successfully executed.** One `confirm=true` with episode id only → `unbound_targets`. All erasures that stuck were **memory-tool remove → cascade** (or replace). Still true at Part D STOP (Part E not started).

**Part D STOP** — reviewed below; 7-D-FIX proposal follows.

### Part D review (Brian + Claude) + episode timeline

Brian (verbatim): *"I agree. Yes."* — adopt a code-enforced forget guard.

| Finding | Ruling |
|---|---|
| D1 FAIL | `confirm=false` returned `ask_brian=true`; she bypassed via memory-tool remove and destroyed the Larkspur episode (unrecoverable) — P6-D06 target-uncertainty rule violated through an ungated path |
| D2 | Confirm Larkspur **episode** at D2 start; if absent, D2 is **untested**, not passed |
| Survivor `fe226252` | Outside D2 target (radio choice) — **correct** to keep |

**Episode IDs / counts:**

| Moment | episodes | IDs |
|---|---|---|
| Pre-D (redeploy backup `…092357`) | **2** | `bbe7265f…` Larkspur; `eb1130fb…` Miata |
| After D1 Larkspur memory-remove (09:27:57) | **1** | Larkspur gone (`episode_rows=1` on `8d03ecaa` cascade); Miata still present |
| After D1 Miata memory-remove (09:29:12) | **0** | Miata gone (`episode_rows=1` on `56a85bd0`) |
| D2 start ("sprinkler-controller…") | **0** | **No Larkspur episode** — D2 episode-forget path **untested** (not a pass) |

## Phase 7-D-FIX proposal (read-only; build nothing)

Brian decision: code-enforced forget guard. Hermespin: `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`).

### G1 — `pre_tool_call` can block without an approval card

| Question | Answer | Evidence |
|---|---|---|
| Inspect name + args? | **Yes** | Hook payload: `tool_name`, `args`, `session_id`, … — `hermes_cli/plugins.py` L1796–1800 (`_get_pre_tool_call_directive_details`); docs `hooks.md` §`pre_tool_call` |
| Block with message to the model (no approval card)? | **Yes** — return `{"action": "block", "message": "<str>"}`. Message becomes the tool result (`{"error": message}`). **`approve`** is the path that opens the human-approval gate; **`block` does not.** | `plugins.py` L1787–1790, L1815–1824, L1859–1860; `tool_executor.py` L622–634, L663–680, L609–613 |
| Fires for builtin `memory` tool? | **Yes** — every tool execution goes through `_dispatch_authorized_once` → `_pre_tool_block` before `execute`; `memory` is handled on that path (post-block bookkeeping at L683–684). Inner `skip_pre_tool_call_hook=True` (L1545) only skips a *second* dispatch inside registry `handle_function_call` after the outer gate already ran. | `tool_executor.py` L649–689, L1525–1546; docs: "built-in tools and plugin tools alike" |
| Can `zola_memory` register it? | **Yes** — memory provider `register(ctx)` already calls `ctx.register_hook("pre_llm_call", …)` (`zola_memory/__init__.py` L66–68). `_ProviderCollector.register_hook` forwards to real `PluginContext` (`plugins/memory/__init__.py` L319–322). |

### G2 — Proposed guard (adopt)

**State (per provider / `self._session_id`):** add `ForgetSessionState.ask_brian_pending: bool` (default False). Set **True** when `forget_memory` `confirm=false` returns any group with `ask_brian=true`. Clear when (a) the **next Brian user turn** begins for that session (`on_turn_start_forget_hooks` — no content heuristics), or (b) hold ends (`clear_hold_process` / `_expire_hold` / successful `confirm=true` / session switch).

**`pre_tool_call` handler** (register next to existing `pre_llm_call`):

1. Resolve provider for `session_id` (registry); if none or not Brian conversation → allow.
2. If `tool_name != "memory"` → no-op (no log).
3. If call is not remove/replace (top-level `action` or any `operations[]` entry) → no-op (`add` never blocked).
4. If remove/replace: log `zola_memory.forget_guard` with `action=blocked|allowed` (no content) from `ask_brian_pending`; if pending → **block**.
5. Block return (exact):

```text
Brian hasn't said which one yet — ask him which he means before removing anything.
```

**"Brian answered" detection (no content heuristics):** at `on_turn_start`, if `ask_brian_pending` and this is a Brian interactive turn for `self._session_id`, set `ask_brian_pending=False` (and keep existing hold/candidate set so `confirm=true` still works). His utterance is not parsed for "which" — the turn boundary is the signal.

**Interaction with today's hole:** `end_hold_if_candidate_removed` (`forget.py` L1163–1195) must **not** clear ask/hold when `ask_brian_pending` (or becomes unreachable because remove is blocked first). Prefer: guard blocks remove → that path never runs during ask; still gate `end_hold_if_candidate_removed` with `if state.ask_brian_pending: return` as belt-and-suspenders.

**Scope:** only `ask_brian=true` (multi-group). Single-group "One match. Ask Brian to confirm" does **not** set `ask_brian_pending` (unchanged confirm UX).

### G3 — Stronger `confirm=false` message when `ask_brian=true`

Replace current (`forget.py` L1053–1055):

> These look like different things. Ask Brian which one he means before calling confirm=true.

with **exact**:

> These look like different things. Ask Brian which one he means before calling confirm=true. Do not use the memory tool to remove or replace anything until he answers — those calls are blocked until then.

(Single-match message unchanged.)

### G4 — Rerun plan (episode-only; new synthetics)

**S1'** (new conversation; Brian tells her not to save notes):

1. `Quick update: we picked a slate roof for the Quillmoor cabin. No need to save a note on this.`
2. `Also, I drove the '72 Bronco to Moab last weekend. No need to note that either.`
3. `Thanks!`
4. ≥10 quiet minutes → Cursor verifies: **2 episodes**, **0** new notebook facts for Quillmoor/Bronco/slate/Moab; hashes for pre-existing MEMORY unchanged (or only allowlisted non-smoke deltas).

**D1'** (same session continues):

1. Brian: `Forget what I told you in that update about the cabin and the trip.`
2. Expect: `forget_memory confirm=false` with **2 groups**, `ask_brian=true`; she **asks which**; any memory remove/replace → blocked + log `forget_guard action=blocked`.
3. Brian: `The trip.`
4. Expect: `forget_memory confirm=true` with **Bronco episode id only**; Quillmoor episode untouched; tombstone; sanitize ok / `sanitize_pending=0`.

**D2'**:

1. Brian: `Please forget what we chose for the roof on that mountain place.` (paraphrase)
2. Expect: Quillmoor episode erased (episode-only path or confirm=true); then  
   `What roof did we pick for Quillmoor?` / `Did I go with slate?` → nothing resurfaces (prefetch empty; no survivor episode).
3. Byte scan Quillmoor/slate/Bronco/Moab → 0 on `.db` + `-wal` (no manual VACUUM).

**Part E** (after D2' pass): Fernhill leak-test note with "no need to save a note"; Cursor force-close before quiet gap; relaunch; consolidate pending; Brian forgets Fernhill; clean byte scan.

**Approved with addition** (Brian + Claude): also block `forget_memory confirm=true` while ask pending (G3 message). Built + redeployed below.

### 7-D-FIX build + redeploy (2026-10-05)

| Item | Result |
|---|---|
| Suites | `zola_memory` **105 OK**; `zola_tools` **44 OK** |
| Backup | `backup_7d_fix/zola_memory_20261005_101629.db` `ade2a7b8…` (200704 B) |
| Live | Client PID **3036**; serve **9632→12544**; `store_open pid=12544 secure_delete=1 fts_secure_delete=true`; init `schema_version=2` |
| G6 tools / provider | ✅ identical (`forget_memory` only) |
| G6 prompt | ⚠️ survivor Larkspur MEMORY line + `Conversation started:` allowlist — expected |
| `pre_tool_call` | ✅ **1** callback after load: `forget.pre_tool_call_hook` |

| File | Live SHA-256 |
|---|---|
| `forget.py` | `35d943a0183b9d6e7e7d8cd855d43d2d76dd82911584635688fad45e375dc8df` |
| `log.py` | `a2515a96171b2f9b4ab7947a41a7c7181db3dca6f636298c11a7373aafdc1b62` |
| `__init__.py` | `7faa42bc030b329eb5f078b80ec45183104105361a29e880eac3ccccf9994c11` |

### G4 — S1' result (session `20261005_101633_f07d35`) — FAIL

| Check | Result |
|---|---|
| Turns / pending written | ✅ 3 keep writes (`d0ba5922…`, `c116c86c…`, `614e3fcb…`) |
| Quiet consolidate | `10:38:52` `trigger=quiet turns=3 episodes=0 ok=true` (LLM returned empty list; pending consumed) |
| Episodes after | ❌ **0** (need Quillmoor + Bronco) |
| New notebook facts (Quillmoor/slate/Bronco/Moab) | ✅ **0** |
| `MEMORY.md` | unchanged `3d66334b…` (311; survivor Larkspur only) |

**S1' accepted as script flaw (Brian + Claude), not a defect.** Lore: the consolidator honors an explicit don’t-note request (consent signal) — **observed, not designed.**

### G4 — Brian step S1'' (new conversation; no note instructions)

1. `Quick update: we picked a slate roof for the Quillmoor cabin after comparing it with metal.`
2. `Also, I took the '72 Bronco out to Moab last weekend. The trail was washed out, so we turned back early.`
3. `Thanks!`

Then **≥10 quiet minutes**, say **done**. Cursor reports per-topic episodes / event_time / notebook facts, then D1'.

### G4 — S1'' result (same session `20261005_101633_f07d35`, turns 4–5)

Quiet consolidate `11:04:19` `turns=2 episodes=2` + `time_unresolved reason=phrase_not_in_table count=1`.

| Topic | Episode? | ID | Summary (Brian) | event_time / basis / evidence | Notebook fact? |
|---|---|---|---|---|---|
| Quillmoor slate roof | ✅ | `172f5cb5…` | *Brian selected a slate roof for the Quillmoor cabin after comparing it with metal.* | `null` / `unknown` / `null` | ✅ `8e86eadd…` MEMORY `[project] Quillmoor cabin roof decision: slate was selected after comparison with metal.` |
| Bronco Moab | ✅ | `b35c6647…` | *Brian took the '72 Bronco to Moab, but turned back early because the trail was washed out.* | `null` / `unknown` / `null` + **`time_unresolved phrase_not_in_table`** (correct for “last weekend”) | ❌ none |

**Both topics do not have notebook facts** — only Quillmoor does. Bronco is **episode-only** → D1' can exercise live `forget_memory` on the trip episode.

### Brian — D1' (continue same conversation)

1. `Forget what I told you in that update about the cabin and the trip.`
2. She **must ask which** (do not pick yourself). If she asks: `The trip.`
3. Say **done** when that turn finishes (before D2').

### G4 — D1' result — PASS (live episode-only `forget_memory`)

| Check | Result |
|---|---|
| Before | episodes: Quillmoor `172f5cb5…` + Bronco `b35c6647…`; fact `8e86eadd…` |
| `confirm=false` | ✅ `group_count=3` all `ask_brian=true` (notebook + cabin ep + Bronco ep); G3 message present |
| She asked | ✅ “I found separate cabin and trip memories. Do you want me to remove both?” |
| Same-turn bypass | ✅ none (no memory remove; no confirm=true until next turn) |
| Brian | `The trip.` |
| Path | **`forget_memory confirm=true`** `target_ids=[b35c6647…]` only; `forget_guard action=allowed`; cascade `reason=tool episode_rows=1` |
| After | Bronco gone; Quillmoor episode + fact remain |
| Sanitize | `secure_delete=1 fts_mode=secure-delete checkpoint_busy=0 … sanitize_pending=0 ok=true` |

### Brian — D2' (same conversation)

1. `Please forget what we chose for the roof on that mountain place.`
2. Then: `What roof did we pick for Quillmoor?`
3. Then: `Did I go with slate?`
4. Say **done**.

### G4 — D2' result — PASS

Brian note: D2-1 follow-up asked whether to remove saved note **and** conversation memory; he answered `yes`.

| Step | Path / result |
|---|---|
| D2-1 paraphrase | `forget_memory confirm=false` → **2 groups** (notebook `8e86eadd…` + episode `172f5cb5…`), `ask_brian`; she asked: “I found both a saved note and a conversation memory about it. Should I remove both?” |
| Brian | `yes` |
| Erase | **memory-tool `remove` → cascade** `reason=remove` fact_rows=1 **episode_rows=1** (fact_refs wiped Quillmoor episode); sanitize `busy=0 sanitize_pending=0`. Parallel `forget_memory confirm=true` → `authority` refuse (hold cleared by candidate remove); leftover confirm=false → no matches |
| After | episodes **0**; Quillmoor fact inactive; tombs **28** |
| Recall | prefetch **0**; “I don’t retain that anymore.” ×2 |
| Byte scan | Bronco/Moab **0**. Quillmoor/slate hits only in **pending** recall rows (`What roof…` / `Did I go with slate?`) — not forgotten episode/fact content; SQL/FTS MATCH for forgotten needles **0** |

### Brian — Part E (new conversation)

1. Send: `Quick note: Project Fernhill's prototype passed its first leak test. No need to save a note on this.`
2. Immediately say **go** (do not wait for quiet gap). Cursor will force-close the client.
3. Relaunch the client yourself, then say **relaunched**.
4. After Cursor confirms consolidate: `Forget everything about Fernhill.`
5. Say **done**.

### Part E result — STOP

| Step | Result |
|---|---|
| Pre-kill | pending `bcab4e74…` written (`20261005_111436_245a1f`); quiet gap **not** waited; client/serve force-killed |
| Relaunch | `initialize` → `consolidate trigger=initialize turns=1 episodes=0` (don’t-note consent again; pending consumed) |
| After consolidate | pending **0**; episodes **0**; no Fernhill fact |
| Forget | `forget_memory confirm=false` → **No matches** (nothing retained); she reported no stored memory |
| Sanitize | n/a (no cascade) |
| Offline `.db` byte scan | Fernhill/leak/Quillmoor/slate/Bronco/Moab all **0**; FTS MATCH **0**; `integrity_check=ok` |
| Live `-wal` | Fernhill/leak + Quillmoor/slate still in **deleted pending frames** (consolidate pending-delete does not run G-ERASE sanitize). Not SQL-visible. |
| Live episode-only `forget_memory` | ✅ executed in **D1'** (Bronco `b35c6647…`) |

**G4 / Part E STOP.** Lore: don’t-note consent suppresses episodes (S1' + Fernhill); pending crash-survival + initialize consolidate confirmed; WAL may retain pending text until checkpoint/TRUNCATE outside forget sanitize.

### Phase 7-WAL (approved Brian + Claude, 2026-10-05)

Gap: Fernhill pending text remained in `-wal` after consolidate consumed the row (no sanitize); zero-match forget also skipped sanitize.

**Fix (repo):**
- (a) `consolidate._commit` → `sanitize_after_erase` after every commit (episodes or zero)
- (b) `forget_memory confirm=false` always sanitizes; memory-tool remove with no match sanitizes
- (c) tests: `test_consolidate_clears_pending_wal_bytes`, `test_zero_match_forget_clears_wal_bytes`

| Suites | Result |
|---|---|
| `zola_memory` | **107 OK** |
| `zola_tools` | **44 OK** |

### 7-WAL redeploy (2026-10-05)

| Item | Result |
|---|---|
| Backup | `zola-spikes/p6-episodes/backup_7wal/` — DB `zola_memory_20261005_112053.db` `440b9825…` (200704 B; schema=2; facts=15; tombs=28; episodes=0); plugin folder `plugins_zola_memory_20261005_112053` |
| Deploy | `consolidate.py` `store.py` `forget.py` `fact_index.py` — live SHA MATCH repo |
| Live | Client PID **8696**; serve **17772→21612**; `store_open pid=21612 secure_delete=1 fts_secure_delete=true`; `initialize schema_version=2` |
| Pre-redeploy note | After serve kill, live `-wal` already absent (Fernhill frames gone with process close); Fernhill forget re-run still required to exercise zero-match sanitize path |

| File | Live SHA-256 |
|---|---|
| `consolidate.py` | `ee2483b53361676e825aa3325e639f9e2cd4107557230c8620ae079bef4c44f8` |
| `store.py` | `c471ea121f993bd00d5e68eef0defb92fbdd3d606774ca78b89adf1b34cb00e8` |
| `forget.py` | `a9b62aa822dbad0a350fe84cb004c4e63124f4fbea98f591d4454eddcc1bb306` |
| `fact_index.py` | `aa0cce9e599ba94f933a8619e2094d3a21192bd4aa785510a9d28fbc53d81b02` |

### Brian — 7-WAL verify (same conversation ok)

1. `Forget everything about Fernhill.`
2. Say **done**.

### 7-WAL verify result — PHASE 7-WAL COMPLETE

Session `20261005_112138_2ff3eb`:

| Check | Result |
|---|---|
| Forget | `11:23:17` `forget_memory confirm=false` → No matches (`candidate_count=0`) |
| Sanitize (new path) | `11:23:17` `sanitize_after_erase secure_delete=1 fts_mode=secure-delete checkpoint_busy=0 sanitize_pending=0 ok=true` **before** tool return |
| Offline `.db` | Fernhill/leak/Quillmoor/slate/Bronco/Moab **0** (Larkspur survivor **3**) |
| Live `-wal` | size **0**; all needles **0** |
| FTS MATCH | Fernhill/leak **0** on facts/episodes/entities |
| `integrity_check` | ok; `sanitize_pending=0`; facts=15 tombs=28 episodes=0 pending=0 |

No manual VACUUM/cleanup.

### G4 full tables (canonical)

#### S1'' (session `20261005_101633_f07d35`, quiet consolidate `11:04:19` turns=2 episodes=2)

| Topic | Episode | ID | Summary | event_time / basis / evidence | Notebook fact |
|---|---|---|---|---|---|
| Quillmoor slate roof | ✅ | `172f5cb5…` | Brian selected a slate roof for the Quillmoor cabin after comparing it with metal. | `null` / `unknown` / `null` | ✅ `8e86eadd…` MEMORY `[project] Quillmoor cabin roof decision: slate was selected after comparison with metal.` |
| Bronco Moab | ✅ | `b35c6647…` | Brian took the '72 Bronco to Moab, but turned back early because the trail was washed out. | `null` / `unknown` / `null` + **`time_unresolved phrase_not_in_table`** (“last weekend”) | ❌ none |

#### D1' (same session) — live episode-only `forget_memory`

| Check | Result |
|---|---|
| `confirm=false` | `11:06:10` `candidate_count=3 group_count=3` all `ask_brian` |
| She asked which? | ✅ “I found separate cabin and trip memories. Do you want me to remove both?” |
| `forget_guard` **blocked** | **none** (0) — she did not attempt remove/confirm=true while ask pending |
| `forget_guard` allowed | `11:06:29` `action=allowed tool=forget_memory` (ask cleared; Brian: “The trip.”) |
| Brian answer | `The trip.` |
| `confirm=true` targets | `[b35c6647…]` only (Bronco episode) |
| Path | **`forget_memory confirm=true`** → cascade `reason=tool episode_rows=1 fts_rows=3 entity_rows=2` |
| Cascade / sanitize | `11:06:29` sanitize `busy=0 sanitize_pending=0 ok=true` |
| After | Bronco gone; Quillmoor episode + fact remain |
| Byte scan (post-D1') | Bronco/Moab **0** in SQL/FTS |

#### D2' (same session) — paraphrase forget + recall

| Check | Result |
|---|---|
| Episode at start? | ✅ Quillmoor `172f5cb5…` + fact `8e86eadd…` still present |
| Wording-overlap | forget phrasing ∩ (ep∪fact) distinctive ≥3-letter tokens: **`roof` only (1)**; forget-only: forget/chose/mountain/place; source-only samples: slate/quillmoor/cabin/metal/… |
| `confirm=false` | `11:07:34` `group_count=2 ask_brian`; she asked: saved note + conversation memory? |
| Brian | `yes` |
| Path / erase | **memory-tool `remove` → cascade** `11:08:35` `reason=remove fact_rows=1 episode_rows=1`; sanitize ok. Parallel `forget_memory confirm=true` → `authority` refuse (hold cleared by remove) |
| Recall | `What roof…` / `Did I go with slate?` → “I don’t retain that anymore.” ×2 |
| Prefetch | `11:08:58` + `11:09:08` `returned_len=0` (empty contents) |
| Byte scan | Bronco/Moab **0**; Quillmoor/slate only in **pending recall** rows until Part E/WAL fix; SQL/FTS MATCH forgotten needles **0** |

#### Part E + 7-WAL

| Check | Result |
|---|---|
| Crash safety | ✅ pending survived kill; `initialize` consolidate turns=1 episodes=0 (don’t-note) |
| Pre-7-WAL gap | Fernhill in `-wal` deleted-pending frames (no sanitize on consolidate / zero-match forget) |
| Post-7-WAL | zero-match forget runs sanitize; `.db` + `-wal` Fernhill/leak **0** |

**PHASE 7-WAL COMPLETE.**

### Phase 7 smoke acceptance (Brian + Claude, verbatim, 2026-10-05)

> Phase 7 smoke accepted (Brian + Claude) with recorded caveats: forget_guard not exercised live (she asked; unit-tested); D2' erased via fact_ref cascade (wordless paraphrase-on-episode-only remains fact-ref dependent — known limit). Lore notes: consolidator honors don't-note requests; "last weekend" not in phrase table (candidate addition); zero-match forget now sanitizes.
> Brian's verdicts (verbatim): C2 summary accuracy: "good". Part C answers 1–6: "good".
> proceed to closeout — 8a's Exit Criteria Verification MUST include, with evidence: the Part C table (direct recall incl. "when" for Q1, associative Q2–Q5 found/top-3/score/shared words, Q6 no block); Part A latency median/p95 (offline ≥30 queries) and live prefetch times; blind test (C2); no-recursion (C4); D1'/D2'/E; G-ERASE scans; deferred-sanitize events (count). Anything missing → ⚠️ with reason, not ✅.

## Phase 8 — Closeout

### 8a Verify

| Check | Result |
|---|---|
| `zola_memory` unit tests | **107 OK** |
| `zola_tools` unit tests | **44 OK** |
| `dotnet build … -r win-x64` | **PASS** (0 warnings / 0 errors) |
| `hermes-agent` | porcelain empty at `345cd2b057a452236de401d3534b8502a7465e8d` (detached `v2026.9.14`; pre-existing pin) |

#### Required evidence pack (Brian closeout instruction)

**Part C table** — see §Part C table (recall) above (Q1–Q6 with Brian **"good"**). Summary:

| # | Prefetch / top-3 | Score | Shared words (Q∩summary) | "when" / notes |
|---|---|---|---|---|
| Q1 direct | ✅ Larkspur in prefetch; top-3 ✅ | `top_score=1.0` | n/a (direct) | spoken "when" ❌; Brian good |
| Q2 assoc | found ❌ / top-3 ❌ | 0 | ∩Larkspur **0** `[]`; ∩Miata **0** `[]` | Brian good |
| Q3 assoc | found ⚠️ gated (`candidates=1 returned=0`) / top-3 ❌ | `top_score=0.0` | ∩Larkspur **1** `['project']`; ∩Miata **0** | Brian good |
| Q4 assoc | found ❌ / top-3 ❌ | 0 | **0** / **0** | Brian good |
| Q5 assoc | found ❌ / top-3 ❌ | 0 | **0** / **0** | Brian good |
| Q6 control | ✅ **no `<memory-context>`** (`returned_len=0`) | 0 | — | Brian good |

Associative top-3: **0/4** (measured, not gating).

**Part A latency (offline ≥30 queries):** n=**32** realistic queries on offline copy + 200 synthetic episodes → median **1.272 ms**, p95 **1.741 ms** (&lt; 50 ms). Scratch: `zola-spikes/p6-episodes/phase7/latency_scratch.db`.

**Live prefetch / retrieve times (smoke):** Part C Q1–Q6 `retrieve elapsed_ms` ∈ {0,1} (Q1=`1`; others `0`); live smoke retrieve n=40 (excl. Part A bulk) median **0** / p95 **0** / max **1** ms. Prefetch logs `returned_len` only (no separate prefetch elapsed field).

**Blind test (C2):** PASS — §C2 re-smoke blind table; Miata `2026-10-04`/`stated`/`yesterday`; one Larkspur + one Miata episode; math/weather/thanks none. Brian summary accuracy: **"good"**.

**No-recursion (C4):** PASS — quiet `episodes=0`; count stayed 2; USER/MEMORY hashes unchanged.

**D1' / D2' / E:** see G4 full tables. D1' episode-only `forget_memory` PASS; D2' paraphrase erase via fact_ref cascade (⚠️ known limit); E crash-safety PASS; 7-WAL zero-match sanitize PASS.

**G-ERASE scans:** post-cascade sanitize `busy=0` on D1'/D2'; post-7-WAL `.db`+`-wal` Fernhill/leak/Quillmoor/slate/Bronco/Moab **0** (Larkspur survivor only). C1 early smoke required manual FTS+VACUUM (reported FAIL then) → fixed by 7-ERASE-FIX + 7-WAL.

**Deferred-sanitize events (live log count):** `sanitize_retry action=defer` = **0**; `action=success` = **0**; `action=retry` = **0**. Unit-only: `test_truncate_busy_defers_then_retry_clears_bytes` exercises defer→success.

### 8c Deploy re-verify (repo = live)

| File | SHA-256 |
|---|---|
| `__init__.py` | `7faa42bc030b329eb5f078b80ec45183104105361a29e880eac3ccccf9994c11` |
| `provider.py` | `e292093763665b0a35e38c67166f84e372493d4f4016704f006217a15e76a18a` |
| `pending.py` | `9ff6156cd946c08bfd737edffc15c6dae2d865ab0c34ed332f48056dda854769` |
| `consolidate.py` | `ee2483b53361676e825aa3325e639f9e2cd4107557230c8620ae079bef4c44f8` |
| `retrieve.py` | `6fd6ba6bd5e634d9bad0a33862ca51814bcb576dfb5657a6f0d9e39d108540b7` |
| `store.py` | `c471ea121f993bd00d5e68eef0defb92fbdd3d606774ca78b89adf1b34cb00e8` |
| `forget.py` | `a9b62aa822dbad0a350fe84cb004c4e63124f4fbea98f591d4454eddcc1bb306` |
| `fact_index.py` | `aa0cce9e599ba94f933a8619e2094d3a21192bd4aa785510a9d28fbc53d81b02` |
| `log.py` | `a2515a96171b2f9b4ab7947a41a7c7181db3dca6f636298c11a7373aafdc1b62` |
| `time_context.py` | `c3b61942358cccec6db422b31b7200c8d743c095779b144db9b174bf105bbf9f` |
| `registry.py` | `86aa4da04d67ab911d569ab1d9774a86e1a36f75f9b1931d49ca3f0272ee771d` |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` |

All MATCH live. No `identity/` / `SOUL.md` edits this track. `config.yaml` untouched.

### Exit criteria verification (PHASE6_BUILD_PLAN.md Track 5 + guardrails)

| Criterion | Verdict | Evidence |
|---|---|---|
| Unit: schema rejects fact-create / bad fact_ref / system basis / untraceable time | ✅ | `test_episodes_phase4` validate paths |
| Unit: zero-episode consumes pending | ✅ | `test_zero_episode_consumes_pending` + 7-WAL WAL-clear test |
| Unit: generation-change discard | ✅ | consolidate discard tests |
| Unit: bounded retry then giveup | ✅ | consolidate attempt/giveup tests |
| Unit: single-consolidation lock | ✅ | lease / dual-provider tests |
| Unit: retrieval floor + pending_erasures exclusion | ✅ | retrieve calibration + forget tests |
| Unit: relative-age formatting | ✅ | retrieve / time_context tests |
| CURSOR: prefetch p95 &lt; 50 ms (≥30 queries) | ✅ | Part A offline n=32 median 1.272 / p95 **1.741 ms**; live smoke max 1 ms |
| CURSOR: consolidate off-thread (no turn block) | ✅ | `on_pre_compress` returns &lt;0.2s; background thread |
| HUMAN: blind episode test (C2) | ✅ | C2 table PASS; Brian summaries **"good"** |
| HUMAN: direct recall + when + no session_search | ⚠️ | Q1 prefetch ✅ / top-3 ✅ / `session_search=0`; spoken **"when" absent** (Brian still **"good"**) |
| HUMAN: associative recall table (not gating) | ⚠️ | **0/4** top-3; shared-word table above; OQ for lore closeout |
| HUMAN: unrelated → no memory block | ✅ | Q6 `returned_len=0` / no `<memory-context>` |
| HUMAN: episode forget clarify-or-erase | ✅ | D1' asked which → `confirm=true` Bronco-only; tomb + recall gone |
| HUMAN: paraphrase forget (P6-D06) | ⚠️ | D2' erased via **fact_ref cascade** after notebook remove; wordless paraphrase-on-episode-only remains fact-ref dependent (accepted caveat) |
| Crash safety | ✅ | Part E pending survived kill; initialize consolidate |
| Synthetics removed / counts | ✅ | G4 + 7-WAL scans; tombs=28; smoke facts cleared |
| G-ERASE (approved) | ✅ | post-FIX/WAL sanitize+TRUNCATE; final `.db`/`-wal` needles 0 (no manual cleanup on 7-WAL verify) |
| Deferred sanitize | ⚠️ | live `action=defer` count=**0** (never busy in smoke); unit defer→success ✅ |
| forget_guard live block | ⚠️ | **0** blocked events live (she asked); unit-tested G2/G3 |
| G-PENDING-ID / G-NO-RECURSION / G-ENTITY-GROUNDING / G-BRIAN-ONLY / G-ONE-CONSOLIDATOR | ✅ | C4 no-recursion; Brian-only tool; lease; entity grounding tests; pending UUID ids |
| Live episode-only forget (Track 4 deferral) | ✅ | D1' `forget_memory confirm=true` on Bronco episode |
| hermes clean; no client source changes | ✅ | hermes porcelain empty; no `windows-client/**` source edits |
| Deploy hashes | ✅ | 8c table MATCH |

All Track 5 criteria met (with approved/recorded ⚠️): **YES**. Unit tests: **PASS**.

### Lore inputs (for later lore; **no lore edits this track**)

1. Consolidator honors explicit don’t-note / “no need to save a note” (S1' + Fernhill) — observed consent signal, not designed.
2. `"last weekend"` not in stated-time phrase table — candidate addition.
3. Associative recall 0/4 → OQ for semantic/associative episode retrieval (plan).
4. Wordless paraphrase-on-episode-only forget remains fact-ref / notebook dependent.
5. Pre-deploy DB backups may retain forgotten synthetic bytes — retention policy TBD.
6. Voice echo / “User correction during the turn” — still open (from Track 4).

### Closeout SHAs

*(filled as commits land)*

- Implementation commit (8f): `be8442b9106a1e13d74e56fe9ced7699a486e2c2`
- Docs record implementation SHA (8g): d673b2f0d1002b168a3e1fc042dca6019d4be84e
- Merge SHA on main (8i): *(pending)*
- Docs record merge SHA (8j): *(pending)*

## Unit test summary

### Phase 1 baseline

| Suite | Result |
|---|---|
| `zola_memory` | 79 OK |
| `zola_tools` | 44 OK |

### Phase 4

| Suite | Result |
|---|---|
| `zola_memory` | Ran 97 tests — OK |
| `zola_tools` | Ran 44 tests — OK |

### Phase 4b

| Suite | Result |
|---|---|
| `zola_memory` | Ran 100 tests — OK |
| `zola_tools` | Ran 44 tests — OK |

### 7-ERASE-FIX

| Suite | Result |
|---|---|
| `zola_memory` | Ran 103 tests — OK |
| `zola_tools` | Ran 44 tests — OK |

### EPISODE_MIN_SCORE calibration (X3 → per-candidate, Phase 4b)

| Query class | Scores (full retrieve path) |
|---|---|
| Related (Alpine Quill / Cedar demo) | ≥ **1.0** (entity-name word-boundary hit boost) |
| Must-not single-common-word: tonight / car / work / weekend + movie | **0.0** (per-candidate gate) |
| **Chosen `EPISODE_MIN_SCORE`** | **0.15** |
| Separation | related min 1.0 vs must-not 0.0 (margin 1.0) |

## Phase 1 notes

- Progress doc created on `p6-episodes`, uncommitted until closeout (or as later phases require).
- Scratch: `C:\Users\test\Dev\zola-spikes\p6-episodes\`.
- Prompt SHA verified against developer-supplied value (case-insensitive match).
- Base `main` includes FORGET merge `7b8f030b…` (ancestor of `c99e21c…`).

## Phase 2 notes

- E1–E10 all **CONFIRMED** (E2 PASS). Not BLOCKED.
- E8: without `secure_delete`, deleted synthetic strings remain in `.db` free pages; with `secure_delete=ON`, byte scan clean. Live backup still contains Dana/Okafor/Vespa/Rosa/marathons/paints byte remnants from prior smokes — G-ERASE one-time `VACUUM` justified.
- E10 proposed FTS query p95 ~0.07 ms on 200 synthetic episodes.
- Scratch artifacts (never committed): `e8_*`, `e10_*`, `live_db_backup_e8/`.

## Phase 3 notes

- Proposed episode contract §1–11 written into this progress doc (nothing built; no store/schema/code changes).
- Phase 2 acceptance recorded verbatim; E5/E6/E7/E8/E9 rulings reflected.
- Phase 3 approved with edits X1–X6 (Brian + Claude); G-ERASE adopted; Phase 4 begun.

## Phase 4 notes

- Built approved contract + X1–X6: `pending.py`, `consolidate.py`, `retrieve.py`, store v2, provider wiring, forget FTS/G-ERASE sanitize, tests.
- Schema v2: `turn_fingerprint` dedupe index, `episodes_fts` / `entities_fts`, `source_user_time`, `secure_delete=ON`.
- G-ERASE: optimize + wal_checkpoint after cascade (same connection + commit; no nested second-conn deadlock); one-time VACUUM remains deploy-only.
- **EPISODE_MIN_SCORE = 0.15** (calibration above).
- Nothing deployed; live profile untouched.

## Phase 4 review (Brian + Claude, verbatim)

> Phase 4 review (Brian + Claude). Claude reran with a test clock: recall block wording ✅ ("talked about Sun Oct 4 (yesterday) · happened: date unknown · … · still open: …"), dedupe ✅ (repeat ignored, next turn queued). Fix as Phase 4b before Phase 5:
> R1 Entity match uses substring: entity "Al" matched "I'm also tired today" and surfaced its episode. Match names/aliases on word boundaries (casefold, \b…\b, multi-word names as phrases) in _entity_name_hits and anywhere else names are matched. Test: "Al" vs "also" → no hit; "Al called" → hit; "Project Larkspur" phrase → hit.
> R2 Relevance gate is query-level; the approved X3 is per CANDIDATE: an episode qualifies only if it has an entity/name hit (word-boundary), shares a number with the query, or shares ≥ 2 distinctive terms with the query. Today "Any plans tonight?" surfaces an episode on the single shared term "tonight". Recalibrate EPISODE_MIN_SCORE on a corpus that includes single-common-word overlaps (tonight, car, work, weekend) as must-not-surface; report separation.
> R3 user_time: choose the user message whose content matches this turn's user_content (normalized, redirect suffix allowed — same containment rule as Track 4), not merely the latest user message; else NULL (X4). State whether sync_turn's messages is a snapshot or a live list (file:line). Test with a messages list whose last user message belongs to the next turn.
> Rerun both suites. STOP with PHASE 4b COMPLETE.

## Phase 4b notes

- **R1:** `retrieve.surface_matches_text` — casefold `\b…\b` / multi-word phrases; used in `_entity_name_hits`, entities_fts boost filter, and consolidator `_entity_grounded`.
- **R2:** Per-candidate gate (`candidate_passes_gate`); query-level gate removed. Recalibrated: related ≥ 1.0, must-not tonight/car/work/weekend = 0.0; **`EPISODE_MIN_SCORE` stays 0.15**.
- **R3:** `resolve_user_time(messages, user_content)` matches normalized content + Track 4 containment; else NULL. **`messages` is a live list** (not a snapshot): `hermes-agent/agent/turn_finalizer.py:604-606` passes `messages=messages` into `_sync_external_memory_for_turn` → async `sync_all` (`memory_manager.py:480-504`) without copying — unlike background review which uses `list(messages)`.
- Suites: `zola_memory` 100 OK, `zola_tools` 44 OK. Nothing deployed.

## Phase 4b verification (Brian + Claude, verbatim)

> Phase 4b verified (Brian + Claude). Claude reran: word-boundary names (Al ⊄ also; "Al called" hits), per-candidate gate (single shared "tonight" → none; ≥2 shared terms → hit), LoRa → Larkspur, and late-sync user_time picks the matching turn, not the next one. 100 tests OK.
> proceed to phase 5

## Phase 5 proposals (approved)

Live profile root: `%LOCALAPPDATA%\hermes\profiles\zola\`  
Plugin: `plugins\zola_memory\`  
Store: `zola_memory\zola_memory.db` (+ `-wal` ~2.6 MB / `-shm`; main `.db` currently 4096 B — **must** use SQLite backup API, not raw `.db` copy)

### 1. Redeploy file list (repo vs live)

| File | Repo SHA-256 | Live SHA-256 | Action |
|---|---|---|---|
| `provider.py` | `e0fa313c221307070968019db15da3d85fb08d71b768dd7cb1f6198bd4622827` | `c1dae292eeddddac3eec5bda82d2d9adc0098b2e0f2df3483f1d13dd23f3d108` | REPLACE |
| `forget.py` | `e24b3a35c8118e4ae75e0b4371b7f26e9a4500c2b892e09e23c44101e37b688b` | `8bb9de8b7d98e3750a7f10bc9a1b019e63d6d42b0c39fcfd32f5bdea91045afd` | REPLACE |
| `log.py` | `c21391e87a77d4efa977e5bfd9f74c996b37f6b9aa5af647c5e1cce584dc9717` | `d274baba8d9a696c95fffc3b2e43a50974739662c18ef8a8b735a356e876faca` | REPLACE |
| `store.py` | `2e57f8d126ea298834a7aee81eaf63070b9555ec5519b0884dd8698643c989ed` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` | REPLACE |
| `pending.py` | `5b7cf7410222754d709075962e633494c2895bd75c8f3d0b1c6455ecf27d2278` | *(absent)* | ADD |
| `consolidate.py` | `26b5daf64e71cba4ae12d92188cda061340c71d1bc0e8f50de24f6d8cbb6d67a` | *(absent)* | ADD |
| `retrieve.py` | `6fd6ba6bd5e634d9bad0a33862ca51814bcb576dfb5657a6f0d9e39d108540b7` | *(absent)* | ADD |
| `__init__.py` | `99eb18f3bedd5cc8abc408233e33b3d7eb591b1293397b7c5f1836bb293cd550` | same | unchanged |
| `fact_index.py` | `49d321a3b371ff61f5763a9b79acf187ea64caec0d04ee54bbbab793ee1afc0e` | same | unchanged |
| `time_context.py` | `c3b61942358cccec6db422b31b7200c8d743c095779b144db9b174bf105bbf9f` | same | unchanged |
| `registry.py` | `86aa4da04d67ab911d569ab1d9774a86e1a36f75f9b1931d49ca3f0272ee771d` | same | unchanged |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | same | unchanged |

No `plugin.yaml`. Tests stay in repo only (not redeployed).  
`config.yaml` unchanged (`7ba2e676a04ff92047c8d711fcb022be8a532b11baac6f74b08986744e704570`). No `approvals.*` / `zola_tools` / `hermes-agent` change.

### 2. Schema v2 migration (runs on first `open_store` after redeploy)

**Precondition:** Phase 6 backs up the store with the **SQLite backup API** (captures WAL) before redeploy; client closed.

Live today: `schema_version = 1`; facts 14; tombstones 16; episodes/pending/entities 0; no `turn_fingerprint` / `source_user_time` / `episodes_fts` / `entities_fts`.

On initialize, `store.migrate()` (BEGIN IMMEDIATE) when `current < 2` runs `_migrate_v2`:

1. `ALTER TABLE pending_turns ADD COLUMN turn_fingerprint TEXT NOT NULL DEFAULT ''`
2. `ALTER TABLE episodes ADD COLUMN source_user_time TEXT`
3. `CREATE UNIQUE INDEX idx_pending_dedupe ON pending_turns(session_id, ifnull(user_time, ''), turn_fingerprint)`
4. `CREATE VIRTUAL TABLE episodes_fts USING fts5(episode_id UNINDEXED, summary)`
5. `CREATE VIRTUAL TABLE entities_fts USING fts5(entity_id UNINDEXED, name)`
6. Set `meta.schema_version = 2`

Every open also sets `PRAGMA secure_delete=ON` and keeps WAL.

**Rollback of migration** = restore the Phase 6 DB backup file (plugin alone is insufficient if v2 already applied — Track 4 plugin refuses `schema_version > 1`… actually Track 4 has SCHEMA_VERSION=1 and **fails closed** if current > supported). So rollback must restore **both** plugin folder and DB backup together.

### 3. One-time G-ERASE maintenance (VACUUM) — adopted

**When:** Phase 6, client closed, **after** plugin redeploy + successful v2 migration verify, **after** DB backup recorded.

Exact steps:

1. Confirm client / hermes serve not holding the profile.
2. Ensure Phase 6 sqlite3.backup of pre-VACUUM (and ideally post-migration) DB is on disk with hash recorded.
3. Offline Python (or `sqlite3` CLI) against the live path:
   - open store (or connect + `PRAGMA wal_checkpoint(TRUNCATE)` then `VACUUM`)
   - `VACUUM;`
   - close
4. Fresh offline copy via sqlite3.backup; byte-scan for Dana / Okafor / Vespa / Rosa / marathons / paints — expect **0**.
5. Do **not** send any turn during this maintenance (G-LIVE).

Per-erase `secure_delete` + FTS optimize + checkpoint already ship in the redeployed cascade path (no logical delay).

### 4. `SOUL.md`

**None.** No new SOUL line expected; no identity mirror this track.

### 5. Rollback

1. Client closed.
2. Restore `plugins\zola_memory\` from the Phase 6 pre-EPISODES plugin backup (live hashes in §1 Live column = Track 4 / post-FORGET baseline).
3. Restore `zola_memory.db` from the Phase 6 sqlite3.backup (pre-migration / pre-VACUUM as chosen at failure point).
4. Delete any `zola_memory.db-wal` / `zola_memory.db-shm` beside the restored file before relaunch (stale WAL must not replay onto the backup).
5. Relaunch the client.
6. `config.yaml`, `approvals.*`, `zola_tools`, `hermes-agent`, `SOUL.md` untouched on the forward path — nothing to restore there unless a later edit is approved.

## Phase 5 notes

- Proposal recorded; Phase 5 approval + clarifications applied in Phase 6 (see **Approved live changes**).
- Rollback clarification from approval: restore plugin + DB together; delete any `zola_memory.db-wal` / `-shm` beside the restored file before relaunch.

## Phase 3 acceptance (Brian + Claude, verbatim, 2026-10-04)

> Phase 3 contract approved with edits (Brian + Claude). Record verbatim. G-ERASE adopted (Brian) as proposed, incl. one-time VACUUM at deploy (client closed, after backup).
> EDITS:
> X1 Retrieval block (gating direct recall needs "when"): each item shows when Brian told her (the episode's source user_time) AND when it happened (event_time or "date unknown"), plus open_items. Proposed shape:
>    - talked about {Mon D} ({relative}) · happened: {Mon D (relative) | date unknown} · {summary}{ · still open: …}
>    Date-only values use calendar wording (same date "today", −1 "yesterday", then format_relative's day/week buckets) — never "about N hours ago" for a date. Tests for both.
> X2 Dedupe: replace UNIQUE(session_id, turn_index) — the provider turn index restarts on relaunch, so post-crash turns in a resumed session would be silently ignored. Use UNIQUE(session_id, user_time, turn_fingerprint) where turn_fingerprint = sha256 of user_text+assistant_text, stored in the row (erased with it). Order by user_time, then created_at. Test: restart mid-session with surviving pending rows → new turns still queued; a repeated sync of the same turn → one row.
> X3 Relevance floor: query terms filtered by Track 4 stopwords; a candidate needs an entity/name hit, a number, or ≥ 2 distinctive terms; then rank by bm25. Phase 4 calibrates EPISODE_MIN_SCORE on the synthetic corpus (related vs unrelated queries incl. "What's a good movie for tonight?") and reports the chosen value and the separation at the Phase 4 STOP.
> X4 Missing user_time → write the turn with user_time NULL (ordering by created_at); stated-time resolution for that turn → unknown. Never drop a keep turn for a missing timestamp. Log the count.
> X5 G-ENTITY-GROUNDING (b): name/alias appears (case-folded substring) in an active fact's text, not equals it.
> X6 sync_turn calls turn_disposition exactly once and passes the result to both logging and the pending writer.
> All else §1–11 approved as proposed.
> proceed to phase 4

### Effective Phase 3→4 edits

| ID | Change |
|---|---|
| X1 | Prefetch item: talked-about (source_user_time) + happened (event_time) + open_items; calendar relative for dates |
| X2 | Dedupe `UNIQUE(session_id, ifnull(user_time,''), turn_fingerprint)`; order `user_time, created_at` |
| X3 | Stopword filter + gate (entity/number/≥2 terms) then bm25; calibrate `EPISODE_MIN_SCORE` in Phase 4 |
| X4 | Missing `user_time` → NULL write (never drop keep); stated-time → unknown; log count |
| X5 | Fact grounding = casefolded **substring** of active fact text |
| X6 | `turn_disposition` once → log + pending writer |
| G-ERASE | **Adopted** (Brian) as proposed + one-time VACUUM at deploy (client closed, after backup) |

## Approved episode contract

As proposed in Phase 3 §1–11, with X1–X6 and G-ERASE adopt above. Phase 4 builds exactly this.
