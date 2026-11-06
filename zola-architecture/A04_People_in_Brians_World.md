# A04 — People in Brian's World

*Draft v0.2, 2026-10-29, revised after ChatGPT's review. Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.**

*v0.3, 2026-11-02 — reconciliation pass after the coverage audit: guest shortlist (ARCH-38); visitor signatures two weeks (ARCH-37).*

*Re-audit corrections, 2026-11-02: evidence label updated.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:**
- `Zola_Architecture_Relationship_Inference.md` (Android P19 locks, which are not Windows locks)
- `Zola_SocialGraph_Reasoning_Architecture.md`
- the people-related principles of `Zola_Relational_Intelligence_Layer_Architecture.md`

**Builds on:**
- A03: the world model, the evidence model, identity, promotion, forget and per-person scope
- A14 and A15 boundary drafts

**Governing records:**
- ARCH-02, ARCH-03, ARCH-05 to ARCH-07, ARCH-12 to ARCH-14
- Brian's 2026-10-19 direction (§3 unified identity; §4 relationship understanding as its own responsibility)
- the P11PRE audit scope (Q2, Q3; DQ-2, DQ-3)

**What this doc does not decide.** It decides no Phase 11 question. Android numbers below (confidences, thresholds, windows, back-offs) are **unvalidated**.*

---

## 1. Intent

Zola knows the people in her world as **understood presences**, not as contact cards. She knows:
- who they are and how they connect to each other;
- what they mean to the people she lives with;
- what has been said about them, and by whom;
- how sure she is of each piece.

> Less like "an assistant that remembers the names you've mentioned", more like "a presence that knows the people in your world and understands how they matter to you." (Social Graph, kept)

Three things are new for Windows.

**She learns about people from what she observes, not only from what Brian says (ARCH-06).** Micah's texts, an email from the school, a Contacts entry and the calendar are all evidence about people. Each is attributed and weighed under A03's rules. She is not "a reflection of me, but of herself growing in the world" (ARCH-02).

**She is a presence for each person in the household (ARCH-03).** Bre and the boys are not only people Brian talks about. They speak for themselves, Zola builds her own relationship with each of them, and each person's information is private to them (A14). This changes one Android principle. On Android, "everything Zola knows about people comes through the user's perspective". On Windows, a household member's own statements about themselves are first-hand.

**Relationship understanding is its own responsibility** (direction §4; A01 §1.2). This doc answers *who is this person to the person concerned*. That answer is kept separate from:
- **source trust:** is this message really from Micah?
- **importance:** does this message matter now? That is A10's question.
- **permission:** may Zola tell them, or do something for them? That is A14 and A15.

A saved contact establishes a known sender, not closeness. Frequent contact is evidence, not importance.

**What this should feel like:**
- *"Micah texted. Your son, about the 4Runner."* She knows who he is without being told again.
- *"Is this the same Tom from the shop, or someone else?"* She asks naturally, once, at a good moment, instead of guessing.
- Brian vents that Marcus was useless today. A week later she doesn't describe Marcus as unreliable.
- Bre asks Zola about her own week. Zola answers from what Bre has shared, not from what Brian said about her (A03 §9).

---

## 2. Principles

1. **One person, one entity.** A person is one entity across Contacts, email, phone, conversation, memory and, later, their voice and face (A03 §6). There is one person resolver (P10-D18), and one relationship vocabulary.
2. **Relationships are evidence-backed facts with provenance.** Every relationship records:
   - its source;
   - its attribution;
   - its confidence;
   - its time;
   - its permitted use.

   This is A03's evidence model; nothing is special to people.
3. **Store what was stated or established; derive the rest.** Only direct relationships are stored, and only when they are stated or established by approved promotion. Everything that follows from them is worked out at read time with its path and confidence. That includes siblings (ARCH-14), grandparents, aunts, cousins and in-laws. No stored inference without an approved, named exception.
4. **Reciprocals are one fact.** "Brian is Micah's parent" and "Micah is Brian's child" are the same relationship seen from two ends. It is one fact, not two separately maintained facts. *(Claude's recommendation, following ARCH-14's reasoning.)*
5. **Secondhand is held loosely.** What one person says about another is that person's account. Venting does not harden into character (§6).
6. **No psychological profiling.** She tracks stated facts, structure and attributed behaviour. She never infers personality types or makes "type of person" judgments about anyone (A03 §5.7).
7. **Background texture, not headlines.** What she knows about people shapes how she talks, invisibly. She doesn't narrate her model of someone, and she doesn't volunteer observations about relationship patterns that nobody asked about.
8. **Conservative identity.** A wrong link between two people is worse than a missed one. When unsure, she asks or waits. She never guesses (A03 §6).
9. **Recognition identifies; policy permits.** Knowing who someone is never grants them anything (A01 §1.3, ARCH-07, ARCH-12).

---

## 3. What a person is in the model

A **person** entity holds:
- **Names, nicknames and aliases**, plus the identifiers that resolve to them:
  - numbers, including RCS senders that are not numbers;
  - email addresses;
  - Contacts entries;
  - later, voice and face (ARCH-07).
- **Relationships**, typed links to other entities (§4).
- **Attributes stated or established about them** (birthday, school, job), each with full provenance.
- **Attributed claims and observations about them**, each with its speaker, recipients and permitted audience (A03 §9, ARCH-13).
- **Their own relationship with Zola**, if they are a household member (A02/A02b).
- **Lifecycle:**
  - candidate (noticed, not yet known);
  - known;
  - in the household;
  - guest seen before;
  - forgotten.

**Three separate steps.** These are never merged:
1. **Recording an attributed introduction or claim.** "Mike says this is his cousin Dave" is kept as Mike's statement.
2. **Creating a person record.** A stable id for a person Zola now knows exists.
3. **Confirming a match.** The person present (a voice, a face, a sender) *is* that record.

An introduction does steps 1 and 2 right away. Only confirmation does step 3.

**No accidental duplicate records for the same person.** Two different people who share a name (two Toms) get two separate records, each with its own stable id. No suffixed names ("Tom_2") are used. The ids are what keep them apart.

**How someone becomes known.** The Social Graph's "people earn their place" intent is kept, adapted to Windows sources. A person record is created when one of these happens:
- **Introduction.** Someone introduces them: "that's my brother", "Marcus works at the shop". The record is created right away. It is attributed to the person who made the introduction. Confirming that the person present matches the record is step 3.
- **Contacts seed.** A Contacts entry creates a **known-sender** entity with that contact's identifiers. It brings no closeness, trust or importance (A03 §5.3).
- **Attributed evidence.** Retrieved records refer to the same identified person, for example a text from a number that resolves to one contact. These follow A03's promotion rules for retrieved records.
- **Recurrence.** A name keeps coming up across distinct conversations over time. Spread across separate conversations counts; many mentions inside one conversation do not. *Android used 3 sessions in 90 days; unvalidated.* The count lives in A03's bounded recurrence record (§5.6).
- **Seen or heard.** For someone she sees or hears (ARCH-07), see §8.

A name mentioned once in passing stays in its episode and gets no person entity of its own.

---

## 4. Relationships

### 4.1 Vocabulary

There is one vocabulary covering at least these families.

| Family | Examples |
|---|---|
| **Family** | parent / child, spouse or partner, sibling (derived; ARCH-14), step-relationships, in-laws, extended family (derived unless stated) |
| **Social** | friend, neighbour, acquaintance |
| **Work and organisations** | employee of, works at (no employment implied), colleague, reports to, customer, client |
| **Service and role** | "my mechanic", "Micah's teacher", "our doctor", "the bank", "the school". Roles are relationships to a person or an organisation, never labels on the person (A03 principle 1). |
| **Ownership and use** | owns, drives, regularly uses (people → vehicles, devices, places) |
| **Zola's own** | Zola's relationship with each household member (A02b and its equivalents); "Zola knows about" (awareness) |

The Android predicate list was kinship plus a few work predicates. The service, role and organisation family is new. Brian's world includes the mechanic, the school and the bank. Knowing that someone *is the mechanic* is what lets "the shop called" mean something.

*Which relationship types the Phase 11 first slice builds is DQ-3.* The 4Runner test needs at least parent/child and ownership.

### 4.2 What is stored and what is derived (ARCH-14)

- **Stored:** relationships someone stated directly ("Micah is my son"), or that reached established status through an approved promotion rule (A03 §5.3, DQ-5). Every user-statable relationship can be stored when stated, including an aunt or cousin named directly.
- **Derived at read time:**
  - siblings (from a shared parent);
  - grandparents and grandchildren;
  - aunts and uncles;
  - nieces and nephews;
  - cousins;
  - step-relationships (via a partner);
  - in-laws.

  Each derived relationship comes with:
  - the path it was derived through;
  - a confidence that falls with each hop;
  - a depth limit. *Android used 3 hops, minus 0.1 per hop, with a floor of 0.5; unvalidated.*
- **Derivation respects privacy.** Every link used in a derivation must be allowed in the current conversation, judged against the person being spoken to (A03 §9, ARCH-13). If a supporting link is not permitted, the derivation does not happen for that person. She answers only from what they may know, or says she can't say. Filtering the wording of the final answer is not enough. A private parent link must not leak through a sibling or grandparent answer.
- **Labels follow what is known.** If the gender of the person in the middle is unknown, she uses a neutral label ("your dad's sibling"), never a guess. The same applies to half- versus full siblings when only one parent is recorded (Q-C).
- **How sure she sounds follows how far the path goes.** A close, well-supported derivation can come up naturally when relevant. A distant or weak one comes up only when someone asks.

### 4.3 Truth maintenance

Because derived relationships are computed when needed, a correction to a stored relationship carries through to the derived ones. Take "Cole is my nephew, not my son":
- the stored parent link changes;
- Jake and Cole stop being derived siblings;
- no derived sibling link has to be cleaned up.

**Copies still need clearing.** An old answer can still sit in a summary, brief, cached context or pending reply. A03 §7 requires every such copy to be invalidated; that rule applies here.

**Conflicting statements follow A03's evidence and conflict rules. There is no automatic override.** What a new statement does depends on who says it, about whom, and with what standing:
- **Standing to correct.** Brian correcting a relationship he stated himself ("Cole is my nephew"), or a person stating their own relationship, supersedes the earlier version. The history is kept.
- **No standing.** A guest saying "Micah isn't Brian's son" creates a *conflicting attributed claim*, kept as the guest's statement. It does not replace an established relationship.
- **Genuine conflicts** stay contested and can be explained. They are never silently resolved (A03 §7).

---

## 5. One identity across sources

This section applies A03 §6 to people.

- **The person resolver** maps every identifier to one person entity:
  - Contacts entries;
  - email addresses;
  - phone numbers, including non-number RCS senders;
  - names and aliases;
  - later, voice and face.

  The Phase 10 Track 5 contact index is its first part. It is shaped as a resolver from the start, one person with all their numbers and addresses, not a phone-only lookup. P10-D18 makes one resolver an architectural boundary: ordering, watches and forget use it and never resolve people on their own. Google Contacts as its only source is a temporary limit; a Contacts entry means a known sender, not a relationship or trust.
- **Automatic vs confirmed links are DQ-2.** Not decided here. Claude's starting point for that decision:
  - **Possibly automatic:** exact identifier matches inside one authoritative record, such as two numbers on the same Contacts entry.
  - **Need confirmation:**
    - linking a Contacts entry to an existing memory entity by name alone;
    - merging two people who share a name;
    - shared or family addresses.
- **Same name, different people.** Example: "Tom from work" and "Tom, Bre's dad". The approach is kept from the Social Graph:
  - She asks naturally, once, at a good moment: "Is this the same Tom from the shop, or someone else?"
  - She uses context clues (shop, family) to keep things apart in the meantime, without merging.
  - If the question is ignored, it is deferred, not failed.
  - If it is ignored repeatedly, she backs off for a while instead of nagging. *Android backed off 14 days after 3 ignored asks; unvalidated.*
  - No suffixed duplicate people ("Tom_2") are ever created.
- **Shared identifiers.** A family email address or a shared landline resolves to a household or group, not to whichever member is guessed. Who actually wrote the message stays unknown unless the content or the person makes it clear.

---

## 6. What people say about each other

All of this applies A03's evidence model (§4, §5.5) and ARCH-13.

- **Everything about a person records who said it.** That covers:
  - what Brian says about Micah;
  - what Micah says about himself in a text;
  - what Bre says about her own plans;
  - what a guest says.

  Each is a different speaker, with a different authority and a different permitted audience (ARCH-13).
- **First-hand vs secondhand.** A person's own statement about themselves carries more weight than someone else's account of them. That includes a household member's statement and a contact's own message. Secondhand claims carry a lower confidence ceiling.
- **Venting doesn't harden into character.** Behavioural claims about someone that are made in frustration enter as **provisional** (A03 §5.4).
  - "Marcus is useless today" stays provisional and shapes hedging only.
  - It becomes established only through explicit confirmation or fresh, independent attributed evidence, under approved rules. Confirmation establishes *the speaker's considered view*, not an objective trait: "yeah, Marcus is generally unreliable" becomes "Brian considers Marcus generally unreliable". It is never "Marcus is unreliable".
  - **It never becomes established because nobody corrected it.** The Social Graph's passive "three sessions without correction" rule is **superseded** (A03 §5.5: silence is not confirmation).
  - It is retired when the speaker walks it back ("I was just frustrated — he's solid").
- **Provisional claims are never surfaced as observations.** They only shape how carefully she speaks.
- **Contact frequency is evidence, not importance.** How often Brian emails someone can inform her understanding, but it never becomes a "relationship weight" that decides how much someone matters. The Cross-Domain design's frequency-based weight is superseded (F8).

---

## 7. The household

This section applies ARCH-03, ARCH-12 and ARCH-13.

- **Household members are full entities, with their own voice in the model.** Brian, Bre and the boys each speak for themselves. Zola builds her own relationship with each one.
- **Their privacy holds in every direction.**
  - Retrieval is scoped to the person in the conversation (A03 §9).
  - Disclosure follows the default audience: speaker, recipients and subject (ARCH-13).
  - Handoff between people at one endpoint carries nothing over (A03 §9; scenario K).
- **Shared household information is today only the family calendar** (ARCH-03).
- **Who is in the household** is a stated fact. It comes from Brian, not from inference about who is around a lot. *How membership is recorded and changed belongs with A15's approval methods (Q-D).*

---

## 8. People she sees or hears (ARCH-05, ARCH-07, ARCH-12)

- **She learns the voice and face of anyone she sees.** She has two purposes:
  - her own recognition;
  - giving accurate information if someone attempts something unauthorised.
- **Someone she hasn't identified is a noticed candidate, not a known person.** The candidate is linked to the evidence of when and where she noticed them. It carries no assumed name or identity.
  - "Mike says this is his cousin Dave" is attributed evidence toward an identity, not the identity itself (A03 §5.7).
  - A candidate becomes a known person through confirmation under DQ-2's rules.
  - If she is engaged in the conversation, she may ask who they are. Otherwise she just notices them and does nothing else (ARCH-05).
- **Guests can talk with her.** What they say is kept as their attributed statements. They get no household or private information. Nothing runs on their requests except the shortlist of harmless lookups (A14 P4, A15 X5, ARCH-38).
- **An unverified speaker is treated as a guest until verified**, even if they sound or look like a household member (ARCH-12).
- **Retention.** The face or voice signature of someone seen once is kept **two weeks**, including every copy and anything derived from it. Seeing them again doesn't quietly make them permanent; they become a known person only through confirmation (ARCH-37; A09 §6).

---

## 9. How what she knows about people reaches the conversation

- **Through the one governed context-assembly path** (A03 §10; DQ-8). There is no separate "social context" injector. The Android `[SOCIAL]` brief section becomes part of that one path.
- **What is offered:**
  - who the active people are and how they connect;
  - relevant attributed facts, with their confidence;
  - provisional flags, so she hedges;
  - a gap signal when her thin knowledge of a relevant person matters right now.
- **What is not offered, unless asked:**
  - observations about relationship patterns or dynamics;
  - provisional claims stated as facts;
  - another person's private information (ARCH-13).
- **Gaps surface only when they matter.** Asking "Who's Dave?" is fine when Dave is part of a decision being made now. A questionnaire is not.

---

## 10. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| People as `[person]`-tagged lines in `USER.md`/`MEMORY.md` | live-tested | P5 | C4, P5-D05 |
| Entities with aliases in the `zola_memory` index; entities organise, they don't author | live-tested | P6 | P6-D01, P6-D02 |
| Contacts lookup on a ticket turn, for a spoken name (P9) | live-tested | P9 | P9-D11 (D5 (b)) |
| Contact index with numbers and addresses per contact; read-time match; contacts ranked above unknown numbers | shipped (P10) | P10 closeout | P10-D10, P10-D18 |
| Watching a person across texts and email | shipped (P10) | P10 closeout | P10-D13, P10-D19 |
| Forget by person or number | shipped (P10) | P10 closeout | P10-D14, P10-D19 |
| Forget by person misses an address known only in Contacts | closed at the Phase 10 closeout; other name forms remain (S96) | P10 closeout | S85 (partly resolved), S96 |
| Structured relationships, read-time derivation | **not built** | VISION_ALIGNMENT_REVIEW G4 | ARCH-14 (intent) |
| One identity per person across sources | **not built** | G1 | P10-D18; S96 |
| Per-person household model, recognition | **not built** | — | S1 deferred; ARCH-03, ARCH-07 |

---

## 11. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| People are text lines, with no structured relationships | temporary limit | — | P6-D01; DQ-1 and DQ-3 |
| Contacts lookup only on Brian's turns; the watcher never calls Contacts | temporary limit | — | P9-D04 (sender resolution (a)) |
| Contact match is the only "known sender" signal | temporary limit | — | P10-D10; Contacts must not define trust or relationship (direction §4) |
| Forget-by-person misses Contacts-only addresses | temporary limit | yes | P9 known limit |
| No household recognition; one voice = Brian | temporary limit | — | S1; ARCH-03, ARCH-07, ARCH-12 |
| No psychological profiling | lasting boundary | — | §2 p6 |
| Silence never promotes a claim about a person | lasting boundary | — | A03 §5.5 |
| Derived relationships are not stored | lasting boundary (ARCH-14), unless a later decision names an exception | — | — |
| Longitudinal tone about people ("you seem tense around Marcus lately") | deferred capability, sensitive | — | Needs its own decision and A14 handling |
| Service and organisation relationships | deferred capability | — | §4.1; first slice per DQ-3 |

---

## 12. Open questions

- **DQ-2:** identity-resolution rules (automatic vs confirmed links). Not decided here.
- **DQ-3:** the people and relationship types in the Phase 11 first slice.
- **Q-C. Half vs full siblings.** With only one shared parent recorded, the derived relationship could be a sibling or a half-sibling. Claude's suggestion: say "sibling" only when both parents are shared or someone stated it. Otherwise use neutral wording ("they share a dad") until someone says.
- **Q-D. Household membership.** How it is recorded and changed: Brian states it; is that enough? Who can add a member? This links to A15's per-person approval methods.
- **Q-E. A household member's view of Brian.** *Resolved by the ARCH-13 amendment (Option B).* The subject hears only plain facts about their own affairs. Bre's private "Brian's been stressed lately" stays with Bre.
- **Q-F. People who leave Brian's life.** An ex-colleague, a former neighbour. Do they fade (confidence and recency), or stay until forgotten?
- **Q-G. Retention of faces and voices of people seen once.** *Resolved by ARCH-37:* two weeks.

---

## 13. Acceptance scenarios

These carry into Phase 11 alongside A03 §16.

- **P1. Known person from a text.** A text arrives from a number on Micah's Contacts entry. Zola knows the sender is Micah, Brian's son (relationship from Brian's statement), and says so.
- **P2. Derived relationship.** Brian has said Micah and Dom are his sons. Asked "Who are Micah's brothers?", she derives Dom. If the relationship is uncertain (Q-C), she uses neutral wording. Nothing new is stored.
- **P3. Correction propagates.** "Cole is my nephew, not my son."
  - Cole stops being anyone's derived sibling.
  - No old sibling answer survives in a summary, brief, cached context or pending reply.
  - The history of the correction is kept.
- **P3b. No standing, no override.** A guest says "Micah isn't Brian's son." It is kept as the guest's conflicting claim. The established relationship stands.
- **P4. Same name.**
  - "Tom" comes up in a work context and in a family context. She keeps them apart using context and asks once, naturally.
  - If the question is ignored, it is deferred.
  - No accidental duplicate record is created for the same Tom. Two different Toms have two stable ids.
- **P5. Venting.**
  - Brian: "Marcus is useless today." Marcus is not described as unreliable later.
  - Three later conversations that mention Marcus without correction do **not** make the claim established.
  - Brian: "yeah, he's generally unreliable." Now Zola holds *Brian's considered view*, not an objective trait.
- **P6. Known sender, not importance.** A frequent sender's message and a first-time sender's message are both understood. Neither is ranked by frequency in this layer (A10 decides).
- **P7. Service role.** Brian: "Dave's my mechanic." Later: "Dave called about the car." She connects the call to Dave the mechanic.
  - She links it to a particular vehicle only with evidence: the call or message names it, or only one car fits.
  - Otherwise she asks which car.
- **P8. Introduced guest.** Mike says "this is my cousin Dave."
  - Mike's introduction is recorded, attributed to Mike.
  - A person record for Dave exists.
  - That the man present *is* that Dave is not confirmed until confirmation under DQ-2.
- **P9. Household voice.** Bre tells Zola about her week. Later Brian asks how Bre's week went. Zola doesn't share what Bre said without her approval (ARCH-03, ARCH-13).
- **P10. Derivation behind a privacy wall.** A parent link is private to Bre. With it, Zola could derive that two people are siblings. Asked by Brian "who are X's siblings?", Zola does not derive through the private link, and her answer reveals nothing of it.
- **P11. Subject's own affairs vs a view about them.**
  - Brian tells Zola "Bre has a doctor's appointment Tuesday." Zola may mention it to Bre.
  - Bre privately tells Zola "Brian's been stressed lately." It is not told to Brian.

---

## 14. Coverage of the source docs

**Status:** *verified* means the destination exists and was checked against a fresh full read of the source on 2026-10-29. *planned* means the destination doc is not yet written.

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Relationship Inference: purpose; P19-D01 single schema | §2 p1 | merged (one vocabulary); Firestore schema dropped | verified |
| P19-D02 storage policy | §4.2 | preserved | verified |
| P19-D03 siblings stored | §4.2 | **superseded by ARCH-14** | verified |
| P19-D04 extended family stored only when stated | §4.2 | preserved | verified |
| P19-D05 `derivedFrom`, P19-D06 synchronous inference | §4.3 | superseded (nothing derived is stored, so no lineage on stored inferences is needed); lineage kept for promoted knowledge in A03 | verified |
| §1 schema, confidence defaults by source | §2 p2; A03 §4 | merged; Android numbers unvalidated; Firestore fields dropped | verified |
| §1.5 authority at read time; §4.4 statement supersedes inference | §4.3 | preserved | verified |
| §2 predicate taxonomy (Tier 1/2) | §4.1, §4.2 | merged and extended (service, role and organisation family) | verified |
| §2 PRIMARY_BOND, KNOWS_ABOUT | §4.1 "Zola's own"; A02b | merged | verified (A02b §4 checked) |
| §2.3 direction convention; IR-01 reciprocal edges | §2 p4 | superseded by "reciprocals are one fact" (Claude's recommendation) | verified |
| §3 IR-02 sibling inference, IR-03 no chaining | §4.2 | superseded by ARCH-14 | verified |
| §4 truth maintenance, correction example | §4.3, P3 | preserved (simpler under read-time derivation) | verified |
| §5 traversal depth, confidence decay, surfacing policy, gender | §4.2 | preserved; numbers unvalidated | verified |
| §6 legacy deletion scope | — | intentionally dropped: Android code | n/a |
| §7 open questions | §12 | merged where still relevant | verified |
| Social Graph: vision, philosophy | §1, §2 | merged; "through the user's perspective" updated for household first-hand statements | verified |
| Named Recurrence Threshold; distinct-session tracker | §3; A03 §5.6 | merged; extended with Contacts seed and attributed evidence (ARCH-06); numbers unvalidated | verified |
| Same-name disambiguation, fail-soft, throttle | §5 | preserved; numbers unvalidated | verified |
| Node evaluator, profile builder | §3, §9 | merged (decisions vs writes kept apart via A03's write door) | verified |
| ThirdPartyAssertionGuard, PROVISIONAL | §6 | preserved; **passive promotion superseded** (A03 §5.5) | verified |
| Social context assembler | §9 | merged into A03's one context path | verified |
| Initiative source; what is not surfaced proactively | §9; A11 | merged; initiative mechanics moved | verified (A11 §7 checked) |
| Professional predicates | §4.1 | preserved and extended | verified |
| Integration tables (Kotlin classes) | — | intentionally dropped: platform plumbing | n/a |
| Deferred: longitudinal tone, edge lifecycle, REPORTS_TO/COLLEAGUE_OF | §11, §4.1 | preserved (tone deferred; predicates folded into the vocabulary) | verified |
| Authority boundaries (may / must not) | §2, §9; A03 §5.1 | merged | verified |
| Relationship to the Relational Intelligence Layer | A02b §2–§8 | moved | verified |
| Relational Intelligence Layer: layer-wide principles (third-party beliefs held loosely; observations never headlines; no profiling) | §2 p5–p7 | preserved | verified (destination §2 p5–p7 checked against the original's privacy section, 2026-11-02) |
| Relational Intelligence Layer: subsystem index, S2/S3/A6 Windows notes | A01 §7; A02b; A11 §7 | moved | verified |
| Cross-Domain Correlation: frequency-based relationship weight | §6 | superseded (F8) | verified |
