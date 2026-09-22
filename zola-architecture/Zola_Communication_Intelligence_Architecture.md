# Zola Communication Intelligence Architecture

**Version:** 1.0
**Updated:** 2026-06-02
**Status:** Reflects Phase 11 (email) + Phase 12 (SMS) build — documentation of what shipped

---

## Purpose

Communication Intelligence turns raw inbox and SMS warm data into structured signals (`EmailSignal`, `SmsSignal`) that downstream consumers can reason about without reading message bodies in the brief pipeline.

The Daily Brief is the primary consumer. Both domains share consent, privacy, and heuristics-first principles but use independent consent flags and warm-fetch gates.

> **Windows Track:** This document describes the Android-built Daily
> Brief pipeline (Phase 11 email + Phase 12 SMS) in full, including the
> relationship-scoring and urgency-heuristics layers. For Zola-Windows,
> the Daily Brief pipeline itself is deferred (`S12`) — basic email and
> SMS read/send come first. See `zola-architecture/lore/DESIGN_DECISIONS.md`.

---

## Shared Principles

### Analysis does not equal storage

Structured signal metadata is produced at assembly time and released after prompt build (SMS preview) or analyzer return (email). No analyzed body text is written to memory or Firestore.

### Heuristics first, model second (email only)

Email Stage 4 may call Gemini for UNCERTAIN rows when `emailAnalysisConsent` is true. SMS in Phase 12 is **heuristics-only** (P12-D10) — no Gemini model pass.

### Consent is explicit and specific

- **Email:** `DailyBriefSettings.emailAnalysisConsent` — gates snippet fetch and Stage 4 model pass.
- **SMS:** `DailyBriefSettings.smsAnalysisConsent` + `includedSources[SMS]` — gates `RECENT_SMS` warm prefetch and brief assembly.

Separate consents; either can be off while the other is on.

### Communication intelligence is not memory

Signals are ephemeral pipeline artifacts. Relationship weight in `EmailSignal` is a heuristic score for brief ranking — not a durable memory fact.

---

## Domain 1 — Email Intelligence (Phase 11)

> **Windows Track:** Email channel is Gmail via Hermes's dedicated
> connector (`P3`). Whether the five-stage analysis pipeline below
> (relationship weight, Gemini Stage-4 model pass, etc.) is built at
> all for Windows is part of the deferred Daily Brief scope (`S12`) —
> not yet decided beyond "not v1."

**Analyzer:** `EmailIntelligenceAnalyzer`
**Warm input:** `MessagesSummary.messages: List<MessageEntry>` (legacy aggregate fields removed P12-T6)
**Warm fetch:** `ToolWarmStartAgent` → Gmail inbox summaries; snippet populated only when `emailAnalysisConsent` is true at map time
**Output:** `EmailSignal`

### Pipeline (five stages)

| Stage | Name | Notes |
|-------|------|-------|
| 1 | Noise elimination | Address, display-name, and subject heuristics |
| 2 | Relationship weight | Calendar attendee, project label, repeat-address rules — **not** memory entity names (see OQ-BRIEF-7) |
| 3 | Heuristic classification | Urgency/subject patterns; CONFIDENT vs UNCERTAIN |
| 4 | Model pass | Gemini on UNCERTAIN rows; snippet-only input (200-char cap); max 3 calls per brief; consent-gated |
| 5 | Signal assembly | `EmailSignal` per message; no body retained |

### EmailSignal (brief contract)

Key fields: `senderName`, `subject`, `unreadCount`, `relationshipWeight`, `isNoise`, `intent`, `urgencyScore`, `actionItemSummary` (Stage 4).

---

## Domain 2 — SMS Intelligence (Phase 12)

> **Windows Track:** Reading the user's own incoming SMS is a real v1
> goal, but the access mechanism this pipeline assumes
> (`Telephony.Sms.CONTENT_URI`, Android-only) has no Windows
> equivalent — needs research (`S13`). The intelligence/scoring layer
> below is deferred with the rest of the Daily Brief (`S12`); Zola
> *sending* texts as a notification channel stays deferred separately
> (`S4`).

**Analyzer:** `SmsIntelligenceAnalyzer`
**Warm input:** `SmsWarmContext.threads: List<SmsThreadEntry>` from `SmsWarmDataProvider`
**Warm fetch:** `ToolWarmStartAgent` `RECENT_SMS` target when `smsAnalysisConsent` and source enabled
**Output:** `SmsSignal`
**Provider:** `Telephony.Sms.CONTENT_URI` — SMS/MMS only; RCS not in provider (OQ-SMS-2 deferred)

### Pipeline (five stages, heuristics-only)

| Stage | Name | Notes |
|-------|------|-------|
| 1 | Contact gate | Unknown numbers excluded (`isKnownContact`) |
| 2 | Thread velocity | Maps warm `threadVelocityScore` → `ThreadVelocity` enum |
| 3 | Intent heuristics | Keyword/pattern classification → `SmsIntent` |
| 4 | Urgency scoring | Velocity + unread + intent → urgency |
| 5 | Signal assembly | `SmsSignal` including `lastMessagePreview` (60-char cap, P12-D09) |

### SmsSignal (brief contract)

Key fields: `threadId`, `contactName`, `phoneNumber`, `unreadCount`, `threadVelocity`, `intent`, `urgencyScore`, `requiresResponse`, `lastMessagePreview`, `isKnownContact`.

Preview is passed to `BriefPromptBuilder` as grounding only and is not stored downstream.

---

## Brief Integration

**Assembler:** `DailyBriefAssembler` invokes both analyzers when respective consent + source flags allow.

**Prompt:** `BriefPromptBuilder` builds email and SMS sections from signals; action-offer instructions for `requiresResponse == true` SMS threads (P12-D11).

**Action flow:** User accepts offer → existing NL send path (`MessageSendIntentHandler` + `SmsNlSendConfirmationStore`) — no new confirmation mechanism.

**Cross-domain:** `CrossDomainCorrelator` matches calendar attendees to email senders via `MessageEntry.displayName` projection (post P12-T6).

---

## Consent and Settings Surfaces

| Surface | Email | SMS |
|---------|-------|-----|
| Opt-in | `BriefOptInCoordinator` email moment | SMS follow-up after email consent (P12-T5) |
| Voice | `QueryRoutingService` email patterns | SMS patterns + B1 bypass exclusion (P12-T6) |
| Settings UI | Context panel email toggle | Context panel SMS toggle (build-only; 3D gate) |
| Writes | `BriefSettingsWriter.setEmailAnalysisConsent` | `setSmsAnalysisConsent` + `setSourceEnabled(SMS)` |

---

## Integration Points

- `Zola_Daily_Brief_Architecture.md` — assembly, delivery, prompt
- `Zola_Sms_Intelligence_Architecture.md` — SMS pipeline detail
- `Zola_CrossDomain_Correlation_Architecture.md` — calendar ↔ email name matching
- `Zola Master Architecture Plan.md` — privacy and truth ownership

---

## Open Questions (post–Phase 12)

See `lore/OPEN_QUESTIONS.md`:

- **OQ-BRIEF-7** — memory/contact-aware email relationship weights (Phase 13)
- **OQ-COMM-1 / OQ-COMM-2** — Stage 4 snippet length and daily rate cap tuning (Phase 13)
- **OQ-SMS-1** — SMS model pass (Phase 13+)
- **OQ-SMS-2** — RCS provider path (Phase 13+)
- **OQ-SMS-3** — `lastMessagePreview` length tuning (Phase 13)
- **OQ-SMS-4** — multi-message thread summarization (Phase 13)

---

*Zola Communication Intelligence Architecture v1.0 — documents Phase 11 email + Phase 12 SMS as built.*
