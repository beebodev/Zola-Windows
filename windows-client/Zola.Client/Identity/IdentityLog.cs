using Zola.Client.Supervision;

namespace Zola.Client.Identity;

// PROC1-ID: persistent identity/drift lines via SupervisionLog → %LOCALAPPDATA%\ZolaClient\logs\supervisor.log — PROC1-D7 / PROC1-D13
public static class IdentityLog
{
    public static string RoleLine(string role, string why, string? tag) =>
        $"identity role={role} why={why} tag={tag ?? ""}";

    public static string StatusWriteOk() => "identity status_write ok";

    public static string StatusWriteFailed(string reason) =>
        $"identity status_write failed reason={reason}";

    public static string DriftCompletedNone() => "drift completed=true components=none";

    public static string DriftCompleted(IReadOnlyList<string> components, int? pluginFiles)
    {
        var keys = string.Join(",", components);
        var line = $"drift completed=true components={keys}";
        if (pluginFiles is int n)
        {
            line += $" plugin_files={n}";
        }

        return line;
    }

    public static string DriftIncomplete(string reason) =>
        $"drift completed=false reason={reason}";

    // PROC1-ID Phase 4c: names/versions only when pip-freeze.txt exists — PROC1-D13
    public static string DriftPackagesDiff(
        IReadOnlyList<string> added,
        IReadOnlyList<string> removed,
        IReadOnlyList<string> changed)
    {
        return "drift packages"
            + " added=" + (added.Count == 0 ? "none" : string.Join(",", added))
            + " removed=" + (removed.Count == 0 ? "none" : string.Join(",", removed))
            + " changed=" + (changed.Count == 0 ? "none" : string.Join(",", changed));
    }

    // PROC1-ID Phase 6b: one packages_capture file name per launch when packages differ — PROC1-D13
    public static string DriftPackagesCapture(string fileName) =>
        $"drift packages_capture={fileName}";

    public static string ReleaseAfterWait(string child) =>
        $"identity release_after_wait child={child} alive=true";

    public static void Write(string line) => SupervisionLog.WriteLine(line);
}
