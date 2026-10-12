# P10PRE Phase 4 — Background Service and SDK (Tier 1)

Scored against TM-06 and TM-07. Old behavior is not treated as Android 16 or Play compliance. `targetSdk` is 35 and `compileSdk` is 36 (`app/build.gradle.kts` lines 32–38). Questions for Synthesis Section 9 are listed in item 7.

## 1. Long-running components

| Component | How it starts | What keeps it alive |
| --- | --- | --- |
| `ListeningService` | `ContextCompat.startForegroundService` from `MainActivity` (lines 479 and 919). | Foreground service. `onStartCommand` runs a watchdog loop. Not a capture service. |
| `AvaNotificationListenerService` | System binds it when notification access is enabled. | Binding. In-memory buffer only (`AvaNotificationListenerService.kt` 9–11, 20–25). |
| `ZolaFcmService` | System delivers `MESSAGING_EVENT`. | Not long-running. `onMessageReceived` launches a short coroutine (`ZolaFcmService.kt` 42–49). |
| `SmsContentProviderPoller` | `start()` from `MainActivity.applyAutonomousOptInSideEffects` when autonomous speech opt-in is on (lines 2168–2174). | `autonomousScope` coroutine plus `delay` of 2 minutes. Not a service. |
| `SmsReceiver` | System broadcast. | `goAsync()` until one emit attempt finishes (`SmsReceiver.kt` 149–160). |
| `DeviceStateMonitor` | `start()` after activity wiring (`MainActivity.kt` 607–611). | Activity lifetime. Dynamic receivers and telephony callback. |
| `ReminderManager` / `ReminderBroadcastReceiver` / `RecurringReminderWorker` | Alarms, geofence, WorkManager from reminder intents. | OS alarm or periodic work. Local notification, not SMS/notification capture. |
| `SessionGraceAlarmReceiver` | `AlarmManager.setAndAllowWhileIdle` (`SessionIdentityProvider.kt` 255). | Session identity for the on-device brain. |
| `NightlyConsolidationWorker`, `EnrichmentReplayWorker`, `CognitivePrepWorker`, `SportsAlertWorker` | WorkManager from brain schedulers. | Periodic or one-shot work. Tier 2. |

INFO: no `JobService`. No `BOOT_COMPLETED` receiver. A Phase 18 audit note in Repository B claimed a `BootReceiver`; that class is not in the current manifest. This audit does not treat that older note as a Phase 10 decision.

## 2. Foreground service

Only `ListeningService`.

| Item | Evidence |
| --- | --- |
| Manifest type | `microphone\|shortService` (`AndroidManifest.xml` lines 76–80) |
| Permissions | `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_MICROPHONE`, `FOREGROUND_SERVICE_SHORT_SERVICE` (lines 8–11) |
| `startForeground` | `ServiceCompat.startForeground` at `ListeningService.kt` 101 (short service, then `stopSelf`) and 111 (microphone type), gated on API 34 (`UPSIDE_DOWN_CAKE`) |
| Channel | `ZolaForegroundServiceChannel`, id constant line 41, notification id 1 |

The notification listener and FCM service are not foreground services.

## 3. Battery exemption

Not present. No `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` and no settings intent for ignoring battery optimizations in `app/src/main`.

## 4. Samsung-specific handling

Not present as Device Care, sleeping-apps, or a battery allow-list.

INFO (code comments, not a policy claim): `SmsContentProviderPoller` exists because RCS can bypass `SMS_RECEIVED` on Samsung (class doc lines 29–31). `MessageReadToolAdapter.kt` lines 217–234 documents Samsung One UI `spam_report` versus a stock `blocked` column, and names SM-S918U1. `SmsWarmDataProvider.kt` lines 190 and 255 comment on OEM date and spam columns. These are old-code assumptions. They do not establish current Android 16 behavior.

## 5. What restarts capture

| Event | SMS receiver | SMS poller | Notification buffer | Call monitor |
| --- | --- | --- | --- | --- |
| Process death | Next `SMS_RECEIVED` can start the process. Emit is dropped until `MainActivity` calls `SmsReceiver.setEnvironmentalEventBus` (line 629). | Not restarted. Job lived in the activity scope. | System may rebind the listener. Buffer starts empty (no persistence, service doc lines 9–11). | Not restarted until the activity starts the monitor. |
| Reboot | Same as process death. No boot receiver. | Not started until the activity opts in again. | Listener rebinds only if the user left notification access on. | No. |
| App update | Manifest receiver remains. Bus and poller do not. | No. | Listener binding is an OS setting. Buffer is empty after process restart. | No. |

TM-07 facts (not gaps): there is no durable capture queue. `lastSeenMessageId` is a field on the poller instance (line 81), lost when the job stops. The listener cap of 20 is an in-memory bound with no acknowledgement protocol.

## 6. Components that mainly support Tier 2

- `ListeningService`: Silero watchdog, gatekeeper, overlay (`ListeningService.kt` 23–27, 115–120). Partial wake lock around a sample (`PARTIAL_WAKE_LOCK`, lines 186–196). Voice, not SMS or notifications.
- Reminder alarms and `RecurringReminderWorker`: on-device reminders.
- `SessionGraceAlarmReceiver`, nightly consolidation, enrichment replay, cognitive prep, sports alerts: memory and brief pipeline.
- `DeviceStateMonitor`: posture for the on-device environmental model, including a call-active boolean.

FCM is not in this list as "leave the mechanism." What it triggers is recorded in Phase 7.

## 7. `targetSdk` questions (not answers)

For Synthesis Section 9:

- The microphone foreground service branches on API 34 types (`ListeningService.kt` 96–111). What does a target at or above the current Play target require for a companion that is not a microphone service?
- `SmsReceiver` is a manifest `SMS_RECEIVED` receiver with `exported="false"`. What delivery rules apply for that receiver on Android 16 when the app is not the default SMS app?
- The poller is an in-process loop while the activity scope is alive. What restrictions apply if that loop is later moved to a background process (Doze, app standby, Samsung battery management) on a Galaxy S23 Ultra?
- `SCHEDULE_EXACT_ALARM` and `setExactAndAllowWhileIdle` are used for reminders and session grace, not for SMS. Do not treat those call sites as a capture scheduler.
- `READ_PHONE_STATE` is used in code and omitted from the manifest. Call items stay INFO.

## 8. Reuse verdicts

| Component | Verdict | TM |
| --- | --- | --- |
| `ListeningService` | **LEAVE** — voice foreground service. | TM-06 |
| `SmsContentProviderPoller` lifetime | **ADAPT** the query; do not reuse the activity scope as the reliability story. Architecture **LEAVE**. | TM-06, TM-07 |
| `SmsReceiver` delivery across process death | **ADAPT** parse; current bus hold is **LEAVE**. | TM-06 |
| `AvaNotificationListenerService` | **ADAPT** — system-bound listener is the access method. Buffer is not a queue. | TM-06, TM-05 |
| `ZolaFcmService` | **REWRITE** — see Phase 7. The service is a push entry point; the handler is handoff. | TM-03, TM-06 |
| Reminder / session / consolidation / sports / cognitive workers | **LEAVE** | TM-06 |
| Battery-exemption helper | **No old component** | TM-06 |
| Boot restart of capture | **No old component** | TM-06 |
| Bounded ack queue | **No old component** (TM-07: absence is a fact, not a `[GAP]`) | TM-07 |

## Findings

- **P10PRE-AUD-05** (also Phase 3) `[RISK]` MEDIUM — activity-scoped poller and bus. TM-06.
- No separate `[GAP]` for the missing queue. TM-07 is report-only. See Phase 10.
