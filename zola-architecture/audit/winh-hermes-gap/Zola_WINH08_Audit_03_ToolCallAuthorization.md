# WINH08 Audit 03 — Tool-Calling Pipeline & Authorization Parity

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola truth for this phase is **only** two lines: Core Rule (no agent executes tools) and Agent 8 Must-never: never “bypass the tool authorization pipeline” or “pre-execute tools that require user confirmation.” No invented full tool-auth spec. Live-turn approval *shape* is `WINH07-AUD-05`–`08` (cite). Disconnect fail-open is `WINH03-AUD-05` (cite; this asks whether **authorization** changes after detach).

---

## 1. Live-turn tool-invocation pipeline (extend `WINH03-AUD-02`)

Confirmed chain from WINH03, with the **approval** step named:

```
perform_api_call  →  assistant tool_calls
  → run_tool_round                    # agent/turn_tool_round.py L45
       persist tool-call msgs         # L116–119 durability invariant
       AIAgent._execute_tool_calls    # run_agent.py L1273
            plan parallel/sequential segments
            invoke_tool / sequential inline
                 _pre_tool_block_message / pre_tool_call hooks
                      # agent_runtime_helpers.py L2211; plugins.py L1782–1794
                      # thread whitelist block lives here
                 model_tools.handle_function_call  # L858
                      registry → concrete tool (terminal, write_file, …)
                 [terminal / execute_code / flagged write]
                      check_all_command_guards / request_tool_approval
                      # tools/approval.py L1079, L1015
                      # mode smart|manual|off; gateway queue → _emit_approval_request
                      # tui_gateway/server.py L709
  → tool result appended to messages
  → next perform_api_call
```

`invoke_tool` (`agent_runtime_helpers.py` L2227–2297) is the concurrent invoke: middleware → `_pre_tool_block_message` → inline executor or `handle_function_call`. Dangerous-command detection is inside the **tool** (`check_all_command_guards` L1079–1107): Tirith + pattern list, then `_run_approval_gate` (`approval.py` L881). YOLO / `approvals.mode: off` skip the recoverable layer (L1094–1095). Plugin `pre_tool_call` `{action: approve}` uses the **same** human gate (`request_tool_approval` L1015–1024).

This is a real authorization step on the live gateway/CLI path (`WINH07-AUD-05` overlay). It is not a Zola Tool Warm-Start pipeline, and it is not a core that workers must use.

**Label:** `[MATCH]` `WINH08-AUD-05` (LOW) — live turn has an identifiable invoke + approval path (the two Agent 8 lines assume such a pipeline exists to *not bypass*).

---

## 2. Do background / subagent tool calls hit the same gate?

**Live gate (`WINH07-AUD-05`–`08`):** enabled toolsets + `approvals.mode` (default `smart`) + gateway/CLI human prompt; unattended/cron/single-query use their own mode (default **deny**).

**Background review:** `_set_thread_approval_callback(_bg_review_auto_deny)` (`background_review.py` L988–992, L1171). Dangerous commands **deny**, never `input()` / gateway card (comment L985–987). Plus dispatch whitelist (AUD-02). Same `handle_function_call` / `check_all_command_guards` **functions**, different **callback and allowed names**. Not the live `smart` human path. `extra_tools` can admit tools the default review cannot call.

**Delegate children:** `_subagent_auto_deny` default, `_subagent_auto_approve` if `delegation.subagent_auto_approve` (`delegate_tool_config.py` L35–59). Comment L40–41: “Gateway sessions are unaffected (they resolve approvals via `tools/approval.py`'s per-session queue).” Children on a **gateway** session can still use the session queue; worker-thread CLI children get auto-deny/approve so they do not deadlock the TUI. Opt-in auto-approve is **weaker** than a live human prompt.

**Cron:** `HERMES_CRON_SESSION` (`approval_context.py` `_is_cron_approval_context` L126–128). `approvals.cron_mode` default **deny** (`config_defaults.py` as cited WINH07; `approval.py` L561, L1021). Same gate functions, **unattended branch**, not the interactive smart path. `cron_mode: approve` auto-approves danger with nobody present — that **exceeds** a live turn’s default smart prompt (Phase 4 RISK if set; default does not).

**Heartbeat / loop:** `_run_prompt_submit` on the **same live session** — same `approvals.mode` / gateway notify as a user-typed turn. Time-triggered, **not** `cron_mode`. A scheduled process can execute confirmation-gated tools with the **live** (more permissive default `smart`) gate if a client is attached.

**Label:** `[RISK]` `WINH08-AUD-06` (HIGH) — non-live callers share code entry points but not the live human/`smart` decision. Review/subagent auto-deny (or auto-approve); cron uses `cron_mode`; heartbeat uses the live gate.

---

## 3. Pre-fetch / warm / speculative tool calls? (Agent 8)

Searched: `prefetch` / `warm` / `speculat` / `tool cache` in agent/tools. Hits are: memory `prefetch_all` (retrieval string, Phase 5), TTS audio prefetch, MCP OAuth metadata, pet/update-check, `side_question` (tools **denied**). No `WarmToolContext`. No code that runs `handle_function_call` for weather/calendar/etc. **before** the model requests that tool.

Nothing to violate “must never … pre-execute tools that require user confirmation” on the **tool** axis.

**Label:** `[MATCH]` `WINH08-AUD-07` (LOW) — by **absence** of a speculative tool-exec mechanism.

---

## 4. Orphaned / detached turn — does tool authorization change?

**Cite `WINH03-AUD-05`:** Surface 3 default fail-open; the turn keeps running after WS drop (`_DropTransport`).

**Authorization:** the session remains a **gateway** approval context (`HERMES_GATEWAY_SESSION` / `_is_gateway_approval_context`). Dangerous tools still go through `_emit_approval_request` (`server.py` L709–732) → `server_requests.send_async("approval", sid, …)`. `write_json` to `_DropTransport` delivers **false** (WINH07-AUD-11). The wait is still `tools.approval`’s queue with `approvals.timeout` (default 300s, WINH07), then deny.

It does **not** flip to `unattended_mode` / `cron_mode` deny-immediately when the client is gone. The originating client cannot tap Approve; a **later fan-out attacher** of the same sid could (`_resume_reuse_live`, WINH07). Until timeout, the turn blocks on a prompt nobody on the original socket can see.

**Label:** `[RISK]` `WINH08-AUD-08` (MEDIUM) — detached tool auth is still the live gateway path (300s then deny), not a tighter unattended policy.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH08-AUD-05 | MATCH | LOW | `turn_tool_round.py` L45; `run_agent.py` L1273; `approval.py` L1015, L1079 | Live turn: persist → execute → guards/approval → result |
| WINH08-AUD-06 | RISK | HIGH | `background_review.py` L988–992; `delegate_tool_config.py` L42–59; `approval_context.py` L126–128 | Background/subagent/cron/heartbeat do not share one live human gate |
| WINH08-AUD-07 | MATCH | LOW | searched prefetch/warm/speculat in agent/tools | No speculative tool pre-execute (Agent 8 constraint holds by absence) |
| WINH08-AUD-08 | RISK | MEDIUM | `server.py` L709; `_DropTransport`; `approval.py` timeout | Orphaned turn keeps gateway approval until timeout, not unattended deny |
