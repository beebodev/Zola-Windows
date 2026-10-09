# P9-FIX-ARM Progress — Only Brian's own turns pass the Brian-only gate

## Branch

- Branch: `p9-fix-arm`
- Base `main` HEAD: `d2db1b85b7abc2411d2f4a5666289a795c354c58` (`audit: record P9PRE merge SHA`; working tree clean)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (porcelain empty; `chore(release): v0.21.3 (v2026.9.14)`)
- Prompt file: `C:\Users\test\Dev\zola-spikes\prompts\P9-FIX-ARM_Prompt_v1.1.md`
  SHA-256 `F30BB679DE35438171785CE24EDDC25FD9CF9B39C8848FB8065667534C0D5B18`
- This Phase 1 message contained the prompt body and no separate comparison digest. The SHA above is the canonical file, hashed 2026-10-09.
- Scratch: `C:\Users\test\Dev\zola-spikes\p9-fix-arm\` (deleted at closeout; never committed)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and setup | COMPLETE |
| 2 | Grounding (read-only) | COMPLETE — decision recorded |
| 2b | Wrap grounding (read-only) | COMPLETE — Claude approved with six conditions |
| 3 | Implement the approved option | COMPLETE — stopped for review |
| 4 | Review checkpoint | COMPLETE — stopped for review |
| 5 | Deploy and smoke | COMPLETE — smoke test passed |
| 6 | Closeout | IN PROGRESS — implementation committed |

## Guardrails (summary)

- G-SCOPE: `hermes-plugins/zola_workspace/` (gate, guards, tests) and `hermes-plugins/zola_memory/` (Brian approved it at the Phase 2 decision). Live mirror and `config.yaml` only in Phase 5 as approved. This progress doc. Nothing else.
- G-ORIGIN: Brian-only actions need positive, non-model-controlled evidence of the client's `prompt.submit`, or a verified replay of one. Armed-state checks, disabled features, text matching, and tool guards do not satisfy this alone. No trustworthy signal without a Hermes or client change → BLOCKED.
- G-ORIGIN-LIFECYCLE: evidence bound to one `turn_id`; created before the authorization hook; unavailable to later turns; invalidated on completion or cancellation (crash-recovery exception verified); safe under concurrency; stale after a serve restart.
- G-SEND-NOT-REPLAYED: a crash replay never creates, restores, or reuses send authorization.
- G-FAIL-CLOSED: unknown origin, missing record, exception, or unreadable state → not Brian.
- G-NOCHANGE: no client change unless the Phase 2 STOP approves one; no Hermes edits; no lore, identity, or `SOUL.md` edits; no Google calls.
- G-STOP: stop after every phase. Closeout only on "proceed to closeout".

## Phase 1 baseline (2026-10-09)

Live profile `%LOCALAPPDATA%\hermes\profiles\zola\`. Hashes match the P9PRE Phase 1 baseline for every file that baseline listed. Contents of the token store were not read.

| File | SHA-256 |
|---|---|
| `config.yaml` | `6ED53ACE35C223ED1B9D5AF1696A6C449626C57B37B38F099F2DCC5B6F4B8E76` |
| `SOUL.md` | `38577550B251AFC6AA21432BA1DF12DF70A6F56378ADD6DC2E30211358C9C5E2` |
| `.env` | MISSING |

### `plugins/zola_workspace/`

| File | SHA-256 |
|---|---|
| `__init__.py` | `ED527D20DD94CDE8D2EB6CC97A627B0B3EAEA2A9B4ACA3D6B037410882E26BA6` |
| `auth.py` | `A8AA8810FC9DF899788273181C8199645E2BAAD3D35A0C1ADAE318F4423E7667` |
| `contacts.py` | `E34343C96CCF8CDAF4FFB91C498CC6FEFFDF5020554D092A5F567831CDB3C3DE` |
| `drive.py` | `2EF13563A57DCD6F30F72D3CF4122C54DF74BF104C37EBD082476065D947CC66` |
| `framing.py` | `0E91FFC883D42DE7AC143B01D2CDBFD822B1EA34B40355D32E9924C10E3B515A` |
| `gcal.py` | `6F17605A69B606946DC9C8ADC50EEB84282E212AABCA2E1EF57778EB7BCDD3BA` |
| `gmail.py` | `DD018F6AE1D220F9D5B3EE10D60874784E556E1EB46D4F7CD3B4079214D3E7A7` |
| `google_http.py` | `81281017D1A93DE26936DC660D2A9E9F7F1DF53411175B95F9136B9F92765B82` |
| `guards.py` | `EB5C505274D2B0EC9CE4826A5E2DBE2C58A3C8B41E28E205CB39BC60C62AF680` |
| `log.py` | `CE00D6FB46FFEAB36E2A212E05BB68FC7ED6CB9292D30E8380355429D2976650` |
| `plugin.yaml` | `4E485461744F49222E1DD7EA378ADB899B2E3C064B4DCFF72F79027C96B7D738` |
| `posture.py` | `E55D8E8253C5C8867C356C20A96716949DCFA22D5E5C2C9391D07219C292CDA9` |
| `read_common.py` | `B37CF4A91E7A211CFBC1865AC925658B28D26BD95A4B98908C4C6F926FB3F562` |
| `send_gate.py` | `0432FAC90B50AAD604C17BC2E2F43C6BFC85F0EF26568EFFE66835B4690ECA33` |
| `setup.py` | `1FFEAAC4DE12A47286ACB2B2C9780D9C9B4E86B151802575ACAFBCC0712D3696` |
| `taint.py` | `6390F091CA3A1ACE957BE7D18A80F1F926EC486FBF81025AC24B016D76CC344E` |
| `textclean.py` | `E5983EBC83858C69C0F53D473DA63A78C15739CF4226453E24EF1C28928DBE64` |
| `turn_context.py` | `7AA76D6C35544B475F299A9D3AFC7EC72BBEFF07FE95687C56B341C19D1BE337` |
| `__pycache__/__init__.cpython-312.pyc` | `C01E055315239505E5466245BAC917E7539B5AD1702B314B9444E5105525D86F` |
| `__pycache__/auth.cpython-312.pyc` | `567849A56780545A08566D72D9B3F341ECA1368AC3EF1D3687B29CD87A894EC6` |
| `__pycache__/contacts.cpython-312.pyc` | `02E1E8A7C6C355269D8FFA57894B3F17454530E480A2D966A2D3EC31CF56ED5F` |
| `__pycache__/drive.cpython-312.pyc` | `38D97D544FFB7776023334D85F39A3AE788D5A81013714600BFBAEAC073ECB97` |
| `__pycache__/framing.cpython-312.pyc` | `04FE8C196840AC551C8F5267D5449B0CB6F205A54D15800D072E35D67605F5D1` |
| `__pycache__/gcal.cpython-312.pyc` | `69F7AABB1D01138AF8C1FCC64C756366CB9C8A83C562533CB713C22049DF37B7` |
| `__pycache__/gmail.cpython-312.pyc` | `418E3156258DE692889D0E1E23BC79E00612E24064130683E4D53F6D32419EAB` |
| `__pycache__/google_http.cpython-312.pyc` | `BA51A9448D52A353CE4B874067EEFE025EF30CD02727F6E0C1979B98D087BB13` |
| `__pycache__/guards.cpython-312.pyc` | `6881946401189DA12D3D707644127DF1BB7494F11D240E05221BECCDF3D8FECF` |
| `__pycache__/log.cpython-312.pyc` | `D8B1923885E2D7E1F41B7DC81BB4ECD6185AE28E86BA50DD23333C3A3981C514` |
| `__pycache__/posture.cpython-312.pyc` | `21F06FE209B54A8A5078CF3F30285884D7F5B19785CB10DC21CF4339BF105342` |
| `__pycache__/read_common.cpython-312.pyc` | `F797DB7E7DCF2CF1C1288A74CD1F0094590AFF1956A6D330EF0D471A2C1B1089` |
| `__pycache__/send_gate.cpython-312.pyc` | `7066BF85586AC9050A18B3D793B4131D730C2945E2A1F93EC6245D936E574C9B` |
| `__pycache__/taint.cpython-312.pyc` | `5B93232B4B2E93FD294DC604E718B2217DC59DE221A966E0821C2C04DFA17D42` |
| `__pycache__/textclean.cpython-312.pyc` | `E8A8702CC9B1C91E884D223D1B2DB5450F0955D1EA29A8C38931674FCD94DF16` |
| `__pycache__/turn_context.cpython-312.pyc` | `74629E17DE1A5CC9EBFF9517435D9F37AC698F3C6FECE521E93C5BD09CEE09B4` |

### `plugins/zola_memory/`

| File | SHA-256 |
|---|---|
| `__init__.py` | `7FAA42BC030B329EB5F078B80EC45183104105361A29E880EAC3CCCCF9994C11` |
| `consolidate.py` | `F7B886C35B5817E74C1F92021D5837123F65B0177354D4D36B6B0C441903B992` |
| `fact_index.py` | `AA0CCE9E599BA94F933A8619E2094D3A21192BD4AA785510A9D28FBC53D81B02` |
| `forget.py` | `A9B62AA822DBAD0A350FE84CB004C4E63124F4FBEA98F591D4454EDDCC1BB306` |
| `llm_access.py` | `EC5A8F319628CB24DEEB0177397D34B754A51B30F80C025D4F93D5E5189FEC57` |
| `log.py` | `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` |
| `pending.py` | `9FF6156CD946C08BFD737EDFFC15C6DAE2D865AB0C34ED332F48056DDA854769` |
| `provider.py` | `E292093763665B0A35E38C67166F84E372493D4F4016704F006217A15E76A18A` |
| `registry.py` | `86AA4DA04D67AB911D569AB1D9774A86E1A36F75F9B1931D49CA3F0272EE771D` |
| `retrieve.py` | `53D8044D896F6F769AA10EF99BAB67083ADF19AA3E01858A067A870916C0290D` |
| `store.py` | `C471EA121F993BD00D5E68EEF0DEFB92FBDD3D606774CA78B89ADF1B34CB00E8` |
| `time_context.py` | `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` |
| `__pycache__/__init__.cpython-312.pyc` | `BBA695FD7CB093DD247CA58C50F2E463DEFDA9258DB86B35424E0D78ABA454A2` |
| `__pycache__/consolidate.cpython-312.pyc` | `4C997ED05687F6DD61503604708587E5AD971ECBDE8BD4EDD44278870490A782` |
| `__pycache__/fact_index.cpython-312.pyc` | `BDBAFBCFB5331CE037A758A90BC574BBA0FD3D1B93B585A36CC33A207B173D4C` |
| `__pycache__/forget.cpython-312.pyc` | `D4EDF6C6FD46490D5D9D5B404E102E46EA7DA6EF190DCCF3D09328F396452007` |
| `__pycache__/llm_access.cpython-312.pyc` | `11D5178130C84CDB7531FF8D900C9FBB96236E9C5E243544C00B9B774C5C095B` |
| `__pycache__/log.cpython-312.pyc` | `E62C5C1DD987044650217BF3708D5D0A535278A84F0A98DC77E16BB1B0B9E950` |
| `__pycache__/pending.cpython-312.pyc` | `5148F60A26FDB64E81735B6F092DE8BE0CB4C6C946B37EE1B45B18E5CEDF15BA` |
| `__pycache__/provider.cpython-312.pyc` | `2E2715D1BD508D1E51AA961F5A8A508FD8A83193F7248896EF561E4EF24A01F6` |
| `__pycache__/registry.cpython-312.pyc` | `74F850D725D4642468A8BB1F421FC2705276090E0F5081CC79A6050C5026828D` |
| `__pycache__/retrieve.cpython-312.pyc` | `9E2FF5CCA225C7E072EDB90E9504EC89A86CFD4B42010742B7543C10F7737DE7` |
| `__pycache__/store.cpython-312.pyc` | `AFCCA4DC137201EF3D9B6EB39C17A0F1BECE4565B55F5E9E69E44ECB3649ABE3` |
| `__pycache__/time_context.cpython-312.pyc` | `3984F7434756768B1DCFC660860303A5DF092BD4BFD4915C08B0079585D51F78` |

### Token store

`zola_workspace\token.dpapi`: name `token.dpapi`, size 926, mtime `2026-10-07T22:58:24.2521851Z`. Contents not read. Unchanged from the P9PRE baseline.

## Approved option

Brian, verbatim (2026-10-09): "Option 1 via a runtime wrap of prompt.submit, no Hermes edit. Crash replay gets no Brian authority. Add the guard rows and drop the cronjob toolset as defense in depth. Bring zola_memory into scope."

Phase 3 implemented the approved option under Claude's six conditions. No live profile edit, no Hermes edit, no client edit.

## Phase 2 — Grounding (read-only, 2026-10-09)

Pin `345cd2b057a452236de401d3534b8502a7465e8d`. No source edits.

Shared `pre_llm_call` shape for every turn on the session agent (`agent/turn_context.py` `_collect_pre_llm_call_context` L663–686): `platform` from `agent.platform`, `parent_session_id` from `agent._parent_session_id` or `""`, `turn_id` from `_bind_turn_identity` L473–477, `user_message` the turn text, `sender_id` from `agent._user_id`. Zola's serve builds that agent with `_resolve_session_platform()` (`server.py` L1415–1419) after the client removes `HERMES_DESKTOP` (`HermesProcessManager.cs` L211), and `_make_agent` (`server.py` L2342–2363) does not pass `parent_session_id` (`agent_init.py` L1141 stores the default `None`). `user_id` is the session's `auth_user_id`, set once at build (`server.py` L2358). Every row below therefore arrives as `platform=tui`, `parent_session_id=""`, a fresh `turn_id`, and the same `sender_id`. The `rid` is an argument of `_run_prompt_submit` (`prompt_turn.py` L796–801). It is not written onto the session, the agent, or the hook kwargs.

### A. Ways a model turn starts

| Entry | rid | Text | Live config can fire it | Agent can arm or trigger it | 
|---|---|---|---|---|
| Client `prompt.submit` → `_run_after_agent_ready` → `_run_prompt_submit` (`methods_prompt.py` L544, L502) | Client JSON-RPC id, a monotonic int (`ChatSocket.cs` L410). Body is `session_id` and `text` only (L285–289) | Brian's words | Yes. This is the typed and spoken path | The turn is the client's RPC |
| Heartbeat poll → `_maybe_fire_tui_heartbeat_tick` (`session_notifications.py` L198–223) | `__heartbeat__{ms}` | Hermes reads the stored heartbeat prompt | Poller runs (L589–591). Nothing is armed, so it does not fire today | Yes. Terminal or a `state_meta` write of `heartbeat:<session_id>` (`heartbeat.py` `save_heartbeat` L119–128). P8 guards do not match that write |
| `/loop` poll → `_maybe_fire_tui_loop_tick` (L233–255) | `__loop__{ms}` | Stored wakeup text, or, when the wakeup is a slash command that returns `type=send`, `payload["message"]` (L172–189) | Same poller. Nothing armed | Yes. `loop:<session_id>` (`loops.py` L236–240) |
| Goal continuation → `_dispatch_followup_turn` (`prompt_turn.py` L355–361, called L389) | Reuses the parent turn's rid | Hermes continuation prompt from `GoalManager.evaluate_after_turn` (L305–311) | Only while a goal is active. None is | Yes. `goal:<session_id>` (`goals.py` L499). Arming during a turn lets that turn's post-hook chain the follow-up |
| Notification poller → `_notif_submit` (L157–161), from process events (L400–408, L487–490) and kanban (L380–397) | `__notif__{ms}` | Hermes formats the event or the kanban batch | Poller runs. A finished background process can deliver a turn. Kanban needs a subscription; `kanban` is not in `platform_toolsets.cli` | Terminal can start a background process whose completion is delivered here |
| Bot live delivery → `_poll_bot_live_delivery_once` (L513–554) | `__bot_dm__{delivery_id}` | Mailbox envelope `claimed["message"]`, plus `turn_author` | Poller runs. The client does not write envelopes. No turn without one | Only by writing that mailbox |
| Crash replay → `_maybe_schedule_auto_continue` (`session_auto_continue.py` L57–114) | `__auto_continue__{ms}` | Hermes note plus the marker's original prompt (`_auto_continue_note` L49–54). `display_kind="auto_continue"` | Yes when `desktop.auto_continue.enabled` is true. The profile omits the key; the pin default is true (`config_defaults.py` L2365–2369; reader L21–30) | A crash leaves the marker. The agent does not schedule this itself |
| Busy-queue drain → `_drain_queued_prompt` (L286–320) | The rid of the turn that drained it | The text `prompt.submit` queued while the session was busy | Yes, when Brian sends during a running turn | The queued text is from the client RPC |
| Compute-host `_run_real_turn` (`compute_host.py` L213–245) | Frame `request_id` | Frame text | No. `dashboard` is absent; `turn_isolation` defaults false (`server.py` L1178, L1198) and the in-process agent stays on the inline path (`compute_host_bridge.py` L29–34) | No, under this profile |

Not the session agent, and not a pass of the current gate: `delegate_task` sets `parent_session_id` to the parent session (`delegate_tool.py` L245). `prompt.background` (`methods_prompt.py` L975–986) builds a new agent with `platform="tui"` and no parent (`agent_callbacks.py` L275–303), so that agent would pass today's `tui` + empty-parent check. Zola's client does not call `prompt.background`. `prompt.preview` limits toolsets to `terminal` and `file` and sets `skip_memory=True` (L306–308).

### B. Origin signals a hook or tool handler can read

| Candidate | Separates `prompt.submit` from every synthetic row in A | Can a turn forge it |
|---|---|---|
| `rid` | The shapes differ for heartbeat, loop, notif, bot, and auto-continue. Goal continuation and the queue drain reuse the parent rid. The rid is not on `_current_runtime_session_record`, `inflight_turn`, `_active_turn_marker_key`, `_TurnScopes`, or `approval_context`. RPC ContextVars do not follow onto the turn thread (`prompt_turn.py` L823–826). The hook kwargs omit it | Not reachable, so it cannot be used. A reachable copy of the parent rid would also bless the goal follow-up |
| `display_kind` / `display_metadata` | Client sends neither (`ChatSocket.cs` L285–289). The RPC keeps only the literal `hidden` (`methods_prompt.py` L552). Heartbeat, loop, goal, kanban, and the queue drain also leave it unset. `auto_continue` is set only on the crash replay. Process completion and async delegation set their own kinds. The value is stored on the user message (`turn_context.py` L572–577) before the hook, and is not a hook kwarg | The client cannot set a unique kind. The model does not get a parameter that sets it. A process that can speak the RPC could |
| `turn_author` / `agent._turn_author` | `parse_turn_author` (`turn_author.py` L58–80) accepts a dict or JSON with `id` and `name`. The RPC rejects a client dict: `methods_prompt.py` L565–567, "turn author is stamped by the gateway, never by a client". Client turns and heartbeat/loop/goal/replay leave it `None`. Bot delivery passes `claimed["author"]` | A client-supplied author is refused. `None` is shared with the synthetic turns that matter |
| `sender_id` (`agent._user_id`) | One value for the life of the agent (`server.py` L2356–2358). Heartbeat and the client turn match | No per-turn write |
| Auto-continue marker | `_record_turn_marker` (`prompt_turn.py` L118–131) sets `auto_continue=True` whenever `terminal_callback` is absent (L830). That includes the client turn, heartbeat, loop, goal, and the replay. Bot delivery passes a callback, so its marker is `auto_continue=False` and is not replayed (L68–69). The marker records prompt text and attempt count, not "this came from `prompt.submit`" | The flag does not identify the client |
| `VALID_HOOKS` on the RPC | `pre_command` fires for a slash command and its return is ignored (`plugins.py` L191–198). `pre_gateway_dispatch` fires for a messaging `MessageEvent` (L130–133), not this JSON-RPC. `on_session_start` / `on_session_end` / `agent_loop_stopped` are session and interrupt events (`session_lifecycle.py` L15–22, L239, L414–416). No hook fires on `prompt.submit` | There is no RPC hook to record "the client submitted turn X" |
| Client field Hermes already passes to a hook | `SubmitAsync` sends `session_id` and `text` only. `surface` and `voice_context` would be stored on the session (`methods_prompt.py` L582–588) and are not hook kwargs. Zola does not send them. No per-launch secret is forwarded | Text is the turn body. A sticky session field would still be set during a later heartbeat |

### C. Armed-state veto

Per session, a plugin can read:

- `HeartbeatManager.is_active` (`heartbeat.py` L152–153) via `load_heartbeat` → `SessionDB.get_meta("heartbeat:<session_id>")` (L102–116). `hermes_state.py` `get_meta` L1481–1486 is a `SELECT`.
- `LoopManager.is_active` (`loops.py` L395–396) via `loop:<session_id>` (L236–240).
- `GoalManager.is_active` (`goals.py` L1099–1100) via `goal:<session_id>` (L499).

There is no list-all helper. Any-session means a `SELECT` on `state_meta` key prefixes. `cron.jobs.list_jobs` (L1881) calls `load_jobs`, and `load_jobs` calls `ensure_dirs` (L1272–1276, L582–588), which creates cron directories. A read that must not create directories is `jobs.json` existence on the profile cron path. The file is absent.

Timing: `_notif_claim_turn` (L145–150) starts a heartbeat only when `running` is false. A heartbeat cannot start a second turn while the arming turn holds `running`. The arm itself can land mid-turn, between a check at `pre_llm_call` and a later tool check. The fire happens on a later idle poll, after `running` is cleared (`prompt_turn.py` L863–864), and that window races `_run_post_turn_followups`.

### D. Config switches

| Feature | Key at the pin | Default | Profile yaml | Zola uses it |
|---|---|---|---|---|
| Heartbeat | No enabled key. Cadence is the stored row | Fires when a row is active | No `heartbeat` key | No row armed |
| `/loop` | `loops.min_interval_seconds` 30, `max_ticks` 100, self-paced floor 60, ceiling 900 (`config_defaults.py` L1308–1313). No enabled key | Poller always runs | Key absent; defaults apply | No row armed |
| Goals | `goals.max_turns` 20 (L1300–1303). No enabled key | Continuation runs while a goal is active | Key absent | No row armed |
| Crash replay | `desktop.auto_continue.enabled`, `freshness_minutes` 15, `max_attempts` 2 (L2365–2369) | `enabled` true | Key absent; reader default true (`session_auto_continue.py` L21–30) | The recovery path is on |
| Notification submits | No key. Poller is process code, 5s (`session_notifications.py` L137) | On with the session | — | Process-completion turns can fire. Kanban toolset is not enabled |
| Goal follow-up | Same as goals | On while a goal is active | — | No |
| Bot DMs | No key. Poller calls `_poll_bot_live_delivery_once` | On with the session | — | No envelopes from this client |

### E. Arming paths to guard

These are defense in depth. Each is bypassable.

| Path | `pre_tool_call` shape | Legitimate Zola need |
|---|---|---|
| (a) `terminal` whose command names `state.db` together with `sqlite3`, Python `sqlite3` / `connect`, or `UPDATE` / `INSERT` aimed at `state_meta`. `write_file` / `patch` whose path is `state.db` | Block those tool names when the command or path matches. A bare `import sqlite3` does not name `state.db` | No write to `state.db`. Ordinary terminal use stays |
| (b) `terminal` command matching `hermes cron` or a `hermes` subcommand that writes a schedule | Block that command shape | No |
| (c) `write_file` / `patch` whose path contains `cron/jobs.json` or `cron/` | Block those paths | No |
| (d) `cronjob` toolset | One config edit. Before: `platform_toolsets.cli` includes `cronjob` (live list: browser, clarify, computer_use, connections, cronjob, delegation, file, image_gen, memory, session_search, skills, terminal, todo, tts, vision, web, zola_tools, zola_workspace). After: the same list without `cronjob`. Tool is `cronjob_manage` (`toolsets.py` L115–118) | No |

`execute_code` is not in the live toolset list. Residuals that a row does not block: an encoded Python writer, a copy of `state.db` under another name, SQL through a tool the row does not name, and a `prompt.submit` forged on the local socket.

### F. The same hole elsewhere

`zola_memory` `is_brian_conversation` (`forget.py` L252–254) is `platform` in `{tui}` and an empty parent. `provider.initialize` copies the agent's platform and parent (L102–103). `sync_turn` writes a pending row when that check passes and `turn_disposition` returns `keep` (`provider.py` L263–277). Ordinary text returns `keep` (`forget.py` L819). A heartbeat turn on this agent is stored as a pending Brian turn and can later consolidate into an episode. `forget_memory` uses the same check (L1012, L1101). `retrieve.prefetch` uses it to decide episode text (retrieve.py L255). The memory-taint guard (`guards.py` `evaluate_memory_taint` L460) keys off taint, not origin.

`send_gate.on_pre_llm_call` (L614–634) writes a send authorization when `passphrase_match(user_message)` and a live draft exists. It does not call `is_brian_turn`. `passphrase_match` (L131–138) returns false when the text contains `previous turn was interrupted`, which the crash-replay note contains (`session_history.py` L162). A synthetic turn whose text is exactly `Approved. Send it.` matches, and today's `is_brian_turn` then lets `_gate` through (`gmail.py` L526–529, `gcal.py` L519, `read_common.py` L109–110).

### G. Options

No choice made.

**(1) Positive origin — required by G-ORIGIN.** No row in B is positive evidence of the client's `prompt.submit`. Checking armed state, config, request text, or a tool guard does not meet the rule. A field added only in `ChatSocket.SubmitAsync` is dropped: `prompt.submit` never copies an extra field into `pre_llm_call`. The smallest change that would meet the rule is a Hermes change: record, at `prompt.submit` only, evidence bound to the `turn_id` created in `_bind_turn_identity`, visible to the hook before it returns, and carried on the busy-queue envelope so a queued client send stays client-origin. A per-launch secret in that field is the trust argument against a local process forging the RPC; the secret must not appear in the user text. That edit is outside this track's G-NOCHANGE. Cost: a pin patch, a client send of the field, and tests for queue, concurrency, restart, and replay. Lifecycle of that evidence, once it exists: (a) key it by `turn_id`, not session; (b) write it in the RPC handler before the turn thread reaches `pre_llm_call`; (c) delete it when the turn completes or is cancelled, and do not leave it for the goal or heartbeat turn that runs next; (d) a crash replay is a new turn with `display_kind=auto_continue` and must not inherit the dead turn's send rights; (e) keep it in process memory so a restart cannot revive it, and key concurrent turns separately.

A plugin wrap of the RPC, with no `hermes-agent` diff, is new behavior, not a signal the pin already exposes. It has the same lifecycle duties, plus the queue-drain race after `running` is cleared.

**(2) Armed-state veto.** Refuse Workspace while this session has an active heartbeat, loop, or goal, and optionally while `jobs.json` exists. Log it as a posture violation. This covers goal follow-ups, because those run only while a goal is armed. It does not cover process-notification turns, which can fire with nothing armed, or bot-DM turns, which can fire when an envelope exists. This profile has no envelopes. It does not cover a heartbeat that is armed and fired as its own turn unless the veto runs on that turn and sees the row. It does not cover a turn that arms nothing and whose origin is still synthetic.

**(3) Disable the features.** `desktop.auto_continue.enabled: false` turns off crash replay. No key disables the heartbeat, loop, or goal poller, notification submits, or bot-DM polling. `goals.max_turns` and `loops.max_ticks` are budgets, not off switches.

**(4) Guard rows and removing `cronjob`.** The rows in E, plus deleting `cronjob` from `platform_toolsets.cli`. They block the obvious arming commands. They leave direct socket writes, encoded writers, and every synthetic turn that is already armed or that is not an arming path (notifications, bot DMs, follow-ups, replay).

Combinations:

| Combination | Still open |
|---|---|
| (1) alone | Arming still works; the armed turn fails the gate. Residuals are a forged RPC and any path that fails to carry the queue stamp |
| (2)+(3)+(4) without (1) | Heartbeat, loop, and goal turns fail only while the veto can see the row. Process notifications still pass. A turn that fires before the veto re-reads, or a cleared row, still passes. G-ORIGIN is unmet |
| (1)+(2)+(4), and (3) for auto-continue if Brian wants replay off | Meets G-ORIGIN only through (1). (2) and (4) are defense in depth |

**Crash replay.** The replay is the turn with `display_kind=auto_continue` and rid `__auto_continue__…`. Its text is the note plus the marker prompt. The marker does not record that the dead turn was a `prompt.submit`. Treating the note prefix as proof is text matching. `display_kind` is Hermes-set on this path and is readable on the staged user message, not as a hook kwarg. If Brian approves replay continuation, reads and memory can resume on that kind. Send authorization must not be created, restored, or reused (`send_gate.on_pre_llm_call` must not write `_auths`). Today's `passphrase_match` already rejects the note because it contains `previous turn was interrupted`. A synthetic turn whose whole text is `Approved. Send it.` has no note and must get no authorization either.

## Phase 2b — Wrap grounding (read-only, 2026-10-09)

Pin `345cd2b057a452236de401d3534b8502a7465e8d`. No source edits. Line checks that were asked: `server.py` L86 is `_methods`, L802 is `_methods.get(method)` inside `handle_request`, `main.py` L2510–2511 is `discover_plugins()` (the comment above it is L2504).

### 1. Dispatch table and when it fills

Zola's socket is `ws://…/api/ws`. `hermes_cli/web_routers/chat_ws.py` L561–565 mounts that route on `tui_gateway.ws.handle_ws`. The receive loop calls `server.dispatch` (`ws.py` L359). `dispatch` (`server.py` L844–862) calls `handle_request` on the calling thread for methods outside `_LONG_HANDLERS`. `prompt.submit` is not in that set (L156–171), so the client's submit is inline. `handle_request` (L797–813) reads `_methods.get(method)` at call time and invokes that function. Replacing the dict entry is visible to the next request without patching `dispatch`.

The dict is empty at plugin `register()`. `discover_plugins()` runs in `_dashboard_prepare_runtime` (`main.py` L2456–2511), and that function returns before `start_server` (`main.py` L2569–2580). `tui_gateway.server` is imported later, in the web lifespan (`web_server.py` L174). The import's tail (L3236–3265) calls each split module's `register`, and `bind_module` finishes with `HandlerRegistry.install` (`method_ctx.py` L62–69, L128–130), which is `register_method` → `_methods[name] = fn` (`server.py` L770–774). `methods_prompt.py` only appends to its registry at decoration time (`L11–12`, `@method("prompt.submit")` at L544). A wrap that runs inside `zola_workspace.register` and does not itself import `tui_gateway.server` finds no `prompt.submit` key. There is no later plugin hook between that import and the socket.

The install point that works with no Hermes edit: `zola_workspace.register` imports `tui_gateway.server` (that import fills `_methods`) and then replaces `_methods["prompt.submit"]`. The lifespan import then finds the module already loaded and does not run the install loop again. A later `register_method("prompt.submit", …)` would overwrite the wrap. Nothing on the serve path does that after the one import.

Two production paths call the handler without going through `handle_request`. The claim that nothing calls it internally does not hold.

- `methods_bot_relay.py` L110, inside `bot_relay.deliver` (L59). It looks up `_methods["prompt.submit"]` at call time, so it hits the wrap. `bot_relay.deliver` is a long handler (L164). `handle_request` has set `_current_rpc_method` to `bot_relay.deliver` for that outer call (`server.py` L811–813).
- `hosted_room_server_rpc.py` L35 and L73. `HostedRoomServerRPC._call` invokes `server._methods[method]` directly. The room submit passes `_hosted_task` and `_hosted_terminal_callback`.

`_current_rpc_method` (`server.py` L181–183) is set only around `handle_request`'s call. Its own comment says the method string is client-supplied and the ContextVar is not authorization. For this wrap it is only a discriminator: a client `prompt.submit` sees the value `prompt.submit`; the bot-relay inner call sees `bot_relay.deliver`; the hosted-room call sees the default `""`. Ticket only the first. Also skip a call whose params carry `_hosted_task`, `_hosted_terminal_callback`, or a `DeliveryAuthor` (`methods_prompt.py` L565–571).

### 2. Ticket at the wrapper

The wrapper is `(rid, params) -> dict`, the same signature `handle_request` uses. Before the original runs it can read `rid`, `params["session_id"]` (the UI sid), and `params["text"]` (raw). `_sessions.get(sid)` (`server.py` L85, populated in `_init_session` L2402–2422) is the session record. `session_key` is on that record. `agent` may still be `None`: the handler returns `{"status": "streaming"}` and only then the turn thread waits for the build (`methods_prompt.py` L655–662, `_run_after_agent_ready` L474–504). `agent.session_id` is the wrong key anyway: compression can replace it before `pre_llm_call` (`conversation_compression.py` `_adopt` path sets `agent.session_id` to the child, L1410; `recover_rotated_compression_session` L1451 runs from `build_turn_context` before the hook).

Hash the string `pre_llm_call` receives as `user_message`, which is `original_user_message` (`turn_context.py` L679, L943): `persist_user_message` when set, else the run message. `_invoke_agent` persists `prompt` when there are no images (`prompt_turn.py` L544–545). `prompt` starts as the handler's `text` (`L487`) and becomes `ctx.message` when the text contains `@` and reference expansion accepts it (`L488–503`). Notes for barge-in, reactions, and the HUD are prepended to `run_message` only (`L509–513`), not to `prompt`.

Handler transforms before that, in order (`methods_prompt.py` L546–593):

| Step | Effect on the hooked text |
|---|---|
| `sanitize_user_prompt_text` (`input_sanitize.py` L50–54) | This is the string to hash when later steps do not change it. Non-strings are left as-is. |
| `_typed_stop_phrase_response` (L169–187) | Returns `voice_stopped` and starts no turn. Issue no ticket. |
| `interrupted` (L555–558) | Latches a speech note on `run_message` only. The hooked text does not include it. |
| `display_kind == "hidden"` (L552) | Transcript kind only. Zola's client does not send it (`ChatSocket.cs` L285–289). |
| Truncation skill re-expand (L589–593) | Changes `text` only when a truncation param is set. Zola does not send those. |
| `@` expansion | Can change `prompt` after the handler has returned. A ticket hashed from the sanitized submit then does not match. Fail closed. |

The wrapper hashes after it knows the handler's result, not before:

- `streaming`: hash the sanitized text (post skill-expand only if truncation params were present). The turn thread uses that same `text` argument (`L656–657`).
- `queued`: `_handle_busy_submit` (`session_auto_continue.py` L240–284) may steer/redirect the live turn (`status` `steered` or `redirected`) or enqueue. Default busy mode is `interrupt` (`server.py` L328–330); the profile does not set `display.busy_input_mode`. A steer/redirect does not start a new `pre_llm_call`. Issue no ticket. A queue stores the text on `session["queued_prompt"]`. Text-only arrivals with no author merge as `f"{prev}\n\n{text}"` (`_enqueue_prompt`, L140–150). Issue a ticket only when the stored text still equals the sanitized submit. A merged string gets no ticket, so the drain turn fails closed.
- `voice_stopped` or an error envelope: no ticket.

The drain (`_drain_queued_prompt`, L286–320) calls `_run_prompt_submit` with `queued["text"]`, not the wrapper. The ticket has to already be on the session record. The drain turn's hook matches that stored text and consumes it. A merged body matches nothing.

### 3. Binding in `pre_llm_call`

Store tickets in process memory, keyed by the session record's identity (the dict in `_sessions`), with a list of `(text_hash, expires_at)`. One slot is not enough: the first turn can still be waiting on the agent build, `running` already true (`_lock_in_submit_turn` L531), and a second submit can queue and would overwrite a single slot before the first `pre_llm_call`.

On `pre_llm_call`, the turn thread has `_current_runtime_session_record` set to that same dict (`prompt_turn.py` L826), before `run_conversation`. Resolve the ticket from that object, not from `agent.session_id`. Hash `user_message`. On a match, delete that one ticket and record `turn_id → consumed`. Later tools on that turn use the `turn_id` binding. A second `pre_llm_call` for the same `turn_id` does not require a second ticket. A different `turn_id` needs its own match. No match, missing record, or an exception → not Brian, and drop any unmatched ticket for that session so a later turn cannot borrow it.

TTL has to cover `_wait_agent_for_prompt`. The cap is `_agent_build_wait_cap` (`server.py` L894–901): default 600s, override `agent.build_wait_timeout`. The hook runs after that wait. A TTL shorter than the cap refuses a slow first build. A TTL far past the cap leaves a ticket after the submit has already failed.

Concurrent sessions: the key is the session record, so two UI sessions do not share a list. Compression rotation changes `agent.session_id` and leaves the session dict in place, so the lookup still hits. Serve restart: the dict is empty. Crash replay is a new process and a new `_run_prompt_submit` with `display_kind=auto_continue` (`session_auto_continue.py` L114). It has no ticket. It gets no Brian authority and `send_gate.on_pre_llm_call` must not write `_auths`.

A synthetic turn whose `user_message` hashes equal to a still-live ticket for that same session would consume it. Heartbeat and loop text are the stored prompt, not the queued client line, unless those strings are identical.

### 4. Fail-closed self-check

`register` sets a marker on the wrapper and stores it in `_methods["prompt.submit"]`. If the import fails, the key is missing, or the stored function is not the wrapper, a process flag stays false. Startup proof is that assignment. There is no later startup hook.

Every Brian-only check calls one helper that, before any ticket lookup, reads `_methods.get("prompt.submit")` again. If the flag is false or the dict value is not the wrapper, refuse with `reason=origin_wrap_missing`. That covers a later `register_method` overwrite. The helper's own exception also refuses (`origin_wrap_missing` or `origin_unknown`, fail closed).

### 5. Consumers to switch

`zola_workspace` — the predicate is `turn_context.is_brian_turn` (`turn_context.py` L99–115) after the hook binds the `turn_id`. Call sites:

| Site | Lines |
|---|---|
| `read_common.authorize` | L110 |
| `gmail._search_impl` → `authorize` | L257 |
| `gmail._read_impl` → `authorize` | L337 |
| `gmail._gate` | L529 |
| `gmail._draft_impl` → `_gate` | L955 |
| `gmail._send_impl` → `_gate` | L977 |
| `gcal._calendar_query_impl` | L519 |
| `contacts._impl` → `authorize` | L97 |
| `drive._search_impl` → `authorize` | L283 |
| `drive._read_impl` → `authorize` | L348 |
| `workspace_status_handler` (`allowed_here`) | `__init__.py` L65 |
| `turn_context.pre_llm_call_hook` → `send_gate.on_pre_llm_call` | `turn_context.py` L139–143; `send_gate.py` L614–634 |

Passphrase capture writes `_auths` only after the origin helper accepts the turn. A replay and a synthetic `Approved. Send it.` write nothing.

`zola_memory` — `is_brian_conversation` (`forget.py` L252–254) is the predicate. Call sites:

| Site | Lines | What changes |
|---|---|---|
| `provider.get_tool_schemas` | L165 | Agent-level. The schema stays listed for this `tui` agent. The handler refuses. |
| `provider.prefetch` → `retrieve_episodes` | `provider.py` L175–185; `retrieve.py` L255 | No episode text without origin. |
| `provider.sync_turn` pending write | L263–277 | No pending row, so no later episode, without origin. |
| `forget.handle_forget_memory` | L1012, L1101 | Refuse. |
| `forget.pre_tool_call_hook` | L1351–1355 | Today a non-Brian conversation returns `None`, which does not block the tool. Switching the predicate without changing that fall-through would stop applying the ask-pending block on a heartbeat. The heartbeat path has to refuse the memory write, not skip the hook. |

### 6. Upgrade risk

Private names the wrap touches: `tui_gateway.server._methods`, `_sessions`, `_current_runtime_session_record`, `_current_rpc_method`, `register_method`; session keys `session_key`, `agent`, `queued_prompt`, `queued_prompts`, `running`; `hermes_cli.input_sanitize.sanitize_user_prompt_text`; handler params `session_id`, `text`, `display_kind`, `interrupted`, `queued`, `_hosted_task`, `_hosted_terminal_callback`, `_turn_author`; hook kwargs `turn_id`, `session_id`, `user_message`.

Loud failures if Hermes renames or reinstalls them:

- Install test: after `register`, `_methods["prompt.submit"]` is the wrapper. `AttributeError` or a missing key fails here.
- Client-turn test: `handle_request` of `prompt.submit` then `pre_llm_call` binds `turn_id`, and `is_brian_turn` is true.
- Replace test: put a different function in `_methods["prompt.submit"]`, and the next check refuses `origin_wrap_missing`.
- Internal-call test: a direct `_methods["prompt.submit"]` call with `_current_rpc_method` unset, or set to `bot_relay.deliver`, leaves no ticket; the following turn is not Brian.
- Queue test: an unmerged queued text still passes; a `\n\n` merge does not.

A rename of `_methods` or of the lookup in `handle_request` fails the first two tests. A second `register_method` after install fails the replace test.

## Tests, live hashes after, smoke, discrepancies

### Voice path (Claude condition 4)

Brian's spoken turns reach the client's `prompt.submit`. They are not submitted inside Hermes.

- `VoiceController.cs` L2232 raises `TranscriptReady` for an admitted transcript.
- `MainWindow.xaml.cs` L208 subscribes. `OnTranscriptReady` L627–651 calls `SubmitTurnAsync(text, KindVoice)` when the transcript is not a clarify answer.
- `SubmitTurnAsync` L444–473 calls `ChatSocket.SubmitAsync`.
- `ChatSocket.SubmitAsync` L277–285 sends `prompt.submit` with `session_id` and `text`.
- A clarify-bound transcript (`MainWindow.xaml.cs` L636–647) answers that clarify and does not submit a turn.
- Hermes `tools/voice_mode.py` and `tui_gateway` voice code do not call `_run_prompt_submit`. `tools/voice_live.py` L14 says the renderer turns a delegation into `prompt.submit`.

### Early import (Claude condition 2)

Scratch harness `C:\Users\test\Dev\zola-spikes\p9-fix-arm\early_import_proof.py`, throwaway `HERMES_HOME`, not the live profile.

Importing `tui_gateway.server` once, and importing it twice, produced the same registry: 215 methods, the same key list, `prompt.submit` at `methods_prompt.py` line 544, and the same log set. The second import kept the same function object (`id_stable` true). Both homes contained only a seeded `SOUL.md`. `_ensure_default_soul_md` (`hermes_cli/config.py` L611–621) writes that file only when it is missing or a legacy template; a customized SOUL is left alone, which is the same write the normal lifespan import already performs.

`sys.stdout` is redirected to stderr at import in both orders. A print between the two imports goes to stderr. On the serve path there is no `print()` between `discover_plugins()` (`main.py` L2509) and the lifespan import: skills sync runs before plugin discovery, the discovery-failure line already uses stderr, and the ready sentinel writes fd 1 (`web_server.py` L1267–1270). The install is the early import inside `register()`, and only when argv contains the token `serve`.

`on_session_start` was not used. It fires from `agent/conversation_loop.py` L765–768 while the first turn is already inside `prompt.submit`, so a wrap installed there cannot mint that submit's ticket.

### What the code does

- Ticket only when `_current_rpc_method` is `prompt.submit`, and never when params carry `_hosted_task`, `_hosted_terminal_callback`, or a `DeliveryAuthor`.
- The ticket is minted before the original handler and revoked on an error, a `voice_stopped` reply, a steer/redirect, or a queue whose stored text is no longer the submitted line. `streaming` and an unmerged queue keep it.
- `pre_llm_call` consumes one matching hash onto that `turn_id`. A later check uses the binding. Restart clears it. TTL is 900 seconds.
- Missing wrap refuses `origin_wrap_missing`. No match or an exception refuses closed. The log line is `gate brian_only action=refuse reason=<token>` with no prompt text.
- `send_gate.on_pre_llm_call` writes `_auths` only after `is_brian_turn`.
- `zola_memory`: a non-ticket turn writes no pending row, retrieves no episodes, `forget_memory` returns `refused_reason=origin`, and `forget.pre_tool_call_hook` blocks `forget_memory` and `memory` instead of returning None.
- Guard rows block `state.db` writes, `hermes cron` (including `list`), `cronjob_manage`, and paths under `cron/`. Removing `cronjob` from `platform_toolsets.cli` stays a Phase 5 config edit.

### Known limits (fail closed, or not blocked)

Fail closed, no ticket: slash-command prompts, mid-turn steers and redirects, a merged busy-queue body, and an `@` expansion that changes the text the hook sees.

Not blocked, recorded as residuals: a command that does not name `state.db` (including `python -c "import sqlite3"` and a base64 payload), a copy of the database under another filename, SQL through a tool other than `terminal` / `write_file` / `patch`, and a `prompt.submit` forged on the local socket with the session token. A still-live ticket can be consumed by another turn in that session whose hooked text hashes equal.

### Tests (2026-10-09)

Offline, throwaway `HERMES_HOME` inside the p9 tests. No live profile, no Google, no model call. The real `prompt.submit` handler was not invoked; the harness wraps a fake handler and then calls the real `pre_llm_call` / send-gate / guard functions. Gmail's transport stub was armed for H6 and received no call.

| Suite | Result |
|---|---|
| `zola_workspace` | 171 OK (Phase 8's 155, plus 16 new) |
| `zola_memory` | 113 OK (Phase 8's 112, plus 1 new) |
| `zola_tools` | 44 OK |

Live hashes were not re-taken. This phase did not edit the profile, the mirror, Hermes, or the client.

## Discrepancies

None that blocked the phase. `on_session_start` is not before the first turn; the early-import proof made that fallback unnecessary.

## Phase 4 — Review checkpoint (2026-10-09)

Claude's Phase 3 review applied. No live profile edit, no Hermes edit, no client edit. Stopped here.

### Stale thread origin

`_thread_ok` is cleared at the start of `consume_for_hook`, before any return, and again from `post_llm_call`, `on_session_end`, and `agent_loop_stopped`. A bound `turn_id` is what `origin_allows`, `sync_turn`, and `on_turn_start` use.

The thread flag is the fallback only when no turn_id exists:

| Call site | When the flag is read |
|---|---|
| `forget.client_origin_active` | `current_turn_id()` is empty. The caller is `retrieve.retrieve_episodes`, which has no turn_id argument. During a live turn the context var is set, so this branch is not taken. |
| `forget.origin_allows` | kwargs, `tools.approval_context._approval_turn_id`, and `current_turn_id()` are all empty. Callers are `handle_forget_memory` and `pre_tool_call_hook`. |

`on_turn_start` reads kwargs `turn_id` or the pre_llm context var. `sync_turn` does not read the thread flag or a remembered turn id.

### Paths that can reach memory without `pre_llm_call`

Each fails closed.

| Path | Where | Why it does not pass |
|---|---|---|
| Persist disabled | `agent/turn_context.py` `_collect_pre_llm_call_context` L670–671 returns `""` and does not run hooks. `_memory_turn_start_and_prefetch` L774–782 still calls `on_turn_start` and `prefetch_all` | No new ticket is consumed. After turn end the binding and the thread flag are gone, so forget, retrieve, and the memory tools refuse. |
| Background review | `agent/background_review.py` L944 sets `_persist_disabled`. `_fork_init_kwargs` L879 sets `parent_session_id` and L881 sets `skip_memory=True`. `agent/turn_finalizer.py` L508–512 runs `post_llm_call` before the spawn at L620 | The fork has no zola_memory provider. A parent session id fails `is_brian_conversation`. The parent's origin was cleared before the spawn. |
| Compression | `agent/conversation_compression.py` does not construct an `AIAgent` and does not set `_persist_disabled` | No separate memory turn. |
| Subagents | `tools/delegate_tool.py` L245 sets `parent_session_id` | Not a Brian conversation. A child `pre_llm_call` clears the thread flag before the miss. |
| Interrupt | `post_llm_call` runs only when `final_response and not interrupted` (`turn_finalizer.py` L508). `on_session_end` L627–633 still runs on the turn thread with `turn_id`, unless `_persist_disabled` (L627). `agent_loop_stopped` (`tui_gateway/session_lifecycle.py` L412–417) has no `turn_id` and runs on the gateway thread | `on_session_end` clears the turn thread. `agent_loop_stopped` clears the gateway thread only. A binding neither hook names expires by the 900s prune. |

### Sync after the binding is gone

`post_llm_call` (L509) runs before `_sync_external_memory_for_turn` (L604). The sync worker copies context after the thread flag is cleared. A successful consume records one permit `{turn_id, sha256(user_message), created}`. Turn end removes `_bound` and the thread flag and leaves the permit. `sync_turn` takes one unexpired permit whose hash equals `sha256(user_content)`. Any other text writes nothing, so a synthetic sync cannot spend Brian's permit. Interrupted turns skip sync (`run_agent.py` L888).

`user_content` and the `pre_llm_call` `user_message` match for an ordinary typed turn: both are `persist_user_message` (`agent/turn_context.py` L943), and `_summarize_user_message_for_log` leaves a string unchanged (`codex_responses_adapter.py` L202–208). These cases differ, and a mismatch writes no pending row:

| Case | What happens |
|---|---|
| Skill scaffolding | `MemoryManager.sync_all` strips a message that starts with `[IMPORTANT: The user has invoked the ` (`memory_manager.py` L490, `skill_commands.py` L79–86) before `sync_turn`. The hook hashed the unstripped text. A slash invocation never gets a ticket (`origin._is_slash`). |
| `@` expansion | `prompt_turn.py` L488–503 expands before `run_conversation`, so the hook and the sync string are the same expanded prompt. The ticket is the pre-expansion submit. A change fails at consume and records no permit. |
| Stop phrase | `methods_prompt.py` L553–554 returns `voice_stopped` before a turn. The ticket is revoked. There is no consume and no sync. |
| Mid-turn redirect | `turn_iteration_prep.py` L318–324 appends `User correction during the turn:` onto `original_user_message` after `pre_llm_call`, and `_run_phase` copies that back (`conversation_loop.py` L1378–1385). Sync hashes the longer string. |
| Images | The persisted turn is a content list (`session_history.py` L49–57). The hook consumes only a string, so the list becomes `""` (`turn_context.py` L161) and no permit is recorded. Sync flattens the list and adds an image marker (`codex_responses_adapter.py` L210–214). |

### Tickets, growth, logging

Pending tickets are stored on the session object and compared with `is`. A miss drops expired tickets for that session and leaves the other pending lines. `_bound` and `_logged` prune on insert (900s TTL, cap 256). Turn end removes that turn's `_bound` entry.

One INFO line when the wrap is first installed: `origin wrap installed method=prompt.submit`. One WARNING when `install_for_serve` is in a serve process and does not install: `origin wrap missing method=prompt.submit`. A process that is not `serve` does not warn. A second install does not log again. Neither line carries prompt text.

### Residual (not blocked)

A synthetic turn whose text exactly equals a queued Brian ticket can consume it if it wins the idle race.

### Tests (2026-10-09)

| Suite | Result |
|---|---|
| `zola_workspace` | 177 OK (Phase 3's 171, plus 6) |
| `zola_memory` | 117 OK (Phase 3's 113, plus 4) |
| `zola_tools` | 44 OK |

The new memory test grants a Brian turn, then on the same thread with no new `pre_llm_call` refuses `forget_memory`, the pre-tool hook, and episode retrieve. The Brian sync permit still writes one pending row after turn end; the follow-up sync does not. A synthetic sync that runs first writes nothing, and Brian's queued sync still writes his row once. Two Brian turns each write once. One permit cannot be used twice. The new workspace test queues Brian's line, runs a non-matching synthetic turn, and consumes the queued line on his turn.

## Phase 5 — Deploy (2026-10-09)

The running client was stopped so the new plugins load: `dotnet` 3216, `Zola.Client` 23372, serve python 12960 and 26284. Blender MCP processes were left running.

Backups of the seven replaced plugin files and `config.yaml` are in `C:\Users\test\Dev\zola-spikes\p9-fix-arm\plugin-backup\`. `origin.py` was new, so there was nothing to back up. `token.dpapi` was not copied. It is still size 926, mtime `2026-10-07T22:58:24.2521851Z`. `SOUL.md` is still `38577550B251AFC6AA21432BA1DF12DF70A6F56378ADD6DC2E30211358C9C5E2`. `hermes-agent` porcelain is empty.

Backup hashes match the Phase 1 live rows for the four workspace files that baseline listed (`__init__.py`, `guards.py`, `send_gate.py`, `turn_context.py`). `config.yaml` backup is `6ED53ACE35C223ED1B9D5AF1696A6C449626C57B37B38F099F2DCC5B6F4B8E76`.

### Mirror

Repo file and live mirror SHA-256 match for each copied file. Tests and `__pycache__` were not copied.

| File | SHA-256 |
|---|---|
| `plugins/zola_workspace/__init__.py` | `90081583CB0570EDCA2BF7D7076597C13DE81669EE494723B19D668154D9B2E1` |
| `plugins/zola_workspace/guards.py` | `0334AE0CADE57FB06DBDF9ABD98D0C248D53BFAD415A58F60D4209E5AD69089D` |
| `plugins/zola_workspace/send_gate.py` | `2E601E2358AF51C0C17B867E1C74B128868F534D310359702D484D9B36CB9696` |
| `plugins/zola_workspace/turn_context.py` | `84B0E58E58EE0A6913F1A9A150115E8C291FF4D339B8BF1EA973BD65ACC1AFAF` |
| `plugins/zola_workspace/origin.py` | `4581898A844C75BD30C8778A3B3611429D0381D3834E4EFCEC449BCF0D7F4DB1` |
| `plugins/zola_memory/forget.py` | `D0717731AEAA7D45C0A38535503CAF488AB53C7D9E317B5E24E193CB6E40E891` |
| `plugins/zola_memory/provider.py` | `12AA675E8B693BADA15160FB251F128ADF7C144F2A6A3C75212F82DD3FA9AC83` |
| `plugins/zola_memory/retrieve.py` | `84E0C44975579C0B6878E64355ADAB4D30B09EE9938E61E9855A6774CC11FA39` |

### Config

`platform_toolsets.cli` lost the `cronjob` entry. Nothing else in the file changed.

Before `6ED53ACE35C223ED1B9D5AF1696A6C449626C57B37B38F099F2DCC5B6F4B8E76`. After `1C37F2A03043D1BA9EF4E9A22D2268B2B52763BACDD8A7939F29F95F79B563F6`.

```
     - connections
-    - cronjob
     - delegation
```

`known_plugin_toolsets.cron` is unchanged.

### Armed state

`state_meta` counts: `heartbeat:` 0, `loop:` 0, `goal:` 0. `cron/jobs.json` is absent.

### Offline harness

Throwaway `HERMES_HOME` inside `test_p9_fix_arm.py`. No Google call. No model call. The real `prompt.submit` handler was not invoked. The harness wraps a fake handler, then calls the real `pre_llm_call` and send-gate functions. `HarnessTests`: 6 OK.

| Probe | Result | Reason |
|---|---|---|
| H1 client turn | passes | ticket consumed onto that `turn_id` |
| H2 heartbeat text, no ticket | refused | `origin_unknown` |
| H3 `/loop` text, no ticket | refused | `origin_unknown` |
| H4 follow-up after H1, same session | refused | `origin_unknown` (the ticket was already consumed) |
| H5 unknown origin | refused | `origin_unknown` |
| H6 text `Approved. Send it.` with a reviewed draft staged | no send authorization | the Gmail stub was not called |

The live heartbeat and `/loop` pollers do not run in this harness. A turn they would start has no `prompt.submit` ticket, so it takes the same `origin_unknown` path as H2 and H3.

### Client

Relaunched with `C:\Program Files\dotnet\dotnet.exe` run on `windows-client\Zola.Client\Zola.Client.csproj`. `Zola.Client` pid 28104. Serve python pids 33972 and 5996 (`hermes_cli.main -p zola serve --isolated`). `agent.log`: `2026-10-09 14:45:22,339 INFO zola_workspace: origin wrap installed method=prompt.submit`. No `origin wrap missing` line.

Scripted lines:

- S1 (voice): "What's on my calendar tomorrow?"
- S2 (typed): "Search my email for anything from Google this week."
- S3 (typed): "Remember that my test word is lantern." then "Forget my test word."
- S4 (typed): "Use the terminal to run: python -c \"import sqlite3\""
- S5 (typed): "Use the terminal to run: hermes cron list"

### Smoke (Brian: smoke test passed)

Session `20261009_144523_f55854`. No `gate brian_only action=refuse` line. No `origin wrap missing` line.

| Step | Log |
|---|---|
| S1 | `zola_workspace.calendar_query state=complete count=1 more=false range_start=2026-10-10T00:00:00-07:00 range_end=2026-10-11T00:00:00-07:00`. Memory pending write, turn index 1. |
| S2 | `zola_workspace.gmail_search state=complete count=8 more=false ms=1905`. Memory pending write, turn index 2. |
| S3 | One typed turn, 66 characters, containing both sentences. `fact_add` then `forget_guard action=allowed tool=memory` and `fact_erase`. Disposition `drop`, so that turn wrote no pending row. |
| S4 | No `state_db_write` or `schedule_write` line. The terminal tool returned `BLOCKED: Command denied by user` (the existing approval prompt). |
| S5 | `zola_workspace.guard name=schedule_write action=block reason=schedule_write tool=terminal`. The terminal tool returned in 0.01s. |

After the smoke, `state_meta` is still `heartbeat:` 0, `loop:` 0, `goal:` 0, and `cron/jobs.json` is still absent.

A background skill-review turn started after S3 and was interrupted when S4 arrived. `skill_manage` was blocked by the existing taint guard: `zola_workspace.guard name=memory_taint action=block reason=skill_manage_taint tool=skill_manage`.

## Phase 6 — Closeout (2026-10-09)

Suites re-run: `zola_workspace` 177 OK, `zola_memory` 117 OK, `zola_tools` 44 OK. The eight mirrored plugin files still match the repo. Live `config.yaml` is `1C37F2A03043D1BA9EF4E9A22D2268B2B52763BACDD8A7939F29F95F79B563F6`. `SOUL.md` is `38577550B251AFC6AA21432BA1DF12DF70A6F56378ADD6DC2E30211358C9C5E2`. `hermes-agent` is `345cd2b057a452236de401d3534b8502a7465e8d`, porcelain empty. Scratch `C:\Users\test\Dev\zola-spikes\p9-fix-arm\` is deleted. No client files changed.

Approved option, Brian, verbatim (2026-10-09): "Option 1 via a runtime wrap of prompt.submit, no Hermes edit. Crash replay gets no Brian authority. Add the guard rows and drop the cronjob toolset as defense in depth. Bring zola_memory into scope."

### Exit criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Synthetic turns fail; origin meets G-ORIGIN and G-ORIGIN-LIFECYCLE (a)–(e) | ✅ | H2–H5 refuse `origin_unknown`. A ticket is minted only inside the `prompt.submit` wrapper, before the handler, and consumed onto one `turn_id` in `pre_llm_call` before send authorization. Turn end clears the thread flag and that binding. Crash replay is not a client `prompt.submit`, so it gets no ticket. Concurrent sessions and restart are tested. Process memory does not survive a serve restart. |
| 1a | No synthetic or replayed send authorization | ✅ | H6 and the replay test write no `_auths`. The Gmail stub is not called. |
| 2 | Brian's client turns pass | ✅ | Live S1–S3. No `gate brian_only` refuse. Calendar query, Gmail search, and forget all ran. |
| 3 | Unknown origin and exceptions fail closed | ✅ | `origin_unknown`, `origin_wrap_missing`, and `origin_check_error` tests. |
| 4 | Guard rows block their patterns; residuals recorded | ✅ | Unit tests. Live S5: `zola_workspace.guard name=schedule_write action=block reason=schedule_write tool=terminal`. S4 had no new guard line. |
| 5 | Approved config edit, hashes recorded | ✅ | `platform_toolsets.cli` lost only `cronjob`. Before `6ED53ACE35C223ED1B9D5AF1696A6C449626C57B37B38F099F2DCC5B6F4B8E76`. After `1C37F2A03043D1BA9EF4E9A22D2268B2B52763BACDD8A7939F29F95F79B563F6`. |
| 6 | No Hermes change, no client change, no identity or build-plan edit | ✅ | `hermes-agent` porcelain empty. No `windows-client` diff. `SOUL.md` unchanged. |
| 7 | Nothing armed after the smoke | ✅ | `heartbeat:` 0, `loop:` 0, `goal:` 0. `cron/jobs.json` absent. |

### Residuals (not blocked)

- A command that does not name `state.db`, including `python -c "import sqlite3"` and a base64 payload.
- A copy of the database under another filename.
- SQL through a tool other than `terminal`, `write_file`, or `patch`.
- A `prompt.submit` forged on the local socket with the session token.
- A synthetic turn whose text exactly equals a queued Brian ticket, if it wins the idle race.

Fail closed, no ticket or no pending row: slash prompts, mid-turn steers and redirects, a merged busy-queue body, an `@` expansion that changes the hooked text, skill-prefix text whose sync string was stripped, and an image turn whose persist payload is a list.

Implementation commit: `f348c2db25d908fad7ee95182a659840144efe59`


