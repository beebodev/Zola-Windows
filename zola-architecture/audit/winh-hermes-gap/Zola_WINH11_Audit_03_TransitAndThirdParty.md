# WINH11 Audit 03 — Transit Encryption and Third-Party Data Boundaries

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Privacy Plan §9 “Data in transit” (TLS 1.2+ device↔cloud); §7 “Provider Abstraction and Replaceability” **privacy dimension only** (credentials / third-party access — swapability is `WINH07`, not re-audited). Distributed Presence endpoint-to-endpoint encryption is **out of series scope** (recorded environmental-scope decision); noted, not searched.

Half A labels.

---

## 1. TLS enforcement to cloud model/tool providers

Zola §9 L517: “all data transmitted between the device and any cloud service must use TLS 1.2 or higher.”

**Default outbound path:** `agent/process_bootstrap.py` `build_keepalive_http_client` (L387) builds `httpx.Client` / `AsyncClient` with `verify: Any = True` and mounts both `http://` and `https://` transports (L422–436). Certificate verification is on by default. There is **no explicit TLS 1.2 minimum** (`ssl.TLSVersion.TLSv1_2` or equivalent) in this client builder — modern httpx/OpenSSL defaults are TLS 1.2+ in practice, but Hermes does not pin the floor.

**HTTPS is not mandatory for a configured provider.** Custom `model.base_url` may be `http://`:

- Setup docs: `hermes_cli/setup.py` L90 — `hermes config set model.base_url http://localhost:8080/v1`.
- Built-in LM Studio overlay: `hermes_cli/providers.py` L41 — `base_url_override="http://127.0.0.1:1234/v1"`.

Those loopback cases are local inference, not “cloud,” but the same config key is how a user would point at any OpenAI-compatible host, including a cleartext remote URL. No allow-list was found that refuses `http://` for non-loopback hosts.

**MCP HTTP:** `tools/mcp_tool_transport.py` L415 — `config.get("ssl_verify", True)`. Default verify-on; a server entry can set `ssl_verify: false`. URL scheme is whatever the MCP config contains (`http` or `https`).

**Distributed Presence E2E:** Privacy Plan §9 L518. Not an audited domain in this series. No finding hunt was run.

**Label:** `[PARTIAL]` `WINH11-AUD-08` (MEDIUM) — default cloud calls go through httpx with `verify=True` (HTTPS + cert check). No TLS 1.2 pin; plaintext `http://` is a first-class `base_url`; MCP can disable verify.

**Label:** `[GAP]` `WINH11-AUD-09` (LOW) — Distributed Presence endpoint-to-endpoint encryption is out of WINH series scope; treated as not applicable here, not as Zola-Windows scratch work.

---

## 2. Credentials sent to third-party integrations — separate authorization?

Zola §9 L534: “Tier 1 and Tier 2 data must not be accessible to third-party integrations without explicit separate authorization.”

§7 Provider Abstraction privacy line (L447): do not strand user data with a provider; replaceability’s privacy dimension. This phase asks whether **credentials/secrets** for third parties are handled securely, not whether providers are swappable (`WINH07`).

**MCP child environment.** `tools/mcp_tool_config.py` `_build_safe_env` L96–118:

- Starts from a **filtered** `os.environ` (`_SAFE_ENV_KEYS` plus `XDG_*`).
- Then, for every name returned by `secret_source_names()` (Bitwarden / 1Password / other external sources that tagged an env var), copies `get_secret(key)` into the child env (L108–111).
- Then merges the server config’s own `env` dict (L115–116).

So: a third-party MCP stdio server, once configured, receives **every externally sourced credential that `get_secret` can resolve for the active profile**, plus whatever the operator put in `mcp_servers.<name>.env`. There is no second prompt of the form “allow this MCP to see `OPENROUTER_API_KEY`.” Installing/enabling the server **is** the authorization. That is not Zola’s “explicit separate authorization” for Tier 1/2.

**Credential file passthrough** (`tools/credential_files.py`): used to mount host files into Docker/Modal/SSH sandboxes, not MCP-by-default. Positive control: master stores (`.env`, `auth.json`, `mcp-tokens/`) are **refused** even when they sit inside `HERMES_HOME` (L63–98, fail-closed if `file_safety` cannot be imported). Skill-declared `required_credential_files` and `terminal.credential_files` **are** registered if they pass containment + deny-list. Presence of those files in the skill/config **is** the authorization; there is no extra per-file user grant at mount time.

Plugin install consent (`WINH06-AUD-11`: CLI/TUI, `plugin_guard`, `plugins.enabled`) is capability consent to **run** the plugin, not a per-secret ACL. In-process plugins “are expected to read their own env keys” (`WINH06-AUD-13` / `plugin_guard.py` L3–4) — once enabled they see the same process environment the agent sees.

**Label:** `[RISK]` `WINH11-AUD-10` (HIGH) — `_build_safe_env` injects profile secret-source credentials into MCP subprocesses without a separate Tier 1/2 authorization step.

**Label:** `[PARTIAL]` `WINH11-AUD-11` (MEDIUM) — master credential files cannot be sandbox-mounted (`credential_files.py` deny-list); skill-scoped files and MCP `env` still flow on “configured/present,” not on a distinct data-sharing grant. Cite `WINH06-AUD-11` (install consent) and `WINH06-AUD-13` (same-user / in-process), not re-derived.

---

## 3. MCP server credential handling vs WINH06

`WINH06-AUD-11` established: plugin install is a human CLI/TUI path with `plugin_guard` and `plugins.enabled` opt-in. MCP add on Desktop has a consent card; non-desktop `hermes mcp add` via `terminal` does not (`WINH06-AUD-10`).

`WINH06-AUD-13` established: MCP stdio children run as the **same OS user**; no extra sandbox. Plugins load in-process and may read env keys.

This phase’s security lens adds what WINH06’s capability-inventory lens did not: **which secrets enter that child.** `_build_safe_env` is the new finding (`WINH11-AUD-10`). WINH06 is not restated as a new ID.

No evidence was found of an MCP-specific secret vault or per-server allow-list of env-var names beyond the config’s own `env` map plus the global secret-source dump.

---

## Finding table (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH11-AUD-08 | PARTIAL | MEDIUM | `process_bootstrap.py` L387–436; `providers.py` L41 | Default `verify=True`; `http://` base_url allowed; no TLS 1.2 pin |
| WINH11-AUD-09 | GAP | LOW | Privacy Plan §9 L518; series scope | Distributed Presence E2E out of series — N/A, not scratch |
| WINH11-AUD-10 | RISK | HIGH | `mcp_tool_config.py` `_build_safe_env` L96–118 | Secret-source credentials copied into MCP child env |
| WINH11-AUD-11 | PARTIAL | MEDIUM | `credential_files.py` L63–98; cite `WINH06-AUD-11`/`13` | Master stores blocked; no separate Tier 1/2 grant for the rest |
