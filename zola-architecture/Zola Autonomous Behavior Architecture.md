# Autonomous Behavior Architecture

### Foundational Architecture for Context-Aware Proactive Intelligence

---

## Vision

Autonomous Behavior enables Zola to move beyond request and response interaction and operate as a context-aware, proactive presence that initiates useful interaction at the right moment, stays silent when it should, and learns over time how to do both better.

The system should eventually feel less like:

> "a tool waiting for a command"

and more like:

> "a system that understands context, respects timing, and participates only when it adds value."

---

## Core Philosophy

### Awareness, Not Automation

Traditional assistants:

- wait for commands
- execute isolated actions
- forget context quickly

Zola should instead:

- maintain persistent contextual awareness
- understand conversational momentum
- decide when silence is appropriate
- re-engage naturally over time

Autonomy should emerge from context, memory, relevance, and behavioral learning — not timers or scripted interruptions.

---

## Long-Term Architectural Pillars

---

## 1. Context Aggregator

### Purpose

Collect and normalize signals from all available input sources into a unified contextual picture. This component does not make decisions — it prepares the information that other components act on.

### Responsibilities

- collect signals from voice, messages, calendar, notifications, device state, weather, and location
- normalize inputs into a consistent internal format
- route normalized signals to the Situational Model
- maintain no decision authority of its own

### Important Principle

The Context Aggregator observes. It does not interpret, judge, or act.

---

## 2. Situational Model

### Purpose

Build a high-level understanding of what is currently happening — not just what events occurred, but what they mean together.

### Responsibilities

- combine signals from the Context Aggregator into a coherent situational picture
- represent context beyond raw events (working late, reflective mood, in the shop, listening to music)
- maintain the current situational state for downstream components
- update continuously as new signals arrive

### Important Principle

Events alone are not context. The Situational Model converts events into meaning.

---

## 3. Attention Model

### Purpose

Maintain a dynamic relevance model across all active topics, goals, and signals so the system understands what matters most at any given moment.

### Responsibilities

- score all active context by relevance, urgency, emotional weight, recency, and engagement
- implement topic heat decay over time
- surface high-heat topics to the Autonomy Engine
- suppress low-heat topics that no longer warrant attention
- track unresolved topics that may re-surface

### Important Principle

Topics decay naturally unless reinforced. The Attention Model ensures Zola's awareness stays current, not accumulated.

---

## 4. Conversational Continuity Engine

### Purpose

Allow Zola to resume past discussions naturally without requiring the user to restate prior context.

### Responsibilities

- track active conversation topics and their suspension state
- support topic return after interruption or time gap
- manage multi-thread conversations
- preserve open loops for later resolution
- provide topic context to the Autonomy Engine when relevant

### Important Principle

Conversations do not end — they pause. Zola should be able to return to them without being asked.

---

## 5. Emotional Regulation Layer

### Purpose

Control the timing, tone, and frequency of autonomous interaction to ensure Zola's behavior feels natural and restrained rather than mechanical or intrusive.

### Responsibilities

- adapt response timing to the user's current emotional and conversational state
- modulate tone to match the context (casual, focused, urgent, reflective)
- regulate interaction frequency to avoid fatigue
- apply restraint during high cognitive-load situations
- adjust pacing based on prior interaction patterns

### Important Principle

Emotional regulation is not about simulating emotion. It is about behaving appropriately for the moment.

---

## 6. Autonomous Trigger Engine

### Purpose

Identify moments when proactive interaction may be appropriate and generate trigger candidates for the Response Governor to evaluate.

### Responsibilities

- detect context changes that may warrant proactive action
- detect time-sensitive events relative to the user's calendar or commitments
- identify behavioral patterns that suggest a proactive opportunity
- detect environmental changes that may be relevant
- generate trigger candidates with urgency and confidence scores
- pass all candidates to the Response Governor without acting on them directly

### Critical Safeguards

- triggers are candidates only — they do not produce output
- the Response Governor holds veto authority over all trigger candidates
- no trigger may bypass the Attention and Relevance Engine
- no trigger may generate speech directly

### Important Principle

The Autonomous Trigger Engine identifies opportunities. It does not take them.

---

## 7. Behavioral Learning Layer

### Purpose

Learn user preferences over time so that autonomous behavior becomes more accurately timed, better toned, and less intrusive as the system matures. This layer does not make decisions — it produces a living Style Profile that other components read when shaping behavior.

### Responsibilities

- observe and record explicit feedback signals from the user
- observe and record implicit feedback signals from user behavior
- maintain a context-scoped Style Profile in the Memory Hierarchy (Behavioral Memory layer)
- issue style reinforcement signals when interactions land well
- issue style penalty signals when interactions land poorly
- provide the current Style Profile to the Emotional Regulation Layer on request
- provide timing tolerance data to the Autonomous Trigger Engine on request
- trigger a periodic identity anchor baseline review via the Autonomous Behavioral Engine
- never write style changes that touch truth handling, privacy boundaries, safety behavior, or core restraint principles

### Feedback Signal Types

**Explicit feedback** — the user says something that directly describes a preference.

Examples:
- "Don't say it like that." → style penalty for current tone in current context
- "Be shorter." → style penalty for response length in current context
- "That's too robotic." → style penalty for formality level in current context
- "Not now." → timing penalty; increase cooldown for proactive triggers in current context
- "Keep me updated." → timing reinforcement; lower suppression threshold for current context

**Implicit feedback** — the user's behavior signals a preference without stating it.

Examples:
- user ignores a proactive update → mild timing penalty; increment ignore counter for this trigger type
- user ignores the same trigger type three or more times → escalate to suppression for that trigger type in this context
- user interrupts or dismisses Zola mid-response → style penalty for length or timing in current context
- user engages positively and asks a follow-up → style reinforcement for tone and timing
- user responds casually or humorously → style reinforcement for lighter tone in current context
- user explicitly corrects a fact → not a style signal; route to Memory Hierarchy write authority, not Behavioral Learning

### Style Profile Structure

The Style Profile is context-scoped, not global. A single universal profile would flatten the user's actual preferences across situations that are genuinely different.

Each context entry should include:

- `contextLabel` — the context this entry applies to (e.g., `shop_work`, `driving`, `desk_focus`, `casual_conversation`, `security_event`)
- `preferredResponseLength` — short, medium, or detailed
- `preferredTone` — casual, direct, warm, administrative, or concise
- `proactiveTolerance` — low, medium, or high (affects trigger candidate threshold in this context)
- `timingCooldownModifier` — a scalar applied to base cooldown values (e.g., 1.5x means wait longer than default before re-triggering in this context)
- `lastUpdated` — timestamp of most recent signal
- `signalCount` — number of signals that have shaped this entry (low signal count = low confidence; high signal count = higher confidence)
- `anchorViolationFlag` — boolean; set true if a proposed style change conflicts with an identity anchor and was rejected

### Write Rules

The Behavioral Learning Layer writes to Behavioral Memory in the Memory Hierarchy. All writes must follow these rules:

- style changes require a minimum signal count before being written as durable preferences (single signals adjust temporary state only)
- no style write may modify entries in Structured Canonical Memory
- no style write may alter truth handling, privacy rules, safety behavior, or restraint principles
- explicit user corrections always override inferred style signals immediately
- the `anchorViolationFlag` must be checked before any write; conflicting writes must be rejected and logged
- all writes must include the context label, signal type, and timestamp for auditability

### Baseline Review Trigger

The Autonomous Behavioral Engine may periodically invoke a baseline review. During a baseline review:

- the current Style Profile is compared against the Identity Seed defined in the Identity and Personality Stability architecture
- any Style Profile entry that has drifted outside identity anchor boundaries is flagged
- flagged entries are either corrected back to boundary or surfaced for explicit user confirmation
- the review result is logged with a timestamp

The purpose is not to reset the Style Profile. The purpose is to ensure learned style changes remain inside the original identity boundaries.

### Important Principle

Behavioral learning may shape how Zola communicates. It may never shape what Zola is willing to do, what she treats as true, or how she handles privacy and user consent.

---

## 8. Response Governor

### Purpose

Act as the final and unconditional authority gate before any autonomous output reaches the user. Every proactive behavior — speech, notification, silent log, deferred summary, or escalation — must be authorized by the Response Governor. No upstream component may produce user-facing output independently.

### Responsibilities

- receive all trigger candidates from the Autonomous Trigger Engine
- evaluate each candidate against the full scoring model before acting
- read the current `CurrentHeat` value from the Attention Dampening System
- read the current Style Profile from the Behavioral Learning Layer
- read the current autonomy mode
- consult the Trust and Permission Framework for privacy and permission constraints
- select the correct output disposition for each candidate
- route authorized candidates to the correct output handler
- hold suppressed candidates in the deferred summary queue when appropriate
- discard stale or expired candidates
- emit a decision log entry for every candidate regardless of outcome
- never speak, notify, or escalate without completing this evaluation sequence

### Candidate Evaluation Sequence

The Response Governor must evaluate every candidate in this order. No step may be skipped.

**Step 1 — Freshness check.**
Verify the candidate has not expired. Each candidate carries an `expiresAt` timestamp. If the current time is past `expiresAt`, discard the candidate and log `EXPIRED`. Do not defer expired candidates.

**Step 2 — Permission check.**
Consult the Trust and Permission Framework. Verify that the candidate's action type is permitted in the current context and endpoint. If permission is denied, suppress and log `PERMISSION_DENIED`.

**Step 3 — Redundancy check.**
Check whether the same or substantially similar information was already surfaced to the user in the recent interaction window. If redundant, suppress and log `REDUNDANT`.

**Step 4 — Autonomy mode check.**
Check the current autonomy mode. Apply mode-level constraints:
- `PASSIVE` — suppress all proactive candidates regardless of score. Log `MODE_PASSIVE`.
- `ASSISTIVE` — allow only candidates with urgency score above the assistive threshold.
- `CONVERSATIONAL` — allow candidates above the standard threshold.
- `FULLY_AUTONOMOUS` — apply standard threshold with no additional mode suppression.

**Step 5 — Heat-adjusted threshold evaluation.**
Compute the effective speech threshold:

```
effectiveThreshold = baseThreshold + CurrentHeat + contextualModifier
```

Where:
- `baseThreshold` is the default relevance score required for output (defined per output type)
- `CurrentHeat` is the current attention burden value from the Attention Dampening System
- `contextualModifier` is a positive or negative adjustment based on the current environment (shop, desk, vehicle, home)

If the candidate's combined score (urgency + relevance + confidence) does not exceed `effectiveThreshold`, proceed to Step 6.

If the candidate's urgency score exceeds the urgency override threshold (defined separately from the standard threshold), skip to Step 7 regardless of heat. Emergency, safety, and security events must not be suppressed by heat alone.

**Step 6 — Disposition decision for below-threshold candidates.**
Candidates that do not pass Step 5 are not simply discarded. The Governor must choose one of:
- `SILENT_LOG` — record the event internally with no user-facing output
- `DEFER` — place in the deferred summary queue with a `deferUntil` timestamp and a grouping tag
- `DISCARD` — drop entirely (used only for low-confidence, low-value, expired, or redundant candidates already caught above)

Defer when the candidate has meaningful value that may be worth surfacing later as part of a grouped summary. Silent log when the event should be recorded but is unlikely to be worth surfacing even in a summary. Discard only when the candidate has no residual value.

**Step 7 — Output disposition selection for above-threshold candidates.**
Select the correct output mode:

- `SPEAK` — deliver as spoken output through the active voice endpoint
- `NOTIFY` — deliver as a silent push notification to the device
- `PASSIVE_DISPLAY` — update a status surface without interrupting the user
- `ESCALATE` — trigger a security or urgency workflow

Selection rules:
- prefer `SPEAK` only when the user is likely available and the endpoint supports voice
- prefer `NOTIFY` when the user is likely occupied or the endpoint is not voice-primary
- prefer `PASSIVE_DISPLAY` for low-urgency informational updates
- use `ESCALATE` only when urgency score exceeds the escalation threshold and the candidate type is security or safety

**Step 8 — Route and emit.**
Route the candidate to the selected output handler. Increment `CurrentHeat` by the appropriate amount for the output type (speech increments heat more than a notification; a passive display increments least). Emit a complete decision log entry.

### Heat and Scoring Reference

`CurrentHeat` increases from:
- Zola speaking (large increment)
- sending a notification (medium increment)
- passive display update (small increment)
- user dismissing or ignoring a prior output (medium increment)
- noisy or high-cognitive-load environment (applied as contextual modifier, not heat)

`CurrentHeat` decreases from:
- time passing without output (continuous decay)
- quiet environment detected (faster decay rate)
- user-initiated conversation (significant decay)
- user asking follow-up questions (moderate decay)
- explicit user permission to continue updating (sets heat to near-zero)

`contextualModifier` values by environment:
- `SHOP` — positive modifier (raises threshold; stronger suppression)
- `DRIVING` — positive modifier (raises threshold significantly; only safety and navigation may pass)
- `DESK_IDLE` — negative modifier (lowers threshold; user is likely available)
- `HOME_SECURITY` — negative modifier for security events only (lowers threshold for unknown person or intrusion candidates)

### Urgency Override Threshold

Candidates with urgency scores above the urgency override threshold bypass heat-adjusted evaluation and go directly to output disposition. This threshold must be set conservatively. Only genuine emergency, safety, and security events should qualify.

Examples of events that should cross the urgency override threshold:
- unknown person near shop after midnight
- security alarm trigger
- severe weather requiring immediate action
- safety-critical vehicle alert

Examples of events that must not cross the urgency override threshold regardless of urgency score:
- package delivered
- calendar reminder for a low-priority event
- weather update for non-severe conditions
- music or media suggestions

### Deferred Summary Queue

Candidates placed in `DEFER` are held in the deferred summary queue. The queue must:

- store each candidate with its original urgency, relevance, grouping tag, and `deferUntil` timestamp
- group candidates with the same grouping tag for combined delivery
- deliver grouped summaries when `deferUntil` is reached and the Response Governor determines the user is available
- allow the Deferred Cognition and Summary Layer to compose the actual summary language from grouped candidates
- expire queue entries that have been held past their maximum hold duration without delivery

Example grouped delivery:
> "Three things happened while you were in the shop. Two packages arrived, and your neighbor stopped by earlier."

### Decision Log Requirements

Every candidate that passes through the Response Governor must produce a log entry. The log entry must include:

- `candidateId`
- `candidateType` (environmental, conversational, calendar, security, etc.)
- `urgencyScore`
- `relevanceScore`
- `confidenceScore`
- `currentHeatAtEvaluation`
- `effectiveThreshold`
- `autonomyMode`
- `permissionResult`
- `redundancyResult`
- `freshnessResult`
- `finalDisposition` (SPEAK, NOTIFY, PASSIVE_DISPLAY, ESCALATE, DEFER, SILENT_LOG, DISCARD)
- `suppressionReason` (if suppressed)
- `deferGroupTag` (if deferred)
- `heatIncrementApplied` (if output was produced)
- `timestamp`

These logs must be queryable so that any output or silence can be explained after the fact.

### Critical Safeguards

- no component other than the Response Governor may call speech, notification, or escalation APIs
- user-initiated conversation always bypasses proactive suppression — direct questions from the user are never held by the governor
- emergency and security candidates must not be permanently suppressed by heat alone; the urgency override threshold exists for this reason
- the Response Governor must never invent, embellish, or alter the content of a candidate; it routes authorized content only
- a candidate rejected in Step 2 (permission denied) must never be retried through an alternate path

### Important Principle

The Response Governor does not look for reasons to speak. It looks for reasons to stay silent, and only authorizes output when no sufficient reason to stay silent remains.

---

## Autonomy Modes

Zola supports four distinct autonomy modes. Each mode defines what the Autonomous Trigger Engine is permitted to surface and what the Response Governor is permitted to pass through. Modes may be set explicitly by the user or inferred from context by the Situational Model.

---

### Passive Mode

**Trigger behavior:** The Autonomous Trigger Engine continues to observe and score context, but all proactive candidates are suppressed at Step 4 of the Response Governor evaluation. No candidates advance to output disposition.

**What is allowed:**
- responding to direct user questions and commands
- silent logging of environmental and contextual events
- updating the deferred summary queue for possible later delivery

**What is suppressed:**
- all proactive speech
- all proactive notifications
- all passive display updates
- all escalations except those that cross the urgency override threshold

**Urgency override:** Security and safety events that cross the urgency override threshold may still interrupt Passive Mode. This is intentional. Passive Mode suppresses unnecessary interruptions — it does not disable emergency awareness.

**When to infer this mode:**
- user is in an active meeting (calendar signal)
- user is engaged in extended human conversation (multi-speaker detection)
- user has explicitly said "not now" or "quiet" recently
- do not disturb is active on the device

---

### Assistive Mode

**Trigger behavior:** The Autonomous Trigger Engine surfaces candidates, and the Response Governor allows only those with urgency scores above the assistive mode threshold. Low-value and informational candidates are suppressed.

**What is allowed:**
- time-sensitive calendar or commitment reminders
- meaningful security or environmental alerts below the urgency override threshold
- high-relevance contextual updates tied to an active user goal
- responses to direct questions

**What is suppressed:**
- general informational updates
- weather or traffic unless directly tied to an imminent departure
- suggestions, recommendations, or casual proactive topics
- anything with urgency score below the assistive threshold

**When to infer this mode:**
- user is in the shop but not in an active meeting
- user is driving
- user has not explicitly requested fuller assistance
- default mode when no stronger signal is present

---

### Conversational Mode

**Trigger behavior:** The Autonomous Trigger Engine surfaces candidates normally, and the Response Governor applies the standard heat-adjusted threshold. A broader range of relevant updates may pass through.

**What is allowed:**
- all Assistive Mode behaviors
- contextually relevant informational updates
- conversation continuity suggestions (unresolved topics, relevant callbacks)
- proactive suggestions tied to active projects or goals
- low-urgency environmental updates when heat is low

**What is suppressed:**
- candidates that fail the heat-adjusted threshold
- candidates that are redundant with recent output
- candidates with low confidence scores

**When to infer this mode:**
- user is idle at desk
- user is in a relaxed conversational state
- user has recently engaged positively with proactive output
- user has said "keep me updated" or similar

---

### Fully Autonomous Mode

**Trigger behavior:** The Autonomous Trigger Engine operates at full sensitivity. The Response Governor applies the standard heat-adjusted threshold with no additional mode suppression. The full range of contextual monitoring is active.

**What is allowed:**
- all Conversational Mode behaviors
- broader environmental awareness surfacing
- pattern-based proactive suggestions
- memory resurfacing when contextually appropriate
- ambient contextual awareness at natural conversational pacing

**What is suppressed:**
- candidates that fail the heat-adjusted threshold (heat still applies — Fully Autonomous Mode does not disable dampening)
- candidates that fail permission or privacy checks
- redundant candidates

**When to use:**
- user has explicitly enabled this mode
- this mode should not be inferred automatically without explicit user activation

**Important constraint:** Fully Autonomous Mode does not disable the Response Governor, the Attention Dampening System, or the Trust and Permission Framework. It widens the candidate set — it does not remove the authority structure.

---

### Mode Transition Rules

- explicit user commands transition mode immediately (highest priority)
- context-inferred transitions must have sufficient signal confidence before applying
- transitions from a higher-permission mode to a lower-permission mode (e.g., Conversational to Passive) take effect immediately
- transitions from a lower-permission mode to a higher-permission mode (e.g., Passive to Conversational) require either explicit user action or sustained contextual signal
- the current mode must be exposed in the decision log for every Response Governor evaluation
- mode history should be retained in session state for observability

---

## System Overview

```text
                ┌────────────────────┐
                │  External Inputs   │
                │────────────────────│
                │ Voice              │
                │ SMS                │
                │ Gmail              │
                │ Calendar           │
                │ Weather            │
                │ Location           │
                │ Sensors            │
                │ Device State       │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Context Aggregator │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Situational Model  │
                └─────────┬──────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
┌────────────────┐ ┌──────────────┐ ┌────────────────┐
│ Attention Model│ │ Memory System│ │ Emotional Layer│
└────────┬───────┘ └──────┬───────┘ └────────┬───────┘
         │                │                  │
         └────────────────┼──────────────────┘
                          ▼
                ┌────────────────────┐
                │ Autonomy Engine    │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Response Governor  │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ User Interaction   │
                └────────────────────┘
```

---

## Core Architectural Principles

---

### Single Decision Authority

Every proactive output must pass through one authoritative gate — the Response Governor. No component upstream of the Response Governor may produce user-facing behavior directly.

---

### Silence Is a Valid Output

The system should not optimize for interaction frequency. Staying silent when the value of speaking is insufficient is a correct and intended behavior, not a failure.

---

### Autonomy Must Not Override User Intent

Zola must never manipulate emotions, create false urgency, invent memories, override explicit user instructions, or force engagement. Autonomy operates within the boundaries of user intent — it does not supersede it.

---

### Interruption Cost Is Real

Every proactive interruption carries a cost to the user's attention and trust. The system must treat that cost as real and require that the value of speaking exceed it before acting.

---

## Integration Points

This document connects directly to:

- Zola Master Architecture Plan
- Attention and Relevance Engine (Section 9 and 9a)
- Conversational Continuity Architecture
- Memory Hierarchy Architecture
- Environmental Awareness Architecture
- Trust, Permission, and Privacy Framework
- Identity and Personality Stability (Section 18)
- Distributed Cognitive Worker Architecture (Section 20)

---

## Failure Modes and Safeguards

### Over-Triggering

Risk: The Autonomous Trigger Engine generates too many candidates, causing the Response Governor to pass too many through and the user to experience notification fatigue.

Safeguards:
- heat-based dampening raises the speech threshold after recent interruptions
- behavioral learning records ignored interactions and increases cooldowns
- autonomy mode controls the baseline trigger sensitivity

### Authority Bypass

Risk: A component upstream of the Response Governor produces user-facing output directly, bypassing the authority gate.

Safeguards:
- no component other than the Response Governor may call speech or notification APIs
- all output paths must be routed through the Response Governor
- observability logs must prove the source of every output

### Behavioral Drift

Risk: The Behavioral Learning Layer adjusts tone or timing in ways that conflict with Zola's identity anchors.

Safeguards:
- behavioral learning may adjust style and timing only — not truth, privacy, or restraint
- periodic baseline review compares learned behavior against identity anchors
- explicit user corrections override learned preferences immediately

### Stale Context Acting

Risk: The Autonomy Engine triggers on outdated situational context, producing irrelevant or confusing proactive output.

Safeguards:
- the Situational Model must timestamp all context
- the Response Governor checks context freshness before allowing output
- stale candidates are suppressed, not deferred

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only.

### Dependencies

- Attention and Relevance Engine must exist before the Response Governor can evaluate candidates
- Attention Dampening System must be integrated before autonomous modes are enabled
- Memory Hierarchy Architecture must be stable before the Behavioral Learning Layer can write preference signals
- Trust and Permission Framework must define autonomy boundaries before Fully Autonomous Mode is activated

### Open Questions

- Should autonomy mode be user-controlled, context-inferred, or both?
- How should the Response Governor handle candidates that expire while being held for deferred summary?
- What is the minimum confidence threshold for a trigger candidate to reach the Response Governor?
- Should behavioral learning signals be visible to the user for review and correction?

### Architectural Risks

- The Response Governor is the most consequential single component in this system — underbuilding it creates a bottleneck that is difficult to fix later
- Behavioral learning without strong identity anchor constraints risks gradual persona drift
- Autonomy modes that are too coarse may not reflect the nuance of real user contexts

---

## Long-Term End State

Autonomous Behavior eventually evolves toward:

- cross-domain reasoning across memory, environment, and conversation
- continuous background monitoring without active resource cost
- long-term goal tracking across sessions and days
- predictive assistance that anticipates needs before they are stated
- ambient conversational awareness that feels natural and unintrusive

The system should ultimately feel:

- intentional
- contextually aware
- appropriately timed
- restrained by default
- trustworthy over time

without losing:

- user control and override authority
- truth and factual reliability
- privacy boundaries
- identity stability
- the principle that silence is a valid and respected output
