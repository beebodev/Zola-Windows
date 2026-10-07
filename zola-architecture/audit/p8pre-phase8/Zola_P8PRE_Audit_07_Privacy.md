# Zola P8PRE Audit 07 — Cloud Model and Privacy

**Date:** 2026-10-07 (F3 corrections)  
**Labels vs:** `P1`, `P6-D07`, `H4`

---

## 1. Where the text goes

Effective: `openai-codex` / `gpt-5.6-terra` / `https://chatgpt.com/backend-api/codex`.

| Call | Sees Workspace content? |
|------|-------------------------|
| Main turn model | **Yes** |
| Background review | **Yes** (default enabled) |
| Episode consolidation | **Yes** (pending user+assistant; `P6-D07`) |
| Title generation | Usually opener only |
| Context compression | **Yes** if still in window |

---

## 2. Provider terms (F3)

**Fetch note:** Direct HTTP GET to `help.openai.com` from this machine returned **403**. The quotes below are from OpenAI Help Center pages as returned in public search indexing on **2026-10-07**, with the same URLs. Brian’s own account toggle state remains **UNCONFIRMED**.

### Training (ChatGPT + Codex on personal plans)

Source: https://help.openai.com/en/articles/5722486-how-your-data-is-used-to-improve-model-performance (indexed 2026-10-07):

> When you use our services for individuals, such as ChatGPT and Codex, we may use your content to train our models. You can choose whether your conversations help improve our models. To opt out, turn off Improve the model for everyone under Settings > Data controls in ChatGPT, or select Do not train on my content in our Privacy Portal.
>
> Either option is sufficient for ChatGPT conversations and Codex tasks. You don’t need to do both. After you opt out, we won’t use your new conversations to improve our models.
>
> Codex has a separate Include environments setting in Codex settings for allowing training on full environments. Changing your settings in ChatGPT or the Privacy Portal does not change that setting.

Source: https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt (indexed 2026-10-07): same “Improve the model for everyone” / Privacy Portal controls; Codex tasks covered by that setting; separate Codex “Include environments”.

### Retention

Source: https://help.openai.com/en/articles/8983778-chatgpt-data-controls-faq (Chat and File Retention Policies; indexed 2026-10-07):

> Chats are saved to your account until you delete them manually.
>
> When you delete a chat (or your account), the chat is removed from your account immediately and scheduled for permanent deletion from OpenAI systems within 30 days, unless [legal/security exceptions].

Temporary Chat: deleted within 30 days; not used for training (Data Controls FAQ indexing).

### Zero-retention / consumer

No separate “zero retention for all Codex/ChatGPT consumer API traffic” option was confirmed on a successfully fetched page in this pass. Training opt-out ≠ zero retention (history still saved until delete). Enterprise/Business “not used to train by default” is a different product tier (Help Center indexing).

**UNCONFIRMED (question for Brian):** whether “Improve the model for everyone” is currently off on his account; whether Codex “Include environments” is on; which ChatGPT plan backs `openai-codex`.

---

## 3. `P6-D07` boundary

Memory local; consolidation may resend pending turns through host-owned model — model processing, not off-device memory. Does **not** exclude email bodies from the conversation-path cloud model.

---

## 4. Levers (facts; no recommendation)

| Lever | Protects | Costs |
|-------|----------|-------|
| Metadata-only default | Body out of model | Weaker answers until expand |
| Length caps | Volume / prompt cost | Incomplete lists |
| Strip quotes/signatures | Quoted history | May drop needed context |
| Redact addresses | Address harvesting | Harder addressing |
| No attachments | Attachment content | Can’t answer attachment questions |
| Local summarizer | Body local | Install or local model (`P2-D17`) |
| Training opt-out (account) | Model-training use | Does not remove retention/history |

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-34 | [RISK] | HIGH | Email/file bodies in tool results go to cloud main model (+ review/consolidation). |
| P8PRE-AUD-35 | [MATCH] | — | `P6-D07` is memory-locality, not email exclusion. |
| P8PRE-AUD-36 | [GAP] | MEDIUM | Brian’s training/Codex environment toggles UNCONFIRMED; public opt-out/retention pages quoted above (F3). |
| P8PRE-AUD-47 | [MATCH] | — | Public Help Center: personal ChatGPT/Codex trainable unless “Improve the model for everyone” off / Privacy Portal opt-out. |
