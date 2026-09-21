# WINH11 Phase 6 — Synthesis: Windows Security & Deployment vs Zola Data Ownership

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Document of Truth: Privacy Plan §9 (encryption/storage/access), §7 Provider Abstraction privacy line (credentials only), §6 in-scope auth sentence which actually lives at §9 L535. Master Plan §13 cited via `WINH07-AUD-05`–`08`, not re-derived. Half B: Master Plan principles + inventory (WINH06 labels). Source: Audit_02–05.

Section 5 questions are not resolved here.

---

## Section 1 — Finding Summary Table

| ID | Half | Label | Severity | File | One-line |
|---|---|---|---|---|---|
| WINH11-AUD-01 | A | GAP | HIGH | `env_loader.py` L321–372; `secret_scope.py` L111–138 | Provider keys live in plaintext `<HERMES_HOME>/.env` |
| WINH11-AUD-02 | A | PARTIAL | MEDIUM | `vault_store.py` L187–260 | Autofill vault is Fernet; `vault.key` sits beside the ciphertext |
| WINH11-AUD-03 | A | PARTIAL | MEDIUM | `secret-storage-policy.ts` L13–65 | Desktop `safeStorage` (DPAPI) exists, default OFF, tokens only |
| WINH11-AUD-04 | A | GAP | HIGH | `hermes_state.py` L675–681; `hermes_state_dbfile.py` L553–566 | `state.db` is plain `sqlite3.connect` |
| WINH11-AUD-05 | A | GAP | HIGH | `learning_graph.py` L130–134; `state.db` | Memory markdown + session DB unencrypted at rest |
| WINH11-AUD-06 | A | PARTIAL | MEDIUM | `web_server.py` L304–311, L457–464, L636–655 | Data-mgmt gate is ephemeral SPA token, not user auth |
| WINH11-AUD-07 | A | GAP | MEDIUM | cite `WINH04-AUD-11` | DWA still absent; §9 write-gate unmet |
| WINH11-AUD-08 | A | PARTIAL | MEDIUM | `process_bootstrap.py` L387–436; `providers.py` L41 | Default `verify=True`; `http://` base_url allowed; no TLS 1.2 pin |
| WINH11-AUD-09 | A | GAP | LOW | Privacy Plan §9 L518; series scope | Distributed Presence E2E out of series — N/A |
| WINH11-AUD-10 | A | RISK | HIGH | `mcp_tool_config.py` `_build_safe_env` L96–118 | Secret-source credentials copied into MCP child env |
| WINH11-AUD-11 | A | PARTIAL | MEDIUM | `credential_files.py` L63–98; `WINH06-AUD-11`/`13` | Master stores blocked; no separate Tier 1/2 grant |
| WINH11-AUD-12 | A | RISK | HIGH | `package.json` L288; `install.ps1` L4149–4160 | Windows Desktop is built unsigned |
| WINH11-AUD-13 | A | RISK | MEDIUM | nsis block; no `deleteAppDataOnUninstall` | Uninstall leaves `HERMES_HOME` / credentials / `state.db` |
| WINH11-AUD-14 | B | ABSENT | HIGH | `.github/workflows`; `notarize.mjs` L54 | No Windows Authenticode/CI signing |
| WINH11-AUD-15 | B | MECHANISM | MEDIUM | `updater-process.ts`; `windows.ps1`; `update_cmd.py` | Custom git/zip update, not electron-updater |
| WINH11-AUD-16 | B | RISK | HIGH | `update_cmd_zip.py` L382; git path (no verify) | No commit-sig / zip checksum on updates |
| WINH11-AUD-17 | B | MECHANISM | LOW | `package.json` L300–303 | NSIS per-user, `oneClick: false` |
| WINH11-AUD-18 | B | MECHANISM | LOW | `package.json` L284–307 | NSIS+MSI targets; MSI extras unverified |
| WINH11-AUD-19 | B | MECHANISM | MEDIUM | `session-windows.ts` L46–57 | Electron `contextIsolation` + `sandbox` + no Node in renderer |
| WINH11-AUD-20 | B | RISK | MEDIUM | `windows-sandbox-fallback.ts` L15–22 | Windows can fall back to `--no-sandbox` |
| WINH11-AUD-21 | B | MECHANISM | LOW | `config_defaults.py` L2279; `vercel_sandbox.py` L44–46 | No always-on Hermes telemetry |
| WINH11-AUD-22 | B | MECHANISM | LOW | `gateway_windows.py` L152–189 | Runs as user; UAC only for gateway task install |

**Counts:** 22 findings — **7 HIGH**, **10 MEDIUM**, **5 LOW**.

HIGH: AUD-01, 04, 05, 10, 12, 14, 16. MEDIUM: AUD-02, 03, 06, 07, 08, 11, 13, 15, 19, 20. LOW: AUD-09, 17, 18, 21, 22.

Half A: 13. Half B: 9.

---

## Section 2 — What Hermes covers as-is (security & deployment)

**Direct answer:** Hermes’s current Windows security/deployment posture is a **usable foundation for a local-first agent**, not an adequate shipped-product bar for Zola-Windows without hardening. Electron renderer hardening, per-user install, user-level runtime, HTTPS-by-default cloud calls, no always-on telemetry, and a real (if custom) update orchestrator are present. Application-level encryption of credentials/memory/`state.db`, Windows code signing, and authenticated updates are not.

### Half A — Security (vs Privacy Plan §9 / scoped §7 / auth line)

Hermes already:

- Isolates provider secrets **across profiles** in a multiplexed gateway (`secret_scope.py` fail-closed).
- Encrypts **browser autofill** secrets with Fernet (`vault_store.py`).
- Offers **opt-in** Chromium `safeStorage` (DPAPI on Windows) for Desktop connection tokens — default off.
- Refuses to bind-mount master stores (`.env`, `auth.json`) into terminal sandboxes (`credential_files.py`).
- Talks to cloud providers through httpx with **certificate verification on** by default.
- Token-gates dashboard `/api/` on loopback (`WINH02-AUD-04`) and requires a real auth provider on non-loopback binds.
- Runs as the logged-in user; does not need admin for `hermes serve` / Desktop chat.

Hermes does not:

- Encrypt `.env`, `MEMORY.md`/`USER.md`, or `state.db` at rest.
- Hold vault keys away from vault data.
- Require user authentication before CLI or local-dashboard memory management.
- Implement Durable Write Authority (`WINH04-AUD-11`).
- Stop MCP children from inheriting secret-source env vars.
- Ship a signed Windows binary or a signed update channel.

Unsigned `Hermes.exe` does **not** feed `WINH07-AUD-05`–`08` (tool-approval catalog). Those remain the live-turn trust model; this phase’s authenticity gap is OS/SmartScreen/supply-chain.

### Half B — Deployment (inventory)

The Desktop path is **Hermes-owned**, not locked to an opaque vendor installer: `apps/desktop` electron-builder (NSIS + MSI), `scripts/install.ps1` pack, `scripts/desktop-update/windows.ps1` + `hermes update` (git or GitHub zip). Zola-Windows can replace signing identity, update URL, and installer branding because those knobs are in-tree — they are just **unset / disabled** for Windows today (`signAndEditExecutable: false`, no `publish` feed).

That is the WINH02/03-style “Truth Ownership” reading of deployment: the mechanism is replaceable. The **security properties** of the current mechanism (unsigned, unverified git/zip) are the problem, not an inability to own the pipeline.

Native CLI install (uv, wheels, PortableGit) remains `WINH01`; this half does not collapse into it.

---

## Section 3 — What needs a Zola-built adapter/hardening layer

For each Half A `[PARTIAL]`/`[RISK]` and each security-relevant Half B finding:

| Finding | What Zola-Windows adds on top |
|---|---|
| AUD-02 PARTIAL | Keep Fernet vault **or** wrap `vault.key` in DPAPI/Credential Manager so the key is not a sibling file. |
| AUD-03 PARTIAL | Default **on** (or wrap) Desktop `safeStorage`; extend the same DPAPI wrapper to provider `.env` (or stop using `.env` for secrets). |
| AUD-06 PARTIAL | Replace SPA-token-as-auth with a real user gate on data-management surfaces (OS login / Windows Hello / app password) even on loopback if those surfaces can read memory. |
| AUD-08 PARTIAL | Policy: refuse non-loopback `http://` `base_url`; pin TLS 1.2+; refuse MCP `ssl_verify: false` in product config. |
| AUD-10 RISK | Per-MCP env allow-list; do not dump `secret_source_names()` into third-party children. Separate authorization for Tier 1/2. |
| AUD-11 PARTIAL | Product-level “share this secret with this integration” grant on top of plugin/MCP install consent (`WINH06-AUD-11` is not that grant). |
| AUD-12 / AUD-14 | Authenticode signing step in the Zola-Windows release pipeline (own cert, not Hermes’s absent one). |
| AUD-13 RISK | Uninstall (or a first-run “remove Hermes data” tool) that purges `HERMES_HOME` after confirmation. Not a restatement of WINH04 deletion cascade — installer leftover only. |
| AUD-16 RISK | Signed update feed or `git verify-commit` / release checksum before applying `hermes update` / zip swap. |
| AUD-20 RISK | Product policy on `--no-sandbox` fallback: allow with banner, or fail closed and require ACL repair only. |

---

## Section 4 — What must be built from scratch

Real requirement gaps only (not “Hermes lacks X and Zola does not need X”):

| Capability | Why scratch | ID |
|---|---|---|
| Application-level encryption of provider credentials (or OS-keystore persistence) | `.env` is plaintext; no keyring/DPAPI on that path. Adapter can wrap, but there is no Hermes API to call. | AUD-01 |
| Encrypted `state.db` (SQLCipher or equivalent) **if** WINH00 does not accept BitLocker as “platform-standard” | Plain `sqlite3.connect`; no pragma-key path to enable. | AUD-04 |
| Encrypted canonical / episodic / preference memory at rest | `MEMORY.md` / `USER.md` / session DB are plaintext files. | AUD-05 |
| Durable Write Authority | Still absent; cite `WINH04-AUD-11`. A Windows security phase cannot retrofit DWA as a signing/installer feature. | AUD-07 |
| Windows code-signing identity + CI | No Hermes signing to inherit (`AUD-14`). Zola must bring a cert and a pipeline step. | AUD-12, AUD-14 |
| Authenticated update channel | Git/zip HTTPS is not a signed product feed. | AUD-16 |

**Filtered out of scratch work:**

- `WINH11-AUD-09` Distributed Presence E2E — out of series; not a Zola-Windows build item here.
- `WINH11-AUD-17` / `AUD-18` / `AUD-19` / `AUD-21` / `AUD-22` — inventory of things that **exist** (per-user NSIS, Electron hardening, no telemetry, user-level process). Not missing capabilities.
- `WINH11-AUD-15` — custom updater exists; the gap is integrity (`AUD-16`), not “must invent updates.”

---

## Section 5 — Open questions for WINH00

Do not resolve these here.

1. **Code signing.** Does Zola-Windows need its own Authenticode certificate and signing step in the release pipeline before any real distribution, given Phase 4 (`AUD-12`/`14`)? (Recommendation-shaped fact: Hermes will not sign Windows for you in this tag.)

2. **Credential storage.** Is wrapping secrets in Windows Credential Manager / DPAPI a WINH00-scoped build requirement, or acceptable to defer given the file already sits inside a per-user-encrypted filesystem (BitLocker) on most Windows installs? This is a product/threat-model decision (local attacker with the same user token vs disk-at-rest / stolen laptop). The audit does not resolve it.

3. **Ship bar.** Given Phase 4/5: does the current Desktop posture (unsigned binary, git/zip updates without signature, Electron sandbox with a `--no-sandbox` fallback) meet a bar the developer is comfortable shipping, or are there **blocking** items for WINH00 before any build plan is finalized? Candidates for “block ship”: AUD-12/14 (signing), AUD-16 (update integrity), AUD-01/04/05 if BitLocker is rejected as sufficient.

4. **`state.db` encryption.** Confirmed unencrypted (`AUD-04`). Is application-level encryption (SQLCipher) in scope for Zola-Windows, or is reliance on OS-disk encryption (BitLocker) considered sufficient per “platform-standard encryption at minimum” in Privacy Plan §9? Memory-specific bullets (“must be encrypted at rest”) are stricter than the general personal-data bullet — WINH00 should say which sentence governs `state.db` and `MEMORY.md`.
