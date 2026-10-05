# P6-LORE Progress — Phase 6 Lore Closeout

## Branch

- Branch: `p6-lore`
- Base (`main` HEAD at branch create): `44bcac0f39a9c632f24b83e11542321a4da23e5d` (includes P6-FIX-2 merge `fa6c7f0…` + docs `44bcac0…`)
- Prompt version: 1.1 (2026-10-05)
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P6-LORE_Prompt_v1.1.md`
  SHA-256 `1415e757dd0ded7dc52d156a3fcff52bd0c08231632e70d33cda2fa6da6f6a02` (verified 2026-10-05 before Phase 1)
- Decisions snapshot (input): `C:\Users\test\Dev\zola-spikes\prompts\PHASE6_DECISIONS_snapshot.md`
  SHA-256 `54acb3f529548491fb9097206267041433038c04b9e1870d3f67b98669a56b8d` (verified 2026-10-05 before Phase 1)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (detached HEAD, porcelain empty at Phase 1)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch, inputs, inventory | COMPLETE |
| 2 | Draft DESIGN_DECISIONS.md | COMPLETE — accepted (incl. P6-D11) |
| 3 | Draft OPEN_QUESTIONS.md | COMPLETE — accepted (+ S45↔S36 note) |
| 4 | Draft ROADMAP.md | COMPLETE — accepted (D09–D11 wording) |
| 5 | Identity and deploy verification | COMPLETE — accepted |
| 6 | Backup deletion | COMPLETE — deleted 2026-10-05 13:25:18 -07:00 (47/47 gone) |
| 6b | p5* memory-copy scan (read-only) | COMPLETE — DELETE/KEEP reported |
| 6c | p5 DELETE (4 USER/MEMORY only) | COMPLETE — deleted 2026-10-05 13:31:30 -07:00 (4/4 gone) |
| 7 | Apply, verify, STOP | COMPLETE — Phase 7 verified Brian+Claude |
| 8 | Commit and merge | COMPLETE � merge `84df45ffd3da11c968acfd6984563ccb6fe30b1a` |

## Guardrails (from prompt)

- **G-LORE-ONLY** / **G-VERDICTS** / **G-HONEST** / **G-PRIVACY** / **G-DECISION-ID** / **G-RESOLVED** / **G-STOP**

## Phase 1 notes

### SHA verification

| Artifact | Expected | Measured | Match |
|---|---|---|---|
| `P6-LORE_Prompt_v1.1.md` | `1415e757…da6f6a02` | `1415e757dd0ded7dc52d156a3fcff52bd0c08231632e70d33cda2fa6da6f6a02` | ✅ |
| `PHASE6_DECISIONS_snapshot.md` | `54acb3f5…9a56b8d` | `54acb3f529548491fb9097206267041433038c04b9e1870d3f67b98669a56b8d` | ✅ |
| P6-FIX-2 merge on `main` | `fa6c7f078ab988a5c07c992f53f4c77b34521f5f` | ancestor of HEAD ✅ | ✅ |

### Phase 6 merge SHA inventory

| Track | Merge SHA | `git merge-base --is-ancestor` vs HEAD | Subject |
|---|---|---|---|
| Plan (`p6-plan`) | `aee0f0da2ce0382c117013dc57f2cc32f1cd8370` | ✅ | Merge branch 'p6-plan' |
| T1 CALC | `5303e368969eaf60a68eb5950867ef302971119b` | ✅ | Merge branch 'p6-calc' |
| T2 STORE | `79a0e3e7504eea98083b2f66066428bc69a56570` | ✅ | Merge branch 'p6-store' |
| T3 TIME | `1c7357e1f9f7c3927fa6e70763d1582b60143979` | ✅ | Merge branch 'p6-time' |
| T4 FORGET | `7b8f030b611372b5d2c35f0c460455916e781384` | ✅ | Merge branch 'p6-forget' |
| T5 EPISODES | `8e12ff0c8226db0cd0ec95a881eabad166f7c00b` | ✅ | Merge branch 'p6-episodes' |
| FIX-WHEN | `a2900eefae3b45222510962d5eb640e7641a0727` | ✅ | Merge branch 'p6-fix-when' |
| FIX-2 | `fa6c7f078ab988a5c07c992f53f4c77b34521f5f` | ✅ | Merge branch 'p6-fix-2' |

Progress-doc cross-check: all eight SHAs match the closeout records in `P6-*_Progress.md`.

### Lore file structure (where Phase 6 goes)

**`DESIGN_DECISIONS.md`** (~861 lines) — thematic early sections (Client / Scope / Provider / Security / Confirmed-action), then phase sections ending at Phase 5. Phase 6 entries go as a new top-level section after Phase 5:

- `## Phase 6 — Memory She Lives With` (build-plan title; house style matches Phase 5)
- P6-D01–D08 + track decisions / annotations / known limits / process lessons
- Optional `### Phase 6 execution notes`
- Annotations that touch earlier IDs (`P4`, `C4`, `S14`, `C8`/`P5-D10`, `P5-D06`, `P4-D07`/`P4-D27`) are inline on those existing bullets (Phase 5 pattern) and/or restated under the Phase 6 section per the build plan.

**`OPEN_QUESTIONS.md`** (~235 lines) — single section `## Research needed…` with `S##` bullets; footer paragraph. Phase 6: update/resolve S43, S42, S35 arithmetic; annotate S28; add new OQs; update footer. **Placement note:** `S14` currently lives only under `DESIGN_DECISIONS.md` → Scope/deferral (not a standalone OQ bullet). Build plan / prompt ask to annotate S14 in OQ — Phase 2/3 will propose either a new OQ bullet or annotate the DESIGN_DECISIONS S14 entry (classification at Phase 2 STOP).

**`ROADMAP.md`** (~169 lines) — `## Phase N complete` blocks, then `## Current stage — Phase 6 — Memory (not started)`. Phase 6: replace current stage with `## Phase 6 — COMPLETE: Memory Foundation` (prompt title) + Phase 7 stub; keep `## Source documents`.

**`identity/SOUL.md`** / **`MEMORY_CONVENTIONS.md`** — read in full at Phase 1; Phase 5 of this prompt is read-only hash verify vs live (no edit unless Brian-approved mismatch).

**`Phase_SOP_Generic.md`** — not found under `zola-windows` or `zola-spikes` at Phase 1; house style taken from existing Phase 5 lore section + `P5-LORE_Progress.md`.

### Phase 1 STOP

Branch `p6-lore` created; progress doc written; inputs verified; merge inventory complete; lore placement mapped.

## Phase 2 — Draft DESIGN_DECISIONS (not applied) — revised after Brian+Claude review

> Lore files are **not** edited until Phase 7 (after Phases 3–6 and Brian approval). Draft only.

### 1. G-DECISION-ID classification

| Item | Classification | One-line reason |
|---|---|---|
| P6-D01…D08 (Appendix A) | keep IDs | Locked before the plan; durable architecture |
| G-AUTHORITY + G-LABELS | **new ID → P6-D09** | Durable forget-authority and label rules future phases must obey |
| `forget_guard` / `pre_tool_call` ("I agree. Yes.") | **note under P6-D09** | Code enforcement of clarify-across-paths; mechanism extending D09 |
| G-ERASE + deferred sanitize | **new ID → P6-D10** | Durable physical-erasure / privacy rule |
| G-BRIAN-ONLY (tui/no-parent; tool hidden/refused for cron) | **note under P6-D04** and **P6-D09** | Same allow-list for pending/episodes and for forget_memory surface |
| Backups: "delete old ones and track passes." | **new ID → P6-D11** (Brian) | Forget cannot reach backups; delete after each track merge |
| Skills `conversation-memory` / `everyday-assistance`: "Keep" | **note** (Phase 6 section) | Brian keep-call; no new architectural ID |
| P6-FIX-WHEN | **note under P6-D05** | SOUL reinforcement of ambient-time recall |
| P6-FIX-2 (last weekend + episodes cue) | **note under P6-D04** / **P6-D05** | Phrase table + prefetch cue; R6 PASS (seeded) |
| Blind C2 first-fail / 7-FIX rerun | **note under P6-D04** | Measured outcome, not a new rule |
| Associative 0/4, voice echo, don't-note, notebook clarification | **known limits / Phase 3 OQs** | Not new decision IDs |
| Process lessons (restart all Hermes; session registry; Unix floats; merge-only-on-PASS) | **process lesson** | Execution hygiene, not product decisions |

### 2. Build-plan annotations on existing bullets (apply with Phase 7)

**P4** — append: `Phase 6: **revised by P6-D07** (local only; the model-processing boundary stated).`

**C4** — append: `Phase 6: **extended.** Files remain the fact authority; the structured store sits beside them (P6-D01).`

**S14** — append: `Phase 6: **foundation complete, not resolved.** Built: the local store, the fact index, episodes, lexical/entity retrieval, time and forget. Still open: long-term retrieval quality (associative-recall table from Track 5); the evidence-based fact-authority migration (P6-D01).`

**C8** / **P5-D10** — append: `Phase 6: forget now cascades through the provider; \`state.db\` is still not redacted (P6-D06).`

**P5-D06** — append: `Phase 6: stands, restated in P6-D02 rule 8.`

**P4-D07** / **P4-D27** — append: `Phase 6: stand (P6-D08).`

### 3–6. New section — insert after Phase 5 execution notes

```markdown
## Phase 6 — Memory She Lives With
Recorded from `PHASE6_BUILD_PLAN.md` v1.1 (`P6-D01`–`P6-D08`, Appendix A),
the P6PRE audit (merge `92dc707ac047d2808b9f1848bb0e31f96689065a`), the
working decisions snapshot (`PHASE6_DECISIONS_snapshot.md`), and the
progress docs `P6-CALC` through `P6-FIX-2`. Full locked wording stays in
Appendix A / the snapshot; this section is the lore pointer, track
amendments, and measured limits.

- **P6-D01 — Two kinds of memory, one authority each.** **As locked.**
  `USER.md`/`MEMORY.md` stay the authority for current durable facts
  (memory tool only). A Zola-owned local store holds (a) a structured fact
  index rebuildable from the files and (b) episodes (store is sole
  authority). Episodes may reference facts; they never create or change
  them. Phase 6 retrieval surfaces episodes and temporal context, not a
  second copy of current facts. Fact-authority migration is a future
  evidence-based decision. **Brian's verdict:** "I agree"

- **P6-D02 — Memory invariants.** **As locked** (eight rules: one author
  each for facts and episodes; episodes never mutate facts; entities
  organize only; timestamps record only what's known; correction preserves
  history / forget erases; retrieval never becomes persistence; raw
  conversation is evidence). Rule 8 keeps `P5-D06` (search past
  conversations only when asked). **Brian's verdict:** "With that
  correction to Rule 8, I would record P6-D02. I wouldn't change Rule 6
  yet; your note captures exactly what the later forget decision needs to
  solve."

- **P6-D03 — A Zola-owned local memory provider (amended by P6-D06).**
  **As locked, then amended.** Own provider (not Holographic); profile
  plugin `zola_memory`; repo source `hermes-plugins/zola_memory/`; local
  SQLite + FTS; no new installs. Model-facing tools: none, **amended** to
  one erase-only forget operation. Must not depend on unreliable Windows
  `on_session_end`. **Brian's verdict:** "yes." Amendment with D06:
  "lock with amendment".

- **P6-D04 — Episodes are written by a background summarizer inside the
  provider.** **As locked.** Host-owned plugin LLM; pending-turn queue;
  consolidate on quiet gap / startup / pre-compress / session end if it
  fires; never reads `state.db`; commit only if pending unchanged;
  bounded retry. `event_time` only when stated or from an authoritative
  system source. **Brian's verdict:** "lock"
  **G-BRIAN-ONLY note:** only `tui` + empty-parent turns become pending /
  episodes (same allow-list as ambient time).
  **Blind test:** first S1 run **failed** (Miata split into two episodes;
  "yesterday" lost to the Unix-float timestamp bug); **C2** (rerun after
  7-FIX: normalize Hermes unix floats; significance/`plan` rule)
  **passed** — Miata+belt one episode, `event_time=2026-10-04` /
  `stated` / `yesterday`; Brian summaries "good". Prefetch p95 ~1.7 ms.
  **P6-FIX-2 note:** phrase table adds "last weekend" → Sat–Sun interval
  (`YYYY-MM-DD/YYYY-MM-DD`, displayed "the weekend of Oct 3–4"; Ashford
  ✅). Merge `fa6c7f078ab988a5c07c992f53f4c77b34521f5f`.

- **P6-D05 — Ambient, system-stamped time.** **As locked.** Per-message
  local stamp via `pre_llm_call`; cross-session gap via content-free
  `last_interaction_at`; relative ages at read time; never invent unknown
  event times; never read stamps aloud. `MeaningfulGapMinutes = 30`
  tunable. Smoke: stamps on trivial turns; gap awareness; no spoken
  readout. **Brian's verdict:** "Yes. I would put both into the build
  plan, and I think the `last_interaction_at` marker is the correct
  solution."
  **P6-FIX-WHEN note:** SOUL line — when recalling a past conversation,
  mention roughly when (merge `a2900eefae3b45222510962d5eb640e7641a0727`,
  landed before a spoken-when PASS — recorded error). **P6-FIX-2 note:**
  episodes-block cue asks her to mention roughly when if she uses an
  episode. **R6 PASS** ("We settled that yesterday.") used a
  Brian-approved one-day backdate of the kiln episode's
  `source_user_time`/`recorded_at` (deviation, not a natural cross-day
  result). Same-day recall may still omit "when".

- **P6-D06 — Forget erases every copy the memory system controls.**
  **As locked with amendment.** Recognition fails closed; cascade deletes
  every provider-controlled copy (index, history, FTS, links, pending,
  whole episodes); content-free tombstones only; `state.db` not redacted
  (`P5-D10` stands); confirmation mentions chat history remains. Episode
  memory: one erase-only `forget_memory` tool (amends D03). Proven across
  Track 4 (mechanism) and Track 5 (live episode forget + paraphrase via
  fact-ref cascade).   **Brian's verdict:** "lock with amendment"

- **P6-D07 — P4 revised: memory local; no third-party memory service.**
  **As locked.** Persistent memory stays on-machine; no Honcho/Hindsight/
  mem0/etc. Episode consolidation may resend pending turns through the
  host-owned model path (same trust boundary as conversation) — model
  processing, not off-device memory. At-rest encryption stays deferred
  (H4). **Brian's verdict:** "lock"

- **P6-D08 — Math without code; approvals unchanged.** **As locked.**
  Bounded `calculate` tool in `zola_tools` (no eval/shell/side effects;
  fails closed); outside the approval gate by contract. `approvals.mode:
  manual`, `P4-D07` and `P4-D27` stand. Resolves the arithmetic case of
  `S35` only. Live: three arithmetic prompts, zero cards; control still
  cards. **Brian's verdict:** "lock"

- **P6-D09 — Forget authority (G-AUTHORITY + G-LABELS).** **Adopted Track
  4.** **Brian's verdicts (verbatim, `P6-FORGET_Progress.md` Phase 3
  approval):** "1 G-AUTHORITY adopt. 2 G-LABELS adopt, F6
  transcript/state.db persistence of args + labels accepted knowingly."
  **G-AUTHORITY:** `confirm=true` runs only when (forget intent or an
  active clarification hold) **and** every `target_id` is in the transient
  candidate set from the latest authorized `confirm=false` for this
  provider instance (plus `is_brian_conversation()`).
  **G-LABELS:** `confirm=false` labels are minimal disambiguators only;
  never persisted by the provider (not logged, tombstoned, or written to
  `meta`); never echoed after `confirm=true` (IDs/kinds/counts only). F6
  transcript/`state.db` persistence of tool args and candidate labels is
  accepted knowingly.
  **G-BRIAN-ONLY note:** `forget_memory` schema omitted after init and
  execution refused (`refused_reason=platform`) for cron/non-Brian agents
  (not `tui` + empty parent).
  **Extension (Track 5):** after `ask_brian=true` she bypassed asking via
  memory-tool `remove` (Larkspur episode lost). Brian adopted a
  `pre_tool_call` guard blocking memory-tool remove/replace while an
  `ask_brian` hold is unresolved. **Brian (verbatim):** "I agree. Yes."
  ⚠️ Guard **not fired live** in later smoke (she asked); unit-tested.

- **P6-D10 — Physical erasure (G-ERASE).** **Adopted in Track 5
  (Brian).** After every cascade, consolidation commit, and zero-match
  forget: `secure_delete=ON`, FTS5 secure-delete, and
  `wal_checkpoint(TRUNCATE)` (commit before checkpoint). Approved
  deferred-sanitize safety net when checkpoint is busy. ⚠️ Live
  `action=defer` count **0** in smoke (never busy); unit defer→success
  covered.

- **P6-D11 — Phase-track backups are deleted after merge.** **Brian
  (closeout, verbatim):** "delete old ones and track passes." Forget
  cannot reach backups, so backups are deleted at each track's closeout
  after merge. Phase 6 backups are deleted at this lore closeout (Phase 6
  STOP delete list).

### Known limits
- **AUD-24:** `session_search` "when" strings omit timezone (Hermes-side;
  no pin edit).
- **Wordless paraphrase → episode:** caught only via `episode_fact_refs`
  (D2' erased after notebook remove; accepted caveat).
- **Notebook-fact clarification:** model judgment (Mara asked; two Rosas
  in one sentence did not); enforced ask exists for episode memory /
  after forget lookup flags `ask_brian`.
- **Same-day recall** may omit spoken "when" even when prefetch supplies
  it (FIX-WHEN / FIX-2 cue; R6 PASS was seeded cross-day).
- **Associative/paraphrased episode retrieval:** 0/4 under fixed blind
  queries (shared words Q2=0, Q3=1, Q4=0, Q5=0) — retrieval-quality limit;
  OQ in Phase 3. Direct lexical recall passed.
- **forget_guard / deferred-sanitize:** not observed live (unit-proven).

### Background-review skills (closeout)
Brian (verbatim): "Keep" — `communication/conversation-memory` and
`communication/everyday-assistance` (procedural; 0 personal facts).
Whether autonomous skill edits need a policy → OQ (Phase 3).

### Phase 6 execution notes
- Deploys must verify **every** Hermes process restarted (stale serve kept
  old modules).
- Module-level provider state is unsafe — one provider per agent; resolve
  via the session registry (identity-checked put/rekey/remove).
- Hermes message timestamps are Unix floats (normalize at write).
- Prompts must say **"merge only on PASS"** (FIX-WHEN merged before spoken
  when PASS — recorded).
```

### Phase 2 STOP (accepted)

Accepted Brian+Claude (2026-10-05). D04 wording: first **S1** failed; **C2** passed after 7-FIX. Backup policy → **P6-D11**. No lore files modified yet.

## Phase 3 — Draft OPEN_QUESTIONS (not applied)

> Lore files are **not** edited until Phase 7. Draft only.

### G-RESOLVED checks

| ID | Original scope (summary) | Proposed status | Why (G-RESOLVED) |
|---|---|---|---|
| **S43** | She knows wall-clock time but not when each message/session was, so near/far look alike (BR1 had no timing). | **RESOLVED** → remove; record under DESIGN_DECISIONS / P6-D05 | P6-TIME shipped per-message stamps, cross-session gap via `last_interaction_at`, SOUL never-read-aloud; smoke: stamps incl. trivial turns, gap awareness, 6 voice turns with no stamp readout (over-mention qualitative PASS). Original question answered. |
| **S42** | Hermes session ≠ Zola memory boundary; durable facts/decisions/episodes shared by relevance; no automatic cross-transcript reads. Facts half-done in P5; **open remainder was episodes**. | **RESOLVED** → remove | Episodes remainder shipped by P6-EPISODES (pending→consolidate→prefetch across sessions). `P5-D06` / P6-D02 rule 8 still bars automatic transcript promotion. Nothing in original S42 scope remains open. Associative-recall quality is a **new** OQ, not S42. |
| **S35** | Approval scopes beyond "once"; revisit `approvals.mode` (session/always; whether `manual` stays). P5 noted arithmetic cards. | **Partial:** arithmetic case **RESOLVED** by P6-CALC/P6-D08; **session/always scopes stay open** | Only the arithmetic card path is closed (bounded `calculate`, zero cards on three prompts). Broader scopes unchanged — keep S35 with annotation. |
| **S14** | Structured store with tiers/confidence projecting into MEMORY.md (long-term). Lives in DESIGN_DECISIONS today, not OQ. | **Annotate (stays open):** foundation complete, not resolved | Built: local store, fact index, episodes, lexical/entity retrieval, time, forget. Open: retrieval quality; evidence-based fact-authority migration; measurement plan (fill %, prefetch relevance, prompt cost). Add an OQ bullet so the open remainder is visible here. |
| **S28** | Session UI retirement when memory makes sessions unnecessary. | **Annotate (stays open)** | Episodes now exist; SESSION HUD / Sessions dock retirement can be evaluated. Not resolved — no retirement decision. |

### Proposed new OQ IDs (next free after S44)

| ID | Topic | Evidence |
|---|---|---|
| **S45** | Voice echo → "User correction during the turn" | T4/T5: TTS picked up by mic; Hermes active-turn redirect. Brian: "Record it as an open question. We have to get this tightened." **High priority.** |
| **S46** | Semantic/associative episode retrieval | Direct lexical recall passed; associative top-3 **0/4** (shared words Q2=0, Q3=1, Q4=0, Q5=0). Retrieval-quality limit, not persistence failure. No embeddings in Phase 6. |
| **S47** | Notebook-fact clarification is model judgment | Mara (separate msgs) asked; two Rosas in one sentence erased both. Guard enforces ask only after forget lookup flags `ask_brian`. |
| **S48** | Consolidator “no need to save a note” as don’t-remember | Observed (S1' + Fernhill), not designed. Decide if that is intended consent behavior. |
| **S49** | Background-review skill edits — policy? | Both skills **Keep** (Brian); pattern: review edits skills autonomously. Need a policy? |
| **S50** | Phase 6 tunables after live use | Starting values shipped: `MEANINGFUL_GAP_MINUTES=30`, `CONSOLIDATE_QUIET_MINUTES=10`, `EPISODE_MIN_SCORE=0.15` (calibrated). Retune only with measured miss/over-mention data. |

### Drafted text changes

#### Remove (move to DESIGN_DECISIONS via Phase 2/7)

Delete the **S42** and **S43** bullets from `OPEN_QUESTIONS.md`.

#### Replace **S35** with:

```markdown
- **S35 — Approval scopes beyond "once"; revisit `approvals.mode`.**
  Phase 4 forces `manual` (`P4-D27`) because Hermes's default `smart` can
  auto-approve. Session/always scopes and whether `manual` remains required
  need their own decision.
  Observation (P5-WAKE smoke B3): a plain arithmetic question produced
  one approval card per math problem (developer: "she showed a card for
  each math problem for approval.").
  **Phase 6:** arithmetic case **RESOLVED** by `P6-CALC` / `P6-D08` —
  bounded `calculate` tool; three arithmetic prompts, zero cards; control
  still cards; `P4-D07`/`P4-D27` stand. **Session/always scopes stay open.**
```

#### Replace **S28** with (annotate):

```markdown
- **S28 — Session UI retirement.** The developer expects his memory system
  to make sessions unnecessary. When it does, remove the SESSION HUD line
  and the Sessions dock button together.
  **Phase 6:** episodes now exist (P6-EPISODES) with cross-session
  prefetch. Session UI retirement can be evaluated; no retirement decision
  yet.
```

#### Add **S14** (open remainder; was only in DESIGN_DECISIONS):

```markdown
- **S14 — Structured memory store (foundation complete, not resolved).**
  Phase 6 built a local Zola store beside the flat files: structured fact
  index (files remain fact authority), episodes with consolidation and
  lexical/entity retrieval, ambient time, and forget with physical erasure
  (`P6-D01`–`D11`). **Still open:** (1) long-term retrieval quality —
  associative/paraphrased episode recall was 0/4 under fixed blind queries
  (see `S46`); (2) evidence-based migration of fact authority to the store
  (relevance, prompt cost, memory quality — not fill %); (3) measurement
  plan — report fill %, prefetch relevance, and prompt cost before any
  migration call. Tiers/confidence/decay and environmental facts remain
  out of scope until that evidence exists.
```

#### Add new OQs (after S44):

```markdown
- **S45 — Voice echo injected as "User correction during the turn".**
  **High priority.** Zola's TTS was picked up by the mic and injected into
  Brian's turn via Hermes's active-turn redirect (`User correction during
  the turn: …`). This can put her words into his turns anywhere (forget
  disposition, pending text, consolidator input). Brian (verbatim):
  "Record it as an open question. We have to get this tightened."
  Related: `S36` (state-aware policy "her echo → ignore"; echo filter
  still only drops ≥3-word / ≥60% tail runs, A32). Observed path was
  Hermes active-turn redirect (mid-turn submit), not barge-in
  (`voice.barge_in` stays false, `P4-D28`). Next-phase candidate.

- **S46 — Semantic / associative episode retrieval.**
  Direct lexical episode recall passed in Track 5. Associative /
  paraphrased retrieval found **0/4** under the fixed blind queries
  (shared-word counts with stored summaries: Q2=0, Q3=1, Q4=0, Q5=0;
  prefetch miss on all four). This is a **retrieval-quality** limitation,
  not an episodic-memory persistence failure. Phase 6 intentionally did
  not add embeddings or vector retrieval. Next-phase question: "What is
  the minimum semantic retrieval mechanism that materially improves
  associative recall without creating another memory authority?"

- **S47 — Notebook-fact clarification is model judgment.**
  For notebook facts, whether she asks before erasing is SOUL-guided
  judgment, not code-enforced: with Mara (separate messages) she asked;
  with two Rosas in one sentence she erased both, then restored the aunt
  on correction (Brian accepted). The `forget_guard` / `ask_brian` path
  enforces clarification for episode memory and after a forget lookup
  flags `ask_brian`, not for ordinary notebook removes. Decide whether
  notebook clarification needs a stronger gate.

- **S48 — Consolidator honors "no need to save a note" as don't-remember.**
  Observed in Track 5 (S1' and Fernhill leak-test): an explicit "no need
  to save a note" / don’t-note request was treated as consent not to
  write an episode. Not designed as a product rule. Decide whether that
  is the intended consent behavior and document it if so.

- **S49 — Background-review skill edits — is a policy needed?**
  During Phase 6 smokes, background review created/patched procedural
  skills (`communication/conversation-memory`,
  `communication/everyday-assistance`; 0 personal facts). Brian
  (verbatim): "Keep". Pattern: background review edits skills
  autonomously. Decide whether that needs an explicit policy (what it may
  write, review cadence, or a hold).

- **S50 — Phase 6 memory tunables after real use.**
  Named starting values shipped and smoke-checked:
  `MEANINGFUL_GAP_MINUTES = 30`, `CONSOLIDATE_QUIET_MINUTES = 10`,
  `EPISODE_MIN_SCORE = 0.15` (calibrated on synthetic related vs
  single-common-word corpus). Retune only with measured over-mention,
  missed consolidations, or prefetch false-positives/negatives — not by
  feel.
```

#### Footer (replace italic close):

```markdown
*S13 and S16 remain open. S17, S21, S26 updated at Phase 4 lore closeout.
S20, S22, S32 resolved (see DESIGN_DECISIONS Phase 4). S33–S41 added at
Phase 4 lore closeout. S42 added at Phase 5 kickoff (2026-10-01). S41
resolved (see DESIGN_DECISIONS Phase 5). S42 and S43 resolved at Phase 6
lore closeout (episodes + ambient time). S35 arithmetic resolved by
P6-CALC; session/always scopes remain. S14 annotated (foundation
complete, not resolved). S28 annotated (episodes exist; retirement
evaluable). S45–S50 added at Phase 6 lore closeout. Not open questions
(one line): question quiet window withdrawn (B38); gap "no Stop" closed
by P4-D29; AUD-37 closed by P4-D18 (residual in S36); external dictation
tool is test hygiene (A20). Resolved items stay in DESIGN_DECISIONS.md.*
```

### Phase 3 STOP (accepted)

Accepted Brian+Claude (2026-10-05). S42/S43 RESOLVED per G-RESOLVED; S45 related-S36 note added. No lore files modified yet.

## Phase 4 — Draft ROADMAP (not applied)

> Lore files are **not** edited until Phase 7. Draft only.

### Placement

Replace `## Current stage — Phase 6 — Memory (not started)` … through the carry-candidates list with the two blocks below. Keep `## Source documents` unchanged.

### Drafted text

```markdown
## Phase 6 — COMPLETE: Memory Foundation
Phase 6 closed five tracks plus FIX-WHEN and FIX-2, then this lore pass.
"Complete" means the planned phase shipped — not that Zola's memory work
is done. Shipped: a local structured fact index (the flat files remain
the fact authority); episodic memory with consolidation and retrieval;
ambient temporal context; destructive forget with physical erasure; a
bounded calculator; and measured limitations (associative recall 0/4;
same-day "when" may still be omitted; notebook clarification is model
judgment). `S43` and `S42` resolved; `S14` foundation complete, not
resolved; `S35` arithmetic resolved (scopes remain).

1. ✅ **AUDIT** — P6PRE, merge `92dc707ac047d2808b9f1848bb0e31f96689065a`
   (audit commit `84f14d83db8efd7e495acbfa078a8da66b415683`).
2. ✅ **DECISIONS LOCKED** — `P6-D01`–`P6-D08` (Appendix A); decisions
   adopted during Phase 6: `P6-D09`–`P6-D11`.
3. ✅ **BUILD PLAN WRITTEN** — `PHASE6_BUILD_PLAN.md` v1.1, commit
   `187275981bdcbfcf3acd87a148bb0606a1c2d1e1`, merge
   `aee0f0da2ce0382c117013dc57f2cc32f1cd8370`.
4. ✅ **TRACKS EXECUTED** — five tracks + FIX-WHEN + FIX-2.
5. ✅ **VERIFICATION / SMOKE TEST** — per-track; recorded ⚠️: associative
   recall 0/4; forget_guard / deferred-sanitize not fired live;
   paraphrase-forget via fact-ref; R6 kiln PASS used an approved
   one-day seed (deviation).
6. ✅ **TRACK MERGED**
   - Plan: `aee0f0da2ce0382c117013dc57f2cc32f1cd8370`
   - P6-CALC: `5303e368969eaf60a68eb5950867ef302971119b`
   - P6-STORE: `79a0e3e7504eea98083b2f66066428bc69a56570`
   - P6-TIME: `1c7357e1f9f7c3927fa6e70763d1582b60143979`
   - P6-FORGET: `7b8f030b611372b5d2c35f0c460455916e781384`
   - P6-EPISODES: `8e12ff0c8226db0cd0ec95a881eabad166f7c00b`
   - P6-FIX-WHEN: `a2900eefae3b45222510962d5eb640e7641a0727`
   - P6-FIX-2: `fa6c7f078ab988a5c07c992f53f4c77b34521f5f`
7. ✅ **LORE CLOSEOUT** — this pass.

One-line track results:
- **P6-CALC** — bounded `calculate`; arithmetic cards gone; approvals stand.
- **P6-STORE** — local SQLite fact index beside the files; import/sync.
- **P6-TIME** — per-message stamps + cross-session gap; never read aloud.
- **P6-FORGET** — cascade erase; `forget_memory`; G-AUTHORITY / G-LABELS.
- **P6-EPISODES** — pending→consolidate→prefetch; G-ERASE; blind C2 PASS.
- **P6-FIX-WHEN** — SOUL: mention roughly when on recall.
- **P6-FIX-2** — "last weekend" interval + episodes-block say-when cue;
  R6 PASS (seeded).

## Current stage — Phase 7 (scope is Brian's call)
Candidates (not a committed order):
- **`S45` voice echo** (Brian: high priority) — TTS → mic → "User
  correction during the turn"; related `S36` echo policy;
- **`S46` semantic / associative episode retrieval** — minimum mechanism
  that improves 0/4 associative recall without a second memory authority;
- **`S44`** — no clarify card in Voice mode;
- **`S40`** — UI polish after Phase 4;
- **`S28`** — session UI retirement (episodes now exist; evaluate);
- then carry: `S35` (session/always scopes), `S38`, `S36` (upstream-gated),
  `S33`, `S34`, `S37`, `S39`, `S17`, `S21`, `S26`, `S14` (migration /
  measurement), `S47`–`S50`, `S12`, `S13`, `S16`, `S24`, `S25`, `S31`.
```

### Phase 4 STOP (accepted)

Accepted Brian+Claude (2026-10-05). Wording: “decisions adopted during Phase 6: P6-D09–P6-D11”. Phase 7 remains a candidate list. No lore files modified yet.

## Phase 5 — Identity and deploy verification (read-only)

### SOUL.md (LF-normalized)

| Copy | Path | Raw SHA-256 | LF SHA-256 |
|---|---|---|---|
| Live | `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` | `e3d7bf9ac29b46237a2685bebae2e89e1a5952edb23e5afeee0ee8363009fb49` | `bb793a70497cd8ce4c09db9f8311b64425c9a12dbe3ce1cd527772fa42e4868b` |
| Identity | `zola-architecture/identity/SOUL.md` | `e3d7bf9a…3009fb49` (same) | `bb793a70…42e4868b` (same) |

**LF_MATCH ✅** (raw also identical; 7247 bytes).

### MEMORY_CONVENTIONS.md

| Copy | Result |
|---|---|
| Identity | `zola-architecture/identity/MEMORY_CONVENTIONS.md` — raw `44a8bf317803c96addc19d9b7d4a88681131ae012044d0bdba5bea97dedbbe37` (CRLF, 4328 B); LF `31bacf1eeffddffb99d49a48c2d9172c5cd4e6f4956dedf3462fc378495db2ca` (= P6-FORGET post-apply record) |
| Live profile | **No live file** — expected. P6-FORGET Phase 5: “Live profile has no separate MEMORY_CONVENTIONS.md apply path beyond the identity mirror… none today.” |

**Mirror status ✅** (identity is the mirror; nothing to reconcile on live).

### `plugins/zola_memory/` vs `hermes-plugins/zola_memory/`

| File | Live = Repo (raw) |
|---|---|
| `__init__.py` | ✅ `7faa42bc…` |
| `consolidate.py` | ✅ `1b2d8d8a…` |
| `fact_index.py` | ✅ `aa0cce9e…` |
| `forget.py` | ✅ `a9b62aa8…` |
| `llm_access.py` | ✅ `ec5a8f31…` |
| `log.py` | ✅ `a2515a96…` |
| `pending.py` | ✅ `9ff6156c…` |
| `provider.py` | ✅ `e2920937…` |
| `registry.py` | ✅ `86aa4da0…` |
| `retrieve.py` | ✅ `53d8044d…` |
| `store.py` | ✅ `c471ea12…` |
| `time_context.py` | ✅ `c3b61942…` |

**12/12 MATCH** (raw). tests/ excluded.

### `plugins/zola_tools/` vs `hermes-plugins/zola_tools/`

| File | Raw | LF-normalized |
|---|---|---|
| `__init__.py` | differ (repo CRLF) | ✅ `a1ef8541…` |
| `calculator.py` | differ (repo CRLF) | ✅ `0f29f3fc…` |
| `plugin.yaml` | differ (repo CRLF) | ✅ `f329e906…` |

**Content MATCH ✅** (LF-normalized). Raw mismatch is `core.autocrlf` CRLF in repo working tree vs LF on live — not a content drift. No fix required.

### Hermes pin

`345cd2b057a452236de401d3534b8502a7465e8d` — porcelain empty.

### Phase 5 STOP (accepted)

Accepted Brian+Claude (2026-10-05). Note: `zola_tools` repo-vs-live differ only by line endings (`core.autocrlf`); content identical (LF-normalized match).

## Phase 6 — Backup deletion inventory (delete nothing yet) — revised

Per **P6-D11** (Brian): "delete old ones and track passes." Forget cannot reach backups. System prompts embed `USER.md`/`MEMORY.md` → memory copies.

### Classification method (prompt dumps)

Markers grepped (counts only): `USER PROFILE`, `MEMORY (your personal notes)`, `[project]`, `[person]`, `[car]`, `[preference]`.

| Class | Rule | Count |
|---|---|---|
| **DELETE_PROMPT** | File is/has `system_prompt*.txt` **or** marker hits > 0 | **16** files (~528 KB) |
| **KEEP_TOOLS** | `tools*.json` / `provider_tools.json` only; marker hits = 0 | **28** files |
| **OTHER→KEEP** | capture scripts, baselines with 0 markers | scripts / baselines |

Every `system_prompt*.txt` hit both `USER PROFILE=1` and `MEMORY (your personal notes)=1` plus tag markers (counts 1–2 each).

### DELETE (final proposed — exact list)

**A. Whole directories (recursive)**

| Path under `zola-spikes\` | Contains (counts only) |
|---|---|
| `p6-calc/backup/` | SOUL + config + plugins listing |
| `p6-store/backup/` | config + `memories/USER.md`+`MEMORY.md` + listing |
| `p6-time/backup/` | plugin + SOUL + DB schema1 facts=14 tombs=5 |
| `p6-time/backup-fixb/` | plugin copy |
| `p6-forget/backup/` | plugin + SOUL 7b/7c + DB schema1 facts=14 tombs=5 |
| `p6-episodes/backup/` | plugin + DB schema1 facts=14 ep=0 tombs=16 |
| `p6-episodes/backup_7fix/` | plugin + DB schema2 facts=18 ep=3 tombs=16 |
| `p6-episodes/backup_7erase_fix/` | plugin + DB schema2 facts=18 ep=2 tombs=20 |
| `p6-episodes/backup_7d_fix/` | plugin + DB schema2 facts=15 ep=0 tombs=26 |
| `p6-episodes/backup_7wal/` | plugin + 2× DB schema2 facts=15 ep=0 tombs=28 |
| `p6-episodes/live_db_backup_e8/` | live DB snapshot (+wal/shm) |
| `p6-episodes/e8_scratch/` | measure.db scratch |
| `p6-episodes/phase6_scan/` | offline DBs schema2 facts=14 |
| `p6-episodes/phase7/` | **entire tree** (simpler rule) — offline DBs, diag FULL, state extracts, logs |
| `p6-fix-2/backup_20261005_124017/` | plugin + DB schema2 facts=16 ep=1 tombs=29 |
| `p6-fix-2/backup_r6seed_20261005_125855/` | DB schema2 facts=17 ep=2 tombs=29 |

**B. Offline DB files** (+ matching `-wal`/`-shm` beside them)

| Path |
|---|
| `p6-episodes/e10_scratch.db` |
| `p6-episodes/part_d_scan.db` |
| `p6-episodes/part_d2_scan.db` |
| `p6-episodes/part_e_scan.db` |
| `p6-fix-when/zola_memory_r4_scan.db` |

**C. System-prompt dumps (memory copies) — DELETE_PROMPT**

| Path | Markers (counts) |
|---|---|
| `p6-episodes/g6-phase6-after/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=2; [car]=1 |
| `p6-fix-when/g6-before/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=2; [car]=1 |
| `p6-fix-when/g6-after/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=2; [car]=1 |
| `p6-forget/g6-before/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-forget/g6-after/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-forget/g6-7b-before/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-forget/g6-7b-after/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-forget/g6-7b-7c-before/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-forget/g6-7b-7c-after/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-store/g6-before/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-store/g6-before/system_prompt_offline.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-store/g6-after/system_prompt.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-store/g6-after/system_prompt_offline.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-store/g6-after/system_prompt_offline_partc.txt` | USER PROFILE=1; MEMORY…=1; [person]=1; [project]=2; [car]=1 |
| `p6-time/g6-before/system_prompt_offline.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |
| `p6-time/g6-after/system_prompt_offline.txt` | USER PROFILE=1; MEMORY…=1; [project]=1; [car]=1 |

### KEEP (examined, excluded)

| Path / class | Why |
|---|---|
| `zola-spikes/prompts/**` + `PHASE6_DECISIONS_snapshot.md` | Canonical prompts + decisions snapshot |
| `zola-windows` repo incl. `audit/p6pre-phase6/*.md` | Source + P6PRE audit docs (no spike DB/prompt dumps found) |
| Live profile + live `zola_memory.db` + live plugins | Production — never delete |
| `hermes-agent` @ `345cd2b0…` | Pin |
| **KEEP_TOOLS** (28): all `tools*.json` / `provider_tools.json` under g6-* | Marker hits = 0; tool names only |
| Spike `*.py`, log-offset json/txt, suite baselines (`baseline_*.txt` markers=0), test output txt, `matcher_corpus.json` | Tooling / synthetic |
| `p6-fix-when/SOUL.md.after`, `SOUL.md.bak-*` | Identity SOUL text; `[car]`/`[project]` are convention examples only (no USER PROFILE / MEMORY headers) |
| `p5pre/`, `p5-memory/` | Prior-phase spikes — **out of Phase 6 P6-D11 scope** |

### P6PRE / other Phase 6 scratch (inventory)

| Location | Finding | Class |
|---|---|---|
| `zola-spikes/p6pre*` | **No directory** | n/a |
| `zola-architecture/audit/p6pre-phase6/` | Markdown audit only (9 `.md` files; no `.db` / prompt dumps / state extracts) | **KEEP** (repo) |
| Other `zola-spikes` Phase 6 dirs | Only the seven `p6-*` track folders listed above | classified in DELETE/KEEP |

### Side-by-side summary

| DELETE | KEEP |
|---|---|
| All `p6-*/backup*` (DB + plugin + memory-file snaps) | `prompts/**` + decisions snapshot |
| Offline/scratch DBs + `phase6_scan/` + `live_db_backup_*` | Live profile + DB + plugins |
| **`p6-episodes/phase7/` entire** | Repo + `audit/p6pre-phase6/*.md` |
| **16× `system_prompt*.txt`** (embedded USER/MEMORY) | **28× tools-only JSON** (0 memory markers) |
| | Spike scripts, baselines, SOUL.after/bak, p5* spikes |

### Phase 6 DELETE executed

**Approved:** Brian + Claude — revised DELETE list exactly as shown above.
**Deletion time:** `2026-10-05 13:25:18 -07:00` (directory mtimes on all seven `p6-*` track folders).
**Verify:** **47/47** listed paths **GONE** (`remain=0`). Re-verified after apply.

| Class | Count verified gone |
|---|---|
| A. Whole directories | 16 |
| B. Offline DB files (+ wal/shm beside them) | 5 DBs + 10 wal/shm = 15 |
| C. `system_prompt*.txt` | 16 |
| **Total path checks** | **47** |

**KEEP spot-check (still present):** live `zola_memory\zola_memory.db` + `memories\USER.md`/`MEMORY.md` + `plugins\zola_memory`; `prompts/PHASE6_DECISIONS_snapshot.md`; sample `provider_tools.json`; `p6-fix-when/SOUL.md.after`; repo `audit/p6pre-phase6/*.md`.

### p5* memory-copy scan (read-only — nothing deleted)

Same classification as Phase 6. Scanned `zola-spikes/p5*`: `p5pre`, `p5-memory`, `p5-lore`.

**Grep markers** (all text files): `USER PROFILE`, `MEMORY (your personal notes)`, `[project]`, `[person]`, `[car]`, `[preference]` → **0 hits** across all p5* files (no system-prompt dumps).

| Class | Count | Paths / notes |
|---|---|---|
| **DELETE-candidate** USER.md / MEMORY.md backups | **4** | `p5pre/USER.md`, `p5pre/MEMORY.md`, `p5-memory/backup/memories-pre-s1/USER.md`, `p5-memory/backup/memories-pre-s1/MEMORY.md` |
| **DELETE-candidate** system-prompt dumps | **0** | none |
| **DELETE-candidate** DB copies / state.db extracts | **0** | none |
| **KEEP** `p5-lore/` | **14** | apply/diff scripts + lore draft diffs (no memory files) |
| **KEEP** `p5-memory/` tooling | **10** | 7× `*.py`, `_soul_section.txt`, `backup/SOUL.md`, `backup/config.yaml` |
| **KEEP** `p5pre/` scripts | **3** | `l2_a2_query.py`, `l2_d1_compare.py`, `privacy_check.py` |

### Side-by-side (p5 — proposed)

| DELETE (4 USER/MEMORY only) | KEEP |
|---|---|
| 4× USER.md / MEMORY.md under `p5pre/` + `p5-memory/backup/memories-pre-s1/` | All `p5-lore/*` (14) |
| | `p5-memory` scripts + SOUL/config backups (10) |
| | `p5pre` audit scripts (3) |
| | Live profile / repo / hermes pin (unchanged) |

### p5 DELETE executed

**Approved:** Brian — the 4 USER/MEMORY copies only (keep everything else).
**Deletion time:** `2026-10-05 13:31:30 -07:00`
**Verify:** **4/4 GONE** (`remain=0`).

| Path under `zola-spikes\` | Status |
|---|---|
| `p5pre/USER.md` | GONE |
| `p5pre/MEMORY.md` | GONE |
| `p5-memory/backup/memories-pre-s1/USER.md` | GONE |
| `p5-memory/backup/memories-pre-s1/MEMORY.md` | GONE |

**KEEP spot-check (still present):** `p5-memory/backup/SOUL.md`, `p5-memory/backup/config.yaml`, `p5pre` scripts, `p5-lore/*`, `p5-memory` `*.py` / `_soul_section.txt`.

## Phase 7 — Apply approved drafts + exit checklist (STOP — no commit)

**Applied** (working tree only): `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`.
`git diff --stat`: `+302 / −44` across the three lore files (LF→CRLF warnings only).

Maps to accepted drafts: Phase 6 section P6-D01–D11 + annotations; S42/S43 bullets removed; S14/S28/S35/S45–S50 + footer; ROADMAP Phase 6 COMPLETE + Phase 7 candidates.

### Phase 6 Exit Checklist

| # | Item | Result |
|---|---|---|
| 1 | Track 1 `P6-CALC` merged; arithmetic zero cards; control cards; fail-closed | ✅ merge `5303e368…` |
| 2 | Track 2 `P6-STORE` merged; G1–G9; live hook; fact index/forget; no P5 regression | ✅ merge `79a0e3e7…` |
| 3 | Track 3 `P6-TIME` merged; stamps; gap; never spoken | ✅ merge `1c7357e1…` |
| 4 | Track 4 `P6-FORGET` merged; unit + live forget mechanism | ✅ merge `7b8f030b…` |
| 5 | Track 5 `P6-EPISODES` merged; blind/direct/forget/paraphrase/crash; prefetch p95; associative table | ✅ merge `8e12ff0c…`; ⚠️ associative 0/4 recorded; paraphrase via fact-ref caveat |
| 6 | No `hermes-agent` edits; clean at `345cd2b0…` | ✅ porcelain empty @ `345cd2b057a452236de401d3534b8502a7465e8d` |
| 7 | No installs; config only approved STOP changes | ✅ |
| 8 | Tunables are named constants; log prefixes named | ✅ |
| 9 | No memory content in logs/repo/tombstones/fixtures | ✅ (synthetic only); Phase 6 backups deleted under P6-D11 |
| 10 | Plugin unit tests pass | ✅ `zola_memory` 109 OK; `zola_tools` 44 OK |
| 11 | Smoke after each track boundary | ✅ (per-track progress) |
| 12 | `DESIGN_DECISIONS.md`: P6-D01–D08 + D09–D11 annotations | ✅ applied |
| 13 | `OPEN_QUESTIONS.md`: S43/S42 resolved; S35 arith; S14/S28 annotated | ✅ applied; + S45–S50 |
| 14 | `ROADMAP.md`: Phase 6 COMPLETE; Phase 7 stub | ✅ applied |

### Phase 7 STOP (accepted)

Phase 7 verified (Brian + Claude): lore files on disk — all approved content present, verdicts exact.

## Phase 8 — Commit and merge

Proceeding on **"proceed to commit and merge"** (commit message per prompt).
