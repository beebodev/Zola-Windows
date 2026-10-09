# Zola P9PRE Audit 05 — Background Ranking

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Labels vs:** `P6-D04`, `P6-D07`, `P8-D09`, `P8-D11`, `A5`

No model call was made (G-NO-LIVE-MODEL).

---

## 1. The accessor (LEAD-3)

`PluginLlm` (`agent/plugin_llm.py` L1–10) is `ctx.llm` (`hermes_cli/plugins.py` L385–393), one instance per `PluginContext`, bound to that plugin id. `complete` takes messages, temperature, max_tokens, timeout, provider/model overrides, and `task`. It has no `system_prompt` parameter and **no `tools` parameter**. A system prompt is a `role: system` message in `messages`. `complete_structured` adds `instructions`, `input`, `json_schema`, `json_mode`, and `system_prompt`.

`_host_kwargs` (L547–557) passes messages, provider, model, temperature, max_tokens, timeout, extra_body, task. It does not pass `tools`. With `task` unset, the call uses the main-model route. A missing `plugins.entries` block allows that route and blocks overrides. Timeout `None` becomes 30 seconds when there is no task (`auxiliary_client.py` `_DEFAULT_AUX_TIMEOUT`). `auxiliary.monitor` is a separate config row, timeout 60, comment "important-mail 0-10 scorer" (`config_defaults.py` L738). The facade does not select it unless the caller passes `task="monitor"`, and that task key needs `allow_task_override` when the plugin did not register it.

`call_llm` (`auxiliary_client.py` L7223) accepts `tools: list = None`. Because the facade omits `tools`, the default `None` is what the plugin path sends. `_build_call_kwargs` adds `tools` only when that argument is truthy (L6144–6161). A script that imports `call_llm` directly can pass tools. The facade cannot.

`_acquire_sync_aux_semaphore` (L5909–5913) returns `None` when `task` is missing or `auxiliary.<task>.max_concurrency` is not a positive int. The pin default has no `max_concurrency`. A facade call with `task=None` does not take that semaphore.

Overrides are gated by `plugins.entries.<plugin_id>.llm.allow_*_override`. A missing block means no overrides (file header L6–8). The live profile has no `plugins.entries` block (Phase 1), so a call uses the host's active provider and model (`openai-codex` / `gpt-5.6-terra`).

`zola_memory` stores the collector in `register` and calls `llm.complete_structured` from consolidation (`consolidate.py` L487–492) with instructions, text, `EPISODE_JSON_SCHEMA`, and `CONSOLIDATE_LLM_TIMEOUT_S`. No tools argument.

**LEAD-3: CONFIRMED for the tool-less facade.** The same accessor is what consolidation uses. It is reached from a daemon thread (`request_consolidate`, `consolidate.py` L386–420), which is outside the user turn and inside the serve process that loaded the plugin.

**P9PRE-AUD-26 [MATCH]** — `PluginLlm.complete` / `complete_structured` do not accept or forward tool schemas. `P6-D04`.

---

## 2. Outside a turn, and from another plugin

`complete` does not take a session id. It needs the host config and provider credentials, which `call_llm` reads itself. `zola_memory` already calls it from `zola-consolidate` with no user turn in progress.

`zola_workspace` does not call `ctx.llm` today. Its `register` receives a `PluginContext` (`plugins.py` L385–393 exposes `.llm`). A second plugin can call **its own** `ctx.llm`. It cannot use `zola_memory`'s collector unless that object is shared. Trust policy is per plugin id. There is no cross-plugin bridge.

A separate process does not have a `PluginContext` unless it loads Hermes and the plugin. Importing `PluginLlm` alone still calls `call_llm`, which expects the Hermes runtime config. That is a fact about the import, not a design.

---

## 3. Concurrency

The default facade path does not take the aux semaphore (section 1). Brian's live turn uses the main conversation client. Nothing in `PluginLlm` queues behind an in-flight stream. Both can hit the same provider account at once. The client cache lock covers lookup only (`auxiliary_client.py` L5548–5591).

**P9PRE-AUD-27 [RISK] MEDIUM** — a ranking call and a live turn are not one queue. The default path has no aux concurrency cap. `A5` is about authority, not rate; the practical risk is overlapping calls, not a second tool path (the facade has no tools).

---

## 4. Logging and persistence

The facade's INFO line (`plugin_llm.py` L530–543) records plugin id, provider, model, task, purpose, and token counts. It does not include message text.

`zola_memory.log` records consolidation as `trigger`, `turns`, `episodes`, `ok`, `attempt`, `elapsed_ms`. From the live log, read-only, 2026-10-09: 37 `ok=true` lines, `elapsed_ms` min 1555, median 4334, max 34601; 19 failures, `elapsed_ms` from 0 to 30145. Token counts are not in that log. No prompt text was copied out of the file.

`PluginLlm` returns a result object. With `task=None`, auxiliary usage recording returns before any `state.db` write (`record_aux_usage` requires a task and an accounting context). A background thread's accounting context defaults to empty. Consolidation writes episodes only after `validate_episodes` and `_commit`. A failed call returns `False` and leaves the pending rows (`consolidate.py` L493–525).

---

## 5. Output shape

`complete_structured` asks for JSON. `_parse_structured_text` (`plugin_llm.py` L316–334): invalid JSON returns `(None, "text")`. A schema `ValidationError` raises `ValueError`. Consolidation treats either failure as `ok=False` and does not commit. Give-up after `CONSOLIDATE_MAX_ATTEMPTS` still logs `pending_count` and does not delete the rows in the failure branch shown.

There is no fixed label set in the accessor. A schema can constrain labels if the caller supplies one. The accessor does not invent that schema.

`_parse_structured_text` skips `jsonschema.validate` when the package is missing (`plugin_llm.py` L330–331) and logs at debug. On 2026-10-09 the Hermes venv raised `ModuleNotFoundError` for `jsonschema`. A `json_schema` argument does not reject a nonconforming object in this environment. Consolidation's own `validate_episodes` still runs after the parse. A ranking caller that passed only `json_schema` would not get that second check.

**P9PRE-AUD-41 [RISK] MEDIUM** — schema enforcement in the accessor depends on `jsonschema`, which is not installed. `P2-D17`. Candidate only (not installed): PyPI `jsonschema` 4.26.0, wheel 90630 bytes, sdist 366583 bytes, requires `attrs>=22.2.0`, `jsonschema-specifications>=2023.03.6`, `referencing>=0.28.4`, `rpds-py>=0.25.0` (format extras omitted). Read from `https://pypi.org/pypi/jsonschema/json` on 2026-10-09.

`_json_response_format` sets `"strict": False` (`plugin_llm.py` L407). If the provider rejects `response_format`, `call_llm` retries once without it and logs that schema enforcement degrades to prompt compliance (`auxiliary_client.py` L6904–6909).

Hermes also ships `cron/scripts/classify_items.py`. `main` (L132–137) calls `call_llm(task="monitor", ...)` with no `tools`. `_parse_scores` (L68–97) returns `{}` when the text is not a JSON array. `main` then surfaces nothing and returns 0 (L154–155), which is silent success. A raised call returns 4 (L141–144). Items that fail to parse are absent from stdout. They are not kept in a queue. This script does not run in Zola's serve, because the cron ticker is not started (audit 02).

**P9PRE-AUD-28 [MATCH]** — malformed structured output fails the consolidation commit and keeps the pending rows. That is the existing "do not drop the item" pattern.  
**P9PRE-AUD-44 [RISK] MEDIUM** — `classify_items.py` is a mail-scoring `call_llm` with no tools, and a bad parse exits 0 with empty stdout. That drops the item from delivery. `call_llm` itself can accept tools; this script does not pass them. `P6-D04`.

---

## 6. Injection surface

`framing.py` wraps tool results. A ranking "reason" string is model output that was conditioned on untrusted metadata. If that reason is later injected into a turn, it is untrusted text with no tool framing unless the injector applies `framing.py`. A hostile snippet can ask to be ranked high, ask that another item be suppressed, or put instructions in a reason field. The model can comply inside the ranking JSON. Delivery code that reads a thread id, event id, or sender **from the model** would be trusting that output. Delivery code that reads those fields from the stored candidate, and only reads a clamped label from the model, does not grant the model those fields. Nothing in the current code ranks mail, so nothing in the current code lets a ranking object create a loop. The gap is the absence of a parser that refuses to treat model text as identifiers.

**P9PRE-AUD-29 [GAP] MEDIUM** — no ranking parser exists. The tool-less call cannot act. A later consumer that trusts identifiers inside the model JSON would. `P8-D09` does not apply until that text is tainted on injection (audit 04, AUD-23).

---

## 7. Ranking is advisory (Phase 6 Q9)

These are facts about what deterministic code can check from data it already has or can store. They are not a design.

| Policy | Can code enforce it without the model? | Data that exists today |
|--------|----------------------------------------|------------------------|
| Eligible sources (account, calendars, labels) | Yes, if the poller stores the account and label ids it queried | `gcal._selected_calendars`; Gmail label ids on `shape_metadata` |
| Open-loop match by thread or event id | Yes, string equality on ids the poller stored | `threadId` on metadata; Calendar event `id`. Model-claimed ids are a different field |
| Freshness | Yes, from the item's date and a clock | `shape_metadata` date; `time_context` for "now" |
| Quiet hours and lock | Yes, at delivery time, from client state | `SessionLockWatcher`; no quiet-hours key in Phase 1 config |
| Frequency caps | Yes, from a delivery-history table of ids and times | no such table today |
| Minimum bar on a bounded label or clamped score | Yes, if the schema's label set is finite and code discards anything else | accessor returns raw text; schema is caller-supplied |
| Suppression / already told | Yes, from stored ids | no such record today |

Nothing in a ranking JSON can grant delivery, open or close a loop, or rewrite a source id **unless a consumer copies those fields out of the JSON**. The current codebase has no such consumer.

Malformed, missing, or schema-failing output: consolidation's pattern is to keep the source rows and return false (section 5). Applying that pattern to a queue means the item stays stored and unranked. The accessor itself does not implement that queue.

**P9PRE-AUD-30 [MATCH]** — the model call on this facade cannot call tools. Authorization, if any, would be a later code decision. `P6-D04`, `A5`.
