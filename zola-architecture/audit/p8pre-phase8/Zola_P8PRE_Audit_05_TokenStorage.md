# Zola P8PRE Audit 05 — Token Storage on Windows

**Date:** 2026-10-07  
**Labels vs:** `H2`, `H6`, `P2-D17`, `S16`

---

## 1. What Hermes does today

| Fact | Citation |
|------|----------|
| Secrets live in plaintext `<HERMES_HOME>/.env` when present | WINH11 Audit 02; `env_loader` |
| Live zola profile: **no `.env` file** | Phase 1 |
| No `keyring` in agent pin | WINH11_02 |
| Desktop `safeStorage` DPAPI path exists but default OFF; not for `.env` | WINH11_02 |
| Workspace skill token: plaintext `google_token.json` | `setup.py` L43–45 |
| H6 `_build_safe_env` re-injects secrets into MCP subprocesses | `mcp_tool_config.py` L96–118; WINH11-AUD-10 |
| Terminal children scrub some provider env keys; **files still readable via shell** | `local.py` |
| `file_safety` denies `.env` for `read_file` but documents terminal bypass; **`google_token.json` not in deny list** | `file_safety.py` L192–202 |

---

## 2. Options (installed only)

| Option | Install? | H-5 result | Who can read | Password reset | Offline disk |
|--------|----------|------------|--------------|----------------|--------------|
| Plain file in profile (`H2` posture) | No | N/A (today’s skill path) | Same-user processes, terminal | Survives | Readable if BitLocker off |
| DPAPI file (`win32crypt.CryptProtectData`) | No | Round-trip OK; blob 272B for 40B synthetic; file deleted | Same Windows user | Typically lost | Hard without user key |
| Credential Manager (`win32cred`) | No | Write/delete OK; `CRED_MAX_VALUE_SIZE=256`; blob size constant **not exported**; read type bytes (encoding nuance on round-trip check) | Same user via CredRead | User-scoped typically lost | Not as plain file |
| `keyring` package | **Yes** | Not probed | — | — | — |

Refresh token ≤512B `[EXT]` fits CredMan value size; full `google_token.json` (client_secret + scopes JSON) may need DPAPI file.

---

## 3. The honest limit (LEAD-3 / terminal)

Serve, terminal, and plugins run as Brian. **None of the options above stop the terminal tool** from calling `CryptUnprotectData` / `CredRead` / reading a plaintext file as the same user.

Mechanisms short of editing hermes-agent:

| Mechanism | Stops terminal? | Bypass |
|-----------|-----------------|--------|
| `file_safety` deny | No | Terminal |
| `pre_tool_call` block on token paths / googleapis hosts | Partial | `execute_code`, alternate hosts, encoding, child agents |
| Separate user / broker process | Would, if built outside pin | Needs OS design; not present |
| BitLocker | Offline disk only | Not runtime terminal |

**No airtight credential isolation from terminal at this pin.**

---

## 4. Exposure paths

| Path | Plugin controls? |
|------|------------------|
| `state.db` tool results | No — avoid echoing tokens in results |
| Logs / trajectories / spillover | Partial (don’t log secrets; Hermes may still persist tool output) |
| Crash dumps (`S51`) | No |
| Client logs | No (P4-D12 already avoids approval bodies) |
| Profile backups | No |

---

## 5. `H2` revisit facts

`H2` deferred Credential Manager/DPAPI; accepted BitLocker-at-rest. Google refresh tokens grant mailbox access until revoked — higher blast radius than many API keys. BitLocker status this session: **unknown** (`manage-bde` access denied without elevation). Do not decide.

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-25 | [MATCH] | — | Hermes plaintext `.env` / skill `google_token.json` posture matches `H2`. |
| P8PRE-AUD-26 | [RISK] | HIGH | No storage option at this pin keeps tokens from the terminal tool (same user). |
| P8PRE-AUD-27 | [MATCH] | — | DPAPI round-trip works with installed `pywin32` (H-5); CredMan usable with size caveats. |
| P8PRE-AUD-28 | [RISK] | MEDIUM | H6 MCP env re-injection + `google_token.json` not in `file_safety` deny list. |
