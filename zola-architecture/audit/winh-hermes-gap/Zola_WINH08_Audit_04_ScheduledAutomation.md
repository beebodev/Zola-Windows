# WINH08 Audit 04 — Scheduled Automation

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola examples: Agent 14 (Compute Priority Scheduler) and Agent 15 (DailyBriefAgent) — time/event-triggered, staleness/dedup, **no independent speech or tool authority** beyond the owning pipeline. Factual Hermes scheduler behavior that has no line-for-line Zola requirement is `[OBSERVATION]`. `[RISK]` only if unsupervised scheduled authority **plainly exceeds** a live turn. Background-review is **post-turn**, not a cron (`WINH06-AUD-07`); distinguished below.

---

## 1. Literal scheduled / cron / time-triggered mechanism?

**Yes. Distinct from post-turn `background_review`.**

**Cross-process cron:**

- Store: `~/.hermes/cron/jobs.json` (per profile home) — `cron/jobs.py` L1–2, L61–73.
- Scheduler: `cron/scheduler.py` L1–2 — `tick()`; file lock so one tick at a time.
- Gateway starts it: `gateway/run.py` `_start_cron_ticker` L4587–4591, default **60s** (`InProcessCronScheduler().start(..., interval=interval)`).
- CLI: `hermes cron` / `hermes cron status` (`hermes_cli/cron.py`, `hermes_cli/console_engine.py` L805).
- Agent tool: `tools/cronjob_tools.py` `cronjob_manage` (create/list/run/…).
- API: `gateway/platforms/api_server.py` cron routes (WINH02 surface; `list_jobs` / `create_job_with_scheduler_registration`).

Jobs have cron expressions or `{kind: "once"}` (`jobs.py` `create_job` L1716, `parse_schedule`).

**In-process timers (not `jobs.json`):**

- `/heartbeat` — `hermes_cli/heartbeat.py` L1–6: session-scoped; “durable cross-process scheduling stays `hermes cron`.” Min interval 60s (L19).
- `/loop` — `hermes_cli/loops.py` L1–6, state in SessionDB `state_meta`.
- Gateway loop ticker — `gateway/run_goals.py` L445 fires due `/loop` for idle gateway sessions.

Searched CLI subcommands / `cron/` / config `cron.*` — the scheduler is real, not inferred from the review fork.

**Label:** `[OBSERVATION]` `WINH08-AUD-09` (MEDIUM) — Hermes has a first-class cron plus in-session heartbeat/loop. No Zola requirement that Hermes *must* ship cron; recorded as fact.

---

## 2. What can a scheduled job do?

**Cron job fire:** `_run_agent_with_watchdog` (`scheduler.py` L1675–1721) → `agent.run_conversation(prompt)`. Full conversational agent: **tools**, memory tool, skill tools, terminal (subject to `approvals.cron_mode`). Default `cron_mode: deny` — dangerous-command overlay **denies** without a human (`approval_context.py` L126–128; WINH07 default). Non-dangerous tools still run unsupervised.

Output: written under `~/.hermes/cron/output/{job_id}/` (`jobs.py` L1–2). Delivery to messaging/desktop via `cron/scheduler_delivery.py` (user-facing — speech is `WINH07`, cite only). Memory/skill writes on this path are the same tools as a live turn (`WINH04-AUD-02` / `WINH06-AUD-07` domain, not re-derived).

**Does cron exceed a live turn by default?** Live default is `approvals.mode: smart` (human/guardian). Cron default **deny** is *stricter* on flagged danger. Cron is *weaker* on supervision (no user watching ordinary tools). Not a plain exceed of live danger-authority at default. **`cron_mode: approve`** would auto-approve danger with nobody present — that **does** exceed a live interactive prompt. That is an operator setting, not the default.

**Heartbeat / loop:** full `_run_prompt_submit` with **live** `approvals.mode` (AUD-06). A timer can run confirmation-gated tools under `smart` if a gateway client is attached — closer to a live turn than cron, and **not** `cron_mode deny`. Combined with AUD-02.

**Label:** `[OBSERVATION]` `WINH08-AUD-10` (MEDIUM) — cron = unsupervised full `run_conversation`; danger gated by `cron_mode` (default deny). Heartbeat/loop = scheduled **live-turn** authority. `[RISK]` not raised for default cron vs live danger; `cron_mode: approve` would be the exceed case (config, not default).

---

## 3. Dedup / staleness / missed trigger?

**Agent 15 analog:** `lastDeliveredDate` dedup; missed Agent 2 work runs on next background window.

**Cron:**

- `last_run_at` on the job record (`jobs.py` ~L920; scheduler writes on completion).
- One-shot `run_claim` + heartbeat so a live long run is not re-dispatched (`scheduler.py` L1684–1690).
- CAS claim on fire so concurrent tickers de-dupe (`gateway/run.py` comment ~L4460).
- Misfire: `cron.misfire_grace_minutes` default **10** (`scheduler_provider.py` L20, L240–247). External providers: `fire_overdue_jobs` L253–260. In-process ticker “self-heals”; grace ≤ 0 disables catch-up.
- Recurring jobs that error retry vs `cadence + grace` (`jobs.py` ~L904–924).

Not Agent 15’s `lastDeliveredDate` / 4-hour brief expiry, but there **is** defined missed/duplicate behavior (claim + last_run + grace), not “run twice with no rule.”

**Heartbeat:** `HeartbeatManager.state` + idle claim; due tick coalesces if busy (`session_notifications.py`). User message wins (`heartbeat.py` L4–6).

**Loop:** `loops.max_ticks` default 100 (`loops.py` L25–26); `LOOP_COMPLETE` / `--until` / `--times`.

**Label:** `[PARTIAL]` `WINH08-AUD-11` (MEDIUM) — cron has last_run/claim/misfire-grace; not Agent 15 `lastDeliveredDate`, and heartbeat/loop are a separate state store.

---

## 4. Discoverability?

**Analog:** `WINH06-AUD-14` (no single capability inventory), `WINH07-AUD-12` (no single routing index).

To see “everything that will fire”:

- `hermes cron status` / `list_jobs` / `jobs.json` (cron only).
- SessionDB heartbeat/loop/`goals` meta (`heartbeat.py`, `loops.py`).
- `cronjob_manage` list from inside a turn.
- Kanban watcher ticks (`kanban_watchers_dispatcher.py`).
- Background-review is not a schedule (post-turn).

No one operator surface lists cron + heartbeat + loop + kanban.

**Label:** `[GAP]` `WINH08-AUD-12` (MEDIUM) — no single scheduled-job inventory (same pattern as `WINH06-AUD-14` / `WINH07-AUD-12`).

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH08-AUD-09 | OBSERVATION | MEDIUM | `cron/jobs.py` L1–73; `scheduler.py` L1–2; `gateway/run.py` L4587 | Real cron ticker (60s) + jobs.json; not the review fork |
| WINH08-AUD-10 | OBSERVATION | MEDIUM | `scheduler.py` L1675–1721; `cron_mode` deny | Cron runs full agent; danger default-deny; heartbeat uses live auth |
| WINH08-AUD-11 | PARTIAL | MEDIUM | `jobs.py` last_run_at; `scheduler_provider.py` L20, L240 | Claim + misfire grace; not Agent 15 lastDeliveredDate |
| WINH08-AUD-12 | GAP | MEDIUM | cron status vs SessionDB heartbeat/loop vs kanban | No single place listing every scheduled job |
