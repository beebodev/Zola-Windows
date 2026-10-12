namespace Zola.Client.Supervision;

// P9-SUPERVISE: TTS restore is a target after voice is on; this class never opens a socket — P9-D02
public static class TtsRestore
{
    public const int MismatchRetryLimit = 1;
    public const int MaxDecisions = 12;

    public static bool IsSameProcessGeneration(long generationAtGap, long generationAtReady)
        => generationAtGap >= 0 && generationAtGap == generationAtReady;

    public enum Action
    {
        ReadStatus,
        EnableVoice,
        StopLeftoverAudio,
        SetTts,
        LogMismatch,
        LogSecondMismatch,
        Done,
    }

    public readonly record struct Snapshot(bool VoiceOn, bool? Tts);

    public readonly record struct Result(
        IReadOnlyList<Action> Actions,
        bool VoiceOn,
        bool? Tts,
        bool TtsSwitchBeforeVoiceOn);

    public static Result Replay(bool sameProcessGeneration, bool targetOn, IReadOnlyList<Snapshot> statuses)
    {
        var session = new TtsRestoreSession(sameProcessGeneration, targetOn);
        var actions = new List<Action>();
        var index = 0;
        var voiceConfirmed = false;
        var switchBeforeVoice = false;
        for (var step = 0; step < MaxDecisions; step++)
        {
            var action = session.Next();
            actions.Add(action);
            if (action == Action.SetTts && !voiceConfirmed)
            {
                switchBeforeVoice = true;
            }

            if (action is Action.Done or Action.LogSecondMismatch)
            {
                break;
            }

            if (action != Action.ReadStatus)
            {
                continue;
            }

            var snapshot = index < statuses.Count ? statuses[index++] : new Snapshot(false, null);
            session.NoteStatus(snapshot.VoiceOn, snapshot.Tts);
            if (snapshot.VoiceOn)
            {
                voiceConfirmed = true;
            }
        }

        return new Result(actions, session.VoiceOn, session.ObservedTts, switchBeforeVoice);
    }
}

// P9-SUPERVISE: one restore decides voice-on, leftover stop, and the saved TTS target — P9-D02
public sealed class TtsRestoreSession
{
    private enum Phase
    {
        NeedStatus,
        Ready,
    }

    private readonly bool _sameProcessGeneration;
    private readonly bool _targetOn;
    private Phase _phase = Phase.NeedStatus;
    private bool _voiceOn;
    private bool? _tts;
    private bool _leftoverStopped;
    private bool _awaitingVerify;
    private bool _pendingMismatchLog;
    private int _mismatchCount;
    private bool _done;

    public TtsRestoreSession(bool sameProcessGeneration, bool targetOn)
    {
        // P9-SUPERVISE: a new process has no leftover audio, so the stop step is skipped — P9-D02
        _sameProcessGeneration = sameProcessGeneration;
        _targetOn = targetOn;
        _leftoverStopped = !sameProcessGeneration;
    }

    public bool VoiceOn => _voiceOn;

    public bool? ObservedTts => _tts;

    public TtsRestore.Action Next()
    {
        if (_done)
        {
            return TtsRestore.Action.Done;
        }

        if (_phase == Phase.NeedStatus)
        {
            return TtsRestore.Action.ReadStatus;
        }

        if (!_voiceOn)
        {
            // P9-SUPERVISE: the TTS switch waits until a status read shows voice on — P9-D02
            _phase = Phase.NeedStatus;
            return TtsRestore.Action.EnableVoice;
        }

        if (_pendingMismatchLog)
        {
            _pendingMismatchLog = false;
            if (_mismatchCount > TtsRestore.MismatchRetryLimit)
            {
                _done = true;
                return TtsRestore.Action.LogSecondMismatch;
            }

            return TtsRestore.Action.LogMismatch;
        }

        if (!_leftoverStopped)
        {
            // P9-SUPERVISE: socket-only reconnect stops leftover audio only after voice is on — P9-D02
            _leftoverStopped = true;
            _phase = Phase.NeedStatus;
            return TtsRestore.Action.StopLeftoverAudio;
        }

        if (_tts is bool observed && observed != _targetOn)
        {
            if (_mismatchCount > TtsRestore.MismatchRetryLimit)
            {
                _done = true;
                return TtsRestore.Action.LogSecondMismatch;
            }

            // P9-SUPERVISE: set the saved target; a matching status does not flip TTS — P9-D02
            _awaitingVerify = true;
            _phase = Phase.NeedStatus;
            return TtsRestore.Action.SetTts;
        }

        if (_tts is null)
        {
            // P9-SUPERVISE: an unknown flag is not a blind toggle and does not force TTS off — P9-D02
            _mismatchCount++;
            if (_mismatchCount > TtsRestore.MismatchRetryLimit)
            {
                _done = true;
                return TtsRestore.Action.LogSecondMismatch;
            }

            _phase = Phase.NeedStatus;
            return TtsRestore.Action.LogMismatch;
        }

        _done = true;
        return TtsRestore.Action.Done;
    }

    public void NoteStatus(bool voiceOn, bool? tts)
    {
        _voiceOn = voiceOn;
        _tts = tts;
        _phase = Phase.Ready;
        if (!_awaitingVerify)
        {
            return;
        }

        _awaitingVerify = false;
        if (tts != _targetOn)
        {
            _mismatchCount++;
            _pendingMismatchLog = true;
        }
    }
}
