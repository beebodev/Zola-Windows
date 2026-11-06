# A06 — Conversation and Continuity

*Draft v0.3, 2026-10-29 (ARCH-16, ARCH-17; ChatGPT review). Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

*v0.4, 2026-11-02 — reconciliation pass after the coverage audit: assembly is read-only; brief reuse scoped (audit C05); scenario C12.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

**Replaces**
- `Zola Conversational Continuity Architecture.md`
- `Zola_Architecture_Context_Injection.md` (portable ideas only)
- `Zola_Session_Identity_Architecture.md` (Android MD-D05 — not a Windows lock)
- Memory Hierarchy §8 (topic stack)
- Agent Map agent 4 (warm start)

**Governing records**
- **Lore:** C1, C6 (the Windows conversation wraps the Hermes session row), C3, P4/P7 (clarify, transcript admission), P5-D06 (past-conversation search only when asked), P6-D04/D05, P9-D10 (surfacing), P9-D11 and S87 (the proactive line is not stored), P9-D02 (crash replay has no Brian authority)
- **Architecture-doc decisions:** ARCH-03, ARCH-05, ARCH-09, ARCH-12, ARCH-13
- **Brian's 10/19 direction:** "once she initiates, I should be able to respond naturally without restarting the conversation"

**What is not decided here.** Android numbers below (budgets, refresh triggers, grace periods) are **unvalidated**.

---

## 1. Intent

> "A session boundary must not become a memory boundary." (Vision §1)

Zola should feel **continuously present**, not like a chatbot that resets every time:
- Conversations cool, pause, branch, resume and reconnect.
- "It still won't start" means the 4Runner, because that's what they were working on.
- "Anyway, where were we on the fuel system?" brings back that thread with what was still unresolved.
- When she speaks up unprompted, Brian can simply answer, and the conversation continues from there (direction §4).
- After a break, she picks up naturally.
- She doesn't recite what she knows, and she doesn't open with "I see you have an open loop about…".

**It must never feel like surveillance** (Conversational Continuity, kept). That means:
- no forced recall
- no reinjecting context just because it exists
- no casually resurfacing emotionally hard topics

**Several people, one Zola (ARCH-03).** A conversation now belongs to **whoever is in it**. What Bre says privately to Zola must never leak into Brian's conversation, and the reverse. That holds even at the same PC, minutes apart. This doc owns how that's achieved (A01 §1.4).

---

## 2. Principles

1. **Hermes owns the conversation; continuity is a layer over it.**
   - The Hermes session and its transcript are the single authority for "what was said in this conversation" (C1, C6).
   - Zola adds *derived* state on top: the topic stack, active entities and unresolved references. That derived state is rebuildable from the conversation and memory.
   - There is no second, competing "conversational state engine". The Android doc's own principle ("no competing or parallel state model") is honoured by making Hermes the base, not by building a rival.
2. **One governed context-assembly path.** Everything injected into a conversation passes through one assembly path (A03 §10; DQ-8):
   - the session brief
   - memory
   - surfacing notes
   - time context
   - people context
3. **The brief is private context, not an opening line.** Zola absorbs it and never recites it, summarises it or announces what she knows (Context Injection, kept; P9-D10: *"injecting is not telling"*).
4. **Confidence gates every recall.** Use the chosen interpretation when sure. Soften it when moderately sure ("You mean the 4Runner?"). When unsure, ask briefly instead of guessing.
5. **Explicit intent wins.** The order of precedence is:
   1. what the person just said
   2. the active topic
   3. the active task
   4. a recent branch
   5. the environment
   6. history
   7. assumptions

   (Domain Priority Matrix, kept.)
6. **A conversation belongs to its participants.** Its contents are available to the people in it and to nobody else, unless ARCH-13's rules allow it (§7).
7. **Record what actually happened: nothing more, nothing less.** P7-D01 governs transcript admission, and A07 owns the streaming boundary.
   - **Never committed.** Speech that was never submitted stays out of history and memory: partial transcripts, cancelled captures, abandoned drafts.
   - **Admitted requests stay.** A request that was admitted remains a request in the conversation, even if the answer was interrupted.
   - **Actions keep their outcomes.** An action that executed keeps its actual outcome, even if what followed was cancelled.
   - **Interrupted is not delivered.** An interrupted answer is recorded as interrupted, never as fully delivered.

   Cancellation must never erase the context needed to explain an action or to continue the conversation.
8. **No synthetic user turns.**
   - Background work never impersonates a conversation (P9-D01).
   - Crash replay carries no person's authority (P9-D02).

---

## 3. What a "conversation" is on Windows

| Term | Meaning | Owner |
|---|---|---|
| **Session** | One Hermes session row: durable, resumable, with its own transcript. The Windows conversation *is* this row (C6). | Hermes |
| **Conversation** | The live exchange happening in a session right now, with its participants | Hermes session + this doc |
| **Participants** | Who is in the conversation: verified people and unverified people/guests (ARCH-12), from A07/A09 recognition | A07, A09 (identity); this doc (membership) |
| **Derived continuity state** | Topic stack, active entities, unresolved references, momentum. Rebuildable, never an authority. | This doc |
| **Episode** | A summary of what mattered, written by consolidation | A03 |

**What is dropped from the Android session model.** The Android model had a separate `SessionRecord`, app-foreground start/end and a 30-second grace period (MD-D05). Hermes's resumable sessions replace them. Three principles are **kept**:
- one session authority (Hermes)
- the session id recorded as provenance on durable writes
- consolidation promptly at session end, not only nightly, so a new session finds memory already up to date. On Windows, consolidation must not depend on the unreliable `on_session_end` (P6-D03).

---

## 4. Continuity within a conversation

### 4.1 Topics, branches and the return stack

Conversations are a **graph of topics**, not a straight line. Example:
- 350Z swap
  - wiring harness
  - clutch hydraulics

When a detour starts, the current topic is **pushed** onto an ordered stack. On return, the most recent detour is **popped**, and each paused topic keeps its unresolved references. The stack unwinds in order:

| Step | Stack |
|---|---|
| Start | `[fuel system]` |
| A text arrives and gets discussed | `[fuel system, text]` |
| A weather question | `[fuel system, text, weather]` |
| "Back to the text" | `[fuel system, text]` |
| "Anyway, the fuel system" | `[fuel system]` |

Returns are acknowledged with a natural bridge ("Right, back to the fuel lines: you were deciding on the pump"), so the person knows she tracked the detour.

**Rules (kept from both sources):**
- It is an ordered stack, never a flat list or a single "previous topic".
- Only the stack changes topic state; nothing mutates it from the side.
- Stale abandoned branches are pruned eventually. *The size and decay of the stack are unvalidated.*

### 4.2 Resolving references

"It", "that line" and "the connector" resolve against:
- the active topic
- active entities
- the stack
- relevant memory

Resolution follows the confidence rules (principle 4). A wrong resolution is worse than a short question.

**Kinds of reinjection, and how each is gated:**
- **Direct.** "back to the harness" restores the branch.
- **Implicit.** "it still won't start" is resolved to the 4Runner, if confident.
- **Environmental.** Being in the shop raises the weight of car threads. That needs A08/A09 signals and is deferred.
- **Emotional.** A tone like a past hard conversation may reconnect it. This gets a higher confidence bar and **emotional-respect rules**: sensitive topics are never casually resurfaced (ARCH-04).

### 4.3 Momentum and pacing

Zola adapts to the shape of the conversation:
- rapid technical back-and-forth: short and direct
- reflective: slower and warmer
- brainstorming: build on it, don't close early
- emotionally heavy: careful, and not problem-solving unless invited

Identity and personality own her style (A02). This doc owns *noticing* the mode.

---

## 5. Continuity across conversations

- **Starting a conversation.** The one context-assembly path (principle 2) prepares a **session brief**: who is relevant, where things left off, what is unresolved, and what is time-sensitive. Rules for the brief:
  - **Structured.** It is structured, not prose.
  - **Budgeted.** It has a size budget. *The Android figure of 2,000 characters is unvalidated.*
  - **Priority order (provisional).** The inherited Android order drops parts from the bottom:
    1. people
    2. the active frame
    3. the recent summary
    4. unresolved items
    5. time-sensitive facts

    *This order is unvalidated.* A part that doesn't fit is dropped whole, never cut off mid-line, and dropping one part never damages another. Whatever is directly relevant to the current request or moment should outrank a large people roster. A long list of people must not crowd out an appointment in an hour.
  - **Optional context never blocks; mandatory checks always run.**
    - Optional context can time out or arrive partially, and a partial brief is fine.
    - Some checks are never skipped to start faster: who is speaking, which session this is, who can hear, and what context is permitted (§7, A14).
    - If those can't be established, the speaker is treated as a guest and nothing protected is brought in (ARCH-12; fail closed).
  - **Seed, not ceiling.** In-turn recall still runs and may add to or refine the brief. Confidence alone never overrides newer corrections, source authority or disclosure restrictions (A03 §4, §7, §9).
- **Mid-conversation refresh.** A bounded refresh may run when the topic shifts or after a while. It runs through the *same* assembly path, never a second one, and has a short timeout that fails closed. *Android: 15 turns or 10 minutes, 500 characters, 1.5 s; all unvalidated.*
- **Gaps.** Time since the last conversation comes from A05 §6 (`last_interaction_at`), per person. The next conversation reflects it: twenty minutes away resumes more naturally than three days.
- **Searching past conversations** happens **only when asked** (P5-D06). Automatic continuity comes from episodes and curated memory (A03), not from mining transcripts.
- **Surfacing after a gap.** On the first turn after a gap, a bounded note of what came in may be injected (P9-D10). It goes through the assembly path, and injecting it is not telling.

**Assembly is read-only.** Preparing a session brief or a refresh, and putting it into the conversation, **never**:
- writes memory or creates a fact;
- triggers consolidation;
- closes, opens or changes a watch.

A brief may be **reused** only as a rebuildable copy, never a new store of truth. Any reuse is scoped to the person, the session and the purpose, and is thrown away on a correction, a forget, a change of audience or permission, or when it goes stale. *The Android date-only household cache key is not carried: it could bring one person's private context into another's session.*

---

## 6. When Zola starts the conversation

- **One decision point.** Whether she speaks up is decided in one place (A10, ARCH-09), and how she does it is A11. This doc owns what happens **after** she speaks.
- **The proactive line is part of the conversation, recorded as delivered.** It goes into that participant's conversation as **a Zola message, never a synthetic user turn**, so a reply like "what did he say?" works without restating anything (direction §4; S87 today).
  - **Two things are recorded separately:**
    - the *authorised content*: what she was cleared to say;
    - the *delivery outcome*: completed; interrupted, with how far it got; or not delivered. This matches P9-D11's evidence rule, "accepted, started, and completed are separate".
  - **Follow-ups rely on what played.** She records what played and where it stopped; acknowledgement is kept separately. Playback is never proof that someone heard or understood. She never assumes a half-played line was heard. Asked "what was that?", she repeats the whole announcement, not just the rest.
- **Follow-up listening.** After she speaks, follow-up listening opens, gated by the speech work (A07). Today a proactive line does not open a follow-up listen (P9-SPEAK D7 (a)), which is a temporary limit (Brian, 10/19).
- **Only the intended audience hears content.** An unprompted line containing protected content goes only to its permitted audience (A14 P9, ARCH-11).

---

## 7. Several people: participants, privacy and handoff

This section owns the mechanism required by A03 §9, A14 P12a and scenario K.

### 7.1 Participants, audience and recipients

These are three different groups, tracked separately:

| Group | Who | Effect |
|---|---|---|
| **Participants** | Who is actively in the conversation | Their requests are handled under their own authority (§7.4); the context brought in must be permitted for all of them |
| **Audience** | Everyone who could hear or see Zola's response: participants plus bystanders in earshot or view | Limits what she may *say or show* right now |
| **Intended recipients** | Who a statement was addressed to (ARCH-13) | Decides who may hear it again later |

**A bystander limits output but gains no access.** Bre walking through the room while Brian talks is *audience*, not a participant and not a recipient.
- While she can hear, Zola says nothing protected.
- Bre gains no right to ask about the conversation afterwards.
- What Brian said before she arrived, or said to Zola rather than to her, is not "told to Bre".

Membership comes from recognition (A07 voice, A09 camera):
- A **verified** participant is known.
- An **unverified** person is treated as a guest (ARCH-12).

When Zola can't tell whether someone is joining or just passing through, she treats them as **audience, not participant**: she restricts what she says and counts nothing as told to them. Membership can change mid-conversation.

### 7.2 What a shared conversation means

**What participants say to each other.** When Brian and Bre are both *participants* talking with Zola, what either says to the group is addressed to the group. Under ARCH-13 the recipients are the participants. That is ordinary speech, not a leak. A bystander who happens to overhear is not a recipient.

**"Mixed company" in ARCH-17** means the participants. Brian re-raising a subject *with the participants* opens that subject there (C14).

**What Zola brings in.** The context-assembly path brings in only what **every participant** may receive, and says only what **everyone in the audience** may hear (A14 §3):
- Nothing private to Brian.
- Nothing private to Bre.
- No household information while a guest or unverified person is present.

### 7.3 The structural constraint, and the handoff rule

**The constraint.** A Hermes session's transcript is visible to the model on every later turn. Private content cannot be "filtered out" of a session that already contains it.

**The rule.** When the participants change in a way that would expose one person's private conversation to someone else, Zola must **move to a different session**. She cannot just keep going in the same one. On a handoff:
- **Stop disclosure immediately.** The moment a participant or audience change is detected, protected playback **stops or pauses at once**, even mid-sentence. This happens before the session switch completes.
- **No late delivery to the new audience.** Pending replies, queued speech and late responses from the old session are held for the original person. None of them reaches the new audience.
- **Executed actions are not "cancelled".** An action that already executed may not be reversible.
  - Its result stays with the original requester.
  - Its actual outcome is recorded in that person's conversation (principle 7).
  - Work not yet started is cancelled or held.
- **Injected context is not carried over.** Cached context and memory injected for the previous person do not carry into the new session.
- **The previous person's session is resumable later**, only for that person.

Examples:
- **Same person returning.** Brian steps away; Bre sits down and starts talking. Bre gets her own session, or a new one. Brian's stays his.
- **Someone joining (ARCH-17).** Bre joins while Brian is talking. Zola moves to a **fresh shared session** for the joint conversation. Brian's earlier session stays his and never enters the shared one.
  - **Exception: the speaker re-raises the subject.** If Brian raises that subject again himself in front of Bre, Zola may speak on it there.
  - **Scope (C14, confirmed).** The exception covers only the particular topic that was brought up, and Brian's own information about it. It does not cover other topics from the private conversation, or anyone else's private information that came up in it.

*The handoff mechanism is Claude's design. ARCH-03 and ARCH-17 require the outcomes.*

### 7.4 Who started the turn

Authority for actions comes from **the person who made the request**, verified, never from whoever owns the session (A15). A session started by Brian doesn't make Bre's request Brian's.

---

## 8. Across devices (ARCH-16)

Zola is one presence, with one brain on the PC. When Brian walks from the PC to the shop with the phone and keeps talking, **the same conversation continues** (ARCH-16). Brian: *"All of Zola-Windows should be PC controlled, so we are continuing the same conversation with the same brain."*
- The phone, and any later endpoint, **attaches** to the existing Hermes session on the PC. No endpoint holds its own conversation.
- This reverses the Android rule "a new device always starts a new session" (MD-D05).

**Requirements:**
- Restoring the wrong state is worse than restoring none (Conversational Continuity §12). When in doubt, she starts fresh, informed by memory.
- Two devices never become two competing conversations for the same person at once without a defined owner (A12).
- The handoff rules of §7 apply across devices too. The phone in Bre's hand is not Brian's conversation.

---

## 9. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| Windows client wraps the Hermes session row; resumable sessions | live-tested | P1 | C1, C6 |
| One capture owner; one transcript admission authority; cancel invalidates | live-tested | P2, P7 | C3, P7-D01–D03 |
| Clarify requests (typed and voice) | live-tested | P4, P7 | P4, P7 |
| Past-conversation search only on request | live-tested | P5 | P5-D06 |
| Episodes; ambient time; gap awareness | live-tested | P6 | P6-D04, D05 |
| Memory and fact injection each turn (USER/MEMORY files; `zola_memory` prefetch) | live-tested | P5, P6 | C4, P6-D01 |
| Surfacing note on the first turn after a gap; `whats_pending` | live-tested | P9 | P9-D10 |
| Proactive line shown as a bubble but **not stored** in the session; resume rebuilds without it | known limit | P9 | S87 |
| Proactive line does not open follow-up listening | live (by decision) | P9 | P9-SPEAK D7 (a) |
| Crash replay resumes the stored session, with no Brian authority | live-tested | P9 | P9-D02 |
| Topic stack, branch return, reference confidence | **not built** (Hermes's own context only) | — | — |
| Session brief through one assembly path | **not built** (two injectors today) | audit Q7 | DQ-8 |
| Participants, per-person sessions, handoff | **not built** (one user) | — | S1; ARCH-03 |
| Cross-device conversation | **not built** | — | ARCH-16 (intent) |

---

## 10. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| Proactive line not stored in the session | temporary limit | — | S87; Brian's 10/19 classification |
| No follow-up listening after an unprompted line | temporary limit | — | P9 D7 (a); speech work |
| Two context injectors (memory prefetch, surfacing) | temporary limit | — | DQ-8 |
| One participant assumed (Brian) | temporary limit | — | ARCH-03, ARCH-12 |
| Ordinary-reply echo can become a ticketed turn | temporary limit | yes | P9 S77 |
| Hermes owns the transcript; no rival state engine | lasting boundary | — | C1, C6, principle 1 |
| Private content never crosses to another person's conversation | lasting boundary | — | ARCH-03, A14 P12a |
| Transcript search only when asked | lasting boundary | — | P5-D06 |
| The brief is never recited | lasting boundary | — | §2 p3 |
| Environmental reinjection; momentum detection | deferred capability | — | A08/A09 signals |
| Cross-device conversation (same session) | deferred capability | — | ARCH-16, A12 |

---

## 11. Open questions

- **B11.** *Resolved by ARCH-16:* one conversation across devices.
- **Q-C1.** *Resolved by ARCH-17:* a fresh shared session, with the re-raised-subject exception. The scope was confirmed by C14: only the particular topic.
- **Q-C3.** *Agreed (ARCH-17):* once alone again, the person resumes their own earlier session, informed by memory of the shared one.
- **Q-C2: how participant changes are detected** (voice, camera, an explicit "this is Bre"), and how fast. This belongs to A07/A09. Until recognition exists, the Windows client assumes Brian (S1).
- **DQ-8: who owns the context-assembly path.** This is a P11 audit question.
- **How the brief is delivered through supported Hermes hooks**, without editing Hermes. This is an audit question.

---

## 12. Acceptance scenarios

- **C1. Implicit reference.** Mid-way through 4Runner troubleshooting, Brian says "it still won't start". She resolves it to the 4Runner. If two vehicles were in play, she asks which.
- **C2. Branch return.** fuel system → text → weather → "back to the text" → "anyway, the fuel system". It unwinds in order, and the unresolved pump choice is restored with a bridge phrase.
- **C3. Never recites.** She opens a conversation after a day away. She doesn't say "I see you have three open items"; she just knows them.
- **C4. Reply to an unprompted line.** She says "Micah texted: his car won't start at the school." Brian replies "what else did he say?" She answers without restating, because the line is part of the conversation (target behaviour; S87 today).
- **C5. Handoff (A03 scenario K).** Bre has a private conversation with Zola. Brian then sits down at the PC and starts talking.
  - Brian's conversation contains none of Bre's turns, cached context or pending replies.
  - Asked "what were you and Bre talking about?", Zola reveals nothing without Bre's approval.
- **C6. Joint conversation.** Brian and Bre talk to Zola together. Zola brings in nothing private to either of them. What each says in the conversation is heard by both, which is ordinary.
- **C7. Guest present.** A guest joins. Household information stops being brought in while they are present, and ordinary conversation continues.
- **C8. Failed recall.** Retrieval fails mid-conversation. She says she doesn't recall rather than inventing anything (A03 scenario G).
- **C9. Topic stack: Memory Hierarchy scenario F.** Same as C2.
- **C9b. Interrupted mid-answer.** Zola is halfway through a private answer to Brian when Bre walks in.
  - Playback stops at once.
  - The rest of the answer is held for Brian.
  - No late reply from Brian's session reaches the room while Bre is there.
  - The record shows the answer was interrupted, not delivered.
- **C9c. Bystander.** Bre walks through the room and doesn't join. Zola holds protected content while Bre can hear. Afterwards Bre asks "what was Brian asking about?", and Zola reveals nothing: Bre was audience, not a recipient.
- **C9d. Half-played proactive line.** A proactive line about Micah's text stops halfway because Brian presses the mic. Brian asks "what was that?" The record shows where playback stopped. Zola repeats the whole announcement.
- **C9e. Action already done.** Brian approved a send, and it went out. Bre then sits down. The send's outcome stays in Brian's conversation, and Bre's session doesn't mention it.
- **C10. Across devices (ARCH-16).** Brian is talking with Zola at the PC about the 4Runner. He walks out with the phone and says "so what do you think it is?" The same conversation continues, with no restating.
- **C11. Re-raised subject (ARCH-17).** Brian privately discussed the 4Runner repair cost with Zola. Bre joins, and Zola moves to a shared session.
  - Zola doesn't bring up the cost.
  - Brian then says "Zola, what was that repair estimate?" in front of Bre. Zola may answer about that estimate.
  - She does not bring up any other topic from Brian's private conversation.

- **C12. The brief changes nothing.** Building Brian's session brief touches an overdue commitment. The watch stays open, and no memory is written. Bre starts a session ten minutes later: she gets a brief built for her, not Brian's reused.

---

## 13. Coverage of the source docs

**Status:** *verified* means the destination exists and was checked against a fresh full read on 2026-10-29. *verified (notes)* means it was checked against the full-read notes. *planned* means the destination doc is not yet written.

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Continuity: vision, "conversation never ends" | §1 | preserved | verified |
| §1 Conversational State Engine | §2 p1, §3 | **superseded**: Hermes session is the authority; Zola state is derived (C1, C6) | verified |
| §2 Topic Graph | §4.1 | preserved | verified |
| §3 Attention layer (weights, decay, inputs) | §4.2; A07 | merged; numbers unvalidated | verified |
| §4 Reinjection types | §4.2 | preserved; environmental deferred; emotional gated by ARCH-04 | verified |
| §5 Branch recovery; §6 Focus stack | §4.1 | merged (one stack) | verified |
| §7 Temporal continuity tiers | §5; A05; A03 §3.4 | merged | verified |
| §8 Momentum | §4.3; A02 | merged | verified |
| §9 Confidence scoring | §2 p4, §4.2 | preserved | verified |
| §10 Safety rules (no forced recall, emotional respect, relevance, not surveillance) | §1, §4.2 | preserved | verified |
| §11 Consolidation engine | A03 §5 | moved | verified |
| §12 Snapshot and sync | §8; A12 | merged; "wrong restore is worse than none" kept | verified (A12 §7 checked) |
| §13 Domain Priority Matrix | §2 p5 | preserved | verified |
| §14 Turn lifecycle (five stages) | §2 p7; A07 | merged | verified |
| Module structure (Kotlin) | — | intentionally dropped: platform plumbing | n/a |
| Failure modes; open questions; risks | §4, §8, §11 | merged | verified |
| Session Identity: purpose, `SessionRecord`, single mint site | §3 | superseded by Hermes sessions (C6); provenance and prompt-consolidation principles kept | verified |
| Session Identity: foreground/30 s grace | — | intentionally dropped: Android lifecycle | n/a |
| Session Identity: no cross-device continuity | §8 | **superseded by ARCH-16** | verified |
| Context Injection: brief concepts (private context, structured, one builder, read-only, priority, seed not ceiling) | §2 p2–p3, §5 | preserved | verified |
| Context Injection: PCI-D04 read-only; PCI-D09 reuse cache | §5 "Assembly is read-only" | retained (audit C05); date-only household cache key intentionally omitted (privacy) | verified (fresh read 2026-11-02) |
| Context Injection: **PCI-D01 household-scoped brief** | §7.2 | **superseded** by ARCH-03/ARCH-13: context is scoped to who's present, never "covers everyone" | verified |
| Context Injection: PCI-D02 amendment (bounded refresh) | §5 | preserved; numbers unvalidated | verified |
| Context Injection: budget, cache, injection path (Gemini Live, RTDB, warm-start retirement) | §5; — | budget kept as an unvalidated principle; platform parts dropped | verified (fresh read 2026-11-02) |
| Memory Hierarchy §8 topic stack | §4.1 | merged | verified |
| Agent Map agent 4 (warm start) | §5 | superseded by the brief (as Android also did, PCI-D05) | verified (fresh read 2026-11-02) |
