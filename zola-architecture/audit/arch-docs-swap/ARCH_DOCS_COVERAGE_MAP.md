# Architecture Docs — Combined Coverage Map

*In the repo this file lives in `zola-architecture/audit/arch-docs-swap/`; the 16 docs and `ARCH_DOCS_DECISIONS.md` are in `zola-architecture/`. Signed off by Brian 2026-11-02 (ARCH-68).*

*v1.1, 2026-11-02. Author: Claude. **Status: re-audited by ChatGPT; corrections R01–R05 and cleanups applied (§6a). Signed off by Brian 2026-11-02 (ARCH-68).** Not in the repo. This map clears nothing for deletion by itself. Deletion happens only in the Cursor repo-swap track, after Brian approves.*

**What this is.** One place that shows where every one of the 39 Android-derived copies in `zola-windows/zola-architecture/` went in the 16 Windows docs (A01–A15, A02b), on what evidence, and what still stands between each copy and deletion. Each draft's own coverage section holds the row-level detail; this map ties them together.

**What it isn't.** It isn't a sentence-by-sentence equivalence proof of about 1.17 MB of originals. It isn't implementation verification. Android thresholds, class names, Firestore paths and phase plans aren't Windows commitments. They're kept only where their *purpose* matters, or their omission is recorded.

---

## 1. Verdict

- **Every original has a home.** No original is orphaned.
- **The 54 "planned" rows are closed.** Each now names exact destination sections, and those sections were checked. One row (Memory Hierarchy observability) had no home; it now has A03 §12.1.
- **No row is "verified (notes)" any more.** Every such row was re-checked against a fresh read of its source on 2026-11-02, or tied to the fresh full read made when its destination doc was drafted.
- **The audit's content gaps C01–C08 are closed** with explicit text, and two decisions (ARCH-65, ARCH-66).
- **The cross-document alignment items X01–X10 are closed.** X02, X03, X04 and X08 were already fixed; the audit had read stale copies of eight docs (§6).
- **The fresh reads found further smaller gaps.** Each is now carried into a doc (§5).

**Re-audit (ChatGPT, 2026-11-02):** C01–C08 and X01–X10 confirmed closed in the actual text; no further large missing capability. It found five focused corrections (R01–R05) and five cleanups, all now applied (§6a). R04 needed a decision: ARCH-67.

**Recommendation:** the 39 originals are ready for deletion **in the repo-swap track**, once Brian signs off. Deletion is a separate, explicitly authorised action; this map doesn't perform it. The full heading inventory (`ARCH_DOCS_HEADING_INVENTORY.md`) goes into the swap record with it.

---

## 2. Evidence standard

| Basis | Meaning |
|---|---|
| **Fresh full read (drafting)** | The source was read in full when its destination doc was drafted (2026-10-29 to 11-02), and the rows were checked against that read |
| **Fresh read 2026-11-02** | Re-read today for this map, either in full or the named sections, after the coverage audit flagged thin mapping |
| **Section inventory** | All 672 `##` headings of the 39 originals were extracted and matched mechanically against every coverage row. 198 had no row naming them. Each was then resolved by reading the section, or classified in §4 |

**Evidence limit.** Several originals reference `Zola_Daily_Brief_Architecture.md`. That file isn't in the Windows checkout, so it was never read. A11 §5.1 was rebuilt from the Agent Map (Agent 15), Communication Intelligence and SMS Intelligence only.

---

## 3. Dispositions

Used in this map, and in new or updated rows:

| Disposition | Evidence it needs |
|---|---|
| **Retained** | The destination section contains the source's required outcome and boundary |
| **Split** | Every part has a destination, and the owner of each handoff is clear |
| **Superseded** | A named Windows decision replaces the old behaviour; the body text and the map agree |
| **Intentionally omitted** | What's omitted is named, with a reason. Android plumbing, phases and numbers usually qualify |
| **Deferred but retained** | The unbuilt experience and its boundaries remain explicit enough to build later |
| **Unresolved** | Not cleared for deletion; says what must be checked or decided |

Older rows still say "preserved", "merged" or "moved". Read them as **retained**, **split** and **split** respectively. They were checked against the destination, not merely pointed at it.

---

## 4. Sections with no row of their own

*At v1.0, 198 of 672 headings had no row naming them. After the reconciliation and re-audit passes, 189 do not. Every heading, with its specific disposition, is listed in `ARCH_DOCS_HEADING_INVENTORY.md`. The class view below is a summary; as the re-audit notes, it is not by itself evidence that every sentence under such a heading was wiring. Substantive requirements found under them were carried into the docs (§5).*

These are mostly structural, and resolved as a class:

| Kind of section | How many (approx.) | Disposition |
|---|---|---|
| Vision, Core Philosophy, Long-Term End State, Final Principle | ~70 | **Retained** in each destination doc's §1 Intent and §2 Principles. The end-state wording appears as "what this should feel like" |
| "Long-Term Architectural Pillars" headers | ~20 | Empty headers. The numbered pillar sections under them are mapped individually |
| Integration Points, Integration Point Map, Relationship to Other Documents | ~30 | **Intentionally omitted** as class wiring. The *ownership* each one expressed is in A01 §3.1 and each doc's "who owns what" |
| Roadmap, Phase Sequencing, Track Sequencing, Recommended Build Order, Pre-Work | ~20 | **Intentionally omitted** (Android phases). One build principle kept: one new kind of unprompted behaviour at a time (A11 §7.3) |
| Non-Goals | ~10 | **Retained** as principles where substantive; Android-scope disclaimers omitted |
| Known Constraints and Deferred Work | ~8 | **Retained** as Limits rows and standing triggers (A01, A14, A15) |
| Android-specific components (Firestore paths, CEA-D lock list, Gemini Live paths, RTDB, mint call site) | ~25 | **Intentionally omitted**. Behavioural content was extracted where present (§5) |
| Remaining substantive sections | ~15 | **Read today and resolved** individually (§5) |

---

## 5. What the fresh reads added (2026-11-02)

Beyond the audit's C01–C08, re-reading the thinly mapped sources found these smaller gaps. Each is now in a doc:

| Source | Gap | Now in |
|---|---|---|
| Self-Model Awareness | A gap raised once per conversation; locked identity never hedged; the self-model is read-only and never shown as numbers | A03 §8.1 |
| Living Voiceprint §6–8, §12 | Improvement samples held until a clean finish; condition diversity; voices still being learned are visible; kept out of backups | A07 §8.1, §8.3 |
| Perception Memory | Dismissing or deferring an unknown entity; contradiction resets the count | A09 §5.2 |
| Perception Memory | Confidence change never applies to identity and doesn't spread by itself | A03 §5.4 |
| Cross-Domain Correlation | Connecting is read-only; the contact index holds signals, not content; future domains deferred but retained | A10 §8 |
| Memory Agency | Fuller salience signals, including a break in a pattern | A03 §5.2 |
| Memory Agency | Usage restrictions only tighten on their own | A14 §5.4 |
| Memory Hierarchy | Every memory decision can be explained (the questions, not the log tags) | A03 §12.1 |
| Context Injection | Brief parts dropped whole, never cut mid-line | A06 §5 |
| Cognitive Engine | Curiosity eases as knowledge fills in; one new kind of behaviour at a time; how items leave the queue | A11 §7.3, §6.0 |
| Communication / SMS Intelligence | The brief may offer a next step through the normal send path; consent explained plainly; how fast a text thread moves is a signal | A11 §5.1; A08 §9 |
| Agent Map (12, 3) | One user-state estimate read by everyone; attention hints are hints only | A08 §5; A07 §4.2 |
| Streaming Cognition | Tool arguments from the final transcript; disagreement between the guessed and final path logged | A07 §7 |
| Event Bus | Interpretation owns meaning, the decision point owns action; every output traceable to a decision | A10 §3 |
| Event Bus | Location alone gives moderate confidence at a known place | A08 §6.2 |
| Autonomous Behavior | Never manipulative: no false urgency, invented memories or forced engagement | A11 §2 p6 |
| Identity Consolidation | Repeated correction of one trait means the evidence is suspect | A02 §6.4 |
| Privacy Plan §2 | A material change of purpose needs fresh permission | A14 §7.1 |
| Event Bus "tier 1 needs multi-signal high confidence" | Recorded as **superseded by ARCH-63** | A08 coverage |
| Memory Agency, Perception Memory, Self-Model, Cross-Domain | The fresh line-by-line check A03 §17 promised | A03 §17 (done) |

---

## 6. Audit findings: closure

**C01–C08 (content):**

| ID | Closed by |
|---|---|
| C01 Daily brief | A11 §5.1; ARCH-65 |
| C02 Preparing information in advance | A10 §9.1 (one owner) |
| C03 How much she knows | A03 §8.1 |
| C04 Memory upkeep | A03 §5.8 |
| C05 Context assembly is read-only | A06 §5 |
| C06 Voice-learning safeguards | A07 §8.1, §8.3 |
| C07 Overload | A08 §4 |
| C08 Four turn-off actions | A14 §7.1; ARCH-66 |

**X01–X10 (alignment).** The audit read old copies of A02, A02b, A07, A08, A12, A13, A14 and A15. The PC drafts folder hadn't been updated after their later revisions; it has been synced since.

| ID | Status |
|---|---|
| X01 A08 low-confidence rule | Fixed (A08 §4, §8; A10 §5.1 "Drop") |
| X02 A02b friction model | Already fixed in A02b v0.2 |
| X03 A02/A13 open questions | Already fixed in A02 v0.2, A13 v0.2 |
| X04 Codes voice | Already fixed in A07 v0.4 |
| X05 Guest tools | Fixed in A01, A04 and A15 (shortlist; timer note) |
| X06 Visitor retention | Fixed in A04 and A07 (A14, A09 were already right) |
| X07 Household-operation trigger | Fixed in A01 and A14 (A15 was already right) |
| X08 A15 approval wording | Already fixed in A15 v0.2 |
| X09 A12 coverage row | Fixed (split row) |
| X10 "Show quietly" | Fixed (A10 §5.1) |

---

## 6a. Re-audit corrections (applied)

| ID | Correction | Now in |
|---|---|---|
| R01 | A phone opened in public: recognition settles who holds it, not who can hear. Minimal opener; the gist waits for a private channel | A12 D15b |
| R02 | Cameras local by default; cloud only per ARCH-62; biometrics never leave the PC | A14 §6, §8 |
| R03 | Held items also leave on forget, withdrawn use or source off, with a recorded reason; your own reminders survive | A11 §6.0; A14 PR21 |
| R04 | Starting a conversation without the wake word is a per-person permission; visitors never; Android activation grant superseded | **ARCH-67**; A07 §4.5, V17; A14 §8 |
| R05 | Uncertain-but-serious is never dropped for low confidence alone, and *may* be raised through the normal checks; repeats can be suppressed | A10 §5.1 |
| Cleanups | "Delivery unconfirmed", not "heard" (A11 §5, A12); VD-5 narrowed, override kept (A07); A04 evidence label; A03 §5.8 reference; guest shortlist examples conditional on the final list (A15) | as listed |

## 7. All 39 originals

"Basis" is how the rows for that source were checked. "Ready" means no unresolved row remains and the re-audit's corrections are applied. Deletion still needs Brian's sign-off in the repo-swap track.

| # | Original | Replacement homes | Basis | Notable dispositions | Ready |
|---|---|---|---|---|---|
| 1 | Zola Autonomous Behavior Architecture | A10, A11; A02, A06, A08 | Drafting read; §1–3, §6, principles and failures re-read 11-02 | Response Governor → A10 §5 single decision point; behavioural learning → A02 §5; never manipulative → A11 | yes |
| 2 | Zola Conversational Attention Architecture | A07 §3–§5; A06, A12, A14 | Drafting read | Inbound attention distinct from proactive interruption | yes |
| 3 | Zola Conversational Continuity Architecture | A06 §2–§5; A03, A05, A07, A12 | Drafting read | Hermes session is the authority (superseded state engine) | yes |
| 4 | Zola Distributed Presence Architecture | A12; A01, A06 | Drafting read | PC the one brain; peer sync superseded by ARCH-16; shop authority settled by ARCH-29 | yes |
| 5 | Zola Environmental Awareness Architecture | A08, A09, A10; A03, A05, A12, A14 | Drafting read | Awareness modes → A08 §6.2 contexts | yes |
| 6 | Zola Environmental Perception Architecture | A09; A03, A05, A08, A10, A14 | Drafting read (A09 v0.2) | Confidence vs urgency (ARCH-63); privacy acts at once (ARCH-64) | yes |
| 7 | Zola Identity and Personality Framework | A02; A02b | Drafting read | Three layers; drift correction | yes |
| 8 | Zola Master Architecture Plan | A01 and all domain docs | Drafting read | All pillar rows now name exact sections | yes |
| 9 | Zola Memory Hierarchy Architecture | A03, A05, A06; A14 | Drafting read; observability re-read 11-02 | Observability questions → A03 §12.1 | yes |
| 10 | Zola Privacy and Data Ownership Plan | A14; A03, A09, A15 | Drafting read | Revocation superseded by ARCH-66; fresh permission for a new purpose retained | yes |
| 11 | Zola Streaming Cognition Architecture | A07 §7; A06, A15 | Drafting read; failure and observability re-read 11-02 | Retained as vision | yes |
| 12 | Zola_Agent_Map | A01–A11 by responsibility | Fresh read 11-02 | Agents 1/8/9 → A10 §9.1 (deferred); 14 → A01 principle 5; 15 → A11 §5.1 | yes |
| 13 | Zola_Architecture_Cognitive_Engagement | A11 §7; A10, A03, A14 | Drafting read | Tension as a signal only | yes |
| 14 | Zola_Architecture_Context_Injection | A06 §2, §5; A03 | Fresh read 11-02 | Household-scoped brief superseded (ARCH-03/13); read-only retained | yes |
| 15 | Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking | A12 | Drafting read | Firebase/FCM omitted; handoff retained | yes |
| 16 | Zola_Architecture_Distributed_Presence_Device_Capabilities | A12; A08, A15 | Drafting read | Primary source for A12 | yes |
| 17 | Zola_Architecture_Environmental_Event_Bus_and_User_State_Model | A08, A10; A05, A09 | Drafting read; §core, §3, principles, failures re-read 11-02 | Overload (C07); multi-signal tier-1 rule superseded by ARCH-63 | yes |
| 18 | Zola_Architecture_Identity_Source_Consolidation_Plan | A02 | Drafting read; failure modes re-read 11-02 | Rename and prompt plumbing omitted | yes |
| 19 | Zola_Architecture_Living_Voiceprint_MultiSpeaker | A07 §8; A09, A14 | Drafting read; §6–8, §12 re-read 11-02 | Safeguards (C06); provisional expiry superseded by ARCH-37 | yes |
| 20 | Zola_Architecture_Memory_Agency | A03, A11, A14; A05 | Fresh read 11-02 | Upkeep (C04); governor "use silently" replaced by "withhold" | yes |
| 21 | Zola_Architecture_Memory_Ethics_and_Privacy | A14; A03, A04 | Drafting read | Sacred no-proactive rule superseded by ARCH-04 | yes |
| 22 | Zola_Architecture_Perception_Memory | A03, A05, A09 | Fresh read 11-02 | Silence-as-confirmation superseded; numbers omitted | yes |
| 23 | Zola_Architecture_Perceptual_Input_Layer | A09, A07, A11, A13, A14 | Drafting read (A09) | Biometrics (ARCH-07), foregrounding (ARCH-21), P5 (ARCH-63) superseded | yes |
| 24 | Zola_Architecture_Relationship_Inference | A04; A03 | Drafting read | Stored siblings superseded by ARCH-14 | yes |
| 25 | Zola_Attention_Relevance_Engine_Architecture | A10, A11; A08, A12 | Drafting read | "Show quietly" defined (X10) | yes |
| 26 | Zola_Capability_Acquisition_Architecture | A15 §8; A01, A14 | Drafting read; non-goals and constraints re-read 11-02 | Effect-based skill edits (ARCH-43); household trigger (ARCH-44) | yes |
| 27 | Zola_Cognitive_Engine_Architecture | A10 §9, A11 §6.0, §7.3 | Fresh read 11-02 | Mid-session freeze rejected; density-driven curiosity kept as intent | yes |
| 28 | Zola_Communication_Intelligence_Architecture | A08 §9, A11 §5.1; A10, A15 | Fresh read 11-02 | Brief deferred but retained (ARCH-65) | yes |
| 29 | Zola_CrossDomain_Correlation_Architecture | A03 §6, §7; A10 §8; A11 | Fresh read 11-02 | Future domains deferred but retained | yes |
| 30 | Zola_Presence_UI_Architecture | A13; A12, A14 | Drafting read | Hologram dropped (ARCH-56); head and hair motion wanted (ARCH-54) | yes |
| 31 | Zola_Relational_Calibration_Architecture | A02b; A02, A15 | Drafting read | Assumption licence rejected (ARCH-10); damper superseded | yes |
| 32 | Zola_Relational_Continuity_Architecture | A02b; A03, A05, A11 | Drafting read | Friction model superseded (ARCH-50/53) | yes |
| 33 | Zola_Relational_Intelligence_Layer_Architecture | A02b, A03, A04, A05; A10, A14 | Drafting read | Umbrella dissolved by responsibility | yes |
| 34 | Zola_SelfModel_Awareness_Architecture | A03 §8, §8.1; A02 | Fresh read 11-02 | Correction-rate formula omitted | yes |
| 35 | Zola_Session_Identity_Architecture | A06 §3; A12 | Drafting read; §5–7 re-read 11-02 | Hermes sessions supersede; cross-device split reversed (ARCH-16) | yes |
| 36 | Zola_Sms_Intelligence_Architecture | A08 §9, A11 §5.1; A12, A15 | Fresh read 11-02 | Contacts-only gate, weights and two-step confirm superseded | yes |
| 37 | Zola_SocialGraph_Reasoning_Architecture | A04; A03, A02b, A11 | Drafting read; mention tracker re-read 11-02 | Passive non-correction promotion superseded | yes |
| 38 | Zola_Temporal_Reasoning_Architecture | A05; A03, A06, A10, A11 | Drafting read | Event, mention, validity and coverage distinctions added | yes |
| 39 | Zola_Tool_Authorization_Architecture | A15; A01, A03 | Drafting read; non-goals and constraints re-read 11-02 | Two-step confirm superseded by read-back plus passphrase | yes |

**Not covered by this map** (references, not originals being retired): the `identity/`, `lore/` and `audit/` subfolders and avatar-work notes. They stay in the repo unless separately decided.

---

## 8. Deliberate changes that must not be "restored"

These are decisions, not omissions (ARCH log):
- The PC is the one brain; Android devices are companions, not fallback assistants (ARCH-24, ARCH-29).
- One conversation per person across devices (ARCH-16).
- Heat and proactivity preferences are per person (ARCH-18, ARCH-19).
- Closeness never grants an assumption licence or execution authority (ARCH-10).
- A saved contact grants no trust or importance; unknown senders aren't excluded.
- Silence, repeat retrieval and Zola's own output aren't corroboration.
- Siblings and extended family are worked out at read time (ARCH-14).
- Brian's one-year location history replaces "context only, no tracking history" (ARCH-23).
- Overheard speech outside her conversations is discarded (ARCH-30).
- No on-screen "I have something" cue on the PC; phone notifications are content-free (ARCH-21, ARCH-26).
- Sensitive topics may get a discreet opener (ARCH-04).
- She learns faces and voices; visitors fade after two weeks (ARCH-07, ARCH-37).
- Busy isn't strain; no recovery period (ARCH-50, ARCH-53).
- Head and hair motion wanted; breathing and hologram effects aren't (ARCH-54, ARCH-56).
- Confidence and urgency are separate (ARCH-63).
- Revoking access keeps history unless deletion is chosen (ARCH-66).
- Learning a voice never lets that person start a conversation without the wake word; that's a per-person grant (ARCH-67).

---

## 9. Next

1. Brian signed off on this map (ARCH-68).
2. The 39 copies are deleted **in the single Cursor repo-swap track**, after the Phase 10 lore closeout and before P11PRE. The same track also fixes the stale SOUL and VOICE_CONFIG lines via P4-D25.
