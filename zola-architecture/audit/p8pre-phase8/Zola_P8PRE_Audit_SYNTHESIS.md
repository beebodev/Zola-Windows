# Zola P8PRE Audit — Synthesis

**Date:** 2026-10-07 (includes P8PRE-FIX F1–F10)  
**Prompt SHA-256:** `DD03C470…7819` · **Fix SHA-256:** `0C9088D9…F78D`  
**Scope:** Google Workspace only. Diagnostic; **no choices**.

---

## Section 1 — Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P8PRE-AUD-01 | [MATCH] | — | 01 | Plugin `register_tool` path proven |
| P8PRE-AUD-02 | [MATCH] | — | 01 | Live enablement matches P6-CALC |
| P8PRE-AUD-03 | [GAP] | MEDIUM | 01 | Handlers lack platform kwargs; hooks can store them |
| P8PRE-AUD-04 | [RISK] | MEDIUM | 01 | state.db/wire persist tool args/results |
| P8PRE-AUD-05 | [MATCH] | — | 01 | pre_tool_call can block; sees terminal command |
| P8PRE-AUD-06 | [GAP] | LOW | 01 | No max_result_size on PluginContext API |
| P8PRE-AUD-07 | [MATCH] | — | 02 | request_tool_approval fail-closed without human |
| P8PRE-AUD-08 | [RISK] | HIGH | 02 | mode:off / YOLO / unattended approve without Brian |
| P8PRE-AUD-09 | [MATCH] | — | 02 | Client card matches P4-D07 |
| P8PRE-AUD-10 | [RISK] | HIGH | 02 | curl/python-file/skill + execute_code bypass |
| P8PRE-AUD-11 | [GAP] | HIGH | 02 | Spoken approval capture (a) not built |
| P8PRE-AUD-12 | [GAP] | MEDIUM | 02 | No Draft-ID/hash bind in code |
| P8PRE-AUD-13 | [MATCH] | — | 02 | No agent send_message on desktop path |
| P8PRE-AUD-14 | [RISK] | MEDIUM | 02 | Clarify-as-send is model-decided |
| P8PRE-AUD-15 | [MATCH] | — | 03 | Workspace skill matches S16 gaps |
| P8PRE-AUD-16 | [RISK] | HIGH | 03 | Skill+terminal send bypasses A1 |
| P8PRE-AUD-17 | [GAP] | MEDIUM | 03 | P3/S15 vs S16 conflict |
| P8PRE-AUD-18 | [MATCH] | — | 03 | No Google MCP; email not tools |
| P8PRE-AUD-19 | [MATCH] | — | 03 | No Google libs; REST stack present |
| P8PRE-AUD-20 | [MATCH] | — | 04 | Testing 7-day RT |
| P8PRE-AUD-21 | [MATCH] | — | 04 | gmail.compose includes send |
| P8PRE-AUD-22 | [RISK] | HIGH | 04 | Restricted scopes + unverified/Testing limits |
| P8PRE-AUD-23 | [MATCH] | — | 04 | Drafts API send-by-id |
| P8PRE-AUD-24 | [RISK] | MEDIUM | 04 | Big results; no newest-first startTime |
| P8PRE-AUD-25 | [MATCH] | — | 05 | Plaintext creds match H2 |
| P8PRE-AUD-26 | [RISK] | HIGH | 05 | No storage stops terminal |
| P8PRE-AUD-27 | [MATCH] | — | 05 | DPAPI/CredMan via pywin32 |
| P8PRE-AUD-28 | [RISK] | MEDIUM | 05 | H6 reinjection; token file not denied |
| P8PRE-AUD-29 | [RISK] | HIGH | 06 | Workspace output not untrusted-wrapped |
| P8PRE-AUD-30 | [GAP] | HIGH | 06 | No email provenance; review can write |
| P8PRE-AUD-31 | [MATCH] | — | 06 | Pending skips raw tool rows |
| P8PRE-AUD-32 | [GAP] | MEDIUM | 06 | No calendar-vs-memory authority |
| P8PRE-AUD-33 | [MATCH] | — | 06 | Forget ≠ state.db redaction |
| P8PRE-AUD-34 | [RISK] | HIGH | 07 | Email bodies → cloud model |
| P8PRE-AUD-35 | [MATCH] | — | 07 | P6-D07 memory locality only |
| P8PRE-AUD-36 | [GAP] | MEDIUM | 07 | Brian account training toggles UNCONFIRMED |
| P8PRE-AUD-37 | [MATCH] | — | 08 | Tool round ~+8–12 s |
| P8PRE-AUD-38 | [RISK] | HIGH | 08 | skill_view → Workspace skill |
| P8PRE-AUD-39 | [RISK] | MEDIUM | 08 | act_dont_ask weights send gate |
| P8PRE-AUD-40 | [MATCH] | — | 08 | Google RTT ≪ model round |
| P8PRE-AUD-41 | [RISK] | HIGH | 02 | Agent can set mode:off via config.yaml |
| P8PRE-AUD-43 | [MATCH] | — | 02 | Shape (b) code-decidable via hooks |
| P8PRE-AUD-44 | [GAP] | LOW | 04 | Calendar/People scope classes UNCONFIRMED |
| P8PRE-AUD-45 | [GAP] | LOW | 04 | Draft cross-client visibility UNCONFIRMED |
| P8PRE-AUD-46 | [MATCH] | — | 04 | No installed-app incremental auth |
| P8PRE-AUD-47 | [MATCH] | — | 07 | Public ChatGPT/Codex training opt-out docs |

**Totals: 46 — 11 HIGH, 10 MEDIUM, 3 LOW, 22 MATCH**

---

## Section 2 — Build plan implications (GAP/RISK)

Unchanged themes from the first synthesis, plus: **AUD-41** (config.yaml write → `mode:off` without restart); **AUD-10/F6** (`python file.py` and `execute_code` after its gate); **AUD-24** (Calendar has no descending `startTime` — “last meeting” needs client-side pick); **AUD-46** (installed apps cannot use `include_granted_scopes` incremental merge).

---

## Section 3 — Pre-work required

1. Brian: Google Cloud project, APIs, consent (Testing + test user or Production), Desktop client.  
2. Install decision (`P2-D17`) — candidate wheels (PyPI JSON, 2026-10-07), `py3-none-any` unless noted:

| Package | Version | Wheel size (bytes) |
|---------|---------|-------------------:|
| google-api-python-client | 2.194.0 | 15,016,514 |
| google-auth | 2.55.1 | 252,349 |
| google-auth-oauthlib | 1.3.1 | 19,247 |
| google-auth-httplib2 | 0.3.1 | 9,534 |
| httplib2 | 0.32.0 | 93,148 |
| pyasn1 | 0.6.4 | 84,410 |

**Transitive deps not already in Hermes venv** (non-extra; sizes = latest PyPI wheel when unpinned):  
`google-api-core` (~215 KB), `googleapis-common-protos` (~308 KB), `proto-plus` (~51 KB), `uritemplate` (~11 KB), `pyparsing` (~126 KB), `pyasn1-modules` (~181 KB), `requests-oauthlib` (~24 KB), `oauthlib` (~160 KB).  
Already in venv: `cryptography`, `requests`, `protobuf`, `urllib3`, `certifi`, `idna`, `charset-normalizer`, `PyJWT`.  
Note: latest `google-api-core` lists `opentelemetry-api` — confirm whether the version pulled by `google-api-python-client==2.194.0` requires it at decision time.

3. No Google account / installs performed in this audit.

---

## Section 4 — Assumptions confirmed (every MATCH)

P8PRE-AUD-01, P8PRE-AUD-02, P8PRE-AUD-05, P8PRE-AUD-07, P8PRE-AUD-09, P8PRE-AUD-13, P8PRE-AUD-15, P8PRE-AUD-18, P8PRE-AUD-19, P8PRE-AUD-20, P8PRE-AUD-21, P8PRE-AUD-23, P8PRE-AUD-25, P8PRE-AUD-27, P8PRE-AUD-31, P8PRE-AUD-33, P8PRE-AUD-35, P8PRE-AUD-37, P8PRE-AUD-40, P8PRE-AUD-43, P8PRE-AUD-46, P8PRE-AUD-47.

---

## Section 5 — Open questions for the developer

### 5.1 Integration shape

(Unchanged options table: REST-only plugin / Google libs install / adapt skill / keep skill.)

### 5.2 OAuth app (F2)

| Topic | Google requires `[EXT]` | We choose |
|-------|-------------------------|-----------|
| Testing | 7-day RT; test users; testing UI + 100-user cap while unverified/testing | Accept weekly re-consent vs not |
| Personal-use exemption | Verification not mandatory if &lt;100 users; click-through unverified screens still apply | Whether to verify anyway |
| Production unverified | Danger UI; 100-user cap; no Testing 7-day RT | Accept warnings |
| Scopes | Gmail/Drive classes quoted; Calendar/People **classes UNCONFIRMED** (Console) | Scope set per ability |
| Incremental | **Installed apps cannot** use `include_granted_scopes` incremental auth | One-shot full consent vs separate installed consents (merge behavior UNCONFIRMED) |
| Quotas | list=5, get=20, drafts.send=100 units; 6k units/user/min; consumer ~500 sends/day | Throttle design |

### 5.3 Token storage (F6/F7)

Plain / DPAPI / CredMan — none stop terminal or `execute_code`/unflagged `python file.py`. **H2 revisit** weighs mailbox-scoped refresh tokens. Agent can also disable the approval gate by editing `config.yaml` (AUD-41).

### 5.4 Send path (F6/F7)

Sanctioned tool + `request_tool_approval` remains necessary; not sufficient while terminal/`python file.py`/`execute_code`/skill can use the token, and while the agent can set `mode:off`. Draft-ID+hash still strongest content bind. “Drafts only; Brian sends in Gmail” still faces LEAD-7 if `gmail.compose` is granted.

### 5.4a Draft authority

Unchanged options; Draft cross-client visibility **UNCONFIRMED** (AUD-45).

### 5.4b Spoken approval (F5)

| Shape | Who decides yes | Feasible at this pin? | New build | Revises |
|-------|-----------------|----------------------|-----------|---------|
| (a) Bound capture | Client | Not built | CaptureKind + TTS + grammar | `P4-D07` |
| (b) Plugin-checked turn | Plugin code | **Yes in principle** — `pre_llm_call` / `on_turn_start` see `user_message`, `platform`, `parent_session_id`; handler reads session-keyed store; voice vs typed **not** distinguishable; busy-input can append to user message | Affirmative grammar + Draft succession + store | Possibly `P4-D07` |
| (c) Clarify | Model | Exists | Little | Weak vs `A1` |
| (d) Card | Client | Exists | None | Stands |

H-6: synthetic recognition mostly OK; mishears/punctuation matter.

### 5.5 Triage actions

Unchanged.

### 5.6 Untrusted content

Unchanged table + levers.

### 5.7 Privacy (inline)

| Lever | Protects | Costs |
|-------|----------|-------|
| Metadata-only default | Body out of model | Weaker answers until expand |
| Length caps | Volume / prompt cost | Incomplete lists |
| Strip quotes/signatures | Quoted history | May drop needed context |
| Redact addresses | Address harvesting | Harder addressing |
| No attachments | Attachment content | Can’t answer attachment questions |
| Local summarizer | Body local | Install / local model |
| Training opt-out (Brian’s ChatGPT setting) | Model-training use | Does not remove chat retention |

Public docs: personal ChatGPT/Codex trainable unless “Improve the model for everyone” off. Brian’s toggle: ask Brian.

### 5.8 Latency and bounds

Fine vs coarse; Calendar “last meeting” needs ascending `startTime` + client pick; skill routing may force extra rounds; may depend on `S54`.

### 5.9 Logging

`zola_tools` metadata-only; cannot stop Hermes `state.db` / wire.

### 5.11 / 5.11a Calendar write & history

Past events: readonly scopes + `timeMin`/`timeMax`/`q`; no API newest-first `startTime`; memory-vs-calendar authority open (AUD-32). Writes out of locked scope.

### 5.12 Attachments

Metadata via part `filename`/`attachmentId`/`size` without `attachments.get`; inline `data` possible for small parts.

### 5.13 Account binding

Unchanged.

### 5.14 Dependencies

Google Cloud → token → reads → drafts → send+gate; strip cron toolset before any send tool; skill routing before plugin-only path; consider config.yaml write protection if send ships.

### Request-path diagram

```text
READ: Brian → client → prompt.submit → model → tool → Zola plugin → token → Google → result* → model → reply
  * untrusted enters; state.db stores tool rows

SEND sanctioned: … → send tool → [GATE] → Google
  (d) card: client   (a) bound capture: client   (b) plugin grammar: plugin   (c) clarify: MODEL

BYPASS: terminal | python file.py | execute_code | skill script → token → Gmail
  + agent may set approvals.mode:off via config.yaml (mtime reload)
```

---

## Section 6 — LEAD outcomes

| LEAD | Outcome | Finding |
|------|---------|---------|
| LEAD-1 | Confirmed | AUD-01 |
| LEAD-2 | Confirmed | AUD-07/08 |
| LEAD-3 | **Confirmed** | AUD-10 |
| LEAD-4 | Confirmed | AUD-19 |
| LEAD-5 | Confirmed | AUD-15/18 |
| LEAD-6 | Confirmed | AUD-20 |
| LEAD-7 | Confirmed | AUD-21 |
| LEAD-8 | Confirmed | AUD-29 |
| LEAD-9 | Confirmed | AUD-37/39 |
| LEAD-10 | Partly | AUD-11/43 |
| LEAD-11 | Partly | AUD-12/23 |
| LEAD-12 | Confirmed | AUD-24 |

---

## Section 7 — `[EXT]` sources

Full table mirrored in `Zola_P8PRE_Audit_PROGRESS.md` (includes F2 Google pages + F3 OpenAI Help Center URLs). UNCONFIRMED items: Calendar/People scope sensitivity classes; Draft cross-client visibility; installed-app second-consent token merge; hard calendar history retention floor; Brian’s OpenAI toggles.
