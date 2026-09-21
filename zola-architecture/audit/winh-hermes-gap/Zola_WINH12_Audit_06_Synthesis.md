# WINH12 Phase 6 — Synthesis: Relational Intelligence & Model Provider Flexibility

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Document of Truth: Relational Intelligence Layer master + Temporal, Social Graph, Continuity, Calibration. SMA cited via `WINH05-AUD-10`–`13`. Half B: Master Plan Provider Abstraction + Tier 1 Conversational Models. Source: Audit_02–05.

Section 5 questions are not resolved here.

This phase is lopsided on purpose: Half A is almost entirely `[GAP]`; Half B is almost entirely `[MATCH]`. Neither side was softened.

---

## Section 1 — Finding Summary Table

| ID | Half | Label | Severity | File | One-line |
|---|---|---|---|---|---|
| WINH12-AUD-01 | A | GAP | HIGH | `system_prompt.py` L433–457, L656 | Timestamps/dates exist; no elapsed-time-to-meaning |
| WINH12-AUD-02 | A | GAP | HIGH | cite `WINH03-AUD-09`, `WINH05-AUD-15` | No relational `SessionBoundaryResolver` |
| WINH12-AUD-03 | A | GAP | HIGH | searched `agent/`/`tools/` | No `ThreadArcClassifier` or `TemporalRecencyFormatter` |
| WINH12-AUD-04 | A | RISK | MEDIUM | `hermes_time.py`; `turn_context.py` L515 | Clock split: prompt TZ vs `time.time` vs UTC datetime |
| WINH12-AUD-05 | A | GAP | HIGH | cite `WINH05-AUD-10`–`13` | Belief/correction/entity-view/arc contracts absent |
| WINH12-AUD-06 | A | GAP | HIGH | `memory_tool.py` L2; `learning_graph.py` L130–134 | No third-party person model; flat MEMORY.md/USER.md |
| WINH12-AUD-07 | A | GAP | HIGH | searched relationship-type / KNOWS_ABOUT | No structured relationship predicates |
| WINH12-AUD-08 | A | GAP | MEDIUM | `learning_graph.py` L130–134 | No salience / distinct-session recurrence ranking |
| WINH12-AUD-09 | A | GAP | HIGH | searched RelationshipArc / relationshipDepth | No relationship-arc document |
| WINH12-AUD-10 | A | GAP | HIGH | `system_prompt.py` L1–8, L656 | Prompt injects memory files + date, not an arc block |
| WINH12-AUD-11 | A | GAP | HIGH | cite `WINH05-AUD-03`/`08` | No depth-driven familiarity / warmth ceiling |
| WINH12-AUD-12 | A | GAP | HIGH | Phase 2 + `WINH05-AUD-10`–`12` | Calibration dependency chain unmet at every link |
| WINH12-AUD-13 | B | MATCH | MEDIUM | `providers.py`; `gemini_native_adapter.py` | Gemini/OpenAI/Anthropic native; not Gemini-locked |
| WINH12-AUD-14 | B | MATCH | MEDIUM | `lmstudio_reasoning.py`; `providers.py` L136–137 | Local OpenAI-compat can run the full tool loop |
| WINH12-AUD-15 | B | MATCH | MEDIUM | `model_switch.py` L15, L203–254 | Live `/model` switches provider+model mid-session |
| WINH12-AUD-16 | B | MATCH | MEDIUM | `transports/base.py`; `NormalizedResponse` | Wire formats convert into one internal representation |
| WINH12-AUD-17 | A | RISK | MEDIUM | cite `WINH07-AUD-01`/`02`; master L312–343 | RIL single delivery path vs Hermes multi-path speech |

**Counts:** 17 findings — **10 HIGH**, **7 MEDIUM**, **0 LOW**.

HIGH (all Half A GAP): AUD-01, 02, 03, 05, 06, 07, 09, 10, 11, 12.

MEDIUM: AUD-04 RISK, AUD-08 GAP, AUD-17 RISK, AUD-13–16 MATCH.

Half A: 13. Half B: 4 (all MATCH).

---

## Section 2 — What Hermes covers as-is

**Direct answers:**

1. **Relational Intelligence Layer:** there is **almost nothing to build on**. Shared infrastructure, data contracts, Social Graph, Continuity, and Calibration are scratch work. Hermes has conversation memory (files + `state.db` transcripts) and a calendar date in the system prompt. Those are not this layer. Do not treat MEMORY.md as a `RelationshipArc`.

2. **Model-provider flexibility:** Hermes gives Zola-Windows **genuine multi-vendor flexibility**, broader than the Master Plan’s four names and **not** coupled to Gemini the way the Tier 1 “Current: Gemini” line describes zola-main’s starting point. Configure adapters; do not rebuild a vendor lock-in layer.

### Half A — Relational Intelligence

Hermes covers: technical sessions (`session_id`, resume — WINH03/WINH05); flat MEMORY.md/USER.md/SOUL.md injection; a date/timezone line (`hermes_time` + `_timestamp_line`); model-written notes that *may* mention people.

Hermes does not cover: elapsed-time-as-meaning; session-boundary-for-arcs; thread-arc classes; recency formatter; belief confidence / correction log / entity belief view / relationship arc; third-party graph; typed relationships; salience; earned familiarity modes; Calibration’s two-axis damper.

Non-goal check: Hermes is not a social surveillance system **because it does not model people**. That is absence, not compliance.

### Half B — Conversational models

Named targets all reachable natively: Gemini (native adapter + Vertex), OpenAI (chat + Responses/Codex), Anthropic (Messages transport), local (LM Studio overlay + Ollama/vLLM/llama.cpp as OpenAI-compat `custom`/`local`). Live `/model` switches provider and model without restart. Transports normalize to `NormalizedResponse`; internal history is OpenAI-shaped by design. Default model string is empty — not Gemini.

---

## Section 3 — What needs a Zola-built adapter layer

Half B is mostly **configure, don’t wrap**. Remaining wraps:

| Finding | Wrap rather than replace |
|---|---|
| AUD-04 RISK | If RIL is built, introduce a single UTC epoch clock and route Temporal math through it; leave `hermes_time` for prompt dates. |
| AUD-15 MATCH + `WINH06-AUD-25` | Product policy: `/model` does not retune toolsets; Zola-Windows may pin toolsets independently of vendor. |
| AUD-16 MATCH | Keep Hermes transports; do not add a Gemini-shaped internal schema. New vendors should register a transport. |
| AUD-17 RISK | If RIL is in scope: constrain output to prompt injection (and a future initiative queue), and **disable or quarantine** `background_review` user-facing speech (`WINH07-AUD-02`) so RIL cannot grow a third path. |

No Half A `[PARTIAL]`/`[MATCH]`. Flat memory is not an adapter target for Social Graph or Continuity.

---

## Section 4 — What must be built from scratch

Dominated by Half A, as expected.

| Capability | Why scratch | ID |
|---|---|---|
| Elapsed-time-to-meaning + `TemporalRecencyFormatter` | Dates in the prompt are not relational deltas | AUD-01, AUD-03 |
| `SessionBoundaryResolver` | Technical `session_id` ≠ last-session-ended-at | AUD-02 |
| Shared contracts (belief confidence, correction history, entity belief view) | SMA also missing (`WINH05-AUD-10`–`12`) | AUD-05 |
| Social graph (nodes, typed edges, recurrence threshold, salience) | MEMORY.md is not a graph | AUD-06, AUD-07, AUD-08 |
| `RelationshipArc` + `[CONTINUITY]` injection | Files/transcripts are not an arc | AUD-09, AUD-10 |
| Relational Calibration (modes, damper, assumption license, repair register) | No depth signal; style is static config | AUD-11, AUD-12 |
| Clock Authority (if RIL ships) | Hygiene for Temporal; not a Zola product feature by itself | AUD-04 (RISK → engineering if Half A is in scope) |

**Not scratch:** Gemini/OpenAI/Anthropic/local adapters, live `/model`, transport normalization (AUD-13–16).

---

## Section 5 — Open questions for WINH00

Do not resolve these here.

1. **RIL scope / deferral.** Given near-total Half A gap: is the full five-subsystem Relational Intelligence Layer in scope for Zola-Windows’s initial build, or should some subsystems (Calibration in particular — most downstream, depends on Continuity + SMA + Temporal, all unmet) be deferred, as voice identity was flagged in `WINH09`? Temporal is foundational; Calibration cannot be honest without it.

2. **Providers: configure vs custom.** Hermes already covers the Master Plan’s conversational-model targets and more. Does Zola-Windows simply configure existing adapters, or is there a reason (cost, latency, a vendor not in `providers.py`) to build a custom one?

3. **Authority / single delivery path.** RIL requires prompt injection or initiative queue only. Hermes already speaks through extra paths (`WINH07-AUD-01`/`02`; `WINH12-AUD-17`). Is a single-path RIL realistic to enforce on this substrate, or does it conflict with what WINH07 already found?

4. **Calibration vs SMA.** Calibration depends on SMA confidence/correction signals (`WINH05-AUD-10`–`13`) that do not exist. Is Calibration blocked until those WINH05 gaps close, or can a first version use a standalone proxy (e.g. session count only) knowing that is **not** the architecture as specified?
