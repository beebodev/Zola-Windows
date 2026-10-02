# P6PRE Audit 07 — Live Probes

**Audit:** P6PRE · Scratch: `C:\Users\test\Dev\zola-spikes\p6pre\`  
**Interpreter:** `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`  
**G-SCRATCH / G-LIVE / G-PRIVACY** apply.

---

## Finding summary (probes)

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-16 | [RISK] | MEDIUM | P-1 results | See Audit 02 — insert cost / HRR SNR at 2k; warm prefetch fine. |
| P6PRE-AUD-08 | [RISK] | HIGH | P-2 results | LEAD-2 confirmed in harness. |
| P6PRE-AUD-36 | [GAP] | MEDIUM | P-3 | Skipped — agent init fails before `_init_memory` without credentials. |
| P6PRE-AUD-37 | [RISK] | MEDIUM | Audit 06 / B3 | One `execute_code` can raise two cards; Approve once on the script does not block nested terminal. |
| P6PRE-AUD-38 | [RISK] | MEDIUM | P-4 live | Turn 1=`execute_code`; turns 2–3=`terminal` with `pattern_key=script execution via -e/-c flag`; tool choice not fixed. |

---

## P-1 — Holographic harness (no model, no network)

**When:** 2026-10-02  
**Commands:**

```text
set HERMES_HOME=C:\Users\test\Dev\zola-spikes\p6pre\profile
C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe C:\Users\test\Dev\zola-spikes\p6pre\p1_holographic_harness.py
```

**Synthetic sample fact (verbatim):** `[car] Aurora GT detail number 0000 stays synthetic.` (51 chars)  
Subjects rotated: Aurora GT, Nimbus Coupe, Cedar Desk, Maple Bridge, Alex Rivera, Jordan Lee, Harbor Lane, teal accents.

**Environment:** NumPy 2.4.3 present → **HRR path** (not FTS-only fallback).

| n | init ms | cold prefetch ms | warm median / p95 / max ms | add median ms (total s) | DB bytes |
|---|---------|------------------|----------------------------|-------------------------|----------|
| 50 | 28.377 | 3.070 | 1.612 / 2.925 / 3.490 | 7.671 (0.380 s) | 4,096 |
| 500 | 17.461 | 3.737 | 1.933 / 3.212 / 4.184 | 26.731 (12.253 s) | 2,342,912 |
| 2,000 | 17.491 | 4.731 | 1.991 / 2.658 / 3.191 | 61.080 (119.825 s) | 9,584,640 |

**5,000:** skipped — 2,000-fact insert+query ≈ **119.9 s** ≥ 30 s gate.  
**HRR:** capacity warnings from ~n=1949 at dim=1024 (SNR≈0.72).  
**vs S38:** warm prefetch ≪ 1.5 s silence + 1.56–1.85 s transcription; insert path is not on the per-turn critical path unless `add_fact` runs mid-turn.

Raw JSON: scratch `p1_results.json` (not committed).

---

## P-2 — Forget / correction via MemoryManager

**When:** 2026-10-02  
**Command:**

```text
C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe C:\Users\test\Dev\zola-spikes\p6pre\p2_forget_propagation.py
```

**Synthetic facts:**

- A: `[car] The Nimbus Coupe has indigo door panels.`
- B: `[car] The Nimbus Coupe has charcoal door panels.`

| Step | Store after | Notes |
|------|-------------|-------|
| `on_memory_write(add, A)` | fact_id=1 content=A | Mirrored |
| `on_memory_write(replace, B, old_text=A)` | still only A | New absent; old survives |
| `on_memory_write(remove, B, old_text=B)` | still only A | Remove ignored |

`metadata_mode` detected: **legacy** (no metadata param). **LEAD-2 confirmed.**

Raw JSON: scratch `p2_results.json`.

---

## P-3 — Hook firing (scratch profile, Windows serve path)

**Status: skipped — no safe credential path** (2026-10-02).

**Harness built (scratch only):**
- `profile/config.yaml` — `memory.provider: p6pre_log` (no auth.json, no .env)
- `profile/plugins/p6pre_log/` — logging-only `MemoryProvider` (`get_tool_schemas() → []`)
- `p3_ws_driver.py` — mimics `ChatSocket.cs` (WS + `session.create` / `prompt.submit` / Abort + replace)

**Credential-free run (graceful sequence):**

| Step | Result |
|------|--------|
| `serve --isolated` HERMES_HOME=scratch | Ready `port=63684` (pid 3288) |
| `session.create` | ok `session_id=a15831a5` |
| Synthetic prompt | ack `streaming` |
| Agent build | **Failed before MemoryProvider.initialize** |
| Error (verbatim) | `agent init failed: No Codex credentials stored. Run \`hermes auth\` to authenticate.` |
| Hook log (`p3_hooks.jsonl`) | **Absent / empty** — zero `initialize` / `on_session_end` / `on_session_switch` / `shutdown` |
| Second `session.create` (old WS aborted) | ok `session_id=9584d776` |
| Wait 30 s | `session.reclaimed` `reason=ws_orphan_reap` at ~20 s (WS-level orphan path still fires) |
| Graceful serve stop | done |
| Hard-kill repeat | **Not run** — stop rule: agent cannot be built without credentials |

**Verdict:** Provider resolution / `_init_memory` never reached. MemoryProvider hooks on the Windows path remain **static-only** (Audits 01/03). No credentials were copied, linked, or re-logged.

---

## P-4 — Reproduce the math card (live client)

**Status: COMPLETE** (2026-10-02).

### Pre-flight (2026-10-02 ~11:28)

| Check | Result |
|-------|--------|
| Client | `Zola.Client` pid 12500 (Debug net9) |
| Serve | `-p zola serve --isolated --host 127.0.0.1 --port 0` (pid 23320 listening; WS accepted 11:20:45) |
| Profile | `%LOCALAPPDATA%\hermes\profiles\zola\` |
| Presence | active (`P3-LIFE` updating) |

**Log byte offsets (before first P-4 prompt):**

| Log | Bytes |
|-----|------:|
| `%LOCALAPPDATA%\ZolaClient\logs\server-requests.log` | 29,704 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\agent.log` | 3,570,178 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\gui.log` | 436,353 |
| `%LOCALAPPDATA%\ZolaClient\logs\tool-events.log` | 78 |

### Planned steps

1. ~~Cursor confirms client + serve; note log offsets~~ **done**
2. ~~Brian: `What is 17 times 23?` — Deny if card~~ **done**
3. ~~Cursor reads new log lines~~ **done** (turn 1)
4. ~~Brian: `What is 15% of 240?`~~ **done**
5. ~~Brian: dollar-sum prompt~~ **done**

### Turn 1 — `What is 17 times 23?` (2026-10-02 ~11:40)

**Brian report (paraphrase):** The approval card came up. On Deny, there was a message stating that he denied the tool.

**Card (UI):** whole-script `execute_code` gate. Body included nested `from hermes_tools import terminal` + `terminal("python -c \"print(17 * 23)\"")`. Buttons: Approve once / Deny. `pattern_key=execute_code`.

| Source | Evidence |
|--------|----------|
| `server-requests.log` | **1** card `srq-0f0853c0fad3` shown 11:40:44 → answered **deny** 11:41:02 (`session_id=c98e165e`) |
| `agent.log` | prompt accepted; tool `execute_code` → `BLOCKED: execute_code script denied by user…` (18.53s); turn complete 24.0s |
| Nested card | **None** — Deny on whole-script gate prevents nested `terminal` approval |

**Offsets after turn 1:** server-requests=30,078 · agent.log=3,572,476 · gui.log=436,770

### Turn 2 — `What is 15% of 240?` (2026-10-02 ~11:43)

**Brian report (paraphrase):** Same outcome as step 1.

**UI deny text:** `python -c "print(0.15 * 240)"`.

| Source | Evidence |
|--------|----------|
| `server-requests.log` | **1** card `srq-765ecfea8a98` shown 11:43:28 → answered **deny** 11:43:36 |
| `agent.log` | `tools.terminal_tool: Creating new local environment…` then **`Tool terminal`** → `BLOCKED: Command denied by user…` (8.06s); INFO does not log `pattern_key` |
| Tool | **`terminal` directly** |
| `pattern_key` / description | **`script execution via -e/-c flag`** / same (replay `detect_dangerous_command` on deny command; Audit 06) |

**Offsets after turn 2:** server-requests=30,452 · agent.log=3,574,505 · gui.log=437,187

### Turn 3 — dollar-sum prompt (2026-10-02 ~11:45)

**Brian report (paraphrase):** A card was presented. On Deny he got a similar message as step 1 and 2.

**UI deny text:** `python -c "print(1347.12 + 466.72 + 565)"`.

| Source | Evidence |
|--------|----------|
| `server-requests.log` | **1** card `srq-3a49f305918a` shown 11:45:02 → answered **deny** 11:45:09 |
| `agent.log` | **`Tool terminal`** → `BLOCKED: Command denied by user…` (7.43s); turn 12.9s |
| Tool | **`terminal` directly** |
| `pattern_key` / description | **`script execution via -e/-c flag`** / same (replay; Audit 06) |

**Offsets after turn 3:** server-requests=30,826 · agent.log=3,576,295 · gui.log=437,604

### P-4 summary

| Turn | Prompt | Cards | Tool blocked | `pattern_key` | Nested second card |
|------|--------|------:|--------------|---------------|--------------------|
| 1 | 17×23 | 1 | `execute_code` (script nests `terminal`) | `execute_code` | No (Deny on gate) |
| 2 | 15% of 240 | 1 | `terminal` (`python -c …`) | `script execution via -e/-c flag` | n/a |
| 3 | $1347.12+$466.72+$565 | 1 | `terminal` (`python -c …`) | `script execution via -e/-c flag` | n/a |

**P6PRE-AUD-38:** Math tool choice is not fixed — `execute_code` and direct `terminal` both appear. Terminal math cards because `python -c` matches dangerous detection, not because manual mode gates all terminal commands (Audit 06 / S16 reconcile). S35 must cover both `pattern_key`s above (and nested terminal after Approve on `execute_code`).

Memory files: **unchanged** (hashes match Phase 1). `state.db` grew (normal session write).

---

## Pre-synthesis hash check

| File | Phase 1 | Pre-synthesis | Match? |
|------|---------|---------------|--------|
| `config.yaml` | `F8D7A1498F3EB41F424CCF36704B94F2E439C599002094403FEB55D30D5B05EF` | `F8D7A1498F3EB41F424CCF36704B94F2E439C599002094403FEB55D30D5B05EF` | yes |
| `MEMORY.md` | `8264268512E5CC7A37FFF847F523CA142C310DBF21BEF30C2AD601EE3A5986EB` | `8264268512E5CC7A37FFF847F523CA142C310DBF21BEF30C2AD601EE3A5986EB` | yes |
| `USER.md` | `47A732A0B218936C9B465F6BB8ADA34BCDA4FE027660F000E9B139B4E7022D12` | `47A732A0B218936C9B465F6BB8ADA34BCDA4FE027660F000E9B139B4E7022D12` | yes |
