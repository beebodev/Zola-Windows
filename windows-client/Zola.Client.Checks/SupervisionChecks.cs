using Zola.Client.Supervision;
using Zola.Client.Voice;

internal sealed partial class CheckRunner
{
    private void RunSupervisionRows()
    {
        Supervision("three exits spawn and the fourth in the window is terminal", () =>
        {
            var policy = new RestartPolicy();
            var first = policy.NoteRestartAttempt(T(0));
            var second = policy.NoteRestartAttempt(T(60));
            var third = policy.NoteRestartAttempt(T(120));
            var fourth = policy.NoteRestartAttempt(T(180));
            return first == RestartChoice.BackoffThenSpawn
                && second == RestartChoice.BackoffThenSpawn
                && third == RestartChoice.BackoffThenSpawn
                && fourth == RestartChoice.Terminal
                && policy.IsTerminal;
        });

        Supervision("an attempt older than the window drops out", () =>
        {
            var policy = new RestartPolicy();
            policy.NoteRestartAttempt(T(0));
            policy.NoteRestartAttempt(T(200));
            var later = policy.NoteRestartAttempt(T(700));
            return later == RestartChoice.BackoffThenSpawn && policy.AttemptsInWindow(T(700)) == 2;
        });

        Supervision("terminal stays after the window rolls until reset", () =>
        {
            var policy = new RestartPolicy();
            policy.NoteRestartAttempt(T(0));
            policy.NoteRestartAttempt(T(60));
            policy.NoteRestartAttempt(T(120));
            policy.NoteRestartAttempt(T(180));
            var after = policy.NoteRestartAttempt(T(10_000));
            policy.Reset();
            var again = policy.NoteRestartAttempt(T(10_001));
            return after == RestartChoice.Terminal
                && !policy.IsTerminal
                && again == RestartChoice.BackoffThenSpawn;
        });

        Supervision("a deliberate stop does not count", () =>
        {
            var policy = new RestartPolicy();
            policy.NoteDeliberateStop();
            var choice = policy.NoteRestartAttempt(T(0));
            var action = policy.Decide(false, null, false, T(1));
            return choice == RestartChoice.IgnoredDeliberate
                && action == RecoveryAction.Stopped
                && policy.AttemptsInWindow(T(1)) == 0;
        });

        Supervision("first two health failures stay fail-closed and the third tree-kills", () =>
        {
            var policy = new RestartPolicy();
            var first = policy.Decide(true, false, false, T(0));
            var second = policy.Decide(true, false, false, T(10));
            var third = policy.Decide(true, false, false, T(20));
            return first == RecoveryAction.ProbeAgainAfterHungSpacing
                && second == RecoveryAction.ProbeAgainAfterHungSpacing
                && third == RecoveryAction.TreeKillThenSpawn
                && policy.AttemptsInWindow(T(20)) == 1;
        });

        Supervision("a healthy probe resets the hung count", () =>
        {
            var policy = new RestartPolicy();
            policy.Decide(true, false, false, T(0));
            policy.Decide(true, false, false, T(10));
            policy.Decide(true, true, true, T(15));
            var again = policy.Decide(true, false, false, T(20));
            return again == RecoveryAction.ProbeAgainAfterHungSpacing && policy.AttemptsInWindow(T(20)) == 0;
        });

        Supervision("five reconnects then tree-kill and the kill counts", () =>
        {
            var policy = new RestartPolicy();
            var actions = new RecoveryAction[6];
            for (var i = 0; i < 5; i++)
            {
                actions[i] = policy.Decide(true, true, false, T(i * 5));
            }

            actions[5] = policy.Decide(true, true, false, T(25));
            return actions[0] == RecoveryAction.Reconnect
                && actions[4] == RecoveryAction.Reconnect
                && actions[5] == RecoveryAction.TreeKillThenSpawn
                && policy.AttemptsInWindow(T(25)) == 1;
        });

        Supervision("a 30 second reconnect budget tree-kills before five attempts", () =>
        {
            var policy = new RestartPolicy();
            var first = policy.Decide(true, true, false, T(0));
            var expired = policy.Decide(true, true, false, T(30));
            return first == RecoveryAction.Reconnect
                && expired == RecoveryAction.TreeKillThenSpawn
                && policy.AttemptsInWindow(T(30)) == 1;
        });

        Supervision("socket loss with health ok does not count until the kill", () =>
        {
            var policy = new RestartPolicy();
            policy.Decide(true, true, false, T(0));
            var before = policy.AttemptsInWindow(T(5));
            policy.Decide(true, true, false, T(5));
            return before == 0 && policy.AttemptsInWindow(T(5)) == 0;
        });

        Supervision("a dead process restarts without waiting for three health failures", () =>
        {
            var policy = new RestartPolicy();
            var action = policy.Decide(false, null, false, T(0));
            return action == RecoveryAction.SpawnAfterBackoff && policy.AttemptsInWindow(T(0)) == 1;
        });

        Supervision("the restart past the limit still tree-kills a living process", () =>
        {
            var policy = new RestartPolicy();
            policy.NoteRestartAttempt(T(0));
            policy.NoteRestartAttempt(T(10));
            policy.NoteRestartAttempt(T(20));
            var hung = RecoveryAction.ProbeAgainAfterHungSpacing;
            for (var i = 0; i < 2; i++)
            {
                hung = policy.Decide(true, false, false, T(30 + i));
            }

            var kill = policy.Decide(true, false, false, T(40));
            return hung == RecoveryAction.ProbeAgainAfterHungSpacing
                && kill == RecoveryAction.TreeKillThenTerminal
                && policy.IsTerminal;
        });

        Supervision("process generation and connection epoch bump independently", () =>
        {
            var generations = new ServeGenerations();
            var process = generations.BumpProcessGeneration();
            var epochBefore = generations.ConnectionEpoch;
            var epoch = generations.BumpConnectionEpoch();
            return process == 1
                && epochBefore == 0
                && epoch == 1
                && generations.ProcessGeneration == 1
                && generations.IsCurrentProcess(1)
                && !generations.IsCurrentProcess(0)
                && ConnectionEpochGuard.Allows(1, generations.ConnectionEpoch)
                && !ConnectionEpochGuard.Allows(0, generations.ConnectionEpoch);
        });

        Supervision("an earlier epoch is refused for admission submit and clarify", () =>
        {
            var generations = new ServeGenerations();
            var stamped = generations.ConnectionEpoch;
            generations.BumpConnectionEpoch();
            var current = generations.ConnectionEpoch;
            return !ConnectionEpochGuard.Allows(stamped, current)
                && ConnectionEpochGuard.Allows(current, current);
        });

        Supervision("a socket-only loss bumps the epoch and not the process generation", () =>
        {
            var generations = new ServeGenerations();
            generations.BumpProcessGeneration();
            var order = new List<string>();
            var epoch = OutageGap.Apply(generations, new RecordingGap(order));
            return epoch == 1
                && generations.ProcessGeneration == 1
                && string.Join(",", order) == "invalidate,drop,stop,block";
        });

        Supervision("stale process generation is not current after the next spawn", () =>
        {
            var generations = new ServeGenerations();
            var first = generations.BumpProcessGeneration();
            var second = generations.BumpProcessGeneration();
            return first == 1 && second == 2 && !generations.IsCurrentProcess(first) && generations.IsCurrentProcess(second);
        });

        Supervision("parallel bumps land on the expected counts", () =>
        {
            var generations = new ServeGenerations();
            Parallel.For(0, 200, _ => generations.BumpProcessGeneration());
            Parallel.For(0, 200, _ => generations.BumpConnectionEpoch());
            return generations.ProcessGeneration == 200 && generations.ConnectionEpoch == 200;
        });

        Supervision("stderr acl failure does not write and logs once", () =>
        {
            var ok = StderrAcl.Evaluate(false, false, 0, 0);
            var inheritanceFailed = StderrAcl.Evaluate(false, false, 1, 0);
            var grantFailed = StderrAcl.Evaluate(false, false, 0, 5);
            var missing = StderrAcl.Evaluate(false, false, null, null);
            var again = StderrAcl.Evaluate(false, true, 1, 1);
            var held = StderrAcl.Evaluate(true, false, null, null);
            var line = SupervisionLog.Format(
                SupervisionConstants.ProcServe,
                SupervisionConstants.EventStderrAclFailed,
                0,
                0);
            return ok.MayWrite && ok.Applied && !ok.LogFailure
                && !inheritanceFailed.MayWrite && !inheritanceFailed.Applied && inheritanceFailed.LogFailure
                && !grantFailed.MayWrite && !grantFailed.Applied && grantFailed.LogFailure
                && !missing.MayWrite && !missing.Applied && missing.LogFailure
                && !again.MayWrite && !again.Applied && !again.LogFailure
                && held.MayWrite && held.Applied && !held.LogFailure
                && line == "supervisor proc=serve event=stderr_acl_failed restarts=0 generation=0";
        });

        Supervision("watcher log line uses its own process name", () =>
        {
            var serve = SupervisionLog.Format(SupervisionConstants.ProcServe, SupervisionConstants.EventRestart, 1, 2);
            var watcher = SupervisionLog.Format("watcher", SupervisionConstants.EventRestart, 1, 2);
            return serve == "supervisor proc=serve event=restart restarts=1 generation=2"
                && watcher == "supervisor proc=watcher event=restart restarts=1 generation=2";
        });

        Supervision("pre-loss capture on the new epoch is refused reason=cancelled", () =>
        {
            var generations = new ServeGenerations();
            var process = generations.BumpProcessGeneration();
            var lifecycle = new CaptureLifecycle();
            lifecycle.BeginStart(CaptureKind.Manual, null, T(0));
            lifecycle.ApplyStatus(CaptureConstants.StatusListening, T(1));
            var before = TranscriptAdmission.Decide(
                new TranscriptFacts(5, false, false),
                lifecycle.Snapshot(),
                turnRunning: false,
                clarifyRequestOpenForSession: false,
                gated: false,
                modeText: false,
                isEcho: false);
            OutageGap.Apply(generations, new CancelCaptureGap(lifecycle));
            var stamped = generations.ConnectionEpoch;
            var after = TranscriptAdmission.Decide(
                new TranscriptFacts(5, false, false),
                lifecycle.Snapshot(),
                turnRunning: false,
                clarifyRequestOpenForSession: false,
                gated: false,
                modeText: false,
                isEcho: false);
            return before is AdmissionVerdict.Admit
                && generations.ProcessGeneration == process
                && ConnectionEpochGuard.Allows(stamped, generations.ConnectionEpoch)
                && after is AdmissionVerdict.Drop drop
                && drop.Reason == AdmissionReasons.Cancelled;
        });

        Supervision("same-generation reconnect stops the recorder before wake", () =>
        {
            return RecordingLatch.StopRecordBeforeRearm(4, 4)
                && !RecordingLatch.StopRecordBeforeRearm(4, 5)
                && !RecordingLatch.StopRecordBeforeRearm(-1, 4);
        });

        Supervision("an outstanding capture does not clear the recording latch", () =>
        {
            return !RecordingLatch.ClearAfterSettledTick(
                hasOutstanding: true,
                hermesBusyUntilIdle: false,
                CaptureState.Accepting,
                captureActive: true,
                recorderIdle: false);
        });

        Supervision("HermesBusyUntilIdle does not clear the recording latch", () =>
        {
            return !RecordingLatch.ClearAfterSettledTick(
                hasOutstanding: false,
                hermesBusyUntilIdle: true,
                CaptureState.Settled,
                captureActive: true,
                recorderIdle: false);
        });

        Supervision("a settled outage with no idle clears the recording latch", () =>
        {
            var lifecycle = new CaptureLifecycle();
            lifecycle.BeginStart(CaptureKind.Wake, null, T(0));
            lifecycle.ApplyStatus(CaptureConstants.StatusListening, T(1));
            lifecycle.Cancel(SupervisionConstants.GapReason, T(2));
            var during = lifecycle.Snapshot();
            var held = !RecordingLatch.ClearAfterSettledTick(
                during.HasOutstanding,
                during.HermesBusyUntilIdle,
                during.State,
                captureActive: true,
                recorderIdle: false);
            lifecycle.Tick(T(2 + CaptureConstants.CancelSettleTimeoutSeconds + 1));
            var settled = lifecycle.Snapshot();
            var clear = RecordingLatch.ClearAfterSettledTick(
                settled.HasOutstanding,
                settled.HermesBusyUntilIdle,
                settled.State,
                captureActive: true,
                recorderIdle: false);
            return held
                && clear
                && settled.State == CaptureState.Settled
                && !settled.HasOutstanding;
        });

        Supervision("session not found falls back instead of a failed reconnect", () =>
        {
            return ResumeReconnect.IsUnstoredDraft("session not found")
                && !ResumeReconnect.CountsAsFailedReconnect("session not found");
        });

        Supervision("any other resume error counts as a failed reconnect", () =>
        {
            return ResumeReconnect.CountsAsFailedReconnect("db unavailable")
                && !ResumeReconnect.IsUnstoredDraft("db unavailable")
                && ResumeReconnect.CountsAsFailedReconnect(null)
                && ResumeReconnect.CountsAsFailedReconnect("");
        });

        Supervision("new-generation restart with TTS on before the gap ends voice on + TTS on", () =>
        {
            var statuses = new[]
            {
                new TtsRestore.Snapshot(false, false),
                new TtsRestore.Snapshot(true, false),
                new TtsRestore.Snapshot(true, true),
            };
            var result = TtsRestore.Replay(false, true, statuses);
            var enable = ActionIndex(result.Actions, TtsRestore.Action.EnableVoice);
            var set = ActionIndex(result.Actions, TtsRestore.Action.SetTts);
            return result.VoiceOn
                && result.Tts == true
                && enable >= 0
                && set > enable
                && !result.Actions.Contains(TtsRestore.Action.StopLeftoverAudio)
                && TtsSwitchFollowsVoiceOn(result, statuses);
        });

        Supervision("new-generation restart with TTS off before the gap ends TTS off", () =>
        {
            var result = TtsRestore.Replay(
                false,
                false,
                new[]
                {
                    new TtsRestore.Snapshot(false, false),
                    new TtsRestore.Snapshot(true, false),
                });
            return result.VoiceOn
                && result.Tts == false
                && ActionIndex(result.Actions, TtsRestore.Action.EnableVoice) >= 0
                && !result.Actions.Contains(TtsRestore.Action.SetTts);
        });

        Supervision("socket-only reconnect stops leftover audio then restores", () =>
        {
            var statuses = new[]
            {
                new TtsRestore.Snapshot(true, true),
                new TtsRestore.Snapshot(true, false),
                new TtsRestore.Snapshot(true, true),
            };
            var result = TtsRestore.Replay(true, true, statuses);
            var stop = ActionIndex(result.Actions, TtsRestore.Action.StopLeftoverAudio);
            var set = ActionIndex(result.Actions, TtsRestore.Action.SetTts);
            return stop >= 0
                && set > stop
                && result.VoiceOn
                && result.Tts == true
                && TtsSwitchFollowsVoiceOn(result, statuses);
        });

        Supervision("a TTS switch sent before voice is on is never part of the sequence", () =>
        {
            var fresh = new[]
            {
                new TtsRestore.Snapshot(false, false),
                new TtsRestore.Snapshot(true, false),
                new TtsRestore.Snapshot(true, true),
            };
            var socket = new[]
            {
                new TtsRestore.Snapshot(false, true),
                new TtsRestore.Snapshot(true, true),
                new TtsRestore.Snapshot(true, false),
                new TtsRestore.Snapshot(true, true),
            };
            var freshResult = TtsRestore.Replay(false, true, fresh);
            var socketResult = TtsRestore.Replay(true, true, socket);
            return TtsSwitchFollowsVoiceOn(freshResult, fresh)
                && TtsSwitchFollowsVoiceOn(socketResult, socket)
                && ActionIndex(socketResult.Actions, TtsRestore.Action.StopLeftoverAudio)
                    < ActionIndex(socketResult.Actions, TtsRestore.Action.SetTts);
        });

        Supervision("a mismatch logs and retries once", () =>
        {
            var recovered = TtsRestore.Replay(
                false,
                true,
                new[]
                {
                    new TtsRestore.Snapshot(true, false),
                    new TtsRestore.Snapshot(true, false),
                    new TtsRestore.Snapshot(true, true),
                });
            var stuck = TtsRestore.Replay(
                false,
                true,
                new[]
                {
                    new TtsRestore.Snapshot(true, false),
                    new TtsRestore.Snapshot(true, false),
                    new TtsRestore.Snapshot(true, false),
                });
            var line = SupervisionLog.Format(
                SupervisionConstants.ProcServe,
                SupervisionConstants.EventTtsRestoreMismatch,
                0,
                0);
            return ActionCount(recovered.Actions, TtsRestore.Action.SetTts) == 2
                && ActionCount(recovered.Actions, TtsRestore.Action.LogMismatch) == TtsRestore.MismatchRetryLimit
                && ActionCount(recovered.Actions, TtsRestore.Action.LogSecondMismatch) == 0
                && recovered.Tts == true
                && ActionCount(stuck.Actions, TtsRestore.Action.SetTts) == 2
                && ActionCount(stuck.Actions, TtsRestore.Action.LogMismatch) == TtsRestore.MismatchRetryLimit
                && ActionCount(stuck.Actions, TtsRestore.Action.LogSecondMismatch) == TtsRestore.MismatchRetryLimit
                && stuck.Actions[stuck.Actions.Count - 1] == TtsRestore.Action.LogSecondMismatch
                && line == "supervisor proc=serve event=tts_restore_mismatch restarts=0 generation=0";
        });

        Supervision("stderr rotates at the byte cap and retention uses the named day count", () =>
        {
            var now = T(0);
            var fresh = now.AddDays(-13);
            var expired = now.AddDays(-14);
            return !SupervisionConstants.StderrShouldRotate(SupervisionConstants.ServeStderrMaxBytes - 1)
                && SupervisionConstants.StderrShouldRotate(SupervisionConstants.ServeStderrMaxBytes)
                && !SupervisionConstants.RetentionExpired(fresh, now, SupervisionConstants.DumpRetentionDays)
                && SupervisionConstants.RetentionExpired(expired, now, SupervisionConstants.ServeStderrRetentionDays);
        });
    }

    private static int ActionIndex(IReadOnlyList<TtsRestore.Action> actions, TtsRestore.Action action)
    {
        for (var i = 0; i < actions.Count; i++)
        {
            if (actions[i] == action)
            {
                return i;
            }
        }

        return -1;
    }

    private static int ActionCount(IReadOnlyList<TtsRestore.Action> actions, TtsRestore.Action action)
    {
        var count = 0;
        for (var i = 0; i < actions.Count; i++)
        {
            if (actions[i] == action)
            {
                count++;
            }
        }

        return count;
    }

    private static bool TtsSwitchFollowsVoiceOn(TtsRestore.Result result, IReadOnlyList<TtsRestore.Snapshot> statuses)
    {
        if (result.TtsSwitchBeforeVoiceOn)
        {
            return false;
        }

        var voiceOn = false;
        var index = 0;
        foreach (var action in result.Actions)
        {
            if (action == TtsRestore.Action.SetTts && !voiceOn)
            {
                return false;
            }

            if (action != TtsRestore.Action.ReadStatus)
            {
                continue;
            }

            if (index < statuses.Count && statuses[index].VoiceOn)
            {
                voiceOn = true;
            }

            index++;
        }

        return true;
    }

    private void Supervision(string name, Func<bool> body)
    {
        _supervisionTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _supervisionPassed++;
            }
        });
    }

    private sealed class RecordingGap : IOutageGap
    {
        private readonly List<string> _order;

        public RecordingGap(List<string> order)
        {
            _order = order;
        }

        public void InvalidateCapture() => _order.Add("invalidate");

        public void DropPendingTranscript() => _order.Add("drop");

        public void StopPlayback() => _order.Add("stop");

        public void BlockInput() => _order.Add("block");
    }

    private sealed class CancelCaptureGap : IOutageGap
    {
        private readonly CaptureLifecycle _lifecycle;

        public CancelCaptureGap(CaptureLifecycle lifecycle)
        {
            _lifecycle = lifecycle;
        }

        public void InvalidateCapture() => _lifecycle.Cancel(SupervisionConstants.GapReason, T(2));

        public void DropPendingTranscript()
        {
        }

        public void StopPlayback()
        {
        }

        public void BlockInput()
        {
        }
    }
}
