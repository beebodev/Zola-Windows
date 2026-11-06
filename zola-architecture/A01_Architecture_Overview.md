# A01 — Zola Architecture Overview

*Draft v0.2, 2026-10-29, revised after ChatGPT's review. Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.**

*v0.3, 2026-11-02 — reconciliation pass after the coverage audit: guests get the harmless-lookup shortlist (ARCH-38); household-operation review trigger (ARCH-44).*
*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

Replaces `Zola Master Architecture Plan.md` (the file's title is "Zola Vocal Computing Architecture Plan") and the core rules of `Zola_Agent_Map.md`.
Governing records: Windows lore (`DESIGN_DECISIONS.md`), the project vision instructions, and architecture-doc decisions ARCH-01–ARCH-13 (`ARCH_DOCS_DECISIONS.md`, in this folder).
**Precedence.** Locked lore governs current implementation unless it is explicitly superseded. Approved future direction may differ from lore. Where it does, this set names the difference and the implementation change it requires. ARCH-08 vs A8 is an example. A difference that is not named is a defect in this doc.*

**How to read this doc.** Every doc in the set has four parts:
- **Intent:** what Zola is meant to become.
- **As built:** what runs today on Windows, with an evidence label.
- **Limits:** each limit is marked as one of:
  - **temporary limit:** accepted for now
  - **lasting boundary:** meant to stay
  - **deferred capability:** planned; the architecture must leave room for it
- **Open questions.**

Evidence labels:
- **designed**
- **implemented**
- **harness-tested**
- **live-tested**
- **accepted risk**
- **deferred**

A decision ID alone does not prove a behaviour shipped.

---

## 1. Intent

Zola is a persistent digital entity, not a chatbot, voice assistant or notification reader. She is meant to:
- develop her own ongoing understanding of Brian, the people around him, his work and responsibilities, and the world they share;
- notice what matters without being asked;
- use judgment about when her attention would help;
- speak in her own words, with shared context;
- grow in autonomy only inside boundaries Brian sets.

Two principles from Brian shape everything below:
- **She grows in her own world (ARCH-02).** *"I don't want her to be a reflection of me, but of herself growing in the world."* She learns from what she observes as well as from what Brian tells her. That includes email, texts, contacts, devices and, eventually, sight and sound.
- **She is a trusted presence for each person (ARCH-03).** She builds her own relationship with each member of the household.
  - She keeps each person's information private to that person unless they approve.
  - She acts for each person only on what pertains to them.

The intended experience (Master Plan, kept):

> less like "a chatbot with speech" and more like "a persistent conversational presence."

She should feel:
- natural
- aware
- continuous
- intelligent
- conversational
- emotionally grounded
- contextually connected
- environmentally present

She should do this without losing:
- trust
- factual reliability
- user control
- architectural discipline
- privacy boundaries
- restraint

### 1.1 The chain of responsibilities

Her intelligence runs along one chain (the vision's autonomy model). Each link has its own owner and its own doc.

| Link | What it means | Owner doc |
|---|---|---|
| **Awareness** | Information arrives: conversation, email, calendar, texts, notifications, devices, eventually sensors | A08 Awareness; A09 Physical Perception; A07 Voice |
| **Understanding** | Interpreting it against what she already knows: people, situations, time, history | A03 Memory and World Model; A04 People; A05 Time; A06 Conversation |
| **Judgment** | Does it matter, how much, may she raise it, and is now the time | A10 Understanding Events and Judgment |
| **Engagement** | Raising it naturally in her own words, then carrying the conversation | A11 Proactive Engagement; A07 Voice; A13 Presence UI |
| **Action** | Recommending, asking, and only with authority, doing | A15 Authority |

Two docs cut across the chain:
- **A14 Privacy and Memory Ethics:** what she may keep, infer and disclose.
- **A12 Distributed Presence:** where she can perceive and reach people.

Identity sits underneath all of it:
- **A02 Identity and Personality:** who she is.
- **A02b Relationship with Brian:** one of her relationships.

### 1.2 Six responsibilities that are never collapsed into one score

The project vision (§3) lists five judgments. Brian's 2026-10-19 direction (§4) separates out **relationship understanding** as a sixth responsibility, and that direction governs. All six are kept distinct everywhere in this set:

| Responsibility | Question | Owner |
|---|---|---|
| **Source authenticity and trust** | How sure are we where this came from and that it is genuine? | A08 (signals), A10 |
| **Relationship understanding** | Who is this person, or what is this thing, to the person concerned? | A04, A03 |
| **Importance and urgency** | How relevant or consequential is it, and how soon does it matter? | A10 |
| **Interruption eligibility** | Is she allowed to raise it unprompted? | A10, with A14 vetoes |
| **Delivery timing** | Is now an appropriate time? | A10, with A11 and A12 |
| **Action authority** | What, if anything, may she do? | A15 |

A saved contact establishes a *known sender*. It does not establish trust, closeness or importance.
Information from an unknown sender may matter. A known contact's message may not. Trust changes *how* she handles information. It never stops her from *recognising* that something is important.

### 1.3 Four authorities that are never merged (matrix F9)

| Authority | Decides | Owner |
|---|---|---|
| **Inbound attention** | Is this speech directed at Zola? | A07 |
| **Outbound engagement** | Should she initiate, and when? | A10 decides (one final decision point, ARCH-09); A11 delivers |
| **Conversational response** | Answering the person's own turn | Hermes turn (A06/A07) |
| **Action authority** | May this tool run this action, for this person, now? | A15, enforced at the executor |

Relationship depth, familiarity and proactivity levels never grant action authority (ARCH-10).

**Recognition is not permission.** Recognition answers one question: who is probably speaking or present (A07/A09). Permission comes only from policy. Under ARCH-03 that means:
- a verified household member may make low-stakes requests that pertain to them;
- anything consequential needs that person's own approval method.

**A speaker she cannot verify is treated as a guest until verified (ARCH-12).** She may talk with them and use a short list of harmless lookups that touch nobody's data, such as the weather or the time (ARCH-38; the list is still to define). Nothing else runs for them, and nothing private is shared.

A15 defines "low stakes". It excludes anything that would expose another person's information.

### 1.4 Several people, one Zola: who owns what

ARCH-03 makes Zola a presence for every household member, not only Brian. Each question this raises has one owner:

| Question | Owner |
|---|---|
| Who is speaking or present, and how sure she is | A07 (voice), A09 (camera) |
| Whose conversation is active; overlapping and handed-off conversations | A06 |
| Whose memories may be retrieved into a conversation; who owns a fact; what counts as shared (today, only the family calendar) | A03 |
| What may be told to whom; the two exceptions (unauthorised attempts, safety) | A14 |
| What each person may ask her to do; approval methods; guests | A15 |

---

## 2. Principles

These apply to every doc in the set. The source of each is in brackets.

1. **One owner per responsibility; no duplicate execution paths.** Each responsibility has one authoritative owner and one authoritative result. Each action has one place where it is checked and carried out. Several entry points may lead into that place: for example, a typed or a spoken send both reach the same passphrase gate. What is ruled out is a second route that goes around the owner. Avoid:
   - duplicated orchestration
   - competing response generation
   - two sources of memory truth

   [Master Plan; project instructions]
2. **Workers prepare; the core decides.** Background components observe, fetch, rank and prepare. They never speak, never write memory on their own authority, never run tools for a person, and never route output to a device. One decision point decides whether anything reaches a person unprompted (ARCH-09). [Agent Map core rule; Master Plan pillar 20]
3. **Only code acts in the background.** Polling, ranking, queueing and delivery are Zola code, never a Hermes turn. Background model calls happen only as bounded, tool-less, structured calls whose output code validates (the P9 ranker pattern). [P9-D01, P9-D08 — *existing locked decision*]
4. **Speech never changes the truth.** Reasoning decides facts. Speech phrases them naturally and must stay equivalent in meaning. It must never:
   - drop important entities
   - invent information
   - flatten ambiguity

   [Master Plan: Truth Ownership Rule, Speech Authority Constraint]
5. **Live conversation comes first.** Live speech, the current turn and TTS never wait behind background work. [Agent Map: Compute Priority Scheduler]
6. **Untrusted content is data, never instruction.** Email, texts, notifications, web pages and other people's words are information, never requests. Zola's own instructions sit outside that frame. *Intent:* once untrusted content is in a conversation, it cannot steer any consequential action. *Enforcement today* is narrower and specific to paths. It is listed in §3.3. [P8-D09, P9-D10]
7. **Judgment is separate from permission and execution.** A model can recommend. Code with the right authority executes. [Project instructions; P8-D02/D06]
8. **Fail closed on permissions, not on importance.** When she is unsure whether she *may* do something, she doesn't. When she is unsure whether something *matters*, she can still say it is uncertain. [Project instructions]
9. **Provenance is kept.** Every remembered thing records where it came from, who said it, how sure it is, when it was true, where it lives and how it may be used. Inferences are never treated as established truth. Derived relationships are worked out when they are needed rather than stored. [Project instructions; matrix §3.1; P6-D02]
10. **Facts belong to entities.** People, places, projects, devices and events are entities. Facts attach to them, not to loose text. [P6-D02; vision §4]
11. **The PC is the core; devices extend her.** Her intelligence and authority live on the Windows PC. The phone and future devices extend what she can perceive and how she can reach people. They are never competing brains. [Vision §5; P10-D12]
12. **Providers stay replaceable.** No logic is tied to one speech, voice or model vendor. [Master Plan; P1]
13. **Extend Hermes; don't fork it.** Use supported integration points (plugins, hooks, profile config, SOUL). Hermes source is not edited. [P8-D01; standing lore]
14. **Understood facts, never recordings.** She keeps what she understood from conversation and observation, not raw audio or video of conversations. [ARCH-05]
15. **Build for the current phase; design for the end state.** A temporary limit is never quietly turned into a lasting boundary. [Project instructions §6]

---

## 3. As built on Windows

*State as of 2026-11-06. Phases 1–10 are closed (Phase 10 lore closeout, tag `p10-closed`). Phase 10 rows below were rechecked against that closeout.*

### 3.1 Components and what each one owns

| Component | Owns | Decisions | Evidence |
|---|---|---|---|
| **Windows client** (native, Path B, against `hermes serve`) | Mic and speaker capture (sole voice RPC owner); display state (`ZolaDisplayState`); the avatar render (Helix, GLB); supervision of serve, watcher and `zola-phone`; the unprompted-speech coordinator; the Systems panel | C1, C3, P2-D01, P3-D01–D03, P9-D02, P9-D11, P9-D12 | live-tested (P2–P9 closeouts) |
| **`hermes serve`** (pinned Hermes Agent) | Conversation turns; sessions (the Windows conversation wraps Hermes's own session row); tools; command approvals (mode `manual`) | C6, P4-D07, P4-D27 | live-tested |
| **SOUL.md + `identity/`** | Zola's identity and standing behaviour lines | C5 | live (some lines stale: §6) |
| **`zola_memory` plugin** | Local structured store beside `USER.md`/`MEMORY.md` (the fact authority): fact index, episodes, time awareness, forget cascade | P6-D01–D07, P5-D03 | live-tested (P6) |
| **`zola_tools` plugin** | Bounded tools such as `calculate` | P6 | live-tested |
| **`zola_workspace` plugin** | The only Google credential holder and caller; Gmail/Calendar/Drive/Contacts tools; drafts and passphrase-bound send; the proactive store (`proactive.db`); the background ranker worker (in serve); the contact index | P8-D01–D12, P9-D06, P9-D08, P10-D10, P10-D18 | live-tested (P8, P9); contact index (the one person resolver): shipped (P10) |
| **Workspace watcher** (separate process) | Gmail and Calendar polling through a fixed read-only API; writes items to the proactive store | P9-D03–D05 | live-tested (P9) |
| **`zola-phone`** (third supervised process) | The only PC link to the phone: pairing, the held signed connection, intake into the proactive store, read relay, phone health | P10-D03, D07, D12 | shipped (P10); live-paired |
| **Android companion app** | Detecting texts and allowlisted notifications on the phone; masking codes; queueing; the connection's phone side | P10-D01–D16 | shipped (P10): texts and allowlisted notifications; versionName 1.1.1 |
| **Voice providers** | Speech out: Deepgram Aura-2 Pandora at 0.95. Speech in: local faster-whisper | P9-D14; P2-D02 | live |

### 3.2 How unprompted output works today

1. The watcher or `zola-phone` writes an item into the proactive store.
2. The ranker labels email items. Phone items are ranked by code only.
3. Surfacing injects a bounded note into the first conversation turn after a gap.
4. Separately, the client coordinator may speak a fixed phrase, but only for items that match a watch Brian asked for, and only when every permission check passes. The checks cover:
   - unlocked
   - Voice mode
   - no capture, turn, playback or clarify
   - outside quiet hours 10 pm–7 am

Nothing else in Zola's code speaks unprompted. Hermes has its own extra output paths (review summaries, child-session completions, heartbeat). They are accepted as-is today (A2) and are not yet mapped against the one-decision-point rule (§5, Q1).

### 3.3 How authority works today

**Draft and send:**
- Drafts: she can make them in conversation (P8-D05).
- Workspace sends: need the spoken passphrase "Approved. Send it.", bound to the exact draft and checked in plugin code (P8-D06).
- Dangerous terminal commands: use Hermes's approval card (P4-D07).

**Brian-only actions** require the client-origin ticket (P9-FIX-ARM).

**Untrusted content: what is actually enforced.** These are path-specific protections, not a universal rule (P8-D09, P9-D10):
- **Framing and taint.** Workspace results, and injected surfacing that contains mail text, are framed as untrusted. They taint the session until it ends. Phone content read in a conversation also taints the session (P8-D09, Phase 10 annotation).
- **Memory saves.** In a tainted session, a memory save runs only if it starts with Brian's own save request in his current message.
- **Skill changes.** Background `skill_manage` is blocked in a tainted session.
- **The consolidator** attributes external content as something Zola read, never as Brian's statement.
- **Watches and forget.** A name or number inside a text, notification, mail subject or other untrusted body can't create a watch or trigger a forget (P10-D19).
- **Workspace sends** are protected separately by the passphrase bound to the exact draft (P8-D06), whether or not the session is tainted.

**Self-modification guards (P8-D02)** protect:
- live config and `.env`
- the token store
- plugin trees
- memory code
- SOUL
- `identity/`

The guards have tested gaps (accepted risk). Skill writes still follow Hermes's default (A8/H5). ARCH-08's approval policy for new skills, new tools and code-reaching edits is **decided, not enforced**.

---

## 4. Limits

*Kind* is temporary limit, lasting boundary, or deferred capability. *Accepted risk* is a separate column: it marks a known gap that is accepted as-is, whatever the kind.

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| Texts ranked by code only; no AI judgment on phone items | temporary limit | — | P10-D11 keeps a judgment slot; Phase 12 judgment may use it |
| Only watched items speak unprompted, in a fixed phrase | temporary limit | — | P9-D11 narrowed; Phase 12 brings judgment and her own words (ARCH-09, ARCH-11) |
| Current facts live in flat `USER.md`/`MEMORY.md`, with the structured store beside them | temporary limit | — | P6-D01; moving fact authority is a future evidence-based decision (Phase 11) |
| One person: voice input is treated as Brian | temporary limit | — | S1; ARCH-03/ARCH-07/ARCH-12 make household recognition the intended capability |
| PC-only delivery; the phone sends information in but does not yet carry her voice out | temporary limit | — | Vision §5; A12 keeps the path open |
| Hermes's extra output paths not arbitrated | temporary limit | yes (A2) | Mapped before A10 claims full coverage (§5 Q1) |
| No layer separating facts from phrasing | temporary limit | yes (A4) | Principle 4 is the intent |
| Approval for new skills, tools and code-reaching edits not enforced | temporary limit | yes (A8/H5) | ARCH-08 is the decided policy; differs from A8 by design |
| Consequential actions need the person's explicit approval | temporary limit | — | Vision §3, §6: must not rule out future controlled low-risk autonomy, which needs its own A15 decision |
| Untrusted-content protections are path-specific, not universal | temporary limit | yes | Principle 6 is the intent; §3.3 lists what is enforced |
| Self-modification guards have tested gaps (variable-held path, junction, `.pyc`-only edit) | temporary limit | yes (P8-D02) | Guards live on `pre_tool_call`, fail closed on named targets |
| **Security protections present:** the Google token and client secret are DPAPI-encrypted (P8-D04); the voice key is in a user-only folder with guard rows (P9-D14); the WER dump folder ACL is user and SYSTEM (P9-D02); BitLocker at rest | — | — | Present today |
| **Security hardening deferred:** code signing (H1); credential protection for everything else (H2, revised only for the Google token); ship bar (H3); application-level encryption of `state.db` and memory (H4); Hermes default-config risks (H5); MCP secret inheritance (H6) | temporary limit | yes | Accepted for personal single-user use. The single-user risks are reviewed **before household operation** is switched on (ARCH-44), and all of these together before any wider distribution |
| Judgment never grants execution | lasting boundary | — | Vision §3; ARCH-10 |
| Recognition identifies; only policy grants permission; an unverified speaker is a guest | lasting boundary | — | ARCH-03, ARCH-07, ARCH-12 |
| No raw recordings of conversations | lasting boundary | — | ARCH-05 |
| Each person's information is private to them, with two narrow exceptions | lasting boundary | — | ARCH-03 (unauthorised attempts; safety) |
| Physical perception (cameras, presence, environmental sound) | deferred capability | — | A09 |
| More devices (shop, vehicle, glasses, smart home) | deferred capability | — | A12 |
| Controlled low-risk autonomy | deferred capability | — | A15 |
| Relationship understanding beyond facts (calibration, continuity) | deferred capability | — | A02b; S2/S3 deferred |

---

## 5. Open questions

- **Q1. Hermes output paths (F10).** List every way Hermes can produce output on its own, and what controls each one, before A10 claims one decision point covers all unprompted output.
- **Q2. Background judgment and P9-D01.** Phase 12 needs judgment in the background, and P9-D01 says background work is never a Hermes turn. Claude's reading: these are compatible if background judgment uses the ranker's shape (bounded, tool-less, validated by code). If Phase 12 needs more than that, it is a new decision. Not decided here.
- **Q3. Phase 10 "as built".** *Resolved 2026-11-06:* every Phase 10 row in this set was rechecked against the Phase 10 lore closeout in ARCH-SWAP Phase 2.
- **Q4. Speech in.** Confirm faster-whisper is still the live speech-to-text provider. The speech qualification track may change it.

---

## 6. Stale records outside this doc (flag only, not changed)

- `identity/SOUL.md` still says "text-based Windows client". She has voice, the avatar and proactive speech.
- `identity/VOICE_CONFIG.md` still has a "Sonia at 0.95" section. The live voice is Deepgram Pandora (P9-D14).

Fixing either is a SOUL/config change and needs its own approval (matrix rule 6). The ARCH-SWAP track proposes both edits for that approval.

---

## 7. The doc set

| Doc | Covers |
|---|---|
| A02 Identity and Personality | Who she is; consistency; growth; style |
| A02b Relationship with Brian | Their relationship; continuity; calibration (wording only, ARCH-10) |
| A03 Memory and World Model | Entities, evidence model, promotion by source, confidence, correction |
| A04 People in Brian's World | People, relationships, household members as entities |
| A05 Time | Elapsed time, event vs mention time, deadlines, validity, freshness |
| A06 Conversation and Continuity | Sessions, topics, warm start, session briefs, layered over the Hermes session |
| A07 Voice, Listening and Speech | Attention, streaming cognition, speakers, speech |
| A08 Awareness | Sources, signals, user state |
| A09 Physical Perception | Cameras, presence, environmental sound |
| A10 Understanding Events and Judgment | The six responsibilities (A10's share); the one final decision point |
| A11 Proactive Engagement | Raising things naturally; watches; pending delivery |
| A12 Distributed Presence and Devices | Endpoints, capabilities, routing |
| A13 Presence UI and Avatar | The window, the avatar, motion |
| A14 Privacy and Memory Ethics | Keeping, inferring, disclosing; per-person privacy |
| A15 Authority | Tools, actions, approvals, self-changes, autonomy |

---

## 8. Coverage of the source docs (feeds the coverage map)

**Status of this map.** A row is **verified** only when its destination section exists and has been checked against the source. Rows that point at docs not yet written are **planned**. They are not proof that anything has been preserved. None of the 39 copies may be deleted while any of their rows is still planned.

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Master Plan: Vision, Core Philosophy (vocal computing), Long-Term End State | A01 §1 | merged (voice as the primary layer → A07) | verified (A01) |
| Pillars 1–3 (presence, conversation engine, streaming) | A13 §3–§6 (presence); A06 §2–§5 (conversation); A07 §7 (streaming) | merged | verified |
| Pillar 4 (memory) | A03 §3–§12 | merged | verified |
| Pillar 5 (autonomous behaviour) and 9/9a (attention, dampening) | A10 §4–§7; A11 §2–§7 | merged; single-score wording replaced (F8) | verified |
| Pillars 6–8 (awareness, perception, interpretation) | A08 §3–§5; A09 §3–§5; A10 §3–§4 | merged | verified |
| Pillars 10, 14 (relationships, multi-person) | A02b §3–§8; A04 §3–§7; A06 §7 | merged; household rules from ARCH-03 | verified |
| Pillars 11–12 (momentum, conversational attention) | A06 §4.3; A07 §4 | merged | verified |
| Pillar 13 (trust, permission, privacy) | A14 §3–§7; A15 §3–§6 | merged | verified |
| Pillars 15–17 (tone, deferred summary, user state) | A02 §5; A11 §5; A08 §5 | merged | verified |
| Pillar 18 (identity) | A02 §3, §6, §8 | merged | verified |
| Pillar 19 (distributed presence) | A12 §2–§9 | merged | verified |
| Pillar 20 (workers, event bus, central authority) | A01 §2 principles 2–3; A08 §4; A09 §2 p10 | merged | verified |
| Core Architectural Principles | A01 §2 | preserved | verified (A01) |
| External API strategy | A08 §3 (source list, vision); A01 §3 (current providers) | merged; Android vendor names dropped as not binding (P1) | verified |
| Privacy and Trust Architecture | A14 §2–§9 | merged | verified |
| Recommended planning docs, near-term focus | — | intentionally dropped: superseded by this doc set | n/a (dropped) |
| Agent Map: core rule | A01 §2 principle 2 | preserved | verified (A01) |
| Agent Map: compute priority | A01 §2 principle 5 | preserved | verified (A01) |
| Agent Map: agents 1, 6, 12 | A08 §5 (agent 12, one user-state estimate), §9 (agent 6); A10 §9.1 (agent 1) | split; agent 1's prepared context is the A10 §9.1 contract | verified |
| Agent Map: agents 2, 9 | A03 §5.8 (agent 2, upkeep); A03 §6, A10 §8, §9.1 (agent 9: resolver, contact index, hot entity set) | split | verified |
| Agent Map: agent 3 | A07 §4.2 (prepared hints only) | merged | verified |
| Agent Map: agent 4 | A06 §5 (session brief) | superseded by the brief (as Android also did, PCI-D05) | verified |
| Agent Map: agents 5, 8 | A10 §4.3, §5 (agent 5: candidates and expiry); A10 §9.1 (agent 8: preparing in advance) | split; agent 8 kept as a deferred contract (audit C02) | verified |
| Agent Map: agent 7 | A02 §5.2 (style learning); A10 §7, ARCH-19 (ignored categories as an inspectable preference) | merged | verified |
| Agent Map: agent 15 | A11 §5.1 | **deferred but retained** (ARCH-65) | verified |
| Agent Map: Android class names and phases | — | intentionally dropped: platform plumbing | n/a (dropped) |
