# Zola P8PRE Audit 06 — Untrusted Content, Memory and Provenance

**Date:** 2026-10-07  
**Labels vs:** `P6-D01`, `P6-D02`, `P6-D06`, `P6-D09`, `P5-D10`, `A5`, `A8`

---

## 1. Tool output → model

`agent/tool_dispatch_helpers.py` wraps only:

```text
_UNTRUSTED_TOOL_NAMES = frozenset({"web_extract", "web_search"})
_UNTRUSTED_TOOL_PREFIXES = ("browser_", "mcp_")
```

(~L435–534). Terminal, plugin tools, memory, file tools — **not wrapped**. Workspace via terminal/plugin would be unmarked.

---

## 2. Hostile email → action surface

| Tool | Gated by | Gate type |
|------|----------|-----------|
| `terminal` | `approvals.mode=manual` dangerous patterns; tirith | pattern/code |
| `memory` add/replace | `memory.write_approval` default **false** | none (soft) |
| `forget_memory` | G-AUTHORITY + Brian conversation | code |
| skills / `skill_manage` | `skills.write_approval` default false | soft |
| file tools | `file_safety` (terminal bypass) | partial code |
| web_*/browser_* | Untrusted wrap | framing |
| send (future plugin) | Must be `request_tool_approval` | code (if built) |
| Workspace via terminal skill | Same as terminal; no content trust wrap | pattern only |

---

## 3. Persistence (LEAD-8)

| Path | Lands? | Provenance |
|------|--------|------------|
| `state.db` tool messages | **Yes** | role/name; no untrusted flag for terminal |
| `session_search` / FTS | **Yes** | none for trust |
| `zola_memory` pending | **user + assistant text only** (`sync_turn`) — not raw tool rows; **paraphrase of email in her reply enters** | disposition only |
| Episodes / facts | Via consolidation / memory tool / review | `source` ∈ {`notify`,`file_check`} only — **no `email:<id>`** |
| Background review | Sees conversation; **can write memory/skills** (`A5`) | `_memory_write_origin` |

**LEAD-8: CONFIRMED** for Workspace path; refine: web/browser/mcp *are* wrapped, but not the Workspace path.

---

## 4. Provenance

Current schema cannot distinguish “Brian said remember X after hearing email” vs “saved from email.” No `source: email:<id>` field. Facts: `store.py` source enum narrow.

---

## 5. Forget

`P6-D06`: forget erases provider-controlled copies. Episodes that absorbed paraphrased email are in cascade if targeted. **`state.db` not redacted (`P5-D10`)** — email text in chat history remains.

### 5a. Two answers to “when was that?”

Episodes carry `event_time` (`P6-D04`/`P6-D05`); consolidation cue: only Brian’s stated phrase. **No rule** that Calendar API wins for scheduled event times vs memory. Calendar result could be written into episode/fact if model/review saves it — no hard block. Authority rule = decision.

---

## 6. Contacts as entities

People entities exist in fact index. Contacts API results do **not** auto-upsert. Collision only if model/review writes memory from names — soft.

---

## 7. Attachments if read later

Same persistence as §3 plus temp downloads, `read_file` (100k), vision tools. Sets Phase 8 boundary: metadata yes / content no unless decided.

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-29 | [RISK] | HIGH | Workspace/terminal tool output not marked untrusted (LEAD-8). |
| P8PRE-AUD-30 | [GAP] | HIGH | No email provenance on memory facts; review can write from tool-tainted turns. |
| P8PRE-AUD-31 | [MATCH] | — | Pending sync excludes raw tool rows; paraphrase path remains. |
| P8PRE-AUD-32 | [GAP] | MEDIUM | No calendar-vs-memory authority rule for event times. |
| P8PRE-AUD-33 | [MATCH] | — | Forget does not clear `state.db` (`P5-D10` / `P6-D06`). |
