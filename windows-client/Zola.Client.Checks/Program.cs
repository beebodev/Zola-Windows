using Zola.Client.Voice;

// P7-VOICEAUTH: exhaustive table checks for lifecycle + admission — P7-D01 / P7-D03

var runner = new CheckRunner();
runner.RunAll();
Console.WriteLine(runner.CoverageLine());
Environment.Exit(runner.Failed > 0 ? 1 : 0);

internal sealed class CheckRunner
{
    private int _lifecycleTotal;
    private int _lifecyclePassed;
    private int _admissionTotal;
    private int _admissionPassed;
    private int _startTotal;
    private int _startPassed;
    private int _invalidTotal;
    private int _invalidPassed;
    private int _stopPhraseTotal;
    private int _stopPhrasePassed;
    private int _amendmentTotal;
    private int _amendmentPassed;
    private int _latchTotal;
    private int _latchPassed;
    private int _wiringTotal;
    private int _wiringPassed;
    private int _clarifyTotal;
    private int _clarifyPassed;
    private int _timingTotal;
    private int _timingPassed;

    public int Failed { get; private set; }

    public void RunAll()
    {
        RunLifecycleRows();
        RunAdmissionRows();
        RunStartRows();
        RunInvalidPairs();
        RunStopPhraseRows();
        RunAmendmentRows();
        RunLatchRows();
        RunPlanExtras();
        RunWiringRows();
        RunClarifyRows();
        RunTimingRows();
    }

    public string CoverageLine()
    {
        return string.Format(
            "coverage: lifecycle rows {0}/{1}, admission rows {2}/{3}, start rows {4}/{5}, invalid pairs {6}/{7}, stop_phrase rows {8}/{9}, amendments {10}/{11}, latch rows {12}/{13}, wiring rows {14}/{15}, clarify rows {16}/{17}, timing rows {18}/{19}",
            _lifecyclePassed,
            _lifecycleTotal,
            _admissionPassed,
            _admissionTotal,
            _startPassed,
            _startTotal,
            _invalidPassed,
            _invalidTotal,
            _stopPhrasePassed,
            _stopPhraseTotal,
            _amendmentPassed,
            _amendmentTotal,
            _latchPassed,
            _latchTotal,
            _wiringPassed,
            _wiringTotal,
            _clarifyPassed,
            _clarifyTotal,
            _timingPassed,
            _timingTotal);
    }

    private void RunLifecycleRows()
    {
        // Starting × events
        Lifecycle("Starting+listening→Accepting", lc =>
        {
            var t0 = T(0);
            lc.BeginStart(CaptureKind.Manual, null, t0);
            var r = lc.ApplyStatus(CaptureConstants.StatusListening, T(1));
            return r.Snapshot.State == CaptureState.Accepting && r.Snapshot.HasOutstanding;
        });

        Lifecycle("Starting+transcribing→Starting", lc =>
        {
            lc.BeginStart(CaptureKind.Wake, null, T(0));
            var r = lc.ApplyStatus(CaptureConstants.StatusTranscribing, T(1));
            return r.Snapshot.State == CaptureState.Starting;
        });

        Lifecycle("Starting+idle→stay_Starting", lc =>
        {
            lc.BeginStart(CaptureKind.Wake, null, T(0));
            var r = lc.ApplyStatus(CaptureConstants.StatusIdle, T(1));
            return r.Snapshot.HasOutstanding
                && r.Snapshot.State == CaptureState.Starting
                && !r.Snapshot.HermesBusyUntilIdle;
        });

        Lifecycle("Starting+cancel→Settled_unsent", lc =>
        {
            // Unsent Starting cancel settles immediately (no Cancelled/30s/stop).
            lc.BeginStart(CaptureKind.FollowUp, null, T(0));
            var r = lc.Cancel("typed-submit", T(1));
            return !r.Snapshot.HasOutstanding
                && r.Snapshot.State == CaptureState.Settled
                && !r.NeedsHermesStop
                && !r.Snapshot.HermesBusyUntilIdle;
        });

        Lifecycle("Starting+late_tick→listening_timeout_first", lc =>
        {
            // Listening deadline (3s) outranks recover (180s) while still Starting (unsent → Settled).
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            var r = lc.Tick(T(0).AddSeconds(CaptureConstants.CaptureSettleTimeoutSeconds));
            return !r.Snapshot.HasOutstanding
                && r.Snapshot.State == CaptureState.Settled
                && r.NeedsHermesStop
                && r.LogLine != null
                && r.LogLine.Contains(CaptureConstants.SignalStartNoListening, StringComparison.Ordinal);
        });

        Lifecycle("Starting+start_busy→Settled", lc =>
        {
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            var r = lc.NoteStartRpcFailed(busy: true, T(1));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Starting+transcript→Settled_failclosed", lc =>
        {
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            var r = lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(1));
            return !r.Snapshot.HasOutstanding;
        });

        // Accepting × events
        Lifecycle("Accepting+transcript_text→Settled", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var r = lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Accepting+stop_phrase→Settled", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var r = lc.ApplyTranscript(LifecycleSignal.TranscriptStopPhrase, T(2));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Accepting+no_speech→Settled", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            var r = lc.ApplyTranscript(LifecycleSignal.TranscriptNoSpeechLimit, T(2));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Accepting+idle→Settled", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            var r = lc.ApplyStatus(CaptureConstants.StatusIdle, T(2));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Accepting+cancel→Cancelled", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var r = lc.Cancel("typed-submit", T(2));
            return r.Snapshot.State == CaptureState.Cancelled && r.NeedsHermesStop;
        });

        Lifecycle("Accepting+recover_timeout→Settled", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            var r = lc.Tick(T(1).AddSeconds(CaptureConstants.CaptureSettleTimeoutSeconds));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Accepting+transcribing→Accepting", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            var r = lc.ApplyStatus(CaptureConstants.StatusTranscribing, T(2));
            return r.Snapshot.State == CaptureState.Accepting;
        });

        Lifecycle("Accepting+speak_text_pause→Accepting", lc =>
        {
            Accepting(lc, CaptureKind.Clarify, "srq-synth-1");
            var r = lc.NoteSpeakTextPauseResume(T(2));
            return r.Snapshot.State == CaptureState.Accepting && r.Snapshot.HasOutstanding;
        });

        // Cancelled × events
        Lifecycle("Cancelled+transcript→Settled", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            lc.Cancel("typed-submit", T(2));
            var r = lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(3));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Cancelled+idle→Settled", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            lc.Cancel("typed-submit", T(2));
            var r = lc.ApplyStatus(CaptureConstants.StatusIdle, T(3));
            return !r.Snapshot.HasOutstanding;
        });

        Lifecycle("Cancelled+recover_timeout→Settled", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            lc.Cancel("session-ready", T(2));
            var r = lc.Tick(T(2).AddSeconds(CaptureConstants.CancelSettleTimeoutSeconds));
            return !r.Snapshot.HasOutstanding;
        });

        // Settled × events
        Lifecycle("Settled+late_transcript→Settled", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            var before = lc.Snapshot();
            var r = lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(3));
            return !r.Snapshot.HasOutstanding && before.Generation == r.Snapshot.Generation;
        });

        Lifecycle("Settled+idle→Settled", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.ApplyStatus(CaptureConstants.StatusIdle, T(2));
            var r = lc.ApplyStatus(CaptureConstants.StatusIdle, T(3));
            return !r.Snapshot.HasOutstanding;
        });
    }

    private void RunAdmissionRows()
    {
        Admission("gated→drop", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.Manual);
            var v = TranscriptAdmission.Decide(Facts(4), snap, false, false, gated: true, modeText: false, isEcho: false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.Gated };
        });

        Admission("mode_text→drop", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.Manual);
            var v = TranscriptAdmission.Decide(Facts(4), snap, false, false, false, modeText: true, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.ModeText };
        });

        Admission("no_owner→drop", () =>
        {
            var snap = new CaptureSnapshot(0, CaptureKind.Manual, null, CaptureState.Settled, null, null, false, false);
            var v = TranscriptAdmission.Decide(Facts(4), snap, false, false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.NoOwner };
        });

        Admission("cancelled→drop", () =>
        {
            var snap = new CaptureSnapshot(3, CaptureKind.FollowUp, null, CaptureState.Cancelled, T(0), null, true, true);
            var v = TranscriptAdmission.Decide(Facts(8), snap, false, false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.Cancelled };
        });

        Admission("settled→drop", () =>
        {
            var snap = new CaptureSnapshot(3, CaptureKind.FollowUp, null, CaptureState.Settled, T(0), T(1), true, false);
            var v = TranscriptAdmission.Decide(Facts(8), snap, false, false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.Settled };
        });

        Admission("starting→drop_no_owner", () =>
        {
            var snap = new CaptureSnapshot(2, CaptureKind.Wake, null, CaptureState.Starting, T(0), null, true, false);
            var v = TranscriptAdmission.Decide(Facts(5), snap, false, false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.NoOwner };
        });

        Admission("accepting_followup→admit", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.FollowUp);
            var v = TranscriptAdmission.Decide(Facts(6), snap, turnRunning: false, false, false, false, false);
            return v is AdmissionVerdict.Admit { Kind: CaptureKind.FollowUp };
        });

        Admission("turn_running_unbound→drop", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.Wake);
            var v = TranscriptAdmission.Decide(Facts(6), snap, turnRunning: true, false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.TurnRunningUnbound };
        });

        Admission("clarify_open_while_turn→admit", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.Clarify, "srq-synth-2");
            var v = TranscriptAdmission.Decide(Facts(3), snap, turnRunning: true, clarifyRequestOpenForSession: true, false, false, false);
            return v is AdmissionVerdict.Admit { Kind: CaptureKind.Clarify, ClarifyId: "srq-synth-2" };
        });

        Admission("clarify_closed→drop", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.Clarify, "srq-synth-3");
            var v = TranscriptAdmission.Decide(Facts(3), snap, turnRunning: true, clarifyRequestOpenForSession: false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.ClarifyNotActive };
        });

        Admission("echo_last_rejects", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.FollowUp);
            var v = TranscriptAdmission.Decide(Facts(7), snap, false, false, false, false, isEcho: true);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.Echo };
        });

        Admission("echo_cannot_admit", () =>
        {
            var snap = new CaptureSnapshot(0, CaptureKind.Manual, null, CaptureState.Settled, null, null, false, false);
            var v = TranscriptAdmission.Decide(Facts(7), snap, false, false, false, false, isEcho: true);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.NoOwner };
        });

        Admission("kinds_wake_manual_echoreopen_admit", () =>
        {
            foreach (var kind in new[] { CaptureKind.Wake, CaptureKind.Manual, CaptureKind.EchoReopen })
            {
                var snap = AcceptingSnapshot(kind);
                var v = TranscriptAdmission.Decide(Facts(2), snap, false, false, false, false, false);
                if (v is not AdmissionVerdict.Admit a || a.Kind != kind)
                {
                    return false;
                }
            }

            return true;
        });
    }

    private void RunStartRows()
    {
        Start("wake_while_accepting→reject", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var r = lc.BeginStart(CaptureKind.Wake, null, T(2));
            return r.Disposition == StartDisposition.Rejected && lc.Snapshot().State == CaptureState.Accepting;
        });

        Start("manual_while_accepting→reject", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var r = lc.BeginStart(CaptureKind.Manual, null, T(2));
            return r.Disposition == StartDisposition.Rejected;
        });

        Start("followup_while_accepting→defer", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            var r = lc.BeginStart(CaptureKind.FollowUp, null, T(2));
            return r.Disposition == StartDisposition.Deferred && r.Pending is not null;
        });

        Start("echoreopen_while_accepting→defer", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var r = lc.BeginStart(CaptureKind.EchoReopen, null, T(2));
            return r.Disposition == StartDisposition.Deferred;
        });

        Start("clarify_while_accepting→supersede_defer", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var r = lc.BeginStart(CaptureKind.Clarify, "srq-synth-4", T(2));
            return r.Disposition == StartDisposition.SupersededAndDeferred
                && r.NeedsHermesStop
                && r.Snapshot.State == CaptureState.Cancelled
                && r.Pending is { Kind: CaptureKind.Clarify };
        });

        Start("deferred_followup_releases_after_settle", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2));
            lc.ApplyStatus(CaptureConstants.StatusIdle, T(3));
            var released = lc.TryReleasePending(T(4));
            return released.Disposition == StartDisposition.Began
                && released.Snapshot.State == CaptureState.Starting
                && released.Snapshot.Kind == CaptureKind.FollowUp;
        });

        Start("deferred_followup_expires", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2));
            lc.ApplyStatus(CaptureConstants.StatusIdle, T(3));
            var tick = lc.Tick(T(2).AddSeconds(CaptureConstants.PendingStartExpirySeconds + 0.1));
            var released = lc.TryReleasePending(T(2).AddSeconds(CaptureConstants.PendingStartExpirySeconds + 1));
            return tick.LogLine != null
                && tick.LogLine.Contains("start_expired", StringComparison.Ordinal)
                && released.Disposition == StartDisposition.Rejected
                && lc.Pending is null;
        });

        Start("at_most_one_pending", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2));
            lc.BeginStart(CaptureKind.EchoReopen, null, T(3));
            return lc.Pending is { Kind: CaptureKind.EchoReopen };
        });

        Start("fresh_start_when_settled", lc =>
        {
            var r = lc.BeginStart(CaptureKind.Wake, null, T(0));
            return r.Disposition == StartDisposition.Began && r.Snapshot.State == CaptureState.Starting;
        });
    }

    private void RunInvalidPairs()
    {
        Invalid("listening_while_accepting_no_transition", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            var before = lc.Snapshot();
            var r = lc.ApplyStatus(CaptureConstants.StatusListening, T(2));
            return r.Snapshot.State == before.State && r.Snapshot.Generation == before.Generation;
        });

        Invalid("listening_while_settled_no_accepting", lc =>
        {
            var r = lc.ApplyStatus(CaptureConstants.StatusListening, T(0));
            return !r.Snapshot.HasOutstanding && r.Snapshot.State != CaptureState.Accepting;
        });

        Invalid("unknown_status_no_accepting", lc =>
        {
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            var r = lc.ApplyStatus("recording", T(1));
            return r.Snapshot.State == CaptureState.Starting;
        });

        Invalid("cancel_when_settled_noop", lc =>
        {
            var r = lc.Cancel("typed-submit", T(0));
            return !r.NeedsHermesStop && !r.Snapshot.HasOutstanding;
        });

        Invalid("speak_text_while_starting_ignored", lc =>
        {
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            var r = lc.NoteSpeakTextPauseResume(T(1));
            return r.Snapshot.State == CaptureState.Starting;
        });

        Invalid("two_accepting_impossible", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            var r = lc.BeginStart(CaptureKind.Manual, null, T(2));
            return r.Disposition == StartDisposition.Rejected && CountAccepting(lc) <= 1;
        });
    }

    private void RunStopPhraseRows()
    {
        StopPhrase("admitted_stop_is_admit", () =>
        {
            var snap = AcceptingSnapshot(CaptureKind.FollowUp);
            var v = TranscriptAdmission.Decide(
                new TranscriptFacts(4, isStopPhrase: true, isNoSpeechLimit: false),
                snap,
                false,
                false,
                false,
                false,
                false);
            // Stop flag must not influence admission — still Admit.
            return v is AdmissionVerdict.Admit;
        });

        StopPhrase("inadmissible_cancelled_stop_is_drop", () =>
        {
            var snap = new CaptureSnapshot(9, CaptureKind.FollowUp, null, CaptureState.Cancelled, T(0), null, true, true);
            var v = TranscriptAdmission.Decide(
                new TranscriptFacts(4, isStopPhrase: true, false),
                snap,
                false,
                false,
                false,
                false,
                false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.Cancelled };
        });

        StopPhrase("inadmissible_no_owner_stop_is_drop", () =>
        {
            var snap = new CaptureSnapshot(0, CaptureKind.Manual, null, CaptureState.Settled, null, null, false, false);
            var v = TranscriptAdmission.Decide(
                new TranscriptFacts(4, isStopPhrase: true, false),
                snap,
                false,
                false,
                false,
                false,
                false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.NoOwner };
        });

        StopPhrase("restore_format_constant", () =>
        {
            var line = string.Format(AdmissionLog.StopPhraseRestoreFormat, AdmissionReasons.Cancelled);
            return line.Contains("stop_phrase restore inadmissible", StringComparison.Ordinal)
                && !line.Contains("VoiceChatEnded", StringComparison.Ordinal);
        });
    }

    private void RunAmendmentRows()
    {
        // Amendment 1: Starting→Accepting only on listening; StartListeningTimeout
        Amendment("A1_only_listening_accepts", lc =>
        {
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            lc.ApplyStatus(CaptureConstants.StatusTranscribing, T(1));
            if (lc.Snapshot().State == CaptureState.Accepting)
            {
                return false;
            }

            lc.ApplyStatus(CaptureConstants.StatusListening, T(2));
            return lc.Snapshot().State == CaptureState.Accepting;
        });

        Amendment("A1_start_listening_timeout_cancel", lc =>
        {
            lc.BeginStart(CaptureKind.Wake, null, T(0));
            var r = lc.Tick(T(0).AddSeconds(CaptureConstants.StartListeningTimeoutSeconds));
            return r.NeedsHermesStop
                && !r.Snapshot.HasOutstanding
                && r.Snapshot.State == CaptureState.Settled
                && r.LogLine != null
                && r.LogLine.Contains(CaptureConstants.SignalStartNoListening, StringComparison.Ordinal);
        });

        Amendment("A1_timeout_wake_rejected_after_idle", lc =>
        {
            lc.BeginStart(CaptureKind.Wake, null, T(0));
            lc.Tick(T(0).AddSeconds(CaptureConstants.StartListeningTimeoutSeconds));
            var idle = lc.ApplyStatus(CaptureConstants.StatusIdle, T(4));
            return idle.StartRejectedAfterNoListening && lc.Pending is null;
        });

        Amendment("A1_timeout_followup_stays_deferred", lc =>
        {
            lc.BeginStart(CaptureKind.FollowUp, null, T(0));
            lc.Tick(T(0).AddSeconds(CaptureConstants.StartListeningTimeoutSeconds));
            var idle = lc.ApplyStatus(CaptureConstants.StatusIdle, T(4));
            return !idle.StartRejectedAfterNoListening
                && idle.ReleasePendingNow
                && lc.Pending is { Kind: CaptureKind.FollowUp };
        });

        // Amendment 2: recover_timeout → next Accepting only via listening (no LateTranscriptGuard)
        Amendment("A2_recover_then_listening_accepts", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.Tick(T(1).AddSeconds(CaptureConstants.CaptureSettleTimeoutSeconds));
            if (lc.Snapshot().HasOutstanding)
            {
                return false;
            }

            lc.BeginStart(CaptureKind.Wake, null, T(200));
            if (lc.Snapshot().State == CaptureState.Accepting)
            {
                return false;
            }

            lc.ApplyStatus(CaptureConstants.StatusListening, T(201));
            return lc.Snapshot().State == CaptureState.Accepting;
        });

        Amendment("A2_no_late_guard_constant", () =>
        {
            // LateTranscriptGuardSeconds must not exist on CaptureConstants.
            var names = typeof(CaptureConstants)
                .GetFields(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static)
                .Select(f => f.Name)
                .ToHashSet(StringComparer.Ordinal);
            return !names.Contains("LateTranscriptGuardSeconds")
                && names.Contains(nameof(CaptureConstants.CaptureSettleTimeoutSeconds));
        });

        // Amendment 3: voice.tts / speak_text pause-resume keeps Accepting
        Amendment("A3_speak_text_keeps_accepting", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            lc.NoteSpeakTextPauseResume(T(2));
            lc.NoteSpeakTextPauseResume(T(3));
            return lc.Snapshot().State == CaptureState.Accepting && lc.Snapshot().HasOutstanding;
        });
    }

    private void RunLatchRows()
    {
        // Repro 1: Clarify deferred behind a capture that ends in a transcript, then idle releases.
        Latch("repro_clarify_deferred_released_after_transcript_idle", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            var defer = lc.BeginStart(CaptureKind.Clarify, "srq-synth-repro1", T(2));
            if (defer.Disposition != StartDisposition.SupersededAndDeferred || defer.Pending is null)
            {
                return false;
            }

            var forced = lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(3));
            if (forced.ReleasePendingNow || !forced.Snapshot.HermesBusyUntilIdle || forced.Snapshot.HasOutstanding)
            {
                return false;
            }

            var idle = lc.ApplyStatus(CaptureConstants.StatusIdle, T(4));
            if (!idle.ReleasePendingNow || idle.Snapshot.HermesBusyUntilIdle || lc.Pending is null)
            {
                return false;
            }

            var released = lc.TryReleasePending(T(5));
            return released.Disposition == StartDisposition.Began
                && released.Snapshot.Kind == CaptureKind.Clarify
                && released.Snapshot.State == CaptureState.Starting;
        });

        // Repro 2: EchoReopen while latch held must defer; idle releases it (not force-settle a Began start).
        Latch("repro_echoreopen_deferred_while_latched", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            if (!lc.Snapshot().HermesBusyUntilIdle || lc.Snapshot().HasOutstanding)
            {
                return false;
            }

            var echo = lc.BeginStart(CaptureKind.EchoReopen, null, T(3));
            if (echo.Disposition != StartDisposition.Deferred || echo.Pending is null)
            {
                return false;
            }

            var idle = lc.ApplyStatus(CaptureConstants.StatusIdle, T(4));
            if (!idle.ReleasePendingNow || idle.Snapshot.HermesBusyUntilIdle)
            {
                return false;
            }

            var released = lc.TryReleasePending(T(5));
            return released.Disposition == StartDisposition.Began
                && released.Snapshot.Kind == CaptureKind.EchoReopen
                && released.Snapshot.State == CaptureState.Starting;
        });

        Latch("latch_set_on_listening", lc =>
        {
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            if (lc.Snapshot().HermesBusyUntilIdle)
            {
                return false;
            }

            lc.ApplyStatus(CaptureConstants.StatusListening, T(1));
            return lc.Snapshot().HermesBusyUntilIdle && lc.Snapshot().State == CaptureState.Accepting;
        });

        Latch("latch_cleared_on_idle", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            if (!lc.Snapshot().HermesBusyUntilIdle)
            {
                return false;
            }

            lc.ApplyStatus(CaptureConstants.StatusIdle, T(2));
            return !lc.Snapshot().HermesBusyUntilIdle && !lc.Snapshot().HasOutstanding;
        });

        Latch("recover_clears_latch", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            var r = lc.Tick(T(1).AddSeconds(CaptureConstants.CaptureSettleTimeoutSeconds));
            return !r.Snapshot.HermesBusyUntilIdle && !r.Snapshot.HasOutstanding;
        });

        Latch("idle_in_Starting_ignored", lc =>
        {
            lc.BeginStart(CaptureKind.FollowUp, null, T(0));
            var r = lc.ApplyStatus(CaptureConstants.StatusIdle, T(1));
            return r.Snapshot.State == CaptureState.Starting
                && r.Snapshot.HasOutstanding
                && !r.ReleasePendingNow;
        });

        Latch("start_while_latched_wake_reject", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            var r = lc.BeginStart(CaptureKind.Wake, null, T(3));
            return r.Disposition == StartDisposition.Rejected && lc.Snapshot().HermesBusyUntilIdle;
        });

        Latch("start_while_latched_followup_defer", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            var r = lc.BeginStart(CaptureKind.FollowUp, null, T(3));
            return r.Disposition == StartDisposition.Deferred && r.Pending is { Kind: CaptureKind.FollowUp };
        });

        Latch("start_while_latched_clarify_defer_only", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            var r = lc.BeginStart(CaptureKind.Clarify, "srq-synth-latch", T(3));
            return r.Disposition == StartDisposition.Deferred
                && !r.NeedsHermesStop
                && r.Pending is { Kind: CaptureKind.Clarify };
        });

        Latch("pending_released_on_idle_after_transcript_settle", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2));
            var tr = lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(3));
            if (tr.ReleasePendingNow)
            {
                return false;
            }

            var idle = lc.ApplyStatus(CaptureConstants.StatusIdle, T(4));
            return idle.ReleasePendingNow && lc.Pending is { Kind: CaptureKind.FollowUp };
        });

        Latch("release_revalidates_expired_pending_not_started", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2));
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(3));
            var idle = lc.ApplyStatus(CaptureConstants.StatusIdle, T(4));
            if (!idle.ReleasePendingNow)
            {
                return false;
            }

            var expiredAt = T(2).AddSeconds(CaptureConstants.PendingStartExpirySeconds + 0.1);
            var released = lc.TryReleasePending(expiredAt);
            return released.Disposition == StartDisposition.Rejected
                && released.LogLine != null
                && released.LogLine.Contains("start_expired", StringComparison.Ordinal)
                && !released.Snapshot.HasOutstanding
                && lc.Pending is null;
        });

        // Stuck-latch liveness: lost idle after transcript-settle must recover at +65 s.
        Latch("repro_stuck_latch_recovers_at_65s", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            var cancel = lc.Cancel("session-ready", T(3));
            if (cancel.NeedsHermesStop || !lc.Snapshot().HermesBusyUntilIdle)
            {
                return false;
            }

            var early = lc.BeginStart(CaptureKind.Wake, null, T(4));
            if (early.Disposition != StartDisposition.Rejected)
            {
                return false;
            }

            var stillStuck = lc.Tick(T(2).AddSeconds(CaptureConstants.LatchIdleTimeoutSeconds - 1));
            if (!stillStuck.Snapshot.HermesBusyUntilIdle)
            {
                return false;
            }

            var recovered = lc.Tick(T(2).AddSeconds(CaptureConstants.LatchIdleTimeoutSeconds));
            if (recovered.Snapshot.HermesBusyUntilIdle
                || recovered.LogLine == null
                || !recovered.LogLine.Contains(CaptureConstants.LogLatchRecover, StringComparison.Ordinal))
            {
                return false;
            }

            var wake = lc.BeginStart(CaptureKind.Wake, null, T(70));
            return wake.Disposition == StartDisposition.Began
                && wake.Snapshot.State == CaptureState.Starting;
        });

        Latch("latch_recover_releases_pending", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            lc.BeginStart(CaptureKind.FollowUp, null, T(3));
            var recovered = lc.Tick(T(2).AddSeconds(CaptureConstants.LatchIdleTimeoutSeconds));
            return recovered.ReleasePendingNow
                && !recovered.Snapshot.HermesBusyUntilIdle
                && lc.Pending is { Kind: CaptureKind.FollowUp };
        });

        Latch("late_idle_after_latch_recover_noop", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            lc.Tick(T(2).AddSeconds(CaptureConstants.LatchIdleTimeoutSeconds));
            lc.BeginStart(CaptureKind.Manual, null, T(70));
            var before = lc.Snapshot();
            var idle = lc.ApplyStatus(CaptureConstants.StatusIdle, T(71));
            return idle.Snapshot.State == CaptureState.Starting
                && idle.Snapshot.Generation == before.Generation
                && !idle.ReleasePendingNow;
        });

        Latch("cancelled_no_idle_settles_at_30s", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            lc.Cancel("typed-submit", T(2));
            var early = lc.Tick(T(2).AddSeconds(CaptureConstants.CancelSettleTimeoutSeconds - 1));
            if (!early.Snapshot.HasOutstanding || early.Snapshot.State != CaptureState.Cancelled)
            {
                return false;
            }

            var settled = lc.Tick(T(2).AddSeconds(CaptureConstants.CancelSettleTimeoutSeconds));
            return !settled.Snapshot.HasOutstanding
                && settled.LogLine != null
                && settled.LogLine.Contains(CaptureConstants.SignalRecoverTimeout, StringComparison.Ordinal);
        });

        Latch("accepting_still_uses_180s", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            var at30 = lc.Tick(T(1).AddSeconds(CaptureConstants.CancelSettleTimeoutSeconds));
            if (!at30.Snapshot.HasOutstanding || at30.Snapshot.State != CaptureState.Accepting)
            {
                return false;
            }

            var at179 = lc.Tick(T(1).AddSeconds(CaptureConstants.CaptureSettleTimeoutSeconds - 1));
            if (!at179.Snapshot.HasOutstanding)
            {
                return false;
            }

            var at180 = lc.Tick(T(1).AddSeconds(CaptureConstants.CaptureSettleTimeoutSeconds));
            return !at180.Snapshot.HasOutstanding;
        });

        Latch("transcript_before_listening_after_latch_recover_dropped", lc =>
        {
            Accepting(lc, CaptureKind.Wake);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            lc.Tick(T(2).AddSeconds(CaptureConstants.LatchIdleTimeoutSeconds));
            lc.BeginStart(CaptureKind.Manual, null, T(70));
            var snap = lc.Snapshot();
            var v = TranscriptAdmission.Decide(Facts(9), snap, false, false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.NoOwner }
                && snap.State == CaptureState.Starting;
        });

        Latch("transcript_before_listening_after_cancel_recover_dropped", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            lc.Cancel("typed-submit", T(2));
            lc.Tick(T(2).AddSeconds(CaptureConstants.CancelSettleTimeoutSeconds));
            lc.BeginStart(CaptureKind.Wake, null, T(40));
            var snap = lc.Snapshot();
            var v = TranscriptAdmission.Decide(Facts(9), snap, false, false, false, false, false);
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.NoOwner }
                && snap.State == CaptureState.Starting;
        });
    }

    private void RunPlanExtras()
    {
        Lifecycle("cancel_then_forced_transcript_not_accepting", lc =>
        {
            Accepting(lc, CaptureKind.FollowUp);
            lc.Cancel("typed-submit", T(2));
            var snap = lc.Snapshot();
            var v = TranscriptAdmission.Decide(Facts(12), snap, false, false, false, false, false);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(3));
            return v is AdmissionVerdict.Drop { Reason: AdmissionReasons.Cancelled }
                && !lc.Snapshot().HasOutstanding;
        });

        Lifecycle("stop_nothing_then_next_admits", lc =>
        {
            // Settled, cancel noop, then genuine capture admits.
            lc.Cancel("typed-submit", T(0));
            Accepting(lc, CaptureKind.Manual);
            var v = TranscriptAdmission.Decide(Facts(5), lc.Snapshot(), false, false, false, false, false);
            return v is AdmissionVerdict.Admit;
        });
    }

    private void RunWiringRows()
    {
        // Phase 5 STOP wiring fixes: DiscardPending, Cancel pending policy, deferral generation.
        Wiring("discard_pending_logs_and_clears", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2), followUpGeneration: 7);
            var d = lc.DiscardPending("revalidate_failed");
            return lc.Pending is null
                && d.LogLine != null
                && d.LogLine.Contains("start_discarded", StringComparison.Ordinal)
                && d.LogLine.Contains("FollowUp", StringComparison.Ordinal)
                && d.LogLine.Contains("revalidate_failed", StringComparison.Ordinal);
        });

        Wiring("cancel_discards_pending_followup", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2), followUpGeneration: 3);
            var r = lc.Cancel("typed-submit", T(3));
            return lc.Pending is null
                && r.LogLine != null
                && r.LogLine.Contains("start_discarded", StringComparison.Ordinal)
                && r.LogLine.Contains("FollowUp", StringComparison.Ordinal);
        });

        Wiring("cancel_discards_pending_echoreopen", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.EchoReopen, null, T(2), followUpGeneration: 4);
            var r = lc.Cancel("turn-start", T(3));
            return lc.Pending is null
                && r.LogLine != null
                && r.LogLine.Contains("start_discarded", StringComparison.Ordinal)
                && r.LogLine.Contains("EchoReopen", StringComparison.Ordinal);
        });

        Wiring("cancel_keeps_pending_clarify", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.Clarify, "srq-synth-keep", T(2), followUpGeneration: 5);
            var r = lc.Cancel("typed-submit", T(3));
            return lc.Pending is { Kind: CaptureKind.Clarify, ClarifyId: "srq-synth-keep" }
                && (r.LogLine is null || !r.LogLine.Contains("start_discarded", StringComparison.Ordinal));
        });

        Wiring("pending_carries_deferral_generation", lc =>
        {
            Accepting(lc, CaptureKind.Manual);
            lc.BeginStart(CaptureKind.FollowUp, null, T(2), followUpGeneration: 42);
            return lc.Pending is { Kind: CaptureKind.FollowUp, FollowUpGeneration: 42 };
        });

        Wiring("release_handoff_can_send_without_second_begin", lc =>
        {
            // Repro: FollowUp → listening → transcript → EchoReopen Deferred → idle → TryReleasePending Began.
            Accepting(lc, CaptureKind.FollowUp);
            lc.ApplyTranscript(LifecycleSignal.TranscriptText, T(2));
            var defer = lc.BeginStart(CaptureKind.EchoReopen, null, T(3), followUpGeneration: 11);
            if (defer.Disposition != StartDisposition.Deferred)
            {
                return false;
            }

            lc.ApplyStatus(CaptureConstants.StatusIdle, T(4));
            var released = lc.TryReleasePending(T(5));
            if (!lc.CanSendRecordStart(released))
            {
                return false;
            }

            // A second BeginStart re-defers (the bug); handoff uses CanSendRecordStart + MarkStartSent instead.
            var second = lc.BeginStart(CaptureKind.EchoReopen, null, T(6), followUpGeneration: 11);
            if (second.Disposition != StartDisposition.Deferred)
            {
                return false;
            }

            _ = lc.MarkStartSent(released.Snapshot.Generation);
            var wake = lc.BeginStart(CaptureKind.Wake, null, T(7));
            return !lc.CanSendRecordStart(released)
                && wake.Disposition == StartDisposition.Rejected
                && lc.Snapshot() is { State: CaptureState.Starting, Kind: CaptureKind.EchoReopen, HasOutstanding: true };
        });

        Wiring("abort_unsent_settles_no_latch_wake_begins", lc =>
        {
            var began = lc.BeginStart(CaptureKind.FollowUp, null, T(0), followUpGeneration: 1);
            var abort = lc.AbortUnsentStart(began.Snapshot.Generation, CaptureConstants.ReasonStaleGeneration, T(1));
            if (abort.Snapshot.HasOutstanding
                || abort.Snapshot.HermesBusyUntilIdle
                || abort.NeedsHermesStop)
            {
                return false;
            }

            var wake = lc.BeginStart(CaptureKind.Wake, null, T(2));
            return wake.Disposition == StartDisposition.Began
                && wake.Snapshot.State == CaptureState.Starting;
        });

        Wiring("cancel_starting_unsent_settles_immediately", lc =>
        {
            lc.BeginStart(CaptureKind.Manual, null, T(0));
            var r = lc.Cancel("typed-submit", T(1));
            return !r.Snapshot.HasOutstanding
                && r.Snapshot.State == CaptureState.Settled
                && !r.NeedsHermesStop;
        });

        Wiring("cancel_starting_sent_cancelled_with_stop", lc =>
        {
            var began = lc.BeginStart(CaptureKind.Manual, null, T(0));
            lc.MarkStartSent(began.Snapshot.Generation);
            var r = lc.Cancel("typed-submit", T(1));
            return r.Snapshot.State == CaptureState.Cancelled
                && r.Snapshot.HasOutstanding
                && r.NeedsHermesStop;
        });
    }

    private void Lifecycle(string name, Func<CaptureLifecycle, bool> body)
    {
        _lifecycleTotal++;
        Run(name, () => body(new CaptureLifecycle()), pass =>
        {
            if (pass)
            {
                _lifecyclePassed++;
            }
        });
    }

    private void Admission(string name, Func<bool> body)
    {
        _admissionTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _admissionPassed++;
            }
        });
    }

    private void Start(string name, Func<CaptureLifecycle, bool> body)
    {
        _startTotal++;
        Run(name, () => body(new CaptureLifecycle()), pass =>
        {
            if (pass)
            {
                _startPassed++;
            }
        });
    }

    private void Invalid(string name, Func<CaptureLifecycle, bool> body)
    {
        _invalidTotal++;
        Run(name, () => body(new CaptureLifecycle()), pass =>
        {
            if (pass)
            {
                _invalidPassed++;
            }
        });
    }

    private void StopPhrase(string name, Func<bool> body)
    {
        _stopPhraseTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _stopPhrasePassed++;
            }
        });
    }

    private void Amendment(string name, Func<CaptureLifecycle, bool> body)
    {
        _amendmentTotal++;
        Run(name, () => body(new CaptureLifecycle()), pass =>
        {
            if (pass)
            {
                _amendmentPassed++;
            }
        });
    }

    private void Amendment(string name, Func<bool> body)
    {
        _amendmentTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _amendmentPassed++;
            }
        });
    }

    private void Latch(string name, Func<CaptureLifecycle, bool> body)
    {
        _latchTotal++;
        Run(name, () => body(new CaptureLifecycle()), pass =>
        {
            if (pass)
            {
                _latchPassed++;
            }
        });
    }

    private void Wiring(string name, Func<CaptureLifecycle, bool> body)
    {
        _wiringTotal++;
        Run(name, () => body(new CaptureLifecycle()), pass =>
        {
            if (pass)
            {
                _wiringPassed++;
            }
        });
    }

    private void RunClarifyRows()
    {
        // P7-CLARIFY: classification, template, haystack stem — P7-D09
        Clarify("shape_single_batch_choices", () =>
            ClarifyShape.IsQuietSingle(
                true,
                new[] { new ClarifyQuestionFacts(false, new[] { "navy", "gray" }) },
                false,
                Array.Empty<string>()));

        Clarify("shape_single_batch_freetext", () =>
            ClarifyShape.IsQuietSingle(
                true,
                new[] { new ClarifyQuestionFacts(false, Array.Empty<string>()) },
                false,
                Array.Empty<string>()));

        Clarify("shape_single_legacy", () =>
            ClarifyShape.IsQuietSingle(false, Array.Empty<ClarifyQuestionFacts>(), false, new[] { "a", "b" }));

        Clarify("shape_card_multiselect", () =>
            !ClarifyShape.IsQuietSingle(
                true,
                new[] { new ClarifyQuestionFacts(true, new[] { "a", "b" }) },
                false,
                Array.Empty<string>()));

        Clarify("shape_card_batch2", () =>
            !ClarifyShape.IsQuietSingle(
                true,
                new[]
                {
                    new ClarifyQuestionFacts(false, new[] { "a" }),
                    new ClarifyQuestionFacts(false, new[] { "b" }),
                },
                false,
                Array.Empty<string>()));

        Clarify("shape_card_zero_questions", () =>
            !ClarifyShape.IsQuietSingle(true, Array.Empty<ClarifyQuestionFacts>(), false, Array.Empty<string>()));

        Clarify("shape_card_legacy_multi", () =>
            !ClarifyShape.IsQuietSingle(false, Array.Empty<ClarifyQuestionFacts>(), true, new[] { "a", "b" }));

        var under20 = Enumerable.Repeat("word", 20).ToArray();
        var over20 = Enumerable.Repeat("word", 21).ToArray();
        Clarify("shape_cap_at_20", () =>
            ClarifyShape.IsQuietSingle(
                true,
                new[] { new ClarifyQuestionFacts(false, under20) },
                false,
                Array.Empty<string>())
            && ClarifyShape.CountSpokenChoiceWords(under20) == 20);

        Clarify("shape_cap_over_20", () =>
            !ClarifyShape.IsQuietSingle(
                true,
                new[] { new ClarifyQuestionFacts(false, over20) },
                false,
                Array.Empty<string>())
            && ClarifyShape.CountSpokenChoiceWords(over20) == 21);

        Clarify("shape_cap_under_20", () =>
            ClarifyShape.IsQuietSingle(
                true,
                new[] { new ClarifyQuestionFacts(false, Enumerable.Repeat("word", 19).ToArray()) },
                false,
                Array.Empty<string>()));

        Clarify("template_0_choices", () =>
            ClarifySpeech.BuildSpokenTemplate("Which color?", Array.Empty<string>()) == "Which color?");

        Clarify("template_1_choice", () =>
            ClarifySpeech.BuildSpokenTemplate("Which color?", new[] { "navy" })
            == "Which color? Is it navy?");

        Clarify("template_2_choices", () =>
            ClarifySpeech.BuildSpokenTemplate("Which color?", new[] { "navy", "gray" })
            == "Which color? Is it navy or gray?");

        Clarify("template_3_choices", () =>
            ClarifySpeech.BuildSpokenTemplate("Pick one?", new[] { "a", "b", "c" })
            == "Pick one? Is it a, b, or c?");

        Clarify("template_4_choices", () =>
            ClarifySpeech.BuildSpokenTemplate("Pick one?", new[] { "a", "b", "c", "d" })
            == "Pick one? Is it a, b, c, or d?");

        Clarify("template_strip_recommended", () =>
            ClarifySpeech.BuildSpokenTemplate(
                "Which color?",
                new[] { "navy " + ClarifyShape.RecommendedMarker, "gray" })
            == "Which color? Is it navy or gray?");

        Clarify("template_already_in_question", () =>
            ClarifySpeech.BuildSpokenTemplate(
                "Do you want navy or gray?",
                new[] { "navy", "gray" })
            == "Do you want navy or gray?");

        Clarify("contain_whole_word_not_substring", () =>
            !ClarifyShape.AllLabelsAppearInQuestion("Which colored option?", new[] { "red" }));

        Clarify("contain_multiword_sequence", () =>
            ClarifyShape.AllLabelsAppearInQuestion("navy blue or gray?", new[] { "navy blue" }));

        Clarify("haystack_stem_only", () =>
            ClarifySpeech.EchoHaystackStem("  Which color?  ") == "Which color?"
            && ClarifySpeech.EchoHaystackStem("Which color?") != ClarifySpeech.BuildSpokenTemplate(
                "Which color?",
                new[] { "navy", "gray" }));
    }

    private void RunTimingRows()
    {
        // P7-LATENCY: pure TurnTiming boundary + line + finalize — P7-D10
        Timing("boundary_short_under_min_len", () =>
            !TurnTiming.HasCompleteFirstSentence("Hi. More text follows here."));

        Timing("boundary_long_first_sentence", () =>
            TurnTiming.HasCompleteFirstSentence(
                "This is a complete first sentence that is long enough. Trailing."));

        Timing("boundary_abbrev_like_hermes", () =>
            // Hermes has no abbrev exception; short head after "Dr. " stays under min_len.
            !TurnTiming.HasCompleteFirstSentence("Dr. Smith said hello today."));

        Timing("boundary_none", () =>
            !TurnTiming.HasCompleteFirstSentence("No terminal punctuation in this reply yet"));

        Timing("line_format_empty_fields", () =>
        {
            var line = TurnTiming.FormatLine(1, TurnTiming.KindTyped, "", "10", "", "", "20", "", "", 0, 0);
            return line.StartsWith(TurnTiming.LogPrefix + " ", StringComparison.Ordinal)
                && line.Contains(" " + TurnTiming.FieldFirstDeltaToFirstSentenceMs + "=", StringComparison.Ordinal)
                && line.Contains(" " + TurnTiming.FieldFirstSentenceToFirstAudioMs + "=", StringComparison.Ordinal)
                && line.Contains(" " + TurnTiming.FieldTranscriptToSubmitMs + "=", StringComparison.Ordinal)
                && line.Contains(" tools=0", StringComparison.Ordinal)
                && line.Contains(" approval=0", StringComparison.Ordinal)
                && line.Contains(TurnTiming.FieldFirstDeltaToFirstSentenceMs + "= ", StringComparison.Ordinal);
        });

        Timing("finalize_complete_before_audio", () =>
        {
            var t = new TurnTiming();
            var t0 = T(0);
            t.Begin(1, TurnTiming.KindVoice, t0, t0.AddMilliseconds(-50));
            t.NoteDelta("This is a complete first sentence that is long enough. ", T(1));
            t.NoteComplete(T(2));
            if (t.ShouldFinalize(T(2), force: false))
            {
                return false;
            }

            if (!t.ShouldFinalize(T(2).AddSeconds(TurnTiming.FinalizeSeconds), force: false))
            {
                return false;
            }

            var line = t.Finalize(T(2).AddSeconds(TurnTiming.FinalizeSeconds), force: false);
            if (line is null)
            {
                return false;
            }

            // first_audio empty: field present with empty value before tools=
            return line.Contains(" " + TurnTiming.FieldSubmitToFirstAudioMs + "= tools=", StringComparison.Ordinal);
        });

        Timing("finalize_audio_before_complete", () =>
        {
            var t = new TurnTiming();
            var t0 = T(0);
            t.Begin(2, TurnTiming.KindTyped, t0, null);
            t.NoteDelta("This is a complete first sentence that is long enough. ", T(1));
            t.NoteFirstAudio(T(2));
            if (t.ShouldFinalize(T(2), force: false))
            {
                return false;
            }

            t.NoteComplete(T(3));
            var line = t.Finalize(T(3), force: false);
            return line is not null
                && line.Contains(TurnTiming.FieldSubmitToCompleteMs + "=3000", StringComparison.Ordinal)
                && line.Contains(TurnTiming.FieldSubmitToFirstAudioMs + "=2000", StringComparison.Ordinal);
        });

        Timing("finalize_no_audio_at_all", () =>
        {
            var t = new TurnTiming();
            t.Begin(3, TurnTiming.KindTyped, T(0), null);
            t.NoteDelta("Short", T(1));
            t.NoteComplete(T(2));
            var early = t.Finalize(T(3), force: false);
            var late = t.Finalize(T(2).AddSeconds(TurnTiming.FinalizeSeconds), force: false);
            return early is null
                && late is not null
                && late.Contains(" " + TurnTiming.FieldSubmitToFirstAudioMs + "= tools=", StringComparison.Ordinal)
                && late.Contains("kind=" + TurnTiming.KindTyped, StringComparison.Ordinal);
        });
    }

    private void Clarify(string name, Func<bool> body)
    {
        _clarifyTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _clarifyPassed++;
            }
        });
    }

    private void Timing(string name, Func<bool> body)
    {
        _timingTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _timingPassed++;
            }
        });
    }

    private void Run(string name, Func<bool> body, Action<bool> tally)
    {
        bool pass;
        try
        {
            pass = body();
        }
        catch (Exception ex)
        {
            pass = false;
            Console.WriteLine("FAIL " + name + " exception=" + ex.GetType().Name);
            Failed++;
            tally(false);
            return;
        }

        Console.WriteLine((pass ? "PASS " : "FAIL ") + name);
        if (!pass)
        {
            Failed++;
        }

        tally(pass);
    }

    private static DateTimeOffset T(double seconds)
        => new DateTimeOffset(2026, 10, 6, 12, 0, 0, TimeSpan.Zero).AddSeconds(seconds);

    private static TranscriptFacts Facts(int len) => new(len, false, false);

    private static void Accepting(CaptureLifecycle lc, CaptureKind kind, string? clarifyId = null)
    {
        lc.BeginStart(kind, clarifyId, T(0));
        lc.ApplyStatus(CaptureConstants.StatusListening, T(1));
    }

    private static CaptureSnapshot AcceptingSnapshot(CaptureKind kind, string? clarifyId = null)
    {
        var lc = new CaptureLifecycle();
        Accepting(lc, kind, clarifyId);
        return lc.Snapshot();
    }

    private static int CountAccepting(CaptureLifecycle lc)
        => lc.Snapshot() is { HasOutstanding: true, State: CaptureState.Accepting } ? 1 : 0;
}
