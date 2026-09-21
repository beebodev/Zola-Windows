# WINH07 Audit 05 — Truth Ownership: Reasoning / Speech Separation

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Zola source: Core Architectural Principles — Truth Ownership Rule, Speech Authority Constraint. Truth (tool results, retrieved facts, computed values) is owned separately from phrasing. Speech must not silently rewrite meaning. Zola’s Response Governor is the example owner of what is *said*; it is not a Hermes type.

Turn/response assembly was already in view from WINH03 (`prompt_turn.py` / conversation loop). This phase confirms whether anything sits **between** tool results and final user-facing text.

---

## 1. Structural separation between “what is true” and “how it is phrased”?

**Zola:** a distinct formatting / presentation layer downstream of tool-call results. The same subsystem that reasons must not freely phrase without a catch on meaning-altering rewrite.

**Hermes turn assembly (gateway path):**

1. `tui_gateway/prompt_turn.py` `_run_prompt_submit` L796–848 invokes the agent, then `_complete_turn_payload` → `_emit("message.complete", …)` with the loop’s `final_response` (and streamer deltas already sent).
2. Agent loop: `agent/conversation_loop.py` `run_conversation` L1573–1600 → `_run_conversation_turn`. Tool rounds append tool results into `messages`; the **next model API call** produces assistant content. `final_response` is that model text (plus recovery/nudge paths).
3. No-tool-call / stop branch: `agent/turn_final_response.py` `finish_text_response` (imported L42 of `conversation_loop.py`). Docstring L1–6: empty/think-only recovery, intent-ack, length-continuation, dropped-tool-call re-prompt, scaffolding pop, **stop gates**, then durable flush. That is loop control, **not** a presentation layer that re-reads tool JSON and formats a user utterance.

**Stop gates are not a speech-authority layer:**

- `agent/turn_stop_gates.py` L1–9: when the model stops with a text answer, gates may append the answer as an *interim* row plus a synthetic user-role **nudge** and continue the turn (`verify_on_stop`, `pre_verify` plugin hook, kanban terminal-tool guard). They clear `final_response` so the loop continues. They do **not** compare the candidate sentence to tool output.
- `agent/verification_stop.py` L1–3: “Turn-end verification guard for **coding edits**. Policy-only: it never runs checks itself” — a bounded follow-up nudge after file mutations, explicitly **not** fact/speech fidelity.

There is no function that takes structured tool results and produces the user-visible string. The model that called the tools is the same model that phrases the answer. Gateway `_complete_turn_payload` packages that string for JSON-RPC; it does not verify it.

**Label:** `[GAP]` `WINH07-AUD-13` (HIGH) — nothing sits between tool results and final text except more model tokens (and coding-edit nudges).

---

## 2. Fidelity check for structured tool data in the final response?

**Zola Truth Ownership:** numbers, entity names, dates from tools must survive phrasing; hallucination during rewrite is not an acceptable sole control.

**Searched at this pin (representative, not exhaustive of every string):** `conversation_loop.py`, `turn_final_response.py`, `turn_stop_gates.py`, `verification_stop.py`, `prompt_turn.py` `_complete_turn_payload`, `tui_gateway` emit path. No compare of assistant text against tool-result JSON (no number/date/entity preservation check, no constrained decoder that must quote tool fields).

Tool-calling itself is structured (name, args, result rows in history). That does **not** constrain the subsequent English/markdown. `verify_on_stop` only fires after **code file** mutations (`verification_stop.py` L15–23 even *suppresses* the nudge for prose/markdown paths). Messaging surfaces skip some of that coding posture (`_session_is_messaging_surface` L39+).

Fidelity of spoken/written facts is **entirely** “the model did not hallucinate while phrasing.”

**Label:** `[GAP]` `WINH07-AUD-14` (HIGH) — no verification layer. Do not infer one from structured tool-calling.

---

## 3. Does Hermes’s architecture assume reasoning and speech are separable?

**Zola Speech Authority Constraint:** reasoning and speech are different responsibilities; speech is authorized separately.

**Hermes:** architecturally a **single-pass (iterative tool-round) generator**. One provider conversation: think / tool / observe / speak in the same `messages` array. `final_response` is whatever the last assistant text was when the loop decides to stop. `display.show_reasoning` (`config_defaults.py` L787–792) can stream a reasoning channel *to the UI* as a display feature; it is not a truth object the speech layer must honor, and it is not a Response Governor.

Nothing in the gateway or loop **enforces** that workers cannot speak (WINH07-AUD-01/02 already: `_emit` from review, notices, child mirrors). Nothing stamps a tool result as the owned truth for a field the utterance must copy.

The requirement still applies to Zola-Windows even though Hermes makes it structurally hard. This is not a reason to skip the question.

**Label:** `[GAP]` `WINH07-AUD-15` (HIGH) — Hermes is a single-pass generator; reasoning/speech separation is not a Hermes invariant. `verify_on_stop` is a coding nudge, not Speech Authority.

---

## Finding list (this phase)

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH07-AUD-13 | GAP | HIGH | `conversation_loop.py`; `turn_final_response.py` L1–6; `prompt_turn.py` L848 | Same model call chain both reasons and phrases; no downstream formatter |
| WINH07-AUD-14 | GAP | HIGH | searched turn/stop/prompt_turn | No check that final text preserves tool numbers/names/dates |
| WINH07-AUD-15 | GAP | HIGH | `turn_stop_gates.py` L1–9; `verification_stop.py` L1–3 | Architecture does not separate reasoning vs speech; verify-on-stop ≠ fidelity |
