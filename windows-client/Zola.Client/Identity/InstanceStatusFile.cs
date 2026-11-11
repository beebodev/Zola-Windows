using System.Text;
using System.Text.Json;

namespace Zola.Client.Identity;

// PROC1-ID: status file outside ZolaClient / profile roots — PROC1-D7
public sealed record InstanceStatus(string Role, string? Tag, int Pid, string Exe, string StartedAt);

public static class InstanceStatusFile
{
    public static string DefaultPath =>
        Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            IdentityConstants.StatusRelativeDir,
            IdentityConstants.StatusFileName);

    public static void WriteAtomic(string path, InstanceStatus status)
    {
        var dir = Path.GetDirectoryName(path)!;
        Directory.CreateDirectory(dir);
        var json = JsonSerializer.Serialize(new
        {
            role = status.Role,
            tag = status.Tag,
            pid = status.Pid,
            exe = status.Exe,
            started_at = status.StartedAt,
        });
        var tmp = path + ".tmp";
        File.WriteAllText(tmp, json, Encoding.UTF8);
        // PROC1-ID: atomic replace — PROC1-D7
        File.Move(tmp, path, overwrite: true);
    }

    public static InstanceStatus? TryRead(string path)
    {
        try
        {
            if (!File.Exists(path))
            {
                return null;
            }

            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var root = doc.RootElement;
            var role = root.TryGetProperty("role", out var r) ? r.GetString() ?? "" : "";
            var tag = root.TryGetProperty("tag", out var t) ? t.GetString() : null;
            var pid = root.TryGetProperty("pid", out var p) ? p.GetInt32() : 0;
            var exe = root.TryGetProperty("exe", out var e) ? e.GetString() ?? "" : "";
            var started = root.TryGetProperty("started_at", out var s) ? s.GetString() ?? "" : "";
            return new InstanceStatus(role, tag, pid, exe, started);
        }
        catch
        {
            return null;
        }
    }

    public static void TryDelete(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch
        {
        }
    }
}
