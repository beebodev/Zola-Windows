# Memory Hierarchy Architecture

### Foundational Architecture for Layered Cognitive Memory

---

## Vision

The Memory Hierarchy Architecture defines how Zola organizes, prioritizes, retrieves, and applies memory across different time scales and confidence levels.

The goal is not simply to remember more. The goal is to make memory useful, safe, explainable, and context-aware.

Zola must be able to distinguish between what is happening right now, what was said recently, what the current conversation is about, what matters from previous conversations, what is permanently true or important, what should fade away, what should be consolidated into durable memory, and what should never be written without authority.

The system should eventually feel less like:

> "a system that stores everything and retrieves whatever is convenient"

and more like:

> "a system that knows what to remember, what to let go, and what to protect."

---

## Core Philosophy

### Memory Must Be Earned

Traditional memory systems:

- store everything by default
- treat all inputs as equally valid
- retrieve broadly and filter late
- allow any layer to overwrite any other

This system:

- classifies every potential memory before storing it
- requires confidence and authority before promoting to durable layers
- retrieves intentionally based on current context and intent
- enforces strict authority ordering when layers conflict

Each memory layer has a defined role with clear ownership, read rules, write rules, decay behavior, and promotion rules. No single memory store acts as universal truth.

---

## Non-Goals

This architecture does not define the full implementation of every memory repository. It does not replace:

- Entity Resolution Architecture
- Episodic Memory Architecture
- Conversational Continuity Architecture
- Autonomous Behavior Architecture
- Durable Write Authority
- Relationship Reasoning Engine
- Agentic RAG Architecture

Instead, this plan defines how those systems fit into a unified memory hierarchy.

---

## Long-Term Architectural Pillars

---

## 1. Memory Layer Overview

### Purpose

Organize Zola's memory into six distinct layers, each with a different durability, scope, confidence requirement, and authority level. No layer may assume the role of another.

### Layer Definitions

**Layer 0 — Immediate Turn Context**

The current user utterance, current system state, current tool results, and active response contract.

Answers: What did the user just ask? What is the system doing right now? What facts are available for this exact response?

- expires immediately after the response is committed
- must never be written directly to durable memory without passing through write authority

**Layer 1 — Short-Term Conversational Memory**

The recent turn window. Allows Zola to understand references like "that," "the one we just talked about," "go back to what we were saying," "before I left," and "what were we talking about?"

Should include:
- recent user turns and assistant responses
- active entities and active topic
- active subtopic
- unresolved questions and open loops
- current emotional tone
- current task state

Layer 1 is volatile and optimized for active flow, not long-term storage. It decays quickly unless promoted.

**Layer 2 — Session Memory**

Tracks the broader state of the current conversation or active work session.

Answers: What is this session mainly about? What goals are active? What has been decided? What branches are paused but returnable?

Should include:
- session topic summary
- active goals and project context
- current document or artifact under development
- decisions made this session
- paused branches and return anchors
- user preference signals observed this session

Session Memory may survive temporary interruptions but must not automatically become permanent memory.

Session boundaries, the `SessionRecord` model, and start/end triggers are defined in `Zola_Session_Identity_Architecture.md`. This document describes what session-scoped memory contains — not the session boundaries themselves.

**Layer 3 — Episodic Memory**

Stores meaningful experiences, conversations, project events, and personal stories as summarized, searchable episodes with metadata — not raw transcripts.

Answers: What happened before? When did it happen? Why did it matter? What themes were involved?

Example episode structure:
- Topic: Childhood memory conversation
- Themes: nostalgia, family, identity, emotional reflection
- Importance: high
- Recall triggers: childhood, growing up, old memories, family stories
- Summary: The user shared several meaningful memories from childhood and wanted them preserved for future contextual use.

Episodic Memory is useful when the current conversation is thematically related to a past experience. It must be injected carefully, not constantly.

**Layer 4 — Structured Canonical Memory**

Stores durable facts and relationships. This is the highest-authority memory layer for factual truth.

Answers: Who is the user? Who are the user's family members? What vehicles does the user own? What projects exist? What relationships exist between entities?

Examples:
- User's wife is Breanna.
- User's sons are Dominic, Micah, and Madden.
- Bumblebee is a Nissan 350Z drift car.
- Zola is the current assistant platform identity under design.

Structured Canonical Memory must be protected by Durable Write Authority. No weaker memory layer may overwrite this layer directly.

**Layer 5 — Behavioral and Preference Memory**

Tracks how the user prefers interactions to work. Context-scoped, not global — the user may prefer one style when working on Zola architecture and another when troubleshooting a car.

Answers: Does the user prefer short answers? Does the user prefer casual tone in shop conversations? Does the user prefer formal tone in work documents?

Example entries:
- Context: Zola engineering → surgical, incremental changes; strict source-of-truth docs; wave-gated prompts
- Context: automotive troubleshooting → direct, casual, practical responses

Behavioral Memory must not flatten the user into a single universal personality profile.

**Layer 6 — Reflective and Consolidated Memory**

Stores higher-level lessons, patterns, and summaries that emerge over time through consolidation — not direct casual capture.

Answers: What recurring themes matter to the user? What long-running projects are evolving? What patterns should influence future behavior?

Example:
> The user is building Zola as a deeply personalized, autonomous assistant platform with strict authority boundaries, memory hierarchy, and agentic reasoning.

Reflective Memory should be compact, high-value, and slow-changing. It improves context — it must never override direct instructions.

### Important Principle

Memory must be layered by durability, scope, confidence, and authority. Each layer has a defined role. No layer may absorb the responsibilities of another.

---

## 2. Memory Authority Order

### Purpose

Define the precedence order when memory layers conflict, ensuring that stronger and more authoritative sources always win over weaker or inferred ones.

### Authority Order

1. Current user instruction
2. Current tool result or verified runtime result
3. Active response contract
4. Structured Canonical Memory (Layer 4)
5. Session Memory (Layer 2)
6. Episodic Memory (Layer 3)
7. Behavioral Memory (Layer 5)
8. Reflective Memory (Layer 6)
9. Weak inferred memory

### Conflict Resolution Rules

- current user instruction always wins unless it violates a safety rule or system constraint
- Structured Canonical Memory wins over episodic summaries when answering factual questions
- Episodic Memory adds context but must not replace canonical truth
- Behavioral Memory shapes style but must not change facts
- Reflective Memory guides high-level understanding but must not create unsupported claims

### Important Principle

When layers conflict, the authority order is the rule — not a suggestion. Silent resolution in favor of a weaker layer is a failure mode, not a feature.

---

## 3. Read Path Rules

### Purpose

Ensure memory retrieval is intentional, selective, and scoped to what is actually needed for the current response — not a broad dump of all available memory.

### Read Path Evaluation Criteria

Before retrieval, the read path must evaluate:
- current user intent
- active topic and active entities
- relationship chain requirements
- emotional tone
- project context
- recency and importance
- confidence
- user permission or sensitivity level
- response type

### Read Modes

**Direct Recall** — used when the user explicitly asks about stored information.

Example: "What are my sons' birthdays?"

Prioritizes Structured Canonical Memory. Does not surface episodic or behavioral memory unless canonical memory is insufficient.

**Contextual Injection** — used when memory is relevant but not explicitly requested.

Example: the user starts talking about childhood nostalgia. Zola may retrieve prior childhood-related episodes to improve contextual understanding.

Contextual Injection must be conservative. Relevance must be clear before injection occurs.

**Conversational Continuity Recall** — used when the user refers to recent or session-level conversation.

Example: "What were we talking about before I said I had to go?"

Prioritizes Layer 1 and Layer 2.

**Autonomous Scan** — used by autonomous systems to identify possible proactive help opportunities.

Must be tightly gated. Must not automatically produce user-facing action. Read results from an Autonomous Scan do not constitute permission to interrupt.

**Relationship Reasoning Recall** — used when the user asks relationship-chain questions.

Example: "Who is Micah's grandmother?"

Must invoke the Relationship Reasoning Engine. Must not rely on shallow memory summaries that may produce incorrect relationship chains.

### Important Principle

Memory retrieval is intentional. Zola should not flood every response with available memory. The read path selects what is actually useful for the current moment.

---

## 4. Write Path Rules

### Purpose

Ensure that memory writes are classified, controlled, and routed through appropriate authority before any durable storage occurs.

### Write Classification

Every potential memory write must first be classified as one of:
- Ignore — no value, no storage
- Short-term only — useful for active flow, expires with the turn
- Session only — useful for this conversation, expires with the session
- Episodic candidate — meaningful experience worth summarizing
- Structured canonical candidate — durable fact requiring DWA approval
- Behavioral preference candidate — style or timing preference, context-scoped
- Reflective consolidation candidate — high-level pattern emerging from multiple episodes

### Durable Write Authority

All durable writes must pass through Durable Write Authority (DWA). This includes:
- structured facts
- entity relationships
- long-term preferences
- important events
- sensitive memories
- project source-of-truth updates

DWA must evaluate each write candidate for:
- explicitness — was this stated clearly or merely implied?
- confidence — how certain is the interpretation?
- sensitivity — does this require stronger protection?
- existing conflicts — does this contradict existing canonical memory?
- source layer — which layer is proposing the write?
- user intent — did the user intend this to be remembered?
- write destination — which layer is being written to?
- merge behavior — how does this interact with existing entries?
- audit trail — can this write be explained and reversed?

### Weak Memory Protection

Weak inferred memory must not overwrite strong memory under any circumstances.

Example: if a casual conversation implies something about the user's preference, it may become a low-confidence candidate. It must not overwrite an explicit long-term preference even if the implied preference seems more recent.

### Important Principle

Zola must never treat every user sentence as durable memory. Writes are earned through classification, confidence, and authority — not proximity to the user's last utterance.

---

## 5. Promotion Rules

### Purpose

Define the conditions under which memory may be promoted from a shorter-lived layer to a more durable one, ensuring that only genuinely valuable memory advances.

### Short-Term to Session

Promote when:
- the topic remains active across multiple turns
- the user makes a decision
- the user starts a task or document
- the conversation contains open loops that are not yet resolved

### Session to Episodic

Promote when:
- the conversation has emotional significance
- the conversation contains meaningful personal stories
- the session produced important project decisions
- the user explicitly wants the conversation remembered
- the session context may be useful in future related conversations

### Episodic to Reflective

Promote when:
- multiple episodes share a recurring theme
- a recurring pattern becomes clearly identifiable
- the user repeatedly reinforces a preference or life context
- a project direction has stabilized across many sessions

### Any Layer to Structured Canonical Memory

Promote only when:
- the fact is durable and clearly stated
- the entity or relationship is unambiguous
- confidence is high
- DWA approves the write
- the existing structured memory is not incorrectly overwritten

### Important Principle

Promotion is earned. A memory that has not been reinforced, confirmed, or proven important should not advance to a more durable layer simply because time has passed.

---

## 6. Decay Rules

### Purpose

Define how memory fades across each layer so that Zola practices intentional forgetting — retaining what matters and releasing what does not.

### Layer 0 Decay

Expires immediately after the response is committed. No persistence.

### Layer 1 Decay

Decays quickly as the conversation advances. Important unresolved references may remain temporarily active but must not persist indefinitely.

### Layer 2 Decay

Persists for the session and may survive short interruptions.

Decays when:
- the active task is completed
- the user switches to a major unrelated context
- a long period passes without return
- the session summary has been consolidated

### Layer 3 Decay

Episodic memories lose retrieval weight over time unless reinforced by related conversations. They should not be automatically deleted — instead, their activation threshold should rise, making them less likely to surface without a strong contextual match.

### Layer 4 Decay

Structured Canonical Memory does not decay automatically. Facts require correction, replacement, or deletion through authority-controlled flows. Time alone does not invalidate a structured fact.

### Layer 5 Decay

Behavioral preferences decay if contradicted repeatedly by newer user behavior. A preference that the user has stopped expressing over many sessions should weaken before it is eventually replaced.

### Layer 6 Decay

Reflective memory should be periodically reviewed and compacted. Outdated reflections must be revised or removed — not blindly accumulated alongside newer patterns that may contradict them.

### Important Principle

Intentional forgetting is as important as intentional remembering. A memory system that never forgets becomes as unusable as one that never remembers.

---

## 7. Consolidation Phase

### Purpose

Review short-lived memory periodically and determine what should be promoted, summarized, or discarded — separate from live response generation so that consolidation decisions are never rushed.

### Responsibilities

- review fading conversations and session memory before they expire
- compress meaningful content into episodic summaries
- extract structured fact candidates for DWA evaluation
- update behavioral preference profiles
- update reflective memory with newly confirmed patterns
- link memory to existing projects or entities where appropriate
- discard low-value memory that has not earned promotion
- produce audit entries for all consolidation decisions

### Consolidation Inputs

- recent conversation summary
- session memory state
- episodic candidates identified during the session
- active entities from the session
- user correction signals
- explicit remember and forget instructions
- repeated behavioral patterns observed

### Consolidation Outputs

- approved structured writes (routed through DWA)
- new or updated episodic entries
- updated behavioral preference profile
- reflection updates
- discarded low-value memory with discard reason
- audit entries for every consolidation decision

### Important Principle

Consolidation must run separately from live response generation. Memory decisions made mid-response under time pressure are more likely to be incorrect and harder to audit.

---

## 8. Topic Stack and Branching

### Purpose

Allow Session Memory to maintain conversational continuity across nested topic detours so that Zola can return to prior branches in the correct order without losing context.

### Responsibilities

- maintain the current topic, parent topic, child branches, paused branches, return anchors, and completion state
- push the current topic pointer onto the stack when a detour begins
- pop the most recent pointer when the user returns from a detour
- preserve open loops for each paused branch
- prune stale abandoned branches that have decayed past a useful threshold
- prevent unrelated detours from overwriting the main session topic

### Return Anchor Stack

Return anchors must be implemented as an ordered stack of pointers — not a flat list or a single stored previous topic. Each push preserves the full nesting order so that unwinding occurs correctly.

Example stack flow:

```text
Start:
[Architecture]

Detour into Git:
[Architecture, Git]

Detour into Branching:
[Architecture, Git, Branching]

Detour into SSH Keys:
[Architecture, Git, Branching, SSH Keys]

User says "back to branching":
[Architecture, Git, Branching]

User says "back to the Git stuff":
[Architecture, Git]

User says "back to the memory architecture doc":
[Architecture]
```

### Topic Pointer Schema

```kotlin
data class TopicReturnPointer(
    val topicId: String,
    val parentTopicId: String?,
    val summaryRef: String?,
    val activeEntityIds: List<String>,
    val openLoopIds: List<String>,
    val createdAt: Instant,
    val lastTouchedAt: Instant
)
```

### Stack Operations

- push on detour entry
- pop on explicit return signal
- peek for "what were we just working on?"
- prune abandoned branches past decay threshold
- preserve open loops when restoring a branch
- prevent detours from overwriting the main topic

### Important Principle

The stack is an ordered structure, not a flat history. Correct unwinding depends entirely on preserving the original nesting order. Any implementation that collapses branches into a flat list will produce incorrect return behavior.

---

## 9. Emotional and Importance Weighting

### Purpose

Apply importance weights to memory based on signals beyond recency alone so that emotionally significant, repeatedly referenced, or project-critical memories receive stronger retention.

### Weighting Signals

- user explicitly states something matters
- user shares a personal story
- user repeats a topic across multiple conversations
- user shows frustration, excitement, or strong emotional engagement
- the memory affects future decisions or actions
- the memory relates to a long-running project
- the memory corrects a previous error in the system's understanding

### Important Principle

Emotional weighting does not mean amplifying or performing emotion. It means using emotional context as a signal for memory importance — the same way a human naturally remembers things that mattered more than things that were incidental.

---

## 10. Memory Injection Rules

### Purpose

Define when and how memory may be injected into a response so that injection feels natural and useful rather than intrusive or surveillance-like.

### Injection Requirements

Injected memory must be:
- relevant to the current turn or topic
- brief — memory should inform the response, not dominate it
- accurate — only inject memory that has sufficient confidence
- non-invasive — do not announce that memory is being used
- contextually appropriate — sensitive memory requires stronger context justification
- lower priority than the user's current instruction — memory never overrides what the user just said

### Good Injection

User: "I was thinking about old childhood stuff again."

Zola may use prior childhood-related episodic memory to understand the emotional context and respond naturally — without announcing that it is drawing on a memory.

### Bad Injection

User: "What socket size is this bolt?"

Zola must not inject unrelated personal memories. The question is a simple factual lookup. Injecting personal context would be intrusive and confusing.

### Important Principle

Zola should not constantly signal that it is remembering. Memory should inform responses invisibly. If injection would feel like an intrusion, it should stay silent.

---

## 11. Conflict Handling

### Purpose

Define how the system resolves conflicts between memory layers so that stronger, more authoritative memory always wins and conflicts are never silently resolved in favor of a weaker source.

### Conflict Types

- structured fact versus episodic statement
- old preference versus new user behavior
- user correction versus existing memory
- multiple entities with similar or identical names
- ambiguous relationship references
- project rename or identity transition

### Conflict Resolution Rules

- user corrections are treated as high-priority and routed through DWA immediately
- Structured Canonical Memory must not be overwritten without DWA approval
- ambiguous entity references must fail closed or prompt a targeted clarification — never guess
- old behavioral memory is adjusted only after repeated contradiction or explicit user correction
- conflicts between layers must be logged with both the conflicting values and the resolution applied

### Important Principle

Silent conflict resolution in favor of weaker memory is a failure mode. Conflicts must be resolved explicitly, logged, and traceable.

---

## 12. Privacy and Sensitivity

### Purpose

Ensure that sensitive and deeply personal memories receive stronger write controls, more conservative recall thresholds, and full respect for user deletion and suppression requests.

### Rules

- sensitive or personal memories require higher confidence before being written as durable entries
- sensitive memories should not be surfaced unless the user asks directly, the context strongly supports it, the memory is necessary to help, and the response can be handled respectfully and minimally
- forget requests must be respected immediately through the appropriate deletion or suppression pathway
- deletion of a sensitive memory must cascade through all layers that may hold a copy

### Important Principle

Privacy is not a feature applied at the display layer. It is enforced at the write layer, the retrieval layer, and the injection layer. A memory the user has asked to forget must not reappear from a layer that was not also cleared.

---

## 13. Runtime Contracts

### Purpose

Define the structured data contracts that govern memory retrieval and write operations so that every read and write decision is explicit, auditable, and traceable.

### Memory Retrieval Contract

```kotlin
data class MemoryRetrievalContract(
    val query: String,
    val intent: String,
    val activeEntities: List<ResolvedEntity>,
    val memoryLayersQueried: List<MemoryLayer>,
    val retrievedItems: List<RetrievedMemoryItem>,
    val selectedItems: List<SelectedMemoryItem>,
    val rejectedItems: List<RejectedMemoryItem>,
    val authorityDecision: MemoryAuthorityDecision,
    val injectionMode: MemoryInjectionMode,
    val confidence: Double,
    val auditId: String
)
```

### Memory Write Candidate Contract

```kotlin
data class MemoryWriteCandidate(
    val sourceLayer: MemoryLayer,
    val proposedDestination: MemoryLayer,
    val extractedFact: String?,
    val extractedEntity: ResolvedEntity?,
    val extractedRelationship: RelationshipCandidate?,
    val preferenceCandidate: PreferenceCandidate?,
    val episodicCandidate: EpisodicCandidate?,
    val confidence: Double,
    val sensitivity: SensitivityLevel,
    val requiresUserConfirmation: Boolean,
    val dwaDecision: DurableWriteDecision?
)
```

### Important Principle

Every memory read and every memory write must produce a structured contract. Implicit or undocumented memory operations are not permitted.

---

## Core Architectural Principles

---

### Memory Is Layered by Authority

No single store acts as universal truth. Each layer has a defined role, and authority ordering determines the outcome when layers conflict. The hierarchy is not a suggestion — it is the rule.

---

### Writes Are Classified Before Storage

Every potential memory write is classified into one of seven categories before any storage decision is made. Unclassified writes do not occur. Durable writes require DWA approval.

---

### Retrieval Is Intentional

Memory is retrieved based on current intent, context, and relevance — not retrieved broadly and filtered late. The read path evaluates what is needed before fetching.

---

### Weak Memory Cannot Override Strong Memory

Inferred, casual, or low-confidence memory candidates must never overwrite explicit, durable, or high-confidence memory. The authority order exists precisely to prevent this.

---

### Intentional Forgetting Is Required

Decay rules, consolidation, and forget-request handling are not optional features. A memory system that never forgets accumulates noise that degrades every recall decision over time.

---

### Memory Failure Must Be Safe

If retrieval fails, Zola continues without memory and does not invent details. If DWA rejects a write, the write does not occur through an alternate path. Failure responses are bounded and honest.

---

## Integration Points

This document connects directly to:

- Zola Master Architecture Plan (Section 4)
- Conversational Continuity Architecture
- Autonomous Behavior Architecture (Behavioral Learning Layer)
- Streaming Cognition Architecture
- Conversational Attention Architecture (No Ambient Durable Writes)
- Environmental Awareness Architecture (Environmental Memory)
- Environmental Perception Architecture (Environmental Memory Integration Layer)
- Trust, Permission, and Privacy Framework (Master Plan Section 13)
- Distributed Presence Architecture

---

## Failure Modes and Safeguards

### Memory Invention

Risk: When retrieval fails or returns insufficient results, Zola fabricates remembered details to fill the gap, producing false memory that the user may treat as fact.

Safeguards:
- retrieval failure must produce a bounded honest response, not an invented one
- Zola must not claim to remember something it did not retrieve
- confidence scores prevent low-quality recalls from surfacing as authoritative

### Authority Bypass

Risk: A weaker memory layer overwrites Structured Canonical Memory directly, corrupting the canonical truth without DWA review.

Safeguards:
- no layer below Layer 4 has direct write access to Structured Canonical Memory
- all writes to Layer 4 must pass through DWA
- all write attempts are logged — failed attempts and their reasons are preserved

### Memory Pollution from Ambient Speech

Risk: Overheard conversations, background media, or low-confidence utterances are stored as user memory, corrupting behavioral or episodic layers over time.

Safeguards:
- ambient speech must be blocked from all write paths by the Conversational Attention Architecture
- write candidates from low-confidence attention states are discarded, not stored
- DWA requires attention-authorized source before any durable write

### Silent Conflict Resolution

Risk: When two memory layers conflict, the system silently resolves in favor of the weaker source without logging the conflict, producing incorrect behavior that is impossible to trace.

Safeguards:
- conflicts must be logged with both conflicting values and the resolution applied
- authority order is enforced, not inferred
- ambiguous entity conflicts fail closed or prompt clarification rather than guessing

### Stale Reflective Memory

Risk: Reflective Memory accumulates outdated patterns that contradict newer behavior but continue to influence responses because consolidation never reviewed or revised them.

Safeguards:
- Reflective Memory must be periodically reviewed and compacted during the consolidation phase
- outdated reflections are revised or removed, not accumulated alongside newer patterns
- consolidation audit entries record what was revised and why

### Forget Request Leakage

Risk: The user requests that a memory be deleted, but the deletion only applies to one layer while copies persist in others, causing the memory to reappear later.

Safeguards:
- forget requests must cascade through all layers that may hold a copy
- deletion must be confirmed in the audit log across all affected layers
- subsequent recall attempts for deleted memory must return nothing, not a degraded version

---

## Observability and Auditability

Memory behavior must be fully auditable. Every read and write decision must be traceable after the fact.

### Required Log Tags

- `ZolaMemory_ReadPath` — which layers were queried and why
- `ZolaMemory_WriteCandidate` — what was proposed and its classification
- `ZolaMemory_DWA` — DWA evaluation result and reason
- `ZolaMemory_Consolidation` — what was promoted, discarded, or revised
- `ZolaMemory_Decay` — what decayed and when
- `ZolaMemory_Conflict` — conflicting values, authority decision, and resolution
- `ZolaMemory_Injection` — what was injected, why, and at what confidence

### Required Queryable Questions

- Why was this memory selected for injection?
- Why was this memory rejected from injection?
- Was a write candidate created from this utterance?
- Did DWA approve or reject the write, and why?
- Did a lower layer attempt to override a higher layer?
- Was this memory affected by consolidation?
- Has this memory been deleted or suppressed?

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only.

### Sequencing Intent

The following represents the intended logical build order for this architecture, subject to revision after the audit:

1. Define formal layer contracts, enums, DTOs, and authority decision types
2. Add read path classification before retrieval
3. Add memory selection and rejection audit logging
4. Add write candidate pipeline — classify before storing
5. Route all durable writes through Durable Write Authority
6. Add session and topic stack memory with return anchor stack
7. Add consolidation phase separate from response generation
8. Add contextual injection rules with relevance and confidence gating
9. Add decay and reinforcement signals per layer
10. Add runtime proof, validation scenarios, and regression coverage

### Dependencies

- Conversational Continuity Architecture must be stable before Session Memory and topic stack are built — they share the same underlying state model
- Durable Write Authority must be defined before any Layer 4 write paths are built
- Conversational Attention Architecture must gate ambient speech before any write paths are activated
- Autonomous Behavior Architecture must define the Autonomous Scan read mode boundaries before autonomous memory access is enabled

### Open Questions

- Should consolidation run after every session, only after high-value sessions, or on a scheduled background basis?
- Should the user be able to review pending memory write candidates before they are committed?
- How should Zola expose memory confidence levels in the UI, if at all?
- Should emotional weighting be stored as metadata on memory entries, or calculated dynamically at retrieval time?
- Should Reflective Memory be user-editable?
- What is the retention policy for low-confidence episodic memory that was never reinforced?
- How should autonomous behavior request memory context without over-triggering recall across all layers?

### Validation Scenarios

The following scenarios must pass before any memory layer is considered production-ready:

**Scenario A — Recent Topic Recall:** User discusses childhood memories, leaves briefly, then asks what they were talking about. Layer 1 and Layer 2 retrieve the prior topic accurately. No durable write occurs unless already approved.

**Scenario B — Durable Fact Recall:** User asks for sons' birthdays. Structured Canonical Memory is queried. Episodic memory does not override the structured result.

**Scenario C — Emotional Episode Recall:** User returns to a nostalgia topic. Episodic memory is retrieved contextually. Injection is brief. Sensitive details are not overexposed.

**Scenario D — Weak Preference Candidate:** User casually says "I kind of like shorter answers when I'm in the shop." A behavioral preference candidate is created, context-scoped to shop interactions. It does not globally override all response style.

**Scenario E — Memory Conflict:** User corrects a stored vehicle fact. The correction routes through DWA. Structured memory is updated only through the approved path. The conflict is logged with both values.

**Scenario F — Topic Branch Return:** User starts an architecture document, detours into Git strategy, then says "back to the memory doc." Session Memory restores the architecture document context via the topic stack. The Git branch is preserved on the stack until explicitly resolved.

**Scenario G — Failed Memory Retrieval:** Memory service fails during a recall request. Zola does not invent memory. Zola gives a bounded response. The failure is logged.

### Architectural Risks

- The topic stack requires strict push and pop discipline — any component that mutates session topic state outside the stack will corrupt unwinding order and produce incorrect branch return behavior
- Consolidation timing is architecturally significant — running it too frequently adds overhead, running it too infrequently means valuable memory is lost when sessions expire before consolidation occurs
- Forget request cascading is easy to implement incompletely — a deletion that misses even one layer will reappear as a ghost memory and erode user trust

---

## Long-Term End State

Memory Hierarchy eventually evolves toward:

- layered memory that intelligently distinguishes immediate context from long-term truth
- authoritative canonical facts that are protected from accidental overwrite
- episodic memory that preserves meaningful experiences without accumulating raw transcripts
- behavioral memory that learns context-specific preferences without flattening the user into a single profile
- reflective memory that captures high-level patterns over time without becoming stale
- consolidation that runs continuously in the background, keeping memory lean and accurate
- full auditability so that every recall and every write can be explained

The system should ultimately feel:

- trustworthy because it remembers what matters accurately
- respectful because it forgets what it should
- transparent because its memory decisions can always be explained
- safe because no write occurs without authority and no deletion goes incomplete

without losing:

- the authority ordering that protects canonical truth from weaker inference
- the write classification discipline that prevents casual utterances from becoming permanent facts
- the intentional forgetting that keeps the system lean over time
- the principle that memory failure must produce honest bounded responses, never invention
