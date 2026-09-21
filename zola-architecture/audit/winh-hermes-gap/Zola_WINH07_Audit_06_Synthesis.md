# WINH07 Phase 6 — Synthesis: Hermes Authority, Governance & Routing

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola Document of Truth: Master Architecture Plan §20 (Centralized Authority Model), Core Architectural Principles (Single Authority Ownership, Truth Ownership Rule, Speech Authority Constraint, Provider Abstraction), §13 Trust/Permission/Privacy, Agent Map Core Rule. **Not scored:** §9/9a, §12 (WINH09). Cross-refs only: WINH02 surfaces; `WINH03-AUD-03/05/08`; `WINH04-AUD-02/03`; `WINH06-AUD-02/07/08/14/23/25`.

Source documents: Audit_02 ResponseAuthority, Audit_03 TrustPermissionFramework, Audit_04 RoutingAuthority, Audit_05 TruthSpeechSeparation.

These questions are not resolved here. They are listed for the developer / WINH00.

---

## Section 1 — Finding Summary Table

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH07-AUD-01 | PARTIAL | HIGH | `prompt_turn.py` L848; `server.py` L623–624, L1006; `agent_callbacks.py` L77 | Primary `message.complete` path exists; review/notices/heartbeat/child completes also speak |
| WINH07-AUD-02 | RISK | HIGH | `background_review.py` L1148–1153; `server.py` L1006 | WINH06 fork emits user-facing `review.summary` / `_safe_print` |
| WINH07-AUD-03 | PARTIAL | MEDIUM | `methods_prompt.py` L610–620; `session_auto_continue.py` L240–245 | Same-gateway submits serialize via `running`; no cross-surface arbiter |
| WINH07-AUD-04 | GAP | HIGH | searched `tui_gateway/`, `agent/` | No Response Governor / named core; `_emit` is a transport helper |
| WINH07-AUD-05 | PARTIAL | MEDIUM | `toolsets.py` L11–31; `approval_context.py` L228–237 | Scope = enabled tools + danger overlay; no §13 permission catalog |
| WINH07-AUD-06 | PARTIAL | MEDIUM | `approval.py` L494–519; `config_defaults.py` L1557–1578 | Danger/sudo/slash confirms; no contact/third-party escalation class |
| WINH07-AUD-07 | RISK | HIGH | `config_defaults.py` L1557, L767, L793–796 | Default `approvals.mode: smart` assumes trust |
| WINH07-AUD-08 | PARTIAL | MEDIUM | `approval.py` L471–519; `server.py` L1000–1002 | Approval prompts explain; smart-allow / missing toolset do not |
| WINH07-AUD-09 | GAP | HIGH | `server.py` `dispatch` vs API/ACP/MCP/webhook | Only Surfaces 2+3 share a dispatcher |
| WINH07-AUD-10 | PARTIAL | MEDIUM | `runtime_provider.py` L835–852; `background_review.py` L205–243 | Shared provider ladder; review/delegation may pick independently |
| WINH07-AUD-11 | RISK | MEDIUM | `_DropTransport`; `event_replay.py` L26–28; `_resume_reuse_live` | Orphaned output: drop / 512-ring / later attacher / session_key notify |
| WINH07-AUD-12 | GAP | MEDIUM | six inbound files (no single index) | Routing authority not discoverable in one place |
| WINH07-AUD-13 | GAP | HIGH | `conversation_loop.py`; `turn_final_response.py`; `prompt_turn.py` L848 | Same model chain reasons and phrases; no downstream formatter |
| WINH07-AUD-14 | GAP | HIGH | searched turn/stop/prompt_turn | No fidelity check that final text preserves tool data |
| WINH07-AUD-15 | GAP | HIGH | `turn_stop_gates.py`; `verification_stop.py` | Hermes is a single-pass generator; verify-on-stop ≠ Speech Authority |

**Counts:** 15 findings — **8 HIGH**, **7 MEDIUM**, **0 LOW**.

HIGH: AUD-01, 02, 04, 07, 09, 13, 14, 15. MEDIUM: AUD-03, 05, 06, 08, 10, 11, 12.

No `[MATCH]` in this phase. Closest analogs (primary `message.complete` path, `running` serialization, `resolve_runtime_provider` ladder, danger-command approval) are all `[PARTIAL]`.

---

## Section 2 — What Hermes covers as-is (authority / governance / routing)

**Response authority.** For JSON-RPC / dashboard (WINH02 Surfaces 2+3), a user turn that finishes cleanly is assembled in `prompt_turn._run_prompt_submit` and emitted as `message.complete` (`WINH03-AUD-03`). That is the primary speech path, not the only one. `write_json` / `_emit` send whatever callers pass: `review.summary` from the background-review fork (AUD-02, citing `WINH06-AUD-07` for the fork), `notification.show`, heartbeat/`/loop` turns that *reuse* `_run_prompt_submit` without a user prompt, and child-watch `message.complete` on another sid. There is no Response Governor (AUD-04). Per-session `running` plus `display.busy_input_mode` (default interrupt) serialize concurrent *submits* inside that gateway (AUD-03); they do not make speech single-owner.

**Behavioral permission.** Hermes does not implement Master Plan §13. What exists is: enabled toolsets as implicit scope; a dangerous-command / sudo / destructive-slash overlay with `approvals.mode` default `smart` (AUD-05, AUD-06, AUD-07); approval *prompts* that explain a matched danger pattern (AUD-08). Unattended/cron/single-query default to deny. There is no inspectable “allowed to summarize / interrupt / access X” table, no escalation-tier for contacting a person or alerting a third party, and silent smart-allow. Capability-acquisition gates remain WINH06; this phase does not re-open them.

**Routing.** Surfaces 2+3 share `tui_gateway.dispatch` → `_sessions[sid]`. Surfaces 1, 4, 5, 6 each resolve sessions in their own process/namespace (API hash ids, ACP `SessionManager`, MCP messaging bridge, webhook → `gateway.run` keys) (AUD-09). Provider selection shares `resolve_runtime_provider` as a *function*; background review and delegation are allowed to resolve a different model (AUD-10; `/model` human switch is `WINH06-AUD-25`). After a fail-open disconnect (`WINH03-AUD-05/08`), completed output hits `_DropTransport`, a 512-event replay ring, SQLite, and/or a later fan-out attacher of the same sid/`session_key` (AUD-11) — not a random other chat, and not a single “return to requester only” path. No one document lists these resolvers (AUD-12; pattern of `WINH06-AUD-14`).

**Truth / speech.** The conversation loop is one iterative generator: tool results go back into `messages`; the next model tokens *are* the user-facing answer (AUD-13, AUD-15). `turn_final_response` / `turn_stop_gates` / `verify_on_stop` continue or nudge coding turns; they do not check that phrasing preserved structured facts (AUD-14). Reasoning-channel display (`show_reasoning`) is UI, not Truth Ownership.

---

## Section 3 — What needs a Zola-built adapter layer

For each `[PARTIAL]` (and `[MATCH]`-with-caveats — none): wrap Hermes rather than replace the turn loop.

| ID | What to wrap | What the adapter must own |
|---|---|---|
| AUD-01 | `message.complete` as the only *chat* completion Hermes already has | Filter or coalesce `review.summary`, `notification.show`, heartbeat/loop-initiated completes, and child-sid completes before they become Zola speech. Decide which Hermes events are HUD vs utterance. |
| AUD-03 | `session["running"]` + `busy_input_mode` inside Surface 3 | Client-side (or sidecar) rule for which Windows surface may submit to a sid; do not assume Hermes will elect among API vs ACP vs gateway. Optionally force `busy_input_mode=queue` for Zola. |
| AUD-05 / AUD-06 / AUD-08 | Toolset enablement + `approvals.*` | A Zola permission document the user can inspect; map §13 verbs onto (enabled tools, approval mode, deny lists). Pass through Hermes approval cards as the danger-command UX; add explanation where Hermes is silent (smart-allow, missing tool). |
| AUD-10 | `resolve_runtime_provider` + session `/model` | Zola-owned provider policy: pin one runtime per session; ignore or override `auxiliary.background_review` / `delegation.model` if Zola forbids a second picker. |

`[RISK]` rows that an adapter can *mitigate* without replacing Hermes: AUD-02 (drop or gate `review.summary`; optionally disable `background_review.enabled` — skill-write remaining WINH06); AUD-07 (set `approvals.mode` to `manual` or `off` in Zola’s config profile; document it); AUD-11 (client interrupt on disconnect — already WINH03 advice — plus treat replay/resume as the same speech owner, not a new one).

---

## Section 4 — What must be built from scratch

| ID | Capability | Why scratch | Finding |
|---|---|---|---|
| Speech / Response Governor | One code path that may emit user-facing utterance for a session; workers prepare only | Hermes `_emit` is a transport helper; no core (AUD-04). Adapter filtering (Section 3) is a wrap if Zola sits *in front* of Surface 3 only; a true governor that covers heartbeat, review, and child windows is new Zola (or a hard Hermes subset + client policy). | AUD-04, and the extras in AUD-01/02 |
| Cross-surface routing authority | One resolver from “inbound Windows request” to one session/agent | Four of six WINH02 surfaces never enter `dispatch`. A Windows product that might expose more than JSON-RPC cannot inherit a Hermes singleton. | AUD-09, AUD-12 |
| Trust / Permission Framework (§13) | Explicit, inspectable, contextual permissions + escalation class + decision log | Toolsets+approvals are a different architecture. Escalation-as-contact does not exist. | AUD-05 (partial wrap) plus scratch for the Framework itself; AUD-06 escalation class; AUD-08 audit trail |
| Truth Ownership / Speech Authority | Structured facts owned separately from phrasing; fidelity check before speak | Single-pass generator; no formatter; no number/name/date check; `verify_on_stop` is coding-only. Cannot be “turned on” in Hermes config. | AUD-13, AUD-14, AUD-15 |

---

## Section 5 — Open questions for WINH00

Do not resolve these here.

1. **Client-side response arbitration.** Phase 2: Hermes does **not** enforce single-authority speech internally (AUD-01, AUD-04). Does the Windows client need its own arbitration layer (drop `review.summary`, ignore child-sid completes, suppress heartbeat as Zola-speech, only paint `message.complete` from user-initiated turns)? Or is “talk to Surface 3 only and live with Hermes’s extra events” acceptable for v1?

2. **§13 as a Zola-side layer regardless.** Phase 3 found a danger-command overlay, not a Trust/Permission Framework (AUD-05–08). Same shape as WINH04/05 open questions (compatibility projection vs Zola owns assembly): should Zola-Windows always own the permission document in front of Hermes, even if Hermes `approvals.mode` stays in the stack for terminal danger?

3. **Weighting vs prior “who’s in charge” findings.** `WINH04-AUD-02` (second memory write authority), `WINH06-AUD-07/08/23` (background-review skill/memory writes), `WINH03-AUD-05/08` (disconnect fail-open). This phase adds: the same review fork **speaks** (`review.summary`, AUD-02); orphaned-turn **output routing** is drop/replay/reattach (AUD-11), not a restatement of fail-open; there is still no core (AUD-04). Are these **additive** (separate problems in the same “who’s in charge” area) or does speech+routing raise the priority of disabling/gating the review fork for the Windows track beyond the skill-write risk already recorded?

4. **Truth/speech separation.** Hermes has no structural split (AUD-13–15). Is that acceptable for the Windows track (treat model output as both fact and phrasing, maybe with client-side display of tool cards), or does Zola-Windows need a verification/formatting layer **regardless** of Hermes’s architecture?

**INFO (not scored):** `prompt.submit` `voice_context` / `surface: voice-live` (`methods_prompt.py` L582–588) is a voice-pipeline concern for WINH09. Master Plan §9/9a was not used as a scoring target.
