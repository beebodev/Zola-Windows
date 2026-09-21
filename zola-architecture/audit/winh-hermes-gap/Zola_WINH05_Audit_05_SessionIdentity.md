# WINH05 Audit 05 — Session Identity

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: `Zola_Session_Identity_Architecture.md` (`SessionRecord`, single mint site, foreground/background + 30s same-device grace, per-user with device as provenance, `sessionId` on durable writes). Document status line: design locked, **not yet implemented** as a Zola build track — this audit asks only whether **Hermes** has an equivalent the Windows track could wrap.

WINH03 session durability / disconnect grace is reused as mechanism evidence, not re-scored as new operational-contract findings.

---

## 1. Session as an explicit record

**Zola requires:** `SessionRecord` with `sessionId`, `userId`, `startedAt`, `endedAt`, `deviceId` (provenance only). Distinct from transcript rows; transcripts **attach** to the session.

**Hermes:** `state.db` table `sessions` (`hermes_state_common.py` L328–389) is an explicit session **row**, not merely messages:

| Zola field | Hermes column | Notes |
|---|---|---|
| `sessionId` | `id` TEXT PK | `YYYYMMDD_HHMMSS_<hex>` when minted via `new_session_id` |
| `userId` | `user_id` TEXT | Optional; used on gateway/messaging (`find_session_by_origin` `hermes_state_sessions.py` L388–409) |
| `startedAt` / `endedAt` | `started_at` / `ended_at` REAL | Present |
| `deviceId` | **none** | `source`, `cwd`, `profile_name`, `chat_id` / `origin_json` are adjacent but not an originating-device field |

Messages are a **child** table (`messages.session_id` REFERENCES `sessions(id)`, L391–393). Session identity is **distinct** from transcript rows.

Live JSON-RPC also keeps an in-process dict `_sessions` (`tui_gateway/server.py`) keyed by a **short runtime sid** (`uuid.uuid4().hex[:8]`, `methods_session.py` `_new_runtime_ids` L65–67) plus durable `session_key`. WINH03-AUD-09: crash loses live runtime; `session.resume` reloads the durable row.

**Label:** `[PARTIAL]` `WINH05-AUD-14` (MEDIUM) — explicit session row exists; `deviceId` provenance field is missing; live sid vs durable `id` is two identifiers for one conversation.

---

## 2. Single minting authority

**Zola requires:** **exactly one call site** mints a session ID, so a future backend can replace that seam (`Session Identity` §5).

**Hermes:** one **shape function**, many **call sites**, plus other ID kinds.

Shared shape: `hermes_state_ids.py` `new_session_id` L24–28 — module docstring: “the ONE place that knows the `YYYYMMDD_HHMMSS_<hex>` shape.” Callers include:

- `agent/agent_init.py` `_init_session_state` L1124 (`session_id or new_session_id(...)`)
- `cli.py` L2836
- `hermes_cli/cli_session_mixin.py` L522
- `tui_gateway/server.py` `_new_session_key` L2432–2433
- `gateway/session.py` L1008, L1095 via `gateway/session_lifecycle.py` `_new_session_id` L25–26 (`hex_len=8`)
- `hermes_state_portability.py` L110 (`hex_len=12`)
- `hermes_cli/foreign_sessions.py` L248

**Independent of that function:**

- JSON-RPC **runtime** sid: `uuid.uuid4().hex[:8]` (`methods_session.py` L67, L1976) — different namespace from durable `session_key`.
- Optional Honcho (and other providers) mint **their own** session/peer session keys (WINH04 Honcho README session naming) — a second session universe when the plugin is on. Analogous to `WINH04-AUD-02` (second write authority).

This is **not** “one call site.” Swapping local mint for a backend-issued ID would require touching every caller above, plus the live-sid path.

**Label:** `[RISK]` `WINH05-AUD-15` (HIGH) against single minting authority.

---

## 3. Start/end triggers and grace period

**Zola requires:** start on app foreground; end on background after **30-second same-device** grace; `endedAt` stamped when grace lapses; reconnect within 30s **reuses** the same `sessionId`.

**Hermes:**

- Sessions start when a CLI/gateway/JSON-RPC path **creates** an agent / `create_session` row — not on OS app-foreground as a defined trigger.
- JSON-RPC disconnect: **20s** orphan grace, then **defer interrupt** while the turn is “fresh” (default **600s** activity window) — WINH03-AUD-05; `tui_gateway/server.py` L122–140; `session_lifecycle.py` L507–572. Product intent: “an active turn runs to completion.” That is **process/connection** grace, not Zola’s 30s same-device background close.
- Reconnect shortly after disconnect: live `_sessions` entry can still be there (parked); client resumes the **same** durable `session_key`. After process death: `session.resume` cold-loads transcript (WINH03-AUD-09) — **same persisted id**, new runtime sid.
- `ended_at` is set on explicit end/compression/archive paths, not on a 30s background timer.

**Label:** `[PARTIAL]` `WINH05-AUD-16` (MEDIUM) — reconnect/resume exists; boundary triggers and 30s foreground/background grace do not match Zola.

---

## 4. Per-user, not per-device scope

**Zola:** session belongs to the **user**; `deviceId` is provenance; a new device always starts a **new** session; no cross-device session continuity.

**Hermes:**

- Default CLI/Desktop: session lives in a **profile** `state.db` (`profile_name` column L380). Scope is **Hermes profile / HERMES_HOME**, which is typically one human operator, not a Zola `userId` plus device provenance.
- Gateway/messaging: `user_id` + `chat_id` routing (`find_session_by_origin` L388–409) — closer to per-sender on a platform, still not “user record + device field.”
- JSON-RPC live sid is **per connection/runtime**.
- No `deviceId` column. Cross-device: two Desktops on one profile share `state.db` if they share `HERMES_HOME`; that can **continue** the same session ids rather than minting per device.

**Label:** `[PARTIAL]` `WINH05-AUD-17` (MEDIUM) — not device-scoped exclusively, but not Zola’s user-owned + device-provenance model either.

---

## 5. Session ID as provenance on durable writes

**Zola requires:** every durable write carries `sessionId` for idempotency/conflict attribution.

**Hermes:**

- **Transcripts:** `messages.session_id` NOT NULL FK (`hermes_state_common.py` L391–393). `[MATCH]` for this store.
- **Token/usage:** `hermes_state_usage.py` keys off `session_id`.
- **Builtin MEMORY.md / USER.md:** `tools/memory_tool.py` / `memory_tool_store.py` — **no** `session_id` field; entries are `§`-delimited strings. `memory_tool` grep for `session_id`: no matches. Agent may have `HERMES_SESSION_ID` in env (`agent_init.py` `_publish_session_id` L1102–1118) for **tools**, but it is not persisted on the memory file.
- **Holographic facts:** `created_at` / `updated_at`, no session column in the schema excerpt (`holographic/store.py` L12–23).

**Label:** `[PARTIAL]` `WINH05-AUD-18` (MEDIUM) — transcripts yes; fact-memory writes **[GAP]** on this requirement (not a new restatement of WINH04-AUD-11 DWA; it is specifically session provenance).

---

## Finding summary (this document)

| ID | Label | Sev | Against |
|---|---|---|---|
| WINH05-AUD-14 | [PARTIAL] | MEDIUM | `SessionRecord` shape |
| WINH05-AUD-15 | [RISK] | HIGH | Single mint call site |
| WINH05-AUD-16 | [PARTIAL] | MEDIUM | Foreground/background + 30s grace |
| WINH05-AUD-17 | [PARTIAL] | MEDIUM | Per-user + device provenance |
| WINH05-AUD-18 | [PARTIAL] | MEDIUM | `sessionId` on all durable writes |
