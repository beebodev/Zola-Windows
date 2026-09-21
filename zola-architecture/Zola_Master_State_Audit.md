# Zola Master State Audit

**Created:** 2026-05-26
**`zola-main` tip at audit time:** `c7aca30` (Phase 39 consolidated lore closeout); prior baseline `bd6fd3c` (Phase 38 complete).
**Audit basis:** Architecture documents, build plans, audit reports, and lore through **Phase 39 exit** (open-question backlog prioritization on `zola-main`).
**Purpose:** Ground-truth inventory of where Zola stands against the full intended architecture. Every domain, every layer, every agent. Basis for long-range roadmap.

---

## How to Read This Document

### Status Ratings

| Symbol | Meaning |
|--------|---------|
| ✅ Built | Exists, wired, and working in production code |
| ⚠️ Partial | Exists but incomplete, unwired, or not fully meeting spec |
| ❌ Not Built | Designed in architecture docs, does not exist in code |
| 🔒 Deferred | Deliberately deferred with documented rationale and phase label |
| 📐 Design Only | Architecture document exists, no implementation started |

### Tier Ratings (Prioritization)

| Tier | Meaning |
|------|---------|
| T1 | Phase 9 — complete deferred work, small unlocks |
| T2 | Phase 10 — high value, requires design work or prerequisite |
| T3 | Phase 11+ — major new system, dedicated design phase required |

---

## Domain 1 — Speech and STT Pipeline

### What Is Working Well
The speech pipeline is functionally sound for the primary foreground use case. Deepgram STT, final transcript delivery, the `TranscriptDeliveryContract` boundary, and the streaming observation layer (Phase 8) are all in place. Continuous listening works correctly when the app is in the foreground — no wake word is required or intended.

### Two Distinct Gaps
There are two separate speech activation gaps that are often conflated but require different solutions:

**Gap 1 — Foreground name detection reliability:** When the app is already open and listening, Zola sometimes requires the user to say her name more than once. This is a calibration and tuning issue in the existing foreground pipeline — likely in Deepgram turn gate timing, name detection sensitivity, or attention scoring. This is a Phase 9 item.

**Gap 2 — Background activation:** When the app is backgrounded, Zola cannot hear her name at all. `ListeningService` exists as a background foreground service but does nothing useful — Picovoice was removed and never replaced. There is no VAD, no name detection, and no auto-foreground trigger. The user must manually open the app. The architecture defines a full two-tier perceptual model (Watchdog + Active Perception) to solve this properly, but none of it is built. This is a Phase 10 item — significant new infrastructure with open design questions (VAD library selection, foregrounding level policy, foreground service notification implications).

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| Deepgram STT (foreground) | ✅ Built | — | Primary speech path |
| Final transcript delivery | ✅ Built | — | `TranscriptDeliveryContract` enforced |
| Continuous foreground listening | ✅ Built | — | Always-on when app is foregrounded; no wake word required |
| Foreground name detection reliability | ⚠️ Partial | T1 | Sometimes requires multiple utterances; calibration/tuning needed in turn gate or name detection path |
| `ListeningService` background service | ⚠️ Partial | T2 | Service exists and holds wake lock; Picovoice removed; does not detect name, does not trigger STT, does not foreground app |
| Watchdog tier — VAD background audio detection | ❌ Not Built | T2 | Architecture defined in `Zola_Architecture_Perceptual_Input_Layer.md`; no implementation; VAD library not selected |
| Watchdog tier — name / voice activity → foreground trigger | ❌ Not Built | T2 | Core of background activation model; auto-foreground on name detection not built |
| Active Perception tier | ❌ Not Built | T2 | Full audio/vision analysis on Watchdog handoff; not started |
| Three-level foregrounding model (ambient / soft / hard) | ❌ Not Built | T2 | Architecture defined; Level 1-3 foregrounding logic not implemented |
| Partial transcript observation | ✅ Built | — | Phase 8 Track 4, observation only |
| `StreamingTurnState` | ✅ Built | — | Phase 8, Deepgram-specific |
| `StablePhraseDetector` | ✅ Built | — | Phase 8 |
| `ProvisionalCognitionArtifact` | ✅ Built | — | Phase 8 — `isCommitEligible` always false |
| `StreamingCognitionObserver` | ✅ Built | — | Phase 8, wired into Deepgram engine |
| Utterance ID contract | 🔒 Deferred | T1 | `startSec` workaround in Phase 8; proper contract needed before Stage 2 |
| Engine-neutral streaming observer interface | 🔒 Deferred | T1 | P8-FLAG-4; needed before non-Deepgram providers added |
| Streaming Stage 2 — provisional candidate generation | ❌ Not Built | T1 | Intent forecaster, entity tracker, memory/tool candidate selectors, correction detector, interruption classifier |
| Streaming Stage 3 — hint promotion into final pipeline | ❌ Not Built | T2 | Requires commit authority design; most sensitive phase in streaming roadmap |
| Streaming Stage 4 — interruption/barge-in | ❌ Not Built | T2 | Requires Live transport cancellation API |
| Streaming Stage 5 — topic stack integration | ⚠️ Partial | T2 | Focus stack exists (Phase 8); streaming-to-continuity bridge not yet built |
| Streaming Stage 6 — cognitive draft buffer | ❌ Not Built | T3 | Long-horizon |
| Barge-in handling | ❌ Not Built | T2 | `DuplexGuard` removed; nothing replaced it |
| `ConversationalAttentionAuthority` | ❌ Not Built | T2 | No inbound directed speech authority exists; outbound attention engine (`AttentionRelevanceEngine`) is not a substitute |
| `DirectedSpeechScorer` | ❌ Not Built | T2 | Prerequisite for Agent 3 |
| Proactive speech `HeatEvent.ProactiveSpeechOccurred` emission | ✅ Built | — | `ResponseExecutionService.executeAssistantInitiatedTurn` applies `HeatEvent.ProactiveSpeechOccurred` after successful Live send (P9-T9); coordinator delegates after Agent 6 approve (P9-T8). |
| Centralized assistant-initiated turn path | ✅ Built | — | `ProactiveDeliveryCoordinator` → `ResponseExecutionService.executeAssistantInitiatedTurn` (identity, polish, `TurnResponseGuard`, Live, heat, RTDB with `ResponseOwnership.ASSISTANT_INITIATED`) (P9-T9). Parallel entry — does not route through `QueryProcessor`. |
<!-- Corrected P9-D06 (pre-build): Was recorded as bypassing TurnResponseGuard; guard now gates proactive turns inside RES assistant-initiated path. -->
<!-- Corrected P9-D06 (pre-build): Was recorded as never emitting ProactiveSpeechOccurred; emission in RES on successful assistant-initiated delivery (P9-T9). -->
<!-- Corrected P9-D06 (pre-build): Was recorded as not persisting proactive turns; RTDB save with ownership marker in RES (P9-T9). -->

---

## Domain 2 — Memory and Storage

### What Is Working Well
The memory pipeline is substantially complete. Write pipeline (11 stages), recall pipeline (9 stages), privacy filter, consolidation foundation, warm-start, open loop tracking, and episodic promotion are all in production. This is the most complete domain in the system.

### Key Gaps
LLM-enriched session summaries and the behavioral pattern / style learning agent are the main outstanding items. Agent 7 has no production callers and remains a design-only component.

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| `MemoryWritePipeline` (11 stages) | ✅ Built | — | Phases 3-4 |
| `RecallPipeline` (9 stages) | ✅ Built | — | Phases 4-5 |
| `ResponsePrivacyFilter` | ✅ Built | — | Phase 4 |
| `SacredMemoryClassifier` | ✅ Built | — | Phase 4 |
| `ConsolidationLoop` Steps 1-2 | ✅ Built | — | |
| `ConsolidationLoop` Step 3 — episodic promotion | 🔒 Deferred | T2 | Explicitly deferred; `PendingMemoryStore` has no episodic tier |
| `ConsolidationLoop` Step 6 — session summary enrichment | ⚠️ Partial | T2 | Rule-based only; no LLM enrichment at consolidation time |
| `NightlyConsolidationScheduler` | ✅ Built | — | Phase 6, wired at auth-stable |
| `OpenLoopTracker` | ✅ Built | — | |
| `EpisodicPromotionManager` | ✅ Built | — | |
| `PendingMemoryStore` | ✅ Built | — | |
| `MemoryWarmStartAgent` (Agent 4) | ✅ Built | — | Phase 6 Track F |
| Agent 7 — Behavioral Pattern / Style Learning | ❌ Not Built | T3 | `ENABLE_STYLE_PROFILE` false; no engagement trace / outcome loop; no production callers |
| Style learning from user feedback | ❌ Not Built | T3 | No dedicated subsystem; no feedback signal pipeline |
| Emotional memory tier | ❌ Not Built | T3 | Described in architecture; no implementation |
| Memory drift / persona consistency audit | ❌ Not Built | T2 | `IdentityBoundaries` is a light pattern pass; no scheduled consistency check |

### Phase 19 — World Memory Architecture (2026-06-11)

Phase 19 delivered the entity-native world memory foundation. Firestore is organized into a six-group hierarchy. The domain entity taxonomy covers seventeen types including SELF. Relationship writes route through `RelationshipWriteGovernor` with synchronous inference. The read path traverses graph edges instead of entity `role` attributes. Zola exists as a first-class SELF entity with PRIMARY_BOND and KNOWS_ABOUT awareness edges.

| Area | Status | Detail |
|------|--------|--------|
| Entity taxonomy | ✅ Built | Seventeen types: SELF, PERSON, PET, PLACE, ORGANIZATION, EVENT, PERIOD, ASSET, OBJECT, PROJECT, GOAL, CONCEPT, CREATIVE_WORK, MEDICAL, ROUTINE, SKILL, BELIEF |
| Firestore structure | ✅ Built | Six-group hierarchy live — `world`, `memory`, `profile`, `state`, `logs`, `brief`; centralized `FirestorePathRefs` |
| Relationship inference | ✅ Built | IR-01 reciprocal; IR-02 sibling from shared parent; IR-03 no chained inference; truth maintenance via `onSourceEdgeChanged` |
| Read path | ✅ Built | Edge traversal replaces role attribute; authority USER_STATEMENT > SYSTEM_INFERRED > SYSTEM; gender inferred from relationship role at write time |
| SELF entity | ✅ Built | Initialized at `zola_self_{userId}` on first launch; PRIMARY_BOND bidirectional to primary user; KNOWS_ABOUT on every new entity CreateEntity |
| Legacy model | ⚠️ Partial | `DynamicMemory.kt` and `HybridMemoryBridge.kt` still exist with active callers; whole-file deletion deferred to future dedicated phase (P19-T1-PARTB) |

**Known open items carried forward:** OQ-P19-REL-01, OQ-P19-REL-02, OQ-P19-REL-03, OQ-P19-TAX-01, OQ-P19-TAX-02, OQ-P19-TAX-03, OQ-P19-TAX-04, OQ-P19-FS-01, OQ-P19-FS-03, OQ-P19-BOND-01, OQ-P19-SCHEMA-01, OQ-P19-T3-RELID-01, OQ-P19-T3-PARSE-01, OQ-P19-T3-SELF-GENDER-01

**Merge SHAs:** P19-LORE `f7aecd6`; P19-T0 `0fde992`; P19-T1 `15429a5`; P19-T2 `d0bd0dd`; P19-T3 `c9f7698`; P19-T4 `08dc42e`

---

## Phase 20 Status — COMPLETE

**Tip SHA:** `0ca4ff7`
**Completed:** 2026-06-11

### Conversation Architecture Components

| Component | Status | Track | Notes |
|-----------|--------|-------|-------|
| Full frame persistence (`ConversationState`) | ✅ Built | T0 | All `ConversationContextSnapshot` fields durable; per-turn save; startup rehydration |
| Focus stack durability (`FocusStackManager`) | ✅ Built | T1 | Serialized to `focusStackJson`; depth cap 3; eviction to open loop |
| World model integration (active context) | ✅ Built | T2 | `activePrimaryEntityId`; `resolveEntityContext()` cache-only; `frameToTopic()` fix |
| Open loop lifecycle (`OpenLoopLifecycleManager`) | ✅ Built | T3 | Aging, promotion to `ActiveThread`, resolution contract, `PendingRecordType` discriminator |
| Initiative queue (`InitiativeQueue`) | ✅ Built | T4 | Firestore-persisted; five source adapters; tier model; relevance filter |
| Room-reading gate (`RoomReadingGate`) | ✅ Built | T5 | Four-signal directedness; emotional temperature; T4 stub replaced |
| Directedness dismissal refinement | ✅ Built | HF01 | Dismissal phrases suppress Signal 1 for 120s window |
| Turn intake directedness gate | ❌ Not Built | — | `OQ-P20-DIRECTEDNESS-01`; Phase 21 design candidate |
| Parallel delivery path retirement | ❌ Not Built | — | `OQ-P20-T4-CLEANUP-01`; Phase 21 cleanup |
| Per-loop urgency scoring | ❌ Not Built | — | `OQ-P20-URGENCY-01`; future track |
| Temporal self-awareness in conversation | ❌ Not Built | — | `OQ-P20-TIME-01`; future track |
| Episodic warm-start on stale frame expiry | ❌ Not Built | — | `OQ-P20-EPIS-01`; future phase |

### Key Architecture Decisions (Phase 20)

- **P20-D08:** Focus stack is now durable — Phase 8 session-local
  lock superseded; `FOCUS_STACK_MAX_DEPTH = 3`
- **P20-D11:** Four-signal directedness model: name detection
  (hard positive), second voice (suppressor), interaction recency
  (positive lean), conversational rhythm (suppressor); dismissal
  refinement adds suppression window
- **P20-D14/D15:** Dual emotional signal — `MoodTracker` per-turn
  for room-reading; `GeminiEmotionAnalyzer` async session-end only
- **P20-D04:** `RoomReadingGate` is the mandatory initiative
  delivery gate; fails to `CHECK_IN_REQUIRED` on exception;
  never bypassed

### Known Gaps and Open Questions

- `OQ-P20-DIRECTEDNESS-01` — Turn intake gate; Zola still responds
  to non-directed speech at `QueryProcessor` level
- `OQ-P20-T4-CLEANUP-01` — Four parallel proactive delivery paths
  still run alongside initiative queue (G-PARALLEL)
- `OQ-P20-URGENCY-01` — All open loops score identically on urgency;
  no per-loop urgency field yet
- `OQ-P20-TIME-01` — Zola has no temporal self-awareness of
  conversation recency ("that was five minutes ago")
- `OQ-P20-EPIS-01` — Stale frame expiry cold-starts; episodic
  memory not used for warm-start
- `OQ-P20-T5-SMOKE-01` — T4/T5 device smoke tests pending full
  verification
- Pre-existing `WriteAuthorityEnforcementTest` flake — documented
  in `OPEN_QUESTIONS.md`

### Test Suite at Phase 20 Exit

- **2257 tests** in `:app:testDebugUnitTest`
- **1 pre-existing failure** — `WriteAuthorityEnforcementTest`
  (unrelated to Phase 20 work; documented in lore)
- **Phase 20 tests added:** 54 new unit tests across T0–T5 and HF01

---

## Phase 21 Status — COMPLETE

**Phase:** 21 — Conversation Refinement
**Merge tip SHA:** 69fc507
**Date:** 2026-06-12

| Capability | Status | Track | Notes |
|------------|--------|-------|-------|
| Turn intake directedness gate | ✅ Built | T0 | handleQuery gate; dismissal window + name-presence check |
| Dismissal state writes | ✅ Built | T0 | TopicShiftDetector + ConversationalTurnClassifier |
| Engagement attribution gated | ✅ Built | T0 | onUserFinalTranscriptDispatched() post-gate only |
| Parallel delivery paths retired | ✅ Built | T1 | ProactiveAutonomousEngine enqueue-only; synthetic fallback removed |
| Initiative queue sole delivery authority | ✅ Built | T1 | ProactiveDeliveryCoordinator holds on empty queue |
| ContextualResurfacingEngine wired | ✅ Built | T1 | triggerResurfacingEvaluation() at session start |
| Temporal self-awareness | ✅ Built | T2 | TemporalRecencyFormatter; recency in Gemini Live memory block |
| Daily brief persistence | ❌ Not Built | — | OQ-P21-BRIEF-PERSIST-01 |
| Per-loop urgency scoring | ❌ Not Built | — | OQ-P20-URGENCY-01; future track |
| Episodic warm-start on stale frame | ❌ Not Built | — | OQ-P20-EPIS-01; future phase |
| Living Voiceprint system | ❌ Not Built | — | Phase 22 |

### Key Architecture Decisions (Phase 21)

- **P21-D10:** Dismissal writes at TopicShiftDetector and
  ConversationalTurnClassifier — two authorities, one field
- **P21-D11:** Intake gate uses dismissal window + "zola"
  name-presence check; DirectednessEvaluator remains on
  proactive delivery path only
- **P21-D07:** Empty initiative queue returns DeliveryPlan.Held;
  no synthetic fallback
- **P21-D08:** launchEvaluation() wired via
  triggerResurfacingEvaluation() after StateFlow collector start
- **P21-D09:** TemporalRecencyFormatter nine-band label system;
  "yesterday" band extended to < 2 days

---

## Phase 22 Status — COMPLETE

**Completed:** 2026-06-13
**Final zola-main tip:** `957028e`
**Architecture document:**
`zola-architecture/Zola_Architecture_Living_Voiceprint_MultiSpeaker.md`
(amended `f1d0f99`)

### Components Delivered

| Component | File | Status |
|-----------|------|--------|
| `EmbeddingPoolEntry` | `perception/identity/EmbeddingPoolEntry.kt` | ✅ Live |
| `VoiceEmbeddingStore` (pool schema) | `perception/identity/VoiceEmbeddingStore.kt` | ✅ Live |
| `VoiceIdentityMetadataWriter` | `perception/identity/VoiceIdentityMetadataWriter.kt` | ✅ Live |
| `SessionIdentityBus` | `perception/identity/SessionIdentityBus.kt` | ✅ Live |
| `SpeakerEvent` | `perception/identity/SpeakerEvent.kt` | ✅ Live |
| `IdentityTrackerConstants` | `perception/identity/IdentityTrackerConstants.kt` | ✅ Live |
| `LiveSessionIdentityTracker` | `perception/identity/LiveSessionIdentityTracker.kt` | ✅ Live |
| `ConversationIdentityCoordinator` | `perception/identity/ConversationIdentityCoordinator.kt` | ✅ Live |
| `ProvisionalEnrollmentManager` | `perception/identity/ProvisionalEnrollmentManager.kt` | ✅ Live |
| `RefinementSampleCollector` | `perception/identity/RefinementSampleCollector.kt` | ✅ Live |
| Audio tap on Deepgram | `speech/deepgram/DeepgramForegroundRecognitionEngine.kt` | ✅ Live |
| Session end hook registry | `memory/session/SessionMemoryCoordinator.kt` | ✅ Live |

### Existing Components Modified

| Component | Change |
|-----------|--------|
| `GatekeeperEngine` | Pool-based max cosine scoring (T0) |
| `VoiceEnrollmentScreen` | Calls `saveFormalEnrollment` (T0) |
| `MainActivity` | Identity stack start/stop wiring (T2–T5) |
| `VoiceEmbeddingStore` | `enrollmentState` param; `updateEnrollmentState`; `deleteEmbedding` → Firestore (T4) |

### Known Gaps at Closeout

| Gap | OQ | Phase Target |
|-----|----|--------------|
| Provisional embedding accumulation (empty pool on promotion) | OQ-P22-EMBED-ACCUM-01 | Phase 23 |
| AmbientConditionTag UNKNOWN for all refinement entries | OQ-P22-CONDITION-TAG-01 | Phase 23 |
| refinementCount store increment approximation | OQ-P22-REFINEMENT-COUNT-01 | Housekeeping |
| worldVoiceIdentitiesCollection() in FirestorePathRefs | OQ-P22-PATHREFS-01 | Housekeeping |
| OQ-VOICE-01 threshold calibration | OQ-VOICE-01 | Ongoing |
| OQ-VOICE-05 promotion threshold calibration | OQ-VOICE-05 | Ongoing |
| Settings panel UI for enrolled voices | — | Phase 23+ |
| linkedEntityId PERSON entity link | — | Future |

### Test Suite at Closeout

2282 pass, 9 skipped, 1 pre-existing failure
(`WriteAuthorityEnforcementTest` / `SelfEntityInitializer.kt` —
baseline from Phase 19; not introduced by Phase 22)

**Next step:** Phase 23 — await developer instruction.

---

## Phase 25 Status — COMPLETE

**Phase:** 25 — Brief Correctness and Voice Presence
**Date:** 2026-06-16
**Final `zola-main` tip:** `11c9751` (includes CAL direct commit; T3 merge `70defc0`)

### Tracks (merged / committed to `zola-main`)

| Track | Deliverable | Merge SHA |
|-------|-------------|-----------|
| T0 | Brief audio fragmentation audit — RESOLVED-BY-DESIGN | `2d0e114` |
| T1 | Memory `entityNames` wiring + calendar diagnostic log | `cc6ea22` |
| T2 | Zero-signal hallucination guard in `DailyBriefAssembler` | `b0771e2` |
| T3 | Voice presence greeting via `InitiativeQueue` | `70defc0` |
| CAL | `DEFAULT_STABLE_WINDOW_SIZE` 3→2 | `11c9751` |

### Components Built or Modified

| Component | Status | Notes |
|-----------|--------|-------|
| `DailyBriefAssembler` zero-signal guard | ✅ Built | Returns null on `signalTotal == 0`; P25-T2 |
| `CrossDomainCorrelator` entity name wiring | ✅ Fixed | `entityNames` was `emptyList()`; P25-T1 |
| Calendar timing diagnostic log | ✅ Added | `warmEntryNull=Y` log in assembler; P25-T1 |
| `ConversationIdentityCoordinator` greeting | ✅ Built | `greetedThisSession` gate; `enqueuePresenceGreeting()`; P25-T3 |
| `InitiativeCategory.SOCIAL_GREETING` | ✅ Added | urgency 0.85; P25-T3 |
| `InitiativeSource.IDENTITY_COORDINATOR` | ✅ Added | P25-T3 |
| `InitiativeQueueEvaluator` SOCIAL_GREETING branch | ✅ Added | G-NOCHANGE waiver D-T3-06; P25-T3 |
| `StablePhraseDetector` window size | ✅ Calibrated | 3→2; P25-CAL |

### Known Gaps at Closeout

| Gap | OQ | Notes |
|-----|-----|-------|
| Calendar timing race at brief assembly | OQ-HOTFIX-BRIEF-02 | Diagnostic added; full fix deferred |
| Voice greeting delivery timing unconfirmed | OQ-P25-GREETING-DELIVERY-01 | Enqueue path built; device delivery pending |
| Brief delivery async race (latent) | OQ-P25-BRIEF-MUTEX-01 | F-T0-01; not observed on device |

**Test suite at Phase 25 exit:** 2347 pass, 9 skipped, 0 fail
(`JAVA_TOOL_OPTIONS=-Duser.timezone=UTC` per OQ-P25-POLLER-TIMEZONE-01)

---

## Phase 26 Status — COMPLETE

**Phase:** 26 — Voice Robustness and Greeting Delivery
**Date:** 2026-06-16
**Final `zola-main` tip:** `80103b6` (lore closeout; T2 merge `6221ded`)

### Delivered

- **Proactive delivery loop:** live via PAE idle schedule + high-urgency
  fast-path callback
- **SOCIAL_GREETING cooldown bypass:** active in `NotificationPriorityPolicy`
- **isLiveTransportConnected guard:** active on fast-path
- **Voice match threshold:** `IN_SESSION_SIMILARITY_THRESHOLD = 0.72f`
- **Refinement suppression:** `AmbientConditionTag` gate active;
  diagnostic `AmbientConditionController` available
- **Calendar timing race:** bounded wait in `DailyBriefAssembler`;
  `withTimeoutOrNull(2000ms)`; `calendarWaitTimeout` fires outside morning
  window when warm agent does not run
- **Brief bypass cold-start:** confirmed resolved by P10-HOTFIX-4;
  deterministic routing at 0.98–1.0 confidence; T3 skipped

### Track merge SHAs

| Track | Merge SHA |
|-------|-----------|
| T0 Greeting delivery | `36ca9ab` |
| T1 Voice false match | `419e6a5` |
| T2 Calendar race | `6221ded` |
| T3 Brief bypass | Skipped (prior hotfix) |

**Test suite at Phase 26 exit:** 2347 pass, 9 skipped, 0 fail

---

## Domain 3 — Conversational State and Continuity

### What Is Working Well
Phase 8 delivered the continuity authority facade, session-local focus stack, deterministic branch-return detection, and return pointer metadata. The foundation is solid. Existing frame and follow-up resolution are proven and wired through the engine.

### Key Gaps
The focus stack is session-local only — it is lost on process death. Bridge phrase generation is the first user-visible continuity behavior and is the Phase 9 unlock. QueryProcessor still has direct references to continuity managers that need cleanup.

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| `ConversationFrameManager` | ✅ Built | — | |
| `ConversationContextManager` | ✅ Built | — | |
| `FollowUpService` / `FollowUpResolver` | ✅ Built | — | |
| `TopicShiftDetector` | ✅ Built | — | |
| `ActiveEntityTracker` | ✅ Built | — | |
| `ConversationalStateEngine` (facade) | ✅ Built | — | Phase 8 Track 1 |
| `ConversationalStateSnapshot` | ✅ Built | — | Carries focus, return pointer, topic shift |
| `FocusItem` / `FocusStack` / `FocusStackManager` | ✅ Built | — | Phase 8 Track 2; session-local only |
| `TopicReturnPointer` (schema) | ✅ Built | — | Phase 8 Track 2 |
| `BranchReturnDetector` | ✅ Built | — | Phase 8 Track 3; deterministic matching |
| Bridge phrase generation on topic return | ✅ Built | — | P9-T4; `BridgePhraseGenerator` + `ResponseExecutionService` prepend |
| Orchestration context integration with focus stack | ✅ Built | — | P9-T7; `OrchestrationContinuityBridge` in `ConversationalStateEngine` |
| `FollowUpService` direct reference in `QueryProcessor` | 🔒 Deferred | T1 | Phase 9; blocked by `ResponseExecutionService` dependency |
| `TopicShiftDetector` direct reference in `QueryProcessor` | 🔒 Deferred | T1 | Phase 9; handoff deferred from Track 2 |
| Focus stack persistence (durable) | ❌ Not Built | T2 | Session-local only; lost on process death; requires Firestore serialization design |
| Persistent topic graph | ❌ Not Built | T3 | Described in architecture; no implementation |
| Conversational state serialization for cross-device handoff | ❌ Not Built | T3 | Dependency on distributed presence design |
| Live citation metadata on response artifacts | 🔒 Deferred | T1 | Streaming architecture limitation; artifact created before metadata arrives |
| `PolishedResponseService` style hint wiring | 🔒 Deferred | T1 | Track 6 optional cleanup |

---

## Domain 4 — Attention and Routing

### What Is Working Well
The outbound attention pipeline — relevance engine, dampening controller, engagement governor — is functionally complete. QueryProcessor final routing authority is stable and well-guarded. Device-tool Live routing, grounding, and turn guard are all working.

### Key Gaps
The inbound attention architecture (`ConversationalAttentionAuthority`) does not exist. This is the highest-complexity missing system — it is what allows Zola to determine whether speech is directed at her without a wake word. Agent 3 is BLOCKED on it. Agent 14 (Compute Priority Scheduler) is only informally implemented.

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| `AttentionRelevanceEngine` / `DefaultAttentionRelevanceEngine` | ✅ Built | — | Outbound proactive gate; not inbound speech authority |
| `AttentionDampeningController` | ✅ Built | — | Heat decay model |
| `InterruptionCostAnalyzer` | ✅ Built | — | |
| `EngagementGovernor` | ✅ Built | — | Phase 5 |
| `QueryProcessor` — final routing authority | ✅ Built | — | Permanent owner; stable |
| `QueryRoutingService` / `KnowledgeRouter` | ✅ Built | — | Frozen |
| `DeviceToolsLiveIntentPolicy` | ✅ Built | — | Live-primary for device tools |
| `TurnResponseGuard` | ✅ Built | — | Turn ordering and commit authority |
| Google Grounding (standard query) | ✅ Built | — | Phase 7 Track 3A |
| Google Grounding (Live) | ✅ Built | — | Phase 7 Track 3B |
| Google Weather API | ✅ Built | — | Phase 7 Track 2 |
| News intent routing gap | ✅ Built | — | P9-T3; general NL current-event queries route through grounding (OQ-T3A-1 resolved) |
| `ConversationalAttentionAuthority` | ❌ Not Built | T2 | No inbound directed speech authority; this is the architectural center of always-on attention |
| `DirectedSpeechScorer` | ❌ Not Built | T2 | Required by `ConversationalAttentionAuthority` |
| Agent 3 — Attention Context | ❌ Not Built | T2 | BLOCKED — requires `ConversationalAttentionAuthority` first |
| `AttentionContextHints` | ❌ Not Built | T2 | No pre-scored directedness priors; no continuation-window state machine |
| `ComputePriorityScheduler` / Agent 14 | ⚠️ Partial | T1 | Informal `isConversationActive` patterns exist; no formal scheduler; increasingly critical as agent fleet grows |
| `maxPerHour` rate limit enforcement | ❌ Not Built | T2 | Dead configuration in `MonitorManifest`; `maxPerHour` field is never checked |

---

## Domain 5 — Environmental Awareness

### What Is Working Well
The environmental bus, core producers (location, weather, calendar, SMS, Gmail), current user state, context cache, and proactive trigger candidate pipeline are all in place from Phases 3-6. This is a solid foundation.

### Key Gaps
The Contextual Interpretation Layer — which converts raw events into meaningful situational understanding (familiar vs. unknown, expected vs. unexpected, normal vs. suspicious) — does not exist. Events go straight from bus to relevance engine without interpretation. Privacy enforcement for proactive emission has the enum but no enforcement consumer.

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| `EnvironmentalEventBus` | ✅ Built | — | |
| Location producer | ✅ Built | — | |
| Weather producer (Google API) | ✅ Built | — | Phase 7 |
| Calendar producer | ✅ Built | — | |
| SMS producer | ✅ Built | — | |
| Gmail producer | ✅ Built | — | |
| Morning briefing producer | ✅ Built | — | |
| `CurrentUserState` / Agent 12 | ✅ Built | — | Phase 6 Track A; unified |
| `CurrentContextCache` / Agent 1 | ✅ Built | — | Phase 6 Track C |
| `ContextCacheWriter` | ✅ Built | — | |
| `ProactiveTriggerCandidate` / Agent 5 | ✅ Built | — | Phase 6 Track H |
| Traffic cache entry | 🔒 Deferred | T2 | P6-C07; blocked until calendar producer emits destination field |
| `PrivacySensitivity` enum | ✅ Built | — | Exists as enum and event metadata |
| Privacy enforcement for proactive emission | ⚠️ Partial | T2 | Enum exists; no enforcement consumer; "do not speak SMS aloud in vehicle" type rules not enforced |
| Contextual Interpretation Layer | ❌ Not Built | T2 | Master Plan §8; raw events go bus → relevance engine with no interpretation; familiar vs. unknown, expected vs. unexpected not modeled |
| Camera / motion / smart home sensor inputs | ❌ Not Built | T3 | Long-horizon; not scheduled |
| Doorbell / vehicle / wearable sensor inputs | ❌ Not Built | T3 | Long-horizon; not scheduled |

---

## Domain 6 — Autonomous Behavior

### What Is Working Well
The cognitive engagement engines (curiosity, pattern investigation, world model building) and the engagement governor are all in place from Phase 5. Proactive trigger pipeline is functional.

### Key Gaps
Proactive delivery routes through `ResponseExecutionService.executeAssistantInitiatedTurn` after Agent 6 notification priority gate (P9-T8/T9). Remaining gap: engine-built `ProactiveTriggerCandidate` not yet threaded into `deliver()`; separate RES instance from user-turn `QueryProcessor` path. Autonomous turn coordination with Streaming Cognition remains future work.

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| `ProactiveAutonomousEngine` | ✅ Built | — | |
| `CuriosityInquiryEngine` | ✅ Built | — | Phase 5 |
| `PatternInvestigationEngine` | ✅ Built | — | Phase 5 |
| `WorldModelBuildingEngine` | ✅ Built | — | Phase 5 |
| `EngagementGovernor` | ✅ Built | — | Phase 5 |
| Agent 6 — Notification Priority | ✅ Built | — | P9-T8; `NotificationPriorityAgent` gate in `ProactiveDeliveryCoordinator.deliver()` |
| `HeatEvent.ProactiveSpeechOccurred` emission | ✅ Built | — | P9-T9; `ResponseExecutionService.executeAssistantInitiatedTurn` |
| Centralized assistant-initiated turn path | ✅ Built | — | P9-T9; coordinator → RES parallel entry (not `QueryProcessor`) |
| Autonomous turn coordination with Streaming Cognition | ❌ Not Built | T3 | Stage 7 in streaming roadmap; autonomous actions must not interrupt active user turns |

---

## Domain 7 — Identity and Personality

### What Is Working Well
The Phase 7 identity rewrite delivered a clean, consistent identity surface: shared seed, standard query appendix, Live appendix, Kore voice, and Zola-canonical Kotlin prompt surfaces. P9-T10 removed dead `toLoreIdentityBlock()` and Ava-era comment residue in `identity/README.md` and `PolishedResponseService.kt`. The core identity is in good shape. `PolishedResponseService`, `IdentityBoundaries`, persona mode routing, and the response orchestrator pipeline are all functional.

### Key Gaps
Style learning from interaction (Agent 7 / behavioral pattern) is not built. The `MoodTracker.updateMoodFromUserInput` method has no production callers. Persona drift detection is a light pattern pass only — no scheduled semantic consistency audit. `ResponseIdentityOrchestrator` still passes `responsePlan = null` at the `ResponseExecutionService` call site.

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| `ZolaIdentityProfile` — shared seed | ✅ Built | — | Phase 7 Track 1 rewrite |
| Standard query appendix | ✅ Built | — | Phase 7 |
| Live appendix (Kore voice) | ✅ Built | — | Phase 7 |
| `IdentityBoundaries` | ✅ Built | — | Light phrase pattern pass |
| `PolishedResponseService` | ✅ Built | — | |
| `PersonaMode` / `IdentityContext` / `ResponseIdentityOrchestrator` | ✅ Built | — | |
| `EmotionEngine` | ✅ Built | — | Keyword/punctuation heuristics |
| `MoodTracker` | ⚠️ Partial | T2 | `updateMoodFromUserInput` has no production callers; mood affects autonomous prompts only |
| `ResponseIdentityOrchestrator` `responsePlan = null` | ⚠️ Partial | T2 | Still passed null at `ResponseExecutionService:1499-1505`; threading deferred since Phase 0 |
| Style learning from interaction | ❌ Not Built | T3 | Agent 7 / behavioral pattern; `ENABLE_STYLE_PROFILE` false |
| Persona drift detection / scheduled consistency audit | ❌ Not Built | T2 | Architecture calls for this; `IdentityBoundaries` is insufficient |
| Growth rings / style profile storage | ❌ Not Built | T3 | No `StyleProfile` production writes |

---

## Domain 8 — Distributed Presence

### What Is Working Well
The Firebase account-scoped data model is the correct foundation for multi-device shared durable state. Conversation history and durable memory are accessible from any device with valid auth. The presence UI (HUD, context panels) is substantially complete pending 3D model delivery.

### Key Gaps
Distributed presence is the most architecturally incomplete domain. Multi-device support today is accidental — it works because Firebase is account-scoped, not because there is any coordination, handoff, or endpoint awareness. Building this properly requires a foundational design pass that precedes any non-phone endpoint work.

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| Firestore durable memory (account-scoped) | ✅ Built | — | Correct foundation for multi-device |
| RTDB conversation history | ✅ Built | — | Readable from any device with auth |
| Presence UI — HUD, context panels | ⚠️ Partial | T3 | Phase 5 Track F; Sessions 1-4 complete; 3D model pending model delivery |
| Device registration model | ❌ Not Built | T3 | Critical prerequisite; nothing else in this domain can be built without it |
| Active endpoint tracking | ❌ Not Built | T3 | No `primary_device` or `active_endpoint` concept exists |
| Conversational state serialization for handoff | ❌ Not Built | T3 | Depends on device registration and Domain 3 frame serialization |
| FCM cross-device coordination | ❌ Not Built | T3 | No push mechanism between devices |
| `GeminiLiveSession` multi-device semantics | 📐 Design Only | T3 | Singleton per process is correct for single-device; multi-device requires above-session coordination layer |
| Firestore conflict resolution | ❌ Not Built | T3 | Last-writer-wins; concurrent device writes risk silent data loss |
| Backend service / API surface | 📐 Design Only | T3 | Required for non-Android endpoints; scope definition needed |
| PC / shop display / glasses endpoints | 📐 Design Only | T3 | Long-horizon; backend prerequisite |
| Wearable integration | 📐 Design Only | T3 | Health Connect aggregates only; no direct transport |
| Directory rename `com/example/avapersonalassistant` | 🔒 Deferred | T3 | High blast radius, zero functional impact, breaks git blame |

---

## Agent Fleet Summary

| Agent | Name | Status | Tier | Blocker (if any) |
|-------|------|--------|------|-----------------|
| 12 | World State Snapshot | ✅ Built | — | Phase 6 Track A |
| 1 | Context Cache | ✅ Built | — | Phase 6 Track C |
| 2 | Memory Consolidation | ⚠️ Partial | T2 | Step 3 (episodic), LLM session summary |
| 4 | Memory Warm-Start | ✅ Built | — | Phase 6 Track F |
| 5 | Proactive Trigger Monitor | ✅ Built | — | Phase 6 Track H |
| 6 | Notification Priority | 🔒 Deferred | T1 | P8-FLAG-7; Agent 9 (prerequisite) now built |
| 7 | Behavioral Pattern | ❌ Not Built | T3 | No engagement trace/outcome loop; `ENABLE_STYLE_PROFILE` false |
| 8 | Tool Warm-Start | ✅ Built | — | Phase 6 Track D |
| 9 | Active Entity Resolver | ✅ Built | — | Phase 6 Track G |
| 3 | Attention Context | ❌ Not Built | T2 | BLOCKED — `ConversationalAttentionAuthority` must exist first |
| 11 | Speculative Intent | ⚠️ Partial | T1 | `ProvisionalCognitionArtifact` exists; no candidates generated yet; lives inside Streaming Stage 2 |
| 14 | Compute Priority Scheduler | ⚠️ Partial | T1 | Informal patterns only; increasingly critical as agent fleet runs concurrently |

---

## Domain 9 — Perceptual Input Layer

### What the Architecture Defines
The `Zola_Architecture_Perceptual_Input_Layer.md` document defines a two-tier model that is the foundational infrastructure for background awareness and intelligent self-activation:

**Tier 1 — Watchdog:** Always running at minimal power. VAD only — detects that speech is present, no transcription. Camera at low resolution (2-4fps) only when phone is upright, face-down phone suspends camera but audio VAD continues. Emits internal trigger signals to Tier 2 only — never directly to the bus. Zero network calls.

**Tier 2 — Active Perception:** Triggered by Watchdog or session start. Full audio/vision analysis. Emits typed observations to the Environmental Event Bus. Steps back to Watchdog when context resolves.

**Three foregrounding levels:** Level 1 (ambient overlay, subtle), Level 2 (soft heads-up notification, dismissible), Level 3 (hard foreground, safety/urgent only). Governed by confidence thresholds — Level 2 requires ≥ 0.80, Level 3 requires ≥ 0.90 with identity confirmed.

### What Exists Today (Phase 18 — 2026-06-09)

Phase 18 delivered audio-only background awareness and gate-pass foregrounding. `ListeningService` hosts a Silero VAD duty-cycle Watchdog (T1) and CampPlus Gatekeeper (T2). On identity match above threshold, `PerceptionEventBus` emits a gate-pass signal and `GatePassOverlayManager` draws an amber overlay chip. Tapping the chip foregrounds `MainActivity` for normal conversation. Voice enrollment, encrypted embedding storage, and settings-panel arming are live (T3). Camera Watchdog, Active Perception tier, and fully ambient background conversation are not built.

### Open Architecture Questions (post Phase 18)

- Fully ambient background conversation without overlay tap — see OQ-P18-OVERLAY-TAP-REQUIRED
- Overlay auto-dismiss and cooldown formal verification — see OQ-P18-OVERLAY-AUTODISMISS-UNVERIFIED
- Level 3 safety event taxonomy — what specifically constitutes a hard-foreground safety trigger
- Camera Watchdog tier — deferred; audio path delivered first

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| Watchdog (Silero VAD) | ✅ Built | — | Phase 18 T1 — duty-cycle loop, ONNX Runtime, onPause mic handoff |
| Gatekeeper (CampPlus speaker verification) | ✅ Built | — | Phase 18 T2 — sherpa-onnx CampPlus, cosine threshold 0.60 |
| Enrollment flow | ✅ Built | — | Phase 18 T3 — `VoiceEnrollmentScreen`, 3× phrase concat |
| Embedding store (`VoiceEmbeddingStore`) | ✅ Built | — | Phase 18 T3 — encrypted on-device store |
| Gate pass signal (`PerceptionEventBus`) | ✅ Built | — | Phase 18 T3 — `recognizedIdentityFlow`, replay=0 |
| Auto-foreground overlay | ✅ Built | — | Phase 18 T4 — `GatePassOverlayManager`, `SYSTEM_ALERT_WINDOW`, 8s dismiss / 15s cooldown |
| Background conversation mode | ❌ Not Built | T2 | Future phase — speak and respond without foregrounding; see OQ-P18-OVERLAY-TAP-REQUIRED |
| `ListeningService` background service shell | ✅ Built | — | FGS with mic type; hosts Watchdog + Gatekeeper + overlay |
| Watchdog tier — camera presence (upright-only) | ❌ Not Built | T2 | Architecture designed; privacy policy defined; no implementation |
| Watchdog trigger taxonomy | ⚠️ Partial | T2 | `VOICE_ACTIVITY` path live; face/phone triggers not implemented |
| Watchdog → Active Perception handoff | ❌ Not Built | T2 | Gate pass → overlay; no Active Perception stub per P18-D11 |
| Active Perception tier | ❌ Not Built | T2 | Full audio/vision analysis on Watchdog handoff; not started |
| Three-level foregrounding model | ⚠️ Partial | T2 | Level 1 overlay chip live; Levels 2–3 not implemented |
| Environmental Event Bus integration for perception events | ❌ Not Built | T2 | Perception observations → bus events → engine |
| Identity enrollment (voice) | ✅ Built | — | Phase 18 T3 — voice enrollment; face enrollment not built |
| Expression and emotional state reading | ❌ Not Built | T3 | Phase 4+ of perception roadmap |
| Complex scene understanding (Gemini Vision) | ❌ Not Built | T3 | Phase 5; consent required; disabled by default |

---

## Infrastructure and Cross-Cutting

| Component | Status | Tier | Notes |
|-----------|--------|------|-------|
| `ZolaContinuity` log tag | ✅ Built | — | Phase 8; fires on shift/return events |
| `ZolaStream` log tag | ✅ Built | — | Phase 8; fires on partial transcripts |
| Live runtime validation of log tags | ⚠️ Partial | T1 | Cannot be verified in Cursor; requires device session |
| Architecture enforcement tests | ✅ Built | — | QueryProcessor boundary tests, streaming isolation tests |
| `ZolaFeatureFlags` | ✅ Built | — | Feature gate infrastructure |
| `ENABLE_CONSOLIDATION_PROMOTION` | ✅ Built | — | Promotion gated; on |
| `ENABLE_MEMORY_PIPELINE` | ✅ Built | — | On |
| `ENABLE_STYLE_PROFILE` | ⚠️ Partial | T3 | Flag exists; false; no production callers |
| Six pre-existing test failures | ⚠️ Partial | T2 | `GmailMonitorTest` / `SmsContentProviderPollerTest` quiet-hours mock override gap; pre-Phase 5 baseline |

---

## Prioritized Roadmap

### Tier 1 — Phase 9 (COMPLETE — 2026-05-27)
Phase 9 tracks 1–10 merged on `zola-main`. Items below are historical scope; completed work is reflected in domain tables above.

**Continuity boundary cleanup:**
- `FollowUpService` direct reference cleanup in `QueryProcessor` (Phase 9; blocked by `ResponseExecutionService` — needs design)
- `TopicShiftDetector` direct reference cleanup in `QueryProcessor`
- Orchestration context integration with focus stack (P8-FLAG-3)

**First user-visible continuity behavior:**
- Bridge phrase generation on topic return (uses Phase 8 return pointer metadata)

**Streaming unlock:**
- Proper utterance ID contract (prerequisite for Stage 2)
- Engine-neutral streaming observer interface (P8-FLAG-4)
- Streaming Stage 2 — provisional candidate generation

**Attention tuning:**
- Always-on name detection reliability / calibration (practical tuning, not new architecture)
- `HeatEvent.ProactiveSpeechOccurred` emission fix (one-line fix once turn path is centralized)

**Deferred agent:**
- Agent 6 — Notification Priority (P8-FLAG-7)

**Routing:**
- News intent / grounding routing gap (OQ-T3A-1)

**Optional cleanup:**
- Track 6 — dead code, `toLoreIdentityBlock()`, identity string cleanup
- Live citation metadata aggregation path
- Live `ZolaContinuity` and `ZolaStream` runtime log validation

---

### Tier 2 — Phase 10
High value, requires design work or prerequisite from Phase 9.

**Background activation (new in Phase 10):**
- Watchdog tier — VAD library selection and implementation (prerequisite: resolve open architecture questions first)
- Watchdog → Active Perception handoff
- Name detection → auto-foreground trigger (the core of "Zola hears her name and comes to the foreground")
- Level 1 and Level 2 foregrounding implementation
- `ListeningService` refactored to host the Watchdog tier properly


- Streaming Stage 4 — interruption/barge-in (requires Live transport cancellation API)
- Streaming Stage 5 — topic stack integration

**Attention architecture:**
- `ConversationalAttentionAuthority` — inbound directed speech authority design and build
- `DirectedSpeechScorer`
- Agent 3 — Attention Context (unblocked once `ConversationalAttentionAuthority` exists)
- `AttentionContextHints`

**Compute governance:**
- `ComputePriorityScheduler` (Agent 14) — formal implementation; critical before more agents run concurrently

**Memory:**
- `ConsolidationLoop` Step 3 — episodic promotion
- `ConsolidationLoop` Step 6 — LLM-enriched session summary
- Memory drift / persona consistency scheduled audit

**Autonomy:**
- Privacy enforcement consumer for proactive emission
- Thread engine-built `ProactiveTriggerCandidate` through `ProactiveDeliveryCoordinator.deliver()`

**Environmental:**
- Contextual Interpretation Layer (raw events → meaningful situational understanding)
- `maxPerHour` rate limit enforcement in `MonitorManifest`
- Traffic cache entry (P6-C07; unblocked when calendar emits destination)

**Identity:**
- `ResponseIdentityOrchestrator` — wire `responsePlan` properly
- `MoodTracker` — production caller wiring
- Persona drift detection / scheduled consistency audit

**Focus stack:**
- Durable focus stack persistence (Firestore serialization)

---

### Tier 3 — Phase 11+
Major new systems requiring dedicated design phases. Do not build without a design pass first.

**Distributed presence (full design pass required before any build):**
- Device registration model
- Active endpoint tracking
- Conversational state serialization and handoff protocol
- FCM cross-device coordination
- Firestore conflict resolution
- Backend service / API surface definition
- Non-phone endpoints (PC, shop display, glasses)

**Streaming late stages:**
- Streaming Stage 6 — cognitive draft buffer
- Autonomous behavior coordination with Streaming Cognition (Stage 7)

**Long-horizon agent work:**
- Agent 7 — Behavioral Pattern / style learning
- Style profile storage and production callers
- Growth rings / tone evolution from interaction history

**Environmental long-horizon:**
- Camera / motion / smart home / wearable inputs
- Contextual Interpretation Layer (full depth beyond Phase 10 MVP)

**Presence UI:**
- 3D model swap (pending model delivery)
- Presence UI Wave 3-5 (procedural life, eyes, mouth)
- Context panels deep wiring

**Housekeeping:**
- Directory rename `com/example/avapersonalassistant` → `com/beebo/zolaassistant` (high blast radius, zero functional impact)

---

## Phase 9 Status — COMPLETE (2026-05-27)

Phase 9 delivered continuity boundary cleanup, bridge phrases, news/grounding routing, orchestration↔focus bridge, streaming observer contract (Track 6), Agent 6 notification gate, proactive delivery unification through `ResponseExecutionService`, and Track 10 dead-code/comment cleanup (`toLoreIdentityBlock()` removed).

Pre-build audit contradictions (P9-D06) are corrected in domain tables: proactive turns use `TurnResponseGuard`, emit `ProactiveSpeechOccurred`, and persist RTDB history via the assistant-initiated RES path (P9-T9).

Phase 10 owns distributed presence, `ConversationalAttentionAuthority`, streaming hint promotion, and background activation — not Phase 9 scope.

---

## Phase 10 Status — COMPLETE (2026-05-29)

<!-- [P10-CLOSEOUT]: Daily Brief pipeline shipped — all ten P10 tracks merged; zola-main tip 5d26ce6 -->

Phase 10 delivered the **Daily Brief** — once-per-day spoken morning summary assembled from warm tool context, consent-gated email heuristics, cross-domain name matching, and memory signals; delivered via `ResponseExecutionService.executeAssistantInitiatedTurn` with `ResponseOwnership.ASSISTANT_INITIATED`. Device-verified on hardware after Track 9 merge; Track 10 opt-in, voice commands, and settings panel entry merged at `8a665dd`; lore closeout tip `5d26ce6`.

### Components built (current state)

| Component | Status | Notes |
|-----------|--------|-------|
| `DailyBriefSettings` + `BriefSettingsWriter` | ✅ Built | Firestore `users/{userId}/brief/settings`; Hilt-free `bind()` / `requireInstance()`; sole write authority |
| `BriefContextStore` + `BriefPackage` + signal models | ✅ Built | In-memory only; 4-hour expiry; no Firestore persistence for brief content |
| `EmailIntelligenceAnalyzer` | ✅ Built | Consent-gated; heuristics only (no model pass in Phase 10); reads `WarmToolContext.recentMessagesSummary`; no body content |
| `CrossDomainCorrelator` | ✅ Built | Calendar-to-email and calendar-to-memory **name matching only**; attendee matching deferred (HIGH-01 / OQ-BRIEF-4 warm-data limit) |
| `BriefPromptBuilder` | ✅ Built | Constraint block always present; email section omitted without consent; no prompt content logged |
| `DailyBriefAssembler` | ✅ Built | Per-source 5s timeout; adaptive length scoring (SHORT / MEDIUM / FULL); returns null on total failure |
| `BriefDeliveryCoordinator` | ✅ Built | Full gate sequence (fresh package, enabled, window, idle, Agent 6, expiry); delivers via `executeAssistantInitiatedTurn`; committed-script path for pre-built brief (HOTFIX-3d) |
| `DailyBriefAgent` (Agent 15) | ✅ Built | Background assembly + on-demand paths; no memory writes; no direct Live calls; reads via Agent 8 warm context only |
| Phase 9 surgical upgrades (T9) | ✅ Built | `MorningBriefingEmitter` assembly trigger; `ProactiveAutonomousEngine` idle delivery hook; `QueryRoutingService` / `FinalRouteDispatcher` on-demand brief routing |
| `BriefOptInCoordinator` | ✅ Built | Generative opt-in path only (`committedScriptDelivery = false`); wired in `GeminiLiveSession.obtain()` + `MainActivity`; writes via `BriefSettingsWriter` only |
| Voice commands (T10) | ✅ Built | Four pattern groups in `QueryRoutingService` (classified before on-demand routing); handlers in `DailyBriefAgent` |
| Settings panel — DAILY BRIEF section | ⚠️ Partial | Built in `ContextPanelLayer.kt`; wired to `BriefSettingsWriter`; **not yet device-testable** — 3D presence navigation gate (approved deferral) |

### Known gaps carried forward to Phase 11

<!-- [P10-CLOSEOUT]: Open items recorded in OPEN_QUESTIONS.md — not Phase 10 regressions -->

- **OQ-BRIEF-1 through OQ-BRIEF-6** — see `OPEN_QUESTIONS.md` (sensitive calendar filtering, multi-device delivery, brief feedback signals, `MessagesSummary` extension, opt-in unit tests, Agent6 / on-demand cooldown conflict)
- **Four pre-existing unit test failures** on `zola-main` baseline at `156bfb7` — not introduced by Phase 10 (`GeminiLiveClientWaveE6Test`, `LiveResponseWatchdogTest`, `ProactiveAutonomousEngineAttentionTest`, `ProactiveTriggerCandidateArchTest`)
- **Settings panel device test** deferred until 3D presence layer activates navigation to settings

### Phase 10 scope not delivered (deferred by design)

<!-- [P10-CLOSEOUT]: P10-D12 boundary — see DESIGN_DECISIONS.md Phase 10 section -->

Email body model analysis, full semantic cross-domain correlation, `ContactRelationshipIndex`, Drive integration, SMS intelligence, brief feedback into behavioral learning, visual brief card — all Phase 11 or later per P10-D11 / P10-D12.

*Note: The pre-closeout stub below listed conversational attention, streaming, and Agent 3 as Phase 10 goals; actual Phase 10 scope was the Daily Brief pipeline per `Zola_Phase10_Build_Plan.md`. Those items remain Tier 2 / Phase 11+ backlog in domain tables above.*

---

## Phase 11 Status — COMPLETE (2026-06-01)

<!-- [P11-CLOSEOUT]: Email intelligence pipeline + brief feedback shipped — all five P11 tracks merged; zola-main tip 87764f6 -->

Phase 11 deepened the Daily Brief email intelligence pipeline from heuristics-only to per-message `MessageEntry` analysis with an optional Stage 4 Gemini model pass, added post-delivery brief feedback into style learning, and closed Phase 10 carry-forward housekeeping (OQ-BRIEF-1/5/6, opt-in tests, four pre-existing Live/proactive test failures). Email pipeline device-verified per developer; test suite clean at exit (2124 completed, 0 failed, 9 skipped).

### Tracks merged to `zola-main`

| Track | Name | Merge SHA |
|-------|------|-----------|
| T1 | MessagesSummary contract extension | `93b729e` |
| T2 | EmailIntelligenceAnalyzer rewrite | `ec89ae9` |
| T3 | Stage 4 model pass + consent gate | `4ea28ba` |
| T4 | Brief feedback signal | `bffd5bd` |
| T5 | Housekeeping | `c7c982e` |

### Components built or upgraded (current state)

| Component | Status | Notes |
|-----------|--------|-------|
| `MessageEntry` + `MessagesSummary.messages` (T1) | ✅ Built | Per-message contract; tiered snippet consent at `ToolWarmStartAgent` map time; `GmailFromHeaderParser` shared utility (P11-D01–D03) |
| `EmailIntelligenceAnalyzer` rewrite (T2) | ✅ Built | Operates on `List<MessageEntry>`; address/name/subject noise filtering; relationship weight scoring (P11-D04); replaces Phase 10 heuristics-only path |
| Stage 4 model pass (T3) | ✅ Built | Gemini `gemini-flash` for UNCERTAIN rows only; snippet-only input (200-char cap); failure falls back to Stage 3 / excludes from brief (P11-D05–D06); consent gate at fetch |
| `BriefFeedbackSignal` + classifier (T4) | ✅ Built | Heuristic ACKNOWLEDGED / ASKED_FOR_MORE / INTERRUPTED / NO_RESPONSE; one-shot post-delivery observation window (P11-D07–D08) |
| `BriefFeedbackStyleMapper` → `StyleProfileLearner` (T4) | ✅ Built | First production brief-feedback write path; full Agent 7 behavioral pattern still not built |
| Sensitive calendar title filter (T5) | ✅ Built | `DailyBriefAssembler` filters sensitive titles before brief assembly (OQ-BRIEF-1) |
| `BriefOptInCoordinator` unit tests (T5) | ✅ Built | Three tests; OQ-BRIEF-5 closed |
| Agent 15 entry in `Zola_Agent_Map.md` (T5) | ✅ Built | Lore alignment |
| Four pre-existing Live/proactive test failures (T5) | ✅ Built | Option A signature-drift fixes after HOTFIX-3d (`GeminiLiveClientWaveE6Test`, `LiveResponseWatchdogTest`, `ProactiveAutonomousEngineAttentionTest`, `ProactiveTriggerCandidateArchTest`) |

### Hotfixes merged during Phase 11

| ID | Description |
|----|-------------|
| HOTFIX-CONV-ACTIVE | `ConversationStateMonitor.computeRawConversationActive()` no longer treats always-on `isListeningActive()` as conversation-active — unblocks Tier 4–6 background workers |
| HOTFIX-CONSENT-PREFETCH | Initial settings gate before email warm prefetch |
| HOTFIX-CONSENT-PREFETCH-FIX | Sequential settings load fix for consent-gated prefetch |
| HOTFIX-OQ-BRIEF-6 | On-demand Agent 15 brief delivery bypasses Agent 6 cooldown |

### Known gaps carried forward to Phase 12

<!-- [P11-CLOSEOUT]: Open items recorded in OPEN_QUESTIONS.md and ROADMAP Phase 12 — not Phase 11 regressions -->

- **OQ-BRIEF-2** — multi-device brief delivery policy (distributed presence dependency)
- **OQ-BRIEF-7** — relationship weight scorer name normalization (display name vs canonical name)
- **OQ-COMM-1** — Stage 4 snippet length tuning (200-char conservative cap)
- **OQ-COMM-2** — Stage 4 daily Gemini rate cap (per-brief cap of 3 only today)
- **`CrossDomainCorrelator` sensitive calendar titles** — filter in `DailyBriefAssembler` only; correlator may still read warm snapshot titles (Phase 12 hardening)
- **`CrossDomainCorrelator` full semantic correlation** — name matching only; `ContactRelationshipIndex` Phase 12
- **`MessagesSummary` legacy aggregated fields** — retained for backwards compatibility; removal Phase 12 (P11-D11)
- **Settings panel device test** — deferred until 3D presence navigation active (from Phase 10)

### Phase 11 scope not delivered (deferred by design)

<!-- [P11-CLOSEOUT]: From build plan "Phase 11 Does Not Include" -->

SMS intelligence (`SmsIntelligenceAnalyzer`), full email body / thread fetch analysis, `ContactRelationshipIndex` full build, multi-device brief delivery validation, Stage 4 snippet/daily rate tuning, Drive integration, visual brief card — Phase 12+ per P11-D05, P11-D09, P11-D11 and `OPEN_QUESTIONS.md`.

*Note: The section below ("What Phase 11+ Should Accomplish") listed distributed presence and full style learning as Phase 11 goals; actual Phase 11 scope was email intelligence and brief feedback per `Zola_Phase11_Build_Plan.md`. Distributed presence, SMS intelligence, and full Agent 7 remain Phase 12+ backlog in domain tables above.*

---

## Phase 12 Status — COMPLETE (2026-06-02)

<!-- [P12-CLOSEOUT]: SMS intelligence pipeline shipped — all six P12 tracks merged; Master State Audit Phase 12 section complete -->

Phase 12 delivered the SMS intelligence pipeline — consent model, warm SMS fetch, five-stage heuristic analysis, brief integration with action offers, voice commands and settings UI wiring, and T6 housekeeping (B1 bypass fix, `MessagesSummary` legacy field removal, lore/OQ closeout). `:app:testDebugUnitTest` PASS at T6 closeout; aggregate completed/failed/skipped counts were not logged in T6 progress (Phase 11 exit baseline: 2124 completed, 0 failed, 9 skipped).

**Status:** COMPLETE

**Merge SHAs:**
- T1 Settings schema: `9de36e4`
- T2 SmsWarmDataProvider: `5a73c91`
- T3 SmsIntelligenceAnalyzer: `25f0c95`
- T4 Brief integration + action offer: `cfef53b`
- T5 Voice commands + settings UI: `450ece8`
- T6 Housekeeping: `132f272`
- Phase 12 lore closeout tip: `7ed9775`

### Tracks merged to `zola-main`

| Track | Name | Merge SHA |
|-------|------|-----------|
| T1 | Settings schema + SMS consent | `9de36e4` |
| T2 | SMS warm data provider | `5a73c91` |
| T3 | SmsIntelligenceAnalyzer | `25f0c95` |
| T4 | Brief integration + action offer | `cfef53b` |
| T5 | Voice commands + settings UI | `450ece8` |
| T6 | Housekeeping | `132f272` |

### Components built

| Component | Status | Notes |
|-----------|--------|-------|
| `DailyBriefSettings.smsAnalysisConsent` | ✅ Built | Separate from email consent; default false; Firestore-backed via `BriefSettingsWriter` |
| `Sources.SMS` | ✅ Built | Excluded from `defaultIncludedSources()` — opt-in only |
| `SmsMessageEntry` / `SmsThreadEntry` / `SmsWarmContext` | ✅ Built | Warm data contracts; sensitive TTL |
| `SmsWarmDataProvider` | ✅ Built | Contact-gated; Samsung DATE + column guards; velocity-scored; 20 thread / 5 message caps |
| `WarmToolContext.recentSmsSummary` | ✅ Built | `isSensitive = true`; 2-min TTL; wiped by `purgeExpiredSensitiveEntries()` |
| `PrefetchTarget.RECENT_SMS` | ✅ Built | Consent + settingsReady gate; immediate prefetch on consent enable |
| `ThreadVelocity` / `SmsIntent` / `SmsSignal` | ✅ Built | Output contract frozen; no raw body in signal |
| `SmsIntelligenceAnalyzer` | ✅ Built | Five-stage heuristic pipeline; consent gate; body boundary enforced |
| `BriefPackage.smsSignals` | ✅ Built | Default `emptyList()`; included in density scoring |
| `BriefPromptBuilder` SMS section | ✅ Built | Consent-gated; `requiresResponse` ordering; action offers; `lastMessagePreview` released after build |
| `DailyBriefAssembler` SMS wiring | ✅ Built | Gate + assembly + `[P12-T4]` log |
| `BriefDeliveryCoordinator` SMS consent | ✅ Built | `smsAnalysisConsented` passed to `build()` |
| SMS voice commands | ✅ Built | `SET_SMS_CONSENT_TRUE/FALSE`; B1 bypass exclusion fixed in T6 |
| `BriefOptInCoordinator` SMS follow-up | ✅ Built | Fires after email consent; same delivery path |
| Settings UI SMS toggle | ⚠️ Partial | Built in `ContextPanelLayer`; not yet device-testable — 3D presence gate (approved deferral) |
| `MessagesSummary` legacy fields | ✅ Removed | `senderNames`, `mostRecentSubject`, `unreadCount` removed; consumers migrated |
| `Zola_Communication_Intelligence_Architecture.md` | ✅ Complete | v1.0 as-built — email + SMS intelligence documented |

### Known carry-forward to Phase 13

<!-- [P12-CLOSEOUT]: Open items recorded in OPEN_QUESTIONS.md and ROADMAP Phase 13 — not Phase 12 regressions -->

- **`sanitizeSensitiveSummaryText` / `MAX_SENDER_NAMES` dead code** in `ToolWarmStartAgent` — harmless, cleanup candidate
- **`fromMap()` / `toMap()` missing `smsAnalysisConsent`** — Firestore round-trip stays false until fixed
- **`onSmsConsentGranted` callback not wired** in `MainActivity`
- **OQ-BRIEF-2, OQ-BRIEF-7, OQ-SMS-1 through OQ-SMS-4, OQ-COMM-1, OQ-COMM-2, OQ-COMM-4** — all formally deferred (see `OPEN_QUESTIONS.md`)
- **`ProactiveAuthorityGate` stub** — long-standing deferred item
- **Settings panel device test** — pending 3D presence gate
- **`QueryProcessor` decomposition** — evaluate for Phase 13 after Gemini audit

**Test suite at Phase 12 exit:** `:app:testDebugUnitTest` PASS (T6 closeout); aggregate counts not logged in T6 progress — Phase 11 exit baseline 2124 completed, 0 failed, 9 skipped.

### Phase 12 scope not delivered (deferred by design)

<!-- [P12-CLOSEOUT]: From build plan "Phase 12 Does Not Include" and ROADMAP Phase 13 carry-forward -->

Gemini model pass for SMS (OQ-SMS-1), RCS intelligence (OQ-SMS-2), multi-device brief delivery (OQ-BRIEF-2), memory-aware email relationship weights (OQ-BRIEF-7), full email body analysis (OQ-COMM-4), multi-message SMS thread summarization (OQ-SMS-4), `ContactRelationshipIndex` full build, full semantic cross-domain correlation, Drive integration, visual brief card — Phase 13+ per `Zola_Phase12_Build_Plan.md` and `OPEN_QUESTIONS.md`.

*Note: Agent 8 (Tool Warm-Start) was extended for SMS prefetch; no new agent was added. Agent 15 brief pipeline was extended for SMS signals and consent voice paths.*

---

## Phase 14 Status — COMPLETE

<!-- [P14-CLOSEOUT]: QueryProcessor wiring tracks shipped — decomposition wired on zola-main -->

**Status:** COMPLETE

**Merge SHA:** `3f647e7`

### What changed

| Component | Change | Status |
|-----------|--------|--------|
| `TurnContinuityState` | Wired into `QueryProcessor` — prior-turn fields replaced | ACTIVE |
| `QueryContextFactory` | Wired into `QueryProcessor` — three inline build methods delegated | ACTIVE |
| `ConversationalModeAuthority` | Wired into `QueryProcessor` — B1 gate replaced, Path A implemented | ACTIVE |
| `QueryProcessor` | Decomposition complete — thin orchestrator; inline policy removed | THINNED |
| Phase 13 delegate methods | Removed — direct calls to `ContextCacheResponses` and `WarmToolContextResponses` | REMOVED |

### Known gaps carried to Phase 15

- ~~`runBlocking` in `QueryContextFactory.buildFull` — suspend cascade not safe to eliminate in Phase 14 (OQ-P13-2)~~ **Resolved P15-T4**
- ~~Hybrid-path helpers in `QueryProcessor` — `getOrLoadHistory`, `buildRecallInput`, `applyRecallHedgeKeysToQueryContext`~~ **Complete P15-T5**
- ~~Path B (`DailyBriefBypassAuthority`) — documented P14-D08~~ **Complete P15-T6**
- ~~Memory write bugs — `AvaExec_HCorrection` parse (OQ-P14-1), `LiveWritePlanner` birthday enrichment (OQ-P14-2)~~ **Resolved P15-T1**

**Test suite at Phase 14 exit:** 2153+ completed, 6 failed (pre-existing `GmailMonitorTest` / `SmsContentProviderPollerTest` baseline — not introduced by Phase 14).

---

## Phase 15 Status — COMPLETE

<!-- [P15-CLOSEOUT]: QueryProcessor follow-on tracks shipped — B1 decomposition complete on zola-main -->

**Status:** COMPLETE

**Merge SHA:** `b4900f0`

### What changed

| Component | Change | Status |
|-----------|--------|--------|
| `LiveMemoryCorrectionToolExecutor` | Conversational phrasing strip for numeric corrections (OQ-P14-1) | ACTIVE |
| `LiveStructuredMemoryWritePlanner` | Birthday year enrichment guard (OQ-P14-2) | ACTIVE |
| `SessionMemoryCoordinator` | Turn-count buffer, consolidation trigger (T2/T2B) | ACTIVE |
| `SessionSummaryRetriever` | Cross-session episodic recall (T3) | ACTIVE |
| `QueryContextFactory` | `buildFull` suspend; hybrid-path helpers authoritative (T4/T5) | ACTIVE |
| `DailyBriefBypassAuthority` | B1 bypass extracted from `QueryProcessor` (T6 / Path B) | ACTIVE |
| `QueryProcessor` | B1 region: bypass authority + mode authority; hybrid redirects only | THINNED |

### Carry-forward (post-Phase 15)

- Episodic recall vs Live routing — OQ-P15-LIVE-RECALL-ROUTING
- Phase 12–13 carry-forward still open: OQ-BRIEF-2, OQ-BRIEF-7, OQ-COMM-1, OQ-COMM-2, OQ-SMS-1 through OQ-SMS-4, OQ-P13-1
- Device smoke for T1/T4/T5/T6 correction, recall, hybrid, and daily-brief bypass — not run in agent closeout environment

**Test suite at Phase 15 exit:** `:app:testDebugUnitTest` PASS at T6 closeout; aggregate counts match T5 baseline (2159 completed, 9 skipped).

---

## Phase 30 Status — COMPLETE (Relational Intelligence Layer)

<!-- [P30-CLOSEOUT]: RIL five subsystems + Phase A pre-work shipped on zola-main -->

**Status:** COMPLETE

**Merge tip SHA:** `9aa8bb7` (`474bb9b` feature merge + closeout doc commits)

### What shipped

| Subsystem | Track | Key components |
|-----------|-------|----------------|
| Pre-work A | A1–A8, HOTFIX-CR | Chunk schema, CONTRADICTED persistence, Live correction dispatch, tombstoning, retrieval filters, EntityBeliefView, SessionSummary affective fields, IdentityContext + CalibrationSignal shell |
| Infrastructure B | B1–B3 | SessionBoundaryResolver, session-mention Firestore paths, DistinctSessionMentionTracker |
| Temporal Reasoning | C1 | ThreadArcClassifier, TemporalContextAssembler, TemporalInitiativeSource, `[TEMPORAL]` brief |
| Self-Model Awareness | C2 | HedgingSignalProducer, GapSignalProducer, SelfBeliefBlock, SelfModelInitiativeSource, `[BELIEF]` brief + entity beliefs injection |
| Social Graph Reasoning | C3 | ThirdPartyAssertionGuard, SocialEntityProfileBuilder, SocialContextAssembler, `[SOCIAL]` brief |
| Relational Continuity | C4 | RelationshipArc, FrictionStateEvaluator, ArcStateUpdater, Step 6b, `[CONTINUITY]` brief |
| Relational Calibration | C5 | RelationalCalibrationAdapter, CalibrationSignalHolder, identity ceiling clamps, `=== RELATIONAL CALIBRATION ===` Live block |

### New production `.kt` files (32)

**Phase A / infrastructure:**
- `identity/CalibrationSignal.kt`
- `memory/domain/ContradictedAttributeRecord.kt`
- `memory/session/SessionBoundaryResolver.kt`
- `memory/social/DistinctSessionMentionTracker.kt`
- `memory/social/SessionMentionRecord.kt`
- `memory/social/SessionMentionStore.kt`
- `memory/view/EntityBeliefView.kt`
- `memory/view/EntityBeliefViewHolder.kt`

**RIL — temporal (`ril/temporal/`):**
- `ThreadArcClassifier.kt`
- `TemporalContextBlock.kt`
- `TemporalContextAssembler.kt`
- `TemporalInitiativeSource.kt`

**RIL — self-model (`ril/selfmodel/`):**
- `GapSignalProducer.kt`
- `HedgingSignalProducer.kt`
- `SelfBeliefBlock.kt`
- `SelfModelInitiativeSource.kt`

**RIL — social (`ril/social/`):**
- `ThirdPartyAssertionGuard.kt`
- `SocialGraphNodeEvaluator.kt`
- `SocialEntityProfileBuilder.kt`
- `SocialContextAssembler.kt`
- `SocialGraphInitiativeSource.kt`

**RIL — continuity (`ril/continuity/`):**
- `RelationshipArc.kt`
- `ArcSessionDelta.kt`
- `FrictionStateEvaluator.kt`
- `RelationshipDepthModel.kt`
- `ArcStateUpdater.kt`
- `ArcContextAssembler.kt`
- `ContinuityInitiativeSource.kt`

**RIL — calibration (`ril/calibration/`):**
- `CalibrationSignalHolder.kt`
- `RelationalCalibrationAdapter.kt`

### New test `.kt` files (12)

- `memory/service/P30A2ContradictedAttributeWriteGateTest.kt`
- `memory/service/P30A4StructuredMemoryChunkTombstoneTest.kt`
- `memory/service/P30A5RetrievalLifecycleFiltersTest.kt`
- `memory/session/SessionBoundaryResolverTest.kt`
- `memory/social/DistinctSessionMentionTrackerTest.kt`
- `memory/view/EntityBeliefViewTest.kt`
- `rag/InMemorySemanticMemoryStoreTest.kt`
- `ril/temporal/TemporalReasoningTest.kt`
- `ril/selfmodel/SelfModelAwarenessTest.kt`
- `ril/social/SocialGraphReasoningTest.kt`
- `ril/continuity/RelationalContinuityTest.kt`
- `ril/calibration/RelationalCalibrationTest.kt`

*(HOTFIX-CR, A1, A3, A4, A5, A7, A8 extended existing files only — no new production `.kt`.)*

### Deferred (carried forward)

- MainActivity C1 session-start `TemporalInitiativeSource` hook (P30-C1-NOTE-01)
- Passive PROVISIONAL → ACTIVE promotion (C3 v1.1, OQ-P30-C3-PROMOTION-01)
- Per-session `correctionCount` at arc Step 6b (C4 v1.1, OQ-P30-C4-CORRECTION-01)

**Test suite at Phase 30 exit:** started at **~2350** tests (Phase A baseline, A8 closeout); ended at **2435+** completed, 0 failures, 9 skipped (C3 closeout; C4/C5 added 36 RIL unit tests incrementally). Full suite PASS at C5 closeout re-verify.

---

## What Phase 10 Should Accomplish *(superseded — see Phase 10 Status above)*

<!-- [P10-CLOSEOUT]: Retained for audit history; content reflected pre–Daily Brief pivot scoping -->

~~Phase 10 is where the system starts to feel meaningfully smarter and more natural:~~

- ~~The `ConversationalAttentionAuthority` makes always-on attention genuinely reliable at an architectural level~~
- ~~Streaming hint promotion makes responses measurably faster~~
- ~~The formal compute scheduler prevents audio contention as the agent fleet grows~~
- ~~The centralized assistant-initiated turn path closes the last major speech architecture gap~~ *(delivered in Phase 9 Track 9; used by Phase 10 brief delivery)*
- ~~Agent 3 comes online and Zola can properly determine when she is being addressed~~

---

## What Phase 11+ Should Accomplish

Phase 11 is foundational infrastructure for the long-term vision:

- Distributed presence enables the "one mind, many bodies" experience
- Style learning lets Zola's communication evolve with the user
- Environmental interpretation makes proactive behavior contextually aware rather than pattern-matched

---

## Phase 31 — Relationship Graph Hardening

**Audit tip SHA:** `93d9bfa` (post all P31 tracks + B5 closeout docs)  
**Phase base SHA:** `47ef659` (Phase 31 Build Plan commit)  
**Completed:** 2026-06-24

### Overview

Phase 31 delivered relationship graph hardening (new predicates, correction
path, resolver coverage), attribute canonicalization (single authoritative
map, P31-D10 schema), targeted hardening (guard coverage, temporal hook),
recall pipeline attribute candidate retrieval with self-entity resolution,
and graph-first relationship query handlers. Four unplanned tracks (A4,
B4, B5) were added during device verification.

### Relationship graph state after Phase 31

- **Active predicates:** `SPOUSE_OF`, `CHILD_OF`, `PARENT_OF`, `SIBLING_OF`,
  `FRIEND_OF`, `PET_OF`, `OWNER_OF`, `GRANDPARENT_OF`, `GRANDCHILD_OF`,
  `INLAW_OF` (with role qualifier), `PRIMARY_BOND`, `KNOWS_ABOUT`,
  `EMPLOYEE_OF`, `WORKS_AT`
- **Write path:** `FamilyRelationshipMapper` →
  `LiveStructuredMemoryWritePlanner` → `RelationshipWriteGovernor`; null
  mapper result is a rejection (`unmapped_relationship_term`)
- **Correction path:** `AvaExec_HCorrection` routes relationship
  corrections through `RelationshipWriteGovernor`; predicate updates
  delete old edge + `onSourceEdgeChanged(DELETED)` + write new edge
- **Reciprocal write:** IR-01 via `runIr01Reciprocal` for all predicates
  with `reciprocalType()` entries (including `GRANDPARENT_OF` →
  `GRANDCHILD_OF`)
- **Resolver coverage:** `grandparent_lookup`, `grandchild_lookup`,
  `friend_lookup`, `inlaw_lookup` added to `RelationshipResolver`; brief
  assembly and referent resolution extended for new predicates

### Attribute system state after Phase 31

- **Authoritative map:** `attributes` field on `StructuredEntityDocument`
- **Legacy map:** `structuredAttributes` no longer written on new Firestore
  saves (B3 `EntityWriteShapeGuard` 3A)
- **Schema version:** `3` on new canonical person writes
- **Canonical key schema:** P31-D10 (`snake_case`, indexed trait/interest
  slots, `custom.*` escape hatch)
- **Normalizer:** `PersonCanonicalAttributeNormalizer` at
  `proposePersonMemory` write time
- **Read paths:** `EntityBeliefViewHolder` and `LiveB1RecallToolExecutor`
  read from unified flat `attributes` map (B3 hot paths)

### Recall system state after Phase 31

- **RecallPipeline Stage 3:** first-person self-reference resolution via
  `SelfReferenceQueryMatcher` (B4)
- **RecallPipeline Stage 4:** `StructuredAttributeRecallCandidates`
  emits per-key candidates from canonical `attributes` map (B4)
- **ReadModeClassifier:** possessive self-attribute queries →
  `DIRECT_RECALL`; lowercase STT names supported (B4)
- **Relationship query handlers:** graph-first pattern on in-law,
  grandparent, and sibling-in-law paths in executor and formatter (B5);
  stale spouse/traversal miss scripts retired

### Known open gaps after Phase 31

- **Third-party relationship correction:** deferred
  (`OQ-P31-CORRECTION-ENTITY-01`)
- **In-law inference from spouse chain:** deferred
  (`OQ-P31-INLAW-INFERENCE-01`)
- **Sixteen downstream `structuredAttributes` consumers:** deferred
  (`OQ-P31-ATTR-STRUCTURED-CONSUMERS-01`)
- **RecallKernel legacy trait key lookup:** deferred
  (`OQ-P31-RECALL-TRAIT-KEY-LEGACY-01`)
- **MemoryRetrievalPipeline DirectFacts legacy keys:** deferred
  (`OQ-P31-RECALL-DIRECTFACTS-LEGACY-01`)
- **Write-path `normalizeRole` in-law collision:** deferred
  (`OQ-P31-B5-NORMALIZE-ROLE-INLAW-01`)
- **Classifier grandparent pattern gap:** deferred
  (`OQ-P31-B5-CLASSIFIER-GRANDPARENT-GAP-01`)
- **correctMemory routing enforcement:** deferred
  (`OQ-P30-A-ROUTING-01`)

### System integrity notes

- Pre-existing test failures in `GmailMonitorTest`,
  `SmsContentProviderPollerTest`, `DailyBriefAssemblerTest`,
  `WriteAuthorityEnforcementTest` are known flakes predating Phase 31 —
  not regressions introduced by P31 tracks
- Graph data was cleared and rebuilt from scratch during Phase 31
  verification; `schemaVersion: 2` documents are no longer written on new
  canonical person entities
- Phase 30 deferred **MainActivity C1 session-start initiative hook** is
  **resolved** by P31-D06 (`TemporalInitiativeSource.run()` at session
  start)

---

## Phase 32 — HUD Rework and Speech Animation (Tracks A and B)

**Audit tip SHA:** `411faf1` (post Track B merge + docs commit)  
**Phase base SHA:** `d4d3f40` (Phase 32 Build Plan commit)  
**Completed (partial):** 2026-06-24 — Tracks A and B only; C and D pending

### Overview

Phase 32 Tracks A and B delivered the HUD visual rework (left and right
panels), live HUD data wiring through `PresenceStateAdapter`, final GLB
camera framing and head tilt lock (P32-D01), and location footer display.
Tracks C (dock buttons + show/hide) and D (jaw drive speech animation)
remain pending.

### Tracks completed

| Track | Name | Merge SHA | Feature commit |
|-------|------|-----------|----------------|
| Pre | GLB asset swap + camera retune | `411faf1` | (bundled on `zola-main` tip) |
| A | HUD left panel rework | `d5b04bf` | `c5d67a0` |
| B | HUD right panel + live data wiring | `411faf1` | `9c6a0d1`, `686b2a1` |

### Key files created

- `ui/presence/layers/CoreSystemsIcons.kt` — seven geometric Core Systems
  icons + Africa outline path (Track A)

### Key files modified

- `ui/presence/layers/HudLayer.kt` — left panel rework (Track A); right
  panel ATTENTION + TIME only (Track B C3); `LeftPanelFooter` with live
  location (Track B C4/C5/C6)
- `ui/presence/HudShellLayer.kt` — corner L-brackets restored (Track A)
- `ui/presence/state/HudState.kt` — five new fields (Track B)
- `ui/presence/PresenceStateAdapter.kt` — `MoodTracker`, `appContext`,
  location coroutine, `attentionLabel()` helper (Track B)
- `MainActivity.kt` — adapter wired with `moodTracker` and
  `applicationContext` (Track B)
- `ui/presence/layers/Zola3DModelLayer.kt` — P32-D01 camera lock +
  `DEFAULT_MODEL_ROTATION_X = 10f` (Track B)
- `ui/presence/EyeLayer.kt` — saccade pupil/glow dot draw suppressed
  (Track B C7; `EyeLayer` composable body no-op at lines 33–34;
  legacy `drawCircle` calls remain in unused `drawEyeSlot` at lines 42–48)

### Locked values (P32-D01)

| Parameter | Value |
|-----------|-------|
| Camera position | `(-0.45, -0.19, 0.879)` |
| Camera target | `(-0.44, -0.04, -0.118)` |
| Model scale | `0.5f` |
| Model rotation X | `10f` |

### Approved deviations

- **P32-EX-01 (Track A C7):** Core Systems status dots removed; icon +
  label only
- **P32-EX-02 (Track B C3):** Right panel reduced to ATTENTION LEVEL +
  TIME only; `momentumPercent` / `emotionalToneLabel` fields retained but
  not populated or rendered after C3 cleanup

### Open items filed

- **OQ-P32-CONTINENT-OUTLINE-01** — data-driven continent outline deferred
- **F3** — VU-meter static until Phase 33 (`attentionConfidence` stubbed
  at `0.5f`)
- **TODO P33** — `ConversationalStateEngine` momentum signal (P32-D08)
- **TODO P33** — real RMS PCM amplitude for `speechAmplitude` (P32-D17)

### Tracks pending

- **Track C:** Dock buttons (Memory, Conversation, Settings) + show/hide
  interaction model
- **Track D:** Jaw drive animation via `Jaw open` morph target

*Superseded by Phase 32 complete section below (Tracks C and D delivered).*

---

## Phase 32 — HUD Rework, Dock Buttons, and Speech Animation (COMPLETE)

**Audit tip SHA:** `e6ee0e7` (post Track D merge + docs commit)  
**Phase base SHA:** `d4d3f40` (Phase 32 Build Plan commit)  
**Completed:** 2026-06-24 — all tracks complete

### Overview

Phase 32 delivered the full presence visual stack: final GLB with
locked camera and head tilt, HUD left/right panel rework with live
data wiring, dock buttons with show/hide and fullscreen immersive
mode, and jaw drive speech animation via the `Jaw open` morph target
(index 8). Binary amplitude proxy (P32-D17) with Tier 5 scheduler
workaround (P32-TD-EX-01).

### Tracks completed

| Track | Name | Merge SHA | Feature commit |
|-------|------|-----------|----------------|
| Pre | GLB asset swap + camera retune | `dd402c5` | (asset commit) |
| A | HUD left panel rework | `d5b04bf` | `c5d67a0` |
| B | HUD right panel + live data wiring | `411faf1` | `9c6a0d1`, `686b2a1` |
| Lore A+B | Lore closeout Tracks A and B | `46a971d` | `9867fe8` |
| C | Dock buttons + show/hide + fullscreen | `fa7207a` | `caafc7e` |
| D | Speech animation — jaw drive | `14ac7e5` | `d91880b` |

### Key files created

- `ui/presence/layers/CoreSystemsIcons.kt` — seven geometric Core Systems
  icons + Africa outline path (Track A)
- `ui/presence/PresenceInteractionEvent.kt` — `DockReveal`, `DockHide`,
  `DockInteraction` (Track C)

### Key files modified

- `ui/presence/layers/HudLayer.kt` — left panel rework (Track A); right
  panel ATTENTION + TIME only (Track B C3); `LeftPanelFooter` with live
  location (Track B C4/C5/C6)
- `ui/presence/HudShellLayer.kt` — corner L-brackets restored (Track A)
- `ui/presence/state/HudState.kt` — five new fields (Track B)
- `ui/presence/PresenceStateAdapter.kt` — `MoodTracker`, `appContext`,
  location coroutine, `attentionLabel()` helper (Track B); P32-TD-EX-01
  speaking poll `SPEAKING_POLL_MS = 50L` (Track D)
- `MainActivity.kt` — adapter wired with `moodTracker` and
  `applicationContext` (Track B)
- `ui/presence/layers/Zola3DModelLayer.kt` — P32-D01 camera lock +
  `DEFAULT_MODEL_ROTATION_X = 10f` (Track B); jaw drive morph target
  `JAW_MORPH_INDEX = 8` (Track D)
- `ui/presence/EyeLayer.kt` — saccade pupil/glow dot draw suppressed
  (Track B C7)
- `ui/presence/state/DockState.kt` — `isExpanded`, `lastInteractionMs`,
  `DOCK_AUTO_HIDE_MS` (Track C)
- `ui/presence/layers/BottomDockLayer.kt` — three Canvas icon buttons,
  separator, `AnimatedVisibility` (Track C)
- `ui/presence/ZolaPresenceRenderer.kt` — fullscreen immersive mode,
  dock gestures, live `dockState` (Track C)

### Locked values

| Parameter | Value | Source |
|-----------|-------|--------|
| Camera position | `(-0.45, -0.19, 0.879)` | P32-D01 |
| Camera target | `(-0.44, -0.04, -0.118)` | P32-D01 |
| Model scale | `0.5f` | P32-D01 |
| Model rotation X | `10f` | P32-D01 |
| `JAW_MORPH_KEY` | `"Jaw open"` | P32-D16 |
| `JAW_MORPH_INDEX` | `8` | P32-D16 (device confirmed, count=15) |
| `JAW_OPEN_SCALE` | `0.6f` | P32-D16 |
| `DOCK_AUTO_HIDE_MS` | `4000L` | P32-D15 |
| `SPEAKING_POLL_MS` | `50L` | P32-TD-EX-01 |

### Approved deviations

- **P32-EX-01 (Track A C7):** Core Systems status dots removed; icon +
  label only
- **P32-EX-02 (Track B C3):** Right panel reduced to ATTENTION LEVEL +
  TIME only; `momentumPercent` / `emotionalToneLabel` fields retained but
  not populated or rendered after C3 cleanup
- **P32-TD-EX-01 (Track D):** `PresenceStateAdapter.kt` modified outside
  original Track D scope — dedicated speaking poll bypasses Tier 5
  scheduler gate

### Open items filed

- **OQ-P32-CONTINENT-OUTLINE-01** — data-driven continent outline deferred
- **OQ-P32-TIER5-PRESENCE-GATE-01** — Tier 5 scheduler vs presence
  updates during active conversation
- **F3** — VU-meter static until Phase 33 (`attentionConfidence` stubbed
  at `0.5f`)
- **TODO P33** — `ConversationalStateEngine` momentum signal (P32-D08)
- **TODO P33** — real RMS PCM amplitude for `speechAmplitude` (P32-D17)
- **TODO P33** — viseme, blink, and expression shape keys; EyeLayer retirement
- **TODO P33** — restore `PresenceMode.SPEAKING` mode gate on jaw drive
- Panel content wiring (Memory, Conversation placeholders) — future phase
- Waveform visual rework — future pass

### Phase 32 deferred to Phase 33

- Viseme shape keys (Open AH, EH/UH, etc.)
- Blink shape keys + EyeLayer retirement
- Expression shape keys (brow, squint, wide eyes)
- Real RMS PCM amplitude
- Dynamic jaw modulation (vs binary hold-open)

---

## Phase 33 — Presence Fast Path, Blink, Expression, and Viseme (COMPLETE)

**Status:** COMPLETE — 2026-06-25  
**Base SHA:** `3834ca8`  
**Final zola-main tip:** `99812db`

### Presence pipeline state after Phase 33

- **`PresenceStateAdapter`** — two publish paths:
  - `publishFastSnapshot()` — ungated 32ms (`FAST_POLL_MS`); morph-driving
    fields; `BlinkController.tick()` each frame
  - `publishSlowSnapshot()` — Tier 5 gated (`SLOW_POLL_MS`); HUD and
    canvas overlay fields
- **`BlinkController`** — adapter-scoped, tick-based, non-composable;
  drives `blinkProgress` every 32ms; device-tuned timing constants
- **`PresenceVisualState`** — extended with `blinkProgress` and
  `expressionWeights`; all `MOCK_*` presets updated
- **`ExpressionMapper`** — stateless `map(mode, cognitiveLoad)` →
  `ExpressionWeights`; wired in fast path
- **`ExpressionWeights`** — data class: `browRaise`, `browFurrow`,
  `squintEyes`, `wideEyes`, `nostrilFlare`

### 3D model morph target state after Phase 33

| Shape key | Index | Status | Driver |
|-----------|-------|--------|--------|
| Blink left | 0 | WIRED | `state.blinkProgress` |
| Blink right | 1 | WIRED | `state.blinkProgress` |
| Blink both | 2 | WIRED | `state.blinkProgress` |
| Squint Eyes | 3 | WIRED | `expressionWeights.squintEyes` |
| Wide/alert Eyes | 4 | WIRED | `expressionWeights.wideEyes` |
| Brow raise | 5 | WIRED | `expressionWeights.browRaise` |
| Brow furrow | 6 | WIRED | `expressionWeights.browFurrow` |
| Nostril flare | 7 | WIRED | `expressionWeights.nostrilFlare` |
| Jaw open | 8 | WIRED (P32) | `state.speechAmplitude` (binary) |
| Open AH | 9 | WIRED | `state.speechAmplitude` (binary; reset when not SPEAKING) |
| Mid-open EH/UH | 10 | WIRED | `VISEME_MID_OPEN_WEIGHT` during SPEAKING + amplitude |
| Closed M/B/P | 11 | WIRED | reset `0f` when not SPEAKING |
| Round OO/W | 12 | DEFERRED | Phase 34 |
| Wide EE/smile- | 13 | DEFERRED | Phase 34 |
| Teeth F/V | 14 | DEFERRED | Phase 34 |

### Retired in Phase 33

- **`EyeLayer.kt`** — removed; replaced by blink shape keys (indices 0–2)
- **`ui/presence/state/ExpressionMapper.kt`** (canvas `ExpressionPose`
  mapper) — removed; replaced by morph-target `ExpressionMapper`

### Locked values (Phase 33 additions)

| Parameter | Value | Source |
|-----------|-------|--------|
| `FAST_POLL_MS` | `32L` | P33-D04 |
| `SLOW_POLL_MS` | `32L` | P33-D05 |
| `CLOSE_DURATION_MS` | `120L` | P33-TB device tune |
| `OPEN_DURATION_MS` | `180L` | P33-TB device tune |
| `BLINK_WAIT_MIN_MS` | `3000L` | P33-TB device tune |
| `BLINK_WAIT_MAX_MS` | `8001L` | P33-TB device tune |
| `THINKING_BLINK_MIN_MS` | `2000L` | P33-TB device tune |
| `THINKING_BLINK_MAX_MS` | `4501L` | P33-TB device tune |
| `VISEME_MID_OPEN_WEIGHT` | `0.6f` | P33-TD binary proxy |
| `LISTENING_BROW_RAISE` | `0.4f` | P33-TC device tune |
| `THINKING_BROW_FURROW` | `0.7f` | P33-TC device tune |
| `THINKING_SQUINT_EYES` | `0.5f` | P33-TC device tune |
| `ALERT_WIDE_EYES` | `0.9f` | P33-TC device tune |
| `ALERT_BROW_RAISE` | `0.6f` | P33-TC device tune |
| `ALERT_NOSTRIL_FLARE` | `0.4f` | P33-TC device tune |

### Known gaps after Phase 33

- **Mode derivation:** LISTENING and THINKING do not fire on user turns
  (`OQ-P33-TC-MODE-DERIVATION-01`)
- **RMS amplitude:** binary `isSpeaking()` proxy only; viseme ~1s lead/tail
  vs audible speech (`OQ-P33-TD-RMS-01`)
- **P32-TD-EX-01:** 50ms speaking-edge poll retained until Phase 34 RMS
  (`OQ-P33-LORE-EX01-RETIRE-01`)

---

## Phase 34 — Presentation Layer Completion (COMPLETE)

**Status:** COMPLETE — 2026-06-26  
**Base SHA:** `b98f851` (pre–Track A)  
**Final merge SHA:** `ed75db4` (Track E)  
**Audit version:** 2.1

### What Phase 34 delivered

| Track | Deliverable | Merge SHA |
|-------|-------------|-----------|
| A | RMS `speechAmplitudeFlow`; continuous amplitude on fast path | `37d2442` |
| B | Viseme bands 9–11; indices 12–14; jaw mode gate | `5fc4812` |
| B-HF01 | Playback-sync RMS; 300ms SPEAKING hold; jaw pipeline fixes | `2d4b083` |
| C | Stagger 450ms/850ms; `expressionTargetMode` wired | `2b5d623` |
| D | Directedness → confidence; four-layer glow | `f855135` |
| E | FaceLayer/ExpressionPose deleted; EX-01 retired | `ed75db4` |

Chore: `FLAG_KEEP_SCREEN_ON` on `MainActivity` @ `44129c8`.

### Architecture state after Phase 34

- **All 15 morph targets wired** in `Zola3DModelLayer` (indices 0–14)
- **`speechAmplitude`** — live RMS float from `speechAmplitudeFlow` (not
  binary); playback-sync per written slice post-HF01
- **Expression stagger** — `expressionTargetMode` lags `state.mode`;
  breathing 450ms, expression 850ms cumulative
- **`attentionConfidence`** — live from `DirectednessEvaluator` on slow
  path; `cachedAttentionConfidence` bridge to fast path
- **Glow** — four-layer hierarchy (`BASE_GLOW`, active, speech, ALERT
  override) per architecture §6
- **Retired:** `FaceLayer.kt`, `ExpressionPose.kt`, P32-TD-EX-01 edge
  poll (`SPEAKING_POLL_MS`)
- **Screen-on:** `FLAG_KEEP_SCREEN_ON` active in foreground

### 3D model morph target state after Phase 34

| Shape key | Index | Status | Driver |
|-----------|-------|--------|--------|
| Blink left–both | 0–2 | WIRED | `blinkProgress` |
| Squint–Nostril flare | 3–7 | WIRED | `expressionWeights` via staggered `expressionTargetMode` |
| Jaw open | 8 | WIRED | SPEAKING gate + proportional RMS amplitude |
| Open AH – Closed M/B/P | 9–11 | WIRED | Amplitude-band blend when SPEAKING |
| Round OO/W – Teeth F/V | 12–14 | WIRED | `expressionWeights` (mapper + amplitude) |

### Locked values (Phase 34 additions)

| Parameter | Value | Source |
|-----------|-------|--------|
| `SPEECH_AMPLITUDE_THRESHOLD` | `0.05f` | P34-TB device tune |
| `SPEAKING_MODE_HOLD_MS` | `300L` | P34-TB-HF01 |
| `VISEME_BAND_LOW_MAX` | `0.2f` | P34-D05 |
| `VISEME_BAND_MID_MAX` | `0.6f` | P34-D05 |
| `JAW_OPEN_SCALE` | `2.5f` | P34-TB-HF01 device tune |
| `BREATHING_STAGGER_MS` | `450L` | P34-D09 |
| `EXPRESSION_STAGGER_MS_GAP` | `400L` | P34-D09 (850ms cumulative) |
| `BASE_GLOW` | `0.12f` | P34-D08 |
| `ACTIVE_GLOW_MAX` | `0.45f` | P34-D08 |
| `SPEECH_GLOW_MAX` | `0.55f` | P34-D08 |
| `ALERT_GLOW` | `1.0f` | P34-D08 |

### Open questions carried forward

- **OQ-P33-TC-MODE-DERIVATION-01** — OPEN. Sole blocker for visible
  LISTENING/THINKING/ALERT expression morphs during typical conversation.

### Resolved in Phase 34 (lore)

- **OQ-P33-TD-RMS-01** — RMS exposure delivered Track A
- **OQ-P33-LORE-EX01-RETIRE-01** — EX-01 retired Track E @ `2c57598`

### Known gaps after Phase 34

- **Mode derivation:** `deriveMode()` rarely reaches LISTENING/THINKING
  on user turns — expression pipeline and stagger are correct; morph
  visibility blocked until user-attention signal added
- **AttentionRelevanceEngine** — injected but unused (`@Suppress("unused")`);
  future confidence source candidate

---

## Phase 35 — FFT Speech Animation, Location Icon, Waveform, Mode Derivation, Conversation Panel

**Status:** COMPLETE — 2026-06-26  
**Final merge SHA on `zola-main`:** `41cacee` (Track E tip; feature `ec81815`)

### Morph target state (post-Phase 35)

| Index | Shape | Driver | Phase introduced |
|-------|-------|--------|------------------|
| 0 | Blink left | `blinkProgress` | P33-TB |
| 1 | Blink right | `blinkProgress` | P33-TB |
| 2 | Blink both | `blinkProgress` | P33-TB |
| 3 | Squint Eyes | `squintEyes` / THINKING (zeroed P35-TD) | P33-TC / P35-TD |
| 4 | Wide/alert Eyes | `wideEyes` / ALERT | P33-TC |
| 5 | Brow raise | `browRaise` / LISTENING | P33-TC |
| 6 | Brow furrow | `browFurrow` / THINKING (0.15f) | P33-TC / P35-TD |
| 7 | Nostril flare | `nostrilFlare` / ALERT | P33-TC |
| 8 | Jaw open | `bandLow * BAND_LOW_JAW_SCALE (0.18f)` | P32-TD / P35-TC |
| 9 | Open AH | `bandMid * BAND_MID_VISEME_SCALE (0.25f)` | P33-TD / P35-TC |
| 10 | Mid-open EH/UH | `bandMid * VISEME_MID_OPEN_SCALE (0.15f)` | P33-TD / P35-TC |
| 11 | Closed M/B/P | `bandMid` band threshold | P33-TD / P35-TC |
| 12 | Round OO/W | `roundOO` ExpressionMapper amplitude-scaled | P34-TB |
| 13 | Wide EE/smile- | `wideEE` ALERT mode (0.4f) | P34-TB |
| 14 | Teeth showing F/V | `bandHigh * VISEME_HIGH_BAND_SCALE (1.0f)` | P35-TC |

RMS-based signals remain for `deriveMode()`, glow, eye luminance, and
`roundOO` amplitude input. FFT bands drive jaw and viseme morph targets
only during SPEAKING (P35-TC-D01).

### New components (Phase 35)

- **`SpeechAnimationAnalyzer`** — `speech/` package; 512-point DFT;
  3-band energy output; subscribes to `AudioOrchestrator.playbackChunkFlow`;
  runs on `Dispatchers.Default`
- **`LocationOutlineIcons`** — `ui/presence/layers/`; lazy-loads
  `location_outlines.json`; parses SVG paths via Compose `PathParser`;
  caches scaled `Path` objects
- **`ConversationTurnDisplay`** — `ui/presence/state/`; display-only
  data class; `speaker` + `message` fields

### New asset files (Phase 35)

- `app/src/main/res/drawable/ic_waveform.png` — static waveform image
  (P35-EX-01)
- `app/src/main/assets/location_outlines.json` — 70 SVG path strings
  (50 US states + 20 countries)

### PresenceStateAdapter changes (Phase 35)

- `SpeechAnimationAnalyzer` constructed, started, stopped with adapter
  lifecycle
- `bandLow` / `bandMid` / `bandHigh` reads in fast path replace RMS-based
  viseme/jaw signals during SPEAKING
- `locationOutlineKey` derived from Geocoder `countryCode` + `adminArea`
- `isUserSpeakingLatch` + `onUserPartialTranscript()` for LISTENING mode
- THINKING predicate + watchdog + `THINKING_USER_TURN_WINDOW_MS`
- `_recentTurns: MutableStateFlow<List<ConversationTurnDisplay>>` +
  `onTurnComplete()` + session-end clear in `stop()`

### Locked values (Phase 35 additions)

| Parameter | Value | Source |
|-----------|-------|--------|
| `BAND_LOW_JAW_SCALE` | `0.18f` | P35-TC-TUNING-01 |
| `BAND_MID_VISEME_SCALE` | `0.25f` | P35-TC-TUNING-01 |
| `VISEME_MID_OPEN_SCALE` | `0.15f` | P35-TC-TUNING-01 |
| `JAW_OPEN_SCALE` | `1.8f` | P35-TC device tune (was 2.5f) |
| `THINKING_MODE_HOLD_MS` | `600L` | P35-TD-EX-02 |
| `THINKING_USER_TURN_WINDOW_MS` | `8000L` | P35-TD-EX-01 |
| `RECENT_TURNS_MAX` | `10` pairs | P35-TE (20 row items) |
| Location outline rotation | `-12f` degrees | P35-EX-02 |

### Open questions filed (Phase 35)

- **OQ-P35-REHYDRATION-01** — session rehydration from turn buffer
- **OQ-P35-MOUTH-REST-01** — mouth not returning to rest after speech
- **OQ-P35-TRANSCRIPT-SPACING-01** — transcript delta spacing in panel

### Open questions resolved (Phase 35)

- **OQ-P32-CONTINENT-OUTLINE-01** — resolved Track B
- **OQ-P33-TC-MODE-DERIVATION-01** — resolved Track D

### Known carry-forward gaps

- Asymmetric blink (indices 0/1 independent): deferred
- Expression tuning (brow furrow, lip thinning, mouth rest): deferred
  to Phase 36 tuning pass
- Memory panel live wiring: deferred to Phase 36
- **`OQ-P27-RESURFACING-01`** (ContextualResurfacingEngine zero call
  sites): still open
- Barge-in architecture: deferred

### Phase 35 merge SHAs

| Track | Branch | Merge SHA |
|-------|--------|-----------|
| A — Waveform | `p35-ta-waveform` | `48dfe5a` |
| B — Location icon | `p35-tb-location` | `03757bb` |
| C — FFT animation | `p35-tc-fft` | `fb6f82e` |
| D — Mode derivation | `p35-td-mode` | `f171ad6` |
| E — Conversation panel | `p35-te-conversation` | `ec81815` |
| Lore | `p35-lore` | `7638e26` |

---

## Phase 36 — Structured Attribute Read/Write Integrity

**Status:** COMPLETE  
**Final merge SHA on `zola-main`:** `b58c8bc` (P36-E closeout tip; lore closeout pending)

### Canonical attribute read path

All production consumers of `Entity.structuredAttributes` migrated to
canonical `attributes` map or
`EntityAttributeUtils.unifiedFlatAttributesFromEntity`. Consumers confirmed:
EntityMapper, RecallKernel, CanonicalPersonRowOracle, ConversationalStateEngine,
SessionBriefBuilder, EntityBeliefViewHolder, HybridMemoryBridge, MemoryService,
StructuredDurableReadFormatter, PersonalizationContextBuilder,
CanonicalVehicleFactBundle, OwnedRecallAssetClassifier,
ProactiveMemoryAwarenessScanner, StructuredMemoryRetriever,
HybridMemoryCompatPersistence (read surface only). Legacy
`structuredAttributes` bridge fallback in
`StructuredEntityDocument.fromFirestoreMapStrict` remains intentional for
pre-P31 documents.

### Write path normalizer

`PersonCanonicalAttributeNormalizer` now enforced on all three write entry
points: `planPerson` (pre-existing), `planPersonAttributePatch` (P36-C), and
`LiveMemoryCorrectionToolExecutor.tryApplyTextAttributeCorrection` (P36-C).
All attribute writes produce canonical P31-D10 `snake_case` keys.

### In-law role write path

`normalizeRole()` removed from all three call sites in
`LiveMemoryWriteProposalHandler`. Raw role passthrough confirmed. In-law
tokens ("mother-in-law", "father-in-law") now reach
`relationshipRoleCandidates` unmodified.

### HybridMemoryCompatPersistence

Read surface migrated to unified flat attribute helper. Write path (L216–478)
preserved — decommission deferred (`OQ-P36-COMPAT-PERSISTENCE-DECOMMISSION-01`).

### DirectFacts

`MemoryRetrievalPipeline.DirectFacts` data class extended to full P31-D10
canonical key set. Retrieval layer complete. `RecallPipeline
.buildStructuredPrimaryContent` serialization of new fields deferred — known
gap (`OQ-P36-DIRECTFACTS-PRIMARY-CONTENT-01`).

### Recall routing

`ReadModeClassifier` updated — name-prefix interrogative matching, short-query
continuity exception for self-attribute queries. `RecallPipeline` gate 1
self-referential carve-out added. `SelfReferenceQueryMatcher` intervening-word
pattern broadened.

### Trait recall

Trait fast-path gate added in `QueryProcessor.runReasoningFastPaths`.
Upstream self-entity resolution added in `resolveConversationContext` via
`SelfReferenceQueryMatcher`. Trait and personality queries now produce
structured entity recall artifact with `COMMITTED_SCRIPT` Live delivery.
Device verified.

### Async correction stale-read

Accepted as known limitation. `OQ-P36-CORRECTION-STALE-01` filed.

### Speaker-aware self-resolution

`findUserEntity()` currently resolves to account owner.
`SelfReferenceQueryMatcher` and entity lookup remain separate concerns by
design. `OQ-P36-SPEAKER-AWARE-SELF-RESOLUTION-01` filed for future
speaker-aware track.

### Phase 36 merge SHAs

| Track | Branch | Merge SHA |
|-------|--------|-----------|
| Pre | `p36-pre-unified-read` | `7301645` |
| A | `p36-ta-hot-path` | `fe89b7c` |
| B | `p36-tb-belief-session` | `5d6bd85` |
| C | `p36-tc-write-path-completeness` | `79c4a30` |
| D | `p36-td-compat-cold-paths` | `0e41d53` |
| E | `p36-te-directfacts-extension` | `b64160d` |
| F | `p36-tf-recall-routing` | `e770482` |
| G | `p36-tg-trait-fast-path` | `fa3020d` |
| G2 | `p36-tg2-self-resolution` | `4b355ef` |
| P36PRE audit | — | `d42160b` |

---

## Phase 37 Status — COMPLETE

**Theme:** Audio/Animation Fidelity + Session Memory Continuity  
**Lore closeout tip:** `0599b12`

### Animation / Presence

- Morph reset: `transitionSpeakingToSilent()` consolidates all
  speech-end paths; `AMPLITUDE_SILENCE` emitted post-drain on natural
  completion, immediately on interrupt
- FFT band energy: `clearBands()` called via `onSpeakingEndedListener`
  on every speech end; bands no longer freeze on last frame at reset time
- ExpressionMapper dedup: `Zola3DModelLayer` indices 3–7 read
  `state.expressionWeights` directly (AUD-12)
- Viseme 13 wideEE: SPEAKING branch mapping from `speechBandMid`;
  `WIDE_EE_MID_BAND_SCALE = 0.6f` (tuning deferred)
- OQ-P37-DRAIN-ANIMATION-01: drain window mouth freeze filed;
  decay model deferred

### Session Memory

- Turn buffer persistence: `RecentTurnsPersistence`
  (`EncryptedSharedPreferences`); 20-row cap; 2-hour TTL; persists on
  turn complete; rehydrates on session start
- Session teardown: `presenceStateAdapter.stop()` in
  `tearDownAssistantSession()` after `flushAndConsolidateSync` (AUD-23)
- OQ-P35-REHYDRATION-01: visual continuity half resolved;
  cognitive injection (Track F) deferred

### Recall

- P36-HF1: RecallPipeline gate 1 — tool intent imperatives excluded
  from self-reference carve-out; `TOOL_INTENT_ACTION_VERBS` +
  `TOOL_INTENT_NOUNS` constants; `isToolIntentQuery()` guard

### Lore

- OQ-P27-RESURFACING-01: RESOLVED — engine wired since P21
- P32-D17: annotated as superseded by P34-D01/D03
- P37-D01 through P37-D09: recorded

### Phase 37 merge SHAs

| Track | Branch | Merge SHA |
|-------|--------|-----------|
| HF1 | `p36-hf1-tool-intent-gate` | `355a756` |
| A | `p37-a-morph-reset` | `bebfd83` |
| B | `p37-b-viseme-13` | `12f8273` |
| C | `p37-c-turn-buffer-persistence` | `d51a1ac` |
| D | `p37-d-session-teardown` | `aca9b98` |
| E | `p37-e-lore-hygiene` | `f9c947b` |
| Lore | `p37-lore` (direct) | `0599b12` |

### Deferred to Phase 38+

- Track F: SessionBriefBuilder cognitive injection (decisions locked)
- Viseme / jaw scaling constant tuning
- OQ-P37-DRAIN-ANIMATION-01 decay model
- Scenario 2 smoke (sign-out UI)
- RTDB retirement
- Barge-in architecture
- HUD visual rework
- GPS-driven continent outline

---

## Phase 38 Status — COMPLETE

**Theme:** Cognitive Injection + Calendar Coverage + Account UI + Conversation Integrity  
**Lore closeout tip:** `bd6fd3c`

### Shipped

- Track A / A1: SessionBriefBuilder `[RECENT_TURNS]` injection with per-turn temporal grounding (P38-D01, P38-D06, P38-D10)
- Track B: `TOOL_INTENT_NOUNS` expansion + noun-only possessive detection (P38-D07)
- Track C: `CalendarManager` multi-calendar aggregation (P38-D02, P38-D08) + Live summary limit fix (5 → 15)
- Track D: Account panel + 4th dock button, sign-out wiring (P38-D04, P38-D05)
- Track E: Live-routed conversation writes deferred to `onTurnComplete` (P38-D03, P38-D09)

### Session memory / continuity

- `RecentTurnsPersistence` visual rehydration (P37-C) + `[RECENT_TURNS]` cognitive injection (P38-A/A1) — `OQ-P35-REHYDRATION-01` fully resolved
- Live conversation persistence: authoritative Firebase write at `MainActivity` `setOnLiveTurnComplete`; seven RES write sites guarded per approved table

### Discovered during Phase 38 (filed — not regressions)

- OQ-P38-SELF-ENTITY-TOOL-INTENT-BYPASS-01 (HIGH) — possessive calendar/SMS queries bypass tool routing via QueryProcessor P36-G2 upstream self-resolution
- OQ-LEGACY-CALENDAR-UNKNOWN-CLASSIFICATION-01 (HIGH) — bare calendar read phrasing never reaches any calendar-reading code path (legacy NL classifier gap)
- OQ-AUTH-SIGNOUT-FORCED-REPROMPT-01 (MEDIUM-HIGH) — user-initiated sign-out triggers unwanted automatic re-authentication prompt (pre-existing; visible via Track D UI)
- OQ-P38-EPISODIC-SUMMARY-TEMPORAL-GROUNDING-01 (MEDIUM-HIGH) — episodic/session-summary fallback lacks reliable temporal grounding
- OQ-P38-WAVE-B-RECENCY-ROUTING-01 (MEDIUM) — "how long ago" queries misrouted to wall-clock Wave B intent
- OQ-AUTH-IDLE-SIGNIN-SURFACE-01 (LOW-MEDIUM) — no neutral idle sign-in state
- OQ-P38-LEGACY-CALENDAR-CAPS-01 (LOW) — legacy calendar fallback has separate, smaller event caps than Live path
- OQ-P38-RECENT-TURNS-WAVE-B-COVERAGE-01 (LOW) — needs one post-install session to confirm
- OQ-PACKAGE-FILE-PATH-DIVERGENCE-01 (LOW) — deferred mechanical rename

### Process note

Several issues surfaced because Phase 38 exercised code paths (multi-calendar aggregation, Track D sign-out entry point, possessive phrasing in normal use) that had not been thoroughly tested before. Each was independently traced to its root cause and confirmed pre-existing or structurally separate before filing.

### Phase 38 merge SHAs

| Track | Branch | Merge SHA |
|-------|--------|-----------|
| PRE | `p38-pre-audit` | `37ede89` |
| A | `p38-a-brief-recent-turns` | `4ff5663` |
| A1 | `p38-a1-recent-turns-temporal-grounding` | `5043bd7` |
| B | `p38-b-tool-intent-expansion` | `edc2ae8` |
| C | `p38-c-calendar-multi-calendar` | `cec9a30` |
| D | `p38-d-sign-in-out-ui` | `adca268` |
| E | `p38-e-conversation-write-timing` | `bd6fd3c` |

### Deferred to Phase 39+

- Open-question backlog prioritization (highest: OQ-P38-SELF-ENTITY-TOOL-INTENT-BYPASS-01, OQ-LEGACY-CALENDAR-UNKNOWN-CLASSIFICATION-01)
- Left HUD nav interactivity
- Viseme/jaw scaling constant tuning
- OQ-P37-DRAIN-ANIMATION-01 decay model
- RTDB retirement, barge-in, HUD visual rework

---

## Phase 39 Status — COMPLETE

**Theme:** Open-Question Backlog Prioritization — routing integrity + auth sign-out  
**Lore closeout tip:** `c7aca30`

### Shipped

- **Track A0:** `ToolIntentMatcher` extracted to `memory/recall/` (P39-D01)
- **Track A1:** Self-entity tool-intent bypass — P36-G2, hybrid-first, RecallPipeline null-phrase guards (P39-D02); relationship-with-X (P39-D06) and kinship-possessive path-A (P39-D07) found in smoke, fixed in-phase
- **Track B:** Calendar QUERY patterns + `handleUnknown()` safety net; `"show schedule"` / `"my schedule"` CREATE mis-steal fix (P39-D03)
- **Track C:** `userInitiatedSignOutPending` — no auto re-prompt after UI sign-out (P39-D04); `AccountPanelSignOutBridge` rewire on session start (P39-D05)

### Resolved OQs (Phase 39)

- OQ-P38-SELF-ENTITY-TOOL-INTENT-BYPASS-01
- OQ-LEGACY-CALENDAR-UNKNOWN-CLASSIFICATION-01
- OQ-AUTH-SIGNOUT-FORCED-REPROMPT-01

### Discovered during Phase 39 (filed — not regressions)

- P39-D06 / P39-D07 — relationship routing gaps (A1 smoke)
- P39-D05 — AccountPanelSignOutBridge lifecycle (C smoke; pre-existing P38-D)
- OQ-AUTH-ACCOUNT-SWITCH-WITHOUT-RESTART-01 — account switch without restart
- OQ-TEST-SUITE-GMAIL-SMS-POLLER-FLAKE-01 — six unit-test failures, pre-existing
- Account panel stale UI after sign-out — repro evidence on OQ-AUTH-IDLE-SIGNIN-SURFACE-01

### Process note

Phase 39 reinforced the Phase 38 lesson **twice more**: real, pre-existing bugs surfaced in **Track A1** (P39-D06, P39-D07) and **Track C** (P39-D05) smoke testing beyond what P39PRE found. Both were resolved by **folding addendum phases into the existing track branch** (same pattern as P39-A1 Phase 4b/4c/4e and P39-C Phase 5b–5d), not new branches.

**G-LORE-DEFER** (consolidated lore at phase end) was adopted mid-phase after Tracks A1/B wrote some entries early. Once established, Track C followed it cleanly. **Recommend G-LORE-DEFER as the standing convention from Phase 40 onward** — single end-of-phase lore pass; tracks write progress docs only until then.

### Phase 39 merge SHAs

| Track | Branch | Merge SHA |
|-------|--------|-----------|
| A0 | `p39-a0-tool-intent-matcher-extraction` | `67fc567` |
| A1 | `p39-a1-self-entity-tool-intent-bypass` | `cd81aaf` |
| B | `p39-b-calendar-classifier-fix` | `3be08b0` |
| C | `p39-c-auth-signout-fix` | `1ceaf35` |

### Deferred to Phase 40+

- Neutral idle sign-in surface + account panel refresh (`OQ-AUTH-IDLE-SIGNIN-SURFACE-01`)
- Login / account switching without app restart (`OQ-AUTH-ACCOUNT-SWITCH-WITHOUT-RESTART-01`)
- Wave B recency routing (`OQ-P38-WAVE-B-RECENCY-ROUTING-01`)
- `[RECENT_TURNS]` Wave B coverage confirmation (`OQ-P38-RECENT-TURNS-WAVE-B-COVERAGE-01`)
- Unit test baseline cleanup (`OQ-TEST-SUITE-GMAIL-SMS-POLLER-FLAKE-01`)
- Conversational-memory temporal read/write architecture (Phase 41 stub — see `ROADMAP.md`)

---

## Phase 40 — Track A complete (file path alignment)

**Status:** Track A merged; Track B (temporal grounding) not started  
**Branch:** `p40-a-path-rename` → `zola-main`

### File path alignment (Track A)

Physical directory structure now matches package identity across `main`, `test`, and `androidTest` source roots. Legacy `com/example/avapersonalassistant/` path fully retired (1,498 `.kt` renames + 11 companion test fixes). Fifty pre-existing beebo-path test files byte-identical except `QueryProcessorBoundaryArchitectureTest.kt` (P40-F07). Compile and unit tests green (2,521 / 0 failures); device smoke passed.

### Phase 40 merge SHAs

| Track | Branch | Merge SHA |
|-------|--------|-----------|
| A | `p40-a-path-rename` | `23d634f` (feature `f383a3e`) |
| B | `p40-b-temporal-grounding` | `9d6e014` (feature `cfb50a7`; tip record `cc4c661`) |

**Resolved:** `OQ-PACKAGE-FILE-PATH-DIVERGENCE-01` (Track A); `OQ-P38-EPISODIC-SUMMARY-TEMPORAL-GROUNDING-01` (Track B — formatting fix; field verification PARTIAL)

---

## Phase 40 — Track B complete (temporal grounding)

**Status:** Merged to `zola-main` (`9d6e014`)  
**Branch:** `p40-b-temporal-grounding`

### Temporal labeling consistency (Track B)

Shared `formatSessionSummaryAge()` helper (`SessionSummaryAgeFormatter.kt`) wraps `TemporalRecencyFormatter` (P21-D09) at three consumer surfaces:

| Surface | File | Field verification |
|---------|------|-------------------|
| Episodic recall spoken lead-in + Live grounding `- When:` | `EpisodicRecallIntentHandler.kt` | ⚠️ PARTIAL — incidental P21-D09 phrasing in ad hoc sessions; scripted 7+ day scenario not run |
| Session brief `[SUMMARY]` age prefix | `SessionBriefBuilder.kt` | Code + unit tests only — `session_summary_age_labeled` log never captured in three device sessions |
| Memory block "The last conversation was …" | `MemoryInjectionBuilder.kt` | Code + unit tests only — `recency_sentence_*` logs never captured; aligned to `SessionBoundaryResolver` (same source as `[TEMPORAL]`) |

`relativeTimeLead()` coarse day-bucket math removed. `[TEMPORAL]` via `TemporalContextAssembler` unchanged (already correct pre–Track B).

**Field findings filed as OQs at P40-LORE:** retrieval-tier inconsistency, stale embedded facts, handler/Live response divergence, entity temporal gap (boundary case for Phase 41).

---

## Phase 41 — Silent Context Enrichment (complete)

**Status:** Merged to `zola-main` — Tracks A–D; lore closeout base `211edab`  
**Build plan:** `zola-architecture/Zola_Phase41_Build_Plan.md`

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A | `753e9be` | Retrieval-tier parity, uniform fail-closed bar (P41-D04) |
| B | `26fa2a6` | Structured temporal-validity signal on session summaries (P41-D03) |
| C | `ffbea91` | Shared `CandidateScoringLibrary` extraction (P41-D05) |
| D | `1f82456` | Mid-session refresh + relevance-aware open-loop selection (P41-D01, P41-D01-EXT) |

Track E (`EnrichmentContent` / silent enrichment delivery) **did not start** — deferred to Phase 42 stub, blocked on `OQ-P41-D-DEVICE-SMOKE-UNCONFIRMED-01`.

### Retrieval tiers

Episodic and session-summary fallback now share a confidence bar (P41-D04). Semantic/RAG tier remains a separate, unaddressed concern (Delta 02).

### Session summaries

Now carry structured temporal-validity classification (`temporalValidity`, `staleAfterMs`); stale future-dated facts excluded from both silent injection (`SessionBriefBuilder`) and explicit recall (`EpisodicRecallIntentHandler` fold-in, P41-D03 Phase 4b/4c).

### Context injection

`SessionBriefBuilder` gained a mid-session refresh capability via formal PCI-D02 amendment (P41-D01). Open-loop selection within that refresh evolved from recency-only to relevance-aware (P41-D01-EXT) after real-world testing showed the naive version failing to surface genuinely relevant older loops. **Device confirmation of the relevance-aware selection remains outstanding** — tracked via `OQ-P41-D-DEVICE-SMOKE-UNCONFIRMED-01`.

### Silent enrichment delivery

Not built this phase. Track E deferred to Phase 42, blocked on the above.

### Resurfacing

Scoring logic extracted to shared library `CandidateScoringLibrary.kt` (P41-D05); resurfacing's own behavior unchanged and proven via characterization testing; library not yet consumed by anything else.

### Standalone bugfix (same day, separate branch)

`BUGFIX-SELFREF-01` (`42a4cd8` on `zola-main`): `SelfReferenceQueryMatcher`'s possessive-object gate converted from negative blocklist to positive attribute allowlist; bare-name fallback in structured recall made fail-closed (decline when no real question was asked) and honest (state "not on file" when a real question has no data) across all five call sites of `buildStructuredEntityRecallArtifact`. Merged and confirmed via device smoke test before Phase 41 tracks resumed.

### New findings requiring future attention

Ten open questions filed at P41-LORE (see `OPEN_QUESTIONS.md`), spanning number normalization, session-timing mechanics, open-loop deduplication, pronoun resolution, dual-path routing, suspected resource contention, suite flakiness, and Track D device-smoke confirmation gap.

**G-LORE-DEFER** honored for Tracks A–D progress docs; consolidated lore in this pass.

---

## Phase 42 — RTDB Retirement (complete)

**Status:** Merged to `zola-main` — Tracks A–D; lore closeout from base `611ffb3`  
**Build plan:** `zola-architecture/Zola_Phase42_Build_Plan.md`

### Track merge SHAs

| Track | Feature SHA | Merge SHA | Scope |
|-------|-------------|-----------|-------|
| A | `b897170` | `b897170` (fast-forward) | Firestore turn-history store (`P42-D07`) |
| B | `04d485c` | `4111d33` | Reader rewiring — `QueryContextFactory`, `HandoffContextSerializer` (`P42-D08`) |
| C | `c93d4ee` | `113813b` | Buffer decoupling — `recordCompleteTurn` independent of write success |
| D | `436996b` | `b65adeb` | RTDB deletion; Firestore-only `saveConversation` |

### RTDB retirement

RTDB turn-by-turn conversation mirror fully retired. Durable history is Firestore-only at `users/{userId}/memory/conversation_history/conversation_history/{entryId}`.

### Intent routing

`QueryContextFactory.getOrLoadHistory` reads `FirestoreConversationHistoryRepository.loadRecentHistory`. Device smoke confirmed behavior-preserving (dark-gray/Saturday routing test; garage-lumber/paint test — `P42-B_Progress.md`).

### Device handoff

`HandoffContextSerializer.recentHistory` reads same Firestore path — code complete (`P42-D08`). Feature not yet reachable in production (`ENABLE_DEVICE_REGISTRATION = false`; multi-device not implemented).

### Session consolidation buffer

`recordCompleteTurn` decoupled from any storage write success (Track C). Five intentional call sites confirmed by P42C-PRE audit: `MainActivity.kt:683` (Live primary), `persistLegacyPipelineConversationHistory:833` (legacy primary), `RES.kt:569` (Live backup), plus `!started` Live-primary branches at `RES.kt` ~1030 and ~1389.

### Known open issues carried forward

- `OQ-P42-09` — retention policy mismatch (Privacy Plan Tier 3 vs last-30/180-day implementation)
- `OQ-P42-10` — **HIGH** — forget-all does not purge Firestore conversation history
- `OQ-P42-11` — `saveTurn` exception swallowing
- `OQ-P42-12`–`OQ-P42-14` — P42C-PRE follow-ups (playback-end hook demotion, different-text dedupe gap, Streaming Cognition doc)
- `OQ-P42-15` — teardown consolidation timeout unrealistic (MEDIUM)
- `OQ-P42-16` — `NetworkOnMainThreadException` on sign-out consolidation (HIGH)
- `OQ-P35-TRANSCRIPT-SPACING-01` — Impact corrected: defect persists in stored turn history, not display-only

### Design decisions added at closeout

`P42-D07` through `P42-D10` in `DESIGN_DECISIONS.md`. `P42-D01` (summary-scoring unification) deferred to Phase 44.

---

## Phase 44 — Semantic Relevance Scoring (complete)

**Status:** Merged to `zola-main` — Tracks P44-0, P44-A, P44-B, P44-C,
P44-D, P44-E, P44-F, plus HOTFIX, HOTFIX-2, HOTFIX-3

### Semantic scoring infrastructure

`SemanticRelevanceScoringService` live: on-device ONNX Runtime +
`all-MiniLM-L6-v2` INT8, production Kotlin WordPiece tokenizer,
fail-closed on `Exception` and `Error` (post-`HOTFIX-2`). Model version
key: `minilm-l6-v2-onnx-int8-v1`.

### Entity embeddings

`OpenLoop`, `SessionSummary`, `EpisodicMemoryEntry` all carry
write-time-computed `embeddingVector` + `embeddingModelVersion`, wired
at every production write path (`OpenLoopClassificationService`,
`FocusStackManager.writeEvictionOpenLoop`, `ConsolidationLoop` Step 6,
`EpisodicMemoryBuilder`). No backfill worker exists — not needed for
this cutover (greenfield); will be needed at the next model version
change.

### Retired: substring/keyword-overlap scoring

Six former independent authorities (`SessionSummaryRetriever`,
`MidSessionRefreshTrigger`, `SessionBriefBuilder` both sections,
`EpisodicMemoryRanker`'s fuzzy components, `CandidateScoringLibrary`'s
fuzzy components) now unified on the one shared scoring service.
`INTENT_TOPIC_KEYWORDS`-style substring matching fully retired at every
site, not retained as fallback.

### `EpisodicMemoryRanker`

Hybrid: always-on structural weight block (parent/linked/intent/
scenario/importance/recency) unchanged, confirmed via diff; only
`computeQueryOverlapRaw` and the free-text branch of
`computeThemeOverlapRaw` now semantic.

### `CandidateScoringLibrary`

Hybrid: four ID/enum-based connection types unchanged; topic-match and
`EMOTIONAL_ECHO` branches now semantic, score-time-computed (not stored,
per `RecallCandidate` not carrying an embedding field), scaled via
ceiling-fraction formulas (`similarity * 0.85` / `* 0.50`) with a
device-confirmed `0.35` raw-similarity floor. `PATTERN_VIOLATION`/
`PATTERN_MATCH` classifier untouched, flagged for future dedicated work
(`P44-AUD-35`).

### Open-loop retrieval

`FirestoreOpenLoopRepository` filters `resolved==false` server-side, no
new composite index required (device-confirmed). Recency confirmed a
scoring component, not a sole shortlist gate, at every migrated call
site.

### Real thresholds, device-confirmed

`MIN_SESSION_SUMMARY_SCORE` = 0.40 (was 0.55); `MIN_OPEN_LOOP_RELEVANCE_SCORE`
unchanged at 0.55; `CandidateScoringLibrary`'s raw-similarity floor =
0.35. All backed by genuine on-device accept/reject data, not defaults.

### Bug found and fixed during this phase (unrelated to scoring)

Session-end consolidation was silently deleting `OpenLoop` Firestore
documents due to a missing `recordType` filter in a shared collection
reader — real, confirmed data loss, fixed in `HOTFIX-3`.

### Known open items (non-blocking)

`FINDING-P44-E-STORED-EMBEDDING-UNUSED` (correct but wasteful —
resurfacing recomputes `OpenLoop` embeddings at score-time rather than
using the stored one); `FINDING-P44-F-SEMANTIC-STORE-MISSING-INDEX`
(unrelated pre-existing missing Firestore index, quick Console fix,
not yet actioned); `OQ-P42-05d`/`OQ-P42-05e`/`OQ-P42-15`/`OQ-P42-16`
carried forward, unaddressed by this phase.

---

## Phase 43 — Silent Enrichment Delivery (complete)

**Status:** Merged to `zola-main` — Tracks A–D; lore closeout from base
`63af4bb`  
**Build plan:** `zola-architecture/Zola_Phase43_Build_Plan.md`  
**Audit:** `zola-architecture/audit/P43PRE/` (merge
`403f4562be6a7e27b3e319d58b8cc79097109569`)

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A | `ae28cef15b234722b9bfc18bf96b19c017f62b1f` | `EnrichmentContent` contract (P41-D02 foundation) |
| B | `261694bd4137c057800295cc995c2672ad399fe8` | Per-turn relevance trigger (P43-D04–D07) |
| C | `a7eb30e089c110f86514fc0a6d835b0bda1e8eee` | Live consumer wiring; legacy string path retired |
| D | `52863856d362f4de47c9e5e2e838e52c1c46cda4` | Text/handler consumer (P43-D08, P43-D09) |

### EnrichmentContent contract

Track A shipped the shared `EnrichmentContent` /
`EnrichmentSourceTier` type under `memory/enrichment/` — fulfilling
`P41-D02`, which Phase 41 specified but never built. No wiring in Track
A; producer and consumers followed in B–D.

### Mid-session open-loop trigger

Per-turn relevance scoring replaces `topicShiftDetected` / 15-turn /
10-minute backstop gating (`P43-D04`). When a focus subject is present
and nothing clears the gate, selection returns empty — no
recency-fallback populate (`P43-D05`). Pool bounded by
`MID_SESSION_CANDIDATE_POOL_CAP` (first-pass 50). Bind-time embedding
warmup (`P43-D06`) plus shared ORT session constrained to one intra-op
thread (`P43-D07`) address cold-start and concurrent-load timeouts under
the always-attempt design.

### Dual-path delivery

Both Live (`MemoryInjectionBuilder`) and text
(`GeneralIntentHandler` / `handler_general`) consume the same mid-session
`EnrichmentContent` (`P43-D01`). Track D scoped to mid-session open-loop
enrichment only; RAG / `PersonalizationInjector` unification deferred
(`P43-D08`). Device-confirmed handler inject:
`mid_session_recall_delivery_injected path=handler_general`.

### Shared rendering

Budget / stale-filter / truncation lives in one place —
`memory/enrichment/EnrichmentRenderer.kt` (`P43-D09`). Both consumers
call the shared top-level function; neither keeps a private copy.

### Device regression found and fixed during this phase

Under P43-D04's per-turn scoring, concurrent session-start resurfacing
(~40 evaluations) plus mid-session embeds on an unconstrained ORT
session caused severe 8-core oversubscription — confirmed 148-second
stall against a 1500ms budget (99x), multi-minute voice unresponsiveness.
Root cause: no `SessionOptions` intra-op thread constraint on the shared
`SemanticRelevanceScoringService` session. Fixed via
`setIntraOpNumThreads(1)` (`P43-D07`); bind-time warmup (`P43-D06`) is
best-effort mitigation for cold init. Unbounded resurfacing fan-out
itself remains open (`OQ-P43-RESURFACING-BURST-SCALING-01`).

### New findings requiring future attention

Four open questions filed at P43-LORE: `OQ-P43-RESURFACING-BURST-SCALING-01`
(**HIGH**), `OQ-P43-LIVE-FAILED-NO-RECOVERY-01`,
`OQ-P43-POOLCAP-TUNING-01`, `OQ-P43-RAG-ENRICHMENT-UNIFICATION-01`.
`OQ-P41-OPENLOOP-DEDUP-01` reinforced with firsthand Firestore evidence
during Phase 43 testing. See `OPEN_QUESTIONS.md`.

**G-LORE-DEFER** honored for Tracks A–D progress docs; consolidated lore in this pass.

---

## Phase 45 — Forget-All Purge + Resurfacing Concurrency Throttle (complete)

**Status:** Merged to `zola-main` — Tracks A + B; lore closeout from base
`e4560257c2551ad8d24eda5782045c73763fe367`  
**Build plan:** `zola-architecture/Zola_Phase45_Build_Plan.md`  
**Audit:** `zola-architecture/audit/p45/`

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A | `0f1046e256f19d40058f389632d3790c909b2196` | Forget-all Firestore `conversation_history` purge; fatal-on-failure; history cache clear |
| B | `5ad3619b94904c965fda6647b46d1b023b5f4f83` | Session-start resurfacing `Semaphore` permits=4 |

### Forget-all / privacy cascade

Firestore `conversation_history` now purged on forget-all; purge failure is
fatal to reported success (`P45-D01`); in-memory history cache also
cleared (`P45-D03`). Known remaining gap:
`cognitive_prep` / `initiative_queue` / `voice_identities` still
unpurged (`OQ-P45-A-FORGET-ALL-CASCADE-GAP-01`).

### Resurfacing session-start fan-out

Bounded to 4 concurrent evaluations via `Semaphore` (`P45-D02`);
unbounded-concurrency risk closed. Wall-clock improvement at this
permit count was inconclusive vs the prior unthrottled baseline.
Known new risk: concurrent Live turns during the burst can degrade
severely or fail outright, independent of permit count
(`OQ-P45-LIVE-BURST-CONTENTION-01`). `OQ-P43-RESURFACING-BURST-SCALING-01`
remains OPEN (fan-out bounded; burst-duration concern only partially
addressed).

---

## Phase 46 — Forget-All Cascade Completion + Live Reliability (complete)

**Status:** Merged to `zola-main` — Tracks A–D; lore closeout from tip
`e877ecd8c70fb69dbfe835cbe1be730887a1a671`  
**Build plan:** `zola-architecture/Zola_Phase46_Build_Plan.md`  
**Audit:** `zola-architecture/audit/p46/`

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A | `111f7ad` (feat `3a45504`, fix `4a8c8a1`) | `cognitive_prep` + `initiative_queue` purge; verify-and-retry on `purgeCollectionDocuments` |
| B | `fcc3aee` | Firestore `voice_identities` + on-device `VoiceEmbeddingStore` purge; `worldVoiceIdentitiesCollection()` |
| C | `1de6e83` | Live-aware resurfacing coordination + watchdog 25s (`P46-D06`) |
| D | `bf0008d` (feat tip `6cfc877`) | Sticky `FAILED` recovery via `GeminiLiveSession.obtain()` (`P46-D07`) |

### Forget-all / privacy cascade

Forget-all is now complete across all known Firestore paths previously
left open by Phase 45 — `cognitive_prep`, `initiative_queue`, and
`voice_identities` — plus the on-device voice biometric store.
Re-enrollment after forget-all is expected product behavior (`P46-D01`).
`purgeCollectionDocuments` was strengthened with verify-and-retry after
Track A device smoke found an intermittent, scale-dependent
partial-purge gap at high document counts (~1,663 candidates) — a
durability improvement to the whole paged-purge mechanism (shared with
Phase 45's `conversation_history` purge), not just this phase's
additions. Initiative-queue *pruning* remains open
(`OQ-P26-QUEUE-ACCUMULATION-01`).

### Live reliability

Session-start resurfacing contention addressed via Live-aware
gate-before-launch + cancel-and-defer layered on Phase 45's `Semaphore`,
plus stop-gap `RESPONSE_WATCHDOG_TIMEOUT_MS=25000` (Track C, `P46-D06`).
Sticky `FAILED`-state recovery wired without requiring sign-out
(Track D, `P46-D07`). Both device-confirmed. Two known, accepted
limitations carried forward as OQs / caveats: the
STT-before-`sendUserTextTurn` gate window (~0.9–1.8s ungated), and
STT's lack of self-healing after a hard network failure
(`OQ-P46-STT-NO-NETWORK-RESTORE-01`).

### New privacy/security consideration surfaced this phase

On-device `VoiceEmbeddingStore` is not user-scoped
(`OQ-P46-VOICE-STORE-NOT-USER-SCOPED-01`) — standing architectural note
for anyone assessing multi-user readiness. Acceptable under today's
single-user model and Track B's full-store wipe; blocks future
multi-user voice recognition / multi-user forget-all until resolved.

---

## Phase 47 — Sign-Out Reliability, Keystore Recovery, Queue Pruning, STT Restore (complete)

**Status:** Merged to `zola-main` — Tracks A–D; lore closeout from base
`d3b550f7173457079275cc74eb29842c09b5ddcc`

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A | `92f2e5cdc271812e0305db5f2b69e7c6884458d5` | Sign-out consolidation fire-and-forget |
| B | `446ad03fb07af3e3a042d7b64d67025ac2a9392a` | Keystore decrypt recreate-on-failure |
| C | `cbab245d2baf0c3ff143b5126d10c82ae70ae4b5` | Initiative queue pruning |
| D | `d1c2956fa64a880d8a628e893df1408c547305ac` | STT network-restore |

### Sign-out consolidation

Gemini emotion-enrichment decoupled from sign-out's 5-second teardown
deadline via baseline-first save + detached async scope (`P47-D01`).
Resolves the diagnosed cause of `OQ-P42-15`/`OQ-P42-16`. Two residual,
disclosed limitations found only through device testing: the outer
timeout can still be exhausted by open-loop age-write volume
(`OQ-P47-OPENLOOP-UNBOUNDED-GROWTH-01`), and enrichment writes issued
after sign-out fail against invalidated auth, by design
(`P47-D06`, `OQ-P47-ENRICHMENT-POSTSIGNOUT-AUTH-01`). A separate,
unscoped finding: `ArcStateUpdater` now permanently sees baseline
(not enriched) summaries at Step 6b — real relationship-arc data
quality impact, needs its own audit (`OQ-P47-ARCSTATE-BASELINE-REGRESSION-01`).

### Keystore decrypt recovery

`RecentTurnsPersistence` recovers from `GeneralSecurityException`
(recreate-on-failure) instead of throwing or silently failing —
`P47-D02`, field-validated via natural on-device reproduction.

### Initiative queue

Pruning (age 20 sessions + 25/category cap, expire-in-place) plus
session-start read-path relief — `P47-D03`. 88.5% read reduction
confirmed at real device volume (~1,663 documents). A low-severity,
self-healing timing gap between pruning and same-session reads is
disclosed, not fixed (`OQ-P47-INITQUEUE-PRUNE-LAG-01`).

### STT reliability

`DeepgramForegroundRecognitionEngine` self-heals after a hard, sustained
network loss via a lifecycle-scoped `NetworkCallback`, without requiring
a background/foreground cycle — `P47-D04`, device-confirmed.

---

## Phase 48 — Arc Backfill, Open-Loop Abandonment, Enrichment Durability, Live Re-Sign-In (complete)

**Status:** Merged to `zola-main` — Tracks A–D; lore closeout from base
`8e5f684f05ac035b3a3d955df830de47759dde0f`

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A | `ca56093a` | Arc nightly backfill — idempotent correction |
| B | `72158b7a` | Open-loop `ABANDONED` + batched age-writes |
| C | `c94e0b42` | Post-sign-out enrichment buffer + replay |
| D | `6c4922d4` | Reactive account panel + live same-account re-sign-in |

### Arc nightly backfill

Nightly idempotent correction of baseline-scored arc friction/depth once
enrichment lands (`P48-D01`/`P48-D02` — `correctionPending` + snapshot +
`sessionCountAtWrite` gate). Resolves
`OQ-P47-ARCSTATE-BASELINE-REGRESSION-01`.

### Open-loop abandonment

`ABANDONED` terminal state (`resolved` stays false) plus chunked
`WriteBatch` age-writes (`P48-D03`). Resolves
`OQ-P47-OPENLOOP-UNBOUNDED-GROWTH-01`.

### Enrichment durability

`EncryptedSharedPreferences.commit()` buffer + `WorkManager` replay on
`PERMISSION_DENIED` (`P48-D04`). Resolves
`OQ-P47-ENRICHMENT-POSTSIGNOUT-AUTH-01`.

### Live same-account re-sign-in

Reactive account panel + Activity-lifetime Sign In bridge (`P48-D05`)
and same-account mismatch guard (`P48-D06`). Partially resolves
`OQ-AUTH-IDLE-SIGNIN-SURFACE-01` and
`OQ-AUTH-ACCOUNT-SWITCH-WITHOUT-RESTART-01` (residuals remain — see
`OPEN_QUESTIONS.md`).

---

## Phase 49 — Session Identity + Firestore Write-Safety Hardening (complete)

**Status:** Merged to `zola-main` — Tracks A0–E; lore closeout from base
`b83a5f57407ae909db9e3a867d0afcca6b2d7c41`

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A0 | `84af786d` | Session identity (`MD-D05`) |
| B | `02d57c66` | Transaction + precondition (`MD-D06a`) |
| C | `b211adc1` | Bootstrap create-if-absent (`MD-D06b`) |
| D | `6f3892dc` | Atomic increment + single-flight (`MD-D06c`) |
| E | `7ad16e74` | RMW-7 dead-code deletion (`MD-D06d`) |

### Session identity

`SessionRecord` / `SessionIdentityProvider` sole mint; AlarmManager grace
+ process-death survival; mint on `onStart`. Resolves
`OQ-KMPPRE-SESSION-IDENTITY-FRAGMENTATION-01`.

### Transaction + precondition

Arc, alias map, OpenLoop DORMANT protected; Arc retry-then-succeed vs
DORMANT fail-closed shapes proven live.

### Bootstrap hardening

PERSON/SELF/PRIMARY_BOND create-if-absent via DWA/governor; mutex
removed; first-writer-creates concurrency shape confirmed.

### Atomic increment + single-flight

`mentionCount` and initiative aging use `FieldValue.increment`; persisted
session-ID-keyed age-bump guard.

### RMW-7 cleanup

Dead hybrid `saveConversationState` (+ 19 stubs) deleted;
`saveConversationActiveContext` sole writer confirmed.

Resolves `OQ-KMPPRE-UNPROTECTED-RMW-01` collectively (B/C/D/E).

---

## Phase 50 — Post-Phase-49 Hardening: Cache Consistency, Teardown Threading, Alias Collision Handling (complete)

**Status:** Merged to `zola-main` — Tracks A–F; lore closeout from base
`3fb589312c3a499a3012764991278ed8dcb97e44`

### Track merge SHAs

| Track | Merge SHA | Scope |
|-------|-----------|-------|
| A | `a3deaa1fac70480301b06a045d3ddcfa32062d40` | Cache singleton (`P50-D02`) |
| B | `1a4c7ad1` | Atomic structured snapshot (`P50-D03` / amended `MD-D08`) |
| C | `86c6a2d9` | Multi-map consumer migration (`P50-D03` / amended `MD-D08`) |
| D | `67cf5af7` | `profileMemory` residual CHM (`P50-D04`) |
| E | `b8e7db2c` | Teardown threading (`MD-D07`) |
| F | `a2b5ea97` | Alias collision logging (`MD-D09`) |

### Structured memory cache

Single owning `StructuredMemoryCacheService` (`MemoryService`). Per-user
atomic `StructuredCacheSnapshot` (graph + both resolvers + structured
hybrid values + `contradictionIndex`). Named multi-accessor consumers
migrated to single-fetch reads; one residual un-migrated site
(`hydrateCompatibilityViewFromStructuredCache`) tracked as
`OQ-P50-HYDRATE-INTERNAL-MULTIFETCH-01`.

### profileMemory residual

Concurrency-protected via `ConcurrentHashMap` for residual
(non-structured) keys after Track B stopped writing the four structured
`hybrid_*` keys here.

### Session teardown / consolidation

`flushAndConsolidateSync` is non-blocking for all callers via
thread-aware dispatch (main launches on process-owned scope; non-main
awaits). Resolves `OQ-P49-TEARDOWN-MAIN-THREAD-BLOCK-01`.

### Alias writes

Destructive same-normalized-key collisions logged; same-value collapses
remain silent. Resolves `OQ-P49-ALIAS-KEY-COLLAPSE-01`.

---

## KMPPRE Audit (thin-client readiness)

**Status:** COMPLETE — census merge `e2544d04`, analysis merge
`62825190`. Synthesis: `zola-architecture/audit/kmp-pre/Zola_KMPPRE_Audit_SYNTHESIS.md`.
Direction: MD-D01–D04 in `DESIGN_DECISIONS.md`.

**Census (declared boundary):** 15 PORTABLE / 35 TANGLED / 6 BOUND —
core cognition + Firestore-touching classes + platform estate + ML
classes; remaining provisional-cognition packages declared out of
scope by name in the synthesis.

**Strongest confirmations:** zero Firestore snapshot listeners (pull-
based throughout); 11/12 models pure Kotlin with epoch-ms timestamps;
15/22 repositories already interfaced; `DurableCollectionWriteGateway`
funneling real for consolidation; cognition ML = exactly one MiniLM
model + one service + one tokenizer (voice ML never crosses in).

**Strongest liabilities:** 24 non-repository classes with direct
Firestore ops; 12 stateful cognition singletons; 8 unprotected RMW
families (same list as multi-device concurrency hazards); turn-buffer
volatility (in-memory only); session identity fragmented into three
uncorrelated notions.

**Gates the next phase:** spikes SPIKE-ML-1/2/3; seven synthesis §6
decisions (embedding locality, wire format, session identity, write
serialization, thick→thin sequencing, Cloud Function hosting,
turn-buffer durability). Standalone current-system OQs filed as
`OQ-KMPPRE-*` in `OPEN_QUESTIONS.md`.

---

*Zola Master State Audit — version 3.4 (Phase 50 complete — Tracks A–F; cache consistency, teardown threading, alias collision handling)*
*Created: 2026-05-26; Phase 9 exit update: 2026-05-27; Phase 10 exit update: 2026-05-29; Phase 11 exit update: 2026-06-01; Phase 12 exit update: 2026-06-02; Phase 14 exit update: 2026-06-03; Phase 15 exit update: 2026-06-03; Phase 26 lore closeout tip: `80103b6`; Phase 30 RIL closeout tip: `9aa8bb7`; Phase 31 lore closeout base: `93d9bfa`; Phase 32 Tracks A+B lore closeout base: `411faf1`; Phase 32 complete lore closeout tip: `e6ee0e7`; Phase 33 complete lore closeout tip: `99812db`; Phase 34 complete lore closeout tip: `ed75db4`; Phase 35 complete lore closeout tip: `41cacee`; Phase 36 complete lore closeout tip: `b58c8bc`; Phase 37 complete lore closeout tip: `0599b12`; Phase 38 complete lore closeout tip: `bd6fd3c`; Phase 39 complete lore closeout tip: `c7aca30`; Phase 40 complete lore closeout tip: `cc4c661`; Phase 41 lore closeout base: `211edab`; Phase 42 lore closeout base: `611ffb3`; Phase 44 complete lore closeout tip: `d92a6d9`; Phase 43 lore closeout base: `63af4bb`; Phase 45 lore closeout base: `e456025`; Phase 46 complete lore closeout tip: `5421da3`; Phase 47 complete lore closeout tip: `d566c3e9`; Phase 48 complete lore closeout tip: `69917499`; KMPPRE lore update tip: `aea5d51776ced478683b3e5b5620c17af1629972`; Phase 49 complete lore closeout tip: `af8201bd`; Phase 50 complete lore closeout tip: `ddfb690f002645e5ee8b1ce4454b214de3eb7d90`*
