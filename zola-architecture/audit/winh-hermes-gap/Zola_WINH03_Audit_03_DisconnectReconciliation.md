# WINH03 Audit 03 — Disconnect, Cancel, and Fail-Closed Reconciliation

Pinned tag: `v2026.9.14`
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Central question of WINH03. Restates `WINH02-AUD-12` with the actual grace mechanism. Zola lens: fail-closed when uncertain; one authority per responsibility.

Surface 1 (OpenAI SSE) reminder, unchanged: `api_server_openai_routes.py` L696–698 / L741–744 — `ConnectionResetError` / `BrokenPipeError` → `_abandon_agent_task(..., "SSE client disconnected")` **immediately**. No grace window.

---

## 1. What triggers the grace window, and how long it is

**Trigger:** last WebSocket for a session disconnects. `tui_gateway/ws.py` calls `_close_sessions_for_transport` (`session_lifecycle.py` L621–678).

Unless `session["close_on_disconnect"]` is true (then: immediate pop + teardown, L653–654), the session is parked on `_detached_ws_transport` (L666) and `_schedule_ws_orphan_reap(sid)` is armed (L673).

**First timer:** `_WS_ORPHAN_REAP_GRACE_S`, default **20.0 seconds**.

Resolved by `_resolve_ws_orphan_reap_grace` (`tui_gateway/server.py` L122–129):

- env `HERMES_TUI_WS_ORPHAN_REAP_GRACE_S` if set
- else `dashboard.ws_orphan_reap_grace_s` in config
- else `20.0`
- **`0` disables the reaper** (park forever) — `session_lifecycle.py` L539–540; `config_defaults.py` L949–951: "0 = park forever."

**After the first 20s, interrupt is not automatic for a healthy turn.** `_reap` L568–572:

```text
if not yet interrupt-requested AND _ws_orphan_turn_activity_is_fresh(session):
    defer; reschedule another grace (20s)
```

"Fresh" (`_ws_orphan_turn_activity_is_fresh` L507–529): `agent.get_activity_summary()["seconds_since_activity"] < _WS_ORPHAN_ACTIVITY_STALE_S`.

`_WS_ORPHAN_ACTIVITY_STALE_S` default **600.0 seconds** (`server.py` L130–132; env `HERMES_TUI_WS_ORPHAN_ACTIVITY_STALE_S` / `dashboard.ws_orphan_activity_stale_s`). Activity is stamped by API waits, stream tokens, and tool heartbeats (`_touch_activity`). `0` means "never fresh" → interrupt at first grace.

`config_defaults.py` L952–955 states the product intent in words: **"an active turn runs to completion."** That is the opposite of Surface 1.

If live async delegations exist, the same 20s timer is rescheduled (`L564–565`).

**Not a single fixed "interrupt after 20s."** It is:

1. 20s park (reconnect window)
2. then, while the turn is running **and** last activity &lt; 600s old: keep running detached, re-check every 20s
3. when activity is stale (or stale threshold is 0): interrupt, then poll

Exact wall-clock under packet loss / sleep is `[UNVERIFIED]` (would need a live WS drop). The constants and branch order are in the code.

---

## 2. What happens when the grace path expires

When activity is **not** fresh (or stale threshold is 0):

- `_interrupt_session_turn` runs (`L591–594`) — same function as `session.interrupt` (`L390–432`): `_turn_cancel_requested`, `request_hard_interrupt(agent)`, pending approvals `deny`.
- Then the timer reschedules at `_WS_ORPHAN_INTERRUPT_REAP_POLL_S` = **1.0s** (`server.py` L133) until the turn settles (`running` false) or `_WS_ORPHAN_INTERRUPT_REAP_MAX_POLLS` = **60** (`L140`) → force-pop + `_teardown_popped_session(..., end_reason="ws_orphan_reap")`.

So: after the *interrupt* decision, the turn is cancelled; it does not "run to completion regardless." But a **healthy** turn (tokens/tools within 10 minutes) **does** run to completion without a client — the 20s window keeps getting renewed.

If the session is already idle (`not running`) at first reap check: it is popped immediately (L566–567), no interrupt needed.

---

## 3. Client method/parameter for immediate interrupt-on-disconnect?

**No JSON-RPC connection option** named interrupt-on-disconnect was found. `JsonRpcGatewayClient` has `replay`, heartbeats, `onSocketClose` — not a server flag to skip grace.

**Existing nearby levers (not equivalent to Surface 1):**

| Lever | Where | What it actually does |
|---|---|---|
| `session.create` param `close_on_disconnect: true` | `methods_session.py` L337; contract `sessions.py` L123 | On WS drop, **reap the session immediately** (`session_lifecycle.py` L653–654). Does **not** call `_interrupt_session_turn`. Teardown joins `_run_thread` up to `_TURN_SETTLE_BEFORE_CLOSE_SECONDS` = 5s (`L356`), then `_finalize_session` + `agent.close()` (`run_agent.py` L918 — resource release, still not `request_hard_interrupt`). Used by dashboard Chat **sidecar** (`web/src/components/ChatSidebar.tsx` `sidecarSessionCreateParams` L94–99). Desktop main chats do **not** set this flag in `desktopSessionCreateParams`. |
| Server env/config `ws_orphan_activity_stale_s = 0` and `ws_orphan_reap_grace_s > 0` | `server.py` L129–132 | Interrupt after the first grace (20s by default, or a smaller configured grace). **Process-wide**, not per-session. Grace `0` **disables** reaping (worse for fail-closed). |
| `session.interrupt` RPC | `methods_session.py` L1995 | Explicit cancel of the live turn. Independent of disconnect. |

There is **no** per-session flag that means "when my socket dies, call `_interrupt_session_turn` immediately like SSE." `close_on_disconnect` is session destroy, not Surface-1 interrupt.

---

## 4. If a Zola client calls `session.interrupt` then closes

**Mostly yes, for the turn** — if the interrupt frame is processed.

`session.interrupt` → `_interrupt_session_turn` → `request_hard_interrupt` (same as Surface 1's stop / SSE abandon). After `running` becomes false, a subsequent disconnect parks an **idle** session; the 20s reaper then tears the record down without keeping a live agent.

**Races (static reading; `[UNVERIFIED]` without a live drop test):**

1. **Interrupt RPC unread:** if the TCP/WS close happens before the server reads the interrupt frame, the session follows the default park + 20s + 600s-fresh path. Fail-open.
2. **Interrupt settling fence:** `_reattach_refusal` returns 4009 while `_client_gone_interrupt_requested` is set (`L489–490`). A client that interrupts, drops, and immediately reconnects can be refused until the reaper finishes polling.
3. **`close_on_disconnect` vs interrupt:** close_on_disconnect teardown does not use `_interrupt_session_turn`. Combining "interrupt then close" with `close_on_disconnect` is two different teardown paths; order is a race (`[UNVERIFIED]`).
4. **Voice barge-in:** interrupt is synchronous *request* to the agent (`request_hard_interrupt`); whether a blocked syscall in a tool returns immediately is `[UNVERIFIED]`. The interrupt RPC itself is dispatched on the JSON-RPC read path, not the turn thread (`server.py` L145–147), so the client can send it during a turn.

---

## 5. WINH02-AUD-12 restated

**Default Surface 3 is fail-open for a live turn:** disconnect parks the session; a producing turn continues until activity is 600s stale, then interrupt. Surface 1 is fail-closed: SSE drop interrupts now.

**Is the tension resolvable with a client-side design choice?**

- **Partially, if Zola owns the client (and preferably the sidecar process):**
  - Always send `session.interrupt` before closing a live turn (Path A/B design rule). Approximates Surface 1 **when the frame is delivered**.
  - Optionally set sidecar env `HERMES_TUI_WS_ORPHAN_ACTIVITY_STALE_S=0` and a small positive `HERMES_TUI_WS_ORPHAN_REAP_GRACE_S` so *unintentional* drops also interrupt after grace. This is **spawn configuration**, not an RPC. Only available if Zola launches `hermes serve`.
  - `close_on_disconnect` is **not** a clean Surface-1 equivalent (reap without `_interrupt_session_turn`).
- **Not resolvable for a client that only drops the socket against a default `hermes serve`:** that client inherits fail-open. No connection option flips the default.

This is a **structural default of Surface 3**, plus optional client/process mitigations. It is not "already fail-closed if you wait 20 seconds."

**Fail-closed principle:** Surface 1 matches. Surface 3 default does not. Client interrupt-before-close is the only in-catalog way to *choose* fail-closed without changing server config; it still has an unread-frame race.

**Findings:** `WINH03-AUD-05`, `WINH03-AUD-06`, `WINH03-AUD-07`, `WINH03-AUD-08`
