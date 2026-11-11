using System.Collections;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;

namespace Zola.Client.Identity;

// PROC1-ID: digests matching StableCommon.psm1 byte-for-byte — PROC1-D13
public static class HermesDigests
{
    public enum EnvCleanMode
    {
        None,
        Python,
        Git,
    }

    private static readonly UTF8Encoding Utf8NoBom = new(encoderShouldEmitUTF8Identifier: false);

    public static string Sha256HexUtf8(string text)
    {
        var bytes = Encoding.UTF8.GetBytes(text);
        var hash = SHA256.HashData(bytes);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    public static string Sha256HexFile(string path)
    {
        using var stream = File.OpenRead(path);
        var hash = SHA256.HashData(stream);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    public sealed record CaptureResult(bool Ok, string? Text, string? Reason, int ExitCode);

    public static CaptureResult Capture(
        string filePath,
        IEnumerable<string> args,
        int timeoutMs,
        string? workingDirectory = null,
        EnvCleanMode envClean = EnvCleanMode.None)
    {
        if (!File.Exists(filePath))
        {
            return new CaptureResult(false, null, "missing:" + filePath, -1);
        }

        var psi = new ProcessStartInfo
        {
            FileName = filePath,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            StandardOutputEncoding = Utf8NoBom,
            StandardErrorEncoding = Utf8NoBom,
        };
        if (!string.IsNullOrWhiteSpace(workingDirectory))
        {
            psi.WorkingDirectory = workingDirectory;
        }

        foreach (var a in args)
        {
            psi.ArgumentList.Add(a);
        }

        ApplyEnvClean(psi, envClean);

        using var p = Process.Start(psi);
        if (p is null)
        {
            return new CaptureResult(false, null, "start_failed", -1);
        }

        var stdoutTask = p.StandardOutput.ReadToEndAsync();
        var stderrTask = p.StandardError.ReadToEndAsync();
        if (!p.WaitForExit(timeoutMs))
        {
            try { p.Kill(entireProcessTree: true); } catch { }
            return new CaptureResult(false, null, "timeout:" + timeoutMs, -1);
        }

        var text = stdoutTask.GetAwaiter().GetResult();
        _ = stderrTask.GetAwaiter().GetResult();
        if (p.ExitCode != 0)
        {
            return new CaptureResult(false, null, "exit:" + p.ExitCode, p.ExitCode);
        }

        return new CaptureResult(true, text, null, 0);
    }

    private static void ApplyEnvClean(ProcessStartInfo psi, EnvCleanMode mode)
    {
        if (mode == EnvCleanMode.None)
        {
            return;
        }

        // Rebuild env so removals stick (ProcessStartInfo starts as a copy of the parent).
        var keep = new List<KeyValuePair<string, string>>();
        foreach (DictionaryEntry entry in Environment.GetEnvironmentVariables())
        {
            var key = (string)entry.Key!;
            if (mode == EnvCleanMode.Python && ShouldOmitPythonEnv(key))
            {
                continue;
            }

            if (mode == EnvCleanMode.Git && key.StartsWith("GIT_", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            keep.Add(new KeyValuePair<string, string>(key, Convert.ToString(entry.Value) ?? ""));
        }

        psi.Environment.Clear();
        foreach (var kv in keep)
        {
            psi.Environment[kv.Key] = kv.Value;
        }

        if (mode == EnvCleanMode.Python)
        {
            psi.Environment["PYTHONUTF8"] = "1";
        }
    }

    private static bool ShouldOmitPythonEnv(string key)
    {
        if (key.Equals("PYTHONPATH", StringComparison.OrdinalIgnoreCase)
            || key.Equals("PYTHONHOME", StringComparison.OrdinalIgnoreCase)
            || key.Equals("PYTHONSTARTUP", StringComparison.OrdinalIgnoreCase)
            || key.Equals("PYTHONUSERBASE", StringComparison.OrdinalIgnoreCase)
            || key.Equals("VIRTUAL_ENV", StringComparison.OrdinalIgnoreCase)
            || key.Equals("PYTHONNOUSERSITE", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return key.StartsWith("PIP_", StringComparison.OrdinalIgnoreCase);
    }

    public static string? FindGit()
    {
        var path = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (var dir in path.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            var exe = Path.Combine(dir, "git.exe");
            if (File.Exists(exe))
            {
                return exe;
            }
        }

        var guess = @"C:\Program Files\Git\cmd\git.exe";
        return File.Exists(guess) ? guess : null;
    }

    // PROC1-ID Phase 4c: match proc1-stable `(cmd lines) -join "\n"` (no trailing LF) — PROC1-D13
    public static string JoinAsV1CommandOutput(string? text)
    {
        var normalized = (text ?? "").Replace("\r\n", "\n").Replace("\r", "\n");
        return normalized.TrimEnd('\n');
    }

    public static CaptureResult LocalEditDigestV1(string hermesRoot, string gitPath, int timeoutMs = 30000)
    {
        // Script-only golden path; client never runs v1 — PROC1-D13
        var cap = Capture(gitPath, new[] { "-C", hermesRoot, "status", "--porcelain" }, timeoutMs);
        if (!cap.Ok)
        {
            return cap;
        }

        var joined = JoinAsV1CommandOutput(cap.Text);
        return new CaptureResult(true, Sha256HexUtf8(joined), null, 0);
    }

    public static CaptureResult LocalEditDigestV2(string hermesRoot, string gitPath, int timeoutMs = 30000)
    {
        // PROC1-ID Phase 6b: WD=hermesRoot; strip GIT_* — PROC1-D13
        var cap = Capture(
            gitPath,
            new[] { "-C", hermesRoot, "status", "--porcelain=v1", "-z", "--untracked-files=all" },
            timeoutMs,
            workingDirectory: hermesRoot,
            envClean: EnvCleanMode.Git);
        if (!cap.Ok)
        {
            return cap;
        }

        var raw = cap.Text ?? "";
        var entries = new List<string>();
        var parts = raw.Split('\0');
        for (var i = 0; i < parts.Length; i++)
        {
            var chunk = parts[i];
            if (string.IsNullOrEmpty(chunk) || chunk.Length < 3)
            {
                continue;
            }

            var code = chunk[..2];
            var path = chunk[3..];
            if (code.Contains('R') || code.Contains('C'))
            {
                i++;
                if (i < parts.Length && !string.IsNullOrEmpty(parts[i]))
                {
                    path = parts[i];
                }
            }

            var full = Path.Combine(hermesRoot, path.Replace('/', Path.DirectorySeparatorChar));
            var payload = File.Exists(full) ? Sha256HexFile(full) : "deleted";
            entries.Add($"{code}|{path.Replace('\\', '/')}|{payload}");
        }

        entries.Sort(StringComparer.Ordinal);
        var text = entries.Count == 0 ? "" : string.Join("\n", entries) + "\n";
        return new CaptureResult(true, Sha256HexUtf8(text), null, 0);
    }

    // Text = v1-joined (hashed); RawText = stdout as captured (packages_capture) — PROC1-D13
    public sealed record FreezeResult(bool Ok, string? Digest, string? Text, string? Reason, int ExitCode, string? RawText = null);

    // PROC1-ID Phase 6b: v2-pip-freeze-clean — PROC1-D13
    public static FreezeResult PipFreeze(string hermesRoot, int timeoutMs = 60000)
    {
        var py = Path.Combine(hermesRoot, ".venv", "Scripts", "python.exe");
        var cap = Capture(
            py,
            new[] { "-m", "pip", "freeze" },
            timeoutMs,
            workingDirectory: hermesRoot,
            envClean: EnvCleanMode.Python);
        if (!cap.Ok)
        {
            return new FreezeResult(false, null, null, cap.Reason, cap.ExitCode);
        }

        var raw = cap.Text ?? "";
        var joined = JoinAsV1CommandOutput(raw);
        return new FreezeResult(true, Sha256HexUtf8(joined), joined, null, 0, raw);
    }

    public static CaptureResult PipFreezeDigest(string hermesRoot, int timeoutMs = 60000)
    {
        var freeze = PipFreeze(hermesRoot, timeoutMs);
        return freeze.Ok
            ? new CaptureResult(true, freeze.Digest, null, 0)
            : new CaptureResult(false, null, freeze.Reason, freeze.ExitCode);
    }

    public static CaptureResult RevParseHead(string hermesRoot, string gitPath, int timeoutMs = 30000)
    {
        var cap = Capture(
            gitPath,
            new[] { "-C", hermesRoot, "rev-parse", "HEAD" },
            timeoutMs,
            workingDirectory: hermesRoot,
            envClean: EnvCleanMode.Git);
        if (!cap.Ok)
        {
            return cap;
        }

        var head = (cap.Text ?? "").Replace("\r\n", "\n").Split('\n')[0].Trim();
        return new CaptureResult(true, head, null, 0);
    }
}
