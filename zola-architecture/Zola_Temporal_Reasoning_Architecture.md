# Temporal Reasoning Architecture

### Foundational Architecture for Time-Aware Relational Intelligence

---

## Vision

The Temporal Reasoning Architecture defines how Zola converts the passage
of time into relational meaning — understanding not just when things
happened, but what the passage of time since then signifies.

The goal is not to add timestamps to more things. The goal is to make
elapsed time a first-class signal that shapes how Zola understands
conversations, how she speaks, and when she chooses to surface
something that has been waiting.

Zola already stores when things happened. This layer answers the
question the memory system does not: *what does it mean that this much
time has passed?*

The system should eventually feel less like:

> "an assistant that remembers facts with timestamps"

and more like:

> "a presence that understands the significance of time passing — and
> participates in your life accordingly."

---

## Core Philosophy

### Time Is Meaning, Not Metadata

Traditional assistant systems treat time as storage metadata.
Timestamps exist to sort records or expire caches. They are not
reasoned about — they are managed.

Traditional systems:

- store timestamps for housekeeping purposes
- treat all memories as equally relevant regardless of age
- surface topics without considering when they were last active
- have no concept of a thread going quiet

This system treats time as a reasoning signal:

- elapsed time since a topic was last touched changes what that
  topic means
- a plan mentioned three weeks ago and never revisited is
  categorically different from one mentioned yesterday
- the gap between sessions is itself information
- some things become more significant the longer they go unresolved

### A Reasoning Lens, Not a Storage Layer

Temporal Reasoning does not own any memory. It does not store facts,
manage decay, or promote candidates. Those responsibilities belong
to the Memory Hierarchy Architecture and the Consolidation Loop.

Temporal Reasoning is a reasoning lens placed on top of existing
memory and conversational state. It reads what is already stored,
interprets what elapsed time means in context, and produces two
outputs:

- **Temporal context signals** — enrichment that flows into prompt
  assembly so Zola speaks with natural time awareness
- **Initiative candidates** — time-based surfacing proposals that
  enter the existing initiative queue when a thread has aged to the
  point where returning to it is appropriate

### How a Person Uses Time

Zola's temporal reasoning should mirror how a perceptive person
naturally relates to time in a close working relationship.

A trusted colleague does not need to be told that three weeks have
passed since a topic was discussed. They notice. They factor it in.
When the moment is right, they bring it back — not mechanically, but
because the elapsed time itself made it worth raising again.

Zola should do the same. When elapsed time is relevant to a response,
she uses it naturally. When it is not relevant, it stays silent. Time
is always present in her understanding — it surfaces only when it
adds something.

---

## Non-Goals

Temporal Reasoning is not:

- a memory system — it does not store, promote, or decay facts
- a replacement for the Memory Hierarchy Architecture
- a scheduler or cron mechanism — it does not queue time-delayed
  actions for future delivery
- a notification system — it does not alert the user to elapsed time
  as an event in itself
- a second proactive delivery path — all initiative candidates it
  produces enter the existing initiative queue through the existing
  intake contract
- a session boundary manager — it reads session boundaries; it does
  not define or write them
- an emotional reasoning system — emotional significance is owned
  by the emotional signal pipeline; temporal reasoning observes
  elapsed time only

---

## Architectural Position

Temporal Reasoning sits between existing memory stores and two
downstream consumers: the prompt assembly layer and the initiative
queue.

It observes:

- open loop entries and their lifecycle timestamps
- session summary boundaries
- conversational state recency
- episodic memory timestamps and retrieval rankings
- topic heat and last-touched signals

It produces:

- a temporal context block injected into `SessionBriefBuilder`
- per-topic elapsed-time labels available to `MemoryInjectionBuilder`
- initiative candidates enqueued via `TemporalInitiativeSource` into
  `InitiativeQueue`

It never:

- writes to Firestore directly
- modifies memory entries
- bypasses the initiative queue to deliver speech
- invokes `ResponseExecutionService` or `GeminiLiveClient` directly
- makes routing or authority decisions

---

## Clock Authority

All temporal computations in this layer use a single clock policy:
`System.currentTimeMillis()` returning UTC epoch milliseconds.

This is consistent with the existing timestamp standard confirmed
across `OpenLoop`, `EpisodicMemoryEntry`, `SessionSummary`, and
`ConversationState`. No alternative clock mechanism is introduced.

All elapsed-time computations produce a `Long` delta in milliseconds.
Natural-language formatting of elapsed time is delegated exclusively
to `TemporalRecencyFormatter` — no formatting logic lives inside
Temporal Reasoning classes.

---

## Session Boundary Resolution

Temporal Reasoning requires a reliable answer to the question:
*when did the previous session end?*

This is resolved through a dedicated `SessionBoundaryResolver`
interface rather than direct field access. This isolates the fallback
logic in one place and allows the resolution strategy to evolve
independently of the Temporal Reasoning layer.

### Resolution Order

1. `SessionSummary.endedAtMs` from the latest session summary
   retrieved via `FirestoreSessionSummaryRepository` — preferred
   source; written by `ConsolidationLoop` on session end
2. `ConversationState.updatedAt` via
   `ConversationContextManager.getConversationRecency` — fallback
   source; always present but lower fidelity

### Known Constraint — Short Session Amnesia

Sessions under `MIN_INACTIVITY_FLUSH_TURNS` (currently 3 turns) do
not produce a `SessionSummary`. For users with frequent brief
interactions, the system will regularly fall back to
`ConversationState.updatedAt`. This produces correct but lower-
fidelity inter-session elapsed time on those sessions.

A dedicated `lastSessionBoundaryMs` field written at every session
open would resolve this gap. This is explicitly deferred to a future
design pass. `SessionBoundaryResolver` is designed to accommodate
this addition as a swap of its resolution logic, not a refactor of
its callers.

---

## Long-Term Architectural Pillars

---

## 1. SessionBoundaryResolver

### Purpose

Provide a single authoritative answer to "when did the previous
session end?" so that no Temporal Reasoning component implements
fallback logic independently.

### Responsibilities

- resolve the last session boundary timestamp using the ordered
  fallback chain
- return a `Long` epoch millisecond value or null if no boundary
  can be resolved
- abstract the fallback chain from all callers; callers receive
  a timestamp, not a source
- log the resolution source at DEBUG level for observability
- on cold start, if both resolution sources require a blocking
  network fetch, return null immediately rather than holding up
  prompt assembly — callers must treat null as "elapsed time
  unknown" and suppress any output that depends on the
  inter-session gap; resolution must never block the session
  initiation pipeline

### Resolution Interface

```
SessionBoundaryResolver.resolveLastBoundaryMs(userId: String): Long?
```

Returns the timestamp of the end of the most recent prior session,
or null if no boundary can be established. Null callers must treat
the elapsed time as unknown and suppress any output that depends on
inter-session gap.

### Important Principle

No component outside `SessionBoundaryResolver` implements inter-
session boundary fallback logic. If the resolution strategy needs
to change, it changes in one place.

---

## 2. ThreadArcClassifier

### Purpose

Read open loop entries and classify each active thread by its
current temporal arc — describing not just how old it is, but
what the elapsed time means about its state.

### Responsibilities

- read active open loop entries from `OpenLoopTracker.listForResurfacing`
  targeting path `users/{userId}/memory/pending` with
  `recordType: open_loop`
- compute elapsed time since `createdAtMs` and `updatedAtMs` for
  each entry
- assign a `ThreadArc` classification to each entry
- produce a ranked list of `ClassifiedThread` objects for downstream
  consumers
- never modify open loop entries; classification is read-only

### Thread Arc Classifications

**FRESH**
Created or touched within the last 24 hours. Fully active.
No temporal signal worth surfacing — the thread is current —
unless overridden by explicit user-requested deferral metadata
on the loop entry.

**ACTIVE**
Touched within the last 7 days. Normal working state.
No resurfacing signal generated. Thread appears in temporal
context as currently in progress — unless overridden by explicit
user-requested deferral metadata on the loop entry.

**AGING**
Not touched in 7–21 days. The thread is still alive but
beginning to drift. Eligible for low-urgency prompt context
enrichment. Not yet a resurfacing candidate.

**QUIET**
Not touched in 21–60 days. Meaningful silence. The thread
may have resolved without being explicitly closed, or may be
genuinely unaddressed. Eligible for resurfacing candidate
generation at appropriate timing.

**OVERDUE**
Not touched in more than 60 days and still marked open.
High temporal significance. Strong resurfacing candidate
unless the topic is one the user has repeatedly declined
to engage with.

**DORMANT**
Classified as DORMANT by `OpenLoopTracker` — the loop's
own staleness model has already transitioned it. Temporal
Reasoning respects this classification and does not generate
resurfacing candidates for DORMANT threads without a new
triggering signal.

### Important Principle

Arc classifications are derived from elapsed time and existing
loop state. They are computed signals, not stored fields.
`ThreadArcClassifier` never writes to any store.

---

## 3. TemporalContextAssembler

### Purpose

Produce the temporal context block injected into prompt assembly
at session start, so that Zola enters every session with natural
awareness of how much time has passed and what threads are
currently in what state.

### Responsibilities

- invoke `SessionBoundaryResolver` to establish the inter-session
  gap
- invoke `ThreadArcClassifier` to classify active open threads
- invoke `TemporalRecencyFormatter` to produce natural-language
  elapsed-time labels
- assemble a structured `TemporalContextBlock` containing:
  - inter-session gap label ("it has been about three days since
    we last spoke")
  - currently FRESH and ACTIVE threads by name
  - AGING threads flagged as drifting
  - count of QUIET and OVERDUE threads (not enumerated inline;
    detail surfaced by initiative candidates separately)
- deliver the block to `SessionBriefBuilder` for injection into
  the `[TEMPORAL]` section
- run at session start; result is valid for the duration of the
  session

### Output Contract

`TemporalContextBlock` is a value object. It is computed once at
session start and treated as immutable for the session. It is not
re-computed mid-session.

### Important Principle

`TemporalContextAssembler` produces context for Zola's awareness.
It does not decide what Zola says or when she says it. Prompt
injection shapes tone and reference — it does not issue directives.

---

## 4. TemporalInitiativeSource

### Purpose

Produce initiative candidates for threads whose elapsed time has
crossed a resurfacing threshold, and deliver them into the existing
initiative queue through the standard intake contract.

### Responsibilities

- read `ClassifiedThread` lists from `ThreadArcClassifier`
- filter for threads classified QUIET or OVERDUE that have not been
  recently surfaced
- apply cross-session deduplication via Firestore query on
  `relevanceTopics` / `entityId` before enqueuing — session-local
  dedup is insufficient
- construct a valid `InitiativeItem` for each eligible thread using
  the confirmed field contract from `InitiativeItem.kt`
- set urgency scores within the initiative queue's tier thresholds:
  - QUIET threads: low-pressure tier (0.2–0.35)
  - OVERDUE threads: moderate tier (0.4–0.55)
  - never above 0.55 — temporal resurfacing is never urgent in the
    alarm sense
- enqueue via `InitiativeQueue.enqueue` — no other delivery path
- run at session start after `TemporalContextAssembler` completes,
  and as a consolidation step after nightly consolidation

### Enqueue Preconditions

A thread is eligible for a `TemporalInitiativeSource` candidate only
when all of the following are true:

- arc classification is QUIET or OVERDUE
- the thread has not been surfaced in the current session
- no existing initiative item for this thread is present in the queue
  (cross-session dedup via Firestore query)
- the elapsed time since `updatedAtMs` meets the arc threshold at
  the time of evaluation — not pre-scheduled, not speculative

### Important Principle

`TemporalInitiativeSource` enqueues only when a threshold is already
met. It does not schedule future candidates or use delayed delivery
mechanisms. Timing decisions after enqueue belong to
`InitiativeQueueEvaluator`.

---

## 5. Initiative Queue Temporal Gate

### Purpose

Ensure that temporal initiative candidates are not delivered too
frequently for the same thread, and that delivery is not attempted
before a meaningful elapsed-time gap since last surfacing.

### Responsibilities

This is not a new component. It is an extension to the existing
`InitiativeQueueEvaluator`.

`InitiativeQueueEvaluator.evaluate` must be extended to apply a
temporal eligibility check before topic relevance filtering:

- read `lastSurfacedAt` on the candidate's associated entity or
  topic (available via `CognitiveHydrationService` Step 4 which
  already tracks `lastSurfacedAt` per entity)
- read `updatedAtMs` from the originating open loop entry
- reject candidates where the elapsed time since last surfacing
  is below the minimum cooldown for the candidate's urgency tier:
  - low-pressure tier (0.2–0.35): minimum 72 hours between
    surfacings of the same thread
  - moderate tier (0.4–0.55): minimum 48 hours between surfacings

This gate applies to all initiative candidates, not only temporal
ones. Temporal candidates benefit from it without requiring special
handling.

### Important Principle

Cooldown enforcement lives in the evaluator, not the producer.
`TemporalInitiativeSource` does not need to know whether it is
"too soon" — the evaluator provides that gate centrally for all
initiative types.

---

## Integration Points

---

### Ingestion — What Temporal Reasoning Reads

| Source | Class / Method | Data consumed |
|---|---|---|
| Open loop store | `OpenLoopTracker.listForResurfacing` | `createdAtMs`, `updatedAtMs`, `resolvedAt`, arc state |
| Session boundary | `SessionBoundaryResolver` (new) | `SessionSummary.endedAtMs` → `ConversationState.updatedAt` fallback |
| Episodic memory | `EpisodicMemoryRetriever` + `EpisodicMemoryEntry.timestampMs` | Timestamp and recency rank |
| Conversational recency | `ConversationContextManager.getConversationRecency` | Fallback inter-session signal |
| Cognitive hydration | `CognitiveHydrationService.hydratedGapScores` | `lastSurfacedAt` per entity |

---

### Generation — What Temporal Reasoning Produces for Prompts

| Destination | Class / Method | What is injected |
|---|---|---|
| Session brief | `SessionBriefBuilder.assemble` — new `[TEMPORAL]` bracket section | Inter-session gap label, thread arc summary |
| Memory block | `MemoryInjectionBuilder.renderMemoryBlock` — recency sentence | Per-topic elapsed-time label for AGING+ threads |
| Proactive context | `ProactiveMemoryContext.buildTimeContext` | Time label for proactive hint enrichment |

---

### Action — What Temporal Reasoning Enqueues

| Destination | Class / Method | What is enqueued |
|---|---|---|
| Initiative queue | `InitiativeQueue.enqueue` via `TemporalInitiativeSource` | QUIET and OVERDUE thread candidates |
| Evaluator gate | `InitiativeQueueEvaluator.evaluate` — extended | Temporal cooldown check on all candidates |

---

### Consolidation Hook

`ConsolidationLoop` step 4b (`OpenLoopTracker.incrementAge`) is the
natural hook point for `TemporalInitiativeSource` to run after
nightly consolidation. No formal extension interface exists on
`ConsolidationLoop` today. The hook is implemented as a sequential
call added after step 4b in the nightly consolidation path, clearly
commented and scoped.

---

## Known Constraints and Deferred Work

### Short Session Amnesia

Sessions under `MIN_INACTIVITY_FLUSH_TURNS` do not produce a
`SessionSummary`. `SessionBoundaryResolver` falls back to
`ConversationState.updatedAt` in these cases. This is accepted
behavior for version 1. A dedicated `lastSessionBoundaryMs` field
is the future resolution path and can be added without changing
`SessionBoundaryResolver` callers.

### Resolved Topic Cadence Tracking

Open loops are closed when a topic resolves. Once closed, there
is no temporal cadence tracking for that topic — Zola cannot
determine how frequently a now-resolved topic was historically
revisited or whether it tends to recur.

This is a known architectural constraint. If tracking the return
frequency of resolved topics becomes necessary, a topic→timestamp
index will be required. That index is explicitly out of scope for
this architecture version. The constraint should not be worked
around by keeping loops artificially open.

### No Seasonal Reasoning

Annual and seasonal time scale reasoning — behavioral shifts across
months, seasonal rhythms in work patterns — is explicitly deferred.
The arc classifications defined here operate on a days-to-months
scale. Seasonal reasoning requires a longer observation window and
a separate design pass.

### Clock Fragmentation Risk

Approximately 150 call sites across the codebase use independent
timestamp mechanisms. Temporal Reasoning uses `System.currentTimeMillis()`
consistently, matching the standard used by `TemporalRecencyFormatter`
and `EpisodicMemoryRanker`. A future clock consolidation pass —
introducing an injectable `Clock` abstraction — would improve
testability and eliminate drift risk across all components. This is
noted as future engineering hygiene, not a prerequisite for this layer.

---

## Authority Boundaries

### Temporal Reasoning may:

- read from any memory store, open loop store, or session boundary
  source
- classify threads by temporal arc
- produce temporal context blocks for prompt injection
- enqueue initiative candidates via the standard intake contract
- invoke `TemporalRecencyFormatter` for natural-language output

### Temporal Reasoning must not:

- write to any Firestore collection or memory store
- modify open loop entries, episodic entries, or session summaries
- invoke `ResponseExecutionService`, `GeminiLiveClient`, or any
  speech execution class
- deliver speech directly — all output goes through the initiative
  queue or prompt injection
- make routing or truth-ownership decisions
- bypass `InitiativeQueueEvaluator` for any candidate

### Important Principle

Temporal Reasoning observes and enriches. It does not commit,
execute, or speak. Every output it produces is consumed by a
system that retains full authority over whether and how to act
on it.

---

## Relationship to Relational Intelligence Layer

Temporal Reasoning is the first implemented subsystem of the Zola
Relational Intelligence Layer — the broader architecture that gives
Zola a genuine model of her relationship with the user over time.

The five subsystems of the Relational Intelligence Layer are:

1. **Temporal Reasoning** — time as meaning, not metadata *(this document)*
2. **Self-Model Awareness** — Zola's model of the confidence and age
   of her own beliefs about the user
3. **Social Graph Reasoning** — dynamic models of the people in the
   user's life
4. **Relational Continuity** — the arc of the relationship between
   Zola and the user
5. **Relational Calibration** — earned familiarity that deepens
   naturally over time

Temporal Reasoning is foundational to the other four. Self-model
awareness requires knowing when beliefs were formed and last
confirmed. Relational continuity requires reasoning about the arc
of a relationship across time. Relational calibration requires
knowing how long the relationship has been active. Social graph
reasoning requires distinguishing recent interactions from distant
ones.

The architecture for each remaining subsystem will reference
Temporal Reasoning as a dependency. The components defined here —
particularly `SessionBoundaryResolver`, `ThreadArcClassifier`, and
`TemporalRecencyFormatter` — are shared infrastructure for the
entire Relational Intelligence Layer.

---

## Long-Term End State

Temporal Reasoning eventually supports:

- natural time reference in all Zola speech without explicit
  instruction
- arc-aware open thread management that surfaces the right things
  at the right moments
- session resumption that always feels like returning to a
  continuous conversation, not starting over
- behavioral pattern recognition across weeks and months as inputs
  to higher Relational Intelligence subsystems
- a presence that understands not just what you've been through,
  but when — and what that timing means

The system should ultimately feel:

- naturally time-aware without announcing it
- perceptive about what has gone quiet and what is overdue
- restrained in surfacing — timing is as important as content
- continuous across sessions rather than episodic and amnesiac

without becoming:

- an alarm system that counts down to topics
- a nag that surfaces unresolved items on a schedule
- a system that treats all elapsed time as urgency
- a logger that annotates every response with timestamps

---

## Final Principle

Time passing is not a problem to manage. It is information to
understand.

Zola should know that three weeks of silence on a topic means
something — and she should be the kind of presence that knows
when, and how, to acknowledge it.
