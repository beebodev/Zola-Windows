# Zola WINH Hermes Gap Analysis — Progress

Shared across the entire WINH series (WINH01–12 + WINH00). Later prompts extend this file; they must not replace the Hermes pin recorded here.

## Hermes pin (set once by WINH01 — do not change)

- Release tag: `v2026.9.14`
- Marketing version: Hermes Agent v0.21.3 (`pyproject.toml` `[project].version = "0.21.3"`)
- Commit SHA: `345cd2b057a452236de401d3534b8502a7465e8d`
- Annotated tag object: `7a963716b81be13ba513d4f127633b7da493aff2` (type `tag`; peels to the commit above)
- Tag creator date (local git): 2026-09-14 09:04:09 -0700
- GitHub release published: 2026-09-14T16:04:14Z
- GitHub release flags: `draft: false`, `prerelease: false` (confirmed via `https://api.github.com/repos/NousResearch/hermes-agent/releases/latest`)
- Clone path (external, not in this repo): `C:\Users\test\Dev\hermes-agent`
- Checkout state: detached HEAD at `v2026.9.14`

### Five most recent local tags (by `git tag --sort=-creatordate`)

1. `v2026.9.14` — 2026-09-14 09:04:09 -0700 — Hermes Agent v0.21.3 (v2026.9.14)
2. `v2026.9.11` — 2026-09-11 12:20:28 -0700 — Hermes Agent v0.21.2 (v2026.9.11) — The state.db Patch Release
3. `v2026.9.7` — 2026-09-07 15:16:56 -0700 — Hermes Agent v0.21.1 (2026.9.7)
4. `v2026.8.31` — 2026-08-31 12:29:39 -0700 — Hermes Agent v0.21.0 (2026.8.31)
5. `v2026.8.27` — 2026-08-27 05:06:48 -0700 — Hermes Agent v0.20.6 (2026.8.27)

Cross-check: GitHub Releases list and `/releases/latest` both name `v2026.9.14` as the latest published non-prerelease. The series audits this tag, not `main` (`main` at clone time was `bb359ec5c1d5da6a66f00ee11f0ad7a86defaee2`).

## Zola-Windows branch

- Shared branch: `winh-hermes-audit`
- Created from: `main` at `4ff1abf2cf20c4a1bdcdb59ea99fd8eaabb66cb3`
- Output directory: `zola-architecture/audit/winh-hermes-gap/`

WINH01 setup note: this workspace had no `.git` when the prompt started. `main` was initialized with the existing `zola-architecture/` documents (clean tree), then `winh-hermes-audit` was created from that `main`. The sibling path `C:\Users\test\Dev\hermes-agent` existed as an empty directory and was cloned from `https://github.com/NousResearch/hermes-agent` (not added as a submodule, not copied into this repo).

## Series phase table

- WINH01 — Setup, Repo Map, Native Windows Runtime — COMPLETE
- WINH02 — Hermes Integration Surface Inventory & Desktop Reference Architecture — COMPLETE
- WINH03 — Integration Request Trace & Operational Contract — COMPLETE
- WINH04 — Memory & Skills — COMPLETE
- WINH05 — Identity, Personality & Self-Model — COMPLETE — commit `3ef603f467366375e4eefa00a0b58cd2a792b82d`
- WINH06 — Self-Improvement & Capability Acquisition — COMPLETE — commit `a62b0fff322df572581d062d5297578346deefce`
- WINH07 — Authority, Governance & Routing — COMPLETE — commit `935aaba0f7ee0950f9f4479076abe1b9451f68ff`
- WINH08 — Tool Calling, Subagents & Scheduled Automation — COMPLETE — commit `a071ea807100afa42bafba36031a6070f3626542`
- WINH09 — Voice Pipeline & Voice Identity — COMPLETE — commit `463667f4d3782dd3b23bb5c2362a5e088987aa5d`
- WINH10 — Messaging Surfaces — COMPLETE — commit `b946ad0b630540bb935aa805db28a0518b2319f7`
- WINH11 — Windows Security & Deployment — COMPLETE — commit `da6bf40f5b3f89c9b5337d4b29b933e16872079a`
- WINH12 — Relational Intelligence & Model Provider Flexibility — COMPLETE — commit `d01ddefb59dd15040d4f178efc732fb864bf8d8b`
- WINH00 — Synthesis + Closeout — PENDING

WINH00 is the only prompt that merges or closes the branch.

## Recorded scope decisions

> Environmental Awareness / Perception (Zola Environmental Awareness Architecture, Zola Environmental Perception Architecture, Zola_Architecture_Environmental_Event_Bus_and_User_State_Model, Zola_Architecture_Perceptual_Input_Layer, Zola_Architecture_Context_Injection, Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking) is out of scope for the entire WINH series, decided 2026-09-21 — treated like the 3D avatar (WINH01's Explicitly Out of Scope): will be assessed separately outside this audit, not audited against Hermes here.

> Zola-Windows is a fresh-start implementation, not a port of zola-main, decided 2026-09-21. The `zola-architecture/` documents are read as a capability/requirements guide, not an implementation spec — an Android-specific implementation choice (a named library, OS API, or hardware component) is never itself a finding against Hermes; only the underlying capability requirement is. This applies to the whole WINH series, past and future phases alike.

> `Zola_Cognitive_Engine_Architecture.md` (the `CognitivePrepWorker` "Prep Kitchen Model," a durable persisted initiative queue, curiosity-derived triggering, and three named cognitive engines routing through the existing authority chain) is out of scope for the entire WINH series, decided 2026-09-21. This document describes background/between-session proactive cognition, distinct from the real-time conversational pipeline this phase audits (Master Plan §3). Hermes has adjacent primitives — a real cron scheduler, heartbeat/loop idle triggers, and the WINH06 background-review post-turn fork — but not this specific pattern; that absence is already covered by existing findings (no Agent-14-style priority tiers, no unified schedule inventory — `WINH06-AUD-14`, `WINH08-AUD-12`) rather than re-derived as a new finding here. Will be assessed separately outside this audit series, not audited against Hermes as its own phase.

WINH04 Document-of-Truth check: all six listed `zola-architecture/` files are present. `Zola_Master_State_Audit.md` is absent from disk (working tree shows it deleted vs HEAD; not restored). Memory-agency exception (entity-vs-user ownership and who holds write authority) is recorded here as superseded for this track — it is not raised as `[GAP]`/`[RISK]`. Retention, deletion, sensitivity, access control, and integrity are **not** exempted.

## Guardrails (entire series)

- G-SCOPE: Diagnostic audit only. Read Hermes at `C:\Users\test\Dev\hermes-agent` (pinned tag) and the Zola-Windows documents listed in each prompt. Produce findings only under `zola-architecture/audit/winh-hermes-gap/`.
- G-NOCHANGE: Zero source modifications in Hermes. Zero modifications in Zola-Windows outside this output directory.
- G-QUALITY: Every finding names a specific file, directory, function, config key, or line in tag `v2026.9.14`. If docs and code conflict, report both.
- G-CLOSEOUT: Deferred to WINH00. This series does not merge, push a final state, or delete the branch until WINH00.

## Repo map (WINH01 Phase 2)

Later prompts should start here:

- [Zola_WINH01_Audit_01_RepoMap.md](./Zola_WINH01_Audit_01_RepoMap.md)

Windows runtime findings:

- [Zola_WINH01_Audit_02_WindowsRuntime.md](./Zola_WINH01_Audit_02_WindowsRuntime.md)

## Integration surfaces (WINH02 Phase 2–4)

- [Zola_WINH02_Audit_01_SurfaceInventory.md](./Zola_WINH02_Audit_01_SurfaceInventory.md)
- [Zola_WINH02_Audit_02_DesktopReference.md](./Zola_WINH02_Audit_02_DesktopReference.md)
- [Zola_WINH02_Audit_03_PreliminaryPaths.md](./Zola_WINH02_Audit_03_PreliminaryPaths.md)

WINH02 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (matches the pin above). No re-clone, no new branch, no re-pin.

Preliminary paths named for WINH00 (no decision in this prompt): (a) fork/re-theme `apps/desktop`; (b) fresh native Windows client against the JSON-RPC/WebSocket gateway; (c) client against the OpenAI-compatible HTTP API only; (d) ACP stdio adapter (IDE-shaped, not a standalone Windows shell).

## Operational contract (WINH03 Phase 2–7)

- [Zola_WINH03_Audit_01_ProcessModel.md](./Zola_WINH03_Audit_01_ProcessModel.md)
- [Zola_WINH03_Audit_02_RequestTrace.md](./Zola_WINH03_Audit_02_RequestTrace.md)
- [Zola_WINH03_Audit_03_DisconnectReconciliation.md](./Zola_WINH03_Audit_03_DisconnectReconciliation.md)
- [Zola_WINH03_Audit_04_SessionDurability.md](./Zola_WINH03_Audit_04_SessionDurability.md)
- [Zola_WINH03_Audit_05_MinimumClientCapabilities.md](./Zola_WINH03_Audit_05_MinimumClientCapabilities.md)
- [Zola_WINH03_Audit_06_Synthesis.md](./Zola_WINH03_Audit_06_Synthesis.md)

WINH03 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match). Process model: Path B (`hermes serve`) and Path C (`hermes gateway` + API server) cannot share one spawned process. Disconnect/fail-closed: Surface 3 default is fail-open for healthy detached turns (20s grace, 600s activity freshness); Surface 1 SSE interrupt remains fail-closed.

## Memory & skills (WINH04 Phase 2–6)

- [Zola_WINH04_Audit_01_StorageOwnership.md](./Zola_WINH04_Audit_01_StorageOwnership.md)
- [Zola_WINH04_Audit_02_PrivacyRetentionAccess.md](./Zola_WINH04_Audit_02_PrivacyRetentionAccess.md)
- [Zola_WINH04_Audit_03_Skills.md](./Zola_WINH04_Audit_03_Skills.md)
- [Zola_WINH04_Audit_04_HierarchyReconciliation.md](./Zola_WINH04_Audit_04_HierarchyReconciliation.md)
- [Zola_WINH04_Audit_05_Synthesis.md](./Zola_WINH04_Audit_05_Synthesis.md)

WINH04 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match). Default Hermes memory is profile-scoped MEMORY.md/USER.md plus `state.db` transcripts plus at most one optional provider. Retention, sacred-category sensitivity, visibility scopes, instance-wide access, and fact-memory audit trail are `[GAP]`s not covered by the memory-agency exception. Skills are a separate backend; agent `skill_manage` is ungated by default.

## Identity, personality, self-model, session identity (WINH05 Phase 2–6)

- [Zola_WINH05_Audit_02_IdentityPersonalityFramework.md](./Zola_WINH05_Audit_02_IdentityPersonalityFramework.md)
- [Zola_WINH05_Audit_03_IdentitySourceConsolidation.md](./Zola_WINH05_Audit_03_IdentitySourceConsolidation.md)
- [Zola_WINH05_Audit_04_SelfModelAwareness.md](./Zola_WINH05_Audit_04_SelfModelAwareness.md)
- [Zola_WINH05_Audit_05_SessionIdentity.md](./Zola_WINH05_Audit_05_SessionIdentity.md)
- [Zola_WINH05_Audit_06_Synthesis.md](./Zola_WINH05_Audit_06_Synthesis.md)

WINH05 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match). Branch HEAD at start of WINH05: `5637a6956a303794f22f01018e5e3f696b3f6a2e` (`winh-hermes-audit`). SOUL.md is configurable identity text, not a locked seed; no Style Profile / SMA layer; `state.db` `sessions` is wrap-able but not a single-mint `SessionRecord`. Lore files are out of scope for this audit (none on disk in this track).

## Self-improvement & capability acquisition (WINH06 Phase 2–6)

Exploratory inventory — **no Zola Document of Truth** for this domain. Labels are `[MECHANISM]` / `[RISK]` / `[ABSENT]` / `[UNVERIFIED]` (not MATCH/GAP/PARTIAL).

- [Zola_WINH06_Audit_02_SkillSelfAuthoring.md](./Zola_WINH06_Audit_02_SkillSelfAuthoring.md)
- [Zola_WINH06_Audit_03_ToolPluginAcquisition.md](./Zola_WINH06_Audit_03_ToolPluginAcquisition.md)
- [Zola_WINH06_Audit_04_SelfDirectedConfigModification.md](./Zola_WINH06_Audit_04_SelfDirectedConfigModification.md)
- [Zola_WINH06_Audit_05_LearningAdaptation.md](./Zola_WINH06_Audit_05_LearningAdaptation.md)
- [Zola_WINH06_Audit_06_Synthesis.md](./Zola_WINH06_Audit_06_Synthesis.md)

WINH06 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match, tag `v2026.9.14`). Branch HEAD at start of WINH06: `5637a6956a303794f22f01018e5e3f696b3f6a2e` (`winh-hermes-audit`). No bundled training loop; skill authoring and background-review writes are ungated by default; `$HERMES_HOME/SOUL.md` is writable via `write_file` (home exempt from the project-local always-ask); desktop MCP setup is a consent card, terminal CLI is the fallback. 25 findings (9 HIGH, 12 MEDIUM, 4 LOW).

## Authority, governance & routing (WINH07 Phase 2–6)

Document of Truth: Master Architecture Plan §20 (Centralized Authority Model), Core Architectural Principles (Single Authority Ownership, Truth Ownership Rule, Speech Authority Constraint, Provider Abstraction), §13 Trust/Permission/Privacy, and `Zola_Agent_Map.md` Core Rule. **Not scored:** §9/9a (series environmental-scope decision) and §12 (reserved for WINH09). Cross-refs only: WINH02 surfaces, `WINH03-AUD-03/05/08`, `WINH04-AUD-02/03`, `WINH06-AUD-02/07/08/14/23/25`.

- [Zola_WINH07_Audit_02_ResponseAuthority.md](./Zola_WINH07_Audit_02_ResponseAuthority.md)
- [Zola_WINH07_Audit_03_TrustPermissionFramework.md](./Zola_WINH07_Audit_03_TrustPermissionFramework.md)
- [Zola_WINH07_Audit_04_RoutingAuthority.md](./Zola_WINH07_Audit_04_RoutingAuthority.md)
- [Zola_WINH07_Audit_05_TruthSpeechSeparation.md](./Zola_WINH07_Audit_05_TruthSpeechSeparation.md)
- [Zola_WINH07_Audit_06_Synthesis.md](./Zola_WINH07_Audit_06_Synthesis.md)

WINH07 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match, tag `v2026.9.14`). Branch HEAD at start of WINH07: `a62b0fff322df572581d062d5297578346deefce` (`winh-hermes-audit`). No Response Governor / named core; `review.summary` is a second user-facing emit from the WINH06 background-review fork; six WINH02 surfaces route independently except dashboard+JSON-RPC sharing `tui_gateway.dispatch`; no reasoning/speech split. 15 findings (8 HIGH, 7 MEDIUM, 0 LOW).

## Tool calling, subagents & scheduled automation (WINH08 Phase 2–6)

Document of Truth: `Zola_Agent_Map.md` (Core Rule, per-agent Must-never, staleness/TTL/confidence, Agent 8 / 14 / 15). Tool-calling held only to the Core Rule line and Agent 8's "must never bypass the tool authorization pipeline / pre-execute confirmation-gated tools." Not re-derived: WINH06 acquisition, WINH07 speech/routing, WINH04 memory-write (`WINH04-AUD-02`).

- [Zola_WINH08_Audit_02_SubagentArchitecture.md](./Zola_WINH08_Audit_02_SubagentArchitecture.md)
- [Zola_WINH08_Audit_03_ToolCallAuthorization.md](./Zola_WINH08_Audit_03_ToolCallAuthorization.md)
- [Zola_WINH08_Audit_04_ScheduledAutomation.md](./Zola_WINH08_Audit_04_ScheduledAutomation.md)
- [Zola_WINH08_Audit_05_SpeculativeExecutionSafety.md](./Zola_WINH08_Audit_05_SpeculativeExecutionSafety.md)
- [Zola_WINH08_Audit_06_Synthesis.md](./Zola_WINH08_Audit_06_Synthesis.md)

WINH08 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match, tag `v2026.9.14`). Branch HEAD at start of WINH08: `935aaba0f7ee0950f9f4479076abe1b9451f68ff` (`winh-hermes-audit`). Subagents/review/cron/heartbeat invoke tools off the live turn; no Agent 8 warm-start; cron is a real scheduler (`~/.hermes/cron/jobs.json`, 60s ticker). 14 findings (2 HIGH, 9 MEDIUM, 3 LOW).

## Voice pipeline & voice identity (WINH09 Phase 2–6)

Document of Truth: Master Plan §3 Current Sequential Model only (not Long-Term Streaming), §12 Conversational Attention Authority (reserved from WINH07), External API Strategy Tier 1, `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` (capability requirements, not Android libraries). Not scored: Long-Term Streaming, §9/9a, camera identity, cloud voiceprint sync, post-session diarization, barge-in mechanics.

- [Zola_WINH09_Audit_02_VoiceProviderLandscape.md](./Zola_WINH09_Audit_02_VoiceProviderLandscape.md)
- [Zola_WINH09_Audit_03_VoicePipelineArchitecture.md](./Zola_WINH09_Audit_03_VoicePipelineArchitecture.md)
- [Zola_WINH09_Audit_04_VoiceIdentity.md](./Zola_WINH09_Audit_04_VoiceIdentity.md)
- [Zola_WINH09_Audit_05_ConversationalAttentionAuthority.md](./Zola_WINH09_Audit_05_ConversationalAttentionAuthority.md)
- [Zola_WINH09_Audit_06_Synthesis.md](./Zola_WINH09_Audit_06_Synthesis.md)

WINH09 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match, tag `v2026.9.14`). Branch HEAD at start of WINH09: `a071ea807100afa42bafba36031a6070f3626542` (`winh-hermes-audit`). Hermes covers ElevenLabs TTS/STT natively; Cartesia/Deepgram are not built-ins; Gemini Live is not GPT-Live. Chained voice is STT → client `prompt.submit` → TTS. No speaker-identity tracker. Wake-word is the primary attention gate, not directed-speech. 16 findings (3 HIGH, 12 MEDIUM, 1 LOW).

## Messaging surfaces (WINH10 Phase 2–6)

Document of Truth: `Zola_Communication_Intelligence_Architecture.md` (email + SMS intelligence, shared principles), `Zola_Sms_Intelligence_Architecture.md` (contact-gate, thread velocity, Send Is Confirmed). Capability-not-Android-impl. Windows has no cellular radio (platform constraint, not a Hermes miss). Cross-refs: `WINH04-AUD-02`/`06`, `WINH07-AUD-07`, `WINH08-AUD-02`/`06`.

- [Zola_WINH10_Audit_02_InboundIntelligence.md](./Zola_WINH10_Audit_02_InboundIntelligence.md)
- [Zola_WINH10_Audit_03_ConfirmedSendFlow.md](./Zola_WINH10_Audit_03_ConfirmedSendFlow.md)
- [Zola_WINH10_Audit_04_ChannelCoverage.md](./Zola_WINH10_Audit_04_ChannelCoverage.md)
- [Zola_WINH10_Audit_05_CrossReference.md](./Zola_WINH10_Audit_05_CrossReference.md)
- [Zola_WINH10_Audit_06_Synthesis.md](./Zola_WINH10_Audit_06_Synthesis.md)

WINH10 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match, tag `v2026.9.14`). Branch HEAD at start of WINH10: `463667f4d3782dd3b23bb5c2362a5e088987aa5d` (`winh-hermes-audit`). Pre-audit “no SMS/Twilio in tools/” was incomplete: Twilio SMS and IMAP/SMTP email are `plugins/platforms/sms` and `email`. `send_message` is not model-callable; live gateway replies still send autonomously. No SmsSignal/EmailSignal pipeline. 12 findings (3 HIGH, 6 MEDIUM, 2 LOW, 1 OBSERVATION).

## Windows security & deployment (WINH11 Phase 2–6)

Document of Truth: Privacy Plan §9 Encryption/Storage/Access (core); §7 Provider Abstraction privacy line (credentials only, not swapability); §6 auth-before-data-management sentence lives at §9 L535. Master Plan §13 cited via `WINH07-AUD-05`–`08`, not re-derived. Half B: no dedicated Zola deployment doc — inventory labels (`[MECHANISM]`/`[RISK]`/`[ABSENT]`/`[UNVERIFIED]`) per WINH06. Distributed Presence E2E out of series. Do not re-audit WINH01 CLI install, WINH02-AUD-04 session token (cite), WINH07/08 approvals.

- [Zola_WINH11_Audit_02_SecretsStorage.md](./Zola_WINH11_Audit_02_SecretsStorage.md)
- [Zola_WINH11_Audit_03_TransitAndThirdParty.md](./Zola_WINH11_Audit_03_TransitAndThirdParty.md)
- [Zola_WINH11_Audit_04_DesktopBuildAndUpdate.md](./Zola_WINH11_Audit_04_DesktopBuildAndUpdate.md)
- [Zola_WINH11_Audit_05_ProcessPosture.md](./Zola_WINH11_Audit_05_ProcessPosture.md)
- [Zola_WINH11_Audit_06_Synthesis.md](./Zola_WINH11_Audit_06_Synthesis.md)

WINH11 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match, tag `v2026.9.14`). Branch HEAD at start of WINH11: `b946ad0b630540bb935aa805db28a0518b2319f7` (`winh-hermes-audit`). Recorded scope decisions still present (fresh-start, Cognitive Engine exclusion, Environmental Awareness). Pre-audit claims verified: `signAndEditExecutable: false` plus `install.ps1` CSC disabled (unsigned Windows, not CI-signed); NSIS `perMachine: false` / `oneClick: false`; custom `windows.ps1` → `hermes update` (not electron-updater); `.env` plaintext, vault Fernet with co-located key, `state.db` plain `sqlite3.connect`. 22 findings (7 HIGH, 10 MEDIUM, 5 LOW).

## Relational intelligence & model provider flexibility (WINH12 Phase 2–6)

Document of Truth: `Zola_Relational_Intelligence_Layer_Architecture.md` plus Temporal, Social Graph, Continuity, Calibration. SMA cited `WINH05-AUD-10`–`13` (not re-read). Half B: Master Plan Provider Abstraction + Tier 1 Conversational Models (Gemini / OpenAI / Anthropic / local). Capability-not-Android-impl. Cognitive Engine and Environmental Awareness still excluded.

- [Zola_WINH12_Audit_02_TemporalFoundation.md](./Zola_WINH12_Audit_02_TemporalFoundation.md)
- [Zola_WINH12_Audit_03_SocialGraphReasoning.md](./Zola_WINH12_Audit_03_SocialGraphReasoning.md)
- [Zola_WINH12_Audit_04_ContinuityAndCalibration.md](./Zola_WINH12_Audit_04_ContinuityAndCalibration.md)
- [Zola_WINH12_Audit_05_ModelProviderFlexibility.md](./Zola_WINH12_Audit_05_ModelProviderFlexibility.md)
- [Zola_WINH12_Audit_06_Synthesis.md](./Zola_WINH12_Audit_06_Synthesis.md)

WINH12 Hermes pin re-check: `git rev-parse HEAD` at `C:\Users\test\Dev\hermes-agent` = `345cd2b057a452236de401d3534b8502a7465e8d` (match, tag `v2026.9.14`). Branch HEAD at start of WINH12: `cc97edac74275dff1a9f67b6d0c509fc89944d04` (`winh-hermes-audit`). Recorded scope decisions still present. Half A is near-total `[GAP]` (RIL is scratch). Half B is `[MATCH]` (multi-vendor + local + live `/model`). 17 findings (10 HIGH, 7 MEDIUM, 0 LOW).

## Running findings list

- WINH01-AUD-01 — [PARTIAL] — MEDIUM — `README.md` L43-45; `website/docs/user-guide/windows-native.md` L85-102 — Native Windows is a first-class install path, but the project's own feature matrix does not claim full Linux/macOS parity.
- WINH01-AUD-02 — [GAP] — HIGH — `tools/lazy_deps.py` `_unsupported_feature_reason` L341-343; `pyproject.toml` L387-392 — Matrix E2EE (`python-olm`) is explicitly unsupported on native Windows; docs tell users to use WSL.
- WINH01-AUD-03 — [RISK] — MEDIUM — `website/docs/user-guide/windows-native.md` L99-102 vs `hermes_cli/web_server_chat.py` L26-33 and `hermes_cli/win_pty_bridge.py` — Dashboard `/chat` docs still say POSIX-PTY / WSL-only; this tag ships a ConPTY `WinPtyBridge`. Docs and code conflict.
- WINH01-AUD-04 — [RISK] — MEDIUM — `.github/workflows/tests.yml`; `.github/workflows/tests-os.yml`; `.github/workflows/ci.yaml` L73-92 — Default pytest suite is Linux-only. Windows CI runs only `@pytest.mark.windows_only` tests, not the full suite.
- WINH01-AUD-05 — [RISK] — MEDIUM — `.github/workflows/ci.yaml` L123-139; `.github/workflows/e2e-desktop.yml` L18-23 — Desktop Playwright E2E is Linux-only and currently hard-disabled (`if: false`).
- WINH01-AUD-06 — [GAP] — LOW — `native/fts5_cjk/build.sh` L1-19 — CJK FTS5 tokenizer builds a `.so` with `gcc`; no Windows/MSVC path in this tag.
- WINH01-AUD-07 — [PARTIAL] — MEDIUM — `tools/environments/local.py` `_find_bash` / `_windows_bash_candidates` L364-413 — Native Windows shell execution goes through Git Bash (`bash.exe`), not cmd/PowerShell; documented as the POSIX-compat strategy.
- WINH01-AUD-08 — [MATCH] — LOW — `scripts/install.ps1`; `pyproject.toml` L19-141; `website/docs/user-guide/windows-native.md` L66-79 — Default native install is `uv` plus CPython 3.11 wheels plus PortableGit/Node; no Visual Studio Build Tools required for the core path.
- WINH01-AUD-09 — [RISK] — LOW — `tests/install/KNOWN_FAILURES.md` — No in-repo `KNOWN_ISSUES.md`. The only tracked Windows issues file is historical installer/updater known-failures, not live bugs.
- WINH02-AUD-01 — [MATCH] — MEDIUM — `tui_gateway/server.py` L85; `tui_gateway/AGENTS.md` L19–30, L53–57; `apps/desktop/src/api/client.ts` L28–37 — JSON-RPC gateway is the only surface that already carries the full first-party agent-loop contract and is exercised by Desktop, TUI, and dashboard `/api/ws`.
- WINH02-AUD-02 — [RISK] — HIGH — `tui_gateway/AGENTS.md` L1–4; `apps/shared/package.json` L2–4 (`version: 0.0.0`); `apps/shared/src/gateway-contract.openrpc.json` L3–5 (`version: "1"`); `gateway-contract.generated.ts` L1–3 — internal, generated, un-semvered contract. A packaged Zola client cannot detect a breaking Hermes update from version numbers alone.
- WINH02-AUD-03 — [PARTIAL] — MEDIUM — `gateway/platforms/api_server.py` L1–6; `website/docs/user-guide/features/api-server.md` L7–9, L109–112; `api_server_openai_routes.py` L668; `api_server_runs.py` L862–883 — public OpenAI-compatible API with streaming, tool progress, and stop; missing the first-party RPC catalog Desktop actually uses.
- WINH02-AUD-04 — [PARTIAL] / [GAP] / [RISK] — MEDIUM — `hermes_cli/web_routers/chat_ws.py` L555–574; `hermes_cli/web_server_chat.py` L26–28; `hermes_cli/web_server.py` L304–311 — dashboard hosts Surface 3 at `/api/ws` and a PTY embed at `/api/pty`; session token is process-ephemeral.
- WINH02-AUD-05 — [PARTIAL] / [GAP] — MEDIUM — `acp_adapter/server.py` L1, L613–628; `website/docs/user-guide/features/acp.md`; `website/docs/reference/toolsets-reference.md` L97 — public ACP stdio for IDEs; `hermes-acp` toolset drops cron and other product tools; not a Windows desktop product surface.
- WINH02-AUD-06 — [GAP] — LOW — `mcp_serve.py` L1–7, L309–314, L721 — MCP messaging-conversation bridge, not an agent chat loop.
- WINH02-AUD-07 — [GAP] — LOW — `gateway/platforms/webhook.py` L1–3, L154, L198–224 — inbound HMAC webhook receiver; Zola cannot call into it as a client.
- WINH02-AUD-08 — [MATCH] — MEDIUM — `apps/desktop/src/api/client.ts` L28–37; `apps/desktop/README.md` L101–103; `apps/desktop/src/AGENTS.md` L6–10 — official Desktop uses Surface 3 JSON-RPC over `/api/ws` via `JsonRpcGatewayClient`.
- WINH02-AUD-09 — [MATCH] / [PARTIAL] — MEDIUM — `apps/desktop/electron/backend-command.ts` L18–21; `apps/desktop/electron/main.ts` L1418–1428; README L90–138 — Desktop launches a `hermes serve` sidecar and can instead attach to a remote/existing gateway.
- WINH02-AUD-10 — [PARTIAL] — MEDIUM — `apps/shared/src/json-rpc-gateway.ts` L27, L121–127, L142; `apps/shared/src/reconnect-backoff.ts`; `tui_gateway/session_lifecycle.py` L380–394, L568–594 — reconnect/replay exist; mid-turn disconnect interrupt is deferred.
- WINH02-AUD-11 — [PARTIAL] — MEDIUM — `LICENSE` (MIT); `apps/desktop/package.json` L2–7; `apps/desktop/src/i18n/en.ts` L3286, L3309; `apps/shared/` vs `apps/desktop/src/` — transport is separable; UI/i18n/productName are Hermes-coupled.
- WINH02-AUD-12 — [RISK] — MEDIUM — `api_server_openai_routes.py` L697–698 vs `tui_gateway/session_lifecycle.py` L380–394, L568–594 — SSE disconnect fail-closes (interrupt); JSON-RPC `client_gone` defers interrupt. Two surfaces disagree on who owns a mid-turn disconnect. Restated with mechanism in WINH03-AUD-05 / WINH03-AUD-08.
- WINH03-AUD-01 — [GAP] — MEDIUM — `hermes_cli/subcommands/dashboard.py` L48–59; `hermes_cli/main.py` `cmd_dashboard` L2543–2590 / `cmd_gateway` L1769–1775; `web_server.py` `start_server` L1365–1385 (no API_SERVER); `gateway/run.py` `start_gateway` L5195 — `hermes serve` does not start the OpenAI API; `hermes gateway` does not bind `/api/ws`. Path B and Path C cannot share one spawned process.
- WINH03-AUD-02 — [MATCH] — LOW — `tui_gateway/methods_prompt.py` L544–662; `prompt_turn.py` `_run_prompt_submit` / `_invoke_agent`; `conversation_loop.py` `run_conversation` L1573; `turn_api_call.py` `perform_api_call` L61; `turn_tool_round.py` `run_tool_round` L45; `run_agent.py` `_execute_tool_calls` L1273 — one JSON-RPC turn traced as a named-function chain.
- WINH03-AUD-03 — [MATCH] — LOW — `prompt_turn.py` `_complete_turn_payload` L634–651 / emit L848; `tui_gateway/contracts/events.py` L164–184 — `message.complete` carries full `text` plus `usage`/`status`, not a bare done signal.
- WINH03-AUD-04 — [PARTIAL] — MEDIUM — `tui_gateway/server.py` `_emit_approval_request` L709–732; `approval_context.py` `_get_approval_timeout` L239–248 — approval blocks the turn thread on the queue (default 300s); JSON-RPC dispatcher can still read `session.interrupt`.
- WINH03-AUD-05 — [RISK] — HIGH — `tui_gateway/server.py` L122–140 (grace default 20s, activity stale default 600s); `session_lifecycle.py` L507–572; `config_defaults.py` L949–955 — Surface 3 default keeps a healthy detached turn running (“an active turn runs to completion”); not an immediate interrupt.
- WINH03-AUD-06 — [PARTIAL] — MEDIUM — `methods_session.py` L337 `close_on_disconnect`; `session_lifecycle.py` L653–654 vs L390 `_interrupt_session_turn`; `ChatSidebar.tsx` L94–99 — no interrupt-on-disconnect RPC; `close_on_disconnect` reaps without calling `_interrupt_session_turn`. Desktop main chats do not set the flag.
- WINH03-AUD-07 — [PARTIAL] / [UNVERIFIED] — MEDIUM — `session.interrupt` → `_interrupt_session_turn` (`methods_session.py` L1995; `session_lifecycle.py` L390–432) — client interrupt-then-close can approximate Surface 1 if the frame is read; unread-frame race `[UNVERIFIED]`.
- WINH03-AUD-08 — [RISK] — HIGH — restates WINH02-AUD-12: Surface 3 default is structurally fail-open; fail-closed requires client `session.interrupt` and/or sidecar env (`HERMES_TUI_WS_ORPHAN_ACTIVITY_STALE_S=0` with grace > 0), not socket-drop alone.
- WINH03-AUD-09 — [PARTIAL] — MEDIUM — `tui_gateway/server.py` `_sessions` L85 vs `hermes_state_sessions.py`; `methods_session.py` `_resume_cold` L762–780; `event_replay.py` L26–28 — process crash loses live runtime and the 512-event ring; `session.resume` reloads durable transcript and builds a new agent.
- WINH03-AUD-10 — [UNVERIFIED] — MEDIUM — Windows `taskkill /F` / Desktop `forceKillProcessTree` vs `state.db` WAL (`hermes_state_wal.py`); `startup_orphan_sweep` (`config_defaults.py` L957–963) — resume-after-hard-kill integrity not settled by static reading.
- WINH03-AUD-11 — [PARTIAL] — LOW — Desktop `powerMonitor.on('resume')` (`apps/desktop/electron/main.ts` L6846–6847); no serve-side OS-sleep handler; loopback WS ping disabled (`config_defaults.py` L945–948) — sleep/wake misfire of the orphan timer is `[UNVERIFIED]`.
- WINH03-AUD-12 — [RISK] — MEDIUM — `tui_gateway/contracts/server_requests.py`; `_ask` L1306; approval 300s / clarify 3600s / sudo 120s — missing handlers time out then skip/deny at defaults; clarify `timeout <= 0` can wait forever.
- WINH03-AUD-13 — [MATCH] — LOW — `apps/desktop/package.json` L95 and `web/package.json` L18 `"@hermes/shared": "file:…"` — consumable outside the Hermes workspace via a relative `file:` dependency; still un-semvered (`WINH02-AUD-02`).
- WINH04-AUD-01 — [PARTIAL] — MEDIUM — `tools/memory_tool.py` L1–4, L38–40; `hermes_state_sessions.py` / `state.db`; `agent/memory_provider.py` L1–4 — builtin files + transcript + optional one plugin do not implement Hierarchy layers 0–6 as distinct stores.
- WINH04-AUD-02 — [RISK] — MEDIUM — `agent/memory_manager.py` `sync_turn` L485–503; `on_memory_write` L720–734 — provider session hooks persist memory outside `memory_tool`.
- WINH04-AUD-03 — [GAP] — HIGH — `tools/memory_tool_store.py` (no TTL); `config_defaults.py` L1222–1223 char limits only — Privacy Plan §3 retention windows unenforced.
- WINH04-AUD-04 — [PARTIAL] — MEDIUM — `MemoryStore.remove` `memory_tool_store.py` L270–274; `_cmd_memory_reset` `hermes_cli/main_agent_cmds.py` L21–56 — per-entry substring delete + file wipe; no cascade to `state.db`/clouds.
- WINH04-AUD-05 — [GAP] — HIGH — builtin entries are untyped strings (`memory_tool_store.py`); Ethics visibility scopes and sacred categories absent.
- WINH04-AUD-06 — [GAP] — HIGH — frozen prompt dump (`memory_tool.py` L2–4); `hermes_tools_mcp_server.py` L40 omits `memory` but instance tools/messaging still see the snapshot.
- WINH04-AUD-07 — [GAP] — MEDIUM — `atomic_write_text` `memory_tool_store.py` L422; no fact-memory ledger (contrast `tools/skill_ledger.py`).
- WINH04-AUD-08 — [MATCH] — LOW — `$HERMES_HOME/skills/` via `skill_manager_tool.py` L68 vs `$HERMES_HOME/memories/` — separate backends.
- WINH04-AUD-09 — [RISK] — MEDIUM — `write_approval.evaluate_gate` L171–175; `config_defaults.py` L1376 `skills.write_approval: False` — agent `skill_manage` create/edit ungated by default.
- WINH04-AUD-10 — [PARTIAL] — MEDIUM — `skills_tool.py` `skill_view` L540–549 fail-visible on load; no auto-disable on runtime skill error.
- WINH04-AUD-11 — [GAP] — MEDIUM — Hierarchy §4 DWA / Agency write pipeline — no source/scope/authority/freshness metadata or promotion state machine.
- WINH04-AUD-12 — [GAP] — MEDIUM — Ethics Context Contamination — USER.md is a single flattened profile (`memory_tool_store.py` L20–21).
- WINH04-AUD-13 — [PARTIAL] — LOW — `plugins/memory/holographic/retrieval.py` L39 `temporal_decay_half_life` default 0 — score decay, not deletion.
- WINH04-AUD-14 — [GAP] — MEDIUM — Privacy Plan §6 inventory / retention visibility / audit-log access — no Hermes mechanism.
- WINH05-AUD-01 — [GAP] — HIGH — `agent/prompt_builder.py` `DEFAULT_AGENT_IDENTITY` L130–138; `load_soul_md` L1452; `hermes_cli/config.py` `_ensure_default_soul_md` L611–623 — no locked Identity Seed; SOUL.md is fully replaceable prompt text.
- WINH05-AUD-02 — [PARTIAL] — MEDIUM — `agent/system_prompt.py` `_identity_parts` L488–494; `hermes_cli/personality.py` L118–124; `tools/memory_tool.py` L1–4 — identity / overlay / USER.md are separate slots, not locked-vs-adaptive types.
- WINH05-AUD-03 — [GAP] — HIGH — `personality.py` `persist_personality` L127–145; `plugins/memory/holographic/retrieval.py` L69 — style is config/presets; `trust_score` is retrieval, not phrasing.
- WINH05-AUD-04 — [GAP] — MEDIUM — no persona drift/baseline job; `agent/curator.py` is skill lifecycle only (WINH04).
- WINH05-AUD-05 — [GAP] — HIGH — `memory_tool_store.py` L20–21; `hermes_cli/profiles.py` — one persona string per session; USER.md has no context key (WINH04-AUD-01 Layer 5 remains additive).
- WINH05-AUD-06 — [RISK] — HIGH — `default_soul.py`; `personality.py` L19–34; `tools/voice_live.py` L48–69; `agent/auxiliary_client.py` L1352; `hermes_cli/doctor_state.py` L133 — multiple independently-maintained identity strings.
- WINH05-AUD-07 — [RISK] — MEDIUM — same sites as AUD-06 — agent name/identity change is a multi-file edit; customized SOUL.md is never auto-updated.
- WINH05-AUD-08 — [GAP] — MEDIUM — no style-profile store; USER.md is the only default place learned style could live.
- WINH05-AUD-09 — [GAP] — MEDIUM — no numeric clamps / bounded-evolution / style drift log (Consolidation Plan §8–9).
- WINH05-AUD-10 — [GAP] — HIGH — no `SelfBeliefBlock`; self-description is static SOUL.md / `DEFAULT_AGENT_IDENTITY`.
- WINH05-AUD-11 — [GAP] — MEDIUM — `prompt_builder.py` L137 — “when unsure, say so” is a style instruction, not computed hedging.
- WINH05-AUD-12 — [GAP] — MEDIUM — no SMA subsystem; agent loop writes memory and produces output (SMA read-only boundary unimplemented).
- WINH05-AUD-13 — [MATCH] — LOW — no user-facing self-model confidence numbers (prohibition not violated).
- WINH05-AUD-14 — [PARTIAL] — MEDIUM — `hermes_state_common.py` `sessions` L328–389 — explicit session row; no `deviceId`; live sid ≠ durable id.
- WINH05-AUD-15 — [RISK] — HIGH — `hermes_state_ids.py` `new_session_id`; many callers; `tui_gateway/methods_session.py` L65–67 runtime uuid — not a single mint call site.
- WINH05-AUD-16 — [PARTIAL] — MEDIUM — `tui_gateway/server.py` L122–140; `session_lifecycle.py` — WS orphan/resume ≠ Zola 30s app-background close.
- WINH05-AUD-17 — [PARTIAL] — MEDIUM — `sessions.user_id` / `profile_name` — profile/connection scoped, not user+device provenance.
- WINH05-AUD-18 — [PARTIAL] — MEDIUM — `messages.session_id` FK vs `tools/memory_tool.py` (no session field) — transcripts stamped; MEMORY.md writes not.
- WINH06-AUD-01 — [MECHANISM] — MEDIUM — `tools/skill_manager_tool.py` L682–688 — `skill_manage` create/edit/patch/delete/write_file/remove_file; no enable/disable action.
- WINH06-AUD-02 — [RISK] — HIGH — `write_approval.py` L171–175; `config_defaults.py` L1376 — `skills.write_approval` default False; gate fail-open on import (WINH04-AUD-09 confirmed).
- WINH06-AUD-03 — [ABSENT] — HIGH — `skill_manager_tool.py` L392–415, L49–63 — no dry-run/staging; `guard_agent_created` default False; write then live.
- WINH06-AUD-04 — [MECHANISM] — LOW — `tools/skill_ledger.py` L1–8, L246–266 — JSONL mutation ledger with before/after blobs; `session_id` in evidence when dispatch injects it.
- WINH06-AUD-05 — [RISK] — MEDIUM — `skill_ledger.py` L6–8, L269–288 — ledger is telemetry not a gate; append failures do not block the write.
- WINH06-AUD-06 — [MECHANISM] — MEDIUM — `skill_ledger.py` `rollback_entry` L338–402 — CLI `hermes curator rollback <id>`; foreground delete is hard; no transcript cascade.
- WINH06-AUD-07 — [MECHANISM] — HIGH — `agent/background_review.py` L1–6, L1025–1065 — post-turn fork can `skill_manage`; default `background_review.enabled: True`.
- WINH06-AUD-08 — [RISK] — HIGH — `write_approval.py` L174–175 — same ungated default applies to the review fork.
- WINH06-AUD-09 — [MECHANISM] — MEDIUM — `tools/setup_mcp_tool.py` L1–32 — desktop `setup_mcp` is a human consent card, not a silent config write.
- WINH06-AUD-10 — [RISK] — HIGH — `setup_mcp_tool.py` L29–32; `mcp_config.py` `cmd_mcp_add` — non-desktop fallback is `terminal` `hermes mcp install/add`; not in hardline patterns.
- WINH06-AUD-11 — [MECHANISM] — MEDIUM — `hermes_cli/plugins_cmd.py`; `plugins_discovery.py` L173–218 — plugin install is CLI/TUI; `plugin_guard`; `plugins.enabled` opt-in; capability consent.
- WINH06-AUD-12 — [ABSENT] — MEDIUM — searched `tools/*_tool.py` — no agent plugin-install tool (directory-drop still needs `plugins.enabled` in config).
- WINH06-AUD-13 — [RISK] — HIGH — `plugins.py` `register_tool` L460–502; `plugin_guard.py` L3–4 — new plugins in-process; MCP stdio as same OS user; no extra sandbox for newly added capability.
- WINH06-AUD-14 — [ABSENT] — MEDIUM — `methods_tools.py` `tools.list` / `plugins.list` — no single inventory of skills + tools + plugins + MCP.
- WINH06-AUD-15 — [MECHANISM] — MEDIUM — `tools/lazy_deps.py` L324–332; `config_defaults.py` L1640 — lazy PyPI installs into the venv; `allow_lazy_installs` default True.
- WINH06-AUD-16 — [UNVERIFIED] — LOW — `methods_slash.py` `_mirror_reload_mcp` L320–322 — live attach of CLI-installed MCP without `/reload-mcp` not confirmed in this checkout.
- WINH06-AUD-17 — [RISK] — HIGH — `file_tools_write_guards.py` L182–187 — `$HERMES_HOME/SOUL.md` exempt from protected-instruction always-ask; `write_file` can rewrite it.
- WINH06-AUD-18 — [MECHANISM] — MEDIUM — `file_tools_write_guards.py` L116–123, L208–213 — project-local SOUL.md always-ask; `config.yaml` hard-blocked on `write_file`.
- WINH06-AUD-19 — [ABSENT] — HIGH — searched write_approval / personality / prompt_builder — no draft/review state for identity or config self-modification.
- WINH06-AUD-20 — [RISK] — HIGH — `prompt_builder.py` `load_soul_md` L1452–1484 — SOUL rewrite has no SOUL ledger; WINH05-AUD-06/07 strings do not follow.
- WINH06-AUD-21 — [RISK] — MEDIUM — `approval_detection.py` (no `hermes config` patterns) — `hermes config set` via `terminal` bypasses the `write_file` config hard-block.
- WINH06-AUD-22 — [ABSENT] — LOW — searched agent/tools/cli for train/RLHF — no bundled fine-tune/RLHF/weight loop; optional TRL skill is user documentation.
- WINH06-AUD-23 — [MECHANISM] — MEDIUM — `agent/background_review.py` — only non-memory adaptation loop: post-turn skill/memory fork.
- WINH06-AUD-24 — [ABSENT] — MEDIUM — `agent/curator.py` (WINH04); no outcome scorer — no performance self-eval / A/B / prompt-optimization loop.
- WINH06-AUD-25 — [MECHANISM] — LOW — `tui_gateway/model_switch.py` L203–254; `model_tools.py` L212–221 — `/model` is a human slash; toolsets do not change with model id.
- WINH07-AUD-01 — [PARTIAL] — HIGH — `prompt_turn.py` L848; `server.py` L623–624, L1006; `agent_callbacks.py` L77 — primary `message.complete` path exists; `review.summary`, notices, heartbeat turns, and child completes also speak.
- WINH07-AUD-02 — [RISK] — HIGH — `background_review.py` L1148–1153; `server.py` L1006 — WINH06 fork emits user-facing `review.summary` / `_safe_print`, not file-only.
- WINH07-AUD-03 — [PARTIAL] — MEDIUM — `methods_prompt.py` L610–620; `session_auto_continue.py` L240–245; `session_transports.py` L50–82 — same-gateway concurrent submits serialize via `running`; no cross-surface arbiter.
- WINH07-AUD-04 — [GAP] — HIGH — searched `tui_gateway/`, `agent/` — no Response Governor / named core; `_emit` is a transport helper.
- WINH07-AUD-05 — [PARTIAL] — MEDIUM — `toolsets.py` L11–31; `approval_context.py` L228–237 — scope = enabled tools + danger overlay; no §13 permission catalog.
- WINH07-AUD-06 — [PARTIAL] — MEDIUM — `approval.py` L494–519; `config_defaults.py` L1557–1578 — danger/sudo/slash confirms; no contact/third-party escalation class.
- WINH07-AUD-07 — [RISK] — HIGH — `config_defaults.py` L1557, L767, L793–796 — default `approvals.mode: smart` (and interrupt/notify defaults) assume trust.
- WINH07-AUD-08 — [PARTIAL] — MEDIUM — `approval.py` L471–519; `server.py` L1000–1002 — approval prompts explain; smart-allow / missing toolset do not.
- WINH07-AUD-09 — [GAP] — HIGH — `server.py` `dispatch` L844–877 vs `api_server.py` / `acp_adapter` / `mcp_serve.py` / `webhook.py` — only Surfaces 2+3 share a dispatcher; four surfaces route alone.
- WINH07-AUD-10 — [PARTIAL] — MEDIUM — `runtime_provider.py` L835–852; `background_review.py` L205–243 — shared ladder function; review/delegation may pick independently.
- WINH07-AUD-11 — [RISK] — MEDIUM — `_DropTransport` L191–207; `event_replay.py` L26–28; `methods_session.py` L677–679 — orphaned output: drop / 512-ring / later attacher / session_key notify.
- WINH07-AUD-12 — [GAP] — MEDIUM — six inbound files (no single index) — routing authority not discoverable in one place (`WINH06-AUD-14` pattern).
- WINH07-AUD-13 — [GAP] — HIGH — `conversation_loop.py`; `turn_final_response.py` L1–6; `prompt_turn.py` L848 — same model call chain both reasons and phrases; no downstream formatter.
- WINH07-AUD-14 — [GAP] — HIGH — searched turn/stop/prompt_turn — no check that final text preserves tool numbers/names/dates.
- WINH07-AUD-15 — [GAP] — HIGH — `turn_stop_gates.py` L1–9; `verification_stop.py` L1–3 — architecture does not separate reasoning vs speech; verify-on-stop ≠ fidelity.
- WINH08-AUD-01 — [PARTIAL] — MEDIUM — `delegate_tool.py`; `background_review.py`; `cron/scheduler.py`; `heartbeat.py` — several worker paths exist; not Agent Map prepare-only categories.
- WINH08-AUD-02 — [RISK] — HIGH — `background_review.py` L1025–1107; `delegate_tool.py`; `scheduler.py` L1675–1721 — subagent/review/cron/heartbeat invoke tools off the live tool-round.
- WINH08-AUD-03 — [GAP] — MEDIUM — searched agent/tools/cron for `ttlMs`/`isStale` — no consumer-facing freshness/confidence on cached/precomputed data.
- WINH08-AUD-04 — [PARTIAL] — MEDIUM — `turn_facade.py` L33–39; `heartbeat.py` L4–6 — review yields to live; cron/delegate have no Agent 14 priority tiers.
- WINH08-AUD-05 — [MATCH] — LOW — `turn_tool_round.py` L45; `run_agent.py` L1273; `approval.py` L1015, L1079 — live turn: persist → execute → guards/approval → result.
- WINH08-AUD-06 — [RISK] — HIGH — `background_review.py` L988–992; `delegate_tool_config.py` L42–59; `approval_context.py` L126–128 — background/subagent/cron/heartbeat do not share one live human gate.
- WINH08-AUD-07 — [MATCH] — LOW — searched prefetch/warm/speculat in agent/tools — no speculative tool pre-execute (Agent 8 constraint holds by absence).
- WINH08-AUD-08 — [RISK] — MEDIUM — `server.py` L709; `_DropTransport`; `approval.py` timeout — orphaned turn keeps gateway approval until timeout, not unattended deny.
- WINH08-AUD-09 — [OBSERVATION] — MEDIUM — `cron/jobs.py` L1–73; `scheduler.py` L1–2; `gateway/run.py` L4587 — real cron ticker (60s) + jobs.json; not the review fork.
- WINH08-AUD-10 — [OBSERVATION] — MEDIUM — `scheduler.py` L1675–1721; `cron_mode` deny — cron runs full agent; danger default-deny; heartbeat uses live auth.
- WINH08-AUD-11 — [PARTIAL] — MEDIUM — `jobs.py` last_run_at; `scheduler_provider.py` L20, L240 — claim + misfire grace; not Agent 15 lastDeliveredDate.
- WINH08-AUD-12 — [GAP] — MEDIUM — cron status vs SessionDB heartbeat/loop vs kanban — no single place listing every scheduled job (`WINH06-AUD-14` / `WINH07-AUD-12` pattern).
- WINH08-AUD-13 — [PARTIAL] — MEDIUM — `turn_context.py` L779–790; `memory_manager.py` L394–443 — memory prefetch exists; no live-wins over cached recall text.
- WINH08-AUD-14 — [MATCH] — LOW — `memory_provider.py` L111–117 — prefetch is read/inject only; no speculative durable write.
- WINH09-AUD-01 — [PARTIAL] — MEDIUM — `tts_registry.py` L25–28; `tts_tool_providers.py` L219–229; `tts_streaming.py` L173–193 — ElevenLabs built-in file + PCM streamer; ABC `stream()` still default-unimplemented.
- WINH09-AUD-02 — [PARTIAL] — MEDIUM — `transcription_registry.py` L23–25; `transcription_command.py` L31–41 — No Cartesia/Deepgram built-in; command or plugin (file STT).
- WINH09-AUD-03 — [MATCH] — LOW — `config_defaults.py` L1008; `plugins.py` L1051–1061 — Built-in `tts.provider` / `stt.provider` swap by config.
- WINH09-AUD-04 — [PARTIAL] — MEDIUM — `tts_provider.py` L58–73; `tts_streaming.py` L142–159 — No latency catalog; `streaming.provider` auto/pin only.
- WINH09-AUD-05 — [PARTIAL] — MEDIUM — `methods_voice.py`; `voice.py` L331; `prompt_turn.py` — Chained: VAD → file STT → `voice.transcript` → client `prompt.submit`.
- WINH09-AUD-06 — [PARTIAL] — MEDIUM — `voice_mode.py` L852; `tts_tool_speaker.py`; `tts_streaming.py` — STT batch after silence; TTS sentence-stream if streamer exists.
- WINH09-AUD-07 — [PARTIAL] — MEDIUM — `methods_prompt.py` L586–588; `voice_live.py` L1–20, L84–90 — Context is a prompt note; GPT-Live WebRTC is a separate OpenAI duplex mode.
- WINH09-AUD-08 — [MATCH] — MEDIUM — `methods_voice.py` L117–134; `tts_streaming.py` L51–60 — Barge-in stops TTS and latches next-turn interrupt note.
- WINH09-AUD-09 — [RISK] — MEDIUM — `methods_voice.py` L1–2, L16–17, L309–312 — One mic/speaker per process; JSON-RPC voice assumes that topology.
- WINH09-AUD-10 — [GAP] — HIGH — searched agent/tools/tui_gateway; `transcription_cloud.py` L260, L318 — No speaker-identity / embedding tracker.
- WINH09-AUD-11 — [GAP] — HIGH — same search — No voice enrollment (ambient or formal).
- WINH09-AUD-12 — [RISK] — MEDIUM — `transcription_provider.py`; `voice_live.py`; WINH02 surfaces — On-device identity would not be structurally enforced.
- WINH09-AUD-13 — [GAP] — MEDIUM — `methods_prompt.py` prompt.submit — Turns are single-author for voice; no speaker field.
- WINH09-AUD-14 — [GAP] — HIGH — `config_defaults.py` L1161–1178; `methods_voice.py` L309–312 — Wake-word is the primary gate, not directed-speech.
- WINH09-AUD-15 — [GAP] — MEDIUM — wake engines; no confidence tiers in voice state machine — Activation is binary.
- WINH09-AUD-16 — [PARTIAL] — MEDIUM — `methods_voice.py` L747–752, L685–687 — After capture, wake re-arms; no continuation window.
- WINH10-AUD-01 — [PARTIAL] — MEDIUM — `authz_mixin.py` L544–605; `run_inbound.py` L191–205; `email/adapter.py` L602–628 — Allowlist/pairing gate, not silent contact-list exclusion.
- WINH10-AUD-02 — [GAP] — HIGH — searched SmsSignal/EmailIntelligenceAnalyzer; `session.py` transcripts — No signal-extract-then-discard; raw body is the turn.
- WINH10-AUD-03 — [GAP] — MEDIUM — searched threadVelocity / last H hours — No first-class thread-velocity signal.
- WINH10-AUD-04 — [PARTIAL] — MEDIUM — `run_startup.py` L821–854; `sms/plugin.yaml` `SMS_ALLOWED_USERS` — Channel allowlist ≠ `smsAnalysisConsent`.
- WINH10-AUD-05 — [MATCH] — LOW — `send_message_tool.py` L22–24; `toolsets.py` L185; registry test L191–194 — `send_message` not model-callable; CLI/cron/kanban/MCP call helpers.
- WINH10-AUD-06 — [RISK] — HIGH — `base.py` `handle_message`; `delivery.py` L254; SMS `adapter.send` — Live gateway reply is autonomous send on the inbound channel.
- WINH10-AUD-07 — [GAP] — HIGH — `send_cmd.py` L195; `scheduler_delivery.py` L1460; `mcp_serve.py` L600 — Host send paths have no two-step per-message confirm.
- WINH10-AUD-09 — [PARTIAL] — MEDIUM — `plugins/platforms/sms/adapter.py` — Twilio SMS exists; Windows has no handset radio.
- WINH10-AUD-10 — [PARTIAL] — MEDIUM — `plugins/platforms/email/adapter.py`; Graph used by `teams_pipeline` — Mail bot ≠ EmailSignal; Graph is Teams not Outlook mail.
- WINH10-AUD-11 — [MATCH] — LOW — `toolsets.py` L202–240; `send_message_tool.py` L568–588 — Broad chat-platform coverage; WhatsApp/Signal/Twilio for “text”.
- WINH10-AUD-12 — [OBSERVATION] — — Twilio plugin; Phone Link / CPaaS / defer — Windows SMS options; not a Hermes score.
- WINH10-AUD-13 — [RISK] — MEDIUM — `session.py` transcripts; cite `WINH04-AUD-02`/`06` — Comms bodies persist like any other turn.
- WINH11-AUD-01 — [GAP] — HIGH — `env_loader.py` L321–372; `secret_scope.py` L111–138 — provider keys live in plaintext `<HERMES_HOME>/.env`.
- WINH11-AUD-02 — [PARTIAL] — MEDIUM — `vault_store.py` L187–260 — autofill vault is Fernet; `vault.key` sits beside `vault.json.enc`.
- WINH11-AUD-03 — [PARTIAL] — MEDIUM — `secret-storage-policy.ts` L13–65 — Desktop `safeStorage` (DPAPI) exists, default OFF, tokens only.
- WINH11-AUD-04 — [GAP] — HIGH — `hermes_state.py` L675–681; `hermes_state_dbfile.py` L553–566 — `state.db` is plain `sqlite3.connect`.
- WINH11-AUD-05 — [GAP] — HIGH — `learning_graph.py` L130–134; `state.db` — memory markdown + session DB unencrypted at rest.
- WINH11-AUD-06 — [PARTIAL] — MEDIUM — `web_server.py` L304–311, L457–464, L636–655 — data-mgmt gate is ephemeral SPA token, not user auth (cite `WINH02-AUD-04`).
- WINH11-AUD-07 — [GAP] — MEDIUM — cite `WINH04-AUD-11` — DWA still absent; §9 write-gate unmet.
- WINH11-AUD-08 — [PARTIAL] — MEDIUM — `process_bootstrap.py` L387–436; `providers.py` L41 — default `verify=True`; `http://` base_url allowed; no TLS 1.2 pin.
- WINH11-AUD-09 — [GAP] — LOW — Privacy Plan §9 L518; series scope — Distributed Presence E2E out of series (N/A, not scratch).
- WINH11-AUD-10 — [RISK] — HIGH — `mcp_tool_config.py` `_build_safe_env` L96–118 — secret-source credentials copied into MCP child env.
- WINH11-AUD-11 — [PARTIAL] — MEDIUM — `credential_files.py` L63–98; cite `WINH06-AUD-11`/`13` — master stores blocked; no separate Tier 1/2 grant.
- WINH11-AUD-12 — [RISK] — HIGH — `package.json` L288; `install.ps1` L4149–4160 — Windows Desktop is built unsigned.
- WINH11-AUD-13 — [RISK] — MEDIUM — nsis block; no `deleteAppDataOnUninstall` — uninstall leaves `HERMES_HOME` / credentials / `state.db`.
- WINH11-AUD-14 — [ABSENT] — HIGH — searched `.github/workflows`; `notarize.mjs` L54 — no Windows Authenticode/CI signing.
- WINH11-AUD-15 — [MECHANISM] — MEDIUM — `updater-process.ts`; `windows.ps1`; `update_cmd.py` — custom git/zip update, not electron-updater.
- WINH11-AUD-16 — [RISK] — HIGH — `update_cmd_zip.py` L382; git path (no verify) — no commit-sig / zip checksum on updates.
- WINH11-AUD-17 — [MECHANISM] — LOW — `package.json` L300–303 — NSIS per-user, `oneClick: false`.
- WINH11-AUD-18 — [MECHANISM] — LOW — `package.json` L284–307 — NSIS+MSI targets; MSI extras unverified.
- WINH11-AUD-19 — [MECHANISM] — MEDIUM — `session-windows.ts` L46–57 — Electron `contextIsolation` + `sandbox` + `nodeIntegration: false`.
- WINH11-AUD-20 — [RISK] — MEDIUM — `windows-sandbox-fallback.ts` L15–22 — Windows can fall back to `--no-sandbox`.
- WINH11-AUD-21 — [MECHANISM] — LOW — `config_defaults.py` L2279; `vercel_sandbox.py` L44–46 — no always-on Hermes telemetry.
- WINH11-AUD-22 — [MECHANISM] — LOW — `gateway_windows.py` L152–189 — runs as user; UAC only for gateway task install.
- WINH12-AUD-01 — [GAP] — HIGH — `system_prompt.py` L433–457, L656 — timestamps/dates exist; no elapsed-time-to-meaning.
- WINH12-AUD-02 — [GAP] — HIGH — cite `WINH03-AUD-09`, `WINH05-AUD-15` — no relational `SessionBoundaryResolver`.
- WINH12-AUD-03 — [GAP] — HIGH — searched `agent/`/`tools/` — no `ThreadArcClassifier` or `TemporalRecencyFormatter`.
- WINH12-AUD-04 — [RISK] — MEDIUM — `hermes_time.py`; `turn_context.py` L515 — clock split: prompt TZ vs `time.time` vs UTC datetime.
- WINH12-AUD-05 — [GAP] — HIGH — cite `WINH05-AUD-10`–`13` — belief/correction/entity-view/arc contracts absent.
- WINH12-AUD-06 — [GAP] — HIGH — `memory_tool.py` L2; `learning_graph.py` L130–134 — no third-party person model; flat MEMORY.md/USER.md.
- WINH12-AUD-07 — [GAP] — HIGH — searched relationship-type / KNOWS_ABOUT — no structured relationship predicates.
- WINH12-AUD-08 — [GAP] — MEDIUM — `learning_graph.py` L130–134 — no salience / distinct-session recurrence ranking.
- WINH12-AUD-09 — [GAP] — HIGH — searched RelationshipArc / relationshipDepth — no relationship-arc document.
- WINH12-AUD-10 — [GAP] — HIGH — `system_prompt.py` L1–8, L656 — prompt injects memory files + date, not an arc block.
- WINH12-AUD-11 — [GAP] — HIGH — cite `WINH05-AUD-03`/`08` — no depth-driven familiarity / warmth ceiling.
- WINH12-AUD-12 — [GAP] — HIGH — Phase 2 + `WINH05-AUD-10`–`12` — Calibration dependency chain unmet at every link.
- WINH12-AUD-13 — [MATCH] — MEDIUM — `providers.py`; `gemini_native_adapter.py` — Gemini/OpenAI/Anthropic native; not Gemini-locked.
- WINH12-AUD-14 — [MATCH] — MEDIUM — `lmstudio_reasoning.py`; `providers.py` L136–137 — local OpenAI-compat can run the full tool loop.
- WINH12-AUD-15 — [MATCH] — MEDIUM — `model_switch.py` L15, L203–254; cite `WINH06-AUD-25` — live `/model` switches provider+model mid-session.
- WINH12-AUD-16 — [MATCH] — MEDIUM — `transports/base.py`; `NormalizedResponse` — wire formats convert into one internal representation.
- WINH12-AUD-17 — [RISK] — MEDIUM — cite `WINH07-AUD-01`/`02`; RIL master L312–343 — single delivery path vs Hermes multi-path speech.
