# Zola Cognitive Engine Architecture
### Independent Thinking, Pre-Computation, and Session Readiness

Version: 0.2 (Pre-Audit — Decisions Locked, Audit Pending)
Created: 2026-06-15
Status: DECISIONS LOCKED — audit prompt ready to be written

This document captures the architectural intent and design decisions
governing Zola's cognitive engine activation, pre-computation offload
strategy, and initiative queue system. All open questions are resolved.
No Cursor prompts are written until this document is committed to
`zola-architecture/` on `zola-main`.

---

## Governing Principle — The Prep Kitchen Model

Zola's cognitive engines — curiosity, pattern investigation, and world
model building — exist to give her genuine independent thinking. They
were built in Phase 5 and have remained unwired since. This phase
activates them.

The governing principle for how they operate is the prep kitchen model.

A shop that starts every customer interaction by going to find their
file, check their history, and look up open work orders is a slow shop.
A good shop does that work before the customer arrives. When they walk
in, everything is already ready.

Zola follows the same model. Expensive cognitive work — scanning the
entity graph, detecting patterns across conversation history, scoring
world model gaps — does not happen during a live session. It happens
between sessions, overnight, during idle time, when nobody is waiting
on it. By the time the user speaks, the results are already in the
initiative queue. Zola knows what she wants to raise before the first
word is said.

The live session is the serving window. The background jobs are the
prep kitchen. Nothing leaves the serving window until it is already
prepared.

Every architectural decision in this document must be evaluated against
this principle.

---

## CEA-D01 — The three cognitive engines are activated this phase

**Decision:** `CuriosityInquiryEngine`, `PatternInvestigationEngine`,
and `WorldModelBuildingEngine` are instantiated and wired into the
live session for the first time. These engines were built in Phase 5
and have remained uninstantiated dead code since. This phase connects
them to the initiative queue and the delivery path.

**What this means:** Zola will, for the first time, produce unprompted
cognitive output that originates from genuine gaps in her world model,
observed patterns across conversations, and active knowledge targets —
not from timers, event buses, or synthetic placeholders.

**What this means going forward:** All three engines are first-class
participants in session behavior. Their output routes through the
`EngagementGovernor` and `AttentionRelevanceEngine` before reaching
the delivery coordinator. Neither gate is bypassed. The authority model
is unchanged — engines propose, the core decides.

---

## CEA-D02 — Cognitive work runs between sessions, not during them

**Decision:** The three cognitive engines do not perform expensive
analysis during a live session. World model gap scoring, pattern
detection across conversation history, and entity relevance ranking
are all pre-computed by background jobs that run between sessions.
The engines read pre-computed results at session start. They do not
compute them live.

**What this means:** A dedicated `CognitivePrepWorker` runs after
`NightlyConsolidationWorker` completes. It executes three analysis
jobs in sequence — gap scoring, pattern detection, world model target
identification — and writes results to Firestore. These results are
what the engines read at session start.

**What this means going forward:** Any future cognitive analysis that
is expensive relative to session startup time belongs in
`CognitivePrepWorker`, not in the live session path. The session path
is for reading and acting on pre-computed results, not for producing
them. This is the architectural boundary that keeps session startup
fast as the cognitive system grows.

---

## CEA-D03 — CognitivePrepWorker is a separate named worker, not a step inside NightlyConsolidationWorker

**Decision:** The nightly cognitive pre-computation runs as a separate
`CognitivePrepWorker`, chained to run after `NightlyConsolidationWorker`
completes. It is not added as a step inside the consolidation worker.

**What this means:** Consolidation has a defined responsibility —
processing the prior session's cognitive output into durable memory.
Pre-computation has a different responsibility — preparing the next
session's cognitive input. These are separate concerns and belong in
separate workers. Consolidation completing is the trigger for
pre-computation beginning, not the host for it.

**What this means going forward:** `CognitivePrepWorker` is independently
testable, independently schedulable, and independently extensible. When
new pre-computation jobs are added in future phases, they are added to
`CognitivePrepWorker` without touching consolidation.

---

## CEA-D04 — The initiative queue is a durable, persisted structure

**Decision:** The initiative queue is not a session-local in-memory
list. It is a durable structure that persists to Firestore between
sessions. Candidates that were not surfaced in one session survive to
the next. The queue is hydrated at session start from both the persisted
Firestore state and the latest pre-computed results from
`CognitivePrepWorker`.

Each candidate is stored as its own document in a subcollection
(`initiativeQueue/candidates/{candidateId}`) rather than as an element
in a shared array. All writes to individual candidates use `set(merge)`
rather than wholesale document replacement. This means aging a candidate,
marking it surfaced, or adding a new candidate are all atomic operations
that do not touch other candidates in the queue.

**What this means:** Zola does not lose what she wanted to raise just
because a session ended before the right moment arrived. An unraised
curiosity question about an entity ages into the next session with
increased priority. Zola's agenda carries forward. Because each candidate
is an independent document, concurrent writes from background workers
and session close operations cannot overwrite each other.

**What this means going forward:** The initiative queue has a defined
lifecycle — candidates are created by pre-computation jobs, held in the
queue, surfaced when conditions are right, and either resolved or aged
into the next session. There is no silent discard. A candidate is
removed from the queue only when it has been surfaced, when it has been
superseded by a newer candidate about the same entity, or when it has
aged past a defined maximum. The subcollection model is the permanent
shape of this queue — no future phase converts it back to an array.

---

## CEA-D05 — Initiative queue hydration sequence at session start

**Decision:** At session start, the initiative queue is populated in
the following sequence before the user speaks:

Step 1 — Load the persisted queue from Firestore. Candidates from
prior sessions that were not surfaced are restored with their age
and priority intact.

Step 2 — Read `CognitivePrepWorker` output from Firestore. Load
pre-computed gap candidates, pattern candidates, and world model
build targets.

Step 3 — Merge and deduplicate. If a pre-computed candidate duplicates
a persisted candidate, the higher-priority version is retained.

Step 4 — Rank. Apply category weights and age adjustments. Time-sensitive
items rank above open loops. Open loops rank above curiosity gaps. Within
each category, age increases priority.

Step 5 — Apply governor frequency limits at read time. Candidates that
would violate session frequency limits are held but not promoted to the
active delivery window.

**What this means:** By the time the user speaks, the queue is fully
populated and ranked. No analysis happens after the first word.

**What this means going forward:** The hydration sequence is the
authoritative entry point for all initiative candidates. No engine
adds candidates to the queue at any other point during a live session.
Engines read the pre-computed output; they do not produce new
candidates mid-session.

---

## CEA-D06 — Curiosity level is derived from world model density, not configured manually

**Decision:** The `CuriosityInquiryEngine` does not have a curiosity
level parameter that is set manually. Its curiosity level is derived
from the density score produced by `CognitivePrepWorker`'s gap scoring
job. A sparse entity graph produces a high curiosity level. A mature,
well-populated entity graph produces a lower one.

**What this means:** Curiosity calibrates itself automatically as the
world model fills in. Early sessions will naturally produce more
curiosity-driven inquiry because the entity graph is genuinely sparse.
As Zola learns more, she asks fewer questions and shifts toward
commentary, pattern observation, and connection-making.

**What this means going forward:** The density score is a computed
value written by `CognitivePrepWorker` to Firestore and read at session
start. It is not recalculated mid-session. The curiosity level for any
given session is fixed at hydration time. Adjusting curiosity behavior
means improving the gap scoring algorithm in `CognitivePrepWorker`,
not adding a dial to the engine.

---

## CEA-D07 — All three engines route through the existing authority chain

**Decision:** `CuriosityInquiryEngine`, `PatternInvestigationEngine`,
and `WorldModelBuildingEngine` do not deliver output directly. Every
candidate they promote from the initiative queue passes through the
`EngagementGovernor` and then the `AttentionRelevanceEngine` before
reaching `ProactiveDeliveryCoordinator`. Both gates must authorize.
Neither is bypassed.

**What this means:** The existing frequency limits, timing gates,
social fit evaluation, trust state checks, and room-reading gates
all apply to cognitive engine output. The engines do not have
elevated authority. They propose. The authority chain decides.

**What this means going forward:** Adding a new cognitive engine in
a future phase does not require new gate infrastructure. The authority
chain is already in place. Any new engine routes through it.

---

## CEA-D08 — Engines activate sequentially across tracks, not simultaneously

**Decision:** The three engines are activated one at a time across
sequential build tracks. `CuriosityInquiryEngine` is activated first.
After it is verified to behave correctly under real conditions,
`PatternInvestigationEngine` is activated. After that is verified,
`WorldModelBuildingEngine` is activated.

**What this means:** We do not activate all three engines in the same
track and hope the combined behavior is correct. Each engine produces
a new class of unprompted Zola behavior that has never been live before.
Each one needs to be verified independently before the next is added.

**What this means going forward:** If an engine produces unexpected
behavior in production, the cause is unambiguous — it is the most
recently activated engine. Sequential activation makes debugging
tractable and prevents compounded failure modes.

---

## CEA-D09 — The synthetic fallback in ProactiveDeliveryCoordinator is retired

**Decision:** The synthetic `ProactiveTriggerCandidate` currently used
as a fallback when the delivery queue is empty is retired in this phase.
When the queue is empty, the coordinator returns an explicit hold result.
It does not synthesize a candidate to fill the gap.

**What this means:** This was already identified as a flag in Phase 21
(P21-T1). The real initiative queue, now populated with genuine
candidates from pre-computation, replaces the synthetic path entirely.
An empty queue means Zola has nothing to raise — which is a valid and
correct state.

**What this means going forward:** The delivery coordinator is a
delivery mechanism, not a content generator. It must not produce
output when it has no real content to deliver. The synthetic fallback
violated this boundary. Its retirement closes the violation.

---

## CEA-D10 — Context pre-assembly begins at app resume, before the user speaks

**Decision:** At app resume — before any user speech is detected — the
context pre-assembler begins warming memory and assembling the context
injection package. The initiative queue hydration sequence runs
concurrently. By the time the user speaks, both the context injection
package and the initiative queue are ready.

**What this means:** Session startup latency is hidden behind the
natural gap between the user picking up the device and speaking their
first word. Zola is fully loaded before she needs to respond.

**What this means going forward:** Any future session startup work
that can begin before the first word should be added to the pre-assembly
sequence, not to the response path. The response path should read
pre-assembled state, not produce it.

---

## Firestore Paths

All paths sit within the existing `state/` group under the current
user hierarchy. No new top-level groups are introduced.

```
users/{userId}/state/initiativeQueue
    hydratedAt       — timestamp of last hydration
    sessionId        — session that last wrote this document

users/{userId}/state/initiativeQueue/candidates/{candidateId}
    candidateId      — stable unique ID for this candidate
    category         — CURIOSITY_GAP | PATTERN | WORLD_MODEL_TARGET | OPEN_LOOP
    entityId         — entity this candidate concerns (if applicable)
    priority         — float; computed at hydration time
    ageSessionCount  — number of sessions this candidate has survived unraised
    createdAt        — timestamp
    lastEvaluatedAt  — timestamp of last governor evaluation
    status           — PENDING | HELD | SURFACED | SUPERSEDED | EXPIRED

users/{userId}/state/worldModelGapScore
    densityScore     — float; drives curiosity level
    rankedGaps       — array of scored gap candidates
    computedAt       — timestamp

users/{userId}/state/patternCandidates
    candidates       — array of scored pattern candidates
    computedAt       — timestamp

users/{userId}/state/worldModelBuildTargets
    targets          — array of prioritized build target candidates
    computedAt       — timestamp
```

The three pre-computation output documents (`worldModelGapScore`,
`patternCandidates`, `worldModelBuildTargets`) use arrays because they
are written atomically by `CognitivePrepWorker` in a single job run and
read once at hydration time. They are not concurrently written by
multiple sources. Only the initiative queue itself — which is written
by both the session close path and background workers — uses the
subcollection model.

---

## CEA-D11 — Queue hydration at app resume is gated by recency and freshness

**Decision:** The full hydration sequence defined in CEA-D05 does not
run on every app resume. Before executing Steps 2 through 5, two
conditions are checked:

Condition 1 — Recency gate. If the queue was hydrated within the last
5 minutes and no conversation turn occurred in that session, the in-memory
cached queue is reused. Steps 2 through 5 are skipped. Step 1 is also
skipped because the in-memory state is already current.

Condition 2 — Freshness gate. If `CognitivePrepWorker` has not produced
new output since the last hydration — determined by comparing the
`computedAt` timestamps on the three pre-computation Firestore documents
against the queue's `hydratedAt` timestamp — Steps 2 and 3 are skipped.
The persisted queue is loaded but not re-merged with pre-computation
output because there is no new pre-computation output to merge.

Both conditions are evaluated independently. Either condition alone is
sufficient to skip the relevant steps.

**What this means:** Transient resume events — locking and unlocking the
screen, checking a notification, briefly switching apps — do not trigger
unnecessary Firestore reads or re-computation. Battery and Firestore
read costs are incurred only when there is genuinely new state to load.

**What this means going forward:** The 5-minute recency window is an
initial value to be calibrated after real use. If it proves too
conservative — hydration feels stale after a short break — it can be
shortened. If transient resumes are still triggering unnecessary reads,
it can be extended. The freshness gate is permanent and unconditional —
reading pre-computation output that has not changed since the last
hydration is always wasteful regardless of elapsed time.

---

## Track Sequencing

Tracks must execute in order. No track begins until the prior track
is merged and device-verified.

```
T0 — CognitivePrepWorker + pre-computation jobs
  └─► T1 — Initiative queue structure + session hydration
        └─► T2 — CuriosityInquiryEngine live
              └─► T3 — PatternInvestigationEngine live
                    └─► T4 — WorldModelBuildingEngine live
                          └─► T5 — Context pre-assembler
```

T0 and T1 produce no new user-facing behavior. The first unprompted
cognitive output appears in T2. T3 and T4 each add one new engine
to the already-verified delivery path.

---

## Open Questions

None. All decisions are locked. The audit will surface any codebase
conflicts with these decisions before the build plan is written.

---

## Principles That Must Not Be Violated

**CEA-P1 — Engines propose. The authority chain decides.**
No cognitive engine delivers output directly. Every candidate passes
through the `EngagementGovernor` and `AttentionRelevanceEngine`.
Both must authorize. No exception.

**CEA-P2 — Pre-computation belongs between sessions.**
Expensive analysis does not run during a live session. If a new
piece of cognitive work is expensive, it belongs in
`CognitivePrepWorker`, not in the session path.

**CEA-P3 — The queue is the single entry point for initiative candidates.**
Engines do not bypass the queue. The delivery coordinator does not
reach into engine internals. All candidates flow through the queue.

**CEA-P4 — Restraint makes engagement meaningful.**
Frequency limits are not obstacles to work around. They are the
mechanism that makes Zola's unprompted speech feel like genuine
attention rather than noise. They must be respected by every engine.

**CEA-P5 — Sequential activation over parallel activation.**
Engines are activated one at a time and verified before the next
is added. No track activates more than one engine simultaneously.

**CEA-P6 — An empty queue is a valid state.**
Zola having nothing to raise is correct behavior. The system must
not generate synthetic content to fill the absence. Silence is
a valid output.
