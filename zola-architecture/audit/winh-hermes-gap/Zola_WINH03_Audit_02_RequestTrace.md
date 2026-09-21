# WINH03 Audit 02 — JSON-RPC Request Trace

Pinned tag: `v2026.9.14`
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

One complete turn on Surface 3 (`WINH02-AUD-01`). Named functions only. This is the contract a Path A/B client must speak.

---

## Named-function chain

```
JsonRpcGatewayClient.request("prompt.submit")
  → tui_gateway.ws.handle_ws  (or stdio dispatcher)
  → methods_prompt._  (@method "prompt.submit")          # methods_prompt.py L544
  → _lock_in_submit_turn  (session["running"]=True)      # L511
  → Thread(_run_after_agent_ready)                       # L655–662
       → _wait_agent_for_prompt
       → _run_prompt_submit                              # prompt_turn.py L796
            → _admit_prompt_turn
            → _emit("message.start")
            → _prepare_turn_input  (scopes, _wire_callbacks)
            → _invoke_agent                              # prompt_turn.py L520
                 → agent.run_conversation                # conversation_loop.py L1573
                      → _run_conversation_turn
                           → perform_api_call            # turn_api_call.py L61
                                → provider chat.completions / stream
                                → stream_callback → _emit("message.delta")
                           → [if tool_calls]
                             run_tool_round              # turn_tool_round.py L45
                               → persist tool-call msgs to state.db
                               → AIAgent._execute_tool_calls  # run_agent.py L1273
                                    → _begin_tool_execution
                                         → tool_start_callback → _on_tool_start → tool.start
                                    → handle_function_call / invoke_tool
                                         → [if dangerous] approval queue → _emit_approval_request
                                              (agent thread blocks on queue)
                                    → tool_complete_callback → _on_tool_complete → tool.complete
                               → next perform_api_call (model sees tool results)
                           → finish_text_response / finalize_turn
            → _absorb_turn_result / _commit_turn_history
            → _complete_turn_payload
            → _emit("message.complete")                  # prompt_turn.py L848
            → _finish_turn; session["running"]=False
```

RPC ack is **not** the turn result. `prompt.submit` returns immediately `{"status": "streaming", ...}` (`methods_prompt.py` L662). Completion is the `message.complete` event. Desktop sets a 1_800_000 ms ack timeout for that reason (`WINH02-AUD-10` / `client.ts`).

---

## 1. What receives `prompt.submit` and what it hands off to

**Receiver:** `tui_gateway/methods_prompt.py` handler `_` registered `@method("prompt.submit")` L544.

It sanitizes text, claims an active-session slot (`_ensure_active_session_slot`), rebinds the current WebSocket transport, handles a busy session (`_handle_busy_submit`), then `_lock_in_submit_turn` (sets `running=True`, starts inflight snapshot).

**Handoff:** a **daemon thread** `threading.Thread(target=_run_after_agent_ready, ...)` L655–662, stored as `session["_run_thread"]` so `session.interrupt` can distinguish a live turn from a stuck flag.

`_run_after_agent_ready` L474 waits for deferred `AIAgent` build (`_wait_agent_for_prompt`), then `_run_prompt_submit`.

---

## 2. What actually invokes the model / provider

`prompt_turn._invoke_agent` L520–563 sets `stream_callback` and calls:

```python
st.result = agent.run_conversation(run_message, **st.run_kwargs)
```

`AIAgent.run_conversation` is `agent/conversation_loop.py::run_conversation` L1573, which runs `_run_conversation_turn`. Each model round uses `agent/turn_api_call.py::perform_api_call` L61 (streaming decision, `_model_request_active` bracket, LLM middleware). Provider kwargs are built in `agent/transports/chat_completions.py` (`_build_kwargs_from_profile` / `chat.completions.create` path — WINH01 repo map).

Token deltas: `_invoke_agent._stream` → `_emit("message.delta", sid, {"text": delta, ...})` (`prompt_turn.py` L523–531).

---

## 3. Tool call: model output → result back in the conversation

When the assistant message has `tool_calls`, the loop selects `run_tool_round` (`conversation_loop.py` L1549).

`agent/turn_tool_round.py::run_tool_round` L45:

1. `validate_tool_calls`
2. Stage assistant tool-call message; `append_message`
3. **Persist to `state.db` before side effects** (`agent._flush_messages_to_session_db`, L116–119). If persist fails, the turn **breaks without running tools** (durability invariant).
4. `agent._execute_tool_calls` (`run_agent.py` L1273) — sequential, concurrent, or segmented (`agent/tool_executor.py`).
5. Each call: `_begin_tool_execution` then `handle_function_call` (`model_tools.py` L858) / `invoke_tool` (`agent/agent_runtime_helpers.py`).
6. Tool JSON result is appended as a `role: "tool"` message on `messages`.
7. Loop continues → another `perform_api_call` with those tool messages.

**Dispatch function:** `AIAgent._execute_tool_calls` → `handle_function_call` / `invoke_tool`.
**Result-injection point:** tool role messages appended onto the in-memory `messages` list inside `_execute_tool_calls`, after `handle_function_call` returns; then the next `perform_api_call`.

---

## 4. Where `tool.start` / `tool.generating` / `tool.complete` emit vs execution

Wired in `tui_gateway/agent_callbacks.py` `_wire_callbacks` / callback dict L89–94:

| Event | Callback | Timing vs execution |
|---|---|---|
| `tool.generating` | `tool_gen_callback` → `_emit("tool.generating")` | When the model is **generating** a tool call (before execution). |
| `tool.start` | `tool_start_callback` → `_on_tool_start` (`tool_progress.py` L232–252) | **Immediately before** the tool body, in `_begin_tool_execution` (`tool_executor.py` L909–932). `tool.started` progress events are dropped as duplicates (`tool_progress.py` L294–295). |
| `tool.complete` | `tool_complete_callback` → `_on_tool_complete` (L255–286) | **After** `handle_function_call` returns, with `result` / `duration_s` / optional `inline_diff`. |

So: `tool.start` is before execution, `tool.complete` is after. There is no separate "during" start event; during-execution progress uses `tool_progress_callback` → `tool.output_risk` / other progress types (`tool_progress.py` L297+).

---

## 5. Where `approval` is inserted; what the agent does while waiting

Dangerous terminal (and similar) tools call `tools.approval` (`approval_prompt.py` / `approval_context.py`). On the TUI/Desktop gateway, `_emit_approval_request` (`tui_gateway/server.py` L709–732) sends a server→client **request** `approval` via `server_requests.send_async`.

The wait is **owned by the approval queue**, not by `send()`'s timeout. Comment L714–716: queue timeout, `/approve all`, coalescing. Default timeout `approvals.timeout` = **300 seconds** (`tools/approval_context.py` `_get_approval_timeout` L239–257). Unattended API-server sessions default **deny** (`_get_unattended_approval_mode` L280–284) — that is Surface 1, not this trace.

**While waiting:** the **turn thread blocks** on the approval queue. It does not continue other tools in that sequential slot. (A parallel tool batch could still run other calls; a flagged terminal call is a sequential barrier in the segment planner — `run_agent.py` L1276–1277.) The JSON-RPC dispatcher stays able to read `approval.respond` / `session.interrupt` because those are not the blocked turn thread (`server.py` L145–147).

If the client never implements a handler: the queue times out → treated as timeout/deny (not an infinite hang at the default 300s). See Phase 6.

---

## 6. What produces `message.complete` and what it contains

**Producer:** `prompt_turn._run_prompt_submit.run()` L848: `_emit("message.complete", sid, payload)` after `_complete_turn_payload` L634–651.

**Payload is not a completion-only signal.** Contract `tui_gateway/contracts/events.py` L164–184: "The turn ended: final text, usage and outcome." Fields from `_complete_turn_payload`:

- `text` — **full raw assistant text** (`raw` from `_turn_outcome`), not merely "done"
- `usage` — `_get_usage(agent)` (authoritative vs mid-turn `session.usage` ticks)
- `status` — `complete` / `error` / `interrupted` (`TurnStatus`)
- optional `reasoning`, `warning`, `billing`, `failure_reason`, `rendered`, error surface

Deltas were already streamed; the complete event **repeats the full text** plus terminal metadata. Goal/loop hooks run **after** this emit (L850–854).

**Finding:** `WINH03-AUD-02` (trace), `WINH03-AUD-03` (complete payload includes full text).

---

## Sidecar death mid-tool (Path A unknown)

If `hermes serve` is killed mid-tool:

- In-process `_sessions` dies.
- Tool-call assistant message was flushed to `state.db` **before** execution (`turn_tool_round.py` L116–119). A tool that already ran side effects may have done so after that flush.
- `session.resume` after restart is a **cold** rebuild (Phase 5), not a live replay of the killed turn thread.
- What the UI shows depends on whether Desktop still has streamed deltas plus resume hydration — **not verified by running the app**. Static: the durable store has the tool-call row if flush succeeded; the tool result row may be missing if the process died during `handle_function_call`.
