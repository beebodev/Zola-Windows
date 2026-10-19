# P9-LORE Progress — Phase 9 Lore Closeout

## Branch

- Work branch: `p9-lore` (from `main`, not committed)
- Base `main` = `origin/main`: `96155dbcfd58883a70ab42efb7b6c94ac015a518` (P9-SPEAK docs follow-up; clean)
- Hermes HEAD: `345cd2b057a452236de401d3534b8502a7465e8d` (tag `v2026.9.14`, clean)
- Prompt: `P9-LORE_Prompt_v1.0.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P9-LORE_Prompt_v1.0.md`)
- Prompt SHA-256 (on-disk, 42,134 bytes): `2A4D94670B351E271036B22B6A8B051BEDF91DE21E3A20F5AA61B2E640DA0C91`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction. On-disk value recorded for Brian to confirm.

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch, inputs, inventory | COMPLETE (STOP) |
| 2 | Draft DESIGN_DECISIONS.md | COMPLETE (STOP) — revised, not applied |
| 3 | Draft OPEN_QUESTIONS.md | COMPLETE (STOP) — draft below, not applied |
| 4 | Draft ROADMAP.md | COMPLETE (STOP) — revised for the old candidate list, not applied |
| 5 | Live, identity, and external verification | COMPLETE (STOP) — read-only, below |
| 6 | Apply, verify, STOP | COMPLETE (STOP) — applied, not committed |
| 7 | Commit and merge | COMPLETE. Implementation `748534b19d570741dd22196896e6fe8efee2e46b`. Merge `8842d315420574a012f2a2d0cd103507560bd376`. |

Phase 5 addition, run below. The ACL of `%LOCALAPPDATA%\ZolaClient\secrets\` and of the key file was read. The contents were not.

## Guardrails summary

- **G-LORE-ONLY:** `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`, and this progress doc. `VOICE_CONFIG.md`, another `identity/` mirror, and the two privacy-plan lines only if Phase 5 proposes the exact text and Brian approves it. No code, plugin, test, config, client, build plan, or live-profile edits.
- **G-NO-CROSS-SCOPE:** Phase 10, VOICEPRE, VOICEBASE, and avatar v2 are not Phase 9. They appear below only as out-of-scope commits.
- **G-STOP:** this phase stops here. Nothing is committed.

## Phase 1 — inventory

Discrepancies: every required SHA is an ancestor of `main` and matches the SHA recorded in its progress doc. One record gap: the Systems panel quotes and the K7 acceptance quote were relayed to Cursor during Track 6 but were not written into `P9-SPEAK_Progress.md`. They are Appendix Q entries from the Track 6 working chat (claude.ai, "Track 6 prompt", 2026-10-17..19).

### Merge ancestry

| Item | Commit | Ancestor | Progress doc |
|---|---|---|---|
| P9-KICKOFF merge | `9d50ebcc7d6370c289419f7122536366b1e25df3` | yes | merge matches; implementation in that doc is `86b96a7d70af56744724e6b59fc3c7443829ede9` |
| P9PRE audit content | `4bf9a32497efc5c589b2d7b792466bc98f6ab4b4` | yes | commit subject is the audit |
| P9PRE merge | `925fa2c7951e9415e09c156209270bb0d3504f7d` | yes | commit subject is the merge |
| P9-FIX-ARM implementation | `f348c2db25d908fad7ee95182a659840144efe59` | yes | matches |
| P9-FIX-ARM merge | `18d4062a84c6ed37e6d9c4f22fbcdec81f1b207f` | yes | matches |
| Build plan | `d3f62cfaed970a69ff5cfc75f156e173411851f2` | yes | commit subject is the plan |
| Build plan merge | `19eaebcd755418985943d6140e01d97ad06f8ca0` | yes | commit subject is the merge |
| P9-SUPERVISE implementation | `48ec49b90ed92ea312ad2409decb95134d0c9503` | yes | matches |
| P9-SUPERVISE merge | `574fe43fb4532878eaff32c2c9f6e4baa9291c9a` | yes | matches |
| P9-FIX-TTS implementation | `0d6e56c94b29458c3e0ea8a9134a8a50f74a2a02` | yes | matches |
| P9-FIX-TTS merge | `72243cb5fa3384ccee19f4ace9728baa0001de06` | yes | matches |
| P9-STORE implementation | `b13989a8f96c713214cb5537e24a401a02526bff` | yes | matches |
| P9-STORE merge | `7e5ea69791173822ff7cba1ea5fcfecd979ebed2` | yes | matches |
| P9-WATCH implementation | `27b56b59d8be5295501177914b22330bc0189aec` | yes | matches |
| P9-WATCH merge | `05ac85f5a9634be80726cb883e94476f60e74997` | yes | matches |
| P9-RANK implementation | `df68dd432b92a634ce4e2b519499d715a8f2179b` | yes | matches |
| P9-RANK merge | `5def3d3ed90bcea2cebe087fd7d4ef52cb801bb1` | yes | matches |
| P9-SURFACE implementation | `bae7ac4874efff807204b977bb6dc0491d27b504` | yes | matches |
| P9-SURFACE merge | `0f880ad00e4c1574d133f3c9e1f9ed08563072cd` | yes | matches |
| P9-SPEAK implementation | `20ea9aeffebabb632eb2b55fb5f36c1189fb514f` | yes | matches |
| P9-SPEAK merge | `abeff7e516bc4c4a9fb9d060cdd414c83b57f5af` | yes | matches |
| P9-SPEAK docs follow-up | `6c180cca9cf4cc5e241d46cbee39fed94fe28058` | yes | merge-SHA record |
| P9-SPEAK docs follow-up | `96155dbcfd58883a70ab42efb7b6c94ac015a518` | yes | this `main` tip |

### Phase 9 bookkeeping not named in the required table

These are on `main` after the build-plan merge. They record a track SHA or a Phase 9 progress note. They are not Phase 10 or VOICEPRE.

| SHA | Subject |
|---|---|
| `487f72ae4f591f984ceef45e69636b44a882b213` | docs: record P9-SUPERVISE implementation SHA |
| `00f60cd6584a30c947b4d38eb79497b99e9e9a46` | docs: record P9-SUPERVISE merge SHA |
| `58e4485ca7a32c2f77bf82843142fcee57337e11` | docs: record P9-FIX-TTS implementation SHA |
| `65a475d6ba1bc83eeed0b7b5e1c95b07e4779869` | docs: record P9-FIX-TTS merge SHA |
| `9b754f79a1dadf38bf0481ec68c1952c3fdab2cb` | docs: P9-SUPERVISE progress — TTS maintenance notes after closeout |
| `f8a8d62add62b0194e2867f039857d27f8f58525` | docs: record P9-STORE implementation SHA |
| `0bec3b7b8fa1d163e5ed947ef3589058d9aef178` | docs: record P9-STORE merge SHA |
| `7cdf4ca1b0ad111ed4f2fc3f7aa6778beb13f76f` | docs: record P9-WATCH implementation SHA |
| `661e1b4a9fbd2dfed3d2b2d82f327f7c4c6ed45b` | docs: record P9-WATCH merge SHA |
| `346f25ece7c7b6907bb70ea015edf583a413f40b` | docs: record P9-RANK implementation SHA |
| `cadc125127be2518ae7c0c10bf001494364d97f1` | docs: record P9-RANK merge SHA |
| `86726add6bd2108316ea53b73311829fad531cac` | docs: record P9-SURFACE implementation SHA |
| `03a3a1fac02a7b6c18b745e6ac3be43b2cd3b090` | docs: record P9-SURFACE merge SHA |
| `c1d7d8980aa392d7e764c7a11ee25e5f278871c5` | docs: record P9-SPEAK implementation SHA |

### Out of scope (G-NO-CROSS-SCOPE)

| SHA | Subject |
|---|---|
| `99c799d3d4cd542106279f5ba39c35220ee90e5f` | audit: P10PRE pre-build audit — old Android Zola companion salvage survey |
| `36782d874b75859d0707eb47932c9de7f0ed32dd` | audit: record P10PRE tip SHA |
| `f07ae366238e5b99df5d045b90d528fed831359a` | Merge branch 'audit/p10pre' |
| `69d2e7754801664c953e3df7baac6e7ba9096d4e` | audit: record P10PRE merge SHA |
| `543b36819e38704f815b6f77bed67f0228ebea79` | VOICEPRE standalone barge-in and wake-free voice feasibility. |
| `83167c2ba474feb1f207013c8406a4652cec60a9` | docs: record VOICEPRE audit content SHA |
| `4ef1fd983965a3545db41e645f8943a51aeb2ee6` | Merge branch 'voicepre-audit' |
| `c4ad6c96f09edfb56a88b3c59acbf56858889ebb` | docs: record VOICEPRE merge SHA |

### Lore files since the P8-LORE merge

P8-LORE merge: `c4ab94c7388d8e502339b99af1dd203d73470cfd`. Commits after it that touch `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`, or `identity/`:

| Commit | Files |
|---|---|
| `86b96a7d70af56744724e6b59fc3c7443829ede9` docs(P9-KICKOFF) | `OPEN_QUESTIONS.md`, `ROADMAP.md` |
| `bae7ac4874efff807204b977bb6dc0491d27b504` feat(P9-SURFACE) | `identity/SOUL.md` only |
| `20ea9aeffebabb632eb2b55fb5f36c1189fb514f` feat(P9-SPEAK) | `identity/SOUL.md` only |

`DESIGN_DECISIONS.md` has no commit since P8-LORE. Not BLOCKED.

### Lore structure

`DESIGN_DECISIONS.md` sections, in order: Client integration path; Scope / deferral; Provider / vendor; Security / hardening; Confirmed-action / authorization; Phase 2 — Voice; Phase 3 — Presence UI; Phase 4 — Conversation Safety and Voice; Phase 5 — Wake After Questions and Memory; Phase 6 — Memory She Lives With; Phase 7 — Voice She Can Trust; Phase 8 — Google Workspace, Inside a Boundary. Phase 8 ends with Annotations, execution notes, Known limits, and Process lessons. Phase 9 entries go in a new section after that: **Phase 9 — Proactive Foundation**.

`OPEN_QUESTIONS.md` is one section, "Research needed", as a single bullet list. Highest existing S-number: **S76**. New OQs continue from S77. Phase 9 status changes edit the existing bullets in place. The footer already records that S71–S76 were added, and S13, S55, S56, and S66 annotated, at P9-KICKOFF.

`ROADMAP.md` sections: Phases 1–8 complete, then "Current stage — Phase 9 (scope is Brian's call)", then Source documents. Phase 9 complete replaces that current-stage section. The one-line Phase 10 pointer goes after it.

### Open questions named for this task (scope only)

| ID | Scope |
|---|---|
| S13 | A Windows-viable path to read the user's own incoming SMS. Annotated at P9-KICKOFF; remains open. |
| S25 | HUD data sources. Each needs a real source first. |
| S36 | Bring back talk-over barge-in without breaking Phase 4. Feasibility gate was no. |
| S51 | Backend native crash, and no automatic recovery. Annotated at Phase 8 for one process death. |
| S54 | Whether `agent.execution_guidance` stays. Annotated at Phase 8; still open. |
| S55 | Streaming TTS bake-off. Annotated at P9-KICKOFF; not a decision. |
| S56 | Voice I/O ownership study. Brian kept the current path; the study stays available. |
| S66 | Proactive Workspace surfacing. Annotated at P9-KICKOFF; not a decision. |
| S68 | OAuth publishing. The app was in Testing. |
| S69 | Whole-message matches versus Hermes-injected text. |
| S70 | No voice playback-completion signal. |
| S71 | Open loops. Intake only. |
| S72 | Background agents and agent status. Intake only. |
| S73 | Android companion and distributed presence. Intake only. |
| S74 | Remote escalation by phone call. Intake only. |
| S75 | Speaker and face recognition as signals. Intake only. |
| S76 | Smart home: Kasa lights. Intake only. |

OQs filed at P8-LORE, from the footer ("S60–S70 added at Phase 8 lore closeout"): S60 Gmail triage actions; S61 calendar writes; S62 Gmail attachment content; S63 provenance-aware memory; S64 Office extraction; S65 an OS-level credential boundary; S66 proactive Workspace surfacing; S67 summary selectivity; S68 OAuth publishing; S69 whole-message matches versus Hermes-injected text; S70 voice playback-completion signal.

### Decision headings

| ID | Heading |
|---|---|
| Edge voice | `P2` — "TTS: Edge (free) for now; STT: local faster-whisper". Execution: `P2-D03` — "Spoken replies: Edge, default voice, on by default in Voice mode" (`en-US-AriaNeural`). Phase 4 supersedes the voice name inside that bullet: `P4-D19` — "Voice: `en-GB-SoniaNeural` at speed 1.1, provisional until a live trial" (live trial kept speed 0.95). Still Edge. |
| P2-D01 | Hermes owns the audio devices; the client drives voice over `/api/ws`. |
| P2-D02 | Speech-to-text is local faster-whisper, pinned explicitly. |
| P2-D17 | No automatic installs. |
| P4-D25 | Live profile edits are developer-approved, exact, and mirrored. |
| P6-D07 | P4 revised: memory local; no third-party memory service. |
| P6-D11 | Phase-track backups are deleted after merge. |
| P8-D02 | Application boundary, enforced where the code can. |
| P8-D03 | The OAuth app. |
| P8-D09 | Workspace content is evidence, not instruction. |
| P8-D11 | Privacy and logging. |
| S7 | Scheduled work: use Hermes cron. |

### Scratch folders

`p9*` folders: `p9-store` (68 files) and `p9pre` (1 file). Contents were not opened. Nothing was deleted.

`p9-store` includes two databases: `proactive_harness.db` (20,480 bytes) and `noticket\proactive.db` (61,440 bytes). No file name is `config.yaml`, a profile copy, or a backup of the live profile. Extensions: 60 `.py`, 3 `.txt`, 2 `.db`, 1 `.go`, 2 `.ready`.

| File | Bytes |
|---|---:|
| `p9-store\deploy_close.py` | 1871 |
| `p9-store\inspect_arm_cutoff.py` | 1706 |
| `p9-store\inspect_cleanup.py` | 17590 |
| `p9-store\inspect_cleanup.txt` | 15137 |
| `p9-store\inspect_hold_retrieve.py` | 1833 |
| `p9-store\inspect_l1.py` | 3049 |
| `p9-store\inspect_l1b.py` | 3178 |
| `p9-store\inspect_l1b_calls.py` | 873 |
| `p9-store\inspect_l1b_redo.py` | 625 |
| `p9-store\inspect_l1b_redo_log.py` | 912 |
| `p9-store\inspect_l1_logs.py` | 1270 |
| `p9-store\inspect_l1_window.py` | 1353 |
| `p9-store\inspect_l2.py` | 1396 |
| `p9-store\inspect_l2_api.py` | 607 |
| `p9-store\inspect_l2_log.py` | 753 |
| `p9-store\inspect_l2_match.py` | 1279 |
| `p9-store\inspect_l2_memlog.py` | 454 |
| `p9-store\inspect_l2_memory.py` | 597 |
| `p9-store\inspect_l2_msgs.py` | 754 |
| `p9-store\inspect_l2_pass.py` | 2123 |
| `p9-store\inspect_l2_retry.py` | 739 |
| `p9-store\inspect_l2_retry_all.py` | 831 |
| `p9-store\inspect_l2_retry_msgs.py` | 2040 |
| `p9-store\inspect_l2_taint.py` | 1393 |
| `p9-store\inspect_l2_wrapper.py` | 566 |
| `p9-store\inspect_l3.py` | 1742 |
| `p9-store\inspect_l3_tools.py` | 780 |
| `p9-store\inspect_l4.py` | 1563 |
| `p9-store\inspect_l4_line1.py` | 1143 |
| `p9-store\inspect_l4_line2.py` | 977 |
| `p9-store\inspect_l4_line3.py` | 2553 |
| `p9-store\inspect_l4_line3_action.py` | 931 |
| `p9-store\inspect_l4_line3_bridge.py` | 879 |
| `p9-store\inspect_l4_line4.py` | 1003 |
| `p9-store\inspect_l4_line5.py` | 1025 |
| `p9-store\inspect_l4_line6.py` | 916 |
| `p9-store\inspect_l4_offer.py` | 666 |
| `p9-store\inspect_l5.py` | 1981 |
| `p9-store\inspect_l5_gate.py` | 836 |
| `p9-store\inspect_l5_memlog.py` | 356 |
| `p9-store\inspect_l5_origin.py` | 1238 |
| `p9-store\inspect_l5_result.py` | 740 |
| `p9-store\inspect_l5_window.py` | 652 |
| `p9-store\inspect_memory_baseline.py` | 1574 |
| `p9-store\inspect_memory_md.py` | 439 |
| `p9-store\inspect_p8_source.py` | 1357 |
| `p9-store\inspect_r2_counts.py` | 2715 |
| `p9-store\inspect_r2_explain.py` | 8751 |
| `p9-store\inspect_reply_bool.py` | 2022 |
| `p9-store\inspect_reply_overlap.py` | 1592 |
| `p9-store\inspect_reply_schema.py` | 585 |
| `p9-store\inspect_restart.py` | 745 |
| `p9-store\inspect_retrieve_elapsed.py` | 758 |
| `p9-store\inspect_voice_window.py` | 1036 |
| `p9-store\l2_wrapper.txt` | 60 |
| `p9-store\l6_live.py` | 15827 |
| `p9-store\l6_result.txt` | 4184 |
| `p9-store\live_check_probe.py` | 1316 |
| `p9-store\memparse_ground.py` | 4448 |
| `p9-store\noticket_harness.py` | 2203 |
| `p9-store\proactive_harness.db` | 20480 |
| `p9-store\run_st_g8.py` | 4401 |
| `p9-store\schema_probe.py` | 1016 |
| `p9-store\st_g8.go` | 2 |
| `p9-store\st_g8.go.A.ready` | 5 |
| `p9-store\st_g8.go.B.ready` | 5 |
| `p9-store\st_g8_harness.py` | 6475 |
| `p9-store\noticket\proactive.db` | 61440 |
| `p9pre\h1\logs\zola_tools.log` | 4108 |

Other folders under `C:\Users\test\Dev\zola-spikes\`, not touched: `p10-transport`, `p3pre-helix`, `p4pre-voice`, `p5-lore`, `p5-memory`, `p5pre`, `p6-calc`, `p6-episodes`, `p6-fix-2`, `p6-fix-when`, `p6-forget`, `p6-store`, `p6-time`, `prompts`.

## Phase 2 — draft of DESIGN_DECISIONS.md (not applied)

Classification is above the draft text. `DESIGN_DECISIONS.md` was not edited. Nothing is committed.

### Classification

| Item | Where | Reason |
|---|---|---|
| Deepgram Aura-2 Pandora at 0.95, key file, guard rows | New **P9-D14** | Revises the Phase 4 Edge voice. A durable provider and secret-handling rule. |
| `urgent` never speaks unprompted (RK-G7 (c)) | Note under P9-D11 | Narrows the locked D11 sentence. Not a new rule. |
| Spoken-name provenance (SPEAK D5) | Note under P9-D11 | How the locked "Contacts name or someone" line is filled. |
| Retention narrowing (SPEAK D8) | Note under P9-D07 | Narrows locked D07. |
| `ranker_enabled`, `surface_enabled`, `speak_enabled`; missing means off; "should remain on" | Notes under P9-D08, P9-D10, P9-D11 | Enable switches for decisions already locked. |
| No follow-up listen after a proactive line (SPEAK D7) | Note under P9-D11 | Delivery behavior of D11. |
| Taint only when the returned text has mail fields (F10) | Note under P9-D10; annotation on P8-D09 | Narrows "taint first". No separate Brian quote was found for this sentence. |
| Code-written tell line outside the untrusted frame | Note under P9-D10 | How D10's injection is spoken. Brian approved the Phase 6 deviations as a set; the progress doc does not quote a separate sentence. |
| Acknowledge is not dismiss; only through the tool with a live handle | Note under P9-D10 | Track 5 mechanism for D10's "acknowledged". |
| Origin-loss fix | Note under P9-D01 | The ticket was already the authority. This is the repair. |
| Runtime allowlist; refresh mutex | Note under P9-D04 | How the locked fixed API is enforced. |
| Shared gateway and watcher-health contract files | Note under P9-D06 | Test mechanism for the store's client entry. |
| Brian's own sent mail stays out of the watcher | Note under P9-D05 | Consequence of the locked INBOX-only filter, as the watch progress doc records it. |
| Systems panel replaces the HEALTHY line | Note under P9-D12 | The locked HUD, as built. |
| MOCKUP label; stop only this track's processes by PID | Process lessons | How the work was done, not a product rule. |

### Draft text

## Phase 9 — Proactive Foundation

Recorded from `PHASE9_BUILD_PLAN.md` Appendix A (locked 2026-10-09), the progress docs `P9-KICKOFF`, `P9-FIX-ARM`, `P9-SUPERVISE`, `P9-FIX-TTS`, `P9-STORE`, `P9-WATCH`, `P9-RANK`, `P9-SURFACE`, and `P9-SPEAK`, and Appendix Q of the P9-LORE prompt. Appendix A governs where a summary differs. This section is the lore pointer, what shipped, the narrowings, and the measured limits.

**Brian's lock (verbatim, 2026-10-09):** "lock it".

**Scope (verbatim, 2026-10-09):** "I feel like this is limiting.  I get the slow approach, but why don't we build it all.  The proactive, the watcher, so it doesn't have to run when I ask. The information is already queued up.  The loops, the authority.  Let's just knock it all out systematically in one Phase." And: "That looks right.  SMS, phone call and talking to each agent can't happen yet.  A requirement for this phase is that I publish the app so that the background watcher can do it's job.  I think background ranking is a requirement.  I'll work on publishing the app while the audit runs."

**Answers (verbatim, 2026-10-09):** "I think the watcher should be able to read the full email and provide a gist.  It doesn't have to read the whole thing.  That could take forever." "1. a separate process 2. Yes, either my words, or Zola offers in turn 3. I agree.  I'm not sure if I like the same wording every time though.  We can work on some common phrases to add some variety. 4. Gmail can be every 2 minutes.  Calendar can be every 2hrs.  My calendar doesn't change that frequently throughout the course of a day. 5. I'll take your recommendation 6. OK 7. Yes" "1.  Agree on 10pm - 7am 2. OK"

### P9-D01 — Only code acts in the background

**As locked.** Polling, ranking, queueing, and delivery are Zola code. They are never a Hermes turn. Brian-only actions keep the P9-FIX-ARM client-origin ticket.

**P9-FIX-ARM, execution notes.** Brian (verbatim): "Let's do the hotfix." Choices, as relayed: "Option 1 via a runtime wrap of prompt.submit, no Hermes edit. Crash replay gets no Brian authority. Add the guard rows and drop the cronjob toolset as defense in depth. Bring zola_memory into scope." Smoke (verbatim): "done.  smoke test passed."

The wrap is around `_methods["prompt.submit"]`. A ticket is issued only when `_current_rpc_method` is `prompt.submit`, and never when the params carry a hosted task, a hosted terminal callback, or a delivery author. Crash replay gets no ticket. `cronjob` was dropped from `platform_toolsets.cli`. `zola_memory` is in scope. Residuals, as that progress doc records them: a still-live ticket can be consumed by another turn in the same session whose hooked text hashes equal; slash-command prompts, mid-turn steers, redirects, a merged busy-queue body, and an `@` expansion that changes the hooked text get no ticket; a command that does not name `state.db`, a copy of the database under another name, SQL through a tool other than `terminal`, `write_file`, or `patch`, and a `prompt.submit` forged on the local socket with the session token are not blocked.

**Origin-loss repair.** From the P9-FIX-ARM deploy on 2026-10-09 until the P9-STORE fix, `pre_llm_call` set the origin ContextVar on Hermes's timeout worker. That worker's context was discarded when the hook returned. The turn thread's turn id stayed empty. Episode retrieval returned nothing on client turns, forget holds did not arm, and `forget_memory` refused Brian. The last `forget_hold` line in that window is 2026-10-09 09:49. The repair looks up one unexpired sync permit whose text hash equals the message (`resolve_turn_from_permit`). The forget token is passed through `pre_tool_call`. Zero or several matches log `origin_unresolved` and fail closed. The Phase 5 scan for "no Hermes turn does proactive work" is recorded here when Phase 5 has run.

### P9-D02 — Backend supervision

**As locked, with Track 1 verdicts.** The client restarts `hermes serve` after an unexpected exit. Voice fails closed during the gap. Crash replay has no Brian authority. Serve stderr goes to a rotating, user-only log. WER local dumps for `python.exe` are a privacy decision: a dump can hold tokens and conversation text.

Brian's Track 1 verdicts, recorded verbatim from the Phase 4 proceed message (`P9-SUPERVISE_Progress.md`):

1. Restart policy: approved as proposed (3 in a rolling 10 minutes, 2 s backoff, quit and reopen clears KeepsFailing, tree-kill the previous generation before every spawn, smoke kills the CPython child).
2. Unreachable policy: approved with two changes.
   a. Fail closed on the first health failure, but declare "hung" and tree-kill only after HungHealthFailureLimit consecutive failed probes (3, about 20 s). Named constant.
   b. When reconnects are exhausted (5 attempts / 30 s) with health OK, tree-kill and restart, counting against RestartLimit. Do not leave that process running.
3. Generations: keep two counters. Process generation bumps on every spawn. Connection epoch bumps on every connectivity loss, including socket-only loss on the same process. Transcript admission, SubmitTurnAsync and clarify answers refuse anything from an earlier connection epoch. Both counters are thread-safe (Interlocked or equivalent); show where each is bumped and checked.
4. Gap behavior and status text: approved as proposed.
5. Crash replay: the recommended option. Resume the stored session, and set desktop.auto_continue.enabled: false in the live config.yaml exactly as shown, applied in Phase 6 with a backup.
6. Playback: approved. After a reconnect, restore the TTS state Brian had before the loss; do not force it on.
7. WER: approved as proposed (user + SYSTEM ACL, mini dumps, count 3, client prunes after 14 days). I will run the reg add commands myself.
8. Scratch crash test: approved as an exception to "never induce a native crash." One throwaway python.exe from the scratch folder only, report name/size/timestamp, then delete the dump.
9. stderr log: approved as proposed.
10. Tests: approved, linked into Zola.Client.Checks, no new packages. Add tests for 2a, 2b and 3.

Shipped: `RestartPolicy` is pure. `HungHealthFailureLimit` is 3, spaced by `HungProbeSpacingSeconds` 10. `RestartBackoffSeconds` is 2. The HKLM key `LocalDumps\python.exe` was read back as dump count 3, dump type 1 (mini), folder under the Zola client profile. The key covers every `python.exe` on the machine. Track 3 reuses `RestartPolicy` for the watcher and does not use `ProcessSupervisor`. That is an accepted deviation.

**WER folder, narrowed.** Appendix A: "a folder under Brian's profile readable only by him". Track 1 verdict 7: "WER: approved as proposed (user + SYSTEM ACL, mini dumps, count 3, client prunes after 14 days)." The closeout read-back is `NT AUTHORITY\SYSTEM:(OI)(CI)(F)` and Brian's user only (`P9-SUPERVISE_Progress.md`).

### P9-D03 — Watcher host

**As locked.** A separate process, `python -m zola_workspace.watcher`, started by the client, lifetime tied to the client, one instance (`Local\ZolaWatcher`). No model, no tools, no Hermes turn. Its own restart policy, 3 in 10 minutes. Job Object kill-on-close. If the job cannot be assigned, it watches the parent pid and exits. Brian's launch verdict was (a): with the client, independent of serve. The other option was after serve is ready, and keep running if serve later dies (`P9-WATCH_Progress.md`, question 10). Shipped: started from `App.OnLaunched`, not as a child of serve.

### P9-D04 — Background read authority

**As locked. Revises P8-D02.** A fixed read API used only by the watcher: Gmail history and a bounded message get; Calendar events with a sync token. No drafts, sends, Drive, Contacts, or any other Google operation from the watcher. Tool paths stay Brian-only. All content stays untrusted.

Shipped: the allowlist runs inside `google_http.request` when the background capability is passed. Tool calls omit it. Brian's verdict: "7. Allowlist: (a), inside google_http.request." The refresh POST takes `Local\ZolaOAuthRefresh`. A lock timeout or a local failure does not set `needs_reconnect`. A rotated refresh token in the response is ignored. That is Brian's verdict 8 (a), "per process, not persisted, rotated refresh token ignored" (`P9-WATCH_Progress.md` question 8 and the Phase 4 build line). It is a decided choice, not a residual. If Google returns a new refresh token, the store keeps the old one. Sender resolution is (a): address hash only. The watcher never calls Contacts. Brian: "3. Sender resolution: (a)."

### P9-D05 — Change detection and cadence

**As locked.** Gmail every 2 minutes (`GMAIL_POLL_SECONDS` 120). Calendar every 2 hours (`CALENDAR_POLL_SECONDS` 7200). A wall-clock jump triggers a catch-up. Gmail `history.list` is `messageAdded` in INBOX. A 404 takes a bounded resync. Calendar 410 writes a resync marker instead of clearing the cursor. Baseline sync creates zero items. An item is a new event first seen after the baseline, or a later cancel or status change that matches an open loop. The item key stays `calendar:<event id>:<updated>`. Brian: "1. Calendar model: (a), with one change. Keep the existing item idempotency key calendar:<event id>:<updated>; do not change it to calendar:<event id>. calendar_events holds known state (ids, status, times; no titles or people). An item is created only for (i) a new event first seen after the baseline, or (ii) a change that matches an open loop (cancelled or status change), and each such change is its own new item, so a cancellation of an already-delivered event can still be told and spoken. Baseline sync creates zero items. The items key needs no v3 change; the v3 migration adds calendar_events, watcher_rejects and the health columns only. Add a test: event created after baseline → item delivered → event cancelled with a loop open → a second, new item that is pending, then loop-eligible." The series-delete match is (a), a residual: no `recurringEventId` match. Recovery window 7 days. `getProfile` returns `historyId` only. A calendar id is percent-encoded (`quote(calendar_id, safe="")`). A segment that still contains `#`, `@`, or `/` is refused.

Brian's own sent mail is not watched, because it is not INBOX. The watch progress doc records that, and records a "Brian replied" signal as a possible later feature. Claude's Phase 5 fixes F1–F11, one line from that progress doc: a cycle exception stays in the process; transport errors, 429, and 5xx hold the cursor and do not count toward the poison cap; Gmail 404 recovery takes `historyId` before `messages.list` and skips mail older than the cursor time minus 120 seconds, using `internalDate`; calendar mode comes from the cursor; a 410 writes the resync marker; stdout and stderr are drained into a user-only log; the watcher calls `purge_retention` at start and on the purge interval.

Poison: `watcher_rejects`, cap 5. Brian: "6. Poison: (a), watcher_rejects, cap 5."

### P9-D06 — One proactive store

**As locked.** `proactive.db` (WAL) under the profile `proactive` directory, owned by `zola_workspace`, separate from memory. Items commit before the cursor advances. Claims are leases with an attempt id. A late completion for an old attempt changes nothing. `forget_memory` cascades into this store. The client does not open SQLite.

Schema, one line each: v1 the store; v2 `closed_intent`; v3 `calendar_events`, `watcher_rejects`, per-source health; v4 surface bookkeeping and `closed_reason`; v5 `loops.name_source` and the speech attempt columns. Live schema at the Track 6 closeout was 5.

Speech and surface attempts stay apart. Brian (SPEAK D18, verbatim): "keep them apart, no new column, with both cross-attempt tests." A confirmed surface note clears `items.attempt_id`. The claim blocks only while that id is set and `attempt_at` is inside 600 seconds.

Recovery. Brian (SPEAK D19, verbatim): "yes to recovery inside the claim transaction, once at coordinator startup, and in the hourly purge. Not on the snapshot: the snapshot stays read-only, because it runs every poll. Instead, surface runs the same recovery in its pre_llm_call before it selects, so the next note sees delivery_uncertain. Same transition function everywhere." Shipped amendment (P4-R2): recovery commits before the claim transaction, so a refused claim does not roll the recovery back.

Gateway methods: `proactive.snapshot`, `proactive.claim`, `proactive.speech_started`, `proactive.outcome`, `proactive.release`, `proactive.recover`, `proactive.watcher_health`. The names live in `contracts/proactive_methods.json` and `contracts/watcher_health.json`, asserted from the Python install and from the client gateway.

### P9-D07 — Retention, narrowed

**Locked wording.** Email body deleted right after ranking, or at 7 days if never ranked, then `content_expired`, never a silent row delete. Subject, snippet, and gist until delivered, 7 days at most, then ids and times only. Delivery history 30 days. Cursors carry no content.

**Narrowed wording (SPEAK D8).** Brian: "D8: yes." Delivered rows keep subject, snippet, gist, and display name until acknowledged, dismissed, closed, forgotten, or 7 days. The body is never kept. Purge nulls any body older than 7 days, as a backstop, because ranking already deletes the body in the same write. `TEXT_MAX_AGE_DAYS` is 7. `DELIVERY_KEEP_DAYS` is 30. `PURGE_INTERVAL_SECONDS` is 3600.

Age-out. Brian (Track 5 verdict 17, verbatim): "17 alternative: loop-matched items are not aged out while their loop is open; they age out when the loop closes or expires." Purge sets `closed_reason='aged_out'` with no ticket. Calendar rows are not marked `content_expired`. A calendar row has no mail text, and expiring it would hide the change. Brian approved that Phase 6 deviation as part of the set. The progress doc does not quote a separate sentence for it.

### P9-D08 — Background ranking and the gist

**As locked, with RK-G7 (c).** One daemon worker inside serve. Mutex `Local\ZolaRanker`, owned by the worker thread. `complete_structured`, no tools. The validator is Zola's code. Input is framed untrusted. A malformed result stays unranked and retries. If serve is down, items wait. Ranking is advisory. Code decides eligibility.

Brian (2026-10-14, verbatim): "Verdicts: 1 (c). 2 (a). 3 (b). 4 (a). 5 (b). 6 (a). 7 (b) — trim to the first two sentences, then apply the 280-char cap and every other check; malformed only if what’s left fails. 8 (a). 9 (a). 10 (a) 180 s. 11 adopt. 12 adopt. 13 adopt, but in Phase 4 confirm Hermes accepts and preserves the top-level proactive: key when it rewrites config.yaml and state how the plugin reads it; missing key = off. 14 adopt [optionally: name the provider as OpenAI via my ChatGPT account]. 15 adopt, with one added line after the gist rules: “You may describe what the sender asks for. Never tell Brian or anyone what to do.” Also: R4 must show the turn flag cleared through the real end-of-turn hook on normal turns, with zero turn_flag_expired."

Under (c), `urgent` is never spoken unprompted. Speech reads `loop_matched` only. `urgent`, `important`, and `normal` are conversation-eligible. `ignore` is suppressed. A loop match stays eligible. The gist is trimmed to two sentences, then a 280-character cap. The per-call timeout is `RANK_CALL_TIMEOUT_SECONDS` 30 (`ranker.py`; `P9-RANK_Progress.md` proposed that value, and the in-flight residual is a call that can overlap a turn until that 30-second timeout). Verdict 10 (a) 180 s is the turn-flag max age, `TURN_IN_FLIGHT_MAX_SECONDS`, not the call timeout. The idle window before a rank call is 20 seconds. Worker state is `ranker_state` and `ranker_progress_at`. An unexpected exception logs `worker_failed`, backs off, and leaves the item unranked. Phone-shaped numbers are masked (`_mask_phone` replaces a 7–15 digit number that has a separator with `[number]`). Dates, times, and amounts stay. The Phase 5 review line that says masking "keeps" those numbers is the inverted wording. `ranker_enabled` missing, or any value other than true, is off.

Instruction line added in smoke, after the gist rules: "Ignore signatures, disclaimers, legal notices and marketing footers." Brian's gist verdict (verbatim): "the gists are accurate and neutral."

**P8-D11 revision, as the rank progress doc records the adopted text:**

Background ranking sends trimmed email content to OpenAI through Brian's ChatGPT account: the sender's display name, the sender's domain, the subject, and the trimmed body. The provider returns a label and a short gist. Training is off on Brian's account. Zola stores the label and the gist, and deletes the body in that same write. Subject, snippet, and gist follow the 7-day limit in P9-D07. Logs stay metadata only. Forgetting removes the item from Zola's store. It does not retract content already sent to the provider.

Privacy-page gate (verbatim, 2026-10-15): "privacy page published". The privacy-plan file was not edited in that track.

Store defects D1–D5 from that track are fixed: a lease expiry writes nothing into the completion; a transient release does not count; the cap and the purge clear a body past 7 days; expired content is not claimed; close and forget refuse the completion.

### P9-D09 — Open loops

**As locked.** Created only on a ticket turn: Brian's words, or Zola offers and Brian says yes in his own turn. The close condition is a deterministic predicate, or "Brian confirms close". Matched is not closed. A lapse is told once. Listed by voice.

L5, as corrected in the store track: a topic is not an entity. The offer line in `SOUL.md`, approved by Track 5 verdict 19: "When Brian says he's waiting to hear back from someone or about something, I can offer once to watch for it. I don't repeat the offer." Ask before a self-selected close. The watch line: "When something I was watching for comes in, I tell Brian and ask whether he wants me to keep watching. I never stop watching on my own."

**Source-message fix (P9-SPEAK Phase 7).** A reply loop matched the message it was compiled from, because `after` compared the watcher insert time with loop creation. She said a reply had arrived when none had. The first K1 and K3 runs were invalid and were redone. Brian (verbatim): "That is a false unprompted announcement: she said a reply had arrived when none had. It is in scope as a Phase 7 deviation, because it directly breaks the speech this track delivers. Fix it before any further human step." Shipped: the compiled reply predicate refuses that message id (`not_source`). `after` uses the Gmail message's `internal_date`, or the calendar event's `event_updated`. A missing or unparseable time does not match.

### P9-D10 — Surfacing in conversation

**As locked, with Track 5 verdicts.** On the first ticket turn after a gap, a bounded block is injected. `whats_pending` works any time. Injecting is not telling. The store is the authority.

Brian (2026-10-16, recorded verbatim in `P9-SURFACE_Progress.md`):

1 yes. 2 yes. 3 600. 4 yes. 5 yes. 6 yes. 7 yes. 8 yes. 9 yes. 10 yes. 11 yes. 12 B. 13 yes. 14 yes, accept the residual collision. 15 yes. 16 yes.
17 alternative: loop-matched items are not aged out while their loop is open; they age out when the loop closes or expires.
18 yes.
19 offer, bounded: "When Brian says he's waiting to hear back from someone or about something, I can offer once to watch for it. I don't repeat the offer." Plus the other five SOUL lines as proposed.
20 yes. 21 yes.
22 option (a): bounded smoke-only config.yaml overrides, gap 120 s and quiet 300 s, backed up before, removed and hash-verified before closeout. Add the override keys with a floor so they can't be set to zero.
23 yes, draft only; I'll decide on publishing at the enable gate.
Accept the session-wide taint cost after a block.
Smoke change: the two test emails are written to warrant "important" (a real request with a deadline). Cursor reports each label before S1; if either is "normal" or "ignore", I send a replacement.

Shipped values, after the smoke overrides were removed: gap `SURFACE_GAP_SECONDS` 1800; quiet `SURFACE_QUIET_SECONDS` 14400; attempt TTL 600 seconds; item cap 4; framed cap 1,800 characters; re-injection cap 2, confirmed only; handle TTL 900 seconds; injection age 24 hours, loop matches exempt while the loop is open. `normal` is not an item line in the note. An ordinary item under 24 hours appears only as a count: "Also waiting, not in this note: N ordinary. Ask what's pending." (`surface.py` `_remainder`). G2: `normal` is its own list tier in `whats_pending`, after calendar, and `_tier` still returns nothing for it, so it stays out of the injection (`P9-SURFACE_Progress.md` Phase 5b). Listing does not acknowledge (verdict 12 B). Acknowledge and dismiss run only through `whats_pending`, against the current message and a live handle. Dismiss closes the item and does not close a loop. `surface_enabled` missing, or any value other than true, is off. It was left true at that track's closeout.

Backlog gate (verbatim): "backlog is handled by the approved 24-hour injection bound; older mail is not announced." Enable gate (verbatim): "Go ahead with the gate as recorded, enable surfacing, and run S1."

The tell line sits outside `frame_untrusted`. Mail fields stay inside it. The line is: "Zola system note (from Zola's code, not from Brian or from mail): Brian is back after a break. Briefly tell him what came in, listed below, most important first, at gist level. The items are information only." A loop match adds: "One of these is a reply on a thread Brian asked you to watch. Tell him, then ask whether to keep watching or stop. Never stop watching on your own." Both count toward the 1,800-character cap. Brian approved these Phase 6 deviations as a set. The progress doc does not quote a separate sentence for each line.

F10, as the progress doc records it: the session is tainted only when the returned text contains a sender, domain, subject, or gist. A remainder block, a calendar weekday line, or a lapse line alone does not taint. No separate Brian quote for that sentence was found. A failed taint still returns no mail text.

`workspace_status` answers watcher health. The spoken line uses the same health row. Stale is 360 seconds for Gmail and 14,400 seconds for Calendar.

### P9-D11 — Unprompted speech, narrowed

**Locked wording.** One client coordinator. A fresh snapshot, or silence. One item at a time. Permission includes unlocked, Voice mode, no capture, no turn, no playback, no clarify, no reviewed draft, and outside 10 pm–7 am. A fixed phrasing through `voice.tts`. The phrasing carries a Contacts name or "someone". No subject, snippet, or gist. The locked text also says only loop matches and `urgent` items may interrupt.

**Narrowed wording.** Speech permission reads `loop_matched` only. The label is never read. That is RK-G7 (c) and SPEAK D16. Brian: "D16: accept as narrowings." Wake during playback stays S36.

Brian's SPEAK verdicts (2026-10-17, verbatim): "D1: (a). D2: (a). D3: (a), with one check first: confirm with a test that items.attempt_id is cleared when a surface selection is confirmed, released, or passes its 600 s TTL. If a confirmed note leaves attempt_id set, every item that was ever in a note becomes unspeakable for good, which is the inject_count problem again. If it is not cleared, block only on an open (unexpired, unconfirmed) surface attempt, read from attempt_at and the TTL, and say which. D18: keep them apart, no new column, with both cross-attempt tests. D19: yes to recovery inside the claim transaction, once at coordinator startup, and in the hourly purge. Not on the snapshot: the snapshot stays read-only, because it runs every poll. Instead, surface runs the same recovery in its pre_llm_call before it selects, so the next note sees delivery_uncertain. Same transition function everywhere. D4: yes, these stamps, 20 s and 20 s. D5: (b). D6: the draft, plus a separate no-name Gmail set used when the name is "someone" (all six existing loops will be): "Brian, the reply you were waiting for just came in." / "Heads up, you've got the reply you were watching for." / "That email you were waiting on, they wrote back." Do not put "someone" into the named lines. D7: (a). D8: yes. D9: (i) and (ii), 2 s tail. D10: yes. D11: yes, locked. D12: (b). Document in the progress doc that for up to 360 s the HUD can say "watcher stopped" while her spoken answer is still healthy. D13: both. D14: off. Enabling for the smoke is decided at the Phase 6 STOP. D15: that line. D16: accept as narrowings. D17: yes. D21: yes."

Name (D5 (b)): from Brian's own message, or a Contacts lookup on a ticket turn. Never from mail. Otherwise the no-name set. Do not put "someone" into the named lines.

Idle since the last interaction and idle since the last speech bout are each 20 seconds (D4). Neither figure is the poll. The poll is `SPEECH_POLL_SECONDS` 20 (`SpeechConstants.PollSeconds`). A proactive line does not open a follow-up listen (D7 (a)).

Echo, three separate items:

- (i) The proactive-line guard as shipped (D9): the exact phrase is in the haystack, a capture that starts while the line is queued, playing, or inside a 2 second tail is refused, and push-to-talk cancels the line first.
- (ii) The tail-restart defect: `NoteCompleted` ran on every bout stop, so each ordinary reply restarted the 2 second tail and follow-up was refused `reason=echo`. Brian (verbatim, `P9-SPEAK_Progress.md`): "follow up isn't working. I have to hit the Mic button for each response." `NoteCompleted` now runs only when the proactive attempt ends.
- (iii) The ordinary-reply echo, the one that can turn her own speech into a ticketed Brian turn, is still an accepted risk. Brian (verbatim, 2026-10-13, Appendix Q): "I'll take the risk.  We aren't in production yet.  We will keep that in the future release.  Let' move to Track 3."

Cancel (D10): push-to-talk, typing, a submit, Stop speaking, a turn starting, and a wake word detected before audio starts. Before start is recorded, the claim is released. After that, playback stops and the outcome is `delivery_uncertain`. K7 met for the store outcome through the mic button, not through the wake word the plan named. Attempt `a85996c0f7828952` ended `delivery_uncertain`, reason `cancelled_by_push_to_talk`, and was not re-spoken. Stop and Cancel are not shown during a proactive line. The mic is the interrupt. Observation (`P9-SPEAK_Progress.md` Phase 7): "Stop and cancel were not present. This time I tried clicking the mic button while she was speaking. I may have done it too late." Acceptance (Appendix Q, Track 6 working chat, 2026-10-19): "I don't need this fix.  I'm good with them not being available.  It was an observation and Cursor explained.  We are good to closeout."

Quiet hours are 22:00–07:00 local (D11). At 07:00 an item speaks only if `detected_at` is still inside `SPEECH_MAX_AGE_SECONDS` (7200).

Evidence (D17): accepted, started, and completed are separate. `delivered` requires evidenced completion of the same attempt. Idle is not completion. Uncertain speech is not spoken again.

Proactive calls use a 2 second timeout (D20). The default RPC timeout stays 45 seconds. `speak_enabled` missing, or any value other than true, is off. Brian, at the Track 6 closeout (`P9-SPEAK_Progress.md` Phase 8): "speak enabled should remain on." The live file was left true.

An accepted proactive line is shown as a Zola bubble in the live conversation list. Brian (verbatim): "Tested and now the proactive speech shows in the conversation." The line is not written into the stored session. A resume rebuilds the list without it. Earlier lines are not backfilled.

`SOUL.md` D15, as shipped: "When I have just told Brian out loud that someone got back to him, a follow-up about what they said uses that note or what's pending. I open the mail only if he asks."

Accepted Phase 5 residuals, no code change: a stamp after `speech_started` and before dispatch records `delivery_uncertain` for a line that was never sent; push-to-talk while `voice.tts` is in flight can let audio begin for up to the 2 second call bound; the proactive phrase replaces the last-reply echo haystack, and a proactive line is dispatched only after 20 seconds of idle.

K4's quiet hours, reviewed draft, locked PC, and serve-unreachable snapshot were harness-only. Text mode was run live.

### P9-D12 — HUD and spoken status, narrowed

**Locked wording.** The client shows healthy, degraded, needs reconnect, or unknown from the watcher's last poll and error class, and computes staleness itself. "How's the watcher?" uses the same data.

**Narrowed wording (SPEAK D12 (b), and D16).** `degraded` at 360 seconds. `unknown` only when there is no row or no fresh snapshot. For up to 360 seconds the HUD can say the watcher stopped while the spoken answer is still healthy. Brian: "D12: (b). Document in the progress doc that for up to 360 s the HUD can say "watcher stopped" while her spoken answer is still healthy."

The Systems panel replaced the single HEALTHY line. Brian (Appendix Q, Track 6 working chat, 2026-10-17): "I noticed that there is now a health status in the Hud. This is not what I intended. I was thinking more like the left panel in the Android app." On the rows: "It should only be what is intended for Zola Windows (workspace watcher or something like that, companion watcher or something like that, backend, memory.) Any others you can think of?" "At some point, I may want to change the wording of some of these, but for now it is a go." On colour: "One thing that we might want to add is a color change for any status that needs attention.  Maybe red when it is down."

Shipped rows: Backend, Workspace watcher, Google account, Ranking, Voice. Memory has no health signal, so no row. The Companion watcher row waits for Phase 10. Colour is keyed by row and state. Attention is gold `#FFE7A5` (`ZolaAlertGlow`). Down is red `#D9534F` (`ZolaError`). Ranking `UNAVAILABLE` is Attention. Voice `UNAVAILABLE` is Down. Live `needs_reconnect` on that panel was not produced. The live token was not touched.

The progress doc's Phase 7 deviation is a paraphrase of these quotes, not a second source.

### P9-D13 — Track order

**As locked.** Supervision, store, watcher, ranking, surfacing, speech and HUD, then this lore closeout. P9-FIX-TTS ran between Tracks 1 and 2 as maintenance. It is not a seventh product track.

### P9-D14 — Voice is Deepgram Aura-2 Pandora

**New. Revises `P2` / `P2-D03` / `P4-D19`.** Those entries set Edge. `P2-D03` records `en-US-AriaNeural`, then annotates: "spoken voice superseded — `en-GB-SoniaNeural` at speed 0.95 (was Aria / provisional Sonia 1.1)." `P4-D19`'s heading is "Voice: `en-GB-SoniaNeural` at speed 1.1, provisional until a live trial." The next sentence is "Live trial rejected 1.1; blind speed A/B picked **0.95**." Neither entry records +10%. The live voice is no longer Edge.

Brian (verbatim): "I used Deepgram for the Android client.  Could we just use that? I really liked the Thalia voice." "I don't know that this is the right Thalia voice.  This one is american and the one that I liked was South African.  I think it was from Cartesia maybe.  There  is also the idea of Flux TTS from Deepgram." "I will stick with Deepgram for now though because I have a ton of credits.  I would just want to change to a different voice.  Something a bit deeper and slower paced." "Pandora is the voice I would like" "She feels a bit too slow and a bit too deep.  Perhaps we should try 1.0" "1.0 was too fast.  I bumped it to .95.  I think we will stay there."

Live settings, from the profile config recorded in `P9-FIX-TTS_Progress.md`: provider Deepgram, model `aura-2-pandora-en`, speed 0.95. The key file is named `deepgram_api_key`. The guard names the folder `%LOCALAPPDATA%\ZolaClient\secrets`. Contents were not read. That progress doc does not record an ACL read-back. The key is not in `.env`. No key value is recorded here. Guard rows from that hotfix stay. The secrets row blocks `terminal`, `read_file`, `write_file`, and `patch` when the path matches that folder or the file name. The second row, `profiles[/\\]+zola[/\\]+zola-tts`, blocks `write_file`, `patch`, and `terminal`. `read_file` of that folder stays allowed (`P9-FIX-TTS_Progress.md`). `execute_code` is not in either list. `VOICE_CONFIG.md` still documents Edge. Replacing it is a Phase 5 proposal, applied only if Brian approves the text.

Voice quality, deferred (verbatim, 2026-10-13): "Speech is working.  I think we have some tightening to to on timing, prosody and emotion.  She sounds more robotic than on Edge.  We can tackle that later though."

### Annotations on earlier entries

- **P8-D02.** Revised by P9-D04: the watcher has a fixed background read. Revised by P9-FIX-ARM: Brian-only means the client-origin ticket, not `platform == "tui"` and an empty `parent_session_id`.
- **P8-D03.** The Testing deviation ended. Brian (verbatim, 2026-10-09): "Okay.  We are "In production".  Audit is still running." The Testing-era refresh token expired, as AUD-14 predicted. Setup was re-run 2026-10-16. The new token is under "In production".
- **P8-D09.** Injected surfacing still taints before the model sees mail text (P9-D10). F10 narrows that to a returned block that contains a sender, domain, subject, or gist.
- **P8-D11.** Revised by P9-D08. The adopted paragraph is under P9-D08.
- **P2-D01.** Unchanged. Proactive speech uses the client's own `voice.tts` path.
- **P2-D17.** No Phase 9 package install is claimed here. Phase 5 confirms it.
- **S7.** Proactive work does not use Hermes cron (P9-D01). `cronjob` was also dropped from the cli toolset (P9-FIX-ARM).

### Named constants

Values are the ones the progress docs record. The decision column names the source. Phase 5 checks each against the code on `main` and records the file. A mismatch is reported there, not corrected here.

| Name | Value | Decision |
|---|---|---|
| `RestartLimit` / window | 3 in 10 minutes | P9-D02 |
| `RestartBackoffSeconds` | 2 | P9-D02 |
| `HungHealthFailureLimit` | 3 | P9-D02 |
| `HungProbeSpacingSeconds` | 10 | P9-D02 |
| Reconnect exhaustion | 5 attempts or 30 s | P9-D02 |
| WER dump count / type / prune | 3 / mini / 14 days | P9-D02 |
| `GMAIL_POLL_SECONDS` | 120 | P9-D05 |
| `CALENDAR_POLL_SECONDS` | 7200 | P9-D05 |
| Gmail stale / Calendar stale | 360 / 14400 | P9-D12 |
| `POISON_ATTEMPT_CAP` | 5 | P9-D05 |
| `GMAIL_RECOVERY_MARGIN_SECONDS` | 120 | P9-D05 |
| `RANK_LEASE_SECONDS` | 120 | P9-D08 |
| `RANK_CALL_TIMEOUT_SECONDS` | 30 | P9-D08 |
| `TURN_IN_FLIGHT_MAX_SECONDS` | 180 | P9-D08 |
| Rank idle window | 20 s | P9-D08 |
| `SPEECH_CLAIM_LEASE_SECONDS` | 30 | P9-D06 |
| `SPEECH_OUTCOME_LEASE_SECONDS` | 120 | P9-D06 |
| `SPEECH_MAX_AGE_SECONDS` | 7200 | P9-D11 |
| Idle since last interaction / last speech bout | 20 s / 20 s | P9-D11 |
| `SPEECH_POLL_SECONDS` | 20 | P9-D11 |
| Quiet hours | 22:00–07:00 local | P9-D11 |
| `SPEECH_ECHO_TAIL_SECONDS` | 2 | P9-D11 |
| Proactive RPC timeout | 2 s | P9-D11 |
| `SPEECH_START_TIMEOUT_SECONDS` | 15 | P9-D11 |
| `SPEECH_COMPLETE_TIMEOUT_SECONDS` | 60 | P9-D11 |
| Reservation lock bound | 50 ms | P9-D11 |
| `POST_SPEECH_WINDOW_SECONDS` | 900 | P9-D11 |
| `BODY_MAX_AGE_DAYS` / `TEXT_MAX_AGE_DAYS` | 7 / 7 | P9-D07 |
| `DELIVERY_KEEP_DAYS` | 30 | P9-D07 |
| `PURGE_INTERVAL_SECONDS` | 3600 | P9-D07 |
| `SURFACE_GAP_SECONDS` | 1800 | P9-D10 |
| `SURFACE_QUIET_SECONDS` | 14400 | P9-D10 |
| Surface attempt TTL | 600 s | P9-D10 |
| Surface item cap / character cap | 4 / 1800 | P9-D10 |
| Re-injection cap | 2, confirmed only | P9-D10 |
| Handle TTL | 900 s | P9-D10 |
| Injection age | 24 h, loop matches exempt while open | P9-D10 |
| Body trim cap | 4000 characters | P9-D04 / P9-D08 |
| Gist cap | 280 characters, two sentences first | P9-D08 |

Gateway methods are the seven names under P9-D06. Deny reasons recorded for speech: `speak_disabled`, `locked`, `suspended`, `text_mode`, `capture`, `turn`, `playback`, `clarify`, `reviewed_draft`, `quiet_hours`, `snapshot_stale`, `snapshot_timeout`, `backend_down`, `reservation_lost`, `one_at_a_time`. The client log line is `proactive.deliver` with attempt hash, outcome, reason, phrase index, and `name_source`. No name and no mail text. Live flags at the Track 6 closeout: `ranker_enabled` true, `surface_enabled` true, `speak_enabled` true.

### Known limits

- The ordinary-reply echo remains an accepted risk (Appendix Q, 2026-10-13). Track 6 closed the echo for the proactive line only (`P9-SPEAK_Progress.md`).
- K7 met on the mic button. The wake-word path in the plan was not the path that met it. Stop and Cancel stay hidden during a proactive line. Brian (Appendix Q, Track 6 working chat, 2026-10-19): "I don't need this fix.  I'm good with them not being available.  It was an observation and Cursor explained.  We are good to closeout." (`P9-SPEAK_Progress.md` records the store outcome; it does not contain this sentence.)
- The conversation bubble is not stored. A resume rebuilds the list without it (`P9-SPEAK_Progress.md`).
- K4 quiet hours, reviewed draft, locked PC, and a serve-unreachable snapshot are harness-only (`P9-SPEAK_Progress.md`).
- Live `needs_reconnect` on the Systems panel was not produced (`P9-SPEAK_Progress.md`).
- No live capture was attempted inside a proactive tail, so the echo refusal line was not produced live (`P9-SPEAK_Progress.md`).
- The false unprompted announcement happened, and was fixed in the track. The first K1 and K3 runs do not count (`P9-SPEAK_Progress.md`).
- The origin ticket failed silently from the 2026-10-09 deploy until the P9-STORE fix (`P9-STORE_Progress.md`).
- The Testing-era token expired. For about two days the watcher held `needs_reconnect` while Zola answered "connected" from the local token check. Setup on 2026-10-16, then polling resumed, is the live proof (`P9-RANK_Progress.md`).
- Painted screenshots were Pillow composites. Brian (verbatim, `P9-SPEAK_Progress.md`): "Cursor was incorrect. The live window did not reflect the change. I closed it and restarted it and it still does not reflect the change." A later capture of the running Debug client is the panel evidence.
- Stale and needs-reconnect watcher wording was proven in scratch only, and was never heard live (`P9-SURFACE_Progress.md` S11).
- `needs_reconnect` resume was unit-tested in Track 3 (`P9-WATCH_Progress.md`: the resume path did not occur live). The 2026-10-16 re-setup proved it live (`P9-RANK_Progress.md`: setup wrote a new token, and the next cycle polled).
- An in-flight ranking call cannot be cancelled at the pin. It overlapped a live turn once: Track 4 R4, turn 6 began while load 7's call was still running (`P9-RANK_Progress.md`).
- Forget-by-person misses an address known only in Contacts (`P9-WATCH_Progress.md`: a scratch row whose address was not a memory alias remained).
- A shell stopped every listener on TCP 8765 and killed the P10 transport listener. The rule adopted: stop only processes this track started, by PID. Zola serve uses `--port 0`. It does not share 8765 (`P9-SPEAK_Progress.md`).
- `forget_subject` redacts, and does not delete, a row whose delivery is `claimed`, `speech_started`, or `delivery_uncertain`. No store function deletes a closed loop (`P9-SPEAK_Progress.md` closeout; the rule is in the store).
- Confirmed notes are sometimes not spoken on a short greeting. Twenty-two real items reached `inject_count` 2 during the Track 5 smoke (`P9-SURFACE_Progress.md`).
- The 24-hour injection bound uses `detected_at`, not the message's own received time (`P9-SURFACE_Progress.md`).
- Hermes logs an 80-character preview of every user message to `agent.log`. This phase does not edit Hermes (`P9-SURFACE_Progress.md`).
- At 900×640 the top-right VOICE / MIC lines overlap her hair. That predates Track 6 (`P9-SPEAK_Progress.md`).

### Process lessons

- A fail-closed gate has to fail loudly. The origin ticket failed for days with empty retrieves. A client poll returned before the HUD and the log. `reservation_lost` hid three different causes.
- A test that passes only against a fake gateway is not integration evidence. The shared method-name contract caught that class. Session checks found order and race defects that policy checks did not.
- Retrying a smoke step until it passes is not proof. The failing check comes first.
- "After" is the source system's own timestamp, not the time we ingested the row.
- Claude's own G-POISON wording ("transient past the cap becomes terminal") would have dropped real mail during a 10-minute outage (`PHASE9_TRACK_LOG.md`). The fix, recorded as F2 in `P9-WATCH_Progress.md` Phase 5, is never to cap transient errors.
- The model does not act on text it was told to treat as data. The tell line had to sit outside the frame.
- Tool routing uses the first words of a tool description. The deferred catalog clips at about 60 characters.
- `time.monotonic()` ticks about 15.6 ms on Windows. Python durations use `perf_counter`.
- Dry-run the selection before a live step whose result depends on what will be selected.
- Smoke the build Brian runs (`dotnet run`, Debug), and check the process tree after every restart.
- Anything that is not an unedited capture of the running client is labelled MOCKUP.
- Stop only processes this track started, and stop them by PID.
- Claude's reviews, cited to `PHASE9_TRACK_LOG.md` except the Track 2 line, which that progress doc names itself. Track 2, `P9-STORE_Progress.md` Phase 5, "Claude's read of the store, loops, and recorded results": a loop belongs to Brian, not to a session; listing a loop taints the session and frames the display name and subject; closing or expiring a loop nulls that text. Track 3, `P9-WATCH_Progress.md` Phase 5: a cycle exception must never kill the watcher (F1); transport, 429, and 5xx must never become terminal (F2). Track 4, `P9-RANK_Progress.md` Phase 5 ("Brian's fixes A–H"): a worker must not die silently (A); a provider 4xx is a per-item rejection, so one bad item does not block the queue (B). Track 5, `P9-SURFACE_Progress.md` Phase 5: a count-only note was never confirmed, so it repeated every turn (F1); the `possibly_surfaced` detector was inverted (F4). Tracks 1 and 6: no line.

Phase 2 revisions are in the draft above. `DESIGN_DECISIONS.md` was not edited.

## Phase 3 — draft of OPEN_QUESTIONS.md (not applied)

`OPEN_QUESTIONS.md` was not edited. New numbers continue from S76. Nothing below is committed.

### G-RESOLVED

| ID | Original scope | Proposed status | Why |
|---|---|---|---|
| S51 | Native APPCRASH with no recovery: find the cause, persist stderr, enable WER dumps, and have the client respawn serve. | RESOLVED in part | Restart, fail-closed gap, stderr, and WER dumps shipped (P9-D02). The crash cause stays open. A natural-dump count is a Phase 5 listing, not read here. |
| S66 | Push, webhooks, and email or calendar raised without a question. | RESOLVED in part | Tracks 3–6 ship polling, ranking, surfacing, and unprompted speech for a loop match. Pub/Sub and push stay open. Evidence: K1 redo, K2, K5. |
| S68 | The app is in Testing, so refresh tokens last about seven days until it is published. | RESOLVED | Published In production 2026-10-09. The Testing token then expired. Setup on 2026-10-16, then polling resumed. |
| S71 | A real record behind a watch: which store, how it closes, how she lists it. | RESOLVED | `proactive.db` owns loops (Track 2). Close is a predicate or Brian confirms. `whats_pending` lists them (Track 5). |
| S72 | Background agents in the left HUD, verbal status, and direct conversation with each, all by voice. | Partly | Watcher status is on the Systems panel and by voice. Per-agent voices and direct conversations remain. The Companion watcher row waits for Phase 10. |
| S25 | HUD fields need a real source. | Annotate | Watcher health is the first real HUD source, on the Systems panel. The other fields stay open. |
| S36 | Talk-over barge-in, upstream-gated. | Annotate | Wake during playback remains. The 2026-10-12 deferral covers barge-in. Changing the TTS provider does not restore it. |
| S56 | Whether Zola should own voice I/O. | Annotate | The speech-pipeline options include client-owned speech, which would give one owner for voice I/O. |
| S69 | The interrupted-turn note a crash replay put in front of a replayed message. | Annotate | `desktop.auto_continue.enabled: false` means that replay no longer runs a model turn. Another path for the note is not established. Prefix matching stays open. |
| S70 | No playback-completion signal; a cut-off read-back still counts as reviewed. | Annotate | Proactive delivery uses the playback monitor's completion. There is still no serve-side signal. |
| S60–S65, S67 | Workspace expansions, provenance, Office, an OS credential boundary, summary selectivity. | No change | No Phase 9 progress doc answers them. |
| S13, S55, S73, S74, S75, S76 | SMS, streaming bake-off, the companion, phone escalation, recognition, Kasa. | No change | No Phase 9 progress doc answers them. S55 stays a bake-off: P9-D14 picks a command-provider voice and does not answer streaming. S73 is not annotated from Phase 10. |

### Annotations to append

**S51.** **Phase 9 (P9-D02): RESOLVED in part.** The client restarts `hermes serve` after an unexpected exit, voice fails closed in the gap, stderr goes to a rotating log, and WER local dumps are on. Original remainder: the native crash cause. Dumps are captured. Whether any natural dump has landed since Track 1 is a Phase 5 folder listing (names, sizes, dates only; a dump is never opened). Not read in this phase.

**S66.** **Phase 9: RESOLVED in part.** Original scope: push, webhooks, and email or calendar raised without a question. Shipped: the watcher polls (Gmail 2 minutes, Calendar 2 hours), ranking writes a gist, a gap note surfaces in conversation, and a loop match is spoken unprompted. Pub/Sub and Calendar push stay deferred. Evidence: K1 redo spoke item `e148f77c0dcd254a` (`delivered`) after the source message was refused; K2 held speech through an active conversation and delivered after idle; K5 left item `532281269e52d06e` `delivery_uncertain` and did not speak it again.

**S68.** **Phase 9: RESOLVED.** Original scope: the app is in Testing, so refresh tokens last about seven days until it is published. Brian (verbatim, 2026-10-09): "Okay.  We are "In production".  Audit is still running." The Testing-era token then expired, as AUD-14 predicted. Setup was re-run 2026-10-16. `needs_reconnect`, then setup, then polling resumed, is proven live (`P9-RANK_Progress.md`).

**S71.** **Phase 9: RESOLVED.** Original scope: which store owns a loop, how it closes, and how she lists it. `proactive.db` is the store (Track 2). Close is a deterministic predicate or "Brian confirms close". `whats_pending` lists open loops (Track 5). A matched loop is not closed by the match.

**S72.** **Phase 9: partly.** Original scope includes agents in the left HUD and a spoken status, plus talking to each agent. The workspace watcher has a Systems-panel row and a spoken health sentence from the same row. Per-agent voices and direct conversations remain. The Companion watcher row waits for Phase 10.

**S25.** **Phase 9 annotation.** Watcher health is the first real HUD source. It is the Systems panel (P9-D12), not a guessed Attention or Core Systems value. The other fields in this question stay open.

**S36.** **Phase 9 annotation.** Wake during playback remains (`voice.barge_in` stays false). The mic button and Stop speaking are the interim interrupts. P9-SUPERVISE N2a: a wake during speech did nothing and she kept talking. P9-SPEAK K7 met on the mic button, not on the wake word. A wake was ignored once as a follow-up phrase (`wake ignored: follow-up phrase=hey zola`, `P9-SPEAK_Progress.md`). Brian (Appendix Q, 2026-10-12): "I would rather wait and do this later. We've already gone off track with P9. Let's finish what we started and document this in lore for follow up in a later phase." That deferral covers barge-in as well as latency. Changing the TTS provider does not restore barge-in.

**S56.** **Phase 9 annotation.** The speech-pipeline options include client-owned speech (S77), which would give one owner for voice I/O. The study itself is not decided.

**S69.** **Phase 9 annotation.** The original question is the interrupted-turn note that a crash replay put in front of a replayed message, which then failed a whole-message match. `desktop.auto_continue.enabled: false` turns that replay off (`P9-FIX-ARM_Progress.md`): the replay that produced the note no longer runs a model turn. Whether the note can still appear by another path is not established. Matching against a known Hermes prefix stays open.

**S70.** **Phase 9 annotation.** Unprompted delivery uses the playback monitor's completion of the same attempt (P9-D11). There is still no serve-side playback-completion signal. A cut-off read-back can still count as reviewed.

### New questions

- **S77 — Speech pipeline.** Latency, sentence gaps, timing, prosody, emotion, and the root cause of the ordinary-reply echo. Brian (Appendix Q, 2026-10-13): "Speech is working.  I think we have some tightening to to on timing, prosody and emotion.  She sounds more robotic than on Edge.  We can tackle that later though." Deferrals (Appendix Q): "I would rather wait and do this later. We've already gone off track with P9. Let's finish what we started and document this in lore for follow up in a later phase." And: "I think there may be something bigger to fix here.  In Android, speech started a lot closer to text using deepgram, so she didn't wait so long to start speaking.  We also didn't have big gaps in speech.  Perhaps there is some tuning that we can do there altogether." Then: "It feels like this is larger than a hotfix that goes into P9.  Perhaps we document this for a later phase and finish up P9." `P9-FIX-TTS_Progress.md` does not record these timings. `PHASE9_TRACK_LOG.md` (2026-10-12) records submit to first audio at about 4.6 s on a simple turn and about 16 s on a tool turn. The follow-up release rule is bout stop plus 0.5 s quiet (`P9-SPEAK_Progress.md`). That quiet is shorter than the multi-second gaps between sentences. That is the suspected path by which the echo became a Brian turn (`PHASE9_TRACK_LOG.md`). Working hypothesis: a per-sentence command provider. Options: (a) trims, (b) a streaming TTSProvider plugin, (c) client-owned speech. Design rule: speed is not the safety mechanism. The ordinary-reply echo stays an accepted risk. Brian (Appendix Q, 2026-10-13): "I'll take the risk.  We aren't in production yet.  We will keep that in the future release.  Let' move to Track 3." Open inside K7: whether cancelling a proactive line can close Brian's capture. The cancel uses the outage-kill path. At 07:18 the capture opened and closed with no transcript (`P9-SPEAK_Progress.md`). The proactive phrase replaces the last-reply echo haystack. Push-to-talk during an in-flight `voice.tts` can let up to about 2 seconds of audio start. See the standalone VOICEPRE audit.

- **S78 — TTS provider resilience.** Hermes has no automatic TTS fallback (`P9-FIX-TTS_Progress.md`: a command provider does not call the builtin engine). Edge has returned HTTP 403 since 2026-10-10 (`rany2/edge-tts` #490), recorded in the Track 1 maintenance note (`P9-SUPERVISE_Progress.md` closeout). `P9-FIX-TTS_Progress.md` does not record that date or that issue. The Voice row now shows the outage (P9-D12, Down). The voice Brian originally remembered (Cartesia) was not pursued (Appendix Q, the Thalia comparison).

- **S79 — Secrets and guard coverage.** `DEEPGRAM_API_KEY`-style names are not on Hermes's secret blocklist. The key lives in a file instead (`P9-FIX-TTS_Progress.md`). The P8 guard rows do not check `execute_code`: Google terminal, self-modification, and schedule (`P9-FIX-TTS_Progress.md` lore closeout). `execute_code` is off the live `cli` list. The `delegation` toolset's sub-agent tools against those guards is unexamined.

- **S80 — P9-FIX-ARM residuals.** A still-live ticket can be consumed by another turn in the same session whose hooked text hashes equal. Slash-command prompts, mid-turn steers, redirects, a merged busy-queue body, and an `@` expansion get no ticket. A command that does not name `state.db`, a copy of the database, SQL through a tool other than `terminal`, `write_file`, or `patch`, and a `prompt.submit` forged on the local socket are not blocked (`P9-FIX-ARM_Progress.md`).

- **S81 — Ranking throughput and cancellation.** Catch-up after an outage: claim order, the idle rate, code-labelled bulk mail, a separate model route, or a local model. An in-flight `complete_structured` call cannot be cancelled at the pin. It overlapped one live turn: Track 4 R4, turn 6 began while load 7's call was still running (`P9-RANK_Progress.md`).

- **S82 — Urgent unprompted speech.** Off by RK-G7 (c) and P9-D11. Speech reads `loop_matched` only. An approved-sender list would be required if Brian wants `urgent` to speak later.

- **S83 — Surfacing quality.** Confirmed notes are sometimes not spoken on a short greeting. The progress doc records a later candidate, count toward the cap only when the reply names the item, and does not quote a separate deferral sentence (`P9-SURFACE_Progress.md`). Twenty-two real items reached `inject_count` 2 during that smoke. The 24-hour bound uses `detected_at`, not the message's own received time. A bare "Got it" after a note cannot act, because the note has no handle (review fix F9). The phrase-checker collision is the accepted residual in Track 5 verdict 14.

- **S84 — Store hygiene.** No store function deletes a closed loop. `forget_subject` redacts, and does not delete, a row whose delivery is `claimed`, `speech_started`, or `delivery_uncertain` (`P9-SPEAK_Progress.md` closeout). The serve purge start swallows exceptions (`P9-SURFACE_Progress.md` closeout: `except Exception: pass` around `start_purge_thread`).

- **S85 — Watcher coverage.** Series-delete match has no `recurringEventId` (Track 3 verdict 2, a residual). Forget-by-person misses an address known only in Contacts (`P9-WATCH_Progress.md`). Brian's own sent mail is not watched, because it is not INBOX. A "Brian replied" signal is a possible later feature. Watcher "keeps failing" recovery is a client relaunch: a close and relaunch returned the watcher to `restarts=0` (`P9-WATCH_Progress.md`). Watching while the client is closed is deferred with P9-D03. Gmail Pub/Sub pull stays deferred; polling is what shipped. If Google ever rotates the refresh token, the store keeps the old one (P9-D04, verdict 8 (a), decided). The risk is low: Google normally does not rotate refresh tokens for this client type. Recovery is a re-run of setup, as on 2026-10-16.

- **S86 — Privacy documents and logs.** Privacy-plan lines 327 and 352 still say mail stays off the cloud. Phase 5 proposes replacement text. The drafted chat-history privacy sentence (SF-G12) is not published. Brian decides. Hermes logs an 80-character preview of every user message to `agent.log` (`P9-SURFACE_Progress.md`). `auxiliary_client.py` can log a provider exception string at INFO (`P9-RANK_Progress.md`). `presence.log` was 69,450,360 bytes on 2026-10-10, with only manual `.bak` copies beside it (`P9-SUPERVISE_Progress.md`). Phase 5 confirms whether it is still unrotated.

- **S87 — Proactive speech UI.** The conversation bubble is not saved into the stored session. A resume rebuilds the list without it (`P9-SPEAK_Progress.md`). No Stop or Cancel during a proactive line. Brian (Appendix Q, Track 6 working chat, 2026-10-19): "I don't need this fix.  I'm good with them not being available.  It was an observation and Cursor explained.  We are good to closeout." At 900×640 the top-right VOICE / MIC lines overlap her hair. The chat panel shows markdown markers as characters (`P9-STORE_Progress.md`).

- **S88 — Live proof still owed.** Live `needs_reconnect` on the Systems panel was not produced. No live capture was attempted inside a proactive tail, so the echo refusal line was not produced live. K4's quiet hours, reviewed draft, locked PC, and serve-unreachable snapshot are harness-only (`P9-SPEAK_Progress.md`). The next natural occurrence is recorded. Nothing is induced.

- **S89 — Remaining Phase 9 deferrals.** Images and a redirected turn are not shown to be saved the same way as a plain prompt: `persist_user_message` is the prompt when the turn has no images (`P9-STORE_Progress.md`). Ranking quality has no later tuning decision after "the gists are accurate and neutral." Per-agent voices stay under S72. A bare section mark is a length-1 fact in `MEMORY.md`: the production parse keeps it, and a raw byte split on the delimiter does not (`P9-STORE_Progress.md`).

Phase 3 fixes are in the draft above. `OPEN_QUESTIONS.md` was not edited.

## Phase 4 — draft of ROADMAP.md (not applied)

This replaces the section "Current stage — Phase 9 (scope is Brian's call)". `ROADMAP.md` was not edited.

## Phase 9 — COMPLETE: Proactive Foundation

Phase 9 shipped the proactive foundation. Complete means every planned track shipped. Push and webhooks were deferred by the plan, and the ordinary-reply echo remains an accepted risk.

| Item | Implementation | Merge |
|---|---|---|
| P9-KICKOFF | `86b96a7d70af56744724e6b59fc3c7443829ede9` | `9d50ebcc7d6370c289419f7122536366b1e25df3` |
| P9PRE | `4bf9a32497efc5c589b2d7b792466bc98f6ab4b4` | `925fa2c7951e9415e09c156209270bb0d3504f7d` |
| P9-FIX-ARM | `f348c2db25d908fad7ee95182a659840144efe59` | `18d4062a84c6ed37e6d9c4f22fbcdec81f1b207f` |
| Build plan | `d3f62cfaed970a69ff5cfc75f156e173411851f2` | `19eaebcd755418985943d6140e01d97ad06f8ca0` |
| P9-SUPERVISE | `48ec49b90ed92ea312ad2409decb95134d0c9503` | `574fe43fb4532878eaff32c2c9f6e4baa9291c9a` |
| P9-FIX-TTS | `0d6e56c94b29458c3e0ea8a9134a8a50f74a2a02` | `72243cb5fa3384ccee19f4ace9728baa0001de06` |
| P9-STORE | `b13989a8f96c713214cb5537e24a401a02526bff` | `7e5ea69791173822ff7cba1ea5fcfecd979ebed2` |
| P9-WATCH | `27b56b59d8be5295501177914b22330bc0189aec` | `05ac85f5a9634be80726cb883e94476f60e74997` |
| P9-RANK | `df68dd432b92a634ce4e2b519499d715a8f2179b` | `5def3d3ed90bcea2cebe087fd7d4ef52cb801bb1` |
| P9-SURFACE | `bae7ac4874efff807204b977bb6dc0491d27b504` | `0f880ad00e4c1574d133f3c9e1f9ed08563072cd` |
| P9-SPEAK | `20ea9aeffebabb632eb2b55fb5f36c1189fb514f` | `abeff7e516bc4c4a9fb9d060cdd414c83b57f5af` |
| P9-SPEAK docs follow-up | `6c180cca9cf4cc5e241d46cbee39fed94fe28058` | merge-SHA record |
| P9-SPEAK docs follow-up | `96155dbcfd58883a70ab42efb7b6c94ac015a518` | this `main` tip |

Suites on `main` after the speech merge (`P9-SPEAK_Progress.md`): workspace 335 OK in 19.700s, memory 134 OK in 6.604s, tools 44 OK in 0.034s, tts 8 OK in 0.132s. Client checks exit 0, wall 9.808s, supervision 38/38, speech 38/38.

Shipped:
- backend supervision with a fail-closed gap and crash diagnostics;
- the proactive store, open loops and the forget cascade;
- the `zola-watcher` process with the fixed background read;
- background ranking and gists (tool-less, advisory);
- surfacing in conversation and `whats_pending`;
- unprompted speech for loop matches, one client coordinator, quiet hours, the Systems panel;
- the Deepgram voice (P9-FIX-TTS) and the origin ticket (P9-FIX-ARM).

Narrowings:
- P9-D07: delivered rows keep subject, snippet, gist, and display name until acknowledged, dismissed, closed, forgotten, or 7 days. The body is never kept.
- P9-D11: speech reads `loop_matched` only. `urgent` does not speak unprompted.
- P9-D12: degraded at 360 seconds. Unknown only with no row or no fresh snapshot. For up to 360 seconds the HUD can say the watcher stopped while the spoken answer is still healthy.
- WER folder: Appendix A said readable only by him. The approved ACL is the user and SYSTEM.

Recorded limits:
- The ordinary-reply echo remains an accepted risk. Track 6 closed the echo for the proactive line only.
- K7 met on the mic button, not the wake word. Stop and Cancel stay hidden during a proactive line, and Brian accepted that.
- The conversation bubble is not stored. A resume rebuilds the list without it.
- K4 quiet hours, reviewed draft, locked PC, and a serve-unreachable snapshot are harness-only.
- Live `needs_reconnect` on the Systems panel was not produced. The echo refusal line was not produced live.
- A false unprompted announcement happened. The first K1 and K3 runs do not count. The source-message fix is in the track.
- The origin ticket failed silently from the 2026-10-09 deploy until the store fix.
- The Testing-era token expired. For about two days the watcher held `needs_reconnect` while Zola answered "connected."
- Painted screenshots were presented as the live window. Brian caught them.
- A shell stopped every listener on TCP 8765. The rule adopted is to stop only this track's processes, by PID.
- `forget_subject` redacts, and does not delete, an in-flight or uncertain row. No store function deletes a closed loop.
- Twenty-two real items reached the re-injection cap during the surfacing smoke. The 24-hour bound uses `detected_at`.
- Hermes logs an 80-character preview of every user message. At 900×640 the VOICE and MIC lines overlap her hair.

## Next

Phase 10 — Android companion: scoped separately and running in parallel; recorded at its own lore closeout.

## Later candidates

Brian's call. One line of evidence each. Every bullet from "Current stage — Phase 9" is either here, in the shipped list, or named in the mapping table as Phase 10.

- **Speech pipeline (S77).** Submit to first audio was about 4.6 s on a simple turn and about 16 s on a tool turn. The follow-up quiet is 0.5 s. The ordinary-reply echo is still accepted.
- **Barge-in (S36).** Wake during playback remains. The 2026-10-12 deferral covers it. A new TTS provider does not restore it.
- **Voice I/O ownership (S56).** The upstream-blocked voice items still sit in the voice and audio layer. `S69` (a Hermes prefix in front of a whole-message match) and `S70` (no playback-completion signal) stay open beside it.
- **`agent.execution_guidance` (S54).** The largest measured latency lever remains (tool rounds about +8–12 s/turn; 17.8 s vs 5.4 s submit to audio). The Gmail skill route is gone. The decision stays open.
- **Backend crash cause (S51).** Supervision and crash diagnostics shipped in P9-SUPERVISE. The cause of the crashes is still open.
- **Phase 7 voice, still open.** `S52` stop-vs-silence race. `S55` streaming TTS bake-off. `S57` no cards in voice; Workspace sends are done, and batch and command approvals are not. `S58` smaller Whisper models. `S59` `silence_duration`, data only.
- **Carried from Phase 8.** `S35` session and always approvals. `S40` UI polish. `S28` session UI retirement (episodes exist; evaluate).
- **Autonomy.** Brian is scoping it separately.
- **Memory round two (S46–S50, S63).** Associative recall and fact-authority migration were left for measured evidence. An attributed save was not chosen.
- **Workspace expansions (S60, S61, S62, S64).** Mark read, archive, and label; calendar writes; attachment bytes; Office extraction. Each was deferred on purpose.
- **Summary selectivity (S67).** Triage summaries and one gist omitted addresses. Brian accepted the smoke and did not ask for a fix.
- **OS credential boundary (S65).** Still open if the application boundary proves insufficient.
- **Phone escalation (S74).** A late rung. A phone line is a weaker channel than a spoken passphrase in the room, and it needs its own decision.
- **Per-agent voices and direct agent conversations (S72 remainder).** The Systems panel and spoken watcher status shipped. Talking to each agent, and a voice of its own, did not.
- **Recognition (S75).** Speaker identification, then face, as signals. Neither is authentication.
- **Kasa (S76).** Lights only. A small local tool, and an install decision if it needs one.
- **Store and watcher coverage (S84, S85).** A closed loop is not deleted. Series delete, Contacts-only addresses, sent mail, and watching while the client is closed remain.
- **Privacy and logs (S86).** The privacy-plan lines, the unpublished chat-history sentence, the `agent.log` preview, and `presence.log` remain.

### Mapping — every bullet in "Current stage — Phase 9"

| Bullet | Disposition |
|---|---|
| Workspace: mark read, archive, label (`S60`) | Carried. |
| Workspace: calendar writes (`S61`) | Carried. |
| Workspace: attachment bytes (`S62`) | Carried. |
| Workspace: Office extraction (`S64`) | Carried. |
| Workspace: proactive surfacing (`S66`) | Shipped, in part. Polling, the store, ranking, surfacing, and speech: P9-WATCH, P9-STORE, P9-RANK, P9-SURFACE, P9-SPEAK. Push and webhooks were deferred by the plan. |
| Summary selectivity (`S67`) | Carried. |
| OAuth publishing (`S68`) | Shipped. Published 2026-10-09. The expired Testing token and the 2026-10-16 setup are in P9-WATCH and P9-RANK. |
| Voice I/O ownership (`S56`), with `S69` and `S70` | Carried. Annotated in Phase 3. Still open. |
| `agent.execution_guidance` (`S54`) | Carried. |
| Backend crash / recovery (`S51`) | Shipped in part: P9-SUPERVISE (supervision, the fail-closed gap, crash diagnostics). The crash cause is carried. |
| Memory round two (`S46`–`S50`, P6-D01, `S63`) | Carried. |
| Phase 7 voice (`S52`, `S55`, `S57`, `S58`, `S59`) | Carried. |
| Carried from Phase 8 (`S35`, `S40`, `S28`) | Carried. |
| OS credential boundary (`S65`) | Carried. |
| Open loops (`S71`) | Shipped: P9-STORE. |
| `P8-D02` Brian-only conflict, named inside the `S66` / `S71` brainstorm bullet | Shipped: P9-FIX-ARM (the client-origin ticket) and P9-WATCH (the fixed background read). |
| Background agents, HUD, spoken status (`S72`) | Shipped in part: P9-SPEAK (Systems panel and spoken watcher status). Per-agent voices and direct agent conversations are carried. The companion watcher row and SMS are Phase 10. |
| Android companion and distributed presence (`S73`) | Phase 10 — Android companion: scoped separately and running in parallel; recorded at its own lore closeout. |
| Remote escalation, phone (`S74`) | Carried. |
| SMS, named inside `S72` | Phase 10 — Android companion: scoped separately and running in parallel; recorded at its own lore closeout. |
| Speaker and face recognition (`S75`) | Carried. |
| Kasa lights (`S76`) | Carried. |

`ROADMAP.md` was not edited.

STOP. Phase 4 revised draft is not in `ROADMAP.md`.

## Phase 5 — live, identity, and external verification (read-only)

Nothing was edited. No process was started or stopped. No secret file, dump, or mail text was opened.

### 1. Identity

✅ `SOUL.md`. Live and `zola-architecture/identity/SOUL.md` are both 9,708 bytes, raw SHA-256 `FD0C09CD7677E7AF2C63E7CADC7DBCA2C8EF834E0E48528E1EFACC70A6CADD14`. LF-normalized hashes match (`1780443CDBED1115FD40AAE3B204EBA2DAE648786009B1F5F2E9EC4CDF87A13B`).

✅ `MEMORY_CONVENTIONS.md`. No live file, which is the recorded state (P6-FORGET: no separate apply path). Phase 9 did not add one.

⚠️ `VOICE_CONFIG.md` still documents Edge. Live `tts` is Deepgram. Expected. Replacement text is below, for approval.

### 2. Live config

✅ `config.yaml` is 4,850 bytes, SHA-256 `823DBD95C6D63EB66BE07182FAA82ACB5C48528A79F01109B6C4120560C74AFC`. CRLF, 140 lines, no bare LF.

⚠️ The post-FIX-ARM file `1C37F2A0…` is not on disk (profile backups and config-named files under `zola-spikes` were hashed). The key list below is the live file, checked against what the track docs say changed after that baseline. It is not a byte diff.

Live keys, values that are not secrets:

- `desktop.auto_continue.enabled`: `false`. This was the FIX-ARM edit, so it is inside the baseline.
- `tts.provider`: `deepgram`. `tts.edge.voice`: `en-GB-SoniaNeural`. `tts.edge.speed`: `0.95`. The Edge block is still in the file.
- `tts.providers.deepgram.type`: `command`. `output_format`: `mp3`. `model`: `aura-2-pandora-en`. `speed`: `0.95`. The command points at `%LOCALAPPDATA%\hermes\profiles\zola\zola-tts\deepgram_tts.py`, not the spike script. `deepgram_api_key` is not in the file.
- `proactive.ranker_enabled`: `true`. `proactive.surface_enabled`: `true`. `proactive.speak_enabled`: `true`.
- `cronjob` does not appear. `code_execution` appears only in a comment, not as an enabled tool.
- Other top-level keys: `model`, `agent`, `approvals`, `plugins`, `_config_version`, `memory`, `stt`, `voice`, `security`, `wake_word`, `platform_toolsets`, `known_plugin_toolsets`, `skills`. `model.provider` is `openai-codex`.

### 3. Plugins

✅ `zola_workspace`. 26 `.py` files and `plugin.yaml` at the plugin root, plus `contracts/proactive_methods.json` and `contracts/watcher_health.json`. The 26 `.py` files plus the two JSON files are the expected 28. `plugin.yaml` matches as well. 0 hash mismatches.

⚠️ `zola_memory`. The 12 mirrored files match. Repo-only: `l6_hold_guard.py`. P9-STORE recorded it as a harness guard, not imported by serve, and not mirrored.

⚠️ `zola_tools`. `__init__.py`, `calculator.py`, and `plugin.yaml` differ as raw SHA-256. After LF normalization they match. The repo working tree is CRLF. The live copies are LF.

✅ `zola-tts\deepgram_tts.py`. Live and `hermes-plugins/zola_tts/deepgram_tts.py` match. 5,596 bytes, SHA-256 `7CD342E0AE3BAD20F6A0E6B6FE0418DB8D6C856D43AB173A3C5EE48EB0432288`.

### 4. Store

✅ `proactive.db` opened `mode=ro` and `query_only`. `PRAGMA integrity_check` is `ok`. Schema version `5`.

Counts, not judged against the Track 6 cleanup: items 149 (143 at that cleanup), loops 9, open loops 0, speakable by the claim predicate 0. No row met the structural filters, so the time bounds did not change the count. No mail text was selected.

✅ `.gitignore` still has `**/proactive.db`, `**/proactive.db-wal`, `**/proactive.db-shm`, and `**/taint.sqlite`. `git check-ignore` matches. `git ls-files` shows none of those names tracked.

### 5. Constants

✅ Every value in the Phase 2 table matches the code on `main`.

| Name | Value | Where |
|---|---|---|
| `RestartLimit` / window | 3 / 10 minutes | `SupervisionConstants.cs` 6–7 |
| `RestartBackoffSeconds` | 2 | `SupervisionConstants.cs` 8 |
| `HungHealthFailureLimit` | 3 | `SupervisionConstants.cs` 12 |
| `HungProbeSpacingSeconds` | 10 | `SupervisionConstants.cs` 13 |
| Reconnect | 5 attempts, 30 s | `SupervisionConstants.cs` 9 and 11 |
| WER count / type / prune | 3 / mini (`DumpType` 1) / 14 days | registry below; `DumpRetentionDays` `SupervisionConstants.cs` 17 |
| `GMAIL_POLL_SECONDS` | 120 | `watcher.py` 30 |
| `CALENDAR_POLL_SECONDS` | 7200 | `watcher.py` 31 |
| Gmail stale / Calendar stale | 360 / 14400 | `SpeechConstants.cs` 16–17; `surface.py` 419 is `3 *` the Gmail poll and `2 *` the Calendar poll |
| `POISON_ATTEMPT_CAP` | 5 | `proactive_store.py` 55 |
| `GMAIL_RECOVERY_MARGIN_SECONDS` | 120 | `watcher.py` 36 |
| `RANK_LEASE_SECONDS` | 120 | `proactive_store.py` 31 |
| `RANK_CALL_TIMEOUT_SECONDS` | 30 | `ranker.py` 26 |
| `TURN_IN_FLIGHT_MAX_SECONDS` | 180 | `ranker.py` 37 |
| Rank idle window | 20 s | `RANK_IDLE_WINDOW_SECONDS`, `ranker.py` 33 |
| `SPEECH_CLAIM_LEASE_SECONDS` | 30 | `proactive_store.py` 32 |
| `SPEECH_OUTCOME_LEASE_SECONDS` | 120 | `proactive_store.py` 33 |
| `SPEECH_MAX_AGE_SECONDS` | 7200 | `proactive_store.py` 35 |
| Idle since last interaction / last speech bout | 20 / 20 | `SpeechConstants.IdleSeconds` 6; `speech.py` `SPEECH_IDLE_SECONDS` 26 |
| `SPEECH_POLL_SECONDS` | 20 | `speech.py` 27; `SpeechConstants.PollSeconds` 7 |
| Quiet hours | 22:00–07:00 | `speech.py` 34–35; `SpeechConstants.cs` 13–14 |
| `SPEECH_ECHO_TAIL_SECONDS` | 2 | `speech.py` 31 |
| Proactive RPC timeout | 2 s | `SPEECH_SNAPSHOT_TIMEOUT_SECONDS`, `speech.py` 28 |
| `SPEECH_START_TIMEOUT_SECONDS` | 15 | `speech.py` 29 |
| `SPEECH_COMPLETE_TIMEOUT_SECONDS` | 60 | `speech.py` 30 |
| Reservation lock bound | 50 ms | `SPEECH_LOCK_HOLD_MS`, `speech.py` 32 |
| `POST_SPEECH_WINDOW_SECONDS` | 900 | `proactive_store.py` 39 |
| `BODY_MAX_AGE_DAYS` / `TEXT_MAX_AGE_DAYS` | 7 / 7 | `proactive_store.py` 43–44 |
| `DELIVERY_KEEP_DAYS` | 30 | `proactive_store.py` 45 |
| `PURGE_INTERVAL_SECONDS` | 3600 | `proactive_store.py` 46 |
| `SURFACE_GAP_SECONDS` | 1800 | `surface.py` 28 |
| `SURFACE_QUIET_SECONDS` | 14400 | `surface.py` 29 |
| Surface attempt TTL | 600 s | `proactive_store.py` 37 |
| Surface item cap / character cap | 4 / 1800 | `surface.py` 30–31 |
| Re-injection cap | 2 | `surface.py` 37 |
| Handle TTL | 900 s | `surface.py` 39 |
| Injection age | 24 h | `SURFACE_AGE_SECONDS`, `surface.py` 36 |
| Body trim cap | 4000 | `textclean.py` 10 |
| Gist cap | 280, two sentences | `ranker.py` 38–39 |

The seven gateway names in `contracts/proactive_methods.json` match the Phase 2 list. The live file's hash matches the repo.

### 6. Exit-checklist scans

✅ No proactive code starts a Hermes turn. Nothing under `hermes-plugins/zola_workspace` calls `prompt.submit(`. `origin.py` wraps that method. It does not submit one. The ranker "heartbeat" is a state write every 300 seconds (`ranker.py` 36, 281–294), not a Hermes heartbeat turn. No `/loop` or cron creation. `cronjob` is absent from the live config.

✅ Google background calls are in `background_read.py`. `watcher.py` calls that module. `gmail.py`, `gcal.py`, and `auth.py` are the ticket and token paths. The token filename `token.dpapi` is referenced from `zola_workspace/auth.py` and from tests. No other plugin or client source names it.

✅ `hermes-agent` is clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

✅ No pre-Phase-9 package list was found in the P9PRE audit or the Phase 9 progress docs. No record. Nothing new is claimed.

### 7. WER

✅ `HKLM\...\LocalDumps\python.exe`: `DumpFolder` `C:\Users\test\AppData\Local\ZolaClient\dumps`, `DumpCount` `0x3`, `DumpType` `0x1`. HKCU key absent.

✅ Folder ACL: `NT AUTHORITY\SYSTEM:(OI)(CI)(F)` and `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only.

Listing, not opened:

| Name | Bytes | Last write |
|---|---:|---|
| `python.exe.2812.dmp` | 22,854,843 | 2026-10-17 08:31:21 |
| `python.exe.27712.dmp` | 23,091,216 | 2026-10-17 08:35:09 |
| `python.exe.29172.dmp` | 7,543,225 | 2026-10-17 16:53:44 |

Three files, which is the cap. The folder was empty at the P9-SUPERVISE closeout.

### ACL of the key file

✅ Read 2026-10-19. Contents were not read. The key file is 40 bytes, the size recorded in `P9-FIX-TTS_Progress.md`.

- `%LOCALAPPDATA%\ZolaClient\secrets\`: `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only.
- `deepgram_api_key`: `DESKTOP-VRB5NB9\test:(I)(F)` only.

The Phase 2 draft of P9-D14 does not say this. Proposed sentence, applied only if Brian approves:

The folder ACL, read 2026-10-19, is `DESKTOP-VRB5NB9\test:(OI)(CI)(F)` only. The key file ACL is `DESKTOP-VRB5NB9\test:(I)(F)` only. Contents were not read.

### 8. Privacy page

Read `https://beebodev.github.io/zola-app/privacy.html`. Last updated October 15, 2026. Not edited. No local clone.

| Behavior | Page |
|---|---|
| Background watching of Gmail and Calendar | Covered. "When the owner enables it, Zola periodically checks his Gmail and Google Calendar for new or changed items so it can tell him about things that matter, including replies he is waiting for. This runs on the owner's own computer and only reads; it never sends, changes or deletes anything." |
| Trimmed mail to the model for ranking and gists | Covered. The Ranking paragraph: display name, domain, subject, and a shortened body; a label and a one- or two-sentence summary stored on the computer; the body deleted after that; training off; forget does not pull the copy back. |
| Reply text to Deepgram | Covered. "When voice replies are on, the text of Zola's spoken replies is sent to Deepgram to be turned into audio." |
| Unprompted speech carries no mail content | Not covered. The Speech paragraph is about replies she is answering, and says that text may include email or calendar details. It does not say the unprompted phrase is free of mail content. |
| Retention 7 days / 30 days | Not covered. Storage says the tracked items are local and can be deleted. It does not say 7 or 30 days. |
| Brian's sent mail is not watched | Not covered. Background monitoring says new or changed Gmail items. It does not say sent mail is skipped. |

The page names OpenAI and the owner's ChatGPT account. Live `model.provider` is `openai-codex` with a `chatgpt.com` base URL. That is the same provider family. Brian judges the three "not covered" rows.

### 9. Privacy plan

`zola-architecture/Zola Privacy and Data Ownership Plan.md`. Not edited.

L327, in "Must remain local":

- content of messages and emails during summarization processing — only summaries or metadata may be transmitted, never raw content

The next block says language-model reasoning is "current: Gemini" and conversational voice synthesis is "current: Gemini Live API". Those two bullets are outside the two lines this prompt names. They do not match the live provider (`openai-codex`) or Deepgram.

L352, in "Data Minimization Rules for Cloud Processing":

- do not transmit raw communication content — process locally, transmit only summaries or intent signals

Proposed replacements, consistent with the P8-D11 paragraph in `P9-RANK_Progress.md`. Applied only if Brian approves.

L327:

- content of messages and emails during summarization processing — summaries or metadata, except background ranking, which sends the sender's display name, the sender's domain, the subject, and a trimmed body. The provider returns a label and a short gist. Those are stored, and the body is deleted in that same write

L352:

- do not transmit raw communication content, except the trimmed body sent for background ranking (display name, sender domain, subject, and that trimmed body). Store the label and the gist, and delete the body in that same write

### 10. Scratch folders

| Folder | Files | Proposal |
|---|---:|---|
| `C:\Users\test\Dev\zola-spikes\p9-store` | 68 | Delete. P9-STORE said delete at closeout. The track's backups were accepted for deletion after the merge. Still present. |
| `C:\Users\test\Dev\zola-spikes\p9pre` | 1 | Delete. One audit-harness log. The audit itself is merged. |

Nothing was deleted.

### `presence.log` (S86)

`C:\Users\test\AppData\Local\ZolaClient\logs\presence.log` is 177,214,171 bytes. At the P9-SUPERVISE closeout it was 69,450,360 bytes (2026-10-10). The three `.bak` copies are unchanged (118,335, 1,324, and 1,324 bytes). The live file is still unrotated. Contents were not read.

### Proposed `VOICE_CONFIG.md` text

Replace the `tts` block in the restore fence, and the three Edge bullets under it. The rest of the file stays.

```yaml
# P9-FIX-TTS: Deepgram command provider; the Edge block stays in the file — P9-D14
tts:
  provider: deepgram
  edge:
    voice: en-GB-SoniaNeural
    speed: 0.95
  providers:
    deepgram:
      type: command
      command: '"C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe" "C:\Users\test\AppData\Local\hermes\profiles\zola\zola-tts\deepgram_tts.py" "{input_path}" "{output_path}" "{model}" "{speed}"'
      output_format: mp3
      model: aura-2-pandora-en
      speed: 0.95
```

- `tts.provider`: `deepgram` (`P9-D14`). The Edge block remains in the live file and is not the active provider.
- `tts.providers.deepgram`: command provider. The script is `%LOCALAPPDATA%\hermes\profiles\zola\zola-tts\deepgram_tts.py`. Model `aura-2-pandora-en`. Speed `0.95`. Output `mp3`.
- The key file is `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key`. The key is not in `config.yaml` and not in this document.

### Approvals Brian needs to give

1. The `VOICE_CONFIG.md` text above.
2. The privacy-plan sentences for L327 and L352. The Gemini bullets beside them are a separate choice.
3. The P9-D14 ACL sentence.
4. Scratch deletions, by folder name: `p9-store` (68 files) and `p9pre` (1 file).

### Every ⚠️

- `VOICE_CONFIG.md` still says Edge. Live TTS is Deepgram.
- The post-FIX-ARM config file is not on disk, so the key diff is from the track records plus the live file.
- `zola_memory` has repo-only `l6_hold_guard.py`, recorded as not mirrored.
- `zola_tools` raw hashes differ by CRLF. LF-normalized text matches.
- The privacy page does not cover mail-free unprompted speech, the 7-day and 30-day retention, or the sent-mail exclusion.
- The privacy plan's Gemini bullets (beside L327) do not match the live model provider or Deepgram.
- `presence.log` is 177,214,171 bytes and still unrotated.

The Phase 5 report above was accepted. Phase 6 applied it.

## Phase 6 — applied, not committed

Brian's verdicts (2026-10-19). These are his answers to four questions. Recorded as he gave them. They are not free-text quotes.

- Doc edits. Brian chose: "Approve all three".
- Scratch folders. Brian chose: "Delete both".
- Crash dumps. Brian chose: "Identify, then diagnose later".
- Privacy page. Brian chose: "Draft text, I'll publish".

### Applied files

| File | What landed |
|---|---|
| `DESIGN_DECISIONS.md` | The Phase 2 draft, from "Phase 9 — Proactive Foundation" through the process lessons. P9-D14 adds the 2026-10-19 user-only ACL sentence. The Phase 5 scan result replaces the "when Phase 5 has run" placeholder. P2-D17 records that no package list was found. |
| `OPEN_QUESTIONS.md` | The Phase 3 annotations and S77–S89. S51 is the dump match below. S86 is the Gemini residual, the unpublished paragraph, and the current `presence.log` size. |
| `ROADMAP.md` | The Phase 4 complete section replaces "Current stage — Phase 9". S51 and S86 carry the verdicts. The mapping table stays in this progress doc. |
| `identity/VOICE_CONFIG.md` | The Deepgram command provider as proposed. Edge block kept. Key file named, no value. |
| `Zola Privacy and Data Ownership Plan.md` | L327 and L352 as proposed. Gemini bullets were not edited (L333, L334, and the same names at L425 and L431). |

`git diff --stat`: 5 files, 418 insertions, 43 deletions. CRLF on every edited file. No bare LF. `hermes-agent` is still clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

### Deletion

The only deletion. Neither folder was opened.

| Folder | Files | After |
|---|---:|---|
| `C:\Users\test\Dev\zola-spikes\p9-store\` | 68 | gone |
| `C:\Users\test\Dev\zola-spikes\p9pre\` | 1 | gone |

### Crash dumps

Not opened, copied, or moved. The supervisor log does not record a serve pid. `serve-stderr.log` names no pid. The watcher log has no line for these PIDs, and none is a watcher `job_assigned` pid.

| Dump | Bytes | Time | Match |
|---|---:|---|---|
| `python.exe.2812.dmp` | 22,854,843 | 2026-10-17 08:31:21 | Zola serve. `zola_memory.store_open pid=2812` at 08:21:09. `supervisor proc=serve event=restart` at 08:31:22. |
| `python.exe.27712.dmp` | 23,091,216 | 2026-10-17 08:35:09 | Zola serve. `store_open pid=27712` at 08:31:32. `proc=serve event=restart` at 08:35:10. |
| `python.exe.29172.dmp` | 7,543,225 | 2026-10-17 16:53:44 | Zola serve. `store_open pid=29172` at 16:52:55, 16:53:00, and 16:53:17, after Track 6 killed serve shim 4676 at 16:52:45. `proc=serve event=stale` at 16:53:43 and `event=restart` at 16:53:45. Why this process exited is not established. |

The dumps are not analyzed. The crash cause stays open. The client deletes them after 14 days (about 2026-10-31). Brian chose: "Identify, then diagnose later". A separate diagnostic task must run before that prune if the dumps are to be analyzed. Nothing in this task extends or changes the prune.

### Privacy-page paragraph (draft only)

Not published. `beebodev/zola-app` was not edited. Brian chose: "Draft text, I'll publish".

When Zola speaks without being asked, she uses a short fixed sentence with a name, or the word "someone." That sentence does not include the email. Notes she keeps about new mail stay for 7 days. A record that she delivered one stays for 30 days. She does not watch mail he sent.

S86 records that this paragraph is drafted and waiting for Brian to publish.

### Recorded, no further approval

- `l6_hold_guard.py` is a test harness guard. P9-STORE left it unmirrored on purpose.
- `zola_tools` differs from the repo working tree by line endings only. LF-normalized text matches.
- The post-FIX-ARM config file is not on disk. The key diff is from the track records plus the live file.
- `presence.log` is 177,214,171 bytes on 2026-10-19, up from 69,450,360 bytes on 2026-10-10. That is about 12 MB a day. It is still unrotated.
- `proactive.db` holds 149 items, against 143 at the Track 6 cleanup. That is live mail since then, not an error.

### Phase 9 Exit Checklist

| Item | Result |
|---|---|
| Track 1 merged | ✅ `574fe43fb4532878eaff32c2c9f6e4baa9291c9a` |
| Track 2 merged | ✅ `7e5ea69791173822ff7cba1ea5fcfecd979ebed2` |
| Track 3 merged | ✅ `05ac85f5a9634be80726cb883e94476f60e74997` |
| Track 4 merged | ✅ `5def3d3ed90bcea2cebe087fd7d4ef52cb801bb1`. The ranking paragraph was published on 2026-10-15 (gate "privacy page published"). |
| Track 5 merged | ✅ `0f880ad00e4c1574d133f3c9e1f9ed08563072cd` |
| Track 6 merged | ⚠️ Code merged (`abeff7e516bc4c4a9fb9d060cdd414c83b57f5af`). Echo is closed for the proactive line only. The ordinary-reply echo remains an accepted risk. HUD unknown is narrowed by D12 (b). Live `needs_reconnect` was not produced. K4's quiet hours, reviewed draft, locked PC, and serve-unreachable snapshot are harness-only. |
| No Hermes turn for proactive work | ✅ Phase 5 scan. |
| Only `background_read` calls Google in the background; only `zola_workspace` names the token | ✅ Phase 5 scan. |
| No `hermes-agent` edits | ✅ Clean at `345cd2b057a452236de401d3534b8502a7465e8d`. |
| No installs unless approved | ✅ No pre-Phase-9 package list. None in this closeout. |
| Live-profile changes limited to those approved, mirrored, backups deleted | ⚠️ Scratch folders `p9-store` (68) and `p9pre` (1) are gone. Live `zola_workspace` and the Deepgram script match the repo. `zola_memory`'s `l6_hold_guard.py` is repo-only on purpose. `zola_tools` matches after LF normalization and differs by CRLF. |
| Named constants; no content in logs or repo documents | ✅ Constants match the code. This closeout added no mail text. |
| All suites pass on `main`; client builds | ✅ Recorded after the speech merge: workspace 335, memory 134, tools 44, tts 8, client checks exit 0. Not re-run here. The tree's code is that merge. |
| Smoke after each track boundary | ✅ Recorded in each track progress doc. Not re-run here. |
| Lore closeout | ⚠️ Decisions, open questions, roadmap, and `VOICE_CONFIG.md` are applied. The lore-closeout paragraph (unprompted speech, 7-day and 30-day retention, sent mail not watched) is drafted and waiting for Brian to publish. |

Implementation commit: `748534b19d570741dd22196896e6fe8efee2e46b`.
Merge commit on `main`: `8842d315420574a012f2a2d0cd103507560bd376`.

Phase 9 CLOSED.




