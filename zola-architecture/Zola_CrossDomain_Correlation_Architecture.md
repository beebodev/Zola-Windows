# Zola Cross-Domain Correlation Architecture

**Version:** 0.1 (stub)
**Created:** 2026-05-27
**Status:** Stub — full specification pending Phase 10 / Phase 11 design

---

## Purpose

Cross-domain correlation is Zola's ability to connect entities, events, and
signals across otherwise isolated data domains — Gmail, Calendar, Memory,
and future domains such as Drive and SMS — and surface relationships that
would be invisible when each domain is viewed in isolation.

This is not a feature. It is infrastructure. Every part of Zola that needs
to understand connections between things — the Daily Brief, the query path,
the proactive system, the conversational awareness system — depends on this
layer.

The value of cross-domain correlation is the answer to questions no single
domain can answer alone:

- "The meeting with John at 10am — what did he email you about last night?"
- "The Henderson project has been stalled for two weeks — is there anything
  on the calendar about it?"
- "You have a follow-up task that was flagged three days ago — when is the
  next time you're free to address it?"

These questions require entity resolution, relationship mapping, and
temporal correlation across domain boundaries. That is what this layer
provides.

---

## Core Principles

### One Authority for Cross-Domain Joins

No component performs its own ad-hoc cross-domain matching. All cross-domain
entity resolution and correlation goes through `CrossDomainCorrelator`. This
prevents fragmented, inconsistent matching logic spread across the codebase.

### Correlation Is Read-Only

`CrossDomainCorrelator` and `ContactRelationshipIndex` read from existing
data stores. They do not write to memory. They do not create new facts.
They surface connections between facts that already exist.

### Entity Resolution Is Conservative

When identity matching is ambiguous — "John" in a calendar event could be
any of three Johns in the contact index — the correlator does not guess.
It returns a low-confidence match or no match. False connections are worse
than missed connections.

### Derived Relationships Are Computed at Read Time

Per Zola's core architectural principle: derived relationships are inferred
at read time, not blindly saved. The correlator computes connections on
demand from live data. It does not cache derived relationships as persistent
facts.

---

## System Components

---

### 1. CrossDomainCorrelator

**Type:** General system service
**Status:** Stub — Phase 1 implementation is scoped to brief assembly only

#### Purpose

The central correlation engine. Takes structured input from one or more
domains and returns enriched context with matched entities, detected
connections, friction flags, and observational context.

Designed to be called by any system component that needs cross-domain
context. The Daily Brief is the first consumer. Future consumers include
the query path ("what do I need for my 10am?"), the proactive system, and
the conversational awareness system.

#### Phase 1 scope (Daily Brief only)

Phase 1 implements calendar-to-email entity matching and calendar-to-memory
entity matching, sufficient to support `DailyBriefAgent` assembly.

Specifically:
- match calendar event attendee names against Gmail sender names using
  `ContactRelationshipIndex`
- match calendar event titles against memory entity names and active project
  names
- detect schedule friction: double-bookings, back-to-back blocks,
  out-of-hours outliers
- identify free time blocks and pair them with flagged action items from
  `EmailIntelligenceAnalyzer`
- detect carryover items from prior day using memory and email context

#### Future scope (Phase 3+)

- semantic topic matching between email threads and calendar events
  (not just name matching)
- Drive document correlation — link Drive files referenced in calendar
  invites or emails to the relevant event
- SMS correlation — match SMS threads against calendar attendees and memory
  entities
- temporal correlation — surface patterns across time, not just today

#### Interface

```
CrossDomainCorrelator.correlate(
    calendarEvents: List<CalendarWindowSnapshot>,
    emailSignals: List<EmailSignal>,
    memoryContext: BriefMemoryContext,
    contactIndex: ContactRelationshipIndex,
    userId: String
) → CorrelatedBriefContext
```

Future general-purpose interface (Phase 3):
```
CrossDomainCorrelator.correlateForQuery(
    entities: List<ResolvedEntity>,
    domains: Set<CorrelationDomain>,
    userId: String
) → CorrelatedQueryContext
```

---

### 2. ContactRelationshipIndex

**Type:** General system service — lightweight queryable index
**Status:** Stub — Phase 1 implementation covers calendar + Gmail only

#### Purpose

A queryable index of known contacts and their cross-domain associations.
Provides entity resolution — the ability to determine that "John" in a
calendar event and "john.smith@company.com" in a Gmail thread are the
same person — along with relationship weight signals that inform
prioritization decisions.

Not a new data store. Built incrementally from data that already exists
in Gmail contact history, calendar co-occurrence, and memory entities.
The index is a derived view, not a primary record.

#### What the index holds

Per contact entry:
- canonical name (from memory entity if present, otherwise most common form)
- known email addresses
- calendar co-occurrence frequency (how often this person appears in events)
- Gmail interaction frequency (how often the user exchanges email with them)
- memory entity link (if a memory entity exists for this person)
- relationship weight score (derived from frequency + recency signals)
- last interaction timestamp

#### Phase 1 scope

Built from:
- Gmail sender history (`GmailManager.listInboxSummary` sender field)
- Calendar attendee names from recent events (`CalendarManager`)
- Memory entity names where entity type is PERSON

Phase 1 matching is name-based with fuzzy string matching. Exact email
address matching is preferred when available. Display name matching is
used as fallback with a confidence threshold — low-confidence matches
are flagged, not asserted.

#### Future scope

- contact enrichment from Google Contacts API
- co-occurrence learning over time (the more often "John from calendar"
  and "john.smith@" appear together, the higher the match confidence)
- household and relationship type classification

#### Privacy rules

- `ContactRelationshipIndex` stores relationship signals, not email content
- no email subject lines, no email bodies, no calendar event descriptions
  are stored in the index
- index entries can be deleted by the user through the privacy settings menu
- index is rebuilt from scratch when the user revokes Gmail or Calendar access

---

## Integration Points

This document connects to:

- `Zola_Daily_Brief_Architecture.md` — Daily Brief is the first consumer
  of `CrossDomainCorrelator` and `ContactRelationshipIndex`
- `Zola Master Architecture Plan.md` — derived relationships at read time
  principle, single authority ownership, privacy architecture
- `Zola_Architecture_Memory_Agency.md` — memory entity reads for person
  and project entity resolution
- `Zola_Communication_Intelligence_Architecture.md` — `EmailSignal` objects
  are the email-domain input to the correlator
- `Zola Autonomous Behavior Architecture.md` — future consumer: proactive
  system will use cross-domain correlation for contextual signals
- `Zola Conversational Attention Architecture.md` — future consumer: query
  path will use cross-domain correlation for pre-meeting context

---

## Open Questions

**OQ-CORR-1 — Index build frequency**
How frequently should `ContactRelationshipIndex` be rebuilt or updated?
On session start? Nightly? On a rolling basis as new emails and events
arrive? The answer affects both freshness and battery/performance cost.

**OQ-CORR-2 — Confidence threshold for name matching**
What is the minimum confidence score for `CrossDomainCorrelator` to assert
a match between a calendar attendee name and a Gmail sender? Below the
threshold, a match is returned with a low-confidence flag. What is the
threshold value?

**OQ-CORR-3 — General-purpose interface timing**
When does `CrossDomainCorrelator` grow from brief-specific to general-purpose?
The interface design should anticipate the general case from Phase 1 even if
only the brief-specific implementation is built. Phase 3 is the current
target for the general interface.

**OQ-CORR-4 — Drive integration**
Google Drive document correlation is the next high-value domain after Gmail
and Calendar. What permissions are required and what is the privacy model
for Drive content referenced in calendar events?

---

## Failure Modes and Safeguards

**Incorrect entity resolution**
Risk: `CrossDomainCorrelator` asserts that "John in the calendar" is the
same as "john.smith@" when they are different people, producing a misleading
connection in the brief.
Safeguard: conservative confidence threshold. Low-confidence matches are
flagged, not asserted. `DailyBriefAssembler` omits low-confidence connections
from `DailyBriefContext`.

**Index staleness**
Risk: `ContactRelationshipIndex` is stale — new contacts or changed email
addresses are not reflected.
Safeguard: index TTL enforced. Stale index returns lower confidence scores.
`CrossDomainCorrelator` falls back to name-only matching when index is stale.

**Privacy boundary crossing**
Risk: email content leaks into `ContactRelationshipIndex` via correlation
path.
Safeguard: correlator only receives `EmailSignal` metadata objects from
`EmailIntelligenceAnalyzer`. Raw email content is never passed to the
correlator. Architecture test confirms no raw email content path to the
index.

---

*Zola Cross-Domain Correlation Architecture version 0.1 (stub)*
*Created 2026-05-27*
*Full specification to be written before Phase 10 / Phase 11 build planning.*
*First consumer: Daily Brief (Phase 1 scoped implementation).*
