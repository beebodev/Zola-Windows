# WINH10 Audit 05 — Cross-Reference: Authorization, Memory, and Prior Findings

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

This phase does not re-derive WINH04 / WINH07 / WINH08. It checks consistency with this phase’s send/inbound tracing.

---

## 1. Tool authorization vs confirmed-send (WINH08)

`WINH08-AUD-02` (HIGH): subagent / background-review / cron / heartbeat invoke tools **off** the live tool-round.

`WINH08-AUD-06` (HIGH): those callers do **not** share one live human/`smart` gate; cron uses `cron_mode`.

Phase 3: cron **delivers** job output through `cron/scheduler_delivery.py` `_send_to_platform` after the unsupervised cron agent turn. That outbound SMS/email/Telegram post is the same ungated-background family: the human authorized the **job**, not the **bytes about to leave**. Kanban notifier sends are also gateway-side, not live `request_tool_approval`.

This is **not** a new independent HIGH. It is WINH08’s finding applied to messaging egress.

Live **gateway chat replies** (`WINH10-AUD-06`) are a **different** mechanism (not a tool-round at all). They neither contradict WINH08 nor are they covered by it. Priority of WINH08’s HIGH findings is **unchanged**; this phase **reinforces** them for cron/kanban delivery.

No new finding ID.

---

## 2. Analysis-does-not-equal-storage vs WINH04 memory

Zola: signals ephemeral; bodies not written to memory/Firestore.

Phase 2 (`WINH10-AUD-02`): Hermes has no discard layer. Gateway sessions persist **transcripts** of inbound and outbound text (`gateway/session.py` SessionTranscriptMixin). Optional memory providers `sync_turn` (`WINH04-AUD-02`) can extract facts from those turns. The instance prompt dump / tools reading `$HERMES_HOME/memories/` (`WINH04-AUD-06`) means SMS/email **bodies that entered a session** can land in the same stores other content already does.

**New evidence, same family:** messaging makes WINH04’s retention story apply to highly sensitive channel content (SMS/email), which Zola’s comms architecture explicitly forbids.

**Label:** `[RISK]` `WINH10-AUD-13` (MEDIUM) — inbound message bodies follow ordinary session/memory persistence (`WINH04-AUD-02`/`06`); no comms-specific discard. Not a re-derivation of those IDs; a channel-specific consequence.

---

## 3. Approval defaults (`WINH07-AUD-07`) vs cross-channel send

`WINH07-AUD-07`: default `approvals.mode: smart` assumes trust for **tool** execution on live turns.

Connection:

- **`send_message` is not a model tool** (`WINH10-AUD-05`). `smart` never sees it. Host CLI/MCP/cron send is outside that gate entirely (`WINH10-AUD-07`).
- **Gateway auto-reply** is not a tool call (`WINH10-AUD-06`). `approvals.mode` does not wrap `adapter.send`.
- A live Desktop turn still cannot silently SMS a stranger via the model — that part of `smart` is **moot** for `send_message`. The remaining hole is gateway/cron/MCP, which `smart` was never going to cover.

Does not raise WINH07-AUD-07’s severity. It **narrows** its relevance for *this* domain: tightening `approvals.mode` does not implement Zola’s two-step SMS confirm.

No new finding ID.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH08-AUD-02/06 | cite | — | cron `scheduler_delivery.py` | Cron/kanban egress is the same ungated background family |
| WINH10-AUD-13 | RISK | MEDIUM | `session.py` transcripts; cite `WINH04-AUD-02`/`06` | Comms bodies persist like any other turn |
| WINH07-AUD-07 | cite | — | `approvals.mode` vs `adapter.send` / `send_message_tool` | Smart approvals do not wrap host or gateway send |
