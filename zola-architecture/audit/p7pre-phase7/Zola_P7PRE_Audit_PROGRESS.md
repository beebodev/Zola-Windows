# Zola P7PRE Audit — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\P7PRE_Audit_Prompt_v1.1.md`  
**Prompt SHA-256:** `38A01D7CC707DA495FB823BA3C72CB147397A9A807E49A13111164E579C2C39F`  
**Started:** 2026-10-05  
**Auditor:** Cursor agent (diagnostic only)

---

## Repositories

| Repo | Branch | HEAD | Clean |
|---|---|---|---|
| `zola-windows` | `p7pre-audit` (from `main`) | `7d77cb51c3866c50862d09f6d026191fbe25540a` | audit docs under `zola-architecture/audit/p7pre-phase7/` only |
| `hermes-agent` | detached / tag `v2026.9.14` | `345cd2b057a452236de401d3534b8502a7465e8d` | yes |

`git describe` (hermes-agent): `v2026.9.14`

---

## Folders

| Role | Path |
|---|---|
| Output | `C:\Users\test\Dev\zola-windows\zola-architecture\audit\p7pre-phase7\` |
| Scratch | `C:\Users\test\Dev\zola-spikes\p7pre\` |
| Live profile | `%LOCALAPPDATA%\hermes\profiles\zola\` |
| Client logs | `%LOCALAPPDATA%\ZolaClient\logs\` |

---

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 1 Setup | COMPLETE | branch, hashes, effective config, processes, logs |
| 2 S45 EchoPaths | COMPLETE | `Zola_P7PRE_Audit_01_EchoPaths.md` |
| 3 S45 EchoEvidence | COMPLETE | `Zola_P7PRE_Audit_02_EchoEvidence.md` |
| 4 S44 ClarifyVoice | COMPLETE | `Zola_P7PRE_Audit_03_ClarifyVoice.md` |
| 5 S38 Latency | COMPLETE | `Zola_P7PRE_Audit_04_Latency.md` (+ L-2 / AUD-25 / AUD-26) |
| 6 S34/S37 ChunkingEstimate | COMPLETE | `Zola_P7PRE_Audit_05_ChunkingEstimate.md` |
| 7 Harness probes | COMPLETE | H-2 + H-1 on L1-1…L1-6 |
| 8 Live probes | COMPLETE | L-1…L-4 done; see Audit_07 |
| 9 Synthesis | COMPLETE | `Zola_P7PRE_Audit_SYNTHESIS.md` |
| 10 Closeout | COMPLETE | 10a–10i; final findings **26** (4 HIGH, 11 MEDIUM, 3 LOW, 8 MATCH) |

---

## Guardrails (summary)

- **G-SCOPE / G-NOCHANGE:** diagnostic writes only under `audit/p7pre-phase7/` (+ scratch). No client, plugin, hermes-agent, live-profile, or lore edits.
- **G-NO-INSTALL:** no pip/npm/model downloads. ffmpeg missing → H-1 deferred.
- **G-SCRATCH:** probe code/audio only in `zola-spikes\p7pre\`; delete at closeout.
- **G-ARCH:** locked decisions stand (`P2-D05`, `P2-D12`, `P2-D14` included).
- **G-QUALITY:** file / class / method / line range; Hermes at pin `345cd2b0`; client at `7d77cb51`.
- **G-PRIVACY:** counts/lengths/hashes/IDs/timestamps only in repo docs.
- **G-LIVE:** Brian steps one at a time; confirm P2-D16 before first live step.
- **G-CLOSEOUT:** not until developer says proceed.
- **G-NO-CROSS-SCOPE:** no Android Zola.

---

## Live-profile hashes (Phase 1)

| File | SHA-256 |
|---|---|
| `config.yaml` | `7BA2E676A04FF92047C8D711FCB022BE8A532B11BAAC6F74B08986744E704570` |
| `SOUL.md` | `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49` |
| `memories/MEMORY.md` | `14DC5F8EBFBDF89A2BCDDA5DF2AFABE57571238C52DBD9644EFA36117E14778D` |
| `memories/USER.md` | `47A732A0B218936C9B465F6BB8ADA34BCDA4FE027660F000E9B139B4E7022D12` |
| `plugins/zola_memory/consolidate.py` | `1B2D8D8AD8140EC515D184279DD3BD541952918025ADEDF47761944AE14941C2` |
| `plugins/zola_memory/fact_index.py` | `AA0CCE9E599BA94F933A8619E2094D3A21192BD4AA785510A9D28FBC53D81B02` |
| `plugins/zola_memory/forget.py` | `A9B62AA822DBAD0A350FE84CB004C4E63124F4FBEA98F591D4454EDDCC1BB306` |
| `plugins/zola_memory/llm_access.py` | `EC5A8F319628CB24DEEB0177397D34B754A51B30F80C025D4F93D5E5189FEC57` |
| `plugins/zola_memory/log.py` | `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` |
| `plugins/zola_memory/pending.py` | `9FF6156CD946C08BFD737EDFFC15C6DAE2D865AB0C34ED332F48056DDA854769` |
| `plugins/zola_memory/provider.py` | `E292093763665B0A35E38C67166F84E372493D4F4016704F006217A15E76A18A` |
| `plugins/zola_memory/registry.py` | `86AA4DA04D67AB911D569AB1D9774A86E1A36F75F9B1931D49CA3F0272EE771D` |
| `plugins/zola_memory/retrieve.py` | `53D8044D896F6F769AA10EF99BAB67083ADF19AA3E01858A067A870916C0290D` |
| `plugins/zola_memory/store.py` | `C471EA121F993BD00D5E68EEF0DEFB92FBDD3D606774CA78B89ADF1B34CB00E8` |
| `plugins/zola_memory/time_context.py` | `C3B61942358CCCEC6DB422B31B7200C8D743C095779B144DB9B174BF105BBF9F` |
| `plugins/zola_memory/__init__.py` | `7FAA42BC030B329EB5F078B80EC45183104105361A29E880EAC3CCCCF9994C11` |
| `plugins/zola_tools/calculator.py` | `0F29F3FC1E1D5EAC3D1E4CEF0BCF6428EF6497EE2AF61BD86503602BE80FE680` |
| `plugins/zola_tools/plugin.yaml` | `F329E9065493F766712A018DF14541172282666EF516AD3D45781B56AE1D2216` |
| `plugins/zola_tools/__init__.py` | `A1EF8541406F1A9C199CC8C8CE1BB7C71E087F4C3EAA2151DAC7B59F04C33513` |

### Row counts (Phase 1)

**state.db:** sessions=123, messages=2286  

**zola_memory.db (core):** entities=0, episodes=0, episode_fact_refs=0, facts=16, pending_turns=0, tombstones=30, meta=9

### Effective config (profile + defaults A10)

| Key | Effective | Source |
|---|---|---|
| `agent.clarify_timeout` | `300` | profile |
| `stt.provider` | `local` | profile |
| `stt.language` | `en` | default |
| `stt.local.model` | `base` | profile |
| `stt.local.language` | `""` (auto; falls through) | default |
| `stt.local.device` / `compute_type` | `auto` (optional YAML; not in defaults table) | code default |
| `beam_size` | `5` hardcoded | not a config key |
| `tts.provider` / voice / speed | edge / `en-GB-SoniaNeural` / `0.95` | profile |
| `voice.silence_duration` | `1.5` | profile |
| `voice.silence_threshold` | `200` | default |
| `voice.barge_in` | `false` | profile |
| `voice.stop_phrases` | `["stop"]` | profile |
| `display.busy_input_mode` | `interrupt` | default |
| `display.interim_assistant_messages` | `true` | default |
| `wake_word.*` | enabled sherpa "hey zola" local … | profile |
| `security.allow_lazy_installs` | `false` | profile |

---

## Processes (Phase 1 snapshot)

| PID | Role | Start | Notes |
|---|---|---|---|
| 25164 | `Zola.Client.exe` | 2026-10-05 13:02:52 | parent of serve |
| 24684 | `hermes serve` (venv) | 2026-10-05 13:02:53 | child of client |
| 18868 | `hermes serve` (uv python) | 2026-10-05 13:02:53 | child of 24684 |

**Stale multi-serve:** no — single serve tree.

---

## Log files (Phase 1)

| File | Size | Range |
|---|---|---|
| `voice-timeline.log` | 776151 | 2026-09-23 → 2026-10-05 |
| `display-state.log` | 876355 | 2026-09-24 → 2026-10-05 |
| `presence.log` | ~44M | active |
| `server-requests.log` | 31200 | 2026-09-29 → 2026-10-02 |
| `agent.log` | 4194185 | 2026-09-22 → 2026-10-05 |

**P5PRE-AUD-17:** `Silence detected` / `WAV written` land in `logs/agent.log`.

---

## LEAD status

| LEAD | Status | Finding ID |
|---|---|---|
| LEAD-1 (mid-turn CancelFollowUp) | **Confirmed** | P7PRE-AUD-02, P7PRE-AUD-09 |
| LEAD-2 (busy-submit / redirect) | **Confirmed** | P7PRE-AUD-05 |
| LEAD-3 (end-anchored guard) | **Confirmed** | P7PRE-AUD-03 (+ H-2) |
| LEAD-4 (haystack ≠ spoken) | **Confirmed** | P7PRE-AUD-04 |
| LEAD-5 (clarify × echo) | **Partly** | P7PRE-AUD-12 (guard runs on bound clarify; unbound/short miss) |
| LEAD-6 (STT config levers) | **Partly** | P7PRE-AUD-17 (device/lang yes; beam_size no) |
| LEAD-7 (monitor-dominated releases) | **Confirmed** | P7PRE-AUD-21 (196/205 monitor) |

---

## Findings (running)

| ID | Label | Severity | File | Summary |
|---|---|---|---|---|
| P7PRE-AUD-01 | [MATCH] | — | methods_voice.py / voice.py | RPC `voice.record` stop always force-transcribes |
| P7PRE-AUD-02 | [RISK] | HIGH | VoiceController.cs L2128–2157 | CancelFollowUp does not stop Hermes; typed-submit orphans capture (LEAD-1) |
| P7PRE-AUD-03 | [RISK] | HIGH | VoiceController.cs L2614–2642 | Echo guard end-anchored; head/middle drop rate ~0 (LEAD-3) |
| P7PRE-AUD-04 | [RISK] | MEDIUM | VoiceController.cs L2595–2612 | Haystack = streamed reply text, not Edge-spoken (LEAD-4) |
| P7PRE-AUD-05 | [MATCH] | — | turn_iteration_prep.py L318–325 | Busy interrupt → `User correction during the turn:` (LEAD-2) |
| P7PRE-AUD-06 | [MATCH] | — | ChatSocket.cs L735–737 | `message.interim` dropped; not in haystack |
| P7PRE-AUD-07 | [RISK] | MEDIUM | zola_memory forget/provider | Echo can enter pending/facts when disposition keep; forget fail-closed for marked keys |
| P7PRE-AUD-08 | [GAP] | HIGH | VoiceController / MainWindow | No single provenance authority for "this is Brian" |
| P7PRE-AUD-09 | [RISK] | HIGH | voice-timeline + state.db | E1/E2 incidents take LEAD-1 path (confirmed) |
| P7PRE-AUD-10 | [MATCH] | — | state.db / VT | History reports candidates; confirmed only with timeline |
| P7PRE-AUD-11 | [GAP] | LOW | zola_memory.db | No pending/episodes at audit; fact contamination unproven without text |
| P7PRE-AUD-12 | [RISK] | MEDIUM | MainWindow L585–593; VC clarify | LEAD-5 partly; unbound clarify routing + short miss |
| P7PRE-AUD-13 | [GAP] | MEDIUM | MainWindow L1557–1559 | No-card Voice breaks batch voice answers |
| P7PRE-AUD-14 | [GAP] | MEDIUM | VoiceController L656–667 | Choices never spoken |
| P7PRE-AUD-15 | [MATCH] | — | MainWindow clarify/approvals | Text keeps card; approvals never voice |
| P7PRE-AUD-16 | [GAP] | MEDIUM | logs | 62% of EoS→audio under-instrumented (TTFT/TTS) |
| P7PRE-AUD-17 | [GAP] | MEDIUM | transcription_local.py L170 | beam_size/cpu_threads not config keys (LEAD-6) |
| P7PRE-AUD-18 | [GAP] | LOW | voice_mode VAD | Cannot judge shorter silence from logs alone |
| P7PRE-AUD-19 | [GAP] | LOW | methods_prompt voice-live | Voice-only note needs client surface or Hermes edit |
| P7PRE-AUD-20 | [RISK] | MEDIUM | VoiceController release | Rare estimate paths can open capture while speaking |
| P7PRE-AUD-21 | [MATCH] | — | voice-timeline | Monitor 95.6% of releases (LEAD-7); S37 small |
| P7PRE-AUD-22 | [MATCH] | — | H-1 harness | L-1 corpus: warm STT ~0.75s med; beam1 no win; lang already en |
| P7PRE-AUD-23 | [RISK] | MEDIUM | VoiceController transcript window | L-3 stale capture_start/stop on echo line |
| P7PRE-AUD-24 | [MATCH] | — | L-4 live | Clarify voice path works end-to-end |
| P7PRE-AUD-25 | [RISK] | MEDIUM | L-2.1 / L-2.2 agent.log | Simple Qs → `skill_view`/`terminal` (+ approval); not `calculate` |
| P7PRE-AUD-26 | [GAP] | MEDIUM | agent.log / H-1 | Live warm WAV→Transcribed ≫ H-1 warm infer; UNEXPLAINED |

**Counts:** 26 findings — **4 HIGH**, **11 MEDIUM**, **3 LOW**, **8 MATCH**

**Deviation:** L-2 ran in existing serve session `20261005_130256_aef4be` (not a new session).
---

## Live-profile hashes (pre-synthesis)

**Result:** `config.yaml`, `SOUL.md`, and all `plugins/**` **match Phase 1** (not BLOCKED).  
`MEMORY.md` / `USER.md` **unchanged**.  

| Store | Phase 1 | Pre-synthesis | Post-quiet consolidate (doc revision) | Δ vs Phase 1 |
|---|---:|---:|---:|---:|
| pending_turns | 0 | 7 | **0** | 0 |
| episodes | 0 | 0 | **0** | 0 |
| facts | 16 | 16 | 16 | 0 |
| episode_fact_refs | 0 | 0 | 0 | 0 |
| tombstones | 30 | 30 | 30 | 0 |

L-2 pendings (`b538748c…`, `3e1ef784…`, `35421edf…`): `19:03:14` `quiet turns=3 episodes=0 ok=true` — consolidated into nothing.  
L-3/L-4 seven IDs: `19:46:03` `quiet turns=7 episodes=0 ok=true` — same drain; store `pending_turns=0`, `episodes=0`.

---

## Closeout SHAs

| Label | SHA |
|---|---|
| Audit content SHA (10c) | `044fe10a857edc364b0fa69cd2f72be5f45067d8` |
| Merge SHA (`--no-ff` merge commit, not final main HEAD) | `3e87e7c47ed2eee4a26f53dc9c4bba7d6f16b1ee` |
| Final main HEAD (after metadata commit) | this commit (`audit: record P7PRE merge SHA`) |

The merge SHA above is the `--no-ff` merge commit that brought `p7pre-audit` into `main`. It is **not** the final `main` HEAD after the closeout metadata commit.

---

## LIVE-PROBE-CONTAMINATION

**Session:** `20261005_192949_1f4302` (L-3/L-4). **No auditor cleanup.** Rows later drained by consolidator (`episodes=0`).

| ID | Kind | Notes |
|---|---|---|
| `d518805a-de66-4666-b132-6a7f283e33e6` | pending_turns | turn 1 — drained 19:46:03 |
| `f5255068-5a04-4e2c-8e1e-19ad053281b0` | pending_turns | turn 2 typed — drained 19:46:03 |
| `b679670c-d203-4042-a295-39db9f18ad8d` | pending_turns | turn 3 echo (whole-turn) — drained 19:46:03 |
| `07299cfa-d89a-47c2-8a62-1eac3286e703` | pending_turns | turn 4 — drained 19:46:03 |
| `09fb5434-c1de-4f83-a914-051725993304` | pending_turns | turn 5 typed — drained 19:46:03 |
| `4ecf0f19-8a53-4a47-a4a9-bd23a7321a26` | pending_turns | turn 6 echo (whole-turn) — drained 19:46:03 |
| `5b2aff76-57d6-4fe6-9959-82fc4d153b11` | pending_turns | L-4 paint/clarify turn — drained 19:46:03 |

Pre-L3: pending=0, episodes=0, facts=16, refs=0, tombs=30.  
Post–L-4 (pre-synthesis): pending=**7**, episodes=0, facts=16.  
After quiet consolidate: pending=**0**, episodes=**0**, facts=16.  
No `"User correction during the turn"` rows in L-3 session `state.db`. Mid-turn redirect not live-reproduced.
