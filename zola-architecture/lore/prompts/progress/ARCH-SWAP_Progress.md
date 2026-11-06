# ARCH-SWAP Progress — Windows architecture docs replace the Android-era copies

## Branch

- Primary folder: `C:\Users\test\Dev\zola-windows`. No worktree.
- Branch: `arch-swap`, cut from `main` on 2026-11-06.
- Base SHA: `898b1e6f83f4d653820b8432afe80660122a8e1d`. At Phase 1, `main` = `origin/main` = this SHA. Working tree was clean before this progress doc.
- HEAD at the end of Phase 1 is still that SHA. This progress doc is untracked. Nothing is committed.
- `core.autocrlf` is `true`. It was read and not changed.
- Hermes: `C:\Users\test\Dev\hermes-agent`. Clean, detached at `345cd2b057a452236de401d3534b8502a7465e8d` (tag `v2026.9.14`). Read-only.
- Prompt: `ARCH-SWAP_Prompt_v1.1.md` (canonical `C:\Users\test\Dev\zola-spikes\prompts\ARCH-SWAP_Prompt_v1.1.md`).
- Prompt SHA-256 (on-disk, 30,762 bytes): `5376c68c9d9eb3e2adf2a8cd170081c2a9c1f1c9233ab7068686e062aeba0e8c`.
- Verified 2026-11-06. The developer confirmed this hash matches Claude's record.

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Preconditions, inputs, inventory | COMPLETE (accepted 2026-11-06) |
| 2 | Reference census and as-built check | COMPLETE (accepted 2026-11-06) |
| 3 | Install the new docs and update active references | COMPLETE (accepted 2026-11-06) |
| 4 | Retire the 39 copies | COMPLETE (accepted 2026-11-06) |
| 5 | Identity lines under P4-D25 | COMPLETE (accepted 2026-11-06) |
| 6 | Apply the identity edits and verify | COMPLETE (accepted 2026-11-06) |
| 7 | Commit and merge | in progress (2026-11-06) |

## Guardrail summary

- G-PRECONDITION: Phase 10 lore closeout is merged. Tag `p10-closed` peels to `898b1e6f83f4d653820b8432afe80660122a8e1d`, which is `main`. Met. See Precondition.
- G-SCOPE: 22 Appendix M files, deletion of the 39 Appendix L files, active-reference edits only after Phase 2 approval, identity edits only after Phase 5 approval (applied in Phase 6), and this progress doc. No code, plugin, test, config, client, lore entry, build plan, audit, or other progress doc.
- G-VERBATIM: the 22 files are installed byte for byte. Problems are reported, not patched.
- G-HISTORY: lore, closed build plans, progress docs, prompts, closeouts, and audits are not rewritten.
- G-ACTIVE: active references are listed at the Phase 2 STOP and edited only after approval.
- G-DELETE-EXACT: `git rm` only the 39 Appendix L files, after a fresh on-disk SHA check. Nothing under `identity/`, `lore/`, or `audit/` is deleted.
- G-P4-D25: Phase 5 reports. Phase 6 applies only text Brian has approved.
- G-NO-RESTART: no process is started, stopped, restarted, or killed.
- G-NO-CROSS-SCOPE: no Phase 10, Phase 11, speech, avatar, decision, or open-question work.
- G-PRIVACY: no message text, tokens, keys, or secrets.
- G-STOP: stop after every phase.
- SOP v3.0 transition: SOP v2.2 verification and merge rules still apply. This merge reaches the everyday build only with Brian's approval. No track merge in Phase 1.

## Discrepancies

None.

Notes that are not discrepancies:

- The P10-LORE implementation `5d2813130c8f48d13acd96eb09d6e4c877ecb57e` also edits `identity/SOUL.md`, `lore/DESIGN_DECISIONS.md`, `lore/OPEN_QUESTIONS.md`, `lore/ROADMAP.md`, and adds `lore/prompts/progress/P10-LORE_Progress.md`. Those files are outside Appendix L. Filtered to the 39 paths, that commit touches only `Zola Privacy and Data Ownership Plan.md`.
- `zola-arch-drafts\arch\A14_Privacy_Boundaries_DRAFT.md` and `zola-arch-drafts\arch\A15_Authority_Boundaries_DRAFT.md` are present. They are not in Appendix M and were not copied.
- `DESIGN_DECISIONS.md` also has `P10-D01a`, `R2`, and `R4` in the Phase 10 section, beside P10-D01 through P10-D19.

## Precondition

Met.

| Check | Result |
|---|---|
| `main` | `898b1e6f83f4d653820b8432afe80660122a8e1d` |
| `origin/main` | `898b1e6f83f4d653820b8432afe80660122a8e1d` |
| Working tree before this doc | clean |
| Tag `p10-closed` | annotated tag; `p10-closed^{commit}` = `898b1e6f83f4d653820b8432afe80660122a8e1d` |
| Tag ancestor of `main` | equal to `main`. `git log --oneline p10-closed..main` is empty |
| Merge `d9effc5ae8b9f55345430a16e1046eeb49df68e1` | on `main`. Subject `Merge branch 'p10-lore'` |
| Implementation `5d2813130c8f48d13acd96eb09d6e4c877ecb57e` | ancestor of `main` |
| ROADMAP | line 355: `## Phase 10 — COMPLETE: Android Companion` |
| DESIGN_DECISIONS | headings P10-D01 through P10-D19 are present |
| Hermes | clean, detached at `345cd2b057a452236de401d3534b8502a7465e8d` |

`git log --oneline --since=2026-11-02 --` the 39 Appendix L paths:

```
5d28131 docs(P10-LORE): Phase 10 lore closeout — decisions, open questions, roadmap
```

`git show --stat 5d2813130c8f48d13acd96eb09d6e4c877ecb57e`:

```
 .../Zola Privacy and Data Ownership Plan.md        |    9 +-
 zola-architecture/identity/SOUL.md                 |   10 +
 zola-architecture/lore/DESIGN_DECISIONS.md         |  285 +++++
 zola-architecture/lore/OPEN_QUESTIONS.md           |   81 +-
 zola-architecture/lore/ROADMAP.md                  |   99 +-
 .../lore/prompts/progress/P10-LORE_Progress.md     | 1135 ++++++++++++++++++++
 6 files changed, 1607 insertions(+), 12 deletions(-)
```

Among the 39, the name list for that commit is only `zola-architecture/Zola Privacy and Data Ownership Plan.md`.

## Appendix M inputs

All 22 files in `C:\Users\test\Dev\zola-arch-drafts` match Appendix M. Each is LF (CR count 0). No destination path exists.

| # | Source | Bytes | SHA-256 | Match |
|---|---|---|---|---|
| 1 | `arch\A01_Architecture_Overview.md` | 25999 | `83dbd372f543daea87125f13ce725ea349892b32388df87bff3695e3aa3c6614` | yes |
| 2 | `arch\A02_Identity_and_Personality.md` | 27944 | `a7e6d632e5dbf126c7b2a98eb466611c05a7d56e40aedd732b638076d72578d5` | yes |
| 3 | `arch\A02b_Relationship_with_Brian.md` | 22197 | `4db25b4fbf6ddff08a102575b0398a9909aa20d1ab9c29b0cee31afc8431ed34` | yes |
| 4 | `arch\A03_Memory_and_World_Model.md` | 51542 | `1bca649cab522b53bf2018739505497766bbbf27b760abd31a35fcec21e5f977` | yes |
| 5 | `arch\A04_People_in_Brians_World.md` | 29279 | `46762fb9e69fe9a2d45b9cebf8b500b9134ca00b82af1bdc33829489eda4a378` | yes |
| 6 | `arch\A05_Time_and_Temporal_Understanding.md` | 23498 | `21b29d5a5a8dc7ca8c92f05f783a5ad9f9e634e70e6eb56b9afb3b0bac33d233` | yes |
| 7 | `arch\A06_Conversation_and_Continuity.md` | 28612 | `b790793fe7981a1906ace8236c772ed563b0c9c7c4779cb8df09131e2b98f988` | yes |
| 8 | `arch\A07_Voice_Listening_and_Speech.md` | 41794 | `8c320f8135d817dce899626bbda6e736400fb6be6ce8b319b838606de76739c3` | yes |
| 9 | `arch\A08_Awareness_Sources_Signals_and_User_State.md` | 34345 | `00dd279eb3bdc494284fc4e9ea912d34c15f62cac666bbe1cdd408c58ebe9616` | yes |
| 10 | `arch\A09_Physical_Perception.md` | 27626 | `890addccd4641f1459da3eb8218260499e658250fca8ed0197bca61176f53d3c` | yes |
| 11 | `arch\A10_Understanding_Events_and_Judgment.md` | 36763 | `1cab51dfea849eb3a79f4a178dbfc951e0a1908cfa770a962065ede6d113e1fb` | yes |
| 12 | `arch\A11_Proactive_Engagement.md` | 33304 | `f7a0bc88874f7c238b420f972120f73431b8c0ef6f715fe34b1dfba1ad777fd5` | yes |
| 13 | `arch\A12_Distributed_Presence_and_Devices.md` | 42985 | `355feaed62f4050da9db6ba8ca3c731cfef42a4eee1aebbdcd70ae6893fec345` | yes |
| 14 | `arch\A13_Presence_UI_and_Avatar.md` | 26081 | `4909c7ab8b3a643016ed5264e0383346e61e2fd772aaa35eedb51b4a0bea7519` | yes |
| 15 | `arch\A14_Privacy_and_Memory_Ethics.md` | 41925 | `3b1711884503b5de8a798bbde6b5b6d6ee4422bba08ce0f08f4e675d62b78d07` | yes |
| 16 | `arch\A15_Authority_Tools_Actions_and_Autonomy.md` | 31432 | `a50308b3f39d896f134acdcd99a978ac3944dfa74795bed949d7ccbaed707356` | yes |
| 17 | `ARCH_DOCS_DECISIONS.md` | 51758 | `db872b47fffc150e20df95cf0a2a699b946f7288060ca81794fe816bf3650639` | yes |
| 18 | `ARCH_DOCS_COVERAGE_MAP.md` | 19559 | `b92073cd2d509f0344a8a73b871c5d4ae59f33e99b7a65d8b33359debf58ad68` | yes |
| 19 | `ARCH_DOCS_HEADING_INVENTORY.md` | 58025 | `8145fe1eca160911542c1a610629b8546d4c927b147efba2ed3783224fff2e7b` | yes |
| 20 | `ARCH_DOCS_MERGE_MATRIX.md` | 22898 | `b8e6626199bca608b7ba55127044ec9baeed3ccbfde69eca8bee7dca72693bcf` | yes |
| 21 | `ARCH_DOCS_READ_NOTES.md` | 52295 | `ee56e075177c0ad0f515fd940bd202162a26c0d69981dc3d134ead838a7410cd` | yes |
| 22 | `swap\README.md` | 6631 | `2f39d9ed6e3b0c99ad5d121dae2c2dfed96017087ce14ebc43bead1f374f3dae` | yes |

Destinations checked and absent: each path in the Appendix M destination column, including `zola-architecture/README.md`, `zola-architecture/ARCH_DOCS_DECISIONS.md`, and `zola-architecture/audit/arch-docs-swap/`.

## Inventory of `zola-architecture/`

Top-level files: exactly the 39 in Appendix L. No extra file, no missing file. On-disk size and SHA-256 match Appendix L for every row, including row 10 (40,370 bytes, `2736c903f5d4b42b4fd6ab9ad6bfd21968793db24b40db550b2b5dfce73f44e5`).

| # | File | Bytes | SHA-256 | Match |
|---|---|---|---|---|
| 1 | `Zola Autonomous Behavior Architecture.md` | 32767 | `5e9df761157d8ec18a477646d4397c5e137b01c3b776650a74984e4c052851d3` | yes |
| 2 | `Zola Conversational Attention Architecture.md` | 32739 | `baf1b8693e6f9ebe563f541936ea4a6ae227f1e57efd44ee851d564e95ec1b5d` | yes |
| 3 | `Zola Conversational Continuity Architecture.md` | 28604 | `e9676df61ca99fce120a6b74df5f40f28f168ca598d0adb9ea4ac9416d793491` | yes |
| 4 | `Zola Distributed Presence Architecture.md` | 31380 | `fca402968178b40871c377baa306e7b686f11d5c9abe36b41b78078b9e3c4145` | yes |
| 5 | `Zola Environmental Awareness Architecture.md` | 37515 | `6360a057d6e69f652f8611c398eb73a25b98c5812d115e78abbb15d2bac733f1` | yes |
| 6 | `Zola Environmental Perception Architecture.md` | 35763 | `d254594c96de661498d0036c5be21c47805cfbf59c8b7e368203065e8b081cf6` | yes |
| 7 | `Zola Identity and Personality Framework.md` | 33544 | `cebae883ebcd8f7c3916c48a0a34a877a897cb76b5184b7acff1fb6c24fe2cb8` | yes |
| 8 | `Zola Master Architecture Plan.md` | 40843 | `c618574fc6a5a7acf6babc94be215677b3a40db0c623bc8319894f56d9fdd20c` | yes |
| 9 | `Zola Memory Hierarchy Architecture.md` | 37137 | `6a6542e40d87da3de58bf0c49e99113d4af3579f9b08d186ae530db470f1b442` | yes |
| 10 | `Zola Privacy and Data Ownership Plan.md` | 40370 | `2736c903f5d4b42b4fd6ab9ad6bfd21968793db24b40db550b2b5dfce73f44e5` | yes |
| 11 | `Zola Streaming Cognition Architecture.md` | 36028 | `19042e794b3380187526955511cd0930a65e81f1eb699b98c6343d9fd81fb619` | yes |
| 12 | `Zola_Agent_Map.md` | 22613 | `f2a6b62b254ccef3c04d0a0460fd89618e1bc2bc724b7f84172554cc667dddd5` | yes |
| 13 | `Zola_Architecture_Cognitive_Engagement.md` | 25916 | `32f91b5acf9f8cb285d8133ab2e65e9c7c87edff2bed35ad691ae695fb359fc1` | yes |
| 14 | `Zola_Architecture_Context_Injection.md` | 41966 | `875356eb4b3ac6d150f1f5c6c9c54662f1e408a90cef4ecbe68fb06a2bdf2e8f` | yes |
| 15 | `Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md` | 39313 | `38697ea4aad261e5901573f9f831555f960d612d2596edc2adc605117540c7b0` | yes |
| 16 | `Zola_Architecture_Distributed_Presence_Device_Capabilities.md` | 28950 | `4d68a7151c716967a683d20b7fba9d5a74d6ef9e6fd5c9d820c9266a34dd4027` | yes |
| 17 | `Zola_Architecture_Environmental_Event_Bus_and_User_State_Model.md` | 47218 | `b000a9cf6ffd59b52b807bc67eb4e49212cc70d69768e657dfd5350611b3d3d3` | yes |
| 18 | `Zola_Architecture_Identity_Source_Consolidation_Plan.md` | 39031 | `6dcf3e319952fe8c64c1b809e95e291fa3146ed382ba8f35bac33301fcb96b75` | yes |
| 19 | `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` | 54033 | `b4e3702e42e4db2c337872482bfeee4b76598d467e8c056b165a8497315f6340` | yes |
| 20 | `Zola_Architecture_Memory_Agency.md` | 39591 | `9c4348e24c3e19fbc44c4c04cbeda2676a88a0f1ccf174ea7f8d6b38f25815db` | yes |
| 21 | `Zola_Architecture_Memory_Ethics_and_Privacy.md` | 33227 | `5f806d2b3f22fdda3d1402eee77171d67e5ddda58f8e44d90c4a0cf68d454c0b` | yes |
| 22 | `Zola_Architecture_Perception_Memory.md` | 30302 | `a1efff388d08923379916106bfb890897b9514bd0e6e12ca36e6a7de3943cc46` | yes |
| 23 | `Zola_Architecture_Perceptual_Input_Layer.md` | 38929 | `5aad024d447fe9bb8f4fd2fc0a91a1770c82db0c88aad13c0b513d0b92489663` | yes |
| 24 | `Zola_Architecture_Relationship_Inference.md` | 22195 | `e4253fb3ba7c08518b0bd7855d297b6d2c324cc71620f6a06ca7907b4f7d4b5f` | yes |
| 25 | `Zola_Attention_Relevance_Engine_Architecture.md` | 27802 | `9719917dab33dd634eb0b98e8180bbc350348481d2f76c836863e05d586526ac` | yes |
| 26 | `Zola_Capability_Acquisition_Architecture.md` | 10402 | `f431f9b9cfeb554b2dd24783c0b3a830ee0a1b144424e4402e952ec4fd95251f` | yes |
| 27 | `Zola_Cognitive_Engine_Architecture.md` | 18730 | `72423f3a81ce95465329d8e8785f12b7740e79250a1bde5e129e7131bbe5e558` | yes |
| 28 | `Zola_Communication_Intelligence_Architecture.md` | 7074 | `341d032014d36a22f90edcf7b8bf4931808b2e34ddfffed30c80944e0ccfaa86` | yes |
| 29 | `Zola_CrossDomain_Correlation_Architecture.md` | 10028 | `25162bfb198f9deebd2055640018afab2b7febd626188bf7fc67569cefa07b82` | yes |
| 30 | `Zola_Presence_UI_Architecture.md` | 48095 | `79cefe4df14157163c1011939e8cc6d2c2ebb6657dd46181e2305cb5226b0d86` | yes |
| 31 | `Zola_Relational_Calibration_Architecture.md` | 31313 | `eb6bd5448c682e951cce3b6ed82dcd7566c350847d8feafa8d3bed5a567aad05` | yes |
| 32 | `Zola_Relational_Continuity_Architecture.md` | 30093 | `29ff8533491b4d017e269f7d7c08960a9b8d6e80ae3bd1afd3bcc01aea3e839e` | yes |
| 33 | `Zola_Relational_Intelligence_Layer_Architecture.md` | 20859 | `296232ee4bb579e4d1226038fbb5079fad4c83e2e0f1d6c46499251d68325af1` | yes |
| 34 | `Zola_SelfModel_Awareness_Architecture.md` | 28277 | `807903a07a31ed7f3ec52b2f9fd7335f906a5453edddf7da20a668da14b2e9b8` | yes |
| 35 | `Zola_Session_Identity_Architecture.md` | 7243 | `ea2f14ca803c5f461c25d321ec4ede89319c6a1d5c67e90eb3717d11837e0179` | yes |
| 36 | `Zola_Sms_Intelligence_Architecture.md` | 21669 | `2fac0f33e59ef2bc827ac0ffc3b6c273556e087e1db480a16bba9ebeabd88809` | yes |
| 37 | `Zola_SocialGraph_Reasoning_Architecture.md` | 28242 | `6468eacb969ef2370f675aaa57c6176220192223227264367d5b0778b6fc63b4` | yes |
| 38 | `Zola_Temporal_Reasoning_Architecture.md` | 22643 | `ee5f7c6bb97866f4281f4e54dd800fd8fc4f0b1f1b4249dcd155551a81f0f620` | yes |
| 39 | `Zola_Tool_Authorization_Architecture.md` | 10923 | `b5ee3f7bb193a0dae5ffb62797e5283a5f5309ff9435428354349af7bc414fc4` | yes |

Subfolders, untouched in Phase 1 except this progress doc:

- `audit/` — `p10pre-phase10`, `p3pre-presence-ui`, `p4pre-conversation`, `p5pre-phase5`, `p6pre-phase6`, `p7pre-phase7`, `p8pre-phase8`, `p9pre-phase9`, `voicepre-standalone`, `winh-hermes-gap`. Phase 3 adds `audit/arch-docs-swap/` only.
- `identity/` — `MEMORY_CONVENTIONS.md` (out of scope), `SOUL.md`, `VOICE_CONFIG.md`. The last two are Phase 5 report and Phase 6 edits only.
- `lore/` — `build-plans/`, `prompts/`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`. This task adds only `lore/prompts/progress/ARCH-SWAP_Progress.md`.

No other top-level entry.

## Repo rules

`.gitattributes` has no `*.md` entry. The file is:

```
# P3-SHELL — P3-D12
*.ttf binary
*.glb binary
*.jar binary
gradlew text eol=lf
*.bat text eol=crlf
```

No `.cursor/rules/`, no `AGENTS.md`, no `CLAUDE.md`, and no `.github/` anywhere in the repo. Root files besides those are `.gitattributes` and `.gitignore`. No editor or agent rule applies to docs or to `zola-architecture/`.
## Phase 2 — Reference census

Read-only. Searched the repo with ripgrep, respecting gitignore, excluding `.git` and the 39 Appendix L files. The 22 approved files are not in the repo. Each Appendix L stem was searched with and without `.md` and with and without a folder prefix (the stem covers both). Space-containing names were also searched URL-encoded (`%20`). Short names searched: Master Architecture Plan, Agent Map, Memory Agency, Living Voiceprint, Context Injection.

No `%20` hit. No hit outside `zola-architecture/`. No hit in code, config, a README, an SOP, or an editor rule. The repo has no SOP file, no README, and no `.cursor/`, `AGENTS.md`, `CLAUDE.md`, or `.github/`.

**Active references: none.** Nothing for Brian to approve as an edit. Phase 3 applies no reference edits unless he adds one.

**Historical references: 116** outside this progress doc, plus **42** inside this progress doc's Phase 1 inventory (the Appendix L table and the notes that name the privacy plan). All 158 are historical under G-HISTORY: lore entries, closed-phase build plans, progress docs, and audits. They are not rewritten. Their successor pointer is the Retired documents table in the new `zola-architecture/README.md`.

Phase 4 re-census: the 116 hits below must be unchanged in file, line, and text. Hits inside this progress doc grow when this section is added; they are this track's own record, not new external references.

| File | Line | Quote | Class |
|---|---|---|---|
| `lore/ROADMAP.md` | 472 | - Companion strawman (v0.1, proposals only): `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_02_PrivacyRetentionAccess.md` | 6 | Requirements extracted **first** from `Zola_Architecture_Memory_Ethics_and_Privacy.md` and `Zola Privacy and Data Ownership Plan.md` (abstract rules only — Android/sensor/camera... | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_02_PrivacyRetentionAccess.md` | 14 | ### A.1 Ethics — `Zola_Architecture_Memory_Ethics_and_Privacy.md` | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_02_PrivacyRetentionAccess.md` | 27 | ### A.2 Privacy Plan — `Zola Privacy and Data Ownership Plan.md` (abstract only) | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_02_PrivacyRetentionAccess.md` | 138 | **Against:** P-UI audit log; P-GUARANTEE “confirmed and logged”; P-RET extension must be logged (n/a because no windows); Ethics write metadata (source/scope/authority/freshness... | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_01_StorageOwnership.md` | 6 | Zola lenses: `Zola Memory Hierarchy Architecture.md` (layers 0–6, authority order, promotion) and `Zola_Architecture_Memory_Agency.md` (write pipeline, salience, consolidation).... | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_01_StorageOwnership.md` | 29 | - `USER.md` is a single “who the user is” profile (`MEMORY_BLOCK_HEADERS["user"]` L20–21). Zola Layer 5 requires **context-scoped** behavioral preferences (`Zola Memory Hierarch... | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_01_StorageOwnership.md` | 70 | `$HERMES_HOME/skills/` is procedural memory (SKILL.md packages). Confirmed separate in Phase 4 (`WINH04-AUD-08`). Zola Hierarchy does not treat skills as a numbered layer; Memor... | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_01_StorageOwnership.md` | 132 | ## 4. Write-classification vs Memory Agency (factual) | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_01_StorageOwnership.md` | 134 | `Zola_Architecture_Memory_Agency.md` Memory Write Pipeline requires source, scope, authority, freshness, and a Durable Write Authority decision before a fact lands. Hermes `memo... | historical |
| `audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md` | 135 | \| WINH08-AUD-01 \| WINH08 \| Tool Calling, Subagents & Scheduled Automation \| [PARTIAL] \| MEDIUM \| several worker paths exist; not Agent Map prepare-only categories. \| | historical |
| `audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md` | 761 | ### S6 — Warm-start / speculation vs Agent Map | historical |
| `audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md` | 764 | > Hermes is not Agent 8/4/9 (`AUD-07`, `AUD-13`). Should the Windows client add a warm-cache for responsiveness, or accept less speculative behavior than the Android Agent Map (... | historical |
| `audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md` | 1031 | The fresh-start / capability-not-implementation framing in "Recorded scope decisions" held across all twelve phases without a further correction. Android-named libraries and OS ... | historical |
| `audit/winh-hermes-gap/Zola_WINH00_Audit_05_DecisionsNeeded.md` | 58 | ### S6 — Warm-start / speculation vs Agent Map | historical |
| `audit/winh-hermes-gap/Zola_WINH00_Audit_05_DecisionsNeeded.md` | 61 | > Hermes is not Agent 8/4/9 (`AUD-07`, `AUD-13`). Should the Windows client add a warm-cache for responsiveness, or accept less speculative behavior than the Android Agent Map (... | historical |
| `audit/winh-hermes-gap/Zola_WINH00_Audit_02_FindingsAggregation.md` | 119 | \| WINH08-AUD-01 \| WINH08 \| Tool Calling, Subagents & Scheduled Automation \| [PARTIAL] \| MEDIUM \| several worker paths exist; not Agent Map prepare-only categories. \| | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 57 | > Environmental Awareness / Perception (Zola Environmental Awareness Architecture, Zola Environmental Perception Architecture, Zola_Architecture_Environmental_Event_Bus_and_User... | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 61 | > `Zola_Cognitive_Engine_Architecture.md` (the `CognitivePrepWorker` "Prep Kitchen Model," a durable persisted initiative queue, curiosity-derived triggering, and three named co... | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 137 | Document of Truth: Master Architecture Plan §20 (Centralized Authority Model), Core Architectural Principles (Single Authority Ownership, Truth Ownership Rule, Speech Authority ... | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 149 | Document of Truth: `Zola_Agent_Map.md` (Core Rule, per-agent Must-never, staleness/TTL/confidence, Agent 8 / 14 / 15). Tool-calling held only to the Core Rule line and Agent 8's... | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 161 | Document of Truth: Master Plan §3 Current Sequential Model only (not Long-Term Streaming), §12 Conversational Attention Authority (reserved from WINH07), External API Strategy T... | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 173 | Document of Truth: `Zola_Communication_Intelligence_Architecture.md` (email + SMS intelligence, shared principles), `Zola_Sms_Intelligence_Architecture.md` (contact-gate, thread... | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 197 | Document of Truth: `Zola_Relational_Intelligence_Layer_Architecture.md` plus Temporal, Social Graph, Continuity, Calibration. SMA cited `WINH05-AUD-10`–`13` (not re-read). Half ... | historical |
| `audit/winh-hermes-gap/Zola_WINH_Audit_PROGRESS.md` | 327 | - WINH08-AUD-01 — [PARTIAL] — MEDIUM — `delegate_tool.py`; `background_review.py`; `cron/scheduler.py`; `heartbeat.py` — several worker paths exist; not Agent Map prepare-only c... | historical |
| `audit/winh-hermes-gap/Zola_WINH02_Audit_01_SurfaceInventory.md` | 9 | Zola evaluation lenses (Master Architecture Plan: centralized authority, L1056 / L1162; "Final authority determines response behavior," L1124; fail-closed when uncertain): if a ... | historical |
| `audit/winh-hermes-gap/Zola_WINH12_Audit_04_ContinuityAndCalibration.md` | 6 | Zola source: `Zola_Relational_Continuity_Architecture.md`, `Zola_Relational_Calibration_Architecture.md`. Cite `WINH05-AUD-03`/`08` (style is config/presets, no learned style-pr... | historical |
| `audit/p3pre-presence-ui/Zola_P3PRE_Audit_PROGRESS.md` | 36 | - **G-ARCH:** `Zola_Presence_UI_Architecture.md` is truth except K1 (GLB replaces SVG). Conflicts are findings. | historical |
| `audit/p3pre-presence-ui/Zola_P3PRE_Audit_PROGRESS.md` | 133 | - `zola-architecture/Zola_Presence_UI_Architecture.md` (full, §1–§25) | historical |
| `audit/p3pre-presence-ui/Zola_P3PRE_Audit_PROGRESS.md` | 134 | - `zola-architecture/Zola Master Architecture Plan.md` Windows Track notes (`S5`, `C1`, `C3`, Tier 1) and endpoint / presence sections | historical |
| `audit/winh-hermes-gap/Zola_WINH12_Audit_03_SocialGraphReasoning.md` | 6 | Zola source: `Zola_SocialGraph_Reasoning_Architecture.md` (full). Depends on Temporal (Phase 2) and SMA confidence pattern (`WINH05-AUD-10`–`13` — cite, do not re-derive). Fresh... | historical |
| `audit/winh-hermes-gap/Zola_WINH12_Audit_02_TemporalFoundation.md` | 6 | Zola source: `Zola_Temporal_Reasoning_Architecture.md` (full); Relational Intelligence master “Shared Infrastructure” and “Shared Data Contracts.” Fresh-start: capability, not F... | historical |
| `audit/winh-hermes-gap/Zola_WINH12_Audit_02_TemporalFoundation.md` | 14 | Zola: elapsed time is a first-class relational signal (“three weeks since you mentioned X”), not storage metadata (`Zola_Temporal_Reasoning_Architecture.md` L13–20, L35–55). | historical |
| `audit/p3pre-presence-ui/Zola_P3PRE_Audit_05_HudDockSources.md` | 35 | Location, facts only. `Windows.Devices.Geolocation` can supply a coordinate. The API asks for location permission. A civic place name is not in that coordinate by itself; a reve... | historical |
| `audit/p3pre-presence-ui/Zola_P3PRE_Audit_04_ArchitectureMap.md` | 3 | Re-read of `Zola_Presence_UI_Architecture.md` against Phase 2–4. K1: the GLB replaces the SVG. Android wave status is not a Windows score. | historical |
| `audit/winh-hermes-gap/Zola_WINH11_Audit_02_SecretsStorage.md` | 6 | Zola source: `Zola Privacy and Data Ownership Plan.md` §9 Encryption and Storage Security (data at rest, memory-specific encryption, Access Control). One Access Control line is ... | historical |
| `audit/p3pre-presence-ui/Zola_P3PRE_Audit_01_ClientSurfaceMap.md` | 5 | Labels are against `Zola_Presence_UI_Architecture.md` §15–§18 (dock, panels, functional integration, authority). K1 does not change those sections. | historical |
| `audit/winh-hermes-gap/Zola_WINH10_Audit_06_Synthesis.md` | 6 | Document of Truth: `Zola_Communication_Intelligence_Architecture.md`, `Zola_Sms_Intelligence_Architecture.md`. Cross-refs: `WINH04-AUD-02`/`06`, `WINH07-AUD-07`, `WINH08-AUD-02`... | historical |
| `audit/winh-hermes-gap/Zola_WINH10_Audit_03_ConfirmedSendFlow.md` | 6 | Zola source: `Zola_Sms_Intelligence_Architecture.md` **Send Is Confirmed, Not Autonomous** and the two-step action flow (offer → user content → read-back → confirm → send; `_con... | historical |
| `audit/winh-hermes-gap/Zola_WINH10_Audit_02_InboundIntelligence.md` | 6 | Zola source: `Zola_Communication_Intelligence_Architecture.md` Shared Principles + both domains; `Zola_Sms_Intelligence_Architecture.md` Core Principles and System Components. C... | historical |
| `audit/winh-hermes-gap/Zola_WINH09_Audit_06_Synthesis.md` | 6 | Document of Truth: Master Plan §3 Current Sequential Model only (not Long-Term Streaming), §12 Conversational Attention Authority, External API Strategy Tier 1, `Zola_Architectu... | historical |
| `audit/winh-hermes-gap/Zola_WINH09_Audit_06_Synthesis.md` | 76 | Phase 4 (Voice Identity) is **near-total scratch work** if the Living Voiceprint *capabilities* are in scope for this integration. That is not softened: Hermes has nothing to wr... | historical |
| `audit/voicepre-standalone/Zola_VOICEPRE_Audit_01_Baseline.md` | 50 | \| Master plan §12 \| `zola-architecture/Zola Master Architecture Plan.md` \| No version header. §12 read at lines 610–666. Target, not a locked build decision. \| | historical |
| `audit/voicepre-standalone/Zola_VOICEPRE_Audit_01_Baseline.md` | 51 | \| Conversational Attention \| `zola-architecture/Zola Conversational Attention Architecture.md` \| No version header. Target. \| | historical |
| `audit/voicepre-standalone/Zola_VOICEPRE_Audit_01_Baseline.md` | 52 | \| Conversational Continuity \| `zola-architecture/Zola Conversational Continuity Architecture.md` \| No version header. Target. \| | historical |
| `audit/voicepre-standalone/Zola_VOICEPRE_Audit_01_Baseline.md` | 53 | \| Streaming Cognition \| `zola-architecture/Zola Streaming Cognition Architecture.md` \| No version header. Target. \| | historical |
| `audit/voicepre-standalone/Zola_VOICEPRE_Audit_01_Baseline.md` | 54 | \| Privacy and Data Ownership \| `zola-architecture/Zola Privacy and Data Ownership Plan.md` \| No version header. \| | historical |
| `audit/voicepre-standalone/Zola_VOICEPRE_Audit_01_Baseline.md` | 55 | \| Presence UI \| `zola-architecture/Zola_Presence_UI_Architecture.md` \| No version header. \| | historical |
| `audit/voicepre-standalone/Zola_VOICEPRE_Audit_01_Baseline.md` | 56 | \| Distributed presence \| `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` \| v0.1, 2026-10-03, strawman. Proposals only. \| | historical |
| `audit/winh-hermes-gap/Zola_WINH09_Audit_04_VoiceIdentity.md` | 6 | Zola source: `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` in full. **Capability requirements only** — not Android `CampPlus` / sherpa-onnx / `AudioRecord` as things Her... | historical |
| `audit/winh-hermes-gap/Zola_WINH09_Audit_04_VoiceIdentity.md` | 42 | Living Voiceprint: embeddings stay on-device; never cloud-sync. | historical |
| `audit/winh-hermes-gap/Zola_WINH09_Audit_03_VoicePipelineArchitecture.md` | 62 | ## 4. Barge-in during TTS (existence, not Living Voiceprint mechanics) | historical |
| `audit/winh-hermes-gap/Zola_WINH09_Audit_03_VoicePipelineArchitecture.md` | 64 | Living Voiceprint §1 excludes barge-in *mechanics*; this item only asks whether interruption **exists**. | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_06_Synthesis.md` | 6 | Document of Truth: `Zola_Agent_Map.md`. Tool-calling held only to the Core Rule and Agent 8’s two Must-never lines. Cross-refs: `WINH03-AUD-02/05`, `WINH04-AUD-02`, `WINH06-AUD-... | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_06_Synthesis.md` | 18 | \| WINH08-AUD-01 \| PARTIAL \| MEDIUM \| `delegate_tool.py`; `background_review.py`; `cron/scheduler.py`; `heartbeat.py` \| Several worker paths exist; not Agent Map prepare-only cat... | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_06_Synthesis.md` | 37 | `[OBSERVATION]` rows (AUD-09, AUD-10) count in the table; they are not scored as Agent Map misses. | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_06_Synthesis.md` | 43 | **Subagents / workers.** Hermes is not a prepare-only Agent Map. It has `delegate_task` children (full tool loop minus a small blocklist), a post-turn background-review fork (di... | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_06_Synthesis.md` | 91 | 4. **Warm-start / speculation.** Hermes is not Agent 8/4/9 (AUD-07, AUD-13). Should the Windows client add a warm-cache for responsiveness, or accept less speculative behavior t... | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_SYNTHESIS.md` | 5 | INFO (lore vs strawman, no finding ID): `S73` says the strawman `Zola_Architecture_Distributed_Presence_Device_Capabilities.md` predates Phases 6–8, that its DP entries are prop... | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_PROGRESS.md` | 34 | - `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_PROGRESS.md` | 38 | - Background only: `zola-architecture/Zola Distributed Presence Architecture.md` | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_02_SubagentArchitecture.md` | 6 | Zola source: `Zola_Agent_Map.md` Core Rule (“Agents prepare. The core decides. No agent writes to memory, speaks, executes tools, or holds routing authority.”), every agent’s Mu... | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_02_SubagentArchitecture.md` | 30 | **Label:** `[PARTIAL]` `WINH08-AUD-01` (MEDIUM) — Hermes has real background/subagent code paths; they are not the Agent Map’s prepare-only fleet. | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_02_SubagentArchitecture.md` | 62 | **Label:** `[GAP]` `WINH08-AUD-03` (MEDIUM) against the Agent Map staleness/confidence pattern. | historical |
| `audit/winh-hermes-gap/Zola_WINH08_Audit_02_SubagentArchitecture.md` | 84 | \| WINH08-AUD-01 \| PARTIAL \| MEDIUM \| `delegate_tool.py`; `background_review.py`; `cron/scheduler.py`; `heartbeat.py` \| Several worker paths exist; not Agent Map prepare-only cat... | historical |
| `audit/winh-hermes-gap/Zola_WINH07_Audit_06_Synthesis.md` | 6 | Zola Document of Truth: Master Architecture Plan §20 (Centralized Authority Model), Core Architectural Principles (Single Authority Ownership, Truth Ownership Rule, Speech Autho... | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_09_Lessons.md` | 3 | Every item is BACKGROUND. Repository B lore, decisions, open questions, and audits are not Phase 10 authority and are not findings. The Windows file `Zola Distributed Presence A... | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_09_Lessons.md` | 8 | - BACKGROUND: `Zola_Agent_Map.md` describes a future notification classifier (message vs alert vs spam). The listener that exists stores raw status-bar entries and extracts titl... | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_09_Lessons.md` | 15 | - BACKGROUND: old perceptual-layer notes (`Zola_Architecture_Perceptual_Input_Layer.md`, Phase 18 plans) say a persistent watchdog wants a foreground service and a visible notif... | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_09_Lessons.md` | 22 | - BACKGROUND: `Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md` says FCM is unreliable under aggressive battery optimization and that critical coordination... | historical |
| `audit/winh-hermes-gap/Zola_WINH07_Audit_04_RoutingAuthority.md` | 6 | Zola source: Core Architectural Principles — Single Authority Ownership, Provider Abstraction Philosophy; Agent Map Core Rule (“…or holds routing authority”). Surfaces are WINH0... | historical |
| `audit/winh-hermes-gap/Zola_WINH07_Audit_04_RoutingAuthority.md` | 14 | **Zola / Agent Map:** one owner of routing authority. Subsystems do not independently resolve “which agent instance.” | historical |
| `audit/winh-hermes-gap/Zola_WINH07_Audit_03_TrustPermissionFramework.md` | 6 | Zola source: Master Architecture Plan §13 Trust, Permission, and Privacy Framework (trust as inspectable, contextual, never assumed; permissions as explicit behavioral boundarie... | historical |
| `audit/winh-hermes-gap/Zola_WINH05_Audit_05_SessionIdentity.md` | 6 | Zola source: `Zola_Session_Identity_Architecture.md` (`SessionRecord`, single mint site, foreground/background + 30s same-device grace, per-user with device as provenance, `sess... | historical |
| `audit/winh-hermes-gap/Zola_WINH07_Audit_02_ResponseAuthority.md` | 6 | Zola source: Master Architecture Plan §20 Centralized Authority Model; Core Architectural Principles — Single Authority Ownership. Agent Map Core Rule: “Agents prepare. The core... | historical |
| `audit/winh-hermes-gap/Zola_WINH07_Audit_02_ResponseAuthority.md` | 91 | **Label:** `[GAP]` `WINH07-AUD-04` (HIGH) against Single Authority Ownership / Agent Map Core Rule. There is no code-level core; co-location in one process is not enforcement. | historical |
| `audit/winh-hermes-gap/Zola_WINH05_Audit_04_SelfModelAwareness.md` | 6 | Zola source: `Zola_SelfModel_Awareness_Architecture.md` (`SelfBeliefBlock`, hedging vs locked identity, read-only authority, no user-facing confidence display). | historical |
| `audit/winh-hermes-gap/Zola_WINH05_Audit_03_IdentitySourceConsolidation.md` | 6 | Zola source: `Zola_Architecture_Identity_Source_Consolidation_Plan.md` (one canonical source, derived builders, name in one field, Style Profile store, locked vs evolvable, nume... | historical |
| `audit/winh-hermes-gap/Zola_WINH05_Audit_02_IdentityPersonalityFramework.md` | 6 | Zola source: `Zola Identity and Personality Framework.md` (Identity Seed §1, locked vs adaptive, Growth Rings §2, Style Profile §3, Feedback Loop §4, Anchors §5, Memory-driven p... | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_04_HierarchyReconciliation.md` | 6 | Zola source of structure: `Zola Memory Hierarchy Architecture.md` (real layers 0–6 plus authority, read/write, promotion, decay, consolidation, topic stack, weighting, injection... | historical |
| `audit/winh-hermes-gap/Zola_WINH04_Audit_04_HierarchyReconciliation.md` | 166 | **Zola (in-scope extract):** observations are not facts; they carry confidence + timestamp; they must earn promotion through layers or they pollute long-term truth (`Zola_Archit... | historical |
| `audit/p10pre-phase10/ZW_P10PRE_Audit_05_Transport_Storage.md` | 72 | \| Firestore initiative / deferred queues \| `memory` package \| Brain state. Not audited internally. Not an SMS transport queue. A background architecture note says a shared defer... | historical |
| `lore/prompts/progress/P1-CLIENT_Progress.md` | 35 | None at start. Documents of truth read before Phase 1: `PHASE1_BUILD_PLAN.md` (Track 1, `P1-D01`, `P1-D02`), `Zola Master Architecture Plan.md` Section 19, `ROADMAP.md`, `DESIGN... | historical |
| `lore/OPEN_QUESTIONS.md` | 15 | `Zola_Sms_Intelligence_Architecture.md` (on-demand read/search/send, | historical |
| `lore/OPEN_QUESTIONS.md` | 19 | **Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision):** The brainstorm favored an Android companion app over Phone Link or Google Messages for Web (neither has a public ... | historical |
| `lore/OPEN_QUESTIONS.md` | 421 | - **S73 — Android companion and distributed presence.** Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Brian's strawman `zola-architecture/Zola_Architecture_Distrib... | historical |
| `lore/prompts/progress/P10-LORE_Progress.md` | 45 | - `git log 8842d315..HEAD` on `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`, `identity/`, and `Zola Privacy and Data Ownership Plan.md` is empty. Tracks 5 and 6 did n... | historical |
| `lore/DESIGN_DECISIONS.md` | 61 | - **C9/C10 — Both architecture docs written.** `Zola_Capability_Acquisition_Architecture.md` | historical |
| `lore/DESIGN_DECISIONS.md` | 62 | and `Zola_Tool_Authorization_Architecture.md` are written, covering | historical |
| `lore/DESIGN_DECISIONS.md` | 98 | speculative behavior than the Android Agent Map for now; revisit if | historical |
| `lore/DESIGN_DECISIONS.md` | 113 | `Zola_Communication_Intelligence_Architecture.md` and | historical |
| `lore/DESIGN_DECISIONS.md` | 114 | `Zola_Sms_Intelligence_Architecture.md` (Daily Brief) is deferred. | historical |
| `lore/prompts/progress/P2-WAKE_Progress.md` | 37 | None at start. Documents of truth read before Phase 1: `PHASE2_BUILD_PLAN.md` v1.1 (Grounding summary wake bullets, `P2-D04`, `P2-D07`, `P2-D08`, `P2-D10`, `P2-D12`, Track 3), `... | historical |
| `lore/prompts/progress/P2-LORE_Progress.md` | 59 | \| `Zola Master Architecture Plan.md` \| Tier 1 Windows Track note: Edge TTS + local faster-whisper (`P2-D02`) \| | historical |
| `lore/prompts/progress/P2-LORE_Progress.md` | 111 | - `zola-architecture/Zola Master Architecture Plan.md` (Tier 1 Windows Track note only) | historical |
| `lore/prompts/progress/P2-SPEAK_Progress.md` | 37 | None at start. Documents of truth read before Phase 1: `PHASE2_BUILD_PLAN.md` v1.1 (Grounding summary, `P2-D03`, `P2-D06`, `P2-D07`, `P2-D08`, `P2-D12`, Track 2), `P2-VOICE_Prog... | historical |
| `lore/prompts/progress/P2-VOICE_Progress.md` | 41 | None at start. Documents of truth read before Phase 1: `PHASE2_BUILD_PLAN.md` (Grounding summary, `P2-D01`–`P2-D11`, Track 1), `Zola Master Architecture Plan.md` (Vocal Computin... | historical |
| `lore/build-plans/PHASE5_BUILD_PLAN.md` | 251 | - `Zola_Temporal_Reasoning_Architecture.md`; | historical |
| `lore/build-plans/PHASE5_BUILD_PLAN.md` | 477 | `Zola_Temporal_Reasoning_Architecture.md`, WINH12-02, and session start dates in | historical |
| `lore/build-plans/PHASE3_BUILD_PLAN.md` | 159 | These parts of `Zola_Presence_UI_Architecture.md` are superseded for Windows: | historical |
| `lore/build-plans/PHASE3_BUILD_PLAN.md` | 1153 | - `Zola_Presence_UI_Architecture.md` §3–§9 and §23. | historical |
| `lore/build-plans/PHASE3_BUILD_PLAN.md` | 1419 | ### Zola_Presence_UI_Architecture.md (named explicitly in scope for the lore-closeout prompt only) | historical |
| `lore/build-plans/PHASE2_BUILD_PLAN.md` | 1008 | ### Zola Master Architecture Plan.md (architecture doc, named explicitly as in scope for the lore-closeout prompt only) | historical |
| `lore/prompts/progress/P3-LORE_Progress.md` | 10 | - Presence UI architecture path: `zola-architecture/Zola_Presence_UI_Architecture.md` | historical |
| `lore/prompts/progress/P3-LORE_Progress.md` | 42 | \| Presence UI Architecture \| `zola-architecture/Zola_Presence_UI_Architecture.md` \| read (Canonical Visual Direction, ?4 PresenceMode, ?5??9 motion, ?14 HUD) \| | historical |
| `lore/prompts/progress/P3-LORE_Progress.md` | 286 | 3. Architecture path confirmed: `zola-architecture/Zola_Presence_UI_Architecture.md`. | historical |
| `lore/prompts/progress/P3-LORE_Progress.md` | 704 | ### KC4 ? `Zola_Presence_UI_Architecture.md` (notes only) | historical |
| `lore/prompts/progress/P5-LORE_Progress.md` | 363 | Inputs: `Zola_Temporal_Reasoning_Architecture.md`, WINH12-02. Phase 6, | historical |
| `lore/prompts/progress/P9-LORE_Progress.md` | 891 | `zola-architecture/Zola Privacy and Data Ownership Plan.md`. Not edited. | historical |
| `lore/prompts/progress/P9-LORE_Progress.md` | 986 | \| `Zola Privacy and Data Ownership Plan.md` \| L327 and L352 as proposed. Gemini bullets were not edited (L333, L334, and the same names at L425 and L431). \| | historical |
| `lore/prompts/progress/P9-RANK_Progress.md` | 551 | - `Zola Privacy and Data Ownership Plan.md` lines 327 and 352 say mail content stays off the cloud and that raw communication content is not transmitted. P9-D08 sends a trimmed ... | historical |
| `lore/prompts/progress/P9-KICKOFF_Progress.md` | 12 | - Strawman: `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` | historical |
| `lore/prompts/progress/P9-KICKOFF_Progress.md` | 32 | - **G-NO-CROSS-SCOPE:** do not open, read, search, or cite the Android Zola project, including `Zola Distributed Presence Architecture.md`. | historical |
| `lore/prompts/progress/P9-KICKOFF_Progress.md` | 45 | - `main` porcelain was exactly one line: `?? zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md`. | historical |
| `lore/prompts/progress/P9-KICKOFF_Progress.md` | 90 | \| 6 \| Strawman SHA-256 on disk and staged blob \| ✅ \| On disk and `git cat-file blob :zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md \\| sha256sum... | historical |
| `lore/prompts/progress/P9-KICKOFF_Progress.md` | 98 | - `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` | historical |

## Phase 2 — Phase 10 as-built check

Read-only. Compared the 22 approved files in `C:\Users\test\Dev\zola-arch-drafts` with `DESIGN_DECISIONS.md` Phase 10 (including P10-D18 and P10-D19), `OPEN_QUESTIONS.md` S90–S102, `ROADMAP.md` "Phase 10 — COMPLETE: Android Companion", and `P10-LORE_Progress.md`. No approved file was edited.

Closeout used for the comparison: Phase 10 is complete; P10-STORE, P10-INTAKE, P10-COMPANION, P10-NOTIFY (Track 4), P10-READ (Track 5) and P10-WATCH (Track 6) are merged. Shipped: texts and allowlisted notifications, `zola-phone`, code reads on request in a local voice, person and number watches, watched-text speech, forget by person or number. Limits that remain: code-only ranking (P10-D11), notifications never speak (P10-D15), no sending (P10-D17), Tailscale only (P10-D06), the phone decides visibility only (P10-D02), one person resolver whose only Phase 10 source is Google Contacts (P10-D18), untrusted content never creates a watch or a forget (P10-D19). The privacy page's Track 5 phone paragraph was published 2026-11-06 (`P10-LORE_Progress.md` Phase 6; ROADMAP S86).

### As-built table

| Doc | Line | Claim | Verdict |
|---|---|---|---|
| `swap/README.md` | 33 | "The 39 Android-era architecture documents that used to sit in this folder were retired on 2026-11-02." | **out of date** (expected). They are retired by this track, after the Phase 10 closeout. Closeout: tag `p10-closed` = `898b1e6f…`, 2026-11-06; ROADMAP Next item 1 is this swap. |
| `A14` §6 | 269 | "It was last updated on 2026-10-15 (P9)." | **out of date** (expected). Closeout: "The privacy page was read again after Brian published. Last updated November 6, 2026. The Track 5 Phone paragraph is on the page." (`P10-LORE_Progress.md` Phase 6). ROADMAP S86: the Track 5 phone paragraph was published on 2026-11-06. |
| `A14` §10 | 374 | "Privacy page \| published 2026-10-15" | **out of date.** Same closeout sentences as §6 line 269. |
| `A01` §3 | 173 | "State as of 2026-10-29. … Phase 10 is in flight: Tracks 1–3 are merged, Tracks 4–6 and the lore closeout are not done." | **out of date.** ROADMAP: "Phase 10 — COMPLETE: Android Companion." Tracks 4–6 are P10-NOTIFY, P10-READ and P10-WATCH, all merged. |
| `A01` §3.1 | 184 | Contact index "implemented (P10, phase not closed)" | **out of date** on the state clause. P10-D18: "Track 5 built the index. Track 6 uses it for watches and forget." |
| `A01` §3.1 | 186 | `zola-phone` "implemented, live-paired (T2–T3); phase not closed" | **out of date** on "phase not closed". ROADMAP shipped list includes `zola-phone`, supervised, Tailscale-only. The ownership description matches P10-D12. |
| `A01` §3.1 | 187 | Companion "T3: implemented, live-paired; notifications (T4): not built" | **out of date** on notifications. ROADMAP: "the companion: texts with masking, cursors and reads; notifications from the allowlist." P10-NOTIFY is merged. |
| `A01` §3.2 | 192–200 | Watcher or `zola-phone` writes items; phone items ranked by code; unprompted speech only for a watch Brian asked for | **matches** P10-D11 and P10-D15. |
| `A01` §4 | 237 | "Texts ranked by code only" is a temporary limit; P10-D11 keeps a judgment slot | **matches** P10-D11 and S99. |
| `A03` §13 | 551 | Text and notification content under the 7-day limit: "implemented (P10 Tracks 1–3; phase not closed; notifications not built)" | **out of date** on "phase not closed" and "notifications not built". P9-D07 annotation: "Phone content is under the same 7-day limit." Notifications shipped with Track 4. |
| `A03` §13 | 552 | Forget by person or number "implemented (P10, phase not closed)" | **out of date** on "phase not closed". ROADMAP shipped "forget by person or number" (P10-D14). |
| `A03` §13 | 553 | Contact index "implemented (P10, phase not closed)" | **out of date** on "phase not closed". P10-D18: Track 5 built the index. |
| `A03` §13 | 556 | "One identity per person across sources \| **not built** (contact index is a start)" | **matches** P10-D18's temporary limit (Contacts only) and S96. |
| `A04` §10 | 277 | Contact index "implemented (P10; phase not closed)" | **out of date** on "phase not closed". Same as A03 line 553. |
| `A04` §10 | 278 | "Watching a person across texts and email \| designed (P10 T6 not started)" | **out of date.** ROADMAP shipped "person and number watches" (P10-D13, P10-WATCH merged). |
| `A04` §10 | 279 | Forget by person or number "implemented (P10; phase not closed)" | **out of date** on "phase not closed". P10-D14 shipped. |
| `A04` §10 | 282 | "One identity per person across sources \| **not built**" | **matches** P10-D18's temporary limit and S96. |
| `A04` §11 | 293 | "Contact match is the only known-sender signal" (P10-D10) | **matches** P10-D10 and P10-D18's temporary limit. |
| `A05` §10 | 208 | "Text time = phone's received time \| implemented (P10; phase not closed)" | **out of date** on "phase not closed". The rule matches P10-D08, which shipped. |
| `A07` §10.3 | 354 | A code is read only on explicit request, on the direct path, by a local voice (R1, ARCH-36) | **matches** R1 and the roadmap line "reads codes only on request in a local voice". The sentence does not name Zira. R1's "Why a local voice" paragraph does: Brian, "I'm going with Zira." |
| `A07` §11 | 369–385 | The As built table has no code-read row | **not covered by the closeout** as a row. The shipped path is described in §10.3, not in this table. |
| `A08` governing records | 16 | "P10-D01–D17 (Phase 10 is not closed; T4–T6 are not built)" | **out of date.** Phase 10 is complete. Tracks 4–6 are merged. The list also stops before P10-D18 and P10-D19 (see the missing-decision report). |
| `A08` §3.1 | 90 | Contact index "implemented (index, P10)", cited as P10-D10 | **matches** the shipped index. It does not name P10-D18. |
| `A08` §3.1 | 92 | Texts "implemented, live-paired (T3); phase not closed" | **out of date** on "phase not closed". Texts shipped; history reads shipped with Track 5. |
| `A08` §3.1 | 93 | Notifications "designed (T4 not built)". Allowlist: Messages never forwarded, Life360, Visual Voicemail, Instagram; Messenger dropped | **out of date** on "T4 not built". The allowlist matches P10-D16. P10-NOTIFY is merged. |
| `A08` §10 | 312–313 | `zola-phone` implemented (T2–T3); phone controls visibility only | **matches** P10-D12 and P10-D02. These two rows do not say the phase is open. |
| `A08` §10 | 315 | "Disconnect reason codes on the phone link \| implemented" cited as P10-D16 | **not covered by the closeout.** P10-D16 is the allowlist. The closeout does not state a disconnect-reason-code decision. |
| `A08` §10 | 318 | Location, weather, traffic, device state from the phone "not built" | **matches.** ARCH-23 location history is not in the shipped list. |
| `A08` §11 | 328–330 | Notifications allowlist and never spoken; no sending; code-only ranking | **matches** P10-D15, P10-D16, P10-D17, P10-D11. |
| `A09` §11 | 249 | "Life360 place alerts (phone notifications) \| designed (P10 T4; A08)" | **out of date** on "designed (T4)". Track 4 shipped allowlisted notifications, including Life360. |
| `A09` §11 | 251 | "The only perception today is reported data: email, calendar, phone texts and notifications." | **matches** the shipped companion. It disagrees with the Life360 row above, which still says designed. |
| `A10` §10 | 376 | Phone items in the store "implemented (texts, P10 not closed)" | **out of date** on "P10 not closed". |
| `A10` §10 | 378 | Phone items ranked by code; contacts above unknown numbers; judgment slot reserved | **matches** P10-D10 and P10-D11. |
| `A10` §10 | 382 | "Notifications never speak \| implemented by decision" | **matches** P10-D15. S91 keeps the constant true. |
| `A10` §11 | 394, 396 | Code-only ranking and notifications never speak, as temporary limits | **matches** P10-D11, P10-D15, S91, S99. |
| `A11` §8 | 328 | Watching a person across texts and email "designed (P10 T6 not started)" | **out of date.** P10-WATCH merged. P10-D13 shipped. |
| `A11` §8 | 332 | "Only watched phone items speak; bursts coalesce; notifications never speak \| designed (P10)" | **out of date** on "designed". ROADMAP shipped "watched-text speech". The behaviour matches P10-D15 (name-only, notifications never speak, burst window in the named constants). |
| `A12` governing records | 17 | "P10-D02, D03, D05–D07, D12, D15–D17; R1–R4. Phase 10 is not closed; T4–T6 are not built." | **out of date** on the phase and the tracks. The list also omits P10-D18 and P10-D19. |
| `A12` §6.2 | 167 | New texts "implemented (P10 T1–T3); held from conversation until T5" | **out of date** on "held from conversation until T5". P10-READ merged. P10-D11: texts reach the model when Brian asks. |
| `A12` §6.2 | 168 | "Text history and search \| designed (T5)" | **out of date.** Track 5 shipped history reads. P10-D03: history stays on the phone. |
| `A12` §6.2 | 169 | Allowlisted notifications "designed (T4)" | **out of date** on the state. The note "Never spoken unprompted in P10 (D15); Messenger dropped (D16)" matches. |
| `A12` §6.2 | 170 | Device health "partly built; Systems panel row in T6" | **out of date** as future work. Track 6 merged. ROADMAP: she "says when it's unavailable". |
| `A12` §6.2 | 171 | "Read a code aloud on request \| designed" (R1) | **out of date** on "designed". R1: "Shipped, mechanism B." ROADMAP: codes are read only on request in a local voice. |
| `A12` §6.2 | 173 | Life360 place alerts "designed (T4)" | **out of date** on the state. The boundary "never live location" is not contradicted. |
| `A12` §6.2 | 176 | Reply or send texts "deferred" (P10-D17) | **matches** P10-D17 and S90. |
| `A12` §11 | 326 | Held connection "implemented; transport not yet qualified (RCS under Doze, 12-hour battery run outstanding)" | **out of date.** ROADMAP honest item: "C10 passed under those amendments, not as a 12-hour run graded on end-to-end delay." Group RCS and the sender-shape probe were not proven; that residual is S93's neighbourhood, not an outstanding 12-hour run. |
| `A12` §11 | 327 | `zola-phone` "implemented (P10 T2–T3)" | **matches** P10-D12. This row does not say the phase is open. |
| `A12` §11 | 328 | "Phone texts into the proactive store; held from conversation until T5" | **out of date** on "until T5". Same as §6.2 line 167. |
| `A12` §11 | 329 | "Phone controls visibility only; codes masked on the phone \| designed and implemented" | **matches** P10-D02 and P10-D04 (shipped). |
| `A12` §11 | 330 | "Notifications (T4), on-demand reads (T5), PHONE health row (T6) \| designed, not built" | **out of date.** All three tracks are merged. |
| `A12` §12 | 349–355 | Tailscale only; permanent notification; no texting; Life360 last-reported place; phone decides visibility only | **matches** P10-D06, P10-D07, P10-D17, P10-D02. The Life360 boundary is the DP rule, not contradicted by Track 4. |
| `A14` §10 | 367 | Forget cascading to phone items "live-tested (phone part designed, P10)" | **out of date** on "phone part designed". P10-D14 shipped with Track 6. |
| `A14` §10 | 372 | "Code masking on the phone; R1 read-aloud path \| designed (P10)" | **out of date.** P10-D04: "Shipped." R1: "Shipped, mechanism B." |
| `A14` §11 | 394 | "Codes never stored; R1 only" as a lasting boundary | **matches** P10-D04 and R1. |
| `A15` §11 | 267 | "Texts read-only; no sending \| designed (P10)" | **out of date** on "designed". P10-D17 shipped as the deferred-capability limit. S90 remains open for a later send design. |
| `A15` §12 | 283 | "No texting or replying" as a temporary limit (P10-D17) | **matches** P10-D17 and S90. |
| `A15` §7 | 176 | X17: content cannot create watches, commitments or approvals | **matches** the watch half of P10-D19 in substance. It does not name P10-D19, and it does not state the forget half. See the missing-decision report. |

Rows in Limits tables that only restate a still-current temporary limit (code-only ranking, notifications never speak, no sending, Tailscale only, visibility stays on the phone) are the matching rows above. They were not copied again for every doc.

### Missing decisions — P10-D18 and P10-D19

No approved file names P10-D18 or P10-D19. Quotes are the lines where the decision would belong. No wording is drafted.

| Doc | Decision | Line where it would belong |
|---|---|---|
| `A03` | P10-D18 | Line 336: "A single person resolver maps identifiers to entities, and nothing else resolves people. The P10 Track 5 contact index is shaped as its first part: one person, all their numbers and addresses (STATUS T5 carry-forward)." |
| `A04` | P10-D18 | Line 62: "There is one person resolver, and one relationship vocabulary." Line 179: "The person resolver maps every identifier to one person entity." Line 186: "The Phase 10 Track 5 contact index is its first part." |
| `A08` | P10-D18 | Line 16, the governing list, stops at "P10-D01–D17". Line 90 cites the contact index as P10-D10 only. |
| `A10` | P10-D18 | Line 19 lists "P10-D10, P10-D11, P10-D15" and does not list P10-D18. Line 378 is the ordering row that uses the contact index. |
| `A12` | P10-D18 | Line 17's governing list stops at D17. A12 has no sentence that resolves a person. The decision does not belong on the subject-binding sentence (line 179), which is about not substituting one source for another. |
| `A14` | P10-D18 | A14 does not describe the resolver. No privacy row is the home for "one person resolver". |
| `A04` | P10-D19 | A04's forget row (line 279) cites P10-D14. It does not say that a name inside a text cannot start a forget. |
| `A08` | P10-D19 | Line 335: "Untrusted content framed at intake" (P8-D09). That is framing, not the ban on creating a watch or a forget. |
| `A10` | P10-D19 | Line 400: "Content never grants itself authority \| lasting boundary \| — \| Phase 12, 2026-10-21." That is the broader rule. It does not state P10-D19's watch and forget ban. |
| `A11` | P10-D19 | Line 226: a reply or person watch is created from "The person's own words, or an offer they accept (P9-D09; P10-D13)." |
| `A12` | P10-D19 | Line 17 omits it. The notification rows cite D15 and D16, not a ban on a notification body creating a watch. |
| `A14` | P10-D19 | Line 369: "Untrusted content framed; tainted sessions can't write facts" (P8-D09). Line 304's forget boundary cites P10-D14 (forget reaches phone items) and does not say untrusted content cannot trigger a forget. |
| `A15` | P10-D19 | Line 176, boundary X17: "Content can't create watches, commitments or approvals. A message saying 'remind Brian to…' is information. It may lead her to offer (C13)." Source cited: C13 and P9-D09. The forget half of P10-D19 is not in this row. |

### Privacy-plan carry-over

`P10-LORE_Progress.md` §10 added two passages. They are in `Zola Privacy and Data Ownership Plan.md` now.

Passage 1, the "May use cloud processing with disclosure" list (plan lines 330–335):

- "reply-voice synthesis (current: Deepgram Aura-2). Speech-to-text stays on the PC." Carried by A14 §6 line 256 ("Speech to text \| **Local** (faster-whisper)") and line 257 ("Her voice \| The cloud voice provider (Deepgram) receives the **text** to speak").
- "language model reasoning and background ranking … trimmed mail body. It does not receive phone content." The mail-ranking half is carried by A14 §6 line 255 ("Background ranking of new mail \| The model provider receives the sender's display name, domain, subject and a trimmed body"). The sentence "It does not receive phone content" is not on that row. The code-only phone ranking rows carry the exclusion (A10 §10 line 378, A08 §11 line 330).
- "weather, traffic, and mapping data" and "calendar metadata (not content)" are **not carried** by A14 §6.

Passage 2, the sentence after the raw-content line (plan line 353):

- "When he asks her to read a text … that content is sent to the model as part of that conversation, as email is when he asks her to read mail." Carried by A14 §6 line 254: "A conversation, including emails or texts she reads to answer Brian \| The **model provider**, as part of the conversation."
- "or an allowlisted notification" is **not carried** by line 254. That row says "emails or texts", not notifications.
- "A verification code is read by a local voice and is not sent to a cloud voice." Carried by A14 §6 line 257: "Codes are spoken by a local voice instead (ARCH-36)."

## Phase 2 STOP

Active reference edits proposed: none.

As-built rows marked out of date are listed above, including the two expected rows (A14 §6 line 269; README line 33). G-VERBATIM: the 22 files were not edited. If Brian wants those rows corrected, Claude issues new files and a new Appendix M before Phase 3.

Nothing committed. HEAD is still `898b1e6f83f4d653820b8432afe80660122a8e1d`.

## Phase 3 — Install the new docs

Phase 2 accepted 2026-11-06. Active references: none, so there is no edit list. Brian's approval of Claude's corrected files, quoted verbatim: "approved".

Start note: `ARCH-SWAP_Phase3_Start.md` (canonical `C:\Users\test\Dev\zola-spikes\prompts\ARCH-SWAP_Phase3_Start.md`).
SHA-256 (on-disk, 5,699 bytes): `2f5b834542d4f45abf0398f73648b82cd88a0ada64fdd66193df5559cee26779`.
Verified 2026-11-06. Matches the hash the developer relayed.

`C:\Users\test\Dev\zola-arch-drafts\approved-2026-11-02\` was not an input and was not copied. `arch\A14_Privacy_Boundaries_DRAFT.md` and `arch\A15_Authority_Boundaries_DRAFT.md` were not copied.

### Step 1 — Merged manifest

Re-verified all 22 sources in `zola-arch-drafts` on 2026-11-06. Each is LF (CR count 0). Every SHA-256 matches the merged manifest below. Mismatches: 0.

Rows 2, 3, 7, 14 and 17–21 are unchanged from v1.1 Appendix M. The other thirteen are the reissued files.

| # | Source | Bytes (LF) | SHA-256 (LF) | Reissued |
|---|---|---|---|---|
| 1 | `arch\A01_Architecture_Overview.md` | 26295 | `f60a4e9240139ece5bbbdc4256987db2a61178ca7ac616a27563dcbf7509b79a` | yes |
| 2 | `arch\A02_Identity_and_Personality.md` | 27944 | `a7e6d632e5dbf126c7b2a98eb466611c05a7d56e40aedd732b638076d72578d5` | no |
| 3 | `arch\A02b_Relationship_with_Brian.md` | 22197 | `4db25b4fbf6ddff08a102575b0398a9909aa20d1ab9c29b0cee31afc8431ed34` | no |
| 4 | `arch\A03_Memory_and_World_Model.md` | 51840 | `2004af5c8eda91d1042c03cabf284ed5526b571e42416b24ec47f9bb897bdb73` | yes |
| 5 | `arch\A04_People_in_Brians_World.md` | 29813 | `0cd4e3083bacb5b00a2f859fbcd5e0bef907a0e878164824d926e6e1540d297e` | yes |
| 6 | `arch\A05_Time_and_Temporal_Understanding.md` | 23687 | `5b9b1ea41219e976fb1c1f3084b0383ce79e1796c2ffe2c60980626b27e21c53` | yes |
| 7 | `arch\A06_Conversation_and_Continuity.md` | 28612 | `b790793fe7981a1906ace8236c772ed563b0c9c7c4779cb8df09131e2b98f988` | no |
| 8 | `arch\A07_Voice_Listening_and_Speech.md` | 42252 | `1c2c51c4732a08cbc5cac5fc39dceef4042a7eb5fd9b18d1f05310ad657d3136` | yes |
| 9 | `arch\A08_Awareness_Sources_Signals_and_User_State.md` | 34604 | `b133be800a3360dbdf50104c55cf96a13bc9c5c33b57e15e53cadc3d5dfcddb4` | yes |
| 10 | `arch\A09_Physical_Perception.md` | 27862 | `86fc32711d6d8bebbd56f3720568d8845e45f970e547d2f5593b06d76de31494` | yes |
| 11 | `arch\A10_Understanding_Events_and_Judgment.md` | 37068 | `63ddbd85d34e063f2c681d859c5e90b7a71e4359f9fe82ff51fbe2c9d93fd9f0` | yes |
| 12 | `arch\A11_Proactive_Engagement.md` | 33553 | `50ccbecfc04e14d36c4fd670e93b6ac45701552560dd695ab6f4d34b95a14d74` | yes |
| 13 | `arch\A12_Distributed_Presence_and_Devices.md` | 43375 | `f73143e6d4cd69f3d5d6614911d92e738aff5ee062cd663d9e2d605f607d1e82` | yes |
| 14 | `arch\A13_Presence_UI_and_Avatar.md` | 26081 | `4909c7ab8b3a643016ed5264e0383346e61e2fd772aaa35eedb51b4a0bea7519` | no |
| 15 | `arch\A14_Privacy_and_Memory_Ethics.md` | 42635 | `437ec81197323a2308ad16ccdfacba1a48890c81298be82c462add5fb1f95084` | yes |
| 16 | `arch\A15_Authority_Tools_Actions_and_Autonomy.md` | 31693 | `fdfb8497840b5b13b1b03f7ba67e550ada68eb521d539cb0a83694b728cb739f` | yes |
| 17 | `ARCH_DOCS_DECISIONS.md` | 51758 | `db872b47fffc150e20df95cf0a2a699b946f7288060ca81794fe816bf3650639` | no |
| 18 | `ARCH_DOCS_COVERAGE_MAP.md` | 19559 | `b92073cd2d509f0344a8a73b871c5d4ae59f33e99b7a65d8b33359debf58ad68` | no |
| 19 | `ARCH_DOCS_HEADING_INVENTORY.md` | 58025 | `8145fe1eca160911542c1a610629b8546d4c927b147efba2ed3783224fff2e7b` | no |
| 20 | `ARCH_DOCS_MERGE_MATRIX.md` | 22898 | `b8e6626199bca608b7ba55127044ec9baeed3ccbfde69eca8bee7dca72693bcf` | no |
| 21 | `ARCH_DOCS_READ_NOTES.md` | 52295 | `ee56e075177c0ad0f515fd940bd202162a26c0d69981dc3d134ead838a7410cd` | no |
| 22 | `swap\README.md` | 6714 | `c84063002d72cc9ec54ca2c0e30bdeb6b96e3488d453a02f46a33a081391731d` | yes |

### Step 2 — Recheck of the 13 reissued files

Read-only. The approved files were not edited.

Every row Phase 2 marked out of date now matches the closeout. Still out of date: none.

P10-D18 is cited where Phase 2 said it belongs: A03 (the resolver paragraph, the contact-index row, and the one-identity row), A04 (principle 1, the Track 5 paragraph, and the as-built rows), A08 (the governing list and the Contacts row), A10 (the governing list and the ranking row), A12 (the governing list, now D15–D19). A14 still does not describe the resolver. Phase 2 said A14 has no home for it. The start note also cites P10-D18 on the A01 workspace row; that citation is there.

P10-D19 is cited where Phase 2 said it belongs: A04 (the watch and forget rows), A10 (the "content never grants itself authority" line), A11 (the watch-creation row and the as-built watch row), A12 (the governing list), A14 §7.2 P12, A15 X17 (the row now includes "can't trigger a forget"). The start note also cites it in a new A01 §3.3 bullet; that bullet is there. A08 line 335 is still the P8-D09 framing row. The start note does not put P10-D19 on that sentence. The A08 governing list does include D19 by range (P10-D01–D19).

Privacy-plan carry-over is complete except calendar metadata. A14 §6 now includes allowlisted notifications on the conversation row, says phone items are never sent for background ranking, and has a "Weather, traffic and mapping | Not built" row. Calendar metadata is not a new row. The start note accepts that omission: A14 §6 already sends Calendar to Google through Brian's authorisation.

### Step 2 table — lines changed that Phase 2 did not flag

| Change | What Phase 2 said | Verdict |
|---|---|---|
| Header on each reissued doc except README: "Phase 10 closeout pass, 2026-11-06…" | Not a Phase 2 row. | Declared by the start note. A05, A07 and A09 do not themselves name P10-D18 or P10-D19. The header says those decisions are cited where they belong. |
| A01 §3.3, new bullet: a name or number in untrusted content can't create a watch or trigger a forget (P10-D19) | The missing-decision table did not name A01. | Declared by the start note. Matches P10-D19. |
| A01 §3.3 framing bullet now cites "P8-D09, Phase 10 annotation" | Not flagged. | Matches the P8-D09 annotation: phone content is untrusted, and showing phone rows taints the session. |
| A01 Q3 marked resolved 2026-11-06 | Not a separate out-of-date row. | Declared. The recheck is this track. |
| A01 §6: this track proposes the SOUL and VOICE_CONFIG edits | Not flagged. | Declared. Phase 5 still reports them. Phase 6 applies them. |
| A01 companion row adds versionName 1.1.1 | Added on a row Phase 2 marked out of date. | Matches P10-D05. |
| A03 one-identity row adds "Contacts-only source is a temporary limit" and cites P10-D18 and S96 | The row was marked matches. | Still matches P10-D18's temporary limit and S96. |
| A04 Contacts-only-address forget row is closed, with other name forms left in S96 | Not marked out of date. | Declared. Matches S85 (partly resolved) and S96. |
| A07 §10.3 names Microsoft Zira and "I'm going with Zira."; §11 gains a code-read row | §10.3 matched and did not name Zira. §11 had no code-read row. | Declared. Matches R1. |
| A08 disconnect row now cites P10-D12 and S92, and records the 2026-10-16 drop | Marked "not covered". The old citation was P10-D16. | Declared. Matches S92 and P10-D12. P10-D16 stays the allowlist. |
| A08 source-health row says "phone row shipped (P10)" | Not a separate row in the Phase 2 table. | Matches Track 6. |
| A09 Life360 row adds "never spoken unprompted" | The row was out of date on "designed (T4)". | Extra clause on a flagged row. Matches P10-D15. |
| A10 ranking and "notifications never speak" rows say "shipped (P10)" and the ranking row cites P10-D18 | Both rows were marked matches. | Substance unchanged. The D18 citation is the home Phase 2 named (the ranking row and the governing list). |
| A12 transport row: C10 passed under Brian's amendments (11 h 20 min first window for survival, battery and reads; 6-hour rerun for the fixes), not as a graded 12-hour run; W2 Firebase wake untested (S92) | The row was out of date. | Matches the scored windows in DESIGN_DECISIONS and S92. The closeout also keeps Brian's Appendix Q quote, which includes completeness in the first window. A12 follows the scored split. |
| A14 privacy-page row adds that the chat-history sentence is still unpublished | The date row was out of date. | Extra clause on a flagged row. Matches S86. |
| A14 "Weather, traffic and mapping" row | Phase 2 reported the carry-over gap. It was not an as-built row yet. | Declared. Calendar metadata was not added. |

### Step 3 — Install

Copied the 22 merged-manifest files to their Appendix M destinations. Created `zola-architecture/audit/arch-docs-swap/`. Working-tree copies are CRLF, matching the other docs in this folder. Each installed file, with CRLF normalised back to LF, matches the merged-manifest SHA-256. Mismatches: 0. No active-reference edit was applied.

| # | Destination | CRLF bytes | LF SHA-256 matches |
|---|---|---|---|
| 1 | `zola-architecture/A01_Architecture_Overview.md` | 26630 | yes |
| 2 | `zola-architecture/A02_Identity_and_Personality.md` | 28330 | yes |
| 3 | `zola-architecture/A02b_Relationship_with_Brian.md` | 22502 | yes |
| 4 | `zola-architecture/A03_Memory_and_World_Model.md` | 52555 | yes |
| 5 | `zola-architecture/A04_People_in_Brians_World.md` | 30201 | yes |
| 6 | `zola-architecture/A05_Time_and_Temporal_Understanding.md` | 23987 | yes |
| 7 | `zola-architecture/A06_Conversation_and_Continuity.md` | 29001 | yes |
| 8 | `zola-architecture/A07_Voice_Listening_and_Speech.md` | 42788 | yes |
| 9 | `zola-architecture/A08_Awareness_Sources_Signals_and_User_State.md` | 35033 | yes |
| 10 | `zola-architecture/A09_Physical_Perception.md` | 28219 | yes |
| 11 | `zola-architecture/A10_Understanding_Events_and_Judgment.md` | 37564 | yes |
| 12 | `zola-architecture/A11_Proactive_Engagement.md` | 33974 | yes |
| 13 | `zola-architecture/A12_Distributed_Presence_and_Devices.md` | 43856 | yes |
| 14 | `zola-architecture/A13_Presence_UI_and_Avatar.md` | 26445 | yes |
| 15 | `zola-architecture/A14_Privacy_and_Memory_Ethics.md` | 43151 | yes |
| 16 | `zola-architecture/A15_Authority_Tools_Actions_and_Autonomy.md` | 32088 | yes |
| 17 | `zola-architecture/ARCH_DOCS_DECISIONS.md` | 52410 | yes |
| 18 | `zola-architecture/audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` | 19783 | yes |
| 19 | `zola-architecture/audit/arch-docs-swap/ARCH_DOCS_HEADING_INVENTORY.md` | 58899 | yes |
| 20 | `zola-architecture/audit/arch-docs-swap/ARCH_DOCS_MERGE_MATRIX.md` | 23131 | yes |
| 21 | `zola-architecture/audit/arch-docs-swap/ARCH_DOCS_READ_NOTES.md` | 52579 | yes |
| 22 | `zola-architecture/README.md` | 6789 | yes |

`audit/arch-docs-swap/` holds those four records and nothing else. The 39 Appendix L files are still present and unmodified.

### README links

`zola-architecture/README.md` has 18 relative markdown links: A01–A15, A02b, `ARCH_DOCS_DECISIONS.md`, and `audit/arch-docs-swap/`. Each resolves. None of them is one of the 39 retired filenames, so each still exists after Phase 4.

The successor table names those 39 files in backticks. Those are names in the table, not links. Phase 4 deletes the files. The table is their successor pointer.

One backtick path in the same paragraph does not resolve from this folder: `ARCH_DOCS_HEADING_INVENTORY.md` (README line 33). The file is at `audit/arch-docs-swap/ARCH_DOCS_HEADING_INVENTORY.md`. The coverage-map path in that sentence includes its folder and does resolve. G-VERBATIM: the README was not patched.

### Git

`git diff` and `git diff --stat` are empty. No tracked file changed, so the active-reference diff is empty.

`git status` (branch `arch-swap`, HEAD `898b1e6f83f4d653820b8432afe80660122a8e1d`):

```
?? zola-architecture/A01_Architecture_Overview.md
?? zola-architecture/A02_Identity_and_Personality.md
?? zola-architecture/A02b_Relationship_with_Brian.md
?? zola-architecture/A03_Memory_and_World_Model.md
?? zola-architecture/A04_People_in_Brians_World.md
?? zola-architecture/A05_Time_and_Temporal_Understanding.md
?? zola-architecture/A06_Conversation_and_Continuity.md
?? zola-architecture/A07_Voice_Listening_and_Speech.md
?? zola-architecture/A08_Awareness_Sources_Signals_and_User_State.md
?? zola-architecture/A09_Physical_Perception.md
?? zola-architecture/A10_Understanding_Events_and_Judgment.md
?? zola-architecture/A11_Proactive_Engagement.md
?? zola-architecture/A12_Distributed_Presence_and_Devices.md
?? zola-architecture/A13_Presence_UI_and_Avatar.md
?? zola-architecture/A14_Privacy_and_Memory_Ethics.md
?? zola-architecture/A15_Authority_Tools_Actions_and_Autonomy.md
?? zola-architecture/ARCH_DOCS_DECISIONS.md
?? zola-architecture/README.md
?? zola-architecture/audit/arch-docs-swap/
?? zola-architecture/lore/prompts/progress/ARCH-SWAP_Progress.md
```

## Phase 3 STOP

The 22 files are installed and match the merged manifest. Active-reference edits: none. The 39 Android-era docs are still in place.

Nothing committed. HEAD is still `898b1e6f83f4d653820b8432afe80660122a8e1d`.

## Phase 4 — Retire the 39 copies

Phase 3 accepted 2026-11-06.

### Delete

Re-checked all 39 Appendix L files on disk before removal. Every size and SHA-256 still matches the Phase 1 inventory. Mismatches: 0. Then `git rm` on those paths only. Staged deletions: 39. No other path is staged. Nothing under `identity/`, `lore/`, or `audit/` was deleted.

| # | Deleted |
|---|---|
| 1 | `zola-architecture/Zola Autonomous Behavior Architecture.md` |
| 2 | `zola-architecture/Zola Conversational Attention Architecture.md` |
| 3 | `zola-architecture/Zola Conversational Continuity Architecture.md` |
| 4 | `zola-architecture/Zola Distributed Presence Architecture.md` |
| 5 | `zola-architecture/Zola Environmental Awareness Architecture.md` |
| 6 | `zola-architecture/Zola Environmental Perception Architecture.md` |
| 7 | `zola-architecture/Zola Identity and Personality Framework.md` |
| 8 | `zola-architecture/Zola Master Architecture Plan.md` |
| 9 | `zola-architecture/Zola Memory Hierarchy Architecture.md` |
| 10 | `zola-architecture/Zola Privacy and Data Ownership Plan.md` |
| 11 | `zola-architecture/Zola Streaming Cognition Architecture.md` |
| 12 | `zola-architecture/Zola_Agent_Map.md` |
| 13 | `zola-architecture/Zola_Architecture_Cognitive_Engagement.md` |
| 14 | `zola-architecture/Zola_Architecture_Context_Injection.md` |
| 15 | `zola-architecture/Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md` |
| 16 | `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` |
| 17 | `zola-architecture/Zola_Architecture_Environmental_Event_Bus_and_User_State_Model.md` |
| 18 | `zola-architecture/Zola_Architecture_Identity_Source_Consolidation_Plan.md` |
| 19 | `zola-architecture/Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` |
| 20 | `zola-architecture/Zola_Architecture_Memory_Agency.md` |
| 21 | `zola-architecture/Zola_Architecture_Memory_Ethics_and_Privacy.md` |
| 22 | `zola-architecture/Zola_Architecture_Perception_Memory.md` |
| 23 | `zola-architecture/Zola_Architecture_Perceptual_Input_Layer.md` |
| 24 | `zola-architecture/Zola_Architecture_Relationship_Inference.md` |
| 25 | `zola-architecture/Zola_Attention_Relevance_Engine_Architecture.md` |
| 26 | `zola-architecture/Zola_Capability_Acquisition_Architecture.md` |
| 27 | `zola-architecture/Zola_Cognitive_Engine_Architecture.md` |
| 28 | `zola-architecture/Zola_Communication_Intelligence_Architecture.md` |
| 29 | `zola-architecture/Zola_CrossDomain_Correlation_Architecture.md` |
| 30 | `zola-architecture/Zola_Presence_UI_Architecture.md` |
| 31 | `zola-architecture/Zola_Relational_Calibration_Architecture.md` |
| 32 | `zola-architecture/Zola_Relational_Continuity_Architecture.md` |
| 33 | `zola-architecture/Zola_Relational_Intelligence_Layer_Architecture.md` |
| 34 | `zola-architecture/Zola_SelfModel_Awareness_Architecture.md` |
| 35 | `zola-architecture/Zola_Session_Identity_Architecture.md` |
| 36 | `zola-architecture/Zola_Sms_Intelligence_Architecture.md` |
| 37 | `zola-architecture/Zola_SocialGraph_Reasoning_Architecture.md` |
| 38 | `zola-architecture/Zola_Temporal_Reasoning_Architecture.md` |
| 39 | `zola-architecture/Zola_Tool_Authorization_Architecture.md` |

### Re-census

Same search as Phase 2: each Appendix L stem, with and without `.md`, with and without a folder prefix, spaces also as `%20`, plus the short names Master Architecture Plan, Agent Map, Memory Agency, Living Voiceprint, and Context Injection. Ripgrep, gitignore respected, `.git` excluded. The 22 installed files are excluded from the comparison, as Phase 2 did, because they cite the old names on purpose.

The 116 historical hits are unchanged in file, line, and text. Each recorded quote is still on that line. The fresh search found those 116 and no others outside this progress doc and the 22 installed files.

| Set | Count | Result |
|---|---|---|
| Phase 2 historical hits outside this progress doc | 116 | same file, line, and text |
| New hits outside this progress doc and the 22 installed files | 0 | none |
| Hits outside `zola-architecture/` | 0 | none |
| `%20` hits | 0 | none |
| Hits in the 22 installed files | 275 | expected. The README successor table, the domain docs, and the swap records name the retired files on purpose. |
| Hits in this progress doc | 145 | this track's own record. Phase 2 counted 42 in the Phase 1 inventory; the census table and later sections added the rest. |

Active references remaining: none. No new active hit. No historical hit changed.

### Final listing

Top level of `zola-architecture/`:

- `README.md`
- `ARCH_DOCS_DECISIONS.md`
- A01–A15 and A02b (16 docs)

Subfolders:

- `audit/` — the Phase 1 set (`p10pre-phase10`, `p3pre-presence-ui`, `p4pre-conversation`, `p5pre-phase5`, `p6pre-phase6`, `p7pre-phase7`, `p8pre-phase8`, `p9pre-phase9`, `voicepre-standalone`, `winh-hermes-gap`) plus `arch-docs-swap/` from Phase 3
- `identity/` — `MEMORY_CONVENTIONS.md`, `SOUL.md`, `VOICE_CONFIG.md`
- `lore/` — `build-plans/`, `prompts/`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`

No other top-level entry.

## Phase 4 STOP

The 39 copies are staged for deletion and are gone from the working tree. The re-census matches Phase 2. The folder listing matches the swap.

Nothing committed. HEAD is still `898b1e6f83f4d653820b8432afe80660122a8e1d`.

## Phase 5 — Identity lines under P4-D25

Read-only. No identity file was edited. No wording is proposed.

### P4-D25

`DESIGN_DECISIONS.md` lines 760–761 state only the title: "Live profile edits are developer-approved, exact, and mirrored." The steps are not restated there. The locked text is `PHASE4_BUILD_PLAN.md` lines 393–398, which the Phase 4 lore closeout recorded as applied as planned:

1. A profile change is proposed as exact text at a STOP.
2. It is applied only after the developer's approval.
3. It is then recorded in `VOICE_CONFIG.md`, or in the identity canonical copy, in the same track.
4. The profile is backed up before each edit. The backup is a timestamped copy in the profile folder, `%LOCALAPPDATA%\hermes\profiles\zola\`.

P4-D25 does not say when a backup is removed. Later plans that say "follow P4-D25" add `P6-D11`. `DESIGN_DECISIONS.md` lines 1003–1007: backups are deleted at each track's closeout after merge, because forget cannot reach them. Brian, at that closeout: "delete old ones and track passes."

The profile folder still holds older backups from Phase 4, including `SOUL.md.bak-P4-VOICE-20261001-091115` and several `config.yaml.bak-*` files. They were not touched.

### SOUL

| Copy | Path | Bytes | SHA-256 |
|---|---|---|---|
| Live | `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` | 10458 | `4411118908839cadd131d1723e969176451be8550172b41dcbb4b792ef9ff45b` |
| Mirror | `zola-architecture/identity/SOUL.md` | 10458 | `4411118908839cadd131d1723e969176451be8550172b41dcbb4b792ef9ff45b` |

Identical, including line endings. Both are CRLF (123 CR, 123 LF).

The line containing "text-based Windows client", with five lines before it and five after it (`identity/SOUL.md` lines 32–42; the live file matches):

```
acquire useful capabilities. I don't silently change my own software,
permissions, or environment to accomplish something that requires
Brian's approval.
I'm intended to become a persistent presence across Brian's devices
and daily life, not merely a program he opens and closes. Right now, I
operate through a text-based Windows client. That's where I'm
starting, not where I'm finished.

## How I talk out loud
When Brian and I are talking out loud, I speak like I'm there with him, not like I'm reading
something I wrote for a screen.
```

Other lines that describe how Brian talks to Zola. No line mentions an avatar.

| Lines | What it says |
|---|---|
| 40–41 | Heading "How I talk out loud." When they are talking out loud, she speaks as if she is there, not as if she is reading something written for a screen. The section runs through line 62. |
| 56–58 | She can see when each message arrives. She uses that the way a person would, and she never reads timestamps or system notes out loud. |
| 110 | When she has just told Brian out loud that someone got back to him, a follow-up uses that note. She opens the mail only if he asks. |
| 112 | She never says the approval phrase, and she never asks him to repeat a sentence she just spoke. |
| 120 | She never guesses a verification code. Only the code reader says or shows it. |

### VOICE_CONFIG

No live copy. `%LOCALAPPDATA%\hermes\profiles\zola\VOICE_CONFIG.md` is absent, including in subfolders. The live speech keys are in that profile's `config.yaml`. This file was not read for editing and was not changed.

The current Deepgram record is in the opening block, not under its own heading. Lines 11–23:

```
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

Lines 52–54:

```
- `tts.provider`: `deepgram` (`P9-D14`). The Edge block remains in the live file and is not the active provider.
- `tts.providers.deepgram`: command provider. The script is `%LOCALAPPDATA%\hermes\profiles\zola\zola-tts\deepgram_tts.py`. Model `aura-2-pandora-en`. Speed `0.95`. Output `mp3`.
- The key file is `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key`. The key is not in `config.yaml` and not in this document.
```

The Sonia / Edge section is lines 86–101, heading `## Voice: Sonia at 0.95 (P4-VOICE Round 1)`:

```
## Voice: Sonia at 0.95 (P4-VOICE Round 1)

P4-VOICE: provisional spoken voice until live trial verdict — P4-D19

| Field | Value |
|---|---|
| Key | `tts.edge.voice` / `tts.edge.speed` |
| Value | `en-GB-SoniaNeural` / `0.95` (Edge `rate=-5%`; was provisional `1.1`) |
| Date | 2026-10-01 |
| Decision | `P4-D19` + speed A/B (pick C) |
| Backup | `config.yaml.bak-P4-VOICE-20261001-075403` (voice); `config.yaml.bak-P4-VOICE-speed-20261001-084653` (speed 1.1→0.95) |
| Approval | developer-approved (`apply voice`; speed A/B **pick C**) |

Diff vs first backup: Sonia + speed. Speed A/B: `1.1` → `0.95` only. Serve restarted after speed apply (`127.0.0.1:52894`).

**Live-trial verdict (2026-10-01):** Keep Sonia. 1.1 too fast. Speed A/B labels A=1.0, B=1.05, C=0.95 — **picked C (0.95)**. Deeper via Phase 6 pitch A/B (`0 / −2 / −4 / −6 Hz`). Husky texture (breathiness) not possible with Edge — future premium-voice item. Phase 6 command `--rate` must be `-5%` (literal duplicate of `tts.edge.speed` — both must change together).
```

The next section, lines 103–118, heading `## Command provider pitch baseline (P4-VOICE Round 3)`, still says the final provider is built-in Edge (Sonia 0.95). The tuning log still has `tts.provider` as `edge` on 2026-10-01 (line 188) and the Sonia voice and speed rows at lines 186–187.

There is no heading on the Deepgram record. A short code-voice pointer would sit after the Deepgram bullets (line 54), in that opening record, and before the heading `## Clarify timeout (P4-REQUEST)` at line 71.

### Code voice

`VOICE_CONFIG.md` does not mention Zira or the local code voice. `DESIGN_DECISIONS.md`, under `### R1 — The read-aloud path, amended by ARCH-36`:

Line 1966: "Why a local voice. The Hermes voice path writes text and audio to files, so it can never carry a code. ARCH-36, as `P10-READ_Progress.md` cites it, supersedes the build plan's Deepgram choice for code reads. Brian: "I'm going with Zira.""

Line 1968: "Shipped, mechanism B. One-time handle. The tool arms the read in `zola-phone`. The client redeems it on the `zola-phone` pipe. Zira speaks from memory. No file. No network. No wire version bump: `code.arm` and `code.redeem` are local requests; the phone contract stays v4. One server request, the same pattern as clarify, method `code_read`, handle only. Handle 60 s. Tool wait 45 s. Client deadline 35 s, and it never starts playback after that deadline. Disarm on every exit. Cancellation includes the client deadline and connection loss when serve disappears without a cancel message. In text mode the value is shown on screen and is not written into the conversation. "Show" prefers the screen. A second ask while one is active is refused."

## Phase 5 STOP

The report is above. No wording is proposed. Phase 6 applies only the exact text Brian approves for both files.

Nothing committed. HEAD is still `898b1e6f83f4d653820b8432afe80660122a8e1d`.

## Phase 6 — Apply the identity edits

Phase 5 accepted 2026-11-06.

Start note: `ARCH-SWAP_Phase6_Start.md` (canonical `C:\Users\test\Dev\zola-spikes\prompts\ARCH-SWAP_Phase6_Start.md`).
SHA-256 (on-disk, 4,668 bytes): `313e4ba68caff3359bed7e68a78a7e281e3e1c78ad83e7a3ce9966df323b43ac`.

The developer relayed that file as this phase's instruction. Its approval section, quoted verbatim: "Phase 6 runs only once the developer relays Brian's approval of the exact text below. Quote it verbatim in the progress doc. If he changes any wording, Claude reissues this file; do not apply a variant." The exact text in that file was applied. No wording was changed.

Before the edit, both SOUL copies were still 10,458 bytes, CRLF, SHA-256 `4411118908839cadd131d1723e969176451be8550172b41dcbb4b792ef9ff45b`. `identity/VOICE_CONFIG.md` was 17,149 bytes, CRLF. No live `VOICE_CONFIG.md` exists.

### SOUL

Backed up the live file first to `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md.bak-ARCH-SWAP-20261106-142512`. That backup is the pre-edit file (10,458 bytes, SHA-256 `4411118908839cadd131d1723e969176451be8550172b41dcbb4b792ef9ff45b`). Older backups in the folder were left alone. Under P6-D11 this backup is deleted at this track's closeout after merge, not before.

Replaced lines 36–38 with the five approved lines. Line 35 is unchanged. Kept CRLF. Copied the live file over `identity/SOUL.md`.

Both copies: 10,587 bytes, 125 lines, CRLF, SHA-256 `11e84261d6379c97164163e4927f6d60fb07d34070d03cf3004ccaa28da65ac5`. They are identical.

### VOICE_CONFIG

Repo file only. Four changes. The YAML block, lines 5–46, was not edited. The bodies of the Sonia section and the Round 3 section were not edited.

Result: 17,993 bytes, 227 lines, CRLF, SHA-256 `357959e031e3a59eb67604264c6318d631adaea851dffdedb3efff751111dd0b`.

### Diffs

`git diff` of the two identity files is only the approved lines.

`SOUL.md`: lines 36–38 become the five approved lines. `VOICE_CONFIG.md`: the Zira bullet after the key-file bullet; the Sonia heading marked historical, with the historical note; the Round 3 heading marked historical, with the historical note; one tuning-log row after the 2026-10-01 `edge` row.

`git diff --stat` for those two files: `SOUL.md` 6 lines changed (4 insertions, 2 deletions); `VOICE_CONFIG.md` 10 lines changed (8 insertions, 2 deletions).

`git diff --stat HEAD` against the Phase 1 base is those two files plus the 39 staged deletions: 41 files changed, 12 insertions, 27,328 deletions. The 22 installed docs and this progress doc are untracked, so they are not in that stat. No code, plugin, config, lore entry, build plan, audit, or other progress doc is in the diff.

### Phase 3 record

The merged manifest is recorded under "Step 1 — Merged manifest". The Step 2 table is recorded under "Step 2 table — lines changed that Phase 2 did not flag".

### Exit checklist

| Check | Mark | Result |
|---|---|---|
| 22 files installed, each verified against its approved SHA-256 | ✅ | Rechecked this phase. CRLF normalised to LF. 22 of 22 match the merged manifest. |
| 39 files deleted, each verified before deletion, nothing else deleted | ✅ | Phase 4. On-disk hashes matched, then `git rm`. Staged deletions are exactly those 39. |
| No active reference to a retired filename remains; historical hits unchanged | ✅ | Phase 4 re-census. 116 historical hits unchanged. Active references: none. This phase did not edit lore, audits, or build plans. |
| Every README link resolves | ⚠️ | The 18 markdown links resolve. README line 33 names `ARCH_DOCS_HEADING_INVENTORY.md` without its folder. That is plain text, not a link, and it was not fixed. Brian went on without a reissue. The file is at `audit/arch-docs-swap/ARCH_DOCS_HEADING_INVENTORY.md`. |
| Every out-of-date as-built row from Phase 2 is corrected, or accepted by Brian | ✅ | Corrected in the reissued files. Brian's Phase 3 approval, quoted then: "approved". The Step 2 table records the lines Phase 2 did not flag. Calendar metadata was the accepted omission. |
| Live SOUL and `identity/SOUL.md` identical, only the approved change, backup handled as P4-D25 says | ✅ | Both SHA-256 `11e84261d6379c97164163e4927f6d60fb07d34070d03cf3004ccaa28da65ac5`. Backup `SOUL.md.bak-ARCH-SWAP-20261106-142512` stays until closeout after merge (P6-D11). |
| `VOICE_CONFIG.md` carries only the approved change | ✅ | SHA-256 `357959e031e3a59eb67604264c6318d631adaea851dffdedb3efff751111dd0b`. No live copy. |
| No code, plugin, config, lore entry, build plan, audit, or other progress doc changed | ✅ | `git diff --stat HEAD` is the 39 deletions and the two identity files. |
| No process started, stopped, or restarted; `hermes-agent` clean | ✅ | No process was touched. `hermes-agent` is clean, detached at `345cd2b057a452236de401d3534b8502a7465e8d`. |

### Experience check

Brian asked Zola, in a new conversation, how he can talk to her. Her answer, verbatim: "Mostly out loud—voice first, with text when you’d rather type."

## Phase 6 STOP

The approved identity text is applied. The experience check is recorded above.

Nothing committed yet. HEAD is still `898b1e6f83f4d653820b8432afe80660122a8e1d`.

## Phase 7 — Commit and merge

Brian, verbatim: "proceed to commit and merge." Under the SOP v3.0 transition, that is also his approval for this merge to reach the everyday build. This track changes documents and the approved identity lines. Active reference edits: none.

The Android-era originals live in the Android repository.

Implementation SHA: `533951ff6a8e022503a19ed3acda9000b9822774`.
Subject: `docs(ARCH-SWAP): Windows architecture docs replace the Android-era copies`.

Merge SHA: `1fb0e6150e8354ea0bbc15a1225b83df2ad3f4f4`.
Subject: `Merge branch 'arch-swap'`.
`main` and `origin/main` are this merge.

