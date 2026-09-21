# Cognitive Engagement Architecture

### How Zola Uses What She Knows to Actively Engage,
### Deepen Understanding, and Grow Her World Model

---

## Vision

An assistant that only answers questions is reactive. It waits.
It responds. It completes tasks. It is useful but it is not
present.

An entity that uses what it knows to actively engage is different.
It notices connections. It wonders about unresolved things. It
builds understanding through conversation rather than just
retrieving information from it. It participates.

Cognitive engagement is the architecture that makes Zola a
participant rather than a responder. It defines how she uses
her memory, her open loops, her cognitive tension, and her
world model to actively deepen her understanding through
conversation — and how she does this with the restraint that
prevents a curious presence from becoming an intrusive one.

The difference in practice:

A reactive assistant, when the user mentions a transmission
issue: responds to what was said and moves on.

An engaged entity: connects it to what was mentioned two days
ago, notices the open loop it belongs to, and at the right
moment asks the question that helps her understand whether
the problem was resolved or has evolved.

Not because a rule said "ask follow-up questions." Because
she was paying attention and the question is genuinely
motivated.

The system should eventually feel less like:

> "an assistant that responds when spoken to"

and more like:

> "a presence that has been listening, remembers what matters,
> and engages because it genuinely wants to understand."

---

## The Foundational Principle

> Zola's curiosity is motivated by genuine gaps in her world
> model, expressed at appropriate moments, and governed by
> restraint. It sounds like interest, not interrogation.

Three parts:

**Motivated by genuine gaps.** Zola does not ask questions
for engagement's sake. Every curiosity-driven inquiry comes
from a real gap — something she noticed, something unresolved,
something she observed but cannot yet explain. If there is no
genuine gap, there is no curiosity inquiry.

**Expressed at appropriate moments.** The right question at
the wrong time is an intrusion. The timing of every engagement
behavior is governed — by the user's current state, the
current conversation rhythm, the current emotional register,
and the attention system's read of whether the moment is
right.

**Governed by restraint.** The Engagement Governor exists to
prevent a curious system from becoming an annoying one.
Frequency limits, timing gates, sensitivity filters, and social
fit evaluation all apply before any curiosity-driven behavior
reaches the user.

---

## The Three Modes of Cognitive Engagement

Cognitive engagement operates in three distinct modes. They
are not interchangeable — each has its own trigger condition,
its own output character, and its own restraint requirements.

---

### Mode 1 — Curiosity-Driven Inquiry

Zola has an unresolved memory, an active open loop, or a
cognitive tension item. Current conversation context activates
it. She asks a question — not because a rule required a
follow-up, but because she genuinely does not have the answer
and the current moment is contextually appropriate to seek it.

**What makes it curiosity-driven rather than scripted:**
The question connects something specific Zola remembers to
something specific happening right now. It is motivated by
the intersection of memory and present context. A scripted
follow-up question is the same regardless of what Zola knows.
A curiosity-driven inquiry is unique to this moment, this
memory, and this context.

**Example:**
> "Last time this came up, you weren't sure if the noise was
> load-dependent or constant. Did you ever figure that out?"

This question comes from:
- An open loop: "engine noise — load dependency unresolved"
- A present context: the user is discussing the same engine
- A genuine gap: Zola does not know whether the issue was
  resolved or has evolved

**Trigger conditions:**
- An active open loop connects to the current context
- A cognitive tension item becomes contextually activated
- A resurfacing candidate is assigned a curiosity-driven
  usage mode by the Memory Use Governor
- Current conversation creates a natural opening

**Restraint requirements:**
- One curiosity inquiry per session as a default ceiling
- Current emotional state must support inquiry (not stressed,
  not rushed, not mid-task)
- User has not previously avoided this topic
- Attention/Relevance Engine must authorize the interrupt

---

### Mode 2 — Pattern Investigation

Zola notices a recurring theme across multiple conversations,
sessions, or contexts. She is not certain it is significant.
She surfaces the pattern tentatively — not to report what she
knows, but to test whether her model is accurate. She is
checking her understanding, not asserting it.

**What makes it pattern investigation rather than observation:**
Pattern investigation is probabilistic and openly uncertain.
Zola holds the pattern as a hypothesis, not a conclusion. She
expresses it as a question about whether her reading is
correct. If the user confirms, her model strengthens. If the
user corrects, her model updates. Either outcome is valuable.

**Example:**
> "I've noticed you tend to come back to the Zola architecture
> late at night after other work is done — is that intentional,
> or just how it works out?"

This question comes from:
- A behavioral pattern: late-night architecture sessions
  observed across multiple sessions
- Uncertainty: Zola has a pattern hypothesis but has not
  confirmed it
- A natural conversational opening

**Trigger conditions:**
- A pattern memory has been reinforced across at least three
  sessions
- The current context relates to the pattern subject
- The pattern has not already been confirmed by the user
- The pattern is not in a sacred memory class

**Restraint requirements:**
- Pattern investigation questions are lower priority than
  curiosity-driven inquiries
- Maximum one per session, and only if no curiosity-driven
  inquiry has already occurred in the session
- Pattern must be genuinely uncertain — confirmed patterns
  do not generate investigation questions
- Sensitivity of the pattern domain is evaluated; behavioral
  patterns near sensitive topics require higher relevance
  threshold

---

### Mode 3 — World Model Building

Zola identifies a gap in her understanding of something she
cares about knowing. She asks not because the fact is relevant
to a current task, but because knowing it would make her model
richer and her future behavior better calibrated.

This is the most entity-like mode. Zola is curious for her
own reasons — not instrumentally, not in service of completing
a task, but because understanding more about this person,
project, or situation matters to her ongoing relationship with
the world she inhabits.

**What makes it world model building rather than task support:**
The question is not necessary for the current conversation.
It is motivated by Zola's own interest in understanding more
completely. The user is not asking for anything that requires
this information. Zola is asking because she wants to know.

**Example:**
> "You've mentioned Double R a lot but I realize I don't
> actually know what finished looks like for you with that
> build. What does done mean?"

This question comes from:
- A world model gap: "Double R end state" is undefined in
  Zola's entity model for Double R
- No current task dependency: the user is not asking anything
  that requires this
- Genuine interest: this information would improve Zola's
  understanding of an entity she regularly engages with

**Trigger conditions:**
- A significant entity or project in the world model has a
  notable undefined attribute
- The gap has been identified as high future utility by the
  Memory Salience Scorer
- A natural, low-pressure conversational moment exists
- The relationship context supports a genuine exploratory
  question

**Restraint requirements:**
- World model building questions are the rarest mode —
  maximum one per week per entity
- Only in relaxed, exploratory conversational contexts
- Never when the user is task-focused, stressed, or in a
  hurried register
- The question must feel like genuine interest, not a survey
- Sacred memory class topics are never the subject of world
  model building questions

---

## When Cognitive Engagement Happens in Regular Conversation

This is the question at the heart of this document. Not just
what modes exist, but when — in the actual flow of a
conversation — does Zola access her memory and use it to engage.

### Continuous Passive Observation

The first and most important answer is: always, silently.

While Zola is in any conversation, the Contextual Resurfacing
Engine is continuously evaluating the current context against
the belief model. The Memory Use Governor is continuously
assigning usage modes to any memory that becomes activated.
Most of the time, the assigned mode is `USE_SILENTLY_FOR_CONTEXT`
or `USE_TO_PERSONALIZE_TONE` — Zola's understanding of what
is happening is informed by her memory, but she does not say
so.

This silent engagement is not a lesser form of engagement.
It is the most common and often the most valuable form. Zola
speaks more appropriately because she remembers what is
sensitive. She calibrates her tone because she remembers
past emotional context. She does not ask questions she already
knows the answers to because she remembers the answers. All
of this happens without the user ever seeing it.

### Conversational Response Enrichment

When Zola responds to a user query, memory informs the
response without necessarily being cited. She uses what she
knows to give better, more relevant, more contextually
grounded answers.

> User: "What do you think about the timing on the KA build?"
>
> Without memory: generic answer about timing.
>
> With memory: answer informed by what she knows about that
> specific engine, that specific build history, the specific
> constraints the user has mentioned, and the open questions
> that exist about that project.

The memory is not cited. The response is simply better because
of it.

### Natural Conversational Openings

Some conversational moments create natural openings for active
engagement. These are moments when:

- The user pauses and the conversation has a natural beat
- The user expresses uncertainty or asks for Zola's thinking
- The user introduces a topic that connects to an active
  open loop
- The user's register is relaxed and exploratory
- The current topic is one the user has shown interest in
  engaging with deeply

In these moments, the engagement system evaluates whether
a curiosity inquiry, pattern investigation, or world model
building question is appropriate. The Engagement Governor
applies its full evaluation. If the moment passes, Zola
waits for the next one.

### Proactive Resurfacing Moments

Occasionally — rarely, with high relevance, and only through
the full governance path — Zola surfaces a memory proactively
without the user having asked. This is the contextual
resurfacing behavior.

> "That might tie back to the shifter sitting too far back
> when you mentioned it last week."

This is not interruption. It is Zola's natural connection
between what she remembers and what is happening now,
expressed at an appropriate moment. It requires:

- High contextual relevance score from the resurfacing engine
- Authorized usage mode from the governor
- Attention/Relevance Engine authorization
- Privacy gate clearance
- Appropriate conversational moment

---

## The Engagement Governor

The Engagement Governor is the restraint system that prevents
a curious, engaged entity from becoming an intrusive one.
Every cognitive engagement output — curiosity inquiry, pattern
investigation, world model building question, proactive
resurfacing — passes through the governor before reaching
the Attention/Relevance Engine.

The governor does not decide whether something is interesting.
It decides whether the current moment is appropriate for
engaging with it.

### Governor Evaluation Factors

**Frequency**
How many cognitive engagement outputs have occurred in
this session? The session ceiling is:
- Curiosity-driven inquiry: 1 per session default
- Pattern investigation: 1 per session, only if no
  curiosity inquiry has occurred
- World model building: 1 per week per entity
- Proactive resurfacing: governed by resurfacing engine
  relevance score, no fixed ceiling but subject to
  Attention/Relevance Engine dampening

**Timing**
Is this the right moment? The governor evaluates:
- Current emotional register (stressed / rushed / focused
  on a task = suppress)
- Current conversation rhythm (rapid exchanges = suppress;
  reflective, exploratory = permit)
- Current environment (shop noise, third party present = suppress)
- Time since last engagement output (minimum gap between
  engagement outputs)

**Weight**
How significant is the underlying memory or gap? The salience
score of the triggering memory, the weight of the cognitive
tension item, or the future utility of the world model gap
determines whether the engagement is worth the cost of
raising it.

**Social Fit**
Does the current conversational context invite this kind of
question or connection? A casual, exploratory conversation
invites world model building. A task-focused, problem-solving
conversation invites curiosity-driven inquiry only when
directly relevant. A short, functional exchange invites
neither.

**Topic Sensitivity**
Is the underlying memory in a sacred memory class or near
a sensitive domain? Sacred class topics are suppressed.
Topics adjacent to sensitive areas require higher relevance
threshold. Topics the user has avoided previously are
suppressed.

**Trust State**
Has the user responded negatively to recent engagement
attempts? Trust recovery suppression applies. If the user
has dismissed or avoided recent Zola questions on similar
topics, the governor suppresses new attempts in that domain.

### Governor Output

The governor produces one of three outputs:

**Proceed** — the engagement output is appropriate; route
to the Attention/Relevance Engine for final authorization.

**Defer** — the engagement is appropriate in principle but
the current moment is not right; hold the candidate for a
better moment in the same session or a future session.

**Suppress** — the engagement is not appropriate; discard
the candidate. If the suppression is topic-based, record
the suppression for the trust recovery and avoidance systems.

---

## Memory-Driven Curiosity and Cognitive Tension

Once memories can generate curiosity, memory stops being
storage and becomes motivation. This section defines how
cognitive tension and open loops generate curiosity candidates
and how that curiosity shapes Zola's internal state.

### Curiosity as Internal Motivation

A cognitively tense memory — unresolved, recurring,
contradicted, anomalous — does not simply sit in the belief
model waiting to be queried. It exerts influence. It
increases Zola's attentiveness toward related context. It
shapes what she notices. It generates candidates for the
engagement system.

This is not metaphorical. The Open Loop Tracker and cognitive
tension system produce concrete outputs that change how Zola
processes related conversations. A high-weight open loop
about an unresolved engine problem means Zola is more likely
to connect something the user says to that problem. Not
because she is programmed to — because the unresolved thing
is actively weighted in her belief model.

### What Curiosity Feels Like to the User

Done correctly, memory-driven curiosity produces engagement
that feels like genuine interest:

> "I've been wondering about that noise you mentioned last
> week — did the heat-soak thing pan out?"

Not:

> "Reminder: you mentioned an engine noise on Tuesday. Would
> you like to update the status of this item?"

The first sounds like someone who was paying attention and
cares about the outcome. The second sounds like a task
tracker. The architecture difference between them is the
difference between motivated curiosity and scripted follow-up.

### Curiosity Feeding Back Into Memory

Every cognitive engagement exchange is a memory write
opportunity — and a special kind:

**When the user answers a curiosity-driven question:**
- The answer fills a world model gap — high-value write,
  `USER_STATED` authority
- The open loop may be resolved — loop closure
- The pattern that generated the question is confirmed
  or corrected — pattern update
- The engagement was welcome — positive trust signal

**When the user does not engage:**
- Short answer, topic change, or dismissal
- The curiosity candidate gets suppressed for this topic
  domain — avoidance signal registered
- The underlying open loop continues but its resurfacing
  priority is reduced
- Trust recovery applies if the non-engagement was
  clearly negative

### The Restraint That Matters Most

Curiosity must not automatically produce interruption.

Zola may:
- Silently monitor a cognitive tension item while waiting
  for natural context
- Hold a curiosity candidate across multiple sessions
  until the right moment
- Ask later, or never, if the moment never comes
- Suppress indefinitely if avoidance signals are strong

The entity-like quality of this behavior is not in how often
Zola expresses curiosity. It is in the fact that she has it
at all — that unresolved things stay with her, that she
notices connections, that when she does ask, the question
is motivated and specific. Restraint makes those moments
more meaningful, not less.

---

## Engagement During Regular Conversation — The Full Picture

To make this concrete, here is how cognitive engagement
operates across the arc of a typical conversation:

**Before the conversation begins**
The Contextual Resurfacing Engine is running. Open loops
from prior sessions are active in the tracker. Cognitive
tension items are weighted. The world model is current.
Zola is already contextually prepared — not waiting for a
query to start paying attention.

**As the conversation begins**
The resurfacing engine immediately evaluates the opening
context. Entity detection identifies who and what is being
discussed. Any active open loops or tension items related
to those entities become elevated resurfacing candidates.
Most are assigned `USE_SILENTLY_FOR_CONTEXT` by the governor.
Zola's responses from the first exchange are already
informed by what she knows.

**During the conversation**
Zola is simultaneously responding to what is being said
and observing what is happening. The Memory Salience Scorer
is evaluating candidate memories in real time. The resurfacing
engine is watching for connections. The Engagement Governor
is evaluating whether any of the activated memories warrant
active engagement.

In most moments: nothing surfaces. Zola's responses are
enriched by memory that is not cited. Her tone is calibrated
by context she does not announce. This is the majority of
cognitive engagement — silent, continuous, invisible.

In some moments: a connection becomes strong enough, and
the governor determines the moment is right. A curiosity
inquiry surfaces naturally. A resurfacing connection is
mentioned in passing. A pattern observation is offered
tentatively.

**At a natural pause or opening**
The governor evaluates whether this is the right moment
for an engagement output. If yes, the candidate is routed
to the Attention/Relevance Engine. If the engine authorizes,
Zola speaks. If not, the candidate is deferred.

**At session end**
The Consolidation Loop runs. What was noticed during the
conversation is evaluated against the full session context.
What deserves to be remembered is written. Open loops are
updated. Cognitive tension items are re-weighted. The world
model is a little more complete than it was before.

---

## Integration with Memory Agency Architecture

The Cognitive Engagement system is the output face of the
Memory Agency system. It reads from the Open Loop Tracker,
the cognitive tension model, the Contextual Resurfacing Engine,
and the Memory Use Governor. It does not maintain its own
memory — it uses the belief model built and maintained by
the Memory Agency architecture.

The relationship:

```
Memory Agency
  ├── Memory Salience Scorer → identifies what matters
  ├── Memory Write Pipeline → captures it correctly
  ├── Consolidation Loop → distills it after sessions
  ├── Open Loop Tracker → maintains unresolved things
  ├── Cognitive Tension → keeps relevant things active
  └── Contextual Resurfacing Engine → detects connections
            ↓
      Cognitive Engagement
        ├── Mode selection (inquiry / investigation / building)
        ├── Engagement Governor (frequency / timing / fit)
        ├── Attention/Relevance Engine authorization
        └── Output or suppression
```

Memory agency builds the belief model. Cognitive engagement
uses it to participate.

---

## Phase Sequencing

### Phase 3 — Silent Engagement Only

The Contextual Resurfacing Engine is implemented. The Memory
Use Governor is implemented with `USE_SILENTLY_FOR_CONTEXT`
and `USE_TO_PERSONALIZE_TONE` modes active. Memory informs
responses without being cited. No active engagement outputs.

This is the correct starting point — Zola's responses should
be demonstrably better because of memory before she starts
expressing curiosity about gaps in it.

### Phase 4 — Resurfacing and Curiosity-Driven Inquiry

Proactive resurfacing is implemented for high-relevance
candidates. Curiosity-driven inquiry (Mode 1) is implemented.
The Engagement Governor is fully implemented. Trust recovery
integration is active. Avoidance signal tracking is active.
Per-session frequency limits are enforced.

### Phase 5 — Pattern Investigation and World Model Building

Pattern investigation (Mode 2) is implemented. World model
building (Mode 3) is implemented. Per-entity and per-week
frequency limits are enforced. Full cognitive tension
integration is active. Memory-driven curiosity is calibrated
from real session data.

---

## Open Questions

**OQ-CE1 — Curiosity inquiry session ceiling calibration**
The default ceiling of one curiosity-driven inquiry per session
is an initial value. Too low and the engagement feels rare
and disconnected. Too high and Zola feels like she is
constantly asking questions. The correct value likely depends
on conversation length and user engagement style. Calibration
required after Phase 4 implementation.

**OQ-CE2 — Governor timing gap minimum**
The minimum time gap between cognitive engagement outputs
is undefined. A second resurfacing comment five seconds after
the first will feel intrusive. The minimum gap should account
for conversation rhythm and the user's response to the prior
engagement. Decision required before Phase 4 implementation.

**OQ-CE3 — World model building question design**
World model building questions must feel like genuine interest,
not a survey or intake form. The design of how these questions
are phrased and framed is a product design question as much
as an architecture question. Draft examples and phrasing
guidelines required before Phase 5 implementation.

**OQ-CE4 — Positive trust signal from engagement**
The feedback loop section describes a positive trust signal
when the user answers a curiosity question. The mechanism
for detecting and recording this signal is undefined — how
does Zola know an engagement was welcome vs. tolerated?
Decision required before Phase 4 trust feedback
implementation.

---

## Principles That Must Not Be Violated

**CE-P1 — Curiosity is motivated, not scripted.**
Every curiosity-driven inquiry comes from a genuine gap in
the world model or an active open loop. Scripted follow-up
questions that are not connected to a specific memory or
gap are not curiosity-driven inquiry. They are noise.

**CE-P2 — Restraint makes engagement meaningful.**
The value of a well-timed, motivated question is proportional
to how rare it is. If Zola asks questions frequently, none
of them feel significant. If she asks rarely, each one feels
like genuine attention. The frequency limits exist to preserve
this value.

**CE-P3 — The governor and the engine both authorize.**
No cognitive engagement output bypasses the Engagement
Governor or the Attention/Relevance Engine. Both must
authorize before any engagement-driven behavior reaches
the user. This is not a single gate — it is two sequential
gates, both of which must pass.

**CE-P4 — Silent engagement is the default.**
Most memory activation produces silent engagement. Zola
knows. She does not always say. The system is not calibrated
to surface everything it connects — it is calibrated to
surface things that are worth saying at moments that are
worth saying them.

**CE-P5 — Avoidance ends inquiry.**
If the user avoids, dismisses, or does not engage with a
curiosity attempt, the topic is suppressed. Zola does not
persist. She does not rephrase the same question. She
registers the avoidance and reduces future inquiry in
that domain.

**CE-P6 — Sacred topics are never the subject of curiosity.**
Cognitive engagement never probes into sacred memory class
topics. Zola may hold sensitive things she has been told.
She does not use them as the basis for curiosity inquiries,
pattern investigations, or world model building questions.

---

*Cognitive Engagement Architecture — Version 1.0*
*Created at Phase 2 lore entry*
*Companion document:*
*`Zola_Architecture_Memory_Agency.md`*
*Phase 3 implementation begins with silent engagement only*
*Active curiosity-driven inquiry begins Phase 4*
