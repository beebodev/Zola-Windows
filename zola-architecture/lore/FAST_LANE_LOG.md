# Fast-lane log

SOP v3 (PR-D07). Small, contained fixes that skip audit, build plan, and lore closeout; reconciled into lore at the next phase's lore closeout.

## Rules (PR-D07)

Eligible only if **all** hold:
- one Cursor prompt;
- no new decision needed;
- no change to architecture, authority, permissions, privacy or memory structure;
- no change to a safety gate;
- a small, contained set of files.

Still required: its own branch, the full test gate (plus a test for the fix), the behavioral scenarios in the area it touches, Claude's review of the result, a `--no-ff` merge, a tag, and an entry in this log.

Skipped: audit, build plan, and lore closeout (the log is reconciled at the next phase's lore closeout).

**Stable hotfix:** branches from the current stable tag, promoted on the developer's approval, and then merged into main, where the full test gate runs again.

Brian (PR-D07 verdict): "Small, contained fixes shouldn't need the full SOP."

## Entries

No fast-lane fixes since SOP v3 adoption (2026-11-06); S51F-FIX, the PROC1 tracks and S51M-FIX ran in the full lane.

**S51M-FIX note:** full-lane hotfix with early promotion (PR-D09). It needed a new decision (S51M-D1) and changed memory concurrency — both outside fast-lane eligibility.
