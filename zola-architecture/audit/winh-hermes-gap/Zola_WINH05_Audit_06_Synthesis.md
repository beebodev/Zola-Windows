# WINH05 Audit 06 — Domain Synthesis (this audit only)

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Not a WINH00 closeout. No integration path chosen. Memory-agency exception (Hermes owns fact-memory R/W) does **not** cover identity seed, personality, self-model, or session identity.

Documents: `Zola_WINH05_Audit_02_IdentityPersonalityFramework.md` … `_05_SessionIdentity.md`.

---

## Section 1 — Finding summary table

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH05-AUD-01 | [GAP] | HIGH | `prompt_builder.py` L130–138; `load_soul_md` L1452; `config.py` `_ensure_default_soul_md` L611–623 | No locked Identity Seed; SOUL.md is fully replaceable prompt text |
| WINH05-AUD-02 | [PARTIAL] | MEDIUM | `system_prompt.py` `_identity_parts` L488–494; `personality.py` L118–124; `memory_tool.py` L1–4 | Identity / overlay / USER.md are separate **slots**, not locked-vs-adaptive types |
| WINH05-AUD-03 | [GAP] | HIGH | `personality.py` `persist_personality` L127–145; holographic `retrieval.py` L69 | Style is config/presets; no interaction-driven Style Profile; `trust_score` is retrieval only |
| WINH05-AUD-04 | [GAP] | MEDIUM | (none — curator is `agent/curator.py` skills only) | No persona drift detection or baseline review vs a seed |
| WINH05-AUD-05 | [GAP] | HIGH | `memory_tool_store.py` L20–21; `profiles.py` | One persona string per session; USER.md has no context key; profiles are other instances |
| WINH05-AUD-06 | [RISK] | HIGH | `default_soul.py`; `personality.py` L19–34; `voice_live.py` L48–69; `auxiliary_client.py` L1352; `doctor_state.py` L133 | Multiple independently-maintained “You are …” strings |
| WINH05-AUD-07 | [RISK] | MEDIUM | same sites as AUD-06 plus `HERMES_AGENT_HELP_GUIDANCE` | Agent name/identity change is a multi-file edit; customized SOUL.md files are never auto-updated |
| WINH05-AUD-08 | [GAP] | MEDIUM | `memory_tool_store.py` USER.md | No style-profile store separate from free-text USER.md |
| WINH05-AUD-09 | [GAP] | MEDIUM | (none) | No numeric clamps / bounded-evolution / drift log for learned traits |
| WINH05-AUD-10 | [GAP] | HIGH | `system_prompt.py` `_identity_parts` | No `SelfBeliefBlock` or structured self-view |
| WINH05-AUD-11 | [GAP] | MEDIUM | `prompt_builder.py` L137 vs SMA hedging | “Say so when unsure” is a style line, not computed hedging |
| WINH05-AUD-12 | [GAP] | MEDIUM | (no SMA module) | No read-only self-model layer; agent loop both writes memory and speaks |
| WINH05-AUD-13 | [MATCH] | LOW | (no SMA UI) | No user-facing belief-confidence numbers (prohibition not violated) |
| WINH05-AUD-14 | [PARTIAL] | MEDIUM | `hermes_state_common.py` `sessions` L328–389 | Explicit session row; no `deviceId`; live sid ≠ durable id |
| WINH05-AUD-15 | [RISK] | HIGH | `hermes_state_ids.py`; `methods_session.py` L65–67; gateway/`agent_init` callers | Shared ID **shape**, many mint **sites**, plus runtime uuid and optional provider sessions |
| WINH05-AUD-16 | [PARTIAL] | MEDIUM | `tui_gateway/server.py` L122–140; `session_lifecycle.py` | WS orphan/resume ≠ 30s app-background session close |
| WINH05-AUD-17 | [PARTIAL] | MEDIUM | `sessions.user_id` / `profile_name` | Profile/connection scoped, not user+device provenance |
| WINH05-AUD-18 | [PARTIAL] | MEDIUM | `messages.session_id` vs `memory_tool.py` | Transcripts carry session_id; MEMORY.md writes do not |

Counts: **18 findings — 6 HIGH, 11 MEDIUM, 1 LOW.**

---

## Section 2 — What Hermes covers as-is (identity / personality / session)

**Identity / personality.** Hermes has a real, first-class **identity file** (`SOUL.md` in `$HERMES_HOME`, loaded first in the stable system-prompt tier) plus a **fallback paragraph** (`DEFAULT_AGENT_IDENTITY`) and **named `/personality` overlays**. Prompt assembly is centralized in `agent/system_prompt.py` (stable / context / volatile tiers). That is a capable **configurable agent persona**, not Zola’s locked seed + learned context-scoped Style Profile. Nothing in default Hermes grows tone from interaction history. Skill curator is unrelated.

**Self-model.** Nothing comparable exists. No `SelfBeliefBlock`, no computed hedging, no SMA authority box. The match on “don’t show confidence numbers” is only because there is no such signal.

**Session identity.** Hermes **does** persist an explicit `sessions` row in `state.db` (id, optional user_id, start/end, source, profile), with messages attached by FK. JSON-RPC can resume a durable `session_key` after a short disconnect or via `session.resume` after process death (WINH03). That is a wrap-able session **store**, not Zola’s single-mint `SessionRecord` with 30s foreground/background semantics and device provenance. Fact-memory writes are not session-stamped.

---

## Section 3 — What needs a Zola-built adapter layer

Wraps rather than replacements:

1. **SOUL.md as a projection surface** (`AUD-02`): adapter owns `ZolaIdentityProfile` (or equivalent) and **writes/injects** a Hermes-compatible identity block into the stable tier — or sets `skip`/empty SOUL and prepends Zola text via `system_message` / `ephemeral_system_prompt`. Adapter must also **disable or ignore** `/personality` builtins that rewrite “who I am” (`AUD-06`).
2. **Session resume** (`AUD-14`, `AUD-16`): keep Hermes `state.db` `sessions.id` as the durable conversation key for the Windows client; adapter owns Zola start/end/grace **policy** if those are required, mapping onto create/end/resume rather than assuming Hermes already implements 30s backgrounding.
3. **Transcript provenance** (`AUD-18`): already on messages — adapter can treat `messages.session_id` as the session FK for chat history. Memory-file writes still need an adapter stamp or a side index.
4. **Profiles** (`AUD-05` caveat): Hermes profiles are **not** context-scoped personality; do not reuse them as Style Profile slices. They remain a multi-agent-home feature if the product wants isolated operators.

---

## Section 4 — What must be built from scratch

| Capability | Why scratch | Finding |
|---|---|---|
| Locked Identity Seed (trait table + non-editable enforcement) | SOUL.md and overlays are unconstrained text | AUD-01 |
| Interaction-driven Style Profile (context keys, signals, confidence) | Config/presets only; USER.md is flat prose | AUD-03, AUD-05, AUD-08 |
| Persona drift detection + baseline review + numeric clamps | No job, no ranges, curator ≠ this | AUD-04, AUD-09 |
| Canonical identity object + derived builders | Several “You are …” authors | AUD-06, AUD-07 |
| `SelfBeliefBlock` + computed hedging | Static prompt only | AUD-10, AUD-11 |
| Read-only SMA layer (no memory write / no direct execute) | No subsystem; agent loop writes and speaks | AUD-12 |
| Single mint seam + `deviceId` + Zola 30s foreground/background | Many callers; WS grace is a different policy | AUD-15, AUD-16, AUD-17 |
| `sessionId` on MEMORY.md / plugin fact writes | Files/rows have no session field | AUD-18 (memory half) |

`AUD-13` is not scratch work.

---

## Section 5 — Open questions for WINH00

1. **Identity assembly owner.** Does Zola-Windows adopt Hermes’s SOUL.md + `system_prompt.py` as the live identity-rendering path, or does Zola inject its own canonical identity text over/around it (same fork as WINH04 synthesis OQ1 for MEMORY.md — compatibility projection vs Zola owns assembly)? This choice drives `AUD-01`, `AUD-06`, `AUD-07`.
2. **SessionRecord vs Hermes `sessions`.** Hermes already has a durable session row and resume. Is that worth wrapping as the Windows conversation id, or must Zola-Windows still inject its own `SessionRecord` (foreground/background, 30s grace, `deviceId`) regardless — given the architecture document’s own status line that the Zola model is design-locked and not a Hermes feature?
3. **SMA write ban vs memory exception.** Hermes’s agent-writes-memory exception relaxes an analogous boundary for **plain facts**. Self-Model Awareness still requires a **read-only** introspective layer that must not write memory or fire speech. Should that SMA boundary stay **hard** on the Windows track even though fact-memory write authority was given to Hermes? Tension: putting SMA inside `AIAgent` inherits write/execute; putting it beside Hermes requires a new component the pin does not provide.
4. **Layer 5 vs this audit’s `AUD-05`.** Phase 2 confirms Hermes has no context-scoped **persona**. That does **not** rescore `WINH04-AUD-01` Layer 5: Layer 5 remains a **memory-store** gap (no context-keyed preference records). `AUD-05` is additive (prompt/personality assembly). WINH00 should keep both IDs.
5. **Lore files.** This track has no `ROADMAP.md` / `DESIGN_DECISIONS.md` / `OPEN_QUESTIONS.md` on disk; this audit was scoped without them. If zola-windows will need its own lore tracking, that is a WINH00 decision — not started here.

Standing earlier findings that still color this domain: WINH03 session live vs durable (`AUD-09`); WINH04 USER.md flattening (`AUD-12`) and DWA absence (`AUD-11`).
