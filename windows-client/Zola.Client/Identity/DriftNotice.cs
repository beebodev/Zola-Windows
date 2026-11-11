namespace Zola.Client.Identity;

// PROC1-ID: drift result → notice decision (testable; UI only posts) — PROC1-D13
public sealed record DriftDecision(bool PostNotice, string NoticeText, IReadOnlyList<string> LogComponents, int? PluginFileCount);

public static class DriftNotice
{
    public static DriftDecision FromResult(DriftCheckResult result)
    {
        if (!result.Completed || !result.HasDrift)
        {
            return new DriftDecision(false, "", Array.Empty<string>(), null);
        }

        var labels = new List<string>();
        var log = new List<string>();
        if (result.HermesHeadDrift || result.HermesLocalEditsDrift)
        {
            labels.Add(IdentityConstants.DriftLabelHermes);
            if (result.HermesHeadDrift)
            {
                log.Add(IdentityConstants.ComponentHermesHead);
            }

            if (result.HermesLocalEditsDrift)
            {
                log.Add(IdentityConstants.ComponentHermesLocalEdits);
            }
        }

        if (result.PackagesDrift)
        {
            labels.Add(IdentityConstants.DriftLabelPackages);
            log.Add(IdentityConstants.ComponentPackages);
        }

        if (result.PluginsDrift)
        {
            labels.Add(IdentityConstants.DriftLabelPlugins);
            log.Add(IdentityConstants.ComponentPlugins);
        }

        var text = $"{IdentityConstants.DriftNoticePrefix} ({string.Join(", ", labels)}).";
        return new DriftDecision(true, text, log, result.PluginDriftFileCount);
    }
}

public sealed class DriftCheckResult
{
    public bool Completed { get; init; }
    public string? IncompleteReason { get; init; }
    public bool HermesHeadDrift { get; init; }
    public bool HermesLocalEditsDrift { get; init; }
    public bool PackagesDrift { get; init; }
    public bool PluginsDrift { get; init; }
    public int? PluginDriftFileCount { get; init; }
    public IReadOnlyList<string> PackagesAdded { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> PackagesRemoved { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> PackagesChanged { get; init; } = Array.Empty<string>();
    public bool PackagesDiffFromFreezeFile { get; init; }
    // PROC1-ID Phase 6b: basename under ZolaClient\logs when packages drifted — PROC1-D13
    public string? PackagesCaptureFileName { get; init; }

    public bool HasDrift =>
        HermesHeadDrift || HermesLocalEditsDrift || PackagesDrift || PluginsDrift;

    public static DriftCheckResult Incomplete(string reason) =>
        new() { Completed = false, IncompleteReason = reason };
}
