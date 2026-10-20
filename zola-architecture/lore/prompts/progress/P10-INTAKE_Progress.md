# P10-INTAKE Progress — zola-phone and the fake phone

## Branch

- Primary folder: `C:\Users\test\Dev\zola-windows`, branch `main`
- Worktree: `C:\Users\test\Dev\zola-windows-p10-intake`, branch `p10-intake`
- Base SHA: `7023e42d0059a3413358e02d4c24697118978236` (`main` = `origin/main` at Phase 1)
- Worktree HEAD: `7023e42d0059a3413358e02d4c24697118978236`
- Hermes HEAD: `345cd2b057a452236de401d3534b8502a7465e8d` (detached `HEAD`, clean, no porcelain)
- Prompt: `P10-INTAKE_Prompt_v1.1.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P10-INTAKE_Prompt_v1.1.md`)
- Prompt SHA-256 (on-disk, 35,227 bytes): `756699e0401d486154b76aa265622d05bcfe005fa889c8cd4de52a5f14e6e895`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction. On-disk value recorded for Brian to confirm.
- Scratch: `C:\Users\test\Dev\zola-spikes\p10-intake\` (created, empty)
- Track 1 closeout tip this branch was cut from: `7023e42d0059a3413358e02d4c24697118978236` (merge `c9677297e50ce0a2c2d45d59f171e506eeb04642`, then the docs commit)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Setup | COMPLETE (STOP) |
| 2 | Grounding | COMPLETE (STOP) |
| 3 | Proposal | COMPLETE (STOP) |
| 4 | Implement | COMPLETE (STOP) |
| 5 | Review checkpoint | COMPLETE (STOP) |
| 6 | Deploy and smoke | COMPLETE (STOP) — smoke test passed |
| 7 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** `zola-phone` process module(s), the serve-side client module, a phone status gateway method only if IN-G8 needs one, the fake phone, tests, client supervision, the COMPANION WATCHER row, a pairing-code display, this progress doc, and (Phase 6 only) the live plugin mirror and a new key folder.
- **G-ARCH:** build plan v1.4 and Appendices A/B are truth. IN-G1, IN-G6, IN-G7, and IN-G8 stop for Brian.
- **G-PATTERN:** read every file in full before changing it.
- **G-NOCHANGE:** no `hermes-agent` edits; no Android code; no `watcher.py`, `ranker.py`, `surface.py`, or `speech.py` logic changes; no Gmail/Calendar/Drive/Contacts module changes; no `SOUL.md`, identity, lore, or `config.yaml` edits unless Phase 3 approves an exact line; no Track 1 store-rule changes unless Phase 3 approves one. No installs.
- **G-ONE-ROUTE:** only `zola-phone` opens or holds a connection to the phone.
- **G-ISOLATION:** runtime `sys.modules` proof that the process never imports Google, auth, send, ranker, or Hermes agent/model modules.
- **G-COMMIT-BEFORE-ACK:** no ack before the store transaction commits.
- **G-RESEND:** a resent item is a new signed envelope (new higher `seq`, current `sent_at_ms`). Replay and stale checks apply to envelopes; duplicate handling applies to item identity.
- **G-SUPERSEDE-AFTER-AUTH:** a new connection replaces the current one only after its first frame passes every Appendix B §3 check.
- **G-SIZE-FIRST:** raw frame ceiling (256 KiB) before parse or signature. Precedence: raw size → `malformed` → §3 order → field limits (`too-large`) → store reasons.
- **G-ONE-WRITER:** one writer per connection on the PC side.
- **G-BIND:** Tailscale address and the dedicated port only. Never `0.0.0.0`, never a LAN address, never 8765. Resolve the address at runtime.
- **G-SECRETS:** PC pairing key DPAPI-protected, user-only ACL, never in the repo, logs, or this doc. `phone_test_keys.json` is never loaded at runtime and is excluded from the live mirror. Phase 6 removes the Track 1 live copy and checks it absent. Pairing codes are never logged.
- **G-PRIVACY:** synthetic `555` numbers and `ZP10-` bodies only. Logs carry hashed item keys, counts, reasons, and timings.
- **G-PROCESSES:** stop only processes this track started, by PID. Never stop by port.
- **G-COMMENT:** `# P10-INTAKE: <why> — P10-D12` / `// P10-INTAKE: …`. Named constants; contract values from `phone_protocol.json`.
- **G-STOP / G-CLOSEOUT / G-LORE-SCOPE / G-LIVE:** no lore edits. Live steps one at a time, Phase 6 only.

## Phase 1 — Setup

Worktree list after `git fetch origin` and before `git worktree add` (primary only):

```
C:/Users/test/Dev/zola-windows  7023e42 [main]
```

`git status --porcelain` on `main` was empty. `main` = `origin/main` = `7023e42d0059a3413358e02d4c24697118978236`.

After the worktree:

```
C:/Users/test/Dev/zola-windows             7023e42 [main]
C:/Users/test/Dev/zola-windows-p10-intake  7023e42 [p10-intake]
```

Primary `main` stayed clean. Hermes stayed clean at the pin. No source files were modified.

### Plugin suites (worktree, Hermes venv)

| Suite | Command | Result |
|---|---|---|
| `zola_workspace` | `python -m unittest discover -s tests -t tests` | 357 OK |
| `zola_memory` | `python -m unittest discover -s tests -t .` | 134 OK |
| `zola_tools` | `python -m unittest discover -s tests -t .` | 44 OK |
| `zola_tts` | `python -m unittest discover -s tests -t .` | 8 OK |

Matches the Track 1 close: **357 / 134 / 44 / 8**.

### Client

`dotnet build windows-client\Zola.Client\Zola.Client.csproj`: succeeded, 0 warnings, 0 errors.

`dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj`: exit 0. Every row PASS.

| Check row | Count |
|---|---|
| lifecycle | 22/22 |
| admission | 13/13 |
| start | 9/9 |
| invalid pairs | 6/6 |
| stop_phrase | 4/4 |
| amendments | 7/7 |
| latch | 18/18 |
| wiring | 9/9 |
| clarify | 20/20 |
| timing | 8/8 |
| compress | 8/8 |
| supervision | 38/38 |
| speech | 38/38 |

### Live profile (read only)

`config.yaml` SHA-256: `823dbd95c6d63eb66be07182faa82acb5c48528a79f01109b6c4120560c74afc` (same as the P10-STORE close).

`proactive.db` opened `mode=ro` with `query_only`. `PRAGMA user_version` 0. `meta.schema_version` **6**. `integrity_check` ok. Journal `wal`.

| Table | Count |
|---|---|
| items | 159 |
| items source gmail | 147 |
| items source calendar | 12 |
| items source phone | 0 |
| item_attempts | 151 |
| loops | 9 |
| calendar_events | 1052 |
| cursors | 5 |
| deliveries | 0 |
| meta | 7 |
| watcher_health | 1 |
| watcher_rejects | 1 |
| phone_tombstones | 1 |

The extra Gmail item and two extra attempts since the P10-STORE smoke (items 158, gmail 146, attempts 149) are watcher activity. The one synthetic tombstone is still the only phone-related row. No phone item rows.

Installed in the Hermes venv (no installs this phase): `websockets` 15.0.1, `cryptography` 50.0.0, `pywin32` 311.

Tailscale IPv4 (`tailscale ip -4`): `100.102.206.71`. Observed only. Later code resolves this at runtime and does not hard-code it.

Port probe for the IN-G2 candidate **47821** (outside 8765 and the common dev ranges 3000/5000/8000–9000): no listener. Port **8765**: no listener. Nothing was bound. The formal port proposal is Phase 2; 47821 is the candidate this check used.

Live `plugins/zola_workspace/` file hashes (34 files, `__pycache__` excluded). `contracts/phone_test_keys.json` is still present from the Track 1 mirror. Phase 6 removes it. Hash only; contents not copied here.

| SHA-256 | Bytes | Path |
|---|---:|---|
| `0d12b8620d3413ea95674dccd2d42f6749ed1661be4231ff7eb14e1b2702ea16` | 8972 | `__init__.py` |
| `e109ebd62fffceed93202d72ebbac03743f7300de744569352ea9704564d000e` | 334 | `address_hash.py` |
| `be8a358e4af0eab58afe9e2c45ab18f11977436b40e7cc31e29f71354675cc8c` | 28648 | `auth.py` |
| `474f60bf942750e32f0645dd57bd06479061f3f70556c8bf0eb7c0645b82096c` | 9684 | `background_read.py` |
| `a8b29e55185dccfa404e0ee8cf9e06e84c7334e599af92f720a5cb8a436e9ac4` | 6351 | `contacts.py` |
| `17a0e960de59ece64ddbce58152b70cb658cc268e19142ab1799a32f3a02f5a2` | 5005 | `contracts/phone_protocol.json` |
| `365f34e744c0477702b1bfb593640cd763bd514b3c02c165780c295e51f2cf77` | 1684 | `contracts/phone_test_keys.json` |
| `3637f724c6aaf5edbd720f9aa6077ea815efa79210b2adc8b936a7c437f13c08` | 14909 | `contracts/phone_vectors.json` |
| `b217b96909296b6f17687b793dcb702debbff110b70226f2fee8df0e980a4d57` | 221 | `contracts/proactive_methods.json` |
| `cc130131a16e1162aae2087fd175b95c1106e00f9e1ccdb630a9ea089065d64f` | 1662 | `contracts/watcher_health.json` |
| `2ef13563a57dcd6f30f72d3cf4122c54df74bf104c37ebd082476065d947cc66` | 18271 | `drive.py` |
| `0e91ffc883d42de7ac143b01d2cdbfd822b1ea34b40355d32e9924c10e3b515a` | 1552 | `framing.py` |
| `b031e31eb1d9391b1b5e7873571c7f8cdb8401c4da4e6d48b14d46372c90ed1d` | 26330 | `gcal.py` |
| `b30bc3d7376e74e221697075e1b2af7309e2642fa15e02c512944b5dbcdd1d79` | 41669 | `gmail.py` |
| `fd10cbcfd304482e850fdb6cadf9f689b6cc482c28068c93b314634e6922c67f` | 15527 | `google_http.py` |
| `29113cef52d200b26fbb2938abafab5292a1bd806c4b65c9fe9ada0fac7cde06` | 32725 | `guards.py` |
| `798fddcb60c02f46e5c4cea57974726d1ecb94880f5579d0241e1c6ff6965b83` | 3673 | `log.py` |
| `267da903d4d0b7b57f62126301d5d45ce0e9d399292a009bc95e70afe5cd7f2b` | 16256 | `loops.py` |
| `bb6ae6ac2c784e36efb3809cb494a62ed69c049cfd0010bb077cefd0fdf4c0c0` | 16193 | `origin.py` |
| `b3dc4c27cb4b780a0e489644c774849e64e78296e8cf41f350ed8b101d14e316` | 2820 | `phone_ids.py` |
| `4e485461744f49222e1dd7ea378adb899b2e3c064b4dcff72f79027c96b7d738` | 199 | `plugin.yaml` |
| `e55d8e8253c5c8867c356c20a96716949dcfa22d5e5c2c9391d07219c292cda9` | 2702 | `posture.py` |
| `b57520f02ae9c6fb408977de16a466557fcae7740e5aa208df52158785912d26` | 136347 | `proactive_store.py` |
| `8296246ea2e9522eeab785af93db27cc7d103f7d6be4eaa2c47ee9a6f887178f` | 26066 | `ranker.py` |
| `b37cf4a91e7a211cfbc1865ac925658b28d26bd95a4b98908c4c6f926fb3f562` | 7051 | `read_common.py` |
| `1fc904077f8ecfbdd99f64a96dae92ea1915e82df5f9740f363799808a1e573f` | 5103 | `recorded_results.py` |
| `04a16292eadc8d4e0d24ab32bd99f8f4e69e90a201b592da4704b85c6a8f0c0a` | 28578 | `send_gate.py` |
| `1ffeaac4de12a47286acb2b2c9780d9c9b4e86b151802575acafbcc0712d3696` | 1356 | `setup.py` |
| `d4414dd9e59fb85706f4f0892f2ad8665fa2c8385401e8c3ff17f45ec457ed93` | 16454 | `speech.py` |
| `72be7fa1d88d5c0cadd70cece68823359aaeec0c311bc4518c73f7d078cecfbc` | 42499 | `surface.py` |
| `6390f091ca3a1ace957be7d18a80f1f926ec486fbf81025ac24b016d76cc344e` | 8520 | `taint.py` |
| `e5983ebc83858c69c0f53d473da63a78c15739cf4226453e24ef1c28928dbe64` | 6217 | `textclean.py` |
| `d857b225067f43d51dc96fb520f9da5e384d0c16298af8f722150ad95a882d03` | 8876 | `turn_context.py` |
| `6bfe0cd465cc120a9a2a6bd562951f8d66bff6dc4aeef94412bb56e4f0c4b29d` | 34262 | `watcher.py` |

## Phase 2 — Grounding (2026-10-19)

Read only. No source files modified. Spike findings file `P10-SPIKE-TRANSPORT_Findings.md` is not in this repo or under `C:\Users\test\Dev\zola-spikes`. The plan's Section 3 (lines 122–137) and Section 4 (lines 163–181) are the spike record used here. Appendix A and Appendix B were read in full.

### IN-G1 — Process and isolation

`python -m zola_workspace.<anything>` runs `zola_workspace/__init__.py` first. That file imports `auth`, `contacts`, `drive`, `gcal`, `gmail`, `guards`, `send_gate`, `posture`, `turn_context`, `loops`, and `surface` at module level (`__init__.py` lines 9–34). The watcher is fine with that: `watcher.py` lines 19–28 import `auth` on purpose, and `App.xaml.cs` lines 24–33 starts it as its own process.

`proactive_store.py` lines 18–24, `phone_ids.py` lines 7–11, and `address_hash.py` (stdlib only) can load as flat modules. Putting the `zola_workspace` directory on `sys.path` and importing those names does not run the package `__init__.py`.

`loops.py` cannot. Its flat fallback (lines 9–22) imports `read_common`, and `read_common.py` lines 10–23 import `auth` and `google_http`. `loops.evaluate` itself is pure (lines 232–234), but importing the module pulls the Google stack into `sys.modules`. `list_open_loop_predicates`, `note_loop_match_on_loop`, and `set_loop_matched` already live on `proactive_store` (lines 3401, 2625, 3446), so the phone process does not need the loops tool.

**(a) Sibling package.** `hermes-plugins/zola_phone/` with an empty-of-Google `__init__.py`, started as `python -m zola_phone`. `PYTHONPATH` is `<profile>\plugins` plus the Hermes root, same shape as the watcher (`WatcherProcess.cs` lines 94–110), but the entry module never imports `zola_workspace`. It inserts the `zola_workspace` directory and imports `proactive_store`, `phone_ids`, and `address_hash` flat. Runtime proof: a subprocess of that entry point asserts `auth`, `google_http`, `gmail`, `gcal`, `drive`, `contacts`, `send_gate`, `ranker`, and any Hermes agent or model name are absent from `sys.modules`. Live mirror: `plugins/zola_phone/` next to `plugins/zola_workspace/`. This option does **not** satisfy isolation if it also imports `loops.py`.

**(b) Lazy package init.** Move the Google imports in `__init__.py` lines 9–34 inside `register` (lines 126–230), and skip them when `origin.in_serve_process()` (`origin.py` lines 64–66) is false. Serve's plugin load would still import them when `register` runs, so a before/after `sys.modules` snapshot of `register()` is the identity proof. Cost: every current importer of the package, including `python -m zola_workspace.watcher`, changes when those modules appear. It still does not let `zola-phone` import `loops.py` cleanly. This changes Phase 8/9 plugin load.

**(c) Leaf matcher.** Move `evaluate` and its private node walker into a stdlib-only module, `loop_match.py`. `loops.py` re-exports `evaluate`, so callers keep the same function. `zola-phone` imports `loop_match` flat and never imports `loops.py`. This is a small `loops.py` edit. It is not a store-rule change.

**Recommendation:** (a) plus (c). (a) alone fails the `sys.modules` proof as soon as watch evaluation imports `loops`. (b) changes serve's import timing to solve a problem it does not solve.

**Mutex, shutdown, log.** Copy the watcher pattern with a different name: `Local\ZolaPhone`, exit code 2 (`watcher.py` lines 39–41 and 115–127; `SupervisionConstants.WatcherAlreadyRunningExit`). Parent PID env, exit 0 when the parent is gone (`watcher.py` lines 130–137 and 797–798). Rotating log under `HERMES_HOME\logs`, 1_000_000 bytes and 3 backups, matching `watcher.py` lines 37–38 and 764–774. The client already writes a separate output log (`ServeStderrLog`, `WatcherOutputFileName`).

### IN-G2 — Bind and port

Resolve with `tailscale ip -4` at start. Do not hard-code the address. Phase 1 observed `100.102.206.71` on interface alias `Tailscale` (`Tailscale Tunnel`, ifIndex 24, prefix 32 on that address). If the command is missing or returns no IPv4, the process stays up, status is `no_tailnet`, and it retries every `timing_ms.connect_backoff[0]` (10_000 ms, `phone_protocol.json` line 54). Each retry runs `tailscale ip -4` again. If the address changes while a socket is bound, close with disconnect reason `network-lost` and bind the new address. Never bind `0.0.0.0`, a LAN address, or port 8765.

**Port candidate: 47821.** Checked free in Phase 1 and again this phase (no listener on 47821 or 8765). It is outside 8765 and the common dev ranges 3000/5000/8000–9000. The contract file has no port field today. Phase 3 would add `listen_port: 47821` to `phone_protocol.json` as the one source.

**Firewall command for Brian** (elevated PowerShell, inbound TCP, this port, Tailscale interface only):

```powershell
New-NetFirewallRule -DisplayName "Zola phone intake" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 47821 -InterfaceAlias "Tailscale" -Profile Any
```

Cursor verifies and does not change it:

```powershell
Get-NetFirewallRule -DisplayName "Zola phone intake" | Get-NetFirewallPortFilter
Get-NetFirewallRule -DisplayName "Zola phone intake" | Get-NetFirewallInterfaceFilter
```

Expected: TCP local port 47821, interface alias `Tailscale`.

### IN-G3 — Keys and pairing

Generate an ECDSA P-256 key in the `zola-phone` process (`cryptography`, already in the venv). Store the private key DPAPI-protected the way `auth._dpapi_protect` does (`auth.py` lines 294–302): `win32crypt.CryptProtectData`, user scope, `CRYPTPROTECT_UI_FORBIDDEN`, description `zola_phone_key`. Path: `%LOCALAPPDATA%\hermes\profiles\zola\phone\pc_key.bin`. Directory ACL: current user only, same idea as `StderrAcl` (the client log path). The phone's paired public key and last accepted `seq` live beside it in `peer_state.json` (not a secret, still user-only ACL). Logs store a hash of `device_id`, never the key and never the code.

Appendix B §4 and `phone_protocol.json` lines 78–85: exchange `phone_open`, `pc_bind`, `phone_bind`, `pc_ok`, MAC'd with the 8-digit code. Code TTL `pairing_code_ttl` 300_000 ms, `pairing_wrong_attempts` 5, single use. Re-pair keeps `device_id` and replaces the key; frames from the old key are `unknown-key`. Any other key for a known `device_id` is `unknown-key` before the store is touched. The contract file does not name the MAC algorithm. Propose HMAC-SHA256 over the canonical payload, key = the 8-digit code. That needs Brian's yes because it is new contract text. `seq` is persisted in `peer_state.json` and is not reset on re-pair, so a replayed envelope still fails after a restart.

**Where Brian sees the code:** a Pair action on the COMPANION WATCHER row. The client asks `zola-phone` on the local path and shows the code in a dialog. The code is not written to a log, the progress doc, or stdout. A one-off console command is the worse option because the shell history would keep it.

### IN-G4 — Ingest and watch recovery

Per frame, first failure wins and is the only reason logged:

1. Raw frame over `size_limits.frame_bytes` (262_144) → `too-large`. No parse, no signature call.
2. Frame structure fails → `malformed`.
3. Appendix B §3, in `verification_order` (`phone_protocol.json` line 46): `unsigned`, `bad-signature`, `unknown-key`, `wrong-device`, `replay`, `stale`, `version`. Golden vectors in `phone_vectors.json` go through this verifier.
4. Field and body limits (`text_body_chars` 16_000, `notification_text_chars` 4_000) → `too-large`.
5. `ingest_phone_item` (`proactive_store.py` lines 890–1158). Tombstone check is inside that transaction (lines 1024–1031).
6. If the result is `stored`, `updated`, or `duplicate` with `watch_evaluated` still 0: `list_open_loop_predicates`, `loops.evaluate` via the leaf in IN-G1, then `note_loop_match_on_loop` and `set_loop_matched`, then `mark_watch_evaluated` only after those return ok or already (`proactive_store.py` lines 1182–1188).
7. Ack. No ack is sent before the ingest commit (`COMMIT` at lines 1030, 1091, 1104, and 1157).

Ack word: `stored`, `updated`, `duplicate`, and `suppressed` pass through. `ignored` acks `duplicate` (`phone_protocol.json` line 45). `rejected` acks `rejected` plus the store reason (`ingest_reject_reasons`, line 88).

Startup calls `list_unevaluated_phone_items` (lines 1161–1174) and runs the same evaluation. A resend that arrives as `duplicate` while the marker is still 0 is evaluated again. A second match is not created: `set_loop_matched` and `note_loop_match_on_loop` treat an existing match as already done. No live phone predicate can match yet (Track 6). Tests use a fixture loop, not a live watch.

**Gmail gap, not this track.** `watcher._ingest_message` commits in `insert_item` and only then calls `_finish_item` (`watcher.py` lines 459–485). Gmail rows have no `watch_evaluated` marker. Changing the watcher is a STOP and is out of scope.

**Fault hooks.** Production `main` takes no fault argument and does not read an environment variable. Tests pass a callable into the frame handler. Two points: after commit and before ack, and after commit and before evaluation. The client spawn never sets a fault env, and a source scan asserts production `main` has no fault switch.

`phone_protocol.json` does not yet state the raw-size-first precedence or the fresh-envelope resend rule. Phase 3 proposes adding both. Current `verification_order` starts at `malformed`, which is step 2 above, not step 1.

### IN-G5 — Keepalive, reconnect, writers

From `phone_protocol.json` lines 49–53 and Appendix B §7: PC sends `keepalive.ping` every 240_000 ms. Each pong is waited 15_000 ms. Two consecutive misses close with `pong-missed`, who=`pc`. A read timeout (15_000 ms) sends an immediate ping, and a dead socket is detected inside that one wait. One `threading.Lock` covers each full write on that connection. A `read_result` with no pending request, or one that arrives after the deadline, is logged `late-result` and dropped. Every disconnect logs a §9 reason and who detected it.

A second connection that claims the paired `device_id` is not installed as current until its first frame passes every §3 check. Failure closes the new socket and leaves the working one. Success closes the old one with `superseded`.

`peer_state.json` holds the last accepted `seq` and the skew check's last `sent_at_ms`. After a `zola-phone` restart, a fresh envelope (higher `seq`, current `sent_at_ms`, same item identity) is accepted and the store returns `duplicate`. An old envelope (`seq` less than or equal to the stored value) is refused `replay` before `ingest_phone_item`.

### IN-G6 — Local read path

Serve reaches the phone only through `zola-phone`. The client never opens a phone socket.

**(a) Named pipe.** `\\.\pipe\ZolaPhone` with a user-only security descriptor (`pywin32`, already installed). Another Windows user gets access denied and sees no frame. A process running as Brian can open the pipe. Latency is the local hop the plan calls ~1 ms (`P10-D12`). If `zola-phone` is down, the open fails at once and the caller returns `phone_unavailable` / `no_connection`. No extra port, so G-BIND stays the Tailscale listener only.

**(b) Loopback TCP plus a per-launch token.** The client mints a token the way `HermesProcessManager.SpawnAsync` mints `HERMES_DASHBOARD_SESSION_TOKEN` (`HermesProcessManager.cs` lines 220–243) and passes it to serve and to `zola-phone`. Any local user can open the port; without the token the request is refused. A same-user process that can read a child environment can read the token. Serve's launch would gain one environment variable. This adds a second listening port on loopback.

Requests, Appendix B §6: `status`, `read_history`, `read_notifications`, `read_code`, `diagnostic_read`. Response `ok` or `phone_unavailable` with `no_connection`, `timeout`, `rejected`, or `not_paired`. Serve blocks for `read_timeout` plus a 1_000 ms margin. No store polling. `read_code` values are not logged (R1). Pairing display needs one more local request, `pairing.start`, which never goes on the phone socket. That is new contract text.

**Recommendation:** (a). Track 5's history, notification, and code tools (`PHASE10_BUILD_PLAN.md` lines 686–700) call this same client module.

### IN-G7 — Client supervision

The watcher is not a child of serve. `App.OnLaunched` constructs `WatcherProcess` and starts it beside serve (`App.xaml.cs` lines 23–34). `ProcessSupervisor` is serve-only: it holds the chat socket and health probes (`ProcessSupervisor.cs` lines 6–27). Folding `zola-phone` into that class would tie the phone link to serve restarts. The plan's "ProcessSupervisor" row means the restart policy, which `WatcherProcess` already uses separately.

`WatcherProcess.Start` resolves the Hermes Python, spawns `python -m zola_workspace.watcher`, sets `HERMES_HOME`, `PYTHONPATH`, and `ZOLA_WATCHER_PARENT_PID`, assigns `WatcherJob` kill-on-close, and on exit asks `WatcherSupervisor` (`WatcherProcess.cs` lines 53–195). Three exits in 10 minutes spawn again; the fourth is terminal (`RestartPolicy.cs` lines 85–108, limits in `SupervisionConstants.cs` lines 6–8). Exit code 2 logs `already_running` and does not count (`WatcherSupervisor.cs` lines 22–29).

**(a) Generalize `WatcherProcess`.** One class parameterized by module, mutex env, log name, and proc label. The duplicated spawn and exit body (about `WatcherProcess.cs` lines 81–224) exists once. The watcher launch path changes. Every current supervision check must be re-run unchanged. The checks compile `WatcherSupervisor` and `RestartPolicy`, not `WatcherProcess`, so the risk is the live spawn, not the check rows.

**(b) A second class.** `PhoneProcess` reuses `RestartPolicy`, `WatcherJob`, `ServeStderrLog`, `ServeGenerations`, and `WatcherSupervisor` without editing them. It keeps its own copy of the spawn and exit methods (the lines (a) would share). `WatcherProcess.cs` stays as it is, so the watcher checks and the watcher launch stay on the current code.

**Recommendation:** (b). Own `RestartPolicy` instance, own job, own output log `zola_phone.out.log`, proc label `phone`. Started from `App.OnLaunched` next to the watcher, stopped on window close. A serve restart does not call `PhoneProcess.StopDeliberate`.

### IN-G8 — Health and the COMPANION WATCHER row

`watcher_health` is one row: `CHECK (id = 1)` (`proactive_store.py` lines 364–365). It cannot store phone health.

**(a) New `phone_health` table.** Schema 7, own version constant, backup-API proof, version re-check inside the migration transaction. The row stays accurate while serve restarts, because `zola-phone` writes it. The client still cannot read `proactive.db` (one store owner). Today's panel reads watcher health through serve (`speech.install_methods`, `proactive.watcher_health`, `speech.py` lines 427–446, and `contracts/proactive_methods.json`). While serve is restarting that gateway is down, so the panel would not show the live phone link unless the client also had another path.

**(b) Status over the local path.** `zola-phone` keeps connection state, last frame, last pong, paired device hash, last disconnect reason, and counts in memory and in its log. `status` returns that snapshot. The client's process latch supplies Restarting and Keeps failing, the same split `WatcherHud` already uses for the workspace watcher (`WatcherHud.cs` lines 32–45): spoken or link state from the process, process words from the latch. While serve is restarting, the panel still asks the pipe, so Connected stays Connected. Track 5's "Is my phone connected?" (`PHASE10_BUILD_PLAN.md` lines 695–696) calls the same `status` from serve. No gateway method and no schema change.

**States, phone link and process kept apart.** Colours already exist: Quiet is the dim dot, Attention is `#FFE7A5` (`ZolaTokens.xaml` line 11), Down is `#D9534F` (line 14). `SystemsCopy.Companion` is already `"COMPANION WATCHER"` (line 12). `Row` has no Companion entry (lines 31–38), and `Rows` returns five rows (lines 73–82). `MainWindow.PaintSystems` paints those five (`MainWindow.xaml.cs` lines 870–887). `MainWindow.xaml` has no Companion grid.

| State | Means | Level |
|---|---|---|
| Not paired | Process up, no paired device | Attention (gold) |
| Connected | Paired, socket up, last pong inside 240_000 ms | Quiet (dim) |
| Reconnecting | Paired, socket down for less than 480_000 ms (two ping intervals) | Attention |
| Offline | Paired, socket down longer than that grace, or the phone unreachable | Down (red) |
| Restarting | Latch says the supervisor is restarting the process | Attention |
| Keeps failing | Latch says the supervisor stopped trying | Down |
| Unknown | Process up, no status yet | Hidden |

Offline is only the phone link. Restarting and Keeps failing are only the process. Latch Restarting or Keeps failing wins over the link state, because there is no process to ask. Unknown is hidden, matching the workspace watcher before the first health row (`SystemsCopy.cs` lines 96–98).

**Recommendation:** (b). The client reads `status` on the pipe. Serve reads the same pipe for Track 5. The plan's "gateway method" sentence is the alternative (a) needs; (b) does not add one.

### IN-G9 — Fake phone

Location: `hermes-plugins/zola_phone/tools/fake_phone.py`. `unittest discover` will not collect it. It pairs, holds the connection, answers pings, sends text and notification events (late revision, duplicate, out-of-order ids, `exhausted`, oversize, U+001F in an identity field), answers reads on time, late, or never, and misbehaves (unsigned, bad signature, unknown key, wrong device, replay, stale, version, malformed, half-open). Keys come from `phone_test_keys.json` or from keys it generates under the scratch profile. It never reads the live `pc_key.bin`.

### IN-G10 — Test profile isolation

F1–F5 use `HERMES_HOME=C:\Users\test\Dev\zola-spikes\p10-intake\home` and a scratch `proactive.db` created by `proactive_store.connect` there. Bind is the live Tailscale address on port 47821. The Zola client is not running, so it is not also launching `zola-phone`. Scratch `zola-phone` is stopped by PID before Part B, and the port is confirmed free. F6–F7 use the live profile and create no phone rows. No synthetic phone row is written to the live database in F1–F5.

### Decisions Phase 3 must take to Brian

1. IN-G1: (a) plus the `loop_match.py` leaf, versus (b) lazy package init.
2. IN-G6: named pipe, versus loopback plus a token.
3. IN-G7: a second `PhoneProcess` class, versus generalizing `WatcherProcess`.
4. IN-G8: live `status` on the pipe and no schema 7, versus a `phone_health` table. No new gateway method under the recommendation.
5. Port 47821 and the firewall command. Brian runs the command and confirms Tailscale 2FA in his own words.
6. Contract additions: `listen_port`, raw-size-first precedence, fresh-envelope resend rule, HMAC-SHA256 for the pairing code, local `pairing.start`.
7. Pairing code shown from a Systems panel action, never logged.

## Phase 3 — Proposal (STOP, 2026-10-20)

No source files modified. Positions below are Claude's review of Phase 2. Brian decides. Tailscale two-factor authentication and the firewall command are not confirmed yet; both are recorded only after Brian says them.

Spike findings stay outside this track. The file is a project document, not in the repo. Plan Sections 3–4 are enough here. Brian will put a copy beside the prompts before Track 3.

### 1. IN-G1 — sibling package plus a moved matcher

`hermes-plugins/zola_phone/` is the process. Entry is `python -m zola_phone` on the Hermes venv. It never imports `zola_workspace` or `loops.py`. It puts the `zola_workspace` directory on its path and imports `proactive_store`, `phone_ids`, `address_hash`, and `loop_match` as flat modules.

`loop_match.py` is a move. `_instant`, `_occurred_at`, `_node_matches`, and `evaluate` (`loops.py` lines 169–235) leave `loops.py` and exist only in `loop_match.py`. `loops.py` binds `evaluate = loop_match.evaluate`, so the watcher (`watcher.py` line 181), the `zola_loops` tool, and `zola-phone` call one function object. A wrapper would fail the identity test. `loop_match.py` imports only the standard library (`datetime`, typing). Track 6 adds phone predicates in that file.

Proof: every existing loop and watcher test stays untouched and passes; one new test asserts `loops.evaluate is loop_match.evaluate`; a source scan asserts `loop_match.py` imports nothing outside the standard library.

Mutex `Local\ZolaPhone`, exit 2 when it is already held, parent-PID shutdown, rotating log `zola_phone.log` (1_000_000 bytes, 3 backups) under `HERMES_HOME\logs`.

### 2. IN-G6 — local path

**Option A, recommended.** Named pipe `\\.\pipe\ZolaPhone`, created with `FILE_FLAG_FIRST_PIPE_INSTANCE` and `PIPE_REJECT_REMOTE_CLIENTS`, DACL for the current user only.

- Another Windows user cannot open the pipe.
- A remote client is rejected by the pipe flag.
- If the name is already owned, `zola-phone` logs `pipe_held` and exits 2. The supervisor treats exit 2 as already-running and does not restart-storm. The single-instance mutex remains `Local\ZolaPhone`.
- `zola-phone` down: the open fails at once, response `phone_unavailable` / `no_connection`.
- No second listening port. The Tailscale socket stays the only phone listener.

**Per-launch secret, for Brian to keep or drop.** The client mints 32 random bytes at launch, the same pattern as `HERMES_DASHBOARD_SESSION_TOKEN` (`HermesProcessManager.cs` lines 220–243), and passes `ZOLA_PHONE_LAUNCH_SECRET` only to serve and `zola-phone`. It is required on `read_code` and `pairing.start`. It is not required on `status`.

What it protects: a same-user program that can open the pipe but cannot read the client, serve, or `zola-phone` environment cannot retrieve a code or start pairing.

What it does not protect: a same-user program that can read another process's environment, or that process's memory, can copy the secret and call `read_code` and `pairing.start`. The pipe ACL does not separate Brian's programs from each other.

`read_history`, `read_notifications`, and `diagnostic_read` are not covered by the secret under this recommendation. History and notification results carry message content. Widening the secret to those three is a one-line change if Brian wants it.

**Option B.** Loopback TCP on a second port, with the same per-launch secret required on every request. Any local user can open the port; the secret is the only check. Serve's launch gains the environment variable. This adds a listening port beside the Tailscale one.

Recommendation is Option A plus the secret on `read_code` and `pairing.start` only. Dropping the secret leaves those two requests protected only by the user ACL.

### 3. IN-G7 — supervision

Both processes start from `App.OnLaunched`, beside each other, and a serve restart does not stop `zola-phone`. Shared pieces either way: `RestartPolicy` (3 per 10 minutes, then keeps failing), `WatcherJob` kill-on-close, `ServeStderrLog`, `ServeGenerations`, exit code 2 logged `already_running` and not counted, deliberate stop not counted. Own output log `zola_phone.out.log`. Own proc label `phone`.

**Option A, Claude's lean.** Generalize `WatcherProcess` into one supervised-Python start path. A pure function builds the start record: file, arguments, working directory, and the environment this track sets. Watcher inputs produce today's command exactly:

- file: the Hermes `python.exe`
- arguments: `-m` `zola_workspace.watcher`
- working directory: Hermes root
- `HERMES_HOME` = profile, `PYTHONUNBUFFERED` = `1`
- `ZOLA_WATCHER_PARENT_PID` = the client pid
- `PYTHONPATH` = `<profile>\plugins` + separator + Hermes root
- no launch-secret variable

Phone inputs differ in the module (`zola_phone`), the parent variable (`ZOLA_PHONE_PARENT_PID`), and the launch secret when that secret is kept. Restart, exit-code-2, and deliberate-stop checks run the same assertions for both process labels. Existing supervision checks stay 38/38. New checks are a new coverage row, so the 38 is not edited.

**Option B, Phase 2's lean.** A second class copies the spawn, exit, and restart handling (about `WatcherProcess.cs` lines 81–224) and reuses the policy, job, log, and generations. `WatcherProcess.cs` stays byte-identical. The watcher cannot drift from this edit. Every later fix to spawn or exit has to be made in both classes.

Phase 9's supervision bugs were in this kind of spawn and exit code. Option A has one copy and a field-by-field proof. Option B has two copies and no watcher diff.

### 4. IN-G8 — health and the row

Live `status` on the pipe. No `phone_health` table, no schema 7, no gateway method, no `proactive_methods.json` change. The client reads the pipe itself, so the row stays true while serve restarts. Serve's later "Is my phone connected?" uses the same `status`. The process latch supplies Restarting and Keeps failing. Those two win over the link state.

Connected means the last pong arrived within one ping interval plus the pong wait: `timing_ms.ping_interval` + `timing_ms.pong_wait` = 240_000 + 15_000 = 255_000 ms. The code names that sum. It is not a third copy of the number. A window of only 240_000 ms would leave a healthy link out of Connected just before each ping.

Reconnecting stays the phone link down for less than `reconnecting_grace_ms` 480_000 (two ping intervals), written in the contract. Offline is the phone link after that grace, or the phone unreachable. Offline is never the process.

| State | Means | Level |
|---|---|---|
| Not paired | Process up, no paired device | Attention `#FFE7A5` |
| Connected | Paired, socket up, last pong within 255_000 ms | Quiet, dim dot |
| Reconnecting | Paired, socket down for less than 480_000 ms | Attention |
| Offline | Paired, socket down longer than that, or the phone unreachable | Down `#D9534F` |
| Restarting | Supervisor is restarting the process | Attention |
| Keeps failing | Supervisor stopped trying | Down |
| Unknown | Process up, no status yet | Hidden |

`SystemsCopy.Row` gains `Companion`. `Rows` returns it. `MainWindow.xaml` gains one grid, painted like the other five. Label stays `COMPANION WATCHER`.

### 5. Port and firewall

`listen_port` 47821 in `phone_protocol.json`. Bind only the address from `tailscale ip -4`. Never `0.0.0.0`, never a LAN address, never 8765. No address: process stays up, status `no_tailnet`, retry every 10_000 ms, re-resolve each time. Address change while bound: close `network-lost`, bind the new address.

Brian runs this elevated:

```powershell
New-NetFirewallRule -DisplayName "Zola phone intake" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 47821 -InterfaceAlias "Tailscale" -Profile Any
```

Cursor only reads:

```powershell
Get-NetFirewallRule -DisplayName "Zola phone intake" | Get-NetFirewallPortFilter
Get-NetFirewallRule -DisplayName "Zola phone intake" | Get-NetFirewallInterfaceFilter
```

Expected: TCP, local port 47821, interface alias `Tailscale`.

### 6. Contract, keys, ingest, keepalive

`phone_protocol.json` `contract_version` becomes 2. Signed payloads in `phone_vectors.json` move to 2 and are re-signed with the test key in the same change. The PC accepts version 2 only. Nothing in the field speaks version 1. `test_p10_store.py` currently treats each `verification_order` entry as both the case name and the expect string (lines 565–570). That assertion is updated in the same change: the step name and the logged reason are allowed to differ.

Additions:

- `listen_port`: 47821
- `reconnecting_grace_ms`: 480000
- `verification_order` gains `raw-size` first, then the current §3 steps, then `field-limits`
- step reasons: `raw-size` and `field-limits` both log `too-large`; every other step logs its own name
- `resend`: a resent item is a new signed envelope, new higher `seq`, current `sent_at_ms`, same item identity and `revision`; replay and stale are refused before the store; a fresh envelope for a stored item is acked `duplicate`
- pairing MAC: HMAC-SHA256 over the canonical payload, key is the one-time 8-digit code
- local requests: `status` (no secret), `read_history`, `read_notifications`, `diagnostic_read`, `read_code` (secret), `pairing.start` (secret)

PC key: ECDSA P-256, DPAPI via `win32crypt.CryptProtectData`, user scope, description `zola_phone_key`, path `%LOCALAPPDATA%\hermes\profiles\zola\phone\pc_key.bin`, directory DACL for the current user only. Paired public key and last accepted `seq` in `phone\peer_state.json` beside it. `seq` is not reset on re-pair. Logs carry a hash of `device_id` only.

Pairing: `phone_open`, `pc_bind`, `phone_bind`, `pc_ok`. Code TTL 300_000 ms, 5 wrong attempts invalidate, single use. Re-pair keeps `device_id`. Any other key for that device is `unknown-key`. A Pair action on the COMPANION WATCHER row asks `pairing.start` and shows the code in a dialog. The code is not logged, printed, written to this doc, or saved in a screenshot in the repo.

Ingest, first failure only: raw size → structure (`malformed`) → §3 → field limits (`too-large`) → `ingest_phone_item` → watch evaluation → `mark_watch_evaluated` → ack. Ack words: store `stored`, `updated`, `duplicate`, `suppressed` pass through; `ignored` acks `duplicate`; `rejected` acks `rejected` plus the store reason. No ack before commit. Startup runs `list_unevaluated_phone_items`. A `duplicate` whose marker is still 0 is evaluated again. Tests use a fixture loop. The Gmail commit-then-evaluate gap in the watcher is unchanged.

Fault points exist only as a callable the tests pass in. Production `main` has no fault switch and reads no fault environment variable.

Keepalive: ping every 240_000 ms; pong wait 15_000 ms; two misses close `pong-missed` who=`pc`; a read timeout sends one immediate ping. One lock covers each full write. Late read results log `late-result` and are dropped. A new connection replaces the current one only after its first frame passes every §3 check. `peer_state.json` is what makes a fresh resend work after a restart and an old envelope fail `replay`.

Fake phone: `hermes-plugins/zola_phone/tools/fake_phone.py`. Scratch keys or `phone_test_keys.json` only. F1–F5 use `HERMES_HOME=C:\Users\test\Dev\zola-spikes\p10-intake\home` and port 47821, with no live client running. F6–F7 touch the live profile and create no phone rows.

No gateway method. No store schema change. No `config.yaml` change. No installs.

### Tests and checks

Plugin suites stay at or above 357 / 134 / 44 / 8. Client build stays clean. Existing check rows stay at their Phase 1 counts (supervision 38/38, speech 38/38, and the other eleven rows). New client checks are new coverage rows.

- `loops.evaluate is loop_match.evaluate`. Existing loop and watcher tests unchanged.
- `loop_match.py` imports only the standard library.
- Every golden vector accepts or fails with its reason, in precedence order, through `zola-phone`'s verifier. Version-2 payloads re-signed.
- G-RESEND: fresh envelope after a lost ack → `duplicate`, one row; same after a `zola-phone` restart → `duplicate`; old envelope after the restart → `replay`, store untouched.
- G-SUPERSEDE-AFTER-AUTH: a second connection with a bad signature, unknown key, replayed `seq`, or stale time is refused and the first connection keeps delivering; a second connection that passes every check supersedes it.
- G-SIZE-FIRST: oversized frame refused before any parse or signature call; oversized and unsigned logs only `too-large`; unsigned and over-limit body logs only `unsigned`.
- Pairing: wrong code ×5 invalidates; expired refused; success; re-pair keeps `device_id` and the old key is `unknown-key`; unauthorized key for a known device is `unknown-key`; replayed `seq` refused after a restart. HMAC-SHA256 cases in the vectors.
- Ingest: each store result maps to the ack word above; fault between commit and ack → resend → `duplicate`, one row; field limits → `too-large`.
- Watch recovery at both fault points through `zola-phone`'s startup and duplicate paths, fixture loop only.
- Keepalive: two missed pongs close; half-open socket detected inside one ping wait after a read timeout; late result → `late-result`.
- Pipe: requests answer; process down → `phone_unavailable` at once; no socket → `no_connection`; timeout → `timeout`; `read_code` value absent from every log (sentinel grep). If the secret is kept: `read_code` and `pairing.start` without it are refused; `status` without it still answers. A second creator of the pipe fails and logs `pipe_held`.
- G-ISOLATION: the real entry point's `sys.modules` lacks `auth`, `google_http`, `gmail`, `gcal`, `drive`, `contacts`, `send_gate`, `ranker`, and Hermes agent or model modules. Source scan: `phone_test_keys.json` is not opened outside tests.
- G-BIND: listening address is the Tailscale IPv4 and port 47821.
- Client, if Option A: watcher start record matches the frozen field list; phone start record differs only where this proposal says; restart, exit 2, and deliberate stop match for both labels. If Option B: those checks cover `PhoneProcess` only, and `WatcherProcess.cs` has an empty diff.
- COMPANION WATCHER row for each state in the table above, including Connected at 255_000 ms and not at 240_000 ms alone.
- Serve restart leaves the phone process running. Four phone exits in 10 minutes → keeps failing.

### Risks

- Re-signing every version-2 vector can disagree with Appendix B if a payload field moves. The same commit updates the contract, the vectors, and `test_p10_store.py`.
- Option A touches the watcher spawn. The frozen start record is the proof that the command did not change. Option B leaves a second copy of the code Phase 9 already got wrong once.
- The launch secret does not stop a same-user program that can read an environment block. History and notification reads are outside the secret unless Brian widens it.
- `FILE_FLAG_FIRST_PIPE_INSTANCE` and the mutex can disagree if a stranger owns the pipe name. Exit 2 plus the `pipe_held` log is the visible signal.
- Connected is a computed sum. A later edit of `ping_interval` or `pong_wait` moves the window without a second constant to forget.
- Status disappears when the process is dead. The latch is what shows Restarting and Keeps failing in that gap.
- Track 3's companion must use this HMAC and version 2. The findings file is still not in the repo; Brian places it before Track 3.

### Decisions for Brian

1. Approve this proposal, or name the items that change.
2. Keep the per-launch secret on `read_code` and `pairing.start`, or drop it. Say if history, notifications, and diagnostic reads should require it too.
3. IN-G7: Option A (generalize `WatcherProcess`, with the start-record proof) or Option B (a second class).
4. Confirm Tailscale two-factor authentication on the sign-in account, in your own words.
5. Run the elevated firewall command above, then say that you ran it, in your own words.

### Verdicts

Spoken 2026-10-20, recorded verbatim:

- "Supervision: Option A."
- "Keep the secret. The client mints it at launch, keeps it, and passes it only to serve and zola-phone. Require it for read_history, read_notifications, read_code, diagnostic_read and pairing.start. Status doesn’t need it."
- "Health: track the connection and its responsiveness separately. Connected = socket open and the last ping answered. Not responding = socket open but a ping missed. Reconnecting = socket closed, counted from the moment it closed, for up to 480 seconds. Offline = closed longer than that. Restarting and Keeps failing come from the process latch."
- "Contract v2 updates the golden vectors and rejects unsupported versions explicitly."
- "Two-factor is on for my Tailscale account."
- "I ran the firewall command."
- "proceed to phase 4"

The Connected window of 255000 ms in the proposal is replaced by the health verdict above.

Firewall read-back, not modified by this track: DisplayName "Zola phone intake", Inbound, Allow, Enabled, Profile Any, TCP local port 47821, InterfaceAlias Tailscale.

## Phase 4 — Implement (STOP, 2026-10-20)

Option A. `PythonStart.Build` is the one start plan. `SupervisedPython` is the one spawn, job, and restart path. `WatcherProcess` is a thin watcher label. `PhoneProcess` is the phone label. The watcher plan has no `ZOLA_PHONE_LAUNCH_SECRET`. The phone plan sets `ZOLA_PHONE_PARENT_PID` and the secret. Serve's spawn sets the same secret and does not start or stop zola-phone.

The client mints one secret per launch and keeps it. The pipe requires it for `read_history`, `read_notifications`, `read_code`, `diagnostic_read`, and `pairing.start`. `status` does not. A missing or wrong secret is `unauthorized` and the value is not logged.

Health is two facts. Connected: socket open and the last ping answered. Not responding: socket open and a ping missed. Reconnecting: socket closed for under 480000 ms, counted from the close. Offline: closed longer than that. No tailnet stays up as `no_tailnet` and retries. Restarting and Keeps failing come from the process latch and win over the link. Unknown stays hidden. Not responding and no tailnet use the existing attention color. Offline and keeps failing use the down color.

Contract version 2. `supported_versions` is `[2]`. An unsupported version is `version`. Golden vectors were re-signed. Raw size is checked before parse or verify.

Pairing is `phone_open`, `pc_bind`, `phone_bind`, `pc_ok`, HMAC-SHA256 with the code over the canonical payload. The code is shown only in the pair dialog.

### Checks

| Suite | Result |
|---|---|
| `zola_workspace` | 357 OK |
| `zola_memory` | 134 OK |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |
| `zola_phone` | 12 OK |
| `Zola.Client` build | succeeded, 0 warnings, 0 errors |
| client checks | lifecycle 22/22, admission 13/13, start 9/9, invalid 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 38/38, phone 3/3 |

No commit.

## Phase 5 fixes F1–F11 from Claude's review

Phase 5 fixes F1–F11 from Claude's review. Nothing outside those fixes changed.

Failing first, then the fix:

| Fix | Red | Green |
|---|---|---|
| F1 | `AttributeError: 'Engine' object has no attribute 'keepalive_step'` | `test_f1_two_missed_pongs_close`, `test_f1_one_miss_is_not_responding_and_a_pong_restores`, `test_f1_read_timeout_pings_once_and_a_dead_socket_closes_inside_one_wait` |
| F6 | `KeyError: 'reason'` — a missing revision was stored and acked without a reason | `test_f6_missing_revision_stores_nothing`, `test_f6_missing_fields_attachments_and_notification_ack` |
| F7 | `AssertionError: True is not false` — `allowed_bind` accepted a LAN address because it compared the host with itself | `test_f7_lan_address_is_not_a_tailnet`, `test_f7_only_cgnat_binds_and_a_change_rebinds` |

F2, F3, F4, F5, F8, F9, F10, and F11 were written as tests against the new contract and passed on the first full run after the implementation. The F2 assertion used `list.append`, which is a new bound method on every access; it was restated on a named function and then passed.

F1 pings every 240000 ms, waits 15000 ms, closes on the second miss with `pong-missed` / `pc`, and sends one immediate ping after a read timeout. F2 binds the sender only after the connection is current and sends every frame through one writer. F3 holds one lock around peer state, sequence numbers, and the pending maps, never across the wait. F4 serves each pipe client on its own thread, keeps the first instance open, and reads until the newline. F5 takes `ZOLA_PHONE_LAUNCH_SECRET` once at register and at zola-phone startup and removes it from the environment. F6 rejects a missing or ill-typed required field, stores attachment fields, and acks a notification with its identity. F7 binds only an address inside 100.64.0.0/10 and rebinds when it changes. F8 is the fake phone. F10 starts the real module and reads the startup line. F11 is the extra client rows.

### Phase 4 requirement → test

| Requirement | Test |
|---|---|
| Golden vectors through the real verifier, in §3 order | `test_f9_vectors_results_and_local_reasons` |
| Pairing wrong code ×5 → invalidated; expired code refused | `test_f9_five_wrong_codes_invalidate_and_an_expired_code_is_refused` |
| Each store result → its ack word | `test_f9_ack_words_and_source_scan` |
| `late-result` | `test_f9_vectors_results_and_local_reasons` |
| `no_connection`, `timeout`, `not_paired`, `unauthorized` | `test_f9_vectors_results_and_local_reasons` |
| G-SIZE-FIRST, three cases | `test_identity_and_size_before_verify` |
| Nothing outside tests opens `phone_test_keys.json` | `test_f9_ack_words_and_source_scan` |
| `loops.evaluate is loop_match.evaluate` | `test_identity_and_size_before_verify` (also `test_p10_store` ContractTests) |
| `read_code` sentinel absent from every log | `test_f9_vectors_results_and_local_reasons`, `test_secret_and_read_code_not_logged` |
| Two missed pongs close | `test_f1_two_missed_pongs_close` |
| One miss is Not responding; a pong restores; a read timeout pings | `test_f1_pong_restores_and_read_timeout_pings` |
| A stranger connection receives nothing | `test_f2_stranger_receives_nothing` |
| Concurrent sends do not interleave | `test_f2_frames_do_not_interleave` |
| 50 concurrent relays get 50 distinct seqs | `test_f3_concurrent_relays_use_distinct_seqs` |
| `status` answers while a read is waiting | `test_f4_status_answers_while_a_read_waits` |
| A 64000-character history line arrives intact | `test_f4_long_history_line_arrives_whole` |
| A second process refuses the pipe and the mutex | `test_f4_second_process_refuses_the_pipe_and_mutex` |
| Secret gone from the environment and a later subprocess | `test_f5_secret_is_removed_before_tools` |
| Watcher plan has no secret; phone plan has it | client checks `watcher start plan has no launch secret`, `phone start plan carries the secret and a different module` |
| Missing field → its reason; attachments stored; notification ack identity | `test_f6_missing_revision_stores_nothing`, `test_f6_fields_and_notification_ack` |
| LAN refused; a change rebinds | `test_f7_lan_address_is_not_a_tailnet`, `test_f7_address_change_rebinds` |
| Fake phone commands | `test_f9_ack_words_and_source_scan` (`fake_phone --help`) |
| Isolation on the real startup path | `test_isolation_on_the_real_startup_path` |
| Watcher start plan field by field | client check `watcher environment matches the frozen start record` |
| Phone restart, keeps failing, deliberate stop | client checks `phone restarts three times and the fourth keeps failing`, `a deliberate phone stop does not count as a failure` |
| Serve restart leaves zola-phone running | client check `a serve restart does not stop zola-phone` |
| Companion row, each link, latch wins | client checks `companion latch wins and unknown stays hidden`, `companion row covers each link and the latch wins` |
| No overlapping status polls | client check `a phone poll skips while one is still running` |
| C# reader keeps a 64000-character line | client check `the pipe reader keeps a 64000 character line` |

### Checks

| Suite | Result |
|---|---|
| `zola_workspace` | 357 OK |
| `zola_memory` | 134 OK |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |
| `zola_phone` | 28 OK |
| `Zola.Client` build | succeeded, 0 warnings, 0 errors |
| `Zola.Client.Checks` build | succeeded, 0 warnings, 0 errors |
| client checks | lifecycle 22/22, admission 13/13, start 9/9, invalid 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 38/38, phone 10/10 |

Live profile untouched. No commit.

## Phase 6 — F12 before deploy

F12, failing first. An idle paired connection, injected clock, pong on every ping, 20 simulated minutes:

Red, before the change: the first pings were at +15000, +30000, +45000, +60000, +75000 ms. `keepalive_step` treated 15000 ms since `last_frame_ms` as an immediate ping, and a pong cleared `immediate_ping_sent`, so a quiet link pinged about every 15 seconds.

Green, after the change: pings at +240000, +480000, +720000, +960000, +1200000 ms. Exactly five. `_relay`'s timeout path sets `read_timeout_ping`, and `keepalive_step` consumes it once. One timed-out read adds one ping; 15000 ms with no pong is `miss` and Not responding with the socket still open; the next missed pong closes with `pong-missed`. `last_frame_ms` is not part of that decision.

`test_f12_idle_link_pings_every_four_minutes`. Phone suite 29 OK. Workspace 357, memory 134, tools 44, tts 8. Client build 0 warnings. Checks unchanged: supervision 38/38, speech 38/38, phone 10/10, and the earlier rows at their Phase 1 counts.

### Part A — scratch profile

`HERMES_HOME` `C:\Users\test\Dev\zola-spikes\p10-intake\home`. Bind `100.102.206.71:47821`. The scratch `zola-phone` was stopped by PID. Nothing is listening on 47821. Live profile untouched.

| Cell | Result |
|---|---|
| F1 wrong code ×5 | invalidated, 5 attempts, no reply |
| F1 correct pair | `pc_bind/pc_ok` |
| F1 re-pair | same device, old key `unknown-key`, resend `duplicate` |
| F1 tombstone | `suppressed` |
| F1 new install | `pc_bind/pc_ok`, 0 resend requests |
| F2 §3 rejections | stored delta 0. unsigned, malformed, bad-signature, wrong-device, stale, version, separator→malformed, raw oversize→too-large, unsigned-and-oversize→too-large, replay |
| F2 supersede | a bad second connection left the first delivering (`stored`) |
| F3 batch | 20 texts stored, 5 notifications stored |
| F3 kill before ack | demonstrated by the scratch fault launcher: pid 20108 exited 1 at `before_ack`, one row; the fresh-envelope resend was `duplicate`, still one row |
| F3 late revision | `updated` |
| F3 G-RESEND | fresh envelope `duplicate`, old envelope `replay` |
| F3 watch crash | demonstrated by the scratch fault launcher: pid 20060 exited 1 at `before_eval`, one row, `watch_evaluated=0`; startup recovery set `watch_evaluated=1` and matched the fixture loop once; the resend was `duplicate` and the match stamp did not move |
| F3b size | oversized frame `too-large`, nothing extra stored; truncated body stored with `truncated=1` |
| F4 half-open | read timed out in 16.015 s; Not responding 15.143 s after that return |
| F4 two misses | closed at 495.398 s, link `reconnecting`, `pong-missed` |
| F1 expired code | `pairing-expired` |
| F5 reads | on time 14 ms; late answer timed out at 16009 ms and logged `late-result`; no socket `no_connection` in 3 ms |
| Log scan | scripted body 0, launch secret 0, PEM 0, pairing code 0. Scratch rows 38 |

Device hashes: `d56eae20263c4aff7eeef985eaa699e7fa375ae2ca03d8f7305a72dfbcc92ea0`, `54e1e0b41429a4a37b3b1744dd40a2d1151de09e4bcfc4f94a0e2fdab6533937`. Public-key hashes: `54c5481c6b125c65ba709bfff1294d66015ce7d8e8fc7842d51ba87d635ea7b8`, `76f6aed3ef05a963580fffc7c1c9de2f0107af6a748a49457f8c35c8f6a964ba`, `880dd67da047db4bfdecc06c6002be155ac65368c3866978ade276c1b4992b75`.

The two crash cells used a scratch-only launcher, `C:\Users\test\Dev\zola-spikes\p10-intake\fault_serve.py`, which is not in the repo and is deleted at closeout. It runs the real serving path with `Engine(fault=...)`. The fault calls `os._exit(1)` at the named point. Production `zola_phone/__main__.py` constructs `Engine` with no fault argument. Its only `os._exit` is `_watch_parent` exiting 0 when the parent is gone. A harness check that treated any `os._exit` as a fault switch is wrong; the product has no fault switch.

| Fault cell | Result |
|---|---|
| before_ack died | pid 20108, exit 1, rows 1. Device hash `cd4e9ea8a1408c31c250c3a43c28632080e9e8a3f00e665d819cb8e41f6573e4`. Public-key hash `8cd5a8bcfb4dc34dd65f2724b9122b92669ac001e3ffc4434c6bd3576a4d2afc` |
| before_ack resend | `duplicate`, rows 1, normal pid 27716 then stopped |
| before_eval died | pid 20060, exit 1, rows 1, `watch_evaluated=0`, loop stamp unset |
| before_eval recovery | `duplicate`, rows 1, `watch_evaluated=1`, `loop_matched=1`, stamp unchanged, normal pid 20332 then stopped |
| port | 47821 free after both runs. No `zola_phone` or `fault_serve` process left |

### Part B — live profile

Brian had closed the client. Before launch: no `Zola.Client.exe`, no `dotnet`, no Hermes serve, watcher, or zola-phone.

Backup folder `C:\Users\test\Dev\zola-spikes\p10-intake\backups\phase6`. `proactive.db` copied with SQLite `Connection.backup` from a read-only source. Backup SHA-256 `4ad041698d92cff5302afce3864acf1bbd33cfb756d94f5970b16f250c214d91`, 954368 bytes. Pre-overwrite plugin hashes: `zola_workspace/__init__.py` `0d12b8620d3413ea95674dccd2d42f6749ed1661be4231ff7eb14e1b2702ea16`, `loops.py` `267da903d4d0b7b57f62126301d5d45ce0e9d399292a009bc95e70afe5cd7f2b`, `phone_protocol.json` `17a0e960de59ece64ddbce58152b70cb658cc268e19142ab1799a32f3a02f5a2`, `phone_vectors.json` `3637f724c6aaf5edbd720f9aa6077ea815efa79210b2adc8b936a7c437f13c08`, `phone_test_keys.json` `365f34e744c0477702b1bfb593640cd763bd514b3c02c165780c295e51f2cf77`.

Mirrored files match the worktree byte for byte. Live `plugins/zola_workspace/contracts/phone_test_keys.json` was removed. A search of the live profile for that filename and for each test key's public value returned 0 hits. No store migration. Schema stays 6. Counts before the mirror: user_version 0, schema_version 6, calendar_events 1052, cursors 5, deliveries 0, item_attempts 151, items 159, loops 9, meta 7, phone_tombstones 1, watcher_health 1, watcher_rejects 1, phone rows (`items` where source is sms, mms, or notif) 0.

Client launched from the worktree: `dotnet run --project C:\Users\test\Dev\zola-windows-p10-intake\windows-client\Zola.Client\Zola.Client.csproj`. One of each at first status:

| Role | PID | Parent | Started |
|---|---|---|---|
| dotnet run | 22112 | 18328 | 09:17:26 |
| Zola.Client.exe | 29104 | 22112 | 09:17:40 |
| watcher trampoline | 6852 | 29104 | 09:17:42 |
| watcher | 25716 | 6852 | 09:17:42 |
| zola-phone trampoline | 19728 | 29104 | 09:17:42 |
| zola-phone | 25776 | 19728 | 09:17:42 |
| serve trampoline | 11780 | 29104 | 09:17:43 |
| serve | 18524 | 11780 | 09:17:43 |

Listener: `TCP 100.102.206.71:47821` only, owned by 25776. Status pipe, no secret: `link_state=not_paired`, `paired=false`, `socket_open=false`. Watcher polled gmail at 09:17:47 (`new=11`) and calendar at 09:17:49.

F6, by PID, all inside 10 minutes. `supervisor.log` under `%LOCALAPPDATA%\ZolaClient\logs`:

| Step | What happened |
|---|---|
| Kill phone leaf 25776 | trampoline 19728 exited. New phone trampoline 11228, leaf 21976. `event=restart restarts=1`, then `job_assigned` pid 11228 |
| Kill serve leaf 18524 | phone stayed 11228 / 21976. Serve came back as trampoline 31176, leaf 26448 |
| Kill phone leaf 21976 | new trampoline 20560. `restarts=2` |
| Kill the next leaf | new trampoline 10024. `restarts=3` |
| Kill the next leaf | no zola-phone remained. `event=keeps_failing restarts=4 generation=4` at 09:20:02 |

After that latch: client 29104, watcher 6852/25716, and serve 31176/26448 are still up. Watcher polled gmail again at 09:19:47 and 09:21:48. Port 47821 is free. Phone rows are still 0. Items 170 and item_attempts 162 (the 09:17 gmail poll added 11). Tombstones still 1. Schema still 6. The client is left running so Brian can see Keeps failing. Relaunching the client clears that latch. F7 is next, and it is human-run.

The first client exited 0 at 12:08. Brian relaunched it. New tree, 12:09:18: client 15484 (parent dotnet 28284), watcher 17416/1312, zola-phone 31032/29432, serve 29544/28340. Listener only `100.102.206.71:47821`, owned by 29432. Status before any pair: `not_paired`, `paired=false`. Watcher polled gmail at 12:11:21 and 12:13:22.

Connected: the scratch fake phone paired to that live listener and sent no events. Status `connected`, `socket_open=true`, `paired=true`. Device hash `99279ee05996733a91141b950dcc36ea69f03a229b62b90db6a78f987293e00e`. Public-key hash `5db94ee6c9d171b0b48b20878e300c443ce4e49cf10550d632c8329ee1855aa7`. Brian's capture showed the PAIR button on that connected row. Smoke failed on that reading.

The companion button now comes from the row. PAIR only for Not paired. RE-PAIR only for Offline. No button for Connected, Not responding, Reconnecting, Restarting, or Keeps failing (the latch still wins, so a restart or a give-up hides the button even if the link would have been Offline). Client build 0 warnings. Checks: phone 11/11, and the other rows stay at their Phase 1 counts.

The fake pairing was cleared from the live peer file after that client exited (device id empty, public key empty; the PC key file was left in place). Relaunch at 12:49:09: client 27396, parent dotnet 30532. One watcher, one serve, one zola-phone (listener pid 27728, only `100.102.206.71:47821`). Status `not_paired`, `paired=false`. The PAIR label was visible and NOT PAIRED was visible. The button did not take clicks: it lived in the HUD grid, which is `IsHitTestVisible="False"` so the pointer passes through to the presence view. zola-phone logged no pairing request from that window.

Overlay attempt. The button was moved out of that grid and placed over the companion row's slot, on the theory that only the button would take the pointer. Client build 0 warnings. Checks: phone 12/12. Relaunched. Status `not_paired`. Listener pid 21904, only `100.102.206.71:47821`. Brian: the overlay covered the COMPANION WATCHER label and flickered between frames. Smoke failed. The HUD layer is click-through by design, so a button in the Systems panel is the wrong place, and UI changes should not be made during smoke.

Revert, source only, not rebuilt at that moment. The overlay button, the in-row slot, `OnPairPhone`, `PlacePairButton`, the PAIR / RE-PAIR copy, and the two button checks were removed. The companion row is status only.

Brian chose the dock. One dock button, styled like Conversation and Sessions, sits after Sessions. `SystemsCopy.PairAction` returns `PAIR PHONE` for `not_paired` and `RE-PAIR PHONE` for `offline`, and null for connected, not responding, reconnecting, Restarting, and Keeps failing. The click calls `PhoneProcess.StartPairing` and opens one dialog: the code in large digits as two groups of four, the line “Expires in 5 minutes”, and Close. No code comes back as “Phone is not available.” The code is not logged. Client build 0 warnings. Checks: phone 11/11, other rows unchanged.

Relaunched from the worktree. Status `not_paired`. The companion row shows the full label COMPANION WATCHER and the state NOT PAIRED, with no button on the row. PAIR PHONE was invoked. The dialog opened with a grouped code, “Expires in 5 minutes”, and Close. The phone log line is `zola_phone.pairing result=started` and does not contain the code. Brian confirmed the row, the dock button, and the dialog.

Connected: the fake phone paired again and sent no events. Status `connected`, socket open, last ping answered. The row was the full label and a dim dot, with no state word and no dock button. Device hash `99279ee05996733a91141b950dcc36ea69f03a229b62b90db6a78f987293e00e`.

Reconnecting: the fake phone was stopped at 13:21:47. Status `reconnecting`, socket closed. The row reads RECONNECTING. No pair button. zola-phone stayed listening, pid 24444, only `100.102.206.71:47821`. Brian confirmed Reconnecting.

Offline: at 13:30:12, past the 480000 ms grace, status `offline`, socket closed, still paired. The row reads OFFLINE. The dock button is RE-PAIR PHONE. zola-phone was still pid 24444. Brian confirmed Offline.

Restarting: phone leaf 24444 was killed at 13:30:49. The row read RESTARTING in that instant. `supervisor.log`: `event=restart restarts=1 generation=1`, then `job_assigned` pid 22860 at 13:30:51. The listener came back as pid 14076, only `100.102.206.71:47821`. The latch was gone before a still capture; the capture after it shows OFFLINE again, which is the link once the new process is up (`offline`, socket closed, paired). Keeps failing stays the F6 result (`restarts=4` at 09:20:02). One kill only, so this restart did not reach the give-up.

Phone rows are still 0. Items 175. Tombstones 1. Schema 6. Live logs: scripted body 0, PEM 0, fault launch secret 0.

Brian, 13:53: smoke test passed.

The fake pairing was then removed from `phone/peer_state.json` (device id empty, public key empty, `phone_seq` 0). The PC key file was left in place. The running zola-phone was killed once so it could not write the old peer back; the replacement loaded the cleared file. Status `not_paired`, `paired=false`.

## IN-G answers

Phase 2 recorded the grounding. Phase 3 was the proposal. Phase 4 applied the verdicts. Phase 5 applied F1–F11.

## Residuals

The pipe's next instance is created right after a client is handed off, so the name has a very short window where only the in-service instance holds it.

Live `phone_test_keys.json` is removed and absent from a profile-wide search. One synthetic tombstone remains. The Phase 9 watcher commit-then-evaluate split is not this track's. Smoke passed. The fake pairing is out of the live key store. Restarting is a latch of about two seconds; F7 confirmed it by the row name at the kill instant and by `supervisor.log`, and the still after the latch shows OFFLINE.

## Phase 7 — Closeout

7a, 2026-10-20. The worktree client was still up and held `Local\ZolaPhone`, so the first phone-suite run failed two tests (`test_f4_second_process_refuses_the_pipe_and_mutex` saw exit 2, and the isolation startup line was empty). That client is a process this track started. It was stopped by PID (dotnet run 31016, Zola.Client 9640). Nothing named `zola_phone` remained, and port 47821 was free. The phone suite was run again and passed. That stop is also the client close Phase 7 asks for before the merge.

| Suite | Result |
|---|---|
| `zola_workspace` | 357 OK |
| `zola_memory` | 134 OK |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |
| `zola_phone` | 29 OK |

`dotnet build` of `Zola.Client`: 0 warnings, 0 errors. Client checks: lifecycle 22/22, admission 13/13, start 9/9, invalid 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 38/38, phone 11/11.

Live mirror: 15 shipped plugin files match the worktree, SHA-256 equal. Live `phone_test_keys.json` is absent. `hermes-agent` is clean at `345cd2b057a452236de401d3534b8502a7465e8d`. The repo tracks no `proactive.db`, no `pc_key.bin`, and no `peer_state.json`. `phone_test_keys.json` stays in the repo as the Track 1 test fixture and is not loaded at runtime.

Firewall read-back, not modified: DisplayName "Zola phone intake", Inbound, Allow, Enabled, Profile Any, TCP 47821, InterfaceAlias Tailscale. Before the client stop, the only listener was `100.102.206.71:47821`.

Implementation SHA: IMPLEMENTATION_SHA

### Exit criteria

| # | Criterion | Result |
|---|---|---|
| 1 | IN-G1–G10 answered; STOP verdicts recorded; firewall in place | Met. Verdicts are in Phase 3. Firewall read-back above. |
| 2 | `zola-phone` imports no Google or model module | Met. Source scan of `zola_phone` `import`/`from` lines: no Google, Gmail, ranker, or Hermes agent/model module. Runtime proof is `test_isolation_on_the_real_startup_path` inside the 29 OK. |
| 3 | Listener only on the Tailscale address and port 47821; LAN refused | Met. One listener, `100.102.206.71:47821`, before the client stop. `test_f7_lan_address_is_not_a_tailnet` is in the 29 OK. |
| 4 | F1–F7 pass; no message content in logs | Met. Part A table and the fault-launcher table above. F6 `keeps_failing` at 09:20:02. F7 states confirmed. Live logs: scripted body 0, PEM 0. |
| 5 | Suites and client checks | Met. Counts in the table above. |
| + | G-RESEND, G-SUPERSEDE-AFTER-AUTH, G-SIZE-FIRST | Met. Fresh envelope `duplicate`; old envelope `replay`; bad second connection left the first delivering; raw oversize `too-large` before parse. |
| + | Track 1 test-key copy removed; `phone_test_keys.json` not in the live mirror and not loaded at runtime | Met. Profile search 0 hits. |
| + | Commit-before-ack and both watch-recovery crash points | Met. Fault launcher: before_ack pid 20108 exit 1, one row, resend `duplicate`; before_eval pid 20060 exit 1, recovery `watch_evaluated=1`, one loop match, resend `duplicate`. Production `__main__.py` takes no fault argument. |
| + | One writer; `late-result` distinct; no live phone rows; PC key DPAPI and never logged | Met. F5 late answer logged `late-result`. Phone rows 0. Schema 6. |
| + | Tailscale 2FA recorded; no installs; no Hermes, watcher, ranker, or lore change | Met. Brian: "Two-factor is on for my Tailscale account." Hermes porcelain empty at the pin. |

### IN-G choices as shipped

| Item | Choice |
|---|---|
| IN-G1 | Sibling package `zola_phone` plus the `loop_match.py` leaf. `loops.py` re-exports `evaluate`. |
| IN-G2 | Port 47821. Resolve with `tailscale ip -4`. Bind only inside 100.64.0.0/10. |
| IN-G3 | ECDSA P-256, DPAPI `pc_key.bin`, HMAC-SHA256 with the 8-digit code. |
| IN-G6 | Named pipe `\\.\pipe\ZolaPhone`. The per-launch secret is required for history, notifications, code, diagnostic read, and `pairing.start`. Status does not need it. |
| IN-G7 | Brian: "Supervision: Option A." Shipped as one start plan (`PythonStart.Build`) and one spawn path (`SupervisedPython`). `PhoneProcess` is the phone label. `WatcherProcess` is the watcher label. |
| IN-G8 | Live `status` on the pipe plus the process latch. No `phone_health` table. No schema 7. Grace 480000 ms. |
| IN-G10 | F1–F5 on the scratch home and port 47821. F6–F7 on the live profile with no phone rows. |

### Verdicts, verbatim

- "Supervision: Option A."
- "Keep the secret. The client mints it at launch, keeps it, and passes it only to serve and zola-phone. Require it for read_history, read_notifications, read_code, diagnostic_read and pairing.start. Status doesn’t need it."
- "Health: track the connection and its responsiveness separately. Connected = socket open and the last ping answered. Not responding = socket open but a ping missed. Reconnecting = socket closed, counted from the moment it closed, for up to 480 seconds. Offline = closed longer than that. Restarting and Keeps failing come from the process latch."
- "Contract v2 updates the golden vectors and rejects unsupported versions explicitly."
- "Two-factor is on for my Tailscale account."
- "I ran the firewall command."
- "proceed to phase 4"
- "Status currently shows Pair."
- "smoke test failed: the PAIR button shows while the phone is connected, which reads as if it needs pairing."
- "It now shows Pair along with Not Paired. Is the Pair button active now? It doesn't seem to be."
- "smoke test failed: the PAIR overlay covers the COMPANION WATCHER label and flickers between frames."
- "The row and the dock button look right, and the dialog opened with a readable code."
- "Reconnecting is confirmed."
- "offline confirmed"
- "smoke test passed"
- "Proceed to closeout"

Merge SHA: MERGE_SHA
