namespace Zola.Client.Presence.Controllers;

// P3-LIFE: eyes, then brightness, then expression; reduced motion bypasses delays — P3-D22
internal sealed class ModeTransitionCoordinator
{
    private long _originTicks;
    private long _eyesDueTicks;
    private long _brightnessDueTicks;
    private long _expressionDueTicks;

    internal void Begin(PresenceLife life, long nowTicks, bool reduced)
    {
        _originTicks = nowTicks;
        var eyesDelay = reduced ? PresenceLife.MsMin : life.EyesDelayMs;
        var brightnessDelay = reduced ? PresenceLife.MsMin : life.BrightnessDelayMs;
        var expressionDelay = reduced ? PresenceLife.MsMin : life.ExpressionDelayMs;
        _eyesDueTicks = nowTicks + PresenceLife.TicksFromMilliseconds(eyesDelay);
        _brightnessDueTicks = nowTicks + PresenceLife.TicksFromMilliseconds(brightnessDelay);
        _expressionDueTicks = nowTicks + PresenceLife.TicksFromMilliseconds(expressionDelay);
    }

    internal bool EyesDue(long nowTicks) => nowTicks >= _eyesDueTicks;

    internal bool BrightnessDue(long nowTicks) => nowTicks >= _brightnessDueTicks;

    internal bool ExpressionDue(long nowTicks) => nowTicks >= _expressionDueTicks;

    internal double ElapsedMs(long nowTicks) => PresenceLife.ElapsedMilliseconds(_originTicks, nowTicks);

    internal double NextPendingMs(long nowTicks, bool eyesArmed, bool brightnessArmed, bool expressionArmed)
    {
        var remaining = double.MaxValue;
        if (!eyesArmed)
        {
            remaining = Math.Min(remaining, PresenceLife.ElapsedMilliseconds(nowTicks, _eyesDueTicks));
        }

        if (!brightnessArmed)
        {
            remaining = Math.Min(remaining, PresenceLife.ElapsedMilliseconds(nowTicks, _brightnessDueTicks));
        }

        if (!expressionArmed)
        {
            remaining = Math.Min(remaining, PresenceLife.ElapsedMilliseconds(nowTicks, _expressionDueTicks));
        }

        return remaining;
    }
}
