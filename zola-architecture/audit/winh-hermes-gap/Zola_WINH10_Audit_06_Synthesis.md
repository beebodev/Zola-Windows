# WINH10 Phase 6 — Synthesis: Messaging Surfaces vs Communication Intelligence

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Document of Truth: `Zola_Communication_Intelligence_Architecture.md`, `Zola_Sms_Intelligence_Architecture.md`. Cross-refs: `WINH04-AUD-02`/`06`, `WINH07-AUD-07`, `WINH08-AUD-02`/`06`. Fresh-start: capabilities, not Android SMS APIs.

Source: Audit_02 InboundIntelligence, Audit_03 ConfirmedSendFlow, Audit_04 ChannelCoverage, Audit_05 CrossReference.

Section 5 questions are not resolved here.

---

## Section 1 — Finding Summary Table

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH10-AUD-01 | PARTIAL | MEDIUM | `authz_mixin.py` L544–605; `run_inbound.py` L191–205 | Allowlist/pairing gate, not silent contact-list exclusion |
| WINH10-AUD-02 | GAP | HIGH | searched SmsSignal / analyzers; session transcripts | No signal-extract-then-discard layer |
| WINH10-AUD-03 | GAP | MEDIUM | searched threadVelocity | No first-class thread-velocity signal |
| WINH10-AUD-04 | PARTIAL | MEDIUM | `run_startup.py` L821–854; `SMS_ALLOWED_USERS` | Channel allowlist ≠ analysis consent |
| WINH10-AUD-05 | MATCH | LOW | `send_message_tool.py` L22–24; `toolsets.py` L185 | `send_message` not model-callable |
| WINH10-AUD-06 | RISK | HIGH | `handle_message` → `adapter.send`; `delivery.py` L254 | Live gateway reply is autonomous send |
| WINH10-AUD-07 | GAP | HIGH | `send_cmd.py`; `scheduler_delivery.py`; `mcp_serve.py` | Host send paths have no two-step confirm |
| WINH10-AUD-09 | PARTIAL | MEDIUM | `plugins/platforms/sms/adapter.py` | Twilio SMS exists; Windows has no handset radio |
| WINH10-AUD-10 | PARTIAL | MEDIUM | `plugins/platforms/email/adapter.py`; Graph/`teams_pipeline` | Mail bot ≠ EmailSignal; Graph is Teams |
| WINH10-AUD-11 | MATCH | LOW | `toolsets.py` L202–240; media note L588 | Broad chat substrate; WhatsApp/Signal/Twilio for “text” |
| WINH10-AUD-12 | OBSERVATION | — | Twilio plugin; out-of-process Phone Link / CPaaS | Windows SMS options; not a Hermes score |
| WINH10-AUD-13 | RISK | MEDIUM | `session.py`; cite `WINH04-AUD-02`/`06` | Comms bodies persist like any other turn |

**Counts:** 12 findings — **3 HIGH**, **6 MEDIUM**, **2 LOW**, **1 OBSERVATION**.

HIGH: AUD-02, AUD-06, AUD-07. MEDIUM: AUD-01, 03, 04, 09, 10, 13. LOW: AUD-05, 11. OBSERVATION: AUD-12 (in table; not a Zola miss).

`[OBSERVATION]` counted as in WINH08. Phase 5 citations of `WINH08-AUD-02`/`06` and `WINH07-AUD-07` are not extra rows.

---

## Section 2 — What Hermes covers as-is (messaging surfaces)

**Direct answer:** Hermes **does** give Zola-Windows a **cross-channel messaging substrate** (gateway adapters + `send_message` host helpers). **Message intelligence** (contact-gated heuristic signals, analysis-not-storage, two-step confirmed send, independent analysis consents) is **scratch work** on top of that substrate — not something to enable with a config flag.

The prompt’s spot-check missed **Twilio SMS** and **IMAP/SMTP email** because they are `plugins/platforms/sms` and `plugins/platforms/email`, not `tools/sms_*.py`. Those are **chat transports**: allowed senders talk to the agent; Hermes replies on the same channel. They are not `SmsIntelligenceAnalyzer` / `EmailIntelligenceAnalyzer`.

`send_message` is correctly **not** a model tool (`WINH10-AUD-05`). Cron, `hermes send`, kanban notifier, and `hermes mcp serve` `messages_send` call the helpers with **configure-once** authorization. Live gateway replies still **send autonomously** (`WINH10-AUD-06`).

WhatsApp, Signal, and Twilio are the practical “text the user” channels. Microsoft Graph in this tag is **Teams meetings**, not Outlook mail.

---

## Section 3 — What needs a Zola-built adapter layer

| ID | Wrap | Adapter owns |
|---|---|---|
| AUD-01 / AUD-04 | `{P}_ALLOWED_USERS`, pairing, email noreply drop | Map Zola “known contact” onto an allowlist (or a Windows contacts source feeding that list). Do not treat pairing-open as contact-gate. Add a **separate** analysis-consent flag if shipping a brief — do not reuse “may chat with the bot.” |
| AUD-05 / AUD-11 | `send_message_tool` / platform adapters / `hermes send` | Windows client uses host send or gateway; keep `send_message` **out** of the model toolset. |
| AUD-09 | Twilio `SmsAdapter` | If carrier SMS is in scope: run gateway with Twilio + webhook; Windows UI does not implement a radio. |
| AUD-10 | Email IMAP/SMTP adapter | Only if “email Zola as a bot” is wanted. Outlook mail still needs Graph Mail or Gmail connector — not the Teams Graph client. |
| AUD-06 / AUD-07 | `adapter.send` / CLI / cron delivery | Adapter must own Zola’s two-step confirm **in front of** these APIs (read-back UI, then send). Hermes will not add `_confirmed` by itself. |

---

## Section 4 — What must be built from scratch

### (a) Message-intelligence layer (software, any channel)

| ID | Capability | Why scratch | Finding |
|---|---|---|---|
| Signal extraction then discard | Urgency/intent/`EmailSignal`/`SmsSignal`; bodies not retained | Hermes uses raw text as the turn | AUD-02 |
| Thread velocity | N messages in last H hours as a named signal | Absent | AUD-03 |
| Analysis consents | Independent SMS vs email analysis opt-in | Allowlists are chat access | AUD-04 remainder |
| Two-step confirmed send | Offer → content → read-back → confirm → send | Gateway reply + host send are one-shot | AUD-06, AUD-07 |
| Comms retention policy | Bodies never enter MEMORY.md / provider `sync_turn` | Ordinary transcripts + `WINH04-AUD-02`/`06` | AUD-13 |

Contact-gate **remainder** (silent unknown-number drop vs pairing) is adapter policy on AUD-01, not a new Hermes module.

### (b) Literal SMS on Windows (independent of Hermes)

Windows has **no cellular radio / SMS content provider**. That is not scored as “Hermes forgot Telephony.” Hermes **already** offers a Twilio bridge (`WINH10-AUD-09`). Remaining product choice (Twilio vs WhatsApp/Signal vs defer vs Phone Link) is Section 5 / WINH00 (`WINH10-AUD-12`).

Do not merge (a) and (b): a perfect analyzer still cannot read handset SMS on Windows without a bridge; a perfect Twilio setup still lacks Zola’s signal/consent/confirm layers.

---

## Section 5 — Open questions for WINH00

Do not resolve these here.

1. **Channel strategy.** Twilio SMS (already in Hermes), WhatsApp/Signal as the practical “text the user” channel, or defer carrier-SMS-equivalent the way WINH09 flagged voice identity as a possible deferral?

2. **Email.** IMAP/SMTP bot vs Outlook (Graph **Mail**, not the existing Teams Graph helper) vs a Gmail connector (`connections_tool` / himalaya). Which matches the user’s accounts?

3. **Confirmed send.** Cron/CLI-only `send_message` is **not** an adequate foundation for Zola’s two-step flow (`WINH10-AUD-07`). Does Zola-Windows build its own approval UI in front of `send_message_tool` / `adapter.send`, including **gateway chat replies** (`WINH10-AUD-06`)?

4. **Authorization framing.** This phase **reinforces** `WINH08-AUD-02`/`06` (cron delivery) and does **not** raise `WINH07-AUD-07`: `smart` never wrapped host send or gateway replies. New HIGH work for Windows messaging is **AUD-06/07** (confirm UX) and **AUD-02** (intelligence layer), not a restatement of those older IDs.
