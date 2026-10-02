# P6PRE Audit 03 — Episodes and Session Boundaries (Windows path)

**Audit:** P6PRE · Hermes `345cd2b0…` · Zola client read-only  
**Labels against:** S14, S42 (episodes remainder), S28, C6, P5-D06.

---

## Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-17 | [RISK] | HIGH | `agent_init.py` L1267–1293; `ChatSocket.cs`; `session_lifecycle.py` | MemoryProvider `on_session_end` does not run with empty provider; client never calls `session.close` (LEAD-4). |
| P6PRE-AUD-18 | [GAP] | HIGH | schema + holographic | No first-class episode store; session ≠ episode. |
| P6PRE-AUD-19 | [MATCH] | — | `session_search_tool.py`; MEMORY_CONVENTIONS | P5-D06 bridge unchanged: search only when asked; results are not memory. |
| P6PRE-AUD-20 | [MATCH] | — | `hermes_state_common.py` sessions/messages | Per-session title exists; **no** durable session-recap column. |
| P6PRE-AUD-21 | [RISK] | MEDIUM | `turn_finalizer.py` L625–639 vs `memory_provider.py` L156–157 | Plugin observer `on_session_end` fires **per turn** (no transcript) — easy to confuse with provider boundary hook. |

---

## Hook taxonomy

| Hook | Kind | When |
|------|------|------|
| Plugin `on_session_end` | Observer | **Every turn** + finalize — IDs/flags only |
| MemoryProvider `on_session_end(messages)` | Provider | Real session boundaries via `commit_memory_session` / shutdown |
| `on_session_switch` | Provider | Mid-process id change (compression, CLI `/new`, …) |
| `on_pre_compress` | Provider | Before compression summary |
| `shutdown` | Provider | `shutdown_memory_provider` |

With `memory.provider: ""` all MemoryProvider hooks are no-ops.

---

## 1. Conversation end/change map (Windows)

| Event | Client / server | MP hooks (if provider set) | Defaults today |
|-------|-----------------|----------------------------|----------------|
| New session | `session.create`; old WS Abort; park → ~20s `ws_orphan_reap` | Finalize may `commit_memory_session` + `close` | Plugin finalize only; no MP |
| Resume | `session.resume`; supersede prior runtime | Same for abandoned runtime | Same |
| Window / app exit | Abort WS; owned serve **tree-killed** | Finalize often **skipped** | Same |
| Serve stop (graceful) | `tui_shutdown` atexit | Would finalize | Rare on Zola path |
| Serve crash / kill | Startup orphan sweep later | Missed in-process | Same |
| Sleep / lock | Presence/voice only | **None** | Session stays open |
| Compression | Continues conversation | `on_pre_compress` + `on_session_switch` | No MP |
| Explicit `session.close` | Exists server-side | Clean teardown | **Client never calls** |

Serve launch: `python -m hermes_cli.main -p zola serve --isolated …` with `HERMES_HOME` profile; `HERMES_DESKTOP` removed → source typically `"tui"` (`HermesProcessManager.cs` L196–213).

**LEAD-4: Confirmed** for MemoryProvider `on_session_end` on the Windows client path (P6PRE-AUD-17).

---

## 2. What hooks receive; LLM possible?

| Moment | Receives | LLM? |
|--------|----------|------|
| Per-turn plugin `on_session_end` | session ids / completed flags — **no messages** | No |
| Finalize `commit_memory_session` | Transcript history if agent+history | Provider-dependent |
| `on_pre_compress` | Messages about to compress | Provider-dependent; compressor itself always LLMs |
| Compression `on_session_switch` | new id, parent, `reason=compression` | Usually no |

---

## 3. “Conversation over” for Brian

| Candidate | Reliability |
|-----------|-------------|
| Idle / lock / sleep | **Unreliable** — session stays open |
| Next `session.create` / resume | **Strong client signal**; old runtime ends ~20s later |
| Compression | **Wrong** — continues conversation |
| Explicit close | **Never used** by client |
| `sessions.ended_at` | Durable when finalize/sweep runs; missing after hard kill until startup sweep |

**Plain answer:** no synchronous, reliable “this conversation is over” signal that also flushes memory on the Windows path with defaults.

---

## 4. `state.db` (schema from code; counts not queried)

**sessions:** id, source, timestamps (`started_at`/`ended_at`/`last_activity_at` as Unix REAL), `title`/`title_source`, `parent_session_id`, `end_reason`, model/prompt hashes, counters, … — **no summary/recap column**.

**messages:** id, session_id, role, content, `timestamp REAL`, tool fields, `api_content`, compression flags, …

TZ: epoch floats; `session_search` formats with local `datetime.fromtimestamp` (no TZ label in string).

---

## 5. `session_search` / P5-D06

Returns session `when` (from `started_at`), title, snippets, message timestamps — JSON to the model. FTS over transcripts. **P5-D06 unchanged:** only when asked; not saved as memory.

**P6PRE-AUD-19 [MATCH].**

---

## 6. Per-session summary writers today

| Mechanism | Active with defaults? |
|-----------|------------------------|
| Compression handoff in transcript | When compresses |
| `title_generator` (short title) | Aux path — not a recap |
| CLI `session_recap` | Not WinUI |
| MP `on_session_end` extraction | **No** (empty provider) |
| Durable recap column | **None** |

**P6PRE-AUD-20 [MATCH]** — no competing durable episode writer today (compression handoff is in-transcript only).

---

## 7. Session ≠ episode ≠ durable fact

| Concept | Hermes today |
|---------|----------------|
| Session recap | Local/CLI or compression text in transcript |
| Episode/event | **No** first-class object |
| Durable fact | MEMORY.md / USER.md via `memory` tool |

Hermes does **not** require episode=session 1:1. Identifiers for multi-episode / cross-session designs: session id, message id + timestamp, `parent_session_id` (compression lineage), FTS search — not episode IDs.

**P6PRE-AUD-18 [GAP]** for S14/S42 episodes remainder.
