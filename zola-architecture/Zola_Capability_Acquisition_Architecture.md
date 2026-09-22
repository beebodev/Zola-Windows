# Capability Acquisition Architecture
### Foundational Architecture for How Zola-Windows Gains New Capabilities
---
## Vision
Capability acquisition is how Zola-Windows's runtime surface grows after initial build — new skills written and installed, new MCP servers and plugins connected, configuration changed at runtime. On the Hermes substrate this is not a hypothetical future concern: Hermes ships with live skill authoring, a configurable skill-write approval gate, CLI fallback paths, and a plugin/MCP system that runs third-party code with access to configured secrets.
This document exists because that domain had no Zola architecture document to audit against during the WINH06 phase of the Windows/Hermes gap audit — Hermes was scored on mechanism (`[MECHANISM]`/`[RISK]`/`[ABSENT]`), not against a Zola requirement, because no requirement existed to score against. This document is that requirement, written after the fact, so future work in this domain — Cursor prompts, build tracks, later hardening passes — has something real to check against instead of inferring intent from an audit finding.
The system should eventually feel less like:
> "whatever the framework ships with, left as configured"
and more like:
> "a deliberate, stated position on what Zola is allowed to acquire, and under what authority."
---
## Core Philosophy
### Personal-Use Posture, Stated Explicitly
Zola-Windows runs, for now, as a single-user product on the user's own machine. The governing decision across this whole domain (`H5`, `H6`, `A8`, locked in Decisions Locked) is: **accept Hermes's stock capability-acquisition behavior as-is, rather than layering Zola-specific gating on top of it.** This is not an oversight or a deferred audit finding — it is a considered choice, made because the realistic threat model for a single-user personal machine is different from a shared or distributed deployment, and because building custom gating before it's needed adds complexity without corresponding value yet.
This posture carries a standing trigger, established alongside the Security bucket of Decisions Locked: **every acceptance in this document is revisited together before any public or multi-user distribution of Zola-Windows.** This document does not re-litigate that trigger per item — it is the same trigger, applied here.
### Mechanism Before Policy
Where Hermes already has a real mechanism (a skill-write approval flag, an MCP secret-injection path), this document states what Zola-Windows does with that mechanism rather than redesigning it. This document does not attempt to build a parallel capability-governance system — consistent with the "extend, don't own a parallel copy" pattern established for memory (`C4`) and identity (`C5`) elsewhere in Decisions Locked.
---
## Non-Goals
Capability Acquisition Architecture is not:
- a redesign of Hermes's skill, plugin, or MCP systems — it states Zola-Windows's posture toward the mechanisms Hermes already has
- a general security architecture — code signing, credential storage, and ship-bar questions are covered by the Security bucket of `DESIGN_DECISIONS.md` (`H1`–`H6`), not restated here except where they intersect capability acquisition directly (`H5`, `H6`)
- applicable to the Android/zola-main capability model — that product has its own Agent Map and skill governance, out of scope here
- a commitment that this posture is permanent — see the standing trigger above
---
## Long-Term Architectural Pillars
---
## 1. Skill Write Authority
### Purpose
Define who or what may author, modify, or install a skill at runtime, and under what approval gate.
### Current Posture (`A8`)
Hermes ships with `write_approval: False` by default — skill writes are ungated unless explicitly configured otherwise. Zola-Windows accepts this default rather than overriding it to default-on approval. This applies uniformly regardless of trigger (a live user request, a background-review pass, or any other skill-writing path Hermes exposes).
### Background-Review Fork (`A5`, `H5`)
Hermes's background-review fork can, in combination: write skills or memory, speak (`review.summary`), and execute from a tool whitelist — all without live user oversight. Zola-Windows accepts this combined authority at Hermes's stock configuration rather than adding gating on top of it. This was evaluated explicitly (not overlooked) during Decisions Locked and resolved the same way as the rest of this bucket: accepted for personal use, revisited under the standing trigger.
### Important Principle
Skill write authority on Zola-Windows today is Hermes's own default, unmodified. Any future change to this posture is a deliberate decision, not a drift.
---
## 2. Default-Config Risk Posture
### Purpose
State Zola-Windows's position on the specific default-configuration risks WINH06 identified, so a future reader doesn't have to reconstruct the reasoning from audit findings alone.
### Findings and Posture (`H5`)
| Finding | What it is | Zola-Windows posture |
|---|---|---|
| `WINH06-AUD-02`/`08` | Ungated skill writes, including the background-review fork | Accepted (Hermes default) |
| `WINH06-AUD-10`/`21` | CLI fallback paths for skill/config operations | Accepted (Hermes default) |
| `WINH06-AUD-17` | Home-directory `SOUL.md` can be read/written outside the expected scope | Accepted (Hermes default) |
None of these are gated more strictly for Zola-Windows than Hermes ships with. This table exists so that "accepted" is a visible, itemized decision rather than an absence of one.
### Important Principle
A risk that has been evaluated and accepted is a different fact than a risk nobody looked at. This table is the record that these were looked at.
---
## 3. MCP and Plugin Secret Inheritance
### Purpose
State Zola-Windows's position on secret exposure to third-party MCP servers and plugins.
### Current Posture (`H6`)
Hermes's `_build_safe_env()` deliberately re-injects configured secrets into MCP subprocess environments — by design, on the reasoning that a user who configured a backend did so precisely so subprocesses could consume it. Zola-Windows accepts this behavior unmodified. No sandboxing, no privilege reduction, and no refusal of unreviewed third-party MCP servers is added on top of Hermes's stock behavior.
### Important Principle
Any MCP server or plugin a user connects to Zola-Windows today inherits whatever secrets Hermes's safe-env construction exposes to it. This is accepted, not hidden — a user adding a new MCP server should be understood to be extending trust to it under this posture.
---
## 4. On-Box Training Loop
### Purpose
Record that on-device model training is explicitly out of scope, so it is never mistaken for an unaddressed gap.
### Posture (`S8`)
No on-box training loop exists or is planned for Zola-Windows. This is an accepted absence, not a deferred requirement — confirmed during the WINH06 audit and carried through Decisions Locked without re-opening.
---
## 5. One Policy, Not Path-Dependent
### Purpose
Confirm that capability-acquisition governance does not need to vary by integration path.
### Posture (`A9`, consistent with `C1`)
Decisions Locked settled on a single client integration path (Path B — native Windows client against `hermes serve`). The capability-acquisition posture in this document applies uniformly; there is no second path requiring separate gating logic.
---
## Authority Boundaries
These boundaries apply across every mechanism this document covers.
### Capability acquisition on Zola-Windows may:
- write, modify, or install skills under Hermes's stock `write_approval: False` gate
- run third-party MCP servers and plugins with Hermes's stock secret-injection behavior
- use CLI fallback paths for skill/config operations where Hermes exposes them
### Capability acquisition on Zola-Windows must not:
- exceed Hermes's own configured gates — nothing in this document authorizes bypassing `approvals.mode` or any other Hermes-native gate; it only states that Zola-Windows does not add a *stricter* gate on top
- be treated as a permanent posture — every acceptance here is subject to the standing security-deferral trigger and must be revisited before public or multi-user distribution
---
## Integration Points
This document connects to:
- `zola-architecture/lore/DESIGN_DECISIONS.md` — `H5`, `H6`, `A5`, `A8`, `A9`, `S8`, the decisions this document records in prose
- `Zola Privacy and Data Ownership Plan.md` — Section 8, Sensitive Capability Governance (the Android-track equivalent governance model; Zola-Windows's posture is deliberately looser for now, per the reasoning above)
- `Zola Master Architecture Plan.md` — Section 13, Trust, Permission, and Privacy Framework (the long-term aspirational target this document's near-term posture does not yet implement)
---
## Known Constraints and Deferred Work
### Standing Security-Deferral Trigger
Every posture in this document is accepted for a single-user, personal-use deployment. All of it is revisited together — alongside `H1`–`H6` — before any public release or multi-user distribution of Zola-Windows. This is one trigger applied across two documents (this one and the Security bucket in `DESIGN_DECISIONS.md`), not independent deferrals.
### No Independent Tool-Authorization Coverage
This document covers *acquiring* capabilities (skills, plugins, MCP servers, config). It does not cover authorization to *use* already-available tools during live or background execution — that is `Zola_Tool_Authorization_Architecture.md`'s domain.
---
## Long-Term End State
Capability Acquisition Architecture eventually evolves toward:
- explicit, itemized gating decisions rather than inherited framework defaults, once Zola-Windows moves beyond personal single-user use
- a real distinction between what a trusted first-party skill may do and what a newly connected third-party MCP server may do
- an accepted-risk record that shrinks over time as each item is either hardened or re-justified, not one that silently persists unexamined
---
## Final Principle
An accepted risk that was never looked at is a gap. An accepted risk that was looked at, reasoned about, and written down is a decision. This document exists to make every item in it the second kind.
