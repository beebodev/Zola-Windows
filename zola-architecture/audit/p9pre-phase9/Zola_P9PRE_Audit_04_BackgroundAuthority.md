# Zola P9PRE Audit 04 — Background Authority Facts

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Labels vs:** `P8-D01`, `P8-D02`, `P8-D09`, `P8-D11`, `P6-D07`, `A5`

This audit does not design the carve-out. It lists where today's checks live.

---

## 1. Where Brian-only is enforced

`turn_context.is_brian_turn` (`turn_context.py` L99–115) is true only for the current `turn_id`, platform `tui`, empty `parent_session_id`, and an unexpired in-memory record. No record means false.

Callers that refuse before any Google read:

| Location | What it checks |
|----------|----------------|
| `read_common.authorize` L109–124 | `is_brian_turn`; else `not_brian_turn` |
| `gmail._search_impl` / `_read_impl` L257, L337 | `authorize` |
| `gmail._gate` L526+ | draft/send path, same turn check (`REASON_NOT_BRIAN`) |
| `gcal` list path around L524 | `REASON_NOT_BRIAN` |

`google_http.request` and `auth.refresh_access_token` / `auth.authorization_header` do not call `is_brian_turn`. `gmail.shape_metadata` (L171) does not either; it only shapes a dict already fetched.

A watcher that calls `gmail._search_impl` still hits `authorize` and fails with no turn. A watcher that calls `auth.authorization_header` and `google_http.request` does not. Both call sites are inside the `zola_workspace` package. `P8-D01` says that package is the Workspace authority. The Brian-only rule is not on the HTTP function; it is on the tool entry. Bypassing the tool entry stays inside the package and skips `P8-D02`.

**P9PRE-AUD-22 [RISK] HIGH** — `P8-D02` is enforced in the tool handlers (`read_common.authorize`, `gmail._gate`, the calendar list gate), not in `google_http` or `auth`. Direct module calls are a second path. `A5`.

---

## 2. What a read would touch

Metadata + snippet, as `shape_metadata` already returns: message `id`, `threadId`, from, subject, date, label ids, snippet, attachment names/types/sizes (`gmail.py` L171–185). Fetching that requires `messages.get` (20 quota units) or whatever `messages.list` already returned (`id` and `threadId` only). Scope: `gmail.readonly` covers `history.list` and `messages.get` (audit 03). `gmail.metadata` would exclude bodies; it is not a granted scope today.

Bodies: `extract_body` (`gmail.py` L210+), used by the read tool, under `P8-D08` caps in the read path. A watcher that called the read impl would still need a Brian turn.

Calendar: selected calendars, no descriptions (`gcal.py` L65, L253, L283). Titles, times, and attendees are in the event resource the list call returns. `P8-D10` keeps descriptions out of the tool result; a raw `google_http` response would include them unless the watcher drops the field.

Framing: tool results go through `framing.py` on the tool path. A direct HTTP response is unframed bytes.

---

## 3. Taint

`taint.mark_tainted` runs in the tool path before content is returned (for example `gcal.py` L706–711). Injection that never calls a tool does not execute that line. `pre_llm_call` in `turn_context.py` L146–158 re-marks an already tainted session; it does not taint a clean session because Workspace text was injected.

The memory guard (`guards.evaluate_memory_taint`, L460+) blocks add/replace only when `taint.is_tainted_ids` is true, and then only accepts a leading save phrase. If the session was never marked, the guard returns None (L505–506) and the write proceeds.

**P9PRE-AUD-23 [GAP] HIGH** — Workspace text that enters a turn without a tool call is not tainted. `P8-D09` then does not apply. The injecting code would have to call `mark_tainted` before the model sees the text.

---

## 4. What the watcher must not do — what stops it today

| Action | In serve, if it calls tool handlers | In serve or another process, if it calls modules directly |
|--------|--------------------------------------|----------------------------------------------------------|
| Call a Workspace tool | `is_brian_turn` is false with no turn | not stopped |
| Write `MEMORY.md` / `USER.md` / the memory store | memory tools are a different plugin; no watcher exists to try | not stopped by `zola_workspace` |
| Create a pending turn or episode | consolidation reads pending rows the provider wrote | not stopped |
| `prompt.submit` / start a turn | no plugin API found that submits a prompt; heartbeat uses private `_run_prompt_submit` | a process with the session token could open `/api/ws`; nothing in the plugin forbids that |
| Send or modify mail | `_gate` requires a Brian turn and the send-gate authorization | `google_http` would perform whatever URL it is given |
| Trigger the send gate | `on_pre_llm_call` only authorizes a passphrase on a real turn (`turn_context.py` L133–144) | not reachable without that hook |

**P9PRE-AUD-24 [RISK] HIGH** — the "never" list is enforced only on the tool/hook path. A direct caller is not on that path. `P8-D02`.

---

## 5. Guards and a state file

`evaluate_self_mod` (`guards.py` L581–588) blocks `write_file`, `patch`, and `terminal` when the command text matches the plugin tree, the token store, `SOUL.md`, or identity files. It does not run unless a tool call hits `pre_tool_call`. A watcher writing its own SQLite file under the profile does not pass through that function. A new state file is not on the self-mod pattern list unless its path matches `STORE_PATH_RE` / `PLUGIN_TREE_RE`. A path outside the plugin tree and outside the token store does not trip the guard, and the guard would not see a non-tool write anyway.

---

## 6. Posture

`posture.posture_ok` (`posture.py` L54–80) is true only when `approvals.mode == manual` and both YOLO flags are off. Unreadable readers fail closed. The live profile sets `approvals.mode: manual`. The posture check is applied to write tools (Phase 8 send/read wiring). It reads Hermes approval state, not "is this a read". A read-only background caller is not passed through `posture_ok` today, because it is not a tool call. Whether it should be is a decision. The fact is: the function does not know about reads versus writes; callers decide when to invoke it.

---

## 7. Privacy

`P8-D11` constrains Workspace **logs** to route labels, counts, and error classes (`google_http._route_for_log`). It does not mention a background model call.

`P6-D07` is the memory-processing boundary: consolidation may send memory text to the configured model. It is about memory episodes, not Gmail.

A ranking call sends watcher content to the model with nobody present. Neither decision's text, as written, covers that send. The plugin LLM audit line logs plugin id, purpose, model, and token counts, not the prompt (`agent/plugin_llm.py` L530–543). The prompt still leaves the machine inside `call_llm`.

**P9PRE-AUD-25 [GAP] MEDIUM** — background ranking of mailbox text is not covered by `P8-D11` (logs) or `P6-D07` (memory). `P8-D09` covers tainted turns, which this path does not create on its own (AUD-23).
