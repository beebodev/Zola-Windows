# Zola P9PRE Audit 06 — Open Loops, Queue, Lifecycle, Retention

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Labels vs:** `S14`, `S71`, `P6-D01`, `P6-D02`, `P6-D06`, `P8-D08`, `P8-D09`, `P8-D10`, `S54`

No open-loop table exists. `S71` is unmet in code. The rows below are what the current store can and cannot do.

---

## 1. Store options

**(a) `zola_memory` store.** `open_store` (`store.py` L83–91) opens SQLite with `check_same_thread=False`, `foreign_keys=ON`, `journal_mode=WAL`, `secure_delete=ON`. No `busy_timeout` in that function. `SCHEMA_VERSION = 2` (L25). `migrate` refuses a newer version (L162–164) and applies versioned steps (v1 L171, v2 L191). Tables: `meta`, `facts`, `fact_history`, `entities`, `entity_aliases`, `tombstones`, `episodes`, `episode_entities`, `episode_fact_refs`, `pending_turns` (L152–281). The provider holds one connection per session (`provider.py` initialize). A second thread in the same process can use that connection under `store.locked` (an `RLock` per connection, L94–96). A second **process** is a second connection to the same file. WAL allows concurrent readers and one writer; the lock behavior is probe H-4. Forget (`P6-D06`) walks this file. Backup is the file plus its `-wal`/`-shm`. Erasure uses secure-delete and WAL truncate (`store.py` L335+).

**(b) A `zola_workspace` store.** The plugin already has `taint.sqlite` beside the token store (Phase 1: size 12288, mtime recorded, contents not read). A new file there would be one Workspace authority's state (`P8-D01`). `forget_memory` does not open it. Cross-plugin reads would be a second opener. DPAPI is used for the token file, not for `taint.sqlite` (taint is a plain SQLite file; confirm by path only — contents not read).

**(c) Elsewhere.** A file under the profile that neither plugin owns has no forget path and no single module authority.

**P9PRE-AUD-31 [GAP] HIGH** — no durable open-loop or watcher-queue table. `S71`.  
**P9PRE-AUD-32 [RISK] MEDIUM** — putting personal text in the memory store makes it subject to `P6-D02` (facts belong to entities) and to forget; putting it only in a workspace file leaves `forget_memory` blind. `P6-D06`.

---

## 2. Forget

`forget.py` deletes matching rows from `fact_history`, `facts`, `facts_fts`, `episodes`, `episodes_fts`, `episode_entities`, `episode_fact_refs`, `pending_turns`, `entities`, `entity_aliases`, `entities_fts` (L550–660). It does not delete a table that does not exist. `USER.md` / `MEMORY.md` are removed by the memory tool's remove action; the comment at L85 and L1132 says the cascade runs from that notification. A queue living only in `zola_workspace` is not in this list.

---

## 3. Entities

`entities` and `entity_aliases` exist. `P6-D02` says facts belong to entities and are derived at read time. A loop can store an entity id that already exists. Inserting a new entity from an email address would be a new fact-like write, which consolidation's rules do not currently perform from Gmail (no such code). Linking without creating a fact is possible only if the entity row already exists and the loop stores the id.

---

## 4. Creation from Brian's words

`turn_context.is_brian_turn` (`turn_context.py` L99–115) is the check a tool handler can call. It is false when the record is missing, the turn id mismatches, the platform is not `tui`, or a parent session is set. Email text is not a turn record. The memory-save guard's lead-in list (`guards.py` L414–439) is a second pattern: only a short allow-list of words may precede the save phrase. A loop-create tool can require `is_brian_turn` the same way `read_common.authorize` does. Content inside the tool arguments is still model-supplied; the turn record says the turn is Brian's, not that every argument was spoken by him. `P8-D09` is the precedent for refusing memory writes that the model derived from tainted content unless Brian's own leading phrase is present.

**P9PRE-AUD-33 [MATCH]** — `is_brian_turn` is reusable for "this turn is Brian's." It does not prove a particular argument was his words. `P8-D09`.

---

## 5. Time

`time_context.capture_now` (L76) and `get_active_timezone` (L85) do not require a turn. `pre_llm_call_hook` (L241–267) injects a stamp only when `is_user_turn(platform, parent)` is true. Background code can call `capture_now` directly. It cannot see the injection hook's stamp unless it is on a user turn.

---

## 6. Injection without a tool round (LEAD-7)

| Mechanism | Contract in this tree |
|-----------|------------------------|
| `prefetch` | `provider.prefetch` (L175–191) returns episode text per query, per call. The host appends it with `pre_llm_call` context onto the API copy of the user message (`agent/turn_context.py` `compose_user_api_content` L81–94). Not the system prompt. |
| `system_prompt_block` | `provider.system_prompt_block` returns `""` (L157–158). The host would place a non-empty return in the system prompt (`system_prompt.py` memory parts). |
| `pre_llm_call` return | Host collects `context` strings (`agent/turn_context.py` L663–714) and appends them to the user message's API copy, not the system prompt. Oversized pieces spill to disk. `zola_memory`'s time hook returns context only for a user turn. `zola_workspace`'s `pre_llm_call_hook` records the turn and re-taints; it does not return mailbox text. |

`_stamp_api_content_sidecar` (`turn_context.py` L793–831) writes that composed string onto the message as `api_content` and calls `set_message_api_content` when a row id exists. The docstring says the injection lives in the API copy and is stamped for replay. The visible transcript content stays the user text. Later turns send the sidecar again.

**P9PRE-AUD-42 [RISK] HIGH** — injected text is stored for replay in `api_content`. Workspace text that enters this way is kept in the session DB and resent on later turns. Combined with AUD-23, that copy is not tainted unless the injector calls `mark_tainted`. `P8-D09`, `P8-D11`.

`zola_memory` already owns memory injection (prefetch + time context). A second plugin can also return `context` from `pre_llm_call`. The host concatenates every hook's context (`L698–714`). Two owners would both inject.

**LEAD-7: CONFIRMED as a fact about the host.** More than one hook can return `context`. Memory injection today has one owner (`zola_memory`). Workspace injection of mail does not exist.

**P9PRE-AUD-34 [RISK] MEDIUM** — the host will inject every `pre_llm_call` `context`. A second owner duplicates the channel Phase 5 said should have one. `S14`.

---

## 7. Taint on injection

See audit 04, AUD-23. `mark_tainted` is on the tool return path. The injector can call it before returning `context`, because `pre_llm_call` runs before the model request (`agent/turn_context.py` L674, then the model call is later). Today the workspace hook does not taint a clean session merely because some other hook added text.

---

## 8. Repeats

`send_gate.py` keeps reviewed drafts in process dicts (`_pending`, `_auths`). They die with the process (audit 01). `pending_turns` rows are durable until consolidation or forget. There is no "already told" table.

---

## 9. "What's pending" by voice

`P8-D08` is one coarse tool call that answers a read question. A new tool would be another model round. `S54` records about 8–12 seconds for a tool round by voice. Injection (section 6) is the path that does not add that round. The tool still exists as the path that answers an explicit question from stored rows.

---

## 10. Processing lifecycle (facts, not a design)

No item type exists. The states the phase named, and the closest existing pattern:

| State | Closest pattern | Crash before the write | Crash after the write |
|-------|-----------------|------------------------|------------------------|
| detected | none | item never stored | — |
| stored | `pending_turns.write_pending` (`pending.py` L153) inside the provider lock | lost | row remains |
| ranked or unranked | consolidation commit only after validation (`consolidate.py` L527–528) | source rows remain, `ok=false` | episodes committed |
| eligible | none | — | — |
| delivery claimed | `send_gate` single-use auth is in memory | claim lost; draft not sent | process death drops the auth (fail closed for send) |
| speech started | client `TtsPlaybackMonitor` is client-side | server does not know | `S70`: no playback-completion signal back to serve |
| speech completed / acknowledged | none | `S70` | — |
| closed or expired | forget deletes rows it knows; no expiry table | — | — |

The ambiguous case is speech started and then a crash. `S70` says Zola has no signal that playback finished. A "told" bit written at start can be wrong if he did not hear it. A "told" bit written only at completion can never be set with today's signal.

---

## 11. Cursor and queue atomicity

`historyId` and `syncToken` are not stored (audit 03, AUD-10, AUD-11). Idempotency keys Google documents: Gmail message `id` and `threadId` (`messages.get`); Calendar event `id` plus `updated` on the event resource (audit 03 `[EXT]`). Message ids are stable for that message. A resync (404/410) returns a full window, so the same ids can appear again.

Two commit shapes, as facts:

- Same transaction: possible only if the cursor and the items share one SQLite connection and one `commit`. `zola_memory.open_store` is one connection. A cursor in another file cannot share that transaction.
- Store items first, then advance the cursor: a crash between them replays the items. Dedup requires a unique key on message id or event id + `updated`. A crash before the item insert loses those changes until the next poll still holding the old cursor. Advancing the cursor first loses items that were not stored.

Delivered twice: possible after replay if "told" is not keyed by the same id. Not possible to demonstrate today; the tables are absent.

H-4 reports the lock behavior of two writers on a scratch copy of this schema.

---

## 12. Retention minimums

What each layer needs if it exists. Not a decision to keep it.

| Data class | Minimum the layer needs | Lifetime pressure already in code | Encryption | Deletion today |
|------------|-------------------------|-----------------------------------|------------|----------------|
| Cursors (`historyId`, `syncToken`) | the token string and which mailbox or calendar | Google: history id often ≥1 week, can be hours; sync token until 410 | none unless the file is DPAPI or the volume is BitLocker | none stored |
| Candidate metadata | id, thread or event id, time, label ids; subject/snippet only if ranking or speech needs them | `P8-D08` caps apply to tool reads, not to a store | plain SQLite like the memory store | forget does not see a new table |
| Calendar fields | title, start, attendees; descriptions stay off (`gcal.py` L65, `P8-D10`) | same | same | same |
| Ranking output | a label or clamped score; a stored reason can repeat email text | consolidation stores episodes, which are derived text | memory store, not DPAPI | forget deletes episodes |
| Open loops | source, subject, close condition, expiry (`S71`) | no expiry job | same question as the chosen file | forget only if the rows live in tables section 2 walks |
| Delivery history | ids and timestamps are enough to suppress repeats | none | same | none |
| Logs | `P8-D11`: route, counts, error class | `zola_memory.log` already keeps counts and ms | filesystem | no rotation fact read this pass |
| Forgotten entities | cascade is section 2 | a queue outside those tables survives forget | — | gap (AUD-32) |

**P9PRE-AUD-35 [GAP] MEDIUM** — forget's delete list is a fixed set of tables. A new personal-text table is invisible to `P6-D06` until that list includes it.
