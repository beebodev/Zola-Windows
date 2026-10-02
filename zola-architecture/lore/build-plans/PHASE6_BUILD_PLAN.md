# ZW Phase 6 Build Plan
## Memory She Lives With: Episodes, Time, Forget, and Math Without Code

**Base branch:** `main`
**Base SHA:** `92dc707ac047d2808b9f1848bb0e31f96689065a` (`main` tip after the P6PRE closeout).
Record the actual tip at plan commit. Each track records the actual HEAD it branches from.
**Audit:** P6PRE, merged at `92dc707ac047d2808b9f1848bb0e31f96689065a` (audit commit
`84f14d83db8efd7e495acbfa078a8da66b415683`). Documents in `zola-architecture/audit/p6pre-phase6/`.
38 findings: 8 HIGH, 15 MEDIUM, 4 LOW, 11 MATCH. All six LEADs confirmed.
**Theme:** New capability, built locally and without editing Hermes. This phase:
- builds a Zola-owned local memory provider beside her existing memory files (`S14`);
- gives her episodes: what happened, when, and with whom, written by a background summarizer
  (`S14`, the `S42` episodes remainder);
- gives her ambient time: when each message happened, and how long since Brian last talked to her
  (`S43`);
- makes "forget" reach every copy the memory system holds;
- revises P4 to "local only";
- stops approval cards for simple arithmetic without loosening the approval gate (`S35`, the
  arithmetic case).

This phase does **not**:
- edit Hermes (`hermes-agent` stays read-only at `v2026.9.14` / `345cd2b0…`);
- install anything;
- move fact authority off `USER.md` / `MEMORY.md` (P6-D01);
- give her any new way to *save* memory (P6-D02);
- redact `state.db` transcripts (P5-D10 stands);
- change approval behavior (P4-D07, P4-D27 stand);
- touch `S44`, `S40`, `S38`, `S36`, `S28`, H4, or tiers/decay.

---

## Phase 6 Overview

| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 (`P6-CALC`) | Math without code | New profile plugin `zola_tools` with one side-effect-free `calculate` tool; `SOUL.md` arithmetic line; first use of the repo→profile plugin deployment pattern | Small-Medium |
| 2 (`P6-STORE`) | Memory store foundation | All Phase 6 grounding checks first; then `zola_memory` provider skeleton, SQLite schema, fact index with notify mirror + file check, fact-level forget recognition and cascade, activation on the live profile | Medium-Large |
| 3 (`P6-TIME`) | Ambient time | `pre_llm_call` timestamp on every user message; `last_interaction_at` marker and cross-session gap; `SOUL.md` time line | Small-Medium |
| 4 (`P6-FORGET`) | Forget reaches everything | Erase-only `forget_memory` tool; cascade over episodes, pending turns and entity links; clarification hold; consolidation invalidation; failed-cascade retry and read suppression; `SOUL.md` forget lines | Medium |
| 5 (`P6-EPISODES`) | Episodes | Pending-turn queue, background summarizer, episode store with entities and fact references, episode retrieval with dates and relative age | Large |

**Sequencing rule:** strictly **1 → 2 → 3 → 4 → 5**. Each track merges and passes its smoke test
before the next begins.
- Track 1 goes first because it is small and independent, and it proves the plugin
  deployment pattern (repo source → live profile under P4-D25) before the memory provider uses it.
- Track 2 runs every grounding check before it builds anything. If a check fails, the phase stops
  at a G-ARCH STOP for a decision. It does not adapt.
- Track 4 comes **before** Track 5 on purpose. No episode is ever written before a forget can
  reach it (fail closed). Track 4 builds and tests the episode cascade against synthetic episode
  rows.

**Build command (client tracks, none expected):** `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`.
**Test command (plugin tracks):** `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m unittest discover -s hermes-plugins\<plugin>\tests -t hermes-plugins\<plugin>`.
- Tests use the standard library only (`unittest`, `sqlite3`, `tempfile`).
- They run against temporary directories, never the live profile, and use synthetic data only.
- This is the project's first automated test suite. The plugins are pure Python with clear
  contracts, so their behavior can be tested without a live model.

Smoke tests on the live client remain the acceptance criteria. Cursor does every
non-interactive step. Live steps run one at a time (G-LIVE). The external dictation tool must be
confirmed off before any voice step.

---

## Grounding summary (established by P6PRE; cite, do not re-derive)

**Memory layer (Audit 01)**
- A provider in `$HERMES_HOME/plugins/<name>/` loads through `memory.provider` without editing
  `hermes-agent` (AUD-01). The built-in files stay active beside it (AUD-02).
- Prefetch output lands in the **user turn** inside a `<memory-context>` fence. It is skipped on
  trivial prompts (AUD-03). The external prefetch timeout is a hard-coded 8 s (AUD-04).
- Successful built-in `add`/`replace`/`remove` reach `on_memory_write` **after** the file write,
  with `old_text` and provenance. The call is synchronous, and provider exceptions are swallowed
  (AUD-05; Audit 01 §5).
- Today `memory.provider` is empty, so there is no MemoryManager and no hooks run (AUD-06).
- Bypass writers reach the files without notify: the background-review fork (`skip_memory`),
  `/memory approve`, and journey/`learning_mutations` (AUD-06/07).
- The memory-provider plugin context supports `register_hook` (fallback hooks)
  (`plugins/memory/__init__.py`, `_ProviderCollector`). Whether it exposes `ctx.llm` is
  unverified.

**Holographic (Audit 02, P-1, P-2)**
- Reference only (P6-D03).
- Warm retrieval is about 2 ms at 2,000 records. Insert cost grows with size (8 → 27 → 61 ms).
  HRR accuracy degrades near 2,000 at dim 1024.
- Its `on_memory_write` mirrors only `add` (AUD-08/27).

**Episodes and sessions (Audit 03)**
- No reliable "conversation over" moment exists on Windows:
  - the client never calls `session.close`;
  - an abandoned runtime is reaped about 20 s after the next `session.create`;
  - app exit force-kills `serve` (AUD-17).
- The plugin `on_session_end` fires on every turn, without a transcript, and is not a session
  boundary (AUD-21).
- There is no episode store anywhere (AUD-18).
- P-3 (live hook proof) was skipped for lack of a safe credential path (AUD-36). Hook firing is
  proven in this phase on the live profile, in Track 2.

**Time (Audit 04)**
- She sees date and timezone, frozen at session start (AUD-22). Messages carry no per-message time
  (AUD-23). `session_search` "when" strings have no timezone (AUD-24).
- `pre_llm_call` can inject context into the user turn without breaking the cached system prefix
  (AUD-25).

**Forget (Audit 05)**
- Forget today covers the files only, and `state.db` stays (AUD-26, P5-D10). No candidate store
  separates superseded from forgotten (AUD-28).
- Data is local and inside the backup scope (AUD-29), and plaintext at rest (AUD-30).

**Approvals (Audit 06, P-4)**
- Arithmetic cards come from `execute_code` (pattern `execute_code`, whole script) and from
  terminal `python -c` (pattern `script execution via -e/-c flag`, from `_execution_flag_findings`
  in `approval_detection.py`). One `execute_code` run can raise two cards (AUD-31/37/38).
- Ordinary terminal commands raise no card (S16 holds).
- Plugin tools have no built-in approval gate (AUD-34).

**LLM access for plugins**
- `agent/plugin_llm.py`: host-owned `complete` / `complete_structured` with JSON-schema
  validation. The host owns routing, auth and timeouts; the plugin never sees tokens.
- It is backed by `auxiliary_client.call_llm`, the auxiliary path, which can resolve to a
  different provider or model from the main conversation.

---

## Decisions Resolved in This Build Plan

Summaries below. The full locked text, with Brian's verdicts in his own words, is in **Appendix A**
(verbatim from the decisions log). Where a summary and Appendix A differ, Appendix A governs. The
track sections cite these IDs.

**P6-D01 — Two kinds of memory, one authority each.**
- `USER.md` / `MEMORY.md` stay the authority for current durable facts, written only through the
  memory tool.
- A Zola-owned local store holds (a) a **structured fact index** and (b) **episodes**.
  - The fact index is derived from the files: stable IDs and timestamps, with entity links
    inferred at read time. It is kept in step by notify plus a file check. The current index is
    always rebuildable from the files. It may keep lifecycle history observed through writes,
    subject to P6-D06.
  - The store is the sole authority for episodes.
- Episodes reference facts and never create or change them.
- Retrieval is built for facts and episodes. In Phase 6 it surfaces only episodes and temporal
  context, because every current fact is already injected.
- Moving fact authority to the store is a future decision, made on measured evidence. The fill
  percentage is reported for review only.

**P6-D02 — Memory invariants.**
1. Facts have one author: Zola, through the memory tool.
2. Episodes have one author: the episode writer.
3. Episodes never create or change facts.
4. Entities organize knowledge; they never create it.
5. Timestamps record only what is known. Lifecycle times are stamped automatically. Event times
   are stored only when Brian states them or an authoritative system event establishes them.
   Validity periods are never inferred.
6. Correction preserves history; forget erases content. Tombstones are content-free.
7. Retrieval never becomes persistence.
8. Raw conversation is evidence; P5-D06 stands (search past conversations only when Brian asks).

**P6-D03 — A Zola-owned local memory provider (amended by P6-D06).**
- `zola_memory`, a profile plugin, loaded through `memory.provider`.
- Source lives at `hermes-plugins/zola_memory/` and is deployed under P4-D25.
- One profile-local SQLite database using built-in `sqlite3` + full-text search.
- No installs, no NumPy, no network, no HRR.
- Model-facing tools: none, except P6-D06's one erase-only forget operation.
- Retrieval runs synchronously on the **current** turn, comfortably inside the 8 s prefetch
  timeout. It never depends on `on_session_end`.

**P6-D04 — Episodes are written by a background summarizer inside the provider.**
- It uses the host-owned plugin model call. Implementation stops if that path is unavailable.
- Each completed exchange goes into a temporary pending-turn queue, with session/turn identity,
  order and source times.
- Consolidation runs at a quiet gap, at startup, before compression, or at a session switch or end
  if one fires. No single trigger is relied on.
- It never reads `state.db`.
- Output is zero or more episodes. Each carries source range, entities, fact references and
  temporal metadata. `event_time` stays unknown unless stated or system-established.
- Commit happens only if the source pending turns are unchanged since consolidation began. Commit
  and pending-turn removal happen in one transaction. Retry is bounded with backoff and logged;
  failed turns stay pending.

**P6-D05 — Ambient, system-stamped time.**
- Every user message carries a short local timestamp, added through `pre_llm_call` and kept in
  history.
- At the start of a conversation, or after a meaningful gap, she also gets the time since Brian's
  last interaction across conversations.
- Episodes show their date and relative age, computed at read time and never stored.
- `SOUL.md` tells her never to read stamps aloud.
- This is the single mechanism; `gateway.message_timestamps` stays off.

**P6-D06 — Forget erases every copy the memory system controls.**
- Recognition fails closed:
  - `remove` is a forget;
  - `replace` is a correction, unless the turn clearly asks to forget, in which case it is erased;
  - a disappearance without notify is a forget;
  - heuristics may only make forgetting stricter.
- The cascade covers index rows, search entries, history, entity links, matching pending turns
  (including the forget request turn), and whole episodes that reference or contain the content.
- It is transactional. A forget invalidates in-flight consolidation.
- The memory-tool path reports before the cascade runs, so the file check retries the cascade and
  retrieval suppresses references until it commits.
- An ambiguous target triggers clarification. Pending turns stay held during clarification and
  are discarded if it is never resolved.
- One erase-only forget tool handles episode-only memory.
- Transcripts stay unredacted, and she says so naturally.
- Tombstones keep only IDs, kind, time and counts.

**P6-D07 — P4 revised: memory is stored and retrieved locally; no third-party memory service.**
- All persistent memory lives in the local profile.
- No cloud or third-party memory provider.
- Episode consolidation may resend pending conversation through the host-owned model call, **inside
  the same model-provider trust boundary already approved for conversation**. That is model
  processing, not off-device memory.
- Memory is unencrypted at rest (H4 deferred) and inside the backup scope.

**P6-D08 — Math without code; approvals unchanged.**
- `zola_tools` registers one side-effect-free `calculate` tool. It uses a bounded arithmetic
  grammar and a fixed allowlist, never `eval`, code, shell, imports, files or network. It has
  input, complexity and result limits, and it fails closed on unsupported input.
- `SOUL.md`: arithmetic directly when she's confident; `calculate` when exactness matters; never
  code or terminal just to calculate.
- `approvals.mode: manual`, P4-D07 and P4-D27 stand.

### Cross-cutting

**Live-profile edits** (`SOUL.md`, `config.yaml`, plugin deployment) follow P4-D25:
1. Back up first.
2. Propose the exact text, diff or file hashes at a STOP.
3. Apply only after developer approval.
4. Mirror: `SOUL.md` into `identity/`; plugin source is canonical in the repo, and the live copy
   is verified against it by per-file SHA-256.

**Plugin deployment** (Tracks 1, 2, 3, 4, 5):
- The repo `hermes-plugins/<name>/` is the only source.
- Deploy copies it to `%LOCALAPPDATA%\hermes\profiles\zola\plugins\<name>\`, excluding `tests/`
  and `__pycache__/`.
- After deploy, every deployed file's SHA-256 must match its repo counterpart, and the table is
  recorded in the progress doc.
- Rollback restores the backed-up previous copy, or removes the folder if this is the first
  deploy. Any `config.yaml` key it added is reverted from backup.

**Privacy (all tracks):**
- Cursor may read memory files, the provider database and logs locally.
- Repo documents carry only counts, tags, IDs, hashes, timings and synthetic test text.
- Test fixtures are synthetic: fictional people, cars and projects.

**Brian's verdicts are recorded in his own words.**

**Logging:**
- Each plugin writes to its own log, `%LOCALAPPDATA%\hermes\profiles\zola\logs\zola_memory.log` /
  `zola_tools.log`.
- One line per event, with named-constant event prefixes.
- No memory content in logs: IDs, counts and timings only.

---

## Track 1 — Math Without Code (`P6-CALC`)

### Problem
Simple arithmetic raises approval cards because she runs code to do it:
- `execute_code` (whole-script gate);
- or terminal `python -c` (exec-flag pattern).

One `execute_code` run can raise two cards (AUD-31/37/38; P-4 turns 1–3). The gate is correct:
Hermes cannot tell harmless code from harmful code. She has no code-free way to compute.

### Files to read
- `hermes-agent` (read-only):
  - `plugins.py` / `hermes_cli/plugin_loader.py` (user plugin discovery, `register_tool`, how a
    plugin tool joins the active toolsets);
  - `tools/registry.py`;
  - `tools/plugin_guard.py`;
  - `tools/approval.py` (`check_execute_code_guard`, ~L1148–1215);
  - `tools/approval_detection.py` (`_execution_flag_findings`, ~L901–917).
- Live profile (read-only until the STOP): `config.yaml` (`plugins.*`, toolsets), `SOUL.md`.
- `zola-architecture/audit/p6pre-phase6/Zola_P6PRE_Audit_06_Approvals.md`,
  `Zola_P6PRE_Audit_07_LiveProbes.md` (P-4).

### Changes

**Phase 2 grounding (read-only), each item answered with file and lines:**
1. How a user plugin in `$HERMES_HOME/plugins/<name>/` registers a model-facing tool, and whether
   that tool is visible to Zola's `tui` platform session without a `config.yaml` change. If a
   change is needed, report the exact key at the STOP.
2. Whether `plugin_guard.py` or any other host policy gates, wraps or rejects plugin tools.
3. Confirmation that registering a plugin tool cannot change any existing approval behavior.

If any answer contradicts P6-D08, stop G-ARCH.

**`hermes-plugins/zola_tools/` (new):**
- `__init__.py`: `register(ctx)` registers one tool, `calculate`, with a JSON schema: a single
  string `expression`. The tool description says what it supports and that it can't run code.
- `calculator.py`: the evaluator.
  - Parse with `ast.parse(expression, mode="eval")`.
  - Walk the tree against a fixed allowlist:
    - numeric constants;
    - unary `+`/`-`;
    - binary `+ - * / // % **`;
    - parentheses (implicit);
    - a named function allowlist: `abs`, `round`, `min`, `max`, `sqrt`, `floor`, `ceil`;
    - a percent helper for the "N% of M" form, if the grammar needs it (the Phase 3 STOP shows
      the exact accepted grammar).
  - **No** names other than the allowlisted functions; no attributes, subscripts, comprehensions,
    lambdas, strings, calls outside the allowlist, `eval`, `exec`, `compile` on anything but the
    parsed tree, imports, or I/O.
  - Limits, as named constants:
    - maximum input length (for example 200 characters);
    - maximum node count;
    - maximum exponent (for example |exp| ≤ 1000, and the base magnitude bounded before `**`);
    - maximum result digits;
    - a wall-clock guard.
  - Use `decimal.Decimal` for `+ - * /` on money-like inputs, so `1347.12 + 466.72 + 565` gives
    `2378.84` exactly. Document the rounding rule.
  - Any unsupported construct or exceeded limit returns a structured error,
    `{"ok": false, "error": "<reason>"}`, and never falls back to anything.
- `tests/test_calculator.py` (stdlib `unittest`):
  - the three P-4 prompts as expressions;
  - precedence;
  - division by zero;
  - each disallowed construct (`__import__('os')`, attribute access, names, lambda, f-strings,
    huge powers, deep nesting, oversize input) fails closed;
  - the Decimal money case;
  - the wall-clock guard.
- `plugin.yaml` as required by the loader.

**Live `SOUL.md`:**
- A line in "How I talk out loud" or a short "Doing math" note, proposed at the STOP.
- Starting draft (Brian decides the final wording):

> When Brian asks me to work out numbers, I do simple arithmetic in my head. When precision
> matters — money, percentages, several steps — I use my calculator. I never run code or
> terminal commands just to do math. If my calculator can't handle something, I say so or work
> through it with him instead.

**Deploy** per the cross-cutting plugin rule. If grounding found a required `config.yaml` key, add
it with the comment tag `# P6-CALC: enable zola_tools calculator — P6-D08`.

**`identity/SOUL.md`:** mirrors the live file.

No client source changes. No `approvals.*` changes.

### Exit criteria
- [ ] Unit tests pass (test command above), covering every case listed.
- [ ] Deployed file hashes match the repo. `identity/SOUL.md` matches the live file, apart from
      line endings.
- [ ] HUMAN-RUN, Text mode, the three P-4 prompts: correct answers (391; 36; 2378.84) and
      **zero approval cards**. `agent.log` shows `calculate` or no tool at all, and no
      `execute_code` or terminal call.
- [ ] HUMAN-RUN control: a request that genuinely needs machine-changing authority still raises
      the existing card. Brian denies it. For example, "make a folder called p6calc-test on my
      desktop", with the exact control agreed at the STOP.
- [ ] CURSOR-RUN: `calculate("__import__('os').system('echo x')")` and an oversize power return
      `ok:false`, with no process spawned (unit test plus the plugin log).
- [ ] `approvals.*` unchanged (config hash comparison). `hermes-agent` clean at the pin.

**Complexity:** Small-Medium
**Primary risk:** The plugin tool isn't visible on the `tui` platform toolset without a config
change, or she keeps choosing `execute_code` out of habit. The first is settled at grounding. For
the second, if the SOUL line doesn't win, report the per-prompt tool choices. Don't add an approval
exception.

---

## Track 2 — Memory Store Foundation (`P6-STORE`)

### Problem
There is no structured store, and today there is no MemoryManager at all (AUD-06). Several
mechanisms the later tracks depend on are unproven on this pin and path:
- `ctx.llm` for a memory provider;
- the auxiliary model's trust boundary;
- `sync_turn` and `pre_llm_call` on `tui_gateway`;
- live hook firing (AUD-36).

Forget does not reach anything beyond the files (AUD-26/27).

### Files to read
- `hermes-agent` (read-only):
  - `agent/memory_provider.py`, `agent/memory_manager.py`, `plugins/memory/__init__.py`
    (`_ProviderCollector`, ~L156–200), `agent/agent_init.py` (`_init_memory`, ~L1240–1295);
  - `agent/inline_tool_executors.py` (~L114–133), `agent/turn_context.py` (prefetch ~L762–790,
    `pre_llm_call` ~L663–714);
  - `agent/plugin_llm.py`, `agent/auxiliary_client.py` (`call_llm` routing, provider/model
    resolution);
  - `tools/memory_tool.py`, `tools/memory_tool_store.py`;
  - `tui_gateway/session_lifecycle.py`, `session_reaper.py`, `prompt_turn.py` (sync and hook
    delivery on the Windows path).
- Live profile (read-only until the STOP): `config.yaml` (`memory.*`, `auxiliary.*` or equivalent,
  `plugins.*`), `memories/` (counts only).
- `zola-architecture/audit/p6pre-phase6/` Audits 01, 02, 03, 05, and the synthesis.

### Changes

**Phase 2: grounding (read-only, plus scratch-only harnesses).** Every item gets a
`[CONFIRMED]` / `[REFUTED]` answer with file and lines. A REFUTED item that a decision depends on
is a G-ARCH STOP.
- **G1, `ctx.llm`:** a provider registered through `_ProviderCollector` can reach the host-owned
  `PluginLlm` (`complete_structured`). What trust flags (`plugins.entries.<id>.llm.*`) does it
  need? Without it, P6-D04 cannot be built: STOP.
- **G2, trust boundary (P6-D07):** record **side by side**:
  - the main conversation's provider and model;
  - the provider and model that `plugin_llm` → `auxiliary_client.call_llm` resolves to under Zola's
    effective config;
  - the identifiers and config keys each one comes from.

  **PASS:** the same provider (the same trust boundary). A different model at the same provider
  passes under P6-D07. **FAIL:** a different provider. That is never accepted silently: report the
  exact config that would pin it to the conversation provider, for a STOP. Never change auth.
- **G3, `sync_turn` on `tui_gateway`:** fires once per completed turn with user and assistant
  content and the `session_id`. Record what message identity is available.
- **G4, `pre_llm_call`:** a hook registered from a memory-provider plugin fires for **every** user
  turn, including trivial ones ("hi", "ok"). Its injected context is kept in the replayed history
  (`api_content`) on later turns. Track 3 depends on this.
- **G5, `on_turn_start`:** receives the current user message (P6-D06 replace-intent check).
- **G6, activation side effects:** turning on a provider with no system-prompt block and no tools
  changes nothing else: the built-in memory tool, the tool list and the system prompt are
  unchanged.
- **G7, `on_memory_write` metadata mode:** the provider signature receives `metadata` (keyword
  mode), including `old_text`.
- **G8, full-text search:** FTS5 is available in the Hermes venv's `sqlite3`.
- **G9, backup scope:** `hermes backup` covers the database path chosen below.

**Phase 3: STOP.** Report G1–G9, the proposed schema, and the exact `config.yaml` diff.

**`hermes-plugins/zola_memory/` (new).** Only the parts Track 2 uses are active; later tracks
fill in the rest.
- `__init__.py`: `register(ctx)` registers the provider and keeps a handle for later hooks.
- `provider.py`: `ZolaMemoryProvider(MemoryProvider)`.
  - `name = "zola_memory"`.
  - `is_available()` checks FTS5 (fails closed if it's missing).
  - `initialize()` opens or creates the database at `$HERMES_HOME/zola_memory/zola_memory.db` (WAL
    mode), runs migrations, then runs the **file check** (below).
  - `system_prompt_block()` returns `""`. No competing prompt text (LEAD-5 lesson).
  - `get_tool_schemas()` returns `[]`. Track 4 adds the forget tool.
  - `prefetch()` returns `""` in this track (nothing to surface yet; P6-D01).
  - All background work uses `spawn_context_thread` / `ctx_bound`.
- `store.py`: the schema, migrations, and every write behind one connection with
  `BEGIN IMMEDIATE` transactions.
  - `meta(key, value)`: schema version, `last_interaction_at` (Track 3), last file-check hash.
  - `facts(id, target, text, tag, state, learned_at, updated_at, superseded_at, source)`, plus an
    FTS5 table over `text`.
    - `state ∈ {active, superseded}`. "Forgotten" is a tombstone, not a state.
    - `source ∈ {notify, file_check}`.
  - `fact_history(id, fact_id, text, superseded_at)`: only for corrections (P6-D06).
  - `entities(id, name, kind, created_at)` and `entity_aliases(entity_id, alias)`, for episode
    links (Track 5). Facts link to entities **at read time** by name/alias match, not stored
    (P6-D01; project principle).
  - `episodes`, `episode_entities`, `episode_fact_refs`, `pending_turns`: created now, empty until
    Tracks 4–5 (schema reviewed once).
  - `tombstones(id, record_kind, erased_at, counts_json)`: no content (P6-D02 rule 6).
- `fact_index.py`:
  - **Notify mirror (`on_memory_write`, keyword metadata):**
    - `add` creates an active fact.
    - `replace` with `old_text` either supersedes it (keeping a history row) or erases it, decided
      by the forget-intent check.
    - `remove` is a forget (cascade).
  - **File check:** parse `MEMORY.md` / `USER.md` with the same `§` delimiter rules as
    `memory_tool_store.py`.
    - A new line becomes an active fact with `source=file_check`.
    - An active fact whose text is missing from the files and has no completed cascade is a
      forget (cascade). Fail closed: no history.
    - It runs at `initialize()` and at `on_turn_start`, cheaply: skipped when the files' combined
      SHA-256 matches `meta`.
- `forget.py` (fact level in this track; Track 4 extends it):
  - `erase_fact(fact_id, reason)` deletes the fact row, its FTS row and its history rows, then
    writes a tombstone, all in one transaction.
  - **Forget-intent check** for `replace`: conservative phrase rules over the current turn's user
    message (from `on_turn_start`), for example "forget", "don't remember", "don't keep", "delete",
    "erase", "stop remembering". It can only escalate a correction to a forget, never the reverse.
    The phrase list is a named constant, unit-tested, and recorded at the STOP.
- `log.py`: event prefixes as named constants. IDs, counts and ms only.
- `tests/`: unit tests over a temp `HERMES_HOME`:
  - schema;
  - add / replace / remove mirroring;
  - forget-intent escalation (including "don't keep my address anymore");
  - file-check detection of a bypass add and a bypass removal;
  - the transactional erase (simulated failure rolls back fully);
  - a tombstone contains no content (byte scan for the synthetic text);
  - the FTS5-missing fail-closed path.

**Live activation (after STOP approval, P4-D25):**
- Back up `config.yaml` and `memories/`, recording hashes.
- Deploy `zola_memory` with the per-file hash table.
- Set `memory.provider: zola_memory`, with the comment `# P6-STORE: Zola-owned local memory
  provider — P6-D03`, plus any G1 trust flags approved at the STOP.
- Restart `serve` through the client.

**`identity/MEMORY_CONVENTIONS.md`:** a short section on the two kinds of memory, the invariants
(P6-D01/D02) and the forget rule, in prose with one note citing P6-D01–D07. `SOUL.md` is not
changed in this track.

**Rollback (pre-agreed):** if the smoke test shows any regression in ordinary memory behavior,
restore `config.yaml` from backup (`memory.provider: ""`) and report. The database stays in place
for diagnosis; nothing reads it with the provider off.

### Exit criteria
- [ ] G1–G9 answered with evidence, and Brian's STOP verdicts recorded.
- [ ] Unit tests pass.
- [ ] Deployed hashes match the repo. `memory.provider: zola_memory` is set, and no other config
      change was made beyond those approved.
- [ ] CURSOR-RUN, live hook proof (closes AUD-36): `zola_memory.log` shows `initialize`,
      `on_turn_start`, `sync_turn` and `on_memory_write` firing on the live Windows path, with
      timestamps. It also records whether `on_session_end` fires at the ~20 s orphan reap after a
      new session (observed, not relied on).
- [ ] HUMAN-RUN, blind, synthetic facts, Text mode:
  - a lasting statement she saves appears as an active fact (Cursor checks IDs and counts);
  - a correction she makes with `replace` leaves one active fact and one history row;
  - "forget that…" leads to `remove`, the fact row is gone, and a content-free tombstone exists;
  - "don't keep my [synthetic detail] anymore", if she uses `replace`, is escalated to erasure,
    with no history row.
- [ ] CURSOR-RUN bypass check: a hand-made **scratch-copy** scenario in the unit tests stands in
      for the bypass writers. No hand edits to live memory files. On the live profile, the file
      check reports `no drift` on startup.
- [ ] Regression: Phase 5 memory behavior unchanged. She still saves lasting facts unprompted
      (2 of 2 synthetic), and recall in a fresh session works (2 of 2). The system prompt and tool
      list match the pre-activation baseline (G6).
- [ ] Prefetch adds nothing to the user turn (no `<memory-context>` fence on any turn).
- [ ] Synthetic test facts are removed through Zola afterwards. The semantic restore check against
      the backup passes. Matching tombstones exist (counts only).
- [ ] `hermes-agent` clean at the pin. No client source changes.

**Complexity:** Medium-Large
**Primary risk:** activation changes something besides the provider: a tool, prompt text, or the
behavior of the built-in memory tool (G6). Or the notify mirror and the file check disagree, and
the file check erases a fact that was only reformatted (for example whitespace normalization by
`memory_tool_store.py`). Mitigation:
- the file-check text comparison uses the same normalization as the store;
- unit tests cover whitespace and `§` edge cases;
- the smoke test confirms `no drift` after a real save.

---

## Track 3 — Ambient Time (`P6-TIME`)

### Problem
She cannot tell "5 minutes ago" from "yesterday" (S43; AUD-22/23). A resumed conversation gives
her no sense of the gap. The BR1 answer had no timing.

### Files to read
- `hermes-agent` (read-only): `agent/turn_context.py` (`pre_llm_call` ~L663–714; how hook context
  is placed and persisted), `agent/system_prompt.py` (`_timestamp_line`), `hermes_time.py`.
- `hermes-plugins/zola_memory/` (Track 2 source). Live `SOUL.md`.
- `zola-architecture/audit/p6pre-phase6/Zola_P6PRE_Audit_04_Time.md`; Track 2 progress doc (G4,
  G5).

### Changes

**`hermes-plugins/zola_memory/time_context.py` (new):**
- `build_turn_time_context(now, last_interaction_at)` returns the stamp text, plus a gap line
  when `now − last ≥ MEANINGFUL_GAP_MINUTES`.
  - `MEANINGFUL_GAP_MINUTES = 30` is a named constant and tunable (P6-D05).
  - The stamp format is short and local, with the timezone abbreviation, for example
    `[Fri Oct 2, 12:31 PM PDT]`.
  - The gap line looks like `Brian's last message to me was 2 days ago (Wed Sep 30, 9:14 PM PDT).`
  - Relative-time wording rules are a single function, reused by Track 5.
- Registered as the `pre_llm_call` hook from `register(ctx)`. **Order is fixed (Brian, P6-D05):**
  1. read `last_interaction_at` from `meta`;
  2. build the context;
  3. return it for injection;
  4. only after the context is built successfully, update `last_interaction_at = now`.

  A failure before step 4 leaves the previous value intact. The gap itself is never stored.
- First run, with no previous value: stamp only, no gap line.
- Times come from the system clock in local time. `hermes_time` is used if it is the established
  local-time helper.

**Live `SOUL.md`:**
- A line in "How I talk out loud", proposed at the STOP.
- Starting draft:

> I can see when each message reaches me and how long it's been since we last talked. I use
> that the way a person would — "yesterday," "a couple of hours ago," "it's been a few days" —
> and I never read timestamps or system notes out loud.

**`identity/SOUL.md`:** mirrors the live file. Redeploy `zola_memory` per the plugin rule.

### Exit criteria
- [ ] Unit tests:
  - stamp format;
  - gap threshold boundary (29/30/31 min);
  - first-run behavior;
  - ordering (a simulated failure before the update leaves `last_interaction_at` unchanged);
  - DST and midnight boundaries.
- [ ] CURSOR-RUN:
  - the stamp is present on every user turn in the replayed history, including a trivial "hi"
    (G4 proven live);
  - no change to the cached system-prompt prefix (`_timestamp_line` untouched);
  - `gateway.message_timestamps` still off.
- [ ] HUMAN-RUN, Text then Voice:
  1. After at least 30 minutes away, a new conversation opens with "hey". She shows natural awareness
     of the gap (Brian's words), or at least doesn't contradict it.
  2. "When did I send my first message today?" is answered correctly from the stamps.
  3. In Voice mode she never reads a stamp aloud (Brian listens across 5 or more turns).
- [ ] Over-mention check: across 10 ordinary turns she doesn't mention clock times unprompted more
      than once (Brian's judgment, recorded).
- [ ] `last_interaction_at` holds a time only (Cursor reads the `meta` row).
- [ ] `hermes-agent` clean. No client source changes.

**Complexity:** Small-Medium
**Primary risk:** the hook's context isn't kept in the replayed history (G4 partly refuted), so
earlier messages lose their stamps. If G4 comes back REFUTED, stop at Track 2's STOP. The fallback
needs its own decision (for example, including a compact rolling list of the last N message times
in the current stamp). Don't adapt silently.

---

## Track 4 — Forget Reaches Everything (`P6-FORGET`)

### Problem
After Track 2, forget reaches fact rows. Phase 6 adds episodes, pending turns and entity links,
and each is a new place a forgotten thing could survive (P6-D06). Episode-only memory has no
forget path at all, because nothing reaches the provider when there's no file fact to remove. This
track makes forget complete **before** any episode exists.

### Files to read
- `hermes-plugins/zola_memory/` (Track 2 and 3 source and tests).
- `hermes-agent` (read-only): `agent/memory_provider.py` (`get_tool_schemas`,
  `handle_tool_call`), `agent/memory_manager.py` (tool routing, ~L561–600).
- Live `SOUL.md`, `identity/MEMORY_CONVENTIONS.md`.
- `zola-architecture/audit/p6pre-phase6/Zola_P6PRE_Audit_05_ForgetPrivacy.md`.

### Changes

**`forget.py` (extended):**
- **Cascade** `forget_cascade(targets)` runs in one `BEGIN IMMEDIATE` transaction and erases:
  - fact rows + FTS + history;
  - episodes that reference an erased fact ID (`episode_fact_refs`);
  - episodes whose text or FTS matches the forgotten content's distinctive terms;
  - `episode_entities` rows of erased episodes;
  - entities left with no remaining links;
  - `pending_turns` that match the content, **plus the forget-request turn**.

  It then writes tombstones with structured counts (`fact_rows`, `episode_rows`, `pending_rows`,
  `index_rows`). The whole cascade commits or rolls back. Episodes are deleted whole, never
  rewritten.
- **Consolidation invalidation:** a `consolidation_generation` counter in `meta` is incremented by
  every forget. A consolidation (Track 5) records the generation and its pending-turn IDs at start
  and may commit only if both are unchanged. Track 5 uses this API; Track 4 tests it with a
  synthetic consolidator.
- **Retry and read suppression for the memory-tool path:**
  - A `remove` whose cascade throws is recorded in `meta.pending_erasures` (IDs only). It is
    retried at every file check until it commits.
  - Until then, retrieval (Track 5) excludes any record referencing an ID in `pending_erasures`.
  - Repeated failure is logged with counts.
- **Clarification hold:**
  - `forget_memory` with `confirm=false` returns candidate groups and sets `meta.forget_hold`
    (session ID + pending-turn IDs from the request turn onward). Held turns are skipped by
    consolidation.
  - The hold is released when the forget executes (`confirm=true`). It expires after
    `FORGET_HOLD_MAX_MINUTES = 30` or at a session switch; on expiry, held pending turns are
    **discarded** (fail closed).

**Erase-only tool, `forget_memory` (the provider's only tool; P6-D03 as amended):**
- Schema: `description` (string), `confirm` (bool), `target_ids` (optional list).
- With `confirm=false`: search facts (provider copies), episodes and pending turns. Return grouped
  candidates (IDs, kinds, dates, short neutral labels). If the candidates span materially different
  subjects, the result tells her to ask Brian which he means (P6-D06).
- With `confirm=true` and `target_ids`: run the cascade over exactly those, then return counts.
- It **cannot** create, modify, replace or promote anything; a unit test asserts no INSERT outside
  tombstones. It never touches `USER.md` / `MEMORY.md`. The tool description tells her that current
  facts are removed with the memory tool.

**Live `SOUL.md`:**
- A short forget note in "What I remember", proposed at the STOP.
- Starting draft:

> When Brian asks me to forget something, I remove it from my notebook rather than rewriting it.
> If he wants to keep a smaller version, I remove the old note and write the new one separately.
> For things I remember from our conversations rather than my notebook, I use my forget tool, and
> if it isn't clear exactly what he means, I ask before erasing. Then I tell him plainly that it's
> gone from my memory, though our past conversation logs still have it.

**`identity/MEMORY_CONVENTIONS.md`:** the forget rules in prose.
**`identity/SOUL.md`:** mirrors the live file. Redeploy per the plugin rule.

### Exit criteria
- [ ] Unit tests (synthetic episodes and pending turns inserted directly):
  - (a) forget via `remove`;
  - (b) semantic forget via `replace`;
  - (c) bypass disappearance;
  - (d) episode-only forget through the tool;
  - (e) ambiguous description returns groups and does not execute;
  - (f) forget during a synthetic consolidation, after which the consolidation cannot commit;
  - (g) failed cascade, then retry and read suppression;
  - (h) clarification-hold expiry discards held turns;
  - (i) tombstones and logs contain no synthetic content (byte scan);
  - (j) the tool performs no writes besides deletes and tombstones.

  These are the seven tests listed in P6-D06, plus three more.
- [ ] CURSOR-RUN: `forget_memory` is the provider's only tool schema. The tool list now contains
      exactly this one extra tool.
- [ ] HUMAN-RUN, synthetic, Text mode:
  - "Forget [synthetic fact]" leads to `remove`, a cascade and a tombstone, with natural
    confirmation wording that mentions the logs (Brian's words);
  - a forget with an ambiguous target makes her ask which one, and nothing is erased until he
    answers.
- [ ] Deployed hashes match the repo. `identity/` matches the live files.
- [ ] `hermes-agent` clean. No client source changes.

**Complexity:** Medium
**Primary risk:** content matching for episodes is too narrow, so an episode that paraphrases the
forgotten thing survives. That fails open. Mitigation:
- match on the fact reference **and** on distinctive terms;
- prefer over-erasure;
- unit tests with paraphrased synthetic episodes;
- Track 5's blind test re-checks this with real episodes.

---

## Track 5 — Episodes (`P6-EPISODES`)

### Problem
She remembers facts but not what happened: no "on Oct 1 we decided X; still open: Y" (S14, the
S42 episodes remainder). Nothing marks the end of a conversation reliably on Windows (AUD-17).
No episode store exists (AUD-18).

### Files to read
- `hermes-plugins/zola_memory/` (Tracks 2–4).
- `hermes-agent` (read-only): `agent/plugin_llm.py` (`complete_structured`), `agent/memory_provider.py`
  (`sync_turn`, `on_pre_compress`, `on_session_switch`, `on_session_end`, `prefetch`),
  `agent/memory_manager.py` (`build_memory_context_block`, prefetch timeout).
- Track 2 progress doc (G1–G5), Track 4 progress doc (cascade APIs).
- `zola-architecture/audit/p6pre-phase6/Zola_P6PRE_Audit_03_EpisodesSessions.md`.

### Changes

**`pending.py` (new):**
- `sync_turn` appends a pending turn: `session_id`, per-session turn index, any message IDs
  available (G3), the user text, the assistant text, and the user-message time (the Track 3
  stamp) and assistant time.
- Content lives only here, temporarily. It is skipped when the turn is under a forget hold.

**`consolidate.py` (new), the summarizer (P6-D04):**
- **Triggers:**
  - a quiet gap, `CONSOLIDATE_QUIET_MINUTES = 10` (a named constant, tunable), checked by a
    background timer through `spawn_context_thread`;
  - `initialize()` (backlog from a previous run);
  - `on_pre_compress`;
  - `on_session_switch` / `on_session_end` if they fire.

  A single in-process lock means only one consolidation runs at a time.
- **Run:**
  1. Snapshot the pending-turn IDs and `consolidation_generation` (Track 4).
  2. Build the input: the pending turns (in order, with times), the current entity list (IDs,
     names, aliases), and the current active fact list (IDs + text). The facts let it reference
     them; it never creates them.
  3. Call `ctx.llm.complete_structured` with a JSON schema for `episodes: [...]`. Each episode has:
     - `summary`;
     - `significance` (from a fixed enum, for example decision / plan / event / preference_change /
       problem / other);
     - `entities` (existing IDs or new names with a kind);
     - `fact_refs` (existing IDs only);
     - `source_turn_range`;
     - `event_time`, `event_time_basis` ∈ {`stated`, `system`, `unknown`}, and
       `event_time_evidence` (P6-D02 rule 5):
       - `stated`: the model quotes the source phrase Brian used (for example "yesterday"), and
         the code resolves it against that message's time;
       - `system`: reserved for a time established by a structured system origin (an ID plus a
         system time), never model prose. The summarizer may not emit it in Phase 6, and the
         validator rejects a model-supplied `system` basis. The schema keeps it so a later source
         can use it;
       - `unknown`: `event_time` and evidence are null.
     - `open_items` (optional).

     The schema has no field for creating facts.
  4. Validate:
     - every `fact_ref` exists;
     - entity names are non-empty;
     - `event_time_basis` is `stated` with a quoted phrase found in a source turn, or `unknown`
       with nulls; a model-supplied `system` is rejected;
     - zero episodes is a valid result.

     Instructions to the model: small talk, arithmetic and passing chatter produce no episode; one
     stretch may produce several episodes; never record the content of a forget request.
  5. Commit in one transaction, **only if** the generation and the pending IDs are unchanged:
     insert episodes, entities and links, set `recorded_at`, copy source times, delete the
     consumed pending turns. Otherwise discard and retry later.
  6. On failure: bounded retries with exponential backoff (`CONSOLIDATE_MAX_ATTEMPTS = 5`); then
     log `consolidate.giveup` with counts and keep the turns pending. The next startup tries again
     once.
- The model call goes only through `ctx.llm` (G1/G2 trust boundary). The plugin handles no
  credentials.

**`retrieve.py` (new), the provider `prefetch` (P6-D01, D03, D05):**
- Runs on the **current** user message.
- FTS5 search over episode summaries and entity names/aliases, plus entity matching on names found
  in the message.
- Excludes anything referencing `pending_erasures`.
- Returns up to `MAX_EPISODES_PER_TURN = 3` above a relevance floor `EPISODE_MIN_SCORE` (named,
  tunable). Returns nothing when none clears the floor.
- Each item shows the date and relative age, using Track 3's helper (computed now, never stored),
  and says "date unknown" when there's no `event_time`.
- **No current facts are surfaced** (P6-D01).
- Prefetch time is logged per turn.

**`SOUL.md`:** no new section expected. If the smoke test shows she ignores retrieved episodes, a
one-line note is proposed at a STOP.

Redeploy per the plugin rule.

### Exit criteria
- [ ] Unit tests (stubbed `ctx.llm`):
  - schema validation rejects a fact-creating field, an unknown `fact_ref`, a model-supplied
    `system` time basis, and an untraceable
    `event_time`;
  - zero-episode commit removes pending turns;
  - the generation-change discard;
  - bounded retry, then giveup, keeps the turns;
  - the single-consolidation lock;
  - retrieval floor and `pending_erasures` exclusion;
  - relative-age formatting.
- [ ] CURSOR-RUN: prefetch p95 **under 50 ms** on the live profile over at least 30 non-trivial
      turns (`zola_memory.log`). Consolidation never blocks a turn (it runs off-thread; turn
      latency is unchanged against the Phase 5 baseline within noise).
- [ ] HUMAN-RUN, **blind episode test**. Brian holds a scripted, natural, synthetic conversation
      in session S1:
  - two meaningful events, for example a decision about a fictional project and a fictional car
    plan, one with a stated time ("I did it yesterday");
  - some small talk;
  - one arithmetic question.

  Then a 10-minute or longer quiet gap. Cursor then records one row per scripted item: expected
  episode?, created?, summary accurate? (Brian judges), entities, `fact_refs`, `event_time`
  correct or unknown as appropriate. **Pass:**
  - both meaningful items become episodes with accurate summaries;
  - small talk and math produce none;
  - the stated time is resolved correctly;
  - the other episode's `event_time` is unknown.
- [ ] HUMAN-RUN recall, new session S2, two categories:
  - **Direct recall (gating):** "What did we decide about [fictional project]?" brings back the
    episode, with when ("earlier today" or a correct date), and no `session_search` call.
  - **Associative recall (measured, not gating):** ask about the same events in wording that does
    **not** repeat the episode summary's key nouns or phrases (the script is fixed before S1 and
    never shown to Zola). For each question, record:
    - whether a candidate was found;
    - whether the correct episode was in the top 3;
    - any irrelevant episodes surfaced;
    - the retrieval score;
    - whether her answer was correct.
  - An unrelated question surfaces no episode (no `<memory-context>` fence).
  - If direct recall passes and associative recall fails, Phase 6 still ships, and the lore
    closeout files an OQ for semantic/associative episode retrieval with this table as evidence.
- [ ] HUMAN-RUN forget on a real episode: "forget what we talked about regarding [fictional car
      plan]" leads to clarify-or-erase per Track 4. The episode is gone, the tombstone exists, and a
      repeat of the S2 question no longer recalls it.
- [ ] HUMAN-RUN **paraphrase forget** (proves P6-D06 against model-written episodes):
  1. Pick an episode whose summary paraphrases its source turns (Cursor confirms the wording
     differs, recording counts and terms, not content).
  2. Brian asks her to forget the underlying information in **different** wording from both the
     source and the summary.
  3. Verify the episode is erased.
  4. Query using the episode's old summary wording, and using the original source wording.
  5. Verify nothing resurfaces through prefetch or her answer. `session_search` is not used, since
     P5-D06 is explicit-request only.

  A survivor is a P6-D06 failure: stop and report.
- [ ] Crash safety: a pending turn written before the client is force-closed is consolidated on
      the next startup (Cursor checks `zola_memory.log`).
- [ ] Synthetic episodes are removed through her forget tool at the end. Counts are recorded.
- [ ] `hermes-agent` clean. No client source changes.

**Complexity:** Large
**Primary risk:** episode quality. The summarizer produces session-recap blobs, or misattributes
events or times, and wrong memories persist. Mitigations:
- the structured schema with zero-episode permission;
- traceable `event_time` only;
- source ranges on every episode;
- the blind per-item test.

If the blind test fails, stop and report the per-item table. Don't loosen the pass criteria or
add a second writer.

---

## Phase 6 Lore Closeout

After all five tracks are merged to `main`:

### DESIGN_DECISIONS.md
- Record P6-D01 through P6-D08 under "Phase 6 — Memory She Lives With". Use the Appendix A text,
  condensed in house style, with each verdict quoted as given.
- Annotate:
  - `P4`: **revised by P6-D07** (local only; the model-processing boundary stated);
  - `C4`: extended. Files remain the fact authority; the structured store sits beside them
    (P6-D01);
  - `S14`: **Phase 6 foundation complete, not resolved.** Built: the local store, the fact index,
    episodes, lexical/entity retrieval, time and forget. Still open:
    - long-term retrieval quality (the associative-recall table from Track 5);
    - the evidence-based fact-authority migration (P6-D01).

    Do not record S14 as resolved;
  - `C8` / `P5-D10`: forget now cascades through the provider; `state.db` is still not redacted
    (P6-D06);
  - `P5-D06`: stands, restated in P6-D02 rule 8;
  - `P4-D07` / `P4-D27`: stand (P6-D08).

### OPEN_QUESTIONS.md
- `S43`: **RESOLVED** by `P6-TIME`. Note the per-message stamp, the cross-session gap, and the
  over-mention result.
- `S42`: episodes remainder **RESOLVED** by `P6-EPISODES`. S42 is closed.
- `S35`: **arithmetic case RESOLVED** by `P6-CALC` (no approval change). Session/always scopes
  stay open.
- `S14`: annotate what was built, with the open migration question and the measurement plan
  (fill %, prefetch relevance, prompt cost).
- `S28`: annotate that episodes now exist. Session UI retirement can be evaluated.
- AUD-24 (the `session_search` timezone label) stays a Hermes-side gap; record it in the Phase 6 decisions entry as a known limit.
- File an OQ for semantic/associative episode retrieval if Track 5's associative-recall table shows
  misses, citing the table.
- File any new OQs the tracks raise, for example tuning values that never felt right, or
  consolidation cost.

### ROADMAP.md
- Mark Phase 6 COMPLETE, with plan, track and merge SHAs.
- Add a Phase 7 stub. The likely candidates are `S44` (deferred here), `S40` and `S28`. Scope is
  the developer's call.

### identity/
- `SOUL.md` and `MEMORY_CONVENTIONS.md` were already updated by the tracks. The closeout confirms
  they match the live profile.
- The plugin source in `hermes-plugins/` matches the deployed copies (hash table).

---

## Phase 6 Exit Checklist
- [ ] Track 1 (`P6-CALC`) merged. Three arithmetic prompts give zero cards; the control still
      raises a card; the calculator fails closed.
- [ ] Track 2 (`P6-STORE`) merged. G1–G9 answered; live hook proof recorded; fact index and
      fact-level forget pass; no Phase 5 regression.
- [ ] Track 3 (`P6-TIME`) merged. Stamps on every turn including trivial ones; gap awareness;
      never spoken aloud.
- [ ] Track 4 (`P6-FORGET`) merged. All ten forget unit tests and both live forget tests pass.
      This proves the forget **mechanism** against synthetic episode rows.
- [ ] Track 5 (`P6-EPISODES`) merged. Blind episode test, direct recall, episode forget,
      **paraphrase forget** and crash safety pass; prefetch p95 under 50 ms; the associative-recall
      table is recorded. This proves forget **behavior** against real model-written episodes.
      P6-D06 counts as proven only after both Track 4 and Track 5.
- [ ] No `hermes-agent` edits; `git status` clean at `345cd2b0…` after each track.
- [ ] No installs. Config changes limited to those approved at STOPs (`memory.provider`, plus any
      approved plugin enable or LLM trust keys), each with its P6 comment tag.
- [ ] All tunables are named constants: `MEANINGFUL_GAP_MINUTES`, `CONSOLIDATE_QUIET_MINUTES`,
      `CONSOLIDATE_MAX_ATTEMPTS`, `FORGET_HOLD_MAX_MINUTES`, `MAX_EPISODES_PER_TURN`,
      `EPISODE_MIN_SCORE`, the calculator limits, and the forget phrase list. Log prefixes are
      named constants. No magic strings.
- [ ] No memory content in any log, repo document, tombstone or test fixture (synthetic only).
- [ ] Plugin unit tests pass on `main` after all merges. The build still passes.
- [ ] Smoke test after each track boundary.
- [ ] `DESIGN_DECISIONS.md`: P6-D01–D08 recorded, with annotations.
- [ ] `OPEN_QUESTIONS.md`: S43 resolved; S42 closed; S35 arithmetic resolved; S14/S28 annotated.
- [ ] `ROADMAP.md`: Phase 6 COMPLETE; Phase 7 stub added.

---

## What Phase 6 Explicitly Defers

| Item | Reason | When |
|---|---|---|
| Moving fact authority from the files to the store | Not needed at current size; must be decided on measured evidence (P6-D01) | Future decision, with Phase 6 measurements |
| Surfacing current facts through retrieval | Every current fact is already injected (P6-D01) | With the fact-authority migration |
| A model-facing "search my episodes" tool | Prefetch covers retrieval; fewer tools, less risk | Future, if recall gaps appear |
| Validity periods (`valid_from` / `valid_until`) | Never inferred (P6-D02 rule 5) | Only if a real need appears, with a decision |
| Redacting `state.db` transcripts on forget | Editing Hermes' own database is a real risk; P5-D10 stands, disclosed (P6-D06) | Future decision |
| Autonomous `session_search` | P5-D06 stands (P6-D02 rule 8) | Would need a new decision |
| Approval session/always scopes (rest of `S35`) | The arithmetic case is solved without touching approvals | Later phase |
| `session_search` timezone label (AUD-24) | Hermes-side formatting; no edit | Upstream, or not at all |
| Prefetch timeout config key (AUD-04) | Needs a `hermes-agent` edit; 2 ms vs 8 s leaves ample headroom | Upstream, or not at all |
| Closing the bypass writers themselves (AUD-06) | The file check makes them harmless to the index (P6-D01) | Not planned |
| Encryption at rest (H4) | Security bucket, before any release | Security bucket review |
| Tiers, confidence decay, environmental/camera facts | Out for v1 (`S14` lore) | Not planned |
| `S44` clarify card in Voice mode | Developer: deferred | Phase 7 candidate |
| `S40`, `S38`, `S36`, `S28` (retirement itself), `S33`, `S34`, `S37`, `S39`, `S17`, `S21`, `S26`, `S12`, `S13`, `S16`, `S24`, `S25`, `S31` | Not in Phase 6 scope | Later phases |

---

## Complexity Legend

| Track | Complexity | Primary Risk |
|---|---|---|
| 1 — `P6-CALC` | Small-Medium | Plugin tool not visible on the `tui` toolset, or she keeps choosing `execute_code` |
| 2 — `P6-STORE` | Medium-Large | Activation changes more than the provider, or the file check misreads a reformatted fact as a forget |
| 3 — `P6-TIME` | Small-Medium | `pre_llm_call` context not kept in history, so earlier messages lose their stamps |
| 4 — `P6-FORGET` | Medium | Episode content matching too narrow; a paraphrased episode survives a forget |
| 5 — `P6-EPISODES` | Large | Episode quality: recap blobs, or wrong attributions and times that persist |

---

## Appendix A — Locked Decisions (verbatim from the decisions log, 2026-10-02)


#### P6-D01: Two kinds of memory, one authority each

`USER.md`/`MEMORY.md` stay the authority for current durable facts in Phase 6, written only through the memory tool as Phase 5 taught her. A Zola-owned local store holds:

- **(a) a structured fact index** derived from the files (entities, stable IDs and timestamps). It is kept in step by write notifications, plus a check against the files that catches bypass writes. The current index is always rebuildable from the files. The store may also keep lifecycle history it observes through those writes, without becoming a second fact authority. History retention is subject to P6-D06 (forget): until a forget can be told apart from a correction or removal, removed content is not kept as history.
- **(b) episodes**, for which the store is the sole authority.

Episodes may reference facts; they never create or change them. Retrieval is built for both facts and episodes. In Phase 6 it does not redundantly surface current facts, because every current fact is already injected; it surfaces relevant episodes and temporal context instead. Moving fact authority to the store is a future decision, made on measured evidence (relevance, prompt cost, memory quality), not on a fill percentage. Fill percentage is reported for review only.

- **Wording:** Brian's, plus Claude's history/forget clause.
- **Brian's verdict:** "I agree"
- **Evidence:** AUD-01, 02, 05, 06, 07, 13, 18; synthesis 5.1 (model A, with the bypass hazard).
- **Review:** ChatGPT and Claude converged. Rejected: the 80%-fill migration trigger; episode `derived_facts`.

#### P6-D02: Memory invariants

1. Facts have one author: Zola, through the memory tool.
2. Episodes have one author: the episode writer. The identity and trigger of that writer are separate decisions.
3. Episodes may reference facts; they never create, replace, remove, or otherwise mutate facts.
4. Entities organize knowledge; they do not create it. They connect facts and episodes without becoming an independent write path.
5. Timestamps record only what's actually known. Lifecycle times (learned, updated, superseded, recorded) are stamped automatically. Event times are stored only when explicitly provided by Brian or directly known from an authoritative system event or source. Validity periods are never inferred.
6. Correction preserves history; forget erases content. A forgotten record may retain only a content-free tombstone, such as an ID and erasure time, to support forget enforcement and auditing; it must contain no recoverable representation of the forgotten content.
7. Retrieval never becomes persistence. Finding something through structured retrieval, an episode, or conversation search does not make it a durable fact.
8. Raw conversation is evidence, not curated memory. P5-D06 stands: past conversations may be searched only when Brian asks, but they are not automatically promoted into durable memory.

- **Wording:** Brian's. Rule 8 uses Claude's wording because Brian's draft ("when explicitly needed") unintentionally loosened P5-D06.
- **Brian's verdict:** "With that correction to Rule 8, I would record P6-D02. I wouldn't change Rule 6 yet; your note captures exactly what the later forget decision needs to solve."
- **Consequences carried forward:**
  - Rule 6 means no content hash or fingerprint in tombstones, because short facts are guessable. Forget enforcement is deletion and cascade across every representation P6 controls (files, index, FTS, relationships, episodes), not suppression.
  - Autonomous conversation-history access would need its own new decision.

#### P6-D03: A Zola-owned local memory provider (amended by P6-D06)

Phase 6 builds its own memory provider and does not use Holographic, even adapted. Holographic is a reference for useful implementation patterns only; none of its model-facing tools, auto-extraction, or HRR/vector machinery carries over.

* **Where it runs:** a profile plugin at `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\`, loaded through `memory.provider`, with no edits to `hermes-agent` (AUD-01).
* **Where its code lives:** canonical source lives in the `zola-windows` repo at `hermes-plugins/zola_memory/`. The live profile copy is deployed under P4-D25: proposed at a STOP, backed up, explicitly approved, and mirrored, as with other live profile artifacts.
* **Storage:** one profile-local SQLite database using Python's built-in `sqlite3` and the SQLite full-text-search capabilities available in the deployed runtime. No new installs, NumPy, network calls, or external memory service.
* **Model-facing tools:** none in Phase 6. The provider registers no model-facing tools. Facts continue to enter only through the existing memory tool under D02. Episode creation is an internal memory-system operation, not an alternate model-callable persistence path.
  * **AMENDED by P6-D06:** this becomes "none except one erase-only forget operation". That operation can locate and erase provider-held memory but can never create, modify, replace or promote memory, so it is not a persistence authority.
* **Hermes contract:** indexing and other maintenance that can be prepared ahead of time run off the turn-critical path, in the right profile context. Relevance retrieval uses the current turn, through Hermes' provider prefetch contract, and returns retrieval context for that turn. It must stay comfortably inside Hermes' fixed 8-second prefetch timeout. The design must not depend on the unreliable Windows `on_session_end` path.

- **Wording:** Brian's. The repo folder was Claude's default; Brian approved it.
- **Brian's verdict:** "yes." (This covers his preferred D03 text and the `hermes-plugins/zola_memory/` folder.) The amendment was accepted with D06: "lock with amendment".
- **Notes for the build plan:**
  - Retrieval runs synchronously on the current turn, which is deliberate. The P-1 warm median is about 2 ms at 2,000 records. This departs knowingly from the queued-prefetch wording that AUD-09 flagged for holographic.
  - The smoke test needs a numeric latency target (for example, p95 under 50 ms on the live profile).
  - The provider checks at startup that SQLite full-text search is available. If it is missing, it fails closed instead of degrading.

#### P6-D04: Episodes are written by a background summarizer inside the provider

It uses Hermes' host-owned plugin model call, with no credentials handled by the plugin. The availability of that model-call path is a build grounding check, and implementation stops if it is unavailable.

Each completed conversational exchange available through the provider/plugin lifecycle is appended to a temporary pending-turn queue in the provider's own store, with its session/message identity, ordering and source timestamps. The summarizer consolidates pending conversation into zero or more episodes when there is a quiet gap, at startup, before compression, or at a session switch or end if one fires. No single trigger is relied on for correctness. It never reads `state.db`.

Its only durable output is episodes. An episode may span multiple turns and includes:
- its source session/message range;
- multiple entity references;
- references to existing fact IDs;
- temporal metadata under P6-D02.

`recorded_at` and source-message times are system-stamped. An episode's `event_time` is recorded only when explicitly supplied by Brian or directly established by an authoritative system event or source; otherwise it remains unknown. The summarizer never creates or changes facts.

Pending turns are removed only after a successfully committed consolidation result, including a valid result of zero episodes. A failed or interrupted consolidation leaves them pending for retry. Pending turns are temporary working data, not memory, and P6-D06's forget cascade applies to them.

A consolidation result is committed only if its source pending turns are unchanged since consolidation began; otherwise it is discarded and the remaining turns are retried. Committing episodes and removing their pending turns happen in one transaction. Retries are bounded with backoff, and repeated failure is logged rather than retried forever; failed turns stay pending.

- **Wording:** Brian's, plus Claude's last paragraph (the forget/consolidation race guard and bounded retry).
- **Brian's verdict:** "lock"
- **Evidence:** AUD-17, 18, 20, 21 (no reliable session end; no episode store); `agent/plugin_llm.py` (host-owned plugin LLM facade; the plugin never sees tokens); `memory_manager.sync_all` (per-turn `sync_turn` on a background worker).
- **Build plan must include:**
  - grounding: confirm that a memory provider can reach `ctx.llm`, and confirm `sync_turn` delivery on the Windows `tui_gateway` path;
  - a live hook-firing proof (P-3 was skipped);
  - a blind check that episodes match what happened;
  - a forget-during-consolidation test.

#### P6-D05: Ambient, system-stamped time

Every user message reaching the model carries a short local timestamp, added by the `zola_memory` plugin through Hermes' `pre_llm_call` hook (no `hermes-agent` edit) and kept in conversation history.

When a conversation starts, or resumes after a meaningful gap, Zola also receives the elapsed time since Brian's most recent prior interaction with her across conversations, not merely within the current Hermes session.

Retrieved episodes show their known date/time and a relative age computed for the current turn. Relative times and elapsed gaps are computed at read time and never stored. Unknown event times are never estimated or presented as known.

`SOUL.md` tells Zola to use temporal awareness naturally in conversation and never to read timestamp/context metadata aloud. That live-profile edit follows P4-D25.

This is Zola's single ambient-time mechanism, and Hermes' `gateway.message_timestamps` stays off. Build grounding must confirm three things:
- `pre_llm_call` fires for every user turn, including trivial turns;
- the injected timestamp is kept in conversation history;
- the cross-session last-interaction time can be determined without reading `state.db` transcripts.

- **Wording:** Brian's.
- **Brian's verdict:** "Yes. I would put both into the build plan, and I think the `last_interaction_at` marker is the correct solution."
- **Build plan requirements (Brian):**
  - Keep a content-free `last_interaction_at` provider metadata value. For each user turn: read the previous value, derive the temporal context, inject the current timestamp (plus the elapsed gap if it is at or above the threshold), and only then update the value to the current system-stamped interaction time. Do not update it until that turn's timestamp/gap context has been built successfully; otherwise a failure could erase the previous interaction time. Never persist the computed elapsed gap. The marker is operational metadata, not memory.
  - `meaningful_gap` (for example, `MeaningfulGapMinutes = 30`) is a tunable starting value, validated and tuned during P6 smoke testing. Changing the threshold does not change P6-D05.
- **Risk:** she over-mentions time. The `SOUL.md` line is the mitigation; the smoke test listens for it.

#### P6-D06: Forget erases every copy the memory system controls

**Recognition fails closed.** `remove` is a forget. `replace` is a correction unless the originating user turn clearly requests forgetting or deletion of the replaced information; in that case the replaced content is erased rather than kept as history. A fact that disappears from an authoritative memory file without a matching notification is treated as forgotten. Heuristics may make forgetting stricter, never looser. `SOUL.md` tells Zola to use `remove`, not `replace`, for forget requests; to keep a reduced version, she removes the old fact and separately adds the reduced one.

**The cascade erases every provider-controlled representation:**
- structured/index rows and search entries;
- lifecycle history containing the content;
- entity links;
- matching pending turns, including the forget-request turn;
- every episode that references or contains the forgotten information. Affected episodes are deleted whole, not rewritten.

A forget invalidates any in-flight episode consolidation containing affected pending material, and those results may not commit. Provider erasure is transactional: Zola reports success only after the cascade commits.

When a fact is removed through the memory tool, Hermes reports success before the provider cascade runs, so the cascade cannot gate that report. Instead, a fact missing from the files without a completed cascade is treated as forgotten by the file check and erased on retry until the cascade commits. Until then, retrieval suppresses any provider-held record that references it. While a forget awaits clarification, the affected pending turns are held back from consolidation; if the forget is never resolved, they are discarded.

**Episode-only memory** is forgotten through one model-facing provider operation whose authority is destructive only: it can locate and erase provider-held memory, but it can never create, modify, replace or promote memory. It does not edit `USER.md` or `MEMORY.md`; current durable facts are still forgotten through the existing memory tool. If a description ambiguously matches materially different memories, Zola clarifies the intended scope rather than guessing. This amends P6-D03's "no model-facing tools" to permit this single erase-only forget operation, without creating a second persistence authority.

**Transcripts** stay outside the forget cascade. `state.db` is not redacted, preserving P5-D10. When confirming a forget, Zola makes clear that the information has been removed from her memory while the original conversation remains in conversation history. The memory system never automatically rebuilds forgotten memory from those transcripts.

**Tombstones are content-free.** They may keep only identifiers, record kind, erasure time and non-content cascade counts. They contain no text, embedding, fingerprint, hash or other recoverable representation of forgotten content.

- **Wording:** ChatGPT's final text, plus Claude's paragraph on the memory-tool path and clarification hold.
- **Brian's verdict:** "lock with amendment"
- **Evidence:** AUD-08, 26, 27, 28; synthesis 5.6; Audit 01 §5 (`on_memory_write` runs after the file write, and provider errors are swallowed).
- **Build plan notes:**
  - Structured tombstone counts (fact, episode, pending and index rows removed) are an implementation detail.
  - The confirmation wording should be natural, not a recited disclaimer.
  - Tests needed: forget via `remove`; a semantic forget via `replace`; a bypass disappearance; an episode-only forget; an ambiguous description (clarify); forget during consolidation; a failed cascade, then retry and suppression.

#### P6-D07: P4 revised to "Memory is stored and retrieved locally; no third-party memory service"

* **Local memory authority:** Zola's persistent memory (the flat files, the provider SQLite store, the pending consolidation queue, indexes and tombstones) lives only in the local profile. Persistent memory is stored, searched, retrieved and erased on the machine. No provider-held memory database, index or retrieval service exists off-device.
* **No third-party memory service:** no cloud or third-party memory provider, such as Honcho, Hindsight, mem0, Supermemory or similar, is used, and Zola's memory is never sent to one for storage or retrieval. The original `P-3P` third-party-retention concern still governs.
* **Model-processing boundary:** P6-D04 episode consolidation may resend pending conversation content through Hermes' host-owned model-call path for summarization. It uses the same model-provider trust boundary already approved for Zola's ordinary conversation processing; it does not introduce a separate model provider or any other third party for memory work. This is model processing, not off-device memory storage or retrieval. A future change to Zola's model-provider trust boundary applies to episode consolidation as well.
* **At-rest boundary:** local memory stays unencrypted at rest (H4 stays deferred) and remains within Hermes' local backup scope.

- **Wording:** Brian's.
- **Brian's verdict:** "lock"
- **Evidence:** AUD-12, 29, 30; synthesis 5.7.
- **Build grounding check (Claude):** `plugin_llm` runs on Hermes' auxiliary path (`auxiliary_client.call_llm`), which can be configured to a different provider or model from the main conversation. The build must confirm which provider and model the plugin call resolves to under Zola's effective config, and stop if it is outside the approved trust boundary.
- **Lore:** at closeout, P4 in `DESIGN_DECISIONS.md` is annotated "revised by P6-D07".

#### P6-D08: Math without code; approvals unchanged

Approval cards appeared for arithmetic because Zola invoked code-execution paths (`execute_code` or terminal `python -c`), which Hermes correctly treats as potentially machine-changing operations. The approval gate is not loosened: `approvals.mode: manual`, P4-D07 and P4-D27 stand, with no allowlist, `smart` mode, or session approval scope.

* **Calculator plugin.** A separate profile plugin, `zola_tools` (canonical source under `hermes-plugins/zola_tools/`, live deployment under P4-D25), registers one side-effect-free `calculate` tool.
  * It evaluates a bounded arithmetic grammar through a fixed allowlist of supported operations and functions.
  * It never uses `eval`, code execution, shell/terminal execution, imports, filesystem access, network access, or other side effects.
  * Input, computational-complexity and result-size limits prevent pathological expressions.
  * Unsupported expressions fail closed rather than falling back to code execution.
  * The tool is intentionally outside the approval gate, because this contract exposes only bounded, side-effect-free arithmetic.
* **`SOUL.md` guidance.** Zola answers arithmetic directly when she can do so confidently. She uses `calculate` when deterministic calculation is useful, especially for multi-step, monetary, percentage, or other precision-sensitive arithmetic. She never invokes code execution or terminal commands solely to calculate.

**Acceptance:**
- The three P-4 arithmetic prompts return correct answers with zero approval cards.
- Unsupported calculator input fails without execution or side effects.
- A control operation that genuinely requires machine-changing authority still produces the existing approval card.

**Scope:** this resolves the arithmetic case of S35. Approval behavior itself is unchanged. Broader approval scopes, including session or persistent scopes, remain open under S35. Whether registering `zola_tools` requires a live-profile/config change is established during build grounding and, if required, follows P4-D25.

- **Wording:** Brian's.
- **Brian's verdict:** "lock"
- **Evidence:** AUD-31, 32, 34, 35, 37, 38; synthesis 5.8; P-4 (Audit 07).
- **Build note (Claude):** the `SOUL.md` text proposed at the STOP should also say that if `calculate` can't handle an expression, she says so or works it through in conversation instead of running code.

---

*Phase 6 Build Plan version 1.1 (v1.1: ChatGPT review. G2 records the conversation and auxiliary providers side by side; same provider passes, a different provider is a STOP. Track 5 measures associative recall (not gating; an OQ if it fails). `event_time_basis`/evidence keeps D02's system source possible. Track 5 adds a live paraphrase-forget test, and P6-D06 counts as proven only after Tracks 4 and 5. S14 is recorded as "foundation complete", not resolved.)*
*Created 2026-10-02*
*Base SHA: `92dc707ac047d2808b9f1848bb0e31f96689065a` (record the actual tip at plan commit)*
*Prerequisite audit: P6PRE — merge `92dc707ac047d2808b9f1848bb0e31f96689065a`, audit commit `84f14d83db8efd7e495acbfa078a8da66b415683`*
*All Phase 6 decisions locked before the plan was written (developer approval 2026-10-02; full text in Appendix A).*
*Next step: commit this build plan to `zola-architecture/lore/build-plans/` on `main` (Track 1,
Phase 1, per SOP v2.2 Stage 3), then begin Track 1 (`P6-CALC`).*
