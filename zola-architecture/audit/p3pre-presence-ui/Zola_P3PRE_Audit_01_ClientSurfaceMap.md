# P3PRE Audit 01 — Client Surface Map

What the current WinUI client shows, and what a full-presence layout has to keep working. Source read: `windows-client/Zola.Client/` at `c05bdfc0301b76b5940b7d019bd0f79fa89beeef`.

Labels are against `Zola_Presence_UI_Architecture.md` §15–§18 (dock, panels, functional integration, authority). K1 does not change those sections.

## 1. Control inventory

Named elements in `MainWindow.xaml`. Unnamed containers (root `Grid`, header `StackPanel`, transcript `Grid`, composer `Grid`) have no `x:Name` and are not rows.

| Name | Type | Shows / does | Handler | IsEnabled / Visibility / Content / Text set | Decision tag |
|---|---|---|---|---|---|
| `ModeButton` | `Button` | Voice/Text toggle. Content is the current mode word. | `Click` → `OnModeClick` (`MainWindow.xaml.cs` 259–300) | XAML `Content="Voice"` `IsEnabled="False"` (`MainWindow.xaml` 28). `ApplyVoiceChrome` sets `Content` to `"Voice"` or `"Text"` and `IsEnabled` (390–391). | `P2-D07` |
| `SessionsButton` | `Button` | Opens or closes the session list. | `Click` → `OnSessionsToggle` (689–714) | XAML `Content="Sessions"` `IsEnabled="False"` (30). `UpdateChrome` sets `IsEnabled` (683). Content never changes in code. | `P1-D04` |
| `StatusText` | `TextBlock` | Readiness, turn, and voice notices. | none | `Render` 73–74; `ConnectAsync` 81, 102; `OnSessionReady` 127, 133; `OnSendClick` path via `SubmitTurnAsync` 169, 192; `SyncVoiceAsync` 214; `ToggleVoiceCaptureAsync` 253; `OnModeClick` 288; `OnVoiceChatEnded` 305; `OnVoiceStatusMessage` 312; `OnSubmitAcknowledged` 405–411; `OnCancelClick` 424, 439; `OnInterruptAcknowledged` 449; `OnMessageStarted` 481; `FinishTurn` 540, 558; `ShowUnreachable` 586–588; `OnNewSessionClick` 742, 755; `OnSessionItemClick` 786, 805, 819. | `P1-D01`, `P2-D08` |
| `DetailText` | `TextBlock` | Session ids, routed notes, unreachable explanation, list errors. | none | `Render` 74; `OnSessionReady` 115; `OnRouted` 572; `ShowUnreachable` 589; `OnSessionsToggle` catch 710. Initial `DetailText` is the profile path from `HermesProcessManager` until the socket owns status. | `P1-D01` |
| `VoiceStateText` | `TextBlock` | Voice-state label. | none | XAML `Text="Idle"` (35). Only `ApplyVoiceChrome` 321–349. | `P2-D08` |
| `MicIndicatorText` | `TextBlock` | Honest mic line. | none | XAML `Text="Mic: off"` (37). Only `ApplyVoiceChrome` 353–387. | `P2-D08` |
| `TranscriptScroll` | `ScrollViewer` | Scrolls the transcript. | none | `ScrollToEnd` 895–896 (`UpdateLayout`, `ChangeView`). | `P1-D01` |
| `Transcript` | `StackPanel` | Bubble host. | none | `AddLiveBubble` 650; `AddBubble` 662; `ClearTranscript` 886. | `P1-D01` |
| `SessionPanel` | `Border` | Sessions column, 300px. | none | XAML `Visibility="Collapsed"` (49). `OnSessionsToggle` 699 `Visible`; `HideSessions` 726 `Collapsed`. | `P1-D04` |
| `EmptySessionsText` | `TextBlock` | Empty-list copy. | none | XAML text (58). `BindSessions` 879 toggles `Visibility`. | `P1-D04` |
| `SessionList` | `ListView` | Stored id + last-activity. | `ItemClick` → `OnSessionItemClick` (768–830) | `BindSessions` 877 `ItemsSource`, 880 `Visibility`. Item template binds `Id`, `LastActiveText` (63–64). | `P1-D04` |
| `NewSessionButton` | `Button` | Fresh socket + `session.create`. | `Click` → `OnNewSessionClick` (730–766) | XAML `Content="New session"` `IsEnabled="False"` (72). `UpdateChrome` 684 sets `IsEnabled`. | `P1-D04` |
| `CloseSessionsButton` | `Button` | Hides the panel. | `Click` → `OnCloseSessionsClick` (716–719) | Content stays `"Close"`. Never disabled in code. | `P1-D04` |
| `Composer` | `TextBox` | Typed input. | `TextChanged` → `UpdateChrome` (57); `PreviewKeyDown` → `OnComposerKeyDown` (58, 593–609) | XAML `IsEnabled="False"` placeholder `"Waiting for the session…"` (86–93). `UpdateChrome` 678 `IsEnabled`. Placeholder set in `OnSessionReady` 134 and resume success 806 to `"Message"`. Text cleared in `OnSendClick` 149. | `P1-D01`, `P2-D07` |
| `MicButton` | `Button` | Starts or stops `voice.record`. | `Click` → `OnMicClick` (220–223) | XAML `Content="Mic"` `IsEnabled="False"` (95). `ApplyVoiceChrome` 392–393: `IsEnabled = CanStartCapture`, `Content` `"Listening"` or `"Mic"`. | `P2-D04`, `P2-D12` |
| `SendButton` | `Button` | Typed submit. | `Click` → `OnSendClick` (138–151) | XAML `Content="Send"` `IsEnabled="False"` (96). `UpdateChrome` 679. | `P1-D01`, `P2-D05` |
| `CancelButton` | `Button` | `session.interrupt`. | `Click` → `OnCancelClick` (416–443) | XAML `Content="Cancel"` `IsEnabled="False"` (97). `UpdateChrome` 680. `OnCancelClick` 425 sets `IsEnabled = false` immediately. | `P1-D01` |

Root `Grid` (`MainWindow.xaml` 9–12) owns `KeyboardAccelerator` Key=`Space` Modifiers=`Control` → `OnVoiceHotkey` (226–231). `P2-D04`.

Theme key on a named element: `SessionPanel.BorderBrush` = `{ThemeResource DividerStrokeColorDefaultBrush}` (49). Header title uses `{StaticResource TitleTextBlockStyle}` (26). Sessions heading uses `{StaticResource SubtitleTextBlockStyle}` (56).

**§15–§18.** This is a permanent text bar plus a header. §15 says the dock replaces the permanent text input and stays hidden in ambient presence. §16 says panels orbit the presence. [GAP] `P3PRE-AUD-02`.

## 2. Behavior inventory

Smoke sources: `P1-CLIENT_Progress.md` Phase 5; `P1-SESSION_Progress.md` Phase 4; `P2-VOICE_Progress.md` (bubble fix, Cancel, resume); `P2-SPEAK_Progress.md` (barge-in, follow-up, loop guard); `P2-WAKE_Progress.md` and `P2-LORE_Progress.md` combined smoke (cold launch, barge-in, follow-up, timeout-then-wake, Text mode, Resume, relaunch, distance).

| Behavior | Methods | XAML it depends on |
|---|---|---|
| Typed submit | `OnSendClick` 138–151 → `SubmitTurnAsync` 153–196 → `ChatSocket.SubmitAsync` (`prompt.submit`). Guard: `!_sessionReady \|\| _streaming \|\| _unreachable \|\| empty` (141). | `Composer`, `SendButton`, `Transcript` (`AddBubble` 163) |
| Spoken submit (same path) | `VoiceController.TranscriptReady` → `SubmitTurnAsync` (45). No composer clear. Running-turn submit still adds a You bubble and does not clear `_streaming` (162–170). | `Transcript` |
| Cancel → `session.interrupt` | `OnCancelClick` 416–443 → `ChatSocket.InterruptAsync`. Ack `OnInterruptAcknowledged` 445–456 → `FinishTurn("interrupted")`. | `CancelButton`, `StatusText`, live bubble in `Transcript` |
| Typed Send blocked while streaming | `OnSendClick` 141 returns when `_streaming`. `UpdateChrome` 677–679 disables `Composer` and `SendButton`. | `Composer`, `SendButton` |
| Sessions list | `OnSessionsToggle` 689–714 → `SessionCatalog.ListAsync` (`GET /api/sessions`). `BindSessions` 873–881. | `SessionsButton`, `SessionPanel`, `SessionList`, `EmptySessionsText` |
| Resume | `OnSessionItemClick` 768–830 → `SessionCatalog.MessagesAsync` then `ChatSocket.ResumeStoredAsync` (`session.resume`). Paints bubbles, then `HideSessions`. | `SessionList`, `Transcript`, `Composer` |
| New session | `OnNewSessionClick` 730–766 → `ChatSocket.BeginNewSessionAsync` (`session.create` on a new socket). | `NewSessionButton`, `Transcript`, `StatusText` |
| Unreachable disables composer and mic | `ShowUnreachable` 575–591 sets `_unreachable`, `_sessionReady = false`. `UpdateChrome` 677–684. `ApplyVoiceChrome` 391–392 disables mode and mic (`CanStartCapture` needs `BackendReachable`). | `Composer`, `SendButton`, `CancelButton`, `MicButton`, `ModeButton`, `SessionsButton`, `StatusText`, `DetailText` |
| Voice/Text toggle | `OnModeClick` 259–300 → `EnterTextModeAsync` or `EnterVoiceModeAsync`. Launch mode is `VoiceController.Mode` default `ModeVoice` (`VoiceController.cs` 146). Composer stays enabled in both modes (`UpdateChrome` does not read `Mode`). | `ModeButton`, `Composer` |
| `Ctrl+Space` | Root `Grid` accelerator → `OnVoiceHotkey` 226–231 → `ToggleVoiceCaptureAsync` 233–257. No-op unless `CanStartCapture` (236–238). | Root `Grid`, `MicButton` (same action) |
| Mic enable rule | `VoiceController.CanStartCapture` 197–203: Voice mode, `IsAvailable`, `SessionReady`, `BackendReachable`, not `TurnRunning`, not `Speaking`. Window copies facts in `SetCaptureGate` (319) before the button read (392). | `MicButton` |
| Voice-state line | `ApplyVoiceChrome` 316–350. Priority in §3. | `VoiceStateText` |
| Mic-indicator line | `ApplyVoiceChrome` 352–388. | `MicIndicatorText` |
| Status / detail lines | `StatusText` / `DetailText` writers in §1. `P2-D13` notice is `VoiceController.NoticeVoicePaused` (38–39), raised from `OnVoiceInterrupted` (746) as `StatusMessage` → `OnVoiceStatusMessage` (309–313) onto `StatusText`. | `StatusText`, `DetailText` |
| Transcript bubbles and auto-scroll | `AddBubble` 654–672 (user, right, max width 720). `AddLiveBubble` 633–652 (assistant). `OnMessageStarted` 458–484 opens or clears the live bubble. `OnMessageDelta` 486–499 appends. `FinishTurn` 512–560 styles error/interrupted badges. `ScrollToEnd` 893–897 after add, delta, and style. `ClearTranscript` 883–891 on new/resume. | `Transcript`, `TranscriptScroll` |

**§17–§18.** These behaviors present authoritative socket and controller state and route actions through `VoiceController` / `ChatSocket`. They do not classify intent. [MATCH] `P3PRE-AUD-03` for the action path. The labels themselves are derived in the window; see §3.

## 3. State sources (K4)

`ApplyVoiceChrome` (`MainWindow.xaml.cs` 316–394), quoted in full:

```316:394:windows-client/Zola.Client/MainWindow.xaml.cs
    private void ApplyVoiceChrome()
    {
        // P2-VOICE: the window copies session and turn facts into the controller, which owns the mic rule — P2-D12
        _voice.SetCaptureGate(_sessionReady, _backend.WebSocketPermitted && !_unreachable, _streaming);
        var unavailable = !_voice.IsAvailable && _voice.Mode == VoiceController.ModeText;
        if (unavailable)
        {
            var details = _voice.UnavailableDetails;
            VoiceStateText.Text = details.Length == 0 ? "Voice unavailable" : "Voice unavailable — " + details;
        }
        else if (_voice.Mode == VoiceController.ModeText)
        {
            VoiceStateText.Text = "Text mode";
        }
        else if (_streaming)
        {
            VoiceStateText.Text = "Thinking";
        }
        else if (_voice.Speaking)
        {
            // P2-SPEAK: Speaking is the simulated-clock estimate, not measured playback — P2-D08
            VoiceStateText.Text = "Speaking";
        }
        else if (_voice.RecorderState == VoiceController.StateTranscribing)
        {
            VoiceStateText.Text = "Transcribing";
        }
        else if (_voice.CaptureActive || _voice.RecorderState == VoiceController.StateListening)
        {
            VoiceStateText.Text = "Listening";
        }
        else
        {
            VoiceStateText.Text = "Idle";
        }

        // P2-VOICE: recording, barge-in, and off are a separate line from the voice state — P2-D08
        if (_voice.Mode != VoiceController.ModeVoice || !_voice.IsAvailable)
        {
            MicIndicatorText.Text = "Mic: off";
        }
        else if (_voice.CaptureActive)
        {
            MicIndicatorText.Text = "Mic: recording";
        }
        else if (_streaming || _voice.Speaking)
        {
            // P2-SPEAK: barge-in keeps the mic while a turn runs or the speaking estimate is still open — P2-D12
            MicIndicatorText.Text = "Mic: listening for interruptions";
        }
        else if (_switchInFlight || _historyPending)
        {
            // P2-WAKE: session replace is the reconnect window; the old socket already disarmed — P2-D08
            MicIndicatorText.Text = "Reconnecting voice…";
        }
        else if (_voice.WakeUnavailable || _voice.WakeHeldElsewhere)
        {
            // P2-WAKE: push-to-talk stays enabled when the detector is unavailable or held — P2-D08
            MicIndicatorText.Text = "Wake word unavailable";
        }
        else if (_voice.Resting && _voice.WakeArmed && _voice.WakePaused)
        {
            MicIndicatorText.Text = "Wake listening paused";
        }
        else if (_voice.Resting && _voice.WakeArmed && !_voice.WakePaused)
        {
            // P2-WAKE: confirmed listening is the Resting indicator — P2-D08
            MicIndicatorText.Text = "Mic: listening for \"Hey Zola\"";
        }
        else
        {
            MicIndicatorText.Text = "Mic: off";
        }

        ModeButton.Content = _voice.Mode == VoiceController.ModeVoice ? "Voice" : "Text";
        ModeButton.IsEnabled = !_unreachable && !_modeSwitching && !string.IsNullOrEmpty(_chat.SessionId);
        MicButton.IsEnabled = _voice.CanStartCapture;
        MicButton.Content = _voice.CaptureActive ? "Listening" : "Mic";
    }
```

### Voice-state label priority

First match wins.

| Order | Label | Condition | Fact owner | Where the fact is set |
|---|---|---|---|---|
| 1 | `Voice unavailable` or `Voice unavailable — {details}` | `!IsAvailable && Mode == text` | `VoiceController.IsAvailable`, `Mode`, `UnavailableDetails` | `MarkUnavailable` (`VoiceController.cs` 1561+) from a failed `voice.toggle` probe in `SyncVoiceModeAsync` (241–251, 260–261, 269). Sets `Mode = ModeText`. |
| 2 | `Text mode` | `Mode == text` (and available, so a user toggle) | `VoiceController.Mode` | Default `ModeVoice` (146). `EnterTextModeAsync` 314. `EnterVoiceModeAsync` 327. Loop guard calls `EnterTextModeAsync` (747). |
| 3 | `Thinking` | window `_streaming` | `MainWindow._streaming` | Set true: `SubmitTurnAsync` 167, `OnSubmitAcknowledged` 404, `OnMessageStarted` 478. Set false: `FinishTurn` 529/551, `ShowUnreachable` 584, `ClearTranscript` 888, failed submit 188. |
| 4 | `Speaking` | `VoiceController.Speaking` | controller | `SetSpeaking` 807–815 from `OnTurnStarted` 385, `OnFollowUpTimerAsync` 758, `CancelFollowUp` 788. Clock eligibility: `Mode == voice && _ttsOn == true` (469). |
| 5 | `Transcribing` | `RecorderState == "transcribing"` | controller | `OnVoiceStatus` 619–622 from `voice.status`. |
| 6 | `Listening` | `CaptureActive` or `RecorderState == "listening"` | controller | `StartCaptureAsync` 532–537; `OnVoiceStatus` 637–639. Cleared on idle (623–625). |
| 7 | `Idle` | else | — | Includes wake-armed resting. Wake is not on this line. |

`_switchInFlight` and `_historyPending` do not change `VoiceStateText`. They change the mic line and they clear `_sessionReady`, which `SetCaptureGate` copies into `VoiceController.SessionReady`, which makes `Resting` false.

### Mic-indicator priority

| Order | Label | Condition | Owner |
|---|---|---|---|
| 1 | `Mic: off` | mode is not voice, or `!IsAvailable` | controller |
| 2 | `Mic: recording` | `CaptureActive` | controller |
| 3 | `Mic: listening for interruptions` | `_streaming` or `Speaking` | window field or controller |
| 4 | `Reconnecting voice…` | `_switchInFlight` or `_historyPending` | window fields, set in `OnNewSessionClick` 738–740 and `OnSessionItemClick` 783–784, cleared in the `finally` blocks |
| 5 | `Wake word unavailable` | `WakeUnavailable` or `WakeHeldElsewhere` | controller, from wake RPC replies (`ApplyWakeStatus`-style block 1426–1429) |
| 6 | `Wake listening paused` | `Resting && WakeArmed && WakePaused` | controller. `Resting` getter 180–194. |
| 7 | `Mic: listening for "Hey Zola"` | `Resting && WakeArmed && !WakePaused` | controller |
| 8 | `Mic: off` | else | — |

### Other derivations of "what state Zola is in"

`P2-D12` gives `VoiceController` sole ownership of which listener is active, of `voice.record` / `wake.*`, and of transcript-to-submit. That part holds: those calls are in `VoiceController.cs` (`ToggleAsync`, `RecordAsync`, `ArmWakeAsync` / `DisarmWakeAsync`, `OnVoiceTranscript` → `TranscriptReady`).

The **label** is a second derivation, in `MainWindow.ApplyVoiceChrome`, not in the controller. Three more surfaces say state in their own words:

- `StatusText`: `"Session ready."`, `"Responding…"`, `"Sending…"`, `"Interrupted."`, `"Voice chat ended"`, `"Voice interrupted."`, `"Cancelling…"`, the `P2-D13` lid notice, Hermes `status.update` text via `OnRouted`.
- `MicButton.Content`: `"Listening"` vs `"Mic"` from `CaptureActive` only (393), which is narrower than the mic line.
- `ModeButton.Content`: `"Voice"` / `"Text"` from `Mode` only (390).

`VoiceController.Resting` (180–194) is a third boolean combination of the same facts, used to accept or ignore `wake.detected` (`HandleWakeDetectedAsync` 1459–1463). It is not what `VoiceStateText` prints. Idle on the label is not the same predicate as `Resting`.

[RISK] `P3PRE-AUD-04`. §4 wants one `PresenceStateAdapter`. §18 forbids a second authority. A presence mapper that re-reads the same facts would duplicate `ApplyVoiceChrome`.

## 4. Change notification

| Source | Raised on | How the window marshals |
|---|---|---|
| `VoiceController.StateChanged` | Caller thread. Socket events arrive on `ChatSocket.ReadLoopAsync` (386–427, `ConfigureAwait(false)`). `System.Threading.Timer` follow-up (`OnFollowUpTimerAsync` 755) is thread-pool. `SetCaptureGate` (214–225) runs on the UI thread because `ApplyVoiceChrome` calls it, then `StateChanged` is queued again. | Constructor: `_voice.StateChanged += () => Dispatch(ApplyVoiceChrome)` (44). `Dispatch` 899–903 uses `DispatcherQueue.TryEnqueue`. |
| `TranscriptReady`, `VoiceChatEnded`, `StatusMessage` | Same controller threads. | Each wrapped in `Dispatch` (45–47). |
| `ChatSocket` events (`SessionReady`, `SubmitAcknowledged`, `MessageStarted`, `MessageDelta`, `MessageCompleted`, `InterruptAcknowledged`, `Routed`, `Unreachable`) | `ReadLoopAsync` thread, or the RPC waiter after `ConfigureAwait(false)`. | Each handler wrapped in `Dispatch` (48–55). |
| `HermesProcessManager.StateChanged` | `Publish` (466), after health/attach work that uses `ConfigureAwait(false)`. | `DispatcherQueue.TryEnqueue(Render)` (56). `Render` does not call `UpdateChrome`. |
| Composer `TextChanged` | UI thread. | `UpdateChrome` directly (57). |
| Window fields (`_streaming`, `_unreachable`, `_switchInFlight`, `_historyPending`, `_modeSwitching`, `_sessionReady`) | Set on the UI thread inside `Dispatch` callbacks, then `UpdateChrome` → `ApplyVoiceChrome`. | Already on the UI thread. |

`OnMessageDelta` (486–499) updates the bubble and `OnTurnDelta` but does not call `UpdateChrome`. The speaking flag does not flip on a delta, so the labels stay put. Bubble text still changes. That is a render of the transcript, not of chrome.

`Render` (68–84) can set `StatusText` / `DetailText` only while `!_socketOwnsStatus`. After the socket connects, backend `StateChanged` does not refresh voice chrome. A later health failure is a `ChatSocket.Unreachable` event (`WatchHealthAsync` 444+), which does `ShowUnreachable` → `UpdateChrome`.

No path was found that flips `_streaming`, `Speaking`, `CaptureActive`, `Mode`, or wake flags without a subsequent `UpdateChrome` or `StateChanged`. `ClearTranscript` (883–891) clears `_streaming` and relies on its callers (`OnNewSessionClick` 743, resume success 805) to call `UpdateChrome`.

## 5. Coupling to layout

Code-behind names that break if the element moves only when the name is deleted. Moving the same named element into an overlay or dock does not break these references. Collapsing or removing it does.

| Member | Lines | What a layout move would hit |
|---|---|---|
| `Transcript.Children` | 650, 662, 886 | Overlay must still be the bubble host. |
| `TranscriptScroll` | 895–896 | Auto-scroll assumes this viewer wraps `Transcript`. |
| `SessionPanel.Visibility` | 699, 726 | Overlay/collapse is already how it works. Width is fixed at 300 in XAML (49), not in code. |
| `Composer` | 57–58, 134, 149, 678, 727, 806 | Focus return (`HideSessions` 727), Enter key, enable, placeholder. A dock-expanded composer keeps the name and these still work. |
| `StatusText`, `DetailText`, `VoiceStateText`, `MicIndicatorText` | see §1 | Any HUD that removes the `TextBlock` breaks the assignment. |
| `ModeButton`, `MicButton`, `SendButton`, `CancelButton`, `SessionsButton`, `NewSessionButton` | see §1 | Enable/content writes. |
| `SessionList`, `EmptySessionsText` | 877–880 | List binding. |
| `AddBubble` / `AddLiveBubble` | 633–672 | Builds `Border`/`TextBlock` in code with `MaxWidth = 720` and alignment. Not XAML names, but layout constants. |

[RISK] `P3PRE-AUD-05`. §16 wants the transcript as a temporary panel. The bubble factory and `ScrollToEnd` are hard-wired to `Transcript` / `TranscriptScroll`. The behavior can move with those names; the chrome writes cannot move onto different controls without edits.

## 6. Accelerator and focus

`Ctrl+Space` is a `KeyboardAccelerator` on the root `Grid` (`MainWindow.xaml` 10–12), not on `Window`. `P2-VOICE_Progress.md` records that this WinUI build has no `Window.KeyboardAccelerators` collection.

`OnComposerKeyDown` (593–609) handles Enter only. It does not mark Space handled.

**UNVERIFIED (no code change in this audit's client):** whether the accelerator still runs when focus is inside `Composer`. WinUI raises `KeyboardAccelerator.Invoked` by walking from the focused element toward the root. The `TextBox` is a descendant of that `Grid`, so the accelerator is in scope. A `TextBox` does not consume Ctrl+Space as text in the en-US layout (`PreviewKeyDown` ignores it here). Phase 4 puts the same accelerator on the spike and records the observed result.

**UNVERIFIED:** a full-window `SwapChainPanel` (Helix `Viewport3DX`'s usual host) is a XAML element, not a separate HWND, so key routing stays in the XAML tree if the panel does not host a child window. If the panel is focusable and sits under the same root `Grid`, the ancestor walk should still find the accelerator. If Helix uses a child HWND, or if the panel marks the key handled before the walk, the hotkey stops while the 3D surface has focus. `S18` already defers a global hotkey; this question is in-window only. Phase 4 measures it.

## 7. Window and resources

| Item | Evidence |
|---|---|
| Initial size | `AppWindow.Resize(960, 720)` (`MainWindow.xaml.cs` 39). No minimum size, no `AppWindow.Changed` handler. |
| Title | `Title="Zola"` (`MainWindow.xaml` 7). Default title bar. `ExtendsContentIntoTitleBar` is not set. |
| Theme | `App.xaml` 7–12 merges `XamlControlsResources` only. No `RequestedTheme`. The window follows the Windows theme. |
| ThemeResource keys | `DividerStrokeColorDefaultBrush` (XAML 49). Code fallbacks in `BubbleBrush` 905–924: `SystemFillColorCriticalBackgroundBrush`, `SystemFillColorCautionBackgroundBrush`, `AccentFillColorDefaultBrush`, `CardBackgroundFillColorDefaultBrush`. |
| Static styles | `TitleTextBlockStyle`, `SubtitleTextBlockStyle`. |
| Custom fonts / colours | None. Bubbles use theme brushes plus hardcoded fallback `Color` values (910, 915, 920, 923). Inline `FontWeight` SemiBold on bubble headings (636, 657). |
| Project | `Zola.Client.csproj`: `net9.0-windows10.0.19041.0`, `TargetPlatformMinVersion` 10.0.17763.0, `Platforms` x64, `RuntimeIdentifiers` win-x64, `UseWinUI` true, `WindowsPackageType` None, `EnableMsixTooling` false, `WinUISDKReferences` false. Packages: `Microsoft.WindowsAppSDK` 2.5.1, `Microsoft.Windows.SDK.BuildTools` 10.0.26100.4654, `System.Management` 9.0.4. |

**§20 Desktop Mode** asks for a sidebar or ambient panel and larger HUD surfaces. The client is one 960×720 window with a chat column. [GAP] `P3PRE-AUD-06`.

## Findings in this document

| ID | Severity | Label | Summary |
|---|---|---|---|
| P3PRE-AUD-02 | MEDIUM | [GAP] | The live UI is a permanent composer bar and header, not a contextual dock and orbiting panels (§15, §16). |
| P3PRE-AUD-03 | — | [MATCH] | Typed and spoken submits share `SubmitTurnAsync`. Cancel, unreachable, Voice/Text, mic gate, and session list/resume match the Phase 1/2 smoke behaviors and §17–§18 action routing. |
| P3PRE-AUD-04 | HIGH | [RISK] | `ApplyVoiceChrome` (`MainWindow.xaml.cs` 316–394) is the only voice-state and mic-label derivation. `VoiceController` owns RPCs and `Resting`, not those labels. A second `PresenceMode` map would split authority (§4, §18, `P2-D12`). |
| P3PRE-AUD-05 | MEDIUM | [RISK] | Bubble creation, scroll, and chrome writes name `Transcript`, `TranscriptScroll`, `Composer`, and the status `TextBlock`s directly. |
| P3PRE-AUD-06 | LOW | [GAP] | Window is 960×720, theme-following, no custom font or obsidian palette (§20 desktop, K7). |
