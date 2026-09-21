# WINH11 Audit 04 — Windows Desktop Build, Signing, and Update Mechanism

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Half B inventory (no dedicated Zola deployment doc): `[MECHANISM]` / `[RISK]` / `[ABSENT]` / `[UNVERIFIED]`, WINH06 convention.

Security-adjacent items (unsigned binary, leftover data on uninstall) are **also** Half A vs Privacy Plan §9 / trust-authenticity.

Not re-audited: native CLI/service install (`WINH01-AUD-08` and related) — this document is `apps/desktop` only.

Pre-audit claims in the prompt were **verified** against this tag, not restated from the prompt alone.

---

## 1. Code signing

**electron-builder `win` block** (`apps/desktop/package.json` L282–288):

```json
"win": {
  "legalTrademarks": "Hermes",
  "target": ["nsis", "msi"],
  "signAndEditExecutable": false
}
```

`signAndEditExecutable: false` disables electron-builder’s rcedit **and** the signtool path that would pull `winCodeSign`.

**Installer confirms this is intentional, not an incomplete snippet.** `scripts/install.ps1` L4149–4160:

- Sets `CSC_IDENTITY_AUTO_DISCOVERY=false`.
- Combined with `signAndEditExecutable=false`, “electron-builder never invokes signtool and therefore never fetches/extracts winCodeSign.”
- Explicitly **clears** `WIN_CSC_LINK` and `WIN_CSC_KEY_PASSWORD` so a leftover env cannot silently sign.

Icon/product name are stamped by `afterPack` (`apps/desktop/scripts/after-pack.mjs`) via rcedit, **decoupled from signing** (`install.ps1` L4292–4298).

**`afterSign`:** top-level `"afterSign": "scripts/notarize.mjs"` (`package.json` L228). `notarize.mjs` L52–54: `if (electronPlatformName !== 'darwin') return`. Apple notary only. No Windows branch.

**CI search:** `.github/workflows/*.yml` — no `signtool`, Authenticode, Azure Trusted Signing, or DigiCert. No Windows signing job.

**Conclusion (not `[UNVERIFIED]`):** this tag’s Windows Desktop artifact is **built unsigned** on the documented pack/install path. A hypothetical out-of-repo signing service was not found in this repository.

Half A: unsigned binaries trigger SmartScreen and give the user no publisher identity. Privacy Plan does not name Authenticode, but authenticity of the binary that will hold Tier 1/2 data is security-relevant. Master Plan §13 / `WINH07-AUD-05`–`08` are the **tool-approval** catalog — an unsigned `Hermes.exe` does **not** participate in that overlay (no finding that approval checks Authenticode). The risk is OS-trust / supply chain, not a silent `approvals.mode: smart` interaction.

**Label (Half A):** `[RISK]` `WINH11-AUD-12` (HIGH) — Windows Desktop ships unsigned; SmartScreen / no publisher identity.

**Label (Half B):** `[ABSENT]` `WINH11-AUD-14` (HIGH) — no Authenticode / `signtool` / CI signing step in this tag.

---

## 2. Update mechanism

**Not `electron-updater`.** `apps/desktop/package.json` has no `electron-updater` dependency and no `publish` block. `npm run pack` uses `--publish never` (pre-audit confirmed in this tag’s scripts).

**What actually runs:**

1. Desktop Update button hands off to `scripts/desktop-update/windows.ps1` (`apps/desktop/electron/updater-process.ts` L14, L51–52, L77, L96). Spawned via `cmd start` + PowerShell `-File` (script header L19–27).
2. `windows.ps1` is **repo-owned** so `hermes update` refreshes the orchestrator itself (header L3–17). It is not a frozen `hermes-setup.exe` self-updater.
3. The orchestrator waits out the Desktop PID, then runs **`hermes update`** against the checkout under `HERMES_HOME\hermes-agent`.
4. `hermes_cli/update_cmd.py` `_cmd_update_impl` (L1280+): git path is scoped `git fetch` + fast-forward (L1335–1336, comments at L807); Windows fallback is ZIP (`update_cmd_zip.py` L382) from `https://github.com/NousResearch/hermes-agent/archive/refs/heads/{branch}.zip`.
5. `scripts/desktop-update/repro.sh` is a **sandbox repro driver** (fresh/behind/error/gate/shim) against `posix.sh` / the real installer — not the production Windows updater.

**Integrity:**

- Transport is HTTPS to GitHub (TLS).
- Searched `update_cmd_git.py` for `verify-commit` / `gpg` / signature: **no hits**.
- Searched `update_cmd_zip.py` for `sha256` / `checksum` / `hashlib`: **no hits**. Zip swap is download-and-replace; `_verify_and_restore_state_dbs_post_update` checks **SQLite integrity after the swap**, not artifact authenticity.
- No signed update feed, no Authenticode check of a newly built `Hermes.exe` after desktop rebuild.

A compromised GitHub account, a MITM that still presents a valid GitHub cert (unlikely), or an unsigned malicious commit on `main` would be applied. HTTPS is not an update-signing scheme.

**Label:** `[MECHANISM]` `WINH11-AUD-15` (MEDIUM) — custom `windows.ps1` → `hermes update` (git or GitHub zip); not electron-updater.

**Label:** `[RISK]` `WINH11-AUD-16` (HIGH) — updates authenticated only by HTTPS to GitHub; no commit signature or zip checksum.

---

## 3. Install scope and privilege

`package.json` `nsis` block L300–307:

- `perMachine: false` — per-user install, no admin elevation required to install.
- `oneClick: false` — user chooses directory (`allowToChangeInstallationDirectory: true`).

This is a least-privilege-relevant fact, not a Zola requirement match.

**Label:** `[MECHANISM]` `WINH11-AUD-17` (LOW) — NSIS per-user, directory chooser, no elevation to install.

---

## 4. Uninstall completeness

Searched `apps/desktop/package.json` for `deleteAppDataOnUninstall` / `removeAppData`: **absent**. electron-builder NSIS uninstall removes the application directory (binaries, unpacked `Hermes.exe` tree). It does **not** document a purge of:

- `HERMES_HOME` (default `%USERPROFILE%\.hermes`) — `.env`, `state.db`, `MEMORY.md`, `vault/`, snapshots.
- Electron `userData` (`%APPDATA%\Hermes` and friends) — connection-token store, sandbox-fallback marker.

`install.ps1` Start Menu / Desktop shortcuts point at the packed exe (L4317+); those shortcuts are typical NSIS uninstall targets. User data lives **beside**, not inside, that tree.

Half A: “uninstall” does not implement a deletion/forget of Tier 1/2 data. Full deletion cascade remains `WINH04`’s domain; this is only the installer-uninstall leftover.

**Label (Half A):** `[RISK]` `WINH11-AUD-13` (MEDIUM) — NSIS/MSI uninstall leaves `HERMES_HOME` credentials, `state.db`, and memory files on disk.

---

## 5. MSI vs NSIS

Both are `win.target` (`package.json` L284–287). There is an `nsis` config block and **no** `msi` block.

| Property | NSIS | MSI |
|---|---|---|
| Per-user (`perMachine: false`) | Explicit | **Not set** in this file |
| Directory chooser | Explicit | WiX/electron-builder defaults |
| Signing | Both unsigned (`signAndEditExecutable: false` applies to `win`) | Same |
| Custom NSIS script | electron-builder generated | Windows Installer service |

They are **not documented as security-equivalent**. MSI may still be a per-user package under electron-builder defaults, but that was not confirmed from a generated `.wxs` in this tag (generated at pack time). Treat privilege/repair/rollback differences as unverified from static reading.

**Label:** `[MECHANISM]` `WINH11-AUD-18` (LOW) — two installer targets; NSIS security-relevant knobs are explicit; MSI extra properties `[UNVERIFIED]` without a generated WiX script. Both inherit unsigned `win`.

---

## Finding table (this phase)

| ID | Half | Label | Severity | File | One-line |
|---|---|---|---|---|---|
| WINH11-AUD-12 | A | RISK | HIGH | `package.json` L288; `install.ps1` L4149–4160 | Windows Desktop is built unsigned |
| WINH11-AUD-13 | A | RISK | MEDIUM | `package.json` nsis block; no `deleteAppDataOnUninstall` | Uninstall leaves `HERMES_HOME` / credentials / `state.db` |
| WINH11-AUD-14 | B | ABSENT | HIGH | searched `.github/workflows`; `notarize.mjs` L54 | No Windows Authenticode/CI signing |
| WINH11-AUD-15 | B | MECHANISM | MEDIUM | `updater-process.ts`; `windows.ps1`; `update_cmd.py` | Custom git/zip update, not electron-updater |
| WINH11-AUD-16 | B | RISK | HIGH | `update_cmd_zip.py` L382; `update_cmd_git.py` (no verify) | No commit-sig / zip checksum on updates |
| WINH11-AUD-17 | B | MECHANISM | LOW | `package.json` L300–303 | NSIS per-user, `oneClick: false` |
| WINH11-AUD-18 | B | MECHANISM | LOW | `package.json` L284–307 | NSIS+MSI targets; MSI extras unverified |
