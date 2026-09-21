# WINH11 Audit 02 — Secrets and Credential Storage

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola Privacy and Data Ownership Plan.md` §9 Encryption and Storage Security (data at rest, memory-specific encryption, Access Control). One Access Control line is also the in-scope fragment the prompt attached to §6; the sentence itself lives at §9 L535, not in §6 L361–399. Master Plan §13 is cited, not re-derived (`WINH07-AUD-05`/`06`/`07`/`08`).

Half A labels: `[MATCH]` / `[GAP]` / `[RISK]` / `[PARTIAL]`.

---

## 1. Where provider API keys / credentials live on disk

**Canonical store:** plaintext dotenv at `<HERMES_HOME>/.env`.

`hermes_cli/env_loader.py` `load_hermes_dotenv` (L321–406) loads, in order:

1. `<home>/.env` with `override=True` (L354, L362–365) — this is the user/profile credential file.
2. `<home>/.op.env` with `override=False` if `OP_SERVICE_ACCOUNT_TOKEN` is unset (L367–372) — gitignored 1Password bootstrap token.
3. Optional project `.env` as a dev fallback (L374–376).
4. Optional external secret sources (Bitwarden / 1Password / similar) via `_apply_external_secret_sources` (L391–392), which **inject values into `os.environ`**, they are not a second on-disk encrypted store for the keys themselves.
5. Managed-scope `.env` overlay (`_apply_managed_env`, L393).

`agent/secret_scope.py` is **not a disk format**. It is a fail-closed `ContextVar` overlay so a multiplexed gateway does not union every profile’s keys into `os.environ` (module docstring L1–11; `get_secret` L111–138). When multiplexing is off, `get_secret` falls through to `os.environ` (L128, L138). The values in that mapping come from the same dotenv / external-source load.

Searched `agent/` and `hermes_cli/` for `import keyring` / `from keyring`: **no hits**. `pyproject.toml` has no `keyring` dependency. Provider keys are not written to Windows Credential Manager.

**Related files (not the LLM-provider key store):**

| Path | What |
|---|---|
| `<HERMES_HOME>/.env` | Provider API keys, tokens, secrets (KEY=value) |
| `<HERMES_HOME>/.op.env` | 1Password service-account bootstrap |
| `<HERMES_HOME>/vault/vault.json.enc` + `vault.key` | Browser autofill vault (passwords/cards/addresses), **not** OpenRouter/OpenAI keys — `agent/vault_store.py` L1–16, L187–195 |
| Electron `userData` token store | Remote-gateway / CF-Access / OAuth tokens via `safeStorage` (`apps/desktop/electron/secret-storage-policy.ts`, `native-token-store.ts`) — **not** the CLI `.env` |

**Label:** `[GAP]` `WINH11-AUD-01` (HIGH) — provider credentials persist as plaintext `.env` / `.op.env` under `HERMES_HOME`. `secret_scope.py` isolates profiles in memory; it does not encrypt the file.

---

## 2. Is that storage encrypted at rest? OS-native credential store?

**`.env` / `.op.env`:** no application-level encryption. `load_dotenv` reads text. File-mode hardening (`0o600` on Unix) is a permission policy, not encryption; on NTFS that chmod does not become DPAPI.

**Browser vault:** yes, Fernet (`cryptography.fernet`) — `vault_store.py` L10–11, L241–260. Payload file `vault.json.enc`. This is **autofill secrets**, not model-provider keys.

**Desktop `safeStorage`:** Chromium OS keychain (DPAPI on Windows, Keychain on macOS). Confirmed present (`apps/desktop/electron/main.ts` L25, L7934–7950; `hardening.ts` L156–195). **Default is OFF:** `secret-storage-policy.ts` L13–17, L48–65 (`on: false`). Even when ON, it covers Desktop connection tokens, not `<HERMES_HOME>/.env`.

**Windows Credential Manager / DPAPI / `keyring` for provider keys:** searched; **not used**. No `win32cred`, `CryptProtectData`, or `keyring` binding in `agent/` or `hermes_cli/`.

Zola §9: “all personal data stored on-device must be encrypted using platform-standard encryption at minimum.” Hermes does not invoke BitLocker, EFS, or DPAPI for `.env`. Optional full-disk BitLocker is an OS setting, not a Hermes mechanism — see WINH00 open question 2/4.

**Label:** `[PARTIAL]` `WINH11-AUD-03` (MEDIUM) — a real DPAPI-capable path exists in the Desktop shell and is **opt-in and scoped to shell tokens**. Default plaintext. Provider `.env` never uses it.

---

## 3. Encryption keys separate from encrypted data?

Zola §9: “encryption keys must not be held by the same service that holds the encrypted data.”

The only application-level at-rest encryption found for user secrets is the autofill vault:

- Data: `<HERMES_HOME>/vault/vault.json.enc`
- Key: `<HERMES_HOME>/vault/vault.key` — same directory, same process, locally generated `Fernet.generate_key()` (`vault_store.py` L194–195, L245–260). Design note L10–11: “default frictionless, 0600 files OK.”

Anyone who can read `HERMES_HOME` can read both files and decrypt. The key is not in an OS keystore, KMS, or separate principal.

`.env` and `state.db` have **no** key because they are not encrypted.

**Label:** `[PARTIAL]` `WINH11-AUD-02` (MEDIUM) — Fernet at rest for the vault payload exists; key co-location violates the Zola key-separation rule. Not a `[MATCH]`.

---

## 4. `state.db` encryption status

**Settled: plain SQLite, not SQLCipher.**

Writer open path:

- `hermes_state.py` `_open_writer_conn` L675–681 calls `_connect_tracked_db(...)`.
- `hermes_state_dbfile.py` `_connect_tracked_db` L553–566: `sqlite3.connect(str(path), **kwargs)` (or the same via `connect_tracked`).
- Pragmas applied after connect: WAL, foreign_keys, FTS (`hermes_state.py` L684–695). **No `PRAGMA key`.**

Searched the Hermes tree for `sqlcipher` / `PRAGMA key`: **no production hits**. Tests open `state.db` the same way (`sqlite3.connect`).

`_secure_state_db_files` tightens file permissions / creates the file before connect (`hermes_state.py` L705–707) — ACL/umask, not encryption.

Session transcripts, tool results, and other durable session state in this DB are therefore readable as a SQLite file to any process running as the same user (or anyone who can read `HERMES_HOME`).

**Label:** `[GAP]` `WINH11-AUD-04` (HIGH) — `state.db` is unencrypted SQLite. Directly bears on “structured canonical memory / episodic memory … encrypted at rest” for whatever of those layers lives in this DB (cross-ref WINH04 storage: MEMORY.md is a separate plaintext file; see AUD-05).

---

## 5. Access control before data-management capability

Zola §9 L535: “authentication must be required before any user-facing data management capability is accessible.”

**Dashboard (loopback — the Desktop-owned path):**

- `should_require_auth` is **False** on `localhost` / `127.0.0.1` / `::1` (`web_server.py` L457–464).
- `auth_middleware` (L636–655) still requires the process-ephemeral `_SESSION_TOKEN` (`X-Hermes-Session-Token` / Bearer) on `/api/` except a public allow-list.
- Token mint: `HERMES_DASHBOARD_SESSION_TOKEN` or `secrets.token_urlsafe(32)` per process start (L304–311). Injected into the SPA HTML so the UI can call APIs.
- This is the same mechanism as `WINH02-AUD-04`. It is a **session identifier / CSRF token for the local SPA**, not user authentication (no password, no OS login prompt, no identity). Anyone who can read the HTML or the env of that process can call memory/config APIs.
- Non-loopback binds **do** require a dashboard auth provider (`should_require_dashboard_auth` L467–478; startup refuses if none, L1118–1122). That is real authentication — and it is not the default Desktop path.

**CLI:** `hermes memory` (`main_agent_cmds.py` `cmd_memory` L59–67) and vault CLI (`hermes_cli/vault.py`) have no user authentication. The OS account that can run the binary is the gate.

**Desktop JSON-RPC / vault panel:** `tui_gateway/methods_vault.py` is the Settings → Credential Vault door on the localhost WS channel. Profile scoping exists (`params.profile`); there is no second user-login step on that channel.

**Durable Write Authority** (same Access Control subsection, L533): already scored `WINH04-AUD-11` `[GAP]`. Not re-derived. Cited here because §9 names DWA as the memory-write gate.

**Label:** `[PARTIAL]` `WINH11-AUD-06` (MEDIUM) — loopback data-management APIs are token-gated (`WINH02-AUD-04`); the token is not authentication. CLI has none. Public-bind OAuth/password **is** authentication when that deployment is used.

**Label:** `[GAP]` `WINH11-AUD-07` (MEDIUM) — DWA still absent (`WINH04-AUD-11`). §9 Access Control requires it; this phase does not reopen the memory-agency cascade.

---

## Memory files at rest (same §9 memory bullets)

Default canonical/profile memory is markdown under `HERMES_HOME` (`MEMORY.md`, `USER.md` — `agent/learning_graph.py` L4, L130–134). No encryption wrapper was found around those writes. Combined with unencrypted `state.db`, the memory-specific §9 bullets are unmet.

**Label:** `[GAP]` `WINH11-AUD-05` (HIGH) — structured / episodic / preference memory is stored as plaintext files and/or plaintext SQLite, not encrypted at rest by Hermes.

---

## Finding table (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH11-AUD-01 | GAP | HIGH | `env_loader.py` L321–372; `secret_scope.py` L111–138 | Provider keys live in plaintext `<HERMES_HOME>/.env` |
| WINH11-AUD-02 | PARTIAL | MEDIUM | `vault_store.py` L187–260 | Autofill vault is Fernet; `vault.key` sits beside `vault.json.enc` |
| WINH11-AUD-03 | PARTIAL | MEDIUM | `secret-storage-policy.ts` L13–65 | Desktop `safeStorage` (DPAPI) exists, default OFF, tokens only |
| WINH11-AUD-04 | GAP | HIGH | `hermes_state.py` L675–681; `hermes_state_dbfile.py` L553–566 | `state.db` is plain `sqlite3.connect` |
| WINH11-AUD-05 | GAP | HIGH | `learning_graph.py` L130–134; `state.db` path | Memory markdown + session DB unencrypted at rest |
| WINH11-AUD-06 | PARTIAL | MEDIUM | `web_server.py` L304–311, L457–464, L636–655 | Data-mgmt gate is ephemeral SPA token, not user auth |
| WINH11-AUD-07 | GAP | MEDIUM | cite `WINH04-AUD-11` | DWA still absent; §9 write-gate unmet |
