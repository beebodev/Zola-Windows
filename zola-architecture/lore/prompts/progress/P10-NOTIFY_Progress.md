# P10-NOTIFY Progress — Notifications

## Branch

- Primary folder: `C:\Users\test\Dev\zola-windows`, branch `main`
- Worktree: `C:\Users\test\Dev\zola-windows-p10-notify`, branch `p10-notify`
- Base SHA: `f12c271775c4b97dd504878e272018e69406f190` (`main` = `origin/main` at Phase 1)
- Worktree HEAD: `f12c271775c4b97dd504878e272018e69406f190`
- Hermes HEAD: `345cd2b057a452236de401d3534b8502a7465e8d` (detached `HEAD`, clean, no porcelain)
- Prompt: `P10-NOTIFY_Prompt_v1.1.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P10-NOTIFY_Prompt_v1.1.md`)
- Prompt SHA-256 (on-disk, 64,256 bytes): `2681e56e6a09bb7ba7d758ecb78d1e3971e1a947c2304694792f612cf2a272c5`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction. On-disk value recorded for Brian to confirm.
- Scratch: `C:\Users\test\Dev\zola-spikes\p10-notify\` (created, empty)
- Track 3 closeout tip this branch was cut from: `f12c271775c4b97dd504878e272018e69406f190`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Setup | COMPLETE (STOP) |
| 2 | Grounding | COMPLETE (Option A) — shade probe dropped; ticker text in the default dump |
| 3 | Proposal | COMPLETE — verdicts recorded below |
| 4 | Implement and bench | COMPLETE — B1–B8 on scratch |
| 5 | Review checkpoint | COMPLETE — F1–F9; Brian B1/B9/B10/B10b/B7/B8; bench build approved and landed |
| 6 | Smoke | COMPLETE — N1–N12, C3, C6, Part B; Brian: smoke test passed |
| 7 | Closeout | IN PROGRESS |

## Guardrails summary

- **G-SCOPE:** `android-companion/` (listener, allowlist, queue, engine, manifest, tests); contract v4 and vectors; Python contract tests and the fake phone in the same commit. PC code only where a Phase 3 verdict approves a listed candidate, including the required Companion-row change. This progress doc. Live plugin mirror only in Phase 6 Part B.
- **G-ARCH:** build plan v1.4 and Appendices A/B are truth. NT-G1–G12 stop for Brian.
- **G-PATTERN / G-ONE-ENGINE:** extend the Track 3 `CompanionEngine`. One engine per process. The listener does not own delivery, the socket, the state file, or queue acks.
- **G-ONE-WRITER / G-VERIFY-BOTH-WAYS / G-RESEND / G-COMMIT-BEFORE-ADVANCE / G-CANONICAL / G-TIMERS / G-PEER-CLOSE:** unchanged from Track 3.
- **G-MASK-BEFORE-QUEUE / G-MASK-WHOLE-ITEM / G-QUEUE / G-ADMISSION / G-NO-SILENT-LOSS / G-LISTENER-VISIBLE / G-VISIBILITY / G-READ-LIVE:** as written in the prompt. Coverage gaps are reported, not recovered. App removal is a named exception only if Brian chooses drop.
- **G-NOCHANGE:** no `hermes-agent` edits; no `watcher.py`, `ranker.py`, `surface.py`, `speech.py`, `loops.py`, `proactive_store.py`, Google modules, `SOUL.md`, identity, lore, or `config.yaml`. No Windows client change beyond candidate (d). No tools, surfacing, speech, or watch matching of notifications.
- **G-ROLLOUT:** no v4 APK while the phone's only reachable PC is the live v3 instance. Rollback build from `main` before the first install. Order approved at the Phase 3 STOP.
- **G-INSTALLS:** no new Gradle plugin, library, SDK component, or download unless listed at the Phase 3 STOP and approved. Nothing in the Hermes venv.
- **G-OLD-REPO:** old-repo credential and configuration files are never opened. The old ZolaAssistant app is recorded and never changed. Nothing in this track grants it notification access.
- **G-PHONE-HANDS-OFF / G-PROBE-REDACTED / G-PRIVACY / G-LOGS / G-PROCESSES:** as written in the prompt.
- **G-COMMENT:** `// P10-NOTIFY: <why> — P10-Dxx` / `# P10-NOTIFY: …`.
- **G-STOP / G-CLOSEOUT / G-LORE-SCOPE / G-LIVE:** no lore edits. Live steps one at a time, Phase 6 Part B only.

## Phase 1 — Setup

`git fetch origin` in the primary folder. `git status --porcelain` was empty. `main` = `origin/main` = `f12c271775c4b97dd504878e272018e69406f190`.

Worktree list before `git worktree add`:

```
C:/Users/test/Dev/zola-windows  f12c271 [main]
```

After the worktree:

```
C:/Users/test/Dev/zola-windows             f12c271 [main]
C:/Users/test/Dev/zola-windows-p10-notify  f12c271 [p10-notify]
```

Primary `main` stayed clean. Hermes stayed clean at the pin. No source files were modified. This progress doc is the only new file.

### Plugin suites (worktree, Hermes venv)

Python: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`.

The Zola client was **not** running. No process name or command line matched `Zola`, `Zola.Client`, or `zola_phone`. Nothing was listening on 47821 or 47822. The two `zola_phone` mutex tests passed in this run.

| Suite | Command | Result |
|---|---|---|
| `zola_workspace` | `python -m unittest discover -s tests -t tests` | 357 OK |
| `zola_memory` | `python -m unittest discover -s tests -t .` | 134 OK |
| `zola_tools` | `python -m unittest discover -s tests -t .` | 44 OK |
| `zola_tts` | `python -m unittest discover -s tests -t .` | 8 OK |
| `zola_phone` | `python -m unittest discover -s tests -t .` | 40 OK |

Matches the Track 3 close: **357 / 134 / 44 / 8 / 40**. Client was closed for this run.

### Client

`dotnet build windows-client\Zola.Client\Zola.Client.csproj`: succeeded, 0 warnings, 0 errors.

`dotnet run` of `Zola.Client.Checks`: exit 0.

coverage: lifecycle rows 22/22, admission rows 13/13, start rows 9/9, invalid pairs 6/6, stop_phrase rows 4/4, amendments 7/7, latch rows 18/18, wiring rows 9/9, clarify rows 20/20, timing rows 8/8, compress rows 8/8, supervision rows 38/38, speech rows 38/38, phone rows 11/11.

### Kotlin

`android-companion\gradlew.bat testDebugUnitTest assembleDebug` (`--offline`; cached Gradle, nothing downloaded). `JAVA_HOME` was the Android Studio JBR already on the machine. `unitTests.isReturnDefaultValues = false` in `app/build.gradle.kts`.

BUILD SUCCESSFUL. `CompanionRulesTest` 12, `EngineFlowTest` 39, `Phase4Test` 14. **65**, 0 failures. Matches the Track 3 close.

### Live profile (read only)

Live plugin tree: `%LOCALAPPDATA%\hermes\profiles\zola\plugins`. Compared every source file except `__pycache__` and `tests` (59 files). **55** match the worktree byte for byte, including the Track 3 closeout set:

| File | SHA-256 |
|---|---|
| `zola_phone/keys.py` | `fdf08a0ca4c70e762831403921600e84f0db8b8c6a58f2acff1ed725eb0fb790` |
| `zola_phone/runtime.py` | `0bdb7d8644573ca051f0b6bb16aecab255bca483147ae78e6e0841c7e193b926` |
| `zola_phone/serve.py` | `4c631cc8b5246694ca94feaea32aeaae48f8633b141e6a60b62490460803011c` |
| `zola_phone/wire.py` | `b058a6d49a49d311fcf02d856a256881e3d13336eaa1599f95df33bfd5356b1a` |
| `zola_workspace/contracts/phone_protocol.json` | `1d2fb8c950409025e80a1548013ef18b3bb0847713e6ec4da5992d5ba28aaab6` |
| `zola_workspace/contracts/phone_vectors.json` | `518e52e63c3d83f01bd080aa3ef7ef6b20f770a59c82a85152903df672ceaa3b` |

`phone_test_keys.json` is absent from the live profile. It exists only in the worktree.

Newline-only differences (equal after CRLF is normalized to LF; live is LF, worktree is CRLF): `zola_tools/__init__.py`, `zola_tools/calculator.py`, `zola_tools/plugin.yaml`.

Content difference, not modified: `zola_phone/tools/fake_phone.py`. Live 10,285 bytes, SHA-256 `0be5bc0478b65c5cfb61597ea9835c76ffc89836246eb2b115f74ae1c7550bdd`, 267 lines. Worktree 10,488 bytes, SHA-256 `461f80fdbd123f1677a03cc4c3b823b6efa3e76bdea954986be7f181fd69224f`, 269 lines. Diff stat +4 / −2 lines. The Track 3 closeout match list did not include this file.

Present in the worktree plugin tree and not under the live `plugins` directory: `zola_memory/l6_hold_guard.py` (test helper), `zola_phone/outage.py` (imported only by `test_induced_outage.py`), `zola_tts/deepgram_tts.py`. The live TTS script at `profiles\zola\zola-tts\deepgram_tts.py` matches the worktree file byte for byte (5,596 bytes, SHA-256 `7cd342e0ae3bad20f6a0e6b6fe0418db8d6c856d43ab173a3c5ee48eb0432288`).

`proactive.db` opened `mode=ro` at `profiles\zola\proactive\proactive.db`. `user_version` 0. `schema_version` 6. Counts: calendar_events 1070, cursors 5, deliveries 0, item_attempts 401, items 959, loops 9, meta 7, phone_tombstones 1, watcher_health 1, watcher_rejects 1. Phone rows by source: sms 57, mms 487, notif 0. Other item sources: calendar 30, gmail 385.

`phone\peer_state.json` keys: `closed_at_ms`, `device_id`, `last_disconnect`, `link_open`, `pc_seq`, `phone_seq`, `public_pem`, `rejected`. Shape only: `device_id` length 32 (not empty), `public_pem` length 178 (not empty), `last_disconnect` length 11 (value not recorded), `link_open` false, `pc_seq` 557, `phone_seq` 4731, `rejected` length 0, `closed_at_ms` 1793204902834. `pc_key.bin` is present, 498 bytes. `pc_id.txt` is present, 34 bytes. No key material recorded.

`tailscale ip -4`: `100.102.206.71`.

Firewall read-back, not modified:

- DisplayName "Zola phone intake": present, Inbound, Allow, Enabled, Profile Any, TCP local port 47821.
- DisplayName "Zola phone intake scratch": **not listed**. Nothing for Brian to remove.

No listener on 47821 or 47822.

### Phone (read only, USB serial `R5CW81KPB6X`)

`adb` is `C:\Users\test\AppData\Local\Android\Sdk\platform-tools\adb.exe`. `adb devices -l` listed one transport: USB `R5CW81KPB6X` (`SM_S918U1`, product `dm3quew`). The tailnet transport Track 3 recorded was not listed this session. Every command used `-s R5CW81KPB6X`.

- Android 16, SDK 36, security patch 2026-09-05, model `SM-S918U1`.
- Companion `com.beebo.zola.companion` `versionName=1.0.0`, `versionCode=1`, minSdk 36, targetSdk 36.
- `SCHEDULE_EXACT_ALARM`: `allow`.
- Granted permissions recorded, nothing changed: `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_REMOTE_MESSAGING`, `RECEIVE_BOOT_COMPLETED`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, `INTERNET`, `ACCESS_NETWORK_STATE`, `WAKE_LOCK`, `READ_SMS`, `POST_NOTIFICATIONS`, plus the app's own `DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`.
- `enabled_notification_listeners` does **not** contain `com.beebo.zola.companion` (expected). The five components named there are Gearhead, Google search, Microsoft Phone Link, Samsung launcher, and Samsung Smart Mirroring.
- SMS role holder: `com.google.android.apps.messaging`. `settings get secure sms_default_application` returned `null`.
- Packages (names only): present `com.life360.android.safetymapd`, `com.facebook.orca`, `com.instagram.android`, `com.google.android.apps.messaging`, `com.samsung.android.messaging`, `com.beebo.zola.companion`. Absent: `com.samsung.vvm`. A package-name scan also listed `com.tmobile.vvm.application` and `com.instagram.barcelona`.
- Old app `com.beebo.zolaassistant`: `pm path` returned nothing and `dumpsys package` returned no version or listener line. It is not in `enabled_notification_listeners`. A `pm list packages` scan also printed a platform `SecurityException` for user 10; that user was not queried further. Nothing was changed.
- Companion files via `run-as`, sizes only: `companion-state.json` 168,619 bytes; `companion.log` 874,364 bytes; `companion.log.1` 999,993; `companion.log.2` 999,994; `companion.log.3` 999,968; `install.json` 115; `profileInstalled` 24. Contents were not read.

### Entry gate

No `google-services.json` and no `local.properties` in the worktree. No Firebase file. `android-companion/gradle.properties` is the tracked companion file (`android.useAndroidX=true` and the Gradle JVM args only). No old-repo credential or configuration file was found.

### Discrepancies (recorded, not blocking Phase 1)

1. The prompt's known context says the old ZolaAssistant app is installed and declares `AvaNotificationListenerService`. This session it is absent for the shell user, and the listener setting does not name it. Not changed.
2. `adb devices -l` showed only the USB transport.
3. Live `fake_phone.py` differs in content from the worktree. Not modified.
4. Three live `zola_tools` files differ from the worktree by newline only.
5. No developer-supplied prompt SHA was in the Phase 1 instruction.

## Phase 2 — Grounding

Read: build plan Sections 1–5, Track 4, Track 5 RD-G2 and RD-G3b, Appendix A (P10-D01–D17, R1, R4), Appendix B. Contract v3. Companion engine, manifest, mask, reads, delivery book. `zola_phone` ingest and `loops.evaluate`. Store ingest and the speech hold. Old listener and its manifest entry only. Lore: `ROADMAP.md` line 357, `P2-D17` (`DESIGN_DECISIONS.md` 383), `P4-D25` (760), `P8-D09` (1489), `P8-D11` (1530). No source files modified.

The shade today has one Life360 posting and the companion's own foreground notification. It has no Messenger, Instagram, Messages, or voicemail posting, so NT-G3's DM-versus-like comparison and an update of the same Life360 posting are not observed yet. Recommendations below say which part is observed and which waits for Brian's batch.

### Redacted probe

`dumpsys notification` with the default redaction (no `--noredact`). The raw dump was not written and not printed. About 2,054,876 characters, 14 notification records. A first pass flagged 40 lines. Every one was a length wrapper of the form `Type [length=N]` (`[` `=` `]` around the word length) or a ticker of three dots. After treating those as redacted, content lines were 0. String lengths below are those wrappers.

Interest packages showing: Life360 1, companion 1. Messenger, Instagram, Instagram Barcelona, Google Messages, Samsung Messages, `com.samsung.vvm`, and `com.tmobile.vvm.application`: 0.

Life360 record: key hash `6c8a6eae55a6`, channel id `Place`, style `android.app.Notification$MessagingStyle`, flags line `AUTO_CANCEL` (not ongoing, not a group summary, not a foreground service), group key present, `when` `1793212250216`. Extras keys present include `android.messages`, `android.isGroupConversation` (typed Boolean; the bit was not in the redacted dump), `android.hiddenConversationTitle`, `android.messagingStyleUser`, `android.conversationUnreadMessageCount`, `android.template`. Lengths: title 6, text 18. `postTime` was not a separate labeled field.

Companion record: channel id `companion`, flags line `ONGOING_EVENT|NO_CLEAR|FOREGROUND_SERVICE`, group key present, title length 14, text length 4. No `android.messages`.

`dumpsys deviceidle whitelist` contains `com.beebo.zola.companion`, so battery optimization is off for this app.

### NT-G1 — Listener

Recommend **(a)**: on every `onListenerConnected`, sweep `getActiveNotifications()` and admit allowlisted postings whose identity is not in the seen set. The first bind after install, and the first sweep after an app is added to the allowlist, record what is already showing as seen and send nothing. A later sweep admits only what is still showing and not seen.

That recovers a posting that is still on the screen. It does not recover one that was dismissed, replaced, or cancelled during a gap. Those gaps are counted, not described as lossless.

Declaration, from the platform reference [EXT] `NotificationListenerService`: `android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"`, intent action `android.service.notification.NotificationListenerService`, `exported="false"` as in the platform sample. No `default_filter_types` or `disabled_filter_types` meta-data: an OS filter could drop a voicemail or a Life360 alert before our code sees it. The old app's entry is `exported="true"` with the same permission and action and no meta-data (`ZolaAssistant` manifest lines 103–111). Its service only buffers 20 raw notifications in memory (`AvaNotificationListenerService.kt` lines 14–32, 41) and can dismiss (`cancelNotification`, lines 55–63). This track does not dismiss anything (P10-D17). The old package is not installed for the shell user and was not changed.

The setup control opens `Settings.ACTION_NOTIFICATION_LISTENER_DETAIL_SETTINGS` with `EXTRA_NOTIFICATION_LISTENER_COMPONENT_NAME` [EXT](https://developer.android.com/reference/android/provider/Settings). If that activity is missing, fall back to `ACTION_NOTIFICATION_LISTENER_SETTINGS`. Android 13+ can treat an `adb install` as sideload and block the grant until Brian allows restricted settings from the app info page [EXT](https://support.google.com/android/answer/12623953). Whether this phone does that for `adb install` is not known. Brian records what he sees. Nothing in this track runs `cmd notification allow_listener` or `appops`.

`onListenerConnected` / `onListenerDisconnected`: the platform says `requestRebind` is the only call that is safe before connect or after disconnect, and it is documented as the rebind after `requestUnbind` [EXT](https://developer.android.com/reference/android/service/notification/NotificationListenerService). Recommend calling it from `onListenerDisconnected` anyway, because a system unbind is not our `requestUnbind`. If the system ignores it, `listener_bound` stays 0 and the gap stays open until the next bind. `BootReceiver` already handles `BOOT_COMPLETED` and `MY_PACKAGE_REPLACED` (`AndroidManifest.xml` lines 34–40) and starts the foreground service. Those paths also call `requestRebind`.

Process kill: the system keeps a notification-listener binding so it does not cold-start on every posting [EXT](https://developer.android.com/topic/performance/memory/guide/service-bindings). After `kill -9` the binding should bring the process back. A force-stop removes that until Brian opens the app (Track 3 lesson 8). Survival is observed at B6, N6, N8, and N10, not claimed from the document alone.

One engine. The listener is in the same process (no `android:process`). `CompanionService` owns the only `CompanionEngine`, created lazily, and `boot()` loads state once (`CompanionEngine.kt` lines 50–56, `CompanionService.kt` lines 57–71 and 83–94). Postings are delivered on the listener's binder thread [EXT]; the engine's worker is the single-thread executor (`CompanionService.kt` line 47). The listener posts each posting onto that worker and does not touch the socket, the state file, or acks.

If a posting arrives before `boot()`: the listener calls `startForegroundService` for `CompanionService`. Starting a foreground service from the background is refused unless an exemption applies [EXT](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start). This app is on the device-idle whitelist, which is the "battery optimizations off" exemption. If the start throws, the listener does not construct a second engine. It logs a gap. The posting is still on screen, and the sweep after `boot()` can admit it. `boot()` from a later start does not reload over a running engine.

### NT-G2 — Allowlist

Recommend a section on the existing setup screen (`PairingActivity`), not a second activity. Installed launchable apps, labels from the package manager, starts empty. Messages packages are shown and not selectable, with one line: texts already come from the message store. The companion's own package is absent from the list.

Never forwarded, even if a stored name names them: `com.google.android.apps.messaging` (the SMS role holder, confirmed this session), `com.samsung.android.messaging` (installed, not the role holder). No other role holder. `com.samsung.vvm` is absent. Visual Voicemail on this phone is `com.tmobile.vvm.application`.

Stored as package names in the notification state file, not in `companion-state.json` (see NT-G10). A change applies to the next event and the next read immediately.

Removing an app: recommend **drop** its queued unacked items, count `allowlist_removed`, and log the package name and the count. That is the third named exception in the no-loss-after-admission rule, and it is tested as one. An item already sent and awaiting ack is still deleted only on the terminal ack, not by the removal. `device.health` carries the list as package names only.

### NT-G3 — Message-only filter

Instagram (`com.instagram.android`) and Messenger (`com.facebook.orca`): not observed this session. Proposed rule, fail closed, until the batch confirms it: forward only when the posting has a `MessagingStyle` template or `CATEGORY_MESSAGE`, and it is not a call (category `call`, or an ongoing/foreground-service call). A like, follow, comment, or story that has neither fails closed and increments `notification_filtered`. No content in that log line.

Life360, observed: the one showing posting is `MessagingStyle`, channel `Place`, `AUTO_CANCEL`, not ongoing and not a summary. For Life360 and Visual Voicemail the message-only filter does not apply. Forward every posting that is not ongoing, not a group summary, not a foreground service, and not media style. The Place posting would be forwarded. Which Life360 kinds are ongoing (location sharing) is not in this shade; the batch's Life360 posting is the next observation.

### NT-G4 — Content and mapping

`MessagingStyle`: the newest message only (last in `getMessages()`), its sender display name and text, `isGroupConversation`, conversation title. No older messages. [EXT](https://developer.android.com/reference/android/app/Notification.MessagingStyle). Life360 is this style, so its title (length 6) and text (length 18) are not what we send if a message is present.

Otherwise `android.bigText` wins over `android.text` when big text is present; `android.title` is the title. The companion's own posting is excluded before this mapping.

Own message: if the newest message's sender is null or equal to `MessagingStyle.getUser()` / `EXTRA_MESSAGING_PERSON`, do not forward. Events are inbound only.

Excluded always: `FLAG_GROUP_SUMMARY`, `FLAG_ONGOING_EVENT`, foreground-service postings, media style, the companion package, the Messages packages above.

Masking: `Mask.kind` (`Mask.kt` lines 29–50) runs on the message text and the conversation title together. Any hit sets `mask_kind` and both `text` and `conversation_title` are absent, not empty strings. `Mask.prepare` today returns an empty body for texts (line 69). Notification items do not use that empty string. The sender display name is kept and never logged. New samples: a voicemail transcript with a spoken six-digit code, a DM with a login link, a Life360 line with an address and a time that must stay plain, and a code that appears only in the title.

`posted_at_ms` is `postTime` (when the phone received the posting). The message's own timestamp is `newest_message_timestamp`, not `posted_at_ms`. This shade had `when` and no separate `postTime` label; the batch records both as numbers and the delta only.

Cancellation: a posting cancelled before admission sends nothing. A posting cancelled after the queue write still delivers. It is not one of the three delete exceptions. The build plan's "a cancelled notification → nothing sent" (Track 4 NT-G6, line 609) is read as "a cancel is not itself an event." Brian confirms that reading at the Phase 3 STOP.

### NT-G5 — Queue

One file, `notification-queue.json`, in app-private storage, written by temp-and-rename. It holds the masked items and the seen-identity hashes. `companion-state.json` holds no notification content. `v3`'s `save()` rewrites that file from known keys only (`CompanionEngine.kt` lines 943–964), so notification state does not live there.

Order: mask the full text and title, then truncate an unmasked text to 4,000 (`notification_text_chars`, contract lines 313–314) with `truncated: 1`, then temp-and-rename, then send. The seen hash is written in that same rename, not before it (G-ADMISSION).

Bounds: `notification_queue_items` 200 and `notification_queue_ms` 604,800,000 (contract lines 307–308). Overflow drops the oldest and increments `notification_queue_drops`. Age-out increments `notification_age_drops`. Delete only on a terminal ack (`stored`, `updated`, `duplicate`, `suppressed`, `rejected`) for that identity and revision. The seen hash stays.

In-flight window: 4, separate from the text window. The text window is hardcoded at 4 (`CompanionEngine.kt` lines 453–454 and 559). A shared window would let notifications stall texts. An unacked notification does not block the next notification or any text. Retry on connect and on each verified PC frame, same drain point as C11 (`CompanionEngine.kt` lines 281–282).

Crash points, one file, one rename:

| Point | Queue file | Seen | Next start |
|---|---|---|---|
| After mask, before rename | previous file | not added | sweep can admit if still showing |
| Rename done, before send | item present, seen present | present | deliver once |
| Sent, no ack | item present | present | fresh envelope, `duplicate`, then delete |
| Ack received, delete rename not done | item still present | present | resend, `duplicate`, delete once |

An acknowledged posting that is still showing is not queued again: the identity stays in the seen set. Seen entries are hashes, kept at least `notification_queue_ms`, with a count cap (propose 2,000, the contract's `deleted_seen_limit`). Evicting an identity that is still showing can re-admit it. The PC's equal revision returns `duplicate` (`proactive_store.py` lines 1103–1105). That is the backstop, tested.

Change of PC identity: **carry** every unacked queued item. `DeliveryBook.open` seeds a new PC with texts from the provider window only (`CompanionEngine.kt` lines 334–347, `DeliveryBook.kt` lines 36–54). There is no notification provider to replay. A new PC gets no 7-day notification window. An acknowledged item is already deleted and is gone. Dropping the queue on a re-pair would be a silent loss.

### NT-G6 — Identity

`notification_key`: recommend the SHA-256 hex of `StatusBarNotification.key`, 64 characters, no U+001F. The PC rejects any identity field containing U+001F (`proactive_store.py` lines 974–975, `wire.py` lines 147 area via the separator check) and a rejected item that cannot be fixed would sit forever. The raw key can contain an app-chosen tag. The hash is content-free. The Life360 key was hashed for the probe (`6c8a6eae55a6` prefix) and not stored.

`newest_message_timestamp`: the newest `MessagingStyle` message's timestamp when that style is present. Otherwise `when`. A new message timestamp is a new item. The same timestamp reposted is `duplicate`. A silent repost that changes neither timestamp nor text does not enqueue again. This shade cannot show what Life360 changes on an update. If the batch shows the text length change while `when` and the message timestamp stay, revision is the wrong tool and the rule comes back to Brian. Until then revision is **1** always. No notification is `incomplete`. `completeness` is `complete`.

### NT-G7 — Read

Same allowlist, same exclusions, same message-only filter, same mapping, same masking as events. From `getActiveNotifications()` at that moment. Newest first. Contract caps: 50 items, 64,000 characters, 4,000 per item (`phone_protocol.json` lines 313–317), or less if the request asks. `capped` when either bound stops the list. Optional `package` filter (Appendix B §6, lines 972–975). The v3 request has no `package` field (contract lines 149–157) and the v3 result has no `items` (lines 159–165).

Partial wake lock `zola:read`, 20 seconds, acquired at accept and released on every path, matching history (`CompanionEngine.kt` lines 568–570 and 629–630). Writes nothing to the queue, the state file, or the log except a count. If the listener is not bound, status `listener_unbound`, not an empty list.

### NT-G8 — Health and hello

`hello` today announces only `receive_messages`, `read_history`, `read_code`, `device_health`, `keepalive` and sends `notification_queue_depth` 0 (`CompanionEngine.kt` lines 680–690). v4 adds `receive_notifications` and `read_notifications` once they exist, and the real queue depth.

`device.health` today is service state, permissions, battery, and the text counts (`CompanionEngine.kt` lines 694–702 and 175–186). v4 adds, sent on connect and on change: `listener_permission`, `listener_bound`, `allowlist_packages`, `notification_queue_depth`, `notification_queue_oldest_age_ms`, `notification_queue_drops`, `notification_age_drops`, `notification_filtered`, `allowlist_removed`, `notification_rejected`, `listener_gap_count`, `listener_gap_ms_total`, `last_gap_start_ms`, `last_gap_end_ms`, `last_gap_inferred` (1 when the gap is inferred from process death). A gap is listener unbound, or access missing while the allowlist is not empty. A gap while the process was dead is inferred at the next start from the last alive time and marked inferred.

The setup screen shows granted, bound, allowlist count, queue depth, and drops. Counts and states only.

The Companion row already has `DEGRADED` as Attention on the watcher row and no Companion degraded state (`SystemsCopy.cs` lines 20–24, 62, 73–80, 188–222). Connected is a null state word. Phase 3 proposes the words; the colours come from this file. Label wording is Brian's.

### NT-G9 — PC side as shipped

`_ingest` (`runtime.py` lines 590–654) for a notification requires `package`, `notification_key`, `newest_message_timestamp`, `completeness` of `complete` or `exhausted`, integer `revision`, integer `posted_at_ms`. Text is `body` or `text`. It does not pass `app_label` or `conversation_title` into `ingest_phone_item`, and that function has no such parameters (lines 890–916). Stored columns include package only inside the idempotency key (`_phone_identity`), plus `sender_display_name`, body, `is_group`, `mask_kind`, `truncated`, `ranking_source` `code`, `judgment` null (`proactive_store.py` lines 1036–1090). There is no package column and no conversation-title column.

Duplicate: equal revision → `duplicate` (lines 1103–1105). Higher → `updated` (lines 1106–1157). Lower → store result `ignored`, and the ack word becomes `duplicate` (`runtime.py` line 645).

`PHONE_CONVERSATION_HOLD` is `sms`, `mms`, `notif` (`proactive_store.py` lines 70–71). `claim_speech` returns `phone_deferred` for every one of those sources (lines 2026–2028). `claim_next_rank` selects `source = 'gmail'` only (lines 1632–1637). Phone rows are inserted already `ranked` with `ranking_source` `code`.

`loops.evaluate` is `loop_match.evaluate` (`loops.py` line 26). It does not look at `source` except to pick a calendar time (`loop_match.py` lines 29–32, 35–69). A lone `sender_is` predicate would match a notification view with the same hash. The compiler never emits that predicate (`loops.py` lines 110–170): every predicate is `brian_confirms`, or an `all` that includes `gmail_thread` or `calendar_event`. The view `_evaluate_item` passes has `source`, `message_id`, `sender_address_hash`, and `detected_at` (`runtime.py` lines 716–721). It has no `thread_id`, no `event_id`, and no `internal_date`, so `gmail_thread`, `calendar_event`, and `after` are false. The nine live loops are all `closed` `reply` predicates (`all` + `gmail_thread` + `sender_is` + `after`; one also has `not_source`). `list_open_loop_predicates` reads `status = 'open'` only (lines 3401–3410), so none of them are evaluated. A notification ingested today cannot set `loop_matched` against any predicate this compiler stores, and speech would refuse it anyway. This is not a block. The Phase 4 test shows a `notif` view does not match a compiled predicate and `claim_speech` returns `phone_deferred`, without editing `loops.py`.

Track 5 RD-G2 (build plan lines 682–685) wants the notification's app and display name. Display name is stored. App label and package are not columns, and conversation title is not stored. A group notification later cannot be described by its group name from the store. Record only. No schema change in this track. RD-G3b (lines 691–694) reads `read_notifications` live and must not answer from stored rows.

`read_code` addresses `provider_id` and `kind` (contract lines 167–174). It stays texts-only. A masked notification code is `mask_kind` on the item. Phase 3 asks Brian to confirm it is not readable through `read_code` in Phase 10.

### NT-G10 — Contract v4 and rollout

v4, `supported_versions: [4]`. `notifications.event` gains `text`, `mask_kind`, `truncated`, `completeness`, and `event_required_notification`: `package`, `notification_key`, `newest_message_timestamp`, `revision`, `completeness`, `is_group`, `posted_at_ms`, `truncated`. `text` is absent when `mask_kind` is set. `notifications.ack` unchanged. `notifications.read.request` gains optional `package`. `notifications.read.result` gains `items`, `item_fields` (the event fields plus `capped` on the result), and status `listener_unbound`. `device.health` gains the NT-G8 fields. New reason `listener_unbound` on the read result, not a frame rejection. Vectors: masked and unmasked notification events (emoji and non-ASCII on the unmasked one), a notification ack, a read result at the cap and over the cap, and one PC-signed refusal per §3 step. Kotlin and Python read the same file. Track 3 text vectors still pass.

A v4 phone against a v3 PC is refused `version` with no reply (`wire.py` lines 180–183, `supported_versions` contract line 415). Texts stay pending on the phone. They send after the phone is paired to a v4 PC. No text is dropped for the version refusal.

Rollback: build the Track 3 APK from `main` `f12c2717` into the scratch folder before the first v4 install. Same debug key. Record SHA-256 and `versionCode` 1. The v4 debug APK uses a higher `versionCode`. Notification state is files the v3 build never opens, so a v3 `load()` of `companion-state.json` cannot see it, and a v3 `save()` cannot erase it. A unit test loads a state document that contains extra keys and still restores the text cursors and slots. `adb install -r -d` of the rollback build is the downgrade path. If the bench fails and cannot be fixed in the session, Brian chooses rollback (re-pair to live; same `pc_id`, so acked texts are not resent) or staying on scratch.

Order, for approval at the Phase 3 STOP, before any install:

1. Rollback APK built and hashed. Scratch v4 `zola-phone` up on 47822. Live v3 stays up.
2. Install v4. The live log may show `version` refusals until re-pair. Record that count and the phone's pending count. Brian re-pairs to scratch immediately.
3. Bench and smoke against scratch.
4. Part B: client closed, live mirror to v4, client launched from the worktree, phone re-paired to the live `pc_id`. The version-mismatch window is the time between the live process becoming v4 and the phone's next hello, or the reverse if the phone moves first. The approved order keeps that window to the re-pair step. Pending texts deliver to the live `pc_id` under the NT-G11 rule.

### NT-G11 — Smoke layout

Recommend **(a)**. Layout (b) would move the live `zola-phone` to v4 before the event cells, which is the live mirror early, and a failure then needs the v3 plugin files restored. Layout (a) leaves live v3 untouched until Part B.

Brian re-pairs to scratch before N1 and back to live after C3 and C6. While the phone is on scratch, the live Companion row is Offline or Reconnecting rather than Connected, because the live process has no socket. Real texts during the smoke are admitted to the scratch `pc_id` and stored in the scratch database. They are also delivered to the live store after the re-pair to the live `pc_id`: `scanAboveCursors` reads the current PC's cursor (`CompanionEngine.kt` lines 137–149), `onOpen` calls it (line 200), and the live cursor is not advanced while `pcId` is the scratch id. The `pcs` map keeps both (`load`/`save` lines 906–964). That is the tested rule. N7 uses the scratch fault launcher. N12 uses the scratch launch secret. The live client and the Gmail watcher stay up.

### NT-G12 — N9 build

A build type `n9` with its own source set that overrides only the queue-item constant to 3. It is not a runtime flag and not a value in `companion-state.json`. Installed for N9 only, then the normal debug build is reinstalled. `versionCode` stays above the rollback build. `MY_PACKAGE_REPLACED` starts the service. App data and the listener grant are expected to remain; N10 checks the grant.

### Phase 2 gap

Brian's batch, still needed before Phase 2 can close. One of each, marked `ZP10-` and neutral, or a note that he cannot produce it:

1. A Messenger 1:1 DM.
2. A Messenger group DM.
3. An Instagram 1:1 DM.
4. An Instagram group DM.
5. An Instagram like or follow.
6. A Life360 notification (an update of one already showing, if he can).
7. A Visual Voicemail notification.

Cursor does not post, cancel, or tap anything. After they are on the screen, the same redacted probe records package, key hash, category, flags, style, extras key names, lengths, `when`, `postTime`, group-key presence, and channel id.

### Brian's clarification (verbatim, 2026-10-28)

Option A. Posting items 1, 3, 5 and 6 now. Add 2, 4, 7 if they are present. Mark any he could not produce as unobserved and fail-closed, to be confirmed at the bench.

Life360 alerts are arrival and departure notices, not messaging, even though the app uses `MessagingStyle`. Mapping by app: the chat rules (newest message, its sender, own-message skip, message-only filter) apply only to Messenger and Instagram. Life360 and Visual Voicemail are forwarded as plain notifications from title and text, whatever their template, with no own-message or message-only filter. For Life360, record what changes when a second arrival or departure posts (same key or a new one, `when`, post time, message count, text length), so the identity rule gives one item per event.

### Second probe — blocked

The probe was run again after that note. The raw dump was not written and not printed. About 2,141,626 characters. Four `tickerText` lines were not a redaction token and not a length wrapper. They were not printed. Each is 11 characters. Letter and space counts only:

| Package | Letters | Spaces |
|---|---|---|
| `com.google.android.gm` | 7 | 1 |
| `com.google.android.apps.messaging` | 7 | 0 |
| `android` | 6 | 2 |
| `com.amazon.mShop.android.shopping` | 7 | 0 |

No allowlisted record was read after that. Items 1–7 are unobserved on this pass. The first probe's Life360 and companion metadata still stands.

Brian (verbatim, 2026-10-28): "proceed to phase 3 (Option A). Do not probe the shade again." The shade probe is dropped for the rest of the track. The reason is the finding above: the default redacted `dumpsys notification` on this phone includes ticker text (four lines, packages Gmail, Google Messages, `android`, and Amazon shopping). No further shade probe will be run.

## Phase 3 — Proposal

No source files are modified in this phase. Items 2, 4, and 7 were not observed. Items 1, 3, 5, and 6 were posted but not read, because the probe stopped first. Until bench step B0, the Messenger and Instagram filter fails closed. Life360 and Visual Voicemail follow Brian's mapping clarification below from the first build.

### Brian's mapping (verbatim, carried into this proposal)

Life360 alerts are arrival and departure notices, not messaging, even though the app uses `MessagingStyle`. The chat rules (newest message, its sender, own-message skip, message-only filter) apply only to Messenger and Instagram. Life360 and Visual Voicemail are forwarded as plain notifications from title and text, whatever their template, with no own-message filter and no message-only filter. B0 records what changes when a second Life360 arrival or departure posts, so the identity rule gives one item per event.

### Listener, threading, catch-up

One new service, `NotificationListener`, in the companion process. Manifest: `exported="false"`, `android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"`, intent action `android.service.notification.NotificationListenerService`. No filter meta-data. No new library and no new `uses-permission`. Notification access is the system setting, not a runtime permission.

The listener does not construct an engine. It posts onto `CompanionService`'s single worker. `boot()` still loads once (`CompanionEngine.kt` lines 50–56). If the engine is not up, the listener calls `startForegroundService`. This app is on the device-idle whitelist, which is the battery-unrestricted exemption. If that start throws, the listener logs a gap and does not build a second engine. The sweep after `boot()` admits whatever is still showing.

Catch-up, recommended: **(a)**. Every `onListenerConnected` sweeps `getActiveNotifications()`. The first bind after install, and the first sweep after an app is added, marks what is already showing as seen and sends nothing. Later sweeps admit only allowlisted postings that are still showing and not seen. A posting dismissed during a gap is not recovered. `onListenerDisconnected` logs and calls `requestRebind`. `BootReceiver` (`BOOT_COMPLETED`, `MY_PACKAGE_REPLACED`) starts the foreground service and calls `requestRebind`.

The setup section on `PairingActivity` opens `ACTION_NOTIFICATION_LISTENER_DETAIL_SETTINGS` with the component extra, and falls back to the listener list. Restricted settings, if Samsung shows them, are Brian's step. The screen shows granted, bound, allowlist count, queue depth, and drops.

### Allowlist

A section of the setup screen. Launchable apps, labels from the package manager, starts empty. The companion package is not listed. `com.google.android.apps.messaging` and `com.samsung.android.messaging` are listed and not selectable. Visual Voicemail on this phone is `com.tmobile.vvm.application` (`com.samsung.vvm` is absent). Stored as package names in `notification-queue.json`, not in `companion-state.json`. A change applies to the next event and the next read.

Removal, recommended: **drop** queued items for that package that have not been sent, count `allowlist_removed`, log the package and the count. An item already sent still waits for its terminal ack. This is the third named exception, and it is tested as one.

### Filter and mapping

**Messenger (`com.facebook.orca`) and Instagram (`com.instagram.android`) only.** Forward only when the template is `MessagingStyle` and the category is `CATEGORY_MESSAGE`. Anything else, including a missing category, is dropped and `notification_filtered` increments. That is fail-closed until B0. From a forwarded posting: the newest `MessagingStyle` message's sender and text, `isGroupConversation`, and the conversation title. No older messages. If the newest sender is null or equal to the device user (`MessagingStyle.getUser()`), do not forward.

**Life360 and Visual Voicemail.** Plain title and text, whatever the template. `android.bigText` wins over `android.text` when big text is present. No own-message skip. No message-only filter. Still excluded, as visibility rather than as a chat filter: `FLAG_GROUP_SUMMARY`, `FLAG_ONGOING_EVENT`, foreground-service postings, and media style. Brian confirms that ongoing exclusion.

**Everyone.** Also excluded: the companion package, and the two Messages packages. `posted_at_ms` is `postTime`, or `when` when `postTime` is 0. `completeness` is always `complete`. Revision is 1 unless B0 forces a change.

Masking runs on the text and the conversation title together before any truncate and before the queue write. A hit sets `mask_kind` and both fields are absent. The sender display name is kept and never logged. Samples added to the mask tests: a voicemail line with a spoken six-digit code, a DM with a login link, a Life360 line with an address and a time that stays plain, a code only in the title, and a code past 4,000 characters.

### Shape log

For every allowlisted posting, including ones the filter drops, the listener writes one metadata line through the existing phone log. The only strings are the identifiers named here. No title, text, sender name, conversation title, ticker, or link.

`shape` fields: `package`, `key_hash` (16 hex characters of SHA-256 of `StatusBarNotification.key`), `template` (class name, or `none`), `category` (or `none`), `channel_id` (or `none`), `flags` (the flag names), `extras` (the extras key names present), `message_count` (integer; 0 when there is no `MessagingStyle`), `newest_is_user` (0/1; 0 when there is no newest message), `when_ms`, `post_ms`, `title_len`, `text_len`, `big_len`, `title_len` of the conversation title as `conversation_len`. A dropped posting adds `result=filtered` or `result=excluded` or `result=own`. An admitted posting adds `result=admitted`.

### Queue, identity, reads, health

`notification-queue.json` in app-private storage, temp-and-rename. It holds masked items and seen hashes. `companion-state.json` is unchanged in shape, so the Track 3 loader still reads it. v3 `save()` cannot delete a file it does not open.

Admit order: mask, truncate an unmasked text to 4,000 with `truncated: 1`, then one rename that adds the item and the seen hash together, then send. Bounds 200 and 7 days from the contract. Overflow drops the oldest (`notification_queue_drops`). Age-out is `notification_age_drops`. Delete only on a terminal ack for that identity and revision. The seen hash stays. Seen hashes are kept at least 7 days, cap 2,000. Eviction can re-admit a posting that is still showing; the PC returns `duplicate`.

Notification in-flight window: 4, separate from the text window (`CompanionEngine.kt` lines 453–454). An unacked notification does not stall a later notification or a text. Drain on connect and on each verified PC frame.

Change of PC, recommended: **carry** every unacked queued item. A new `pc_id` gets no notification history beyond that. Acknowledged items are already deleted.

Identity: `notification_key` is the SHA-256 hex of `StatusBarNotification.key` (64 hex characters on the wire; the shape log prints 16). `newest_message_timestamp` is `when`, as a decimal string, for every app including Messenger. A new `when` is a new item. The same key and the same `when` is `duplicate` at revision 1. B0 is allowed to change the Life360 timestamp source if a second arrival keeps the same key and the same `when`. Chat items use the same identity fields; the newest message's own timestamp is not the identity until B0 shows that `when` collides two different messages.

Cancellation: nothing is sent for a posting cancelled before the queue rename. A posting cancelled after that rename is still delivered.

Reads use the same allowlist, exclusions, per-app mapping, and masking. Newest first. Caps 50 / 64,000 / 4,000, or less if asked, with `capped`. Optional package filter. Wake lock `zola:read`, 20 seconds, released on every path. Listener not bound: status `listener_unbound`, not an empty list. Nothing written to the queue or the state file.

`hello` adds `receive_notifications` and `read_notifications` and the real queue depth. `device.health` adds `listener_permission`, `listener_bound`, `allowlist_packages` (package names), `notification_queue_depth`, `notification_queue_oldest_age_ms`, `notification_queue_drops`, `notification_age_drops`, `notification_filtered`, `allowlist_removed`, `notification_rejected`, `listener_gap_count`, `listener_gap_ms_total`, `last_gap_start_ms`, `last_gap_end_ms`, `last_gap_inferred`. Sent on connect and on change. A gap is unbound, or access missing while the allowlist is not empty. Process death is inferred from the last alive time and marked inferred.

### PC findings

`loops.evaluate` cannot match a notification against any predicate the compiler stores, and `claim_speech` returns `phone_deferred` for `notif` (`proactive_store.py` lines 70–71 and 2026–2028). No `loops.py` change. A test locks that.

`_ingest` already requires `completeness` and reads `body` or `text`. It does not store `app_label` or `conversation_title`. Track 5 RD-G2 will not have the app label or the group title from the store. Display name is stored. No schema change here.

`read_code` stays texts-only. A masked notification code is reported as masked. It is not readable through `read_code` in Phase 10. Brian confirms that.

### Contract v4

`contract_version` 4, `supported_versions: [4]`. `notifications.event` gains `text`, `mask_kind`, `truncated`, `completeness`. New `event_required_notification`: `package`, `notification_key`, `newest_message_timestamp`, `revision`, `completeness`, `is_group`, `posted_at_ms`, `truncated`. When `mask_kind` is set, `text` and `conversation_title` are absent. `notifications.ack` unchanged. `notifications.read.request` gains optional `package`. `notifications.read.result` gains `items`, `item_fields`, `capped`, and status `listener_unbound`. `device.health` gains the fields listed above. Vectors: masked and unmasked notification events (the unmasked one has emoji and non-ASCII text), a notification ack, a read result at the cap and over the cap, and one PC-signed refusal per §3 step. Kotlin and Python read one file. Text vectors still pass.

### PC changes (G-SCOPE)

- **(a)** Needed. `zola-phone` accepts version 4 only and ingests the v4 notification fields. It still does not store `app_label` or `conversation_title`.
- **(b)** Needed. `notifications.read.result` items are re-checked against the §7a caps before they are returned. Their content is not stored and not logged.
- **(c)** Needed. `zola_phone.hello` and `zola_phone.health` gain the integer listener and queue fields, plus `allowlist_count`. The log does not repeat package names or any text.
- **(d)** Required. `status()` keeps the last listener and queue integers. The client reads them with `link_state`. The Companion row uses the existing levels in `SystemsCopy.cs`. Connected stays the healthy dot (`MainWindow.xaml.cs` lines 943–949: a null state shows the dot). `DEGRADED` already exists (line 24) and is Attention, which paints `ZolaAlertGlowBrush`. `ZolaErrorBrush` is Down. Recommended word: **DEGRADED**, colour **Attention / `ZolaAlertGlowBrush`**. Show it only when the link would otherwise be Connected, the allowlist count is greater than 0, and `listener_permission` is 0 or `listener_bound` is 0. An empty allowlist does not degrade the row. Offline, Reconnecting, Not paired, Failing, Restarting, and Stopped keep their current words and colours. The latch still wins.
- **(e)** Needed, scratch only, never committed. The side-by-side launcher and the fault launcher, as in Track 3.

### Rollout, smoke, N9

Rollout, for approval before any install:

1. Build the Track 3 APK from `main` `f12c2717` into the scratch folder. Record its SHA-256 and `versionCode` 1.
2. Start scratch v4 `zola-phone` on 47822. Live v3 stays up.
3. Install the v4 APK (`versionCode` higher, same debug key). Record live `version` refusals and the phone's pending count. Brian re-pairs to scratch immediately.
4. Bench, including B0, then smoke, against scratch.
5. Part B moves the live mirror to v4 and the phone back to the live `pc_id` together.

A unit test loads a state document that contains extra keys and still restores text cursors and slots. Notification state is not in that file. If a cell cannot be fixed in the session, Brian chooses rollback (`install -r -d` of the scratch rollback build, re-pair to live) or staying on scratch.

Smoke layout, recommended: **(a)**. Real texts admitted while the phone is paired to scratch are delivered to the live `pc_id` on re-pair, because `scanAboveCursors` uses the current PC's cursor (`CompanionEngine.kt` lines 137–149 and 200) and the live cursor is not advanced meanwhile. That rule gets an engine test.

N9: build type `n9`, source set overrides the queue-item constant to 3. Not a runtime flag. Reinstall the normal debug build immediately after. N10 checks that the listener grant survived.

### Tests

Kotlin, engine-level through the ports, `isReturnDefaultValues = false`. Track 3's 65 stay green. New groups: contract vectors and canonical bytes; PC-direction refusals; Messenger/Instagram newest-sender mapping; own message skipped; title/text for Life360 even when the template is `MessagingStyle`; group summary, ongoing, foreground-service, media, own package, and Messages packages produce nothing; a non-message Instagram or Messenger posting is filtered and counted; empty allowlist produces nothing; mask samples including title-only and mask-before-truncate; a sentinel code never appears in a frame, a log line, the state file, or the queue file; masked items omit `text` and `conversation_title`; shape lines contain no title, text, or sender; queue survival across a new engine; overflow; age-out; duplicate; new `when` is a new item; same `when` is `duplicate`; cancel after admit still delivers; every ack word deletes; an unacked item does not stall the next; cold start drains from the file; acks from another thread interleaved with an alarm, a service start, a listener rebind, and an allowlist change deliver each item once; carry across a new `pc_id`; each crash point in the Phase 2 table; an acknowledged posting that is still showing is not queued again; seen-set eviction re-admits and the PC returns `duplicate`; gap records for unbind, access loss, and inferred process death; allowlist add is immediate; removal drops and counts; Messages cannot be selected; health carries package names only; baseline on first bind and on add; reads, caps, package filter, wake lock released on every path, `listener_unbound`, nothing written; health sent on change; texts still drain while notifications are queued; v3 loader ignores extra keys.

Python: five suites at or above 357 / 134 / 44 / 8 / 40. v4 accept, read-result cap and "not stored", health count log, fake phone sends v4 notifications and answers reads, a `notif` row does not match a compiled watch and `claim_speech` returns `phone_deferred`.

Client: one check row for Connected with an empty allowlist, one for Connected with a bound listener and a non-empty allowlist, one for DEGRADED when access is missing, one for DEGRADED when the listener is unbound, and one that an empty allowlist is not DEGRADED while unbound. Every existing row stays.

### Bench and smoke

B0 is before B2. The filter on that build is the fail-closed rule above.

| Step | Check |
|---|---|
| B1 | Listener bound and granted in `device.health` and the PC count log; `hello` announces both notification capabilities |
| B0 | Brian posts a Messenger 1:1, a Messenger group DM, an Instagram 1:1, an Instagram group DM, an Instagram like or follow, a Life360 alert, a second Life360 arrival or departure, and a voicemail if he can. Cursor reads shape lines only. Confirm the message-only filter, the Messenger/Instagram mapping, and the Life360 identity rule (same key or a new one, `when`, post time, message count, text lengths). Any item he cannot produce is unobserved and stays fail-closed. If a rule is wrong, a failing test is written first, then reinstall, then B0 again |
| B2 | One `ZP10-` Instagram DM stored once; sender is the person; text present; ack received; queue empty |
| B3 | One Instagram like or follow stores nothing; `notification_filtered` increases by 1 |
| B4 | A text is stored as a text only; no `notif` row from Messages |
| B5 | `read_notifications` returns only allowlisted postings, masked and bounded; scratch store row count unchanged |
| B6 | Process kill with one DM queued and `zola-phone` down; listener rebounds without Brian; the DM is delivered once after `zola-phone` returns |
| B7 | Phone log, logcat, and the state file: 0 hits for the scripted text and the sender name; queue file empty after the acks |
| B8 | Every PC log: 0 hits for the same |

Smoke cells N1–N12, then C3 and C6, then Part B, as in the prompt, with the P10-D16 amendment: N1 is an Instagram DM plus an Instagram like, and N4 is an Instagram group. N10's Companion-row check is Part B step 6, against the live client. Part B step 6: Connected, then DEGRADED with access off, then Connected with access on, matching `device.health`.

### Risks

The chat filter is unobserved until B0, so the first install can drop a real DM that does not carry both `MessagingStyle` and `CATEGORY_MESSAGE`. B0 is the correction point, with a failing test first. Life360 identity can collapse two alerts if they share a key and `when`. The listener may fail to start the foreground service despite the battery exemption; that is a gap, not a second engine. Samsung may require restricted settings. A v4 install against live v3 holds texts as pending until the scratch re-pair.

### Verdicts

1. Catch-up (a) approved: sweep on connect; baseline on first bind and on allowlist add.
2. Allowlist removal approved, plus: an item already sent and awaiting ack for a removed app is retired too. It stops retransmitting on reconnect, is deleted from the queue, counts in `allowlist_removed`, and a late ack for it is ignored.
3. Messenger/Instagram filter approved. Fail closed until B0; B0 may loosen it.
4. Life360 and Visual Voicemail approved, including the ongoing exclusion. Text is the title and the text together (title first, one line break). `sender_display_name` and `conversation_title` are absent. The mask decision runs over that combined text.
5. For Messenger and Instagram, the identity timestamp is the newest MessagingStyle message’s own timestamp. Life360 and Visual Voicemail use `when`, subject to B0.
6–8. Approved.
9. Companion word is **DEGRADED**.
10. Smoke layout (a) approved.
11. A masked notification code is reported as masked and is not readable through `read_code` in Phase 10.
12. Contract v4, no new dependency, and PC candidates (a)–(e) approved. Rollout amended: no v4 frame may reach the live v3 `zola-phone`. Shape log: `channel_id` is a 16-hex SHA-256 prefix; `extras` lists only recognized Android `EXTRA_*` key names, plus `extras_other=<count>`.

B0, before B2: Messenger and Instagram stay on the strict filter when a DM shape was not observed, and that rule is recorded unverified. Life360 and Visual Voicemail stay forwarding-on from the first build; a missing observation marks that rule unverified for N2 or N11, not disabled. For each scripted `ZP10-` item, the stored row’s sender and text are compared to what was sent, by hash.

The live `fake_phone.py` stays untouched in Part B. That is a residual. The worktree copy answers `notifications.read.request`.

## Phase 4 — implementation, not the bench

Contract is 4. Notification state is `notification-queue.json`. `companion-state.json` still holds the text slots, and extra keys in it are ignored on load. Hello carries `receive_notifications` and `read_notifications` plus the listener and queue counts. `status()` returns those counts. A notification read result is capped and is not written to the store or the log. The Companion row shows DEGRADED only when the link would otherwise be Connected, the allowlist count is greater than 0, and listener permission or listener bound is 0.

Scratch launcher: `C:\Users\test\Dev\zola-spikes\p10-notify\start-scratch.ps1`. Home `hermes-home`, port 47822, pipe `\\.\pipe\ZolaPhoneScratch`, mutex `Local\ZolaPhoneScratch`. Not committed.

### Tests

| Suite | Result |
|---|---|
| Kotlin `testDebugUnitTest` | BUILD SUCCESSFUL. CompanionRulesTest 12, EngineFlowTest 39, NoticeFlowTest 22, Phase4Test 14. **87**, 0 failures |
| `zola_workspace` | 357 OK |
| `zola_memory` | 134 OK |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |
| `zola_phone` | 42 OK |
| Client build | 0 warnings, 0 errors |
| `Zola.Client.Checks` | exit 0. Phone rows **12/12**. The new row is the DEGRADED allowlist case |

APK check on the v4 build: no `google-services` entry, no `org.json` archive, no private key, no `phone_test_keys`. `classes3.dex` references the platform `org.json` class.

### Builds

| APK | versionCode | SHA-256 |
|---|---|---|
| Rollback, from primary `main` `f12c2717` | 1 (`1.0.0`) | `853004122bc2ee5845c93063ed48560e7449ef212a28e2fdd08e6195017e9733` |
| v4 debug, first install | 2 (`1.1.0`) | `22ad4c829af91cd605a1669da91d46adcc8997a71adbbbcec0d80d5995f9cd9e` |
| v4 debug, queries fix | 3 (`1.1.0`) | `84cb5c1b0736f0fadc0d5d046bd8ca9bb5ac3de78c22933cfa964f5c82f49612` |
| v4 debug, row labels | 4 (`1.1.0`) | `efd404d805db60b37a5715b652da854092ce0f25d5531dd6b9da8b9bc2e9be66` |
| v4 debug, installed | 5 (`1.1.0`) | `38f1a9df0c9bd08e6b84b7e06d08ec64cb3d6bc1b97169a9caa551325b9d0ec0` |
| v4 debug, installed | 6 (`1.1.0`) | `33eb6c86d8345ad27e07d6e8b3ef8c29e2b9da0b6df681cdb19934a90ae07248` |

The rollback APK and the versionCode 2 APK are in the scratch folder. VersionCode 6 is the installed debug build. Primary `main` has no source change.

### Install gate

No `Zola.Client` process and no live `zola-phone` process. Nothing was listening on 47821. Scratch v4 is listening on `100.102.206.71:47822` only. Its log is one line: `zola_phone.start forbidden=-`. No phone frame has reached it.

`adb install -r` of the v4 APK succeeded. The installed package is versionCode 2, versionName 1.1.0. `SCHEDULE_EXACT_ALARM` is `allow`. The battery whitelist still contains `com.beebo.zola.companion`. `install.json` is still 115 bytes, dated 2026-10-20, and its `device_id` is 32 characters. `companion-state.json` is still present. `notification-queue.json` exists and has 0 items.

The saved address port is 47821. After the install the phone log has 7 `disconnect reason=failure` lines and 0 `reason=version` lines (counted from timestamp `1793217000000`). For the current pc, 4 text slots are in flight and 11 are waiting. The phone is backing off. The firewall rule “Zola phone intake scratch” is not installed: creating it returned Access is denied.

### Bench

B1 passed. B0 is not started. The allowlist read-back matches the bench set.

| Step | Result |
|---|---|
| B1 | Pass. Paired to scratch at 13:20:15. `hello` logged `capabilities=7` (the seven names include `receive_notifications` and `read_notifications`). `device.health` and the queue file: `listener_permission=1`, `listener_bound=1`. The companion listener is in `enabled_notification_listeners`. Count log matches. Allowlist at that moment was 0 |
| B0 | Instagram DMs admitted. Instagram non-messages filtered. Voicemail admitted. Messenger excluded (P10-D16 amendment). Life360 observed before Phase 4 STOP: two alert keys, and one key with a new `when` as a second item. See B0 section |
| B2 | Pass. Instagram DM `ZP10-B2-IG` (body hash match). Shape `MessagingStyle`/`msg`, admitted once then duplicate. Store: one `notif` row, sender present, `is_group=0`. Ack `stored`. Queue depth 0 |
| B3 | Pass. Instagram non-message shape `other`/`none`, result `filtered`. `notification_filtered` 12→14 (two filtered posts of the same like). No store row for that body |
| B4 | Pass. SMS `ZP10-B4-SMS` stored as `sms` once. Messages package `notif` rows in the store: 0 |
| B5 | Pass. `read_notifications` status ok, 2 Life360 items only, no Messages/companion. Store row count unchanged at 819 |
| B6 | Pass. Scratch stopped; DM `ZP10-B6-IG` queued (depth 1). `run-as kill -9` ended pid 20606; process rebounded to 28301 with listener still granted/bound and the item still queued. Scratch restarted; one `notif` `stored` accept; store hit count 1; queue empty |
| B7 | Pass. Phone `companion.log` (+ backups), logcat, `companion-state.json`, and `notification-queue.json`: 0 hits for the three scripted bodies and the Instagram sender display name. Queue items 0 |
| B8 | Pass. Scratch `zola_phone.log`: 0 hits for the same strings |

### Allowlist visibility

Cause confirmed. The versionCode 2 manifest had no `<queries>` element, and the installed package's queries sections were empty. `targetSdk` 36, so `queryIntentActivities(ACTION_MAIN, CATEGORY_LAUNCHER)` returned only packages visible by default, which on this phone were system apps. `CompanionRulesTest.launcherVisibilityQueryIsDeclared` failed on that manifest, then passed after the edit. The fix is a `<queries>` intent for `android.intent.action.MAIN` / `android.intent.category.LAUNCHER`. `QUERY_ALL_PACKAGES` is not declared. Installed versionCode 3 dumpsys: `queriesIntents=[Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] }]`.

`adb install -r` of that APK succeeded twice (the second replace started the service via `MY_PACKAGE_REPLACED` so the engine loaded the queue). Pairing survived: saved address port `47822`, `install.json` device id SHA-256 `6a03b08eafb666106b5bb47633c821ee1ff09b8f3c066189f35d85c863f7041e`. Listener grant survived: `com.beebo.zola.companion/.NotificationListener` is still in `enabled_notification_listeners`, and after reconnect `listener_permission=1`, `listener_bound=1`. `SCHEDULE_EXACT_ALARM` is `allow`. Scratch log has `allowlist_count=4` and does not contain the four package names.

On the versionCode 3 screen, before the phone slept, the hierarchy listed `com.facebook.orca`, `com.instagram.android`, `com.life360.android.safetymapd`, and `com.tmobile.vvm.application` as enabled rows, plus other user apps (Slack, Airbnb, Amazon). `com.google.android.apps.messaging` and `com.samsung.android.messaging` were disabled, labeled `"<pkg> texts"`. A new dump is blocked: the screen is awake on the lock bouncer, and the pairing activity is underneath it.

Dialer and camera: the only writer is a tap on an allowlist row. Those two were visible system launcher apps. The queue file at 13:21:48 was exactly `com.samsung.android.dialer` and `com.sec.android.app.camera`. Scratch health went `allowlist_count` 0 at 13:20:15, 1 at 13:21:31, 2 at 13:21:34. The row label is set when the activity is created and does not change to "on" after a tap, so a selected row still looks unselected. Two later taps cleared them: count 1 at 13:24:25, 0 at 13:24:27. They are not in the queue now. The PC log stores the count only.

### Hands-off breach

**G-PHONE-HANDS-OFF** was broken before the stop. The session ran `check_allowlist_screen.py` and `select_allowlist.py`, and it took UI hierarchy dumps (`uiautomator dump`, `dumpsys activity top`). It also sent `input keyevent KEYCODE_WAKEUP`, `wm dismiss-keyguard`, and `cmd statusbar collapse` while the lock screen was up. The screen scan found Messenger, Instagram, and Life360 enabled and Messages disabled; Visual Voicemail was off that dump. Every tap missed. The select script was stopped after it missed Messenger. Those scripts did not change the stored allowlist. They have stopped. No further tap scripts, input, or hierarchy dumps.

### Allowlist row state

`CompanionRulesTest.rowStateFollowsTheStoredListAfterATapAndAfterReopen` failed on the old labels (`"<pkg> on"` / `"<pkg>"` / `"<pkg> texts"`) at `CompanionRulesTest.kt:212`, then passed. A row's text is `AllowlistRows.label` of the stored set: `"<pkg> selected"` or `"<pkg> not selected"`. A tap toggles that set and redraws every row immediately. `onResume` redraws from `notification-queue.json`, so reopening the screen matches the file. Messages rows stay disabled and show the application label plus `Texts already come from the message store`, not the package name. Installed versionCode was 4. `adb install -r` kept port `47822`, device id SHA-256 `6a03b08eafb666106b5bb47633c821ee1ff09b8f3c066189f35d85c863f7041e`, the listener component in `enabled_notification_listeners`, and the four-package allowlist above. VersionCode 5 replaces that single list with the three sections below.

### B0

Shape lines only, from `1793223578221` through the voicemail line. No Life360 line in the batch.

| Posting | Shape | Result |
|---|---|---|
| Messenger, two posts | same `key_hash=98034d247825ec2b`, `template=other`, `category=none`, `message_count=0`, `conversation_len=0`, `title_len=14`, `text_len=12`, distinct `when_ms` | both `filtered`. 1:1 and group were not distinguishable |
| Instagram DM | `MessagingStyle`, `category=msg`, `message_count=1`, `newest_is_user=0`, `key_hash=2353d4b9fa829a74`, `conversation_len=41`, `title_len=59`, `text_len=26` | `admitted` |
| Instagram DM | same template and category, `key_hash=ceeec33b95d77064`, `conversation_len=12`, `title_len=30`, `text_len=24` | `admitted`, then `duplicate` on the same `when_ms` |
| Instagram non-message | `template=other`, `category=none`, `message_count=0`, `title_len=16`, `text_len=15`, two keys | `filtered` |
| Instagram group summary | `GROUP_SUMMARY`, empty title and text | `excluded` |
| Visual Voicemail | `template=other`, `category=none`, `title_len=14`, `text_len=72`, `big_len=72`, `key_hash=e3276e80122ce868` | `admitted`. Its group summary was `excluded` |
| Life360 | later, before Phase 4 STOP | Two distinct alert keys admitted: `64a5d0004a9126c2` and `b4bad5c9267e65fa`. The second key also posted again with a new `when` (`…9211` then `…9695`, `message_count` 1→2), so one key with a new `when` is a second item. Ongoing FGS Life360 stays `excluded`. Forwarding stays on |

The Instagram message-only filter held. Messenger on this phone does not post `MessagingStyle` or category `msg`. The two posts shared `key_hash=98034d247825ec2b` and had no per-message timestamp (`message_count=0`), so a 1:1 and a group could not be told apart.

Brian’s decision, verbatim, amends P10-D16: “In reality, I don’t really use Messenger much. I’m good with excluding it altogether.”

The versionCode 5 plain-posting admission is reverted. Messenger, if selected again, uses the strict chat rule only (`MessagingStyle` plus `CATEGORY_MESSAGE`). `NoticeFlowTest.plainMessengerPostingWithTitleAndTextIsFiltered` failed at `NoticeFlowTest.kt:67` while that admission was still in place, then passed. A plain Messenger posting with a title and text is filtered and `notification_filtered` increases.

Bench and smoke cells that used Messenger move to Instagram. B2 is one Instagram DM. N1 is an Instagram DM plus an Instagram like. N4’s group sender check is an Instagram group.

Open question for lore closeout: Messenger support, if wanted later.

VersionCode 6 `adb install -r` succeeded on 2026-11-02. Pairing survived: port `47822`, device id SHA-256 `6a03b08eafb666106b5bb47633c821ee1ff09b8f3c066189f35d85c863f7041e`. The listener component is still in `enabled_notification_listeners`. Scratch `status()` from `device.health`: exactly `com.instagram.android`, `com.life360.android.safetymapd`, `com.tmobile.vvm.application`. `listener_permission=1`, `listener_bound=1`, link connected. At reconnect the queue depth was 67 and `notification_filtered` was 12.

### Phase 4 STOP

Bench B1–B8 complete on scratch. Life360 identity: two events used two keys; a later update on one of those keys used a new `when` and became a second item. Waiting for Brian before Phase 5.

### Life360 same-key second item (pre–Phase 5)

Key `b4bad5c9267e65fa`, first pair admitted at `when` `…9211` and `…9695`. Shape: both `title_len=5`, `text_len=12`. Store body hashes for those two stamps match. **Same content.** Proposed fix (not implemented): a repost on the same key with identical title and text is not a new item, even when `when` moves.

### Allowlist sections

`CompanionRulesTest.listMembershipFollowsTheStoredAllowlistAfterACheckAnUncheckAndAReopen` failed at `CompanionRulesTest.kt:228`, then passed. The screen is three checkbox lists. “Zola can see” is the stored allowlist, checked, alphabetical by application label. “Not shared” is every other launchable app, unchecked, alphabetical. “Never shared” is the two Messages packages, disabled, with the application label and `Texts already come from the message store`. A check or uncheck moves the app immediately. Reopening reads `notification-queue.json`. A Messages package in the stored set still stays in “Never shared”. Rows use the package-manager label.

VersionCode 5 `adb install -r` kept port `47822`, the same device id hash, `listener_permission=1`, `listener_bound=1`, and the same four packages. `device.health` order was `com.instagram.android`, `com.life360.android.safetymapd`, `com.tmobile.vvm.application`, `com.facebook.orca`. `NoticeFlowTest` 23 and `CompanionRulesTest` 15 passed.

## Phase 5 — fixes from Claude's review of the Phase 4 diff and bench

Applied F1–F9 in order. Behaviour changes used a failing test through the engine's real entry points first. No phone UI work. No lore edits except this progress doc (F2 discrepancies for closeout). Hands off the phone's UI.

### F1 — Production pipe and mutex overrides

`test_production_entry_does_not_read_scratch_pipe_or_mutex_env` failed while `__main__.py` read `ZOLA_PHONE_PIPE` / `ZOLA_PHONE_MUTEX`, then passed after revert to the Track 3 shape (contract `pipe_name`, fixed `Local\ZolaPhone`). `PhoneProcess.cs` and `App.xaml.cs` set neither. `ZOLA_PHONE_LISTEN_PORT` residual stays. Scratch names live only in `C:\Users\test\Dev\zola-spikes\p10-notify\run_scratch_phone.py` (hard-coded Scratch pipe/mutex), launched by `start-scratch.ps1`.

### F2 — Lore edit reverted

`PHASE10_BUILD_PLAN.md` was restored to `f12c2717` (no remaining diff). The 13 lines that had been changed:

- N1/N4 smoke cells: Messenger DM / group wording → Instagram-only, with a “Messenger DM removed 2026-10-28; P10-D16 amendment” note.
- P10-D16 amendment paragraph (Brian excluding Messenger; selectable but strict chat rule; bench/smoke cells move to Instagram).
- New open question **OQ-P10-10 — Messenger support, if wanted later.**

#### Discrepancies (for Phase 10 lore closeout)

1. Smoke N1 should be an Instagram DM (and like → nothing); drop the Messenger DM cell. N4’s group-sender check should be an Instagram group.
2. P10-D16 amendment (2026-10-28): Messenger excluded from the bench allowlist; if selected it keeps the strict chat rule only. Plain Messenger postings are filtered.
3. OQ-P10-10: Messenger support, if wanted later (B0: plain Messenger posts shared one key with no per-message timestamp).

### F3 — Adding an app baselines via `currentNotices()`

`addingAnAppBaselinesWhatActiveNoticesReportsWithoutCallerPassingShowing` failed when `setAllowlist(packages)` ignored showing postings, then passed. `CompanionEngine.setAllowlist` now reads `currentNotices()` itself (same call shape as `PairingActivity`). Showing at add time is not sent, including after a later `onListenerConnected` sweep; a posting that arrives after the add is sent.

### F4 — `listener_permission` follows real access

`listenerPermissionFollowsAccessGrantAndOpensAGap` failed when access could not move permission/gap, then passed after `onAccess` close-on-grant (when bound). Service start, `onListenerDisconnected`, and each `device.health` refresh call `isNotificationListenerAccessGranted` into `onAccessChanged` / `refreshAccess`. Re-check on the phone at N10. Brian bench **B9**.

### F5 — Life360 same-content repost is a duplicate

`plainSameKeyIdenticalOutgoingContentIsADuplicateEvenWhenWhenChanges` failed under the old when-only rule, then passed. Plain apps (Life360, Visual Voicemail): same notification key + identical outgoing masked text → `result=duplicate` even when `when` changes. Masked items are never content-deduped (two codes → two items). One content hash per key, bounded with the seen set. Chat apps unchanged.

### F6 — Gap only when allowlist nonempty

`emptyAllowlistDoesNotOpenAGapOnUnbindOrRestart` failed when unbind/restart always opened a gap, then passed. `onDisconnected` and `onProcessStart` open/infer a gap only while the allowlist is not empty.

### F7 — `retired` pruned with the seen set

`retiredIsPrunedWithTheSeenCapAndALateAckStaysIgnored` failed under unbounded retired, then passed. `retired` and `content_by_key` prune with the same cap as seen. A late ack for a pruned retired identity is ignored (not queued); the identity can be admitted again after seen prune.

### F8 — First read item respects `max_characters`

**Chosen:** truncate the first item’s text to the request limit with `truncated: 1` (and `capped: 1`). Alternative not taken: return `capped: 1` with no items. `readTruncatesTheFirstItemWhenMaxCharactersIsSmaller` failed when the first item ignored the budget, then passed.

### F9 — Client check rows split

One Companion check covering five cases → five named rows (no behaviour change): Connected with an empty allowlist; Connected with a bound listener; DEGRADED with access missing; DEGRADED with the listener unbound; not DEGRADED with an empty allowlist and the listener unbound.

### Re-run counts

| Suite | Result |
|---|---|
| Kotlin `NoticeFlowTest` + `CompanionRulesTest` + `Phase4Test` | **58** OK, 0 failures (`NoticeFlowTest` 29 including F3–F8 names; `CompanionRulesTest` 15; `Phase4Test` 14). `EngineFlowTest` not re-run this pass (full Gradle unit suite hangs as in Phase 4; prior count 39) |
| `zola_workspace` | 357 OK |
| `zola_memory` | 134 OK |
| `zola_tools` | 44 OK |
| `zola_tts` | 8 OK |
| `zola_phone` | 41 OK; **2 mutex/isolation tests blocked** — orphaned live `zola_phone` PID 36076 (since 2026-10-28) still holds `Local\ZolaPhone` on 47821; `taskkill` Access Denied. New F1 source check passed. Discover total 43 with those 2 FAIL |
| Client build | 0 warnings, 0 errors |
| `Zola.Client.Checks` | exit 0. Phone rows **16/16** (five named Companion cases + prior phone rows) |

### Install gate (versionCode 7)

`adb install -r` succeeded. Installed `versionCode=7` / `versionName=1.1.0`. APK SHA-256 `AC9F95024F834F69CBE0C23C1AEC2EABDC2E12B03EB73287770FF58DA8A9A701`. Scratch restarted via `run_scratch_phone.py`. Status: `paired` true, `link_state` connected, port 47822, device hash `6a03b08eafb666106b5bb47633c821ee1ff09b8f3c066189f35d85c863f7041e`, `listener_permission=1`, `listener_bound=1`, allowlist exactly Instagram / Life360 / Visual Voicemail.

### EngineFlowTest hang (post–F1–F9)

Hung test: `stateFileOmitsBodiesAndStaysBounded`. Thread dump: `Time-limited test` / `Test worker` RUNNABLE in ECDSA (`Intake.verifySignature` / `Rig.sign`) under `ackNewEvents` ← `stateFileOmitsBodiesAndStaysBounded`. Cause: F4’s `sendHealth` → `refreshAccess` → `notices.onAccess` rewrote the notification queue on every ack when access stayed granted, and `ackNewEvents` re-parsed the whole signed transcript each round (O(n²) with one `device.health` per ack). Fix: `onAccess` is idempotent (save only when permission/gap changes); `ackNewEvents` scans each sent frame once. Re-run: EngineFlowTest **39** + NoticeFlowTest **29** + CompanionRulesTest **15** + Phase4Test **14** = **97** OK in ~19s.

### PID 36076 (not killed)

- `python.exe`, started 2026-10-28 13:22:44. WMI `ExecutablePath`/`CommandLine` empty (query limited).
- Parent **21568** `python.exe` (alive) → grandparent **29260** `Zola.Client` (alive, started 2026-10-28 13:22:42).
- `HERMES_HOME` = live profile `C:\Users\test\AppData\Local\hermes\profiles\zola`.
- Code = **live mirror v3** at `...\profiles\zola\plugins\zola_phone` (`contract_version` 3, `listen_port` 47821, pipe `\\.\pipe\ZolaPhone`). Not the worktree.
- Listens on **47821**. Zola client is running.

### Install gate (versionCode 8)

After the EngineFlow fix: `adb install -r` versionCode **8**. Pairing/grant/allowlist re-confirmed on scratch 47822.

### Bench (Brian; Cursor hands off the UI)

| Step | Result |
|---|---|
| B1 again | Pass. Scratch linked; `listener_permission=1`, `listener_bound=1`, allowlist Instagram / Life360 / Visual Voicemail |
| B9 (F4) | Pass. App notifications off → health `listener_permission=0` / `listener_bound=0`. On again → `1`/`1`, `listener_gap_count` 13→14 |
| B10 (F3) | Pass. Instagram untick → `allowlist_count=2`, queue 0, no new notif. Retick → `allowlist_count=3`, no send of a showing item. New Instagram DM at 12:18:45: one `shape` `admitted` (new `when_ms`), one PC `accept` `kind=notif` `stored`, queue depth 0. A second untick/retick at 12:17–12:18 repeated the same baseline behaviour |
| B10b (access + showing) | Pass. Brian approved exact adb toggles (below). Instagram item still showing. `disallow_listener` → health `listener_permission=0`/`listener_bound=0`. `allow_listener` → `1`/`1`, `listener_gap_count` 14→15. Reconnect shape for the same `when_ms`: `result=duplicate` only. PC `notif` accepts after toggle: 0 |
| B7/B8 again | Pass. Sender + body taken from scratch `proactive.db` notif row `detected_at=2026-11-02T20:18:46Z` (lengths only: sender 16, body 11). Phone `companion.log` (+`.1`–`.3`), logcat, `companion-state.json`, `notification-queue.json`: sender=0 body=0 each; queue items 0. Scratch `zola_phone.log` (+`.1`): sender=0 body=0. Contents never printed |
| F5 | Observed in companion shape: Life360 key `b4bad5c…` → `result=duplicate` on identical outgoing content |

### Approved adb access toggle (Brian, 2026-11-02)

Exact commands only, device `R5CW81KPB6X`, component `com.beebo.zola.companion/.NotificationListener`:

```
adb -s R5CW81KPB6X shell cmd notification disallow_listener com.beebo.zola.companion/.NotificationListener
adb -s R5CW81KPB6X shell cmd notification allow_listener com.beebo.zola.companion/.NotificationListener
```

Nothing else of that kind without a new approval. Used for B10b.

### Approved bench build + `cmd notification post` (Brian, 2026-11-02)

- Build type `bench` (and `n9` for the overflow cell): `com.android.shell` is a plain app and is auto-allowlisted in-process. No harness writes the allowlist or any state file.
- Debug/release never treat shell as plain; Kotlin + Python source tests lock that. Normal builds prune a leftover shell allowlist entry on load (teardown path).
- `cmd notification post` from the shell is allowed **only** while `bench` or `n9` is installed, **only** for N5–N9 and the shell parts of N11 and N12. Real-app cells stay real.
- Teardown after those cells: reinstall normal debug; service load prunes shell; read back allowlist exactly `com.instagram.android`, `com.life360.android.safetymapd`, `com.tmobile.vvm.application`.

### Bench implementation (versionCode 9)

- `NoticePlain` / `NoticeAutoAllowlist` per source set; `NoticePackages.PLAIN` reads `NoticePlain.PACKAGES`.
- `NoticeBook.ensureAutoAllowlist` + prune-on-load; engine calls ensure from `boot` / `setAllowlist` / `onListenerConnected`.
- Tests: `defaultBuildNeverTreatsShellAsAPlainAppOrAutoAllowlistsIt`; `test_debug_and_release_never_treat_shell_as_plain`.
- Installed normal debug versionCode **9**, SHA-256 `43F2D5B84A536CDC7B48802EFE9F997B5EBD169E98152069ADF864760AE73566`. Allowlist readback after install: Instagram / Life360 / Visual Voicemail only. `listener_permission=1`, `listener_bound=1`.

Review copy refreshed under `C:\Users\test\Dev\zola-spikes\p10-notify\review\` including `diffstat.txt`. `PHASE10_BUILD_PLAN.md` is not in the diff.

## Phase 6 — Smoke (started 2026-11-02)

Layout (a): scratch through N1–N12, C3, C6; Part B live mirror after. P10-D16: N1/N4 are Instagram-only (no Messenger). Shell posts only on `bench`/`n9` for N5–N9 and shell parts of N11/N12.

| Cell | Result |
|---|---|
| N1 | Pass. Instagram DM `ZP10-N1-IG…` (body prefix match): `MessagingStyle`/`msg`, `admitted` once, one PC `notif` `stored`, sender present, `is_group=0`, queue 0. Like/follow: `other`/`none` `filtered` twice (`notification_filtered` 14→16); no store row. Group summary `excluded` |
| N2 | Pass (Life360 unobserved). Brian: no way to generate a Life360 alert — skipped. VVM: one `admitted`, one PC `stored`, `mask_kind=verification_code`, body absent, queue 0. Code privacy grep: 0 hits on phone logs/state/queue/logcat, scratch phone logs, and store |
| N3 | Pass. One `sms` `stored` (body_len 11); Messages-package `shape` lines: 0; `notif` store rows after N2: 0; `notification_filtered` unchanged at 16; queue 0 |
| N4 | Pass. Instagram group DM `ZP10-N4-IG…`: `MessagingStyle`/`msg`, `admitted` once, one PC `stored`, `is_group=1`, sender present (len 16 ≠ title_len 59), queue 0 |
| N5 | Pass. Bench installed (shell auto-allowlisted). Scratch stopped; 5 shell posts → phone queue 5, 5 `admitted`. Scratch restarted; hello `notification_queue_depth=5`; 5 `notif` `stored` once (~49 s delay, screen-on/charging window); queue 0 |
| N6 | Pass. Scratch stopped; 3 shell posts queued; `kill -9` pid 21465 → rebound 23330; listener 1/1; queue still 3; scratch returned → 3 `stored` once (~26 s); queue 0 |
| N7 | Pass. Fault launcher `before_ack` → `zola_phone.fault point=before_ack`, exit 1; store +1 with no accept; phone queue 1. Normal scratch restart → one `duplicate` accept; rows delta still 1; queue 0 |
| N8 | Pass. After reboot/unlock: companion pid up without opening the app; listener 1/1; queue still 2. Scratch restarted → 2 `stored` once; queue 0 |
| N9 | Pass. `n9` install (queue cap 3, shell plain). Scratch down; 5 shell posts → queue 3, `notification_queue_drops=2`. Scratch up → 3 `stored`, drops stay 2, queue 0; PC health `notification_queue_drops=2` |
| N10 | Pass. Normal debug v9 reinstall after N9: allowlist exactly Instagram / Life360 / VVM (shell pruned). Listener 1/1 without opening settings (also after N8 reboot). Access off → perm/bound 0, gap open; on → 1/1, `listener_gap_count` 22→23 |

| N11 | Pass. Soak ~13:49–16:14 unplugged (~2h25m). Phone admitted 7 notifs (Life360 4, Instagram 3) = 7 PC `stored`, 0 notif `duplicate`. Texts: 10 `mms` `stored`. Gap count flat at 23 (last gap 13:46 N10, before soak); health never showed bound/perm 0. Queue 0; `notification_queue_drops` unchanged at 2 (N9 residual). Notif accept delay p90/max 873 ms. Brian: no heat/slowness; texts + Life360 observed |
| N12 | Pass. Mid-cell fix: `runtime._relay` now forwards `package` (was omitted; filter could not work). Full `read_notifications`: 2 Life360 only, no Messages/companion, newest-first, store 1091 unchanged. Package filter Life360 → 2; Instagram → 0. Access off → `status=listener_unbound` (not empty list). Scratch killed → `phone_unavailable`. Listener re-allowed; scratch restored. Unit: `test_v4_read_notifications_forwards_package_filter` OK |
| C3 | Pass (text-only MMS not produced; RCS `rcs_flag=unknown`). Four scripted rows once each: S1 `sms` rev1 group0 parts1; P1 `mms` rev3 group0 parts2 image; G1 `mms` rev3 group1 parts3 image; R1 `sms` rev1 group0 parts1 sender prefix `11fa8cb3` (RCS sender; provider `sms` this run). Store 1091→1096 (+1 unrelated group MMS). Label hits in PC log: 0 |
| C6 | Pass. Scratch stopped 16:43:12; three SMS during outage (`ZP10-C6-1/2/3`); restart 16:53:13; all three `sms` `stored` once in send order (detected 00:44:16 / 00:44:24 / 00:44:36Z), rev1 complete group0 parts1, sender prefix `20bc10a3`; accept `delay_ms` ≈705–725 s (includes outage). Store 1096→1101 (+2 unrelated group MMS after catch-up) |

Phase 6 scratch cells N1–N12, C3, C6 complete.

## Part B — live profile

1. Client closed. No `Zola.Client.exe`, no serve/watcher/`zola-phone`, ports 47821/47822 free. Scratch stopped by PID.
2. Backup `C:\Users\test\Dev\zola-spikes\p10-notify\live-backup-partb\`. `proactive.db` via SQLite backup API, SHA-256 `68C054CF76367184DBE0A1C0A918DE944248472AD06DE4623E0148EF2F1E599F`, 1,826,816 bytes. Items by source at backup: gmail 538, mms 487, sms 57, calendar 45 (phone sms+mms 544; no `notif` yet). Mirrored to match worktree (live port 47821 / pipe `ZolaPhone` unchanged): `zola_phone/runtime.py`, `phone_protocol.json` (v4), `phone_vectors.json`. `fake_phone.py` untouched. `phone_test_keys.json` absent; tests not copied; `outage.py` not copied.

| File | Backup SHA-256 | Live SHA-256 |
|---|---|---|
| `zola_phone/runtime.py` | `0BDB7D8644573CA0…` | `54B4EC225203366B…` |
| `zola_workspace/contracts/phone_protocol.json` | `1D2FB8C950409025…` | `7E4FB2DE0DC7948F…` |
| `zola_workspace/contracts/phone_vectors.json` | `518E52E63C3D83F0…` | `8C029E75A6E3CCF8…` |

3. Worktree client launched (`dotnet build` Release, 0 warnings/errors). Exactly one of each:

| Process | PID | Parent | Start (local) |
|---|---|---|---|
| client | 30576 | — | 17:01:44 |
| serve | 4364 → 43092 | 30576 | 17:01:45 |
| watcher | 37304 → 7624 | 30576 | 17:01:45 |
| zola-phone | 5460 → 4376 | 30576 | 17:01:45 |

`zola-phone` listening on Tailscale `100.102.206.71:47821` only; 47822 free. Pipe status before re-pair: `paired=true`, `link_state=offline`, `socket_open=false`, device hash matches Track 3.

4. Re-pair complete 17:03:21. Device hash matches Track 3. `hello` `capabilities=7` (includes `receive_notifications` + `read_notifications`); `listener_permission=1`, `listener_bound=1`, `allowlist_count=3` (Instagram / Life360 / VVM); queue 0; drops 2 (N9 residual). Link connected on 47821.
5. NT-G11 live store: all smoke **texts** present once each (`ZP10-B4-SMS`, `N3-SMS`, `C3-S1/P1/G1/R1`, `C6-1/2/3`) with matching `detected_at`. MMS catch-up needed multiple connect scans (batch 50; ~400 MMS above the live cursor after the scratch window). Smoke **notif** rows remain 0 on live (scratch-only; `PHONE_CONVERSATION_HOLD` would apply if present). Backup deltas: gmail +1 (watcher), calendar 0, sms +36, mms +404, notif 0.

6. Companion row vs `device.health` (approved adb toggles): Connected (`listener` 1/1) → access off → `listener_permission=0`/`listener_bound=0`, allowlist 3, link connected (DEGRADED) → access on → 1/1, `listener_gap_count` 25→26 (Connected). Brian confirms the three row words on the live client.
7. Live logs (`agent`, `errors`, `gui`, `zola_memory`, `zola_phone`, `zola_tools`, `zola_watcher`, `zola_workspace`) and phone `companion.log`(+.1–.3), `notification-queue.json`, `companion-state.json`: 0 hits for scripted `ZP10-*` labels, `body=`, `address=`, `sender_raw=`, `phone_test_keys`, or private-key blocks. Scratch firewall rule still listed once, enabled inbound Allow — removal shown, not run: `Remove-NetFirewallRule -DisplayName "Zola phone intake scratch"`.

Awaiting Brian: Companion-row confirmation for step 6, then **"smoke test passed"** or **"smoke test failed: …"**.

Brian, 2026-11-02: **smoke test passed**. STOP. Continue only on **"proceed to closeout"**.

## Phase 7 — Closeout

Brian: **proceed to closeout** (2026-11-02). Residuals and Track 5 carry-forwards recorded below per his list.

### 7a — Suites and hygiene

Worktree client stopped for mutex tests. Ports 47821/47822 free during the run.

| Suite | Result |
|---|---|
| Kotlin `testDebugUnitTest` | **98** OK, 0 failures (`NoticeFlowTest` 30, `EngineFlowTest` 39, `CompanionRulesTest` 15, `Phase4Test` 14) |
| `zola_phone` | **45** OK (includes `test_v4_read_notifications_forwards_package_filter`) |
| `zola_workspace` | **357** OK |
| `zola_memory` | **134** OK |
| `zola_tools` | **44** OK |
| `zola_tts` | **8** OK |
| `Zola.Client.Checks` | exit 0; phone rows **16/16** (Connected empty allowlist; Connected bound; DEGRADED access missing; DEGRADED unbound; not DEGRADED empty+unbound) |

Live mirror vs worktree (Part B files): `runtime.py`, `phone_protocol.json` (v4, port 47821, pipe `ZolaPhone`), `phone_vectors.json` **match**. `fake_phone.py` **intentionally different** (live untouched residual). `phone_test_keys.json` absent from live; tests not copied. Hermes-agent HEAD still `345cd2b057a452236de401d3534b8502a7465e8d`, porcelain empty. `android-companion/local.properties` gitignored. `phone_test_keys.json` remains the Track 3 test fixture already on `main` (not newly introduced). No APK/keystore/`google-services` tracked. Normal debug **versionCode 9** is the installed build (N10 teardown; USB not attached at 7a re-check).

C3 and C6 re-ran on v4 during Phase 6 and passed (see cells).

### Residuals (Brian, closeout)

1. **F5** (Life360 / plain identical re-post → `duplicate` even when `when` changes): proven by unit test `plainSameKeyIdenticalOutgoingContentIsADuplicateEvenWhenWhenChanges` only; no identical re-post was observed on the phone during smoke.
2. **N12 mid-smoke fix:** `runtime._relay` now forwards `package`; unit test `test_v4_read_notifications_forwards_package_filter`; N12 re-run after the fix and passed. The mirrored live `runtime.py` is that fixed file (SHA-256 prefix `54B4EC225203366B`).
3. Live `notification_queue_drops=2` is from the **N9** overflow cell. The counter is cumulative and was not reset.
4. **N11 coverage:** no listener gaps in the soak window, so admitted equals seen for that window; Brian's own tally was not formally compared.
5. **C3** produced no text-only MMS (same Track 3 limitation).
6. **Open question answered — why did a link peer-close raise `listener_gap_count` 12→13?** A TCP peer-close alone does not open a listener gap. `listener_gap_count` advances only when a gap closes (`closeGap`) or when `onProcessStart` records an **inferred** gap after finding persisted `listener_bound=1` (or an open gap). At 11:46:16 the PC logged `disconnect reason=peer-closed who=phone`; at 11:46:22 a new `hello` arrived with gap 13 while `listener_permission`/`listener_bound` stayed 1. That is a **companion process restart**: `boot()` → `notices.onProcessStart()` increments the count with `last_gap_inferred=1`, then the listener rebound and the socket reopened. Phone log shows `reconnect socket=open` at that instant without a matching phone-side disconnect line in the same second (old process gone). Coincident with Brian turning off **App notifications** for Zola Companion (not notification access)—which can tear down the foreground service/process on this Samsung while leaving notification access granted.
7. **Scratch firewall rule:** Brian will remove it himself (`Remove-NetFirewallRule -DisplayName "Zola phone intake scratch"`). Not run by Cursor.

### Track 5 carry-forwards

- No app label or conversation title is stored for notifications (schema residual; RD-G2).
- Messenger support remains an open question (OQ-P10-10); this track shipped Instagram-only for DMs/groups (P10-D16).
- `read_code` stays texts-only; a masked notification code is reported as masked and is not readable through `read_code` in Phase 10.

### Exit criteria

| # | Criterion | Result |
|---|---|---|
| 1 | NT-G1–G12 answered; STOP verdicts recorded | Met (Phases 2–3) |
| 2 | Kotlin + plugin suites + client checks; C3/C6 re-run | Met (7a; C3/C6 Phase 6) |
| 3 | B1–B8 before review; N1–N12; N11 seven criteria | Met (Phase 5–6; N11 coverage residual #4) |
| 4 | Privacy greps 0 | Met (bench B7/B8; smoke; Part B step 7) |
| 5 | Contract v4; hello capabilities; health fields; notif≠watch; Companion DEGRADED | Met |
| 6 | Guardrail tests (one-engine, mask, queue, admission, no silent loss, visibility, read-live) | Met in NoticeFlowTest / EngineFlowTest |
| 7 | G-ROLLOUT recorded; NT-G11 live texts present | Met (layout a; Part B step 5) |
| 8 | No forbidden installs/edits; live paired at end | Met; phone left on live `zola-phone` after Part B |

### 7b–7i

Progress doc completed in this section. Implementation commit and merge SHAs follow the git steps.


