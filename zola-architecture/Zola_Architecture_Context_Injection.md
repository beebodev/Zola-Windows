# Zola Architecture — Context Injection

**Document version:** 1.3
**Status:** Draft — pending lore integration
**Authored:** Post-Phase 22 planning cycle
**Change from v1.1:** Brief model changed from speaker-scoped to
household-scoped. PCI-D01 (UNKNOWN gate), PCI-D02 (delta-brief),
and related speaker-scoped complexity retired. OQ-PCI-02, OQ-PCI-03,
OQ-PCI-05, OQ-PCI-07 closed as resolved-by-simplification.
**Change from v1.2:** Added internal-context-only principle to
Section 2. Added behavioral instruction wrapper to Section 6
injection path. Brief is private context — never delivered aloud
or referenced directly by Zola.

**Depends on:**
- Phase 19 world model (`EntityGraph`, `RelationshipWriteGovernor`, `SelfEntityInitializer`)
- Phase 20 conversation architecture (`ConversationFrameManager`, `FocusStackManager`, `OpenLoopTracker`)
- Phase 21 directedness gate (`TurnDirectednessGate`, `TurnResponseGuard`)
- Phase 22 living voiceprint (`LiveSessionIdentityTracker`, `ConversationIdentityCoordinator`, `VoiceEmbeddingStore`)
- Phase 6 warm start (`MemoryWarmStartAgent`, `WarmMemoryContextProvider`, `SessionMemoryCoordinator`)
- Phase 15 session summaries (`ConsolidationLoop` Step 6, `SessionSummary`)

Companion documents:
- `zola-architecture/Zola_Architecture_Memory_Agency.md`
- `zola-architecture/Zola_Architecture_Entity_Taxonomy.md`
- `zola-architecture/Zola_Architecture_Relationship_Inference.md`
- `zola-architecture/Zola_Architecture_Firestore_Structure.md`
- `zola-architecture/Zola_Architecture_Living_Voiceprint_MultiSpeaker.md`
- `zola-architecture/lore/DESIGN_DECISIONS.md`

---

## Section 1 — Purpose & Scope

### What This Document Covers

This document defines the architecture for Phase 23 — Context Injection.
Context Injection is the mechanism by which Zola assembles a structured
household brief from her world model, conversation history, and entity
graph, and injects it into the Live session system instruction before
the first word of a conversation is spoken.

The goal is simple: Zola should never start a session cold. Everything
she knows about the people in her world — who they are, what their
relationships are, what was discussed recently, what remains unresolved,
what is time-sensitive today — should be present in her context before
the first turn begins. She does not wait to learn who is speaking before
orienting herself. She arrives already knowing her world. When Phase 22
identifies the active speaker during the session, Zola already has that
person's context in hand and can apply it naturally.

Phases 19 through 22 built the foundation this requires:

- Phase 19 gave Zola a genuine world model with entities, relationships,
  and a SELF node
- Phase 20 gave her persistent conversational state — topic threads, focus
  stack, and open loops that survive restarts
- Phase 21 gave her speaker directedness — she knows whether she is being
  addressed
- Phase 22 gave her continuous speaker identity — she knows who is speaking
  during a live session

Context Injection is the phase that puts those capabilities to work at
session open. It replaces the Phase 6 `MemoryWarmStartAgent` — which was
built against a flat episodic recall model that predates the entity graph —
with a `SessionBriefBuilder` that draws from the full world model and
delivers a structured, character-limited household brief through the
existing `MemoryInjectionBuilder` injection path.

### What This Document Covers

- The `SessionBriefBuilder` component and its assembly responsibilities
- The household brief model — speaker-agnostic context covering all
  recognized entities in Zola's world
- Brief content sections — what gets assembled and in what priority order
- The structured rendering schema — format that maximizes token efficiency
  within the character budget
- The character budget model and `SESSION_BRIEF_MAX_CHARS` constant
- The brief cache model and `SESSION_BRIEF_REUSE_WINDOW_MS` constant
- The injection path — how the brief reaches `GeminiLiveClient` via
  `MemoryInjectionBuilder`
- `MemoryWarmStartAgent` retirement — transition from Phase 6 warm start
  to the new brief model
- RTDB as a known liability — scoped out of this phase but documented
- Session lifecycle integration — where brief assembly fits in the existing
  session start sequence
- Open questions requiring on-device calibration or deferred design

### What This Document Does Not Cover

- RTDB retirement — a known liability documented in Section 9; belongs in
  a dedicated cleanup phase
- Behavioral differentiation per speaker — Zola's personality is her
  personality regardless of who she is talking to; what varies is how she
  applies context, not what context she holds
- Cross-device session handoff — `HandoffContextSerializer` is gated off
  and remains out of scope
- Multi-device brief synchronization — all brief assembly is local,
  on-device, per-session
- Mid-session brief refresh — the brief assembles once at session open;
  Phase 22 speaker identity handles real-time speaker awareness during
  the session itself; these are complementary, not redundant
- Write-path changes — `SessionBriefBuilder` is read-only; it assembles
  from existing stores and writes nothing
- Speaker-scoped filtering of sessions summaries or open loops — the
  household brief intentionally includes all recognized entities; Zola
  determines relevance at response time, not at assembly time

---

## Section 2 — Foundational Concepts

### The Brief as a Household Briefing Packet

The closest analogy to what Context Injection delivers is a well-prepared
briefing packet handed to someone before they walk into a room where any
of several people might be present. The packet does not try to predict
who will speak first — it covers everyone. Who is in this household. What
their relationships are. What was discussed recently. What is unresolved.
What is time-sensitive today.

When someone speaks, the person holding the packet already knows who that
is and what context applies. They do not need to run to a filing cabinet
mid-conversation. The briefing packet did its job before the room got loud.

Zola has been building the contents of that packet across Phases 19 through
22. Context Injection is the phase that assembles it and puts it on the
desk before the session starts.

### The Recall Gap Was Always a Delivery Problem

Phase 15 documented `OQ-P15-LIVE-RECALL-ROUTING`: when Gemini Live
intercepts a turn first, `QueryRoutingService` never runs and recall
never fires. Phase 17 partially addressed this with
`EpisodicRecallBypassAuthority`. But the deeper insight is that reactive
recall — waiting for a query to trigger a memory lookup — is the wrong
model for session-opening context.

The right model is proactive delivery: assemble the brief before the first
turn, inject it once, and let the session proceed from an informed starting
point. Recall at query time remains available and continues to win when it
produces higher-confidence results. The brief is a seed, not a ceiling.

### Speaker-Agnostic Brief, Speaker-Aware Response

The brief does not try to predict who will speak. It covers the household.
Phase 22's `ConversationIdentityCoordinator` provides the real-time pointer
to who is speaking during any given turn. These two capabilities are
complementary:

- The brief gives Zola her world map — all recognized entities and their
  context — before the session begins
- Phase 22 tells Zola which point on that map is currently active during
  each turn

Neither replaces the other. The brief without identity is a map with no
current location. Identity without the brief is a location with no map.
Together they give Zola genuine situational awareness.

### The World Model as the Source of Truth

Phase 6's `MemoryWarmStartAgent` ran Stages 1–5 of the recall pipeline
against episodic session summaries. That was the right design for Phase 6.
It is no longer sufficient.

Phase 19 built an entity graph with relationships, attributes, and a SELF
node. Phase 20 built a persistent conversational frame with topic threads
and open loops. These are richer sources than episodic summaries alone.
`SessionBriefBuilder` draws from all of them. `MemoryWarmStartAgent`'s
first-turn seed role is retired in this phase — the brief replaces it
at the injection point.

### One Authority for Brief Assembly

A single component — `SessionBriefBuilder` — owns brief assembly. No other
component writes to the brief. No other component decides what goes in it.
This is consistent with the project-wide principle of one authority per
responsibility. `SessionBriefBuilder` is read-only with respect to all
data stores; it assembles and renders, never writes.

### The Brief Is Internal Context — Not an Opening Statement

The brief is private context for Zola. It is the briefing packet she
reads before walking into the room — not something she recites to the
people in it. The user never hears the brief. They never see it. They
experience only the effect of it: a Zola who already knows them, already
knows where things left off, and already knows what is unresolved.

Zola must never open a session by summarizing the brief, referencing it
directly, or announcing what she knows. She absorbs it silently and lets
it shape her responses naturally. The system instruction wrapper around
the brief block (Section 6) enforces this explicitly — it is a behavioral
instruction, not just a content marker.

The risk of not stating this clearly: Gemini Live may treat prominent
structured content in the system prompt as a conversation prompt.
"Hello Brian, I see you have an open loop about the parts order" is
exactly the wrong behavior. The instruction wrapper prevents it.

### Structured Format Over Prose

The brief is injected into a Live system instruction that already carries
identity, persona, and behavioral content. Every character counts. Prose
wastes the character budget — the same information conveyed in a labeled
structured schema uses roughly 40% fewer characters and parses more
reliably when the model processes the instruction block. All brief sections
render in the structured schema defined in Section 3. Prose examples are
illustrative only and are not the rendering target.

---

## Design Decisions Locked by This Document

**PCI-D01 — The brief is household-scoped, not speaker-scoped.**
`SessionBriefBuilder` assembles a brief covering all recognized entities
in Zola's world — not a brief tailored to a single predicted speaker.
The brief fires at session open regardless of who is speaking or whether
any speaker has been identified yet. There is no identity gate on brief
assembly. Rationale: waiting for speaker identity before assembling context
introduces a timing dependency that the audit confirmed cannot be reliably
resolved at `onSessionStart()` hook time (P23-AUD-09, P23-AUD-25). A
household brief sidesteps this dependency entirely and is more useful —
Zola knows her whole world, not just one person's slice of it. Phase 22
speaker identity handles real-time speaker awareness during turns; it does
not need to gate session-level context.

**PCI-D02 — Brief assembles once at session open via onSessionStart() hook.**
`SessionBriefBuilder` is called once per session at the
`SessionMemoryCoordinator.onSessionStart()` hook point. There is no
mid-session brief refresh, no delta-brief on speaker transitions, and no
secondary assembly pass. Phase 22 speaker identity is the mechanism for
mid-session speaker awareness — brief injection is not. Rationale: the
household brief already contains context for every recognized entity.
When a new speaker is identified mid-session, Zola already has their
context. No additional injection is needed.

## PCI-D02 Amendment (Phase 41) — Bounded Mid-Session Refresh

**Status:** PCI-D02's original single-shot assembly guarantee for the
primary session brief remains unchanged and binding. This amendment
adds a second, independent mechanism — the mid-session refresh block —
layered alongside it, not replacing it.

**What stays the same:** `SessionBriefBuilder.assemble()` still runs
exactly once, at session start. Its output, its 2000-character budget
(`SESSION_BRIEF_MAX_CHARS`), and its existing five-source assembly are
untouched by this amendment.

**What's new:** A second, independently-budgeted content block may
populate during a session, after the primary brief has already been
delivered. This block:

- Is capped at `SESSION_BRIEF_MID_SESSION_MAX_CHARS` (500 characters —
  25% of the primary budget), separate from and not deducted from
  `SESSION_BRIEF_MAX_CHARS`.
- Is populated by an incremental re-query, scoped only to sources
  whose content can plausibly change within a single session (open
  loops as of Phase 41 Track D; temporally-gated facts per P41-D03
  added in Track E) — not a re-run of the full five-source primary
  assembly.
- Is triggered by one of two independent signals, whichever fires
  first since the block was last populated (or since session start, if
  never populated):
  - A topic-shift signal from the existing `TopicShiftDetector` →
    `ConversationalStateSnapshot.topicShiftDetected` per-turn signal
    (already computed in `QueryProcessor`) — no new detection logic.
  - A backstop timer: 15 turns or 10 minutes, whichever comes first
    (`MID_SESSION_REFRESH_TURN_THRESHOLD` /
    `MID_SESSION_REFRESH_TIME_THRESHOLD_MS`).
- Executes under a bounded timeout
  (`MID_SESSION_REFRESH_EXECUTION_TIMEOUT_MS`, 1500ms — matching the
  existing `SESSION_BRIEF_AWAIT_TIMEOUT_MS` precedent). If the
  re-query doesn't complete within this window, the refresh is skipped
  for that cycle — fail closed, no partial or blocking update — and
  retried at the next trigger.
- Is rendered as a separate, clearly labeled section in
  `MemoryInjectionBuilder`'s output, appended after the primary brief,
  and only when non-empty.

**Why this is an amendment, not a workaround:** Rather than building a
second, independent context-assembly system to avoid touching PCI-D02,
this amendment extends `SessionBriefBuilder`'s existing authority for
"what does Zola currently know" — preserving one authority per
responsibility instead of creating two systems with overlapping jobs.

**Traceability:** P41-D01, `Zola_Phase41_Build_Plan.md` Track D.

**PCI-D03 — Character budget enforced by named constant SESSION_BRIEF_MAX_CHARS.**
The assembled brief is truncated to fit within `SESSION_BRIEF_MAX_CHARS`
characters before injection. The default value is 2000 characters. This
constant is defined in `ZolaConstants` and is never inlined as a magic
number. The budget is applied at render time by `SessionBriefBuilder`
before the brief is handed to `MemoryInjectionBuilder`. On-device
calibration may adjust this default — documented as OQ-PCI-01.

**PCI-D04 — SessionBriefBuilder is read-only.**
`SessionBriefBuilder` reads from existing stores — the entity graph,
`SessionSummary` documents, the conversational frame, open loop tracker,
and `UserStateProvider`. It writes nothing. It does not trigger
consolidation, does not update any cache, and does not modify any
Firestore document. Rationale: agents that read and write to memory at
the same time introduce subtle ordering dependencies and truth corruption
risks. Brief assembly is a read-and-render operation only.

**PCI-D05 — MemoryWarmStartAgent first-turn seed role is retired.**
The `WarmMemoryContextProvider` first-turn seed path in `QueryProcessor`
and `GeneralIntentHandler` is removed in this phase. The brief injected
at session open through `MemoryInjectionBuilder` replaces it as the
session-opening context mechanism. `MemoryWarmStartAgent` infrastructure
(`WarmRecallRunner`, `WarmMemoryContextProvider`) is retired. The idle
refresh loop in `MainActivity` is also removed. Rationale: maintaining
two parallel session-opening context mechanisms with different input
sources produces conflicting context signals and redundant Firestore
reads. One mechanism, one injection point.

**PCI-D06 — Brief injects through MemoryInjectionBuilder, not GeminiLiveClient directly.**
The brief content is delivered to the Live session system instruction via
the existing `MemoryInjectionBuilder.buildMemoryBlock()` path, which is
called from `GeminiLiveClient.buildSetupMessage()`. `GeminiLiveClient`
is not modified. `SessionBriefBuilder` produces a rendered string;
`MemoryInjectionBuilder` incorporates it into the memory block at setup
time. Rationale: `GeminiLiveClient` is a high-risk file with a large blast
radius. The existing injection path was specifically designed to accept
assembled memory content. Using it respects the established boundary.

**PCI-D07 — Brief content priority order is fixed.**
When the character budget requires truncation, brief sections are dropped
in reverse priority order. Priority from highest to lowest: (1) household
entity roster and relationships, (2) active conversational frame and topic
threads, (3) recent session summary, (4) open loops and unresolved items,
(5) time-relevant entity facts. Each section is self-contained — dropping
a lower-priority section never corrupts a higher-priority one. Within
Section 3, `summaryText` is hard-capped at 300 characters regardless of
budget remaining — if the summary exceeds this cap, `factsSurfaced` is
used as the fallback content for that section. Rationale: LLM-generated
session summaries vary widely in length. A verbose prior summary must not
crowd out structured open loop and time-relevant content that is often
higher signal.

**PCI-D08 — RTDB retirement is out of scope for this phase.**
RTDB carries known liabilities: duplicate entries per Live turn
(`OQ-P17-RTDB-DUAL-WRITE`), incomplete purge behavior, and a legacy
`loadUserMemory` path that conflicts with the structured graph. These are
real problems but scoped to a dedicated cleanup phase. Context Injection
does not read from RTDB and does not introduce new RTDB dependencies.
Rationale: RTDB retirement touches `FirebaseHelper`, the conversation log
write path, and the purge sequence — enough blast radius to deserve its
own phase rather than being a side task here.

**PCI-D09 — Brief cache with reuse window prevents burst re-assembly.**
`SessionBriefHolder` caches the most recently assembled brief keyed on
`sessionDate` (calendar date in device timezone). If a session restarts
within `SESSION_BRIEF_REUSE_WINDOW_MS` (default: 5 minutes) on the same
calendar date, the cached brief is reused without re-querying Firestore.
The cache is invalidated on calendar date change and on explicit
`SessionBriefHolder.clear()` at session end. `SESSION_BRIEF_REUSE_WINDOW_MS`
is a named constant in `ZolaConstants`. Rationale: in environments with
flaky connectivity, a Live WebSocket may drop and reconnect several times
within a short window. Without a reuse cache, each reconnect triggers
concurrent Firestore reads, spiking latency and read quota at exactly
the moment the user needs responsiveness. Because the brief is now
household-scoped rather than speaker-scoped, the cache key is simply the
session date — no speaker entity ID needed.

---

## Section 3 — SessionBriefBuilder

### Responsibility

`SessionBriefBuilder` is the single component responsible for assembling
the household session brief. It is called once per session at the
`SessionMemoryCoordinator.onSessionStart()` hook point. No speaker
identity is required before assembly begins.

Its output is a rendered string — a compact structured block that
summarizes what Zola knows about her world and this moment. That string
is passed to `MemoryInjectionBuilder` for inclusion in the Live system
instruction.

### Inputs

`SessionBriefBuilder` reads from:

- `EntityResolutionService` / entity graph — all recognized PERSON entities
  with relationship edges from the SELF node; key attributes per entity
- `SessionSummaryRetriever` — most recent `SessionSummary` document;
  `summaryText`, `factsSurfaced`, `topicTags`, `emotionalRegister`
- `ConversationFrameManager` — current active frame if present;
  `activeTopic`, `activeEntityIds`, `recentTopics`
- `FocusStackManager` — top of focus stack if non-empty; durable topic
  thread with return pointer
- `OpenLoopTracker` — all open loops in ACTIVE or DORMANT state, sorted
  by recency; capped at 5 items to control budget
- `UserStateProvider` — time of day, workspace context for time-relevant
  framing

Note: `ConversationIdentityCoordinator` is not an input to
`SessionBriefBuilder`. Speaker identity is not required for household
brief assembly.

### Outputs

A single `SessionBrief` data class:

```kotlin
data class SessionBrief(
    val renderedContent: String,             // assembled brief, within budget
    val characterCount: Int,                 // actual length after truncation
    val sectionsIncluded: List<BriefSection>,
    val assembledAtMs: Long,
    val entityCount: Int                     // number of entities included in roster
)
```

`BriefSection` is an enum: `ENTITY_ROSTER`, `ACTIVE_FRAME`,
`SESSION_SUMMARY`, `OPEN_LOOPS`, `TIME_RELEVANT_FACTS`.

`SessionBrief` never returns null. If all Firestore reads fail,
`renderedContent` is empty and `sectionsIncluded` is empty — the brief
is omitted from the session instruction gracefully.

### Rendering Schema

All sections render using a consistent labeled bracket schema. This format
is dense, labeled, and character-efficient. Prose is explicitly not the
rendering target.

Each section opens with a `[LABEL]` header. Content follows using short
middot-separated fields. No closing tags. No XML angle brackets.

Full household brief rendering example within budget:

```
[ENTITIES] Brian · Primary Bond | Micah · Son (Brian) | Breanna · Daughter (Brian)
[FRAME] 3h ago · Parts order (Double R) · Stack: parts order > NFL draft
[SUMMARY] Discussed NFL draft and Micah's schedule · Tone: relaxed
[LOOPS] Parts follow-up 2d · Micah tournament date 4d · Breanna ride 1d
[TIME] Breanna birthday 3d · Shop opens 8AM
```

This schema conveys the same payload as equivalent prose in approximately
40% fewer characters, preserving budget for actual content depth.

### Threading

`SessionBriefBuilder.assemble()` is a suspend function. It runs on
`Dispatchers.IO` via `lifecycleScope.launch(Dispatchers.IO)` from the
session start hook — consistent with the existing hook pattern confirmed
by the pre-build audit (P23-AUD-11). Assembly is fire-and-forget relative
to the hook caller. `SessionBriefHolder` is populated when assembly
completes. If the Live session setup runs before assembly completes,
the brief is omitted from that setup call — the session opens without
brief context rather than blocking. See PCI-D09 and OQ-PCI-06.

### Failure Behavior

If any individual data source fails, `SessionBriefBuilder` continues
assembly with what is available. It does not throw. It does not abort.
A partial brief is better than no brief. Each section is independently
failable — section failure causes that section to be omitted, not the
entire brief.

---

## Section 4 — Brief Content Sections

The brief is assembled from five content sections in priority order.
Each section renders using the labeled bracket schema defined in Section 3.

### Section 1 — Household Entity Roster (Highest Priority)

Who exists in Zola's world and how they relate to each other and to SELF.

Assembled from:
- All recognized PERSON entities in the entity graph
- Relationship edges from SELF node — relationship label per entity
- Relationship edges between entities where relevant (e.g. parent-child)
- Capped at 6 entities to control budget; PRIMARY_BOND entities first

Rendered example:
```
[ENTITIES] Brian · Primary Bond | Micah · Son (Brian) | Breanna · Daughter (Brian)
```

### Section 2 — Active Conversational Frame (High Priority)

Where the conversation left off and what topic threads are live.

Assembled from:
- `ConversationFrameManager.getCurrentFrameOrNull()` — active topic,
  active entity IDs, recency from `TemporalRecencyFormatter`
- `FocusStackManager` — top of stack if non-empty

Rendered example:
```
[FRAME] 3h ago · Parts order (Double R) · Stack: parts order > NFL draft
```

### Section 3 — Recent Session Summary (Medium Priority)

What was discussed in the most recent session. `summaryText` is
hard-capped at `SESSION_BRIEF_SUMMARY_MAX_CHARS` (300 characters). If
`summaryText` exceeds this cap, `factsSurfaced` is used as section
content instead. If Gemini enrichment failed at consolidation time,
the baseline summary template is used — brief assembly handles this
gracefully per P23-AUD-31.

Assembled from:
- Most recent `SessionSummary` via `SessionSummaryRepository.getLatestSessionSummary()`
- `summaryText` (capped at 300 chars) or `factsSurfaced` as fallback
- `emotionalRegister` appended if present

Rendered example (summary within cap):
```
[SUMMARY] Discussed NFL draft and Micah's schedule · Tone: relaxed
```

Rendered example (facts fallback):
```
[SUMMARY] Facts: Micah break Jun 15 · Double R needs brakes
```

### Section 4 — Open Loops and Unresolved Items (Medium Priority)

What Zola is tracking as unresolved across the household. Not filtered
by speaker — all ACTIVE and DORMANT loops are included. Capped at 5
items sorted by recency.

Assembled from:
- `OpenLoopTracker.listForResurfacing()` — ACTIVE and DORMANT loops,
  all speakers, sorted by recency

Rendered example:
```
[LOOPS] Parts follow-up 2d · Micah tournament date 4d · Breanna ride 1d
```

### Section 5 — Time-Relevant Entity Facts (Lowest Priority)

Facts from the entity graph that are time-relevant to this moment
across any recognized entity.

Assembled from:
- `UserStateProvider` time-of-day context
- Entity attributes with temporal relevance: upcoming birthdays within
  7 days, active goals with near-term deadlines, ROUTINE entities
  relevant to current time of day

Rendered example:
```
[TIME] Breanna birthday 3d · Shop opens 8AM
```

---

## Section 5 — Character Budget Model

### Named Constants

```kotlin
const val SESSION_BRIEF_MAX_CHARS = 2000            // full session-open brief
const val SESSION_BRIEF_REUSE_WINDOW_MS = 300_000L  // 5-minute reuse window
const val SESSION_BRIEF_SUMMARY_MAX_CHARS = 300      // per-section cap on summaryText
```

All three constants are defined in `ZolaConstants`. None are inlined as
magic numbers at any call site.

Note: `DELTA_BRIEF_MAX_CHARS` from v1.1 is removed — the delta-brief
mechanism has been retired along with speaker-scoped brief assembly.

### Budget Allocation

Informal per-section targets within the 2000-character budget:

| Section | Target allocation |
|---------|------------------|
| Entity roster | ~300 chars |
| Active conversational frame | ~300 chars |
| Recent session summary | ~400 chars (summaryText capped at 300) |
| Open loops | ~400 chars |
| Time-relevant facts | ~200 chars |
| Schema labels and separators | ~100 chars |
| Headroom | ~300 chars |

These are targets, not hard per-section limits. The only hard limits
are the total budget (`SESSION_BRIEF_MAX_CHARS`) and the summary text
cap (`SESSION_BRIEF_SUMMARY_MAX_CHARS`).

### Truncation Strategy

`SessionBriefBuilder` assembles sections in priority order. After each
section is appended, the running character count is checked. If the
remaining budget cannot fit the next section, that section is dropped
entirely — partial sections that cut off mid-line are never injected.

Sections are never reordered to fit more content. Priority order is
fixed per PCI-D07.

`summaryText` within Section 3 is truncated to
`SESSION_BRIEF_SUMMARY_MAX_CHARS` before the section budget check runs.
If the truncated summary is still too long for the remaining budget,
the section falls back to `factsSurfaced`. If `factsSurfaced` is also
too long or empty, Section 3 is dropped.

### Brief Cache and Reuse

`SessionBriefHolder` caches the most recently assembled brief keyed on
`sessionDate` (calendar date in device timezone).

On session open, before any Firestore reads begin, `SessionBriefHolder`
is checked:
- If a cached brief exists for the same date and the session is
  restarting within `SESSION_BRIEF_REUSE_WINDOW_MS`, the cached brief
  is returned immediately with no Firestore reads.
- Otherwise, full assembly runs and the result is cached.

Cache invalidation:
- Calendar date change (midnight rollover)
- Explicit `SessionBriefHolder.clear()` at session end

### Calibration

All three constants are starting defaults. On-device calibration should
validate across single-person sessions, multi-person household sessions,
and sessions following long prior conversations with many open loops.
See OQ-PCI-01.

---

## Section 6 — Injection Path

### How the Brief Reaches the Live Session

The brief travels through the existing memory injection path:

```
SessionMemoryCoordinator.onSessionStart()
    ↓
SessionBriefBuilder hook fires (lifecycleScope.launch(Dispatchers.IO))
    ↓
SessionBriefBuilder.assemble()
    → Reads entity graph, SessionSummary, ConversationFrame,
      OpenLoopTracker, UserStateProvider
    → Renders structured brief string
    ↓
SessionBriefHolder.set(brief)
    ↓
[session active — brief held in memory]
    ↓
First Live-path turn triggers GeminiLiveSession.obtain()
    ↓
GeminiLiveClient.buildSetupMessage()
    → MemoryInjectionBuilder.buildMemoryBlock() reads SessionBriefHolder.get()
    → Brief incorporated as named block in systemInstruction
    ↓
Gemini Live WebSocket opens with household brief in system prompt
    ↓
Phase 22 ConversationIdentityCoordinator identifies active speaker
    → Zola applies relevant context from the brief to the current speaker
```

`GeminiLiveClient` is not modified. The brief is incorporated by
`MemoryInjectionBuilder` alongside existing episodic and structured
memory blocks, coexisting with the `=== MEMORY ===` schema confirmed
in the audit (P23-AUD-03).

### Instruction Wrapper

The `=== SESSION BRIEF ===` block is wrapped with an explicit behavioral
instruction that tells Zola how to use the brief content. This wrapper
is rendered by `MemoryInjectionBuilder` and is not part of the brief
string produced by `SessionBriefBuilder`.

The full injected block looks like this:

```
=== SESSION BRIEF ===
The following is your private context for this session. Use it to
inform your responses naturally. Do not read it aloud, summarize it,
announce what you know, or reference it directly unless the
conversation specifically calls for it.
[ENTITIES] Brian · Primary Bond | Micah · Son (Brian) | Breanna · Daughter (Brian)
[FRAME] 3h ago · Parts order (Double R) · Stack: parts order > NFL draft
[SUMMARY] Discussed NFL draft and Micah's schedule · Tone: relaxed
[LOOPS] Parts follow-up 2d · Micah tournament date 4d · Breanna ride 1d
[TIME] Breanna birthday 3d · Shop opens 8AM
```

The instruction wrapper is static text — it does not vary per session
and does not count against `SESSION_BRIEF_MAX_CHARS`. It is part of
`MemoryInjectionBuilder`'s rendering responsibility, not
`SessionBriefBuilder`'s.

### Latency Model

Brief assembly is fire-and-forget from the hook. `SessionBriefHolder`
is populated when assembly completes. `GeminiLiveClient.buildSetupMessage()`
reads from `SessionBriefHolder` at WebSocket open time.

Under normal conditions the gap between `onSessionStart()` and the
first Live turn is large enough for assembly to complete. Under rapid
reconnect conditions, the reuse cache (PCI-D09) serves the brief
immediately. The edge case — cold cache, fast first turn, slow Firestore
— results in a session opening without brief context. This is acceptable
and documented as OQ-PCI-06.

### SessionBriefHolder

A session-scoped singleton — `SessionBriefHolder` — holds the assembled
`SessionBrief` between assembly and injection:

```kotlin
class SessionBriefHolder {
    fun set(brief: SessionBrief)         // called by SessionBriefBuilder
    fun get(): SessionBrief?             // called by MemoryInjectionBuilder
    fun clear()                          // called at session end
    fun isCacheValid(                    // reuse check
        sessionDate: LocalDate
    ): Boolean
}
```

`SessionBriefHolder.clear()` is called at session end via
`registerSessionEndHook` or `tearDownAssistantSession` — whichever
teardown path is confirmed available during the build. The cache entry
(`sessionDate` key + rendered content) persists across the reuse window.

---

## Section 7 — MemoryWarmStartAgent Retirement

### What Is Retired

Phase 6 delivered:
- `WarmMemoryContext` and `WarmMemoryContextEntry` data classes
- `WarmRecallRunner` — lightweight Stages 1–5 recall runner
- `MemoryWarmStartAgent` — session-start agent
- `WarmMemoryContextProvider` — application-scoped singleton
- First-turn seed wiring in `QueryProcessor` via `applyFirstTurnWarmMemorySeed`
- First-turn seed wiring in `GeneralIntentHandler`
- 30-minute idle refresh loop in `MainActivity`

All of the above are retired in this phase. The audit (P23-AUD-17
through P23-AUD-21) confirmed the full caller inventory and the
existence of architecture tests covering the warm start constraints.

### Why This Is Safe

The Phase 6 warm start was always a seed — live recall at query time
could override it. The household brief delivered by `SessionBriefBuilder`
serves the same seed role but is richer (world model and entity graph
rather than episodic recall only) and more reliably present (injected
into the system prompt rather than the first-turn query context). The
live recall override behavior is unchanged — query-time recall continues
to run and continues to win when it produces higher-confidence results.

### Migration Path

The retirement is additive-then-remove:

1. `SessionBriefBuilder` and `SessionBriefHolder` are built and wired
2. Brief injection through `MemoryInjectionBuilder` is verified on device
3. First-turn seed wiring in `QueryProcessor` and `GeneralIntentHandler`
   is removed
4. `WarmMemoryContextProvider`, `WarmRecallRunner`, and
   `MemoryWarmStartAgent` are deleted
5. Idle refresh loop in `MainActivity` is removed
6. `WarmMemoryContext` and `WarmMemoryContextEntry` are deleted after
   grep confirms no remaining consumers (P23-AUD-20 confirmed external
   consumer list)
7. `MemoryWarmStartArchitectureTest` is rewritten to cover
   `SessionBriefBuilder` read-only and no-pipeline-invocation constraints
   (P23-AUD-21, OQ-PCI-04)

---

## Section 8 — Session Lifecycle Integration

### Where Brief Assembly Fits

Brief assembly registers as a hook in `SessionMemoryCoordinator` using
the existing `registerSessionStartHook` pattern (P23-AUD-07, P23-AUD-08).
It fires at `onSessionStart()` — no identity dependency, no ordering
constraint relative to `ConversationIdentityCoordinator`.

The full session-start sequence with Context Injection additions marked:

```
Firebase auth stable
    ↓
runAssistantInitialization()
    ↓
Agent registration
    ↓
SessionMemoryCoordinator.onSessionStart(userId) fires all hooks:
    → MemoryWarmStartAgent hook [RETIRED in this phase]
    → SessionBriefBuilder hook [NEW — checks cache; assembles async on IO]
    → ActiveEntityResolver hook [unchanged]
    ↓
[session active]
[SessionBriefBuilder assembling async on Dispatchers.IO]
    ↓
SessionBriefHolder populated when assembly completes
    ↓
First Live-path turn triggers GeminiLiveSession.obtain()
    ↓
GeminiLiveClient.buildSetupMessage()
    → MemoryInjectionBuilder reads SessionBriefHolder
    → Household brief in systemInstruction (if populated)
    ↓
Live WebSocket opens — Zola knows her world
    ↓
Phase 22 identifies active speaker during session
    → Zola applies context for that speaker from brief already in hand
```

### Session End

`SessionBriefHolder.clear()` is called at session end. The date-keyed
cache entry persists through the reuse window. The brief is never
persisted to Firestore — it is always assembled fresh from durable
sources at each new session (or served from the short-lived reuse cache
on rapid reconnects).

### Interaction with Existing Lifecycle Hooks

The `SessionBriefBuilder` start hook is additive. It does not interfere
with Phase 20 resurfacing and emotion enrichment hooks or Phase 22
`ProvisionalEnrollmentManager` and `RefinementSampleCollector` hooks.
Because the household brief has no identity dependency, no hook ordering
constraint exists between `SessionBriefBuilder` and
`ConversationIdentityCoordinator` initialization.

---

## Section 9 — RTDB as a Known Liability

**P42 audit closeout (2026-07-07, baseline `477e2a4`):** Two of three
historically documented liabilities are **resolved in code**. Remaining
RTDB retirement work is scoped to the turn-by-turn conversation mirror
(`users/{userId}/conversations`) and its readers — not the liabilities
below.

**Duplicate entries per Live turn — RESOLVED (P38-E).**
`OQ-P17-RTDB-DUAL-WRITE` is closed. `ResponseExecutionService.onFinalSynced`
no longer writes RTDB conversation entries for Live turns; the
authoritative Live write is `MainActivity.onTurnComplete` →
`FirebaseHelper.saveConversation`. See `DESIGN_DECISIONS.md` P38-E.

**Incomplete purge — RESOLVED (P0-B / current purge path).**
`MemoryService.clearAllMemoryAndContext` calls
`FirebaseHelper.purgeAllRealtimeDatabaseUserMirror`, which deletes
`users/{userId}/conversations` and `users/{userId}/memory`.

**Legacy loadUserMemory path — RESOLVED (removed).**
`FirebaseHelper.loadUserMemory` has zero Kotlin call sites on the audited
baseline.

**Remaining liability — turn-by-turn conversation mirror.**
RTDB `conversations` push log is the sole durable store for
`ConversationEntry` turn history (last-30 routing, handoff `recentHistory`,
proactive-turn mirror). No Firestore equivalent exists today. Safe RTDB
deletion requires a replacement store (developer direction: Option A —
new Firestore collection) or explicit feature retirement. See
`zola-architecture/audit/P42/Zola_P42_Audit_SYNTHESIS.md` (P42-AUD-01,
P42-AUD-14) and `OQ-P42-01`.

`SessionBriefBuilder` does not read from RTDB. Context Injection
introduces no new RTDB dependencies.

---

## Section 10 — Open Questions

**OQ-PCI-01 — Named constant calibration**
Default values: `SESSION_BRIEF_MAX_CHARS = 2000`,
`SESSION_BRIEF_REUSE_WINDOW_MS = 300_000`, `SESSION_BRIEF_SUMMARY_MAX_CHARS = 300`.
All three must be validated on device across single-person sessions,
multi-person household sessions, and sessions following long prior
conversations with many open loops. The entity roster cap (6 entities)
and open loop cap (5 items) should also be validated empirically.

**OQ-PCI-04 — MemoryWarmStartAgent retirement test coverage**
The Phase 6 architecture test confirming warm start read-only behavior
and Stage 6–9 exclusion must be rewritten to cover `SessionBriefBuilder`'s
equivalent constraints: read-only, no recall pipeline invocation, no
Firestore writes. See migration path step 7.

**OQ-PCI-06 — Brief assembly latency at session open**
Brief assembly is fire-and-forget. If `SessionBriefHolder` is empty
when `buildSetupMessage()` is called, the session opens without brief
context. Under normal conditions the assembly window is adequate. The
edge case is cold cache plus fast first turn plus slow Firestore reads.
The accepted policy is graceful cold-open — the session proceeds without
brief content rather than blocking. This should be validated on device
under degraded connectivity conditions.

---

## Section 11 — Closed Questions (Resolved by Design Change)

The following open questions from v1.1 are closed. They were resolved by
adopting the household-scoped brief model in v1.2.

**OQ-PCI-02 — SessionSummary speaker scoping** — CLOSED. The household
brief uses the most recent `SessionSummary` without speaker scoping.
No schema change to `SessionSummary` is required.

**OQ-PCI-03 — ConversationIdentityCoordinator availability at hook time**
— CLOSED. The household brief has no identity dependency. Assembly fires
at `onSessionStart()` without waiting for speaker identity.

**OQ-PCI-05 — OpenLoopTracker speaker scoping** — CLOSED. The household
brief includes all open loops without speaker filtering. No schema change
to `OpenLoop` is required.

**OQ-PCI-07 — Gemini Live mid-session system instruction update support**
— CLOSED. The delta-brief mechanism has been retired. No mid-session
injection is required.

---

*Document created: post-Phase 22 planning cycle*
*Document version: 1.3 — internal-context-only principle; behavioral instruction wrapper added*
*Status: Draft — ready for lore integration and build plan*
*Base SHA: c011c09*
*Next step: commit updated architecture document, update lore, begin Phase 23 T0 prompt*
