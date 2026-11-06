# P10-WATCH Progress — watches, forget and watched-text speech

## Branch

- Primary folder: `C:\Users\test\Dev\zola-windows`, branch `main`
- Worktree: `C:\Users\test\Dev\zola-windows-p10-watch`, branch `p10-watch`
- Base SHA: `166acb13af227fd8584905b399e92238e407dedd` (`main` = `origin/main` at Phase 1)
- Worktree HEAD: `7c701d9b27e125b8601ba82d40439fc9f8a94cf8` (implementation). The 7d commit records this SHA.
- Hermes HEAD: `345cd2b057a452236de401d3534b8502a7465e8d` (clean, no porcelain)
- Prompt: `P10-WATCH_Prompt_v1.1.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P10-WATCH_Prompt_v1.1.md`)
- Prompt SHA-256 (on-disk, 76,371 bytes): `176e4adde68d056fe7257e54282d6661681519ea119c366e555ad3ee7f83b668`
  - Confirmed in the Phase 3 start (Claude read this value back after writing the file). Phase 1 discrepancy 1 is closed.
- Scratch: `C:\Users\test\Dev\zola-spikes\p10-watch\` (created; suite logs and the read-only inventory script only)
- Track 5 closeout tip this branch was cut from: `166acb13af227fd8584905b399e92238e407dedd`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Setup | COMPLETE (STOP) |
| 2 | Grounding | COMPLETE (STOP) |
| 3 | Proposal | COMPLETE (verdicts below) |
| 4 | Implement and bench | STOP. Bench recorded. |
| 5 | Review checkpoint | Run sheet amended after review. STOP for "proceed to phase 6". |
| 6 | Smoke | Passed. Phase 6 report is written. Open watches 0. |
| 7 | Closeout | Merged. 7i waits on his confirmation of the live state. |

## Guardrails summary

- **G-SCOPE:** `zola_workspace` loops, matcher, speech, surface, store (speech hold, coalescing, loop and forget), contact index only to report match quality, and tests; `zola_phone/runtime.py` only for the evaluation view and coalescing at intake, and tests; client `Speech/` for text phrasings and check rows; `zola_memory/forget.py` only for a Phase 3 forget seam; `watcher.py` only if Phase 3 approves an email-view change; contracts only for an approved gateway method; schema only if Phase 3 approves; this progress doc; live mirror and `SOUL.md` only in approved deploy steps (P4-D25).
- **G-ARCH:** build plan v1.4 and Appendices A/B are truth. RD-W1–W13 stop for Brian.
- **G-PATTERN / G-ONE-RESOLVER / G-CONFIRM-FUZZY / G-BRIAN-WORDS / G-NO-SILENT-WIDENING / G-KNOWN-NOT-TRUSTED / G-SPEECH / G-NAME-ONLY / G-ONE-LINE / G-FORGET-COMPLETE-OR-HONEST / G-TOLD-MEANS-TOLD / G-UNTRUSTED / G-NO-BACKGROUND-MODEL:** as written in the prompt.
- **G-NOCHANGE:** no `hermes-agent`, R1 code path, ranker, Gmail/Calendar/Drive readers, `send_gate`, `zola_tools`, `zola_tts`, companion, `phone_protocol.json`, lore, or `config.yaml`. No Track 5 briefing or pending-rule change beyond a phone-correct watched line. No reply/send (P10-D17). No notification watch matching (P10-D15). No commitment watches (ARCH-15).
- **G-NO-TEST-SWITCH / G-ENTRY-POINTS / G-LIVE-FAULTS / G-INSTALLS / G-PHONE-HANDS-OFF / G-PRIVACY / G-PROCESSES / G-COMMENT / G-STOP / G-CLOSEOUT / G-LORE-SCOPE / G-LIVE:** as written. No lore edits. Live steps one at a time.

## Phase 1 — Setup

`git fetch origin` in the primary folder. `git status --porcelain` was empty. `main` = `origin/main` = `166acb13af227fd8584905b399e92238e407dedd`.

Worktree list before `git worktree add` (no `p10-read` entry):

```
C:/Users/test/Dev/zola-windows  166acb1 [main]
```

After the worktree:

```
C:/Users/test/Dev/zola-windows            166acb1 [main]
C:/Users/test/Dev/zola-windows-p10-watch  166acb1 [p10-watch]
```

Primary `main` stayed clean. Hermes stayed clean at the pin. No source files were modified. This progress doc is the only new tracked file (uncommitted). Scratch logs live under `C:\Users\test\Dev\zola-spikes\p10-watch\` and are never committed. `android-companion/local.properties` was written as a gitignored SDK pointer so Gradle could run (`sdk.dir=C:/Users/test/AppData/Local/Android/Sdk`).

The leftover folder `C:\Users\test\Dev\zola-windows-p10-read` still exists. It is not a registered worktree. Its top level is a `hermes-plugins` directory. It was not opened further and was not modified.

### Plugin suites (worktree, Hermes venv)

Python: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`.

The Zola client was **not running** during this Phase 1 suite pass. No `Zola.Client` process, no serve, no watcher, and no `zola-phone`. Named pipe `\\.\pipe\ZolaPhone` was absent (winerror 2). Ports 47821 and 47822 had no listener. This is the client-closed run, so the two `zola_phone` mutex tests are included in the green 62.

| Suite | Command | Result | Floor |
|---|---|---|---|
| `zola_workspace` | `python -m unittest discover -s tests -t tests` | **505** OK (130.443s) | 505 |
| `zola_memory` | `python -m unittest discover -s tests -t .` | **134** OK (19.878s) | 134 |
| `zola_tools` | `python -m unittest discover -s tests -t .` | **44** OK (0.205s) | 44 |
| `zola_tts` | `python -m unittest discover -s tests -t .` | **8** OK (0.420s) | 8 |
| `zola_phone` | `python -m unittest discover -s tests -t .` | **62** OK (54.280s), mutex included | 62 |

No suite hung, skipped, or stopped early. Each log ends `OK` and `EXIT:0`.

### Client

`dotnet build windows-client\Zola.Client\Zola.Client.csproj -c Release -o %TEMP%\zola-p10-watch-client-build`: succeeded, **0 warnings, 0 errors**.

`dotnet run` of `Zola.Client.Checks` (-c Release): the first attempt used `--no-restore` and failed with `NETSDK1004` because the fresh worktree had no `project.assets.json`. The same command was rerun with restore. That run exited 0. **0** lines starting `FAIL`, **248** lines starting `PASS`.

coverage: lifecycle rows 22/22, admission rows 13/13, start rows 9/9, invalid pairs 6/6, stop_phrase rows 4/4, amendments 7/7, latch rows 18/18, wiring rows 9/9, clarify rows 20/20, timing rows 8/8, compress rows 8/8, supervision rows 38/38, speech rows 38/38, phone rows 16/16, code rows 32/32.

The checks compile logged **9** `CA1416` warnings on the Windows-only speech synthesizer calls. The client project build itself stayed at 0 warnings. Row floors:

| Row | Floor |
|---|---|
| lifecycle | 22 |
| admission | 13 |
| start | 9 |
| invalid pairs | 6 |
| stop_phrase | 4 |
| amendments | 7 |
| latch | 18 |
| wiring | 9 |
| clarify | 20 |
| timing | 8 |
| compress | 8 |
| supervision | 38 |
| speech | 38 |
| phone | 16 |
| code | 32 |

### Kotlin

`android-companion\gradlew.bat testDebugUnitTest assembleDebug` (`--offline`; `JAVA_HOME` = Android Studio JBR; `local.properties` gitignored SDK path).

BUILD SUCCESSFUL in 2m 9s. `CompanionRulesTest` 15, `EngineFlowTest` 39, `NoticeFlowTest` 30, `Phase4Test` 14. **98**, 0 failures, 0 errors, 0 skipped.

### Live profile (read only)

Live plugin tree: `%LOCALAPPDATA%\hermes\profiles\zola\plugins`. Compared every `.py`, `.json`, `.yaml`, and `.yml` except `__pycache__` and `tests`.

| Result | Count |
|---|---|
| Byte-identical | 62 |
| Newline only (equal after CRLF→LF; live LF, worktree CRLF) | 3 |
| Content differs | 0 |

Newline-only: `zola_tools/__init__.py`, `zola_tools/calculator.py`, `zola_tools/plugin.yaml`.

Present in the worktree plugin tree and not under the live `plugins` directory: `zola_memory/l6_hold_guard.py` (test helper), `zola_tts/deepgram_tts.py`. The live TTS script at `profiles\zola\zola-tts\deepgram_tts.py` matches the worktree file (5,596 bytes).

The Track 5 content difference in `zola_phone/tools/fake_phone.py` is gone: that file is in the identical set.

`phone_test_keys.json` is **absent** from `plugins\zola_phone\`. It **is** present at `plugins\zola_workspace\contracts\phone_test_keys.json`, 2,183 bytes, SHA-256 identical to the tracked worktree fixture. `zola-phone` loads `phone\pc_key.bin` (`keys.py`), not that fixture. Not modified.

Speech holds on the matching live `proactive_store.py` (worktree lines 78–79): `P10_TEXT_NO_UNPROMPTED_SPEECH = True`, `P10_NOTIF_NO_UNPROMPTED_SPEECH = True`.

`proactive.db` opened `mode=ro`. `user_version` 0. `schema_version` **7**. SHA-256 `c891322f0d1e01106df705bb665e3f8980d79c094a3776e0fa5e9ed1922a221a`, 2,310,144 bytes. Cut-off `phone_surface_cutoff_at` = `2026-11-03T17:08:23Z`.

Table counts: calendar_events 1088, cursors 5, deliveries 0, item_attempts 612, items 1771, loops 9, meta 8, phone_tombstones 1, watcher_health 1, watcher_rejects 7.

Loops: **0 open**. All 9 are `status=closed`, `intent=reply`, `name_source=mail`.

Tombstones: 1. Oldest `created_at` `2026-10-19T22:30:48Z` (age 15.99 days at the read).

Items by source: calendar 48, gmail 592, mms 963, notif 36, sms 132.

Phone rows (sms + mms + notif = 1131). Every phone row is `loop_matched=0`, `watch_evaluated=1`, `delivery=none`.

| Source | content_state | Count |
|---|---|---|
| mms | available | 460 |
| mms | content_expired | 503 |
| sms | available | 74 |
| sms | content_expired | 58 |
| notif | available | 36 |

`SOUL.md`: 10,316 bytes, SHA-256 `2cff9fa4832ac6fcc1b41096a9b17da9786a3bf0740aebcbcb4c76b03e6d5f5c`.

`config.yaml`: 4,850 bytes, SHA-256 `823dbd95c6d63eb66be07182faa82acb5c48528a79f01109b6c4120560c74afc`. `proactive.speak_enabled: true`. No other config line was recorded.

`phone\` file sizes only: `pc_id.txt` 34, `pc_key.bin` 498, `peer_state.json` 570. Peer shape only: `device_id` length 32, `public_pem` length 178, `rejected` count 1, `link_open` false, `closed_at` `2026-11-04T17:03:40Z`, `pc_seq` 1822, `phone_seq` 29536. No key material recorded.

`tailscale ip -4`: `100.102.206.71`. Nothing listening on 47821 or 47822.

### Live processes (read only)

No Zola client, serve, watcher, or `zola-phone` was running. The status pipe was not present, so there is no live `zola-phone` status payload.

| Role | PID | Parent | Start (local) | Notes |
|---|---|---|---|---|
| java (pre-existing) | 19600 | 47740 (gone) | 13:30:05 | Gradle/Android daemon from before this track. Not stopped. |
| java worker | 3052 | 19600 (alive) | 14:11:43 | Worker of that daemon, seen during the Kotlin run. Not stopped. |
| VBCSCompiler | 11556 | 20760 (this track's `dotnet`, gone) | 14:11:55 | Compiler server left by the client build. Stopped by PID after the suites. |

Suite shells this track started (workspace, memory, tools, tts, phone, client, Kotlin) all exited. Their child processes exited, except 11556, which was stopped. No Zola orphan was found before or after the launches.

### `zola-phone` status

Not available. The process is not running and `\\.\pipe\ZolaPhone` does not exist (winerror 2). Peer file says the link is closed as of `2026-11-04T17:03:40Z`.

### Phone (read only, USB serial `R5CW81KPB6X`)

`adb` is `C:\Users\test\AppData\Local\Android\Sdk\platform-tools\adb.exe`. `adb devices -l` listed USB `R5CW81KPB6X` (`SM_S918U1`, product `dm3quew`, transport_id 5). Every command used `-s R5CW81KPB6X`.

- Android 16, SDK 36, model `SM-S918U1`.
- Companion `com.beebo.zola.companion` `versionName=1.1.1`, `versionCode=10`, minSdk 36, targetSdk 36.
- `enabled_notification_listeners` **contains** `com.beebo.zola.companion` (6 components; other names not logged).
- On-device notice file, keys only: `listener_permission=1`, `listener_bound=1`, allowlist count 3, packages `com.instagram.android`, `com.life360.android.safetymapd`, `com.tmobile.vvm.application`. Item count 1. Bodies were not read.
- Companion files via `run-as`, sizes only: `companion-state.json` 239,022; `companion.log` 858,794; `.1` 999,998; `.2` 999,955; `.3` 999,940; `install.json` 115; `notification-queue.json` 54,349; `profileInstalled` 24. Contents were not read, except the notice keys above.

### Entry gate

No `google-services.json`, no `credentials.json`, no `client_secret*.json`, no `.env` under the worktree. `android-companion/local.properties` is gitignored (SDK path only, written for Gradle). The worktree's only matching name is the tracked fixture `hermes-plugins\zola_workspace\contracts\phone_test_keys.json`. Live `plugins\zola_phone\phone_test_keys.json` is absent. The same fixture is on the live plugin mirror under `contracts\` and matches the repo byte for byte. The phone runtime does not load it.

### Discrepancies (recorded, not blocking Phase 1)

1. No developer-supplied prompt SHA was in the Phase 1 instruction. Closed at Phase 3: Claude confirmed the on-disk SHA above.
2. Leftover folder `C:\Users\test\Dev\zola-windows-p10-read` still exists and is not a git worktree. Not touched.
3. Live `plugins\zola_workspace\contracts\phone_test_keys.json` is present and identical to the repo fixture. `plugins\zola_phone\phone_test_keys.json` is absent. Runtime key file is `phone\pc_key.bin`. Not modified. Residual for the lore closeout. This track does not change it.
4. Three live `zola_tools` files differ from the worktree by newline only (live LF, worktree CRLF).
5. The Zola client and `zola-phone` were not running, so there is no live status payload. Peer file shows the link closed at `2026-11-04T17:03:40Z`. Phone-side listener is granted and bound.
6. A pre-existing Gradle/Android java daemon (PID 19600, parent gone) was already running. Not stopped. Its worker 3052 was still alive after the Kotlin run.
7. The checks project compile logged 9 CA1416 warnings. The `Zola.Client` Release build logged 0 warnings and 0 errors, and every check row passed.

## Phase 2 — Grounding (2026-11-04)

Read-only. No source files modified. Build plan v1.4 Sections 1–5, Track 5 RD-G1, Track 6 WA-G1–G4 and W1–W7, Appendix A P10-D13–D15, Appendix B §1, §5, §8. Architecture drafts were read and not edited. Where a draft and Appendix A differ, Appendix A governs.

### Probes

| Probe | What it read | Result (counts and shapes only) |
|---|---|---|
| Live `proactive.db` `mode=ro` | Row counts after the stored cut-off `2026-11-03T17:08:23Z` | After cut-off, available: gmail 38, mms 60, sms 35, notif 25. All `loop_matched=0`. Unwatched text sender-groups after cut-off: 13. Gmail available and `loop_matched=1`: 0. Four gmail rows are `loop_matched=1` and `forgotten`, all before the cut-off. |
| People API refresh through `contact_index` (`HERMES_HOME` = the live zola profile, sync refresh) | In-memory index only. No names, numbers, or addresses printed. | Refresh ok. People 277. With an email 63. With a number 248. Shared number hashes 0. The scripted test contact's name token matched **0** people. W1b cannot use a live address until that contact is present again. |

### What the code does today

Watches are handle-only. `loops.py` `_ALLOWED_KEYS` is `{action, handle, intent, loop_id}` (line 60) and `_INTENTS` is `{reply, cancelled, status_change, confirm_close}` (line 61). `compile_predicate` (lines 110–170) builds `gmail_thread` + `sender_is` + `not_source` + `after`, or a calendar predicate. `create_loop` (lines 192–258) requires `turn_context.is_brian_turn()` and refuses any key outside the allow list.

No phone row can match. `loop_match._occurred_at` (lines 29–32) reads `internal_date` for every non-calendar item. `runtime._evaluate_item` (lines 930–939) passes `source`, `message_id`, `sender_address_hash`, and `detected_at`, and does not pass `internal_date`, so `after` is false. The watcher view (`watcher.py` lines 476–483) does pass `internal_date`. Notifications take the same ingest path (`runtime.py` lines 786–836) and are evaluated.

A match leaves the loop open. `note_loop_match_on_loop` (lines 2713–2753) sets `matched_at` once and keeps `status='open'`. The comment at line 2719 says matched is not closed.

Speech holds are still on. `P10_TEXT_NO_UNPROMPTED_SPEECH` and `P10_NOTIF_NO_UNPROMPTED_SPEECH` are `True` (`proactive_store.py` lines 78–79), read at call time (lines 132–139), and applied in `_speech_block_reason` (lines 2113–2116) and both claim queries. Claim also requires `loop_matched=1`.

Phrases are email-shaped. `speech.py` `GMAIL_NAMED`, `GMAIL_UNNAMED`, `CALENDAR_LINES` (lines 37–52). `_name_for_item` (lines 184–212) walks `sender_is` only and skips `name_source='mail'`. `SpeechPhrases.Pick` (`SpeechPhrases.cs` lines 28–43) uses Calendar for `calendar` and the Gmail sets for everything else. Nothing in the client checks reads `speech.py`. `test_p9_speak.py` `test_sanitizer_and_unnamed_lines` (lines 498–512) checks the Python tuples only. Equality is a comment in `SpeechPhrases.cs` line 3, not a test.

Forget is entity- and email-shaped. `handle_forget_memory` with no matching entity appends `MSG_PROACTIVE_UNMAPPED` (`forget.py` lines 65–67 and 1518–1520): the pending list is not touched. `_alias_hashes` (lines 1262–1273) hashes aliases that contain `@` only. `_forget_subject` (lines 2888–2976) links by entity id, sender hash, source id, or `_name_hit` (substring of subject, snippet, or gist, and only when an entity id is given, lines 2859–2866). In-flight rows (`_IN_FLIGHT` line 107: `claimed`, `speech_started`, `delivery_uncertain`) are redacted, including `sender_hint` (line 2936), and are not tombstoned. Deleted phone rows are tombstoned (lines 2925–2926). `name_source` CHECK is `mail`, `contacts_ticket`, `brian_message` (line 535). `CLOSED_INTENTS` (lines 37–39) has no `delivered` or `acknowledged`.

The contact index cannot say exact versus fuzzy. `_person_matches_query` (lines 162–187) returns one boolean for a full-name exact match, a single-token exact match, and a fuzzy edit. `Person` (lines 46–55) stores `display_name` only. Other People API name fields are not kept.

`SURFACE_TELL_LINE` (lines 71–76) already says to use the block when it helps the current request and not to open with a rundown. `SURFACE_LOOP_ASK` (lines 103–107) still says "a reply on a thread" and "ask whether to keep watching or stop." `_collapse_key` (lines 446–451) returns `None` for `loop_matched` rows, so watched texts are not collapsed. Inject cap is `SURFACE_ITEM_CAP = 4` (line 34), with one reserved contact-text slot (lines 885–895).

### RD-W1 — The watch tool

Stay on `zola_loops`. Add intents `person` and `number`. Add allowed arguments `person`, `number`, and optional `channel` (`text`, `email`, `both`). Keep `address`, `email`, `sender`, `from`, and any hash forbidden (`loops.py` lines 48–59). A model-supplied address still refuses as `untrusted_argument`.

The channel is decided in code from Brian's own message, not from the model:

| Set | Phrases | Result |
|---|---|---|
| `CHANNEL_TEXT` | "texts", "text", "texts back", "text back", "messages me", "messages" | text only (`sms` and `mms`, including RCS stored as MMS) |
| `CHANNEL_EMAIL` | "emails", "email", "writes", "sends an email", "emailed" | email only (`gmail`) |
| `CHANNEL_BOTH` | "hear from", "gets back to me", "get back to me", "reaches out", "contacts me", or no channel word | both |

A message that hits both a text phrase and an email phrase means both, and the reply says she heard both. If the model also passes `channel` and it disagrees, the tool returns `channel_disagrees` and creates nothing.

The name or number must occur in Brian's message. Names use `_speech_form` (`contact_index.py` lines 107–116). Numbers use `phone_ids.normalize` (lines 60–81): the canonical digit run must appear as a contiguous digit run in his message. Two exceptions, and only these: the confirmation token (RD-W2), and a pronoun reference (RD-W11).

Compiled predicates, all with `after` set to creation time:

- Person, two numbers and one email, no channel word: `all` of `sender_any` (three hashes), `channel` `both`, `after`.
- Same person, "when she texts": `sender_any` of the number hashes only, `channel` `text`, `after`.
- Spoken number not in Contacts: `sender_any` of that one hash, `channel` `text`, `after`. `name_source` stays empty of a person name.
- Spoken number that is one contact's number: same one-hash text watch. Contacts may name it in the reply. She may ask "That's Beebo Dev's number. Want me to watch for Beebo Dev on any channel?" Only a later yes on the widen token creates a person watch. The number watch is not replaced until that yes.
- Name not in Contacts: refuse. Reply shape: "I can't find that name in your contacts. If you tell me the number, I can watch that."
- Shared number (`resolve_person_by_phone_hash` returns none when two people own it, lines 530–538): refuse naming, ask which person.
- Several name matches: ask, display names only, nothing created.
- Name only inside a text body: refuse. The check reads `turn_record.user_message` (`create_loop` lines 203–204), never a tool result.

Create result for Zola to say back: "I'll let you know when Beebo Dev texts or emails." It carries a Contacts name. It does not call `mark_then_frame` (`loops.py` lines 319–330), because that path is for mail subject and display name. A list that still contains a mail loop keeps today's untrusted frame. A person or number row in that list shows the Contacts name, or "a number", plus the channel. No digits on a number watch, in the tool result or in her words. The list does not taint beyond today's mail rule.

The created reply states the freeze only if Phase 3 asks for that sentence. P10-D13 already accepts that numbers and addresses are frozen at creation (`PHASE10_BUILD_PLAN.md` lines 1267–1268). Default proposal: one short clause in the create result, "I'll use the numbers and email addresses saved for them right now."

### RD-W2 — Fuzzy confirmation

Smallest index addition, still the one matcher: `match_quality(person, query)` returning `exact`, `token`, `fuzzy`, or `none`, using `_speech_form`, `_compact_form`, `_name_tokens`, and `_fuzzy_allowed` (lines 107–187). `exact` is the full display name after that normalization. `token` is a single name token that is not the full name (a first name alone). `fuzzy` is the existing edit-distance hit. `match_people_by_name` stays the finder.

Watch create and forget treat `exact` as ready. `token` and `fuzzy` return `confirm_needed` with the resolved display name and a confirmation token. Several matches return `which` and the display names, and the token is minted only after he names one of them.

The token lives in process memory, bound to `session_id`, the person handle, and the action (`watch_person`, `watch_widen`, `forget_person`, `forget_widen`, `watch_lifetime`). TTL `CONFIRM_TTL_SECONDS = 120`. It is refused from another session, after the TTL, for another action, and if the word "yes" arrives only inside a text body or a tool result. The check reads the next Brian turn's `user_message`.

Yes, with the same negation window as `code_phrase.py` (`NEGATION` line 40, `BLOCKER_WINDOW` line 37): "yes", "yeah", "yep", "that's right", "correct". "don't", "not", and "no" in that window refuse. No: "no", "nope", "don't", "cancel", "never mind", "wrong". Any other reply drops the token and changes nothing.

Memory forget already confirms (`forget.py` lines 1464–1514, hold 30 minutes and 3 turns, lines 76–78). One question, not two. If the person is also a memory entity, the yes authorizes both the memory erase and the proactive payload. If there is no memory entity, the same yes authorizes the proactive forget alone. Today's unmapped sentence (lines 65–67) is what happens only when Contacts also fails to resolve the person.

### RD-W3 — Matching

Add to `loop_match._node_matches`:

- `sender_any`: the item's `sender_address_hash` is in `address_hashes`.
- `channel`: `text` matches `source` in `sms`, `mms`; `email` matches `gmail`; `both` matches those three. `notif` matches nothing. There is no `notif` channel.

Time fix inside `_occurred_at`: `sms`, `mms`, and `notif` compare `detected_at` (the phone's local received time, P10-D08, already stored as `detected_at` by `ingest_phone_item` lines 1106–1107). Gmail keeps `internal_date`. Calendar keeps `event_updated`.

The phone view already has `detected_at` (`runtime.py` lines 934–939). The watcher view already has `internal_date` (`watcher.py` lines 476–483). No watcher change for the operators. Existing reply and calendar predicates keep the same operators and stay green.

A notification cannot match: the channel operator rejects `notif`, and `set_loop_matched` refuses `source='notif'` even if a predicate is wrong. Intake test goes through `_ingest` (`runtime.py` line 784), not a helper with arguments production never passes. Startup recovery (`_recover` lines 187–193) and a duplicate resend still evaluate an item once: `mark_watch_evaluated` stays, and `note_loop_match_on_loop` returns `already` when `matched_at` is set (lines 2738–2740).

### RD-W4 — Watch lifetime

Proposal **(c)**. "Let me know when", "tell me when", and "when I hear" compile `lifetime: once`. "Every time", "whenever", and "each time" compile `lifetime: standing`. "Keep an eye on" returns a clarifying question and creates nothing until he answers on the `watch_lifetime` token. Ambiguous is asked, not guessed.

Satisfaction, for both lifetimes: a match never closes the watch. `matched_at` set and `status='open'` is the recorded matched-not-told state. The item stays pending. The watch closes only when:

| Reason | When | Recorded `closed_intent` |
|---|---|---|
| delivered | playback outcome is delivered | `delivered` |
| acknowledged | conversation acknowledgement, the Phase 9 meaning | `acknowledged` |
| cancelled | he stops that watch | `cancelled` (already allowed) |
| expired | `expires_at` | `expired` (already allowed) |

Quiet hours, a busy turn, a released claim, and `delivery_uncertain` leave it open and the item pending. The next conversation may say she tried earlier. It does not say she told him. `delivery_uncertain` is not delivered.

One-shot closes on the first of those four reasons for the matched item. Standing stays open and can match again after the burst window (RD-W7). Closing one watch does not close another watch that also matched the item (A11 §6.0: removing a delivery item never closes anything else, lines 205–206).

Email reply loops have no `lifetime` key and keep Phase 9 behavior: they stay open and keep matching. Default expiry stays `LOOP_DEFAULT_EXPIRY_DAYS = 14` (line 61), max 90.

`delivered` and `acknowledged` are not in `CLOSED_INTENTS` (lines 37–39) or the v2 CHECK. Adding them is a schema change. See the schema note below. `lifetime` itself fits in `predicate_json` with no new column. Matched-not-told needs no new column.

### RD-W5 — How the line is delivered

What exists: the coordinator refuses while a turn is in flight, capture is up, or playback is up (`ProactiveDeliveryCoordinator.cs` lines 476–499), waits until idle for `IdleSeconds = 20` (lines 510–524, `SpeechConstants.cs` lines 6 and 13–14), and keeps quiet hours 22–07 (`Quiet` lines 504–508). A07 §5 (lines 192–200) says immediate listening exists after ordinary replies and not after unprompted lines (P9 D7(a)). ARCH-21 is a spoken ask and no on-screen cue. ARCH-22 waits for a natural pause unless time-critical. The idle and turn gates are the pause this client can enforce. Nothing listens after the line.

Proposal **(c)**: one fixed line that is an attention opener and the who, in one breath, inside the sets in RD-W6. **(b)**, the two-step "got a second?" that waits for an answer, needs listening after an unprompted line. That belongs to the speech pipeline, not this track. Building half of it would ask a question he cannot answer. **(a)** and **(c)** do not let him choose whether he is ready. That choice is the point of the 2026-10-25 principle, and this track records the gap as a Phase 10 limit, not as a rule that the office-door ask is unwanted. Phase 12 can lift it.

### RD-W6 — Phrasings and names

Same tuples in `speech.py` and `SpeechPhrases.cs`. A new check reads the C# arrays and compares them to the Python tuples. Every set rotates and does not repeat the last index (`SpeechPhrases.Take`, lines 45–58).

`TEXT_NAMED` (office-door, name only):

- "Brian, quick one: {name} texted you."
- "Heads up, {name} just texted."
- "Quick one: you've got a text from {name}."
- "Brian, {name} texted you."
- "{name} just sent you a text."

`TEXT_UNNAMED` (Contacts name fails `sanitize_name`, lines 83–93):

- "Brian, someone you asked me to watch for just texted."
- "Heads up, someone you're watching for just texted."
- "Quick one: a text from someone you asked me to watch for."

`TEXT_NUMBER`:

- "Brian, that number you asked me to watch just texted."
- "Heads up, that number you asked me to watch just texted."
- "Quick one: a text from the number you're watching."

`EMAIL_PERSON` (a person watch whose item source is gmail; do not reuse "wrote back" / "that email you were waiting on"):

- "Brian, quick one: {name} emailed you."
- "Heads up, {name} just emailed."
- "Quick one: you've got an email from {name}."
- "Brian, {name} emailed you."

The channel word comes from the item's `source` (`sms`/`mms` → texted, `gmail` → emailed). It is not content. `Pick` and `IndexOf` key off that family. Calendar stays calendar. Deny log and HUD fields stay as they are.

Name provenance: `name_source` value `contacts_index`, set at creation from `Person.display_name` after `sanitize_name`. `_name_for_item` also collects hashes from `sender_any`, not only `sender_is` (lines 171–181). It ignores `forgotten` loops and loops whose display name was cleared. A number watch uses `TEXT_NUMBER` and no name. Constants cite P10-D15 and ARCH-11: content to a known-private audience is a later decision (ARCH-11 lines 185–189). Phase 10 speaks who, not the body.

`contacts_index` is not in the v5 CHECK (`proactive_store.py` line 535) or `NAME_SOURCES` (line 55). Insert would return `bad_args` (lines 2678–2680). That is a schema change, named below.

### RD-W7 — Bursts

One owner: claim time, in `_claim_next_speech` / `_speech_block_reason`. Evaluation still records every match. Coalescing changes speech only.

`BURST_WINDOW_SECONDS = 180`, measured from the anchor item's `detected_at`, not sliding. The anchor is the oldest item for that person that already has a speech `item_attempts` row of any status. A later item whose `detected_at` falls in `[anchor, anchor + 180s]` is not claimable. The window is per person across channels: a text and an email that share a watch's hash set count as one person. Releasing a claim sets the attempt to `released` and leaves the row (`_release_speech_claim` lines 2521–2528), so a restart, a resend, or a second claim does not speak the rest of the burst.

Before any attempt exists, claim takes the oldest speakable row (`ORDER BY detected_at, id`, lines 2240–2241). The newer row then fails the window check. No item is marked `delivered` or `acknowledged` because another item was spoken. The unspoken rows stay `delivery='none'` and still surface.

No count in the spoken line. A count is closer to content, and the burst size may still be growing at claim time.

Overlapping watches on one item: the item is claimed once, the line is chosen once, and each open watch records its own match. Satisfying one watch does not write the other's `closed_intent`. A text and an email inside the window produce one claim. Both items stay pending. Only the claimed item moves through delivery.

No new column. The attempt row is the marker. This is not a schema change.

### RD-W8 — The forget seam

Proposal **(a)**. `forget_memory` stays the only entry and the only confirmation. When the description resolves through the contact index, the proactive payload gains every canonical number hash, every email hash, and the display name. `forget.py` does not import the workspace stack at load. It already finds `proactive_store` by the `PROACTIVE_STORE_MARKER` scan (lines 1219–1226). The new lookup is a function on that module, `contact_forget_keys`, and `proactive_store` calls `contact_index`. Memory's change is: call that function, and if it resolves, run `forget_subject_from_profile` even when `entities_matching` is empty.

Today an unknown memory subject never reaches proactive (lines 1518–1520). That is why a contact with no entity, every phone number, and every notification display name are out of reach (S85).

"Forget" plus a number: normalize, forget items and watches for that one hash, and do not include the person's other numbers or email. If Contacts names the number, the reply says it is that person's number and asks whether to forget the person. Only the widen token does that. Same rule as a number watch (G-NO-SILENT-WIDENING).

### RD-W9 — What forget removes

Items: every text whose sender hash is one of the person's number hashes; every email whose sender hash is one of their email hashes; rows already linked by entity id; every open watch whose `address_hashes_json` overlaps, closed `forgotten` with name and subject cleared (the update at lines 2958–2969).

Notifications: `source='notif'` and `sender_display_name` equals the contact's display name after `_name_key` (case, spacing). Not a substring. Not a first name. The index does not store other names (`Person` lines 46–55). Matching "other names" would mean keeping more of the People `names[]` array in memory. That is beyond the contact-index scope in G-SCOPE (quality only). Proposal: display name only, unless Phase 3 approves retaining the other whole names already returned by the same fetch. `_name_hit` (lines 2859–2866) stays a substring for email content when an entity id is present. It is not used for notifications.

In flight: redact as today, and also tombstone the phone identity key at redaction. The speech attempt ends without a delivered outcome. A line already playing finishes; it has no content after redaction; the outcome call is refused cleanly. Test `claimed`, `speech_started`, and `delivery_uncertain`.

`sender_hint` is already cleared on redaction (line 2936). Add the test. Deletion removes the row, so the hint goes with it.

Tombstones: `identity_key_hash` of the install-based key (Appendix B §1, §5, §8), content-free, 30 days (`PHONE_TOMBSTONE_KEEP_DAYS` line 100). Purge deletes tombstone rows older than 30 days (lines 3115–3118) and does not delete live items in that statement. A resend, a catch-up replay, and a re-pair of the same install hit the tombstone check in `ingest_phone_item` (lines 1109–1114) and ack `suppressed`.

Reinstall, grounded: `CompanionEngine.openInstall` (lines 75–102) generates a new `device_id` when no install file exists and sets the SMS and MMS cursors to `provider.maxId`. `CursorMachine.baseline` (lines 55–62) does that once. `Notice.baseline` (around lines 381–384 and 573–577) does not send notifications already showing. Tombstones are keyed by `device_id`, so they do not cover the new install. The history read (`phone_tools.py` lines 1–3 and 358–421) returns live phone texts and does not write `proactive.db`. A new install can still surface an old text if Brian asks for a history read, because that read is the phone's store and is not a replay into `proactive.db`. Replay protection across a reinstall rests on the companion's first-run baseline, not on tombstones. That limit is stated here and in the forget tool's documentation. The forget reply does not claim the phone's history was erased.

Concurrency windows:

1. `runtime._evaluate_item` loads predicates (line 933), then `note_loop_match_on_loop` and `set_loop_matched` in later transactions (lines 940–948). `note_loop_match_on_loop` already requires `status='open'` (lines 2735–2737). `set_loop_matched` does not look at the loop (lines 3546–3574). A forget can close the loop between the two calls, and the item can still become `loop_matched`.
2. The watcher does the same split: `_matching` (lines 173–183) then `note_loop_match_on_loop` and `mark_loop_eligible` (`watcher.py` lines 200–222).
3. `_claim_next_speech` requires `loop_matched=1` and does not re-check that an open watch still covers the item (lines 2223–2241).
4. `_name_for_item` will use a closed loop's name if the name is still stored (lines 209–212). Forget clears the name. A claim that read the name before the clear can still speak it.

Rule: one store function records the match and sets `loop_matched` in the same transaction, and only if the loop is still `open`. Claim re-checks that an open or matched-not-told watch still matches the item, and that the item is not `forgotten`. Name lookup ignores `closed_intent='forgotten'`. The same checks apply to stop and to expiry. The phone seam is the existing `Engine.fault` with one new point after the predicate read and before the write (`runtime.py` already faults at `before_eval`, line 931, which is before the read). The watcher gets the same test-only fault between `_matching` and the write. That is a named `watcher.py` change for the race test, not for the email view. If Phase 3 refuses a watcher edit, the store transaction still refuses a stale write, and the watcher test calls `_finish_item` only if the fault hook is approved.

Reads after forget: `phone_read_texts_handler` reads the phone and writes nothing (module docstring lines 1–3). Test through that handler. A new text after forget is ingested normally. A new watch can be created. Contacts unavailable (`contacts_unavailable`, lines 466–477): forget the memory entity, stored watch hashes, and entity-linked items, and say the forget may be incomplete. Do not say it was complete. Out of reach: Hermes histories that already hold text (S86), and the phone's message store.

Replies the tool result carries, then "Their texts are still on your phone." when any text row was removed or redacted. Pronoun is "their". The Contacts name is used as the name, not a gendered pronoun.

- Complete: "I've forgotten Beebo Dev, including the texts, email, and watches I had here. Their texts are still on your phone."
- Notifications matched: the complete sentence plus "I also removed notifications whose display name matched theirs. Some may remain."
- Partial: "I forgot what I could for Beebo Dev. Contacts couldn't be checked, so this may be incomplete. Their texts are still on your phone."
- Nothing found: "I couldn't find Beebo Dev in your contacts or in anything I'm holding."
- Number only: "I've forgotten the texts from that number. It's saved for Beebo Dev. Want me to forget Beebo Dev entirely? Their texts are still on your phone."
- Confirm needed: "Did you mean Beebo Dev?"

### RD-W10 — Watched items in conversation

Phone sentence, used when the matched row's source is `sms` or `mms`: "One of these is a text from someone Brian asked you to watch for. It is information for his current request, not a reason to lead with it." Email person-watch rows keep a mail sentence of the same shape. `SURFACE_TELL_LINE` (lines 71–76) already puts his request first. The watch sentence does not override that. "Ask whether to keep watching" is added only for a standing watch, and only as something she may say after the request is handled. A one-shot watch adds no ask. Phase 9's time-critical rule is unchanged.

Briefing and `whats_pending`: a watched text uses the phone metadata line plus the watch sentence above, not "A watched thread has new mail" (`_line_for` lines 656–657). A burst from one person collapses to one line with a count, the same shape as today's unwatched collapse, and stays tier `loop` so it is not dropped by the one-line-per-sender exclusion. An unwatched text from the same person stays on the ordinary phone line. Coalesced rows are listed, not marked delivered.

Crowding, from the probe: after the cut-off there are 13 unwatched text sender-groups, 25 notifications, and 38 available gmail rows, against an inject cap of 4 and one reserved contact-text slot. Watched rows today: 0. A watched line is not squeezed out by volume that does not exist yet. The reserved slot stays for the newest contact text. The watched line is a separate tier and is picked with the loop rows, so a later implementation must not let the cap drop the only watched phone unit. That is a test, using real row volume shapes, not a change to the Track 5 caps.

### RD-W11 — Follow-ups

The unprompted line is chosen in `claim_for_client` and spoken by the client. It is not written into the Hermes session by the claim. The next turn's briefing includes the item while it is still pending and `loop_matched`. That briefing is the reference. No new memory table.

"What did they say?", "stop watching for her", "forget him": resolve a pronoun only to a person this session's watch create, watch list, or spoken claim named from the contact index or from a watch's `contacts_index` name. Never from a text body, a notification title, or a mail subject. One such person: the question calls `phone_read_texts` live; "stop watching" closes that watch. Two: she asks which. A one-shot watch already closed answers "That one already closed" and does not invent a second watch.

### RD-W12 — Bench, smoke, faults

Backups and a one-step restore script before any live file change, as Track 5. Expected result written before each cell. Daytime. One sending number. The live contact's name is Bebo. Every bench expected result uses that name. The one-letter misspelling is Beebo.

| Cell | Method | What Brian sees | Undo |
|---|---|---|---|
| W1b email | The scripted test contact has **0** name-token hits in the current index, so no live address was counted. If Brian adds an email on that contact before the bench, the watcher evaluates a real message. A scratch harness row also runs the watcher path against a copy of the store. | One email line, name only. | Close the watch. The harness uses the scratch copy. |
| W4 notification | Scratch store, real `_ingest` of a fake-phone `notifications.event` whose display name equals the contact. Live check: no notification row claimed in the speech log for the whole cell. A live Instagram DM is not required. | Silence. | Scratch store discarded. |
| W5 number not in Contacts | Brian removes the extra sending number from the test contact when told. Cursor refreshes the index and records counts only. He speaks the number, sends, hears the number line, then restores the number. An open person watch on the contact is a different watch and stays a person watch. | Number line, no name, no digits. | He puts the number back. Cursor confirms the index counts. |
| W6 replay | Real ingest of the forgotten identity against a backup-API copy of the live store in a scratch home. Expect `suppressed`. Live tombstone count recorded. No live file edited to inject the fault. | Counts only. | Delete the scratch home. |
| W7 Contacts down | No clean live method that avoids editing a live file. Run W7 on a scratch serve with `contact_index`'s existing test seam for an unavailable index. Say so in the run sheet. | Partial reply, never a full-forget claim. | Scratch serve stopped by PID. |
| W10 quiet hours | Unit and check tests with the existing clock. Live smoke is daytime, so quiet hours are not exercised live. | Tests only. | None. |
| Unprompted window | Cursor watches the speech log for 90 seconds after the text is stored, while Brian is idle. Silence means zero claims. One claim with the approved phrase index is the pass. A second claim is a fail. | He reports what he heard. | Close the watch. |

### RD-W13 — Tests

All through the real entry points named in the prompt. Names to add:

`test_person_watch_unnamed_channel_both`, `test_person_watch_text_only`, `test_person_watch_email_only`, `test_person_watch_several_numbers_and_emails`, `test_number_watch`, `test_number_watch_on_a_contact_does_not_widen`, `test_widen_only_after_yes`, `test_name_missing_from_contacts_refused`, `test_shared_number_asks`, `test_name_only_in_text_body_refused`, `test_number_only_in_text_body_refused`, `test_channel_argument_disagrees`, `test_keep_an_eye_on_asks`, `test_phone_row_matches_on_detected_at`, `test_notification_never_matches_through_ingest`, `test_reply_and_calendar_predicates_unchanged`, `test_fuzzy_confirm_yes`, `test_fuzzy_confirm_no`, `test_fuzzy_token_lapses`, `test_fuzzy_token_other_session`, `test_fuzzy_token_other_action`, `test_fuzzy_token_text_body_yes`, `test_confirmation_turn_without_name`, `test_one_shot_stays_open_through_quiet_hours_release_and_uncertain`, `test_one_shot_closes_delivered_acknowledged_cancelled_expired`, `test_burst_three_texts_one_claim`, `test_burst_across_phone_restart`, `test_burst_resend`, `test_burst_window_boundary`, `test_text_and_email_one_line_both_pending`, `test_overlapping_watches_one_claim`, `test_text_phrases_sms_mms_both_sides`, `test_unwatched_text_never_claimed`, `test_notification_never_claimed`, `test_quiet_hours_unchanged`, `test_forget_person_texts_emails_notifications_watches`, `test_forget_number_only`, `test_forget_contact_number_asks`, `test_forget_in_flight_claimed`, `test_forget_in_flight_speech_started`, `test_forget_in_flight_uncertain`, `test_sender_hint_cleared`, `test_tombstone_on_delete_and_redact`, `test_resend_suppressed`, `test_replay_suppressed`, `test_repair_resend_suppressed`, `test_read_after_forget_stores_nothing`, `test_new_text_after_forget_stored`, `test_partial_reply_index_down`, `test_confirm_needed_reply`, `test_forget_race_phone`, `test_forget_race_watcher`, `test_stop_race_phone`, `test_stop_race_watcher`, `test_briefing_watched_phone_line`, `test_briefing_task_before_watched_item`, `test_pending_watched_burst_one_line`, `test_followup_pronoun_live_read`, `test_pronoun_two_people_asks`, `test_reinstall_limit_documented`.

### Schema, memory, watcher

- **Schema 8, a STOP.** Two CHECK constraints cannot take the new values any other way: `name_source` needs `contacts_index`; `closed_intent` needs `delivered` and `acknowledged`. `lifetime` and burst state do not need columns. Migration is tested on a scratch copy of the live store first, counts before and after. If Brian refuses the schema, the fallback is to reuse `contacts_ticket` and to record satisfaction in `predicate_json` while leaving `closed_intent` as `cancelled` for both stop and "he heard it", which hides the reason. The proposal is the schema, not the fallback.
- **`zola_memory/forget.py`:** the seam in RD-W8. Named for Phase 3.
- **`watcher.py`:** no email-view change. One test-only fault between the predicate read and the match write, so the race tests can interleave. Named for Phase 3.

### Drafts versus Appendix A

A11 §6.2 (lines 240–241) says she tells him and asks whether to keep watching. Appendix A P10-D13 does not require that ask, and a one-shot watch must not ask. The ask is proposed only for a standing watch, after his request. A11 §6.1's example "Tell me when Micah texts" is one-shot under RD-W4. ARCH-11 allows content to a known-private audience; the name-only lines are a Phase 10 limit. ARCH-15 commitment watches are out of scope. ARCH-21's two-step ask is not built here (RD-W5). A04 line 50: a saved contact is a known sender, not closeness or trust. No comment, tool description, or phrase in this track calls a watched person trusted.

### SOUL and privacy

Proposed `SOUL.md` lines, not written: a watch says when to speak up, not who matters; a forget removes what this PC is holding and never deletes texts from the phone. Privacy page: no change proposed. The Track 5 phone paragraph already covers texts reaching this PC. Watches do not send a new category of content, and forget does not touch the phone.

## Phase 3 — Proposal (2026-11-04) — STOP

No source changes. No lore edits. The phone was not touched. Phase 2 leans stand unless this section amends them. Nothing here is a verdict.

Q1, Q2, Q6, Q7, Q8 and Q9 are inside decisions 11, 3, 5, 8, 10 and 12. Decisions 13–16 are the extra questions from the Phase 3 review.

### Decisions

**1. Watch tool, Brian's words, channel (RD-W1).**
Approve the Phase 2 tool: same `zola_loops`, intents `person` and `number`, arguments `person` / `number` / optional `channel`, model addresses still forbidden. The name or number must be in his message, except the confirmation token and the pronoun path in decision 10. Channel from his words: text phrases, email phrases, both when unnamed.
Ordinary-word rule, added here: "text" or "email" counts as a channel only as the request ("when she texts", "texts back", "sends an email"). A noun does not ("about the text I sent"). "Let me know when I hear from Beebo Dev about the text I sent" is both, because the request is "hear from". Test `test_text_as_ordinary_word_is_both`.
Create reply includes one freeze clause: "I'll use the numbers and email addresses saved for them right now."
- Option A (lean): this shape.
- Option B: drop the freeze clause.
- Consequence: A tells him the watch will miss a number added in Google later. B leaves that tradeoff only in the build plan.

**2. Fuzzy confirmation, including widen (RD-W2).**
`match_quality` returns `exact` / `token` / `fuzzy` / `none` from the one index. Exact proceeds. First-name-only and fuzzy return `confirm_needed` and a token bound to session, person handle, and action. TTL 120 seconds. Yes: yes, yeah, yep, that's right, correct, with the `code_phrase.py` negation window. No: no, nope, don't, cancel, never mind, wrong. Anything else drops the token. Refused from another session, after the TTL, for another action, and from a text body.
Widen uses that same token, TTL, and yes/no. Actions `watch_widen` and `forget_widen`. Tests `test_widen_token_lapses`, `test_widen_token_other_session`.
One question when a memory entity also exists: the same yes authorizes both.
- Option A (lean): this.
- Option B: a longer TTL (the memory hold is 30 minutes and 3 turns).
- Consequence: A expires if he does not answer on the next turn. B leaves a yes available longer, including after he has talked about something else.

**3. Lifetime, satisfaction, and muting the rest of a one-shot (RD-W4, Q2).**
"Let me know when" / "tell me when" / "when I hear" → `once`. "Every time" / "whenever" / "each time" → `standing`. "Keep an eye on" asks and creates nothing. Unlisted phrasing is decision 15. Default expiry stays 14 days, max 90. `lifetime` lives in the predicate. No new column.
A match sets `matched_at` and leaves the watch `open`. That is matched-not-told. Close only on delivered, acknowledged, cancelled, or expired, each with its own `closed_intent`. Quiet hours, a released claim, and `delivery_uncertain` leave it open. `delivery_uncertain` is not delivered. The next conversation may say she tried. It does not say she told him.
Mute rule, stated here: while a one-shot is still open, later items from that person are also `loop_matched`. When the first line is delivered and the watch closes `delivered`, claim refuses every other item that matched that watch. Those items stay `loop_matched` and still surface in conversation. They are not a second spoken line. Claim allows an item only when an open or matched-not-told watch still covers it. A standing watch is not muted by one delivery.
Test `test_one_shot_satisfied_mutes_later_matches`: two texts an hour apart, both matched while the watch is open, the first delivered, the second never claimed, the second still surfaces as a watched item.
- Option A (lean): one-shot / standing / ask, as above, plus the mute rule, expiry 14 days.
- Option B: every watch is standing.
- Option C: every watch is one-shot, and "every time" is refused.
- Consequence: B on a busy sender is decision 14's volume. C cannot do "every time" without a second request.

**4. How the line is delivered (RD-W5).**
One breath: an attention opener and the who, inside the fixed sets. The idle gate (20 seconds) and the turn/capture/playback gates are the pause this client already enforces. Nothing listens after the line.
This is a Phase 10 limit. It is not a decision that the office-door ask is unwanted. The two-step "got a second?" needs listening after an unprompted line (A07 §5, P9 D7(a)) and stays Phase 12.
- Option A (lean): one breath, recorded as a limit.
- Option B: direct email-style lines with no attention opener.
- Option C: build the two-step ask in this track.
- Consequence: A and B do not let him choose whether he is ready. C is speech-pipeline work this track does not contain.

**5. What the line says (RD-W6, Q6).**
Name only, recorded as a Phase 10 limit, not as a rule that content is unwanted (ARCH-11). Channel word comes from the item source. No count. No digits. `name_source` `contacts_index` when schema 8 is approved (decision 12).
Every line opens with an attention word: "Brian,", "Heads up,", or "Quick one:". Phase 2's fifth named line, "{name} just sent you a text.", has no opener. It is replaced. The other Phase 2 sets already open correctly.

`TEXT_NAMED`:
- "Brian, quick one: {name} texted you."
- "Heads up, {name} just texted."
- "Quick one: you've got a text from {name}."
- "Brian, {name} texted you."
- "Brian, quick one: {name} just sent you a text."

`TEXT_UNNAMED`, `TEXT_NUMBER`, and `EMAIL_PERSON` stay as Phase 2 wrote them. Group lines are decision 14. Same tuples in `speech.py` and `SpeechPhrases.cs`, checked equal, last line not repeated.
- Option A (lean): these sets, name only, as a limit.
- Option B: put message content in the line.
- Consequence: B conflicts with P10-D15 and ARCH-11's "audience unknown → who only" until a known-private audience is a real check. This track does not add that check.

**6. Burst window and how a burst sounds (RD-W7).**
`BURST_WINDOW_SECONDS = 180` from the anchor item's `detected_at`, not sliding. Per person, across text and email. Spoken line has no count. Coalesced items stay pending and are not marked delivered or acknowledged. Overlapping watches: one claim, one line, each watch records its own match. The case where he is busy and a later text was already waiting is decision 13.
- Option A (lean): 180 seconds, no count in the line.
- Option B: a different window (he names it).
- Consequence: a shorter window splits a burst he would hear as one. A longer window holds a second topic behind the first line.

**7. Forget seam, and forgetting a contact's number (RD-W8).**
Extend `forget_memory`. No second tool. Memory does not import the workspace stack at load. It calls a new `proactive_store` function, which calls `contact_index`. If Contacts resolves the person, proactive forget runs even when there is no memory entity. One yes covers both when an entity exists.
"Forget" plus a number removes that number only. If Contacts names it, she says so and asks whether to forget the person. Only the widen token does. The number watch rule and the number forget rule are the same: no silent widening.
- Option A (lean): extend memory forget.
- Option B: a separate forget tool for phone items.
- Consequence: B is a second path. A is the only confirmation he already has.

**8. Forget rules and replies (RD-W9, Q7).**
Notifications: whole display name only, after the index's spacing and case normalization. Not a substring. Not a first name. Other People API names are not kept.
Miss, so the reply is honest: a notification whose display name is "Beebo" does not match the contact "Beebo Dev". It stays. The reply says some may remain only when at least one notification was removed.
The sentence is built from the kinds actually removed. No spoken counts. "Their texts are still on your phone." only when that person has at least one number.

| Store state | Reply |
|---|---|
| Texts removed. No email. No watch. Has a number. | "I've forgotten Beebo Dev, including the texts I had here. Their texts are still on your phone." |
| Texts and email. No watch. Has a number. | "I've forgotten Beebo Dev, including the texts and email I had here. Their texts are still on your phone." |
| Texts, email, and watches. Has a number. | "I've forgotten Beebo Dev, including the texts, email, and watches I had here. Their texts are still on your phone." |
| Those, plus at least one notification removed by display name. | The matching sentence, then "I also removed notifications whose display name matched theirs. Some may remain." |
| In Contacts. Nothing held. Has a number. | "I wasn't holding anything for Beebo Dev. Their texts are still on your phone." |
| In Contacts. Nothing held. No number. | "I wasn't holding anything for Beebo Dev." |
| Not in Contacts. Nothing held. | "I couldn't find Beebo Dev in your contacts, and I'm not holding anything under that name." |
| Contacts unreachable. | "I forgot what I could for Beebo Dev. Contacts couldn't be checked, so this may be incomplete." Phone sentence only if a stored row already had one of their number hashes. |
| Number only. Contacts names the person. | "I've forgotten the texts from that number. It's saved for Beebo Dev. Want me to forget Beebo Dev entirely?" Phone sentence because the number itself is a number. |

In flight: redact and tombstone. A line already playing finishes with no content. `sender_hint` stays cleared. Tombstones cover resend, catch-up replay, and re-pair of the same install. They do not cover a new install. That limit stays in the forget documentation. The phone is never touched. A forget does not delete the Google contact.
- Option A (lean): display name only, replies from this table.
- Option B: also keep other whole names from the same People fetch.
- Consequence: B removes more notifications and needs a contact-index change beyond match quality. A leaves "Beebo" in place and says so when it did remove a full-name row.

**9. Watched items in conversation (RD-W10).**
Phone sentence, after the Track 5 line that puts his current request first: "One of these is a text from someone Brian asked you to watch for. It is information for his current request, not a reason to lead with it." "Ask whether to keep watching" only for a standing watch, and only after the request. A one-shot adds no ask. A watched burst collapses to one briefing line. The spoken line still has no count. Track 5 caps and the metadata-only rules stay.
- Option A (lean): this sentence.
- Option B: keep the Phase 9 "reply on a thread" sentence for phone rows too.
- Consequence: B describes a text as mail.

**10. Follow-up after a spoken line (RD-W11, Q8).**
The spoken claim is not a Hermes session record, and it is not a pronoun source. The check reads three in-memory records, all keyed by `session_id`, all written by serve on this session:

1. Watch create and watch list. Create already adds the loop id to `loops._listed` (`loops.py` line 247). List replaces that set (line 278). The person handle is the one stored on those loops.
2. Briefing lines injected this session. `surface` records the person handle of each watched phone or email row it injects. It does not parse the prose.
3. A `phone_read_texts` result this session whose person was resolved from (1), (2), or from his own words.

Zero matches: she asks who. Two: she asks which. She never takes a person from a text body, a notification title, or a mail subject.

One stop path. The model does not supply a `loop_id`. The close handler resolves the person from those three records, finds that person's open watch, adds that loop id to `_listed` if create or list has not already, and closes it `cancelled`. Same session as the create: the id is already listed, so this adds nothing. A watch from an earlier session: the briefing record is what names the person, and the handler lists that one id itself. Already closed `delivered` or `acknowledged`: "That one already closed." Test `test_stop_pronoun_one_path` covers create-then-stop, briefing-then-stop, and no-reference.
"What did they say?" uses the same resolution, then a live `phone_read_texts`. Nothing is stored.
- Option A (lean): these three records, and the handler produces the loop id.
- Option B: she must call list aloud and he must confirm before any close.
- Consequence: B adds a turn after every "stop watching for her". A closes the watch he just heard about.

**11. Bench, smoke, and the missing test contact (RD-W12, Q1).**
The scripted contact had 0 name-token hits (Phase 2 probe: 277 people). W1, W1b, W3, W5, and W6 have no person until Brian recreates it. That step is first, on the bench list and on the run sheet.

Brian, before any watch cell: in Google Contacts, recreate the test contact with the Google Voice number and one email address he can send from. Cursor refreshes the index and records counts only. Pass: one person matched by exact name, numbers 1, emails 1, shared-number hashes 0. Fail: stop, no watch created.

Order after that, so later cells still have the contact:

1. W1, W1b, W1c, W2, W2b, W3, W3b, W3c. These need the number and the email.
2. W5. He removes the Google Voice number when told. Cursor confirms counts (numbers 0 on that person). He speaks the number, sends, hears the number line. He puts the number back. Cursor confirms numbers 1, emails 1. An open person watch is a different watch and is not widened into, or replaced by, the number watch.
3. W4. Notification display name. Scratch ingest plus a live check that no notification row is claimed.
4. W6. Forget. This removes phone items, email items, and watches on this PC. It does not delete the Google contact. The run sheet says that, so he does not recreate the contact afterward.
5. W6b. A little new data, then forget the number only.
6. W8, W9, W10, and the RCS probe if one arrives.
7. W7 is decision 16.

W6 replay stays on a scratch copy through real ingest. No live-file edit. Quiet hours stay on the unit clock. Live smoke is daytime.
- Option A (lean): this order, contact recreate first, forget does not touch Google.
- Option B: skip live W1b until an email exists and run only the harness row.
- Consequence: B leaves the live email path unproven if he does not add the address.

**12. Schema 8, deploy, SOUL, privacy (Q9).**
`_migrate` refuses a newer `schema_version` (`proactive_store.py` lines 285–288). `zola-phone`, the watcher, and serve all open this database. Old code cannot run on schema 8.

Schema 8 rebuilds `loops` so the CHECKs accept `name_source` `contacts_index` and `closed_intent` `delivered` and `acknowledged`. Items, tombstones, and attempts are not rebuilt. `lifetime` and burst state need no column. Phase 4 runs the migration on a scratch copy of the live store first and logs counts before and after: loops equal, items equal, tombstones equal. Live migrate only in the deploy below.

Deploy: Brian closes the client. Cursor confirms no Zola client, serve, watcher, or `zola-phone`. Backup `proactive.db` through the backup API, plus the plugin files the mirror will replace, with SHA-256, and a one-step restore script in the scratch folder. Mirror the new code. Open the database once with the new code so the migration commits. Then start the client from the worktree and confirm exactly one of each process, each started after that open, and `schema_version` 8.

Rollback: client closed, no Zola openers, restore the database backup and the old plugin mirror together, then start the old code. `schema_version` is 7. Leaving the new code in place would migrate the restored file forward again.

Fallback if schema 8 is refused: `name_source` stays `contacts_ticket`, and both "he was told" and "he said stop" store `closed_intent` `cancelled`, with the real reason only inside `predicate_json`. That hides why the watch closed. A list or a later audit cannot tell a stop from a delivery.
SOUL lines, written only if approved, at deploy: a watch says when to speak up, not who matters; a forget removes what this PC is holding and never deletes texts from the phone. Privacy page: no change.
- Option A (lean): schema 8, this deploy and rollback, those SOUL lines, privacy unchanged.
- Option B: no schema change, accept the hidden close reason, no SOUL lines.
- Consequence: B avoids a migration and makes "delivered" indistinguishable from "cancelled" in the column the rest of the store reads.

**13. Items already waiting when the line plays (Q3).**
The 180-second window is measured from `detected_at`. If he is busy, the anchor may be claimed minutes later. A text from minute 4 is outside that window and would otherwise be claimable immediately after the anchor's line. Two lines back to back is what P10-D15 forbids.
Rule: when an anchor line is delivered, every other item for that person whose `detected_at` is earlier than that delivery joins the burst and is not claimed later. A released claim is not a delivery. Brian started talking, the attempt stays `released`, and the same anchor can be claimed again. Items that arrived before the eventual delivery join that one line. Exactly one line. A text detected after the delivery is a new burst for a standing watch, or unmatched for a one-shot that has closed.
Tests `test_burst_already_waiting_joins` and `test_released_anchor_one_line`.
- Option A (lean): this "already waiting" rule, on top of the 180-second window.
- Option B: keep the strict 180-second window only.
- Consequence: B can speak twice in a row after a long meeting. A can hold a text that arrived many minutes before the line and is a different topic; it still surfaces in conversation.

**14. Group texts and standing-watch gaps (Q4).**
A person watch matches on sender hash, so a group text from that person matches. The item already has `is_group` (`proactive_store.py` line 634). Read-only counts from the live store, local evening defined as 17:00–22:00 (speech is allowed; quiet hours start at 22:00): one sender had 20 texts in one evening, 6 of them group. At a 180-second burst that evening is 4 spoken lines. The same sender across speech hours that day (07:00–22:00) had 60 texts, which is 20 lines at 180 seconds and 10 lines if lines are at least 30 minutes apart. Four senders had an evening of 5 or more. Store-wide: 410 group rows and 685 one-to-one rows, 54 senders, 1,095 phone rows. No identity is recorded here.
Group line, only when `is_group` is 1. No group name. No content. Each opens with an attention word:
- "Brian, quick one: {name} texted in a group thread."
- "Heads up, {name} just texted in a group thread."
- "Quick one: a group text from {name}."
- "Brian, {name} texted in a group thread."

(a) Do group texts match a person watch?
- Option A (lean): yes for a one-shot. A standing watch is created for one-to-one only, and she asks once, on the same confirmation token (`watch_groups`), whether to include group threads. Until he says yes, `is_group=1` does not match that standing watch.
- Option B: groups match both lifetimes with no ask.
- Option C: groups never match.
- Consequence: B on that sender is up to 20 lines in a day of speech hours. C misses a group text he asked to be told about. A asks only when he asked for a standing watch.

(b) Minimum gap between standing lines, beyond the burst rule.
- Option A (lean): `STANDING_MIN_GAP_SECONDS = 1800` from the previous delivered line for that person. The day above drops from 20 lines to 10.
- Option B: no extra gap.
- Consequence: A holds a later text for half an hour; it still surfaces. B is the 20-line day.

**15. Default lifetime for phrasing that is not listed (Q5).**
Bench B5 says "Watch for Bebo Dev." That phrase is not in the one-shot list, the standing list, or "keep an eye on".
- Option A (lean): anything not listed is one-shot, including "watch for". "Keep an eye on" still asks. He can say "every time" when he wants standing.
- Option B: "watch for" asks, the same as "keep an eye on", and other unlisted phrasing is one-shot.
- Option C: any unlisted phrasing asks.
- Consequence: A creates a one-shot on B5's words without a second question. The fuzzy "Bebo" question still happens. B adds a lifetime question on top of the fuzzy question, so B5 has two asks.

**16. How W7 runs (Q10).**
Test seams are module seams. No environment variable, no config key, no production argument. Each is inert until a test sets it.

| Seam | Where | Production |
|---|---|---|
| Phone race | Existing `Engine.fault` (`runtime.py` lines 115, 931). New point `after_predicates`, after the predicate read and before the match write. | `fault` is `None`. |
| Watcher race | `watcher.set_evaluate_fault_for_tests`, between `_matching` and the match write. | Setter never called. Default `None`. |
| Contacts down | `contact_index.set_unavailable_for_tests`, overriding `contacts_unavailable` (`contact_index.py` lines 466–477). | Setter never called. Default leaves `_unavailable` to the real refresh. |

No email-view change in the watcher. The store transaction still refuses a stale match if the watcher fault is refused; the watcher race test then cannot interleave inside the watcher, and that test would be phone-only.
W7's partial sentence is built by the forget handler, not by the model. The cell is CURSOR-RUN: the real handler, Brian-turn fixture, seam set, scratch serve. Brian will not hear it spoken.
- Option A (lean): CURSOR-RUN is enough.
- Option B: Brian also does a live method he controls (for example a firewall block he adds and removes) and listens to the partial reply.
- Consequence: A proves the sentence and does not depend on a network break. B proves he hears it. The seam is still what the tests use either way.

### Files Phase 4 may change, if these verdicts are approved

`loops.py`, `loop_match.py`, `speech.py`, `proactive_store.py`, `contact_index.py` (match quality and the unavailable seam only), `surface.py`, `phone_tools.py` (session read record only), `runtime.py` (evaluation view already has `detected_at`; the new fault point; notification refused), `watcher.py` (test fault only), `zola_memory/forget.py` (the seam), `SpeechPhrases.cs` and the phrase-parity check. Tests in the existing suites. `SOUL.md` only in the approved deploy. No gateway method. No companion change. No contract change. No lore edit.

### Tests added to RD-W13

`test_one_shot_satisfied_mutes_later_matches`, `test_burst_already_waiting_joins`, `test_released_anchor_one_line`, `test_text_as_ordinary_word_is_both`, `test_widen_token_lapses`, `test_widen_token_other_session`, `test_forget_reply_matches_store_state`, `test_notification_short_name_remains`, `test_stop_pronoun_one_path`, `test_group_line_names_no_group`, `test_schema8_scratch_counts`. Standing-gap and group-ask tests are named in Phase 4 from decisions 14 and 15.

### Risks

A one-shot that does not mute its other matches speaks twice about one request. A standing watch on a frequent sender, including group threads, is the 20-line day above. A forget reply that lists kinds he did not have looks complete when it is not. Schema 8 with an old process still running will refuse to open, or the new code will migrate a database the old code then cannot read; the deploy stops every opener first and rolls the database and the mirror back together. Name-only speech and the one-breath delivery are Phase 10 limits, not rules that content or an office-door ask are unwanted. A watch is not a trust list. Tombstones do not cover a new install.

### Residuals carried forward

Live `contracts\phone_test_keys.json` matches the repo fixture, is not loaded at run time, and is not changed in this track. Leftover folder `C:\Users\test\Dev\zola-windows-p10-read` is still not a worktree and was not touched.

## Phase 3 verdicts

Recorded from Brian, 2026-11-04. These lock the proposal. They are not re-opened here.

1. A.
2. A, 2 minutes. The confirmation covers the whole proposed action: person, numbers and emails, channels, lifetime and group inclusion, and a yes does exactly that.
3. A.
4. A.
5. A.
6. A.
7. A.
8. A, with changes: every person forget says notifications are matched by display name only and some may remain, even when none matched; the reply includes the memory facts actually removed alongside texts, email and watches; wording must not suggest past conversations were erased ("the texts I was holding").
9. A, with the watched-text sentence reworded to: "One of these is a text from someone Brian asked you to watch for. His current request comes first; mention it when it fits."
10. A.
11. A. Brian will recreate the test contact with the Google Voice number and an email.
12. A. Schema 8 approved. Both SOUL lines approved. Privacy page unchanged. SOUL is written only at the approved deploy.
13. A, limited to items matched by the same watch or by overlapping watches on the same item. Speaking about one text never closes or mutes an email-reply watch or any other watch.
14. (a) A: until Brian answers the group question, a standing watch covers direct texts only and she says so when she creates it. (b) A, 30 minutes. Texts held by the gap stay pending and join one line when the gap ends, and the same held texts never produce another line.
15. A, only after the code confirms it is a request to watch. "don't watch," "stop watching," and "what are you watching" never create one.
16. A. W7 is reported as tested in code, not live spoken behavior.

## Phase 4 — implementation (4A)

Source is in the worktree. The live database was not migrated. `SOUL.md` was not edited. No plugin mirror was replaced. Part 4B has not started.

Scratch copy of the live store, migrated by the new code, then discarded: schema 7 to 8. Loops 9 = 9. Items 1771 = 1771. Tombstones 1 = 1.

Approved tests added after the first 4A report, through the real entry points. Suites re-run 2026-11-04:

| Suite | Result | Floor |
|---|---|---|
| `zola_workspace` | 573 OK | 505 |
| `zola_memory` | 145 OK | 134 |
| `zola_tools` | 44 OK | 44 |
| `zola_tts` | 8 OK | 8 |
| `zola_phone` | 71 OK (mutex included) | 62 |
| Client Release build | 0 warnings, 0 errors | 0 / 0 |
| `Zola.Client.Checks` | 250 PASS, 0 FAIL. Speech 40/40. Every other row is at its Phase 1 count | those rows |
| Kotlin `testDebugUnitTest` | 98 tests, 0 failures. `assembleDebug` succeeded | 98 |

The checks project still prints the nine existing CA1416 warnings on `LocalCodeVoice.cs`. The client project build is 0 warnings and 0 errors.

The bench is not started. It waits for Brian.

## Phase 4 — deploy (4B), 2026-11-05

Orphan check before any live change: no Zola client, serve, watcher, or zola-phone. A first launch from the temp build folder failed to find the Hermes checkout (`resolve_failed` for watcher and phone, serve `keeps_failing`). That process was the one this step started, and it was stopped. Nothing else was stopped.

Backup, scratch `C:\Users\test\Dev\zola-spikes\p10-watch\part4b-backup\`, taken before the mirror. `proactive.db` via the SQLite backup API: 2,326,528 bytes, SHA-256 `9dc5916a095c6db67410a6332fc2fbc8eb87f10eb90785fb2af98cfdeb6dc626`, schema 7, cutoff `2026-11-03T17:08:23Z`, loops 9, items 1771, tombstones 1. `SOUL.md` SHA-256 `2cff9fa4832ac6fcc1b41096a9b17da9786a3bf0740aebcbcb4c76b03e6d5f5c`. The ten plugin files the mirror replaces are in that folder. `restore.ps1` puts the plugins, `SOUL.md`, and the database back together, then re-applies the recorded cutoff. It refuses to run while a Zola opener is up.

Mirrored those ten files. One open of the live database with the new code: schema 8, cutoff unchanged, loops 9, items 1771, tombstones 1, integrity ok. Then the client was started from the worktree build.

| Role | PID | Parent | Started |
|---|---|---|---|
| client | 9292 | 5820 | 07:10:45 |
| watcher | 46716 / 30244 | 9292 | 07:10:46 |
| zola-phone | 24772 / 22140 | 9292 | 07:10:46 |
| serve | 48264 / 46084 | 9292 | 07:10:46 / 07:10:47 |

One of each. All started after the schema 8 open. Read-back of `schema_version` is 8. Cutoff is still `2026-11-03T17:08:23Z`.

Live `SOUL.md` is 10,458 bytes, SHA-256 `4411118908839cadd131d1723e969176451be8550172b41dcbb4b792ef9ff45b`. Added: "A watch says when to speak up, not who matters." and "A forget removes what this PC is holding and never deletes the texts from the phone." The older line that asks whether to keep watching is still in the file. Privacy page unchanged. `config.yaml` unchanged.

Contact index after deploy: 277 people, available. A lookup for the two-word scripted name had 0 hits. Brian corrected the live contact to the one-word name. Recheck at his go: 277 people, one exact name, 1 number, 1 email, 1 canonical number, 0 shared-number hashes. The one-letter misspelling is fuzzy. The two-word phrases do not match.

### Expected results, written before Brian speaks

| Step | Expected |
|---|---|
| B1 | Say "Let me know when I hear from Bebo." One person watch, channel both, lifetime once. Her words: "I'll let you know when Bebo texts or emails. I'll use the numbers and email addresses saved for them right now." |
| B2 | One text. One spoken line, name only, a text phrasing. Speech log: one claim, a phrase index, `name_source` contacts_index. The one-shot closes delivered. |
| B3 | A fresh watch if B2 closed the first. Three texts inside the window. One spoken line. Speech log: one claim, the others coalesced. |
| B4 | "What did they say?" reads that person's texts from the phone. He does not have to say the name. |
| B5 | "Watch for Beebo." She asks "Did you mean Bebo?" If he does not confirm, nothing is created. "I don't have a Beebo contact. What number should I watch?" is an accepted reply. |
| B6 | "Forget Bebo." Then the confirmation if she asks. The reply names what was actually removed, says notifications are matched by display name only and some may remain, and says the texts are still on the phone. Counts only: phone and email rows gone or redacted, watches closed forgotten, tombstones written, sender hint cleared. The Google contact stays. |
| B7 | On a backup-API copy, not the live file: a replay of the forgotten identity is suppressed. One new text is stored and can surface. |
| B8 | Grep of the PC logs and the phone log for the scripted bodies, the test contact's name, and the number: 0 hits. |

W5 (a number that is not in Contacts) runs before W6. Quiet hours stay a unit and check result. The live smoke is daytime.

### B1 result (2026-11-05)

Brian said he would let her know when he hears from the one-word contact. One new loop. Open loops: 1. Intent person, `name_source` contacts_index, channel both, lifetime once, two address hashes, display-name length 4. Loop rows 10, was 9.

The tool `say` is both sentences, including "I'll use the numbers and email addresses saved for them right now." The assistant message stored in `state.db` is only "I’ll let you know when Bebo texts or emails." The freeze sentence was not what Brian heard. The watch itself matches. B2 uses this watch.

### B2 result (2026-11-05)

Brian heard "Brian, quick one: Bebo texted you." That is text phrase index 0. Speech log: one `outcome=delivered` claim for this track, `phrase=0`, `name_source=contacts_index`, attempt `22a03017e6c5fda3`. One sms at `2026-11-05T15:26:57Z` is `loop_matched` 1 and `delivery` delivered. The person watch is closed, `closed_intent` delivered. Open loops: 0.

### B3 result (2026-11-05)

Brian heard "Heads up. Bebo just texted." That is text phrase index 1. A second person watch was created and is closed `delivered`. Speech log adds one claim, attempt `3ab309fd03447aec`, `phrase=1`, `name_source=contacts_index`. Three sms at `15:33:09Z`, `15:33:11Z`, and `15:33:12Z` are `loop_matched` 1. The first is `delivery` delivered. The other two are `delivery` none. Open loops: 0.

### B4 result (2026-11-05)

Brian asked what they said, 16 characters, without the name. `phone_read_texts` returned the scripted body three times and the earlier body once. Her reply named the three. She also asked whether to keep watching. Open loops stayed 0. Items 1833. Tombstones 1.

### B5 (2026-11-05) — accepted, then a deviation

"Watch for Beebo" called `zola_loops`. She asked "Did you mean Bebo?" "No." did not call the tool. She said "What number should I watch for Beebo?" and, on the repeat, "I don't have a Beebo contact. What number should I watch?" Brian accepted that wording. The pass is that nothing is created. Open loops stayed 0. Loop rows stayed 11.

Deviation, mid-bench. The tool description was given "When the tool returns say, that is your whole reply, every sentence." and the client was restarted on that text. Brian rejected that requirement. That sentence is reverted. The description still says a yes or a no after the name question is another call to this tool. An open confirmation now lapses at the next turn unless that turn's words are the answer and its tool call consumes it. A later yes creates nothing. Test `test_unrelated_turn_drops_an_open_confirmation`.

Mirrored after the suites. `loops.py` 35,077 bytes, SHA-256 `688e5d52368bb0f391649c9cc46f9c1d36b4637efa8c444a7fe61c82c7071785`. `turn_context.py` 9,100 bytes, SHA-256 `6d83e2fb1b1108a1a7cbc4b03e7bbe33992eedba6e582681325c374d1a206d67`. The pre-change `turn_context.py` is in the backup, and `restore.ps1` puts it back with the other files.

Suites after the fix: workspace 576 OK, memory 145 OK, tools 44 OK, tts 8 OK, phone 71 OK, client Release 0 warnings 0 errors, checks exit 0 with speech 40/40 and every coverage row at its floor, Kotlin 98 tests 0 failures, `assembleDebug` succeeded.

Client restarted for the B5 repeat: client 31404, watcher 10480, phone 34396, serve 12084, started 07:58:51.

### B5 repeat (2026-11-05)

The stored transcript is the 15-character line "Watch for Beebo". `zola_loops` was not called. `contacts_lookup` was not called. The tools on that turn were `skill_view` and `tool_describe`. Open loops stayed 0. She asked for a number without a watch-tool result. The "Did you mean" question is only returned by `zola_loops`.

The earlier "I don't have a Beebo contact" turn did call `contacts_lookup`: ok, state `no_match`, 0 contacts. That tool is the search API, not the fuzzy index. The index was not asked on the repeat, so it did not miss.

### W5 (2026-11-05) — failed, bench fix, suites, then a repeat

Brian spoke a 10-digit number. The stored request is 47 characters, one digit run of 10, and the watch tool classifies those words as channel both. Four `zola_loops` calls, all refused, in order: `channel_disagrees`, `number_not_in_message`, `channel_disagrees`, `name_not_in_message`. The tool `say` was empty and had no digits. Open loops stayed 0. Loop rows stayed 11. No number-intent row.

She repeated those same 10 digits and said the text watcher was not recognizing the number. The watcher did not refuse. The watch tool did.

Bench fix. A number watch is text, so passing channel text on a both-phrase is no longer `channel_disagrees`. A spoken 10-digit number normalizes to the +1 form, and that national number now counts as the number in the transcript. Test `test_ten_digit_number_is_the_spoken_number` failed on the old path, then passed.

The spoken number was not the contact's number. Its hash is not the sender hash of the four matched bench texts (one distinct hash, the number the person watch was compiled from). A number that does belong to one contact is still stored as a number watch first. The reply names that person and asks, and the person watch is created only on a later yes. Tests `test_number_watch_on_a_contact_does_not_widen` and `test_widen_only_after_yes`.

Mirrored `loops.py`, 35,491 bytes, SHA-256 `cb53f815007cda79a5fac2e0ce06de3a1c748cc11037d32501b3acb17ab9313d`. A client on that file was started at 08:24:04 (client 20300), then stopped so the phone suite could take the mutex. Full suites after the fix, client closed: workspace 577 OK (107.8s), memory 145 OK, tools 44 OK, tts 8 OK, phone 71 OK, client Release 0 warnings 0 errors, checks exit 0 with 250 PASS and 0 FAIL, coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` ran (not up to date): CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded in the same run.

Client restarted on the same mirrored file: client 14200, watcher 38484, phone 23272, serve 45304, started 08:39:47. One of each. Live index before the repeat: 277 people, available, one exact name, 0 numbers, 1 email, 0 canonical numbers. W5 waits on him saying the Google Voice number. Pass: one number watch, channel text; the reply has no digits and no name; a text from that number speaks the number line; nothing is matched to the contact.

### W5 create (2026-11-05)

He said the number in words first. That message has no digit characters. The assistant message after it is 41 characters and contains those 10 digits. The next request, "Let me know when I get a text from that number.", has no digits. `zola_loops` refused it `number_not_in_message`. She asked him to send the digits. He did: 48 characters, one run of 10. That hash is the sender hash of the four matched bench texts.

`zola_loops` returned ok, intent number, channel text. The tool `say` is the approved sentence, 65 characters, no digits, no name. The stored reply is the first sentence only: "I'll let you know when that number texts." One open loop. Intent number, channel text, lifetime once, `name_source` mail, display "a number", one hash, and that hash is the number he just said. No person handle. Open person watches: 0. Loop rows 12. The text from that number is still outstanding.

### W5 text (2026-11-05)

Brian heard "Brian, that number you asked me to watch just texted." That is number phrase index 0. Speech log: one `outcome=delivered` claim, attempt `ef31dd92bb9ba486`, `phrase=0`, `name_source=someone`. The log uses `someone` when the spoken name is empty. A number watch is `name_source` mail, and that source is not spoken as a name.

One sms at `2026-11-05T16:51:47Z`, `loop_matched` 1, `delivery` delivered, sender hash equal to the watch hash, not a group, sender display length 0. The number watch is closed `delivered`. Open loops 0. Open person watches 0. Nothing else has matched since the watch was created. The spoken line has no digits and no name.

### Number restored (2026-11-05)

Brian put the number back. The first People fetch still showed 0 numbers and 1 email. The next fetch, and a repeat of the index path, showed one exact name, 1 number, 1 email, 1 canonical number, 0 shared. That number's hash is the bench sender hash.

The client that had been up since 08:39 still held the earlier list. A name hit does not reload it, so a forget in that process would have seen 0 numbers. That client was stopped and started again: client 6744, watcher 40416, phone 17152, serve 3328, started 09:06:38. One of each. B6 waits on "Forget Bebo."

### B6 first try (2026-11-05)

The stored request is "Forget Bebo." `forget_memory` returned ok, `confirm` false, 3 groups, all `ask_brian`: two episodes and one entity. No contact candidate. `zola_loops` was a list. She opened a clarify card and then asked for a clear choice. Nothing was erased. Forgotten loops 0. Tombstones 1. Open loops 0.

The texts from that number are not on the entity. 65 sms share its sender hash, 0 have the name in subject, snippet, or gist, and 0 have an entity id. Gmail rows whose sender hash is the contact's email: 0. Confirming the entity would not remove those texts. The card is not the B6 erase. Brian skipped it. Nothing was erased.

### B6 bench fix (2026-11-05)

Confirming a memory entity now also takes the contact's number and email hashes when that name is one contact. Test `test_entity_forget_includes_the_contact_number` failed first (the reply was "I wasn't holding anything"), then passed. The reply names the texts and says they are still on the phone.

Suites, client stopped: workspace 577 OK, memory 146 OK, tools 44 OK, tts 8 OK, phone 71 OK, client Release 0 warnings 0 errors, checks 250 PASS and 0 FAIL, speech 40/40 and every coverage row at its floor. Kotlin `testDebugUnitTest` ran: 15, 39, 30, 14, 0 failures. `assembleDebug` succeeded.

Mirrored `forget.py`, 77,095 bytes, SHA-256 `2b4aafbf10641cb1eb50d9d9fbc5f93c627dc441a2b2608e4db992ead5a175b7`. `contact_index.py`, 22,855 bytes, SHA-256 `10e7a5aaba694266205a0b89dc86d203eed0b6e5524305da4c1748d7b435856c`. Client restarted: client 8324, watcher 40616, phone 3684, serve 43420, started 09:23:49. One of each. B6 waits on "Forget Bebo" again.

### B6 second try (2026-11-05)

He said yes to removing all three references. `forget_memory` confirm true erased 2 episodes and 1 entity. The tool message was the memory-only sentence, including "conversation logs still have it," and said the pending list was not changed. She said Bebo is gone from her memory and the old chat history still contains it.

The entity is gone: 0 entities named Bebo. The texts are not. 65 items still have that sender hash, 28 of them still have a sender hint. Tombstones 1. Forgotten loops 0. The Google contact is still one exact name, 1 number, 1 email.

The yes did not reach the contact hashes. The episode erase deletes an entity that no longer has episodes before the proactive step, and the confirm description was "Yes", which does not match the entity name. B6 is not done.

### B6 bench deviation (2026-11-05)

One yes authorizes the memory erase and the phone and email forget together. The contact's numbers and emails are resolved when the candidates are listed, and that plan is stored on the confirmation. The yes uses the stored plan. It does not search the confirm word for the name.

If the phone step fails after the memory erase, the reply says the memory was removed and the texts, email, and watches were not. A person who is in Contacts does not get the memory-only line.

A delivered or acknowledged watch for that person is retagged forgotten. A cancelled watch keeps its close reason.

`test_yes_forgets_memory_and_the_bound_contact` and `test_yes_reports_a_partial_when_proactive_fails` failed on the old path, then passed.

Suites, client stopped: workspace 577 OK (99.9s), memory 148 OK, tools 44 OK, tts 8 OK, phone 71 OK, client Release 0 warnings 0 errors, checks 250 PASS and 0 FAIL, speech 40/40 and every coverage row at its floor. Kotlin `testDebugUnitTest` ran: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded.

Mirrored `forget.py`, 84,742 bytes, SHA-256 `d627e8fcc3f1a8d2221675ec8e556be05fe0e99de99e9921ffb1915e548f3011`. `proactive_store.py`, 167,073 bytes, SHA-256 `84642cbb29e0c794cf69f95734cb870bbfc4ac88d950d8431b148d73c2cb89a1`. Client restarted: client 10280, watcher 23272, phone 46532, serve 34424, started 09:51:31. One of each. No `resolve_failed`.

B6 waits. He first tells her one harmless fact so a memory record exists, then says "Forget Bebo" and yes.

### B6 third try (2026-11-05)

He said "Forget Bebo." The memory tool removed one notebook fact whose text contained the name. `forget_memory` was then confirm false. Its description was four words and did contain the name. The tool returned no matches and said the pending list was not changed. She said Bebo is gone from her memory and that it remains in the old chat history. There was no confirm true.

Entities named Bebo: 0. One older episode still matches the name. Items with the bench sender hash: 66, and 29 of those still have a sender hint. Tombstones 1. Forgotten loops 0. The number watch is still closed delivered. The Google contact is still one exact name, 1 number, 1 email. B6 did not pass.

### STOP for review (2026-11-05)

Brian stopped the bench. The live mirror stays as deployed at 09:51. No further patch. The review report is the reply in that session. The yes-attempt tool description was one word and did contain the name. The miss was the cascade deleting the entity before the contact step, not a description that lacked the name.

### Review answers, not approved (2026-11-05)

The contact confirm returned ok false in 5ms. The store error is `origin`, from `_forget_subject` calling `_ticket_ok()` with no turn id. No row changed. The handler replaced that error with the pending-list sentence. The contact-index log has no timestamps. A call is resolved from the tool description only. The one-word misspelling found the contact by a fuzzy token match. The four-word description that contained the name found nothing because the index was cold at the phrase scan, and the matcher used after the refresh does not see a name inside a longer description. The plan is in the session reply. No code. Live mirror unchanged.

The approval that followed this section, before the change below, is Brian's, verbatim: "Approved, with these conditions: Before fixing _ticket_ok, find which branch of is_brian_turn returned false: empty turn id, no turn record, platform, or parent session. Give each silent branch a reason-code log line, and make the forget tool return the store’s refusal reason instead of dropping it. Write a failing test that reproduces the real cause, then fix that cause. If passing the turn id is the fix, say why the ContextVar was empty there. Preflight before any erase: the store ticket is valid and the contact index is resolved (or confirmed unavailable). Then run the proactive step, then memory and notebook facts. A failure leaves everything as it was, or the reply says exactly which stores changed. Add a test where the ticket is refused at preflight → nothing is erased. Contacts unavailable follows locked P10-D14: forget what can be matched (memory entity, notebook facts, stored watches’ hashes, entity-linked items) and say it may be incomplete. Don’t remove nothing. Wait for a cold index with a bound, like Track 5’s 2 seconds, and say what happens at the bound. Show how forget removes USER.md/MEMORY.md facts through a supported Hermes path, not by editing the files directly. If there isn’t one, STOP and tell me. Then implement with your listed tests plus these. Run full suites, record everything as bench deviations, redeploy with file hashes, and rerun B6 as planned."

### B6 bench deviation (2026-11-05)

One yes authorizes the memory erase and the phone and email forget together. The contact's numbers and emails are resolved when the candidates are listed, and that plan is stored on the confirmation. The yes uses the stored plan. It does not search the confirm word for the name.

If the phone step fails after the memory erase, the reply says the memory was removed and the texts, email, and watches were not. A person who is in Contacts does not get the memory-only line.

A delivered or acknowledged watch for that person is retagged forgotten. A cancelled watch keeps its close reason.

`test_yes_forgets_memory_and_the_bound_contact` and `test_yes_reports_a_partial_when_proactive_fails` failed on the old path, then passed.

Suites, client stopped: workspace 577 OK (99.9s), memory 148 OK, tools 44 OK, tts 8 OK, phone 71 OK, client Release 0 warnings 0 errors, checks 250 PASS and 0 FAIL, speech 40/40 and every coverage row at its floor. Kotlin `testDebugUnitTest` ran: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded.

Mirrored `forget.py`, 84,742 bytes, SHA-256 `d627e8fcc3f1a8d2221675ec8e556be05fe0e99de99e9921ffb1915e548f3011`. `proactive_store.py`, 167,073 bytes, SHA-256 `84642cbb29e0c794cf69f95734cb870bbfc4ac88d950d8431b148d73c2cb89a1`. Client restarted: client 10280, watcher 23272, phone 46532, serve 34424, started 09:51:31. One of each. No `resolve_failed`.

B6 waits. He first tells her one harmless fact so a memory record exists, then says "Forget Bebo" and yes.

### B6 third try (2026-11-05)

He said "Forget Bebo." The memory tool removed one notebook fact whose text contained the name. `forget_memory` was then confirm false. Its description was four words and did contain the name. The tool returned no matches and said the pending list was not changed. She said Bebo is gone from her memory and that it remains in the old chat history. There was no confirm true.

Entities named Bebo: 0. One older episode still matches the name. Items with the bench sender hash: 66, and 29 of those still have a sender hint. Tombstones 1. Forgotten loops 0. The number watch is still closed delivered. The Google contact is still one exact name, 1 number, 1 email. B6 did not pass.

### STOP for review (2026-11-05)

Brian stopped the bench. The live mirror stays as deployed at 09:51. No further patch. The review report is the reply in that session. The yes-attempt tool description was one word and did contain the name. The miss was the cascade deleting the entity before the contact step, not a description that lacked the name.

### Review answers, not approved (2026-11-05)

The contact confirm returned ok false in 5ms. The store error is `origin`, from `_forget_subject` calling `_ticket_ok()` with no turn id. No row changed. The handler replaced that error with the pending-list sentence. The contact-index log has no timestamps. A call is resolved from the tool description only. The one-word misspelling found the contact by a fuzzy token match. The four-word description that contained the name found nothing because the index was cold at the phrase scan, and the matcher used after the refresh does not see a name inside a longer description. The plan is in the session reply. No code. Live mirror unchanged.

The approval that followed this section, before the change below, is Brian's, verbatim: "Approved, with these conditions: Before fixing _ticket_ok, find which branch of is_brian_turn returned false: empty turn id, no turn record, platform, or parent session. Give each silent branch a reason-code log line, and make the forget tool return the store's refusal reason instead of dropping it. Write a failing test that reproduces the real cause, then fix that cause. If passing the turn id is the fix, say why the ContextVar was empty there. Preflight before any erase: the store ticket is valid and the contact index is resolved (or confirmed unavailable). Then run the proactive step, then memory and notebook facts. A failure leaves everything as it was, or the reply says exactly which stores changed. Add a test where the ticket is refused at preflight → nothing is erased. Contacts unavailable follows locked P10-D14: forget what can be matched (memory entity, notebook facts, stored watches' hashes, entity-linked items) and say it may be incomplete. Don't remove nothing. Wait for a cold index with a bound, like Track 5's 2 seconds, and say what happens at the bound. Show how forget removes USER.md/MEMORY.md facts through a supported Hermes path, not by editing the files directly. If there isn't one, STOP and tell me. Then implement with your listed tests plus these. Run full suites, record everything as bench deviations, redeploy with file hashes, and rerun B6 as planned."

### B6 bench deviation (2026-11-05)

The silent branch on that contact confirm is `empty_turn_id`. `is_brian_turn()` with no argument reads the tool ContextVar. `forget_memory` is a memory-provider tool. Its dispatch is `memory_manager.handle_tool_call`. The only place that sets `_approval_turn_id` is `model_tools._approval_observability`, and a memory-provider tool never enters it, so the ContextVar stays empty. `pre_tool_call` still runs. It receives `agent._current_turn_id` from `tool_hook_ids` and mints the origin token with that id. The store then called `is_brian_turn()` with no argument and took the empty-id branch. Each silent branch now logs `brian_turn reason=` with one of `empty_turn_id`, `no_turn_record`, `platform`, or `parent_session`. The tool returns that store reason. On consume, the token's turn id is kept on the provider and passed into `ticket_reason` and `forget_subject`.

Before any erase, the store ticket has to be valid and the contact plan has to be exact, token, fuzzy, or confirmed unavailable. The proactive step runs next. Memory episodes, the named entity, and notebook facts run after it returns ok. A ticket refusal or a proactive failure before commit leaves every store as it was and the reply is "I didn't change anything." If the phone step has already committed and memory then fails, the reply says the texts, email, and watches were removed and the memory was not.

One person candidate covers that contact's numbers and emails, the matching memory entity, the episodes, and the USER.md/MEMORY.md facts that name the person. The same yes removes those notebook facts through Hermes `memory_tool` `action=remove` (`MemoryStore.remove`, which locks, rereads, and writes). After a committed remove, the plugin calls `on_memory_write`, the same mirror Hermes uses. The files are not edited directly. `pre_tool_call` blocks a model `memory` remove or replace on a person-forget turn.

Contacts unavailable follows P10-D14. The forget removes what it can already match: a memory entity whose name matches, notebook facts that name the person, stored watches whose display name matches (hashes and display name cleared, closed forgotten), and items linked to that entity. The reply says the forget may be incomplete. If there is no such entity and no such watch, the old episode and notebook candidates stay as they were.

A cold index waits in `contact_plan_waiting` through `refresh_bounded`, bound 2.0 seconds, the same bound as Track 5. At the bound, with still no index, this turn's plan is unavailable with bound `timeout`. The reply says Contacts could not be checked within 2 seconds, so this may be incomplete. The background fetch may still finish after the bound. This turn does not use that later result. A fetch that fails marks contacts unavailable, so a later forget in the same process returns immediately and the sentence leaves out "within 2 seconds".

`test_yes_reports_a_partial_when_proactive_fails` refuses the ticket at preflight and leaves the episode, the entity, the text, the email, and the open watch in place. `test_empty_context_var_still_forgets_when_the_turn_id_is_passed` shows `is_brian_turn()` false and `is_brian_turn` of the token's id true, then the yes erases the text. `test_brian_turn_branches_log_a_reason`, `test_description_without_the_name_uses_his_message`, `test_cold_index_waits_then_returns_one_person`, `test_index_bound_forgets_what_it_can_and_says_so`, and `test_memory_remove_is_blocked_and_the_yes_sweeps_the_note` cover the reason codes, the message name, the 2 second wait, the incomplete forget, and the notebook path.

The first workspace invocation ran 511 tests and failed to import `test_p8_read` and `test_p8_send` because the tests directory was not on the path. The same suite with that directory on the path: 577 OK (99.715s). Memory 154 OK (17.409s). Tools 44 OK. TTS 8 OK. Phone 71 OK (59.616s), client stopped. Client Release 0 warnings, 0 errors. Checks exit 0, 250 PASS, 0 FAIL. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded in the same run. The Kotlin deprecation warnings are the ones already on those files.

Mirrored `forget.py`, 100,523 bytes, SHA-256 `89f96a41c230cd9542bbd95bb67f66cd073d270a76500dbcf57b75f74a705044`. `proactive_store.py`, 168,944 bytes, SHA-256 `5940bb20f335a4677b08765323b9131664ae81bf92d4d081dc9a0760bada8bd0`. `turn_context.py`, 9,895 bytes, SHA-256 `2801031296eb7b7fc072036fdb8ec5c35477eab759bf94bd31e63e545ae87f51`. Live copies match. Client restarted: client 19932, watcher 25092, phone 30688, serve 39300, started 10:44:03. One of each. No `resolve_failed`. The database was not restored.

B6 waits. He first tells her one harmless fact so a memory record exists, then says "Forget Bebo" and yes. Pass: the memory record is gone; the stored texts are gone or redacted with the last-4 cleared; tombstones are written; the number watch is closed forgotten; the reply says the texts are still on the phone and that notifications are matched by display name only; the Google contact is still there.

### B6 fourth try (2026-11-05)

He gave one fact, then said "Forget Bebo." The first listing was confirm false, 4 groups, all `ask_brian`: three pending turns and one person. A second "Forget Bebo" returned the same four. She asked whether to forget everything she was holding about him. He said yes. `forget_memory` confirm true, ok, 47ms, erased those four. The cascade removed 3 pending rows and 0 episodes. A following memory-tool remove took 1 fact. The tool message named the texts, the watches, and the notes, said notifications are matched by display name only, and said the texts are still on the phone. It did not say chat history.

She said: "Done — Bebo is gone from my memory, though it’s still in our old chat history." That is 78 characters. It does not name the texts, the phone, or the notification limit.

When she asked him to confirm, she said: "Do you want me to forget everything I’m holding about Bebo?" She did not read four choices. The tool had returned four groups and told her they were different things. She asked one question.

After the yes: entities whose name is Bebo, 0. Facts and episodes that name him, 0. `USER.md` and `MEMORY.md` do not contain the name. Items whose sender hash is his number or his email, 0. Tombstones 67. The number watch is closed `forgotten`, display length empty, hash count 0. Both person watches are closed `forgotten` the same way. Open loops 0. The Google contact is still one exact name, 1 number, 1 email.

Brian's ruling: the stores are a pass for B6. The spoken line is not a bench rerun. It is one open item for W6 in the smoke. Her reply has to convey, in her own words, that the texts are still on the phone and that notifications are matched by display name only, so some may remain.

### One person, and must_tell (2026-11-05)

Pending turns that name the person fold into the one person candidate. One person is one group and one question. A confirm of that candidate deletes those pending turns with the rest.

The phone limit and the notification limit are no longer sentences inside the tool message. The confirm result carries `must_tell`: `notifications_display_name`, and `texts_on_phone` when he has a number. The tool description says to convey each fact in her own words and not to recite a set sentence. `test_one_person_folds_the_pending_turns_that_name_them` covers the single group.

Suites, client stopped: workspace 577 OK (110.5s), memory 155 OK, tools 44 OK, tts 8 OK, phone 71 OK, client Release 0 warnings and 0 errors, checks 250 PASS and 0 FAIL, coverage at the same floors. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures. `assembleDebug` succeeded.

Mirrored `forget.py`, 101,516 bytes, SHA-256 `5778ac28eae65cd60bc716f257fb969311bb9abce9519c6e5e757dbd0e3ee7c8`. `proactive_store.py`, 169,185 bytes, SHA-256 `d6b988fb404708d0ee4d97d272e06535a93e207217893746c980f4f235785a19`. Live copies match. Client restarted: client 29640, watcher 41968, phone 48916, serve 7568, started 12:22:39. One of each.

### B7 (2026-11-05)

Backup-API copy of the live store, then the copy only. Live before and after: tombstones 67, items 1790, forgotten 4. The scratch directory was deleted.

The 4 forgotten rows are gmail. They have a message id and no device. No forgotten sms, mms, or rcs row remains, so the phone identity string is not in the copy. The 66 phone tombstones are hashes. The replay of that forgotten identity was not run.

A new text from the contact's number, new provider id, result `stored`. `content_state` available, eligibility eligible, delivery none, `loop_matched` 0. `claim_next_speech` returned `nothing_speakable`. No watch is open. The Google contact was still one exact name, 1 number.

Brian accepted the new-text half. The replay half moves to W6 smoke. It is not a bench rerun.

### W6 replay procedure (not run)

The B6 forget already deleted the phone rows. A tombstone keeps the hash, not the device id, kind, or provider id, so the identity cannot be rebuilt after the forget.

On the smoke, before the forget, capture one of that person's stored phone identities (device id, kind, provider id) in the scratch folder only. Do not log it and do not commit it. After the forget, replay that identity through the real `zola-phone` ingest against a backup-API copy of the store. Pass is `suppressed`, with nothing stored. Delete the scratch capture and the copy. Record counts only.

The other W6 smoke item is unchanged: her reply has to convey, in her own words, that the texts are still on the phone and that notifications are matched by display name only, so some may remain.

### B8 (2026-11-05)

Needles: the bench markers `ZP10-W`, `ZP10-W1`, `ZP10-W3`, and `ZP10-W7`; the contact name; the misspoken form; the contact's number. Counts only.

33 PC log files: the zola profile logs (including `agent.log` and `agent.log.1`, `errors.log`, `gui.log`, `zola_memory.log`, `zola_phone.log` and three rotations, `zola_tools.log`, `zola_watcher.log` and its rotation and out log, `zola_workspace.log`, the run reports, and the lock files) and the parent Hermes logs.

Scripted markers: 0 in every file.

The name: 26, all in the profile `agent.log`, all `agent.turn_context` conversation-turn lines. One of those is today's bench session. The other 25 are older sessions. The misspoken form: 3, same file, same line type, older sessions.

The number: 1 line, profile `agent.log`, a conversation-turn line, an 11-digit run, an older session. Every other PC log, including `zola_phone.log` and its three rotations, is 0 for the name, the misspoken form, and the number.

The handset was not in `adb devices`, so the on-device log buffer was not read.

The written cell expects 0 hits. The markers and the phone-process log meet that. The name and the number in `agent.log` do not.

### Phase 4 STOP (2026-11-05)

| Step | Result |
|---|---|
| B1 | Pass. One person watch, both channels, two address hashes, display length 4. She said she would say when Bebo texts or emails. The tool result also carried the freeze sentence; the stored assistant message did not. |
| B2 | Pass. Text phrase index 0. One delivered claim. The person watch closed delivered. Open loops 0. |
| B3 | Pass. Text phrase index 1. Three texts, one claim, two left at delivery none. Open loops 0. |
| B4 | Pass. A live phone read, without him naming the person. She named the three and asked whether to keep watching. Open loops stayed 0. |
| B5 first | Accepted. "Watch for Beebo" asked whether he meant Bebo, then asked what number to watch. Nothing created. Open loops 0. |
| B5 rerun | Pass. The stored line is "Watch for Beebo". `zola_loops` was not called. `contacts_lookup` was not called. Nothing created. |
| W5 first | Fail. The spoken line repeated a number. Fixed on the bench, then the suites, then a rerun. |
| W5 rerun | Pass. The number was off the contact, a number watch was created, the unnamed line was spoken, and the number was put back. The contact is one exact name, 1 number, 1 email. |
| B6 first three | Fail. The first yes erased memory and cited chat history. The next reply cited chat history again. The cold-index try returned no candidates. |
| B6 fourth, data | Pass. One question, not four choices. The yes erased three pending turns and the person candidate, removed one notebook fact, closed the watches forgotten, cleared the hashes and the display name, and wrote the phone tombstones. Entities, facts, and the two memory files do not contain the name. Items for his number or email: 0. The Google contact is still there. |
| B6 reply | Open for W6 smoke, not a bench rerun. She said Bebo is gone from her memory and still in the old chat history. That line does not carry the two must-tell facts. |
| B7 new text | Pass. A new text stored on the backup-API copy. Eligibility eligible, delivery none, `loop_matched` 0, `nothing_speakable`. The live file was not edited by that harness. |
| B7 replay | Moved to W6 smoke. The identity was already gone. |
| B8 | Recorded above. Markers 0. Name 26 and number 1, both in `agent.log`. Phone-process log 0. The handset was not attached. |

Bench deviations, with the file hash at the time that deviation was mirrored:

| Deviation | Files |
|---|---|
| B5. The tool description was given a whole-reply sentence. Brian rejected it. That sentence was reverted. An open confirmation lapses unless the next turn answers it. | `loops.py` 35,077 bytes, `688e5d52368bb0f391649c9cc46f9c1d36b4637efa8c444a7fe61c82c7071785`. `turn_context.py` 9,100 bytes, `6d83e2fb1b1108a1a7cbc4b03e7bbe33992eedba6e582681325c374d1a206d67`. |
| W5. A spoken number matched the contact's number and was treated as unnamed. | `loops.py` 35,491 bytes, `cb53f815007cda79a5fac2e0ce06de3a1c748cc11037d32501b3acb17ab9313d`. This is still the live file. |
| B6. The cascade deleted the entity before the contact step, so the contact confirm found nothing. | `forget.py` 77,095 bytes, `2b4aafbf10641cb1eb50d9d9fbc5f93c627dc441a2b2608e4db992ead5a175b7`. `contact_index.py` 22,855 bytes, `10e7a5aaba694266205a0b89dc86d203eed0b6e5524305da4c1748d7b435856c`. The contact-index file is still the live one. |
| B6. The yes path. Ticket and a resolved contact plan before any erase, then proactive, then memory and the notebook. A refused ticket erases nothing. | `forget.py` 84,742 bytes, `d627e8fcc3f1a8d2221675ec8e556be05fe0e99de99e9921ffb1915e548f3011`. `proactive_store.py` 167,073 bytes, `84642cbb29e0c794cf69f95734cb870bbfc4ac88d950d8431b148d73c2cb89a1`. Both were replaced by later mirrors. |
| The contact confirm failed `empty_turn_id` because a memory-provider tool never enters the registry path that sets the turn ContextVar. The token's turn id is now passed through. | `forget.py` 100,523 bytes, `89f96a41c230cd9542bbd95bb67f66cd073d270a76500dbcf57b75f74a705044`. `proactive_store.py` 168,944 bytes, `5940bb20f335a4677b08765323b9131664ae81bf92d4d081dc9a0760bada8bd0`. `turn_context.py` 9,895 bytes, `2801031296eb7b7fc072036fdb8ec5c35477eab759bf94bd31e63e545ae87f51`. `turn_context.py` is still the live file. |
| One person candidate, including the pending turns that name them, and `must_tell` instead of a scripted sentence. | `forget.py` 101,516 bytes, `5778ac28eae65cd60bc716f257fb969311bb9abce9519c6e5e757dbd0e3ee7c8`. `proactive_store.py` 169,185 bytes, `d6b988fb404708d0ee4d97d272e06535a93e207217893746c980f4f235785a19`. These two are the live files. |
| Runner. The first workspace invocation ran 511 tests and failed to import `test_p8_read` and `test_p8_send`. The same suite with the tests directory on the path ran 577. | No product file. |

Latest suites, after the must_tell mirror, client stopped: workspace 577 OK (110.5s), memory 155 OK, tools 44 OK, tts 8 OK, phone 71 OK (52.9s). Client Release 0 warnings, 0 errors. Checks exit 0, 250 PASS, 0 FAIL. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded.

Live, checked with the client still up. Client 29640, parent 40148. Watcher 41968, child 21144. Phone 48916, child 42960. Serve 7568, child 36652. Started 12:22:39. One of each. Schema 8. Tombstones 67. Items 1814 (1790 at the B7 check; the harness did not write the live file). Content state forgotten: 4, all gmail. Sources: calendar 48, gmail 629, mms 1001, notif 46, sms 90. Open loops 0. Loops closed forgotten: 3. The Google contact is still one exact name, 1 number, 1 email, unavailable false. Entities whose name is the contact: 0. Aliases: 0. Facts that name him: 0 of 20. Pending turns: 0. `USER.md` 2232 characters, name absent. `MEMORY.md` 308 characters, name absent. Episodes that name him: 1 of 41, recorded 2026-11-03, 43 characters, not today's bench session. The B6 count written after the yes was 0. Memory tombstones 41.

The worktree copies of `forget.py`, `proactive_store.py`, `turn_context.py`, `loops.py`, and `contact_index.py` match the live mirror.

Read-only check. The memory provider's only tool is `forget_memory`. `handle_tool_call` refuses any other name. Both production `is_brian_turn` calls pass the token's turn id, and the confirm path passes that id into `ticket_reason`. No other memory-provider tool calls `is_brian_turn`.

The built-in `memory` tool is not a memory-provider tool. It runs in the inline executor and does not call `is_brian_turn`. On a person-forget turn the pre-tool hook blocks its remove and replace.

`loops.create_loop`, `list_loops`, and `close_listed` call `is_brian_turn()` with no argument. `proactive_store` `_close_item`, `_insert_loop`, `_close_loop`, and `_replace_loop_predicate` call `_ticket_ok()` with no argument. Those are registry tools. Their dispatch sets the turn ContextVar before the handler, which is the path `forget_memory` never enters. B1 created a watch through `zola_loops` on a live turn. They do not fail the way the forget confirm did.

At this stop, Phase 5 had not started. Nothing was committed. The database was not restored.

To continue: "proceed to phase 5"

## Phase 5 (2026-11-05)

Brian's fixes, applied before the smoke. No live plugin file changed, so nothing was mirrored. The client was stopped for the phone suite and started again on the same Release build.

### B8 is a Hermes log, not a Track 6 leak

The 26 name hits and the 1 number hit are `agent.log` lines from Hermes `agent/turn_context.py`. The line is `conversation turn:` and it includes his own message, truncated for the log. No Zola plugin writes that line. The only plugin occurrence of the words "conversation turn" is the consolidator's instruction text, which is not a log call. This is pre-existing. It goes on the lore-closeout residual list. It is not a Track 6 leak.

The phone-log grep moves to the smoke, with USB attached. The Phase 4 pass over `zola_phone.log` and its rotations stays 0. The handset buffer was not read then.

### The 2026-11-03 episode

The one episode whose summary matches the letter sequence is not the exact contact name. The name in it is one token, the letters of Bebo followed immediately by Dev, with no space. It is not the one-word contact name, and it is not the two-word form. The forget did not miss an exact Bebo episode. No test and no fix.

### Notebook sweep

The sweep removes a whole USER.md or MEMORY.md fact when that fact names the person, even if the same fact names other people too. It does not edit the fact down. The reply lists the kinds that were removed, including the notes when a note was removed.

### Hermes pins, next to Track 5's list

Track 5's lore-closeout list, from P10-READ, is `tui_gateway.contracts.registry.SERVER_REQUESTS`, `registry.server_request`, `tui_gateway.server_requests.send`, `tui_gateway.server._sessions`, and `tui_gateway.server._current_runtime_session_record`.

Track 6 adds the internals the forget path now uses. A Hermes rename of any of these fails `test_forget_path_hermes_internals_keep_their_names`:

- `tools.memory_tool.memory_tool`
- `tools.memory_tool.load_on_disk_store`
- `agent.inline_tool_executors.tool_hook_ids`, which `agent.tool_executor._pre_tool_block` passes into `pre_tool_call`, including `turn_id` from `agent._current_turn_id`. The memory-provider dispatch is `_resolve_sequential_dispatch`: when `has_tool` is true it calls `MemoryManager.handle_tool_call`.
- `provider._current_user_message`, filled from the `message` argument Hermes `MemoryManager.on_turn_start` passes to the provider.

### Suites

Client stopped for the phone suite. Workspace 577 OK (107.423s). Memory 156 OK (18.716s), the new pin included. Tools 44 OK. TTS 8 OK. Phone 71 OK (47.942s). Client Release 0 warnings, 0 errors, same output directory as the bench build. Checks exit 0, 250 PASS, 0 FAIL. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded. The Kotlin deprecation warnings are the ones already on those files.

Client started again on that build, not a new mirror. Client 3680, parent 16004. Watcher 24860, child 28636. Phone 20512, child 42804. Serve 22144, child 18424. Started 12:58:52. One of each.

## Phase 5 follow-up (2026-11-05)

Phase 5 is accepted. No code change. The run sheet below is the one the smoke uses.

### Brian's verdicts (verbatim)

Spoken numbers: "Actually, it did recognize the number verbally. I used the sentence: Let me know when I get a text from <the Google Voice number>. I think it needed the reference of text message to register it as a number."

Chat history in the forget reply: "I don't think it is necessary to ban it."

Notebook sweep removing a whole fact that also names other people: "Keep it as is for now."

Asking whether to keep watching after a one-shot watch: "I don't see why it is a problem to ask a follow up. What if I did want her to keep watching? Leave it."

### Lore-closeout residuals

- Forget finds a person by their current Contacts name. A memory item stored under an older or different name form (the 2026-11-03 one-token episode) is not reached. That is the approved conservative rule. The gap is identity (one person, one entity, A04) and belongs to Phase 11.
- The notebook sweep removes a whole fact that names the person, even when that fact also names other people. Brian: "Keep it as is for now." Facts about other people in the same note go with it. The reply says notes were removed.
- She may ask whether to keep watching after a one-shot watch closes. Brian: "Leave it." The older `SOUL.md` line stays. If he says yes, that is a new watch request and goes through `zola_loops` on his turn like any other.
- A bare number spoken alone was transcribed as words in the W5 bench and refused by the number check. A number inside a sentence about texts is transcribed with digits and passes. That is a residual for the lore closeout, not a Track 6 fix.
- `agent.log` lines that log his own words stay the Hermes residual, not a fail.
- The forget reply may leave out removed kinds (texts, email, episodes) when she paraphrases the tool result. Must-tell facts are still conveyed. Decide at closeout whether the removed kinds should become a must-tell. No fix in this smoke.
- `forget_memory` confirm false returned 4 groups for one person and marked them as different subjects. Her question was one question, which passes. The fold is partial, not a regression. It absorbs a row only when the name is its own word. `group_candidates` still splits whatever remains by label. A longer word that starts with the name, and a one-token form, still do not match. The code path is in the Phase 6 report.
- A number forget whose contact owns the number did not ask whether to forget the person. The erase plan had no display name. The number path does not call `refresh_bounded`. A name forget waits up to 2 seconds through `contact_plan_waiting` when the words name a person. This sentence had digits, so it was not person-shaped, and `number_forget_plan` read `get_index` without waiting. A later fetch in another process waited and found the contact. The number's texts were forgotten and the person was not. No fix in this smoke.
- She may withhold unmasked code-looking text in a history read. Only masked items can be read through the code path. A possible `SOUL.md` wording is "only items the phone masked are codes." No fix in this smoke.

### Approvals of the six Phase 4 bench deviations

The six product rows in the Phase 4 STOP table. The runner row (511 discovered, then 577) is not one of them.

1. Confirmation lapse, and the revert of the whole-reply sentence (`loops.py` 35077, `turn_context.py` 9100). Brian: "Make an open confirmation lapse in code: it's dropped at the start of my next turn unless that turn's tool call is the answer to it." And: "Revert "the tool's sentence is the whole reply" from the tool description. Keep "a yes or no to that question goes back to the tool"."
2. W5 number watch (`loops.py` still live). Brian, before the rerun: "Record the fix and the redeploy in the progress doc as a bench fix, with mirrored file hashes." The pass he set is a number watch, channel text, a reply with no digits and no name, and a later text from that number giving the number line with nothing matched to the contact. The spoken-number verdict above is how he says the number in the smoke. It is not a new code change.
3. Entity deleted before the contact step (`forget.py` 77095, `contact_index.py` still live). That mirror went out after "Card is skipped" and before any approval sentence. Brian did not approve that order. The order he required next is the yes-path row.
4. Yes path, ticket and contact plan before any erase (`forget.py` 84742, `proactive_store.py` 167073). Brian: "Don't rerun B6 yet. This is a defect against verdicts 2 and 7: one yes must authorise the memory erase and the proactive forget together, and the phone/email step must not depend on the confirm word repeating the name. Fix it this way: Resolve the contact (numbers and emails) before any memory erase, and bind it to the same confirmation. On the yes, run both steps. If either step fails, the reply says exactly what was and wasn't done. Never use the memory-only line for a person who's in Contacts."
5. `empty_turn_id` (`forget.py` 100523, `proactive_store.py` 168944, `turn_context.py` still live). The progress doc said "Review answers, not approved" and then this change. The approval that came after that heading is quoted in that section: "Approved, with these conditions," including the turn-id cause, the preflight, the cold-index bound, and the Hermes path for notebook facts.
6. One person candidate, including the pending turns that name them, and the two must-tell facts (`forget.py` 101516, `proactive_store.py` 169185, both still live). Brian, on the candidate, before the code: "Redesign the candidate: when the name matches a contact, forget_memory returns one person candidate covering the contact's numbers and emails, any matching memory entity, and the episodes. One target, one yes, the person-forget reply." And: "I approve forget also removing notebook facts that name the person, under the same one yes, as part of the one forget path." After the data pass: "B6: the stores pass, so log it as a pass for the data. One open item for W6 in the smoke, not a bench rerun. Her reply must convey, in her own words, that the texts are still on my phone and that notifications are matched by display name only, so some may remain. The forget result should mark those two facts as must-tell, and the tool description should say so. Don't script the sentence. Also tell me what she said when she asked me to confirm: did she read four choices aloud? The approved shape is one person, one question. If the listing still returns separate groups for one person, fix that too."

## Phase 6 run sheet

Started 2026-11-05, 13:53 local. Daytime, outside quiet hours (22:00–07:00). Expected results are written first.

### Preflight

One client, 3680, parent 16004, started 12:58:52, exe `zola-p10-watch-client-build-p4b`. One watcher, 24860, child 28636. One phone, 20512, child 42804. One serve, 39352, child 31076, started 13:32:57, still parented by the client. No second client and no leftover watcher, phone, or serve.

Phone status: `link_state` connected, socket open, last ping answered, paired. `listener_permission` 1, `listener_bound` 1, allowlist count 3, notification queue 0.

Mirror: 62 files match. The three `zola_tools` files differ by newline only, the same Phase 1 residual. `zola_memory/l6_hold_guard.py` is the test helper and is not in the live plugins tree. Live `zola-tts/deepgram_tts.py` matches the worktree file once newlines are normalized. `SOUL.md` is 10458 bytes, SHA-256 `4411118908839cadd131d1723e969176451be8550172b41dcbb4b792ef9ff45b`.

Schema 8. Cutoff `2026-11-03T17:08:23Z`. Open loops 0. Closed loops: number 1, person 2, reply 9. Items 1823. Tombstones 67. Contact: one exact hit, 1 number, 1 email. Unavailable false.

Pending and eligible, available, after the cutoff, by shape: calendar 2 (body length 0). Gmail 43 (body null). MMS, e164, direct: body 0 × 1, 1–20 × 32, 21–80 × 36, 81+ × 11, plus attachments 13 with empty body, 1 in 21–80, 1 in 81+. MMS groups: 7, 3, 3 without attachments and 2, 3, 1 with, in those same length buckets. Notifications, unparsed, direct: 18, 14, 3. SMS, e164, direct: body 0 × 2, 1–20 × 4, 21–80 × 3, 81+ × 1. SMS shortcode: body 0 × 2, 21–80 × 1, 81+ × 6. No row is an exact `ZP10-W` marker. Seven older rows carry other `ZP10-` tokens from earlier tracks. W1 does not reuse them.

Open before W1: 0, which matches the row.

W1 create, 22:01:37Z. His transcript is the expected sentence, 34 characters, no digit run. One open person watch, channel both, lifetime once, `name_source` contacts_index, display length 4, two address hashes. Tool result ok, and its `say` is both sentences, including the freeze sentence. The stored assistant message is only "I'll let you know when Bebo texts or emails."

W1 text, 22:04:55Z. One sms row, body length 7, the marker, direct, `loop_matched` 1, delivery `delivered`. The watch closed `delivered` at 22:04:56Z. Open loops 0. Workspace speech log: one `claimed` for that attempt, `name_source` contacts_index, then `speech_started`, then `delivered`. Client `proactive.log`: the same attempt, `outcome=delivered`, `phrase=0`, `name_source` contacts_index. Phrase 0 of the named-text set is "Brian, quick one: Bebo texted you." No body and no digits. W1 passes.

W1c, open before 0. First transcript "Watch for Beebo". She said "Did you mean Bebo?" "Yes!" at 22:09:19Z created one person watch, channel both, lifetime once, two address hashes, at 22:09:23Z. She said she will tell him when Bebo texts or emails. "Stop watching for Bebo." listed that watch and closed it by id, with no intent argument. The row is `closed`. `closed_intent` is empty, not `cancelled`. The close clears the display name. She said "Stopped watching for Bebo." Open loops 0. Second "Watch for Beebo" got "Did you mean Bebo?" again. "No." returned created false, and she said she didn't change anything. No second watch. The empty close reason fails the cell. Smoke stopped. No fix.

### Smoke deviation (2026-11-05, W1c close reason)

A stop that listed the watch and closed it by id, with no intent argument, wrote `closed_intent` empty. `delivered`, `acknowledged`, `expired`, and `forgotten` already record their reason. The failing test is `test_stop_by_name_and_pronoun_records_cancelled`: "Stop watching for Beebo Dev." and "Stop watching for her.", each listed and then closed by id with no intent, must store `cancelled`. `test_each_close_path_records_its_reason` checks the other four. The fix is in `close_listed`: a "stop watching" message stores `cancelled` even when the call carries a loop id and no intent.

`loops.py` mirrored, 35916 bytes, SHA-256 `778d0944938ad26b8e400e99cc2519ddd76ee9f60d87432a3964f42186bc5336`. The worktree file matches the live file.

The one W1c row is left as it was. Counts only: 1 closed person watch, channel both, lifetime once, 2 address hashes, created 22:09:23Z, never matched, `closed_intent` empty. Three older closed reply rows from 2026-10-13 also have an empty close reason. Those were not rewritten.

Suites, client stopped for the phone mutex: workspace 579 OK (108.667s), memory 156 OK, tools 44 OK, TTS 8 OK, phone 71 OK (30.130s). Client Release 0 warnings, 0 errors, same output directory. Checks exit 0, 250 PASS, 0 FAIL. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded.

Client restarted on that build. Client 21804, parent 33556, started 14:27:09. One watcher, one phone, one serve. Phone link connected, listener bound, allowlist count 3. Open loops 0. W1c is rerun from the start.

W1c rerun, 22:32:04Z. Transcript "Watch for Beebo." She called `contacts_lookup` with that query. Result `no_match`, no contacts. She did not call `zola_loops`. Her sentence matches what Brian heard. No watch was created. Open loops stayed 0.

W1c rerun, pass, 22:34:43Z. "Watch for Beebo" called `zola_loops` create. The tool said "Did you mean Bebo?" She asked that. "Yes." at 22:35:00Z created one person watch, channel both, lifetime once, two address hashes. She said she will tell him when Bebo texts or emails. He said "Stop watching Bebo." She listed the one watch and closed it by id with no intent argument. The row is closed, `closed_intent` cancelled, display name cleared. She said she stopped. Open loops 0. The second "Watch for Beebo" got the same question. "No." returned created false. She said she didn't change anything. No second watch.

W2 line, 22:39:29Z. The first transcript was "Tell me when vivo emails", 26 characters, no digit run. `zola_loops` refused `not_in_contacts` and created nothing. He corrected it: "I said can you tell me when Bebo emails?" At 22:39:55Z one person watch, channel email, lifetime once, `name_source` contacts_index, display length 4, one address hash. Tool `say` includes the freeze sentence. She said she set it to tell him when Bebo emails. Open loops 1.

W2 text, 22:41:56Z. One sms, body length 7, the marker, direct, e164, one participant, display length 0. Its sender hash is not on the watch. `loop_matched` 0, delivery `none`, `watch_evaluated` 1. The email watch is still open and unmatched. Open loops 1. No new speech claim. The last claim is still the W1 attempt. Deliveries since the watch: 0. One rank attempt completed at 22:40:17Z, before the text. A separate notification arrived at 22:43:36Z: body length 11, not the marker, display length 21, unparsed, group, hash not on the watch, `loop_matched` 0, delivery `none`. It was not spoken. W2 passes.

W2b line, open before 1. A first transcript at 22:46:48Z was "Tell me when Bebo text.", 23 characters, no digit run. No tool call and no watch followed it. The next transcript, "Tell me when Bebo texts.", 24 characters, no digit run, called `zola_loops`. At 22:47:29Z one person watch, channel text, lifetime once, `name_source` contacts_index, display length 4, one address hash. That hash does not overlap the email watch's hash. Tool `say` includes the freeze sentence. She said she will let him know when Bebo texts. The email watch from 22:39:55Z is still open and unmatched. Open loops 2. The emails are not sent yet.

W1b email, 22:51:26Z. One gmail row. Subject length 8 and snippet length 8, both the marker. Body is null. `loop_matched` 1, delivery `delivered`. The email watch closed `delivered`, matched at 22:51:26Z. The close cleared its display name. The text watch from 22:47:29Z is still open and unmatched. Open loops 1. Speech attempt `2d2fd28719e60751` on that gmail row: claimed with `name_source` contacts_index, then `speech_started`, then `delivered` at 22:51:37Z. Client log: the same attempt, `phrase=0`, `name_source` contacts_index. The item is gmail, so phrase 0 is the first email sentence, name only. W1b passes. The second email is not sent yet.

W2b email, 22:55:28Z. One gmail row. Subject length 8 and snippet length 8, both the marker. Body is null. The sender hash is the email watch's hash and not the text watch's hash. `loop_matched` 0. Rank label `ignore`, eligibility `suppressed`, delivery `none`. No speech attempt and no new claim. The text watch is still open and unmatched. Open loops 1. W2b passes.

W3 line, 22:57:44Z. Transcript "Let me know when I hear from Bebo.", 34 characters, no digit run. Open before the turn was 1, the text watch from 22:47:29Z. She listed that one watch. She then tried to create an email watch. `zola_loops` refused `channel_disagrees`. She closed the listed text watch by id, with no intent argument. That row is closed, `closed_intent` empty, display name cleared, never matched. She then created one person watch, channel both, lifetime once, `name_source` contacts_index, display length 4, two address hashes, at 22:58:02Z. Those hashes are the email watch's hash and the text watch's hash. Tool `say` includes the freeze sentence. She said she will let him know when Bebo texts or emails. Open loops 1. The text watch was supposed to stay open. The cell fails. Smoke stopped. No sends.

### Smoke deviation (2026-11-05, W3 widen and blank close)

Replacing the open text watch with a both-channels watch is accepted. On a contact-watch turn she may close an older watch for that same person only after the new watch exists, and only when the new one covers every channel and the lifetime of the older one. The close result says "I've widened your text watch to cover email." A close the new watch does not fully cover is refused (`not_covered`), and the older watch stays open. A once watch does not cover a standing watch. Closing before the new watch exists is refused.

The blank close was `close_listed`: she had listed the text watch and closed it by id, with no intent argument. The message was "Let me know when I hear from Bebo.", which is not "stop watching", so the W1c branch did not run. The other branch stored a close reason only when the intent argument was in `_INTENTS`, and an omitted argument became `None`. `close_loop` then wrote that empty reason. The W1c check missed it because `test_stop_by_name_and_pronoun_records_cancelled` only uses a "stop watching" message, and `test_each_close_path_records_its_reason` checks delivered, acknowledged, expired, and forgotten, which set their reasons in their own SQL. `test_match_does_not_close_and_close_needs_list_and_ticket` closes by id with no intent and asserts only that the row is closed. `test_each_close_intent_is_stored_and_watch_intent_stays` always passes an explicit close reason. None of those hit a close by id on his turn with the reason omitted.

A close on his turn with no close reason, or with a watch intent (`person`, `number`), now records `cancelled`. An explicit `reply`, `cancelled`, `status_change`, or `confirm_close` is still stored as itself. `close_loop` no longer writes an empty reason: a missing one becomes `cancelled`.

Places that set a loop to closed, and the reason each one writes:

- `proactive_store._satisfy_matched_watches_locked`, acknowledged: `closed_intent` `acknowledged`. Once lifetime only.
- The same function, delivered: `closed_intent` `delivered`. Once lifetime only. A standing watch stays open.
- `proactive_store._close_loop`: the reason it was given. A missing reason is `cancelled`. This is the call `close_listed` and `_close_by_reference` make. `_close_by_reference` passes `cancelled`.
- `proactive_store.forget_subject`: `closed_intent` `forgotten`. A cancelled row is not retagged.
- `proactive_store._close_loop_from_match`: `cancelled` or `status_change` only.
- `purge_retention` sets status `expired`, not `closed`, and `closed_intent` `expired`.

`loops.py` mirrored, 41383 bytes, SHA-256 `018ccae0bbf403c8b615ae64042f445da941324acc8944a79baf19585f08db44`. `proactive_store.py` mirrored, 169349 bytes, SHA-256 `e08fcf6b34add7bf4cce054c94e6259acc776ca258b201a2e0d0536278875148`. The worktree files match the live files.

The two blank rows are left as they were. Counts only. One closed person watch, channel both, lifetime once, 2 address hashes, created 22:09:23Z, never matched, `closed_intent` empty. One closed person watch, channel text, lifetime once, 1 address hash, created 22:47:29Z, never matched, `closed_intent` empty. The three closed reply rows from 2026-10-13 are still empty and were not rewritten.

Suites, client stopped for the phone mutex: workspace 582 OK (103.836s), memory 156 OK (16.482s), tools 44 OK, TTS 8 OK, phone 71 OK (45.576s). Client Release 0 warnings, 0 errors, same output directory. Checks exit 0. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 98 total, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded.

Open loops 1: the person watch from 22:58:02Z, channel both, lifetime once, `name_source` contacts_index, display length 4, two address hashes. That is the expected count for the rest of W3. Client restarted on that build. Client 41968, parent 1380. One watcher, one phone, one serve. Phone link connected, listener bound, allowlist count 3. The three texts are not sent yet.

W3 texts, 23:23:40Z through 23:23:44Z. Three sms, each body length 7, the marker, direct, e164, sender hash on the watch. Four seconds apart. The first is `loop_matched` 1, delivery `delivered`. The other two are `loop_matched` 1, delivery `none`, conversation `none`. One speech attempt, `412b1e8289c97110`, on the first text: claimed with `name_source` contacts_index, `speech_started`, `delivered` at 23:24:07Z. Client log: that attempt, `phrase=0`, `name_source` contacts_index. The item is sms, so phrase 0 is the first named-text sentence, name only, no count. The both-channels watch closed `delivered`, matched at 23:23:42Z. Open loops 0. Two notifications and one other sms in the window were not on the watch, `loop_matched` 0, delivery `none`. W3 passes.

W3b, first number transcript, 23:27:41Z. One user message, 97 characters, 0 digit runs. The words are the two sentences, and the number place is "the Google voice number". No 10-digit run. `zola_loops` created one person watch at 23:28:05Z, channel both, lifetime once, `name_source` contacts_index, display length 4, two address hashes. She asked which Google Voice number to watch. No number watch. Open loops 1. First miss. He says that sentence once more. A second miss fails the cell and the smoke stops.

W3b, second number transcript, 23:30:57Z. 79 characters. 10 digit characters, in groups of 3, 3, and 4. Contiguous 10-digit runs: 0. Brian's decision: a spoken number in groups is valid. The check for W3b, W5, and W6b is 10 digits in the transcript, in any grouping. The number watch was created at 23:31:01Z: intent number, channel text, lifetime once, `name_source` mail, display length 8, one address hash. The person watch from 23:28:05Z is unchanged: channel both, lifetime once, two address hashes. Open loops 2. No third watch. W3b's spoken lines pass.

She did not ask the widen question. That is accepted. His "No" is skipped. There is no third watch.

Widen token. No user turn after 23:30:57Z. Tool results containing `lapsed` after that create: 0. The token lives in the running serve, minted on that create, and lasts 120 seconds. A later create call after that window drops it and does not create the widened person watch. There is no lapsed line, because no later turn called the tool while the token was still live. Nothing beyond the two watches was created.

Rule change, his decision. A direct reply to a request he just made may repeat a number he said in that request. A line she speaks on her own, when a text or email arrives, never says the digits. The tool description says that. The number-watch sentence no longer says it will not say the digits. `test_ten_digit_number_is_the_spoken_number` checks the description and checks that every unprompted number line has no digits. That change is in the worktree and is not in the running client. Worktree `loops.py` is 41553 bytes, SHA-256 `bef113a5ceaa6d73179c2656224e23218e8cd3c63f012113d116458900243a09`. The live `loops.py` is still the mirrored file from the widen fix, 41383 bytes, SHA-256 `018ccae0bbf403c8b615ae64042f445da941324acc8944a79baf19585f08db44`. The next restart is before a cell whose reply uses the new description.

W3b text and email, sent as the pair. The single `ZP10-W3b` text was skipped. The text arrived at 00:03:37Z: sms, body length 9, the marker, direct, e164. Its sender hash is on both open watches. `loop_matched` 1, delivery `delivered`, conversation `none`, not acknowledged. Both watches matched at 00:03:39Z and closed `delivered`: the person watch from 23:28:05Z, both channels, once, and the number watch from 23:31:01Z, text, once. One speech attempt, `f235f599040cc882`, completed 00:03:42Z. Client `proactive.log`: that attempt, `outcome=delivered`, `phrase=1`, `name_source` contacts_index. The item is sms and the matching name is from the contact index, so phrase 1 is the second named-text sentence, name only, no count and no digits. No second delivered line. `zola_workspace.log` was last written at 15:24:41 local and has no line for this attempt. `voice-timeline.log` was last written at 15:31:21 local.

The email arrived at 00:04:44Z, 67 seconds after the text. Subject length 9 and snippet length 9, both the marker, body empty. Its sender hash is on the person watch and not on the number watch. By then both watches were already closed. Rank label `ignore`, eligibility `suppressed`, `loop_matched` 0, delivery `none`, conversation `none`, not acknowledged, `watch_evaluated` empty. No speech attempt.

W3b passes. Expectation corrected. One line for two overlapping watches follows the overlapping-watch rule: the item is claimed once, the line is chosen once, and each open watch records its own match. Both one-shots closing `delivered` follows verdict 3: a delivered line closes a one-shot with `closed_intent` `delivered`. The email 67 seconds later matching nothing follows the same verdict: once that line is delivered and the one-shot has closed, a later item is unmatched. A simultaneous text and email cannot be produced by hand, because the line plays within seconds. That case is covered by `test_text_and_email_one_line_both_pending`. Open loops after the cell: 0.

Four other messages in the window were not the marker and not spoken: a gmail at 23:34:33Z, an sms at 23:41:19Z with body length 12, a gmail at 23:56:41Z, and an mms at 00:06:28Z with body length 6. Each is `loop_matched` 0, delivery `none`.

W3c. Open before the cell: 0. During the request, `zola_loops` listed 0 watches and created nothing. The text arrived at 00:50:48Z, the same second the reply to that request was stored: sms, body length 8, the marker, direct, e164. Its sender hash is on the closed person watch and the closed number watch. `loop_matched` 0, delivery `none`, conversation `none`, not acknowledged, `watch_evaluated` 1. No speech attempt. The client log after the W3b line has deny reasons `turn`, `capture`, `playback`, and `not_idle`, then idle. No delivered line. The replies do not contain the marker. He reports she did not bring it up. Nothing was created or removed. Open loops stay 0.

W3c passes. Expectation corrected. The sheet expected an open person watch, a matched-not-told text, and an acknowledge that closes it. No watch was open. Verdict 3 allows a claim only while an open watch covers the item. An unwatched text is not spoken. That is `test_unwatched_text_never_claimed`. She is not required to bring up an unmatched text.

W4. Scratch store, then deleted. One `notifications.event` through `ingest_phone_item`, display length 4, the contact's name, package length 22. An open person watch was on that scratch store. The row is source `notif`, `loop_matched` 0, delivery `none`. Binding it to the watch is refused `notif`. Claiming it is refused `phone_deferred`. That is `test_notification_never_matches_through_ingest` and `test_notification_never_claimed`. Live open loops stay 0. Live notification rows: 52, all delivery `none`. Speech attempts since the W3c text: 0. He hears nothing. No live Instagram send.

Contact edit. People fetch: 277 people, one exact name, name length 4, numbers 0, emails 1, canonical numbers 0, shared numbers on that person 0. The contact was not deleted.

`loops.py` mirrored before the restart, 41553 bytes, SHA-256 `bef113a5ceaa6d73179c2656224e23218e8cd3c63f012113d116458900243a09`. The worktree file matches the live file. The previous client tree was stopped. The new tree is client 33304. One watcher, one phone, one serve. Phone link connected, listener bound, allowlist count 3. Open loops 0. The number sentence is not spoken yet.

W5 line, session `20261105_170213_b9f500`. One user message, 129 characters. 10 digit characters, in groups of 3, 3, and 4. Contiguous 10-digit runs: 0. The check passes. `zola_loops` first listed 0. The second call created one number watch at 14:54:51Z, channel text, lifetime once, `name_source` mail, display length 8, the placeholder, no digits in the display, one address hash. The tool `say` and her stored reply are both 41 characters, no digits, no name, and no widen question. Open loops 1.

W5 text, 14:58:21Z. One sms, body length 7, the marker, direct, e164. Its sender hash is the watch's hash. `loop_matched` 1, delivery `delivered`, conversation `none`, not acknowledged. The watch matched at 14:58:22Z and closed `delivered`. The close clears the display name. Client log: a `quiet_hours` deny, then one delivered attempt `3153eada90ffa962` at 15:00:05Z, `phrase=0`, `name_source` someone. The item is a number-watch text, so phrase 0 is the first number sentence: that number texted, no name and no digits. Open loops 0. W5's text passes.

The number is back. People fetch: 255 people, one exact name, name length 4, numbers 1, emails 1, canonical numbers 1, shared numbers on that person 0. Open loops 0. One stored phone identity, an sms, is set aside in scratch for the replay. It is not logged here.

W6, session `20261105_170213_b9f500`. "Forget Bebo" is 12 characters. `forget_memory` with confirm false returned 4 groups: 4 episodes and 1 person. Every label contains his name. The tool marked them as different subjects. Her reply is 152 characters, one question, no digits: remove all of those records. Not a menu. He said yes, 3 characters. Confirm true. The tool message names the texts, the email, the watches, and the episodes. `must_tell` is `notifications_display_name` and `texts_on_phone`. Her reply is 161 characters, no digits. She says she forgot him and the watches, that some notifications may remain, that the texts are still on the phone, and that the old chat history remains. She does not name the texts, the email, or the episodes the tool said were removed.

Store: items whose sender hash is his number or his email, 0. Items whose display name is his, 0. Tombstones created since 15:40Z, 8. The number watch from 14:54:51Z is closed `forgotten`, hash list empty, display empty. Open loops 0. Memory counts from the confirm: fact rows 0, history rows 0, fts rows 5, episode rows 4, pending rows 0, link rows 4, entity rows 1. The Google contact is still one exact name, 1 number, 1 email.

Replay, after the yes. A sqlite backup copy of the live store. `ingest_phone_item`, the call `zola_phone` runtime `_ingest` makes, with the captured sms identity and a sentinel body. Result `suppressed`. Items 1889 before and after. Sentinel rows 0. The copy and the capture are deleted.

W6 passes. Expectation corrected. Nothing was created, removed, or spoken that should not have been. She claimed nothing untrue. The person and the content were his. The stored state is the forget above. Her reply conveyed both must-tell facts from the B6 verdict: the texts are still on the phone, and notifications are matched by display name only so some may remain. B6 also said not to script the sentence. Under-naming the removed kinds is not over-claiming. The "names what was removed" line was written to prevent over-claiming. The two residuals are on the lore-closeout list. No fix in this smoke.

W6 read, 15:55Z. "What did Bebo say?" is 18 characters, one question. `phone_read_texts` returned ok, person length 4, 10 messages, the newest body length 7. Her reply is 32 characters and names that newest text. Items stayed 1889. Items detected since 15:45Z: 0. Tombstones stayed 75. Open loops 0. The read stored nothing.

W7 text, 15:58:13Z. One sms, body length 7, the marker, direct, e164. Its sender hash is the contact's number. `content_state` available, eligibility eligible, `loop_matched` 0, delivery `none`, conversation `none`, `watch_evaluated` 1. No speech attempt. The client log has no new delivered line. Open loops 0. Tombstones stayed 75. A gmail at 15:59:03Z, body length 543, is not the marker, eligibility pending, and was not spoken. The text passes.

W6b, first transcript. One user message, 33 characters, 0 digit characters. The number place is the words "the number". No 10-digit group. `forget_memory` confirm false returned one group, not a number: 2 episodes and 1 pending turn. Labels are length 8 with 6 digits, and they do not contain his name. She asked whether to remove them from her memory. He answered, 4 characters. Confirm true erased those 3 memory rows. Counts also show 1 entity row, 3 fts rows, and 1 link row. The tool said it could not link that to one person. Her reply says they are gone from her memory, still in the old chat history, and still on the phone. She did not ask about forgetting him. The `ZP10-W7` text is still stored: sms, body length 7, the marker, `content_state` available. Tombstones stayed 75. No tombstone since 16:00Z. Open loops 0. First miss. He says that sentence once more, with the digits. A second miss stops the smoke.

W6b, second transcript, stops the smoke. One user message, 45 characters. 10 digit characters, in groups of 3, 3, and 4. Contiguous 10-digit runs: 0. The tool argument has the same grouping and no contiguous 10-digit run. `number_forget_plan` looks for one run of 10 to 15 digits, so it returned no number. `forget_memory` confirm false: no groups, message "No matches. I couldn't link that to one person, so I did not change your pending list." Nothing erased on this turn. Tombstones stayed 75. Open loops 0. The `ZP10-W7` text is still stored: sms, body length 7, the marker, `content_state` available, eligibility eligible, loop_matched 0, delivery none. Her reply, 122 characters, 0 digits, no question, does not name him: nothing is left from that number in her memory, and the texts remain on the phone and in the old chat history. That claim is untrue. The tool did not change the pending list, and the text is still stored. The watch path accepts this grouping because it strips separators. This forget path does not. She did not ask about forgetting him, because no number candidate was returned. No fix in this smoke.

The three rows the first confirm removed, counts and shapes only. He said yes to that question. The rows are gone.

- Episode, date 2026-11-03. The label is two tokens, each length 3, all digits. The memory tombstone for this erase uses that episode's id, record kind episode, erased 2026-11-06. The summary was deleted with the row, so its significance is not recoverable. It is not a synthetic test row. Those are inserted into a temporary database. One episode from that day remains: recorded 2026-11-03, significance other, length 72, no digits, and it does not contain his name. The 43-character one-token episode is not in the table anymore. Episodes that contain his name: 0. Episodes of length 43: 0.
- Episode, date 2026-11-05. The same label shape, two 3-digit tokens. It is not the tombstone id. The summary is gone. It was a live episode, not a test fixture and not a `ZP10` marker.
- Pending turn, created 2026-11-06, turn index 1, disposition keep, reason ordinary. The logged user length is 129 and the assistant length is 41. That is the W5 number sentence and the 41-character number-watch reply. Not a `ZP10` marker. Not synthetic.

The tombstone counts are fact rows 0, history rows 0, fts rows 3, episode rows 2, pending rows 1, link rows 1, entity rows 1. The entity row is the orphan removed with the episodes. It is not one of the three listed rows.

W6b fix, his approval: "W6b: approved fix." Number forget uses the same number extraction as the watch path. One function, `phone_ids.spoken_number`, normalizes through `phone_ids.normalize`. Grouped digits with spaces or dashes, a bare 10-digit run, and a +1 form are the same number. `loops._create_contact_watch` and `number_forget_plan` both call it. A forget result with no number in his words comes back `status` `no_number`. A number that was found, with nothing held for it, comes back `status` `nothing_held`. The tool description says that when status is `no_number`, she must not say that nothing is left. Tests: `test_grouped_number_forget_uses_the_watch_extractor`, `test_no_number_is_not_nothing_left`, `test_number_found_with_nothing_held`. The first run failed, then the code matched.

Suites, client stopped for the phone mutex. Workspace 582 OK (123.237s). Memory 159 OK (8.633s). Tools 44 OK. TTS 8 OK. Phone 71 OK (27.241s). Client Release 0 warnings, 0 errors, same output directory. Checks exit 0, 250 PASS, 0 FAIL. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 98 total, 0 failures, 0 errors, 0 skipped. `assembleDebug` succeeded.

Mirrored. `phone_ids.py` 5,791 bytes, SHA-256 `aa901a36600ff5f6ef626ceacc3956a15d939036a0cdd0225daee34e26b5aceb`. `loops.py` 41,557 bytes, SHA-256 `94577f6093ff500d6f9a3f609067d2cb27398c4a8c13a9f12721bc7e63653747`. `proactive_store.py` 170,507 bytes, SHA-256 `a03e13856126fd31b3ef8674b9a5da8c3542c6771545de451f8a59554a6be540`. `forget.py` 103,002 bytes, SHA-256 `f35952d58903eadf68c1586cebb640c568115c6ad6ad4abb1dc515157c46b0c2`. The worktree files match the live files. The previous client tree was stopped. The new tree is client 41788. One watcher, one phone, one serve. Open loops were 0 before the stop. The `ZP10-W7` text is still stored. The rerun sentence is next.

W6b rerun, first turn. New session. One user message, 35 characters. 10 digit characters, in groups of 3, 3, and 4. Contiguous 10-digit runs: 0. `forget_memory` confirm false: one group, kind number, message asks him to confirm before erasing and says it could not link that to one person. Nothing erased. Tombstones stayed 75. Open loops 0. The `ZP10-W7` text is still stored. Her reply, 80 characters, one question, no name, 0 digits: she found one matching number and asks whether to erase the texts held for it. The owner question is the erase result, so it is not due yet. He says yes.

W6b rerun, yes. User message length 3. `forget_memory` confirm true, ok. Erased 1, kind number. The tool message is 42 characters, no question, no name: the texts from that number are forgotten. It does not say the number is saved for anyone, and it does not ask to forget him entirely. Her reply is 154 characters, no question, no name, 0 digits. She says the texts held here are forgotten, they are still on the phone and in the old chat history, and notifications matched only by display name may remain. Both must-tell facts are in that reply. Items 1892, was 1893. Tombstones 76, was 75, one new since 16:20Z. The marker text is gone. Two other sms from that window, different sender hashes, are still stored. The gmail is still stored. Open loops 0. A contact fetch after the turn: 255 people, one exact name, name length 4, numbers 1, emails 1, and that person owns this number. The erase plan had no display name, so the owner question was not in the tool result. Expectation corrected. The no-owner number message does not ask. The sheet expected the question because the contact owns the number. Nothing untrue was said. The person was not forgotten. He does not say no. Residual for the lore closeout, no fix in this smoke: the owner question did not fire on a number the contact owns. Investigate why that plan had no display name.

Phase 6 report, no fix. The number-owner path skips the 2-second cold-index wait. A name forget goes through `_plan_for_forget`, and that calls `contact_plan_waiting` only when `_spoken_person` returns a name. `_spoken_person` returns nothing when the words after "forget" contain a digit, run longer than three words, or include "the". This sentence did all three, so the plan came back `missing` and `refresh_bounded` was not called. The owner is then `number_forget_plan`. That calls `get_index`, and `get_index` only starts a background refresh and returns whatever index is already installed. It does not join the fetch. If that index is missing, or a first load is still in flight, `contacts_unavailable` is true and the plan returns the hash with an empty display name. The later fetch was a separate process that called the People fetch and waited for it, so it found the contact. The name path's wait is `refresh_bounded(TURN_REFRESH_BOUND_SECONDS)`, and that bound is 2.0 seconds. The number path never calls it.

The three rows from the first W6b confirm, counts and shapes. He said yes to that question. They were live memory rows, not synthetic test inserts. Synthetic rows are written into a temporary database with significance `synthetic`. These ids were in the live memory database.

- Episode, date 2026-11-03. Label: two tokens, each length 3, all digits. This erase's tombstone uses that id, record kind episode, erased 2026-11-06. The summary was deleted with the row, so significance is not recoverable. One other episode from that day remains: significance other, length 72, no digits, no name. Episodes that contain his name: 0. Episodes of length 43: 0.
- Episode, date 2026-11-05. The same two-token label. Not the tombstone id. Summary deleted. Not a `ZP10` marker that could be checked, because the text is gone.
- Pending turn, created 2026-11-06, turn index 1, disposition keep, reason ordinary. Logged user length 129, assistant length 41. That is the W5 number sentence and the 41-character number-watch reply. Not a `ZP10` marker.

Tombstone counts for that erase: fact rows 0, history rows 0, fts rows 3, episode rows 2, pending rows 1, link rows 1, entity rows 1. The entity is the orphan removed with the episodes.

W7, cursor-run, verdict 16. Not spoken. Scratch process 27392, its own home, contact index forced unavailable through `set_unavailable_for_tests`. The handler was given "Forget Bebo." Confirm false returned one person id. Confirm true, ok. Reply length 88. It says contacts couldn't be checked and this may be incomplete. It does not say "I've forgotten". It does not say "2 seconds", which is the timeout bound, not the forced-unavailable bound. The scratch text was removed. The scratch watch closed forgotten. The process exited. The live client stayed 41788. Live open loops 0. `test_partial_reply_index_down` and `test_index_bound_forgets_what_it_can_and_says_so` passed. W8 is next.

W8 text, 17:02:12Z. Open before the cell: 0. One sms, body length 7, the marker, `watch_evaluated` 1, `loop_matched` 0, delivery `none`, conversation `none`. No speech attempt since 16:40Z. Open loops stay 0. He stayed quiet and said done. The client speech log's last delivered attempt is still the W5 line. Repeated idle reasons are not written again, and the last line is idle, nothing speakable. Scratch notification, then the scratch store was deleted. One `notifications.event` through `ingest_phone_item`, display length 4, package length 21. An open person watch was on that scratch store. The row is source `notif`, `loop_matched` 0, delivery `none`. Binding it is refused `notif`. Claiming it is refused `phone_deferred`. Live notification rows: 56, all delivery `none`. No live Instagram send.

The question, 09:09 local. Voice turn, 4 tool calls, first audio 23 seconds after submit. `phone_read_notifications` returned `no_match`, count 0, in 375 ms. The tool sentence is that there are no notifications from the apps she can see. Her reply is 231 characters, 0 digits. It says there aren't any live phone notifications from the apps she can see, then adds a pending-mail summary from `whats_pending`. That list had a mail section and a phone section. Counts on it: suppressed 82, expired 0, content-expired 0, unranked 0, rank_failed 1. No open watch was listed. Two content words in the reply, lengths 4 and 9, are not in the tool text. The notification sentence matches the empty read. The `ZP10-W8` text stays `loop_matched` 0, delivery `none`. Speech attempts since 16:40Z stay 0. Open loops 0. Three later voice turns, no tools, are outside this cell. W8 passes. W9 is next.

W9 line, 17:18:50Z. Open before it: 0. The transcript is the W1 sentence, length 34, 0 digits. Voice turn, 3 tool calls, first audio 15 seconds after submit. `zola_loops` created one person watch, channel both, lifetime once, display length 4, `name_source` contacts_index, 2 address hashes. The tool say is 111 characters and includes texts or emails and the saved-addresses sentence. Her reply is 44 characters, 0 digits, no question: she will let him know when he texts or emails. The saved-addresses sentence is in the tool result and not in the reply, the same split as W1. Open loops 1.

W9 read, 09:21 local. "What did they say?" is 18 characters, no name, 0 digits. Voice turn, 2 tool calls, first audio 20 seconds after submit. `phone_read_texts` was called with the pronoun. It resolved one person, name length 4, and read the phone live: ok, state complete, 5 inbound sms, one number leg answered, capped, 3077 ms. None of the five is marked as a verification code. Each body is a scripted marker. Lengths 7, 7, 7, 8, 9, newest first. The read did not store them. One mms arrived at 17:19:20Z with body length 0, `loop_matched` 0, delivery `none`. The watch stayed open. Her reply is 91 characters, 0 digits. It names him, and withholds the newest text, body length 7, as a code she can't repeat. That text is an unmasked scripted marker. Expectation corrected. The pronoun resolved to the watched person, the read was live, and nothing was stored. No untrue claim. She failed toward caution. The code-withholding residual is above. "Stop watching for them" is next.

W9 stop, 09:32 local. The transcript is that sentence, 23 characters, no name, 0 digits. The turn is typed, one tool call, first audio 12 seconds after submit. `zola_loops` returned ok. The watch from 17:18:50Z is closed `cancelled`. Channel both, lifetime once, `name_source` contacts_index. The close cleared the display name. Her reply is 26 characters, 0 digits: she stopped watching for him. It does not say the watch had already closed. Open loops 0. W9 passes. W10 is next.

W10, 09:35 local. "What are you watching for?" is 26 characters, no name. The turn is typed, one tool call, first audio 7 seconds after submit. `zola_loops` list returned ok, 0 loops. Her reply is 18 characters, 0 digits: nothing right now. She did not name a person or a number. Open loops stayed 0. W10 passes.

RCS. Since 2026-11-05T20:00Z, `rcs_flag` yes: 0. Rows in that window are null 36 and unknown 78. No natural RCS text arrived. Not a closeout gate.

Phone grep, PC logs. The needle is the contact's one number. Plugin logs, `zola_phone.log` and its three rotations, `zola_workspace.log`, `zola_memory.log`, `zola_tools.log`, `zola_watcher.log` and its rotation and out log, `errors.log`, `gui.log`, and `agent.log.1`: markers 0, name 0, misspoken form 0, number 0. `agent.log`: markers 0. Name 37, misspoken form 8, number 5, all `conversation turn:` lines. No other line in that file has the name or the number. That is the Hermes residual. The handset is on USB. `companion.log` and its three rotations: markers 0, name 0, misspoken form 0, number 0. The device buffer's last 8000 lines: markers 0, number 0. Five lines contain the package name `com.beebo.zola`. After that token is removed, the misspoken form is 0. The phone grep is 0.

### Phase 6 report, before closeout

Report only. No fixes. Smoke passed.

**W6, four groups.** Partial fix, not a regression. The B6 change does not make every mention one group. `handle_forget_memory` on confirm false builds candidates with `search_candidates`, then `_absorb_person`. That function removes an episode, a pending turn, or a notebook fact only when `_names_person` is true, and it adds one person candidate. `_names_person` is true only when `_speech_form` of the name appears as its own word. `_speech_form` drops punctuation and joins the letters, so a possessive becomes one token and does not match the bare name. A one-token form that starts with the name also fails that word check. Those rows stay in the candidate list. `group_candidates` was not changed. It groups the remaining candidates by `_short_label`, and `_short_label` keeps capitalized tokens from `[A-Za-z0-9]+`, which splits on an apostrophe. More than one label sets `ask_brian` on every group, and the tool description tells her those are different subjects. The bench line "one person is one group" is `test_one_person_folds_the_pending_turns_that_name_them`: pending turns whose text contains the name as a word. The B6 fourth try, before that fold, was three pending turns and one person. W6, after the fold, was four groups holding four episodes and one person, and every label contained the name. Those episodes were not absorbed. The word-match fold is still in the code. The label grouper still applies to what the fold leaves behind. A possessive of the name is no longer part of that residual. The pre-closeout deviation makes a straight or curly apostrophe-s count as the name, so the fold and the notebook sweep take it. A longer word that starts with the name, and a one-token form, still stay outside the fold.

**W6b, owner lookup.** The number path skips the 2-second wait. A name forget calls `contact_plan_waiting` only when `_spoken_person` returns a name. That function returns nothing when the words after "forget" contain a digit, run past three words, or include "the". This sentence did all three, so `_plan_for_forget` returned `missing` and did not call `refresh_bounded`. The owner is `number_forget_plan`. That calls `get_index`, which starts a background refresh and returns the index already installed. It does not join the fetch. With no index, or with a first load still in flight, `contacts_unavailable` is true and the plan returns the hash with an empty display name. The later fetch was another process. It called the People fetch and waited, and it found the contact. The name path's wait is `refresh_bounded(TURN_REFRESH_BOUND_SECONDS)`, and that bound is 2.0 seconds. The number path never calls it. The tool message was the no-owner sentence. The contact still owned the number. The person was not forgotten.

**W6b first try, three rows.** He confirmed that question. Live memory rows, not synthetic inserts. Synthetic rows are written into a temporary database. None of these three is a `ZP10` marker.

- Episode, date 2026-11-03. Label: two tokens, each length 3, all digits. This erase's tombstone uses that id, record kind episode, erased 2026-11-06. The summary was deleted with the row. One other episode from that day remains: significance other, length 72, no digits, no name. Episodes that contain his name: 0. Episodes of length 43: 0.
- Episode, date 2026-11-05. The same two-token label. Not the tombstone id. Summary deleted.
- Pending turn, created 2026-11-06, turn index 1, disposition keep, reason ordinary. Logged user length 129, assistant length 41. That is the W5 number sentence and the 41-character number-watch reply.

Tombstone counts for that erase: fact rows 0, history rows 0, fts rows 3, episode rows 2, pending rows 1, link rows 1, entity rows 1. The entity is the orphan removed with the episodes, not one of the three rows.

**Expectation corrected.**

- W3b. One line for two overlapping watches: the item is claimed once and each open watch records its own match. Both one-shots closing `delivered`, and the email 67 seconds later matching nothing: verdict 3, a delivered line closes a one-shot, and a later item is unmatched. A simultaneous text and email is `test_text_and_email_one_line_both_pending`. She did not ask the widen question. That was accepted, and his "No" was skipped.
- W3c. Verdict 3: a claim only while an open watch covers the item. No watch was open, so the text was not spoken. `test_unwatched_text_never_claimed`.
- W6. B6: convey the two must-tell facts in her own words, and do not script the sentence. Under-naming removed kinds is not over-claiming. The stored forget was the one he described.
- W6b. The no-owner number message does not ask about the person. The plan had no display name. Nothing untrue was said. The person was not forgotten.
- W9 read. The pronoun resolved to the watched person, the read was live, and nothing was stored. She withheld one unmasked scripted marker as a code. No untrue claim. She failed toward caution.

**Smoke deviations, with the mirrored hashes.**

- W1c close reason. A listed stop closed by id with no intent stored an empty `closed_intent`. `loops.py` 35,916 bytes, SHA-256 `778d0944938ad26b8e400e99cc2519ddd76ee9f60d87432a3964f42186bc5336`.
- W3 widen and blank close. A create may close an older watch on that person only when the new watch covers its channels and lifetime, and the reply says so. A close on his turn with no reason records `cancelled`. `loops.py` 41,383 bytes, SHA-256 `018ccae0bbf403c8b615ae64042f445da941324acc8944a79baf19585f08db44`. `proactive_store.py` 169,349 bytes, SHA-256 `e08fcf6b34add7bf4cce054c94e6259acc776ca258b201a2e0d0536278875148`.
- Direct reply may repeat a number he just said. An unprompted line never says the digits. His decision during the smoke. `loops.py` 41,553 bytes, SHA-256 `bef113a5ceaa6d73179c2656224e23218e8cd3c63f012113d116458900243a09`.
- W6b number extraction, after the second transcript. One `phone_ids.spoken_number`, and the two empty statuses `no_number` and `nothing_held`. `phone_ids.py` 5,791 bytes, SHA-256 `aa901a36600ff5f6ef626ceacc3956a15d939036a0cdd0225daee34e26b5aceb`. `loops.py` 41,557 bytes, SHA-256 `94577f6093ff500d6f9a3f609067d2cb27398c4a8c13a9f12721bc7e63653747`. `proactive_store.py` 170,507 bytes, SHA-256 `a03e13856126fd31b3ef8674b9a5da8c3542c6771545de451f8a59554a6be540`. `forget.py` 103,002 bytes, SHA-256 `f35952d58903eadf68c1586cebb640c568115c6ad6ad4abb1dc515157c46b0c2`.

**Lore-closeout residuals.**

- Forget finds a person by the current Contacts name. A memory item under an older or different form, the 2026-11-03 one-token episode, is not reached. Approved conservative rule. Identity gap, Phase 11.
- The notebook sweep removes a whole fact that names the person, even when that fact also names other people. Brian: keep it as is.
- She may ask whether to keep watching after a one-shot closes. Brian: leave it. The older `SOUL.md` line stays.
- A bare number spoken alone was transcribed as words in the W5 bench. A number inside a sentence about texts is transcribed with digits.
- `agent.log` lines that log his own words are the Hermes residual. The line is `conversation turn:` from `agent/turn_context.py`. No Zola plugin writes it. At the phone grep: name 37, misspoken form 8, number 5, all that line. Plugin logs and the phone log: 0.
- Hermes internals the forget path uses, beside Track 5's list (`tui_gateway.contracts.registry.SERVER_REQUESTS`, `registry.server_request`, `tui_gateway.server_requests.send`, `tui_gateway.server._sessions`, `tui_gateway.server._current_runtime_session_record`). A rename fails `test_forget_path_hermes_internals_keep_their_names`: `tools.memory_tool.memory_tool`, `tools.memory_tool.load_on_disk_store`, `agent.inline_tool_executors.tool_hook_ids` (passed by `agent.tool_executor._pre_tool_block` into `pre_tool_call`, with `turn_id` from `agent._current_turn_id`; memory-provider dispatch is `_resolve_sequential_dispatch` to `MemoryManager.handle_tool_call`), and `provider._current_user_message` from `MemoryManager.on_turn_start`.
- The forget reply may leave out removed kinds when she paraphrases. Must-tell facts are still conveyed. Decide at closeout whether the removed kinds should become a must-tell.
- Four groups for one person, above. Partial fold, not a regression. The result shape is still not "one target, one yes" for rows the word check does not absorb. A longer word that starts with the name, and a one-token form, are what remain.
- A number forget whose contact owns the number did not ask, because the number path skips `refresh_bounded`. Above. No fix in this smoke.
- She may withhold unmasked code-looking text in a history read. Only masked items can be read through the code path. A possible `SOUL.md` wording is "only items the phone masked are codes." W9. No fix in this smoke.
- Two blank close reasons, left as they are. The W1c row: one person watch, both channels, once, 2 address hashes, created 22:09:23Z, never matched, `closed_intent` empty. The W3 row: one person watch, text, once, 1 address hash, created 22:47:29Z, never matched, `closed_intent` empty. Three older closed reply rows from 2026-10-13 are also empty and were not rewritten.

### Pre-closeout deviation

A possessive counts as the name. A straight apostrophe-s and a curly apostrophe-s match the name in `_names_person`. The person-candidate fold and the notebook sweep both use that check. A longer word that starts with the name does not match.

Failing tests first. `test_possessive_notebook_fact_is_removed_by_forget_bebo` and `test_possessive_episode_folds_into_one_person` failed on `_names_person`. `test_longer_word_starting_with_the_name_is_not_removed` passed before the change and still passes. A notebook fact beginning "Bebo's birthday" is removed by "Forget Bebo", for both apostrophes. An episode whose label comes from a possessive summary folds into the one person candidate. "Beboland" is not removed.

Suites, client stopped for the phone mutex. Workspace 582 OK (146.506s). Memory 162 OK (45.965s). Tools 44 OK (0.072s). TTS 8 OK (0.243s). Phone 71 OK (91.933s). Checks exit 0, 250 PASS, 0 FAIL. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 98 total, 0 failures, 0 errors, 0 skipped. `assembleDebug` BUILD SUCCESSFUL in 1m 48s. None hung.

Mirrored `forget.py`, 103,190 bytes, SHA-256 `7812d83be454cf6d9b3702333558f05aef3059505a7859a4696085b1aba6c83c`. The worktree file matches the live file.

Redeployed. Client 5444. One watcher, 42628. One phone, 47876. One serve, 25076.

Scratch home, the real `handle_forget_memory`, not live speech. The scratch directory was deleted after the run. Confirm false: 1 group, not marked as different subjects, one person id. Confirm true: ok. Possessive notebook facts remaining 0, both apostrophes, and both gone from the notebook file. Possessive episodes remaining 0. The longer-word fact remaining 1, still in the file, episode remaining 1. The one-token form does not match.

### 7a

Client closed for the phone mutex. Workspace 582 OK (124.123s). Memory 162 OK (26.764s). Tools 44 OK (0.067s). TTS 8 OK (0.237s). Phone 71 OK (63.165s). Checks exit 0, 250 PASS, 0 FAIL. Coverage lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 40/40, phone 16/16, code 32/32. Kotlin `testDebugUnitTest` with `--rerun-tasks`: CompanionRules 15, EngineFlow 39, NoticeFlow 30, Phase4 14, 98 total, 0 failures, 0 errors, 0 skipped. `assembleDebug` BUILD SUCCESSFUL in 1m 16s. None hung. The client was started again on the same mirrored `forget.py`: client 2028, one watcher, one phone, one serve.

Stopped before closeout.

Default is to run every cell again. Daytime. Voice mode unless a cell says otherwise. Sends are from the Google Voice number. Bodies are the markers below and nothing else. USB stays attached for the phone-log grep at the end. The Google contact is not deleted.

Before every cell, Cursor lists the open watches (intent, channel, lifetime, counts only) and compares the count with the Open before column. For the rest of the smoke, Brian's rule is: if her behaviour follows an approved rule and only the run sheet's expected result was wrong, record it as "expectation corrected", name the rule, and continue. He reviews those at the end. Stop only if something was created, removed, or spoken that should not have been, she claimed something untrue, the wrong person or message content was used, or a close reason or other stored state is wrong. A cell that says scratch does not change the live count.

On W3b, W5, and W6b, the number is spoken inside the sentence written in his list. After each of those lines, Cursor confirms the stored transcript has 10 digits, in any grouping, before anything else. Grouped 3-3-4 counts. If it does not, Cursor records the transcript shape (length, how many digit characters, how they are grouped) and Brian says the line once more. A second miss fails that cell and the smoke stops. No fix mid-smoke. The digits are not written down. A direct reply to that request may repeat the number. A line spoken on its own never says the digits.

Cursor, when he says go, before the first line: one of each process and no orphans; phone linked and the listener bound; mirror matches the worktree; schema 8; open loops 0; the contact is still one exact name, 1 number, 1 email. Record the pending inventory as counts and shapes. Then give him the go for batch 1.

| Cell | Open before | Expected |
|---|---|---|
| W1 | 0 | "Let me know when I hear from Bebo." One person watch, both channels. She says she will tell him when Bebo texts or emails. The tool result also carries the freeze sentence. One `ZP10-W1` text while he is quiet: one spoken line, name only, a text phrasing, no body and no digits. Speech log: one claim, `name_source` contacts_index. The one-shot closes delivered. |
| W1b | 2 | The send is the `ZP10-W1b` email in his list, after the W2 email watch and the W2b text watch are both open. One spoken line, name only, an email phrasing. That closes the email watch delivered. The text watch stays open. If he cannot send that mail, Cursor runs the scratch harness against a store copy and he skips the send. The live watcher still evaluates a real message when the mail arrives. |
| W1c | 0 | "Watch for Beebo." She asks whether he meant Bebo. "Yes" creates one person watch, both channels, once. He then says "Stop watching for Bebo." That watch closes cancelled, and open loops are 0 again, the count written for W2. A second try, "No", creates nothing. |
| W2 | 0 | "Tell me when Bebo emails." One email-only one-shot. A text from him does not speak and does not close it. Speech log: no claim. The text can show up later in conversation. It is not spoken unprompted. Open loops after the text: 1. |
| W2b | 1 | "Tell me when Bebo texts." The email watch from W2 is still open. A text-only one-shot is added. An email from him does not speak for the text watch. The `ZP10-W2b` email is that check. Open after both email sends: 1, the text watch. |
| W3 | 1 | The text watch from W2b is still open. "Let me know when I hear from Bebo" adds one person watch, both channels, once. Three `ZP10-W3` texts inside 180 seconds: one line, name only, no count. The other two stay pending and are not delivered. Both one-shots close on that delivered line. One more text after the window is its own event only if a watch is still open; a delivered one-shot does not speak again. Open after the line: 0. |
| W3b | 0 | "Let me know when I hear from Bebo," then "Also let me know when I get a text from <the number>." The number belongs to the contact, so she asks whether to watch for Bebo on any channel. He says "No." The number watch stays a number watch, text only. The person watch is unchanged. There is no third watch. Open after the No: 2. Expectation corrected: one line for the two overlapping watches, both one-shots close delivered, and an email that arrives after that line matches nothing. A hand send cannot land the text and the email before the line plays. `test_text_and_email_one_line_both_pending` covers that case. |
| W3c | 0 | Expectation corrected from 1. Both one-shots closed delivered on the W3b text, so the open count before this cell is 0. A text arrives while a turn is in flight. No unprompted line. An unmatched text stays unmatched, and she does not have to bring it up. |
| W4 | 0 | Cursor ingests a scratch notification whose display name is the contact. No live Instagram send. Speech log: no notification claim for the whole cell. He hears nothing. |
| W5 | 0 | He removes the Google Voice number from the contact, not the contact. Cursor records 0 numbers and 1 email. He says "Let me know when I get a text from <the number>." A number watch is created. One text: the number line, no name and no digits. He puts the number back. Cursor records 1 number and 1 email again. |
| W6 | 0 | Before he says forget, Cursor copies one stored phone identity (device id, kind, provider id) into scratch only. It is not logged and not committed. "Forget Bebo." One question, about that one person, not a list of choices. "Yes." Expectation corrected: the reply may leave out removed kinds when she paraphrases. It conveys both must-tell facts, texts still on the phone and notifications matched by display name only so some may remain, and it does not claim past conversations were erased. Phone items, email items, and watches for him are gone or redacted. Cursor replays the captured identity through the real `zola-phone` ingest against a backup-API copy. Pass is `suppressed` and nothing stored. The capture and the copy are deleted. Counts only. "What did Bebo say?" reads the phone live and stores nothing. A new `ZP10-W7` text is stored and can surface. The Google contact is still there. |
| W6b | 0 | "Forget the texts from <the number>." That number's items only. If the contact owns the number, she says so and asks whether to forget the person. She does not forget the person unless he says yes to that. He says "No." |
| W7 | 0 | Cursor's scratch serve, with the contact index forced unavailable. Reported as tested in code (verdict 16), not as live spoken behavior. "Forget Bebo." The reply says the forget may be incomplete. It does not claim a full forget. Cursor stops that serve by PID. The live client is the one in front again. |
| W8 | 0 | No open watch. One `ZP10-W8` text and one scratch notification, while he is quiet for 90 seconds. Speech log: zero claims. Then "What notifications do I have?" and she answers aloud. |
| W9 | 0 | After a W1-style line Cursor asks him to set up: "What did they say?" reads that person live, without him naming them. "Stop watching for them." closes that watch, or says it already closed if the one-shot already delivered. |
| W10 | 0 | "What are you watching for?" Names person watches from the tool list, and a number watch as a number, with channels. Not from memory. |
| RCS | 0 | If a natural RCS text arrives, record sender-shape tokens only and whether the index named the person. If none arrives, record that. Not a closeout gate. |
| Phone grep | 0 | USB attached. Grep the phone log (device log and `zola_phone.log`) and the PC plugin logs for the scripted markers, the contact name, and the number. Expected 0 in the plugin logs and the phone log. Hits in `agent.log` that are his own words are the Hermes residual above, not a fail. |

### His list

Voice mode. Wait wherever the list says wait. Cursor talks only to say the result and the next go. Before each block, Cursor has already checked the open-watch count against the row. If it does not match, Cursor stops before you speak.

**Lines, first set.** Say "Let me know when I hear from Bebo." Wait. You should hear that she will tell you when Bebo texts or emails.

**Sends, first set.** From the Google Voice number, send one text whose whole body is `ZP10-W1`. Stay quiet. You should hear one short line that names Bebo and says he texted, with no message body and no digits. Wait.

**Lines.** Say "Watch for Beebo." You should hear her ask if you meant Bebo. Say "Yes." Wait. Then say "Stop watching for Bebo." That watch should close cancelled, and open loops should be back to 0. Wait. Say "Watch for Beebo" again. You should hear the same question. Say "No." Nothing new should be created. Wait.

**Lines.** Say "Tell me when Bebo emails." Wait.

**Sends.** Send one text whose body is `ZP10-W2`. Stay quiet for the window. You should hear nothing. Wait.

**Lines.** Say "Tell me when Bebo texts." Wait.

**Sends.** If you can send mail as the contact, send one note whose body is `ZP10-W1b` for the email watch, and later one whose body is `ZP10-W2b` while the text-only watch is open. If you cannot send that mail, say so and skip both. You should hear an email line only for the first of those, and nothing for the second. Wait after each.

**Lines.** Say "Let me know when I hear from Bebo." Wait.

**Sends.** Three texts, bodies `ZP10-W3`, one after another, inside three minutes. Stay quiet. You should hear one line, not three. Wait.

**Lines.** Say "Let me know when I hear from Bebo." Then say "Also let me know when I get a text from <the number>." Cursor checks the stored transcript has 10 digits, in any grouping, before anything else. Grouped 3-3-4 counts. If it does not, Cursor tells you the shape and you say that sentence once more. A second miss stops the smoke. If she asks whether to watch for Bebo on any channel, say "No." She did not ask, and that is accepted, so the "No" is skipped. The number watch stays text only. The person watch stays as it is. There should not be a third watch. Wait until both watches are confirmed.

**Sends.** One text, body `ZP10-W3b`. Stay quiet. You should hear one line. Then send one text, body `ZP10-W3b2`, and one email, body `ZP10-W3b2`, as close together as you can. You should hear one line. Wait.

**Lines.** Open watches before this cell: 0. That is the expected count. Start an ordinary request that is not about Bebo, and keep going. During that request, send one text whose whole body is `ZP10-W3c`. You should not hear an unprompted line. Stay with the request until Cursor says the text is in.

**Sends.** The text is the one in the lines above, sent while the request is still going. When you are done with the request, acknowledge the text if she brings it up after. Nothing should be spoken about it after that. Wait.

**Contact edit.** Remove the Google Voice number from Bebo. Do not delete Bebo. Wait until Cursor confirms the counts.

**Lines.** Say "Let me know when I get a text from <the number>." Cursor checks the stored transcript has 10 digits, in any grouping, before anything else. If it does not, you say that sentence once more. A second miss stops the smoke. You should hear a number watch, with no name. The reply may repeat the number. Wait.

**Sends.** One text from that number, body `ZP10-W5`. Stay quiet. You should hear a number line, no name and no digits. Wait.

**Contact edit.** Put the number back on Bebo. Wait until Cursor confirms it is back.

**Lines.** Say "Forget Bebo." You should hear one question, not a menu. Say "Yes." You should hear what she was holding, and, in her own words, that the texts are still on your phone and that notifications are matched by the display name only, so some may remain. Mentioning that the old chat history still holds it is allowed. She must not suggest that past conversations were erased. Wait. Cursor does the replay in between and does not show you the identity. Then say "What did Bebo say?" You should hear a live read. Wait.

**Sends.** One text, body `ZP10-W7`. It should be stored. She does not have to speak if no watch is open. Wait.

**Lines.** Say "Forget the texts from <the number>." Cursor checks the stored transcript has 10 digits, in any grouping, before anything else. If it does not, you say that sentence once more. A second miss stops the smoke. You should hear that the number's texts were forgotten, and, because the contact owns it, a question about forgetting Bebo. The reply may repeat the number. Say "No." Wait.

**Lines, scratch.** Cursor will say when the scratch client is the one in front. Say "Forget Bebo." You should hear that the forget may be incomplete, not that everything is gone. Wait until Cursor says the live client is back. This cell is reported as tested in code.

**Sends.** With no watch open, send `ZP10-W8`. Stay quiet. You should hear nothing. Then ask "What notifications do I have?" and she should answer aloud. Wait.

**Lines.** After the next watch line Cursor asks you to set up: say "What did they say?" without the name. You should hear a live read. Then say "Stop watching for them." The watch should close, or she should say it already closed. Then ask "What are you watching for?" She should answer from the watch list.

Cursor then greps, with USB attached. Stop. No further cells until that grep is recorded.

To continue: "proceed to phase 6"

## Phase 7 — Closeout (2026-11-06)

Brian: smoke test passed, then "proceed to closeout".

### 7a — Suites and hygiene

The suite pass is the 7a table already recorded above, client closed for the phone mutex. None hung or skipped.

This track's twelve plugin files match the live mirror, byte for byte: `forget.py`, `runtime.py`, `contact_index.py`, `loop_match.py`, `loops.py`, `phone_ids.py`, `phone_tools.py`, `proactive_store.py`, `speech.py`, `surface.py`, `turn_context.py`, `watcher.py`.

Four live drifts are outside this diff. They are unchanged from `HEAD`. `zola_tools\calculator.py` and `zola_tools\__init__.py` differ. `zola_memory\l6_hold_guard.py` and `zola_tts\deepgram_tts.py` are in the worktree and absent live. Phase 1 already recorded a newline-only drift in `zola_tools`. This track does not copy those files.

`hermes-agent` is `345cd2b057a452236de401d3534b8502a7465e8d`, porcelain empty.

No `proactive.db`, `pc_key.bin`, `token.dpapi`, or `peer_state.json` is tracked. The spoken number is not in the plugin sources, the client sources, or this progress doc. `phone_test_keys.json` remains the existing test fixture.

### 7b — Progress completeness

Phase 3 verdicts 1–16 are verbatim above. The Phase 5 follow-up verdicts are verbatim above. The run sheet, the per-cell results, the Discrepancies section, and the lore-closeout residuals are in this file. Expectation-corrected cells are W3b, W3c, W6, W6b, and the W9 read.

### Exit criteria

| # | Criterion | Result |
|---|---|---|
| 1 | WA-G1–G4 answered; RD-W1–W13 and the prompt's questions; STOP verdicts verbatim | Met. Verdicts 1–16 are above. |
| 2 | W1–W7, W1b, W1c, W2b, W3b, W3c, W6b, W8, W9, W10 pass; RCS recorded; no content in the log | Met. Brian: "Smoke test passed." W7 is the cursor-run cell from verdict 16. W3b, W3c, W6, W6b, and the W9 read are expectation corrected under his smoke rule. RCS since 2026-11-05T20:00Z: `rcs_flag` yes 0. The phone grep is 0. |
| 3 | Only watched texts speak; notifications never speak; a burst speaks once; quiet hours unchanged | Met. `P10_NOTIF_NO_UNPROMPTED_SPEECH` stays True. `P10_TEXT_NO_UNPROMPTED_SPEECH` stays True and an unwatched text is `phone_deferred` unless a watch allows it. W4 and W8 were quiet. W3 was one line for three texts. Quiet hours stay 22:00–07:00. |
| 4 | One contact index; fuzzy names confirm; untrusted content cannot create a watch or a forget; a number watch does not widen without a yes | Met. The widen token lapses when the next turn is not the answer. |
| 5 | One forget path; tombstones stop a replay; a read after forget stores nothing; the partial reply is honest; the phone is not edited; both evaluators' race tests pass; the reinstall limit is stated | Met. The W6 replay was `suppressed`. W6's read stored nothing. W7's reply does not say "I've forgotten". Tombstones do not cover a new install. |
| 5b | A watch closes only when told, acknowledged, cancelled, or expired; overlapping watches and a text plus an email are one line, with every item still pending | Met for closes made after the W3 fix. One line for two watches is W3b and `test_text_and_email_one_line_both_pending`. Two older rows still have an empty `closed_intent` and were left as they are. |
| 6 | Suites, Kotlin, and client checks at or above the floors; none hung or skipped | Met. 7a: workspace 582 (floor 505), memory 162 (floor 134), tools 44, TTS 8, phone 71 (floor 62), checks 250 PASS and 0 FAIL, Kotlin 98 and 0 failures. |
| 7 | No Hermes, ranker, Gmail reader, companion, contract, or lore change; schema, memory, and watcher only as the Phase 3 verdicts allow; no installs; no production test switch; no live-file fault edit | Met. Schema 8 is verdict 12. `forget.py` and `watcher.py` are on the Phase 3 file list. The live profile was not used as a fault seam. `SOUL.md` was not edited. |

### Residuals for the Phase 10 lore closeout

P10-D13–D15 as built. A watch has a lifetime, a delivered line closes a one-shot, the unprompted line is a name or "that number" and never the message, overlapping watches are one line, and forget is one path for a person or a number.

Phase 10 limits, recorded as limits: the unprompted line is name only; notifications never speak; the line is one sentence, not the office-door ask.

`S84` in-flight rule, as built: a row whose delivery is `claimed`, `speech_started`, or `delivery_uncertain` is redacted and is not tombstoned. The rest of S84 is unchanged. `S85` is not resolved. Forget now reaches a person's numbers and emails through the contact index, which is the address-known-only-in-Contacts part. The rest stays: a series delete has no `recurringEventId`, his sent mail is not watched, watcher recovery is a relaunch, watching while the client is closed is deferred, Gmail Pub/Sub stays deferred, and a rotated refresh token is kept. `S86` is unchanged.

Track 5 carry-forwards stay open: the code backstop, the two-injection limit, and Messenger.

Residuals already listed: the Hermes-internals names in the Phase 6 report; serve crash dumps, including `python.exe.25760.dmp`; orphaned processes after a client close; the synthetic `482193`; the RCS probe (no natural RCS text). The lore-closeout list above stays, including the two blank close-reason rows and the code-looking-text caution.

The four-group residual no longer includes a possessive. A longer word that starts with the name, and a one-token form, still do not match. The number-owner path still skips the 2-second wait.

### 7c — Implementation commit

**Implementation SHA:** `7c701d9b27e125b8601ba82d40439fc9f8a94cf8`

Message: `feat(P10-WATCH): person and number watches, forget by person or number, watched-text speech — P10-D13/D14/D15`

### 7d–7e

Docs commit recording the implementation SHA: `100b713b7eae6689d99798a4afe6148bde6d8396`. Branch `p10-watch` pushed to origin. The tracked tree was clean.

### 7f — Merge

The worktree client was closed so the merge could leave that folder. Client 2028 and its watcher, phone, and serve are gone.

**Merge SHA (`main`):** `2e0b72ab23bdd78cd5b0b242ed77f396671d9a93` (`git merge --no-ff p10-watch`). Pushed to `origin/main`. `main` = `origin/main` at that commit.

### 7g

The commit that records this merge SHA follows. 7h follows that commit. 7i waits until Brian confirms the live state. Scratch `C:\Users\test\Dev\zola-spikes\p10-watch\` is still there, including the part4b backup. He relaunches the client from `main`.
