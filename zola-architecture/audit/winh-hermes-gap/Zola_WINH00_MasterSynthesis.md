# WINH00 — Master Synthesis (Hermes Gap Analysis Series)

Pinned tag (final re-check, WINH00 Phase 1): Hermes Agent `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d` at `C:\Users\test\Dev\hermes-agent`. Match confirmed. This phase produced no new finding IDs (G-NO-INVENT) and resolves no open questions (G-NO-DECIDE).

This document is meant to be readable alone. Sections 2–5 reproduce WINH00 Audit 02–05 in full.

---

## Section 1 — Series Overview

The WINH series audited **Hermes Agent `v2026.9.14`** (commit `345cd2b057a452236de401d3534b8502a7465e8d`, marketing v0.21.3) against the Zola-Windows **fresh-start** architecture requirements in `zola-architecture/`: capability requirements, not a port of zola-main and not Android implementation choices. Work ran on shared branch `winh-hermes-audit` (created from `main` at `4ff1abf`) with output under `zola-architecture/audit/winh-hermes-gap/`.

**Twelve domain audits** (WINH01–12) plus this synthesis (WINH00) were committed on **2026-09-21** (every series commit date is that day). Domains: Native Windows Runtime; Integration Surfaces & Desktop Reference; Operational Contract; Memory & Skills; Identity, Personality & Self-Model; Self-Improvement & Capability Acquisition; Authority, Governance & Routing; Tool Calling, Subagents & Scheduled Automation; Voice Pipeline & Voice Identity; Messaging Surfaces; Windows Security & Deployment; Relational Intelligence & Model Provider Flexibility.

**Series total: 187 findings** (WINH01-AUD-01 through WINH12-AUD-17; `WINH10-AUD-08` never issued). Severity: **55 HIGH**, **102 MEDIUM**, **27 LOW**, plus **3 OBSERVATION** counted separately. Recorded scope decisions that held for the whole series: Environmental Awareness / Perception out; fresh-start / capability-not-implementation; Cognitive Engine Architecture out.

WINH00 closes Stage 1 (AUDIT). It does not lock decisions, write a build plan, or merge until the developer says proceed to closeout.

---

## Section 2 — Findings by the Numbers

Reproduced from `Zola_WINH00_Audit_02_FindingsAggregation.md`. Source of IDs: running findings list in `Zola_WINH_Audit_PROGRESS.md`. No new IDs.

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

---

## Section 3 — Cross-Cutting Themes

Reproduced from `Zola_WINH00_Audit_03_CrossCuttingThemes.md`. A theme requires contributing findings in three or more phases.

Pinned tag (final re-check, WINH00 Phase 1): Hermes Agent `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.

A theme is included only when **three or more phases** independently recorded contributing findings. Two-finding links are noted in prose, not promoted to themes. Candidate list from the WINH00 prompt was checked against the running findings list; one candidate (encryption spanning WINH06 skills/config as its own scored finding) did not independently hold.

---

## Theme 1 — At-rest stores in `$HERMES_HOME` and `state.db` are not application-encrypted

**Phases:** WINH04, WINH10, WINH11 (WINH06 did **not** independently score encryption).

**Contributing IDs:**

| ID | Phase | What it recorded |
|---|---|---|
| WINH04-AUD-01 | WINH04 | Builtin memory is profile-scoped files (`MEMORY.md` / `USER.md`) plus `state.db` transcripts — the physical stores later scored for encryption |
| WINH04-AUD-06 | WINH04 | Frozen prompt snapshot of those files; tools can read `$HERMES_HOME/memories/` |
| WINH10-AUD-13 | WINH10 | Messaging bodies persist like any other turn (same transcript/memory path; cites `WINH04-AUD-02` / `AUD-06`) |
| WINH11-AUD-01 | WINH11 | Provider keys in plaintext `<HERMES_HOME>/.env` |
| WINH11-AUD-04 | WINH11 | `state.db` is plain `sqlite3.connect` |
| WINH11-AUD-05 | WINH11 | Memory markdown + session DB unencrypted at rest |

**Not contributing as an encryption finding:** WINH06 inventoried skill/config mutation (`WINH06-AUD-01`, `AUD-18`) as capability-acquisition mechanisms, not as an at-rest crypto gap. Those files sit on the same filesystem; the series did not give them an encryption label.

**Significance.** Encryption-at-rest is not three unrelated misses. WINH04 and WINH10 described *what* lives on disk (notes, transcripts, comms bodies). WINH11 scored *how* it is stored (plaintext files and sqlite). Vault Fernet (`WINH11-AUD-02`) is the exception, and even there `vault.key` is co-located. Whether BitLocker/OS disk encryption satisfies Privacy Plan §9 is a WINH11 Section 5 question, not a finding.

---

## Theme 2 — No confirmed human-in-the-loop gate on irreversible or background actions

**Phases:** WINH04, WINH06, WINH07, WINH08, WINH10.

**Contributing IDs:**

| ID | Phase | What it recorded |
|---|---|---|
| WINH04-AUD-09 | WINH04 | `skill_manage` create/edit ungated (`skills.write_approval: False`) |
| WINH06-AUD-02 | WINH06 | Same default confirmed; scored HIGH because live skills plus review fork |
| WINH06-AUD-07 | WINH06 | Background-review fork can `skill_manage`; default enabled |
| WINH06-AUD-08 | WINH06 | Same ungated approval applies to the review fork |
| WINH06-AUD-10 | WINH06 | Non-desktop MCP add falls back to `terminal` `hermes mcp install/add` |
| WINH07-AUD-07 | WINH07 | Default `approvals.mode: smart` assumes trust |
| WINH08-AUD-02 | WINH08 | Subagent / review / cron / heartbeat invoke tools off the live tool-round |
| WINH08-AUD-06 | WINH08 | Those callers do not share the live human/`smart` gate |
| WINH08-AUD-10 | WINH08 | OBSERVATION: cron is a full unsupervised agent (danger default-deny) |
| WINH10-AUD-06 | WINH10 | Live gateway reply is autonomous send on the inbound channel |
| WINH10-AUD-07 | WINH10 | Host send paths (`hermes send`, cron delivery, MCP `messages_send`) have no two-step confirm |

**Two-finding link (not a separate theme):** `WINH07-AUD-06` (no contact/third-party escalation class) and `WINH10-AUD-06` (autonomous channel reply) are the same “contacting a person” class of action, recorded once as a missing permission class and once as a missing confirm UX.

**Significance.** Live Surface 3 turns do have a persist→execute→approval pipeline (`WINH08-AUD-05` `[MATCH]`). Background, scheduled, gateway-inbound, and host-send paths consistently use different callbacks or no confirm at all. The live-turn gate is not a product-wide HITL.

---

## Theme 3 — Hermes’s provider-abstraction / registry pattern is a consistent strength

**Phases:** WINH06, WINH09, WINH10, WINH12.

**Contributing IDs:**

| ID | Phase | Label | What it recorded |
|---|---|---|---|
| WINH06-AUD-11 | WINH06 | `[MECHANISM]` | Plugin install is CLI/TUI with `plugin_guard`, opt-in `plugins.enabled`, capability consent |
| WINH09-AUD-03 | WINH09 | `[MATCH]` | Built-in `tts.provider` / `stt.provider` swap by config |
| WINH09-AUD-01 | WINH09 | `[PARTIAL]` | ElevenLabs built-in file + PCM streamer (wrap, don’t replace) |
| WINH10-AUD-11 | WINH10 | `[MATCH]` | Broad chat-platform coverage; WhatsApp/Signal/Twilio for “text” |
| WINH12-AUD-13 | WINH12 | `[MATCH]` | Gemini / OpenAI / Anthropic native; not Gemini-locked |
| WINH12-AUD-14 | WINH12 | `[MATCH]` | Local OpenAI-compat can run the full tool loop |
| WINH12-AUD-15 | WINH12 | `[MATCH]` | Live `/model` switches provider+model (cites `WINH06-AUD-25`) |
| WINH12-AUD-16 | WINH12 | `[MATCH]` | Transports normalize to `NormalizedResponse` |

**Related `[PARTIAL]`, not the theme’s core:** `WINH07-AUD-10` (shared `resolve_runtime_provider` ladder; review/delegation may pick independently) — a routing caveat on the same ladder, not a missing registry.

**Significance.** Across voice, messaging, plugins, and conversational models, Hermes already swaps vendors by config/registry rather than baking one SDK into the agent loop. WINH12 Half B is the strongest statement of this; WINH09 and WINH10 show the same pattern on I/O. That is one architectural fact, not four coincidences. Remaining work on those surfaces is wrapping, pin/policy, or (for voice identity and message *intelligence*) unrelated scratch layers.

---

## Theme 4 — Single-delivery-path / single-speech-authority tension

**Phases:** WINH07, WINH10, WINH12 (WINH08 supplies the worker-execute half of the same fact).

**Contributing IDs:**

| ID | Phase | What it recorded |
|---|---|---|
| WINH07-AUD-01 | WINH07 | Primary `message.complete` exists; `review.summary`, notices, heartbeat turns, child completes also speak |
| WINH07-AUD-02 | WINH07 | Background-review fork emits user-facing `review.summary` / `_safe_print` |
| WINH07-AUD-04 | WINH07 | No Response Governor / named core; `_emit` is a transport helper |
| WINH08-AUD-02 | WINH08 | Workers invoke tools (and therefore can produce user-visible effects) off the live round |
| WINH10-AUD-06 | WINH10 | Gateway inbound reply is an autonomous send — another delivery path |
| WINH12-AUD-17 | WINH12 | Relational Intelligence requires one delivery path; Hermes already has several (cites `WINH07-AUD-01` / `02`) |

The WINH00 prompt named `WINH09-AUD-06` as “gateway reply is autonomous send.” That ID is the chained STT/TTS pipeline (`[PARTIAL]`), not a send-authority finding. The autonomous-send finding is `WINH10-AUD-06`. Theme membership uses the latter.

**Significance.** Zola’s Response Governor / RIL “prompt injection or initiative queue only” / confirmed-send UX all assume one code path that may address the user. Hermes has a real primary path (`message.complete` / `WINH03-AUD-03`) and several additional emitters (review, heartbeat/loop, child sid, gateway `adapter.send`). Filtering Surface 3 events in a client is a wrap; covering review + heartbeat + inbound channels + children is the same missing governor showing up in three domains.

---

## Theme 5 — No single inventory of capabilities, routing surfaces, or scheduled jobs

**Phases:** WINH06, WINH07, WINH08.

**Contributing IDs:**

| ID | Phase | Layer |
|---|---|---|
| WINH06-AUD-14 | WINH06 | No single inventory of skills + tools + plugins + MCP (`tools.list` / `plugins.list` are separate) |
| WINH07-AUD-12 | WINH07 | Six inbound surfaces; routing authority not discoverable in one place (explicitly the `WINH06-AUD-14` pattern) |
| WINH08-AUD-12 | WINH08 | Cron status vs SessionDB heartbeat/loop vs kanban — no single scheduled-job list (cites `WINH06-AUD-14` / `WINH07-AUD-12`) |

**Significance.** Each phase asked a different “what is live right now?” question (allowed capabilities, who may route a request, what clocks will fire) and found the same shape: multiple real mechanisms, no unified operator index. A Windows client cannot ask Hermes one API for “everything this agent can do or will do unattended.”

---

## Theme 6 — The background-review fork is one actor across write, speech, and tools

**Phases:** WINH06, WINH07, WINH08.

**Contributing IDs:**

| ID | Phase | Facet |
|---|---|---|
| WINH06-AUD-07 | WINH06 | Post-turn fork can `skill_manage`; default `background_review.enabled: True` |
| WINH06-AUD-08 | WINH06 | Ungated skill writes on that fork |
| WINH06-AUD-23 | WINH06 | Only non-memory adaptation loop: that same fork |
| WINH07-AUD-02 | WINH07 | Same fork emits user-facing `review.summary` |
| WINH08-AUD-02 | WINH08 | Same fork invokes tools off the live tool-round |
| WINH08-AUD-06 | WINH08 | Review uses auto-deny + whitelist, not the live human gate |

WINH07 Q3 and WINH08 Q3 both ask whether this combination raises gating urgency; those questions are preserved in Audit_05, not answered here.

**Significance.** A phase-by-phase reader sees a skill-write risk, then a speech risk, then a tool-authorization risk. They are one default-on post-turn process (`agent/background_review.py`) touching three Zola authority planes (capability acquisition, speech, tool execute).

---

## Theme 7 — Surface 3 disconnect is fail-open; orphaned output and approvals still run

**Phases:** WINH02, WINH03, WINH07, WINH08.

**Contributing IDs:**

| ID | Phase | What it recorded |
|---|---|---|
| WINH02-AUD-12 | WINH02 | SSE fail-closes; JSON-RPC `client_gone` defers interrupt |
| WINH03-AUD-05 | WINH03 | Surface 3 default: healthy detached turn runs to completion (grace / activity stale) |
| WINH03-AUD-08 | WINH03 | Fail-closed requires client `session.interrupt` and/or sidecar env, not socket-drop |
| WINH07-AUD-11 | WINH07 | Orphaned output: `_DropTransport` / 512-ring / later attacher / `session_key` notify |
| WINH08-AUD-08 | WINH08 | Orphaned turn keeps gateway approval until timeout, not unattended deny |

**Significance.** The operational-contract finding is not isolated to “who owns disconnect.” It determines where speech lands after the user is gone (`WINH07-AUD-11`) and whether a danger prompt is still live with nobody watching (`WINH08-AUD-08`). Path A/B clients inherit this unless they interrupt-on-close.

---

## Theme 8 — Technical session identity is not Zola session / device / relational-boundary identity

**Phases:** WINH03, WINH05, WINH12.

**Contributing IDs:**

| ID | Phase | What it recorded |
|---|---|---|
| WINH03-AUD-09 | WINH03 | Crash loses live `_sessions` + 512-ring; `session.resume` reloads durable transcript, new agent |
| WINH05-AUD-14 | WINH05 | Explicit `sessions` row; no `deviceId`; live sid ≠ durable id |
| WINH05-AUD-15 | WINH05 | Shared ID shape, many mint sites, plus runtime uuid |
| WINH05-AUD-16 | WINH05 | WS orphan/resume ≠ Zola 30s app-background close |
| WINH05-AUD-17 | WINH05 | Profile/connection scoped, not user+device provenance |
| WINH12-AUD-02 | WINH12 | No relational `SessionBoundaryResolver` (cites `WINH03-AUD-09`, `WINH05-AUD-15`) |

**Two-finding link:** `WINH05-AUD-18` (MEMORY.md writes unstamped) plus `WINH04-AUD-01` (collapsed layers) — memory is not session-keyed; only two phases.

**Significance.** Hermes *does* persist sessions and resume transcripts. That store is wrap-able for a chat log. It is not a single-mint `SessionRecord`, not device-provenanced, and not the “last session ended at” boundary Relational Intelligence needs. WINH12’s SessionBoundaryResolver gap is the same identity split WINH03/05 already measured, applied to arcs rather than RPC.

---

## Candidate from the prompt that was not promoted to a 3-phase theme

**“Nothing is encrypted at rest, anywhere” including WINH06 skills/config as a third scored domain.** WINH06 has no encryption finding. Theme 1 states the real span (WINH04 stores + WINH10 persistence + WINH11 encryption labels) and excludes WINH06 rather than inflating it.

**`WINH09-AUD-06` as a speech-authority member.** Not used; see Theme 4.

---

## Two-finding connections (not themes)

- **SOUL.md write vs split identity strings:** `WINH06-AUD-17` / `AUD-20` make `WINH05-AUD-06` / `AUD-07` operational (agent can rewrite one identity file; other strings do not follow). Two phases.
- **DWA cited from security:** `WINH11-AUD-07` cites `WINH04-AUD-11` — restatement, not a third domain.
- **Calibration depends on SMA:** `WINH12-AUD-05` / `AUD-12` cite `WINH05-AUD-10`–`13`. Two phases; ranked as a scratch dependency in Audit_04.
- **Voice identity vs RIL deferral:** both Section 5 questions ask “initial build vs defer”; findings are different domains (`WINH09-AUD-10`–`13` vs `WINH12` Half A). Grouped in Audit_05, not merged here.

---

## Section 4 — Build-Readiness Picture

Reproduced from `Zola_WINH00_Audit_04_BuildReadinessPicture.md`. Compression of each phase Sections 2-4; ranking heuristic only; not a build plan.

## Section A — What Hermes already covers, by domain

Grouped: substantially covered first, then partial, then largely uncovered.

### Substantially covered

**WINH12 — Model provider flexibility (Half B).** Gemini, OpenAI, and Anthropic are native adapters; local OpenAI-compat (LM Studio / Ollama / vLLM / llama.cpp as `custom`/`local`) can run the full tool loop; live `/model` switches provider+model mid-session; transports normalize to `NormalizedResponse`. Findings: `WINH12-AUD-13`, `AUD-14`, `AUD-15`, `AUD-16` (all `[MATCH]`). WINH12 synthesis: configure adapters; do not rebuild a vendor lock-in layer. Related: `WINH06-AUD-25` (`/model` is a human slash; toolsets do not follow model id).

**WINH10 — Messaging channel transport (substrate only).** Gateway adapters plus host `send_message` helpers cover WhatsApp, Signal, Twilio SMS, IMAP/SMTP email, and other chat platforms. `send_message` is not model-callable (`WINH10-AUD-05` `[MATCH]`, `WINH10-AUD-11` `[MATCH]`). Message *intelligence* is not covered (Section C).

**WINH09 — Chained voice I/O and TTS/STT registry.** ElevenLabs TTS (file + PCM streamer) and ElevenLabs Scribe STT are built-in; `tts.provider` / `stt.provider` swap by config (`WINH09-AUD-03` `[MATCH]`). Chained VAD → file STT → `voice.transcript` → client `prompt.submit` → TTS matches Master Plan §3’s current sequential model (`WINH09-AUD-05`, `AUD-06` `[PARTIAL]` wrap). Barge-in exists (`WINH09-AUD-08` `[MATCH]`). Voice *identity* and directed-speech are not covered (Section C).

**WINH08 — Live-turn tool pipeline; no speculative execute.** User-initiated Surface 3 turns persist → execute → guards/approval → result (`WINH08-AUD-05` `[MATCH]`). No speculative tool pre-execute (`WINH08-AUD-07` `[MATCH]` by absence). Memory prefetch does not speculatively durable-write (`WINH08-AUD-14` `[MATCH]`). Cron exists as a real 60s ticker + `jobs.json` (`WINH08-AUD-09` OBSERVATION) — that is coverage of *a* scheduler, not Agent 14/15.

**WINH02 / WINH03 — JSON-RPC agent-loop contract and turn trace.** Surface 3 JSON-RPC is the first-party catalog Desktop/TUI/dashboard already use (`WINH02-AUD-01`, `AUD-08` `[MATCH]`). One named-function turn chain; `message.complete` carries full text (`WINH03-AUD-02`, `AUD-03` `[MATCH]`). Sidecar spawn `hermes serve` exists (`WINH02-AUD-09`). `apps/shared` is consumable via `file:` (`WINH03-AUD-13`). Standing caveat: contract is un-semvered (`WINH02-AUD-02` HIGH).

**WINH01 — Native Windows runtime (usable, not full parity).** CLI, gateway, TUI, Electron desktop, cron, browser tool, MCP, most extras install via `install.ps1` without WSL (`WINH01-AUD-08` `[MATCH]` for core install). Series conclusion: treat native Windows as `[PARTIAL]` (`WINH01-AUD-01`). Hard refuse: Matrix E2EE on win32 (`WINH01-AUD-02` HIGH).

**WINH04 — Skills filesystem backend.** Skills live in a separate backend from fact-memory (`WINH04-AUD-08` `[MATCH]`), with ledger/rollback (`WINH06-AUD-04`, `AUD-06`).

**WINH11 — Local-first process/desktop posture (inventory).** Electron renderer hardening, per-user NSIS, user-level runtime, HTTPS verify default, no always-on telemetry, replaceable (unsigned) update orchestrator (`WINH11-AUD-17`–`22`, `AUD-15`, `AUD-19`). Not a shipped-product security bar (Section C).

**WINH05 — Session row exists; SMA prohibition on showing confidence numbers holds by absence.** Durable `sessions` in `state.db` (`WINH05-AUD-14` `[PARTIAL]` wrap). `WINH05-AUD-13` `[MATCH]` (no user-facing belief-confidence numbers).

### Partially covered

**WINH04 — Memory as a single-user notebook, not Hierarchy 0–6.** Durable MEMORY.md/USER.md, char caps, threat scan, per-entry remove, optional `write_approval` (off by default), optional one memory provider, holographic decay as retrieval weight only. Findings `WINH04-AUD-01` `[PARTIAL]` plus HIGH gaps `AUD-03`, `AUD-05`, `AUD-06`.

**WINH05 — Configurable persona, not locked seed + Style Profile + SMA.** SOUL.md + overlays + `system_prompt.py` tiers (`WINH05-AUD-02` `[PARTIAL]`). No Identity Seed, no interaction-driven style, no SMA (`AUD-01`, `AUD-03`, `AUD-10`, `AUD-12`).

**WINH07 — Primary speech path and danger overlay, not Governor / §13 / Truth Ownership.** `message.complete` is real but not exclusive (`WINH07-AUD-01` `[PARTIAL]`). Toolsets + `approvals.mode: smart` (`AUD-05`, `AUD-06`, `AUD-07`). Surfaces 2+3 share a dispatcher; four others do not (`AUD-09`).

**WINH06 — Skill authoring and plugin/MCP install exist; gates default off or human-CLI.** Mechanisms (`AUD-01`, `AUD-09`, `AUD-11`, `AUD-15`, `AUD-18`, `AUD-23`, `AUD-25`) with HIGH risks on defaults (`AUD-02`, `AUD-07`, `AUD-08`, `AUD-10`, `AUD-13`, `AUD-17`, `AUD-20`). No Zola Document of Truth for this domain.

**WINH03 — Resume and interrupt exist; Surface 3 default is fail-open.** `session.resume` reloads transcript (`WINH03-AUD-09` `[PARTIAL]`). Fail-closed needs client interrupt (`AUD-05`, `AUD-08` HIGH). Path B (`hermes serve`) and Path C (`hermes gateway` + API) cannot share one process (`AUD-01`).

**WINH11 Half A — Secrets isolation and TLS defaults, not app-level encryption or signing.** Profile-scoped secrets, Fernet vault, opt-in `safeStorage`, credential-file refuse, `verify=True` (`WINH11-AUD-02`, `AUD-03`, `AUD-08`, `AUD-11` `[PARTIAL]`). Plaintext `.env` / `state.db` / memory (`AUD-01`, `AUD-04`, `AUD-05` HIGH). Unsigned Windows (`AUD-12`, `AUD-14`).

### Largely uncovered

**WINH12 Half A — Relational Intelligence Layer.** Near-total `[GAP]`: no elapsed-time-to-meaning, SessionBoundaryResolver, ThreadArcClassifier, TemporalRecencyFormatter, social graph, RelationshipArc, Calibration (`WINH12-AUD-01`–`03`, `AUD-05`–`12`). Hermes has dates in the prompt and flat memory files; those are not this layer.

**WINH09 Phase 4 — Voice identity and Conversational Attention Authority.** No speaker tracker, enrollment, per-utterance speaker field; wake-word is the primary gate, not directed-speech (`WINH09-AUD-10`, `AUD-11`, `AUD-14` HIGH; `AUD-13`, `AUD-15`).

**WINH10 — Message intelligence.** No signal-extract-then-discard, no thread-velocity, no two-step confirmed send (`WINH10-AUD-02`, `AUD-06`, `AUD-07` HIGH; `AUD-03`).

**WINH07 — Response Governor, cross-surface routing singleton, Trust/Permission Framework, Truth/Speech split.** `WINH07-AUD-04`, `AUD-09`, `AUD-13`–`15` HIGH.

**WINH05 — Self-Model Awareness and locked identity.** `WINH05-AUD-01`, `AUD-03`, `AUD-10`, `AUD-12`.

**WINH04 — Retention, visibility/sacred classes, DWA, context isolation, fact audit log.** `WINH04-AUD-03`, `AUD-05`, `AUD-06`, `AUD-11`, `AUD-12`, `AUD-14`.

---

## Section B — What needs a Zola-built adapter layer (wrap, don’t replace)

Consolidated from each phase’s “adapter” section. Grouped by domain.

### Native Windows / surfaces / operational contract (WINH01–03)

| IDs | Wrap | Adapter owns |
|---|---|---|
| WINH01-AUD-01, AUD-07 | Native install + Git Bash/ConPTY | Do not assume Matrix E2EE (`AUD-02`) or CJK FTS (`AUD-06`); treat dashboard `/chat` docs vs ConPTY as a known conflict (`AUD-03`) |
| WINH02-AUD-01, 08, 09, 10, 11 | JSON-RPC + `apps/shared` + sidecar spawn | Pin Hermes tag / probe methods (`AUD-02`); re-theme vs new shell is an open path question, not decided here |
| WINH03-AUD-02, 03, 04, 12, 13 | Turn chain, `message.complete`, approval cards, `file:` shared client | Implement `approval` / `clarify` / `sudo` handlers; interrupt-on-close if fail-closed is required (`AUD-05`/`08`) |
| WINH03-AUD-09, WINH05-AUD-14, AUD-16 | `state.db` sessions + resume | Client policy for start/end/grace; do not assume 30s backgrounding |

### Memory & skills (WINH04)

| IDs | Wrap | Adapter owns |
|---|---|---|
| WINH04-AUD-01, AUD-02 | Builtin files + optional provider | Product config: `write_approval` on; default `memory.provider = ""` unless a vendor is chosen; box or disable `sync_turn` second writer |
| WINH04-AUD-04, AUD-10 | `remove` / `memory reset` / skill error visibility | Deletion orchestrator across builtin / provider / `state.db`; optional `skills.disabled` on runtime failure |
| WINH04-AUD-08 | Skills filesystem | Keep Hermes storage; default `skills.write_approval: true` is adapter/policy |

### Identity & session (WINH05)

| IDs | Wrap | Adapter owns |
|---|---|---|
| WINH05-AUD-02, AUD-06 | SOUL.md / `_identity_parts` | Projection of a Zola identity object into the stable tier, or inject via `system_message`; disable conflicting `/personality` builtins |
| WINH05-AUD-14, AUD-16, AUD-18 | `sessions` row + `messages.session_id` | Conversation key wrapping; stamp or side-index memory writes |

### Capability acquisition (WINH06)

WINH06 Section 4 is a *candidate* list pending a domain architecture document (open question). Adapter-shaped items the phase named: flip `skills.write_approval`; pin review whitelist / disable review; fail closed instead of `terminal` MCP/plugin/config fallbacks; `allow_lazy_installs: false`; close HERMES_HOME SOUL.md exemption. IDs: `WINH06-AUD-02`, `AUD-08`, `AUD-10`, `AUD-15`, `AUD-17`, `AUD-21`.

### Authority / tools / schedule (WINH07–08)

| IDs | Wrap | Adapter owns |
|---|---|---|
| WINH07-AUD-01, AUD-02, AUD-11 | `message.complete` vs extra emits | Filter `review.summary` / notices / heartbeat / child completes; interrupt-on-disconnect |
| WINH07-AUD-03, AUD-05, AUD-06, AUD-08 | `running` + approvals overlay | Permission document mapped onto toolsets/`approvals.*`; optional `busy_input_mode=queue` |
| WINH07-AUD-10 | `resolve_runtime_provider` | Pin one runtime per session; ignore independent review/delegation pickers if product forbids them |
| WINH07-AUD-07 | `approvals.mode` | Product profile can set `manual` / `off` (mitigation, not a Framework) |
| WINH08-AUD-01, AUD-04, AUD-06, AUD-11 | delegate / review cancel / cron claim | Which workers even start; `subagent_auto_approve: false`; `cron_mode: deny` |
| WINH08-AUD-05 | Live `run_tool_round` | Keep as invoke engine for user-initiated turns |
| WINH08-AUD-13 | `prefetch_all` | Optional TTL-stamp / strip so live memory-tool results win |

### Voice (WINH09)

| IDs | Wrap | Adapter owns |
|---|---|---|
| WINH09-AUD-01, AUD-03, AUD-04 | Built-in TTS/STT registry + ElevenLabs streamer | Pin provider; measure latency outside Hermes |
| WINH09-AUD-02 | STT ABC / `type: command` | Only if Cartesia/Deepgram streaming is required |
| WINH09-AUD-05, AUD-06, AUD-08, AUD-16 | Gateway `voice.*` + barge-in | Windows owns capture (`client_direct` / local mic); continuation window is client-side |
| WINH09-AUD-07 | `voice_live_context`; optional GPT-Live | Do not treat as Gemini Live |
| WINH09-AUD-09 | One mic/speaker per process | Single JSON-RPC owner of capture |

### Messaging (WINH10)

| IDs | Wrap | Adapter owns |
|---|---|---|
| WINH10-AUD-01, AUD-04 | Allowlists / pairing | Map “known contact”; separate analysis-consent flag |
| WINH10-AUD-05, AUD-11 | `send_message` host helpers | Keep out of the model toolset |
| WINH10-AUD-09, AUD-10 | Twilio SMS; IMAP/SMTP email | Channel choice is Section 5; Graph in this tag is Teams not Outlook mail |
| WINH10-AUD-06, AUD-07 | `adapter.send` / CLI / cron delivery | Two-step confirm UX in front of these APIs |

### Security & deployment (WINH11)

| IDs | Wrap / harden | Adapter owns |
|---|---|---|
| WINH11-AUD-02, AUD-03 | Fernet vault; opt-in `safeStorage` | DPAPI/Credential Manager wrap; default `safeStorage` on |
| WINH11-AUD-06, AUD-08, AUD-10, AUD-11 | SPA token; TLS; MCP env dump; credential_files | User gate on data-mgmt; refuse `http://` base_url; per-MCP env allow-list; Tier 1/2 grant |
| WINH11-AUD-12, AUD-14, AUD-16 | Unsigned build; custom git/zip update | Authenticode + signed feed / checksum (Zola pipeline — Hermes will not sign this tag) |
| WINH11-AUD-13, AUD-20 | Uninstall leftovers; `--no-sandbox` fallback | Purge `HERMES_HOME` tool; product policy on sandbox fallback |

### Relational intelligence / models (WINH12)

| IDs | Wrap | Adapter owns |
|---|---|---|
| WINH12-AUD-04 | `hermes_time` vs `time.time` vs UTC | Single UTC epoch if RIL is built |
| WINH12-AUD-15, AUD-16 | `/model` + `NormalizedResponse` | Pin toolsets independently of vendor; register new transports rather than a Gemini-shaped schema |
| WINH12-AUD-17 | Extra speech paths | If RIL in scope: constrain to prompt injection; quarantine `review.summary` (`WINH07-AUD-02`) |

No Half A `[PARTIAL]` to wrap — Social Graph / Continuity are not projections of MEMORY.md.

---

## Section C — What must be built from scratch, ranked

Every confirmed scratch item from phase Section 4, then ordered by (a) HIGH findings that depend on it, (b) whether other scratch items depend on it, (c) whether a phase already flagged deferral. Foundational / most-depended-upon first.

**Prerequisite call-outs (confirmed from citations, not assumed):**

- **Temporal Reasoning is a prerequisite for Calibration and for honest Continuity recency.** `WINH12-AUD-12` states Calibration’s dependency chain is unmet at every link; WINH12 Section 5 Q1: “Temporal is foundational; Calibration cannot be honest without it.” IDs: `WINH12-AUD-01`, `AUD-03` (and clock hygiene `AUD-04` if RIL ships).
- **Self-Model Awareness is a prerequisite for Calibration as specified.** `WINH12-AUD-05` and `AUD-12` cite `WINH05-AUD-10`–`13`. WINH12 Section 5 Q4 asks whether a proxy (session count) is even allowed; that is undecided. Scratch SMA: `WINH05-AUD-10`, `AUD-11`, `AUD-12`.
- **SessionBoundaryResolver depends on a stable notion of session end**, already split in `WINH03-AUD-09` / `WINH05-AUD-15` (`WINH12-AUD-02` cites both).
- **RelationshipArc / familiarity modes depend on Style Profile + depth signals** (`WINH12-AUD-11` cites `WINH05-AUD-03` / `AUD-08`) and on a graph (`AUD-06`–`09`).
- **Single-path RIL / confirmed-send / Governor sit on the same missing speech authority** (`WINH07-AUD-04` plus extras in `AUD-01`/`02`; `WINH12-AUD-17`; `WINH10-AUD-06`/`07`).

**Deferral candidates already flagged by a phase (not decided here):** voice identity (`WINH09` Section 5 Q3, citing `WINH09-AUD-10`–`13`); Relational Intelligence subsystems, Calibration in particular (`WINH12` Section 5 Q1); literal SMS channel strategy (`WINH10` Section 5 Q1); on-box training loop as explicit non-goal (`WINH06` Section 4 item 12, `WINH06-AUD-22`); Distributed Presence E2E (`WINH11-AUD-09`, out of series).

### Ranked list

1. **Durable session / identity mint seam (technical).** Single mint + durable vs live sid + device provenance if the product requires `SessionRecord`. Scratch: `WINH05-AUD-15`, `AUD-16`, `AUD-17`; resume integrity still `[UNVERIFIED]` (`WINH03-AUD-10`). **Prerequisite for** relational SessionBoundaryResolver (item 6) and for stamping memory writes (`WINH05-AUD-18`). HIGH: `WINH05-AUD-15` (1 HIGH).

2. **Memory hierarchy, visibility/sacred classes, retention, DWA, context isolation, fact audit log.** Scratch: `WINH04-AUD-03`, `AUD-05`, `AUD-06`, `AUD-07`, `AUD-11`, `AUD-12`, `AUD-14` (plus cascade remainder of `AUD-04`). `WINH11-AUD-07` restates DWA. **Prerequisite for** social-graph stores, comms retention (`WINH10-AUD-13`), and any typed Layer 5 preferences (`WINH05-AUD-05` additive to `WINH04-AUD-01`). HIGH: `WINH04-AUD-03`, `AUD-05`, `AUD-06` (3 HIGH) plus DWA MEDIUM that later phases treat as blocking for §9.

3. **Locked Identity Seed + canonical identity object + Style Profile (context-scoped, bounded).** Scratch: `WINH05-AUD-01`, `AUD-03`, `AUD-04`, `AUD-05`, `AUD-08`, `AUD-09` and consolidation of split strings `AUD-06`/`AUD-07` (HIGH/MEDIUM). `WINH06-AUD-17`/`AUD-19`/`AUD-20` add that the agent can rewrite SOUL.md with no draft/ledger. **Prerequisite for** Continuity warmth/familiarity (`WINH12-AUD-11`). HIGH: `WINH05-AUD-01`, `AUD-03`, `AUD-05`, `AUD-06` (4 HIGH) plus `WINH06-AUD-17`, `AUD-19`, `AUD-20` (3 HIGH) if identity self-mod is in the same bucket.

4. **Self-Model Awareness (read-only `SelfBeliefBlock`, computed hedging, no memory-write / no direct speech).** Scratch: `WINH05-AUD-10`, `AUD-11`, `AUD-12`. **Prerequisite for** Calibration as specified (`WINH12-AUD-05`, `AUD-12`). HIGH: `WINH05-AUD-10` (1 HIGH) but unblocks `WINH12-AUD-05`, `AUD-12` (2 HIGH).

5. **Response Governor / Truth Ownership / Speech Authority (one utterance path; structured facts ≠ phrasing).** Scratch: `WINH07-AUD-04`, `AUD-13`, `AUD-14`, `AUD-15` (and extras `AUD-01`/`AUD-02`). **Prerequisite for** RIL single-path (`WINH12-AUD-17`), for treating review/heartbeat/child as non-speech, and for a clean confirmed-send layer in front of gateway replies. HIGH: `WINH07-AUD-01`, `AUD-02`, `AUD-04`, `AUD-13`, `AUD-14`, `AUD-15` (6 HIGH).

6. **Temporal Reasoning + SessionBoundaryResolver + shared RIL contracts.** Scratch: `WINH12-AUD-01`, `AUD-02`, `AUD-03`, `AUD-05`; clock `AUD-04` if this ships. **Prerequisite for** Continuity injection, salience-over-time, and Calibration. HIGH: `AUD-01`, `AUD-02`, `AUD-03`, `AUD-05` (4 HIGH).

7. **Core Rule enforcement on workers (prepare vs execute) + tool-authorization product policy.** Scratch: `WINH08-AUD-02` (workers *are* executors); Agent 14 remainder `AUD-04`; staleness metadata `AUD-03`; unified schedule inventory `AUD-12`. Adapter can *disable* workers; a Zola core that prepares only is not in Hermes. HIGH: `WINH08-AUD-02`, `AUD-06` (2 HIGH), plus the review fork HIGH cluster in WINH06/07.

8. **Trust / Permission Framework (§13) as its own document and runtime.** Danger overlay is wrap (`WINH07-AUD-05`–`08`); the Framework, escalation-as-contact, and inspectable catalog are scratch (`AUD-05` remainder, `AUD-06`, `AUD-08` audit). Cross-surface routing singleton is scratch (`WINH07-AUD-09`, `AUD-12`). HIGH: `WINH07-AUD-07`, `AUD-09` (2 HIGH) plus MEDIUM catalog gaps.

9. **Confirmed-action / two-step send UX (messaging + any irreversible host action).** Scratch: `WINH10-AUD-06`, `AUD-07`. Contact-gate remainder is adapter on `AUD-01`. HIGH: 2 (`AUD-06`, `AUD-07`). Depends on knowing which speech/send paths exist (item 5 / Theme 4).

10. **Social Graph + RelationshipArc + `[CONTINUITY]` injection.** Scratch: `WINH12-AUD-06`, `AUD-07`, `AUD-08`, `AUD-09`, `AUD-10`. Depends on items 2 and 6 (typed memory + temporal/session boundary). HIGH: `AUD-06`, `AUD-07`, `AUD-09`, `AUD-10` (4 HIGH) + `AUD-08` MEDIUM.

11. **Relational Calibration (modes, damper, assumption license, repair register).** Scratch: `WINH12-AUD-11`, `AUD-12`. **Depends on items 4, 6, and 10** (SMA + Temporal + Continuity/depth). Phase-flagged **deferral candidate** (WINH12 Q1, Q4). HIGH: `AUD-11`, `AUD-12` (2 HIGH) that cannot be honestly closed first.

12. **Message-intelligence layer (signals, velocity, analysis consents, comms retention).** Scratch: `WINH10-AUD-02`, `AUD-03`, `AUD-04` remainder, `AUD-13`. Independent of whether Twilio vs WhatsApp is chosen (WINH10: do not merge (a) and (b)). HIGH: `AUD-02` (1 HIGH).

13. **Voice identity + directed-speech / addressee confidence.** Scratch: `WINH09-AUD-10`, `AUD-11`, `AUD-12` (constraint), `AUD-13`, `AUD-14`, `AUD-15`. Phase-flagged **deferral candidate** (WINH09 Q3). HIGH: `AUD-10`, `AUD-11`, `AUD-14` (3 HIGH) that drop out of a build plan *if* deferred — still findings of record.

14. **Application-level encryption of credentials, `state.db`, and memory files — if BitLocker is not accepted as sufficient.** Scratch: `WINH11-AUD-01`, `AUD-04`, `AUD-05`. WINH11 Q2/Q4 leave OS-disk vs SQLCipher/DPAPI undecided. HIGH: 3. Not a prerequisite for RIL *logic*, but a ship-bar candidate (WINH11 Q3).

15. **Windows code-signing identity + authenticated update channel.** Scratch: `WINH11-AUD-12`, `AUD-14`, `AUD-16`. Recommendation-shaped fact from WINH11: Hermes will not sign Windows for you in this tag. HIGH: 3. Ship-bar candidate (WINH11 Q1, Q3).

16. **Capability-acquisition product controls that Hermes does not have:** dry-run/quarantine for `skill_manage` (`WINH06-AUD-03` HIGH `[ABSENT]`), draft/review for identity/config (`AUD-19` HIGH `[ABSENT]`), unified capability inventory (`AUD-14`), sandbox for new MCP/plugins (`AUD-13` HIGH). WINH06 Q1: without a domain architecture doc these stay “candidates,” not a scored Zola miss.

17. **Agent 8/4/9 warm-start with live-wins** — only if Windows wants that model (`WINH08-AUD-07` is a MATCH by absence; `AUD-13` has no live-wins). WINH08 Q4 is the product choice. Not a Hermes gap of “must add speculation.”

18. **Agent 15 Daily Brief pipeline** — scratch *if* Windows needs prepare-only briefs; Hermes cron is a full agent (`WINH08-AUD-09`/`AUD-10`). WINH08 Q2.

**Filtered out of scratch (phase Section 4 exclusions, restated):** `WINH05-AUD-13`; `WINH11-AUD-09` (out of series); `WINH11-AUD-17`/`18`/`19`/`21`/`22` (mechanisms that exist); `WINH11-AUD-15` (updater exists; gap is `AUD-16`); `WINH12-AUD-13`–`16`; WINH10 literal handset SMS (platform constraint; Twilio already exists — `WINH10-AUD-09` / `AUD-12`); Cognitive Engine / Environmental Awareness (recorded scope decisions).

**JSON-RPC semver (`WINH02-AUD-02` HIGH)** is not a Zola module; it is a packaging/pin policy on whatever path is chosen. **Fail-open disconnect (`WINH03-AUD-05`/`08`)** is client interrupt policy (adapter) unless a new Hermes default is forked.

---

## Domain one-liners (index)

| Domain | Coverage | Dominant IDs |
|---|---|---|
| WINH01 Native Windows | Partial — runnable, not parity | AUD-01 PARTIAL; AUD-02 HIGH GAP |
| WINH02 Surfaces | JSON-RPC covered; contract unversioned | AUD-01/08 MATCH; AUD-02 HIGH RISK |
| WINH03 Operational contract | Turn/resume MATCH/PARTIAL; disconnect HIGH | AUD-02/03; AUD-05/08 |
| WINH04 Memory & skills | Notebook + skills FS; hierarchy scratch | AUD-08 MATCH; AUD-03/05/06 HIGH |
| WINH05 Identity / SMA | Persona file wrap; SMA/seed scratch | AUD-02 PARTIAL; AUD-01/10 HIGH |
| WINH06 Capability acquisition | Mechanisms exist; defaults HIGH risk | AUD-01 MECHANISM; AUD-02/07 HIGH |
| WINH07 Authority | Primary path PARTIAL; Governor scratch | AUD-01 PARTIAL; AUD-04/13–15 HIGH |
| WINH08 Tools / schedule | Live pipeline MATCH; workers execute | AUD-05 MATCH; AUD-02/06 HIGH |
| WINH09 Voice | Chained I/O MATCH/PARTIAL; identity scratch | AUD-03/08 MATCH; AUD-10/11/14 HIGH |
| WINH10 Messaging | Transport MATCH; intelligence scratch | AUD-05/11 MATCH; AUD-02/06/07 HIGH |
| WINH11 Security / deploy | Local-first foundation; crypto/signing scratch | AUD-19 MECHANISM; AUD-01/04/05/12/14/16 HIGH |
| WINH12 RIL / providers | Providers MATCH; RIL scratch | AUD-13–16 MATCH; AUD-01–03/05–07/09–12 HIGH |

---

## Section 5 — Decisions Needed Before a Build Plan Can Be Written

*"These are not resolved in this document. Per the project's Phase SOP, they get decided in conversation between the developer and Claude — Decisions Locked — before any build plan is written. This list is the complete input to that conversation."*

Reproduced from `Zola_WINH00_Audit_05_DecisionsNeeded.md`. Grouping is a first pass; original question texts and origin-phase IDs are preserved.

**Coverage of Section 5 sources**

| Phase | Synthesis heading | Questions pulled |
|---|---|---|
| WINH01 | None (`Zola_WINH01_Audit_02_WindowsRuntime.md` roll-up only) | 0 — no Section 5 |
| WINH02 | No Section 5; document states WINH00 records the path decision | 1 (integration path A/B/C/D) |
| WINH03 | No Section 5; “No path is recommended here” + Path C resume still unresolved | 1 remainder (Path C `/api/sessions` if Path C is considered) |
| WINH04 | “Open questions for WINH00” | 6 |
| WINH05–12 | “Section 5 — Open questions for WINH00” | 4 each (WINH05 has 5) |

WINH05 has five numbered questions. WINH06–12 have four each. WINH04 has six. Plus WINH02 path decision and WINH03 Path C resume caveat.

---

## Scope / deferral decisions

Questions that ask what is in the initial Zola-Windows build versus deferred (or out of series).

### S1 — Voice identity in or deferred
**Origin:** WINH09 Section 5 Q3. **IDs:** `WINH09-AUD-10`, `AUD-11`, `AUD-12`, `AUD-13` (Phase 4 near-total gap); related `AUD-14`, `AUD-15`.

> Phase 4 is a near-total capability gap (`WINH09-AUD-10`–`13`). Is a Windows-native voiceprint system in scope for this integration at all, or is it deferred the way environmental awareness was for the whole series? If deferred, record it under “Recorded scope decisions” so WINH10–12 / WINH00 do not re-raise it.

*(WINH10–12 did not re-score voiceprint. The deferral itself was never written into “Recorded scope decisions.” That recording is still outstanding if the answer is defer.)*

### S2 — Relational Intelligence Layer in or deferred
**Origin:** WINH12 Section 5 Q1. **IDs:** Half A `WINH12-AUD-01`–`03`, `AUD-05`–`12`; Calibration call-out `AUD-11`, `AUD-12`.

> Given near-total Half A gap: is the full five-subsystem Relational Intelligence Layer in scope for Zola-Windows’s initial build, or should some subsystems (Calibration in particular — most downstream, depends on Continuity + SMA + Temporal, all unmet) be deferred, as voice identity was flagged in `WINH09`? Temporal is foundational; Calibration cannot be honest without it.

Grouped with S1 because both ask “initial build vs defer,” **not** merged: WINH09 frames *voiceprint/enrollment/speaker field*; WINH12 frames *five RIL subsystems and Calibration’s dependency chain*.

### S3 — Calibration vs SMA: blocked or proxy
**Origin:** WINH12 Section 5 Q4. **IDs:** `WINH12-AUD-12`; SMA `WINH05-AUD-10`–`13`.

> Calibration depends on SMA confidence/correction signals (`WINH05-AUD-10`–`13`) that do not exist. Is Calibration blocked until those WINH05 gaps close, or can a first version use a standalone proxy (e.g. session count only) knowing that is **not** the architecture as specified?

### S4 — Literal SMS / “text the user” channel strategy
**Origin:** WINH10 Section 5 Q1. **IDs:** `WINH10-AUD-09`, `AUD-11`, `AUD-12`.

> Twilio SMS (already in Hermes), WhatsApp/Signal as the practical “text the user” channel, or defer carrier-SMS-equivalent the way WINH09 flagged voice identity as a possible deferral?

Grouped with S1 as a deferral-shaped channel question; original WINH10 framing (Twilio vs WhatsApp/Signal vs defer) preserved.

### S5 — Full-duplex voice transport in or not
**Origin:** WINH09 Section 5 Q2. **IDs:** `WINH09-AUD-07`.

> Is native full-duplex audio (Gemini-Live-style) actually a Windows-track requirement, given Master Plan §3’s current model is STT → Reasoning → TTS? Hermes’s GPT-Live is OpenAI, not Gemini, and chained mode already matches the current sequential model. If duplex is only a zola-main/Android detail, `WINH09-AUD-07` is a non-issue for Windows, not a gap to close.

### S6 — Warm-start / speculation vs Agent Map
**Origin:** WINH08 Section 5 Q4. **IDs:** `WINH08-AUD-07`, `AUD-13`.

> Hermes is not Agent 8/4/9 (`AUD-07`, `AUD-13`). Should the Windows client add a warm-cache for responsiveness, or accept less speculative behavior than the Android Agent Map (zola-main remains out of scope; this is a Windows-track product choice)?

### S7 — Hermes cron vs Zola sidecar for scheduled work
**Origin:** WINH08 Section 5 Q2. **IDs:** `WINH08-AUD-09`, `AUD-10`, `AUD-11`, `AUD-12`.

> Hermes **has** cron (`AUD-09`), not a gap of “no scheduler.” Does the Windows track **use** Hermes cron for Agent 14/15-shaped work (knowing jobs are full unsupervised `run_conversation`s, `AUD-10`), or keep time-triggered prepare/brief in a Zola sidecar and leave Hermes cron off?

### S8 — On-box training loop as non-goal
**Origin:** WINH06 Section 4 item 12, carried in the spirit of Section 5 (WINH06 Q1 also blocks converting Section 4 to scratch vs inherit). **IDs:** `WINH06-AUD-22`.

WINH06 Section 4: “Explicit non-goal: no on-box training loop — document `AUD-22` as accepted absence so WINH00 does not invent a Zola training requirement by accident.”

WINH06 Section 5 Q1 (architecture doc — see O1 below) is the blocker for treating the rest of Section 4 as required scratch.

### S9 — Environmental perception stays out
**Origin:** WINH04 Open questions Q6. **IDs:** none new (recorded scope decision 2026-09-21).

> Environmental perception → memory promotion stays out of series (progress “Recorded scope decisions”); WINH00 should not reopen it inside Hermes gap analysis.

### S10 — Distributed Presence E2E
**Origin:** WINH11 Section 4 exclusion / `WINH11-AUD-09`. Not a numbered Section 5 question; WINH11 filtered it from scratch as out of series. Restated here so it is not silently dropped from the deferral picture: N/A for this series, not a Zola-Windows build item here.

### S11 — WINH04 identity-memory pointer (audit subsequently happened)
**Origin:** WINH04 Open questions Q5. **IDs:** `WINH04-AUD-01` Layer 5; later `WINH05-AUD-05`.

> Identity memory (self-model, USER.md vs Zola personality docs) is **deferred to WINH05** — USER.md flattening (`Layer 5 [PARTIAL]`) will reappear there.

Preserved as written. WINH05 did run; it did **not** decide product assembly (see I1). WINH05 Q4 asks WINH00 to keep both `WINH04-AUD-01` Layer 5 and `WINH05-AUD-05`.

---

## Security / hardening decisions

Underlying question named by WINH11: what security bar Zola-Windows needs before shipping, and whether BitLocker/OS-level protection counts as sufficient for any of plaintext `.env` / `state.db` / memory files.

### H1 — Code signing
**Origin:** WINH11 Section 5 Q1. **IDs:** `WINH11-AUD-12`, `AUD-14`.

> Does Zola-Windows need its own Authenticode certificate and signing step in the release pipeline before any real distribution, given Phase 4 (`AUD-12`/`14`)? (Recommendation-shaped fact: Hermes will not sign Windows for you in this tag.)

Fact restated only: this tag ships unsigned Windows (`signAndEditExecutable: false`; no Authenticode CI). The *decision* of what Zola-Windows does about that is not made here.

### H2 — Credential storage (DPAPI / Credential Manager vs BitLocker)
**Origin:** WINH11 Section 5 Q2. **IDs:** `WINH11-AUD-01`, `AUD-02`, `AUD-03`.

> Is wrapping secrets in Windows Credential Manager / DPAPI a WINH00-scoped build requirement, or acceptable to defer given the file already sits inside a per-user-encrypted filesystem (BitLocker) on most Windows installs? This is a product/threat-model decision (local attacker with the same user token vs disk-at-rest / stolen laptop). The audit does not resolve it.

### H3 — Ship bar (blocking items)
**Origin:** WINH11 Section 5 Q3. **IDs:** `WINH11-AUD-12`, `AUD-14`, `AUD-16`, `AUD-01`, `AUD-04`, `AUD-05`, `AUD-20`.

> Given Phase 4/5: does the current Desktop posture (unsigned binary, git/zip updates without signature, Electron sandbox with a `--no-sandbox` fallback) meet a bar the developer is comfortable shipping, or are there **blocking** items for WINH00 before any build plan is finalized? Candidates for “block ship”: AUD-12/14 (signing), AUD-16 (update integrity), AUD-01/04/05 if BitLocker is rejected as sufficient.

### H4 — `state.db` / MEMORY.md encryption which Privacy Plan sentence governs
**Origin:** WINH11 Section 5 Q4. **IDs:** `WINH11-AUD-04`, `AUD-05`.

> Confirmed unencrypted (`AUD-04`). Is application-level encryption (SQLCipher) in scope for Zola-Windows, or is reliance on OS-disk encryption (BitLocker) considered sufficient per “platform-standard encryption at minimum” in Privacy Plan §9? Memory-specific bullets (“must be encrypted at rest”) are stricter than the general personal-data bullet — WINH00 should say which sentence governs `state.db` and `MEMORY.md`.

### H5 — Which WINH06 default-config RISKs block adopting Hermes defaults
**Origin:** WINH06 Section 5 Q2. **IDs:** `WINH06-AUD-02`, `AUD-08`, `AUD-10`, `AUD-21`, `AUD-17`; contrast `AUD-09`, `AUD-11`.

> Of the `[RISK]` findings in Section 3's companion list, which should block adopting Hermes's default config as-is for the Windows track, versus which are acceptable because a human operator is assumed present?
> - Strongest default-config problems if the Windows client exposes `skill_manage` + `terminal` + `write_file`: AUD-02/08 (ungated skill writes, including the review fork), AUD-10/21 (CLI fallbacks), AUD-17 (home SOUL.md).
> - More acceptable if a human is always on the desktop card and terminal is disabled: AUD-09 then covers MCP; AUD-11 covers plugins; AUD-02 still matters because background review does not need the user to type `skill_manage`.

### H6 — MCP / plugin sandbox and secret inheritance
Not a standalone Section 5 number; implied by WINH06 Q2 (`AUD-13`) and WINH11 adapter list (`WINH11-AUD-10`, `AUD-11`). WINH06: “Sandbox or reduced privilege for newly added MCP/plugins (or refuse third-party MCP on Windows until reviewed)” is Section 4 candidate 7. Listed here so `WINH06-AUD-13` / `WINH11-AUD-10` are not dropped from the hardening conversation.

---

## Provider / vendor decisions

### P1 — Conversational model: configure vs custom adapter
**Origin:** WINH12 Section 5 Q2. **IDs:** `WINH12-AUD-13`, `AUD-14`, `AUD-15`, `AUD-16`.

> Hermes already covers the Master Plan’s conversational-model targets and more. Does Zola-Windows simply configure existing adapters, or is there a reason (cost, latency, a vendor not in `providers.py`) to build a custom one?

### P2 — TTS/STT provider choice
**Origin:** WINH09 Section 5 Q1. **IDs:** `WINH09-AUD-01`, `AUD-02`, `AUD-03`, `AUD-04`.

> Given Audit_02: does Zola-Windows use Hermes’s built-in ElevenLabs TTS as-is (or Edge as the free default), or is a specific voice quality/latency requirement strong enough to warrant a custom Cartesia/Deepgram plugin from day one?

### P3 — Email channel
**Origin:** WINH10 Section 5 Q2. **IDs:** `WINH10-AUD-10`.

> IMAP/SMTP bot vs Outlook (Graph **Mail**, not the existing Teams Graph helper) vs a Gmail connector (`connections_tool` / himalaya). Which matches the user’s accounts?

### P4 — Honcho / Hindsight (or any external memory provider) in the product
**Origin:** WINH04 Open questions Q2. **IDs:** `WINH04-AUD-02`, `AUD-06`.

> Are Honcho/Hindsight allowed in the product? If yes, P-3P (provider retention, stranding, workspace sharing) becomes a shipping constraint, not a plugin footnote.

---

## Confirmed-action / authorization decisions

### A1 — Confirmed send (including live gateway replies)
**Origin:** WINH10 Section 5 Q3. **IDs:** `WINH10-AUD-06`, `AUD-07`.

> Cron/CLI-only `send_message` is **not** an adequate foundation for Zola’s two-step flow (`WINH10-AUD-07`). Does Zola-Windows build its own approval UI in front of `send_message_tool` / `adapter.send`, including **gateway chat replies** (`WINH10-AUD-06`)?

WINH10 Q4 (INFO): this phase **reinforces** `WINH08-AUD-02`/`06` (cron delivery) and does **not** raise `WINH07-AUD-07`: `smart` never wrapped host send or gateway replies. New HIGH work is `AUD-06`/`07` and `AUD-02`, not a restatement of those older IDs.

### A2 — Client-side response arbitration / extra Hermes speech
**Origin:** WINH07 Section 5 Q1. **IDs:** `WINH07-AUD-01`, `AUD-04`; also `AUD-02`.

> Hermes does **not** enforce single-authority speech internally (`AUD-01`, `AUD-04`). Does the Windows client need its own arbitration layer (drop `review.summary`, ignore child-sid completes, suppress heartbeat as Zola-speech, only paint `message.complete` from user-initiated turns)? Or is “talk to Surface 3 only and live with Hermes’s extra events” acceptable for v1?

### A3 — §13 Trust/Permission as a Zola-side layer regardless
**Origin:** WINH07 Section 5 Q2. **IDs:** `WINH07-AUD-05`, `AUD-06`, `AUD-07`, `AUD-08`.

> Phase 3 found a danger-command overlay, not a Trust/Permission Framework (`AUD-05`–`08`). Same shape as WINH04/05 open questions (compatibility projection vs Zola owns assembly): should Zola-Windows always own the permission document in front of Hermes, even if Hermes `approvals.mode` stays in the stack for terminal danger?

### A4 — Truth/speech separation required regardless of Hermes
**Origin:** WINH07 Section 5 Q4. **IDs:** `WINH07-AUD-13`, `AUD-14`, `AUD-15`.

> Hermes has no structural split (`AUD-13`–`15`). Is that acceptable for the Windows track (treat model output as both fact and phrasing, maybe with client-side display of tool cards), or does Zola-Windows need a verification/formatting layer **regardless** of Hermes’s architecture?

### A5 — Background-review combined authority (write + speak + tools)
**Origin:** WINH07 Section 5 Q3 **and** WINH08 Section 5 Q3. Both preserved.

**WINH07 Q3.** **IDs:** `WINH04-AUD-02`; `WINH06-AUD-07`/`08`/`23`; `WINH03-AUD-05`/`08`; this phase `WINH07-AUD-02`, `AUD-11`, `AUD-04`.

> Weighting vs prior “who’s in charge” findings. `WINH04-AUD-02` (second memory write authority), `WINH06-AUD-07/08/23` (background-review skill/memory writes), `WINH03-AUD-05/08` (disconnect fail-open). This phase adds: the same review fork **speaks** (`review.summary`, `AUD-02`); orphaned-turn **output routing** is drop/replay/reattach (`AUD-11`), not a restatement of fail-open; there is still no core (`AUD-04`). Are these **additive** (separate problems in the same “who’s in charge” area) or does speech+routing raise the priority of disabling/gating the review fork for the Windows track beyond the skill-write risk already recorded?

**WINH08 Q3.** **IDs:** `WINH06-AUD-07`; `WINH07-AUD-02`; `WINH08-AUD-02`, `AUD-06`.

> Background-review combined authority. `WINH06-AUD-07` (skill/memory write), `WINH07-AUD-02` (speaks via `review.summary`), and `WINH08-AUD-02/06` (tools on a whitelist, auto-deny for danger, `extra_tools` can widen). Does that combination raise gating urgency for Windows beyond WINH06/07?

Not merged into one reworded question: WINH07 asks additive-vs-priority including disconnect/orphan routing; WINH08 asks specifically whether the write+speak+tool combination raises gating urgency.

### A6 — RIL single delivery path vs Hermes multi-path
**Origin:** WINH12 Section 5 Q3. **IDs:** `WINH12-AUD-17`; `WINH07-AUD-01`, `AUD-02`.

> RIL requires prompt injection or initiative queue only. Hermes already speaks through extra paths (`WINH07-AUD-01`/`02`; `WINH12-AUD-17`). Is a single-path RIL realistic to enforce on this substrate, or does it conflict with what WINH07 already found?

Grouped with A2 (arbitration) but original RIL framing kept.

### A7 — SMA write ban vs memory-agency exception
**Origin:** WINH05 Section 5 Q3. **IDs:** `WINH05-AUD-10`, `AUD-12`.

> Hermes’s agent-writes-memory exception relaxes an analogous boundary for **plain facts**. Self-Model Awareness still requires a **read-only** introspective layer that must not write memory or fire speech. Should that SMA boundary stay **hard** on the Windows track even though fact-memory write authority was given to Hermes? Tension: putting SMA inside `AIAgent` inherits write/execute; putting it beside Hermes requires a new component the pin does not provide.

### A8 — Skills governance default-on
**Origin:** WINH04 Open questions Q4. **IDs:** `WINH04-AUD-09`; later `WINH06-AUD-02`.

> Skills governance vs WINH06: stock `write_approval: False` is recorded (`AUD-09`); WINH06 should not rediscover it — decide default-on for Zola.

WINH06 did rediscover it as `WINH06-AUD-02` (HIGH vs WINH04 MEDIUM). See C2 for the severity-pick question.

### A9 — One Windows policy vs path-dependent gating
**Origin:** WINH06 Section 5 Q3. **IDs:** `WINH06-AUD-02`, `AUD-08`, `AUD-10`, `AUD-17`, `AUD-21`; `WINH03-AUD-12`.

> One policy vs surface-dependent gating (WINH02/03 Path A/B/C/D)?
> - Path A (fork `apps/desktop`): inherits `setup_mcp` cards, `plugins.manage` RPC, slash `/model` `/personality`, and whatever toolsets the fork leaves enabled.
> - Path B (`hermes serve` / JSON-RPC): same gateway gates **if** the Windows client implements the consent/approval methods; otherwise timeouts skip/deny per `WINH03-AUD-12`.
> - Path C (HTTP API only): no desktop card, no slash commands; agent tool surface is whatever the API session enables — `setup_mcp` will tell the model to use `terminal` (`AUD-10`) if terminal exists.
> - Path D (ACP): file/terminal shims; `file_safety.py` already notes it is not a security boundary.
> - Question: one Windows policy ("no self-authored live skills, no config CLI, always-ask SOUL") applied in the client, or per-path?

---

## Client integration path (does not fit the four named buckets)

WINH02 and WINH03 have no “Section 5” heading. Both documents state that **no path is recommended** and that WINH00 records the decision. That is the series’ original open product choice.

### C1 — Path A / B / C / D
**Origin:** WINH02 `Zola_WINH02_Audit_03_PreliminaryPaths.md` (entire document); restated WINH03 synthesis. **IDs:** `WINH02-AUD-01`–`12`; `WINH03-AUD-01` and standing `WINH02-AUD-02`.

WINH02 named four realistic primary paths and ruled out dashboard `/api/pty`, `hermes mcp serve`, and inbound webhooks as primary chat contracts:

1. **Path A** — Fork / re-theme `apps/desktop`.
2. **Path B** — Fresh native Windows client against JSON-RPC / `apps/shared`.
3. **Path C** — Client against the OpenAI-compatible HTTP API only.
4. **Path D** — ACP stdio (IDE-shaped, not a standalone Windows shell).

WINH03 resolved the WINH02 “unknown until WINH03” list for A/B (and the process split for C): Path B is `hermes serve` only; Path C needs `hermes gateway` + `API_SERVER_ENABLED`; **they cannot share one spawned process** (`WINH03-AUD-01`). Surface 3 default is fail-open; Surface 1 SSE is fail-closed. `WINH02-AUD-02` (un-semvered JSON-RPC) still applies to any Path A/B packaged client.

**WINH03 remainder if Path C is considered:** whether `/v1/chat/completions` plus `/api/sessions` can resume a crashed turn the way `session.resume` + `session.events.since` can was **not** traced end-to-end in WINH03 (out of that prompt’s Surface 3 scope).

Voice topology (`WINH09` Q4) may constrain this choice — see C3.

### C2 — Cross-phase severity / additivity (WINH06 Q4)
**Origin:** WINH06 Section 5 Q4. **IDs:** `WINH04-AUD-09` vs `WINH06-AUD-02`; `WINH04-AUD-10` vs `WINH06-AUD-03`; `WINH05-AUD-06`/`07` vs `WINH06-AUD-17`/`20`.

> Cross-reference WINH04-AUD-09 / -10 and WINH05-AUD-06 / -07: additive or severity-changing?
> - WINH04-AUD-09: **confirmed, not re-raised as a new WINH04 finding**. WINH06-AUD-02 is the same default, restated because this phase's question is capability acquisition rather than memory safety. WINH04 recorded it as MEDIUM; WINH06 scores HIGH (ungated live skills plus the default-on review fork). WINH00 should pick one severity for the Windows default. Scratch-build framing in WINH04 (gate skill writes) is **reinforced**, not replaced.
> - WINH04-AUD-10: **unchanged**. WINH06-AUD-03 (no pre-live test) is additive: a broken skill not only fails visible (`AUD-10`), it went live without any test.
> - WINH05-AUD-06 / -07: **not re-derived**. WINH06-AUD-17/20 are additive: the agent can **itself** rewrite one identity file, which makes the multi-string split (`AUD-06`) and non-propagation (`AUD-07`) operationally worse. They do not change those findings' labels; they add a write-authority problem WINH05 did not ask.

### C3 — Process topology vs voice (single capture owner)
**Origin:** WINH09 Section 5 Q4. **IDs:** `WINH09-AUD-09`; WINH08 topology; WINH02/03 paths.

> `WINH09-AUD-09` (one mic/one speaker per process, single wake owner) plus WINH08 subagent/surface routing and WINH02/03 paths: does that narrow the Windows client to a single JSON-RPC owner of capture (Desktop-style Path A/B, likely `client_direct` / local mic), and rule out N dashboard+TUI voice clients against one `hermes serve`? Surface 1 HTTP and Surface 4 ACP still do not carry this voice state machine unless they speak the gateway voice methods.

### C4 — MEMORY.md live store vs compatibility projection
**Origin:** WINH04 Open questions Q1. **IDs:** `WINH04-AUD-03`, `AUD-05`, `AUD-06` (WINH04: “This choice drives almost every HIGH finding”).

> Does Zola-Windows keep Hermes builtin MEMORY.md as the live store, or only as a compatibility projection from a Zola store?

### C5 — Identity assembly owner (SOUL.md vs Zola inject)
**Origin:** WINH05 Section 5 Q1. **IDs:** `WINH05-AUD-01`, `AUD-06`, `AUD-07`.

> Does Zola-Windows adopt Hermes’s SOUL.md + `system_prompt.py` as the live identity-rendering path, or does Zola inject its own canonical identity text over/around it (same fork as WINH04 synthesis OQ1 for MEMORY.md — compatibility projection vs Zola owns assembly)? This choice drives `AUD-01`, `AUD-06`, `AUD-07`.

Grouped with C4 as the same “projection vs own assembly” shape; original identity framing preserved.

### C6 — SessionRecord vs Hermes `sessions`
**Origin:** WINH05 Section 5 Q2. **IDs:** `WINH05-AUD-14`, `AUD-15`, `AUD-16`, `AUD-17`; `WINH03-AUD-09`.

> Hermes already has a durable session row and resume. Is that worth wrapping as the Windows conversation id, or must Zola-Windows still inject its own `SessionRecord` (foreground/background, 30s grace, `deviceId`) regardless — given the architecture document’s own status line that the Zola model is design-locked and not a Hermes feature?

### C7 — Layer 5 vs WINH05-AUD-05 (keep both IDs)
**Origin:** WINH05 Section 5 Q4. **IDs:** `WINH04-AUD-01` Layer 5; `WINH05-AUD-05`.

> Phase 2 confirms Hermes has no context-scoped **persona**. That does **not** rescore `WINH04-AUD-01` Layer 5: Layer 5 remains a **memory-store** gap (no context-keyed preference records). `AUD-05` is additive (prompt/personality assembly). WINH00 should keep both IDs.

This document keeps both IDs (G-NO-INVENT / G-NO-DECIDE). The product still needs to say whether Layer 5 records are in the first build.

### C8 — Session transcripts vs forget
**Origin:** WINH04 Open questions Q3. **IDs:** `WINH04-AUD-04`; `state.db` from WINH03.

> Session transcripts vs forget: is redacting `state.db` in scope for Zola, or is “forget” defined as MEMORY.md only (weaker than P-CASCADE)?

### C9 — Write a capability-acquisition architecture document
**Origin:** WINH06 Section 5 Q1. **IDs:** (domain had no Document of Truth).

> Should Zola-Windows write an architecture document for this domain (mirroring Memory Hierarchy / Identity & Personality) before WINH00? This audit had nothing to score against. Without that document, WINH00 cannot convert Section 4 into "scratch-build vs inherit."

*(This synthesis cannot convert WINH06 Section 4 into required scratch vs inherit. Audit_04 lists those items as candidates for that reason.)*

### C10 — Write a tool-authorization architecture document
**Origin:** WINH08 Section 5 Q1. **IDs:** `WINH08-AUD-05`, `AUD-06` (Known Context only had two Zola lines).

> This phase only had two Zola lines (Known Context). Should Zola-Windows write a real tool-authorization spec before WINH00, the way WINH06 asked for capability-acquisition policy?

### C11 — Lore files for zola-windows
**Origin:** WINH05 Section 5 Q5.

> This track has no `ROADMAP.md` / `DESIGN_DECISIONS.md` / `OPEN_QUESTIONS.md` on disk; this audit was scoped without them. If zola-windows will need its own lore tracking, that is a WINH00 decision — not started here.

### C12 — WINH04/05 “keep both IDs” and environmental non-reopen
Covered as S9, S11, C7. No additional text.

---

## Inventory of numbered Section 5 / Open-questions items (checkable)

| Origin | Count | IDs in this file |
|---|---|---|
| WINH02 path decision | 1 | C1 |
| WINH03 Path C resume remainder | folded into C1 | C1 |
| WINH04 Q1–Q6 | 6 | C4, P4, C8, A8, S11, S9 |
| WINH05 Q1–Q5 | 5 | C5, C6, A7, C7, C11 |
| WINH06 Q1–Q4 | 4 | C9, H5, A9, C2 |
| WINH07 Q1–Q4 | 4 | A2, A3, A5 (WINH07 text), A4 |
| WINH08 Q1–Q4 | 4 | C10, S7, A5 (WINH08 text), S6 |
| WINH09 Q1–Q4 | 4 | P2, S5, S1, C3 |
| WINH10 Q1–Q4 | 4 | S4, P3, A1, (Q4 INFO under A1) |
| WINH11 Q1–Q4 | 4 | H1, H2, H3, H4 |
| WINH12 Q1–Q4 | 4 | S2, P1, A6, S3 |

WINH04 6 + WINH05 5 + WINH06–12 (7×4=28) = 39 numbered synthesis questions, plus WINH02/03 path decision. Nothing from those lists was dropped. Extra context-only rows (S8, S10, H6) are labeled as such so they are not mistaken for new findings.

---

## Section 6 — Series Retrospective (brief)

The fresh-start / capability-not-implementation framing in "Recorded scope decisions" held across all twelve phases without a further correction. Android-named libraries and OS APIs were not scored as Hermes misses (explicit in WINH09 voiceprint, WINH10 handset SMS, WINH12 Gemini-as-zola-main-current). Where a domain had no Zola Document of Truth (WINH06 entirely; WINH08 tool-authorization beyond two Agent Map lines; WINH11 Half B deployment), phases used MECHANISM/ABSENT/OBSERVATION instead of inventing MATCH/GAP targets — which is the same framing working in the opposite direction. The three recorded exclusions (Environmental Awareness, Cognitive Engine, and the memory-agency exception's limited scope) were enough; WINH00 did not need a fourth correction, and WINH04 Q6's instruction not to reopen environmental perception was followed.

A few findings were restatements or delayed facets of something an earlier phase already had in hand, rather than true misses: `WINH06-AUD-02` is `WINH04-AUD-09` confirmed at higher severity because of the review fork; `WINH03-AUD-05`/`08` restate `WINH02-AUD-12` with mechanism; `WINH11-AUD-05` encrypts-at-rest the stores WINH04 already named; `WINH12-AUD-17` is the RIL reading of `WINH07-AUD-01`/`02`; `WINH11-AUD-07` cites `WINH04-AUD-11` DWA. The background-review process is the clearest hindsight: WINH06 correctly scored its skill/memory writes, but the same default-on fork's speech and tool-execute facets waited for WINH07 and WINH08 — appropriate given each phase's Document of Truth, and easy to under-weight until Theme 6. WINH03 left Path C API-server resume untraced; that remains a follow-up only if Path C is chosen, not an unrecorded WINH03 finding. WINH01–04 closeout SHAs were not written into the series phase table at the time (recovered in WINH00 from git: `2b0c7ed`, `a73038b`, `e5d237a`, `5637a69`).

What the phase-by-phase structure made harder to see, and Section 3 now states as single facts: (1) extra speech paths, autonomous gateway send, and RIL's single-delivery rule are one authority tension, not three product accidents; (2) live-turn approval is real while background, cron, review, and inbound send consistently bypass it; (3) Hermes's registry/provider pattern is a genuine cross-domain strength (voice, messaging, plugins, models); (4) `HERMES_HOME` files plus `state.db` are one unencrypted at-rest surface scored most directly in WINH11; (5) capabilities, routing surfaces, and clocks each lack a unified index. Those are substrate properties of this Hermes tag for any Zola-Windows build plan, independent of which Section 5 options are later chosen.

---

*End of master synthesis. Next stage per Phase_SOP_Generic.md is Decisions Locked (developer + Claude in conversation), then a build plan. This series does not write that plan.*
