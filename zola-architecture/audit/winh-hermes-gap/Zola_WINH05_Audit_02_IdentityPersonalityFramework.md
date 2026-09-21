# WINH05 Audit 02 — Identity and Personality Framework

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola Identity and Personality Framework.md` (Identity Seed §1, locked vs adaptive, Growth Rings §2, Style Profile §3, Feedback Loop §4, Anchors §5, Memory-driven personality §6, Drift Detection §7, Baseline Review §8, endpoint consistency §9).

Carries `WINH04-AUD-01` Layer 5 deferral: context-scoped personality vs a single `USER.md`. The WINH04 memory-agency exception does **not** apply here.

---

## 1. Identity Seed as a fixed, protected trait set

**Zola requires:** a small non-negotiable seed (Truthful, Restrained, Calm, …) that is **locked** — not modified by interaction, feedback, style penalty, or baseline review (`Framework` §1 Locked Versus Adaptive Traits; Important Principle: the seed is not a starting point the system grows away from).

**Hermes:** identity is **editable prompt text**.

- Primary identity slot: `$HERMES_HOME/SOUL.md`, loaded by `agent/prompt_builder.py` `load_soul_md` L1452–1484. Content is threat-scanned and truncated, then injected **verbatim** (docs: “no wrapping language”). There is no protected-vs-unprotected split inside the file.
- First-run seed: `hermes_cli/config.py` `_ensure_default_soul_md` L611–623 writes `DEFAULT_SOUL_MD` (`hermes_cli/default_soul.py` L9–17) unless the user has customized it. Customized files are never touched. The user (or Desktop profile UI) may rewrite the entire identity.
- Fallback when SOUL.md is missing/empty: `DEFAULT_AGENT_IDENTITY` (`prompt_builder.py` L130–138) — a **behavior-spec paragraph**, not a trait table. Comment L131: “a behavior spec … not a trait list — trait lists change nothing.” Wired in `agent/system_prompt.py` `_identity_parts` L488–494: SOUL.md **or** that constant.
- Profiles: each `HERMES_HOME` has its own `SOUL.md` (`hermes_cli/profiles.py` clone/seed). Switching profile switches identity wholesale.

There is **no** sealed constant list of locked traits (truth handling, privacy, restraint, …) that a write path is forbidden to change. `SOUL.md` is the product’s intended customization surface (`hermes_cli/tips.py`: “SOUL.md completely replaces the agent's default identity”).

**Label:** `[GAP]` `WINH05-AUD-01` (HIGH) against Framework §1.

---

## 2. Identity vs Personality separation

**Zola requires:** Identity (what the agent **is**, stable) and Personality (how it **communicates**, adaptive) as two separable layers. Identity anchors personality; personality must not overwrite identity (`Framework` Core Philosophy).

**Hermes prompt assembly** is a **separate mechanism** from `MEMORY.md`/`USER.md` injection (confirmed):

| Slot | Function | What it is |
|---|---|---|
| Stable identity | `system_prompt.py` `_identity_parts` L488–494 → `build_system_prompt_parts` L617 | SOUL.md **or** `DEFAULT_AGENT_IDENTITY` |
| Ephemeral overlay | `hermes_cli/personality.py` `resolve_ephemeral_system_prompt` L118–124; appended at API time (`agent/turn_context.py` L1138–1139; `system_prompt.py` L639: “never cached”) | `/personality` named preset **or** `agent.system_prompt` |
| Volatile user/memory | `_memory_parts` in `system_prompt.py`; `tools/memory_tool.py` L1–4 frozen MEMORY.md/USER.md | Fact/profile dump |

So persona/system-instruction text is **not** the memory tool. Assembly owner: `agent/system_prompt.py` `build_system_prompt` L666 + `build_system_prompt_parts` L605.

**What is missing vs Zola:** the split is **prompt-cache tiers and override slots**, not locked-vs-adaptive types. `/personality` can replace how the agent speaks **and** who it claims to be (`BUILTIN_PERSONALITIES` includes “You are Neko-chan…”, “Captain Hermes…”, `personality.py` L19–34). Nothing prevents the overlay from contradicting SOUL.md. USER.md is “who the **user** is,” not Zola Layer 5 personality.

**Label:** `[PARTIAL]` `WINH05-AUD-02` (MEDIUM) — separable **inputs** exist; they are not an Identity Seed vs Style Profile architecture.

---

## 3. Personality evolution through interaction, not configuration

**Zola requires:** Growth Rings / Style Profile updated from explicit and implicit interaction signals; configuration is not the growth mechanism (`Framework` §2–4, Core Principles).

**Hermes:**

- Tone/style is set by **editing SOUL.md**, selecting `display.personality`, or writing `agent.system_prompt`. `persist_personality` (`personality.py` L127–145) writes the **name** of a preset to `config.yaml`. That is configuration.
- Transcript history in `state.db` is **not** mined for style signals. No Style Profile schema, no signal weights, no Behavioral Learning Layer analog.
- Holographic `trust_score` (`plugins/memory/holographic/store.py` L17; `retrieval.py` L69: `fact["score"] = relevance * fact["trust_score"]`) ranks **which facts to retrieve**. It does **not** feed response phrasing, warmth, or formality. Not a personality-adaptation mechanism.
- Honcho observations (optional plugin) model the **user/AI peer** in a vendor store; they are not a Zola Style Profile and are not default (`memory.provider` default `""`).

**Label:** `[GAP]` `WINH05-AUD-03` (HIGH) against Framework §2–4.

---

## 4. Drift detection and correction

**Zola requires:** periodic/event-triggered compare of Style Profile vs Identity Seed; rollback of drifted entries; baseline review (`Framework` §7–8).

**Hermes searched:** `drift` hits are file-roundtrip guards (`memory_tool_store.py` `_drift_error`), contract/schema drift comments, and skill-curator **staleness**. `agent/curator.py` archives unused **agent-created skills** (WINH04 skills audit) — not persona-vs-seed audit.

No scheduled self-audit of SOUL.md vs current behavior. No `anchorViolationFlag`. No drift log for style.

**Label:** `[GAP]` `WINH05-AUD-04` (MEDIUM) against Framework §7–8. Curator is not this mechanism.

---

## 5. Context-scoped personality (WINH04-AUD-01 Layer 5 deferral)

**Zola requires:** Style Profile entries keyed by context (`shop_work`, `casual_conversation`, `security_event`, …); a single universal profile “would flatten the user’s actual preferences” (`Framework` §3 Context Labels). Layer 5 of the Memory Hierarchy is the same requirement for **behavioral** memory.

**Hermes:**

- **One active persona string per session:** SOUL.md (profile home) + optional one `display.personality` overlay. No context key on either.
- **`USER.md`:** single “USER PROFILE (who the user is)” block (`memory_tool_store.py` `MEMORY_BLOCK_HEADERS` L20–21). No `contextLabel`. Confirmed WINH04-AUD-01 / AUD-12.
- **Hermes profiles** (`hermes_cli/profiles.py`): separate `HERMES_HOME` directories, each with its own SOUL.md/memories. That is **multiple agent instances**, not one user with shop-vs-desk style slices in the same relationship.
- `/personality` is a **manual session overlay**, not an automatic context switch.

**Label:** `[GAP]` `WINH05-AUD-05` (HIGH) against Framework §3 and the deferred Layer 5 identity angle.

**Implication for WINH04-AUD-01 Layer 5:** this audit does **not** collapse Layer 5 into the personality finding. Layer 5 is still a **memory-store** gap (no context-keyed preference records). Phase 2 adds that there is also **no** context-keyed **persona** assembly. Additive, not a rescore of WINH04-AUD-01 (see synthesis OQ4).

---

## Finding summary (this document)

| ID | Label | Sev | Against |
|---|---|---|---|
| WINH05-AUD-01 | [GAP] | HIGH | Framework §1 Identity Seed / locked traits |
| WINH05-AUD-02 | [PARTIAL] | MEDIUM | Identity vs personality as separable **typed** layers |
| WINH05-AUD-03 | [GAP] | HIGH | §2–4 growth from interaction |
| WINH05-AUD-04 | [GAP] | MEDIUM | §7–8 drift detection / baseline review |
| WINH05-AUD-05 | [GAP] | HIGH | §3 context-scoped Style Profile; Layer 5 deferral |
