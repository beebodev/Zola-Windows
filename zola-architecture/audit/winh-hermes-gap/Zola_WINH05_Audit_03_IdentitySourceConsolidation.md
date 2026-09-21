# WINH05 Audit 03 — Identity Source Consolidation

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Architecture_Identity_Source_Consolidation_Plan.md` (one canonical source, derived builders, name in one field, Style Profile store, locked vs evolvable, numeric drift clamps).

---

## 1. Single canonical identity source

**Zola requires:** one profile object; every prompt surface calls a builder; identity content authored in one place; “If identity content exists in more than one place, one of them is wrong” (One Source, Derived Everywhere).

**Hermes:** there is a **primary** identity slot (SOUL.md / `DEFAULT_AGENT_IDENTITY`), but **not** a single authored source. Independently maintained strings that can reach a model:

| # | Text | File / function | How it reaches a model |
|---|---|---|---|
| 1 | `DEFAULT_AGENT_IDENTITY` (“You are Hermes Agent, built by Nous Research…”) | `agent/prompt_builder.py` L130–138 | `system_prompt.py` `_identity_parts` L494 when SOUL.md is absent |
| 2 | `DEFAULT_SOUL_MD` (comment: kept identical to #1) | `hermes_cli/default_soul.py` L9–17 | Seeded to `$HERMES_HOME/SOUL.md` by `_ensure_default_soul_md` (`config.py` L611–623); then `load_soul_md` L1452 |
| 3 | User-edited `SOUL.md` | `$HERMES_HOME/SOUL.md` (per profile) | Same `load_soul_md`; **overrides** #1/#2 |
| 4 | `BUILTIN_PERSONALITIES` (14 named strings, many “You are …”) | `hermes_cli/personality.py` L19–34 | `resolve_ephemeral_system_prompt` L118–124 → API-time append |
| 5 | User `agent.personalities` / root `personalities:` | `config.yaml` | Overlay on #4 (`available_personalities` L86–97) |
| 6 | `agent.system_prompt` | `config.yaml` | Used when no named personality (`resolve_ephemeral_system_prompt` L124) |
| 7 | `LIVE_PERSONA` (“You are Hermes, a calm and friendly voice assistant…”) | `tools/voice_live.py` L48–69 | Voice-live vendor session persona (separate model from the agent) |
| 8 | Alibaba model-name identity | `system_prompt.py` `_alibaba_identity_part` L526–537 | Extra stable-tier sentence when `provider == "alibaba"` |
| 9 | Aux fallback `"You are a helpful assistant."` | `agent/auxiliary_client.py` L1352 | Codex/aux path when no system message in kwargs |
| 10 | Doctor template | `hermes_cli/doctor_state.py` L133 | Can create `SOUL.md` with “You are Hermes, a helpful AI assistant.” — **wording not identical** to `DEFAULT_SOUL_MD` |
| 11 | Optional Honcho `aiCard` / AI peer representation | `plugins/memory/honcho/` (injected via `MemoryManager.build_system_prompt`) | Only if `memory.provider = honcho` |

Call sites that **assemble** the main agent prompt (derive from SOUL.md + overlays, do not each author a full persona): `system_prompt.py` `build_system_prompt_parts` L605 / `build_system_prompt` L666; ephemeral join in `turn_context.py` L1138, `conversation_loop.py` L1076, `chat_completion_helpers.py` L1982.

**Failure mode the Zola doc exists to prevent:** multiple independently-maintained identity narratives. Hermes has that: default identity is duplicated (#1/#2 by comment discipline), doctor template (#10) can diverge, personality presets (#4) and voice-live (#7) are separate “You are …” authors, aux (#9) is a third generic assistant.

**Label:** `[RISK]` `WINH05-AUD-06` (HIGH) — SOUL.md is the intended live source for the **agent** loop, but it is not the only authoring site and is not a derived-builder architecture.

---

## 2. What happens on an identity update (e.g. the agent’s name)

Trace: rename “Hermes Agent” / “Hermes” in user-visible model-facing identity.

| Location | Must edit? |
|---|---|
| `agent/prompt_builder.py` `DEFAULT_AGENT_IDENTITY` L133 | Yes — fallback identity |
| `hermes_cli/default_soul.py` `DEFAULT_SOUL_MD` L10 | Yes — first-run seed (must stay in lockstep with the previous, per file comment L3–8) |
| Existing user `SOUL.md` files | Yes — `_ensure_default_soul_md` **will not** rewrite customized souls (`config.py` L620–621) |
| `hermes_cli/personality.py` `BUILTIN_PERSONALITIES` L19–34 | Yes — “Captain Hermes”, “They call me Hermes”, etc. |
| `tools/voice_live.py` `LIVE_PERSONA` L49 | Yes — spoken-layer name |
| `hermes_cli/doctor_state.py` L133 | Yes — repair template |
| `agent/system_prompt.py` `HERMES_AGENT_HELP_GUIDANCE` L141–148 | Yes — “You run on Hermes Agent (by Nous Research)” |
| Website/docs (`website/docs/user-guide/features/personality.md` and i18n copies) | Yes — product copy |
| Desktop/i18n `productName` (WINH02-AUD-11) | Product chrome, not the model prompt — still a user-facing name surface |

That is **at least six Python authoring sites** plus every already-seeded `SOUL.md` plus docs. There is no `ZolaIdentityProfile.name` equivalent. Changing the name in SOUL.md alone leaves voice-live, builtins, doctor, and fallback out of date.

**Label:** `[RISK]` `WINH05-AUD-07` (MEDIUM) against “The Name Lives in One Field.”

---

## 3. Style profile / learned-preference storage

**Zola requires:** a Style Profile document structurally **separate** from the Identity Seed; per-context fields; observation counts; not free-text USER.md (`Consolidation Plan` Part 2).

**Hermes:**

- No Firestore/SQLite style-profile schema in the default agent.
- Learned “how the user likes to be spoken to” can only accumulate as **prose** in `USER.md` or `MEMORY.md` (`tools/memory_tool.py` / `memory_tool_store.py`) if the model chooses to write it. That store has no context keys, no `styleObservationCount`, no warmth/formality floats (WINH04-AUD-01, AUD-12).
- `display.personality` is a **selected preset name**, not learned data.
- Holographic facts are optional memory, not a style profile.

**Label:** `[GAP]` `WINH05-AUD-08` (MEDIUM). `USER.md` is the only default place such data could live, and it is the wrong shape.

---

## 4. Guardrails against evolution becoming drift

**Zola requires:** locked traits as sealed constants; evolvable fields with min/max; scheduled clamp (20% nudge); hard reset at extremes; drift log (`Consolidation Plan` §8–9).

**Hermes:**

- Phase 2 already: no seed-vs-style drift job (`WINH05-AUD-04`).
- No numeric clamps on warmth/formality/humor. Personality overlays have **no range type** — they are strings.
- `write_approval` gates **memory/skills file writes**, not “how far a trait moved from seed.”
- SOUL.md threat scan (`_scan_context_content`) blocks **injection**, not identity-anchor violations.

**Label:** `[GAP]` `WINH05-AUD-09` (MEDIUM) against bounded evolution / Part 3.

---

## Finding summary (this document)

| ID | Label | Sev | Against |
|---|---|---|---|
| WINH05-AUD-06 | [RISK] | HIGH | One Source, Derived Everywhere |
| WINH05-AUD-07 | [RISK] | MEDIUM | Name / identity in one field |
| WINH05-AUD-08 | [GAP] | MEDIUM | Style Profile store |
| WINH05-AUD-09 | [GAP] | MEDIUM | Bounded evolution / clamps |
