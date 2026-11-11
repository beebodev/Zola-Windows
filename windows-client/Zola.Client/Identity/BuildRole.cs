using System.Diagnostics;
using System.Text.Json;

namespace Zola.Client.Identity;

// PROC1-ID: resolve stable vs dev from build-role.json + embedded commit — PROC1-D7
public sealed record BuildRoleInfo(string Role, string? Tag, string? Commit, string? Manifest, string Why);

public static class BuildRole
{
    public static BuildRoleInfo Resolve(string baseDirectory, string? productVersion = null)
    {
        var path = Path.Combine(baseDirectory, IdentityConstants.RoleFileName);
        if (!File.Exists(path))
        {
            return new BuildRoleInfo(IdentityConstants.RoleDev, null, null, null, "missing");
        }

        string json;
        try
        {
            json = File.ReadAllText(path);
        }
        catch
        {
            return new BuildRoleInfo(IdentityConstants.RoleDev, null, null, null, "unreadable");
        }

        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            var role = root.TryGetProperty("role", out var r) ? r.GetString() : null;
            var tag = root.TryGetProperty("tag", out var t) ? t.GetString() : null;
            var commit = root.TryGetProperty("commit", out var c) ? c.GetString() : null;
            var manifest = root.TryGetProperty("manifest", out var m) ? m.GetString() : null;
            if (!string.Equals(role, IdentityConstants.RoleStable, StringComparison.Ordinal))
            {
                return new BuildRoleInfo(IdentityConstants.RoleDev, tag, commit, manifest, "role");
            }

            var embedded = ExtractEmbeddedCommit(productVersion ?? ReadProductVersion(baseDirectory));
            if (string.IsNullOrEmpty(embedded))
            {
                return new BuildRoleInfo(IdentityConstants.RoleDev, tag, commit, manifest, "no_embedded_commit");
            }

            if (!string.Equals(commit, embedded, StringComparison.OrdinalIgnoreCase))
            {
                return new BuildRoleInfo(IdentityConstants.RoleDev, tag, commit, manifest, "commit_mismatch");
            }

            return new BuildRoleInfo(IdentityConstants.RoleStable, tag, commit, manifest ?? IdentityConstants.ManifestFileName, "ok");
        }
        catch
        {
            return new BuildRoleInfo(IdentityConstants.RoleDev, null, null, null, "unreadable");
        }
    }

    public static string? ExtractEmbeddedCommit(string? productVersion)
    {
        if (string.IsNullOrEmpty(productVersion))
        {
            return null;
        }

        var plus = productVersion.IndexOf('+');
        if (plus < 0 || plus + 1 >= productVersion.Length)
        {
            return null;
        }

        return productVersion[(plus + 1)..].Trim();
    }

    public static string? ReadProductVersion(string baseDirectory)
    {
        try
        {
            var dll = Path.Combine(baseDirectory, "Zola.Client.dll");
            if (!File.Exists(dll))
            {
                dll = Path.Combine(baseDirectory, "Zola.Client.exe");
            }

            if (!File.Exists(dll))
            {
                return null;
            }

            return FileVersionInfo.GetVersionInfo(dll).ProductVersion;
        }
        catch
        {
            return null;
        }
    }
}
