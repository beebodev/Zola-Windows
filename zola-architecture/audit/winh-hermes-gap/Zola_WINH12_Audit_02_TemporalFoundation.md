# WINH12 Audit 02 — Temporal Reasoning & Shared Infrastructure

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Temporal_Reasoning_Architecture.md` (full); Relational Intelligence master “Shared Infrastructure” and “Shared Data Contracts.” Fresh-start: capability, not Firestore/RTDB class names. Self-Model Awareness contracts that SMA owns (`EntityBeliefView`, hedging thresholds) are cited via `WINH05-AUD-10`–`13`, not re-derived.

`[PARTIAL]` requires a real analog. Raw timestamps in transcripts are **not** Temporal Reasoning.

---

## 1. Elapsed-time-to-meaning conversion

Zola: elapsed time is a first-class relational signal (“three weeks since you mentioned X”), not storage metadata (`Zola_Temporal_Reasoning_Architecture.md` L13–20, L35–55).

Hermes stores times and prints calendar dates. It does not convert deltas into relational meaning.

- Session transcripts in `state.db` carry timestamps (WINH03/WINH05 session machinery).
- System prompt volatile tier includes `_timestamp_line` (`agent/system_prompt.py` L433–457, injected L656): “Conversation started: *Weekday, Month DD, YYYY*” plus optional “Today’s date (as of the last context rebuild).” That is a **clock date for the model**, not “this topic has been quiet for 21 days.”
- `hermes_time.now()` (`hermes_time.py` L1–6, L38) is timezone-aware display time for that line.
- Searched `agent/`, `tools/`, `tui_gateway/` for `ThreadArc`, `TemporalRecency`, elapsed-time labels, “days since”: **no production hits** (test class `TestCodexSparkShortSessionBoundary` is unrelated).

**Label:** `[GAP]` `WINH12-AUD-01` (HIGH) — timestamps exist; no elapsed-time-to-meaning layer.

---

## 2. `SessionBoundaryResolver`

Zola: one function answers “when did the previous session end?” for relational-arc math (`SessionBoundaryResolver.resolveLastBoundaryMs`), with `SessionSummary.endedAtMs` then `ConversationState.updatedAt`, null = suppress gap-dependent output (master L192–207; Temporal L159–231).

Hermes `session_id` is a **technical** conversation handle:

- Cite `WINH03-AUD-09`: live runtime vs durable transcript resume — process identity, not relational boundary.
- Cite `WINH05-AUD-15`: `hermes_state_ids.py` `new_session_id` / gateway uuid — minting, not “last session ended at T.”
- Cite `WINH05-AUD-18`: transcript rows stamped with `session_id`; `MEMORY.md` writes are not.

No resolver, no `endedAtMs` fallback chain, no “elapsed time unknown → suppress” contract. `/new` starts a new technical session; the gap to the previous one is not computed as a relational signal.

**Label:** `[GAP]` `WINH12-AUD-02` (HIGH) — no relational session-boundary resolver. Technical `session_id` (WINH03/WINH05) is a different question.

---

## 3. `ThreadArcClassifier` / `TemporalRecencyFormatter`

Zola: classify open loops FRESH / ACTIVE / AGING / QUIET / OVERDUE / DORMANT (Temporal L241–303). All natural-language elapsed-time labels go through `TemporalRecencyFormatter` (master L218–223).

Hermes:

- No open-loop store of the Temporal `OpenLoopTracker` kind (WINH04 memory is `MEMORY.md` strings + optional plugins; not re-audited).
- No arc enum, no ranked `ClassifiedThread` list.
- `_timestamp_line` formats **calendar dates**, not “about three weeks ago.”

**Label:** `[GAP]` `WINH12-AUD-03` (HIGH) — neither classifier nor recency formatter exists.

---

## 4. Clock Authority

Zola: all five subsystems use a single UTC epoch-ms clock (`System.currentTimeMillis()`); Temporal L143–155. The Temporal doc itself flags ~150 independent timestamp sites as future hygiene (L514–522).

Hermes:

- Prompt dates: `hermes_time.now()` / `get_timezone()` (`hermes_time.py`; `system_prompt.py` L437–438) — IANA zone from `HERMES_TIMEZONE` or `config.yaml`, else server-local. **Not** UTC epoch-ms, and **not** used by the turn loop’s duration math.
- Turn/tool timing: `time.time()` (`turn_context.py` L515, `tool_executor.py` L286, many others).
- Vault / evidence / usage: `datetime.now(timezone.utc)` (`vault_store.py` L348, `verification_evidence.py` L106).

There is no injectable `Clock` and no rule that relational (or any) elapsed-time math must use one source. A future RIL built on Hermes would inherit this split.

**Label:** `[RISK]` `WINH12-AUD-04` (MEDIUM) — `hermes_time` is a prompt-date helper, not Clock Authority; `time.time()` and `datetime.now(timezone.utc)` coexist.

---

## 5. Shared Data Contracts

| Contract | Zola | Hermes |
|---|---|---|
| Belief Confidence | `StructuredEntityMetadata.confidence`, authority hierarchy, SMA hedging thresholds | No typed confidence; SMA hedging is `WINH05-AUD-11` (style instruction, not computed) |
| Correction History | `MemoryCorrectionLog` via `HybridMemoryRepository.logCorrection` | No correction log; memory writes are `memory_tool` strings (WINH04) |
| Entity Belief View | per-entity aggregator, session-cached, dual-endpoint invalidation | No entity belief aggregator (`WINH05-AUD-10`/`12`) |
| Relationship Arc | Continuity-owned document, other subsystems read-only | No arc document (Phase 4) |

Informal stretch (“the model might remember a correction in MEMORY.md”) is **not** a contract shape.

**Label:** `[GAP]` `WINH12-AUD-05` (HIGH) — none of the four shared contract shapes exist, even informally as named or equivalent types.

---

## Finding table (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH12-AUD-01 | GAP | HIGH | `system_prompt.py` L433–457, L656; searched ThreadArc/recency | Timestamps/dates exist; no elapsed-time-to-meaning |
| WINH12-AUD-02 | GAP | HIGH | cite `WINH03-AUD-09`, `WINH05-AUD-15` | No relational `SessionBoundaryResolver` |
| WINH12-AUD-03 | GAP | HIGH | searched `agent/`/`tools/` | No `ThreadArcClassifier` or `TemporalRecencyFormatter` |
| WINH12-AUD-04 | RISK | MEDIUM | `hermes_time.py`; `turn_context.py` L515; `vault_store.py` L348 | Clock split: prompt TZ vs `time.time` vs UTC datetime |
| WINH12-AUD-05 | GAP | HIGH | searched contracts; cite `WINH05-AUD-10`–`13` | Belief/correction/entity-view/arc contracts absent |
