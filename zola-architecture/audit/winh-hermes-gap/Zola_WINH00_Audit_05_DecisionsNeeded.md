# WINH00 Audit 05 — Consolidated Decisions Needed

Pinned tag (final re-check, WINH00 Phase 1): Hermes Agent `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.

These are **not resolved** in this document. No option is ranked or preferred (G-NO-DECIDE). Grouping is a first pass for the Decisions Locked conversation; the developer may regroup.

Every entry keeps origin phase and cited finding IDs. Overlapping questions are grouped under one heading but **both original texts are preserved**.

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
