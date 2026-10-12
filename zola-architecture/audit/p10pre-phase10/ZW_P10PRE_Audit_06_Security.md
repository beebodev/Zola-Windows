# P10PRE Phase 6 — Security and Secrets

No Git commands were run in Repository B. Nothing below is described as committed or tracked. Secret values are not written. Search skipped `build/`, `.gradle/`, `.idea/`, and `.cxx/`.

## 1. Secret candidates in the tree

| Path | Line | Type | Status |
| --- | --- | --- | --- |
| `app/src/main/assets/diagflow_service_account.json` | 5 | GCP service-account private key block | Present in the repository tree. Value redacted. Commit status not checked. |
| `app/google-services.json` | 29 | JSON field name `api_key` | Present. Value redacted. Commit status not checked. |
| `app/google-services.json` | 31 | Google API key pattern | Present. Value redacted. Commit status not checked. |
| `local.properties` | 11 | `CUSTOM_SEARCH_API_KEY` value matches a Google API key pattern | Present. Value redacted. Commit status not checked. |
| `local.properties` | 14 | `MAPS_API_KEY` value matches a Google API key pattern | Present. Value redacted. Commit status not checked. |
| `local.properties` | 15 | `GOOGLE_WEATHER_API_KEY` value matches a Google API key pattern | Present. Value redacted. Commit status not checked. |
| `progress docs/PHASE0_TRACK_A_PROGRESS.md` | 626 | Google API key pattern | Present. Value redacted. Commit status not checked. This path is not named in the readable `.gitignore` lines. |

Property names present in `local.properties` whose values did **not** match the Google API key pattern during the scan (values not transcribed): line 12 `CUSTOM_SEARCH_ENGINE_ID`, line 13 `GEMINI_API_KEY`, line 16 `DEEPGRAM_API_KEY`. Treat the key properties as credential material until a human inspects them. Line 8 is `sdk.dir` (machine path, not an API secret).

OAuth client-id identifiers (not scored as API secrets; values redacted): `app/build.gradle.kts` line 51 (`CLIENT_ID` build config), `app/src/main/res/values/strings.xml` line 4, `app/google-services.json` lines 17, 25, and 38, `local.properties` line 17 (`CIENT_ID`, spelling as in the file).

No `*.jks` or `*.keystore` files were found outside skipped folders.

Findings: **P10PRE-AUD-07** (private key), **P10PRE-AUD-08** (API key candidates).

## 2. `.gitignore` lines that match the question

Readable plain-text lines include:

```
/local.properties
app/google-services.json
app/src/main/assets/diagflow_service_account.json
local.properties
```

`google-services.json.old` and `*.json.old` are also named. No readable line names `*.jks` or `*.keystore`.

INFO: some later lines of `.gitignore` did not decode as plain ASCII (embedded nulls between characters), including an `.idea/` line and several `.tmp-sceneview-src/` entries. The four exclusions quoted above were plain text. This audit does not claim those null-containing lines are effective ignore rules.

Ignore rules do not establish commit history. A file can be present, ignored, and still have been committed earlier. That was not checked.

## 3. Credential storage

| Credential | Where | Class and line |
| --- | --- | --- |
| Firebase / FCM token | Firestore, after Firebase Auth uid check | `ZolaFcmService.storeFcmToken` lines 73–89 |
| Install UUID | Plain `SharedPreferences` `zola_device_registration_prefs` | `DeviceInstallIdProvider.getOrCreate` lines 32–39 |
| Google API keys and Deepgram/Gemini property names | `local.properties`, copied into `BuildConfig` when Gradle properties resolve | `app/build.gradle.kts` lines 51–58 |
| OAuth client id | String literal in `build.gradle.kts` line 51 | Build config, ships in the app binary if built |
| Enrichment replay buffer | `EncryptedSharedPreferences` (security-crypto) | `memory/consolidation/EnrichmentReplayBuffer.kt` lines 62–67 — brain state, not a companion credential |
| Recent turns | `EncryptedSharedPreferences` | `ui/presence/RecentTurnsPersistence.kt` lines 53–58 — brain state |
| Android Keystore for an API key, FCM token, or pairing key | Not present | — |

**P10PRE-AUD-09**.

## 4. Token, credential, or message-content logging

| File | Line | Fact |
| --- | --- | --- |
| `MessageSendToolAdapter.kt` | 135 | `Log.d` includes 40 characters of the sent SMS body |
| `MessageReadToolAdapter.kt` | 584 | exception log includes 15 characters of an address |
| `MessageReadToolAdapter.kt` | 422, 477 | last 4 digits on spam-skip logs |
| `MainActivity.kt` | 2151 | `Log.d` includes `account.email` after Firebase Auth success |
| `LocationHelper.kt` | 150–154 | `Log.d` includes latitude and longitude of a resolved fix |
| `ZolaFcmService.kt` | 69, 80, 91 | logs failure text and a 6-character uid prefix; the token string is not written in the lines read |
| `SmsReceiver.kt` | 108, 156, 163 | exception messages only |

**P10PRE-AUD-03** (message body). **P10PRE-AUD-14** (coordinates). Email logging is included in AUD-03's file list as account identifier in logcat, same TM-08 rule family; severity stays on the body preview as the message-content hit. The email line is part of AUD-03's evidence, not a second id.

## 5. Exported components

| Component | exported | Protection | Could another app invoke it? |
| --- | --- | --- | --- |
| `MainActivity` | true | Launcher `MAIN` | Yes, as a normal launch. |
| `ViewPermissionUsageActivity` alias | true | `android.permission.START_VIEW_PERMISSION_USAGE` | Only holders of that system permission. |
| `AvaNotificationListenerService` | true | `BIND_NOTIFICATION_LISTENER_SERVICE` | Binding is limited to the system permission. |
| `CognitivePrepDebugReceiver` | true | No manifest permission. `onReceive` returns immediately unless `BuildConfig.DEBUG` (`CognitivePrepDebugReceiver.kt` 21–24). | A debug build can be started by any app that sends `com.beebo.zolaassistant.ACTION_TRIGGER_COGNITIVE_PREP`. Release builds no-op. |
| `SmsReceiver` | false | Not exported | Other apps cannot send it. The system can still deliver `SMS_RECEIVED`. |
| `ListeningService`, `ZolaFcmService`, reminder and session receivers | false | Not exported | Not a general IPC surface. |

**P10PRE-AUD-10** for the debug receiver.

## 6. Severity

| ID | Severity | Why |
| --- | --- | --- |
| P10PRE-AUD-07 | HIGH | Private key material is in the tree. Live secret. Commit status not checked. Path is named in `.gitignore`. |
| P10PRE-AUD-08 | HIGH | API key patterns are in the tree (`google-services.json`, `local.properties`, a progress markdown file). Commit status not checked. The JSON and `local.properties` paths are named in `.gitignore`. The progress markdown path is not. |
| P10PRE-AUD-03 | MEDIUM | Message-content preview in logcat. |
| P10PRE-AUD-09 | MEDIUM | Credential and install id storage misses the Keystore target. |
| P10PRE-AUD-14 | LOW | Precise location in logcat. |
| P10PRE-AUD-10 | LOW | Exported debug receiver, release-guarded. |

OAuth client ids are identifiers that Android apps normally ship. They are recorded above and are not given finding IDs.
