# P10PRE Phase 8 — Capability Fit

No new Tier 2 internals. Delivery-model choices are not made. "Supportable with little change" means a path that already exists in the old app, not a preference.

## SMS

1. **Classes.** `SmsReceiver`, `SmsContentProviderPoller`, `MessageReadToolAdapter`, `MessageSearchToolAdapter`, `MessageSendToolAdapter`, `SmsWarmDataProvider`.
2. **Acquisition.** Broadcast `SMS_RECEIVED`; inbox poll every 2 minutes while the activity scope runs; on-demand `ContentResolver` queries of `Telephony.Sms` and `content://mms`. Runtime `RECEIVE_SMS`, `READ_SMS`, `SEND_SMS`, `WRITE_SMS`. Not the default SMS role. The poller and the bus holder must be alive for proactive emit. On-demand query does not need a resident listener.
3. **Delivery.** No PC path. Proactive classes forward one in-process event (known contact, 80-character snippet) and do not answer a remote request. On-demand adapters answer a local tool request. Nothing queues for another device. No push/wake for SMS. FCM does not start these classes.
4. **Models the code could support with little change.**
   - On-demand answers: **yes, locally.** `MessageReadToolAdapter.invoke` actions `unread_summary`, `last_from_sender`, `unread_count`, `mark_read`.
   - Event reporting: **yes, in-process only.** `SmsReceiver.onReceive` and `SmsContentProviderPoller.pollForNewMessages`. A PC event stream is missing (no outbound client, no durable queue).
   - Both: the two paths are separate code. Nothing fans a provider query out to a remote subscriber.
5. **Output.** Proactive: `EventPayload.SmsReceived` (`sender`, `messageSnippet`) tied to the brain bus. On-demand: `Map` fields `sender_name`, `sender_phone`, `body`, `date_ms`, `thread_id`, `is_mms`, and for last-from-sender also `direction`, `threadId`, `thread_name`, `is_group`. The map is built inside `ToolResult`, which is a brain tool type. Search uses `sender`, `body`, `date`, `threadId`, `isGroup`.
6. **Adapter fit.** **WITH CHANGES.** Keep the provider queries and maps; remove Firestore person matching, the bus emit, and `AssistantTool`. Phase 7 seam DEEP. **P10PRE-AUD-01**, **P10PRE-AUD-02**, **P10PRE-AUD-13**.
7. **Remote command router.** Not present. `AssistantTool` is an in-process router for the on-phone model.
8. **Consent and retention.** Runtime permission dialog (`MainActivity.kt` 2084–2095). Proactive path also requires a Firestore person with a matching phone and skips quiet hours. `smsAnalysisConsent` (default false, `DailyBriefSettings.kt` line 10) gates brief analysis only. No delete-after-read. Mark-read is a local provider update behind a confirm flag.

## Notifications

1. **Classes.** `AvaNotificationListenerService`, `NotificationReadManager`, `NotificationReadToolAdapter`. Dismiss adapter is a separate action.
2. **Acquisition.** `NotificationListenerService` while the user has enabled notification access. The listener must stay bound for `onNotificationPosted` to fill the buffer. There is no query of a notification history provider.
3. **Delivery.** No PC path. Reads are local tool calls. `ProactiveMemoryAwarenessScanner` may emit one `NotificationNudge` (`appLabel`, `titleSnippet`) on the brain bus. That is not "forward each notification."
4. **Models.**
   - On-demand answers: **yes, locally**, if the buffer has been filled. `NotificationReadToolAdapter.invoke` (`max_results`, `app_filter`).
   - Event reporting: **no per-item stream.** `onNotificationPosted` only mutates the buffer (`AvaNotificationListenerService.kt` 20–25). A nudge scanner is a separate, throttled brain path.
   - Both: missing. The listener does not invoke a reporter.
5. **Output.** `NotificationSummary`: `key`, `packageName`, `appLabel`, `title`, `text`, `postedAtMs`. Tool map uses `app` instead of `appLabel`. Plain data object, then wrapped in `ToolResult`. Title and text come from `EXTRA_TITLE` and `EXTRA_TEXT` / `EXTRA_BIG_TEXT`, not `MessagingStyle`.
6. **Adapter fit.** **WITH CHANGES.** `NotificationReadManager.toSummary` is close to a narrow adapter. The service object buffer and the tool interface are the cuts. Seam THIN at the service, DEEP at the shared buffer. **P10PRE-AUD-12**.
7. **Remote router.** Not present.
8. **Consent.** One-shot settings redirect (`MainActivity.kt` 2098–2118) stored in a boolean preference. No retention clock. Cap 20, process lifetime. Dismiss requires `_confirmed` (`NotificationDismissToolAdapter.kt` 31–39) and is not a read.

## Calls (exploratory INFO)

1. `DeviceStateMonitor.readCallActive` and `registerTelephonyListener`.
2. Acquisition: audio mode always; telephony callback only if `READ_PHONE_STATE` is granted (it is not in the manifest). Must stay started by the activity for continuous updates.
3. Delivery: in-process bus boolean `callActive`. No PC path. No call audio, no number on the API 31 callback.
4. Neither a call-control capability nor a remote event stream. `S74` is deferred. No MATCH/GAP/RISK.
5. Payload keys are posture strings, not a call record.
6. Adapter fit **NO** for a companion call capability — the class is a brain posture monitor. Verdict LEAVE.
7. Not present.
8. No call-consent UI. Permission is undeclared.

## Contacts

1. `ContactsLookupToolAdapter` (`READ_CONTACTS`). Also used by SMS send to resolve a name (`MessageSendToolAdapter.kt` 57–68). `MessageReadToolAdapter` uses `ContactsContract.PhoneLookup` for display names.
2. Acquisition: query on each lookup. Does not need a listener. Runtime prompt from `MainActivity.scheduleWaveKPermissionPrompts` (lines 2065–2074).
3. Delivery: local tool response. No PC path.
4. On-demand answers: yes, locally (`name`, `max_results`). Event reporting: not present.
5. Maps with `name` and `phone` (send path reads `phone`, lines 98–100). `ToolResult` wrapper.
6. **WITH CHANGES.** Query is separable; type is `AssistantTool`.
7. Not present for a remote caller.
8. Runtime permission. No local retention of the contact list was found in this class.

## Location

1. `LocationHelper.getCurrentLocationFix` (`utils/LocationHelper.kt` 69, 167). Permissions `ACCESS_FINE_LOCATION` and `ACCESS_COARSE_LOCATION`. `LocationEventProducer` is a bus adapter; its own comment says it was not wired to `LocationHelper` in that wave (`LocationEventProducer.kt` lines 11–12). `MainActivity` still constructs a producer (line 600). This audit does not treat that constructor as continuous forwarding.
2. Acquisition: one-shot fused request (`setMaxUpdates(1)`, lines 140–170). The callback is removed after one fix. It does not have to stay active.
3. Delivery: return value to the caller. No PC path. Logcat includes coordinates (Phase 6).
4. On-demand: yes, locally. Events: a producer method `onLocationUpdate` exists; a continuous PC stream does not.
5. `CurrentLocationFix`: `lat`, `lng`, `accuracyMeters`. Plain data class, then consumed by place/maps code (Tier 2 callers not inspected).
6. **WITH CHANGES.** The fix method is narrow. Logging and Places/OkHttp methods in the same class are extra. **P10PRE-AUD-14**.
7. Not present.
8. Manifest permissions. No separate consent screen was read. No retention of fixes in this method.

## Health

1. `HealthConnectManager`. Permissions `health.READ_STEPS`, `health.READ_SLEEP`, `health.READ_HEART_RATE`. Activity-alias for the Health Connect rationale (`AndroidManifest.xml` 64–74).
2. Acquisition: on-demand `readRecords`. Client must be available. Permissions are Health Connect grants, not a resident listener in this class.
3. Delivery: return values to the caller. No PC path.
4. On-demand: yes (`readTodaySteps`, `readLastNightSleepHours`). Events: not present in this class.
5. Numeric snapshots, not a brain document. Callers are Tier 2 tools (not inspected).
6. **WITH CHANGES.** The manager does not implement `AssistantTool`. A tool adapter elsewhere likely wraps it; that wrapper was not part of the capture read. The manager itself is the closest thing to an isolated reader.
7. Not present.
8. Health Connect permission UI via the platform. Reads are not deleted by this class.

## Capability list another device could call

Not present. `DeviceCapabilities.toMap` is hardware flags for Firestore device registration, not an RPC surface.
