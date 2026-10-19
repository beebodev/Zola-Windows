using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using Zola.Client.Speech;

internal sealed partial class CheckRunner
{
    private void RunSpeechRows()
    {
        foreach (var (reason, arm) in Gates())
        {
            Speech("gate " + reason, () =>
            {
                var coordinator = new ProactiveDeliveryCoordinator();
                var facts = Ready();
                arm(facts);
                var action = coordinator.Poll(facts);
                return action.Step == SpeechStep.Stop
                    && action.Reason == reason
                    && action.Step != SpeechStep.Claim;
            });
        }

        Speech("snapshot turn does not claim", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            var polled = coordinator.Poll(facts);
            var action = coordinator.AfterSnapshot(facts, new SpeechSnapshot(true, null, true, false, facts.UtcNow));
            return polled.Step == SpeechStep.Snapshot
                && action.Step == SpeechStep.Stop
                && action.Reason == SpeechConstants.ReasonTurn;
        });

        Speech("reviewed draft does not claim", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            var action = coordinator.AfterSnapshot(facts, new SpeechSnapshot(true, null, false, true, facts.UtcNow));
            return action.Step == SpeechStep.Stop && action.Reason == SpeechConstants.ReasonReviewedDraft;
        });

        Speech("final check releases before tts", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            var polled = coordinator.Poll(facts);
            var after = coordinator.AfterSnapshot(facts, Fresh(facts));
            facts.Turn = true;
            var claimed = coordinator.AfterClaim(facts, GoodClaim());
            return polled.Step == SpeechStep.Snapshot
                && after.Step == SpeechStep.Claim
                && claimed.Step == SpeechStep.Release
                && claimed.Reason == SpeechConstants.ReasonTurn
                && coordinator.Poll(facts).Step != SpeechStep.Claim;
        });

        Speech("one at a time", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            coordinator.Poll(facts);
            coordinator.AfterSnapshot(facts, Fresh(facts));
            var started = coordinator.AfterClaim(facts, GoodClaim());
            var spoken = coordinator.AfterSpeechStarted(facts, new SpeechStoreReply(true, null));
            coordinator.AfterSpeak(facts, accepted: true);
            var again = coordinator.Poll(facts);
            return started.Step == SpeechStep.SpeechStarted
                && spoken.Step == SpeechStep.Speak
                && again.Reason == SpeechConstants.ReasonOneAtATime
                && again.Step != SpeechStep.Claim;
        });

        Speech("quiet hours", () =>
        {
            var night = Ready();
            night.LocalNow = new DateTimeOffset(2026, 10, 16, 22, 0, 0, TimeSpan.Zero);
            var morning = Ready();
            morning.LocalNow = new DateTimeOffset(2026, 10, 16, 6, 59, 0, TimeSpan.Zero);
            var day = Ready();
            day.LocalNow = new DateTimeOffset(2026, 10, 16, 7, 0, 0, TimeSpan.Zero);
            var nightGate = new ProactiveDeliveryCoordinator().Poll(night);
            var morningGate = new ProactiveDeliveryCoordinator().Poll(morning);
            var dayGate = new ProactiveDeliveryCoordinator().Poll(day);
            return nightGate.Reason == SpeechConstants.ReasonQuietHours
                && morningGate.Reason == SpeechConstants.ReasonQuietHours
                && dayGate.Step == SpeechStep.Snapshot;
        });

        Speech("stale snapshot and timeout", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            var stale = coordinator.AfterSnapshot(facts, new SpeechSnapshot(true, null, false, false, facts.UtcNow.AddSeconds(-5)));
            var timed = coordinator.AfterSnapshot(facts, new SpeechSnapshot(false, SpeechConstants.ReasonSnapshotTimeout, false, false, null));
            return stale.Reason == SpeechConstants.ReasonSnapshotStale
                && stale.Step == SpeechStep.Stop
                && timed.Reason == SpeechConstants.ReasonSnapshotTimeout
                && timed.Step != SpeechStep.Claim;
        });

        Speech("deny log changes once then idle once", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            facts.Locked = true;
            coordinator.Poll(facts);
            coordinator.Poll(facts);
            facts.Locked = false;
            coordinator.Poll(facts);
            coordinator.AfterSnapshot(facts, Fresh(facts));
            coordinator.AfterClaim(facts, new SpeechClaimResult(false, SpeechConstants.ReasonNothingSpeakable, null, null, null, null, null));
            coordinator.AfterClaim(facts, new SpeechClaimResult(false, SpeechConstants.ReasonNothingSpeakable, null, null, null, null, null));
            var text = string.Join("\n", coordinator.Log.Lines);
            return text.Split("reason=locked").Length - 1 == 1
                && text.Split("outcome=idle").Length - 1 == 1;
        });

        Speech("pending outcome retries after backoff", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            DriveToAccepted(coordinator, facts);
            facts.UtcNow = facts.UtcNow.AddSeconds(SpeechConstants.StartTimeoutSeconds + 1);
            var first = coordinator.Poll(facts);
            coordinator.AfterStore(facts, new SpeechStoreReply(false, SpeechConstants.ReasonBackendDown));
            var early = coordinator.Poll(facts);
            facts.UtcNow = facts.UtcNow.AddSeconds(SpeechConstants.OutcomeRetrySeconds);
            var retry = coordinator.Poll(facts);
            return first.Step == SpeechStep.Outcome
                && first.StoreOutcome == SpeechConstants.OutcomeUncertain
                && early.Step == SpeechStep.Stop
                && retry.Step == SpeechStep.Outcome
                && retry.Step != SpeechStep.Claim;
        });

        Speech("each stamp clears a reservation", () =>
        {
            foreach (var stamp in new[]
            {
                SpeechConstants.StampComposer,
                SpeechConstants.StampWake,
                SpeechConstants.StampPushToTalk,
                SpeechConstants.StampSubmit,
                SpeechConstants.StampTurn,
            })
            {
                var coordinator = new ProactiveDeliveryCoordinator();
                var facts = Ready();
                DriveToAccepted(coordinator, facts);
                var cleared = coordinator.NoteStamp(stamp, facts);
                var next = coordinator.Poll(facts);
                if (cleared.Step != SpeechStep.Outcome
                    || cleared.StoreOutcome != SpeechConstants.OutcomeUncertain
                    || cleared.Reason != SpeechConstants.CancelledBy(stamp)
                    || next.Step == SpeechStep.Claim
                    || next.Step == SpeechStep.Speak)
                {
                    return false;
                }
            }

            return true;
        });

        Speech("echo haystack and playback guard", () =>
        {
            var echo = new SpeechEchoGuard();
            var now = DateTimeOffset.Parse("2026-10-16T19:00:00Z");
            const string phrase = "Heads up, you've got the reply you were watching for.";
            echo.Remember(phrase, now);
            var during = !echo.AllowsCapture(pushToTalk: false, now) && echo.TranscriptMatches(phrase, now);
            var push = echo.AllowsCapture(pushToTalk: true, now);
            echo.NoteCompleted(now);
            var tail = !echo.AllowsCapture(pushToTalk: false, now.AddSeconds(1));
            var after = echo.AllowsCapture(pushToTalk: false, now.AddSeconds(SpeechConstants.EchoTailSeconds));
            var dropped = !echo.TranscriptMatches(phrase, now.AddSeconds(SpeechConstants.EchoTailSeconds));
            return during && push && tail && after && dropped;
        });

        Speech("phrase sets do not repeat or say someone", () =>
        {
            var cursor = new PhraseCursor();
            var first = SpeechPhrases.Pick("gmail", "Quinn", "brian_message", cursor);
            var second = SpeechPhrases.Pick("gmail", "Quinn", "brian_message", cursor);
            var unnamed = SpeechPhrases.Pick("gmail", "", "someone", cursor);
            var calendar = SpeechPhrases.Pick("calendar", "Quinn", "brian_message", cursor);
            return first != second
                && first.Contains("Quinn", StringComparison.Ordinal)
                && !unnamed.Contains("someone", StringComparison.OrdinalIgnoreCase)
                && !unnamed.Contains("{name}", StringComparison.Ordinal)
                && !calendar.Contains("Quinn", StringComparison.Ordinal)
                && !calendar.Contains("{name}", StringComparison.Ordinal);
        });

        Speech("hud fixture", () =>
        {
            var path = Path.GetFullPath(Path.Combine(
                AppContext.BaseDirectory,
                "..", "..", "..", "..", "..",
                "hermes-plugins", "zola_workspace", "contracts", "watcher_health.json"));
            if (!File.Exists(path))
            {
                return false;
            }

            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var now = DateTimeOffset.Parse("2026-10-16T12:00:00Z");
            foreach (var item in doc.RootElement.GetProperty("cases").EnumerateArray())
            {
                var latch = item.GetProperty("hud_process").GetString() switch
                {
                    "stopped" => WatcherProcessLatch.Stopped,
                    "restarting" => WatcherProcessLatch.Restarting,
                    _ => WatcherProcessLatch.Running,
                };
                WatcherHealthRow? row = null;
                var raw = item.GetProperty("row");
                if (raw.ValueKind == JsonValueKind.Object)
                {
                    row = new WatcherHealthRow
                    {
                        NeedsReconnect = raw.TryGetProperty("needs_reconnect", out var reconnect) ? reconnect.GetInt32() : 0,
                        GmailOkAt = raw.TryGetProperty("gmail_ok_at", out var gmail) ? gmail.GetString() : null,
                        CalendarOkAt = raw.TryGetProperty("calendar_ok_at", out var calendar) ? calendar.GetString() : null,
                        GmailError = raw.TryGetProperty("gmail_error", out var gmailError) ? gmailError.GetString() : null,
                        CalendarError = raw.TryGetProperty("calendar_error", out var calendarError) ? calendarError.GetString() : null,
                        ErrorClass = raw.TryGetProperty("error_class", out var errorClass) ? errorClass.GetString() : null,
                    };
                }

                var result = WatcherHud.Classify(row, latch, now);
                if (result.Spoken != item.GetProperty("spoken").GetString()
                    || result.HudLine != item.GetProperty("hud_line").GetString())
                {
                    return false;
                }
            }

            var restarting = WatcherHud.Classify(null, WatcherProcessLatch.Restarting, now);
            return restarting.Spoken == SpeechConstants.SpokenUnknown
                && restarting.HudLine == SpeechConstants.HudWatcherRestarting
                && restarting.DisplayLine == SpeechConstants.HudWatcherRestarting;
        });

        Speech("reservation clear stays under the lock bound", () =>
        {
            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            var watch = Stopwatch.StartNew();
            for (var i = 0; i < 1000; i++)
            {
                coordinator.NoteStamp(SpeechConstants.StampComposer, facts);
            }

            watch.Stop();
            return watch.ElapsedMilliseconds < SpeechConstants.LockHoldMs;
        });

        Speech("proactive method names match the contract", () =>
        {
            var root = Path.GetFullPath(Path.Combine(
                AppContext.BaseDirectory,
                "..", "..", "..", "..", ".."));
            var contractPath = Path.Combine(root, "hermes-plugins", "zola_workspace", "contracts", "proactive_methods.json");
            var gatewayPath = Path.Combine(root, "windows-client", "Zola.Client", "Speech", "ChatSpeechGateway.cs");
            if (!File.Exists(contractPath) || !File.Exists(gatewayPath))
            {
                return false;
            }

            using var doc = JsonDocument.Parse(File.ReadAllText(contractPath));
            var expected = new HashSet<string>();
            foreach (var item in doc.RootElement.GetProperty("methods").EnumerateArray())
            {
                var name = item.GetString();
                if (!string.IsNullOrEmpty(name))
                {
                    expected.Add(name);
                }
            }

            var found = new HashSet<string>();
            foreach (Match match in Regex.Matches(File.ReadAllText(gatewayPath), "proactive\\.[a-z_]+"))
            {
                found.Add(match.Value);
            }

            return expected.SetEquals(found);
        });

        Speech("recover failure still updates the hud and logs once", () =>
            RecoverHudOnce().GetAwaiter().GetResult());
        Speech("push to talk during tts stops and records uncertain", () =>
            PushToTalkDuringTts().GetAwaiter().GetResult());
        Speech("crash after dispatch is not spoken again", () =>
            CrashAfterDispatch().GetAwaiter().GetResult());
        Speech("terminal outcome refusal frees the coordinator", () =>
            TerminalRefusalFrees().GetAwaiter().GetResult());
        Speech("transient outcome refusal retries", () =>
            TransientRefusalRetries().GetAwaiter().GetResult());
        Speech("stamp before speech_started does not dispatch", () =>
            StampBeforeSpeechStarted().GetAwaiter().GetResult());
        Speech("stamp during speech_started does not dispatch", () =>
            StampDuringSpeechStarted().GetAwaiter().GetResult());
        Speech("stamp during playback is never delivered", () =>
            StampDuringPlayback().GetAwaiter().GetResult());
        Speech("a later reply does not restart the echo tail", () =>
            LaterReplyDoesNotRefreshEchoTail().GetAwaiter().GetResult());
        Speech("an accepted proactive line is noted for the conversation", () =>
            AcceptedLineIsNoted().GetAwaiter().GetResult());
        Speech("each drop logs its own reason", () => EachDropLogsItsOwnReason());
        Speech("ranking unavailable is attention", () =>
            SystemsCopy.LevelFor(SystemsCopy.Row.Ranking, SystemsCopy.Unavailable) == SystemsCopy.Level.Attention);
        Speech("voice unavailable is down", () =>
            SystemsCopy.LevelFor(SystemsCopy.Row.Voice, SystemsCopy.Unavailable) == SystemsCopy.Level.Down);
        Speech("stopped watcher is red and the spoken line stays healthy", () =>
        {
            var now = DateTimeOffset.Parse("2026-10-16T12:00:00Z");
            var row = new WatcherHealthRow
            {
                GmailOkAt = "2026-10-16T11:59:00Z",
                CalendarOkAt = "2026-10-16T11:00:00Z",
            };
            var spoken = WatcherHud.Classify(row, WatcherProcessLatch.Stopped, now);
            var view = SystemsCopy.Rows(new SystemsFacts(
                true, false, false, WatcherProcessLatch.Stopped, row, true,
                true, "idle", "2026-10-16T12:00:00Z", now, true, false))[1];
            return spoken.Spoken == SpeechConstants.SpokenHealthy
                && view.State == SystemsCopy.Stopped
                && view.Level == SystemsCopy.Level.Down;
        });
        Speech("reconnect is red on the account row only", () =>
        {
            var now = DateTimeOffset.Parse("2026-10-16T12:00:00Z");
            var row = new WatcherHealthRow
            {
                NeedsReconnect = 1,
                GmailOkAt = "2026-10-16T11:59:00Z",
                CalendarOkAt = "2026-10-16T11:00:00Z",
            };
            var spoken = WatcherHud.Classify(row, WatcherProcessLatch.Running, now);
            var rows = SystemsCopy.Rows(new SystemsFacts(
                true, false, false, WatcherProcessLatch.Running, row, true,
                false, "idle", "2026-10-16T12:00:00Z", now, true, false));
            return spoken.Spoken == SpeechConstants.SpokenNeedsReconnect
                && rows[1].State is null
                && rows[2].State == SystemsCopy.Reconnect
                && rows[2].Level == SystemsCopy.Level.Down;
        });
    }

    private static async Task<bool> RecoverHudOnce()
    {
        var gateway = new FakeSpeechGateway { RecoverFailuresLeft = 1, RecoverReason = "no_store" };
        var logs = new List<string>();
        var hud = 0;
        var session = Session(gateway, Ready(), logs, () => hud++);
        await session.PollAsync();
        var denied = logs.Count(line => line.Contains("reason=no_store", StringComparison.Ordinal));
        var hudAfterDeny = hud;
        await session.PollAsync();
        return hudAfterDeny == 1
            && denied == 1
            && hud == 2
            && logs.Count(line => line.Contains("reason=no_store", StringComparison.Ordinal)) == 1
            && logs.Any(line => line.Contains("outcome=idle", StringComparison.Ordinal));
    }

    private static async Task<bool> PushToTalkDuringTts()
    {
        var hold = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var entered = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var gateway = new FakeSpeechGateway { SpeakHold = hold, OnSpeakEntered = () => entered.TrySetResult(true) };
        var stops = 0;
        var session = Session(gateway, Ready(), new List<string>(), stopPlayback: () => stops++);
        var poll = session.PollAsync();
        var started = await Task.WhenAny(entered.Task, Task.Delay(2000));
        if (started != entered.Task)
        {
            hold.TrySetResult(true);
            await poll;
            return false;
        }

        await session.OnStampAsync(SpeechConstants.StampPushToTalk);
        hold.TrySetResult(true);
        await poll;
        return stops == 1
            && gateway.SpeakCalls == 1
            && gateway.Outcomes.Contains(SpeechConstants.OutcomeUncertain)
            && !gateway.Outcomes.Contains(SpeechConstants.OutcomeDelivered);
    }

    private static async Task<bool> CrashAfterDispatch()
    {
        var store = new FakeSpeechStore();
        var hold = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var entered = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var gateway = new FakeSpeechGateway(store)
        {
            SpeakHold = hold,
            OnSpeakEntered = () => entered.TrySetResult(true),
        };
        var session = Session(gateway, Ready(), new List<string>());
        var poll = session.PollAsync();
        var started = await Task.WhenAny(entered.Task, Task.Delay(2000));
        if (started != entered.Task)
        {
            hold.TrySetResult(true);
            await poll;
            return false;
        }

        store.ExpireOnRecover = true;
        var second = new FakeSpeechGateway(store);
        var next = Session(second, Ready(), new List<string>());
        await next.PollAsync();
        var spokenAgain = second.SpeakCalls != 0 || store.Delivery != "delivery_uncertain";
        hold.TrySetResult(true);
        await poll;
        return !spokenAgain;
    }

    private static async Task<bool> TerminalRefusalFrees()
    {
        var gateway = new FakeSpeechGateway { OutcomeReply = new SpeechStoreReply(false, "illegal_transition") };
        var facts = Ready();
        var session = Session(gateway, facts, new List<string>());
        await session.PollAsync();
        facts.UtcNow = facts.UtcNow.AddSeconds(SpeechConstants.StartTimeoutSeconds + 1);
        await session.PollAsync();
        var outcomes = gateway.OutcomeCalls;
        facts.UtcNow = facts.UtcNow.AddSeconds(SpeechConstants.OutcomeRetrySeconds);
        await session.PollAsync();
        return outcomes == 1
            && gateway.OutcomeCalls == 1
            && gateway.Calls.Contains("snapshot");
    }

    private static async Task<bool> TransientRefusalRetries()
    {
        var gateway = new FakeSpeechGateway { OutcomeReply = new SpeechStoreReply(false, SpeechConstants.ReasonBackendDown) };
        var facts = Ready();
        var session = Session(gateway, facts, new List<string>());
        await session.PollAsync();
        facts.UtcNow = facts.UtcNow.AddSeconds(SpeechConstants.StartTimeoutSeconds + 1);
        await session.PollAsync();
        var afterFirst = gateway.OutcomeCalls;
        await session.PollAsync();
        var duringBackoff = gateway.OutcomeCalls;
        facts.UtcNow = facts.UtcNow.AddSeconds(SpeechConstants.OutcomeRetrySeconds);
        await session.PollAsync();
        return afterFirst == 1
            && duringBackoff == 1
            && gateway.OutcomeCalls == 2
            && gateway.ClaimCalls == 1;
    }

    private static async Task<bool> StampBeforeSpeechStarted()
    {
        var gateway = new FakeSpeechGateway();
        var logs = new List<string>();
        var session = Session(gateway, Ready(), logs);
        session.BeforeSpeechStartedForTests = () => session.OnStampAsync(SpeechConstants.StampPushToTalk);
        await session.PollAsync();
        return gateway.Calls.Contains("release")
            && !gateway.Calls.Contains("speech_started")
            && gateway.SpeakCalls == 0
            && logs.Any(line => line.Contains("reason=" + SpeechConstants.CancelledBy(SpeechConstants.StampPushToTalk), StringComparison.Ordinal));
    }

    private static async Task<bool> StampDuringSpeechStarted()
    {
        var hold = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var entered = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var gateway = new FakeSpeechGateway
        {
            StartHold = hold,
            OnStartEntered = () => entered.TrySetResult(true),
        };
        var logs = new List<string>();
        var session = Session(gateway, Ready(), logs);
        var poll = session.PollAsync();
        var started = await Task.WhenAny(entered.Task, Task.Delay(2000));
        if (started != entered.Task)
        {
            hold.TrySetResult(true);
            await poll;
            return false;
        }

        await session.OnStampAsync(SpeechConstants.StampSubmit);
        hold.TrySetResult(true);
        await poll;
        return gateway.SpeakCalls == 0
            && gateway.Outcomes.Contains(SpeechConstants.OutcomeUncertain)
            && !gateway.Outcomes.Contains(SpeechConstants.OutcomeDelivered)
            && !gateway.Calls.Contains("release")
            && logs.Any(line => line.Contains("reason=" + SpeechConstants.CancelledBy(SpeechConstants.StampSubmit), StringComparison.Ordinal))
            && !logs.Any(line => line.Contains("reason=" + SpeechConstants.ReasonReservationLost, StringComparison.Ordinal));
    }

    private static async Task<bool> StampDuringPlayback()
    {
        var hold = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        var gateway = new FakeSpeechGateway { OutcomeHold = hold };
        var stops = 0;
        var session = Session(gateway, Ready(), new List<string>(), stopPlayback: () => stops++);
        await session.PollAsync();
        await session.NotePlayback(active: true, forced: false);
        var stamp = session.OnStampAsync(SpeechConstants.StampPushToTalk);
        var entered = await Task.WhenAny(gateway.OutcomeEntered.Task, Task.Delay(2000));
        if (entered != gateway.OutcomeEntered.Task)
        {
            hold.TrySetResult(true);
            await stamp;
            return false;
        }

        var end = session.NotePlayback(active: false, forced: false);
        hold.TrySetResult(true);
        await stamp;
        await end;
        return stops >= 1
            && gateway.Outcomes.Contains(SpeechConstants.OutcomeUncertain)
            && !gateway.Outcomes.Contains(SpeechConstants.OutcomeDelivered);
    }

    private static bool EachDropLogsItsOwnReason()
    {
        foreach (var (reason, arm) in Gates())
        {
            if (reason == SpeechConstants.ReasonNotIdle)
            {
                continue;
            }

            var coordinator = new ProactiveDeliveryCoordinator();
            var facts = Ready();
            coordinator.AfterClaim(facts, GoodClaim());
            arm(facts);
            var dropped = coordinator.AfterSpeechStarted(facts, new SpeechStoreReply(true, null));
            if (dropped.Step != SpeechStep.Outcome || dropped.Reason != reason)
            {
                return false;
            }
        }

        var quiet = new ProactiveDeliveryCoordinator();
        var quietFacts = Ready();
        quiet.AfterClaim(quietFacts, GoodClaim());
        quietFacts.LocalNow = new DateTimeOffset(2026, 10, 16, 22, 0, 0, TimeSpan.Zero);
        if (quiet.AfterSpeechStarted(quietFacts, new SpeechStoreReply(true, null)).Reason != SpeechConstants.ReasonQuietHours)
        {
            return false;
        }

        var idle = new ProactiveDeliveryCoordinator();
        var idleFacts = Ready();
        idle.AfterClaim(idleFacts, GoodClaim());
        idleFacts.LastSubmitUtc = idleFacts.UtcNow;
        var idleDrop = idle.AfterSpeechStarted(idleFacts, new SpeechStoreReply(true, null));
        if (idleDrop.Reason != SpeechConstants.ReasonNotIdle)
        {
            return false;
        }

        var failed = new ProactiveDeliveryCoordinator();
        var failedFacts = Ready();
        failed.AfterClaim(failedFacts, GoodClaim());
        var failedDrop = failed.AfterSpeechStarted(failedFacts, new SpeechStoreReply(false, "bad_args"));
        if (failedDrop.Step != SpeechStep.Release || failedDrop.Reason != SpeechConstants.ReasonSpeechStartedFailed)
        {
            return false;
        }

        var refused = new ProactiveDeliveryCoordinator();
        var refusedFacts = Ready();
        refused.AfterClaim(refusedFacts, GoodClaim());
        refused.AfterSpeechStarted(refusedFacts, new SpeechStoreReply(true, null));
        var refusedDrop = refused.AfterSpeak(refusedFacts, accepted: false);
        if (refusedDrop.Reason != SpeechConstants.ReasonVoiceTtsRefused)
        {
            return false;
        }

        var blind = new ProactiveDeliveryCoordinator();
        var blindFacts = Ready();
        blindFacts.MonitorAvailable = false;
        blind.AfterClaim(blindFacts, GoodClaim());
        blind.AfterSpeechStarted(blindFacts, new SpeechStoreReply(true, null));
        var blindDrop = blind.AfterSpeak(blindFacts, accepted: true);
        if (blindDrop.Reason != SpeechConstants.ReasonMonitorUnavailable)
        {
            return false;
        }

        var slowStart = new ProactiveDeliveryCoordinator();
        var slowFacts = Ready();
        DriveToAccepted(slowStart, slowFacts);
        slowFacts.UtcNow = slowFacts.UtcNow.AddSeconds(SpeechConstants.StartTimeoutSeconds + 1);
        if (slowStart.Poll(slowFacts).Reason != SpeechConstants.ReasonStartTimeout)
        {
            return false;
        }

        var slowEnd = new ProactiveDeliveryCoordinator();
        var endFacts = Ready();
        DriveToAccepted(slowEnd, endFacts);
        slowEnd.NotePlayback(endFacts, active: true, forced: false);
        endFacts.UtcNow = endFacts.UtcNow.AddSeconds(SpeechConstants.CompleteTimeoutSeconds + 1);
        if (slowEnd.Poll(endFacts).Reason != SpeechConstants.ReasonCompleteTimeout)
        {
            return false;
        }

        var second = new ProactiveDeliveryCoordinator();
        var secondFacts = Ready();
        DriveToAccepted(second, secondFacts);
        second.NotePlayback(secondFacts, active: true, forced: false);
        if (second.NotePlayback(secondFacts, active: true, forced: false).Reason != SpeechConstants.ReasonSecondBout)
        {
            return false;
        }

        var unexplained = new ProactiveDeliveryCoordinator();
        var unexplainedFacts = Ready();
        unexplained.AfterClaim(unexplainedFacts, GoodClaim());
        var lost = unexplained.ConfirmDispatch(unexplainedFacts);
        if (lost.Step != SpeechStep.Release || lost.Reason != SpeechConstants.ReasonReservationLost)
        {
            return false;
        }

        var forced = new ProactiveDeliveryCoordinator();
        var forcedFacts = Ready();
        DriveToAccepted(forced, forcedFacts);
        forced.NotePlayback(forcedFacts, active: true, forced: false);
        return forced.NotePlayback(forcedFacts, active: false, forced: true).Reason == SpeechConstants.ReasonReservationLost;
    }

    private static async Task<bool> LaterReplyDoesNotRefreshEchoTail()
    {
        var facts = Ready();
        var session = Session(new FakeSpeechGateway(), facts, new List<string>());
        await session.PollAsync();
        await session.NotePlayback(active: true, forced: false);
        await session.NotePlayback(active: false, forced: false);
        var proactiveEnd = facts.UtcNow;
        var duringTail = !session.Echo.AllowsCapture(pushToTalk: false, proactiveEnd.AddSeconds(1));
        var afterTail = session.Echo.AllowsCapture(
            pushToTalk: false,
            proactiveEnd.AddSeconds(SpeechConstants.EchoTailSeconds));
        facts.UtcNow = proactiveEnd.AddMinutes(2);
        await session.NotePlayback(active: true, forced: false);
        await session.NotePlayback(active: false, forced: false);
        var followUp = session.Echo.AllowsCapture(pushToTalk: false, facts.UtcNow.AddSeconds(0.5));
        return duringTail && afterTail && followUp;
    }

    private static async Task<bool> AcceptedLineIsNoted()
    {
        var noted = new List<string>();
        var accepted = new FakeSpeechGateway();
        var acceptedFacts = Ready();
        var acceptedSession = Session(accepted, acceptedFacts, new List<string>(), noteSpoken: noted.Add);
        await acceptedSession.PollAsync();
        var refused = new FakeSpeechGateway { SpeakAccepted = false };
        var refusedFacts = Ready();
        var refusedSession = Session(refused, refusedFacts, new List<string>(), noteSpoken: noted.Add);
        await refusedSession.PollAsync();
        var expected = SpeechPhrases.Pick("gmail", "Quinn", "brian_message", new PhraseCursor());
        return noted.Count == 1 && noted[0] == expected;
    }

    private static ProactiveSpeechSession Session(
        FakeSpeechGateway gateway,
        SpeechFacts facts,
        List<string> logs,
        Action? onHud = null,
        Action? stopPlayback = null,
        Action<string>? noteSpoken = null)
    {
        return new ProactiveSpeechSession(
            gateway,
            () => facts,
            () => WatcherProcessLatch.Running,
            stopPlayback,
            null,
            _ => onHud?.Invoke(),
            line =>
            {
                if (!string.IsNullOrEmpty(line))
                {
                    logs.Add(line);
                }
            },
            noteSpoken: noteSpoken);
    }

    private void Speech(string name, Func<bool> body)
    {
        _speechTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _speechPassed++;
            }
        });
    }

    private static SpeechFacts Ready()
    {
        return new SpeechFacts
        {
            UtcNow = DateTimeOffset.Parse("2026-10-16T19:00:00Z"),
            LocalNow = new DateTimeOffset(2026, 10, 16, 12, 0, 0, TimeSpan.Zero),
            BackendUp = true,
            MonitorAvailable = true,
        };
    }

    private static SpeechSnapshot Fresh(SpeechFacts facts)
    {
        return new SpeechSnapshot(true, null, false, false, facts.UtcNow);
    }

    private static SpeechClaimResult GoodClaim()
    {
        return new SpeechClaimResult(true, null, "item-1", "attempt-1", "Quinn", "brian_message", "gmail");
    }

    private static void DriveToAccepted(ProactiveDeliveryCoordinator coordinator, SpeechFacts facts)
    {
        coordinator.Poll(facts);
        coordinator.AfterSnapshot(facts, Fresh(facts));
        coordinator.AfterClaim(facts, GoodClaim());
        coordinator.AfterSpeechStarted(facts, new SpeechStoreReply(true, null));
        coordinator.AfterSpeak(facts, accepted: true);
    }

    private static (string Reason, Action<SpeechFacts> Arm)[] Gates()
    {
        return new (string, Action<SpeechFacts>)[]
        {
            (SpeechConstants.ReasonBackendDown, facts => facts.BackendUp = false),
            (SpeechConstants.ReasonLocked, facts => facts.Locked = true),
            (SpeechConstants.ReasonSuspended, facts => facts.Suspended = true),
            (SpeechConstants.ReasonTextMode, facts => facts.TextMode = true),
            (SpeechConstants.ReasonCapture, facts => facts.Capture = true),
            (SpeechConstants.ReasonTurn, facts => facts.Turn = true),
            (SpeechConstants.ReasonPlayback, facts => facts.Playback = true),
            (SpeechConstants.ReasonClarify, facts => facts.Clarify = true),
            (SpeechConstants.ReasonNotIdle, facts => facts.LastSubmitUtc = facts.UtcNow.AddSeconds(-1)),
        };
    }
}

internal sealed class FakeSpeechStore
{
    public string Delivery { get; set; } = "none";

    public bool ExpireOnRecover { get; set; }
}

internal sealed class FakeSpeechGateway : ISpeechGateway
{
    private readonly FakeSpeechStore _store;

    public FakeSpeechGateway()
        : this(new FakeSpeechStore())
    {
    }

    public FakeSpeechGateway(FakeSpeechStore store)
    {
        _store = store;
    }

    public int RecoverFailuresLeft { get; set; }

    public string RecoverReason { get; set; } = "no_store";

    public TaskCompletionSource<bool>? SpeakHold { get; set; }

    public Action? OnSpeakEntered { get; set; }

    public bool SpeakAccepted { get; set; } = true;

    public TaskCompletionSource<bool>? StartHold { get; set; }

    public Action? OnStartEntered { get; set; }

    public TaskCompletionSource<bool>? OutcomeHold { get; set; }

    public TaskCompletionSource<bool> OutcomeEntered { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);

    public SpeechStoreReply OutcomeReply { get; set; } = new(true, null);

    public SpeechStoreReply StartReply { get; set; } = new(true, null);

    public List<string> Calls { get; } = new();

    public List<string> Outcomes { get; } = new();

    public int SpeakCalls { get; private set; }

    public int OutcomeCalls { get; private set; }

    public int ClaimCalls { get; private set; }

    public Task<SpeechStoreReply> RecoverAsync()
    {
        Calls.Add("recover");
        if (RecoverFailuresLeft > 0)
        {
            RecoverFailuresLeft--;
            return Task.FromResult(new SpeechStoreReply(false, RecoverReason));
        }

        if (_store.ExpireOnRecover)
        {
            if (_store.Delivery == "claimed")
            {
                _store.Delivery = "none";
            }
            else if (_store.Delivery == "speech_started")
            {
                _store.Delivery = "delivery_uncertain";
            }
        }

        return Task.FromResult(new SpeechStoreReply(true, null));
    }

    public Task<SpeechSnapshot> SnapshotAsync()
    {
        Calls.Add("snapshot");
        var now = DateTimeOffset.Parse("2026-10-16T19:00:00Z");
        return Task.FromResult(new SpeechSnapshot(true, null, false, false, now));
    }

    public Task<SpeechClaimResult> ClaimAsync()
    {
        Calls.Add("claim");
        ClaimCalls++;
        if (_store.Delivery != "none")
        {
            return Task.FromResult(new SpeechClaimResult(false, SpeechConstants.ReasonNothingSpeakable, null, null, null, null, null));
        }

        _store.Delivery = "claimed";
        return Task.FromResult(new SpeechClaimResult(true, null, "item-1", "attempt-1", "Quinn", "brian_message", "gmail"));
    }

    public async Task<SpeechStoreReply> SpeechStartedAsync(string itemId, string attemptId)
    {
        Calls.Add("speech_started");
        OnStartEntered?.Invoke();
        if (StartHold is not null)
        {
            await StartHold.Task;
        }

        if (StartReply.Ok && _store.Delivery == "claimed")
        {
            _store.Delivery = "speech_started";
        }

        return StartReply;
    }

    public async Task<SpeechStoreReply> OutcomeAsync(string itemId, string attemptId, string outcome)
    {
        Calls.Add("outcome");
        Outcomes.Add(outcome);
        OutcomeCalls++;
        OutcomeEntered.TrySetResult(true);
        if (OutcomeHold is not null)
        {
            await OutcomeHold.Task;
        }

        if (OutcomeReply.Ok)
        {
            _store.Delivery = outcome;
        }

        return OutcomeReply;
    }

    public Task<SpeechStoreReply> ReleaseAsync(string itemId, string attemptId)
    {
        Calls.Add("release");
        if (_store.Delivery == "claimed")
        {
            _store.Delivery = "none";
        }

        return Task.FromResult(new SpeechStoreReply(true, null));
    }

    public async Task<bool> SpeakAsync(string phrase)
    {
        Calls.Add("speak");
        SpeakCalls++;
        OnSpeakEntered?.Invoke();
        if (SpeakHold is not null)
        {
            await SpeakHold.Task;
        }

        return SpeakAccepted;
    }

    public Task<WatcherHudResult> HealthAsync(WatcherProcessLatch latch, DateTimeOffset utcNow)
    {
        Calls.Add("health");
        return Task.FromResult(WatcherHud.Classify(
            new WatcherHealthRow
            {
                GmailOkAt = "2026-10-16T19:00:00Z",
                CalendarOkAt = "2026-10-16T19:00:00Z",
            },
            latch,
            utcNow));
    }
}
