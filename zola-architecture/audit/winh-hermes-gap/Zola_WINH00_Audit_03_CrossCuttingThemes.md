# WINH00 Audit 03 — Cross-Cutting Themes

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
