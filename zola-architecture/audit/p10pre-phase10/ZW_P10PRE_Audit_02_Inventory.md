# P10PRE Phase 2 — Inventory (Tier 3)

**Repository B:** `C:\Users\test\StudioProjects\ZolaAssistant`  
**Branch file:** `.git/HEAD` = `ref: refs/heads/zola-main`  
**SHA file:** `.git/refs/heads/zola-main` = `a139ccacab596f12b95e2dd3eda14352bcb97836`  
**Read time:** 2026-10-12 (filesystem reads only; no Git commands in this repository)

Skipped and not opened: `build/`, `.gradle/`, `.idea/`, `.cxx/`, binary assets.

## 1. Modules

| Module | Type | Notes |
| --- | --- | --- |
| `:app` | Android application | Only module. `settings.gradle.kts` line 27: `include(":app")`. `rootProject.name` is `AvaPersonalAssistant` (line 26). Namespace and `applicationId` are `com.beebo.zolaassistant`. |

INFO: the Gradle project name is still Ava. The Kotlin package under audit is `com.beebo.zolaassistant`. The separate Ava tree `com.example.avapersonalassistant` was not read.

## 2. SDK and toolchain (`:app`)

| Item | Value | Where |
| --- | --- | --- |
| minSdk | 26 | `app/build.gradle.kts` line 37 |
| targetSdk | 35 | line 38 |
| compileSdk | 36 | line 32 |
| Kotlin | 2.0.0 | `gradle/libs.versions.toml` `kotlin` |
| AGP | 8.9.2 | `libs.versions.toml` `agp` |
| Gradle wrapper | 8.11.1 | `gradle/wrapper/gradle-wrapper.properties` `distributionUrl` |
| Java / JVM target | 17 | `app/build.gradle.kts` lines 96–101 |
| Google Services plugin | 4.4.2 | root `build.gradle.kts` line 7 |
| Kotlin serialization plugin | 1.9.10 | `app/build.gradle.kts` line 15 |

No library modules.

## 3. Setup presence (not contents)

| Item | Present |
| --- | --- |
| Gradle wrapper properties | yes |
| `local.properties` | yes |
| `app/google-services.json` | yes |
| `*.jks` / `*.keystore` | no files found outside skipped folders |

## 4. Top-level packages

Source root: `app/src/main/java/com/beebo/zolaassistant/`. No `src/main/kotlin` tree. One line each. Tier 2 means connection-check only.

| Package | Tier | Function |
| --- | --- | --- |
| `(root)` | mixed | `MainActivity`, `ListeningService`, `MapsActivity`, feature flags. Activity wires Tier 1 pollers and Tier 2 brain. |
| `agent` | 2 | Orchestrator, tools, daily brief, notification-priority agent. |
| `ai` | 2 | Gemini helper and Vertex token cache. |
| `attention` | 2 | Attention cost, dampening, deferred surfacing. |
| `auth` | 2 | Google sign-in options. Credential use is noted in Phase 6 only where Tier 1 touches it. |
| `brief` | 2 | Daily brief assembly, SMS-analysis consent settings, prompt. |
| `calendar` | 2 | Google Calendar manager and NL confirmation stores. |
| `coffee` | 2 | Coffee-shop search intent. |
| `cognitive` | 2 | Response planning and cognitive-prep worker. |
| `context` | 2 | Context resolution. |
| `conversation` | 2 | Turn, topic, and follow-up state. |
| `data` | 2 | `ConversationEntry`. |
| `dispatch` | 2 | Final route dispatcher. |
| `emotion` | 2 | Emotion engine and mood tracker. |
| `entity` | 2 | Entity resolution. |
| `environment` | 1 and 2 | Bus, device-state monitor (call posture), location bus producer. Bus is shared with the brain. |
| `execution` | 2 | Tool execution logs. |
| `firebase` | 2 | `FirebaseHelper`. FCM itself is `presence/fcm`. |
| `gas` | 2 | Gas-station search. |
| `gmail` | 2 | Gmail manager. |
| `groundedinfo` | 2 | Grounded-info tool metadata. |
| `health` | 1 (capability, not first-wave SMS/notification) | Health Connect read-only steps, sleep, heart rate. |
| `identity` | 2 | Persona and identity context. |
| `improvement` | 2 | Self-improvement events. |
| `intent` / `intents` | 2 | Intent handlers, including SMS/notification NL handlers that call Tier 1 adapters. |
| `interpretation` | 2 | Query interpretation. |
| `live` | 2 | Gemini Live session and tool executors that call Tier 1 adapters. |
| `maps` | 2 | Travel-time parsing. |
| `memory` | 2 | Firestore-backed Zola memory. |
| `messaging` | 1 helper | `MessageReadContext` cleared after SMS send. |
| `multimodal` | 2 | Multimodal coordinator. |
| `nearby` | 2 | Nearby-business intent. |
| `news` | 2 | News search. |
| `nlp` | 2 | Gemini NLP client. |
| `notification` | 1 | Notification listener and in-memory read buffer. |
| `perception` | 2 | Watchdog, gatekeeper, overlay. Used by `ListeningService`. |
| `persona` | 2 | Speaking persona. |
| `place` | 2 | Place search. |
| `presence` | 1 (transport-adjacent) | Device registration, heartbeat, FCM, handoff. Not a PC companion channel. |
| `proactive` | 1 (`sms`) and 2 | `proactive/sms` capture; the rest is the on-device autonomous engine. |
| `prosody` | 2 | Speech chunking. |
| `purchase` | 2 | Purchase records. |
| `query` | 2 | Query processor. |
| `rag` | 2 | Semantic memory retrieval. |
| `reasoning` | 2 | Reasoning engine. |
| `relationship` | 2 | Relationship follow-up. |
| `reminder` | neither (background, not a phone capability) | AlarmManager and WorkManager reminders. |
| `response` | 2 | Response composition and delivery. |
| `restaurant` | 2 | Restaurant search. |
| `ril` | 2 | Calibration, continuity, self-model, social, temporal. |
| `roomreading` | 2 | Directedness and room-reading gate. |
| `routing` | 2 | Query routing, including SMS-send phrase signals. |
| `scene` | 2 | Scene analyzer. |
| `session` | 2 | Conversation state monitor. |
| `sms` | 1 and 2 | Provider warm-fetch and brief signals (Tier 1 query); `sms/speech` is voice (Tier 2). |
| `speechdelivery` / `speechresponse` | 2 | Speech plans. |
| `sports` | 2 | Sports clients and alert worker. |
| `system` | neither | Compute-priority scheduler for on-device work. |
| `timing` | 2 | Filler and timing controller. |
| `ui` | 2 | Compose UI, presence scene, settings. |
| `util` / `utils` | 1 (`LocationHelper`) and other | Location fix; other files are formatting and logging helpers. |
| `voice` | 2 | Voice switcher. |
| `weather` | 2 | Weather repository and speech. |

## 5. Manifest components

Main manifest: `app/src/main/AndroidManifest.xml`. Debug manifest only sets `android:name=".AvaDebugApplication"` and replaces `networkSecurityConfig`.

| Kind | Class | exported | Intent filter / type |
| --- | --- | --- | --- |
| activity | `.MapsActivity` | false | none |
| activity | `.MainActivity` | true | `MAIN` / `LAUNCHER` |
| activity-alias | `com.beebo.zolaassistant.ViewPermissionUsageActivity` → `.MainActivity` | true | `VIEW_PERMISSION_USAGE` / `HEALTH_PERMISSIONS`; permission `android.permission.START_VIEW_PERMISSION_USAGE` |
| service | `.ListeningService` | false | `foregroundServiceType="microphone\|shortService"` |
| receiver | `.reminder.ReminderBroadcastReceiver` | false | none |
| receiver | `.memory.session.SessionGraceAlarmReceiver` | false | `com.beebo.zolaassistant.session.ACTION_GRACE_LAPSED` |
| receiver | `.proactive.sms.SmsReceiver` | false | `android.provider.Telephony.SMS_RECEIVED`, priority 999 |
| service | `.notification.AvaNotificationListenerService` | true | `NotificationListenerService`; permission `android.permission.BIND_NOTIFICATION_LISTENER_SERVICE` |
| service | `.presence.fcm.ZolaFcmService` | false | `com.google.firebase.MESSAGING_EVENT` |
| receiver | `.cognitive.prep.CognitivePrepDebugReceiver` | true | `com.beebo.zolaassistant.ACTION_TRIGGER_COGNITIVE_PREP`; no permission attribute |

No `provider` elements. No `BOOT_COMPLETED` receiver.

## 6. Permissions and features (`:app` only)

`uses-permission`: `RECORD_AUDIO`, `FOREGROUND_SERVICE_MICROPHONE`, `FOREGROUND_SERVICE_SHORT_SERVICE`, `INTERNET`, `FOREGROUND_SERVICE`, `WAKE_LOCK`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `POST_NOTIFICATIONS`, `SYSTEM_ALERT_WINDOW`, `READ_CONTACTS`, `SEND_SMS`, `RECEIVE_SMS`, `READ_SMS`, `WRITE_SMS`, `SCHEDULE_EXACT_ALARM`, `health.READ_STEPS`, `health.READ_SLEEP`, `health.READ_HEART_RATE`.

`uses-feature`: `android.hardware.microphone` required.

`queries`: package `com.google.android.apps.healthdata`.

Not declared: `READ_PHONE_STATE`, `RECEIVE_MMS`, `RECEIVE_WAP_PUSH`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, `FOREGROUND_SERVICE_DATA_SYNC`, `POST_NOTIFICATIONS` is declared. `READ_PHONE_STATE` is checked in code (Phase 3) but absent here.

## 7. Dependencies (declared in `app/build.gradle.kts`)

**Networking:** OkHttp 4.10.0, logging interceptor, Retrofit 2.9.0, Gson converter, Volley, commons-net, gRPC artifacts in the version catalog (not all are `implementation` lines).

**Storage:** `androidx.security:security-crypto` (EncryptedSharedPreferences). No Room dependency declared.

**Background work:** `androidx.work:work-runtime-ktx:2.9.1`.

**Security:** security-crypto; Play Services Auth; Google auth library.

**Firebase / Google, FCM separate:** BOM `firebase-bom` 33.12.0; Analytics; Auth; Firestore; Realtime Database. **FCM:** `com.google.firebase:firebase-messaging-ktx` (line 205). Also Places, Play Services location and maps, Calendar and Gmail API clients, Health Connect.

**AI / LLM:** `com.google.ai.client.generativeai:generativeai` 0.9.0. Gemini Live client is first-party code, not a separate Gradle module.

**Voice / audio:** onnxruntime-android, sherpa-onnx local AAR, tensorflow-lite. Deepgram is called from app code via OkHttp WebSocket (no Deepgram Maven artifact in the dependency block).

**3D / UI:** SceneView 3.6.0, Jetpack Compose, AppCompat, ConstraintLayout.

**Other:** Health Connect, kotlinx-serialization, jsoup, coroutines.

## 8. Tier marks

| Area | Tier |
| --- | --- |
| `proactive/sms`, `notification`, SMS tool adapters, `SmsWarmDataProvider` | 1 |
| `DeviceStateMonitor` call posture | 1 exploratory |
| `ListeningService`, reminders, WorkManager, FCM service, device registration | 1 for background / reachability facts |
| `presence` handoff payloads | 1 only for how FCM is used; handoff content is brain state |
| Brain, voice, Firebase helpers, avatar/UI, Gmail, calendar, memory | 2 |
| Coffee, gas, news, sports, weather, restaurant | neither (not a companion capability in this audit) |
