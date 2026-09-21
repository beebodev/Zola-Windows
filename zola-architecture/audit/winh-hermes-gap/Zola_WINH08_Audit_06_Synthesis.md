# WINH08 Phase 6 — Synthesis: Tool Calling, Subagents & Scheduled Automation

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Document of Truth: `Zola_Agent_Map.md`. Tool-calling held only to the Core Rule and Agent 8’s two Must-never lines. Cross-refs: `WINH03-AUD-02/05`, `WINH04-AUD-02`, `WINH06-AUD-07/08/14`, `WINH07-AUD-01/02/04/05–08/12`.

Source: Audit_02 SubagentArchitecture, Audit_03 ToolCallAuthorization, Audit_04 ScheduledAutomation, Audit_05 SpeculativeExecutionSafety.

Section 5 questions are not resolved here.

---

## Section 1 — Finding Summary Table

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH08-AUD-01 | PARTIAL | MEDIUM | `delegate_tool.py`; `background_review.py`; `cron/scheduler.py`; `heartbeat.py` | Several worker paths exist; not Agent Map prepare-only categories |
| WINH08-AUD-02 | RISK | HIGH | `background_review.py` L1025–1107; `delegate_tool.py`; `scheduler.py` L1675–1721 | Subagent/review/cron/heartbeat invoke tools off the live tool-round |
| WINH08-AUD-03 | GAP | MEDIUM | searched for `ttlMs`/`isStale` | No consumer-facing freshness/confidence on cached data |
| WINH08-AUD-04 | PARTIAL | MEDIUM | `turn_facade.py` L33–39; `heartbeat.py` L4–6 | Review yields to live; cron/delegate have no Agent 14 tiers |
| WINH08-AUD-05 | MATCH | LOW | `turn_tool_round.py` L45; `approval.py` L1015, L1079 | Live turn has persist → execute → approval → result |
| WINH08-AUD-06 | RISK | HIGH | `background_review.py` L988; `delegate_tool_config.py` L42–59; `approval_context.py` L126 | Non-live callers do not share the live human/`smart` gate |
| WINH08-AUD-07 | MATCH | LOW | searched prefetch/warm in agent/tools | No speculative tool pre-execute (Agent 8 by absence) |
| WINH08-AUD-08 | RISK | MEDIUM | `server.py` L709; `_DropTransport` | Orphaned turn keeps gateway approval until timeout |
| WINH08-AUD-09 | OBSERVATION | MEDIUM | `cron/jobs.py`; `gateway/run.py` L4587 | Real 60s cron ticker + jobs.json (not the review fork) |
| WINH08-AUD-10 | OBSERVATION | MEDIUM | `scheduler.py` L1675–1721; `cron_mode` | Cron = full unsupervised agent, danger default-deny |
| WINH08-AUD-11 | PARTIAL | MEDIUM | `jobs.py` last_run_at; `scheduler_provider.py` L20 | Claim + 10 min misfire grace; not lastDeliveredDate |
| WINH08-AUD-12 | GAP | MEDIUM | cron status vs SessionDB vs kanban | No single scheduled-job inventory |
| WINH08-AUD-13 | PARTIAL | MEDIUM | `turn_context.py` L779–790; `memory_manager.py` L394 | Memory prefetch; no live-wins vs cached recall |
| WINH08-AUD-14 | MATCH | LOW | `memory_provider.py` L111–117 | Prefetch does not speculatively durable-write |

**Counts:** 14 findings — **2 HIGH**, **9 MEDIUM**, **3 LOW**.

HIGH: AUD-02, AUD-06. MEDIUM: AUD-01, 03, 04, 08, 09, 10, 11, 12, 13. LOW: AUD-05, 07, 14.

`[OBSERVATION]` rows (AUD-09, AUD-10) count in the table; they are not scored as Agent Map misses.

---

## Section 2 — What Hermes covers as-is

**Subagents / workers.** Hermes is not a prepare-only Agent Map. It has `delegate_task` children (full tool loop minus a small blocklist), a post-turn background-review fork (dispatch whitelist: skills, optional memory, reads, optional `extra_tools`), a 60s cron that `run_conversation`s a stored prompt, in-session `/heartbeat` and `/loop` that submit **live** turns when idle, and `/btw` side-questions with tools denied (AUD-01, AUD-02). Review is cancelled when a new `run_conversation` starts (`turn_facade.py`); heartbeat yields to a busy session. Cron and children have no Agent 14 priority table (AUD-04). No `lastUpdatedMs` / `isStale` on worker products (AUD-03).

**Tool calling.** A live Surface 3 turn persists the tool-call message, executes via `_execute_tool_calls` / `handle_function_call`, and runs `check_all_command_guards` / `request_tool_approval` for flagged actions (AUD-05, extending `WINH03-AUD-02`). That is the pipeline Agent 8 must not bypass. Workers reuse those functions with **different** callbacks: review auto-deny + whitelist; subagent auto-deny (or `subagent_auto_approve`); cron `HERMES_CRON_SESSION` + `cron_mode` (default deny); heartbeat the **live** `smart` gate (AUD-06). Detached fail-open turns (`WINH03-AUD-05`) still wait on a gateway approval card that went to `_DropTransport` until 300s timeout (AUD-08). There is **no** speculative tool execution (AUD-07).

**Scheduling.** Cron is real: per-profile `jobs.json`, `hermes cron status`, `cronjob_manage`, gateway ticker (`AUD-09`). A job is an unsupervised agent turn with default danger-deny (`AUD-10`). Dedup via `last_run_at`, fire claims, 10-minute misfire grace (`AUD-11`). Heartbeat/loop/kanban are other clocks. No unified job list (`AUD-12`).

**Speculative / warm-start.** No Agent 8 tool cache. Memory `prefetch_all` at turn start injects recall text without TTL/live-wins (AUD-13). Prefetch itself does not write MEMORY.md (AUD-14). Review/cron writes are not warm-start side effects (already `WINH04`/`WINH06`).

---

## Section 3 — What needs a Zola-built adapter layer

| ID | Wrap | Adapter owns |
|---|---|---|
| AUD-01 / AUD-04 | Existing `delegate_task`, review cancel, heartbeat idle-claim | Policy: which workers Zola-Windows even starts; force review yield; do not treat children as prepare-only agents |
| AUD-05 | Live `run_tool_round` + `approval.py` | Keep Hermes as the invoke engine for **user-initiated** turns; Zola permission doc (WINH07 Q2) maps onto this gate |
| AUD-06 | Same functions, different callbacks | Pin review whitelist; `subagent_auto_approve: false`; `cron_mode: deny`; consider disabling heartbeat/loop or routing them through `cron_mode` |
| AUD-07 / AUD-14 | Absence of tool warm-start / prefetch-write | Nothing to wrap for Agent 8 execute; do not enable a Hermes-side speculative executor |
| AUD-11 | Cron claim + misfire grace | If Windows uses Hermes cron, keep grace/claim; add product-level `lastDeliveredDate` only if shipping a Daily Brief analog |
| AUD-13 | `prefetch_all` | Optional: strip or TTL-stamp injected memory in the client/sidecar so live memory-tool results are authoritative |

---

## Section 4 — What must be built from scratch

| ID | Capability | Why scratch | Finding |
|---|---|---|---|
| Core Rule enforcement | Workers must not execute tools / speak / write unless the core grants it | Hermes workers **are** tool executors (AUD-02). An adapter can disable them; a Zola core that *prepares only* is not in Hermes. | AUD-02 (+ speech `WINH07-AUD-04`, writes `WINH04-AUD-02`) |
| Staleness metadata | `ttlMs` / `isStale` / `confidence` on cached context | No Hermes consumer contract. | AUD-03 |
| Agent 14 scheduler | Live STT/turn always beats cron/children | Review-cancel ≠ fleet priority. | AUD-04 remainder |
| Unified schedule inventory | One operator list of cron + heartbeat + loop + kanban | Same pattern as `WINH06-AUD-14` / `WINH07-AUD-12`. | AUD-12 |
| Agent 8 / 4 / 9 warm-start (if Windows wants Zola’s model) | Pre-fetch with live-wins, no confirmation bypass | Hermes has no tool warm-start (AUD-07); memory prefetch has no live-wins (AUD-13). Building Zola warm-start is new, not a Hermes flag. | AUD-07, AUD-13 |
| Agent 15 Daily Brief pipeline | Prepare-only brief, `lastDeliveredDate`, Response Governor delivery | Cron is a **full agent**, not a prepare-only brief assembler. | AUD-09/10 as facts; scratch if Windows needs Agent 15 |

Orphaned-turn approval (AUD-08) is an adapter/policy on `WINH03-AUD-05` (interrupt on disconnect, or fail-closed), not a new Hermes module.

---

## Section 5 — Open questions for WINH00

Do not resolve these here.

1. **Tool-authorization architecture document.** This phase only had two Zola lines (Known Context). Should Zola-Windows write a real tool-authorization spec before WINH00, the way WINH06 asked for capability-acquisition policy?

2. **Cron vs Zola sidecar.** Hermes **has** cron (AUD-09), not a gap of “no scheduler.” Does the Windows track **use** Hermes cron for Agent 14/15-shaped work (knowing jobs are full unsupervised `run_conversation`s, AUD-10), or keep time-triggered prepare/brief in a Zola sidecar and leave Hermes cron off?

3. **Background-review combined authority.** `WINH06-AUD-07` (skill/memory write), `WINH07-AUD-02` (speaks via `review.summary`), and `WINH08-AUD-02/06` (tools on a whitelist, auto-deny for danger, `extra_tools` can widen). Does that combination raise gating urgency for Windows beyond WINH06/07?

4. **Warm-start / speculation.** Hermes is not Agent 8/4/9 (AUD-07, AUD-13). Should the Windows client add a warm-cache for responsiveness, or accept less speculative behavior than the Android Agent Map (zola-main remains out of scope; this is a Windows-track product choice)?
