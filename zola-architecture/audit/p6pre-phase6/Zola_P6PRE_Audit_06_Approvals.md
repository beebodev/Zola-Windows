# P6PRE Audit 06 — Approvals (S35)

**Audit:** P6PRE · Pin `345cd2b0…` · Live `approvals.mode: manual`  
**Labels against:** P4-D07, P4-D27, A3, S35.

---

## Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-31 | [MATCH] | — | `approval.py` L1148–1215; `agent.log` 2026-10-02 | B3 math cards were **`execute_code`** whole-script approvals (`pattern_key=execute_code`), not `terminal` (LEAD-1). |
| P6PRE-AUD-32 | [RISK] | MEDIUM | `approval.py` L1148–1153, L1200–1203; P4-D07 | Gateway always prompts for whole `execute_code` scripts; `once` does not persist → card per call under Zola’s once-only UI. |
| P6PRE-AUD-33 | [MATCH] | — | DESIGN_DECISIONS P4-D27; `approval_smart.py` | `smart` can auto-approve; live forces `manual`. |
| P6PRE-AUD-34 | [GAP] | LOW | `plugins.py` register_tool | Plugin tools register with **no** built-in approval; harm only if they call gated primitives or escalate via hooks. |
| P6PRE-AUD-35 | [RISK] | LOW | candidate shapes | Permanent allowlist / `smart` for math would weaken or conflict with P4-D07/P4-D27; SOUL + side-effect-free calculator need no hermes-agent edit. |
| P6PRE-AUD-37 | [RISK] | MEDIUM | B3 pairing + `code_execution_tool.py` | One `execute_code` can raise **two** cards (whole-script + nested terminal); Approve once on the script does not prevent the nested card. |
| P6PRE-AUD-38 | [RISK] | MEDIUM | P-4 + `approval_detection.py` | Math also hits `terminal` with `pattern_key=script execution via -e/-c flag` (`python -c`); not all terminal cmds card under manual. |

---

## 1. Which tool made the B3 cards (LEAD-1)

**Window:** P5-WAKE B3, 2026-10-02 ~07:41–07:43, `session_id=f96e5304`, agent `20261002_073405_763f1e`.

**Client `server-requests.log` (approval cards, answered `once`):**

| Request id | Received (local) | Answered |
|------------|------------------|----------|
| `srq-a85209ba796b` | 07:41:53 | once |
| `srq-753131655711` | 07:42:01 | once |
| `srq-a75ef0072f86` | 07:42:54 | once |
| `srq-0ce32949e4dd` | 07:42:58 | once |
| `srq-5d1eeed7cd7e` | 07:43:34 | once |
| `srq-ed2e9062f28f` | 07:43:36 | once |

Client log lines do **not** store `tool_name` / `pattern_key` (`text_or_len=-`).

**Hermes `agent.log` (tool completions, same session):**

| Time | Tool |
|------|------|
| 07:42:16 | `execute_code` completed (23.50s) |
| 07:43:00 | `execute_code` completed (5.60s) |
| 07:43:37 | `execute_code` completed (3.28s) |

Correlation: cards immediately precede `execute_code` completions. No `terminal` completions in that window for those turns.

**Code:** `check_execute_code_guard` sets `pattern_key = "execute_code"` and, in gateway/ask, always whole-script approval (`approval.py` L1148–1215). Call site: `code_execution_tool.py` ~L711–714.

**LEAD-1: Confirmed** (P6PRE-AUD-31).

Brian (P5-WAKE): *"she showed a card for each math problem for approval."*

### B3 pairing: 6 cards vs 3 `execute_code` completions

| Math turn | Prompt accepted | Cards (answered `once`) | `execute_code` completed | Nested evidence |
|-----------|-----------------|-------------------------|--------------------------|-----------------|
| 1 | 07:41:50 (16 chars) | `srq-a85209ba796b` 07:41:53 → once 07:42:00; `srq-753131655711` 07:42:01 → once 07:42:16 | 07:42:16 | After card 1: `terminal_tool` created local env (07:42:00–01). Result: `tool_calls_made: 1`, kernel `reused: false` |
| 2 | 07:42:50 (23 chars) | `srq-a75ef0072f86` 07:42:54 → once 07:42:58; `srq-0ce32949e4dd` 07:42:58 → once 07:43:00 | 07:43:00 | Result: `tool_calls_made: 1`, kernel `reused: true` |
| 3 | 07:43:30 (3 chars) | `srq-5d1eeed7cd7e` 07:43:34 → once 07:43:36; `srq-ed2e9062f28f` 07:43:36 → once 07:43:37 | 07:43:37 | Result: `tool_calls_made: 1`, kernel `reused: true` |

(A 9-char turn at 07:43:13 had **no** approval cards and **no** `execute_code` — follow-up path.)

**Explanation (evidence-based):** each math problem produced **two cards for one top-level `execute_code`**:

1. **Card A — whole-script gate:** `check_execute_code_guard` → `pattern_key = "execute_code"` (`approval.py` L1163–1215). Fires before the session kernel runs the cell.
2. **Card B — nested sandbox tool:** each `execute_code` result reports `tool_calls_made: 1` (`state.db` messages 1703/1707/1713). Session kernels may RPC into `SANDBOX_ALLOWED_TOOLS` including `terminal` (`code_execution_tool.py` L42–43). The first run’s log shows `tools.terminal_tool: Creating new local environment…` **between** the two cards — consistent with a nested `terminal` call that hit `check_all_command_guards` (its own `pattern_key`, not logged in `server-requests.log`).

Not explained by: two top-level `execute_code` tools (only one tool result row per turn); a simple retry of the same gate (second card is after env create / mid-run); client double-rendering one request (six distinct `srq-*` ids).

**Residual (B3 nested card):** `server-requests.log` and INFO `agent.log` did **not** record `pattern_key` for card B. P-4 Deny-only did not Approve through to a nested card; the direct-`terminal` math path (below) identifies the same dangerous pattern that nested `python -c` would hit.

**For synthesis (plain):** one `execute_code` run can raise **more than one** approval card — the whole-script gate (`pattern_key=execute_code`) plus a nested `terminal` command approval inside the session kernel. Approving the script **once** does **not** prevent further cards from nested tool RPCs (and `once` does not persist for later `execute_code` calls either).

### P-4 terminal cards — `pattern_key` / description

INFO `agent.log` for P-4 turns 2–3 logs `Tool terminal` + `BLOCKED: Command denied by user` but **not** `pattern_key`. UI deny text gave the exact command strings. Replayed against pin `345cd2b0` via `detect_dangerous_command`:

| Turn | Command (from UI deny) | `is_dangerous` | `pattern_key` | `description` |
|------|------------------------|----------------|---------------|---------------|
| 2 | `python -c "print(0.15 * 240)"` | True | `script execution via -e/-c flag` | `script execution via -e/-c flag` |
| 3 | `python -c "print(1347.12 + 466.72 + 565)"` | True | `script execution via -e/-c flag` | `script execution via -e/-c flag` |

**Why these cards under `approvals.mode: manual` (not “all terminal”):**

1. `terminal_tool` calls `check_all_command_guards` (`terminal_tool.py` ~L856 → `approval.py` L1079–1138).
2. Guards call `detect_dangerous_command` (`approval.py` L1112; `approval_detection.py` L1427–1443).
3. For `python -c …`, regex `DANGEROUS_PATTERNS` miss; `_execution_flag_findings` then yields the hit: interpreter family `python` + exec flag `-c` (`approval_detection.py` L901–917, `_INTERPRETER_EXEC_FLAGS` L556–558) → description/key **`script execution via -e/-c flag`** (returned as both `pattern_key` and `description` at L1439–1440).
4. With a finding and live mode `manual` (not `off`/`smart`), `_human_decision(..., smart=False)` prompts the gateway card (`approval.py` L1133–1138). Ordinary commands (`ls`, `echo hello`) return `(False, None, None)` and are approved with **no** card (same detect call).

**Reconcile S16** (`OPEN_QUESTIONS.md`: terminal “does not call `request_tool_approval()` for ordinary commands”): still accurate. The path is `check_all_command_guards` / dangerous detection, not `request_tool_approval()`. `python -c` is **not** ordinary — it is a dangerous-pattern hit. Manual mode does **not** gate every gateway terminal command; it prompts when detection (or tirith) flags the command. S16’s Workspace/send concern is about ordinary (non-matching) command strings that skip the card entirely.

**P6PRE-AUD-38** — S35 must cover at least: `pattern_key=execute_code` (whole-script), nested/direct `terminal` with `pattern_key=script execution via -e/-c flag`, and any other tool choice that still cards for math.

---

## 2. Tools that can raise cards under live config

Effective: `approvals.mode: manual` (profile); other approval keys at defaults.

| Tool / path | Why it asks | Can change something? |
|-------------|-------------|------------------------|
| `execute_code` | Always in gateway/ask (sandbox skip exceptions) | Yes — arbitrary Python / subprocess |
| `terminal` | Dangerous patterns / tirith findings | Yes — shell |
| File write tools | Sensitive/protected/approval-required paths | Yes — filesystem |
| Plugin `pre_tool_call` escalate | Hook returns approve action | Depends on tool |
| Memory/skills write approval | Only if `*.write_approval` (default false) | Yes — files/skills |
| MCP reload / destructive slash | Confirm flags | Yes — tool surface / state |

---

## 3. Approval config keys (this pin)

From `config_defaults.py` L1543–1578 (+ related):

| Key | Role | Per-tool? | Gate type |
|-----|------|-----------|-----------|
| `approvals.mode` | off / smart / manual | Global | Mode switch |
| `approvals.timeout` | Wait before fail-closed | Global | Timer |
| `approvals.cron_mode` / `single_query_mode` / `unattended_mode` | Unattended deny/approve | Context | Mode |
| `approvals.smart_policy` | Extra guardian prompt | Global | String → LLM |
| `approvals.denial_breaker_threshold` | Escalate after N smart DENYs | Global | Counter |
| `approvals.deny` | fnmatch globs vs terminal commands | Pattern | String match |
| `approvals.mcp_reload_confirm` / `destructive_slash_confirm` | Confirm UX | Feature | Flag |
| `command_allowlist` | Permanent “always” patterns | Pattern | Persist |
| `memory.write_approval` / `skills.write_approval` | Stage writes | Feature | Flag |
| `security.approval.transport` | Presentation transport | Global | Plugin/builtin |
| Env `HERMES_YOLO_MODE` | Bypass | Global | Env |

Session approvals exist in code (`is_approved(session_key, pattern_key)`) but Zola UI offers **Approve once / Deny only** (P4-D07) — session/always choices are not surfaced.

---

## 4. Can `execute_code` tell harmless from harmful?

**No.** Own comments (`approval.py` L1148–1153):

> The script can call `subprocess`/`os.system`/`ctypes` directly, none of which pass through `terminal()` / `DANGEROUS_PATTERNS`; in gateway/ask contexts we fail closed by approving the script as a whole.

**P6PRE-AUD-32 [RISK]** relative to “no card for simple math” while keeping fail-closed for arbitrary code.

---

## 5. Smart mode and P4-D27

- Smart: guardian LLM APPROVE/DENY/ESCALATE; APPROVE can auto-run (`approval_smart.py`).
- **P4-D27:** force `manual` because `smart` can auto-approve (P6PRE-AUD-33).

---

## 6. Plugin tools without approval

`register_tool` has **no** approval flag. A plugin tool runs without a card unless it calls gated primitives or a hook escalates. There is **no** Hermes “pure function / no I/O ⇒ skip approval” proof. Side-effect-free would be a Zola design claim + implementation discipline (no FS/net/process), not a host certificate (P6PRE-AUD-34).

---

## 7. Candidate shapes for the developer principle

Principle: *"She should not throw a card for simple math problems. Only for tools that make changes that need control or for clarifying."*

Keep apart: **(a)** she reaches for `execute_code` for 17×23; **(b)** when she really needs exact computation.

| Shape | Still cards | Stops cards | Weakens P4-D07? | Edits hermes-agent? | Fail |
|-------|-------------|----------------|-----------------|---------------------|------|
| SOUL: do simple math without tools | Control tools; clarify | (a) if she complies | No | No (identity) | Open if she still tools |
| Side-effect-free calculator tool | Control tools | (a)/(b) if she uses it | No | No (profile plugin) if ungated | Closed if tool is pure |
| **Both** (guidance + calculator) | Control tools | (a) via guidance; (b) via calc | No | No | Open if she still chooses `execute_code`/`python -c` |
| Session scope for `execute_code` | First call; later free in session | Repeat math in session | Softens once-only UX | Likely client + host | Open after first approve |
| Permanent allowlist `execute_code` | Other tools | All execute_code | **Yes** — broad host code | Config | Open |
| `smart` mode | Escalations only? | Auto-approved “safe” | Conflicts P4-D27 | Config | Open (auto-approve) |
| Leave as-is | Every gateway `execute_code` | Nothing | No | No | Closed for code; noisy for math |

**P6PRE-AUD-35** — options for synthesis §5.8; no recommendation.
