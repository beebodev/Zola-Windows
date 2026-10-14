# P9-WATCH Progress — The watcher

## Branch

- Work branch: `p9-watch` (created from `main`)
- Base `main`: `0bec3b7b8fa1d163e5ed947ef3589058d9aef178`
- Implementation commit: `27b56b59d8be5295501177914b22330bc0189aec`
- Merge commit on `main`: `05ac85f5a9634be80726cb883e94476f60e74997`
- Hermes (read-only): clean at `345cd2b057a452236de401d3534b8502a7465e8d`
- Prompt file: `C:\Users\test\Dev\zola-spikes\prompts\P9-WATCH_Prompt_v1.1.md`
  SHA-256 `D5D31C0D26E9B43009D9D917655C7013362366C130F26C96A75F3800F1376B8C` (55,422 bytes)
- This Phase 1 message contained the prompt body and no separate comparison digest. The SHA above is the canonical file, hashed 2026-10-13.
- Scratch: `C:\Users\test\Dev\zola-spikes\p9-watch\` deleted at closeout (2026-10-14), including the `-before-p9watch` plugin backups. The `p9-store\plugin-backup` folder was already gone (verdict 18).

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and setup | COMPLETE |
| 2 | Read and understand | COMPLETE |
| 3 | Proposal | COMPLETE |
| 4 | Build | COMPLETE |
| 5 | Review checkpoint | COMPLETE |
| 6 | Deploy and smoke | COMPLETE |
| 7 | Closeout | COMPLETE |

## Guardrails (summary)

- G-SCOPE: `background_read.py`, `watcher.py`, the refresh lock in `auth.py`, approved `proactive_store` additions, client launch and a watcher supervisor on `RestartPolicy`, this progress doc, the live plugin mirror, any approved `config.yaml` line. No ranking, surfacing, speech, Gmail push, Calendar channels, mailbox actions, Calendar writes, Drive, or Contacts calls from the watcher.
- G-ARCH: the build plan and Appendix A are truth. Two known conflicts are Phase 3 decisions: sender resolution versus P9-D04, and Calendar baseline versus the store.
- G-PATTERN: read every relevant file in full before changing it.
- G-NOCHANGE: no Hermes edits; no `SOUL.md`, identity, lore, or build-plan edits; no installs; no token-store format or location change; no change to existing tool behavior except the shared refresh lock.
- G-FIXED-API / G-RUNTIME-AUTHORITY: a fixed operation list, plus an allowlist at the request boundary before any HTTP call. The source scan is a check, not the boundary.
- G-NO-TURN: no model, no Hermes agent, tool, gateway, or plugin-loader import, no client socket, no `prompt.submit`, no origin ticket.
- G-ONE-OWNER: every `proactive.db` write goes through `proactive_store`. Cursor and health functions do not exist yet; Phase 2 specifies them.
- G-ITEMS-BEFORE-CURSOR / G-CURSOR-COMPLETE / G-POISON / G-NO-FALSE-NEW: an item is committed before its cursor advances; unfinished work holds the cursor or becomes a durable terminal record; first run and recovery re-baseline.
- G-TOKEN: one inter-process lock around the token POST. A lock timeout, cache miss, store error, or network failure never sets `needs_reconnect`. The token store is never backed up, copied, printed, or logged.
- G-UNTRUSTED / G-PRIVACY: mail and calendar content is stored, not interpreted. No subject, snippet, body, address, display name, event title, or token in logs, tests, commits, or this doc.
- G-LOUD: every refusal, stop, or skipped cycle writes a WARN with a named reason.
- G-GENERATION / G-DELIBERATE: the watcher supervisor has its own generation and counters. A deliberate stop does not consume a restart.
- G-LIVE / G-ECHO-HYGIENE: live steps one at a time. Cursor never injects turns. Before and after each human step, report `echo_suspect` and `origin_unresolved` (expected 0).
- G-NO-CROSS-SCOPE: no Phase 10 documents, and no stop, kill, or restart of a P10 process.
- G-STOP / G-CLOSEOUT / G-LORE-SCOPE: stop after every phase. Closeout only on "proceed to closeout". No lore edits.

## Known conflicts (not start discrepancies)

1. Sender resolution versus P9-D04. Forget-by-person reaches a proactive row through a stored entity id, an address hash, or a source id. P9-D04 forbids Contacts calls from the watcher. Phase 2 lays out the options. Brian decides at Phase 3.
2. Calendar baseline versus the store. First sync should be known and never "new". The store has no baseline flag, and the Calendar idempotency key is `calendar:<event id>:<updated>`. Phase 2 proposes a model. Any schema change is a v3 migration and needs Brian's approval.
3. The build plan names `ProcessSupervisor` for the watcher. P9-SUPERVISE accepted the deviation: reuse `RestartPolicy`, not `ProcessSupervisor`.

## Discrepancies

None at start. `main` was clean and equal to `origin/main` at the pinned SHA. Hermes was clean at the pin. Live `proactive.db` is schema version 2, `integrity_check` ok, 0 open loops. `cursors` and `watcher_health` are empty. `desktop.auto_continue.enabled` is false. The Release client is the serve parent.

## Live baseline (2026-10-13)

`config.yaml`: SHA-256 `0DD2F5635E438AAE6644FBA0B7502AE54C2AFF8837D599D3E2F8F6EA77FE1E26` (4,629 bytes). Contents were not copied here. `desktop.auto_continue.enabled` is false.

`proactive.db`: schema version 2. `PRAGMA integrity_check` = `ok`.

| Table | Rows |
|---|---:|
| `cursors` | 0 |
| `deliveries` | 0 |
| `item_attempts` | 0 |
| `items` | 0 |
| `loops` | 4 (all `closed`; 0 open) |
| `meta` | 1 |
| `watcher_health` | 0 |

Live `plugins/zola_workspace/` files. `__pycache__` is not listed.

| SHA-256 | Bytes | File |
|---|---:|---|
| `67642E14509F5B009EFE227D9B1157FE37D7C07CD964A922181C2A9EB7BBB652` | 7150 | `__init__.py` |
| `A8AA8810FC9DF899788273181C8199645E2BAAD3D35A0C1ADAE318F4423E7667` | 25186 | `auth.py` |
| `A8B29E55185DCCFA404E0EE8CF9E06E84C7334E599AF92F720A5CB8A436E9AC4` | 6351 | `contacts.py` |
| `2EF13563A57DCD6F30F72D3CF4122C54DF74BF104C37EBD082476065D947CC66` | 18271 | `drive.py` |
| `0E91FFC883D42DE7AC143B01D2CDBFD822B1EA34B40355D32E9924C10E3B515A` | 1552 | `framing.py` |
| `B031E31EB1D9391B1B5E7873571C7F8CDB8401C4DA4E6D48B14D46372C90ED1D` | 26330 | `gcal.py` |
| `B30BC3D7376E74E221697075E1B2AF7309E2642FA15E02C512944B5DBCDD1D79` | 41669 | `gmail.py` |
| `81281017D1A93DE26936DC660D2A9E9F7F1DF53411175B95F9136B9F92765B82` | 9189 | `google_http.py` |
| `29113CEF52D200B26FBB2938ABAFAB5292A1BD806C4B65C9FE9ADA0FAC7CDE06` | 32725 | `guards.py` |
| `33D49FAE7E9CF472668692396E430B6A2CAFBF11165FFD602E923378F279D891` | 2924 | `log.py` |
| `13784314633847D7453FBAE50A05A3B7A2394F5B6003F58C8D592156772610D9` | 13628 | `loops.py` |
| `BB6AE6AC2C784E36EFB3809CB494A62ED69C049CFD0010BB077CEFD0FDF4C0C0` | 16193 | `origin.py` |
| `4E485461744F49222E1DD7EA378ADB899B2E3C064B4DCFF72F79027C96B7D738` | 199 | `plugin.yaml` |
| `E55D8E8253C5C8867C356C20A96716949DCFA22D5E5C2C9391D07219C292CDA9` | 2702 | `posture.py` |
| `A167FBEE6C347D3C3280EF674B8A24567AF73E7EE2836B036F57F841F6C2E463` | 52494 | `proactive_store.py` |
| `B37CF4A91E7A211CFBC1865AC925658B28D26BD95A4B98908C4C6F926FB3F562` | 7051 | `read_common.py` |
| `6B3F60CC0380C7D06EB1CB0C2F6EDDB0B1F7BA8852C1B22BB2187420A245A07C` | 4881 | `recorded_results.py` |
| `2E601E2358AF51C0C17B867E1C74B128868F534D310359702D484D9B36CB9696` | 27940 | `send_gate.py` |
| `1FFEAAC4DE12A47286ACB2B2C9780D9C9B4E86B151802575ACAFBCC0712D3696` | 1356 | `setup.py` |
| `6390F091CA3A1ACE957BE7D18A80F1F926EC486FBF81025AC24B016D76CC344E` | 8520 | `taint.py` |
| `E5983EBC83858C69C0F53D473DA63A78C15739CF4226453E24EF1C28928DBE64` | 6217 | `textclean.py` |
| `6BD9E082276A88AC17EA7B370F8A415902D174E2E17D17B4064A0820EB4D5D3C` | 7967 | `turn_context.py` |

## Processes (left running)

| PID | Parent | Start | What |
|---|---:|---|---|
| 12548 | 1780 | 2026-10-13 15:39:40 | Release `Zola.Client.exe` |
| 32352 | 12548 | 2026-10-13 15:39:41 | serve shim, `hermes_cli.main -p zola serve` |
| 36256 | 32352 | 2026-10-13 15:39:41 | serve CPython, same command |
| 2884 | 13420 | 2026-10-13 08:19:17 | P10 `phase4_listen.py` |
| 2696 | 2884 | 2026-10-13 08:19:17 | P10 `phase4_listen.py` child |
| 36292 | 2696 | 2026-10-13 08:19:17 | P10 `server.py` |
| 10092 | 36292 | 2026-10-13 08:19:17 | P10 `server.py` child |

Blender MCP processes were also up (parents 25444, 22260, 15948, started 2026-10-12 17:39 and 2026-10-13 09:30). They are not this track. No watcher process exists.

## Suites and checks (baseline)

| Suite | Result |
|---|---|
| `zola_workspace` | 208 OK |
| `zola_memory` | 134 OK |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |
| `Zola.Client.Checks` | exit 0; supervision 31/31; coverage line all matched (lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8) |

Workspace top is the tests directory. Memory, tools, and tts top is the plugin root. The venv is `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`. Checks: `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj`.

## P9-STORE backups

Phase 1 left the folder in place. Verdict 18 deleted the whole folder. It is gone. The listing below is what Phase 1 found.

| Bytes | File |
|---:|---|
| 68188 | `zola_memory__forget-before-p9store-close.py` |
| 53049 | `zola_memory__forget.py` |
| 62240 | `zola_memory__forget.py-before-origin-token` |
| 4319 | `zola_memory__log.py-before-origin-token` |
| 13893 | `zola_memory__provider.py-before-origin-token` |
| 13648 | `zola_memory__retrieve.py-before-origin-token` |
| 5664 | `zola_workspace__contacts.py` |
| 25205 | `zola_workspace__gcal.py` |
| 40053 | `zola_workspace__gmail.py` |
| 2780 | `zola_workspace__log.py` |
| 13502 | `zola_workspace__loops-before-60.py` |
| 13495 | `zola_workspace__loops-before-p9store-close.py` |
| 13048 | `zola_workspace__loops.py` |
| 16203 | `zola_workspace__origin-before-p9store-close.py` |
| 15611 | `zola_workspace__origin.py-before-origin-token` |
| 50942 | `zola_workspace__proactive_store-before-p9store-close.py` |
| 6619 | `zola_workspace__turn_context.py-before-origin-token` |
| 6440 | `zola_workspace____init__.py` |

## Phase 2 — Read and understand (2026-10-13)

No plugin or client source was modified. Scratch only: `C:\Users\test\Dev\zola-spikes\p9-watch\hw1_run.py`. The `-before-p9store-close` backups are still on disk. Deletion was not confirmed, so it stays a Phase 3 decision.

### Fixed operation list

Background reads, and nothing else:

| Source | Call | Allowed query |
|---|---|---|
| Gmail | `users.getProfile` (`userId=me`) | none; keep `historyId` only |
| Gmail | `users.history.list` | `startHistoryId`, `historyTypes=messageAdded`, `labelId=INBOX`, `pageToken`, `maxResults` |
| Gmail | `users.messages.get` | `format=full`, `fields` limited to id, threadId, labelIds, snippet, payload, internalDate |
| Gmail recovery | `users.messages.list` | a bounded page (`maxResults`, a short `q`); only after history 404 |
| Calendar | `calendarList.list` | id only, to learn calendar ids |
| Calendar | `events.list` | `maxResults`, `pageToken`, `showDeleted=true`; `syncToken` only after a finished full sync |

No `q`, `timeMin`, `timeMax`, `orderBy`, or `singleEvents` on the watcher calendar call. No Drive, Contacts, drafts, or sends. Body text goes through `extract_body` (`gmail.py` 233) and `textclean.prepare_body` (`textclean.py` 190, cap `BODY_CHAR_CAP = 4000` at line 10). The watcher does not call `gmail.py` or `gcal.py` handlers. Those handlers call `read_common.authorize`, which refuses unless `is_brian_turn` (`read_common.py` 109–124).

### WT-G1 — background read and the allowlist

`google_http.request` (`google_http.py` 170) is the only HTTP entry. It logs the route label and retries 429/500/502/503/504. It does not check route, path, or parameters. Routes today are lines 17–32. There is no `users.history.list` route and no `users.getProfile` route. Add `gmail.users.getProfile` and `gmail.users.history.list`. Keep `gmail.users.messages.get`, `gmail.users.messages.list`, `calendar.events.list`, and `calendar.calendarList.list`.

The runtime allowlist belongs inside `google_http.request`, before the transport call. A background capability argument defaults to absent. Tool calls omit it and keep today's behavior. `background_read` is the only production caller that passes the capability. With the capability set, an off-list route, path shape, parameter, or `fields` value raises before HTTP. The source scan walks `watcher.py` and `background_read.py` and fails if they import `gmail`, `gcal`, `contacts`, `drive`, `framing`, `guards`, `send_gate`, or a Hermes agent, gateway, or tool module. The scan is a test. The allowlist is the boundary.

### WT-G2 — refresh lock

`_access_lock` (`auth.py` 83) is a `threading.Lock` around the in-process cache only (657–664 and 718–720). The token POST at `_token_post` (430) runs outside that lock. The cache is per process. `refresh_access_token` (644) does not call `save_token_record` (238). A `refresh_token` in the response is ignored. The access token is stored only in process memory. `save_token_record` already writes with `_atomic_write_bytes` (231, used at 251).

What the in-process lock protects: two threads in one process sharing one cached access token. What it does not protect: two processes POSTing the same refresh token.

Proposal: a Windows named mutex `Local\ZolaOAuthRefresh`, stdlib `ctypes` only, around the POST. Timeout `REFRESH_LOCK_TIMEOUT_SECONDS = 45` because the HTTP timeout is 30 seconds (`google_http.py` 10). `WAIT_ABANDONED` means the holder died; the waiter proceeds and re-reads the DPAPI record before it POSTs. A timeout raises a transient error and does not call `set_reconnect_reason`. `needs_reconnect` stays limited to a real token-endpoint failure: HTTP 400/401 (691–693) or body `error == invalid_grant` (696–699), plus the existing `sub_mismatch` path (710). Per-process access tokens are acceptable. Do not persist them. If a response includes a new refresh token, persist it with the existing atomic replace or leave the file unchanged. That persistence is a Phase 3 yes/no. The default proposal is to keep ignoring a rotated refresh token, matching today's code.

### WT-G3 — process

Entry: the Hermes venv `python.exe -m zola_workspace.watcher`. `HERMES_HOME` is the zola profile. `PYTHONPATH` includes the live `plugins` directory so `zola_workspace` imports from the mirror, plus the hermes root the way `PrependPythonPath` does for serve (`HermesProcessManager.cs` 560–567). Do not set `HERMES_DASHBOARD_SESSION_TOKEN`. The command line contains `zola_workspace.watcher` and does not contain `hermes_cli.main`.

A second named mutex `Local\ZolaWatcher` is the single instance. The second launch logs `already_running` and exits 2. Clean shutdown: the client sets the deliberate flag, signals `Local\ZolaWatcherStop`, and the process exits 0. Log file: profile `logs/zola_watcher.log`, metadata only, same style as `log.py` (`LOG_FILENAME` at line 10 is the tool log and is not the watcher log). Stderr is captured by the client beside that file. The watcher does not import the tool handlers, `origin`, `prompt.submit`, the gateway, or the client socket. `loops.py` may be imported for `evaluate` (188–190). That module also imports `turn_context` because `_session` (193) is the tool path. `evaluate` itself does not use it.

Do not start the watcher from `register` (`__init__.py` 116). That function installs the origin wrap (176) and the purge thread (183) inside serve. A watcher started there dies with serve and fails W5.

### WT-G4 — commit order

For one Gmail history page or one Calendar page:

1. Insert or upsert each item (`insert_item`, 341). Each insert commits on its own (435–436). Idempotency: `gmail:<message id>` or, today, `calendar:<event id>:<updated>` (387–392). A duplicate returns `created=False` (437–445). New rows start `entity_resolution=unresolved`, `processing=unranked`, `eligibility=pending` (413–414).
2. Sender resolution: no write under the recommended option in WT-G8.
3. `loops.evaluate` for each new or updated item against each open loop.
4. On a real match, `note_loop_match_on_loop` then `mark_loop_eligible`.
5. Cursor write, only after every id on the page is an item or a terminal poison record.
6. Health write, after the cycle, in its own transaction.

Items, the match, the cursor, and health do not share a transaction. A later failure must not roll back an item that already committed.

Replay: crash after step 1 and the item is already there; the retry gets `created=False` and continues. Crash before step 5 and the cursor is unchanged, so the page runs again. A second `mark_loop_eligible` hits `eligibility = 'pending'` (730) and returns `illegal_transition` (735–737). The caller treats that as already matched and still advances once the page is complete. `note_loop_match_on_loop` rewrites `matched_at` whenever the loop is still open (1265–1267). Recommend `AND matched_at IS NULL` so a replay is a no-op success. That is a Phase 3 store change.

Partial failure (G-CURSOR-COMPLETE): one `messages.get` failing inside a history page holds the cursor. Already inserted siblings replay as `created=False`. A failed later page holds the cursor the same way. A loop-evaluation error after the item is committed holds the cursor; the item stays.

Poison (G-POISON): a 404 on `messages.get` for an id history already returned is terminal (deleted before fetch). Network errors, 429, 5xx, and `locked` are transient. Propose `POISON_ATTEMPT_CAP = 5`, then a terminal record, then the cursor may advance past that id. Propose a v3 table `watcher_rejects` (`source`, `source_id_hash`, `error_class`, `disposition`, `attempts`, `first_seen`, `last_seen`). No subject, snippet, body, or address. Brian decides the cap and whether this is a new table or columns on an existing one.

### WT-G4a — Google rules

Read 2026-10-13.

- [EXT] https://developers.google.com/workspace/gmail/api/reference/rest/v1/users/getProfile — `historyId` is the mailbox's current history record. Also returns `emailAddress`, `messagesTotal`, `threadsTotal`. The watcher stores `historyId` only.
- [EXT] https://developers.google.com/workspace/gmail/api/guides/sync — first full sync in the guide is `messages.list` plus `messages.get`, then the `historyId` of the newest message. P9-D04 does not take that path: existing mail is not ingested. Partial sync uses `history.list` with `startHistoryId`. History is typically kept at least a week and can be only a few hours. An out-of-range id is HTTP 404, and the client must full-sync. Our 404 recovery is a bounded `messages.list`, not the guide's unbounded recent-mail cache. Only ids not already stored become candidates. The recovery is recorded on the health row. After those candidates are durable, `getProfile` supplies the new `historyId`.
- [EXT] https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list — `startHistoryId` is required and returns records after that id. History ids increase with gaps. `labelId` keeps messages with that label. `historyTypes` includes `messageAdded`. The generic `messages` list usually has only `id` and `threadId`; use `messagesAdded`. If there is no `nextPageToken`, store the returned `historyId`. A crash mid-page does not store it, so the next poll repeats the same `startHistoryId`. `labelId=INBOX` is what keeps a sent reply out: sent mail is not in INBOX. No second from-me filter.
- [EXT] https://developers.google.com/workspace/calendar/api/v3/reference/events/list — `syncToken` cannot be combined with `iCalUID`, `orderBy`, `privateExtendedProperty`, `q`, `sharedExtendedProperty`, `timeMin`, `timeMax`, or `updatedMin`. Other parameters should match the initial sync. Deleted events are always in an incremental result, and `showDeleted=false` is not allowed with `syncToken`. `nextSyncToken` is omitted while `nextPageToken` is present. An expired token is 410; clear storage and full-sync with no `syncToken`. `singleEvents` is not in the forbidden list. `showDeleted` and `singleEvents` both false still return cancelled instances of a recurring event, not the underlying series, as cancelled.
- [EXT] https://developers.google.com/workspace/calendar/api/guides/sync — store `nextSyncToken` from the last page only. 410 clears the client store and runs a new full sync.
- [EXT] https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html — a cancelled exception is only guaranteed to have `id`, `recurringEventId`, and `originalStartTime`. `status=cancelled` is also how a deleted single event appears on an incremental sync.

The tool path cannot be reused for this. `_list_events_for_calendar` sends `singleEvents`, `orderBy`, `timeMin`, `timeMax`, and optional `q` (`gcal.py` 347–355). Those conflict with `syncToken`. `_shape_event` sets `descriptions_included` false (253) on the tool result; a raw list still contains `description` unless `fields` drops it. The watcher `fields` mask omits `description`.

Calendar 410 clears that calendar's cursor and full-syncs again. Those rows are baseline, not new.

### WT-G4b — calendar model

Recommend (b): one `items` row per event id, a `baseline` column, and upsert. Live `items` is 0, so a v3 change of the calendar idempotency key from `calendar:<event id>:<updated>` to `calendar:<event id>` does not rewrite rows. An update changes `event_updated`, `calendar_status`, and times on that row. First-sync rows have `baseline=1`. The ranker (Track 4) ignores `baseline=1`. A later first-seen event has `baseline=0`.

(a) a separate `calendar_events` table splits "known" from "item", and forget plus loop matching would walk two tables. (c) is not needed.

Recurring events, with `singleEvents` omitted on both the full sync and the incremental sync:

- The series is one row, keyed by its event id.
- A modified instance is another row: its own id, plus `recurring_event_id` and `original_start`.
- A cancelled instance updates that row to `calendar_status=cancelled` (or inserts it once, if this is the first time that instance has been seen). It is not a second row and it is not a new event for ranking.
- `singleEvents=true` is allowed beside a sync token by the parameter list above, but `timeMin` / `timeMax` / `orderBy` are not, and an open-ended series expanded with no `timeMax` is unbounded. Both passes omit `singleEvents`.
- `showDeleted=true` on the full sync so the parameter matches the incremental call, which always returns deletions.

Stable key is the event `id`. `recurringEventId` and `originalStartTime` are stored columns, not a second idempotency key. A loop on "that meeting" binds the event id the calendar tool returned. That tool expands instances (`gcal.py` 348), so the id is an instance id. The watcher sees that id when the instance becomes an exception. Recommend also matching a cancelled row whose `recurring_event_id` equals the loop's event id, so a deleted series closes an instance loop. Brian decides that extra match.

Phase 4 tests: series insert is baseline; modified instance is one extra row; cancelled instance updates status and does not insert again; incremental delete shape; `singleEvents` absent when `syncToken` is set; no `timeMin` / `timeMax` / `orderBy` / `q`; a loop on an instance id matches the cancelled exception; a second sync of the same id does not add a row.

### WT-G5 — constants

- `GMAIL_POLL_SECONDS = 120`
- `CALENDAR_POLL_SECONDS = 7200`
- Both poll once at process start, then on their intervals.
- Clock jump: compare wall-clock delta to `time.monotonic()` delta. H-5 flagged a gap above 2 seconds. Propose `CLOCK_JUMP_SECONDS = 15` so a slow poll does not double-fire and a real sleep still does. On a jump, catch up immediately.
- Per-source backoff after errors, cap `ERROR_BACKOFF_CAP_SECONDS = 600`.
- `needs_reconnect` stops both sources, because they share one token. Health records the reason. Polling resumes after setup clears it (`clear_reconnect_reason` on a successful refresh, 721).
- `proactive.db` `locked` skips the cycle, logs WARN `db_locked`, and retries next interval. `connect` uses a 5000 ms busy timeout (135–137). The cursor does not move.

### WT-G6 — loop matching

Evaluation runs in the watcher, after the item commit and before the cursor write. `evaluate` is pure and does not close (`loops.py` 188–190). The watcher has no ticket, and serve may be down (W5), so this cannot wait for a tool turn.

On a match: `note_loop_match_on_loop` (1255) sets `matched_at` and leaves `status=open`. `mark_loop_eligible` (704) sets `eligibility=eligible` and `loop_matched=1` only from `pending`. Matched is not closed (P9-D09).

Terminal calendar predicates: `calendar_cancelled` (178–179) and `calendar_status_differs` (180–182) are the predicates ST-G6 says can close. `close_loop` refuses without a ticket (`proactive_store.py` 1298). Propose `close_loop_from_match(loop_id, closed_intent)` with no ticket check, allowed intents only `cancelled` and `status_change`, and only from `status=open`. The tool path keeps `close_loop`. Brian decides. The other option is to record the match and leave the close to Track 5.

Replay does not double-match: the second eligibility update is `illegal_transition`, and the recommended `matched_at IS NULL` guard makes the loop stamp a no-op.

### WT-G7 — client

Start the watcher from `App.OnLaunched` (`App.xaml.cs` 17–26) on its own, not after serve is healthy and not as a child of serve. W5 requires polling while serve is dead. The window `Closed` handler already calls `_backend.Shutdown()` (24). It should set the watcher deliberate flag and signal stop in that same handler.

Supervisor: a new type that owns a `RestartPolicy` and its own generation. Not `ProcessSupervisor` (`ProcessSupervisor.cs` 6), which is built around `HermesProcessManager` and the chat socket. Same numbers unless Phase 3 changes them: `RestartLimit = 3` and `RestartWindowMinutes = 10` (`SupervisionConstants.cs` 6–7). `NoteRestartAttempt` returns `IgnoredDeliberate` when the flag is set (89–92) and `Terminal` past the limit (101–104).

Kill rule: command line contains `zola_workspace.watcher`, and the generation matches. Never match `phase4_listen.py`, `server.py`, or Blender. Log with `SupervisionLog.Format` (`SupervisionLog.cs` 9–14): `supervisor proc=watcher event=… restarts=…`. Checks are `Compile Include` links into `Zola.Client.Checks`, same pattern as the serve supervision checks.

### WT-G8 — sender resolution

Forget matches, in order (`proactive_store.py` 1432–1439): `entity_id` equality; `sender_address_hash` in the hash set; `message_id`, `thread_id`, or `event_id` in the source ids; otherwise a name hit only when `entity_id` is set. Alias hashes are address-shaped `entity_aliases`, hashed with `address_hash` (`forget.py` 1262–1272). `insert_item` already stores `sender_address_hash` and leaves `entity_id` NULL.

Scratch check, no `set_sender_resolution`: a row whose hash equals the entity alias hash was deleted (`items_deleted=1`). A second row whose address is not in that hash set remained (`remaining=1`) with `entity_resolution=unresolved`. So a memory alias is forget-reachable with no resolution write. An address that exists only in Contacts is not.

Options:

| Option | What the watcher does | Forget-by-person when the address is in Contacts only |
|---|---|---|
| (a) | Store `sender_address_hash`. Leave resolution `unresolved`. | The row remains. Memory never had the alias. |
| (b) | Read memory aliases and set `entity_id`. | Same gap. Also a cross-plugin read against the P9-D03 import rule. |
| (c) | Leave the row unresolved; serve fills `entity_id` later. | Same gap until the address is a memory alias. Contacts stay out of the watcher. |
| (d) | none recommended | |

Recommend (a). The watcher never calls Contacts. (c) can still be added later inside serve without a watcher change. Brian decides.

### WT-G9 — cursors and health

`cursors` (`proactive_store.py` 275–281): `source`, `scope_key`, `cursor_value`, `updated_at`, primary key `(source, scope_key)`. No read or write functions exist. `watcher_health` (283–288): one row, `id=1`, `last_ok_at`, `error_class`, `updated_at`. Empty in the live baseline.

Scope keys: `gmail` / `mailbox` for the one mailbox, and `calendar` / `<calendar id>` per calendar. Add `read_cursor`, `write_cursor`, and `clear_cursor` on `proactive_store`. `write_cursor` is its own transaction and runs only after the page is complete (WT-G4). `clear_cursor` is the 410 and recovery reset. A caller that writes the cursor before the page is finished is a bug the Phase 4 test covers; the function itself does not know which ids were fetched.

One health row cannot tell a stale Gmail poll from a stale Calendar poll, and it cannot store `needs_reconnect` beside a per-source error. Propose v3 columns on the same single row: `gmail_ok_at`, `calendar_ok_at`, `gmail_error`, `calendar_error`, `needs_reconnect`, `recovery_count`, `updated_at`. Keep `id=1`. Health is written after the cycle, never in the cursor transaction. The client computes staleness later (Track 6). The watcher does not store a stale flag.

### H-W1

Scratch harness `hw1_run.py`. Fake token endpoint and a scratch `proactive.db`. No live Google and no live profile.

| Check | Result |
|---|---|
| Two processes, one named mutex, fake token POST | `posts=2`, `post_overlap=0`, `post_elapsed_ms=985` |
| Waiter blocked, holder killed | `abandoned` in `171` ms (timeout was 5000), `reconnect=0` |
| Lock timeout while the holder is alive | `timeout`, `reconnect=0` |
| Fake body `invalid_grant` | `reconnect=1` |
| Crash after item commit, before cursor | exit `9`, `items=1`, `cursor_rows=0` |
| Restart replay of that item | `created=0`, `items=1`, `duplicates=0`, cursor `h-1` |
| Watcher inserts 4 items while a serve-like process purges and closes one loop | `items=4`, distinct keys `4`, `lost_updates=0`, loop `closed` |

POSTs 2. Lost updates 0. Duplicates 0. Final cursor `h-1`.

### Phase 2 flags (decisions, not blockers)

1. Sender resolution vs P9-D04. Recommend (a). Brian decides.
2. Calendar baseline vs the current idempotency key. Recommend (b) plus v3. Brian decides.
3. Build plan says `ProcessSupervisor`. Accepted deviation remains `RestartPolicy`.
4. `close_loop` is ticket-gated. A predicate close needs `close_loop_from_match` or it waits for Track 5.
5. Poison cap and `watcher_rejects` vs another table. Propose cap 5 and a new table.
6. Rotated refresh tokens are ignored today. Propose leaving that as-is.
7. `loops.py` imports `turn_context`. The watcher imports `evaluate` only.
8. No `history.list` or `getProfile` route exists yet. Phase 4 adds them behind the allowlist.

## Phase 3 — Proposal (2026-10-13)

Nothing in this section is approved. No plugin or client source was modified. Phase 4 waits for verdicts recorded verbatim.

### background_read

One module. The watcher calls it. It calls `google_http.request` with a background capability. Tool handlers do not pass that capability and stay as they are.

| Function | Call | Kept fields |
|---|---|---|
| `gmail_profile()` | `GET users/me/profile` | `historyId` only. The address is discarded. |
| `gmail_history(start_history_id, page_token)` | `history.list` | `historyId`, `nextPageToken`, and `messagesAdded[].message.id` / `threadId` where the label filter applied |
| `gmail_message(message_id)` | `messages.get` `format=full` | id, threadId, labelIds, headers From / Subject / Date, snippet, body through `extract_body` and `prepare_body` (cap 4000). No attachment bytes. |
| `gmail_recovery_list(page_token)` | `messages.list` | id and threadId only. Used only after history 404. |
| `calendar_ids()` | `calendarList.list` | id, and only where `selected` is true (`gcal.py` `_selected_calendars`, 308–309) |
| `calendar_events(calendar_id, page_token, sync_token)` | `events.list` | id, updated, status, start, end, attendee count, recurringEventId, originalStartTime. No description, no title in logs. |

Source scan: `watcher.py` and `background_read.py` may import `google_http`, `auth`, `proactive_store`, `loops`, `textclean`, and `log`. They may not import `gmail`, `gcal`, `contacts`, `drive`, `framing`, `guards`, `send_gate`, `origin`, or a Hermes agent, tool, gateway, or model module. The scan failing is a test failure. The allowlist inside `google_http.request` is the runtime boundary.

### Refresh lock

Named mutex `Local\ZolaOAuthRefresh` via stdlib `ctypes`, around the token POST only. Timeout 45 seconds. `WAIT_ABANDONED`: proceed and re-read the DPAPI record before POST. Timeout: transient, WARN `refresh_lock_timeout`, no `needs_reconnect`. Access tokens stay in each process. A rotated refresh token is ignored. `needs_reconnect` only from the existing token-endpoint failures in `auth.py` 691–710.

### Process

`python -m zola_workspace.watcher` on the Hermes venv. `HERMES_HOME` is the zola profile. `PYTHONPATH` is the live `plugins` directory plus the hermes root. No dashboard session token. Second instance: mutex `Local\ZolaWatcher`, WARN `already_running`, exit 2. Log: profile `logs/zola_watcher.log`, 1 MB, 3 backups, metadata only. Line shape `zola_watcher.poll source=… ok=… new=… ms=…`. Stderr captured beside that file. Not started from `register`.

Orphan rule: the client creates a Job Object, sets `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, and assigns the watcher. A crashed client closes the job handle and the watcher dies with it. If assignment fails, the watcher watches its parent PID and exits when that process is gone. Smoke: kill the client process; the watcher exits within 5 seconds; the next launch starts exactly one watcher.

### Commit order

Same for a Gmail history page and a Calendar page:

1. Upsert each event or insert each message. Each write commits on its own.
2. Run `loops.evaluate` on every item on the page, including a replay that returned `created=False`.
3. On a match, `note_loop_match_on_loop` (proposed: also `AND matched_at IS NULL`, so a second pass does not rewrite the stamp).
4. `mark_loop_eligible`. If it refuses, read the item. `eligibility=eligible` and `loop_matched=1` is success. Any other state is a WARN with a named reason (`not_eligible`, `loop_not_matched`, `suppressed`, `expired`, `closed`). Never silent.
5. Cursor write, only after every id is an item or a terminal poison record.
6. Health write, its own transaction, after the cycle.

Test: crash after the insert and before evaluation, then restart. The replay evaluates, and the match is recorded once.

While `needs_reconnect` is set, do not call Google. Every 60 seconds call `store_status()` (`auth.py` 275), which reads the local store and does not use the network. When `needs_reconnect` is clear, resume. Test: reason set, no poll; reason cleared, the next recheck polls.

### Constants

| Name | Value |
|---|---|
| `GMAIL_POLL_SECONDS` | 120 |
| `CALENDAR_POLL_SECONDS` | 7200 |
| `CLOCK_JUMP_SECONDS` | 15 |
| `ERROR_BACKOFF_CAP_SECONDS` | 600 |
| `REFRESH_LOCK_TIMEOUT_SECONDS` | 45 |
| `POISON_ATTEMPT_CAP` | 5 |
| `RECONNECT_RECHECK_SECONDS` | 60 |
| `GMAIL_RECOVERY_WINDOW_DAYS` | 7 |
| `WATCHER_ORPHAN_EXIT_SECONDS` | 5 |
| `WATCHER_LOG_MAX_BYTES` | 1000000 |
| `WATCHER_LOG_BACKUPS` | 3 |

No `config.yaml` line. `desktop.auto_continue.enabled` stays false.

### Gmail 404 recovery

`labelIds=INBOX` is a `messages.list` parameter. The window is `q=newer_than:7d`.

- [EXT] https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list — read 2026-10-13. `labelIds` returns messages with all of those label ids. `q` uses Gmail search syntax. `q` cannot be used with the `gmail.metadata` scope. This token's scope is `gmail.readonly` (`auth.py` 43, 59), so `q` is allowed.
- [EXT] https://support.google.com/mail/answer/7190 — read 2026-10-13. `newer_than:` takes a number plus `d`, `m`, or `y`. Example on that page: `newer_than:2d`.

Only ids not already stored become candidates. Then `getProfile` supplies the next `historyId`, and only `historyId` is kept. A change older than the window is not a candidate. Changes after the new history id are not skipped.

### Calendar scope and the measured first sync

Use `_selected_calendars`: `selected is True` only (`gcal.py` 308–309). Not every `calendarList` entry.

Counted 2026-10-13 with the watcher parameter set (`showDeleted=true`, no `singleEvents`, no `timeMin`, `timeMax`, `orderBy`, or `q`). Counts only.

| Count | Value |
|---|---:|
| Calendars with `selected` true | 4 |
| Other calendarList entries | 0 |
| First-sync event rows | 1041 |
| Pages | 7 |
| Truncated | 0 |
| Gmail items on first sync | 0 |

### Calendar model — (a) and (b)

The case: an event is created after the baseline, Track 4 ranks it or Track 6 delivers it, then it is cancelled, and an open loop's predicate is that event id plus `calendar_cancelled`.

Both designs update one existing row's `calendar_status` to `cancelled` and do not insert a second row. `loops.evaluate` then runs on that row.

What Brian actually receives depends on a store transition that is the same in both designs:

- The loop is still open: `note_loop_match_on_loop` sets `matched_at` once.
- The item is still `eligibility=pending`: `mark_loop_eligible` sets `loop_matched=1`. Track 5's loop block and, if `delivery` is still `none`, Track 6 `claim_speech` (`proactive_store.py` 911–918) can proceed.
- The item is already `eligible` with `loop_matched=1`: success, no second write. This is the replay.
- The item is already `eligible` or already `delivered`, and `loop_matched` is still 0: today's `mark_loop_eligible` refuses, because it requires `eligibility=pending` (730). Under the replay rule that refusal is a WARN `loop_not_matched`, and Brian is not told. Proposed function `set_loop_matched` sets `loop_matched=1` and leaves eligibility and delivery alone. Track 5 then shows the matched loop. Track 6 speaks only when `delivery` is still `none`. A row that is already `delivered` is not spoken a second time. The conversation block is how that cancellation reaches Brian.
- `suppressed`, `expired`, or `closed`: WARN with that reason. Do not flip the row back.

**(a) `calendar_events` plus items only for a real change.** First sync writes 1041 rows into `calendar_events` and zero `items`. A post-baseline create writes one `calendar_events` row and one `items` row (`baseline` is not a column). The cancel updates both. The path above runs on the item. A later Track 4, 5, or 6 query does not need a baseline filter, because the 1041 baseline rows are not items. A cancellation of a baseline event that a loop watches inserts one item at cancel time, then runs the same path. That insert is the loop's signal, not a second copy of the series.

```sql
CREATE TABLE calendar_events (
  calendar_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  event_updated TEXT NOT NULL,
  calendar_status TEXT,
  recurring_event_id TEXT,
  original_start TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (calendar_id, event_id)
);
```

Item idempotency for a post-baseline calendar row becomes `calendar:<event id>`. Schema version 3.

**(b) one `items` row per event id, `baseline` column.** First sync writes 1041 `items` with `baseline=1`. The post-baseline create is one row with `baseline=0`. The cancel updates that same row and runs the path above. `baseline` stays 0, so the row remains visible to later tracks. The 1041 baseline rows stay `baseline=1`.

```sql
ALTER TABLE items ADD COLUMN baseline INTEGER NOT NULL DEFAULT 0;
ALTER TABLE items ADD COLUMN recurring_event_id TEXT;
ALTER TABLE items ADD COLUMN original_start TEXT;
```

Calendar idempotency becomes `calendar:<event id>`. Schema version 3.

Readers that would have to filter `baseline=1` under (b), and would not under (a):

| Track | Reader | Today |
|---|---|---|
| 4 | The ranker picker that will select `processing=unranked` | Not written. `claim_rank` (518–539) will rank any unranked id it is given. |
| 4 | `mark_eligible` (742–768) | No baseline check. It promotes a ranked pending row. |
| 5 | `list_open_items` (1350–1358) | Every unclosed item, which is what `whats_pending` will list. |
| 5 | The surface block of eligible items | Planned in Track 5. It will read `eligibility=eligible`. |
| 6 | The coordinator query that feeds `claim_speech` | `claim_speech` (911–918) requires `eligibility=eligible` and `delivery=none`. It has no baseline check. |

The loop evaluator does not filter `baseline=1`. A loop on an existing event has to see the baseline row. HUD reads `watcher_health`, not items.

Recommendation: (a). A missed filter under (b) would rank or list 1041 baseline rows. (a) keeps those rows out of `items`.

### Series cancellation

`recorded_results.remember` (79–124) stores `event_id`, `event_updated`, and `calendar_status` for a calendar handle. It has no `recurringEventId` field. `_stamp_event` (269–276) does not pass one. A loop created from a calendar tool is bound to the instance `event_id` only.

The series-delete match (a cancelled master also matches a loop bound to an instance) is a residual. It is not in this proposal. An instance that is itself cancelled still matches, because that response carries the instance id.

### Sender resolution

Recommend (a): store `sender_address_hash`, leave `entity_resolution=unresolved`, never call Contacts. Phase 2's scratch check deleted the alias-hash row with no `set_sender_resolution`, and left the Contacts-only row. (b) reads memory from the watcher. (c) lets serve fill `entity_id` later. (c) can be added in a later track without a watcher change.

### Health

v3 columns on the single `watcher_health` row (`id=1`): `gmail_ok_at`, `calendar_ok_at`, `gmail_error`, `calendar_error`, `needs_reconnect`, `recovery_count`, `updated_at`. The client computes staleness in Track 6. Poison records go in a new `watcher_rejects` table: `source`, `source_id_hash`, `error_class`, `disposition`, `attempts`, `first_seen`, `last_seen`. No content columns. Cap 5, then the cursor may pass that id.

Cursor functions on `proactive_store`: `read_cursor`, `write_cursor`, `clear_cursor`. Scope `gmail` / `mailbox`, and `calendar` / `<calendar id>`.

`close_loop_from_match(loop_id, closed_intent)` has no ticket check. Allowed intents: `cancelled`, `status_change`. Only from `status=open`. `close_loop` stays ticket-gated for the tool.

### Client

Start the watcher in `App.OnLaunched`, not after serve is healthy, and not as a child of serve. Own `RestartPolicy`, own generation, 3 restarts in 10 minutes. Deliberate stop on window close before any kill. Kill only a process whose command line contains `zola_workspace.watcher` and whose generation matches. Log `supervisor proc=watcher event=… restarts=…`.

### Tests and smoke changes

Unit tests with fakes, plus the Phase 4 list in the prompt. Added here:

- Crash after insert and before evaluation; restart; the match is stored once.
- `mark_loop_eligible` refusal: eligible plus `loop_matched=1` is success; every other eligibility WARNs with a named reason.
- `needs_reconnect` set: no Google call; `store_status` clear on the next 60-second recheck resumes.
- Recovery list uses `labelIds=INBOX` and `newer_than:7d`.
- Calendar ids are the `selected is True` subset.

Smoke, adjusted:

- W5 gains a kill of the client process. Identify the CPython child of the venv shim and prove that process, not only the shim, is gone within 5 seconds. The next launch starts exactly one watcher, which requires the mutex to be free.
- W1 reports the Calendar baseline count and Gmail new-item count 0.
- W7's resume, if a reconnect happens live, follows the 60-second local recheck. If it does not happen, the unit test covers it.

### Risks

A missed `baseline=1` filter under (b) would push 1041 calendar rows into ranking and `whats_pending`. (a) avoids that and adds a second table forget and the loop path must both know about. The recovery window can miss a message older than 7 days; the replacement history id must be taken only after the candidates are durable. A Job Object assignment can fail; the parent-PID watch is the backup, and the smoke has to kill the client rather than close the window. A cancellation of an already delivered item is not spoken again.

### Decisions

Each line is open.

1. Calendar model. (a) `calendar_events`, items only for a post-baseline change or a loop-matched cancellation. (b) `baseline` on `items`, and every reader in the table above filters `baseline=1`. Recommend (a).
2. Series-delete match. Recorded handles do not store `recurringEventId`. (a) residual, no code. (b) add the field to `recorded_results` and match a cancelled master. Recommend (a).
3. Sender resolution. (a) hash only, unresolved. (b) watcher reads memory aliases. (c) serve fills `entity_id` later. Recommend (a). Contacts stay out of the watcher.
4. Terminal calendar predicates. (a) `close_loop_from_match` for `cancelled` and `status_change`. (b) set `matched_at` only and leave the close to Track 5. Recommend (a).
5. Already-eligible cancellation. (a) `set_loop_matched` so a ranked or delivered item still records the loop. (b) WARN `loop_not_matched` and do not set the flag. Recommend (a). Speech still requires `delivery=none`.
6. Poison. (a) `watcher_rejects`, cap 5. (b) columns on `items`. Recommend (a).
7. Runtime allowlist. (a) inside `google_http.request` when the background capability is passed. (b) a wrapper, and `google_http` stays unchecked. Recommend (a).
8. Access tokens. (a) per process, not persisted, rotated refresh token ignored. (b) persist a rotated refresh token with the existing atomic replace. (c) one shared access token. Recommend (a).
9. Health. (a) the v3 columns above. (b) leave `last_ok_at` and `error_class` as they are. Recommend (a).
10. Launch. (a) with the client, independent of serve. (b) after serve is ready, and keep running if serve later dies. Recommend (a).
11. Orphan. (a) Job Object `KILL_ON_JOB_CLOSE`, parent-PID watch if assignment fails, exit bound 5 seconds. (b) parent-PID watch only. Recommend (a).
12. `needs_reconnect` resume. (a) local `store_status` every 60 seconds, no network, resume when the reason clears. (b) stay stopped until the process is restarted. Recommend (a).
13. Recovery window. `labelIds=INBOX` plus `newer_than`. (a) 7 days. (b) 2 days. Recommend (a).
14. Replay. Evaluate every item on the page, including `created=False`. Eligible and `loop_matched=1` is success. Anything else WARNs with a named reason. Recommend adopt, with the crash-before-evaluation test.
15. `getProfile`. Keep `historyId` only. The address is not stored. The proceed message says this is agreed. Confirm in the verdict.
16. Restart limit. Keep 3 restarts in 10 minutes. Recommend keep.
17. `config.yaml`. No new line. Recommend none.
18. Backups. Delete the whole `C:\Users\test\Dev\zola-spikes\p9-store\plugin-backup\` folder, or keep it. Recommend delete only after an explicit yes. The folder today:

| Bytes | File |
|---:|---|
| 68188 | `zola_memory__forget-before-p9store-close.py` |
| 53049 | `zola_memory__forget.py` |
| 62240 | `zola_memory__forget.py-before-origin-token` |
| 4319 | `zola_memory__log.py-before-origin-token` |
| 13893 | `zola_memory__provider.py-before-origin-token` |
| 13648 | `zola_memory__retrieve.py-before-origin-token` |
| 5664 | `zola_workspace__contacts.py` |
| 25205 | `zola_workspace__gcal.py` |
| 40053 | `zola_workspace__gmail.py` |
| 2780 | `zola_workspace__log.py` |
| 13502 | `zola_workspace__loops-before-60.py` |
| 13495 | `zola_workspace__loops-before-p9store-close.py` |
| 13048 | `zola_workspace__loops.py` |
| 16203 | `zola_workspace__origin-before-p9store-close.py` |
| 15611 | `zola_workspace__origin.py-before-origin-token` |
| 50942 | `zola_workspace__proactive_store-before-p9store-close.py` |
| 6619 | `zola_workspace__turn_context.py-before-origin-token` |
| 6440 | `zola_workspace____init__.py` |

## Brian's verdicts (verbatim, 2026-10-13)

1. Calendar model: (a), with one change. Keep the existing item idempotency key calendar:<event id>:<updated>; do not change it to calendar:<event id>. calendar_events holds known state (ids, status, times; no titles or people). An item is created only for (i) a new event first seen after the baseline, or (ii) a change that matches an open loop (cancelled or status change), and each such change is its own new item, so a cancellation of an already-delivered event can still be told and spoken. Baseline sync creates zero items. The items key needs no v3 change; the v3 migration adds calendar_events, watcher_rejects and the health columns only. Add a test: event created after baseline → item delivered → event cancelled with a loop open → a second, new item that is pending, then loop-eligible.
2. Series-delete match: (a), a residual.
3. Sender resolution: (a).
4. Terminal calendar predicates: (a), close_loop_from_match for cancelled and status_change only. The matched item stays eligible; closing the loop is not the same as telling me.
5. set_loop_matched: (a), as a backstop.
6. Poison: (a), watcher_rejects, cap 5.
7. Allowlist: (a), inside google_http.request.
8. Access tokens: (a).
9. Health: (a).
10. Launch: (a).
11. Orphan: (a).
12. needs_reconnect resume: (a).
13. Recovery window: (a), 7 days.
14. Replay: adopt, with the crash-before-evaluation test.
15. getProfile: confirmed, historyId only.
16. Restart limit: keep 3 in 10 minutes.
17. config.yaml: none.
18. Backups: yes, delete the whole zola-spikes\p9-store\plugin-backup folder.

## Phase 4 — Build (2026-10-13)

Repo only. No commit, no deploy, no live `proactive.db` open. `config.yaml` was not edited.

Verdict 1 keeps `calendar:<event id>:<updated>`. `calendar_events` is updated in place. A new item is inserted only for a new event id after the baseline, or for a later `cancelled` / `status_change` that matches an open loop. The prompt line "a cancelled event updates, not inserts" applies to `calendar_events`. The items table gets a second row so a cancellation after delivery can still be told. Baseline sync writes zero items. Schema v3 adds `calendar_events`, `watcher_rejects`, and the health columns. It does not change the items key.

The allowlist runs inside `google_http.request` when the background capability is passed. Tool calls omit it. The refresh POST takes the named mutex `Local\ZolaOAuthRefresh`. A timeout raises `RefreshLockTimeout` and does not set `needs_reconnect`. A dead holder is `WAIT_ABANDONED` and the next refresh proceeds. The access token stays in process memory. A rotated refresh token in the response is ignored.

The watcher is started from `App.OnLaunched`, not from `zola_workspace.register` and not as a child of serve. `WatcherSupervisor` has its own `RestartPolicy` and generation. The limit stays 3 restarts in 10 minutes. The job object uses `KILL_ON_JOB_CLOSE`. If assignment fails, the process watches the parent pid and exits within 5 seconds. Killing the client is a Phase 6 smoke step.

### Suites and checks (after Phase 4)

| Suite | Before | After |
|---|---|---|
| `zola_workspace` | 208 OK | 232 OK |
| `zola_memory` | 134 OK | 134 OK |
| `zola_tools` | 44 OK | 44 OK |
| `zola_tts` | 8 OK | 8 OK |
| `Zola.Client.Checks` | supervision 31/31 | supervision 36/36 |

`dotnet build windows-client\Zola.Client\Zola.Client.csproj`: 0 warnings, 0 errors.

## Residuals

Series-delete match (verdict 2). `recorded_results` does not store `recurringEventId`, so a cancelled series master does not match a loop bound to an instance id. An instance that is itself cancelled still matches. The backup folder is deleted.

## Phase 5 — Fixes (2026-10-13)

F1–F11. A cycle exception stays in the process. Transport errors, 429, and 5xx hold the cursor and do not count toward the poison cap. Gmail 404 recovery takes `historyId` before `messages.list` and skips mail older than the cursor `updated_at` minus `GMAIL_RECOVERY_MARGIN_SECONDS` (120), using `internalDate`. Calendar mode comes from the cursor: empty is a first sync until the first `nextSyncToken` (no items), `zola:calendar-resync` is a 410 recovery, and any other value is the incremental token. A 410 writes that marker instead of clearing the cursor. Stdout and stderr are drained into `zola_watcher.out.log` beside `zola_watcher.log`, with serve's stderr cap, rotation, and user-only ACL. The watcher calls `purge_retention` at start and every `PURGE_INTERVAL_SECONDS`.

Suites after these fixes: workspace 238 OK, memory 134 OK, tools 44 OK, tts 8 OK, supervision 38/38. Not committed. Not deployed.

## Phase 6 — Deploy and smoke (2026-10-14) — BLOCKED at W1

`config.yaml` was not edited. SHA-256 `0DD2F5635E438AAE6644FBA0B7502AE54C2AFF8837D599D3E2F8F6EA77FE1E26`, 4,629 bytes, before and after.

Live plugin backups are in `C:\Users\test\Dev\zola-spikes\p9-watch\plugin-backup\`. `background_read.py` and `watcher.py` were new, so they have no backup. Tests and `__pycache__` were not copied.

| Backup file | Bytes | SHA-256 |
|---|---:|---|
| `zola_workspace__auth.py-before-p9watch` | 25186 | `A8AA8810FC9DF899788273181C8199645E2BAAD3D35A0C1ADAE318F4423E7667` |
| `zola_workspace__google_http.py-before-p9watch` | 9189 | `81281017D1A93DE26936DC660D2A9E9F7F1DF53411175B95F9136B9F92765B82` |
| `zola_workspace__proactive_store.py-before-p9watch` | 52494 | `A167FBEE6C347D3C3280EF674B8A24567AF73E7EE2836B036F57F841F6C2E463` |

Repo file and live mirror SHA-256 match for each copied file.

| File | Bytes | SHA-256 |
|---|---:|---|
| `zola_workspace/auth.py` | 28263 | `90064F40B3FDB6DC61C09E081D4391B8A8506B7781A3520FF71BD4869E955812` |
| `zola_workspace/google_http.py` | 15252 | `A7990B280328676FB11FC9EA57C0E3709C04CBB01D800838E037074B41319C14` |
| `zola_workspace/proactive_store.py` | 70709 | `09F33E24A304856FC766D628420667503FC73F5F54A5FE3D3B7F932BBDDD7832` |
| `zola_workspace/background_read.py` | 9548 | `ACB8C3E21288A22A241E46239B840F6CC8F944CD2C4CF1E2E4FE86FC5BB1A1DD` |
| `zola_workspace/watcher.py` | 32517 | `2C25BCD0092A4DA1A75B0667CC66F89174CF4079DAA9752BDE4C343CE2730091` |

The client was closed before the migration so the store had one writer. `WM_CLOSE` of client 12548. Shim 32352 and CPython 36256 exited with it. Other python processes that were already running were left alone. Schema version 3. `integrity_check` ok. Journal mode `wal`. Before the new client started: items 0, loops 4 (open 0), cursors 0, calendar_events 0, watcher_rejects 0.

Release build: 0 warnings, 0 errors.

New window: client 39144, parent 32532, start 2026-10-14 07:00:29. Watcher shim 37124, parent 39144, start 07:00:32. Watcher CPython 8388, parent 37124, start 07:00:32. Serve shim 35880, parent 39144, start 07:00:32. Serve CPython 5820, parent 35880, start 07:00:33. `supervisor.log` `2026-10-14T07:00:32` `supervisor proc=watcher event=job_assigned restarts=0 generation=1 pid=37124`. `agent.log` `07:00:49` `origin wrap installed method=prompt.submit`. One dedicated Zola serve. One watcher.

### W1 — BLOCKED

Gmail polls, about 120 seconds apart, `new=0`:

```
2026-10-14 07:00:34 zola_watcher.poll source=gmail ok=1 new=0 ms=1313
2026-10-14 07:02:34 zola_watcher.poll source=gmail ok=1 new=0 ms=282
2026-10-14 07:04:35 zola_watcher.poll source=gmail ok=1 new=0 ms=250
```

A second `python -m zola_workspace.watcher` exited 2 and logged `zola_watcher reason=already_running`.

Calendar did not sync. `zola_watcher.out.log` has `zola_workspace.google_http.refused route=calendar.events.list reason=url`. The watcher log has `zola_watcher reason=url source=calendar` at 07:00:35. Four selected calendars. The first id, placed unencoded into the events path, is parsed as a URL fragment, so the allowlist refuses it before any page is stored. Counts after the three Gmail polls: items 0, calendar_events 0, watcher_rejects 0, loops 4 (open 0). Cursors: 1, source gmail, value is a token. No calendar cursor. The resync marker is not present. Health: `calendar_error=url`, `needs_reconnect=0`, `recovery_count=0`. `origin_unresolved` since 07:00: 0. No human step yet, so `echo_suspect` is not scored.

The next calendar attempt is the normal 2-hour interval plus the error backoff, so this process will not retry the list before then. W2 has not started. The client is still running.

### W1 retry (2026-10-14)

The events path now uses `urllib.parse.quote(calendar_id, safe="")`, the same call `gcal.py` uses. The allowlist still refuses a raw query or fragment, and it refuses a calendar-id segment that still contains `#`, `@`, or `/`. One held calendar logs its error, keeps its own cursor, and the loop continues. The cycle is ok only when every calendar succeeds. Health then shows `calendar_error` as `<reason> failed=<count>`.

Suites after the fix: workspace 240 OK (the first run was 2 failures while the live watcher held `Local\ZolaWatcher`; the rerun after the deliberate close was 240 OK in 10.599s), memory 134 OK, tools 44 OK, tts 8 OK, supervision 38/38.

Backups of the three replaced live files, taken before this copy:

| Backup file | Bytes | SHA-256 |
|---|---:|---|
| `zola_workspace__background_read.py-before-p9watch-encode` | 9548 | `ACB8C3E21288A22A241E46239B840F6CC8F944CD2C4CF1E2E4FE86FC5BB1A1DD` |
| `zola_workspace__google_http.py-before-p9watch-encode` | 15252 | `A7990B280328676FB11FC9EA57C0E3709C04CBB01D800838E037074B41319C14` |
| `zola_workspace__watcher.py-before-p9watch-encode` | 32517 | `2C25BCD0092A4DA1A75B0667CC66F89174CF4079DAA9752BDE4C343CE2730091` |

Repo and live mirror match:

| File | Bytes | SHA-256 |
|---|---:|---|
| `zola_workspace/background_read.py` | 9684 | `474F60BF942750E32F0645DD57BD06479061F3F70556C8BF0EB7C0645B82096C` |
| `zola_workspace/google_http.py` | 15527 | `FD10CBCFD304482E850FDB6CADF9F689B6CC482C28068C93B314634E6922C67F` |
| `zola_workspace/watcher.py` | 32758 | `7CA0330309B590801F19C0B7A361EEB8E837863777B884D3DC8E50A3F94C838D` |

`WM_CLOSE` of client 39144. `supervisor.log` `07:15:35` `supervisor proc=watcher event=stop restarts=0 generation=1`. Shim 37124 and CPython 8388 exited with it. No watcher restart was logged.

New window: client 7332, parent 39200, start 2026-10-14 07:16:09. Watcher shim 40924, parent 7332. Watcher CPython 40864, parent 40924. Both started 07:16:10. Serve shim 40320, parent 7332. Serve CPython 40884, parent 40320. `07:16:10` `supervisor proc=watcher event=job_assigned restarts=0 generation=1 pid=40924`.

Gmail polls, `new=0`:

```
2026-10-14 07:16:12 zola_watcher.poll source=gmail ok=1 new=0 ms=1780
2026-10-14 07:18:13 zola_watcher.poll source=gmail ok=1 new=0 ms=296
2026-10-14 07:20:14 zola_watcher.poll source=gmail ok=1 new=0 ms=203
```

Calendar: `07:16:16 zola_watcher.poll source=calendar ok=1 new=0 ms=4219`.

Counts: items 0, gmail items 0, calendar items 0, calendar_events 1039, watcher_rejects 0, loops 4 (open 0). Cursors: 4 calendar, each a token, none the resync marker; 1 gmail token. Health: `calendar_error` empty, `calendar_ok` set, `needs_reconnect` 0. A second watcher exited 2 and logged `zola_watcher reason=already_running`. `origin_unresolved` since 07:16: 0. No human step yet.

W1 passed. Stopped for W2.

### W2 (2026-10-14)

The next Gmail poll after the send was `07:28:27 zola_watcher.poll source=gmail ok=1 new=1 ms=782`.

One Gmail item. Id SHA-256/16 `542e30e637c7eafa`. Message id SHA-256/16 `7b6658fbac171b3b`. Thread id SHA-256/16 `7b6658fbac171b3b` (same value). `entity_resolution=unresolved`, entity id empty. `sender_address_hash` is 64 hex; SHA-256/16 of that hash is `dfdc7acb33391ba6`. Display-name length 12. Address length 20; the address is stored and is not copied here. `processing=unranked`, `eligibility=pending`, `delivery=none`, `loop_matched=0`, `content_state=available`, `detected_at=2026-10-14T14:28:27Z`.

A search of the profile logs and the client logs found the scripted title in no log file.

Counts: items 1, loops 4 (open 0), calendar_events 1039, watcher_rejects 0. `echo_suspect` 0. `origin_unresolved` since 07:27: 0.

Stopped for W3.

### W3 lines (2026-10-14)

Two typed turns in session `7678912c`. `07:30:07` prompt accepted, 35 characters, then a Gmail tool. `07:30:24` prompt accepted, 36 characters. `07:30:34` `zola_loops`. No `gate brian_only` refusal. No `origin_unresolved`.

One new open loop. Id SHA-256/16 `96ccfbd7ce005f29`. Intent `reply`. Created `2026-10-14T14:30:34Z`, expires `2026-10-28T14:30:34Z`, `matched_at` empty, entity id empty. Session SHA-256/16 `13e8958da3183c2b`. Display-name length 12. Subject length 13. Predicate is `all` of `gmail_thread` (thread SHA-256/16 `7b6658fbac171b3b`, the same hash as the W2 item), `sender_is` (address hash length 64, SHA-256/16 `dfdc7acb33391ba6`), and `after` `2026-10-14T14:30:34Z`. Two source ids, both that same thread hash. One address hash, that same sender hash.

Counts: items 1, loops 5 (open 1), calendar_events 1039, watcher_rejects 0. `echo_suspect` 0. `origin_unresolved` 0.

The own-account reply and the other-account reply have not been checked yet.

### W3 own-account reply (2026-10-14) — criterion failed

The thread has two messages. The first is the W2 item: labels `IMPORTANT,CATEGORY_PERSONAL,INBOX`, sender hash SHA-256/16 `dfdc7acb33391ba6` (not the profile). The reply: message SHA-256/16 `c5481a95dffe7b14`, labels `SENT` only, sender hash SHA-256/16 `b269a14baacdafd1`, which matches the profile address hash and not the loop's other-party hash.

`07:34:31 zola_watcher.poll source=gmail ok=1 new=5 ms=1641`. That SENT message was stored as an item at `2026-10-14T14:34:30Z`: `unranked`, `pending`, `delivery=none`, `loop_matched=0`, `entity_resolution=unresolved`. The open loop's `matched_at` is still empty. Four other new items are on other threads, from neither hash. They are not described here.

`history.list` is called with `labelId=INBOX`. Ingest does not read the fetched message's `labelIds`, so a SENT-only message that arrives in that history still becomes an item. The loop did not match, because `sender_is` is the other party.

Counts: items 6, loops 5 (open 1), calendar_events 1039, watcher_rejects 0. `echo_suspect` 0. `origin_unresolved` 0. The other-account reply has not been sent.

### W3 own-reply fix (2026-10-14)

`_ingest_message` skips a fetched message whose `labelIds` do not include `INBOX`. That skip writes no item, no poison row, and no loop evaluation, and the cursor still advances. Each Gmail poll logs `skipped_not_inbox=N`. Recovery uses the same check.

The four messages from the 07:34 poll other than the SENT item all include `INBOX` (label counts 2, 3, 3, and 2). They were left in place. The SENT item, message SHA-256/16 `c5481a95dffe7b14`, was removed with `proactive_store.forget_subject`, passing that message id as `source_ids`. The call used the test ticket override because there was no turn. Before: items 7, loops 5 (open 1), calendar_events 1039, watcher_rejects 0. After: items 6, loops 5 (open 1), calendar_events 1039, watcher_rejects 0. `items_deleted=1`, `loops_deleted=0`. The W2 item and the open loop remain. One later INBOX item from 14:40 was also left.

Suites: workspace 241 OK after the deliberate close (the run while the watcher held the mutex was the same 2 failures as before), memory 134 OK, tools 44 OK, tts 8 OK, supervision 38/38.

Backup `zola_workspace__watcher.py-before-p9watch-inbox` is 32758 bytes, SHA-256 `7CA0330309B590801F19C0B7A361EEB8E837863777B884D3DC8E50A3F94C838D`. Live `watcher.py` is 33735 bytes, SHA-256 `E73EBD6A4BBB7900BA3D391CC933CA3176BAF1298F36DCF1DC7BCA1ACE5C8282`, matching the repo.

`WM_CLOSE` of client 7332. `07:44:35` `supervisor proc=watcher event=stop restarts=0 generation=1`. New window: client 27824, parent 24064, start 07:45:09. Watcher shim 812, parent 27824. Watcher CPython 28472, parent 812. `07:45:09` `job_assigned restarts=0 generation=1 pid=812`. First poll: `07:45:11 zola_watcher.poll source=gmail ok=1 new=0 ms=907 skipped_not_inbox=0`.

Waiting for one more own-account reply on the same thread.

### W3 own-account redo (2026-10-14)

The reply is on the thread and was not stored. Thread messages are now 3. The new one, message SHA-256/16 `af3d68d500b1cf07`, labels `SENT` only, From hash SHA-256/16 `b269a14baacdafd1` (the profile address hash, not the loop's other-party hash `dfdc7acb33391ba6`). It is not an item. The earlier SENT message `c5481a95dffe7b14` is still not stored. The W2 item `7b6658fbac171b3b` is unchanged: `unranked`, `pending`, `delivery=none`, `loop_matched=0`, `entity_resolution=unresolved`.

`09:21:37 zola_watcher.poll source=gmail ok=1 new=0 ms=546 skipped_not_inbox=1`. Open loop `96ccfbd7ce005f29` is still `open`, `matched_at` empty.

Counts: items 6, loops 5 (open 1), calendar_events 1039, watcher_rejects 1. `echo_suspect` 0 (no prompt accepted and no `zola_loops` since 09:19). `origin_unresolved` 0.

The reject is not this reply. It is one `gmail` row, error class `http_404`, disposition `terminal`, attempts 1, first and last seen `2026-10-14T16:13:35Z`. The watcher logged `09:13:35 zola_watcher reason=http_404 source=gmail` on a poll with `new=0 skipped_not_inbox=0`. Its source-id hash (SHA-256/16 `1642d5d9565cf4a7`) matches none of the three messages on this thread.

Waiting for the other-account reply on the same thread.

### W3 other-account reply (2026-10-14)

`09:27:39 zola_watcher.poll source=gmail ok=1 new=1 ms=530 skipped_not_inbox=0`. The new item is message SHA-256/16 `a9ebf43799f7552e` on the same thread (`7b6658fbac171b3b`), detected `2026-10-14T16:27:39Z`. States: `unranked`, `eligible`, `delivery=none`, `loop_matched=1`, `entity_resolution=unresolved`. Labels are `UNREAD,IMPORTANT,CATEGORY_PERSONAL,INBOX`. From hash SHA-256/16 `dfdc7acb33391ba6`, the loop's other-party hash.

Open loop `96ccfbd7ce005f29` stayed `open`. `matched_at` is `2026-10-14T16:27:39Z`.

Counts: items 7, loops 5 (open 1), calendar_events 1039, watcher_rejects 1. `echo_suspect` 0. `origin_unresolved` 0.

Waiting for the W4 calendar event.

### W4 create (2026-10-14)

`WM_CLOSE` of client 27824. `09:33:03` `supervisor proc=watcher event=stop restarts=0 generation=1`. New window: client 41644, parent 40580, start 09:33:31. Watcher shim 27464, parent 41644. Watcher CPython 38016, parent 27464. `09:33:32` `job_assigned restarts=0 generation=1 pid=27464`.

`09:33:33 zola_watcher.poll source=gmail ok=1 new=0 ms=1125 skipped_not_inbox=0`. `09:33:35 zola_watcher.poll source=calendar ok=1 new=1 ms=1688`.

One new `calendar_events` row, event SHA-256/16 `8718a178bc61cb9f`, calendar SHA-256/16 `c9be2ee18558617b`, status `confirmed`, start day `2026-10-15`. One calendar item for that event id, detected `2026-10-14T16:33:35Z`: `unranked`, `pending`, `delivery=none`, `loop_matched=0`, `entity_resolution=unresolved`, status `confirmed`. The other 86 rows rewritten on that poll were already known and produced no item. Four calendar cursors, all tokens, no resync marker. `calendar_ok` `2026-10-14T16:33:35Z`, `calendar_error` empty, `needs_reconnect` 0.

Counts: items 8, loops 5 (open 1, `matched_at` still `2026-10-14T16:27:39Z`), calendar_events 1040, watcher_rejects 1. `echo_suspect` 0. `origin_unresolved` 0. The scripted title is in no log under the profile logs or the client logs.

Waiting for the cancellation.

### W4 cancel (2026-10-14)

`WM_CLOSE` of client 41644. `09:36:03` `supervisor proc=watcher event=stop restarts=0 generation=1`. New window: client 37948, parent 33540, start 09:36:16. Watcher shim 15108, parent 37948. Watcher CPython 17764, parent 15108. Serve shim 16108, parent 37948. Serve CPython 38600, parent 16108. `09:36:16` `job_assigned restarts=0 generation=1 pid=15108`.

`09:36:18 zola_watcher.poll source=gmail ok=1 new=0 ms=1140 skipped_not_inbox=0`. `09:36:20 zola_watcher.poll source=calendar ok=1 new=0 ms=1875`.

The same event, SHA-256/16 `8718a178bc61cb9f`, is now `cancelled`. `updated_at` `2026-10-14T16:36:19Z`. Start day still `2026-10-15`. `calendar_events` stayed 1040. The one calendar item is still the 16:33 row: `unranked`, `pending`, `delivery=none`, `loop_matched=0`, `entity_resolution=unresolved`, and its stored status is still `confirmed`. No second item.

Counts: items 8, loops 5 (open 1, `matched_at` `2026-10-14T16:27:39Z`), calendar_events 1040, watcher_rejects 1. `echo_suspect` 0. `origin_unresolved` 0. The scripted title is in no log.

W4 passed. Next is W5.

### W5 (2026-10-14)

Watcher kill. CPython 17764, parent shim 15108, command line the watcher. Both were gone after the stop. `09:39:51` `supervisor proc=watcher event=restart restarts=1 generation=1`. Replacement: shim 41088, parent client 37948, CPython 41860, parent 41088, both started 09:39:53. `09:39:53` `job_assigned restarts=1 generation=2 pid=41088`. Poll resumed `09:39:54 zola_watcher.poll source=gmail ok=1 new=0 ms=563 skipped_not_inbox=0`. Serve was still shim 16108 and CPython 38600.

Serve held down. Four stops of the dedicated serve CPython, 09:40:57 through 09:41:11. The first stop logged `event=stale` three times, then `event=restart restarts=1 generation=1` at 09:41:00. Then `restarts=2` at 09:41:03, `restarts=3` at 09:41:07, and `event=keeps_failing restarts=4 generation=4` at 09:41:11. No serve process after that. Watcher shim 41088, CPython 41860, parent 37948, start 09:39:53, unchanged, and the watcher restart counter stayed at 1. Polls while serve was absent: `09:41:55 zola_watcher.poll source=gmail ok=1 new=0 ms=217 skipped_not_inbox=0` and `09:43:56 zola_watcher.poll source=gmail ok=1 new=0 ms=438 skipped_not_inbox=0`.

Normal close. `WM_CLOSE` of client 37948. `09:44:22` `supervisor proc=watcher event=stop restarts=1 generation=2`. No watcher restart line. Shim 41088 and CPython 41860 were gone. Serve logged `event=stale restarts=4` and did not restart.

Relaunch at 09:44:36: client 16492, parent 21328. One watcher, shim 11144, CPython 24696, both started 09:44:37. `09:44:37` `job_assigned restarts=0 generation=1 pid=11144`. Serve shim 32856, CPython 39960.

Client-process kill, not a window close. Client 16492 was stopped. Watcher CPython 24696 and shim 11144 were both gone at 182 ms. The job line for that watcher was the `job_assigned` above. Serve was not in the watcher job, so shim 32856 and CPython 39960 were still present with the dead client as parent; those two were stopped before the next launch.

Next launch at 09:45:22: client 40116, parent 6452. One watcher, shim 15676, CPython 36724, both started 09:45:22. `09:45:22` `job_assigned restarts=0 generation=1 pid=15676`. Serve shim 17764, CPython 40172, both started 09:45:23.

W5 passed. Next is W6.

### W6 (2026-10-14)

Scratch database only. Fake transport. The script refused the live `proactive.db` path. It opened one file, the scratch database. Live file hash and mtime were unchanged. `live_opened` 0.

Crash after the item commit and before the cursor write: held, cursor stayed `h-1`, items 1. The log line was `zola_watcher reason=unexpected source=gmail class=RuntimeError`. Replay: `ok` `new=0`, cursor `h-2`, items still 1.

Gmail history 404, recovery list containing only that stored id: `recovery` 1, items still 1, `recovery_count` delta 1, cursor `h-3`.

Calendar 410 after a baseline that stored the known event with 0 items: `ok` `new=0`, calendar items 0, `calendar_events` 2 (the known event and one unknown event from the gap), `recovery_count` delta 1, cursor the new token.

`duplicate_keys` 0.

W6 passed. Next is W7.

### W7 (2026-10-14)

Live `store_status`: `connected` 1, `needs_reconnect` none, `missing_scopes` 0. `watcher_health.needs_reconnect` is 0. `gmail_error` and `calendar_error` are empty. No `needs_reconnect` line in the profile logs or the client logs. Polling did not stop.

The resume path did not occur live. Covered by unit tests only (`test_needs_reconnect_does_not_call_google_until_the_reason_clears`).

W7 passed. Next is W8.

### W8 (2026-10-14)

Purge ran. The current watcher logged `09:45:23 zola_watcher.purge bodies=0 texts=0 deliveries=0 loops=0`. Earlier lines the same day were also all zeros.

`PRAGMA integrity_check` ok. Journal mode `wal`. Schema version 3. Counts: items 8, loops 5 (open 1), calendar_events 1040, watcher_rejects 1.

`hermes-agent` is clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

Live mirror: 23 Python files, 0 diffs. `auth.py` and `watcher.py` were behind the repo by the test-mutex helpers. The previous live bytes were saved as `zola_workspace__auth.py-before-p9watch-mutex` (28263 bytes, SHA-256 `90064F40B3FDB6DC61C09E081D4391B8A8506B7781A3520FF71BD4869E955812`) and `zola_workspace__watcher.py-before-p9watch-mutex` (33735 bytes, SHA-256 `E73EBD6A4BBB7900BA3D391CC933CA3176BAF1298F36DCF1DC7BCA1ACE5C8282`). The mirror now matches the repo: `auth.py` 28648 bytes, SHA-256 `BE8A358E4AF0EAB58AFE9E2C45AB18F11977436B40E7CC31E29F71354675CC8C`; `watcher.py` 34130 bytes, SHA-256 `5C0E0BBE7FA95C952A660523086392FC875CC6965C4132478B9B60DC9B23D5DB`. The running watcher was not restarted, so it still has the previous files loaded. Production mutex names are unchanged.

Smoke items, left in place:

| source | id SHA-256/16 | thread or event SHA-256/16 | detected | states |
| --- | --- | --- | --- | --- |
| gmail | `7b6658fbac171b3b` | `7b6658fbac171b3b` | `2026-10-14T14:28:27Z` | unranked, pending, delivery none, loop_matched 0, unresolved |
| gmail | `32461db79b62a4ef` | `32461db79b62a4ef` | `2026-10-14T14:34:30Z` | unranked, pending, delivery none, loop_matched 0, unresolved |
| gmail | `261010cfb42bd10f` | `261010cfb42bd10f` | `2026-10-14T14:34:30Z` | unranked, pending, delivery none, loop_matched 0, unresolved |
| gmail | `9cc7308750c97b25` | `9cc7308750c97b25` | `2026-10-14T14:34:31Z` | unranked, pending, delivery none, loop_matched 0, unresolved |
| gmail | `ab6b58a1d4bb7e3c` | `ab6b58a1d4bb7e3c` | `2026-10-14T14:34:31Z` | unranked, pending, delivery none, loop_matched 0, unresolved |
| gmail | `861169ecc2b38f30` | `861169ecc2b38f30` | `2026-10-14T14:40:33Z` | unranked, pending, delivery none, loop_matched 0, unresolved |
| gmail | `a9ebf43799f7552e` | `7b6658fbac171b3b` | `2026-10-14T16:27:39Z` | unranked, eligible, delivery none, loop_matched 1, unresolved |
| calendar | `8718a178bc61cb9f` | `8718a178bc61cb9f` | `2026-10-14T16:33:35Z` | unranked, pending, delivery none, loop_matched 0, unresolved, status confirmed |

Not deleted.

W8 passed. Smoke test passed. Next is closeout.

### W5 rerun on the current mirror (2026-10-14)

Watcher CPython 36724 stopped. `10:00` wait, `09:59:52` `event=restart restarts=1 generation=1`. Replacement shim 35844, CPython 41820, parent 40116, start 09:59:54. `job_assigned restarts=1 generation=2 pid=35844`.

Serve stopped four times, 10:00:06 through 10:00:18: `restarts=1`, `restarts=2`, `restarts=3`, then `event=keeps_failing restarts=4`. Polls with no serve process: `10:01:55 ok=1 new=0` and `10:03:56 ok=1 new=1`. Watcher pid and start time unchanged. The `new=1` row is Gmail SHA-256/16 `542841f5251f4a24`, real inbox mail, kept.

`WM_CLOSE` of client 40116. `10:04:27` `event=stop restarts=1 generation=2`. No further watcher restart. Clear relaunch `10:04:41` `job_assigned restarts=0 generation=1 pid=40868`, one watcher, CPython 18628. Client-process kill: CPython 18628 and shim 40868 gone at 90 ms. Orphan serve 31996/39404 was stopped because it is outside the watcher job.

Final launch 10:05:09: client 2320, watcher shim 40048, CPython 5052. `job_assigned restarts=0 generation=1 pid=40048`. `10:05:10 zola_watcher.poll source=gmail ok=1 new=0 ms=671 skipped_not_inbox=0`. Mirror 23 Python files, 0 diffs.

### Cleanup (2026-10-14)

`close_loop` on loop `96ccfbd7ce005f29`, `closed_intent=confirm_close`. `forget_subject` for the W2 message id deleted 2 items (that message and the reply on its thread) and 0 loops. `forget_subject` for the calendar event id deleted 1 item and 0 loops. Before: items 9, loops 5 (open 1), calendar_events 1040, watcher_rejects 1. After: items 6, loops 5 (open 0), calendar_events 1040, watcher_rejects 1. Kept Gmail hashes `32461db79b62a4ef`, `261010cfb42bd10f`, `9cc7308750c97b25`, `ab6b58a1d4bb7e3c`, `861169ecc2b38f30`, and `542841f5251f4a24`.


### Test mutex names (2026-10-14)

Suites were taking `Local\ZolaWatcher` and `Local\ZolaOAuthRefresh`, so a run while Zola was up failed `test_second_instance_exits` and `test_main_stays_up_after_auth_and_a_down_profile`. `set_instance_mutex_name_for_tests` and `set_refresh_mutex_name_for_tests` leave those production names as the default. The workspace and connect suites set `Local\ZolaWatcherTest` and `Local\ZolaOAuthRefreshTest` at import, which the child processes inherit because they re-exec the test module.

Re-run with the live watcher still up (client 27824, shim 812, CPython 28472, unchanged through the run): workspace 241 OK in 11.190s, memory 134 OK, tools 44 OK, tts 8 OK. The live process was not restarted and the plugin mirror was not updated.

## Phase 7 — Closeout (2026-10-14)

### watcher_rejects

One row. `source=gmail`, `error_class=http_404`, `disposition=terminal`, `attempts=1`, `first_seen=last_seen=2026-10-14T16:13:35Z`, id SHA-256/16 `b18b0b712f843c1c`. `_message_failure` returns `gone` only for HTTP 404. Transport, 429, and 5xx stay transient and do not write a reject. The watcher log at 09:13:35 local is `zola_watcher reason=http_404 source=gmail`. This is a history id that 404'd on fetch (deleted before fetch). Closeout continued.

### Verification

`Zola.Client` Release build: 0 warnings, 0 errors. Suites with the live watcher up: workspace 241 OK in 15.028s, memory 134 OK, tools 44 OK, tts 8 OK. `Zola.Client.Checks` passed, supervision rows 38/38. Live mirror: 23 Python files, 0 diffs. `hermes-agent` clean at `345cd2b057a452236de401d3534b8502a7465e8d`. `.gitignore` still has `**/proactive.db`, `**/proactive.db-wal`, `**/proactive.db-shm`. No `proactive.db` is tracked. Scratch folder deleted.

### Files

New: `hermes-plugins/zola_workspace/background_read.py`, `hermes-plugins/zola_workspace/watcher.py`, `hermes-plugins/zola_workspace/tests/test_p9_watch.py`, `windows-client/Zola.Client/WatcherProcess.cs`, `windows-client/Zola.Client/Supervision/WatcherJob.cs`, `windows-client/Zola.Client/Supervision/WatcherSupervisor.cs`, this progress doc.

Modified: `hermes-plugins/zola_workspace/auth.py`, `hermes-plugins/zola_workspace/google_http.py`, `hermes-plugins/zola_workspace/proactive_store.py`, `hermes-plugins/zola_workspace/tests/test_p9_store.py`, `hermes-plugins/zola_workspace/tests/test_phase4_connect.py`, `windows-client/Zola.Client/App.xaml.cs`, `windows-client/Zola.Client/Supervision/ServeStderrLog.cs`, `windows-client/Zola.Client/Supervision/SupervisionConstants.cs`, `windows-client/Zola.Client/Supervision/SupervisionLog.cs`, `windows-client/Zola.Client.Checks/SupervisionChecks.cs`, `windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj`.

### Exit criteria

| Criterion | Result |
|---|---|
| WT-G1–G7 answered; STOP verdicts recorded | MET. Verdicts 1–18 are recorded verbatim above. |
| Suites pass; source scan shows only the fixed operations | MET. Closeout suites above. `test_source_scan_and_one_owner_imports` is in the 241. |
| Watcher is its own process; second launch exits; Gmail poll about every 2 minutes | MET. Final launch client 2320, shim 40048, parent = client. Second launch exit 2, `already_running`. `10:05:10 zola_watcher.poll source=gmail ok=1`. |
| Human mail becomes an item; a reply marks the loop matched | MET. W2 item at 07:28:27. W3 other-account reply `09:27:39`, loop `96ccfbd7ce005f29` `matched_at` `2026-10-14T16:27:39Z`. No content in the logs. |
| Kill the watcher restarts it; kill serve and the watcher keeps polling | MET. W5: watcher `event=restart restarts=1`; serve reached `keeps_failing restarts=4`; polls `10:01:55 ok=1` and `10:03:56 ok=1` with no serve. |
| Cursor-advance crash replays without duplicates | MET. W6: crash held cursor `h-1`, replay `new=0`, items stayed 1, `duplicate_keys` 0. Live db not opened. |
| Fakes: baseline, pagination, cancel, 404/410 | MET. Those cases are in `test_p9_watch` and W6 (Gmail 404 recovery of the stored id only; calendar 410 `new=0`). |
| `needs_reconnect` during the track | MET. It did not happen. Health `needs_reconnect` 0. Resume is unit-test only (residual). |
| WT-G4a, G4b, G8, G9 decided | MET. Verdicts 1, 2, 3, 6, 9, 13, 15. |
| Allowlist refuses off-list requests before HTTP | MET. `google_http.request` checks the background capability. Smoke refused a raw `#` calendar id before any page was stored. |
| No cursor passes unfinished work | MET. Partial-failure tests; W6 held the cursor until replay finished. |
| Terminal poison is recorded | MET. The single reject row above is terminal `http_404`, attempts 1. |
| Lock or local failure never sets `needs_reconnect` | MET. Refresh lock timeout raises `RefreshLockTimeout` and does not set the flag. |
| Watcher polled while serve was down | MET. W5 polls at 10:01:55 and 10:03:56. |
| Sender resolution per option (a), forget-by-person | MET. Rows store `sender_address_hash` and stay `unresolved`. Cleanup `forget_subject` deleted the W2 item and the reply on that thread. |
| Refresh lock, one POST | MET. The lock harness is in the workspace suite. |
| G-NO-TURN and G-ONE-OWNER | MET. Source scan in the 241. |
| Live calendar cancellation (W4) | MET. `09:36:20` calendar poll `ok=1 new=0`. `calendar_events` stayed 1040. No second item. |
| Deliberate close leaves no watcher and counts no restart | MET. `WM_CLOSE` logged `event=stop`. No `event=restart` after that stop. |
| `origin_unresolved` 0 and `echo_suspect` reported | MET. Both were 0 on every scored smoke step. |
| No content in logs, tests, or this doc | MET. Hashed ids only. |
| No Hermes edit, no install, no lore change | MET. `hermes-agent` unchanged. This progress doc is the only lore file this phase writes. |
| P10 processes untouched | MET. Process checks matched the client, the dedicated serve, and the watcher only. |

### Residuals

- The speech echo is still an accepted risk (Brian, 2026-10-13). Track 6 must resolve it.
- Series-delete match is not built. `recorded_results` has no `recurringEventId`.
- Forget-by-person misses an address known only in Contacts (sender resolution option a).
- The `needs_reconnect` resume is covered by unit tests only. No live reconnect happened.
- Brian's own sent mail is not watched (skipped as not INBOX). A "Brian replied" signal is a possible later feature.
- Calendar ids are now encoded (`#` in holiday and birthday ids), found in smoke.

Implementation commit: `27b56b59d8be5295501177914b22330bc0189aec`.
Merge commit on `main`: `05ac85f5a9634be80726cb883e94476f60e74997`.
