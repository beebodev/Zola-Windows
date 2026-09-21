# WINH05 Audit 04 — Self-Model Awareness

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_SelfModel_Awareness_Architecture.md` (`SelfBeliefBlock`, hedging vs locked identity, read-only authority, no user-facing confidence display).

WINH04 DWA/memory-write findings (`WINH04-AUD-11`) are **not** restated as new IDs. They are contrast only: Hermes already writes fact-memory from the agent loop; this document asks whether a **self-model layer** exists and whether it would be read-only.

---

## 1. Introspective self-belief object

**Zola requires:** a `SelfBeliefBlock` value object — foundational identity (high confidence, never hedged) plus evolved behavioral patterns with confidence, plus flagged drift — assembled for prompt injection (`SMA` §5). It reads `ZolaIdentityProfile`; it does not define identity.

**Hermes searched:** `SelfBelief`, `self_model`, `EntityBeliefView`, `HedgingSignal`, `metaKnowing`, `hedging` as an SMA feature — **no matches** in agent identity/prompt code. Identity in the prompt is static SOUL.md / `DEFAULT_AGENT_IDENTITY` (`system_prompt.py` `_identity_parts` L488–494). No structured self-view, no confidence fields, no gap signals about the agent’s own knowledge.

Honcho `aiRepresentation` / `aiCard` (optional plugin README) is a **vendor user-modeling** artifact, not a Hermes `SelfBeliefBlock`, and is not default.

**Label:** `[GAP]` `WINH05-AUD-10` (HIGH). Self-description is static prompt text with no confidence modeling.

---

## 2. Confidence modeling and hedging

**Zola requires:** locked identity traits **never hedged**; adaptive/learned patterns **may** be hedged from computed belief confidence/age (`SMA` Core Philosophy; `HedgingSignalProducer`; `SelfBeliefBlock` relationship to Identity Framework).

**Hermes:** `DEFAULT_AGENT_IDENTITY` includes “when unsure, say so plainly” (`prompt_builder.py` L137) — a **style instruction**, which SMA explicitly says is not the same as computed uncertainty (“A prompt that says ‘be uncertain sometimes’ is not the same as a system that computes uncertainty from evidence”).

Holographic `trust_score` ranks fact retrieval (`retrieval.py` L69). It is not applied as a hedging register on identity or on how the agent speaks about itself.

Everything the agent says about itself from SOUL.md is presented with **uniform prompt certainty** (whatever the prose claims).

**Label:** `[GAP]` `WINH05-AUD-11` (MEDIUM).

---

## 3. Authority boundaries — read vs write

**Zola requires:** Self-Model Awareness **may** read broadly; **must not** write memory, modify beliefs/identity, or invoke speech/response execution; output only via prompt injection or initiative queue (`SMA` Authority Boundaries).

**Hermes has no self-model subsystem** (`WINH05-AUD-10`). The authority-boundary question still applies:

- There is **no** dedicated SMA process that could violate or satisfy the boundary.
- The closest introspective **behavior** is the same `AIAgent` loop that **does** write memory (`memory_tool`, `MemoryManager.notify_memory_tool_write` — WINH04) and **does** produce user-facing replies. If Zola later bolted SMA-like hedging onto that loop without a new layer, it would inherit write/execute authority — the opposite of the SMA split.
- Prompt assembly (`system_prompt.py`) is read-of-files + inject; it does not write MEMORY.md. That is ordinary prompt build, not an SMA layer.

**Label:** `[GAP]` `WINH05-AUD-12` (MEDIUM) — no SMA role exists, so the read-only / no-direct-execution boundary is **unimplemented**, not vacuously satisfied. Contrast with the Windows-track memory exception (agent may write facts): SMA’s write ban is a **different** principle and remains live (synthesis OQ3).

---

## 4. No user-facing confidence display

**Zola requires:** confidence values never shown to the user as numbers/scores/indicators (`SMA` Known Constraints; Non-Goals).

**Hermes:** no self-model confidence signal was found to display. Desktop/TUI do not surface a “certainty %” for identity beliefs. Token **usage** counters on `message.complete` (WINH03-AUD-03) are billing/usage, not belief confidence.

Holographic `trust_score` can appear in **tool JSON** returned to the model when that plugin is on; that is not a user-facing identity-confidence HUD. Default installs do not show it in the product chrome.

**Label:** `[MATCH]` `WINH05-AUD-13` (LOW) — the prohibition is not violated, because no SMA confidence UI exists. This is not evidence that hedging works; it only records that the forbidden display is absent.

---

## Finding summary (this document)

| ID | Label | Sev | Against |
|---|---|---|---|
| WINH05-AUD-10 | [GAP] | HIGH | `SelfBeliefBlock` / introspective object |
| WINH05-AUD-11 | [GAP] | MEDIUM | Computed hedging vs locked traits |
| WINH05-AUD-12 | [GAP] | MEDIUM | SMA read-only / no-execute boundary (no subsystem) |
| WINH05-AUD-13 | [MATCH] | LOW | No user-facing confidence numbers |
