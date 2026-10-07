# Zola P8PRE Audit — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\P8PRE_Audit_Prompt_v1.2.md`  
**Prompt SHA-256:** `DD03C4706CFB97E995D156A766D90D0AF11DF3FE7D6DDA33C862EF65E0377819`  
**Fix prompt:** `C:\Users\test\Dev\zola-spikes\prompts\P8PRE_Fix_Prompt_v1.0.md`  
**Fix prompt SHA-256:** `0C9088D9F2CE33459D6BE76B1A9B6417715EEA3E0FDDD3526BDAB74B2C57F78D`  
**Audit started:** 2026-10-07 · Fix pass: 2026-10-07  
**SOP:** v2.2 Stage 1 · Template v2.1 · Scope: Google Workspace only

---

## Repositories

| Repo | Branch | HEAD | Clean? |
|------|--------|------|--------|
| `zola-windows` | `p8pre-audit` | `7d2a1e71ca7cc5d12afa901738eca47ee8b5ecee` | audit docs only (uncommitted) |
| `hermes-agent` | detached `v2026.9.14` | `345cd2b057a452236de401d3534b8502a7465e8d` | yes |

---

## Folders

| Role | Path |
|------|------|
| Output | `zola-architecture/audit/p8pre-phase8/` |
| Scratch | `C:\Users\test\Dev\zola-spikes\p8pre\` |
| Live profile | `%LOCALAPPDATA%\hermes\profiles\zola\` |
| Client logs | `%LOCALAPPDATA%\ZolaClient\logs\` |

---

## Guardrails

G-SCOPE / G-NOCHANGE / G-NO-INSTALL / G-NO-GOOGLE-ACCOUNT / G-SCRATCH / G-EXT / G-QUALITY / G-HYPOTHESIS / G-PRIVACY / G-ARCH / G-NO-CROSS-SCOPE / G-CLOSEOUT (wait).

---

## Phase status

| Phase | Status |
|-------|--------|
| 1–11 | COMPLETE (F1–F10 corrections applied) |
| 12 Closeout | COMPLETE |

**Final findings count:** 46 — 11 HIGH, 10 MEDIUM, 3 LOW, 22 MATCH  
**LEADs:** 9 confirmed / 0 refuted / 2 partly

## Closeout SHAs

| Item | SHA |
|------|-----|
| **Audit content SHA (12c)** | `fba2663d0fbb030b42a925b58e6de960e21327f6` |
| Merge SHA (--no-ff merge commit) | *(recorded in 12g)* |
| Final main HEAD (after metadata commit) | *(recorded in 12g)* |

Note: The merge SHA recorded below is the `--no-ff` merge commit, **not** the final `main` HEAD after the metadata commit.

---

## Live-profile hashes (Phase 1 = pre-synthesis; unchanged)

| File | SHA-256 |
|------|---------|
| `config.yaml` | `7BA2E676A04FF92047C8D711FCB022BE8A532B11BAAC6F74B08986744E704570` |
| `SOUL.md` | `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49` |
| `.env` | MISSING |
| `memories/MEMORY.md` | `14DC5F8EBFBDF89A2BCDDA5DF2AFABE57571238C52DBD9644EFA36117E14778D` |
| `memories/USER.md` | `DCA61432F1EF0E16FC5E44A33F127533C330F3EB6B3CE6BB02C82F4A1D79A58D` |

### Plugins (every non-`.pyc` file)

| File | SHA-256 |
|------|---------|
| `zola_memory/__init__.py` | `7FAA42BC030B329EB5F078B80EC45183104105361A29E880EAC3CCCCF9994C11` |
| `zola_memory/consolidate.py` | `1B2D8D8AD8140EC515D184279DD3BD541952918025ADEDF47761944AE14941C2` |
| `zola_memory/fact_index.py` | `AA0CCE9E599BA94F933A8619E2094D3A21192BD4AA785510A9D28FBC53D81B02` |
| `zola_memory/forget.py` | `A9B62AA822DBAD0A350FE84CB004C4E63124F4FBEA98F591D4454EDDCC1BB306` |
| `zola_memory/llm_access.py` | `EC5A8F319628CB24DEEB0177397D34B754A51B30F80C025D4F93D5E5189FEC57` |
| `zola_memory/log.py` | `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` |
| `zola_memory/pending.py` | `9FF6156CD946C08BFD737EDFFC15C6DAE2D865AB0C34ED332F48056DDA854769` |
| `zola_memory/provider.py` | `E292093763665B0A35E38C67166F84E372493D4F4016704F006217A15E76A18A` |
| `zola_memory/registry.py` | `86AA4DA04D67AB911D569AB1D9774A86E1A36F75F9B1931D49CA3F0272EE771D` |
| `zola_memory/retrieve.py` | `53D8044D896F6F769AA10EF99BAB67083ADF19AA3E01858A067A870916C0290D` |
| `zola_memory/store.py` | `C471EA121F993BD00D5E68EEF0DEFB92FBDD3D606774CA78B89ADF1B34CB00E8` |
| `zola_memory/time_context.py` | `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` |
| `zola_tools/plugin.yaml` | `F329E9065493F766712A018DF14541172282666EF516AD3D45781B56AE1D2216` |
| `zola_tools/__init__.py` | `A1EF8541406F1A9C199CC8C8CE1BB7C71E087F4C3EAA2151DAC7B59F04C33513` |
| `zola_tools/calculator.py` | `0F29F3FC1E1D5EAC3D1E4CEF0BCF6428EF6497EE2AF61BD86503602BE80FE680` |

---

## LEAD status

| LEAD | Status | Finding |
|------|--------|---------|
| LEAD-1 | Confirmed | AUD-01 |
| LEAD-2 | Confirmed | AUD-07/08 |
| LEAD-3 | **Confirmed** (substance; F6) | AUD-10 |
| LEAD-4 | Confirmed | AUD-19 |
| LEAD-5 | Confirmed | AUD-15/18 |
| LEAD-6 | Confirmed | AUD-20 |
| LEAD-7 | Confirmed | AUD-21 |
| LEAD-8 | Confirmed | AUD-29 |
| LEAD-9 | Confirmed | AUD-37/39 |
| LEAD-10 | Partly | AUD-11/43 |
| LEAD-11 | Partly | AUD-12/23 |
| LEAD-12 | Confirmed | AUD-24 |

**LEADs: 9 confirmed / 0 refuted / 2 partly**

---

## `[EXT]` source table

| URL | Read date | Findings |
|-----|-----------|----------|
| https://developers.google.com/identity/protocols/oauth2/native-app | 2026-10-07 | OAuth flow |
| https://developers.google.com/identity/protocols/oauth2 | 2026-10-07 | AUD-20 |
| https://developers.google.com/identity/protocols/oauth2/production-readiness/overview | 2026-10-07 | AUD-22 |
| https://developers.google.com/identity/openid-connect/openid-connect | 2026-10-07 | AUD-46 incremental |
| https://developers.google.com/identity/protocols/oauth2/web-server | 2026-10-07 | incremental web |
| https://developers.google.com/gmail/api/auth/scopes | 2026-10-07 | AUD-21 |
| https://developers.google.com/gmail/api/reference/rest/v1/users.drafts | 2026-10-07 | AUD-23 |
| https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list | 2026-10-07 | paging |
| https://developers.google.com/gmail/api/reference/rest/v1/users.messages/get | 2026-10-07 | format |
| https://developers.google.com/gmail/api/reference/quota | 2026-10-07 | quota units |
| https://support.google.com/mail/answer/22839 | 2026-10-07 | consumer send ≤500/day |
| https://developers.google.com/calendar/api/auth | 2026-10-07 | Calendar scopes |
| Calendar Discovery `events.list` | 2026-10-07 | AUD-24 / 13a |
| https://developers.google.com/drive/api/guides/api-specific-auth | 2026-10-07 | Drive classes |
| https://developers.google.com/drive/api/reference/rest/v3/files/list | 2026-10-07 | pageSize |
| https://developers.google.com/people/api/rest/v1/people.connections/list | 2026-10-07 | contacts page |
| https://support.google.com/cloud/answer/13464323 | 2026-10-07 | personal-use exception |
| https://support.google.com/cloud/answer/7454865 | 2026-10-07 | unverified apps |
| https://help.openai.com/en/articles/5722486-… | 2026-10-07* | AUD-47 (*direct GET 403; indexed text) |
| https://help.openai.com/en/articles/7730893-… | 2026-10-07* | AUD-47 |
| https://help.openai.com/en/articles/8983778-… | 2026-10-07* | retention |

---

## Running findings list

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
| P8PRE-AUD-10 | [RISK] | HIGH | 02 | curl/python-file/skill + execute_code bypass patterns |
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

**Totals: 46 findings — 11 HIGH, 10 MEDIUM, 3 LOW, 22 MATCH**

---

## Closeout

Await developer: **proceed to closeout**.
