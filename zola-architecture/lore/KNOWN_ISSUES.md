# Known issues

SOP v3 Stage 0 input. The next phase does not start while an open serious issue exists (PR-D03); unrelated minor bugs never block a phase. Each row has a dated status line.

**PR-D03 serious** means: a crash or hang of a core process; data loss or memory corruption; a privacy or security leak; a safety-gate bypass (e.g. send approval, verification-code masking, voice privacy); a break in the core conversation loop (can't talk to the assistant); or any issue in the area the next phase builds on. Historical serious failures get a time-boxed investigation, not an automatic indefinite block. A serious issue becomes a blocker only if it still reproduces or its cause is still present in current code.

Counting rule for serve crashes (S51M, 2026-11-16): faulting PID is a `supervisor` serve `child_pid`, or a faulthandler block for that crash is in `ZolaClient\logs\serve-stderr\`.

| id | title | area | severity | serious? | status | evidence |
|----|-------|------|----------|----------|--------|----------|
| KI-S51-PA | PortAudio / Group A serve crash | voice/audio | high | yes | mitigated, watching | No PortAudio-module Application Error since 2026-11-09 13:23:08 (MEASURED). Stream direction input vs output remains UNRESOLVED inside S51 Group A. S51F-D01/D03. |
| KI-S51-3B1FF | `python312.dll+0x3b1ff` shutdown race | memory/serve | critical | yes | fix shipped, watching | S51M fix promoted `fix-s51m` 2026-11-16 07:43:37. Live stacks on old code fit consolidator-in-SQLite + teardown shutdown. History fit 6/3/1. Watch quiet since promote: 0 (MEASURED 2026-11-16). |
| KI-S51-SQLITE | sqlite AV during consolidate/shutdown | memory/serve | critical | yes | fix shipped, watching | Same race class as KI-S51-3B1FF. History fit 0/2/1. Nov-12 10:47 live serve-child. Watch quiet since promote: 0 (MEASURED 2026-11-16). |
| KI-S51-UI | `Zola.Client.exe` UI crash class | client | medium | no | open | **2026-11-10 08:10–08:11 (4 AEs):** PROC1-STABLE first-switch crash — `dotnet publish` staging omitted `.xbf`/`.pri`; fault `Microsoft.UI.Xaml.dll` / `0xc000027b`. Fixed by `dotnet build -o` plus the WinUI resource gate (`PROC1-STABLE_Progress.md`). **Original Sep–Oct class (S51 audit):** last occurrence **2026-10-13 15:34:04** (`CoreMessagingXP.dll` / `0xc000027b`, timeline row 20); no recurrence identified since. serious=no. |
| KI-S51F-ADMIT | Admit→submit gap | voice | low | no | open | ~22 ms median measured in S51F-FIX. |
| KI-S51F-ECHO | Self-echo | voice | medium | no | open | Includes 2026-11-09 S1 turns; speech-baseline related. |
| KI-S51F-MIC | Mic button does not interrupt a reply | voice | medium | no | open | S51F known residual. |
| KI-S51F-STOP | Stop Speaking unavailable on unprompted lines | voice | medium | no | open | S51F / P9 observation. |
| KI-S51F-CLIP | Clipped opening words | voice/TTS | medium | no | open | S51F residual. |
| KI-S51F-HERMESROOT | Release build outside Dev can't find Hermes | launch | high | no | fixed | Fixed by PROC1-STABLE User env `ZOLA_HERMES_ROOT`. |
| KI-PROC1-PRESENCE | `presence.log` unbounded growth | ops | medium | no | open | SOURCE: `PresenceView.WriteLog` → `ClientPaths.LogsDirectory` / `presence.log` (`PresenceView.cs` ~1118–1131; `ClientPaths.cs` role folder `ZolaClient` or `ZolaClient-dev`). MEASURED 2026-11-16: `%LOCALAPPDATA%\ZolaClient\logs\presence.log` = **375,592,721** bytes (lw 2026-11-16 08:48); `%LOCALAPPDATA%\ZolaClient-dev\logs\presence.log` = **1,481,716** bytes. Manual `.bak-*` copies only (Sep 28); **no rotation**. |
| KI-PROC1-WT | Leftover worktree folders | ops | low | no | open | 2026-11-16: `zola-windows-proc1-gate`, `proc1-id`, `proc1-stable` still on disk; `C:\Users\test\Zola\stable\_failed` present. |
| KI-PROC1-BACKUP | Stable backups never pruned | ops | low | no | open | 2026-11-16: 5 folders under `stable\backups`. |
| KI-PROC1-WATCHER | Watcher `job_assigned` missing on one launch | supervision | low | no | open | 2026-11-10 09:19 fix-s51f launch: watcher processes live, no `job_assigned` line (PROC1-STABLE). |
| KI-PROC1-AUTH | `hermes auth add openai-codex` reports Added without persisting | auth | medium | no | open | PROC1 track record. |
| KI-S51M-LOCK | Forget/tool reads not serialized with consolidator transactions | memory | medium | no | open | S51M known issue (not fixed). |
| KI-S51M-RETRIEVE | Retrieval sees only finished episodes | memory | medium | no | open | Catch-up after reopening; S51M known. |
| KI-S51M-CLOSE | Client close kills serve; graceful teardown skipped | session | medium | no | open | S51M Phase 5 SOURCE. |
| KI-S100 | Phase 10 operations hygiene | phone/ops | low–medium | no | open | See OPEN_QUESTIONS **S100** (pointer only; do not duplicate the ten bullets). |
| KI-FEAT-GAUTH | Google sign-in from inside the app | auth/UX | feature | no | requested | Brian: "We have to make a note to add google auth to the app UI." |

### Dated status lines

- **2026-11-16 — KI-S51-PA.** Status: mitigated, watching (S51F). Review ~2026-11-23; resolve by dated note if watch quiet under the counting rule.
- **2026-11-16 — KI-S51-3B1FF / KI-S51-SQLITE.** Status: fix shipped (`fix-s51m`), watching. Review ~2026-11-23; resolve by dated note if watch quiet. Do not claim the historical class closed.
- **2026-11-16 — KI-S51-UI.** Nov-10 cluster = PROC1-STABLE publish miss (fixed). Original Sep–Oct class: last at 2026-10-13 15:34:04; no recurrence identified since. serious=no.
- **2026-11-16 — KI-PROC1-PRESENCE.** Path is client logs (`ZolaClient` / `ZolaClient-dev`), not the Hermes profile. Stable file 375,592,721 bytes, unrotated; dev 1,481,716 bytes.
- **2026-11-16 — KI-S51F-HERMESROOT.** Status: fixed (PROC1-STABLE).
