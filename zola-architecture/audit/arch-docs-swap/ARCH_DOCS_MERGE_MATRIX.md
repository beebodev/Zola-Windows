# Zola-Windows Architecture Docs — Proposed Merge Matrix

*Historical record, kept for traceability. The doc structure below was approved as ARCH-01 (2026-10-29); every later decision is in `ARCH_DOCS_DECISIONS.md`. In the repo this file lives in `zola-architecture/audit/arch-docs-swap/`.*

*v1.2, 2026-10-29. Author: Claude. Status: **proposal — awaiting Brian's approval.** Nothing in the repo has been written or moved.
Recommendations here are Claude's (with ChatGPT's review folded in). They are not Brian's decisions.*

**History.** v1.0 was built from headings and openings. v1.1 followed a full read of all 39 docs; per-doc notes are in
`claude/ARCH_DOCS_READ_NOTES.md`. v1.2 folds in ChatGPT's review (2026-10-29):
- Three of Claude's findings are corrected (provenance, governor chain, self-modification).
- Two issues are added (recurrence persistence, self-reinforcement).
- The shared evidence model, the memory/watch distinction, the evidence standard for "as built" and a section-level coverage map
  are now defined.
- Factual reconciliations (§4) are separated from choices only Brian can make (§5).

**Scope.** The 39 docs at the top level of `zola-windows/zola-architecture/`. Out of scope: `identity/` (SOUL, VOICE_CONFIG,
MEMORY_CONVENTIONS are live runtime/config records), `lore/`, `audit/`.

**Brian's rules (2026-10-29).**
- The Android originals live in the Android repo; these copies are deleted when the rewrite is done.
- Merging is fine; this matrix must be approved first.
- Unbuilt areas stay full vision docs to build against.

---

## 1. Drafting rules (apply to every new doc)

1. **Same shape.** Each doc has four parts: Intent (the vision), As built on Windows, Limits and Open questions. Each limit is
   marked as a temporary limit, a lasting boundary or a deferred capability.
2. **Keep the behaviour, drop the plumbing.** Firestore, Compose, Kotlin, Gemini Live and Android worker names go. Their intended
   behaviour, authority boundaries and acceptance scenarios stay. Example: Streaming Cognition keeps its full set of behaviour
   requirements:
   - progressive interpretation while Brian is still speaking
   - provisional entity and tool preparation
   - handling corrections before and after a turn is committed
   - throwing away drafts that no longer apply
   - the hard boundary that nothing provisional is ever committed

   It is not shortened to a latency note.
3. **Android locks are not Windows locks.** Decisions marked LOCKED in the Android docs (P19-D, CEA-D, PCI-D, MD-D, P29-D…) become
   recommendations unless Windows lore already decided the same thing.
4. **Inherited numbers are provisional.** Thresholds for confidence, relationship depth, curiosity frequency, style weights, decay,
   recurrence and so on are labelled "unvalidated" unless a Windows decision adopted them. The purpose of each mechanism stays.
5. **Evidence standard for "As built".** Each claim is labelled with one of these states, cited to lore, closeout or implementation
   evidence:
   - designed
   - implemented
   - harness-tested
   - live-tested
   - accepted risk
   - deferred

   A decision ID alone does not prove the behaviour shipped. Example: P8 R7b (the self-modification guard) was unit-tested, not
   invoked live.
6. **No silent changes.** A rewrite never authorises implementation, never edits live SOUL or config, and never reopens a locked
   decision by rewording it. Each change is labelled either *factual correction* or *proposed change needing a decision*.
7. **No real-family example data** in specs. The Android examples are inconsistent anyway (Breanna is listed as wife in one doc and
   daughter in another).

## 2. Target set (39 → 16)

Ordered along the vision's chain: identity → understanding → awareness → judgment → engagement → action.

| # | New doc | Merged from | Phase |
|---|---|---|---|
| A01 | **Architecture Overview**: owners of each responsibility and how they interact; PC is the core; Hermes boundary; principles | Master Plan; Agent Map (core rule, live-speech priority) | All |
| A02 | **Identity and Personality** | Identity & Personality Framework; Identity Source Consolidation (kept parts); Agent Map (behavioural pattern); Autonomous Behavior (behavioural learning) | P1 built |
| A02b | **Relationship with Brian** | Relational Continuity; Relational Calibration (wording only) | Vision |
| A03 | **Memory and World Model**: evidence model (§3), promotion rules by source, person resolver, confidence and hedging | Memory Hierarchy; Memory Agency (types, write, consolidation, recall, lifecycle); Perception Memory; Self-Model Awareness; Cross-Domain Correlation; Agent Map (consolidation, entity resolver) | **P11 core** |
| A04 | **People in Brian's World** | Relationship Inference; Social Graph Reasoning | **P11** |
| A05 | **Time and Temporal Understanding**: elapsed time, event time vs mention time, future events and deadlines, validity intervals, source freshness | Temporal Reasoning | P6 built; P11 |
| A06 | **Conversation and Continuity**: a layer over the Hermes session, not a second state authority | Conversational Continuity; Context Injection; Session Identity; Memory Hierarchy (topic stack); Agent Map (warm start) | P1/P5/P6 built |
| A07 | **Voice, Listening and Speech**: full behaviour of Streaming Cognition and Conversational Attention | Conversational Attention; Streaming Cognition; Living Voiceprint & Multi-Speaker; Agent Map (attention context) | P2/P4/P7 built; speech track |
| A08 | **Awareness: Sources, Signals and User State** | Environmental Awareness (sources, modes); Event Bus & User State; Communication Intelligence; SMS Intelligence; Agent Map (world state, cache, notifications) | P8/P9/P10 built |
| A09 | **Physical Perception** | Environmental Perception; Perceptual Input Layer | Vision |
| A10 | **Understanding Events and Judgment**: the six separate responsibilities; one final delivery decision point | Attention/Relevance Engine; Autonomous Behavior (governor, triggers, modes); Environmental Awareness + Event Bus (interpretation, fusion, dispositions); Cognitive Engine; Agent Map (trigger monitor, tool warm-start) | P9 built; **P12** |
| A11 | **Proactive Engagement**: engagement inside a conversation and event-driven delivery; watches and pending delivery state | Cognitive Engagement; Memory Agency (open loops, tension, resurfacing); Autonomous Behavior (summaries, regulation); Perceptual Input (attention-request levels) | P9 built; **P12** |
| A12 | **Distributed Presence and Devices** | Distributed Presence; Device Registration; DP Device Capabilities (primary) | P10 built |
| A13 | **Presence UI and Avatar** | Presence UI | P3 built; avatar phase |
| A14 | **Privacy and Memory Ethics** | Privacy & Data Ownership; Memory Ethics & Privacy; Memory Agency (use governor); Voiceprint (biometric rules) | All |
| A15 | **Authority: Tools, Actions and Autonomy** | Tool Authorization; Capability Acquisition; Relational Calibration (assumption license, as deferred) | P8 built; later |

The v1.1 per-doc file→target table is unchanged. It is superseded for deletion purposes by the section-level coverage map (§6).

## 3. Shared models A03 must define (other docs reference them)

### 3.1 Evidence dimensions — kept separate, never collapsed into one label

| Dimension | Describes |
|---|---|
| Acquisition / source | How Zola obtained it: Brian's statement, a retrieved message or record, a sensor observation, an inference |
| Attribution | Who made the underlying claim, and which message, record or observation supports it |
| Confidence and conflict | How certain it is, and whether contrary evidence exists |
| Time and validity | When it was said, observed or retrieved; when the event happened; when the claim was or is valid |
| Lifecycle and storage | Candidate, active, stale, superseded, …; where the record lives |
| Privacy and permitted use | What may be retained, inferred, disclosed or used for engagement |

- "Uncertain / conflicting" is a confidence state, not a source. A retrieved email can carry an uncertain claim. Something Brian
  said can go out of date.
- Confirmation adds to the evidence history; it never erases how a claim first arose.
- "Brian said X about Micah" establishes the *attributed statement*, not X as a trait of Micah. Retrieving an email reliably does
  not make everything its author asserts true.
- The five source docs' provenance lists map onto this model:
  - Memory Ethics: USER_STATED, USER_CONFIRMED, PERCEPTION_DERIVED, SYSTEM_INFERRED, TOOL_PROVIDED, CONVERSATIONAL_IMPLICIT
  - Memory Agency: Stage 6 authority classes
  - Perception Memory: authority tiers
  - Relationship Inference: edge sources
  - the Relational Intelligence Layer shared contract

### 3.2 Promotion rules by source (one contract, rules that fit the source)

The evidence, attribution, lifecycle and privacy contracts are shared. The rules for when a claim becomes established knowledge
differ by source:

| Source | Promotion shape (vision; numbers unvalidated) |
|---|---|
| Brian's own statements | As today (P5/P6): an explicit fact is saved; venting and rhetorical statements get lower authority (social deniability) |
| Retrieved records (email, calendar, texts, notifications) | An attributed claim the moment it is read; recognised as an event straight away; not made to wait for recurrence. Durable retention follows A14 retention rules. |
| Contacts | May seed a **known-sender** entity. This does not establish importance, trust or closeness. |
| Sensors (A09) | Recurrence across sessions plus confirmation for unknown entities (Perception Memory's pipeline) |
| Derived inferences | Computed at read time where possible; never stated as fact; dependent on their sources (truth maintenance) |

### 3.3 Two source-design issues to fix

- **Recurrence needs durable evidence.** Perception Memory's buffer is session-only, yet promotion needs observations across
  ≥3 sessions. A03 either defines a bounded persistent evidence record (with retention and deletion) or changes the design.
  *Source-design issue, not a Windows defect.*
- **Zola must not reinforce her own claims.** Perception Memory reinforces a fact when Brian "does not correct it". Social Graph
  promotes a provisional trait after 3 uncorrected sessions. Rules:
  - A repeated retrieval, generated summary or Zola-authored reference is not independent corroboration.
  - Brian's silence is not confirmation.
  - Copies of one claim count once.
  - Explicit confirmation and fresh attributed evidence may reinforce a claim.
  - Corrections invalidate the superseded fact and everything inferred from it at retrieval time. Hedging alone does not fix
    wrong evidence.

### 3.4 Remembered situations vs operational watches (A03 ↔ A11)

- "The 4Runner problem is unresolved" is a remembered situation, owned by A03.
- "Watch for the ECU email" is an operational watch or pending delivery, owned by A11 and the proactive store (P9-D06's separation
  stands as an existing boundary).
- The two are linked by stable IDs. A11 defines which owner closes what, how resolution propagates and how forget affects both.
- Neither may edit the other's status.
- An unresolved topic never silently becomes an authorised watch.

## 4. Factual reconciliations (Claude fixes these while drafting; no decision needed)

| # | Item | Correction |
|---|---|---|
| F1 | **Provenance (corrects v1.1 §3 item 2).** v1.1 said no source had an external-source class. Wrong: Memory Ethics defines TOOL_PROVIDED for calendar, email and contacts, and Memory Agency includes tool-provided material. | The real problem is inconsistent treatment, fixed by §3.1. |
| F2 | **Governor chain (corrects v1.1 §3 item 1).** Cognitive Engagement and Cognitive Engine describe an *ordered chain* (the Engagement Governor checks appropriateness, then Attention/Relevance gives final authorisation). That is not a competing owner. | The real conflict is Autonomous Behavior's Response Governor vs the Attention Engine, each claiming final authority. A01 names owners per responsibility; A10 has one final delivery decision point without absorbing privacy, endpoint or action checks, which stay independently enforceable. |
| F3 | **Self-modification (corrects v1.1 §3 item 15).** "A promise with no mechanism" overstated the gap. P8-D02 built `config_self_edit` (live config, `.env`) and `self_mod` (plugin trees, token store, `zola_memory`, `zola_tools`, SOUL.md, `identity/`), with tested residual bypasses (a path held only in a variable, a junction, a `.pyc`-only edit). R7b was unit-tested and not invoked live. Background `skill_manage` is blocked in a Workspace-tainted session (P8-D09). | A15 states four things separately: what policy authorises (A8/H5 Hermes defaults), what code enforces (P8-D02), accepted residual risks, and proposed changes. See B15 for the policy question. |
| F4 | **Scheduled work.** Reconcile S7 (cron = unsupervised `run_conversation`) per execution context against P8-D02 (cron does not receive the Workspace toolset) and P9-D01/D04 (background is code; the watcher has a fixed read API). | Neither the old posture nor a blanket ban is assumed to apply everywhere. |
| F5 | **Code rule.** v1.1 shorthand "codes never" was inaccurate. R1: Zola reads a verification code aloud **only on Brian's explicit request**, and that read bypasses the model, history, memory, logs and persistent TTS caches. | State R1 exactly. |
| F6 | **Save confirmations.** "Never announced" (Identity Consolidation) vs P5-D03 brief mention. | P5-D03 stands; the old rule is dropped. |
| F7 | **SMS "known contacts only"** vs P10-D10 (contacts ordered above unknown numbers, not exclusion). | Windows decision stands. |
| F8 | **Single-score importance.** The source docs collapse trust, importance and eligibility. | Restated around the vision's separate responsibilities; contact frequency is evidence, not importance. |
| F9 | **Inbound vs outbound vs response vs action.** | A01 keeps four distinct authorities: inbound attention (is speech directed at Zola), outbound engagement (should she initiate), conversational response (answering Brian's turn), action authority (may a tool run this action). Relationship familiarity and proactivity levels never grant execution. Action enforcement stays at the executor, with action-bound approvals rechecked. |
| F10 | **Hermes's extra output paths** (`review.summary`, child-session completes, heartbeat; A2/A6) | Mapped from the actual current paths and their controls before A10/A11 claim one delivery point covers everything. |

**Stale Windows notes** (factual corrections in the rewrite):
- Master Plan P2: Edge TTS / faster-whisper → Deepgram Aura-2 Pandora 0.95 (P9-D14).
- S13 "texts need research" → Phase 10.
- "Gmail via the P3 connector" → P8 Workspace plugin; `google-workspace`, `himalaya` and `email-inbox-triage` retired (P8-D02).
- A1 "own approval UI + two-step confirm" → P8 spoken passphrase "Approved. Send it." checked in plugin code (P8-D06), no cards.
- Privacy Plan C8 forget scope → P6-D06.
- Retention table → P9-D07 and P10.
- "May use cloud" provider list.
- **H2 "no DPAPI" → P8 setup writes the token to a DPAPI store.**
- DP-D11 local-network-only, push vendor, gateway, allowlist → P10 transport (Tailscale, W1, no Firebase), `zola-phone` (P10-D12), allowlist as amended 10/28.
- Device Registration FCM → dropped (P10-D16).

Before any P10 or P11 line is written as built, it is checked against the current P10 closeout records. The inspected lore
`ROADMAP.md` lists Phase 10 only as a separate track.

**Outside the 39 docs (flag only):**
- `identity/SOUL.md` still says "text-based Windows client".
- `identity/VOICE_CONFIG.md` still has a "Sonia at 0.95" section.

Missing referenced docs (Entity_Taxonomy, Firestore_Structure, Firestore_Write_Safety, Daily_Brief, Agent_Architecture,
Entity-Native Memory Principle): the links are dropped, but any essential requirement they stood for is preserved in the
coverage map.

## 5. Choices that need Brian's decision

Each choice lists what Zola does under each option, plus Claude's recommendation (*italic*).

| # | Choice | What changes in Zola's behaviour | Recommendation |
|---|---|---|---|
| B1 | **One final delivery decision point** for unprompted output (replacing the Response Governor / Attention Engine double claim) | One place decides speak / defer / log; one log explains every unprompted line or silence. Engagement, privacy, endpoint and action checks feed in or veto separately. | *Yes, in A10.* |
| B2 | **Assumption license** (a deep relationship lets her act on known preferences without asking) | Kept in A02b: familiarity could create action authority. Moved: calibration may only drop unnecessary *preference questions inside an action already authorised*; silent execution needs its own A15 decision. | *Move to A15 as deferred.* |
| B3 | **People in Brian's household.** The Privacy Plan bars retaining non-consenting household members "in identifiable form" | Kept literally, Zola could not know Bre and the boys. Split into four cases, each with its own rule: (a) facts Brian tells her; (b) attributed info from authorised sources; (c) ambient conversation capture; (d) biometric enrolment. | *Split; (a) and (b) allowed with provenance, (c) and (d) separate consent decisions.* |
| B4 | **Speaking message content unprompted** ("never read content aloud" vs the 10/19 "in her own words, with context") | Private: "Micah texted — his car won't start at the school lot." Restrained: "Micah texted you." Note: desk presence alone doesn't prove nobody else is in the room. | *Content allowed when the audience is known private; restrained when unknown; R1 for codes.* |
| B5 | **Third-party voiceprints** (Perceptual Input says never; Living Voiceprint enrols introduced people) | Never: Zola can't tell Bre's voice from a guest's. Allow on introduction: she can, with stored embeddings of people who may not know. | *Your call. If allowed: introduction-only, on-device, visible and deletable, never used to wake her.* |
| B6 | **Sensitive topics and proactivity** ("sacred facts are never proactive") | Strict: she won't remind you about a medical appointment you asked her to watch. Split: unsolicited personalisation from sensitive topics stays blocked; watches, reminders and relevant heads-ups you asked for are allowed. | *Split.* |
| B7 | **Third party present → stop writing conversation memory** (Perceptual Input rule) | Strict: nothing you deliberately tell her while Bre is in the room is kept. Alternative: your own deliberate statements are kept; others' speech is not. | *Keep Brian's deliberate statements; don't keep others' speech.* |
| B8 | **Social graph from observed sources** (source: conversation only) | Conversation only: she learns who Micah is only from what you say. Attributed evidence allowed: email, texts and Contacts count, at lower authority and via §3.2 rules. | *Allow attributed evidence.* |
| B9 | **Sibling relationships stored at write time** (P19-D03) vs inferred at read time | Stored: faster answers, but corrections must clean up stored edges. Read time: always consistent, slightly more work per question. | *Read time, unless the P11 audit shows a reason not to.* |
| B10 | **Heat** (how much of your attention she has spent recently) **per device or per person** | Per device: after she talks a lot on the PC, the phone starts "fresh" and may pile on. Per person: restraint follows you across devices. | *Per person.* |
| B11 | **Cross-device conversation** (Session Identity: new device = new session; Distributed Presence: continues invisibly) | Attach: walk away from the PC and keep the same conversation on the phone. New session: the phone starts a new conversation informed by memory. | *Attach to the existing Hermes session (DP Device Capabilities §9).* |
| B12 | **"No breathing, no head motion" (P3)** vs your avatar goal (hair, head and speech motion; AV7 bones) | Boundary: the avatar stays still apart from blink and mouth. Temporary limit: motion arrives in the avatar integration phase. | *Temporary limit.* |
| B13 | **"Restrained" as a locked trait** vs SOUL "I take initiative" | Wording only: restraint means interruption discipline, not waiting to be asked. | *Reword in A02.* |
| B14 | **HOUSEHOLD_OK disclosure** needs a "trusted entity list" (the 10/19 direction says no manual list) | Relationship understanding can inform the policy, but knowing someone is family is not by itself permission to disclose everything household-scoped. Audience, channel, work context and explicit confirmation are separate constraints, not one ranking. | *Relationship-informed policy, with permission decided separately.* |
| B15 | **Which self-changes need your approval** (after F3) | Today Hermes's default lets skill writes through, while P8 guards protect config, SOUL, identity, plugins and memory code. Choose whether new or edited skills also need your OK. | *Your call; Claude leans "skills that add tools or run code need approval".* |

## 6. Coverage map before deletion (new requirement)

Before the 39 copies are deleted, Claude produces a **section-level** map (file-level is not enough for docs split three to five
ways):

| Original file / section | Destination doc / section | Treatment | Reason or authority |
|---|---|---|---|
| e.g. Memory Agency § Open Loop Tracker | A11 § Watches and pending items | merged | §3.4 |

**Treatment** is one of: preserved, merged, superseded (with a decision ID) or intentionally dropped (with a rationale). Behaviour
examples and acceptance scenarios stay where they clarify intent; this includes Memory Hierarchy scenarios A–G, which are good
P11 acceptance candidates.

**Traceability:**
- Historical audits, closeouts and decision records stay as written.
- Current indexes and active build/audit references are updated.
- Historical references get successor pointers via the migration map, not rewrites.
- Active references are checked before replacement.

## 7. Drafting order and process

1. **Boundaries first.** Short boundary drafts of A14 (what she may retain and disclose) and A15 (what may act), alongside A03. The
   full docs follow later.
2. Then A01 → A03 → A04 → A05 → A06 → A10 → A11 → A08 → A12 → A07 → A14 (full) → A15 (full) → A02 → A02b → A13 → A09.
3. Before each doc, settle the §5 choices it depends on: B3, B6, B7 and B8 before A03/A04; B1, B2, B10 and B15 before A10/A15.
4. Drafts go into the project (`claude/arch/A0x_*.md`). Nothing touches the repo.
5. **Repo change:** one small Cursor track after the Phase 10 lore closeout and before P11PRE. It adds the 16 docs, removes the 39
   copies only once the coverage map is approved, and updates active references.
