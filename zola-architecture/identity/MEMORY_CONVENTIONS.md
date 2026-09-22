P1-MEMORY: document the prompt-only [tag] convention and the raised budget snippet — P1-D05

Zola keeps notes in Hermes's existing flat files: `MEMORY.md` for Zola's own notes and `USER.md` for facts about Brian. Each entry starts with one lowercase tag in square brackets, then the fact. One tag per entry. Examples:

- `[project] The Windows client is the current surface.`
- `[person] Brian is the person this profile is for.`
- `[preference] Brian wants a straight answer when a short one will do.`
- `[car] Keep vehicle facts under this tag when one comes up.`

That set is the whole convention. It is not a taxonomy and it is not a schema.

Hermes does not parse or require the brackets. `MemoryStore` and the memory tool accept any text, and nothing in this track checks the prefix. The convention is an instruction for how entries should be written. It is not code-enforced.

The live profile config that raises the budgets is outside this repo, at `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`. Reapply this block to restore it:

```yaml
# P1-MEMORY: 2x Hermes defaults (2200/1375) on the existing flat-file store — P1-D05
memory:
  memory_char_limit: 4400
  user_char_limit: 2750
```

Hermes deep-merges that section over its defaults, so the other `memory` keys stay at their defaults. A fresh `MemoryStore` built from the profile config should report `memory_char_limit` 4400 and `user_char_limit` 2750. `hermes serve` reads the file on launch.
