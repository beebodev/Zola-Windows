# PROC1_02 — Data and Credentials

**Audit:** PROC1 · Phase 2 · read-only  
**Prompt:** v1.1 · SHA-256 `94f130a0e81abb6a56a73d0bfd00ce5ab53c550bcaffed0b1295dbe0dc1d542f`  
**Secrets policy:** names, paths, sizes, owners, which code reads — **never values**.

## Summary

Almost all durable Zola/Hermes state for the live build sits under one hard-coded profile, `%LOCALAPPDATA%\hermes\profiles\zola` (`HERMES_HOME`), plus a second tree `%LOCALAPPDATA%\ZolaClient\` for client logs, dumps, and the Deepgram key. Google OAuth is a DPAPI blob in the profile; the phone pairing key is DPAPI under `phone\`; Deepgram is a **hard-coded absolute path** outside `HERMES_HOME`. A second profile via `HERMES_HOME` alone would isolate Google tokens and phone keys **if** the client stopped hard-coding `profiles\zola` and Deepgram stopped using the absolute key path — today a “dev” client still aims at the real profile and the real Deepgram file.

## Evidence

### 1. Persistent path table

Expanded roots on this PC:  
`HERMES_HOME` → `C:\Users\test\AppData\Local\hermes\profiles\zola`  
`ZolaClient` → `C:\Users\test\AppData\Local\ZolaClient`

| Path (unexpanded → category) | Size (OBSERVED) | Reads | Writes | Path decided by | Redirect without Hermes src? |
|---|---|---|---|---|---|
| `%LOCALAPPDATA%\hermes\profiles\zola\` (profile root) | dir | serve, plugins, watcher, phone | same | Client hard-codes `profiles\zola` (`HermesProcessManager.cs` 40–44); env `HERMES_HOME` for children | **Zola-side** (change hard-code / allow override). Hermes already honors `HERMES_HOME` / `get_hermes_home()` |
| `…\config.yaml` | 4874 B | hermes serve | rare (P4-D25 edits) | under profile | via `HERMES_HOME` |
| `…\auth.json` | 4141 B | Hermes auth | Hermes | under profile | via `HERMES_HOME` (contents not opened) |
| `…\SOUL.md`, `memories\USER.md`, `MEMORY.md` | small | memory / prompt | memory tools | under profile | via `HERMES_HOME` |
| `…\state.db` (+wal/shm) | ~22 MB db | Hermes sessions | Hermes | under profile | via `HERMES_HOME` |
| `…\zola_memory\zola_memory.db` (+wal/shm) | ~254 KB db | `zola_memory` | `zola_memory` | `store.db_path(hermes_home)` (`store.py` 51–52) | via `HERMES_HOME` |
| `…\proactive\proactive.db` (+wal/shm) | ~2.9 MB db | watcher, ranker, phone ingest, surface | same | `proactive_store.default_db_path` (`proactive_store.py` 51–52, 251) | via `HERMES_HOME` |
| `…\zola_workspace\token.dpapi` | 926 B | `auth.load_token_record` | `auth` / setup | `get_hermes_home()/zola_workspace/token.dpapi` (`auth.py` 26–27, 227–236) | via `HERMES_HOME` |
| `…\zola_workspace\taint.sqlite` | 12288 B | `taint` | `taint` | under `zola_workspace` | via `HERMES_HOME` |
| `…\phone\pc_key.bin` | 498 B | `zola_phone.keys` | same | `Engine.key_dir = home/"phone"` (`runtime.py` 120, 176) | via `HERMES_HOME` |
| `…\phone\peer_state.json`, `pc_id.txt` | small | phone | phone | same | via `HERMES_HOME` |
| `…\pairing\` | empty dir OBSERVED | pairing flows | pairing | under profile | via `HERMES_HOME` |
| `…\zola-tts\deepgram_tts.py` | 5596 B | Hermes TTS command | deploy | profile + `config.yaml` command string | profile path via `HERMES_HOME`; **script still hard-codes key path** |
| `…\logs\*` | multi-MB | humans / ops | serve, plugins, watcher, phone | under profile | via `HERMES_HOME` |
| `…\plugins\zola_*` | dirs | PYTHONPATH import | mirror deploys | under profile | via `HERMES_HOME` |
| `…\sessions\`, `runtime\`, `cache\`, `skills\`, `cron\`, … | various | Hermes | Hermes | under profile | via `HERMES_HOME` |
| `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` | 40 B | `deepgram_tts.read_key` | manual/setup | **Hard-coded absolute** in `hermes-plugins/zola_tts/deepgram_tts.py` L22 **and** profile copy | **Zola-side** change to script (or env); **not** `HERMES_HOME` |
| `%LOCALAPPDATA%\ZolaClient\logs\*` | large (`presence.log` ~280 MB) | client | client | `LocalApplicationData\ZolaClient\…` in several `.cs` files | **Zola-side** (constant `ZolaClient`) |
| `%LOCALAPPDATA%\ZolaClient\dumps\*.dmp` | ~23 MB ×3 | WER / pruner | WER | `DumpPruner` under `ZolaClient\dumps` | Zola-side / WER reg (Brian-owned) |
| `%LOCALAPPDATA%\ZolaClient\debug\*` | presence JSON | presence | presence | under ZolaClient | Zola-side |
| `C:\Users\test\Dev\hermes-agent\` (+ `.venv`) | checkout | all Python children | package installs | `HermesLaunchResolver` | `ZOLA_HERMES_ROOT` / separate checkout (**Zola-side** discovery) |
| Named pipe `\\.\pipe\ZolaPhone` | n/a | serve tools ↔ phone | phone | `phone_protocol.json` `pipe_name` | **contract / Zola change**; not `HERMES_HOME` |
| TCP Tailscale `:47821` | n/a | companion ↔ phone | phone | `listen_port` 47821; override `ZOLA_PHONE_LISTEN_PORT` | env override exists; companion default 47821 in Kotlin |
| Loopback serve | dynamic port (`--port 0`) | client WS/HTTP | serve | spawn args + ready line; default constant 9119 in resolver helpers | per process |
| OAuth loopback `127.0.0.1` | ephemeral | Google redirect | `auth` setup | `auth.py` `OAUTH_LOOPBACK_HOST` | code |

Profile top-level names OBSERVED (structure only): listed in Phase 1 progress; sizes above for key stores.

### 2. Credentials inventory (names / paths only)

| Credential | Path / location | Loaded by | Account / device |
|---|---|---|---|
| Google OAuth refresh + client_id/secret blob | `%HERMES_HOME%\zola_workspace\token.dpapi` | `zola_workspace.auth` (DPAPI user-scope) | **Real account** (live authorized Workspace; sub not opened) |
| Hermes `auth.json` | `%HERMES_HOME%\auth.json` | Hermes | Provider/API material for Hermes — **UNKNOWN** which accounts without opening |
| Deepgram API key | `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` | `deepgram_tts.py` `KEY_PATH` | Deepgram project for Aura-2 TTS |
| Phone PC pairing key | `%HERMES_HOME%\phone\pc_key.bin` (DPAPI) | `zola_phone.keys` | Paired Android companion |
| Phone peer / pc id | `peer_state.json`, `pc_id.txt` under `phone\` | phone runtime | Same pairing |
| Launch secret | env `ZOLA_PHONE_LAUNCH_SECRET` (minted per client launch, popped from env) | phone + serve tools; `launch_secret.take()` | Process-local; not a durable file |
| Dashboard session token | env `HERMES_DASHBOARD_SESSION_TOKEN` | serve / client | Loopback WS auth |
| Test fixture keys | repo `contracts/phone_test_keys.json` (and historically live mirror — S100) | tests / fake_phone | Test only |

No Windows Credential Manager entries were enumerated (would need interactive tooling); DPAPI blobs above are the product stores. SOURCE for paths; Windows cred store usage **UNVERIFIED** (not found in Zola plugin code searched).

### 3. Network endpoints

| Endpoint | How chosen | Auth |
|---|---|---|
| Hermes serve `127.0.0.1:<port>` | `--port 0`; ready sentinel; attach via TCP table | Dashboard session token |
| Phone Tailscale TCP **47821** | `phone_protocol.json` `listen_port`; env `ZOLA_PHONE_LISTEN_PORT` residual | ECDSA paired keys; pairing code HMAC |
| Named pipe `\\.\pipe\ZolaPhone` | contract `pipe_name` | Launch secret on local requests |
| Google HTTPS | fixed URIs in `auth.py` | OAuth bearer from token store |
| Deepgram `https://api.deepgram.com/v1/speak` | `deepgram_tts.py` | API key file |
| OAuth loopback during setup | `127.0.0.1` ephemeral server in `auth` | one-shot redirect |

Companion finds PC via Tailscale IP + port 47821 (`CompanionService.linkUrl`, default port 47821). SOURCE.

### 4–5. Redirectability and escapes

**Redirectable with `HERMES_HOME` only (once the client sets it):** memory DB, proactive DB, token.dpapi, taint, phone keys, profile logs, config, state.db, plugins under profile.

**Needs Zola-side change (not Hermes fork):**  
- Client hard-coded `profiles\zola`  
- `%LOCALAPPDATA%\ZolaClient\…` log/dump/secret folder name  
- `deepgram_tts.py` absolute `KEY_PATH`  
- Fixed mutex/pipe/port names (see PROC1_03)  
- `ZOLA_HERMES_ROOT` already exists for Hermes checkout

**Escapes from `HERMES_HOME` / client data folder:**  
- Deepgram key under `ZolaClient\secrets` (absolute)  
- Hermes checkout + `.venv` under `Dev\`  
- `ffplay` / `uv` on PATH  
- Named pipe + port 47821 (machine-global names)  
- WER dumps under `ZolaClient\dumps`  
- Google / Deepgram cloud APIs  
- Android companion keystore (on device)

### 6. Live authorization vs what a dev profile must hold

Live profile is authorized for the **real** Google Workspace account via `token.dpapi` (setup historically `python -m zola_workspace.setup` with `HERMES_HOME` = zola profile — P8 progress). Phone pairing keys bind the **real** companion.

A dev profile would need: **test Google account only** OAuth (separate `token.dpapi`), **no** copy of live refresh token; separate phone pairing key + companion (or fake_phone); separate Deepgram key file or disabled TTS; synthetic memories. SOURCE for mechanism; account email not read (G-SECRETS).

### 7. Action-to-authority trace

| Action | Code path | Credential / pairing | If different `HERMES_HOME` only (client still hard-codes zola)? | Different `HERMES_HOME` **and** client points at it? |
|---|---|---|---|---|
| Send email | `gmail_send_draft_handler` / send gate (P8-D06) → `auth` refresh → Google | `token.dpapi` in profile | **YES** still real — client forces live profile | **NO** if token absent/test-only; empty store → reconnect / fail (no fallback to another profile found in `auth.store_path`) SOURCE |
| Calendar create/change | `gcal` handlers → `auth` | same token | **YES** | **NO** with test token only |
| Drive change | `drive` handlers → `auth` | same token | **YES** | **NO** with test token only |
| Send text via phone | phone tools / companion path → pipe → `zola-phone` → paired device | `pc_key.bin` + peer; launch secret; port 47821 | **YES** — same profile phone keys + same pipe/port | **NO** for keys if separate profile; **YES risk** if still bind 47821 / same pipe while stable holds them (contention) |
| Phone notification/command | phone runtime ↔ companion | pairing keys | same as above | same |
| Memory write | `zola_memory` / flat MEMORY.md | profile files under `HERMES_HOME` | **YES** writes live memory | **NO** with separate home |
| Proactive / watch writes | watcher + `proactive_store` | `token.dpapi` (Gmail/Calendar read) + `proactive.db` | **YES** | **NO** for data; Google still needs test token |
| TTS speak | Hermes TTS command → `deepgram_tts.py` | **hard-coded** Deepgram key path | **YES** — key path ignores `HERMES_HOME` | **YES** still real Deepgram unless key path changed |

**Fallback if expected location empty:**  
- Google: no token → needs_reconnect / setup; no scan of another profile. SOURCE `auth.store_path` single path.  
- Deepgram: `fail("deepgram: no key")`. SOURCE.  
- Phone: not paired / no_connection sentences in tools. SOURCE `phone_tools.py`.  
- Mutex/pipe held: second phone exits `EXIT_ALREADY_RUNNING` (2). SOURCE.

## Gaps against target state

| Target | Today | Gap |
|---|---|---|
| Dev resolves every persistent path under a dev root | Client hard-codes `zola`; Deepgram absolute; ZolaClient shared | Fail-open toward live data |
| Dev holds only test Google credentials | Live `token.dpapi` is the real account | Accidental send/calendar/Drive possible from any client using that profile |
| Separate phone port and pairing | Fixed 47821 + `Local\ZolaPhone` + one `pc_key` | Dev cannot safely share machine with stable phone |
| Nothing copies dev → stable | N/A until isolation exists | Shared trees mean “copy” is unnecessary — they are the same files |

## Open questions for Brian

1. Confirm the Google account on live `token.dpapi` is your real everyday account (yes/no only — do not paste identifiers).
2. Is the Deepgram key under `ZolaClient\secrets` acceptable to keep shared for early stable, or must TTS be per-profile from the first isolation cut?
3. For a first dev profile name/root preference: sibling under `profiles\` (e.g. `zola-dev`) vs entirely outside `%LOCALAPPDATA%\hermes\`?
