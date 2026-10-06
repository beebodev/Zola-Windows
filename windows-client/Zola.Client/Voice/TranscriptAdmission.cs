namespace Zola.Client.Voice;

// P7-VOICEAUTH: pure admission — ownership then authority then echo-only reject — P7-D01

public static class AdmissionReasons
{
    public const string NoOwner = "no_owner";
    public const string Cancelled = "cancelled";
    public const string Settled = "settled";
    public const string TurnRunningUnbound = "turn_running_unbound";
    public const string ClarifyNotActive = "clarify_not_active";
    public const string Gated = "gated";
    public const string ModeText = "mode_text";
    public const string Echo = "echo";
}

public static class AdmissionLog
{
    public const string AdmitFormat =
        "transcript admit gen={0} kind={1} clarify={2} len={3} owner_window={4}";
    public const string DropFormat =
        "transcript drop reason={0} gen={1} kind={2} len={3} owner={4}";
    public const string OwnerNone = "none";
    public const string ClarifyNone = "none";
    public const string StopPhraseRestoreFormat =
        "stop_phrase restore inadmissible reason={0}";
}

public readonly struct TranscriptFacts
{
    public TranscriptFacts(int length, bool isStopPhrase, bool isNoSpeechLimit)
    {
        Length = length;
        IsStopPhrase = isStopPhrase;
        IsNoSpeechLimit = isNoSpeechLimit;
    }

    public int Length { get; }
    public bool IsStopPhrase { get; }
    public bool IsNoSpeechLimit { get; }
}

public abstract record AdmissionVerdict
{
    private AdmissionVerdict()
    {
    }

    public sealed record Admit(CaptureKind Kind, string? ClarifyId) : AdmissionVerdict;

    public sealed record Drop(string Reason) : AdmissionVerdict;
}

public static class TranscriptAdmission
{
    // P7-VOICEAUTH: Decide ignores stop-phrase/no-speech flags for Admit/Drop; wire acts after — P7-D01
    public static AdmissionVerdict Decide(
        TranscriptFacts facts,
        CaptureSnapshot lifecycle,
        bool turnRunning,
        bool clarifyRequestOpenForSession,
        bool gated,
        bool modeText,
        bool isEcho)
    {
        _ = facts;

        if (gated)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.Gated);
        }

        if (modeText)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.ModeText);
        }

        if (!lifecycle.HasOutstanding)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.NoOwner);
        }

        if (lifecycle.State == CaptureState.Cancelled)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.Cancelled);
        }

        if (lifecycle.State == CaptureState.Settled)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.Settled);
        }

        if (lifecycle.State != CaptureState.Accepting)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.NoOwner);
        }

        if (lifecycle.Kind == CaptureKind.Clarify)
        {
            if (string.IsNullOrEmpty(lifecycle.ClarifyId) || !clarifyRequestOpenForSession)
            {
                return new AdmissionVerdict.Drop(AdmissionReasons.ClarifyNotActive);
            }
        }
        else if (turnRunning)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.TurnRunningUnbound);
        }

        if (isEcho)
        {
            return new AdmissionVerdict.Drop(AdmissionReasons.Echo);
        }

        return new AdmissionVerdict.Admit(
            lifecycle.Kind,
            lifecycle.Kind == CaptureKind.Clarify ? lifecycle.ClarifyId : null);
    }

    public static string FormatAdmit(AdmissionVerdict.Admit admit, CaptureSnapshot lifecycle, int length)
    {
        var clarify = admit.ClarifyId ?? AdmissionLog.ClarifyNone;
        var window = FormatWindow(lifecycle);
        return string.Format(
            AdmissionLog.AdmitFormat,
            lifecycle.Generation,
            FormatKind(lifecycle),
            clarify,
            length,
            window);
    }

    public static string FormatDrop(AdmissionVerdict.Drop drop, CaptureSnapshot lifecycle, int length)
    {
        var gen = lifecycle.HasOutstanding || lifecycle.Generation > 0
            ? lifecycle.Generation.ToString()
            : AdmissionLog.OwnerNone;
        var kind = lifecycle.HasOutstanding || lifecycle.Generation > 0
            ? FormatKind(lifecycle)
            : AdmissionLog.OwnerNone;
        var owner = lifecycle.HasOutstanding || lifecycle.WindowStart is not null
            ? FormatWindow(lifecycle)
            : AdmissionLog.OwnerNone;
        return string.Format(AdmissionLog.DropFormat, drop.Reason, gen, kind, length, owner);
    }

    private static string FormatKind(CaptureSnapshot lifecycle)
    {
        return lifecycle.Kind == CaptureKind.Clarify && !string.IsNullOrEmpty(lifecycle.ClarifyId)
            ? "Clarify(" + lifecycle.ClarifyId + ")"
            : lifecycle.Kind.ToString();
    }

    private static string FormatWindow(CaptureSnapshot lifecycle)
    {
        if (lifecycle.WindowStart is null)
        {
            return AdmissionLog.OwnerNone;
        }

        var start = lifecycle.WindowStart.Value.ToString("o");
        var stop = lifecycle.WindowStop?.ToString("o") ?? "";
        return "start=" + start + ";stop=" + stop;
    }
}
