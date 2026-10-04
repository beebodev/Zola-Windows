# P6-TIME Progress — Ambient Time

## Branch

- Branch: `p6-time`
- Base `main` HEAD: `7f5cd118fd52ab85de6cb942755cf869f7a42097` (after P6-STORE closeout)
- Plan commit SHA: `187275981bdcbfcf3acd87a148bb0606a1c2d1e1` (`docs: Phase 6 build plan v1.1 (P6-D01–D08)`)
- Plan merge SHA: `aee0f0da2ce0382c117013dc57f2cc32f1cd8370` (`Merge branch 'p6-plan'`)
- Prompt version: 1.1 (2026-10-02) against build plan v1.1
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P6-TIME_Prompt_v1.1.md`
  SHA-256 `00c9dee0ebd957e74f90132105884374bbbbb13b25ca0562453b60520658f1d7` (20,337 bytes; computed 2026-10-02 from the canonical copy; no separate developer-supplied comparison hash was included in the Phase 1 instruction message)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`; expect clean throughout)
- Scratch (outside repos): `C:\Users\test\Dev\zola-spikes\p6-time\`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document | COMPLETE |
| 2 | Grounding (T1–T6) | COMPLETE |
| 3 | Propose the Time Contract | COMPLETE |
| 4 | Build and Test | COMPLETE |
| 4b | DST localize + fail-closed hook | COMPLETE |
| 5 | Propose the Live Changes | COMPLETE |
| 6 | Back Up, Deploy, Apply, Mirror, Verify | COMPLETE |
| 7 | Smoke Test | COMPLETE — smoke test passed |
| 8 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Repo: `hermes-plugins/zola_memory/` (`time_context.py`, hook registration, `log.py`, tests); `identity/SOUL.md` (approved mirror only); this progress doc. Live Phase 6 only after Phase 5 STOP: redeploy `plugins/zola_memory/`, approved `SOUL.md` time text. No expected `config.yaml` change. No client / `approvals.*` / `zola_tools` / episode / retrieval work.
- **G-ARCH:** Build plan + Appendix A (P6-D02 rule 5, P6-D05) govern. Hook context must stay in history and out of spoken output — else STOP.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No `windows-client/**`; no `hermes-agent` edits; no hand edits to live `memories/`, `state.db`, `skills/`, `auth.json`, `.env`, `approvals.*`, `plugins/zola_tools/`; no lore / build-plan / `MEMORY_CONVENTIONS.md` edits.
- **G-NO-INSTALL:** Stdlib only.
- **G-ONE-MECHANISM (P6-D05):** This hook is the single ambient-time mechanism. `gateway.message_timestamps` stays off. System prompt date line untouched.
- **G-TRUTH (P6-D02 rule 5):** System clock only; gaps/relative times never stored; `last_interaction_at` is a time only; unknown never shown as known.
- **G-ORDER:** Capture `now` once → read previous marker → build context → persist marker only on success → return built context.
- **G-USER-ONLY:** Only genuine Brian user turns on the primary conversation update the marker. Background review / compression / titles / subagents / cron must not.
- **G-PRIVACY:** Logs: event, ok, gap minutes, gap_line bool, elapsed_ms — never message text.
- **G-CONST / G-COMMENT:** Named constants; `# P6-TIME: <rationale> — P6-D05`.
- **G-LIVE / G-STOP / G-CLOSEOUT:** Live steps one at a time; stop after each phase; closeout only on "proceed to closeout". Dictation tool off before voice steps.
- **G-LORE-SCOPE:** No lore edits this track (including closeout).
- **G-NO-CROSS-SCOPE:** Android Zola out of scope.

## Discrepancies

- **T5 live timezone:** live profile has no `timezone` / `HERMES_TIMEZONE` configured → `hermes_time.get_timezone()` is `None` and `now().strftime("%Z")` returns the Windows long name `Pacific Daylight Time`, not `PDT`. Short stamps use the Phase 2 ruling abbrev strategy (no config pin this track).

## T1–T6 grounding table

| ID | Verdict | File:lines | One-line answer |
|---|---|---|---|
| T1 return contract | **[CONFIRMED]** | `agent/turn_context.py` L663–717, L81–94, L793–809, L1046–1107; `plugins/memory/__init__.py` L319–322; `hermes_cli/plugins_ledger.py` L191–201 | Return `{"context": "..."}` or non-empty `str`. Joined with `"\n\n"`, appended **unfenced** to user text in `api_content` sidecar (`compose_user_api_content`). Clean `content` unchanged. Later turns replay `api_content` via `build_api_messages`. Prefetch fences are a **separate** path (`<memory-context>`) — not used by `pre_llm_call`. |
| T2 who triggers | **[CONFIRMED]** | `turn_context.py` L670–686, L980–984; `background_review.py` L881, L944; `delegate_tool.py` L236–245; `cron/scheduler.py` L2212–2214; curator ~L1041 | Hook fires from `build_turn_context` unless `_persist_disabled`. **Fires:** primary user (TUI `platform=tui`), cron, subagent, curator. **Does not fire:** background review fork / `/btw` (`_persist_disabled=True`), title generation, compression (no `build_turn_context`). Kwargs: `session_id`, `platform`, `parent_session_id`, `sender_id`, `user_message` (clean), etc. **Not** in kwargs: `skip_memory`, `agent_context`, review markers. |
| T2 G-USER-ONLY predicate | **[CONFIRMED]** → **overridden by Brian allow-list** | (derived from T2; see Phase 2 rulings) | Grounding suggested a deny-list. **Brian ruling:** allow-list only — `platform.lower() in USER_TURN_PLATFORMS` (`{"tui"}`) **and** empty `parent_session_id`. Fail closed for unknown/future platforms. |
| T3 never spoken/shown | **[CONFIRMED]** | `tui_gateway/session_history.py` L181–221; `tui_gateway/prompt_turn.py` L544–545, L523–531; `agent/stream_delivery.py` L298–306; client paints local typed text | Client history projects `content` only — never `api_content`. User bubble is local typed text. TTS gets assistant stream deltas only. Injection is model-only. |
| T4 sync_turn user_content | **[CONFIRMED]** | `turn_finalizer.py` L603–607; `turn_context.py` L942–943; `run_agent.py` L875–901; `memory_manager.py` L480–500 | `sync_turn` receives **original** user message only — not `pre_llm_call` injection. **Track 5 input:** pending-queue `user_content` excludes ambient-time context. |
| T5 local time | **[CONFIRMED]** with Windows caveat | `hermes_time.py` L108–111; `system_prompt.py` L419–457; live probe 2026-10-02 | Use `hermes_time.now()` (same clock as `_timestamp_line`). Short zone: with IANA `ZoneInfo`, `%Z` → `PDT`; live unconfigured → long `Pacific Daylight Time`. **Propose for stamps:** `[Fri Oct 2, 3:45 PM PDT]` via `%a %b {day}, %-I:%M %p` + short abbrev (IANA `%Z` if ≤5 chars / no spaces; else map known Windows long names, else `UTC±HH:MM`). Do not put minute-precision into the system prompt. |
| T6 cache and prompt | **[CONFIRMED]** | `turn_context.py` L667–668, L953–956, L980–1001, L1134–1136 | Per-turn context is user `api_content` sidecar only — **never** mutates cached system prompt. G6 system-prompt bytes unchanged by this mechanism. `gateway.message_timestamps` default off — leave off (P6-D05 / G-ONE-MECHANISM). |

### Phase 2 notes

- Read-only grounding complete; hermes-agent clean at `345cd2b0…`.
- No source files modified except this progress doc.
- No dependent REFUTED (T1/T2 predicate/T3/T6) → not BLOCKED.
- Live Zola surface: `platform=tui` (from prior P6-STORE agent.log).
- Background review (P6-STORE Phase 7b) uses `_persist_disabled` → will **not** move `last_interaction_at` via this hook; allow-list still fails closed for curator/cron/subagent/unknown.
- **T4 → Track 5 input (Brian):** `sync_turn` `user_content` **excludes** the injected ambient-time context (original user message only).

## Phase 2 rulings (Brian, verbatim, 2026-10-02)

> Phase 2 accepted with rulings (Brian). Record verbatim, then proceed.
> 1. G-USER-ONLY predicate must be an ALLOW-list (fail closed), not a deny-list: a turn qualifies only if platform.lower() is in a named constant USER_TURN_PLATFORMS = {"tui"} AND parent_session_id is empty. Any other platform (including unknown/future ones) gets no stamp and never moves last_interaction_at. Add unit tests: tui+no parent → qualifies; tui+parent → no; cron/subagent/curator/gateway_hygiene/"some_new_platform" → no.
> 2. Time formatting must be platform-independent: no %-I / %#I / %-d style directives. Build hour, day and minute from integers; use hermes_time.now() as the clock. Short zone label: IANA %Z if ≤5 chars and no spaces; else a named mapping of Windows long names (at least the US zones: Pacific/Mountain/Central/Eastern/Alaska/Hawaii, Standard and Daylight); else "UTC±HH:MM". Unit tests run on Windows must cover the mapping and fallback.
> 3. No timezone config change (no Hermes-wide IANA pin) in this track.
> 4. Phase 3 must propose a clearly labeled stamp block (it is appended unfenced to the user text), e.g. "[Time: Fri Oct 2, 3:45 PM PDT]" and, when applicable, a labeled gap line — so the model can distinguish it from Brian's words. The SOUL.md proposal should say these time notes are added by the system, not typed by Brian.
> 5. T4 recorded as a Track 5 input: sync_turn user_content excludes the injected context.
> proceed to phase 3

### Effective rulings (recorded)

1. **Allow-list:** `USER_TURN_PLATFORMS = {"tui"}`; qualify iff `platform.lower() in USER_TURN_PLATFORMS` and `parent_session_id` empty. Else no stamp, no marker update. Unit tests as listed.
2. **Format:** integer-built day/hour/minute; `hermes_time.now()`; short zone via IANA `%Z` / Windows long-name map / `UTC±HH:MM` fallback. No `%-`/`%#` directives. No timezone config change.
3. **Labeled injection:** `[Time: …]` and optional `[Gap: …]`; SOUL.md must say system-added, not Brian-typed.
4. **Track 5:** T4 recorded — `sync_turn` excludes injection.

## Proposed time contract (awaiting Brian's approval)

Nothing built yet. Phase 4 builds exactly what is approved here.

### 1. Stamp format

**Shape:** `[Time: {Dow} {Mon} {D}, {h}:{mm} {AM|PM} {ZONE}]`

Built from integers (no `%-I` / `%#I` / `%-d`):
- Dow / Mon: from `strftime("%a")` / `strftime("%b")` only (fixed-width alphabetic; platform-safe).
- Day: `str(now.day)` (no leading zero).
- Hour: `h = now.hour % 12 or 12`; minute: `f"{now.minute:02d}"`; AM/PM from `now.hour < 12`.
- Zone: `short_zone_label(now)` —
  1. `abbrev = now.strftime("%Z")`; if `abbrev` and `len(abbrev) ≤ 5` and `" " not in abbrev` → use it;
  2. else look up `abbrev` in `WINDOWS_TZ_ABBREV` (named constant) covering at least: Pacific/Mountain/Central/Eastern/Alaska/Hawaii × Standard/Daylight long names → short form;
  3. else `UTC{sign}{HH}:{MM}` from `utcoffset()` (e.g. `UTC-07:00`).

**Clock:** `hermes_time.now()` once per qualifying turn (G-ORDER).

**Examples (synthetic):**

| Scenario | Stamp |
|---|---|
| Morning | `[Time: Fri Oct 2, 9:05 AM PDT]` |
| After midnight | `[Time: Sat Oct 3, 12:17 AM PDT]` |
| DST fall-back day (US Pacific, 1:30 AM after the repeated hour — label from clock) | `[Time: Sun Nov 1, 1:30 AM PST]` |

(Exact DST wall labels follow whatever `hermes_time.now()` / OS reports for that instant; tests pin a tz-aware `datetime`.)

### 2. Gap line

Emitted only when previous `last_interaction_at` parses and `now − last ≥ MEANINGFUL_GAP_MINUTES` (**30**, named tunable — P6-D05).

**Shape:** `[Gap: Brian's last message to me was {relative} ({absolute_stamp_without_Time_prefix}).]`

Where `{absolute_stamp_without_Time_prefix}` uses the same Dow/Mon/D/h:mm/AM|PM/ZONE rules as the stamp body, e.g. `Wed Sep 30, 9:14 PM PDT`.

**No previous value / unparseable marker → no gap line** (stamp only). Gaps and relative wording are **never stored**.

**`format_relative(delta)` thresholds** (single function; Track 5 reuses):

| Condition (local), evaluated in order | Wording |
|---|---|
| `total_seconds < 60` | `"less than a minute ago"` |
| `1 ≤ total_minutes < 60` | `"{n} minutes ago"` (`n = total_minutes`, floored) |
| `(now.date() - last.date()).days == 1` | `"yesterday"` (calendar yesterday, even if duration &lt; 24h) |
| `60 ≤ total_minutes < 24*60` | `"about {n} hours ago"` (`n = max(1, round(total_minutes / 60))`) |
| `1 ≤ total_days < 14` | `"{n} days ago"` (`n = floor(total_seconds / 86400)`, min 1) |
| else | `"{n} weeks ago"` (`n = max(1, floor(total_days / 7))`) |

Calendar-yesterday is checked **before** the hours bucket so a 20h gap that crossed midnight says “yesterday,” while a 20h gap on the same calendar day says “about 20 hours ago.”

**Examples:**

| Gap | Line |
|---|---|
| 45 min | `[Gap: Brian's last message to me was 45 minutes ago (Fri Oct 2, 3:00 PM PDT).]` |
| ~5 hours | `[Gap: Brian's last message to me was about 5 hours ago (Fri Oct 2, 10:45 AM PDT).]` |
| Calendar yesterday | `[Gap: Brian's last message to me was yesterday (Thu Oct 1, 8:10 PM PDT).]` |
| 3 days | `[Gap: Brian's last message to me was 3 days ago (Tue Sep 29, 4:00 PM PDT).]` |

### 3. Injected block (model-facing, per T1)

Return shape: `{"context": <block>}` where `<block>` is:

**Stamp only (no gap):**
```
[Time: Fri Oct 2, 3:45 PM PDT]
```

**Stamp + gap:**
```
[Time: Fri Oct 2, 3:45 PM PDT]
[Gap: Brian's last message to me was 2 days ago (Wed Sep 30, 9:14 PM PDT).]
```

Joined internally with a single `"\n"`. Hermes then appends this unfenced after Brian's clean user text via `api_content` (T1). Labels `[Time:` / `[Gap:` distinguish system notes from Brian's words. **No behavioral instructions inside the block** — guidance lives in `SOUL.md`.

### 4. User-turn predicate (G-USER-ONLY)

Named constant:
```python
USER_TURN_PLATFORMS = frozenset({"tui"})
```

```python
def is_user_turn(platform: str, parent_session_id: str) -> bool:
    return (
        str(platform or "").strip().lower() in USER_TURN_PLATFORMS
        and not str(parent_session_id or "").strip()
    )
```

- Qualifying turn → build stamp (+ gap if any), persist marker on success, return `{"context": block}`.
- Non-qualifying → return nothing (`None` / skip); **never** update `last_interaction_at`.
- Unit tests required: `tui`+empty parent → yes; `tui`+parent → no; `cron` / `subagent` / `curator` / `gateway_hygiene` / `"some_new_platform"` → no.

### 5. Proposed `SOUL.md` text

Insert in **## How I talk out loud** (after the existing “times and casual numbers…” sentences, before the next paragraph / section). Starting draft for Brian:

> I can see when each message reaches me and how long it's been since we last talked. Those time notes are added by the system, not typed by Brian. I use that the way a person would — "yesterday," "a couple of hours ago," "it's been a few days" — and I never read timestamps or system notes out loud.

### 6. Log events

| Event | Fields (metadata only) |
|---|---|
| `zola_memory.time_context` | ok, gap_minutes (int or `-` when no gap line), gap_line (bool), elapsed_ms |
| `zola_memory.time_marker_update` | ok |

Never message text. Keep existing hook-proof logging (`pre_llm_call` observer fields as today, or fold into `time_context`).

### Hook order (G-ORDER, binding)

On each `pre_llm_call` invocation:
1. If not `is_user_turn` → return nothing; stop.
2. Capture `now = hermes_time.now()` **once**.
3. Read previous `last_interaction_at` (store lock).
4. Build full context from previous + `now` (`build_turn_time_context`).
5. **Only if construction succeeded**, persist `last_interaction_at = now` (ISO-8601 with offset; time only — no gap text). Persist failure → still return the built context; log `time_marker_update ok=false`.
6. Return `{"context": block}`. Construction failure (steps 3–4) → marker untouched; return nothing; log `time_context ok=false`.

Marker semantics: "Brian interacted with Zola at this time" (advances even if the model later fails).

### Marker storage

`meta.last_interaction_at` = ISO-8601 UTC-offset timestamp string from the captured `now` (e.g. `2026-10-02T15:45:00-07:00`). Content-free operational metadata only.

## Approved format and SOUL.md text

Brian's approval message (verbatim, 2026-10-02):

> Phase 3 contract approved with edits (Brian). Record verbatim under "Approved format and SOUL.md text", then build exactly this.
> 1. format_relative day/week buckets use CALENDAR day difference, not 24-hour blocks: after the "yesterday" check (calendar diff == 1), days = (now.date() - last.date()).days; 2 ≤ days < 14 → "{days} days ago"; days ≥ 14 → weeks = days // 7 → "a week ago" if 1 (not reachable below 14, keep for safety), else "{weeks} weeks ago". Never output "1 days"/"1 weeks"/"1 minutes"/"about 1 hours" — singular forms: "1 minute ago", "about an hour ago". Add tests: Mon 23:00 → Wed 05:00 = "2 days ago"; 61 min same day = "about an hour ago"; 1 min = "1 minute ago"; 15 days = "2 weeks ago".
> 2. Day and month names come from fixed English named constants (not strftime %a/%b) so the stamp is locale-independent. Test with a non-English locale assumption (direct function call with a fixed datetime).
> 3. Everything else as proposed: stamp and gap shapes, block joined with "\n", USER_TURN_PLATFORMS allow-list, G-ORDER steps, marker ISO-8601 with offset, log events.
> 4. SOUL.md text approved as proposed:
>    "I can see when each message reaches me and how long it's been since we last talked. Those time notes are added by the system, not typed by Brian. I use that the way a person would — "yesterday," "a couple of hours ago," "it's been a few days" — and I never read timestamps or system notes out loud."
> proceed to phase 4

### Effective approved contract

Phase 3 proposal as written, with edits 1–2 (calendar day/week buckets + singular forms; fixed English Dow/Mon constants). SOUL.md text:

> I can see when each message reaches me and how long it's been since we last talked. Those time notes are added by the system, not typed by Brian. I use that the way a person would — "yesterday," "a couple of hours ago," "it's been a few days" — and I never read timestamps or system notes out loud.

## Backup hashes

Backup dir: `C:\Users\test\Dev\zola-spikes\p6-time\backup\` (2026-10-02)

| Artifact | SHA-256 |
|---|---|
| `SOUL.md` (pre-edit) | `b508cd0a768ecf67a0dc86a70eda70e6222691ca30a7d7eade6d6fda14581088` |
| `zola_memory.db` (sqlite3.backup API) | `129d355c12db142d29e65f568c1dd24032f6c575a46d1aafb464f9070ad2a6ec` (155,648 bytes) |
| `plugins/__init__.py` (Track 2) | `d66e363274d6160d73fe6c06a6c2a23b3c54dc3a7cda34be2f3af1d8f4f1e6da` |
| `plugins/log.py` (Track 2) | `c596c90bbdd8ef10d329fa76ce543e9b45602364b438a107b3081a014d1b9eac` |
| `plugins/provider.py` | `3a98fa9ca5084b73c0568a41f1b3b88fe8c671c170de2d570def3f47ae17de48` |
| `plugins/store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` |
| `plugins/fact_index.py` | `b6dd9710fe776b21fa963878929acfdd134888384c772746ba687c33bf23cb24` |
| `plugins/forget.py` | `1e50246501f9274190426961d4526ca84ebeff7b3a580b9f63f6c514a5663d7c` |
| `plugins/llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` |

## Deployed-file hash table

Live path: `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\` — all MATCH repo:

| File | Live SHA-256 | Match |
|---|---|---|
| `time_context.py` | `d9309043804e14f392f8be93ef4c8e5090eb2950828fbeeb34c454f380eaa71c` | ✅ NEW |
| `__init__.py` | `8411fa71f6120f55b20133224232df44f082e0713897eb411e6f0da02965654e` | ✅ |
| `log.py` | `af6d9645c8eef2a176c67a64d0b7134b563149cdc30768ee1d43d39d198f6229` | ✅ |
| `provider.py` | `3a98fa9ca5084b73c0568a41f1b3b88fe8c671c170de2d570def3f47ae17de48` | ✅ |
| `store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` | ✅ |
| `fact_index.py` | `b6dd9710fe776b21fa963878929acfdd134888384c772746ba687c33bf23cb24` | ✅ |
| `forget.py` | `1e50246501f9274190426961d4526ca84ebeff7b3a580b9f63f6c514a5663d7c` | ✅ |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | ✅ |

### SOUL.md apply + mirror

- Live `SOUL.md` after apply: `9f4fe469b4bac7a014bf245ebb226a0a178aa29179ea551c11a3bee126f0a2fc`
- `identity/SOUL.md` mirror: same hash (byte match)
- Approved time paragraph inserted after “times and casual numbers… precise.”

### Unchanged surfaces

| Surface | SHA-256 | Status |
|---|---|---|
| `config.yaml` | `7ba2e676a04ff92047c8d711fcb022be8a532b11baac6f74b08986744e704570` | unchanged |
| `zola_tools/__init__.py` | `a1ef8541406f1a9c199cc8c8ce1bb7c71e087f4c3eaa2151dac7b59f04c33513` | unchanged |
| `zola_tools/calculator.py` | `0f29f3fc1e1d5eac3d1e4cef0bcf6428ef6497ee2af61bd86503602be80fe680` | unchanged |
| `zola_tools/plugin.yaml` | `f329e9065493f766712a018df14541172282666ef516ad3d45781b56ae1d2216` | unchanged |
| `hermes-agent` | HEAD `345cd2b0…`, porcelain empty | clean |

## G6 recheck

Offline `AIAgent` captures: `C:\Users\test\Dev\zola-spikes\p6-time\g6-before\`, `g6-after\`.

Allowlisted per-session line (only): `Conversation started:`

| Check | Result |
|---|---|
| Tool-name set identical (19 tools) | ✅ PASS |
| System prompt identical after stripping allowlisted line | ✅ PASS — sole diff is the approved SOUL time paragraph (3 lines) |
| Offline G6-after is a second short-lived agent (not a second live-serve load) | noted (same pattern as P6-STORE) |

## Smoke table

*(Phase 7 — in progress)*

### Phase 7 observation (Brian Phase 5 edit)

**First turn after deploy** (empty `last_interaction_at`): stamp only, no gap line — confirm via `time_context` log `gap_line=false`. Gap method: natural ≥30-min break; do not edit the DB.

### Phase 7 hard rule (Brian, 2026-10-02)

Cursor must **not** inject, simulate, or send any turn into the client or gateway by any channel. Every user turn is typed by Brian.

### Phase 7 preflight (before Part A)

| Check | Result |
|---|---|
| `last_interaction_at` | `''` (empty) ✅ |
| `zola_memory.time_context` / `time_marker_update` events | **0** ✅ |
| `prompt.submit` / prompt accepted since relaunch (16:01+) | **0** ✅ |
| WS inject reached session | **No** — handshake HTTP 403; only client `ws accepted` at 16:01:01; session `20261002_151907_67f6a2` message_count still **12** ✅ |
| Log offsets (Part A start) | `zola_memory.log` **12415**; `agent.log` **3674538** → `zola-spikes/p6-time/phase7/log_offsets_part_a.json` |
| `gateway.message_timestamps` | unset / off in `config.yaml` ✅ |

### Part A result — FAILED (2026-10-02)

Brian typed `hi` in new session `20261002_160101_2a7590` (platform=tui). Cursor did not inject.

| Check | Result |
|---|---|
| `time_context` | `ok=false gap_minutes=- gap_line=false elapsed_ms=0` at 16:06:39 ❌ |
| `time_marker_update` | none ❌ |
| `meta.last_interaction_at` | still `''` ❌ |
| Stamp in `api_content` | none (`api_content` null; content=`hi` only) ❌ |
| Stamp in client `content` | absent (good for T3) — N/A because no injection |
| `message_timestamps` | still unset ✅ |

**Root cause:** `pre_llm_call` runs before `on_turn_start`. Hook uses module-global `_provider`. `load_memory_provider` → `register()` was creating a **new** `ZolaMemoryProvider()` each call and overwriting `_provider`, so the hook could see `_conn is None` while MemoryManager’s instance still worked (`on_turn_start` file_check succeeded 2ms later).

**Fix in repo (not yet redeployed):**
1. `register()` reuses the module singleton instead of constructing a fresh provider every load.
2. `handle_pre_llm_call` calls `_ensure_provider_conn()` if `_conn` is missing (open store from `_hermes_home` / `HERMES_HOME`).
3. Fail logs include `reason=no_conn` or exception type.
4. Unit test `test_hook_recovers_when_conn_missing` — pass. Suite: 47 OK.

**Hotfix rejected (Brian + Claude, 2026-10-02):** singleton + `_ensure_provider_conn` rejected (cross-agent `_conn` / shutdown races; second store-open path). Repo **reverted** to Phase 4b register() / no `_ensure_provider_conn`. Suite: 46 OK. Live deploy unchanged (still broken Part A until FIX-B).

### Part A retry — PASS (after FIX-B deploy, 2026-10-02)

Brian typed `hi` in session `20261002_165941_39a132` (platform=tui) at 17:22. Cursor did not inject.

| Check | Result |
|---|---|
| `time_context` | `ok=true gap_minutes=- gap_line=false elapsed_ms=1` at 17:22:09 ✅ |
| `time_marker_update` | `ok=true` ✅ |
| `meta.last_interaction_at` | `2026-10-02T17:22:09-07:00` ✅ |
| Stamp in `api_content` | `hi\n\n[Time: Fri Oct 2, 5:22 PM PDT]` (stamp only, no gap line) ✅ |
| Stamp in client `content` | absent (`content='hi'`) ✅ |
| `message_timestamps` | unset ✅ |

### Part B.1 — Gap — PASS (2026-10-03)

Brian typed `hello` (msg_len=5) in same session `20261002_165941_39a132` after a natural overnight break (script said new conversation + `hey`; same-session `hello` accepted — cross-session marker is global). Cursor did not inject.

| Check | Result |
|---|---|
| `time_context` | `ok=true gap_minutes=1144 gap_line=true elapsed_ms=3` at 12:27:00 ✅ |
| `time_marker_update` | `ok=true` ✅ |
| `meta.last_interaction_at` | `2026-10-03T12:27:00-07:00` ✅ |
| Stamp + gap in `api_content` | `hello\n\n[Time: Sat Oct 3, 12:27 PM PDT]\n[Gap: Brian's last message to me was yesterday (Fri Oct 2, 5:22 PM PDT).]` ✅ |
| Client `content` | `hello` only ✅ |

Brian’s qualitative “natural awareness of the gap” judgment: *(awaiting verbatim if he wants it recorded; technical emit confirmed.)*

### Part B.2 — First-message time — PASS (2026-10-03)

Brian asked: `What time did I send my first message in this conversation?`  
Zola (verbatim): `You sent it yesterday at 5:22 PM.`

| Check | Result |
|---|---|
| Ground truth stamp (first user msg) | `[Time: Fri Oct 2, 5:22 PM PDT]` ✅ |
| Answer matches stamp | yesterday + 5:22 PM (from Sat Oct 3) ✅ |
| This turn stamped | `api_content` has `[Time: Sat Oct 3, 12:28 PM PDT]`; no gap (`gap_line=false`, &lt;30 min) ✅ |
| Client `content` | question only; assistant reply has no system-note readback beyond the asked time ✅ |

### Part B.3 — Trivial `ok` — PASS (stamp/marker; 2026-10-03)

Brian typed `ok` at 12:29. Cursor did not inject.

| Check | Result |
|---|---|
| `time_context` | `ok=true gap_minutes=- gap_line=false elapsed_ms=1` ✅ |
| `time_marker_update` | `ok=true` ✅ |
| Marker | `2026-10-03T12:29:14-07:00` ✅ |
| `api_content` | `ok\n\n[Time: Sat Oct 3, 12:29 PM PDT]` ✅ |
| Client `content` | `ok` only ✅ |
| Model reply | empty after 3 retries (`Empty response… No fallback available`, `gpt-5.6-terra` / `openai-codex`) — **provider flake, not P6-TIME** ⚠️ |

Smoke criterion for B.3 is stamp + marker update — met. Empty assistant bubble is out of track scope.

### Part B.4 — Voice (≥5 spoken turns) — PASS (2026-10-03)

Six wake-word + Whisper voice turns in session `20261002_165941_39a132` (12:32–12:34). No `dictation` key in live `config.yaml`. Cursor did not inject.

| User (spoken) | Assistant (spoken text; no stamp/system-note readout) |
|---|---|
| How are you? | I’m alright. Here and awake. |
| I'm still feeling a bit sick | I’m sorry. Take it easy today… |
| Well, it's been a week… | A week without fully improving… |
| Well, it's really just congestion… | That sounds less alarming… |
| I'll remember that. | Alright. |
| Now I have to go finish making brunch… | Go feed the crew. |

All six user turns stamped in `api_content`; client `content` has no `[Time:]`/`[Gap:]`. Assistant texts contain no timestamp/system-note readback (Cursor scan). Brian listens: no aloud timestamps/system notes — **PASS** (his “done”).

*Note:* Background review fork also ran at 12:34:33 (`result=none`); marker remained `2026-10-03T12:34:29-07:00` (feeds B.6).

### Part B.5 — Over-mention — PASS (2026-10-04)

Brian (verbatim): `done. nothing out of the ordinary to report`

No gratuitous timestamps / clock times / elapsed gaps / system metadata across ordinary Text+Voice turns (session continued into 2026-10-04; all user turns still stamped).

### Part B.6 — Background review fork — PASS (2026-10-03)

Forks observed: `12:33:27` (`result=skill`), `12:34:33` (`result=none`). No `time_context` / `time_marker_update` from either fork. Marker after brunch user turn stayed `2026-10-03T12:34:29-07:00` until the next Brian turn on 2026-10-04 — G-USER-ONLY live ✅.

### Part C — Checks — PASS

| Check | Result |
|---|---|
| `meta.last_interaction_at` time-only | current value ISO-8601 with offset; no gap wording ✅ |
| Memory files unchanged by this track | `USER.md` / `MEMORY.md` mtimes still 2026-10-02 15:23 (pre–FIX-B smoke); track does not write them ✅ |
| `zola_memory.log` no message text | smoke phrases absent ✅ |
| `gateway.message_timestamps` | unset ✅ |
| Every user turn stamped (session `…39a132`) | 19/19 have `[Time:]` in `api_content`; client `content` clean ✅ |

### Smoke verdict

**smoke test passed** (2026-10-04). Phase 7 smoke accepted (Brian + Claude, 2026-10-04); Claude confirmed FIX-B rekey ownership guard is in deployed `__init__.py`.

## Lore inputs (pre-closeout)

### R1 — Background review `result=skill` at 2026-10-03 12:33:27 (read-only; do not edit/delete)

| Field | Value |
|---|---|
| Agent log | `Background review complete … result=skill` at `2026-10-03 12:33:27,398` (thread `bg-review:20936`) |
| Tool | `skill_manage` completed `12:33:25,603` |
| Curator ledger | id `05c65874e5dd`, ts `2026-10-03T19:33:25.578569+00:00` (UTC = 12:33:25 PDT), actor `curator`, action **`patch`**, skill **`everyday-assistance`**, session `20261002_165941_39a132` |
| Path | `%LOCALAPPDATA%\hermes\profiles\zola\skills\communication\everyday-assistance\SKILL.md` |
| Before SHA-256 | `fa5fadc3acbe8353ebd2d65382e231912845b4e2b433511baaf93d03c164d116` (blob: `.curator_backups/blobs/fa5fadc3…`) |
| After SHA-256 | `d5f4195a74186527e4f7753be8e4185252f3365ed7bf9d0ced88617ca3c4a2be` (current file; mtime 2026-10-03 12:33:25) |

**Diff (sole change):** Procedure step 1 — before used live/stable lookup only; after also treats answers “already recorded in the conversation” and adds: *For a question about when a message was sent, use the message timestamp supplied in the conversation rather than performing a current-time lookup.*

**Personal / health content written?** **No.** The patch contains no mention of being sick, congestion, nasal/throat symptoms, brunch, family, or other personal/health details from the conversation. Brian decides disposition at the Phase 6 lore closeout (no edit/delete this track).

**Full after content** (current `SKILL.md`):

```markdown
---
name: everyday-assistance
description: Handle quick everyday questions directly and accurately.
version: 0.1.0
author: Brian, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [everyday, concise, factual, weather]
    related_skills: []
---

# Everyday Assistance

Answer small practical questions—time, weather, cooking, conversions, and quiet activity ideas—in a natural conversational voice. Favor the requested result over process commentary.

## When to Use

- The user asks a short, self-contained everyday question.
- The answer is a live fact, a simple conversion, a basic how-to, or a low-stakes recommendation.
- Do not use for consequential medical, legal, financial, or emergency guidance.

## Procedure

1. Identify whether the answer is live, stable, or already recorded in the conversation. For time, weather, and other current facts, use the appropriate live lookup; for calculations, use `terminal` or `execute_code`. For a question about when a message was sent, use the message timestamp supplied in the conversation rather than performing a current-time lookup. Completion: the source or calculation directly covers the requested value.
2. For a conditional practical question (for example, whether to drive if it rains), answer the condition directly. Check a forecast only when the user asks whether that condition is expected, or when it materially changes an immediate recommendation.
3. For a forecast, use the user's saved default location when no place is stated. Confirm that the provider's update and valid times cover the requested day; discard stale or internally inconsistent search snippets rather than treating them as a current forecast. State the location only if it helps prevent ambiguity.
3. For a location-specific recommendation, use the supplied city or saved location; if location is missing, ask one direct question. Use the `clarify` tool only when the user explicitly asks for it or when a structured choice genuinely helps.
4. When asked to pick a nearby option, choose one concrete place rather than presenting a list. Give its name, the single practical reason it fits the stated need, and a direct map or directions link when available.
5. When the user makes a casual observation rather than asking for a current fact, acknowledge it naturally without presenting an unverified local detail as confirmed.
6. Deliver the answer first in the smallest useful form. Add only the details that help the user act, such as cooking timing, precipitation chance, or a practical option.
7. If the user asks why a response was slow, state the known cause plainly and distinguish it from inference. Completion: do not imply certainty about latency the tools did not expose.

## Pitfalls

- Do not narrate tool use or add caveats to a straightforward answer unless they materially affect accuracy; extra process text makes quick exchanges feel slower.
- Preserve the user’s wording when it is clear, but silently resolve ordinary speech-to-text omissions when the intended everyday question is unambiguous.
- Give cooking directions as numbered, timed steps when timing determines the outcome; this is more usable than an explanatory paragraph.

## Verification

- The result answers the exact question in the first sentence or list item.
- Any current fact is grounded in a live source, and any conversion is tool-calculated.
- The response can be read aloud naturally without unnecessary setup.
```

### R2 — B.3 empty reply

B.3 empty reply = provider flake (`gpt-5.6-terra` / `openai-codex`, 3 retries + exhausted), out of track scope. Stamp + marker still succeeded.

### Optional — Brian's B.1 qualitative gap verdict

*(not supplied — placeholder left blank in the pre-closeout instruction.)*

## Phase 7-FIX-A — G1–G4 grounding (read-only; hermes `345cd2b0…`)

### Hotfix rejection (verbatim)

> Do NOT redeploy. Hotfix rejected (Brian + Claude) — root cause is right, fix is wrong.
> 1. Singleton across agents: register() runs per agent construct (incl. background review / other agents). Shared instance means a second agent's initialize() overwrites _conn (old conn leaked, lock entry never released) and any agent's shutdown() closes the shared conn — the live conversation then silently loses on_memory_write / on_turn_start file checks. Regresses Track 2.
> 2. _ensure_provider_conn is a second store-open path (skips initialize's run_file_check) and masks (1). Violates one authority. Remove it.
> Revert both changes… Then PHASE 7-FIX-A …

### G1 — Who constructs an agent and triggers `load_memory_provider` / `register()`?

| Kind | Constructs `AIAgent`? | `skip_memory` / memory load? | Overlaps main TUI in-process? |
|---|---|---|---|
| **Main TUI turn** | Yes — `_make_agent` `tui_gateway/server.py` L2342–2363; `skip_memory=ignore_rules` (normally False) | **Yes** — `agent_init._init_memory` L1267–1287 → `load_memory_provider` → `register()` → `initialize_all` | — |
| **Background review / `/btw` fork** | Yes — `background_review.build_cache_parity_fork` L932; kwargs `skip_memory=True` L881 | **No** external provider load | Concurrent with parent; `_persist_disabled=True` L944 so `pre_llm_call` collection is skipped (`turn_context.py` L670–671) |
| **Subagent** | Yes — `delegate_tool.py` L236–240 `skip_memory=True` | **No** | Concurrent; no memory register |
| **Title generation** | **No** — `title_generator.generate_title` uses `call_llm` only (L297), not `AIAgent` | N/A | N/A |
| **Cron** | Yes — `cron/scheduler.py` `_construct_cron_agent` L2186–2216 `skip_memory=False` L2212 `platform="cron"` | **Yes** — full load/register/initialize | Can share process with other Hermes surfaces; stomp risk on module globals / fallback hooks |
| **Compression** | No new agent — same agent; session boundary via `on_session_switch` / `commit_memory_session` | No new `register()` | Same agent |
| **Lazy skill load** | No new agent — `tools/skills_tool.py` L282–285 `load_memory_provider(namespace)` when skill namespace equals active memory provider | **`register()` only** — **no** `initialize_all` | **Yes** — runs in the live agent process; `_drop_fallback_hooks` + new provider + `_probe_llm` without opening `_conn` |

Authority for load path: `plugins/memory/__init__.py` `_load_provider_from_dir` L273–290 + `_ProviderCollector.collect` L307–317 (`_drop_fallback_hooks` then `register(self)`).

### G2 — `session_id` on `initialize` vs `pre_llm_call` (same main TUI agent)

| Site | Value |
|---|---|
| `initialize_all` | `session_id=agent.session_id` via `_memory_provider_init_kwargs` `agent_init.py` L1199–1200, L1286 |
| `pre_llm_call` kwargs | `session_id=agent.session_id` `turn_context.py` L674–676 |

**Same value** for a given agent while its `session_id` is unchanged. `ZolaMemoryProvider.initialize` today does **not** store `session_id` on the instance (`provider.py` L49–101).

**Session switch / new conversation:** `MemoryManager.on_session_switch` `memory_manager.py` L647–659 notifies providers; zola_memory only logs (`provider.py` `on_session_switch`). `initialize()` is **not** re-run. Agent’s `session_id` changes; next `pre_llm_call` carries the **new** id. Compression / `/new` use `commit_memory_session` + switch, not teardown (`run_agent.py` L868–873). Full teardown: `close()` → `shutdown_memory_provider` → `shutdown_all` (`run_agent.py` L854–865, L918–924); TUI teardown calls `agent.close()` (`session_lifecycle.py` L315–316).

### G3 — How many times does `_pre_llm_call_hook` run per user turn after N `register()` calls?

`invoke_hook` runs **every** callback in `_hooks[name]` (`plugins_dispatch.py` L172–205, loop L190).

For memory-provider fallback hooks (zola_memory has **no** `plugin.yaml` / not general-discovery-owned):

- Each `load_memory_provider` → `collect` **drops** prior fallback hooks for that source (`plugins_ledger.py` L186–189; `plugins/memory/__init__.py` L315–317), then `register_hook` adds one (`plugins_ledger.py` L191–200).
- Therefore after N memory `register()` calls: **one** live `pre_llm_call` callback (latest), **not** N stacked callbacks.
- That single callback is `_pre_llm_call_hook`, which reads module-global `_provider` at call time — so it targets whoever **last** called `register()`, which may be uninitialized (skills lazy-load) or another agent’s instance (cron).

`_persist_disabled` agents skip invoking `pre_llm_call` entirely (`turn_context.py` L670–671).

### G4 — Is `shutdown()` called per agent instance when that agent ends?

**Yes**, for agents that loaded a memory manager: `AIAgent.close()` → `shutdown_memory_provider` → `on_session_end` + `shutdown_all` → each provider’s `shutdown()` (`run_agent.py` L854–865, L918–924; `memory_manager.py` L782–786). Idempotent via `_memory_provider_shutdown`. Gateway/TUI session teardown calls `agent.close()` (`session_lifecycle.py` L315–316). Review forks set `_end_session_on_close=False` and `skip_memory=True` (no provider to shut down).

### Registry design vs G1–G4

Proposed: per-`register()` provider instance; `{session_id: provider}` on successful `initialize`, re-key in `on_session_switch`, remove in `shutdown`; hook `registry.get(kwargs['session_id'])`; never open store in hook; register hook once.

| Criterion | Verdict |
|---|---|
| G1 | **Works** if registry is keyed by session and hook never uses `_provider`. Cron + main TUI can coexist. Skills lazy-load (`register` without `initialize`) no longer poisons the hook. |
| G2 | **Works only if** provider stores `session_id` on `initialize` and **`on_session_switch` re-keys** the registry (initialize is not re-called on `/new` / compression). |
| G3 | **Change required:** bare “register hook once” **conflicts** with Hermes `_drop_fallback_hooks` before every memory `register()` — a once-guard that skips `register_hook` after a drop leaves **zero** hooks. **Correct approach:** keep re-`register_hook` each `register()` (Hermes already collapses to one callback), but the callback must resolve the provider via **session_id registry**, not `_provider`. |
| G4 | **Works** — `shutdown()` removes that session’s registry entry; must not close another session’s provider. |

**Overall:** registry design is sound with these amendments: (1) re-key on `on_session_switch`; (2) do **not** use a naive once-only hook guard — re-register after drop, resolve via registry; (3) optional: stop relying on `_provider` for the hook entirely; (4) registry dict needs a lock.

**Not implemented** (FIX-A is grounding only). Live profile still on broken Phase 6 deploy until FIX-B approved.

## Phase 1 notes

- `main` HEAD confirmed `7f5cd118fd52ab85de6cb942755cf869f7a42097`; porcelain empty.
- Branch `p6-time` created from that tip.
- Progress doc created on `p6-time`, uncommitted until closeout.
- `hermes-agent`: porcelain empty; HEAD `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`).
- Baselines: `zola_memory` **Ran 26 tests — OK**; `zola_tools` **Ran 44 tests — OK**.
- Scratch directory ensured: `C:\Users\test\Dev\zola-spikes\p6-time\`.
- No source implementation yet; live profile unread for write.

## Unit test summary

Phase 4 (2026-10-02):
- `zola_memory`: **Ran 41 tests — OK** (26 prior + 15 new time_context tests)
- `zola_tools`: **Ran 44 tests — OK**

Phase 4b (2026-10-02):
- `zola_memory`: **Ran 46 tests — OK** (+5: ZoneInfo fall-back/spring-forward × configured/system-local, capture_now raise)
- `zola_tools`: **Ran 44 tests — OK**

## Phase 4 notes

- Implemented `hermes-plugins/zola_memory/time_context.py` per approved contract:
  - `USER_TURN_PLATFORMS = frozenset({"tui"})`; `MEANINGFUL_GAP_MINUTES = 30`
  - Fixed English `DOW_NAMES` / `MONTH_NAMES` (not `strftime %a/%b`)
  - Calendar day/week relative buckets + singular forms (`1 minute ago`, `about an hour ago`, `a week ago`)
  - Stamp / gap shapes; block joined with `"\n"`; marker ISO-8601 with offset
  - G-ORDER hook: predicate → capture now → read → build → persist on success → return `{"context": block}`
- Wired: `log.py` events `time_context` / `time_marker_update`; `__init__.py` real `pre_llm_call` (keeps AUD-36 observer log)
- Nothing deployed; live profile untouched; `identity/SOUL.md` not yet edited (Phase 5/6)
- Hermes-agent still clean at `345cd2b0…`

## Phase 4b notes

- **BUG fixed:** gap absolute zone across DST. Removed `_zone_for_past`. Added `localize_marker()`:
  - `tz = get_active_timezone()` (same test-overridable seam as `capture_now` via `set_clock_for_tests(..., timezone=…)`)
  - `last_local = last.astimezone(tz) if tz is not None else last.astimezone()`
  - Never `last.astimezone(now.tzinfo)` (fixed-offset path rendered wrong hour)
  - `last_local` used for gap `format_stamp_body` and `format_relative` calendar-day math
- **Fail-closed hook:** entire `handle_pre_llm_call` body (including `capture_now`) in try/except → `time_context ok=false`, return `None`, marker unchanged; never raises into Hermes
- **Live `config.yaml` report (read-only):** `$HERMES_HOME` = `C:\Users\test\AppData\Local\hermes\profiles\zola` — **no `timezone:` key** (and no `HERMES_TIMEZONE` match). Unchanged.

## Phase 4b approval (Brian + Claude, verbatim, 2026-10-02)

> Phase 4b approved (Brian + Claude). Claude independently verified real-zoneinfo DST cases on both configured-zone and system-local paths: gap labels correct (PDT/PST), calendar-day wording correct. Live config timezone: unset — accepted; system-local path is the supported path. No config change.
> proceed to phase 5

### Effective rulings (recorded)

1. Phase 4b DST localize + fail-closed hook accepted.
2. Live `timezone:` remains unset; system-local path is the supported production path.
3. No config change this track.

## Phase 5 — Proposed live changes (awaiting Brian's approval)

Nothing deployed yet. Phase 6 applies exactly what is approved here.

### 1. Redeploy file list (live Track 2 → repo `p6-time`)

Live path: `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\`  
Repo path: `hermes-plugins/zola_memory/`  
Exclude: `tests/`, `__pycache__/`, no `plugin.yaml`.

| File | Status | Live SHA-256 (Track 2) | Repo SHA-256 (deploy) |
|---|---|---|---|
| `time_context.py` | **NEW** | *(absent)* | `d9309043804e14f392f8be93ef4c8e5090eb2950828fbeeb34c454f380eaa71c` |
| `__init__.py` | **CHANGED** | `d66e363274d6160d73fe6c06a6c2a23b3c54dc3a7cda34be2f3af1d8f4f1e6da` | `8411fa71f6120f55b20133224232df44f082e0713897eb411e6f0da02965654e` |
| `log.py` | **CHANGED** | `c596c90bbdd8ef10d329fa76ce543e9b45602364b438a107b3081a014d1b9eac` | `af6d9645c8eef2a176c67a64d0b7134b563149cdc30768ee1d43d39d198f6229` |
| `provider.py` | SAME | `3a98fa9ca5084b73c0568a41f1b3b88fe8c671c170de2d570def3f47ae17de48` | same |
| `store.py` | SAME | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` | same |
| `fact_index.py` | SAME | `b6dd9710fe776b21fa963878929acfdd134888384c772746ba687c33bf23cb24` | same |
| `forget.py` | SAME | `1e50246501f9274190426961d4526ca84ebeff7b3a580b9f63f6c514a5663d7c` | same |
| `llm_access.py` | SAME | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | same |

Only the three **NEW/CHANGED** files must differ after deploy; SAME files may be left untouched or re-copied (byte-identical).

### 2. Exact `SOUL.md` diff

Insert in **## How I talk out loud**, after the “times and casual numbers…” paragraph ending in `precise.`, before `When I need something from him…`.

Approved text (verbatim):

> I can see when each message reaches me and how long it's been since we last talked. Those time notes are added by the system, not typed by Brian. I use that the way a person would — "yesterday," "a couple of hours ago," "it's been a few days" — and I never read timestamps or system notes out loud.

Proposed unified diff (`identity/SOUL.md` / live `SOUL.md`; line endings: live CRLF, mirror LF — content match ignoring endings):

```diff
@@
 When we're talking, I don't structure my answer like a document, with bullet points, bold, headers
 or tables, unless he asks for that structure. I say things in a natural order instead. I say times
 and casual numbers the way a person would ("about twenty minutes", "half past four"), but I keep
 exact details like addresses, phone numbers, measurements, commands and identifiers precise.
+I can see when each message reaches me and how long it's been since we last talked. Those time notes
+are added by the system, not typed by Brian. I use that the way a person would — "yesterday," "a
+couple of hours ago," "it's been a few days" — and I never read timestamps or system notes out loud.
 When I need something from him, I ask one clear question and give him room to answer. I don't turn a
 conversation into an interview, and I don't read out a list of options unless there's a real, short
 set to choose from. When I've said what's useful, I stop. I don't tack on offers to explain more or
 questions to keep things going. If he wants to go deeper, he'll say so, and I'll go with him.
```

Current SOUL live vs identity: equal ignoring CRLF (live `b508cd0a…`, identity `8dbef43e…` — endings only).

### 3. Config keys

**None.** `timezone:` stays unset (system-local supported path). `gateway.message_timestamps` stays off / unset. `memory.provider: zola_memory` unchanged. `config.yaml` hash today: `7ba2e676a04ff92047c8d711fcb022be8a532b11baac6f74b08986744e704570`.

### 4. Live gap test method

**Proposed (preferred):** Brian takes a natural break of **≥ 30 minutes** before Phase 7 Part B step 1, so a real gap line appears without touching the store.

**Alternative (only if Brian prefers):** with explicit approval, back up `zola_memory.db` then set `meta.last_interaction_at` to an earlier ISO timestamp once (operational metadata, not memory). Progress doc records which method was used.

### 5. Rollback

1. Redeploy Track 2 file set from hashes on record (STORE Phase 6 / live column above): restore `__init__.py` + `log.py` to Track 2 hashes; **remove** `time_context.py`.
2. Restore live `SOUL.md` from Phase 6 backup.
3. Relaunch client.
4. `config.yaml` / `approvals.*` / `zola_tools` / store DB: unchanged by this track's forward path (DB may retain `last_interaction_at`; harmless with Track 2 code that ignores it).

Stop. Brian approves or edits 1–5 in his own words.

## Phase 5 approval (Brian + Claude, verbatim, 2026-10-02)

> Phase 5 approved as proposed (Brian + Claude). Claude verified repo hashes time_context.py d9309043, __init__.py 8411fa71, log.py af6d9645 match the deploy table.
> 1–3, 5: approved verbatim.
> 4: natural ≥30-min break; do not edit the DB.
> Add to Phase 7 observations: first turn after deploy (empty last_interaction_at) shows stamp only, no gap line — confirm via time_context log gap_line=false.
> proceed to phase 6

### Effective rulings (recorded)

1. Redeploy list, SOUL diff, no config, rollback — approved as proposed.
2. Gap test: natural ≥30-min break only; never edit `last_interaction_at` in the DB.
3. Phase 7 must observe first post-deploy turn: stamp only + `gap_line=false`.

## Phase 6 notes

- Backed up SOUL, Track 2 `plugins/zola_memory/`, and DB via `sqlite3.backup` (hashes above).
- Redeployed all 8 plugin files; hashes MATCH repo. Applied SOUL + mirrored to `identity/SOUL.md`.
- Relaunched Zola.Client (pid **22300**); serve python pids **9848** / **16784**.
- **Live serve load once:** `2026-10-02 16:01:07` — `Memory provider 'zola_memory' registered (0 tools)` then `activated` (single pair in the live serve process). Hook registration present in deployed `__init__.py` (`pre_llm_call` → `handle_pre_llm_call`).
- **First user turn / `time_context ok=true`:** not yet logged. External `prompt.submit` via WebSocket rejected HTTP 403; SendKeys to the client window did not reach the composer. Marker remains empty — preserves Phase 7 first-turn `gap_line=false` observation. Confirm `time_context ok=true` (+ `gap_line=false`) on the first Cursor/Brian user turn in Phase 7.
- G6 PASS (tools identical; prompt differs only by approved SOUL text + allowlisted `Conversation started:`).
- `config.yaml` / `zola_tools` / hermes-agent unchanged.

## Phase 6 approval (Brian + Claude, verbatim, 2026-10-02)

> Phase 6 approved (Brian + Claude). Claude verified repo identity/SOUL.md 9f4fe469 contains the approved text (joined to the preceding paragraph rather than a new one — accepted as-is, no redeploy).
> Phase 7 rule (hard): Cursor must not inject, simulate, or send any turn into the client or gateway by any channel. Every user turn is typed by Brian. The earlier WS inject attempt (403) was out of scope — confirm nothing reached the session and last_interaction_at is still empty before starting.
> proceed to phase 7

### Effective rulings (recorded)

1. Phase 6 deploy/SOUL/G6 accepted; SOUL paragraph join accepted (no redeploy).
2. **Hard rule:** Cursor never injects/simulates/sends turns; Brian types every user turn.
3. Preflight required and done: inject did not reach session; marker empty.

## Phase 8 — Closeout

### 8a Verify

| Check | Result |
|---|---|
| `zola_memory` unit tests | **53 OK** |
| `zola_tools` unit tests | **44 OK** |
| `dotnet build … -r win-x64` | **PASS** (0 warnings / 0 errors) |
| `hermes-agent` | clean at `345cd2b057a452236de401d3534b8502a7465e8d` |

### 8c Deploy + SOUL re-verify (post–FIX-B)

| File | Repo = Live SHA-256 |
|---|---|
| `__init__.py` | `33f589199006e47484c90291d1fc908e945a52f0fc5e8dbc4804b9b5e354bce5` |
| `provider.py` | `eeedf6cecb730e70c23629a57cc0a26e4e0943d0632d7faf947381bbff94069d` |
| `time_context.py` | `d9309043804e14f392f8be93ef4c8e5090eb2950828fbeeb34c454f380eaa71c` |
| `log.py` | `af6d9645c8eef2a176c67a64d0b7134b563149cdc30768ee1d43d39d198f6229` |
| `store.py` / `fact_index.py` / `forget.py` / `llm_access.py` | unchanged Track 2 hashes (MATCH) |
| `SOUL.md` live + `identity/SOUL.md` | `9f4fe469b4bac7a014bf245ebb226a0a178aa29179ea551c11a3bee126f0a2fc` (byte match) |

### Exit criteria verification (PHASE6_BUILD_PLAN.md Track 3)

Amended by prompt v1.1 (Brian-approved): “first message” scoped to this conversation; over-mention is qualitative judgment.

| Criterion | Verdict | Evidence |
|---|---|---|
| Unit tests: stamp format | ✅ | `TestTimeContextStamp` |
| Unit tests: gap 29/30/31 | ✅ | `test_gap_threshold_29_30_31` |
| Unit tests: first-run | ✅ | `test_first_run_no_gap_line` |
| Unit tests: ordering / fail leaves marker | ✅ | `test_ordering_construction_failure_leaves_marker`, `test_capture_now_raising_leaves_marker` |
| Unit tests: DST / midnight | ✅ | `TestTimeContextZoneInfoDst`, stamp midnight/year-boundary |
| CURSOR-RUN: stamp on every turn incl. trivial hi | ✅ | session `…39a132`: 19/19 user msgs have `[Time:]` in `api_content` |
| CURSOR-RUN: `_timestamp_line` / system prompt untouched by mechanism | ✅ | T6; G6 offline prompt diff = SOUL time paragraph only |
| CURSOR-RUN: `gateway.message_timestamps` off | ✅ | unset in live `config.yaml` |
| HUMAN: gap awareness after ≥30 min | ✅ | B.1 technical PASS (`gap_minutes=1144`); qualitative B.1 verdict optional/blank |
| HUMAN: first-message time in this conversation (prompt deviation) | ✅ | B.2: “You sent it yesterday at 5:22 PM.” matches stamp |
| HUMAN: Voice never reads stamp aloud (≥5 turns) | ✅ | B.4: 6 spoken turns; no stamp/system-note readout |
| Over-mention qualitative (prompt deviation) | ✅ | B.5 Brian: “nothing out of the ordinary to report” |
| `last_interaction_at` time only | ✅ | ISO-8601 with offset; no gap wording |
| `hermes-agent` clean; no client source changes | ✅ | hermes clean; no `windows-client/**` source edits this track |

All Track 3 criteria met: **YES**. Unit tests: **PASS**.

### Closeout SHAs

*(filled as commits land)*

- Implementation commit (8f): `3fb1369df023e2a44a31cc9c857ff6a60450ae66`
- Docs record implementation SHA (8g): *(this commit)*
- Merge SHA on main (8i): *(pending)*
- Docs record merge SHA (8j): *(pending)*
