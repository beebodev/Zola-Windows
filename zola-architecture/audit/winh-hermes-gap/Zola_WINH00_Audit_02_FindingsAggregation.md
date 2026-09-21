# WINH00 Audit 02 — Full-Series Findings Aggregation

Pinned tag (final re-check, WINH00 Phase 1): Hermes Agent 2026.9.14 / 345cd2b057a452236de401d3534b8502a7465e8d.

Source of IDs, labels, severities, and one-liners: Zola_WINH_Audit_PROGRESS.md running findings list (WINH01-AUD-01 through WINH12-AUD-17). No new finding IDs. This table is a 1:1 row count of that list.

Domain names are the phase short titles from the series phase table / each phase synthesis.

## Master findings table

| ID | Phase | Domain | Label | Severity | One-line |
|---|---|---|---|---|---|
| WINH01-AUD-01 | WINH01 | Native Windows Runtime | [PARTIAL] | MEDIUM | Native Windows is a first-class install path, but the project's own feature matrix does not claim full Linux/macOS parity. |
| WINH01-AUD-02 | WINH01 | Native Windows Runtime | [GAP] | HIGH | Matrix E2EE (`python-olm`) is explicitly unsupported on native Windows; docs tell users to use WSL. |
| WINH01-AUD-03 | WINH01 | Native Windows Runtime | [RISK] | MEDIUM | Dashboard `/chat` docs still say POSIX-PTY / WSL-only; this tag ships a ConPTY `WinPtyBridge`. Docs and code conflict. |
| WINH01-AUD-04 | WINH01 | Native Windows Runtime | [RISK] | MEDIUM | Default pytest suite is Linux-only. Windows CI runs only `@pytest.mark.windows_only` tests, not the full suite. |
| WINH01-AUD-05 | WINH01 | Native Windows Runtime | [RISK] | MEDIUM | Desktop Playwright E2E is Linux-only and currently hard-disabled (`if: false`). |
| WINH01-AUD-06 | WINH01 | Native Windows Runtime | [GAP] | LOW | CJK FTS5 tokenizer builds a `.so` with `gcc`; no Windows/MSVC path in this tag. |
| WINH01-AUD-07 | WINH01 | Native Windows Runtime | [PARTIAL] | MEDIUM | Native Windows shell execution goes through Git Bash (`bash.exe`), not cmd/PowerShell; documented as the POSIX-compat strategy. |
| WINH01-AUD-08 | WINH01 | Native Windows Runtime | [MATCH] | LOW | Default native install is `uv` plus CPython 3.11 wheels plus PortableGit/Node; no Visual Studio Build Tools required for the core path. |
| WINH01-AUD-09 | WINH01 | Native Windows Runtime | [RISK] | LOW | No in-repo `KNOWN_ISSUES.md`. The only tracked Windows issues file is historical installer/updater known-failures, not live bugs. |
| WINH02-AUD-01 | WINH02 | Integration Surfaces & Desktop Reference | [MATCH] | MEDIUM | JSON-RPC gateway is the only surface that already carries the full first-party agent-loop contract and is exercised by Desktop, TUI, and dashboard `/api/ws`. |
| WINH02-AUD-02 | WINH02 | Integration Surfaces & Desktop Reference | [RISK] | HIGH | internal, generated, un-semvered contract. A packaged Zola client cannot detect a breaking Hermes update from version numbers alone. |
| WINH02-AUD-03 | WINH02 | Integration Surfaces & Desktop Reference | [PARTIAL] | MEDIUM | public OpenAI-compatible API with streaming, tool progress, and stop; missing the first-party RPC catalog Desktop actually uses. |
| WINH02-AUD-04 | WINH02 | Integration Surfaces & Desktop Reference | [PARTIAL] / [GAP] / [RISK] | MEDIUM | dashboard hosts Surface 3 at `/api/ws` and a PTY embed at `/api/pty`; session token is process-ephemeral. |
| WINH02-AUD-05 | WINH02 | Integration Surfaces & Desktop Reference | [PARTIAL] / [GAP] | MEDIUM | public ACP stdio for IDEs; `hermes-acp` toolset drops cron and other product tools; not a Windows desktop product surface. |
| WINH02-AUD-06 | WINH02 | Integration Surfaces & Desktop Reference | [GAP] | LOW | MCP messaging-conversation bridge, not an agent chat loop. |
| WINH02-AUD-07 | WINH02 | Integration Surfaces & Desktop Reference | [GAP] | LOW | inbound HMAC webhook receiver; Zola cannot call into it as a client. |
| WINH02-AUD-08 | WINH02 | Integration Surfaces & Desktop Reference | [MATCH] | MEDIUM | official Desktop uses Surface 3 JSON-RPC over `/api/ws` via `JsonRpcGatewayClient`. |
| WINH02-AUD-09 | WINH02 | Integration Surfaces & Desktop Reference | [MATCH] / [PARTIAL] | MEDIUM | Desktop launches a `hermes serve` sidecar and can instead attach to a remote/existing gateway. |
| WINH02-AUD-10 | WINH02 | Integration Surfaces & Desktop Reference | [PARTIAL] | MEDIUM | reconnect/replay exist; mid-turn disconnect interrupt is deferred. |
| WINH02-AUD-11 | WINH02 | Integration Surfaces & Desktop Reference | [PARTIAL] | MEDIUM | transport is separable; UI/i18n/productName are Hermes-coupled. |
| WINH02-AUD-12 | WINH02 | Integration Surfaces & Desktop Reference | [RISK] | MEDIUM | SSE disconnect fail-closes (interrupt); JSON-RPC `client_gone` defers interrupt. Two surfaces disagree on who owns a mid-turn disconnect. Restated with mechanism in WINH03-AUD-05 / WINH03-AUD-08. |
| WINH03-AUD-01 | WINH03 | Operational Contract | [GAP] | MEDIUM | `hermes serve` does not start the OpenAI API; `hermes gateway` does not bind `/api/ws`. Path B and Path C cannot share one spawned process. |
| WINH03-AUD-02 | WINH03 | Operational Contract | [MATCH] | LOW | one JSON-RPC turn traced as a named-function chain. |
| WINH03-AUD-03 | WINH03 | Operational Contract | [MATCH] | LOW | `message.complete` carries full `text` plus `usage`/`status`, not a bare done signal. |
| WINH03-AUD-04 | WINH03 | Operational Contract | [PARTIAL] | MEDIUM | approval blocks the turn thread on the queue (default 300s); JSON-RPC dispatcher can still read `session.interrupt`. |
| WINH03-AUD-05 | WINH03 | Operational Contract | [RISK] | HIGH | Surface 3 default keeps a healthy detached turn running (“an active turn runs to completion”); not an immediate interrupt. |
| WINH03-AUD-06 | WINH03 | Operational Contract | [PARTIAL] | MEDIUM | no interrupt-on-disconnect RPC; `close_on_disconnect` reaps without calling `_interrupt_session_turn`. Desktop main chats do not set the flag. |
| WINH03-AUD-07 | WINH03 | Operational Contract | [PARTIAL] / [UNVERIFIED] | MEDIUM | client interrupt-then-close can approximate Surface 1 if the frame is read; unread-frame race `[UNVERIFIED]`. |
| WINH03-AUD-08 | WINH03 | Operational Contract | [RISK] | HIGH | restates WINH02-AUD-12: Surface 3 default is structurally fail-open; fail-closed requires client `session.interrupt` and/or sidecar env (`HERMES_TUI_WS_ORPHAN_ACTIVITY_STALE_S=0` with grace > 0), not socket-drop alone. |
| WINH03-AUD-09 | WINH03 | Operational Contract | [PARTIAL] | MEDIUM | process crash loses live runtime and the 512-event ring; `session.resume` reloads durable transcript and builds a new agent. |
| WINH03-AUD-10 | WINH03 | Operational Contract | [UNVERIFIED] | MEDIUM | resume-after-hard-kill integrity not settled by static reading. |
| WINH03-AUD-11 | WINH03 | Operational Contract | [PARTIAL] | LOW | sleep/wake misfire of the orphan timer is `[UNVERIFIED]`. |
| WINH03-AUD-12 | WINH03 | Operational Contract | [RISK] | MEDIUM | missing handlers time out then skip/deny at defaults; clarify `timeout <= 0` can wait forever. |
| WINH03-AUD-13 | WINH03 | Operational Contract | [MATCH] | LOW | consumable outside the Hermes workspace via a relative `file:` dependency; still un-semvered (`WINH02-AUD-02`). |
| WINH04-AUD-01 | WINH04 | Memory & Skills | [PARTIAL] | MEDIUM | builtin files + transcript + optional one plugin do not implement Hierarchy layers 0–6 as distinct stores. |
| WINH04-AUD-02 | WINH04 | Memory & Skills | [RISK] | MEDIUM | provider session hooks persist memory outside `memory_tool`. |
| WINH04-AUD-03 | WINH04 | Memory & Skills | [GAP] | HIGH | Privacy Plan §3 retention windows unenforced. |
| WINH04-AUD-04 | WINH04 | Memory & Skills | [PARTIAL] | MEDIUM | per-entry substring delete + file wipe; no cascade to `state.db`/clouds. |
| WINH04-AUD-05 | WINH04 | Memory & Skills | [GAP] | HIGH | builtin entries are untyped strings (`memory_tool_store.py`); Ethics visibility scopes and sacred categories absent. |
| WINH04-AUD-06 | WINH04 | Memory & Skills | [GAP] | HIGH | frozen prompt dump (`memory_tool.py` L2–4); `hermes_tools_mcp_server.py` L40 omits `memory` but instance tools/messaging still see the snapshot. |
| WINH04-AUD-07 | WINH04 | Memory & Skills | [GAP] | MEDIUM | `atomic_write_text` `memory_tool_store.py` L422; no fact-memory ledger (contrast `tools/skill_ledger.py`). |
| WINH04-AUD-08 | WINH04 | Memory & Skills | [MATCH] | LOW | separate backends. |
| WINH04-AUD-09 | WINH04 | Memory & Skills | [RISK] | MEDIUM | agent `skill_manage` create/edit ungated by default. |
| WINH04-AUD-10 | WINH04 | Memory & Skills | [PARTIAL] | MEDIUM | `skills_tool.py` `skill_view` L540–549 fail-visible on load; no auto-disable on runtime skill error. |
| WINH04-AUD-11 | WINH04 | Memory & Skills | [GAP] | MEDIUM | no source/scope/authority/freshness metadata or promotion state machine. |
| WINH04-AUD-12 | WINH04 | Memory & Skills | [GAP] | MEDIUM | USER.md is a single flattened profile (`memory_tool_store.py` L20–21). |
| WINH04-AUD-13 | WINH04 | Memory & Skills | [PARTIAL] | LOW | score decay, not deletion. |
| WINH04-AUD-14 | WINH04 | Memory & Skills | [GAP] | MEDIUM | no Hermes mechanism. |
| WINH05-AUD-01 | WINH05 | Identity, Personality & Self-Model | [GAP] | HIGH | no locked Identity Seed; SOUL.md is fully replaceable prompt text. |
| WINH05-AUD-02 | WINH05 | Identity, Personality & Self-Model | [PARTIAL] | MEDIUM | identity / overlay / USER.md are separate slots, not locked-vs-adaptive types. |
| WINH05-AUD-03 | WINH05 | Identity, Personality & Self-Model | [GAP] | HIGH | style is config/presets; `trust_score` is retrieval, not phrasing. |
| WINH05-AUD-04 | WINH05 | Identity, Personality & Self-Model | [GAP] | MEDIUM | no persona drift/baseline job; `agent/curator.py` is skill lifecycle only (WINH04). |
| WINH05-AUD-05 | WINH05 | Identity, Personality & Self-Model | [GAP] | HIGH | one persona string per session; USER.md has no context key (WINH04-AUD-01 Layer 5 remains additive). |
| WINH05-AUD-06 | WINH05 | Identity, Personality & Self-Model | [RISK] | HIGH | multiple independently-maintained identity strings. |
| WINH05-AUD-07 | WINH05 | Identity, Personality & Self-Model | [RISK] | MEDIUM | agent name/identity change is a multi-file edit; customized SOUL.md is never auto-updated. |
| WINH05-AUD-08 | WINH05 | Identity, Personality & Self-Model | [GAP] | MEDIUM | no style-profile store; USER.md is the only default place learned style could live. |
| WINH05-AUD-09 | WINH05 | Identity, Personality & Self-Model | [GAP] | MEDIUM | no numeric clamps / bounded-evolution / style drift log (Consolidation Plan §8–9). |
| WINH05-AUD-10 | WINH05 | Identity, Personality & Self-Model | [GAP] | HIGH | no `SelfBeliefBlock`; self-description is static SOUL.md / `DEFAULT_AGENT_IDENTITY`. |
| WINH05-AUD-11 | WINH05 | Identity, Personality & Self-Model | [GAP] | MEDIUM | “when unsure, say so” is a style instruction, not computed hedging. |
| WINH05-AUD-12 | WINH05 | Identity, Personality & Self-Model | [GAP] | MEDIUM | no SMA subsystem; agent loop writes memory and produces output (SMA read-only boundary unimplemented). |
| WINH05-AUD-13 | WINH05 | Identity, Personality & Self-Model | [MATCH] | LOW | no user-facing self-model confidence numbers (prohibition not violated). |
| WINH05-AUD-14 | WINH05 | Identity, Personality & Self-Model | [PARTIAL] | MEDIUM | explicit session row; no `deviceId`; live sid ≠ durable id. |
| WINH05-AUD-15 | WINH05 | Identity, Personality & Self-Model | [RISK] | HIGH | not a single mint call site. |
| WINH05-AUD-16 | WINH05 | Identity, Personality & Self-Model | [PARTIAL] | MEDIUM | WS orphan/resume ≠ Zola 30s app-background close. |
| WINH05-AUD-17 | WINH05 | Identity, Personality & Self-Model | [PARTIAL] | MEDIUM | profile/connection scoped, not user+device provenance. |
| WINH05-AUD-18 | WINH05 | Identity, Personality & Self-Model | [PARTIAL] | MEDIUM | transcripts stamped; MEMORY.md writes not. |
| WINH06-AUD-01 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | MEDIUM | `skill_manage` create/edit/patch/delete/write_file/remove_file; no enable/disable action. |
| WINH06-AUD-02 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | HIGH | `skills.write_approval` default False; gate fail-open on import (WINH04-AUD-09 confirmed). |
| WINH06-AUD-03 | WINH06 | Self-Improvement & Capability Acquisition | [ABSENT] | HIGH | no dry-run/staging; `guard_agent_created` default False; write then live. |
| WINH06-AUD-04 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | LOW | JSONL mutation ledger with before/after blobs; `session_id` in evidence when dispatch injects it. |
| WINH06-AUD-05 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | MEDIUM | ledger is telemetry not a gate; append failures do not block the write. |
| WINH06-AUD-06 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | MEDIUM | CLI `hermes curator rollback <id>`; foreground delete is hard; no transcript cascade. |
| WINH06-AUD-07 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | HIGH | post-turn fork can `skill_manage`; default `background_review.enabled: True`. |
| WINH06-AUD-08 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | HIGH | same ungated default applies to the review fork. |
| WINH06-AUD-09 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | MEDIUM | desktop `setup_mcp` is a human consent card, not a silent config write. |
| WINH06-AUD-10 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | HIGH | non-desktop fallback is `terminal` `hermes mcp install/add`; not in hardline patterns. |
| WINH06-AUD-11 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | MEDIUM | plugin install is CLI/TUI; `plugin_guard`; `plugins.enabled` opt-in; capability consent. |
| WINH06-AUD-12 | WINH06 | Self-Improvement & Capability Acquisition | [ABSENT] | MEDIUM | no agent plugin-install tool (directory-drop still needs `plugins.enabled` in config). |
| WINH06-AUD-13 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | HIGH | new plugins in-process; MCP stdio as same OS user; no extra sandbox for newly added capability. |
| WINH06-AUD-14 | WINH06 | Self-Improvement & Capability Acquisition | [ABSENT] | MEDIUM | no single inventory of skills + tools + plugins + MCP. |
| WINH06-AUD-15 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | MEDIUM | lazy PyPI installs into the venv; `allow_lazy_installs` default True. |
| WINH06-AUD-16 | WINH06 | Self-Improvement & Capability Acquisition | [UNVERIFIED] | LOW | live attach of CLI-installed MCP without `/reload-mcp` not confirmed in this checkout. |
| WINH06-AUD-17 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | HIGH | `$HERMES_HOME/SOUL.md` exempt from protected-instruction always-ask; `write_file` can rewrite it. |
| WINH06-AUD-18 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | MEDIUM | project-local SOUL.md always-ask; `config.yaml` hard-blocked on `write_file`. |
| WINH06-AUD-19 | WINH06 | Self-Improvement & Capability Acquisition | [ABSENT] | HIGH | no draft/review state for identity or config self-modification. |
| WINH06-AUD-20 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | HIGH | SOUL rewrite has no SOUL ledger; WINH05-AUD-06/07 strings do not follow. |
| WINH06-AUD-21 | WINH06 | Self-Improvement & Capability Acquisition | [RISK] | MEDIUM | `hermes config set` via `terminal` bypasses the `write_file` config hard-block. |
| WINH06-AUD-22 | WINH06 | Self-Improvement & Capability Acquisition | [ABSENT] | LOW | no bundled fine-tune/RLHF/weight loop; optional TRL skill is user documentation. |
| WINH06-AUD-23 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | MEDIUM | only non-memory adaptation loop: post-turn skill/memory fork. |
| WINH06-AUD-24 | WINH06 | Self-Improvement & Capability Acquisition | [ABSENT] | MEDIUM | no performance self-eval / A/B / prompt-optimization loop. |
| WINH06-AUD-25 | WINH06 | Self-Improvement & Capability Acquisition | [MECHANISM] | LOW | `/model` is a human slash; toolsets do not change with model id. |
| WINH07-AUD-01 | WINH07 | Authority, Governance & Routing | [PARTIAL] | HIGH | primary `message.complete` path exists; `review.summary`, notices, heartbeat turns, and child completes also speak. |
| WINH07-AUD-02 | WINH07 | Authority, Governance & Routing | [RISK] | HIGH | WINH06 fork emits user-facing `review.summary` / `_safe_print`, not file-only. |
| WINH07-AUD-03 | WINH07 | Authority, Governance & Routing | [PARTIAL] | MEDIUM | same-gateway concurrent submits serialize via `running`; no cross-surface arbiter. |
| WINH07-AUD-04 | WINH07 | Authority, Governance & Routing | [GAP] | HIGH | no Response Governor / named core; `_emit` is a transport helper. |
| WINH07-AUD-05 | WINH07 | Authority, Governance & Routing | [PARTIAL] | MEDIUM | scope = enabled tools + danger overlay; no §13 permission catalog. |
| WINH07-AUD-06 | WINH07 | Authority, Governance & Routing | [PARTIAL] | MEDIUM | danger/sudo/slash confirms; no contact/third-party escalation class. |
| WINH07-AUD-07 | WINH07 | Authority, Governance & Routing | [RISK] | HIGH | default `approvals.mode: smart` (and interrupt/notify defaults) assume trust. |
| WINH07-AUD-08 | WINH07 | Authority, Governance & Routing | [PARTIAL] | MEDIUM | approval prompts explain; smart-allow / missing toolset do not. |
| WINH07-AUD-09 | WINH07 | Authority, Governance & Routing | [GAP] | HIGH | only Surfaces 2+3 share a dispatcher; four surfaces route alone. |
| WINH07-AUD-10 | WINH07 | Authority, Governance & Routing | [PARTIAL] | MEDIUM | shared ladder function; review/delegation may pick independently. |
| WINH07-AUD-11 | WINH07 | Authority, Governance & Routing | [RISK] | MEDIUM | orphaned output: drop / 512-ring / later attacher / session_key notify. |
| WINH07-AUD-12 | WINH07 | Authority, Governance & Routing | [GAP] | MEDIUM | routing authority not discoverable in one place (`WINH06-AUD-14` pattern). |
| WINH07-AUD-13 | WINH07 | Authority, Governance & Routing | [GAP] | HIGH | same model call chain both reasons and phrases; no downstream formatter. |
| WINH07-AUD-14 | WINH07 | Authority, Governance & Routing | [GAP] | HIGH | no check that final text preserves tool numbers/names/dates. |
| WINH07-AUD-15 | WINH07 | Authority, Governance & Routing | [GAP] | HIGH | architecture does not separate reasoning vs speech; verify-on-stop ≠ fidelity. |
| WINH08-AUD-01 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [PARTIAL] | MEDIUM | several worker paths exist; not Agent Map prepare-only categories. |
| WINH08-AUD-02 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [RISK] | HIGH | subagent/review/cron/heartbeat invoke tools off the live tool-round. |
| WINH08-AUD-03 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [GAP] | MEDIUM | no consumer-facing freshness/confidence on cached/precomputed data. |
| WINH08-AUD-04 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [PARTIAL] | MEDIUM | review yields to live; cron/delegate have no Agent 14 priority tiers. |
| WINH08-AUD-05 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [MATCH] | LOW | live turn: persist → execute → guards/approval → result. |
| WINH08-AUD-06 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [RISK] | HIGH | background/subagent/cron/heartbeat do not share one live human gate. |
| WINH08-AUD-07 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [MATCH] | LOW | no speculative tool pre-execute (Agent 8 constraint holds by absence). |
| WINH08-AUD-08 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [RISK] | MEDIUM | orphaned turn keeps gateway approval until timeout, not unattended deny. |
| WINH08-AUD-09 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [OBSERVATION] | OBSERVATION | real cron ticker (60s) + jobs.json; not the review fork. |
| WINH08-AUD-10 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [OBSERVATION] | OBSERVATION | cron runs full agent; danger default-deny; heartbeat uses live auth. |
| WINH08-AUD-11 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [PARTIAL] | MEDIUM | claim + misfire grace; not Agent 15 lastDeliveredDate. |
| WINH08-AUD-12 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [GAP] | MEDIUM | no single place listing every scheduled job (`WINH06-AUD-14` / `WINH07-AUD-12` pattern). |
| WINH08-AUD-13 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [PARTIAL] | MEDIUM | memory prefetch exists; no live-wins over cached recall text. |
| WINH08-AUD-14 | WINH08 | Tool Calling, Subagents & Scheduled Automation | [MATCH] | LOW | prefetch is read/inject only; no speculative durable write. |
| WINH09-AUD-01 | WINH09 | Voice Pipeline & Voice Identity | [PARTIAL] | MEDIUM | ElevenLabs built-in file + PCM streamer; ABC `stream()` still default-unimplemented. |
| WINH09-AUD-02 | WINH09 | Voice Pipeline & Voice Identity | [PARTIAL] | MEDIUM | No Cartesia/Deepgram built-in; command or plugin (file STT). |
| WINH09-AUD-03 | WINH09 | Voice Pipeline & Voice Identity | [MATCH] | LOW | Built-in `tts.provider` / `stt.provider` swap by config. |
| WINH09-AUD-04 | WINH09 | Voice Pipeline & Voice Identity | [PARTIAL] | MEDIUM | No latency catalog; `streaming.provider` auto/pin only. |
| WINH09-AUD-05 | WINH09 | Voice Pipeline & Voice Identity | [PARTIAL] | MEDIUM | Chained: VAD → file STT → `voice.transcript` → client `prompt.submit`. |
| WINH09-AUD-06 | WINH09 | Voice Pipeline & Voice Identity | [PARTIAL] | MEDIUM | STT batch after silence; TTS sentence-stream if streamer exists. |
| WINH09-AUD-07 | WINH09 | Voice Pipeline & Voice Identity | [PARTIAL] | MEDIUM | Context is a prompt note; GPT-Live WebRTC is a separate OpenAI duplex mode. |
| WINH09-AUD-08 | WINH09 | Voice Pipeline & Voice Identity | [MATCH] | MEDIUM | Barge-in stops TTS and latches next-turn interrupt note. |
| WINH09-AUD-09 | WINH09 | Voice Pipeline & Voice Identity | [RISK] | MEDIUM | One mic/speaker per process; JSON-RPC voice assumes that topology. |
| WINH09-AUD-10 | WINH09 | Voice Pipeline & Voice Identity | [GAP] | HIGH | No speaker-identity / embedding tracker. |
| WINH09-AUD-11 | WINH09 | Voice Pipeline & Voice Identity | [GAP] | HIGH | No voice enrollment (ambient or formal). |
| WINH09-AUD-12 | WINH09 | Voice Pipeline & Voice Identity | [RISK] | MEDIUM | On-device identity would not be structurally enforced. |
| WINH09-AUD-13 | WINH09 | Voice Pipeline & Voice Identity | [GAP] | MEDIUM | Turns are single-author for voice; no speaker field. |
| WINH09-AUD-14 | WINH09 | Voice Pipeline & Voice Identity | [GAP] | HIGH | Wake-word is the primary gate, not directed-speech. |
| WINH09-AUD-15 | WINH09 | Voice Pipeline & Voice Identity | [GAP] | MEDIUM | Activation is binary. |
| WINH09-AUD-16 | WINH09 | Voice Pipeline & Voice Identity | [PARTIAL] | MEDIUM | After capture, wake re-arms; no continuation window. |
| WINH10-AUD-01 | WINH10 | Messaging Surfaces | [PARTIAL] | MEDIUM | Allowlist/pairing gate, not silent contact-list exclusion. |
| WINH10-AUD-02 | WINH10 | Messaging Surfaces | [GAP] | HIGH | No signal-extract-then-discard; raw body is the turn. |
| WINH10-AUD-03 | WINH10 | Messaging Surfaces | [GAP] | MEDIUM | No first-class thread-velocity signal. |
| WINH10-AUD-04 | WINH10 | Messaging Surfaces | [PARTIAL] | MEDIUM | Channel allowlist ≠ `smsAnalysisConsent`. |
| WINH10-AUD-05 | WINH10 | Messaging Surfaces | [MATCH] | LOW | `send_message` not model-callable; CLI/cron/kanban/MCP call helpers. |
| WINH10-AUD-06 | WINH10 | Messaging Surfaces | [RISK] | HIGH | Live gateway reply is autonomous send on the inbound channel. |
| WINH10-AUD-07 | WINH10 | Messaging Surfaces | [GAP] | HIGH | Host send paths have no two-step per-message confirm. |
| WINH10-AUD-09 | WINH10 | Messaging Surfaces | [PARTIAL] | MEDIUM | Twilio SMS exists; Windows has no handset radio. |
| WINH10-AUD-10 | WINH10 | Messaging Surfaces | [PARTIAL] | MEDIUM | Mail bot ≠ EmailSignal; Graph is Teams not Outlook mail. |
| WINH10-AUD-11 | WINH10 | Messaging Surfaces | [MATCH] | LOW | Broad chat-platform coverage; WhatsApp/Signal/Twilio for “text”. |
| WINH10-AUD-12 | WINH10 | Messaging Surfaces | [OBSERVATION] | OBSERVATION | Windows SMS options; not a Hermes score. |
| WINH10-AUD-13 | WINH10 | Messaging Surfaces | [RISK] | MEDIUM | Comms bodies persist like any other turn. |
| WINH11-AUD-01 | WINH11 | Windows Security & Deployment | [GAP] | HIGH | provider keys live in plaintext `<HERMES_HOME>/.env`. |
| WINH11-AUD-02 | WINH11 | Windows Security & Deployment | [PARTIAL] | MEDIUM | autofill vault is Fernet; `vault.key` sits beside `vault.json.enc`. |
| WINH11-AUD-03 | WINH11 | Windows Security & Deployment | [PARTIAL] | MEDIUM | Desktop `safeStorage` (DPAPI) exists, default OFF, tokens only. |
| WINH11-AUD-04 | WINH11 | Windows Security & Deployment | [GAP] | HIGH | `state.db` is plain `sqlite3.connect`. |
| WINH11-AUD-05 | WINH11 | Windows Security & Deployment | [GAP] | HIGH | memory markdown + session DB unencrypted at rest. |
| WINH11-AUD-06 | WINH11 | Windows Security & Deployment | [PARTIAL] | MEDIUM | data-mgmt gate is ephemeral SPA token, not user auth (cite `WINH02-AUD-04`). |
| WINH11-AUD-07 | WINH11 | Windows Security & Deployment | [GAP] | MEDIUM | DWA still absent; §9 write-gate unmet. |
| WINH11-AUD-08 | WINH11 | Windows Security & Deployment | [PARTIAL] | MEDIUM | default `verify=True`; `http://` base_url allowed; no TLS 1.2 pin. |
| WINH11-AUD-09 | WINH11 | Windows Security & Deployment | [GAP] | LOW | Distributed Presence E2E out of series (N/A, not scratch). |
| WINH11-AUD-10 | WINH11 | Windows Security & Deployment | [RISK] | HIGH | secret-source credentials copied into MCP child env. |
| WINH11-AUD-11 | WINH11 | Windows Security & Deployment | [PARTIAL] | MEDIUM | master stores blocked; no separate Tier 1/2 grant. |
| WINH11-AUD-12 | WINH11 | Windows Security & Deployment | [RISK] | HIGH | Windows Desktop is built unsigned. |
| WINH11-AUD-13 | WINH11 | Windows Security & Deployment | [RISK] | MEDIUM | uninstall leaves `HERMES_HOME` / credentials / `state.db`. |
| WINH11-AUD-14 | WINH11 | Windows Security & Deployment | [ABSENT] | HIGH | no Windows Authenticode/CI signing. |
| WINH11-AUD-15 | WINH11 | Windows Security & Deployment | [MECHANISM] | MEDIUM | custom git/zip update, not electron-updater. |
| WINH11-AUD-16 | WINH11 | Windows Security & Deployment | [RISK] | HIGH | no commit-sig / zip checksum on updates. |
| WINH11-AUD-17 | WINH11 | Windows Security & Deployment | [MECHANISM] | LOW | NSIS per-user, `oneClick: false`. |
| WINH11-AUD-18 | WINH11 | Windows Security & Deployment | [MECHANISM] | LOW | NSIS+MSI targets; MSI extras unverified. |
| WINH11-AUD-19 | WINH11 | Windows Security & Deployment | [MECHANISM] | MEDIUM | Electron `contextIsolation` + `sandbox` + `nodeIntegration: false`. |
| WINH11-AUD-20 | WINH11 | Windows Security & Deployment | [RISK] | MEDIUM | Windows can fall back to `--no-sandbox`. |
| WINH11-AUD-21 | WINH11 | Windows Security & Deployment | [MECHANISM] | LOW | no always-on Hermes telemetry. |
| WINH11-AUD-22 | WINH11 | Windows Security & Deployment | [MECHANISM] | LOW | runs as user; UAC only for gateway task install. |
| WINH12-AUD-01 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | timestamps/dates exist; no elapsed-time-to-meaning. |
| WINH12-AUD-02 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | no relational `SessionBoundaryResolver`. |
| WINH12-AUD-03 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | no `ThreadArcClassifier` or `TemporalRecencyFormatter`. |
| WINH12-AUD-04 | WINH12 | Relational Intelligence & Model Provider Flexibility | [RISK] | MEDIUM | clock split: prompt TZ vs `time.time` vs UTC datetime. |
| WINH12-AUD-05 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | belief/correction/entity-view/arc contracts absent. |
| WINH12-AUD-06 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | no third-party person model; flat MEMORY.md/USER.md. |
| WINH12-AUD-07 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | no structured relationship predicates. |
| WINH12-AUD-08 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | MEDIUM | no salience / distinct-session recurrence ranking. |
| WINH12-AUD-09 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | no relationship-arc document. |
| WINH12-AUD-10 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | prompt injects memory files + date, not an arc block. |
| WINH12-AUD-11 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | no depth-driven familiarity / warmth ceiling. |
| WINH12-AUD-12 | WINH12 | Relational Intelligence & Model Provider Flexibility | [GAP] | HIGH | Calibration dependency chain unmet at every link. |
| WINH12-AUD-13 | WINH12 | Relational Intelligence & Model Provider Flexibility | [MATCH] | MEDIUM | Gemini/OpenAI/Anthropic native; not Gemini-locked. |
| WINH12-AUD-14 | WINH12 | Relational Intelligence & Model Provider Flexibility | [MATCH] | MEDIUM | local OpenAI-compat can run the full tool loop. |
| WINH12-AUD-15 | WINH12 | Relational Intelligence & Model Provider Flexibility | [MATCH] | MEDIUM | live `/model` switches provider+model mid-session. |
| WINH12-AUD-16 | WINH12 | Relational Intelligence & Model Provider Flexibility | [MATCH] | MEDIUM | wire formats convert into one internal representation. |
| WINH12-AUD-17 | WINH12 | Relational Intelligence & Model Provider Flexibility | [RISK] | MEDIUM | single delivery path vs Hermes multi-path speech. |

Row count of the table above: **187**.

Note: WINH10-AUD-08 was never issued (numbering skip in WINH10). Multi-label rows kept as recorded: WINH02-AUD-04 [PARTIAL] / [GAP] / [RISK]; WINH02-AUD-05 [PARTIAL] / [GAP]; WINH02-AUD-09 [MATCH] / [PARTIAL]; WINH03-AUD-07 [PARTIAL] / [UNVERIFIED]. Label tallies below use the **first** bracket token.

[OBSERVATION] rows (WINH08-AUD-09, WINH08-AUD-10, WINH10-AUD-12) are listed in the table and counted separately from HIGH/MEDIUM/LOW, per the WINH08 convention.

## Literal count breakdown

### Total

187 rows in the table = 187 findings in the running list (counted, not estimated).

Arithmetic by phase (table rows):

9 (WINH01) + 12 (WINH02) + 13 (WINH03) + 14 (WINH04) + 18 (WINH05) + 25 (WINH06) + 15 (WINH07) + 14 (WINH08) + 16 (WINH09) + 12 (WINH10) + 22 (WINH11) + 17 (WINH12)

= 21 + 13 = 34; +14 = 48; +18 = 66; +25 = 91; +15 = 106; +14 = 120; +16 = 136; +12 = 148; +22 = 170; +17 = **187**.

### By severity

Counted from the same 187 rows. [OBSERVATION] excluded from HIGH/MEDIUM/LOW:

| Severity | Count | Arithmetic |
|---|---|---|
| HIGH | 55 | 1+1+2+3+6+9+8+2+3+3+7+10 (WINH01–12) |
| MEDIUM | 102 | 5+9+7+9+11+12+7+7+12+6+10+7 |
| LOW | 27 | 3+2+4+2+1+4+0+3+1+2+5+0 |
| OBSERVATION (separate) | 3 | WINH08-AUD-09, WINH08-AUD-10, WINH10-AUD-12 |
| **Sum** | **187** | 55+102+27+3 |

HIGH IDs (55): WINH01-AUD-02; WINH02-AUD-02; WINH03-AUD-05, 08; WINH04-AUD-03, 05, 06; WINH05-AUD-01, 03, 05, 06, 10, 15; WINH06-AUD-02, 03, 07, 08, 10, 13, 17, 19, 20; WINH07-AUD-01, 02, 04, 07, 09, 13, 14, 15; WINH08-AUD-02, 06; WINH09-AUD-10, 11, 14; WINH10-AUD-02, 06, 07; WINH11-AUD-01, 04, 05, 10, 12, 14, 16; WINH12-AUD-01, 02, 03, 05, 06, 07, 09, 10, 11, 12.

WINH08 phase synthesis counted AUD-09/10 inside MEDIUM (9 MEDIUM including 2 OBS). This series roll-up follows WINH08’s own OBSERVATION convention and WINH10’s (AUD-12 not a Zola miss): those three rows are **not** folded into MEDIUM. WINH08 MEDIUM here is therefore 7, not 9.

### By label (first bracket token)

Scored-against-Zola-requirement labels (MATCH/GAP/RISK/PARTIAL), then exploratory-convention labels counted separately (WINH06 all 25; WINH11 Half B; WINH03-AUD-10 UNVERIFIED; WINH08/10 OBSERVATION):

| Label | Count | Notes |
|---|---|---|
| MATCH | 20 | first token only; WINH02-AUD-09 counted MATCH not PARTIAL |
| GAP | 53 | |
| RISK | 39 | |
| PARTIAL | 47 | WINH02-AUD-04/05 and WINH03-AUD-07 counted PARTIAL |
| MECHANISM | 16 | WINH06 + WINH11 Half B |
| ABSENT | 7 | WINH06 + WINH11-AUD-14 |
| UNVERIFIED | 2 | WINH06-AUD-16, WINH03-AUD-10 |
| OBSERVATION | 3 | WINH08-AUD-09, WINH08-AUD-10, WINH10-AUD-12 |
| **Sum** | **187** | 20+53+39+47+16+7+2+3 |

20+53=73; +39=112; +47=159; +16=175; +7=182; +2=184; +3=**187**.

### By phase

| Phase | Domain | Findings | HIGH | MEDIUM | LOW | OBS |
|---|---|---|---|---|---|---|
| WINH01 | Native Windows Runtime | 9 | 1 | 5 | 3 | 0 |
| WINH02 | Integration Surfaces & Desktop Reference | 12 | 1 | 9 | 2 | 0 |
| WINH03 | Operational Contract | 13 | 2 | 7 | 4 | 0 |
| WINH04 | Memory & Skills | 14 | 3 | 9 | 2 | 0 |
| WINH05 | Identity, Personality & Self-Model | 18 | 6 | 11 | 1 | 0 |
| WINH06 | Self-Improvement & Capability Acquisition | 25 | 9 | 12 | 4 | 0 |
| WINH07 | Authority, Governance & Routing | 15 | 8 | 7 | 0 | 0 |
| WINH08 | Tool Calling, Subagents & Scheduled Automation | 14 | 2 | 7 | 3 | 2 |
| WINH09 | Voice Pipeline & Voice Identity | 16 | 3 | 12 | 1 | 0 |
| WINH10 | Messaging Surfaces | 12 | 3 | 6 | 2 | 1 |
| WINH11 | Windows Security & Deployment | 22 | 7 | 10 | 5 | 0 |
| WINH12 | Relational Intelligence & Model Provider Flexibility | 17 | 10 | 7 | 0 | 0 |
| **Series** | | **187** | **55** | **102** | **27** | **3** |

Most findings: WINH06 (25), WINH11 (22), WINH05 (18). Fewest: WINH01 (9), WINH02 and WINH10 (12 each). Most HIGH: WINH12 (10), WINH06 (9), WINH07 (8).

WINH00 produces no WINH00-AUD-NN rows (G-NO-INVENT).

