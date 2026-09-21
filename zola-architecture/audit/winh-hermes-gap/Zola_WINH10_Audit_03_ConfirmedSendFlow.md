# WINH10 Audit 03 — Confirmed-Send Action Flow

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Sms_Intelligence_Architecture.md` **Send Is Confirmed, Not Autonomous** and the two-step action flow (offer → user content → read-back → confirm → send; `_confirmed` gate).

---

## 1. Verify “not agent-callable”

**Confirmed.** Module comment (`tools/send_message_tool.py` L22–24): `send_message` is intentionally **not** registered as a model tool. `toolsets.py` L185: “there is deliberately no agent-callable send_message tool.” Test `tests/tools/test_send_message_plugin_extensibility.py` L191–194: `registry.get_entry("send_message") is None`. `tools/delegate_tool_toolsets.py` L19 lists `send_message` among tools children must not get. `SEND_MESSAGE_SCHEMA` (L655+) exists for host/MCP-shaped callers, not the agent registry.

**Who can actually send (call sites):**

| Caller | File | Authorization assumed |
|---|---|---|
| `hermes send` CLI | `hermes_cli/send_cmd.py` L195–199 → `send_message_tool({action: send, …})` | Whoever can run the CLI in that profile (local user / script). No per-message confirm. |
| Cron delivery | `cron/scheduler_delivery.py` L1460–1471 `_standalone_send` → `_send_to_platform`; also live adapter path ~L1440 | Job already in `jobs.json`; `cron_mode` for the **agent turn** (WINH08), not a second confirm before the outbound SMS/email. Delivery is automatic after the job finishes. |
| Kanban notifier | `gateway/kanban_watchers_notifier.py` (deliver subscription events via adapter send); TUI path `tui_gateway/session_notifications.py` | Subscription row in kanban DB; consecutive send failures drop a dead chat (`MAX_SEND_FAILURES` L53). No human re-confirm per event. |
| Opt-in MCP | `mcp_serve.py` L1–7, L600–620 `messages_send` → `send_message_tool` | `hermes mcp serve` — any MCP client that can invoke the tool. No Hermes-side two-step confirm. |

Relay egress: `_authorize_relay_target` (`send_message_tool.py` L67–116) is **destination verification** for gateway relay targets, not user confirmation of message text.

**Label:** `[MATCH]` `WINH10-AUD-05` (LOW) — `send_message` is not a model-callable tool; host callers listed above.

---

## 2. Does a live conversational turn have a send path?

**Yes — the primary path is not `send_message`.** A messaging-platform inbound turn **always replies on that platform**: adapter `handle_message` → agent → `adapter.send` / `gateway/delivery.py` `_deliver_to_platform` (L254). That is how Twilio SMS and IMAP/SMTP email work as “talk to Hermes by text/email.”

That reply is **not** gated by `approvals.mode` danger-tier (those wrap **tool** execution on a live JSON-RPC/CLI turn — `WINH07`/`WINH08`). It is the conversation result itself. There is no `_confirmed` flag analogous to Zola’s `MessageSendToolAdapter`.

Cross-channel `send_message` remains unreachable from the model’s tool list regardless of `approvals.mode`. A live Desktop/TUI turn cannot ask the model to SMS a third party via `send_message`. A live **gateway SMS session** *will* SMS the authorized sender back with the model’s words, autonomously.

**Label:** `[RISK]` `WINH10-AUD-06` (HIGH) — live gateway replies send without Zola’s two confirmation moments; removing the tool from the model does not create a confirmed-send flow — it relocates autonomous send to the adapter reply path.

---

## 3. Compare to Zola’s two-confirmation shape

Zola: surface → offer to reply → user supplies content → read back → user confirms → send.

Hermes host paths:

- **CLI `hermes send`:** one shot; body from argv/stdin/file.
- **Cron:** job prompt runs unsupervised (`WINH08-AUD-02`/`06`); result posted to home channel / explicit target.
- **Kanban notify:** event text posted to subscribed chat.
- **MCP `messages_send`:** MCP client supplies target+text once.
- **Gateway chat:** the inbound message *is* the user’s content; Hermes’s **reply** goes out without a read-back confirm.

None implement two distinct confirmation moments per outbound message. Authorization is **configure-the-caller** (allowlist, cron job, MCP server, CLI access), not **confirm-this-text**.

The email-inbox-triage skill **asks** the user to approve drafts in conversation — that is prompt policy, not an adapter `_confirmed` gate, and it is not on the SMS Twilio path by default.

**Label:** `[GAP]` `WINH10-AUD-07` (HIGH) — no two-step human confirmation on cron/CLI/kanban/MCP/gateway-reply send.

---

## 4. Media / attachment sends

`_MEDIA_PLATFORMS_NOTE` (`send_message_tool.py` L588) at this pin:

> telegram, discord, matrix, weixin, signal, yuanbao, feishu, whatsapp and slack

SMS Twilio path strips markdown and sends **text** (`sms/adapter.py` `format_message` / `MAX_SMS_LENGTH` 1600). Zola’s SMS send flow is text-only. Hermes media capability is **unused surface** for that requirement — not a match and not a gap.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH10-AUD-05 | MATCH | LOW | `send_message_tool.py` L22–24; `toolsets.py` L185; registry test L191–194 | `send_message` not model-callable; CLI/cron/kanban/MCP call helpers |
| WINH10-AUD-06 | RISK | HIGH | `base.py` `handle_message`; `delivery.py` L254; SMS `adapter.send` L160 | Live gateway reply is autonomous send on the inbound channel |
| WINH10-AUD-07 | GAP | HIGH | `send_cmd.py` L195; `scheduler_delivery.py` L1460; `mcp_serve.py` L600 | Host send paths have no two-step per-message confirm |
