# P10PRE Phase 10 — Gaps Against the Target Model

Open or report-only items are facts, not `[GAP]`: per-capability delivery model (TM-05), queue contract (TM-07), and which side opens the connection or how a sleeping phone is woken (TM-03). `[RISK]` still applies where code conflicts with a firm rule.

## TM-01 Capability endpoint

`[RISK]` **P10PRE-AUD-01**, **P10PRE-AUD-02**.

The phone runs the brain. Proactive SMS emits `sms_received` onto `EnvironmentalEventBus` after a Firestore entity match (`SmsReceiver.kt` 104–134, `SmsContentProviderPoller.kt` 159–182). On-demand reads implement `AssistantTool` and return `ToolResult` (`MessageReadToolAdapter.kt` 56–64, `NotificationReadToolAdapter.kt` 12–16). There is no request/response or event contract with another device.

Fact, not a gap: which of request/response, events, or a subscription a future capability should use is open. The old app happens to contain both a local query API and an in-process event. Neither is a PC contract. **Not present** for another device.

## TM-02 One authority

`[RISK]` **P10PRE-AUD-01**, **P10PRE-AUD-06**.

Firestore person entities gate proactive SMS. FCM writes tokens and reads handoff documents in Firestore (`ZolaFcmService.kt` 85–89, 105). `EncryptedSharedPreferences` stores enrichment replay and recent turns (brain). The phone is a second Zola-memory store. A bounded transport queue is not what those stores are.

## TM-03 Reachability

`[GAP]` **P10PRE-AUD-04** for the firm part: no code exchanges requests, results, or observations with a PC, at home or away.

Facts, not gaps:

- Which side opens: no PC connection exists. Cloud clients are phone-outbound. No listening socket.
- Wake: FCM is present (`ZolaFcmService.onMessageReceived`). It does not wake SMS or notification capture. It reads Firestore handoff or logs session invalidation. That dependency is **P10PRE-AUD-06** `[RISK]` because the payload is brain state (TM-02), not because "wake is unsolved."
- Polling the SMS provider is local. It does not wake a PC path.

## TM-04 Provenance and pairing

`[GAP]` **P10PRE-AUD-04**. Evidence that a result came from this paired phone: **not present**. `DeviceInstallIdProvider` is a UUID in plain prefs used for Firebase device docs. Unpaired input cannot be rejected because there is no pair.

## TM-05 First capabilities

`[MATCH]` **P10PRE-AUD-11** (SMS acquisition), **P10PRE-AUD-12** (notification listener).

Facts, not gaps:

| Capability | Acquisition | Delivery in the old app |
| --- | --- | --- |
| SMS | Receiver, inbox poll, provider query. Not default-SMS role. | Local tool response and/or in-process event. No PC path. |
| Notifications | Listener plus on-demand buffer read. Not `MessagingStyle`. | Local tool response. Nudge is a separate in-process event, not per-item forward. |
| Calls | INFO. `DeviceStateMonitor` boolean. `READ_PHONE_STATE` undeclared. | INFO. No PC path. `S74` deferred, so this is not MATCH/GAP/RISK. |

Missing request/response **to a PC**, or missing event delivery **to a PC**, is not scored as a gap.

## TM-06 Reliability

`[RISK]` **P10PRE-AUD-05**. The poller and the bus holder live in `MainActivity`. After process death the receiver can run and then drop the emit (`SmsReceiver.kt` 113–115). No boot receiver, no battery-exemption request, no Samsung Device Care handling. `ListeningService` shows how this app kept a microphone foreground service alive; that does not show that an SMS poller would survive Doze. Android 16 questions are in Phase 4 item 7 and Synthesis Section 9. Old behavior is not compliance.

## TM-07 Offline delivery (report-only)

No `[GAP]`.

| Property | Evidence |
| --- | --- |
| A queue of capability results | Not present |
| Acknowledgements | Not present |
| Retries | Not present (tool `retryable` is in-process) |
| Duplicate handling | In-process only: poller id cursor, listener key dedupe |
| Bounded size | Listener cap 20. Poller stores one id, not a message log |
| Delete after acknowledge | Not present |

A queue that stores Zola memory would be a TM-02 risk. The Firestore handoff and deferred-queue **design note** in old lore are brain state. The code path this audit verified, FCM handoff read, is **P10PRE-AUD-06**, not a TM-07 gap.

## TM-08 Secrets and data lifecycle

`[RISK]` **P10PRE-AUD-07** HIGH private key in tree; **P10PRE-AUD-08** HIGH API key candidates in tree; **P10PRE-AUD-03** MEDIUM message-body log; **P10PRE-AUD-09** MEDIUM Keystore miss; **P10PRE-AUD-14** LOW location log; **P10PRE-AUD-10** LOW exported debug receiver.

`[MATCH]` none for the full TM-08 rule. Partial facts: release network security config denies cleartext for the OpenWeather domain; debug cleartext is loopback only; notification listener binding requires `BIND_NOTIFICATION_LISTENER_SERVICE`; SMS send and notification dismiss require `_confirmed`.

Commit status of every secret candidate: **not checked**.

## TM-09 Adapter boundary

`[MATCH]` **P10PRE-AUD-13** — on-demand SMS maps already use plain field names.

`[RISK]` **P10PRE-AUD-01**, **P10PRE-AUD-02** — those maps and the listener sit inside brain types (bus events, `AssistantTool`, Firestore entity filter). Fit is WITH CHANGES, not isolated. No general capability registry exists, which matches the strawman review note to hardcode the first capabilities (INFO, `S73`). Absence of a registry is not a gap.

## Finding index

| ID | Label | Severity | TM |
| --- | --- | --- | --- |
| P10PRE-AUD-01 | Proactive SMS uses Firestore memory and the brain bus | RISK | 01, 02, 09 |
| P10PRE-AUD-02 | Capture tools are on-device `AssistantTool` adapters | RISK | 01, 09 |
| P10PRE-AUD-03 | SMS body preview (and account email) in logcat | RISK | 08 |
| P10PRE-AUD-04 | No phone–PC exchange or pairing proof | GAP | 03, 04 |
| P10PRE-AUD-05 | Proactive capture is activity-scoped and drops if the bus is unset | RISK | 06 |
| P10PRE-AUD-06 | FCM handler is Auth plus Firestore handoff | RISK | 02, 09 |
| P10PRE-AUD-07 | Service-account private key in the tree | RISK | 08 |
| P10PRE-AUD-08 | API key candidates in the tree | RISK | 08 |
| P10PRE-AUD-09 | Install id and FCM token are not Keystore-backed | RISK | 08 |
| P10PRE-AUD-10 | Exported debug prep receiver | RISK | 08 |
| P10PRE-AUD-11 | SMS acquisition mechanisms exist | MATCH | 05 |
| P10PRE-AUD-12 | Notification listener acquisition exists | MATCH | 05 |
| P10PRE-AUD-13 | On-demand SMS field map is plain data | MATCH | 09 |
| P10PRE-AUD-14 | Location coordinates in logcat | RISK | 08 |
