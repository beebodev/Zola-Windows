# Architecture Docs — Full-Read Notes (per source doc)

*Historical record, kept for traceability: Claude's notes from the full read of the 39 Android-era docs (2026-10-29). In the repo this file lives in `zola-architecture/audit/arch-docs-swap/`.*

*2026-10-29. Author: Claude. Working notes from reading all 39 top-level docs in `zola-windows/zola-architecture/` in full, plus SOUL.md and VOICE_CONFIG.md. Companion to `claude/ARCH_DOCS_MERGE_MATRIX.md` (v1.1). These are Claude's observations and recommendations, not decisions. "!!!" marks items that need Brian's judgment.*


## Master Architecture Plan (title in file: "Zola Vocal Computing Architecture Plan") → A01
- 20 pillars; each is a summary of a sub-doc (pillars 18 identity, 19 distributed presence, 9/9a attention+heat duplicate their own docs nearly verbatim). A01 should keep vision + principles + ownership map and point to sub-docs, not re-summarize them.
- Windows notes: S5 (no full duplex), C1 (Path B native client vs hermes serve), C3 (single capture owner), P1 providers, P2 = "Edge TTS + local faster-whisper" — STALE: Deepgram Aura-2 Pandora since P9-D14.
- Keep: Truth Ownership Rule, Speech Authority Constraint (speech never alters facts), single authority, provider abstraction, "speech is a costly action", workers prepare / core decides, no worker speaks.
- Worth keeping for vision: Deferred Cognition & Summary (group events "three things happened while you were in the shop") → A11.
- Shop / vehicle / glasses endpoints → A12 vision. Health/Spotify APIs → A08 vision source list.
- Title mismatch (file name vs "Vocal Computing") — rename.

## Agent Map → DISSOLVE across many (matrix said A01/A08/A10 — widen)
- Fully Android (class names, Android phases 5–12). Core rule "Agents prepare. The core decides. No agent writes memory, speaks, runs tools or routes" → A01 principle (matches P9-D01/D03 watcher + zola-phone).
- Agent 12 World State Snapshot / Agent 1 Context Cache / Agent 6 Notification Priority → A08 (stale-field confidence 0, cautious interpretation wins on conflict).
- Agent 2 Consolidation, Agent 9 Active Entity Resolver + ContactRelationshipIndex (one index, not a separate agent) → A03/A04. Agent 9 = the P10 T5 contact index → person resolver carry-forward. Important.
- Agent 4 Memory Warm-Start → A06 (Context Injection later retires it in favour of a session brief).
- Agent 3 Attention Context, Agent 11 speculative intent → A07.
- Agent 5 Proactive Trigger Monitor (candidate expiry windows), Agent 8 Tool Warm-Start → A10.
- Agent 7 Behavioral Pattern → A02 style profile.
- Agent 14 Compute Priority Scheduler (live speech/turn/TTS never yield) → A01 principle.
- Agent 15 DailyBrief → references Zola_Daily_Brief_Architecture.md, NOT in repo. Windows S12 deferred. → A08/A11 vision note only.

## Identity & Personality Framework → A02
- Platform-neutral vision. Seed traits (10; locked vs adaptive table), growth rings, Style Profile (context-scoped, signal-count confidence 1–5/6–20/21+), feedback loop (explicit > implicit; "Not now" → dampening not style), anchors, memory-driven personality, drift detection, baseline review, endpoint consistency.
- One Kotlin schema block — drop.
- TENSION with SOUL: "Restrained" is LOCKED ("does not speak unless value exceeds cost") vs SOUL "I take initiative rather than waiting to be told... bring useful observations". Not a contradiction if restraint = interruption discipline, but A02 must word it so restraint doesn't read as passivity (vision §1 proactive awareness). Flag for Brian.
- Open Qs worth keeping: can Brian view/edit/reset style profile; drift report visible or silent.

## Identity Source Consolidation Plan → A02 (mostly dropped)
- Part 1 (3 Android prompt surfaces, rename Ava→Zola, Kotlin package, Firebase) = obsolete. On Windows SOUL.md is the single identity source (Hermes profile) — record that as the "as built".
- KEEP: locked behavioral rules list; communication style defaults; style profile fields + weighted-average signal model (explicit 1.0 / ambiguous 0.6 / implicit 0.2 / session 0.3); drift ranges + hard resets (warmth ≥0.95 sycophancy etc.); context default targets table (shop/desk/vehicle/emotional).
- CONFLICT: locked rule "save confirmations are never announced — memory is silent unless questioned" vs P5-D03 / SOUL "When I save something on my own, I mention it in a few words". P5-D03 wins (locked Windows decision). Must not carry the old rule.

## SOUL.md (identity/, live — not merged)
- STALE line: "Right now, I operate through a text-based Windows client." She is voice-first since P2. Flag for a SOUL fix (separate from docs; SOUL is runtime → Cursor/lore change).
- A02 "as built" should cite SOUL sections: How I talk out loud (P4 naturalness), math (P6-CALC), memory (P5), forget (P6), Workspace (P8/P9), drafts/send (P8).

## Relational Continuity → A02 (or separate "Relationship with Brian")
- Vision portable: arc = history / trajectory / texture; informs, never announces; friction state vs trajectory (slow to escalate, proportional recovery HIGH→ELEVATED→NONE); depth score 0–1 (EARLY/DEVELOPING/ESTABLISHED/DEEP); continuity initiative low-pressure only, silent in HIGH friction.
- All implementation is Firestore/ConsolidationLoop/Gemini — drop.
- Vision-alignment note: stress/emotional register of Brian are INFERENCES → must carry provenance (vision §4), and are sensitive (A14).
- No Windows equivalent built. Depends on episodes (P6) + time (P6) — plausible P11/P12+ seam.

## Relational Calibration → A02 (or separate)
- Vision: familiarity is a ceiling not a target; two axes (baseline depth vs damper friction/gap: 30/90/180 days); composition PersonaMode → calibration ceiling → style; behavioral directives, never state labels (no "our early relationship" leakage) — strong, keep.
- Repair register by depth — keep.
- !!! CONFLICT WITH VISION §3 / one-authority: "Assumption License" (NONE / INLINE_VERIFY / SILENT_EXECUTE) lets relationship depth grant silent execution of preference-based actions. That is action authority decided by an expression layer. Vision: "independent judgment does not grant execution authority"; controlled autonomy needs its own decision. → Move assumption license to A15 as a DEFERRED capability that only A15 can grant; calibration may only shape wording. Keep the safety-filter invariant (always say the allergy/safety constraint aloud). Flag for Brian.
- RECOMMEND: A02 split into A02 Identity & Personality + A02b Relationship with Brian (continuity + calibration). Both docs are long and the relationship pair is its own subsystem.

## Memory Hierarchy → A03 (core)
- Platform-neutral vision + Kotlin contracts. Layers L0 turn / L1 short-term / L2 session / L3 episodic / L4 structured canonical / L5 behavioral / L6 reflective. Authority order (user instruction > tool result > contract > L4 > L2 > L3 > L5 > L6 > weak inference). Read modes (direct, contextual injection, continuity, autonomous scan — "read ≠ permission to interrupt", relationship reasoning). Write classification (7 classes) + Durable Write Authority. Promotion, decay, consolidation, topic stack, injection rules ("don't announce memory use"), conflict handling, forget cascades, log tags, validation scenarios A–G.
- Windows as-built mapping: L4 = USER.md/MEMORY.md flat files (P6-D01 authority) with the store as derived index; L3 = P6 episodes (Brian's turns only, G-BRIAN-ONLY); DWA ≈ P6-D02 rules; forget = P6-D06; L1/L2 = Hermes session.
- GAP vs vision §4: layers are by DURABILITY only — no axis for PROVENANCE (stated / retrieved / observed / inferred / uncertain). Memory Agency's "authority classification" (Stage 6) is that axis — merge them in A03 as two separate axes.
- GAP: no layer for observations from external sources (email/texts) → that is Perception Memory's observation → promotion path (G3). A03 needs one model covering conversation + external observations.
- "Memory injection must not announce" vs P5-D03 brief mention on SAVE — different things (save mention vs recall mention); fine but note.
- Topic stack (§8) → A06.
- Validation scenarios A–G → good starting set for P11 acceptance alongside the 4Runner scenario.

## Memory Agency → A03 + A11 (+ A14)
- "Governed belief model": every item carries source, scope, authority, freshness, privacy, allowed-use metadata. Strong — this IS vision §4.
- 12 memory types (identity, entity, relationship, episodic, semantic, preference, instruction, pattern, open loop, context, correction, privacy-as-property).
- 11-stage write pipeline incl. entity resolution, sensitivity, AUTHORITY classification (user-stated / confirmed / perception / inferred / tool / implicit) = provenance, scope, salience (8 criteria; thresholds 0.40 / 0.65), lifecycle (CAPTURED→PENDING→ACTIVE→REINFORCED→STALE→CONTRADICTED→ARCHIVED→FORGOTTEN; never auto-forget).
- Recall pipeline w/ authority ranking ("perception never beats user-stated"), freshness → hedged language ("Last I knew… is that still the case?").
- Memory Use Governor usage modes (silent context / tone / disambiguate / suggest / only if asked / after confirmation / never proactive / never aloud / suppress; default silence) → A14 (it governs disclosure) with a pointer from A03.
- Open loops, cognitive tension, resurfacing engine → A11 (generate candidates; never speak; MA-P6 route through the attention engine).
- CONFLICT to resolve: here open loops are MEMORY; on Windows, P9 open loops/watches live in the proactive store, which P9-D06 keeps SEPARATE from memory. A03/A11 must state which owns open loops (lasting boundary or temporary limit?). Flag for Brian / P11 audit.
- MA-P2 "Zola decides what to remember… user need not say remember" — matches P5-D03 + SOUL. Good.

## Perception Memory → A03 (KEY for P11)
- Written for camera/mic observations, but it is exactly the "observation → attributed claim → controlled promotion" model the 10/19 direction asks for. Generalise in A03 to ALL external observations (email, texts, notifications, calendar) not just sensors.
- L1 ephemeral (per-type decay) → L2 episodic pattern (recurrence ≥N across ≥3 sessions, confidence ≥0.75, reset on contradiction) → L3 world-graph promotion (memory system owns; entity candidates need Brian's confirmation: "I've noticed a silver truck… someone you know?") → L4 world fact lifecycle (certainty drift with floors by authority tier, age multiplier at read time, retrievalWeight = confidence × age × authority, reinforcement resets drift).
- Authority tiers: user-stated 1 > user-confirmed 2 > system-inferred 3 > perception-derived 4 > candidate (not in graph). = provenance ladder for vision §4.
- Never promotable: emotional state as person type ("Brian is stressed"), third-party identity claims, perception+hearsay combos. Lasting boundaries — keep.
- Windows mapping: P9-D07 raw content ≤7 days = L1 analogue for mail/texts; nothing distilled survives today (VISION_ALIGNMENT_REVIEW G3). This doc is the design answer to G3.
- Refers to "Entity-Native Memory Principle" — not in repo (missing doc #3).

## Self-Model Awareness → A03 (confidence + hedging section)
- Hedged language IS the correction mechanism (NONE/SOFT/STRONG/GAP thresholds); gaps surface only when relevant; same epistemic rules for Brian, third parties, herself; accuracy computed from correction record not stored; absence scaling (>14-day gap: well-reinforced beliefs capped at 30-day effective age so she doesn't hedge everything); never shift context mid-response.
- Windows A7 locked: read-only boundary no harder than Hermes's own write model. S2 deferred.
- Hard dependency: corrected facts must be excluded from retrieval before hedging works (else old wrong text + hedge coexist). Windows: P6-D06 forget erases; check correction path in P11 audit.
- Fits A03 well; small. No separate doc.

## Cross-Domain Correlation (stub) → A03 (identity resolution) + A10 (situation recognition)
- One authority for cross-domain joins; read-only; conservative matching (false connection worse than missed); derived relationships at read time.
- ContactRelationshipIndex: canonical name, emails, calendar co-occurrence, Gmail frequency, memory entity link, "relationship weight score", last interaction. = the P10 Track 5 contact index / Agent 9. A03 should make this the ONE person resolver (phone numbers + emails + Contacts + memory entity), per VISION_ALIGNMENT_REVIEW §5.
- VISION TENSION: "relationship weight score derived from frequency + recency" treats how-often-you-email-someone as importance. Vision: known/frequent sender ≠ trusted/important relationship. Keep frequency as an evidence signal only; relationship meaning comes from A04.
- Daily Brief consumer + Zola_Daily_Brief_Architecture.md (missing doc).

## Relationship Inference (LOCKED Android P19) → A04
- Firestore edge schema + predicate taxonomy (Tier 1 storable, Tier 2 read-time only: grandparent, aunt/uncle, cousin, step, in-law), source ladder USER_STATEMENT 1.0 > SYSTEM_INFERRED 0.85 > SYSTEM 0.9(!), derivedFrom + truth maintenance (retract inferred edges when source changes), 3-hop max, -0.1 per hop floor 0.5, surfacing policy by confidence, gender-neutral label when unknown.
- "LOCKED" status is Android lore (P19-Dxx) — NOT a Windows decision. A04 must not inherit locks; restate as vision/recommendations. Flag.
- VISION TENSION: P19-D03 stores SIBLING_OF at write time (write-time inference) vs vision §4 / principle "infer derived relationships at read time where appropriate". Defensible exception but should be Brian's call on Windows.
- GAP vs 10/19 direction: predicates are kinship + employment + friend. Vision needs family / friend / business / acquaintance / service provider ("my mechanic", "the bank", "the school") without a trusted-contact list. Taxonomy needs extending in A04 (organisations, roles, service relationships).
- Missing doc referenced: Zola_Firestore_Write_Safety_Architecture.md.
- Concrete family facts (Brian's sons etc.) appear in examples only — fine.

## Social Graph Reasoning → A04
- People earn a node: explicit introduction OR ≥3 distinct sessions in 90 days. Distinct-session tracker. Same-name disambiguation by natural question; fail-soft; back-off 3 deflections → 14 days quiet; context-clue routing meanwhile.
- Third-party beliefs held loosely (lower confidence ceiling — "one side of a story"); ThirdPartyAssertionGuard: venting-derived traits enter PROVISIONAL, promote only by confirmation or 3 sessions without correction/negative valence. Strong; keep.
- Professional predicates EMPLOYEE_OF, WORKS_AT.
- !!! VISION CONFLICT: Non-goal says the graph is built "from what the user actively shares in conversation, not from environmental observation". 10/19 direction: Zola should understand people across email, texts, Contacts, memory — sources beyond conversation, as attributed observations. A04 must allow observed evidence (attributed, lower authority) to inform person models — via A03 promotion rules. Also Google Contacts should be able to SEED a person entity (known sender) without meeting the conversation recurrence threshold, while relationship meaning stays separate. Flag.
- Longitudinal tone about people deferred (v2) — keep deferred; sensitive.

## Relational Intelligence Layer (umbrella) → DISSOLVE
- Content = index of the 5 subsystems + shared infra + shared contracts + layer-wide privacy principles (third-party beliefs held loosely; observations never headlines; no psychological profiling) → those principles go to A04/A14.
- Windows lore carried here: S2 (whole layer deferred), S3 (Calibration BLOCKED, standalone proxy rejected), A6 (single delivery path vs Hermes's own extra speech paths: review.summary, child-session completes, heartbeat — left unsuppressed per A2) → A6 must land in A01/A11 as an open question; it matters for proactive speech authority.
- Dual-endpoint cache invalidation on edge correction → A04.

## Temporal Reasoning → A05
- Time is meaning, not metadata; reasoning lens, no storage. SessionBoundaryResolver (never blocks; null = unknown → suppress gap-dependent output), ThreadArcClassifier FRESH <24h / ACTIVE <7d / AGING 7–21d / QUIET 21–60d / OVERDUE >60d / DORMANT, temporal context block, temporal initiative (QUIET 0.2–0.35, OVERDUE 0.4–0.55, never above 0.55), central cooldown in evaluator (72h / 48h). Deferred: seasonal reasoning, resolved-topic cadence.
- Windows as built: P6-TIME / P6-D05 ambient time (SOUL "I can see when each message reaches me…"), P6 episodes with when-said. Not built: thread arcs, temporal initiatives.
- GAP for P11 "temporal understanding": doc covers ELAPSED time only. Missing: event time vs mention time ("Micah's car broke down Tuesday" told on Thursday), future time (upcoming calendar events, deadlines, "in two weeks"), validity intervals on facts ("used to work at X"). Android had GovernedTemporalIntervalRecord (mentioned in SMA doc) but no doc describes it. A05 needs these added as vision.

## Conversational Continuity → A06
- Vision: conversation never ends (cools / suspends / resumes / branches); topic graph; attention weights with decay (recency, emotion, focus, task, environment); context reinjection types (direct, implicit "it still won't start", environmental, emotional); branch recovery with bridge phrase; focus stack (DUPLICATES Memory Hierarchy §8 topic stack — merge once in A06); continuity confidence (high inject / medium soft phrasing / low suppress → ask); safety rules (no forced recall, emotional respect, relevance filter, not surveillance); consolidation (dup with A03 — keep in A03, pointer here); state snapshot sync (→ A12); Domain Priority Matrix (explicit request > active topic > task > branch > environment > history > assumptions) — keep; 5-stage turn lifecycle.
- WINDOWS TENSION: proposes a "Conversational State Engine" as single source of truth for conversation state. On Windows the Hermes session/transcript is the conversation authority; a parallel state engine would be a second authority (principle: extend Hermes, don't add competing authority). A06 should define continuity as a layer over the Hermes session (prompt/context injection + Zola-owned derived state), and say so explicitly.
- As built: Hermes sessions + resume; P5 past-conversation search on request (P5-D06); P6 episodes; P4/P7 clarify; S87 (proactive lines not in stored session).

## Context Injection → A06
- Portable ideas: session brief = PRIVATE context, never read aloud, never "I see you have an open loop…"; structured not prose; one read-only builder; fixed priority order with whole-section truncation (roster > frame > last summary > open loops > time-relevant facts); partial brief OK; never block session start; bounded mid-session refresh (topic-shift or 15 turns/10 min, 1.5s timeout, fail closed).
- Everything else (Gemini Live setup message, RTDB, MemoryWarmStartAgent retirement, Kotlin) = drop.
- Windows as built: Hermes system prompt + SOUL + USER/MEMORY injection + P6 store retrieval; P9 'note'/whats_pending. A06 should map the brief idea onto Hermes's supported prompt hooks.
- Example data inconsistency: brief example lists "Breanna · Daughter" while Memory Hierarchy example says Breanna is Brian's wife — example only; don't carry examples with real family facts into docs.
- Missing docs referenced: Zola_Architecture_Entity_Taxonomy.md, Zola_Architecture_Firestore_Structure.md.

## Session Identity → A06
- Android app-foreground session with 30 s grace; session per user not per device; no cross-device session continuity (memory carries, session doesn't); single mint call site; session ID as provenance on every durable write. MD-D05 = Android lore lock.
- Windows: Hermes owns sessions (resumable, persistent). Keep principles: one session authority (Hermes), session id on writes as provenance, consolidation promptly at session end, "session boundary ≠ memory boundary" (vision §1). Drop foreground/grace mechanics.

## Conversational Attention → A07
- Platform-neutral (the 9 "windows" hits are "continuation window"). Attention before understanding; single attention authority between transcript finalisation and reasoning; directed vs ambient vs continuation vs interruption; confidence bands (high process / medium light clarify / low fail SILENT); wake word = override not foundation; endpoint-aware (desktop: work calls, stronger privacy); speaker & social context; attention state machine (CLOSED, WAKE_WORD_LISTENING, ACTIVE, CONTINUATION_WINDOW, CLARIFICATION_PENDING, INTERRUPTED, SUPPRESSED_AMBIENT…); 3 kinds of clarification (attention vs semantic vs action confirmation — never confuse); no ambient durable writes; sensitive domains need higher confidence; inbound attention ≠ outbound interruption (separate authorities; user questions bypass dampening).
- Windows as built: P2 wake word + capture (C3 single capture owner = native client), P4 clarify (S20), P7 voice clarify, barge_in off (Brian's choice; wants talk-over back without breaking spoken answers), no follow-up listen after proactive lines (P9-SPEAK D7(a)). Speech track (SP-D01/02, VOICEPRE) owns the next steps.
- Direct link to vision §3 Engagement ("respond naturally without restarting") → the continuation window after a proactive line is the missing piece for P12. Cross-ref A11.

## Streaming Cognition → A07 (condensed)
- "Think early, commit late": provisional artifacts with isCommitEligible=false; stable phrase detector, intent forecaster, entity tracker, memory/tool candidate preparation, correction detector (before commit = patch; after commit = new turn), interruption classes (hard/soft/correction/new-command/clarification), draft buffer (never truth), full observability.
- Android actors (QueryProcessor, Gemini Live, ResponseExecutionService) — drop. Windows S5: full duplex not a requirement; Hermes chained STT→LLM→TTS. On Windows most of this is a latency/first-words concern owned by the speech track (VOICEPRE, SPEECH-BASELINE), so A07 keeps the principles only, as vision.

## Living Voiceprint & Multi-Speaker → A07 (vision section) ; privacy → A14
- Android implementation (CampPlus/sherpa-onnx, Silero VAD, audio tap on Deepgram loop, EncryptedSharedPreferences, Firestore metadata). Vision: in-session speaker tracking, introduction-triggered enrollment ("who's joining us?", UNKNOWN cluster gate 2 in 6 s), embedding pool w/ never-evicted formal anchor, refinement only ≥0.70, room-aware turn-taking (wait for natural pause; never narrate speaker switches), voice ↔ PERSON entity link (future).
- Hard privacy rules worth keeping: embeddings never leave the device; no raw audio stored; introduced people not gatekeeper-eligible without Brian's explicit grant; full view/delete.
- Windows: Brian uses Zola alone in his office, integrated mic. Nothing built (check what P7-VOICEAUTH covers — likely voice-mode auth/lock, not speaker ID). Pure vision. Biometric = A14 sensitive category.

## Environmental Awareness → A08 (sources, signals, user state) + A10 (interpretation, fusion, scoring, dispositions)
- Pipeline: signal → perception → structured event → interpretation → fusion → user state → attention scoring → privacy → decision → speech / silent log / deferred summary / escalation. "Raw signals never directly produce speech."  "Silence is a valid cognitive outcome."
- Sources (location, time, calendar, weather, traffic, device, notifications, health, media, shop/home, cameras, vehicle, wearables); dispositions (ignore, silent log, passive display, deferred summary, spoken heads-up, confirmation, escalation — exactly one per event); awareness modes (passive, normal, focus, shop, driving, security watch, quiet hours); anti-annoyance protections; observability questions ("why did Zola speak / stay silent?").
- Overlaps heavily with Master Plan §6–9, Attention Engine (scoring + heat duplicated) and Event Bus (schema + user state duplicated). Merge: sources + events + user state → A08; interpretation + fusion + scoring + dispositions → A10.
- !!! VISION/DECISION CONFLICT: "Zola must not read message content aloud without explicit permission; in shared environments even sender identity withheld". 10/19 direction: unprompted lines should carry meaningful context in her own words (numbers, amounts, locations allowed), protecting only secrets and sensitive info; Brian in his office (private). P9-D11 fixed phrasings are a TEMPORARY limit. A08/A14 must restate this as: content may be spoken in private context per Brian's direction; shared-space restraint stays; secrets/codes never (R1). Flag.
- Weather/traffic/location/health sources: none built on Windows (Life360 arrival notices via phone notifications is the only location-ish signal, P10).

## Event Bus + User State Model → A08
- Unified event schema (eventId, sourceWorker, category, type, timestamp, expiresAt, interpreted content, suggestedSummary hint, baseRelevance, urgencyTier 1–4, confidence, privacySensitivity PUBLIC/HOUSEHOLD/PRIVATE/SENSITIVE, requiresUserDecision, relatedEntities, dedupKey, groupingTag). Integrity rules (confidence <0.4 → passive log; expired dropped; dedup; SENSITIVE w/o permission → silent log).
- "The bus is the only path" to the engine; no worker speaks or notifies directly. Heat is NOT a user-state field (separate concerns, meet only in the engine).
- User State Model: activity, workspace, cognitive load, interruption tolerance, noise, others present, device state, conversational readiness, emotional register (inference!), calendar state; every field an estimate with confidence + staleness; conflict rules (higher confidence wins; on ambiguity assume higher-cost; on-change beats periodic). Known-place model. Audio environment monitor (classify, never record).
- Windows mapping: P9 watcher + P10 zola-phone feed ONE proactive store (P9-D06) — that store is the de facto event bus; ranker/surfacing = engine seed. A08 "as built" should say so and note where the schema differs (no confidence, no privacySensitivity label, no expiresAt?) → P11/P12 audit questions.
- CONFLICT: "message previews / calendar titles must not enter the bus as readable text without explicit permission" vs Brian's P9 choice (watcher reads full emails, trimmed, gives a gist) — Brian's decision supersedes; record as an informed choice.
- Emotional register as a user-state field = inference about Brian → provenance + A14 sensitivity.

## Communication Intelligence (Android "as built" P11/P12) → A08 (design reference only)
- Documents Android Daily Brief email + SMS pipelines (heuristics first, model second; consent separate per channel; "analysis ≠ storage"; communication intelligence is not memory).
- Windows notes STALE: S13 says reading texts on Windows "needs research" — Phase 10 delivered it via the Android companion + zola-phone over Tailscale. P3 says Gmail via Hermes's connector — Windows actually built its own Workspace plugin in P8 (check: P8-D0x plugin path). Must be corrected.
- Useful: email 5-stage triage pattern; consent-per-source idea; Daily Brief remains deferred S12.

## SMS Intelligence (Android design) → A08 (design reference) — mostly superseded by Phase 10
- "Known contacts only" gate (unknown numbers never analysed). VISION CONFLICT: vision §3 "information from an unknown sender may be important". Windows P10-D10 already chose ordering (contacts above unknown), not exclusion — Windows is closer to the vision; don't carry the Android gate.
- Relationship weight by memory entity 0.9 / calendar attendee 1.0 / phone book 0.6 — another single-score collapse of trust+importance (vision says keep separate).
- Two-step send confirmation; texting send deferred on Windows (P10-D17, RCS/MMS send research).
- Natural surfacing examples ("Micah sent you a few texts — looks like he's asking if you're free this weekend") = good illustration of vision §1 natural engagement → A11.
- Old Android send bug, Telephony provider, warm-context Kotlin → drop. Refs missing docs Zola_Daily_Brief_Architecture.md, Zola_Agent_Architecture.md.

## Environmental Perception → A09
- Pure vision (cameras, doorbell, motion, smart home, vehicle, wearables, glasses): input → sensor adapters → normalisation (one real event = one signal) → perception workers (motion, person, vehicle, package, audio, scene continuity) → spatial zones → temporal persistence → multi-sensor correlation → structured events → confidence layer → continuity per zone ("unknown person present 11 min") → memory integration via DWA → bus. Privacy: person / plate recognition and camera retention need separate explicit consent, zone exclusions enforced at input, sensor failure lowers confidence.
- Nothing built on Windows. Platform-neutral. Keep as A09 vision (Brian: unbuilt areas stay full vision).
- Overlap: event schema (A08), interpretation (A10), memory integration (A03 perception memory).

## Perceptual Input Layer → A09 (+ A11 foregrounding, A14 biometrics)
- Phone-centric (camera upright policy, ML Kit, CameraX, Android overlay). Two tiers: Watchdog (notices, no network, no storage) vs Active Perception (understands, in-memory only). Typed observation schema (USER_CONFIRMED, THIRD_PARTY_PRESENT, EXPRESSION_READING, VOICE_TONE, ENVIRONMENT_CLASSIFIED…). Face + voice enrollment on-device.
- Foregrounding levels 1 ambient surface / 2 soft (dismissible) / 3 hard (rare) — the engine picks; confidence gates level; existing suppression applies; foregrounds count toward heat. → maps well onto Brian's 10/25 "assistant at the office door" principle → A11 delivery mechanisms (PC: presence glow / HUD cue → spoken "got a second?" → full delivery).
- Lasting boundaries worth keeping: P1 raw frames/audio never stored; P2 biometrics never leave device; P3 perception never triggers output directly; P5 uncertain perception lowers proactivity; P6 can be fully off.
- !!! INTERNAL CONFLICT between source docs: this doc P4 "third-party biometric data is never captured — no voice capture, no identity attempt" vs Living Voiceprint doc (introduction-triggered enrollment stores introduced people's voice embeddings). A07/A09/A14 must pick one; Brian's call (flag).
- Third-party present → memory writing of conversation suspended (interesting rule; keep as vision).
- Windows angle: the PC has a webcam + mic; Brian alone in office. "Is Brian at his desk" presence is the realistic first perception on Windows (would help delivery timing). Vision only.

## Attention/Relevance Engine + Dampening → A10
- Attention as finite resource; relevance scoring on 3 axes (impact, timeliness, user-relevance); urgency tiers 1 override-eligible / 2 standard / 3 low / 4 passive; interruption cost (activity, noise, recency, conversation, emotion); CurrentHeat w/ curved decay, context-modified; contextual profiles (shop, desk, driving, human conversation, home/security); override full/partial/deferred (conservative); channel selection separate from surface decision; deferred summaries with expiry ("A few things happened while you were working…"); user-initiated speech never dampened; heat ≠ user state.
- !!! VISION GAP: one relevance number + one urgency tier carries importance, timeliness AND eligibility. Vision §3 needs SIX separate responsibilities (source trust, importance, interruption eligibility, delivery timing, action authority + relationship understanding per direction). Source trust and action authority are missing entirely. A10 must be re-organised around the six; heat/cost = delivery timing; tier/override = eligibility; impact axis = importance.
- "Restraint as a feature… default leans toward not speaking" — keep, but balance with vision §1 proactive awareness (over-suppression risk is listed in the doc itself).
- Windows as built: P9 ranker = four labels + gist (importance seed, item-level); only loop_matched speaks (eligibility = watch match); quiet hours 22–07 (timing floor); P10 code-only text ranking. No heat model.

## Autonomous Behavior → A10 (governor, triggers, modes) + A11 (deferred summaries, emotional regulation) + A02 (behavioral learning)
- Context Aggregator → Situational Model → Attention Model (topic heat) → Trigger Engine (candidates only) → Response Governor (8-step: freshness, permission, redundancy, mode, heat threshold, below-threshold disposition SILENT_LOG/DEFER/DISCARD, output SPEAK/NOTIFY/PASSIVE_DISPLAY/ESCALATE, route + heat + full decision log). "Looks for reasons to stay silent."
- Autonomy modes PASSIVE / ASSISTIVE (default) / CONVERSATIONAL / FULLY_AUTONOMOUS (explicit only); downgrade immediate, upgrade needs explicit or sustained signal.
- Behavioral Learning Layer + Style Profile = DUPLICATE of Identity Framework §2–4 → A02 only.
- !!! INTERNAL AUTHORITY CONFLICT across source docs: Autonomous Behavior says the RESPONSE GOVERNOR is the single authority for proactive output; Attention/Relevance Engine says IT is the sole authority; Master Plan has the engine as "final gatekeeper". A10 must name ONE owner (principle: one authority per responsibility). Windows: P9 surfacing + client gate + speak path exist — P12 audit maps who owns it now.
- !!! TERMINOLOGY: "autonomy modes" here = how much proactive SURFACING is allowed. Vision "autonomy" = increasing ACTION authority. Rename in A10 (e.g. "proactivity levels") so A15's action autonomy isn't confused with it.

## Cognitive Engine (Android P-later, DECISIONS LOCKED there) → A10 (prep) + A11 (initiative queue)
- "Prep kitchen" — expensive thinking (gap scoring, pattern detection, world-model targets) between sessions / idle; live session reads results. Durable initiative queue (per-candidate records; survives sessions; ages up; never silently discarded; removed only when surfaced / superseded / aged out). Hydration order (persisted → precomputed → dedupe → rank: time-sensitive > open loops > curiosity gaps → frequency limits). Curiosity level derived from world-model density (sparse → more questions), not a dial. Engines activated one at a time. Empty queue is valid — no synthetic filler.
- Windows mapping: P9-D01 (background work is code, never a Hermes turn) + P9 durable proactive store ≈ initiative queue. Keep principles; drop Firestore + Android worker names. CEA-Dxx locks are Android lore, not Windows.
- TENSION: CEA-D05 "no candidates added mid-session" fits curiosity, but contradicts live events (watcher email / phone text arriving mid-conversation). A11 must distinguish in-conversation engagement from event-driven proactive delivery.
- Adds a THIRD gate claim ("EngagementGovernor AND AttentionRelevanceEngine must both authorize") → feeds the A10 single-owner question.

## Cognitive Engagement → A11
- Curiosity "motivated by genuine gaps, expressed at appropriate moments, governed by restraint — sounds like interest, not interrogation". Three modes: curiosity inquiry (≤1/session), pattern investigation (tentative hypothesis check, ≤1/session, only if no inquiry), world-model building (≤1/week/entity, relaxed moments only). Silent engagement is the default and most valuable. Engagement Governor (frequency, timing, weight, social fit, topic sensitivity, trust state) → proceed / defer / suppress. Avoidance ends inquiry. Answers feed memory as USER_STATED.
- Good contrast example ("I've been wondering about that noise… did the heat-soak thing pan out?" vs "Reminder: you mentioned an engine noise on Tuesday…") — exactly vision §1 natural engagement.
- INSIGHT for A11 shape: Android docs cover IN-CONVERSATION engagement well (curiosity, resurfacing) but EVENT-DRIVEN proactive delivery (watcher/phone, P9/P12, door-knock first, follow-up without wake word) only thinly. A11 needs both halves.
- Windows: nothing of the curiosity side built; P9 has "offer once to watch" (SOUL) which is a small engagement behaviour.

## Distributed Presence (Android) → A12 (vision)
- One mind, many bodies; Core Presence Layer owns identity, memory, continuity, user state, heat, autonomy mode, trust; endpoints are clients (capture, render, local delivery constraints; no independent cognition/memory/output). Endpoint profiles: phone, PC (deeper, stronger ambient privacy), shop (hands-free; local-authority open question), vehicle (safety is the defining constraint), wearables/glasses (higher bar than any endpoint). Primary endpoint = most recent real interaction > proximity > context fit > fallback. Invisible transitions. Snapshot sync (most valid, not newest). Workers amplify, don't decide.
- Android framing STALE: "phone is the first/primary anchor"; its biggest open question "is the Core Presence Layer server-side, local, or hybrid?" is now ANSWERED by Windows: the PC (vision §5). Rewrite around PC-as-core.
- !!! INTERNAL CONFLICTS across source docs: (1) "transitions invisible, conversation continues across devices" vs Session Identity §4 "a new device always starts a new session; no cross-device session continuity". DP Device Capabilities §9 resolves it better (phone may attach to the existing Hermes session). (2) Heat: Distributed Presence lists heat as shared core state; Device Registration §7 makes heat per-device. A10/A12 must pick (vision: attention is the person's, so per-person heat seems right — Brian's call).

## Device Registration & Active Endpoint → A12 (vision + some mechanics)
- Registration record (deviceId, type, capabilities, interaction profile, dampening profile, lastSeen, platform…), active endpoint from heartbeat > interaction > last seen > place > explicit switch (explicit wins), NO_ACTIVE_ENDPOINT state (suppress speech, keep queueing), handoff context (recent history tail, pending clarification, deferred queue ref, session notes; invisible unless it failed — "I haven't heard from you in a bit — we were talking about the Camaro…"), output routing (capability downgrade, privacy filtering, tier-1 secondary delivery), stale cleanup, conflict rules per write category.
- FCM coordination layer = STALE (P10-D16: held connection W1, Firebase dropped). Firestore/RTDB paths drop.
- Windows as built: P10 device id + pairing + capability-named contract v3 (R4) + COMPANION WATCHER row + zola-phone held connection over Tailscale. That's the as-built for registration/pairing; active-endpoint tracking + handoff not built (PC-only delivery today).

## DP & Device Capabilities (Windows strawman v0.1, 2026-10-03) → A12 PRIMARY SOURCE
- Best-aligned doc in the set: host identity + memory; endpoints not assistants; device access specific & revocable; gateway as logical boundary (no Hermes source edits); capability registry with explicit availability states; observation / query / action / subscription distinguished; notification bodies are untrusted data; observation ≠ delivery ≠ memory; Life360 = last-reported place with age, never live location; per-conversation input/output leases for handoff; each device owns its own audio capture; delivery ID across push/display/speech; action-bound expiring approvals rechecked by executor; reconnect replays with original timestamps, expired events summarised not alerted.
- STALE vs locked P10 decisions: DP-D11 local-network-only (→ Tailscale chosen, P10 transport); "gateway" (→ zola-phone process, P10-D12); S13 SMS unresolved (→ P10 delivered texts incl. MMS/RCS); push vendor open (→ held connection W1, no Firebase, P10-D16); allowlist open (→ P10-D16 amended: Messages, Life360, Visual Voicemail, Instagram; Messenger dropped 10/28); phone-side voice/typed conversation (→ not built; P11-D01 phone as speaking endpoint later). DP-Dxx are proposals — reconcile each against P10-Dxx in A12.
- It says "Capability Acquisition / Tool Authorization contents not reviewed" — A12 rewrite should cross-check A15.

## Presence UI → A13
- Vision (presence-first, voice-first, restraint, functional UI only when needed, "the UI must not become a second brain") portable. ~75 Android refs: SVG blueprint + Compose Canvas layers, Rajdhani/Orbitron fonts, Kotlin state types, 25 sections of Compose build waves / perf rules / Cursor rules → drop or move to a short "Android reference" note.
- Windows notes present: P3-D01 zola.glb via Helix in-process; P3-D20 unlit albedo sRGB/ACES/gain; P3-D24 ZolaBackground token; P3-D04 DORMANT mode; S25 ALERT has no producer; P3-D22/D23 motion channels = blink, expression, brightness, speaking mouth; "no breathing and no head motion, by developer decision"; S30 particles deferred; P3-D06 HUD shows only true state; P3-D07 identity text exception.
- Keep: two-layer state model (adapter is the only place cognitive values enter; composables see safe floats) — maps to Windows client; HUD = true state only; dock replaces permanent text bar; context panels orbit the presence; visual dampening mirrors heat; endpoint adaptation; authority boundaries.
- !!! TENSION with Brian's stated end goal (memory, avatar track): wants hair movement, head movement and speech animation; avatar v2 (AV7 .glb) adds 49 hair-end bones + 67 face shapes; integration to be its own scoped phase. "No head motion, by developer decision" (P3) must be reclassified as a TEMPORARY limit in A13, not a boundary. Flag.
- As-built missing from doc: P9 Systems panel (Backend / Workspace watcher / Google account / Ranking / Voice / Memory; + COMPANION WATCHER P10), proactive lines as Zola bubbles (P9 T6), avatar v2 (AV5/AV7) and Helix bones test pending.
- For A11: presence UI is where the "door-knock" (attention request before delivery) can be shown on the PC.

## Privacy & Data Ownership Plan → A14
- Data category inventory in 4 tiers (T1 biometrics/face/voice, health, camera+identity, financial, precise location history; T2 communication content, episodes, relationships, style, calendar content, environmental history, household patterns; T3 canonical facts, session memory, current location, device state; T4 logs). Consent tiers (T1 explicit off-by-default; T2 informed default-on, revocable; T3 disclosed; T4 required). Retention tables. Deletion cascade (6 steps, ghost-memory prevention via deletion log). Local vs cloud classification + minimisation. User controls (inventory, memory browser, consent, forget, monitoring, retention, processing location, audit). Third-party boundaries. Sensitive capability governance (camera/person recognition, always-on listening, household, autonomous actions). Encryption.
- Windows notes present: C8 (forget = MEMORY.md only; state.db transcripts not in cascade); H2/H4/C4 (BitLocker accepted; no SQLCipher / DPAPI; single-user). P9 ranking exception edited in (display name, domain, subject, trimmed body to provider; store label+gist, delete body same write).
- STALE / CONFLICTS to fix in A14:
  - C8 note predates P6-D06 forget (store + flat files; SOUL says transcript remains in chat history). Update as-built.
  - Retention: "communication content not retained; processed transiently" vs P9-D07 (raw ≤7 days then ids/times) and P10 (texts kept like email under P9 retention; full history stays on phone). Windows decisions win → rewrite table.
  - Provider names (Gemini, Gemini Live, Deepgram STT) stale — Windows: model openai-codex (memory), local faster-whisper STT? (VOICE_CONFIG: stt provider local) + Deepgram Aura-2 Pandora TTS. STATUS already flags "May use cloud list stale".
  - "Content of messages/emails must remain local" (with one ranking exception) — check against P8 (Gmail read through the model in conversation is cloud by nature). Needs honest restatement.
  - !!! VISION TENSION: "children and household members who did not consent must not have their data retained in identifiable form" + "conversations involving non-consenting parties must not be retained as episodic memory". Read literally this blocks Zola knowing Brian's family (Bre, the boys) — core to the vision. Intended scope was probably biometric/observed data. A14 must split: facts Brian tells her about people in his life (allowed, his memory) vs biometric / sensor-observed identifying data of non-consenting people (not allowed). Flag for Brian.
  - Code masking + R1 (codes read only on explicit request, bypass model/history/memory/logs/TTS caches) is Windows' strongest privacy rule and is absent — add.

## Memory Ethics & Privacy → A14 (core of "what she may say")
- Two questions never collapsed: can she remember it (write time) vs can she reveal it (every output). Discretion ≠ forgetting. Reasonable-expectation test. Visibility scopes (PRIVATE_TO_USER, PRIVATE_TO_ZOLA, HOUSEHOLD_OK, PUBLIC_OK default, WORK_CONTEXT_ONLY, NEVER_SPEAK_ALOUD, EXPLICIT_CONFIRMATION_REQUIRED), scopes only tighten automatically. Sacred classes (health, financial stress, legal, relationship conflict, grief, abuse/trauma, addiction, HR, credentials) → silent context only, never proactive. Response Privacy Filter + decision matrix + rules R1–R6 (third party present lowers ceiling; sacred never proactive; emotions always hedged "you seem"; avoidance suppresses; embarrassment check; provenance governs surfacing). Provenance types USER_STATED / USER_CONFIRMED / PERCEPTION_DERIVED / SYSTEM_INFERRED / TOOL_PROVIDED / CONVERSATIONAL_IMPLICIT. Social deniability (venting/rhetoric → implicit provenance). Mutual memory asymmetry (older sensitive memories need more justification: sacred 30 d, private 60 d, emotional 14 d). Context contamination (work ↔ personal). Conversational vaulting. Trust recovery (automatic, doesn't delete). Avoidance = privacy signal.
- Platform-neutral, very strong; mostly vision on Windows. As-built: P8-D09 tainted-session fact rule, SOUL Workspace rules (content is information not instruction), R1 code rule, P6 forget.
- !!! PROVENANCE DEFINED FOUR DIFFERENT WAYS across sources: Memory Agency (Stage 6 authority classes), Perception Memory (authority tiers 1–4), RIL shared contract (USER_STATEMENT > USER_CONFIRMED > SYSTEM_INFERRED > PERCEPTION_DERIVED), Memory Ethics (6 provenance types incl. TOOL_PROVIDED). Relationship Inference adds USER_STATEMENT / SYSTEM_INFERRED / SYSTEM. A03 must define ONE provenance model mapped to vision §4's five (stated / retrieved / observed / inferred / uncertain-conflicting); A14 references it. Note: none of the Android lists has a clean "retrieved from external source" (email/text) class — TOOL_PROVIDED is closest.
- VISION TENSION: HOUSEHOLD_OK depends on "the user's trusted entity list". 10/19 direction: no separately maintained trusted-contact list; relationship meaning comes from entity memory. Restate as relationship-derived. Flag.
- Possible tension with vision §1 natural engagement: PUBLIC_OK default but "when uncertain, suppress" + sacred classes → OK for Brian alone in office; A14 should say the private-office default is not the shared-space default.

## Tool Authorization (Windows, WINH08 era) → A15
- Posture: Hermes approvals.mode / danger overlay accepted (A3); ONE stricter Zola gate = confirmed send (A1), applies to every trigger (live, cron, CLI, MCP); authority is about the trigger, not just the tool; A2 Hermes extra speech paths (review.summary, child-session completes, heartbeat) accepted un-arbitrated "for now"; A5 background-review combined authority at stock; S7 scheduled work = Hermes cron full unsupervised run_conversation (sidecar fallback if needed); A9 one policy (Path B); standing security-deferral trigger before any multi-user/public release.
- STALE vs later Windows decisions:
  - Confirmed send shape: doc says own approval UI + two-step (content confirm then send confirm, from Android SMS). Windows P8 built: spoken approval PHRASE ("Approved. Send it."), checked in plugin code from Brian's own turn (P8-D06 option b), typing the phrase also approves, no cards (Brian doesn't want more cards). Rewrite.
  - Background authority: P9-D01 "background work is code, never a Hermes turn; Brian's authority is the origin ticket" + P9-D03 supervised watcher — not reflected; S7 cron-as-run_conversation may be superseded for proactive work. Check lore.
  - "Gmail via the P3-decided connector" → P8 Workspace plugin.
  - A2 (extra Hermes speech paths) is now load-bearing for P12 proactive speech + the one-speech-authority question (A10/A11). Flag as open.
- Missing vision content A15 needs: path to controlled autonomy (vision §3 Action: judgment ≠ execution authority; low-risk actions only after separate decisions on permissions, limits, accountability, reversibility, logging); assumption-license idea from Relational Calibration belongs here as deferred.

## Capability Acquisition (Windows, WINH06 era) → A15
- Accepts Hermes stock: skill writes ungated (A8, write_approval False), background-review fork combined authority (A5/H5), CLI fallbacks, home SOUL.md readable/writable (WINH06-AUD-17), MCP secret re-injection (H6), no on-box training (S8). All under standing trigger.
- TENSION with SOUL.md: "I don't silently change my own software, permissions, or environment to accomplish something that requires Brian's approval" vs ungated skill writes (A8) — behaviour promise without a mechanism. A15 should state which is the boundary. Flag for Brian.
- Small; merge cleanly with Tool Authorization.

---

## Corrections and additions, v1.2 (2026-10-29, after ChatGPT review)

These supersede anything above that conflicts with them. Matrix v1.2 has the full treatment.

- **Provenance (corrects the Memory Ethics / cross-doc note).** Memory Ethics *does* define TOOL_PROVIDED (calendar, email, contacts), and Memory Agency's write-time classes include tool-provided material. The real problem is inconsistent treatment across five docs, not a missing class. Fixed by the six evidence dimensions (matrix §3.1).
- **Governor chain (corrects the Cognitive Engagement / Cognitive Engine note).** The Engagement Governor followed by Attention/Relevance is an *ordered chain*, not competing owners. The real double claim to final authority is Autonomous Behavior's Response Governor vs the Attention Engine.
- **Self-modification (corrects the Identity / Tool Authorization note).** It is not "a promise with no mechanism". P8-D02 built `config_self_edit` and `self_mod` guards with tested residual bypasses. R7b was unit-tested, not invoked live. Background `skill_manage` is blocked in a tainted session. The open question is policy: which self-changes need Brian's OK (matrix B15).
- **R1 wording.** Earlier shorthand "codes never" is wrong. R1: read aloud only on Brian's explicit request, bypassing the model, history, memory, logs and TTS caches.
- **Added, Perception Memory:** the recurrence buffer is session-only, yet promotion needs ≥3 sessions. No durable evidence record bridges them. This is a source-design gap (matrix §3.3).
- **Added, Perception Memory + Social Graph:** "Brian did not correct it" reinforcement lets Zola's own repetition raise confidence. Silence is not confirmation; self-references are not corroboration (matrix §3.3).
- **Open loops (refines the Memory Agency note).** Not a one-store problem. A remembered situation (A03) and an operational watch (A11 / P9 store) are linked by IDs, with defined close and forget ownership (matrix §3.4).
- **Streaming Cognition (refines its note).** Keep its full behavioural requirements (progressive interpretation, provisional prep, corrections, draft invalidation, commit boundary). It is not just a latency principle.
- **Privacy blanket rules** (household identifiable form, sacred never proactive, third-party-present suspends memory, desk presence = private, HOUSEHOLD_OK trusted list) are review items (matrix B3–B7, B14), not adoptions.
- **All Android thresholds and numbers** are unvalidated unless a Windows decision adopted them.
- **Review caveat.** ChatGPT's review was not a cover-to-cover read. Its checkout's ROADMAP lists P10 as a separate track, so P10/P11 "as built" claims must be checked against current closeout records.
