# Zola P9PRE Audit — Synthesis

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Prompt SHA-256:** `D5652874B9A17885174391A8E8331DDC1BBE0AE75C92065EB713C54978CF199A` (no developer comparison hash was supplied)

Diagnostic only. This document does not choose a host, a cadence, a store, or a delivery shape.

---

## 1. Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P9PRE-AUD-01 | [MATCH] | — | 01 | Exit after ready is detected and not restarted |
| P9PRE-AUD-02 | [GAP] | HIGH | 01 | No respawn, backoff, or "keeps failing" state |
| P9PRE-AUD-03 | [MATCH] | — | 01 | Unreachable disables new input; presence goes Dormant |
| P9PRE-AUD-04 | [RISK] | MEDIUM | 01 | Unreachable does not invalidate an open capture |
| P9PRE-AUD-05 | [MATCH] | — | 01 | Reviewed-draft authorization dies with serve |
| P9PRE-AUD-06 | [MATCH] | — | 01 | Interrupted-turn note fails the memory guard and the passphrase |
| P9PRE-AUD-07 | [GAP] | MEDIUM | 01 | Serve stderr is not persisted; WER LocalDumps is not configured for python.exe |
| P9PRE-AUD-08 | [GAP] | LOW | 01 | No distinct watcher-down signal |
| P9PRE-AUD-09 | [MATCH] | — | 03 | Gmail historyId / 404 contract matches Google's pages |
| P9PRE-AUD-10 | [GAP] | MEDIUM | 03 | No stored historyId and no history.list route |
| P9PRE-AUD-11 | [GAP] | MEDIUM | 03 | Calendar list parameters cannot be combined with syncToken |
| P9PRE-AUD-12 | [RISK] | MEDIUM | 03 | Gmail pull and Calendar webhooks are different products |
| P9PRE-AUD-13 | [MATCH] | — | 03 | One user's poll is not near the published quotas |
| P9PRE-AUD-14 | [GAP] | LOW | 03 | Pages do not say whether a Testing refresh token keeps the 7-day life after publish |
| P9PRE-AUD-15 | [MATCH] | — | 03 | invalid_grant becomes needs_reconnect, readable without a turn |
| P9PRE-AUD-16 | [RISK] | MEDIUM | 03 | Two refreshes can both POST; the lock covers the access-token cache |
| P9PRE-AUD-17 | [MATCH] | — | 03 | google_http does not assume a turn and does not set taint |
| P9PRE-AUD-18 | [MATCH] | — | 02, 08 | register runs once per process until force=True |
| P9PRE-AUD-19 | [GAP] | MEDIUM | 02 | No serve-started or serve-stopping hook |
| P9PRE-AUD-20 | [RISK] | HIGH | 02 | no_agent cron skips the model and the Brian-only tool gate; Zola's serve does not tick cron |
| P9PRE-AUD-21 | [RISK] | HIGH | 02 | Heartbeat and /loop on Zola's serve are `platform == "tui"` with an empty parent |
| P9PRE-AUD-22 | [RISK] | HIGH | 04 | Brian-only is in the tool handlers, not in google_http or auth |
| P9PRE-AUD-23 | [GAP] | HIGH | 04 | Injected Workspace text does not taint the session |
| P9PRE-AUD-24 | [RISK] | HIGH | 04 | The never-list is enforced on the tool path only |
| P9PRE-AUD-25 | [GAP] | MEDIUM | 04 | Background ranking of mail is outside P8-D11 and P6-D07 as written |
| P9PRE-AUD-26 | [MATCH] | — | 05, 08 | PluginLlm.complete does not accept or forward tools |
| P9PRE-AUD-27 | [RISK] | MEDIUM | 05 | Default ranking path has no aux concurrency cap and does not queue behind a live turn |
| P9PRE-AUD-28 | [MATCH] | — | 05 | Consolidation keeps pending rows when the model call fails |
| P9PRE-AUD-29 | [GAP] | MEDIUM | 05 | No parser refuses to treat ranking JSON as identifiers |
| P9PRE-AUD-30 | [MATCH] | — | 05 | The facade cannot call tools; delivery authority would be later code |
| P9PRE-AUD-31 | [GAP] | HIGH | 06 | No open-loop or watcher-queue table |
| P9PRE-AUD-32 | [RISK] | MEDIUM | 06 | Memory-store text is on the forget path; a workspace-only file is not |
| P9PRE-AUD-33 | [MATCH] | — | 06 | is_brian_turn says the turn is Brian's; it does not certify each argument |
| P9PRE-AUD-34 | [RISK] | MEDIUM | 06 | Every pre_llm_call context is concatenated |
| P9PRE-AUD-35 | [GAP] | MEDIUM | 06 | forget_memory deletes a fixed table list |
| P9PRE-AUD-36 | [GAP] | HIGH | 07 | A plugin cannot push an event the client will speak |
| P9PRE-AUD-37 | [RISK] | HIGH | 07 | A synthetic prompt on the TUI agent can pass P8-D02 and be stored as a user turn |
| P9PRE-AUD-38 | [RISK] | MEDIUM | 07 | Echo rejection uses the last accumulated reply, not every voice.tts text |
| P9PRE-AUD-39 | [GAP] | MEDIUM | 07 | The HUD has no watcher-health source |
| P9PRE-AUD-40 | [GAP] | HIGH | 07 | No component claims a queue row and checks live speech state together |
| P9PRE-AUD-41 | [RISK] | MEDIUM | 05 | json_schema is not enforced; jsonschema is absent from the venv |
| P9PRE-AUD-42 | [RISK] | HIGH | 06 | Injected context is stored in `api_content` and replayed on later turns |
| P9PRE-AUD-43 | [RISK] | MEDIUM | 02 | `zola_memory.register` runs per memory-enabled agent, including cron |
| P9PRE-AUD-44 | [RISK] | MEDIUM | 05 | `classify_items.py` scores mail with no tools and drops a bad parse as silence |
| P9PRE-AUD-45 | [RISK] | HIGH | 02 | A live turn can arm a heartbeat or /loop through `terminal`; P8 guards do not match |

Counts: 45 findings — 12 HIGH, 18 MEDIUM, 2 LOW, 13 MATCH.

---

## 2. Build-plan implications

**AUD-02.** A serve-hosted watcher stops when serve stops, and the client does not start it again. Supervision is a dependency of that host, not of a process the client supervises separately.

**AUD-04.** During the gap, an open capture is not invalidated and the Speaking flag is not cleared. A restart policy has to name what happens to that capture.

**AUD-07.** A crash after ready leaves no Hermes stderr file. WER local dumps are not configured for `python.exe`. Post-crash diagnosis stays on the Application event log (event 1000), which this audit counted through 2026-10-08.

**AUD-08, AUD-39.** "Watcher down" is not a signal. Backend-down is. A HUD line needs an observed poll time or error class, not a self-reported healthy bit.

**AUD-10, AUD-11.** Change detection needs new calls. `messages.list` today is not `history.list`. Calendar list always sends `timeMin`, `timeMax`, and `orderBy`, which Google's sync page says cannot ride with `syncToken`.

**AUD-12.** Gmail `users.watch` can land on a Pub/Sub pull subscription with no public endpoint. Calendar `events.watch` is an HTTPS webhook. Polling remains the catch-up path for both, because a watch notification is an id, not the change list.

**AUD-14.** Publishing's effect on an already issued Testing refresh token is not on Google's pages. `invalid_grant` already becomes `needs_reconnect`.

**AUD-16.** Two callers can refresh at once. The access-token lock does not wrap the token POST.

**AUD-45.** A live turn's tool list includes `terminal`, `cronjob`, and `file`, and not `execute_code`. The P8 self-mod and terminal-Google guards do not match `hermes cron`, a heartbeat write, or `jobs.json`. Heartbeat and /loop, once armed, fire as Brian-shaped turns (AUD-21). Cron jobs can be written and do not tick while `HERMES_DESKTOP` is unset. None are armed: 0 `heartbeat:` / `loop:` / `goal:` rows, no `jobs.json`. `gateway_heartbeats` (118 rows) is process liveness.

**AUD-21, AUD-43.** On this serve a heartbeat or /loop is `platform` `tui` with no parent, because the client removes `HERMES_DESKTOP`. `zola_memory.register` runs again for every memory-enabled agent, including a cron agent.

**AUD-27, AUD-44.** The default plugin LLM path has no concurrency cap. `call_llm` can take tools; the facade does not pass them. `classify_items.py` is an existing mail scorer on `task="monitor"` whose bad parse exits 0 and prints nothing.

**AUD-42.** Prefetch and `pre_llm_call` context are stamped into `api_content` and can be written to the session DB for replay. The chat transcript stays the user's words. Untainted mail in that sidecar would be resent on later turns.

**AUD-22, AUD-24.** Any background reader that calls `google_http` directly skips `P8-D02`. The carve-out, if one is made, is a revision of that decision. This audit does not write the revision.

**AUD-23, AUD-34.** Mail text injected through `pre_llm_call` is not tainted, and the host will inject every hook's `context`. `P8-D09` applies after `mark_tainted`.

**AUD-25, AUD-41.** A ranking call sends mailbox text to the model. `P8-D11` covers logs. `P6-D07` covers memory consolidation. Schema validation in the accessor is a no-op without `jsonschema`.

**AUD-27.** The aux semaphore does not include Brian's streaming turn.

**AUD-29, AUD-30.** The model cannot call tools on this facade. It can still name a thread id inside JSON. Delivery stays advisory only if code ignores those fields.

**AUD-31, AUD-32, AUD-35.** Loops and the queue have no table. Forget will not see a new table until the delete list includes it. H-4: WAL, `database is locked` when a writer holds `BEGIN IMMEDIATE`.

**AUD-36, AUD-37, AUD-38, AUD-40.** Unprompted speech has no plugin push. A synthetic turn can look like Brian. Echo matching is tied to the last reply accumulation. Nothing claims an item and checks lock, capture, playback, and draft in one place. `S70` still has no playback-completion signal.

---

## 3. Pre-work

Brian is publishing the OAuth client himself during this audit. The audit did not touch Google.

Re-consent after publishing is **not** established. Google's pages say Testing refresh tokens expire in seven days, and they do not say whether a token already issued under Testing keeps that expiry after the app is In production. `AUD-14`. Detection that already exists: `created_at` inside the DPAPI record at consent, and `invalid_grant` → `needs_reconnect` via `store_status`, without a turn. The live `token.dpapi` mtime did not change during this audit (`2026-10-07T22:58:24.2521851Z`).

Installs performed: none.  
`P2-D17` candidate, only if a later decision wants the accessor to enforce `json_schema`: `jsonschema` 4.26.0 is not importable in the Hermes venv. Wheel 90630 bytes. Runtime dependencies: `attrs>=22.2.0`, `jsonschema-specifications>=2023.03.6`, `referencing>=0.28.4`, `rpds-py>=0.25.0`. PyPI read 2026-10-09. Consolidation already has its own `validate_episodes` and does not require this package to fail closed.

---

## 4. Assumptions confirmed

AUD-01, AUD-03, AUD-05, AUD-06, AUD-09, AUD-13, AUD-15, AUD-17, AUD-18, AUD-26, AUD-28, AUD-30, AUD-33.

Exit after ready is visible and not restarted. Unreachable blocks new input. Reviewed-draft auth is process memory. The interrupted-turn note fails both Zola gates. Gmail's history contract and the quota headroom match the public pages. `needs_reconnect` is readable without a turn. `google_http` is turn-agnostic. Plugin load is once per process until force. The plugin LLM facade has no tools. Failed consolidation keeps the source rows. `is_brian_turn` is the reusable "this turn is Brian" check.

---

## 5. Open questions

### 5.1 Supervision

| Option | Evidence |
|--------|----------|
| Restart serve from the client after an unexpected exit | AUD-01, AUD-02. Token is minted by the parent (`DashboardSessionToken.Mint`). Port comes from the ready sentinel. Socket reconnect and `session.create` already exist. Resume of the previous session is `ResumeStoredAsync` on a session row, not the startup path. |
| Leave serve down until the window is reopened | Today's behavior after ready. Voice input is gated off (AUD-03). An open capture is not invalidated (AUD-04). |
| Cap restarts | No counter, backoff, or "keeps failing" state exists. |
| Interrupted-turn note | `tui_gateway/session_auto_continue.py` prefixes the note when `desktop.auto_continue.enabled` is true (profile default true, freshness 15 minutes, max attempts 2). Memory guard and passphrase already fail closed on it (AUD-06). |

### 5.2 Watcher host

| Host | Single instance | Crash / sleep | Token | Authority |
|------|-----------------|---------------|-------|-----------|
| Thread in `zola_workspace.register` or `spawn_task` | Once per process until force (H-1). A second process duplicates (H-2). | Dies with serve (AUD-02). Sleep is a timer gap (H-5). | In-process `auth.py` | Direct `google_http` skips `P8-D02` (AUD-22) |
| Thread in `zola_memory.register` | Once per memory-enabled agent, including cron (AUD-43) | Same process death. `shutdown` is per session and would not stop a thread started in `register`. | Same | Same, plus a cron agent would start it |
| Separate process the client supervises | Client would have to enforce it. Cron's `.tick.lock` is not automatically reused. | Independent of serve's crash. Dies when the client quits, if the client is the parent. | Same user, same DPAPI (`CryptProtectData` user scope) | Second caller unless Google stays inside `zola_workspace` |
| `no_agent` cron script | Tick lock `cron/.tick.lock` | Ticker is not running: Zola removes `HERMES_DESKTOP` | Script would open the store | Bypasses the tool gate (AUD-20) |
| Heartbeat or /loop | Session-scoped | Dies with serve | n/a | Brian-shaped turn (AUD-21). A live turn can arm one through `terminal`. Nothing is armed now (AUD-45). |
| Task Scheduler or a service | Task settings | Runs with the client closed | Fails for a different account (`CRYPTPROTECT_LOCAL_MACHINE` is the flag that would share across users; the store does not use it) | Runs with Brian absent (`P8-D02`) |

### 5.3 Change detection and cadence

| Option | Evidence |
|--------|----------|
| Gmail `history.list` + stored `historyId` | `[EXT]` 404 when too old; full sync; id often valid at least a week. Not implemented (AUD-10). `gmail.readonly` covers it. |
| Gmail `messages.list` with `newer_than` / `after` | Operator page was not fetched. **UNCONFIRMED** as a fallback. |
| Calendar `events.list` + `syncToken` | Cannot combine with `timeMin`, `timeMax`, `orderBy`, or `q`. Current list sends those (AUD-11). 410 means full sync. |
| Gmail Pub/Sub pull | Usable without a public endpoint. Watch renews at least every 7 days. Notification is email + historyId; history.list still required. Pub/Sub OAuth scope and free tier **UNCONFIRMED**. |
| Calendar `events.watch` | HTTPS webhook, publicly trusted certificate. No pull. Not usable without exposing an endpoint. |
| Poll every 1, 2, 5, or 15 minutes | One user is not near per-user or per-project quotas on the published numbers (AUD-13). Project quota bucket (pre- or post-2026-05-01) was not checked. |
| After sleep | H-5 flags a wall jump against monotonic time. `PBT_APMRESUMEAUTOMATIC` exists and the client does not subscribe. `S33`: this laptop did not deliver suspend. |
| Resync replay | Same Gmail message id and Calendar event id can appear again. Dedup needs those keys stored before "told" (audit 06 Q11). |

### 5.4 Background authority

| Question | Evidence |
|----------|----------|
| What a read may include | Metadata and snippet are what `shape_metadata` returns. Bodies are `extract_body` under the read-tool caps. Descriptions are omitted on the tool path (`P8-D10`) and present on a raw event resource. |
| Where the check lives | `read_common.authorize`, `gmail._gate`, calendar list gate. Not `google_http` or `auth` (AUD-22). |
| Never-list | Tools, memory writes, pending rows, `prompt.submit`, send, send-gate: stopped on the tool/hook path; not stopped on a direct module call (AUD-24). |
| Posture | `posture_ok` is manual mode and YOLO off. It does not know read versus write. Live mode is `manual`. Callers decide when to invoke it. |
| Decision a carve-out revises | `P8-D02` at least. `P8-D01` still holds if the caller stays inside `zola_workspace`. `P8-D09` does not follow automatically (AUD-23). |

### 5.5 Background ranking

| Topic | Evidence |
|-------|----------|
| Path | `ctx.llm` → `PluginLlm.complete_structured` → `call_llm` with `tools` defaulting to None (AUD-26, H-3). `call_llm` itself accepts tools. `classify_items.py` calls it with `task="monitor"` and no tools, and a bad parse exits 0 (AUD-44). |
| Timeout | Facade default 30s when `task` is unset. `auxiliary.monitor` default is 60s. Consolidation passes its own timeout. |
| Output | `json_schema` is sent with `strict: false`. A provider that rejects `response_format` is retried once without it. `jsonschema` is not installed (AUD-41). |
| Who can call it | The plugin that was handed the `PluginContext`. Consolidation already does, on a daemon thread, outside the user turn. `zola_workspace` does not call it today. |
| Model | Host active model when no override is allowed. Profile: `openai-codex` / `gpt-5.6-terra`. No `plugins.entries` block. |
| Failure | Invalid JSON → `(None, "text")`. Schema error raises only if `jsonschema` is installed (AUD-41). Consolidation returns false and keeps pending rows (AUD-28). |
| Logs | Facade INFO line is ids, model, purpose, token counts. `zola_memory.log` consolidation elapsed_ms: 37 successes, min 1555, median 4334, max 34601. |
| Privacy | AUD-25. |
| Concurrency | No semaphore on `task=None` (AUD-27). Live turn is a different client. |
| Advisory policies code can enforce from stored fields | Source ids, thread/event id equality, age, lock and quiet hours at delivery, frequency from a history of ids and times, a clamped label, suppression by id. A model field grants none of these unless a consumer copies it (AUD-29, AUD-30). |

### 5.6 Loop and queue storage

| Store | Authority | Forget | Second writer |
|-------|-----------|--------|---------------|
| New tables in `zola_memory` | Memory provider already owns the file (`P6-D01`) | Invisible until `forget.py` deletes them (AUD-35) | WAL; `database is locked` under a held write (H-4). `open_store` busy timeout measured 5000 ms |
| New file under `zola_workspace` | `P8-D01` | Not walked | Same SQLite facts if the same open settings are used. `taint.sqlite` is a separate file today |
| Other path | No owner | Not walked | — |

Entity link: an existing `entities.id` can be stored. Creating an entity from an email address would be a new write. `P6-D02`.

### 5.6a Lifecycle and atomicity

States with no table today: detected, stored, ranked or unranked, eligible, delivery claimed, speech started, speech completed, closed or expired.

Closest patterns: `pending_turns` for stored work; consolidation commit only after validation; `send_gate` claim in memory (dies on crash, fail closed for mail); no playback-completion signal (`S70`). Speech started, then a crash: Zola cannot know whether Brian heard it.

Cursor commit: one SQLite transaction only if cursor and items share a connection. Otherwise store items first, dedup on Gmail message id or Calendar event id + `updated`, then advance the cursor. Advancing first can drop the items from the next incremental page. A 404/410 resync can deliver the same ids again.

### 5.6b Retention minimums

| Class | Minimum | Encryption today | Deletion today |
|-------|---------|------------------|----------------|
| Cursors | token string plus mailbox or calendar id; no message body | none | not stored |
| Candidate metadata | ids, times, labels; subject and snippet only while ranking or speech needs them | plain SQLite | forget misses a new table |
| Calendar fields | title, start, attendees; descriptions stay off on the tool path | same | same |
| Ranking output | label or clamped score; a stored reason can repeat mail text | memory store is not DPAPI | episodes are forgotten; a reason in a new table is not |
| Open loops | source, subject, close condition, expiry (`S71`) | chosen file | chosen file |
| Delivery history | ids and timestamps | chosen file | none |
| Logs | route, counts, error class (`P8-D11`) | filesystem | no rotation fact this pass |
| Forgotten people | cascade is the fixed table list | — | AUD-35 |

### 5.7 Loop creation

| Option | Evidence |
|--------|----------|
| A tool that requires `is_brian_turn` | Same check as `read_common.authorize` (AUD-33). Arguments are still model-supplied. |
| Require a leading phrase the way memory saves do | `guards._save_request_suffix` allow-list. The interrupted-turn note fails it (AUD-06). |
| Create from mail text | No turn record. `is_brian_turn` is false. AUD-23 if that text is also injected. |

### 5.8 Surfacing inside a turn

| Mechanism | Evidence |
|-----------|----------|
| `prefetch` | Episode text, per call, user message. Owner today: `zola_memory`. |
| `system_prompt_block` | Returns empty. |
| `pre_llm_call` `context` | Appended to the user message's API copy. Every hook is concatenated (AUD-34). Stamped into `api_content` and replayed (AUD-42). Time context only on a user turn. |
| A tool round | `P8-D08` coarse-tool pattern. `S54`: about 8–12 seconds by voice. |
| Taint | Must be `mark_tainted` before the model sees the text. Not automatic (AUD-23). |
| Repeats | No "already told" table. `send_gate` state is in memory. `pending_turns` is durable. |

### 5.9 Unprompted delivery

| Shape | Who decides | What fails |
|-------|-------------|------------|
| (a) Client reads a queue and calls `voice.tts` with a fixed template | Client code. RPC returns `speaking` and starts a thread. No model. | Lock is not checked inside `voice.tts`. Echo haystack may still be the previous reply (AUD-38). Two calls can overlap (AUD-40). |
| (b) Synthetic model turn | The model phrases it. `_run_prompt_submit` on the TUI agent. | Can pass `P8-D02` and be stored as a user turn (AUD-37). |
| (c) Wait for Brian's next turn | Injection only. No speech until he talks. | Lock and quiet hours do not apply. `S54` tool cost is avoided if injection is used. |

Eligibility (ids, match, clamped label, not yet delivered) can live with the queue. Permission (lock, capture, playback, turn, clarify, draft, Text mode, quiet hours) lives in the client, except the draft and the turn, which live in serve. An item stays eligible while permission is false only if "told" is not set at ranking time or on a refused attempt. No such bit exists. `S70`: completed versus started is not observable from serve.

### 5.10 HUD and spoken status

| Source | Honest state |
|--------|----------------|
| Socket health poll | Backend reachable or not. Already shown as Dormant / "not reachable" (AUD-03). |
| `store_status` | `needs_reconnect` and store presence, without a turn (AUD-15). The client does not poll it. |
| A poll cursor's last success time | Not stored (AUD-10). |
| Watcher self-report | Not an observed source. `P3-D06`. |
| Spoken question | Same data as the HUD, through a tool or injection. Neither exists. |

HUD slots that exist: `StatusText`, the session label, presence mode, the mic line (including locked).

### 5.11 Dependencies

Facts about order, not a track plan:

- A watcher inside serve depends on a restart policy (AUD-02) if it must survive a crash.
- A watcher that calls Google depends on a readable token. Publishing is in progress. Re-consent is unconfirmed (AUD-14). `needs_reconnect` is the existing failure signal.
- Matching loops depends on a stored loop and on thread or event ids (AUD-31, AUD-10).
- Ranking depends on the accessor (AUD-26) and on items already stored. It does not depend on a live turn. It does send text to the model (AUD-25).
- Unprompted speech depends on a queue the client can read (AUD-36) or on a synthetic turn (AUD-37), and on a claim that sees client state (AUD-40).
- Injection into Brian's turn depends on taint (AUD-23) and on one hook owner (AUD-34).
- Forget coverage depends on where the rows live (AUD-35).

### Data path

```
Google (untrusted)
  |  history.list / events.list     [code: zola_workspace HTTP]
  |  gate today: tool handlers only [code: is_brian_turn]  --> direct HTTP skips this (AUD-22)
  v
watcher poll
  |  cursor + items                  [code: commit / dedup by message id or event id]
  v
queue (stored | unranked)
  |  ranking call, no tools          [model: label/score/reason only]
  |  malformed -> stay unranked      [code: consolidation pattern]
  v
policy                          [code: source, id match, age, clamp, suppression]
  |  model JSON is not an id
  v
eligible, not yet told
  |
  +-- Brian's turn
  |     prefetch or pre_llm_call context   [host concatenates; one owner is a decision]
  |     mark_tainted BEFORE the model sees it   [code; missing today AUD-23]
  |     api_content sidecar stores the injection for replay   [AUD-42]
  |     memory guard if a save is attempted     [code: P8-D09, only if tainted]
  |
  +-- unprompted
        permission: lock, capture, playback, turn, clarify, draft, mode, quiet hours
        [client + serve; no single gate today AUD-40]
        claim row, then voice.tts template [code]  or synthetic turn [model, AUD-37]
        speech started != heard             [S70]
        echo haystack                       [code: last reply, AUD-38]
```

Untrusted content enters at the Google response, again inside the ranking reason, and again if that reason is injected. Gates that are code: Brian-only on the tool path, dedup keys, clamped labels, lock and capture checks that exist for today's speech, taint plus the memory-save phrase, echo admission. The model decides ranking text only. It does not decide delivery unless a later consumer treats its JSON as authority.

---

## 6. LEAD outcomes

| LEAD | Outcome | Findings |
|------|---------|----------|
| 1 Where a background loop can live | Partly confirmed. Tool-plugin `register` is once per process until `force=True`, and again in a second process (H-1, H-2). `zola_memory.register` is once per memory-enabled agent, including cron (AUD-43). No serve start/stop hook. `PluginContext.emit` does not reach the client. | AUD-18, AUD-19, AUD-43 |
| 2 Cron is the wrong shape | Partly. `no_agent` runs a script with no model turn, so "every job is `run_conversation`" is false at this pin. Zola's serve does not tick cron, and a script would skip the tool gate. | AUD-20 |
| 3 Plugin model accessor | Confirmed for the tool-less facade and for use outside a user turn (consolidation's daemon thread). Another plugin uses its own `ctx.llm`. Fake transport was not injectable (H-3). | AUD-26, AUD-28, AUD-41 |
| 4 No supervision | Confirmed. | AUD-01, AUD-02 |
| 5 Gmail and Calendar feeds | Confirmed as separate facts. History 404 and sync-token 410 match the pages. Gmail pull needs no public endpoint. Calendar channels do. | AUD-09, AUD-11, AUD-12 |
| 6 No plugin push | Confirmed. The client drops unknown events. | AUD-36 |
| 7 One injection authority | Confirmed as a host fact: every `pre_llm_call` context is injected. `zola_memory` is the only owner today. Injected Workspace text is not tainted. | AUD-23, AUD-34 |
| 8 Publishing and re-consent | Partly. Seven-day Testing refresh tokens are on Google's page. The fate of an already issued token after publish is UNCONFIRMED. | AUD-14 |
| 9 Sleep and lock | Partly. WTS lock/unlock exists. `S33` stands. A timer can see a wall jump (H-5). Resume broadcast exists; the client does not subscribe. The vendor page does not mention Modern Standby. | H-5, audit 02 §8 |

Confirmed: 3, 4, 5, 6, 7 (five). Partly: 1, 2, 8, 9 (four). Refuted: none. LEAD-3's remaining limits are the fake transport (not injectable) and the absence of a cross-plugin bridge; the tool-less call outside a user turn is what the lead asked, and that is in the code.

---

## 7. `[EXT]` sources

Read 2026-10-09 unless noted. Full URL list is also in the progress doc.

Google: Gmail `history.list`, sync guide, push guide, `users.watch`, `messages.get`, list-messages, scopes, quota. Calendar `events.list`, sync, errors (410), push, quota. OAuth 2.0 (Testing refresh tokens; page updated 2026-05-26), production-readiness overview, restricted-scope verification, consent configuration. Support answers 15549945 (audience, 7-day test authorizations, 100-user cap) and 13464323 (personal-use exemption: under 100 users may continue without verification and click through the unverified warning). Drive `drive.readonly` is Restricted. Gmail `gmail.readonly` and `gmail.compose` are Restricted.

Microsoft: Collecting User-Mode Dumps. `RegisterPowerSettingNotification`. `PBT_APMRESUMEAUTOMATIC`. `CryptProtectData`.

PyPI: `https://pypi.org/pypi/jsonschema/json` for the candidate in section 3.

UNCONFIRMED after those reads: Gmail `newer_than` / `after` operators; whether a Testing refresh token converts on publish; Pub/Sub OAuth scope and free tier; whether a single-user local app must complete a restricted-scope security assessment; Calendar and Contacts scope class beyond the Gmail and Drive pages read; Modern Standby versus `PBT_APMRESUMEAUTOMATIC` on this laptop (local fact remains `S33`).
