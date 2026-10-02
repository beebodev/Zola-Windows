# P5-MEMORY Progress — Memory She Keeps

## Branch

- Branch: `p5-memory`
- Base (`main` HEAD at branch create): `b29b6edc4b1c9011595b5444378b927b1a31a833`
- Prompt version: 1.1 (2026-10-02) against build plan v1.2
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P5-MEMORY_Prompt_v1.1.md`
  SHA-256 `6eec0a2be31ba77aaad5af8b1f95372c097739b048901bb0a1edbe77202b3eb3` (verified 2026-10-02 before Phase 1)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (expect clean throughout)
- Scratch / backups (outside repos): `C:\Users\test\Dev\zola-spikes\p5-memory\`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document | COMPLETE |
| 2 | Read-Only Checks and Baseline | COMPLETE |
| 3 | Propose the Exact Edits (STOP) | COMPLETE |
| 4 | Back Up, Apply, Mirror, Verify | COMPLETE |
| 5 | Smoke Test | COMPLETE |
| 6 | Closeout | IN PROGRESS |

## Guardrails summary

- **G-SCOPE:** Live: `SOUL.md` new "What I remember" section (approved text only); `config.yaml` `user_char_limit` 2750→4000 with plan comment. Repo: `identity/SOUL.md` mirror; `identity/MEMORY_CONVENTIONS.md` budget 4400/4000 + routing / brief-mention / explicit-only-search prose; this progress doc. No client source.
- **G-ARCH:** Build plan is truth. Conflicts → STOP.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No `windows-client/**`, hermes-agent, other live profile files, hand-edits to `memories/*`, skills, lore, build plans.
- **G-PRIVACY:** Repo docs may hold counts, tags, hashes, skill names, dates, classifications, and this track's synthetic test statements only — never other memory/skill/conversation content.
- **G-BLIND:** Smoke script classifications stay out of Zola's ear; Brian speaks naturally.
- **G-LIVE:** One live step at a time; dictation off before voice.
- **G-COMMENT:** YAML comment per plan; one prose note in `MEMORY_CONVENTIONS.md` citing P5-D03–D06.
- **G-STOP / G-CLOSEOUT:** Stop after each phase; closeout only on "proceed to closeout".
- **G-LORE-SCOPE:** No lore edits in this track (S42 waits for Phase 5 lore closeout).
- **G-NO-CROSS-SCOPE:** Android Zola out of scope.

## Discrepancies

None that block Phase 3.

- Note only (out of scope): live/`identity` `SOUL.md` still says "text-based Windows client".
- USER.md fill is high at current budget (2108/2750 ≈ 77%); P5-D05 raises the limit to 4000.

## Phase 2 findings

### 1. Soul match

- Live and `identity/SOUL.md` are **identical** (raw SHA-256 match; LF-normalized match).
- SHA-256 (both): `ca2cd346eadab3d6972fe36d16ef129e186c3b66b538f05ead20baa9ec4014a5` (4,124 bytes).
- LF-normalized SHA-256 (both): `edcba475eb1c29beee8042f0cfda32004f0d69bf397a1e1393aee9ca4a0c3ee8`.

### 2. Effective memory config

Profile `memory:` deep-merges over `hermes_cli/config_defaults.py` L1215–1228:

| Key | Effective | Source |
|---|---|---|
| `memory.memory_enabled` | `true` | default |
| `memory.user_profile_enabled` | `true` | default |
| `memory.memory_char_limit` | `4400` | profile |
| `memory.user_char_limit` | `2750` | profile |
| `memory.provider` | `""` (built-in only) | default |
| `memory.nudge_interval` | `10` | default |
| `memory.write_approval` | `false` | default |

No `platform_toolsets` / `disabled_toolsets` / `agent.coding_context` in the profile. `memory` and `session_search` are in `_HERMES_CORE_TOOLS` (`toolsets.py`); both targets enabled → no single-target schema narrowing. Both tools are available to client sessions.

### 3. Memory baseline (G-PRIVACY: counts only)

| File | Entries (§-delimited) | Chars (`MemoryStore._char_count`) | Limit | Fill | `[tag]` prefixes | SHA-256 |
|---|---|---|---|---|---|---|
| `MEMORY.md` | 1 | 234 | 4400 | 5.3% | none | `8264268512e5cc7a37fff847f523ca142c310dbf21bef30c2ad601ee3a5986eb` |
| `USER.md` | 13 | 2108 | 2750 | 76.7% | none | `47a732a0b218936c9b465f6bb8ada34bcda4fe027660f000e9b139b4e7022d12` |

### 4. Skills check (P5-D07)

Profile has many bundled skills (SKILL.md under category dirs; most created ~2026-09-22). Agent-created/modified via `skill_manage` (curator ledger, actor=`curator`):

| Skill | Created | Modified | Personal-fact count | Classification |
|---|---|---|---|---|
| `spoken-conversation` | 2026-09-23 | 2026-10-01 | 0 | procedural only |
| `architecture-review` | 2026-09-28 | 2026-09-28 | 0 | procedural only |
| `personal-location-context` | 2026-09-29 | 2026-09-29 | 0 | procedural only |
| `interactive-preferences` | 2026-09-30 | 2026-10-02 | 0 | procedural only |
| `everyday-assistance` | 2026-10-01 | 2026-10-01 | 0 | procedural only |

**STOP item for Brian:** none — no agent-managed skill holds personal facts about Brian (content read locally; not copied here). Nothing moved.

### 5. Tool text she sees

Both `memory` and `user` targets enabled → full `MEMORY_SCHEMA` description (no `_SINGLE_TARGET_TEXT` rewrite). WHEN / SKIP / skills / `session_search` redirections are present. This is the conflict P5-D03 overrides. Quoted in Phase 2 stop message.

### 6. Correction path

**Confirmed.** `MemoryStore._mutate` (`memory_tool_store.py`): under `_file_lock`, re-reads the file from disk (`_read_raw_checked` → `_parse_entries`), then `mutate` runs against that live entry list — not `_system_prompt_snapshot`. `replace` / `remove` → `_edit` → `_mutate`. Snapshot stays frozen for the prompt (AUD-08); disk + live lists update. Correction test expectation stands.

## Baseline memory fill

See Phase 2 §3 table above.

## Skills check

See Phase 2 §4 table above.

## Backup hashes

### Phase 4 pre-edit (live profile → `C:\Users\test\Dev\zola-spikes\p5-memory\backup\`)

- `SOUL.md` SHA-256 `ca2cd346eadab3d6972fe36d16ef129e186c3b66b538f05ead20baa9ec4014a5` (4,124 bytes)
- `config.yaml` SHA-256 `26cc6a6f811589b6b0963d598dc95bb6153c5ad60fb8072b10b7bac601a0605e` (3,117 bytes)

### Phase 4 post-edit

- Live / identity `SOUL.md` SHA-256 `855679031e752a550c9840f35cd53870de606b99f896d58f017da1203d4d5800` (5,630 bytes; raw-identical)
- Live `config.yaml` SHA-256 `f8d7a1498f3eb41f424ccf36704b94f2e439c599002094403feb55d30d5b05ef` (3,106 bytes)
- `identity/MEMORY_CONVENTIONS.md` SHA-256 `f279318fde2133184847621161240cc4fa1881e7e0744dcbc9fee7139332a072` (2,735 bytes)
- `MemoryStore` (`load_on_disk_store`, `HERMES_HOME`=zola profile): `memory_char_limit=4400`, `user_char_limit=4000`

## Approved text

Brian Phase 3 verdict (2026-10-02): B — keep P1 comment; indented P5 comment above `user_char_limit` only. C — approved as proposed + MemoryStore sentence → 4000 + yaml layout as B. A — developer-revised section below (verbatim); hard-wrap to match existing `SOUL.md`. Then: "proceed to phase 4".

### Approved `SOUL.md` section (as applied; hard-wrapped, words unchanged)

```
## What I remember
I keep a small notebook that carries over between our conversations. When I learn something that
will still matter later — about Brian, the people in his life, his projects and cars, how he likes
things done, or a decision we've made — I write it down with my memory tool, even if he didn't ask
me to. I keep the notebook small and selective, but lasting facts about Brian and his world belong
in it, his preferences included. They go in my notebook, not tucked away somewhere else. When he
says "remember this," I always do. When I save something on my own, I mention it in a few words,
like "I'll remember that," and keep going.
Facts about Brian himself — who he is, what he prefers, the people in his life — go in his profile.
Facts about his world — projects, vehicles, decisions, how things are set up — go in my notes. Each
entry starts with one lowercase tag in square brackets, like [car] or [project], then the fact in a
sentence. I don't save small talk, one-off task progress, or things I can easily look up again. I
save what Brian tells me, what we clearly decide, and what I've confirmed; I don't turn guesses or
assumptions into facts. When Brian corrects something or it changes, I update the existing fact
instead of keeping both versions. If the notebook is full, I tighten or drop what's stale to make
room.
When Brian asks about something from an earlier conversation and it isn't in my notebook, I search
our past conversations and tell him roughly when it was. I don't go through past conversations on my
own.
```

## Smoke Part A — pre-S1 baseline

- Memory backup dir: `C:\Users\test\Dev\zola-spikes\p5-memory\backup\memories-pre-s1\`
- `MEMORY.md`: 1 entry, 234 chars / 4400; SHA-256 `8264268512e5cc7a37fff847f523ca142c310dbf21bef30c2ad601ee3a5986eb`
- `USER.md`: 13 entries, 2108 chars / 4000; SHA-256 `47a732a0b218936c9b465f6bb8ada34bcda4fe027660f000e9b139b4e7022d12`
- Log offsets before launch: `voice-timeline.log` **454255**; `display-state.log` **690374**; `server-requests.log` **29704**; `tool-events.log` **78**
- Dictation: off (Brian confirmed 2026-10-02)
- Client pid **23288** launched 2026-10-02T08:48:51-07:00 (Debug win-x64)
- Ready: `2026-10-02T08:48:53.602` display-state voice="Idle" mic="Mic: listening for "Hey Zola"" mode=Idle link connected; `wake.start` ok (fresh app session / new agent)

## Per-candidate results

Session S1: `20261002_084852_0e07b4`. `session_search` calls during S1: **0**. Budget rejections: **0**. Memory tool ops: 10 (9 add + 1 replace). No fact in both files.

| # | Expected | Saved? | File | Tag | Self-initiated? | Correct? |
|---|---|---|---|---|---|---|
| 1 | lasting → user | yes | user | contact | yes | yes |
| 2 | trivial → — | no | — | — | — | yes |
| 3 | lasting → user | yes | user | preference | yes | yes |
| 4 | correction first → memory | yes then replaced | memory | car | yes | yes (written, then replaced by #11) |
| 5 | trivial → — | no | — | — | — | yes |
| 6 | lasting → memory | yes | memory | car | yes | yes |
| 7 | explicit → user | yes | user | schedule | no | yes |
| 8 | trivial → — | no | — | — | — | yes |
| 9 | lasting → memory | yes | memory | project | yes | yes |
| 10 | lasting → user | yes | user | preference | yes | yes |
| 11 | correction second → memory | yes (final) | memory | car | yes | yes — exactly one final entry (gunmetal); purple removed via replace |
| 12 | explicit → memory | yes | **user** | schedule | no | **no — routing miss** (prompt: USER counts as miss) |
| 13 | lasting → memory | yes | memory | project | yes | yes |
| 14 | trivial → — | no | — | — | — | yes |
| 15 | transient → — | **no** | — | — | — | yes (bridge still valid) |

Brian mentions (his words): #1 remember; #2 normal; #3 remember; #4 remember; #5 normal; #6 remember; #7 remember; #8 normal; #9 remember; #10 remember; #11 "got it"; #12 remember; #13 remember; #14 normal; #15 "got it".

### S1 score vs Part C thresholds

| Check | Result |
|---|---|
| Lasting ≥5/6 | **6/6** PASS |
| Trivial ≤1/4 | **0/4** PASS |
| Explicit 2/2 | **2/2** PASS |
| Correction one gunmetal | **PASS** (add purple → replace gunmetal) |
| Expected file + tag + no dual | **PARTIAL** — #12 in `user` not `memory`; all tagged; no duals |
| No budget rejection | PASS |
| Brief mention (self-initiated) | PASS (Brian heard remember-style on #1,3,4,6,9,10,13; #11 "got it") |
| #15 absent | PASS |

## Character counts / capacity

| | Before S1 | After S1 |
|---|---|---|
| USER.md chars | 2108 / 4000 | 2413 / 4000 (18 entries) |
| MEMORY.md chars | 234 / 4400 | 462 / 4400 (5 entries) |
| USER delta | — | +305 chars |
| MEMORY delta | — | +228 chars |
| Saved test facts (final unique) | — | 10 (#1,3,6,7,9,10,11,12,13 + #4 absorbed into #11) |
| Avg chars / saved fact (total delta / 10) | — | ~53.3 |
| Rough remaining capacity (USER) | — | (4000−2413)/53.3 ≈ **29.8** facts |
| Rough remaining capacity (MEMORY) | — | (4400−462)/53.3 ≈ **73.9** facts |

### Pre-S2 / pre-BR1 memory hashes (after S1)

- `MEMORY.md` `f0f75aa1b1e7230351269a822f81a860601ca02b53ca306d1a477a1f4c618f69`
- `USER.md` `e181e26745f43af451b1463b1c4ba211190b3bce33224fb98d795743cdaea9e5`

## Session S2 results

Session: `20261002_090944_47ca34`

| # | Result | Notes |
|---|---|---|
| R1 | **PASS** | Gunmetal gray; TURN tools=`[]` |
| R2 | **PASS** | Marcus (Brian: "Marucs"); TURN tools=`[]` |
| R3 | **PASS** | Monday and Thursday; TURN tools=`[]` |
| BR1 | **PARTIAL** | `session_search` ran on this turn only; answer "You stopped at Fred Meyer."; **no timing phrase** in the reply (prompt asked for roughly when). #15 still absent from memory. Memory hashes **unchanged** after BR1 (nothing saved from search). R1–R3 had zero `session_search`. |

Post-BR1 hashes (unchanged): MEMORY `f0f75aa1…8618f69`; USER `e181e267…aea9e5`.

## Cleanup result

Brian: empty box while thinking, then "forgotten".

**BYTE-IDENTICAL** vs pre-S1 baseline (`memories-pre-s1/`):
- `MEMORY.md` / `USER.md`: entry-count match, character-count match, hash match.
- All test cues absent; no preexisting entries missing; no extras; tags unchanged (still untagged baseline entries).
- SEMANTIC PASS also holds.

Part C after cleanup: client stopped; `hermes-agent` clean at `345cd2b0…`; live `SOUL.md` / `config.yaml` still match Phase 4 post-edit hashes (`85567903…`, `f8d7a149…`).

Brian verdict: proceed to closeout with two developer-acknowledged ⚠️ PARTIAL exit criteria (routing #12; bridge timing) — 2026-10-02.

## Final file list

- Modified (repo): `identity/SOUL.md`, `identity/MEMORY_CONVENTIONS.md`
- Modified (live, outside git): `SOUL.md`, `config.yaml` (backed up under `zola-spikes/p5-memory/backup/`)
- New: `zola-architecture/lore/prompts/progress/P5-MEMORY_Progress.md`

## Exit criteria verification (Track 2, PHASE5_BUILD_PLAN.md v1.2)

| Criterion | Status | Evidence |
|---|---|---|
| Live SOUL has approved section; identity matches live | ✅ MET | Section applied verbatim (hard-wrapped); live≡identity SHA `85567903…4d5800` |
| MemoryStore 4400/4000; MEMORY_CONVENTIONS matches | ✅ MET | `load_on_disk_store` → 4400/4000; conventions yaml example 4400/4000 |
| Save-rate: lasting ≥5/6 | ✅ MET | S1 **6/6** |
| Save-rate: trivial ≤1/4 | ✅ MET | S1 **0/4** |
| Save-rate: explicit 2/2 | ✅ MET | S1 **2/2** |
| Correction one corrected value | ✅ MET | purple add → gunmetal replace; one final |
| Routing correct, no duplicates | ⚠️ PARTIAL | **Developer-acknowledged.** 9/10 correct. #12 (registration) went to user with tag `[schedule]` instead of memory. Both files are injected every turn, so recall is unaffected. Not tuned in Phase 5; it is an input for S14. |
| Every new entry tagged | ✅ MET | All S1 saves had `[tag]` |
| No budget rejection | ✅ MET | 0 reject signals in S1 |
| Brief mention on self-initiated saves | ✅ MET | Brian heard remember-style on #1,3,4,6,9,10,13 |
| Bridge: session_search when asked + dated answer; zero elsewhere | ⚠️ PARTIAL | **Developer-acknowledged.** `session_search` ran only when asked, the answer was correct, and nothing was saved, but there was no "roughly when" in the reply. Not tuned in Phase 5; it is evidence for S43 (time awareness, Phase 6). |
| Recall fresh session ≥3 facts, no tools | ✅ MET | R1–R3 PASS, tools=`[]` |
| Per-candidate table + char counts recorded | ✅ MET | Progress doc S1/S2 tables |
| Cleanup semantic/byte-identical; no hand edits | ✅ MET | **BYTE-IDENTICAL** to pre-S1 |
| Skills check reported; no skill files changed | ✅ MET | Phase 2; no skill edits this track |
| hermes-agent clean; no client source changes | ✅ MET | `345cd2b0…` clean; git status only identity + progress |

All criteria met or developer-acknowledged PARTIAL: **YES**

## Closeout SHAs

- Implementation commit: *(pending 6c)*
- Merge SHA on main: *(pending 6f)*
- Final main tip: *(pending 6g)*
