# ZW Phase 1 Build Plan
## Native Windows Client Foundation — Scaffold, Identity, Sessions, Memory, Email, Confirmed Send
**Base branch:** main
**Pre-plan baseline SHA:** 64999cd61d9d8c33d2b25e3590ba0a04ddd09d4c (captured before this plan
document itself was committed — `main` will move ahead of this once
the plan lands; this is a baseline reference, not the plan's own
commit SHA)
**Audit:** none — greenfield build atop the pinned Hermes tag already
fully audited in WINH01–WINH12 (merged to `main`); no additional audit
required since the pinned Hermes tag is unchanging — only normal
per-track "files to read" grounding was needed, done below.
**Theme:** New-feature work, not remediation. Stands up the first
working slice of Zola-Windows: a native Windows client process that
can start/attach to a Hermes agent, carry Zola's own identity, track
sessions, extend memory for v1, send/read email via Gmail, and gate
outbound sends behind explicit user confirmation. SMS reading and the
Daily Brief pipeline are explicitly out of scope (see Defers table).
## Phase Overview
| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 | Client/process scaffold | New Windows client connects to `hermes serve`, renders chat over `/api/ws`/`/api/pty` | High |
| 2 | Identity extension | Zola's SOUL.md + identity wiring | Low |
| 3 | Session wrap | Client-side session resume/list against Hermes's `/api/sessions` HTTP API (`SessionDB`, not `SessionStore` — corrected) | Medium |
| 4 | Memory extension | Raise MEMORY.md/USER.md budgets + tagging convention | Low |
| 5 | Email (Gmail) | Deferred — see S16 | Deferred |
| 6 | Confirmed send | Deferred — see S16 | Deferred |
**Sequencing rule:** Track 1 must merge before any other track begins
— every other track needs a running client to build/test against, and
Track 1 is also where Zola's dedicated `HERMES_HOME` profile gets
established (see Track 1's new exit criterion) — Tracks 2, 3, 4 all
assume that profile exists, so none of them should start against a
shared/default Hermes install. Tracks 2, 3, and 4 are independent of
each other and may proceed in parallel once Track 1 is merged. Tracks
5 and 6 were descoped out of Phase 1 after Track 5's Phase 2 grounding
found no viable hard-gate path within the original config-only email
scope (see `S16`).
## Decisions Resolved in This Build Plan
- **P1-D01 — Client transport.** The native Windows client talks to
  `hermes serve` (`hermes_cli/main.py:2543` `cmd_dashboard()`, invoked
  headless via the `serve` subcommand at `hermes_cli/main.py:2955-2991`)
  over its existing HTTP/WebSocket API — `/api/ws` for turn streaming,
  `/api/pty` for PTY-backed chat (`hermes_cli/main.py:2578-2579`).
  Chosen over building a new dedicated socket/RPC server because this
  surface already exists, is exercised daily by Hermes's own web UI,
  and `apps/desktop/electron/api-transport.ts` +
  `gateway-ws-probe.ts` + `backend-child.ts` already prove the exact
  pattern (spawn/manage a local backend process, connect over HTTP/WS)
  that the Windows client mirrors natively instead of via Electron.
  Resolves `C1`/`C2` for the concrete transport mechanism.
- **P1-D02 — Approval channel.** Corrected from an earlier draft that
  described this as a second connection: the client's single `/api/ws`
  connection from `P1-D01` already carries approval traffic, because
  `/api/ws` **is** `tui_gateway`'s WebSocket handler
  (`hermes_cli/web_routers/chat_ws.py:561`
  `@router.websocket("/api/ws")`, which at line 565 imports
  `tui_gateway.ws.handle_ws`; `hermes_cli/web_server.py:174` imports
  `tui_gateway.server` at startup; `hermes_cli/main.py:2517-2519`
  documents "Desktop chat uses the in-process /api/ws gateway"). No
  second socket is opened — the client subscribes to
  `approval.pending`, calls `approval.respond`, `approval.received`
  (`tui_gateway/methods_prompt.py:1150-1212`) over the same connection
  used for chat, backed by the per-session pending-approval queue in
  `tools/approval.py` (`_gateway_queues` at line 118,
  `list_gateway_approvals` at 174, `resolve_gateway_approval` at 139).
  Chosen because this queue is already machine-readable (not
  terminal-only) and is the same gate that already governs
  shell/dangerous-command approval — reusing it for `A1`'s
  confirmed-send keeps one approval mechanism instead of two. Resolves
  `A1`'s "how" for a non-terminal client.
- **P1-D03 — Identity.** Zola's identity is written into `SOUL.md` at
  the Hermes-home root, loaded by `agent/prompt_builder.py:1452`
  `load_soul_md()` and assembled into the system prompt's stable tier
  by `agent/system_prompt.py:488` `_identity_parts()`. No code change
  — a content change to the seeded `SOUL.md`, using the existing
  auto-seed/upgrade-detection path in `hermes_cli/default_soul.py`
  rather than building a separate identity file or touching
  `personality.py`'s persona-overlay system (a separate,
  session-ephemeral axis). Resolves `C5`.
- **P1-D04 — Sessions.** Corrected from an earlier draft that named
  the wrong class: `gateway/session.py`'s `SessionStore` is NOT wired
  to any client-facing endpoint — it's an in-process routing class
  used by messaging-platform gateways (Slack/Telegram/etc.), not
  reachable over `/api/ws` or REST. The actual client-facing session
  API is `hermes_cli/web_routers/sessions.py`, backed by `SessionDB`
  (`hermes_state.py`) via `_open_session_db_for_profile`:
  `GET /api/sessions` (line 165), `GET /api/sessions/{id}` (476),
  `GET /api/sessions/stats` (457), plus write endpoints
  (`PATCH`/`DELETE`, lines 621/567/440). There is no explicit "create
  session" REST endpoint — a new session is created implicitly the
  first time the client opens `/api/ws` for it, not through a separate
  API call. The client lists/resumes through the `/api/sessions*`
  endpoints and creates a new session by opening a fresh `/api/ws`
  connection with no existing session id. Resolves `C6`.
- **P1-D05 — Memory.** `MemoryStore`'s (`tools/memory_tool_store.py`)
  `memory_char_limit`/`user_char_limit` constructor defaults
  (2200/1375) are raised via config, and a lightweight in-text tagging
  convention (`[project]`, `[person]`, `[car]`, etc.) is documented
  for Zola's own writes to MEMORY.md/USER.md entries — both
  config/prompt-level changes, no new engineering. Resolves `C4`/`S14`
  (v1 scope only; structured store deferred).
- **P1-D06 — Email.** Gmail is reached through the existing generic
  `plugins/platforms/email/` IMAP/SMTP adapter, configured with a
  Gmail App Password (`EMAIL_ADDRESS`, `EMAIL_PASSWORD`,
  `EMAIL_SMTP_HOST=smtp.gmail.com`, `EMAIL_IMAP_HOST=imap.gmail.com`)
  rather than a dedicated Gmail OAuth connector, which does not exist
  in the repo. Resolves the corrected `P3`; OAuth is deferred to `S15`.
## Track 1 — Client/Process Scaffold
**Problem:** Zola-Windows has no client yet — WINH02/WINH03
characterized Path B (native client + persistent Hermes process) only
at the audit level, without enumerating the concrete API surface a
client would call. This track is the foundation every other track
builds on.
**Files to read:**
- `hermes_cli/main.py:2543-2600, 2955-2991` — `cmd_dashboard()` /
  `serve` dispatch, confirms `hermes serve` = headless
  `web_server.start_server()`.
- `hermes_cli/web_server.py`, `hermes_cli/web_server_chat.py`,
  `hermes_cli/web_server_gateway.py`,
  `hermes_cli/web_routers/chat_ws.py` (the actual `/api/ws` route,
  line 561) — the HTTP/WS surface itself; read for the `/api/ws` and
  `/api/pty` message contracts.
- `apps/desktop/electron/api-transport.ts`, `gateway-ws-probe.ts`,
  `backend-health.ts`, `backend-child.ts`, `local-backend-lifecycle.ts`,
  `windows-hermes-path.ts`, `windows-remote-lifecycle.ts`,
  `windows-child-options.ts` — READ-ONLY reference: Hermes's own
  existing Windows-aware client (Electron), showing the exact
  spawn/health-check/connect pattern to mirror. Do not modify — this
  is a different app (`apps/desktop`) in the same repo.
**Changes:**
- New Windows client project (framework choice — WinUI 3 vs. WPF — is
  left to whoever picks up this track; no prior Zola-Windows client
  code exists to constrain it) that: (a) spawns/attaches to a
  `hermes serve` process the same way `backend-child.ts`/
  `local-backend-lifecycle.ts` do, launched against a **dedicated
  `HERMES_HOME` profile for Zola**, never the machine's default/shared
  Hermes profile (find and use Hermes's existing profile-selection
  mechanism — e.g. a `--home`/`HERMES_HOME` env override — rather than
  inventing one; confirm the exact flag/env var during this track's
  own grounding pass, not assumed here); (b) health-checks it the way
  `gateway-ws-probe.ts` does before connecting, binding only to
  `127.0.0.1`, not `0.0.0.0` (confirm `hermes serve`'s bind-address
  default/flag during this track); (c) opens `/api/ws` and renders
  streamed turns; (d) tags every new source file with
  `// P1-CLIENT: <rationale> — P1-D01`.
- No changes to `apps/desktop/` or any Hermes-side file in this track
  — read-only reference only.
**Exit criteria:**
- [ ] Zola's dedicated `HERMES_HOME` profile is established and used
      by every client launch — verify by confirming `SOUL.md`/
      `MEMORY.md`/session data land under that profile's directory,
      not a shared/default one. This blocks Track 1's merge: Tracks 2,
      3, and 4 all assume this profile already exists.
- [ ] Client binary starts a `hermes serve` process (or attaches to an
      already-running one) and reaches a connected state, mirroring
      `backend-health.ts`'s readiness check.
- [ ] Smoke test: launch the client, type "hello" in the chat surface,
      and see a streamed response render token-by-token from
      `/api/ws`. Exact pass signal: full response text appears with
      no manual refresh.
- [ ] A second message in the same session reflects context from the
      first (e.g. ask a follow-up that only makes sense with the prior
      turn in view) — confirms turn history round-trips through
      `/api/ws`, not just single-shot streaming.
- [ ] User can cancel an in-flight response before it finishes, and
      the client returns to a usable state afterward.
- [ ] Closing the client does not leave an orphaned `hermes serve`
      process running — either the client owns the process lifecycle
      and terminates it, or the client only ever attaches to a process
      it didn't spawn and never kills someone else's; whichever model
      is chosen, verify via Task Manager/`Get-Process` after closing.
- [ ] Client cleanly detects and surfaces a "backend unreachable"
      state if `hermes serve` isn't running (no silent hang).
- [ ] `hermes serve`'s bound address is confirmed localhost-only
      (`127.0.0.1`), not reachable from another device on the network
      — check now, before Track 5/6 give it access to email.
**Complexity:** High
**Primary Risk:** `/api/ws`'s exact message framing (event types,
turn-boundary markers) isn't nailed down from `apps/desktop`'s
TypeScript alone — a Windows-native client parsing the same wire
format from scratch risks silently mis-parsing turn boundaries (e.g.
truncating a streamed response) rather than failing loudly; the smoke
test's exact-text-match pass signal is designed to catch this.
## Track 2 — Identity Extension
**Problem:** `C5` locked "Zola has her own identity" with mechanism
TBD; grounding this session found the exact injection point.
**Files to read:**
- `SOUL.md` (repo root) — current seeded content, single-paragraph
  prose.
- `hermes_cli/default_soul.py` — `DEFAULT_SOUL_MD` (line 9),
  `is_legacy_template_soul()` (line 62).
- `agent/prompt_builder.py:1452` (`load_soul_md()`) and
  `agent/prompt_builder.py:130` (`DEFAULT_AGENT_IDENTITY` fallback).
- `agent/system_prompt.py:488-500, 617` (`_identity_parts()`,
  stable-tier assembly).
**Changes:**
- Write Zola's identity text into `zola-architecture/identity/SOUL.md`
  in the Zola-Windows repo (source of truth, under version control),
  and deploy that content into Zola's dedicated `HERMES_HOME`
  profile's `SOUL.md` (profile established in Track 1 — this track
  does not create the profile, it populates its `SOUL.md`). Keeping
  the canonical text in the repo means a fresh machine/reinstall
  reproduces Zola's identity from source rather than depending on
  whatever happens to be sitting in an existing profile directory.
  Exact wording is Brian's to write/approve, not prescribed here.
- No code change required — `load_soul_md()` already reads whatever's
  in `SOUL.md` at `{HERMES_HOME}`.
**Exit criteria:**
- [ ] `zola-architecture/identity/SOUL.md` exists in the repo and
      matches what's deployed to the live profile's `SOUL.md`.
- [ ] Live `SOUL.md` (in Zola's dedicated profile from Track 1)
      contains Zola's identity text, not the Hermes default template.
- [ ] `is_legacy_template_soul()` returns `False` against the new
      content (confirms it won't be silently overwritten by the
      upgrade-detection path).
- [ ] Smoke test: ask the running agent "who are you?" — exact pass
      signal: response reflects Zola's identity, not generic Hermes
      framing.
**Complexity:** Low
**Primary Risk:** Low, given Track 1's profile-isolation gate — the
prior risk here (editing a `SOUL.md` shared with another Hermes
install) is resolved upstream by Track 1's exit criteria, not by this
track.
## Track 3 — Session Wrap
**Problem:** `C6` locked "stick with Hermes's existing sessions
table"; needed the actual public API surface, not the raw DB layer.
**Corrected from an earlier draft** that pointed at `SessionStore`
(`gateway/session.py`) — verified that class has no client-facing
endpoint at all; it's an in-process routing class used by
messaging-platform gateways, not reachable from a Windows client
talking to `hermes serve` over HTTP/WS. The real client-facing surface
is `hermes_cli/web_routers/sessions.py`.
**Files to read:**
- `hermes_cli/web_routers/sessions.py` — the actual HTTP routes:
  `GET /api/sessions` (line 165), `GET /api/sessions/stats` (457),
  `GET /api/sessions/{session_id}` (476),
  `GET /api/sessions/{session_id}/latest-descendant` (492),
  `PATCH /api/sessions/{id}` (621), `DELETE /api/sessions/{id}` (567),
  `DELETE /api/sessions/empty` (440). No explicit "create session"
  endpoint exists — read this file to confirm how session creation is
  actually signaled (expected: implicitly, the first time `/api/ws`
  opens for a session id the server hasn't seen).
- `hermes_cli/web_server_sessions.py` — `_open_session_db_for_profile`
  and related helpers the routes above call into; confirms these
  routes are backed by `SessionDB` (`hermes_state.py`), not
  `gateway/session.py`'s `SessionStore`.
- `hermes_state_sessions.py:367-1467` — underlying SQLite row CRUD on
  `SessionDB` (`create_session`, `ensure_session`, `get_session`,
  `list_recent_sessions_bounded`, `list_sessions_rich`,
  `delete_session`) — read-only, for context; the client talks to the
  HTTP routes, not this layer directly.
- `hermes_state_schema.py` — not yet read; read for the actual
  `sessions` table column list before finalizing any UI that displays
  session metadata.
**Changes:**
- Client resumes/lists sessions via `GET /api/sessions` and
  `GET /api/sessions/{id}`; creates a new session by opening a fresh
  `/api/ws` connection with a new session id (client-generated or
  server-assigned — confirm which during this track's grounding pass),
  not through a separate "create" call. Tag new client code
  `// P1-SESSION: <rationale> — P1-D04`.
- No changes to `hermes_cli/web_routers/sessions.py`,
  `hermes_cli/web_server_sessions.py`, or `hermes_state_sessions.py`
  in this track — read/wrap the existing HTTP surface, don't modify
  it.
**Exit criteria:**
- [ ] Client can create a new session and resume a previously-created
      one (via `GET /api/sessions/{id}` + reopening `/api/ws` with
      that id) across a client restart.
- [ ] Session list UI shows at least session id and last-activity
      time, sourced from `GET /api/sessions`.
- [ ] Smoke test: start a conversation, close the client, reopen,
      resume the same session — exact pass signal: prior turns are
      visible in the resumed session.
**Complexity:** Medium
**Primary Risk:** The exact contract for "how a new session id gets
assigned and how the client learns it" isn't nailed down by this
Build Plan (no create endpoint exists, so it must happen through
`/api/ws`'s own handshake) — if the client generates its own id and
Hermes expects something specific (a UUID format, a particular
prefix), sessions could silently fail to resume rather than erroring;
confirm the exact handshake as the first thing this track does, before
writing any session-list UI against it.
## Track 4 — Memory Extension
**Problem:** `C4`/`S14` (corrected after reading
`tools/memory_tool_store.py`) scoped v1 memory work to two cheap
changes on the existing flat-file store.
**Files to read:**
- `tools/memory_tool_store.py` — `MemoryStore.__init__`
  (`memory_char_limit=2200, user_char_limit=1375`),
  `MEMORY_BLOCK_HEADERS`, `ENTRY_DELIMITER`.
- `tools/memory_tool.py` — the tool schema the agent calls to write
  entries (confirm exact `action`/`target` values match
  `agent/memory_provider.py`'s `on_memory_write` contract:
  `add`/`replace`/`remove`, `memory`/`user`).
- `agent/memory_provider.py:185-187` — `on_memory_write` contract.
**Changes:**
- Config change: raise `memory_char_limit`/`user_char_limit` for the
  Zola-Windows profile (exact new values are a product call — start
  with 2x defaults, 4400/2750, and tune from real usage per `S14`'s
  "revisit once usage data exists").
- Documentation-only: a short convention note (in
  `zola-architecture/lore/`) describing the `[tag]` prefix convention
  for entries, tagged `// P1-MEMORY: <rationale> — P1-D05` wherever
  it's enforced in code (if enforced only by system-prompt instruction
  rather than code, note that explicitly instead of a fake tag).
**Exit criteria:**
- [ ] Config confirms the raised budgets take effect (`MemoryStore`
      initialized with the new values, verifiable via a debug/status
      command).
- [ ] A memory entry written through normal conversation uses the
      `[tag]` convention (spot-check, not automated — this is a
      prompting convention, not enforced structurally in v1).
- [ ] No drift-protection failures (`MemoryStore`'s round-trip check)
      after the budget change.
- [ ] Restart-persistence test: write a memory entry through normal
      conversation → close the client → restart `hermes serve` → ask
      Zola to recall the information — exact pass signal: the recalled
      fact matches what was written, confirming persistence and
      retrieval end-to-end, not just that a file got written.
**Complexity:** Low
**Primary Risk:** Raising the char budget increases what's rendered
into every system prompt on every turn — a silent token-cost/latency
regression if raised too aggressively; the "start at 2x, tune from
data" approach in Changes is deliberately conservative for this
reason.
## Track 5 — Email (Gmail)
**DEFERRED from Phase 1** — see `OPEN_QUESTIONS.md` S16 for why and
what was learned. Folded into a future Google Workspace Integration
build alongside Calendar, Drive, and Contacts.
**Problem:** `P3` (corrected this build cycle) — Gmail via the
existing generic email platform adapter, app-password auth, OAuth
deferred to `S15`.
**Files to read:**
- `plugins/platforms/email/plugin.yaml` — required/optional config
  keys (`EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `EMAIL_SMTP_HOST`, optional
  `EMAIL_SMTP_PORT`, `EMAIL_IMAP_HOST`, `EMAIL_ALLOWED_USERS`,
  `EMAIL_HOME_ADDRESS`).
- `plugins/platforms/email/adapter.py` — IMAP poll / SMTP send
  implementation; read in full (docstring lines 1-3, error text at
  line 471) before configuring.
**Changes:**
- Config only: set `EMAIL_ADDRESS`/`EMAIL_PASSWORD` (Gmail App
  Password, requires 2FA enabled on the Google account — generated at
  Google Account → Security → App Passwords),
  `EMAIL_SMTP_HOST=smtp.gmail.com`, `EMAIL_IMAP_HOST=imap.gmail.com`,
  `EMAIL_ALLOWED_USERS` restricted to Brian's own address(es). No code
  change.
- **Hard gate, not a soft note:** the agent-facing tool/capability
  that actually invokes SMTP send is not registered/enabled for Zola
  until Track 6's approval gate is merged and verified. This track may
  land and be used for the read/poll side (inbox reading, summarizing)
  on its own; the send action is inert/absent until Track 6 exists,
  not merely "gated behind approval" in principle.
**Exit criteria:**
- [ ] Adapter successfully polls the Gmail inbox via IMAP (confirm via
      adapter logs or a debug command — exact command TBD by whoever
      picks up this track, not enumerated during this planning pass).
- [ ] Confirm the send-capable tool is not exposed to the agent yet if
      Track 6 hasn't merged (i.e. Zola can read/summarize email but
      has no way to actually send one at this point in the build).
- [ ] Smoke test: ask Zola to read the latest inbox email and
      summarize it — exact pass signal: summary matches an email
      actually in the inbox.
**Complexity:** Low
**Primary Risk:** Google may restrict or deprecate App Passwords for
some account types/policies outside Brian's control — if the account
configured here doesn't support App Passwords, this track's entire
mechanism is blocked and falls back to needing `S15`'s OAuth work
sooner than planned.
## Track 6 — Confirmed Send
**DEFERRED from Phase 1** — see `OPEN_QUESTIONS.md` S16 for why and
what was learned. Folded into a future Google Workspace Integration
build alongside Calendar, Drive, and Contacts.
**Problem:** `A1` ("Confirmed Send" — draft first, explicit
confirmation before actually sending) needed a concrete, non-terminal
mechanism since Zola-Windows's client is a GUI, not a CLI.
**Files to read:**
- `tools/approval.py:118` (`_gateway_queues`), `139`
  (`resolve_gateway_approval`), `174` (`list_gateway_approvals`),
  `191` (`ack_gateway_approval`), `1015-1040`
  (`request_tool_approval`), `881-950` (`_run_approval_gate`,
  including `fail_closed_when_no_human` at 886/934-941).
- `tui_gateway/methods_prompt.py:1150-1212` — `approval.pending`,
  `approval.respond`, `approval.received` JSON-RPC methods.
- `tools/approval_gateway_wait.py:1-70` — blocking-wait implementation
  the agent thread uses until a client resolves the entry.
- Unverified, needs a targeted read before finalizing wiring: an
  existing call site of `request_tool_approval()` from a real tool
  (e.g. a shell/dangerous-command path) to confirm the exact call
  pattern a new Gmail-send tool should copy.
**Changes:**
- Client polls/subscribes to `approval.pending` over the **same**
  `/api/ws` connection opened in Track 1 (corrected from an earlier
  draft describing a separate `tui_gateway` connection — verified
  `/api/ws` is `tui_gateway.ws.handle_ws`, see `P1-D02`); on a pending
  entry, shows the drafted content (e.g. the outgoing email) with
  Approve/Deny; calls `approval.respond` with the user's choice; calls
  `approval.received` to ack.
- The Gmail-send path from Track 5 must call `request_tool_approval()`
  before actually invoking SMTP send — exact call site to be added
  once the "unverified" call-site pattern noted above is confirmed,
  tagged `// P1-CONFIRM: <rationale> — P1-D02`.
- **Confirmed-send hardening (explicit requirements, not just "show a
  dialog"):**
  - The approval is bound to the exact, immutable message payload (to,
    subject, body, attachments) shown to the user. If any field
    changes after the approval request is issued, that approval is
    invalidated and a new one must be requested — Zola cannot silently
    revise a drafted email after it's been approved.
  - Deny-by-default: if the approval interface is unreachable or the
    client is disconnected when a send is attempted, the send does not
    proceed (this is `fail_closed_when_no_human`'s existing behavior —
    confirm it holds for this new call site, don't assume).
  - No automatic retry of a send that could result in a duplicate
    email going out.
  - No alternate SMTP call path in the codebase that bypasses
    `request_tool_approval()` for this tool — confirm there's exactly
    one code path that can trigger an actual send.
  - An unanswered approval times out and cancels rather than hanging
    or defaulting to approved (confirm `tools/approval.py`'s existing
    timeout behavior, referenced in Track 6's Files to read, applies
    here too).
  - Test both the normal chat-driven send path and any
    autonomous/scheduled path (e.g. a future cron-triggered email) that
    could reach the same adapter — every outbound send must go through
    this same enforcement point, not just the interactive one.
**Exit criteria:**
- [ ] Requesting Zola send an email produces a pending approval
      visible in the client, showing the exact to/subject/body that
      will be sent, before anything is sent.
- [ ] Approving sends the email exactly as shown; denying does not
      send it.
- [ ] Editing the drafted email after the approval request is shown
      invalidates that approval (new approval required, not a
      silent re-send of stale content).
- [ ] Smoke test: ask Zola to send a test email, deny it, confirm via
      Gmail's Sent folder that nothing was sent; repeat and approve,
      confirm it was sent — exact pass signal: Sent folder state
      matches the approve/deny choice exactly.
- [ ] Fail-closed check: if the client disconnects from the approval
      RPC surface mid-request, the send does not silently proceed
      (`fail_closed_when_no_human` behavior holds).
- [ ] Timeout check: leave a pending approval unanswered past its
      timeout — confirm it cancels rather than hangs or auto-approves.
- [ ] Code-path check: confirm (by reading, not just testing) that
      `request_tool_approval()` sits on every path that can trigger an
      actual SMTP send — no bypass route exists.
**Complexity:** Medium
**Primary Risk:** `_run_approval_gate`'s `is_cli`/`is_gateway`
branching (`tools/approval.py:908`) was written for CLI and messaging-
platform gateways — a third client type (native GUI over
`tui_gateway` RPC) may not be one of the branches it currently
recognizes, which could silently fail closed (safe but broken) or
misroute rather than working as intended; this needs to be confirmed
as part of this track's own investigation, not assumed from this
Build Plan alone.
## Phase Lore Closeout
At Phase 1 merge:
- `zola-architecture/lore/DESIGN_DECISIONS.md`: no new decisions to
  record beyond `P1-D01`–`P1-D06` already captured above (these live
  in this Build Plan document, not duplicated into
  `DESIGN_DECISIONS.md`, per the template's decisions-in-plan
  convention).
- `zola-architecture/lore/OPEN_QUESTIONS.md`: no prior items resolved
  by Phase 1 — `S13` (SMS-reading research) remains open. `S16` was
  added in this closeout for the deferred Google Workspace work.
- `zola-architecture/lore/ROADMAP.md`: Phase 1 marked COMPLETE with
  the four landed merge SHAs. Phase 2 stub lists candidates only
  (S16 Google Workspace, the deferred Obsidian-style UI theme, voice,
  `S13`, `S12`) — order not decided.
## Phase Exit Checklist
- [ ] All 4 completed tracks' exit criteria checked off (Tracks 5 and 6 deferred — see S16).
- [ ] Full manual smoke pass: fresh client launch → start session →
      resume session → identity check → memory write/read → email
      read → email send with approve → email send with deny.
- [ ] No Hermes-side files modified outside what's explicitly listed
      per track (`apps/desktop/`, `hermes_cli/web_routers/sessions.py`,
      `hermes_cli/web_server_sessions.py`, `hermes_state_sessions.py`,
      `plugins/platforms/email/adapter.py`, `tools/approval.py`,
      `tui_gateway/` all stay read-only/config-only per the tracks
      above — flag any deviation).
- [ ] All lore-file updates above confirmed on `main`.
## What Phase 1 Explicitly Defers
| Item | Reason | When |
|---|---|---|
| SMS reading | Needs Windows-viable mechanism research (`S13`) | After `S13` resolves |
| Daily Brief pipeline (email+SMS analysis) | Explicitly deferred by Brian until core email/SMS work first (`S12`) | Post-Phase-1 |
| Gmail OAuth / native connector | No existing code to extend; app-password adapter covers v1 (`S15`) | Post-Phase-1, revisit if app-password path breaks |
| Gmail/Calendar/Drive/Contacts integration (full Google Workspace) | No viable hard-gate path found within original email-only scope; Brian wants full Workspace access, not email alone (`S16`) | Future dedicated build |
| Structured/tiered memory store | Deferred long-term target (`S14`) | After real usage data exists |
| Relational Intelligence Layer, Self-Model Awareness subsystems | Too in-depth for v1 (`S2`/`S3`) | Post-foundation |
| Response arbitration/suppression tuning | Want to see default behavior first (`A2`) | After Phase 1 usage |
| Sidecar scheduling (vs. cron) | Cron sufficient for now (`S7`) | If cron proves insufficient |
| Voice identity / RIL calibration | Blocked pending other subsystems | Post-foundation |
## Complexity Legend
| Track | Complexity |
|---|---|
| 1 — Client/process scaffold | High |
| 2 — Identity extension | Low |
| 3 — Session wrap | Medium |
| 4 — Memory extension | Low |
| 5 — Email (Gmail) | Deferred — see S16 |
| 6 — Confirmed send | Deferred — see S16 |
## Footer
Version 1.2 · Created 2026-09-21, corrected 2026-09-22 (Track 3's
session API, Track 6's connection model, profile-isolation moved to
Track 1, confirmed-send hardening). 2026-09-22: Tracks 5 & 6 deferred
to a future Google Workspace Integration build after Track 5's Phase 2
grounding (see S16). · Pre-plan baseline SHA: 64999cd61d9d8c33d2b25e3590ba0a04ddd09d4c
· Prerequisite: WINH01–WINH12 audit series (merged to `main`) +
Decisions Locked stage (this project's `DESIGN_DECISIONS.md`,
complete). Begin with Track 1 — no other track should start until it
merges.
