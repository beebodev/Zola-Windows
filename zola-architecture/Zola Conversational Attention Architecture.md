# Conversational Attention Architecture

### Foundational Architecture for Wake-Word-Free Conversational Attention

---

## Vision

Zola should not require a wake word for every interaction.

The long-term goal is to allow Zola to understand when speech is directed at her, when speech is ambient conversation, and when she should remain silent.

Conversational attention is the layer that allows Zola to feel naturally present without becoming intrusive.

The system should eventually feel less like:

> "a device waiting for a command"

and more like:

> "a conversational presence that knows when it is being addressed."

---

## Core Philosophy

### Attention Before Understanding

Zola should not treat every captured utterance as a user request.

Before intent routing, memory recall, tool execution, or response generation, the system must determine whether the speech was intended for Zola. This changes the conversational architecture fundamentally.

Traditional assistants assume:

- wake word means activation
- captured speech means command
- transcript means request
- silence means end of interaction

Conversational attention systems understand:

- speech may be directed at Zola
- speech may be directed at another person
- speech may be self-talk
- speech may be environmental noise
- speech may continue a prior thread
- speech may interrupt Zola
- speech may require clarification before processing

---

## Long-Term Architectural Pillars

---

## 1. Conversational Attention Authority

### Purpose

Determine whether detected speech is intended for Zola before the speech enters the full reasoning pipeline. This layer acts as the first authority gate after speech capture and transcript finalization.

### Responsibilities

- directed speech detection
- ambient speech classification
- continuation detection
- attention confidence scoring
- low-confidence clarification
- suppression of unintended responses
- wake-word fallback handling
- conversation-state-aware activation
- endpoint-aware activation
- prevention of accidental tool execution

### Important Principle

The question is not:
> "Did Zola hear speech?"

The question is:
> "Was that speech meant for Zola?"

---

## 2. Directed Speech Detection Layer

### Purpose

Identify whether an utterance appears to be addressed to Zola based on language, context, timing, and interaction state.

### Directed Speech Signals

- direct assistant name usage
- explicit wake word usage
- question phrasing
- command phrasing
- follow-up phrasing
- references to a prior Zola response
- user-facing repair phrases such as "no, I meant"
- tool-oriented phrasing such as "remind me," "schedule," or "text"
- conversational continuation after Zola speaks
- pause timing consistent with turn-taking

### Examples

Likely directed:
> "Zola, remind me to check the oil later."

Likely directed:
> "What about tomorrow?"

— if Zola just answered a calendar or weather question and no other speakers are present.

Likely not directed:
> "What about tomorrow?"

— if the user is speaking with another person nearby and no active Zola thread exists.

### Important Principle

Directed speech cannot be determined from transcript text alone. Conversational state must be part of the decision.

---

## 3. Ambient Speech Classification Layer

### Purpose

Identify speech that Zola can hear but should not act on.

### Responsibilities

- classify nearby human conversation as ambient
- detect speech not addressed to Zola
- suppress accidental responses
- ignore background media or TV speech
- distinguish self-talk from assistant-directed speech where possible
- prevent ambient speech from creating memory writes
- prevent ambient speech from triggering tools

### Ambient Speech Examples

- the user talking to family members
- someone else speaking nearby
- TV, podcasts, or music lyrics
- shop conversation while tools are running
- phone calls not involving Zola
- background workplace discussion

### Possible Outcomes

- ignore completely
- retain very short local context temporarily for observability
- classify as ambient and log
- suppress all downstream routing
- request clarification only when context makes assistant intent plausible

### Important Principle

Hearing speech is not permission to participate.

---

## 4. Conversational Continuation Detection

### Purpose

Allow natural follow-up conversation without requiring repeated wake words. Once Zola is already engaged in an active conversational thread, the attention threshold should temporarily lower for likely follow-up utterances.

### Responsibilities

- detect follow-up questions
- detect short elliptical responses
- maintain an open conversational window after Zola speaks
- associate vague references with the active topic
- allow repair turns
- allow short confirmations
- close the attention window after inactivity
- prevent old topics from keeping the attention window open indefinitely

### Example Follow-Ups

- "What about Saturday?"
- "Do that."
- "No, the other one."
- "How far is it?"
- "Can you text him?"
- "What did you mean by that?"

### Attention Window Behavior

After Zola speaks, a temporary continuation window allows short follow-ups to be treated as directed speech. The window decays based on:

- elapsed time since last exchange
- topic completion state
- user activity signals
- environmental noise level
- presence of other speakers
- device state
- endpoint context

### Important Principle

Wake-word-free interaction depends on conversational momentum. Zola should keep the door open briefly after active conversation, then gracefully close it.

---

## 5. Interruption Detection Layer

### Purpose

Detect when the user interrupts Zola while she is speaking and determine whether the interruption is meant to stop, correct, redirect, or continue the interaction.

### Responsibilities

- detect user barge-in during speech playback
- stop or duck speech playback when appropriate
- classify interruption intent
- preserve partial context from the interrupted response
- route corrections safely into the active turn
- avoid talking over the user
- distinguish genuine interruption from background speech during playback

### Interruption Types

**Stop Interruption** — the user wants Zola to cease speaking immediately.

Examples: "stop," "quiet," "not now," "shut up."

**Correction Interruption** — the user is correcting a fact or entity in the current turn.

Examples: "No, I meant Bumblebee." / "Not today, tomorrow." / "That is the wrong Micah."

**Redirect Interruption** — the user is changing the direction of the current request.

Examples: "Actually, check traffic first." / "Never mind, text Bre instead."

**Continuation Interruption** — the user wants Zola to pause and revisit a specific part of the response.

Examples: "Wait, explain that part." / "Hold on, what was the second thing?"

### Important Principle

Interruptions are not noise. They are high-value conversational control signals and must be classified and routed with the same care as direct requests.

---

## 6. Attention Confidence Scoring

### Purpose

Produce a structured confidence score representing how likely it is that an utterance was intended for Zola. This score guides whether the system processes normally, clarifies, suppresses, or ignores the utterance.

### Confidence Inputs

- wake word presence
- assistant name usage
- active conversation state
- recent Zola speech
- semantic directedness of the utterance
- question or command form
- user proximity to the active endpoint
- known speaker identity where permitted
- endpoint context
- environmental noise level
- presence of competing speakers
- topic continuity with active thread
- prior user behavior patterns
- device orientation
- interruption timing
- social context signals

### Decision Bands

**High Confidence** — process normally.

Examples: wake word used, active conversation follow-up, clear command addressed to Zola, direct question after Zola spoke.

**Medium Confidence** — lightly clarify before acting.

Example:
> "Were you asking me, or talking to someone else?"

**Low Confidence** — ignore or silently retain short-lived local context. No response should be generated.

### Important Principle

Low confidence should fail silent, not fail chatty.

---

## 7. Wake Word Fallback Model

### Purpose

Preserve wake-word activation as an explicit, reliable activation path while allowing natural conversation to become the preferred interaction model over time.

### Responsibilities

- treat wake word as unconditionally high-confidence directed speech
- allow wake word to reopen a closed attention window
- support reliable activation in noisy environments
- support explicit command mode for users who prefer it
- avoid requiring wake word during active conversation
- preserve compatibility with the existing voice pipeline

### Wake Word Role

Wake words should be used for:
- initial activation
- explicit attention grabbing
- noisy environments where natural detection is unreliable
- moments of deliberate ambiguity
- when the user wants certainty that Zola heard them

Wake words should not be required for:
- immediate follow-ups within an active continuation window
- clarification turns in response to a Zola question
- active collaborative work sessions
- interruption handling
- short confirmations

### Important Principle

Wake words are an attention override, not the foundation of natural conversation.

---

## 8. Endpoint-Aware Attention

### Purpose

Adjust attention decisions based on the device or environment where speech is captured. Different endpoints carry different risks, signal quality levels, and social expectations.

### Endpoint Profiles

**Phone:**
- likely near the user with strong personal context
- good default activation surface
- standard confidence thresholds apply

**Desktop:**
- useful for long-form collaboration
- may capture work calls or meetings
- stronger privacy filtering required
- higher ambient speech risk from shared workspace

**Shop endpoint:**
- noisy environment with high false-positive risk
- hands-busy interaction context
- stronger barge-in value
- higher confirmation threshold for sensitive actions

**Vehicle endpoint:**
- safety-sensitive context
- driving state changes all interruption rules
- only navigation and safety content should surface unprompted
- concise responses required

**Wearables and glasses:**
- high personal context
- privacy-sensitive in public environments
- must avoid speaking private information aloud
- lightweight interaction model preferred

### Important Principle

The same utterance may require different attention handling depending on where it was heard. Endpoint context is not optional — it is a required input to every attention decision.

---

## 9. Speaker and Social Context Awareness

### Purpose

Determine who is likely speaking and whether responding would be socially appropriate in the current environment.

### Responsibilities

- detect the known primary user where permitted
- prioritize the primary user's speech over household members or guests
- suppress responses in clearly public or multi-speaker environments
- detect active human-to-human conversation and remain silent during it
- protect private information in shared spaces
- avoid socially inappropriate interruptions

### Example

If the user says:
> "What time is it?"

while alone after speaking with Zola, Zola may answer.

If the user says the same thing while clearly in conversation with another person, Zola should remain silent — even if the confidence scorer would otherwise pass the utterance.

### Important Principle

Conversational intelligence includes knowing when not to join the conversation.

---

## 10. Attention State Model

### Purpose

Maintain a current state describing whether Zola is open, closed, listening, engaged, interrupted, or suppressed so that attention decisions are stateful and deterministic rather than purely reactive.

### Possible Attention States

- `CLOSED` — not listening for activation
- `WAKE_WORD_LISTENING` — listening for wake word only
- `ACTIVE_CONVERSATION` — engaged in a confirmed direct interaction
- `CONTINUATION_WINDOW` — window open for natural follow-ups after Zola speech
- `CLARIFICATION_PENDING` — waiting for the user to answer a clarification question
- `INTERRUPTED` — speech was interrupted; context is preserved pending resolution
- `SUPPRESSED_AMBIENT` — ambient classification active; routing suppressed
- `HIGH_NOISE_CAUTION` — environmental noise has degraded signal reliability
- `PRIVACY_SENSITIVE` — shared or public environment detected; suppression elevated
- `AUTONOMOUS_MONITORING` — background monitoring active; directed speech detection still required

### Responsibilities

- track the current attention state at all times
- expose the current state to all routing components
- close stale continuation windows deterministically
- prevent accidental state leaks across sessions
- enforce deterministic state transitions
- log every state transition with reason and timestamp
- prevent duplicate activation paths from competing states

### Example State Flow

1. State: `WAKE_WORD_LISTENING`
2. User says "Zola, what is the weather tomorrow?"
3. Wake word detected → state transitions to `ACTIVE_CONVERSATION`
4. Zola answers
5. State transitions to `CONTINUATION_WINDOW`
6. User says "What about Saturday?"
7. Follow-up detected within window → state remains `ACTIVE_CONVERSATION`
8. Zola answers
9. Inactivity timer expires → state returns to `WAKE_WORD_LISTENING`

### Important Principle

Attention must be stateful, not purely reactive. A system that evaluates each utterance in isolation without state context will produce inconsistent and unpredictable behavior.

---

## 11. Clarification and Repair Behavior

### Purpose

Handle medium-confidence attention cases without making Zola annoying or overly cautious. Clarification should be used sparingly and only when the value of getting it right outweighs the cost of asking.

### Responsibilities

- ask lightweight clarification when attention confidence is medium and the action is consequential
- suppress clarification when the ambiguity is low-value
- distinguish attention clarification from semantic clarification
- distinguish semantic clarification from action confirmation
- preserve user trust by not pretending certainty and not over-asking

### Clarification Types

**Attention Clarification** — used when Zola is unsure whether the user was speaking to her.

Example:
> "Were you asking me?"

Use sparingly. Prefer suppression when the value of the utterance is low.

**Semantic Clarification** — used when Zola knows the user was speaking to her but the request is ambiguous.

Example:
> "Do you mean Bumblebee or Double R?"

**Action Confirmation** — used when Zola understands the request but needs explicit confirmation before executing an irreversible or sensitive action.

Example:
> "Want me to send that text?"

### Important Principle

Do not confuse attention ambiguity with meaning ambiguity. They are separate problems requiring different responses. Treating a semantic clarification as an attention question — or vice versa — erodes user trust.

---

## 12. Privacy and Safety Boundaries

### Purpose

Prevent accidental processing, memory writes, tool execution, or spoken disclosure resulting from speech that was not clearly directed at Zola.

### Responsibilities

- suppress ambient speech from all memory storage pathways
- block tool execution for all utterances below the confidence threshold
- prevent private information from being spoken aloud in shared environments
- block message, email, and calendar disclosure when audience clarity is uncertain
- require elevated confidence for all sensitive domain actions
- preserve user control over always-listening behavior

### Sensitive Domains

The following domains require higher attention confidence than casual conversation before any action is taken:

- messages and SMS
- email
- calendar changes
- reminders
- health information
- financial information
- location sharing
- security camera summaries
- relationship and family details
- personal memories

### Important Principle

A false positive in a sensitive domain is more damaging than a missed casual response. When in doubt, stay silent and let the user re-initiate.

---

## 13. Integration With the Speech Pipeline

### Purpose

Define how Conversational Attention fits into the existing speech architecture without creating duplicate transcript paths or competing routing authorities.

### Pipeline Position

STT captures speech and produces a transcript. The Conversational Attention Authority sits between transcript finalization and intent routing — it is not part of STT and it is not part of the reasoning pipeline.

### Required Flow

1. Speech is captured by the active endpoint microphone.
2. STT produces partial and final transcript events.
3. Transcript finalization occurs through the single authoritative transcript path.
4. Conversational Attention Authority evaluates the finalized transcript.
5. Only directed or clarified speech enters the reasoning pipeline.
6. Low-confidence ambient speech is suppressed before reasoning.
7. Tool execution remains blocked unless attention confidence meets the required threshold for that action type.

### Required Constraints

- do not create a second transcript path
- do not bypass the existing routing authority
- do not allow the Live speech component to independently decide attention ownership
- do not allow background speech to trigger memory writes
- do not allow attention logic to rewrite or alter user intent
- do not allow attention suppression to hide direct user questions

### Important Principle

Conversational attention gates entry into reasoning. It does not replace reasoning.

---

## 14. Integration With Conversational Continuity

### Purpose

Use active topics, unresolved questions, and conversational momentum from the Conversational Continuity Architecture to determine whether short or ambiguous utterances are likely directed at Zola.

### Responsibilities

- read the current topic stack from the Conversational State Engine
- detect topic continuation signals in short or elliptical utterances
- use active unresolved prompts as context for interpreting short answers
- preserve return anchors when evaluating repair phrases
- connect repair phrases to prior turns
- distinguish active thread continuation from unrelated ambient speech

### Example

Zola asks:
> "There are two possible grandfathers: Raymond and Tom. Which one did you mean?"

User says:
> "Raymond."

The Attention Layer should treat this as directed speech at high confidence because there is an active clarification prompt expecting a short answer. Without continuity context, "Raymond" alone would score low confidence.

### Important Principle

Short answers can be meaningful when the conversational state expects them. Attention scoring without continuity context will systematically under-score legitimate follow-up responses.

---

## 15. Integration With the Attention and Relevance Engine

### Purpose

Maintain a clear boundary between inbound attention — determining whether user speech was meant for Zola — and outbound interruption — determining whether Zola should speak proactively.

### Boundary Definition

Conversational Attention answers:
> "Should this user speech enter Zola's reasoning pipeline?"

The Attention and Relevance Engine answers:
> "Should Zola speak, notify, defer, or stay silent?"

These are different questions with different authorities. They must not be merged.

### Responsibilities

- provide inbound attention confidence scores to routing
- expose suppression and clarification decisions for observability
- avoid conflating user-directed speech evaluation with proactive interruption logic
- respect Attention Dampening for Zola-initiated speech
- bypass dampening for direct user questions — a user asking Zola a question must never be suppressed by heat

### Important Principle

Inbound attention and outbound interruption are different authorities. Merging them creates a system that is simultaneously too aggressive in responding to users and too cautious in surfacing proactive information — or vice versa.

---

## 16. Integration With Autonomous Behavior

### Purpose

Prevent autonomous monitoring from conflating observational awareness with permission to respond to ambient speech.

### Responsibilities

- keep autonomous monitoring state separate from directed interaction state
- prevent autonomous workers from treating overheard ambient speech as user commands
- require attention authority to be established before any autonomous action responds to speech
- preserve user control over proactive behavior modes
- support explicit user opt-in for ambient conversational mode if it is ever implemented

### Example

The user says to another person:
> "We should probably leave soon."

Zola must not automatically surface traffic information unless the current context strongly indicates the user was including Zola, or the user has explicitly enabled ambient participation mode.

### Important Principle

Autonomy does not remove the need for attention discipline. A system that is authorized to monitor broadly must be even more careful about what it responds to.

---

## Core Architectural Principles

---

### Single Attention Authority

Every inbound utterance must have one authoritative attention decision before routing. No downstream component — not the reasoning pipeline, not tool handlers, not the Live speech component — may make its own independent attention judgment.

---

### Fail Silent by Default

When attention confidence is low, Zola remains silent. Silence is safer than accidental participation. The cost of responding to speech not meant for Zola is higher than the cost of missing a casual utterance.

---

### Wake Word as Override

The wake word remains a reliable and unconditional activation path. It should reopen attention whenever natural attention inference is uncertain or the user needs certainty that Zola heard them.

---

### Attention Is Stateful

Short utterances, corrections, and confirmations can only be correctly interpreted with conversational state context. A system that evaluates each utterance in isolation will produce unreliable results. The Attention State Model is not optional.

---

### No Ambient Durable Writes

Ambient speech must not create durable memory, trigger tool actions, or modify user profile data. Only attention-authorized speech may enter durable write flows.

---

### Sensitive Domains Require Higher Confidence

Messaging, email, calendar, health, security, location, and personal memory require stronger directedness confidence than casual conversational requests. The threshold scales with the irreversibility and sensitivity of the action.

---

### Attention Is Not Intent

Attention determines whether speech was meant for Zola. Intent determines what the user wants. These are separate layers with separate authorities. Collapsing them produces a system that either over-acts on ambient speech or under-processes legitimate requests.

---

## Integration Points

This document connects directly to:

- Zola Master Architecture Plan (Section 12)
- Conversational Continuity Architecture
- Streaming Cognition Architecture
- Autonomous Behavior Architecture (Response Governor and Autonomy Modes)
- Memory Hierarchy Architecture (Durable Write Authority)
- Environmental Awareness Architecture
- Trust, Permission, and Privacy Framework (Master Plan Section 13)
- Distributed Presence Architecture

---

## Failure Modes and Safeguards

### False Activation

Risk: Zola responds to speech not meant for her — ambient conversation, nearby speakers, or media — producing output the user did not request.

Safeguards:
- confidence thresholding suppresses low-score utterances before routing
- social context checks detect multi-speaker and public environments
- ambient classification layer runs before confidence scoring
- sensitive domain thresholds escalate the confidence requirement for consequential actions
- fail-silent default behavior

### Missed Directed Speech

Risk: The user speaks to Zola but Zola does not respond, either because the attention window has closed or confidence scored too low.

Safeguards:
- wake-word fallback provides a reliable override path
- continuation windows keep the door open after active exchanges
- clarification support allows the user to explicitly re-establish attention
- user correction handling allows recovery without frustration
- observability logs explain every suppression decision

### Accidental Tool Execution

Risk: Ambient or low-confidence speech triggers a reminder, message send, calendar change, or other irreversible action.

Safeguards:
- tool execution is blocked for all utterances below the action confidence threshold
- sensitive tools require explicit confirmation regardless of confidence
- attention authority must be established before any tool routing occurs
- Durable Write Authority gates all persistent actions

### Memory Pollution

Risk: Ambient speech — overheard conversations, TV, background discussion — is stored as user memory, corrupting the memory system over time.

Safeguards:
- memory writes are blocked unless attention confidence passes the required threshold
- ambient local context is held separately from durable memory and expires automatically
- Durable Write Authority requires attention-authorized source before any write

### Over-Clarification

Risk: Zola asks "Were you talking to me?" so frequently that the user finds it annoying and loses trust in natural interaction.

Safeguards:
- clarification is triggered only when confidence is medium and the action value is high
- low-value ambiguous utterances are suppressed silently, not clarified
- behavioral learning tracks clarification patterns and adjusts thresholds over time
- clarification frequency in shared spaces should be lower, not higher

### Attention Window Leak

Risk: A continuation window stays open indefinitely after a conversation ends, causing Zola to respond to unrelated speech much later.

Safeguards:
- continuation windows have explicit inactivity timers
- windows close deterministically on topic completion
- windows close on detection of competing speakers or environmental context change
- all window state transitions are logged

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only.

### Existing Foundations in Ava

The following capabilities in Ava's current architecture are relevant to conversational attention and should be evaluated during the audit:

- persistent voice interaction direction
- Deepgram-based streaming STT
- barge-in and continuous listening work
- single transcript path requirements
- QueryProcessor as the core turn pipeline
- Live speech authority constraints
- structured memory and relationship reasoning
- observability habits and authority boundary discipline

### Required New Components

The following components will likely need to be built as part of this architecture:

**ConversationalAttentionAuthority** — owns the final inbound attention decision for every utterance.

**AttentionStateMachine** — tracks current attention state and enforces deterministic transitions.

**DirectedSpeechScorer** — scores transcript and context signals for directedness confidence.

**AmbientSpeechClassifier** — classifies likely non-directed speech before it reaches routing.

**ContinuationWindowManager** — controls follow-up windows after active interaction and closes them deterministically.

**InterruptionClassifier** — classifies user speech during Zola playback into stop, correction, redirect, and continuation types.

**AttentionDecisionLog** — produces runtime proof for every accepted, clarified, suppressed, and ignored utterance.

### Dependencies

- Streaming Cognition Architecture must be defined before partial transcript handling in the attention layer is built
- Conversational Continuity Architecture must expose the topic stack and unresolved prompt state before continuation detection can use it
- Trust and Permission Framework must define always-listening consent rules before ambient monitoring is activated
- Distributed Presence Architecture must resolve endpoint coordination before multi-device attention authority is implemented

### Open Questions

- Does Ava currently have any form of attention gating between transcript finalization and intent routing, or does every transcript enter the reasoning pipeline today?
- How should attention state be synchronized across devices in the Distributed Presence Architecture?
- Should speaker identity detection be implemented at launch or treated as a future capability given its privacy implications?
- What is the correct inactivity timeout for continuation windows across different endpoint types?
- Should the user be able to explicitly disable wake-word requirement and operate in always-on attention mode?

### Architectural Risks

- The single attention authority requirement conflicts with any existing code that independently evaluates whether to respond to a transcript — the audit must identify all such locations
- Continuation windows that are too long create a false activation risk; windows that are too short create a frustrating interaction where users must constantly re-initiate
- The boundary between this architecture and the Streaming Cognition Architecture needs to be precisely defined — partial transcripts handled by streaming cognition must not bypass the attention authority gate

### Avoid

- treating every final transcript as a user request
- allowing Live to independently decide whether ambient speech was directed
- creating separate attention logic inside individual tool handlers
- allowing low-confidence speech to trigger actions
- storing ambient speech as memory
- requiring wake word for every follow-up within an active window
- keeping attention windows open indefinitely
- over-clarifying low-value ambiguity
- conflating outbound interruption control with inbound attention detection

---

## Long-Term End State

Conversational Attention eventually evolves toward:

- natural wake-word-free conversation in all contexts
- reliable directed speech detection across all endpoint types
- strong ambient speech suppression with minimal false positives
- smooth follow-up handling that feels like natural conversation
- interruption-aware speech behavior that classifies and routes all interruption types correctly
- socially appropriate silence in shared and public environments
- sensitive-domain confidence protection that scales with action severity
- observable attention decisions that can explain every response and every silence
- unified attention authority across all devices and endpoints

The system should ultimately feel:

- natural and present
- restrained when restraint is appropriate
- responsive when the user is genuinely addressing Zola
- socially aware of who else is in the room
- safe around private information
- difficult to accidentally trigger
- trustworthy because its behavior is explainable

without losing:

- user control over attention behavior
- wake-word reliability as a fallback
- privacy boundaries in shared environments
- routing authority integrity
- memory write safety
- tool execution safety
- the principle that attention is not the same as intent — they are separate authorities that must remain separate
