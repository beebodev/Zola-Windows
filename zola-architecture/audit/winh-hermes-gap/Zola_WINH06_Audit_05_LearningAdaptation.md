# WINH06 Phase 5 — Learning & Behavioral Adaptation Beyond Memory

Hermes pin: `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.
Labels: `[MECHANISM]` / `[RISK]` / `[ABSENT]` / `[UNVERIFIED]`.
Narrow scope: mechanisms that change **future** behavior that are **not** simply text written to `MEMORY.md` / `USER.md` (WINH04) and **not** personality/style config (WINH05).

Do not re-cite `WINH05-AUD-03` `trust_score` as a new finding. It is retrieval scoring, not training.

---

## 1. Fine-tuning, RLHF-style, or weight-adjustment pathway

### WINH06-AUD-22 — `[ABSENT]` — HIGH — searched the pinned tag for training / RLHF / LoRA / eval-harness **runtime**

Searched (among others): `fine.?tun`, `RLHF`, `lora`, `train_loop`, `self.?eval`, `prompt.?optim` under `agent/`, `tools/`, `hermes_cli/`, `tui_gateway/`.

What exists is **not** a bundled training loop invoked by the agent runtime:

- `optional-skills/mlops/training/trl-fine-tuning/SKILL.md` is a **skill document** teaching the user how to run HuggingFace TRL (`SFTTrainer`, `DPOTrainer`, …) in their own environment (`pip install trl …`). It is optional hub content, not imported by `AIAgent`. Installing that skill does not fine-tune Hermes.
- `hermes_cli/models.py` L2451 mentions "private fine-tunes" as **provider catalog** entries (user-scoped model ids), not a local trainer.
- Repo `tests/` is pytest for Hermes itself, not an on-line eval harness that retunes prompts/weights from live sessions.

No `agent/` or `tools/` module loads a trainer, writes checkpoints, or calls a hosted fine-tune API as part of `run_conversation`. If a deployment pointed `model.default` at a user-fine-tuned endpoint, that is operator config (Phase 5 question 3), not a Hermes training pathway.

---

## 2. Measuring own performance and changing behavior from the measurement

### WINH06-AUD-23 — `[MECHANISM]` — MEDIUM — `agent/background_review.py` L1–6, L1025–1065; `config_defaults.py` L748

The post-turn background-review fork (also WINH06-AUD-07/08) is the only in-runtime loop found that **inspects a conversation and then mutates future-facing artifacts other than a one-shot reply**: it may `skill_manage` and/or `memory`. Default enabled. That is adaptation from observed dialogue, not a numeric performance score.

It is not a test harness: there is no held-out eval set, no reward model, no comparison of variants.

### WINH06-AUD-24 — `[ABSENT]` — MEDIUM — `agent/curator.py` (WINH04); searched for scoring-tied retention beyond curator

Not found:

- A self-eval loop that scores answers and then changes defaults/prompts/weights.
- A/B behavior variants.
- Prompt-optimization (DSPy-style, bandit over system-prompt text, etc.).
- Skill retention/archival driven by **outcome quality**. The curator (WINH04, not re-derived) uses **inactivity / staleness / overlap** (`config_defaults.py` `curator.stale_after_days` L1392, `archive_after_days` L1393), not task-success metrics.

`plugins/memory/holographic/retrieval.py` `trust_score` remains WINH05-AUD-03: retrieval ranking, not behavioral training. Not listed as a new WINH06 finding.

`agent/verification_evidence.py` records command-verification events per session — an audit/debug store, not a loop that rewrites skills or config from pass/fail rates (read `verification_evidence.py` L54–78; no writer into `skill_manage` / `config.yaml`).

---

## 3. Provider / model-swap as a capability-acquisition vector

### WINH06-AUD-25 — `[MECHANISM]` — LOW — `tui_gateway/model_switch.py` `_apply_model_switch` L203–254; `model_tools.py` `get_tool_definitions` L212–221; `hermes_cli/model_switch.py` `persist_model_selection` L1586–1604

Hermes can be pointed at a different provider/model:

- Live: `/model` (session, `--once`, or persist-global). Human slash command, not an agent tool.
- Persist-global writes `model.*` into `config.yaml` via `persist_model_selection` (sanctioned YAML updater, not `write_file`).
- Session pin: `session["model_override"]` (L242–245) so rebuilds of **this** session keep the pick without leaking via `os.environ` to sibling desktop sessions.

Does the swap change which **tools** exist?

`get_tool_definitions` filters by **toolset** (`enabled_toolsets` / `disabled_toolsets`), not by model id (L212–221). Switching models does not, by itself, register a new plugin or MCP server. A different model may **use** the same tools more or less competently, and some providers reject duplicate tool names (comment L228–230: DeepSeek / Kimi / MiMo HTTP 400) — that is a **compatibility** constraint, not an unlock of extra tools.

Tool/MCP/plugin acquisition remains the Phase 2–3 paths. Model swap is ungated by `write_approval`; it is gated by being a **human slash command** (plus optional expensive-model confirm in `_apply_model_switch` L233–236). It is unrelated to the skills gate.

If the operator persists a model whose vendor trains on prompts, `security.allow_data_training_tiers_noninteractive` (`config_defaults.py` L1615–1617) is a **startup warning / ack** flag, not a training loop inside Hermes.

`[UNVERIFIED]` whether a specific third-party model exposes extra built-in tools through a provider-specific adapter that `get_tool_definitions` does not see — searched `model_tools.py` for model-id branches that add tools: none. Provider plugins (`manifest.kind == "model-provider"`) load via `providers/` discovery (`plugins_discovery.py` L200–204), which is operator plugin install + config, not `/model` alone.

---

## Summary for this phase

| Category | Result |
|---|---|
| Bundled weight-training / RLHF | `[ABSENT]` (AUD-22) |
| Post-turn skill/memory fork | `[MECHANISM]` (AUD-23), authority risks in Phase 2 (AUD-07/08) |
| Outcome-based self-eval / A/B | `[ABSENT]` (AUD-24) |
| Runtime model/provider swap | `[MECHANISM]` human slash (AUD-25); does not install tools |
