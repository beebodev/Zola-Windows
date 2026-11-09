# Zola S51F-PRE — 02 "Let me look" / pre-tool acknowledgement

Phase 4. Labels **SOURCE** / **MEASURED** / **INFERENCE** / **UNRESOLVED**.  
Phase 2 S2: Brian heard no acknowledgement; first text delta after tools.

---

## 1. TTS pipeline when a short sentence precedes a tool call (SOURCE)

Path (Voice / TUI gateway):

1. `_start_turn_voice` opens TTS queue (`prompt_turn.py` L183–187 → `stream_tts_to_speaker`).
2. Model text deltas → `_stream` → `st.tts_queue.put(delta)` (`prompt_turn.py` L523–530).
3. `stream_tts_to_speaker` feeds `SentenceChunker` (`tts_tool_speaker.py` L305–335; chunker `tts_streaming.py` L67–96).
4. Complete sentences (boundary `.!?` / blank line **and** `len(strip) ≥ min_len` **20**) are spoken via Deepgram command TTS → mp3 → **ffplay** (sync pipeline).
5. Incomplete / too-short heads stay in `chunker.buf`.
6. Flush happens on: end sentinel `None` (`prompt_turn.py` L740–741); or idle flush only if `len(buf) > 100` (`tts_tool_speaker.py` L329–331).
7. Interim assistant text beside tools can emit `message.interim` (`prompt_turn.py` L533–538) — separate from the TTS queue unless those bytes also arrived as stream deltas.

| Case | What happens to the sentence | Label |
|------|------------------------------|-------|
| Complete sentence ≥ 20 chars before tool round ends | Spoken when chunker emits — **before** tools if deltas finished streaming before tool execution | SOURCE |
| Short complete sentence &lt; 20 chars (e.g. "Let me look.") | **Held** in buffer; merged into later text or flushed at turn-end `None` — **not** spoken at once | SOURCE `tts_streaming.py` L85–86 |
| Text without sentence boundary before tools | Held until boundary, idle&gt;100, or end flush | SOURCE |
| No assistant text before tools | Nothing to speak | — |

There is **no** tool-start flush of the TTS chunker today. Stronger: tool-start display may call `stream_delta_callback(None)` for UI only, and Hermes explicitly must **not** send that EOS into the TTS (`_stream_callback`) path (`agent/turn_tool_round.py` ~L146–147) — **SOURCE**.

Speech-baseline path trace agrees: SentenceChunker `min_len=20`; last/short material waits for more text or end (`SPEECH-BASELINE_Findings.md` § path table; `TurnTiming.MinSentenceLen = 20` mirrors it).

---

## 2. S2 MEASURED vs SOURCE

| Milestone | Time | Label |
|-----------|------|-------|
| Submit | ~12:13:01.50 | MEASURED |
| Tools complete | skill_view 12:13:06.580; tool_describe 12:13:06.723; calendar_query 12:13:11.969 | MEASURED |
| First text delta | ~12:13:15.87 (`submit_to_first_delta_ms=14369`) | MEASURED |
| First `Generating speech` | 12:13:16.612 | MEASURED |
| Brian | no "let me look"; no thinking sound | MEASURED |

**Agree:** no speakable pre-tool text was emitted; pipeline had nothing to hold or speak before tools. The hold/flush rules above are still SOURCE for *if* she had emitted text.

---

## 3. Addition — explicit answers

### (a) Did the model emit any assistant text before the tool call in S2? (MEASURED)

**No.** First delta is after `calendar_query` completed. She never generated an acknowledgement in that turn.

### (b) Same-response text + tool call; would text stream/speak before tools? (SOURCE)

| Claim | Verdict | Cite |
|-------|---------|------|
| Provider/Hermes can return assistant **content** and **tool_calls** in one assistant message | **Yes** (content staged with tool_calls; chat/Codex paths) | SOURCE `turn_tool_round.py` ~L255–266; stream helpers |
| Content deltas are pushed to TTS as they stream | **Yes**, while still in the pre-tool-call stream window | `prompt_turn.py` L529–530; chat: text before tool-call acc → `_fire_stream_delta`; after tool-call acc, further content can be display-suppressed (`chat_completion_helpers.py` ~L2819–2837) |
| Codex (Zola live) commentary | Goes to **interim** (`message.interim`), **not** `tts_queue` | SOURCE `codex_runtime.py` commentary path; `prompt_turn.py` L535–536 |
| Such text would be **spoken before tools run** | **Only if** it is non-commentary final-phase content **and** clears `SentenceChunker` (≥ 20 chars + boundary) before/during the tool wait | SOURCE chunker + Codex/`has_tool_calls` gating |
| Short phrases &lt; 20 chars | Likely **held across the tool gap**, then merged/flushed with later text — **not** a reliable pre-tool cue | SOURCE min_len=20 |
| Discord `voice_fx.ack_*` | Fixed phrases on Discord VC only — **not** the Zola Windows path | SOURCE `config_defaults.py` ~L1492–1499 |

### (c) Options for a short acknowledgement in her own words (G-INTEGRATION · G-NO-FIX)

No hardcoded phrase recommended.

| Option | Integration | What Brian experiences | Notes |
|--------|-------------|------------------------|-------|
| **SOUL wording** under P4-D25 | Identity edit only (supported Zola process). **No draft text in this audit.** | Relies on the model choosing to emit a short spoken line before slow tools | Existing SOUL already says: if something will take a moment, "a few words to say so is enough" (`SOUL.md` "How I talk out loud"). S2 shows the model did not do that. A wording tweak might raise frequency; it does not guarantee chunker-speakable length or timing |
| **Hermes setting / hook** | Prefer supported: e.g. display/interim commentary already exists (`show_commentary`, `interim_assistant_callback`). A **flush-TTS-on-tool-start** or **pre-tool speak hook** is **not** a documented config today → **Hermes source** (Brian's no-fork call) | If content streams and is flushed at tool start, he could hear her words before the wait | Smallest *behavioral* gap for held text: flush chunker when tool execution begins — source change unless an existing hook is found that already does it (**none found**) |
| **Zola-side cue at tool start** | Zola client or plugin on tool-start event (client already sees tool activity in UI). Must **not** hardcode a fixed spoken phrase if the goal is "her own words" | Non-verbal UI cue, or a model-authored path only | A fixed "Let me look" string would violate Brian's preference; a client beep/chime is a different product choice (see Phase 3 cues) |

**Hardcoded elsewhere?** No Zola code path found that injects a fixed pre-tool spoken acknowledgement. SOUL is guidance, not a canned TTS string (**SOURCE** / search).

---

## 4. If text is held — smallest supported flush point

| Candidate | Supported? |
|-----------|------------|
| Existing config key to flush TTS on tool start | **No** |
| Plugin hook that flushes `tts_queue` / chunker | **No** documented flush API for plugins |
| Hermes source: flush chunker (or put boundary) when tool executor starts | **Hermes source change** |
| Rely on model emitting ≥20-char complete sentence before tools | Prompt/SOUL only — no code change |

---

## Findings

| ID | Severity | Summary |
|----|----------|---------|
| S51F-AUD-05 | MEDIUM | S2: no pre-tool assistant text (MEASURED); acknowledgement did not fail in the chunker — it was never generated |
| S51F-AUD-06 | MEDIUM | SentenceChunker `min_len=20` can hold short pre-tool lines; tool-start deliberately skips TTS EOS (`turn_tool_round`) |
| S51F-AUD-07 | INFO | SOUL already asks for a few words before slow work; not enforced in code |
