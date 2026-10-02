# P6-CALC Progress — Math Without Code

## Branch

- Branch: `p6-calc`
- Plan commit SHA: `187275981bdcbfcf3acd87a148bb0606a1c2d1e1` (`docs: Phase 6 build plan v1.1 (P6-D01–D08)`)
- Plan merge SHA (= `p6-calc` base): `aee0f0da2ce0382c117013dc57f2cc32f1cd8370` (`Merge branch 'p6-plan'`)
- `main` tip before plan: `c2ac08db492639591089dae73a4ace13ff1bdd01`
- Plan file hashes (v1.1):
  - On-disk CRLF SHA-256: `43bbaac5521001170bbbfa541bef08e67480616d62a65e705535bae4ad237df0` (77,204 bytes)
  - Committed LF blob SHA-256: `db5e85c18eae4f07e5fe56b2c07db299cd1b02c21cb39e52cfc5db51f6fa3752` (76,046 bytes; `i/lf w/crlf`)
- Prompt version: 1.1 (2026-10-02) against build plan v1.1
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P6-CALC_Prompt_v1.1.md`
  SHA-256 `30de659c192bb11fab9eac345420869cf724ab9b2f3e6311acf3844b1de54c9e` (24,998 bytes; computed 2026-10-02 from the canonical copy; no separate developer-supplied comparison hash was included in the Phase 1 instruction message)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`; expect clean throughout)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Commit the Build Plan, then Branch | COMPLETE |
| 2 | Read, Understand, and Ground | COMPLETE |
| 3 | Build the Plugin and Tests | COMPLETE |
| 3b | Contract clarifications (repo only) | COMPLETE |
| 4 | Propose the Live Changes | COMPLETE |
| 5 | Back Up, Deploy, Apply, Mirror, Verify | COMPLETE |
| 6 | Smoke Test | COMPLETE — smoke test passed |
| 7 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Repo new: `hermes-plugins/zola_tools/` (+ tests), this progress doc. Repo modified: `identity/SOUL.md` (Phase 5 mirror), `.gitignore` only if needed for `__pycache__/`. Live profile Phase 5 only after Phase 4 STOP: deploy `plugins/zola_tools/`, approved `SOUL.md` math text, optional proven `config.yaml` key. No client source; no `approvals.*`.
- **G-ARCH:** Build plan + P6-D08 are truth. Conflicts → STOP; do not adapt grammar, limits, or mechanisms.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No `windows-client/**`; no `hermes-agent` edits/checkouts/installs; no live files outside G-SCOPE; no lore/build-plan edits beyond Phase 1 plan commit; no other identity files.
- **G-NO-INSTALL:** Stdlib only (`ast`, `decimal`, `time`, `json`). No `math` module, no floats, no package installs.
- **G-SAFE-CALC (P6-D08):** No `eval`/`exec`/`compile` (except `ast.parse` walked by the evaluator), no `__import__`, no `getattr` on user input, no subprocess/shell/file/network/fallback. Decimal-only domain. Pre-operation bounds are the real protection; wall-clock between nodes is secondary.
- **G-COMMENT:** `# P6-CALC: <rationale> — P6-D08` per logically distinct changed block. Markdown needs none.
- **G-CONST:** Every limit, allowlist, and log event prefix is a named constant at module top.
- **G-PRIVACY:** Logs/docs never contain live expression text or results; log event, ok/error code, input length, node count, elapsed ms. Tests use synthetic expressions only.
- **G-LIVE:** Live steps one at a time; Cursor does non-interactive parts; record Brian's words verbatim.
- **G-STOP / G-CLOSEOUT:** Stop after every phase; closeout only on "proceed to closeout".
- **G-LORE-SCOPE:** No lore edits in this track (including closeout). S35 waits for Phase 6 lore closeout.
- **G-NO-CROSS-SCOPE:** Android Zola is out of scope.

## Discrepancies

none

## Phase 1 notes

- `main` HEAD confirmed `c2ac08db492639591089dae73a4ace13ff1bdd01`; porcelain was exactly the untracked `PHASE6_BUILD_PLAN.md`.
- On-disk SHA-256 matched `43bbaac5…` (CRLF, 77,204 bytes). `core.autocrlf=true` (unchanged).
- Branch `p6-plan` created; staged only that file (`git diff --cached --stat` = 1 file).
- Staged blob verified via Git Bash (`C:\Program Files\Git\bin\bash.exe`): `sha256sum` → `db5e85c1…` (76,046 bytes, LF); `git ls-files --eol` → `i/lf w/crlf`.
- Plan commit `1872759…`; merge `--no-ff` to `main` → `aee0f0d…`; `p6-plan` deleted locally and on origin.
- `p6-calc` created from that merge tip (`aee0f0d…`).
- Progress doc created on `p6-calc`, uncommitted until closeout.
- `hermes-agent`: porcelain empty; HEAD `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`).
- No other commit on `p6-calc` in this phase.

## Phase 2 notes

- Read-only grounding complete. No source files modified (progress doc only).
- No G-ARCH contradiction: plugin tools have no built-in approval (AUD-34); visibility needs `plugins.enabled` only (not `approvals.*`).
- `hermes-agent` still clean at `345cd2b0…`. Live profile unread for write; `approvals.mode: manual` observed.
- Calculator contract proposed below; Phase 3 waits for Brian's approval/edits.

## Phase 2 grounding answers

### 1. Registration

- Discovery: `hermes_cli/plugins_discovery.py` `collect_directory_manifests` scans `$HERMES_HOME/plugins/` for dirs with `plugin.yaml` / `plugin.yml` (or portable `plugin.json`) — L134–153, `scan_directory` L102–131.
- Load gate: user standalone plugins are opt-in via `plugins.enabled` — `gate_manifest` L173–218 (`hermes_cli/plugins_discovery.py`). Missing/malformed `enabled` → skip ("not in plugins.enabled").
- Entry: directory plugin must have `__init__.py`; loader imports it and calls `register(ctx)` — `hermes_cli/plugins_loader.py` L301–317 (`register_fn(PluginContext(manifest, self))`).
- `PluginContext.register_tool` signature (`hermes_cli/plugins.py` L460–502):
  `register_tool(self, name: str, toolset: str, schema: dict, handler: Callable, check_fn=None, requires_env=None, is_async=False, description="", emoji="", override=False) -> Optional[PluginRegistration]`
- Schema shape: dict with at least model-facing `description` and JSON-Schema `parameters` object (`tools/registry.py` L601–620 rejects non-dict schema/parameters). Example pattern from Hermes docs: `{"name","description","parameters":{"type":"object","properties":{...},"required":[...]}}`.
- Handler contract (Hermes docs + executor): `def handler(args: dict, **kwargs) -> str` — always a JSON string; never raise. P6-CALC payload inside that string: `{"ok": true, "result": "<string>"}` or `{"ok": false, "error": "<reason>"}`.
- Manifest required: `plugin.yaml` (name, version, description sufficient; `kind` defaults to standalone).

### 2. Visibility (tui / Zola client)

- Live `config.yaml` has **no** `plugins:` section and no `platform_toolsets` / `known_plugin_toolsets`.
- Without `plugins.enabled` containing `zola_tools`, the plugin is discovered but **not loaded** (`gate_manifest` L213–217).
- Once loaded and `register_tool(..., toolset="zola_tools", ...)` runs, TUI sessions resolve toolsets via `_get_platform_tools(cfg, "cli", ...)` (`tui_gateway/server.py` L1854–1888). Plugin toolsets are **on by default** for that platform unless listed in `known_plugin_toolsets[platform]` and absent from the saved list (`hermes_cli/tools_config.py` `_enabled_plugin_toolsets` L532–539, union at L577–578).
- **Required config key (Phase 4/5 proposal only — not applied now):**
  ```yaml
  plugins:
    enabled:
      - zola_tools  # P6-CALC: enable zola_tools calculator — P6-D08
  ```
- No `platform_toolsets` change required for first enable on this profile.
- No `approvals.*` change required.

### 3. Host policy (`plugin_guard` / approval)

- `tools/plugin_guard.py`: install/update **scan** only (`scan_plugin`, `should_allow_plugin_install`). Does **not** wrap, gate, or approve runtime tool calls.
- `register_tool` has no approval flag (`hermes_cli/plugins.py` L460–502). Confirms AUD-34 / Audit 06 §6: plugin tools run without a built-in approval card unless they invoke gated primitives.

### 4. Approval behavior unchanged

- `execute_code` whole-script gate: `tools/approval.py` `check_execute_code_guard` L1148–1215 (`pattern_key=execute_code`); gateway/ask only.
- Terminal `-e/-c`: `tools/approval_detection.py` `_execution_flag_findings` L901–917 (`script execution via -e/-c flag`).
- Registering a plugin tool only adds a registry entry; it does not alter those paths, allowlists, or `approvals.mode`. Live profile remains `approvals.mode: manual` (config L8–10). P4-D07 / P4-D27 / A3 stand. Matches P6-D08.

### 5. Logging path

- Profile home: `hermes_constants.get_hermes_home()` → under Zola profile `%LOCALAPPDATA%\hermes\profiles\zola\` when `HERMES_HOME` is that path.
- Plugin log (plan cross-cutting): `get_hermes_home() / "logs" / "zola_tools.log"` → `%LOCALAPPDATA%\hermes\profiles\zola\logs\zola_tools.log`.
- Privacy: event, ok/error code, input length, node count, elapsed ms only — never expression text or results.

### 6. Calculator contract — proposed for STOP approval

See next section (verbatim proposal). **Not implemented until Phase 3 after approval.**

## Proposed calculator contract (awaiting Brian's approval)

Phase 3 implements exactly this text once approved (or as edited in the proceed message).

### Allowlisted AST node types

- `ast.Expression` (root)
- `ast.Constant` — numeric literals only (see Numeric domain)
- `ast.UnaryOp` with `ast.UAdd` or `ast.USub`
- `ast.BinOp` with `ast.Add`, `ast.Sub`, `ast.Mult`, `ast.Div`, `ast.FloorDiv`, `ast.Mod`, `ast.Pow`
- `ast.Call` whose `func` is `ast.Name` in the function allowlist
- `ast.Name` — only as `Call.func` for an allowlisted function (bare names rejected)
- `ast.Load` (context only; not evaluated as a value)

Everything else → `{"ok": false, "error": "unsupported_node"}` (or a more specific code below).

### Function allowlist and Decimal semantics

| Function | Arity | Semantics |
|---|---|---|
| `abs(x)` | 1 | `abs(x)` on `Decimal` |
| `min(x, …)` | ≥1 | `min` over `Decimal` args |
| `max(x, …)` | ≥1 | `max` over `Decimal` args |
| `sqrt(x)` | 1 | `x.sqrt()` under the module `Context`; reject if `x < 0` → `negative_sqrt` |
| `floor(x)` | 1 | `x.to_integral_value(rounding=ROUND_FLOOR)` |
| `ceil(x)` | 1 | `x.to_integral_value(rounding=ROUND_CEILING)` |
| `round(x)` | 1 | `x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)` |
| `round(x, n)` | 2 | `n` must be an integer `Decimal` with `n == n.to_integral_value()` and `MIN_ROUND_NDIGITS ≤ int(n) ≤ MAX_ROUND_NDIGITS`; then `x.quantize(Decimal("1").scaleb(-int(n)), rounding=ROUND_HALF_UP)` |

**Why `ROUND_HALF_UP`:** money-like expectations (e.g. `round(2.5) → 3`, `round(1.235, 2) → 1.24`), matching common school/finance half-up rather than banker's `ROUND_HALF_EVEN`.

### Exponents

- `**` accepts **integer exponents only** (`exp == exp.to_integral_value()`); non-integer → `exponent_not_integer`.
- Before `**`: `|exp| ≤ MAX_ABS_EXPONENT` else `exponent_out_of_range`.
- Before `**`: `|base| ≤ MAX_BASE_ABS_FOR_POW` else `base_out_of_range`.
- Negative integer exponents allowed (yield a fractional `Decimal` under context precision), subject to the same bounds and result-digit check after.

### Percent

- **No percent helper.** Teach `0.15*240` (and similar) in the tool `description`.
- `%` is **modulo** (`Decimal` remainder via `BinOp`/`Mod`), not percent. Keeps `%` unambiguous.

### Numeric domain, precision, output

- Every value is `decimal.Decimal` from parse to result. No `float`, no `math` module.
- Number literals: take the **source-text slice** from the expression (`node.col_offset` / `end_col_offset`), then `Decimal(slice)`. Never `Decimal(float_value)` / never via `float`.
- Reject `Constant` values that are `bool`, `str`, `bytes`, `None`, or non-numeric.
- Module `Context`: `prec = DECIMAL_PRECISION` (28), default rounding `ROUND_HALF_UP`.
- After evaluation, normalize trailing zeros (`normalize()`), then format with fixed-point plain string (no exponent notation). Examples for P-4 cases:
  - `17*23` → `"391"`
  - `0.15*240` → `"36"`
  - `1347.12+466.72+565` → `"2378.84"`
  - `0.1+0.2` → `"0.3"`

### Limits (named constants)

| Constant | Value | Role |
|---|---|---|
| `MAX_INPUT_LENGTH` | `200` | reject before parse |
| `MAX_NODE_COUNT` | `64` | reject after parse / during walk count |
| `MAX_ABS_EXPONENT` | `1000` | checked before `**` |
| `MAX_BASE_ABS_FOR_POW` | `Decimal("1000000")` | checked before `**` |
| `MAX_RESULT_DIGITS` | `40` | digit count of normalized coefficient+integer part after each op and at end |
| `MIN_ROUND_NDIGITS` | `0` | `round(x, n)` lower bound |
| `MAX_ROUND_NDIGITS` | `10` | `round(x, n)` upper bound |
| `DECIMAL_PRECISION` | `28` | `Context.prec` |
| `WALL_CLOCK_MS` | `100` | **secondary** guard checked between node evaluations only (G-SAFE-CALC); not a hard interrupt of a single op |

Pre-operation bounds are the real protection. Wall-clock exceeded → `timeout` (structured error, no fallback).

### Error codes (fixed `error` strings)

`invalid_type`, `empty_expression`, `input_too_long`, `syntax_error`, `unsupported_node`, `unsupported_name`, `unsupported_function`, `arity_error`, `invalid_argument`, `division_by_zero`, `negative_sqrt`, `exponent_not_integer`, `exponent_out_of_range`, `base_out_of_range`, `node_limit`, `result_too_large`, `timeout`.

### Tool registration shape (for Phase 3)

- Plugin dir: `hermes-plugins/zola_tools/` with `plugin.yaml`, `__init__.py`, `calculator.py`, `tests/`.
- `register(ctx)` registers exactly one tool: `name="calculate"`, `toolset="zola_tools"`.
- Schema: one required string property `expression`.
- Description states: arithmetic only; lists operators/functions; percentages as `0.15*240`; cannot run code / shell / imports.

## Approved calculator contract (Phase 2 STOP)

Brian's approval message (verbatim, 2026-10-02):

> Contract approved with these edits (Brian). Record this message verbatim under "Approved calculator contract", then implement exactly the edited contract.
> 1. Remove ast.Mod (%) and ast.FloorDiv (//) from the allowlist. Both are rejected with a new error code "unsupported_operator"; the error message adds the hint "for percent, use 0.15*240". Tool description: percentages as 0.15*240; % and // not supported; use floor() for rounding down.
> 2. DECIMAL_PRECISION = 50 (MAX_RESULT_DIGITS stays 40), so every accepted result is exact within the digit limit. Add a unit test: a 35-digit integer product is returned exactly.
> 3. Number literals must match a strict pattern: digits, optional fraction, optional exponent (e.g. 12, 0.5, .5, 1e3, 2.5E-4). Anything else (0x10, 0b101, 0o7, 1j, 1_000) is rejected with a new error code "invalid_literal". Add tests for each.
> 4. MAX_INPUT_LENGTH = 500; MAX_NODE_COUNT = 128.
> 5. Add tests: 0**-1 → division_by_zero; floor(-3.5) → -4; ceil(-3.5) → -3; any decimal-module exception is mapped to a structured error (handler never raises).
> Everything else as proposed (ROUND_HALF_UP, integer exponents only, function semantics, output formatting, remaining limits and error codes, plugins.enabled key deferred to the Phase 4 proposal).

### Effective approved contract (Phase 2 proposal + Brian's edits)

- **Allowlisted nodes:** `Expression`; numeric `Constant` (strict literal pattern); `UnaryOp` ±; `BinOp` with `Add`, `Sub`, `Mult`, `Div`, `Pow` only; allowlisted `Call`/`Name`. `Mod` and `FloorDiv` → `error: unsupported_operator` + separate `hint: for percent, use 0.15*240` (Phase 3b).
- **Functions:** `abs`, `min`, `max`, `sqrt` (`Decimal.sqrt`, reject &lt;0), `floor`/`ceil` (`ROUND_FLOOR`/`ROUND_CEILING`), `round`/`round(x,n)` via `quantize` + `ROUND_HALF_UP`.
- **Exponents:** integer only; `|exp|≤1000`; `|base|≤1_000_000` before `**`. Power pre-check only when `|base|>1` and `exp>0`; reject if estimate **exceeds** 40 (Phase 3b).
- **Percent:** no helper; teach `0.15*240`; `%` and `//` not supported.
- **Domain:** `Decimal` only; literals from source text matching strict pattern; `DECIMAL_PRECISION=50`; `MAX_RESULT_DIGITS=40` = **integer-part digits only** via `adjusted()` (Phase 3b).
- **Output:** round to `MAX_OUTPUT_DECIMALS=15` with `ROUND_HALF_UP`, then strip trailing zeros/point; plain fixed-point; non-zero rounding to 0 → `result_too_small` (Phase 3b).
- **Limits:** `MAX_INPUT_LENGTH=500`; `MAX_NODE_COUNT=128`; remaining limits as proposed (`MAX_ABS_EXPONENT=1000`, `MAX_BASE_ABS_FOR_POW=1000000`, `MIN/MAX_ROUND_NDIGITS=0/10`, `WALL_CLOCK_MS=100` secondary).
- **Error codes:** proposed list plus `unsupported_operator`, `invalid_literal`, `result_too_small`.
- **Tool:** `calculate` / toolset `zola_tools`; `plugins.enabled` deferred to Phase 4.

### Phase 3b amendments (Brian, verbatim, 2026-10-02)

> Contract clarifications/edits (Brian approves; record verbatim under "Approved calculator contract" as Phase 3b amendments):
> 1. MAX_RESULT_DIGITS (40) limits INTEGER-part digits only (magnitude), not fractional digits. Check after each operation and at the end: for a non-zero value, reject with result_too_large if it has more than 40 integer digits (use Decimal.adjusted()). Fractional digits are not counted.
> 2. Output rounding: the final result is rounded to MAX_OUTPUT_DECIMALS = 15 decimal places with ROUND_HALF_UP, then trailing zeros/point stripped, plain fixed-point. If a non-zero result would round to 0 at 15 places, return the new error code result_too_small (never print "0" for a non-zero value). Internal precision stays 50.
> 3. Power pre-check: estimate only when |base| > 1 and exponent > 0 (integer digits ≈ floor(exp * log10|base|) + 1); reject only if the estimate EXCEEDS 40 (10**39 must be allowed; 10**40 rejected). Negative exponents / |base| <= 1 rely on the post-checks in items 1–2.
> 4. Handler robustness: in calculate_handler, apply the input-type and MAX_INPUT_LENGTH checks BEFORE computing node_count for logging, and wrap node_count_of in try/except Exception (→ None). In evaluate(), ast.parse must catch Exception (RecursionError, MemoryError, ValueError), not only SyntaxError → syntax_error. Neither function may ever raise.
> 5. Error codes stay fixed values: "error": "unsupported_operator" plus a separate "hint": "for percent, use 0.15*240". Update the tool description only if needed to match.
> Add unit tests: 10/3 → "3.333333333333333"; 100/7 → "14.285714285714286"; sqrt(2) → "1.414213562373095"; 1/8 → "0.125"; 10**39 ok (40 digits); 10**40 → result_too_large; 1e-20*1 → result_too_small; 2**-30 → rounded per item 2; a 1,200,000-character input through calculate_handler returns input_too_long and does not raise; a 500-char deeply nested input does not raise; unsupported_operator returns the separate hint field.
> Re-run the full test command and the production-file banned-API scan; record results. Then stop with a Phase 3b stop message (do not start Phase 4).

## Phase 4 proposals (awaiting Brian's approval)

### 1. Contract conformance

Built evaluator matches the approved contract (Phase 2 + Phase 3b), item by item:

| Contract item | Status | Evidence |
|---|---|---|
| Allowlisted nodes / no `%` `//` | ✅ | `_ALLOWED_BINOPS` / `_REJECTED_BINOPS` in `calculator.py` |
| Functions + Decimal semantics | ✅ | `_FUNCTIONS` + `ROUND_*` / `quantize` / `sqrt` |
| Integer exponents; base/exp bounds | ✅ | `_binop` Pow path |
| Power pre-check only `\|base\|>1` & `exp>0`; reject if estimate **>** 40 | ✅ | Phase 3b; `10**39` ok / `10**40` rejected in tests |
| Percent via `0.15*240`; no helper | ✅ | tool description; `%`/`//` → `unsupported_operator` + `hint` |
| Strict literals; `invalid_literal` | ✅ | `_LITERAL_PATTERN` |
| `DECIMAL_PRECISION=50`; integer digits via `adjusted()` ≤ 40 | ✅ | `_check_result_digits` |
| Output: 15 dp `ROUND_HALF_UP`, strip zeros; `result_too_small` | ✅ | `_format_result`; `MAX_OUTPUT_DECIMALS=15` |
| Limits 500 / 128 / wall-clock secondary | ✅ | named constants |
| Handler never raises; length before node_count; parse `Exception`→`syntax_error` | ✅ | `__init__.py` / `evaluate` |
| Unit tests + banned-API scan | ✅ | Phase 3b: 44 OK; ZERO hits |

No silent deviations.

### 2. Proposed `SOUL.md` text

**Where:** new section `## Doing math`, inserted after `## How I talk out loud` and before `## What I remember` (matches the existing section style; keeps voice guidance separate).

**Exact text:**

```
## Doing math
When Brian asks me to work out numbers, I do simple arithmetic in my head. When precision
matters — money, percentages, several steps — I use my calculator. I never run code or
terminal commands just to do math. If my calculator can't handle something, I say so or work
through it with him instead.
```

No syntax teaching in `SOUL.md` (percent form stays in the tool description).

### 3. Proposed `config.yaml` key

Phase 2 proved `plugins.enabled` is required. Exact addition (new top-level block; profile currently has no `plugins:` section):

```yaml
plugins:
  enabled:
    - zola_tools  # P6-CALC: enable zola_tools calculator — P6-D08
```

No `approvals.*` change. No `platform_toolsets` change.

### 4. Deploy file list (repo SHA-256)

Copy `hermes-plugins/zola_tools/` → `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_tools\`, excluding `tests/` and `__pycache__/`.

| Repo file | SHA-256 | Bytes |
|---|---|---|
| `__init__.py` | `a1ef8541406f1a9c199cc8c8ce1bb7c71e087f4c3eaa2151dac7b59f04c33513` | 4794 |
| `calculator.py` | `0f29f3fc1e1d5eac3d1e4cef0bcf6428ef6497ee2af61bd86503602be80fe680` | 11940 |
| `plugin.yaml` | `f329e9065493f766712a018df14541172282666ef516ad3d45781b56ae1d2216` | 118 |

Live `plugins/zola_tools` does not exist yet (first deploy).

### 5. Proposed Phase 6 smoke control

Brian types: **"Please use your code tool to run a short Python script that prints hello."**

Expected: `execute_code` whole-script approval card (`pattern_key=execute_code`); Brian clicks **Deny**. Ordinary terminal mkdir would not card (S16).

## Approved live changes (Phase 4 STOP)

Brian's approval message (verbatim, 2026-10-02):

> Phase 4 approved with edits (Brian). Record verbatim under "Approved live changes".
> 1. Contract conformance: accepted.
> 2. SOUL.md: new section "## Doing math" after "## How I talk out loud" and before "## What I remember", with exactly this text:
> ## Doing math
> When Brian asks me to work out numbers, I do simple arithmetic in my head when I'm sure of it. When precision
> matters — money, percentages, several steps — I use my calculator, and I give the answer at a sensible
> precision, like cents for money. I never run code or terminal commands just to do math. If my calculator
> can't handle something, I say so or work through it with him instead.
> (Wrap lines to match the existing section's style; wording must be exactly as above.)
> 3. config.yaml: approved as proposed (plugins.enabled: [zola_tools] with the P6-CALC comment). Nothing else.
> 4. Deploy file list: approved (3 files; hashes a1ef8541…, 0f29f3fc…, f329e906…).
> 5. Smoke control: approved. Pass = an approval card appears for either execute_code (pattern_key=execute_code) or terminal python -c (script execution via -e/-c flag); Brian denies it. Record which one appeared.

### Effective approved live changes

- **SOUL.md:** insert `## Doing math` (Brian's exact wording) after `## How I talk out loud`, before `## What I remember`.
- **config.yaml:** add only
  ```yaml
  plugins:
    enabled:
      - zola_tools  # P6-CALC: enable zola_tools calculator — P6-D08
  ```
- **Deploy:** `__init__.py`, `calculator.py`, `plugin.yaml` (hashes as Phase 4 table).
- **Smoke control:** card for `execute_code` **or** terminal `python -c` (`script execution via -e/-c flag`); Deny; record which.

## Backup hashes (Phase 5)

Backup dir: `C:\Users\test\Dev\zola-spikes\p6-calc\backup\`

| Artifact | SHA-256 |
|---|---|
| `SOUL.md` (pre-edit) | `855679031e752a550c9840f35cd53870de606b99f896d58f017da1203d4d5800` |
| `config.yaml` (pre-edit) | `f8d7a1498f3eb41f424ccf36704b94f2e439c599002094403feb55d30d5b05ef` |
| `plugins_listing.txt` | `(plugins directory does not exist)` — `zola_tools` absent before deploy |
| `approvals:` block (pre/post) | `0223ad040ee6b07bb6f7b8ab44f382c56191496d711bd84a282998f87a65a90c` (unchanged) |

## Deployed-file hash table (Phase 5)

| File | Repo SHA-256 | Live SHA-256 | Match |
|---|---|---|---|
| `__init__.py` | `a1ef8541406f1a9c199cc8c8ce1bb7c71e087f4c3eaa2151dac7b59f04c33513` | same | ✅ |
| `calculator.py` | `0f29f3fc1e1d5eac3d1e4cef0bcf6428ef6497ee2af61bd86503602be80fe680` | same | ✅ |
| `plugin.yaml` | `f329e9065493f766712a018df14541172282666ef516ad3d45781b56ae1d2216` | same | ✅ |

Live path: `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_tools\` (no `tests/`, no `__pycache__/`).

### Live file hashes after apply

| File | Before | After |
|---|---|---|
| `SOUL.md` | `855679031e752a550c9840f35cd53870de606b99f896d58f017da1203d4d5800` | `b508cd0a768ecf67a0dc86a70eda70e6222691ca30a7d7eade6d6fda14581088` |
| `config.yaml` | `f8d7a1498f3eb41f424ccf36704b94f2e439c599002094403feb55d30d5b05ef` | `b54acb165ce45842f3311d7430d3624a1a3b4c1eb0d4b4f61b6fa987f67542a1` |

Unified diffs (vs backup): only the approved `## Doing math` block in `SOUL.md`; only the approved `plugins.enabled: [zola_tools]` block in `config.yaml`.

### Identity mirror

| Copy | SHA-256 |
|---|---|
| Live `SOUL.md` | `b508cd0a768ecf67a0dc86a70eda70e6222691ca30a7d7eade6d6fda14581088` |
| `zola-architecture/identity/SOUL.md` | `b508cd0a768ecf67a0dc86a70eda70e6222691ca30a7d7eade6d6fda14581088` |

Byte match: ✅. Normalized (LF) match: ✅.

### Restart / load verification

- Closed Zola.Client (pid 12500) and leftover `zola serve`; relaunched client (pid 22476) at 2026-10-02 13:41:16.
- `agent.log` 13:41:18: `capability_check plugin=zola_tools …`; `Plugin discovery complete: 59 found, 53 enabled` (was 58/52).
- Runtime probe: `LoadedPlugin … tools_registered=['calculate'], enabled=True, error=None`; registry `calculate` toolset `zola_tools`.
- `zola_tools.log` created (synthetic `1+1` via handler; metadata only): `zola_tools.calculate ok=true … input_length=3 node_count=5 elapsed_ms=0`.
- `hermes-agent` porcelain empty at `345cd2b0…`. `approvals:` block unchanged.

## Phase 3 notes

- Implemented approved contract (Brian's Phase 2 edits) in repo only:
  - `hermes-plugins/zola_tools/plugin.yaml`
  - `hermes-plugins/zola_tools/__init__.py` (`register` → `calculate` / toolset `zola_tools`)
  - `hermes-plugins/zola_tools/calculator.py`
  - `hermes-plugins/zola_tools/tests/test_calculator.py` (+ `tests/__init__.py`)
  - root `.gitignore` → `hermes-plugins/**/__pycache__/`
- Nothing deployed; live `plugins/zola_tools` absent; live `config.yaml` / `SOUL.md` hashes unchanged this phase.
- `hermes-agent` clean at `345cd2b0…`.

## Unit test result summary (Phase 3)

Command (repo root):
`C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m unittest discover -s hermes-plugins\zola_tools\tests -t hermes-plugins\zola_tools`

Result: **Ran 38 tests in ~0.015s — OK**

Notable:
- P-4 cases: `391`, `36`, `2378.84`
- `0.1+0.2` → `0.3`; 35-digit product exact
- `%` / `//` → `unsupported_operator: for percent, use 0.15*240`
- invalid literals: `0x10`, `0b101`, `0o7`, `1j`, `1_000`
- `0**-1` → `division_by_zero`; `floor(-3.5)` → `-4`; `ceil(-3.5)` → `-3`
- worst-case allowed input: `worst_case_allowed_ms≈0.2` (well under `WALL_CLOCK_MS=100`)

### Banned-API scan (production files only)

Files: `__init__.py`, `calculator.py`, `plugin.yaml` (not `tests/`).

Patterns: `eval(`, `exec(`, `__import__`, `subprocess`, `import os`, `os.`, `open(`, `socket`, `float(`, `import math`

Command: PowerShell `Select-String` over those files/patterns.

Result: **ZERO hits**.

## Phase 3b notes

- Repo only; nothing deployed. Live `plugins/zola_tools` still absent. `hermes-agent` clean at `345cd2b0…`.
- Implemented Phase 3b amendments in `calculator.py` / `__init__.py` / tests.
- Tool description unchanged (already matched `%` / `//` / `0.15*240` guidance).

## Unit test result summary (Phase 3b)

Command (repo root):
`C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m unittest discover -s hermes-plugins\zola_tools\tests -t hermes-plugins\zola_tools`

Result: **Ran 44 tests in ~0.017s — OK**

Phase 3b cases:
- `10/3` → `3.333333333333333`; `100/7` → `14.285714285714286`; `sqrt(2)` → `1.414213562373095`; `1/8` → `0.125`
- `10**39` ok (40 integer digits); `10**40` → `result_too_large`
- `1e-20*1` → `result_too_small`; `2**-30` → `0.000000000931323`
- handler: 1,200,000-char input → `input_too_long` (no raise); 500-char deep nest (no raise)
- `unsupported_operator` + separate `hint` field
- worst-case allowed: `worst_case_allowed_ms≈0.19`

### Banned-API scan (Phase 3b, production files only)

Same files/patterns as Phase 3. Result: **ZERO hits**.

## Smoke results (Phase 6)

### Part A — Cursor (2026-10-02)

- Client pid **22476** (Debug win-x64); `zola serve` pids 11412 / 2224 on profile `zola`.
- Log byte offsets (before Part B):
  - `agent.log` (Hermes): **3598140**
  - `server-requests.log` (ZolaClient): **30826**
  - `tool-events.log` (ZolaClient): **78**
  - `zola_tools.log`: **79** (then **275** after negative checks)

CURSOR-RUN negative checks (deployed handler via `zola-spikes\p6-calc\negative_calculate.py`; no live agent turn):

| Expression (synthetic) | Result | Notes |
|---|---|---|
| `__import__('os').system('echo x')` | `ok:false` `unsupported_node` | no side-effect files; plugin listing unchanged |
| `9**9**9` | `ok:false` `exponent_out_of_range` | same |

Plugin log (metadata only): two `ok=false` lines with lengths 33 / 7. No new shell process spawned for the hostile import path.

### Part B — Brian (Text mode)

| Step | Prompt | Tools | Cards | Correct? | Brian |
|---|---|---|---|---|---|
| 1 | What is 17 times 23? | `calculate` (also `tool_search`, `tool_describe`; no `execute_code`/`terminal`) | none | yes (391) | "Answer 391. No card presented" |
| 2 | What is 15% of 240? | `calculate` only (no `execute_code`/`terminal`) | none | yes (36) | "Answer 36. No card presented" |
| 3 | money total ($1347.12+$466.72+$565) | `calculate` only (no `execute_code`/`terminal`) | none | yes (2378.84) | "Answer $2,378.84. No card presented." |
| 4 (control) | Please use your code tool… prints hello. | `execute_code` | 1 card (`srq-dbca914ee9a9`, Deny) | n/a (blocked) | "Approval card present. After Deny, the response is: I couldn’t run it: the code tool denied execution because consent wasn’t available." |

Log notes (step 3): `calculate completed`; `zola_tools.log` `ok=true input_length=18 node_count=8`; `server-requests.log` still unchanged. Offsets after step 3: agent **3606467**, zola_tools **514**, server-requests **30826**, tool-events **78**.

Log notes (step 4 control): `server-requests.log` approval `srq-dbca914ee9a9` received/shown/answered `deny`; `agent.log` `Tool execute_code returned error` / `BLOCKED: execute_code script denied by user` (pattern class: `execute_code`, not terminal `-e/-c`). No `calculate` / no `zola_tools.log` line. Offsets after step 4: agent **3610946**, zola_tools **514**, server-requests **31200**, tool-events **78**.

### Part C — Pass/fail (Track 1 exit)

| Criterion | Result |
|---|---|
| Prompts 1–3: correct answers, zero cards, no `execute_code`/terminal | ✅ PASS |
| Control: expected card; Deny blocks | ✅ PASS (`execute_code`) |
| Negative checks: `ok:false`, no side effects | ✅ PASS |

**smoke test passed**

## Phase 7 notes (Closeout)

- **7a:** Unit tests **Ran 44 tests in 0.025s — OK** (hermes-agent venv python). `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` → **Build succeeded** (0 Warning(s), 0 Error(s); full path `C:\Program Files\dotnet\dotnet.exe`). Banned-API scan production files: **ZERO hits**. Exit-criteria table below.
- **7b:** `hermes-agent` porcelain empty at `345cd2b057a452236de401d3534b8502a7465e8d`.
- **7c:** Deployed plugin hashes MATCH repo (`a1ef8541…` / `0f29f3fc…` / `f329e906…`). `identity/SOUL.md` ↔ live `SOUL.md` normalized MATCH (`bd18413d…`); raw SHA-256 both `b508cd0a…`. Approvals block (Phase 5 method) MATCH backup/live `0223ad04…`; live `config.yaml` still `b54acb16…`.
- **7d–7k:** Commit / push / merge / delete as below.

### Exit criteria verification (PHASE6_BUILD_PLAN.md Track 1)

| Criterion | Verdict | Evidence |
|---|---|---|
| Unit tests pass (every listed case) | ✅ MET | 44/44 OK closeout re-run |
| Deployed hashes match repo; `identity/SOUL.md` matches live (line endings aside) | ✅ MET | 7c hash table; normalized SOUL match |
| HUMAN-RUN P-4 prompts: 391 / 36 / 2378.84; zero cards; no `execute_code`/terminal | ✅ MET | Phase 6 Part B steps 1–3 |
| HUMAN-RUN control: machine-changing card; Brian Deny | ✅ MET | Phase 4 STOP control (not desktop folder): `execute_code` card `srq-dbca914ee9a9` Denied (Brian approval: execute_code **or** terminal `python -c`) |
| CURSOR-RUN hostile/`ok:false`; no process spawned | ✅ MET | Phase 6 Part A negative checks + unit tests |
| `approvals.*` unchanged; `hermes-agent` clean at pin | ✅ MET | approvals block `0223ad04…`; hermes `345cd2b0…` clean |

All Track 1 exit criteria: **YES**

### Final file list (repo)

**New:**
- `hermes-plugins/zola_tools/plugin.yaml`
- `hermes-plugins/zola_tools/__init__.py`
- `hermes-plugins/zola_tools/calculator.py`
- `hermes-plugins/zola_tools/tests/__init__.py`
- `hermes-plugins/zola_tools/tests/test_calculator.py`
- `zola-architecture/lore/prompts/progress/P6-CALC_Progress.md`
- `.gitignore` (new file: `hermes-plugins/**/__pycache__/`)

**Modified:**
- `zola-architecture/identity/SOUL.md` (`## Doing math` mirror)

**Live profile (not in git):**
- `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_tools\` (3 files)
- `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` (`## Doing math`)
- `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` (`plugins.enabled: [zola_tools]`)

### Closeout SHAs

- Implementation commit (7f): *(pending)*
- Merge SHA on `main` (7i): *(pending)*
