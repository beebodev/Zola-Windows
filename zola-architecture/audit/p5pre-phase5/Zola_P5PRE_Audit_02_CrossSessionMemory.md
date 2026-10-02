# P5PRE Audit 02 — Cross-session memory (S42)

**Audit ID:** P5PRE
**Scope:** S42 — a fact told in one Hermes session does not reach another
**Sources:** Hermes `345cd2b…` (`v2026.9.14`); live profile `%LOCALAPPDATA%\hermes\profiles\zola\` (read-only, 2026-10-01); Windows client session RPCs at `6494aca…`
**Labels against:** C4, C6, C8, S14, P4, P1-MEMORY. Android entity store / SessionBrief are not scored (`G-NO-CROSS-SCOPE`).

No entry text is quoted. Counts, tags, sizes, and tool-call counts only.

---

## Finding summary (this document)

| ID | Label | Severity | File | Summary |
|---|---|---|---|---|
| P5PRE-AUD-05 | [MATCH] | — | `tools/memory_tool.py` `get_memory_dir`; live `config.yaml` | The live store is the profile's `MEMORY.md` / `USER.md`. Limits are 4400 / 2750. `memory.provider` is unset, so the built-in store is the one in use (C4). |
| P5PRE-AUD-06 | [MATCH] | — | live `memories/` | Both files are under the limit. A new `add` would succeed today. No `.bak` drift snapshots. |
| P5PRE-AUD-07 | [RISK] | HIGH | `tools/memory_tool.py` `MEMORY_SCHEMA`; `agent/turn_finalizer.py` | A durable write happens only when some agent calls the `memory` tool. The tool text tells the model to save almost nothing. Across 93 sessions the tool has 2 result rows. |
| P5PRE-AUD-08 | [RISK] | LOW | `tools/memory_tool_store.py` `format_for_system_prompt`; `agent/agent_init.py` `_init_memory` | The system-prompt block is frozen at `load_from_disk()`. `add` / `replace` / `remove` update disk and the live lists, and leave the snapshot unchanged. |
| P5PRE-AUD-09 | [MATCH] | — | `tui_gateway/server.py` `_make_agent` / `_start_agent_build`; `ChatSocket.BeginNewSessionAsync` | A new client session builds a new `AIAgent` on its first prompt, which calls `load_from_disk()` again. A fact already on disk is in that new snapshot. |
| P5PRE-AUD-10 | [MATCH] | — | `tools/session_search_tool.py`; `state.db` | `session_search` searches `messages_fts`. It has been called. It is not the injection path for `MEMORY.md`. |
| P5PRE-AUD-11 | [MATCH] | — | `plugins/memory/__init__.py` | A user provider loads from `$HERMES_HOME/plugins/<name>/` without editing `hermes-agent`. The zola profile has no `plugins` directory. `memory.provider` is empty. |
| P5PRE-AUD-12 | [GAP] | LOW | live `SOUL.md`; `memories/*.md` | The `[tag]` convention is not in the live `SOUL.md`. None of the 13 entries starts with a `[tag]`. |

---

## 1. Effective config

Profile `config.yaml` `memory:` is only:

```yaml
memory:
  memory_char_limit: 4400
  user_char_limit: 2750
```

Hermes deep-merges that over `hermes_cli/config_defaults.py` L1215–1228. Effective values:

| Key | Effective | Source |
|---|---|---|
| `memory.memory_enabled` | `true` | default L1216 |
| `memory.user_profile_enabled` | `true` | default L1217 |
| `memory.write_approval` | `false` | default L1221 |
| `memory.memory_char_limit` | `4400` | profile |
| `memory.user_char_limit` | `2750` | profile |
| `memory.nudge_interval` | `10` | default L1225 |
| `memory.provider` | `""` (built-in only) | default L1228 |

There is no `platform_toolsets`, `toolsets`, or `agent.disabled_toolsets` key in the profile. The serve child cwd is the Hermes checkout (`HermesProcessManager.cs` L500). Coding-posture toolset collapse runs only when `agent.coding_context` is `focus` (`agent/coding_context.py` `toolset_selection` L319–324). That key is absent, so the session keeps the CLI platform toolset.

`memory` and `session_search` are both in `_HERMES_CORE_TOOLS` (`toolsets.py` L24–25), which `hermes-cli` bundles. Live proof they are reachable: `state.db` `messages.tool_name` counts are `memory` 2 and `session_search` 4 (1637 messages, 93 sessions). `tool_calls` text matches: `memory` 2, `session_search` 7.

`AUD-05 [MATCH]` with C4.

---

## 2. Store state

| File | Entries | Chars (`§`-join, the budget `MemoryStore._char_count` uses) | Limit | Tags | Other files |
|---|---|---|---|---|---|
| `MEMORY.md` | 1 | 234 | 4400 | none | `MEMORY.md.lock` (0 bytes) |
| `USER.md` | 12 | 1938 | 2750 | none | `USER.md.lock` (0 bytes) |

No `.bak` files in `memories/`. `add` refuses only when the new entry would pass the limit (`memory_tool_store.py` `add` L248–253). Both files have room. A new `add` would succeed today on either target.

`AUD-06 [MATCH]`. The budget is not why a fact would be missing.

`state.db` is 7,503,872 bytes, schema version 30. Tables include `sessions`, `messages`, `messages_fts` (FTS5), and `system_prompts`. `sessions.system_prompt` is NULL on all 93 rows; the body is stored by hash in `system_prompts` (`hermes_state_sessions.py` `update_system_prompt` L617–624). 31 prompt bodies. 23 contain the header `USER PROFILE (who the user is)`. 0 contain `MEMORY (your personal notes)`. An empty target renders `""` and is omitted (`_render_block` L382–383), so those 31 bodies were stored while `MEMORY.md` had no entries. The one current `MEMORY.md` entry is newer than those stored prompts, or those sessions never rebuilt. Which of those two is **UNVERIFIED** until L2 writes a probe and a new session stores a prompt.

---

## 3. Write path

There is no automatic extractor on the built-in store. `MemoryStore.add` / `replace` / `remove` run only from `memory_tool` (`tools/memory_tool.py` L172 and the registry handler L364).

The tool description the model sees (`MEMORY_SCHEMA` L264–286) says to save only facts that apply to every session, to put task procedures in a skill, and to skip task progress and temporary state ("use session_search for those"). An explicit "please remember" is the kind of fact the text allows. It does not require the model to call the tool.

A second path can also call that same tool. Every `memory.nudge_interval` user turns (10), `_tick_memory_nudge` (`agent/turn_context.py` L627–635) asks `turn_finalizer.py` L613–623 to spawn a background review fork whose toolset includes `memory` (`agent/background_review.py` L1035). That fork may call the tool. It is not a guaranteed write, and it does not run on the built-in provider's `sync_turn` (there is no built-in provider object when `memory.provider` is empty — `_init_memory` L1267–1272 creates `MemoryManager` only for a non-empty provider).

`AUD-07 [RISK]`. Two `memory` tool-result rows in the whole profile is the live shape of this. L2's first question is whether the probe turn calls `memory` at all. If it does not, the fact never reaches disk, and no snapshot or session design will surface it.

---

## 4. Read path and snapshot lifecycle

`load_from_disk()` (`memory_tool_store.py` L112–141) reads both files into the live lists and copies the rendered block into `_system_prompt_snapshot`.

It is called from:

- `agent/agent_init.py` `_init_memory` L1259–1265, once per `AIAgent`, during construction.
- `agent/system_prompt.py` `invalidate_system_prompt` L695–696, which the docstring says runs after context compression.

`format_for_system_prompt` (L363–366) returns that snapshot, not the live lists:

```363:366:C:\Users\test\Dev\hermes-agent\tools\memory_tool_store.py
    def format_for_system_prompt(self, target: str) -> Optional[str]:
        """Frozen load-time snapshot (NOT live state — mid-session writes don't touch
        it, preserving the prefix cache); None if empty."""
        return self._system_prompt_snapshot.get(target, "") or None
```

`_mutate` (L220–235), which `add`, `replace`, `remove`, and `apply_batch` all use, writes the file and updates the live list. It does not assign `_system_prompt_snapshot`. After a successful write the three views are:

| View | After `add` / `replace` / `remove` |
|---|---|
| Disk (`MEMORY.md` / `USER.md`) | Updated |
| Live lists (`memory_entries` / `user_entries`) | Updated |
| `_system_prompt_snapshot` | Unchanged until the next `load_from_disk()` |

The class docstring (L68–70) states the reason: one `MemoryStore` per `AIAgent`, snapshot frozen for prefix-cache stability. Changing it would rebuild the system-prompt prefix on the next turn and miss the provider prompt cache. That cost is stated in the code; it is not measured here.

`_memory_parts` (`agent/system_prompt.py` L460–468) appends those frozen blocks to the volatile tier of the system prompt. `build_system_prompt` caches the result on the agent (L667–669) until compression invalidates it.

### Who builds the agent

`tui_gateway/server.py` `session.create` (L318–335) stores a runtime session with `"agent": None`. `_start_agent_build` (L1077–1119) builds once, on the first prompt, via `_make_agent` → `AIAgent(...)` → `_init_memory` → `load_from_disk()`.

The Windows client does not reuse that runtime session for a new conversation. `ChatSocket.BeginNewSessionAsync` (L118–121) opens a new `/api/ws` and calls `session.create`. `ResumeStoredAsync` (L124–130) calls `session.resume`, which the client comment says returns a new runtime id. C6: the client wraps Hermes's `sessions` row; it does not keep one agent for every row.

### Can a fact written in A miss B?

| Case | Does the snapshot mechanism hide a fact that is already on disk? |
|---|---|
| Later turns of session A (same `AIAgent`) | **Yes.** Disk and live lists change. The prompt block does not, until compression calls `invalidate_system_prompt`. |
| Session B created after the write, same `hermes serve` process | **No.** B's first prompt constructs a new agent and `load_from_disk()` reads the files. |
| Any runtime session whose agent was already built before the write | **Yes**, for that agent's remaining life. |
| After a serve restart | **No**, for the same reason as a new agent: every session builds again and loads disk. |

`AUD-08 [RISK]` is the same-agent freeze. `AUD-09 [MATCH]` is the new-session reload. K3's "frozen snapshot" lead is confirmed for the agent that wrote, and it does not by itself explain a **new** session missing a fact that reached disk. If L2 writes successfully and a new session still misses the fact, that contradicts AUD-09 and needs the stored prompt check below before any other design. If L2 does not write, AUD-07 is the cause and AUD-08 never gets a chance.

Same-session recall (L2 A3) cannot prove the snapshot was injected. The fact is in that session's own transcript. A wrong answer there means the failure is not cross-session.

Read-only check for what B was injected: `sessions.system_prompt_hash` joins `system_prompts.prompt` (`update_system_prompt` L617–624; also `agent/conversation_loop.py` L643). L2 can ask whether the probe string occurs in the new session's stored prompt and print only yes/no. Nothing new has to be enabled.

---

## 5. Session-switch hooks

`MemoryManager.on_session_switch`, `commit_session_boundary_async`, and `on_session_end` (`agent/memory_manager.py` L610–658) fan out to registered providers. With `memory.provider` empty, `_init_memory` leaves `_memory_manager` as `None` (L1268–1290). Those hooks do not run, and they would not reload `MemoryStore` if they did: the built-in file store is not a `MemoryProvider` in that list.

The built-in reload points remain `load_from_disk()` at agent construction and `invalidate_system_prompt()` after compression. A client session switch does not call either of those on the old agent. The new session's new agent loads disk for itself (AUD-09).

---

## 6. `session_search`

`session_search` (`tools/session_search_tool.py` L508–552) searches conversation history in `state.db` with FTS5 (`messages_fts` exists). The description says it is for "what did we do about X", and that results are actual DB messages. It is in the core toolset and has been called (4 `tool_name` rows, 7 `tool_calls` matches).

It is not on the path that injects `MEMORY.md`. Built-in injection is the frozen system-prompt block (AUD-08). External prefetch, which would be a per-turn `<memory-context>` message (`agent/turn_context.py` `compose_user_api_content` L80–94 and `_memory_turn_start_and_prefetch` L762–782), runs only when `_memory_manager` is set. It is not set.

`AUD-10 [MATCH]`. Not a `[RISK]`: normal cross-session memory does not depend on reading another session's transcript. An explicit "what did we decide last week" search is the tool's own job. L2 still records, at every recall step, whether `session_search` ran. A correct answer that came from it is transcript search, not memory recall.

---

## 7. External provider loading without editing `hermes-agent`

The module docstring of `plugins/memory/__init__.py` L1–6 is confirmed:

- Bundled providers live in `plugins/memory/<name>/`.
- User providers live in `$HERMES_HOME/plugins/<name>/` (`plugins/plugin_loader.py` `user_plugins_dir` L28–33). The directory must already exist; the function returns `None` otherwise. The zola profile has no `plugins` directory.
- Project `./.hermes/plugins/<name>/` is opt-in via `HERMES_ENABLE_PROJECT_PLUGINS`.
- Bundled names win: `_iter_provider_dirs` yields bundled first and first-seen wins (L92–93).
- One provider is activated by `memory.provider`.

`_is_memory_provider_dir` (L62–69): the child must contain `__init__.py`, and the first 8192 characters of that file must contain `register_memory_provider` or `MemoryProvider`.

The built-in file store stays up beside an external provider. `_init_memory` L1236–1265 builds `MemoryStore` whenever memory is not skipped. L1267 says the plugin is "one at a time, alongside built-in".

Per turn, only if a provider is loaded:

| Hook | Where | Thread | Timeout |
|---|---|---|---|
| `on_turn_start` then `prefetch_all` | `turn_context.py` L762–782, before the tool loop | External prefetch runs on a daemon thread and the caller joins it (`memory_manager.py` L418–427) | `external_prefetch_timeout` default `_EXTERNAL_PREFETCH_TIMEOUT_S = 8.0` (L32, L290–299) |
| `queue_prefetch_all` | `run_agent.py` L904, after a turn | Background worker (`memory_manager.py` L463–472) | none on the queue itself |
| `sync_all` → `sync_turn` | `turn_finalizer.py` L603–607 | Same background worker, not the conversation thread (L480–486) | none stated; the comment says a provider may block for minutes, which is why it is off-thread |

`build_memory_context_block` (L266–279) wraps prefetch text in `<memory-context>`. `compose_user_api_content` appends that to the **current user message** (`api_content`), not to the system prompt. The provider's `system_prompt_block()` is a separate static block inside `_memory_parts` (L473–484).

`AUD-11 [MATCH]` with the plugin docstring. The profile does not use it.

---

## 8. Decision mapping (no recommendation)

What L2 must show, before any shape is "the" fix:

| L2 pattern | What it supports |
|---|---|
| Write FAIL (no `memory` tool row, files unchanged) | AUD-07. The fact never entered the store. Snapshot and providers are not the miss. |
| Write PASS, same-session control PASS, new session FAIL, restart FAIL | The bytes are on disk and a new agent still did not inject them. Contradicts AUD-09. Check the stored prompt for the probe string before any other theory. |
| Write PASS, new session FAIL, restart PASS | Would point at same-process agent reuse. AUD-09 says a new `session.create` should not do that. This pattern would refute AUD-09 for the client's actual RPC. |
| Write PASS, new session PASS | The store already crosses sessions. S42's symptom is the model not calling `memory`, or the same-agent snapshot (AUD-08), not a missing store. |
| Recall PASS but the only tool was `session_search` | Transcript search. Not memory. |

| Shape | C4 | S14 | P4 | C8 | Edits `hermes-agent`? | Fixes the observed cause only if L2 shows |
|---|---|---|---|---|---|---|
| **(i)** built-in fix: prompt / save behavior | Fits. The live store stays `MEMORY.md` / `USER.md`. | Does not build S14. Does not contradict it. | Fits. No provider. | Fits. Forget stays on `MEMORY.md`. | No, if the change is profile `SOUL.md` or the existing tool. | Write FAIL. |
| **(i)** built-in fix: refresh `_system_prompt_snapshot` on write | Fits the store. Changes the prefix-cache rule the class states. | Same. | Fits. | Fits. | **Yes.** The snapshot lives in `hermes-agent`. P2-D10 / P3-D16 do not allow that edit. A new session already reloads (AUD-09), so this only changes same-agent turns. | Write PASS and the miss is a later turn of the **same** agent, not a new session. |
| **(ii)** Zola-owned local provider in the profile `plugins` folder | Tension. C4 says the two files are the single live store for v1. The file store stays on beside the provider (AUD-11), so this is a second store. | Overlaps the deferred target if the provider becomes the real source of truth. | **Tension.** P4 says no external memory provider, to close the third-party retention risk. A local Zola-owned plugin is still `memory.provider`. This audit does not revise P4. | Tension if forget deletes only `MEMORY.md` and the provider keeps its own copy. | No, if it is a profile plugin that passes `_is_memory_provider_dir`. | Write FAIL is not fixed by a provider the model also has to call, unless the provider's `sync_turn` writes without a tool call. New-session FAIL with a successful file write is not fixed by a second store unless that store is what B reads. |
| **(iii)** S14 structured store projecting into `MEMORY.md` | Fits the long-term half of C4: the structured store is the source of truth and `MEMORY.md` stays what Hermes injects. Not the v1 store. | This is S14. It is deferred until there is usage data. | Tension if the projector is registered as `memory.provider` (same as ii). No tension if it only writes the two files and leaves `provider` empty. | Fits if forget updates the structured store and the projected `MEMORY.md` together. A forget that touches only the file leaves the structured copy. | No, if it writes the files the built-in store already loads. Yes, if it needs the snapshot to refresh inside an already-built agent. | Write FAIL, and the projector writes the file without waiting for the model. A new session then loads it (AUD-09). |

---

## LEAD disposition (K3)

| Lead | Result |
|---|---|
| The store is profile-scoped and designed to cross sessions | **Confirmed.** `get_memory_dir()` → `<HERMES_HOME>/memories`. |
| A write never happens | **Open.** The only write path is the `memory` tool, and it has run twice in 93 sessions. L2 decides. |
| A write is blocked by the budget | **Refuted for today.** 234/4400 and 1938/2750. |
| The snapshot is stale | **Confirmed for the writing agent. Refuted as the reason a later new session would miss a fact already on disk.** |
| The serve process reuses one agent across client sessions | **Refuted for `session.create`.** A new runtime session builds a new agent on first prompt. |
| The memory tool or toolset is disabled | **Refuted.** Both are in the core toolset and have run. |
