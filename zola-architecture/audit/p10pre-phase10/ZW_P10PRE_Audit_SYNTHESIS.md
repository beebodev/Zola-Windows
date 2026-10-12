# P10PRE Synthesis

Salvage survey of `ZolaAssistant` (`zola-main` at `a139ccacab596f12b95e2dd3eda14352bcb97836`) against the provisional Companion Target Model and Zola-Windows lore (`S73`, `S13`, `S74`). This is not a Phase 10 design.

INFO (lore vs strawman, no finding ID): `S73` says the strawman `Zola_Architecture_Distributed_Presence_Device_Capabilities.md` predates Phases 6–8, that its DP entries are proposals, and that gateway placement (DP-Q01) and a general registry should wait until the first two or three capabilities are hardcoded. Lore wins where they differ. This audit does not score gateway placement.

INFO: `S13` remains an open research item. Its body still lists Phone Link and a Twilio number as candidates, plus a P9-KICKOFF brainstorm that is marked not a decision. The brainstorm's `MessagingStyle` shape is not what the old listener extracts.

## Section 1 — Finding summary

| ID | Label | Severity | Verdict | File | Summary |
| --- | --- | --- | --- | --- | --- |
| P10PRE-AUD-01 | RISK | HIGH | LEAVE (architecture) / ADAPT (parse) | `proactive/sms/SmsReceiver.kt` 104–134; `SmsContentProviderPoller.kt` 159–182 | Proactive SMS loads Firestore people and emits a brain-bus event. |
| P10PRE-AUD-02 | RISK | HIGH | ADAPT query / LEAVE tool type | `agent/tools/adapters/MessageReadToolAdapter.kt` 56–64; `NotificationReadToolAdapter.kt` 12–16 | On-demand capture is an on-phone `AssistantTool`, not a remote capability result. |
| P10PRE-AUD-03 | RISK | MEDIUM | ADAPT | `MessageSendToolAdapter.kt` 135; `MainActivity.kt` 2151 | Logcat receives an SMS body preview and the Google account email. |
| P10PRE-AUD-04 | GAP | HIGH | No old component | (no pairing or PC client class) | Nothing exchanges data with a PC or proves which phone sent it. |
| P10PRE-AUD-05 | RISK | MEDIUM | ADAPT lifetime | `SmsReceiver.kt` 113–115; `MainActivity.kt` 649–657, 2168–2183 | Poller and bus live in the activity; a receiver emit is dropped if the bus is unset. |
| P10PRE-AUD-06 | RISK | MEDIUM | REWRITE | `presence/fcm/ZolaFcmService.kt` 42–58, 73–110 | FCM is present, and the handler is Firebase Auth plus Firestore handoff. |
| P10PRE-AUD-07 | RISK | HIGH | — | `app/src/main/assets/diagflow_service_account.json` line 5 | Private key material is in the tree. Commit status not checked. |
| P10PRE-AUD-08 | RISK | HIGH | — | `app/google-services.json` 31; `local.properties` 11, 14, 15; `progress docs/PHASE0_TRACK_A_PROGRESS.md` 626 | API key patterns are in the tree. Commit status not checked. |
| P10PRE-AUD-09 | RISK | MEDIUM | LEAVE as provenance | `DeviceInstallIdProvider.kt` 32–39; `ZolaFcmService.kt` 85–89 | Install id is plain prefs; FCM token is stored in Firestore. |
| P10PRE-AUD-10 | RISK | LOW | LEAVE | `AndroidManifest.xml` 122–129; `CognitivePrepDebugReceiver.kt` 21–24 | Debug receiver is exported; release builds return immediately. |
| P10PRE-AUD-11 | MATCH | — | ADAPT | `SmsReceiver.kt`; `SmsContentProviderPoller.kt`; `MessageReadToolAdapter.kt` | SMS can be acquired without a default-SMS role. |
| P10PRE-AUD-12 | MATCH | — | ADAPT | `AvaNotificationListenerService.kt`; `NotificationReadManager.kt` | Notification access is a bound listener plus an on-demand read. |
| P10PRE-AUD-13 | MATCH | — | ADAPT | `MessageReadToolAdapter.kt` 426–434, 1173–1186 | Unread and last-from-sender results use named fields. |
| P10PRE-AUD-14 | RISK | LOW | ADAPT | `utils/LocationHelper.kt` 150–154 | A resolved fix logs latitude and longitude. |

Counts: 14 findings — 5 HIGH, 4 MEDIUM, 2 LOW; 3 MATCH. HIGH ids: 01, 02, 04, 07, 08. MEDIUM: 03, 05, 06, 09. LOW: 10, 14. MATCH: 11, 12, 13.

### INFO items (not findings)

1. `S13` still names Phone Link and Twilio beside the companion brainstorm.
2. `S74` is present and open. Call items stay exploratory.
3. Strawman vs `S73`: DP ids are proposals; registry and gateway placement are not decisions.
4. No `ROLE_SMS`, `SMS_DELIVER`, or `ContentObserver`.
5. RCS appears as MMS provider rows, not a separate API.
6. Listener uses `EXTRA_TITLE` / `EXTRA_TEXT` / `EXTRA_BIG_TEXT`, not `MessagingStyle`, and does not skip group summaries.
7. `READ_PHONE_STATE` is checked and not declared.
8. No `BOOT_COMPLETED`, no battery-exemption request, no Samsung Device Care API.
9. No PC or LAN endpoint. Phone opens cloud connections outbound. No app listening socket.
10. TM-07 queue properties are absent. That absence is a fact.
11. OAuth client ids are present in build config and `google-services.json` (identifiers, values not printed).
12. Gradle project name is `AvaPersonalAssistant`; application id is `com.beebo.zolaassistant`.
13. `smsAnalysisConsent` gates the brief, not the receiver, poller, or read tool.
14. FCM does not start SMS or notification capture.
15. `targetSdk` 35, `compileSdk` 36. Behavior is not an Android 16 compliance result.
16. Debug cleartext is limited to emulator loopback.
17. `.gitignore` names `local.properties`, `app/google-services.json`, and the service-account JSON. It does not name keystores. Some later ignore lines did not read as plain ASCII.
18. `LocationEventProducer` comment says it was not wired to `LocationHelper` in that wave.
19. Call posture is a boolean on the brain bus.

## Section 2 — Build plan implications

A later plan has to account for these. This section does not choose a design.

- **P10PRE-AUD-04.** There is no component to extend into phone–PC reachability or fail-closed provenance. The plan starts from nothing on that axis.
- **P10PRE-AUD-01.** `SmsReceiver` and `SmsContentProviderPoller` call `FirestoreHybridMemoryRepository` and the environmental bus. Lifting them unchanged pulls Zola memory onto the phone.
- **P10PRE-AUD-02.** `MessageReadToolAdapter`, search, send, and `NotificationReadToolAdapter` are `AssistantTool` types. The query code is in the same class as the brain contract.
- **P10PRE-AUD-05.** Proactive SMS does not survive process death as an event source. The plan cannot treat the current poller as a background capability.
- **P10PRE-AUD-06.** `ZolaFcmService` is the only push receiver. Its messages mean handoff and session invalidation and require Firebase Auth and Firestore. Reusing the class as a companion wake copies that coupling. The existence of FCM is still a fact for the transport spike.
- **P10PRE-AUD-07, P10PRE-AUD-08, P10PRE-AUD-09, P10PRE-AUD-03, P10PRE-AUD-14.** Secret files, log previews, and non-Keystore token storage are in the tree the plan would copy from.
- **P10PRE-AUD-10.** A debug-only exported receiver is in the main manifest. A new app manifest should not copy it by habit.
- **P10PRE-AUD-11, P10PRE-AUD-12, P10PRE-AUD-13.** SMS and notification access already have concrete Android entry points and, for SMS reads, named fields. Those are the salvage surfaces.

## Section 3 — Pre-work required

Before a build copies this tree:

1. Treat `app/src/main/assets/diagflow_service_account.json` as a live private key. Rotate it if it was ever a real account. This audit did not check Git history.
2. Treat the API key patterns in `app/google-services.json`, `local.properties` (lines 11, 14, 15), and `progress docs/PHASE0_TRACK_A_PROGRESS.md` line 626 as live candidates. Rotate any that are real. Commit status was not checked. Also review `GEMINI_API_KEY` and `DEEPGRAM_API_KEY` property values, which were not pattern-matched.
3. Do not print those values into tickets or logs while rotating them.

No other pre-work is required to *read* the salvage map. Building a companion is blocked on the open questions in Section 5, not on a missing audit file.

## Section 4 — Target Model confirmed

**TM-05.** SMS acquisition exists without a default-SMS role (AUD-11). Notification acquisition exists as a listener plus on-demand read (AUD-12).

**TM-09.** On-demand SMS results already use a plain field map (AUD-13). That confirms the shape, not the boundary. The boundary is a risk (AUD-01, AUD-02).

No MATCH was recorded for TM-01, TM-02, TM-03, TM-04, TM-06, TM-07, or TM-08.

## Section 5 — Open questions

### Raised by evidence

- Proactive SMS will not emit known-contact events unless the phone already holds Firestore person records and a live bus. A companion that must not keep Zola memory cannot reuse that filter. What replaces "known contact" is a product question, not answered here.
- `smsAnalysisConsent` does not cover the receiver, the poller, or `MessageReadToolAdapter`. Those paths run on permission and feature flags alone.
- The listener does not read `MessagingStyle`. `S13`'s brainstorm assumed Google Messages extras that include recent thread messages. The code does not do that. Whether the companion needs thread history is open.
- The poller advances past every new inbox id, then emits at most one known-contact snippet. Unknown senders are consumed from the cursor and never emitted. Any later event design has to notice that.
- FCM as implemented cannot wake capture. Whether some other use of FCM is acceptable is a transport question (Section 8), and it is tied to Firebase Auth and Firestore today.
- Secret candidates may or may not be in Git. That has to be checked outside this audit's no-Git rule before anyone assumes they were never pushed.

### Unresolved design options (not decided here)

- Per capability (SMS, notifications, and later contacts, location, health): request/response, event delivery, subscription, or a mix. Evidence: Phases 3, 5, and 8. SMS already has a local query (`MessageReadToolAdapter.invoke`) and a separate in-process event (`SmsReceiver`, poller). Notifications already have a local query (`NotificationReadToolAdapter.invoke`) and do not emit per posted notification. Neither path leaves the phone.
- Android access method for SMS (role, listener, provider, or other) and for notifications. The old app uses the provider plus `SMS_RECEIVED`, and a notification listener. That is evidence, not a selection.
- TM-03 connection direction and wake mechanism.
- TM-07 whether a queue is needed, and its contract, after the delivery model is chosen.
- Gateway placement and a capability registry (`S73`, DP-Q01). Hardcoding the first capabilities is the strawman review note, not a decision this audit locks.
- `S74` remote escalation. Out of scope for reuse verdicts.

Challenged TM items: TM-01 (AUD-01, AUD-02), TM-02 (AUD-01, AUD-06), TM-03 exchange (AUD-04; direction and wake stay open), TM-04 (AUD-04), TM-06 (AUD-05), TM-08 (AUD-03, AUD-07, AUD-08, AUD-09, AUD-10, AUD-14), TM-09 (AUD-01, AUD-02). TM-05 and TM-07 were not given gaps.

## Section 6 — Reuse matrix

| Component | Files | Verdict | Seam (Phase 7) | Bounded changes | Finding IDs |
| --- | --- | --- | --- | --- | --- |
| `SmsReceiver` | `proactive/sms/SmsReceiver.kt` | ADAPT platform / LEAVE architecture | DEEP | Drop Firestore match and bus emit; keep PDU parse only if events are wanted | 01, 05, 11 |
| `SmsContentProviderPoller` | `proactive/sms/SmsContentProviderPoller.kt` | ADAPT platform / LEAVE architecture | DEEP | Same cut; lifetime is not a service | 01, 05, 11 |
| `MessageReadToolAdapter` | `agent/tools/adapters/MessageReadToolAdapter.kt` | ADAPT | DEEP | Extract queries and maps from `AssistantTool` | 02, 11, 13 |
| `MessageSearchToolAdapter` | `agent/tools/adapters/MessageSearchToolAdapter.kt` | ADAPT | DEEP | Same cut; body cap stays explicit | 02, 11 |
| `MessageSendToolAdapter` | `agent/tools/adapters/MessageSendToolAdapter.kt` | ADAPT | DEEP | Remove body log; send is not required for a read-only first cut | 02, 03 |
| `SmsWarmDataProvider` | `sms/SmsWarmDataProvider.kt` | LEAVE | DEEP (brief) | Brief warm cache | 01 |
| `AvaNotificationListenerService` | `notification/AvaNotificationListenerService.kt` | ADAPT | THIN | Keep the binding; stop storing raw `StatusBarNotification` as the API | 12 |
| `NotificationReadManager` | `notification/NotificationReadManager.kt` | ADAPT | DEEP | `NotificationSummary` is the data cut; scanner and tool share it | 02, 12 |
| `NotificationReadToolAdapter` | `agent/tools/adapters/NotificationReadToolAdapter.kt` | ADAPT | THIN | Replace `AssistantTool` return type | 02, 12 |
| `NotificationDismissToolAdapter` | `agent/tools/adapters/NotificationDismissToolAdapter.kt` | LEAVE | THIN | On-device dismiss action | — |
| `DeviceStateMonitor` | `environment/device/DeviceStateMonitor.kt` | LEAVE | DEEP | Exploratory call boolean. INFO | — |
| `ListeningService` | `ListeningService.kt` | LEAVE | DEEP | Voice foreground service | — |
| Reminder, session, consolidation, sports, cognitive workers | `reminder/`, `memory/consolidation/`, `memory/session/`, `sports/`, `cognitive/prep/` | LEAVE | DEEP | Not phone capabilities | 10 (debug receiver only) |
| `ZolaFcmService` | `presence/fcm/ZolaFcmService.kt` | REWRITE | DEEP | Push entry only; do not reuse handoff | 06 |
| Device registration and handoff | `presence/device/`, `presence/handoff/` | LEAVE | DEEP | Old multi-device brain | 06, 09 |
| `DeviceInstallIdProvider` | `presence/device/DeviceInstallIdProvider.kt` | LEAVE | THIN | Not pairing proof | 04, 09 |
| `ContactsLookupToolAdapter` | `agent/tools/adapters/ContactsLookupToolAdapter.kt` | ADAPT | DEEP | Query is separable from `AssistantTool` | 02 |
| `LocationHelper` | `utils/LocationHelper.kt` | ADAPT | THIN at `getCurrentLocationFix` | One-shot fix; remove coordinate log | 14 |
| `HealthConnectManager` | `health/HealthConnectManager.kt` | ADAPT | THIN | Read methods do not implement `AssistantTool` | — |
| PC client | — | No old component | NONE | — | 04 |
| Pairing handshake | — | No old component | NONE | — | 04 |
| Transport queue | — | No old component | NONE | Absence is a TM-07 fact | — |
| Battery-exemption helper | — | No old component | NONE | — | — |
| Boot restart of capture | — | No old component | NONE | — | 05 |

Verdict tally: REUSE 0, ADAPT 11, REWRITE 1, LEAVE 7, No old component 5. The two SMS proactive classes are counted as ADAPT (platform) and also carry an architecture LEAVE in the verdict cell, not as extra rows. LEAVE rows are warm provider, dismiss, device-state monitor, listening service, Tier 2 workers (one row), device registration, and install-id provider (7). ADAPT rows are the two SMS classes, three message adapters, listener, read manager, read tool, contacts, location, and health (11). REWRITE is FCM (1). No old component rows: PC client, pairing, transport queue, battery exemption, and boot restart (5).

## Section 7 — Capability table

| Capability | Acquisition mechanism | Must stay active? | Old delivery mode | Delivery models supportable | Adapter fit | Consent observed | Finding IDs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SMS | `SMS_RECEIVED`; inbox poll; `Telephony` / MMS query | Poller and bus yes; query no | In-process event and/or local tool response. No PC path | Local on-demand yes; in-process events yes; PC stream missing | WITH CHANGES | Runtime SMS permissions; person-match and quiet hours on the proactive path; brief consent does not gate these classes | 01, 02, 03, 05, 11, 13 |
| Notifications | `NotificationListenerService` | Yes, to fill the buffer | Local tool read of the buffer. Nudge is separate and in-process | Local on-demand yes; per-post events no | WITH CHANGES | One-time system settings screen | 02, 12 |
| Calls | INFO. Audio mode and optional telephony callback | Yes while the monitor is started | INFO. Bus boolean. No PC path | INFO. Not a call API | NO | `READ_PHONE_STATE` undeclared | — |
| Contacts | `ContactsContract` query | No | Local tool response | Local on-demand yes; events no | WITH CHANGES | Runtime `READ_CONTACTS` | 02 |
| Location | One-shot fused update | No | Return value to caller | Local on-demand yes | WITH CHANGES | Manifest location permissions | 14 |
| Health | Health Connect `readRecords` | No | Return value to caller | Local on-demand yes | WITH CHANGES | Health Connect grants; rationale activity-alias | — |

## Section 8 — Questions for the transport spike

Questions only.

- How does the phone reach the PC at home, and how does it reach the PC away from home, given this app has no PC address and no listening socket?
- Which side opens the connection?
- How is a sleeping phone woken: a connection the phone holds, a push such as FCM, or polling? The only push receiver today handles Firestore handoff and depends on Firebase Auth.
- What does the PC check before it accepts a result, given there is no pairing record?
- What is the request/response contract for a capability that today only answers an in-process `AssistantTool` call?
- What is the event or subscription contract for a capability whose only event is an in-memory bus payload?
- What happens to SMS or notifications that arrive while the PC is unreachable, given there is no ack, retry, or delete-after-ack queue?

## Section 9 — Questions requiring current Android 16 / Play policy verification

Each names old behavior. None is answered from memory.

- `SmsReceiver` is a non-exported manifest receiver for `SMS_RECEIVED`, and the app does not request the SMS role. The poller reads `Telephony.Sms.Inbox` with `READ_SMS`. Which of those are still allowed for a companion that is not the user's SMS app, on Android 16 and under current Play policy, on a Galaxy S23 Ultra?
- The inbox poll runs on an activity coroutine, not a foreground service. If a companion needs that loop while the UI is gone, which foreground-service type, exemption, or scheduler is still permitted? The old app's exemption request is absent, and its only foreground service is `microphone|shortService` for voice (`ListeningService.kt` 96–111).
- `AvaNotificationListenerService` must be enabled by the user under notification access, and it reads title and text rather than `MessagingStyle`. What disclosure and Play declaration does that listener require now, and does policy restrict which packages may be read?
- `WRITE_SMS` and mark-read update the provider (`MessageReadToolAdapter` mark-read path). Is that still a permitted use for a non-default SMS app?
- `READ_PHONE_STATE` is used and not declared (`DeviceStateMonitor.kt` 305–307). Call items are exploratory only; any later call work needs a current permission and role answer. `S74` is deferred.
- Health Connect reads and location reads are extra capabilities. What consent and policy text is required before they are exposed off-device? The old code only shows local reads.
- Samsung comments in `MessageReadToolAdapter.kt` 217–234 claim `spam_report` behavior on SM-S918U1. Verify on current One UI before a plan depends on that column.
- `targetSdk` is 35 and `compileSdk` is 36. Confirm the target a new companion must ship, without treating this app's behavior as evidence that the target is already met.

## Section 10 — Background lessons

- BACKGROUND: Brief SMS analysis is opt-in and defaults off. The capture classes do not read that flag.
- BACKGROUND: The notification listener was already described, in old audits, as a process-local buffer rather than a bus of notification events.
- BACKGROUND: Old device-registration prose says FCM can be delayed by battery management and lists a PC as a future endpoint. The implemented handler is handoff.
- BACKGROUND: Old watchdog notes refused a battery-exemption permission and required a visible foreground notification for microphone listening. That is not an SMS design.
- BACKGROUND: A Phase 49 note treats Doze as a risk for a short session alarm. The capture poller does not use that alarm.
- BACKGROUND: Samsung inbox and spam-column comments are workarounds in the read adapter, not a current compatibility certificate.

Awaiting "proceed to closeout". No commit was made.
