# P9-STORE Progress — Proactive store and open loops

## Branch

- Work branch: `p9-store` (created from `main`; not pushed)
- Base `main` = `origin/main`: `9b754f79a1dadf38bf0481ec68c1952c3fdab2cb` (fetched before the check; porcelain empty)
- `p9-store` HEAD: `9b754f79a1dadf38bf0481ec68c1952c3fdab2cb`
- Hermes (read-only): detached `HEAD` at `345cd2b057a452236de401d3534b8502a7465e8d` (`chore(release): v0.21.3 (v2026.9.14)`; porcelain empty)
- Prompt file: `C:\Users\test\Dev\zola-spikes\prompts\P9-STORE_Prompt_v1.1.md`
  SHA-256 `F25B149F51A69E4103F7F6362F0149150521DD19D84466F769ED1A6E2A08A53E` (24,484 bytes)
- This Phase 1 message contained the prompt body and no separate comparison digest. The SHA above is the canonical file, hashed 2026-10-13.
- Scratch: `C:\Users\test\Dev\zola-spikes\p9-store\` (harness scripts only; never committed; delete at closeout)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and setup | COMPLETE |
| 2 | Grounding (read-only + scratch harness) | COMPLETE |
| 3 | Proposal | LOCKED — verdicts recorded in Phase 4 |
| 4 | Implement | IMPLEMENTED — stopped for review; not committed |
| 5 | Review checkpoint | FIXES APPLIED — stopped for the next phase |
| 6 | Deploy and smoke | COMPLETE — Release serve restarted; schema version 2 |
| 7 | Closeout | COMPLETE |

## Guardrails (summary)

- G-SCOPE: `hermes-plugins/zola_workspace/` (new store, loops, tool, tests), the forget-cascade call in `hermes-plugins/zola_memory/`, `.gitignore` for the store file, this progress doc, the live plugin mirror. No watcher, ranking, surfacing, speech, or Google calls from new code.
- G-ARCH: the build plan and Appendix A are truth. A contradiction or a new decision point stops for Brian.
- G-PATTERN: read every file in full before changing it.
- G-NOCHANGE: no Hermes edits; no client changes unless Phase 3 approves; no `SOUL.md`, identity, lore, or build-plan edits; no installs. Standard library only (`sqlite3`).
- G-ONE-OWNER: every write to `proactive.db` goes through `proactive_store` transition functions. A source-scan test enforces this.
- G-TRANSITIONS: each allowed transition is one function, one transaction, with a guarded `WHERE`. An illegal transition changes nothing and returns a refusal.
- G-NO-AUTHORITY: nothing stored in `proactive.db` grants Brian-only authority. Loop create and close require `is_brian_turn()` at call time.
- G-PROVENANCE: loop predicates use ids from tool results this plugin recorded, bound to an opaque handle, session, and turn. An ambiguous reference asks before a loop is created. In a tainted session, free-text arguments are untrusted.
- G-FORGET-HONEST: the cascade removes by entity id, address, and source id first. A text sweep is extra. An unmapped subject is said so. Never claim a deletion that was not done.
- G-FORGET-ATOMICITY: memory and `proactive.db` cannot share one transaction. A failure after one side commits is a partial reply plus a durable idempotent retry. The pending record is deleted only on success.
- G-STATE-INDEPENDENCE: a failed or uncertain delivery does not erase ranking or conversation history. A retention purge does not change delivery or claim state or invalidate an active attempt.
- G-PRIVACY: `proactive.db` is git-ignored and lives outside the repo. No subject, snippet, gist, body, address, or name in logs, tests, commits, or this doc.
- G-COMMENT: `# P9-STORE: <why> — P9-D0X`. Named constants for every limit.
- G-STOP / G-CLOSEOUT / G-LORE-SCOPE / G-LIVE: stop after every phase. Closeout only on "proceed to closeout". No lore edits. Live steps one at a time.

## ST-G1–G8

Answered 2026-10-13. Read-only. No repo source file was modified. The harness lives only under `C:\Users\test\Dev\zola-spikes\p9-store\`.

Recommendations below are not locked. Phase 3 turns them into a proposal and stops for Brian. Two of them are the decision points the prompt names: where `proactive.db` lives, and the loop-expiry default.

### ST-G1 — Schema

**Recommendation: orthogonal dimensions, not one `state` column.** `content_expired` is a content flag, not a replacement for delivery or conversation.

P9-D06 (`PHASE9_BUILD_PLAN.md` 805–814) writes the lifecycle as one chain: detected, ranked or unranked, eligible, claimed, speech started, delivered, acknowledged, closed or expired. P9-D07 (816–819) also calls `content_expired` a state. P9-D10 (841–849) says selected, surfaced, and acknowledged are different facts. P9-D11 (851–862) says eligibility and permission are different facts, and a blocked speech attempt stays eligible. G-STATE-INDEPENDENCE says a purge must not change delivery, claim, or the active attempt.

A single column cannot hold those at once. Ranking nulls the body immediately (P9-D07) while the item is still eligible to speak later. An uncertain delivery can outlive the content. A conversation selection is not a speech claim.

| Dimension | Column | Values |
|---|---|---|
| Processing | `processing` | `unranked`, `ranked`, `rank_failed` |
| Eligibility | `eligibility` | `pending`, `eligible`, `suppressed`, `expired` |
| Conversation | `conversation` | `none`, `selected`, `possibly_surfaced`, `acknowledged` |
| Delivery | `delivery` | `none`, `claimed`, `speech_started`, `delivery_uncertain`, `delivered` |
| Content | `content_state` | `available`, `content_expired`, `forgotten` |
| Closure | `closed_at` | null, or the time it closed |

`item_attempts` holds the lease and the attempt id for ranking and for speech. `deliveries` holds the 30-day history. Loops have their own `status` (`open`, `closed`, `expired`) and are not item states.

Four conditions the single column would collapse, and that the columns above keep:

1. Ranked, selected for the next conversation, and still eligible to speak (`processing=ranked`, `conversation=selected`, `eligibility=eligible`, `delivery=none`).
2. Speech outcome unknown, and the body and gist already gone (`delivery=delivery_uncertain`, `content_state=content_expired`, attempt id unchanged).
3. Body already nulled at ranking, then speech starts (`processing=ranked`, `content_state=content_expired` for the body, `delivery=speech_started`).
4. Brian has acknowledged it in conversation while a late speech completion for an older attempt must still be ignored (`conversation=acknowledged`, `delivery=delivered` or `delivery_uncertain`, old attempt id refused).

**Tables.** `meta` (schema version). `items`. `item_attempts`. `loops`. `deliveries`. `cursors` and `watcher_health` are created here and unused until Track 3. A `pending_forget` table is not in this file; see ST-G5.

`items` columns: `id`, `source` (`gmail` or `calendar`), `message_id`, `thread_id`, `event_id`, `event_updated`, `idempotency_key`, `sender_address`, `sender_address_hash`, `entity_id`, `entity_resolution` (`memory_entity`, `contacts_handle`, `unresolved`), `label` (null until ranked; then `urgent`, `important`, `normal`, `ignore`), the five dimension columns, `closed_at`, timestamps (`detected_at`, `ranked_at`, `eligible_at`, and `updated_at`), and separate content columns `subject`, `snippet`, `body`, `gist` so retention can null them one group at a time.

Idempotency, from P9-D06 and audit 06 section 11: Gmail message id; Calendar event id plus `updated`. Unique indexes. Items are committed before a cursor advances. That writer is Track 3; the unique key is created now.

**Allowed transitions.** Each is one function and one `BEGIN IMMEDIATE` transaction. The `WHERE` includes the current dimension value and, where a lease exists, the attempt id. Zero rows changed means a refusal dict, not an exception.

| Function | From | To | Who |
|---|---|---|---|
| `insert_item` | absent | `unranked` / `pending` / `none` / `none` / `available` | watcher (Track 3) |
| `claim_rank` | `processing=unranked` and rank lease free | same, plus an `item_attempts` row | ranker |
| `complete_rank` | that attempt | `processing=ranked`, label set, body nulled | ranker |
| `fail_rank` | that attempt | `processing=unranked` (retry) or `rank_failed` after the cap | ranker |
| `release_rank_lease` | rank lease expired | attempt released, processing unchanged | ranker or purge |
| `mark_eligible` | `eligibility=pending` and `processing=ranked` | `eligible` | plugin code (Track 5) |
| `suppress` | `pending` or `eligible` | `suppressed` | plugin code |
| `expire_eligibility` | `pending` or `eligible` | `expired` | purge |
| `select_for_conversation` | `conversation=none` | `selected` | plugin (Track 5) |
| `mark_possibly_surfaced` | `selected` | `possibly_surfaced` | plugin (Track 5) |
| `acknowledge` | `selected` or `possibly_surfaced` | `acknowledged` | plugin, ticket turn only |
| `claim_speech` | `eligibility=eligible` and `delivery=none` | `delivery=claimed`, new attempt id | client entry point (Track 6) |
| `mark_speech_started` | `claimed` and matching attempt | `speech_started` | client entry point |
| `mark_delivered` | `speech_started` and matching attempt | `delivered`, plus a `deliveries` row | client entry point |
| `mark_delivery_uncertain` | `speech_started` and matching attempt | `delivery_uncertain` | client entry point |
| `release_speech_lease` | `claimed` and lease expired | `delivery=none`, attempt released | client entry point or purge |
| `close_item` | any delivery except an open speech attempt | `closed_at` set | plugin, ticket turn |
| `purge_retention` | any | content columns nulled only; dimensions and attempt id unchanged | serve and, later, the watcher |
| `forget_subject` | any | loops removed; item content redacted or the row removed | `forget_memory`, ticket turn |

Illegal, and a refusal that writes nothing: `delivery_uncertain` back to `none` or `claimed`; `complete_rank` or `mark_delivered` setting the other dimension; any completion whose attempt id does not match; a purge that updates `delivery`, `conversation`, `eligibility`, or `attempt_id`. Ranking never writes `delivered` (P9-D06).

### ST-G2 — Leases and attempt ids

Precedent: consolidation takes one lease in `BEGIN IMMEDIATE` and stores owner plus expiry in `meta` (`consolidate.py` 30, `CONSOLIDATE_LEASE_TTL_S = 60`; acquire at 1085–1107). Proactive claims are per row, not one global owner, because the ranker and the client claim different work.

`claim_rank` and `claim_speech` are each one `UPDATE … WHERE <dimension predicate> AND (attempt lease is null or expired)` inside `BEGIN IMMEDIATE`. `changes()` is 1 only for the winner. The function inserts the `item_attempts` row in that same transaction and returns the new attempt id. A loser gets a refusal and the row is unchanged.

Completion (`complete_rank`, `mark_speech_started`, `mark_delivered`, `mark_delivery_uncertain`) requires that attempt id in the `WHERE`. A late completion for an older id matches zero rows and returns a refusal.

Recovery, from P9-D06 (810–812):

- Rank lease expired: release the attempt, leave `processing=unranked`, allow another claim.
- Speech `claimed` and the lease expires before `speech_started`: release back to `delivery=none`. It may be claimed again.
- `speech_started` and the outcome is unknown when that lease expires: `mark_delivery_uncertain`. Never back to claimable. Track 5 carries it in conversation instead of speaking it again.

Proposed constants, for Phase 3, not locked:

| Name | Value | Why |
|---|---|---|
| `RANK_LEASE_SECONDS` | 120 | one tool-less model call; consolidation uses 60 for a shorter call |
| `SPEECH_CLAIM_LEASE_SECONDS` | 30 | claim until speech starts |
| `SPEECH_OUTCOME_LEASE_SECONDS` | 120 | after start, unknown completion becomes uncertain rather than reusable |

### ST-G3 — Location and cross-process access

**Where.** `get_hermes_home()` is how `taint.py` finds the profile (43–46). The client sets `HERMES_HOME` to that profile (`HermesProcessManager.cs` 37–41 and 242): `%LOCALAPPDATA%\hermes\profiles\zola`. Memory's file is `<hermes_home>\zola_memory\zola_memory.db` (`store.py` 26–27, 51–52). Taint's file is `<hermes_home>\zola_workspace\taint.sqlite` (`taint.py` 12–13), beside the token. That folder is outside `plugins\`, but it is the wrong neighbor for mail text.

Proposed path, for Phase 3: `<hermes_home>\proactive\proactive.db`. Outside the repo, outside `plugins\`, and not in the token directory. Serve, the ranker, and the watcher all see `HERMES_HOME`. The watcher does not exist yet; Track 3 will use the same helper.

**Connection.** Match the measured memory store, and set the timeout on purpose. `open_store` (`store.py` 83–91) uses `check_same_thread=False`, `foreign_keys=ON`, `journal_mode=WAL`, `secure_delete=ON`, and does not pass `timeout`. H-4 measured the default busy timeout at 5000 ms (`Zola_P9PRE_Audit_08_Probes.md` 46–64). A held `BEGIN IMMEDIATE` then raises `database is locked` once the other connection's timeout expires. The checkpoint helper drops `busy_timeout` to 50 ms only around `wal_checkpoint(TRUNCATE)` (`store.py` 416–417). Taint sets `timeout=5.0` explicitly (`taint.py` 63).

Proposed for this file: `timeout=5.0`, `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=5000`, `PRAGMA synchronous=NORMAL`, `PRAGMA foreign_keys=ON`. `secure_delete=ON` as well, because forget removes personal text (P6-D10). `NORMAL` is SQLite's value 1. The harness measured that combination: `journal_mode=wal`, `busy_timeout_ms=5000`, `synchronous=1`.

**Who writes.** Watcher (its own process, Track 3), ranker (inside serve, Track 4), `zola_loops` and the forget call (inside serve, this track), retention (serve now, watcher also in Track 3). Every write is a function in `proactive_store`. No other module executes `INSERT` / `UPDATE` / `DELETE`.

**Client, Track 6.** Recommend **(b) a small entry point**, not **(a) .NET issuing SQL**. G-ONE-OWNER forbids a second writer. The client needs claims only while it can speak, and speech already depends on a running backend (P9-D02 fails voice closed when serve is down). The entry point is a localhost listener in the watcher process, because that process already has the store and is supervised separately from the agent loop. It calls the same Python functions. This track does not build it. It documents the function names, arguments, and refusal shapes in the table above so Track 6 can test them from both sides. HUD reads go through that entry point too, so health does not grow a second query dialect. The risk in the build plan (Track 2, primary risk) is drift between Python and .NET; (b) avoids a copied statement list.

### ST-G4 — Retention

P9-D07 (816–819) is the rule. Proposed constants that restate it, plus one interval that is not locked:

| Name | Value |
|---|---|
| `BODY_MAX_AGE_DAYS` | 7 |
| `TEXT_MAX_AGE_DAYS` | 7 |
| `DELIVERY_KEEP_DAYS` | 30 |
| `PURGE_INTERVAL_SECONDS` | 3600 |

There is no serve start/stop hook (build-plan grounding, AUD-19). `register` runs once per process. This track starts a daemon thread from `zola_workspace.register`, the same shape as consolidation's quiet timer, and also runs one purge at that start. The watcher calls the same function in Track 3. Two callers are safe because the purge is idempotent and its `UPDATE`s null a column only when it is still non-null.

What one pass does:

- Body becomes null when the item is ranked, inside `complete_rank`, not later. If it is still unranked at 7 days, the purge nulls the body and sets `content_state=content_expired`. The row stays.
- Subject, snippet, and gist become null when `delivery=delivered` or when `detected_at` is 7 days old, whichever is first. The label stays.
- `deliveries` rows older than 30 days are deleted. They hold ids and times only.
- Loops past `expires_at` move to `expired`. A lapse is told once (ST-G6); the purge does not delete the loop row on that pass.
- Cursors have no content columns to null.

On an item that is `claimed`, `speech_started`, or `delivery_uncertain`: the purge may null body, subject, snippet, and gist when the age rules say so, and may set `content_state=content_expired`. It does not change `delivery`, `conversation`, `eligibility`, `processing`, or the active attempt id.

### ST-G5 — Forget cascade

**How a subject becomes an entity today.** `fact_index.py` does not resolve entities. `_upsert_entity` (`consolidate.py` 1034–1079) finds one row by `lower(name)` or `lower(alias)` and otherwise inserts a new id. `_entity_name_hits` (`retrieve.py` 207–223) matches a name or alias on word boundaries and returns episode ids. `search_candidates` (`forget.py` 1010–1063) does not look at entities; it matches fact, episode, and pending text. `group_candidates` (1066–1093) sets `ask_brian` when more than one label group comes back. Confirm then erases only ids from that candidate set (`handle_forget_memory` 1216–1261). The cascade deletes a fixed table list (`forget.py` 641–768): facts, fact history, fact FTS, episodes, episode links, pending turns, and orphan entities. Audit 06 records the gap: AUD-31 (line 19), AUD-32 (line 20), AUD-35 (line 137). P6-D02 says entities organize only (`DESIGN_DECISIONS.md` 897–898). A proactive row may store an entity id that already exists. This track does not create entities from mail.

**Ticket.** `handle_forget_memory` already refuses a non-conversation (1120–1128) and a turn with no client-origin ticket (1129–1138, `origin_allows` at 320–348). The proactive call sits after that gate, on `confirm=true` only, and the store function checks the ticket again. `forget.py` finds the ticket module by `ORIGIN_MODULE_MARKER == "p9-fix-arm"` (273–283, marker at `origin.py` 15). The same scan finds `proactive_store` by a new marker `p9-store`. If the module is absent, that is the "proactive missing" failure below, not a silent skip.

**Resolution before any delete.**

- More than one memory entity matches the subject: delete nothing in either database. The existing ask-which reply stands (`MSG_ASK_BRIAN_MULTI`, `forget.py` 72–76).
- No entity matches: delete nothing in `proactive.db`. Reply: "I couldn't link that to one person, so I did not change your pending list." A text sweep is not used as the only method (R1).
- Exactly one entity: collect its id, the hashes of its known aliases that are addresses, and source ids already stored on proactive rows for that entity. Then run the cross-database sequence below.

**What is removed.** Loops for that entity, address hash, or source id are deleted. Item rows with no open speech attempt are deleted. An item that is `claimed`, `speech_started`, or `delivery_uncertain` is redacted in place: content columns and sender address null, `content_state=forgotten`, entity id cleared, attempt id and `delivery` left so the in-flight attempt can still complete. A text sweep of subject, snippet, and gist for that entity's names is extra, after the id and address pass, and only when the entity matched.

**Order and the pending record.** The two files cannot share a transaction. Pending-forget lives in the memory database, in `meta`, beside `pending_erasures` (`store.py` 31). It is written inside the same `BEGIN IMMEDIATE` as the memory cascade, so a memory rollback leaves no pending row and does not touch `proactive.db`.

1. Memory transaction: cascade plus insert of the pending record. Commit.
2. Call `proactive_store.forget_subject(...)`.
3. On success, delete the pending record.
4. On locked, missing, or error, leave the record and do not claim success.

The record holds the entity id, address hashes, and source ids. No name and no subject, snippet, or body. Retries are idempotent: deleting an absent row is success, and redacting an already-redacted row changes nothing. The record is deleted only after a successful proactive pass.

Retry runs at the next `proactive_store` open, at each retention pass, and at the start of the next ticket turn that already has the memory connection. A crash after step 1 and before step 3 leaves the record; the next open finishes it. A crash after step 2 and before step 3 runs a no-op delete and then clears the record.

`proactive ok + memory error` does not arise on this order, because proactive is not called until memory commits. If memory rolls back, proactive is untouched and the reply is the existing erase failure, with no claim about the pending list.

**Replies.**

- Both sides succeeded: the existing erase sentence, plus that the pending list was included. Only in this case.
- Memory succeeded, proactive did not: "I forgot it in memory, but I could not finish the pending list. I will retry. It is not fully forgotten yet."
- Unmapped subject: the sentence in the resolution list. No delete.

### ST-G6 — Loop predicates

P9-D09 (832–839). Compile and evaluate are pure. Evaluate returns matched or not. It does not close the loop. Close happens when Brian confirms (`zola_loops` close on a ticket turn), when the predicate itself is a terminal calendar fact (`cancelled` or the stated status), or at `expires_at`.

Grammar, each node an operator the compiler emits. The model never supplies this JSON.

- `all` / `any` of nodes
- `gmail_thread` — thread id from a recorded handle
- `gmail_message` — message id from a recorded handle
- `sender_is` — address hash from a recorded Gmail handle or a recorded Contacts handle
- `not_from` — address hashes known to be Brian's, only when a recorded result in this session has them
- `after` — unix time, set by the compiler to the loop's creation time unless Brian's words named a later bound
- `calendar_event` — event id from a recorded calendar handle
- `calendar_updated_after` — that event's recorded `updated` value
- `calendar_cancelled`
- `calendar_status` — the status Brian stated, compared with the item's status
- `brian_confirms` — evaluate always returns not matched; only the close tool ends it

**"Tell me when they reply."** Compiler input is the one live Gmail handle. Emitted predicate: `all` of `gmail_thread` for that handle's thread, `sender_is` the other party's address hash, and `after` the creation time. The other party is the recorded `from_address` when that message is not a sent message. An incoming item on that thread from that address, after creation, matches. Brian's own later message on that thread has a different from-address, so it does not match. If the only recorded message is one he sent, the recipient is not in the search payload (`shape_metadata`, `gmail.py` 171–185, has no To). This track does not call Google to look it up (G-SCOPE). Compile refuses and asks for a received message or a Contacts handle for the other party. There is no stored account address in the plugin (`auth.py` has the email scope at 38–40 and does not keep the address on the token record).

Allowed compiles:

- One live Gmail handle, intent reply → the predicate above.
- One live calendar handle, intent cancelled → `all` of `calendar_event` and `calendar_cancelled`.
- One live Contacts handle plus a thread handle, intent "when this person writes on that thread" → `all` of `gmail_thread` and `sender_is` that contact's address hash.
- Words that name no checkable fact ("when it feels resolved") → stored as `brian_confirms`, not refused, because P9-D09 allows that.

Refused compiles:

- A message id, thread id, event id, or address typed in the tool arguments.
- Zero live handles, or a handle from another session, or an expired handle.
- Several live handles and no single one identified (ST-G7).
- "Not from Brian" when this session has no recorded address for him.

**Expiry and lapse.** Proposed, not locked: `LOOP_DEFAULT_EXPIRY_DAYS = 14`. Brian can name a shorter bound at creation; the compiler caps it at `LOOP_MAX_EXPIRY_DAYS = 90`. When `expires_at` passes, `status` becomes `expired` and `lapse_told` is still 0. Track 5 may surface that lapse once, then sets `lapse_told=1`. The purge will not surface it again.

### ST-G7 — Recorded results and the tool

Nothing records returned ids today. Search returns Gmail `id` and `thread_id` to the model (`gmail.py` 171–185, payload at 307–324). Read removes `id` before the payload (366) and does not copy `thread_id` (the key list at 374–385). Calendar shaping has no event id and no `updated` (`gcal.py` 236–255); `_strip_internal` (366–367) drops `_start_dt` only, and the model sees `items` (696–704). Contacts returns display name, emails, and phones (`contacts.py` 59–72) with no person id. Draft fields do include `thread_id` (`gmail.py` 632–641). `mark_then_frame` (`read_common.py` 190–226) is the success path for the read tools; refusals go through `refuse` (80–96) and must not be recorded.

**Registry.** Process memory in a new `zola_workspace` module. On each successful search, read, calendar query, contacts lookup, and draft or send result, the handler records what it actually fetched, including ids stripped before the model sees them. Each row gets an opaque handle (random, not a hash of the id). The row stores the handle, the session id, the turn id, the tool name, the kind (`gmail_message`, `calendar_event`, `contact`), the ids and address hashes, and `created_at`. Cap `RECORDED_RESULTS_CAP = 64` per session, dropping the oldest. Lifetime `HANDLE_TTL_SECONDS = 1800`, and `send_gate.on_session_end_hook` (`send_gate.py` 774) clears the session. The registry proves the id was in a tool result. It does not prove Brian meant that row.

The model-visible payload gains the handle and does not need to gain the raw id. Search already shows raw ids; the loop tool still ignores any id the model types.

**Resolve.** "That email" with exactly one live `gmail_message` handle in this session uses that handle. Several live handles: the tool returns `refused_reason=ambiguous` and a count, no loop is written, and Zola asks which one. None, expired, or another session: `refused_reason=unknown_handle`. A Contacts address is accepted only as a `contact` handle. A model-typed id or address is `refused_reason=untrusted_argument` even when the characters match a real result.

In a tainted session, free-text arguments are untrusted (P8-D09, `DESIGN_DECISIONS.md` 1489–1497). The compiler uses handles and Brian's intent enum only.

**Tool.** Registered in `register` (`__init__.py` 125–159) on toolset `zola_workspace`, `is_async=False`, same as the other tools. Handler calls `turn_context.is_brian_turn` (112–139) at execution time. No ticket: `ok: false`, `refused_reason: origin`, and the forget-style sentence that the turn was not sent from Brian's app. No row is written.

Schema the model sees:

- `action`: `create`, `list`, or `close`
- `handle`: string, optional, the opaque handle
- `intent`: `reply`, `cancelled`, `status_change`, or `confirm_close`
- `loop_id`: string, only for `close`, and only an id `list` returned earlier in this session

No `message_id`, `thread_id`, `event_id`, or address property.

`create` compiles, inserts one open loop, and returns the loop id and the operator names (not the raw ids). `list` returns open loops: id, intent, expiry, matched flag. `close` requires a ticket and a loop id from the latest list. "Zola offers, Brian confirms" is not a flag in the tool: the offer is her reply, and the row appears only if the next ticket turn calls `create`. A later turn that does not call `create` leaves no row.

**config.yaml.** No new line. Tools on toolset `zola_workspace` are already on `platform_toolsets.cli` (live `config.yaml` 100–118, which includes `zola_workspace` and does not include `code_execution`). `plugins.enabled` already lists `zola_workspace` (11–14). `known_plugin_toolsets.cron` lists `zola_workspace` (121–123), and there is no `platform_toolsets.cron`, so cron does not receive the toolset. A no-ticket call is refused even if some other path invoked the handler.

### ST-G8 — Two-process harness

Scratch only: `C:\Users\test\Dev\zola-spikes\p9-store\st_g8_harness.py` and `run_st_g8.py`. Database: `proactive_harness.db` in that folder. Interpreter: the Hermes venv. Not committed.

The stand-in claim is `BEGIN IMMEDIATE` plus `UPDATE … WHERE delivery='none'`. Both processes connect, wait on one gate, then claim 40 rows from opposite ends. A third process holds `BEGIN IMMEDIATE` for 2.5 seconds while a waiter claims a row that is already taken. A fourth process inserts a probe row and exits without committing.

| Check | Result |
|---|---|
| Process A wins | 21 |
| Process B wins | 19 |
| Lock errors | 0 and 0 |
| Exit codes | 0 and 0 |
| Rows claimed after | 40 |
| Rows unclaimed | 0 |
| Rows with more than one attempt | 0 |
| Waiter elapsed | 2288 ms |
| Waiter won a row | no (the row was already claimed; it did not steal it) |
| Waiter lock errors | 0 |
| Hold committed | yes |
| Crash exit | 3 |
| Crash probe rows left behind | 0 |
| `integrity_check` | `ok` |
| `journal_mode` | `wal` |
| `busy_timeout` | 5000 ms |
| `synchronous` | 1 (`NORMAL`) |

No lost update. One winner per row. A held write made the other writer wait inside the timeout instead of failing. A crash mid-transaction left the earlier commits in place and the uncommitted insert gone.

Phase 2's decision list below is superseded by the Phase 3 proposal. ST-G3's choice of a watcher listener is not locked.

### Phase 3 decisions (superseded)

The nine lines that were here are restated, amended, in the proposal. Do not treat item 3 from Phase 2 (a watcher listener) as the client contract.

## Phase 3 — Proposal (2026-10-13)

No code changes. This amends ST-G1 (eligibility without ranking; `rank_failed` stays visible), ST-G3 (who owns SQL, not where the entry point lives), ST-G5 (what forget can reach), and ST-G7 (an explicit handle among several candidates). Claude's review of ST-G1–G8 is incorporated. Verdicts are not recorded yet.

### Schema (DDL)

`SCHEMA_VERSION = 1`. File: `<HERMES_HOME>\proactive\proactive.db`, which on this machine is `%LOCALAPPDATA%\hermes\profiles\zola\proactive\proactive.db`. Connection: `timeout=5.0`, `journal_mode=WAL`, `busy_timeout=5000`, `synchronous=NORMAL`, `foreign_keys=ON`, `secure_delete=ON`.

```sql
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE items (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL CHECK (source IN ('gmail', 'calendar')),
  message_id TEXT,
  thread_id TEXT,
  event_id TEXT,
  event_updated TEXT,
  idempotency_key TEXT NOT NULL,
  sender_address TEXT,
  sender_address_hash TEXT,
  sender_display_name TEXT,
  entity_id TEXT,
  contacts_handle TEXT,
  entity_resolution TEXT NOT NULL
    CHECK (entity_resolution IN ('memory_entity', 'contacts_handle', 'unresolved')),
  label TEXT CHECK (label IS NULL OR label IN ('urgent', 'important', 'normal', 'ignore')),
  processing TEXT NOT NULL
    CHECK (processing IN ('unranked', 'ranked', 'rank_failed')),
  eligibility TEXT NOT NULL
    CHECK (eligibility IN ('pending', 'eligible', 'suppressed', 'expired')),
  conversation TEXT NOT NULL
    CHECK (conversation IN ('none', 'selected', 'possibly_surfaced', 'acknowledged')),
  delivery TEXT NOT NULL
    CHECK (delivery IN ('none', 'claimed', 'speech_started', 'delivery_uncertain', 'delivered')),
  content_state TEXT NOT NULL
    CHECK (content_state IN ('available', 'content_expired', 'forgotten')),
  loop_matched INTEGER NOT NULL DEFAULT 0,
  rank_attempts INTEGER NOT NULL DEFAULT 0,
  closed_at TEXT,
  detected_at TEXT NOT NULL,
  ranked_at TEXT,
  eligible_at TEXT,
  updated_at TEXT NOT NULL,
  subject TEXT,
  snippet TEXT,
  body TEXT,
  gist TEXT,
  calendar_status TEXT
);
CREATE UNIQUE INDEX idx_items_idempotency ON items (idempotency_key);

CREATE TABLE item_attempts (
  attempt_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL REFERENCES items (id),
  purpose TEXT NOT NULL CHECK (purpose IN ('rank', 'speech')),
  status TEXT NOT NULL CHECK (status IN ('open', 'completed', 'released', 'uncertain')),
  lease_expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE loops (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('open', 'closed', 'expired')),
  intent TEXT NOT NULL,
  predicate_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  matched_at TEXT,
  lapse_told INTEGER NOT NULL DEFAULT 0,
  session_id TEXT NOT NULL,
  entity_id TEXT,
  source_ids_json TEXT NOT NULL,
  address_hashes_json TEXT NOT NULL,
  sender_display_name TEXT,
  subject TEXT
);

CREATE TABLE deliveries (
  id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  outcome TEXT NOT NULL,
  at TEXT NOT NULL
);

CREATE TABLE cursors (
  source TEXT NOT NULL,
  scope_key TEXT NOT NULL,
  cursor_value TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (source, scope_key)
);

CREATE TABLE watcher_health (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  last_ok_at TEXT,
  error_class TEXT,
  updated_at TEXT NOT NULL
);
```

Gmail idempotency key is `gmail:` plus the message id. Calendar is `calendar:` plus the event id plus `:` plus `updated`. `cursors` and `watcher_health` are created here and unused until Track 3. `contacts_handle` and `entity_id` stay null, and `entity_resolution` stays `unresolved`, until Track 3 fills them through `set_sender_resolution`.

### Transition table

Each function is one `BEGIN IMMEDIATE` transaction. A guarded `WHERE` that matches nothing returns a refusal and writes nothing. `complete_rank` nulls `body` and does not change `eligibility` or `delivery`.

| Function | From | To | Who |
|---|---|---|---|
| `insert_item` | absent | `unranked` / `pending` / `none` / `none` / `available`, `entity_resolution=unresolved` | watcher (Track 3) |
| `set_sender_resolution` | any open item | `entity_id` and/or `contacts_handle` filled; resolution enum updated | watcher (Track 3) |
| `claim_rank` | `processing=unranked`, no open rank lease | open rank attempt | ranker (Track 4) |
| `complete_rank` | that attempt | `processing=ranked`, label set, body null | ranker |
| `fail_rank` | that attempt, `rank_attempts` below the cap | `processing=unranked`, attempt released, count incremented | ranker |
| `fail_rank` | that attempt, count at the cap | `processing=rank_failed`, row kept, eligibility unchanged | ranker |
| `release_rank_lease` | rank lease expired | attempt released, processing unchanged | ranker or purge |
| `mark_loop_eligible` | `eligibility=pending`, any `processing`, not suppressed or expired | `eligibility=eligible`, `loop_matched=1` | watcher after evaluate (Track 3); function tested now |
| `mark_eligible` | `eligibility=pending` and `processing=ranked` | `eligible` | plugin code (Track 5) |
| `suppress` | `pending` or `eligible` | `suppressed` | plugin code |
| `expire_eligibility` | `pending` or `eligible` | `expired` | purge |
| `select_for_conversation` | `conversation=none` | `selected` | plugin (Track 5) |
| `mark_possibly_surfaced` | `selected` | `possibly_surfaced` | plugin (Track 5) |
| `acknowledge` | `selected` or `possibly_surfaced` | `acknowledged` | plugin, ticket turn |
| `claim_speech` | `eligibility=eligible` and `delivery=none` | `delivery=claimed`, new attempt | client entry point (Track 6) |
| `mark_speech_started` | `claimed`, matching attempt | `speech_started` | client entry point |
| `mark_delivered` | `speech_started`, matching attempt | `delivered`, plus a `deliveries` row | client entry point |
| `mark_delivery_uncertain` | `speech_started`, matching attempt | `delivery_uncertain` | client entry point |
| `release_speech_lease` | `claimed`, lease expired | `delivery=none`, attempt released | client entry point or purge |
| `close_item` | no open speech attempt | `closed_at` set | plugin, ticket turn |
| `purge_retention` | any | content columns nulled only | serve now; watcher also in Track 3 |
| `forget_subject` | any | loops removed; idle items deleted; in-flight items redacted | `forget_memory`, ticket turn |
| `note_loop_match_on_loop` | loop `open` | `matched_at` set, `status` stays `open` | watcher (Track 3) |
| `expire_loop` | `open` and past `expires_at` | `expired`, `lapse_told` still 0 | purge |
| `close_loop` | `open` | `closed` | `zola_loops` close, ticket turn |

`mark_loop_eligible` is the review amendment. Ranking is advisory (P9-D08). A loop match is a code fact (P9-D09, P9-D11), so an item can become eligible while `processing` is still `unranked` or already `rank_failed`. The function does not change `processing`, `delivery`, or `conversation`. It refuses `suppressed` and `expired`.

Illegal, and a no-op refusal: `delivery_uncertain` back to `none` or `claimed`; a completion whose attempt id does not match; `complete_rank` or the purge changing `eligibility` or `delivery`; `mark_eligible` while `processing` is not `ranked`; deleting a `rank_failed` row because ranking failed.

### `rank_failed` stays visible

Track 4's grounding says a capped malformed rank is left unranked and never dropped. This proposal uses a distinct `processing=rank_failed` after `RANK_ATTEMPT_CAP` so "not tried yet" and "tried and gave up" are different, and the row is still not deleted. `eligibility` is whatever it already was. A loop match can already have set `eligible`.

Track 5 shows them like this:

- `whats_pending` lists every open item, including `rank_failed`, with reason token `rank_failed` when that is the processing value. No gist is invented.
- The first-ticket-turn injection block includes a `rank_failed` item only when `eligibility=eligible` (a loop match, or a later code decision). Otherwise it is not spoken as news and appears only when Brian asks what is pending.
- Unprompted speech (Track 6) still requires `eligibility=eligible` plus a loop match or an `urgent` label. `rank_failed` alone does not interrupt.
- This track exposes `list_open_items` for that later tool. A unit test asserts a `rank_failed` id is still returned and that no transition deletes it for being `rank_failed`.

### Constants

| Name | Value |
|---|---|
| `RANK_LEASE_SECONDS` | 120 |
| `SPEECH_CLAIM_LEASE_SECONDS` | 30 |
| `SPEECH_OUTCOME_LEASE_SECONDS` | 120 |
| `RANK_ATTEMPT_CAP` | 5 |
| `BODY_MAX_AGE_DAYS` | 7 |
| `TEXT_MAX_AGE_DAYS` | 7 |
| `DELIVERY_KEEP_DAYS` | 30 |
| `PURGE_INTERVAL_SECONDS` | 3600 |
| `LOOP_DEFAULT_EXPIRY_DAYS` | 14 |
| `LOOP_MAX_EXPIRY_DAYS` | 90 |
| `HANDLE_TTL_SECONDS` | 1800 |
| `RECORDED_RESULTS_CAP` | 64 |
| `BUSY_TIMEOUT_MS` | 5000 |

`RANK_ATTEMPT_CAP` is the store's ceiling so `fail_rank` can be tested now. Track 4 may propose a different cap; until then the column and the transition use 5.

### Cross-process contract

**To lock:** Python `proactive_store` owns every statement. The client never issues SQL. G-ONE-OWNER is this rule. No `.cs` change in this track.

**Not locked:** where Track 6's entry point lives. Both candidates stay open:

- (a) A localhost listener in the watcher. It needs its own authentication. The watcher is a separate process and can answer when serve is down; speech still fails closed without serve (P9-D02).
- (b) A plugin-registered method on serve's existing socket, the same `_methods` pattern as P9-FIX-ARM's `prompt.submit` wrap (`origin.py`). The dashboard session token is already the authenticator.

Either candidate, when Track 6 builds it: authenticated, loopback only, fail closed. A missing token, a non-loopback peer, or an unknown method does nothing and returns a refusal. This track documents the function names above so either host can call them. The two-process harness stays the proof that two Python processes can share the file through those functions.

### Retention

Unchanged from ST-G4. One purge at `register` and every `PURGE_INTERVAL_SECONDS` on a daemon thread. Body nulls inside `complete_rank`, and also at 7 days if still unranked, which sets `content_state=content_expired` without deleting the row. Subject, snippet, gist, and sender display name null when delivered or at 7 days. `sender_address` nulls on forget, not on the 7-day text pass, because forget matches the hash column. Deliveries older than 30 days are deleted. An item that is `claimed`, `speech_started`, or `delivery_uncertain` can lose content and keep delivery, conversation, eligibility, processing, and the active attempt id. A `rank_failed` row is subject to those same content rules and is not removed for being `rank_failed`.

### Forget cascade

Order, pending record, and the three replies stand as in ST-G5.

Limitation, recorded on purpose: forget reaches proactive rows only through an entity id, an address hash, or a source id already stored on the row. A text sweep runs only after a unique memory entity matched, and only as an extra pass. With no memory entity, `proactive.db` is unchanged and the reply is: "I couldn't link that to one person, so I did not change your pending list."

That limitation is real until the watcher fills identity. **Track 3 requirement:** when the watcher inserts an item, it stores sender identity resolution on that row, a Contacts handle and/or a memory entity id, through `set_sender_resolution`. Until those columns are filled, `entity_resolution` stays `unresolved` and a later forget-by-person cannot see the row. This track does not call Google or Contacts to fill them.

In-flight redaction stands: an item in `claimed`, `speech_started`, or `delivery_uncertain` keeps `delivery` and the attempt id; content, sender address, and entity id are cleared; `content_state=forgotten`.

Replies:

- Both sides succeeded: memory's existing erase sentence, plus that the pending list was included.
- Memory succeeded and proactive did not: "I forgot it in memory, but I could not finish the pending list. I will retry. It is not fully forgotten yet."
- No entity: "I couldn't link that to one person, so I did not change your pending list."

### Predicate grammar

Unchanged from ST-G6. Compile emits operators. The model never supplies the JSON. Evaluate returns matched or not and does not close the loop.

"They reply" is `gmail_thread` plus `sender_is` the other party's recorded address hash plus `after` creation. An incoming item from that address matches. Brian's own later message on the thread does not. If the only recorded message is one he sent, compile refuses. This track does not call Google for the recipient.

Allowed: one Gmail handle with intent `reply`; one calendar handle with intent `cancelled`; a thread handle plus a Contacts handle; words with no checkable fact stored as `brian_confirms`.

Refused: a typed id or address; an unknown, expired, or other-session handle; several live handles and no handle argument; "not from Brian" when this session recorded no address for him.

Expiry default 14 days, cap 90. A lapse sets `expired` with `lapse_told=0`. Track 5 may tell it once, then sets `lapse_told=1`.

### Recorded results and `zola_loops`

Registry: process memory, opaque handle, session, turn, kind, ids, address hashes, sender display name, subject, `created_at`. Cap 64. Lifetime 1800 seconds. Cleared on session end. Refusals are not recorded. The model-visible tool payload gains the handle.

Resolve:

- No handle, exactly one live candidate of that kind: that handle.
- No handle, several live candidates of that kind: `refused_reason=ambiguous`. No row. Zola asks which one.
- An explicit handle that is live in this session: accepted even when other candidates of the same kind are live. The create response includes that item's sender display name and subject so Zola states exactly what she is watching. Logs record the loop id, the intent, and a hash of the handle. Logs do not record the name or the subject.
- Expired, other session, or a typed id or address: refused.

The tool description tells her to ask when Brian's words do not single one out, and that a create response names the sender and subject of the handle she passed.

Schema, on toolset `zola_workspace`, `is_async=False`. No `config.yaml` line. Actions `create`, `list`, `close`. Arguments: `action`, optional `handle`, `intent` (`reply`, `cancelled`, `status_change`, `confirm_close`), and `loop_id` for close. No id or address property. Create and close call `is_brian_turn()` at execution. No ticket: `refused_reason=origin`, no write.

`list_open_items` is the read Track 5's `whats_pending` will call. It returns ids, dimension values, and reason tokens. It does not log subjects.

### Live forget identity

L6 uses a dedicated synthetic identity, checked before the test for zero memory entities and zero Contacts hits. Proposed token: `P9STORE_SYNTHETIC`. Proposed address: `p9store-synthetic@example.com`. The seeded item's subject does not contain that token. Not used until Phase 6, and only after that check.

### Tests

- Every allowed transition succeeds once; every illegal one changes nothing.
- `mark_loop_eligible` from `unranked` plus `pending` sets `eligible` and leaves `processing=unranked`. The same from `rank_failed`. `suppressed` and `expired` refuse.
- Lease expiry release; attempt-id mismatch ignored; `delivery_uncertain` never returns to claimable.
- Retention nulls the right columns, is idempotent, and does not touch delivery or the attempt on claimed, speech-started, or uncertain items.
- `rank_failed` remains in `list_open_items`.
- Forget by entity id, address hash, and source id. No entity: proactive rows unchanged and the unmapped reply. In-flight item redacted, not deleted.
- Memory ok and proactive locked: partial reply, pending record, idempotent retry, record deleted. Crash between the two databases recovers on the next open.
- The four simultaneous conditions from ST-G1 survive the transitions and the purge.
- Handles: one candidate resolves; several and no handle is `ambiguous`; several plus an explicit handle creates and the response carries the synthetic display name and subject; expired or other-session handle refused; a typed id refused.
- "They reply": incoming matches, his own outgoing does not; a sent-only recorded message refuses compile. Matched does not close.
- Ticket required for create and close.
- Source scan: no `INSERT` / `UPDATE` / `DELETE` against this file outside `proactive_store`.
- Existing suites still pass.

### Risks

- Track 6 could still copy SQL into C# later. The proposal forbids that. The entry-point host is deliberately undecided, so Track 6 must not treat either candidate as already chosen.
- Until Track 3 stores sender resolution, forget cannot see watcher rows. The reply says so. That is an honest gap, not a silent delete.
- `rank_failed` is a stronger distinction than Track 4's "leave it unranked." Track 5 must list it. If that distinction is rejected, `fail_rank` at the cap stays `unranked` and `list_open_items` still returns the row with reason `rank_attempts_exhausted`.
- A create that accepts an explicit handle can watch the wrong item if the model picks one Brian did not mean. The response makes her say the sender and subject back. The tool description tells her to ask first. The registry still cannot prove he meant that handle.
- Loopback entry points are a later track. This track does not open a socket.

### Decisions for Brian

Reply with verdicts. "Lock it" accepts every recommended line. A line to change, name it.

1. Orthogonal columns, and `content_expired` as `content_state`.
2. File at `<HERMES_HOME>\proactive\proactive.db`.
3. Lock only this client rule: Python `proactive_store` owns every statement, and the client never issues SQL. Do not lock the entry-point host. Track 6 chooses between the watcher listener (a) and a method on serve's existing socket (b). Either way: authenticated, loopback only, fail closed.
4. `mark_loop_eligible`: a loop match may set `eligible` without ranking, and must not override `suppressed` or `expired`.
5. `rank_failed` after 5 failed rank attempts, row kept, listed by Track 5's `whats_pending`, and not injected as news unless it is already eligible.
6. Leases 120 / 30 / 120. Loop expiry 14 days, cap 90. Handles 1800 seconds, cap 64. Purge every 3600 seconds.
7. An explicit handle is accepted when several candidates are live. The create response returns that item's sender display name and subject. No handle and several candidates is `ambiguous`.
8. Forget reaches only a stored entity id, address hash, or source id. No memory entity means the pending list is unchanged and the reply says so. Track 3 must store sender resolution on each item.
9. The three forget replies, in-flight redaction, and the "they reply" refusal when the only recorded message is one he sent.
10. No `config.yaml` change and no client change in this track.
11. L6 identity token `P9STORE_SYNTHETIC`, address `p9store-synthetic@example.com`, after a zero-hit check. Seed both a synthetic memory entity for that token (alias `p9store-synthetic@example.com`) and the synthetic proactive item, after the zero-hit check, so the forget takes the exactly-one-entity path. Record memory and proactive row counts before seeding, after seeding, and after the forget: the synthetic entity and item are gone, every other count is unchanged. The unmappable-name check stays a separate step.

### Verdicts (2026-10-13)

Brian: "lock it".

Addition to line 11, verbatim:

> One addition to line 11 (L6): seed BOTH a synthetic memory entity for P9STORE_SYNTHETIC (alias p9store-synthetic@example.com) and the synthetic proactive item, after the zero-hit check, so the forget takes the exactly-one-entity path. Record memory and proactive row counts before seeding, after seeding, and after the forget: the synthetic entity and item are gone, every other count is unchanged. The unmappable-name check stays as a separate step.

Lines 1–10 stand as written above. Line 11 includes that addition. Phase 4 implemented the locked proposal. Not committed.

## Phase 4 — Implement (2026-10-13)

Python `proactive_store` owns every statement. `zola_loops` registers on `zola_workspace` (`is_async=False`). No `config.yaml` change and no client change. `.gitignore` ignores `proactive.db`, `-wal`, and `-shm`.

Forget of one memory entity deletes that entity, its aliases, and its `entities_fts` rows in the memory transaction, writes `pending_proactive_forget`, then calls the store. It does not run the orphan-entity sweep, so unrelated counts stay put. A proactive lock or a crash leaves the pending row. The next store open, retention pass, or ticket turn retries it with no names. Text sweep runs only on the first call, and only after that unique entity matched.

Hermes `on_session_end` runs every turn (`send_gate.py` `on_session_end_hook`). Recorded-result handles are not cleared there. They live for `HANDLE_TTL_SECONDS` (1800) inside the session id and are dropped for a different session id. Clearing them on that hook would make the next turn's "that email" die. This is an implementation correction so locked line 7 works. It is recorded here; the phase did not stop for it.

Tests, 2026-10-13, venv `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`:

| Suite | Result |
|---|---|
| `zola_workspace` | 200 OK (baseline 184, plus 16 in `test_p9_store.py`) |
| `zola_memory` | 121 OK (baseline 117, plus 4 in `test_p9_store_forget.py`) |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |

The L6 count test is `test_zero_hit_then_exactly_one_entity_counts`. The unmappable name is a separate step in that test, before the seed. Live counts are Phase 6. The synthetic token and `example.com` address are the only identity used.

## Phase 5 — Review fixes (2026-10-13)

Claude's read of the store, loops, and recorded results:

1. A loop belongs to Brian, not to a session. `list_open_loops` returns every open loop. `session_id` stays on the row as provenance. Close still accepts only a loop id that `list` returned in this session.
2. Each listed loop includes `sender_display_name` and `subject` with id, intent, expires_at, and matched. That text is mail, so the list goes through `mark_then_frame`: the session is tainted, and the body is framed untrusted. A create response's `watching` fields take the same path when the session is not already tainted. The log line is a count only.
3. When a loop is closed or expired, retention nulls `sender_display_name` and `subject`. Source ids and address hashes stay until the row is deleted. `close_loop` still clears that text immediately; the purge clears any closed or expired row that still has it, including loops it has just expired. An open loop is left alone.

Suites after these fixes: workspace 203 OK, memory 121 OK, tools 44 OK, tts 8 OK.

## Phase 6 — Deploy (2026-10-13)

No `config.yaml` change. Live config is still SHA-256 `0DD2F5635E438AAE6644FBA0B7502AE54C2AFF8837D599D3E2F8F6EA77FE1E26`, 4,629 bytes, before and after the restart.

Backups of the six replaced files are in `C:\Users\test\Dev\zola-spikes\p9-store\plugin-backup\`. `loops.py`, `proactive_store.py`, and `recorded_results.py` were new, so they have no backup. Tests and `__pycache__` were not copied.

| Backup file | Bytes | SHA-256 |
|---|---:|---|
| `zola_workspace____init__.py` | 6440 | `90081583CB0570EDCA2BF7D7076597C13DE81669EE494723B19D668154D9B2E1` |
| `zola_workspace__contacts.py` | 5664 | `E34343C96CCF8CDAF4FFB91C498CC6FEFFDF5020554D092A5F567831CDB3C3DE` |
| `zola_workspace__gcal.py` | 25205 | `6F17605A69B606946DC9C8ADC50EEB84282E212AABCA2E1EF57778EB7BCDD3BA` |
| `zola_workspace__gmail.py` | 40053 | `DD018F6AE1D220F9D5B3EE10D60874784E556E1EB46D4F7CD3B4079214D3E7A7` |
| `zola_workspace__log.py` | 2780 | `CE00D6FB46FFEAB36E2A212E05BB68FC7ED6CB9292D30E8380355429D2976650` |
| `zola_memory__forget.py` | 53049 | `D0717731AEAA7D45C0A38535503CAF488AB53C7D9E317B5E24E193CB6E40E891` |

Repo file and live mirror SHA-256 match for each copied file.

| File | Bytes | SHA-256 |
|---|---:|---|
| `zola_workspace/__init__.py` | 7150 | `67642E14509F5B009EFE227D9B1157FE37D7C07CD964A922181C2A9EB7BBB652` |
| `zola_workspace/contacts.py` | 6351 | `A8B29E55185DCCFA404E0EE8CF9E06E84C7334E599AF92F720A5CB8A436E9AC4` |
| `zola_workspace/gcal.py` | 26330 | `B031E31EB1D9391B1B5E7873571C7F8CDB8401C4DA4E6D48B14D46372C90ED1D` |
| `zola_workspace/gmail.py` | 41669 | `B30BC3D7376E74E221697075E1B2AF7309E2642FA15E02C512944B5DBCDD1D79` |
| `zola_workspace/log.py` | 2924 | `33D49FAE7E9CF472668692396E430B6A2CAFBF11165FFD602E923378F279D891` |
| `zola_workspace/loops.py` | 13048 | `41B12A1FD297374F9DF104E54E73061829148726CD78370E203C7028D99090E2` |
| `zola_workspace/proactive_store.py` | 50942 | `70149A5D7E6E67CA974A9A5F4D36C33F443F1DCAAC1D4D638DF3E1D350CDE4D6` |
| `zola_workspace/recorded_results.py` | 4881 | `6B3F60CC0380C7D06EB1CB0C2F6EDDB0B1F7BA8852C1B22BB2187420A245A07C` |
| `zola_memory/forget.py` | 62240 | `8388283CB62D05C9CC50E085D8AFC4BDDAFC678D06130ABFF446D24BB2BE171B` |

WM_CLOSE of client 12988. Shim 24628 and CPython 23000 exited with it. Blender and the p10 listen processes were left running. New window: client 18340, parent 25264, start 2026-10-13 10:18:06; shim 29816, parent 18340; CPython 12368, parent 29816; both started 10:18:07. One dedicated Zola serve.

`proactive.db` is `C:\Users\test\AppData\Local\hermes\profiles\zola\proactive\proactive.db`. Schema version 1. Tables: `cursors`, `deliveries`, `item_attempts`, `items`, `loops`, `meta`, `watcher_health`. Journal mode `wal`. A search of `%LOCALAPPDATA%\hermes`, this repo, and `zola-spikes\p9-store` found that file as the only profile store. The no-ticket harness wrote a separate scratch file, `zola-spikes\p9-store\noticket\proactive.db`, and did not insert a loop.

Live purge once, counts only: bodies 0, texts 0, content_expired 0, deliveries_deleted 0, loops_expired 0, loops_text_cleared 0, speech_released 0, speech_uncertain 0. After that pass, items 0, loops 0, item_attempts 0, deliveries 0.

No-ticket create, through the live `loops_handler`: with no turn, `refused_reason=origin`. With a tui turn and no client-origin ticket, `refused_reason=origin`. Scratch loop count stayed 0.

The isolated L6 count test `test_zero_hit_then_exactly_one_entity_counts` passed again against a scratch store. The live seed waits until that step.

Brian confirmed the titled test email is in the inbox (2026-10-13).

L1 passed. She said she is watching for a reply. `proactive.db` has 1 open loop, intent `reply`, created `2026-10-13T17:31:18Z`, expires `2026-10-27T17:31:18Z`, `matched_at` empty, entity id empty. Items, attempts, and deliveries stay 0. The predicate is `all` of `gmail_thread` (thread id SHA-256/16 `e3971975972c3466`, length 16), `sender_is` (stored address hash is 64 hex characters; SHA-256/16 of that hash `dfdc7acb33391ba6`), and `after` `2026-10-13T17:31:18Z`. Two source ids, both the same hash as the thread id. Display-name and subject lengths are 12; the text is not copied here. Loop id SHA-256/16 `98aa1357d361770d`. Session SHA-256/16 `8440a4500b042db6`.

Ticket check: `agent.log` `2026-10-13 10:18:09` `origin wrap installed method=prompt.submit`. `10:30:25` `tui prompt accepted`, `platform=tui`, session `20261013_101810_a9f313` (same SHA-256/16 as the loop row). `10:31:18` `tool zola_loops completed`. No `gate brian_only action=refuse` on that turn. The row exists, so `insert_loop`'s ticket check passed.

Voice L1b is invalid. It is not a store fault and not a P9-STORE result. Brian switched to Text mode for the rest of Phase 6. The typed redo and the L2 miss are recorded below.

### Phase 6 FINDING (not part of P9-STORE)

After the Deepgram switch, inter-sentence gaps in her reply let the follow-up listen open (`bout_stop` + 0.5 s quiet). Her own speech was transcribed and accepted as a Brian turn (`10:38:03`, 116 chars, `prompt.submit` with a ticket). The next real line created a loop with the handle that false turn had singled out.

There is no `bout_start` token. `bout_stop` is on the `follow_up_release` line. No `follow_up_release quiet_restart` in this window, so the 0.5 s quiet ran to completion. The echo check does not write its own line: a match would be `transcript drop reason=echo` (and maybe `echo-reopen`). This window has neither. Both transcripts were admitted.

Exact `voice-timeline.log` lines, `2026-10-13T10:37:49` through `10:38:31` (wake-reconcile lines omitted):

```
2026-10-13T10:37:49.3045201-07:00 follow_up_release seeded_active_bout=true
2026-10-13T10:37:51.0819324-07:00 follow_up_release rule=monitor complete=2026-10-13T10:37:49.3043176-07:00 estimatedEnd=2026-10-13T10:38:17.9130163-07:00 bout_stop=2026-10-13T10:37:51.0818453-07:00 quiet_s=0.5 fire=2026-10-13T10:37:51.0818632-07:00 seen=false
2026-10-13T10:37:51.0828400-07:00 start=2026-10-13T10:37:17.0413178-07:00 complete=2026-10-13T10:37:49.3043176-07:00 estimatedEnd=2026-10-13T10:38:17.9130163-07:00 delay=0s fireOrCancel=2026-10-13T10:37:51.0827407-07:00 followUpStarted=True words=72
2026-10-13T10:37:51.0836166-07:00 capture lifecycle gen=5 kind=FollowUp from=Settled to=Starting signal=start
2026-10-13T10:37:51.3279091-07:00 capture lifecycle gen=5 kind=FollowUp from=Starting to=Accepting signal=listening
2026-10-13T10:38:03.7285730-07:00 transcript len=116 filtered=false stop=false nospeech=false bound=none capture_start=2026-10-13T10:37:51.0833063-07:00 capture_stop=2026-10-13T10:38:03.7284697-07:00 duration_s=12.4
2026-10-13T10:38:03.7288145-07:00 capture lifecycle gen=5 kind=FollowUp from=Accepting to=Settled signal=transcript
2026-10-13T10:38:03.7290167-07:00 transcript admit gen=5 kind=FollowUp clarify=none len=116 owner_window=start=2026-10-13T10:37:51.0833063-07:00;stop=
2026-10-13T10:38:09.4519230-07:00 turn_timing turn=4 kind=voice transcript_to_submit_ms=18 submit_to_first_delta_ms=4505 first_delta_to_first_sentence_ms= submit_to_first_sentence_ms= submit_to_complete_ms=5705 first_sentence_to_first_audio_ms= submit_to_first_audio_ms=15 tools=0 approval=0
2026-10-13T10:38:20.4073845-07:00 follow_up_release rule=monitor complete=2026-10-13T10:38:09.4523545-07:00 estimatedEnd=2026-10-13T10:38:17.1519738-07:00 bout_stop=2026-10-13T10:38:20.4072179-07:00 quiet_s=0.5 fire=2026-10-13T10:38:20.4072331-07:00 seen=false
2026-10-13T10:38:20.4079312-07:00 start=2026-10-13T10:38:03.7553747-07:00 complete=2026-10-13T10:38:09.4523545-07:00 estimatedEnd=2026-10-13T10:38:17.1519738-07:00 delay=0s fireOrCancel=2026-10-13T10:38:20.4078938-07:00 followUpStarted=True words=20
2026-10-13T10:38:20.4083030-07:00 capture lifecycle gen=6 kind=FollowUp from=Settled to=Starting signal=start
2026-10-13T10:38:21.0695947-07:00 capture lifecycle gen=6 kind=FollowUp from=Starting to=Accepting signal=listening
2026-10-13T10:38:31.9453956-07:00 transcript len=39 filtered=false stop=false nospeech=false bound=none capture_start=2026-10-13T10:38:20.4081850-07:00 capture_stop=2026-10-13T10:38:31.9452921-07:00 duration_s=10.875
2026-10-13T10:38:31.9456877-07:00 capture lifecycle gen=6 kind=FollowUp from=Accepting to=Settled signal=transcript
2026-10-13T10:38:31.9458519-07:00 transcript admit gen=6 kind=FollowUp clarify=none len=39 owner_window=start=2026-10-13T10:38:20.4081850-07:00;stop=
```

`agent.log` on that session: `10:38:03` `tui prompt accepted` 116 chars, then `interrupted_during_api_call`. `10:38:31` `tui prompt accepted` 39 chars. `10:38:39` `zola_loops` completed. No `gate brian_only` refusal. The second loop is intent `reply`, created `2026-10-13T17:38:39Z`, thread SHA-256/16 `77163fa9ed620a02`, subject length 97, display-name length 12, loop id SHA-256/16 `3a97f2d83707e409`. Search had recorded several messages (`count=9`). Several live messages and no handle is `ambiguous`. The create succeeded, so the call carried a handle.

Her reply to that create (assistant message, 73 characters) contains the sender display name and a 15-character slice of the subject (3 of 17 subject words). It does not contain the full subject. The `zola_loops` tool result (634 characters) is framed untrusted and contains both the full subject and the sender display name. Neither string is copied here.

Typed L1b passed (Text mode, same session). `10:50:35` prompt accepted, 51 chars. `10:51:03` `gmail_search` completed (10286 chars). No `zola_loops` on that turn. `10:53:23` prompt accepted, 39 chars. `10:53:27` turn ended, `response_len=31`, no tool call. She asked which Google email he meant. Store unchanged: 2 open loops, the same two ids, items 0, attempts 0, deliveries 0.

L2 missed the tool. New Text session `20261013_105514_760952`, history 0. `10:55:26` prompt accepted, 26 chars. `10:55:31` turn ended, `tool_turns=0`, `response_len=52`. She said she is watching for the P8 smoke test tomorrow at 3 PM. `zola_loops` was not called. Memory prefetch for that turn is `returned_len=0` and retrieve `candidates=0`. Store unchanged: the same 2 open loops. L3 has not started.

Description fix (tool text only, no `SOUL.md`). `zola_loops` now says to call list for "what are you watching for", "what are you keeping an eye on", "what am I waiting on", "any open loops", and "what did I ask you to watch". The list result is the only source; she must not answer that question from memory or the conversation, and a tool failure is "could not check". The handle, ambiguity, sender-and-subject, and no-id sentences are unchanged. Test `test_list_description_names_triggers_and_only_source`. Suites: workspace 204 OK, memory 121 OK, tools 44 OK, tts 8 OK.

Live `loops.py` backup `zola_workspace__loops.py` is 13048 bytes, SHA-256 `41B12A1FD297374F9DF104E54E73061829148726CD78370E203C7028D99090E2`. Repo and live mirror are 13502 bytes, SHA-256 `3B29E870FBD66175A43DEEA0B727785D5ADDE5B91221F88B794AE31D1019D92C`.

WM_CLOSE of client 18340. Shim 29816 and CPython 12368 exited with it. Blender and the p10 listen processes stayed up. New window: client 17744, parent 36748, start 2026-10-13 12:23:27; shim 14448, parent 17744; CPython 35492, parent 14448; both started 12:23:27. `agent.log` `12:23:30` `origin wrap installed method=prompt.submit`. One dedicated Zola serve. Open loops still 2.

L2 retry missed the same way. New Text session `20261013_122331_4ff24e`, history 0. `12:24:37` prompt accepted, 26 chars. She called `skill_view` on `everyday-assistance` (4673 chars), not `zola_loops`. `12:24:47` turn ended, `response_len=52`. Memory prefetch `returned_len=0`, retrieve `candidates=0`. The P8 sentence is in `memories\MEMORY.md`, which is always-on Hermes memory, not the zola prefetch. Plugin tools are deferred: the catalog line is the first sentence only, clipped to 60 characters (`tool_search_catalog._short_desc`). That sentence is 62 characters, so the catalog shows a clipped "Create, list, or close…" line. The trigger phrases and the only-source sentence are later sentences, so they were not in the prompt. Store was not written; `zola_loops` did not run. L3 has not started.

Catalog fix. The first sentence is now `What Brian asked you to watch for: list, add, or close.` (55 characters, contains `watch`). Every later sentence is unchanged. Test `test_catalog_first_sentence_is_short_and_says_watch`. Suites: workspace 205 OK, memory 121 OK, tools 44 OK, tts 8 OK.

The replaced live file is backed up as `zola_workspace__loops-before-60.py`, 13502 bytes, SHA-256 `3B29E870FBD66175A43DEEA0B727785D5ADDE5B91221F88B794AE31D1019D92C`. The earlier backup `zola_workspace__loops.py` is unchanged. Repo and live mirror are 13495 bytes, SHA-256 `24E4F728BC028120AAC68253017F49107D11DB799A810386C4A20A5FCDA8A7C2`.

WM_CLOSE of client 17744. Shim 14448 and CPython 35492 exited with it. Blender and the p10 listen processes stayed up. New window: client 26436, parent 2504, start 2026-10-13 12:33:26; shim 26400, parent 26436; CPython 6696, parent 26400; both started 12:33:27. `agent.log` `12:33:30` `origin wrap installed method=prompt.submit`. One dedicated Zola serve.

L2 passed on the second new Text conversation. `12:39:42` session `20261013_123921_a9572f`, history 0, prompt 26 chars. She called `skill_view`, `tool_describe`, then `zola_loops` (820 chars). The tool result is framed untrusted and contains both stored display names and both stored subjects. `zola_workspace.loops state=complete count=2`. The session is tainted. Her reply is 178 characters and contains both names and both subjects. Store unchanged: 2 open loops, 0 closed. An earlier new conversation at 12:35 (`20261013_123331_812960`) also listed count 2 in a framed result, but the 119-character reply omitted one display name and the longer subject.

L3 passed in that same session. `12:45:31` prompt accepted, 35 chars. `zola_loops` returned `{"ok": true}` (12 chars), then a second `zola_loops` (546 chars, framed, contains the remaining test title). Her reply is 58 characters. The loop created `2026-10-13T17:38:39Z` (id SHA-256/16 `3a97f2d83707e409`) is `closed`, and its display name and subject are NULL. The loop created `2026-10-13T17:31:18Z` stays `open`, display-name length 12, subject length 12. Items, attempts, and deliveries stay 0.

L4's first question did not create a loop. Same session, `12:47:45` prompt accepted, 37 chars. Four `gmail_search` calls, no `zola_loops`. Turn ended `12:48:45`, `response_len=141`. The reply does not offer to watch. Store unchanged: 1 open loop, 1 closed loop.

L2 passed. L3 passed. Recorded.

L4 is restructured. Proactive offering is SOUL / Track 5 behavior, not a pass condition for this track. This track tests that a loop is created only on Brian's explicit yes. Finding: Zola does not proactively offer a watch today. Carried to Track 5 as a SOUL line. No `SOUL.md` edit in this track.

Six typed lines. After each: whether `zola_loops` was called, the action, and the open-loop count. Expected: a create only on "Yes, watch it.", with sender and subject read back. No create on either "offer, don't set it up yet", and no create on the subject change. The two finds are the message from the L4 search, then the P9 loop test email. Open loops before these lines: 1.

Line 1, new Text session `20261013_125839_1ac22b`, `12:58:44`, prompt 45 chars. `gmail_search` and `gmail_read`. `zola_loops` not called. Open loops 1.

Line 2, same session, `13:00:10`, prompt 61 chars. No tool call. `zola_loops` not called. The reply offers in words (`response_len=58`). Open loops 1.

Line 3, same session, `13:02:19`, prompt 14 chars. `zola_loops` called, action `create`, intent `reply`. New open loop created `2026-10-13T20:02:27Z`, id SHA-256/16 `7bba6d3c51083a6b`, display-name length 13, subject length 77. The tool result is framed and contains that sender and subject. Her reply (131 characters) contains both. Open loops 2.

Line 4, same session, `13:04:32`, prompt 28 chars. `gmail_search` only. `zola_loops` not called. Open loops 2.

Line 5, same session, `13:05:55`, prompt 27 chars. No tool call. `zola_loops` not called. The reply offers in words (`response_len=83`). Open loops 2.

Line 6, same session, `13:07:22`, prompt 21 chars. `terminal` only. `zola_loops` not called. Open loops 2.

L4 passed on the restructured check. A `create` happened only on the explicit yes. Neither offer created a loop, and the subject change did not create one. Open loops are the original test watch plus the one created at `2026-10-13T20:02:27Z`.

L5 is stopped. It is not a pass and not a fail of the forget-by-topic rule. Same session, `13:10:32`, prompt 24 chars. `forget_memory` completed in 0.01s and returned `refused_reason=origin`. `zola_memory.forget_tool` is `confirm=false candidate_count=0 refused_reason=origin ok=false elapsed_ms=0`. No `forget_guard` line. `zola_loops` was not called. Open loops stay 2. The loop created `2026-10-13T17:31:18Z` still has its subject (length 12). The proactive store was not reached. L6 has not started. No code change from this diagnosis.

Corrected expected result, from the locked design: forget reaches proactive rows only through a memory entity, an address hash, or a source id. "Forget the P9 loop test." names a subject, not a person. The correct outcome is the unmapped reply ("I couldn't link that to one person, so I did not change your pending list.") and the loop stays open. Removing a loop by topic is "Stop watching for that" (L3, passed). L5 is re-run after the origin bug below is fixed.

### Phase 6 FINDING — forget_memory origin on a client turn (not fixed)

The `13:02` `zola_loops` create in this same session accepted the ticket: prompt accepted, 14 chars, no `gate brian_only` refuse, then `pending_write` turn index 3. The L5 turn is the same process (wrap installed `12:33:30`, no later restart).

L5 turn, read from the logs:

- Mint: the wrap does not log each mint. It logs one install line. `13:10:32` `tui prompt accepted` `kind=user` `chars=24` is the `prompt.submit` handler, which runs only after the wrapper. A ticket is minted there for the sanitized submit text, and kept when the handler starts a turn.
- Bind: `zola_memory.pre_llm_call` at `13:10:32.774`, then `on_turn_start` `msg_len=24`. No `gate brian_only action=refuse` in `agent.log` or `zola_workspace.log`. A hash miss in `consume_for_hook` logs that refuse, so this turn's `pre_llm` `user_message` matched a pending ticket and `turn_id` was stored in the process-global `_bound` map.
- What the handler looked up: `origin_allows` takes `kwargs["turn_id"]`, then `tools.approval_context._approval_turn_id`, then `origin.current_turn_id()`, then the thread flag. `sync_turn_allowed` does not use a turn id. It takes one permit whose SHA-256 equals `user_content`. The permit is recorded at consume from the `pre_llm` string. L5's disposition is `drop` / `forget_intent`, and that check is evaluated before the keep check, so a matching permit would be spent and still write no row. `sync_turn` logged `user_len=24` and no `pending_write`. The log does not say whether the hash matched.

Why it failed: Hermes runs `pre_llm_call` on a timeout worker (`hermes_cli/plugins_dispatch.py`, `_HOOK_TIMEOUT_BOUNDED_HOOKS` includes `pre_llm_call`). `consume_for_hook` sets the origin ContextVar on that worker. The worker's context is discarded when the hook returns. `_bound` and the sync-permit list are process-global, so they survive. The turn thread's `current_turn_id()` stays empty. `retrieve` at `13:10:32.777` is `candidates=0 returned=0 elapsed_ms=0`, which is the shape of the `client_origin_active()` short-circuit.

`zola_loops` still passes. Registry dispatch calls `model_tools.handle_function_call` with `turn_id=agent._current_turn_id`, which sets `_approval_turn_id`. `is_brian_turn` then checks `_bound`.

`forget_memory` does not. Both memory-provider call sites pass only the args: `agent/tool_executor.py` (`handle_tool_call(function_name, next_args)`) and `agent/inline_tool_executors.py` (the same). No `_approval_observability`. `handle_forget_memory` calls `origin_allows(**kwargs)` with empty kwargs, finds no turn id, and returns `refused_reason=origin` in 0ms. The pre_tool hook does not block: it receives `turn_id` from `tool_hook_ids`, `turn_is_bound` is true, and `confirm=false` returns without a `forget_guard` line.

P9-FIX-ARM S3 does not cover this. S3 allowed the built-in `memory` tool (`forget_guard action=allowed tool=memory`, then `fact_erase`). That gate is the pre_tool hook, which has `turn_id`. S3 never called `handle_forget_memory`.

`git diff main -- hermes-plugins/zola_memory/forget.py` does not change `origin_allows`, `sync_turn_allowed`, or the origin gate in `handle_forget_memory`. P9-STORE adds the proactive retry and the unmapped reply after that gate. This bug is not a P9-STORE edit.

Proposed fix, not applied: pass `turn_id=agent._current_turn_id` into those two `handle_tool_call` sites. `origin_allows` already checks `kwargs["turn_id"]` against `_bound`. That is a Hermes edit. A plugin-only stash keyed by session would reintroduce the latest-turn fallback P9-FIX-ARM removed.

Finding, recorded: `forget_memory` has refused origin on a client turn since P9-FIX-ARM. P9-STORE did not cause it.

Scope expansion implemented. No Hermes edit. Three fixes: the forget handler's token, the forget hold on the turn thread, and episode retrieve on the turn thread.

Execution-args check, before the code. The named writers do not log the post-modify execution args. `hermes_logging.py` sends logging records to `agent.log` (INFO+) and `errors.log` (WARNING+); `print()` is not that stream. `agent/tool_executor.py` logger calls record names, durations, and result length, not the args dict. `agent/session_persistence.py` `_db_flush_row` (lines 172–174) stores `msg["tool_calls"]`. That dict is built in `agent/chat_completion_helpers.py` `_assistant_tool_call_dict` (lines 1472–1474) from the API `tool_call.function.arguments`, before the pre_tool modify, and flushed before tools run. `agent/agent_runtime_helpers.py` `_trajectory_tool_call_turn` (lines 112–128) converts those stored arguments. The warning at line 125 is the first 100 characters of invalid stored JSON, not the execution dict. `dump_api_request_debug` writes the API request body. `hermes_cli/observability/relay_shared_metrics.py` `start_tool_call` (line 329), `record_tool_call` (line 369), and `_open_tool_call` (lines 665–670) record a tool category and duration, not args. Two exposures are not those writers: `agent/tool_executor.py` lines 915–919 print execution args to stdout when tool progress is on, and `tui_gateway/tool_progress.py` `_on_tool_start` (lines 245–252) and `_on_tool_complete` (line 258) put the execution args on `tool.start` and `tool.complete`. Socket exposure of the token is accepted: the token is single-use, bound to the turn, tool call, tool name, and args hash, with a 60-second TTL, and socket access already implies turn submission. The client reads tool id and name only.

Text identity, before the permit lookup. The string hashed at consume and the string the hooks receive are the same bytes on a typed or voice turn. `agent/turn_context.py` line 943 sets `original_user_message` to `persist_user_message` when that argument is present. Line 679 passes that string into `pre_llm_call` as `user_message`. `zola_workspace/turn_context.py` `pre_llm_call_hook` gives it to `origin.consume_for_hook`, and `origin.py` `_note_sync_ready` (lines 111–118) hashes it. `agent/turn_context.py` lines 770–775 pass that same `original_user_message` to `on_turn_start` and then to prefetch. Hermes prefixes do not touch it. `tui_gateway/prompt_turn.py` lines 509–513 prepend the speech-interrupted note, reaction notes, and the HUD note onto `run_message` only. Lines 544–545 set `persist_user_message` to `prompt` when the turn has no images, and line 563 calls `run_conversation(run_message, persist_user_message=prompt)`. A voice turn is that same `prompt`. `agent/turn_context.py` lines 560–563 put an API-facing voice prefix back on the conversation dict's content; `original_user_message` stays the persist string. Prefetch strips skill scaffolding (`agent/memory_manager.py` line 396). `agent/skill_commands.py` lines 85–86 return the string unchanged unless it starts with the skill-invocation prefix. A slash prompt never receives a ticket (`origin.py` `_is_slash`), so that one case has no permit and fails closed.

The token is the map key. The value is `(turn_id, tool_call_id, tool name, canonical args hash excluding the token, expiry)`. TTL 60 seconds. The pre_tool hook strips any model-supplied token key, and mints only when `turn_context.is_brian_turn(turn_id)` is true. The handler pops the token, checks the row, and deletes it on every outcome. A miss returns the existing origin refusal. Log lines are `zola_memory.origin_token` with `action=minted`, `action=consumed`, or `action=refused` plus a reason. The token value is not in the result, the log, or the error.

`turn_context.resolve_turn_from_permit` is a non-consuming lookup: exactly one unexpired sync permit whose text hash equals the message, then `is_brian_turn`. Zero or several return None and log `origin_unresolved`. `on_turn_start_forget_hooks` and `retrieve_episodes` use it when no turn id was passed and the test override is unset. The ContextVar path is still in the code and does not serve the turn thread. Remaining readers: `origin.end_turn` reads `current_turn_id()` and, on the turn thread, that value is empty; `forget.origin_allows` falls back to it only when kwargs, the approval context, and that ContextVar are all empty (the pre_tool hook passes `turn_id`, and the forget handler no longer calls `origin_allows` on a production turn); `forget.client_origin_active` and `forget.current_origin_turn_id` have no production caller. The test in `test_forget_phase4.py` still calls `client_origin_active`.

`origin_unresolved` is a WARNING on logger `zola_workspace`. Fields are `path` and `reason` only.

Suites after the change: workspace 205 OK, memory 131 OK, tools 44 OK, tts 8 OK.

Deployed to the live plugin mirror. Tests and `__pycache__` were not copied. Backups are in `C:\Users\test\Dev\zola-spikes\p9-store\plugin-backup\` with the suffix `-before-origin-token`. Live file matches the repo hash.

| SHA-256 before | SHA-256 after | Bytes | File |
|---|---|---:|---|
| `8388283CB62D05C9CC50E085D8AFC4BDDAFC678D06130ABFF446D24BB2BE171B` | `105DD4AAE953DBA6E7BE73E7B53D9C98F2D9F6F5745BE342A08BD01AD12D5535` | 68188 | `zola_memory/forget.py` |
| `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` | `4898ED462BCBAF503A8B478B16E5F482756C28BFF36BFDCBEB3B67740FFB341D` | 4372 | `zola_memory/log.py` |
| `84E0C44975579C0B6878E64355ADAB4D30B09EE9938E61E9855A6774CC11FA39` | `DA2E5C88CEE4182BB8C9DCCE09998FAAA45F6FC2A08250617E91E0F6F64DD4E0` | 13984 | `zola_memory/retrieve.py` |
| `12AA675E8B693BADA15160FB251F128ADF7C144F2A6A3C75212F82DD3FA9AC83` | `2C5991569F09926E5256014EC0718252F66C7BF7E4BE674B48080390A181B0BA` | 13868 | `zola_memory/provider.py` |
| `4581898A844C75BD30C8778A3B3611429D0381D3834E4EFCEC449BCF0D7F4DB1` | `43F59BAD2E0312B7AA080CB1A772CC253B6A27B4414B9DBC4CAAAF35C650CE19` | 16203 | `zola_workspace/origin.py` |
| `84B0E58E58EE0A6913F1A9A150115E8C291FF4D339B8BF1EA973BD65ACC1AFAF` | `6BD9E082276A88AC17EA7B370F8A415902D174E2E17D17B4064A0820EB4D5D3C` | 7967 | `zola_workspace/turn_context.py` |

WM_CLOSE of client 26436. Shim 26400 and CPython 6696 exited with it. Blender and the p10 listen processes stayed up. The window did not relaunch on its own, so the Debug client was started. New window: client 24732, parent 5100, start 2026-10-13 14:19:40; shim 32272, parent 24732; CPython 21680, parent 32272; both started 14:19:41. `agent.log` `14:19:43` `origin wrap installed method=prompt.submit`. One dedicated Zola serve.

Stopped for Brian's live checks. R1 and R2 were run by Brian. R3 has not been called. L6, the MEMORY.md line-7 cleanup, the no-ticket harness, and closeout stay as already planned.

R1, recorded from the log. The origin short-circuit is gone: retrieve now takes 1–2 ms and can count candidates. On the recall turns the score gate still returned nothing, so no episode text was injected.

Resumed session `20261007_130438_f4d04b`. `14:28:24` prompt 55 chars, history 45. `retrieve candidates=8 returned=0 top_score=0.0 elapsed_ms=2`, prefetch `returned_len=0`. No tool. Reply 46 chars. `pending_write` turn index 1. `14:28:43` prompt 44 chars. `retrieve candidates=0 returned=0 elapsed_ms=2`. She called `session_search`. Reply 51 chars.

New session `20261013_142932_f40cb4`. `14:30:14` prompt 52 chars, history 0. `retrieve candidates=8 returned=0 top_score=0.0 elapsed_ms=1`, prefetch `returned_len=0`. Tools: `skill_view`, `tool_describe`, `session_search`. Reply 50 chars. Brian marked R1 complete.

R2, same new session, `14:30:58` prompt 24 chars. Origin refusal is gone. The locked outcome (unmapped reply, loop left open) did not happen.

`retrieve candidates=8 returned=1 top_score=3.1802`, prefetch `returned_len=343`. `origin_token action=minted`, then `action=consumed`. `forget_tool confirm=false candidate_count=11 group_count=9 refused_reason=- ok=true elapsed_ms=3`. `forget_hold action=set held_count=1`. The tool result is the which-one message, not the unmapped sentence. A later `confirm=true` was blocked: `forget_guard action=blocked tool=forget_memory`. She then called `zola_loops` list, then `zola_loops` close. The close result is `ok=true` (12 characters). Disposition `drop` / `marked`. Reply 185 chars. No `origin_unresolved`.

The loop created `2026-10-13T17:31:18Z` is now `closed`, and its name and subject are null. The loop created `2026-10-13T20:02:27Z` is still open (name length 13, subject length 77). The Google loop created `2026-10-13T17:38:39Z` was already closed. Open loops: 1.

### R2 behavior (read-only), then L6

Brian accepted R1 as the origin regression fixed (candidates 0 to 8) and accepted the R2 origin path (token minted, then consumed, no refusal). The which-one reply is the score gate and the forget branch order, not another origin failure.

Score gate. `retrieve.py` `candidate_passes_gate` (lines 71–86) keeps a hit only when it is an entity hit, shares a number, or shares at least two distinctive terms. `EPISODE_MIN_SCORE` is 0.15 (line 26). The log's `candidates` is the pool before that gate. `returned` and `top_score` are after it, so `top_score=0` means nothing qualified.

For 2026-10-05 through 2026-10-09 there were 246 retrieves and 64 with `returned>0`: 10-05 98 retrieves / 21 returned, 10-06 54 / 0, 10-07 11 / 0, 10-08 44 / 20, 10-09 39 / 23. Since `14:19:43` today, 4 retrieves and 1 with `returned>0` (the R2 turn: pool 8, one entity hit, top score 3.1802).

Both R1 queries (55 characters and 52) had a pool of 8, zero entity hits, and eight raw scores above 0.15: 0.4638, 0.4157, 0.4018, 0.3826, 0.3766, 0.3652, 0.3652, 0.2938. Each of the eight shared exactly one distinctive term. The gate dropped all of them. That is the designed X3 behavior. It is not a separate finding. Before the origin fix those turns were `candidates=0 elapsed_ms=0`, so the gate never ran.

R2 branch order, `forget.py` `handle_forget_memory`, `confirm=false`. Search is first (line 1504, any distinctive term). Entity names that occur inside the description are appended (lines 1506–1515). `group_candidates` (lines 1225–1232) sets `ask_brian` when there is more than one group. The which-one message is chosen at lines 1544–1547. The unmapped sentence is appended only when `ask_brian` is false and `entities_matching` is empty (lines 1554–1556). The proactive cascade runs only on `confirm=true` after exactly one entity (lines 1631–1637).

The tool description was 12 characters. `P9` is length 2 and is dropped, leaving two terms. Search returned 10 rows (1 notebook fact, 8 episodes, 1 pending turn). One entity of kind `other`, name length 12, was also a match because that name occurs inside the description; it is not one of the two search terms. 11 candidates, 9 groups, so `ask_brian`, so the which-one message. The unmapped sentence was not reached. The cascade never ran.

Nothing was erased. No `fact_erase` and no `forget_cascade` since `14:19`. Three `sanitize_after_erase` lines (`14:20:00`, `14:29:33`, `14:31:08`) have `checkpoint_frames=0`; that call runs on every `confirm=false`, including a no-op. `MEMORY.md` is still 372 bytes, SHA-256 `6DC835B5FA5563CD609856F6C1EFB73E1DCE1F57008B6F592AD22E44619227AB`. `USER.md` is 2315 bytes, SHA-256 `27B375222430AF4E6D4D50A7205B6380A2B7058B799F068DB4CFD467676816D5`. Facts 20, episodes 20, entities 10, tombstones 36. There is no snapshot of episodes, entities, or `USER.md` from the minute before R2; the erase-log absence and the unchanged fact count and `MEMORY.md` hash are the evidence.

Hold. `held_count` is the number of normalized user texts in `hold_user_texts` (lines 1520–1542). The R2 set is that one turn. Those texts are `mark_drop`'d, so `pending_write` skips them. It does not block tools and it does not erase. It releases on the 30-minute wall (`FORGET_HOLD_MAX_MINUTES`, line 76), on the 4th later user turn (`HOLD_MAX_TURNS` is 3, lines 1794–1805), on a successful confirm, or when a new process sees the meta row with an empty candidate set (`expire_orphan_hold_on_restart`, lines 1733–1761). A new session does not inherit the in-memory hold. The same session's next turns are dropped from pending until the hold ends, so a later memory write of those turns can be skipped. Meta at record time: present, 75 bytes, session `20261013_142932_f40cb4`, `started_at` `2026-10-13T21:31:08Z`. No later turn in that session. The L6 harness below cleared that meta as an orphan and wrote the same bytes back.

Blocked `confirm=true`. Not the token, and not a new-ticket check. `pre_tool_call_hook` (`forget.py` lines 1925–1932) returns `block` when `ask_brian_pending` is set, before mint. Log: `2026-10-13 14:31:22,525 zola_memory.forget_guard action=blocked tool=forget_memory ok=false`. The flag was set on the same turn at line 1546. The next Brian turn clears it (lines 1787–1789) before a later confirm can mint.

Loop close. The nested call is `zola_loops` `action=close` with `loop_id` and an `intent` argument `cancelled`. `close_listed` (`loops.py` lines 285–294) uses `loop_id` only. The id's SHA-256/16 is `98aa1357d361770d`, the loop created `2026-10-13T17:31:18Z`. Its intent column is still `reply`. That is the typed loop for the approved test title, not the voice-echo loop. The Google loop (`3a97f2d83707e409`, created `2026-10-13T17:38:39Z`) was already closed in L3. The loop created `2026-10-13T20:02:27Z` (`7bba6d3c51083a6b`) stayed open. Nulling `sender_display_name` and `subject` is `_close_loop` (`proactive_store.py` lines 1269–1271). The forget cascade did not run.

Unmapped-reply test. `test_zero_hit_then_exactly_one_entity_counts` already asserts the unmapped sentence when nothing matches, and it does not insert a loop. `test_unmapped_subject_leaves_open_loop` was added: a forget whose subject resolves to no person, with an open loop present, returns `MSG_PROACTIVE_UNMAPPED`, and that loop stays `open` with its name and subject. Memory suite after the addition: 132 OK. The test file is not mirrored to the live profile.

L6, harness against the live databases, no Zola turn. Contacts lookup was not called: it refuses without a Brian turn, and this harness does not mint one. The checks the cascade actually uses were zero before the seed: entities named the token, aliases of the example.com address, entity names contained in the forget phrase, items with that address hash, items whose subject, snippet, or gist contain the token, and loops linked by that entity id or address hash.

Separate unmapped step, before the seed: search 0, entities 0, `ok=true`, groups 0, the unmapped sentence present (message length 86). Content counts did not change. `meta` went from 10 to 9 because `expire_orphan_hold_on_restart` cleared the R2 hold row in this process (empty candidate set). The original 75 bytes were written back at the end (`meta` 10 again).

Before the seed: entities 10, aliases 0, episodes 20, facts 20, tombstones 36, items 0, loops 3. After the seed: entities 11, aliases 1, items 1, loops still 3. The phrase resolved to that one entity. `confirm=false` listed one group and that entity id. `confirm=true` with only that id returned ok and the included-pending-list sentence. After the forget: entities 10, aliases 0, items 0, episodes 20, facts 20, tombstones 36, loops 3, and the loop id/status/name-length/subject-length list was unchanged. The synthetic entity and item are gone. `MEMORY.md` and `USER.md` hashes are the same as the before line above.

Stopped here. The MEMORY.md line-7 cleanup has not been started.

Hold and retrieve are confirmed from the code and the log. `pre_llm_call` sets the origin ContextVar on the timeout worker. `on_turn_start` and `prefetch` run on the turn thread after that worker returns, so the ContextVar is empty. Last `forget_hold` line is `2026-10-09 09:49`. Last retrieve with candidates is `2026-10-09 09:54`. After the `14:45` deploy, through `13:10` on `2026-10-13`, every retrieve is `candidates=0 returned=0 elapsed_ms=0`, every prefetch is `returned_len=0`, and there are no `forget_hold` lines. `pending_write` continues on those days. The turn thread can see a consumed ticket only by a non-consuming lookup of one unexpired sync permit whose text hash equals this message. Zero or several matches fail closed.

### Phase 6 FINDING — Hermes MEMORY.md (not part of P9-STORE; file not edited)

Path `C:\Users\test\AppData\Local\hermes\profiles\zola\memories\MEMORY.md`. 372 bytes. 7 lines. The line behind the P8 answer is line 7: `Remember the P8 smoke test is tomorrow at 3 PM.`

That line was written by Hermes's built-in `memory` tool, action `add`, target `memory`, on 2026-10-08 at 08:11, session `20261008_072029_bde806` (P8-CONNECT C4b). The first add was blocked; the second completed (47 characters, fact id prefix `d4b9c252`). The file's creation and last-write time are both 2026-10-08 14:53:34, which is the later `memory` remove in session `20261008_132442_33c4a0` (P8-READ C5c, `fact_erase` of a different entry, `Entry removed.`). That rewrite left this line in place. Live `agent.log` starts 2026-10-09 and does not contain either call.

`platform_toolsets.cli` includes `memory`. That name is Hermes's built-in toolset. `tools/memory_tool.py` registers tool `memory` on toolset `memory`. Target `memory` writes this file; target `user` writes `USER.md`. The module docstring says both files enter the system prompt as a frozen snapshot at session start.

`DESIGN_DECISIONS`: C4 says `MEMORY.md` and `USER.md` are the flat, prompt-injected fact store. P5-D10 says forget removes the entry from whichever of those files holds it, and does not redact `state.db`. P6-D01 says those files stay the authority for current durable facts, written by the memory tool only; `zola_memory` holds a structured fact index rebuildable from the files, plus episodes, and retrieval does not keep a second copy of current facts. P6-D03 is the `zola_memory` provider, with no model-facing tool except the later erase-only forget. P6-D06 extends forget through that provider; `state.db` is still not redacted.

### Post-L6 cleanup — stale MEMORY.md line (outside the L6 counts)

Brian ran this himself in a new session, `20261013_145725_98a8fe`. Turn 1 was `14:58:57` (prompt 63 characters). The later two turns in the same session were `15:01:15` and `15:02:08`.

Turn 1 tools, in order: `skill_view`, then the built-in `memory` tool `action=remove` `target=memory` (`old_text` length 47), then `forget_memory` `confirm=false` (description length 99, no target ids). `forget_memory` did not erase. It listed 7 candidates in 6 groups and set a hold. The spoken reply is 78 characters. The which-one payload (1,357 characters) was not that reply.

The erase is the memory-tool notification. `14:59:04` `forget_guard action=allowed tool=memory`. `forget_cascade reason=remove fact_rows=1 history_rows=0 fts_rows=4 episode_rows=3 pending_rows=0 link_rows=8 entity_rows=0`. `fact_erase fact_id=d4b9c252-5e07-4f10-91e6-bd9823915a40 reason=remove`. `sanitize_after_erase checkpoint_frames=0`. That path is `fact_index._notify_remove` (lines 198–236) calling `erase_fact` with reason `remove`. A unique text match does not run a full file rebuild. The next turn's `file_check` ran because the file hash changed and logged `added=0 erased=0`. There is no second confirm turn on this path. `forget_memory` `confirm=true` refuses a notebook fact and points at this tool (`forget.py` lines 1604–1614). That is the P6-D06 split.

`origin_token` minted and consumed at `14:59:07` on the `forget_memory` `confirm=false` call, after the erase.

The sentence is gone from `MEMORY.md` and from `facts`. Tombstone present, `record_kind=fact`, `erased_at=2026-10-13T21:59:04Z`. The fact row is gone. Episodes containing the sentence: 0. The cascade deleted 3 episodes (`episode_rows=3`); episodes 20 → 17. One `state.db` message still contains the sentence. Files are the fact authority (P6-D01), and `state.db` is not redacted (P5-D10), so the index will not restore the fact from that message. A later `memory` add could write it again.

`MEMORY.md` is now 319 bytes, 5 lines, SHA-256 `7D6A394EBCDF1F08F405A3F6D6C627F9A96AD5916CBA2A41A917127FB7BABB53`. The lines 1–6 baseline does not hold: that baseline was 6 lines and 318 bytes. The tool rewrote the file with CRLF and no trailing newline. `USER.md` is unchanged, SHA-256 `27B375222430AF4E6D4D50A7205B6380A2B7058B799F068DB4CFD467676816D5`. Counts now: facts 19 active (3 memory, 16 user; was 20), episodes 17, entities 10, tombstones 37 (was 36). The three memory-fact lengths are 234, 67, and 1. The length-1 fact is the section mark. Production `parse_entries`, after `read_text` translates CRLF to LF, returns those three entries, and they equal the active memory facts. A raw byte split on `\n§\n`, with the carriage returns left in place, is one 312-character piece. That raw split is not a parser this process uses. The `14:59:21` file check logged no drift because the translated parse matched the index. Later turns skipped because the stored hash matched. Grounding is under P9-FIX-MEMPARSE. The parser is not changed in this track.

Turn 3, `15:01:15`, prompt 19 characters. `zola_loops` `action=close` `intent=cancelled` with a `loop_id`, result 12 characters, then `action=list`. Open loops: 0. All three rows are `closed`. Each `intent` column is still `reply`. At this moment `close_listed` does not write the `intent` argument, and the live schema has no close-intent column. The column added after this review is recorded below. The loop created `2026-10-13T20:02:27Z` (`7bba6d3c51083a6b`) is closed, name and subject null.

Turn 4, `15:02:08`, prompt 28 characters. `contacts_lookup` `query` length 5, `max_results=10`. `agent.log` `2026-10-13 15:02:16,777` `tool contacts_lookup completed (0.47s, 692 chars)` in this session. The workspace log tail is `people.people.searchContacts` status 200, then `contacts_lookup state=complete count=2 more=false ms=469`. That is a Brian turn. It closes the L6 Contacts gap.

`origin_unresolved` since `14:19:43`: 0, across `agent.log`, `errors.log`, `gui.log`, `zola_memory.log`, `zola_workspace.log`, and `zola_tools.log`.

The hold meta row is now this session, `started_at` `2026-10-13T21:59:07Z`, from the turn-1 `confirm=false`. The R2 row the L6 harness restored is no longer the stored row.

### Findings recorded with the cleanup

The L6 harness called `handle_forget_memory` against the live database. `expire_orphan_hold_on_restart` cleared the live forget-hold meta row because that process had an empty candidate set, and the harness wrote the original bytes back afterward. Fixed below: a hold row that is already stored is skipped before either store is opened, and the harness does not write that row.

A closed loop did not store the close `intent`. The column stayed `reply`. The `cancelled` argument on this close was not written. Fixed below as schema version 2. The live file is still version 1 until a process loads the new module.

The chat panel shows the markdown markers as characters. The turn-4 reply is 44 characters and contains two `**` sequences. Cosmetic. Later phase.

## P9-STORE fixes after the cleanup review

Brian's verdicts, recorded here: the turn-1 erase is the P6 notebook path (built-in `memory` remove, cascade, tombstone; the `state.db` residue stays because forget is erase-only). The Contacts gap is closed. `origin_unresolved` since `14:19:43` is 0. The R2 self-initiated loop close is accepted. Ask-first is a Track 5 question.

### Close intent

`SCHEMA_VERSION` is 2. `_migrate` runs v1, then v2. `_migrate_v2` is `ALTER TABLE loops ADD COLUMN closed_intent TEXT` with a check for NULL or one of `reply`, `cancelled`, `status_change`, `confirm_close`, `expired`, `forgotten`. Existing rows are not backfilled.

`close_listed` writes the tool `intent` when it is one of the four tool intents, and NULL otherwise. The watch-type `intent` column is unchanged. `close_loop` rejects any other non-NULL value as `bad_args`. The purge sets `closed_intent='expired'` only on the open-to-expired update. Forget no longer deletes a matched loop. An open match becomes `status='closed'`, `closed_intent='forgotten'`, with name and subject NULL. An already-closed match is left alone, so a prior `cancelled` is not overwritten. `loops_deleted` counts only the open-to-closed rows.

Tests: each tool close path stores its intent; a v1 database migrates and both the closed and the open row stay NULL; forget of an open loop stores `forgotten` and does not replace `cancelled` on a second loop; the purge stores `expired` on the row it expires.

The live file was read with `mode=ro` after these edits. `schema_version` is still `1`. `closed_intent` is not a column. Open loops 0, closed loops 3. Nothing in this step called `connect()` on that file. The running serve still has the previous module loaded. The column appears when a process loads this module and opens the file.

### L6 harness

`l6_hold_guard.harness_hold_decision` returns `skip` when the hold value is non-empty, and `proceed` for None or `""`. `l6_live.py` reads that row through a read-only connection and returns before `open_store` or `proactive_store.connect` on `skip`. The cleanup path reads the row and records whether it is unchanged. It does not write it. The unit test inserts a foreign row, takes `skip`, and asserts the row is still there. The live script was not run.

### Dead ContextVar readers

`origin.end_turn` clears the thread flag and pops only the turn id it was passed. It does not call `current_turn_id()`. `forget.origin_allows` uses the passed id, then the approval context, then `thread_turn_is_client()`. It does not call `current_turn_id()`. `forget.client_origin_active` and `forget.current_origin_turn_id` are gone. `current_turn_id()` remains; the only caller is the test that expects it to be empty on a miss. `agent_loop_stopped_hook` still calls `end_turn` with whatever `turn_id` the hook received. The test that used to expect a binding drop from the ContextVar now expects the binding to stay when that hook is given no turn id. The thread flag still clears.

## P9-FIX-MEMPARSE — withdrawn

Production parse matches the index: MEMORY 3/3, USER 16/16. There is no P9-FIX-MEMPARSE hotfix. The measurement below is what closed it.

### A. Line endings

No `MEMORY.md` backup is in the profile. The memories directory contains `MEMORY.md`, `USER.md`, and the two lock files. `MEMORY.md` was rewritten at `2026-10-13T21:59:04Z` (319 bytes, 4 CRLF, no trailing newline). `USER.md` was last written at `2026-10-09T21:49:50Z` (2315 bytes, 30 CRLF, no trailing newline) and was not rewritten today, so the Windows writer was already emitting CRLF before today's remove.

Hermes writes through `MemoryStore._write_file` (`tools/memory_tool_store.py` line 422), which calls `atomic_write_text`. `_atomic_write` (`utils.py` line 237) opens the temp file with `os.fdopen(..., "w")` and does not pass `newline`. On Windows that translates `\n` to `os.linesep`. `os.linesep` on this machine is CRLF. `ENTRY_DELIMITER` is `\n§\n` (line 23), so a tool rewrite lands on disk as `\r\n§\r\n`. The 10-08 remove used this same function. There is no byte copy of the file from before today.

Hermes reads through `_read_raw_checked` (line 402): `Path.read_text(encoding="utf-8-sig")`, which also defaults to universal newlines, so CRLF is translated back to `\n` before `_parse_entries` (line 407). That split is the full `\n§\n`. A bare section mark is kept (the comment on line 408). `_render_block` (line 384) joins every parsed entry into the system-prompt block.

### B. Zola parsers

| Path | Newlines | Delimiter |
|---|---|---|
| `store.read_memory_file` | `read_text(encoding="utf-8-sig")`, universal newlines | none; returns the translated string |
| `store.parse_entries` | operates on that string | `\n§\n`, strip, drop empties |
| `store.combined_files_sha256` | hashes the translated strings | none |
| `fact_index._load_file_entry_set` | both files through the two functions above | same |
| `fact_index.run_file_check` | same, then set-compare | same; hash skip before the compare |
| `fact_index.handle_memory_write` / `_notify_add` / `_notify_replace` / `_notify_remove` | the tool's text, not a resplit of the raw file | exact text; an unmatched remove falls through to the file check |
| `fact_index._insert_file_check_fact` | one parsed entry | this is the rebuild; there is no other rebuild function |

`provider.system_prompt_block` returns `""`. `provider.prefetch` calls `retrieve_episodes` and does not parse the files.

Measured on the live files, counts and lengths only. Production parse of `MEMORY.md`: 3 entries, lengths 1, 67, 234, set-equal to the 3 active memory facts. Raw byte split of the same file on `\n§\n`: 1 entry, length 312. The 3 facts are the production parse. The 312-character piece is the raw split. The length-1 fact's text is the section mark.

That fact has one `facts_fts` row. An FTS `MATCH` of the quoted section mark returns 0. `distinctive_terms` and `derive_search_terms` both return no terms (length under 3). Episode retrieve and forget search will not use it. Hermes still puts it in the memory block, because `_render_block` includes every parsed entry.

### C. Drift

`run_file_check` loads the translated entries, then compares `combined_files_sha256` to `meta.files_sha256`. When they match and no pending erasure remains, it logs `ran=false skipped_hash_match=true` and does not add or erase. A `ran=true` check with `added=0 erased=0` means the translated set already equaled the active facts; the hash is then saved. That is what `14:59:21` recorded. The stored hash equals the current translated hash (`hash_matches_stored=true`), so a later check skips.

### D. USER.md

Same on-disk exposure: CRLF, and a raw `\n§\n` split is one entry of length 2286. The production parse is 16 entries, lengths 30, 45, 47, 48, 74, 78, 127, 133, 154, 167, 189, 194, 199, 219, 242, 265. That set equals the 16 active user facts. The file check hashes both files together, so an unchanged hash skips `USER.md` as well.

## No-ticket harness

Scratch database only. `pre_llm_call_hook` with no preceding `prompt.submit`, the same shape as P9-FIX-ARM H2, then `loops.loops_handler` `action=create` `intent=reply`. `is_brian_turn` was false. The handler returned `ok=false`, `refused_reason=origin`. The scratch `loops` table had 0 rows. That scratch file was created at schema version 2 by this module. The live file was not opened.

## Published client launch

`dotnet build windows-client\Zola.Client\Zola.Client.csproj -c Release`: 0 warnings, 0 errors. The Release exe is 156,672 bytes, written `2026-10-13T15:33:43-07:00`. It was started as pid 5760. It had no python child, so it did not spawn a second serve. A window handle appeared. `WM_CLOSE` was posted to that window only. The process exited. The Debug client pid 24732 is still the parent of `hermes_cli.main -p zola serve`. The Blender MCP processes and the p10 listen processes were still running afterward. `config.yaml` is unchanged, SHA-256 `0DD2F5635E438AAE6644FBA0B7502AE54C2AFF8837D599D3E2F8F6EA77FE1E26`.

## Suites

| Suite | Result |
|---|---|
| `zola_workspace` | 208 OK |
| `zola_memory` | 134 OK |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |

Workspace top is the tests directory. Memory and tools top is the plugin root. The venv is `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`.

## Exit table

Live mirror matches the repo for the four files copied at closeout. `proactive.db` is schema version 2. Scratch harness scripts stay beside the unapproved plugin backups until Brian accepts those backups.

| Criterion | Result |
|---|---|
| ST-G1–G8 answered; verdicts recorded | Met. Phase 3 verdicts are in this doc. Later verdicts: R1 accepted; R2 accepted, and ask-first is Track 5; L6 accepted; the turn-1 erase accepted; the R2 self-initiated close accepted. |
| Suites pass; two-process harness shows no lost update | Met. 208 / 134 / 44 / 8. The Phase 2 harness: one winner per row, the waiter stayed inside the timeout, a crash left the earlier commits and dropped the uncommitted insert. |
| L1–L6 live | L1 passed. Typed L1b asked which message and created none. L2 passed (both watches). L3 passed (one closed). L4 passed on the restructured check: a create only on the explicit yes. L5's corrected outcome holds: a topic is not an entity, the reply is unmapped, and the loop stays open; closing by topic is L3. L6 passed: the synthetic entity and item are gone, and the other counts were unchanged. |
| A synthetic no-ticket turn cannot create a loop | Met. `refused_reason=origin`, 0 rows, scratch database. |
| G-STATE-INDEPENDENCE and G-FORGET-ATOMICITY | Met in the store tests. The live purge earlier in Phase 6 changed nothing (all counts 0). It was not run again against the version-1 file. |
| Ambiguous references ask before creating | Met. Typed L1b, and the unit test. |
| Live forget touched only the synthetic identity | Met for L6. The later notebook remove was Brian's separate cleanup of the P8 line, through the memory tool. |
| G-ONE-OWNER source scan | Met. The suite includes it. |
| No model-typed id accepted | Met. Close requires a listed id. |
| Forget never claims completeness it did not achieve | Met. The unmapped reply is the L5 outcome. |
| No Hermes, client, or lore change | Met. Hermes was not edited. The client was built and launched, not changed. Lore was not edited. |
| No content in logs | Met for this track's new lines. The chat-panel `**` display is a later-phase cosmetic. |

## Lore closeout residuals

- A bare section-mark entry is in `MEMORY.md`. Hermes renders it in the memory block. Search ignores it.
- The lines 1–6 hash differs by line endings only. The content is equal.
- Ask-first before a self-selected loop close is Track 5.
- The chat panel shows literal `**`. Later phase.
- The L1 echo is `P9-FIX-ECHO`, after Track 2.

Schema version 2 is in the repo. The closeout restart below is what applies it to the live file.

## Closeout deploy (2026-10-13)

Four live plugin files differed from the repo. Each was copied to `C:\Users\test\Dev\zola-spikes\p9-store\plugin-backup\` with the suffix `-before-p9store-close` before the copy. Tests and `__pycache__` were not copied. `l6_hold_guard.py` is the harness guard and is not imported by the serve, so it was not mirrored. Every other plugin `.py` already matched. `config.yaml` is unchanged, SHA-256 `0DD2F5635E438AAE6644FBA0B7502AE54C2AFF8837D599D3E2F8F6EA77FE1E26`.

| SHA-256 before | SHA-256 after | Bytes | File |
|---|---|---:|---|
| `24E4F728BC028120AAC68253017F49107D11DB799A810386C4A20A5FCDA8A7C2` | `13784314633847D7453FBAE50A05A3B7A2394F5B6003F58C8D592156772610D9` | 13628 | `zola_workspace/loops.py` |
| `43F59BAD2E0312B7AA080CB1A772CC253B6A27B4414B9DBC4CAAAF35C650CE19` | `BB6AE6AC2C784E36EFB3809CB494A62ED69C049CFD0010BB077CEFD0FDF4C0C0` | 16193 | `zola_workspace/origin.py` |
| `70149A5D7E6E67CA974A9A5F4D36C33F443F1DCAAC1D4D638DF3E1D350CDE4D6` | `A167FBEE6C347D3C3280EF674B8A24567AF73E7EE2836B036F57F841F6C2E463` | 52494 | `zola_workspace/proactive_store.py` |
| `105DD4AAE953DBA6E7BE73E7B53D9C98F2D9F6F5745BE342A08BD01AD12D5535` | `D4ACC55DE895B1D3584B29078B8896A15BCC8D32736F93FD06697F6CDE3FE209` | 67028 | `zola_memory/forget.py` |

`WM_CLOSE` of Debug client 24732. Its serve children 2828 and 25860 exited with it. Blender MCP and the p10 listen processes stayed up. Release client 12548, parent 1780, is `bin\Release\net9.0-windows10.0.19041.0\Zola.Client.exe`. Serve shim 32352, parent 12548. CPython 36256, parent 32352, is `hermes_cli.main -p zola serve`. `agent.log` `2026-10-13 15:39:43,892` `origin wrap installed method=prompt.submit`.

Live `proactive.db` after that start: schema version 2, `closed_intent` present, 3 closed rows with `closed_intent` NULL, 0 open, `PRAGMA integrity_check` = `ok`. `origin_unresolved` since `15:39:43` across the six logs: 0.

Short live check passed. Session `20261013_153944_65d504`. `zola_loops` completed at `16:03:14` (573 characters) and at `16:03:46` (12 characters). The new row, created `2026-10-13T23:03:14Z`, SHA-256/16 `925055ec8a833290`, is `closed`. Its watch `intent` is still `reply`. `closed_intent` is `cancelled`. Name and subject are null. The three older closed rows still have `closed_intent` NULL. Open loops 0. Schema version 2. `integrity_check` is `ok`. `origin_unresolved` since `15:39:43` across the six logs: 0.

Plugin backups with the suffix `-before-p9store-close` stay until Brian accepts them.

## Phase 1 hashes (2026-10-13)

Live `config.yaml`: `C:\Users\test\AppData\Local\hermes\profiles\zola\config.yaml`
SHA-256 `0DD2F5635E438AAE6644FBA0B7502AE54C2AFF8837D599D3E2F8F6EA77FE1E26` (4,629 bytes). Contents were not copied here.

`proactive.db`: none under `C:\Users\test\AppData\Local\hermes\profiles\zola` (recursive search, 0 files).

Live `plugins/zola_workspace/` source files. `__pycache__` holds 17 `.pyc` files and is not listed. No `tests/` directory in the live mirror.

| SHA-256 | Bytes | File |
|---|---:|---|
| `90081583CB0570EDCA2BF7D7076597C13DE81669EE494723B19D668154D9B2E1` | 6440 | `__init__.py` |
| `A8AA8810FC9DF899788273181C8199645E2BAAD3D35A0C1ADAE318F4423E7667` | 25186 | `auth.py` |
| `E34343C96CCF8CDAF4FFB91C498CC6FEFFDF5020554D092A5F567831CDB3C3DE` | 5664 | `contacts.py` |
| `2EF13563A57DCD6F30F72D3CF4122C54DF74BF104C37EBD082476065D947CC66` | 18271 | `drive.py` |
| `0E91FFC883D42DE7AC143B01D2CDBFD822B1EA34B40355D32E9924C10E3B515A` | 1552 | `framing.py` |
| `6F17605A69B606946DC9C8ADC50EEB84282E212AABCA2E1EF57778EB7BCDD3BA` | 25205 | `gcal.py` |
| `DD018F6AE1D220F9D5B3EE10D60874784E556E1EB46D4F7CD3B4079214D3E7A7` | 40053 | `gmail.py` |
| `81281017D1A93DE26936DC660D2A9E9F7F1DF53411175B95F9136B9F92765B82` | 9189 | `google_http.py` |
| `29113CEF52D200B26FBB2938ABAFAB5292A1BD806C4B65C9FE9ADA0FAC7CDE06` | 32725 | `guards.py` |
| `CE00D6FB46FFEAB36E2A212E05BB68FC7ED6CB9292D30E8380355429D2976650` | 2780 | `log.py` |
| `4581898A844C75BD30C8778A3B3611429D0381D3834E4EFCEC449BCF0D7F4DB1` | 15611 | `origin.py` |
| `4E485461744F49222E1DD7EA378ADB899B2E3C064B4DCFF72F79027C96B7D738` | 199 | `plugin.yaml` |
| `E55D8E8253C5C8867C356C20A96716949DCFA22D5E5C2C9391D07219C292CDA9` | 2702 | `posture.py` |
| `B37CF4A91E7A211CFBC1865AC925658B28D26BD95A4B98908C4C6F926FB3F562` | 7051 | `read_common.py` |
| `2E601E2358AF51C0C17B867E1C74B128868F534D310359702D484D9B36CB9696` | 27940 | `send_gate.py` |
| `1FFEAAC4DE12A47286ACB2B2C9780D9C9B4E86B151802575ACAFBCC0712D3696` | 1356 | `setup.py` |
| `6390F091CA3A1ACE957BE7D18A80F1F926EC486FBF81025AC24B016D76CC344E` | 8520 | `taint.py` |
| `E5983EBC83858C69C0F53D473DA63A78C15739CF4226453E24EF1C28928DBE64` | 6217 | `textclean.py` |
| `84B0E58E58EE0A6913F1A9A150115E8C291FF4D339B8BF1EA973BD65ACC1AFAF` | 6619 | `turn_context.py` |

Live `plugins/zola_memory/` source files. `__pycache__` holds 12 `.pyc` files and is not listed. No `plugin.yaml` and no `tests/` directory in the live mirror.

| SHA-256 | Bytes | File |
|---|---:|---|
| `7FAA42BC030B329EB5F078B80EC45183104105361A29E880EAC3CCCCF9994C11` | 2418 | `__init__.py` |
| `F7B886C35B5817E74C1F92021D5837123F65B0177354D4D36B6B0C441903B992` | 41896 | `consolidate.py` |
| `AA0CCE9E599BA94F933A8619E2094D3A21192BD4AA785510A9D28FBC53D81B02` | 16281 | `fact_index.py` |
| `D0717731AEAA7D45C0A38535503CAF488AB53C7D9E317B5E24E193CB6E40E891` | 53049 | `forget.py` |
| `EC5A8F319628CB24DEEB0177397D34B754A51B30F80C025D4F93D5E5189FEC57` | 379 | `llm_access.py` |
| `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` | 4319 | `log.py` |
| `9FF6156CD946C08BFD737EDFFC15C6DAE2D865AB0C34ED332F48056DDA854769` | 8151 | `pending.py` |
| `12AA675E8B693BADA15160FB251F128ADF7C144F2A6A3C75212F82DD3FA9AC83` | 13893 | `provider.py` |
| `86AA4DA04D67AB911D569AB1D9774A86E1A36F75F9B1931D49CA3F0272EE771D` | 1432 | `registry.py` |
| `84E0C44975579C0B6878E64355ADAB4D30B09EE9938E61E9855A6774CC11FA39` | 13648 | `retrieve.py` |
| `C471EA121F993BD00D5E68EEF0DEFB92FBDD3D606774CA78B89ADF1B34CB00E8` | 17563 | `store.py` |
| `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` | 11425 | `time_context.py` |

## SHAs

- Implementation: `b13989a8f96c713214cb5537e24a401a02526bff` (`feat(P9-STORE): proactive store, lifecycle, retention, open loops, forget cascade — P9-D06/D07/D09`)
- Implementation-SHA commit: `f8a8d62add62b0194e2867f039857d27f8f58525`
- Merge `--no-ff`: `7e5ea69791173822ff7cba1ea5fcfecd979ebed2` (`Merge branch 'p9-store'`)

