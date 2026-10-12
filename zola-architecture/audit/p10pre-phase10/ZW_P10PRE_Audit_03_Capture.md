# P10PRE Phase 3 — Capture (Tier 1)

Call and phone-state items are INFO only (TM-05, `S74` deferred). No finding IDs on INFO lines.

## Mechanisms

| Mechanism | Class | File |
| --- | --- | --- |
| SMS broadcast receiver | `SmsReceiver` | `app/src/main/java/com/beebo/zolaassistant/proactive/sms/SmsReceiver.kt` |
| SMS inbox poll (not a `ContentObserver`) | `SmsContentProviderPoller` | `proactive/sms/SmsContentProviderPoller.kt` |
| On-demand SMS/MMS/RCS provider query | `MessageReadToolAdapter` | `agent/tools/adapters/MessageReadToolAdapter.kt` |
| On-demand SMS/MMS search | `MessageSearchToolAdapter` | `agent/tools/adapters/MessageSearchToolAdapter.kt` |
| SMS send | `MessageSendToolAdapter` | `agent/tools/adapters/MessageSendToolAdapter.kt` |
| Brief warm SMS query | `SmsWarmDataProvider` | `sms/SmsWarmDataProvider.kt` |
| Notification listener | `AvaNotificationListenerService` | `notification/AvaNotificationListenerService.kt` |
| Notification read model | `NotificationReadManager` | `notification/NotificationReadManager.kt` |
| Notification tool | `NotificationReadToolAdapter` | `agent/tools/adapters/NotificationReadToolAdapter.kt` |
| Call posture | `DeviceStateMonitor` | `environment/device/DeviceStateMonitor.kt` |

INFO: `RoleManager`, `ROLE_SMS`, and `SMS_DELIVER` are not present. The app is not implemented as the default SMS handler.

INFO: no `ContentObserver` on the SMS provider. The poller uses `ContentResolver.query` on a timer.

INFO: RCS is present only as MMS/provider rows (`content://mms`, `m_type` 132 retrieve-conf, Samsung date-unit comments in `MessageReadToolAdapter.kt` lines 108–125). There is no separate RCS API.

## Permissions and manifest

| Mechanism | Declaration |
| --- | --- |
| `SmsReceiver` | `RECEIVE_SMS`. Manifest lines 95–101: `exported="false"`, action `android.provider.Telephony.SMS_RECEIVED`, priority 999. |
| Poller and read/search adapters | `READ_SMS`. |
| Send | `SEND_SMS`. `SmsManager.getDefault()` at `MessageSendToolAdapter.kt` lines 132–134. |
| Mark read | `WRITE_SMS` is in the manifest. `performMarkThreadRead` updates SMS/MMS rows (`MessageReadToolAdapter.kt` around 1255–1325). |
| Runtime request | `MainActivity.maybeRequestSmsPermissions` lines 2084–2095 requests `RECEIVE_SMS`, `READ_SMS`, and `SEND_SMS` together when `smsReceiverEnabled` is true. |
| Listener | Manifest lines 103–111: `exported="true"` with `android.permission.BIND_NOTIFICATION_LISTENER_SERVICE`. User path: `MainActivity.scheduleNotificationListenerHintAfterContactsFlow` lines 2098–2118 opens `Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS` once. |
| Call | `READ_PHONE_STATE` is checked at `DeviceStateMonitor.kt` lines 305–307 and is **not** in the manifest. Audio mode is used without that permission (lines 136–144). |

`SpeechFeatureFlags.kt`: `smsReceiverEnabled` and `smsContentProviderPollerEnabled` are true (lines 326–329). Poll interval `smsPollerIntervalMs` is 120000 (line 332).

## Fields extracted (no values quoted)

**Receiver** (`SmsReceiver.kt` 141–144, 112–120): originating address, joined `messageBody`, then an 80-character snippet. Bus payload `EventPayload.SmsReceived` is `sender` (person display name) and `messageSnippet` (`environment/bus/EventPayload.kt` 43–46). Thread id is not on that payload.

**Poller** (`SmsContentProviderPoller.kt` 223–240, 165–168): inbox `_ID`, `ADDRESS`, `BODY`, `DATE`. Emits the same snippet payload. Advances `lastSeenMessageId` to the max id in the batch (lines 156–157) even when only one known-contact row is emitted.

**On-demand unread summary** (`MessageReadToolAdapter.kt` 426–434 and 482–490): `sender_name`, `sender_phone`, `body` (truncated at 300, line 102), `date_ms`, `thread_id`, `is_mms`. Result map also has `status`, `unread_count`, `unread_count_raw` (lines 511–518). Lookback 30 days (line 126). One row per thread after dedupe (line 500).

**Last from sender** (lines 1173–1186): `status`, `sender_name`, `body`, `date_ms`, `direction`, optional `is_mms`, `sender_phone`, `threadId`, `thread_name`, `is_group`.

**Search** (`MessageSearchToolAdapter.kt` 131–137): `sender`, `body` (capped), `date`, `threadId`, `isGroup`.

**Warm fetch** (`SmsWarmDataProvider.kt` 71–76): `THREAD_ID`, `READ`, `ADDRESS`, `BODY`, `DATE`, `TYPE`. Feeds brief signals, not a PC payload.

**Notifications** (`NotificationReadManager.kt` 95–116): `key`, `packageName`, `appLabel`, `title` (`EXTRA_TITLE`), `text` (`EXTRA_TEXT`, else `EXTRA_BIG_TEXT`), `postedAtMs`. Tool payload renames label to `app` (`NotificationReadToolAdapter.kt` 45–51). Optional `app_filter` is a substring on the label.

## Next destination

| Source | Destination |
| --- | --- |
| `SmsReceiver` / poller | In-process `EnvironmentalEventBus` event type `sms_received`. Sender must match a Firestore person entity `phone` attribute (`SmsReceiver.kt` 104–111, poller 159–163). If the activity has not set the bus, the receiver logs `sms_emit_skipped` and drops the message (lines 113–115). |
| Bus consumer | `ProactiveAutonomousEngine` handles `EventPayload.SmsReceived` (import/use site in that Tier 2 class). Not re-read internally. |
| `MessageReadToolAdapter` / search / send | `ToolResult` for `AssistantTool`. Callers include Live executors and `WaveKIntentHandlers` (Tier 2). |
| `SmsWarmDataProvider` | Daily-brief warm context when `smsAnalysisConsent` is true (`ToolWarmStartAgent` connection; brief internals not audited). |
| Listener buffer | `NotificationReadManager.getVisibleNotifications`, then the read tool and `ProactiveMemoryAwarenessScanner` (`NotificationNudge`: `appLabel`, `titleSnippet`). |
| `DeviceStateMonitor` | Bus event `device_state_update` with `callActive` boolean. No phone number is copied on API 31+ (`onCallStateChanged(state)` only, lines 205–208). |

None of these destinations is a PC, a socket to a local-network device, or a durable outbound queue.

## Notification filters and grouping

- Listener stores every posted `StatusBarNotification`, dedupes by `key`, cap 20, process lifetime (`AvaNotificationListenerService.kt` 20–25, 41). Removal drops that key (lines 28–31).
- No package allow-list, no `MessagingStyle` / `EXTRA_MESSAGES`, no group-summary skip.
- On-demand SMS group handling is separate: `is_group` / `thread_name` from `content://mms-sms/conversations` (`MessageReadToolAdapter.kt` 1153–1186).
- Proactive SMS emits at most one known-contact event per poll cycle (class doc lines 33–34; pick at line 163).

## Message-content logging

| File | Line | What is logged |
| --- | --- | --- |
| `MessageSendToolAdapter.kt` | 135 | `Log.d` of `body.take(40)` after a successful send |
| `MessageReadToolAdapter.kt` | 584 | exception log includes `address.take(15)` |
| `MessageReadToolAdapter.kt` | 422, 477 | last 4 digits of an address on a spam-skip log |
| `SmsReceiver.kt` / poller | — | logs errors and ids, not the snippet |
| `AvaNotificationListenerService.kt` | 59, 66 | notification key prefix (40 chars), not title or text |

Finding: **P10PRE-AUD-03**.

## Two axes

| Mechanism | Phone-side acquisition | Must stay active? | PC-side delivery |
| --- | --- | --- | --- |
| `SmsReceiver` | Manifest broadcast. Process can be started by the system for `SMS_RECEIVED`. | The receiver does not stay resident. Emit succeeds only if the activity already published the in-memory bus. | No PC path. In-process event for the on-device brain. |
| `SmsContentProviderPoller` | Timed inbox query. | Yes, while the coroutine job runs. Started from `MainActivity.applyAutonomousOptInSideEffects` (lines 2168–2174) on `autonomousScope`. `stop()` on opt-out (2180–2182) and activity teardown (2616). | No PC path. Same in-process event. Not request/response. |
| `MessageReadToolAdapter` / search | Query when a tool call runs. | No ongoing listener. | No PC path. Local request/response: the on-phone agent calls `invoke` and gets `ToolResult`. |
| `MessageSendToolAdapter` | `SmsManager.sendTextMessage` after `_confirmed=true` (lines 33–42, 134). | No. | No PC path. |
| `SmsWarmDataProvider` | Query at brief warm-fetch. | No. | No PC path. |
| Notification listener | Bound by the system while notification access is on. `onNotificationPosted` must be connected to fill the buffer. | Yes, for the buffer to stay current. The service does not forward each post. | No PC path. Reads are local tool calls against the buffer. Nudges are in-process bus events, not per-notification forwarding. |
| `DeviceStateMonitor` | INFO. Telephony callback plus audio mode, while `start()` has been called from the activity. | Yes for continuous posture. | INFO. No PC path. Boolean `callActive` only. |

## Reuse verdicts

| Component | Platform code | Old Zola architecture around it | TM |
| --- | --- | --- | --- |
| `SmsReceiver` | **ADAPT** — PDU parse and address are usable; drop the Firestore person gate and bus emit. | **LEAVE** — brain event. | TM-05, TM-01, TM-09 |
| `SmsContentProviderPoller` | **ADAPT** — inbox query and id cursor are usable; lifetime is activity-scoped. | **LEAVE** — same brain emit and entity match. | TM-05, TM-06, TM-09 |
| `MessageReadToolAdapter` | **ADAPT** — provider queries and field maps are the salvageable read path. | **LEAVE** the `AssistantTool` / Live / intent wiring. | TM-05, TM-09 |
| `MessageSearchToolAdapter` | **ADAPT** | **LEAVE** tool wiring. | TM-05, TM-09 |
| `MessageSendToolAdapter` | **ADAPT** — send plus confirm flag; remove body logging. | **LEAVE** tool wiring. | TM-08, TM-09 |
| `SmsWarmDataProvider` | **LEAVE** — brief warm cache, not a companion endpoint. | **LEAVE** | TM-02 |
| `AvaNotificationListenerService` | **ADAPT** — bound listener is the access method; replace the raw `StatusBarNotification` buffer with an explicit extract. | **LEAVE** as an assistant cache. | TM-05, TM-09 |
| `NotificationReadManager` | **ADAPT** — already a plain `NotificationSummary`. | **LEAVE** nudge/tool callers. | TM-05, TM-09 |
| `NotificationReadToolAdapter` | **ADAPT** — thin map over the manager. | **LEAVE** `AssistantTool`. | TM-09 |
| `NotificationDismissToolAdapter` | **LEAVE** — dismiss is an on-device assistant action, not a first read capability. | **LEAVE** | TM-05 |
| `DeviceStateMonitor` | **LEAVE** — exploratory posture for the on-device bus, not a call capability. INFO only. | **LEAVE** | TM-05 |

## Findings from this phase

- **P10PRE-AUD-01** `[RISK]` HIGH — Proactive SMS loads Firestore person entities and emits an in-process brain event. `SmsReceiver.kt` 104–134; `SmsContentProviderPoller.kt` 159–182. Challenges TM-01, TM-02, TM-09.
- **P10PRE-AUD-03** `[RISK]` MEDIUM — Sent SMS body is written to logcat (`MessageSendToolAdapter.kt` 135). Challenges TM-08.
- **P10PRE-AUD-05** `[RISK]` MEDIUM — Proactive capture dies with the activity bus/scope (`SmsReceiver.kt` 113–115; `MainActivity.kt` 649–657, 2168–2183). Challenges TM-06.
- **P10PRE-AUD-11** `[MATCH]` — — SMS acquisition exists as a broadcast, an inbox poll, and on-demand provider queries, without a default-SMS role. TM-05.
- **P10PRE-AUD-12** `[MATCH]` — — A notification listener and an on-demand shade read exist. TM-05.
- **P10PRE-AUD-13** `[MATCH]` — — On-demand SMS results are named maps (`sender_name`, `sender_phone`, `body`, `date_ms`, `thread_id`, `is_mms` / `is_group`). `MessageReadToolAdapter.kt` 426–434 and 1173–1186. TM-09 field shape only.
