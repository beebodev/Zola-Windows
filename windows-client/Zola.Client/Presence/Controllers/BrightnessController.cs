namespace Zola.Client.Presence.Controllers;

// P3-LIFE: ease the multiplier, then pulse while the mode amplitude is non-zero — P3-D22
internal sealed class BrightnessController
{
    private PresenceLife _life = PresenceLife.CreateDefault();
    private PresenceMode _mode = PresenceMode.Idle;
    private float _current = PresenceLife.DefaultIdleMultiplier;
    private float _from = PresenceLife.DefaultIdleMultiplier;
    private float _to = PresenceLife.DefaultIdleMultiplier;
    private float _amplitude = PresenceLife.DefaultPulseAmplitude;
    private long _startTicks;
    private long _pulseStartTicks;
    private bool _easing;
    private bool _pulsing;
    private bool _reduced;

    internal bool IsChanging => _easing || _pulsing;

    internal void Reset(PresenceLife life, PresenceMode mode, bool snap, bool reduced, long nowTicks)
    {
        _life = life;
        _mode = mode;
        _reduced = reduced;
        _to = life.BrightnessMultiplier(mode);
        _amplitude = reduced ? PresenceLife.DefaultPulseAmplitude : life.PulseAmplitude(mode);
        _pulsing = false;

        if (snap
            || life.BrightnessEaseMs <= PresenceLife.MsMin
            || Math.Abs(_to - _current) <= life.MultiplierEpsilon)
        {
            _current = _to;
            _easing = false;
            BeginPulse(nowTicks);
            return;
        }

        _from = _current;
        _startTicks = nowTicks;
        _easing = true;
    }

    internal void ApplyReducedMotion(bool reduced, long nowTicks)
    {
        _reduced = reduced;
        if (reduced)
        {
            _amplitude = PresenceLife.DefaultPulseAmplitude;
            _pulsing = false;
            if (_easing)
            {
                _current = _to;
                _easing = false;
            }

            return;
        }

        _amplitude = _life.PulseAmplitude(_mode);
        if (!_easing)
        {
            BeginPulse(nowTicks);
        }
    }

    internal float Evaluate(long nowTicks)
    {
        if (_easing)
        {
            AdvanceEase(nowTicks);
        }

        if (_pulsing)
        {
            AdvancePulse(nowTicks);
        }

        return _current;
    }

    private void AdvanceEase(long nowTicks)
    {
        var elapsedMs = PresenceLife.ElapsedMilliseconds(_startTicks, nowTicks);
        var t = (float)(elapsedMs / _life.BrightnessEaseMs);
        if (t >= PresenceLife.CurveOne)
        {
            _current = _to;
            _easing = false;
            BeginPulse(nowTicks);
            return;
        }

        if (t < PresenceLife.WeightMin)
        {
            t = PresenceLife.WeightMin;
        }

        _current = PresenceLife.Lerp(_from, _to, PresenceLife.ApplyCurve(t, _life.BrightnessCurve));
        if (Math.Abs(_to - _current) <= _life.MultiplierEpsilon)
        {
            _current = _to;
            _easing = false;
            BeginPulse(nowTicks);
        }
    }

    private void BeginPulse(long nowTicks)
    {
        if (_reduced || _amplitude <= PresenceLife.PulseAmplitudeMin)
        {
            _pulsing = false;
            return;
        }

        _pulseStartTicks = nowTicks;
        _pulsing = true;
    }

    private void AdvancePulse(long nowTicks)
    {
        var periodMs = _life.PulsePeriodMs(_mode);
        if (periodMs <= PresenceLife.PulsePeriodMinMs)
        {
            _current = _to;
            return;
        }

        var cycles = PresenceLife.ElapsedMilliseconds(_pulseStartTicks, nowTicks) / periodMs;
        var wave = MathF.Sin(MathF.Tau * (float)cycles);
        _current = Math.Clamp(
            _to + (_amplitude * wave),
            PresenceLife.MultiplierMin,
            PresenceLife.MultiplierMax);
    }
}
