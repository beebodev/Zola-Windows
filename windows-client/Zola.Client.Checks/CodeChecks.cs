using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Zola.Client.Speech;
using Zola.Client.Voice;

// P10-READ: code reader checks. The code value here is a synthetic sentinel.
internal sealed partial class CheckRunner
{
    private const string CodeSentinel = "CODE-SENTINEL-8841";
    private static readonly string[] CodeOutcomesAllowed = ["read", "shown", "failed", "cancelled"];

    private sealed class CodeHarness
    {
        public readonly object Gate = new();
        public readonly List<(string Id, string Outcome, string? Reason)> Answers = new();
        public readonly List<string> Logs = new();
        public readonly List<string> Events = new();
        public readonly List<string> Spoken = new();
        public readonly List<string> Shown = new();
        public int StopCount;
        public CodeReader Reader = null!;

        public void Note(string e)
        {
            lock (Gate)
            {
                Events.Add(e);
            }
        }

        public string Joined()
        {
            lock (Gate)
            {
                return string.Join("|", Events);
            }
        }

        public int AnswerCount()
        {
            lock (Gate)
            {
                return Answers.Count;
            }
        }

        // the sentinel may reach the voice and the screen. It must not reach an answer or a log line.
        public bool ValueStayedLocal()
        {
            lock (Gate)
            {
                return !Answers.Any(a => a.Outcome.Contains(CodeSentinel) || (a.Reason ?? "").Contains(CodeSentinel) || a.Id.Contains(CodeSentinel))
                    && !Logs.Any(l => l.Contains(CodeSentinel))
                    && Answers.All(a => CodeOutcomesAllowed.Contains(a.Outcome));
            }
        }
    }

    private sealed class FakeRedeemer : ICodeRedeemer
    {
        private readonly CodeHarness _h;
        private readonly Func<CancellationToken, Task<CodeRedeemResult>> _behavior;

        public FakeRedeemer(CodeHarness h, Func<CancellationToken, Task<CodeRedeemResult>> behavior)
        {
            _h = h;
            _behavior = behavior;
        }

        public Task<CodeRedeemResult> RedeemAsync(string sessionId, string handle, CancellationToken ct)
        {
            _h.Note("redeem");
            return _behavior(ct);
        }
    }

    private sealed class FakeVoice : ICodeVoice
    {
        private readonly CodeHarness _h;
        private readonly Func<CancellationToken, Task<CodePlayback>> _behavior;

        public FakeVoice(CodeHarness h, Func<CancellationToken, Task<CodePlayback>> behavior)
        {
            _h = h;
            _behavior = behavior;
        }

        public Task<CodePlayback> SpeakAsync(string value, CancellationToken ct)
        {
            lock (_h.Gate)
            {
                _h.Spoken.Add(value);
            }

            _h.Note("speak");
            return _behavior(ct);
        }

        public void Stop()
        {
            lock (_h.Gate)
            {
                _h.StopCount++;
            }

            _h.Note("stop");
        }
    }

    private sealed class FakeDisplay : ICodeDisplay
    {
        private readonly CodeHarness _h;

        public FakeDisplay(CodeHarness h)
        {
            _h = h;
        }

        public void Show(string value)
        {
            lock (_h.Gate)
            {
                _h.Shown.Add(value);
            }

            _h.Note("show");
        }

        public void Clear() => _h.Note("clear");
    }

    private sealed class FakeLatch : ICodeLatch
    {
        private readonly CodeHarness _h;

        public FakeLatch(CodeHarness h)
        {
            _h = h;
        }

        public void Begin() => _h.Note("latch.begin");

        public void End() => _h.Note("latch.end");
    }

    private static CodeHarness CodeHarnessWith(
        Func<CancellationToken, Task<CodeRedeemResult>> redeem,
        Func<CancellationToken, Task<CodePlayback>> speak,
        TimeSpan? deadline = null,
        Func<bool>? isVoiceMode = null)
    {
        var h = new CodeHarness();
        h.Reader = new CodeReader(
            new FakeRedeemer(h, redeem),
            new FakeVoice(h, speak),
            new FakeDisplay(h),
            new FakeLatch(h),
            (id, outcome, reason) =>
            {
                lock (h.Gate)
                {
                    h.Answers.Add((id, outcome, reason));
                }

                h.Note("answer:" + outcome);
            },
            line =>
            {
                lock (h.Gate)
                {
                    h.Logs.Add(line);
                }
            },
            deadline,
            isVoiceMode);
        return h;
    }

    private static Task<CodeRedeemResult> CodeOk() => Task.FromResult(new CodeRedeemResult(true, CodeSentinel, null));

    private static Task<CodeRedeemResult> CodeRefused(string reason) => Task.FromResult(new CodeRedeemResult(false, null, reason));

    private static async Task<CodePlayback> CodeHoldUntilCancelled(CancellationToken ct)
    {
        try
        {
            await Task.Delay(Timeout.Infinite, ct).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
        }

        return CodePlayback.Cancelled;
    }

    private static bool CodeWait(Func<bool> condition, int milliseconds = 4000)
    {
        var until = DateTime.UtcNow.AddMilliseconds(milliseconds);
        while (DateTime.UtcNow < until)
        {
            if (condition())
            {
                return true;
            }

            Thread.Sleep(10);
        }

        return condition();
    }

    private void RunCodeRows()
    {
        Code("read: redeem then speak then answer read, value never in an answer or log", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), _ => Task.FromResult(CodePlayback.Completed));
            h.Reader.StartAsync("srq-1", "gw-1", "handle-1").Wait(5000);
            return h.Answers.Count == 1
                && h.Answers[0] == ("srq-1", "read", null)
                && h.Spoken.SequenceEqual([CodeSentinel])
                && h.Shown.Count == 0
                && h.ValueStayedLocal()
                && h.Logs.Count == 1
                && h.Joined() == "latch.begin|redeem|speak|answer:read|stop|latch.end";
        });
        // P10-READ F7: text mode never speaks; Voice mode speaks; "show" prefers the screen
        Code("text-mode request never calls the voice and answers shown", () =>
        {
            var h = CodeHarnessWith(
                _ => CodeOk(),
                _ => Task.FromResult(CodePlayback.Completed),
                isVoiceMode: () => false);
            h.Reader.StartAsync("srq-1", "gw-1", "h").Wait(5000);
            return h.Answers.Count == 1
                && h.Answers[0].Outcome == "shown"
                && h.Spoken.Count == 0
                && h.Shown.SequenceEqual([CodeSentinel])
                && !h.Joined().Contains("speak")
                && !h.Joined().Contains("latch.begin")
                && h.ValueStayedLocal();
        });
        Code("voice-mode request speaks and answers read", () =>
        {
            var h = CodeHarnessWith(
                _ => CodeOk(),
                _ => Task.FromResult(CodePlayback.Completed),
                isVoiceMode: () => true);
            h.Reader.StartAsync("srq-1", "gw-1", "h").Wait(5000);
            return h.Answers[0].Outcome == "read" && h.Spoken.SequenceEqual([CodeSentinel]) && h.Shown.Count == 0;
        });
        Code("voice-mode show phrase shows instead of speaking", () =>
        {
            var h = CodeHarnessWith(
                _ => CodeOk(),
                _ => Task.FromResult(CodePlayback.Completed),
                isVoiceMode: () => true);
            h.Reader.StartAsync("srq-1", "gw-1", "h", preferShow: true).Wait(5000);
            return h.Answers[0].Outcome == "shown"
                && h.Spoken.Count == 0
                && h.Shown.SequenceEqual([CodeSentinel])
                && !h.Joined().Contains("speak");
        });
        Code("echo latch is up before the redeem and down only after playback ends", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), _ => Task.FromResult(CodePlayback.Completed));
            h.Reader.StartAsync("srq-1", "gw-1", "h").Wait(5000);
            var joined = h.Joined();
            return joined.IndexOf("latch.begin", StringComparison.Ordinal) < joined.IndexOf("redeem", StringComparison.Ordinal)
                && joined.LastIndexOf("latch.end", StringComparison.Ordinal) > joined.LastIndexOf("speak", StringComparison.Ordinal);
        });
        Code("echo latch refuses capture while up and inside the tail, never remembers the value", () =>
        {
            var now = DateTimeOffset.Parse("2026-11-01T12:00:00Z");
            var guard = new SpeechEchoGuard();
            var latch = new EchoCodeLatch(guard, () => now);
            latch.Begin();
            var during = !guard.AllowsCapture(false, now) && guard.Haystack == CodeReadConstants.LatchPhrase;
            now = now.AddSeconds(5);
            latch.End();
            var tail = !guard.AllowsCapture(false, now.AddSeconds(1)) && guard.Active(now.AddSeconds(1));
            var after = guard.AllowsCapture(false, now.AddSeconds(SpeechConstants.EchoTailSeconds + 1));
            return during && tail && after && !CodeReadConstants.LatchPhrase.Contains(CodeSentinel);
        });
        Code("voice failure shows the code on screen, answers shown, clears on dismiss", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), _ => Task.FromResult(CodePlayback.Failed));
            var run = h.Reader.StartAsync("srq-1", "gw-1", "h");
            var shown = CodeWait(() => h.AnswerCount() == 1);
            var stillUp = h.Reader.IsActive && h.Shown.SequenceEqual([CodeSentinel]) && !h.Joined().Contains("clear");
            h.Reader.Dismiss();
            run.Wait(5000);
            return shown
                && stillUp
                && h.Answers[0].Outcome == "shown"
                && h.Joined().Contains("clear")
                && !h.Reader.IsActive
                && h.ValueStayedLocal();
        });
        Code("shown code clears itself at the client deadline", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), _ => Task.FromResult(CodePlayback.Failed), TimeSpan.FromMilliseconds(250));
            var run = h.Reader.StartAsync("srq-1", "gw-1", "h");
            var done = run.Wait(5000);
            return done && h.Answers[0].Outcome == "shown" && h.Joined().Contains("clear") && h.Joined().EndsWith("latch.end", StringComparison.Ordinal);
        });
        Code("a refusal from the phone passes through as failed with a short reason", () =>
        {
            var failed = CodeHarnessWith(_ => CodeRefused("not_identifiable"), _ => Task.FromResult(CodePlayback.Completed));
            failed.Reader.StartAsync("a", "s", "h").Wait(5000);
            var expired = CodeHarnessWith(_ => CodeRefused("expired"), _ => Task.FromResult(CodePlayback.Completed));
            expired.Reader.StartAsync("a", "s", "h").Wait(5000);
            var odd = CodeHarnessWith(_ => CodeRefused("Bad Reason: " + CodeSentinel), _ => Task.FromResult(CodePlayback.Completed));
            odd.Reader.StartAsync("a", "s", "h").Wait(5000);
            var cancelled = CodeHarnessWith(_ => CodeRefused("cancelled"), _ => Task.FromResult(CodePlayback.Completed));
            cancelled.Reader.StartAsync("a", "s", "h").Wait(5000);
            return failed.Answers[0] == ("a", "failed", "not_identifiable")
                && expired.Answers[0] == ("a", "failed", "expired")
                && odd.Answers[0] == ("a", "failed", "failed")
                && cancelled.Answers[0] == ("a", "cancelled", null)
                && failed.Spoken.Count == 0
                && failed.Joined() == "latch.begin|redeem|answer:failed|stop|latch.end"
                && odd.ValueStayedLocal();
        });
        Code("a redeemer that throws reads as no_connection", () =>
        {
            var h = CodeHarnessWith(_ => throw new InvalidOperationException("pipe"), _ => Task.FromResult(CodePlayback.Completed));
            h.Reader.StartAsync("a", "s", "h").Wait(5000);
            return h.Answers[0] == ("a", "failed", "no_connection") && h.Spoken.Count == 0;
        });
        Code("a voice that throws reads as shown, not read", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), _ => throw new InvalidOperationException("synth"), TimeSpan.FromMilliseconds(300));
            h.Reader.StartAsync("a", "s", "h").Wait(5000);
            return h.Answers[0].Outcome == "shown" && h.Answers[0].Outcome != "read";
        });
        Code("interruption mid-playback: connection loss stops playback and answers cancelled", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), CodeHoldUntilCancelled);
            var run = h.Reader.StartAsync("srq-1", "gw-1", "h");
            CodeWait(() => h.Spoken.Count == 1);
            h.Reader.CancelAll("connection_lost");
            var done = run.Wait(5000);
            return done
                && h.Answers.Count == 1
                && h.Answers[0] == ("srq-1", "cancelled", null)
                && h.StopCount >= 1
                && h.Shown.Count == 0
                && h.Joined().EndsWith("latch.end", StringComparison.Ordinal)
                && h.Logs[0].Contains("connection_lost")
                && h.ValueStayedLocal();
        });
        Code("serve restart during playback cancels the same way", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), CodeHoldUntilCancelled);
            var run = h.Reader.StartAsync("srq-1", "gw-1", "h");
            CodeWait(() => h.Spoken.Count == 1);
            h.Reader.CancelAll("serve_restart");
            run.Wait(5000);
            return h.Answers[0].Outcome == "cancelled" && h.Logs[0].Contains("serve_restart") && !h.Reader.IsActive;
        });
        Code("a cancel for the request id during the redeem wait never speaks", () =>
        {
            var h = CodeHarnessWith(CodeHoldRedeem, _ => Task.FromResult(CodePlayback.Completed));
            var run = h.Reader.StartAsync("srq-1", "gw-1", "h");
            CodeWait(() => h.Joined().Contains("redeem"));
            h.Reader.Cancel("srq-other", "server_cancel");
            var untouched = h.Reader.IsActive && h.AnswerCount() == 0;
            h.Reader.Cancel("srq-1", "server_cancel");
            run.Wait(5000);
            return untouched && h.Answers[0].Outcome == "cancelled" && h.Spoken.Count == 0 && h.Logs[0].Contains("server_cancel");
        });
        Code("playback never starts after the client deadline, even if the value arrives late", () =>
        {
            var h = CodeHarnessWith(
                async _ =>
                {
                    // a redeemer that ignores the token and answers after the deadline
                    await Task.Delay(500).ConfigureAwait(false);
                    return new CodeRedeemResult(true, CodeSentinel, null);
                },
                _ => Task.FromResult(CodePlayback.Completed),
                TimeSpan.FromMilliseconds(150));
            h.Reader.StartAsync("srq-1", "gw-1", "h").Wait(5000);
            return h.Answers[0].Outcome == "cancelled" && h.Spoken.Count == 0 && h.Shown.Count == 0 && h.ValueStayedLocal();
        });
        Code("the client deadline fires during playback and the answer is cancelled", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), CodeHoldUntilCancelled, TimeSpan.FromMilliseconds(200));
            h.Reader.StartAsync("srq-1", "gw-1", "h").Wait(5000);
            return h.Answers[0].Outcome == "cancelled" && h.StopCount >= 1;
        });
        Code("the client deadline is shorter than the tool wait and the handle ttl", () =>
            CodeReadConstants.ClientDeadline < TimeSpan.FromSeconds(45)
            && TimeSpan.FromSeconds(45) < TimeSpan.FromSeconds(60)
            && CodeReadConstants.VoiceName == "Zira"
            && CodeReadConstants.Method == "code_read");
        Code("a second ask while one is active is refused busy and does not disturb the first", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), CodeHoldUntilCancelled);
            var run = h.Reader.StartAsync("srq-1", "gw-1", "h");
            CodeWait(() => h.Spoken.Count == 1);
            h.Reader.StartAsync("srq-2", "gw-1", "h2").Wait(1000);
            var busy = h.Answers.Count == 1 && h.Answers[0] == ("srq-2", "failed", "busy") && h.Reader.IsActive;
            h.Reader.CancelAll("window_closed");
            run.Wait(5000);
            return busy && h.Answers.Count == 2 && h.Answers[1] == ("srq-1", "cancelled", null);
        });
        Code("one answer per request even if cancelled again afterwards", () =>
        {
            var h = CodeHarnessWith(_ => CodeOk(), _ => Task.FromResult(CodePlayback.Completed));
            h.Reader.StartAsync("srq-1", "gw-1", "h").Wait(5000);
            h.Reader.CancelAll("late");
            h.Reader.Cancel("srq-1", "late");
            return h.Answers.Count == 1 && !h.Reader.IsActive;
        });
        Code("the value never reaches an answer, a log line, or a latch phrase across every path", () =>
        {
            var all = new List<CodeHarness>();
            foreach (var playback in new[] { CodePlayback.Completed, CodePlayback.Failed, CodePlayback.Cancelled })
            {
                var h = CodeHarnessWith(_ => CodeOk(), _ => Task.FromResult(playback), TimeSpan.FromMilliseconds(200));
                h.Reader.StartAsync("srq-1", "gw-1", "h").Wait(5000);
                all.Add(h);
            }

            return all.All(h => h.ValueStayedLocal());
        });
        Code("redeem over the pipe: request carries the secret, handle, and session; value returns to the caller", () =>
        {
            var pipe = "ZolaPhoneCheck" + Environment.ProcessId + "a";
            string? seen = null;
            using var server = PipeServe(pipe, line =>
            {
                seen = line;
                return JsonSerializer.Serialize(new Dictionary<string, object> { ["ok"] = true, ["value"] = CodeSentinel, ["value_kind"] = "code" });
            });
            var redeemer = new PhoneCodeRedeemer(() => "launch-secret", pipe);
            var result = redeemer.RedeemAsync("gw-1", "handle-1", CancellationToken.None).Result;
            using var doc = JsonDocument.Parse(seen ?? "{}");
            var root = doc.RootElement;
            return result.Ok
                && result.Value == CodeSentinel
                && root.GetProperty("type").GetString() == "code.redeem"
                && root.GetProperty("secret").GetString() == "launch-secret"
                && root.GetProperty("handle").GetString() == "handle-1"
                && root.GetProperty("session_id").GetString() == "gw-1";
        });
        Code("redeem over the pipe: a refusal carries its reason and no value", () =>
        {
            var pipe = "ZolaPhoneCheck" + Environment.ProcessId + "b";
            using var server = PipeServe(pipe, _ => "{\"ok\":false,\"reason\":\"replay\"}");
            var result = new PhoneCodeRedeemer(() => "s", pipe).RedeemAsync("gw-1", "h", CancellationToken.None).Result;
            return !result.Ok && result.Value is null && result.Reason == "replay";
        });
        Code("redeem over the pipe: no listener reads as no_connection", () =>
        {
            var pipe = "ZolaPhoneCheck" + Environment.ProcessId + "none";
            var result = new PhoneCodeRedeemer(() => "s", pipe).RedeemAsync("gw-1", "h", CancellationToken.None).Result;
            return !result.Ok && result.Reason == "no_connection";
        });
        Code("redeem over the pipe: a cancel while the phone is slow stops the wait and drops a late value", () =>
        {
            var pipe = "ZolaPhoneCheck" + Environment.ProcessId + "slow";
            using var release = new ManualResetEventSlim(false);
            using var server = PipeServe(pipe, _ =>
            {
                release.Wait(5000);
                return JsonSerializer.Serialize(new Dictionary<string, object> { ["ok"] = true, ["value"] = CodeSentinel });
            });
            using var cts = new CancellationTokenSource(150);
            var started = DateTime.UtcNow;
            var cancelled = false;
            try
            {
                new PhoneCodeRedeemer(() => "s", pipe).RedeemAsync("gw-1", "h", cts.Token).Wait(4000);
            }
            catch (AggregateException ex) when (ex.InnerException is OperationCanceledException)
            {
                cancelled = true;
            }

            release.Set();
            return cancelled && DateTime.UtcNow - started < TimeSpan.FromSeconds(2);
        });
        Code("local voice: spoken form is one digit or letter at a time", () =>
            LocalCodeVoice.SpokenForm("471298") == "4 7 1 2 9 8"
            && LocalCodeVoice.SpokenForm("G-4412") == "G . 4 4 1 2"
            && LocalCodeVoice.SpokenForm("ab12") == "A B 1 2");
        Code("local voice: wave duration comes from the header, and a streamed header uses the bytes in memory", () =>
        {
            var wave = Wave(byteRate: 16000, dataBytes: 32000, declaredData: 32000);
            var streamed = Wave(byteRate: 16000, dataBytes: 16000, declaredData: 0);
            var bad = new byte[10];
            return LocalCodeVoice.WaveDuration(wave) == TimeSpan.FromSeconds(2)
                && LocalCodeVoice.WaveDuration(streamed) == TimeSpan.FromSeconds(1)
                && LocalCodeVoice.WaveDuration(bad) is null;
        });
        Code("local voice: Zira renders to memory and touches no file", () =>
        {
            // the process temp folder is an empty private one for the render, so any file written there shows
            var scratch = Path.Combine(Path.GetTempPath(), "zola-code-voice-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(scratch);
            var oldTmp = Environment.GetEnvironmentVariable("TMP");
            var oldTemp = Environment.GetEnvironmentVariable("TEMP");
            var before = FileSnapshot(includeTemp: false);
            byte[]? wave;
            try
            {
                Environment.SetEnvironmentVariable("TMP", scratch);
                Environment.SetEnvironmentVariable("TEMP", scratch);
                wave = LocalCodeVoice.Render("471298", CodeReadConstants.VoiceName);
            }
            finally
            {
                Environment.SetEnvironmentVariable("TMP", oldTmp);
                Environment.SetEnvironmentVariable("TEMP", oldTemp);
            }

            var wrote = Directory.EnumerateFileSystemEntries(scratch).Any();
            Directory.Delete(scratch, true);
            var same = before.SetEquals(FileSnapshot(includeTemp: false));
            if (wave is null)
            {
                Console.WriteLine("note: Zira is not installed here; the render row only proved no file was written");
                return !wrote && same;
            }

            var duration = LocalCodeVoice.WaveDuration(wave);
            return Encoding.ASCII.GetString(wave, 0, 4) == "RIFF"
                && duration is { } d && d > TimeSpan.FromMilliseconds(300) && d < TimeSpan.FromSeconds(10)
                && !wrote
                && same;
        });
        Code("local voice: an absent voice renders nothing and falls to the screen, never to another voice", () =>
            LocalCodeVoice.Render("1234", "NoSuchVoiceName") is null);
        Code("source: the code path has no file, network, voice.tts, or transcript call", () =>
        {
            var root = ClientRoot();
            var forbidden = new Regex(
                @"HttpClient|WebSocket|TcpClient|UdpClient|\bSocket\b|File\.|FileStream|StreamWriter|GetTempFileName|SetOutputToWaveFile|SetOutputToDefaultAudioDevice|voice\.tts|Clipboard",
                RegexOptions.Compiled);
            string[] files =
            [
                Path.Combine(root, "Zola.Client", "Voice", "LocalCodeVoice.cs"),
                Path.Combine(root, "Zola.Client", "Voice", "CodeReader.cs"),
                Path.Combine(root, "Zola.Client", "Voice", "PhoneCodeRedeemer.cs"),
            ];
            return files.All(f => !forbidden.IsMatch(StripComments(File.ReadAllText(f))));
        });
        Code("source: the window never puts the value in the conversation, a notice, a status, or a log", () =>
        {
            var root = ClientRoot();
            var window = StripComments(File.ReadAllText(Path.Combine(root, "Zola.Client", "MainWindow.CodeRead.cs")));
            var reader = StripComments(File.ReadAllText(Path.Combine(root, "Zola.Client", "Voice", "CodeReader.cs")));
            var banned = new Regex(@"AddBubble|ShowRequestNotice|StatusText|DetailText|WriteDockLog|Transcript\.|voice\.tts|RememberProactivePhrase|RememberSpokenEcho");
            // the only line that touches the value in the window is the one TextBlock
            var valueLines = window.Split('\n').Where(l => l.Contains("value", StringComparison.Ordinal)).ToList();
            var logsOnlyOutcome = !Regex.IsMatch(reader, @"_log\(\$?""[^""]*\{value|Log\([^)]*value");
            return !banned.IsMatch(window)
                && valueLines.All(l => l.Contains("CodeShownText") || l.Contains("Show(") || l.Contains("ShowCodeShown") || l.Contains("string value") || l.Contains("(value)"))
                && logsOnlyOutcome
                && window.Contains("CodeShownText.Text = \"\"", StringComparison.Ordinal);
        });
        Code("source: the broker answers code_read on its own request and ends it on every loss", () =>
        {
            var root = ClientRoot();
            var broker = File.ReadAllText(Path.Combine(root, "Zola.Client", "ServerRequestBroker.cs"));
            var window = File.ReadAllText(Path.Combine(root, "Zola.Client", "MainWindow.CodeRead.cs"));
            var replacing = Between(broker, "public void MarkSocketReplacing()", "public void OnSessionChanged");
            var session = Between(broker, "public void OnSessionChanged", "public void OnRequest(");
            var cancel = Between(broker, "private List<Action> AcceptCancelLocked", "private List<Action> WithdrawCodeReadsLocked");
            var reconcile = Between(broker, "private List<Action> ReconcileOpenRequestsLocked", "private Entry NewEntry");
            var accept = Between(broker, "if (method == MethodCodeRead)", "if (method != MethodClarify");
            return broker.Contains("MethodCodeRead = \"code_read\"", StringComparison.Ordinal)
                && replacing.Contains("WithdrawCodeReadsLocked", StringComparison.Ordinal)
                && session.Contains("WithdrawCodeReadsLocked", StringComparison.Ordinal)
                && cancel.Contains("CodeReadWithdrawn", StringComparison.Ordinal)
                && reconcile.Contains("CodeReadWithdrawn", StringComparison.Ordinal)
                && accept.Contains("replayed", StringComparison.Ordinal)
                && accept.Contains("OutcomeCancelled", StringComparison.Ordinal)
                && !accept.Split('\n').Any(l => l.Contains("WriteLog", StringComparison.Ordinal) && l.Contains("handle", StringComparison.OrdinalIgnoreCase))
                && window.Contains("ConnectionLost", StringComparison.Ordinal)
                && window.Contains("UnexpectedExit", StringComparison.Ordinal)
                && window.Contains("Closed +=", StringComparison.Ordinal)
                && window.Contains("CodeReadWithdrawn", StringComparison.Ordinal)
                && window.Contains("AnswerCodeRead", StringComparison.Ordinal)
                && window.Contains("CodeEcho = echo", StringComparison.Ordinal);
        });
        Code("source: capture is refused while the code latch is up", () =>
        {
            var voice = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "VoiceController.cs"));
            return voice.Contains("CodeEcho is not null && !CodeEcho.AllowsCapture", StringComparison.Ordinal);
        });
    }

    private static Task<CodeRedeemResult> CodeHoldRedeem(CancellationToken ct) =>
        Task.Run<CodeRedeemResult>(async () =>
        {
            try
            {
                await Task.Delay(Timeout.Infinite, ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                throw;
            }

            return new CodeRedeemResult(false, null, null);
        });

    private static string ClientRoot() => Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", ".."));

    private static string StripComments(string source) => Regex.Replace(source, @"//[^\n]*", "");

    private static string Between(string text, string start, string end)
    {
        var from = text.IndexOf(start, StringComparison.Ordinal);
        if (from < 0)
        {
            return "";
        }

        var to = text.IndexOf(end, from + start.Length, StringComparison.Ordinal);
        return to < 0 ? text[from..] : text[from..to];
    }

    private static HashSet<string> FileSnapshot(bool includeTemp)
    {
        var set = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var dirs = new List<string> { Directory.GetCurrentDirectory(), AppContext.BaseDirectory };
        if (includeTemp)
        {
            dirs.Add(Path.GetTempPath());
        }

        foreach (var dir in dirs)
        {
            try
            {
                foreach (var path in Directory.EnumerateFiles(dir, "*", SearchOption.TopDirectoryOnly))
                {
                    set.Add(path);
                }
            }
            catch (Exception)
            {
            }
        }

        return set;
    }

    private static byte[] Wave(int byteRate, int dataBytes, int declaredData)
    {
        var bytes = new byte[44 + dataBytes];
        Encoding.ASCII.GetBytes("RIFF").CopyTo(bytes, 0);
        BitConverter.GetBytes(36 + dataBytes).CopyTo(bytes, 4);
        Encoding.ASCII.GetBytes("WAVEfmt ").CopyTo(bytes, 8);
        BitConverter.GetBytes(16).CopyTo(bytes, 16);
        BitConverter.GetBytes((short)1).CopyTo(bytes, 20);
        BitConverter.GetBytes((short)1).CopyTo(bytes, 22);
        BitConverter.GetBytes(byteRate / 2).CopyTo(bytes, 24);
        BitConverter.GetBytes(byteRate).CopyTo(bytes, 28);
        BitConverter.GetBytes((short)2).CopyTo(bytes, 32);
        BitConverter.GetBytes((short)16).CopyTo(bytes, 34);
        Encoding.ASCII.GetBytes("data").CopyTo(bytes, 36);
        BitConverter.GetBytes(declaredData).CopyTo(bytes, 40);
        return bytes;
    }

    // one-shot fake ZolaPhone: reads a line, answers with the handler's reply
    private static IDisposable PipeServe(string name, Func<string, string> reply)
    {
        var stop = new CancellationTokenSource();
        var server = new NamedPipeServerStream(name, PipeDirection.InOut, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
        var worker = Task.Run(async () =>
        {
            try
            {
                await server.WaitForConnectionAsync(stop.Token).ConfigureAwait(false);
                var line = Zola.Client.PhonePipe.ReadLine(server) ?? "";
                var answer = Encoding.UTF8.GetBytes(reply(line) + "\n");
                await server.WriteAsync(answer, stop.Token).ConfigureAwait(false);
                await server.FlushAsync(stop.Token).ConfigureAwait(false);
                await Task.Delay(300, stop.Token).ConfigureAwait(false);
            }
            catch (Exception)
            {
            }
        });
        return new PipeScope(stop, server, worker);
    }

    private sealed class PipeScope : IDisposable
    {
        private readonly CancellationTokenSource _stop;
        private readonly NamedPipeServerStream _server;
        private readonly Task _worker;

        public PipeScope(CancellationTokenSource stop, NamedPipeServerStream server, Task worker)
        {
            _stop = stop;
            _server = server;
            _worker = worker;
        }

        public void Dispose()
        {
            _stop.Cancel();
            try
            {
                _worker.Wait(1000);
            }
            catch (Exception)
            {
            }

            _server.Dispose();
            _stop.Dispose();
        }
    }

    private void Code(string name, Func<bool> body)
    {
        _codeTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _codePassed++;
            }
        });
    }
}
