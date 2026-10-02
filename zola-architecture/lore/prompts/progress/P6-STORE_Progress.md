# P6-STORE Progress — Memory Store Foundation

## Branch

- Branch: `p6-store`
- Base `main` HEAD: `4e2aea90adaa70c7a116d0a456f2918b03c4a565` (after P6-CALC closeout)
- Plan commit SHA: `187275981bdcbfcf3acd87a148bb0606a1c2d1e1` (`docs: Phase 6 build plan v1.1 (P6-D01–D08)`)
- Plan merge SHA: `aee0f0da2ce0382c117013dc57f2cc32f1cd8370` (`Merge branch 'p6-plan'`)
- Prompt version: 1.1 (2026-10-02) against build plan v1.1
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P6-STORE_Prompt_v1.1.md`
  SHA-256 `047b518264dc2bad1a06de06d4599127da2c7a00a2ae93bd53d1cfab476ecb3a` (29,694 bytes; computed 2026-10-02 from the canonical copy; no separate developer-supplied comparison hash was included in the Phase 1 instruction message)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`; expect clean throughout)
- Scratch (outside repos): `C:\Users\test\Dev\zola-spikes\p6-store\`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document | COMPLETE |
| 2 | Grounding (G1–G10) | COMPLETE |
| 3 | Propose the Store Contract | COMPLETE |
| 4 | Build the Provider and Tests | COMPLETE |
| 4b | Contract hardening (repo only) | COMPLETE |
| 5 | Propose the Live Changes | COMPLETE |
| 6 | Back Up, Capture Baseline, Deploy, Activate, Verify | COMPLETE |
| 7 | Smoke Test | COMPLETE — smoke test passed |
| 7b | Skill investigation (read-only) | COMPLETE — Brian accepted |
| 8 | Closeout | IN PROGRESS |

## Guardrails summary

- **G-SCOPE:** Repo new: `hermes-plugins/zola_memory/` (+ tests), this progress doc. Repo modified: `identity/MEMORY_CONVENTIONS.md` (new section only, Phase 3 STOP text). Live profile Phase 6 only after Phase 5 STOP: deploy `plugins/zola_memory/`, `memory.provider: zola_memory` plus only keys Phase 2 proves necessary. No client source; no `approvals.*`; no `SOUL.md`; no `zola_tools` changes.
- **G-ARCH:** Build plan + Appendix A (P6-D01/D02/D03/D06/D07) govern. Conflicts / dependent REFUTED grounding → STOP; do not adapt.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No `windows-client/**`; no `hermes-agent` edits/checkouts/installs; no hand edits to live `memories/`; no live `SOUL.md`, `state.db`, `skills/`, `auth.json`, `.env`, `approvals.*`, `plugins/zola_tools/`; no lore/build-plan/`identity/SOUL.md` edits.
- **G-NO-INSTALL:** Stdlib only. No package installs.
- **G-AUTHORITY (P6-D01/D02):** Provider never writes `USER.md`/`MEMORY.md`, never registers model-facing tools this track (`get_tool_schemas()=[]`), never returns `system_prompt_block` or prefetch content. Indexes only.
- **Track invariant:** If the store vanished, factual knowledge rebuilds from `USER.md`/`MEMORY.md`. If files say a fact is gone, no provider failure may leave its structured copy active.
- **G-FAILCLOSED (P6-D06):** Ambiguity → erasure. Forget-intent may only escalate correction→forget, never reverse.
- **G-PRIVACY:** Live DB may hold real memory text (local Cursor reads OK). Repo docs/logs/tests/stops: IDs, counts, tags, hashes, timings, synthetic text only. Tombstones/logs never contain fact text.
- **G-CONST / G-COMMENT:** Named constants; `# P6-STORE: <rationale> — P6-D0x` per distinct block.
- **G-LIVE / G-STOP / G-CLOSEOUT:** Live steps one at a time; stop after each phase; closeout only on "proceed to closeout".
- **G-LORE-SCOPE:** No lore edits this track (including closeout).
- **G-NO-CROSS-SCOPE:** Android Zola out of scope.

## Discrepancies

- **G1 API shape:** `_ProviderCollector` does **not** expose a public `ctx.llm` attribute (`__getattr__` only forwards `register_*`; non-`register_*` raises `AttributeError`). Host-owned `PluginLlm` is still reachable via `ctx._plugin_context().llm` (real `PluginContext`). Brian accepted with conditions (Phase 2 rulings below).

### Phase 6 lore-closeout inputs (Brian, Phase 7b accepted)

Record for the Phase 6 lore closeout (no lore edits this track — G-LORE-SCOPE):

1. **Background review (A5) procedural memory skill:** during the P6-STORE smoke, the background-review fork (`curator` ledger `2f19297eafde`) authored `skills/communication/conversation-memory` — procedural only (0 synthetic tokens, 0 personal facts; no forget leak; D02 rule 1 holds). At lore closeout, check consistency with `SOUL.md` “What I remember” and P6-D06; **keep or remove is a developer decision**.
2. **G1 private-API coupling:** provider reaches host `PluginLlm` only via `_get_plugin_llm()` → `ctx._plugin_context().llm` on `_ProviderCollector` — private Hermes API, pinned to hermes-agent `v2026.9.14` (`345cd2b0…`).
3. **`hermes backup --quick` excludes the store:** full `hermes backup` covers `$HERMES_HOME/zola_memory/zola_memory.db`; `--quick` does not (G9).
4. **Session-end hooks (Track 5):** `on_session_end` fired twice (15:19:27,212 and ,217) for the same session when a new conversation started; `on_session_switch` and orphan-reap `on_session_end` were **not** observed. Track 5 session-end handling must be **idempotent**.

## Phase 1 notes

- `main` HEAD confirmed `4e2aea90adaa70c7a116d0a456f2918b03c4a565`; porcelain empty.
- Branch `p6-store` created from that tip.
- Progress doc created on `p6-store`, uncommitted until closeout.
- `hermes-agent`: porcelain empty; HEAD `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`).
- P6-CALC baseline: `unittest discover -s hermes-plugins\zola_tools\tests -t hermes-plugins\zola_tools` → **Ran 44 tests — OK**.
- Scratch directory ensured: `C:\Users\test\Dev\zola-spikes\p6-store\`.
- No source implementation yet; live profile unread for write.

## Phase 2 notes

- Read-only grounding complete (Hermes pin `345cd2b0…` clean; live profile read-only).
- No source files modified except this progress doc.
- Scratch harnesses: FTS5 probe + auxiliary auto-route resolution under live `HERMES_HOME` (no model call, no auth change, no live writes).
- No dependent REFUTED / G2 FAIL → not BLOCKED.

### Entry delimiter and normalization (`memory_tool_store.py`)

- Delimiter: `ENTRY_DELIMITER = "\n§\n"` (`tools/memory_tool_store.py` L23).
- Parse: split on the **full** delimiter only; per-piece `.strip()`; drop empties — bare `§` survives (`_parse_entries` L407–409).
- Writes: `content` / `new_content` / `old_text` are `.strip()`'d on add/replace/remove (L239, L261–274).
- Match: case-sensitive substring `old_text in e` (`_find_unique_match` L58–64) — **no** casefold.
- Read encoding: `utf-8-sig` (BOM strip only) L392–402.

### Live memory counts (counts only; 2026-10-02)

| File | Entries (`\n§\n` split) | Characters |
|---|---|---|
| `USER.md` | 13 | 2108 |
| `MEMORY.md` | 1 | 234 |

Live `config.yaml`: `model.provider=openai-codex`, `model.default=gpt-5.6-terra`; `memory.memory_char_limit=4400`, `memory.user_char_limit=4000`; **no** `memory.provider` key; `plugins.enabled: [zola_tools]`; **no** `auxiliary.*` block; `approvals.mode: manual`.

## G1–G10 grounding table

| ID | Verdict | File:lines | One-line answer |
|---|---|---|---|
| G1 `ctx.llm` | **[CONFIRMED]** | `plugins/memory/__init__.py` L295–373 (`_ProviderCollector` / `_plugin_context`); `hermes_cli/plugins.py` L386–393 (`PluginContext.llm`); `agent/plugin_llm.py` L1–8, L121–134, L498–519 | Collector builds a real `PluginContext`; host `PluginLlm` via `ctx._plugin_context().llm` (stash at `register`). Public `ctx.llm` not delegated. Plain `complete_structured` needs **no** `plugins.entries.<id>.llm.*` trust flags (missing block = no overrides only). |
| G2 trust boundary | **[CONFIRMED] PASS** | Live `config.yaml` L1–4; `agent/auxiliary_client.py` L4165–4236, L5653–5721; probe: `_resolve_auto_route` → `openai-codex` / `gpt-5.6-terra` | Main = `openai-codex` / `gpt-5.6-terra` (`model.provider` / `model.default`). `plugin_llm` → `call_llm` with no overrides resolves `"auto"` → same provider+model. Same provider → PASS (P6-D07). |
| G3 `sync_turn` | **[CONFIRMED]** | `agent/turn_finalizer.py` L603–607; `run_agent.py` L875–906; `agent/memory_manager.py` L480–518; `memory_provider.py` L124–130 | Fires once per **completed** turn via agent finalizer (tui runs `run_conversation`); user+assistant text + `session_id` on background executor. Identity: `session_id`, optional `messages`, optional `turn_author` — **no** message/turn IDs. Interrupted turns **do not** sync (early return L879–889). |
| G4 `pre_llm_call` | **[CONFIRMED]** | `plugins/memory/__init__.py` L319–322; `agent/turn_context.py` L663–717, L980–984, L793–809, L1046–1107; `hermes_cli/plugins_ledger.py` L191–201 | Memory `register_hook` → fallback hooks invoked by `invoke_hook("pre_llm_call")` every user turn (no trivial-prompt gate; that gate is prefetch-only L779–782). Returned context → user-turn `api_content` sidecar and replayed on later turns. |
| G5 `on_turn_start` | **[CONFIRMED]** | `agent/turn_context.py` L762–778; `memory_provider.py` L145–148; `memory_manager.py` L601–606 | Receives current user message text (`original_user_message`) every turn, including trivial prompts. |
| G6 activation side effects | **[CONFIRMED]** | `agent/agent_init.py` L1228–1296; `memory_manager.py` L106–146, L384–402; `tui_gateway/server.py` L2112–2128 | Empty provider (`system_prompt_block=""`, `get_tool_schemas=[]`, `prefetch=""`) adds no prompt text and no tools; built-in memory tool remains. Lifecycle/mirroring still attach. **Capture method:** live `session.info` RPC (`tools` + `system_prompt` from `_cached_system_prompt`); offline: construct `AIAgent` under live `HERMES_HOME` and dump tool names + `build_system_prompt` (no completion). |
| G7 `on_memory_write` metadata | **[CONFIRMED]** | `memory_provider.py` L185–187; `memory_manager.py` L712–774; `inline_tool_executors.py` L114–133 | Keyword `metadata` mode when signature accepts it; `old_text` forwarded for replace/remove when present. Sync after committed file write (`success` and not staged). Exceptions swallowed (`_each_provider` / notify try/except). |
| G8 FTS5 | **[CONFIRMED]** | Hermes venv sqlite 3.53.1; `PRAGMA compile_options` includes `ENABLE_FTS5`; `CREATE VIRTUAL TABLE … USING fts5` OK | Available in `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`. |
| G9 backup coverage | **[CONFIRMED]** with known limits | `hermes_cli/backup.py` L88–92, L257–266, L319–357, L558–591, L658–668 | Full `hermes backup` includes `$HERMES_HOME/zola_memory/zola_memory.db` if present (root walk + `*.db` snapshot). **WAL/SHM excluded** by design. **`--quick` does not** list `zola_memory/…`. |
| G9 backup consistency | **[CONFIRMED]** | `hermes_cli/backup.py` L319–357 (`_safe_copy_db` → `sqlite3.backup`) | Uses SQLite backup API (WAL-safe point-in-time snapshot), not a torn main-file copy. Known limitation: sidecars not archived (regenerated on open); P6-D07 coverage promise met. |
| G10 single load path | **[CONFIRMED]** | `plugins/memory/__init__.py` L189–208, L261–290; `agent/agent_init.py` L1267–1287; `plugins_discovery.py` L146–149, L194–199; `plugins_manifest.py` L251–256 | Loaded once via `memory.provider` → `load_memory_provider`. General loader treats MemoryProvider markers as `kind: exclusive` → placeholder, not activated. **`plugin.yaml` optional** (recommend present with exclusive/memory markers, or omit); **must not** be a non-exclusive standalone opted into `plugins.enabled`. **`plugins.enabled` must not list it** for activation (not required; memory path owns it). Hooks via memory `register_hook` do **not** need `plugins.enabled`. |

## Phase 2 rulings (Brian, verbatim, 2026-10-02)

> Phase 2 reviewed and accepted (Brian). Rulings:
> 1. G1 (private API): accepted with conditions. In __init__.py, keep the PluginContext handle through ONE accessor function (e.g. _get_plugin_llm()) that is the only place referencing ctx._plugin_context(). At register/initialize, probe it once; if unavailable, log a named WARNING event and set an internal flag llm_available=False (Track 5 will fail closed on it; nothing else depends on it). No model calls in this track. Record the coupling (private Hermes API, pinned to v2026.9.14) in the progress doc as a known dependency for the Phase 6 lore closeout.
> 2. G10: plan to OMIT plugin.yaml from hermes-plugins/zola_memory/ (memory path loads it; general loader never sees it). Confirm in Phase 5's deploy list.
> 3. G3: note for Track 5 recorded — interrupted turns don't sync; no message IDs (provider assigns its own per-session turn sequence).
> 4. G9: record that `hermes backup --quick` does not include the store (full backup only).

### Effective rulings (recorded)

1. **G1:** Single accessor `_get_plugin_llm()` is the only call site for `ctx._plugin_context()`. Probe once at register/initialize; on failure log WARNING + `llm_available=False`. No model calls in P6-STORE. **Known dependency (Phase 6 lore closeout):** private Hermes API `PluginContext` via `_ProviderCollector._plugin_context()`, pinned to hermes-agent `v2026.9.14` (`345cd2b0…`).
2. **G10:** **Omit** `plugin.yaml` from `hermes-plugins/zola_memory/` (and from the Phase 5 deploy list).
3. **G3 → Track 5:** interrupted turns do not sync; no host message IDs — provider will assign its own per-session turn sequence.
4. **G9:** `hermes backup --quick` does **not** include `zola_memory/zola_memory.db`; full backup only.

## Proposed store contract (awaiting Brian's approval)

Nothing built yet. Phase 4 builds exactly what is approved here.

### 1. Schema

**Migration / version:** `meta` key `schema_version` (integer string). Current `SCHEMA_VERSION = 1`. On open: create if missing, apply ordered migrations inside `BEGIN IMMEDIATE` until current. Fail closed on unknown future version.

**`meta`** — key/value store (`key TEXT PRIMARY KEY`, `value TEXT NOT NULL`):
| Key | Purpose |
|---|---|
| `schema_version` | integer as text |
| `files_sha256` | last combined SHA-256 of `USER.md`+`MEMORY.md` bytes (utf-8-sig normalized path below) |
| `last_interaction_at` | Track 3 marker (created now; unused this track) |
| `pending_erasures` | JSON array of fact IDs awaiting erase retry (operational help only; files are authority) |

**`facts`**
| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | UUID4 |
| `target` | TEXT | `user` \| `memory` |
| `text` | TEXT | entry body as stored (post-strip) |
| `tag` | TEXT NULL | leading `[tag]` if present (lowercase letters inside brackets); else NULL |
| `state` | TEXT | `active` \| `superseded` only — never "forgotten" |
| `learned_at` | TEXT NULL | ISO-8601 UTC; set **only** on notified `add` |
| `indexed_at` | TEXT NOT NULL | ISO-8601 UTC; when store first saw the entry |
| `updated_at` | TEXT NULL | set on notified correction `replace` |
| `superseded_at` | TEXT NULL | set when this row becomes `superseded` |
| `source` | TEXT | `notify` \| `file_check` |

Indexes: `(target, state)`, `(state)`, unique partial index on `(target, text)` **WHERE state='active'`** (one active copy of identical text per target).

**`facts_fts`** — FTS5 virtual table over `facts.text` (content-sync / external-content pattern; rowid tied to facts). Deleted with the fact on erase.

**`fact_history`** (corrections only)
| Column | Type |
|---|---|
| `id` | TEXT PK (UUID4) |
| `fact_id` | TEXT NOT NULL (same fact ID retained across correction) |
| `text` | TEXT NOT NULL (old text) |
| `superseded_at` | TEXT NOT NULL |

Index: `(fact_id)`.

**`entities`** / **`entity_aliases`** (empty until Tracks 4–5; created now)
- `entities(id TEXT PK, name TEXT NOT NULL, kind TEXT NOT NULL, created_at TEXT NOT NULL)` + unique `(name, kind)`
- `entity_aliases(entity_id TEXT NOT NULL, alias TEXT NOT NULL, PRIMARY KEY(entity_id, alias))` + unique `(alias)`

**Fact↔entity links are not stored** (inferred at read time).

**`tombstones`**
| Column | Type |
|---|---|
| `id` | TEXT PK (erased record's ID) |
| `record_kind` | TEXT (`fact` this track; later `episode` / `pending_turn`) |
| `erased_at` | TEXT NOT NULL |
| `counts_json` | TEXT NOT NULL — e.g. `{"fact_rows":1,"history_rows":n,"fts_rows":1}` |

No text, hash, fingerprint, or recoverable content.

**Tracks 4–5 tables (created empty now)**

`episodes(id, summary, significance, event_time, event_time_basis, event_time_evidence, open_items_json, source_session_id, source_turn_start, source_turn_end, recorded_at)` — all TEXT/INTEGER as appropriate; unused this track.

`episode_entities(episode_id, entity_id)` PK `(episode_id, entity_id)`.

`episode_fact_refs(episode_id, fact_id)` PK `(episode_id, fact_id)`.

`pending_turns(id, session_id, turn_index, user_text, assistant_text, user_time, assistant_time, consolidation_generation, forget_hold, created_at)` — `turn_index` is the **provider-assigned** per-session sequence (G3 ruling); no host message IDs.

### 2. Database location

- Path: `$HERMES_HOME/zola_memory/zola_memory.db` (directory created as needed).
- Mode: WAL (`PRAGMA journal_mode=WAL`), `PRAGMA foreign_keys=ON`.
- Every write transaction: `BEGIN IMMEDIATE` … `COMMIT` / `ROLLBACK`.
- Backup: full `hermes backup` covers the `.db` via `sqlite3.backup()`; WAL/SHM excluded; **`hermes backup --quick` does not include the store**.

### 3. Fact identity rules

- **Normalization for identity / file-check set membership** (named `normalize_entry`):
  1. Decode file with `utf-8-sig` when reading from disk.
  2. Split on full delimiter `"\n§\n"` only.
  3. `strip()` each piece; drop empties (bare `§` survives as content if present inside a piece).
  4. **No** casefold / whitespace collapse beyond strip — matches Hermes `MemoryStore._parse_entries`.
- An active fact's identity key is `(target, normalize_entry(text))` with `text` already stripped as Hermes stores it.
- **`add` (notify):** new UUID; `state=active`; `source=notify`; `indexed_at=now`; `learned_at=now`.
- **`replace` (notify) with `old_text`:** locate active fact whose text contains / equals the stripped `old_text` the same way Hermes matches (substring uniqueness). Same `fact_id` kept: append `fact_history` row with old text; update `text`/`tag`; `updated_at=now`; if prior state was active stay active. **Unless** forget-intent fires → erase instead (no history).
- **`remove` (notify):** erase cascade (forget).
- **File-check new entry:** new UUID; `source=file_check`; `indexed_at=now`; **`learned_at=NULL`**.
- **Initial import** at activation: same as file-check new (`learned_at=NULL`).

### 4. File-check rules

**When:**
- Always at `initialize()` after migrate.
- At `on_turn_start`: compute combined SHA-256 of the two files' raw bytes (missing file = empty bytes); if equal to `meta.files_sha256`, **skip**; else run full check and update the hash.

**Diff (fail closed):**
- Build set of `(target, normalized_text)` from files.
- Active facts missing from the set with no completed erase → **erase** (no history). Files are the recovery signal even if `pending_erasures` write failed.
- File entries with no matching active fact → insert as `file_check` (`learned_at=NULL`).
- Whitespace/`§` reformatting that round-trips through `normalize_entry` → **no** change.
- Unchanged hash → skipped (no row churn).

**Erase transaction (`erase_fact`):** one `BEGIN IMMEDIATE`: delete fact + FTS + history rows; insert tombstone; commit. On failure: rollback fully; then best-effort separate txn to append fact ID to `meta.pending_erasures`. Next file check retries erase from file absence regardless.

### 5. Forget-intent phrase list (P6-D06)

Named constant `FORGET_INTENT_PHRASES` (match case-insensitively on **word boundaries** in the current turn's user message from `on_turn_start`; kept in memory only, never persisted):

```
forget
don't remember
do not remember
don't keep
do not keep
stop remembering
delete
erase
remove that
get rid of
no longer remember
```

**Scope:** a match is evidence that **this** `replace` (same memory-tool op / same `old_text`) may be a forget. Never broadens to other facts or later turns. Escalation only (correction → erase); never the reverse.

**Heuristic examples (crude; false positives erase old-text history only):**

| User message (synthetic) | Heuristic | Expected store outcome if she `replace`s |
|---|---|---|
| "When I said 'forget my address' yesterday, I didn't mean it; my address is actually 1 Demo Lane" | **match** (`forget`) — false positive accepted | erase old text (no history) |
| "Don't forget that I moved" | **no match** (`don't forget` ≠ listed phrases as whole; `forget` alone is a word — **will match `forget`**) — false positive risk | if treated as match → erase; noted as crude |
| "Actually, the car is blue, not green" | **no match** | correction: same ID + history row |
| "Please forget the demo project codename" | **match** | erase |
| "Don't keep my demo phone number anymore, just keep that I have a landline" | **match** (`don't keep`) | erase old; she may also `remove`+`add` |

Refinement for "Don't forget…": proposal matches bare `forget` as a word boundary, so "Don't forget that…" **is a false positive**. Acceptable under P6-D06 (stricter). Alternative if Brian prefers: require phrases as listed only (still matches `forget` as its own phrase). **Starting proposal keeps word-boundary match on each phrase including the single word `forget`.**

### 6. Tombstone format

```json
{
  "id": "<erased-record-id>",
  "record_kind": "fact",
  "erased_at": "<ISO-8601 UTC>",
  "counts_json": "{\"fact_rows\":1,\"history_rows\":N,\"fts_rows\":1}"
}
```

Stored as table columns (not a JSON blob row). No fact text anywhere.

### 7. Log events (`zola_memory.log`)

Named prefixes (IDs, counts, ms only — never fact text):

| Event | Fields (metadata only) |
|---|---|
| `zola_memory.initialize` | ok, schema_version, fts_ok, import_count, elapsed_ms |
| `zola_memory.llm_probe` | llm_available (WARNING when false) |
| `zola_memory.file_check` | ran, drift, added, erased, skipped_hash_match, elapsed_ms |
| `zola_memory.fact_add` | fact_id, target, source |
| `zola_memory.fact_replace` | fact_id, target, history=1 |
| `zola_memory.fact_erase` | fact_id, reason (`remove`\|`forget_intent`\|`file_check`\|`pending_retry`), history_rows, ok |
| `zola_memory.erase_rollback` | fact_id |
| `zola_memory.pending_erasure_mark` | fact_id, ok |
| `zola_memory.on_turn_start` | session_id, turn_number, msg_len |
| `zola_memory.sync_turn` | session_id, user_len, assistant_len |
| `zola_memory.on_session_end` | session_id, message_count |
| `zola_memory.on_session_switch` | session_id, parent_session_id, reset, rewound |
| `zola_memory.on_pre_compress` | session_id, message_count |
| `zola_memory.prefetch` | session_id, returned_len=0 |
| `zola_memory.shutdown` | ok |

Hook observers this track are **logging-only** (no returned context).

### 8. Proposed `MEMORY_CONVENTIONS.md` section

Append as a new section (existing text untouched):

```markdown
## Structured store (P6)

Two kinds of memory, one authority each. The flat files (`USER.md` / `MEMORY.md`) remain the
authority for current durable facts — written only through the memory tool. A local Zola store
keeps a structured index of those facts (stable IDs, lifecycle times) and will later hold
episodes. The index is always rebuildable from the files. Episodes, when they exist, are the
store's own authority; they may reference facts but never create or change them.

Invariants in short: Zola authors facts through the memory tool; the store does not write the
files and does not invent facts. Correction keeps a content history; forget erases every copy
the memory system controls and leaves only a content-free tombstone. Ambiguous disappearances
and unclear "replace vs forget" cases resolve toward erasure. Retrieval never becomes
persistence.

(P6-D01–D07)
```

### Implementation notes bound by Phase 2 rulings (Phase 4)

- **No `plugin.yaml`** in `hermes-plugins/zola_memory/`.
- **`__init__.py`:** `_get_plugin_llm()` sole `_plugin_context()` call site; probe → `llm_available`; WARNING `zola_memory.llm_probe` if false.
- **G-AUTHORITY:** `system_prompt_block`→`""`; `get_tool_schemas`→`[]`; `prefetch`→`""`; never open memory files for write.
- Stdlib only; temp `HERMES_HOME` in tests; content scan on tombstones/logs.

## Approved store contract

Brian's approval message (verbatim, 2026-10-02):

> Phase 3 contract approved with these edits (Brian). Record verbatim under "Approved store contract", then build exactly the edited contract.
> 1. Forget-intent exclusions: add a named constant FORGET_INTENT_EXCLUSIONS = ["don't forget", "do not forget", "never forget", "won't forget", "not forget"]. A bare "forget" match is cancelled when it occurs inside one of these phrases. Other phrases unaffected. Update the example table so "Don't forget that I moved" → no match (correction keeps history), and keep the quoted "When I said 'forget my address'…" → match (accepted false positive). Add unit tests for both.
> 2. Replace with no unique store match: if a notified replace's old_text has no unique active match in the store (or any uniqueness/constraint conflict occurs during a notified add/replace), do not guess — run the full file check instead: the missing old entry is erased without history (fail closed) and the new entry is indexed as file_check with learned_at NULL. Log a named event (e.g. zola_memory.replace_unmatched) with IDs/counts only. Add unit tests (store lagging behind a bypass edit; ambiguous substring match).
> 3. Entities: remove UNIQUE(name, kind) on entities and UNIQUE(alias) on entity_aliases. Keep plain (non-unique) indexes on entities(name) and entity_aliases(alias). Entity resolution is decided in Track 5.
> Everything else as proposed (schema otherwise, DB path/WAL/BEGIN IMMEDIATE, identity and normalization, file-check rules, erase + separate pending marker, phrase list, tombstones, log events, MEMORY_CONVENTIONS text, no plugin.yaml, single _get_plugin_llm accessor).

### Effective approved contract

Phase 3 proposal as written, with the three edits above. Notable deltas from the proposal:
- `FORGET_INTENT_EXCLUSIONS` cancels bare `forget` inside those phrases; "Don't forget that I moved" → no match.
- Notified replace without unique store match (or add/replace uniqueness conflict) → full file check + `zola_memory.replace_unmatched` log; no guessing.
- `entities` / `entity_aliases`: non-unique indexes only (no UNIQUE constraints).

## Phase 5 proposals (awaiting Brian's approval)

Nothing applied. Live profile unread for write.

### 1. Deploy file list (repo SHA-256)

Copy `hermes-plugins/zola_memory/` → `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\`, excluding `tests/` and `__pycache__/`.

**`plugin.yaml`: OMITTED** (G10 ruling — memory path loads via `memory.provider`; general loader must not see a manifest).

| Repo file | SHA-256 | Bytes |
|---|---|---|
| `__init__.py` | `d66e363274d6160d73fe6c06a6c2a23b3c54dc3a7cda34be2f3af1d8f4f1e6da` | 2078 |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | 379 |
| `provider.py` | `3a98fa9ca5084b73c0568a41f1b3b88fe8c671c170de2d570def3f47ae17de48` | 6921 |
| `store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` | 9384 |
| `fact_index.py` | `b6dd9710fe776b21fa963878929acfdd134888384c772746ba687c33bf23cb24` | 14820 |
| `forget.py` | `1e50246501f9274190426961d4526ca84ebeff7b3a580b9f63f6c514a5663d7c` | 6982 |
| `log.py` | `c596c90bbdd8ef10d329fa76ce543e9b45602364b438a107b3081a014d1b9eac` | 3245 |

Live `plugins/zola_memory` does not exist yet (first deploy). `plugins/zola_tools/` unchanged.

### 2. Exact `config.yaml` diff

Under the existing `memory:` block (after the char-limit keys), add **only**:

```yaml
  provider: zola_memory  # P6-STORE: Zola-owned local memory provider — P6-D03
```

**Not proposed (grounding):**
- No `plugins.enabled` entry for `zola_memory` (G10 — must not list it).
- No `plugins.entries.zola_memory.llm.*` trust flags (G1 — plain calls need none).
- No `auxiliary.*` pin (G2 PASS — same `openai-codex` / `gpt-5.6-terra`).
- No `approvals.*` change. No `SOUL.md` change. No `zola_tools` change.

### 3. G6 baseline capture plan

**Method (primary):** with the client running on the current config, capture via TUI/gateway `session.info` (or equivalent client debug surface that exposes the same payload):
- `tools` — grouped tool names from the live agent
- `system_prompt` — from `_cached_system_prompt` / session mirror

Store full captures under scratch only: `C:\Users\test\Dev\zola-spikes\p6-store\g6-before\` and `g6-after\` (may contain personal memory text — never committed).

**Compare:**
- **Tool list:** exact set equality of tool names (sorted). Must be identical.
- **System prompt:** SHA-256 of normalized text (LF). Allowlisted differences only: per-session timestamp / date lines that already vary without a provider. Any other difference → STOP.

**Fallback (if session.info unavailable):** offline `AIAgent` under live `HERMES_HOME` dumping tool names + `build_system_prompt` (no completion) — same compare rules. Prefer live session.info so Phase 6 matches the running client.

**Unchanged means:** tool name set identical; system prompt identical aside from the allowlisted per-session fields listed in the Phase 6 notes.

### 4. Smoke script (Phase 7 Part B — synthetic, blind)

Cursor holds the script; Brian types one step at a time; Cursor never shows the expected store outcome to Zola. All names/details are fictional.

| Step | Brian types (natural) | Expected store / tool behavior (Cursor checks) |
|---|---|---|
| B1 | lasting fact about a fictional project | `add` → active fact (`notify`, `learned_at` set) |
| B2 | lasting fact about a fictional person preference | `add` → second active fact |
| B3 | correction of B1 (“actually, …”) | `replace` without forget-intent → same fact ID + 1 history row |
| B4 | forget B2 using “forget” wording | `remove` → erased + content-free tombstone |
| B5 | semantic forget of remaining project detail without “forget”: e.g. “don’t keep my [synthetic detail] anymore, just keep [reduced]” | if `replace` → escalated erase (no history); if `remove`+`add` → also correct; record which |
| B6 | unprompted-save regression statement A (natural lasting fact) | she saves without being asked → `add` |
| B7 | unprompted-save regression statement B | she saves → `add` |
| B8 | **new conversation**; ask her to recall B6 and B7 | both recalled (files/authority); Cursor confirms active facts still present |

Exact wording of B1–B8 is finalized by Cursor at Phase 7 start (still synthetic) and shown to Brian one line at a time — not listed here in full to keep this doc free of unused fixture text. Theme: fictional people, cars, projects only.

### 5. Rollback

1. Restore `config.yaml` from Phase 6 backup (removes / clears `memory.provider`, restoring pre-activation hash).
2. Relaunch the client.
3. Database at `$HERMES_HOME/zola_memory/zola_memory.db` **stays** for diagnosis; nothing reads it with the provider off.
4. Deployed `plugins/zola_memory/` may remain on disk unused, or be left for inspection — not required to delete for rollback of behavior.

## Approved live changes

Brian's approval message (verbatim, 2026-10-02):

> Phase 5 approved with one edit (Brian). Record verbatim under "Approved live changes".
> 1. Deploy list: approved (7 files, hashes as listed; plugin.yaml omitted).
> 2. config.yaml: approved — only `provider: zola_memory` under the existing memory: block with the P6-STORE comment. Nothing else.
> 3. G6 capture plan: approved (session.info primary; offline fallback; tool-name set must be identical; system prompt identical except allowlisted per-session timestamp/date lines — list each allowlisted line explicitly in the Phase 6 notes before comparing).
> 4. Smoke script: use exactly these lines (synthetic; held by Cursor and Brian, never shown to Zola as a test):
>    B1: "The Nimbus Garden project I'm helping my neighbor with — we're going with cedar for the raised beds."
>    B2: "My buddy Rowan only drinks oat milk, by the way, so keep that in mind when he comes over."
>    B3: "Oh, and don't forget — we switched the Nimbus Garden beds from cedar to redwood."  (expected: correction with history; also live-tests FORGET_INTENT_EXCLUSIONS)
>    B4: "Actually, forget what I said about Rowan and the oat milk."
>    B5: "Don't keep the wood type for the Nimbus Garden anymore, just keep that it's a raised-bed project for my neighbor."
>    B6: "I've started racing go-karts at Pinecrest Speedway on Sunday mornings."
>    B7: "My sister Talia just moved to Spokane."
>    B8 (new conversation): "Where does my sister live now, and what do I do on Sunday mornings?"
>    Cleanup (Part D): Brian asks her to forget the remaining Nimbus Garden, Pinecrest and Talia facts.
> 5. Rollback: approved as proposed.
> proceed to phase 6

### Effective approved live changes

- **Deploy:** 7 files to `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\` (hashes as Phase 5 table); **no** `plugin.yaml`; no `tests/`.
- **config.yaml:** under existing `memory:` only:
  ```yaml
    provider: zola_memory  # P6-STORE: Zola-owned local memory provider — P6-D03
  ```
- **G6:** session.info primary; offline fallback; tool-name set identical; system prompt identical except allowlisted per-session timestamp/date lines (list each explicitly in Phase 6 notes before comparing).
- **Smoke (Phase 7):** exact B1–B8 + Part D cleanup lines above (synthetic; blind).
- **Rollback:** restore `config.yaml` from backup; relaunch; DB stays.

## Backup hashes

Backup dir: `C:\Users\test\Dev\zola-spikes\p6-store\backup\`

| Artifact | SHA-256 |
|---|---|
| `config.yaml` (pre-edit) | `b54acb165ce45842f3311d7430d3624a1a3b4c1eb0d4b4f61b6fa987f67542a1` |
| `memories/USER.md` | `47a732a0b218936c9b465f6bb8ada34bcda4fe027660f000e9b139b4e7022d12` |
| `memories/MEMORY.md` | `8264268512e5cc7a37fff847f523ca142c310dbf21bef30c2ad601ee3a5986eb` |
| `plugins_listing.txt` | `6f55b3a736c683eeb00772b991cb637e337a64028b284e7e497b75526219ab9e` |
| `approvals:` block (pre/post) | `7d191e543313c217084db4ddd8041116494bba8a8458d9c5d1baef77b8809c1c` (unchanged) |

Pre-deploy plugins listing: `zola_tools/` only (3 source files + `__pycache__`). Memory entry counts at backup: USER **13**, MEMORY **1** (matches Phase 2).

## Deployed-file hash table

| File | Repo SHA-256 | Live SHA-256 | Match |
|---|---|---|---|
| `__init__.py` | `d66e363274d6160d73fe6c06a6c2a23b3c54dc3a7cda34be2f3af1d8f4f1e6da` | same | ✅ |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | same | ✅ |
| `provider.py` | `3a98fa9ca5084b73c0568a41f1b3b88fe8c671c170de2d570def3f47ae17de48` | same | ✅ |
| `store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` | same | ✅ |
| `fact_index.py` | `b6dd9710fe776b21fa963878929acfdd134888384c772746ba687c33bf23cb24` | same | ✅ |
| `forget.py` | `1e50246501f9274190426961d4526ca84ebeff7b3a580b9f63f6c514a5663d7c` | same | ✅ |
| `log.py` | `c596c90bbdd8ef10d329fa76ce543e9b45602364b438a107b3081a014d1b9eac` | same | ✅ |

Live path: `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\` — **no** `plugin.yaml`, no `tests/`, no `__pycache__/`.

### Live `config.yaml` after apply

| File | Before | After |
|---|---|---|
| `config.yaml` | `b54acb165ce45842f3311d7430d3624a1a3b4c1eb0d4b4f61b6fa987f67542a1` | `7ba2e676a04ff92047c8d711fcb022be8a532b11baac6f74b08986744e704570` |

Unified diff (vs backup): **only** the approved line under `memory:`:
```diff
+  provider: zola_memory  # P6-STORE: Zola-owned local memory provider — P6-D03
```

`plugins/zola_tools/` hashes unchanged (`a1ef8541…` / `0f29f3fc…` / `f329e906…`). `approvals:` block unchanged. `hermes-agent` porcelain empty at `345cd2b0…`.

### Restart / load verification

- Closed Zola.Client (pid 22476) and leftover `zola serve`; relaunched client (pid **19020**) at 2026-10-02 14:57:27 PDT.
- Serve child: pid 13200 (`hermes-agent\.venv\…\python.exe -m hermes_cli.main -p zola serve`); grandchild 20128 (uv python re-exec — normal).
- `agent.log` 14:57:33: `Plugin discovery complete: 59 found, 53 enabled` (unchanged vs P6-CALC — `zola_memory` not in general `plugins.enabled`).
- `agent.log` 14:57:41: `Memory provider 'zola_memory' registered (0 tools)` then `Memory provider 'zola_memory' activated` — **once** in the live serve process (G10).
- `zola_memory.log` 14:57:41: `initialize ok=true schema_version=1 fts_ok=true import_count=14`; DB created at `%LOCALAPPDATA%\hermes\profiles\zola\zola_memory\zola_memory.db`.
- Import counts: active **user=13**, **memory=1** (total 14) — equals Phase 2 live counts; all 14 have `learned_at` NULL; `source=file_check`; FTS rows=14; tombstones=0.

## Activation baseline comparison (G6)

Scratch captures (personal memory text — never committed): `C:\Users\test\Dev\zola-spikes\p6-store\g6-before\`, `g6-after\`.

### Allowlisted per-session lines (listed before compare — Brian edit)

Only this line prefix is allowlisted as a per-session timestamp/date field:

- `Conversation started:`

Observed instances:

| Capture | Line index | Value |
|---|---|---|
| Offline before | 257 | `Conversation started: Friday, October 02, 2026 (Pacific Daylight Time, UTC-07:00)` |
| Offline after | 257 | `Conversation started: Friday, October 02, 2026 (Pacific Daylight Time, UTC-07:00)` |

(No other date/timestamp prompt lines are allowlisted.)

### Method

1. **session.info primary (live mirror):** before deploy, read open session `20261002_134120_b53232` from `state.db` (`system_prompts.prompt` via `system_prompt_hash` + `sessions.tool_names`). Secondary WS RPC not used (would require a second authenticated `/api/ws` against the live client).
2. **Offline fallback (activation compare):** `AIAgent(quiet_mode=True, platform='desktop')` under live `HERMES_HOME`, dump tool names + `_build_system_prompt` / `_cached_system_prompt` (no completion). Used for before→after because the client **resumed** the same session after relaunch; the DB-mirrored prompt hash did not re-fingerprint a new build, so offline before (provider off) vs offline after (provider on) is the fair activation side-effect check.

### Result

| Check | Result |
|---|---|
| Tool-name set (offline before vs after) | ✅ identical (19 names; sorted set equal) |
| Tool-name set (live session mirror before vs after resume) | ✅ identical |
| System prompt after stripping allowlisted `Conversation started:` lines (offline) | ✅ identical (SHA-256 `04c4bc4d…` both sides including the identical allowlisted line) |
| Live session prompt SHA (resume; same session) | `6024a3a9…` before = after (expected under resume; not used alone for activation claim) |

G6 **PASS** — empty provider adds no tools and no prompt text.

### Note on second initialize in `zola_memory.log`

A Cursor offline G6-after probe at 14:58:25 constructed a second short-lived `AIAgent` (initialize import_count=0 / hash path, then `on_session_end` + `shutdown`). That is **not** a second load inside the live serve process. Live serve: one register + one activate at 14:57:41.

## Hook-firing table (AUD-36)

### Part A — log offsets (before hook proof)

Recorded 2026-10-02 15:00:53 PDT. Scratch: `C:\Users\test\Dev\zola-spikes\p6-store\phase7\log_offsets_part_a.json`.

| Log | Exists | Byte offset |
|---|---|---|
| `zola_memory.log` | yes | 2600 |
| `agent.log` | yes | 3628553 |
| `tool-events.log` | no | 0 |

Client pid 19020 (since 14:57:27).

### Hook-firing table (after Brian's Part A sequence)

Brian reported done at ~15:08. Observed in `zola_memory.log` / `agent.log` (session `20261002_145734_57ad69`, ui `e818102e`; first user turn `"Hello Zola"` / 10 chars). **Observed, not relied on.**

| Event | Timestamp | Notes |
|---|---|---|
| `initialize` | 14:57:41,899 (Phase 6 relaunch) | `ok=true schema_version=1 fts_ok=true import_count=14` — not re-logged on the 15:07 turn |
| `llm_probe` | 15:07:55,596 | `llm_available=true` (lazy agent build on first prompt after relaunch) |
| `pre_llm_call` | 15:07:56,068 | `session_id=20261002_145734_57ad69 observer=1` |
| `on_turn_start` | 15:07:56,071 | `session_id=-` (provider turn counter), `turn_number=1`, `msg_len=10` |
| `prefetch` | 15:07:56,074 | `session_id=20261002_145734_57ad69 returned_len=0` (empty) |
| `sync_turn` | 15:07:58,880 | `session_id=20261002_145734_57ad69 user_len=10 assistant_len=13` |
| `on_session_switch` | — | **not observed** |
| `on_session_end` (orphan ~20s reap) | — during Part A | **not observed** in Part A window |
| `on_session_end` (later, B8 redo) | 15:19:27,212 **and** 15:19:27,217 | Fired **twice** for the same session `20261002_145734_57ad69` (`message_count=32`) when a new conversation started; then `shutdown ok=true` on that agent |
| `on_session_switch` | — | **not observed** (Part A or later) |
| `on_session_end` (orphan ~20s reap) | — | **not observed** |

**Track 5 input:** `on_session_end` double-fire (15:19:27,212 / ,217) means session-end handling must be **idempotent**. `on_session_switch` and orphan-reap `on_session_end` were not observed this track.

Part A itself only produced one user turn (new conversation + one message). Session-end was observed later when B8 opened a further new conversation.

## Smoke results

### Part B — blind script (approved lines; one step at a time)

| Step | Memory-tool action | Store outcome (IDs/counts) | Privacy |
|---|---|---|---|
| B1 | `memory` tool completed → provider `fact_add` `source=notify` `target=memory` | fact `609306a6-5992-453c-bff7-eb5b35107ced` active; `learned_at` set; active 14→15 (memory 1→2); history 0; tombstones 0; MEMORY.md entries 1→2 | log/tombstones clean |
| B2 | `memory` → `fact_add` `source=notify` `target=user` | fact `1b7c0ffa-d761-40fa-9882-a389b80a9a50` active; `learned_at` set; active 15→16 (user 13→14); history 0; tombstones 0; USER.md entries 13→14 | log/tombstones clean |
| B3 | `memory` → `fact_replace` (same id; history kept) | fact `609306a6-…` still active; history row `7b644c08-…` on that fact_id; active still 16; tombstones 0; FTS cedar→0 redwood→1; exclusions path (no erase) | log/tombstones clean |
| B4 | `memory` → `fact_erase` `reason=remove` | fact `1b7c0ffa-…` erased; tombstone same id `counts_json={"fact_rows":1,"history_rows":0,"fts_rows":1}`; active 16→15 (user 14→13); FTS Rowan/oat→0 | log/tombstones clean |
| B5 | `memory` → `fact_erase` `reason=forget_intent` (replace escalated); reduced entry via `file_check` add | erased `609306a6-…` (tombstone history_rows=1); new active `b5c542a8-…` `source=file_check`; history table 0; tombstones 2; FTS redwood→0 Nimbus remains 1 | log/tombstones clean |
| B6 | `memory` → `fact_add` `source=notify` `target=user` (unprompted) | fact `394506ae-9a94-47a0-8461-f008cee65408` active; `learned_at` set; active 15→16; FTS Pinecrest→1 | log/tombstones clean |
| B7 | `memory` → `fact_add` `source=notify` `target=user` (unprompted) | fact `67bf64c0-8296-4595-ad5e-401de7592b70` active; `learned_at` set; active 16→17; FTS Talia/Spokane→1 | log/tombstones clean |
| B8 (same session — invalid) | none | Same-chat recall; session `…57ad69` turn 9. **Invalid for fresh-session claim.** | log clean |
| B8 redo (new conversation) | none (text reply) | New session `20261002_151907_67f6a2` turn 1; Brian: “Talia lives in Spokane. On Sunday mornings, you race go-karts at Pinecrest Speedway.” B6/B7 facts still active (`394506ae-…`, `67bf64c0-…`). Prefetch `returned_len=0`. Prior session `…57ad69` got `on_session_end` (message_count=32). | log clean |

Brian observation (verbatim): She replied - Talia lives in Spokane. On Sunday mornings, you race go-karts at Pinecrest Speedway.

Offsets after B8 redo: `zola_memory.log`=9579, `agent.log`=3648860.

### Part C — Checks

| Check | Result |
|---|---|
| After real saves, file_check `no drift` | ✅ post-B6 checks all `drift=0` (B5 had intentional `drift=1` when reduced entry indexed) |
| No `<memory-context>` fence | ✅ none in smoke window; all 9 Part-B/C `prefetch` events `returned_len=0` |
| G6 still holds | ✅ tool-name set still identical to Phase 6 offline baseline; no provider tools / no `<memory-context>`. Offline system prompt differs from Phase 6 baseline due to Part B flat-file memory edits **and** a `conversation-memory` skill she created mid-smoke via `skill_manage` (skills list shift) — not provider injection. Allowlisted line still only `Conversation started:`. |

### Part D — Cleanup

Brian (verbatim): “Zola, forget what I said about the Nimbus Garden project, Pinecrest speedway, sunday go-karts, my sister talia and Spokane.” She said forgotten.

| Check | Result |
|---|---|
| Memory files vs Phase 6 backup | ✅ USER.md 13=13 set-equal; MEMORY.md 1=1 set-equal; no synthetic tokens in live entries |
| No active synthetic facts | ✅ active 14 (user 13 + memory 1); FTS Nimbus/Pinecrest/Talia/Spokane/Rowan/cedar/redwood/oat all 0; all five smoke fact IDs absent |
| Tombstones | ✅ 5 content-free (`1b7c0ffa`, `609306a6`, `b5c542a8`, `394506ae`, `67bf64c0`) |
| Privacy | ✅ `zola_memory.log` / tombstones clean |

Provider erases in cleanup turn: `b5c542a8` / `394506ae` / `67bf64c0` (`reason=remove`). One intermediate Hermes `memory` remove miss (wrong entry text) then successful removes — no hand edits.

### Smoke verdict

**smoke test passed** (Brian accepted). Closeout **HOLD** pending Phase 7b.

## Phase 7b — Read-only skill investigation (no live/skill edits)

### 1. `conversation-memory` skill — path / times / actor

| Field | Value |
|---|---|
| Path | `%LOCALAPPDATA%\hermes\profiles\zola\skills\communication\conversation-memory\SKILL.md` |
| Created | 2026-10-02 15:16:11 PDT |
| Modified | 2026-10-02 15:16:11 PDT (same) |
| Size | 1399 bytes |
| Actor | **Background review fork** (`thread=bg-review:18352`), not the main user turn |
| Ledger | `.curator_ledger.jsonl` id `2f19297eafde` — `actor=curator`, `action=create`, `skill=conversation-memory`, `evidence.session_id=20261002_145734_57ad69`, ts `2026-10-02T22:16:11Z` |

**agent.log citations (session `20261002_145734_57ad69`):**

1. `15:15:51,003` — main B5 turn finished (`tui turn finished` … duration=5.6s).
2. `15:15:51,020` — `OpenAI client created … thread=bg-review:18352`.
3. `15:15:51,046` — review-context turn: `conversation turn: … msg='Review the conversation above and update the skill library. Be ACTIVE — most ses…'` (platform=tui, same session id; budget later shows `4/16` typical of review fork).
4. `15:15:54,149` / `15:15:54,225` — `skills_list` / `skill_view` (no session bracket on these two lines).
5. `15:16:03,791` — `Tool skill_manage returned error` — `create on 'conversation-memory'` failed (description 110 chars > 60-char budget).
6. `15:16:11,423` — `tool skill_manage completed` (create succeeded; matches file mtime).
7. `15:16:14,181–182` — bg-review client closed; `agent.background_review: Background review complete: thread=bg-review … result=skill`.

### 2. Content classification (not copied into repo)

Local scan of `SKILL.md` only — **no skill body quoted here**.

| Synthetic token | Present |
|---|---|
| Nimbus | no |
| Rowan | no |
| oat | no |
| cedar | no |
| redwood | no |
| Pinecrest | no |
| go-kart | no |
| Talia | no |
| Spokane | no |

- Classification: **procedural only** (frontmatter `name` / 59-char `description` about retaining/correcting/forgetting user context; body is instructional).
- Personal-fact statement count (heuristic): **0**.
- No `Brian` / people / project fact assertions found.

### 3. Other skills changed since Phase 6 deploy (~14:57)

Phase 6 backup did not snapshot `skills/`; comparison is filesystem mtime ≥ 14:50 on 2026-10-02 under `%LOCALAPPDATA%\hermes\profiles\zola\skills\`.

| Path | Times | Actor | Classification |
|---|---|---|---|
| `communication/conversation-memory/SKILL.md` | created+modified 15:16:11 | bg-review / curator (above) | procedural only; 0 synthetic tokens; 0 personal facts |
| `.bundled_manifest` | 14:57:32 | serve relaunch (Phase 6) | manifest metadata — not a skill body |
| `.curator_ledger.jsonl` | mtime 15:16:11 | curator append for create | ledger — not a skill body |
| `.usage.json` | mtime 15:22:56 | runtime usage accounting | usage stats — not a skill body |

No other `SKILL.md` files were created or modified after Phase 6 deploy. (Other `communication/*` skills have older mtimes from earlier 2026-10-02 morning / prior days.)

### 4. Hook table update

Recorded above under Hook-firing table: double `on_session_end` at 15:19:27,212 and ,217; `on_session_switch` and orphan-reap `on_session_end` not observed; **Track 5 input — session-end must be idempotent**.

## Phase 4 notes

- Built approved contract in repo only (`hermes-plugins/zola_memory/`; **no** `plugin.yaml`).
- `identity/MEMORY_CONVENTIONS.md`: appended approved “Structured store (P6)” section.
- Modules: `__init__.py` (`register`, `_get_plugin_llm` sole `_plugin_context()` site), `llm_access.py`, `provider.py`, `store.py`, `fact_index.py`, `forget.py`, `log.py`, `tests/`.
- Nothing deployed; live `plugins/zola_memory` absent; live `config.yaml` hash unchanged (`b54acb16…`).
- `hermes-agent` clean at `345cd2b0…`.

## Phase 4b notes (Brian, 2026-10-02)

Repo only; nothing deployed.

1. **Pending retry vs hash skip:** `run_file_check` does not store `files_sha256` when any erase in that run fails; hash-match skip is blocked while `meta.pending_erasures` is non-empty.
2. **Read failure:** existing but unreadable `USER.md`/`MEMORY.md` aborts the whole check (no erases/adds/hash); logs `zola_memory.file_check_read_error`. Missing file still = empty.
3. **Concurrency:** per-connection `threading.RLock` (keyed by `id(conn)`) held for every DB use; provider also has `self._lock`.
4. **Apostrophes:** U+2018/U+2019 normalized to `'` before forget-intent matching.
5. **Remove unmatched:** exact-text erase **plus** full file-check fallback (`remove_unmatched`).

## Unit test summary

Command (repo root):
`C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m unittest discover -s hermes-plugins\zola_memory\tests -t hermes-plugins\zola_memory`

Result (Phase 4b): **Ran 26 tests in ~0.83s — OK**

Also: P6-CALC suite **Ran 44 tests — OK**.

Coverage highlights:
- schema/migration; empty surfaces; no MEMORY/USER write opens
- add / replace+history / remove+tombstone
- forget-intent + exclusions (`Don't forget…` / curly `Don’t forget…` no match; quoted `forget` match; `don't keep` / curly `don’t keep` erase)
- file-check bypass add/remove; whitespace no-op; hash skip; import `learned_at=NULL`
- replace unmatched (lag + ambiguous) → file check + `zola_memory.replace_unmatched`
- remove unmatched → exact erase + file check
- erase failure: no hash advance; pending blocks skip; retry clears fact
- read failure aborts check; next success normal
- concurrent notify + file check: no exceptions, consistent FTS
- erase failure rollback + pending marker + file-check recovery even if marker fails
- FTS5 missing → `is_available() False`
- content scan: tombstones/logs contain no synthetic fact strings

### Production-file scan

Production `.py` under `hermes-plugins/zola_memory/` (excluding `tests/`): USER.md/MEMORY.md referenced **read-only** (`Path.read_text` / `read_memory_file`); no write-mode opens; no network imports. No `plugin.yaml`.

## Phase 8 notes (Closeout)

- **8a:** `zola_memory` **Ran 26 tests — OK**; `zola_tools` **Ran 44 tests — OK**. `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` → **Build succeeded** (0 Warning(s), 0 Error(s)). Exit-criteria table below.
- **8b:** `hermes-agent` porcelain empty at `345cd2b057a452236de401d3534b8502a7465e8d`.
- **8c:** Deployed hashes MATCH repo (all 7 files); `plugin.yaml` absent; live `config.yaml` still `7ba2e676…` (`memory.provider: zola_memory` only approved key).
- **8d–8k:** Commit / push / merge / delete as below.

### Exit criteria verification (PHASE6_BUILD_PLAN.md Track 2)

| Criterion | Status | Evidence |
|---|---|---|
| G1–G9 answered + Brian STOP verdicts | ✅ | Progress G1–G10 table + Phase 2 rulings; G10 omit `plugin.yaml` |
| Unit tests pass | ✅ | 26 OK (+ CALC 44 OK at closeout) |
| Deployed hashes match; `memory.provider` only approved config | ✅ | 8c re-verify; config `7ba2e676…` |
| Hook proof AUD-36 (`initialize` / `on_turn_start` / `sync_turn` / memory-write path; session-end observed) | ✅ / ⚠️ | Live log: initialize, on_turn_start, sync_turn, fact_add/replace/erase (on_memory_write path). `on_session_end` observed (double-fire) on new conversation; orphan ~20s reap **not** observed (⚠️ noted, not relied on) |
| Blind smoke: save / correct+history / forget+tombstone / don't-keep escalate | ✅ | B1–B5 table |
| Bypass via unit tests; live no hand edits; file_check no drift after saves | ✅ | Phase 4b tests; post-B6 `drift=0` |
| Regression: 2/2 unprompted saves + fresh-session recall; G6 tools/prompt | ✅ | B6–B8 redo; G6 tools identical; no provider prompt/tools; Part C prompt diffs = memory+skill content only |
| Prefetch empty (no `<memory-context>`) | ✅ | All smoke `prefetch returned_len=0`; no fence |
| Synthetic cleanup; backup restore; tombstones | ✅ | Part D: files set-equal backup; 5 tombstones; FTS synth 0 |
| `hermes-agent` clean; no client source changes | ✅ | pin clean; dotnet build only |

All Track 2 exit criteria: **YES** (orphan-reap session_end ⚠️ observed-not-relied-on gap only).

### Closeout SHAs

*(filled after 8f / 8i)*
