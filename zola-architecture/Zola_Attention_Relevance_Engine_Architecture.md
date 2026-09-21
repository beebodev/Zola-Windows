# Attention/Relevance Engine + Attention Dampening System

### Foundational Architecture for Contextually Intelligent Interruption Management

---

## Vision

The Attention/Relevance Engine is not an alert dispatcher.

It is the system that decides whether the user's attention is worth spending — and if so, at what cost, through which channel, and at what moment.

Most ambient intelligence systems fail in the same way: they surface every event because they lack the judgment to distinguish useful information from interruption noise. The result is an assistant the user learns to ignore.

This system is designed to make the opposite choice at every decision point.

The goal is not to maximize information delivery. The goal is to maximize meaningful contribution while protecting the user's attention as a finite and valuable resource.

The Attention Dampening System is not a separate module bolted onto the engine. It is the engine's internalized sense of restraint — a continuous awareness of how much the user's attention has already been spent, and how much justification the next interruption must earn.

Together, these two systems should eventually feel less like:

> "a notification engine deciding what to push"

and more like:

> "a thoughtful presence that knows when to speak and when to stay quiet."

---

## Core Philosophy

### Attention as a Finite Resource

Traditional assistant systems treat every event as a candidate notification. If the event exceeds a fixed relevance threshold, it surfaces. If it does not, it is dropped. The threshold is static. The history of prior interruptions is not considered. The user's current cognitive state is not considered. The environment is not considered.

This produces alert spam.

Zola's Attention/Relevance Engine operates on a fundamentally different model.

Attention is treated as a resource with a current balance.

Every interruption draws from that balance.

The balance recovers over time, but it is never unlimited.

Before spending attention, the engine must ask: is this worth it right now?

Traditional notification systems:

- static thresholds
- event-driven triggering
- no memory of prior interruptions
- no awareness of current context
- no concept of interruption cost

This system:

- dynamic thresholds that rise and fall with context
- event interpretation before triggering
- full awareness of recent interruption history
- continuous current-state modeling
- explicit interruption cost analysis before every decision

---

## Long-Term Architectural Pillars

---

## 1. Relevance Scoring Layer

### Purpose

Assign a raw relevance score to every interpreted event that reaches this engine, reflecting how much the event is likely to matter to the user in isolation — before context or attention cost is applied.

### Responsibilities

- evaluate event type and category
- assess event urgency at face value
- assess potential user impact
- assign a base relevance score
- flag events that carry override potential regardless of context
- classify event expiration — how long does this remain actionable?

### Scoring Dimensions

Each event should be scored across multiple axes rather than a single relevance number.

**Impact Axis**

How much does this event affect the user's life, safety, property, plans, or relationships?

- security threat near property: very high
- package delivery: low
- calendar reminder: moderate
- familiar visitor arriving: low to moderate depending on context
- traffic affecting a departure time: moderate to high

**Timeliness Axis**

How quickly does this event stop being actionable?

- unknown person lingering near shop: expires quickly — urgency decays fast
- package delivered: expires slowly — package will still be there later
- traffic warning: expires at departure time
- calendar event starting: expires at event time

**User-Relevance Axis**

How personally relevant is this event to the user's known interests, routines, and priorities?

- event in a location the user is heading to: high
- event involving a known close contact: high
- recurring routine event with no variation: low
- anomaly against known routine: high

### Important Principle

Relevance scoring produces a candidate score, not a decision.

The raw relevance score enters the engine.

The decision to act on it depends on everything that comes next.

---

## 2. Urgency Classification Layer

### Purpose

Convert the raw relevance score into a discrete urgency classification that determines which response pathways are available.

### Urgency Tiers

**Tier 1 — Override-Eligible**

Events that may bypass dampening when urgency is sufficiently high.

Examples:
- unknown person lingering near high-value area at night
- active security escalation
- urgent safety signal
- user explicitly asked to be alerted about this category

Behavior: enters override evaluation rather than standard dampening check.

**Tier 2 — Standard Interrupt Candidate**

Events that are genuinely relevant and time-sensitive, but not emergencies.

Examples:
- familiar visitor approaching
- traffic affecting a departure in the next 30 minutes
- calendar event starting soon
- message from a high-priority contact requiring timely response

Behavior: enters full dampening evaluation. May be spoken, deferred, or silently logged depending on current heat.

**Tier 3 — Low-Priority Surface Candidate**

Events worth acknowledging but not urgent.

Examples:
- package delivered
- weather update with no near-term relevance
- routine notification with no time sensitivity

Behavior: enters dampening evaluation with a high suppression likelihood. Frequently deferred to silent log or summary batch.

**Tier 4 — Passive Log Only**

Events with no realistic case for interruption under current conditions.

Examples:
- animal movement in yard
- routine motion in expected areas
- familiar vehicle in familiar location at a normal hour

Behavior: logged silently. Not forwarded to the dampening system at all under normal conditions.

### Important Principle

Urgency classification prevents the dampening system from spending computational and attention resources evaluating events that should never surface.

Not every event deserves to reach the interrupt decision.

---

## 3. Interruption Cost Analysis

### Purpose

Evaluate the real cost of interrupting the user in their current state before any spoken or notification output is committed.

This layer asks: even if this event is relevant and urgent, what is the cost of speaking right now?

### Cost Factors

**Current Activity State**

- hands-busy work in the shop: high cost
- active human conversation nearby: very high cost
- driving in complex traffic: high cost
- idle at desk: low cost
- walking or light activity: moderate cost
- user-initiated conversation already active: low cost

**Environmental Noise Level**

- loud power tools running: interruption may not be heard, and attempting it may feel disruptive
- quiet environment: lower cost
- ambient music or background audio: moderate cost

**Recency of Prior Interruptions**

- Zola spoke very recently: high cost
- last interruption was well-received: slightly lower cost
- user dismissed or ignored last update: elevated cost

**Conversational State**

- user is mid-response to Zola: very high cost to interrupt
- conversation is at a natural pause: low cost
- user is speaking to another person: very high cost

**Emotional Context**

- user is in a high-stress state: elevated cost
- user appears relaxed or idle: lower cost
- emotionally sensitive topic is active: elevated cost

### Output

Interruption cost analysis produces a cost modifier that is applied on top of the relevance score inside the dampening evaluation.

High cost raises the bar the event must clear to justify a spoken response.

Low cost allows relevant events to surface more naturally.

### Important Principle

A relevant event in the wrong moment is still a bad interruption.

Context determines whether spending attention now serves the user or simply spends them.

---

## 4. Attention Dampening System

### Purpose

Prevent Zola from becoming repetitive, intrusive, or background-noisy by maintaining a running model of recent attention expenditure and dynamically raising the threshold for future interruptions as recent speech accumulates.

This is the engine's internalized sense of when it has already said enough.

### Core Mechanism

The Attention Dampening System maintains a value called `CurrentHeat`.

`CurrentHeat` represents the accumulated attention burden from recent Zola speech and interruptions.

As `CurrentHeat` rises, the effective threshold for Zola speaking again also rises.

As time passes without interruption, `CurrentHeat` decays back toward baseline.

The decision model becomes:

> Speak if: relevance score > (base threshold + CurrentHeat + interruption cost modifier + contextual dampening modifier)

Rather than a fixed threshold, the bar Zola must clear is always dynamic — reflecting the current state of the user's attention account.

### Heat Sources

The following events increase `CurrentHeat`:

- Zola speaking proactively (unsolicited)
- Zola delivering a long spoken response
- user dismissing or ignoring a Zola update
- user saying "not now," "stop," or equivalent
- multiple proactive updates in a short window
- interruption occurring during high-noise or high-focus context
- user failing to engage with a prior proactive suggestion

### Heat Reduction Sources

The following events reduce `CurrentHeat` over time:

- time passing without Zola speaking
- quiet environment with no active interruptions
- user-initiated conversation (user asked something — this signals conversational openness)
- user engaging positively with a proactive update
- explicit user invitation such as "keep me updated on that"
- transition to a lower-cost context such as moving from shop to desk idle time
- emergency context flag, which partially suspends dampening for safety events

### Heat Decay Model

`CurrentHeat` should decay naturally over time using a curve rather than a linear step.

Recent speech carries heavier weight. Speech from twenty minutes ago should carry meaningfully less weight than speech from two minutes ago.

Decay rate should be modifiable by context.

Shop work should slow decay — the interruption cost stays elevated longer.

Idle desk time should accelerate decay — the user is more available.

### Important Principle

`CurrentHeat` is not a punishment system.

It is a restraint model that reflects how much Zola has recently asked of the user's attention, and how much margin remains before the next ask becomes an imposition.

---

## 5. Contextual Dampening Modifiers

### Purpose

Apply environment-aware dampening adjustments that reflect the specific interaction context the user is currently in, beyond the base heat model.

Different environments carry different baseline interruption costs that should directly shift how aggressively the dampening system suppresses speech.

### Environment Profiles

**Shop / Hands-Busy Work Context**

- tools running, hands occupied, noise elevated
- baseline dampening modifier: high
- heat decay rate: slow
- events that may still override: security tier 1, urgent safety
- events that should be suppressed: package delivery, routine notifications, low-urgency updates

**Desk / Idle Context**

- seated, quiet, low active cognitive load
- baseline dampening modifier: low
- heat decay rate: fast
- events that may surface: tier 2 and above
- events that may still be deferred: tier 3 unless user has been idle for a meaningful window

**Driving Context**

- active vehicle operation
- baseline dampening modifier: high
- heat decay rate: slow during active driving
- exception: navigation-relevant events may have a lower cost modifier
- events that should be suppressed: anything non-essential to the drive
- events that may still override: urgent safety, navigation conflict, emergency contact

**Active Human Conversation Context**

- user is speaking to another person nearby
- baseline dampening modifier: very high
- events that may still override: genuine safety emergency only
- behavior: Zola should almost never interrupt human-to-human conversation

**Home / Security Context**

- user is present at home, no active task
- baseline dampening modifier: moderate
- events calibrated toward household-relevant delivery
- familiar visitor arrival: may surface as low-interruption notification
- unknown lingering near property: may override dampening

**Vehicle Idle / Passenger Context**

- user is in a vehicle but not driving
- baseline dampening modifier: low to moderate
- more available than during active driving
- conversational interaction more natural

### Important Principle

Contextual modifiers do not replace heat.

They change the rate at which heat accumulates and decays, and they shift the baseline threshold the event must clear.

The same event in a quiet desk context may justify a brief spoken update.

The same event during active shop work may be silently logged.

---

## 6. Override Evaluation System

### Purpose

Evaluate whether a tier 1 urgency event justifies bypassing or partially suspending normal dampening constraints.

This system exists to ensure that genuine emergencies and safety-critical events always reach the user, even when `CurrentHeat` is elevated.

### Override Eligibility Criteria

An event may enter override evaluation if:

- urgency classification is tier 1
- event involves potential physical threat, security risk, or safety hazard
- event involves a close contact in a situation requiring urgent response
- user has explicitly pre-authorized override for this event category

### Override Decision Outputs

**Full Override**

Event bypasses dampening entirely. Zola speaks immediately.

Use when: unknown person at property after midnight, active security escalation, safety event requiring immediate awareness.

**Partial Override**

Event bypasses heat suppression but still selects lowest-cost delivery method. May be spoken briefly or delivered as a high-priority notification rather than a full spoken interruption.

Use when: urgent but not safety-critical. Familiar visitor arriving when user expected them. High-priority message that has been waiting.

**Deferred Override**

Event is flagged for immediate delivery at next natural conversational opening rather than forcing an interruption mid-task.

Use when: event is important but not time-expiring in the next few minutes. User is mid-task but will likely pause soon.

### Critical Safeguard

Override evaluation must remain conservative.

If the override system fires frequently, it is no longer functioning as an override — it has become a bypass, which defeats the purpose of dampening entirely.

Override should feel like the exception, not the rule.

### Important Principle

The override system exists so that Zola never fails the user when it matters most.

It does not exist to make high-urgency events more convenient to surface.

---

## 7. Delivery Channel Selection

### Purpose

Determine which output channel delivers the event, once the decision to surface it has been made.

This layer ensures that the method of delivery matches the event's urgency, the user's current context, and the available endpoints.

### Available Channels

**Spoken Response**

Full voice delivery through the active audio endpoint.

Use for: tier 1 overrides, tier 2 events in low-cost context, user-initiated conversation responses.

**Brief Spoken Update**

Short voice delivery — one to two sentences maximum.

Use for: tier 2 events where speaking is justified but brevity is required by context or heat.

**Passive Status Display**

Silent visual update pushed to an available screen endpoint such as a phone notification, ambient display, or future glasses surface.

Use for: tier 3 events where visibility is useful but spoken interruption is not warranted.

**Silent Log**

Event is recorded in internal memory with no user-facing output.

Use for: tier 4 events, tier 3 events during high heat, deferred events pending summary.

**Deferred Summary Queue**

Event is held and grouped with other deferred events for later summary delivery at a natural conversational moment.

Use for: tier 3 events that would individually not justify interruption but may be worth surfacing together.

**Security / Escalation Workflow**

Structured escalation pathway — presents the user with options such as viewing camera feed, contacting someone, or confirming awareness.

Use for: high-urgency security events that require user decision rather than passive awareness.

### Important Principle

The decision to surface an event and the decision about how to surface it are separate decisions.

An event that justifies surfacing during high heat should still choose the least-interruptive delivery method available.

---

## 8. Deferred Summary Coordination

### Purpose

Collect deferred and suppressed events and surface them as a coherent summary at an appropriate moment, rather than losing them entirely or delivering them as individual interruptions.

### Responsibilities

- maintain a deferred event queue with timestamps and expiration windows
- identify natural conversational openings for summary delivery
- group related events into coherent summaries
- drop expired events that are no longer actionable
- prioritize summary delivery when the user transitions to a lower-cost context
- avoid delivering stale summaries that have lost relevance

### Example Behavior

Three events occurred while the user was working in the shop:

- 2:14 PM — UPS package delivered
- 2:47 PM — Neighbor stopped by briefly
- 3:22 PM — Calendar reminder for a call at 4:00 PM

Rather than three individual interruptions during shop work, Zola surfaces them together when the user steps away:

> "A few things happened while you were working. UPS dropped something off, your neighbor came by around 2:45, and you've got that 4 o'clock call coming up."

### Expiration Management

Events should carry an expiration time beyond which they are no longer worth surfacing.

- package delivery: low expiration urgency — worth surfacing hours later
- calendar reminder for a meeting that has already passed: expired, drop it
- traffic warning for a trip the user has already taken: expired, drop it
- security event from earlier that evening: may still be worth mentioning at lower urgency

### Important Principle

Deferred summary is not the same as dropping an event.

The goal is to find a moment when multiple events can be surfaced with lower total attention cost than delivering them individually would have required.

---

## Core Architectural Principles

---

### Single Decision Authority

The Attention/Relevance Engine is the sole authority over whether Zola speaks proactively.

No worker, no environmental monitor, no background process may bypass this engine and cause Zola to speak or notify.

All proactive output paths pass through relevance scoring, urgency classification, interruption cost analysis, and dampening evaluation before anything reaches the user.

---

### Separation of Sensing, Interpretation, and Decision

The Environmental Perception Layer senses what is happening.

The Contextual Interpretation Layer determines what it means.

The Attention/Relevance Engine decides what to do about it.

These are three distinct responsibilities. None should perform another's function. An event passing from perception through interpretation arrives at this engine as a structured, meaningful signal — not a raw sensor event and not a pre-made notification.

---

### Restraint as a Feature

The default behavior of this engine should lean toward not speaking.

When the engine is uncertain whether an event justifies interruption, the correct answer is to log it silently or defer it rather than surface it and discover it was unwelcome.

An assistant that occasionally surprises the user with something genuinely useful is more valuable than one that speaks constantly and must be tuned out.

---

### User-Initiated Conversation Is Never Suppressed

`CurrentHeat` applies to proactive, system-initiated speech only.

When the user asks a question, makes a request, or initiates conversation, the dampening system does not apply.

The user's own conversational act resets the cost model for that exchange.

---

### Override Is Conservative by Design

The override system should be difficult to trigger and easy to audit.

If override events become frequent, something upstream is miscategorized.

The solution is to fix the urgency classification, not to widen the override criteria.

---

### Heat and State Are Separate Concerns

The Current User State Model describes the user's world. The Attention Dampening System describes Zola's recent behavior. These are distinct. `CurrentHeat` must never be a field in the state model. The dampening system reads the state model to select decay rates and dampening profiles. The engine reads both independently and combines them at the point of decision.

---

## Integration Points

This document connects directly to:

- Contextual Interpretation Layer — provides the interpreted event input that enters relevance scoring
- Autonomous Behavioral Engine — proposes proactive actions that must pass through this engine before execution
- Conversational State and Momentum Layer — provides current conversational context used in interruption cost analysis
- Current User State Model — provides activity, location, and cognitive load signals used in dampening modifiers. The engine reads the Current User State Model and the Attention Dampening System as independent inputs. `CurrentHeat` is not a field in the state model — it is internal system state owned by the dampening system, reflecting Zola's recent output history rather than the user's current condition. The engine combines both at evaluation time.
- Distributed Cognitive Worker Architecture — all worker output enters this engine; no worker may speak directly
- Deferred Cognition and Summary Layer — receives events held by the deferred summary queue
- Trust, Permission, and Privacy Framework — validates that surfacing an event in a given context is permitted
- Distributed Presence Architecture — endpoint selection depends on which devices are active and appropriate

---

## Failure Modes and Safeguards

### Alert Saturation

Risk: `CurrentHeat` fails to suppress low-value events at sufficient rate, and the user experiences repeated unnecessary interruptions. The system erodes trust and the user begins ignoring Zola entirely.

Safeguards:
- heat accumulation must be aggressive relative to decay
- tier 3 events should default to silent log under any moderate heat level
- user dismissal and ignore signals must increase heat substantially
- a persistent pattern of ignored updates should trigger a style and threshold review

### Override Inflation

Risk: the override system is invoked too frequently, effectively removing dampening for a wide class of events and restoring alert spam under a different label.

Safeguards:
- override eligibility criteria must be reviewed if override fires more than once per session on average
- override triggers should be auditable and logged for pattern review
- urgency classification accuracy is the first line of defense

### Stale Deferred Events

Risk: the deferred summary queue accumulates events that expire without being surfaced, creating gaps in the user's awareness that are never recovered.

Safeguards:
- all queued events carry explicit expiration windows
- expired events are dropped with a log entry rather than surfaced late
- summary delivery must be triggered at context transitions, not just held indefinitely
- a queue depth limit should prevent unbounded accumulation

### Context Misclassification

Risk: the engine applies the wrong contextual dampening profile — for example, treating shop work context as desk idle — resulting in over-interruption during high-cost situations.

Safeguards:
- context signals should be sourced from multiple inputs, not a single sensor
- context confidence scoring should determine whether to apply the higher or lower cost modifier when ambiguous
- user signals such as dismissal or positive engagement should provide implicit feedback on context accuracy

### Dampening Starvation

Risk: `CurrentHeat` remains elevated for so long that legitimate tier 2 events never surface, and the user misses information they would have wanted.

Safeguards:
- heat decay rate must be tunable per context
- tier 2 events that have been suppressed beyond their timeliness window should be flagged for review
- deferred summary should catch events that decay past their direct interrupt window

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only — not committed build order.

### Dependencies

- Current User State Model must be capable of producing reliable context signals before contextual dampening modifiers can be applied accurately
- Contextual Interpretation Layer must be operational before relevance scoring has meaningful input
- Deferred Cognition and Summary Layer must exist before deferred summary coordination can function
- Distributed Cognitive Worker Architecture must enforce the no-direct-speech rule before this engine can serve as sole interrupt authority

### Open Questions

- What is the right initial heat accumulation rate per spoken update, and how should it vary by response length?
- How should the engine handle a situation where `CurrentHeat` is high but multiple tier 2 events have accumulated — batch them into one spoken update, or continue to defer?
- What is the minimum viable user feedback loop for implicit heat calibration — and how early can it be introduced?
- How should endpoint availability affect channel selection when the preferred endpoint is not active?
- Should the deferred summary queue have a maximum hold time before it forces a lower-priority delivery attempt?

### Architectural Risks

- Over-suppression in early tuning may make Zola feel unaware, which erodes the perception of intelligence even if the architecture is correct
- Heat model calibration is highly user-dependent — what feels restrained to one user may feel absent to another — requiring a personalization pathway
- Context misclassification is a systematic risk until the Current User State Model achieves reliable multi-signal accuracy
- The override system creates a potential escalation pathway that could be exploited by upstream miscategorization if urgency classification is too permissive

---

## Long-Term End State

The Attention/Relevance Engine and Attention Dampening System eventually evolve toward:

- continuous dynamic interrupt evaluation that requires no manual tuning
- personalized heat curves that have learned individual user rhythm and tolerance
- proactive summary timing that anticipates natural conversational openings
- reliable override behavior that the user has come to trust without having to configure
- seamless multi-endpoint delivery that selects the right surface without explicit routing rules
- implicit calibration through ongoing interaction history

The system should ultimately feel:

- restrained
- trustworthy
- well-timed
- intelligently selective

without losing:

- reliability in genuine emergencies
- responsiveness to user-initiated conversation
- architectural discipline around who holds speech authority
- the principle that attention is finite and worth protecting
