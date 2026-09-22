# Tool Authorization Architecture
### Foundational Architecture for What Zola-Windows's Agents Are Allowed to Do
---
## Vision
Tool authorization is distinct from capability acquisition: it is not about what Zola *can* eventually do, but about what any given execution context — a live conversational turn, the background-review fork, a scheduled cron job — is actually permitted to *do right now*, especially where a tool has a real-world effect (sending a message, writing data, executing a command).
This document exists because that domain had almost no Zola requirement to audit against during the WINH08 phase — only two lines under Known Context existed. This document is the real specification that should have existed, written after the fact from the decisions actually made in Decisions Locked, so future work has a stated authorization model to build against rather than inferring one from scattered audit findings.
The system should eventually feel less like:
> "whatever tool whitelist the framework happened to have configured"
and more like:
> "a presence that knows the difference between speaking, executing, and acting irreversibly — and treats them with different levels of care."
---
## Core Philosophy
### Hermes's Gate Is the Floor, Not the Ceiling — Except Where Zola Requires More
For most tool execution, Zola-Windows accepts Hermes's existing `approvals.mode`/danger-command overlay as sufficient (`A3`) rather than building a separate Zola-owned permission layer in front of it. This is the same personal-use, accept-the-default posture that governs capability acquisition.
There is exactly one deliberate exception: **confirmed send (`A1`).** Sending a message on the user's behalf is not treated as an ordinary tool call subject to Hermes's general gate — it is a standing Zola product requirement, established before this document existed (in the SMS Intelligence architecture's "Send Is Confirmed, Not Autonomous" principle), and it applies regardless of which trigger fires the send. This is the one place in Zola-Windows's authorization model where Zola's own gate sits *above* Hermes's default rather than deferring to it.
### Authority Is About the Trigger, Not Just the Tool
The same tool (e.g. a send) can be invoked from a live user turn, a cron job, or the background-review fork. This document's authorization boundaries are stated per-trigger where that distinction matters, not only per-tool — because a send confirmed by a live user is a different event than a send fired by an unsupervised scheduled job.
---
## Non-Goals
Tool Authorization Architecture is not:
- a replacement for Section 13 (Trust, Permission, and Privacy Framework) of `Zola Master Architecture Plan.md` — that section describes the long-term aspirational framework; this document states Zola-Windows's actual near-term posture, which does not yet implement it
- a redesign of Hermes's `approvals.mode` or danger-command overlay
- applicable to the Android/zola-main Agent Map's tool-authorization model — that system has its own subagent whitelist structure, out of scope here
- coverage of *acquiring* new tools/skills — see `Zola_Capability_Acquisition_Architecture.md` for that domain
---
## Long-Term Architectural Pillars
---
## 1. Confirmed Send
### Purpose
Guarantee that no message leaves Zola-Windows on the user's behalf without the user having explicitly confirmed its content and the act of sending.
### Requirement (`A1`)
Zola-Windows builds its own approval UI in front of `send_message_tool`/`adapter.send`, covering every outbound send path — including gateway chat replies, which Hermes's own gating (model cannot call `send_message` directly) does not cover. This applies uniformly regardless of trigger: a live user turn, cron-delivered send, CLI-invoked send, or any opt-in MCP server that can fire a send.
### Confirmation Shape
Two confirmation moments, matching the pattern already established in `Zola_Sms_Intelligence_Architecture.md`: content confirmation (Zola states what she is about to send and asks if it's right) followed by send confirmation (explicit go-ahead before the send executes). This two-step shape extends to any future send-capable channel Zola-Windows adds (e.g. Gmail via the P3-decided connector), not just SMS.
### Important Principle
Confirmed send is the one place in this document where Zola's authority is stricter than Hermes's default, not equal to it. Every other pillar below defers to Hermes's existing gate; this one does not.
---
## 2. Response Arbitration
### Purpose
State Zola-Windows's position on Hermes's multiple speech paths (`review.summary`, child-session completes, heartbeat events) that can each produce output beyond the main conversational turn.
### Current Posture (`A2`)
No suppression or arbitration layer is added for now. Zola-Windows accepts Hermes's extra speech paths as-is and observes real behavior before deciding whether filtering is needed. This is an explicit "not yet decided permanently" posture, not a final answer — revisit once there's enough real usage to evaluate against.
---
## 3. Trust/Permission Layer
### Purpose
State whether Zola-Windows owns a permission-checking layer independent of Hermes, or relies on Hermes's own gate.
### Current Posture (`A3`)
Hermes's existing `approvals.mode`/danger-command overlay is accepted as sufficient for now. No separate Zola-owned permission layer sits in front of it. This is the default posture this whole document assumes except where a pillar states otherwise (see Pillar 1, Confirmed Send).
---
## 4. Background-Review Combined Authority
### Purpose
State Zola-Windows's position on the background-review fork's combined write, speak, and tool-execute authority, from the tool-execution angle (the write-authority angle is covered in `Zola_Capability_Acquisition_Architecture.md` Pillar 1).
### Current Posture (`A5`)
Accepted at Hermes's stock configuration — the same combined-authority posture as capability acquisition, evaluated once and applied consistently rather than re-litigated per document. The background-review fork's tool whitelist, auto-deny-for-danger behavior, and `extra_tools` widening all run as Hermes configures them by default.
---
## 5. Scheduled Work Authority
### Purpose
State what authority Zola-Windows grants to time-triggered work.
### Current Posture (`S7`)
Zola-Windows uses Hermes's existing cron system for scheduled work (prepare/brief-style jobs) rather than routing that logic through a separate Zola-controlled sidecar. This means scheduled jobs run as full, unsupervised `run_conversation`s — the same authority shape as any other Hermes cron job, with no additional Zola gating layered on for scheduled triggers specifically.
### Fallback Trigger
If Hermes cron's unsupervised-`run_conversation` shape proves insufficient in practice (produces unwanted autonomous actions, for example), the fallback is a Zola-owned sidecar for time-triggered logic, evaluated at that point rather than built preemptively.
### Interaction with Confirmed Send
A cron job that reaches a send is still subject to Pillar 1 (Confirmed Send) — cron authority to *run* is not authority to *send without confirmation*. The two are independent gates.
---
## 6. Self-Model Write Boundary (Cross-Reference)
Self-Model Awareness's read-only write boundary (`A7`) is part of the Relational Intelligence Layer, currently deferred (`S2`). It is recorded in `Zola_SelfModel_Awareness_Architecture.md`, not restated here — this pillar exists only as a pointer so a future reader searching tool-authorization material for SMA's boundary finds it.
---
## 7. One Policy, Not Path-Dependent
### Purpose
Confirm that tool-authorization governance does not vary by integration path.
### Posture (`A9`, consistent with `C1`)
As with capability acquisition, the single locked integration path (Path B) means there is no second path requiring separate authorization logic.
---
## Authority Boundaries
### Tool execution on Zola-Windows may:
- execute any tool Hermes's `approvals.mode`/danger-command overlay permits, across live turns, background-review, and scheduled cron jobs, without an additional Zola-owned permission check (Pillars 3–5)
- run scheduled work as full unsupervised `run_conversation`s via Hermes cron (Pillar 5)
### Tool execution on Zola-Windows must not:
- send a message on the user's behalf through any path — live turn, cron, CLI, or MCP-triggered — without completing both confirmation steps defined in Pillar 1, regardless of what Hermes's own gate would otherwise allow
- be assumed permanently fixed at today's posture — Pillars 2–5 are personal-use defaults subject to the same standing security-deferral trigger recorded in `Zola_Capability_Acquisition_Architecture.md`
---
## Integration Points
This document connects to:
- `zola-architecture/lore/DESIGN_DECISIONS.md` — `A1`–`A5`, `A7` (cross-reference), `A9`, `S7`, the decisions this document records in prose
- `Zola_Capability_Acquisition_Architecture.md` — the companion document; that one covers acquiring capabilities, this one covers authorizing their use
- `Zola_Sms_Intelligence_Architecture.md` — origin of the two-step confirmed-send pattern this document extends to all send-capable channels
- `Zola Master Architecture Plan.md` — Section 13, Trust, Permission, and Privacy Framework (the long-term aspirational target)
---
## Known Constraints and Deferred Work
### Standing Security-Deferral Trigger
Pillars 2 through 5 are accepted personal-use postures, revisited together — alongside `H1`–`H6` and the equivalent trigger in `Zola_Capability_Acquisition_Architecture.md` — before any public or multi-user distribution. Pillar 1 (Confirmed Send) is the one exception: it is a firm product requirement, not subject to this trigger.
### Cron Fallback Not Yet Built
The sidecar fallback described in Pillar 5 is not designed or built — it is a documented fallback path to reach for if Hermes cron proves insufficient, not a current build track.
---
## Long-Term End State
Tool Authorization Architecture eventually evolves toward:
- a real Zola-owned permission layer in front of Hermes's gate, once personal-use assumptions no longer hold
- response arbitration informed by actual observed behavior rather than a placeholder "accept for now" posture
- the same explicit, itemized-decision discipline this document already applies to Confirmed Send, extended to every other pillar as each is revisited
---
## Final Principle
Confirmed send shows what this document is really about: not every tool needs its own layer of caution, but the ones that act irreversibly on the user's behalf need one regardless of what the underlying framework would otherwise allow. The discipline is knowing which is which.
