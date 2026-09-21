# WINH07 Audit 03 — Governance: Trust, Permission & Behavioral Boundaries

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Master Architecture Plan §13 Trust, Permission, and Privacy Framework (trust as inspectable, contextual, never assumed; permissions as explicit behavioral boundaries; escalation as a distinct class; explainability of allow/refuse).

This phase is **runtime behavioral permission** (what the agent may *do now*), not capability-acquisition (WINH06: can it add a skill/tool/plugin). Cite `WINH06-AUD-02` (default-off skill write approval) and `WINH04-AUD-03` (no-TTL retention) only as *shape* examples. Do not restate those findings. §9/9a proactive interrupt is not scored (INFO only if code is adjacent).

---

## 1. Explicit, inspectable permission / boundary system?

**Zola §13 examples:** allowed to summarize messages, allowed to proactively interrupt, allowed to access X — a layer *above* “which tools exist.”

**Hermes:** behavioral scope is **tool registration + a dangerous-command overlay**, not a Framework permission table.

- **What tools exist:** `toolsets.py` `_HERMES_CORE_TOOLS` L11–31 and named toolsets; gateway enables per session (`tui_gateway/server.py` `_load_enabled_toolsets`, referenced from `toolsets.py` L8–10). If a tool is not in the enabled set, the model cannot call it. That is inventory, not “allowed to summarize / allowed to interrupt.”
- **Dangerous terminal / similar:** `tools/approval.py` + `tools/approval_context.py` `_get_approval_mode` L228–237 (`manual` / `smart` / `off`; hosted-room policy can override). Default mode is **`smart`** (`hermes_cli/config_defaults.py` L1557). Unattended / cron / single-query modes default **`deny`** (L1559–1561).
- **Protected writes:** project-local SOUL.md always-ask and `config.yaml` hard-block on `write_file` are WINH06 file-guard mechanisms, not a §13 permission catalog.
- **No** inspectable map of Framework-style capabilities (“summarize messages”, “proactively interrupt”, “access calendar”). Heartbeat/loop (`session_notifications.py`) are **armed features** that speak when due (WINH07-AUD-01), not permission checks against a user-visible “allowed to interrupt.” Searched at this pin: no `PermissionFramework`, no per-action allow-list of the §13 shape.

Operator-visible settings exist (`approvals.mode`, toolset enablement, `skills.write_approval` — the last is WINH06). They do not add up to an explicit behavioral-boundary *system* comparable to §13.

**Label:** `[PARTIAL]` `WINH07-AUD-05` (MEDIUM) — toolsets + approval overlay exist; no §13 permission layer above registration.

---

## 2. Escalation permissions

**Zola §13:** some actions are escalation-tier — contacting someone, irreversible product action, alerting a third party — requiring a higher bar than a normal response.

**Hermes distinctions that exist (not named “escalation”):**

- Dangerous-command approval (`tools/approval.py` `_pending_result` L494–519): user is asked; timeout then deny (gateway notify via `server.py` `_emit_approval_request`). Message text includes the pattern description.
- `approvals.cron_mode` / `single_query_mode` / `unattended_mode` default deny (L1559–1561) — unattended surfaces do not get the interactive smart path.
- Sudo / slash-destructive confirms (`config_defaults.py` L1572–1578 `mcp_reload_confirm`, `destructive_slash_confirm`).
- `denial_breaker_threshold` L1565–1567: after N consecutive smart DENYs, escalate to a hard-stop / ask `/approve`.

**What is missing:** no action class for “contact a person / alert a third party / irreversible product commitment” distinct from “this shell command matched a danger pattern.” Sending a message on Telegram/Discord *is* ordinary gateway delivery, not an escalation gate. There is no “escalation permission” the user can inspect or grant separately from tool enablement.

Ordinary model text (a normal `message.complete`) has **no** extra bar. The Framework’s escalation concept does not appear as a type.

**Label:** `[PARTIAL]` `WINH07-AUD-06` (MEDIUM) — danger/sudo/slash confirms exist; no §13 escalation-tier action class (contact / irreversible / third party). Not a total `[GAP]`: Hermes *does* distinguish some high-risk *commands* from ordinary tool use.

---

## 3. “Trust should never depend on assumptions”

**Zola §13:** trust is explicit, inspectable, contextual; never an unspoken default.

**Shape already found elsewhere (not re-audited):** `WINH04-AUD-03` no-TTL retention; `WINH06-AUD-02` `skills.write_approval` default False.

**Permission-framework equivalent at this pin:**

- `approvals.mode` default **`"smart"`** (`config_defaults.py` L1557). Interactive sessions therefore grant a **guardian-model** auto-decision for dangerous commands unless the operator changes YAML. That is an assumption: the user did not opt into “the model may approve danger on my behalf”; they got it by shipping default. `approval_context.py` L228–237: if hosted-room policy is unset, `_get_approval_config().get("mode", "manual")` — the **config default** still wins, and that default is `smart`, not `manual`.
- `display.busy_input_mode` default `"interrupt"` (L767): a second prompt barges the live turn. Documented in config comments, not a permission the user granted per session.
- `background_review.enabled` default True (`WINH06-AUD-07`) plus `display.memory_notifications` default `"on"` (L793–796): the fork both acts and notifies unless turned off.
- `approvals.timeout` default 300s then deny (L1558, `approval_context.py` L239–247) — fail-closed on timeout, which is explicit, but the *smart allow* path before timeout is not.

The permission *framework itself* therefore has the same shape as those earlier findings: a documented default that silently grants a broad behavior (guardian auto-approve on interactive surfaces) rather than a user-visible, default-deny boundary.

**Label:** `[RISK]` `WINH07-AUD-07` (HIGH) — `approvals.mode: smart` (and related notify/interrupt defaults) is assumed trust, not an explicit grant.

---

## 4. Explainability of allow / refuse

**Zola §13:** if a boundary decision is made, the user (or at least the log) should see *why*.

**When Hermes explains:**

- Pending dangerous command: `tools/approval.py` L510–519 builds a user-facing message (`⚠️ This action is potentially dangerous ({description}). Asking the user for approval.`). Gateway emits an approval request (`server.py` `_wire_session_agent` L1000–1002 `register_gateway_notify` → `_emit_approval_request`).
- Denied / blocked helpers `_denied` / `_blocked` (L471–479) carry `description` and `outcome`.
- RPC session-not-found: `_sess_nowait` L1148–1157 logs why 4001 fired (detached/reaped runtime) so a vanished message is diagnosable.

**When it does not:**

- `approvals.mode: "off"`: dangerous commands proceed without a user-facing why (the overlay is disabled).
- `mode: "smart"`: a guardian **allow** is typically silent to the user (the command just runs). A guardian deny may surface through the tool result / denial-breaker, not a Framework “permission X refused because Y” record.
- Tool-not-in-toolset: the model simply does not see the tool; no user-facing “you are not allowed to do X.”
- `review.summary` with `memory_notifications: "off"`: the review still runs; the user is not told a boundary was applied — only that the *notice* was suppressed.

There is no durable, queryable permission-decision log comparable to a §13 audit trail (skill ledger is WINH06 and gates *writes*, not speech/behavior permissions).

**Label:** `[PARTIAL]` `WINH07-AUD-08` (MEDIUM) — interactive approval prompts explain danger patterns; silent smart-allow, mode=off, and missing-toolset are opaque.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH07-AUD-05 | PARTIAL | MEDIUM | `toolsets.py` L11–31; `approval_context.py` L228–237 | Scope = enabled tools + danger overlay; no §13 permission catalog |
| WINH07-AUD-06 | PARTIAL | MEDIUM | `approval.py` L494–519; `config_defaults.py` L1557–1578 | Danger/sudo/slash confirms; no contact/third-party escalation class |
| WINH07-AUD-07 | RISK | HIGH | `config_defaults.py` L1557, L767, L793–796 | Default `approvals.mode: smart` (and interrupt/notify defaults) assume trust |
| WINH07-AUD-08 | PARTIAL | MEDIUM | `approval.py` L471–519; `server.py` L1000–1002 | Approval prompts explain; smart-allow / missing toolset do not |
