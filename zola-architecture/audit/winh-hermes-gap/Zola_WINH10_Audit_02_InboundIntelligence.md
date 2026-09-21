# WINH10 Audit 02 — Inbound Message Intelligence: Contact Gate, Signals, Consent

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Communication_Intelligence_Architecture.md` Shared Principles + both domains; `Zola_Sms_Intelligence_Architecture.md` Core Principles and System Components. Capability requirements only (not Android `Telephony.Sms` / contact-provider APIs).

Inbound path actually traced (names confirmed, not assumed from the prompt):

```
platform adapter (SMS Twilio webhook / Email IMAP poll / Discord/Telegram/…)
  → BasePlatformAdapter.handle_message          # gateway/platforms/base.py L3633
  → GatewayInboundMixin._hm_admit_event         # gateway/run_inbound.py L112
       pre_gateway_dispatch hook
       _is_user_authorized_for_source           # gateway/run.py L3935 → authz_mixin.py L544
  → agent turn on the session (raw event.text)
  → adapter.send reply on the same chat
```

`tools/bot_relay.py` / `tools/bot_mode_dm.py` / `tools/bot_mode_probe.py` are **agent-to-agent** Bot Chat DMs (Desktop roster), not user SMS/email. `tools/discord_tool.py` is a **model tool** for Discord REST introspection (`search_members`, `fetch_messages`), not the inbound gateway adapter (`plugins/platforms/discord/adapter.py`).

---

## 1. Sender / contact gating

Zola SMS: unknown numbers are **silently excluded** before analysis (`isKnownContact` on the device contact list).

Hermes does **not** resolve senders against a contact book. It gates on an **operator allowlist / pairing store**:

- `GatewayAuthzMixin._is_user_authorized` (`gateway/authz_mixin.py` L544–605): `{PLATFORM}_ALLOWED_USERS`, group allowlists, pairing-store approval, `{PLATFORM}_ALLOW_ALL_USERS`, `GATEWAY_ALLOW_ALL_USERS`; **default deny** if none of those grant.
- Startup warns if no allowlist is set (`gateway/run_startup.py` L834–854). Open `dm_policy` without allow-all **refuses to start** (L857–868).
- Unauthorized DMs get a pairing code (`run_inbound.py` L191–205), not silent drop — an unknown sender can *request* admission.
- **SMS:** `SMS_ALLOWED_USERS` (E.164) on `plugins/platforms/sms/adapter.py` L9, `plugin.yaml`; webhook still builds a `MessageEvent` with full `Body` (L254–268) and relies on the shared authz gate.
- **Email:** extra pre-dispatch `_sender_accepted` (`plugins/platforms/email/adapter.py` L602–628): drop self, automated/noreply substrings (`_NOREPLY_PATTERNS` L38–42), require `EMAIL_ALLOWED_USERS` unless `EMAIL_ALLOW_ALL_USERS` / `GATEWAY_ALLOW_ALL_USERS`, optional From: authentication.

Connecting a bot token is **not** by itself “everyone may talk.” Connecting **plus** an allowlist (or pairing, or allow-all) is. That is a **who-may-converse** gate, not a **known-contact-before-analysis** gate. Eligible inbound is then a full agent turn, not a signal pipeline.

**Label:** `[PARTIAL]` `WINH10-AUD-01` (MEDIUM) — real sender gate (allowlist/pairing/noreply); not Zola’s silent contact-list exclusion; unknown users can pair.

---

## 2. Structured signal extraction without body retention

Zola: `SmsIntelligenceAnalyzer` / `EmailIntelligenceAnalyzer` emit `SmsSignal` / `EmailSignal`; bodies discarded; communication intelligence is not memory.

Hermes: **no** analog. Searched `SmsSignal`, `EmailSignal`, `SmsIntelligenceAnalyzer`, `threadVelocity`, `urgencyScore`, `smsAnalysisConsent` — **no production hits**. Inbound `event.text` is the user message of a gateway session (`run_inbound.py` pipeline). Sessions persist transcripts (`gateway/session.py` SessionTranscriptMixin). There is no assemble-signal-then-drop-body layer.

The bundled skill `skills/email/email-inbox-triage/SKILL.md` is a **prompt procedure** for a live agent (classify threads, draft, ask approval). It still **reads full thread bodies** via connector skills and does not emit an ephemeral `EmailSignal` contract.

**Label:** `[GAP]` `WINH10-AUD-02` (HIGH) — no analysis-then-discard signal layer; raw bodies are conversational input (and stored on the session).

---

## 3. Thread velocity as a distinct signal

Zola: first-class `threadVelocityLastHours` → HIGH/MEDIUM/LOW.

Hermes “velocity” hits are **token throughput** on the status bar (`hermes_cli/cli_status_bar_mixin.py`), not message-rate in a thread. No `N messages in last H hours` field on `MessageEvent` or session.

**Label:** `[GAP]` `WINH10-AUD-03` (MEDIUM) — thread velocity is a Zola construct; not present.

---

## 4. Consent gating per channel

Zola: independent `smsAnalysisConsent` / `emailAnalysisConsent` before warm-fetch and analysis.

Hermes analogs:

| Mechanism | What it gates |
|---|---|
| Platform enabled + env credentials | Adapter starts |
| `{P}_ALLOWED_USERS` / pairing / allow-all | **Who** may start an agent turn |
| `smsAnalysisConsent`-shaped flag | **Absent** |

There is no “include texts in the brief / analyze and discard” consent distinct from “this number may chat with the bot.” Enabling SMS (`TWILIO_*` + webhook) and listing a number in `SMS_ALLOWED_USERS` means **full conversational agent**, including tools on `hermes-sms` (`toolsets.py` L228).

Email `EMAIL_ALLOWED_USERS` is the same shape. Separate email vs SMS analysis consents do not exist.

**Label:** `[PARTIAL]` `WINH10-AUD-04` (MEDIUM) — explicit per-platform allowlists exist; they are access control for a chat bot, not analysis-only consent.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH10-AUD-01 | PARTIAL | MEDIUM | `authz_mixin.py` L544–605; `run_inbound.py` L191–205; `email/adapter.py` L602–628 | Allowlist/pairing gate, not silent contact-list exclusion |
| WINH10-AUD-02 | GAP | HIGH | searched SmsSignal/EmailIntelligenceAnalyzer; `session.py` transcripts | No signal-extract-then-discard; raw body is the turn |
| WINH10-AUD-03 | GAP | MEDIUM | searched threadVelocity / last H hours | No first-class thread-velocity signal |
| WINH10-AUD-04 | PARTIAL | MEDIUM | `run_startup.py` L821–854; `sms/plugin.yaml` `SMS_ALLOWED_USERS` | Channel allowlist ≠ `smsAnalysisConsent` |
