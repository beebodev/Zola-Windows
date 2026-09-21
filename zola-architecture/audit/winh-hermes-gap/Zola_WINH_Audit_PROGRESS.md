# Zola WINH Hermes Gap Analysis — Progress

Shared across the entire WINH series (WINH01-07 + WINH00). Later prompts extend this file; they must not replace the Hermes pin recorded here.

## Hermes pin (set once by WINH01 — do not change)

- Release tag: `v2026.9.14`
- Marketing version: Hermes Agent v0.21.3 (`pyproject.toml` `[project].version = "0.21.3"`)
- Commit SHA: `345cd2b057a452236de401d3534b8502a7465e8d`
- Annotated tag object: `7a963716b81be13ba513d4f127633b7da493aff2` (type `tag`; peels to the commit above)
- Tag creator date (local git): 2026-09-14 09:04:09 -0700
- GitHub release published: 2026-09-14T16:04:14Z
- GitHub release flags: `draft: false`, `prerelease: false` (confirmed via `https://api.github.com/repos/NousResearch/hermes-agent/releases/latest`)
- Clone path (external, not in this repo): `C:\Users\test\Dev\hermes-agent`
- Checkout state: detached HEAD at `v2026.9.14`

### Five most recent local tags (by `git tag --sort=-creatordate`)

1. `v2026.9.14` — 2026-09-14 09:04:09 -0700 — Hermes Agent v0.21.3 (v2026.9.14)
2. `v2026.9.11` — 2026-09-11 12:20:28 -0700 — Hermes Agent v0.21.2 (v2026.9.11) — The state.db Patch Release
3. `v2026.9.7` — 2026-09-07 15:16:56 -0700 — Hermes Agent v0.21.1 (2026.9.7)
4. `v2026.8.31` — 2026-08-31 12:29:39 -0700 — Hermes Agent v0.21.0 (2026.8.31)
5. `v2026.8.27` — 2026-08-27 05:06:48 -0700 — Hermes Agent v0.20.6 (2026.8.27)

Cross-check: GitHub Releases list and `/releases/latest` both name `v2026.9.14` as the latest published non-prerelease. The series audits this tag, not `main` (`main` at clone time was `bb359ec5c1d5da6a66f00ee11f0ad7a86defaee2`).

## Zola-Windows branch

- Shared branch: `winh-hermes-audit`
- Created from: `main` at `4ff1abf2cf20c4a1bdcdb59ea99fd8eaabb66cb3`
- Output directory: `zola-architecture/audit/winh-hermes-gap/`

WINH01 setup note: this workspace had no `.git` when the prompt started. `main` was initialized with the existing `zola-architecture/` documents (clean tree), then `winh-hermes-audit` was created from that `main`. The sibling path `C:\Users\test\Dev\hermes-agent` existed as an empty directory and was cloned from `https://github.com/NousResearch/hermes-agent` (not added as a submodule, not copied into this repo).

## Series phase table

- WINH01 — Setup, Repo Map, Native Windows Runtime — COMPLETE
- WINH02 — Memory and Skills — PENDING
- WINH03 — (domain audit; title filled by that prompt) — PENDING
- WINH04 — (domain audit; title filled by that prompt) — PENDING
- WINH05 — (domain audit; title filled by that prompt) — PENDING
- WINH06 — (domain audit; title filled by that prompt) — PENDING
- WINH07 — (domain audit; title filled by that prompt) — PENDING
- WINH00 — Synthesis + closeout — PENDING

WINH02-07 titles are filled in by those prompts. WINH00 is the only prompt that merges or closes the branch.

## Guardrails (entire series)

- G-SCOPE: Diagnostic audit only. Read Hermes at `C:\Users\test\Dev\hermes-agent` (pinned tag) and the Zola-Windows documents listed in each prompt. Produce findings only under `zola-architecture/audit/winh-hermes-gap/`.
- G-NOCHANGE: Zero source modifications in Hermes. Zero modifications in Zola-Windows outside this output directory.
- G-QUALITY: Every finding names a specific file, directory, function, config key, or line in tag `v2026.9.14`. If docs and code conflict, report both.
- G-CLOSEOUT: Deferred to WINH00. This series does not merge, push a final state, or delete the branch until WINH00.

## Repo map (WINH01 Phase 2)

Later prompts should start here:

- [Zola_WINH01_Audit_01_RepoMap.md](./Zola_WINH01_Audit_01_RepoMap.md)

Windows runtime findings:

- [Zola_WINH01_Audit_02_WindowsRuntime.md](./Zola_WINH01_Audit_02_WindowsRuntime.md)

## Running findings list

- WINH01-AUD-01 — [PARTIAL] — MEDIUM — `README.md` L43-45; `website/docs/user-guide/windows-native.md` L85-102 — Native Windows is a first-class install path, but the project's own feature matrix does not claim full Linux/macOS parity.
- WINH01-AUD-02 — [GAP] — HIGH — `tools/lazy_deps.py` `_unsupported_feature_reason` L341-343; `pyproject.toml` L387-392 — Matrix E2EE (`python-olm`) is explicitly unsupported on native Windows; docs tell users to use WSL.
- WINH01-AUD-03 — [RISK] — MEDIUM — `website/docs/user-guide/windows-native.md` L99-102 vs `hermes_cli/web_server_chat.py` L26-33 and `hermes_cli/win_pty_bridge.py` — Dashboard `/chat` docs still say POSIX-PTY / WSL-only; this tag ships a ConPTY `WinPtyBridge`. Docs and code conflict.
- WINH01-AUD-04 — [RISK] — MEDIUM — `.github/workflows/tests.yml`; `.github/workflows/tests-os.yml`; `.github/workflows/ci.yaml` L73-92 — Default pytest suite is Linux-only. Windows CI runs only `@pytest.mark.windows_only` tests, not the full suite.
- WINH01-AUD-05 — [RISK] — MEDIUM — `.github/workflows/ci.yaml` L123-139; `.github/workflows/e2e-desktop.yml` L18-23 — Desktop Playwright E2E is Linux-only and currently hard-disabled (`if: false`).
- WINH01-AUD-06 — [GAP] — LOW — `native/fts5_cjk/build.sh` L1-19 — CJK FTS5 tokenizer builds a `.so` with `gcc`; no Windows/MSVC path in this tag.
- WINH01-AUD-07 — [PARTIAL] — MEDIUM — `tools/environments/local.py` `_find_bash` / `_windows_bash_candidates` L364-413 — Native Windows shell execution goes through Git Bash (`bash.exe`), not cmd/PowerShell; documented as the POSIX-compat strategy.
- WINH01-AUD-08 — [MATCH] — LOW — `scripts/install.ps1`; `pyproject.toml` L19-141; `website/docs/user-guide/windows-native.md` L66-79 — Default native install is `uv` plus CPython 3.11 wheels plus PortableGit/Node; no Visual Studio Build Tools required for the core path.
- WINH01-AUD-09 — [RISK] — LOW — `tests/install/KNOWN_FAILURES.md` — No in-repo `KNOWN_ISSUES.md`. The only tracked Windows issues file is historical installer/updater known-failures, not live bugs.
