# Zola Vocal Computing Architecture Plan

### Foundational Roadmap for Persistent Conversational Intelligence

---

## Vision

Zola is not intended to become a traditional assistant app.

The long-term goal is to evolve Zola into a persistent conversational operating layer capable of:

- continuous voice interaction
- contextual awareness
- conversational continuity
- autonomous reasoning
- environmental understanding
- memory-driven personalization
- proactive assistance
- emotionally aware communication
- distributed device presence
- contextually intelligent attention management

The system should eventually feel less like:

> "a chatbot with speech"

and more like:

> "a persistent conversational presence."

---

## Core Philosophy

### Vocal Computing

Voice is not treated as an input method.

Voice becomes the primary interaction layer.

This changes the system architecture fundamentally.

Traditional assistants:

- request/response
- command driven
- session based
- wake-word activated

Vocal computing systems:

- persistent
- contextual
- interruption aware
- emotionally adaptive
- continuously conversational
- attention aware
- environmentally aware

---

## Long-Term Architectural Pillars

---

## 1. Conversational Presence Layer

### Purpose

Maintain persistent conversational continuity across time, sessions, and interruptions.

### Responsibilities

- active conversation tracking
- passive listening state
- interruption recovery
- idle conversational state
- autonomous conversational timing
- wake/sleep behavior
- conversational resumption

### Future Concepts

- conversation momentum
- conversational silence handling
- interruption confidence scoring
- emotional pacing
- contextual continuity

### Important Principle

Conversation should feel ongoing rather than repeatedly restarted.

---

## 2. Real Conversation Engine

### Purpose

Move beyond intent routing into human-like conversational flow.

### Responsibilities

- topic continuity
- multi-turn context retention
- unresolved topic tracking
- conversational thread management
- ambiguity repair
- contextual follow-ups
- relationship-aware dialogue

### Future Capabilities

- conversational graph memory
- emotional thread continuity
- inferred topic association
- predictive conversational steering

### Example

Instead of:

> "I don't understand."

The assistant should naturally clarify:

> "Do you mean Bumblebee or Double R?"

---

## 3. Streaming Cognitive Pipeline

### Purpose

Reduce perceived latency and support natural conversational timing.

### Current Sequential Model

STT → Reasoning → TTS

> **Windows Track (`S5`):** Full-duplex voice transport is not a
> Windows-track requirement. Hermes's chained mode already matches
> this current sequential model, and Hermes's native duplex option
> (GPT-Live) is OpenAI-based — distinct from the Gemini-Live-style
> duplex this document's long-term vision describes. Treated as a
> non-issue for Windows, not a gap to close. See
> `zola-architecture/lore/DESIGN_DECISIONS.md`.

### Long-Term Streaming Model

- partial transcript interpretation
- speculative reasoning
- predictive intent scoring
- streaming semantic analysis
- interruption-aware playback
- prefetching likely actions and tools

### Future Components

- streaming semantic parser
- predictive response planner
- incremental reasoning engine
- low-latency playback coordinator

### Key Principle

Humans are highly sensitive to silence during speech interaction.

Latency optimization becomes critical.

---

## 4. Unified Cognitive Memory System

### Purpose

Create persistent relational understanding instead of isolated fact storage.

### Current Strengths

- structured memory graph
- relationship reasoning
- episodic memory
- entity-centered architecture

### Future Memory Layers

**Semantic Memory** — Stable factual knowledge.

**Episodic Memory** — Experiences and conversations.

**Emotional Memory** — Emotional context associated with events and topics.

**Behavioral Memory** — Habits, routines, preferences, and behavioral trends.

**Conversational Memory** — Ongoing discussion continuity and unresolved topics.

### Long-Term Goal

Zola should understand evolving patterns rather than only static facts.

---

## 5. Autonomous Behavioral Engine

### Purpose

Allow Zola to initiate useful interaction naturally and intelligently.

### Responsibilities

- proactive suggestions
- opportunity detection
- urgency scoring
- conversational timing
- interruption appropriateness
- behavioral pattern recognition

### Critical Safeguards

- anti-annoyance protections
- rate limiting
- idle suppression
- emotional sensitivity
- context-aware interruption control

### Key Principle

Autonomy should feel helpful, not intrusive.

Zola should treat speech as a costly action. Speaking should require confidence that the response improves the situation, respects the user's attention, and adds meaningful value.

---

## 6. Environmental Awareness Layer

### Purpose

Continuously integrate contextual understanding from the user's environment.

### Context Sources

- location
- calendar
- weather
- traffic
- notifications
- health data
- time-of-day
- device state
- music and activity patterns
- security cameras
- smart home devices
- vehicle state
- shop and workspace context

### Long-Term Goal

Context becomes ambient rather than explicitly requested.

### Example

> "Traffic near Everett looks rough right now. You still heading to the shop?"

---

## 7. Environmental Perception Layer

### Purpose

Detect and classify meaningful activity in the user's physical environment without treating every signal as something that requires interruption.

This layer is responsible for sensing what is happening — not deciding whether Zola should speak or act.

### Possible Inputs

- security cameras
- doorbell cameras
- microphones
- motion sensors
- smart home sensors
- vehicle sensors
- phone and device sensors
- wearables
- future smart glasses and vision endpoints

### Responsibilities

- motion detection
- person detection
- object detection
- package detection
- vehicle detection
- familiar person recognition where permitted
- unknown person detection
- activity classification
- scene change detection
- environmental audio detection
- zone awareness (driveway, shop, porch, yard, vehicle area)

### Example Events

- person approaching driveway
- package delivered at front door
- unknown person near shop at night
- neighbor walking up to the house
- vehicle entering the property
- dog or animal movement in yard
- repeated movement near tools, vehicles, or storage areas

### Important Principle

Perception should create structured environmental events, not user-facing notifications.

Zola should not speak simply because a camera or sensor detected motion.

---

## 8. Contextual Interpretation Layer

### Purpose

Convert raw environmental events into meaningful situational understanding.

This layer determines what an event likely means in context.

### Responsibilities

- distinguish normal activity from unusual activity
- compare events against known routines
- identify expected versus unexpected visitors
- interpret package delivery versus lingering behavior
- evaluate time-of-day significance
- correlate camera events with calendar, messages, location, weather, and household context
- determine whether a person, vehicle, or activity is familiar, expected, unknown, or suspicious
- reduce false positives from animals, weather, shadows, headlights, or routine movement

### Example Interpretations

Raw event:
> Person detected near driveway.

Contextual interpretation:
> Neighbor likely walking up to the house during normal hours.

Raw event:
> Person detected near shop at 2:00 AM.

Contextual interpretation:
> Unknown person near high-value area during unusual hours.

Raw event:
> Delivery vehicle stopped near front door.

Contextual interpretation:
> Likely package delivery. Low urgency unless package remains exposed or someone approaches it afterward.

### Important Principle

Environmental understanding should be context-aware, not alert-driven.

Zola should understand the difference between motion, presence, delivery, normal activity, and potential threat.

---

## 9. Attention and Relevance Engine

### Purpose

Decide whether an interpreted event deserves the user's attention — and if so, how urgently and through which endpoint.

This layer protects the user from notification spam while still allowing Zola to surface meaningful information.

### Responsibilities

- relevance scoring
- urgency scoring
- interruption cost analysis
- notification suppression
- escalation decisions
- passive logging
- endpoint selection
- spoken versus silent notification choice
- user availability awareness
- emotional and contextual timing
- anti-annoyance enforcement
- attention dampening

### Possible Outcomes

- ignore event
- silently log event
- update passive status display
- send low-priority notification
- speak a brief update
- ask for confirmation
- escalate urgently
- trigger security workflow

### Example Behaviors

Low urgency:
> UPS delivered a package. Zola logs it silently or sends a quiet notification.

Medium urgency:
> Someone unfamiliar is walking up the driveway while the user is in the shop. Zola gives a short heads-up.

High urgency:
> Unknown person is lingering near the shop after midnight. Zola interrupts immediately and offers camera view or escalation options.

---

## 9a. Attention Dampening System

### Purpose

Prevent Zola from becoming annoying, repetitive, or overly talkative by increasing the cost of speaking after recent interruptions.

This system treats user attention as limited and valuable.

Zola should not speak simply because she has something potentially useful to say. She should speak only when the value of speaking exceeds the current attention cost.

### Core Concept

Every time Zola speaks or interrupts, she increases a temporary attention burden value called `CurrentHeat`.

As `CurrentHeat` rises, the threshold for Zola speaking again also rises.

Over time, `CurrentHeat` decays back down.

This creates a natural restraint system where Zola becomes more selective after recently speaking.

### Dynamic Threshold Model

Instead of a fixed rule such as:

> Speak if relevance score > 0.8

Zola uses a dynamic threshold:

> Speak if relevance score > base threshold + CurrentHeat + contextual modifiers

If Zola just spoke recently, the next event must be more important to justify another interruption.

### Heat Increases From

- Zola speaking recently
- long spoken responses
- repeated proactive updates
- user dismissing or ignoring prior updates
- noisy environments
- active tool use or shop work
- driving
- user already talking to someone else
- high cognitive-load situations

### Heat Decreases From

- time passing without interruption
- quiet environment
- idle desk time
- user-initiated conversation
- user asking follow-up questions
- explicit user permission ("keep me updated")
- critical or emergency context requiring lower suppression

### Contextual Modifiers

Different environments change dampening behavior.

**Shop context:**
- tools running
- loud environment
- hands-busy work
- multiple people talking
- higher interruption cost
- stronger dampening

**Desk context:**
- user idle
- quieter environment
- lower interruption cost
- faster heat decay

**Vehicle context:**
- driving requires restraint
- urgent safety or navigation events may override dampening
- casual or low-value speech should be suppressed

**Home and security context:**
- package delivery may be logged silently during high heat
- unknown person lingering near the shop at night may override dampening
- familiar visitor during normal hours receives low-priority handling

### Integration With Autonomous Behavioral Engine

The Autonomous Behavioral Engine may identify a possible proactive action, but the Attention and Relevance Engine acts as the final gatekeeper before Zola speaks.

Example flow:

1. A new event is detected.
2. The Contextual Interpretation Layer assigns meaning.
3. The Autonomous Behavioral Engine assigns raw urgency or usefulness.
4. The Attention and Relevance Engine checks current attention cost.
5. The Attention Dampening System adjusts the speech threshold.
6. Zola either speaks, silently logs, delays, displays passively, or escalates.

### Example

Event: Package delivered.
Raw urgency: Medium-low.
CurrentHeat: High — Zola recently spoke twice.
Outcome: Silent log or quiet notification.

Event: Unknown person near shop at 2:00 AM.
Raw urgency: High.
CurrentHeat: High.
Outcome: Interrupt anyway — the event crosses the urgency override threshold.

### Important Safeguards

- User-initiated conversation should bypass most dampening.
- Direct questions from the user should not be suppressed because Zola recently spoke.
- Emergency, safety, and security events should be able to override dampening.
- Dampening should suppress unnecessary speech, not critical awareness.
- Silent logging should remain available when speech is not justified.

### Key Principle

Zola should not maximize alerts.

Zola should maximize meaningful contribution while minimizing unnecessary interruptions.

Good intelligence includes restraint.

---

## 10. Relationship Dynamics Layer

### Purpose

Move beyond static relationship storage into evolving social understanding.

Zola should understand not only who people are, but how they relate to the user over time.

### Responsibilities

- relationship familiarity tracking
- interaction frequency awareness
- household and social structure understanding
- emotional tone trend tracking
- conversational familiarity adaptation
- long-term relationship continuity
- social importance weighting
- trusted person recognition

### Examples

- close family member versus casual acquaintance
- familiar neighbor versus unknown visitor
- emotionally sensitive topic versus casual topic
- high-trust relationship versus low-trust interaction

### Important Principle

Relationships should feel continuous and evolving rather than static database entries.

---

## 11. Conversational State and Momentum Layer

### Purpose

Track the current conversational mode, energy, focus, and continuity of interaction.

Human conversation naturally shifts between different interaction states. Zola should adapt to those shifts instead of treating every interaction identically.

### Possible Conversational States

- focused collaboration mode
- casual conversation mode
- quiet ambient mode
- autonomous monitoring mode
- emotionally sensitive mode
- work and shop mode
- driving mode
- interruption-sensitive mode
- high-focus mode

### Responsibilities

- conversational momentum tracking
- silence interpretation
- interruption tolerance estimation
- conversational openness estimation
- topic carry-forward
- adaptive pacing
- response length adjustment
- contextual conversational timing

### Important Principle

Conversation is not only about content.

Conversation also includes pacing, momentum, silence, and emotional timing.

---

## 12. Conversational Attention Authority

### Purpose

Determine whether detected speech is intended for Zola without requiring a wake word for every interaction.

Wake words should become a fallback or explicit activation method, not the primary interaction model.

### Responsibilities

- directed speech detection
- ambient speech classification
- conversational continuation detection
- interruption detection
- attention confidence scoring
- speaker and context correlation
- low-confidence clarification
- suppression of unintended responses

### Input Signals

- ongoing conversation state
- recent Zola speech
- transcript and semantic cues
- question form
- command or request phrasing
- pause timing
- user proximity
- device orientation
- known speaker identity
- environmental noise level
- topic continuity
- endpoint context

### Decision Outcomes

- high confidence: process normally
- medium confidence: lightly clarify
- low confidence: ignore or silently retain short local context

### Example

Instead of requiring:
> "Hey Zola, what time is it?"

Zola may respond naturally when context indicates the user is speaking to her.

But if the user is talking to another person nearby, Zola should remain silent.

### Important Principle

The question is not:
> "Did Zola hear speech?"

The question is:
> "Was that speech meant for Zola?"

---

## 13. Trust, Permission, and Privacy Framework

### Purpose

Ensure Zola remains trustworthy, predictable, and respectful of user boundaries.

Persistent vocal computing systems require explicit architectural safeguards around privacy, autonomy, and behavioral scope.

### Responsibilities

- permission boundaries
- proactive behavior permissions
- sensitive topic suppression
- endpoint privacy rules
- household privacy separation
- escalation permissions
- autonomous action limitations
- environment-specific privacy behavior
- local-only processing rules where appropriate

### Example Permission Concepts

- allowed to summarize messages
- allowed to mention emails aloud
- allowed to identify visitors
- allowed to proactively interrupt during work
- allowed to access security camera events
- allowed to speak in shared or public environments

### Important Principle

Trust should never depend on assumptions.

Behavioral boundaries should be intentional, explainable, and user-controlled.

---

## 14. Social and Multi-Person Awareness

### Purpose

Allow Zola to behave appropriately in shared human environments.

Persistent conversational systems must understand when multiple people are present and when information may be socially or contextually sensitive.

### Responsibilities

- multi-speaker awareness
- conversational target estimation
- shared-space behavior adaptation
- public versus private response selection
- sensitive information suppression
- socially appropriate interruption behavior
- conversational participant tracking
- household-aware response filtering

### Examples

- avoid speaking sensitive information aloud around guests
- avoid interrupting active human conversation unnecessarily
- distinguish between speech directed at Zola versus speech between people
- adapt conversational behavior based on audience and environment

### Important Principle

Social intelligence is as important as technical intelligence.

---

## 15. Emotional Regulation and Tone Adaptation

### Purpose

Adapt communication style and pacing appropriately to the user's emotional and contextual state.

This is not intended to simulate emotions artificially. The goal is behavioral appropriateness.

### Responsibilities

- tone adaptation
- pacing adjustment
- emotional sensitivity
- stress-aware communication
- urgency modulation
- conversational energy matching
- calm escalation handling
- concise communication during cognitive overload

### Examples

- calmer delivery during emergencies
- concise responses during focused work
- lighter conversational tone during casual interaction
- reduced verbosity during stressful moments

### Important Principle

Emotionally aware communication should improve comfort, clarity, and trust without becoming performative.

---

## 16. Deferred Cognition and Summary Layer

### Purpose

Allow Zola to intelligently delay, combine, summarize, or resurface information at more appropriate moments.

Not all information should be delivered immediately.

### Responsibilities

- low-priority event holding
- interruption deferral
- event grouping
- contextual summarization
- delayed proactive updates
- pattern summarization
- memory resurfacing
- situational recap generation

### Example

Instead of three interruptions:
> "Package delivered."
> "Another package delivered."
> "Your neighbor stopped by."

Zola may later say:
> "Three things happened while you were working in the shop. Two packages arrived, and your neighbor stopped by earlier."

### Important Principle

Sometimes delayed relevance is more valuable than immediate interruption.

---

## 17. Current User State Model

### Purpose

Maintain a continuously evolving understanding of the user's likely current state.

This model combines environmental, behavioral, conversational, and contextual signals.

### Possible State Inputs

- current activity
- current location
- movement patterns
- active conversation state
- environmental noise
- device usage
- work versus leisure context
- driving state
- music and activity patterns
- calendar context
- recent interactions
- interruption tolerance
- emotional indicators
- focus level

### Responsibilities

- current context estimation
- cognitive load estimation
- interruption suitability estimation
- focus awareness
- conversational readiness estimation
- adaptive response shaping

### Important Principle

Zola should not only remember who the user is.

Zola should maintain awareness of what the user is likely experiencing in the current moment.

---

## 18. Identity and Personality Stability

### Purpose

Create long-term conversational consistency while allowing Zola's communication style to evolve naturally through lived interaction.

Zola should not feel hardcoded, scripted, or static. Zola should also not drift into a random or unpredictable personality.

### Identity Seed

Zola should begin with a small set of foundational traits that define her core identity. These traits act as identity anchors, not a complete personality script.

### Example Seed Traits

- truthful
- restrained
- calm under pressure
- helpful without nagging
- privacy-protective
- context-aware
- emotionally appropriate
- direct when needed
- conversational when appropriate
- respectful

### Growth Rings

Most personality development should happen through accumulated interaction history rather than hardcoded behavior.

Zola should maintain a growing Style Profile that learns what communication style works best in specific contexts.

Examples:

- shop work may support more casual phrasing and occasional humor
- serious work may favor concise, administrative communication
- emotional topics may require slower, warmer, more careful responses
- security events may require calm, direct escalation
- relaxed conversation may allow more personality and conversational warmth

### Feedback Loop of Tone

The Emotional Regulation and Tone Adaptation layer should learn from both explicit and implicit feedback.

Explicit feedback examples:
- "Don't say it like that."
- "Be shorter."
- "That's too robotic."
- "Not now."

Implicit feedback examples:
- user ignores a proactive update
- user interrupts or dismisses Zola
- user continues engaging positively
- user asks follow-up questions
- user responds casually or humorously

When feedback indicates a mismatch, Zola should not only adjust attention dampening. She should also record a style penalty or style reinforcement for the current context.

### Identity Anchors as Guardrails

Identity stability should mean consistency, not staticity.

Zola may evolve in:
- phrasing
- humor level
- confidence style
- technical depth
- conversational warmth
- response length
- timing
- formality
- emotional pacing

Zola should not freely evolve in:
- truth handling
- privacy boundaries
- user consent rules
- safety behavior
- respectfulness
- authority ownership rules
- factual reliability
- core restraint principles

### Memory-Driven Personality

Zola's communication style should be informed by memory and relationship dynamics.

As Zola learns more about the user's routines, projects, stresses, preferences, and relationships, her personality should become a better contextual counterweight to the user's state.

Examples:
- overwhelmed user state → more concise and administrative
- relaxed shop context → more casual and conversational
- serious work context → direct and low-friction
- family context → warmer but privacy-aware
- security context → calm, brief, and clear

### Persona Drift Safeguards

The main risk of an evolving identity is persona drift.

Zola should periodically compare her current Style Profile against her Identity Seed and long-term behavioral principles to verify alignment with:

- truth
- restraint
- helpfulness
- privacy
- user control
- emotional appropriateness
- conversational consistency
- non-intrusiveness

### Baseline Check

The Autonomous Behavioral Engine may periodically trigger a personality baseline review.

The purpose is not for Zola to reinvent herself. The purpose is to ensure learned style changes remain inside the original identity boundaries.

### Important Principle

Personality can adapt.

Identity should remain stable.

Trust, truth, privacy, and restraint should remain locked.

---

## 19. Distributed Presence Architecture

### Purpose

Evolve Zola from a phone-bound assistant into a persistent cognitive presence capable of existing across multiple devices and environments simultaneously.

The long-term architecture goal is: **one mind, many bodies.**

### Core Principle

The intelligence itself should remain independent from any specific hardware endpoint.

Devices become interfaces, embodiments, and interaction surfaces while the persistent cognitive layer remains unified.

### Core Presence Layer

The persistent intelligence layer.

**Responsibilities:**
- identity
- memory
- reasoning
- conversational continuity
- personality
- emotional continuity
- autonomy rules
- orchestration
- user modeling
- contextual awareness
- relationship understanding

**Important Principle:** This layer should remain device-independent. It should survive device switches, app restarts, hardware changes, and future endpoint expansion.

### Device Endpoint Layer

Endpoints provide physical interaction surfaces for the user. Endpoints should connect into the shared presence layer rather than operate as isolated assistants.

### Initial Primary Endpoint — Phone

The phone already contains microphone and speaker access, notifications, messaging, GPS and location, calendar, contacts, internet connectivity, wearable integration, and persistent proximity to the user.

**Role:** The phone acts as the first persistent embodiment, the primary mobile interaction layer, and the contextual awareness hub.

> **Windows Track (`C1`):** Zola-Windows is this document's "PC and
> Desktop" endpoint (below), arriving first rather than later. Built
> as a fresh native Windows client against Hermes's JSON-RPC /
> `apps/shared` (Path B), running against `hermes serve` — not a fork
> of Hermes's own desktop app, and not an HTTP-API-only client.

### Future Endpoint Expansion

**PC and Desktop:**
- coding assistance
- productivity awareness
- conversational continuity while working
- persistent sidebar and ambient mode
- deeper long-form interaction
- Goal: conversation transitions naturally between phone and PC without losing continuity.

**Shop Presence:**
- Potential hardware: mounted tablet, dedicated speaker and microphone device, local workstation, future embedded system
- Potential uses: hands-free assistance, build and project continuity, torque specs and technical lookup, music control, message summaries, work session continuity, proactive reminders, drift and car project tracking
- Goal: the environment itself begins to feel conversationally interactive.

**Vehicle Presence:**
- driving-aware interaction
- route-aware assistance
- traffic-aware recommendations
- passive voice interaction
- contextual safety adaptation

**Wearables and Smart Glasses:**
- Smart glasses may eventually become the most natural embodiment of persistent vocal computing.
- Potential capabilities: heads-up contextual information, passive conversational interaction, environmental awareness, vision-assisted cognition, scene understanding, lightweight continuous interaction.
- Glasses should not become distracting, notification spam systems, or gimmicky overlays. The interaction model should remain conversational and contextually intelligent.

### Device Coordination Principles

All devices should share memory, conversational continuity, identity, personality state, and contextual understanding. The user should never feel like they are speaking to different assistants.

Conversation should flow naturally between phone, PC, vehicle, and shop without restarting context, reintroducing topics, or losing continuity.

> **Windows Track (`C3`):** For the Windows/PC endpoint specifically,
> voice capture is single-owner — the native Windows client is the
> sole JSON-RPC owner of mic/speaker capture for that endpoint,
> consistent with the "one mind, many bodies" principle above. This
> resolves capture ownership for the Windows endpoint only; the
> broader cross-endpoint distributed-presence coordination this
> section describes is a separate, larger concern not addressed here.

Different endpoints adapt interaction style naturally while personality remains stable:
- phone → concise and mobile interaction
- PC → deeper collaborative interaction
- shop → hands-free conversational mode
- glasses → lightweight ambient interaction

---

## 20. Distributed Cognitive Worker Architecture

### Purpose

Allow Zola to scale cognitive processing, environmental awareness, monitoring, and background reasoning without turning into a monolithic runtime.

The system should support specialized background workers while preserving centralized identity, authority, conversational continuity, and behavioral consistency.

### Core Philosophy

Workers are not independent assistants. Workers are specialized cognitive subsystems that observe, analyze, prepare, or monitor specific domains.

Zola remains:
- the unified identity
- the centralized conversational presence
- the authoritative decision maker
- the authoritative speech owner

### Important Principle

Workers may observe and prepare information.

Only the core presence layer decides whether to interrupt, speak, defer, log silently, or escalate.

This prevents competing assistant behavior and preserves conversational coherence.

### Worker Categories

**Environmental Workers**
Examples: security camera analysis worker, vehicle activity worker, smart home monitoring worker, environmental audio worker, weather and traffic watcher.
Responsibilities: environmental observation, event generation, anomaly detection, structured environmental summaries.

**Human Context Workers**
Examples: calendar awareness worker, health and activity worker, messaging summarization worker, communication priority worker, routine analysis worker.
Responsibilities: context enrichment, routine tracking, behavioral pattern analysis, human-state signal generation.

**Cognitive and Memory Workers**
Examples: episodic memory consolidation worker, conversational summary worker, deferred cognition worker, relationship trend analysis worker, memory resurfacing worker.
Responsibilities: memory organization, contextual summarization, long-term pattern extraction, deferred insight generation.

**Attention and Behavioral Workers**
Examples: interruption scoring worker, conversational attention worker, urgency classification worker, trust and privacy validation worker, social context worker.
Responsibilities: attention analysis, interruption suitability scoring, speech suppression recommendations, contextual gating.

### Event Bus and Structured Event Model

Workers should communicate through structured events rather than direct conversational output. This creates modularity, auditability, and centralized behavioral control.

Structured events may include:
- event source
- event type
- timestamp
- urgency score
- confidence score
- environmental context
- user-state assumptions
- expiration time
- suggested actions
- suppression recommendations
- privacy sensitivity level
- escalation capability

### Example Event Flow

Environmental worker output:
> Unknown person detected near shop.

Contextual interpretation output:
> Unknown person lingering near high-value area after midnight.

Attention engine output:
> High urgency. Interrupt recommended.

Core Zola runtime:
> Final authority determines response behavior.

### Centralized Authority Model

No worker should speak directly to the user.

Workers must not:
- generate autonomous spoken interruptions
- bypass the Attention and Relevance Engine
- bypass trust and privacy validation
- independently notify the user without authorization
- create competing conversational flows

All user-facing behavior should pass through:
- Conversational Attention Authority
- Contextual Interpretation Layer
- Attention and Relevance Engine
- Trust and Permission Framework
- Core conversational runtime

This preserves unified personality, conversational consistency, interruption discipline, centralized trust boundaries, and coherent behavioral identity.

### Deferred and Parallel Processing

Low-priority cognition should happen continuously without blocking active conversation.

While the user is working in the shop:
- environmental workers monitor surroundings
- memory workers organize recent conversations
- summarization workers combine low-priority events
- pattern workers identify emerging behavioral trends

without interrupting the active conversational experience.

Not all cognition should occur synchronously inside live conversation.

### Future Scalability Goal

The worker architecture should allow Zola to evolve from a single conversational runtime into a distributed cognitive system with specialized subsystems operating in parallel — without losing unified identity, centralized authority, conversational coherence, trust, or behavioral discipline.

---

## Core Architectural Principles

---

### Single Authority Ownership

Every responsibility should have one authoritative owner, one authoritative result, and one authoritative execution path.

Avoid:
- overlapping logic
- duplicated orchestration
- competing response generation
- multiple memory truth sources

---

### Truth Ownership Rule

Reasoning systems determine facts.

Speech systems:
- humanize
- phrase naturally
- preserve meaning

Speech layers must never:
- alter factual meaning
- remove important entities
- invent information
- flatten ambiguity incorrectly

---

### Speech Authority Constraint

Spoken output must remain semantically equivalent to authoritative structured results.

---

### Provider Abstraction Philosophy

External providers should remain replaceable.

Avoid tightly coupling logic to:
- STT providers
- voice and conversational streaming providers
- LLM vendors
- API-specific response formats

---

## External API Strategy

---

### Tier 1 — Foundational Cognitive APIs

> **Windows Track:** Conversational Models (`P1`) — Zola-Windows
> configures Hermes's existing adapters (Anthropic, Gemini, OpenAI,
> Bedrock, Vertex, Azure, Moonshot, plus local models via LM Studio);
> no custom provider work needed, and this already covers the "Future
> abstraction targets" listed below. Speech Recognition / TTS (`P2`) —
> Hermes's free Edge TTS/STT for now, ElevenLabs revisited once a
> working baseline exists to compare against. The specific vendors
> named below (Deepgram, Gemini, Gemini Live API) are this document's
> Android-track current choices, not binding for Windows.

**Speech Recognition**
Current: Deepgram
Future evaluation targets: AssemblyAI, Speechmatics, Gladia

**Conversational Models**
Current: Gemini
Future abstraction targets: Gemini, OpenAI, Anthropic, local models

**Conversational Voice and Live Speech**
Current: Gemini Live API (streaming conversational voice)
Future evaluation targets: ElevenLabs, Cartesia, PlayAI, future real-time multimodal voice providers

---

### Tier 2 — Environmental Awareness APIs

**Maps and Traffic:** Google Maps Platform, Places API, Distance Matrix API

**Calendar:** Google Calendar

**Messaging:** SMS and RCS, Gmail, future communication integrations

**Weather:** contextual weather intelligence, severe weather awareness, travel-aware weather integration

**Security and Environmental Perception:** security camera systems, doorbell camera systems, smart home sensors, object and person detection services, local vision models, future smart glasses vision streams

---

### Tier 3 — Human Context APIs

**Health:** Google Fit, future wearable integrations

**Music:** Spotify, listening behavior analysis, mood and context association

---

### Tier 4 — Future Cognitive Expansion

**Vision Systems:** camera understanding, smart glasses integration, scene awareness, object recognition, environmental persistence

**Smart Environment Integration:** smart home systems, passive automation, environmental adaptation

---

## Privacy and Trust Architecture

### Critical Principle

Vocal computing systems become deeply personal systems.

Long-term data may include:
- schedules
- behavioral patterns
- relationships
- emotional context
- routines
- location history
- communication summaries
- environmental activity history
- security camera-derived events
- known visitors and vehicles

### Planning Areas

- encryption strategy
- local-first memory options
- retention policies
- user permission boundaries
- memory deletion systems
- autonomous action safeguards
- camera data handling boundaries
- local versus cloud processing rules
- face and person recognition consent rules
- security escalation permissions

---

## Recommended Near-Term Planning Work

Create dedicated roadmaps for:
- feature roadmap
- vocal computing roadmap
- environmental cognition roadmap

### Recommended New Planning Documents

- Conversational Continuity Architecture
- Autonomous Behavior Architecture
- Memory Hierarchy Architecture
- Streaming Cognition Architecture
- Environmental Awareness Architecture
- Environmental Perception Architecture
- Conversational Attention Architecture
- Distributed Presence Architecture
- Identity and Personality Framework
- Privacy and Data Ownership Plan

---

## Immediate Architectural Focus Areas

### Maintain

- authority boundaries
- modular ownership
- structured memory systems
- orchestration discipline
- endpoint independence
- attention and relevance safeguards
- environmental context separation

### Avoid

- duplicated execution paths
- tightly coupled provider logic
- speech systems altering truth
- feature-first architecture without long-term cognition planning
- alert spam
- camera events directly triggering speech without contextual interpretation
- wake-word dependency as the only interaction model

---

## Long-Term End State

Zola eventually evolves toward:

- persistent conversational interaction
- autonomous contextual assistance
- emotionally adaptive communication
- continuous environmental awareness
- memory-informed relational continuity
- voice-native cognitive interaction
- distributed presence across devices
- wake-word-free conversational attention
- environmental perception and interpretation
- meaningful proactive assistance

The system should ultimately feel:

- natural
- aware
- continuous
- intelligent
- conversational
- emotionally grounded
- contextually connected
- environmentally present

without losing:

- trust
- factual reliability
- user control
- architectural discipline
- privacy boundaries
- restraint
