# Self-Model Awareness Architecture

### Foundational Architecture for Zola's Introspective Belief Model

---

## Vision

The Self-Model Awareness Architecture defines how Zola maintains an
introspective view of her own belief model — understanding not just
what she knows, but how confident she is, how current her knowledge
is, what she has gotten wrong before, and where her understanding is
genuinely thin.

The goal is not to make Zola perform uncertainty. The goal is to make
her uncertainty real — grounded in the actual state of her belief
model — and to surface it naturally through the language she uses
rather than through explicit declarations.

The system should eventually feel less like:

> "an assistant that states facts with uniform confidence"

and more like:

> "a presence that knows what it knows well, acknowledges what it
> holds loosely, and is honest about where its picture is incomplete."

---

> **Windows Track:** Self-Model Awareness is deferred along with the
> rest of the Relational Intelligence Layer for Zola-Windows (`S2`).
> One decision is locked in advance of that work — see the Authority
> Boundaries section below (`A7`).

## Core Philosophy

### Hedged Language Is the Correction Mechanism

Uncertainty that stays internal never resolves. A belief Zola holds
with quietly declining confidence will drift until it is confidently
wrong. The only way the self-model stays honest over time is if
uncertainty surfaces — and the only way correction happens is if the
user has something to respond to.

Zola does not surface uncertainty through explicit confirmation
requests. She surfaces it through language. "If I remember right,"
"last I knew," "I think this is still the case" — these phrasings are
not stylistic choices. They are computed outputs of the self-model.
When a belief crosses a staleness or confidence threshold, the
self-model produces a hedging signal that shapes how Zola speaks
about that belief. The language is the mechanism.

This approach is lower friction than explicit questioning, more natural
in conversation, and consistent with Zola's character as a presence
rather than a system running confirmations. The phrasing itself is an
implicit invitation to correct her. If the user responds with a
correction, the correction pipeline handles it. If they say nothing,
the belief holds — which is itself a weak reinforcement signal.

### Gaps Surface When Relevant, Not on a Schedule

Zola does not proactively announce what she does not know. She
maintains a model of her own gaps — topics where her information is
sparse, entities she knows only shallowly, domains where her beliefs
have not been reinforced or tested. But that model stays internal
until a gap becomes relevant to something happening right now.

When a gap becomes relevant — when a decision involves someone Zola
knows little about, when a topic she has thin coverage of comes up in
a consequential context — she surfaces it then. "I don't know much
about Marcus, and it sounds like he's involved in this decision." The
gap surfaces in service of the moment, not as a standalone admission.

### Consistent Behavior Across Self, User, and Others

The same hedging language, the same gap-surfacing timing, and the same
confidence mechanics apply regardless of who or what the belief is
about. Beliefs about the user, beliefs about Zola herself, and beliefs
about third parties in the user's life are all subject to the same
model. There is no special treatment for any category. Zola's epistemic
humility is uniform.

### Accuracy Is Computed, Not Stored

Confidence is an internal state on each belief — a current value that
drifts with time and updates with reinforcement or correction. Accuracy
is a historical metric computed from the correction record — a ratio of
how often beliefs in a given domain were reinforced versus corrected
over time. Zola does not store a belief about how accurate she is. She
computes it from evidence when needed.

This distinction matters. Storing accuracy as a field would require its
own write authority, lifecycle, and correction path — recursive
complexity. Computing it from existing data keeps the architecture
clean and ensures the metric always reflects the actual record rather
than a stale stored value.

---

## Non-Goals

Self-Model Awareness is not:

- a memory system — it does not store, promote, or decay beliefs
- a replacement for the Memory Hierarchy Architecture or world graph
- a second identity system — Zola's foundational identity is owned by
  `ZolaIdentityProfile` and the Identity and Personality Framework;
  Self-Model Awareness reads from that foundation, it does not
  redefine it
- a user-facing transparency system — it does not produce a UI surface
  showing the user what Zola believes; it shapes how Zola speaks
- a correction detection system — correction detection belongs to
  `CorrectionHandler` and `LiveMemoryCorrectionToolExecutor`; Self-Model
  Awareness reads the correction record, it does not produce it
- a confidence display — confidence values are internal signals that
  produce hedged language; they are never shown to the user as numbers
- a parallel delivery path — all output from this layer goes through
  existing prompt injection or the initiative queue

---

## Architectural Position

Self-Model Awareness sits between the existing belief model and two
downstream consumers: the prompt assembly layer and the initiative
queue.

It reads from:

- the world graph entity model and per-entity confidence metadata
- the correction log (`MemoryCorrectionLog`) for correction history
- `GovernedTemporalIntervalRecord` for temporal supersession
- `ZolaIdentityProfile` for Zola's own foundational identity
- `Relationship` edges for relationship belief confidence
- `SessionBoundaryResolver` from the Temporal Reasoning layer for
  belief age calculations
- `TemporalRecencyFormatter` for natural-language age labels

It produces:

- **Hedging signals** — per-belief flags that shape prompt phrasing
  when beliefs are stale or low-confidence
- **Gap signals** — per-entity or per-domain signals identifying where
  Zola's knowledge is thin, surfaced when relevant
- **Belief summary blocks** — structured context about what Zola
  believes about a given entity, injected into prompt assembly
- **Initiative candidates** — when a gap or stale belief becomes
  relevant enough to surface proactively, a candidate enters the
  initiative queue

It never:

- writes to any Firestore collection or memory store
- modifies beliefs, correction records, or lifecycle states
- invokes `ResponseExecutionService` or `GeminiLiveClient` directly
- delivers speech — all output goes through prompt injection or the
  initiative queue
- makes correction decisions — it observes the correction record,
  it does not write to it

---

## Dependency on Retrieval Hygiene

Self-Model Awareness cannot function correctly until the Self-Correction
Amnesia risk identified in P29-SMA audit Section 5 is remediated.

Specifically, before any SMA build track begins:

- `CONTRADICTED` lifecycle state must be written on correction commit
  (P29-D01)
- semantic chunk tombstoning must be implemented (P29-D02)
- `CONTRADICTED` exclusion filter must be active on
  `MemoryInjectionBuilder` world graph load
- `superseded` exclusion filter must be active on
  `FirestoreSemanticMemoryStore.search`

If these are not in place, the prompt will simultaneously contain
SMA's carefully hedged uncertainty signals and the old wrong belief
text from stale semantic chunks — producing contradictory context
that the model cannot resolve correctly.

This is a hard architectural dependency. It is not a preference.

---

## Long-Term Architectural Pillars

---

## 1. EntityBeliefView

### Purpose

Provide a unified, per-entity view of everything Zola believes about
a given entity — aggregating facts, relationships, confidence states,
correction history, and gap analysis into a single coherent structure
that Self-Model Awareness components can read from.

### Responsibilities

- aggregate world graph attributes for a given entity from
  `StructuredMemoryCacheService`
- read per-field provenance from `StructuredEntityMetadata.fieldSources`
  and `fieldUpdatedAt`
- read document-level `StructuredEntityMetadata.confidence` as the
  entity-level confidence signal (v1; per-attribute `currentConfidence`
  is the long-term design target per P29-D06)
- synthesize mock per-attribute confidence from `fieldUpdatedAt` age
  as a proxy for drift until per-attribute fields are implemented
- read correction history for the entity from `MemoryCorrectionLog`
- read relationship edges from `Relationship` and
  `FirestoreStructuredMemoryRepository`
- compute `metaKnowingConfidence` — Zola's confidence in her overall
  understanding of this entity (see component 2)
- identify belief gaps — attributes or relationship categories where
  Zola has no data or only low-confidence data
- expose the assembled view as an immutable value object per entity
  per session

### Output Contract

`EntityBeliefView` is computed once per entity at session start or
on first access during a session. It is cached in session scope and
treated as immutable for the session. It is not re-computed mid-session
except when a correction commits during a Live session, at which point
the affected entity's view is invalidated and recomputed on next access.

### Concurrency Directive — Mid-Sentence Invalidation

In the Gemini Live audio pipeline, tool calls execute concurrently on
`Dispatchers.Default` while audio frames flow independently. If a Live
correction invalidates an `EntityBeliefView` cache entry while the
model is actively streaming an audio response that was built from the
prior snapshot, the system must not shift the prompt context
mid-response.

If ongoing response generation is actively streaming audio tokens when
a Live correction invalidates the cache, the current linguistic turn
completes under the initial session snapshot. The recomputed view
enforces its updated thresholds exclusively starting on the subsequent
conversational turn. Mid-response context shifts are never permitted.

This is not a best-effort guideline. A response that begins with one
confidence state and ends with another is worse than a response that
completes with a slightly stale state — the incoherence is more
damaging than the staleness.

### Important Principle

`EntityBeliefView` is a read aggregator. It never writes to any store.
It never modifies lifecycle states. It is a lens on existing data, not
a producer of new data.

---

## 2. MetaKnowingConfidence

### Purpose

Compute a single score representing how well Zola understands a given
entity overall — a meta-belief about the depth and reliability of her
knowledge of that entity, distinct from confidence in any individual
fact.

### Responsibilities

- compute a `Float` score in [0.0, 1.0] representing overall knowledge
  depth for a given entity
- derive the score from three inputs:
  - **Belief breadth** — how many attributes and relationship edges
    are known relative to what would be expected for this entity type
  - **Belief freshness** — the mean age of known beliefs weighted by
    `fieldUpdatedAt`, computed via `SessionBoundaryResolver` and
    `TemporalRecencyFormatter`
  - **Correction rate** — the ratio of correction events to
    reinforcement events for this entity over the correction log
    history; a high correction rate reduces the score
- apply consistent scoring logic regardless of whether the entity is
  the primary user, a third party, or any other entity type
- expose the score via `EntityBeliefView.metaKnowingConfidence`

### Score Interpretation

| Range | Meaning |
|---|---|
| 0.80 – 1.00 | Well known — broad, fresh, rarely corrected |
| 0.60 – 0.79 | Moderately known — some gaps or aging beliefs |
| 0.40 – 0.59 | Shallowly known — sparse data or frequent corrections |
| 0.00 – 0.39 | Poorly known — very little reliable information |

### Important Principle

`MetaKnowingConfidence` is a computed score, not a stored field. It
is computed at session start, cached in session context, and discarded
at session end. It is never written to Firestore. Future refinements
to the scoring formula do not require schema migrations.

---

## 3. HedgingSignalProducer

### Purpose

Evaluate each belief Zola is about to reference and produce a hedging
signal that shapes how she phrases it — so that the language she uses
naturally reflects the actual confidence state of the belief.

### Responsibilities

- evaluate belief confidence from `EntityBeliefView` against defined
  thresholds
- evaluate belief age from `fieldUpdatedAt` and `SessionBoundaryResolver`
- produce a `HedgingLevel` classification for each belief:
  - `NONE` — belief is current and high-confidence; state it directly
  - `SOFT` — belief is moderately aged or moderate-confidence;
    use light hedging ("last I knew," "if I remember right")
  - `STRONG` — belief is significantly aged or low-confidence;
    use explicit uncertainty ("I'm not sure if this is still the case,"
    "this may have changed")
  - `GAP` — no belief exists or confidence is below minimum threshold;
    surface as a gap rather than a hedged fact
- expose hedging classifications as part of the belief context block
  injected into prompt assembly

### Hedging Language Register

Hedging language is always natural and conversational. It is never
formal, apologetic, or system-like. The following register is the
canonical reference:

**SOFT hedging examples:**
- "if I remember right"
- "last I knew"
- "I think this is still the case"
- "as far as I know"

**STRONG hedging examples:**
- "I'm not sure if this is still the case"
- "this may have changed"
- "last I heard, though I'm not certain"
- "my information on this might be out of date"

These are not exhaustive — Zola should vary phrasing naturally. They
define the register, not a fixed vocabulary.

### Thresholds

Initial hedging thresholds (subject to calibration):

| Condition | HedgingLevel |
|---|---|
| confidence ≥ 0.75 AND age < 30 days | NONE |
| confidence ≥ 0.60 OR age < 90 days | SOFT |
| confidence < 0.60 AND age ≥ 30 days | STRONG |
| confidence < 0.40 OR no belief exists | GAP |

### Absence Scaling — Preventing Systemic Self-Doubt

Age-based thresholds applied naively after a prolonged user absence
will produce a degenerate state where every belief simultaneously
crosses the staleness threshold. A user returning after 45 days would
hear Zola hedge every single statement — sounding disoriented rather
than stable.

To prevent this, age-based decay curves are adjusted at session
initialization when the inter-session gap exceeds 14 days:

- Read the inter-session gap from `SessionBoundaryResolver`
- If the gap exceeds 14 days, identify all beliefs where
  `reinforcementCount > 5` — these are well-established, repeatedly
  confirmed beliefs that have earned stability
- For this subset, temporarily flatten the age-based decay curve
  during session initialization: treat their effective age as
  capped at 30 days regardless of actual elapsed time
- Standard decay resumes from the next session after re-engagement

This scaling applies to age-based thresholds only. Confidence-based
thresholds are not affected — a belief with genuinely low confidence
is still hedged regardless of absence duration.

The 14-day gap threshold and `reinforcementCount > 5` floor are
initial values subject to calibration against real session patterns.

### Important Principle

Hedging signals are computed from the actual state of the belief model.
They are not style instructions. A prompt that says "be uncertain
sometimes" is not the same as a system that computes uncertainty from
evidence and reflects it in language. This layer produces the latter.

---

## 4. GapSignalProducer

### Purpose

Identify where Zola's knowledge of an entity or domain is genuinely
thin and surface that gap when it becomes relevant to something the
user is doing — not as a standalone admission, but as useful context
in the moment.

### Responsibilities

- read `EntityBeliefView.beliefGaps` for entities relevant to the
  current conversation
- evaluate whether a gap is relevant to the current context — a gap
  about someone uninvolved in the current topic does not surface
- produce a `GapSignal` when a gap is relevant, containing:
  - the entity the gap is about
  - the category of the gap (relationship, behavioral, factual,
    temporal)
  - a natural-language description suitable for prompt injection
- deliver relevant gap signals to the temporal context block in
  `SessionBriefBuilder` for passive awareness
- deliver high-relevance gap signals as initiative candidates to
  `InitiativeQueue` when the gap is directly relevant to an active
  decision or task

### Gap Relevance Evaluation

A gap is considered relevant when:

- the entity the gap is about is actively mentioned in the current
  conversation or open loop
- the gap category directly affects a decision or task currently
  in progress
- the `MetaKnowingConfidence` for the entity is below 0.40 and the
  entity appears in a high-stakes context

A gap is not surfaced when:

- the entity is not relevant to anything currently active
- the gap has been surfaced in the same session already
- the gap is about a domain where Zola intentionally does not collect
  information (privacy-protected categories)

### Important Principle

Gaps surface in service of the moment, not as a confession schedule.
Zola does not announce all her gaps at session start. She notices
when a gap matters and surfaces it then.

---

## 5. SelfBeliefBlock

### Purpose

Maintain Zola's introspective view of herself — her own values, her
own patterns of behavior, and her understanding of how she has changed
— as a structured input to prompt assembly.

### Responsibilities

- read `ZolaIdentityProfile` for foundational identity traits —
  these are treated as permanently high-confidence and never hedged
- read style profile and growth ring data for evolved behavioral
  patterns — these are subject to confidence modeling and may be
  hedged if the pattern is weakly established
- identify any known inconsistencies in Zola's own behavior — patterns
  the correction record or behavioral signal suggests have drifted
- produce a `SelfBeliefBlock` value object containing:
  - foundational identity summary (high-confidence, no hedging)
  - current behavioral patterns with confidence levels
  - any flagged drift or inconsistency worth noting

### Relationship to Identity Framework

The Identity and Personality Framework owns Zola's foundational
identity. `SelfBeliefBlock` reads from it — it does not define,
modify, or override it. Locked identity traits are never subject to
confidence modeling. Adaptive traits and style profile entries are.

### Important Principle

Zola's foundational identity does not drift. Her behavioral patterns
can evolve. The `SelfBeliefBlock` knows the difference and treats them
accordingly.

---

## Integration Points

---

### What Self-Model Awareness Reads

| Source | Class / Method | Data consumed |
|---|---|---|
| World graph entities | `StructuredMemoryCacheService` + `Entity` | Attributes, confidence metadata |
| Per-field provenance | `StructuredEntityMetadata.fieldSources`, `fieldUpdatedAt` | Field-level age and source |
| Correction history | `MemoryCorrectionLog`, `HybridMemoryRepository.logCorrection` | oldValue, newValue, timestamp |
| Temporal supersession | `GovernedTemporalIntervalRecord` | Superseded belief periods |
| Relationship edges | `Relationship`, `FirestoreStructuredMemoryRepository` | Typed edges with confidence |
| Identity model | `ZolaIdentityProfile.toSystemPromptBlock` | Foundational traits |
| Session boundary | `SessionBoundaryResolver` (Temporal Reasoning layer) | Belief age baseline |
| Recency formatting | `TemporalRecencyFormatter` (Temporal Reasoning layer) | Natural-language age labels |
| Entity graph context | `MemoryGraphService.summarizeForEntity`, `RelationshipResolver` | Entity relationship summary |

---

### What Self-Model Awareness Produces for Prompts

| Destination | Class / Method | What is injected |
|---|---|---|
| Session brief | `SessionBriefBuilder.assemble` — belief confidence summary block | Entity confidence states, known gaps |
| Memory block | `MemoryInjectionBuilder.buildMemoryBlock` — hedging signals | Per-belief hedging level for fact phrasing |
| Proactive context | `ProactiveMemoryContext.buildTimeContext` | Gap relevance signals for proactive enrichment |

---

### What Self-Model Awareness Enqueues

| Destination | Class / Method | What is enqueued |
|---|---|---|
| Initiative queue | `InitiativeQueue.enqueue` via `SelfModelInitiativeSource` | High-relevance gap candidates |
| Evaluator gate | `InitiativeQueueEvaluator.evaluate` | Standard cooldown applies |

### Live Correction Write Path — Optimistic Dispatch Requirement

Phase 8b audit (P29-SMA-AUD-47) confirmed that the Live correction
write path suspend-blocks the tool batch for up to 3 seconds waiting
for Firestore commit before returning the tool response to Gemini.
During an active Live audio session this stalls model generation
mid-conversation on every correction.

The build track implementing `LiveMemoryCorrectionToolExecutor`
corrections must patch the write path to execute an optimistic return
to the Live API tool handler immediately upon handoff to
`DurableWriteAuthority`, allowing conversational generation to proceed
while the Firestore I/O flushes asynchronously. This matches the
optimistic background dispatch pattern already used by memory write
tools in `LiveToolExecutionManager`.

This directive is recorded here because Self-Model Awareness depends
on correction writes completing correctly and promptly. A stalled
correction write degrades both the correction record and the hedging
signal quality for the affected entity in the current session.

The design decision locking this behavior is P29-D05.

---

## Known Constraints and Deferred Work

### Per-Attribute Confidence (v1 Limitation)

`StructuredEntityMetadata.confidence` is document-level. Per-attribute
`currentConfidence` as defined in `Zola_Architecture_Perception_Memory.md`
Layer 4 does not exist on the current data model. The v1 implementation
uses `fieldUpdatedAt` age as a proxy for per-attribute drift. This is
explicitly temporary. When per-attribute `currentConfidence` is added,
`EntityBeliefView` switches to reading it directly. The proxy must not
be treated as a permanent solution.

### CONTRADICTED Schema Design

P29-D01 requires `CONTRADICTED` lifecycle state on correction commit.
The schema for per-attribute vs per-document CONTRADICTED persistence
is an open question (OQ-P29-SMA-CONTRADICTED-02). The correction
history read path in `EntityBeliefView` is designed to work with either
schema — it reads from `MemoryCorrectionLog` in v1 until the CONTRADICTED
document schema is defined and implemented.

### Relationship Arc

The `RelationshipArc` document type defined in P29-D07 does not exist
yet. Self-Model Awareness references it in `SelfBeliefBlock` for Zola's
understanding of her relationship with the primary user. Until
`RelationshipArc` is implemented (Relational Continuity subsystem),
this section of `SelfBeliefBlock` reads from available `PRIMARY_BOND`
edge metadata only.

### No User-Facing Confidence Display

Confidence values computed by this layer are never exposed to the user
as numbers, scores, or visual indicators. They are internal signals
that shape language. Any future transparency surface for memory
confidence is a separate product decision outside the scope of this
architecture.

---

## Authority Boundaries

> **Windows Track (`A7`):** The strict read-only boundary specified
> below is not enforced any harder for Zola-Windows than Hermes's own
> general write-authority model elsewhere in the agent — i.e. no
> Windows-specific hardening added on top of whatever this document
> specifies. Locked in advance since Self-Model Awareness itself is
> deferred (`S2`); applies whenever this subsystem is actually built.

### Self-Model Awareness may:

- read from any memory store, correction log, identity profile, or
  relationship edge
- compute confidence scores, accuracy metrics, and gap assessments
- produce hedging signals, gap signals, and belief summary blocks
- enqueue initiative candidates via the standard intake contract
- invoke `TemporalRecencyFormatter` and `SessionBoundaryResolver`
  from the Temporal Reasoning layer

### Self-Model Awareness must not:

- write to any Firestore collection or memory store
- modify beliefs, lifecycle states, or correction records
- invoke `ResponseExecutionService`, `GeminiLiveClient`, or any
  speech execution class directly
- deliver speech — all output goes through prompt injection or the
  initiative queue
- redefine or override Zola's foundational identity — that belongs
  to `ZolaIdentityProfile` and the Identity and Personality Framework
- make correction decisions — it observes corrections, it does not
  produce them

### Important Principle

Self-Model Awareness gives Zola self-knowledge. It does not give her
self-modification. The system that knows what it believes is different
from the system that changes what it believes. Those responsibilities
belong to different layers and must remain separate.

---

## Relationship to Relational Intelligence Layer

Self-Model Awareness is the second implemented subsystem of the
Relational Intelligence Layer. It depends on:

- **Temporal Reasoning** (subsystem 1) — for `SessionBoundaryResolver`,
  `TemporalRecencyFormatter`, and belief age calculations; these are
  shared infrastructure and are not reimplemented here

It is depended on by:

- **Social Graph Reasoning** (subsystem 3) — borrows the confidence
  modeling pattern from `EntityBeliefView` for third-party entity
  beliefs; the `MetaKnowingConfidence` concept applies directly to
  social graph entities
- **Relational Continuity** (subsystem 4) — reads `SelfBeliefBlock`
  for Zola's understanding of herself within the relationship arc
- **Relational Calibration** (subsystem 5) — uses confidence and gap
  signals to determine what depth of familiarity the relationship
  currently warrants

---

## Long-Term End State

Self-Model Awareness eventually supports:

- natural hedging language throughout all of Zola's responses,
  calibrated to the actual confidence state of each belief she
  references
- gap surfacing that feels like perceptive awareness rather than
  system admission — Zola notices what she doesn't know when it
  matters
- a correction record that feeds back into behavior — domains where
  Zola has been corrected frequently get more hedging; domains where
  she has been consistently right earn more confidence
- a self-model that covers Zola's own identity, her relationship with
  the user, third parties in the user's life, and her own behavioral
  patterns — all under the same confidence mechanics
- a presence that knows itself — not as an exercise in artificial
  humility, but because honest self-knowledge is what makes Zola
  trustworthy over time

The system should ultimately feel:

- honest without being apologetic
- confident where confidence is earned
- uncertain where uncertainty is real
- aware of its gaps without being paralyzed by them
- consistent in its epistemic humility across all subjects

without becoming:

- a system that hedges everything to avoid being wrong
- an assistant that constantly asks for confirmation
- a presence that announces its limitations unprompted
- a tool that treats its own uncertainty as the user's problem

---

## Final Principle

Zola's self-model is not a humility performance. It is an honest
account of what she knows, how well she knows it, and where she
does not know enough.

The language that emerges from it — "if I remember right," "last I
knew," "I don't know much about this person" — is not a disclaimer.
It is Zola being real.
