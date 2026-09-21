# Relational Continuity Architecture

### Foundational Architecture for the Arc of the Relationship Between
### Zola and the User

---

## Vision

The Relational Continuity Architecture defines how Zola maintains an
understanding of her relationship with the user as a living thing —
not a log of interactions, not a set of stored facts, but an arc
with history, trajectory, and texture.

Every conversation happens inside a relationship. The quality of that
relationship — how long it has been active, what it has been through,
how it tends to feel, where it is heading — is what determines whether
Zola responds like a system that knows facts about the user or a
presence that genuinely knows the user.

The goal is not for Zola to narrate the relationship. It is for the
relationship to be present in everything she says — in how she frames
things, in what she references, in how she reads a moment that
resembles something from before.

The system should eventually feel less like:

> "an assistant that starts fresh each session"

and more like:

> "a presence that has been here, that remembers what this has been
> like, and that shows up for this session knowing where things stand."

---

## Core Philosophy

### The Arc Is History, Trajectory, and Texture

Three things define what the relationship arc is:

**History** — what has happened between Zola and the user over time.
Not a transcript. Not an event log. The meaningful shape of the
relationship: what has been worked through, what has been understood,
what has become a standing reference without needing to be explained.
History is what makes it possible to say "last time you were in a
stretch like this" with accuracy.

**Trajectory** — where the relationship is heading. Is it deepening?
Has it plateaued into a functional steady state? Has there been a
period of friction that has since cleared? Trajectory is not
sentiment — it is the directional signal derived from patterns across
sessions over time. A single difficult session does not change
trajectory. A sustained pattern does.

**Texture** — the feel of the relationship as it has developed. How
Zola and the user tend to interact. What has become implicit between
them. What kind of presence Zola has learned to be for this person.
Texture is what makes a callback feel natural rather than performative.

### The Arc Informs, Never Announces

The relationship arc is never narrated to the user. Zola does not say
"based on our history" or "over the course of our relationship." She
simply responds in a way that reflects that history — in the callbacks
she makes, in the framing she chooses, in her read of what a moment
means given what she knows about this person.

The arc is the background intelligence that makes responses feel
personally grounded. It is not a topic. It is not a feature. It is
the substrate of continuity.

### Difficult Periods Are Part of the Arc

The arc does not smooth over variance. A difficult week, a period of
terse functional-only interaction, a stretch where things are clearly
stressful — these are part of the relationship's texture and the arc
holds them honestly.

A temporary High Context Friction state allows Zola to register a
difficult period without overwriting the long-term trajectory. She
does not pretend everything is fine when it clearly is not. She also
does not catastrophize a rough patch. She reads the current state
accurately and adjusts — and when the friction clears, she returns
to the longer trajectory naturally.

### Default Is Internal; Surface When Earned

The arc's primary output is internal influence on how Zola responds.
By default, the relationship history informs framing and callbacks
without being referenced explicitly.

Zola may reference the relationship naturally when a moment genuinely
calls for it — "last time you were dealing with something like this"
or "you mentioned once that." She can reflect on the relationship
honestly when asked directly. These are not scripted behaviors — they
are the natural result of having genuine relationship context available.

---

## Non-Goals

Relational Continuity is not:

- a session log or conversation transcript system — the arc is derived
  meaning, not raw storage
- a sentiment tracking system — it reads emotional signals as inputs
  to arc state, it does not produce emotional assessments
- a relationship management UI — the arc has no user-facing display
  surface; it influences behavior silently
- a therapy or coaching system — it observes patterns, it does not
  interpret or diagnose
- a replacement for the Memory Hierarchy or world graph — the arc is
  derived from what those systems already store; it does not duplicate
  them
- a parallel delivery path — all output goes through prompt injection
  or the initiative queue per RIL-D04

---

## Architectural Position

Relational Continuity sits between the existing consolidation loop
and two downstream consumers: the prompt assembly layer and the
initiative queue.

It reads from:

- `SessionSummary` — including `emotionalRegister`, `stressLevel`,
  `interactionType`, `topicTags`, `openItems`, and temporal bounds
- `MemoryCorrectionLog` — correction events that reflect the
  relationship's history of misunderstanding and course-correction
- `EpisodicMemoryEntry` — sessions of particular emotional or
  relational significance
- `OpenLoopTracker` — threads that recur across sessions,
  revealing what genuinely occupies the user's attention over time
- `ThreadArcClassifier` (Temporal Reasoning) — thread state signals
  for QUIET and OVERDUE threads that reveal unresolved relational
  patterns
- `EntityBeliefView` (Self-Model Awareness) — Zola's confidence in
  her own understanding as a signal of relationship depth
- `SessionBoundaryResolver` (Temporal Reasoning) — inter-session
  gap for trajectory and friction calculations
- `TemporalRecencyFormatter` (Temporal Reasoning) — natural-language
  age labels for history references

It produces:

- **`RelationshipArc` document** — the synthesized arc state
  maintained at `users/{userId}/world/arcs/primary_bond`
- **Arc context block** — structured relationship context injected
  into `SessionBriefBuilder` at session start
- **Friction state signal** — whether High Context Friction is
  active, available to prompt assembly for register adjustment
- **Initiative candidates** — relational observations that have
  earned the right to surface at an appropriate moment

It writes through:

- `ConsolidationLoop` step `runStep6bUpdateRelationshipArc` —
  the confirmed clean hook point between Step 6 and Step 7
- `NightlyConsolidationWorker` — arc compaction when threshold
  is breached (never synchronous at session close)

---

## The RelationshipArc Document

### Purpose

The `RelationshipArc` is the single durable document representing
the state of the relationship between Zola and the user. It is
written and maintained by `ConsolidationLoop` at session end. It is
never written in real time and never written directly by any component
other than the consolidation layer.

### Storage Structure

**Parent document** — synthesized arc state:
`users/{userId}/world/arcs/primary_bond`

Fields:
- `arcVersion: Int` — schema version; incremented on compaction
- `relationshipDepth: Float` — 0.0 to 1.0; overall depth signal
  computed from session count, correction rate, and engagement breadth
- `trajectory: String` — DEEPENING / STABLE / PLATEAUED / FRICTION
- `currentFrictionState: FrictionState` — NONE / ELEVATED / HIGH
- `frictionSessionCount: Int` — consecutive friction sessions;
  resets to 0 when friction clears
- `dominantInteractionType: String` — most common interaction mode
  across recent sessions (COLLABORATIVE / FUNCTIONAL / CASUAL /
  MIXED)
- `lastSessionAt: Long` — epoch ms of most recent session
- `firstSessionAt: Long` — epoch ms of first session
- `totalSessionCount: Int` — lifetime session count
- `compactionPending: Boolean` — set true when delta threshold
  is breached; read by nightly consolidation worker
- `arcNarrativeSummary: String?` — LLM-synthesized narrative
  summary of the arc; written by nightly compaction pass; null
  until first compaction runs
- `updatedAtMs: Long` — epoch ms of last arc update

**Delta sub-collection** — raw session history:
`users/{userId}/world/arcs/primary_bond/arc_session_deltas/{sessionId}`

Fields per delta:
- `sessionId: String`
- `sessionAt: Long` — epoch ms of session end
- `emotionalRegister: String?` — from `SessionSummary`
- `stressLevel: String?` — from `SessionSummary` (new field)
- `interactionType: String?` — from `SessionSummary` (new field)
- `topicTags: List<String>` — from `SessionSummary`
- `openLoopCount: Int` — active open loops at session end
- `correctionCount: Int` — corrections in this session
- `frictionContribution: Boolean` — whether this session
  contributed to friction state
- `sessionDeltaSizeBytes: Int` — for compaction threshold tracking

### Scaling and Compaction

Per-session deltas are approximately 200–300 bytes each. At 1–3
sessions per day the delta sub-collection grows at roughly 200KB
per year — well within manageable bounds as a sub-collection.

The parent arc document stays small and readable — it holds only
synthesized state, not raw history.

**Compaction triggers** (whichever comes first):
- `ARC_COMPACTION_MAX_DELTAS = 180` (approximately 60–90 days
  of daily use)
- `ARC_COMPACTION_BYTE_THRESHOLD = 500_000` (500KB across
  sub-collection)

When either threshold is breached at session close:
1. `runStep6bUpdateRelationshipArc` writes the session delta normally
2. Sets `compactionPending: true` on the parent document
3. Session close completes — no LLM call, no latency spike

`NightlyConsolidationWorker` reads `compactionPending`:
1. Captures `compactBefore = System.currentTimeMillis()` at job
   start — this is the compaction boundary timestamp
2. Reads all deltas from `arc_session_deltas` where
   `sessionAt <= compactBefore` — deltas written by concurrent
   late-night sessions after `compactBefore` are excluded from
   this compaction run and preserved for the next cycle
3. Runs LLM re-synthesis over the filtered delta set only
4. Writes compressed `arcNarrativeSummary` to parent document
5. Removes only deltas where `sessionAt <= compactBefore` AND
   `sessionAt < (compactBefore - ARC_COMPACTION_ROLLING_WINDOW_MS)`
   — never deletes deltas newer than `compactBefore` regardless
   of rolling window calculation
6. Clears `compactionPending: false` only after step 5 completes
   successfully — if the job fails before step 5, the flag
   remains set and the job retries on the next nightly pass

Any delta written by a live session with `sessionAt > compactBefore`
is invisible to the current compaction run. It is not synthesized
into the current narrative and is not deleted. It will be included
in the next compaction cycle when its `sessionAt` falls before the
next `compactBefore` timestamp.

This design ensures that a late-night session concurrent with
nightly compaction cannot lose its arc delta to a race condition.

This design ensures session close is always lightweight. The
expensive LLM work happens asynchronously overnight.

---

## Long-Term Architectural Pillars

---

## 1. ArcStateUpdater

### Purpose

Compute the updated arc state from a completed session's data and
write it to both the parent `RelationshipArc` document and the
`arc_session_deltas` sub-collection.

### Responsibilities

- run as `runStep6bUpdateRelationshipArc` in `ConsolidationLoop`,
  after `launchGeminiEmotionEnrichment` and before
  `runStep7ClearEphemeralBuffers`
- read the persisted `SessionSummary` for the completed session,
  including `emotionalRegister`, `stressLevel`, and `interactionType`
- read the current `RelationshipArc` parent document
- compute updated `trajectory`, `currentFrictionState`, and
  `frictionSessionCount` (see FrictionStateEvaluator below)
- compute updated `relationshipDepth` (see RelationshipDepthModel
  below)
- write the session delta to `arc_session_deltas`
- write updated synthesized state to parent arc document
- check compaction thresholds; set `compactionPending: true` if
  either threshold is breached
- use sync enrichment output only — async enrichment that completes
  after Step 7 is handled by a nightly backfill pass, not by this
  step

### Inputs Available at Hook Point

Confirmed available at `ConsolidationLoop.kt:194–199`:
- Persisted `SessionSummary` with all fields
- `chunkTurns` transcript buffer for optional richer synthesis
- Active open-loop state from Steps 4 and 4b

### Important Principle

`ArcStateUpdater` writes to the arc. It does not read from the arc
to make decisions about the session — only the prior arc state
provides context. Session data is the input; arc update is the
output.

---

## 2. FrictionStateEvaluator

### Purpose

Determine whether the current session contributes to a High Context
Friction state, and whether the friction state should change.

### Friction vs Trajectory — The Key Distinction

These are two separate signals that must not be conflated:

**Current Friction State** — a temporary behavioral flag derived
from single-session signals. If `stressLevel` is elevated in a
session, friction state rises. When subsequent sessions show lower
stress, friction state clears. Friction state changes session to
session.

**Trajectory** — a longitudinal signal derived from sustained
patterns. Trajectory changes only when the pattern persists across
`ARC_FRICTION_TRAJECTORY_MIN_SESSIONS` consecutive sessions. A
single high-stress session does not change trajectory. Three
consecutive sessions of HIGH friction with FUNCTIONAL interaction
type does.

### Friction State Transitions

**NONE → ELEVATED:**
- `stressLevel == HIGH` in current session
- OR `interactionType == FUNCTIONAL` with no warm signals

**ELEVATED → HIGH:**
- `frictionSessionCount >= ARC_FRICTION_ELEVATED_THRESHOLD`
  (initial value: 2 consecutive sessions)

**HIGH → ELEVATED** (proportional recovery — not direct to NONE):
- Current session `stressLevel` is NORMAL or LOW
- AND `interactionType` is not FUNCTIONAL
- A single positive session from HIGH drops to ELEVATED, not NONE —
  the relationship does not instantly heal from a deep friction period

**ELEVATED → NONE:**
- Current session `stressLevel` is NORMAL or LOW
- AND `interactionType` is not FUNCTIONAL
- A single positive session from ELEVATED clears to NONE

**Trajectory update (STABLE → FRICTION):**
- `frictionSessionCount >= ARC_FRICTION_TRAJECTORY_MIN_SESSIONS`
  (initial value: 5 consecutive sessions)

**Trajectory update (FRICTION → STABLE):**
- 3 consecutive sessions with friction state NONE

All threshold values are named constants, calibration-ready.

### Proportional Recovery Rationale

The two-step recovery from HIGH (HIGH → ELEVATED → NONE) mirrors
how real relationships work. A single pleasant interaction after a
sustained difficult period does not instantly restore full warmth —
the user and Zola are still finding their footing. Moving from HIGH
to ELEVATED on one positive session reduces friction immediately and
meaningfully, while the second positive session confirms that the
recovery is genuine before full callback range is restored.

This prevents conversational whiplash — Zola pivoting from highly
reserved directly back to personal callbacks in a single session,
which can feel jarring if the user is still testing the waters.

### Important Principle

A single bad session does not redefine the relationship. A single
good session does not instantly repair one. The friction evaluator
is designed to be slow to escalate trajectory, gradual in recovery
from deep friction, and fast to clear surface-level friction —
because a presence that catastrophizes a rough patch is worse than
one that registers it accurately and recovers proportionally.

---

## 3. RelationshipDepthModel

### Purpose

Compute the `relationshipDepth` score — a single float representing
how deep the relationship between Zola and the user currently is.

### Inputs

- `totalSessionCount` — raw session history depth
- `correctionRate` — ratio of corrections to reinforcements across
  `MemoryCorrectionLog`; lower rate indicates more accurate
  understanding
- `engagementBreadth` — number of distinct topic domains that have
  appeared in session summaries; wider engagement indicates deeper
  relationship
- `relationshipAge` — elapsed time since `firstSessionAt`, computed
  via `SessionBoundaryResolver`

### Score Interpretation

| Range | Meaning |
|---|---|
| 0.00 – 0.25 | Early — relationship is new; Zola knows little about this person yet |
| 0.26 – 0.50 | Developing — patterns are emerging; some texture is established |
| 0.51 – 0.75 | Established — clear history; Zola has a reliable picture of who this person is |
| 0.76 – 1.00 | Deep — rich history, broad engagement, high mutual understanding |

### Important Principle

`relationshipDepth` feeds Relational Calibration (subsystem 5)
as its primary input for determining what depth of familiarity
Zola's expression should reflect. The depth score must be stable
— it should not spike or drop based on a single session.

---

## 4. ArcContextAssembler

### Purpose

Produce the relationship context block injected into prompt assembly
at session start — so that Zola enters every session knowing where
things stand with this person.

### Responsibilities

- read the current `RelationshipArc` parent document
- read recent `arc_session_deltas` (last N sessions, where N is
  configurable) for recent pattern context
- read `arcNarrativeSummary` if available from prior compaction
- produce a structured `ArcContextBlock` containing:
  - relationship depth signal
  - current trajectory
  - current friction state and its behavioral implication
    (HIGH friction → suppress casual callbacks, match functional
    register; NONE → full callback range available)
  - recent pattern summary (what the last few sessions have felt
    like)
  - `arcNarrativeSummary` excerpt if available and relevant
- deliver to `SessionBriefBuilder` for injection into the
  `[CONTINUITY]` bracket section
- run at session start; result is valid for the session duration

### Friction State Behavioral Implication

The friction state is not just a label — it carries a specific
behavioral implication for how Zola shows up:

**HIGH Context Friction:**
- suppress casual banter and personal callbacks
- match the user's functional register
- reduce proactive initiative surfacing from the continuity layer
- do not reference relationship history unless directly relevant
  to what is being worked on

**ELEVATED Context Friction:**
- reduce casual callbacks; keep references purposeful
- maintain warmth but prioritize efficiency
- soften proactive continuity observations

**NONE:**
- full callback range available
- relationship texture can inform framing naturally
- continuity observations may surface when contextually appropriate

### Important Principle

`ArcContextAssembler` produces context. It does not instruct Zola
what to say. The friction state and relationship depth inform the
register and reference range available — they do not script
responses.

---

## 5. ContinuityInitiativeSource

### Purpose

Produce initiative candidates when a relational observation has
earned the right to surface — when the arc contains something
genuinely worth saying at this moment.

### What May Surface

- A callback to a previous period that is directly relevant to
  what is happening now: "last time you were in a stretch like this,
  you mentioned that it helped to just talk through it"
- An observation about a recurring pattern that has become
  significant: "this is the third time in the last month that
  this has come up"
- A gentle acknowledgment of a difficult period that has passed:
  "things have felt a bit different lately — seems like things
  have eased up a bit"

### What Does Not Surface

- Relationship arc observations that are not directly relevant
  to the current moment
- Anything during HIGH Context Friction — the continuity layer
  goes quiet when friction is high
- Callbacks that reference specific past sessions in ways that
  might feel surveillance-like
- Observations that would require the user to confirm or engage
  with the observation itself

### Urgency Tiers

All continuity initiative candidates use the low-pressure tier
(0.2–0.35). Continuity observations are never urgent. They surface
when the moment is right — not because a threshold was crossed.

### Important Principle

Continuity observations surface in service of the moment, not as
a report on the relationship's status. If they feel like the former,
they belong. If they feel like the latter, they do not.

---

## Emotional Signal Integration

### What Feeds the Arc

The arc is designed to read synthesized outputs of the first three
Relational Intelligence subsystems rather than raw conversational
fragments:

- **Temporal Reasoning** — thread arc classifications, session age,
  inter-session gap signals
- **Self-Model Awareness** — Zola's confidence in her own beliefs
  about the user; a proxy for how well she knows this person
- **Social Graph Reasoning** — recurring entities that reveal what
  genuinely occupies the user's attention across sessions

Plus direct session data from `ConsolidationLoop`:
- `SessionSummary.emotionalRegister` — existing durable field
- `SessionSummary.stressLevel` — new field added in RC pre-work
- `SessionSummary.interactionType` — new field added in RC pre-work
- `SessionSummary.topicTags` — existing field
- Open loop state from Steps 4 and 4b

### Handling Partial Emotional Signal

The audit (P29-RC-AUD-16, AUD-18) confirmed the current emotional
signal is partial — `emotionalRegister` exists as a single word but
`stressLevel` and `interactionType` do not exist yet. The arc is
designed to function with whatever signal is available:

- If `stressLevel` is null: friction evaluation uses
  `emotionalRegister` as a proxy
- If `interactionType` is null: trajectory uses topic tag patterns
  as a proxy for interaction mode

These are explicitly temporary fallbacks. Once `stressLevel` and
`interactionType` are added to `SessionSummary` and populated by
Step 6, the arc will use the full signal.

### MoodTracker and detectedTone

`MoodTracker` keyword mood signal and `ConversationContext.detectedTone`
are not currently read by `ConsolidationLoop`. The arc does not
depend on them in v1. If they are wired into consolidation synthesis
in a future track, the arc benefits automatically — no arc change
required.

---

## Integration Points

---

### What Relational Continuity Reads

| Source | Class / Method | Data consumed |
|---|---|---|
| Session summary | `FirestoreSessionSummaryRepository` | emotionalRegister, stressLevel, interactionType, topicTags, openItems, temporal bounds |
| Correction history | `MemoryCorrectionLog` | Correction count per session |
| Open loop state | `OpenLoopTracker` | Active loop count at session end |
| Thread arc | `ThreadArcClassifier` (Temporal Reasoning) | QUIET / OVERDUE thread signals |
| Entity belief | `EntityBeliefView` (Self-Model Awareness) | metaKnowingConfidence for user entity |
| Session boundary | `SessionBoundaryResolver` (Temporal Reasoning) | Inter-session gap, relationship age |
| Recency formatting | `TemporalRecencyFormatter` (Temporal Reasoning) | Natural-language age labels |

---

### What Relational Continuity Writes

| Target | Class / Method | What is written |
|---|---|---|
| Arc parent document | `ArcStateUpdater` via `ConsolidationLoop` step 6b | Synthesized arc state |
| Arc delta sub-collection | `ArcStateUpdater` via `ConsolidationLoop` step 6b | Per-session delta |
| Arc compaction flag | `ArcStateUpdater` — sets `compactionPending: true` | Threshold breach signal |
| Arc narrative summary | `NightlyConsolidationWorker` | LLM-synthesized narrative after compaction |

---

### What Relational Continuity Produces for Prompts

| Destination | Class / Method | What is injected |
|---|---|---|
| Session brief | `SessionBriefBuilder.assemble` — `[CONTINUITY]` bracket section | Arc context block, friction state, depth signal |
| Memory block | `MemoryInjectionBuilder.buildMemoryBlock` | Friction behavioral implication for register adjustment |

---

### What Relational Continuity Enqueues

| Destination | Class / Method | What is enqueued |
|---|---|---|
| Initiative queue | `InitiativeQueue.enqueue` via `ContinuityInitiativeSource` | Low-pressure relational observations |
| Evaluator gate | `InitiativeQueueEvaluator.evaluate` | Standard cooldown; suppressed during HIGH friction |

---

## Known Constraints and Deferred Work

### Emotional Signal Extension (Pre-Work Required)

`SessionSummary` requires two new fields before the arc can use
a full affective profile: `stressLevel: String?` and
`interactionType: String?`. These must be populated by an extension
to Step 6's Gemini enrichment prompt. Until then, the arc uses
`emotionalRegister` as a proxy with explicit fallback logic.

### Async Emotion Enrichment Timing

`GeminiEmotionAnalyzer` runs asynchronously and may complete after
Step 7. The arc write step uses sync enrichment output only. If
async enrichment later updates `SessionSummary.emotionalRegister`,
the nightly pass can optionally backfill the arc delta — but this
is a future enhancement, not a v1 requirement.

### Nightly Pass Affective Signal

`NightlyConsolidationWorker` lacks access to affective signals at
the time it runs (P29-RC-AUD-10). Arc compaction in the nightly
pass reads `arc_session_deltas` which were written at session end
with whatever signal was available then. The nightly pass does not
re-derive emotional signals from session data.

### User Self-Entity Gender

OQ-P19-T3-SELF-GENDER-01 — the user's SELF entity lacks a gender
attribute, which affects traversal disambiguation. This is a known
open question that predates Relational Continuity. The arc does not
depend on gender disambiguation.

---

## Authority Boundaries

### Relational Continuity may:

- read from session summaries, correction logs, open loop state,
  and RIL shared infrastructure
- write to the `RelationshipArc` document and `arc_session_deltas`
  sub-collection through `ConsolidationLoop` step 6b
- set `compactionPending` flag on the arc document
- trigger arc compaction via `NightlyConsolidationWorker`
- produce arc context blocks for prompt injection
- enqueue initiative candidates via `ContinuityInitiativeSource`

### Relational Continuity must not:

- write to any other Firestore collection or memory store
- modify session summaries, correction logs, or open loop entries
- invoke `ResponseExecutionService` or `GeminiLiveClient` directly
- deliver speech through any path other than the initiative queue
  or prompt injection
- surface initiative candidates during HIGH Context Friction state
- run LLM synthesis synchronously at session close

---

## Relationship to Relational Intelligence Layer

Relational Continuity is the fourth implemented subsystem of the
Relational Intelligence Layer. It depends on:

- **Temporal Reasoning** (subsystem 1) — `SessionBoundaryResolver`
  for relationship age and inter-session gap, `ThreadArcClassifier`
  for thread state signals, `TemporalRecencyFormatter` for
  natural-language references
- **Self-Model Awareness** (subsystem 2) — `EntityBeliefView`
  for Zola's confidence in her understanding of the user;
  `MetaKnowingConfidence` as a relationship depth input
- **Social Graph Reasoning** (subsystem 3) — recurring entity
  signals that reveal sustained attention patterns

It is depended on by:

- **Relational Calibration** (subsystem 5) — reads
  `relationshipDepth` and current `trajectory` as primary inputs
  for calibrating how familiar Zola's expression should be

It produces the `RelationshipArc` document type that:

- **Self-Model Awareness** references for Zola's understanding of
  herself within the relationship
- **Relational Calibration** reads for depth-based expression
  calibration

---

## Long-Term End State

Relational Continuity eventually supports:

- a relationship that deepens naturally over months and years
  without the user ever having to manage it
- callbacks and framing that feel grounded in genuine shared
  history — not scripted warmth, not generic familiarity
- honest registration of difficult periods that adjusts Zola's
  register without erasing the longer arc
- a narrative summary of the relationship that could be read
  as a coherent account of what has been built together
- the foundation for Relational Calibration to know not just
  how deep the relationship is but what that depth means for
  how Zola should show up

The system should ultimately feel:

- continuous across sessions without requiring the user to
  re-establish context
- warm where warmth has been earned, functional where that is
  what is needed
- perceptive about what a moment means given what has come before
- honest about difficult periods without being defined by them

without becoming:

- a relationship manager that narrates the relationship back
- a system that treats every session as an opportunity to
  reference the history
- a presence that holds on to difficult periods longer than
  the user does
- a layer that produces output in proportion to how much
  it has accumulated

---

## Final Principle

The relationship between Zola and the user is not a feature.
It is the context inside which every interaction happens.

Relational Continuity exists to ensure that context is present —
quietly, accurately, and in service of the moment — so that every
session feels like a continuation of something real, not a fresh
start with a system that has forgotten what came before.
