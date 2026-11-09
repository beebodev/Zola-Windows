# Zola S51F-PRE — 03 Lost request when serve crashes

Phase 5. Labels **SOURCE** / **EVIDENCE** / **INFERENCE** / **UNRESOLVED**.  
Prior: S51 audit §2 / `_05_CodePaths.md` request-on-crash. G-NO-FIX.

---

## 1. What the client knows when serve dies

| Question | Answer | Cite | Label |
|----------|--------|------|-------|
| Turn in progress? | `_streaming == true` while a turn is open; cleared in `ShowSupervisionStatus`, but **`_turnFinalized` is not set true** on gap | `MainWindow.xaml.cs` L1301–1305; submit arms `_turnFinalized=false` | SOURCE |
| Since when? | `TurnTiming` holds `_submitAt` while `IsOpen`; not consulted by unreachable UI | `Voice/TurnTiming.cs` L116+, `IsOpen` | SOURCE |
| Voice vs typed? | `TurnTiming` kind `voice` / `typed` on the open timing object | `TurnTiming.KindVoice` / `KindTyped` | SOURCE |
| Any reply text arrived? | Timing: `_firstDeltaAt`, `_accumulated`. UI: live bubble text can remain (gap does **not** clear `_live`) | TurnTiming; `OnMessageDelta` / `ShowSupervisionStatus` | SOURCE |
| Tool / approval pending? | Timing `_tools` / `_approval`; display tools wiped (`ClearToolActivity`); broker may still hold open cards until reconcile | L1308; `ChatSocket.LastPendingApprovalPresent`; TurnTiming `NoteToolStart` / `NoteApproval` | SOURCE |
| What Brian is shown | Status only: `SupervisionConstants.StatusRestarting` ("Zola's backend stopped. Restarting…"); **reason discarded** | `ShowUnreachable` L1289–1298; `StatusRestarting` | SOURCE |
| Voice / capture | Fail closed: `AbandonPendingQuestion(GapReason)`; VoiceController gap uses `backend-unreachable` | L1307; `VoiceController` ~L1645–1659; `GapReason` | SOURCE |

**INFERENCE:** enough in-memory state exists to know an open turn was dropped; the outage UI never consults it for Brian-facing copy.

**Gap (unchanged from S51):** no announcement that *this request's answer was dropped*.

---

## 2. After restart

| Question | Answer | Label |
|----------|--------|-------|
| Can client tell previous turn never completed? | Partially: it saw `_streaming` → unreachable cleared streaming without `message.complete`. No durable "lost turn" UI row today | SOURCE / INFERENCE |
| Same session or new? | Supervision resumes stored session when configured; session id may continue after reconnect | EVIDENCE prior P9-SUPERVISE |
| Hermes replay interrupted message? | **`desktop.auto_continue.enabled: false`** in live profile (confirmed keys-only read). Auto-continue model turn does **not** run (S69 path off) | EVIDENCE config; SOURCE `session_auto_continue.py` behavior documented in P9 lore |

---

## 3. Options (describe only)

### (a) Visible line in the conversation

- **Brian sees:** a system/status line that his last request did not finish (not the restart chrome alone).
- **Brian hears:** nothing unless paired with (b).
- **Integration:** Zola client change on unreachable / post-restart (supported Zola surface). No Hermes fork required for a client-authored notice.

### (b) Zola says it in her own voice once back

- **Brian hears:** a short spoken notice after serve is healthy again.
- **Integration:** needs **model-authored** or **client-local** speech. Pandora/Deepgram needs serve up. Hardcoded line conflicts with "her own words" preference if used as the product recommendation.
- **Hermes:** optional post-reconnect prompt would be a design/Hermes or client submit — treat carefully with approvals (fail closed).

### (c) Automatic re-submission of his last request

- **Brian experiences:** the same ask runs again without him repeating it.
- **Consequential repeat risks** (fail closed):

| Action class | Risk on blind replay | Existing guards |
|--------------|----------------------|-----------------|
| `gmail_send` / send draft | Duplicate send | P8-D06 single-use send authorization; spoken-phrase approval — **process-local**; may **not** survive crash (**INFERENCE** / P9 lore: crash replay gets no origin ticket) |
| Calendar write | Duplicate event / update | Same approval posture where gated |
| Forget | Destructive memory wipe replay | Must not auto-replay without fresh authority |
| Watch create / mutate | Duplicate watches | Fail closed without ticket |
| Read-only tools (calendar_query, search) | Mostly annoyance / extra API | Lower severity; still not free |

**Fail-closed rule for any fix track:** do not auto-resubmit unless Brian-visible authority is proven intact after restart; prefer (a)/(b) over (c). With `auto_continue` already false, Hermes will not silently continue the interrupted turn as a model job.

---

## 4. Can she speak while serve is down?

| Path | Available? | Note |
|------|------------|------|
| Pandora / Deepgram / Hermes TTS | **No** — serve is down | SOURCE |
| Client **Zira** code-read voice | **Technically yes** for a short local line (R1 path: local render, no file/network) | SOURCE CodeRead / `LocalCodeVoice` |
| Design | Using Zira for a crash notice is a **different voice** from identity Pandora — design question, **not** a recommendation here | — |

---

## Findings

| ID | Severity | Summary |
|----|----------|---------|
| S51F-AUD-08 | HIGH | Restart status shown; lost in-flight request still not announced (carries S51-AUD-02) |
| S51F-AUD-09 | MEDIUM | Auto-resubmit unsafe for send/calendar write/forget/watch without surviving single-use authority |
| S51F-AUD-10 | INFO | Zira could speak locally while serve is down; identity-voice mismatch is a design call |
