# P10PRE Phase 5 — Pairing, Networking, and Storage (Tier 1)

## 1. Remote endpoints (no secret values)

| Host / service | Calling area | Tier |
| --- | --- | --- |
| Firebase Auth, Firestore, Realtime Database, Analytics | App-wide, including SMS entity load and FCM token write | 2, touched by Tier 1 |
| Firebase Cloud Messaging | `ZolaFcmService` | 1 for the wake question; handler is handoff |
| Google Calendar, Gmail, Places, Maps, Weather, Custom Search, speech, Gemini / Vertex | Feature packages | 2 |
| Deepgram listen WebSocket | `sms/speech/deepgram` via OkHttp | 2 voice |
| `api.openweathermap.org` | Named only in `network_security_config.xml` line 3 | neither |

No URL builder targeting a Windows PC, a LAN host, or a user-entered companion address was found under `app/src/main`.

## 2. PC or local-network device

Not present.

INFO: `DeviceCapabilities` (`presence/device/DeviceCapabilities.kt`) describes microphone, speaker, display, camera, GPS, notification permission, TTS, live voice, and Bluetooth audio for a Firestore device record. It does not list SMS, a PC, or a capability RPC.

## 3. Who opens the connection

| Connection | Side | Held open? |
| --- | --- | --- |
| Firebase, Google APIs, Deepgram | Phone outbound | Deepgram WebSocket is held for a recognition session (Tier 2). Firestore listeners were not audited internally. |
| FCM data message | Google delivers inbound to the phone. The app does not open a listening socket. | No app-held socket. `onMessageReceived` is per message. |
| SMS poller | Local content provider. | Loop held only inside the activity scope. |
| Inbound server (`ServerSocket`, Ktor server, embedded HTTP) | Not present | — |

TM-03 direction and wake stay facts: the phone opens cloud connections; nothing accepts a PC connection; FCM can wake the process for handoff messages only.

## 4. Authentication

| Endpoint | Credential source |
| --- | --- |
| Firestore entity load in `SmsReceiver` | `FirebaseAuth.getInstance().currentUser` (`SmsReceiver.kt` 96–97). No second factor. |
| FCM token write | Same Firebase uid plus install id (`ZolaFcmService.kt` 78–89). |
| Google APIs | Google sign-in / OAuth clients in Tier 2 auth. Not a device-pairing token. |
| Deepgram | `DEEPGRAM_API_KEY` build config from project properties (`app/build.gradle.kts` line 58). |
| PC pairing token | Not present. |

## 5. TLS

| File | Line | Fact |
| --- | --- | --- |
| `app/src/main/res/xml/network_security_config.xml` | 2–4 | `cleartextTrafficPermitted="false"` for `api.openweathermap.org` including subdomains. |
| `app/src/debug/res/xml/network_security_config_debug.xml` | 3–7 | Debug only: cleartext permitted for `10.0.2.2`, `127.0.0.1`, and `localhost` (comment: Firebase emulators). |
| `AndroidManifest.xml` | 44 | `android:networkSecurityConfig` points at the release XML. Debug manifest replaces it. |
| App code | — | No `CertificatePinner` and no custom `TrustManager` under `app/src/main`. No `usesCleartextTraffic` attribute. |

## 6. Device pairing

Not present. No QR setup, no pairing handshake, no companion trust store.

What exists instead is multi-device registration for this Android app:

- `DeviceInstallIdProvider` stores a UUID in plain `SharedPreferences` file `zola_device_registration_prefs`, key `device_install_id_v1` (lines 32–39, 48–57).
- `DeviceRegistrationRepository.updateFcmToken` writes that token to Firestore (`ZolaFcmService.kt` 85–89).
- `HandoffContextSerializer.readIfFresh` reads session handoff state (`ZolaFcmService.kt` 105).

That is not proof to a PC that a result came from Brian's phone. **P10PRE-AUD-04**.

## 7. Offline queue, retry, ack

Not present for SMS, notifications, or any PC delivery.

| Observed state | Class | What it is |
| --- | --- | --- |
| In-memory id cursor | `SmsContentProviderPoller.lastSeenMessageId` | Poll progress. Not acknowledged by another device. Lost with the process. |
| In-memory notification cap 20 | `AvaNotificationListenerService` | Process-local buffer. |
| `MessageReadToolAdapter.retryable = true` | line 98 | Tool-framework retry flag for the on-device agent. Not a transport retry. |
| Firestore initiative / deferred queues | `memory` package | Brain state. Not audited internally. Not an SMS transport queue. A background architecture note says a shared deferred queue lives in Firestore (`Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md`). That document is old-app lore, not a Phase 10 decision, and the queue it describes is not a phone-to-PC capability queue. |

TM-07 properties, each separate:

| Property | Evidence |
| --- | --- |
| Acknowledgements | Not present |
| Retries of unsent capability results | Not present |
| Duplicate handling | Poller skips ids `<= lastSeenMessageId` in one process. Listener dedupes by notification key in one process. Neither is a cross-device duplicate policy. |
| Bounded size | Listener cap 20. Poller does not bound a stored message list; it stores one id. |
| Delete after acknowledge | Not present. Mark-read updates the telephony provider for the local user; it is not an ack from a PC. |

Absence of these properties is a fact, not a `[GAP]`.

## 8. Tables, entities, preferences

No Room `@Entity` or `@Database` under `app/src/main`. Durable app data for the brain is Firestore (Tier 2). Local stores touched by this phase:

| Store | Fields observed | Mark |
| --- | --- | --- |
| `EventPayload.SmsReceived` | `sender`, `messageSnippet` (80 chars) | Message content, in memory, then brain |
| `NotificationSummary` | `key`, `packageName`, `appLabel`, `title`, `text`, `postedAtMs` | Message/notification content, in memory |
| `SmsInboxRow` | `id`, `address`, `body`, `date` | Message content, poller-local |
| `zola_device_registration_prefs` | `device_install_id_v1` | Config / identity, not proof of pairing |
| Wave K prefs in `MainActivity` | boolean that the notification-access screen was opened | Config |
| `EncryptedSharedPreferences` in `EnrichmentReplayBuffer` and `ui/presence/RecentTurnsPersistence` | brain enrichment and recent turns | Zola memory/brain state |
| `SessionIdentityProvider` prefs | session identity | Brain state |
| Firestore device doc `fcmToken` | token written by `ZolaFcmService` | Credential material in cloud storage, not Keystore |
| Firestore person `phone` | used to filter proactive SMS | Zola memory |

## 9. Deletion and retention

- Notification buffer: dropped on process death; key removed in `onNotificationRemoved`. No time-based retention.
- SMS poller: does not delete messages. It moves an id cursor forward.
- `mark_read`: sets read flags on SMS/MMS rows. It does not delete them.
- No companion retention policy for message bodies. Brief `smsAnalysisConsent` gates brief analysis (`DailyBriefSettings.kt` line 10, default false; `SmsIntelligenceAnalyzer.kt` line 21). The receiver, poller, and `MessageReadToolAdapter` do not read that flag.

## 10. Axes

| Component | Acquisition | Delivery |
| --- | --- | --- |
| Cloud clients | Phone-outbound HTTPS/WSS | Not a PC channel |
| FCM | Inbound push to the phone | Triggers a Firestore handoff read or a log of `SESSION_INVALIDATED`. Does not fetch SMS. |
| Device install id | Written once locally | Uploaded as part of Firebase device registration. No PC verifier. |
| Local SMS/notification stores | On-device only | No outbound delivery |

## 11. Reuse verdicts

| Component | Verdict | TM |
| --- | --- | --- |
| PC client / pairing handshake | **No old component** | TM-03, TM-04 |
| `ZolaFcmService` | **REWRITE** — push entry exists; payload is handoff. Do not mark the FCM mechanism LEAVE. | TM-03 |
| `DeviceInstallIdProvider` | **LEAVE** as provenance. A random UUID in plain prefs does not satisfy TM-04. | TM-04, TM-08 |
| Device registration and handoff | **LEAVE** — old multi-device brain presence. | TM-02 |
| Transport queue | **No old component** | TM-07 |
| `EncryptedSharedPreferences` brain buffers | **LEAVE** | TM-02 |
| Cleartext debug config | **LEAVE** — emulator Firestore, not a companion transport. | TM-08 |

## Findings

- **P10PRE-AUD-04** `[GAP]` HIGH — No phone–PC exchange and no fail-closed provenance. TM-03 (the exchange; direction and wake are separate facts in this file), TM-04.
- **P10PRE-AUD-06** `[RISK]` MEDIUM — FCM handler depends on Firebase Auth and Firestore handoff (`ZolaFcmService.kt` 42–58, 73–89, 95–110). TM-02, TM-09.
- **P10PRE-AUD-09** `[RISK]` MEDIUM — Install id is plain SharedPreferences; FCM token is stored in Firestore, not Keystore. TM-08.
