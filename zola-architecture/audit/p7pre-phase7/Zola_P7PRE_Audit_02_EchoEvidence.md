# P7PRE Audit 02 — S45: Incidents and History

**Sources:** `voice-timeline.log`, `agent.log`, `state.db` (scratch RO copy), `zola_memory.db` (scratch RO copy), `P6-FORGET_Progress.md` (incident wording exception).  
**Labels:** `S45`, `P6-D06`, `P5-D10`  
**Privacy:** lengths, timestamps, session IDs, ratios only.

---

## 1. Incident reconstruction — session `20261004_213345_e1ca3d`

### E1 — Whole-user-turn echo (step-2 confirmation)

| t (local) | Event | Evidence |
|---|---|---|
| 21:34:46.769 | `message.complete` (prior reply, 7 words in timeline) | voice-timeline |
| 21:34:53.241 | `follow_up_release rule=monitor` → capture arm | VT |
| 21:34:53.246 | `followUpStarted=True` | VT |
| 21:34:54.284 | **`fireOrCancel=typed-submit`** — CancelFollowUp; flags cleared | VT |
| 21:34:54.361 | Hermes `Voice recording started` (orphan CAP continues) | agent.log |
| 21:34:54.408 | Typed `prompt accepted` chars=26 | agent.log |
| 21:34:54–21:35:02 | New turn runs; `capture=true` while `turn=true` | VT |
| 21:35:02.464 | Assistant reply len=77 persisted | state.db |
| 21:35:10.543 | Follow-up release **ineligible** (`capture` already live) | VT |
| 21:35:10.738 | Silence / WAV stop (16.8 s recording) | agent.log |
| 21:35:14.618 | Whisper done | agent.log |
| 21:35:14.627 | **`transcript len=76`** `bound=none`; `followUpStarted=False` → **no echo check** | VT |
| 21:35:14.646 | `prompt accepted` chars=76 (new whole turn) | agent.log |
| 21:35:14.691 | User msg len=76; **equal** to prior assistant (ratio 1.000) | state.db |

**Path (matrix):** Follow-up recording → typed-submit cancel-without-stop → TurnRunning with orphan CAP → transcript after reply → whole `prompt.submit`.  
**Brian typing:** **Yes** — `typed-submit` at 21:34:54; prompt accepted with no preceding transcript for that turn.

### E2 — Mid-turn redirect (80-char echo during step 4)

| t (local) | Event | Evidence |
|---|---|---|
| 21:35:26.298 | `follow_up_release rule=monitor` → recording | VT |
| 21:35:26.935 | Hermes recording started | agent.log |
| 21:35:27.824 | **`typed-submit`** again; CAP left live | VT |
| 21:35:27.843 | Typed prompt chars=65 | agent.log |
| 21:35:35.821 | Assistant reply len=80 (remember text) | state.db |
| 21:35:46.160 | Silence stop (19.2 s) — capture heard prior reply + into next turn | agent.log |
| 21:35:46.879 | Typed forget prompt chars=**30** (turn starts) | agent.log |
| 21:35:48.782 | **`transcript len=80`** `bound=none` during `turn=true` | VT |
| 21:35:48.905 | User msg len=80 at **same timestamp** as empty assistant row; overlap ratio **0.917** vs prior asst len=80 | state.db |

**Hermes handling:** P6-FORGET 7c-1 — active-turn **redirect**; `original_user_message` became `"{forget}\n\nUser correction during the turn: {echo}"` (**145** chars) for sync. That concatenated form is **not** retained as a `messages.content` / `api_content` row today (`content_redirects=0`, `api_content_redirects=0` DB-wide); the 80-char echo is stored as its own user message.

**Path (matrix):** Follow-up recording → typed-submit cancel-without-stop → orphan CAP → transcript during TurnRunning → busy `interrupt` → redirect.

**Finding P7PRE-AUD-09** [RISK] HIGH — E1 and E2 both take the LEAD-1 orphan-capture path; E1 → whole turn, E2 → mid-turn redirect.

---

## 2. Typing vs speaking in that window

**Brian was typing.** Evidence: multiple `fireOrCancel=typed-submit` lines; `tui prompt accepted` lines with no preceding transcript for those char counts (26, 65, 30). Voice mode stayed on (`mode=voice`), so follow-up captures still armed after spoken replies.

---

## 3. History — echo candidates (not confirmed echoes)

### Redirect marker in `state.db`

| Query | Count |
|---|---:|
| `User correction during the turn:` in `content` | **0** |
| Same in `api_content` | **0** |

(The redirect string is an in-turn / sync construct; not a durable message prefix in this DB snapshot.)

### Whole-turn echo candidates

Method: user message following an assistant message in the same session; normalized word-set overlap; temporal proximity ≤ **120 s** when timestamps allow. Thresholds: **strict ≥ 0.70**, **moderate ≥ 0.45**. Min 4 words each side.

| Threshold | Candidates | Voice-associated | Typed-associated | Corroborated |
|---|---:|---:|---:|---:|
| Strict (≥0.70) | **15** | **1** | **1** | **2** |
| Moderate (≥0.45) | **27** | *(not fully classified)* | *(not fully classified)* | **2** (same as strict hits) |

**Corroborated** = `voice-timeline.log` has `transcript len=` matching turn length within ~30–60 s:

1. Session `20261004_213345_e1ca3d`, ulen=76 (E1) — **confirmed echo**.
2. Session `20261001_095314_498bdb`, ulen=107 — timeline length match only (not re-litigated here).

**E2** (ulen=80 mid-turn) is a **confirmed echo** via timeline + same-ts inject, but is a redirect path rather than a "whole turn after assistant" candidate row (overlap ratio 0.917 vs prior assistant; stored as concurrent user row).

Association notes (strict):

- Typed-associated heuristic (typed-submit within 80 log lines before matching transcript): **1**
- Other / voice-path match: **1**
- Remaining strict candidates: **content-overlap only** — may be Brian quoting her; **not** confirmed echoes.

**Finding P7PRE-AUD-10** [MATCH] — Historical search reports **candidates**; confirmed echoes require timeline corroboration. Confirmed in this audit: **E1**, **E2** (+ one older length-matched candidate).

---

## 4. Contamination in `zola_memory`

| Table | Count | Echo/redirect link |
|---|---:|---|
| `pending_turns` | 0 | None present |
| `episodes` | 0 | None |
| `episode_fact_refs` | 0 | None |
| `facts` | 16 | No automated link to E1/E2 without content (not done; privacy) |
| `tombstones` | 30 | Forget path may have removed related facts |

**Finding P7PRE-AUD-11** [GAP] LOW — Store shows **no pending/episodes** holding the incident; fact-level contamination not proven without reading fact text (out of privacy scope for repo docs). Developer cleanup decision remains for any known notebook pollution from that session (see synthesis 5.2).

---

## 5. Base rates (`voice-timeline.log`, full file)

| Metric | Count |
|---|---:|
| Transcripts (all, incl. empty/nospeech flags) | **177** |
| Non-empty transcript lens logged | **168** |
| `echo-ignored` drops | **16** |
| `follow_up_release` | **255** (script) / **205** distinct rule lines in Phase 6 recount |
| `typed-submit` mentions | **31** |
| Typed-submit followed by transcript within 40 log lines | **8** |

Echo-ignore rate vs non-empty transcripts: **16 / 168 ≈ 9.5%**.  
LEAD-1-shaped orphans (typed-submit → later transcript): **8** occurrences in log history — upper bound on this failure mode's frequency.

**Transcript length distribution (non-zero):** p50=42, p95=207, max=283.
