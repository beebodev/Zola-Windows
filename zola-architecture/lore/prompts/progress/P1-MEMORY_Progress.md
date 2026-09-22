# P1-MEMORY Progress — Track 4: Memory Extension

## Branch

- Branch: `track4-memory-extension`
- Base SHA: `c95d7b2ebaedc10d29f4991ee86c08b037a8cadc`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Raise Memory Budgets and Document Tagging | COMPLETE |
| 4 | Smoke Test | COMPLETE |
| 5 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Raise the Zola profile's `memory_char_limit`/`user_char_limit` on Hermes's existing flat-file `MemoryStore`, and document a lightweight `[tag]` prefix convention for MEMORY.md and USER.md entries. No new storage layer, no structured memory system (`S14`), no Hermes memory-code edits, and nothing from Tracks 5 or 6.
- **G-ARCH:** Build plan is truth. Stop and flag conflicts; do not silently deviate.
- **G-PATTERN:** Read every relevant file in full before any change. No changes from partial reads or memory.
- **G-NOCHANGE:** Edits limited to the files and lines described in the current task.
- **G-COMMENT:** Every changed line or block carries `// P1-MEMORY: [rationale] — P1-D05`, or a one-line prose note when the change is documentation. Do not comment unchanged lines.
- **G-STOP:** Stop after each phase and wait for that phase's explicit proceed message.
- **G-CLOSEOUT:** Closeout begins only on the explicit message "proceed to closeout".
- **G-LORE-SCOPE:** Do not add, resolve, or update `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, or any project state-audit document in this track, including closeout. Do not touch `S14`.

## Discrepancies

The prompt named base SHA `eecd72821d31587a824f55b97892c9f1a7841483` (Track 3's merge commit). `main` HEAD was `c95d7b2ebaedc10d29f4991ee86c08b037a8cadc` (`docs: record P1-SESSION merge SHA on main`, one commit after that merge). Developer chose Option A: branch from current `main` and record `c95d7b2ebaedc10d29f4991ee86c08b037a8cadc` as the base SHA.

Phase 2 (not a blocker; this is the contract Phase 3 builds against):

1. The limits are `memory.memory_char_limit` and `memory.user_char_limit` in the profile `config.yaml`. Defaults in `hermes_cli/config_defaults.py` are 2200 and 1375. `load_config()` deep-merges that file over the defaults, so setting only those two keys keeps the rest of the `memory` section. Zola's file is `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`. It has no `memory` section today, so the defaults are in effect. That file is outside the git repo.
2. `MemoryStore.__init__` hardcodes 2200/1375 only as constructor defaults. `agent/agent_init.py` `_init_memory` and `tools/memory_tool.py` `load_on_disk_store()` both pass `get_builtin_memory_config()` into the constructor. There is no status command that prints the limits (`GET /api/memory` returns the provider name and file sizes). A constructed `MemoryStore` exposes `.memory_char_limit` and `.user_char_limit`. A successful write's `usage` string is `current/limit chars`.
3. Drift protection is `_detect_external_drift`: replace/remove refuse a file that does not round-trip through the `§` delimiter, or an entry longer than the whole-file limit, and write a `.bak` snapshot. `add` skips that drift check but still refuses an unreadable file. The tool actions are `add`/`replace`/`remove` and targets `memory`/`user`, matching `MemoryProvider.on_memory_write`. Nothing in the tool parses a `[tag]` prefix, so the convention is prompt-only. `memory.provider` is empty, so the built-in store is the one in use.

Phase 3: the live profile `config.yaml` now has `memory.memory_char_limit: 4400` and `memory.user_char_limit: 2750`. The same block is recorded in `zola-architecture/identity/MEMORY_CONVENTIONS.md`. A `MemoryStore` built with `load_on_disk_store()` under `HERMES_HOME` set to the Zola profile reported `4400` and `2750`. An add returned `37/4,400 chars`, a reload read the entry back, and a replace then remove both succeeded with no `.bak` snapshot. The probe entry and the empty `MEMORY.md` it left were removed afterward. No files under `hermes-agent` or `windows-client/` were edited.

Phase 4: developer reported "smoke test passed" (recalled fact matched, the stored entry used a `[tag]` prefix, and no drift-protection failure surfaced).

## Closeout

- `dotnet build windows-client/Zola.Client/Zola.Client.csproj` passed (0 warnings, 0 errors).
- Existing tests: N/A. This project has no automated test suite.
- No lore files were updated (`ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, and `S14` were left untouched).
- Live profile `config.yaml` is outside the git repo and is not part of the feature commit. The budget snippet is in `zola-architecture/identity/MEMORY_CONVENTIONS.md`.
- Feature commit SHA and the merge commit SHA on `main` are recorded after those commits.

## Files

### Created this track

- `zola-architecture/lore/prompts/progress/P1-MEMORY_Progress.md` (Phase 1)
- `zola-architecture/identity/MEMORY_CONVENTIONS.md` (Phase 3)

### Modified this track

- `zola-architecture/lore/prompts/progress/P1-MEMORY_Progress.md` (Phase 2 findings, Phase 3 result, Phase 4 result, closeout)
- Live profile `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` (Phase 3; outside the git repo)
