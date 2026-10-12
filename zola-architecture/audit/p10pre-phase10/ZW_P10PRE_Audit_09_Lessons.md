# P10PRE Phase 9 — Lessons Already Paid For

Every item is BACKGROUND. Repository B lore, decisions, open questions, and audits are not Phase 10 authority and are not findings. The Windows file `Zola Distributed Presence Architecture.md` was read only for historical lessons. It does not mention SMS capture, Doze, Samsung battery policy, or FCM. It mentions notifications as a presence surface, not as an Android listener design.

## 1. SMS and notification policy lessons

- BACKGROUND: Phase 12 build-plan note `P12-D02` in `zola-architecture/Zola_Phase12_Build_Plan.md` says SMS is excluded from the daily brief until the user opts in. The code default `smsAnalysisConsent = false` matches that note (`DailyBriefSettings.kt` line 10). The proactive receiver and the on-demand reader do not consult that flag.
- BACKGROUND: `Zola_Agent_Map.md` describes a future notification classifier (message vs alert vs spam). The listener that exists stores raw status-bar entries and extracts title and text only.
- BACKGROUND: `Deltas-v2/Zola_Audit_Findings_v2_05_Environmental.md` records that `AvaNotificationListenerService` is an in-memory buffer and does not emit on the environmental bus; a scanner may nudge later. That matches the code read in Phase 3.
- BACKGROUND: no Repository B document read in this pass states a Play Console SMS-role or default-SMS-handler decision. `RoleManager` / `ROLE_SMS` are absent from the current source. Do not treat that absence as a policy conclusion.
- BACKGROUND: notification access is a special setting, not a runtime permission. `MainActivity` sends the user to the system screen once.

## 2. Foreground service, Doze, Samsung, target SDK

- BACKGROUND: old perceptual-layer notes (`Zola_Architecture_Perceptual_Input_Layer.md`, Phase 18 plans) say a persistent watchdog wants a foreground service and a visible notification, and a Phase 18 audit said not to add `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`. The current tree still has no battery-exemption request. `ListeningService` is the microphone foreground service. Those notes are about on-device hearing, not SMS.
- BACKGROUND: `Zola_Phase49_Build_Plan.md` names Doze as a risk for a 30-second session grace timer. The code uses `setAndAllowWhileIdle` for that timer (`SessionIdentityProvider.kt` 255). That is session identity, not capture.
- BACKGROUND: `MessageReadToolAdapter.kt` lines 217–234 comment that Samsung One UI on SM-S918U1 (called Android 16 in the comment) has no `blocked` column and uses `spam_report`. This is a code comment, not a current policy verification.
- BACKGROUND: `Zola_Master_State_Audit.md` Gap 2 says an older `ListeningService` did nothing useful after Picovoice was removed. The current file starts a watchdog and gatekeeper. The stale audit sentence is not a description of this tree and is not a Phase 10 fact.

## 3. Networking, push, pairing, security

- BACKGROUND: `Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md` says FCM is unreliable under aggressive battery optimization and that critical coordination needs a non-FCM fallback (architectural risks, about line 704). The same document's long-term list includes a PC among future endpoints. That is old-app design prose. The code's FCM handler only reads handoff context.
- BACKGROUND: that document describes a shared Firestore deferred queue drained by the active device. It is brain/presence state, not a phone-to-PC SMS queue. TM-07 still has no capability-transport queue in code.
- BACKGROUND: no pairing or QR lesson was found that defines how a Windows PC would authenticate this phone.

## 4. Workaround comments in Tier 1 files

| File | Line | Comment |
| --- | --- | --- |
| `SmsContentProviderPoller.kt` | 29–31 | Polls the inbox because RCS can bypass `SMS_RECEIVED` on Samsung. |
| `SmsContentProviderPoller.kt` | 262 | TODO: extract shared phone-match logic. |
| `MessageReadToolAdapter.kt` | 117–125 | MMS `date` may be seconds or milliseconds on Samsung / Google Messages. |
| `MessageReadToolAdapter.kt` | 217–234 | Samsung `spam_report` versus stock `blocked` column. |
| `MessageReadToolAdapter.kt` | 394–395 | Comment that the Samsung provider ignores `ORDER BY`. |
| `SmsWarmDataProvider.kt` | 190, 255 | OEM spam columns and date units. |
| `ListeningService.kt` | 92–94 | API 34+ rejects a microphone foreground type without `RECORD_AUDIO`; short service is used to satisfy `startForeground` and then stop. |
| `ZolaFcmService.kt` | 52–53 | `SESSION_INVALIDATED` is log-only; teardown is commented as deferred. |

No `FIXME`, `HACK`, or `Doze` comments in `proactive/sms` or `notification`.
