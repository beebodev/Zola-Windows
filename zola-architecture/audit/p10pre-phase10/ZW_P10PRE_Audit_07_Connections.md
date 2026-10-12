# P10PRE Phase 7 — Connection Check (Tier 2)

Tier 2 bodies were not reviewed. This table is imports and call sites from Tier 1 components in Phases 3–5.

## 1. Connections

| Tier 1 component | Tier 2 target | Type | File and line |
| --- | --- | --- | --- |
| `SmsReceiver` | `FirestoreHybridMemoryRepository.loadEntities` | direct call | `SmsReceiver.kt` 106 |
| `SmsReceiver` | `FirebaseAuth` | direct call | `SmsReceiver.kt` 97 |
| `SmsReceiver` | `EnvironmentalEventBus` / `EventPayload.SmsReceived` | static holder, then emit | `SmsReceiver.kt` 58–59, 122–133 |
| `SmsReceiver` | `AutonomousPolicy.isQuietHoursWallClockProduction` | direct call | `SmsReceiver.kt` 74 |
| `SmsContentProviderPoller` | `FirestoreHybridMemoryRepository.loadEntities` | direct call | `SmsContentProviderPoller.kt` 255 |
| `SmsContentProviderPoller` | `EnvironmentalEventBus` | constructor injection and emit | lines 41, 171–182 |
| `SmsContentProviderPoller` | `AutonomousPolicy` | constructor | line 39 |
| `SmsWarmDataProvider` | brief warm path (`ToolWarmStartAgent`, `SmsIntelligenceAnalyzer`) | caller in Tier 2 pulls this query | consent gate `SmsIntelligenceAnalyzer.kt` 21; provider itself is the query |
| `MessageReadToolAdapter` | `AssistantTool` / `ToolResult` | interface | `MessageReadToolAdapter.kt` 56–58, 144 |
| `MessageSearchToolAdapter` | `AssistantTool` | interface | class declaration |
| `MessageSendToolAdapter` | `AssistantTool`; `ContactsLookupToolAdapter`; `MessageReadContext` | direct call | `MessageSendToolAdapter.kt` 58–68, 136 |
| `NotificationReadToolAdapter` | `AssistantTool` | interface | lines 12–24 |
| `NotificationDismissToolAdapter` | `AssistantTool` | interface | class declaration |
| `AvaNotificationListenerService` buffer | `ProactiveMemoryAwarenessScanner` | Tier 2 scanner calls `NotificationReadManager` | `ProactiveMemoryAwarenessScanner.kt` 161–162, emit 227 |
| `DeviceStateMonitor` | `EnvironmentalEventBus`, `UserStateReducer` | constructor and emit | `DeviceStateMonitor.kt` 39, 86–104 |
| `ListeningService` | `GatekeeperEngine`, `SileroVadEngine`, `PerceptionEventBus`, `GatePassOverlayManager` | direct construction | `ListeningService.kt` 23–27, 116–118 |
| `ZolaFcmService` | `FirebaseAuth`, `FirebaseFirestore`, `HandoffContextSerializer`, `DeviceRegistrationRepository` | direct call | `ZolaFcmService.kt` 9–10, 78–89, 105 |
| `MainActivity` wiring | constructs poller, bus, auth, monitors | composition root | `MainActivity.kt` 607–657, 2168–2183 |

Live executors (`LiveMessageReadExecutor`, `LiveNotificationReadExecutor`, `LiveMessageSendExecutor`) call the adapters. Those executors are Tier 2; their internals were not read. The adapters' `AssistantTool` type is the seam.

## 2. Seam

| Component | Seam | Why |
| --- | --- | --- |
| `SmsReceiver`, `SmsContentProviderPoller` | **DEEP** | Shared bus, Firebase Auth, and Firestore entity memory. Many fields on the brain event. |
| `MessageReadToolAdapter`, search, send | **DEEP** | One class owns provider I/O and the brain tool contract. Live and NL handlers are additional call sites. |
| `NotificationReadManager` | **DEEP** | Shared in-memory buffer used by the read tool and the proactive scanner. |
| `NotificationReadToolAdapter` | **THIN** | One mapping function over `NotificationReadManager`, still typed as `AssistantTool`. |
| `AvaNotificationListenerService` | **THIN** at the service boundary | System callback writes a buffer. Coupling starts at the consumers. |
| `DeviceStateMonitor` | **DEEP** | Exists to feed the brain bus. |
| `ListeningService` | **DEEP** | Voice stack. |
| `ZolaFcmService` | **DEEP** | Auth, Firestore token, Firestore handoff document. |
| `DeviceInstallIdProvider` | **THIN** | One prefs key, but the only caller path found is Firebase registration. |
| PC client | **NONE** | No component. |

## 3. Firebase other than FCM

Tier 1 SMS proactive path depends on Firebase Auth for the user id and on Firestore for person phones. That is identity plus memory storage, not app config. `SmsWarmDataProvider` does not import Firebase; the brief that consumes it does (Tier 2). Device registration uses Firestore as storage for the FCM token and device record.

Notification read and `MessageReadToolAdapter` queries do not import Firebase. Their callers in Live and the brief do.

## 4. Firebase Cloud Messaging

Present.

| Question | Evidence |
| --- | --- |
| Receiver | `ZolaFcmService` (`presence/fcm/ZolaFcmService.kt`), manifest lines 113–120, `exported="false"`. |
| Dependency | `firebase-messaging-ktx` in `app/build.gradle.kts` line 205. |
| What a message triggers | Data payload `type`. `HANDOFF_CONTEXT_AVAILABLE` logs and calls `HandoffContextSerializer.readIfFresh` (lines 45–49, 95–110). `SESSION_INVALIDATED` logs `newActiveDeviceId` and does not tear down (lines 51–53). Other types are ignored (lines 55–57). |
| Wake a capture or the brain? | It does not start `SmsReceiver`, the poller, or the notification listener. It does not call an LLM in this class. It reads handoff context from Firestore, which is brain/session state. |
| Depends on Firebase Auth or Firestore? | Yes. Token store and handoff read both require a current Firebase user and `FirebaseFirestore` (lines 78–89, 100–105). Gated by `ZolaFeatureFlags.ENABLE_DEVICE_REGISTRATION`. |

FCM is a possible wake mechanism in the abstract (TM-03). This implementation is not a capability wake. Verdict **REWRITE**, not LEAVE. **P10PRE-AUD-06**.

## 5. Shared database or DI with the brain

- No Room database is shared.
- Firestore is shared: SMS proactive filtering reads the same person entities the brain writes.
- The environmental bus is a process singleton/holder shared with proactive speech.
- There is no DI graph file. Wiring is `MainActivity` constructors plus `SmsReceiver.setEnvironmentalEventBus`.
- Tool adapters share the `AssistantTool` type with the rest of the agent tool set.

## 6. Verdict updates

Phase 3 ADAPT/LEAVE splits stand. Coupling makes the architecture side **LEAVE** or **REWRITE**, not REUSE.

| Component | Updated verdict | Reason |
| --- | --- | --- |
| `SmsReceiver`, poller | Platform **ADAPT**, architecture **LEAVE** | DEEP Firestore and bus seam. |
| `MessageReadToolAdapter`, search, send | **ADAPT** the query and field maps; **LEAVE** `AssistantTool` | DEEP tool seam. Not REUSE. |
| `NotificationReadManager` | **ADAPT** | Structured summary is separable; consumers are not. |
| `ZolaFcmService` | **REWRITE** | Push receiver is the salvageable idea; handler is Auth plus Firestore handoff. |
| `ListeningService`, `DeviceStateMonitor` | **LEAVE** | DEEP voice and brain-bus coupling. Call monitor stays INFO. |
| Pairing proof, PC socket, transport queue | **No old component** | Seam NONE. |

No Tier 1 component is REUSE after this pass.
