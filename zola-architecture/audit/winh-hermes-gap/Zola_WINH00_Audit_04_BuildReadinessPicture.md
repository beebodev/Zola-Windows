# WINH00 Audit 04 — Master Build-Readiness Picture

Pinned tag (final re-check, WINH00 Phase 1): Hermes Agent `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.

Compression of each phase synthesis Sections 2–4. Not a re-derivation and not a build plan. “Wrap” vs “scratch” language is copied from the phases; ranking in Section C uses the heuristic in the WINH00 prompt (HIGH-finding load, dependency, phase-flagged deferral candidates). No option among open questions is preferred here.

---

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
