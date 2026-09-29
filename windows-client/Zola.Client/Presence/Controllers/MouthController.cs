namespace Zola.Client.Presence.Controllers;

// P3-LIFE: synthetic mouth while a Hermes TTS segment is active — P3-D14 / S17
internal sealed class MouthController
{
    private readonly float[] _current = new float[MorphTargets.MorphTargetCount];
    private readonly float[] _velocity = new float[MorphTargets.MorphTargetCount];
    private readonly float[] _target = new float[MorphTargets.MorphTargetCount];
    private PresenceLife _life = PresenceLife.CreateDefault();
    private Random _random = new();
    private long _lastEvalTicks;
    private long _nextStepTicks;
    private float _level;
    private bool _owns;
    private bool _speaking;
    private bool _generating;
    private bool _reduced;
    private bool _stepPendingLog;

    internal bool OwnsMouth => _owns;

    internal bool IsChanging => _owns && !_reduced && (_speaking || !AtRest());

    internal float Level => _level;

    internal void SnapToRest()
    {
        _owns = false;
        _speaking = false;
        _generating = false;
        _reduced = false;
        _stepPendingLog = false;
        _level = PresenceLife.WeightMin;
        ClearMotion();
    }

    internal void Begin(PresenceLife life, Random random, long nowTicks, float[] current, bool reduced)
    {
        _life = life;
        _random = random;
        _owns = true;
        _speaking = true;
        _generating = true;
        _reduced = reduced;
        _lastEvalTicks = nowTicks;
        _stepPendingLog = false;
        Adopt(current);
        if (reduced)
        {
            ClearMotion();
            return;
        }

        PickStep(nowTicks);
    }

    // P3-LIFE: segment gaps stop new targets; springs settle; resume keeps current weights — P3-D14
    internal void SetGenerating(bool generating, long nowTicks)
    {
        if (!_owns || _generating == generating)
        {
            return;
        }

        _generating = generating;
        _lastEvalTicks = nowTicks;
        if (!generating)
        {
            _stepPendingLog = false;
            if (!_reduced)
            {
                for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
                {
                    _target[i] = PresenceLife.WeightMin;
                }
            }

            return;
        }

        if (_reduced || !_speaking)
        {
            return;
        }

        PickStep(nowTicks);
    }

    internal void Release(long nowTicks)
    {
        if (!_owns)
        {
            return;
        }

        _speaking = false;
        _generating = false;
        _lastEvalTicks = nowTicks;
        _stepPendingLog = false;
        if (_reduced)
        {
            SnapToRest();
            return;
        }

        for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
        {
            _target[i] = PresenceLife.WeightMin;
        }
    }

    internal void ApplyReducedMotion(bool reduced, long nowTicks)
    {
        _reduced = reduced;
        _lastEvalTicks = nowTicks;
        if (!reduced || !_owns)
        {
            return;
        }

        ClearMotion();
        _stepPendingLog = false;
        if (!_speaking)
        {
            _owns = false;
        }
    }

    internal void Evaluate(long nowTicks)
    {
        if (!_owns)
        {
            return;
        }

        if (_reduced)
        {
            ClearMotion();
            _lastEvalTicks = nowTicks;
            return;
        }

        var elapsedMs = PresenceLife.ElapsedMilliseconds(_lastEvalTicks, nowTicks);
        _lastEvalTicks = nowTicks;
        if (_speaking && _generating && nowTicks >= _nextStepTicks)
        {
            PickStep(nowTicks);
        }

        PresenceLife.IntegrateMouthSprings(
            _current,
            _velocity,
            _target,
            _life,
            elapsedMs,
            (!_speaking || !_generating) ? _life.ReleaseStiffnessScale : PresenceLife.CurveOne);
        if (!_speaking && AtRest())
        {
            _owns = false;
            ClearMotion();
        }
    }

    internal float Weight(MorphTarget target)
    {
        if (!PresenceLife.IsMouthTarget(target))
        {
            return PresenceLife.WeightMin;
        }

        return Math.Clamp(
            _current[(int)target] * _life.MouthGain(target),
            PresenceLife.WeightMin,
            PresenceLife.WeightMax);
    }

    internal bool TryTakeStepLog()
    {
        if (!_stepPendingLog)
        {
            return false;
        }

        _stepPendingLog = false;
        return true;
    }

    private void PickStep(long nowTicks)
    {
        var closure = PresenceLife.ChanceHit(_random, _life.ClosureChance);
        _level = closure
            ? PresenceLife.WeightMin
            : PresenceLife.NextRange(_random, _life.LevelMin, _life.LevelMax);
        var mid = _level * _life.MidScale;
        PresenceLife.BlendMouthBands(mid, _life, out var openAh, out var midOpen, out var closed);
        _target[(int)MorphTarget.JawOpen] = _life.MouthRest(MorphTarget.JawOpen)
            + (closure ? PresenceLife.WeightMin : _life.JawBase + (_life.JawRange * _level));
        _target[(int)MorphTarget.OpenAH] = _life.MouthRest(MorphTarget.OpenAH) + openAh;
        _target[(int)MorphTarget.MidOpenEhUh] = _life.MouthRest(MorphTarget.MidOpenEhUh) + midOpen;
        _target[(int)MorphTarget.ClosedMBP] = _life.MouthRest(MorphTarget.ClosedMBP) + closed;
        _target[(int)MorphTarget.RoundOOW] = _life.MouthRest(MorphTarget.RoundOOW)
            + (!closure && _level > _life.BandMidMax && PresenceLife.ChanceHit(_random, _life.RoundOoChance)
                ? _life.RoundOoWeight
                : PresenceLife.WeightMin);
        _target[(int)MorphTarget.WideEE] = _life.MouthRest(MorphTarget.WideEE) + (mid * _life.WideEeScale);
        _target[(int)MorphTarget.TeethFV] = _life.MouthRest(MorphTarget.TeethFV)
            + (!closure && PresenceLife.ChanceHit(_random, _life.TeethChance)
                ? _life.TeethWeight
                : PresenceLife.WeightMin);
        for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
        {
            _target[i] = Math.Clamp(_target[i], PresenceLife.WeightMin, PresenceLife.WeightMax);
        }

        var stepMs = PresenceLife.NextInclusive(_random, _life.MouthStepMinMs, _life.MouthStepMaxMs);
        _nextStepTicks = nowTicks + PresenceLife.TicksFromMilliseconds(stepMs);
        _stepPendingLog = true;
    }

    private void Adopt(float[] current)
    {
        for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
        {
            _current[i] = current[i];
            _velocity[i] = PresenceLife.WeightMin;
            _target[i] = current[i];
        }
    }

    private void ClearMotion()
    {
        for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
        {
            _current[i] = PresenceLife.WeightMin;
            _velocity[i] = PresenceLife.WeightMin;
            _target[i] = PresenceLife.WeightMin;
        }

        _level = PresenceLife.WeightMin;
    }

    private bool AtRest()
    {
        for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
        {
            if (Math.Abs(_current[i]) > _life.WeightEpsilon || Math.Abs(_velocity[i]) > _life.WeightEpsilon)
            {
                return false;
            }
        }

        return true;
    }
}
