P1-MEMORY: document the prompt-only [tag] convention and the raised budget snippet — P1-D05

Zola keeps notes in Hermes's existing flat files: `MEMORY.md` for Zola's own notes and `USER.md` for facts about Brian. Each entry starts with one lowercase tag in square brackets, then the fact. One tag per entry. Examples:

- `[project] The Windows client is the current surface.`
- `[person] Brian is the person this profile is for.`
- `[preference] Brian wants a straight answer when a short one will do.`
- `[car] Keep vehicle facts under this tag when one comes up.`

That set is the whole convention. It is not a taxonomy and it is not a schema.

Hermes does not parse or require the brackets. `MemoryStore` and the memory tool accept any text, and nothing in this track checks the prefix. The convention is an instruction for how entries should be written. It is not code-enforced.

Routing (P5-D04): facts about Brian as a person — identity, preferences, people in his life — go in `USER.md` (`user`). Facts about his world — projects, vehicles, decisions, conventions, how things are set up — go in `MEMORY.md` (`memory`). Tie-breaker: if a fact could fit both, store it once in the file for what it is primarily about; never duplicate it to satisfy both.

Brief mention (P5-D03): when Zola saves something on her own (not after "remember this"), she mentions it in a few natural words and continues.

Conversation search (P5-D06): she searches past conversations only when Brian asks about something from an earlier conversation that is not already in her notes, and she says roughly when it was. She does not search on her own for ordinary turns. Search results are evidence for the current answer, not memory — nothing found by `session_search` is saved just because it was found.

P5-MEMORY note (P5-D03–D06): lasting-fact saving, routing, brief mention, and explicit-only conversation search are governed by the live `SOUL.md` "What I remember" section and this file; they override the memory tool's general "save less" guidance.

The live profile config that raises the budgets is outside this repo, at `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`. Reapply this block to restore it:

```yaml
# P1-MEMORY: 2x Hermes defaults (2200/1375) on the existing flat-file store — P1-D05
memory:
  memory_char_limit: 4400
  # P5-MEMORY: USER.md budget raised for lasting-fact saves — P5-D05
  user_char_limit: 4000
```

Hermes deep-merges that section over its defaults, so the other `memory` keys stay at their defaults. A fresh `MemoryStore` built from the profile config should report `memory_char_limit` 4400 and `user_char_limit` 4000. `hermes serve` reads the file on launch.

## Structured store (P6)

Two kinds of memory, one authority each. The flat files (`USER.md` / `MEMORY.md`) remain the
authority for current durable facts — written only through the memory tool. A local Zola store
keeps a structured index of those facts (stable IDs, lifecycle times) and will later hold
episodes. The index is always rebuildable from the files. Episodes, when they exist, are the
store's own authority; they may reference facts but never create or change them.

Invariants in short: Zola authors facts through the memory tool; the store does not write the
files and does not invent facts. Correction keeps a content history; forget erases every copy
the memory system controls and leaves only a content-free tombstone. Ambiguous disappearances
and unclear "replace vs forget" cases resolve toward erasure. Retrieval never becomes
persistence.

(P6-D01–D07)
