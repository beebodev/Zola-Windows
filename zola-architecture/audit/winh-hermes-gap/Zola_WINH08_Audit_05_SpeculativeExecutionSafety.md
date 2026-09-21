# WINH08 Audit 05 — Warm-Start / Speculative Execution Safety

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola: Agent 4 (Memory Warm-Start), Agent 8 (Tool Warm-Start), Agent 9 (Active Entity Resolver). Live result always wins over cached/speculative. Must never speculatively write; Agent 8 must never pre-execute confirmation-gated tools.

Phase 3 already answered **tool** warm-start: none (`WINH08-AUD-07`). This phase does not re-search tool pre-execute. Remaining question: other prefetch/cache, live-vs-stale, speculative **durable** writes.

This is **not** “no speculative layer at all” — memory prefetch exists — so the phase is not a single MATCH-by-absence.

---

## 1. Cached/speculative vs live — which wins?

**Tool results:** no Agent 8 cache (`WINH08-AUD-07`). A live `handle_function_call` is the only tool result. N/A for tools.

**Memory / retrieval prefetch (Agent 4 shape, not Agent 8):**

- Each turn: `agent/turn_context.py` `_memory_turn_start_and_prefetch` L779–790 → `memory_manager.prefetch_all` L394–402. Non-trivial prompts only. Injected as `ext_prefetch_cache` into the user message’s API copy (`compose_user_api_content`). Comment L442–443: stamped into `api_content` and **replayed on later iterations of that turn**.
- Provider contract: `agent/memory_provider.py` `prefetch` L111–113: “recall in the background and return cached results”; `queue_prefetch` L116–117 queues after a turn for the **next** turn’s `prefetch()`. `recall_status` L119–121: “only the LAST prefetch, never a stale prior count” — that is an **indicator** invariant, not a live-vs-cache winner for payload text.
- Builtin `prefetch` default is empty string (`memory_provider.py` L114). External providers (Honcho, etc.) may return cached recall. Optional; `memory.provider` default `""` (WINH04).

**When both prefetch text and a later live `memory` tool result exist in the same turn:** both sit in `messages`. Nothing discards the prefetch block in favor of the tool result. The model sees both. There is no “live recall always wins” replacement of `ext_prefetch_cache`.

MCP `ttlMs` (`mcp_schema_cache.py` L61) is schema-catalog expiry, not tool-result / entity-resolution cache.

**Label:** `[PARTIAL]` `WINH08-AUD-13` (MEDIUM) — no tool warm-cache to lose to live tools; memory prefetch can coexist with a later live memory tool result with **no** live-wins rule (Agents 4/8/9).

---

## 2. Stale cache served instead of a fresher available value?

**Tool layer:** none to serve stale (`WINH08-AUD-07`).

**Memory prefetch:** within a turn, the first `prefetch_all` string is reused across iterations (`conversation_loop` `_ext_prefetch_cache`). A later provider update mid-turn is not refreshed unless something else calls prefetch again. External prefetch timeout skips the provider until the stuck thread returns (`memory_manager.py` L421–432) — the turn may proceed **without** that memory, not with a flagged-stale blob (`WINH08-AUD-03`: no `isStale`).

Holographic `trust_score` ranks facts; it is not TTL invalidation (WINH05).

No cache-invalidation-on-newer-live-result for prefetch text.

**Label:** included in `WINH08-AUD-13` (same mechanism). No separate ID.

---

## 3. Speculative durable write?

**Agent 4/8/9 Must-never:** speculatively write memory / execute confirmation-gated tools / write entities.

**Memory prefetch:** `prefetch` / `prefetch_all` return strings for prompt injection. `queue_prefetch` is next-turn recall, not a MEMORY.md write. `sync_turn` L124–128 persists a **completed** turn to the provider — post-turn, not speculative pre-fetch. Builtin default provider tool writes remain live `memory` tool (`WINH04-AUD-02`, not this path).

**Background-review / cron / heartbeat writes** are not a warm-start cache; they are full (or whitelisted) tool loops already scored as invocation (`WINH08-AUD-02`) and skill/memory authority (`WINH06-AUD-07`, `WINH04-AUD-02`). They are not side effects of speculative **cache** work.

**Label:** `[MATCH]` `WINH08-AUD-14` (LOW) — the prefetch/cache path does not itself durable-write; speculative write-via-warm-start is absent.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH08-AUD-13 | PARTIAL | MEDIUM | `turn_context.py` L779–790; `memory_manager.py` L394–443 | Memory prefetch exists; no live-wins over cached recall text |
| WINH08-AUD-14 | MATCH | LOW | `memory_provider.py` L111–117 | Prefetch is read/inject only; no speculative durable write |
