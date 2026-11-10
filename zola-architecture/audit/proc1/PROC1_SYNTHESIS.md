# PROC1 Synthesis

**Audit:** PROC1 · Phase 3 · read-only  
**Prompt:** v1.1 · SHA-256 `94f130a0e81abb6a56a73d0bfd00ce5ab53c550bcaffed0b1295dbe0dc1d542f`  
**Inputs:** `PROC1_01`–`05`; Brian facts 2026-11-09 (verbatim where quoted)

---

## Serious issues (stability-gate / privacy-security)

Under the SOP’s serious bar (privacy or security leak, safety-gate bypass), this audit did **not** find a new leak or a bypass of the send/phone gates in source. Consequential actions still go through the existing Google token + send passphrase (P8-D06) and phone pairing (P10-D12).

What this audit **does** elevate as process-critical (not a new code CVE, but the reason the first process track exists):

1. **Working-tree is the everyday build.** Brian launches with `dotnet run` against the live checkout. Every launch rebuilds from whatever is checked out there — including another branch or uncommitted edits. That is the top isolation/stability risk below; it is not a privacy leak by itself, but it is how crash-watch and daily use stay coupled to Cursor’s tree.

No separate “serious” privacy/security finding is filed beyond the known S51 crash track already on the seriousness path (PR-D03 / OPEN_QUESTIONS S51). Residual hygiene (live `phone_test_keys` mirror historically, large client logs) belongs in known-issues seeds, not this serious list.

---

## 1. Current state in plain English

Brian starts Zola from PowerShell with:

`dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj`

That means everyday Zola is whatever source is currently in `C:\Users\test\Dev\zola-windows` — not a pinned folder of last-good bits. He has said an **executable** (and by implication a stable shortcut) would be better. The client resolves Hermes from a sibling `hermes-agent` (or `ZOLA_HERMES_ROOT`), always uses the hard-coded live profile `%LOCALAPPDATA%\hermes\profiles\zola`, and shares one Hermes checkout + venv with anything else on the machine. That profile holds the **real** Google OAuth token (Brian: “Yes”), the real phone pairing key, memories, proactive store, and Hermes session DB. Client logs and the Deepgram key live under `%LOCALAPPDATA%\ZolaClient\`. There is no client single-instance lock; phone/watcher mutexes only protect some children. Tests are seven separate commands; the phone suite fails two mutex tests while Zola is up. The four SOP v3 lore files do not exist yet. Stable and development are not separate because nothing has been built to separate them — the first process track is meant to create that infrastructure, starting with a stable folder so daily use and the crash watch leave the working tree.

---

## 2. Gap table (target state vs today)

| # | Target-state rule | Today | Gap | Evidence | Diff. | Needs Hermes source? |
|---|---|---|---|---|---|---|
| T1 | Stable = promoted release in its **own folder**, day-to-day | `dotnet run` on live working tree; Debug/bin under repo | No stable folder; launch rebuilds from checkout | Brian verbatim; PROC1_01 | M | **No** |
| T2 | Development = working tree / track branch for build+test only | Same tree is everyday launch | Dev edits = next everyday binary | Brian; PROC1_01 | S–M (once T1 exists) | **No** |
| T3 | Dev resolves every persistent path under a confirmed **dev data root**; fail closed | Client hard-codes `profiles\zola`; Deepgram absolute path | No fail-closed dev profile | PROC1_02 | L | **No** for client/`HERMES_HOME`; Deepgram script is Zola-side. Hermes already honors `HERMES_HOME` |
| T4 | Dev holds only **test Google** credentials; real send/calendar/Drive impossible | Live `token.dpapi` = real account | Any client on live profile can act as Brian | Brian “Yes”; PROC1_02 | M | **No** |
| T5 | Separate phone port + pairing key | Fixed 47821, `Local\ZolaPhone`, one `pc_key.bin` | Dev cannot safely share phone stack with stable | PROC1_02, _03 | M–L | **No** (contract/env/client); companion default port is Zola Android |
| T6 | Nothing copies from dev back to stable | N/A — same trees | Shared files make “copy” unnecessary | PROC1_02 | — | **No** |
| T7 | One build at a time: **refuse** and name which; never stop the other | No client mutex; second client can attach; child mutexes only | No stable/dev identity or refuse UX | PROC1_03; Brian never runs two on purpose | M | **No** |
| T8 | PR-D01 one-command test gate (suites separate, skips, missing/zero fail, SHA, FAIL≠INFRA) | Seven manual commands; phone mutex vs live | No runner; live-stable conflict | PROC1_04 | M–L | **No** |
| T9 | Lore: known-issues, scenarios, experience log, fast-lane log | Missing; seeds scattered | Create four files + seed | PROC1_05 | S | **No** |
| T10 | Rollback = launch previous tag | Schema refuse-newer on `proactive.db` (v8); shared pin | Tag alone unsafe without data+pin restore | PROC1_01 §6 | M | **No** for Zola stores; Hermes `state.db` format may track pin (UNVERIFIED) |

**Hermes no-fork (2026-10-06):** nothing in the gap table requires forking Hermes. Isolation is `HERMES_HOME` + Zola client/plugins + separate checkouts/venv copies as needed.

---

## 3. Isolation risk list (ranked)

Hard isolation lines: **Google token** and **phone pairing**.  
Cost-only if shared (no consequential account/device action): **Deepgram key**, **Hermes `auth.json` (LLM provider)**.

| Rank | Risk | Why it matters | Reach |
|---|---|---|---|
| **R1** | **`dotnet run` on the live checkout** | Every everyday launch rebuilds from current branch / uncommitted changes. Crash watch and daily use track Cursor’s tree. | Running stable behavior = whatever is in the worktree |
| **R2** | Dev or any client uses hard-coded **`profiles\zola`** | Same `token.dpapi` (real Google), same memories, same proactive DB | Real email / calendar / Drive / memory |
| **R3** | Shared **phone** mutex, pipe, port 47821, `pc_key.bin` | Second phone loses; first keeps device; tests collide; a “dev” phone cannot safely pair beside live | Real phone / block stable phone |
| **R4** | Shared **`hermes-agent` + `.venv`** | Package install or pin move changes stable’s backend without a client rebuild | Stable behavior drift / break |
| **R5** | Second client **attach** to live serve | Two UIs, one backend; close semantics confuse ownership | Running stable process |
| **R6** | Dual serve same `HERMES_HOME` if attach misses | Concurrent SQLite writers | Data corruption risk |
| **R7** | Shared Deepgram key path | Same paid TTS key; **cost-only**, not a Google/phone action | Billing / quota |
| **R8** | Shared Hermes `auth.json` (LLM) | Same provider credentials; **cost-only** | Billing / quota |
| **R9** | Large client logs (e.g. **~280 MB `presence.log`**) | Disk / privacy retention seed for known-issues — not an action path | Local disk; review retention |
| **R10** | Rollback by tag without store backup | Old client refuses newer `proactive.db` | Availability / crash-watch recovery |

---

## 4. Suggested wave order (options, not a locked plan)

Constraint: **stable folder first** so Brian’s Zola and the crash watch leave the working tree.

| Wave | Deliverable (option shape) | Lets SOP switch on |
|---|---|---|
| **W1** | Stable folder + Release executable from tag `fix-s51f` (or later promote) + Desktop/Start shortcut; set `ZOLA_HERMES_ROOT` (and Python) so TEMP-style discovery does not fail; Brian stops using `dotnet run` for everyday | Everyday ≠ working tree; crash watch can pin to the folder |
| **W2** | Build identity + single-instance refuse (“stable is running” / “dev is running”) without killing the other | One-build-at-a-time rule for following tracks |
| **W3** | Dev profile root (fail closed) + client override off hard-coded `zola`; **test Google** token only; separate phone port/pairing (or fake_phone-only until paired) | Isolation rule for consequential actions |
| **W4** | Optional: separate Hermes checkout/venv for stable (if not done in W1) | Shared-Hermes risk closed |
| **W5** | One-command test runner (PR-D01); phone suite INFRA when mutex held | Test gate for following tracks |
| **W6** | Lore files seeded (known-issues incl. S51 + **~280 MB presence.log**, scenarios, experience, fast-lane) | Lore v3 artifacts |

Promotion/rollback backup of profile stores can attach to W1 or sit between W1 and W3 so “previous tag” becomes meaningful.

---

## 5. Decisions for Brian (options, trade-offs, recommendation)

### D1 — Where the stable folder lives + how he launches it

| Option | Trade-offs |
|---|---|
| **A. Folder under e.g. `%LOCALAPPDATA%\ZolaStable\` or `C:\Users\test\App\Zola\` + shortcut to `Zola.Client.exe`** | Matches his preference for an executable; clear split from Dev; needs Hermes root env or layout so discovery works |
| **B. Keep launching via `dotnet run` but on a second clone/worktree pinned to the tag** | Still rebuilds every launch; slower; easier to accidentally wrong-tree |
| **C. Shortcut to today’s Debug `bin\` exe without a promote step** | Fast but still tied to last local build of the working tree |

**Recommendation: A.** He already asked for an executable; W1’s job is to make everyday launch a shortcut to a promoted Release build, with `ZOLA_HERMES_ROOT` set so S51F’s TEMP failure cannot recur.

### D2 — Self-contained vs framework-dependent publish

| Option | Trade-offs |
|---|---|
| **A. Framework-dependent win-x64** (csproj default today) | Smaller folder; needs .NET 9 / WinAppSDK on the machine (already true for him) |
| **B. Self-contained** | Larger; more portable if runtimes drift; longer publish |

**Recommendation: A for the first stable.** Same machine already runs the app; ship speed and simplicity beat portability until a second PC appears.

### D3 — Does stable get its own `hermes-agent` copy?

| Option | Trade-offs |
|---|---|
| **A. Own checkout + venv at the recorded pin, beside the stable folder** | Protects stable from Dev package/pin moves; more disk; two update paths |
| **B. Share `C:\Users\test\Dev\hermes-agent` via `ZOLA_HERMES_ROOT`** | Simple for W1; **R4** remains until W4 |
| **C. Own checkout later (W1 share, W4 split)** | Fastest path off `dotnet run`; deferred isolation of the backend |

**Recommendation: C (share for W1, split in W4).** Gets him off the working-tree launch immediately; closes R4 before isolation-heavy tracks, without blocking the first promote.

### D4 — Dev profile name and root

| Option | Trade-offs |
|---|---|
| **A. `%LOCALAPPDATA%\hermes\profiles\zola-dev`** | Same Hermes layout; easy `HERMES_HOME`; clear sibling of `zola` |
| **B. Entirely outside Hermes profiles (e.g. `%LOCALAPPDATA%\ZolaDev\home`)** | Harder to confuse with live; still must fail closed in client |
| **C. Repo-local `.zola-dev-home/`** | Convenient for tests; easier to commit by mistake / cleaner for CI later |

**Recommendation: A.** Matches how Hermes already isolates profiles; client change is “profile name + fail closed,” not a new path scheme. Keep live name `zola` for stable.

### D5 — Deepgram key and Hermes `auth.json` when isolating

| Option | Trade-offs |
|---|---|
| **A. Share both for early waves** | Cost-only risk (R7/R8); no Google/phone consequential action; less setup |
| **B. Separate Deepgram key and LLM auth for dev from day one** | Cleaner billing attribution; more secrets to mint |
| **C. Share LLM auth; separate Deepgram when TTS script path is parameterized** | Middle path |

**Recommendation: A until after W3.** Hard lines are Google + phone. Parameterize Deepgram path when building fail-closed dev so a later split is easy; do not block isolation on TTS billing.

### D6 — Phone while stable is the everyday build

| Option | Trade-offs |
|---|---|
| **A. Dev uses fake_phone / no Tailscale bind until a second device or port+pairing exists** | Safest for R3; no real texts from dev |
| **B. Separate port (e.g. 47822) + separate pairing key + second companion build** | Real phone testing from dev; more moving parts |
| **C. Stop stable whenever phone tests or phone-dev runs** | Breaks crash-watch / everyday use — conflicts with SOP v3 intent |

**Recommendation: A for W3 defaults; B when he wants real companion testing.** Never C as the steady state.

### D7 — Single-instance refuse UX

| Option | Trade-offs |
|---|---|
| **A. Modal in the second UI naming role + path + pid** | Clear; matches “refuse and say which” |
| **B. Console / log only** | Easy to miss for shortcut users |
| **C. Both** | Best coverage; slightly more work |

**Recommendation: C**, with modal required for shortcut launches (his target everyday path).

### D8 — Test gate vs live `Local\ZolaPhone`

| Option | Trade-offs |
|---|---|
| **A. Mutex-held → those two tests = INFRA (not PASS), rest of phone suite still runs** | Stable can stay up; gate stays honest |
| **B. Gate requires stable stopped** | Green mutex tests; breaks crash-watch / everyday |
| **C. Separate phone INFRA job off the main gate** | Clear reporting; easy to ignore INFRA |

**Recommendation: A** as the PR-D01 default while stable is normally up; schedule occasional B only when he deliberately closes Zola.

### D9 — Kotlin scope in the one-command gate

| Option | Trade-offs |
|---|---|
| **A. `testDebugUnitTest` only** | Faster; covers 98 unit tests |
| **B. Also `assembleDebug`** | Catches packaging breakages; slower; needs SDK |

**Recommendation: A in the default gate; B on promote / nightly.** Matches “fail on missing suite” without making every commit wait on assemble.

### D10 — Where the four lore files live

| Option | Trade-offs |
|---|---|
| **A. Root siblings under `lore/`** | Matches `DESIGN_DECISIONS` / `OPEN_QUESTIONS` / `ROADMAP` |
| **B. `lore/process/`** | Tidier if process docs grow; one more hop |

**Recommendation: A** for the first cut.

### D11 — Speech-baseline material

| Option | Trade-offs |
|---|---|
| **A. Cite `zola-spikes/speech-baseline` from known-issues / scenarios** | No copy drift; spikes stay canonical for raw runs |
| **B. Copy summaries into lore** | Self-contained repo; duplication |

**Recommendation: A**, with short titled entries in known-issues/scenarios that point at the spike findings.

### D12 — Rollback / promote backup

| Option | Trade-offs |
|---|---|
| **A. On every promote: backup `proactive.db`, `zola_memory.db`, `state.db`, `token.dpapi`, `phone\`, `config.yaml` (+ note hermes pin)** | Makes previous-tag rollback plausible |
| **B. Tag-only rollback** | Insufficient (PROC1_01) |
| **C. Full profile zip every promote** | Safest; larger |

**Recommendation: A minimum; C if he wants one-button restore.** B is not a real option given schema refuse-newer.

---

## 6. Known-issue seed (explicit)

Add to the future known-issues list when W6 lands:

- **`%LOCALAPPDATA%\ZolaClient\logs\presence.log` ~280 MB** (OBSERVED Phase 2) — retention / rotation / privacy review; not an action-authority issue.

Also seed from PROC1_05: S51 Group A/B, S51F admit→submit gap, phone mutex vs live tests (S100 hygiene), etc.

---

## 7. Answers already locked by Brian (Phase 3)

| Topic | Verbatim / fact |
|---|---|
| Everyday launch | “I usually start Zola from powershell using: `dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj`, but it would probably be better to have an executable” |
| Live Google token | “Yes” (real everyday account) |
| Two windows on purpose | “No” |

---

*End of synthesis. Phase 3 STOP — await proceed to commit and merge (Phase 4).*
