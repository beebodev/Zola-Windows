# WINH08 Audit 02 — Background Worker / Subagent Architecture

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Agent_Map.md` Core Rule (“Agents prepare. The core decides. No agent writes to memory, speaks, executes tools, or holds routing authority.”), every agent’s Must-never, and the staleness/TTL/confidence pattern (`lastUpdatedMs`, `confidence`, `ttlMs`, `isStale`). Agent 14 is the priority/yield analog.

Speech of these workers is `WINH07-AUD-01/02/04` (cite, not re-derived). Skill-write of the review fork is `WINH06-AUD-07/08` (cite). Memory writes are `WINH04-AUD-02` (cite). This phase asks whether they **invoke tools**.

---

## 1. Formalized background-worker / subagent model?

**Zola shape:** Background Preparation / Session-Start / Live Turn agent categories, each preparing for a core that decides.

**Hermes actually has several independent-of-the-user-prompt paths** (not those Zola categories, and not one fleet with Must-never):

| Path | Trigger | Process |
|---|---|---|
| `delegate_task` children | Live-turn tool call | `tools/delegate_tool.py` L1–11: child `AIAgent` with own `task_id`, parent toolsets minus `DELEGATE_BLOCKED_TOOLS`. Top-level children run in background; orchestrator children wait. |
| Background-review fork | Post-turn (`WINH06-AUD-07`) | `agent/background_review.py` daemon thread; default `enabled: True`. |
| Cron ticker | Time (`cron/scheduler.py` L1–2; `gateway/run.py` `_start_cron_ticker` L4587–4591, interval 60s) | Independent of a live user turn. Distinct from post-turn review — see Phase 4. |
| `/heartbeat` | Interval, idle session | `hermes_cli/heartbeat.py` L1–6; fired by `session_notifications.py` `_maybe_fire_tui_heartbeat_tick`. In-process; “durable cross-process scheduling stays `hermes cron`.” |
| `/loop` | Interval / self-paced | `hermes_cli/loops.py` L1–6; `session_notifications.py` loop ticks. |
| Side-question `/btw` | User slash mid-turn | `agent/side_question.py` L1–7, L21–33: cache-parity fork with **tools denied**. |
| Kanban watchers | Board tick | `gateway/kanban_watchers_dispatcher.py` `tick_once`. |

There is no World-State / Context-Cache / Tool-Warm-Start agent types, and no core they check in with. The closest “formalized subagent” is `delegate_task` plus the review fork.

**Label:** `[PARTIAL]` `WINH08-AUD-01` (MEDIUM) — Hermes has real background/subagent code paths; they are not the Agent Map’s prepare-only fleet.

---

## 2. Can a subagent / background process invoke a tool independently of the live turn’s tool-round?

**Core Rule:** no agent executes tools.

**Yes. Several paths call `run_conversation` → `run_tool_round` → `_execute_tool_calls` without the parent’s current tool-round owning the call.**

**Background review (not only `skill_manage`):** `_review_tool_whitelist` (`background_review.py` L1025–1065) builds a **dispatch-side** whitelist: toolsets `skills` and optionally `memory`, plus `read_file` / `search_files`, plus `auxiliary.background_review.extra_tools` (any named parent tool already in the inherited schema). Write tools (`write_file` / `patch` / `terminal`) stay denied by default. Then `_run_review_fork` L1098–1107 `set_thread_tool_whitelist(...)`. Denied names never reach the registry (`hermes_cli/plugins.py` `set_thread_tool_whitelist` L1770–1794). Default is **not** every registered tool; it **is** independent tool execution (`skill_manage`, `memory`, reads, and any `extra_tools`). Cite `WINH06-AUD-07` for skill-write; this is the general invoke path.

**Delegate children:** `run_agent.py` `_dispatch_delegate_task` L1298–1311 → `delegate_task`. Children run a full agent loop with terminal/file/web by default (`delegate_tool_toolsets.py` `DEFAULT_TOOLSETS` L23; blocked: `delegate_task`, `clarify`, `memory`, `send_message`, `cronjob_manage` L14–21). Tool calls are the child’s `_execute_tool_calls`, not the parent’s round. Parent sees only the summary (`delegate_tool.py` L8–11).

**Cron:** `cron/scheduler.py` `_run_agent_with_watchdog` L1675–1721 submits `agent.run_conversation` on a worker thread. That is a full tool loop, time-triggered, no live user turn.

**Heartbeat / loop:** `_run_prompt_submit` (`WINH07-AUD-01`) — a **plain user turn** including tools, on a timer, if the session is idle.

**Side-question:** tools disabled (L21–33). Not an executor.

**Label:** `[RISK]` `WINH08-AUD-02` (HIGH) against Core Rule “no agent … executes tools.” Independent invoke is intentional in Hermes (whitelist / child toolsets / cron / heartbeat), not an accident.

---

## 3. Staleness / confidence metadata?

**Zola:** every background product carries `lastUpdatedMs` / `confidence` / `ttlMs` / `isStale` (Agent 1, 8, 12, 15).

**Hermes searched:** those field names as a cache contract — no `lastUpdatedMs` / `ttlMs` / `isStale` on tool results, review output, or session prefetch blobs. Hits: MCP schema cache `ttlMs` (`tools/mcp_schema_cache.py` L61 — catalog TTL, not tool-result freshness); holographic `trust_score` (WINH05: retrieval rank, not TTL). Memory `prefetch_all` (`agent/memory_manager.py` L394–402) returns a merged string with no per-entry freshness. Cron jobs have `last_run_at` (scheduler bookkeeping, Phase 4), not consumer-facing stale flags.

Cached/precomputed data is either used as live text or silently old.

**Label:** `[GAP]` `WINH08-AUD-03` (MEDIUM) against the Agent Map staleness/confidence pattern.

---

## 4. Priority / yield (Agent 14 analog)?

**Zola Agent 14:** live turn never yields; cache/warm-start/consolidation yield or run only when idle.

**Hermes:**

- **Review vs next live turn:** `agent/turn_facade.py` `run_conversation` L33–39 calls `cancel_background_review_for_live_turn` (`background_review.py` L120–144): interrupt the fork (`request_hard_interrupt`, “superseded by a new live turn”), wait a bounded timeout, then proceed anyway. That is a **yield of review to live**, for that fork only.
- **Heartbeat vs user:** `heartbeat.py` L4–6: “a real user message always wins”; ticks only if idle (`session_notifications.py` `_notif_claim_turn`).
- **Cron / delegate children / live turn:** no shared priority tier. Cron ticker is a separate 60s loop (`gateway/run.py` L4587). Children consume provider/I/O concurrently (`delegation` max concurrent children default 10, `delegate_tool_config.py` L17). No `isConversationActive` scheduler.

**Label:** `[PARTIAL]` `WINH08-AUD-04` (MEDIUM) — review-cancel and heartbeat-idle exist; no Agent 14 fleet scheduler. Cron and subagents can compete with a live turn for model calls.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH08-AUD-01 | PARTIAL | MEDIUM | `delegate_tool.py`; `background_review.py`; `cron/scheduler.py`; `heartbeat.py` | Several worker paths exist; not Agent Map prepare-only categories |
| WINH08-AUD-02 | RISK | HIGH | `background_review.py` L1025–1107; `delegate_tool.py`; `scheduler.py` L1675–1721 | Subagent/review/cron/heartbeat invoke tools off the live tool-round |
| WINH08-AUD-03 | GAP | MEDIUM | searched agent/tools/cron for `ttlMs`/`isStale` | No consumer-facing freshness/confidence on cached/precomputed data |
| WINH08-AUD-04 | PARTIAL | MEDIUM | `turn_facade.py` L33–39; `heartbeat.py` L4–6 | Review yields to live; cron/delegate have no priority tiers |
