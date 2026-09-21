# WINH12 Audit 04 — Relational Continuity & Calibration

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Relational_Continuity_Architecture.md`, `Zola_Relational_Calibration_Architecture.md`. Cite `WINH05-AUD-03`/`08` (style is config/presets, no learned style-profile store) — this phase asks only about **relationship-depth-driven** variation. SMA: `WINH05-AUD-10`–`13`. Temporal: Phase 2.

---

## 1. Relationship arc / shared history as a first-class construct

Zola: `RelationshipArc` at `users/{userId}/world/arcs/primary_bond` — depth, trajectory, friction, narrative summary, per-session deltas — owned by ConsolidationLoop step 6b (Continuity L168–268). Distinct from transcripts and from flat memory.

Hermes: searched `relationshipDepth`, `familiarity`, `earned`, `relational mode`, `RelationshipArc`: **no hits** in production Python. Continuity artifacts do not exist. Compaction (`context_compressor.py`) shrinks **transcript** context; it does not synthesize a relationship-arc document.

**Label:** `[GAP]` `WINH12-AUD-09` (HIGH) — no relationship-arc document or summary distinct from transcript / MEMORY.md.

---

## 2. “Lived relationship” vs starting fresh — prompt assembly

Zola: `ArcContextAssembler` injects `[CONTINUITY]` into `SessionBriefBuilder` (Continuity L435–460). History/trajectory/texture inform speech without narrating the relationship.

Hermes prompt assembly (`agent/system_prompt.py`, `agent/prompt_builder.py`):

- **stable:** identity, guidance, env (`system_prompt.py` L1–8, `load_soul_md` L492–493 / `prompt_builder.py` L1452).
- **context:** workspace, caller system message, context files.
- **volatile:** skills index, **MEMORY.md / USER.md**, external memory provider, `_timestamp_line` (L656).

Continuity is “re-read the memory files and the current transcript.” That is the flatter mechanism Continuity’s Non-Goals distinguish from an arc (Continuity L104–107). Compaction notes tell the model MEMORY.md stays authoritative (`context_compressor.py` L212, L4457) — still fact files, not arc state.

**Label:** `[GAP]` `WINH12-AUD-10` (HIGH) — prompt injects SOUL/MEMORY/USER and a date line, not a relationship-arc block.

---

## 3. Earned familiarity / calibrated warmth

Zola Calibration: four modes (EARLY→DEEP) from `relationshipDepth`, damper from friction + inter-session gap, behavioral directives not state labels (Calibration L149–243, L107–124). Ceiling for StyleProfile, not a warmth dial.

Hermes persona/tone:

- Cite `WINH05-AUD-03`: style is config/presets; `trust_score` is retrieval, not phrasing.
- Cite `WINH05-AUD-08`: no style-profile store; USER.md is the only default place learned style could live.

This phase’s narrower question: does anything scale tone to **how long / how deep the relationship is**? No `RelationalCalibrationAdapter`, no EARLY default for a new profile vs DEEP for a long-running one. A brand-new `HERMES_HOME` and a two-year MEMORY.md get the same identity prompt shape; only the **content** of MEMORY.md differs, and that content is not a depth score or mode enum.

Assumption license / repair register by depth: absent (Calibration pillars 4–5).

**Label:** `[GAP]` `WINH12-AUD-11` (HIGH) — no relationship-depth-driven familiarity; persona is static config (`WINH05-AUD-03`/`08`).

---

## 4. Dependency correctness

Master dependency order (L153–181): Temporal → SMA → Social Graph / Continuity → Calibration last.

| Link | Hermes |
|---|---|
| Temporal (elapsed time, boundary, recency formatter) | Unmet (`WINH12-AUD-01`–`03`) |
| SMA (belief confidence, hedging, EntityBeliefView) | Unmet (`WINH05-AUD-10`–`12`) |
| Continuity (`RelationshipArc`) | Unmet (`WINH12-AUD-09`) |
| Weak proxy: “MEMORY.md file mtime ≈ relationship age” | Not implemented as a signal; would not be Calibration |

There is **no** partial chain. Raw memory age is not wired as a depth proxy. Calibration cannot run on Hermes as specified.

**Label:** `[GAP]` `WINH12-AUD-12` (HIGH) — every Calibration dependency link is unmet; no usable proxy chain.

---

## Authority-boundary compatibility (structural, not a missing class)

Master “The Layer Must Not” / Delivery Paths (L312–343): RIL output reaches the user only via prompt injection or `InitiativeQueue`. No third path. No direct speech execution.

Hermes already has **multiple user-facing speak paths** (`WINH07-AUD-01`: `message.complete` plus review.summary, notices, heartbeat, child completes; `WINH07-AUD-02`: `background_review` prints to the user). There is no Hermes `InitiativeQueueEvaluator`. A Zola RIL that assumed “one injection path + one queue” would have to **constrain Hermes**, not inherit a single path.

**Label:** `[RISK]` `WINH12-AUD-17` (MEDIUM) — RIL single-delivery-path rule conflicts with Hermes’s existing multi-path speech (`WINH07-AUD-01`/`02`). Numbered 17 so Half B can occupy 13–16 without colliding.

---

## Finding table (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH12-AUD-09 | GAP | HIGH | searched RelationshipArc / relationshipDepth | No relationship-arc document |
| WINH12-AUD-10 | GAP | HIGH | `system_prompt.py` L1–8, L492–493, L656 | Prompt injects memory files + date, not an arc block |
| WINH12-AUD-11 | GAP | HIGH | cite `WINH05-AUD-03`/`08` | No depth-driven familiarity / warmth ceiling |
| WINH12-AUD-12 | GAP | HIGH | Phase 2 + `WINH05-AUD-10`–`12` | Calibration dependency chain unmet at every link |
| WINH12-AUD-17 | RISK | MEDIUM | cite `WINH07-AUD-01`/`02`; master L312–343 | RIL single delivery path vs Hermes multi-path speech |
