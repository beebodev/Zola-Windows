# P6PRE Audit 04 — Time Awareness (S43)

**Audit:** P6PRE · Pin `345cd2b0…`  
**Labels against:** S43, WINH12-AUD-01/02.

---

## Finding summary

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-22 | [MATCH] | — | `system_prompt.py` L433–457 | Model sees calendar date + timezone; date-frozen until compression rebuild. |
| P6PRE-AUD-23 | [GAP] | HIGH | `message_metadata.py`; `turn_context.py` | Per-message timestamps exist in DB/metadata but are **not** on the model wire by default. |
| P6PRE-AUD-24 | [GAP] | MEDIUM | `session_search_tool.py` L62–69 | Search “when” strings omit timezone — weak for elapsed-time math. |
| P6PRE-AUD-25 | [MATCH] | — | `turn_context.py` L663–714; hooks docs | `pre_llm_call` can inject conditional time into the user turn without editing hermes-agent. |

---

## 1. Time text today

Exact shape (`system_prompt.py` L433–457):

```
Conversation started: {Weekday, Month DD, YYYY} ({IANA}, {abbrev}, UTC±HH:MM)
```

Optional second line only when calendar day ≠ start day:

```
Today's date (as of the last context rebuild): {Weekday, Month DD, YYYY} — trust this over the start date for what day it is now; query tools for exact time.
```

- Built once per session; rebuild on **context compression**.
- **No clock time of day** — docstring sends exact time to tools.
- Source: `hermes_time.now()` / `get_timezone()` (`HERMES_TIMEZONE` → config `timezone` → server-local). Live profile has no explicit `timezone:` key.

**P6PRE-AUD-22 [MATCH]** with WINH12 foundation (date present; elapsed awareness missing).

---

## 2. Message timestamps

| Location | On wire? |
|----------|----------|
| `messages[].timestamp` (persistence) | **No** — stripped as persistence-only |
| Gateway `[Tue YYYY-MM-DD HH:MM:SS TZ]` prefix | Only if `gateway.message_timestamps.enabled` (default **off**) |
| `state.db` message/session times | Via `session_search` |
| Client logs | Ops only |

**P6PRE-AUD-23 [GAP]** for S43 “how long ago.”

---

## 3. Prompt caching

- Static system prefix vs volatile suffix; timestamp lives in **volatile** tier after memory (`system_prompt.py` L649–656).
- Changing the time line **every turn** would break the volatile system cache every turn.
- Status quo avoids that by freezing until compression.
- Per-message timestamp on the **user** turn does not break the static system prefix (same shape as prefetch / `pre_llm_call` context).

---

## 4. Resumed session

Model sees start date (+ rebuild day if multi-day). **Does not** know elapsed since last message without tools or new injection. Aligns with P5-MEMORY BR1 (correct answer, no timing phrase).

---

## 5. Dates in search / memory

- `session_search`: `"%B %d, %Y at %I:%M %p"` from local `fromtimestamp` — **no TZ label** (P6PRE-AUD-24).
- Memory files: prose + `[tag]`; no structured absolute+TZ fields.

---

## 6. Candidate mechanisms (not a choice)

| Mechanism | Hook | Edits hermes-agent? | Cache | Tokens/turn |
|-----------|------|---------------------|-------|-------------|
| Refresh `_timestamp_line` every turn | System prompt | Yes | Breaks volatile system every turn | ~1 line |
| Status quo + tools | Compression + `session_search` | No | Safe | Tool when used |
| Enable `gateway.message_timestamps` | Config | No | User msgs | ~1 prefix/msg in history |
| `pre_llm_call` context | Plugin/shell | No | User turn | Conditional |
| Provider `prefetch` / `system_prompt_block` | Memory provider | No (profile plugin) | User / volatile system | Conditional / rebuild |
| SOUL instruction to use tools | Identity | No | None | 0 until tool |
| Client-side prefix | WinUI → prompt | Client only | User | Per turn if always |

---

## 7. Conditional time

**Yes.** Best existing hook: `pre_llm_call` → `{"context": "…"}` on the user message (`turn_context.py` L663–714). Provider `prefetch` can also carry dated facts when relevance retrieval runs. **What decides “needs time”:** entirely inside the hook/provider (inspect user text / history) — no built-in classifier. Hook points only; no design here.

**P6PRE-AUD-25 [MATCH]** — substrate exists for conditional delivery.

---

## 8. Temporal architecture reach (Windows context)

**In reach now:** calendar+TZ in prompt; `hermes_time`; DB timestamps; optional gateway prefixes; `session_search` when; flat memory files; plugin/provider injection.

**Depends on missing layers** (WINH12 / Temporal arch — not scored as Windows gaps for Android pieces): SessionBoundaryResolver, ThreadArcClassifier, TemporalRecencyFormatter, SessionBrief `[TEMPORAL]`, initiative queue, episodic stores, ConsolidationLoop, etc.
