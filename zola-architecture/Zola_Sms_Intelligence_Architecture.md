# Zola SMS Intelligence Architecture

**Version:** 0.1
**Created:** 2026-06-01
**Status:** Design complete — pending Phase 12 implementation
**Companion document:** `Zola_Communication_Intelligence_Architecture.md`

> **Windows Track:** `S4` (Zola sending texts as a notification
> channel) is deferred. `S12` (the Daily Brief pipeline this whole
> document specifies — intelligence pipeline, brief surfacing, action
> offers) is deferred until basic email/SMS work. `S13` (reading the
> user's own incoming texts at all) is a real v1 goal but needs
> research into a Windows-viable access path — this document's
> `SmsWarmDataProvider` (component 1 below) assumes Android's on-device
> SMS content provider, which has no Windows equivalent. See
> `zola-architecture/lore/DESIGN_DECISIONS.md` and `OPEN_QUESTIONS.md`.

---

## Purpose

This document specifies the SMS intelligence pipeline for Zola — the
ability to read, analyze, surface, and act on text messages on the
user's behalf. It covers the analysis pipeline (`SmsIntelligenceAnalyzer`),
the output signal contract (`SmsSignal`), the warm data path, the brief
integration, the action/send flow, and the consent model.

SMS intelligence is the second domain in Zola's communication intelligence
layer. It follows the same architectural principles as email intelligence:
heuristics first, contact-gated, consent-explicit, analysis-does-not-equal-
storage. Where the two pipelines differ, this document calls out the
difference explicitly.

---

## Core Principles

### Known Contacts Only

SMS analysis is gated at the contact level. If the sender is not in the
user's phone contact list, the message does not enter the intelligence
pipeline. This single gate eliminates spam texts, verification codes,
delivery notifications, and automated messages without requiring pattern
matching. It also means Zola never analyzes messages from unknown senders,
which is a stronger privacy guarantee than the email noise filter.

### Analysis Does Not Equal Storage

Message content analyzed for intelligence signals is analyzed and discarded.
The output of analysis is structured signal metadata — `SmsSignal` objects —
not content. No message body persists after analysis produces its output.
Zola knows what matters. It does not store what was said.

### Consent Is Explicit and Separate

SMS analysis consent is collected separately from email analysis consent.
A user may opt into email intelligence without opting into SMS intelligence.
The consent moment explains in plain language what happens, what is read,
and what is discarded. There is no implicit consent.

### Thread Velocity Matters

Unlike email, SMS is a real-time medium. A thread with five messages in the
last two hours carries more urgency than a single message from three days
ago, regardless of content. Thread velocity is a first-class signal in the
SMS intelligence pipeline.

### Send Is Confirmed, Not Autonomous

Zola never sends a text message without explicit user confirmation. The
action flow is: surface the message → offer to reply → user provides
reply content → Zola reads it back → user confirms → send. There are
exactly two confirmation moments before any message is sent.

---

## System Components

---

### 1. SmsWarmDataProvider

> **Windows Track:** This component's entire data-access model
> (`Telephony.Sms.CONTENT_URI`, on-device contact resolution) is
> Android-only. The Windows equivalent is unresolved pending `S13`
> research — whatever replaces this component depends entirely on
> which access path (Phone Link, Twilio-provisioned number, etc.) that
> research lands on.

**Type:** Warm data adapter
**Status:** Partially exists — `SmsContentProviderPoller` handles presence
detection today; warm intelligence path is new in Phase 12
**Primary consumer:** `SmsIntelligenceAnalyzer`

#### Purpose

Provides `SmsIntelligenceAnalyzer` with the raw material it needs to
produce `SmsSignal` objects. Reads recent SMS threads from the Android
SMS content provider via `SmsContentProviderPoller` and packages them
into a structured input contract. Does not do intelligence analysis.

#### What it provides per thread

```
SmsThreadEntry {
    threadId: String
    contactName: String           // resolved display name from contacts
    phoneNumber: String           // normalized phone number
    messageCount: Int             // total messages in thread
    unreadCount: Int              // unread messages in thread
    recentMessages: List<SmsMessageEntry>  // last N messages (capped)
    lastMessageTimeMs: Long
    threadVelocityLastHours: Int  // message count in last 2 hours
    isKnownContact: Boolean       // always true — unknown contacts excluded
}

SmsMessageEntry {
    messageId: String
    body: String                  // full message body — released after analysis
    timeMs: Long
    isFromUser: Boolean           // true if user sent this message
}
```

#### Contact gate

`SmsWarmDataProvider` only produces `SmsThreadEntry` objects for threads
where the sender resolves to a named contact in the device contact list.
Threads where the sender is an unrecognized number are silently excluded
before any analysis runs. Contact resolution uses the existing
`ContactsLookupToolAdapter` resolution path.

#### Data freshness

SMS warm data is sensitive. TTL is 2 minutes, matching the existing
`recentMessagesSummary` TTL in `WarmToolContext`. Entries are wiped on
expiry via `ToolWarmStartAgent.purgeExpiredSensitiveEntries()`.

The warm path only runs when `smsAnalysisConsent` is true at fetch time.
If consent is false, no SMS data is fetched or stored in the warm context.

---

### 2. SmsIntelligenceAnalyzer

**Type:** Standalone analysis service
**Status:** New in Phase 12
**Primary consumer:** `DailyBriefAgent`

#### Purpose

Converts `SmsThreadEntry` data from `SmsWarmDataProvider` into structured
`SmsSignal` objects. Each signal carries everything a downstream consumer
needs to reason about a thread's relevance — without that consumer ever
touching raw message content.

`SmsIntelligenceAnalyzer` is the only component in Zola that reads SMS
message body content. It is responsible for ensuring that content does not
propagate beyond this boundary.

#### Analysis pipeline

**Stage 1 — Contact gate (always runs)**

Confirm `isKnownContact == true`. Any thread that reaches the analyzer
without a known contact is a pipeline error — log and skip. The gate is
belt-and-suspenders: `SmsWarmDataProvider` should have already excluded
unknown contacts.

**Stage 2 — Thread velocity scoring**

Compute thread velocity score from `threadVelocityLastHours`:
- 5+ messages in last 2 hours → HIGH velocity
- 2–4 messages in last 2 hours → MEDIUM velocity
- 0–1 messages in last 2 hours → LOW velocity

HIGH velocity threads receive a weight boost regardless of content. An
active back-and-forth conversation is inherently more urgent than a single
message.

**Stage 3 — Heuristic signal extraction**

Applied to message body content. Heuristic signals detected:

*Urgency signals (weight: HIGH)*
- Explicit urgency keywords: "urgent", "emergency", "911", "call me",
  "call me now", "are you okay", "need you", "help"
- Question requiring response: message ends with "?" and is not rhetorical
- Time-bound request: contains today/tomorrow + time reference
  ("are you free tomorrow", "can you make it at 3")

*Action signals (weight: MEDIUM)*
- Request for information or decision
- Scheduling or coordination language
  ("when are you", "can we", "does [time] work")
- Follow-up on prior conversation
  ("did you get my", "just checking", "following up")

*Informational signals (weight: LOW)*
- Status update with no required response
- Sharing content (photo/video/link with minimal text)
- Single-word or emoji-only response

*No-action signals (classified as ACKNOWLEDGED, not surfaced in brief)*
- "ok", "thanks", "sounds good", "👍", "got it" — terminal acknowledgments
  that do not require a response

**Stage 4 — Relationship weight scoring**

Score each thread using contact relationship data:
- Contact appears in memory as a known entity (family, close friend,
  colleague): 0.9
- Contact in calendar as meeting attendee within 48 hours: 1.0
- Contact in phone book, no memory match: 0.6
- Thread has HIGH velocity regardless of other signals: +0.2 boost

Threads with combined score < 0.4 are excluded from the brief.
Threads with combined score ≥ 0.4 produce an `SmsSignal`.

**Stage 5 — Signal assembly**

One `SmsSignal` per surviving thread. Raw message content is released
after this stage. The signal carries structured metadata only — no
message body, no quoted text.

---

### 3. SmsSignal

**Type:** Output contract
**Status:** New in Phase 12

#### Shape

```
SmsSignal {
    threadId: String
    contactName: String             // display name from contacts
    phoneNumber: String             // for send resolution only
    messageCount: Int               // messages in thread
    unreadCount: Int
    threadVelocity: ThreadVelocity  // HIGH, MEDIUM, LOW
    intent: SmsIntent               // ACTION_REQUEST, TIME_SENSITIVE,
                                    // INFORMATIONAL, ACKNOWLEDGED, UNCERTAIN
    urgencyScore: Float             // 0.0–1.0
    requiresResponse: Boolean       // heuristic: does this thread need a reply?
    lastMessagePreview: String?     // first 60 chars only, for brief prompt
                                    // construction — released after brief assembly
    relationshipWeight: Float       // 0.0–1.0
    analyzedAtMs: Long
}
```

#### Privacy enforcement

- `SmsIntelligenceAnalyzer` is the only component that reads SMS message
  body content
- Raw `SmsThreadEntry` objects are not passed to `DailyBriefAssembler`,
  `BriefPromptBuilder`, `CrossDomainCorrelator`, or any memory component
- `SmsSignal` objects contain no full message body
- `lastMessagePreview` is a 60-char truncation used only for brief prompt
  construction — it is never stored, never written to memory, and released
  after `BriefPromptBuilder` runs
- If the analyzer throws on a thread, that thread is omitted — never
  partially processed
- An architecture test must confirm no raw SMS body escapes the analyzer
  boundary

---

### 4. SMS Brief Integration

> **Windows Track:** Deferred with the rest of the Daily Brief pipeline
> (`S12`).

**Type:** Modification to existing pipeline
**Status:** New in Phase 12
**Owned by:** `DailyBriefAgent` / `DailyBriefAssembler`

#### Brief surfacing

When `smsAnalysisConsent` is true and `SmsIntelligenceAnalyzer` produces
signals, `DailyBriefAssembler` includes an SMS section in the brief package.

The brief surfaces:
- Threads with `requiresResponse == true` first, ordered by urgency score
- High-velocity threads second
- Informational threads only if signal density allows (SHORT brief mode
  excludes informational SMS)

For each surfaced thread, the brief includes: contact name, message count,
and a natural-language description of what the thread is about — derived
from `intent` and `urgencyScore`, not from `lastMessagePreview` directly.
`lastMessagePreview` is passed to `BriefPromptBuilder` as grounding context
so the prompt can produce a natural description without quoting the message.

Example brief phrasing (generated by Live, not hardcoded):
- "Micah sent you a few texts — looks like he's asking if you're free
  this weekend."
- "Bre sent an urgent message — she needs you to call her."
- "You have an active thread with your mom from this morning."

#### Action offer

After surfacing an SMS thread in the brief, Zola offers to help the user
respond. The offer is always opt-in — Zola asks, does not assume.

Standard offer phrasing:
- "Do you want to reply to Micah?"
- "Want me to send Bre a message?"

User response determines next step:
- "Yes, tell him [message content]" → Zola repeats the message back and
  asks for confirmation before sending
- "Yes" without content → Zola asks what to say
- "No" / "Not now" / any decline → Zola moves on
- No response → Zola moves on after a natural pause

#### Confirmation flow (two steps)

Step 1 — Content confirmation:
Zola repeats the proposed message: "I'll send Micah: [message]. Does that
sound right?"
- User confirms → Step 2
- User corrects → Zola updates and confirms again
- User cancels → flow ends, no message sent

Step 2 — Send confirmation:
"Sending now." → `MessageSendToolAdapter` with `_confirmed = "true"`

The `_confirmed` gate in `MessageSendToolAdapter` is the final safety gate.
It must be present and enforced at the adapter level regardless of the
confirmation flow above. Belt and suspenders.

---

### 5. SMS On-Demand Query Path

> **Windows Track:** This on-demand pattern (independent of the Daily
> Brief pipeline) is the likely shape of Zola-Windows's v1 SMS
> capability once `S13` research identifies a Windows-viable access
> path — not the full intelligence analyzer above, which is deferred
> with the rest of the Daily Brief (`S12`).

**Type:** Existing capability — already wired
**Status:** Functional via `MessageReadToolAdapter` and `MessageSendToolAdapter`

#### What exists today

On-demand SMS queries ("do I have any texts from Micah", "read my texts",
"send a message to Bre") are handled by the Live tool path:
- `readTextMessages` — `MessageReadToolAdapter.unread_summary` /
  `last_from_sender`
- `searchTextMessages` — `MessageSearchToolAdapter`
- `sendTextMessage` — `MessageSendToolAdapter` with `_confirmed` gate

The on-demand path is independent of the brief intelligence pipeline.
It operates directly on the SMS content provider at query time.

#### Known send bug

As of Phase 11 closeout, Zola can read texts on-demand correctly but the
`sendTextMessage` tool fails after user confirmation. The confirmation flow
works — Zola asks what to send and asks for confirmation — but the actual
send fails with a reported error.

Suspected causes (to be investigated in Phase 12 audit):
1. `SEND_SMS` permission not granted or revoked at runtime
2. `ContactsLookupToolAdapter` returning `not_found` or `ambiguous`,
   blocking the send before `SmsManager.sendTextMessage` is called
3. `SmsManager.sendTextMessage` called but fails silently
4. `_confirmed` flag not flowing correctly through the Live tool call chain
   — Live may not be passing `_confirmed = "true"` despite user confirmation

The Phase 12 pre-build audit must diagnose this bug before any SMS
intelligence build begins. A broken send path must be fixed before
`SmsIntelligenceAnalyzer` is built — the action flow in the brief
depends on send working correctly.

---

## Consent Model

### SMS analysis consent

SMS intelligence requires explicit user consent, collected separately from
email analysis consent. The two consents are independent: a user may opt
into email intelligence without opting into SMS intelligence.

**Consent flag:** `DailyBriefSettings.smsAnalysisConsent: Boolean`
(new field — added in Phase 12)

**Consent moment:** During daily brief opt-in, after email consent is
collected:

> "Would you also like me to include important texts in your brief? I'll
> only look at messages from your contacts — nothing from unknown numbers.
> I read the messages to understand what they're about, but nothing gets
> stored. You can turn this off anytime."

Consent is stored as `DailyBriefSettings.smsAnalysisConsent`. This flag
gates `SmsWarmDataProvider` at the fetch level — no SMS data is fetched
or analyzed when consent is false.

**Settings UI:** When the presence layer activates, an SMS toggle is added
to the DAILY BRIEF section of `SettingsPanel` in `ContextPanelLayer.kt`,
alongside the existing email toggle. The two toggles are independent.

**Voice commands:**
- "stop including my texts in the brief" → `smsAnalysisConsent = false`
- "include my texts in the brief" → `smsAnalysisConsent = true` (with
  confirmation of what this means)

**Revoking consent:** Setting `smsAnalysisConsent = false` immediately
stops all SMS data fetching. Any cached SMS warm data is wiped on next
`purgeExpiredSensitiveEntries()` call.

---

## Warm Data Integration

### WarmToolContext extension

`WarmToolContext` (in `agent/toolwarm/WarmToolContext.kt`) gains a new
sensitive field in Phase 12:

```kotlin
val recentSmsSummary: ToolWarmthEntry<SmsWarmContext>?
```

`SmsWarmContext` carries:
```kotlin
data class SmsWarmContext(
    val threads: List<SmsThreadEntry>,
    val fetchedAtMs: Long
)
```

This field follows the same sensitive data pattern as `recentMessagesSummary`:
- `isSensitive = true`
- TTL: 2 minutes
- Wiped by `purgeExpiredSensitiveEntries()`
- Only populated when `smsAnalysisConsent` is true

### ToolWarmStartAgent extension

`ToolWarmStartAgent` gains a new prefetch target `RECENT_SMS` in Phase 12.
The target is included in `decidePrefetchSet()` only when:
1. SMS provider access is available
2. `smsAnalysisConsent` is true at fetch time
3. Settings are ready (same `settingsReady` gate as `RECENT_MESSAGES`)

---

## DailyBriefSettings Extension

New fields added to `DailyBriefSettings` in Phase 12:

```kotlin
val smsAnalysisConsent: Boolean = false
val includedSources: Map<BriefSourceType, Boolean>
    // BriefSourceType.SMS added alongside existing CALENDAR, EMAIL,
    // MEMORY, WEATHER
```

`BriefSettingsWriter` gains corresponding setters:
- `setSmsAnalysisConsent(value: Boolean)`
- `setSourceEnabled(BriefSourceType.SMS, value: Boolean)`

---

## Differences from Email Intelligence

| Dimension | Email | SMS |
|-----------|-------|-----|
| Noise gate | Address pattern matching | Contact list gate only |
| Content access | Subject + snippet (Stage 3) / body first para (Stage 4) | Full message body (all stages) |
| Thread model | Individual messages grouped by sender | Explicit thread with velocity |
| Urgency signal | Subject keywords, thread size | Body keywords, velocity, response patterns |
| Action flow | None in Phase 11 (read only) | Surface + offer to reply + two-step confirm |
| Brief preview | Subject line | 60-char body truncation (prompt grounding only) |
| Consent flag | `emailAnalysisConsent` | `smsAnalysisConsent` (separate) |
| Model pass | Stage 4 Gemini for UNCERTAIN (Phase 11) | Phase 12+ — heuristics only in Phase 12 |

---

## Integration Points

This document connects to:

- `Zola_Communication_Intelligence_Architecture.md` — SMS intelligence is
  the second domain in the communication intelligence layer; shares
  core principles with email intelligence
- `Zola_Daily_Brief_Architecture.md` — `SmsIntelligenceAnalyzer` is called
  by `DailyBriefAgent`; `SmsSignal` is the brief input contract for SMS
- `Zola_CrossDomain_Correlation_Architecture.md` — `SmsSignal` objects are
  available as SMS-domain input to `CrossDomainCorrelator` in Phase 12+;
  a text from a calendar attendee the morning of a meeting is a high-value
  cross-domain signal
- `Zola Master Architecture Plan.md` — privacy architecture, truth ownership,
  confirmation-before-action principle
- `Zola_Agent_Architecture.md` — `DailyBriefAgent` (Agent 15) is the primary
  consumer; SMS intelligence does not write to memory or hold routing authority

---

## Phase 12 Build Sequence

Before any SMS intelligence build begins:

1. **Diagnose and fix the send bug.** The action flow in the brief depends
   on `sendTextMessage` working correctly. The audit must identify the root
   cause and fix it before build tracks begin.

2. **Add `smsAnalysisConsent` to `DailyBriefSettings`** and wire the consent
   opt-in into `BriefOptInCoordinator`.

3. **Build `SmsWarmDataProvider`** — extend `WarmToolContext` with
   `recentSmsSummary`, add `RECENT_SMS` prefetch target to
   `ToolWarmStartAgent`.

4. **Build `SmsIntelligenceAnalyzer`** — five-stage pipeline, contact-gated,
   produces `SmsSignal` objects.

5. **Wire `SmsIntelligenceAnalyzer` into `DailyBriefAssembler`** — SMS
   section, action offer, confirmation flow.

6. **Add SMS voice commands and settings UI toggle** — parallel to existing
   email commands and toggle.

---

## Open Questions

**OQ-SMS-1 — Model pass for SMS**
Phase 12 is heuristics-only for SMS, consistent with email Phase 10.
Should Phase 13 add a Gemini model pass for UNCERTAIN SMS threads,
parallel to email Stage 4? SMS body content is shorter and less
ambiguous than email — heuristics may be sufficient without a model pass.
Evaluate after Phase 12 production data.

**OQ-SMS-2 — RCS support**
`SmsContentProviderPoller` reads SMS/MMS. RCS messages may not appear
in the standard SMS content provider depending on the device and carrier.
What is the right approach for RCS thread access? Evaluate in Phase 12
audit.

**OQ-SMS-3 — lastMessagePreview in brief**
The 60-char preview is passed to `BriefPromptBuilder` as grounding context
so Live can describe the message naturally without quoting it. Is 60 chars
sufficient for Live to understand the message intent, or does it need more?
Conservative starting point — tune after Phase 12 production data.

**OQ-SMS-4 — Multi-message thread summarization**
When a thread has 5+ unread messages, the brief currently describes the
thread by intent and velocity. Should Zola summarize what the thread is
about across all messages? Requires reading all unread bodies, which has
privacy and cost implications. Defer to Phase 13.

**OQ-SMS-5 — Send bug root cause**
See Known send bug section above. Must be resolved before Phase 12 build
begins. Suspected causes documented — Phase 12 audit to diagnose.
