# P4-REQUEST Progress — Server-Request Handler and Cards

## Branch

- Branch: `p4-request`
- Base commit SHA (`main` HEAD at branch): `2b97390eb736d7501bbfa81a995ef959b138c6d2` (`docs: record P4-LOCK merge SHA`)
- Plan on `main`: `PHASE4_BUILD_PLAN.md` v1.1 — SHA-256 `d98b3e6c87457266c8c2d06fc57a771cb1c56977790198fa2020429a5216616e` (54,285 bytes; verified matched)
- Prompt version: 1.1 (2026-09-29)
- Hermes HEAD verified Phase 2: `345cd2b057a452236de401d3534b8502a7465e8d` (clean)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Broker and Wire Layer (`P4-D06`, `P4-D11`, `P4-D12`) | COMPLETE |
| 4 | Build: Cards and Composer (`P4-D07`, `P4-D08`, `P4-D09`) | COMPLETE |
| 5 | Clarify Timeout Profile Edit (`P4-D10`, `P4-D25`) | COMPLETE |
| 6 | Smoke Test | COMPLETE — B11 ⚠️ PARTIAL (2nd Send after complete; drop via Part C); B16 lock PASS, no `suspended=true`; approvals.mode manual kept |
| 7 | Closeout | IN PROGRESS |

## Closeout SHAs

- Implementation commit: `d21ff9f9ceeeb1fecb16c5603c6b0b9549f41ace` (`feat(P4-REQUEST): server-request broker, clarify and approval cards — P4-D06..D12`)
- Merge SHA on main: *(pending 7g)*
- Final main tip: *(pending 7i)*

## Guardrails summary

- **G-SCOPE:** Only `ServerRequestBroker.cs` (new), `ChatSocket.cs`, `MainWindow.xaml` / `.xaml.cs`, optional `ZolaTokens.xaml` (flag first), live `config.yaml` one line (Phase 5), `VOICE_CONFIG.md` (P4-D10), and this progress doc.
- **G-ARCH:** Build plan is truth; stop on conflict. Apply K12 amendments exactly; no other silent deviations.
- **G-PATTERN:** Read every relevant file in full before changing it. No partial reads or memory of prior phases.
- **G-NOCHANGE:** No `VoiceController`, `ZolaDisplayState`, `Presence/*`, process/session managers, `App.xaml(.cs)`, csproj, `SOUL.md`, other profile keys, or hermes-agent edits.
- **G-COMMENT:** One `// P4-REQUEST: [rationale] — P4-D0X` per logically distinct changed block.
- **G-STOP:** Stop after each phase; wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-LORE-SCOPE:** No lore file updates (`ROADMAP`, `DESIGN_DECISIONS`, `OPEN_QUESTIONS`, etc.), including closeout. `PHASE4_BUILD_PLAN.md` not edited. `VOICE_CONFIG.md` in scope for P4-D10 only.
- **G-NO-CROSS-SCOPE:** Android Zola, Ava, Hermes TUI/Desktop UI conventions, and P4PRE spikes are out of scope.
- **G-ONE-AUTHORITY:** Broker sole holder of open-request state and sole caller of `SendResponseAsync` / `SendErrorAsync`. No clarify answer via `prompt.submit`. Voice/gate and display authorities unchanged.
- **G-FAIL-CLOSED:** Uncertain id → do not send; unrenderable approval → Deny; unknown method → error decline; send failure → closed locally, no auto-retry.
- **G-CONST:** Every new string, timeout, JSON-RPC code and field name is a named constant.
- **G-DEPS:** No installs of any kind.
- **G-PRIVACY:** `server-requests.log` never contains answer text (length only); no sudo/secret/vault params beyond method name; approval choice value may be logged.

## Developer amendments (K12)

Recorded verbatim from the prompt (decided 2026-09-29, before this prompt):

1. **"Client restart with a clarify open → card re-appears" is tested in attach mode.** Because of K6, a spawn-mode restart kills Hermes and the question with it. The amended test:
   - the developer starts a dedicated `--isolated` serve for the zola profile outside the client (Phase 2 reports the exact command the attach path recognises);
   - launch the client (it attaches), force a clarify, and close the client;
   - relaunch within the time budget from K6, open Sessions, and resume the prior session;
   - the card re-appears (from `open_requests`), and answering it works.
   Additionally, a spawn-mode restart must leave **no** stale card and no stuck state (the question is expected to die with Hermes).

2. **"Session switch with a clarify open" stays impossible from the UI** (K7; switching remains locked while a turn runs). The P4-D11 park/re-show rule is still built exactly as specified (with the K10 reconciliation). It is exercised live by amended test 1 (the question re-shows when its session becomes current again), and by a source-level walkthrough in Part C. Do **not** unlock session switching during a turn.

## Discrepancies and flags

- See Phase 2 item 15. No BLOCKED STOP conditions tripped.
- **Decline test:** developer chose option **(a)** — DEBUG-only F-key synthetic `tour` inject. **Build in Phase 4** (not Phase 3).
- **Approval probe prompt (developer-approved text):** use literal path  
  `C:\Users\test\AppData\Local\Temp\zola-p4-approval-probe.txt` (replace any `%TEMP%` form). Developer will read the command on the card before approving.
- **server-requests.log:** dedicated `_logGate` separate from broker state lock (developer decision) so concurrent socket/UI lines are not lost to a swallowed IOException.
- **Part A attach serve:** must ship a paste-ready PowerShell block matching `HermesProcessManager` cwd + env (see Phase 3 notes / Phase 6 Part A).
- **K7 resumed-running gap:** client leaves `_streaming=false` after resuming a running turn. **Do not fix in this track.** Known gap for the Phase 4 lore closeout. In B12 the developer will not send anything else until her reply completes.
- Non-blocking: K12 session-switch amendment; K13 Voice→Track 3; ChatSocket ignore path replaced in Phase 3; `ZolaDisplayState` read-only this track.
- **Lore closeout flag (new decision):** keep live-profile `approvals.mode: manual` (Hermes merged default is `smart`). Record as a new DESIGN_DECISIONS entry at Phase 4 lore closeout — not written in this track (G-LORE-SCOPE). See developer decision 2026-09-30 below.

## Developer decisions (Phase 2 review, 2026-09-29)

1. Decline test: option (a). DEBUG-only (`#if DEBUG`) F-key hook following the existing pattern; inject a synthetic `tour` request (id `srq-debug-<hex>`, session_id = current) through the same ChatSocket request hand-off if a small internal DEBUG entry allows it, otherwise directly into `broker.OnRequest`. Tag it. **Build it in Phase 4.**
2. Approval probe prompt:  
   `In the terminal tool only, create an empty file at C:\Users\test\AppData\Local\Temp\zola-p4-approval-probe.txt, then delete it with a recursive force remove so I can test the approval card. Use that exact literal path. Do not touch any other path.`
3. `server-requests.log`: serialize all writes with a dedicated log lock (separate from the broker state lock).
4. Part A must include a paste-ready PowerShell block that starts the dedicated `--isolated` serve with the same working directory and environment (`PYTHONPATH` and any `HERMES_*` vars) that `HermesProcessManager` uses for spawn.
5. K7 resumed-running gap: do **not** fix in this track; record for lore closeout; B12 waits for reply complete.

## Developer decisions (2026-09-30, post-smoke)

1. **Keep `approvals.mode: manual`** on the live zola profile. Hermes default (merged) is `smart` (`hermes_cli/config_defaults.py` ~L1557). This is a **P4-D25 live-profile edit outside the original G-SCOPE**, developer-approved 2026-09-30. Backup: `config.yaml.bak-P4-REQUEST-approvals-manual-20260930-075913`. `VOICE_CONFIG.md` entry retained. Flag for lore closeout as a new decision (do not write lore in this track).

## Phase 2 understanding

### Preflight
- hermes-agent HEAD `345cd2b057a452236de401d3534b8502a7465e8d`; working tree clean.
- Live profile `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`: `agent:` has only `reasoning_effort: medium`; **no** `approvals:` block; **no** `clarify_timeout` / `clarify.timeout`.

### 1. Approval (STOP) — PASS
**Params** (`contracts/server_requests.py` L72–86 `ApprovalRequestParams`): `session_id`, `request_id`, `command` (""), `description` (""), `choices: list[ApprovalChoice]`, `allow_permanent`, `allow_session`, `smart_denied`, `tool_name`, `gateway_session_id` (alias), extras allowed.

**Choices enum** (L65–69): `once` | `session` | `always` | `deny`.

**Payload builder** (`server.py` `_approval_request_payload` L666–679): if `choices` absent → start `["once"]`; append `session` unless `smart_denied` or `allow_session is False`; append `always` unless permanent disallowed; always append `deny`. Command redacted.

**Result** (L89–91 `ApprovalResult`): `{choice: ApprovalChoice, all?: bool}`.

**Emit** (`server.py` L709–732): `send_async("approval",…)`; `on_result` → `choice = str(result.get("choice") or "deny")`; `_approval.resolve_gateway_approval(…, choice, resolve_all=bool(result.get("all")), request_id=…)`.

**once = single-use** (`approval.py` `_persist_choice` L349–355): `"once" persists nothing"` — only `session`/`always` enter allowlists. Coalesce path (`approval_gateway_wait.py` L102–104): follower that sees leader `once` returns `None` → fresh prompt. Desktop smoke pattern: Deny → no run; Approve once → runs once; third ask again.

**deny = hard halt** (`approval.py` L822–833): `choice is None or choice == "deny"` → `deny(…)` → BLOCKED message / `outcome="denied"`. CLI: L862–865 same. Doc L624: "deny is a hard halt".

**`all`**: `resolve_gateway_approval` L145–160 — `resolve_all=True` clears **entire** queue (`/approve all`). Client must **never** send `all` (K2 / P4-D07). Only `{"choice":"once"}` or `{"choice":"deny"}`.

**Missing choice** → treated as `"deny"` (`server.py` L726). **Unknown non-deny choice** (e.g. `"foo"`) would fall through to `grant(choice)` (L834) and approve without persisting — client builders must not emit unknowns.

**vs K2:** matches. Not BLOCKED.

### 2. Approval reachability (STOP / K14) — PASS (corrected 2026-09-30)
**Original Phase 2 write-up (incorrect):** Profile has no `approvals:` → claimed `_get_approval_mode()` default `"manual"` (`approval_context.py` L228–236 `.get("mode", "manual")`). That read only the live profile file and treated the code fallback as the effective default.

**Correction:** Hermes merges profile with `hermes_cli/config_defaults.py` (~L1543–1557): default `approvals.mode` is **`"smart"`**. With no profile `approvals:` block, `load_config_readonly()` still yields `mode: smart`, so `_get_approval_mode()` returns `"smart"` (B6: auxiliary LLM auto-approved). Code-path `"manual"` fallback only applies when the merged config omits `mode` entirely — not the shipped defaults case. `_load_approval_mode` (`server.py` L1716–1721) still routes through `_get_approval_mode`. No YOLO in profile; approvals can fire. Not BLOCKED (cards reachable under smart when guardian escalates; smoke forced `manual` for deterministic cards — see developer decision below).

### 3. Harmless approval trigger
**Prompt (developer-approved before Part B):**  
`In the terminal tool only, create an empty throwaway file at %TEMP%\zola-p4-approval-probe.txt then delete it with a recursive force remove so I can test the approval card. Do not touch any other path.`

**Expected command shape:** `rm -rf '%TEMP%/zola-p4-approval-probe.txt'` or `Remove-Item … -Recurse -Force` on that temp file only.

**Patterns:**
- `approval_detection.py` L202 `r'\brm\s+-[^\s]*r'` → `"recursive delete"`
- or L227 `r'\bremove-item\b[^\n;|&]*\s-(?:recurse|force)\b'` → `"PowerShell destructive delete (Remove-Item)"`

Desktop already uses `rm -rf /tmp/x` as a fixture (`approval.test.tsx` L195).

### 4. Decline test
No coding-toolset method besides clarify/approval is safely user-triggerable from Zola chat without desktop_ui (Audit 03 §5: tour/mcp.setup/preview.* not default).

**Options for developer:**
- **(a)** DEBUG F-key hook (existing Ctrl+Shift+F* pattern in `MainWindow.xaml.cs` L1147+) injects synthetic `method:"tour"` into the broker dispatch path; error response to unknown Hermes id is dropped (K3).
- **(b)** Source-level walkthrough of Decline → `-32601` without a live trigger.

### 5. Clarify shapes
- **Single:** request `{question, choices?, multi_select?}`; answer `{answer}` / skip `{answer:""}` — Audit 03 §1; contracts L39–55; `_clarify_block` `server.py` L1339–1342.
- **multi_select (K8):** `_parse_multi_select_response` `clarify_tool.py` L78–86 accepts JSON array or comma-split. **Client sends JSON-array string** as `answer` (e.g. `"[\"red\",\"blue\"]"`) — commas in labels.
- **Batch (K9):** wire `questions[{qid,question,choices,multi_select}]` (`server.py` L1331–1335); final `{answers:{qid:text}}` every qid; Skip/cancel-all `{}` (no answer/answers); replayed locks in `params.answers` (`server_requests.snapshot` L59–65). **P4-D08: no `clarify.lock`.**
- **Recommended:** `RECOMMENDED_LABEL = "(Recommended)"` L16; `mark_recommended` L35–41 first choice; `strip_recommended` L44–49 before `user_response`. Show as label; strip on send.

### 6. Reconnect / open_requests / K6
**resume fast path** (`methods_session.py` `_resume_reuse_live_locked` L684–698): `_live_session_payload` + `resumed`, optional hydrating overlay.

**Cold/deferred/eager** via `_resume_response` L700–717: `session_id`, `resumed`, `message_count`, `messages`, `info`, `inflight`, `running`, `session_key`, `started_at`, `status`, optional `auto_continue` / `hydrating`.

**activate** L940–952: `_ok(_live_session_payload(...))`.

**`_live_session_payload`** (`server.py` L2754–2792): always `info`, `message_count`, `messages`, `messages_omitted`, `running`, `turn_started_at`, `session_id`, `session_key`, `started_at`, `status`; **conditionally** `inflight`, `queued`, **`pending_approval`**, **`open_requests`** when truthy.

**`open_requests` = snapshot** (`server_requests.py` L59–65, L211–215): `{id, method, params}` with locked `answers` merged — same as original frame (+ locks).

**`pending_approval` ignored (K5):** queue view without `srq-*`; do not render.

**Smallest ChatSocket surface:** add typed optional `IReadOnlyList<OpenRequestEntry>? OpenRequests` on `RpcReply` (id/method/params only). Do **not** parse `pending_approval`. Raise/pass to broker from `OnSessionReady` without a general bag. Clone params out of `JsonDocument` before hand-off (K4).

**K6 spawn cmdline** (`HermesProcessManager.cs` L197–206, L280):  
`python -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0`  
Attach matcher (`HermesLaunchResolver.cs` L113–131): `serve` + `--isolated` + `127.0.0.1` + `-p/--profile zola`.  
`Shutdown` L95–116: tree-kill only if `OwnsProcess`; attach never killed.

**Orphan budget:** grace `_WS_ORPHAN_REAP_GRACE_S` default **20 s** (`server.py` L122–129); activity-stale **600 s** (L130–132). TUI clarify wait is `Event.wait` in `server_requests.send` (L114) — **no** periodic activity touch (unlike messaging `clarify_gateway.wait_for_response` L76–79). Practical relaunch budget: **resume within ~20 s** (cancels orphan reap). After grace, a quiet clarify-blocked turn may be interrupted once activity is stale (up to ~600 s idle). Prefer ≤20 s for amended test 1.

### 7. Session identity — PASS (not BLOCKED)
`ServerRequest.frame` L55–57 stamps `params.session_id = self.sid` (runtime sid of the session that registered the request). `ChatSocket` L64 holds the same runtime id after create/resume. Compute-host mirror (`compute_host_bridge.py` L105–111) keys the parent session by that `params.session_id`, so a live turn's request always carries the current runtime sid. Child `srq-*` ids stay distinct (server_requests L9–10). Parking by foreign session_id remains valid for non-current sessions only.

### 8. Threading (STOP) — design closes §12c — PASS
**Proposed broker concurrency** (implements prompt v1.1):

| State | Meaning |
|---|---|
| Open | Awaiting UI answer; may be Shown or Parked (session ≠ current) |
| Sending | Claimed; frame write in flight |
| Answered | Response sent (or accepted as settled) |
| Declined | Error response sent |
| Cancelled | `request.cancel` while Open |
| SendFailed | Write threw; closed locally |
| Tombstone | Id closed for process life; never reopen |

**Transitions (under one lock; events after release):**  
unknown+OnRequest(clarify\|approval, not tombstoned)→Open;  
unknown+OnRequest(other)→Decline path→Declined+tombstone;  
unknown+OnCancel→tombstone only (K10a);  
Open+Answer/Decline→Sending→Answered\|Declined\|SendFailed (+tombstone);  
Open+OnCancel→Cancelled (+tombstone);  
Sending\|Answered+OnCancel→log only (K3);  
LoadOpenRequests: atomic reconcile (dedupe, K10 park/withdrawn_while_away, K10a skip tombstones, batch pre-fill, receipt sequences oldest-first);  
second Answer on non-Open→drop+log.

**claim-then-send:** Answer/Decline move Open→Sending under lock, unlock, write, then Answered/SendFailed.  
**UI from state:** handlers re-read `GetState(id)` after `Dispatch`; render card only if still Open for current session.  
**Receipt sequence:** monotonic `long` at first know; `NewestOpenClarify` = max sequence among Open clarify for session.

Closes Audit 03 §12c rows by construction (id-keyed; cancel races tombstoned; foreign session parked not answered; double Send impossible). Not BLOCKED.

### 9. Composer P4-D09
- Disable: `UpdateChrome` L765 `canType = _sessionReady && !_streaming && !_unreachable && !_switchInFlight && !_historyPending`; `OnSendClick` L265; Enter → `OnSendClick` L694.
- Exception: enable composer **only** when `broker.HasOpenClarify(currentSessionId)`; Send → `broker.Answer(NewestOpenClarify…)` never `SubmitTurnAsync`; else byte-identical today.
- Placeholder: set `"Answer Zola's question…"` while open; restore `"Message"` on close (`OnSessionReady` L258 already sets Message).
- **K7 resumed-running:** resume path L901–914 sets `_streaming=false`, `_sessionReady=true` even if Hermes `running:true` / clarify still open. Composer would enable under today's rules once session ready; Cancel hidden (`_streaming` false L775–777); late `message.delta`/`complete` still handled. P4-D09 must enable composer from broker open-clarify even when `_streaming` true mid-turn, and also when resume left `_streaming` false with clarify still open (HasOpenClarify).

### 10. Cards
- Tokens: `ZolaPanelBorderStyle`, `ZolaBodyStyle`, `ZolaBubbleHeadingStyle`, `ZolaTextButtonStyle`, `ZolaAmber*`, spaces `ZolaSpace4/8`, `ZolaComposerStyle` for free text (`ZolaTokens.xaml`).
- Host: `Transcript` StackPanel `MainWindow.xaml` L238.
- Collapse records: "You answered: …", "You approved once: \<cmd\>", "You denied: \<cmd\>", "Skipped", cancelled notice.
- Auto-open: reuse `OnConversationClick` L1248–1267 / set `ConversationOverlay.Visibility=Visible`.
- `ClearTranscript` L990–1000 clears visual children; broker keeps parked entries; re-show from broker state on session current.

### 11. Gate
`VoiceGated` (`VoiceController.cs` L236). Approval buttons disabled while gated; re-eval on `StateChanged` → existing `Dispatch(ApplyVoiceChrome)` L133 (and `UpdateChrome` after). Click handlers re-check gate (prompt v1.1).

### 12. Logging P4-D12
**Pattern:** `VoiceController.WriteTimeline` L1550–1561 → `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` as `o-timestamp + " " + line + NL`; swallow IO errors. Same folder as `display-state.log`. **Reuse append pattern; no new abstraction.**

**Line format:** `{time:o} {event} id={srq} method={m} session_id={sid} text_or_len={…} reason={…}`  
Answer text never logged (length only); choice `once`/`deny` ok; sudo/secret/vault: method only.

**Events:** received, shown, parked, reshown, answered, declined, cancelled, dropped, send_failed, withdrawn_while_away, replayed, replay_ignored_closed, gated_click_refused, pending_approval_ignored.

### 13. Clarify timeout P4-D10
**Current agent block:**  
```yaml
agent:
  reasoning_effort: medium
```
**Propose (Phase 5, after developer approve):** `  clarify_timeout: 300` under `agent:`.

**Restart?** `get_clarify_timeout` → `load_config()` **per call** (`clarify_gateway.py` L272–282); `_clarify_timeout_seconds` L1315–1321 calls it each clarify. **No serve restart required** for the new value to apply on the next clarify.

### 14. Track 1 sleep carry-over
Confirmed: Part B and Part C will include the Track 1 S4 lock/sleep check (Modern Standby PARTIAL — require sign-in on wake / note if Suspending still absent).

### 15. Flags / conflicts
- No BLOCKED STOPs.
- Non-blocking: K7 UI session-switch exit criterion amended (K12); Voice clarify answer = Track 3 (K13); decline needs (a)/(b) — **developer chose (a), Phase 4**; ChatSocket ignore replaced in Phase 3; `ZolaDisplayState` read-only this track; optional `ZolaTokens` only if flagged.

## Phase 3 notes

### Broker (`ServerRequestBroker.cs`)
- One `_gate` over the request map; separate `_logGate` for `server-requests.log` (developer decision 3).
- States: Open / Sending / Answered / Declined / Cancelled / SendFailed; tombstone set for process life.
- `LoadOpenRequests` / `OnRequest` / `OnCancel`: compute under lock → raise after release.
- Claim-then-send for Answer/Decline; unknown methods → `-32601` immediately; unparseable approval → `{"choice":"deny"}`.
- Approval builders emit **only** `{"choice":"once"}` or `{"choice":"deny"}` (no `all` / `session` / `always`).
- Events: `ClarifyOpened`, `ApprovalOpened`, `RequestClosed`, `Notice` (Phase 3: Notice → `OnRouted`; cards deferred to Phase 4).

### ChatSocket
- String-id branch → `ServerRequestReceived` with cloned params.
- `request.cancel` event → `ServerRequestCancelled`.
- `SendResponseAsync` / `SendErrorAsync` (no `method` member).
- `RpcReply.OpenRequests` + `PendingApprovalPresent`; `LastOpenRequests` / `LastPendingApprovalPresent` for `SessionReady`.

### MainWindow (wiring only)
- One `new ServerRequestBroker(_chat)` at L119.
- `OnSessionReady`: `OnSessionChanged` → optional `NotePendingApprovalIgnored` → `LoadOpenRequests`.

### Done-criteria greps (2026-09-29)
- One `new ServerRequestBroker(` — `MainWindow.xaml.cs:119`
- `SendResponseAsync` / `SendErrorAsync` called only from `ServerRequestBroker` (defs on `ChatSocket`)
- No `prompt.submit` / `SubmitTurnAsync` in broker
- No `"all"` in approval result builders
- `pending_approval` never rendered (log-only ignore)
- Build: PASS (`dotnet build … -r win-x64`)

### Phase 3 review fixes (2026-09-29)
1. **Resume race:** `ChatSocket.Replacing` → `MarkSocketReplacing()` (`_currentSessionId=null`, `_replaceMark=_nextSequence`); reconcile withdraws only `ReceiptSequence <= _replaceMark`; `OnSessionChanged` re-raises `ClarifyOpened`/`ApprovalOpened` for Open entries of the new session (`reshown`).
2. **Approval fail-closed:** `TryBuildApprovalView` requires non-empty `request_id` and `command`.
3. **ClaimAndSendAsync:** send only when `_currentSessionId` is non-empty and equals `entry.SessionId` (else drop `no_current_session` / `foreign_session`).
4. **Phase 4 note:** after fix 1 the same id can get more than one opened event. UI keeps **one card per id** (id → card map); an opened event for an id already on screen is a no-op; still render from `GetState`.

### Attach-serve recipe (for Phase 6 Part A paste block)
Matches `HermesProcessManager.SpawnAsync` / `HermesLaunchResolver.TryResolve`:
- WorkingDirectory = hermes-agent root (sibling or `ZOLA_HERMES_ROOT`)
- Python = `ZOLA_HERMES_PYTHON` or `{root}\.venv\Scripts\python.exe` or PATH
- Args: `-m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0`
- Env: `HERMES_HOME=%LOCALAPPDATA%\hermes\profiles\zola`, `PYTHONPATH={root}`, `PYTHONUNBUFFERED=1`, mint `HERMES_DASHBOARD_SESSION_TOKEN`; remove `HERMES_DESKTOP` / `HERMES_WEB_DIST` / `HERMES_SERVE_HEADLESS`

## Phase 4 notes

### Cards (`MainWindow.xaml.cs`)
- Id → card map (`_requestCards`); duplicate `ClarifyOpened`/`ApprovalOpened` for an on-screen id is a no-op; render only when `GetState(id) == Open` and not `_historyPending`.
- Clarify (P4-D08): question, choice buttons with `(Recommended)` as a separate label (never sent), free-text + Send, Skip; `multi_select` checkboxes; batch = one row per `qid`, one Send / one Skip.
- Approval (P4-D07): command + description; **only** "Approve once" / "Deny"; both disabled while `VoiceGated` and re-checked in click handlers (`NoteGatedClickRefused` on refuse).
- Close → collapse to read-only record (`You answered:…` / `You approved once:…` / `You denied:…` / `Skipped` / cancelled / etc.); controls removed.
- Auto-opens conversation panel on card open; resume path re-shows via `OnSessionChanged` after history bubbles (ClearTranscript drops visuals).
- **FLAG:** no monospace token in `ZolaTokens.xaml`; approval command uses `Cascadia Mono` via named constant `CommandFontFamilyName` (not a new resource). No token file change.

### Composer (`P4-D09`)
- **Before:** `canType = _sessionReady && !_streaming && !_unreachable && !_switchInFlight && !_historyPending`
- **After:** `canType = _sessionReady && !_unreachable && !_switchInFlight && !_historyPending && (!_streaming || openClarify)` where `openClarify = _requests.HasOpenClarify(_chat.SessionId)` — additive only.
- Placeholder `"Answer Zola's question…"` while clarify open; `"Message"` otherwise.
- Send/Enter → `NewestOpenClarify` → `AnswerClarify` (or batch: fill first unanswered row; card Send submits). Never `SubmitTurnAsync` for clarify answers.
- Batch typed-Send rule: fill first unanswered row; report at stop (kept as specified).

### DEBUG
- Ctrl+Shift+F5: synthetic `tour` via `ChatSocket.DebugInjectServerRequest` (`srq-debug-<hex>`).
- Ctrl+Shift+F1 / F2: clarify (toggles single↔batch) / approval preview.
- Env `ZOLA_DEBUG_INJECT_CARDS=clarify|batch|approval|record`: one-shot inject after session ready (screenshot capture when hotkeys cannot reach WinUI).

### Screenshots (under `zola-architecture/lore/prompts/progress/`)
| File | Content |
|---|---|
| `P4-REQUEST_clarify_choices.png` | Clarify with choices + Recommended; composer placeholder |
| `P4-REQUEST_clarify_batch.png` | Batch card (city choices + theme checkboxes) |
| `P4-REQUEST_approval.png` | Approval: command + Approve once / Deny only (Hermes offered session/always in params; not rendered) |
| `P4-REQUEST_record.png` | Collapsed `You answered: Short`; placeholder restored to Message |

Gated-approval screenshot: skipped (could not force `VoiceGated` without lock/suspend in this capture pass).

### Done-criteria
- [x] Card variants use existing tokens (+ Cascadia Mono flag above)
- [x] `canType` additive only (quoted above)
- [x] Approval never shows session/always (screenshot + DEBUG inject params included those choices)
- [x] Build PASS (`dotnet build … -c Debug -r win-x64`)

## Phase 5 notes

### Proposal (2026-09-29) — approved; applied 2026-09-30
- **Current `agent:` block** (before apply):
  ```yaml
  agent:
    reasoning_effort: medium
  ```
- **Exact line added:**
  ```yaml
    clarify_timeout: 300
  ```
- **Serve restart:** not required (Phase 2 item 13).

### Apply (2026-09-30)
- Backup: `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml.bak-P4-REQUEST-20260930-072643`
- Live `agent:` after apply:
  ```yaml
  agent:
    reasoning_effort: medium
    clarify_timeout: 300
  ```
- Diff vs backup: exactly one added line (`clarify_timeout: 300`); no other profile key changed.
- `VOICE_CONFIG.md`: recorded key/value/date/`P4-D10`/backup name/developer-approved.
- Serve restart: not performed (not required).

## Smoke evidence tables (Phase 6)

### Part A (CURSOR-RUN) — 2026-09-30
- **Build:** PASS (`dotnet build … -c Debug -r win-x64`, 0 warnings / 0 errors).
- **hermes-agent:** clean; HEAD `345cd2b057a452236de401d3534b8502a7465e8d`.
- **One-authority searches:**
  - `new ServerRequestBroker(` → one hit (`MainWindow.xaml.cs:160`).
  - `SendResponseAsync` / `SendErrorAsync` call sites → only `ServerRequestBroker.cs` (defs on `ChatSocket`).
  - No `session.interrupt` / `voice.` / `wake.` in `ServerRequestBroker.cs`; track diff does not add those to MainWindow for this path.
  - Clarify/composer-answer path: `OnSendClick` routes open clarify to `AnswerClarify` / batch fill and returns before `SubmitTurnAsync`; card handlers call broker only.
  - Approval builders: only `ChoiceOnce` / `ChoiceDeny` — no `"all"` in result payloads.
  - `pending_approval`: presence flag → `NotePendingApprovalIgnored` log only; never rendered.
- **Constants:** new user-facing card/composer strings and JSON field/choice names are named constants (`PlaceholderAnswerClarify`, `LabelApproveOnce`, `ChoiceOnce`, etc.).
- **Status:** Part A PASS; Phase 6 COMPLETE (Parts A–C).

### Part B interactive (2026-09-30) — COMPLETE
| Step | Result | Notes |
|---|---|---|
| B1 | PASS | clarify city; shown≤1s; answered len=7 |
| B2 | PASS | choices; answered len=5 (Short) |
| B3 | PASS | Skip → `text_or_len=skip` |
| B4 | PASS | multi_select; answered len=16 |
| B5 | PASS | batch; answered len=33 |
| B6 | **FAIL** then **PASS** (retry) | First: smart auto-approve. After `approvals.mode: manual`: Deny blocked command. |
| B7 | PASS | Approve once (retry after PS error needed 2nd once); terminal completed; probe gone |
| B8 | PASS | New approval card; Deny; BLOCKED |
| B9 | PASS | Ctrl+Shift+F5 tour → `declined … not supported` (notice easy to miss) |
| B10 | PASS | Cancel → `cancelled … interrupted` |
| B11 | ⚠️ PARTIAL | Second Send landed **after** turn complete → correctly a new `prompt.submit`; broker drop path covered by Part C walkthrough. Developer-acknowledged. Timestamps below. |
| B12 | PASS | Attach; relaunch ~1.7s; `replayed`/`reshown`; answered len=4; clarify completed |
| B13 | PASS | Spawn kill; no post-relaunch reshown of dead clarify; no stale card |
| B14 | PASS | Plain Send → text turn complete; no card on no-tools retry (agent text refused tools) |
| B15 | PASS | Voice wake → time reply + TTS; no server-request cards |
| B16 | PASS | `gate fact: locked=true` 08:39:39 and 08:40:23; gate closed/opened; sign-in wake. `suspended=false` throughout (Modern Standby / no Suspending — same Track 1 PARTIAL pattern; B16 criterion asks for locked=true). |

Profile: `approvals.mode: manual` **kept** (developer 2026-09-30); backup `config.yaml.bak-P4-REQUEST-approvals-manual-20260930-075913`. See Phase 2 item 2 correction + post-smoke decision.

#### B11 timing (developer re-check 2026-09-30)

Session `c203da1b` / clarify `srq-de949f35e868` (favourite number):

| Event | Timestamp | Source |
|---|---|---|
| (a) Clarify answer | `2026-09-30T08:16:50.6729612-07:00` | `server-requests.log` `answered … text_or_len=1`; agent `tool clarify completed` `08:16:50,674` |
| (b) That turn complete | `2026-09-30 08:16:52,851` | `gui.log` / `agent.log` `tui turn finished … status=complete` (wire `message.complete`; string not logged verbatim) |
| (c) Second `prompt.submit` | `2026-09-30 08:16:56,610` | `gui.log` `tui prompt accepted … kind=user chars=5` (`again`); agent turn `08:16:56,900` |

**(c) came after (b)** (~3.8 s). Not a mid-stream submit. **B11 = ⚠️ PARTIAL** (test design: second Send after turn end → new prompt; broker `dropped` path = Part C walkthrough only). Developer-acknowledged.

### Part C (CURSOR-RUN) — 2026-09-30

**Privacy:** searched `server-requests.log` for Seattle, Portland, Short, Detailed, Quiet, Warm, Apple, Banana, Cherry, Mars, Earth, again, italian/Italian, sushi, Mexican → **0 hits**. Answered lines are length/choice only (`text_or_len=N|skip|once|deny`).

**Source walkthrough (K12.2):**
- **Park:** `OnSessionChanged` foreign Open → `EventParked` (`ServerRequestBroker.cs` ~L176–177); arrival for non-current → park `foreign_session` (~L394/L410). UI: `ClearTranscript` drops visuals.
- **Reconcile / re-show:** `ChatSocket.Replacing` → `MarkSocketReplacing` (~L134–141, `_replaceMark=_nextSequence`). `LoadOpenRequests` → `ReconcileOpenRequestsLocked` (~L439+): snapshots replayed/`reshown`; absent Open with `ReceiptSequence <= _replaceMark` → `withdrawn_while_away` (~L455–465).
- **Session resume re-show:** `OnSessionChanged` matching Open → `EventReshown` + `ClarifyOpened`/`ApprovalOpened` (~L158–171). Live B12: `replayed` + `shown` + `reshown … session_changed` for `srq-7ea7d16aeebf`.
- **Drop (B11):** `ClaimAndSendAsync` / cancel on non-Open → `EventDropped` `not_open` / `already_settled` (~L320, L428, L531). UI smoke did not hit `dropped` (second Send was post-complete new prompt); code path present — covers the deferred drop criterion.

**B16 note:** no `suspended=true` in this sleep cycle; lock/sign-in gate path verified.

## Exit-criteria table (closeout)

From `PHASE4_BUILD_PLAN.md` Track 2 Exit criteria. Verified 2026-09-30 (Phase 7a). Build: PASS (0 warnings / 0 errors).

| Criterion | Result | Evidence |
|---|---|---|
| Forced clarify (L6) Text → card ≤1 s; typed answer used | ✅ MET | B1: shown≤1s; answered len=7; clarify completed |
| Clarify with choices → buttons; click sends text without `(Recommended)` | ✅ MET | B2: answered len=5 (Short) |
| Skip → `{"answer":""}` | ✅ MET | B3: `text_or_len=skip` |
| Batch clarify → one card, two rows, one `answers` | ✅ MET | B5: answered len=33 |
| Approval: Deny not run; Approve once runs once; third asks again | ✅ MET | B6 Deny; B7 once; B8 new card + Deny (after `approvals.mode: manual`) |
| Unhandled method → error, notice, log | ✅ MET | B9: DEBUG F5 tour → `declined … not supported` |
| Cancel open clarify → `interrupted` closes card | ✅ MET | B10: `cancelled … interrupted` |
| Client restart with clarify open → card re-appears; answer works **(amended by developer 2026-09-29)** | ✅ MET | B12 attach: `replayed`/`reshown`; answered len=4. B13 spawn: no stale card |
| Second Send after answering → dropped, log line | ⚠️ PARTIAL | B11: 2nd Send at 08:16:56.610 **after** turn complete 08:16:52.851 → new prompt (test design). Broker `dropped` path: Part C walkthrough. Developer-acknowledged |
| Session switch with clarify open → park / re-show **(amended by developer 2026-09-29)** | ✅ MET | UI switch locked during turn (K7). Amended: B12 resume re-show + Part C park/reconcile/reshow walkthrough |
| `server-requests.log` complete; no answer text | ✅ MET | Events for B1–B13; privacy search 0 hits |
| Plain-text questions still via normal Send (AUD-33) | ✅ MET | B14: text turn complete; no card |
| Build passes | ✅ MET | `dotnet build … -c Debug -r win-x64` 0W/0E (7a re-run) |
| Smoke Part B (HUMAN-RUN) | ✅ MET | B1–B16 exercised; PARTIALs developer-acknowledged |

### Track-level checks

| Check | Result | Evidence |
|---|---|---|
| One authority (broker sole responder; no `prompt.submit` answer path) | ✅ | One `new ServerRequestBroker(`; `SendResponseAsync`/`SendErrorAsync` only from broker; composer open-clarify → `AnswerClarify` before `SubmitTurnAsync` |
| Approval results only `once` / `deny` | ✅ | `ChoiceOnce` / `ChoiceDeny` only in result payloads |
| `pending_approval` never rendered | ✅ | `NotePendingApprovalIgnored` log only |
| No answer text in `server-requests.log` | ✅ | Privacy search 0 hits |
| hermes-agent clean at `345cd2b0…` | ✅ | 7b: clean; HEAD `345cd2b057a452236de401d3534b8502a7465e8d` |
| G-NOCHANGE files untouched | ✅ | `git diff --stat main` (pre-commit): only `ChatSocket.cs`, `MainWindow.xaml.cs`, `VOICE_CONFIG.md` + new broker/progress/screenshots. No VoiceController / ZolaDisplayState / Presence / App / csproj / lore / plan |

### Final file list

**New:**
- `windows-client/Zola.Client/ServerRequestBroker.cs`
- `zola-architecture/lore/prompts/progress/P4-REQUEST_Progress.md`
- `zola-architecture/lore/prompts/progress/P4-REQUEST_approval.png`
- `zola-architecture/lore/prompts/progress/P4-REQUEST_clarify_batch.png`
- `zola-architecture/lore/prompts/progress/P4-REQUEST_clarify_choices.png`
- `zola-architecture/lore/prompts/progress/P4-REQUEST_record.png`

**Modified:**
- `windows-client/Zola.Client/ChatSocket.cs`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `zola-architecture/identity/VOICE_CONFIG.md`

**Live profile (not in repo):** `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` — `agent.clarify_timeout: 300` (backup `config.yaml.bak-P4-REQUEST-20260930-072643`); `approvals.mode: manual` kept (backup `config.yaml.bak-P4-REQUEST-approvals-manual-20260930-075913`).
