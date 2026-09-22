# P1-IDENTITY Progress — Track 2: Identity Extension

## Branch

- Branch: `track2-identity` (merged into `main` and deleted)
- Base SHA: `03a9af742bb6eb7e14043884a6816a9ff636e81e`
- Feature commit SHA: `bd0e7e56c83e55df2941ab2c841cfe4656f9bec4`
- Branch tip merged: `52c92c274ab39eb014d4f3d79db92d03a51cb430`
- Merge commit SHA on `main`: `83405c34ea96a598e6bb6a32bd3d9137d078cee2`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Write and Deploy Identity Text | COMPLETE |
| 4 | Smoke Test | COMPLETE |
| 5 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Write Zola's identity into `zola-architecture/identity/SOUL.md` and deploy that same text to the live profile `SOUL.md`. Content only. No `windows-client/` changes unless a blocker is flagged. `hermes-agent` is read-only.
- **G-ARCH:** Build plan is truth. Stop and flag conflicts; do not silently deviate.
- **G-PATTERN:** Read every relevant file in full before any change. No changes from partial reads or memory.
- **G-NOCHANGE:** Edits limited to `zola-architecture/identity/SOUL.md`, the live profile `SOUL.md`, and this progress document. No `hermes-agent` edits. No `windows-client/` edits unless a blocker is flagged.
- **G-COMMENT:** Do not put code-style comments in the identity prose. A source file, if one is touched, carries `// P1-IDENTITY: [rationale] — P1-D03`.
- **G-STOP:** Stop after each phase and wait for that phase's explicit proceed message.
- **G-CLOSEOUT:** Closeout begins only on the explicit message "proceed to closeout".
- **G-LORE-SCOPE:** Do not add, resolve, or update `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, or any project state-audit document in this track, including closeout.

## Discrepancies

The prompt named base SHA `c3542c678b063b1321927e23c5b91ae90149a155`. `main` HEAD was `03a9af742bb6eb7e14043884a6816a9ff636e81e` (`docs: record P1-CLIENT merge SHA on main`, one commit after that merge). Developer chose Option A: branch from current `main` and record `03a9af742bb6eb7e14043884a6816a9ff636e81e` as the base SHA.

Phase 2 clarifications (not blockers):

1. Live profile path from Track 1 is `%LOCALAPPDATA%\hermes\profiles\zola\`. `SOUL.md` is there and its text equals `hermes_cli/default_soul.py` `DEFAULT_SOUL_MD` (the current Hermes seed: "You are Hermes Agent, built by Nous Research..."). It is not user-edited.
2. `is_legacy_template_soul(text: str) -> bool` compares normalized text to older scaffolds and the ASCII-dash copy of the current default. The current em-dash `DEFAULT_SOUL_MD` is the upgrade target, not an entry in that list, so the live file returns `False` even though it is still the stock template. Phase 3's `False` check means "will not be auto-replaced," not "this text is already custom."
3. `load_soul_md()` reads `{HERMES_HOME}/SOUL.md` (or `home_override / "SOUL.md"`). It strips whitespace, drops a legacy "## Messaging other agents" roster only when that heading is present, blocks the file only if the context threat scan matches, and truncates only above the context-file character cap. Zola's prose has none of those triggers.

Phase 3: `zola-architecture/identity/SOUL.md` and `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` are byte-identical (SHA-256 `5BE357072C44D37E0B9CCEF8C87162B1C836664F285C4F3EF30B665FC1BB2AB0`). `is_legacy_template_soul()` on that text returns `False`. The live file is a content deploy outside the git repo. No `hermes-agent` or `windows-client/` files were changed.

Phase 4: developer reported "smoke test passed" ("who are you?" reflected Zola's identity and tone).

## Closeout

- No build command (content-only track). No automated test suite.
- Live profile `SOUL.md` is deployed outside the repo and is not part of the feature commit.
- Feature commit SHA: `bd0e7e56c83e55df2941ab2c841cfe4656f9bec4`
- Branch tip merged: `52c92c274ab39eb014d4f3d79db92d03a51cb430`
- Merge commit SHA on `main`: `83405c34ea96a598e6bb6a32bd3d9137d078cee2`

## Files

### Created this track

- `zola-architecture/lore/prompts/progress/P1-IDENTITY_Progress.md` (Phase 1)
- `zola-architecture/identity/SOUL.md` (Phase 3)

### Modified this track

- `zola-architecture/lore/prompts/progress/P1-IDENTITY_Progress.md` (Phase 2 and Phase 3 status)

### Deployed outside the repo

- `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` (Phase 3 content deploy; not a git commit)
