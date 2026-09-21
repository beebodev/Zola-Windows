# Social Graph Reasoning Architecture

### Foundational Architecture for Dynamic Models of People in the User's Life

---

## Vision

The Social Graph Reasoning Architecture defines how Zola builds and
maintains dynamic models of the people in the user's life — not as
static entries in a contact list, but as understood presences with
relationship structure, conversational patterns, and behavioral
context that evolves over time.

The goal is not to profile people. The goal is to understand the
user's world well enough that when someone important comes up in
conversation, Zola already knows who they are, how they fit, and
what the user has said about them — without the user having to
re-explain.

The system should eventually feel less like:

> "an assistant that remembers the names you've mentioned"

and more like:

> "a presence that knows the people in your world and understands
> how they matter to you."

---

## Core Philosophy

### People Earn Their Place in the Graph

Not every name mentioned becomes a social graph node. A name
mentioned once in passing stays in episodic memory. A person earns
a social graph node by meeting a Named Recurrence Threshold —
appearing across enough distinct sessions within a meaningful time
window to demonstrate that they are a recurring presence in the
user's life, not a passing reference.

This threshold prevents the graph from filling with noise. It ensures
that every person in Zola's social graph is someone who genuinely
matters to the user's ongoing world.

### Third-Party Beliefs Are Held Loosely

Everything Zola knows about people in the user's life comes through
the user's perspective. When the user describes someone — especially
in frustration, or in the middle of a conflict — that is one side of
a story. Zola is not hearing from the person directly. She is hearing
the user's account.

This is reflected architecturally through source metadata and
confidence ceilings, not through a mechanical flag. Facts about
third parties structurally carry a lower confidence ceiling than
direct user facts. The Self-Model Awareness hedging register handles
how this surfaces in language — naturally, through phrasing, never
through explicit disclaimers.

### Observations Are Background Texture, Not Headlines

The social graph informs Zola's responses as background intelligence.
It does not narrate itself. Zola should feel perceptive — aware of
who Marcus is and what the user has said about him — without ever
announcing that she has been building a model. When a social graph
observation surfaces, it surfaces because it is directly relevant to
something happening right now. Never as a standalone disclosure.

### Transient Emotion Does Not Harden Into Fact

The user will vent. The user will describe people in the heat of a
frustrating moment with language that does not represent a considered
assessment. The architecture must prevent transient emotional content
from writing permanent behavioral traits onto entity profiles. Zola
heard that Marcus was having a bad day. She should not remember
Marcus as someone who is consistently unreliable based on that.

This protection is structural — through the PROVISIONAL lifecycle
state in the write pipeline — not through prompt instructions or
post-hoc filtering.

---

## Non-Goals

Social Graph Reasoning is not:

- a contact list or address book replacement
- a psychological profiling system — it tracks structural facts and
  stated behaviors, not inferred personality types
- an emotional register profiling system in v1 — longitudinal
  per-entity tone analysis is deferred to v2
- a surveillance system — it builds models from what the user
  actively shares in conversation, not from environmental observation
- an independent memory store — it reads from and extends the
  existing world graph, it does not create a parallel entity system
- an interrogation system — it surfaces gaps when relevant, not as
  a scheduled questionnaire
- a parallel delivery path — all output goes through prompt injection
  or the initiative queue per RIL-D04

---

## Architectural Position

Social Graph Reasoning sits between the existing world graph and two
downstream consumers: the prompt assembly layer and the initiative
queue.

It reads from:

- world graph entity documents and relationship edges
- `KNOWS_ABOUT` awareness edges and their `mentionCount` and
  `firstMentionedAt` fields
- `DistinctSessionMentionTracker` for session recurrence counts
- `EpisodicMemoryEntry.linkedEntityIds` for entity-session linkage
- `MemoryCorrectionLog` for correction history on third-party facts
- `EntityBeliefView` from Self-Model Awareness for unified entity
  belief aggregation
- `SessionBoundaryResolver` from Temporal Reasoning for session
  age calculations
- `TemporalRecencyFormatter` from Temporal Reasoning for
  natural-language recency labels
- `ConversationContext` session tone signal (conversation-level only
  in v1)

It produces:

- **Social context blocks** — structured context about who people
  are and how they appear in the user's life, injected into prompt
  assembly
- **Gap signals** — when Zola's knowledge of a relevant person is
  thin and that gap matters to something happening now
- **Initiative candidates** — when a social graph observation is
  relevant enough to surface proactively

It never:

- writes entity attributes or relationship edges without going
  through `RelationshipWriteGovernor` and `DurableWriteAuthority`
- modifies belief lifecycle states directly
- invokes speech execution classes
- produces behavioral assessments of third parties beyond what the
  user has explicitly stated

---

## Named Recurrence Threshold

A person does not receive a social graph node on first mention. They
earn one by meeting both conditions of the Named Recurrence Threshold:

**Condition 1 — Explicit introduction:** The user explicitly
introduces the person to Zola ("Marcus works at the shop with me",
"that's my brother") or the person is confirmed through direct
entity creation.

**OR**

**Condition 2 — Session recurrence:** The person is mentioned across
`SOCIAL_GRAPH_MIN_SESSIONS` distinct sessions within
`SOCIAL_GRAPH_RECURRENCE_WINDOW_DAYS` days.

Initial values (named constants, calibration-ready):
- `SOCIAL_GRAPH_MIN_SESSIONS = 3`
- `SOCIAL_GRAPH_RECURRENCE_WINDOW_DAYS = 90`

Until a person crosses the Named Recurrence Threshold, their name
stays in episodic memory via `EpisodicMemoryEntry.linkedEntityIds`
and `KNOWS_ABOUT` awareness edges. They do not receive a social
graph profile. They are not tracked for tone or behavioral patterns.

### Why Distinct Sessions, Not Raw Mentions

A person mentioned twelve times in one conversation is not
necessarily a recurring presence in the user's life — they might
be the subject of one extended story. A person mentioned twice in
three separate sessions almost certainly is. The threshold is
designed to require spread across time, not accumulation within a
moment.

---

## DistinctSessionMentionTracker

### Purpose

Track how many distinct sessions have mentioned a given entity, as
a prerequisite for Named Recurrence Threshold evaluation.

### Why a Separate Component

`KNOWS_ABOUT.mentionCount` is confirmed to increment only on entity
creation — not on re-mention (P29-SGR-AUD-11, AUD-28). It does not
track session boundaries. Repurposing it would corrupt its semantics
and create confusion about what it represents.

The tracker is a dedicated lightweight store, separate from the
awareness edge, so that the semantic meaning of `KNOWS_ABOUT` remains
clean.

### Storage

Stored as a lightweight Firestore document per entity per user:
`users/{userId}/memory/session_mentions/{entityId}`

Fields:
- `entityId: String`
- `distinctSessionCount: Int`
- `lastSessionId: String` — prevents double-counting within a session
- `firstSessionAt: Long` — epoch ms of first session mention
- `lastSessionAt: Long` — epoch ms of most recent session mention
- `windowStartAt: Long` — epoch ms of window start for threshold
  evaluation

### Increment Logic

Once per session per entity — not per mention. When an entity is
mentioned in a session, the tracker checks whether the current
session ID differs from `lastSessionId`. If different, it increments
`distinctSessionCount` and updates `lastSessionId` and
`lastSessionAt`. Multiple mentions of the same entity within one
session produce one increment.

### Window Enforcement

At threshold evaluation time, the tracker checks whether
`lastSessionAt - windowStartAt` is within
`SOCIAL_GRAPH_RECURRENCE_WINDOW_DAYS`. If the window has expired
without crossing the threshold, `distinctSessionCount` resets and
`windowStartAt` advances to the first mention within the new window.

---

## Same-Name Disambiguation

### The Problem

Two different people in the user's life may share a name. "Tom from
work" and "Tom the father-in-law" are different entities. Auto-
generating suffixed IDs (`person_tom_2`) creates permanent
disambiguation debt — the graph accumulates unclear nodes that are
difficult to merge or correct later, and semantic search will
conflate them.

### The Solution

When the Named Recurrence Threshold is crossed for a name that
already exists as an entity in the graph, Social Graph Reasoning
triggers a disambiguation request before creating a new node.

Zola surfaces a natural clarification at an appropriate conversational
moment: "You've mentioned Tom a few times — is this the same Tom
[relationship context], or someone else?"

The user confirms or clarifies. Entity creation proceeds only after
disambiguation is resolved.

### Clarification Fail-Soft

In a Live Audio session, the user may ignore the disambiguation
question or change the subject before answering. If this occurs:

- the clarification hold is dropped immediately
- the data is routed to an ephemeral disambiguation token that does
  not become a permanent entity
- the Named Recurrence Threshold clock is not reset — subsequent
  mentions continue to accumulate
- the next appropriate conversational moment triggers a new
  disambiguation attempt, not immediately but at natural re-entry

The pipeline never hangs waiting for a clarification response. A
dropped clarification is not a failure — it is a deferral.

### Clarification Throttle — Preventing Disambiguation Loops

If disambiguation is deflected or ignored across
`DISAMBIGUATION_BACKOFF_THRESHOLD` consecutive sessions, the verbal
clarification prompt is suppressed for `DISAMBIGUATION_BACKOFF_DAYS`
days. The system does not ask again during this back-off window.

Initial values (named constants, calibration-ready):
- `DISAMBIGUATION_BACKOFF_THRESHOLD = 3`
- `DISAMBIGUATION_BACKOFF_DAYS = 14`

During the back-off window, new episodic attributes for the ambiguous
name are appended to the generic ephemeral token with context-clue
tags derived from co-occurring signals in the turn — workspace
context, topic domain, other named entities in the same turn. These
tags allow implicit internal routing (matching "Tom" alongside "shop"
or "work" routes differently from "Tom" alongside "family") without
requiring the user to resolve the ambiguity explicitly.

When the back-off window expires, the disambiguation prompt is
eligible to surface again at the next natural conversational moment
— not immediately on window expiry.

The throttle state is tracked per ambiguous name pair, not globally.
Backing off on "Tom" disambiguation does not affect disambiguation
requests for other names.

---

## Long-Term Architectural Pillars

---

## 1. SocialGraphNodeEvaluator

### Purpose

Evaluate whether a named entity has crossed the Named Recurrence
Threshold and is eligible for social graph node promotion — and
handle disambiguation when required.

### Responsibilities

- read `DistinctSessionMentionTracker` for the entity
- evaluate threshold conditions against `SOCIAL_GRAPH_MIN_SESSIONS`
  and `SOCIAL_GRAPH_RECURRENCE_WINDOW_DAYS`
- check whether a same-name entity already exists in the world graph
- if threshold is met and no name collision exists: approve promotion
- if threshold is met and name collision exists: initiate
  disambiguation request before approving promotion
- if explicit introduction is detected: approve promotion immediately
  without waiting for session recurrence
- produce a `NodePromotionDecision` — APPROVE, DISAMBIGUATE, or
  HOLD

### Important Principle

`SocialGraphNodeEvaluator` produces decisions. It does not write
entities. Entity creation goes through the existing world graph
write path via `DurableWriteAuthority`.

---

## 2. SocialEntityProfileBuilder

### Purpose

Produce a structured social profile for each social graph entity —
aggregating relationship structure, conversational frequency signals,
and user-stated behavioral facts into a coherent model Zola can
reason from.

### Responsibilities

- read entity document and relationship edges from
  `FirestoreStructuredMemoryRepository`
- read `KNOWS_ABOUT` edge for `firstMentionedAt` and `mentionCount`
- read `DistinctSessionMentionTracker` for session recurrence signal
- read correction history from `MemoryCorrectionLog`
- read `EpisodicMemoryEntry.linkedEntityIds` for episodic linkage
  frequency (read-only aggregation — no new durable store)
- compute `SocialEntityProfile` containing:
  - relationship structure (who this person is, how they connect)
  - conversational frequency signal (how often they appear, across
    how many sessions)
  - user-stated behavioral facts (marked as PROVISIONAL or ACTIVE
    per lifecycle state)
  - confidence level from `EntityBeliefView.metaKnowingConfidence`
  - correction history summary

### v1 Tone Signal

Longitudinal per-entity tone analysis is deferred to v2. In v1, the
social entity profile carries the session-level tone signal from
`ConversationContext.detectedTone` as context for the current session
only — not a durable longitudinal register. This is explicitly
temporary. The v2 tone path reads from episodic entries with entity
linkage and session-level emotional register fields once those are
available.

### Important Principle

`SocialEntityProfileBuilder` is a read aggregator. It never writes
to any store. It is computed per entity per session and cached in
session scope.

---

## 3. ThirdPartyAssertionGuard

### Purpose

Prevent transient emotional content from hardening into permanent
behavioral attributes on third-party entity profiles.

### The Problem

When the user vents about someone — "Marcus is completely unreliable
today" — the memory write pipeline may extract "unreliable" as a
behavioral assertion and attempt to write it to Marcus's entity
profile. Without a guard, this becomes a permanent attribute. With
subsequent venting, Marcus's profile accumulates a collection of
emotionally-derived trait attributions that do not represent the
user's considered view of him.

### The Solution

All behavioral assertions about third-party entities enter the write
pipeline with a `PROVISIONAL` lifecycle state. They do not promote
to `ACTIVE` automatically. Promotion from PROVISIONAL to ACTIVE
requires one of:

**Active promotion triggers:**
- The user explicitly confirms the assertion ("yes, Marcus is
  generally unreliable")
- The assertion is reinforced across `PROVISIONAL_MIN_SESSIONS`
  distinct sessions without triggering user correction or high
  negative emotional valence (passive promotion rule)

Initial value (named constant):
- `PROVISIONAL_MIN_SESSIONS = 3`

**Passive promotion rule:** If a PROVISIONAL attribute is referenced
across three distinct sessions and the user never corrects it and no
session involving that entity has high negative emotional valence
associated with the attribute, it automatically matures to ACTIVE.
This prevents stable facts from remaining hedged indefinitely.

**Demotion:** If the user explicitly contradicts a PROVISIONAL
attribute ("I was just frustrated — Marcus is actually pretty solid"),
the attribute is retired without promotion.

### Integration Point

`ThirdPartyAssertionGuard` operates at `MemoryWritePipeline
.runSensitivityClassification` — the existing Stage 5 sensitivity
classification step. It does not require a separate pipeline. It
extends the existing classification to distinguish:

- user emotional state (how the user is feeling)
- user-stated assertion about a third party (what someone else does)
- emotionally-derived third-party assertion (behavioral claim made
  in a high-negative-valence turn)

The third category enters with `PROVISIONAL` lifecycle state. The
first and second categories follow existing handling.

### Important Principle

PROVISIONAL is not a quarantine. It is a holding state that gives
stable facts the opportunity to earn their permanence naturally,
while preventing one-off venting from hardening into permanent
characterization.

---

## 4. SocialContextAssembler

### Purpose

Produce the social context block injected into prompt assembly at
session start, so that Zola enters every session with awareness of
the people in the user's world.

### Responsibilities

- read `SocialEntityProfile` for entities relevant to the current
  session context (active entities, recently mentioned entities,
  entities with open loops)
- produce a structured `SocialContextBlock` containing:
  - key relationship summaries for active entities
  - conversational frequency signals for frequently appearing entities
  - PROVISIONAL fact indicators so Zola knows to hedge unconfirmed
    behavioral assertions
  - gap signals for entities Zola knows little about that are
    currently relevant
- deliver the block to `SessionBriefBuilder` for injection into
  the `[SOCIAL]` section
- run at session start; result is valid for the session duration

### Important Principle

`SocialContextAssembler` produces context for Zola's awareness. It
does not produce announcements. The social context block shapes how
Zola speaks about people — it does not instruct her to make
observations about them.

---

## 5. SocialGraphInitiativeSource

### Purpose

Produce initiative candidates when a social graph observation is
relevant enough to surface proactively — when a gap about someone
relevant to an active decision needs to be filled, or when a pattern
about a person has become significant enough to be worth noting.

### Responsibilities

- evaluate gap signals from `SocialEntityProfileBuilder` for
  relevance to current conversation or open loops
- produce `InitiativeItem` candidates for high-relevance gaps
  only — using low-pressure urgency tier (0.2–0.35)
- enqueue via `InitiativeQueue.enqueue` — no other delivery path
- apply cross-session deduplication before enqueuing — do not
  surface the same gap twice in consecutive sessions

### What Social Graph Reasoning Does Not Surface Proactively

- Observations about relationship patterns or dynamics that the
  user did not ask about
- Longitudinal tone signals about people ("you seem tense around
  Marcus lately") — this is v2 scope and requires confirmed
  longitudinal data
- Any PROVISIONAL behavioral assertion — PROVISIONAL facts are
  used internally to shape hedging, not surfaced as observations

### Important Principle

Social graph observations that surface do so in service of the
current moment, not as a report on what Zola has been tracking.

---

## Professional Relationship Predicates

The existing `RelationshipType` enum covers kinship and social
relationships. Social Graph Reasoning v1 requires professional and
organizational relationships to model the people in a shop
environment accurately.

### v1 Additions to RelationshipType

- `EMPLOYEE_OF` — person is employed by an entity or organization
- `WORKS_AT` — person works at a location or organization without
  implying employment (contractor, vendor, frequent presence)

### v1.1 Deferred

- `REPORTS_TO` — management hierarchy; deferred to v1.1
- `COLLEAGUE_OF` — peer relationship; deferred; may be inferred
  from shared `EMPLOYEE_OF` edges per OQ-P19-REL-02

### Integration

New predicates are added to `RelationshipType` and wired through
`FamilyRelationshipMapper` normalization for Live session writes.
`RelationshipWriteGovernor` requires no structural changes — it
accepts arbitrary entity pairs and the new predicates are valid
edge types within the existing schema.

---

## Integration Points

---

### What Social Graph Reasoning Reads

| Source | Class / Method | Data consumed |
|---|---|---|
| World graph entities | `StructuredMemoryCacheService` + `Entity` | Entity attributes and source metadata |
| Relationship edges | `FirestoreStructuredMemoryRepository.loadRelationshipsForEntity` | Typed edges, bidirectional |
| Awareness edges | `KNOWS_ABOUT` via `StructuredMemoryService` | firstMentionedAt, mentionCount |
| Session recurrence | `DistinctSessionMentionTracker` (new) | Distinct session count per entity |
| Episodic linkage | `EpisodicMemoryEntry.linkedEntityIds` | Entity-session frequency signal |
| Correction history | `MemoryCorrectionLog` | Third-party fact corrections |
| Entity belief aggregation | `EntityBeliefView` (Self-Model Awareness) | Unified per-entity confidence view |
| Session boundary | `SessionBoundaryResolver` (Temporal Reasoning) | Recency baseline |
| Recency formatting | `TemporalRecencyFormatter` (Temporal Reasoning) | Natural-language age labels |
| Session tone | `ConversationContext.detectedTone` | Session-level tone signal (v1 only) |

---

### What Social Graph Reasoning Produces for Prompts

| Destination | Class / Method | What is injected |
|---|---|---|
| Session brief | `SessionBriefBuilder.assemble` — new `[SOCIAL]` bracket section | Key entity summaries, frequency signals, PROVISIONAL flags |
| Memory block | `MemoryInjectionBuilder.buildMemoryBlock` | Entity context for active entities |
| Proactive context | `ProactiveMemoryContext` | Gap relevance signals |

---

### What Social Graph Reasoning Writes

| Target | Class / Method | What is written |
|---|---|---|
| Session mention tracker | `DistinctSessionMentionTracker` (new) | Per-entity session increment |
| Entity promotion | `DurableWriteAuthority` via existing world graph path | Entity node on threshold crossing |
| Relationship edges | `RelationshipWriteGovernor.commitRelationship` | New predicates (EMPLOYEE_OF, WORKS_AT) |

---

### What Social Graph Reasoning Enqueues

| Destination | Class / Method | What is enqueued |
|---|---|---|
| Initiative queue | `InitiativeQueue.enqueue` via `SocialGraphInitiativeSource` | High-relevance gap candidates |
| Evaluator gate | `InitiativeQueueEvaluator.evaluate` | Standard cooldown applies |

---

## Known Constraints and Deferred Work

### Longitudinal Tone Analysis (v2)

Per-entity longitudinal tone tracking — noticing that the user tends
to seem frustrated when discussing a particular person across sessions
— is deferred to v2. It requires `EpisodicMemoryEntry` tone metadata
fields that do not currently exist (P29-SGR-AUD-37) and a pattern
recognizer that accumulates tone signals across sessions
(P29-SGR-AUD-38). The v1 social context block carries session-level
tone only and explicitly marks this as temporary.

### BehavioralPattern entityId (Optional Enhancement)

`BehavioralPattern.entityId` does not currently exist — behavioral
patterns are user-scoped only (P29-SGR-AUD-24). Adding `entityId`
to `BehavioralPattern` would allow the pattern recognizer to store
third-party behavioral patterns durably rather than only within
the entity's attribute fields. This is an optional enhancement that
improves v2 tone analysis but is not required for v1.

### Edge Lifecycle State (Optional Enhancement)

`Relationship` edges lack `lifecycleState` and `lastReinforcedAt`
fields (P29-SGR-AUD-17). These would allow relationship confidence
to drift and be reinforced using the same mechanics as entity facts.
This is an additive schema extension that improves relationship
confidence modeling but is not required for v1. The existing
`confidence` and `updatedAt` fields on edges provide a working
signal in the interim.

### REPORTS_TO and COLLEAGUE_OF Predicates (v1.1)

Organizational hierarchy and peer relationships are deferred to
v1.1. The v1 professional predicate set (EMPLOYEE_OF, WORKS_AT)
is sufficient to model the primary shop environment use case.

---

## Authority Boundaries

### Social Graph Reasoning may:

- read from entity documents, relationship edges, episodic memory,
  correction logs, and session boundary data
- evaluate Named Recurrence Threshold conditions
- produce disambiguation requests through the conversation layer
- produce social entity profiles and social context blocks
- write to `DistinctSessionMentionTracker`
- enqueue entity promotion through `DurableWriteAuthority`
- enqueue initiative candidates via `InitiativeQueue`

### Social Graph Reasoning must not:

- write entity attributes directly — all entity writes go through
  `DurableWriteAuthority`
- write relationship edges directly — all edge writes go through
  `RelationshipWriteGovernor`
- produce psychological assessments of third parties
- surface longitudinal tone observations in v1
- deliver speech through any path other than the initiative queue
  or prompt injection
- create entity nodes without passing through `SocialGraphNodeEvaluator`
  and disambiguation resolution

---

## Relationship to Relational Intelligence Layer

Social Graph Reasoning is the third implemented subsystem of the
Relational Intelligence Layer. It depends on:

- **Temporal Reasoning** (subsystem 1) — `SessionBoundaryResolver`
  for session age calculations, `TemporalRecencyFormatter` for
  natural-language recency labels
- **Self-Model Awareness** (subsystem 2) — `EntityBeliefView` for
  unified entity belief aggregation, `MetaKnowingConfidence` for
  entity knowledge depth scoring, the hedging register for
  third-party fact phrasing

It is depended on by:

- **Relational Continuity** (subsystem 4) — reads social graph
  entity profiles as context for the relationship arc
- **Relational Calibration** (subsystem 5) — informs calibration
  indirectly; social graph entity profiles inform `relationshipDepth`
  tracking through Relational Continuity; calibration reads the
  resulting consolidated arc and the unified `EntityBeliefView`,
  not the raw social graph nodes directly

---

## Long-Term End State

Social Graph Reasoning eventually supports:

- natural awareness of the people in the user's life — who they
  are, how they fit, what has been said about them — without the
  user needing to re-explain each session
- honest handling of third-party facts — hedged when unconfirmed,
  firmed up when reinforced, never permanently colored by one moment
  of venting
- organizational context that makes the shop environment feel
  understood — Zola knows Marcus works there, knows his role, and
  can reason about shop dynamics accordingly
- gap awareness that surfaces naturally when Zola's understanding
  of someone relevant is thin and that thinness matters
- longitudinal tone signals in v2 that make Zola genuinely
  perceptive about relationship dynamics over time

The system should ultimately feel:

- socially aware without being intrusive
- accurate about people without being reductive
- appropriately uncertain about things it heard secondhand
- genuinely helpful when someone relevant comes up in a consequential
  context

without becoming:

- a system that profiles people as psychological types
- an assistant that surfaces relationship observations unprompted
- a presence that treats overheard venting as permanent character
  assessment
- a layer that duplicates what the world graph already owns

---

## Final Principle

The people in the user's life matter. Understanding them — carefully,
honestly, and with appropriate humility about the limits of secondhand
knowledge — is what makes Zola genuinely useful when those people
come up in conversation.

Social Graph Reasoning is not about knowing more about people. It is
about understanding them well enough to be genuinely helpful when
they matter.
