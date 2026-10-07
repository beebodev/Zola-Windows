# Zola P8PRE Audit 02 — Approval Gate and Confirmed Send

**Date:** 2026-10-07  
**Pins:** hermes-agent `345cd2b0…` · zola-windows `7d2a1e71…`  
**Labels vs:** `A1`, `A3`, `P4-D01`, `P4-D02`, `P4-D07`, `P4-D12`, `P4-D27`, `P7-D01`–`P7-D05`, `P7-D09`, `S35`, `S57`

---

## 1. The function

`tools/approval.py` `request_tool_approval` L1015–1040. Arguments: `tool_name`, `reason`, optional `rule_key`, `approval_callback`. Card/wire fields via gateway: `command` (display target `<tool_name>`), `description` (= reason), `choices`, `allow_permanent`, `allow_session` (`tui_gateway/server.py` `_approval_request_payload` ~L667–679).

Returns: `{"approved": True/False, "message": ...}` plus deny/timeout metadata on human path. Uses `_run_approval_gate(..., fail_closed_when_no_human=True)`.

---

## 2. Approve without Brian

| Mechanism | Approves without human? | Evidence |
|-----------|-------------------------|----------|
| `approvals.mode: off` | **Yes** | `_run_approval_gate` L902–903; H-2 probe |
| `approvals.mode: manual` (live) | No | Live profile |
| `approvals.mode: smart` | **No for this function** (smart not passed) | L946–950 |
| `HERMES_YOLO_MODE` / `--yolo` (frozen at import) | **Yes** | `_YOLO_MODE_FROZEN` L45; H-2 re-probe with env set before import → approved |
| Session `/yolo` | **Yes** | `is_session_yolo_enabled` |
| Session/always allowlist of `pattern_key` | **Yes** | L905–906; Zola UI never sends `always`/`session` |
| `cron_mode` / `single_query_mode` / `unattended_mode: approve` | **Yes** | L916–944 |
| Same modes `deny` (live defaults) | Fail closed | Live effective config |
| `delegation.subagent_auto_approve: true` | **Yes** | `delegate_tool_config.py` L50–58 |

**[RISK]** Any path that sets `mode: off` or YOLO auto-approves a future send tool.

---

## 3. No client attached

With live defaults (`*_mode: deny`) and `fail_closed_when_no_human=True`: **fail closed** (`_blocked`). Background review callback auto-denies (`background_review.py` L988–992). Subagent default deny. H-2 confirmed: manual/smart + no interactive → `approved: false`.

---

## 4. The card

Client `ServerRequestBroker` `ApprovalView`: `Command`, `Description`, `Replayed` only (`ServerRequestBroker.cs` ~L117–122). Renders heading “Approval needed”, wrapped description + monospace command, **Approve once / Deny** (`MainWindow.xaml.cs` ~L1502–1548). `MaxWidth` 380; no dedicated To/Cc/Subject/body fields — those would have to be stuffed into `description`/`command`. Panel opens via `EnsureConversationOpen`.

`server-requests.log` (P4-D12): logs choice (`once`/`deny`) length/event metadata — **not** command or email body (`WriteLogCore` ~L769–776).

---

## 5. `A1` two steps (three “draft” meanings)

| Shape | Content confirm | Send confirm | Binding |
|-------|-----------------|--------------|---------|
| Composed text in chat + gated send tool | She reads back | `request_tool_approval` | Weak — model can change args between turns |
| Gmail Draft object + send-by-ID | “It’s in Drafts” / show draft | Gated `drafts.send` | Stronger if send tool re-fetches draft and hashes content (API exists; **not in code today**) |
| Single card showing exact To/Subject/body | Combined in description | Approve once | Binds to that request_id only; no content hash |

### 5a. Draft authority

`[EXT]` Gmail Draft resource has immutable `id` + `message` (`users.drafts`, read 2026-10-07). Methods: create/update/delete/get/list/send. A Draft is stored in the user’s mailbox with the DRAFT label — syncs to other Gmail clients; **not transmitted to recipients until send**. Saving a Draft is an external side effect on Brian’s mailbox (visible on his devices) but not a send under `A1`’s “transmitted to another person” reading. Hostile use of an ungated draft tool: fill Drafts folder; stage a message for a later “send it”. Whether draft create/update needs a gate is a decision (synthesis 5.4a).

**LEAD-11:** API supports Draft-by-ID send; **unimplemented** in Hermes/Zola code.

---

## 6. Voice mode today (`P4-D07`)

`OnApprovalOpened` (~L1184–1214): build card, `NoteTurnApproval()` (timing only — `VoiceController.cs` ~L3418–3424), `EnsureConversationOpen()`. **No TTS.** Buttons disabled when `VoiceGated`. Approvals remain typed/clicked only.

---

## 7. Existing outbound sends

`send_message` is **not** registered as a model tool (`tools/send_message_tool.py` L22–24). Live profile has no messaging gateway platforms configured. **A1 baseline:** no agent-reachable outbound send on the desktop path today.

---

## 8. Bypass measured (H-3, expanded F6)

| Command shape | Flagged? | Matched pattern |
|---------------|----------|-----------------|
| `python -c` … Gmail POST | **Yes** | `script execution via -e/-c flag` |
| `curl` POST gmail.googleapis.com | **No** | — |
| `Invoke-RestMethod` Gmail | **No** | — |
| Workspace `google_api.py gmail send` via python | **No** | — |
| `python -c` + win32crypt | **Yes** | `-e/-c` flag |
| `type …\google_token.json` | **No** | — |
| `Remove-Item -Force` (control) | **Yes** | PowerShell destructive delete |
| `python <file>.py` (after file-write) | **No** | — |
| `powershell -File script.ps1` | **Yes** | `script execution via -e/-c flag` |
| `python -m …` | **No** | — |

**`execute_code`:** In the live toolset as `code_execution` (H-1 `_get_platform_tools` for `cli`). It does **not** pass through `detect_dangerous_command` on a shell string. It uses `check_execute_code_guard` (`tools/approval.py` L1148–1215). On gateway/ask surfaces the whole script is approval-gated once; if `not is_gateway and not is_ask`, the function **returns `_approved()`** (L1193–1194). After one gateway approval (or YOLO/`mode:off`), host Python inside the sandbox can call Google APIs without the terminal pattern detector.

**LEAD-3: Confirmed in substance** — the sanctioned send-tool card is not the only path; unflagged `curl` / `python file.py` / skill scripts, plus `execute_code` after its own gate, can use a token.

---

## 9–12. Spoken approval

### 9. Shapes

| Shape | Exists today | Who decides yes/no | Fail |
|-------|--------------|--------------------|------|
| **(a) Bound approval capture** | **No** — `CaptureKind` has Clarify, not Approval (`CaptureLifecycle.cs` L13–20). Clarify binding pattern exists (`P7-D05`). | Would be **client code** | Would fail closed on unclear (if built like clarify) |
| **(b) Plugin-checked confirming turn** | See §9b facts below | Can be **plugin code** if built | Fail closed if coded so |
| **(c) Clarify as confirmation** | Yes (`P7-D09`) | **Model** (answer → model only) | Open relative to code gate |
| **(d) Card** | Yes | **Client** (click) | Deny/timeout closed |

Wire for (a): existing `{choice: once|deny}` reusable. Summary text would need a field the client can speak (description/command today).

### 9b. Shape (b) — can a plugin decide in code? (F5)

1. **Hooks that see the user message**
   - **`pre_llm_call`** (`agent/turn_context.py` `_collect_pre_llm_call_context` L663–686) invokes hooks with: `session_id`, `task_id`, `turn_id`, `user_message` (= `original_user_message`), `conversation_history`, `is_first_turn`, `model`, **`platform`**, **`parent_session_id`**, `sender_id`. `zola_memory.time_context.handle_pre_llm_call` reads `platform` / `parent_session_id` (L264–267).
   - **`on_turn_start`** on the memory provider (`zola_memory/provider.py` L214–225) receives `(turn_number, message, **kwargs)` with `author_id` / `author_name` / `author_is_bot` from `turn_context.py` L774–777. The message string is the turn query.

2. **Can a tool handler reach what the hook saw?**  
   Standard tool `**kwargs` are only `task_id`, `session_id`, `user_task` (`model_tools.py` L811–817) — **not** `user_message` / `platform`. A plugin can **store** hook-seen facts keyed by `session_id` (and optionally `task_id` / `turn_id` from `pre_llm_call`) in process memory, then read them in the tool handler by `session_id`. That is plugin-owned state, not a Hermes-provided link. **AUD-03 refined:** handlers lack kwargs, but a plugin hook *can* record `platform` / `parent_session_id` / user text per session for later handlers.

3. **Voice vs typed**  
   Client `ChatSocket.SubmitAsync` sends only `session_id` + `text` (`ChatSocket.cs` L285–289). No voice/typed marker on `prompt.submit`. **Not distinguishable at this pin** in Hermes hooks.

4. **Can the model put text into that “user message”?**  
   Busy-input redirect appends to `original_user_message`: `User correction during the turn: {_redirect_text}` (`agent/turn_iteration_prep.py` L321–323). So the string seen by `pre_llm_call` / `on_turn_start` is **not exclusively** Brian’s original submit — mid-turn corrections can be merged in. It is still user-channel text, not free model-authored assistant content, but it is not a pure “Brian’s first utterance only” guarantee.

**Verdict for shape (b):** Yes — a plugin can decide affirmatives in code from hook-captured user text + `platform`/`parent_session_id`, without trusting send-tool args, **if** it implements that session store + grammar. Not built today. Voice vs typed: not distinguishable.

### 7b. Can the agent open its own gate? (F7)

| Mechanism | Agent-reachable? | Evidence |
|-----------|------------------|----------|
| Edit `config.yaml` → `approvals.mode: off` | **Yes**, via `terminal` / file tools (profile `config.yaml` not in `file_safety` hard-deny for Hermes home the way `.env` is). `_get_approval_mode` → `load_config_readonly()` (`approval_context.py` L217–236), cached on **mtime/size** (`config.py` ~L184–190, L1986+) — a write that bumps mtime is seen **without restart**. | RISK |
| Session `/yolo` | Via client `config.set` key `yolo` / slash (`methods_config_set.py` L264–276, L461). **Not** a model tool; agent cannot call JSON-RPC `config.set` / `slash.exec` unless some other path exposes them. Typing `/yolo` in chat is Brian, not the model. | No (as model tool) |
| `HERMES_YOLO_MODE` for running serve | Frozen at import (`approval.py` L45). Agent cannot change the parent serve process env. | No |
| Permanent allowlist / `always` | Zola client never sends `always`. Writing allowlist files via terminal is possible in principle (same-user). | Partial (file edit) |
| `delegation.subagent_auto_approve` | Config key — same as config.yaml edit if present under `delegation`. | Yes if config writable |
| Spawn subagent with auto-approve | Only if config already allows / agent edits config first. | Config-dependent |

### 10. Answer grammar (facts for decision)

Candidate yes: “send it”, “yes”, “go ahead”. No: “no”, “cancel”, “never mind”, “don’t send it”. Collisions: Hermes stop phrase default `("stop",)` — exact whole utterance only. Clarify skip/cancel words exist separately. Cases: silence / `no_speech` / timeout / “yes but change…” / off-topic → rule is a **decision**. H-6 (synthetic): punctuation (`Send it!`, `No!`) and mishears (`Council` for cancel, `Don't sand it`) break naive exact-match.

### 11. Her own voice / echo

`TranscriptAdmission` drops echo (`TranscriptAdmission.cs` ~L110–113); `IsEchoOfLastReply` end-anchored ≥3-word run. Clarify speak adds to echo haystack. **No approval capture today** — if (a) speaks a summary containing “send it” then opens capture, it must reuse RememberSpokenEcho discipline or that is a gap.

### 12. What she says / gate

How much of the email to speak is a **decision**. `VoiceGated` / asleep: admission Drop(gated); approval buttons disabled — fail closed for clicks. Composer lives in panel; open approval does **not** enable composer the way open clarify does (`UpdateChrome` ~L1773–1777) — typed approve in Voice while streaming is not the path.

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-07 | [MATCH] | — | `request_tool_approval` exists; plugin-callable; fail-closed without human (live defaults). |
| P8PRE-AUD-08 | [RISK] | HIGH | `mode: off` / YOLO / unattended `approve` / subagent_auto_approve can approve send without Brian. |
| P8PRE-AUD-09 | [MATCH] | — | Client card path matches `P4-D07` (once/deny, not voice). |
| P8PRE-AUD-10 | [RISK] | HIGH | Terminal/script bypass: `curl` / `python file.py` / skill unflagged; `execute_code` in live toolset (F6). |
| P8PRE-AUD-11 | [GAP] | HIGH | Spoken approval shape (a) not built; `P4-D07` stands; `S57` open. |
| P8PRE-AUD-12 | [GAP] | MEDIUM | No Draft-ID / content-hash binding in code (LEAD-11 unimplemented). |
| P8PRE-AUD-13 | [MATCH] | — | No agent-reachable `send_message` on live desktop path today. |
| P8PRE-AUD-14 | [RISK] | MEDIUM | Clarify-as-send-confirm is model-decided — hostile email can argue with the model. |
| P8PRE-AUD-41 | [RISK] | HIGH | Agent can set `approvals.mode: off` by editing live `config.yaml`; re-read on mtime (F7). |
| P8PRE-AUD-43 | [MATCH] | — | Shape (b) decidable in plugin code via hooks + session store; voice/typed not distinguishable (F5). |

## LEADs

| LEAD | Outcome |
|------|---------|
| LEAD-2 | **Confirmed** (AUD-07/08) |
| LEAD-3 | **Confirmed** in substance (AUD-10; F6) |
| LEAD-10 | **Partly** — (a) unwired (AUD-11); (b) feasible in plugin code (AUD-43) |
| LEAD-11 | **Partly** — API yes `[EXT]`, code no (AUD-12) |
