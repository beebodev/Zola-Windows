# Scenario library

SOP v3 behavioural regression library (PR-D08). Grows at each lore closeout. Speech-baseline cases are **referenced**, not copied (PROC1-D11).

**PR-D08 fields:** an ID; its area (memory, identity, privacy, conversation continuity, voice, permissions, proactive behavior); the setup; the steps; the expected behavior (what happens and what it should be like); whether it is automated or scripted-manual; and the tag it last passed on.

| id | area | setup | steps | expected | kind | last passed |
|----|------|-------|-------|----------|------|-------------|
| SC-S51F-SM1 | voice | S51F applied; stable up | Wake, follow-up, clarify | No beeps; can tell when she is listening | scripted-manual | fix-s51f |
| SC-S51F-SM2 | conversation continuity | S51F applied | Kill serve mid-turn; re-engage | Notice to ask again; no auto-resubmit; partial interrupted | scripted-manual | fix-s51f |
| SC-S51F-SM3 | conversation continuity | After SM2 | Check faulthandler env + supervisor restart/start | Lines present | automated / Cursor | fix-s51f |
| SC-S51F-EXP-BEEP | voice | After S51F everyday | Talk with Zola | Brian: she no longer beeps | scripted-manual | fix-s51f |
| SC-S51F-EXP-LOST | conversation continuity | Backend can die mid-ask | Backend dies during a request | Brian: told it didn't go through and to ask again | scripted-manual | fix-s51f |
| SC-PROC1-S1 | conversation continuity | Stable shortcut | Wake, question, follow-up, calendar/email, phone | Functions work; shortcut feels same as before (repo wording) | scripted-manual | fix-s51f / proc1-stable path |
| SC-PROC1-S2 | identity | After Switch | Launch from Desktop shortcut | Exe under `stable\<tag>\`; live profile serve | scripted-manual | fix-s51f |
| SC-PROC1-S3 | identity | After Switch | Cursor isolation checks | Shortcut outside repos; hashes hold | automated | fix-s51f |
| SC-PROC1-ID1 | identity | Dev build | Second start | Refuses; names holder | scripted-manual | proc1-id |
| SC-PROC1-ID2 | identity | Lock-aware build | Second start; cleanup after close | Refuses; cleanup OK | scripted-manual | proc1-id |
| SC-PROC1-ID3 | identity | Stable and dev | Both orders | Each refuses naming the other | scripted-manual | proc1-id |
| SC-PROC1-ID4 | identity | Stable with plugin drift | Start | Non-blocking drift notice | scripted-manual | proc1-id |
| SC-PROC1-ID5 | identity | Stable | Start | Supervisor identity + drift fields | automated | proc1-id |
| SC-PROC1-DEV1 | privacy | No `zola-dev` | Start dev | Refuse pop-up; live untouched | scripted-manual | proc1-dev |
| SC-PROC1-DEV2 | privacy | Dev profile present | Start | `zola-dev`; synthetic memory; no phone | scripted-manual | proc1-dev |
| SC-PROC1-DEV3 | privacy | Dev + test Google | Calendar read / draft (not send) | Not on real account | scripted-manual | proc1-dev |
| SC-PROC1-DEV4 | memory | Dev | Memory write | Only in dev stores | scripted-manual | proc1-dev |
| SC-PROC1-DEV5 | privacy | Dev | Phone tools | Can't reach / unavailable | scripted-manual | proc1-dev |
| SC-PROC1-DEV6 | identity | Dev running | Stable shortcut | Refused while other build runs | scripted-manual | proc1-dev |
| SC-S51M-ORPHAN | memory | Dev after Sync-DevPlugins | Invented fact → UI New Conversation → wait ≥30s → ask in new session | No serve crash; WS-orphan teardown + shutdown; recall (invented astronaut fact) | scripted-manual | fix-s51m (dev smoke) |
| SC-S51M-EXP | memory | After S51M promote | End conversation; ask next time | Brian experience: no crash; remembered | scripted-manual | fix-s51m |

**References (not copied):** `C:\Users\test\Dev\zola-spikes\speech-baseline\` (SPEECH-BASELINE sessions A/B; PROC1-D11).
