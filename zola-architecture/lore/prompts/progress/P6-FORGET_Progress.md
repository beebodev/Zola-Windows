# P6-FORGET Progress — Forget Reaches Everything

## Branch

- Branch: `p6-forget`
- Base `main` HEAD: `d4d52f3d06613bb7d3913d81125bcfbdf202dd50` (after P6-TIME closeout)
- Plan commit SHA: `187275981bdcbfcf3acd87a148bb0606a1c2d1e1` (`docs: Phase 6 build plan v1.1 (P6-D01–D08)`)
- Plan merge SHA: `aee0f0da2ce0382c117013dc57f2cc32f1cd8370` (`Merge branch 'p6-plan'`)
- Prompt version: 1.1 (2026-10-04) against build plan v1.1 (+ Track 3 lifecycle lessons)
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P6-FORGET_Prompt_v1.1.md`
  SHA-256 `a3e3b01a9891f3b4c0589853f93773b91d01376eb5c941278e87194fc743944c` (29,804 bytes; matches developer-supplied hash, case-insensitive)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`; expect clean throughout)
- Scratch (outside repos): `C:\Users\test\Dev\zola-spikes\p6-forget\`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document | COMPLETE |
| 2 | Grounding (F1–F8) | COMPLETE — STOP awaiting Phase 3 |
| 3 | Propose the Forget Contract | COMPLETE — approved with E1–E6 |
| 4 | Build and Test | COMPLETE |
| 4b | Defect fixes (D1 schema pre-init; D2 notify mark) | COMPLETE |
| 4c | Defect fix (D3 search recall) | COMPLETE |
| 4d | Label ranking (names/digits/matches) | COMPLETE |
| 5 | Propose the Live Changes | COMPLETE — approved |
| 6 | Back Up, Deploy, Apply, Mirror, Verify | COMPLETE |
| 7 | Smoke Test | COMPLETE — machinery PASS; P6-D06 FAIL → 7b |
| 7b | SOUL confirmation fix + retest | COMPLETE |
| 7c | Disposition key mismatch + SOUL clarify | COMPLETE |
| 8 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Repo: `hermes-plugins/zola_memory/` (`forget.py`, `provider.py`, cascade wiring in `fact_index.py`, `log.py`, tests); `identity/SOUL.md` + `MEMORY_CONVENTIONS.md` (approved mirrors only); this progress doc. Live Phase 6 only after Phase 5 STOP: redeploy `plugins/zola_memory/`, approved `SOUL.md` forget text. No expected `config.yaml` change. No client / `approvals.*` / `zola_tools` / `time_context.py` behavior change / episode writing / retrieval.
- **G-ARCH:** Build plan + Appendix A (P6-D02 rules 6–7, P6-D03 amended, P6-D06) govern. If a provider tool cannot register without editing `hermes-agent`, STOP.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No `windows-client/**`; no `hermes-agent` edits; no hand edits to live `memories/`, `state.db`, `skills/`, `auth.json`, `.env`, `approvals.*`, `plugins/zola_tools/`; no lore / build-plan edits.
- **G-NO-INSTALL:** Stdlib only.
- **G-ONE-AUTHORITY:** Current facts forgotten only via memory-tool `remove`. Forget tool is erase-only; never edits `USER.md`/`MEMORY.md`; never creates/modifies/replaces/promotes memory.
- **G-FAIL-CLOSED:** Target uncertainty → clarify/refuse; copy uncertainty within established target → erase.
- **G-TOMBSTONE:** Tombstones = IDs, kind, erasure time, non-content counts only. No recoverable content representation anywhere persistent.
- **G-REGISTRY:** Per-conversation via FIX-B session→provider registry or Hermes-called instance; `_provider` only for LLM probe.
- **G-AUTHORITY / G-LABELS:** Proposed; Brian decides at Phase 3.
- **G-PRIVACY:** Logs: event, IDs, kinds, counts, ok, timings — never message text, labels, or matched terms. Synthetic test data only.
- **G-CONST / G-COMMENT:** Named constants; `# P6-FORGET: <rationale> — P6-D06`.
- **G-LIVE / G-STOP / G-CLOSEOUT:** One step at a time; Cursor never injects turns; closeout only on "proceed to closeout".
- **G-LORE-SCOPE:** No lore edits this track (including closeout).
- **G-NO-CROSS-SCOPE:** Android Zola out of scope.

## Discrepancies

- **F4 byte-identity:** `on_turn_start.message` is **not** always byte-identical to `sync_turn.user_content` — Hermes strips skill scaffolding and flattens multimodal on the sync path only (`memory_manager.py` L490–491; `turn_context.py` L770–775). For ordinary TUI string turns without skill bodies they match (same `original_user_message` source; excludes time injection — T4). Disposition must not assume raw equality for all turns.
- **F4 `session_id` on `on_turn_start`:** Hermes passes only `author_id` / `author_name` / `author_is_bot` (`turn_context.py` L774–778). Zola today logs `kwargs.get("session_id")` → usually `-`. Use provider `self._session_id` (FIX-B) for conversation identity.
- **F3 cron:** Cron agents load memory with `skip_memory=False` and can expose provider tools unattended — Phase 3 must address (G-AUTHORITY / platform allow-list).
- **F6 transcript args:** Tool-call **arguments** appear in Windows history (`session_history.py` L197–216) and live `tool.start`/`tool.complete`. Results: live events yes; history projection no. TTS: neither. Carry into Phase 3 for G-LABELS (Brian knowingly approves transcript persistence of candidate labels if F6 applies).

## Phase 1 baselines

| Check | Result |
|---|---|
| `main` HEAD | `d4d52f3d06613bb7d3913d81125bcfbdf202dd50` ✅ |
| Working tree on branch create | clean ✅ |
| Branch | `p6-forget` created from that tip ✅ |
| `hermes-agent` HEAD | `345cd2b057a452236de401d3534b8502a7465e8d` ✅ |
| `hermes-agent` porcelain | empty ✅ |
| Prompt SHA-256 | matches developer-supplied `a3e3b01a…3944c` ✅ |
| `zola_memory` unit tests | **Ran 53 — OK** ✅ |
| `zola_tools` unit tests | **Ran 44 — OK** ✅ |

## F1–F8 grounding table

Hermes pin `345cd2b057a452236de401d3534b8502a7465e8d`. Live `approvals.mode: manual` (`config.yaml` L9–10).

| ID | Verdict | File:lines | One-line answer |
|---|---|---|---|
| F1 tool contract | **[CONFIRMED]** | `memory_provider.py` L133–138; `memory_manager.py` L64–76, L144–157, L354–375, L590–596; `tool_executor.py` L1522–1528; `agent_init.py` L1273–1296 | Schema: OpenAI `{"name","description","parameters"}` (or wrapped function); inject as `{"type":"function","function":…}`. `handle_tool_call(tool_name, args, **kwargs) → str` (JSON); executor passes `(name, args)` only. Core-tool / duplicate names dropped at `add_provider`. Dispatch hits **this** agent's `MemoryManager` → `_tool_to_provider` instance from that agent's `load_memory_provider`. |
| F2 approval gate | **[CONFIRMED]** — does **not** card | `tool_executor.py` L639–689, L1522–1528; `tools/approval.py` L1–5; `memory_manager.py` L590–596; live `config.yaml` L9–10 | Under `approvals.mode: manual`, provider tools skip the dangerous-command approval card. Path: scope → `pre_tool_call` → guardrails → `MemoryManager.handle_tool_call`. Builtin `memory` writes use separate `memory.write_approval` (unset live). A plugin `pre_tool_call` `approve` action could still card — not default. **Carry to Phase 3:** two-step `confirm` cannot rely on approval cards. |
| F3 which agents see the tool | **[CONFIRMED]** | `agent_init.py` L1273–1296; `cron/scheduler.py` L2212–2214; `background_review.py` L869–881, L1031–1065; `delegate_tool.py` L239–240 | **Main TUI:** yes when `skip_memory=False`. **Cron:** yes (`skip_memory=False`) — can call provider tools **without Brian**. **Background review:** `skip_memory=True`; no `MemoryManager` on fork; provider tools only if listed in `extra_tools` (default no). **Subagents:** `skip_memory=True`; no provider tools. **Carry to Phase 3:** cron / unattended exposure. |
| F4 turn identity | **[CONFIRMED]** (byte-identity caveat) | `turn_context.py` L770–778, L937, L942–943, L980–984; `memory_manager.py` L480–504, L590–608, L720–734; `memory_provider.py` L124–148, L185–187; `run_agent.py` L875–901 | `on_turn_start(turn_number, message, author_*)` — message = `original_user_message` (no time injection). `sync_turn(user, assistant, session_id, messages?, turn_author?)` — user after skill-strip. `handle_tool_call`: name+args only (no session kwargs). `on_memory_write`: action/target/content + metadata (`session_id`, …). **Not** always byte-identical (skill strip / multimodal) — see Discrepancies. Provider conversation id: `self._session_id` (FIX-B), not `on_turn_start` kwargs. |
| F5 ordering / races | **[CONFIRMED]** | `memory_manager.py` L302–303, L480–533; `turn_finalizer.py` L603–607; `turn_context.py` L990; `turn_recovery.py` L968–981; `run_agent.py` L888–889 | Turn N `sync_turn` (single background worker) can still run/finish **after** N+1 `on_turn_start` (sync prologue). Interrupted turns: `on_turn_start` yes, `sync_turn` often **no**. Turn-number-only disposition is unsafe; prefer content + session_id. |
| F6 visibility | **[CONFIRMED]** | `session_history.py` L197–216; `tool_progress.py` L232–286; `prompt_turn.py` L523–530; `test_tui_gateway_server.py` L2965–3001 | Tool **args** in client history + live `tool.start`/`tool.complete`. Tool **results** in live events; **not** in history projection. **TTS:** assistant `message.delta` only — not tool args/results. `api_content` never on client wire. **Carry to Phase 3 (G-LABELS):** candidate labels in tool results can persist in `state.db` via transcript/live events. |
| F7 schema use | **[CONFIRMED]** | `store.py` L167–239; `provider.py` L175–189; live DB counts | Tables `episodes`, `episode_entities`, `episode_fact_refs`, `pending_turns`, `entities`, `entity_aliases` exist; **0 rows** live; nothing in zola_memory writes them today (`sync_turn` log-only). FTS: `facts_fts` only — **no episode FTS** (C4). |
| F8 cache / prompt | **[CONFIRMED]** | `provider.py` L127–131; `memory_manager.py` L115–158; `system_prompt.py` L460–484; `model_metadata.py` L2277–2302 | Empty `system_prompt_block` + `get_tool_schemas=[]` → G6: no prompt/tool delta today. Adding one unique provider tool appends exactly that schema when memory toolset exposed; prompt unchanged if block stays `""`. Rough cost for PHASE6-shaped `forget_memory`: **~140 tokens** (Hermes tools estimator). |

### Phase 2 notes

- No F1/F4 API absence → not BLOCKED. Byte-identity and cron/labels are Phase 3 inputs (Discrepancies).
- Read-only; hermes-agent clean; no source changes except this progress doc.
- zola_memory still returns `get_tool_schemas() → []` (no `forget_memory` yet).

## Proposed forget contract (awaiting Brian's approval)

Nothing built. Phase 4 builds exactly what is approved here.

### Phase 2 acceptance (Brian + Claude, verbatim amendments, 2026-10-04)

> Phase 2 accepted (Brian + Claude). Phase 3 must address these explicitly:
> 1. F3 cron: forget_memory usable only on genuine Brian conversations — same predicate as time_context (platform "tui", no parent). Propose (a) whether get_tool_schemas can omit the tool for non-tui agents … and (b) mandatory execution refusal … reason=platform. has_forget_intent alone is not sufficient…
> 2. F4/F5 disposition: content + conversation keyed, never turn-number keyed. … TTL … clear on session switch/shutdown … uncertain → drop. Show the algorithm and the race table…
> 3. F2: no card — two-step confirm + G-AUTHORITY + candidate binding is the control…
> 4. F6: state plainly where candidate labels and tool args persist…
> 5. Conversation identity … self._session_id (FIX-B), never kwargs.
> proceed to phase 3

### Shared predicate (F3 / time_context parity)

```
USER_TURN_PLATFORMS = frozenset({"tui"})  # same constant as time_context

def is_brian_conversation(provider) -> bool:
    platform = (provider._platform or "").lower()
    parent = provider._parent_session_id or ""
    return platform in USER_TURN_PLATFORMS and parent == ""
```

- Set `self._platform` / `self._parent_session_id` in `initialize(**kwargs)` (`platform` from init kwargs; `parent_session_id` from kwargs if present, else `""`).
- Update both in `on_session_switch(new_session_id, *, parent_session_id=…)`.
- **Conversation identity for `on_turn_start` and `handle_tool_call` is always `self._session_id` (FIX-B), never kwargs.**

### 1. Cascade — `forget_cascade(conn, targets, *, reason, terms_source)`

**Inputs**
- `conn`: store connection (caller holds provider lock as today).
- `targets`: list of `{id, kind}` where `kind ∈ {fact, episode, pending_turn}` (entity/link rows are derived, not primary targets).
- `reason`: short code (`remove` | `forget_intent` | `file_check` | `pending_retry` | `tool` | `hold_execute`).
- `terms_source`: optional str — Brian description and/or pre-delete fact texts used for episode/pending matching (never logged).

**Transaction:** one `BEGIN IMMEDIATE` … commit/rollback. Episodes deleted whole (never rewritten).

**Erase order (within the txn)**
1. For each target fact: read text (for terms) → DELETE `fact_history` → `facts_fts` → `facts`.
2. Collect episode IDs via `episode_fact_refs` for erased fact IDs **union** matcher hits on episode text columns (`summary`, `significance`, `open_items_json`, `event_time_evidence`) using distinctive terms (see §2).
3. DELETE those episodes; DELETE their `episode_entities` / `episode_fact_refs`.
4. DELETE `pending_turns` matching terms **or** flagged for this forget (hold / request turn) — Track 5 rows; today tables empty.
5. DELETE `entities` with no remaining `episode_entities` links (and their `entity_aliases`).
6. INSERT one or more content-free `tombstones` with `counts_json`:
   `{fact_rows, history_rows, fts_rows, episode_rows, pending_rows, link_rows, entity_rows}`  
   (`link_rows` = episode_entities + episode_fact_refs deleted).
7. Increment `meta.consolidation_generation` by 1.
8. Clear satisfied `pending_erasures` IDs; on total failure → rollback then best-effort mark pending (Track 2 behavior).

**Track 2 bridge:** `erase_fact(conn, fact_id, *, reason)` becomes a thin wrapper: `forget_cascade(conn, [{id: fact_id, kind: "fact"}], reason=reason, terms_source=None)` reading fact text inside the cascade. Existing tests must pass unchanged (same return bool, same tombstone shape for fact-only erases may gain zeroed episode/pending/link/entity keys — **assertions that require exact counts_json key set will be updated to accept the extended zeros**; listed at Phase 4 if any fail).

### 2. Matcher (episodes / pending_turns)

**Terms**
- From fact text(s) read inside the txn before delete, plus optional Brian `description` on the tool path.
- Tokenize: Unicode letters/digits; keep tokens length ≥ 3; lowercased.
- **Never count (stopwords / always-present):** English function-word stop list (the/a/an/is/…); names **`brian`**, **`zola`**; months/days abbreviations used in stamps; the words `forget`/`delete`/`remove`/`remember`/`please`.
- **Strong terms (E4):** any token with a digit; proper names (capitalized, not sentence-initial, not stopwords). **No** `length ≥ 6 = strong`.

**Match rule (prefer over-erasure):** an episode/pending row matches if **either**
- it references an erased fact ID via `episode_fact_refs`, **or**
- it contains ≥ 1 strong term from the source, **or** ≥ 2 ordinary distinctive terms (substring/word-boundary match on scanned columns).

**No multi-hop:** matching does not expand through entity aliases into further episodes beyond the rows hit in this pass.

**Synthetic corpus (Phase 4; counts only in progress):** ≥ 20 rows (mix of episodes + pending_turns): must-match paraphrases, near-misses (may match), unrelated (must not). Zero misses on must-match required.

### 3. Turn disposition (C1) — F4/F5

**API (Track 5):** `turn_disposition(provider, user_content, *, session_id) -> "keep" | "drop"`.  
Track 4: `sync_turn` calls it and **logs only** (stores nothing).

**State (process memory only, on the provider instance):**
- `_disposition_drops: dict[str, float]` — normalized user-text key → expiry monotonic/unix deadline.
- `_forget_in_session: bool` — true after any forget executed while `self._session_id` current.
- Cleared on: disposition consumed for that key; TTL expiry; `shutdown` only (**not** `on_session_switch` — E1).
- **Never keyed by turn_number. Conversation key = `self._session_id`.**

**Normalize:** NFKC; apply the same skill-scaffold strip Hermes uses when available, else identity; collapse whitespace; casefold. Multimodal/`""` → key `""` (uncertain).

**TTL:** `DISPOSITION_ENTRY_TTL_MINUTES = 30` (aligned with hold).

**Algorithm (`sync_turn` → disposition)** — E1: no session_mismatch short-circuit
1. Expire stale `_disposition_drops` entries.
2. `key = normalize(user_content)`.
3. If `key` in `_disposition_drops` → `drop`, delete key, reason `marked`.
4. Else if `_forget_in_session` and (`key == ""` or normalize-confidence low / empty after strip) → `drop`, reason `uncertain_after_forget`.
5. Else → `keep`, reason `ordinary`.

**Mark for drop:**
- E2: any `on_turn_start` with `has_forget_intent` (Track 2 exclusions) → mark, regardless of outcome.
- Setting a hold during a turn also marks that turn.
- On forget execute (tool or memory-tool cascade): mark current + all held user texts; set `_forget_in_session = True`.

**Race table**

| Race | Covered by |
|---|---|
| sync N finishes after on_turn_start N+1 | Content keys in `_disposition_drops`; N+1 start does not clear N’s key; N’s later sync still `drop` |
| Interrupted turn: on_turn_start, never sync | Entry unused → TTL expiry or shutdown |
| Skill-strip / multimodal ≠ between start message and sync user | Same normalize on mark and sync; if forget-in-session and uncertain → `drop` (fail closed) |
| Forget in turn N, then immediate `/new` or compression, then late sync N | E1: drops survive session switch → late sync N still `drop` |

### 4. Consolidation invalidation

- `meta.consolidation_generation`: integer string, default `"0"`; +1 on every successful cascade commit.
- `begin_consolidation(conn) -> token` where `token = {generation: int, pending_ids: sorted list}`.
- `can_commit(conn, token) -> bool` (E5): false while `meta.pending_erasures` non-empty; else true iff current generation == token.generation **and** current pending_turn ID set == token.pending_ids. Failed cascade still bumps `consolidation_generation` (best-effort separate txn).

### 5. Retry and read suppression

- Failed cascade for fact IDs → `meta.pending_erasures` (JSON list of IDs only) — unchanged Track 2 shape.
- Retry at every file check until commit (existing).
- `is_suppressed(conn, record_ids) -> set[str]`: intersection of `record_ids` with pending_erasures (and, once Track 5 writes episodes, IDs linked to those facts). Track 5 retrieval calls this.

### 6. Clarification hold (C2)

- `meta.forget_hold` JSON: `{session_id, started_at}` — **no content, no labels, no pending texts**.
- Process memory (same provider): `_hold_user_texts: list[str]` (normalized) for turns under the hold; `_candidate_set: dict` (see §7).
- Set hold on authorized `confirm=false` that returns ≥1 candidate.
- While hold active for `self._session_id`: each `on_turn_start` appends normalize(message) to `_hold_user_texts` and marks disposition drop.
- **On execute (`confirm=true` success):** cascade includes matcher + deletes held pending_turn rows when they exist; disposition marks all `_hold_user_texts`; clear hold + candidate set.
- **Hold ends (E3):** `confirm=true` execution; memory-tool `remove` of any fact in the transient candidate set (incl. `notebook_fact` IDs); `HOLD_MAX_TURNS = 3` user turns after the hold is set (4th → keep); `FORGET_HOLD_MAX_MINUTES = 30`; session switch; restart (meta hold + empty candidates → expired). Turns already marked stay dropped. Log `forget_hold` expired/executed.
- Expiry checked: `on_turn_start`, `on_session_switch`, file check start, `begin_consolidation`.

### 7. Tool `forget_memory`

#### F3 — schema visibility (a) + mandatory refuse (b)

**(a) `get_tool_schemas` omit for non-tui**
- Hermes order: `add_provider` → `get_tool_schemas()` (**platform not set yet**) → `initialize_all` (platform known) → `inject_memory_provider_tools` → `get_all_tool_schemas()` → `get_tool_schemas()` **again**.
- Therefore (**Phase 4b / D1**): if `not self._initialized` → return the schema (so `_tool_to_provider` gets a route); after `initialize`, return **`[]` when `not is_brian_conversation()`**, else the schema.
- Effect: cron/sub-path agents that initialize with `platform=cron` (etc.) do **not** get `forget_memory` injected into `agent.tools`. TUI agents do.
- Residual: `_tool_to_provider` may still route the name from the pre-initialize registration — covered by (b).

**(b) Mandatory execution refusal**
- First line of `handle_tool_call` for `forget_memory`: if `not is_brian_conversation()` → refuse JSON, log `forget_tool` `refused_reason=platform`, erase nothing. **Independent of `has_forget_intent`** (cron text may say “delete”).

#### F2 — no approval card
- Live `approvals.mode: manual` does **not** card provider tools (F2).
- **Control plane = two-step `confirm` + G-AUTHORITY + transient candidate binding** (below). Stated as contract: we do not rely on Hermes approval cards for forget.

#### F6 / G-LABELS persistence (Brian knowingly)
- Tool **arguments** (including `description`) appear in Windows **history** (`role: tool` + `args`) and live `tool.start` / `tool.complete` events → persisted in **`state.db` messages / gateway traffic**.
- Tool **results** (including `confirm=false` **candidate labels**) appear in live `tool.complete` and are stored as tool-message content in the session DB; history projection omits result bodies but **args remain**.
- **TTS does not speak** tool args/results.
- Labels are never written to zola `meta`, tombstones, or `zola_memory.log`. Approving G-LABELS means accepting transcript/`state.db` persistence of labels for that turn.

#### Conversation identity
- All authority, hold, and candidate-set checks use **`self._session_id`**, never `handle_tool_call` / `on_turn_start` kwargs.

#### Schema (exact description text)

```json
{
  "name": "forget_memory",
  "description": "Erase provider-held memory copies (index facts, episodes, pending turns) after Brian asks to forget something. Erase-only: never creates or edits notes. Current notebook facts in USER.md/MEMORY.md must be removed with the memory tool's remove action (that path also runs the erase cascade). Two steps: confirm=false to list candidates; confirm=true with target_ids Brian chose. If candidates are different subjects, ask him which one before confirming.",
  "parameters": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "What Brian wants forgotten (his words or a short paraphrase)."
      },
      "confirm": {
        "type": "boolean",
        "description": "false = search and return candidates only; true = erase target_ids from the last candidate list."
      },
      "target_ids": {
        "type": "array",
        "items": {"type": "string"},
        "description": "IDs from the latest confirm=false result. Required when confirm=true."
      }
    },
    "required": ["description", "confirm"]
  }
}
```

#### G-AUTHORITY (adopt as written, proposed)
`confirm=true` executes only when **both**:
1. **Authority:** current `_current_user_message` has `has_forget_intent` **or** an active clarification hold for `self._session_id`; **and** `is_brian_conversation()`;
2. **Bound targets:** every `target_id` ∈ transient candidate set from the latest authorized `confirm=false` for this provider instance.

Otherwise refuse (neutral), erase nothing. Candidate set: process memory only; cleared on execute, hold expiry, session switch, shutdown/restart (restart ⇒ hold treated expired).

#### G-LABELS (adopt as written, proposed)
- `confirm=false` labels: minimal disambiguators only; never logged/tombstoned/meta’d; never echoed on `confirm=true` (IDs/kinds/counts only).
- Brian approves F6 transcript persistence knowingly (above).

#### `confirm=false` result (synthetic examples — fictional)

Example A — single subject:
```json
{"ok": true, "confirm": false, "groups": [{"subject_key": "g1", "ask_brian": false, "candidates": [{"id": "f_syn_01", "kind": "notebook_fact", "action": "use memory remove", "date": "2026-10-01", "label": "cousin, cello"}]}], "message": "One match. Ask Brian to confirm before erasing."}
```

Example B — materially different subjects:
```json
{"ok": true, "confirm": false, "groups": [{"subject_key": "g1", "ask_brian": true, "candidates": [{"id": "f_syn_02", "kind": "notebook_fact", "action": "use memory remove", "date": "2026-09-20", "label": "coworker, Denver"}]}, {"subject_key": "g2", "ask_brian": true, "candidates": [{"id": "e_syn_03", "kind": "episode", "date": "2026-10-02", "label": "project, Nimbus"}]}], "message": "These look like different things. Ask Brian which one he means before calling confirm=true."}
```

#### `confirm=true` result
```json
{"ok": true, "confirm": true, "erased": [{"id": "f_syn_01", "kind": "fact"}], "counts": {"fact_rows": 1, "history_rows": 0, "fts_rows": 1, "episode_rows": 0, "pending_rows": 0, "link_rows": 0, "entity_rows": 0}, "message": "Erased from provider memory. Tell Brian plainly it is gone from your memory; conversation logs still have it."}
```
No labels in this payload.

#### C3 — active fact ID refuse (exact wording)
```json
{"ok": false, "refused_reason": "active_fact", "message": "That ID is a current notebook fact. Use the memory tool remove on USER.md/MEMORY.md; the cascade runs from that notification."}
```

#### Platform refuse wording
```json
{"ok": false, "refused_reason": "platform", "message": "Forget is only available in Brian's interactive conversation."}
```

### 8. `SOUL.md` text (“What I remember”)

Proposed insert (own paragraph) after the existing notebook/search paragraphs:

> When Brian asks me to forget something, I remove it from my notebook rather than rewriting it. If he wants to keep a smaller version, I remove the old note and write the new one separately. If what he names could mean more than one person or thing, I ask which one before erasing anything. For things I remember from our conversations rather than my notebook, I use my forget tool. Every time, I confirm it in one short sentence that also says the conversation itself is still in our chat history, something like "Done — that's gone from my memory, though it's still in our old chat history."

*(Amended: Phase 7b confirmation sentence; Phase 7c ask-first clause unbound from forget-tool sentence.)*

### 9. `MEMORY_CONVENTIONS.md` prose (add under invariants)

Proposed addition:

> Forget: lasting notebook facts are removed with the memory tool’s `remove` (or replaced when Brian wants a smaller version—`replace` with forget intent erases the old copy). The provider erase cascade then deletes every provider-held copy it can find (index rows, history, FTS, and later episodes/pending turns/links) and leaves only content-free tombstones (IDs, kinds, times, counts). The erase-only `forget_memory` tool never writes USER.md/MEMORY.md and refuses active fact IDs so the notebook stays the authority for current facts. Ambiguous targets require clarification before erase. Conversation transcripts in the gateway/`state.db` are outside the cascade and are not rewritten.

### 10. Log events

| Event | Fields (never content/labels) |
|---|---|
| `zola_memory.forget_cascade` | reason, fact_rows, history_rows, fts_rows, episode_rows, pending_rows, link_rows, entity_rows, ok, elapsed_ms |
| `zola_memory.forget_tool` | confirm, candidate_count, group_count, refused_reason (or `-`), ok, elapsed_ms |
| `zola_memory.forget_hold` | action=`set`\|`expired`\|`executed`, held_count, ok |
| `zola_memory.turn_disposition` | decision=`keep`\|`drop`, reason (`ordinary`\|`marked`\|`uncertain_after_forget`), ok |

### Named constants (new)

| Constant | Value |
|---|---|
| `FORGET_HOLD_MAX_MINUTES` | `30` |
| `DISPOSITION_ENTRY_TTL_MINUTES` | `30` |
| `HOLD_MAX_TURNS` | `3` |
| `USER_TURN_PLATFORMS` | `{"tui"}` (shared with time_context) |
| Tool name | `forget_memory` |

### Phase 3 approval (Brian + Claude, verbatim, 2026-10-04)

> Phase 3 contract approved with edits (Brian + Claude). Record verbatim.
> Brian's verdicts: 1 G-AUTHORITY adopt. 2 G-LABELS adopt, F6 transcript/state.db persistence of args + labels accepted knowingly. 3 schema omit (a) + platform refuse (b) adopt. 4 disposition adopt with edits below. 5 SOUL + MEMORY_CONVENTIONS text adopt as proposed. 6 cascade/matcher/hold/results adopt with edits below.
> EDITS (required):
> E1 Disposition — remove algorithm step 1 (session_mismatch → keep). _disposition_drops is NOT cleared on on_session_switch (compression and /new are switches, and a late sync N can arrive after one). Cleared only by consumption, TTL, or shutdown. Add race-table row: forget in turn N, then immediate /new or compression, then late sync N → drop.
> E2 Any turn whose user message has has_forget_intent (Track 2 exclusions apply) is marked drop at on_turn_start, regardless of outcome (zero candidates, refusal, memory-tool path). Setting a hold during a turn also marks that turn. Tests: zero-candidate forget turn → drop; first ambiguous turn → drop.
> E3 Hold ends on: confirm=true execution; a memory-tool remove of any fact in the transient candidate set; HOLD_MAX_TURNS = 3 user turns; 30 min; switch; restart. Turns already marked stay dropped. Test: answer via memory remove ends the hold; the 4th turn after a hold is keep.
> E4 Matcher — drop "length ≥ 6 = strong". Strong = tokens with a digit, or proper names (capitalized, not sentence-initial, not stopwords). Otherwise ≥ 2 distinctive terms. The corpus must include realistic unrelated episodes sharing common words (report over-match rate), and label "must-match" only rows sharing a fact ref, a name, a number, or ≥ 2 distinctive terms. Record plainly that wordless paraphrases are caught only by fact refs (Track 5 input).
> E5 Consolidation — can_commit is false while meta.pending_erasures is non-empty. A failed cascade still bumps consolidation_generation (best-effort separate txn).
> E6 confirm=false lists active notebook facts as kind "notebook_fact" with action "use memory remove"; never accepted in target_ids (C3 refusal unchanged).
> proceed to phase 4

### Effective rulings (recorded)

1. **G-AUTHORITY** and **G-LABELS** adopted; F6 persistence accepted knowingly.
2. **Schema omit (a) + platform refuse (b)** adopted.
3. **Disposition (E1):** no session_mismatch keep; `_disposition_drops` cleared only by consumption / TTL / shutdown — **not** on session switch. Race: forget N → /new or compression → late sync N → drop.
4. **E2:** `has_forget_intent` at `on_turn_start` → mark drop (any outcome); hold set also marks that turn.
5. **E3 hold ends:** confirm=true; memory-tool remove of any candidate-set fact; `HOLD_MAX_TURNS=3`; 30 min; switch; restart. Marked drops remain.
6. **E4 matcher:** strong = digit token or proper name (capitalized, not sentence-initial, not stopword); else ≥2 distinctive terms. Wordless paraphrases only via fact refs (Track 5 input).
7. **E5:** `can_commit` false if `pending_erasures` non-empty; failed cascade still bumps generation (best-effort).
8. **E6:** active facts listed as `notebook_fact` / `use memory remove`; not valid `target_ids`.
9. SOUL + MEMORY_CONVENTIONS text adopted as proposed.
10. Cascade/matcher/hold/results adopted with E1–E6.

## Approved forget contract

Phase 4 builds the **Proposed forget contract** above as amended by Effective rulings E1–E6.

## Matcher corpus results

### Cascade copy matcher (E4 — unchanged by D3)

| Metric | Value |
|---|---|
| must-match rows (Volvo query) | 2 |
| matched | 2 |
| missed | **0** |
| over-matched (unrelated sharing “weekly status report” etc.) | **0** |
| Note | Wordless paraphrases are caught only by fact refs (Track 5 input). |

Strong terms (E4, cascade only): digit-bearing tokens, or proper names (capitalized, not sentence-initial, not stopwords). Otherwise ≥ 2 distinctive ordinary terms. No `length ≥ 6 = strong`.

### Candidate search (D3 — recall-oriented; Phase 4c)

| Probe | Result |
|---|---|
| `"Mara"` | 2 notebook_fact candidates, ≥2 groups, `ask_brian` |
| `"Tobias car"` | Tobias `notebook_fact` listed |
| `"Nimbus project"` | synthetic episode containing “Nimbus” listed |
| stopwords/command-only (`please forget delete remove that`) | 0 candidates |

Search: any distinctive term (stopwords + command words excluded); capitalized tokens count as names in any position. Nothing erased at search time.

## Smoke table

### Phase 6 acceptance (Brian + Claude, verbatim, 2026-10-04)

> Phase 6 accepted (Brian + Claude). proceed to phase 7, run as follows.
> Brian's direction: Cursor performs every check; Brian only types turns and judges tone. G-LIVE stands (Cursor sends no turns).
> …(script + verification plan as in chat)…

### Part A baselines (Cursor, pre-Brian)

| Check | Value |
|---|---|
| `zola_memory.log` offset | **33641** bytes / **342** lines |
| Tombstones | **5** |
| Facts (active) | **14** |
| `USER.md` SHA-256 | `47a732a0b218936c9b465f6bb8ada34bcda4fe027660f000e9b139b4e7022d12` (2156 bytes) |
| `MEMORY.md` SHA-256 | `8264268512e5cc7a37fff847f523ca142c310dbf21bef30c2ad601ee3a5986eb` (236 bytes) |
| F8 provider tools | **`['forget_memory']` only** ✅ |

### Part B script (Brian — Text mode, **new conversation**)

| Step | Brian types |
|---|---|
| 1 | Remember that my neighbor Tobias Wren drives a green 1971 Volvo P1800. |
| 2 | Forget the thing about Tobias's car. |
| 3 | Remember my cousin Mara is learning the cello. |
| 4 | Remember my coworker Mara just moved to Denver. |
| 5 | Forget what I told you about Mara. |
| 6 | The cousin one. |
| 7 | Remember that my friend Dana Okafor restores old Vespas. |
| 8 | Dana sold the last Vespa, take that out of your notes. |
| 9 | Forget about my coworker Mara too. |
| 10 | Any ideas for dinner tonight? |

### Brian tone notes (verbatim)

| Step | Brian |
|---|---|
| 2 | response: It's gone from my memory. |
| 5 | response: Do you mean your cousin learning cello, your coworking moving to Denver or both? |
| 6 | response: Gone |

### Per-step verification (session `20261004_211943_725b38`)

| Step | Expected | Result |
|---|---|---|
| 1 Tobias remember | memory add; fact indexed | ✅ `fact_add` `10ba49d8…` target=user; disposition **keep** |
| 2 Tobias forget | remove → cascade ok → +1 tombstone; disposition drop | ✅ `forget_cascade reason=remove ok=true`; erase `10ba49d8…`; tombs 5→6; disposition **drop** |
| 3 cousin Mara | memory add; fact indexed | ✅ `fact_add` `6c24a25c…`; **keep** |
| 4 coworker Mara | memory add; fact indexed | ✅ `fact_add` `5b4bfb6e…`; **keep** |
| 5 Forget Mara | no erase before step 6; if tool: confirm=false, 2 cands, ask_brian; drop | ✅ **No erase** (no cascade/remove before step 6). Disposition **drop**. **Deviation:** `forget_memory` **never called** — she clarified in natural language (Brian’s wording). No `forget_tool` / `forget_hold` log lines. |
| 6 The cousin one | only cousin removed; coworker remains; hold ended; drop | ✅ cascade/remove `6c24a25c…` (cousin) after step-6 `on_turn_start`; coworker `5b4bfb6e…` still present until step 9; disposition **drop**. **Deviation:** erase via **memory remove**, not `forget_memory` confirm=true — no hold set/executed. |
| 7 Dana remember | memory add; fact indexed | ✅ `fact_add` `c8a72157…`; **keep** |
| 8 Dana remove (D2) | remove → cascade; drop without forget words | ✅ cascade `reason=remove` `c8a72157…`; disposition **drop** |
| 9 coworker Mara forget | coworker removed; drop | ✅ cascade/remove `5b4bfb6e…`; disposition **drop** |
| 10 dinner | disposition keep | ✅ disposition **keep** `reason=ordinary` |

**Authority:** zero `forget_tool` events in the smoke window → no `confirm=true` outside intent/hold; no unbound target IDs. ✅

**Incidental turns (not in script; report only):** after step 5, voice interrupt note `Oh` (2 chars) → keep; after step 6, voice `Gone.` (5 chars) → keep.

### Part C

| Check | Result |
|---|---|
| Byte scan tombstones + meta + `zola_memory.log` for Tobias/Wren/Volvo/P1800/Mara/cello/Denver/Dana/Okafor/Vespa | **zero hits** ✅ |
| USER.md / MEMORY.md contain none of those strings at end | ✅ |
| Files changed only via memory tool | ✅ (only `memory` tool on forget/add paths; no approval card) |
| Tombstones end | **9** (+4 vs Part A baseline 5) ✅ |
| Active facts end | **14** (same count; smoke facts fully removed) |

### Phase 7 notes

- Smoke used **memory tool remove** for all erasures; provider `forget_memory` tool was not exercised live (ambiguous Mara handled in dialogue).
- D2 live path (step 8) confirmed: disposition drop without forget-intent phrases.
- No code fixes applied for deviations.

### Phase 7 review (Brian + Claude, verbatim, 2026-10-04)

> Phase 7 review (Brian + Claude): machinery PASS on every step. Deviations 5/6 accepted as correct design (notebook facts → in-dialogue clarification + memory remove; forget_memory/hold reserved for episode memory, live proof deferred to P6-EPISODES).
> FAIL (P6-D06 / exit criterion): confirmations didn't mention the conversation history ("It's gone from my memory." / "Gone").
> Phase 7b — SOUL fix (P4-D25: back up, apply, mirror):
> Replace the last sentence of the approved forget paragraph ("Then I tell him plainly that it's gone from my memory, though our past conversation logs still have it.") with exactly:
> "Every time, I confirm it in one short sentence that also says the conversation itself is still in our chat history, something like "Done — that's gone from my memory, though it's still in our old chat history.""
> Mirror to identity/SOUL.md (own paragraph). Show the diff + hashes, apply, relaunch, G6 recheck (prompt delta = this sentence only).
> Then Brian retests (new conversation, Text):
> 1 "Remember that my friend Priya Lund keeps bees."
> 2 "Forget about Priya's bees."
> 3 "Remember my aunt Rosa paints and my neighbor Rosa runs marathons."
> 4 "Forget what I said about Rosa." → she asks which → "Both."
> 5 "Sounds good, thanks."
> Cursor verifies cascades/drops/byte scan as in Phase 7; Brian reports whether 2 and 4 mention the chat history naturally.
> Brian's tone notes on Phase 7 steps 2/5/6 (verbatim): "________"
> STOP with PHASE 7b COMPLETE.

### Effective rulings (Phase 7 review)

1. Machinery PASS; deviations 5/6 accepted (notebook → dialogue + `memory` remove; `forget_memory`/hold deferred to P6-EPISODES).
2. P6-D06 FAIL on confirmation wording → Phase 7b SOUL sentence replace (exact text above).
3. Retest script as listed; Brian judges whether steps 2 and 4 mention chat history naturally.

## Phase 7b — SOUL confirmation fix

### Diff (live `SOUL.md` vs `SOUL-phase7b-pre.md`)

```diff
-…ask before erasing. Then I tell him plainly that it's gone from my memory, though our past conversation logs still have it.
+…ask before erasing. Every time, I confirm it in one short sentence that also says the conversation itself is still in our chat history, something like "Done — that's gone from my memory, though it's still in our old chat history."
```

(Sole content hunk; em-dashes elsewhere unchanged.)

### Hashes

| Artifact | SHA-256 |
|---|---|
| Backup `SOUL-phase7b-pre.md` | `aa0181b3e00c990264e6b203b0a48426cc72b5cd104837e8078e9e986e6b28cf` |
| Live `SOUL.md` after apply | `afacd15738676e033486293e4ba982610c99a37d00fec58c0f0709187314a7b3` |
| `identity/SOUL.md` mirror | `afacd15738676e033486293e4ba982610c99a37d00fec58c0f0709187314a7b3` (byte-equal to live) |
| `config.yaml` | `7ba2e676…` unchanged |

### G6 recheck (7b)

Offline captures: `zola-spikes/p6-forget/g6-7b-before/`, `g6-7b-after/`. Allowlisted: `Conversation started:` only.

| Check | Result |
|---|---|
| Tool-name set | ✅ identical (20; includes `forget_memory`) |
| Provider schemas | ✅ `['forget_memory']` only |
| Prompt after allowlist strip | ✅ differs by **exactly** the confirmation sentence swap (`after_equals_before_with_sentence_swap True`) |
| Live load | ✅ one `initialize ok=true` at 21:33:53; registered (1 tools) + activated once; `on_turn_start` = 0 (G-LIVE) |

### Part A baselines (7b retest, pre-Brian)

| Check | Value |
|---|---|
| `zola_memory.log` offset | **48244** bytes / **486** lines |
| Tombstones | **9** |
| Facts (active) | **14** |
| `USER.md` SHA-256 | `47a732a0…` (2156) |
| `MEMORY.md` SHA-256 | `82642685…` (236) |

### Part B script (Brian — Text mode, **new conversation**)

| Step | Brian types |
|---|---|
| 1 | Remember that my friend Priya Lund keeps bees. |
| 2 | Forget about Priya's bees. |
| 3 | Remember my aunt Rosa paints and my neighbor Rosa runs marathons. |
| 4 | Forget what I said about Rosa. → (she asks which) → Both. |
| 5 | Sounds good, thanks. |

### Brian tone notes (7b, verbatim)

| Step | Brian |
|---|---|
| 2 | Done — that’s gone from my memory, though it’s still in our old chat history. |
| 4 | Done — both Rosa details are gone from my memory, though they’re still in our old chat history. (She did not ask which one) |
| Phase 7 steps 2/5/6 (verbatim) | ________ |

### Per-step verification (7b, session `20261004_213345_e1ca3d`)

| Step | Expected | Result |
|---|---|---|
| 1 Priya remember | memory add; keep | ✅ `fact_add` `ecba8e10…`; disposition **keep** |
| 2 Priya forget | cascade remove; drop; confirmation mentions chat history | ✅ `forget_cascade reason=remove`; erase `ecba8e10…`; disposition **drop**; tone mentions old chat history |
| 3 Rosa remember (aunt + neighbor) | facts indexed; keep | ✅ one notify add then file_check split to `98247da1…` + `fe383308…` (aunt/neighbor); keep on remember turn |
| 4 Forget Rosa → ask → Both | no erase before clarify; then both removed; drop; history in confirm | ⚠️ **Deviation:** erased **both** on the forget turn **without asking** (Brian: “She did not ask which one”). Both cascades `reason=remove` ok. Confirmation mentions chat history. **Disposition keep/ordinary** (not drop) — report only. “Both.” never typed. |
| 5 Sounds good | keep | ✅ disposition **keep** |

**Incidental turns (report only):** voice echo of step-2 confirm as user turn (`Done, that's gone…`); mid–step-4 echo of remember text as user. Skill-library background turn after Rosa remember.

**Authority / Part C**

| Check | Result |
|---|---|
| `forget_tool` / `forget_hold` in window | none ✅ |
| Byte scan DB + log + USER/MEMORY for Priya/Lund/bees/Rosa/paints/marathons | **zero hits** ✅ |
| End USER/MEMORY hashes | match 7b Part A (`47a732a0…` / `82642685…`) ✅ |
| Tombstones | **13** (+4 vs 7b Part A baseline 9) ✅ |
| Active facts | **14** ✅ |

### Phase 7b notes (close)

- P6-D06 confirmation wording: **PASS** on steps 2 and 4 (chat history mentioned).
- Ambiguous Rosa: she chose both without clarify — report only; no code fix.
- Phase 7b review → Phase 7c (disposition keep + SOUL clarify scope).

## Phase 7c — investigation (STOP; nothing applied)

### Phase 7b review (Brian + Claude, verbatim, 2026-10-04)

> Phase 7b review (Brian + Claude): history wording PASS (P6-D06). Two issues at step 4 — Phase 7c.
> 7c-1 DEFECT (code): … Investigate … Report root cause with evidence BEFORE fixing. Then fix + a unit test…
> 7c-2 SOUL: … Show the full revised paragraph + diff at the STOP; apply only after Brian approves…
> STOP after the root cause + proposed SOUL paragraph (PHASE 7c STOP).

### 7c-1 Root cause (evidence)

Session `20261004_213345_e1ca3d`, forget-Rosa turn:

| Event | Evidence |
|---|---|
| `on_turn_start` | `turn_number=5` `msg_len=30` (forget intent) → E2 `mark_drop` on that text |
| Cascades | two `forget_cascade reason=remove ok=true` → D2 also `mark_drop(_current_user_message)` (still the 30-char turn message; echo had **no** second `on_turn_start`) |
| `sync_turn` | `user_len=145` `assistant_len=95` |
| `turn_disposition` | `decision=keep reason=ordinary` |

**Mechanism:** Mid-turn voice echo (80 chars) was applied as an active-turn **redirect**. Hermes rewrote `original_user_message` in `turn_iteration_prep.begin_iteration` to:

`"{forget}\n\nUser correction during the turn: {echo}"` → **exactly 145** chars.

`normalize_disposition_key(on_turn_start msg)` ≠ `normalize_disposition_key(sync user_content)` (compared in memory; keys unequal). Marks sit on the 30-char key; sync looks up the 145-char key → miss → `keep`/`ordinary`.

Unit tests / Claude repro use the **same** string for `on_turn_start` and `sync_turn`, so they always get `drop`. Live path differs when redirect augments sync text.

**Fail-closed note:** `has_forget_intent(sync_user_content)` is still **True** on this shape (forget text preserved at the front). Approved fix applied below (exact / contained / intent).

### 7c-2 SOUL paragraph (approved; applied below)

**Full revised paragraph:**

> When Brian asks me to forget something, I remove it from my notebook rather than rewriting it. If he wants to keep a smaller version, I remove the old note and write the new one separately. If what he names could mean more than one person or thing, I ask which one before erasing anything. For things I remember from our conversations rather than my notebook, I use my forget tool. Every time, I confirm it in one short sentence that also says the conversation itself is still in our chat history, something like "Done — that's gone from my memory, though it's still in our old chat history."

**Diff vs current live/identity:**

```diff
-When Brian asks me to forget something, I remove it from my notebook rather than rewriting it. If he wants to keep a smaller version, I remove the old note and write the new one separately. For things I remember from our conversations rather than my notebook, I use my forget tool, and if it isn't clear exactly what he means, I ask before erasing. Every time, I confirm it in one short sentence that also says the conversation itself is still in our chat history, something like "Done — that's gone from my memory, though it's still in our old chat history."
+When Brian asks me to forget something, I remove it from my notebook rather than rewriting it. If he wants to keep a smaller version, I remove the old note and write the new one separately. If what he names could mean more than one person or thing, I ask which one before erasing anything. For things I remember from our conversations rather than my notebook, I use my forget tool. Every time, I confirm it in one short sentence that also says the conversation itself is still in our chat history, something like "Done — that's gone from my memory, though it's still in our old chat history."
```

### Phase 7c approval (Brian + Claude, verbatim, 2026-10-04)

> Phase 7c root cause accepted (Brian + Claude). Approved:
> FIX … turn_disposition drops when ANY of: (a) exact key; (b) marked key CONTAINED in sync; (c) has_forget_intent(user_content). Consume on a/b. Tests… SOUL 7c-2 approved verbatim… Redeploy… Record for lore: voice echo injected as User correction… open question for closeout. Then Brian retests… Voice/mic off… STOP with PHASE 7c COMPLETE.

### Effective rulings

1. `turn_disposition` fail-closed: exact / contained / forget-intent; consume on a/b.
2. SOUL 7c-2 ask-first sentence approved verbatim; applied under P4-D25.
3. Lore note (not this track): TTS echo → “User correction during the turn” barge-in loop — open for closeout.
4. Retest with **voice/mic off**.

### Fix applied (repo + live)

- `forget.py` `turn_disposition`: reasons `marked` | `marked_contained` | `forget_intent`.
- Tests: `test_7c_redirect_augmented_{forget_drops,d2_remove_drops,ordinary_keeps}` — both suites **79 OK**.

| File | SHA-256 | Match |
|---|---|---|
| `forget.py` (repo = live) | `8bb9de8b7d98e3750a7f10bc9a1b019e63d6d42b0c39fcfd32f5bdea91045afd` | ✅ |
| Backup pre-7c live forget | `eaa89aae…` | — |

### SOUL 7c-2 apply

| Artifact | SHA-256 |
|---|---|
| Backup `SOUL-phase7c-pre.md` | `afacd157…` |
| Live + identity (byte-equal) | `e2b932a9d10dd6b9267530737fe8e438c8003b74032aeb21004093fd89b24d52` |

### G6 recheck (7c)

Captures: `g6-7b-7c-before/`, `g6-7b-7c-after/`. Allowlisted: `Conversation started:` only.

| Check | Result |
|---|---|
| Tools / provider schemas | ✅ identical (`forget_memory` only) |
| Prompt after allowlist | ✅ differs by **exactly** the approved paragraph swap |
| Live load | ✅ `initialize` 21:44:55; registered+activated once; `on_turn_start`=0 |

### Part A baselines (7c retest, pre-Brian)

| Check | Value |
|---|---|
| `zola_memory.log` offset | **56863** bytes |
| Tombstones | **13** |
| Facts (active) | **14** |
| USER / MEMORY | `47a732a0…` / `82642685…` |

### Part B script (Brian — Text, **new conversation**, voice/mic **off**)

| Step | Brian types | Expected disposition |
|---|---|---|
| 1 | Remember my aunt Rosa paints and my neighbor Rosa runs marathons. | keep |
| 2 | Forget what I said about Rosa. | drop (she should ask which) |
| 3 | The neighbor. | drop via D2 remove mark (keep acceptable only if no hold/no remove) |
| 4 | Forget about my aunt Rosa too. | drop |
| 5 | Thanks. | keep |

### Brian tone / ask note (7c, verbatim)

> Done. Step 2, she didn't ask which Rosa still.

### Per-step verification (7c, session `20261004_214449_eb264b`)

| Step | Expected | Result |
|---|---|---|
| 1 Rosa remember | keep | ✅ two `fact_add` (aunt+neighbor); disposition **keep** |
| 2 Forget Rosa | drop; she should ask which | ✅ disposition **drop** `reason=marked`; history confirm present. ⚠️ **SOUL ask-first FAIL:** erased **both** without asking (Brian). Two cascades `reason=remove`. |
| 3 The neighbor. | drop via D2 if remove; keep OK if no remove | ⚠️ disposition **keep** `ordinary` — no remove; she **restored** aunt (`fact_add`) saying she misunderstood. Keep acceptable (no D2 remove). |
| 4 Forget aunt too | drop | ✅ cascade remove; disposition **drop** `reason=marked`; history confirm |
| 5 Thanks | keep | ✅ **keep** |

**Authority / Part C**

| Check | Result |
|---|---|
| Mic/redirect | voice off; sync `user_len` matched `on_turn_start` (no redirect wrap) ✅ |
| Byte scan Rosa/paints/marathons in DB+log+USER/MEMORY | **zero hits** ✅ |
| End USER/MEMORY hashes | match Part A ✅ |
| Tombstones | **16** (+3 vs Part A 13) ✅ |
| Active facts | **14** ✅ |

### Phase 7c notes (close)

- Disposition fail-closed **PASS** (steps 2/4 drop; no redirect this retest).
- Step 2 ask-first: accepted as model judgment (Brian) — see Lore inputs.
- Smoke test passed → proceed to closeout.

### Phase 7c acceptance (Brian + Claude, verbatim, 2026-10-04)

> Phase 7c accepted (Brian + Claude). Claude verified the deployed turn_disposition implements a/b/c (exact, contained, forget-intent).
> Step 2 ask-first: accepted as model judgment (Brian's call). Record under Lore inputs: "Notebook-fact clarification is SOUL-guided judgment, not enforced. When two same-named facts arrive in one sentence, 'forget what I said about X' was read as that statement (erased both; restored the aunt on correction). With separate messages (Mara) she asked. Episode-memory clarification is enforced by the tool (ask_brian groups + G-AUTHORITY target binding)."
> Also record for lore: voice echo injected as "User correction during the turn" (open question); live episode-only forget deferred to P6-EPISODES.
> Smoke test passed. proceed to closeout

## Lore inputs (for later lore; **no lore edits this track**)

1. **Notebook-fact clarification is SOUL-guided judgment, not enforced.** When two same-named facts arrive in one sentence, "forget what I said about X" was read as that statement (erased both; restored the aunt on correction). With separate messages (Mara) she asked. Episode-memory clarification is enforced by the tool (`ask_brian` groups + G-AUTHORITY target binding).
2. **Voice echo** injected as `"User correction during the turn"` (TTS heard by mic / barge-in loop) — **open question**.
3. **Live episode-only forget** deferred to **P6-EPISODES**.

## Phase 8 — Closeout

### 8a Verify

| Check | Result |
|---|---|
| `zola_memory` unit tests | **79 OK** |
| `zola_tools` unit tests | **44 OK** |
| `dotnet build … -r win-x64` | **PASS** (0 warnings / 0 errors) |
| `hermes-agent` | clean at `345cd2b057a452236de401d3534b8502a7465e8d` |

### 8c Deploy + identity re-verify

| File | Repo = Live SHA-256 |
|---|---|
| `__init__.py` | `99eb18f3bedd5cc8abc408233e33b3d7eb591b1293397b7c5f1836bb293cd550` |
| `provider.py` | `c1dae292eeddddac3eec5bda82d2d9adc0098b2e0f2df3483f1d13dd23f3d108` |
| `forget.py` | `8bb9de8b7d98e3750a7f10bc9a1b019e63d6d42b0c39fcfd32f5bdea91045afd` |
| `fact_index.py` | `49d321a3b371ff61f5763a9b79acf187ea64caec0d04ee54bbbab793ee1afc0e` |
| `log.py` | `d274baba8d9a696c95fffc3b2e43a50974739662c18ef8a8b735a356e876faca` |
| `time_context.py` | `c3b61942358cccec6db422b31b7200c8d743c095779b144db9b174bf105bbf9f` |
| `registry.py` | `86aa4da04d67ab911d569ab1d9774a86e1a36f75f9b1931d49ca3f0272ee771d` |
| `store.py` / `llm_access.py` | Track 2 hashes MATCH |
| `SOUL.md` live + `identity/SOUL.md` | `e2b932a9d10dd6b9267530737fe8e438c8003b74032aeb21004093fd89b24d52` (byte-equal) |
| `identity/MEMORY_CONVENTIONS.md` | `31bacf1eeffddffb99d49a48c2d9172c5cd4e6f4956dedf3462fc378495db2ca` |

### Exit criteria verification (PHASE6_BUILD_PLAN.md Track 4 + C1–C4)

| Criterion | Verdict | Evidence |
|---|---|---|
| Unit (a) remove cascade | ✅ | `test_forget_phase4` remove/cascade paths |
| Unit (b) replace+forget-intent | ✅ | Phase 4 suite |
| Unit (c) bypass disappearance | ✅ | file_check erase path |
| Unit (d) episode-only via tool | ✅ | synthetic episodes in suite; **live** deferred |
| Unit (e) ambiguous → groups, no execute | ✅ | Mara/`ask_brian` tests; confirm=false |
| Unit (f) consolidation cannot commit | ✅ | E5 / `can_commit` tests |
| Unit (g) failed cascade + retry/suppress | ✅ | pending_erasures / suppress tests |
| Unit (h) hold expiry discards | ✅ | E3 hold tests |
| Unit (i) tombstones/logs no synthetic content | ✅ | byte-scan tests + live Part C |
| Unit (j) tool writes only deletes+tombstones | ✅ | no INSERT outside tombstones tests |
| CURSOR: only `forget_memory` provider tool | ✅ | G6 + Part A F8 |
| HUMAN: forget → remove/cascade + history wording | ✅ | Phase 7/7b/7c; P6-D06 wording PASS after 7b |
| HUMAN: ambiguous asks before erase | ⚠️ | Mara (separate msgs) asked; Rosa one-sentence both erased — **accepted as SOUL judgment** (Brian) |
| Live episode-only forget | ⚠️ | deferred to P6-EPISODES (Brian-approved) |
| Deploy hashes + identity mirrors | ✅ | 8c table |
| hermes clean; no client source changes | ✅ | hermes clean; no `windows-client/**` source edits |
| C1 disposition on forget turn | ✅ | drop on forget; keep on ordinary; 7c fail-closed |
| C2 held turns erased on execute | ✅ | unit hold/execute tests |
| C3 refuse active fact IDs | ✅ | unit C3 refuse |
| C4 no episode FTS; scan columns | ✅ | matcher scans text columns |
| G-AUTHORITY | ✅ | confirm=true bound to candidates; no unbound live erases via tool |

All Track 4 criteria met (with approved ⚠️): **YES**. Unit tests: **PASS**.

### Closeout SHAs

*(filled as commits land)*

- Implementation commit (8f): `31cca800d526bfbfaa37751a099ef47140bc6bf9`
- Docs record implementation SHA (8g): `70106fb47c434dcb6548bbd95bd13be276490d78`
- Merge SHA on main (8i): *(pending)*
- Docs record merge SHA (8j): *(pending)*

## Unit test summary

### Phase 1 baseline (pre-build)

| Suite | Result |
|---|---|
| `zola_memory` | Ran 53 tests — OK |
| `zola_tools` | Ran 44 tests — OK |

### Phase 4 (post-build)

| Suite | Result |
|---|---|
| `zola_memory` | **Ran 72 tests — OK** (53 prior + 19 Phase 4) |
| `zola_tools` | **Ran 44 tests — OK** |

Covered: (a)–(q) including E2 zero-candidate/ambiguous drop, E3 memory-remove ends hold + 4th turn keep, E4 corpus zero misses, E5 can_commit/generation bump, E6 notebook_fact listing + C3 refuse, G-AUTHORITY/G-LABELS, schema omit + platform refuse.

### Phase 4b (defect fixes)

| Suite | Result |
|---|---|
| `zola_memory` | **Ran 74 tests — OK** (+ D1 Hermes-order routing; + D2 notify mark) |
| `zola_tools` | **Ran 44 tests — OK** |

**D1 (Brian + Claude):** `get_tool_schemas` returned `[]` pre-initialize (`_platform == ""`), so `add_provider` never routed `forget_memory`; live calls failed “No memory provider handles tool”. Fix: return schema while `not self._initialized`; after initialize, omit for non-Brian; platform refuse (b) unchanged.

**D2 (Brian + Claude):** memory-tool `remove` / replace-with-forget-intent committed a cascade but left disposition `keep` when the user message lacked Track-2 forget phrases. Fix: `mark_after_notify_cascade` sets `forget_in_session` + `mark_drop(current)` on successful notification-path erases only (not file-check/bypass).

## Phase 4 notes

- Built approved contract + E1–E6 in repo only (`forget.py`, `provider.py`, `fact_index.py`, `log.py`, `registry.py`, tests).
- `erase_fact` → thin `forget_cascade` wrapper; existing Track 2 erase tests pass.
- Disposition drops survive `/new`/compression (session switch); hold ends on switch/restart/TTL/`HOLD_MAX_TURNS`/execute/memory-remove of candidate.
- Nothing deployed; live profile untouched.
- Phase 5 not started.

## Phase 4b notes

- Repo-only fixes for D1/D2; progress updated; nothing deployed.
- Phase 5 not started.

### Phase 4c (D3 search recall)

| Suite | Result |
|---|---|
| `zola_memory` | **Ran 75 tests — OK** (+ D3 search recall) |
| `zola_tools` | **Ran 44 tests — OK** |

**D3 (Brian + Claude):** `search_candidates` used the cascade matcher (`derive_terms` + ≥2 ordinary / strong), so short descriptions starting with a name (`"Mara"`, `"Tobias car"`) returned no matches (fails open). Fix (search side only): `derive_search_terms` / `row_matches_search` — any distinctive term; capitalized tokens count regardless of position; cascade matcher unchanged.

## Phase 4c notes

- Repo-only; cascade E4 corpus re-checked (miss=0, over=0).
- Nothing deployed; Phase 5 not started.

### Phase 4d (label ranking)

| Suite | Result |
|---|---|
| `zola_memory` | **Ran 76 tests — OK** |
| `zola_tools` | **Ran 44 tests — OK** |

`_short_label`: tier names (capitalized, any position) + digit tokens, then description matches, then others; within a tier prefer matched terms (so “Nimbus” beats sentence-initial “Talked”). Groups key on full label so cousin/coworker Mara stay distinguishable. G-LABELS unchanged (labels still never logged/tombstoned/meta’d).

## Phase 5 proposals (awaiting Brian's approval)

### 1. Redeploy file list (repo vs live)

Live root: `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\`

| File | Repo SHA-256 | Live SHA-256 | Action |
|---|---|---|---|
| `__init__.py` | `99eb18f3bedd5cc8abc408233e33b3d7eb591b1293397b7c5f1836bb293cd550` | `33f589199006e47484c90291d1fc908e945a52f0fc5e8dbc4804b9b5e354bce5` | REPLACE |
| `provider.py` | `c1dae292eeddddac3eec5bda82d2d9adc0098b2e0f2df3483f1d13dd23f3d108` | `eeedf6cecb730e70c23629a57cc0a26e4e0943d0632d7faf947381bbff94069d` | REPLACE |
| `forget.py` | `eaa89aae9edc7dda36c44b0cbbb620b529c8d0069ccedeba75229590b15883f6` | `1e50246501f9274190426961d4526ca84ebeff7b3a580b9f63f6c514a5663d7c` | REPLACE |
| `fact_index.py` | `49d321a3b371ff61f5763a9b79acf187ea64caec0d04ee54bbbab793ee1afc0e` | `b6dd9710fe776b21fa963878929acfdd134888384c772746ba687c33bf23cb24` | REPLACE |
| `log.py` | `d274baba8d9a696c95fffc3b2e43a50974739662c18ef8a8b735a356e876faca` | `af6d9645c8eef2a176c67a64d0b7134b563149cdc30768ee1d43d39d198f6229` | REPLACE |
| `time_context.py` | `c3b61942358cccec6db422b31b7200c8d743c095779b144db9b174bf105bbf9f` | `d9309043804e14f392f8be93ef4c8e5090eb2950828fbeeb34c454f380eaa71c` | REPLACE |
| `registry.py` | `86aa4da04d67ab911d569ab1d9774a86e1a36f75f9b1931d49ca3f0272ee771d` | *(absent)* | ADD |
| `store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` | same | unchanged |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | same | unchanged |

No `plugin.yaml` in this plugin folder (unchanged / absent both sides).

### 2. Exact `SOUL.md` diff (“What I remember”)

Insert as **its own paragraph** after the existing conversation-search paragraph (end of `## What I remember`), approved Phase 3 text:

```diff
 When Brian asks about something from an earlier conversation and it isn't in my notebook, I search
 our past conversations and tell him roughly when it was. I don't go through past conversations on my
 own.
+
+When Brian asks me to forget something, I remove it from my notebook rather than rewriting it. If he wants to keep a smaller version, I remove the old note and write the new one separately. For things I remember from our conversations rather than my notebook, I use my forget tool, and if it isn't clear exactly what he means, I ask before erasing. Then I tell him plainly that it's gone from my memory, though our past conversation logs still have it.
```

Mirror the same paragraph to `identity/SOUL.md` (byte match apart from line endings; today live vs identity are LF-normalized equal at `9f4fe469…` / `56e203cf…`).

### 3. Exact `identity/MEMORY_CONVENTIONS.md` diff

Add under **Structured store (P6)** invariants (after the existing “Invariants in short…” paragraph):

```diff
 and unclear "replace vs forget" cases resolve toward erasure. Retrieval never becomes
 persistence.
+
+Forget: lasting notebook facts are removed with the memory tool’s `remove` (or replaced when Brian wants a smaller version—`replace` with forget intent erases the old copy). The provider erase cascade then deletes every provider-held copy it can find (index rows, history, FTS, and later episodes/pending turns/links) and leaves only content-free tombstones (IDs, kinds, times, counts). The erase-only `forget_memory` tool never writes USER.md/MEMORY.md and refuses active fact IDs so the notebook stays the authority for current facts. Ambiguous targets require clarification before erase. Conversation transcripts in the gateway/`state.db` are outside the cascade and are not rewritten.
 
 (P6-D01–D07)
```

Live profile has no separate `MEMORY_CONVENTIONS.md` apply path beyond the identity mirror (same as prior tracks): apply to `identity/MEMORY_CONVENTIONS.md` in repo; no live copy expected unless one already exists (none today).

### 4. Config key

**None.** `config.yaml` stays `7ba2e676a04ff92047c8d711fcb022be8a532b11baac6f74b08986744e704570`. `memory.provider: zola_memory` unchanged. No `approvals.*` change.

### 5. Rollback

1. Restore `plugins/zola_memory/` from the Phase 6 backup (pre-FORGET live hashes in the Live column of §1 — Track 3 + FIX-B baseline).
2. Restore live `SOUL.md` from the Phase 6 backup.
3. Relaunch the client.
4. Tombstones written during smoke stay (content-free). `config.yaml` / `approvals.*` / `zola_tools` / `hermes-agent` untouched on the forward path.

## Approved live changes

### Phase 5 approval (Brian + Claude, verbatim, 2026-10-04)

> Phase 5 approved as proposed (Brian + Claude). Claude verified all 9 repo hashes match the deploy table (7 replace/add, store.py + llm_access.py unchanged) and the 4d labels (Mara cousin/coworker distinct; Nimbus episode → "nimbus, …").
> 1–5 approved verbatim. SOUL.md mirror goes in as its own paragraph. Do not send any turn after relaunch (G-LIVE).
> proceed to phase 6

### Effective rulings (recorded)

1–5 approved as proposed. SOUL mirror = own paragraph. No turns after relaunch.

## Backup hashes

Backup dir: `C:\Users\test\Dev\zola-spikes\p6-forget\backup\` (2026-10-04)

| Artifact | SHA-256 |
|---|---|
| `SOUL.md` (pre-edit) | `9f4fe469b4bac7a014bf245ebb226a0a178aa29179ea551c11a3bee126f0a2fc` |
| `zola_memory.db` (sqlite3.backup API) | `5062e0f94d4246bdc4f55391a1aba67d8e635df13de20d78e7908e29093f55da` (155,648 bytes) |
| `plugins_zola_memory/__init__.py` | `33f589199006e47484c90291d1fc908e945a52f0fc5e8dbc4804b9b5e354bce5` |
| `plugins_zola_memory/provider.py` | `eeedf6cecb730e70c23629a57cc0a26e4e0943d0632d7faf947381bbff94069d` |
| `plugins_zola_memory/forget.py` | `1e50246501f9274190426961d4526ca84ebeff7b3a580b9f63f6c514a5663d7c` |
| `plugins_zola_memory/fact_index.py` | `b6dd9710fe776b21fa963878929acfdd134888384c772746ba687c33bf23cb24` |
| `plugins_zola_memory/log.py` | `af6d9645c8eef2a176c67a64d0b7134b563149cdc30768ee1d43d39d198f6229` |
| `plugins_zola_memory/time_context.py` | `d9309043804e14f392f8be93ef4c8e5090eb2950828fbeeb34c454f380eaa71c` |
| `plugins_zola_memory/store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` |
| `plugins_zola_memory/llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` |

## Deployed-file hash table

Live path: `%LOCALAPPDATA%\hermes\profiles\zola\plugins\zola_memory\` — all MATCH repo:

| File | Live SHA-256 | Match |
|---|---|---|
| `__init__.py` | `99eb18f3bedd5cc8abc408233e33b3d7eb591b1293397b7c5f1836bb293cd550` | ✅ |
| `provider.py` | `c1dae292eeddddac3eec5bda82d2d9adc0098b2e0f2df3483f1d13dd23f3d108` | ✅ |
| `forget.py` | `eaa89aae9edc7dda36c44b0cbbb620b529c8d0069ccedeba75229590b15883f6` | ✅ |
| `fact_index.py` | `49d321a3b371ff61f5763a9b79acf187ea64caec0d04ee54bbbab793ee1afc0e` | ✅ |
| `log.py` | `d274baba8d9a696c95fffc3b2e43a50974739662c18ef8a8b735a356e876faca` | ✅ |
| `time_context.py` | `c3b61942358cccec6db422b31b7200c8d743c095779b144db9b174bf105bbf9f` | ✅ |
| `registry.py` | `86aa4da04d67ab911d569ab1d9774a86e1a36f75f9b1931d49ca3f0272ee771d` | ✅ NEW |
| `store.py` | `6c8c488c1ab0d731b60f09f7d76e020d1026945f9db5395622244b6846e393f7` | ✅ |
| `llm_access.py` | `ec5a8f319628cb24deeb0177397d34b754a51b30f80c025d4f93d5e5189fec57` | ✅ |

### SOUL.md apply + mirror

- Live `SOUL.md` after apply: `aa0181b3e00c990264e6b203b0a48426cc72b5cd104837e8078e9e986e6b28cf`
- `identity/SOUL.md` mirror: `746dd206eafb2a67153e3450699ad5ae41b26ad1682fb2b698dbf9cd1a8b3964` (LF-normalized **equal** to live; own paragraph after conversation-search)
- `identity/MEMORY_CONVENTIONS.md` after apply: `31bacf1eeffddffb99d49a48c2d9172c5cd4e6f4956dedf3462fc378495db2ca`

### Unchanged surfaces

| Surface | SHA-256 | Status |
|---|---|---|
| `config.yaml` | `7ba2e676a04ff92047c8d711fcb022be8a532b11baac6f74b08986744e704570` | unchanged |
| `zola_tools/__init__.py` | `a1ef8541406f1a9c199cc8c8ce1bb7c71e087f4c3eaa2151dac7b59f04c33513` | unchanged |
| `zola_tools/calculator.py` | `0f29f3fc1e1d5eac3d1e4cef0bcf6428ef6497ee2af61bd86503602be80fe680` | unchanged |
| `zola_tools/plugin.yaml` | `f329e9065493f766712a018df14541172282666ef516ad3d45781b56ae1d2216` | unchanged |
| `hermes-agent` | HEAD `345cd2b0…`, porcelain empty | clean |

## G6 recheck

Offline captures: `C:\Users\test\Dev\zola-spikes\p6-forget\g6-before\`, `g6-after\` (may contain personal memory text — never committed).

Allowlisted per-session line (only): `Conversation started:`

| Check | Result |
|---|---|
| Tool-name set after vs before | ✅ differs by exactly `forget_memory` (19 → 20) |
| Provider schemas | ✅ `zola_memory` → `['forget_memory']` only |
| System prompt after stripping allowlisted `Conversation started:` | ✅ differs by exactly the approved forget SOUL paragraph (1 line added) |
| Live load | ✅ one `initialize ok=true` at relaunch (21:19:52); no post-relaunch `on_turn_start` (G-LIVE) |
| Offline G6-after is a second short-lived agent | noted (shutdown at 21:20:13; not a second live-serve load) |

## Phase 6 notes

- Backed up SOUL, pre-FORGET `plugins/zola_memory/`, and DB via `sqlite3.backup`.
- Redeployed 7 files + added `registry.py`; hashes MATCH repo.
- Applied SOUL forget paragraph as its own paragraph; mirrored to identity (LF-normalized equal). Applied MEMORY_CONVENTIONS Forget paragraph.
- Relaunched client; `zola_memory` loaded once; `forget_memory` is the only provider tool schema.
- G6 PASS; no turns sent.

## Phase 7 notes (close)

- Session `20261004_211943_725b38`; tombs 5→9; Part C clean; end USER/MEMORY hashes match Part A baselines.
- Deviations: steps 5–6/2/8/9 used `memory` remove (+ dialogue clarify); `forget_memory` unused live — accepted in Phase 7 review.
- P6-D06 FAIL on confirmation wording → Phase 7b.

## Phase 1 notes

- Progress doc created on `p6-forget`, uncommitted until closeout.
- Track 3 lessons in scope for grounding: FIX-A/FIX-B session registry; T4 (`sync_turn` excludes time context).
- Prompt SHA verified against developer-supplied value (case-insensitive match).
