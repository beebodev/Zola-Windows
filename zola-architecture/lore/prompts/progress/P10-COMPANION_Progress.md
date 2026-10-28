# P10-COMPANION Progress — Android app, texts

## Branch

- Primary folder: `C:\Users\test\Dev\zola-windows`, branch `main`
- Worktree: `C:\Users\test\Dev\zola-windows-p10-companion`, branch `p10-companion`
- Base SHA: `43c7bc1c4ec6870810ac0bac9b42d230ee28cf33` (`main` = `origin/main` at Phase 1)
- Worktree HEAD: `43c7bc1c4ec6870810ac0bac9b42d230ee28cf33`
- Hermes HEAD: `345cd2b057a452236de401d3534b8502a7465e8d` (detached `HEAD`, clean, no porcelain)
- Prompt: `P10-COMPANION_Prompt_v1.1.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P10-COMPANION_Prompt_v1.1.md`)
- Prompt SHA-256 (on-disk, 54,288 bytes): `cdd7a97756a73bb7b745e145a0b5db07fdac4e67df2be363886e854b705aba99`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction. On-disk value recorded for Brian to confirm.
- Scratch: `C:\Users\test\Dev\zola-spikes\p10-companion\` (created, empty)
- Track 2 closeout tip this branch was cut from: `43c7bc1c4ec6870810ac0bac9b42d230ee28cf33` (merge `2e467c50b7b54a9e8f4cd6a352eaf652f7d4c4a6`, then the docs commit)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Setup | COMPLETE (STOP) |
| 2 | Grounding | COMPLETE (STOP) |
| 3 | Proposal | COMPLETE (STOP) — verdicts 1–7 and 9–11 recorded here; item 8 chosen in the Phase 4 instruction |
| 4 | Implement | COMPLETE (STOP) — not installed |
| 5 | Review checkpoint | COMPLETE (STOP) — R1–R11 in. Scratch bench corrected 2026-10-25. |
| 6 | Smoke | COMPLETE — passed. C1–C9, C10 under amendments, C11 on the fresh home, Part B, and the C9 repeat. |
| 7 | Closeout | IN PROGRESS — 7a checked. The worktree client is up and paired. The merge waits until that client is closed. |

## Guardrails summary

- **G-SCOPE:** `android-companion/`, the `.gitattributes` and `.gitignore` lines it needs, contract v3 and vectors, Python contract tests and the fake phone in the same commit. PC code only where a Phase 3 verdict approves a listed candidate. This progress doc. Live plugin mirror only in Phase 6 Part B.
- **G-ARCH:** build plan v1.4 and Appendices A/B are truth. CP-G1–G12 stop for Brian.
- **G-PATTERN:** read every file in full before changing it.
- **G-NOCHANGE:** no `hermes-agent` edits; no `watcher.py`, `ranker.py`, `surface.py`, `speech.py`, `proactive_store.py`, Google modules, `SOUL.md`, identity, lore, `config.yaml`, or Windows client edits. No notification listener, allowlist, Zola tools, speech, or sending.
- **G-INSTALLS:** every Gradle plugin, library, SDK component, JDK, or platform-tools download is listed at the Phase 3 STOP and approved before Phase 4. No Firebase, Google Services plugin, analytics, or crash reporting. Nothing is installed in the Hermes venv.
- **G-OLD-REPO:** old-repo `assets/`, `gradle.properties`, `local.properties`, `google-services.json*`, and Firebase files are never opened, copied, logged, or built. The old ZolaAssistant app on the phone is recorded and never changed.
- **G-ONE-ROUTE / G-ONE-WRITER / G-VERIFY-BOTH-WAYS / G-RESEND / G-COMMIT-BEFORE-ADVANCE / G-NO-SILENT-LOSS / G-BASELINE-ONCE / G-SIZE / G-CANONICAL / G-TIMERS / G-PEER-CLOSE:** as written in the prompt.
- **G-SECRETS / G-PRIVACY:** StrongBox key, non-exportable. Pairing code never logged or stored after pairing. Metadata-only logs. Scripted texts marked `ZP10-`.
- **G-PROCESSES:** stop only processes this track starts, by PID.
- **G-COMMENT:** `// P10-COMPANION: <why> — P10-D0X` / `# P10-COMPANION: …`.
- **G-STOP / G-CLOSEOUT / G-LORE-SCOPE / G-LIVE:** no lore edits. Live steps one at a time, Phase 6 only.

## Phase 1 — Setup

`git fetch origin` in the primary folder. `git status --porcelain` was empty. `main` = `origin/main` = `43c7bc1c4ec6870810ac0bac9b42d230ee28cf33`.

Worktree list before `git worktree add`:

```
C:/Users/test/Dev/zola-windows  43c7bc1 [main]
```

After the worktree:

```
C:/Users/test/Dev/zola-windows                43c7bc1 [main]
C:/Users/test/Dev/zola-windows-p10-companion  43c7bc1 [p10-companion]
```

Primary `main` stayed clean. Hermes stayed clean at the pin. No source files were modified.

### Plugin suites (worktree, Hermes venv)

| Suite | Command | Result |
|---|---|---|
| `zola_workspace` | `python -m unittest discover -s tests -t tests` | 357 OK |
| `zola_memory` | `python -m unittest discover -s tests -t .` | 134 OK |
| `zola_tools` | `python -m unittest discover -s tests -t .` | 44 OK |
| `zola_tts` | `python -m unittest discover -s tests -t .` | 8 OK |
| `zola_phone` | `python -m unittest discover -s tests -t .` | 29 OK |

Matches the Track 2 close: **357 / 134 / 44 / 8 / 29**.

### Client

`dotnet build windows-client\Zola.Client\Zola.Client.csproj`: succeeded, 0 warnings, 0 errors.

`dotnet run` of `Zola.Client.Checks`: exit 0.

coverage: lifecycle rows 22/22, admission rows 13/13, start rows 9/9, invalid pairs 6/6, stop_phrase rows 4/4, amendments 7/7, latch rows 18/18, wiring rows 9/9, clarify rows 20/20, timing rows 8/8, compress rows 8/8, supervision rows 38/38, speech rows 38/38, phone rows 11/11.

### Live profile (read only)

Fifteen shipped plugin files match the worktree, SHA-256 equal. Live `plugins/zola_workspace/contracts/phone_test_keys.json` is absent.

`proactive.db` opened `mode=ro`. `user_version` 0. `schema_version` 6. Counts: calendar_events 1052, cursors 5, deliveries 0, item_attempts 167, items 175, loops 9, meta 7, phone_tombstones 1, watcher_health 1, watcher_rejects 1. Phone rows (`items` where source is sms, mms, or notif): 0.

`phone\peer_state.json` keys: `device_id`, `link_open`, `pc_seq`, `phone_seq`, `public_pem`, `rejected`. `device_id` empty, `public_pem` empty, `link_open` false, both sequence numbers 0, `rejected` length 0. `pc_key.bin` is present, 498 bytes. No key material recorded.

`tailscale ip -4`: `100.102.206.71`.

Firewall read-back, not modified: DisplayName "Zola phone intake", Inbound, Allow, Enabled, Profile Any, TCP local port 47821, InterfaceAlias Tailscale.

No listener on 47821.

### Android toolchain (present; nothing installed)

- SDK: `C:\Users\test\AppData\Local\Android\Sdk`. `ANDROID_HOME` and `ANDROID_SDK_ROOT` are unset.
- JDK: `C:\Program Files\Android\Android Studio\jbr` (`JAVA_HOME`), OpenJDK 21.0.10.
- platform-tools: Android Debug Bridge 1.0.41, version 37.0.0-14910828, at `platform-tools\adb.exe`.
- build-tools: 35.0.0, 35.0.1, 36.0.0.
- platforms: android-35, android-36.
- Gradle cache: `8.11.1` and `8.13` under `%USERPROFILE%\.gradle\caches`. Spike wrapper distribution: `gradle-8.13-bin.zip`.

### Phone (read only, USB serial `R5CW81KPB6X`)

`adb devices -l` lists two transports of this one phone: USB `R5CW81KPB6X` (`SM_S918U1`) and `100.118.148.119:5555` (same model). Every shell below used `-s R5CW81KPB6X`.

- Android 16, SDK 36, security patch 2026-09-05, model `SM-S918U1`.
- SMS role holder: `com.google.android.apps.messaging`. `settings get secure sms_default_application` returned `null`.
- Tailscale package `com.tailscale.ipn` is installed. `tun0` is `100.118.148.119/32`.
- IPVanish package `com.ixolit.ipvanish` is installed. `pidof` returned no process. The up tunnel is Tailscale, not IPVanish.
- Spike package `com.beebo.zola.spike.transport`: `pm path` returned nothing.
- Old app `com.beebo.zolaassistant` is installed, `versionName=1.0`. It declares `AvaNotificationListenerService`. It is not in `enabled_notification_listeners`, so it does not hold notification-listener access. Granted names recorded, nothing changed: `READ_SMS`, `RECEIVE_SMS`, `SEND_SMS`, `WRITE_SMS`, `POST_NOTIFICATIONS`, `READ_CONTACTS`, `RECORD_AUDIO`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_MICROPHONE`, `RECEIVE_BOOT_COMPLETED`, `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE`, `WAKE_LOCK`, `health.READ_SLEEP`, `health.READ_STEPS`, `health.READ_HEART_RATE`, plus the Google Play services grants `BIND_GET_INSTALL_REFERRER_SERVICE`, `C2DM RECEIVE`, `READ_GSERVICES`, `AD_ID`, and the ads-services grants.

### Entry gate

No `google-services.json`, `local.properties`, or `gradle.properties` in the worktree. `android-companion/` does not exist yet. `%LOCALAPPDATA%\zola-spikes\p10-transport\` is absent.

## Phase 2 — Grounding (2026-10-20)

Read in full: build plan Sections 1–5, Track 3, Track 4 NT-G5, Track 5 RD-G3 through RD-G5, Appendix A and Appendix B; `phone_protocol.json` v2; `phone_ids.py`; `zola_phone` `__main__.py`, `runtime.py` `local_request` / `_dispatch`, `serve.py` `create_pipe` and `listen_forever`; spike findings §§4–7; spike `HoldService.kt`, `SocketWriter.kt`, `InboxReader.kt`, `InboxWatch.kt`, `PhoneKey.kt`, `RetryBackoff.kt`, the manifest, and `app/build.gradle.kts`. Lore: `P2-D17` (`DESIGN_DECISIONS.md` line 383), `P4-D25` (line 760), `P8-D09` (line 1489), `P8-D11` (line 1530).

**Discrepancy.** The build plan Track 3 file list says the spike code was deleted at closeout. It is on disk at `C:\Users\test\Dev\zola-spikes\p10-transport\android\`. Read only. Not built, not installed, not copied. Its `app/build.gradle.kts` lines 7–15 copy `google-services.json` from `%LOCALAPPDATA%\zola-spikes\p10-transport\` and can apply the Google Services plugin. The companion must not do that. That secrets folder is absent (Phase 1).

### CP-G1 — Project

Layout: `android-companion/` with `settings.gradle.kts`, root `build.gradle.kts`, `gradlew.bat`, `gradle/wrapper/`, `app/` (manifest, Kotlin, unit tests). Package `com.beebo.zola.companion`. Not the spike id `com.beebo.zola.spike.transport` and not `com.beebo.zolaassistant`.

SDK: `compileSdk` 36, `minSdk` 36, `targetSdk` 36, `buildToolsVersion` 36.0.0. The phone is API 36. Kotlin JVM target 17, matching the spike `app/build.gradle.kts` lines 36–45. `hello.app_version` is the manifest `versionName`, proposed `1.0.0` (`versionCode` 1).

Dependencies, every one already in the Gradle cache from the spike. None are new downloads. No Firebase, no Google Services plugin.

| Piece | Version | Cache |
|---|---|---|
| Gradle wrapper | 8.13 | cached (`caches\8.13`); reuse the spike wrapper files |
| Android Gradle Plugin | 8.13.2 | cached |
| Kotlin | 2.3.21 | cached (`kotlin-stdlib`) |
| OkHttp | 5.4.0 | cached |
| `androidx.core:core-ktx` | 1.17.0 | cached |
| `androidx.appcompat:appcompat` | 1.7.1 | cached |
| `com.google.android.material:material` | 1.13.0 | cached |
| `junit:junit` | 4.13.2 | cached |

Debug signing uses the default debug keystore. It is not committed. `.gitignore` covers `build/`, `.gradle/`, `local.properties`, and APKs.

`.gitattributes` lines to add: `*.jar binary`, `gradlew text eol=lf`, `*.bat text eol=crlf`. `git ls-files` of `*.bat`, `*.jar`, and `gradlew` in this worktree is empty, so those patterns match no tracked file and do not renormalize the tree. Existing attributes stay `*.ttf binary` and `*.glb binary`.

### CP-G2 — Foreground service

Type `remoteMessaging` with `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_REMOTE_MESSAGING`, as the spike manifest lines 5–6 and 32–35. `dataSync` has a 6-hour cap and, on target 35+, cannot start from `BOOT_COMPLETED`. This type is the one the spike used instead. [EXT] https://developer.android.com/about/versions/14/changes/fgs-types-required [EXT] https://developer.android.com/develop/background-work/services/fgs/service-types

Start from the app, from `BOOT_COMPLETED`, and from `MY_PACKAGE_REPLACED` (the app's own package). No `directBootAware`. Nothing runs before unlock. Findings §5 lines 378–379. That is accepted.

Ongoing notification: channel "Companion", low importance. Title "Zola companion". Text is the link word only (Connected, Reconnecting, Not paired). No message content. `POST_NOTIFICATIONS` is a runtime grant.

Battery: the app asks for the exemption with `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`. Brian also sets Samsung Never sleeping apps and battery Unrestricted, and the same Unrestricted setting for Tailscale. Sideloaded SMS permission can hit Android's restricted-settings gate. [EXT] https://support.google.com/android/answer/12623953 The companion is not installed yet, so what that screen shows is a Phase 5 record, not a guess.

`RECEIVE_MMS` is not in the spike manifest and is not proposed. Capture is the observer and the content job. `RECEIVE_SMS` stays as a wake trigger. The receiver does not read the PDU.

### CP-G3 — Connection

One socket. One writer: `SocketWriter.write` holds its lock across the whole sink call (spike lines 10–14). Every PC frame is verified in Appendix B §3 order before a pong, a read, or an ack is acted on. `onClosing` drops the socket and reconnects (findings §6; `HoldService.kt` line 255).

Reconnect triggers: the Tailscale VPN network (`TRANSPORT_VPN` on `tun0`, address `100.118.148.119`), a lost socket, a PC close, boot, and the app starting the service. The spike's physical-network callback treats VPN as not physical (`HoldService.kt` lines 641–644) and would miss a Tailscale-only path. This track watches the VPN network Tailscale provides.

Backoff is the contract list 10 s, 30 s, 60 s cap (`phone_protocol.json` lines 224–228). It is a timer. C6 and C10 need a reconnect within 60 s of `zola-phone` returning when no text arrives to wake the phone. A network callback does not fire for that, because the phone's network never left.

| Option | Lateness, screen off, battery | Battery cost | What C10 criterion 4 would measure |
|---|---|---|---|
| (a) `Handler` only | Spike: a 30 s arm ran 43.7 s late; another timer reached 339 s (findings §6) | Low | Time from PC listen to the next frame. This misses 60 s. |
| (b) `AlarmManager.setExactAndAllowWhileIdle` at the backoff steps | Fires in idle. `setAndAllowWhileIdle` is quota-batched (about one per 9 minutes) and cannot promise 60 s. Exact-while-idle can. | One short wake per attempt | The alarm is the wake. 60 s is measurable. |
| (c) Partial wake lock for the whole disconnect | Handler fires on time while the lock is held | CPU stays up for the whole outage. A 10-minute outage fights the 2 mAh budget if it happens more than once. | On time, at a battery cost. |
| (d) Network callback only | No timer | Lowest | Does not run when the PC process returns and the network stayed up. |

**Recommend (b).** Permission: `SCHEDULE_EXACT_ALARM`. Android does not pre-grant it to a sideloaded app that is not a calendar or clock. Brian grants it under Special app access → Alarms & reminders. [EXT] https://developer.android.com/develop/background-work/services/alarms One alarm armed at a time, at 10 s then 30 s then 60 s. If the grant is refused, (c) is the fallback and it needs a named cap.

An event with no socket stays in the durable pending set. Nothing is dropped.

A second partial wake lock, from starting a send until that event's ack or the socket drops, is not in the plan (the plan's lock is for reads). **Recommend yes, Brian decides.** Tag `zola:event`, max hold 20 s. C10 criterion 3 is p90 ≤ 5 s. Without it the process can sleep between the observer callback and the ack.

### CP-G4 — Capture

While the service runs: `ContentObserver` on `content://sms` and `content://mms`, descendants included. [EXT] https://developer.android.com/reference/android/content/ContentResolver#registerContentObserver(android.net.Uri,%20boolean,%20android.database.ContentObserver) A content-URI job is armed again at boot, same shape as `InboxWatch.kt` lines 17–33: update delay 1 s, max delay 5 s. That delay is the debounce. Under CPU sleep the job's max delay is the tolerance; the observer is the path while the process is alive.

Inbound only. SMS `type` 1 is inbox (`Telephony`). On this phone the SMS table is type 1 (18386) and type 2 sent (9755). MMS `msg_box` 1 is inbox. `m_type` 132 is the retrieve-conf the spike treats as complete (`InboxReader.kt` line 462); 128 is the sent request. Drafts, outbox, and failed are not those values.

MMS text comes from `text/plain` parts (`content://mms/part`, column `ct` / `text`, charset on the part). Sender is address `type` 137 (`InboxReader.kt` lines 351–355 and 459), stored as `sender_raw` with no phone-side normalization (P10-D10). `participant_count` is the address-row count. `is_group` is 1 when that count is greater than 2. Attachment metadata uses the contract list `image` / `video` / `audio` / `other` (`phone_protocol.json` lines 285–290). The spike's `coarseKind` has no `audio` branch (`InboxReader.kt` lines 466–469); the companion adds it.

`rcs_flag`: `yes` only when a part or the row `ct_t` proves RCS (content type contains `rcs`, or `application/vnd.gsma.`). The probe below shows this phone stores an RCS 1:1 as an SMS-provider row with no column that marks it, so an SMS-provider row is `unknown`, not `no`. An MMS-provider row that does not prove RCS is also `unknown`. No logic depends on telling RCS from MMS (build plan Section 4).

**Schema probe, USB `R5CW81KPB6X`, projection of non-content columns only.** SMS 28141 rows. MMS 149300 rows. `spam_report` exists on both and is `0` on every row. `safe_message` exists on both and is `0` on every row. `content://sms/spam` has 0 rows. Columns `blocked` and `block_type` error, so they are not on this provider. [EXT] https://developer.android.com/reference/android/provider/BlockedNumberContract is readable only by the system, the default SMS app, and the default phone app. This app will be none of those (default SMS is `com.google.android.apps.messaging`).

`ct_t` across all 149300 MMS rows contains the substring `rcs` in 0 rows. Part content types include 32 rows of `application/vnd.gsma.botmessage.v1.0+json` and no `rcs` type. SMS creators include `com.google.android.apps.messaging` (9959) and `com.sec.android.easyMover` (18157). MMS creators are only those two.

**Send probes, 2026-10-20, after Brian said they were done.** Rows whose body starts with `ZP10-`. Addresses are SHA-256 of the stored form. No body recorded.

| Row | Provider id | Who | Stored address hash | Thread | Provider `date` |
|---|---|---|---|---|---|
| SMS | 29006 | the stated SMS sender | `20bc10a373586bd95a5946b574ac9bf42125dae3b9cf8c3e813b4787cb11f536` | 1683 | 1792534972657 |
| RCS 1:1 | 29007 | the stated RCS sender | `11fa8cb302978567148d83d35af5f2ee07238883137261f9196adb94afb1a4b4` | 56 | 1792535108357 |

Both rows are `content://sms`, `type` 1, `protocol` 0, creator `com.google.android.apps.messaging`. No `ZP10-` row is in `content://mms` (43 MMS rows in the surrounding window, none marked). There is no group `ZP10-` row. The RCS 1:1 is an SMS-provider row. The non-content columns match the SMS row. `spam_report` 0, `spam_type` 0, `safe_message` 0, `block_filtered_status` empty, `hidden` 0, `contains_otp` 0, `group_id` empty, `group_type` empty. `read` is 0 on the SMS row and 1 on the RCS row. That is the seen flag, not a type.

Which app stores RCS on this phone: Google Messages, in the SMS provider.

Blocked: Brian blocked the test number, sent an SMS and an RCS, then unblocked. No surviving row has `block_filtered_status`, `spam_type`, or `spam_report` set. The two `ZP10-` rows above are the ones still present, and they are unmarked. A blocked text that the app drops never becomes a row, so there is nothing to send. This probe did not leave a blocked row behind, so it did not meet the stop condition (a blocked row with no marking column). Columns that do exist, and that the companion will treat as not sendable when they are set: `spam_report` nonzero, `spam_type` nonzero, `block_filtered_status` non-empty.

Spam: `content://sms/spam` has 0 rows. No SMS row has `spam_report` nonzero. No spam `ZP10-` row was stored.

Provider ids: in 28990–29009, ids 29003 and 29005 are absent. The new `ZP10-` rows are 29006 and 29007, both higher than those holes, so the missing ids were not reused. Limit: this is two missing ids in one span on this phone, not a proof that ids stay unique forever. R2 identity is not blocked by this probe.

### CP-G5 — Cursors, pending set, resends

Per id space, `sms` and `mms`. An incomplete row waits in the pending set and is retried on provider change, on connect, and on the contract schedule `incomplete_retry_ms` 600000 and `incomplete_retry_attempts` 20 (`phone_protocol.json` lines 232–233). Completed rows above it are sent (Appendix B §5). At the bound it is sent `exhausted` with what exists. A later completion is a higher `revision`. A lower or equal revision is never sent as new.

What raises a revision: part text arriving, sender arriving, completeness changing, or the final provider `date` changing (P10-D08; spike `173961` moved by 83 s).

First run writes the install id, both cursors at the current max ids, and the baseline time in one atomic file write, before any send (G-BASELINE-ONCE). Restart, a permission regrant, `MY_PACKAGE_REPLACED`, and a re-pair do not baseline again. Only clearing app data or reinstalling does (Appendix B §1).

A row that is gone when it comes due is a terminal `deleted` outcome. That covers a row deleted before the first send and a pending row that is gone at resend time, including the resend after a crash. The phone records `deleted`, counts it, sends one terminal notice for that identity, and removes it from the pending set. It does not stay pending, and it does not wait for an ack of a body it can no longer read. The notice itself is not kept pending.

Crash before ack, row still present: the pending entry is still there after restart. The resend is a fresh envelope (new `seq`, current `sent_at_ms`, same identity and revision). `seq` is strictly increasing across restart and re-pair and is not reset while the install lives.

In-flight window: **4**, matched on `provider_id` + `kind` + `revision`. An unacked item does not block later ids (G-NO-SILENT-LOSS). It stays pending, is retried on every connect and once a minute while connected, and is counted in `device.health` as `unacked`. The log line is `reason=unacked` plus the hashed id.

Ids acknowledged above the cursor live in a durable set so they are not resent. When the cursor advances, ids at or below it leave the set. The set is not discarded to save space. If it passes 2000 entries the count is logged and the entries stay.

**Provider reset.** If the provider max id falls below the cursor for an id space: stop sending that id space, log `provider-reset`, and count it in `device.health`. The cursor stays where it is. The phone does not lower the cursor and keep sending. A reused id would collide with an item already stored. Starting that id space again is a later decision.

**Restore.** A new id is `restored`, not sendable, when its provider `date` is older than the newest delivered text's date in that id space by more than 43200000 ms (12 hours). Older than the baseline is not the test. A restored date can be after the baseline. The margin is measured below, under Phase 3. A lower or equal revision is never a new item.

The id-reuse results are in Phase 3. SMS ids 29003 and 29005 were not reused. The photo-MMS follow-up did not reuse the deleted id. Both are observed reuse only.

### CP-G6 — Masking

Order: mask the complete text, then truncate an unmasked body to 16000 characters with `truncated: true`. A masked body is withheld. `mask_kind` is `verification_code`, `reset_link`, or `unsure` (`phone_protocol.json` lines 280–284). The same function runs on history results.

Rules, fail closed, in this order:

1. `contains_otp` set on the row → `verification_code`, whatever the text says.
2. A URL whose path segment or query-parameter name is `reset`, `verify`, `login`, `sign-in`, `signin`, `token`, `magic`, or `auth`, or whose query value is a run of 20 or more letters and digits → `reset_link`. Any URL in a message that also has a whole word `reset`, `password`, `verify`, `login`, `sign-in`, or `signin`, or the phrase `sign in` or `log in` → `reset_link`.
3. A whole word `code`, `otp`, `pin`, `passcode`, `verification`, `verify`, `one-time`, `login`, `sign-in`, or `signin`, or the phrase `log in` or `sign in`, within 40 characters of a code token → `verification_code`. A code token is a 4–8 digit run, a 5–8 letter-and-digit token, or a 4–8 digit code split by single spaces or hyphens (`482-913`, `48 29 13`, `48-29-13`). The split form counts only when a keyword is in that 40-character window, so `555-0100` and `2026-10-21` stay plain.
4. A line that is a letter label, a colon, and a 4–8 digit token (`Amazon: 482913`) → `verification_code`. `6:30` is two digits. A sentence with digits and no colon is not this rule.
5. A body that is only a 4–8 digit token, only a 6-character letter-and-digit token, or only a split 4–8 digit code → `unsure`.
6. Anything else stays unmasked. A bare number inside a sentence is not enough.

The Phase 2 paragraph headed "40" names 41 strings. All 41 mask. All 20 ordinary samples stay plain. The gate code, the building PIN, and the order code stay masked (verdict 11). `password` is a URL-adjacency word, not a code keyword.

Masked (40): Google "Your verification code is 482913"; "G-482913 is your Google verification code"; "OTP 482913"; "Your OTP is 482913. It expires in 10 minutes."; "PIN 4829"; "passcode 482913"; "one-time password 482913"; "Use code 482913 to sign in"; "code: AB12CD"; "Enter 482913 to verify your device"; carrier "Msg: 482913 is your code"; "WhatsApp code 482-913"; "Apple ID code 482913"; "Microsoft account security code 482913"; "Amazon: 482913"; bank "verification code 482913 do not share"; "Your temporary PIN is 4829"; "passcode: 48-29-13"; "Login code 482913"; `https://accounts.example/reset?token=aaaaaaaaaaaaaaaaaaaa`; `https://id.example/verify/email`; `https://id.example/login`; `https://id.example/sign-in`; `https://id.example/signin/continue`; `https://id.example/magic/aaaaaaaaaaaaaaaaaaaa`; `https://id.example/auth/callback`; a query `?token=abcDEF1234567890abcd`; "click to reset your password https://id.example/reset"; a body that is only `482913`; a body that is only `AB12CD`; "code 482913" with the digits after a newline; "OTP" then the digits on the next line; "Your code is 482913." with a period; fullwidth-safe ASCII "verification code 482913"; "PIN is 482913 for the transfer"; "passcode 482913 expires today"; `https://example.test/path/token/aaaaaaaaaaaaaaaaaaaa`; "Use 482913 as the verification code for order discussion"; "one-time code 482913"; "security code 482913"; "confirmation code 482913".

Ordinary, must stay unmasked (20): "See you at 6:30"; "It was $19.99"; "Call 555-0100"; "1600 Amphitheatre Parkway"; "Zip 94043"; "Order 100045"; "Tracking 1Z999AA10123456784"; "Score was 6 to 3"; "Meet on 2026-10-21"; "https://video.example/watch?v=abc"; "https://news.example/story/12"; "https://maps.example/place/1"; "Table for 2 at 7"; "Room 1204"; "Gate B12"; "The total is 48.29"; "Reference 482913 is the invoice" (digits, no keyword); "https://carrier.example/track/1Z999"; "Birthday 04/19"; "Extension 2048".

Stay masked (verdict 11): "The gate code is 1948"; "Building PIN 1948"; "Your order code is AB12CD".

### CP-G7 — Reads

Partial wake lock from accepting the request until the result frame is written. Tag `zola:read`. Max hold 20 s. Released on timeout, error, and socket loss.

**Selector. Approved.** The PC sends the number. The phone builds a digits-only key with the same US rules as `phone_ids.normalize` (`phone_ids.py` lines 60–81) and matches that key. This is a narrow clarification of P10-D10: the phone still does no contact matching, and it does not normalize a stored or sent `sender_raw`. The key is used only to find messages. It is not written to the state file and it is not put in a frame. Shared vectors in the contract keep the two implementations identical.

**Sent texts. Approved.** History reads include the phone's own sent texts, `direction: "out"`. They are never events.

**Groups. Approved.** A history read includes a group thread when the number is a participant. The phone counts distinct participants. Each history item has an explicit `thread_id` and `is_group`. It also carries that message's `sender_raw` and `participant_count`. No group title and no contact name.

`read_code`: only an item this phone masked, and only if `received_at_ms` is within 86400000 ms (24 hours). Result is `value_kind` `code` or `link`, or `status: "refused"` with `not_identifiable`. `unsure` always refuses. The value is one extracted token or one URL, never the body. It is held in memory until the frame is written, then dropped. Never logged, never stored. For an `unsure` item Zola can say a masked text arrived from that sender and that it is on the phone.

`diagnostic_read` counts only: rows since baseline per id space, pending incomplete, exhausted, unacked, rejected, restored, deleted, provider-reset, cursor lag (max id minus cursor). No ids and no content.

The phone still answers after `deadline_ms`. The PC logs `late-result` (`runtime.py` lines 484–490). Dropping the answer would hide the measurement.

History limits stay Appendix B §7a: at most 50 messages and 64000 characters, or less if asked. The PC re-check of result `items` is G-SCOPE candidate (b). Today `_dispatch` copies `items` through (`runtime.py` lines 491–493).

### CP-G8 — Time

On this phone a sampled SMS `date` and `date_sent` are both greater than 1e12 (milliseconds). A sampled MMS `date` and `date_sent` are both less than 1e12 (seconds). `received_at_ms` is the final local provider `date` after the row is complete: MMS seconds times 1000, same rule as `InboxReader.normalizeMmsDate` (lines 464). `date_sent_ms` is metadata only, same conversion. A later revision that changes the final `date` updates `received_at_ms` and raises `revision`. It does not create a new item.

### CP-G9 — Contract v3

`supported_versions` becomes `[3]`. v2 frames are `version`. The bump is a STOP (build plan lines 238–239). Python tests, the fake phone, and the Kotlin verifier move in the same commit.

Additions: selector shape for recommendation (b); history items with the §6 event fields plus `direction`, `truncated`, and `mask_kind`; `diagnostic_read` request and the count fields above; `code.read.result` gains `value`, `value_kind`, `status`, and refusal reason `not_identifiable`; `hello` keeps Appendix B §6 (app version, capabilities, cursors, pending-incomplete count; notification queue depth stays 0 until Track 4); `device.health` for texts adds permissions held, battery-exempt, unacked, exhausted, rejected, restored, deleted, provider-reset. Provider-reset means that id space is stopped, not that the cursor was lowered. Listener fields stay absent. New not-sendable reasons `deleted` and `restored` are phone-side, not PC reject reasons.

New vectors: PC-signed frames from a new PC test key in `phone_test_keys.json` (accept and each §3 refusal); canonical-byte cases (nested objects, escapes, U+001F, non-ASCII, emoji, a lone surrogate replaced by U+FFFD, a large integer); pairing MAC cases from the phone side. Kotlin reads the contract by a test resource that points at `hermes-plugins/zola_workspace/contracts/`, and a unit test fails if generated constants drift from the file. The built APK is scanned for the test-key material and for `google-services`.

PC candidates needed: (a) accept v3; (b) re-check §7a on read results before they return to serve; (c) `zola_phone.accept` logs `received_at_ms` delay with no content, for C10 criterion 3; (d) log `hello` and `device.health` as counts. (e) is not a production change under the layout recommended in CP-G11.

Live `zola-phone` moves to v3 only in Phase 6 Part B, after the mirror.

### CP-G10 — Pairing and delivery state

Pairing screen: PC address is the Tailscale IPv4 (Phase 1: `100.102.206.71`), port 47821 from the contract, and the 8-digit code Brian types. MagicDNS is a second label he can type, resolved on the phone only if it is a single host on the tailnet; the IPv4 is the primary. Four frames as Track 2. The phone pins the PC public key from `pc_bind` after the code MAC checks. Stored: `device_id`, phone `seq`, PC public key, last PC `seq`, PC address. The code is not stored after `pc_ok`. The screen shows paired or not, connected or not, and counts. No code and no key material after pairing.

Re-pair keeps `device_id` and phone `seq`, replaces the PC key, and resets the last PC `seq` only when the PC key changed.

**Delivery state is not chosen.** Verdict 8 still has both options. Phase 4 does not start on this item until one of them is kept. The two options, and how the second one would work, are in the Phase 3 verdicts below.

### CP-G11 — Smoke layout

**Approved: layout (c).** The scratch `zola-phone` runs beside the live client, so Zola and the Gmail watcher stay up for the 12 hours. The phone is paired to the scratch instance. The live row shows Not paired until the final cell.

The scratch launcher lives in the scratch folder and is never committed. Its `main` is the production `main` with three names changed. `serve_pipe` creates the next pipe from `engine.protocol["pipe_name"]` (`serve.py` lines 113 and 128), so the scratch process assigns the scratch pipe name on the engine before `create_pipe`. The first instance and every later instance then use it. `listen_forever` checks the port it was given against that same port (`serve.py` line 239), so 47822 does not change the contract. The side-by-side is in the Phase 3 section. A source check reads `PhoneProcess.cs`, `App.xaml.cs`, and `__main__.py` and fails if they contain `ZolaPhoneScratch` or `47822`.

Production `__main__.py` line 75 still reads `ZOLA_PHONE_LISTEN_PORT` before the contract port. That override is a residual. The client does not set it. The scratch launcher does not read it.

The scratch process is started with `HERMES_HOME` set to a directory inside the scratch folder. The code line that reads `HERMES_HOME` is the same line. The value is what keeps the scratch peer file off the live profile.

| Layout | Pairings | Zola | Live store | Production change |
|---|---|---|---|---|
| (a) | scratch, then one live re-pair | down for the 12 h | no `ZP10-` rows | none |
| (b) | live and scratch, re-pair between cells | up for some cells | scripted rows in the live store | none |
| (c) | scratch during the smoke, then live | stays up | no `ZP10-` rows | none, under the launcher above |

C10's 12 reads are a Cursor-started job. Its PID is recorded. The phone log is pulled with `run-as com.beebo.zola.companion` on the debug build.

### CP-G12 — State and logs

One app-private file, write to a temp file and rename. First run writes install id, both cursors, and baseline time together. Later writes cover phone `seq`, the PC key, last PC `seq`, the address, the pending set, and the acked-above set. Credential-encrypted storage. A process kill keeps the last rename. A reboot keeps it. Before unlock, nothing runs.

Log file under app-private storage, 1000000 bytes, 3 backups. Fields are hashed ids, counts, kinds, reasons, timings, and states. Logcat tag `zola.companion`, same fields. No body, address, code, or link.

**Idle samples. Recommend sampling on each PC ping.** The ping is every 240000 ms while connected, which is finer than hourly, and it needs no extra alarm. The gap is a disconnect: no ping, no sample. The induced outage is 10 minutes. An hourly `setAndAllowWhileIdle` would cover that gap and cost one wake an hour. Not recommended unless a disconnect longer than an hour has to appear in the idle table.

## Phase 3 — Proposal (STOP, 2026-10-20)

No code changes. This is the proposal Phase 2 recommended, plus the probe correction and the four items below.

### SMS id timeline

The different address hashes and threads on 29006 and 29007 are the two senders. 29006 is the SMS sender. 29007 is the RCS sender. Both are inbox rows.

The last row before the probe cluster is 29002, provider date 1792526572378, about 2 h 20 min before 29006. Ids 28980–29001 are older ordinary traffic and are not in this table. From 29002 through 29007:

| Id | What it was | Type | Address hash | Thread |
|---|---|---|---|---|
| 29002 | Last row before the probes. Not a `ZP10-` text. | 1 inbox | `47648cf20b89fa261a048a5d937cd08d9694ff87b3ac1248d65fa071245b274c` | 1685 |
| 29003 | Absent. Never seen. One of the two ids missing in this span. | — | — | — |
| 29004 | Present. Outgoing (`type` 2) on the RCS sender's thread. Not a `ZP10-` text. | 2 sent | `11fa8cb302978567148d83d35af5f2ee07238883137261f9196adb94afb1a4b4` | 56 |
| 29005 | Absent. Never seen. The other missing id. | — | — | — |
| 29006 | Normal `ZP10-` from the SMS sender. | 1 inbox | `20bc10a373586bd95a5946b574ac9bf42125dae3b9cf8c3e813b4787cb11f536` | 1683 |
| 29007 | Normal `ZP10-` from the RCS sender, stored in the SMS provider. | 1 inbox | `11fa8cb302978567148d83d35af5f2ee07238883137261f9196adb94afb1a4b4` | 56 |

Counts in 28980–29007: 26 ids present, 2 absent (29003, 29005), 2 of the present rows are `ZP10-`. No present row has `spam_report`, `spam_type`, or `block_filtered_status` set.

Brian deleted two texts (the newest `ZP10-` SMS and the newest `ZP10-` RCS) and then the two survivors arrived at 29006 and 29007. Those two new ids are higher than the holes, so the missing ids were not reused. The two absences match the two deletions. There is no third hole. A blocked text that was inserted and later removed would be an extra missing id. There isn't one.

**Did a blocked text ever exist as a row, even briefly?** This probe never saw one. The span accounts for every id as a surviving row or as one of the two deletions. A blocked insert that never committed would also leave no hole. Either way, no blocked row was observed.

**If Google Messages writes a blocked row and removes it later**, the companion still does not send it:

1. The observer is only a wake. The send reads the row again. If it is gone, the phone records a terminal `deleted` outcome and removes the id from pending. It does not send the body, and it does not wait for an ack.
2. If the row is still there and `spam_report` is nonzero, `spam_type` is nonzero, or `block_filtered_status` is non-empty, it is not sendable (`spam` or `blocked`).
3. A row is not acknowledged, and not counted as sent, until that second read says it is an ordinary inbound row.

**C5 proves it.** Block one probe sender. That sender sends one `ZP10-`. After one capture cycle the scratch store has no row for a new provider id from that sender, and the phone log says `blocked`, `spam`, or `deleted` (or no row). Unblock. The same sender sends one `ZP10-`. That one is stored once. A unit test does the same with a fake row: `block_filtered_status` set, then the row removed before send. Neither becomes a frame.

### Discrepancy — build plan Section 4

Section 4 says RCS on this phone is stored as MMS-provider rows. With Google Messages as the default SMS app, the probe's RCS 1:1 is stored in the SMS provider (`content://sms`, id 29007), not the MMS provider. No column marks it as RCS. `rcs_flag` stays `unknown` on SMS-provider rows and on MMS-provider rows that do not prove RCS. `rcs_flag` is `yes` only when a content type proves it. Capture still watches both `content://sms` and `content://mms`. Kind stays `sms` or `mms` from the provider that holds the row.

### MMS id reuse

All three photo messages landed in the MMS provider. Two are still there. The deleted one is gone, and it was not an SMS row.

| MMS id | Provider date (seconds) | What |
|---|---|---|
| 174299 | 1792538474 | `ZP10-` photo MMS. Inbox, `m_type` 132, `ct_t` `application/vnd.wap.multipart.related`, parts `image/jpeg` and `text/plain`, creator `com.google.android.apps.messaging`. |
| 174300, 174301, 174302 | — | Absent. The only run of three missing ids from 174201 through 174309. |
| 174303 | 1792538655 | The later `ZP10-` photo MMS. Same shape as 174299. 181 seconds after it. |

The from-address (`type` 137) stored-form hash is `4a3b1ad87706b3360bd4b9b0c3e75f0ef0fbd21e6070ab42606d46998533ada8`. That is not the SMS row's stored-form hash. Both stored forms are 11 digits, and the US digit key of the MMS from-address matches the digit key of SMS id 29006. Same sender. The key was compared and dropped. It is not recorded.

The part table has two `ZP10-` parts, mids 174299 and 174303, and both parents exist. No orphan part. No `ZP10-` SMS with id above 29007. SMS ids 29008–29013 are present and are not `ZP10-` (RCS sender hash `11fa8cb302978567148d83d35af5f2ee07238883137261f9196adb94afb1a4b4`). From 29002 through 29013 the only holes are still 29003 and 29005. Deleting the photo did not remove an SMS row.

The follow-up id is 174303, higher than 174299. The ids between them are empty, so the follow-up did not take the deleted id. Which of 174300–174302 was the deleted row is not visible: the part is gone with the row. In 174201–174309 there are 87 rows and 22 holes, mostly single holes, and this is the only triple. That is why the triple is the deletion, and why a single hole elsewhere is not.

The MMS id was not reused in this probe. This tests observed reuse only, on this phone, after deleting the newest photo MMS. It does not prove an MMS id stays unique for the life of the provider.

### Reconnect delay by phone state

The backoff stays 10 s, then 30 s, then 60 s (`phone_protocol.json` lines 224–228). One mechanism for every state: `AlarmManager.setExactAndAllowWhileIdle`. A `Handler` is not the reconnect clock. There is no wake-lock fallback. A wake lock is ignored in Doze.

| State | Evidence | What a `Handler` did | Bar |
|---|---|---|---|
| Awake, screen on, or screen off while charging | Findings §6: on the cable the `Handler` fired within about 113 ms of the armed time. | On time | Reconnect within 60 s. Not deep Doze. |
| Unplugged, 10 s step | Phase 6b: a `closed` reconnect armed for 10000 ms was 180 ms late | Close to on time | Within 60 s |
| Unplugged, 30 s step, CPU asleep | Phase 6b: armed `1792267100728`, due 30000 ms later, connect `1792267174461`, 43733 ms late | Misses a 60 s bar | Within 60 s when not in deep Doze |
| Unplugged, light idle | Phase 6: the phone's own `Handler` ping was median 14284.5 ms late and max 339336 ms. | Can miss by minutes | Within 60 s. This is not deep Doze. |
| Deep idle | Phase 6's 12 h run recorded no deep-idle sample. Android defers these alarms in Doze; the documented window is about 9 to 15 minutes. [EXT] https://developer.android.com/develop/background-work/services/alarms | Not measured | C10 criterion 4: within 15 minutes |

C10 criterion 4 is: reconnect within 60 s when the phone is not in deep Doze, and within 15 minutes when it is. Every reconnect logs the idle state at the moment the socket opens: `PowerManager.isDeviceIdleMode` (deep Doze), whether the screen is interactive, and whether it is charging. Counts and states only.

`SCHEDULE_EXACT_ALARM` is not pre-granted. Brian grants Alarms & reminders. If that grant is refused, stop and ask. Do not substitute a wake lock.

The read wake lock stays tag `zola:read`, max 20 s. The send-until-ack wake lock is approved: tag `zola:event`, max 20 s, from the second read until the ack. Release tests cover ack, the 20 s cap, error, and socket loss.

### Delivery state when the PC key changes

Phase 3 left this open. The Phase 4 instruction chose per-PC-identity state. The table below is the proposal that was not adopted.

| Option | What the new PC receives | Smoke |
|---|---|---|
| The install keeps one delivery state. | Pending, incomplete, and unacked rows only. Nothing the scratch PC acknowledged. No new baseline. | Real texts the scratch PC acknowledged during the smoke never reach the live store. They stay on the phone. Brian would be recording that as his decision. |
| Separate delivery state per PC key. | At the live pairing, every still-sendable row since the baseline, including the `ZP10-` rows. | Those `ZP10-` rows enter the live store. Layout (c)'s "no `ZP10-` in the live store" would be dropped. `PHONE_CONVERSATION_HOLD` would hold them. |

How the second option would work, if it is the one kept. Not adopted.

- One install id, one phone `seq`, one baseline. Those stay shared.
- The state file maps the hash of each PC public key to that key's SMS cursor, MMS cursor, pending set, and acked-above set.
- The first `pc_ok` for a key creates that entry with the cursors at the baseline max ids, not at the current max, and with an empty ack set.
- The paired key walks from its own cursor. An ack from the scratch key does not advance the live key.
- The live pairing sends fresh envelopes for every still-sendable row since the baseline, including the `ZP10-` rows.
- Provider reset stops that id space for every key. Lowering one key's cursor would resend ids the store already has. `deleted` and `restored` are properties of the row, so no key sends those rows.

### Sent texts

Approved. Events stay inbound. A history read also returns the phone's own sent texts in that conversation, `direction: "out"`. They are never events, and they are not stored as new items.

### Port 47822

Approved, layout (c). The contract port stays 47821. The scratch launcher is never committed. During the smoke the live companion row stays Not paired. The phone is paired to the scratch instance on 47822. The last cell re-pairs it to the live `zola-phone` on 47821.

Production `main` (`__main__.py`):

```python
def main() -> int:
    if not _acquire():  # mutex Local\ZolaPhone
        return EXIT_ALREADY_RUNNING
    home = os.environ.get("HERMES_HOME") or ""
    if not home:
        return 1
    secret = take_secret()
    home_path = Path(home)
    configure_logging(home_path)
    engine = Engine(home_path, secret)
    try:
        handle = create_pipe(engine.protocol["pipe_name"], first=True)  # \\.\pipe\ZolaPhone
    except Exception:
        return EXIT_ALREADY_RUNNING
    from .runtime import _note

    found = forbidden_loaded()
    _note("zola_phone.start", forbidden=",".join(found) if found else "-")
    stop = threading.Event()
    threading.Thread(target=_watch_parent, daemon=True).start()
    threading.Thread(target=serve_pipe, args=(engine, stop, handle), daemon=True).start()
    port = int(os.environ.get("ZOLA_PHONE_LISTEN_PORT") or engine.protocol["listen_port"])  # residual
    asyncio.run(listen_forever(engine, tailscale_ipv4, port, stop))
    return 0
```

Scratch launcher, same steps, three names changed:

```python
def main() -> int:
    if not _acquire():  # mutex Local\ZolaPhoneScratch
        return EXIT_ALREADY_RUNNING
    home = os.environ.get("HERMES_HOME") or ""
    if not home:
        return 1
    secret = take_secret()
    home_path = Path(home)
    configure_logging(home_path)
    engine = Engine(home_path, secret)
    engine.protocol["pipe_name"] = r"\\.\pipe\ZolaPhoneScratch"
    try:
        handle = create_pipe(engine.protocol["pipe_name"], first=True)
    except Exception:
        return EXIT_ALREADY_RUNNING
    from zola_phone.runtime import _note

    found = forbidden_loaded()
    _note("zola_phone.start", forbidden=",".join(found) if found else "-")
    stop = threading.Event()
    threading.Thread(target=_watch_parent, daemon=True).start()
    threading.Thread(target=serve_pipe, args=(engine, stop, handle), daemon=True).start()
    port = 47822
    asyncio.run(listen_forever(engine, tailscale_ipv4, port, stop))
    return 0
```

The scratch file sits outside the package, so that one import is `zola_phone.runtime` instead of the relative import production `main` uses. The scratch `_acquire` is the production function with the mutex set to `Local\ZolaPhoneScratch`. The scratch process does not read `ZOLA_PHONE_LISTEN_PORT`. Production `main` still does, at line 75. That is the residual. The client never sets it. Assigning `engine.protocol["pipe_name"]` is required: `serve_pipe` creates the next instance from that field (`serve.py` lines 113 and 128). The launch environment sets `HERMES_HOME` to a directory in the scratch folder. The read of `HERMES_HOME` is the same line in both.

Firewall command, not run. Brian adds it. The display name is not the live rule's name. Remove this rule at closeout.

```powershell
New-NetFirewallRule -DisplayName "Zola phone intake scratch" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 47822 -InterfaceAlias "Tailscale" -Profile Any
```

### RCS sender is a smoke prerequisite

C3, C8, and C10 need the RCS sender from this probe, address hash `11fa8cb302978567148d83d35af5f2ee07238883137261f9196adb94afb1a4b4`, to send RCS that Google Messages stores. The SMS sender is hash `20bc10a373586bd95a5946b574ac9bf42125dae3b9cf8c3e813b4787cb11f536`. Group RCS was not stored in the probe. A group MMS is still a C3 cell. A group RCS is recorded only if a `ZP10-` group row appears.

`rcs_flag` stays `unknown` unless a content type proves RCS (`rcs` in the type, or `application/vnd.gsma.`). Kind stays `sms` or `mms` from the provider. Capture watches both.

### Restore margin

A new id is restored when its date is older than the newest delivered text's date in that id space by more than 12 hours (43200000 ms). The margin comes from this phone's rows, walked in id order. "Behind" means the row's date is older than the newest date already seen at a lower id.

| Set | Rows | Behind the running newest | More than 1 day behind, after that set's own date had already reached within 1 day of the newest |
|---|---|---|---|
| SMS, all | 28150 (ids 4–29013) | 17650 | — |
| SMS, Smart Switch | 18157 | 17643 | 1424 rows after id 16931 |
| SMS, not Smart Switch | 9993 | 7 | 0 after id 28998 |
| MMS, all | 149334 (ids 4–174320) | 57517 | — |
| MMS, Smart Switch | 55378 | 55339 | 54899 rows after id 1872 |
| MMS, not Smart Switch | 93956 | 2178 | 0 after id 174207 |
| SMS, last 500 ids | 478 | 0 | — |
| MMS, last 500 ids | 409 | 3, all under 10 s | — |

The seven live SMS gaps are 122626 ms (id 21114), 1 ms (21402), 28291279 ms (25804, 7.86 h), 22448589 ms (25805, 6.24 h), 8713298 ms (25806, 2.42 h), 40 ms (27575), and 33 ms (28349). The three recent MMS gaps are 7000 ms (173943), 1000 ms (173945), and 2000 ms (174119).

SMS rows behind the running newest, by size: under 1 s, 3; 1–5 min, 1; 1 h–1 d, 10; 1–7 d, 73; 7–30 d, 168; over 30 d, 17395. Almost all of the long gaps are Smart Switch. MMS non-Smart-Switch rows behind the running newest include 125 under 10 s and 30 under 60 s, which is the MMS `date` moving, and 1993 over 30 d that sit before id 174207.

Twelve hours is above the largest live gap on this phone (7.86 h) and above the recent MMS movement (7 s). It is below the Smart Switch shape: those 1424 SMS rows and 54899 MMS rows are more than a day behind a newest date that id space had already reached. Smart Switch wrote 18157 SMS rows here, so a restore that appends old dates at new ids is a real event on this phone, not a hypothetical.

### Mask results

The rules in CP-G6 were run on every named sample. 29 `verification_code`, 10 `reset_link`, 2 `unsure`, 20 plain. Failed: 0. The two that missed the old keyword list, `Amazon: 482913` and `Enter 482913 to verify your device`, are M15 and M10.

| # | Sample | Result |
|---|---|---|
| M01 | Your verification code is 482913 | verification_code |
| M02 | G-482913 is your Google verification code | verification_code |
| M03 | OTP 482913 | verification_code |
| M04 | Your OTP is 482913. It expires in 10 minutes. | verification_code |
| M05 | PIN 4829 | verification_code |
| M06 | passcode 482913 | verification_code |
| M07 | one-time password 482913 | verification_code |
| M08 | Use code 482913 to sign in | verification_code |
| M09 | code: AB12CD | verification_code |
| M10 | Enter 482913 to verify your device | verification_code |
| M11 | Msg: 482913 is your code | verification_code |
| M12 | WhatsApp code 482-913 | verification_code |
| M13 | Apple ID code 482913 | verification_code |
| M14 | Microsoft account security code 482913 | verification_code |
| M15 | Amazon: 482913 | verification_code |
| M16 | verification code 482913 do not share | verification_code |
| M17 | Your temporary PIN is 4829 | verification_code |
| M18 | passcode: 48-29-13 | verification_code |
| M19 | Login code 482913 | verification_code |
| M20 | `https://accounts.example/reset?token=aaaaaaaaaaaaaaaaaaaa` | reset_link |
| M21 | `https://id.example/verify/email` | reset_link |
| M22 | `https://id.example/login` | reset_link |
| M23 | `https://id.example/sign-in` | reset_link |
| M24 | `https://id.example/signin/continue` | reset_link |
| M25 | `https://id.example/magic/aaaaaaaaaaaaaaaaaaaa` | reset_link |
| M26 | `https://id.example/auth/callback` | reset_link |
| M27 | `https://id.example/continue?token=abcDEF1234567890abcd` | reset_link |
| M28 | click to reset your password https://id.example/reset | reset_link |
| M29 | 482913 | unsure |
| M30 | AB12CD | unsure |
| M31 | code, then 482913 on the next line | verification_code |
| M32 | OTP, then 482913 on the next line | verification_code |
| M33 | Your code is 482913. | verification_code |
| M34 | verification code 482913 | verification_code |
| M35 | PIN is 482913 for the transfer | verification_code |
| M36 | passcode 482913 expires today | verification_code |
| M37 | `https://example.test/path/token/aaaaaaaaaaaaaaaaaaaa` | reset_link |
| M38 | Use 482913 as the verification code for order discussion | verification_code |
| M39 | one-time code 482913 | verification_code |
| M40 | security code 482913 | verification_code |
| M41 | confirmation code 482913 | verification_code |

| # | Ordinary sample | Result |
|---|---|---|
| O01 | See you at 6:30 | plain |
| O02 | It was $19.99 | plain |
| O03 | Call 555-0100 | plain |
| O04 | 1600 Amphitheatre Parkway | plain |
| O05 | Zip 94043 | plain |
| O06 | Order 100045 | plain |
| O07 | Tracking 1Z999AA10123456784 | plain |
| O08 | Score was 6 to 3 | plain |
| O09 | Meet on 2026-10-21 | plain |
| O10 | `https://video.example/watch?v=abc` | plain |
| O11 | `https://news.example/story/12` | plain |
| O12 | `https://maps.example/place/1` | plain |
| O13 | Table for 2 at 7 | plain |
| O14 | Room 1204 | plain |
| O15 | Gate B12 | plain |
| O16 | The total is 48.29 | plain |
| O17 | Reference 482913 is the invoice | plain |
| O18 | `https://carrier.example/track/1Z999` | plain |
| O19 | Birthday 04/19 | plain |
| O20 | Extension 2048 | plain |

Stay masked, verdict 11: "The gate code is 1948", "Building PIN 1948", "Your order code is AB12CD". Each is `verification_code`.

Rule checks beyond the named set, also passing: "Your code is 48 29 13" (`verification_code`); "482913 to log in"; "482913 login"; "482913 to sign in"; "482913 sign-in"; "verify your device at https://files.example/a" (`reset_link`); the invoice sentence with `contains_otp` set (`verification_code`); "See you at 48 29 13" with no keyword (plain).

### The rest of the proposal

Package `com.beebo.zola.companion`. `versionName` `1.0.0`. SDK 36, JVM 17. Dependencies, all already cached: Gradle 8.13, AGP 8.13.2, Kotlin 2.3.21, OkHttp 5.4.0, `androidx.core:core-ktx` 1.17.0, appcompat 1.7.1, material 1.13.0, junit 4.13.2. No Firebase and no Google Services plugin. Debug keystore, not committed.

Service `remoteMessaging`. Channel "Companion", low importance. Title "Zola companion". Text is the link word only. Started from the app, `BOOT_COMPLETED`, and `MY_PACKAGE_REPLACED`. Nothing before unlock.

Permissions: `READ_SMS`, `RECEIVE_SMS`, `POST_NOTIFICATIONS`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_REMOTE_MESSAGING`, `RECEIVE_BOOT_COMPLETED`, `WAKE_LOCK`, `INTERNET`, `ACCESS_NETWORK_STATE`, `SCHEDULE_EXACT_ALARM`, and the battery-exemption request. No `RECEIVE_MMS`. No Contacts permission.

Capture, cursors, masking, reads, contract v3, pairing screen, and logs are the corrected CP-G4 through CP-G12 sections. In-flight window 4. Incomplete retry 600000 ms and 20 attempts. `read_code` serves only a masked item within 86400000 ms, the extracted value only, or refuses `not_identifiable`. `unsure` refuses. History selector is the shared US digit key, used only to find messages. PC changes (a) through (d). No production change for the scratch port.

Kotlin tests: golden vectors and canonical bytes, PC-direction refusals, pairing MACs, one writer, cursor walk, baseline once, the PC-key case for whichever delivery option is kept, the mask table above including mask-before-truncate, size ceiling, reads, both wake locks released on every path, `read_code` refusals, backoff through an injectable clock, no ping armed, blocked and deleted rows produce no body frame. A provider-reset test stops that id space and does not lower the cursor. A pending row missing at resend becomes terminal `deleted`. Python: the five suites at or above 357 / 134 / 44 / 8 / 29, Track 2 tests on v3, and one test each for v3 accept, the §7a re-check, the accept delay, and the health count log. The APK contains no test key and no `google-services` file. Client checks stay at the Phase 1 counts.

Smoke, in order, on layout (c): C1 through C11, then the live re-pair. C5 is the blocked-row proof above. C10 criterion 4 uses the 60 s / 15 min bars, and the idle state is in the log at every reconnect. C10's 12 reads are a recorded PID. The phone log is pulled with `run-as`.

Risks: the exact-alarm grant is refused, and Phase 4 stops to ask; an MMS id is reused outside what this probe observed and R2 collides; a blocked row appears with none of the three columns set; Samsung stops the service unplugged.

### Verdicts

1. "Approved, with the changes below."
2. "Exact-while-idle alarms. I'll grant Alarms & reminders. If the grant is refused, stop and ask; no wake-lock fallback, since wake locks are ignored in Doze. Android throttles these alarms in Doze (documented as 9 to about 15 minutes), so change C10 criterion 4: reconnect within 60 s when the phone is not in deep Doze, and within 15 minutes when it is. Record the idle state at every reconnect."
3. "Yes to the send-until-ack wake lock, 20 s max, with release tests on every path."
4. "Shared US digit key for history matching, used only to find messages, never stored or sent. Record it as a narrow clarification of P10-D10."
5. "Include my sent texts in history reads only, direction "out". Never as events."
6. "Include group threads when the number is a participant. Count distinct participants, and give each history item an explicit thread id and group flag."
7. "read_code as proposed: extracted value only, masked items only, 24 hours, unsure refuses."
8. Chosen in the Phase 4 instruction. Separate delivery state per PC identity, not per key. The install-owned option and the per-key "how" above were not adopted. The rule that was built is in Phase 4.
9. "Layout (c) on port 47822. I'll add the firewall rule when you show the command. The scratch launcher must do exactly what __main__.main does apart from the port, pipe and mutex names; show the two side by side in the progress doc. Record the existing ZOLA_PHONE_LISTEN_PORT override in production main as a residual."
10. "rcs_flag stays unknown unless a content type proves RCS."
11. "The gate code, building PIN and order code stay masked."

Fixes recorded before Phase 4, then superseded where the Phase 4 instruction says so: provider reset stops that id space and does not lower the cursor; a deleted-before-ack row is terminal `deleted` and the notice is resent until the PC acknowledges it; the 12-hour restore margin is replaced by the creator rule and the 48-hour suspected rule; the mask rules produce the table above.

## Discrepancies

Build plan Section 4 says this phone stores RCS as MMS-provider rows. The 2026-10-20 probe, with Google Messages as the default app, stored the RCS 1:1 in the SMS provider. `rcs_flag` stays `unknown` unless a content type proves RCS. Capture still watches both providers. The photo-MMS probe did not observe an MMS id being reused. That is observed reuse only.

## Residuals

Two adb transports can point at the same phone. Phase 3 queries used the USB serial. The Phase 4 date-row query did not: USB `R5CW81KPB6X` was not attached, and the query used tailnet adb `100.118.148.119:5555`. IPVanish is installed and not running.

Production `__main__.py` line 75 reads `ZOLA_PHONE_LISTEN_PORT` before the contract port. The client does not set it. The scratch launcher does not read it. The override stays in production `main`.

## Phase 4 — Implement (STOP, 2026-10-20)

Nothing was committed. The debug APK was not installed. Phase 5 has not started.

### Item 8, as chosen

Separate delivery state per PC identity, not per key. `zola-phone` creates a random 128-bit id once, beside the key, in `pc_id.txt`. `pc_bind` sends it. The MAC covers the canonical payload, so the id is MAC-checked. `rotate_key` deletes the key file and keeps the id. The phone keeps cursors, pending, unacked, and acknowledged sets per that id. A PC identity the phone has not seen starts with the last 7 days of sendable rows (`604800000` ms), and never further back than the install baseline. The boundary row is included. Scratch and live are different ids, so they have different state. At the live pairing, live receives that 7-day window, including the `ZP10-` rows. `PHONE_CONVERSATION_HOLD` holds them. Layout (c)'s "no `ZP10-` in the live store" is dropped for that pairing.

Brian's amendment of the prompt's smoke line that a text the first instance acknowledged is never resent: a new PC identity does receive those rows when they fall in the 7-day window. A key rotation, same PC identity, keeps state and does not resend. The prompt's "change of PC key delivers exactly those three" test is replaced by the three tests below.

### Restore

Creators of SMS rows on this phone, other than Google Messages and `com.sec.android.easyMover`: `com.microsoft.appmanager` (2), `com.samsung.android.app.sharelive` (1), `com.beebo.zolaassistant` (5), `com.example.avapersonalassistant` (10), `com.android.server.telecom`, `com.google.android.googlequicksearchbox` (2). MMS creators other than Google Messages and easyMover: none. Only `com.sec.android.easyMover` is a phone-migration or restore tool. A row from that creator is `restored` at any date, and it is not sent.

A row older than the newest delivered date in its id space by more than 48 hours (`172800000` ms) is `suspected_restored`. It is not sent. Its id stays in a durable set, is counted in `device.health` and the log, and is not discarded. Releasing those is a later decision. The newest-delivered watermark never moves backward. It stays unset until something is delivered, so nothing is suspected on time until then.

### The 7.86 h, 6.24 h, and 2.42 h rows

These are id-order inversions: the row's `date` is older than the newest `date` already seen on a lower id. They are not a gap between `date` and `date_sent`. Queried over tailnet adb `100.118.148.119:5555` because USB `R5CW81KPB6X` was not attached. All three are Google Messages, not easyMover.

| Id | Type | `date` | `date_sent` | `date` minus `date_sent` | Creator |
|---|---|---|---|---|---|
| 25806 | 1 inbox | 1759191604938 | 1759191603000 | 1938 ms | `com.google.android.apps.messaging` |
| 25805 | 1 inbox | 1759177869647 | 1759177868000 | 1647 ms | `com.google.android.apps.messaging` |
| 25804 | 2 sent | 1759172026957 | 0 | `date_sent` is 0 | `com.google.android.apps.messaging` |

25804 has protocol NULL. The two inbox rows have protocol 0. Recent inbox rows from id 29000 up have `date` 892–7737 ms after `date_sent`. On this sample, SMS `date` is local receipt, a second or so after the sender timestamp in `date_sent`. It is not the carrier timestamp.

P10-D08 says `received_at_ms` is the final provider `date` as local received time. That matches this phone's sample. If a later row stored the carrier timestamp in `date` (`date` equal to `date_sent`, or `date` hours earlier), the 48-hour rule would compare that carrier clock with the newest delivered local date. A carrier clock hours behind could mark a live text `suspected_restored`. These three rows would not: `date` versus `date_sent` is under 2 seconds, the id-order gaps are under 48 hours, and the creator is Google Messages, so the creator rule does not mark them restored.

### C10 criterion 4

Brian's amendment of the build plan's 60 seconds. Targets: within 60 seconds when the phone is not in deep Doze, within 15 minutes when it is. These are qualification targets, not guarantees. Android does not promise either. Every reconnect records the idle state: `PowerManager.isDeviceIdleMode`, whether the screen is interactive, and whether it is charging. The phone does not arm a ping. Reconnect uses an exact-while-idle alarm. If Alarms & reminders is refused, the service does not substitute a wake lock. That grant is checked when the app runs; Phase 4 did not install, so it was not asked.

### Deleted-before-ack

Content-free v3 `messages.deleted`: provider id, kind, revision, outcome `deleted`. The phone keeps the outcome and resends it until the PC acknowledges it. The PC logs the identity hash, stores nothing, and a repeat is `duplicate`. The first ack is `suppressed`.

### Contract and PC

`contract_version` 3, `supported_versions` `[3]`. v2 frames are reason `version`. The contract records the PC id, the 7-day window, the restore creator, the 48-hour suspected margin, and the reconnect targets with `guarantee: false`. Vectors were moved to v3 and re-signed where the old signature still verified. Pairing-mac-bad, bad-signature, unsigned, and version 99 were not blindly re-signed. Canonical vectors cover nested objects, escapes, non-ASCII, emoji, a large integer, and a lone surrogate replaced by U+FFFD.

PC: `pc_id` created once and kept across rotation; `pc_bind` includes it; history results are capped again before they return to serve; `zola_phone.accept` logs the delay; `hello` and `device.health` log counts; `messages.deleted` is logged and not stored.

### Diff summary

Tracked edits, against `43c7bc1c`: `.gitattributes` (jar binary, gradlew lf, bat crlf); `keys.py`, `runtime.py`, `wire.py`, `fake_phone.py`, `test_p10_intake.py`; `phone_protocol.json`; `phone_vectors.json`. 8 files, +388 / −67.

Untracked, and part of this phase: `android-companion/` (Gradle 8.13 wrapper, app sources, unit tests). `local.properties` is gitignored. `zola-architecture/lore/prompts/progress/P10-COMPANION_Progress.md` is this file. Scratch scripts `row_times.py` and `resign_vectors.py` were deleted.

### Dependencies, as resolved

Gradle 8.13 from the local cache. AGP 8.13.2. Kotlin 2.3.21. compile/min/target SDK 36. JVM 17. OkHttp 5.4.0. `androidx.core:core-ktx` 1.17.0. appcompat 1.7.1. material 1.13.0. junit 4.13.2. No Firebase and no Google Services plugin.

`org.json:json:20240303` is `testImplementation` only. The Android unit-test jar stubs `org.json` and returns defaults, so the contract tests needed a real parser. It was not in the cache and was fetched. It is not in the APK.

### Tests and checks

Kotlin `testDebugUnitTest`: `CompanionRulesTest` 10, `Phase4Test` 14, 0 failures. That includes the 41 mask samples, the 7-day window and nothing older, key rotation keeping the same state, canonical bytes, every golden vector through the Kotlin verifier, pairing MACs, one writer, the cursor walk, baseline once, deleted-notice resend, restore and suspected rows, provider reset, the size ceiling, the lone surrogate, reads, both wake-lock release paths, `read_code` refusals, backoff, and no ping.

`assembleDebug` succeeded. The APK has no test-key body and no `google-services` entry. The dex contains the PEM label `BEGIN PUBLIC KEY` because the device key is formatted that way. That label is not a test key.

Python, Hermes venv: `zola_workspace` 357 OK, `zola_memory` 134 OK, `zola_tools` 44 OK, `zola_tts` 8 OK. `zola_phone` ran 33 (the Phase 1 floor was 29, plus the four v3 tests). 31 passed. 2 failed: `test_f4_second_process_refuses_the_pipe_and_mutex` (`poll()` is 2, already running) and `test_isolation_on_the_real_startup_path` (no `zola_phone.start`). Both are the live mutex `Local\ZolaPhone` already being held, so the spawned process exits before it logs a start.

Client: `dotnet build` of `Zola.Client` succeeded, 0 warnings, 0 errors. `Zola.Client.Checks` exit 0. Coverage: lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 38/38, phone 11/11.

Firewall command, not run:

`New-NetFirewallRule -DisplayName "Zola phone intake scratch" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 47822 -InterfaceAlias "Tailscale" -Profile Any`

To continue: "proceed to phase 5"

## Phase 5 fixes F1–F17 from Claude's review

Phase 5 fixes F1–F17 from Claude's review. Claude read every Kotlin file (copied to the scratch `review\` folder), the manifest and Gradle files, the contract v3 diff, `phone_vectors.json`, and the `runtime.py`, `wire.py` and `keys.py` diffs, and four items from ChatGPT's review are folded in (F1, F5, F7, F8). What is right: the pure pieces (masking with mask-before-truncate and `contains_otp`, canonical JSON with the surrogate rule on both sides, the PC verifier order in `Intake.classify`, the pairing MAC, the backoff steps, the restore and suspected rules, the 7-day window in `DeliveryBook`, the atomic `install.json` write, the PC identity created beside the key so the live key file needs no migration, `delay_ms` on the accept log, count-only `hello` and health logs). What is not right: the service does not wire those pieces together. As built, the phone can pair, then sends events the PC must reject, never answers a ping, never reconnects, and forgets its `seq` on restart. The 24 tests pass because they test the pieces, not the app. Apply the fixes below, each with a failing test first where it changes behaviour. Re-run everything and report counts. Nothing else changes.

The service now runs one engine. Pairing, hello, ping, events, acks, reads, deleted notices, provider reset, and reconnect go through that engine. State is one JSON file, written before a frame's seq is used. A refused PC frame is logged and not acted on. Provider reads are bounded. The code is handed to the service in the process, not in an Intent extra.

Verdict on org.json, in Brian's words: "Approved after the fact: org.json:json:20240303, test-only, not in the APK. Record it as a deviation."

`deleted_seen` is capped at 2000 newest hashes. That number is `deleted_seen_limit` in the contract.

### Failing, then passing

The engine-flow test was written before the engine. The first compile of that test failed (`Overload resolution ambiguity` on the clock). After the engine existed, three tests failed: the flow never produced `messages.deleted` (the row's date was ancient against the watermark, so it was suspected), an exhausted row's later completion stayed at revision 1 (the batch query dropped an acked id), and a network-up while the socket was already open did not fail or arm an alarm. Those three then passed. The service compile failed on `PowerManager.isCharging` (charging is on `BatteryManager`) and then succeeded. The shared digit-key test failed to compile (`assertNull` not imported) and then passed.

| Fix | Test that failed first | How it failed | Now |
|---|---|---|---|
| F1 | `reconnectWithoutACodeUsesTheStoredPeer` | First compile: unresolved `CompanionEngine`. After the engine compiled, the alarm assertion failed. `onNetworkUp` did nothing while the socket was still open, so no alarm was armed and the log had no `failure`. | Passes. A reconnect with no code opens the stored address and sends `hello`. A failed connect logs `failure` and arms the next exact alarm. |
| F2 | `pairHelloPingEventAckRestartReconnectReadsAndReset`, `refusedPcFrameIsLoggedAndNotActedOn` | First compile: unresolved engine. On the first compiled run a ping produced a `pong`, and `refusedPcFrame` passed (replay seq 1, nothing sent, log contains `replay` or `refused`). | Passes. Every PC frame goes through `Intake.classify`. A refused frame is logged and not acted on. |
| F3 | `providerRowsCarryTheContractFields`, and the event-field checks in `pairHello…` | First compile: unresolved `TextRecord`. The SMS field checks passed on the first compiled run (`received_at_ms` 11, `is_group` not a boolean). The five-row test was added with the mapping and was not captured red. | Passes. SMS, text MMS, photo MMS, group MMS, and a masked row each carry the contract fields. `is_group`, `truncated`, and `attachment_has` are integers. |
| F4 | `signingUsesTheSamePayloadTheFrameCarries`, `signingFailureSendsNothing` | First compile: unresolved engine. Both passed on the first compiled run. The clock advances on every read and the sent event still verifies. A null signature sends nothing, the log contains `sign`, and the next change sends. | Passes. One map is signed and sent. |
| F5 | the restart section of `pairHello…` | First compile: unresolved engine. On the first compiled run the log showed a history read, a code read, and an ack after restart. The test then failed on the deleted row, so the restarted `hello` seq and the no-resend check had already succeeded. | Passes. A new engine loads the store, `hello` continues the seq, and the acked event is not resent. |
| F6 | `newPcGetsSevenDaysAndRotationKeepsState` | First compile: unresolved engine. Passed on the first compiled run: event ids `{2, 3}`, the same PC id did not resend 2, the new PC id sent 2 and did not send 1. The edge row in this test sits 10 seconds inside the window so the moving clock cannot drop it. The exact boundary stays in `newPcGetsSevenDaysAndNothingOlder`. | Passes. |
| F7 | `providerBatchIsBounded` | First compile: unresolved `TextProvider`. Passed on the first compiled run. The fake provider counted the work: `rowsRead` at most 50, `lastLimit` at most 50, `queries` at least 1, after 100 rows were added. | Passes. Baseline is one `maxId` query. A change reads ids above the cursor plus pending ids, limit 50. |
| F8 | `incompleteExhaustsOnTimeOrAttempts` | `AssertionError` on the revision check. The row became `exhausted` after 600000 ms, and the later completion stayed at revision 1 because the batch query dropped an id once it was acknowledged. | Passes. Exhaustion is the 10-minute bound or 20 attempts. A later completion is a new revision. |
| F9 | the code-read and deleted sections of `pairHello…` | `NoSuchElementException`: no `messages.deleted`. The log line was `suspected` for id 13, because that row's date was the id and the watermark was already a current timestamp. The code read of provider 12 had already returned the value, and the log file did not contain it. | Passes. `code.read.request` reads the named `provider_id` and `kind`. A row removed while in flight sends `messages.deleted` with outcome `deleted` and no body. |
| F10 | `goldenVectorsMatchPythonOrder`, `test_f9_vectors_results_and_local_reasons` | The PC test key and the five PC-signed cases were absent, so both-ways verification had no contract vector. No red run of those new cases was captured before they were signed. After they were added, `decide_case` matched every case. | Passes. 37 vector cases: accept, replay, stale, wrong-device, and bad-signature. Kotlin `DigitKey` and Python `phone_ids.normalize` both pass `digit_key_vectors`. |
| F11 | `test_v3_history_result_is_capped`, `test_deleted_seen_is_bounded` | The old history test only asserted 50 items. It did not assert `capped` or a log line. `deleted_seen` had no bound and no test. The new assertions were added with the change. A red run of them was not captured. | Passes. A 60-item history result has `capped` true and the log contains `kept=50`. `deleted_seen` stays at 2000. A hash that fell out is `suppressed` again. |
| F12 | `oneWriterDoesNotInterleaveFrames`, `EngineFlowTest` | First compile: unresolved `FrameWriter` and `CompanionEngine`. The one-writer test called `FrameOutbox`, which the service never used. It was pointed at `FrameWriter`. No assertion failure of that test was captured. `unitTests.isReturnDefaultValues` is false. | Passes. 40 frames from four threads each parse. The engine test runs pair, hello, ping, event, ack, restart, reconnect, history, code, deleted, and provider reset. 36/36. |
| F13 | `logOmitsBodyAddressAndCode` | First compile: unresolved `PhoneLogFile`. Passed on the first compiled run. The log contained `zola.companion` or `detect`, and did not contain the URL, the sender digits, or the token. | Passes. The file is the metadata log. The service mirrors each line to logcat tag `zola.companion`. |
| F14 | `handoffKeepsTheCodeOutOfTheIntent` | First compile: unresolved `Setup` and `Handoff`. Passed on the first compiled run. `pairIntent` extras are null, `Handoff.code` holds the typed code, and the missing-grant list is `READ_SMS` and `Alarms & reminders`. | Passes. The activity requests `READ_SMS` and `POST_NOTIFICATIONS`, has an Alarms & reminders button, prefills the saved address, and shows paired, connected, and the counts. The code is not put on the start Intent. |
| F15 | none | No product test. The dependency was already `testImplementation`. | Recorded, in Brian's words: "Approved after the fact: org.json:json:20240303, test-only, not in the APK. Record it as a deviation." APK scan: `org.json` 0. |
| F16 | `test_f4_second_process_refuses_the_pipe_and_mutex`, `test_isolation_on_the_real_startup_path` | Phase 4, with the client running: `poll()` was 2 (`EXIT_ALREADY_RUNNING`), and the isolation log had no `zola_phone.start`. | Passes. This run, `Local\ZolaPhone` did not exist and no Zola process was running. Both tests passed inside 36/36. |
| F17 | the bench, B1 to B7 | No unit test. The bench is the check. | The debug APK is installed. The bench table is filled when B1 to B7 finish. |


Final Kotlin run, with `unitTests.isReturnDefaultValues = false`: `CompanionRulesTest` 11, `EngineFlowTest` 11, `Phase4Test` 14, 36 tests, 0 failures. `assembleDebug` succeeded.

### Counts

Kotlin: 36/36.

Python, Hermes venv, Zola client not running. `Local\ZolaPhone` did not exist (`OpenExisting` : no handle of the given name). No process named Zola was running, so there is no PID, name, or parent to record. `zola_phone` 36/36 (the previous 33, plus the deleted-seen bound, the shared digit-key vectors, and the event-required list). `zola_workspace` 357/357. `zola_memory` 134/134. `zola_tools` 44/44. `zola_tts` 8/8.

Client: `dotnet build` of `Zola.Client`, 0 warnings, 0 errors. `dotnet run` of `Zola.Client.Checks`, exit 0. Coverage unchanged: lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 38/38, phone 11/11.

APK scan: `BEGIN PRIVATE KEY` 0, `google-services` 0, `org.json` 0. `BEGIN PUBLIC KEY` 2, which is the device-key label in the dex, not a test key.

The debug APK is installed on USB `R5CW81KPB6X` (versionName 1.0.0, versionCode 1). `READ_SMS` and `POST_NOTIFICATIONS` were not granted at install. The setup screen was opened.

### Diff

Against `43c7bc1c`, tracked: `.gitattributes`; `keys.py`, `runtime.py`, `wire.py`, `fake_phone.py`, `test_p10_intake.py`; `phone_protocol.json`, `phone_test_keys.json`, `phone_vectors.json`. 9 files, +558 / −70. Untracked: `android-companion/`, and this progress file. Nothing committed. Live profile not touched.

### Bench

| Step | Result |
|---|---|
| B1 pairing | not run |
| B2 hello accepted | not run |
| B3 six pings, no pong-missed | not run |
| B4 one SMS and one photo MMS | not run |
| B5 kill without force-stop, no replay, no resend | not run |
| B6 history read and diagnostic read | not run |
| B7 phone log grep of scripted bodies | not run |

Waiting on Brian: grant READ_SMS, notifications, battery, Samsung, and Alarms & reminders; add the firewall rule; pair the scratch `zola-phone` on 47822; then the 30-minute bench. Phase 6 has not started.

Firewall command, not run:

`New-NetFirewallRule -DisplayName "Zola phone intake scratch" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 47822 -InterfaceAlias "Tailscale" -Profile Any`

## Phase 5 fixes R1–R11

Claude's second review. The F1–F17 wiring stays: reconnect from stored state with a signed `hello`, health and resend on connect; every PC frame through `Intake.classify` with the persisted last PC seq and pinned key; pong at once; one payload built, signed and sent; bounded batches above the cursor; all engine work on one background worker; real wake locks released in `finally`; `read_code` by exact identity; the VPN network callback; the bounded metadata log.

`install.json` is the source of the install id, baseline, and initial cursors. A missing state file does not mint a new install. A new pairing exchange checks its own PC seq, and the stored last PC seq is replaced only on `pc_ok`. A new PC's cursors are the current max ids after the 7-day window is collected, and that window is paged. History is newest-first, merged by date, and cut by `max_messages`, `max_characters`, and the frame budget. An ack drains the next waiting items. A second connect is ignored while the first is still connecting. Diagnostic counts are computed. Provider ids in the log are a stable SHA-256 prefix. A failed pairing clears the typed code. The state file stores no message body and no sender.

Pairing gives the PC 30 seconds (`PAIRING_WAIT_MS`) to send `pc_bind`. A bad MAC, a refused pairing frame, a close during pairing, or that timeout clears the code, logs `failed`, and the setup screen shows "Pairing failed".

### Failing, then passing

First engine-flow run, before the fixes, 22 tests, 11 failed. The eleven were the new ones:

| Fix | Test | How it failed | Now |
|---|---|---|---|
| R1 | `stateFileOmitsBodiesAndStaysBounded` | `AssertionError`. The state file contained the sentinel body. | Passes. Slots persist identity, revision, completeness, a fingerprint hash, attempts, times, and flags. A resend rebuilds the payload from `provider.one`. A missing row becomes `messages.deleted`. A complete slot at or below the cursor is removed once acknowledged. After 500 acknowledged texts the file stays under 40 000 bytes and contains neither the bodies nor the senders. |
| R2 | `interruptedSaveKeepsInstallIdentity` | `AssertionError`. `install.json` was not written, so a missing state file was a new install. | Passes. The save replaces the file with `ATOMIC_MOVE` and `REPLACE_EXISTING`. A temp file left beside a good state file keeps the id and baseline. A missing state file with `install.json` present keeps both. |
| R3 | `secondPcPairsWhenItsSeqStartsAtOne` | `AssertionError`. No `phone_bind`. The live PC's `pc_bind` at seq 1 was refused as a replay against last PC seq 500. | Passes. A typed code starts a fresh seq check. The stored last PC seq is written on `pc_ok`. |
| R4 | `newPcReceivesOnlyTheSixtyInTheWindow` | `AssertionError`. The new PC did not receive exactly the 60 in-window texts. | Passes. The window is paged, then the cursors are set to the current max ids. The 20 older texts are not sent. |
| R5 | `historyReturnsNewestWithContractFields`, `historyStaysInsideTheFrameBudget` | Newest-of-one returned the oldest id. The long-text read produced no `history.read.result`. The 11-digit needle was absent. | Passes. Newest first, with `received_at_ms` and `revision`. The character budget marks the result capped. `AddressNeedles` includes the `1XXXXXXXXXX` form. Shared digit-key vectors stay in `digitKeyMatchesTheSharedVectors`. |
| R6 | `sixTextsDrainWhenAcksFreeTheWindow` | `AssertionError`. Six texts and one provider change did not deliver all six. | Passes. Each ack sends the next waiting items. |
| R7 | `connectingIgnoresASecondOpen` | `AssertionError`. An alarm and a network callback while the socket was still connecting opened two. | Passes. The second connect is ignored until the first opens or fails. |
| R8 | `diagnosticCountsRejectionAndLag` | `AssertionError`. `rejected` was 0. | Passes. `rejected` counts rejected acks. `cursor_lag` is max id minus cursor. `rows_since_baseline` counts rows admitted. |
| R9 | `logHashesProviderIdsAndKeepsRequestIds` | `AssertionError`. The log contained the raw provider id. | Passes. The same 16-hex hash is on each line for that row. The request id is unchanged. |
| R10 | `wrongPairingCodeClearsAndDoesNotRetry` | `ComparisonFailure`. The state was not `pairing-failed`, and the next alarm sent again. | Passes. The code is cleared, the log contains `failed`, and the next alarm does not send `phone_open`. |

After those ten passed, `incompleteExhaustsOnTimeOrAttempts` failed: pruning the exhausted slot dropped it from the next batch, so the later completion stayed at revision 1. A non-complete acknowledged slot is kept, and the revision hash is kept, so that completion is a new revision. That test then passed.

### Counts

Kotlin `testDebugUnitTest`, `unitTests.isReturnDefaultValues` false: `CompanionRulesTest` 11, `EngineFlowTest` 22, `Phase4Test` 14. 47 tests, 0 failures.

Python, Hermes venv: `zola_phone` 36/36, `zola_workspace` 357/357, `zola_memory` 134/134, `zola_tools` 44/44, `zola_tts` 8/8.

Client: `dotnet build` of `Zola.Client`, 0 warnings, 0 errors. `dotnet run` of `Zola.Client.Checks`, exit 0. Coverage unchanged: lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 38/38, phone 11/11.

### Diff

Against `43c7bc1c`, tracked: `.gitattributes`; `keys.py`, `runtime.py`, `wire.py`, `fake_phone.py`, `test_p10_intake.py`; `phone_protocol.json`, `phone_test_keys.json`, `phone_vectors.json`. 9 files, +558 / −70. Untracked: `android-companion/` (this round: `CompanionEngine.kt`, `CompanionService.kt`, `EnginePorts.kt`, `Inbox.kt`, `PairingActivity.kt`, `EngineFlowTest.kt`), and this progress file. Nothing committed. Live profile not touched.

### Bench

`adb devices` listed no devices. USB `R5CW81KPB6X` was not attached, so the bench was not started and the new APK was not installed. The previously installed debug APK does not contain R1–R11.

| Step | Result |
|---|---|
| B1 pairing | not run — phone not attached |
| B2 hello accepted | not run |
| B3 six pings, no pong-missed | not run |
| B4 one SMS and one photo MMS | not run |
| B5 kill without force-stop, no replay, no resend | not run |
| B6 history read and diagnostic read | not run |
| B7 phone log grep of scripted bodies | not run |
| B8 state file grep of scripted bodies and test numbers | not run |

Phase 6 has not started.

## Bench attempt after the alarm grant

`SCHEDULE_EXACT_ALARM` is `allow` and stayed `allow` after `adb install -r`. The scratch listener came up on port 47822 with `forbidden=-`. The live profile was not started.

The first unlocked pass typed the scratch address and the PC logged `pairing result=started`. No `hello` followed. The phone log was `disconnect reason=failure`, then `pairing result=failed reason=timeout`. A shell TCP probe to port 47822 reached the listener; the app's own attempts did not. The manifest targets SDK 36 and had no cleartext permit, so `ws://` is rejected before a socket. `android:usesCleartextTraffic="true"` is now on the application tag, and a disconnect log includes the exception class. That APK is installed. The cleartext permit is accepted: Tailscale encrypts the link (P10-D06), and the app connects only to the PC (G-ONE-ROUTE). The retry did not reach that build because the phone was on the lock screen.

The retry found the lock screen, then the PIN pad. `pair_tap` was `setup-screen-missing`. Those shell `content insert` attempts and the denied `SMS_RECEIVED` broadcast left no provider rows. Counts only: scripted SMS body 0, plain probe body 0, test address 0, plus-form address 0, scripted MMS part 0, MMS address 0, MMS plus-form address 0. Later benches do not write to the providers. B4 is two real texts from the SMS-only number.

| Step | Result |
|---|---|
| B1 pairing | not paired. One `pairing result=started`, then timeout. Retry blocked by the PIN screen. |
| B2 hello accepted | no `zola_phone.hello` |
| B3 six pings, no pong-missed | 0 answered, 0 `pong-missed`. The 26 minute wait did not run. |
| B4 one SMS and one photo MMS | not stored. Shell insert returned no URI. Store count 0. |
| B5 kill without force-stop, no replay, no resend | not a reconnect test. The process was killed while unpaired. It came back. No hello, no replay, no extra stored. |
| B6 history read and diagnostic read | both `phone_unavailable` |
| B7 phone log grep of scripted bodies | 0 hits, file readable |
| B8 state file grep of scripted bodies and test numbers | 0 hits, file readable |

Phase 6 has not started.

The Pair control did nothing when the code field was empty: the service was not started, and the status line stayed `stopped`. A blank address or code now stays on screen and the status says which one is missing. A filled tap sets the status to Pairing and starts the service. A new code connects even if an earlier attempt is still connecting. The code field is labeled, the screen scrolls above the keyboard, and `SCHEDULE_EXACT_ALARM` stayed `allow` after the reinstall. The scratch listener was still `waiting-for-pair`.

## Bench on 2026-10-23

Scratch listener on port 47822, `forbidden=-`. The live profile was not started. The phone paired and sent `hello`. Six pings were answered and none were missed. The diagnostic read returned `ok`. The phone log and the state file were readable and the privacy grep was 0 hits in each.

The 20 SMS and 7 MMS figures were a snapshot while the backlog was still draining. The log has 238 distinct `result=stored` accepts (21 SMS, 217 MMS) and the scratch store had those same 238 rows, one each, with none missing. The first kill was `adb shell kill` and did not disconnect the phone.

On 2026-10-25 the same scratch home was started again, with no new pairing code. `run-as com.beebo.zola.companion kill -9` removed pid 24905. The PC logged `disconnect reason=peer-closed who=phone`, pid 23631 came back, and a new `hello` arrived. Replay rejects were 0. No message id has two rows. Four MMS from 2026-10-24 were stored once on that reconnect (store is now 21 SMS and 221 MMS). After the new hello those four were acknowledged `duplicate`, and nothing else was stored.

The history read used the SMS-only number as the selector. It was passed only in the pipe request. Status `ok`, 27 items, not capped, newest first, every `received_at_ms` set, mask violations 0. Three items contain `ZP10-`: MMS `1da00bbc3a17b746`, MMS `a7b4d7f96f64e3cc`, SMS `ada609c4d9c02682`. Mask is omitted on each.

The 16:34 failure is unexplained. The phone file shows `pairing result=handed`, `reconnect socket=open`, `pairing material_bytes=323`, then `pairing result=failed reason=timeout`, and no disconnect line. The PC accepted `phone_open` and no `phone_bind` followed. The close at 16:37:26 has no phone-side reason. Pairing steps are now logged for a repeat: the PC logs each `pc_bind` and `pc_ok` it sends and why it drops a pairing frame, and the phone logs the type of each pairing frame it receives and why it ignores one. Those lines carry no code, key, or MAC.

| Step | Result |
|---|---|
| B1 pairing | paired |
| B2 hello accepted | one `zola_phone.hello` on 2026-10-23, then a second after the real kill |
| B3 six pings, no pong-missed | 6 answered, 0 `pong-missed` |
| B4 one SMS and one photo MMS | 238 distinct stored accepts, 21 SMS and 217 MMS, all present in the store. The 20/7 figure was mid-drain. |
| B5 kill without force-stop, no replay, no resend | `kill -9` via `run-as`. PC disconnect, new pid, new hello, 0 replay, 0 message ids stored twice |
| B6 history read and diagnostic read | diagnostic `ok` on 2026-10-23. History redone: `ok`, 27 items, newest first, `received_at_ms` set, mask violations 0. Three `ZP10-` items, hashes above. |
| B7 phone log grep of bodies | 0 hits, file readable |
| B8 state file grep of bodies and test numbers | 0 hits, file readable |

## Residual — phone mutex tests

`test_isolation_on_the_real_startup_path` and `test_f4_second_process_refuses_the_pipe_and_mutex` need `Local\ZolaPhone` free. On 2026-10-26 the Zola client was running, the mutex was held, and both exited 2. The other 35 `zola_phone` tests passed. On 2026-10-28, with the client closed, the whole `zola_phone` suite passed, 40 tests, and those two are in that run.

## Phase 6 rules before the first cell

Layout (c). C7 uses a scratch-only fault launcher in the scratch folder, the Track 2 shape (`Engine(fault=...)`, `os._exit(1)` at `before_ack`), never `python -m zola_phone`. C10 delivery time counts only texts that arrive during the run, not rows seeded from the 7-day window. The scratch store already holds the bench texts. It stays in `C:\Users\test\Dev\zola-spikes\p10-companion\` and is deleted at closeout. It is not copied anywhere else.

## C1 — code field was clearing

Scratch listener pid 9036 came up on port 47822 with `forbidden=-`. The phone was already paired, and `render` cleared the code field whenever `paired` was true, so typed digits did not stay. `alreadyPairedScreenKeepsDigitsUntilPairIsTapped` failed on that rule, then passed. The field now clears only after Pair is tapped and the phone is paired. The APK is installed (`adb install -r`, Success). `SCHEDULE_EXACT_ALARM` stayed `allow`. The first code was discarded with that listener. Scratch listener pid 18924 came up for the second code. Tapping Pair while the bench session was still connected set the status to pairing, then `save` published `connected` again and `connectIfNeeded` left the open socket in place, so the typed code was not sent. `typedCodeWhileConnectedStartsANewPairing` failed on that, then passed. A typed code now closes the live socket, sends `phone_open`, and a refused code stays on Pairing failed instead of reconnecting. That APK is installed (`adb install -r`, Success). `SCHEDULE_EXACT_ALARM` stayed `allow`. Scratch listener pid 38412, port 47822. The wrong code was refused: `bad-signature` at 08:37:39 (material `d892a27ad8037e69`) and again at 08:38:09 (material `9c4ab71791707280`), with no `pc_bind` between them. The right code then paired at 08:39:08 (`pc_bind`, `pc_ok`). `device_id` hash `6a03b08eafb666106b5bb47633c821ee1ff09b8f3c066189f35d85c863f7041e`, the same hash as the 2026-10-23 bench pair. Scratch status `connected`, socket open, last ping answered. One `hello` followed the new pair.

| Cell | Result |
|---|---|
| C1 | PASS |

## C2 — screen on

A history read did not log the wake lock. `historyReturnsNewestWithContractFields` failed on that, then passed. Each read now logs `wake tag=zola:read result=held` and `result=released`. That APK is installed (`adb install -r`, Success). `SCHEDULE_EXACT_ALARM` stayed `allow`. The SMS-only selector was resolved on the phone (length 12) and was not saved. The four history reads and one diagnostic read start when the cable is out.

Screen on, cable out. Four `read_history` calls through `phone_client`, scratch pipe, max 50 messages. Each returned `ok`, 27 items (22 SMS, 5 MMS), not capped, newest first, every `received_at_ms` set, mask violations 0. The four results were the same order. Durations 1522 ms, 515 ms, 521 ms, 483 ms. The three `ZP10-` items match the bench: MMS `1da00bbc3a17b746`, MMS `a7b4d7f96f64e3cc`, SMS `ada609c4d9c02682`. The scratch store has 2 rows for that sender hash, the same count as B6. Wake-lock lines are on the phone and have not been pulled.

The first diagnostic returned `ok` in 3783 ms and the PC dropped the count fields. `test_diagnostic_result_keeps_counts_only` failed on `pending_incomplete`, then passed. The scratch listener was restarted (pid 45856) and the diagnostic was repeated: `ok` in 355 ms, `pending_incomplete=0`, `exhausted=0`, `unacked=0`, `rejected=0`, `rows_since_baseline=284`, `cursor_lag=227`.

Locked, cable out. Four `read_history` calls, same bounds. Each returned `ok`, 27 items (22 SMS, 5 MMS), not capped, newest first, every `received_at_ms` set, mask violations 0. The order fingerprint matches the screen-on reads (`1f2822296d8687dc`). The same three `ZP10-` hashes. Durations 3228 ms, 646 ms, 629 ms, 615 ms. Diagnostic `ok` in 4101 ms, `pending_incomplete=0`, `exhausted=0`, `unacked=0`, `rejected=0`, `rows_since_baseline=285`, `cursor_lag=154`.

The phone log, pulled while the cable was in, has 11 `wake tag=zola:read result=held` and 11 `result=released`. That is one pair for each read so far: four screen-on history reads, the first diagnostic, the diagnostic redo, four locked history reads, and the locked diagnostic.

The selector is held again (length 12). The two cellular history reads start after the cable is out and Wi-Fi is off.

Cellular, cable out, Wi-Fi off. Two `read_history` calls. Each returned `ok`, 27 items (22 SMS, 5 MMS), not capped, newest first, every `received_at_ms` set, mask violations 0. The order fingerprint matches the screen-on reads (`1f2822296d8687dc`), including the same three `ZP10-` hashes. Durations 1712 ms and 769 ms. After those two reads the phone log has 13 `wake tag=zola:read result=held` and 13 `result=released`, each pair in that order.

| Cell | Result |
|---|---|
| C2 | PASS |

## C3 — text MMS cannot be sent

Brian, 2026-10-26: there is no way to send an MMS without a photo. A text-only MMS will not be produced. C3 will store the SMS, the photo MMS, the RCS 1:1, and the group MMS. The group MMS includes a photo if the composer requires one.

SMS, screen on. One `zola_phone.accept` at 13:52:46 local, `delay_ms=197`, `kind=sms`, `result=stored`, and that item hash appears once. Store row: `ZP10-` body hash `19bc424afe086a4b`, length 11, sender hash matches the SMS-only number, `is_group=0`, `participant_count=1`, no attachment, `detected_at` 2026-10-26T20:52:46Z. The message id has one row. Link was connected.

Photo MMS, screen locked. Accepted 13:53:52, `delay_ms=2449`, `result=stored`, then one `updated` on the same item. One store row, revision 2, `complete`. `ZP10-` body hash `9e1120f61ee40f1e`, length 11, sender hash matches the SMS-only number, `is_group=0`, `participant_count=2`, `attachment_has=1`, `attachment_count=1`, `attachment_kind=image`, `detected_at` 2026-10-26T20:53:53Z.

Group MMS, screen locked. Accepted 13:54:36, `delay_ms=2355`, `result=stored`, then two `updated` lines on the same item. One store row, revision 3, `complete`. `ZP10-` body hash `4027a185d6948842`, length 16, sender hash matches the SMS-only number, `is_group=1`, `participant_count=3`, no attachment, `detected_at` 2026-10-26T20:54:38Z.

A second group row arrived at 13:54:55 from a different sender. It is not a `ZP10-` text. Body length 3, so no body hash is recorded. `is_group=1`, `participant_count=3`, `attachment_kind=other`, revision 3, `complete`, one message id.

Group MMS with a photo, screen locked. Accepted 14:00:26, `delay_ms=606`, `result=stored`, then one `updated` on the same item. One store row, revision 2, `complete`. `ZP10-` body hash `011dee6d39aa1ed7`, length 21, sender hash matches the SMS-only number, `is_group=1`, `participant_count=3`, `attachment_has=1`, `attachment_count=1`, `attachment_kind=image`, `detected_at` 2026-10-26T21:00:27Z.

RCS 1:1, screen locked. Accepted 14:12:59, `delay_ms=3316`, `result=stored`, one accept line. One store row, revision 1, `complete`. `ZP10-` body hash `0d3e2d222d8d2295`, length 11, `is_group=0`, `participant_count=2`, no attachment, `detected_at` 2026-10-26T21:12:56Z. The provider row is `mms`, and `rcs_flag` is `unknown`. `sender_address` is empty. The sender hash is `1cd1739e914f8b6a57fdd936ac50f099cee91f1815b59ebff4301c1076235c31`, which is neither the SMS-only hash nor the RCS hash recorded from the SMS provider during the bench.

| Cell | Result |
|---|---|
| C3 | PASS, with the text-only MMS not produced and this RCS row labeled `unknown` |

## C4 — masking

Four SMS from the SMS-only number, phone unplugged. Each is one store row, revision 1, `complete`, one accept line, body length 0, sender hash matches the SMS-only number.

| Order | Accepted (local) | `delay_ms` | `mask_kind` | Item |
|---|---|---|---|---|
| 1 | 14:19:46 | 292 | `verification_code` | `3359e4cb917b7a37e3e39caa72347cab47698111eeff40132e6b458006626ce7` |
| 2 | 14:19:55 | -499 | `verification_code` | `1c5aaba0fdbb0e675abf3ccf6d352040cdcfba2743cc3bf2c13fecb4e6a7af59` |
| 3 | 14:20:02 | -694 | `verification_code` | `e3784c8940545c9ad1088aabfb996238a856222472789f6d7669321d4d6fcfdc` |
| 4 | 14:20:11 | -736 | `reset_link` | `82dbfc0668d3a951a1c7566c670ec60faab015f164b350a45d2b3fcfb7e65a7c` |

The negative delays are the PC clock minus the phone's `received_at_ms`. Each row was stored once.

One `read_code` for the first row, through the scratch pipe with the scratch launch secret. `phone_client.call` cannot take the message kind, because its first argument is also named `kind`, so the harness built that one request the same way `call` does and sent it on the scratch pipe. Status `ok` in 395 ms. The returned value matched the digit code by hash. The local result did not include `value_kind`. The scratch store and the PC logs have 0 hits for the scripted texts and the values a code read is allowed to return.

Phone log files `companion.log` through `companion.log.3`: 0 hits. Logcat, all buffers, 38,197,147 bytes: the four sentences, the letter code, and the link are absent. The six-digit sequence occurs once, at 13:53:15, as the tail of a longer number on an `io_stats` line. That line is a disk counter from before these texts were sent, and the sequence is not a field of its own.

| Cell | Result |
|---|---|
| C4 | PASS |

## C5 — blocked, then a normal text

Blocked SMS, phone unplugged, link connected. Brian sent it at about 14:30. No accept after the 14:20:11 reset-link row, and no store row after `2026-10-26T21:20:11Z`. The blocked text was not sent.

Normal SMS after unblocking. Accepted 14:32:54, `delay_ms=-654`, `result=stored`, one accept line. One store row, revision 1, `complete`. `ZP10-` body hash `6279e48e58d7b3d4`, length 14, sender hash matches the SMS-only number, `is_group=0`, `participant_count=1`, no mask, `detected_at` 2026-10-26T21:32:54Z. The blocked text is still absent.

No spam row was produced. This phone does not mark spam in a column the app can see.

| Cell | Result |
|---|---|
| C5 | PASS, with no spam row produced |

## C6 — outage

Scratch listener stopped at 14:35:43 local. Processes 43940 and 45856 were killed. The scratch pipe stopped answering. Brian reported all three SMS messages sent at 14:38. At that check the store had no row after the C5 text, and no scratch listener was running.

The listener came back at 14:45:54 (pid 6264), 10 minutes after the stop. All three were stored 22.1 seconds after that restart, in send order, one accept each, `result=stored`. Each row is revision 1, `complete`, one copy, sender hash matches the SMS-only number, body length 9.

| Order | Phone time | Body hash | Item | `delay_ms` |
|---|---|---|---|---|
| 1 | 2026-10-26T21:38:01Z | `9a0970999e763fb3` | `f7b8203e7ed098d305819a301339995c00fe66fe69ea135c8494ba9d6521b51b` | 483357 |
| 2 | 2026-10-26T21:38:16Z | `261b9e9e18e57bff` | `523791b13f0527f811b85beb1c2d2cad7ef87934caf450de717321be85f0e10f` | 468584 |
| 3 | 2026-10-26T21:38:37Z | `d414d668834e5cd6` | `897f01c531b4c59e6e1369a594c3a45cb01e57109a4514e0ad47a8b10bfb53a1` | 448018 |

`delay_ms` is the PC clock minus the phone's `received_at_ms`, so it includes the outage. The catch-up clock is the 22.1 seconds after restart.

| Cell | Result |
|---|---|
| C6 | PASS |

## C7 — ack loss

Scratch-only `fault_serve.py`. It runs the real serving path with `Engine(fault=...)` and calls `os._exit(1)` at `before_ack`. Production `zola_phone/__main__.py` was not used and has no fault argument.

The normal scratch listener was stopped by PID. The fault process, pid 42568, was connected. Brian sent one SMS. The process logged `zola_phone.fault point=before_ack` once and exited 1. That attempt did not log an accept. One store row was already committed: revision 1, `complete`, sender hash matches the SMS-only number, body length 7, body hash `1eb40eff7bfed1aa`, `detected_at` 2026-10-26T21:50:50Z, one message id.

The normal scratch listener came back as pid 45932. The resend logged one `zola_phone.accept`, `result=duplicate`, `delay_ms=32516`. The store still has that one row.

| Cell | Result |
|---|---|
| C7 | PASS |

## C8 — deep idle

Cable attached. `dumpsys battery unplug`, then `dumpsys deviceidle force-idle`. Before the texts: `get deep` returned `IDLE`, `mState=IDLE`, `mLightState=OVERRIDE`, `mScreenOn=false`, `mCharging=false`, AC/USB/wireless powered false. Scratch link was connected.

After both texts, and again after the two reads: `get deep` was still `IDLE`, `mState=IDLE`, `mLightState=OVERRIDE`, screen off, not charging. Then `dumpsys deviceidle unforce` and `dumpsys battery reset`. After the reset: `get deep` `ACTIVE`, `mLightState=ACTIVE`, `mCharging=true`, USB powered true.

SMS, one accept, `delay_ms=1589`, `result=stored`. One row, revision 1, `complete`. Body hash `69705cf1bcb2f0a5`, length 11, sender hash matches the SMS-only number, `is_group=0`, `participant_count=1`, no attachment, `rcs_flag` `unknown`, `detected_at` 2026-10-26T21:54:57Z. Item `497f1633482f99db10129877c64016b81310a246528062b9f7f372f6e908baf8`.

RCS 1:1, one accept, `delay_ms=1728`, `result=stored`. One row, revision 1, `complete`. The stored text is the uppercase form of the scripted RCS text. Body hash `06f16bb157050fa5`, length 11, sender hash `1cd1739e914f8b6a57fdd936ac50f099cee91f1815b59ebff4301c1076235c31` (the same hash as the C3 RCS row), `is_group=0`, `participant_count=2`, no attachment, provider `mms`, `rcs_flag` `unknown`, `detected_at` 2026-10-26T21:55:49Z. Item `fcab5a4ef143ebca0dec2dd0aa9a0dbc7c41b45fde66859a61692b7fe92f3a45`.

Two `read_history` calls for the SMS-only number, while deep idle still held. Both `ok`, 44 items, not capped, mask violations 0. The SMS text was in each result. Durations 2805 ms and 773 ms.

| Cell | Result |
|---|---|
| C8 | PASS |

## C9 — reboot

Baseline at 15:14 local, before the reboot. Scratch link connected. Store floor `2026-10-26T22:11:15Z`.

The link closed at 15:16:22 (`peer-closed`, who=phone). The SMS is provider id 29068, inbox, 86 seconds after boot, body hash `59d8bef2276c6388`, length 7. Brian sent it before unlock. The companion process did not exist yet. It started about 129 seconds after boot, `createdFromFg=false`, foreground, pid 19780. The app was not opened.

Hello at 15:18:11 had `pending_incomplete=0`. The text was stored at 15:30:34, one accept, `result=stored`, `delay_ms=785676`. One row, revision 1, `complete`, sender hash matches the SMS-only number, `is_group=0`, `participant_count=1`, `detected_at` 2026-10-26T22:17:28Z. Item `824ac8e6d3ee1953cd238fba69f30241509b968ef3c8d7d7e1af4f7e7cf4324b`. The phone log shows `detect`, `send`, and `ack result=stored` for that id after `reconnect socket=open`. The 13 minutes are the wait from the provider timestamp until that later scan. `boot()` does not read the provider. The next scan is `onProviderChanged`.

| Cell | Result |
|---|---|
| C9 | PASS, delivered after unlock, not on the first hello |

## C10 — 12 hours unplugged

Cable out at 20:57:57 local on 2026-10-26. The job exited 0 at 08:18:01 local on 2026-10-27, when the 12th history read finished. That span is 11 h 20 m, short of the 12 h window. `dumpsys batterystats --reset` had returned 0 at 20:56, before the cable came out. The pre-reset dump kept device-wide discharge lines only.

Fifteen marked rows, each one id, all `complete`. Six SMS (`S1`–`S6`) from the SMS-only sender. Four photo MMS (`M1`–`M4`) from that sender; `M2`, `M3`, and `M4` were stored then updated, revision 2. One group MMS (`G1`) from that sender, revision 2, no attachment. `R1` and `R2` are MMS, no attachment, sender hash prefix `b79a8100f2370cd5`. `R3` is MMS, no attachment, the C3 RCS sender. The stored `R3` text has one character after the label. `R4` is SMS, the bench RCS sender, delay 14044 ms. Accepts for the marked rows: one `stored` each, plus `updated` on `G1`, `M2`, `M3`, and `M4`. No `duplicate`.

Marked-text delays, connected state, milliseconds: -207, 212, 212, 853, 976, 1269, 1468, 1534, 1680, 1940, 2495, 2881, 3521, 5630, 14044. Thirteen of fifteen are at or under 5 s. The 90th is 5630 ms (`R1`). The max is 14044 ms (`R4`), under 120 s. Criterion 3 does not meet p90 ≤ 5 s.

### Delivery split, before any fix

All 44 inbound texts, not only the marked ones. Phone `detect` is immediately followed by `send` on every one of them (the next log line, one turn). The PC frame line is 2–17 ms before the accept line on every one of them. `sent_at_ms` was not logged, and the night’s logcat is gone, so detect and send have no timestamps of their own. The seconds in `delay_ms` are the provider date until the frame reached the PC.

Eight texts are over 5 s. Idle is `device_idle` at the provider date. Screen is the display state then.

| Provider time | Kind | Text | Idle | Screen | To PC frame | PC work |
|---|---|---|---|---|---|---|
| 20:59:14 | mms | other | neither | off | 8325 ms | 3 ms |
| 22:47:41 | mms | other | light | off | 20438 ms | 4 ms |
| 23:21:52 | mms | ZP10-C10-R1 | light | off | 5619 ms | 11 ms |
| 00:38:49 | mms | other | light | off | 7607 ms | 6 ms |
| 06:15:08 | mms | other | light | off | 8364 ms | 14 ms |
| 06:31:25 | mms | other | neither | off | 6529 ms | 4 ms |
| 06:46:51 | sms | ZP10-C10-R4 | neither | on | 14040 ms | 4 ms |
| 06:48:34 | mms | other | neither | on | 10729 ms | 3 ms |

Four of the eight were light idle with the screen off. Four were not in device idle, and two of those had the screen on. None of the eight were in deep idle. The only two texts that arrived during deep idle took 2515 ms and 398 ms. The 22:47:41 provider date is already 22 s after `date_sent`; the 20.4 s is after the provider date. `R4`’s provider date is 1.7 s after `date_sent`. The other six have no earlier sent time.

Stopped here. No code change.

### Link state and logcat, still before any fix

The link was up at the provider time of all eight slow texts. Ping interval is 240 s. The only down interval in the run is the killed listener, 02:57:58 until the new process opened at 03:08:06. No slow text and no marked text falls in that interval.

Nearest PC link events:

| Provider time | Connected | Previous link event | Next link event | Last ping before it |
|---|---|---|---|---|
| 20:59:14 | yes | open 15:18:10 after disconnect 15:16:22 | open 03:08:06 | 20:55:58 (196 s) |
| 22:47:41 | yes | open 15:18:10 | open 03:08:06 | health at 22:47:41 |
| 23:21:52 | yes | open 15:18:10 | open 03:08:06 | 23:20:11 (101 s) |
| 00:38:49 | yes | open 15:18:10 | open 03:08:06 | 00:36:18 (151 s) |
| 06:15:08 | yes | open 03:08:06 | none through 08:18 | 06:12:27 (161 s) |
| 06:31:25 | yes | open 03:08:06 | none through 08:18 | 06:28:27 (178 s) |
| 06:46:51 | yes | open 03:08:06 | none through 08:18 | 06:44:28 (143 s) |
| 06:48:34 | yes | open 03:08:06 | none through 08:18 | 06:48:29 (5 s) |

Fifteen marked texts went into the connected-state p90. None arrived while the link was down, so dropping disconnected texts would not change that set. The 90th remains `R1` at 5630 ms. `R4` at 14044 ms is also connected-state.

Logcat main, system, radio, and events now begin at 09:13:11. They contain no `detect` or `incomplete` line, and no line from 06:45–06:47. `prev_dump.log` is from the 15:16 reboot and has neither. The observer callback is not logged: `onChange` only posts `onProviderChanged` onto the worker. The first logged sight of a row is `detect` or `incomplete`.

In the untimed phone file, seven of the eight slow texts are `detect`, `send`, `ack` only. No `incomplete` line, and the provider date still matches the one stored payload, so there is no logged download interval before completion and no recorded date change. The 22:47 MMS is the exception: `detect`, `send`, `detect`, `send`, and one phone `ack`. The PC stored it at 22:47:39.442 (`delay_ms` 20442, payload date about 22:47:19) and updated it at 22:47:39.816 (`delay_ms` 816, payload date about 22:47:39). Both sights were complete. The date moved about 20 s between them. That 20.4 s is the early date against the clock, not time spent incomplete.

`R4` has the same single `detect` / `send` / `ack` shape, and its provider date still matches the payload. Logcat cannot show the 06:45–06:47 observer, worker, or radio lines. Battery history, a different record, shows Wi-Fi `disconn` at 06:44:25, then `data_conn=nr` and `conn=CONNECTED`. The PC ping at 06:44:28 got through after that drop, and the frame arrived at 06:47:05. The screen turned on at 06:46:02 and off at 06:47:10. No PC reconnect in that minute.

Brian's amendment to criterion 3, in his words: "Delivery is reported two ways. End-to-end runs from the final provider date to the PC accept and is reported, not graded. Companion time runs from when the phone first saw the complete text to the PC accept, and the 5-second p90 and 120-second max apply to companion time."

The first window above stays graded on the old bar and stays not passed. Companion time for a later window is the `seen` line whose completeness is `complete`, through the PC accept. A row whose only `seen` line is `incomplete` has no later complete timestamp, so it is reported end-to-end and left out of the companion-time grade.

Approved fixes, in on 2026-10-27. Each test failed first. Phone log lines now start with a millisecond clock. Each scan trigger logs `scan` with no ids. The first sight of a row logs `seen` once, complete or incomplete. Each PC ping logs deep, light, screen interactive, and charging. No extra alarm. The harness writes `who=pc reason=pc-shutdown induced=true` to its own log before an induced kill. Companion unit tests 59/59. The induced-line test passed after the missing module failed the import. The new debug build was installed at 11:12:41, before the passive window.

All inbound rows in the provider window: 10 SMS inbox and 34 MMS inbox, 0 with a spam or blocked column set. The store has those same 44 ids, each once. The phone log after the last pre-window text has a `detect` for all 44. Five of the stored rows were then `updated` (revision 2). Accepts: 44 `stored`, 5 `updated`, 0 `duplicate`.

The induced outage stopped listener pids 40300 and 45932 at 02:57:58. The new listener pid 20072 was connected 9.0 s after it started, at 03:08:07, with a hello (`pending_incomplete=0`). The killed process did not write a disconnect line. No other PC disconnect landed in the window. In the phone log the outage is one cluster: `peer-closed` who=phone, then six `failure` who=phone, each followed by a reconnect alarm, then `reconnect socket=open`. Every alarm in that cluster is `deep=true`, `interactive=false`, `charging=false`. Nothing else in the phone log through plug-in is a disconnect. Criterion 4 is short because the PC kill has no reason line on the PC side.

Twelve `read_history` calls, all `ok`, mask violations 0. Durations ms: 2327, 4434, 1976, 4111, 3844, 4880, 1029, 4852, 1119, 1596, 4056, 4045. Median 3945 ms, max 4880 ms. Spike band was 2.8–13.4 s. The first returned 46 items; the rest returned 50, `capped` false. The phone log in the same span has 12 `read` lines.

Battery since the 20:56 reset, estimated power: companion uid 10299 (`u0a299`) 1.16 mAh, all background; Tailscale uid 10058 (`u0a58`) 3.94 mAh, all background. Both are under the 2 mAh and 10 mAh caps. The spike figures were 0.485 and 4.67. These are UID estimates since the reset, not a clean 12 h unplugged integral. Charge history: setup plug 20:56:46 to 20:57:57; bedtime plug 23:58:29 to 23:59:08 (39 s, plug=ac); end plug 08:36:34. Brian reports no heat, no slowness, and no noticeable drain. He had already described the bedtime plug as a few seconds.

The companion process was still pid 19780 at 08:40, foreground, `createdFromFg=false`, `createTime` about 17 h 21 m earlier (the C9 boot). No crash line on that service record. `lastStartId=8`.

Idle: the companion does not log an hourly deep/light sample. The only samples in the span are the seven outage alarms, all deep idle, screen off, not charging. Device-wide stats since the reset include 444 mAh light-doze discharge and 365 mAh deep-doze discharge. Criterion 8's hourly samples were not recorded.

| Cell | Result |
|---|---|
| C10 | Scored below. The 201 s reconnect is the measurement. The pass under the 2026-10-28 amendment is the later cell. |

### Passive rerun, scored

Clock 2026-10-27 11:23:51 to 17:23:59 local, 6 h 8 s. Battery history shows `plug=none` and `status=discharging` at 11:23:52. The next plug is 17:36:28, after the window. Brian plugged in then and reported no heat and no slowness. No scripted `ZP10-` marker in the phone log, the PC log, or the harness log.

Provider inbox in the window: 1 SMS and 26 MMS, 0 with a spam or blocked column set. PC accepts: 27 `stored`, 6 `updated`, 0 `duplicate`. The phone log has a `seen` and a `detect` for all 27. `scan` lines: 318. The same arm-time sender stayed ahead, 13 texts when the reads began and 20 at the close.

Companion time, connected state, 15 texts whose first `seen` was `complete` while the link was up. Sorted values sit between −1216 ms and −981 ms. The 90th is −1018 ms. The max is −981 ms. None are over 5 s. That tight negative band is the phone log clock reading about a second later than the PC accept clock on deliveries that were immediate. End-to-end for those 15 is reported and not graded: two are over 5 s (5802 ms and 10494 ms), and the rest are under 5 s.

Three more texts were first seen `complete` while the listener was down (14:25:59, 14:28:41, 14:29:21) and were accepted at the 14:37:15 hello. Their companion times are 473805 ms, 513668 ms, and 674984 ms. They are the outage catch-up, not part of the connected-state grade. Nine texts were first seen `incomplete`, so they stay out of the companion-time grade. Their end-to-end times run from −319 ms to 2723 ms.

The harness wrote `who=pc reason=pc-shutdown induced=true` at 14:23:51.550, before the kill. The phone logged `peer-closed` who=phone at 14:23:53, then eight `failure` who=phone through 14:36:15. Every reconnect alarm in that cluster is `deep=false`, `interactive=false`, `charging=false`. The new listener logged `start` at 14:33:53.928. The socket opened and the hello arrived at 14:37:14.530, 201 s after the process was back, past the 60 s bar. Socket-down after that 10-minute outage is 201 s, 0.93% of the window. No other disconnect in the window.

Twelve `read_history` calls, one minute apart from 15:19:35, all `ok`, mask violations 0, `capped` false, 50 items each. Durations ms: 5646, 5697, 4734, 3843, 3612, 3318, 3395, 3327, 3193, 3123, 3129, 3242. Median 3323 ms, max 5697 ms. Spike band was 2.8–13.4 s.

Battery since the arm-time reset, estimated power: companion uid 10299 (`u0a299`) 0.627 mAh (background 0.409, foreground-service 0.134); Tailscale uid 10058 (`u0a58`) 2.37 mAh, all background. Both are under the 2 mAh and 10 mAh caps. The reset was a few minutes before cable-out, and the dump was a few minutes after the 17:36 plug, so this is not a pure unplugged integral. The companion process was still pid 14962, the process started at the 11:12 install.

Idle samples on the phone log match all 86 answered PC pings in the window. None were charging. Light and screen off: 39. Screen on and not idle: 25. Neither idle nor screen on: 12. Light and screen on: 8. Deep idle and screen off: 2.

| Criterion | Result |
|---|---|
| 1 Completeness | PASS. 27 inbox, 0 exclusions, 27 stored. |
| 2 Duplicates | PASS. 0 duplicate accepts. 6 updates are revisions. |
| 3 Companion time | PASS on connected state. p90 −1018 ms, max −981 ms, 15 texts. Three outage texts are outside that grade. |
| 4 Reconnect | PASS under the 2026-10-28 amendment. 201 s, screen off, on battery, inside 15 minutes. |
| 5 Reads | PASS on the first window. 12/12, median 3945 ms, max 4880 ms, mask violations 0. |
| 6 Battery | PASS on the first window. Companion 1.16 mAh, Tailscale 3.94 mAh. No heat, no slowness. The 39 s bedtime charge and the 11 h 20 m span stay in that record. |
| 7 Survival | PASS on the first window. pid 19780 stayed up from the C9 boot through that window. |
| 8 Idle | PASS on the 6-hour rerun. 86/86 pings have deep, light, screen, and charging. Deep idle was 2 samples. |

### C10 passed under amendments

Brian's amendment to criterion 4, in his words: "Android throttles while-idle alarms whenever the screen is off on battery, not only in deep Doze. Reconnect after a PC-side outage must happen within 60 seconds when the screen is on or the phone is charging, and within 15 minutes when the screen is off on battery. These are qualification targets, not guarantees."

C10 is passed under three amendments. The window is the 6-hour rerun, not the original 12 hours. Delivery is companion time, and end-to-end stays reported. Reconnect uses the screen-off-on-battery bar above: the rerun's 201 seconds, screen off, on battery, is inside 15 minutes. Survival, battery, and reads are taken from the first window. Completeness, duplicates, companion time, reconnect, and idle samples are taken from the 6-hour rerun.

| Cell | Result |
|---|---|
| C10 | PASSED under Brian's amendments. 6-hour rerun for completeness, duplicates, companion time, reconnect, and idle. First window for survival, battery, and reads. |

## C11 — change of PC key

The first scratch listener, pids 9300 and 28928, was stopped. A second scratch instance is pid 47884, home `hermes-home-c11`, port 47822. Its PC identity hash differs from the first home. At arm time the new store had 0 phone rows. The first home's 547 phone rows were not copied. The two texts were reported on the phone at 07:26. The phone was not on USB, so the provider rows were not read.

Pairing completed at 07:29:16.617 (`result=paired`). Hello at 07:29:16.733, `pending_incomplete=0`. The link stayed up: pings answered at 07:33:17 and 07:37:17. Seven `bad-signature` rejects from 07:22:50 through 07:28:23 are the phone opening the new listener before the code was accepted.

Scored against the Phase 4 amendment: a new PC identity receives the still-sendable rows in the 7-day window, including rows the first instance acknowledged. The two new texts must arrive once, and the MMS must be complete. Pending and unacked must return to 0.

The first home has 61 SMS and 480 MMS whose provider dates fall in the seven days before 07:36 local. The new store received 4 SMS, all `stored`, 0 `updated`, 0 `duplicate`, 0 MMS. Each of the four is already in the first home. Their provider dates are 2026-10-21 15:32:28Z, 16:03:03Z, 17:34:21Z, and 20:27:43Z, the oldest SMS in that window. Accept delays are 601016549, 599182230, 593703770, and 583301842 ms. Neither marked text is in the new store. Health after the four acks stepped `unacked` 3, 2, 1, 0 at 07:29:28, with `pending_incomplete=0` and `exhausted=0`. Nothing further arrived. The phone was still not on USB, so `companion.log` was not read.

| Cell | Result |
|---|---|
| C11 | NOT PASSED. Pairing, hello, and the idle counts passed. The 7-day window and both new texts did not. 4 of 541 first-home rows in the window arrived, the oldest SMS only. Track stopped. |

### Cause, from the phone log after USB returned

`companion.log` for 07:20–07:41, same process pid 14962. The seed admitted the window, then a reconnect alarm reloaded those slots from disk with empty payloads before the four acks, and `drain` sends only a slot whose payload is still in memory.

Before pairing, the only first sights are two rows: seen and sent at 07:25:29.902 and 07:26:00.138. Both were resent on the 07:26, 07:27, and 07:28 reconnects. None of those sends was acked. They are the two slots still `in_flight` on the first PC identity, dated 07:25:28 and 07:26:00. The socket those sends used was the new listener, which answered `bad-signature` and `peer-closed` until the code was accepted.

`pc_ok` at 07:29:17.497 ran the seed. Pending was then cleared. By 07:29:26.584 the phone had sent four `messages.event` frames, the four oldest SMS, and had logged `seen` for six rows. It kept admitting. At 07:29:28.970 the seen count was 541 events, 539 distinct rows, including both early rows again under the new PC identity. The state file now has that identity at pending 0, acknowledged 4, and 535 complete slots, none in flight and none acked: 54 SMS and 481 MMS, dates from 2026-10-21 10:09 local through 07:26:00. Nothing after the four seed sends tried to send again. The two early rows are in that 535, not in the four acks.

The line at 07:29:28.970 is `reconnect deep=false interactive=true charging=false`, which is `onAlarm`, 64 s after the 07:28:24.867 `peer-closed`. `ReconnectReceiver` starts the service with `ACTION_RECONNECT`. That start has no pairing code, so `onStartCommand` calls `boot()` and then `onAlarm`. `boot` calls `load`, which rebuilds every slot from `companion-state.json`. The file stores no payload, so the rebuilt slots have an empty payload. The four acks are the next worker tasks, at 07:29:28.986 through 07:29:29.345. `drain` keeps a waiting slot only when `payload` is non-empty, so it sent nothing, and health stepped 3, 2, 1, 0. The link was already open, so `connectIfNeeded` did not call `resendInFlight`. A ping does not drain. The 535 slots are still waiting.

R4 (`newPcReceivesOnlyTheSixtyInTheWindow`) admits 60 in-window SMS, and R6 (`sixTextsDrainWhenAcksFreeTheWindow`) admits 6. Both are above the in-flight cap of 4. `ackNewEvents` calls `replySigned`, which calls `onMessage` on the same thread after the seed or the provider change has returned. No alarm and no `boot` run in between, so the queued slots still hold the payloads `admit` attached, and each ack's `drain` sends the next slot. That is why those tests pass.

### Fix, approved 2026-10-28

Each check failed before the engine change, then the suite passed.

`boot` loads the state file once per process. A later service start publishes, connects if needed, and drains when the link is already open. It does not call `load` again. `serviceStartBeforeAcksStillDeliversTheWindow` seeds 8 texts, calls `boot` before the acks, then acks one at a time.

`drain` rebuilds a waiting slot from the provider row when the in-memory payload is empty, the same read `resendInFlight` uses. A missing row becomes `messages.deleted`. `coldStartSendsWaitingSlotsThatHaveNoPayload` loads four complete slots with `in_flight` cleared and one provider row gone.

Every verified PC frame, including a ping, calls `drain`, and so does connect when the in-flight window has room. `pingSendsWaitingSlotsWhenNoAckIsPending` leaves three slots waiting after a sign failure and sends them on the next ping.

`asynchronousAcksInterleaveWithAlarmsAndAProviderChange` posts acks from another thread through one worker, with a service start, alarms, and a second provider change, and requires all 12 texts.

`testDebugUnitTest`: `CompanionRulesTest` 12, `EngineFlowTest` 37, `Phase4Test` 14. 63 tests, 0 failures.

The debug APK was installed. The previous scratch listener was stopped. A fresh home, `hermes-home-c11b`, is listener pid 39240, port 47822. At arm time it had 0 phone rows and a PC identity different from the first home.

### Fresh-home rerun, scored

Pairing completed at 2026-10-28 08:33:08 (`result=paired`). The store climbed while the in-flight count stayed at 4, then settled. Two later polls matched: 542 phone rows, all `complete`, all revision 1. Accepts: 542 `stored`, 0 `updated`, 0 `duplicate`. Health: `unacked=0`, `pending_incomplete=0`, `exhausted=0`.

By source: 57 SMS and 485 MMS. The SMS marker arrived once. The MMS marker arrived once, `complete`, with one image attachment. Neither marker is in the first home.

The first home has 540 phone rows whose provider dates fall in the seven days before 08:33 local (60 SMS and 480 MMS), all `complete`. 536 of those are in the new store. The other 4 are verification-code SMS. After the pair the phone log has `seen` for 57 SMS and 485 MMS, `send` for 542, and no `suspected` or `deleted` line. Those 4 hashes are absent from that span. Three other verification-code SMS and both reset-link MMS from the same window are in the new store, so that class was delivered when it was still sendable. The new store also has 6 rows the first home never had (1 SMS and 5 MMS), all inside the window. That is the two markers plus four more texts that arrived after the first home closed.

| Cell | Result |
|---|---|
| C11 | PASSED. The new PC identity received the still-sendable 7-day rows, including rows the first home had already acknowledged. Both new texts arrived once, and the MMS is complete with its attachment. Pending and unacked returned to 0. |

### Provider check before Part B

Read-only. The four verification-code SMS present in the first home and absent from the fresh store were queried on the phone by provider id, projection `_id` only. 0 of 4 returned a row. The same query against one SMS the fresh store has returned 1 row, so the read can see the provider. Those four ids are gone. No code change.

Scratch listener pid 39240 (child 39904), the pairing harnesses pids 48588 and 36892, and the earlier harness pid 15124 were stopped. Port 47822 had no listener. The live client was closed before the mirror.

## Part B — live profile

No Zola client, serve, watcher, or `zola-phone` was running. The backup is `C:\Users\test\Dev\zola-spikes\p10-companion\live-backup-partb\`. `proactive.db` was copied with the SQLite backup API. SHA-256 `E4743A0108795C8E73DDA6E37D5BC359F6DD8165131F53F3DA9F09EC4163B68F`, 1171456 bytes. Phone rows in that backup: 0. Other tables: `calendar_events` 1070, `cursors` 5, `deliveries` 0, `item_attempts` 400, `items` 414, `loops` 9, `meta` 7, `phone_tombstones` 1, `watcher_health` 1, `watcher_rejects` 1.

Mirrored files match the worktree. `phone_test_keys.json` is absent from the live profile. Tests were not copied.

| File | Backup SHA-256 | Live SHA-256 |
|---|---|---|
| `zola_phone/keys.py` | `92B1FF814E6D7BF9C87A2AD2A13A1AD1569718DB64057B2D62A2C1CDBB04AC91` | `FDF08A0CA4C70E762831403921600E84F0DB8B8C6A58F2ACFF1ED725EB0FB790` |
| `zola_phone/runtime.py` | `8C6047C7B742D1C9B4AC8BF8153E6D9770508E712FAB0B8A1C146CED145D4D46` | `DA2C60CE9343B091FB4F59417FCC0C1B113B90C96BA37AC2F5EDEA83AB5FDA54` |
| `zola_phone/serve.py` | `0D3499EE7448B3EFE89E61395E32D06FAB2D2210D6E8DE89CE722136EA8C6C5C` | `4C631CC8B5246694CA94FEAEA32AEAAE48F8633B141E6A60B62490460803011C` |
| `zola_phone/wire.py` | `D67DDF8C7D947E20F701ECF9BBDAD7B518AEA7116B64C573DE7F2E66A994A3EE` | `B058A6D49A49D311FCF02D856A256881E3D13336EAA1599F95DF33BFD5356B1A` |
| `zola_workspace/contracts/phone_protocol.json` | `2A4A5A21445F5B495AA6531F6CA8157161987B253970746C87C5B32B54FACCA7` | `1D2FB8C950409025E80A1548013EF18B3BB0847713E6EC4DA5992D5BA28AAAB6` |
| `zola_workspace/contracts/phone_vectors.json` | `C0C51CFA34A8E1D3229175B5D46DD95E2346A477EE1675EEA02D735C000EEC81` | `518E52E63C3D83F01BD080AA3EF7EF6B20F770A59C82A85152903DF672CEAA3B` |

The mirrored contract listens on port 47821 and pipe `\\.\pipe\ZolaPhone`.

The worktree client is running. One client, one serve, one watcher, and one `zola-phone`, each Python service as the launcher and its interpreter.

| Process | PID | Parent | Start |
|---|---|---|---|
| client | 24400 | 43688, then exited | 09:02:31 |
| serve | 33796, interpreter 13268 | 24400 | 09:02:32 |
| watcher | 27008, interpreter 39988 | 24400 | 09:02:32 |
| zola-phone | 45868, interpreter 48904 | 24400 | 09:02:32 |

`zola_phone.start` at 09:02:32, `forbidden=-`. The interpreter is listening on `100.102.206.71:47821` only. Port 47822 is free. Pipe status: `link_state=not_paired`, `paired=false`, `socket_open=false`. The phone's saved address is still port 47822.

The scratch firewall rule is still listed, twice, both enabled inbound Allow. Shown, not run:

`Remove-NetFirewallRule -DisplayName "Zola phone intake scratch"`

### Live pair, scored

Pairing completed at 2026-10-28 09:06:43. The device hash matches the C1 hash. One `hello`. The store climbed with `unacked` at 4, then three polls matched.

541 phone rows, all `complete`, all revision 1, each `(source, message_id)` once. Accepts: 541 `stored`, 0 `updated`, 0 `duplicate`. Health: `unacked=0`, `pending_incomplete=0`, `exhausted=0`. By kind: 56 SMS and 485 MMS. The SMS marker is present once. The MMS marker is present once, `complete`, with one image.

The fresh home had 542 rows. The one absent from the live store is an SMS whose provider date is 2026-10-21 16:03:03Z, three minutes before this pair's 7-day floor (09:06:43 local). Nothing inside the floor is missing. Nothing in the live store is outside it.

Backup tables are unchanged except the watcher's Gmail activity: `gmail` 384 to 385, `item_attempts` 400 to 401, `items` 414 to 956 (415 non-phone plus 541 phone).

Live logs (`agent`, `errors`, `gui`, `zola_memory`, `zola_phone`, `zola_tools`, `zola_watcher`, `zola_workspace`) and the phone log, including `companion.log.1` through `.3`: 0 hits for the scripted markers, `body=`, `address=`, `sender_raw=`, a private or public key block, or `phone_test_keys`.

Closeout has not started.

## After Part B — C3, C4, C9

Part B passed. Three items before the smoke call.

### C9 — scan above the cursor

`serviceStartScansAboveTheCursor` and `verifiedConnectScansAboveTheCursor` failed first. A service start now reads one bounded batch above each cursor, the same read as `onProviderChanged`, and so does a verified reconnect. A text that arrived while the process was dead, or while the link was down, is admitted without waiting for a provider change. Both tests then passed.

`run-as kill -9` on pid 31916 returned a new process, pid 32032, within 8 seconds. The package was then force-stopped so the process stayed absent while the SMS-only text arrived. Reinstall did not clear `stopped=true`. Opening the launcher activity cleared it, and the service was started as the app itself (`run-as` `am start-foreground-service --user 0`). The shell cannot start that service.

Live score, 2026-10-28: baseline 541 phone rows. One new SMS, complete, revision 1, sender hash matches the SMS-only number. Hello `2026-10-28 09:34:09,079`. Accept `stored` at `09:34:09,333`, 254 ms later. No other new phone row. PASS.

### C4 — code.read.result

`test_code_read_result_passes_value_kind_and_reason` failed first (`value_kind` was missing). `zola-phone` now copies `value_kind` and `reason` from `code.read.result` onto the local result. The value is still not logged. The test then passed.

Track 5 carry-forward: `phone_client.call` cannot pass the message kind, because its first argument is already named `kind`.

### C3 — RCS sender shape

Two MMS rows in the live store have `sender_kind=unparsed` and `sender_address` length 0. One has `rcs_flag=yes`. The other has `rcs_flag=unknown`. On both, the provider from-address (type 137) and the type 130 address are the same shape: they start with a letter, contain `@`, and include letters, phone punctuation, and one other symbol. The lengths are 32 and 41. The type 151 address on both is a phone number: length 12, starts with `+`, digits and phone punctuation. That is the handset, not the sender.

`phone_ids.normalize` does not treat either sender as `e164`, a short code, or a short alphanumeric token, so the kind is `unparsed` and only `e164` is matchable. The phone ingest writes `sender_address` as an empty string on every phone row and stores the kind plus the hash. The column is empty because that insert never writes the address, and the kind is not one person matching uses.

Track 5 carry-forward: RCS senders may not be phone numbers, so person matching must handle them.

### Suites after the C9 repeat

Kotlin `testDebugUnitTest`: `CompanionRulesTest` 12, `EngineFlowTest` 39, `Phase4Test` 14. 65 tests, 0 failures. The two new scan tests are in the engine-flow count.

`zola_workspace` 357 OK, `zola_memory` 134 OK, `zola_tools` 44 OK, `zola_tts` 8 OK.

`dotnet run` of `Zola.Client.Checks`: exit 0. Coverage: lifecycle 22/22, admission 13/13, start 9/9, invalid pairs 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20, timing 8/8, compress 8/8, supervision 38/38, speech 38/38, phone 11/11.

`zola_phone`, client closed: 40 tests, 0 failures, 27.576 s. That includes `test_code_read_result_passes_value_kind_and_reason` and the two mutex tests.

The worktree client was started again at 09:45:43, pid 17884. A new hello arrived at 09:46:29,516. Pipe status after that hello: `link_state=connected`, `socket_open=true`, `paired=true`, `last_ping_answered=true`. The phone process is a child of that client. That is the Companion row's connected state.

Smoke passed.

## Phase 7 — Closeout

### 7a

Suites, this closeout: Kotlin 65/65 (`CompanionRulesTest` 12, `EngineFlowTest` 39, `Phase4Test` 14). `zola_workspace` 357, `zola_memory` 134, `zola_tools` 44, `zola_tts` 8, `zola_phone` 40, all OK. `Zola.Client.Checks` exit 0, coverage unchanged, phone 11/11.

Live mirror matches the worktree for `keys.py`, `runtime.py`, `serve.py`, `wire.py`, `phone_protocol.json`, and `phone_vectors.json`. `runtime.py` was copied after the C4 edit; its live SHA-256 is `0BDB7D8644573CA051F0B6BB16AECAB255BCA483147AE78E6E0841C7E193B926`. `phone_test_keys.json` is not in the live profile. Tests were not copied. Hermes is clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

`local.properties`, the debug APK, and `android-companion/.idea/` are gitignored. The APK has 0 `google-services` entries, 0 `phone_test_keys` names, and 0 `BEGIN PRIVATE KEY` labels. `android-companion/` has no `google-services` file. The root `.idea/` folder is not part of the commit.

### Exit

| # | Criterion | Result |
|---|---|---|
| 1 | Entry gates, CP-G1–G12, STOP verdicts | Met. Recorded in Phases 1–4. |
| 2 | Kotlin, golden vectors, plugin suites, client checks | Met. 65 / 357 / 134 / 44 / 8 / 40, checks exit 0. |
| 3 | C1–C9, C10 under the amendments | Met. Cells above. C10 table is in the passive-rerun section. |
| 4 | Section 4 open items | Met in grounding and smoke. Unplugged MMS and group delivery are C3. RCS under the screen-off bar is the C10 amendment. RCS labelling is `unknown` on the C3 row. Spam and blocked columns are the schema probe and C5. Provider ids 29003 and 29005 were not reused. RCS on this phone is stored by `com.google.android.apps.messaging`. |
| 5 | No message content in the logs | Met at the Part B grep: 0 hits. |
| 6 | Contract v3, both directions, the named guards, C11, no test key in the APK, approved dependencies, no Hermes or lore change | Met. C11 fresh-home rerun passed. Dependencies are the resolved list in Phase 4. The phone is paired to the live `zola-phone`. |

Track 5 carry-forwards stay open: `phone_client.call` cannot pass a message kind, and RCS senders may not be phone numbers.

Implementation SHA: `839cb7ab63f601790bb1df012d92172e6f0e10de`. The merge waits until the worktree client is closed. Scratch, the pulled logs, and the backups stay until the worktree is removed. The scratch firewall rule is still present.






