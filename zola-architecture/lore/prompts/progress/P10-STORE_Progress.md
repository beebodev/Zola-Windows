# P10-STORE Progress — Contract and Store

## Branch

- Primary folder: `C:\Users\test\Dev\zola-windows`, branch `main`
- Worktree: `C:\Users\test\Dev\zola-windows-p10-store`, branch `p10-store`
- Base `main` before the plan commit: `af8507fa249da957a78f5f21d5864290a3d11305` (`main` = `origin/main`)
- Plan commit (`p10-plan`, never pushed, deleted locally): `9f245622b4eb0d44ef8fb26e6f2fb35f5b3af691`
- Plan merge on `main`: `4099a18079d3a32981e95f0c077d9c492ae14b39`
- After the push: `main` = `origin/main` = `4099a18079d3a32981e95f0c077d9c492ae14b39`
- Worktree HEAD: `4099a18079d3a32981e95f0c077d9c492ae14b39`
- Hermes HEAD: `345cd2b057a452236de401d3534b8502a7465e8d` (detached `HEAD`, clean, no porcelain)
- Prompt: `P10-STORE_Prompt_v1.1.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P10-STORE_Prompt_v1.1.md`)
- Prompt SHA-256 (on-disk, 26,523 bytes): `5599aaca1a71d3f5f06e60183d813c12dd7c426bf4b3b3c7ef1383dea600fdf3`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction. On-disk value recorded for Brian to confirm.
- Scratch: `C:\Users\test\Dev\zola-spikes\p10-store\` (created, empty)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Commit the build plan, then branch | COMPLETE (STOP) |
| 2 | Grounding | COMPLETE (STOP) |
| 3 | Proposal | COMPLETE (STOP) |
| 4 | Implement | COMPLETE (STOP) |
| 5 | Review checkpoint | COMPLETE (STOP) |
| 6 | Deploy and smoke | COMPLETE (STOP) |
| 7 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** `proactive_store.py`, `phone_ids.py`, `contracts/phone_protocol.json` and golden vectors, the ranker claim filter, tests, this progress doc, the Phase 1 plan commit, and (Phase 6 only) the live plugin mirror and a migrated live `proactive.db`. A dependency-free hash-helper extraction is in scope only if the WT-G8 helper's module imports watcher, Google, or Hermes code.
- **G-ARCH:** the build plan and Appendix A/B are truth. A contradiction or a new decision stops for Brian.
- **G-PATTERN:** read every file in full before changing it.
- **G-NOCHANGE:** no `hermes-agent` edits; no client, watcher, surface, speech, loops-tool, or memory-plugin changes; no `SOUL.md`, identity, lore, or config edits; no installs. The build plan file is committed byte for byte and is not edited.
- **G-ONE-OWNER:** every write to `proactive.db` goes through `proactive_store`.
- **G-PHASE9-SAFE:** existing Gmail and Calendar rows, loops, deliveries, attempts, and watcher health survive migration with identical counts and states.
- **G-NO-CONTENT-RESTORE:** a revision never puts back removed content.
- **G-SNAPSHOT:** every copy of a live or possibly-in-use SQLite database uses `sqlite3.Connection.backup` from a read-only source. Phase 1 took no copy. The live read below was `mode=ro` and `query_only`.
- **G-HASH-CLEAN:** `phone_ids.py` imports only the standard library and the shared hash helper.
- **G-PRIVACY:** synthetic numbers and text only. This doc records counts, states, and hashes.
- **G-COMMENT:** one rationale comment per changed block.
- **G-STOP / G-CLOSEOUT / G-LORE-SCOPE / G-LIVE:** no lore edits. Live steps one at a time, Phase 6 only. Stop only processes this track started, by PID.

## Phase 1 — commit the build plan, then branch

Worktree list before the plan commit (only the primary folder; `main` was not checked out elsewhere):

```
C:/Users/test/Dev/zola-windows  af8507f [main]
```

`git status --porcelain` on that tip showed only `?? zola-architecture/lore/build-plans/PHASE10_BUILD_PLAN.md`.

`core.autocrlf` (all scopes that set it): `file:C:/Program Files/Git/etc/gitconfig` `true`. No local or global value. Not changed.

`.gitattributes` (repo root only):

```
# P3-SHELL — P3-D12
*.ttf binary
*.glb binary
```

Plan file on disk, before `git add`:

| Check | Expected | Actual |
|---|---|---|
| SHA-256 | `cd4002209ae38f44c6a338bb259453c9fec678c8d731a2272c2de57c8adc9523` | match |
| Size | 105,109 bytes | 105,109 |
| CRLF | 1,399 | 1,399 |
| Bare LF | 0 | 0 |

Staged blob (`git cat-file blob :zola-architecture/lore/build-plans/PHASE10_BUILD_PLAN.md | sha256sum`), with `core.autocrlf=true`: `fa83d8c5b50ed802907761ef6e97e67203e885a0f0d5d5da68aefc4863b3d663`. Same hash on the committed blob. Only that file was staged.

Worktree list after Phase 1:

```
C:/Users/test/Dev/zola-windows            4099a18 [main]
C:/Users/test/Dev/zola-windows-p10-store  4099a18 [p10-store]
```

Primary folder remains on `main`, clean, equal to `origin/main`. No source files modified.

### Suite counts on the new tip

Commands from each plugin directory in the worktree. `PYTHONPATH` = `C:\Users\test\Dev\hermes-agent`. Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`.

| Plugin | Command | Result |
|---|---|---|
| `zola_workspace` | `python -m unittest discover -s tests -t tests` | 335 tests, OK |
| `zola_memory` | `python -m unittest discover -s tests -t .` | 134 tests, OK |
| `zola_tools` | `python -m unittest discover -s tests -t .` | 44 tests, OK |
| `zola_tts` | `python -m unittest discover -s tests -t .` | 8 tests, OK |

Phase 9 close was 335 / 134 / 44 / 8. Phase 1 matches. Workspace printed three `ResourceWarning: unclosed file` lines for temp `zola_workspace.log` handlers. The run still exited 0.

### Live profile (read only)

Profile: `%LOCALAPPDATA%\hermes\profiles\zola`. No `-wal` or `-shm` beside `proactive.db`. The database was opened `file:` URI `mode=ro` with `PRAGMA query_only=ON`. File mtime was unchanged. Counts only.

`proactive.db` SHA-256 `1cb53fae2f4cdbdcc27e36f55cf65e8e2f5c447a47997eef488fe3b03774f923` (794,624 bytes). Schema version **5**.

| Table | Rows |
|---|---|
| calendar_events | 1052 |
| cursors | 5 |
| deliveries | 0 |
| item_attempts | 145 |
| items | 153 |
| loops | 9 |
| meta | 7 |
| watcher_health | 1 |
| watcher_rejects | 1 |

The prompt's "about 143 items and 9 loops" is the pre-count estimate. The live read is 153 items and 9 loops.

`config.yaml` SHA-256 `823dbd95c6d63eb66be07182faa82acb5c48528a79f01109b6c4120560c74afc` (4,850 bytes).

Live `plugins/zola_workspace/` (55 files):

| SHA-256 | Bytes | Path |
|---|---|---|
| `0d12b8620d3413ea95674dccd2d42f6749ed1661be4231ff7eb14e1b2702ea16` | 8972 | `__init__.py` |
| `6999d3714b13b2da6bc24c473cbf9cd56f773da4b5373da97deecb666444c431` | 9589 | `__pycache__/__init__.cpython-312.pyc` |
| `2234a8b88ee23a54d4677167b04340e3c64adfc9e5eb809be655913eec709eab` | 34451 | `__pycache__/auth.cpython-312.pyc` |
| `5c92222943a23996bb5b2b04016e74348f33c39db251e5b3b2f9a95bc13b32c7` | 14095 | `__pycache__/background_read.cpython-312.pyc` |
| `c908ad8e2d8a01a5d48cc3fda480becbe7eeec221308b07f2c7b367cd717dc4b` | 7614 | `__pycache__/contacts.cpython-312.pyc` |
| `38d97d544ffb7776023334d85f39a3ae788d5a81013714600bfbaeac073ecb97` | 20895 | `__pycache__/drive.cpython-312.pyc` |
| `04fe8c196840ac551c8f5267d5449b0cb6f205a54d15800d072e35d67605f5d1` | 1848 | `__pycache__/framing.cpython-312.pyc` |
| `3335fc84f573bcb46ffc8162bfcba89e162261d4949cc65afe04cf5bf47c566f` | 28861 | `__pycache__/gcal.cpython-312.pyc` |
| `2892a44217d81372c4a1a52a28a89dd352373392533a88406426d85a058189f4` | 46849 | `__pycache__/gmail.cpython-312.pyc` |
| `3444d36c21d4c32bf1d05717bb076210062c9f7f94abca828484c7fcdead0364` | 17743 | `__pycache__/google_http.cpython-312.pyc` |
| `56110c6a9f43203593cfc33a3e14bb7cc1701ade79fcbf6545d8f420ea557f77` | 33882 | `__pycache__/guards.cpython-312.pyc` |
| `fa1cfe275db262c75fa2a972c83d5fef0fa0a8887f97b242f4f2c0c3b4ddc40c` | 4923 | `__pycache__/log.cpython-312.pyc` |
| `e99ebe63a721fd996617e2aee573250a8fcf2676aa2722a0fe724e42c7b2bf42` | 20468 | `__pycache__/loops.cpython-312.pyc` |
| `ff0623bf569b63b6ed3c8592ec50dff29857d23a2ffa3d11892603fb9491921c` | 23156 | `__pycache__/origin.cpython-312.pyc` |
| `21f06fe209b54a8a5078cf3f30285884d7f5b19785cb10dc21cf4339bf105342` | 3264 | `__pycache__/posture.cpython-312.pyc` |
| `eacf2698303d538bc0d9dbf732e8b114c25d449d2dcd6fb4a5a941a6087a6304` | 121881 | `__pycache__/proactive_store.cpython-312.pyc` |
| `3140b8fbcd92630d991aebc3c6d3962ca0362b4942cebe1506651d1133229e52` | 33912 | `__pycache__/ranker.cpython-312.pyc` |
| `f797db7e7dcf2cf1c1288a74cd1f0094590aff1956a6d330ef0d471a2c1b1089` | 8457 | `__pycache__/read_common.cpython-312.pyc` |
| `aa2ae5fe19ae1ce6e838b96d0b6e86462022119b4528f60cb19b1d9c079ebbd3` | 7407 | `__pycache__/recorded_results.cpython-312.pyc` |
| `9fc35b058752d4618e114f4e52841240132314a37a5e4f38714ff075446f85af` | 40467 | `__pycache__/send_gate.cpython-312.pyc` |
| `6ebbcbd363d8495ea91b244d13f68f3553bc21fa988158690547e45c949542d5` | 2116 | `__pycache__/setup.cpython-312.pyc` |
| `90cf8ca1fd00a4a7ab74210d212b4086521846d8bb0e71d3a066fadb07ad2734` | 20291 | `__pycache__/speech.cpython-312.pyc` |
| `f4a0624eee48b754b8022e1251854f60c7fbb1b2c4b2afefcdc62486e4249d1d` | 55204 | `__pycache__/surface.cpython-312.pyc` |
| `5b93232b4b2e93fd294dc604e718b2217dc59de221a966e0821c2c04dfa17d42` | 9485 | `__pycache__/taint.cpython-312.pyc` |
| `e8a8702cc9b1c91e884d223d1b2db5450f0955d1ea29a8c38931674fcd94df16` | 10174 | `__pycache__/textclean.cpython-312.pyc` |
| `44dd6f9b2f22ba9c1b5ef86c52e078a2cac680ae65f4e8c40ab3889abb4d8b2d` | 10462 | `__pycache__/turn_context.cpython-312.pyc` |
| `733081c76dd4dda8c3cc823c9f681c018d033a4e6874da0bb937863a58cd5e7b` | 39174 | `__pycache__/watcher.cpython-312.pyc` |
| `be8a358e4af0eab58afe9e2c45ab18f11977436b40e7cc31e29f71354675cc8c` | 28648 | `auth.py` |
| `474f60bf942750e32f0645dd57bd06479061f3f70556c8bf0eb7c0645b82096c` | 9684 | `background_read.py` |
| `a8b29e55185dccfa404e0ee8cf9e06e84c7334e599af92f720a5cb8a436e9ac4` | 6351 | `contacts.py` |
| `b217b96909296b6f17687b793dcb702debbff110b70226f2fee8df0e980a4d57` | 221 | `contracts/proactive_methods.json` |
| `cc130131a16e1162aae2087fd175b95c1106e00f9e1ccdb630a9ea089065d64f` | 1662 | `contracts/watcher_health.json` |
| `2ef13563a57dcd6f30f72d3cf4122c54df74bf104c37ebd082476065d947cc66` | 18271 | `drive.py` |
| `0e91ffc883d42de7ac143b01d2cdbfd822b1ea34b40355d32e9924c10e3b515a` | 1552 | `framing.py` |
| `b031e31eb1d9391b1b5e7873571c7f8cdb8401c4da4e6d48b14d46372c90ed1d` | 26330 | `gcal.py` |
| `b30bc3d7376e74e221697075e1b2af7309e2642fa15e02c512944b5dbcdd1d79` | 41669 | `gmail.py` |
| `fd10cbcfd304482e850fdb6cadf9f689b6cc482c28068c93b314634e6922c67f` | 15527 | `google_http.py` |
| `29113cef52d200b26fbb2938abafab5292a1bd806c4b65c9fe9ada0fac7cde06` | 32725 | `guards.py` |
| `798fddcb60c02f46e5c4cea57974726d1ecb94880f5579d0241e1c6ff6965b83` | 3673 | `log.py` |
| `267da903d4d0b7b57f62126301d5d45ce0e9d399292a009bc95e70afe5cd7f2b` | 16256 | `loops.py` |
| `bb6ae6ac2c784e36efb3809cb494a62ed69c049cfd0010bb077cefd0fdf4c0c0` | 16193 | `origin.py` |
| `4e485461744f49222e1dd7ea378adb899b2e3c064b4dcff72f79027c96b7d738` | 199 | `plugin.yaml` |
| `e55d8e8253c5c8867c356c20a96716949dcfa22d5e5c2c9391d07219c292cda9` | 2702 | `posture.py` |
| `084c3c0d4342efbf0999066c210855e09452a4daa4b5a57eaf70486444243b15` | 109840 | `proactive_store.py` |
| `8296246ea2e9522eeab785af93db27cc7d103f7d6be4eaa2c47ee9a6f887178f` | 26066 | `ranker.py` |
| `b37cf4a91e7a211cfbc1865ac925658b28d26bd95a4b98908c4c6f926fb3f562` | 7051 | `read_common.py` |
| `1fc904077f8ecfbdd99f64a96dae92ea1915e82df5f9740f363799808a1e573f` | 5103 | `recorded_results.py` |
| `04a16292eadc8d4e0d24ab32bd99f8f4e69e90a201b592da4704b85c6a8f0c0a` | 28578 | `send_gate.py` |
| `1ffeaac4de12a47286acb2b2c9780d9c9b4e86b151802575acafbcc0712d3696` | 1356 | `setup.py` |
| `d4414dd9e59fb85706f4f0892f2ad8665fa2c8385401e8c3ff17f45ec457ed93` | 16454 | `speech.py` |
| `72be7fa1d88d5c0cadd70cece68823359aaeec0c311bc4518c73f7d078cecfbc` | 42499 | `surface.py` |
| `6390f091ca3a1ace957be7d18a80f1f926ec486fbf81025ac24b016d76cc344e` | 8520 | `taint.py` |
| `e5983ebc83858c69c0f53d473da63a78c15739cf4226453e24ef1c28928dbe64` | 6217 | `textclean.py` |
| `d857b225067f43d51dc96fb520f9da5e384d0c16298af8f722150ad95a882d03` | 8876 | `turn_context.py` |
| `6bfe0cd465cc120a9a2a6bd562951f8d66bff6dc4aeef94412bb56e4f0c4b29d` | 34262 | `watcher.py` |

## Phase 2 — grounding (2026-10-19)

Read in the worktree, no source edit: `proactive_store.py` (through line 3446), `ranker.py` (`step` and `claim_next_rank`), `loops.py`, `speech.py`, `surface.py` (header, tiers, sort), `watcher.py` (ingest and `_finish_item`), `contracts/proactive_methods.json`, `contracts/watcher_health.json`, the contract tests in `tests/test_p9_speak.py`, the one-owner scan in `tests/test_p9_store.py`, and `zola_memory/forget.py` from the marker scan through `apply_entity_proactive_forget`. Lore cited below. Scratch only: a backup-API snapshot and a failing ranker test. Live `proactive.db` mtime unchanged.

### ST-G1 — Schema 6

Schema is 5 (`proactive_store.py` line 21). `_migrate` (178–219) walks versions and raises when `meta.schema_version` is newer than `SCHEMA_VERSION` (192–195). `items.source` is `CHECK (source IN ('gmail', 'calendar'))` (228). SQLite cannot widen a CHECK. The migration rebuilds `items`, copies every old column and the same `rowid`, then renames. `PRAGMA foreign_keys` cannot change inside the migration transaction, so the rebuild turns foreign keys off before `BEGIN` and back on after `COMMIT`. `item_attempts` keeps `REFERENCES items(id)`.

`sms`, `mms`, and `notif` are further `source` values on the same `items` row as Gmail and Calendar. One row per item is what forget (2140–2155), surface (`list_surface_rows`, 3092–3108), and speech already walk. A side table would be a second place those paths must learn.

| Plan field | Where | Phase 9 rows | Why |
|---|---|---|---|
| `device_id` | `items.device_id TEXT` NULL | NULL | Install id. Gmail and Calendar have none. |
| `source` `sms` / `mms` / `notif` | widened CHECK on `items.source` | unchanged `gmail` or `calendar` | Same table as the pending list. |
| Identity (Appendix B §5) | existing `idempotency_key`, unique index `idx_items_idempotency` (265) | unchanged | One row per key. Format below. |
| `revision` | `items.revision INTEGER` NULL | NULL | Phone-assigned. |
| `completeness` | `items.completeness TEXT` NULL, CHECK `complete` / `incomplete` / `exhausted` | NULL | |
| `rcs_flag` | `items.rcs_flag TEXT` NULL, CHECK `yes` / `no` / `unknown` | NULL | |
| `sender_hash` | existing `items.sender_address_hash` | unchanged | WT-G8 column forget already matches (2144). No second hash column. |
| `sender_kind` | `items.sender_kind TEXT` NULL, CHECK `e164` / `shortcode` / `alnum` / `unparsed` | NULL | |
| `is_group`, `participant_count` | `items` INTEGER NULL | NULL | |
| Attachment metadata | `attachment_has`, `attachment_count`, `attachment_kind` | NULL | Coarse kind only. No bytes. |
| `mask_kind` | `items.mask_kind TEXT` NULL | NULL | No enum in the plan. |
| `ranking_source` | `items.ranking_source TEXT NOT NULL DEFAULT 'model'`, CHECK `model` / `code` | `'model'` | Gmail and Calendar are `model`. Phone inserts write `code`. |
| Judgment slot | `items.judgment TEXT` NULL | NULL | Reserved. No store function writes it. |
| `watch_evaluated` | `items.watch_evaluated INTEGER` NULL, CHECK NULL / 0 / 1 | NULL | ST-G8 recommendation (b). Drop the column if Brian picks (a). |
| Tombstone | table `phone_tombstones` | absent, then 0 rows | Not an item. See ST-G3. |

Identity string, unit separator `\x1f`, stored in `idempotency_key`:

- Text: `v1\x1f{device_id}\x1f{sms|mms}\x1f{provider_id}`
- Notification: `v1\x1f{device_id}\x1fnotif\x1f{package}\x1f{notification_key}\x1f{newest_message_timestamp}`

`device_id` is also its own column so a re-pair lookup does not parse the key. Provider id for a text is also `message_id`, which forget already matches (2146). Raw sender numbers are not stored: `sender_address` stays empty; only `sender_address_hash` is written (P10-D10). `detected_at` is the phone's received time for a phone row (P10-D08), not a second clock column.

Indexes: `idx_items_idempotency` is the identity lookup. New partial index `idx_items_phone_sender` on `(sender_address_hash, detected_at) WHERE source IN ('sms','mms','notif')`. Track 5 orders contacts before unknown in memory (`surface._sort_key` is tier, then `detected_at`, lines 365–374). The index is the hash-then-age fetch once serve has the contact hashes. No `is_contact` column.

Phone insert state, so the ranker and the unranked-body path do not treat them as mail: `processing='ranked'`, `eligibility='eligible'`, `label` NULL, `ranking_source='code'`, `watch_evaluated=0`. A watch match then uses `set_loop_matched` (2738–2778), because `mark_loop_eligible` requires `eligibility='pending'` (1156).

Scratch proof. Snapshot `C:\Users\test\Dev\zola-spikes\p10-store\phase2-snapshot.db`, `sqlite3` `backup()` from `file:` `mode=ro`. Live mtime unchanged. Counts below are from the snapshot. Schema before: 5. Sources: gmail 141, calendar 12.

| Table | Before | After |
|---|---|---|
| calendar_events | 1052 | 1052 |
| cursors | 5 | 5 |
| deliveries | 0 | 0 |
| item_attempts | 145 | 145 |
| items | 153 | 153 |
| loops | 9 | 9 |
| meta | 7 | 7 |
| watcher_health | 1 | 1 |
| watcher_rejects | 1 | 1 |
| phone_tombstones | absent | 0 |

Old-column fingerprints matched for every Phase 9 table except `meta`. The only `meta` change is `schema_version` 5 → 6. The other six meta keys matched the pre-migration copy. `rowid` order of `items.id` matched. Every item has `ranking_source='model'`. Every other new column is NULL on all 153 rows. `PRAGMA foreign_key_check` empty. `integrity_check` ok. Second run: schema stays 6, full-row fingerprints identical, counts identical. A copy with `schema_version` 99 raises `RuntimeError` before any DDL; fingerprints and counts unchanged; `ranking_source` absent.

State counts after migration (all `ranking_source=model`): ranked/eligible/none/delivery_uncertain/forgotten/loop-matched/closed 3; ranked/eligible/none/none/available 56; ranked/eligible/possibly_surfaced/none/available 7; ranked/eligible/selected/delivery_uncertain/forgotten/loop-matched/closed 1; ranked/eligible/selected/none/available 19; ranked/suppressed/none/none/available 67.

### ST-G2 — Revisions

One function, `ingest_phone_item`, one transaction:

1. Tombstone lookup (ST-G3). Hit → `suppressed`, no item write.
2. Bad arguments or an unknown kind → `rejected`, rollback, nothing stored.
3. No row for the identity key → insert → `stored`.
4. Same key, higher `revision` → `updated`.
5. Same key, same `revision` → `duplicate`, no write.
6. Lower `revision` → no write, log `result=ignored` with the hashed key and the two revision numbers. Not one of the five ack words. Proposal for Track 2: ack `duplicate` so the phone stops resending the older revision. Open for Brian.

`updated` while the row still holds content refreshes: `body`, `sender_display_name`, `sender_address_hash`, `sender_kind`, `is_group`, `participant_count`, `attachment_has`, `attachment_count`, `attachment_kind`, `mask_kind`, `rcs_flag`, `completeness`, `revision`, and `detected_at` (provider date can move, P10-D08). It does not change `delivery`, `conversation`, `eligibility`, `processing`, `loop_matched`, `closed_at`, `acknowledged_at`, or any attempt row.

Content is gone, and the revision writes only `revision` and `completeness`, when any of these is true: `content_state != 'available'`; `acknowledged_at` set or `conversation = 'acknowledged'`; `closed_at` set (dismiss, age-out, `close_item`). That covers acknowledgement, dismissal, closing, the 7-day purge (`content_expired`), forget redaction (`forgotten`, 2161–2170), and forget deletion (the row is gone, so a resend is a tombstone, not a revision). `acknowledge` (1270–1341) does not itself null `body`. The revision rule does not wait for the columns to be null.

### ST-G3 — Tombstones

```sql
CREATE TABLE phone_tombstones (
  identity_key_hash TEXT PRIMARY KEY,
  created_at TEXT NOT NULL
);
```

`identity_key_hash` is `address_hash` of the identity string. No other column. Ingest checks this table first. Purge deletes rows with `created_at` older than 30 days, the delivery-history bound (`DELIVERY_KEEP_DAYS`, line 45). Named constant in Phase 4: `PHONE_TOMBSTONE_KEEP_DAYS = 30`. Scratch, after the Phase 9 proof: an old synthetic hash was deleted and `new-synthetic` remained. `PRAGMA table_info` is those two columns. The one-owner regex (`tests/test_p9_store.py` 31–34) does not name this table yet. Phase 4 adds `phone_tombstones` to it.

### ST-G4 — Ranker skip

`ranker.step` (577) calls `claim_next_rank`. The candidate query is `source = 'gmail'` plus unranked, open, `content_state = 'available'`, `body IS NOT NULL` (`proactive_store.py` 966–981). `_claim_rank` repeats `row["source"] != "gmail"` (652–661). Neither mentions `ranking_source`. Calendar goes through `rank_next_calendar` (1048–1077), not this claim.

Scratch test `C:\Users\test\Dev\zola-spikes\p10-store\test_ranker_skip_fails.py`, run against this worktree. Both tests failed: `'ranking_source' not found` in `_claim_next_rank` and in `_claim_rank`. Exit code 1. The current SQL is the `source = 'gmail'` query above.

Phase 4 adds `ranking_source = 'model'` to both. It keeps `source = 'gmail'` as well. Dropping that check would let an unranked Calendar row, which is also `model`, reach the model. The plan forbids a key-prefix filter (`idempotency_key LIKE 'sms:%'`). It does not say to remove the Gmail source check.

### ST-G5 — Normalizer

`address_hash` is `proactive_store.py` 78–80: SHA-256 of `strip().casefold()` UTF-8. The module's top imports (9–16) are the standard library only. `hermes_constants` is imported inside `profile_db_path` (145–147), not at import. `watcher.py` calls it at 282 and 480. `forget.py` calls it at 1272 after the marker scan (1219–1226).

`phone_ids.py` cannot import `proactive_store` if the store also imports `phone_ids` (a cycle), and G-HASH-CLEAN allows the standard library plus the hash helper. The bad-import trigger for editing `watcher.py` is not met. Proposal: a new `address_hash.py` that imports only `hashlib`, `proactive_store.address_hash` re-exports it, and `watcher.py` stays as it is. Output stays byte-identical. Open for Brian because G-SCOPE allows that extraction only when the helper's module imports watcher, Google, or Hermes.

Recorded from the current function:

| Input | SHA-256 |
|---|---|
| `""` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `5551234567` | `3c95277da5fd0da6a1a44ee3fdf56d20af6c6d242695a40e18e6e90dc3c5872c` |
| `+15551234567` | `8a59780bb8cd2ba022bfa5ba2ea3b6e07af17a7d8b30c1f9b3390e36f69019e4` |
| `amzn` | `b923405ba2c6a80ac557a30930e6119300a1c0805536c8dd0795340970591324` |
| `ZP10-synthetic` | `783f21b98663b5d809b9503f825edcba3522161c497d102d479261d11bc87c3a` |

`phone_ids.normalize` rules, in order, after removing whitespace and punctuation other than a leading `+`: 10 digits → `e164`, `+1` prefix; 11 digits starting `1` → `e164`, `+` prefix; leading `+` and 8–15 digits → `e164`, kept; 3–6 digits → `shortcode`; any letter → `alnum`, canonical casefolded; else `unparsed`. Only `e164` is matchable. `phone_ids.hash` calls the shared helper.

| Input | Kind | Canonical | Matchable |
|---|---|---|---|
| `(555) 123-4567` | e164 | `+15551234567` | yes |
| `555-123-4567` | e164 | `+15551234567` | yes |
| `+1 555 123 4567` | e164 | `+15551234567` | yes |
| `1-555-123-4567` | e164 | `+15551234567` | yes |
| `5551234567` | e164 | `+15551234567` | yes |
| `15551234567` | e164 | `+15551234567` | yes |
| `+15551234567` | e164 | `+15551234567` | yes |
| `+44 20 7946 0958` | e164 | `+442079460958` | yes |
| `32665` | shortcode | `32665` | no |
| `AMZN` | alnum | `amzn` | no |
| empty | unparsed | empty | no |
| `junk` | alnum | `junk` | no |

`junk` is letters, so the written rule makes it `alnum`. Confirm if that input was meant to be `unparsed`.

### ST-G6 — Contract file and vectors

Same pattern as `contracts/proactive_methods.json` and `contracts/watcher_health.json`. Python locks them in `tests/test_p9_speak.py` 454–468 and 514–520 by reading the file next to the plugin. Proposal:

- `hermes-plugins/zola_workspace/contracts/phone_protocol.json` — version, frame kinds (`signed`, `pairing`), message types and fields (§6), capabilities (§2), reason codes (§9), timing (§7), size limits (§7a), identity (§5), and the pairing rule.
- `hermes-plugins/zola_workspace/contracts/phone_vectors.json` — one file of cases, like `watcher_health.json`.
- `hermes-plugins/zola_workspace/contracts/phone_test_keys.json` — fixed ECDSA P-256 keys, the string `TEST KEYS — never used outside tests` in the file. Vectors store signatures. Tests verify; they do not generate keys.

Pairing rule written into the protocol file: a re-pair of the same install keeps `device_id`. The pairing exchange (`phone_open`, `pc_bind`, `phone_bind`, `pc_ok`), MAC'd with the one-time code, is the only authorization of a replacement key for that `device_id`. After it, the old key is `unknown-key`. A frame that presents a known `device_id` signed by any other key is `unknown-key` and stores nothing.

Vectors: one valid canonical payload per signed message type, with its signature; one rejection vector per §3 reason, in §3 order (`malformed`, `unsigned`, `bad-signature`, `unknown-key`, `wrong-device`, `replay`, `stale`, `version`), plus `too-large` from §7a; three pairing vectors (re-pair keeps `device_id`, old key refused, known `device_id` with an unauthorized key refused).

A Track 3 Kotlin test reads those three paths from the repo root (`hermes-plugins/zola_workspace/contracts/`). One copy. No Android resource duplicate.

### ST-G7 — Retention for phone items

P9-D07 and SPEAK D8 (`DESIGN_DECISIONS.md` 1707–1711; purge 2228–2354): body and display fields at most 7 days (`BODY_MAX_AGE_DAYS`, `TEXT_MAX_AGE_DAYS`, lines 43–44), then ids and times. Delivery rows last 30 days and are a different table (2317–2320). Phone items are not model-ranked, so there is no body-after-ranking delete.

Phone sources in the purge, and in `acknowledge`, `dismiss_item`, and `close_item`: set `body`, `subject`, `snippet`, `gist`, `sender_display_name`, and the three attachment columns to NULL when the row is acknowledged, dismissed, closed, forgotten, or `detected_at` is older than 7 days. Then `content_state='content_expired'` when those fields are null. The `SET` list does not include `delivery`, `attempt_id`, or any `item_attempts` column. Forget already nulls body and display and sets `forgotten` (2161–2170), or deletes the row when it is not in flight (2152–2159). A later revision sees `content_state != 'available'` or `closed_at` / `acknowledged_at` and stays metadata-only (ST-G2).

### ST-G8 — Watch recovery, store side

`loops.evaluate` (232–234) is pure. The watcher calls it from `_finish_item` (`watcher.py` 186–244), then `note_loop_match_on_loop` (its own transaction, `proactive_store.py` 1964–1986, already-matched at 1972–1974) and `mark_loop_eligible` (1147–1165). `insert_item` commits on its own (509–548) before `_finish_item` (`watcher.py` 459–485).

(a) Insert and evaluation in one store transaction. Both crash points disappear: the item and the match commit together, or neither does. A crash before commit stores nothing; the phone resends; one evaluation; one match. There is no marker to save late. This needs the match writes inside the insert transaction. Those functions each issue `BEGIN IMMEDIATE`, so they cannot be called as they are. A second, locked path would be a second evaluation writer. The Track 2 kill test (kill after commit, before evaluation) has no gap to hit.

(b) `watch_evaluated` on the phone row, 0 at insert. The caller, not the store, calls `loops.evaluate` and then the existing `note_loop_match_on_loop` and `set_loop_matched`. The store lists phone rows with `watch_evaluated = 0` and sets the marker only after those calls return ok or already. A `duplicate` whose marker is still 0 runs that same sequence. A `duplicate` whose marker is 1 does not.

Crash 1: item committed, evaluation never started. Marker is 0. Startup or the resend evaluates once. `set_loop_matched` writes `loop_matched` once (2763–2765). The marker is set after that. One match. The alert is not lost.

Crash 2: match committed, marker not saved. Recovery and a later `duplicate` both see marker 0. `note_loop_match_on_loop` returns already. `set_loop_matched` returns already. No second match. Then the marker is saved. Nothing to lose; the match is already on the row.

Recommendation: (b). Track 2's crash test needs a committed item with evaluation still ahead. The store does not call `loops.evaluate`, so there is one evaluation path, the caller's, matching the watcher. `watch_evaluated` is in the scratch DDL above. Phase 9 rows are NULL and are not listed.

Gmail, report only. The same split exists: insert commits, then `_finish_item`. The cursor moves only after the page finishes without `held` (`watcher.py` 371–376). `tests/test_p9_watch.py` 352–395 plants an evaluate failure, sees the item committed, `matched_at` null, cursor unmoved, then the replay matches once and does not add a row. A hard crash in that window is the same shape while Gmail history still returns the message. There is no evaluated marker. If history no longer returns the message, the committed row stays unmatched. Not changed here.

### Open points for Phase 3

These are not decided. The scratch DDL used the recommendations so the proof matches one concrete schema.

1. `sender_hash` reuses `sender_address_hash`.
2. Identity lives in `idempotency_key` with the unit-separator format above.
3. Phone rows insert as `processing='ranked'`, `eligibility='eligible'`, `ranking_source='code'`.
4. `detected_at` is the phone received time. No `received_at` column.
5. `judgment` is the reserved column name.
6. `mask_kind` and `attachment_kind` are unconstrained text.
7. Lower revision is store result `ignored`, and the ack word is `duplicate`.
8. Ranker filter adds `ranking_source = 'model'` and keeps `source = 'gmail'`.
9. ST-G8 (b), including `watch_evaluated`.
10. Extract `address_hash` into its own module and re-export it, leaving `watcher.py` unchanged.
11. `junk` normalizes to `alnum`.
12. Contract files are `phone_protocol.json`, `phone_vectors.json`, and `phone_test_keys.json`.

## Phase 3 — Proposal (STOP, 2026-10-19)

No source file was changed. The positions below are Claude's recommendations from the Phase 3 start message. They become decisions when Brian records verdicts. Everything else in Phase 2 stands. The scratch snapshot remains the schema-6 proof: 153 items, counts unchanged, idempotent, schema 99 refused. That scratch DDL left `mask_kind` and `attachment_kind` as unconstrained text. The DDL in this proposal adds the CHECKs in point 6. Every Phase 9 value is NULL, which both CHECKs allow.

### Schema 6

Rebuild `items` (SQLite cannot alter a CHECK). Foreign keys off before `BEGIN`, on after `COMMIT`, because `item_attempts` references `items`. Copy old columns and `rowid`, recreate the saved indexes, then:

- `source` CHECK `gmail`, `calendar`, `sms`, `mms`, `notif`
- `device_id TEXT` NULL
- `revision INTEGER` NULL
- `completeness TEXT` NULL CHECK `complete`, `incomplete`, `exhausted`
- `rcs_flag TEXT` NULL CHECK `yes`, `no`, `unknown`
- `sender_kind TEXT` NULL CHECK `e164`, `shortcode`, `alnum`, `unparsed`
- `is_group INTEGER` NULL CHECK `0`, `1`
- `participant_count INTEGER` NULL
- `attachment_has INTEGER` NULL CHECK `0`, `1`
- `attachment_count INTEGER` NULL
- `attachment_kind TEXT` NULL CHECK `image`, `video`, `audio`, `other`
- `mask_kind TEXT` NULL CHECK `verification_code`, `reset_link`, `unsure`
- `ranking_source TEXT NOT NULL DEFAULT 'model'` CHECK `model`, `code`
- `judgment TEXT` NULL, reserved, written by nothing
- `watch_evaluated INTEGER` NULL CHECK `0`, `1`

Phase 9 rows receive `ranking_source = 'model'` and NULL in every other new column. Partial index `idx_items_phone_sender` on `(sender_address_hash, detected_at) WHERE source IN ('sms','mms','notif')`.

`items` has `detected_at`, `updated_at`, `ranked_at`, `eligible_at`, `closed_at`, `selected_at`, `acknowledged_at`, and `attempt_at` (`proactive_store.py` 255–258 and the v4 adds at 367–375). `created_at` exists on `item_attempts` (273) and `loops` (281), not on `items`. `updated_at` is rewritten on later writes, so it is not a durable store-time. This proposal adds no store-time column. Retention and age ordering use `detected_at`.

### Ingest

`ingest_phone_item`, one transaction. The store calls `phone_ids.normalize` on the raw sender and hashes that canonical. A caller-supplied hash is not an argument.

1. Identity field contains U+001F → `rejected`, nothing stored.
2. Tombstone hit → `suppressed`, nothing stored.
3. Bad arguments, unknown kind, unknown `mask_kind`, or unknown `attachment_kind` → `rejected`, nothing stored. NULL mask and NULL attachment kind are allowed.
4. No row → insert → `stored`. Insert state: `processing='ranked'`, `eligibility='eligible'`, `label` NULL, `ranking_source='code'`, `watch_evaluated=0`, `sender_address` empty.
5. Higher `revision` → `updated`.
6. Equal `revision` → `duplicate`, no write.
7. Lower `revision` → no write, log `result=ignored`. Ack word to the phone: `duplicate`.

`updated` while content is present refreshes `body`, `sender_display_name`, `sender_address_hash`, `sender_kind`, `is_group`, `participant_count`, `attachment_has`, `attachment_count`, `attachment_kind`, `mask_kind`, `rcs_flag`, `completeness`, `revision`, `detected_at`. It leaves `delivery`, `conversation`, `eligibility`, `processing`, `loop_matched`, `closed_at`, `acknowledged_at`, and attempt rows alone.

Metadata-only (`revision` and `completeness`) when `content_state != 'available'`, or `acknowledged_at` is set, or `conversation = 'acknowledged'`, or `closed_at` is set.

Identity in `idempotency_key`, unit separator, version prefix `v1`:

- Text: `v1` + U+001F + `device_id` + U+001F + `sms` or `mms` + U+001F + provider id
- Notification: `v1` + U+001F + `device_id` + U+001F + `notif` + U+001F + package + U+001F + notification key + U+001F + newest message timestamp

`phone_protocol.json` states that U+001F cannot occur in any identity field. Provider id is also `message_id`. `device_id` is its own column.

### Tombstones

`phone_tombstones (identity_key_hash TEXT PRIMARY KEY, created_at TEXT NOT NULL)`. Hash of the identity string. Checked first. Purge at 30 days (`PHONE_TOMBSTONE_KEEP_DAYS`). Phase 4 adds the table name to the one-owner regex.

### Ranker

`_claim_next_rank` (966–981) and `_claim_rank` (652–661) both keep `source = 'gmail'` and add `ranking_source = 'model'`.

### Normalizer

`phone_ids.normalize`, after removing spaces:

1. Punctuation other than a leading `+` removed, and the remainder is digits: 10 digits → `e164` `+1…`; 11 digits starting with `1` → `e164` `+…`; leading `+` and 8–15 digits → `e164` kept; 3–6 digits → `shortcode`.
2. Otherwise, if what remains after removing spaces is 1–11 letters and digits, at least one letter, and no other character → `alnum`, canonical casefolded.
3. Otherwise `unparsed`. Canonical is the space-stripped casefold. Matchable is false.

Only `e164` is matchable. Hash input is that canonical, never the raw sender. `junk` → `alnum` `junk`. `abc!@#def` and `hello-world-123456` → `unparsed`. The plan's other inputs stay as in the Phase 2 table.

`address_hash.py` imports `hashlib` only. `proactive_store.address_hash` re-exports it. `phone_ids` imports that module and the standard library. `proactive_store` imports `phone_ids` for ingest, so `phone_ids` cannot import the store. `watcher.py` stays as it is. Recorded hashes in Phase 2 must match.

### Contract

`contracts/phone_protocol.json`, `contracts/phone_vectors.json`, `contracts/phone_test_keys.json`. Protocol includes the pairing rule, the U+001F ban, and the `mask_kind` and `attachment_kind` enums. Vectors: one valid signed payload per message type; one rejection per Appendix B §3 in order, plus `too-large`; three pairing vectors. Test keys carry the label `TEST KEYS — never used outside tests`. Kotlin reads the same repo paths.

### Retention

Phone content (`body`, `subject`, `snippet`, `gist`, `sender_display_name`, attachment columns) is cleared on acknowledge, dismiss, close, forget, or when `detected_at` is older than 7 days. Then `content_state='content_expired'` once those fields are null. Delivery and attempt rows stay. A later revision is metadata-only.

### ST-G8

Option (b). `watch_evaluated=0` at insert. The store lists phone rows still at 0 and sets the marker only after `note_loop_match_on_loop` and `set_loop_matched` return ok or already. The store does not call `loops.evaluate`. Crash 1 evaluates once. Crash 2 gets already, then saves the marker. Phase 4 tests both.

### Point 13 — conversation and speech hold

Phone rows inserted as `ranked` / `eligible` / `loop_matched=1` would enter today's conversation. `list_surface_rows` (3092–3110) returns every open row. `_tier` (surface.py 249–251) treats `loop_matched` as the loop tier. `_line_for` (316–331) then uses the mail sentence, including "A watched thread has new mail" when gist is empty. `whats_pending` reads the same list (surface.py 931–932). `claim_next_speech` (1460–1478) would claim that row. `speech.claim_for_client` (227–240) is that claim. `post_speech_candidate` (3398–3412) would hand a delivered phone row back into the next note.

One constant, `PHONE_CONVERSATION_HOLD = ("sms", "mms", "notif")`. Track 5 removes it and every predicate that uses it. Until then, `source NOT IN` that tuple on:

- `list_surface_rows`
- `_claim_next_speech` select and update
- `_claim_speech` update, and `_speech_block_reason` returns `phone_deferred`
- `post_speech_candidate`
- `provisional_select` (the writer that attaches a row to a turn)

Retention, forget, `source_ids_for`, and the ranker skip still include phone rows. The ranker predicate stays `ranking_source = 'model'` plus `source = 'gmail'`, separate from this constant.

Test: a phone row with `loop_matched=1` and `eligibility='eligible'` is absent from `list_surface_rows` and `post_speech_candidate`, `claim_next_speech` returns nothing from it, `claim_speech` on its id returns `phone_deferred`, and `provisional_select` refuses. A Gmail row in the same state is still listed and still claimable.

Readers checked:

| Reader | Lines | Feeds conversation or speech | Hold |
|---|---|---|---|
| `list_surface_rows` | 3092–3110 | yes: pre-llm note and `whats_pending` | yes |
| `_claim_next_speech` | 1460–1478 | yes: `speech.claim_for_client` | yes |
| `_claim_speech` | 1380–1419 | yes, by id; the client method rejects a caller item id (speech.py 233–234) | yes |
| `post_speech_candidate` | 3387–3417 | yes: the note after speech | yes |
| `list_open_items` | 2059–2068 | no; state only; callers are tests (`test_p9_store.py` 357, `test_p9_rank.py` 213) | no |
| `list_open_loops` | 2028 | loops | no |
| `list_untold_lapses` | 3119 | loop lapse ids | no |
| `open_loop_source_ids` | 3354 | loop source ids for the pending list | no |
| `list_open_loop_predicates` | 2693 | watcher matching | no |
| `source_ids_for` | 2207 | forget | no; must see phone rows |
| `_claim_next_rank` / `_claim_rank` | 966, 652 | model ranking | no; point 8 |
| `rank_next_calendar` | 1048 | calendar ranking | no |
| `_item` | 438 | by-id fetch after a claim (`speech._name_for_item` 184) | no; the claim is already held |
| purge, forget, acknowledge, dismiss | 2144+, 2228+ | retention and forget | no; must see phone rows |

`surface.py` and `speech.py` stay unchanged. They only see rows the store returns.

### Phase 4 tests

Migration on a schema-5 fixture (counts, states, idempotent, unknown version refused). Identity. Revisions, including no content restore after ack, dismiss, 7-day purge, redaction, and forget. Tombstone suppress, 30-day expiry, no content column. Ranker skip passes and a Gmail item is still claimed. Normalizer table plus `abc!@#def`, `hello-world-123456`, and the 1–11 alnum rule; only `e164` matchable; ingest hashes the canonical. Vectors and the pairing rule. Phone retention leaves delivery and claim state. Both ST-G8 crash points. Hash source scan and the recorded hashes. Point 13 hold, with a Gmail control row. Unknown mask and attachment kinds rejected. U+001F in an identity field rejected. One-owner scan green, including `phone_tombstones`. Suite counts against 335 / 134 / 44 / 8.

### Risks

The hold is a temporary gate. A new reader added before Track 5 can leak a phone row into the mail sentence unless it uses the constant. `list_open_items` still returns phone ids and states, with no body. A wrong phone clock moves retention, because age uses `detected_at`. An alphanumeric sender longer than 11 characters is `unparsed` and cannot match a contact. The hash extraction is past the written G-SCOPE trigger; the reason is the import cycle, and `watcher.py` is not edited.

### Decisions for Brian

Record each verdict verbatim. Recommended position in parentheses.

1. Reuse `sender_address_hash`. Hash the canonical, never the raw sender. (agree)
2. Identity in `idempotency_key`, `v1` and U+001F. The contract bans that character in identity fields. Ingest rejects a frame that contains it. (agree)
3. Phone insert: `processing='ranked'`, `eligibility='eligible'`, `ranking_source='code'`, together with the point 13 hold. (agree)
4. `detected_at` is the phone received time. `items` has no store-time column. Add none. Retention and ordering use `detected_at`. (agree)
5. Reserved column name `judgment`. (agree)
6. `mask_kind` CHECK `verification_code`, `reset_link`, `unsure`, or NULL. `attachment_kind` CHECK `image`, `video`, `audio`, `other`, or NULL. Unknown value → `rejected`, nothing stored. Same enums in `phone_protocol.json`. (agree; this replaces the unconstrained text in Phase 2)
7. Lower revision: store result `ignored`, ack `duplicate`. (agree)
8. Ranker: `ranking_source = 'model'` and `source = 'gmail'`, in both claim sites. (agree)
9. ST-G8 (b), `watch_evaluated`. Phase 4 tests both crash points. (agree)
10. Extract `address_hash` to `address_hash.py`, re-export from `proactive_store`, leave `watcher.py` unchanged. Recorded hashes must match. (agree)
11. `alnum` is 1–11 letters and digits after removing spaces, at least one letter, no other character. `junk` stays `alnum`. `abc!@#def` and `hello-world-123456` are `unparsed`. Ingest normalizes; callers cannot pass a hash. (agree)
12. Contract files `phone_protocol.json`, `phone_vectors.json`, `phone_test_keys.json`. (agree)
13. `PHONE_CONVERSATION_HOLD` on the readers and on `provisional_select` listed above. Track 5 removes it. Refusal reason `phone_deferred`. (agree)

### Verdicts

> Approve all 13 as recommended.

Recorded 2026-10-19. All thirteen recommended positions are the decisions Phase 4 builds.

## Phase 4 — Implement (2026-10-19)

Built the approved proposal. `address_hash.py` holds the WT-G8 hash. `proactive_store.address_hash` re-exports it. `watcher.py` is unchanged. `phone_ids.py` normalizes and hashes through that module. Schema 6 rebuilds `items` with foreign keys off around the drop, then sets `ranking_source='model'` on existing rows. `ingest_phone_item` is the phone write. Tombstones, the conversation hold, phone retention, and `watch_evaluated` are in the store. The ranker claim keeps `source='gmail'` and adds `ranking_source='model'`.

`tests/test_p9_surface.py` now expects `SCHEMA_VERSION` after the v3 upgrade, which is 6. The one-owner scan includes `phone_tombstones`.

Workspace 349 OK (335 at Phase 1, plus 14 in `test_p10_store.py`). Memory 134 OK. Tools 44 OK. TTS 8 OK. Live profile not migrated.

## Test counts per phase

| Phase | workspace | memory | tools | tts |
|---|---|---|---|---|
| 1 | 335 OK | 134 OK | 44 OK | 8 OK |
| 4 | 349 OK | 134 OK | 44 OK | 8 OK |
| 5 | 356 OK | 134 OK | 44 OK | 8 OK |
| 5 F8 | 357 OK | 134 OK | 44 OK | 8 OK |
| 7 | 357 OK | 134 OK | 44 OK | 8 OK |

## Migration, live hashes after change, smoke

Fixture migration is covered by `test_p10_store.py`: a schema-5 row keeps its old columns, `ranking_source` becomes `model`, `truncated` is NULL, a second connect changes nothing, and schema 99 is refused. Live `proactive.db` is not migrated. That waits for Phase 6.

Phase 5 re-ran the proof with the backup API and the real store migration, after the `truncated` column was in the schema 6 rebuild. Scratch copy: `C:\Users\test\Dev\zola-spikes\p10-store\phase5-snapshot.db`. Live file was opened `mode=ro` only.

| Check | Before | After |
|---|---|---|
| Live schema | 5 | 5 (not migrated) |
| Live mtime and size | recorded | unchanged |
| Snapshot schema | 5 | 6, and a second connect stays 6 |
| items | 155 | 155 |
| item_attempts | 147 | 147 |
| loops | 9 | 9 |
| calendar_events | 1052 | 1052 |
| cursors | 5 | 5 |
| deliveries | 0 | 0 |
| meta | 7 | 7 |
| watcher_health | 1 | 1 |
| watcher_rejects | 1 | 1 |
| phone_tombstones | absent | 0 |
| `truncated` NULL | column absent | 155 of 155 |
| `ranking_source` | absent | `model` 155 |
| sources | gmail 143, calendar 12 | same |
| integrity_check | | ok |
| foreign_key_check | | 0 rows |

## Residuals

- Prompt comparison SHA was not in the Phase 1 instruction.
- Phase 1 read live `items` 153. The Phase 5 read-only snapshot is 155 (gmail 143, calendar 12) and `item_attempts` 147. Loops are still 9. Schema is still 5.
- Phase 2 and Phase 5 scratch snapshots stay in `C:\Users\test\Dev\zola-spikes\p10-store\` until closeout. They are copies of the live store. The progress doc has counts only.
- Gmail's commit-then-evaluate gap is reported under ST-G8. This track does not change the watcher.
- Phase 6 smoke left one synthetic `phone_tombstones` row (hash and created time only). It ages out at 30 days. There is no single-row delete.

## Discrepancies

None that block Phase 6. The approved 1–11 `alnum` rule is what the tests lock. `junk` is `alnum`. The live store gained two Gmail rows between the Phase 5 snapshot (155) and the Phase 6 backup (157), and one more during smoke (158). That is the watcher. Schema was 5 until this phase migrated it.

## Phase 5 fixes F1–F7 from Claude's review

Recorded 2026-10-19 as Brian's Phase 5 instruction. Header verbatim. The seven fixes are applied. Nothing else. `watcher.py` is unchanged. Not committed. Live profile not migrated.

`python -m zola_workspace.watcher --help` is not a safe entry: `__main__` calls `main()`, which polls. The package test imports `zola_workspace.proactive_store`, `zola_workspace.phone_ids`, and `zola_workspace.watcher` with only `hermes-plugins` on `PYTHONPATH`, from a directory that is not the plugin folder.

| Fix | Before the change | After |
|---|---|---|
| F1 | Subprocess exit 1. `import address_hash` raised `ModuleNotFoundError` while loading the package. | Exit 0. `package-import-ok`. |
| F2 | The second `_migrate_v6_committed` raised `sqlite3.OperationalError: index idx_items_phone_sender already exists`. | The second call is a no-op. Schema is 6 once. Item count unchanged. A dangling `item_attempts.item_id` raises `RuntimeError`, rolls back, and leaves schema 5 with no `phone_tombstones`. |
| F3 | The new open-loop test passed on the current code. The existing expiry UPDATE already sets `content_expired` after the 7-day nulls, and a higher revision does not restore the body. `closed_at` stays null because the loop is open. | Same test passes. Purge and `_clear_phone_content_locked` now share one empty-content condition. |
| F4 | `completeness='incomplete'` returned `stored`. | `rejected` / `bad_completeness`. Nothing stored. The schema CHECK still allows `incomplete`. |
| F5 | `phone_protocol.json` had no `ingest_reject_reasons` (`KeyError`). | Each of the ten reasons once. Nothing stored. |
| F6 | `proactive_store` had no `TEXT_BODY_CHARS`. | Limits are read from `size_limits`. A body over the limit is `rejected` / `too_large`. `truncated` is on the schema 6 rebuild. Phase 9 rows are NULL. |
| F7 | `555123456²` normalized to `e164`. | `555123456²` and `٥٥٥١٢٣٤٥٦٧` are `unparsed`. |

Workspace 356 OK (349 at Phase 4, plus 7). Memory 134 OK. Tools 44 OK. TTS 8 OK.

STOP. To continue: proceed to phase 6.

## F8 — v6 writes 6, not SCHEMA_VERSION

Recorded 2026-10-19 before the Phase 6 deploy. `_migrate_v6_committed` compared against and wrote `SCHEMA_VERSION`. A later schema 7 would let a racing opener stamp `7` without running the v7 step, and the re-check would no longer skip a store already at 6.

The v6 step now uses `SCHEMA_V6 = 6`: re-check `>= SCHEMA_V6`, write `"6"`. `_migrate` still uses `SCHEMA_VERSION` for the newer-than-supported check. `needs_v6` uses `SCHEMA_V6`.

Failing first, with `SCHEMA_VERSION` patched to 7: a version-5 fixture was written as `"7"` (`AssertionError: '7' != '6'`), and a version-6 fixture re-ran the rebuild (`sqlite3.OperationalError: index idx_items_phone_sender already exists`). After the constant, both cases leave the schema at 6 and the second is a no-op.

Workspace 357 OK. Memory 134 OK. Tools 44 OK. TTS 8 OK.

## Phase 6 — Deploy and smoke (2026-10-19)

No `Zola.Client` process and no `python.exe` from the Hermes venv were running. Other `python.exe` processes were Blender MCP, not Hermes. Cursor then started the client with the prompt's command: `dotnet run --project C:\Users\test\Dev\zola-windows-p10-store\windows-client\Zola.Client\Zola.Client.csproj`.

One client, one serve, and one watcher. On Windows the venv `python.exe` spawns the base interpreter, so each role is a parent and a child.

| Role | PID | Parent | Started | Command |
|---|---|---|---|---|
| client | 25552 | 10632 | 15:26:20 | `Zola.Client.exe` |
| serve | 3704 | 25552 | 15:26:23 | Hermes venv `python.exe -m hermes_cli.main -p zola serve --isolated` |
| serve interpreter | 22020 | 3704 | 15:26:23 | base `python.exe` for that serve |
| watcher | 19064 | 25552 | 15:26:23 | Hermes venv `python.exe -m zola_workspace.watcher` |
| watcher interpreter | 7768 | 19064 | 15:26:23 | base `python.exe` for that watcher |

`zola_watcher.purge bodies=0 texts=0 deliveries=0 loops=0` at 15:26:24. `zola_watcher.poll source=gmail ok=1 new=0` at 15:26:25. `zola_watcher.poll source=calendar ok=1 new=0` at 15:26:27. The ranker logged `zola_workspace.ranker … ok=1` after the relaunch.

### Backup and mirror

Backup API copy: `C:\Users\test\Dev\zola-spikes\p10-store\phase6-proactive-before.db`, SHA-256 `acc870a5a9fd496dfea9d87cac503c77da8c6ef5c380f0c2a5648d1408038379`. Live plugin tree copied to `phase6-plugin-before` before the mirror. Live `config.yaml` stayed `823dbd95c6d63eb66be07182faa82acb5c48528a79f01109b6c4120560c74afc`. `watcher.py` was not copied; its live hash still matches the worktree.

Backup schema 5. Counts: items 157 (gmail 145, calendar 12), item_attempts 149, loops 9, calendar_events 1052, cursors 5, deliveries 0, meta 7, watcher_health 1, watcher_rejects 1.

Mirrored files, live SHA-256 equal to the worktree:

| File | SHA-256 |
|---|---|
| `proactive_store.py` | `b57520f02ae9c6fb408977de16a466557fcae7740e5aa208df52158785912d26` |
| `address_hash.py` | `e109ebd62fffceed93202d72ebbac03743f7300de744569352ea9704564d000e` |
| `phone_ids.py` | `b3dc4c27cb4b780a0e489644c774849e64e78296e8cf41f350ed8b101d14e316` |
| `contracts/phone_protocol.json` | `17a0e960de59ece64ddbce58152b70cb658cc268e19142ab1799a32f3a02f5a2` |
| `contracts/phone_vectors.json` | `3637f724c6aaf5edbd720f9aa6077ea815efa79210b2adc8b936a7c437f13c08` |
| `contracts/phone_test_keys.json` | `365f34e744c0477702b1bfb593640cd763bd514b3c02c165780c295e51f2cf77` |

Migration used the mirrored `proactive_store.connect`, `retry=False`. Schema 6. A second connect stayed 6. Counts unchanged, plus `phone_tombstones` 0. `ranking_source` is `model` on all 157. Every new phone column is NULL on all 157, including `truncated`. Old item columns fingerprint unchanged. Other tables unchanged. Meta unchanged except `schema_version`. Integrity ok. Foreign-key check empty. `config.yaml` unchanged.

### Smoke

One synthetic SMS through `ingest_phone_item` (`555` sender, `ZP10-` body, synthetic device id). Over the next ranker cycle the workspace log grew, `ranker_progress_at` moved, and the row stayed `processing=ranked`, `ranking_source=code`, `delivery=none`, `eligibility=eligible`, with 0 attempts. Its item hash was not in the new ranker lines.

`forget_subject` with that provider id as the source id, ticket override set in the harness because this was not a client turn: `items_deleted=1`, row gone. The same identity ingested again: `suppressed`. No phone rows remain. Gmail is 146 and calendar is 12; the extra Gmail row arrived from the watcher during the wait. Items 158.

`phone_tombstones` is 1. Columns are `identity_key_hash` and `created_at` only. The store deletes tombstones inside `purge_retention` once they are 30 days old. A purge clocked far enough ahead to delete this fresh row would also age live mail, so that was not run. The synthetic tombstone stays until the watcher's normal 30-day purge.

No `ZP10-synthetic`, `5551234567`, `15551234567`, `zp10-device-smoke`, or `zp10-smoke` in the profile logs.

STOP. To continue: proceed to closeout.

## Phase 7 — Closeout (2026-10-19)

### 7a evidence

| Check | Result |
|---|---|
| Suites | workspace 357 OK, memory 134 OK, tools 44 OK, tts 8 OK |
| Live mirror vs worktree | `proactive_store.py`, `address_hash.py`, `phone_ids.py`, the three phone contract files, and `watcher.py` all MATCH |
| `hermes-agent` | clean at `345cd2b057a452236de401d3534b8502a7465e8d` |
| `proactive.db` in the repo | absent (`git ls-files` has none) |
| `watcher.py` vs `main` | byte-identical |
| Scratch backups | kept until 7i under `C:\Users\test\Dev\zola-spikes\p10-store\` |

### Exit criteria

| # | Criterion | Evidence |
|---|---|---|
| 1 | ST-G1–G8 answered; STOP verdicts recorded | Phase 2 grounding, Phase 3 proposal, verdicts: `Approve all 13 as recommended.` |
| 2 | Suites pass; migration on a live copy keeps Phase 9 rows | Phase 5 and Phase 6 backup-API proofs; Phase 6 live migrate: counts unchanged, old columns fingerprint unchanged |
| 3 | Identity, revision, duplicate, lower ignored, tombstone, ranker skip, normalizer, vectors | `tests/test_p10_store.py` |
| 4 | No Google, model, or phone code touched | Diff is store, hash helper, phone_ids, contracts, tests, progress doc only |
| Plan committed byte for byte | Plan commit `9f245622…`, merge `4099a180…`, blob hash recorded in Phase 1 |
| G-NO-CONTENT-RESTORE | Revision tests after ack, dismiss, purge, redact, forget |
| Both ST-G8 crash points | `WatchRecoveryTests` |
| G-HASH-CLEAN and recorded hashes | Import scan + `RECORDED_HASHES` |
| Backup API for every DB copy | Phase 2, 5, 6 scratch scripts |
| Live migration + smoke | Phase 6 section |
| No installs; no Hermes, client, watcher, or lore change | Diff and `watcher.py` unchanged |
| No content in logs | Phase 6 grep: no matches |

### Brian's verdicts (verbatim)

> Approve all 13 as recommended.

### SHAs

| Item | SHA |
|---|---|
| Plan commit (`p10-plan`) | `9f245622b4eb0d44ef8fb26e6f2fb35f5b3af691` |
| Plan merge on `main` | `4099a18079d3a32981e95f0c077d9c492ae14b39` |
| Implementation (7c) | *(filled after 7c)* |
| Merge of `p10-store` (7f) | *(filled after 7f)* |

### Residuals after closeout

- Prompt comparison SHA was never supplied in Phase 1.
- Live item counts moved with Gmail during the track (Phase 1: 153 → Phase 5 snapshot: 155 → Phase 6 backup: 157 → after smoke: 158). Schema is 6 after Phase 6.
- One synthetic `phone_tombstones` row remains from smoke (hash + created time). Ages out at 30 days.
- Gmail watcher still commits then evaluates in a separate transaction (ST-G8 report only). This track did not change the watcher.
