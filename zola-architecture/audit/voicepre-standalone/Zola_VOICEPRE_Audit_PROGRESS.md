# VOICEPRE Audit Progress

Standalone voice feasibility audit. Version 1.2 of the prompt, 2026-10-18. Diagnostic only. Closeout approved with "proceed to closeout".

## Branch and base

| | |
|---|---|
| Output branch | `voicepre-audit` |
| Output path | `C:\Users\test\Dev\zola-windows-voicepre-audit` |
| Base | local `main` `03a3a1fac02a7b6c18b745e6ac3be43b2cd3b090` (no fetch) |
| Primary checkout | left on `p9-speak` at the same commit, dirty P9 overlay |
| Hermes | clean detached `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`) |
| Android | left on `zola-main` `a139ccacab596f12b95e2dd3eda14352bcb97836` |
| Audit directory | `zola-architecture/audit/voicepre-standalone/` |

## Source scopes

Committed worktree versus primary overlay. Hashes rechecked in Audit 08; unchanged from Audit 01.

Overlay prefixes: VoiceController `0136876FF16DE9A6`, ChatSocket `B339E54B56FBE130`, MainWindow `E63317A2CF55A400`, CaptureLifecycle `D8B95D69E6E9DC0E` (matches committed), TranscriptAdmission `BCCE33FA242E496E` (matches), ClarifySpeech `5F6D6760F2052B4A` (matches), TtsPlaybackMonitor `763178A261879FB3`, SpeechEchoGuard `8176EC4E5EEEF4BF`, ProactiveDeliveryCoordinator `210FFF3AC901257C`, ProactiveSpeechSession `2D94F6F23C2CDA30`, speech.py `D4414DD9E59FB857`, P9-SPEAK progress `BFB7E79C2936ED91`, VOICE_CONFIG `0CACE932C857B57F` (matches committed).

The audit worktree does not contain uncommitted P9 speech code.

## Guardrails

G-SCOPE, G-NOCHANGE, G-ARCH, G-QUALITY, G-CLOSEOUT, G-NO-LIVE, G-TIMING-LOGS, G-EVIDENCE. No source edit, no live probe, no log dump, no credential read. Keys-only TTS provider/model/speed were read from the live profile. Voice timeline was not read (mixed content).

## Phase status

| Phase | Status |
|---|---|
| 1 Baseline | Complete |
| 2 Audio lifecycle and TTS trace | Complete |
| 3 Echo and buffering | Complete |
| 4 Always-listening | Complete |
| 5 Integration | Complete |
| 6 Options | Complete |
| 7 Proof plan | Complete (design only) |
| 8 Reconciliation | Complete |
| 9 Synthesis | Complete |
| 10 Closeout | Content committed. Integration not done in this commit. |

## Limitations

- SYM-01 and SYM-02 causes are UNRESOLVED. No reproduction by this audit.
- SYM-05 current frequency is UNRESOLVED. Edge figures are historical. Live provider is Deepgram command.
- Hardware endpoints, enhancements, level, and room are UNKNOWN. PC is a Latitude 7430 on Windows 11 build 26200, observed by WMI.
- P9-SPEAK is in smoke, not closed, not on `main`.
- Android `speech/**` is deleted in the working tree; those files were read from HEAD.
- No `AGENTS.md` in the Zola-Windows tree.
- Later-than-pin Hermes voice behavior was not inspected.
- AEC support of the attached endpoints was not probed.

## Running findings

| ID | Label | Severity | Source | Summary |
|---|---|---|---|---|
| VOICEPRE-AUD-01 | [MATCH] | N/A | Hermes + client monitor | Serve owns the devices |
| VOICEPRE-AUD-02 | [MATCH] | N/A | `methods_voice.py` L158–161 | Barge listener stays disarmed when the flag is false |
| VOICEPRE-AUD-03 | [MATCH] | N/A | `TranscriptAdmission.cs` | One admission authority |
| VOICEPRE-AUD-04 | [MATCH] | N/A | follow-up + monitor | Monitor outranks the estimate |
| VOICEPRE-AUD-05 | [GAP] | HIGH | P4-D28 / S36 | Talk-over deliberately absent |
| VOICEPRE-AUD-06 | [RISK] | HIGH | `_fd_trip` + Decide | Flag flip drops the words and ignores clarify |
| VOICEPRE-AUD-07 | [GAP] | HIGH | `start_continuous` | No pre-roll; beep first |
| VOICEPRE-AUD-08 | [GAP] | MEDIUM | `voice.record` | No capture id, no cancel |
| VOICEPRE-AUD-09 | [RISK] | HIGH | echo matcher + 450 ms bout | Self-echo can still be admitted; cause of current reports open |
| VOICEPRE-AUD-10 | [GAP] | HIGH | wake / record-once | Wake-free idle listening absent |
| VOICEPRE-AUD-11 | [GAP] | MEDIUM | no completion RPC | Playback end is ffplay presence |
| VOICEPRE-AUD-12 | [RISK] | MEDIUM | command TTS | Per-sentence file playback; current gaps unmeasured |
| VOICEPRE-AUD-13 | [RISK] | MEDIUM | overlay LocalGate | Open capture denies all proactive speech |
| VOICEPRE-AUD-14 | [RISK] | LOW | VOICE_CONFIG vs live keys | Canonical file still documents Edge |
| VOICEPRE-AUD-15 | [GAP] | MEDIUM | no Windows directedness | Addressee gate absent; Android's does not admit turns |

Counts: 4 MATCH, 6 GAP, 5 RISK. HIGH 5, MEDIUM 5, LOW 1.

## Documents

- `Zola_VOICEPRE_Audit_01_Baseline.md`
- `Zola_VOICEPRE_Audit_02_AudioLifecycle.md`
- `Zola_VOICEPRE_Audit_03_EchoAndBuffering.md`
- `Zola_VOICEPRE_Audit_04_AlwaysListening.md`
- `Zola_VOICEPRE_Audit_05_Integration.md`
- `Zola_VOICEPRE_Audit_06_Options.md`
- `Zola_VOICEPRE_Audit_07_ProofPlan.md`
- `Zola_VOICEPRE_Audit_08_Reconciliation.md`
- `Zola_VOICEPRE_Audit_SYNTHESIS.md`
- `Zola_VOICEPRE_Audit_PROGRESS.md`

## Closeout

Approved with "proceed to closeout". No `AGENTS.md` in the Zola-Windows tree. Primary checkout remains dirty `p9-speak` and is not the integration target.

- Audit-content SHA: `543b36819e38704f815b6f77bed67f0228ebea79`
- Content preparation: complete
- Integration: not merged. No clean `main` worktree existed when this metadata was written.
