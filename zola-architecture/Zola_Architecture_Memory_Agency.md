# Memory Agency Architecture

### How Zola Decides What Matters, Retains It Appropriately,
### and Maintains Continuity Without Being Asked

---

## Vision

Most memory systems are storage systems. They accept input, write
it to a database, and return it when queried. They do not evaluate
whether the input mattered. They do not decide whether the stored
fact is still relevant. They do not notice when something they
know connects to something happening right now.

Zola's memory is not a storage system. It is a governed belief
model — an internal representation of the world that Zola
maintains, refines, and acts from. The difference is not
cosmetic. It changes every part of the architecture.

A storage system accumulates. A belief model breathes.

A storage system answers when queried. A belief model participates
actively in Zola's understanding of every moment.

A storage system treats all input equally. A belief model evaluates
significance, assigns authority, tracks freshness, and maintains
the integrity of what it holds.

This document defines the architecture that makes Zola's memory
a belief model rather than an accumulation. It covers how Zola
decides what is worth remembering, how memories are consolidated
and maintained, how unresolved things stay cognitively active,
and how memory feeds Zola's curiosity and engagement without
producing an entity that constantly interrupts.

The system should eventually feel less like:

> "an assistant that stores what you tell it"

and more like:

> "a presence that pays attention, remembers what matters,
> and remains engaged with the threads of your world over time."

---

## The Foundational Principle

> Zola's memory system is not a database of facts.
> It is a governed belief model.
>
> Every stored item carries source, scope, authority, freshness,
> privacy, and allowed-use metadata.
>
> Zola does not wait for memory to be requested. She maintains
> continuity by deciding what matters, retaining it appropriately,
> and resurfacing it when context makes it useful, safe,
> and welcome.

This principle has three active parts:

**She decides what matters.** The save decision is internal and
evaluated. Zola does not write everything to memory. She writes
what is significant relative to her world model — what changes
her understanding of an entity, a pattern, a relationship, or
a situation.

**She retains it appropriately.** Not all memories are equal.
Some are ephemeral. Some are episodic. Some earn permanent world
graph status. The storage layer, lifecycle, and decay policy
match the nature of what was remembered.

**She resurfaces when context makes it useful, safe, and welcome.**
Recall is not only query-driven. Zola maintains contextual
awareness of what she knows and notices when a memory becomes
relevant — but she governs whether and how to surface it through
the privacy and attention systems that protect against intrusion.

---

## Memory Types

Zola's belief model contains distinct memory types. Each type
has its own storage layer, authority level, decay policy, and
recall behavior. They are not interchangeable.

**Identity Memory**
What Zola knows about herself — her values, her character, her
commitments, her operating principles. This memory is
foundational and does not decay. It is the anchor of consistent
behavior across all contexts.

**Entity Memory**
What Zola knows about named entities — people, vehicles, places,
devices, projects, businesses. Entity memory is structured,
entity-native, and world graph-resident. It persists until
corrected. It is the subject of world fact lifecycle management
(confidence aging, drift).

**Relationship Memory**
What Zola knows about edges between entities — how people relate
to each other, how projects connect to people, how places
connect to routines. Relationship memory is directional and
typed. Relationships decay faster than entity facts when
unreinforced.

**Episodic Memory**
Things that happened — conversations, events, experiences,
sessions. Episodic memory is time-bounded and contextually
rich. It decays on a defined schedule but may be promoted to
semantic memory if patterns emerge across multiple episodes.

**Semantic Memory**
Stable facts that have earned durable status — things Zola
understands to be consistently true about the world, people,
and situations she inhabits. Semantic memory is promoted from
episodic through the Consolidation Loop. It is subject to
confidence drift.

**Preference Memory**
What Zola knows about the user's likes, defaults, habits, and
behavioral tendencies. Preference memory is reinforced by
recurrence and weakened by contradiction. It informs tone and
behavior without being stated explicitly.

**Instruction Memory**
Rules the user has given Zola — behavioral directives, standing
preferences, explicit instructions. Instruction memory has high
authority and does not decay passively. It requires explicit
user correction to change.

**Pattern Memory**
Recurring behavioral, environmental, or contextual patterns
observed across multiple sessions. Pattern memory is built by
the Consolidation Loop from episodic evidence. It has moderate
authority and decays if the pattern breaks.

**Open Loop Memory**
Unresolved things — promises, plans, questions, worries,
abandoned topics, unfinished tasks, open investigations. Open
loop memory is actively maintained — it generates cognitive
tension and resurfaces when context makes resolution possible.
It is explicitly closed when resolved or abandoned.

**Context Memory**
Current session and active topic state. Context memory is
ephemeral — it exists only for the duration of the session
and the active conversational thread. It does not persist
beyond session boundaries unless promoted by the Consolidation
Loop.

**Correction Memory**
Records of corrections — what was wrong, what replaced it,
when, and why. Correction memory is kept as a record even
after the correction has been applied. It prevents re-learning
incorrect facts and informs how Zola handles similar
information in the future.

**Privacy Memory**
What cannot be repeated casually — facts the user has
designated as private, facts in sacred memory classes, facts
that carry `NEVER_SPEAK_ALOUD` or `PRIVATE_TO_ZOLA` scope.
Privacy memory is a property of other memory types, not a
separate store, but it governs their disclosure across all
output paths.

---

## Memory Write Pipeline

Every candidate memory — whether sourced from conversation,
perception, tool data, or inference — passes through a staged
evaluation before any write to durable storage occurs. The
pipeline is not optional. There is no direct write path that
bypasses it.

### Pipeline Stages

**Stage 1 — Input**
The raw signal arrives. This may be a conversation utterance,
a typed observation from Active Perception, a tool result, or
an inference from the reasoning system. The signal enters the
pipeline as uninterpreted input.

**Stage 2 — Meaning Extraction**
What was actually said or observed, and what did it mean?
This stage separates surface content from semantic content.
"I hate Mondays" is surface. "User expressed negative sentiment
about the start of the work week" is semantic. The extraction
also applies the social deniability layer — rhetorical,
sarcastic, and emotionally heightened statements are flagged
and handled with reduced authority.

**Stage 3 — Entity Resolution**
Who or what is this about? The extracted meaning is resolved
against the existing entity graph. If the subject is a known
entity, the candidate is associated with that entity record.
If the subject is unknown, an entity candidate is created or
an existing candidate is updated. Ambiguous subjects are
flagged for resolution rather than assumed.

**Stage 4 — Memory Type Classification**
Is this a fact, a preference, a mood, an event, a pattern,
a correction, or an instruction? The classification determines
which memory type the candidate belongs to and which storage
layer and decay policy apply.

**Stage 5 — Sensitivity Classification**
Does this candidate fall into a sacred memory class? Does it
carry sensitivity signals — emotional weight, health content,
financial content, legal content, relationship conflict? The
sensitivity classification informs scope assignment and governs
how the candidate is handled throughout its lifecycle.

**Stage 6 — Authority Classification**
What is the source of this candidate and what authority level
does that source carry? User-stated, user-confirmed, perception-
derived, system-inferred, tool-provided, conversational-implicit.
Authority is assigned at write time and travels with the memory
throughout its lifecycle.

**Stage 7 — Scope Assignment**
What visibility scope applies? The scope taxonomy from the
Memory Ethics and Privacy Layer is applied here. Vault session
status, sacred class membership, explicit user designation,
and inferred sensitivity all inform scope. The scope may only
be upgraded (made more restrictive) after write time — never
downgraded without explicit user action.

**Stage 8 — Salience Evaluation**
Does this candidate deserve to be remembered? The Memory
Salience Scorer evaluates the candidate against the criteria
defined below. If salience is below the write threshold, the
candidate is discarded without trace. If salience is above
the threshold, the candidate advances to Stage 9.

**Stage 9 — Storage Layer Decision**
Where should this live? Based on memory type, authority, and
salience score, the pipeline assigns the candidate to a storage
layer: ephemeral buffer (session-only), episodic store
(medium-term), or world graph (durable). Context memory lives
only in the session buffer. Open loop candidates are flagged
for the Open Loop Tracker. Pattern candidates enter the
episodic store with `kind: PERCEPTION_PATTERN` or
`kind: BEHAVIORAL_PATTERN` as appropriate.

**Stage 10 — Lifecycle and Freshness Policy**
The candidate's lifecycle state, decay window, drift parameters,
and reinforcement rules are assigned based on memory type and
authority. These govern the memory's entire future existence
in the belief model.

**Stage 11 — Write Approval**
The candidate is written to its assigned storage layer with
all metadata intact: source, scope, authority, freshness
policy, provenance, sensitivity flags, and lifecycle state.
The write is the final stage. There is no post-write
correction path — corrections are handled through Correction
Memory as a separate write.

### What the Pipeline Is Not

The pipeline is not a filter that rejects bad inputs. It is
a governance system that ensures every memory that enters
the belief model carries the metadata required to be used
correctly throughout its lifetime. A candidate that fails
salience evaluation is not rejected because it was bad input
— it was simply not significant enough to deserve retention.
Most inputs will not survive salience evaluation. That is
the correct behavior.

---

## Memory Salience Scorer

The Memory Salience Scorer is a standalone component that
evaluates whether a moment deserves retention. It is called
by the Write Pipeline during Stage 8 and by the Consolidation
Loop during post-session review.

The Scorer does not write. It evaluates and scores. The
pipeline and the Consolidation Loop use the score to make
write decisions.

### Salience Criteria

**Relationship Significance**
Does this moment change what Zola understands about a person,
project, place, or relationship? New information about an
entity's situation, character, needs, or state carries high
relationship significance. Repetition of already-known facts
carries low significance.

**Future Utility**
Will this help Zola act better later? Information that is
likely to be relevant to future decisions, future conversations,
or future assistance has high future utility. One-time
contextual details with no forward relevance have low utility.

**Emotional Weight**
Was this moment important, frustrating, exciting, stressful,
sensitive, or emotionally significant in any direction? Emotionally
weighted moments carry higher salience because they represent
moments that mattered to the user. Neutral, transactional
exchanges carry lower emotional salience.

**Pattern Value**
Is this part of something recurring? A moment that fits or
extends a recognized pattern carries higher salience than an
isolated instance. A moment that breaks a recognized pattern
carries very high salience — pattern violations are significant.

**Identity Relevance**
Does this affect who Zola is, how she should behave, or how
she relates to the world? Instructions, corrections, and
character-relevant moments carry high identity relevance.

**Project Relevance**
Does this belong to an ongoing project Zola is tracking —
Zola architecture, Double R, the shop, work, family, an
ongoing investigation? Active project relevance elevates
salience because the candidate is more likely to be useful
within a defined ongoing context.

**Unfinished Business**
Is there an unresolved task, question, plan, worry, promise,
or open loop here? Unresolved things carry high salience
because they require future tracking and potential resurfacing.
A completed thing has lower salience than an open one.

**Novelty**
Is this new information, or does Zola already know it? Genuinely
new facts carry higher salience than confirmation of existing
facts (though confirmation still carries reinforcement value).

### Salience Score Output

The Scorer produces:

- `salienceScore` — float 0.0–1.0
- `salienceClass` — the dominant criterion that drove the score
- `memoryTypeRecommendation` — what kind of memory this should
  become
- `openLoopFlag` — whether this candidate should also enter
  the Open Loop Tracker
- `cognitiveHeatContribution` — whether this candidate should
  increase the salience weight of a related existing memory

### Write Threshold

The initial write threshold is 0.40. Candidates below this
score are discarded without trace. Candidates between 0.40
and 0.65 enter the episodic store as pending candidates,
subject to Consolidation Loop review. Candidates above 0.65
are written immediately to their assigned storage layer.

These thresholds are initial values subject to calibration
after Phase 3 implementation.

---

## Memory Consolidation Loop

The Consolidation Loop runs at session end and on a nightly
schedule. Its job is to distill session content into persistent
knowledge — to decide what survives, what gets promoted, what
decays, and what enters the world graph.

### Trigger Model

**Session-end trigger:** The Session Lifecycle Manager fires
a `CONSOLIDATION_TRIGGER` event when a session closes. The
memory system receives this trigger and executes the full
Consolidation Loop against the session's candidate memory.

**Nightly trigger:** A background worker fires the nightly
pass independently of session rhythm. The nightly pass handles
long-term memory health — drift evaluation, open loop aging,
pattern promotion across multiple sessions, and stale memory
review.

### Session-End Consolidation Sequence

**Step 1 — Re-score pending candidates**
Candidates that entered the episodic store as pending during
the session are re-scored by the Memory Salience Scorer with
full session context. A candidate that scored 0.45 in isolation
may score 0.72 when evaluated against everything else that
happened in the same session. The session provides the context
the real-time scorer didn't have.

**Step 2 — Write or discard pending candidates**
Candidates that cross the write threshold after re-scoring are
written to their assigned storage layer with full metadata.
Candidates that do not cross the threshold are discarded.
No record of discarded candidates is kept — they were not
significant enough to remember.

**Step 3 — Promote episodic entries**
Episodic entries from prior sessions that have now crossed
their recurrence and consistency thresholds are flagged
`promotionEligible` for world graph consideration, per the
Perception Memory Architecture promotion rules.

**Step 4 — Update Open Loop items**
Open loop items touched during the session are updated.
Resolved loops are closed. Loops that were mentioned but
not resolved are reinforced. New open loops identified
during the session are created.

**Step 5 — Flag cognitive tension items**
The loop evaluates what has emerged as cognitively active
— unresolved, recurring, contradicted, emotionally weighted,
or anomalous. These become cognitive tension candidates (see
Cognitive Tension below).

**Step 6 — Write session summary**
A high-level episodic summary of the session is written to
the episodic store. This is not a transcript — it is a
semantic summary of what happened, what was discussed, what
was resolved, and what remains open. The summary becomes
the retrievable record of the session.

**Step 7 — Clear ephemeral buffer**
The session's ephemeral observation buffer is cleared.
Raw ephemeral content does not survive session close.

### Nightly Pass

The nightly pass runs the following without session context:

- Drift evaluation across all world graph facts
- Open loop aging — loops not touched in their staleness
  window are downgraded in priority
- Pattern detection across multiple recent sessions —
  patterns that only emerge across sessions are identified
- Stale memory review — facts that have drifted to their
  floor are flagged for user confirmation
- Cognitive tension review — tension items that have grown
  in salience over multiple sessions are escalated

---

## Open Loop Tracker

The Open Loop Tracker maintains a live list of unresolved
things — the cognitive items that cannot simply be stored
and forgotten because they require future attention.

### What Becomes an Open Loop

- Explicit promises or commitments Zola made or the user made
- Unresolved questions the user raised but did not answer
- Plans that were mentioned but not completed
- Worries or concerns the user expressed that were not resolved
- Abandoned topics — subjects that were dropped mid-conversation
  without conclusion
- Unfinished tasks referenced in conversation
- Open investigations — "I need to figure out what's causing X"
- Contradictions that were noticed but not resolved

### Open Loop States

**Active** — currently relevant; recent and high-salience

**Pending** — potentially relevant; waiting for context that
might make resolution possible

**Dormant** — not recently relevant; salience has decreased
but the loop is not closed

**Resolved** — explicitly closed by user action, conversation
outcome, or confirmed resolution

**Abandoned** — the loop has aged past its staleness window
and the user has not returned to it; treated as intentionally
dropped unless context reactivates it

### Loop Lifecycle

An open loop is created with an initial salience score and
a staleness window. Its salience is reinforced each time it
appears in conversation or perception context. It decays
when nothing touches it. When it crosses its staleness
threshold without resolution, it moves from Active to Pending
to Dormant. A user explicitly closing or resolving it moves
it to Resolved.

Open loops do not delete themselves. A Resolved or Abandoned
loop is kept as a record. Zola may recognize when a previously
resolved loop has reopened.

### What Open Loops Generate

Active open loops generate:
- Elevated attention toward related context
- Curiosity candidates in the Cognitive Engagement system
- Resurfacing candidates in the Contextual Resurfacing Engine
- Cognitive tension weighting that affects Zola's tone and
  attentiveness in related conversational areas

---

## Cognitive Tension

Cognitive tension is the state of having something in memory
that is unresolved, recurring, contradictory, emotionally
weighted, or anomalous. Cognitively tense memories are not
passive — they remain active in Zola's belief model and
influence her attention, engagement, and behavior.

### What Creates Cognitive Tension

**Unresolved problems**
A problem was identified, discussed, or acknowledged and no
resolution has been observed. The tension remains until
resolution is confirmed or the loop is explicitly closed.

**Abandoned topics**
A subject was dropped without conclusion across multiple
sessions. The abandonment itself is data — but the unresolved
content maintains low-level tension as an open question.

**Recurring anomalies**
Something that should not keep happening keeps happening.
A noise that reappears. A pattern that contradicts an
established expectation. Anomalies accumulate tension with
each recurrence.

**Broken expectations**
Zola expected something based on established patterns and
it did not happen. A routine that was broken. A plan that
was not followed through. A person who has not been mentioned
when they typically would be.

**Emotionally significant changes**
A shift in tone, behavior, or situation that represents a
meaningful change from baseline. Not a diagnosis — a noticed
change that Zola holds as an active question.

**Interrupted plans**
Plans that were in motion and then stopped without explanation.
The interruption creates tension because the outcome is unknown.

**Inconsistent information**
Two things Zola knows that are in tension with each other.
Not a formal contradiction — an inconsistency that has not
been resolved. Zola holds both and the inconsistency generates
cognitive heat.

**Unexplained observations**
Something perception observed or conversation implied that
has no clear explanation in the current world model.

### Cognitive Tension Properties

Each tension item carries:

- `tensionType` — the category above
- `subject` — which entity or topic this tension is about
- `tensionWeight` — float 0.0–1.0; how much cognitive heat
  this item carries
- `firstObservedAt` — when the tension was first registered
- `lastReinforcedAt` — when it was most recently relevant
- `reinforcementCount` — how many times the situation has
  recurred or been touched
- `resolutionCandidates` — what would resolve this tension
- `curiosityCandidate` — whether this is eligible to generate
  a curiosity-driven inquiry

### Tension Accumulation and Resolution

Tension weight increases with each reinforcement — each time
the related situation appears without resolution. It decreases
slowly over time without reinforcement. A tension item that
reaches high weight generates proactive behavior candidates
routed through the Attention/Relevance Engine.

Tension is resolved when:
- The user provides a resolution in conversation
- Zola asks and receives a satisfying answer
- The underlying open loop is closed
- The anomaly stops recurring across a sufficient time window
- The user explicitly dismisses the concern

Resolved tension items are kept as records. Zola can recognize
when resolved tension has reopened.

---

## Contextual Resurfacing Engine

The Contextual Resurfacing Engine detects when a dormant or
pending memory becomes relevant given the current context.
It is not query-driven — it runs continuously against the
active context stream and identifies connections between what
is happening now and what Zola knows.

### What the Engine Does

The engine maintains an attention index — a lightweight
representation of current context: active topic, active
entities, current environment, current emotional register,
active project, and current open loops. Against this index,
it continuously evaluates whether stored memories have
become newly relevant.

A memory becomes a resurfacing candidate when:

- Its subject entity is active in the current context
- Its topic domain matches the current conversation area
- It connects to an active open loop
- It relates to a currently active project
- Its content is directly relevant to something the user
  just said or is working on
- It represents a pattern that the current moment fits or
  violates

### Resurfacing Candidate Evaluation

Not every resurfacing candidate produces output. The candidate
is evaluated by the Memory Use Governor before any output
is considered. The governor assigns a usage mode (see below)
and routes the candidate through the privacy gate and the
Attention/Relevance Engine before anything reaches the user.

The engine does not speak. It identifies candidates and hands
them to the governor. This is the boundary that prevents the
resurfacing engine from becoming an interruption machine.

### Connection Types

The resurfacing engine identifies connection types to inform
how a memory might be used:

**Direct relevance** — the memory is about the exact topic
currently being discussed

**Causal connection** — the memory may explain or be explained
by the current situation

**Pattern match** — the current moment fits a pattern Zola
has in memory

**Pattern violation** — the current moment breaks a pattern
Zola has in memory

**Open loop connection** — the current context relates to an
active unresolved loop

**Emotional echo** — the current emotional register matches
a previously observed situation

---

## Memory Use Governor

The Memory Use Governor is the final gate between what Zola
knows and what she does with it. No memory-backed behavior
— spoken, displayed, behavioral, tonal — bypasses the governor.

The governor assigns a usage mode to every memory that the
resurfacing engine or a direct query surfaces as a candidate.

### Usage Modes

**`USE_SILENTLY_FOR_CONTEXT`**
The memory informs Zola's understanding of the current moment
but produces no output. Zola knows. She does not say. This
is the most frequent usage mode for sensitive, private, or
marginally relevant memories.

**`USE_TO_PERSONALIZE_TONE`**
The memory shapes how Zola speaks — her register, warmth,
formality, pacing — without being explicitly referenced.
The memory is felt, not cited.

**`USE_TO_DISAMBIGUATE`**
The memory resolves an ambiguity in the current conversation.
Zola uses it to understand correctly, and may reference it
briefly to confirm understanding.

**`USE_TO_SUGGEST`**
The memory supports a suggestion or observation Zola offers.
The memory is the basis for the suggestion but does not need
to be cited explicitly.

**`USE_ONLY_IF_ASKED_DIRECTLY`**
The memory is relevant but should not be volunteered. If the
user asks a question that directly calls for this memory,
it may be used. It does not surface proactively.

**`USE_ONLY_AFTER_CONFIRMATION`**
The memory requires explicit in-session user confirmation
before it influences output. This corresponds to
`EXPLICIT_CONFIRMATION_REQUIRED` visibility scope.

**`NEVER_USE_PROACTIVELY`**
The memory may be used if directly queried by the user.
It never surfaces in any proactive, autonomous, or
ambient output.

**`NEVER_SPEAK_ALOUD`**
The memory may never be produced as audio output under
any circumstances. It may appear in private screen display
only, under appropriate conditions.

**`SUPPRESS`**
The memory is blocked from all output by the privacy gate,
the topic avoidance tracker, or trust recovery suppression.

### Governor Decision Factors

The governor evaluates:

- Visibility scope of the memory
- Sacred class membership
- Third-party presence
- Output channel and mode
- Vault session status
- Topic avoidance history
- Trust recovery suppression
- Emotional confidence flag (is this an interpreted state?)
- Memory age and asymmetry threshold
- Context contamination risk
- Contextual relevance strength

When the governor is uncertain, it defaults to
`USE_SILENTLY_FOR_CONTEXT`. The system fails toward silence,
not toward disclosure.

---

## Recall Pipeline

When a memory is explicitly queried by the user or contextually
triggered by the resurfacing engine, the recall pipeline
governs how it is retrieved and prepared for use.

### Pipeline Stages

**Stage 1 — Query / Context**
The recall request arrives — either a user query that implies
a memory retrieval, or a resurfacing candidate from the engine.

**Stage 2 — Intent Understanding**
What is the user actually asking, or what is the resurfacing
connection? Surface-level queries may have deeper intent.
"How did that go?" requires understanding what "that" refers
to. Intent understanding resolves the recall target.

**Stage 3 — Entity Resolution**
Which entity is the subject of this recall? The entity is
resolved against the world graph. Ambiguous subjects are
clarified before retrieval.

**Stage 4 — Candidate Retrieval**
The memory system retrieves all candidates relevant to the
resolved entity and intent. Candidates are retrieved from
the appropriate storage layers — world graph for durable
facts, episodic store for time-bounded events, open loop
tracker for unresolved items, context memory for session
state.

**Stage 5 — Authority Ranking**
Competing candidates are ranked by authority tier. User-stated
beats user-confirmed beats system-inferred beats perception-
derived. Within the same tier, recency and reinforcement
count are the tiebreakers.

**Stage 6 — Freshness Check**
Candidates are evaluated for freshness. The age multiplier
and current confidence score from the World Fact Lifecycle
are applied. Stale facts are flagged and will require hedging
language if used.

**Stage 7 — Privacy Gate**
Every candidate passes through the Response Privacy Filter
from the Memory Ethics and Privacy Layer. Candidates blocked
by the filter are removed from the recall set. The remaining
candidates are what Zola is permitted to use.

**Stage 8 — Context Fit Check**
Among the permitted candidates, which are actually relevant
to the current conversational context? A fact may be accurate,
authorized, and fresh but not relevant to what is being asked
right now. Context fit reduces the candidate set to what
is genuinely useful.

**Stage 9 — Response Contract**
The remaining candidates are assembled into a response
contract: what Zola will say, how she will say it (hedging
language if needed), what she will withhold, and whether
she will ask a follow-up. The response contract is handed
to the output layer for execution.

### Recall Conflict Resolution

When competing memories conflict:

- User correction wins over all other sources
- Newer confirmed facts beat older facts of the same type
- Perception never beats user-stated truth
- Inferred facts are downgraded when contradicted
- Stale facts require hedging language rather than assertion

Example of correct conflict handling in output:

> "Last I knew, Double R had the KA setup, but that may have
> changed — is that still the case?"

Not:

> "Double R has the KA setup."

The hedged form is correct when the underlying fact is stale
or when a contradicting signal exists.

---

## Memory Lifecycle

Every memory in the belief model moves through a defined
lifecycle. No memory exists outside this lifecycle.

```
CAPTURED
    ↓
PENDING
(candidate written; awaiting Consolidation Loop review)
    ↓
ACTIVE
(written to assigned storage layer; in use)
    ↓
REINFORCED
(confirmed, re-observed, or re-stated; confidence increased)
    ↓
STALE
(drift floor approached; not recently reinforced)
    ↓
CONTRADICTED
(conflicting information received; confidence penalized)
    ↓
ARCHIVED
(below active use threshold; retained as record)
    ↓
FORGOTTEN
(explicit user deletion or lifecycle expiration)
```

Transitions are managed by:
- The Consolidation Loop (CAPTURED → PENDING → ACTIVE)
- The World Fact Lifecycle drift pass (ACTIVE → STALE)
- The Write Pipeline correction path (ACTIVE → CONTRADICTED)
- The memory system's promotion pass (STALE → ARCHIVED)
- Explicit user action (any state → FORGOTTEN)

No memory transitions to FORGOTTEN automatically. Deletion
is always a user-initiated action.

---

## Integration with Existing Architecture

### Environmental Event Bus

The Memory Salience Scorer is an observer on the Environmental
Event Bus. Perception events, conversation events, and state
change events that cross the bus are evaluated for memory
significance in real time. The scorer does not block the bus
— it observes asynchronously and produces salience candidates
that enter the Write Pipeline independently.

### Attention/Relevance Engine

The Memory Use Governor routes all resurfacing candidates
and cognitive engagement proposals through the Attention/
Relevance Engine before any output is produced. The engine
applies its full gate — dampening, suppression, context fit,
urgency — to memory-driven output candidates exactly as it
applies them to all other output candidates. Memory agency
does not bypass the engine's authority.

### Session Lifecycle Manager

The Session Lifecycle Manager fires the `CONSOLIDATION_TRIGGER`
event at session end. It does not execute the Consolidation
Loop — that is the memory system's responsibility. The trigger
is the only dependency between the session lifecycle and the
memory system.

When that trigger fires — including the 30-second same-device
grace period — is defined by
`Zola_Session_Identity_Architecture.md`. This document describes
what happens when the trigger fires, not when it fires.

### Memory Ethics and Privacy Layer

The Response Privacy Filter from the Memory Ethics and Privacy
Layer is the final gate in the Recall Pipeline. The Memory
Use Governor applies the full visibility scope, sacred class,
and privacy context evaluation before any memory-backed output
is produced. These two systems share the same privacy
enforcement model — the governor applies it at assignment time,
the filter applies it at output time.

### Open Loop Tracker → Cognitive Engagement

The Open Loop Tracker feeds the Cognitive Engagement system
directly. Active open loops are the primary source of curiosity
candidates. The engagement system reads the tracker's current
state when evaluating whether a curiosity-driven inquiry is
appropriate.

---

## Phase Sequencing

### Phase 3 — Write Pipeline and Memory Types

- Memory Write Pipeline implemented with all eleven stages
- Memory type taxonomy implemented
- Memory Salience Scorer implemented (initial thresholds)
- Write threshold enforcement active
- Open Loop Tracker implemented
- Basic Consolidation Loop implemented (session-end trigger only)
- Memory lifecycle states implemented
- All memory writes route through the pipeline

### Phase 4 — Consolidation and Resurfacing

- Full Consolidation Loop implemented including nightly pass
- Contextual Resurfacing Engine implemented
- Memory Use Governor implemented with full usage mode taxonomy
- Recall Pipeline fully implemented
- Cognitive tension tracking implemented
- Authority ranking enforced in recall
- Conflict resolution rules active

### Phase 5 — Cognitive Engagement and Full Lifecycle

- Cognitive Engagement system implemented (see companion document)
- World Fact Lifecycle drift pass integrated with Consolidation Loop
- Open loop aging and dormancy implemented
- Trust recovery behavior integrated with the governor
- Full memory lifecycle transitions implemented
- Nightly pass fully operational

---

## Open Questions

**OQ-MA1 — Memory Salience Scorer write threshold calibration**
The initial write threshold of 0.40 is illustrative. Too low
and the belief model fills with low-significance entries. Too
high and genuinely useful memories are discarded. Calibration
required after Phase 3 implementation against real session data.

**OQ-MA2 — Consolidation Loop session summary format**
The session summary written at Consolidation Loop step 6
is described as a semantic summary of the session. The exact
format, length, and content model for this summary is undefined.
Decision required before Phase 3 Consolidation Loop
implementation.

**OQ-MA3 — Open Loop staleness windows by loop type**
Open loops age on a staleness window, but the window varies
by loop type — a promise has a different staleness window
than an abandoned topic or an unresolved question. Initial
values need to be defined and calibrated.

**OQ-MA4 — Cognitive tension threshold for proactive behavior**
When a cognitive tension item's weight reaches the proactive
behavior threshold, it generates a resurfacing candidate
routed through the Attention/Relevance Engine. The tension
weight threshold that qualifies for proactive consideration
is undefined. Too low and every minor unresolved item generates
a candidate. Too high and genuinely significant tension never
surfaces.

---

## Principles That Must Not Be Violated

**MA-P1 — Every memory write passes through the pipeline.**
There is no direct write path that bypasses the eleven-stage
Write Pipeline. No exception for urgency, simplicity, or
implementation convenience.

**MA-P2 — Zola decides what to remember.**
The save decision is internal and evaluated by the Memory
Salience Scorer. The user does not need to say "remember this"
for something to be remembered. The user saying "remember this"
is an authority signal that elevates salience — not the only
path to retention.

**MA-P3 — The Consolidation Loop is the distillation gate.**
Pending candidates are not active memories. They survive only
if the Consolidation Loop promotes them. The loop is the
boundary between noticing and capturing.

**MA-P4 — Notice freely. Capture deliberately.**
The salience scorer observes continuously and scores freely.
The write pipeline captures rarely and deliberately. The gap
between noticing and capturing is what prevents accumulation.

**MA-P5 — Open loops stay open until explicitly closed.**
An unresolved thing is not resolved by being forgotten. Open
loops maintain their state until the user resolves them,
Zola confirms resolution, or the user explicitly abandons
them. They do not auto-close.

**MA-P6 — Memory agency does not bypass the engine.**
All memory-driven output candidates — resurfacing, curiosity,
cognitive tension — route through the Attention/Relevance
Engine. Memory agency provides the motivation. The engine
provides the authorization. These are never collapsed.

**MA-P7 — Conflict resolution favors the user.**
When memories conflict, user-stated and user-confirmed facts
win. Perception, inference, and model-generated facts do not
override what the user has directly asserted.

---

*Memory Agency Architecture — Version 1.0*
*Created at Phase 2 lore entry*
*Companion document:*
*`Zola_Architecture_Cognitive_Engagement.md`*
*Phase 3 implementation begins with Write Pipeline and Memory Types*
