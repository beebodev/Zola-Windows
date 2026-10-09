# Zola P9PRE Audit — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\P9PRE_Audit_Prompt_v1.1.md`  
**Prompt SHA-256:** `D5652874B9A17885174391A8E8331DDC1BBE0AE75C92065EB713C54978CF199A`  
**Developer-supplied comparison hash:** none in the prompt message. The SHA above is the on-disk canonical file (computed 2026-10-09).  
**Audit started:** 2026-10-09  
**SOP:** v2.2 Stage 1 · Template v2.1 · Scope: proactive foundation (supervision, watcher, ranking, loops, delivery, publishing facts)

---

## Repositories

| Repo | Branch | HEAD | Clean? |
|------|--------|------|--------|
| `zola-windows` | `p9pre-audit` (from `main`) | `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc` | audit docs only once written |
| `hermes-agent` | detached `v2026.9.14` | `345cd2b057a452236de401d3534b8502a7465e8d` | yes (`git status --porcelain` empty) |

`main` was clean at `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc` before `p9pre-audit` was created. No managed-scope marker (`.managed` absent; `HERMES_MANAGED` unset).

---

## Folders

| Role | Path |
|------|------|
| Output | `zola-architecture/audit/p9pre-phase9/` |
| Scratch | `C:\Users\test\Dev\zola-spikes\p9pre\` |
| Live profile | `%LOCALAPPDATA%\hermes\profiles\zola\` |
| Client logs | `%LOCALAPPDATA%\ZolaClient\logs\` |
| Hermes pin | `C:\Users\test\Dev\hermes-agent` |

---

## Guardrails

G-SCOPE / G-NOCHANGE / G-NO-INSTALL / G-NO-GOOGLE / G-NO-LIVE-MODEL / G-SCRATCH / G-EXT / G-ARCH / G-QUALITY / G-HYPOTHESIS / G-PRIVACY / G-CLOSEOUT (wait) / G-NO-CROSS-SCOPE.

Effective config was computed by deep-merging the profile `config.yaml` with pinned `DEFAULT_CONFIG` in a scratch script. `load_config()` was not called (it writes a backup into the profile).

---

## Phase status

| Phase | Status |
|-------|--------|
| 1 Setup | COMPLETE |
| 2 Supervision | COMPLETE |
| 3 Watcher host | COMPLETE |
| 4 Google feeds | COMPLETE |
| 5 Background authority | COMPLETE |
| 6 Ranking | COMPLETE |
| 7 Loops and queue | COMPLETE |
| 8 Delivery and HUD | COMPLETE |
| 9 Probes | COMPLETE |
| 10 Synthesis | COMPLETE |
| 11 Closeout | COMPLETE |

---

## Processes at Phase 1 (2026-10-09)

| Process | PID | Start (local) | Command (shape) |
|---------|-----|---------------|-----------------|
| `dotnet.exe` | 3216 | 2026-10-09 09:04:54 | `dotnet run --project …\Zola.Client.csproj` |
| `Zola.Client.exe` | 23372 | 2026-10-09 09:05:09 | Debug `net9.0-windows10.0.19041.0\Zola.Client.exe` |
| `python.exe` (serve parent) | 12960 | 2026-10-09 09:05:10 | `hermes-agent\.venv\Scripts\python.exe -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0` |
| `python.exe` (serve child) | 26284 | 2026-10-09 09:05:10 | `uv\python\cpython-3.12-…\python.exe -m hermes_cli.main -p zola serve --isolated …` |

Other `python.exe` processes are Blender MCP (`mcp-for-blender`), not Hermes.

---

## Effective config

Merge: pinned `hermes_cli/config_defaults.py` `DEFAULT_CONFIG`, then profile `config.yaml`. Profile wins per leaf. No managed overlay. Secret-shaped leaves were not present in these sections.

### Profile overrides (requested sections)

| Key | Value | Source |
|-----|-------|--------|
| `approvals.mode` | `manual` | profile |
| `plugins.enabled` | `zola_tools`, `zola_workspace` | profile |
| `platform_toolsets.cli` | browser, clarify, computer_use, connections, cronjob, delegation, file, image_gen, memory, session_search, skills, terminal, todo, tts, vision, web, zola_tools, zola_workspace | profile |
| `known_plugin_toolsets.cron` | `zola_workspace` | profile |
| `memory.memory_char_limit` | 4400 | profile |
| `memory.user_char_limit` | 4000 | profile |
| `memory.provider` | `zola_memory` | profile |
| `model.provider` | `openai-codex` | profile |
| `model.base_url` | `https://chatgpt.com/backend-api/codex` | profile |
| `model.default` | `gpt-5.6-terra` | profile |
| `tts.provider` | `edge` | profile (same string as the pin default) |
| `tts.edge.voice` | `en-GB-SoniaNeural` | profile |
| `tts.edge.speed` | 0.95 | profile |
| `voice.barge_in` | false | profile |
| `voice.silence_duration` | 1.5 | profile |
| `voice.stop_phrases` | `stop` | profile (same list as the pin default) |
| `voice.thinking_sound` | true | profile (same as the pin default) |

`platform_toolsets` and `known_plugin_toolsets` are absent from `DEFAULT_CONFIG`. The profile has no `platform_toolsets.tui` and no `platform_toolsets.cron`. Adjacent profile keys outside the requested set: `agent.reasoning_effort` = `medium`, `agent.clarify_timeout` = 300.

### Pin defaults (not set in the profile)

| Key | Value | Source |
|-----|-------|--------|
| `approvals.timeout` | 300 | default |
| `approvals.cron_mode` | `deny` | default |
| `approvals.single_query_mode` | `deny` | default |
| `approvals.unattended_mode` | `deny` | default |
| `approvals.smart_policy` | empty | default |
| `approvals.denial_breaker_threshold` | 3 | default |
| `approvals.deny` | `[]` | default |
| `approvals.mcp_reload_confirm` | true | default |
| `approvals.destructive_slash_confirm` | true | default |
| `plugins.hook_callback_timeout` | 30 | default |
| `plugins.allow_deprecated_imports` | false | default |
| `memory.memory_enabled` | true | default |
| `memory.user_profile_enabled` | true | default |
| `memory.write_approval` | false | default |
| `memory.nudge_interval` | 10 | default |
| `agent.execution_guidance` | `auto` | default |
| `cron.*` | entire block absent from the profile | default (`catch_up_missed` true, `allow_agent_scheduling` false, `preflight` true, `model` empty, `provider` empty, `script_timeout_seconds` 3600, `max_parallel_jobs` null) |
| `auxiliary` | entire block absent | default |
| `auxiliary.background_review.enabled` | true | default |
| `auxiliary.background_review.provider` | `auto` | default |
| `auxiliary.background_review.model` | empty | default |
| `auxiliary.background_review.timeout` | 120 | default |
| `auxiliary.background_review.max_input_tokens` | 600000 | default |
| `auxiliary.background_review.reasoning_effort` | empty | default |
| `auxiliary.background_review.api_key` | empty | default |
| `display.memory_notifications` | `on` | default |
| `display.background_process_notifications` | `concise` | default |
| `fallback_providers` | `[]` | default |
| `voice.voice_chat_mode` | `chained` | default |
| `voice.auto_tts` | false | default |
| `voice.max_recording_seconds` | 120 | default |
| `voice.record_key` | `ctrl+b` | default |
| `voice.silence_threshold` | 200 | default |
| `voice.submit_mode` | `direct` | default |
| `voice.client_direct` | true | default |
| `voice.beep_enabled` | true | default |
| `voice.beep_volume` | 0.3 | default |
| `tts` providers other than the Edge voice/speed above | pin defaults (Edge is the selected provider) | default |
| `desktop.auto_continue.enabled` | true | default |
| `desktop.auto_continue.freshness_minutes` | 15 | default |
| `desktop.auto_continue.max_attempts` | 2 | default |

`auxiliary.monitor` exists only as a pin comment ("important-mail 0-10 scorer") on a generic aux block (`config_defaults.py` L738). No profile override.

---

## `.env`

MISSING. Key names: none.

---

## Live-profile hashes (Phase 1)

| File | SHA-256 |
|------|---------|
| `config.yaml` | `6ED53ACE35C223ED1B9D5AF1696A6C449626C57B37B38F099F2DCC5B6F4B8E76` |
| `SOUL.md` | `38577550B251AFC6AA21432BA1DF12DF70A6F56378ADD6DC2E30211358C9C5E2` |
| `.env` | MISSING |
| `memories/MEMORY.md` | `6DC835B5FA5563CD609856F6C1EFB73E1DCE1F57008B6F592AD22E44619227AB` |
| `memories/USER.md` | `27B375222430AF4E6D4D50A7205B6380A2B7058B799F068DB4CFD467676816D5` |

### Plugins (every file, including `.pyc`)

| File | SHA-256 |
|------|---------|
| `plugins/zola_memory/consolidate.py` | `F7B886C35B5817E74C1F92021D5837123F65B0177354D4D36B6B0C441903B992` |
| `plugins/zola_memory/fact_index.py` | `AA0CCE9E599BA94F933A8619E2094D3A21192BD4AA785510A9D28FBC53D81B02` |
| `plugins/zola_memory/forget.py` | `A9B62AA822DBAD0A350FE84CB004C4E63124F4FBEA98F591D4454EDDCC1BB306` |
| `plugins/zola_memory/llm_access.py` | `EC5A8F319628CB24DEEB0177397D34B754A51B30F80C025D4F93D5E5189FEC57` |
| `plugins/zola_memory/log.py` | `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` |
| `plugins/zola_memory/pending.py` | `9FF6156CD946C08BFD737EDFFC15C6DAE2D865AB0C34ED332F48056DDA854769` |
| `plugins/zola_memory/provider.py` | `E292093763665B0A35E38C67166F84E372493D4F4016704F006217A15E76A18A` |
| `plugins/zola_memory/registry.py` | `86AA4DA04D67AB911D569AB1D9774A86E1A36F75F9B1931D49CA3F0272EE771D` |
| `plugins/zola_memory/retrieve.py` | `53D8044D896F6F769AA10EF99BAB67083ADF19AA3E01858A067A870916C0290D` |
| `plugins/zola_memory/store.py` | `C471EA121F993BD00D5E68EEF0DEFB92FBDD3D606774CA78B89ADF1B34CB00E8` |
| `plugins/zola_memory/time_context.py` | `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` |
| `plugins/zola_memory/__init__.py` | `7FAA42BC030B329EB5F078B80EC45183104105361A29E880EAC3CCCCF9994C11` |
| `plugins/zola_memory/__pycache__/consolidate.cpython-312.pyc` | `4C997ED05687F6DD61503604708587E5AD971ECBDE8BD4EDD44278870490A782` |
| `plugins/zola_memory/__pycache__/fact_index.cpython-312.pyc` | `BDBAFBCFB5331CE037A758A90BC574BBA0FD3D1B93B585A36CC33A207B173D4C` |
| `plugins/zola_memory/__pycache__/forget.cpython-312.pyc` | `D4EDF6C6FD46490D5D9D5B404E102E46EA7DA6EF190DCCF3D09328F396452007` |
| `plugins/zola_memory/__pycache__/llm_access.cpython-312.pyc` | `11D5178130C84CDB7531FF8D900C9FBB96236E9C5E243544C00B9B774C5C095B` |
| `plugins/zola_memory/__pycache__/log.cpython-312.pyc` | `E62C5C1DD987044650217BF3708D5D0A535278A84F0A98DC77E16BB1B0B9E950` |
| `plugins/zola_memory/__pycache__/pending.cpython-312.pyc` | `5148F60A26FDB64E81735B6F092DE8BE0CB4C6C946B37EE1B45B18E5CEDF15BA` |
| `plugins/zola_memory/__pycache__/provider.cpython-312.pyc` | `2E2715D1BD508D1E51AA961F5A8A508FD8A83193F7248896EF561E4EF24A01F6` |
| `plugins/zola_memory/__pycache__/registry.cpython-312.pyc` | `74F850D725D4642468A8BB1F421FC2705276090E0F5081CC79A6050C5026828D` |
| `plugins/zola_memory/__pycache__/retrieve.cpython-312.pyc` | `9E2FF5CCA225C7E072EDB90E9504EC89A86CFD4B42010742B7543C10F7737DE7` |
| `plugins/zola_memory/__pycache__/store.cpython-312.pyc` | `AFCCA4DC137201EF3D9B6EB39C17A0F1BECE4565B55F5E9E69E44ECB3649ABE3` |
| `plugins/zola_memory/__pycache__/time_context.cpython-312.pyc` | `3984F7434756768B1DCFC660860303A5DF092BD4BFD4915C08B0079585D51F78` |
| `plugins/zola_memory/__pycache__/__init__.cpython-312.pyc` | `BBA695FD7CB093DD247CA58C50F2E463DEFDA9258DB86B35424E0D78ABA454A2` |
| `plugins/zola_tools/calculator.py` | `0F29F3FC1E1D5EAC3D1E4CEF0BCF6428EF6497EE2AF61BD86503602BE80FE680` |
| `plugins/zola_tools/plugin.yaml` | `F329E9065493F766712A018DF14541172282666EF516AD3D45781B56AE1D2216` |
| `plugins/zola_tools/__init__.py` | `A1EF8541406F1A9C199CC8C8CE1BB7C71E087F4C3EAA2151DAC7B59F04C33513` |
| `plugins/zola_tools/__pycache__/calculator.cpython-312.pyc` | `195110B9B7A5AC0D99CBE0D4340BE8565B3557C0FD25D6C1F78C97BAC6EFA94D` |
| `plugins/zola_tools/__pycache__/__init__.cpython-312.pyc` | `D4380D89D9C97470DA5BBB4078EFFA2B9D2CF5D87311F42D596FA0FFE073A7CD` |
| `plugins/zola_workspace/auth.py` | `A8AA8810FC9DF899788273181C8199645E2BAAD3D35A0C1ADAE318F4423E7667` |
| `plugins/zola_workspace/contacts.py` | `E34343C96CCF8CDAF4FFB91C498CC6FEFFDF5020554D092A5F567831CDB3C3DE` |
| `plugins/zola_workspace/drive.py` | `2EF13563A57DCD6F30F72D3CF4122C54DF74BF104C37EBD082476065D947CC66` |
| `plugins/zola_workspace/framing.py` | `0E91FFC883D42DE7AC143B01D2CDBFD822B1EA34B40355D32E9924C10E3B515A` |
| `plugins/zola_workspace/gcal.py` | `6F17605A69B606946DC9C8ADC50EEB84282E212AABCA2E1EF57778EB7BCDD3BA` |
| `plugins/zola_workspace/gmail.py` | `DD018F6AE1D220F9D5B3EE10D60874784E556E1EB46D4F7CD3B4079214D3E7A7` |
| `plugins/zola_workspace/google_http.py` | `81281017D1A93DE26936DC660D2A9E9F7F1DF53411175B95F9136B9F92765B82` |
| `plugins/zola_workspace/guards.py` | `EB5C505274D2B0EC9CE4826A5E2DBE2C58A3C8B41E28E205CB39BC60C62AF680` |
| `plugins/zola_workspace/log.py` | `CE00D6FB46FFEAB36E2A212E05BB68FC7ED6CB9292D30E8380355429D2976650` |
| `plugins/zola_workspace/plugin.yaml` | `4E485461744F49222E1DD7EA378ADB899B2E3C064B4DCFF72F79027C96B7D738` |
| `plugins/zola_workspace/posture.py` | `E55D8E8253C5C8867C356C20A96716949DCFA22D5E5C2C9391D07219C292CDA9` |
| `plugins/zola_workspace/read_common.py` | `B37CF4A91E7A211CFBC1865AC925658B28D26BD95A4B98908C4C6F926FB3F562` |
| `plugins/zola_workspace/send_gate.py` | `0432FAC90B50AAD604C17BC2E2F43C6BFC85F0EF26568EFFE66835B4690ECA33` |
| `plugins/zola_workspace/setup.py` | `1FFEAAC4DE12A47286ACB2B2C9780D9C9B4E86B151802575ACAFBCC0712D3696` |
| `plugins/zola_workspace/taint.py` | `6390F091CA3A1ACE957BE7D18A80F1F926EC486FBF81025AC24B016D76CC344E` |
| `plugins/zola_workspace/textclean.py` | `E5983EBC83858C69C0F53D473DA63A78C15739CF4226453E24EF1C28928DBE64` |
| `plugins/zola_workspace/turn_context.py` | `7AA76D6C35544B475F299A9D3AFC7EC72BBEFF07FE95687C56B341C19D1BE337` |
| `plugins/zola_workspace/__init__.py` | `ED527D20DD94CDE8D2EB6CC97A627B0B3EAEA2A9B4ACA3D6B037410882E26BA6` |
| `plugins/zola_workspace/__pycache__/auth.cpython-312.pyc` | `567849A56780545A08566D72D9B3F341ECA1368AC3EF1D3687B29CD87A894EC6` |
| `plugins/zola_workspace/__pycache__/contacts.cpython-312.pyc` | `02E1E8A7C6C355269D8FFA57894B3F17454530E480A2D966A2D3EC31CF56ED5F` |
| `plugins/zola_workspace/__pycache__/drive.cpython-312.pyc` | `38D97D544FFB7776023334D85F39A3AE788D5A81013714600BFBAEAC073ECB97` |
| `plugins/zola_workspace/__pycache__/framing.cpython-312.pyc` | `04FE8C196840AC551C8F5267D5449B0CB6F205A54D15800D072E35D67605F5D1` |
| `plugins/zola_workspace/__pycache__/gcal.cpython-312.pyc` | `69F7AABB1D01138AF8C1FCC64C756366CB9C8A83C562533CB713C22049DF37B7` |
| `plugins/zola_workspace/__pycache__/gmail.cpython-312.pyc` | `418E3156258DE692889D0E1E23BC79E00612E24064130683E4D53F6D32419EAB` |
| `plugins/zola_workspace/__pycache__/google_http.cpython-312.pyc` | `BA51A9448D52A353CE4B874067EEFE025EF30CD02727F6E0C1979B98D087BB13` |
| `plugins/zola_workspace/__pycache__/guards.cpython-312.pyc` | `6881946401189DA12D3D707644127DF1BB7494F11D240E05221BECCDF3D8FECF` |
| `plugins/zola_workspace/__pycache__/log.cpython-312.pyc` | `D8B1923885E2D7E1F41B7DC81BB4ECD6185AE28E86BA50DD23333C3A3981C514` |
| `plugins/zola_workspace/__pycache__/posture.cpython-312.pyc` | `21F06FE209B54A8A5078CF3F30285884D7F5B19785CB10DC21CF4339BF105342` |
| `plugins/zola_workspace/__pycache__/read_common.cpython-312.pyc` | `F797DB7E7DCF2CF1C1288A74CD1F0094590AFF1956A6D330EF0D471A2C1B1089` |
| `plugins/zola_workspace/__pycache__/send_gate.cpython-312.pyc` | `7066BF85586AC9050A18B3D793B4131D730C2945E2A1F93EC6245D936E574C9B` |
| `plugins/zola_workspace/__pycache__/taint.cpython-312.pyc` | `5B93232B4B2E93FD294DC604E718B2217DC59DE221A966E0821C2C04DFA17D42` |
| `plugins/zola_workspace/__pycache__/textclean.cpython-312.pyc` | `E8A8702CC9B1C91E884D223D1B2DB5450F0955D1EA29A8C38931674FCD94DF16` |
| `plugins/zola_workspace/__pycache__/turn_context.cpython-312.pyc` | `74629E17DE1A5CC9EBFF9517435D9F37AC698F3C6FECE521E93C5BD09CEE09B4` |
| `plugins/zola_workspace/__pycache__/__init__.cpython-312.pyc` | `C01E055315239505E5466245BAC917E7539B5AD1702B314B9444E5105525D86F` |

### Token store (names, sizes, mtimes only; contents not read)

Not under `plugins/`. Profile path `zola_workspace\token.dpapi`: size 926, mtime `2026-10-07T22:58:24.2521851Z`.

### Skills names

`.curator_backups`, `.hub`, `apple`, `autonomous-ai-agents`, `communication`, `creative`, `devops`, `email`, `media`, `note-taking`, `productivity`, `research`, `social-media`, `software-development`, `web`, `.bundled_manifest`, `.curator_ledger.jsonl`, `.curator_state`, `.usage.json`, `.usage.json.lock`.

### Cron contents

`cron\output` (directory; no job files named at Phase 1).

---

## LEAD status

| LEAD | Status | Finding |
|------|--------|---------|
| LEAD-1 | Partly confirmed | P9PRE-AUD-18, P9PRE-AUD-19, P9PRE-AUD-43, H-1, H-2 |
| LEAD-2 | Partly | P9PRE-AUD-20 |
| LEAD-3 | Confirmed | P9PRE-AUD-26, P9PRE-AUD-28, P9PRE-AUD-41 |
| LEAD-4 | Confirmed | P9PRE-AUD-01, P9PRE-AUD-02 |
| LEAD-5 | Confirmed | P9PRE-AUD-09, P9PRE-AUD-11, P9PRE-AUD-12 |
| LEAD-6 | Confirmed | P9PRE-AUD-36 |
| LEAD-7 | Confirmed | P9PRE-AUD-23, P9PRE-AUD-34 |
| LEAD-8 | Partly | P9PRE-AUD-14 |
| LEAD-9 | Partly | H-5, audit 02 §8 |

---

## Pre-synthesis hashes (2026-10-09)

`config.yaml`, `SOUL.md`, `memories/MEMORY.md`, `memories/USER.md`, and every file under `plugins/` matched the Phase 1 table. `.env` still missing. Not BLOCKED.

`token.dpapi`: size 926, mtime `2026-10-07T22:58:24.2521851Z`. Same as Phase 1. Contents not read.

---

## `[EXT]` source table

| URL | Read date | Supports |
|-----|-----------|----------|
| https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list | 2026-10-09 | history.list parameters, 404, historyId lifetime |
| https://developers.google.com/gmail/api/guides/sync | 2026-10-09 | partial sync and full resync on 404 |
| https://developers.google.com/workspace/gmail/api/guides/sync | 2026-10-09 | same sync guide, workspace host |
| https://developers.google.com/workspace/gmail/api/guides/push | 2026-10-09 | Pub/Sub push and pull; watch renewal |
| https://developers.google.com/workspace/gmail/api/reference/rest/v1/users/watch | 2026-10-09 | users.watch |
| https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get | 2026-10-09 | message id and threadId |
| https://developers.google.com/workspace/gmail/api/guides/list-messages | 2026-10-09 | messages.list |
| https://developers.google.com/workspace/gmail/api/auth/scopes | 2026-10-09 | gmail.readonly and gmail.compose Restricted |
| https://developers.google.com/workspace/gmail/api/reference/quota | 2026-10-09 | Gmail quota units |
| https://developers.google.com/workspace/calendar/api/v3/reference/events/list | 2026-10-09 | syncToken exclusions |
| https://developers.google.com/workspace/calendar/api/guides/sync | 2026-10-09 | sync token and 410 |
| https://developers.google.com/calendar/api/guides/errors | 2026-10-09 | 410 fullSyncRequired |
| https://developers.google.com/workspace/calendar/api/guides/push | 2026-10-09 | Calendar webhook channels |
| https://developers.google.com/calendar/api/guides/quota | 2026-10-09 | Calendar quota |
| https://developers.google.com/identity/protocols/oauth2 | 2026-10-09 | Testing refresh tokens expire in 7 days |
| https://developers.google.com/identity/protocols/oauth2/production-readiness/overview | 2026-10-09 | production readiness |
| https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification | 2026-10-09 | restricted-scope verification |
| https://support.google.com/cloud/answer/15549945 | 2026-10-09 | audience, 7-day test authorizations, 100-user cap |
| https://support.google.com/cloud/answer/13464323 | 2026-10-09 | personal-use exemption text |
| https://developers.google.com/workspace/drive/api/guides/api-specific-auth | 2026-10-09 | drive.readonly Restricted |
| https://developers.google.com/workspace/guides/configure-oauth-consent | 2026-10-09 | consent screen configuration |
| https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps | 2026-10-09 | LocalDumps not enabled by default |
| https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerpowersettingnotification | 2026-10-09 | power setting notifications |
| https://learn.microsoft.com/en-us/windows/win32/power/pbt-apmresumeautomatic | 2026-10-09 | resume-from-sleep broadcast; user presence not implied |
| https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata | 2026-10-09 | DPAPI user-scope decryption |
| https://pypi.org/pypi/jsonschema/json | 2026-10-09 | P2-D17 candidate metadata; not installed |

---

## Running findings list

44 findings was the count before addendum P9PRE-ADD-1. The list is now 45 findings: 12 HIGH, 18 MEDIUM, 2 LOW, 13 MATCH. IDs P9PRE-AUD-01 through P9PRE-AUD-45.

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
| P9PRE-AUD-27 | [RISK] | MEDIUM | 05 | Default ranking path has no aux concurrency cap |
| P9PRE-AUD-28 | [MATCH] | — | 05 | Consolidation keeps pending rows when the model call fails |
| P9PRE-AUD-29 | [GAP] | MEDIUM | 05 | No parser refuses to treat ranking JSON as identifiers |
| P9PRE-AUD-30 | [MATCH] | — | 05 | The facade cannot call tools |
| P9PRE-AUD-31 | [GAP] | HIGH | 06 | No open-loop or watcher-queue table |
| P9PRE-AUD-32 | [RISK] | MEDIUM | 06 | Memory-store text is on the forget path; a workspace-only file is not |
| P9PRE-AUD-33 | [MATCH] | — | 06 | is_brian_turn says the turn is Brian's; it does not certify each argument |
| P9PRE-AUD-34 | [RISK] | MEDIUM | 06 | Every pre_llm_call context is concatenated |
| P9PRE-AUD-35 | [GAP] | MEDIUM | 06 | forget_memory deletes a fixed table list |
| P9PRE-AUD-36 | [GAP] | HIGH | 07 | A plugin cannot push an event the client will speak |
| P9PRE-AUD-37 | [RISK] | HIGH | 07 | A synthetic prompt on the TUI agent can pass P8-D02 and be stored as a user turn |
| P9PRE-AUD-38 | [RISK] | MEDIUM | 07 | Echo rejection uses the last accumulated reply |
| P9PRE-AUD-39 | [GAP] | MEDIUM | 07 | The HUD has no watcher-health source |
| P9PRE-AUD-40 | [GAP] | HIGH | 07 | No component claims a queue row and checks live speech state together |
| P9PRE-AUD-41 | [RISK] | MEDIUM | 05 | json_schema is not enforced; jsonschema is absent from the venv |
| P9PRE-AUD-42 | [RISK] | HIGH | 06 | Injected context is stored in `api_content` and replayed on later turns |
| P9PRE-AUD-43 | [RISK] | MEDIUM | 02 | `zola_memory.register` runs per memory-enabled agent, including cron |
| P9PRE-AUD-44 | [RISK] | MEDIUM | 05 | `classify_items.py` scores mail with no tools and drops a bad parse as silence |
| P9PRE-AUD-45 | [RISK] | HIGH | 02 | A live turn can arm a heartbeat or /loop through `terminal`; P8 guards do not match |

---

## Closeout

Phases 1–11 COMPLETE. Final findings: 45 (12 HIGH, 18 MEDIUM, 2 LOW, 13 MATCH).

11a (2026-10-09): worktree changes are only `zola-architecture/audit/p9pre-phase9/`. hermes-agent porcelain empty at `345cd2b057a452236de401d3534b8502a7465e8d`. Live-profile hashes match Phase 1 (67 files; `.env` still missing). `token.dpapi` size 926, mtime `2026-10-07T22:58:24.2521851Z` (unchanged; contents not read).

Audit content SHA (11c): `4bf9a32497efc5c589b2d7b792466bc98f6ab4b4`  
Merge SHA (`--no-ff` merge commit, not the HEAD after this metadata commit): `925fa2c7951e9415e09c156209270bb0d3504f7d`  
Scratch `C:\Users\test\Dev\zola-spikes\p9pre\`: deleted at step 11i, after this commit.

