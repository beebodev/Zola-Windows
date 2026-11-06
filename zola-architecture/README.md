# zola-architecture — Windows architecture docs

*Created 2026-11-02 by the ARCH-SWAP track (ARCH-68).*

These 16 docs describe the Zola-Windows architecture: the intended vision, what is built today, its limits and open questions. They **state intent and authorise no implementation**. Build work is still scoped, decided and approved phase by phase under the SOP.

| Doc | Covers |
|---|---|
| [`A01_Architecture_Overview.md`](A01_Architecture_Overview.md) | Architecture Overview: who owns each responsibility; the PC is the core; principles |
| [`A02_Identity_and_Personality.md`](A02_Identity_and_Personality.md) | Identity and Personality: who she is; growth; per-person style; drift |
| [`A02b_Relationship_with_Brian.md`](A02b_Relationship_with_Brian.md) | Relationship with Brian: history, the moment vs the relationship, familiarity |
| [`A03_Memory_and_World_Model.md`](A03_Memory_and_World_Model.md) | Memory and World Model: entities, evidence, promotion, confidence, correction, forget |
| [`A04_People_in_Brians_World.md`](A04_People_in_Brians_World.md) | People in Brian's World: people, relationships, the household |
| [`A05_Time_and_Temporal_Understanding.md`](A05_Time_and_Temporal_Understanding.md) | Time: elapsed time, event vs mention time, validity, freshness |
| [`A06_Conversation_and_Continuity.md`](A06_Conversation_and_Continuity.md) | Conversation and Continuity: sessions, topics, session briefs, several people, devices |
| [`A07_Voice_Listening_and_Speech.md`](A07_Voice_Listening_and_Speech.md) | Voice, Listening and Speech: attention, the wake word, streaming, speakers, speech |
| [`A08_Awareness_Sources_Signals_and_User_State.md`](A08_Awareness_Sources_Signals_and_User_State.md) | Awareness: sources, items, user state, places, communications |
| [`A09_Physical_Perception.md`](A09_Physical_Perception.md) | Physical Perception: cameras, presence, environmental sound |
| [`A10_Understanding_Events_and_Judgment.md`](A10_Understanding_Events_and_Judgment.md) | Understanding Events and Judgment: the six responsibilities; the one decision point |
| [`A11_Proactive_Engagement.md`](A11_Proactive_Engagement.md) | Proactive Engagement: raising things, summaries, the daily brief, watches, curiosity |
| [`A12_Distributed_Presence_and_Devices.md`](A12_Distributed_Presence_and_Devices.md) | Distributed Presence and Devices: endpoints, capabilities, handoff, routing |
| [`A13_Presence_UI_and_Avatar.md`](A13_Presence_UI_and_Avatar.md) | Presence UI and Avatar: her look, states, motion, the window |
| [`A14_Privacy_and_Memory_Ethics.md`](A14_Privacy_and_Memory_Ethics.md) | Privacy and Memory Ethics: keeping, disclosing, forget, turning things off |
| [`A15_Authority_Tools_Actions_and_Autonomy.md`](A15_Authority_Tools_Actions_and_Autonomy.md) | Authority: tools, actions, approvals, self-changes, future autonomy |

**Records**
- [`ARCH_DOCS_DECISIONS.md`](ARCH_DOCS_DECISIONS.md): Brian's decisions for the rewrite, ARCH-01 onwards.
- [`audit/arch-docs-swap/`](audit/arch-docs-swap/): the coverage map, the source heading inventory, the merge matrix and the read notes. They show where every retired document's content went, and why.
- `lore/` (decisions, open questions, roadmap, build plans, progress) and `identity/` (live identity mirrors) are unchanged by the rewrite and remain the authority for what each phase decided and built.

## Retired documents

The 39 Android-era architecture documents that used to sit in this folder were retired by the ARCH-SWAP track, after the Phase 10 lore closeout (approved by Brian 2026-11-02, ARCH-68). **The originals live in the Android repository.** Historical lore, closeouts and audits still cite them by name; this table is their successor pointer. Section-level detail is in `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` (§7) and `ARCH_DOCS_HEADING_INVENTORY.md`.

| Retired document | Now covered in |
|---|---|
| `Zola Autonomous Behavior Architecture.md` | A10, A11; A02, A06, A08 |
| `Zola Conversational Attention Architecture.md` | A07 §3–§5; A06, A12, A14 |
| `Zola Conversational Continuity Architecture.md` | A06 §2–§5; A03, A05, A07, A12 |
| `Zola Distributed Presence Architecture.md` | A12; A01, A06 |
| `Zola Environmental Awareness Architecture.md` | A08, A09, A10; A03, A05, A12, A14 |
| `Zola Environmental Perception Architecture.md` | A09; A03, A05, A08, A10, A14 |
| `Zola Identity and Personality Framework.md` | A02; A02b |
| `Zola Master Architecture Plan.md` | A01 and all domain docs |
| `Zola Memory Hierarchy Architecture.md` | A03, A05, A06; A14 |
| `Zola Privacy and Data Ownership Plan.md` | A14; A03, A09, A15 |
| `Zola Streaming Cognition Architecture.md` | A07 §7; A06, A15 |
| `Zola_Agent_Map.md` | A01–A11 by responsibility |
| `Zola_Architecture_Cognitive_Engagement.md` | A11 §7; A10, A03, A14 |
| `Zola_Architecture_Context_Injection.md` | A06 §2, §5; A03 |
| `Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md` | A12 |
| `Zola_Architecture_Distributed_Presence_Device_Capabilities.md` | A12; A08, A15 |
| `Zola_Architecture_Environmental_Event_Bus_and_User_State_Model.md` | A08, A10; A05, A09 |
| `Zola_Architecture_Identity_Source_Consolidation_Plan.md` | A02 |
| `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` | A07 §8; A09, A14 |
| `Zola_Architecture_Memory_Agency.md` | A03, A11, A14; A05 |
| `Zola_Architecture_Memory_Ethics_and_Privacy.md` | A14; A03, A04 |
| `Zola_Architecture_Perception_Memory.md` | A03, A05, A09 |
| `Zola_Architecture_Perceptual_Input_Layer.md` | A09, A07, A11, A13, A14 |
| `Zola_Architecture_Relationship_Inference.md` | A04; A03 |
| `Zola_Attention_Relevance_Engine_Architecture.md` | A10, A11; A08, A12 |
| `Zola_Capability_Acquisition_Architecture.md` | A15 §8; A01, A14 |
| `Zola_Cognitive_Engine_Architecture.md` | A10 §9, A11 §6.0, §7.3 |
| `Zola_Communication_Intelligence_Architecture.md` | A08 §9, A11 §5.1; A10, A15 |
| `Zola_CrossDomain_Correlation_Architecture.md` | A03 §6, §7; A10 §8; A11 |
| `Zola_Presence_UI_Architecture.md` | A13; A12, A14 |
| `Zola_Relational_Calibration_Architecture.md` | A02b; A02, A15 |
| `Zola_Relational_Continuity_Architecture.md` | A02b; A03, A05, A11 |
| `Zola_Relational_Intelligence_Layer_Architecture.md` | A02b, A03, A04, A05; A10, A14 |
| `Zola_SelfModel_Awareness_Architecture.md` | A03 §8, §8.1; A02 |
| `Zola_Session_Identity_Architecture.md` | A06 §3; A12 |
| `Zola_Sms_Intelligence_Architecture.md` | A08 §9, A11 §5.1; A12, A15 |
| `Zola_SocialGraph_Reasoning_Architecture.md` | A04; A03, A02b, A11 |
| `Zola_Temporal_Reasoning_Architecture.md` | A05; A03, A06, A10, A11 |
| `Zola_Tool_Authorization_Architecture.md` | A15; A01, A03 |
