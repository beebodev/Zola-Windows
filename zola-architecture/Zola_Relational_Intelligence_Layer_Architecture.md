# Relational Intelligence Layer Architecture

### Master Document for the Zola Relational Intelligence Layer

---

## Vision

The Relational Intelligence Layer gives Zola a genuine model of her
relationships — with the user, with the people in the user's life,
and with herself as an entity that knows things, holds beliefs, and
exists in time.

Traditional assistant systems store facts. They remember that someone
exists, what their name is, what role they play. But they have no
model of what those facts mean over time, no sense of how confident
those facts are, no awareness of the arc of a relationship, and no
capacity to notice when something has changed.

The Relational Intelligence Layer is the architecture that moves Zola
beyond fact storage into relational understanding. It gives her:

- awareness of how much time has passed and what that means
- honest self-knowledge about what she believes and how well she
  believes it
- a dynamic model of the people in the user's life
- a sense of the arc of her relationship with the user
- the ability to calibrate her familiarity to the actual depth of
  the relationship

The system should eventually feel less like:

> "an assistant that knows facts about the people you've mentioned"

and more like:

> "a presence that understands the people in your world — and knows
> its own place among them."

---

## Core Philosophy

### Relational Intelligence Is a Reasoning Lens, Not a Storage Layer

The Relational Intelligence Layer does not own memory. The world
graph, memory hierarchy, entity resolution architecture, and
consolidation loop own memory. The Relational Intelligence Layer
reads from those systems, applies relational reasoning to what it
finds, and produces enriched signals that shape how Zola speaks and
what she surfaces.

Every subsystem in this layer is a lens on existing data — not a
parallel memory store, not a competing truth source, not a shadow
entity model. What the layer produces is meaning derived from what
already exists, not new facts stored alongside the old ones.

### Relationships Are Dynamic, Not Static

A relationship is not a label assigned once and held forever. It is
a pattern that evolves through accumulated interaction. The person
who appears occasionally in passing conversation is different from
the person who appears constantly and with emotional weight. The
belief that was fresh six months ago is different from the same
belief today. The relationship that started three sessions ago is
different from one that has been active for two years.

Every subsystem in this layer treats the passage of time, the
accumulation of evidence, and the evolution of patterns as first-
class inputs — not as metadata to be ignored.

### Earned Understanding, Not Assumed Familiarity

Relational intelligence should emerge from evidence, not from
configuration. Zola should not behave as if she knows someone well
until she actually does. She should not assume familiarity until it
has been established. She should not surface observations about
people or relationships until she has earned the right to do so
through accumulated understanding.

This is not just a product principle. It is an architectural one.
Systems that assume familiarity produce uncanny, presumptuous
behavior that erodes trust. Systems that earn familiarity through
genuine accumulation produce a presence that feels perceptive and
trustworthy.

---

## Non-Goals

The Relational Intelligence Layer is not:

- a memory system — it reads from existing memory, never replaces it
- a social surveillance system — it does not profile people without
  purpose or surface observations gratuitously
- a therapy system — it observes emotional patterns but does not
  diagnose, interpret, or project psychological states
- a second identity system — Zola's foundational identity is owned
  by `ZolaIdentityProfile`; this layer reads from it
- a parallel delivery path — all output goes through existing prompt
  injection or the initiative queue per RIL-D04
- a replacement for the world graph — entities, relationships, and
  facts remain owned by the existing entity architecture

---

## The Five Subsystems

The Relational Intelligence Layer consists of five subsystems. Each
has a dedicated architecture document. Each reads from the shared
infrastructure defined in this master document.

**Subsystem 1 — Temporal Reasoning**
Converts elapsed time into relational meaning. Understands not just
when things happened but what the passage of time since then
signifies. Foundational infrastructure for all other subsystems.
Architecture document: `Zola_Temporal_Reasoning_Architecture.md`

**Subsystem 2 — Self-Model Awareness**
Maintains Zola's introspective view of her own belief model —
what she knows, how confident she is, what she has gotten wrong,
and where her understanding is thin. Produces hedging signals that
shape how Zola speaks about beliefs based on their actual confidence
state.
Architecture document: `Zola_SelfModel_Awareness_Architecture.md`

**Subsystem 3 — Social Graph Reasoning**
Builds and maintains dynamic models of the people in the user's
life. Tracks relationship structure, conversational patterns, and
user-stated behavioral facts. Understands which people matter, how
they appear in conversation, and what the user has said about them.
Architecture document: `Zola_SocialGraph_Reasoning_Architecture.md`

**Subsystem 4 — Relational Continuity**
Maintains the arc of the relationship between Zola and the user —
the shared history, the patterns, the moments that have defined the
relationship, and the trajectory it is on. Makes Zola feel like a
presence with a lived relationship rather than a system that starts
fresh each session.
Architecture document: `Zola_Relational_Continuity_Architecture.md`

**Subsystem 5 — Relational Calibration**
Calibrates the depth of familiarity Zola expresses to the actual
depth of the relationship. Earned familiarity deepens naturally over
time. Early-relationship behavior is appropriately careful and
curious. Later behavior is warmer because the warmth has been earned.
Architecture document: `Zola_Relational_Calibration_Architecture.md`

---

## Dependency Order

The five subsystems are interdependent. The dependency order defines
which must be built before which.

**Temporal Reasoning** is foundational. All four remaining subsystems
depend on it for elapsed-time calculations, session boundary
resolution, and natural-language age formatting. No subsystem
reimplements these — they use the shared components from Temporal
Reasoning.

**Self-Model Awareness** depends on Temporal Reasoning for belief age
calculations. It is depended on by Social Graph Reasoning (confidence
modeling pattern), Relational Continuity (self-understanding within
the relationship arc), and Relational Calibration (confidence signals
for familiarity depth).

**Social Graph Reasoning** depends on Temporal Reasoning for
distinguishing recent from distant interactions, and on Self-Model
Awareness for the confidence modeling pattern on third-party entity
beliefs.

**Relational Continuity** depends on Temporal Reasoning heavily, and
reads from Self-Model Awareness for Zola's understanding of herself
within the relationship. It produces the `RelationshipArc` document
type that Self-Model Awareness references.

**Relational Calibration** is the most downstream subsystem. It reads
from Relational Continuity for relationship depth, from Self-Model
Awareness for confidence signals, and from Temporal Reasoning for
relationship age. It is built last.

---

## Shared Infrastructure

The following components are defined in Subsystem 1 (Temporal
Reasoning) and used as shared infrastructure across all subsystems.
No subsystem reimplements these. No subsystem defines its own
version of any contract defined here.

### SessionBoundaryResolver

Answers the single question: when did the previous session end?

```
SessionBoundaryResolver.resolveLastBoundaryMs(userId: String): Long?
```

Resolution order:
1. `SessionSummary.endedAtMs` — preferred; written by consolidation
2. `ConversationState.updatedAt` — fallback; always present

On cold start where both sources require a blocking network fetch,
returns null immediately. Callers treat null as "elapsed time unknown"
and suppress any output that depends on the inter-session gap.
Resolution never blocks the session initiation pipeline.

### ThreadArcClassifier

Classifies open loop entries by their current temporal arc:
FRESH / ACTIVE / AGING / QUIET / OVERDUE / DORMANT.

All subsystems that need to reason about thread state use this
classifier. No subsystem implements its own elapsed-time threshold
logic for open loop entries.

### TemporalRecencyFormatter

Produces natural-language elapsed-time labels from epoch millisecond
deltas. All natural-language time references across all five
subsystems go through this formatter. No subsystem formats elapsed
time inline.

### Clock Authority

All temporal computations across all five subsystems use
`System.currentTimeMillis()` returning UTC epoch milliseconds.
No Firestore `FieldValue.serverTimestamp()` is used in any memory
lifecycle write path within this layer. This is consistent with the
clock standard confirmed across the existing codebase (P26-TR-AUD-01,
P29-SMA-AUD-23).

---

## Shared Data Contracts

### Belief Confidence

All five subsystems share the same understanding of belief confidence:

- **Source:** `StructuredEntityMetadata.confidence` (document-level
  in v1; per-attribute `currentConfidence` is the long-term target
  per P29-D06)
- **Proxy:** `fieldUpdatedAt` age as a proxy for per-attribute drift
  until per-attribute fields are implemented
- **Authority hierarchy:** USER_STATEMENT > USER_CONFIRMED >
  SYSTEM_INFERRED > PERCEPTION_DERIVED
- **Hedging thresholds:** defined in Self-Model Awareness
  `HedgingSignalProducer`; all subsystems that produce hedged output
  use these thresholds, not locally defined ones

### Correction History

All five subsystems read correction history from `MemoryCorrectionLog`
via `HybridMemoryRepository.logCorrection`. No subsystem implements
its own correction record. The `CONTRADICTED` lifecycle state (P29-D01)
is the durable supersession mechanism once implemented.

### Entity Belief View

`EntityBeliefView` (defined in Self-Model Awareness) is the unified
per-entity belief aggregator. Any subsystem that needs a synthesized
view of what Zola believes about a given entity reads from
`EntityBeliefView` rather than querying entity documents directly.
This prevents redundant aggregation logic across subsystems.

`EntityBeliefView` is computed once per entity at session start and
cached in session scope. When a Live correction commits during a
session, the cache entry for the affected entity is invalidated and
recomputed on next access.

**Dual-endpoint invalidation:** When a correction alters a
bidirectional relationship edge — for example, changing who someone
works for — the invalidation routine must clear the cached
`EntityBeliefView` for both affected entity endpoints simultaneously.
Both the `fromEntityId` and `toEntityId` of the corrected edge must
be invalidated in the same operation. This ensures that graph
traversal from either node produces consistent results for the
remainder of the session. A correction that invalidates only one
endpoint leaves the other serving stale relationship data, which is
worse than serving no data — it produces asymmetric graph state that
will produce different answers depending on which entity is traversed
first.

### Relationship Arc

`RelationshipArc` (defined in Relational Continuity) is the document
type representing the arc of a relationship over time. It is distinct
from graph edges. Self-Model Awareness, Social Graph Reasoning, and
Relational Calibration read from it. Relational Continuity exclusively
owns the write path via `ConsolidationLoop` step 6b. No other subsystem
creates or writes to it.

---

## Authority Boundaries

These boundaries apply to every subsystem in the Relational
Intelligence Layer without exception.

### The Layer May:

- read from any memory store, entity document, relationship edge,
  correction log, or session boundary source
- compute confidence scores, accuracy metrics, arc classifications,
  and gap assessments
- produce context signals for prompt injection
- enqueue initiative candidates via `InitiativeQueue.enqueue`
- invoke shared infrastructure components defined in this document

### The Layer Must Not:

- write to any Firestore collection or memory store except through
  specifically authorized write paths defined per subsystem
- modify beliefs, lifecycle states, correction records, or entity
  attributes without explicit authority
- invoke `ResponseExecutionService`, `GeminiLiveClient`, or any
  speech execution class directly
- deliver speech through any path other than the initiative queue
  or prompt injection
- create a parallel memory store, shadow entity model, or competing
  truth source
- bypass `InitiativeQueueEvaluator` for any candidate

### Delivery Paths

All Relational Intelligence Layer output that reaches the user goes
through one of two paths:

**Prompt injection** — enriching session context so that Zola's
natural responses reflect relational understanding without announcing
it. Integration points: `SessionBriefBuilder` and
`MemoryInjectionBuilder`.

**Initiative queue** — proactive surfacing of relational observations
when timing and relevance warrant it. Integration point:
`InitiativeQueue.enqueue` via subsystem-specific source classes.
All candidates are subject to `InitiativeQueueEvaluator` cooldown
and gating.

No subsystem may produce a third delivery path. New output surfaces
require a design decision entry before they are implemented.

---

## Integration Point Map

| Subsystem | Reads From | Injects Into | Enqueues To |
|---|---|---|---|
| Temporal Reasoning | OpenLoopTracker, SessionSummary, EpisodicMemoryEntry, ConversationState | SessionBriefBuilder [TEMPORAL], MemoryInjectionBuilder | InitiativeQueue via TemporalInitiativeSource |
| Self-Model Awareness | Entity/Relationship/StructuredEntityMetadata, MemoryCorrectionLog, ZolaIdentityProfile | SessionBriefBuilder belief block, MemoryInjectionBuilder hedging signals | InitiativeQueue via SelfModelInitiativeSource |
| Social Graph Reasoning | Entity, Relationship, EpisodicMemoryEntry.linkedEntityIds, KNOWS_ABOUT edges, DistinctSessionMentionTracker | SessionBriefBuilder [SOCIAL] block, MemoryInjectionBuilder | InitiativeQueue via SocialGraphInitiativeSource |
| Relational Continuity | RelationshipArc, SessionSummary, EpisodicMemoryEntry, MemoryCorrectionLog, OpenLoopTracker, ThreadArcClassifier (Temporal Reasoning), EntityBeliefView (SMA), SessionBoundaryResolver (Temporal Reasoning) | SessionBriefBuilder [CONTINUITY] block | InitiativeQueue via ContinuityInitiativeSource |
| Relational Calibration | RelationshipArc, EntityBeliefView, SessionBoundaryResolver, TemporalRecencyFormatter, MemoryCorrectionLog | MemoryInjectionBuilder behavioral constraint block, IdentityContext via ResponseIdentityOrchestrator | InitiativeQueue via CalibrationInitiativeSource |

---

## Privacy Principles

Third-party entity models carry special privacy obligations.
Everything Zola knows about people in the user's life comes through
the user's perspective — it is inherently secondhand, inherently
filtered, and inherently incomplete.

The Relational Intelligence Layer enforces three privacy principles
that apply across all five subsystems:

**Third-party beliefs are held loosely.** All beliefs about third
parties carry a structurally lower confidence ceiling than direct
user facts, derived from source metadata. The hedging register
handles output phrasing — Zola does not announce this distinction
to the user, she reflects it in how she speaks.

**Observations are never headlines.** Social graph observations,
relationship arc patterns, and calibration signals inform responses
as background texture. They do not surface as standalone
announcements. When a relational observation surfaces proactively
it does so because it is directly relevant to something happening
now — not because a threshold was crossed.

**No psychological profiling.** This layer tracks structural facts,
conversational patterns, and user-stated behavioral assertions. It
does not produce psychological diagnoses, character assessments, or
inferred emotional states about third parties. What someone did in
a situation the user described is recordable. What kind of person
they are is not.

---

## Known Constraints Across the Layer

### Retrieval Hygiene Dependency

All five subsystems share the retrieval hygiene dependency
established in P29-D09. Self-Correction Amnesia remediation —
CONTRADICTED lifecycle state persistence, semantic chunk
tombstoning, and retrieval filters — must be in place before any
subsystem build track begins that produces hedged output or reads
correction history.

### Per-Attribute Confidence

Document-level `StructuredEntityMetadata.confidence` is the v1
confidence signal. Per-attribute confidence is the long-term design
target. All subsystems use the proxy calculation defined in
`EntityBeliefView` until per-attribute fields are implemented.

### RTDB Retirement

The legacy RTDB conversation log is a known deferred item. Until it
is retired, the Relational Intelligence Layer reads from Firestore-
backed stores only. No subsystem introduces a new RTDB dependency.

---

## Relationship to Other Architecture Documents

The Relational Intelligence Layer reads from and operates within the
constraints established by:

- **Zola Master Architecture Plan** — single authority ownership,
  truth ownership rule, provider abstraction philosophy
- **Memory Hierarchy Architecture** — memory layer definitions,
  decay and promotion rules, consolidation loop
- **Memory Agency Architecture** — write pipeline authority, belief
  lifecycle states, correction handling
- **Identity and Personality Framework** — foundational identity
  traits that are never subject to confidence modeling
- **Autonomous Behavior Architecture** — initiative queue, proactive
  delivery, attention gating
- **Privacy and Data Ownership Plan** — third-party data obligations,
  consent requirements, retention policies

---

## Long-Term End State

The Relational Intelligence Layer eventually produces a Zola that:

- speaks with natural time awareness without being prompted to
- hedges beliefs honestly based on their actual confidence state
- understands the people in the user's life as dynamic models,
  not static entries
- maintains the arc of her relationship with the user as something
  real and continuous
- expresses familiarity that has been genuinely earned over time

without becoming:

- a system that announces its own relational intelligence
- a presence that profiles people gratuitously
- an assistant that assumes familiarity it has not earned
- a layer that duplicates what the world graph already owns

---

## Final Principle

Relational intelligence is not a feature. It is the quality that
makes the difference between a system that knows facts about people
and a presence that understands them.

Every component in this layer exists to serve that quality — quietly,
through the texture of how Zola speaks and what she notices, rather
than through any announcement that she is doing it.
