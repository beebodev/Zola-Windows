# Streaming Cognition Architecture

### Foundational Architecture for Real-Time Cognitive Preparation

---

## Vision

Streaming Cognition is the architecture layer that allows Zola to reason while a user interaction is still unfolding.

Instead of waiting for a complete prompt, producing a single static answer, and then speaking, Streaming Cognition allows Zola to progressively interpret speech, update working context, track uncertainty, prepare likely responses, detect interruptions, and adapt the final response as new information arrives.

This is not a replacement for the authoritative turn pipeline. It is a real-time cognition layer that feeds structured, provisional signals into the existing authority model without bypassing truth ownership, memory rules, routing authority, or response execution contracts.

The system should eventually feel less like:

> "a system that waits for the user to finish before it starts thinking"

and more like:

> "a presence that is already prepared when the user finishes speaking."

---

## Core Philosophy

### Think Early, Commit Late

Traditional voice systems:

- wait for the complete utterance
- produce a single static interpretation
- begin reasoning only after speech ends
- treat every pause as a turn boundary

This system:

- begins preparing as speech unfolds
- tracks provisional interpretations continuously
- adapts understanding as new speech arrives
- handles corrections, interruptions, and detours as normal conversational events

Streaming Cognition may think early, but it may not commit early.

Partial transcripts, provisional intent guesses, predicted tool needs, draft reasoning paths, emotional cues, and likely response shapes may be generated during a live interaction — but only the final authorized pipeline may commit truth, execute actions, write memory, or produce the final spoken answer.

Streaming Cognition is a preparation layer, not a decision authority.

---

## Non-Goals

Streaming Cognition is not:

- a second QueryProcessor or routing authority
- a replacement for intent routing
- a hidden Live responder
- a memory writer
- a tool executor
- a shortcut around the Authoritative Result Contract
- a reason to let Live improvise facts from provisional drafts
- a reason to commit based on partial transcripts
- a replacement for deterministic finalization

---

## Architectural Position

Streaming Cognition sits between live input capture and final turn execution.

It observes:
- partial speech transcripts
- final transcript segments
- user pauses
- corrections and restarts
- barge-in events
- conversation state
- topic stack state
- attention state
- emotional tone signals
- memory recall candidates
- tool likelihood signals
- autonomous behavior signals

It outputs provisional cognition artifacts to the turn pipeline.

It does not directly:
- speak final answers
- execute tools
- write durable memory
- override routing
- override structured memory truth
- bypass ResponseExecutionService
- bypass the Authoritative Result Contract
- collapse multiple authorities into a blended answer

---

## Long-Term Architectural Pillars

---

## 1. Streaming Cognition Engine

### Purpose

Serve as the central coordinator for all real-time cognitive state during an active user turn. The engine consumes transcript events, maintains streaming turn state, and emits provisional cognition artifacts — without making any final decisions.

### Responsibilities

- consume transcript events as they arrive from STT
- track provisional understanding continuously
- maintain the streaming turn state for the current turn
- track confidence levels across all provisional candidates
- detect topic movement, correction patterns, and interruption patterns
- emit provisional cognition artifacts to the turn pipeline
- reset or finalize streaming state at proper turn boundaries
- operate as a lightweight real-time layer that does not block input responsiveness

### Important Principle

The Streaming Cognition Engine coordinates preparation. It does not produce results. Every output it emits is provisional until the authoritative pipeline promotes it.

---

## 2. Streaming Turn State

### Purpose

Represent the current evolving user turn as a structured, mutable object that accumulates provisional understanding as speech unfolds — and is discarded or archived when the final turn is committed.

### State Contents

- current partial transcript
- finalized transcript segments
- last stable phrase
- current speech activity status
- detected pauses
- detected correction markers
- detected restart markers
- provisional intent candidates
- provisional entity candidates
- provisional memory candidates
- provisional tool candidates
- confidence history
- active topic pointer
- possible return anchor
- interruption state
- cancellation state

### Rules

- Streaming Turn State is temporary and must be cleared or archived when the final turn is committed
- it must not be treated as durable memory
- it must not be exposed to the Live speech component as an independent source of facts

### Important Principle

Streaming Turn State is working memory for the current moment. It has no authority and no persistence beyond the turn boundary.

---

## 3. Provisional Cognition Artifact

### Purpose

Provide the structured output format for all data generated during the streaming phase, explicitly marking all contents as provisional until the authoritative pipeline promotes them.

### Schema

```kotlin
data class ProvisionalCognitionArtifact(
    val turnId: String,
    val partialTranscript: String,
    val stableTranscript: String?,
    val provisionalIntentCandidates: List<IntentCandidate>,
    val provisionalEntityCandidates: List<EntityCandidate>,
    val provisionalMemoryCandidates: List<MemoryCandidate>,
    val provisionalToolCandidates: List<ToolCandidate>,
    val topicMovement: TopicMovementSignal?,
    val interruptionSignal: InterruptionSignal?,
    val correctionSignal: CorrectionSignal?,
    val emotionalToneSignal: EmotionalToneSignal?,
    val confidence: Double,
    val isCommitEligible: Boolean = false
)
```

`isCommitEligible` must remain false until the authoritative turn finalization process explicitly promotes relevant information into the final pipeline artifact. Nothing in the streaming layer may set this to true.

### Important Principle

Every artifact produced by Streaming Cognition is explicitly provisional. The artifact format must make this impossible to misuse — `isCommitEligible` is the hard gate.

---

## 4. Stable Phrase Detector

### Purpose

Identify portions of partial speech that are unlikely to change as the utterance continues, allowing downstream components to begin preparation earlier with reasonable confidence.

### Examples of Stable Phrases

- "Remind me tomorrow…"
- "What was the name of…"
- "Text Micah…"
- "How long would it take to drive to…"

### Rules

- stable phrases may seed provisional candidates
- stable phrases may not execute actions
- stable phrases may not write memory
- stable phrases may not produce final spoken truth
- stable phrases must be superseded by final transcript authority — a phrase that was stable may still change

### Important Principle

Stable does not mean final. The Stable Phrase Detector improves preparation confidence — it does not authorize commitment.

---

## 5. Streaming Intent Forecaster

### Purpose

Predict likely intent categories before the final transcript is complete so that downstream routing paths can be prepared early.

### Possible Intent Predictions

- reminder likely
- calendar likely
- message likely
- memory recall likely
- weather likely
- navigation likely
- tool request likely
- casual conversation likely
- correction likely
- continuation likely

### Rules

- the forecaster improves responsiveness by preparing the correct downstream path early
- it must not replace final intent routing
- final intent authority remains with the established turn pipeline
- forecast results are hints — they are discarded if final routing disagrees

### Important Principle

The Streaming Intent Forecaster prepares paths. It does not choose them.

---

## 6. Streaming Entity Tracker

### Purpose

Identify likely entities while speech is forming so that entity context can be prepared before the final transcript lands.

### Examples

- "Micah"
- "Bre"
- "Bumblebee"
- "Double R"
- "Evergreen Speedway"
- "the 350Z"
- "my wife"
- "my oldest son"

### Rules

- entity candidates may be prepared early
- final entity resolution must still happen through the authoritative Entity Resolution Engine
- the Streaming Entity Tracker must not invent relationships or resolve ambiguous entities by guesswork
- provisional entity candidates are discarded if the final transcript resolves differently

### Important Principle

Entity tracking during streaming improves preparation. It does not authorize resolution. Ambiguous entities must never be resolved by provisional guesswork.

---

## 7. Streaming Topic Tracker

### Purpose

Update the live topic state as the user moves between subjects so that the Conversational Continuity layer has real-time topic movement signals without requiring a completed turn to detect a shift.

### Detectable Events

- topic continuation
- topic shift
- topic detour
- topic return
- nested detour
- abandoned topic
- resumed topic

### Return Anchor Behavior

Return anchors must be modeled as a stack of pointers, not a flat previous-topic field.

Example: Architecture → Git → Branching → SSH Keys

If the user exits SSH Keys, Zola should unwind back to Branching, then Git, then Architecture — in order. Streaming Cognition may observe and signal provisional topic movement, but final topic stack mutation must occur through the authorized Conversational Continuity layer.

### Important Principle

Streaming Cognition observes topic movement. The Conversational Continuity Architecture owns the topic stack. These authorities must not merge.

---

## 8. Interruption and Barge-In Handler

### Purpose

Detect when the user cuts Zola off or changes direction mid-response and classify the interruption type so it can be routed correctly.

### Interruption Types

**Hard interruption** — user wants immediate stop.
Examples: "Stop." / "Quiet." / "Not now."

**Soft interruption** — user wants to pause or slow down.
Examples: "Hold on." / "Wait."

**Correction interruption** — user is correcting a fact or entity.
Examples: "No, not that." / "Actually, make it tomorrow." / "Wait, I meant Micah."

**New-command interruption** — user is redirecting to a different request.
Examples: "Actually, text Bre instead." / "Never mind, check traffic first."

**Clarification interruption** — user wants to revisit part of the response.
Examples: "Wait, explain that part." / "Hold on, what was the second thing?"

### Rules

- stop and cancel requests may interrupt speech immediately
- new commands must create a new turn boundary
- corrections should patch the current turn only when safe and before commitment
- tool execution must not be silently altered after commitment unless the tool supports cancellation or update
- the handler must coordinate with audio playback and the authoritative turn state

### Important Principle

Interruptions are high-value conversational control signals. Every interruption type must be classified and routed deliberately — not treated as noise or a generic stop.

---

## 9. Correction Detector

### Purpose

Identify when the user is revising something they just said so that corrections can be incorporated before final routing rather than after commitment.

### Correction Markers

- "Actually…"
- "No, I mean…"
- "Wait…"
- "Not Micah, Madden."
- "Make that Friday."
- "Scratch that."
- "I meant…"

### Rules

- correction handling should happen before final routing whenever possible
- if a correction happens after commitment, Zola must treat it as a new turn and use normal update and cancel flows
- corrections must not silently alter already-committed tool executions

### Important Principle

A correction before commitment is a streaming event. A correction after commitment is a new turn. The distinction must be enforced precisely.

---

## 10. Streaming Memory Candidate Selector

### Purpose

Prepare possible memory context while the user is speaking so that relevant memory can be available when the final pipeline needs it — without writing anything or overriding structured truth.

### Examples

- user says "Bumblebee" → prepare vehicle context
- user says "Bre" → prepare spouse context
- user says "Evergreen" → prepare known track context
- user says "my son" → prepare family entity candidates

### Rules

- streaming memory candidates are read-preparation only
- no memory write may occur from streaming cognition
- no memory candidate may override structured truth
- no memory candidate may be injected into the final response unless authorized by the final pipeline
- memory relevance must be revalidated against the final transcript before use

### Important Principle

Memory preparation during streaming reduces latency. It does not grant streaming cognition any authority over memory reads or writes.

---

## 11. Streaming Tool Candidate Selector

### Purpose

Identify likely tool needs before final routing so that tool schemas, parameter extraction paths, and validation requirements can be prepared early.

### Examples

- calendar read or write likely
- reminder likely
- weather likely
- place search likely
- message send likely
- contact lookup likely
- email search likely
- music control likely

### Rules

- no tool executes from provisional state under any circumstances
- no irreversible action may occur before final confirmation rules are satisfied
- tool arguments prepared during streaming must be revalidated against the final transcript
- provisional tool candidates must be discarded if final routing disagrees

### Important Principle

Tool prediction improves preparation. Tool execution requires final commitment. These are different events separated by an authority boundary that must never be crossed.

---

## 12. Streaming Emotional Tone Detector

### Purpose

Identify the user's conversational tone as the interaction unfolds so that response style, attention level, and interruption handling can be informed by emotional context.

### Possible Tone Signals

- casual
- focused
- frustrated
- urgent
- excited
- reflective
- tired
- confused
- playful
- serious

### Rules

- tone detection must not override factual truth
- tone detection must not produce unsupported assumptions about the user's state
- tone detection should influence phrasing only after the authoritative response payload exists
- sensitive emotional inference must remain lightweight and non-clinical

### Important Principle

Tone detection informs style. It does not alter content. The authoritative response payload is shaped by truth — tone shapes how that truth is delivered.

---

## 13. Streaming Attention Gate

### Purpose

Determine how much cognitive effort the streaming layer should invest in a given input, preventing the system from over-processing background noise, half-utterances, or stale partials.

### Gate Outcomes

- ignore — background noise, not worth tracking
- track lightly — casual side comment, low attention investment
- prepare — likely command forming, begin provisional preparation
- escalate — clear directed speech, full turn handling begins
- suppress — stale partial, cancel and discard
- cancel — active provisional state is invalidated

### Important Principle

The Attention Gate protects the streaming layer from wasting resources on inputs that will not result in a turn. It must integrate with the Conversational Attention Architecture — the two must not produce conflicting attention decisions.

---

## 14. Cognitive Draft Buffer

### Purpose

Store provisional response plans before final commitment so that response composition can begin earlier and the final response feels faster to the user.

### Example Draft Types

- likely clarification question
- likely short factual answer
- likely tool confirmation response
- likely memory recall response
- likely conversational response
- likely refusal or safety path

### Rules

- drafts are disposable — they have no authority
- drafts must be invalidated on correction
- drafts must be invalidated on topic shift
- drafts must be invalidated when final routing disagrees
- drafts must not contain unverified facts even internally unless marked explicitly provisional
- Live may not use draft content as an independent source of truth under any circumstances

### Important Principle

The Cognitive Draft Buffer improves speed. Its contents must never be promoted to the user without passing through the authoritative response pipeline first.

---

## Lifecycle Flow

### Stage 1 — Listening Starts

Zola enters streaming cognition mode when valid user speech begins or an active conversational session is open.

Actions:
- create streaming turn state
- assign turn ID
- begin partial transcript observation
- initialize attention state
- initialize confidence tracking

### Stage 2 — Partial Transcript Updates

As partial speech arrives:
- update partial transcript
- detect stable phrase segments
- predict provisional intents
- track provisional entities
- track correction markers
- track topic movement
- prepare memory candidates
- prepare tool candidates
- update emotional tone signal
- update attention score

No final actions are committed at any point during this stage.

### Stage 3 — Stable Segment Promotion

When a phrase becomes stable:
- mark it as stable within Streaming Turn State
- allow provisional preparation to increase in confidence
- prepare the likely downstream route
- prepare possible memory and tool context

Stable does not mean final. Final transcript authority still wins.

### Stage 4 — End-of-Turn Detection

When the user appears to finish speaking:
- wait for final transcript boundary
- resolve the coalesced transcript
- close streaming turn state
- convert relevant provisional data into final pipeline hints
- discard all stale provisional branches

The final transcript enters the normal authoritative pipeline.

### Stage 5 — Final Pipeline Execution

The authoritative turn pipeline performs:
- final transcript normalization
- final intent routing
- final entity resolution
- final memory retrieval
- final tool execution eligibility check
- final safety checks
- Authoritative Result Contract construction
- ResponseExecutionService commit
- Live phrasing within truth constraints

Streaming Cognition may have provided hints. It does not own the result.

### Stage 6 — Speech Output Phase

During speech output:
- Streaming Cognition watches for barge-in
- the Attention Gate detects interruption signals
- the Interruption Handler classifies the interruption type
- speech stops if classification warrants it
- a new turn state begins if appropriate

Live phrases the authorized response only. It may not use streaming draft content as independent truth.

---

## Authority Rules

### Provisional Is Not Truth

Anything generated during streaming is provisional unless explicitly promoted by the authoritative final pipeline. Provisional status is not a formality — it is a hard constraint.

### Final Transcript Wins

Partial transcripts and stable segments must be superseded by the final transcript without exception. A provisional candidate that conflicts with the final transcript must be discarded.

### QueryProcessor Remains Final Routing Authority

Streaming intent forecasting may prepare routing paths. It may not decide which path is taken. The QueryProcessor — or equivalent — owns final routing.

### Structured Memory Remains Canonical

Streaming memory candidates may prepare read paths. They may not override structured memory truth. The Memory Hierarchy authority order applies regardless of what streaming candidates suggest.

### Durable Write Authority Remains Required

Streaming Cognition may never write durable memory directly. All durable writes must pass through Durable Write Authority regardless of how confident the streaming layer is.

### Tool Execution Requires Final Commitment

Streaming Cognition may never execute tools directly. No provisional tool candidate may trigger an action before the final pipeline authorizes it.

### Live Owns Phrasing Only

Live may speak authorized content naturally. It may not introduce facts, claims, or information drawn from streaming draft content. The authorized response payload is the only source Live may draw from.

### ResponseExecutionService Remains Commit Authority

Final response commitment must pass through ResponseExecutionService. Streaming Cognition has no commit authority of its own.

---

## State Model

### Temporary State

Streaming Cognition may maintain temporary state including:
- partial transcripts and stable transcript segments
- provisional intent, entity, memory, and tool candidates
- attention score and tone signal
- topic movement signal
- draft response plan
- tool likelihood signal

Temporary state must be discarded or archived as non-authoritative metadata after the turn completes. It must never be treated as durable memory.

### Session State

Streaming Cognition may reference session-level structures including:
- active conversation ID
- active topic stack (read-only reference)
- current user engagement mode
- current speech mode
- current autonomous mode
- recent interruption history
- recent correction history

Session state is referenced, not owned. The Conversational Continuity Architecture owns the topic stack. Streaming Cognition reads it — it does not write it.

### Durable State

Streaming Cognition may not directly mutate durable state. All durable writes must route through existing memory write authorities.

---

## Core Architectural Principles

---

### Preparation Without Authority

Streaming Cognition prepares everything and decides nothing. Every output it produces is provisional. Every decision it appears to make is actually a hint that the authoritative pipeline may accept, ignore, or contradict.

---

### Final Transcript Supersedes All Partials

No partial transcript, stable segment, or provisional candidate has authority over the final transcript. When the final transcript lands, it supersedes everything that came before it without exception.

---

### No Streaming Writes

Streaming Cognition has no write access to durable memory, tool execution APIs, or the topic stack. These authorities belong to other systems. The streaming layer observes and prepares — it does not persist.

---

### Provisional State Is Temporary

All streaming state expires at the turn boundary. Nothing from the streaming phase persists beyond the turn without passing through the appropriate authority. Streaming Turn State that is not promoted is discarded.

---

### Live Speaks Authorized Content Only

The Live speech component phrases authorized responses naturally. It may not draw from the Cognitive Draft Buffer, provisional cognition artifacts, or streaming turn state as independent sources of fact. The authorized response payload is the only truth Live receives.

---

## Integration Points

This document connects directly to:

- Zola Master Architecture Plan (Section 3)
- Conversational Continuity Architecture (Topic Stack and Streaming Topic Tracker boundary)
- Conversational Attention Architecture (Streaming Attention Gate integration)
- Memory Hierarchy Architecture (Streaming Memory Candidate Selector boundary)
- Autonomous Behavior Architecture (Autonomous Coordination rules)
- Environmental Awareness Architecture (signal observation during active turns)

---

## Failure Modes and Safeguards

### Premature Commitment

Risk: Zola acts on partial speech before the user finishes, executing a tool or routing a response based on an incomplete transcript.

Safeguards:
- no tool execution from provisional state
- no durable writes from provisional state
- final transcript authority required before any commitment
- provisional candidates are marked with `isCommitEligible = false`

### Partial Transcript Drift

Risk: A partial transcript that appeared stable changes meaning after finalization, but a downstream component has already acted on the earlier interpretation.

Safeguards:
- partial state is superseded by the final transcript without exception
- all provisional candidates are revalidated against the final transcript
- no provisional candidate may be treated as final until the pipeline confirms it

### Hidden Second Router

Risk: The Streaming Intent Forecaster accumulates enough influence that it effectively becomes a second routing authority, with the QueryProcessor rubber-stamping its predictions rather than evaluating independently.

Safeguards:
- forecasts are hints only — the QueryProcessor must evaluate independently
- runtime logs must prove the final route source on every turn
- any turn where the streaming forecast and the final route disagree must be logged

### Live Improvisation Leak

Risk: Live speaks facts drawn from a discarded cognitive draft rather than the authorized response payload, introducing unverified information into the spoken response.

Safeguards:
- Live receives only the authorized response payload
- the Cognitive Draft Buffer is not exposed to Live as a source of truth
- the Speech Authority Constraint must be enforced at the interface between the pipeline and Live

### Memory Pollution

Risk: Partial user statements are stored as memory before the user has finished or corrected them, producing incorrect durable memory from incomplete input.

Safeguards:
- no memory writes from streaming cognition under any circumstances
- Durable Write Authority is required for all durable writes
- correction handling must occur before memory learning triggers

### Tool Argument Pollution

Risk: A tool executes with arguments derived from a stale partial phrase rather than the final transcript, producing an action based on something the user did not actually say.

Safeguards:
- tool arguments must be re-extracted from the final transcript before execution
- provisional tool arguments are explicitly marked disposable
- final tool execution logs must include the source transcript used for argument extraction

### Topic Stack Corruption

Risk: Streaming topic movement signals mutate the topic stack directly, corrupting the unwinding order and causing incorrect branch return behavior.

Safeguards:
- streaming topic signals are provisional — they are observations, not mutations
- the Conversational Continuity layer owns all final topic stack mutations
- return anchors are implemented as stack pointers; streaming cognition may not push or pop directly

---

## Observability and Runtime Proof

Streaming Cognition must be fully observable in logs without exposing private reasoning to the user.

### Required Log Tags

- `ZolaStream_Input` — transcript event received
- `ZolaStream_State` — streaming turn state snapshot
- `ZolaStream_IntentForecast` — provisional intent prediction and confidence
- `ZolaStream_EntityCandidate` — entity identified during streaming
- `ZolaStream_TopicSignal` — topic movement detected
- `ZolaStream_Interruption` — interruption classified and routed
- `ZolaStream_Correction` — correction detected and handled
- `ZolaStream_MemoryCandidate` — memory context prepared
- `ZolaStream_ToolCandidate` — tool predicted and schema prepared
- `ZolaStream_Finalize` — final transcript received, streaming state closed
- `ZolaStream_Discard` — provisional candidate discarded and reason
- `ZolaStream_PromoteHint` — provisional hint passed to final pipeline

### Required Proof Points

Every completed turn must produce log evidence for:
- partial transcript received and streaming state initialized
- stable phrase detected with confidence level
- provisional candidates generated with types and confidence
- final transcript received and superseding partials
- provisional candidates either discarded or passed as hints with routing decision
- final routing source confirmed as authoritative pipeline
- no tool executed before final commitment
- no durable memory write from streaming state
- barge-in classified if it occurred
- correction handled if it occurred
- topic movement signal logged separately from any topic stack mutation

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only.

### Sequencing Intent

The following represents the intended logical build order, subject to revision after the audit:

1. **Observation Only** — add Streaming Turn State and logging without influencing routing. Exit criteria: streaming state can be observed and discarded safely with no effect on final output.

2. **Provisional Candidate Generation** — add intent forecaster, entity tracker, memory candidate selector, tool candidate selector, correction detector, and interruption classifier. Exit criteria: candidates are generated and discarded without changing final output.

3. **Hint Promotion Into Final Pipeline** — allow selected provisional data to be passed as hints. Exit criteria: hints improve speed or context without changing authority boundaries, proven by runtime logs.

4. **Interruption-Aware Speech Coordination** — connect to speech playback and barge-in handling. Exit criteria: Zola can safely stop, resume, or reroute during live speech.

5. **Topic Stack Integration** — connect streaming topic signals to the Conversational Continuity layer. Exit criteria: Zola tracks live topic movement without corrupting continuity state.

6. **Cognitive Draft Buffer** — add disposable draft planning. Exit criteria: drafts improve responsiveness but never bypass final response authority.

7. **Autonomous Coordination** — coordinate streaming cognition with autonomous behavior so proactive actions do not interrupt active user turns. Exit criteria: autonomous behavior and streaming cognition do not compete.

### Implementation Guardrails for Cursor

When implementing Streaming Cognition, Cursor must follow these constraints without exception:

- do not replace QueryProcessor
- do not create a second routing authority
- do not execute tools from partial transcripts
- do not write memory from partial transcripts
- do not expose cognitive drafts to Live as truth
- do not let Live use provisional artifacts as independent facts
- do not mutate the Topic Stack directly from streaming detection
- do not refactor unrelated STT, TTS, memory, or routing code
- do not blend provisional and final authority
- add runtime logs before enabling any behavioral influence
- prefer small wave-based implementation
- preserve all existing authority contracts

### Files Likely Involved

Exact file paths must be determined by the Ava codebase audit. The following areas are likely to be relevant:

- speech and STT transcript ingestion
- turn coalescer
- QueryProcessor
- ResponseExecutionService
- Live client and session handling
- audio playback and TTS interruption handling
- memory read pipeline
- entity resolution pipeline
- tool execution manager
- conversational continuity and topic stack layer
- autonomous behavior layer

### Open Questions

- Should Streaming Cognition live as its own service or as a subcomponent of the speech and session layer?
- What minimum confidence threshold should allow a provisional hint to be passed forward?
- Should memory candidates be prepared synchronously or asynchronously?
- Should tool schemas be preloaded for likely tools during streaming to reduce latency?
- How should streaming state be surfaced in the debug UI?
- Should cognitive drafts be logged in full, summarized, or redacted for privacy?
- Should interruption history influence future speech pacing behavior?
- Should repeated corrections temporarily lower confidence thresholds in the Stable Phrase Detector?
- Should Streaming Cognition be enabled only in Live mode first, or across all voice modes from the start?
- How much of Streaming Cognition should remain active during autonomous monitoring mode?

### Success Criteria

Streaming Cognition is successful when:
- Zola feels faster and more naturally responsive without any change to final output accuracy
- Zola handles corrections without losing the conversation
- Zola handles barge-in cleanly and classifies interruption type correctly
- Zola prepares context before the final response phase
- Zola tracks topic movement more naturally during live speech
- Zola does not commit partial misunderstandings
- Zola does not create duplicate routing authority
- Zola does not pollute memory
- Zola does not execute tools prematurely
- Zola does not let Live improvise from provisional drafts
- runtime logs prove provisional state was either discarded or promoted safely on every turn

### Architectural Risks

- the boundary between streaming cognition and the Conversational Attention Architecture must be precisely defined — both layers process live speech and both make attention-related decisions; without a clear boundary they will conflict
- the hint promotion mechanism in Stage 3 is the most architecturally sensitive phase — hints that are accepted too broadly will silently become a second routing authority
- the Cognitive Draft Buffer creates a risk that Live will draw from draft content in edge cases; the interface between the pipeline and Live must make this architecturally impossible, not just policy-prohibited

---

## Long-Term End State

Streaming Cognition eventually evolves toward:

- real-time topic tracking that anticipates conversational direction before turns complete
- interruption handling so natural that corrections and redirects feel like normal conversation
- provisional preparation so accurate that final pipeline execution feels nearly instantaneous
- emotional tone detection that informs response style without clinical inference
- full coordination with autonomous behavior so proactive cognition never competes with active user speech
- complete observability so every streaming decision can be traced and explained

The system should ultimately feel:

- responsive without being hasty
- prepared without being presumptuous
- aware of corrections before they finish
- natural in handling interruptions
- invisible — the user should feel faster responses, not notice the streaming layer

without losing:

- the hard separation between provisional cognition and committed truth
- the authority of the final transcript over all partial interpretations
- the prohibition on streaming memory writes and tool execution
- the principle that Live speaks authorized content only
- complete runtime observability for every provisional decision
