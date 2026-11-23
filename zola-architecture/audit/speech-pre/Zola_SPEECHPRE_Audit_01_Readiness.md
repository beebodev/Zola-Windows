# SPEECH-PRE Audit 01 — Readiness (PR-D03 / PR-D04 / PR-D08)

**Labels:** EVIDENCE unless marked otherwise.  
**Base SHA:** `bc4fd8b4dab18da2b0026d7423825d5715e75500`  
**Branch:** `speech-pre-audit`  
**Hermes HEAD:** `345cd2b057a452236de401d3534b8502a7465e8d` (= pin), clean tree.  
**Prompt SHA-256:** `f1cba41957591a555edea335e3a676b39cac4d200bb0fd3e796d1ec96c8ee8c4` (MATCH Brian's expected).

---

## 1. Setup

| Check | Result |
|-------|--------|
| `main` = `origin/main` | EVIDENCE: both `bc4fd8b4…`, porcelain empty before branch create |
| Branch `speech-pre-audit` | Created from that tip |
| Output folder | `zola-architecture/audit/speech-pre/` |
| Hermes pin | HEAD match; porcelain empty |
| Spike listings | `speech-spike-2` 6594 files; `speech-spike` 3179 files (recorded in agent store; re-check at closeout) |
| Speech docs | Six inputs hashed in progress doc; three Brian-expected hashes MATCH |

Brian readiness STOP answer (verbatim, for missing attachments): files placed under `zola-spikes\prompts\` and `speech-pre-inputs\`; older spike-docs `SPEECH_DECISIONS` ignored.

---

## 2. Stability gate (PR-D03)

### 2.1 Open serious issues and every voice issue (`KNOWN_ISSUES.md`)

**Serious (serious?=yes):**

| id | area | status | Notes for this gate |
|----|------|--------|---------------------|
| KI-S51-PA | voice/audio | **mitigated, watching** | Not status=`open`. PortAudio Group A; relevant to moving mic out of serve — record, don't decide (Known context). |
| KI-S51-3B1FF | memory/serve | **fix shipped, watching** | Not voice/speech area. |
| KI-S51-SQLITE | memory/serve | **fix shipped, watching** | Not voice/speech area. |

**Voice issues (any severity):**

| id | severity | serious? | status |
|----|----------|----------|--------|
| KI-S51-PA | high | yes | mitigated, watching |
| KI-S51F-ADMIT | low | no | open |
| KI-S51F-ECHO | medium | no | open |
| KI-S51F-MIC | medium | no | open |
| KI-S51F-STOP | medium | no | open |
| KI-S51F-CLIP | medium | no | open |

No row with `serious?=yes` **and** `status=open` in the voice/speech area. KI-S51-PA is mitigated/watching, not open.

### 2.2 Live serve crash count since 2026-11-16 07:43:37

Counting rule (KNOWN_ISSUES / S51M): serve `child_pid` in `supervisor.log` that ended unexpectedly, **or** a faulthandler block for that crash in `serve-stderr.log`.

**supervisor.log** (lw 2026-11-16 09:14:49; no rotations present):

Lines with `proc=serve` and timestamp ≥ watch start:

| Timestamp | event | generation | child_pid |
|-----------|-------|------------|-----------|
| 2026-11-16T07:43:38 | `start` | 1 | 25956 |
| 2026-11-16T09:14:48 | `start` | 1 | 28008 |

No `restart`, `keeps_failing`, or unexpected-end events for serve after the watch start. **EVIDENCE:** unexpected serve ends = **0**.

**serve-stderr.log** (lw 2026-11-20 09:40:05): four `Windows fatal exception: access violation` blocks exist in the file. Stacks attribute to `zola_memory` `store.py` / `consolidate.py` (memory/sqlite class — KI-S51-SQLITE), **not** PortAudio. Blocks have **no ISO timestamps**. No matching supervisor unexpected serve end after the watch start. Application log query for `python.exe` / PortAudio AVs since the watch returned **empty**.

**INFERENCE:** the four faulthandler blocks are historical residue in the rolling stderr file from the pre-`fix-s51m` (or at-promote) memory class, not live crashes during the watch window.

**Live serve crash count since 2026-11-16 07:43:37: 0**

**Other `python.exe` access violations attributable to other processes:** none found in Application log for the watch window (EVIDENCE: empty query).

---

## 3. Experience log (PR-D04) — voice / listening / speaking

From `EXPERIENCE_LOG.md` (all rows; voice-touching marked):

| date | id/track | One line |
|------|----------|----------|
| 2026-11-09 | S51F-FIX | she no longer beeps at me. **(voice)** |
| 2026-11-09 | S51F-FIX | If her backend dies while I'm asking something, I'm told it didn't go through and to ask again **(conversation / lost-request; touches speech track failure UX)** |
| 2026-11-10 | PROC1-STABLE | SM-S1 passed; functions worked; shortcut feels the same |
| 2026-11-10 | PROC1-ID | Second start names which Zola is running |
| 2026-11-13 | PROC1-DEV | Dev Zola isolated from real data/phone |
| 2026-11-13 | PROC1-GATE | Works as expected |
| 2026-11-15 | S51M-FIX | Conversation end doesn't crash; memory kept |
| 2026-11-15 | S51M-FIX (dev smoke) | Recalled invented astronaut fact |

Voice/listening/speaking entries for the track: **S51F beep-off** and **lost-request notice** (plus PROC1 SM-S1 which includes wake/follow-up by scenario).

---

## 4. Scenarios (PR-D08) — voice, conversation-continuity, privacy, safety-gate

From `SCENARIO_LIBRARY.md` (areas requested). No dedicated `safety-gate` area rows exist in the library table; P8 send-approval scenarios live in architecture AU* lists, not here.

### Voice

| id | One line | last passed |
|----|----------|-------------|
| SC-S51F-SM1 | Wake, follow-up, clarify; no beeps; can tell when listening | fix-s51f |
| SC-S51F-EXP-BEEP | Everyday talk; she no longer beeps | fix-s51f |

### Conversation continuity

| id | One line | last passed |
|----|----------|-------------|
| SC-S51F-SM2 | Kill serve mid-turn; notice to ask again; no auto-resubmit | fix-s51f |
| SC-S51F-SM3 | Faulthandler env + supervisor restart/start lines | fix-s51f |
| SC-S51F-EXP-LOST | Backend dies mid-ask; told to ask again | fix-s51f |
| SC-PROC1-S1 | Wake, question, follow-up, calendar/email, phone; shortcut feels same | fix-s51f / proc1-stable path |

### Privacy

| id | One line | last passed |
|----|----------|-------------|
| SC-PROC1-DEV1 | Start dev without zola-dev → refuse; live untouched | proc1-dev |
| SC-PROC1-DEV2 | Dev profile → zola-dev; synthetic memory; no phone | proc1-dev |
| SC-PROC1-DEV3 | Dev + test Google calendar/draft not on real account | proc1-dev |
| SC-PROC1-DEV5 | Dev phone tools can't reach / unavailable | proc1-dev |

### Safety-gate

None in `SCENARIO_LIBRARY.md` under that area name. **INFO:** P8 passphrase / send-gate covered by architecture AU scenarios and `hermes-plugins/zola_workspace/tests/test_p8_send.py` (Phase 9).

**References (not copied):** speech-baseline sessions A/B under `zola-spikes\speech-baseline\` (PROC1-D11).

---

## Readiness verdict

**readiness: PASS**

Evidence: no open serious issue in the voice/speech area (KI-S51-PA is mitigated/watching); live serve crash count since 2026-11-16 07:43:37 is **0**. Continuing to Phase 2 without stop.
