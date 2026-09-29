using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Zola.Client.Presence;

internal enum LifeCurve
{
    Linear,
    EaseOut,
    EaseInOut,
}

// P3-LIFE: every life value is a named constant with a named range — P3-D22
internal sealed class PresenceLife
{
    internal const string DebugFileName = "presence-life.json";
    internal const string DefaultsFileName = "presence-life.defaults.json";

    internal const float WeightMin = 0f;
    internal const float WeightMax = 1f;
    internal const int MsMin = 0;
    internal const int MsMax = 120000;
    internal const int OnsetOffsetMin = -300;
    internal const int OnsetOffsetMax = 300;
    internal const float ChanceMin = 0f;
    internal const float ChanceMax = 1f;
    internal const float MultiplierMin = 0f;
    internal const float MultiplierMax = 8f;
    internal const float PulseAmplitudeMin = 0f;
    internal const float PulseAmplitudeMax = 2f;
    internal const int PulsePeriodMinMs = 1;
    internal const int PulsePeriodMaxMs = 120000;
    internal const float StiffnessMin = 1f;
    internal const float StiffnessMax = 20000f;
    internal const float DampingMin = 0.01f;
    internal const float DampingMax = 20f;
    internal const int TickIntervalMinMs = 1;
    internal const int TickIntervalMaxMs = 1000;
    internal const float EpsilonMin = 0f;
    internal const float EpsilonMax = 1f;
    internal const int SpringSubstepMinMs = 1;
    internal const int SpringSubstepMaxMs = 16;
    internal const int SeedMin = 0;
    internal const int SeedMax = int.MaxValue;
    internal const float ScaleMin = 0f;
    internal const float ScaleMax = 2f;

    internal const int DefaultBlinkCloseMs = 120;
    internal const int DefaultBlinkOpenMs = 180;
    internal const float DefaultMixBlinkLeft = 0f;
    internal const float DefaultMixBlinkRight = 0f;
    internal const float DefaultMixBlinkBoth = 1f;
    internal const float DefaultAsymmetryChance = 0f;
    internal const float DefaultAsymmetryRatio = 0.85f;
    internal const int DefaultBlinkIntervalMinMs = 3000;
    internal const int DefaultBlinkIntervalMaxMs = 8000;
    internal const int DefaultThinkingIntervalMinMs = 2000;
    internal const int DefaultThinkingIntervalMaxMs = 4500;
    internal const float DefaultBlinkDepth = 1f;
    internal const float DefaultThinkingBlinkDepth = 0.4f;
    internal const float DefaultLidRest = 0f;
    internal const float DefaultDormantLidRest = 0.3f;
    internal const float DefaultListeningBrowRaise = 0.4f;
    internal const float DefaultThinkingBrowFurrow = 0.15f;
    // P3-LIFE: Alert placeholder-safe after Round 5 (S25 has no Windows trigger) — P3-D22
    internal const float DefaultAlertWideEyes = 0.35f;
    internal const float DefaultAlertBrowRaise = 0.3f;
    internal const float DefaultAlertNostril = 0.1f;
    internal const float DefaultAlertWideEe = 0f;
    internal const float DefaultIdleMultiplier = 1f;
    internal const float DefaultListeningMultiplier = 1.1f;
    internal const float DefaultThinkingMultiplier = 0.75f;
    internal const float DefaultSpeakingMultiplier = 1f;
    internal const float DefaultAlertMultiplier = 1.25f;
    internal const float DefaultDormantMultiplier = 0.5f;
    internal const float DefaultPulseAmplitude = 0f;
    // P3-LIFE: Round 3 quieter speaking pulse; Round 4 mouth baseline — P3-D22
    internal const float DefaultSpeakingPulseAmplitude = 0.05f;
    internal const int DefaultPulsePeriodMs = 1200;
    internal const int DefaultEyesDelayMs = 0;
    internal const int DefaultBrightnessDelayMs = 450;
    internal const int DefaultExpressionDelayMs = 850;
    internal const int DefaultExpressionEaseMs = 300;
    internal const int DefaultBrightnessEaseMs = 600;
    internal const int DefaultLidEaseMs = 600;
    internal const bool DefaultSpeakingHoldsThinkingUntilOnset = true;
    internal const int DefaultMouthOnsetOffsetMs = 0;
    internal const int DefaultPlaybackPollHz = 20;
    internal const int DefaultReleaseDebounceMs = 450;
    internal const bool DefaultSpeakingPauseShowsThinking = false;
    internal const int PlaybackPollHzMin = 1;
    internal const int PlaybackPollHzMax = 60;
    internal const int DefaultMouthStepMinMs = 150;
    internal const int DefaultMouthStepMaxMs = 250;
    internal const float DefaultClosureChance = 0.2f;
    internal const float DefaultLevelMin = 0.1f;
    internal const float DefaultLevelMax = 0.85f;
    internal const float DefaultJawBase = 0.02f;
    internal const float DefaultJawRange = 0.1f;
    internal const float DefaultMidScale = 0.25f;
    internal const float DefaultBandLowMax = 0.2f;
    internal const float DefaultBandMidMax = 0.6f;
    internal const float DefaultMidOpenScale = 0.15f;
    internal const float DefaultWideEeScale = 0f;
    internal const float DefaultRoundOoChance = 0.3f;
    internal const float DefaultRoundOoWeight = 0.35f;
    internal const float DefaultTeethChance = 0.15f;
    internal const float DefaultTeethWeight = 0.12f;
    internal const float DefaultMouthGain = 1f;
    internal const float DefaultOpenAhGain = 0.5f;
    internal const float DefaultMidOpenGain = 0.5f;
    internal const float DefaultClosedMbpGain = 0.6f;
    internal const float DefaultTeethFvGain = 0.3f;
    internal const float DefaultReleaseStiffnessScale = 2.5f;
    internal const float DefaultJawStiffness = 400f;
    internal const float DefaultBandStiffness = 200f;
    internal const float DefaultVisemeStiffness = 1500f;
    internal const float DefaultJawDamping = 1f;
    internal const float DefaultBandDamping = 1f;
    internal const float DefaultVisemeDamping = 0.5f;
    internal const int DefaultTickIntervalMs = 16;
    internal const int DefaultSpeakingTickIntervalMs = 33;
    internal const float DefaultWeightEpsilon = 0.0005f;
    internal const float DefaultMultiplierEpsilon = 0.0005f;
    internal const int DefaultSpringSubstepMs = 4;
    internal const int DefaultRandomSeed = 0;
    internal const double MsPerSecond = 1000.0;
    internal const float CurveOne = 1f;
    internal const float CurveMid = 0.5f;
    internal const float CurveQuadraticScale = 2f;
    internal const int RandomExclusiveMaxOffset = 1;
    internal const int BlinkChannelCount = 3;
    internal const float SpringMass = 1f;
    internal const float CriticalDampingRatio = 1f;

    private static readonly PresenceMode[] AllModes = Enum.GetValues<PresenceMode>();
    private static readonly MorphTarget[] MouthTargets =
    {
        MorphTarget.JawOpen, MorphTarget.OpenAH, MorphTarget.MidOpenEhUh,
        MorphTarget.ClosedMBP, MorphTarget.RoundOOW, MorphTarget.WideEE, MorphTarget.TeethFV,
    };

    private bool[] _blinkEnabled = new bool[AllModes.Length];
    private int[] _blinkIntervalMinMs = new int[AllModes.Length];
    private int[] _blinkIntervalMaxMs = new int[AllModes.Length];
    private float[] _blinkDepth = new float[AllModes.Length];
    private float[] _lidRest = new float[AllModes.Length];
    private float[,] _expression = new float[AllModes.Length, MorphTargets.MorphTargetCount];
    private float[] _multiplier = new float[AllModes.Length];
    private float[] _pulseAmplitude = new float[AllModes.Length];
    private int[] _pulsePeriodMs = new int[AllModes.Length];
    private float[] _mouthRest = new float[MorphTargets.MorphTargetCount];
    private float[] _mouthStiffness = new float[MorphTargets.MorphTargetCount];
    private float[] _mouthDamping = new float[MorphTargets.MorphTargetCount];
    private float[] _mouthGain = new float[MorphTargets.MorphTargetCount];

    internal int BlinkCloseMs { get; private set; } = DefaultBlinkCloseMs;
    internal int BlinkOpenMs { get; private set; } = DefaultBlinkOpenMs;
    internal LifeCurve BlinkCurve { get; private set; } = LifeCurve.Linear;
    internal float MixBlinkLeft { get; private set; } = DefaultMixBlinkLeft;
    internal float MixBlinkRight { get; private set; } = DefaultMixBlinkRight;
    internal float MixBlinkBoth { get; private set; } = DefaultMixBlinkBoth;
    internal float AsymmetryChance { get; private set; } = DefaultAsymmetryChance;
    internal float AsymmetryRatio { get; private set; } = DefaultAsymmetryRatio;
    internal int EyesDelayMs { get; private set; } = DefaultEyesDelayMs;
    internal int BrightnessDelayMs { get; private set; } = DefaultBrightnessDelayMs;
    internal int ExpressionDelayMs { get; private set; } = DefaultExpressionDelayMs;
    internal int ExpressionEaseMs { get; private set; } = DefaultExpressionEaseMs;
    internal LifeCurve ExpressionCurve { get; private set; } = LifeCurve.EaseOut;
    internal int BrightnessEaseMs { get; private set; } = DefaultBrightnessEaseMs;
    internal LifeCurve BrightnessCurve { get; private set; } = LifeCurve.EaseInOut;
    internal int LidEaseMs { get; private set; } = DefaultLidEaseMs;
    internal LifeCurve LidCurve { get; private set; } = LifeCurve.EaseInOut;
    internal bool SpeakingHoldsThinkingUntilOnset { get; private set; } = DefaultSpeakingHoldsThinkingUntilOnset;
    internal int MouthOnsetOffsetMs { get; private set; } = DefaultMouthOnsetOffsetMs;
    internal int PlaybackPollHz { get; private set; } = DefaultPlaybackPollHz;
    internal int ReleaseDebounceMs { get; private set; } = DefaultReleaseDebounceMs;
    internal bool SpeakingPauseShowsThinking { get; private set; } = DefaultSpeakingPauseShowsThinking;
    internal int MouthStepMinMs { get; private set; } = DefaultMouthStepMinMs;
    internal int MouthStepMaxMs { get; private set; } = DefaultMouthStepMaxMs;
    internal float ClosureChance { get; private set; } = DefaultClosureChance;
    internal float LevelMin { get; private set; } = DefaultLevelMin;
    internal float LevelMax { get; private set; } = DefaultLevelMax;
    internal float JawBase { get; private set; } = DefaultJawBase;
    internal float JawRange { get; private set; } = DefaultJawRange;
    internal float MidScale { get; private set; } = DefaultMidScale;
    internal float BandLowMax { get; private set; } = DefaultBandLowMax;
    internal float BandMidMax { get; private set; } = DefaultBandMidMax;
    internal float MidOpenScale { get; private set; } = DefaultMidOpenScale;
    internal float WideEeScale { get; private set; } = DefaultWideEeScale;
    internal float RoundOoChance { get; private set; } = DefaultRoundOoChance;
    internal float RoundOoWeight { get; private set; } = DefaultRoundOoWeight;
    internal float TeethChance { get; private set; } = DefaultTeethChance;
    internal float TeethWeight { get; private set; } = DefaultTeethWeight;
    internal float ReleaseStiffnessScale { get; private set; } = DefaultReleaseStiffnessScale;
    internal int TickIntervalMs { get; private set; } = DefaultTickIntervalMs;
    internal int SpeakingTickIntervalMs { get; private set; } = DefaultSpeakingTickIntervalMs;
    internal float WeightEpsilon { get; private set; } = DefaultWeightEpsilon;
    internal float MultiplierEpsilon { get; private set; } = DefaultMultiplierEpsilon;
    internal int SpringSubstepMs { get; private set; } = DefaultSpringSubstepMs;
#if DEBUG
    internal int RandomSeed { get; private set; } = DefaultRandomSeed;
#endif

    internal static PresenceLife CreateDefault()
    {
        var life = new PresenceLife();
        foreach (var mode in AllModes)
        {
            var i = (int)mode;
            life._blinkEnabled[i] = mode != PresenceMode.Dormant;
            life._blinkIntervalMinMs[i] = mode == PresenceMode.Thinking
                ? DefaultThinkingIntervalMinMs
                : DefaultBlinkIntervalMinMs;
            life._blinkIntervalMaxMs[i] = mode == PresenceMode.Thinking
                ? DefaultThinkingIntervalMaxMs
                : DefaultBlinkIntervalMaxMs;
            life._blinkDepth[i] = mode == PresenceMode.Thinking
                ? DefaultThinkingBlinkDepth
                : DefaultBlinkDepth;
            life._lidRest[i] = mode == PresenceMode.Dormant ? DefaultDormantLidRest : DefaultLidRest;
            life._multiplier[i] = mode switch
            {
                PresenceMode.Listening => DefaultListeningMultiplier,
                PresenceMode.Thinking => DefaultThinkingMultiplier,
                PresenceMode.Speaking => DefaultSpeakingMultiplier,
                PresenceMode.Alert => DefaultAlertMultiplier,
                PresenceMode.Dormant => DefaultDormantMultiplier,
                _ => DefaultIdleMultiplier,
            };
            life._pulseAmplitude[i] = mode == PresenceMode.Speaking
                ? DefaultSpeakingPulseAmplitude
                : DefaultPulseAmplitude;
            life._pulsePeriodMs[i] = DefaultPulsePeriodMs;
        }

        life._expression[(int)PresenceMode.Listening, (int)MorphTarget.BrowRaise] = DefaultListeningBrowRaise;
        life._expression[(int)PresenceMode.Thinking, (int)MorphTarget.BrowFurrow] = DefaultThinkingBrowFurrow;
        life._expression[(int)PresenceMode.Alert, (int)MorphTarget.WideAlertEyes] = DefaultAlertWideEyes;
        life._expression[(int)PresenceMode.Alert, (int)MorphTarget.BrowRaise] = DefaultAlertBrowRaise;
        life._expression[(int)PresenceMode.Alert, (int)MorphTarget.NostrilFlare] = DefaultAlertNostril;
        life._expression[(int)PresenceMode.Alert, (int)MorphTarget.WideEE] = DefaultAlertWideEe;

        foreach (var target in MouthTargets)
        {
            var i = (int)target;
            life._mouthRest[i] = WeightMin;
            life._mouthGain[i] = DefaultMouthGain;
            if (target == MorphTarget.JawOpen)
            {
                life._mouthStiffness[i] = DefaultJawStiffness;
                life._mouthDamping[i] = DefaultJawDamping;
            }
            else if (target is MorphTarget.OpenAH or MorphTarget.MidOpenEhUh or MorphTarget.ClosedMBP)
            {
                life._mouthStiffness[i] = DefaultBandStiffness;
                life._mouthDamping[i] = DefaultBandDamping;
            }
            else
            {
                life._mouthStiffness[i] = DefaultVisemeStiffness;
                life._mouthDamping[i] = DefaultVisemeDamping;
            }
        }

        life._mouthGain[(int)MorphTarget.OpenAH] = DefaultOpenAhGain;
        life._mouthGain[(int)MorphTarget.MidOpenEhUh] = DefaultMidOpenGain;
        life._mouthGain[(int)MorphTarget.ClosedMBP] = DefaultClosedMbpGain;
        life._mouthGain[(int)MorphTarget.TeethFV] = DefaultTeethFvGain;

        return life;
    }

    internal PresenceLife Clone()
    {
        var copy = (PresenceLife)MemberwiseClone();
        copy._blinkEnabled = (bool[])_blinkEnabled.Clone();
        copy._blinkIntervalMinMs = (int[])_blinkIntervalMinMs.Clone();
        copy._blinkIntervalMaxMs = (int[])_blinkIntervalMaxMs.Clone();
        copy._blinkDepth = (float[])_blinkDepth.Clone();
        copy._lidRest = (float[])_lidRest.Clone();
        copy._multiplier = (float[])_multiplier.Clone();
        copy._pulseAmplitude = (float[])_pulseAmplitude.Clone();
        copy._pulsePeriodMs = (int[])_pulsePeriodMs.Clone();
        copy._mouthRest = (float[])_mouthRest.Clone();
        copy._mouthStiffness = (float[])_mouthStiffness.Clone();
        copy._mouthDamping = (float[])_mouthDamping.Clone();
        copy._mouthGain = (float[])_mouthGain.Clone();
        copy._expression = (float[,])_expression.Clone();
        return copy;
    }

    internal bool BlinkEnabled(PresenceMode mode) => _blinkEnabled[(int)mode];
    internal int BlinkIntervalMinMs(PresenceMode mode) => _blinkIntervalMinMs[(int)mode];
    internal int BlinkIntervalMaxMs(PresenceMode mode) => _blinkIntervalMaxMs[(int)mode];
    internal float BlinkDepth(PresenceMode mode) => _blinkDepth[(int)mode];
    internal float LidRest(PresenceMode mode) => _lidRest[(int)mode];
    internal float ExpressionWeight(PresenceMode mode, MorphTarget target) => _expression[(int)mode, (int)target];
    internal float BrightnessMultiplier(PresenceMode mode) => _multiplier[(int)mode];
    internal float PulseAmplitude(PresenceMode mode) => _pulseAmplitude[(int)mode];
    internal int PulsePeriodMs(PresenceMode mode) => _pulsePeriodMs[(int)mode];
    internal float BlinkMix(MorphTarget target)
    {
        return target switch
        {
            MorphTarget.BlinkLeft => MixBlinkLeft,
            MorphTarget.BlinkRight => MixBlinkRight,
            MorphTarget.BlinkBoth => MixBlinkBoth,
            _ => WeightMin,
        };
    }

    internal float BlinkPeak(PresenceMode mode)
    {
        var rest = LidRest(mode);
        return rest + (BlinkDepth(mode) * (WeightMax - rest));
    }

    internal static bool IsBlinkTarget(MorphTarget target) => target <= MorphTarget.BlinkBoth;

    internal static bool IsMouthTarget(MorphTarget target) => target >= MorphTarget.JawOpen;

    internal static bool ChanceHit(Random random, float chance)
    {
        return chance > ChanceMin && random.NextDouble() < chance;
    }

    internal static float NextRange(Random random, float min, float max)
    {
        return Lerp(min, max, (float)random.NextDouble());
    }

    internal static void BlendMouthBands(
        float mid,
        PresenceLife life,
        out float openAh,
        out float midOpen,
        out float closed)
    {
        if (mid <= WeightMin)
        {
            closed = WeightMax;
            openAh = WeightMin;
            midOpen = WeightMin;
            return;
        }

        if (mid < life.BandLowMax)
        {
            var t = mid / life.BandLowMax;
            closed = WeightMax - t;
            openAh = t;
            midOpen = WeightMin;
            return;
        }

        if (mid < life.BandMidMax)
        {
            var span = life.BandMidMax - life.BandLowMax;
            var t = span <= WeightMin ? CurveOne : (mid - life.BandLowMax) / span;
            closed = WeightMin;
            openAh = CurveOne - t;
            midOpen = t * life.MidOpenScale;
            return;
        }

        closed = WeightMin;
        openAh = WeightMin;
        midOpen = life.MidOpenScale;
    }

    internal static void IntegrateMouthSprings(
        float[] current,
        float[] velocity,
        float[] target,
        PresenceLife life,
        double elapsedMs,
        float stiffnessScale)
    {
        if (elapsedMs <= WeightMin)
        {
            return;
        }

        if (stiffnessScale < ScaleMin)
        {
            stiffnessScale = ScaleMin;
        }

        var remaining = elapsedMs;
        var step = life.SpringSubstepMs;
        while (remaining > WeightMin)
        {
            var dtMs = remaining > step ? step : remaining;
            var dt = (float)(dtMs / MsPerSecond);
            for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
            {
                var morph = (MorphTarget)i;
                IntegrateSpring(
                    ref current[i],
                    ref velocity[i],
                    target[i],
                    life.MouthStiffness(morph) * stiffnessScale,
                    life.MouthDamping(morph),
                    dt);
            }

            remaining -= dtMs;
        }
    }

    internal static void IntegrateSpring(
        ref float position,
        ref float velocity,
        float target,
        float stiffness,
        float zeta,
        float dt)
    {
        if (dt <= WeightMin)
        {
            return;
        }

        var omega = MathF.Sqrt(stiffness / SpringMass);
        var x0 = position - target;
        if (zeta >= CriticalDampingRatio)
        {
            var a = x0;
            var b = velocity + (omega * x0);
            var decay = MathF.Exp(-omega * dt);
            position = target + ((a + (b * dt)) * decay);
            velocity = ((b * (CurveOne - (omega * dt))) - (a * omega)) * decay;
        }
        else
        {
            var wd = omega * MathF.Sqrt(CurveOne - (zeta * zeta));
            var a = x0;
            var b = wd <= WeightMin ? WeightMin : (velocity + (zeta * omega * x0)) / wd;
            var decay = MathF.Exp(-zeta * omega * dt);
            var angle = wd * dt;
            var cos = MathF.Cos(angle);
            var sin = MathF.Sin(angle);
            var shaped = (a * cos) + (b * sin);
            position = target + (decay * shaped);
            velocity = (-zeta * omega * decay * shaped)
                + (decay * (((-a * wd) * sin) + (b * wd * cos)));
        }

        position = Math.Clamp(position, WeightMin, WeightMax);
    }

    internal static float ApplyCurve(float t, LifeCurve curve)
    {
        switch (curve)
        {
            case LifeCurve.EaseOut:
                var u = CurveOne - t;
                return CurveOne - (u * u);
            case LifeCurve.EaseInOut:
                if (t < CurveMid)
                {
                    return CurveQuadraticScale * t * t;
                }

                var v = CurveOne - t;
                return CurveOne - (CurveQuadraticScale * v * v);
            default:
                return t;
        }
    }

    internal static float Lerp(float from, float to, float t)
    {
        return from + ((to - from) * t);
    }

    internal static double ElapsedMilliseconds(long startTicks, long nowTicks)
    {
        return (nowTicks - startTicks) * MsPerSecond / Stopwatch.Frequency;
    }

    internal static long TicksFromMilliseconds(double milliseconds)
    {
        return (long)(milliseconds * Stopwatch.Frequency / MsPerSecond);
    }

    internal static int DelayMilliseconds(double remainingMs)
    {
        if (remainingMs <= TickIntervalMinMs)
        {
            return TickIntervalMinMs;
        }

        return (int)Math.Ceiling(remainingMs);
    }

    internal static int NextInclusive(Random random, int min, int max)
    {
        if (max <= min)
        {
            return min;
        }

        return random.Next(min, max + RandomExclusiveMaxOffset);
    }

    internal static float Max3(float a, float b, float c)
    {
        return Math.Max(a, Math.Max(b, c));
    }

    internal float MouthRest(MorphTarget target) => _mouthRest[(int)target];
    internal float MouthStiffness(MorphTarget target) => _mouthStiffness[(int)target];
    internal float MouthDamping(MorphTarget target) => _mouthDamping[(int)target];
    internal float MouthGain(MorphTarget target) => _mouthGain[(int)target];

    internal static IEnumerable<MorphTarget> ExpressionTargets(PresenceMode mode)
    {
        var last = mode == PresenceMode.Speaking ? MorphTarget.NostrilFlare : MorphTarget.TeethFV;
        for (var t = MorphTarget.SquintEyes; t <= last; t++)
        {
            yield return t;
        }
    }

    internal static bool TryReplaceJson(string json, out PresenceLife next, out string reason)
    {
        next = CreateDefault();
        reason = "";
        JsonDocument document;
        try
        {
            document = JsonDocument.Parse(json);
        }
        catch (JsonException ex)
        {
            reason = "invalid JSON: " + ex.Message;
            return false;
        }

        using (document)
        {
            if (document.RootElement.ValueKind != JsonValueKind.Object)
            {
                reason = "root is not an object";
                return false;
            }

            var seen = new HashSet<string>(StringComparer.Ordinal);
            if (!TryWalk(document.RootElement, "", next, seen, out reason))
            {
                return false;
            }

            foreach (var key in RequiredKeys)
            {
                if (!seen.Contains(key))
                {
                    reason = key + " is missing";
                    next = CreateDefault();
                    return false;
                }
            }
        }

        return true;
    }

    internal string ToCanonicalJson()
    {
        var builder = new StringBuilder();
        builder.Append('{');
        AppendGroup(builder, "blink", AppendBlink);
        builder.Append(',');
        AppendGroup(builder, "expression", AppendExpression);
        builder.Append(',');
        AppendGroup(builder, "brightness", AppendBrightness);
        builder.Append(',');
        AppendGroup(builder, "transition", AppendTransition);
        builder.Append(',');
        AppendGroup(builder, "mouth", AppendMouth);
        builder.Append(',');
        AppendGroup(builder, "engine", AppendEngine);
        builder.Append('}');
        return builder.ToString();
    }

    internal string ToPrettyJson()
    {
        using var parsed = JsonDocument.Parse(ToCanonicalJson());
        return JsonSerializer.Serialize(parsed.RootElement, new JsonSerializerOptions { WriteIndented = true });
    }

    internal string Fingerprint()
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(ToCanonicalJson()));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }

    internal static readonly string[] RequiredKeys = BuildRequiredKeys();

    internal static IReadOnlyDictionary<string, int> KeyCountByGroup()
    {
        var counts = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (var key in RequiredKeys)
        {
            var group = key.Split('.')[0];
            counts.TryGetValue(group, out var n);
            counts[group] = n + 1;
        }

        return counts;
    }

    private static string[] BuildRequiredKeys()
    {
        var keys = new List<string>
        {
            "blink.closeMs", "blink.openMs", "blink.curve",
            "blink.mixBlinkLeft", "blink.mixBlinkRight", "blink.mixBlinkBoth",
            "blink.asymmetryChance", "blink.asymmetryRatio",
        };
        foreach (var mode in AllModes)
        {
            var prefix = "blink." + mode + ".";
            keys.Add(prefix + "enabled");
            keys.Add(prefix + "intervalMinMs");
            keys.Add(prefix + "intervalMaxMs");
            keys.Add(prefix + "depth");
            keys.Add(prefix + "lidRest");
        }

        foreach (var mode in AllModes)
        {
            foreach (var target in ExpressionTargets(mode))
            {
                keys.Add("expression." + mode + "." + target);
            }
        }

        foreach (var mode in AllModes)
        {
            var prefix = "brightness." + mode + ".";
            keys.Add(prefix + "multiplier");
            keys.Add(prefix + "pulseAmplitude");
            keys.Add(prefix + "pulsePeriodMs");
        }

        keys.AddRange(
        [
            "transition.eyesDelayMs", "transition.brightnessDelayMs", "transition.expressionDelayMs",
            "transition.expressionEaseMs", "transition.expressionCurve",
            "transition.brightnessEaseMs", "transition.brightnessCurve",
            "transition.lidEaseMs", "transition.lidCurve",
            "transition.speakingHoldsThinkingUntilOnset",
            "mouth.mouthOnsetOffsetMs", "mouth.playbackPollHz", "mouth.releaseDebounceMs",
            "mouth.speakingPauseShowsThinking",
            "mouth.stepMinMs", "mouth.stepMaxMs",
            "mouth.closureChance", "mouth.levelMin", "mouth.levelMax",
            "mouth.jawBase", "mouth.jawRange", "mouth.midScale",
            "mouth.bandLowMax", "mouth.bandMidMax", "mouth.midOpenScale",
            "mouth.wideEeScale", "mouth.roundOoChance", "mouth.roundOoWeight",
            "mouth.teethChance", "mouth.teethWeight",
            "mouth.releaseStiffnessScale",
        ]);
        foreach (var target in MouthTargets)
        {
            var prefix = "mouth." + target + ".";
            keys.Add(prefix + "rest");
            keys.Add(prefix + "stiffness");
            keys.Add(prefix + "damping");
            keys.Add(prefix + "gain");
        }

        keys.Add("engine.tickIntervalMs");
        keys.Add("engine.speakingTickIntervalMs");
        keys.Add("engine.weightEpsilon");
        keys.Add("engine.multiplierEpsilon");
        keys.Add("engine.springSubstepMs");
#if DEBUG
        keys.Add("engine.randomSeed");
#endif
        return keys.ToArray();
    }

    private static bool TryWalk(JsonElement element, string path, PresenceLife life, HashSet<string> seen, out string reason)
    {
        reason = "";
        if (element.ValueKind != JsonValueKind.Object)
        {
            reason = (path.Length == 0 ? "root" : path) + " is not an object";
            return false;
        }

        foreach (var property in element.EnumerateObject())
        {
            var child = path.Length == 0 ? property.Name : path + "." + property.Name;
            if (property.Value.ValueKind == JsonValueKind.Object)
            {
                if (!TryWalk(property.Value, child, life, seen, out reason))
                {
                    return false;
                }

                continue;
            }

            if (!TryAssign(life, child, property.Value, out reason))
            {
                return false;
            }

            seen.Add(child);
        }

        return true;
    }

    private static bool TryAssign(PresenceLife life, string key, JsonElement value, out string reason)
    {
        reason = "";
        var parts = key.Split('.');
        if (parts.Length < 2)
        {
            reason = key + " is not a life value";
            return false;
        }

        switch (parts[0])
        {
            case "blink": return AssignBlink(life, parts, value, out reason);
            case "expression": return AssignExpression(life, parts, value, out reason);
            case "brightness": return AssignBrightness(life, parts, value, out reason);
            case "transition": return AssignTransition(life, parts, value, out reason);
            case "mouth": return AssignMouth(life, parts, value, out reason);
            case "engine": return AssignEngine(life, parts, value, out reason);
            default:
                reason = key + " is not a life value";
                return false;
        }
    }

    private static bool AssignBlink(PresenceLife life, string[] parts, JsonElement value, out string reason)
    {
        if (parts.Length == 2)
        {
            return parts[1] switch
            {
                "closeMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.BlinkCloseMs = v, out reason),
                "openMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.BlinkOpenMs = v, out reason),
                "curve" => AssignCurve(parts[1], value, v => life.BlinkCurve = v, out reason),
                "mixBlinkLeft" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.MixBlinkLeft = v, out reason),
                "mixBlinkRight" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.MixBlinkRight = v, out reason),
                "mixBlinkBoth" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.MixBlinkBoth = v, out reason),
                "asymmetryChance" => AssignFloat(parts[1], value, ChanceMin, ChanceMax, v => life.AsymmetryChance = v, out reason),
                "asymmetryRatio" => AssignFloat(parts[1], value, ChanceMin, ChanceMax, v => life.AsymmetryRatio = v, out reason),
                _ => Unknown(string.Join('.', parts), out reason),
            };
        }

        if (parts.Length == 3 && TryMode(parts[1], out var mode))
        {
            var i = (int)mode;
            return parts[2] switch
            {
                "enabled" => AssignBool(parts[2], value, v => life._blinkEnabled[i] = v, out reason),
                "intervalMinMs" => AssignInt(parts[2], value, MsMin, MsMax, v => life._blinkIntervalMinMs[i] = v, out reason),
                "intervalMaxMs" => AssignInt(parts[2], value, MsMin, MsMax, v => life._blinkIntervalMaxMs[i] = v, out reason),
                "depth" => AssignFloat(parts[2], value, WeightMin, WeightMax, v => life._blinkDepth[i] = v, out reason),
                "lidRest" => AssignFloat(parts[2], value, WeightMin, WeightMax, v => life._lidRest[i] = v, out reason),
                _ => Unknown(string.Join('.', parts), out reason),
            };
        }

        return Unknown(string.Join('.', parts), out reason);
    }

    private static bool AssignExpression(PresenceLife life, string[] parts, JsonElement value, out string reason)
    {
        if (parts.Length == 3 && TryMode(parts[1], out var mode) && TryMorph(parts[2], out var target))
        {
            var owned = false;
            foreach (var allowed in ExpressionTargets(mode))
            {
                if (allowed == target)
                {
                    owned = true;
                    break;
                }
            }

            if (!owned)
            {
                return Unknown(string.Join('.', parts), out reason);
            }

            return AssignFloat(parts[2], value, WeightMin, WeightMax, v => life._expression[(int)mode, (int)target] = v, out reason);
        }

        return Unknown(string.Join('.', parts), out reason);
    }

    private static bool AssignBrightness(PresenceLife life, string[] parts, JsonElement value, out string reason)
    {
        if (parts.Length == 3 && TryMode(parts[1], out var mode))
        {
            var i = (int)mode;
            return parts[2] switch
            {
                "multiplier" => AssignFloat(parts[2], value, MultiplierMin, MultiplierMax, v => life._multiplier[i] = v, out reason),
                "pulseAmplitude" => AssignFloat(parts[2], value, PulseAmplitudeMin, PulseAmplitudeMax, v => life._pulseAmplitude[i] = v, out reason),
                "pulsePeriodMs" => AssignInt(parts[2], value, PulsePeriodMinMs, PulsePeriodMaxMs, v => life._pulsePeriodMs[i] = v, out reason),
                _ => Unknown(string.Join('.', parts), out reason),
            };
        }

        return Unknown(string.Join('.', parts), out reason);
    }

    private static bool AssignTransition(PresenceLife life, string[] parts, JsonElement value, out string reason)
    {
        if (parts.Length != 2)
        {
            return Unknown(string.Join('.', parts), out reason);
        }

        return parts[1] switch
        {
            "eyesDelayMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.EyesDelayMs = v, out reason),
            "brightnessDelayMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.BrightnessDelayMs = v, out reason),
            "expressionDelayMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.ExpressionDelayMs = v, out reason),
            "expressionEaseMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.ExpressionEaseMs = v, out reason),
            "expressionCurve" => AssignCurve(parts[1], value, v => life.ExpressionCurve = v, out reason),
            "brightnessEaseMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.BrightnessEaseMs = v, out reason),
            "brightnessCurve" => AssignCurve(parts[1], value, v => life.BrightnessCurve = v, out reason),
            "lidEaseMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.LidEaseMs = v, out reason),
            "lidCurve" => AssignCurve(parts[1], value, v => life.LidCurve = v, out reason),
            "speakingHoldsThinkingUntilOnset" => AssignBool(
                parts[1],
                value,
                v => life.SpeakingHoldsThinkingUntilOnset = v,
                out reason),
            _ => Unknown(string.Join('.', parts), out reason),
        };
    }

    private static bool AssignMouth(PresenceLife life, string[] parts, JsonElement value, out string reason)
    {
        if (parts.Length == 2)
        {
            return parts[1] switch
            {
                "mouthOnsetOffsetMs" => AssignInt(parts[1], value, OnsetOffsetMin, OnsetOffsetMax, v => life.MouthOnsetOffsetMs = v, out reason),
                "playbackPollHz" => AssignInt(parts[1], value, PlaybackPollHzMin, PlaybackPollHzMax, v => life.PlaybackPollHz = v, out reason),
                "releaseDebounceMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.ReleaseDebounceMs = v, out reason),
                "speakingPauseShowsThinking" => AssignBool(parts[1], value, v => life.SpeakingPauseShowsThinking = v, out reason),
                "stepMinMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.MouthStepMinMs = v, out reason),
                "stepMaxMs" => AssignInt(parts[1], value, MsMin, MsMax, v => life.MouthStepMaxMs = v, out reason),
                "closureChance" => AssignFloat(parts[1], value, ChanceMin, ChanceMax, v => life.ClosureChance = v, out reason),
                "levelMin" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.LevelMin = v, out reason),
                "levelMax" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.LevelMax = v, out reason),
                "jawBase" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.JawBase = v, out reason),
                "jawRange" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.JawRange = v, out reason),
                "midScale" => AssignFloat(parts[1], value, ScaleMin, ScaleMax, v => life.MidScale = v, out reason),
                "bandLowMax" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.BandLowMax = v, out reason),
                "bandMidMax" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.BandMidMax = v, out reason),
                "midOpenScale" => AssignFloat(parts[1], value, ScaleMin, ScaleMax, v => life.MidOpenScale = v, out reason),
                "wideEeScale" => AssignFloat(parts[1], value, ScaleMin, ScaleMax, v => life.WideEeScale = v, out reason),
                "roundOoChance" => AssignFloat(parts[1], value, ChanceMin, ChanceMax, v => life.RoundOoChance = v, out reason),
                "roundOoWeight" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.RoundOoWeight = v, out reason),
                "teethChance" => AssignFloat(parts[1], value, ChanceMin, ChanceMax, v => life.TeethChance = v, out reason),
                "teethWeight" => AssignFloat(parts[1], value, WeightMin, WeightMax, v => life.TeethWeight = v, out reason),
                "releaseStiffnessScale" => AssignFloat(parts[1], value, ScaleMin, MultiplierMax, v => life.ReleaseStiffnessScale = v, out reason),
                _ => Unknown(string.Join('.', parts), out reason),
            };
        }

        if (parts.Length == 3 && TryMorph(parts[1], out var target))
        {
            var ownedMouth = false;
            foreach (var mouth in MouthTargets)
            {
                if (mouth == target)
                {
                    ownedMouth = true;
                    break;
                }
            }

            if (ownedMouth)
            {
                var i = (int)target;
                return parts[2] switch
                {
                    "rest" => AssignFloat(parts[2], value, WeightMin, WeightMax, v => life._mouthRest[i] = v, out reason),
                    "stiffness" => AssignFloat(parts[2], value, StiffnessMin, StiffnessMax, v => life._mouthStiffness[i] = v, out reason),
                    "damping" => AssignFloat(parts[2], value, DampingMin, DampingMax, v => life._mouthDamping[i] = v, out reason),
                    "gain" => AssignFloat(parts[2], value, ScaleMin, ScaleMax, v => life._mouthGain[i] = v, out reason),
                    _ => Unknown(string.Join('.', parts), out reason),
                };
            }
        }

        return Unknown(string.Join('.', parts), out reason);
    }

    private static bool AssignEngine(PresenceLife life, string[] parts, JsonElement value, out string reason)
    {
        if (parts.Length != 2)
        {
            return Unknown(string.Join('.', parts), out reason);
        }

        switch (parts[1])
        {
            case "tickIntervalMs":
                return AssignInt(parts[1], value, TickIntervalMinMs, TickIntervalMaxMs, v => life.TickIntervalMs = v, out reason);
            case "speakingTickIntervalMs":
                return AssignInt(parts[1], value, TickIntervalMinMs, TickIntervalMaxMs, v => life.SpeakingTickIntervalMs = v, out reason);
            case "weightEpsilon":
                return AssignFloat(parts[1], value, EpsilonMin, EpsilonMax, v => life.WeightEpsilon = v, out reason);
            case "multiplierEpsilon":
                return AssignFloat(parts[1], value, EpsilonMin, EpsilonMax, v => life.MultiplierEpsilon = v, out reason);
            case "springSubstepMs":
                return AssignInt(parts[1], value, SpringSubstepMinMs, SpringSubstepMaxMs, v => life.SpringSubstepMs = v, out reason);
#if DEBUG
            case "randomSeed":
                return AssignInt(parts[1], value, SeedMin, SeedMax, v => life.RandomSeed = v, out reason);
#endif
            default:
                return Unknown(string.Join('.', parts), out reason);
        }
    }

    private void AppendBlink(StringBuilder builder)
    {
        AppendInt(builder, "closeMs", BlinkCloseMs);
        builder.Append(',');
        AppendInt(builder, "openMs", BlinkOpenMs);
        builder.Append(',');
        AppendCurve(builder, "curve", BlinkCurve);
        builder.Append(',');
        AppendFloat(builder, "mixBlinkLeft", MixBlinkLeft);
        builder.Append(',');
        AppendFloat(builder, "mixBlinkRight", MixBlinkRight);
        builder.Append(',');
        AppendFloat(builder, "mixBlinkBoth", MixBlinkBoth);
        builder.Append(',');
        AppendFloat(builder, "asymmetryChance", AsymmetryChance);
        builder.Append(',');
        AppendFloat(builder, "asymmetryRatio", AsymmetryRatio);
        foreach (var mode in AllModes)
        {
            builder.Append(',');
            builder.Append('"').Append(mode).Append("\":{");
            AppendBool(builder, "enabled", _blinkEnabled[(int)mode]);
            builder.Append(',');
            AppendInt(builder, "intervalMinMs", _blinkIntervalMinMs[(int)mode]);
            builder.Append(',');
            AppendInt(builder, "intervalMaxMs", _blinkIntervalMaxMs[(int)mode]);
            builder.Append(',');
            AppendFloat(builder, "depth", _blinkDepth[(int)mode]);
            builder.Append(',');
            AppendFloat(builder, "lidRest", _lidRest[(int)mode]);
            builder.Append('}');
        }
    }

    private void AppendExpression(StringBuilder builder)
    {
        var firstMode = true;
        foreach (var mode in AllModes)
        {
            if (!firstMode)
            {
                builder.Append(',');
            }

            firstMode = false;
            builder.Append('"').Append(mode).Append("\":{");
            var first = true;
            foreach (var target in ExpressionTargets(mode))
            {
                if (!first)
                {
                    builder.Append(',');
                }

                first = false;
                AppendFloat(builder, target.ToString(), _expression[(int)mode, (int)target]);
            }

            builder.Append('}');
        }
    }

    private void AppendBrightness(StringBuilder builder)
    {
        var first = true;
        foreach (var mode in AllModes)
        {
            if (!first)
            {
                builder.Append(',');
            }

            first = false;
            builder.Append('"').Append(mode).Append("\":{");
            AppendFloat(builder, "multiplier", _multiplier[(int)mode]);
            builder.Append(',');
            AppendFloat(builder, "pulseAmplitude", _pulseAmplitude[(int)mode]);
            builder.Append(',');
            AppendInt(builder, "pulsePeriodMs", _pulsePeriodMs[(int)mode]);
            builder.Append('}');
        }
    }

    private void AppendTransition(StringBuilder builder)
    {
        AppendInt(builder, "eyesDelayMs", EyesDelayMs);
        builder.Append(',');
        AppendInt(builder, "brightnessDelayMs", BrightnessDelayMs);
        builder.Append(',');
        AppendInt(builder, "expressionDelayMs", ExpressionDelayMs);
        builder.Append(',');
        AppendInt(builder, "expressionEaseMs", ExpressionEaseMs);
        builder.Append(',');
        AppendCurve(builder, "expressionCurve", ExpressionCurve);
        builder.Append(',');
        AppendInt(builder, "brightnessEaseMs", BrightnessEaseMs);
        builder.Append(',');
        AppendCurve(builder, "brightnessCurve", BrightnessCurve);
        builder.Append(',');
        AppendInt(builder, "lidEaseMs", LidEaseMs);
        builder.Append(',');
        AppendCurve(builder, "lidCurve", LidCurve);
        builder.Append(',');
        AppendBool(builder, "speakingHoldsThinkingUntilOnset", SpeakingHoldsThinkingUntilOnset);
    }

    private void AppendMouth(StringBuilder builder)
    {
        AppendInt(builder, "mouthOnsetOffsetMs", MouthOnsetOffsetMs);
        builder.Append(',');
        AppendInt(builder, "playbackPollHz", PlaybackPollHz);
        builder.Append(',');
        AppendInt(builder, "releaseDebounceMs", ReleaseDebounceMs);
        builder.Append(',');
        AppendBool(builder, "speakingPauseShowsThinking", SpeakingPauseShowsThinking);
        builder.Append(',');
        AppendInt(builder, "stepMinMs", MouthStepMinMs);
        builder.Append(',');
        AppendInt(builder, "stepMaxMs", MouthStepMaxMs);
        builder.Append(',');
        AppendFloat(builder, "closureChance", ClosureChance);
        builder.Append(',');
        AppendFloat(builder, "levelMin", LevelMin);
        builder.Append(',');
        AppendFloat(builder, "levelMax", LevelMax);
        builder.Append(',');
        AppendFloat(builder, "jawBase", JawBase);
        builder.Append(',');
        AppendFloat(builder, "jawRange", JawRange);
        builder.Append(',');
        AppendFloat(builder, "midScale", MidScale);
        builder.Append(',');
        AppendFloat(builder, "bandLowMax", BandLowMax);
        builder.Append(',');
        AppendFloat(builder, "bandMidMax", BandMidMax);
        builder.Append(',');
        AppendFloat(builder, "midOpenScale", MidOpenScale);
        builder.Append(',');
        AppendFloat(builder, "wideEeScale", WideEeScale);
        builder.Append(',');
        AppendFloat(builder, "roundOoChance", RoundOoChance);
        builder.Append(',');
        AppendFloat(builder, "roundOoWeight", RoundOoWeight);
        builder.Append(',');
        AppendFloat(builder, "teethChance", TeethChance);
        builder.Append(',');
        AppendFloat(builder, "teethWeight", TeethWeight);
        builder.Append(',');
        AppendFloat(builder, "releaseStiffnessScale", ReleaseStiffnessScale);
        foreach (var target in MouthTargets)
        {
            builder.Append(',');
            builder.Append('"').Append(target).Append("\":{");
            AppendFloat(builder, "rest", _mouthRest[(int)target]);
            builder.Append(',');
            AppendFloat(builder, "stiffness", _mouthStiffness[(int)target]);
            builder.Append(',');
            AppendFloat(builder, "damping", _mouthDamping[(int)target]);
            builder.Append(',');
            AppendFloat(builder, "gain", _mouthGain[(int)target]);
            builder.Append('}');
        }
    }

    private void AppendEngine(StringBuilder builder)
    {
        AppendInt(builder, "tickIntervalMs", TickIntervalMs);
        builder.Append(',');
        AppendInt(builder, "speakingTickIntervalMs", SpeakingTickIntervalMs);
        builder.Append(',');
        AppendFloat(builder, "weightEpsilon", WeightEpsilon);
        builder.Append(',');
        AppendFloat(builder, "multiplierEpsilon", MultiplierEpsilon);
        builder.Append(',');
        AppendInt(builder, "springSubstepMs", SpringSubstepMs);
#if DEBUG
        builder.Append(',');
        AppendInt(builder, "randomSeed", RandomSeed);
#endif
    }

    private static void AppendGroup(StringBuilder builder, string name, Action<StringBuilder> body)
    {
        builder.Append('"').Append(name).Append("\":{");
        body(builder);
        builder.Append('}');
    }

    private static void AppendInt(StringBuilder builder, string key, int value)
    {
        builder.Append('"').Append(key).Append("\":").Append(value.ToString(CultureInfo.InvariantCulture));
    }

    private static void AppendFloat(StringBuilder builder, string key, float value)
    {
        builder.Append('"').Append(key).Append("\":").Append(value.ToString("G9", CultureInfo.InvariantCulture));
    }

    private static void AppendBool(StringBuilder builder, string key, bool value)
    {
        builder.Append('"').Append(key).Append("\":").Append(value ? "true" : "false");
    }

    private static void AppendCurve(StringBuilder builder, string key, LifeCurve curve)
    {
        builder.Append('"').Append(key).Append("\":\"").Append(CurveName(curve)).Append('"');
    }

    private static bool AssignInt(string key, JsonElement value, int min, int max, Action<int> assign, out string reason)
    {
        if (value.ValueKind != JsonValueKind.Number || !value.TryGetInt32(out var parsed))
        {
            reason = key + " is not a number";
            return false;
        }

        if (parsed < min || parsed > max)
        {
            reason = key + " out of range";
            return false;
        }

        assign(parsed);
        reason = "";
        return true;
    }

    private static bool AssignFloat(string key, JsonElement value, float min, float max, Action<float> assign, out string reason)
    {
        if (value.ValueKind != JsonValueKind.Number || !value.TryGetDouble(out var parsed))
        {
            reason = key + " is not a number";
            return false;
        }

        if (parsed < min || parsed > max)
        {
            reason = key + " out of range";
            return false;
        }

        assign((float)parsed);
        reason = "";
        return true;
    }

    private static bool AssignBool(string key, JsonElement value, Action<bool> assign, out string reason)
    {
        if (value.ValueKind == JsonValueKind.True)
        {
            assign(true);
            reason = "";
            return true;
        }

        if (value.ValueKind == JsonValueKind.False)
        {
            assign(false);
            reason = "";
            return true;
        }

        reason = key + " is not a boolean";
        return false;
    }

    private static bool AssignCurve(string key, JsonElement value, Action<LifeCurve> assign, out string reason)
    {
        if (value.ValueKind != JsonValueKind.String)
        {
            reason = key + " is not a curve";
            return false;
        }

        switch (value.GetString())
        {
            case "linear": assign(LifeCurve.Linear); break;
            case "easeOut": assign(LifeCurve.EaseOut); break;
            case "easeInOut": assign(LifeCurve.EaseInOut); break;
            default:
                reason = key + " is not a curve";
                return false;
        }

        reason = "";
        return true;
    }

    private static string CurveName(LifeCurve curve)
    {
        return curve switch
        {
            LifeCurve.EaseOut => "easeOut",
            LifeCurve.EaseInOut => "easeInOut",
            _ => "linear",
        };
    }

    private static bool TryMode(string name, out PresenceMode mode) => Enum.TryParse(name, ignoreCase: false, out mode);

    private static bool TryMorph(string name, out MorphTarget target) => Enum.TryParse(name, ignoreCase: false, out target);

    private static bool Unknown(string key, out string reason)
    {
        reason = key + " is not a life value";
        return false;
    }
}
