# WINH10 Audit 04 — Channel Coverage: SMS, Email, and What Hermes Actually Has

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

**Correction of this session’s pre-audit spot-check:** a Twilio SMS adapter and an IMAP/SMTP email adapter **do** exist at this pin. They live under `plugins/platforms/`, not as `tools/sms_*.py` / `tools/gmail_*.py` filenames.

---

## 1. Literal SMS

**Hermes half (coverage):** Built-in platform plugin `plugins/platforms/sms/` (`plugin.yaml` name `sms-platform`, label “SMS (Twilio)”). `SmsAdapter` (`adapter.py`): outbound Twilio REST `Messages.json`; inbound aiohttp webhook `POST /webhooks/twilio` (L232). Env: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `SMS_WEBHOOK_URL`, `SMS_ALLOWED_USERS`. Toolset `hermes-sms` (`toolsets.py` L228). `send_message_targets.py` L24 includes `"sms"` in `_PHONE_PLATFORMS`. Tests: `tests/gateway/test_sms.py`.

Searched `tools/`, `gateway/`, `agent/` for a second SMS stack: no `tools/twilio.py`; Twilio is this plugin + telephony skill tests. No Android content-provider path (expected; not a finding).

**Windows-platform half (not a Hermes deficiency):** Windows has no cellular radio and no SMS content provider. Device-local SMS ingest/send cannot exist inside Hermes-on-Windows the way phone SMS exists on Android. A Twilio (or similar) **bridge number** is required for actual SMS. Hermes already *is* that class of bridge if the operator supplies Twilio credentials and a reachable webhook.

**Label:** `[PARTIAL]` `WINH10-AUD-09` (MEDIUM) — Hermes has Twilio SMS I/O; Windows still cannot read the handset SMS inbox without a bridge; that radio gap is platform fact, not “Hermes forgot SMS.”

---

## 2. Email

**IMAP/SMTP gateway (real):** `plugins/platforms/email/adapter.py` — poll IMAP, reply SMTP; `EMAIL_*` env (`plugin.yaml`). Toolset `hermes-email` (`toolsets.py` L213). This is **“email Hermes as a bot”** (allowed senders’ mail becomes agent turns), not `EmailIntelligenceAnalyzer`’s five stages (noise elimination, relationship weight, heuristic classification, consent-gated model pass, signal assembly with no body retention).

**Microsoft Graph:** `tools/microsoft_graph_client.py` / `microsoft_graph_auth.py` are a generic Graph REST client (app-only client credentials). Production consumers at this pin are **`plugins/teams_pipeline/`** (Teams meetings, transcripts, recordings — `meetings.py`, `subscriptions.py`) and Teams platform summary writer. **Not** Outlook `/me/messages` mail send/read. Graph is **not** an email-intelligence equivalent.

**Other email paths:** optional Composio-style connectors (`tools/connections_tool.py` mentions Gmail; `GMAIL_SEND_EMAIL` in tests) — remote **connector** tools, not a built-in Gmail API. Bundled skills `email-inbox-triage` + `himalaya` are CLI/skill procedures. Env allowlist includes `EMAIL_IMAP_HOST` / `EMAIL_SMTP_HOST` (`local_env_policy.py` L34).

Versus five-stage email intelligence: **scratch for the analyzer contract**; Hermes email adapter is a **chat transport** to wrap if Windows wants “talk to Zola by mail,” not a drop-in `EmailSignal` pipeline.

**Label:** `[PARTIAL]` `WINH10-AUD-10` (MEDIUM) — IMAP/SMTP bot exists; Graph ≠ mail; no EmailSignal pipeline.

---

## 3. Channels Hermes covers well (outbound / gateway)

Confirmed at this pin (toolsets `hermes-*` + `send_message` `_TEXT_SENDERS` / `_CHUNKED_ROUTES` / `_MEDIA_PLATFORMS_NOTE` + platform plugins):

**Prompt’s list, verified plus corrections:**

| Platform | Notes |
|---|---|
| Telegram, Discord, Matrix, Weixin, Signal, Yuanbao, Feishu, WhatsApp, Slack | Media-capable send_message note L588 |
| ntfy | `plugins/platforms/ntfy/` — topic push; no user identity |
| BlueBubbles / Photon | iMessage via local server (`_send_bluebubbles`; Photon adapter comments iMessage/BlueBubbles parity). Needs a Mac-side Messages/BlueBubbles host — **not a native Windows SMS/iMessage radio** |
| QQ | `qqbot` in `_TEXT_SENDERS` / `hermes-qqbot` |
| **SMS (Twilio)** | Missing from the prompt list; **present** |
| **Email (IMAP/SMTP)** | Missing from the prompt list; **present** |
| DingTalk, WeCom, Mattermost, Home Assistant, webhook, LINE/Teams (shared ingress comments) | Additional gateway platforms |

**Closest “text the user” analogs (not literal carrier SMS):** WhatsApp, Signal, Twilio SMS. Slack/Telegram/Discord are chat apps. ntfy is alerts. BlueBubbles/Photon are iMessage and assume a macOS (or BlueBubbles) endpoint — weak Windows-native path.

**Label:** `[MATCH]` `WINH10-AUD-11` (LOW) — Hermes is a real multi-platform messaging substrate; WhatsApp/Signal/Twilio are the practical personal-text channels.

---

## 4. Windows-side SMS despite no radio — `[OBSERVATION]`

Not scored against a Zola requirement. Plausible paths (do not pick one here):

1. **Use Hermes’s existing Twilio SMS plugin** — Windows client or `hermes gateway` with `TWILIO_*` + public webhook (ngrok/reverse proxy). This is already in-tree; not a new plugin type (`WINH06` plugin findings apply only if swapping vendors).
2. **Hermes plugin / `type: command` sender** for another CPaaS if Twilio is unacceptable.
3. **Paired-phone / Phone Link / companion-app sync entirely outside Hermes**, then inject text via `prompt.submit` or `hermes send`.
4. **Defer carrier SMS** and use WhatsApp or Signal as the “reach the user by message” channel.

WINH00 decides.

**Label:** `[OBSERVATION]` `WINH10-AUD-12` — Windows SMS is a bridge problem; Twilio is already a Hermes-shaped answer.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH10-AUD-09 | PARTIAL | MEDIUM | `plugins/platforms/sms/adapter.py`; Windows has no SMS radio | Twilio SMS exists; device SMS does not |
| WINH10-AUD-10 | PARTIAL | MEDIUM | `plugins/platforms/email/adapter.py`; Graph used by `teams_pipeline` | Mail bot ≠ EmailSignal; Graph is Teams not Outlook mail |
| WINH10-AUD-11 | MATCH | LOW | `toolsets.py` L202–240; `send_message_tool.py` L568–588 | Broad chat-platform coverage; WhatsApp/Signal/Twilio for “text” |
| WINH10-AUD-12 | OBSERVATION | — | Twilio plugin; Phone Link / CPaaS / defer | Windows SMS options; not a Hermes score |
