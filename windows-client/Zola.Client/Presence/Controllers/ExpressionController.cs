namespace Zola.Client.Presence.Controllers;

// P3-LIFE: per-mode expression eased over ExpressionEaseMs — P3-D22
internal sealed class ExpressionController
{
    private readonly float[] _current = new float[MorphTargets.MorphTargetCount];
    private readonly float[] _from = new float[MorphTargets.MorphTargetCount];
    private readonly float[] _to = new float[MorphTargets.MorphTargetCount];
    private PresenceLife _life = PresenceLife.CreateDefault();
    private long _startTicks;
    private bool _easing;

    internal bool IsChanging => _easing;

    internal void Reset(
        PresenceLife life,
        PresenceMode mode,
        bool snap,
        long nowTicks,
        float[] current,
        bool mouthOwns)
    {
        _life = life;
        var last = mouthOwns ? MorphTarget.NostrilFlare : MorphTarget.TeethFV;
        var needsEase = false;
        for (var i = (int)MorphTarget.SquintEyes; i <= (int)last; i++)
        {
            var target = (MorphTarget)i;
            _current[i] = current[i];
            _to[i] = life.ExpressionWeight(mode, target);
            if (snap
                || life.ExpressionEaseMs <= PresenceLife.MsMin
                || Math.Abs(_to[i] - _current[i]) <= life.WeightEpsilon)
            {
                _current[i] = _to[i];
                _from[i] = _to[i];
                continue;
            }

            _from[i] = _current[i];
            needsEase = true;
        }

        if (!needsEase)
        {
            _easing = false;
            return;
        }

        _startTicks = nowTicks;
        _easing = true;
    }

    internal void TakeFromMouth(PresenceMode mode, bool snap, long nowTicks, float[] current)
    {
        var needsEase = false;
        for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
        {
            var target = (MorphTarget)i;
            _current[i] = current[i];
            _to[i] = _life.ExpressionWeight(mode, target);
            if (snap
                || _life.ExpressionEaseMs <= PresenceLife.MsMin
                || Math.Abs(_to[i] - _current[i]) <= _life.WeightEpsilon)
            {
                _current[i] = _to[i];
                _from[i] = _to[i];
                continue;
            }

            _from[i] = _current[i];
            needsEase = true;
        }

        if (!needsEase)
        {
            return;
        }

        if (!_easing)
        {
            for (var i = (int)MorphTarget.SquintEyes; i <= (int)MorphTarget.NostrilFlare; i++)
            {
                _from[i] = _current[i];
            }

            _startTicks = nowTicks;
            _easing = true;
            return;
        }

        var elapsedMs = PresenceLife.ElapsedMilliseconds(_startTicks, nowTicks);
        var t = _life.ExpressionEaseMs <= PresenceLife.MsMin
            ? PresenceLife.CurveOne
            : (float)(elapsedMs / _life.ExpressionEaseMs);
        if (t >= PresenceLife.CurveOne)
        {
            for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
            {
                _current[i] = _to[i];
                _from[i] = _to[i];
            }

            return;
        }

        if (t <= PresenceLife.WeightMin)
        {
            return;
        }

        var remain = PresenceLife.CurveOne - t;
        for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
        {
            if (Math.Abs(_from[i] - _to[i]) <= _life.WeightEpsilon)
            {
                continue;
            }

            _from[i] = (_current[i] - (_to[i] * t)) / remain;
        }
    }

    internal void ApplyReducedMotion()
    {
        if (!_easing)
        {
            return;
        }

        for (var i = (int)MorphTarget.SquintEyes; i < MorphTargets.MorphTargetCount; i++)
        {
            _current[i] = _to[i];
        }

        _easing = false;
    }

    internal void Evaluate(long nowTicks)
    {
        if (!_easing)
        {
            return;
        }

        if (_life.ExpressionEaseMs <= PresenceLife.MsMin)
        {
            SnapTo();
            return;
        }

        var t = (float)(PresenceLife.ElapsedMilliseconds(_startTicks, nowTicks) / _life.ExpressionEaseMs);
        if (t >= PresenceLife.CurveOne)
        {
            SnapTo();
            return;
        }

        if (t < PresenceLife.WeightMin)
        {
            t = PresenceLife.WeightMin;
        }

        var shaped = PresenceLife.ApplyCurve(t, _life.ExpressionCurve);
        var remaining = false;
        for (var i = (int)MorphTarget.SquintEyes; i < MorphTargets.MorphTargetCount; i++)
        {
            _current[i] = PresenceLife.Lerp(_from[i], _to[i], shaped);
            if (Math.Abs(_to[i] - _current[i]) > _life.WeightEpsilon)
            {
                remaining = true;
            }
            else
            {
                _current[i] = _to[i];
            }
        }

        if (!remaining)
        {
            _easing = false;
        }
    }

    internal float Weight(MorphTarget target)
    {
        if (PresenceLife.IsBlinkTarget(target))
        {
            return PresenceLife.WeightMin;
        }

        return _current[(int)target];
    }

    private void SnapTo()
    {
        for (var i = (int)MorphTarget.SquintEyes; i < MorphTargets.MorphTargetCount; i++)
        {
            _current[i] = _to[i];
        }

        _easing = false;
    }
}
