# WINH12 Audit 03 — Social Graph Reasoning

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_SocialGraph_Reasoning_Architecture.md` (full). Depends on Temporal (Phase 2) and SMA confidence pattern (`WINH05-AUD-10`–`13` — cite, do not re-derive). Fresh-start: Named Recurrence Threshold and `KNOWS_ABOUT` are capabilities, not Firestore paths.

`[PARTIAL]` is not “Hermes has MEMORY.md and people get mentioned there.”

---

## 1. Dynamic third-party person modeling

Zola: people who earn a social-graph node get a maintained model — relationship structure, conversational patterns, user-stated facts (`SocialEntityProfileBuilder`, L340–381). Passing names stay episodic until Named Recurrence Threshold (L150–174).

Hermes default memory is **flat prose**:

- `MEMORY.md` = agent notes, `USER.md` = user profile (`tools/memory_tool.py` L2; `learning_graph.py` L130–134 splits on `§`, not on person).
- No `DistinctSessionMentionTracker`, no per-entity session counts, no third-party profile object.
- Optional holographic / Honcho / Mem0 plugins (WINH04) are external memory providers, not a social-graph evaluator. They are not scored as this subsystem.

The model may write “Marcus works at the shop” into `MEMORY.md`. That is undifferentiated fact storage. There is no subsystem that builds or updates a person model over time.

Third-party confidence ceilings and SMA `EntityBeliefView` for those people: **blocked on** `WINH05-AUD-10`/`12` (no SMA / no belief view).

**Label:** `[GAP]` `WINH12-AUD-06` (HIGH) — no dynamic third-party person model; memory is flat notes.

---

## 2. Relationship structure vs flat facts

Zola v1 wants typed edges: kinship plus `EMPLOYEE_OF` / `WORKS_AT` (`RelationshipType`, L522–547), written only through `RelationshipWriteGovernor` / DWA.

Hermes: searched `agent/`, `tools/`, `hermes_cli/` for sibling/coworker/`relationship type`/`KNOWS_ABOUT` as data model: **no hits** (unrelated “sibling” uses are processes/profiles/UI). No enum of relationship predicates. A USER.md sentence “brother Tom” is free text.

**Label:** `[GAP]` `WINH12-AUD-07` (HIGH) — no structured relationship types; only free-text mentions.

---

## 3. Which people matter (salience)

Zola: Named Recurrence Threshold (3 distinct sessions / 90 days, or explicit introduction) plus frequency signals on the profile (L150–168, L358–361). Not every name becomes a node.

Hermes: every `§` chunk in MEMORY.md is equal for injection (`learning_graph.py` L130–134). No ranking of third parties. No mention-across-sessions counter.

**Label:** `[GAP]` `WINH12-AUD-08` (MEDIUM) — no salience / recurrence scoring for third parties.

---

## 4. Non-goal: not a social surveillance system

Master Non-Goals (L91–95) and Social Graph (L66–69, L87–96): do not profile without purpose or surface observations gratuitously.

Hermes has **no** general-purpose person tracker to over-surface. Default behavior is silent: people facts appear only if the model wrote them into memory and later reads that file. There is no `SocialGraphInitiativeSource` announcing “you’ve mentioned Marcus a lot.”

That is **not** a `[MATCH]` for Social Graph (the capability is missing). It is also **not** a `[RISK]` of surveillance-by-default. Per the phase prompt, skip a forced finding.

INFO only: if Zola-Windows later dumps every mentioned name into prompt context without a recurrence threshold, *that* would recreate the surveillance failure mode. Hermes does not do that today because it does not extract people at all.

---

## Finding table (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH12-AUD-06 | GAP | HIGH | `memory_tool.py` L2; `learning_graph.py` L130–134 | No third-party person model; flat MEMORY.md/USER.md |
| WINH12-AUD-07 | GAP | HIGH | searched relationship-type / KNOWS_ABOUT | No structured relationship predicates |
| WINH12-AUD-08 | GAP | MEDIUM | `learning_graph.py` L130–134 | No salience / distinct-session recurrence ranking |
