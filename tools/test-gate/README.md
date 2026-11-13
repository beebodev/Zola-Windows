# PROC1-GATE — one command for the test suites

## Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\test-gate\Run-TestGate.ps1
```

Optional:

| Switch | Meaning |
|--------|---------|
| `-RepoRoot <path>` | Checkout to test (default: repo containing this script) |
| `-Promote` | Also run `assembleDebug --offline` |
| `-Only a,b` | Subset only; overall is **PARTIAL** (not a pass) |
| `-UpdateFloors` | After a complete all-PASS run, raise floors (never lower) |
| `-Json <path>` | Where to write the UTF-8 (no BOM) result JSON |

## Results

| Overall | Exit | Meaning |
|---------|------|---------|
| PASS | 0 | Every suite PASS and the git tree is clean |
| FAIL | 1 | At least one suite FAIL |
| INFRA | 2 | At least one suite INFRA, no FAIL (or commit drifted mid-run) |
| DIRTY / PARTIAL | 3 | All suites PASS but tree dirty or `-Only` was used |

Suite-level **PASS** needs a completion marker, parsed counts, zero failures, passed ≥ floor, and no unexpected skips.  
**FAIL** includes real failures, below floor, unexpected skips, and **zero tests / `NO TESTS RAN` / exit 5**.  
**INFRA** means the suite could not be judged: missing tool/path, timeout, missing marker, unreadable output, or (for `zola_phone`) Zola still holding `Local\ZolaClient` or `Local\ZolaPhone`.

## INFRA — what to do

| Reason | Action |
|--------|--------|
| `stable is running; close Zola for a clean run` | Close Zola, then re-run (phone suite only) |
| `ZOLA_HERMES_ROOT (User) missing` | Set User env `ZOLA_HERMES_ROOT` to the hermes-agent checkout |
| JBR / Android SDK missing | Install Android Studio JBR / SDK; paths are in `Suites.psd1` |
| timeout | Inspect `%TEMP%\zola-test-gate\<stamp>\*.log`; raise timeout only with evidence |
| missing completion marker / stale XML | Logs and Kotlin `test-results`; gate deletes XML and uses `--rerun` |

## Notes

- The gate never starts or stops Zola.
- Checks never receive `--drift-dry-run`.
- Floors live in `floors.json` (committed). `-UpdateFloors` only raises after every suite PASS.
- Self-tests: `Test-TestGate.ps1` (also run as the `gate_self` suite).
