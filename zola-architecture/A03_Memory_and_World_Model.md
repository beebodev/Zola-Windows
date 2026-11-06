# A03 — Memory and World Model

*Draft v0.2, 2026-10-29, revised after ChatGPT's review; overheard-speech rows amended for ARCH-30. Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.**

*v0.3, 2026-11-02 — reconciliation pass after the coverage audit: §5.8 upkeep (audit C04); §8.1 how much she knows (C03); scenarios M, N.*

*Re-audit corrections, 2026-11-02: consolidation row points to §5.8.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:**
- `Zola Memory Hierarchy Architecture.md`
- `Zola_Architecture_Memory_Agency.md` (types, write pipeline, consolidation, recall, lifecycle; the open-loop, tension and resurfacing parts go to A11, and the use governor goes to A14)
- `Zola_Architecture_Perception_Memory.md` (generalised beyond sensors)
- `Zola_SelfModel_Awareness_Architecture.md` (confidence and hedging)
- `Zola_CrossDomain_Correlation_Architecture.md` (identity across sources; situation recognition goes to A10)
- the consolidation and entity-resolver parts of `Zola_Agent_Map.md`

**Governing records:**
- Windows lore: P5, P6, P8-D09, P9-D06/D07, P10-D10/D14
- Brian's direction of 2026-10-19 (§3) and its refinements
- the P11PRE audit scope v1.1, approved
- architecture-doc decisions ARCH-02 to ARCH-07, ARCH-12 and ARCH-13

**Precedence (A01):**
- Locked lore governs current implementation.
- This doc states intent. It **does not decide any Phase 11 question** (DQ-1 to DQ-8 in `PHASE11_AUDIT_SCOPE.md` §6). Where intent depends on one of those decisions, the dependency is named in §15.
- Android numbers in the sources (confidences, thresholds, floors, multipliers) are historical choices, **unvalidated** for Windows.*

---

## 1. Intent

> "The purpose of memory is understanding." (Brian, 2026-10-19)

Memory is not a database of facts. It is Zola's **governed belief model of the world she lives in**. That world includes:
- the people in it
- their vehicles, projects, places, devices and events
- what happened
- what someone said
- what seems to be true now
- what she has worked out for herself

She learns from what she is told **and** from what she observes: email, texts, calendar, contacts and, later, sight and sound (ARCH-02, ARCH-06). She keeps track of:
- where each piece of knowledge came from
- how sure she is
- when it was true
- who may hear it

She revises what she knows as the world changes.

**What this should feel like.**
- A text from Micah about his 4Runner arrives. Later Brian asks, "What's going on with Micah's car?" She knows who Micah is, which car is meant, and that she read it in Micah's text, not that Brian told her.
- A week later Brian asks, "Did he ever fix it?" She remembers the problem and says she hasn't heard anything since, so she doesn't know.

That is the first acceptance test (§16), not the boundary of the design.

**Design general, build the slice** (Brian, 2026-10-19). The model must be able to hold people, vehicles, projects, places, devices and events. Each phase builds only what its experience needs. The architecture must avoid two failures:
- one so narrow it needs replacing later
- one so large it is built before it is needed

**It is her model of her world.** Following the Android taxonomy intent and ARCH-02:
- Zola herself is an entity in the model.
- Each person she knows, Brian included, is connected to her by a relationship of her own (A02b, A04).
- She is a trusted presence for each person in the household (ARCH-03). The model therefore knows *whose* information something is, not only *what* it says.

---

## 2. Principles

These are specific to memory. A01's principles apply too.

1. **Facts belong to entities.** Knowledge attaches to the entity it is about, not to loose text. Roles ("my mechanic", "Micah's school") are relationships between entities, not labels on one. [Vision §4; Android taxonomy intent]
2. **Entities organise; they do not author.** Creating or linking an entity never creates a fact on its own. [P6-D02 rule 4, kept as a lasting boundary]
3. **One writer per kind of knowledge, enforced by structure.** Each kind of knowledge has one write path, and no other code can write that store:
   - facts
   - observations
   - relationships
   - episodes
   - identity links

   Tests prove there is no side door. The Android design had this principle and leaked 21 bypasses (digest §2.2). [P6-D02 rule 1]
4. **Instructions are not evidence.** What someone tells Zola to *do* ("don't bring that up", "remember this") governs her behaviour. What is *true* is weighed from evidence. They are separate mechanisms, never one ranking. A reliable retrieval can carry an unreliable claim. [Digest §2.1 caution; audit Q4]
5. **Observations are not facts.** What she reads or senses enters as attributed evidence. It can earn more confidence through controlled, traceable promotion rules, each approved separately. It is never permanently barred from becoming established knowledge. [Direction refinement; DQ-5]
6. **Untrusted content never instructs.** Text inside a message, event or file is information about the world, never a request to Zola. This holds even when Brian repeats it. [P8-D09; SOUL]
7. **Weak knowledge never silently overrides strong knowledge.** Every conflict is resolved explicitly and logged, or kept open as uncertainty. [Memory Hierarchy §2, §11]
8. **Derived relationships are worked out when needed**, unless a named exception is approved with lineage. [Vision §4; A04, B9]
9. **Retrieval is not persistence, and reading is not permission.** Retrieving something never writes it. Finding something relevant in the background never grants permission to raise it (A10). [P6-D02 rule 6; Memory Hierarchy §3]
10. **Correction keeps history; forget erases.** A correction records what was wrong and what replaced it. Forget removes every copy Zola controls. [P6-D02 rule 5; P6-D06]
11. **Memory failure is honest.** If retrieval fails, she says she doesn't know. She never fills the gap with invention. [Memory Hierarchy, Memory Invention]
12. **Remembering is not interrupting.** Deciding that something is worth keeping (here) is separate from deciding it deserves someone's attention now (A10). [Digest §2.11; audit Q4]
13. **Understood facts, never recordings.** What she keeps from conversation and observation is what she understood, attributed to its source. It is never raw audio or video of conversations. [ARCH-05]
14. **Memory stays local.** No third-party memory service. Model processing of memory content is a separate, stated boundary. [P6-D07]

---

## 3. What she knows about: the world model

### 3.1 Entities

An **entity** is anything that matters enough to be known about over time.

The model must be able to represent at least these types:

| Type | Examples |
|---|---|
| Self | Zola |
| Person | Brian, Bre, the boys, Micah, a guest she has seen |
| Organisation | the school, the bank, a garage |
| Place | the shop, home, the school lot |
| Asset | Micah's 4Runner, Bumblebee, the PC, the phone |
| Project | Zola-Windows, an engine build |
| Event | an appointment, a breakdown, a trip |

Further types can be added as needed: pet, routine, goal, creative work, concept, period. The Android taxonomy is the design reference (17 types), not a target. *Which types the first slice builds is DQ-3.*

Every entity has:
- a stable id
- a type
- names and aliases
- the identifiers that resolve to it (§6)
- an owner/subject scope (§9)
- its own lifecycle (§5.4)

### 3.2 Relationships

Relationships are typed, directed links between entities, carrying the same evidence model as any other knowledge (§4). Examples:
- *Micah* —child of→ *Brian*
- *Micah* —owns→ *4Runner*
- *Brian* —works on→ *Zola-Windows*

Stored relationships are the ones stated or established. Others are derived when needed:
- grandparent, cousin, in-law
- "Micah's grandmother"

A04 owns the relationship vocabulary, derivation, people-specific rules and the sibling question (B9). One vocabulary, not two (digest §4).

### 3.3 Kinds of knowledge (Brian's five-way distinction)

Every piece of knowledge is one of these. They are kept distinct because they age, correct and disclose differently (direction §3).

| Kind | Example | How it behaves over time |
|---|---|---|
| **Event that occurred** | Micah's car broke down on Tuesday | Stays true; it happened |
| **Claim made by a source** | Micah *said* his car broke down | Stays true as a claim, even if the content proves wrong |
| **Condition believed current** | The car is not running | Becomes *unknown* without fresh evidence (A05) |
| **Established fact** | Micah owns a 4Runner | Durable until corrected, replaced or forgotten. Changeable attributes (ownership, job, address) stay valid *as of* their evidence date, and their current applicability fades slowly (A05 §4). |
| **Zola's inference** | He'll probably need a ride Thursday | Never stated as fact; depends on its sources |

Other memory types from the sources fit inside these. They keep their own write and decay rules, but use the same evidence model:
- preference (context-scoped, never one global profile; C7 deferred)
- instruction
- pattern
- correction
- episode (a summarised experience)

### 3.4 Durability layers (vision)

The Android hierarchy's layers survive as **durability**, which is one dimension among several, not the whole model:

| Layer | Holds | Windows today |
|---|---|---|
| Turn | This exact response | Hermes turn |
| Short-term | Recent turns, active entities and topic | Hermes session |
| Session | What this conversation is about; decisions; paused branches (A06) | Hermes session |
| Episodic | Summarised experiences, not transcripts | P6 episodes |
| Established | Durable facts and relationships | `USER.md`/`MEMORY.md` (P6-D01) |
| Behavioural | How people prefer to interact, per context | partial (SOUL lines, P5-D03 facts) |
| Reflective | Slow-changing patterns over many episodes | not built |

No layer absorbs another's job. Durability is **not** the same as provenance: a stated fact and an inferred one can both be durable. That is why §4 exists.

---

## 4. The evidence model

Every piece of knowledge carries six separate dimensions. They are never collapsed into one label or one score (matrix v1.2 §3.1).

| Dimension | Describes | Example |
|---|---|---|
| **Acquisition / source** | How Zola obtained it | Brian said it; read in a text; seen by camera; worked out by Zola |
| **Attribution** | Who made the underlying claim, and the exact record that supports it | Micah, in the text received Tue 4:12 pm |
| **Confidence and conflict** | How sure; whether contrary evidence exists | Moderate; no contrary evidence |
| **Time and validity** | When said, observed or retrieved; when the event happened; when the claim is or was valid | Reported Tue; event Tue; condition unrefreshed since Tue |
| **Lifecycle and storage** | Candidate, active, provisional, stale, contested, superseded, forgotten; where the record lives | Active observation |
| **Privacy and permitted use** | Whose information it is, who may be told, how it may be used | Micah's and Brian's; usable in Brian's conversation |

**Rules:**
- *Uncertain* and *conflicting* are confidence states, not sources. A retrieved email can carry an uncertain claim, and something Brian said can go out of date.
- Confirmation **adds** to a claim's history. It never erases how the claim first arose.
- "Brian said X about Micah" establishes the attributed statement, not X as a trait of Micah. Reliable retrieval of an email does not make everything its author asserts true.
- A lower-confidence source never overrides a higher one silently. The discrepancy is kept and logged.
- **Output follows provenance** (from Memory Ethics). She states established facts plainly and attributes observations ("Micah texted that…", never "you told me…"). She marks inferences as hers ("I'd guess…") and hedges uncertain ones (§8).

How the five sources' provenance lists map onto these dimensions:
- Memory Ethics: USER_STATED, USER_CONFIRMED, PERCEPTION_DERIVED, SYSTEM_INFERRED, TOOL_PROVIDED, CONVERSATIONAL_IMPLICIT
- Memory Agency authority classes
- Perception Memory tiers
- relationship edge sources

The map goes into the coverage map. The labels themselves are not carried forward.

---

## 5. How knowledge is written

### 5.1 One write door per kind

Every potential write is first classified as one of:
- ignore
- short-term only
- session only
- episode candidate
- established-fact candidate
- observation candidate
- preference candidate
- reflective candidate

Durable writes go through the single write path for their kind. That path checks:
- how explicit the source was
- confidence
- sensitivity
- conflicts with existing knowledge
- the source
- intent (did someone mean this to be remembered?)
- the destination
- how the write merges
- an audit trail that can explain and reverse it

[Memory Hierarchy §4]

*Who the writer of observations is, and how it relates to the P6 episode writer, is DQ-4.*

### 5.2 Retention selection

Most of what she observes should leave no durable trace. Before anything is kept, a **retention selection** decides whether it is worth remembering at all, and as which kind (§3.3).
- Salience signals inform it: someone said it matters, a personal story, repetition across conversations, strong emotional engagement, effect on future decisions, a long-running project, a correction, something left unfinished, genuine novelty, and especially **a break in an established pattern**. Repeating what she already knows adds reinforcement, not a new memory. [Memory Agency, salience criteria]
- Salience is a gate on keeping, not a measure of importance to Brian right now (principle 12).
- The Android thresholds (0.40 discard / 0.65 active) are unvalidated.

### 5.3 Promotion rules by source

The evidence, attribution, lifecycle and privacy contracts are shared. *When* a claim becomes established knowledge depends on its source. **Each rule below is vision only; each actual rule is a separate decision (DQ-5).**

| Source | Enters as | Shape of promotion |
|---|---|---|
| **A person's own deliberate statement to Zola** | That person's statement | Explicit facts saved, as today (P5-D03). Venting, sarcasm and rhetorical statements enter at lower authority and don't harden without confirmation ("social deniability"). |
| **Retrieved records** (email, calendar, texts, notifications) | An attributed claim and/or event, recognised as soon as read | Not made to wait for recurrence. Confidence may rise through corroboration, source reliability, explicit confirmation or later observations. |
| **Contacts** | A **known-sender** entity seed | Establishes that a name, number or address belongs together. Establishes no importance, trust or closeness (A01 §1.2). |
| **Overheard speech** (ARCH-05; ARCH-30) | Only within a conversation Zola is part of: the speaker's attributed statement, never the listener's. When she isn't part of the conversation, it is discarded and never kept (ARCH-30) | Same as retrieved records. Never written as Brian's statement. Ambient media (TV, radio) is not a speaker. |
| **Sensors** (camera, presence, environmental sound; A09) | An observation | Recurrence across sessions and contexts, no contradiction, and for a new entity a natural confirmation ("I've seen a silver truck a few times. Someone you know?"). |
| **Zola's inferences** | An inference | Worked out at read time where possible. Never stated as fact. Depends on its sources (§7). |

### 5.4 Lifecycle

A piece of knowledge moves through:
- **candidate**: noticed, not yet kept
- **provisional**: kept, not yet trusted, e.g. a trait someone asserted while venting
- **active**
- **reinforced**
- **stale**: unrefreshed, so confidence falls or the condition becomes unknown
- **contested**: conflicting evidence, kept open
- **superseded**: corrected or replaced; history kept
- **forgotten**: erased; a content-free tombstone where needed

**Three different operations, never confused:**

| Operation | What it is | Example |
|---|---|---|
| **Policy expiry** | A retention rule removes content when its limit is reached | Raw mail and text content after 7 days (P9-D07); the recurrence record's own limit (§5.6) |
| **Confidence change** | Knowledge loses confidence or becomes "unknown" over time. It is still kept. | "The car is broken" becomes "status unknown" |
| **Forget** | A person asks for something to be erased (§12) | "Forget Micah's car trouble" |

**Confidence change has limits.** It applies to patterns and conditions, never to identity (who an entity *is*). It never spreads by itself to related facts; those follow truth maintenance (§7). [Perception Memory, Layer 4]

"She never forgets on her own initiative" means she never decides by herself to delete knowledge she holds, outside the approved retention rules. Stale knowledge is surfaced for confirmation, not silently deleted. [Memory Agency; Perception Memory]

### 5.5 Evidence independence and self-reinforcement

Confidence rises only on **independent** evidence:
- A repeated retrieval is not corroboration of the original claim. Neither is a forwarded copy, a duplicate intake, a generated summary or anything Zola herself said.
- Copies of one claim count once. Lineage is tracked so that copies can be recognised.
- **Silence is not confirmation.** "Brian didn't correct me" never reinforces a claim, and never promotes a characterisation of a third party. Both Perception Memory and Social Graph had rules like that. They are replaced.
- Explicit confirmation and fresh attributed evidence may reinforce a claim, under the approved rules.
- *Open:* when Brian repeats what a message said ("yeah, Micah's car broke down"), is that his own statement, a confirmation, or an echo of the message (audit Q4)?

### 5.6 Recurrence needs a durable record

Promotion by recurrence (sensors, unknown entities) needs evidence that survives across sessions. The Perception Memory design kept that evidence in a session-only buffer, which cannot prove a multi-session pattern.

Intent: a **bounded persistent evidence record**. It keeps the minimum needed to count recurrence: what was observed, when, the source and lineage. It has its own retention limit, joins the forget cascade, and is never a copy of the raw content. *Size and retention are DQ-7.*

### 5.7 Never promotable

These are lasting boundaries, kept from Perception Memory ("What Perception Cannot Promote") in their original wording and scope:
- **Emotional state as a person type.** An emotional-state assertion about the user never becomes a "type of person" fact ("Brian is a stressed person").
- **Who an unconfirmed person is.** Zola cannot assert who an unconfirmed person is.
- **Sensing plus hearsay.** Inferences that combine perception with hearsay cannot be promoted **without the user's confirmation**.

**Scope.** The source lists a fourth item: "any fact whose world graph form would assert something the user has not confirmed about themselves or others". It is kept, **for promotion from sensing (camera, presence, environmental sound) only**. Applied to every source, it would contradict ARCH-06 (she learns from attributed observations). Other sources follow §5.3 and their approved promotion rules.

**Identity claims are evidence, not identity.** "Mike says this is his cousin Dave" is useful attributed evidence. Zola keeps it, attributed to Mike, as a candidate identity. It does not establish who the person is until confirmed under DQ-2's rules. What is barred is an *unsupported* identity assertion, not the evidence.

### 5.8 Upkeep: consolidation and review

Kept from Memory Hierarchy §§6–7, Memory Agency's consolidation loop and Agent Map Agent 2 as responsibilities. **When it runs is open (§15); what it must do isn't.**

**After a conversation, with the fuller picture:**
- **Re-judge pending candidates.** Something that looked minor mid-conversation may matter once the whole conversation is known, and the reverse.
- **Record what mattered:** meaningful outcomes and anything left unresolved, as episodes (A06 §3).
- **Release what was only for the moment:** short-lived working state is let go.

**Periodically:**
- **Review stale reflections and patterns.** A pattern the evidence no longer supports is revised or retired, not left to pile up beside a contradicting one.
- **Catch up after missed upkeep.** After a crash or a long gap, the work is done once. It never duplicates episodes and never brings back forgotten content (§12).

**Rules**
- **Every change goes through its normal owner and write door** (§5.1), with provenance, privacy and forget intact.
- **Never on the critical path of live speech** (A01 principle 5).
- **Memory upkeep never closes an operational watch on its own** (A11 §6.3).

---

## 6. Identity: one entity, many identifiers

**Intent.** One person is one entity, whichever source mentions them. That covers:
- Google Contacts entries
- email addresses
- phone numbers, including RCS senders that aren't numbers
- names and aliases in conversation
- memory entities
- later, a learned voice and face (ARCH-07)

Her understanding of Micah comes together in one place. [Direction §3; VISION_ALIGNMENT_REVIEW G1]

**One resolver.** A single person resolver maps identifiers to entities, and nothing else resolves people. The P10 Track 5 contact index is its first part: one person, all their numbers and addresses. One resolver is an architectural boundary (P10-D18). Google Contacts as its only source is a temporary limit that Phase 11 identity extends.

**Rules:**
- **Conservative.** A false link is worse than a missed one. When a match is ambiguous, she does not guess.
- **Clarify, don't assume.** Examples of ambiguity: two Micahs, a shared family address, a vehicle she doesn't know yet. She keeps the reference unresolved until there is enough evidence, or she asks naturally ("Which Micah — your son?") with options that carry entity ids.
- **Which links may be automatic and which need confirmation is DQ-2.** Example candidate: an exact phone-number match to a contact. *Not decided here.*
- **A guest she cannot identify** is a person entity only as a noticed, unnamed candidate (ARCH-05, ARCH-07). It carries no assumed identity until confirmed.
- **Recognition identifies; it never grants permission** (A01 §1.3; ARCH-07, ARCH-12). A low-confidence voice or face match leaves the speaker unverified, so they are treated as a guest.

---

## 7. Correction, conflict and derived knowledge

- **Corrections** are high priority. They record the wrong value, the replacement, when and why, so the mistake isn't re-learned. They never overwrite history in place. [Memory Ethics; digest §2.7]
- **Supersession reaches every copy.** That includes every index, summary, cached context, brief and search structure. A superseded fact must stop being served everywhere. Android's derived copies kept serving corrected facts (digest §2.7). Hedging does not fix wrong evidence.
- **Truth maintenance.** An inference depends on its sources. When a source is corrected, superseded or forgotten, inferences derived from it are re-evaluated or withdrawn.
- **Conflict** is kept, not hidden. Two pieces of evidence that disagree stay *contested*, and she can explain the disagreement. Nothing is silently overwritten, and the conflict is logged with both values.
- **Example (4Runner checks 4–6).** Micah later says it's fixed: the earlier report stays true, and the condition changes. Brian says "that was his other car": the link is revised, and the original text is still attributed to Micah.

---

## 8. Confidence and how she speaks about it

Her language reflects how sure she is. Hedging is part of the correction mechanism, because it invites correction. [Self-Model Awareness]

| State | Sounds like |
|---|---|
| Established, fresh | "Micah's 4Runner…" |
| Attributed observation | "Micah texted Tuesday that it broke down." |
| Ageing condition | "Last I heard it wasn't running. I haven't heard anything since." |
| Inference | "I'd guess he'll need a ride Thursday." |
| Gap | "I don't know. I haven't heard." |

**Rules (from Self-Model Awareness):**
- She surfaces a gap only when it is relevant.
- The same epistemic rules apply to what she knows about Brian, third parties and herself.
- After a long absence she doesn't start hedging everything. Well-reinforced knowledge keeps its strength. *The Android cap of 30 days' effective age after a 14-day gap is unvalidated.*
- She never shifts context mid-response.
- *Unvalidated:* the Android hedge thresholds and the confidence-ageing formula (confidence × age × authority, computed at read time). The principle stands: **ageing is computed when read, not stored.**

### 8.1 How much she knows, and about herself

Kept from Self-Model Awareness as behaviour, not as its formulas.

**One claim vs the whole subject.** Confidence in a single fact is different from how much she understands an entity or a subject overall:
- "I know which truck this is" (one well-established fact).
- "…but I know little about how it's set up now" (thin, old or unreliable knowledge of the subject).

**Depth is evidence about breadth, freshness and reliability.** It is never a closeness score and never a permission (A02b; A15).

**Why a gap matters.** She can say which gap matters for the decision at hand: "I don't know whether Micah's car is fixed, and that matters for whether he needs a ride Thursday." A gap is raised only when it's relevant (§8).

**Once is enough.** A gap already raised in this conversation isn't raised again.

**Gaps that are protected.** A topic she's been told not to use, or a sensitive category she doesn't hold, is an **intentional gap**. It is never a prompt to go and find out (A14 §5.3).

**About herself (read-only).** She can describe her own learned behaviour, known weaknesses and repeated mistakes: "I keep getting the shop hours wrong." This is understanding, not control:
- Self-observation never rewrites her identity (A02) or her memory.
- She doesn't claim to have fixed the cause of a repeated mistake just because she's noticed it.
- **Her locked identity is never hedged** (A02). Learned patterns are held with the confidence their evidence supports.

**Read-only, and never shown as numbers.** The self-model only reads. It writes nothing, changes no belief and makes no correction decision; what it produces reaches speech only through the normal context assembly (A06) or A10. Confidence and depth shape her wording and are never shown to anyone as scores.

**Not carried from Android:** the correction-rate formula and score bands. Being corrected often in an area may make her more careful there, but a correction *improves* what she now knows rather than counting against it, and silence is not evidence that she was right (§5.5).

---

## 9. Several people, one memory (ARCH-03, ARCH-05, ARCH-12)

The household rules mean memory must know more than *what*. A01 §1.4 assigns these questions to this doc.

**Every piece of knowledge records four things separately (ARCH-13):**
- **Speaker or source.** Who said or wrote it, or which sensor or record it came from.
- **Subject.** Who or what it is about. There may be several.
- **Intended recipients.** Who it was addressed to:
  - Micah's text to Brian → Brian
  - Bre telling Zola something → Zola
  - speech between others, in a conversation Zola is part of → those addressed, not Zola (speech she isn't part of isn't kept at all, ARCH-30)
- **Permitted audience.** This is *derived* from the first three by A14's policy. It is never stored as a free-form label.

**Default audience (ARCH-13, as amended).** By default, these people may hear it:
- the speaker
- the intended recipients
- the subject, but **only for plain facts about the subject's own affairs** (their appointment, schedule, car, plans)

The speaker's views, observations or discussion *about* the subject stay with the speaker. Being the subject never opens someone else's private conversation. When Zola cannot tell which kind a statement is, it stays with the speaker.

Anyone else needs the speaker's approval. For a sensitive topic (A14), they also need the subject's approval.

**Examples:**
- **A message sent to Brian.** Micah's text to Brian may be told to Brian, because he was its recipient. It is not told to Bre unless it is shared information. This is the 4Runner case.
- **Something about another person.** Brian tells Zola "Bre has a doctor's appointment Tuesday." Zola may mention it to Bre, because she is the subject. She does not mention it to the boys without Brian's approval, and, because it is health-related, Bre's too.
- **Something private.** Bre tells Zola she's planning Brian's surprise party. It stays from Brian (ARCH-03).
- **A view about someone.** Bre privately tells Zola "Brian's been stressed lately". This is Bre's observation about Brian, not a fact about his own affairs, so it stays with Bre.
- **Something overheard.** *Amended by ARCH-30:* Bre on the phone in the kitchen is **not kept at all**; Zola isn't part of that conversation. If Bre says something to Brian within a conversation Zola is part of, it is kept as Bre's statement, addressed to Brian.

**Forget and use by role (ARCH-13):**
- The speaker can make Zola forget their own statement.
- The subject can ask Zola not to use it. That suppresses its use and disclosure. It does not erase the speaker's statement.

**Retrieval is scoped to the person in the conversation.** The governed context-assembly path (§10) brings in only what the person Zola is talking to may receive:
- Bre's private statements never enter Brian's conversation.
- Brian's never enter Bre's.
- Each person's approval can open their own information (ARCH-03).
- The two exceptions are A14's: an unauthorised attempt, and safety.

**Shared household information** is, today, only the family calendar (ARCH-03, C11). It can be retrieved for any household member. Nothing becomes shared without Brian's explicit decision.

**Guests and unverified speakers:**
- What they say is kept as their attributed statements (ARCH-05).
- They receive no household or private information.
- Nothing they say becomes a household member's statement.

**No recordings.** Conversation in the room becomes understood facts attributed to their speaker, never audio (ARCH-05).

**Conversation handoff (required outcome).** Scoping what memory retrieves is not enough. Private information can already be sitting in the active conversation. When one person's conversation ends and another person takes over at the same endpoint, none of these carry into the new person's conversation:
- the first person's transcript
- their cached context and injected memory
- their pending or queued replies

A06 owns the mechanism. This doc and A14 require the outcome. Scenario K tests it.

---

## 10. Retrieval and context

- **One governed context-assembly path** owns what reaches a conversation or a background evaluator:
  - attribution
  - deduplication
  - precedence
  - privacy (per §9)
  - the size budget

  Several components may supply information; one assembles it. Today there are at least two injectors: `zola_memory` prefetch and `zola_workspace` surfacing. *Who owns the path is DQ-8.* [Audit Q7; digest §2.9]
- **Retrieval is intentional.** It selects what this moment needs. It does not dump everything. A socket-size question gets no personal history. [Memory Hierarchy §3, §10]
- **Read modes:**

  | Mode | Use |
  |---|---|
  | Direct recall | Asked |
  | Contextual | Relevant, not asked; conservative |
  | Continuity | "what were we talking about", A06 |
  | Relationship reasoning | A04 |
  | Background scan | A10's evaluators |

  **A background scan never grants permission to speak** (A10).
- **Background use without a synthetic turn.** Judgment components (Phase 12) read memory through supported integration points in plugin code, never by borrowing a Hermes conversation turn. [P9-D01; direction §3]
- **She doesn't announce memory use.** Memory informs her answers without her saying "I remember that…" or "based on my memory…". Saving a new fact is different, and keeps P5-D03's brief mention.
- **Transcript search only when asked.** Searching past raw conversations happens only on request (P5-D06). Automatic retrieval from curated memory and observations is a different operation and is not restricted by this.
- **Retrieval quality must be measured.** Phase 6 associative recall was 0 of 4 (S46). Local semantic scoring is a candidate fix. It would need an install decision (P2-D17) and its own measurement, within Hermes's 8-second prefetch budget.

---

## 11. Remembered situations and operational watches

These are two different things with two owners (matrix §3.4):
- **"The 4Runner problem is unresolved"** is a *remembered situation*, owned here.
- **"Tell me when the ECU email arrives"** is an *operational watch*, owned by A11 and the proactive store (P9-D06; the separation is an existing boundary).

They are linked by stable ids. A11 defines which owner closes what and how resolution passes between them. Neither may edit the other's status. **An unresolved topic never silently becomes a watch.** A watch is created only from a person's own words or their acceptance of an offer (P9-D09).
- **Stated commitments are the defined case (ARCH-15).** When Brian states a commitment with a time ("I need to renew the registration by the 15th"), the remembered situation and a linked watch are created together. No offer step is needed.
- **Check-ins and completion belong to A11.** A11 owns check-ins and completion verification; closing the watch needs Brian's confirmation.
- **Vague intentions with no time are remembered only.** An in-between case gets one question: "keep track of it?" (C12).
- **Deadlines found in observed sources** (an email, a bill) are offered, never auto-watched (C13). Untrusted content never creates a watch.
- **Still never a watch:** ordinary unresolved topics ("the 4Runner problem").

---

## 12. Forget

**Forget removes the selected information from governed memory stores and everything derived from them** (P6-D06), extended to people and numbers (P10-D14). **Current chat transcripts remain in `state.db`** (P5-D10). That is an explicit exclusion from today's forget, not an outside system. Forget is a different operation from policy expiry and from confidence change (§5.4).

**What each forget scope covers.** The details are DQ-7.
- **One observation, an entity, or future learning.** Forgetting one observation, forgetting an entity ("forget Micah"), and suppressing future learning about it are distinct scopes.
- **Replay vs genuinely new information.** Replay or re-ingestion of a forgotten source is suppressed: a resent text doesn't bring it back. Genuinely new information about the same subject is kept normally, unless Brian asked to suppress future learning.
- **Everything derived.** Forget reaches summaries, indexes, cached context, inferred links, promoted knowledge, identity links, the recurrence record and, later, voice and face embeddings.
  - Brian decides whether a conclusion with independent support survives with revised provenance or is removed.
- **Tombstones.** Content-free tombstones are kept only where needed to prevent re-learning, never as another copy.
- **Background work.** Queued background work (consolidation, distillation, ranking) must not write forgotten content back.

**What forget does not cover:**
- **Explicitly excluded today:** `state.db` chat transcripts (P5-D10, temporary limit, accepted risk).
- **Outside Zola's systems, no deletion promised:** provider-side copies (for example, content already sent for model processing) and the phone's own message store.

**Who may forget what:** the speaker forgets their own statement, and the subject can stop its use (§9, ARCH-13). A14 holds the full rules.

Android's forget-all repeatedly missed stores. Every store has a forget-completeness test (digest §2.12).

### 12.1 Every memory decision can be explained

Kept from Memory Hierarchy "Observability and Auditability" as a requirement; the log tag names are build detail. From records, not recollection, it must be possible to answer:
- Why was this brought into the conversation, or left out?
- Did this remark produce a write candidate? Was it kept or rejected, and why?
- Did a weaker source try to override a stronger one?
- Did upkeep (§5.8) change it?
- Has it been forgotten, suppressed or expired?

Records hold decisions and reasons, never the private content itself beyond what the store already holds (A14).

---

## 13. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| Durable facts in `USER.md` / `MEMORY.md` (4400 / 4000 chars, `[tag]` convention); memory tool only | live-tested | P5, P6 closeouts | C4, P5-D05, P6-D01 |
| Zola saves lasting facts on her own, with a brief mention | live-tested | P5 | P5-D03 |
| `zola_memory`: local SQLite and full-text store, fact index rebuildable from the files, entities as organisers | live-tested | P6 | P6-D01–D03 |
| Episodes from a background summariser; Brian's own turns only | live-tested (blind test C2 passed) | P6 | P6-D04, G-BRIAN-ONLY |
| Ambient time, gap awareness, "roughly when" recall | live-tested | P6, P7 | P6-D05 |
| Forget cascades through every provider copy; `state.db` not redacted | live-tested | P6 Tracks 4–5 | P6-D06, P5-D10 |
| Memory local, no third-party service | live | — | P6-D07 |
| Tainted session: saves only from Brian's own words, after a save phrase | live-tested | P8 | P8-D09 Option A ("for now") |
| Consolidator attributes external content as something Zola read | implemented | P8 | P8-D09 |
| Raw **mail** content at most 7 days in `proactive.db`, then ids and times | live-tested | P9 closeout | P9-D07 |
| Raw **text and notification** content under the same 7-day limit | shipped (P10) | P10 closeout | P9-D07, P10-D03 |
| Forget by person or number reaches phone items and watches | shipped (P10) | P10 closeout | P10-D14 |
| Contact index (numbers and addresses per contact, read-time match): the one person resolver | shipped (P10) | P10 closeout | P10-D10, P10-D18 |
| Associative recall | measured weak (0 of 4) | P6 blind test | S46 |
| Observations surviving as memory | **not built**. What she only observed is gone after 7 days. | VISION_ALIGNMENT_REVIEW G3 | — |
| One identity per person across sources | **not built** (contact index is a start; Contacts-only source is a temporary limit) | G1 | P10-D18; S96 |
| Structured relationships; entity-centric facts | **not built** (facts are text lines) | G4 | S14 |

---

## 14. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| Facts are text lines in two flat files; the store is a derived index | temporary limit | — | P6-D01; fact authority is DQ-1, decided on evidence (direction §3) |
| Tainted sessions save facts only in Brian's own words | temporary limit | — | P8-D09 "for now"; provenance-aware memory replaces it (Brian's classification, 10/19) |
| Episodes only from Brian's own turns | lasting boundary for *conversation episodes*; observations need their own attributed path | — | VISION_ALIGNMENT_REVIEW row 8 |
| Nothing she only observes survives 7 days | temporary limit (the gap); deferred capability (observational memory, P11) | — | Brian 10/19 |
| Raw communication content at most 7 days | lasting boundary unless explicitly changed | — | Brian 10/19 |
| Distilled observations must not be a loophole for storing whole messages | lasting boundary | — | Brian 10/19; the testable definition is DQ-7 |
| One voice = Brian; no per-person memory scoping | temporary limit | — | ARCH-03, ARCH-12 |
| `state.db` keeps raw transcripts after forget | temporary limit | yes | P5-D10 |
| No at-rest encryption of memory beyond BitLocker | temporary limit | yes | H4 |
| Weak associative recall | temporary limit | — | S46 |
| Entities don't author facts | lasting boundary | — | P6-D02 rule 4 |
| Retrieval never becomes persistence | lasting boundary | — | P6-D02 rule 6 |
| Never-promotable list (§5.7) | lasting boundary | — | Perception Memory |
| No recordings of conversations | lasting boundary | — | ARCH-05 |
| Reflective memory; behavioural memory per context | deferred capability | — | C7 deferred |
| Memory from sensors (camera, presence) | deferred capability | — | A09 |

---

## 15. Open questions

**Phase 11 decisions (from the approved audit scope; not decided here):**
- **DQ-1.** Fact authority and Hermes integration.
- **DQ-2.** Identity-resolution rules.
- **DQ-3.** Entity types and relationships in the first slice.
- **DQ-4.** The observation model, its writer, and retention selection.
- **DQ-5.** Each promotion rule, separately.
- **DQ-6.** Background processing of message content. This partly reverses P10-D11. Includes the privacy page.
- **DQ-7.** Retention and size limits for observations and the recurrence record; forget scope.
- **DQ-8.** Owner of the governed context-assembly path.

**From the household decisions:**
- **Q-A. Whose information is a statement about someone else?** *Resolved by ARCH-13 (2026-10-29), §9.*
- **Q-B. Repeating a message.** When Brian repeats a message, is it his statement, a confirmation, or an echo (§5.5)? This is audit Q4, raised here because it decides whether one claim gets counted twice.

**Design questions carried from the sources (for the P11 audit or later):**
- When consolidation runs: after every session, only after high-value ones, or on a schedule.
- Whether Brian can review pending durable writes before they commit.
- Whether confidence is ever shown in the UI.
- Whether reflective memory is user-editable.
- Retention for unreinforced low-confidence episodes.

---

## 16. Acceptance scenarios

**Phase 11 first test: the 4Runner scenario** (audit scope §2). This is the minimum Phase 11 must make work, not the design boundary.
1. **Arrives.** A text from Micah about his 4Runner arrives.
2. **Asked later.** Brian asks what's going on with Micah's car. She knows Micah (his son), the vehicle and the source (Micah's text, not Brian).
3. **A week later.** The raw text is gone. Brian asks if Micah fixed it. She remembers the problem and says the current status is unknown.
4. **Changing status.** Micah later says it's fixed. She distinguishes the earlier report from the new status.
5. **Correction.** "That was his other car." She revises the link, and the original stays attributed to Micah.
6. **Conflict.** Evidence disagrees. She keeps or explains the uncertainty and overwrites nothing.
7. **Ambiguity.** Two Micahs, or an unknown vehicle. She leaves it unresolved, or asks. She does not guess.

**Negative checks:**
- **Untrusted content stays in its place.** External content cannot:
  - bypass promotion rules
  - pose as Brian
  - change a relationship without the required evidence
  - raise its own confidence
  - instruct
- **No false corroboration.** Repeats, forwards, duplicate intake and Zola's own summaries never corroborate.
- **Forget holds.** "Forget Micah's car trouble" and "forget Micah" behave as defined, and a resend doesn't bring it back.
- **Attribution is visible.** "Micah texted that…", never "you told me…".

**Carried from Memory Hierarchy** (scenarios A–G, adapted):
- **A. Recent topic.** Brian leaves mid-topic, returns, and asks what they were talking about. She recalls it from session memory. Nothing durable is written unless already approved.
- **B. Durable fact.** A factual question is answered from established knowledge. An episode never overrides it.
- **C. Emotional episode.** Returning to a personal topic brings back the relevant episode briefly, without over-exposing sensitive details.
- **D. Weak preference.** "I kind of like shorter answers when I'm in the shop" becomes a preference for shop conversations only, not a global rule.
- **E. Correction.** A corrected vehicle fact goes through the write path. Both values are logged.
- **F. Topic return.** Belongs to A06.
- **G. Failed retrieval.** The memory service fails. She does not invent, gives a bounded answer, and logs the failure.

**From the household decisions:**
- **H. Privacy by person.** Bre tells Zola something privately. Later Brian asks a related question, and Zola does not use or reveal Bre's statement. Bre approves; then she may.
- **I. Unverified speaker.** A voice resembling Bre's, but not verified, asks about Bre's calendar. Zola treats the speaker as a guest and reveals nothing.
- **J. Guest speech.** A guest mentions a fact in conversation. It is kept as the guest's attributed statement, never as Brian's or the household's. No audio is kept. The guest can still hold an ordinary conversation with Zola.
- **K. Conversation handoff.** Bre has a private conversation with Zola. Brian then takes over at the same endpoint. None of the following enters his conversation:
  - her transcript
  - her cached context or injected memory
  - her pending replies

  Asked about what she said, Zola reveals nothing.
- **L. Recipient and subject.**
  - Micah texts Brian. Zola may tell Brian what Micah said. She does not tell Bre.
  - Brian tells Zola about Bre's doctor's appointment. Zola may mention it to Bre, but not to the boys without approval from Brian and from Bre.

- **M. Fuller context.** Mid-conversation, "the supplier's moving" looks minor. By the end it's clear it changes Brian's whole parts order. Upkeep keeps it. After a crash, upkeep runs once on restart: no duplicate episode, and nothing forgotten comes back.
- **N. Depth, not just a fact.** Asked about Micah's truck, she says she knows which truck it is but little about its current setup, and that her last news is three weeks old.

---

## 17. Coverage of the source docs

**Status:**
- **verified**: the destination section exists and was checked against the source (this doc).

None of these source docs may be deleted while any of its rows is unresolved.

**How the rows were checked.**
- Memory Hierarchy rows: checked against a fresh full read of that doc.
- Memory Agency, Perception Memory, Self-Model Awareness and Cross-Domain rows: first checked against the full-read notes; **re-checked against a fresh full read on 2026-11-02** (coverage audit). That read added §5.8, §8.1, §12.1, the salience signals in §5.2 and the limits on confidence change in §5.4.


| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Memory Hierarchy: vision, philosophy ("memory must be earned"), non-goals | §1, §2 | merged | verified |
| Memory Hierarchy §1 layers | §3.4 | merged; durability split from provenance | verified |
| Memory Hierarchy §2 authority order | §2 p4, p7; §4 | merged; instruction authority separated from evidence | verified |
| Memory Hierarchy §3 read modes | §10 | merged | verified |
| Memory Hierarchy §4 write classification, DWA | §5.1 | merged | verified |
| Memory Hierarchy §5 promotion, §6 decay | §5.3, §5.4; A05 §4 | merged | verified |
| Memory Hierarchy §7 consolidation | §5.8; §5.1, §15 | retained (upkeep contract) | verified |
| Memory Hierarchy §8 topic stack | A06 §4.1 | moved | verified |
| Memory Hierarchy §9 emotional weighting | §5.2 | merged | verified |
| Memory Hierarchy §10 injection rules | §10 | merged | verified |
| Memory Hierarchy §11 conflict | §7 | merged | verified |
| Memory Hierarchy §12 privacy | §9; A14 §3–§5 | merged | verified |
| Memory Hierarchy §13 Kotlin contracts | — | intentionally dropped: platform plumbing; the audit-trail intent is kept in §5.1 | n/a |
| Memory Hierarchy failure modes | §2, §5, §7, §12 | merged; ambient-speech rule reconciled with ARCH-05 (attributed to the speaker, never as Brian) | verified |
| Memory Hierarchy log tags, queryable questions | §12.1 | questions retained as requirements; tag names left to the build plan | verified |
| Memory Hierarchy open questions | §15 | preserved | verified |
| Memory Hierarchy scenarios A–G | §16 | preserved (F → A06) | verified |
| Memory Agency: belief model, memory types | §1, §3.3 | merged | verified |
| Memory Agency: write pipeline, salience, lifecycle | §5 (salience criteria §5.2); A14 §5.4 (restrictions only tighten) | merged; thresholds unvalidated | verified |
| Memory Agency: recall pipeline, hedged language | §8, §10 | merged | verified |
| Memory Agency: consolidation loop (session-end re-scoring, summary, release; nightly review) | §5.8; §5.1, §15 | retained as responsibilities; schedule open (§15) | verified |
| Memory Agency: open loops, tension, resurfacing | A11 §6, §7.2, §7.3; A03 §11 | moved | verified |
| Memory Agency: memory use governor | A14 §5.4 | moved; "when unsure, use silently" replaced by "withhold" | verified |
| Perception Memory: observations aren't facts; layers; promotion; authority tiers | §2 p5, §4, §5.3, §5.6 | merged; generalised to all sources; session-only buffer replaced by §5.6 | verified |
| Perception Memory: never promotable | §5.7 | preserved in original wording; fourth item limited to sensing (ARCH-06) | verified (re-read 10/29) |
| Perception Memory: reinforcement by non-correction | §5.5 | superseded (silence is not confirmation) | verified |
| Perception Memory: world-fact drift, read-time ageing | §5.4, §8; A05 §4 | merged; numbers unvalidated | verified |
| Perception Memory: camera, presence specifics | A09 §4, §5.2 | moved | verified |
| Self-Model Awareness: hedging, gaps, absence scaling, same rules for all | §8 | merged | verified |
| Self-Model Awareness: corrected facts excluded from retrieval | §7 | preserved | verified |
| Self-Model Awareness: MetaKnowingConfidence, GapSignalProducer relevance, SelfBeliefBlock, read-only authority | §8.1 | retained as behaviour; correction-rate formula and score bands intentionally omitted | verified |
| Self-Model Awareness: SelfBeliefBlock reads identity, never redefines it | §8.1; A02 §3, §6 | retained | verified |
| Cross-Domain Correlation: one join authority, conservative matching, read-time derivation | §6, §7 | merged | verified |
| Cross-Domain Correlation: relationship weight from frequency | §5.3 Contacts row; A04 | superseded (frequency is evidence, not importance; F8) | verified |
| Cross-Domain Correlation: situation recognition, Daily Brief consumer | A10 §8; A11 §5.1 | moved | verified |
| Cross-Domain Correlation: ContactRelationshipIndex privacy (signals not content; deletable; rebuilt on revocation) | A10 §8; A14 §7.1 (ARCH-66) | retained | verified |
| Cross-Domain Correlation: future scope (topic matching, documents, texts, patterns over time) | A10 §8 | **deferred but retained** | verified |
| Perception Memory: candidate dismiss/defer; contradiction resets recurrence | A09 §5.2 | retained | verified |
| Perception Memory: drift excludes identity, doesn't cascade | §5.4 | retained | verified |
| Perception Memory: phase sequencing, decay tables, Firestore paths | — | intentionally omitted (Android phases and numbers) | verified |
| Agent Map: agent 2 (consolidation), agent 9 (entity resolver, contact index) | §5.1, §6 | merged | verified |
