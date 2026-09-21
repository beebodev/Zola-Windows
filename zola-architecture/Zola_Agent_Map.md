# Zola Agent Map — Complete Reference

> **Core Rule (applies to every agent without exception):**
> Agents prepare. The core decides. No agent writes to memory, speaks, executes tools, or holds routing authority.

---

## Foundation Layer
*Must exist before other agents are meaningful*

---

### Agent 12 — World State Snapshot Agent
**Priority: Foundation — everything else reads from this**

**What it is:**
The single authoritative picture of what is happening right now. Location, device state, activity, time-of-day window, noise level, focus state, availability, others-present flag. Every other agent and the core reads from this instead of assembling their own picture from raw signals.

**What it watches:**
GPS/geofence, Bluetooth state, DND state, call state, audio environment, time-of-day, Health Connect activity signal, calendar busy state.

**What it produces:**
`WorldStateSnapshot` — a timestamped, confidence-annotated struct. Each field carries its own `lastUpdatedMs` and `confidence` value. Consumers know exactly how fresh and how reliable each dimension is. This maps closely to the existing `CurrentUserState` — the goal is to make that the single canonical read target, not assemble it piecemeal.

**Where it enters the core:**
`CurrentUserState` / `CurrentContextCache` — read by `AttentionRelevanceEngine`, `ProactiveAutonomousEngine`, `QueryProcessor`, and all other agents.

**Must never:**
Make interruption decisions. Produce speech. Override signal conflicts optimistically — when signals disagree, the more cautious interpretation wins.

**Staleness rule:**
Per-field TTLs matching the `CurrentUserState` architecture table. On-change events take priority over periodic readings. If a field is stale, it returns the last known value with `confidence: 0` — never blocks.

**Status:** `CurrentUserState` exists and is substantially built. Needs unification so all reads go through one canonical object instead of scattered signal reads.

---

## Background Preparation Agents
*Run continuously or on schedule, independent of active conversations*

---

### Agent 1 — Context Cache Agent
**Priority: High**

**What it is:**
A continuously running background worker that keeps environmental context warm — weather, traffic, calendar events in the next 24 hours, location state. The core never waits on a live API call for data that should already be available.

**What it watches:**
Weather API, Google Calendar, traffic data, location state from `WorldStateSnapshot`.

**What it produces:**
`CurrentContextCache` — a structured cache of pre-fetched environmental data. Each entry carries `fetchedAtMs`, `ttlMs`, and a `stale` flag. When TTL expires, the entry is marked stale but not removed — the core can still use it with reduced confidence while the refresh runs in the background.

**Where it enters the core:**
Read directly by `QueryProcessor`, `ProactiveAutonomousEngine`, `GeneralIntentHandler`, and the Tool Warm-Start Agent (Agent 8).

**Must never:**
Trigger proactive turns. Write to memory. Present stale data as current without the staleness flag.

**TTLs:**
Weather: 15 min. Calendar: 5 min. Traffic: 3 min. Location-derived context: 2 min.

**Status:** Partially built as fragmented poll loops in `MainActivity`. Needs consolidation into a unified cache with TTL metadata.

---

### Agent 2 — Memory Consolidation Agent
**Priority: High — already in Phase 5**

**What it is:**
Post-session and nightly background worker. Reviews candidate memories from the session, re-scores salience with full session context, promotes worthy candidates through the Memory Write Pipeline, closes resolved open loops, writes the session summary, and flags cognitive tension candidates.

**What it watches:**
Session close signal (`CONSOLIDATION_TRIGGER`), episodic pending store, open loop tracker, nightly schedule.

**What it produces:**
Written memory candidates (via pipeline with full authority checks), session summary document, updated open loop states, cognitive tension candidates.

**Where it enters the core:**
All writes route through `DurableWriteAuthority` and `DurableCollectionWriteGateway`. Session summary enters the episodic store. Cognitive tension candidates enter the `AttentionModel`.

**Must never:**
Run during an active live conversation. Write directly to Firestore outside the pipeline. Promote memories that didn't pass salience scoring.

**Staleness rule:**
Session-end trigger fires once per session close. Nightly trigger fires once per night. If missed, runs on next available background window.

**Status:** Foundation exists in `ConsolidationLoop.kt`. Several steps still stubbed. Phase 5 Track A work.

---

### Agent 5 — Proactive Trigger Monitor Agent
**Priority: Medium — substantially built**

**What it is:**
Continuously watches for conditions that might warrant a proactive turn — approaching calendar events, traffic building near a known route, open loops aging past threshold, stale projects, weather alerts, significant notification arrivals. Generates scored trigger candidates. Does not decide to speak.

**What it watches:**
Calendar events (upcoming within 60 min), traffic signals, weather alerts, open loop aging, active goals stalled, notification priority queue.

**What it produces:**
`ProactiveTriggerCandidate` objects with urgency score, trigger type, context payload, and `producedAtMs` timestamp.

**Where it enters the core:**
`EnvironmentalEventBus` → `ProactiveAutonomousEngine` → `AttentionRelevanceEngine` → `Response Governor`.

**Must never:**
Trigger a proactive turn directly. Bypass quiet hours or the `Response Governor`. Emit more than one candidate per trigger type per evaluation window.

**Staleness rule:**
Each candidate carries `producedAtMs`. The `Response Governor` discards candidates past their domain relevance window — traffic alerts: 10 min, birthday reminders: valid all day, weather alerts: until condition clears.

**Status:** Substantially built. `ProactiveAutonomousEngine` and `EnvironmentalEventBus` handle the core path. Needs structured candidate expiry metadata.

---

### Agent 6 — Notification Priority Agent
**Priority: Medium**

**What it is:**
Watches the Android notification stream, classifies incoming notifications by urgency and relationship relevance, and produces prioritized summaries for the core to surface when appropriate. Uses the entity memory graph to weight known senders higher.

**What it watches:**
Android `NotificationListenerService`, sender identity against entity graph, notification content type (message vs. alert vs. calendar vs. financial vs. spam).

**What it produces:**
A prioritized `NotificationSummary` queue — classified, deduplicated notifications with urgency score, sender relationship weight, and expiry time.

**Where it enters the core:**
`EnvironmentalEventBus` as a typed `EventPayload.PrioritizedNotification`. `ProactiveAutonomousEngine` evaluates against timing rules before surfacing.

**Must never:**
Read notification content without permission. Surface message content in a shared-space environment without privacy checks. Store notification content in durable memory without the write pipeline.

**Staleness rule:**
Messages: 15 min. Calendar alerts: until event time. Weather alerts: until condition clears. General: 5 min.

**Status:** `NotificationNudge` payload type exists. Full classification and entity-aware prioritization not built.

---

### Agent 7 — Behavioral Pattern Agent
**Priority: Low / Long-term**

**What it is:**
Slow post-session and nightly agent. Analyzes interaction history for patterns — timing preferences, response length preferences, proactive turn hit/miss rates, topics the user engages with vs. ignores. Updates the `StyleProfile` in `Behavioral Memory`.

**What it watches:**
Session engagement traces, proactive turn outcomes, explicit feedback signals, response length signals, topic engagement patterns.

**What it produces:**
Updated `StyleProfile` entries in `Behavioral Memory`, timing tolerance adjustments, proactive trigger suppression rules for consistently ignored trigger types.

**Where it enters the core:**
`Behavioral Memory` → read by `Emotional Regulation Layer`, `Autonomous Trigger Engine`, and `Response Governor` at decision time.

**Must never:**
Modify truth-handling behavior, privacy boundaries, or safety behavior. Override explicit user corrections. Run during a live session.

**Status:** Not built. Requires solid engagement trace infrastructure first. Phase 6+.

---

## Session-Start Agents
*Fire when a session opens, preload context before the first turn*

---

### Agent 4 — Memory Warm-Start Agent
**Priority: High — depends on Phase 5 Track A completing first**

**What it is:**
Fires at session start and speculatively pre-loads the most likely relevant memory context before the user says anything. Instead of waiting for the first query to trigger recall, this agent does an anticipatory pass based on time-of-day, location, last session summary, open loops, active goals, and today's calendar.

**Think of it like:** A good assistant who reviews your notes and calendar before your morning standup so relevant context is already on the table when you walk in.

**What it watches:**
Session start event, `WorldStateSnapshot`, last session summary, open loop tracker, active goals, calendar events today.

**What it produces:**
`WarmMemoryContext` — top episodic matches for likely today's topics, active open loops, relevant structured facts pre-fetched, active goals summary. Each entry carries a confidence score and `fetchedAtMs`.

**Where it enters the core:**
Injected into `ConversationContextSnapshot` as a warm-start block. `QueryProcessor` and `GeneralIntentHandler` read from it before triggering a full recall pass. If a live recall produces a higher-confidence result, the live result wins.

**Must never:**
Speculatively write new memory. Override a live recall result. Inject memory that hasn't passed confidence thresholds.

**Staleness rule:**
Built once at session start. Refreshes if the session idles more than 30 minutes before the next turn.

**Status:** Not built. `EpisodicContextAssembler` and `HandoffContextSerializer` contain relevant pieces. Depends on Phase 5 Track A recall pipeline work.

---

### Agent 9 — Active Entity Resolver Agent
**Priority: High**

**What it is:**
At session start — and updating as topic movement is detected — keeps a hot pre-resolved entity set for the people, vehicles, projects, and places most likely to be relevant. "Who are we talking about?" is expensive to resolve cold. Having Double R, Bumblebee, Micah, the shop, Madden, and active projects pre-resolved means entity context is available instantly when needed.

**What it watches:**
Session start event, last session summary, active projects, recent conversation topics, topic movement signals from `Streaming Cognition` (read-only observation).

**What it produces:**
`ActiveEntitySet` — pre-resolved entity records with relationship context, confidence scores, and `resolvedAtMs` timestamps.

**Where it enters the core:**
`CurrentContextCache` → read by `QueryProcessor`, `RecallPipeline`, entity resolution stages.

**Must never:**
Write new entities to the entity graph. Override a live entity resolution result. Hold stale resolved entities beyond topic context change without decay.

**Staleness rule:**
Refreshed at session start and when topic movement signals a context shift. Individual entities decay from the hot set if not referenced within the session window.

**Status:** Not built. Entity resolution infrastructure exists. Warm-caching layer needed.

**Planned scope extension (Phase 12):**
When full cross-domain correlation is built in Phase 12, Agent 9's
scope expands to include `ContactRelationshipIndex` maintenance —
building and keeping fresh a persistent index of known contacts
with cross-domain association signals: calendar co-occurrence
frequency, Gmail interaction frequency, memory entity links, and
relationship weight scores. This is the contact-domain extension
of Agent 9's existing entity resolution work. Do not build
`ContactRelationshipIndex` as a separate agent. Design Agent 9's
full implementation to accommodate this scope from the start so
it does not need to be rebuilt.
See `zola-architecture/Zola_CrossDomain_Correlation_Architecture.md`
for the full `ContactRelationshipIndex` specification.

---

## Live Turn Agents
*Active during a conversation turn, feed hints into the pipeline*

---

### Agent 8 — Tool Warm-Start Agent
**Priority: High**

**What it is:**
Pre-fetches likely tool results — weather, traffic, calendar details, recent messages, shop context, active project data — based on the current context and recent turn patterns. When Zola needs to answer a question that would normally require a live tool call, the result is already warm.

**What it watches:**
`WorldStateSnapshot`, `CurrentContextCache`, active entity set, recent turn history, time-of-day context (morning → likely weather/calendar, driving → likely traffic, shop mode → likely project/parts data).

**What it produces:**
`WarmToolContext` — pre-fetched tool results with `fetchedAtMs`, `ttlMs`, and explicit `isStale` flag per result.

**Where it enters the core:**
Readable by `QueryProcessor` and intent handlers before triggering a live tool call. If the warm result is within TTL and confidence threshold, it's used. If stale or below threshold, a live fetch runs and replaces it.

**Must never:**
Present stale results as current facts. Bypass the tool authorization pipeline. Pre-execute tools that require user confirmation. Cache sensitive data (messages, financial data) beyond its TTL.

**TTLs:**
Weather: 10 min. Traffic: 3 min. Calendar: 5 min. Messages: 2 min. Project/shop data: 15 min.

**Status:** Not built as a unified agent. Individual tool fetches exist. Needs consolidation into a context-aware warm cache with TTL and staleness metadata.

---

### Agent 3 — Attention Context Agent
**Priority: Medium**

**What it is:**
Maintains a running model of attention-relevant priors so the real-time `ConversationalAttentionAuthority` can score incoming speech faster and more accurately. Pre-computes who is typically present at this time and location, what topics are active, what the continuation window state is.

**Think of it like:** A sports analyst who has the stats sheet ready before the play starts so the decision-maker doesn't have to look anything up mid-moment.

**What it watches:**
Behavioral memory, time-of-day, location context (home vs. shop), recent interaction frequency, continuation window state, `WorldStateSnapshot`.

**What it produces:**
`AttentionContextHints` — pre-scored directedness priors, active topic list, known speaker context, continuation window readiness flag.

**Where it enters the core:**
Read by `ConversationalAttentionAuthority` as hint input only. The Authority still makes the final call. Hints improve speed and accuracy.

**Must never:**
Make the final attention decision. Override the `ConversationalAttentionAuthority`. Suppress speech the Authority hasn't evaluated. Create a second routing path.

**Staleness rule:**
Refreshed at session start and every 5 minutes during an active session. If hints are stale when speech arrives, the Authority falls back to base scoring — no blocking.

**Status:** Not built. Depends on `ConversationalAttentionAuthority` being built first.

---

### Agent 11 — Speculative Intent (Streaming Cognition feature, not a standalone agent)

The speculative intent work belongs to the `Streaming Intent Forecaster` inside the Streaming Cognition Architecture. It already has a defined home: `ProvisionalCognitionArtifact.provisionalIntentCandidates`. Building this as a separate agent would create a second routing authority. Build it as part of Streaming Cognition when that system is implemented.

---

## Infrastructure Agent

---

### Agent 14 — Compute Priority Scheduler
**Priority: Medium now, critical later**

**What it is:**
Governs which background workers run when, ensuring live speech and active reasoning always get highest CPU and I/O priority. Without this, consolidation loops, cache refreshes, and entity resolution can compete with live voice processing and cause audio stutters or response delays on lower-end hardware.

**What it watches:**
`isConversationActive` flag, turn state, agent workload signals, device performance headroom.

**What it produces:**
Execution priority decisions — run, yield, pause, defer — for each background agent based on current system state.

**Where it enters the core:**
Core runtime worker scheduler. Every background agent checks in before doing expensive work.

**Priority tiers:**

| Tier | Work | Yields? |
|------|------|---------|
| 1 | Live speech capture and STT | Never |
| 2 | Active turn reasoning and response | Never |
| 3 | TTS playback | Never |
| 4 | Tool warm-start and entity resolution | Yield during active turn |
| 5 | Context cache refresh | Yield during active turn, run between turns |
| 6 | Proactive trigger monitor | Run between turns |
| 7 | Memory consolidation and behavioral pattern | Run only when idle or session-end triggered |

**Must never:**
Delay or preempt live speech processing. Make behavioral decisions. Determine what Zola says or does.

**Status:** Not built as a formal system. The `isConversationActive` flag pattern already exists in parts of the codebase. Needs formalization before the full agent fleet is running.

---

### Agent 15 — DailyBriefAgent
**Priority: Medium — Phase 10**

**What it is:**
`DailyBriefAgent` (Agent 15) assembles the user's daily brief and
packages it for spoken delivery. It reads warm data exclusively
from `WarmToolContextProvider` (Agent 8) — no direct calendar,
weather, Gmail, or traffic API calls. `DailyBriefAssembler` and
`EmailIntelligenceAnalyzer` perform analysis and correlation;
`BriefPromptBuilder` produces the synthesis prompt; the finished
package is stored in `BriefContextStore`. `BriefDeliveryCoordinator`
owns delivery timing and gates; Zola speaks via
`ResponseExecutionService.executeAssistantInitiatedTurn`. Agent 15
prepares only — it never speaks, never writes to memory, and holds
no routing authority.

**What it watches:**
First Live session start of the day within the brief window.
`DailyBriefSettings.isEnabled` and `lastDeliveredDate` deduplication.
On-demand assembly triggers from the user path (separate from the
morning slot).

**What it produces:**
`BriefPackage` in `BriefContextStore` — structured brief context
plus a `BriefPromptBuilder` prompt string ready for committed-script
Live delivery through `BriefDeliveryCoordinator`.

**Where it enters the core:**
`BriefContextStore` → `BriefDeliveryCoordinator` →
`ResponseExecutionService.executeAssistantInitiatedTurn`.

**Must never:**
Speak. Write to memory. Hold routing authority. Call external APIs
for warm data (delegates to Agent 8). Persist email body content
outside the brief pipeline boundary.

**Key dependencies:**
- Agent 8 (`WarmToolContextProvider` / Tool Warm-Start) — sole warm
  data source
- `BriefDeliveryCoordinator` — delivery gate and Live send
- `DailyBriefAssembler` — multi-source assembly
- `BriefPromptBuilder` — synthesis prompt packaging
- `EmailIntelligenceAnalyzer` — inbox triage and Stage 4 pass
- `BriefContextStore` — in-memory single-slot package holder

**Phase introduced:** Phase 10

**Staleness rule:**
Brief package expires 4 hours after assembly. Expired packages are
discarded silently. On-demand requests trigger fresh assembly
regardless of prior delivery state.

**Status:** Active — implemented Phase 10; Phase 11 extends email
analysis (Stage 4) and post-brief feedback signals (Track 4).

**Full specification:**
`zola-architecture/Zola_Daily_Brief_Architecture.md`

---

## Summary Table

| # | Agent | Priority | Status | Produces | Enters Core Via |
|---|---|---|---|---|---|
| 12 | World State Snapshot | **Foundation** | Mostly built, needs unification | `WorldStateSnapshot` | `CurrentUserState` / `CurrentContextCache` |
| 1 | Context Cache | High | Partial, fragmented | `CurrentContextCache` | Direct read by core |
| 2 | Memory Consolidation | High | Foundation exists, stubs remain | Memory writes, session summary | `DurableWriteAuthority` / pipeline |
| 4 | Memory Warm-Start | High | Not built — needs Phase 5 first | `WarmMemoryContext` | `ConversationContextSnapshot` |
| 5 | Proactive Trigger Monitor | Medium | Substantially built | `ProactiveTriggerCandidate` | `EnvironmentalEventBus` |
| 6 | Notification Priority | Medium | Partial | `NotificationSummary` queue | `EnvironmentalEventBus` |
| 7 | Behavioral Pattern | Low / Long-term | Not built | `StyleProfile` updates | `Behavioral Memory` |
| 8 | Tool Warm-Start | High | Not built | `WarmToolContext` | `QueryProcessor` / intent handlers |
| 9 | Active Entity Resolver | High | Not built | `ActiveEntitySet` | `CurrentContextCache` |
| 3 | Attention Context | Medium | Not built | `AttentionContextHints` | `ConversationalAttentionAuthority` |
| 11 | Speculative Intent | — | Lives inside Streaming Cognition | `provisionalIntentCandidates` | `ProvisionalCognitionArtifact` |
| 14 | Compute Priority Scheduler | Medium → Critical | Not built | Priority decisions | Core runtime worker scheduler |
| 15 | DailyBriefAgent | Medium | **Active** (Phase 10) | `BriefContextStore` / `BriefPackage` | `BriefDeliveryCoordinator` → `ResponseExecutionService` |

---

## Recommended Build Order

### Phase 6 — Foundation and highest-value wins
Unify Agent 12 → Build Agent 4 → Build Agent 8 → Consolidate Agent 1

### Phase 7 — Conversational intelligence
Agent 9 → Agent 3 → Agent 14 (formalize the scheduler before the fleet gets bigger)

### Phase 8 — Long-running maturity
Agent 6 → Agent 7 → Streaming Cognition with Agent 11 baked in

---

*Generated during Zola architecture planning session. Store in `zola-architecture/` alongside other domain architecture documents.*
