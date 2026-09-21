# WINH07 Audit 02 — Single Authority Ownership: The Response Generation Path

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Master Architecture Plan §20 Centralized Authority Model; Core Architectural Principles — Single Authority Ownership. Agent Map Core Rule: “Agents prepare. The core decides. No agent writes to memory, speaks, executes tools, or holds routing authority.” Named Zola objects (`Response Governor`, `DurableWriteAuthority`) are examples of one owner per responsibility, not Hermes types.

Not scored here: §9/9a, §12. `voice_context` on `prompt.submit` (`tui_gateway/methods_prompt.py` L582–588) is **INFO for WINH09**. Memory-write ownership is `WINH04-AUD-02` (cite, not re-derived). Background-review *skill* writes are `WINH06-AUD-07/08/23` (cite existence; this phase asks whether the fork *speaks*).

---

## 1. Is there exactly one code path that turns agent reasoning into a user-facing response?

**Zola requires:** one authoritative owner of speech for a given session. Workers may prepare; they must not emit independently.

**Primary Surface 3 / dashboard path (already traced as `WINH03-AUD-03`):**

1. `tui_gateway/methods_prompt.py` `prompt.submit` L544–662 → `_run_after_agent_ready` → `tui_gateway/prompt_turn.py` `_run_prompt_submit` L796.
2. `_run_prompt_submit` L820 `_emit("message.start", sid)`, then the turn thread `_invoke_agent` → `_complete_turn_payload` → **L848 `_emit("message.complete", sid, payload)`**.
3. `_emit` is `tui_gateway/server.py` L623–624 → `write_json` L611–614, which writes the event frame to `_sessions[sid]["transport"]` (FanoutTransport if multiple live peers; else the bound transport).

That is the **main-turn** complete-emit. It is not the only user-facing emit that can fire for the same live session while that turn (or a post-turn fork) is alive.

**Additional emit / speech-adjacent paths on the same session:**

| Path | File | What the user can see |
|---|---|---|
| Background-review summary | `server.py` `_wire_session_agent` L1006; `contracts/events.py` L231 `review.summary` | Toast/HUD text, not `message.complete`, but client-visible |
| Agent notices | `agent_callbacks.py` L101–105 `_emit("notification.show", sid, …)` | Out-of-band toast (`events.py` L322) |
| Slow agent-build notice | `server.py` L937 `_emit("notification.show", …)` | Same channel |
| Heartbeat / `/loop` ticks | `session_notifications.py` `_maybe_fire_tui_heartbeat_tick` L198–223; loop L233+ | Claim idle session, then **the same** `_run_prompt_submit` — a full assistant `message.complete` the user did not type |
| Child-session mirror | `agent_callbacks.py` `_mirror_subagent_to_child` L77 `_emit("message.complete", csid, {"text": summary})` | A second sid (watch window) gets its own complete event while the parent turn is still running |
| Status lines | `session_notifications.py` `_notif_loop_status` L168–169 `status.update` | HUD text |

Heartbeat/loop reuse the main complete path (so there is not a *third* assembler), but they **are** a second *decision* to speak: a poller claims `session["running"]` and submits a prompt without a user `prompt.submit`. Subagent watch windows get a **second `message.complete`** on a different sid for the same parent turn.

There is no Hermes type named Response Governor, no `if not core.authorize_speech` gate, and no single function every emitter must call besides the transport helper `_emit` / `write_json`. `_emit` is a wire formatter, not an authority.

**Could more than one emit be active for the same session at once?** Yes: a live turn streams `message.delta` / later `message.complete` while `background_review` later fires `review.summary` on the same sid (`_wire_session_agent` L1006). A delegated child can `message.complete` on the child sid (`agent_callbacks.py` L77) while the parent is still in `_run_prompt_submit`. Two WS peers on one sid both receive the same events via `FanoutTransport` (`session_transports.py` L50–82) — that is fan-out of one stream, not two independent generators, but it is still not a named speech owner.

**Label:** `[PARTIAL]` `WINH07-AUD-01` (HIGH) — one *primary* complete path (`prompt_turn.py` L848, `WINH03-AUD-03`); not exactly one speech owner. Competing user-facing channels exist on the same process/session.

---

## 2. Can the background-review fork (or any other post-turn/parallel process) emit user-facing output?

**Cite, do not re-derive:** `WINH06-AUD-07` — `agent/background_review.py` is a post-turn daemon-thread fork (`enabled` default True) that can `skill_manage` / write memory. This phase asks only whether it *speaks*.

**It does emit to the user, through a path other than the main turn’s `message.complete`:**

- `agent/background_review.py` `_publish_review_summary` L1148–1153: `_safe_print("💾 Self-improvement review: …")` **and**, if set, `agent.background_review_callback(summary)`.
- Gateway wiring: `tui_gateway/server.py` `_wire_session_agent` L994–1007. Comment L996–997: the self-improvement summary “is emitted as `review.summary` (no print surface), honoring `display.memory_notifications`.” Callback: `lambda message, _sid=sid: _emit("review.summary", _sid, {"text": str(message)})`.
- Contract: `tui_gateway/contracts/events.py` L225–231 — `review.summary` / “Background review of the last turn finished.”
- Display default: `hermes_cli/config_defaults.py` `display.memory_notifications` L793–796 — default `"on"` (generic “💾 Memory updated”; `"verbose"` includes a preview; `"off"` still *runs* the review, only hides the notice).

That is a second, competing “speech-adjacent” owner: a worker notifies the user without going through the main turn’s response payload. It is not a second chat bubble by default, but it **is** user-facing output the Core Rule forbids workers from producing independently. Skill/memory writes remain `WINH06-AUD-07/08/23`; this finding is the notify path.

Other parallel speakers (not the review fork, same question): heartbeat/loop (`session_notifications.py` L198–223) produce a **real** `message.complete` via `_run_prompt_submit`. Child mirrors produce `message.complete` on another sid (`agent_callbacks.py` L77).

**Label:** `[RISK]` `WINH07-AUD-02` (HIGH) — background review is not file-only; `review.summary` + `_safe_print` reach the user. Not `[MATCH]`.

---

## 3. Concurrent surfaces against the same session — who wins?

**Inside one `tui_gateway` process (WINH02 Surfaces 2+3 share `dispatch`):**

- Session lookup: `server.py` `_sess_nowait` L1141–1157 — `_sessions.get(sid)`. Missing sid → RPC 4001, not a new session.
- One in-flight turn: `session["running"]`. `prompt.submit` L610–620 loops while `running`; `_handle_busy_submit` (`session_auto_continue.py` L240–245) applies `display.busy_input_mode` (default `"interrupt"`, `config_defaults.py` L767): interrupt/redirect, queue, or steer. Hosted-room internal submits get 4091 instead (`methods_prompt.py` L614–615).
- Heartbeat claims with `_notif_claim_turn` (`session_notifications.py` L145–150): if already running, the tick coalesces (L216). A racing user prompt wins idle; there is **no** named arbiter object, only the boolean.
- Two live clients: `_resume_reuse_live` (`methods_session.py` L677–679) **attaches alongside** existing streamers. `_attach_session_transport` (`session_transports.py` L50–82) builds `FanoutTransport` and `_warn_foreign_login`. Both peers see the same events. Concurrent `prompt.submit` from both still serialize on `running` + busy mode — **first to claim / interrupt policy**, not “surface A always wins.”

**Across WINH02’s six surfaces:** there is **no** shared arbitration. Surface 1 (`gateway/platforms/api_server.py`) mints/looks up its own ids (`_derive_chat_session_id` L1012–1017 hashes system prompt + first user message to `api-{digest}`). Surface 4 ACP (`acp_adapter/server.py` `prompt` L781–786) uses `SessionManager.get_session` in the ACP process. Surface 5 `mcp_serve.py` is a messaging-conversation bridge, not this turn loop. Surface 6 `gateway/platforms/webhook.py` renders into the messaging gateway. Those processes do not consult `_sessions` or `busy_input_mode`. Two surfaces live against “the same” logical chat is **undefined at the product layer** unless the operator has wired them to one `hermes serve` sid (dashboard `/api/ws` and Desktop do; API/ACP/webhook do not).

**Label:** `[PARTIAL]` `WINH07-AUD-03` (MEDIUM) — per-session `running` + `busy_input_mode` serialize *inside* the JSON-RPC gateway; no cross-surface authority; two peers fan out rather than elect a speaker.

---

## 4. Does Hermes have a “core,” or is the process the only aggregation point?

**Zola:** “the core decides.” Subsystems route output through one owner. A lack of code-level enforcement is a `[GAP]` even if nothing has gone wrong in practice.

**Hermes:** aggregation is the **process** plus dicts:

- `_sessions` (`server.py`) + `session["transport"]` + `write_json` / `_emit`.
- `handle_request` L797–821 looks up `_methods[method]` — a registry, not a governor.
- `_current_session_steer_authority` L824–837 is **steer/interrupt authenticity** (transport must be attached to the live record), not speech authorization.

Searched at this pin: no `ResponseGovernor`, no `SpeechAuthority`, no `DurableWriteAuthority` analog in the turn path (memory write authority remains `WINH04-AUD-02`). Nothing requires `review.summary`, `notification.show`, or child `message.complete` to pass a core. Workers call `_emit` directly.

**Label:** `[GAP]` `WINH07-AUD-04` (HIGH) against Single Authority Ownership / Agent Map Core Rule. There is no code-level core; co-location in one process is not enforcement.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH07-AUD-01 | PARTIAL | HIGH | `prompt_turn.py` L848; `server.py` L623–624, L1006; `agent_callbacks.py` L77 | Primary `message.complete` path exists; `review.summary`, notices, heartbeat turns, and child completes also speak |
| WINH07-AUD-02 | RISK | HIGH | `background_review.py` L1148–1153; `server.py` L1006 | WINH06 fork emits user-facing `review.summary` / `_safe_print`, not file-only |
| WINH07-AUD-03 | PARTIAL | MEDIUM | `methods_prompt.py` L610–620; `session_auto_continue.py` L240–245; `session_transports.py` L50–82 | Same-gateway concurrent submits serialize via `running`; no cross-surface arbiter |
| WINH07-AUD-04 | GAP | HIGH | searched `tui_gateway/`, `agent/` | No Response Governor / named core; `_emit` is a transport helper |
