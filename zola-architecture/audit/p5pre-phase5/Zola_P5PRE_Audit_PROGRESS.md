# P5PRE Audit — Progress

**Audit ID:** P5PRE
**Prompt version:** 1.1 (2026-10-01)
**Scope:** S41, S42, S36, S38 (SOP Stage 1). Diagnostic only.

## Repositories

| Repo | Path | Branch | HEAD | Clean |
|---|---|---|---|---|
| zola-windows (audited) | `C:\Users\test\Dev\zola-windows` | `p5pre-audit` | `6494acace5c124368bf9ce284d2d3d5ddcd22aac` | yes at branch creation (no porcelain) |
| hermes-agent (read-only) | `C:\Users\test\Dev\hermes-agent` | detached `v2026.9.14` | `345cd2b057a452236de401d3534b8502a7465e8d` | yes (`git status --porcelain` empty) |

Remote: `https://github.com/beebodev/Zola-Windows`. Base branch `main` at the same SHA.

## Folders

| Role | Path |
|---|---|
| Output | `zola-architecture/audit/p5pre-phase5/` |
| Scratch (never committed) | `C:\Users\test\Dev\zola-spikes\p5pre\` |
| Live profile (read-only) | `%LOCALAPPDATA%\hermes\profiles\zola\` |
| Client logs (read-only) | `%LOCALAPPDATA%\ZolaClient\logs\` |

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Setup | COMPLETE |
| 2 | S41 clarify wake/mic static trace | COMPLETE |
| 3 | S42 cross-session memory | COMPLETE |
| 4 | S36 barge-in feasibility | COMPLETE |
| 5 | S38 listen-to-think map | COMPLETE |
| 6 | Live probes | COMPLETE |
| 7 | Synthesis | COMPLETE |
| 8 | Closeout | COMPLETE |

Findings at closeout: 19 — 4 HIGH, 3 MEDIUM, 2 LOW, 10 MATCH.

Audit commit: `5629bc2ba04bbfe7a12489946623249b243fba62`

Merge SHA: `c5be52e47ef8686d3643f5c57cf262cfd3991b8b`

## Guardrails

- **G-SCOPE:** Read-only diagnostic. Findings only under `zola-architecture/audit/p5pre-phase5/`.
- **G-NOCHANGE:** No source, lore, hermes-agent, or live-profile edits. Phase 6 probe memory is written and removed only through Zola.
- **G-ARCH:** Lore and architecture are truth. Conflicts are findings. Locked decisions (C4, S14, P4, P2-D01) are not treated as revised.
- **G-QUALITY:** Every finding names a file, method or class, and a line range.
- **G-HYPOTHESIS:** LEADs are confirmed or refuted with evidence. They are not copied in as findings.
- **G-PRIVACY:** Counts, tags, hashes, session IDs, and Phase 6 probe text only. Other memory and conversation text redacted.
- **G-LIVE:** One developer step at a time. Wait for Brian before the next step.
- **G-CLOSEOUT:** Does not begin without "proceed to closeout".
- **G-NO-CROSS-SCOPE:** Android Zola is not opened. Android memory designs are not scored as missing.

## Prep hashes

Dictation tool confirmed off (2026-10-01). Build: `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` succeeded, 0 warnings, 0 errors. Scratch copies of `MEMORY.md` and `USER.md` match these hashes.

| File | Bytes | SHA-256 |
|---|---|---|
| `memories/MEMORY.md` | 236 | `8264268512E5CC7A37FFF847F523CA142C310DBF21BEF30C2AD601EE3A5986EB` |
| `memories/USER.md` | 1983 | `881E6D34683E77B078E84BE856D9BC91F689BEFAEC39E5630869ECB22A9F8BE7` |
| `config.yaml` | 3117 | `26CC6A6F811589B6B0963D598DC95BB6153C5AD60FB8072B10B7BAC601A0605E` |
| `SOUL.md` | 4124 | `CA2CD346EADAB3D6972FE36D16EF129E186C3B66B538F05EAD20BAA9EC4014A5` |

Log offsets taken after the previous client stopped and before this launch. Probe excerpts start at these byte offsets.

| Log | Offset |
|---|---|
| `voice-timeline.log` | 385006 |
| `display-state.log` | 627071 |
| `server-requests.log` | 23018 |
| `presence.log` | 31045774 |

Launch: win-x64 `Zola.Client.exe` pid 15960 at 2026-10-01T17:17:44-07:00. HUD reached Idle, mic listening for "Hey Zola", local link connected. The already-running `hermes serve` (python pids 15568 and 5024, started 12:29) was left up; this window attached and does not own it. A later full restart (L2 C1) has to stop that serve, because closing the window will not.

## Running findings

| ID | Severity | Label | File | Summary |
|---|---|---|---|---|
| P5PRE-AUD-01 | HIGH | [RISK] | `VoiceController.cs` `OnVoiceTranscript` / `OnVoiceStatus` | A spoken clarify answer sets `_followUpTranscriptSeen` and does not start a turn, so the later reply follow-up's silence never calls `CancelFollowUp`. `Resting` stays false and `wake.resume` is never requested. |
| P5PRE-AUD-02 | MEDIUM | [GAP] | `VoiceController.cs` `ReconcileWakeRestingAsync` | Several reconcile exits write nothing, and no line snapshots the `Resting` flags. A stuck pause looks like "no `wake.resume`" with no error. |
| P5PRE-AUD-03 | — | [MATCH] | `MainWindow.OnTranscriptReady` | A bound clarify transcript answers that request and does not call `prompt.submit` (`P4-D14`). |
| P5PRE-AUD-04 | — | [MATCH] | `VoiceController.ReconcileWakeRestingAsync` | Pause and resume of wake have one owner. Text→Voice recovers by disarming and `ArmWakeAsync`, not by a second resume path (`P2-D12`). |
| P5PRE-AUD-05 | — | [MATCH] | `tools/memory_tool.py` `get_memory_dir`; live `config.yaml` | The live store is the profile's `MEMORY.md` / `USER.md`. Limits 4400 / 2750. `memory.provider` is unset (C4). |
| P5PRE-AUD-06 | — | [MATCH] | live `memories/` | Both files are under the limit. A new `add` would succeed. No `.bak` drift snapshots. |
| P5PRE-AUD-07 | HIGH | [RISK] | `tools/memory_tool.py` `MEMORY_SCHEMA` | A durable write happens only when an agent calls the `memory` tool. The tool text says to save almost nothing. 2 result rows across 93 sessions. |
| P5PRE-AUD-08 | LOW | [RISK] | `tools/memory_tool_store.py` `format_for_system_prompt` | The system-prompt block is frozen at `load_from_disk()`. Writes update disk and the live lists, and leave the snapshot unchanged. |
| P5PRE-AUD-09 | — | [MATCH] | `tui_gateway/server.py` `_make_agent` | A new client session builds a new `AIAgent` on its first prompt and calls `load_from_disk()` again. A fact already on disk is in that snapshot. |
| P5PRE-AUD-10 | — | [MATCH] | `tools/session_search_tool.py` | `session_search` searches `messages_fts`. It has been called. It is not the `MEMORY.md` injection path. |
| P5PRE-AUD-11 | — | [MATCH] | `plugins/memory/__init__.py` | A user provider loads from `$HERMES_HOME/plugins/<name>/` without editing hermes-agent. The zola profile has no plugins directory. |
| P5PRE-AUD-12 | LOW | [GAP] | live `SOUL.md`; `memories/*.md` | The `[tag]` convention is not in the live `SOUL.md`. None of the 13 entries starts with a `[tag]`. |
| P5PRE-AUD-13 | — | [MATCH] | `tui_gateway/methods_voice.py` `_arm_barge_listener_if_enabled` | Live `barge_in: false` means the process-global full-duplex listener is not armed. |
| P5PRE-AUD-14 | HIGH | [RISK] | `tui_gateway/methods_voice.py` `_fd_trip` | The barge trip is not clarify-aware. It always cuts TTS and emits `voice.interrupted`. Re-enabling barge-in as-is fails S36 (b). |
| P5PRE-AUD-15 | HIGH | [GAP] | `tui_gateway/methods_voice.py` `voice.record` | The answer capture has no pre-roll. The 1200 ms buffer is only on the barge listener and on uncalled `listen_for_speech`. S36 (e) fails on this pin. |
| P5PRE-AUD-16 | MEDIUM | [GAP] | `plugins/` (no voice hook) | No profile plugin or config key can make the listener clarify-aware or add pre-roll to `voice.record`. |
| P5PRE-AUD-17 | MEDIUM | [GAP] | `VoiceController.cs` timeline; `ZolaDisplayState.cs` | Client logs time transcript delivery and the Thinking label. They do not split silence, WAV, Whisper load, inference, `prompt.submit`, or `message.start`. |
| P5PRE-AUD-18 | — | [MATCH] | `hermes_cli/voice.py` `_continuous_on_silence` | Listen-to-think is one path: VAD silence, WAV, Whisper, `voice.transcript`, `prompt.submit`, `message.start`, Thinking label. |
| P5PRE-AUD-19 | — | [MATCH] | `tools/transcription_tools.py`; live `stt` | Local faster-whisper, model `base`, device and compute type `auto` (not pinned). Idle unload is off. |
