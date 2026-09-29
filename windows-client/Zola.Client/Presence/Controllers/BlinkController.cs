namespace Zola.Client.Presence.Controllers;

internal enum BlinkPhase
{
    Rest,
    Closing,
    Opening,
    LidEasing,
}

// P3-LIFE: irregular blinks, thinking half-blink, dormant lid rest — P3-D22
internal sealed class BlinkController
{
    private readonly float[] _weights = new float[PresenceLife.BlinkChannelCount];
    private PresenceLife _life = PresenceLife.CreateDefault();
    private PresenceMode _mode = PresenceMode.Idle;
    private Random _random = new();
    private BlinkPhase _phase = BlinkPhase.Rest;
    private float _lidAmount = PresenceLife.WeightMin;
    private float _fromAmount = PresenceLife.WeightMin;
    private float _peak = PresenceLife.WeightMax;
    private float _targetRest = PresenceLife.WeightMin;
    private float _mixLeft = PresenceLife.DefaultMixBlinkLeft;
    private float _mixRight = PresenceLife.DefaultMixBlinkRight;
    private float _mixBoth = PresenceLife.DefaultMixBlinkBoth;
    private long _phaseStartTicks;
    private long _nextBlinkTicks;
    private int _lastIntervalMs;
    private int _startedIntervalMs;
    private bool _hasSchedule;

    internal BlinkPhase Phase => _phase;

    internal float LidAmount => _lidAmount;

    internal float Peak => _peak;

    internal int LastIntervalMs => _lastIntervalMs;

    internal int StartedIntervalMs => _startedIntervalMs;

    internal bool IsChanging => _phase != BlinkPhase.Rest;

    internal bool HasScheduledBlink => _hasSchedule && _phase == BlinkPhase.Rest && _life.BlinkEnabled(_mode);

    internal void Reset(
        PresenceLife life,
        PresenceMode mode,
        Random random,
        float currentLeft,
        float currentRight,
        float currentBoth,
        bool snap,
        long nowTicks)
    {
        _life = life;
        _mode = mode;
        _random = random;
        _lidAmount = PresenceLife.Max3(currentLeft, currentRight, currentBoth);
        _targetRest = life.LidRest(mode);
        UseRestMix();
        _hasSchedule = false;
        _lastIntervalMs = PresenceLife.MsMin;
        _nextBlinkTicks = 0;

        if (snap
            || life.LidEaseMs <= PresenceLife.MsMin
            || Math.Abs(_lidAmount - _targetRest) <= life.WeightEpsilon)
        {
            _lidAmount = _targetRest;
            _phase = BlinkPhase.Rest;
            Compose();
            ScheduleNext(nowTicks);
            return;
        }

        _fromAmount = _lidAmount;
        _phaseStartTicks = nowTicks;
        _phase = BlinkPhase.LidEasing;
        Compose();
    }

    internal void ApplyReducedMotion(long nowTicks)
    {
        if (_phase != BlinkPhase.LidEasing)
        {
            return;
        }

        _lidAmount = _targetRest;
        _phase = BlinkPhase.Rest;
        UseRestMix();
        Compose();
        ScheduleNext(nowTicks);
    }

    internal void Evaluate(long nowTicks)
    {
        switch (_phase)
        {
            case BlinkPhase.Closing:
                AdvanceToward(_peak, _life.BlinkCloseMs, _life.BlinkCurve, nowTicks, BlinkPhase.Opening);
                break;
            case BlinkPhase.Opening:
                AdvanceToward(_targetRest, _life.BlinkOpenMs, _life.BlinkCurve, nowTicks, BlinkPhase.Rest);
                break;
            case BlinkPhase.LidEasing:
                AdvanceToward(_targetRest, _life.LidEaseMs, _life.LidCurve, nowTicks, BlinkPhase.Rest);
                break;
            default:
                MaybeStartBlink(nowTicks);
                break;
        }

        Compose();
    }

    internal float Weight(MorphTarget target)
    {
        if (!PresenceLife.IsBlinkTarget(target))
        {
            return PresenceLife.WeightMin;
        }

        return _weights[(int)target];
    }

    internal double RemainingMs(long nowTicks)
    {
        if (!HasScheduledBlink)
        {
            return PresenceLife.TickIntervalMinMs;
        }

        return PresenceLife.ElapsedMilliseconds(nowTicks, _nextBlinkTicks);
    }

    private void AdvanceToward(float destination, int durationMs, LifeCurve curve, long nowTicks, BlinkPhase next)
    {
        if (durationMs <= PresenceLife.MsMin)
        {
            FinishPhase(destination, next, nowTicks);
            return;
        }

        var t = (float)(PresenceLife.ElapsedMilliseconds(_phaseStartTicks, nowTicks) / durationMs);
        if (t >= PresenceLife.CurveOne)
        {
            FinishPhase(destination, next, nowTicks);
            return;
        }

        if (t < PresenceLife.WeightMin)
        {
            t = PresenceLife.WeightMin;
        }

        _lidAmount = PresenceLife.Lerp(_fromAmount, destination, PresenceLife.ApplyCurve(t, curve));
    }

    private void FinishPhase(float destination, BlinkPhase next, long nowTicks)
    {
        _lidAmount = destination;
        _fromAmount = destination;
        _phaseStartTicks = nowTicks;
        _phase = next;
        if (next == BlinkPhase.Rest)
        {
            UseRestMix();
            ScheduleNext(nowTicks);
        }
        else if (next == BlinkPhase.Opening)
        {
            _peak = destination;
        }
    }

    private void MaybeStartBlink(long nowTicks)
    {
        if (!_life.BlinkEnabled(_mode))
        {
            _hasSchedule = false;
            return;
        }

        if (!_hasSchedule)
        {
            ScheduleNext(nowTicks);
            return;
        }

        if (nowTicks < _nextBlinkTicks)
        {
            return;
        }

        PickBlinkMix();
        _fromAmount = _lidAmount;
        _peak = _life.BlinkPeak(_mode);
        _phase = BlinkPhase.Closing;
        _phaseStartTicks = nowTicks;
        _hasSchedule = false;
        _startedIntervalMs = _lastIntervalMs;
        _lastIntervalMs = PresenceLife.NextInclusive(
            _random,
            _life.BlinkIntervalMinMs(_mode),
            _life.BlinkIntervalMaxMs(_mode));
        _nextBlinkTicks = nowTicks + PresenceLife.TicksFromMilliseconds(_lastIntervalMs);
    }

    private void ScheduleNext(long nowTicks)
    {
        if (!_life.BlinkEnabled(_mode) || _phase != BlinkPhase.Rest)
        {
            _hasSchedule = false;
            return;
        }

        if (_nextBlinkTicks > nowTicks && _lastIntervalMs > PresenceLife.MsMin)
        {
            _hasSchedule = true;
            return;
        }

        _lastIntervalMs = PresenceLife.NextInclusive(
            _random,
            _life.BlinkIntervalMinMs(_mode),
            _life.BlinkIntervalMaxMs(_mode));
        _nextBlinkTicks = nowTicks + PresenceLife.TicksFromMilliseconds(_lastIntervalMs);
        _hasSchedule = true;
    }

    private void PickBlinkMix()
    {
        if (_life.AsymmetryChance > PresenceLife.ChanceMin
            && _random.NextDouble() < _life.AsymmetryChance)
        {
            var left = _random.Next((int)MorphTarget.BlinkLeft, (int)MorphTarget.BlinkBoth)
                == (int)MorphTarget.BlinkLeft;
            _mixLeft = left ? _life.AsymmetryRatio : PresenceLife.WeightMin;
            _mixRight = left ? PresenceLife.WeightMin : _life.AsymmetryRatio;
            _mixBoth = PresenceLife.WeightMin;
            return;
        }

        UseRestMix();
    }

    private void UseRestMix()
    {
        _mixLeft = _life.MixBlinkLeft;
        _mixRight = _life.MixBlinkRight;
        _mixBoth = _life.MixBlinkBoth;
    }

    private void Compose()
    {
        _weights[(int)MorphTarget.BlinkLeft] = Math.Clamp(
            _lidAmount * _mixLeft,
            PresenceLife.WeightMin,
            PresenceLife.WeightMax);
        _weights[(int)MorphTarget.BlinkRight] = Math.Clamp(
            _lidAmount * _mixRight,
            PresenceLife.WeightMin,
            PresenceLife.WeightMax);
        _weights[(int)MorphTarget.BlinkBoth] = Math.Clamp(
            _lidAmount * _mixBoth,
            PresenceLife.WeightMin,
            PresenceLife.WeightMax);
    }
}
