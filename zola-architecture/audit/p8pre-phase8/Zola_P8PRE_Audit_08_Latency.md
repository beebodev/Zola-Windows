# Zola P8PRE Audit 08 — Latency and Tool Shape (`S54`)

**Date:** 2026-10-07  
**Labels vs:** `S54`, `P7-D10`, `S16`

---

## 1. Cost of one plugin tool round

Source: `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` + `P7-LATENCY_Progress.md`. Client lines expose `tools=N` counts, not tool names; P7 progress joins `calculate` turns.

| Sample | tools | submit→first_audio_ms |
|--------|------:|----------------------:|
| 2026-10-06 turn (P7 calc remeasure) | 1 | 10875 |
| 2026-10-06 14:05 | 1 | 17808 |
| 2026-10-06 14:00 | 1 | 10529 |
| No-tool medians (P7) | 0 | ~5394 |
| Tool-group median (P7) | ≥1 | ~17808 |
| Δ (S54 class) | | **~8–12 s** (P7 measured ~12.4 s) |

`calculate` execution is near-zero — delta ≈ extra model round. **L-1 skipped** — logs sufficed.

---

## 2. Google API latency (H-4)

Unauthenticated discovery GET from this machine (requests / httpx, n=5):

| API | requests median ms | max ms |
|-----|-------------------:|-------:|
| Gmail | 140.6 | 153.7 |
| Calendar | 169.4 | 183.0 |
| Drive | 170.6 | 210.2 |
| People | 116.1 | 385.6 |

All HTTP 200. No TLS/proxy issues. `[EXT]` Google-published “typical API latency” for these calls: **none found** in this pass. Network RTT ≪ model-round cost.

---

## 3. Rounds per ability (minimum, spoken)

| Request | Fine-grained (a) | Coarse (b) |
|---------|------------------:|-----------:|
| What’s on calendar tomorrow | 1–2 (+ optional skill_view) | 1 |
| When was last meeting with Dana | 1–2 (search + get) | 1 |
| Anything important in email | 2+ (list + gets) | 1 metadata page |
| Draft reply to Dana saying yes | 1–2 read + compose (no send) | 1–2 |
| Find lease PDF | 1–2 Drive | 1 |
| Mike’s number | 1 People | 1 |

Plus mandatory `skill_view` prelude if `google-workspace` matches before a plugin exists (Phase 9 Q5).

---

## 4. `execution_guidance` and acting (LEAD-9)

`agent/prompt_builder.py` ~L423–430:

> When a question has an obvious default interpretation, act on it immediately instead of asking for clarification… Only ask when the ambiguity genuinely changes what tool you would call.

Profile: `execution_guidance: auto` (default). Conflicts with `A1` only if she **sends** without a code gate — the gate must not rely on her asking. Drafting without asking is a softer tension. **LEAD-9: CONFIRMED.**

---

## 5. Skill routing

Mandatory skills rule (~L1322–1339): if a skill matches, **must** `skill_view` even if basic tools could handle it. `google-workspace` description matches Gmail/Calendar/Drive — routes to terminal skill path today. A future plugin competes with this unless skill disabled/demoted or guidance changed (`S54`).

---

## 6. Result budget

Hermes default result size 100_000 chars; turn 200_000; spillover preview ~1500. Safe Workspace result: prefer metadata pages (e.g. ≤20 items, newest first), body only on request; signal “more available — narrow it” in tool JSON. Coarse tools can answer typical spoken questions from one bounded page.

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-37 | [MATCH] | — | Tool round ~+8–12 s voice (`S54` / LEAD-9); logs confirm. |
| P8PRE-AUD-38 | [RISK] | HIGH | Mandatory `skill_view` → Workspace skill (terminal) competes with plugin path. |
| P8PRE-AUD-39 | [RISK] | MEDIUM | `<act_dont_ask>` puts weight on send gate, not her asking. |
| P8PRE-AUD-40 | [MATCH] | — | Google RTT ≪ model round (H-4). |
