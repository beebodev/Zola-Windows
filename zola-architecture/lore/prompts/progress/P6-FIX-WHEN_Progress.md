# P6-FIX-WHEN Progress — Recall mentions when

## Branch

- Branch: `p6-fix-when`
- Base: `8e12ff0c8226db0cd0ec95a881eabad166f7c00b` (P6-EPISODES merge on `main`)
- Scope: live `SOUL.md` + `identity/SOUL.md` mirror + this progress note. **No** plugin/code/config changes. P4-D25.

## Status

| Step | Status |
|---|---|
| 1 Backup live SOUL | COMPLETE |
| 2 Add recall-when paragraph | COMPLETE |
| 3 Mirror + relaunch + G6 | COMPLETE |
| 4 STOP (verification) | COMPLETE — accepted Brian + Claude |
| R1–R4 retest | COMPLETE |
| Commit / merge / delete | COMPLETE |

### Verification acceptance (Brian + Claude, 2026-10-05)

> P6-FIX-WHEN verification accepted (Brian + Claude). Claude confirmed identity/SOUL.md hash e3d7bf9a… and placement. Proceed to R1–R4; cue Brian at each step. STOP after R4 with the R3 result (her exact recall answer, prefetch contents) and the merge SHA.

## Backup (P4-D25)

| Artifact | SHA-256 |
|---|---|
| Live `SOUL.md` (pre-edit) | `e2b932a9d10dd6b9267530737fe8e438c8003b74032aeb21004093fd89b24d52` |
| Backup file | `zola-spikes/p6-fix-when/SOUL.md.bak-20261005_113909` (same hash) |

## Applied text (Brian option A — pre-approved)

Own paragraph in **What I remember**, immediately after the forget paragraph:

```
When I recall something we talked about before, I mention roughly when it was, using the
dates I'm given — "this morning," "last Tuesday," "a couple of weeks ago" — and I say so
if I don't know when it happened.
```

## Hashes (post-edit)

| File | SHA-256 |
|---|---|
| Live `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` | `e3d7bf9ac29b46237a2685bebae2e89e1a5952edb23e5afeee0ee8363009fb49` |
| Repo `identity/SOUL.md` | `e3d7bf9ac29b46237a2685bebae2e89e1a5952edb23e5afeee0ee8363009fb49` (byte-equal to live) |

## G6 recheck

| Check | Result |
|---|---|
| Tools identical | ✅ (20 tools) |
| Provider tools | ✅ `['forget_memory']` unchanged |
| Prompt delta | ✅ **only** the new recall-when paragraph |

## Retest results

### R1

Session `20261005_113943_201011`: 2 pending kept.

### R2

Quiet consolidate `11:56:47` `turns=2 episodes=1`.

| Item | Result |
|---|---|
| Episode | ✅ `9d825fee…` — *Finalized the Halvorsen deck plans, selecting composite boards instead of cedar.* |
| `source_user_time` | `2026-10-05T11:46:13-07:00` |
| Notebook fact | ✅ also `5000e76b…` MEMORY `[project] The Halvorsen deck plans are finalized with composite boards rather than cedar.` |

### R3 (session `20261005_120023_d27274`) — spoken-when **FAIL**

| Check | Result |
|---|---|
| Prefetch | ✅ `retrieve candidates=1 returned=1 top_score=1.0` `prefetch returned_len=151` |
| Prefetch contents | `- talked about Mon Oct 5 (today) · happened: date unknown · Finalized the Halvorsen deck plans, selecting composite boards instead of cedar.` |
| Her exact answer | `We finalized the Halvorsen deck plans with composite boards rather than cedar.` |
| Says when? | ❌ no (“earlier today” / “this morning” / similar) |

Prefetch supplied the talked-about date; she did not voice it. Decision recall ✅; gating “when” ❌.

### R4

| Check | Result |
|---|---|
| Path | memory-tool `remove` → cascade `reason=remove fact_rows=1 episode_rows=1 pending_rows=1` `12:02:23` |
| Sanitize | `busy=0 sanitize_pending=0` |
| After | episodes **0**; Halvorsen fact gone; MEMORY no Halvorsen |
| Offline `.db` / live `.db` / `-wal` | Halvorsen/halvorsen/composite/cedar all **0** (`-wal` size 0) |
| FTS MATCH | **0** |

## Closeout SHAs

- Implementation commit: `d00161aaa3150cae6cd409ec6dc83e86d0a3fc1e`
- Merge SHA on main: `a2900eefae3b45222510962d5eb640e7641a0727`
