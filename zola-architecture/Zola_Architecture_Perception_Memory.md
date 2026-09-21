# Perception Memory Architecture

### Three-Layer Model for Observation, Pattern, and World Graph Promotion

---

## Vision

Perception produces a continuous stream of observations. Most of them
should vanish. A few should become patterns. Fewer still should become
facts that Zola carries permanently as part of her world model.

Without a discipline governing this pipeline, perception observations
slowly pollute long-term truth. Zola saw Brian look stressed on a
Tuesday afternoon and now her world model says Brian is a stressed
person. She saw an unknown truck three times in one week and now her
world graph contains a confidently-asserted vehicle entity that was
never confirmed. She classified the shop as noisy during a busy period
and that classification persists months later when the shop has changed.

The failure mode is not dramatic. It is gradual. Individual facts
look reasonable when they are written. The problem emerges when they
accumulate — when the world model becomes a sediment layer of stale
observations that were never intended to be permanent.

This document defines the architecture that prevents that failure.

Three layers stand between a perception observation and a durable
world fact. Each layer has its own storage, its own lifetime rules,
its own promotion criteria. A fact must earn its way through all
three before it becomes part of what Zola believes about the world.

The system should eventually feel less like:

> "an assistant whose memory slowly fills with outdated impressions"

and more like:

> "a presence whose world model is trustworthy because it was earned,
> not accumulated."

---

## Core Philosophy

### Observations Are Not Facts

An observation is what the perceptual layer detected at a moment in
time. It carries a confidence score. It has a timestamp. It describes
a specific instance.

A fact is what Zola believes to be durably true about an entity or
pattern in her world. It has survived recurrence, consistency checks,
and promotion rules. It may have been confirmed by the user. It
belongs in the world graph.

The mistake of treating observations as facts directly is the same
mistake as a mechanic writing a first-impression diagnosis in the
permanent service record. The observation belongs in the work log.
The permanent record gets the finding after it has been confirmed.

### Decay Is a Feature, Not a Bug

Most observations should decay without trace. The ephemeral layer
is not a failure state — it is the correct destination for most of
what perception produces. The fact that something was observed and
then forgotten is not a loss. It is the system working correctly.

Decay clears space for the observations that matter. A fact that
recurs earns persistence. A fact that doesn't recur didn't deserve
it.

### Promotion Must Be Earned

The path from observation to world graph is not a threshold to cross —
it is a discipline to satisfy. Recurrence alone is not enough.
Recurrence across sessions, across contexts, with sufficient
confidence, and without contradiction — that is the standard.

For entity candidates, user confirmation is the final gate. Zola
does not unilaterally promote an unknown entity into her world model.
She surfaces the candidate, asks naturally, and waits for the user
to ground it or dismiss it.

### The Memory System Is the Authority for Promotion

The perceptual layer produces observations and patterns. It flags
promotion-eligible episodic entries. It does not promote anything.

The memory system owns the world graph. It reads the `promotionEligible`
flag, applies its own promotion rules, handles user confirmation, and
decides what enters the world graph and in what form. These are two
different systems with a clean handoff interface between them. Neither
crosses into the other's responsibility.

---

## The Three Layers

---

## Layer 1 — Ephemeral State Memory

### Owner

Perceptual Input Layer.

### Purpose

Hold the current moment. Feed real-time systems. Decay completely.

### What It Is

The ephemeral layer is the perceptual layer's working memory. It is
an in-memory buffer — not a database, not a Firestore collection, not
a file. It exists only while the session is running. It does not
survive app restarts. It does not persist between sessions.

Every observation produced by Active Perception enters the ephemeral
layer first. From there, it feeds the Environmental Event Bus and
informs the Current User State Model in real time. Nothing in the
ephemeral layer is written to durable storage unless it subsequently
meets the promotion criteria for Layer 2.

### What It Holds

Individual typed observations from Active Perception. Each entry
in the ephemeral buffer carries:

- `observationType` — the typed observation category
- `subject` — who or what was observed
- `confidence` — float 0.0–1.0
- `observedAt` — timestamp
- `payload` — type-specific data
- `expiresAt` — computed decay deadline
- `sessionId` — which session produced this observation
- `recurrenceKey` — computed key used to match observations of the
  same type and subject for Layer 2 promotion tracking

### Decay Schedule

Observations decay on a per-type schedule. Expired observations are
removed from the buffer without trace. No record of their existence
is kept unless they were already promoted to Layer 2.

| Observation Type | Decay Window |
|------------------|-------------|
| `EXPRESSION_READING` | 10 minutes |
| `VOICE_TONE` | 10 minutes |
| `USER_CONFIRMED` | Session boundary |
| `THIRD_PARTY_PRESENT` | 5 minutes after last observation |
| `ENVIRONMENT_CLASSIFIED` | 30 minutes |
| `ACTIVITY_INFERRED` | 15 minutes |
| `NOISE_LEVEL` | 20 minutes |
| `SIGNIFICANT_AUDIO_EVENT` | 5 minutes |
| `OBJECT_DETECTED` | 10 minutes |

These decay windows are initial values. They should be validated
against real-world usage patterns after Phase 3 implementation.

### What the Ephemeral Layer Does Not Do

- Does not write to Firestore
- Does not survive session boundaries
- Does not feed the world graph directly
- Does not make promotion decisions
- Does not accumulate indefinitely

---

## Layer 2 — Environmental Episodic Memory

### Owner

Perceptual Input Layer (write). Memory System (read and promotion).

### Purpose

Capture patterns. Surface entity candidates. Flag what is ready
for world graph consideration.

### What It Is

The episodic layer is where recurring observations graduate to.
It uses the existing episodic memory infrastructure —
`EpisodicMemoryEntry` at `users/{userId}/episodic/` — with
perception-specific fields and tagging. Perception-sourced
episodic entries are distinguished from conversation-sourced
entries by `source: PERCEPTION` in their metadata.

This layer persists across sessions. It survives app restarts.
It accumulates over time. It is also subject to decay — but on a
much longer schedule than the ephemeral layer.

### Promotion from Layer 1 to Layer 2

An observation is eligible for promotion from the ephemeral buffer
to episodic memory when it meets all of the following criteria:

**Recurrence threshold:**
The same `recurrenceKey` (observation type + subject) has been
observed N times. Initial thresholds by observation category:

| Category | Recurrence Threshold |
|----------|---------------------|
| Environmental (environment, noise) | 5 distinct sessions |
| Behavioral (expression, voice tone) | 8 distinct sessions |
| Entity candidate (unknown person, vehicle) | 3 distinct sessions |
| Activity pattern | 6 distinct sessions |

These thresholds are initial values subject to calibration.

**Session distribution:**
Recurrences must be distributed across at least 3 separate sessions.
A single session in which the same observation fires 10 times does
not qualify. The pattern must appear across time, not within a
single moment.

**Confidence floor:**
Each recurrence used toward the threshold must carry confidence
≥ 0.75. Low-confidence observations do not count toward promotion.
The episodic entry records the mean and minimum confidence across
qualifying recurrences.

**No contradiction:**
If a contradicting observation of the same type and subject has
been recorded within the same window, the recurrence counter resets.
Example: "shop classified as SHOP environment" and "shop classified
as OFFICE environment" on the same subject within the same week
produces no episodic entry — the observations are inconsistent.

### Episodic Entry Structure for Perception

Perception-sourced episodic entries use `EpisodicMemoryEntry` with
the following specific fields:

```
kind: PERCEPTION_PATTERN
intentType: [observation category — e.g. "environment_pattern",
             "behavioral_pattern", "entity_candidate"]
summary: plain-language description of the pattern
importanceScore: derived from confidence mean and recurrence count
source: PERCEPTION  (in metadata)
recurrenceCount: int  (in metadata)
sessionCount: int  (in metadata)
confidenceMean: float  (in metadata)
confidenceMin: float  (in metadata)
firstObservedAt: long  (in metadata)
lastObservedAt: long  (in metadata)
promotionEligible: boolean  (in metadata)
entityCandidateType: string?  (in metadata, if entity candidate)
entityCandidateAttributes: map?  (in metadata, if entity candidate)
```

### Entity Candidates

An entity candidate is a special case of episodic entry — a pattern
that describes something that has been observed repeatedly but has
no confirmed identity in the world graph.

Examples:
- Unknown vehicle (silver truck) seen at consistent times
- Unknown person observed near the shop on multiple occasions
- Recurring sound pattern suggesting a specific piece of equipment

Entity candidates are promoted to episodic memory using the same
recurrence rules above, with a lower recurrence threshold (3 sessions)
because their significance — something is consistently present that
has no name — warrants earlier attention.

An entity candidate episodic entry carries observed attributes
as `entityCandidateAttributes`:

```
entityCandidateType: VEHICLE
entityCandidateAttributes:
  color: silver
  approximate_size: truck
  observed_times: [Monday evening, Tuesday evening]
  observation_count: 5
```

The entity candidate is not created in the world graph until the
user confirms it. The episodic entry holds the candidate state
until that confirmation occurs or the candidate decays.

### Episodic Decay

Perception-sourced episodic entries decay if the underlying pattern
breaks — if contradicting observations accumulate after the entry
was written, or if the pattern simply stops appearing.

**Passive decay:**
Episodic entries carry a `lastObservedAt` timestamp. If no
confirming observation has occurred within a configurable staleness
window, the entry's `importanceScore` decreases on a schedule.
Entries whose importance score drops below a floor are marked stale
and excluded from promotion consideration.

Initial staleness windows by category:

| Category | Staleness Window |
|----------|-----------------|
| Environmental pattern | 30 days without confirming observation |
| Behavioral pattern | 60 days without confirming observation |
| Entity candidate | 14 days without confirming observation |

**Active contradiction:**
If a strong contradicting observation fires after an episodic entry
exists, the entry's `promotionEligible` flag is cleared and its
importance score is penalized. The entry is not deleted — it becomes
a record that the pattern was once present but is no longer reliable.

### The Promotion-Eligible Flag

When an episodic entry has met all promotion criteria and has not
been contradicted or staled out, it is marked `promotionEligible: true`.

This flag is the handoff to the memory system. The perceptual layer's
responsibility ends here. The memory system reads this flag and
decides what to do with it.

---

## Layer 3 — World Graph Promotion

### Owner

Memory System exclusively.

### Purpose

Evaluate promotion candidates. Confirm entity candidates with the
user. Write durable facts to the world graph as entity-native truth.

### What It Is

The world graph is the entity-native memory model defined in the
Entity-Native Memory Principle. Facts here are durable. They survive
indefinitely unless explicitly corrected. They are the highest-weight
signals in Zola's world model.

Perception-derived facts occupy a specific authority tier within
the world graph — below user-stated facts, above pure inference.

### Promotion Rules

The memory system evaluates `promotionEligible` episodic entries
on a scheduled basis (not in real time). For each eligible entry:

**Step 1 — Duplication check**
Does a fact covering the same subject and observation type already
exist in the world graph? If yes, the promotion is evaluated as a
potential update rather than a new fact. If the new pattern is more
recent and consistent, it supersedes. If the existing fact was
user-stated, it is not superseded by perception-derived promotion.

**Step 2 — Authority check**
Is this the kind of fact that perception is allowed to assert
permanently? Behavioral patterns, environmental patterns, and
confirmed entity attributes are eligible. Emotional state assertions
about the user are not eligible for world graph promotion — they
decay at Layer 2 only. No world graph fact should assert that the
user is a particular type of person based solely on perception.

**Step 3 — Entity candidate confirmation**
If the episodic entry is an entity candidate, promotion requires
user confirmation before any world graph write occurs. The memory
system surfaces the candidate to the user through Zola naturally:

> "I've noticed a silver truck parked nearby on Monday and Tuesday
> evenings a few times this week — is that someone you know?"

The user may:
- Confirm and name the entity → promotion proceeds, entity created
- Dismiss → episodic entry marked dismissed, no promotion
- Defer → episodic entry remains eligible, surfaced again after a
  configurable interval

For non-entity-candidate patterns (environmental, behavioral), user
confirmation is not required for promotion. These are facts about
patterns Zola observes, not claims about named entities.

**Step 4 — Write**
Promoted facts are written to the world graph as entity-native
attributes or relationship edges, per the Entity-Native Memory
Principle. They carry:

- `source: PERCEPTION`
- `authority: PERCEPTION_DERIVED`
- `promotedFrom: episodic/{entryId}`
- `promotedAt: timestamp`
- `originalConfidenceMean: float`

These metadata fields allow future correction passes to identify
perception-derived facts and apply appropriate weight in retrieval.
They also seed the World Fact Lifecycle system — `promotedAt` and
`originalConfidenceMean` are the starting point for confidence
aging. See Layer 4 below.

### Authority Hierarchy in Retrieval

When two facts about the same subject conflict in the world graph,
authority hierarchy determines which is used:

| Source | Authority Tier |
|--------|---------------|
| User-stated (direct assertion) | 1 — highest |
| User-confirmed (entity candidate confirmed by user) | 2 |
| System-inferred (relationship graph inference) | 3 |
| Perception-derived (promoted from episodic) | 4 |
| Perception-candidate (not yet confirmed) | Not in world graph |

A perception-derived fact that conflicts with a user-stated fact
does not override it. It is flagged for review — logged as a
discrepancy — and the user-stated fact remains authoritative until
the user explicitly updates it.

### What Perception Cannot Promote to the World Graph

These fact types are permanently ineligible for world graph promotion
regardless of recurrence, confidence, or pattern stability:

- Emotional state assertions about the user as a person type
  ("Brian is a stressed person")
- Third-party identity claims (Zola cannot assert who an
  unconfirmed person is)
- Inferences that combine perception with hearsay without user
  confirmation
- Any fact whose world graph form would assert something the user
  has not confirmed about themselves or others

---

## Layer 4 — World Fact Lifecycle

### Owner

Memory System exclusively.

### Purpose

Ensure that promoted world facts do not remain equally trusted
forever. Facts that are not reinforced should weaken over time.
Facts that are re-confirmed should strengthen. The world model
should feel alive, not fossilized.

### The Problem This Solves

Promotion gets a fact into the world graph. It does not guarantee
the fact remains accurate indefinitely. The world changes. Routines
shift. Relationships evolve. A fact that was true eighteen months
ago and has never been contradicted but has also never been seen
again occupies a false position of certainty in the world model.

Without a lifecycle, the world graph accumulates stale certainty.
Zola references "Brian usually works nights" with full confidence
eight months after that pattern ended, because nothing ever told
her otherwise.

The World Fact Lifecycle prevents this without deleting facts. A
weakened fact is still retrievable. Its history is preserved. If
the pattern returns, confidence recovers. Deletion is irreversible
and loses that history. Drift is graduated and reversible.

### Three Mechanisms

**Certainty Drift**

Every promoted world fact carries a `currentConfidence` field
initialized to `originalConfidenceMean` at promotion time. On a
scheduled drift pass, facts that have not been reinforced within
their drift window have their `currentConfidence` reduced by a
small per-period decrement.

Drift is not contradiction. It is the passive passage of time
without confirmation. A drifted fact is not wrong — it is
uncertain. The world model reflects that uncertainty honestly.

Drift floors by authority tier:

| Authority Tier | Drift Floor | Notes |
|---------------|-------------|-------|
| User-stated | 0.70 | Drifts slowly; floor is high |
| User-confirmed entity | 0.65 | Moderate drift |
| Perception-derived | 0.40 | Drifts faster; lower floor |

A fact whose `currentConfidence` reaches its floor does not drift
further and is not deleted. It is marked `driftFloorReached: true`
and surfaced to the user on the next appropriate occasion for
confirmation or dismissal.

**Confidence Aging**

A fact's age — the time elapsed since `promotedAt` — is used as
a retrieval multiplier independent of `currentConfidence`. Two
facts with identical `currentConfidence` scores are not equal if
one is three weeks old and the other is fourteen months old.

The age multiplier is applied at retrieval time only. It is not
stored as a field — it is computed from `promotedAt` and the
current timestamp. This keeps the stored record clean while
ensuring retrieval reflects temporal reality.

Age multiplier schedule (illustrative — subject to calibration):

| Age Since Last Reinforcement | Multiplier |
|-----------------------------|------------|
| 0–30 days | 1.00 |
| 31–90 days | 0.90 |
| 91–180 days | 0.80 |
| 181–365 days | 0.65 |
| 365+ days | 0.50 |

The multiplier applies to `currentConfidence` at retrieval time.
A fact at 0.85 `currentConfidence` that is 200 days old competes
as 0.85 × 0.80 = 0.68 in retrieval ranking against a fresh fact
at 0.70 `currentConfidence` which competes as 0.70 × 1.00 = 0.70.
The fresher fact wins despite the lower base score.

**Fact Freshness Weighting**

At retrieval time, all three signals are combined into a single
retrieval weight:

```
retrievalWeight = currentConfidence × ageMultiplier × authorityMultiplier
```

Authority multipliers:

| Authority Tier | Multiplier |
|---------------|------------|
| User-stated | 1.20 |
| User-confirmed entity | 1.10 |
| System-inferred | 1.00 |
| Perception-derived | 0.90 |

This formula means a well-reinforced, recently-confirmed,
user-stated fact always outcompetes a stale, perception-derived
fact in retrieval — even if the perception-derived fact has a
higher raw `currentConfidence`. The formula encodes the
authority hierarchy dynamically at retrieval time rather than
as a static ordering.

### Reinforcement

Any of the following events reinforce a fact and reset its drift
clock:

- User explicitly states the same fact again
- Perception re-observes the same pattern with confidence ≥ 0.75
- User confirms the fact in response to a Zola question
- A conversation references the fact and the user does not
  correct it (implicit confirmation — lower reinforcement weight)

On reinforcement, `currentConfidence` increases toward the
original `originalConfidenceMean` or the new observation's
confidence, whichever is higher — up to the authority tier's
ceiling. `lastReinforcedAt` is updated. The age multiplier
resets from `lastReinforcedAt`, not `promotedAt`.

### World Fact Lifecycle Fields

All promoted world graph facts carry these lifecycle fields:

```
promotedAt: long            — when the fact entered the world graph
promotedFrom: string        — episodic entry ID that was promoted
originalConfidenceMean: float — confidence at time of promotion
currentConfidence: float    — current drifted confidence
lastReinforcedAt: long      — last time this fact was confirmed
reinforcementCount: int     — total reinforcement events
driftFloorReached: boolean  — whether drift floor has been hit
source: string              — PERCEPTION / USER_STATED / INFERRED
authority: string           — authority tier
```

### Drift Pass Schedule

The drift pass runs on the same schedule as the promotion pass —
once per session end and once nightly. It evaluates all world
graph facts whose `lastReinforcedAt` has exceeded their drift
window and applies the per-period decrement to `currentConfidence`.

Per-period decrement by authority tier and observation category
(illustrative — subject to calibration):

| Category | Drift Window | Per-Period Decrement |
|----------|-------------|---------------------|
| User-stated behavioral | 180 days | 0.03 per period |
| User-stated factual | 365 days | 0.02 per period |
| Perception behavioral | 60 days | 0.05 per period |
| Perception environmental | 30 days | 0.07 per period |
| User-confirmed entity attribute | 120 days | 0.04 per period |

### What Drift Does Not Do

- Does not delete facts
- Does not contradict facts — drift is time passage, not evidence
- Does not affect user-stated facts below their floor without
  explicit user correction
- Does not apply to identity facts (who an entity is) — only
  to behavioral and pattern facts about entities
- Does not cascade — a drifted fact does not automatically drift
  related facts

---

## Integration Points

### Perceptual Input Layer → Layer 1

Active Perception writes every observation to the ephemeral buffer
immediately. The buffer feeds the Environmental Event Bus and User
State Model in real time. No Firestore write at this stage.

### Layer 1 → Layer 2

The ephemeral buffer tracks recurrence keys. When a recurrence key
crosses its promotion threshold, the buffer writes an
`EpisodicMemoryEntry` with `source: PERCEPTION` to Firestore.
This is the only Firestore write the perceptual layer makes to the
memory system.

### Layer 2 → Layer 3

The memory system runs a scheduled promotion pass. It queries
episodic entries where `source = PERCEPTION` and
`promotionEligible = true`. It applies the promotion rules defined
above. It writes confirmed promotions to the world graph. It
surfaces entity candidates through the conversation layer.

### Existing Episodic Infrastructure

The existing `EpisodicMemoryEntry`, `EpisodicMemoryKind`,
`EpisodicMemoryRanker`, and `EpisodicMemoryBuilder` infrastructure
is reused for perception-sourced entries. A new `EpisodicMemoryKind`
value — `PERCEPTION_PATTERN` — is added to distinguish perception
entries from conversation-sourced entries. The ranker's existing
decay and importance scoring logic applies to perception entries
using the same half-life parameters, with perception-specific
metadata supplementing the standard fields.

No new Firestore paths are required. The existing
`users/{userId}/episodic/` collection holds all episodic entries
regardless of source.

---

## Phase Sequencing

### Phase 3 — Ephemeral Layer Only

The ephemeral buffer is implemented. Observations decay per schedule.
The Event Bus and User State Model receive real-time ephemeral
observations. No Layer 2, 3, or 4 work.

This is the correct starting point because the perceptual layer
must be proven reliable before any pattern is worth capturing.

### Phase 4 — Layer 2 Implementation

Recurrence tracking is added to the ephemeral buffer. Promotion
to episodic memory is implemented. Entity candidate episodic
entries are written. `promotionEligible` flag logic is implemented.
Episodic decay schedules are implemented.

The memory system's promotion pass is implemented in stub form —
reads `promotionEligible` entries and logs them without writing
to the world graph yet. This allows validation of the episodic
entries before any world graph writes occur.

### Phase 5 — Layer 3 and Layer 4 Implementation

The memory system's promotion pass is fully implemented. Entity
candidate confirmation surface is implemented. World graph writes
are enabled for eligible perception-derived facts. Authority
hierarchy is enforced in retrieval. Contradiction detection and
discrepancy logging are implemented.

World Fact Lifecycle fields are written to all new promotions.
The drift pass is implemented and runs on the promotion pass
schedule. Retrieval weight formula is applied — `currentConfidence`
× age multiplier × authority multiplier. Reinforcement tracking
is implemented.

Existing promoted facts (if any) are backfilled with lifecycle
fields at Phase 5 entry. Since Zola has never been initialized
in production, no migration is required at first launch.

---

## Open Questions

**OQ-PM1 — Scheduled promotion pass frequency**
How frequently should the memory system run its Layer 2 → Layer 3
promotion evaluation pass? Too frequent and it adds unnecessary
processing. Too infrequent and promotion-eligible facts sit in
episodic memory for too long. Likely: once per session end plus
a daily background pass. Decision required before Phase 4
promotion pass implementation.

**OQ-PM2 — Entity candidate surface conversation design**
What is the exact conversational pattern Zola uses to surface
an entity candidate to the user? The question must feel natural,
not robotic. It must not alarm the user by revealing too much
about how the perception system works. It should offer easy
dismissal. Draft required before Phase 4 entity candidate
surfacing implementation.

**OQ-PM3 — Contradiction threshold**
How strong does a contradicting observation need to be to clear
the `promotionEligible` flag on an existing episodic entry? A
single low-confidence contradicting observation should not undo
a well-established pattern. A sustained pattern of contradictions
should. The threshold defines the boundary. Decision required
before Phase 4 episodic contradiction logic.

**OQ-PM4 — Perception-derived fact correction UI**
If a perception-derived fact has been promoted to the world graph
and the user wants to correct it, what is the mechanism? The
same correction path as user-stated facts, or a separate
"what Zola observed" review surface? Decision required before
Phase 5 world graph promotion is enabled.

**OQ-PM5 — Confidence drift and age multiplier calibration**
The drift decrement schedules, drift floors, age multiplier
brackets, and authority multipliers defined in Layer 4 are
illustrative starting values. They have not been validated
against real-world usage patterns. What is the calibration
process — empirical tuning from real sessions, user feedback
loops, or defined A/B criteria? The risk of miscalibration is
real in both directions: too aggressive and Zola forgets reliable
facts; too conservative and stale facts persist with unearned
confidence. A calibration plan is required before Layer 4
drift pass is enabled in production.

---

## Principles That Must Not Be Violated

**PM-P1 — Observations do not enter the world graph directly.**
Every perception-derived world graph fact must have passed through
Layer 1 and Layer 2 first. No shortcut from observation to world
graph exists. No exception.

**PM-P2 — Emotional state is not a durable world fact.**
"Brian appeared stressed" is an ephemeral observation. It may
become an episodic pattern ("Brian shows elevated stress in
deadline contexts"). It does not become a world graph assertion
that Brian is a stressed person. Layer 3 rejects emotional state
assertions about persons as a permanent fact type.

**PM-P3 — Entity candidates require user confirmation.**
Zola does not name or characterize an unconfirmed entity in the
world graph. The episodic entry holds the candidate. The world
graph receives the entity only after the user confirms it.

**PM-P4 — User-stated facts are never overridden by perception.**
If the user has stated a fact, perception cannot supersede it.
Contradicting perception-derived evidence is logged as a
discrepancy and surfaced appropriately. The user's stated fact
remains authoritative.

**PM-P5 — The memory system owns Layer 3.**
The perceptual layer's authority ends at the `promotionEligible`
flag. It does not write to the world graph. It does not make
promotion decisions. It does not confirm entity candidates. These
responsibilities belong exclusively to the memory system.

**PM-P6 — Drift weakens confidence. It does not delete truth.**
A drifted fact is uncertain, not wrong. Facts are never
automatically deleted by the drift system regardless of how low
`currentConfidence` falls. Deletion requires explicit user action
or a formal correction. The drift floor is the lowest a fact can
go without user intervention. History is preserved.

---

*Perception Memory Architecture — Version 1.1*
*Created at Phase 2 lore entry*
*Updated: Layer 4 World Fact Lifecycle added — certainty drift,*
*confidence aging, fact freshness weighting.*
*Companion document to `Zola_Architecture_Perceptual_Input_Layer.md`*
*Layer 2 implementation begins Phase 4*
*Layer 3 and Layer 4 implementation begins Phase 5*
