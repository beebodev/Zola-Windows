# P10PRE Audit Progress

**Audit ID:** P10PRE
**Status:** Phases 1–12 COMPLETE. Closeout approved with "proceed to closeout".
**Updated:** 2026-10-12 11:06 -07:00

## Repository A

- Audit branch: `audit/p10pre`
- Audit worktree: `C:\Users\test\Dev\zola-windows-p10pre`
- Worktree HEAD at setup: `19eaebcd755418985943d6140e01d97ad06f8ca0` (equals `main`)
- Base `main` SHA: `19eaebcd755418985943d6140e01d97ad06f8ca0`
- `origin/main` SHA: `19eaebcd755418985943d6140e01d97ad06f8ca0` (re-checked 2026-10-12; equal; no pull, reset, or merge)
- Output directory: `zola-architecture/audit/p10pre-phase10/`

### Primary folder (not modified)

- Path: `C:\Users\test\Dev\zola-windows`
- Checked-out branch: `p9-supervise`
- State: dirty (same paths as Setup: modified `windows-client` client/checks files, untracked `Supervision` sources, untracked `P9-SUPERVISE_Progress.md`)

## Repository B

- Path: `C:\Users\test\StudioProjects\ZolaAssistant`
- `.git/HEAD`: `ref: refs/heads/zola-main`
- SHA from `.git/refs/heads/zola-main`: `a139ccacab596f12b95e2dd3eda14352bcb97836`
- Read time: 2026-10-12 07:39:39 -07:00 (survey reads were filesystem-only; no Git commands)
- Present, contents not used as source text except the security classification in Phase 6: Gradle wrapper 8.11.1, `local.properties`, `app/google-services.json`
- `*.jks` / `*.keystore`: not found
- Repository B modified by this audit: no

## Documents of Truth

- `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md`
- `zola-architecture/lore/ROADMAP.md`
- `zola-architecture/lore/DESIGN_DECISIONS.md`
- `zola-architecture/lore/OPEN_QUESTIONS.md`
- Background only: `zola-architecture/Zola Distributed Presence Architecture.md`

### Lore entries

- **S13 — Windows-viable path to read the user's own incoming SMS.** Open. P9-KICKOFF brainstorm intake is marked not a decision.
- **S73 — Android companion and distributed presence.** Open. Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Strawman DP entries are proposals.
- **S74 — Remote escalation (phone call).** Open. Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Present.

INFO: `S13` still lists Phone Link and Twilio as research candidates beside the companion brainstorm.

## Phase status

| Phase | Status |
| --- | --- |
| 1 Setup | COMPLETE |
| 2 Inventory | COMPLETE |
| 3 Capture | COMPLETE |
| 4 Background | COMPLETE |
| 5 Transport and storage | COMPLETE |
| 6 Security | COMPLETE |
| 7 Connections | COMPLETE |
| 8 Capability fit | COMPLETE |
| 9 Lessons | COMPLETE |
| 10 Gaps | COMPLETE |
| 11 Synthesis | COMPLETE |
| 12 Closeout | COMPLETE |

## Guardrails

- G-SCOPE / G-NOCHANGE: writes are only under `zola-architecture/audit/p10pre-phase10/` in the audit worktree.
- G-READONLY-B: no Git, Gradle, or writes in Repository B.
- G-SECRETS: candidates recorded as path, line, type, value redacted. Commit status not checked.
- G-TIER: Tier 2 internals were not audited. FCM use is recorded in Phase 7.
- G-NO-INSTALL: network use was `git fetch origin` in Repository A only.
- G-CLOSEOUT: approved. 12a passed: worktree changes are only `zola-architecture/audit/p10pre-phase10/`. Repository B `.git/HEAD` is still `ref: refs/heads/zola-main` and `.git/refs/heads/zola-main` is still `a139ccacab596f12b95e2dd3eda14352bcb97836`. This audit did not write to Repository B.

## Closeout SHAs

- Audit tip SHA (12c): `99c799d3d4cd542106279f5ba39c35220ee90e5f`
- Merge SHA (12h): not yet recorded.

## Running findings

| ID | Label | Severity | Verdict | File | Summary |
| --- | --- | --- | --- | --- | --- |
| P10PRE-AUD-01 | RISK | HIGH | LEAVE architecture / ADAPT parse | `SmsReceiver.kt`, `SmsContentProviderPoller.kt` | Proactive SMS uses Firestore people and the brain bus. |
| P10PRE-AUD-02 | RISK | HIGH | ADAPT / LEAVE tool type | `MessageReadToolAdapter.kt`, `NotificationReadToolAdapter.kt` | Capture tools are on-phone `AssistantTool` adapters. |
| P10PRE-AUD-03 | RISK | MEDIUM | ADAPT | `MessageSendToolAdapter.kt` 135 | SMS body preview in logcat. |
| P10PRE-AUD-04 | GAP | HIGH | No old component | — | No phone–PC exchange or pairing proof. |
| P10PRE-AUD-05 | RISK | MEDIUM | ADAPT | `SmsReceiver.kt`, `MainActivity.kt` | Activity-scoped poller; emit dropped if the bus is unset. |
| P10PRE-AUD-06 | RISK | MEDIUM | REWRITE | `ZolaFcmService.kt` | FCM handler is Auth plus Firestore handoff. |
| P10PRE-AUD-07 | RISK | HIGH | — | `diagflow_service_account.json` line 5 | Private key in the tree. Commit status not checked. |
| P10PRE-AUD-08 | RISK | HIGH | — | `google-services.json`, `local.properties`, progress markdown | API key candidates in the tree. Commit status not checked. |
| P10PRE-AUD-09 | RISK | MEDIUM | LEAVE | `DeviceInstallIdProvider.kt`, `ZolaFcmService.kt` | Install id and FCM token are not in Keystore. |
| P10PRE-AUD-10 | RISK | LOW | LEAVE | `CognitivePrepDebugReceiver.kt` | Exported debug receiver; release no-ops. |
| P10PRE-AUD-11 | MATCH | — | ADAPT | SMS receiver, poller, read adapter | SMS acquisition exists. |
| P10PRE-AUD-12 | MATCH | — | ADAPT | notification listener and read manager | Notification acquisition exists. |
| P10PRE-AUD-13 | MATCH | — | ADAPT | `MessageReadToolAdapter.kt` | On-demand SMS results use named fields. |
| P10PRE-AUD-14 | RISK | LOW | ADAPT | `LocationHelper.kt` 150–154 | Coordinates in logcat. |

Totals: 14 findings — 5 HIGH, 4 MEDIUM, 2 LOW; 3 MATCH.
Reuse tally: REUSE 0, ADAPT 11, REWRITE 1, LEAVE 7, No old component 5.
FCM present: yes.
INFO items: 19 (see synthesis).
