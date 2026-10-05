# P6-FIX-2 Progress — last weekend + episodes say-when cue

## Branch

- Branch: `p6-fix-2`
- Base: `3515a65beeafe57a80efa27d47209f78fd7a4154` (FIX-WHEN docs on `main`, clean)
- Scope: `hermes-plugins/zola_memory/` (`consolidate.py`, `retrieve.py`, tests) + this progress note. P4-D25 for live deploy. **MERGE ONLY ON R6 PASS.**

## Status

| Step | Status |
|---|---|
| Build (phrase + cue + tests) | COMPLETE — verified Brian + Claude |
| Deploy (P4-D25) | COMPLETE — cue Brian Ashford |
| Today Ashford seed + interval confirm | COMPLETE |
| R6 one-time test seed (deviation) | COMPLETE — kiln times −1 day |
| R6 kiln recall | **PASS** |
| Forget + byte-scan | COMPLETE |
| Merge | COMPLETE |

## Build

### 1 — `last weekend` phrase table

- Resolves to Sat–Sun whose Sunday is the most recent Sunday **strictly before** the turn's local date.
- Stored `event_time`: ISO interval `YYYY-MM-DD/YYYY-MM-DD`; basis `stated`; evidence `last weekend`.
- `time_unresolved` / `phrase_not_in_table` no longer for this phrase.
- Retrieval: `happened: the weekend of Oct 3–4 (last weekend)` — relative by Sunday (`last weekend` when that Sunday is still the most recent before *now*; else day/week buckets).

### 2 — Episodes-block cue (exact)

```
[Episodes — past conversations. If you use one, mention roughly when it was (e.g. "yesterday", "last week").]
```

Replaces `[Episodes]`. Nothing else in the line format changes.

### Suites

| Suite | Result |
|---|---|
| `zola_memory` | **109 OK** |
| `zola_tools` | **44 OK** |

### Repo hashes

| File | SHA-256 |
|---|---|
| `consolidate.py` | `1b2d8d8ad8140ec515d184279dd3bd541952918025adedf47761944ae14941c2` |
| `retrieve.py` | `53d8044d896f6f769aa10ef99bab67083adf19aa3e01858a067a870916c0290d` |
| `tests/test_episodes_phase4.py` | `082b664dad4326332af3b43ee39b2b0efcfdce5063e232a2e2519c5e1cc0fd05` |

### Diff summary

- `consolidate.py`: +`last weekend` → interval
- `retrieve.py`: `EPISODES_BLOCK_HEADER`; interval display via `format_weekend_happened`
- tests: Mon/Sat/Sun + month boundary + DST weekend; display at +1d / +10d / +3w; header exact text

**FIX-2 BUILD COMPLETE.** Verified and deployed (below).

### Deploy (2026-10-05)

| Item | Result |
|---|---|
| Backup | `zola-spikes/p6-fix-2/backup_20261005_124017/` — DB `f7950729…` (200704 B; episodes=1 kiln intact); plugin folder copied |
| Live files | `consolidate.py` / `retrieve.py` MATCH repo |
| Relaunch | Client **19488**; serve **20788→13372**; `store_open pid=13372 schema_version=2 secure_delete=1` |
| G6 | tools **20** unchanged; provider `['forget_memory']`; episodes cue **not** in system prompt (prefetch-only) ✅ |
| Kiln episode | `c2a99319…` untouched |

### Brian — Ashford (today, new conversation)

1. `Last weekend I repainted the trim on the Ashford shed.`
2. Wait **≥10 quiet minutes**, say **done**.

### Ashford result (session `20261005_124024_4a930a`)

Quiet consolidate `12:51:56` `turns=1 episodes=1` — **no** `time_unresolved`.

| Field | Value |
|---|---|
| Episode | `2c7d9d6e…` — *Brian repainted the trim on the Ashford shed last weekend.* |
| `event_time` | ✅ `2026-10-03/2026-10-04` |
| `event_time_basis` | ✅ `stated` |
| `event_time_evidence` | ✅ `Last weekend` |
| Kiln | ✅ `c2a99319…` untouched |

**Retrieval line (would produce):**
```
[Episodes — past conversations. If you use one, mention roughly when it was (e.g. "yesterday", "last week").]
- talked about Mon Oct 5 (today) · happened: the weekend of Oct 3–4 (last weekend) · Brian repainted the trim on the Ashford shed last weekend.
```

### Deviation — R6 one-time test seed (Brian approved, 2026-10-05)

Not a natural cross-day result. Client closed; no Hermes held the store; DB backed up; **only** kiln episode `c2a99319…` had `source_user_time` and `recorded_at` moved back exactly 1 day (same clock, `-07:00`). No other rows/columns/FTS/facts. Commit + `wal_checkpoint(TRUNCATE)`.

| Item | Value |
|---|---|
| Backup | `zola-spikes/p6-fix-2/backup_r6seed_20261005_125855/zola_memory.db` |
| Backup SHA-256 | `8b199f264f74f6d7df6a24afe85d2fe3d1ddb3777dff39a51fb0205bbf1c8aa8` (208896 B) |
| Episode | `c2a99319-3793-4638-907d-27675f05aa0c` |
| `source_user_time` | `2026-10-05T12:07:59-07:00` → `2026-10-04T12:07:59-07:00` |
| `recorded_at` | `2026-10-05T12:18:21-07:00` → `2026-10-04T12:18:21-07:00` |
| Ashford `2c7d9d6e…` | untouched |
| Relaunch | Client **14956**; serve **18616→20380**; `store_open pid=20380` `schema_version=2` `secure_delete=1` |

**Offline retrieval** (deployed `retrieve.py` `53d8044d…`, copy of live DB, query *What did we decide about the Calderon kiln?*):
```
[Episodes — past conversations. If you use one, mention roughly when it was (e.g. "yesterday", "last week").]
- talked about Sun Oct 4 (yesterday) · happened: date unknown · Booked the Calderon kiln for a cone 6 glaze firing, rather than cone 10.
```

### Brian — R6 (new conversation; after seed)

1. `What did we decide about the Calderon kiln?`
2. Say **done** (+ exact answer). PASS = “yesterday” or Oct 4 / the date.
3. On PASS: forget kiln + Ashford; Cursor byte-scans then merges `p6-fix-2`. On FAIL: STOP, no merge.

### R6 result (session `20261005_125907_2e549d`) — **PASS**

| Check | Result |
|---|---|
| Prefetch | ✅ `retrieve candidates=1 returned=1 top_score=1.0` `prefetch returned_len=246` |
| Prefetch contents | `[Episodes — past conversations. If you use one, mention roughly when it was (e.g. "yesterday", "last week").]` + `- talked about Sun Oct 4 (yesterday) · happened: date unknown · Booked the Calderon kiln for a cone 6 glaze firing, rather than cone 10.` |
| Her exact answer | `You booked the Calderon kiln for a cone 6 glaze firing next week—not cone 10. We settled that yesterday.` |
| Says when? | ✅ “yesterday” |

### Cleanup (post-PASS)

| Check | Result |
|---|---|
| Cascade | `reason=r6_pass_cleanup fact_rows=2 fts_rows=6 episode_rows=2 pending_rows=1 link_rows=4 entity_rows=2 ok=true` |
| After | episodes **0**; kiln + Ashford facts gone; MEMORY lines removed |
| Offline/live `.db` / `-wal` | Calderon/Ashford/kiln/cone 6/cone 10/glaze firing all **0** (`-wal` size 0) |

### Merge

- Implementation commit: *(filled at commit)*
- Merge SHA on main: *(filled at merge)*
