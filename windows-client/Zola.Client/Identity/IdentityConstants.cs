namespace Zola.Client.Identity;

// PROC1-ID: named constants for lock, role, and drift — PROC1-D7 / PROC1-D13
public static class IdentityConstants
{
    public const string MutexName = @"Local\ZolaClient";
    public const string StatusRelativeDir = @"Zola\run";
    public const string StatusFileName = "instance.json";
    public const string RoleFileName = "build-role.json";
    public const string ManifestFileName = "stable-manifest.json";
    public const string RoleStable = "stable";
    public const string RoleDev = "dev";

    public const string RefuseTitle = "Zola";
    public const string RefuseStableFormat = "Zola (stable, {0}) is already running. Close it before starting another.";
    public const string RefuseDevText = "Zola (dev) is already running. Close it before starting another.";
    public const string RefuseUnknownText = "Another Zola is already running. Close it before starting another.";

    public const string DriftNoticePrefix = "Zola's installed parts have changed since this build was promoted";
    public const string DriftLabelHermes = "Hermes code";
    public const string DriftLabelPackages = "Python packages";
    public const string DriftLabelPlugins = "plugins";

    public const string ComponentHermesHead = "hermes_head";
    public const string ComponentHermesLocalEdits = "hermes_local_edits";
    public const string ComponentPackages = "packages";
    public const string ComponentPlugins = "plugins";

    public const string AlgoLocalEditV2 = "v2-content";
    public const string AlgoLocalEditV1 = "v1-porcelain"; // script golden / legacy manifests only
    public const string AlgoPipFreezeV1 = "v1-pip-freeze"; // script golden / legacy manifests only
    public const string AlgoPipFreezeV2 = "v2-pip-freeze-clean";

    public static readonly TimeSpan DriftTimeout = TimeSpan.FromSeconds(10);
}
