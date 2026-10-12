using System.Diagnostics;
using System.Security.Principal;
using System.Text;
using Zola.Client.Supervision;

namespace Zola.Client;

// P9-SUPERVISE: serve stderr stays on disk with a size cap, file count, and retention — P9-D02
public sealed class ServeStderrLog
{
    private readonly object _gate = new();
    private readonly string _directory;
    private bool _aclApplied;
    private bool _aclFailureLogged;

    public ServeStderrLog()
    {
        _directory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "ZolaClient",
            "logs",
            "serve-stderr");
    }

    public void WriteLine(string? line)
    {
        if (string.IsNullOrEmpty(line))
        {
            return;
        }

        try
        {
            lock (_gate)
            {
                Directory.CreateDirectory(_directory);
                if (!EnsureAcl())
                {
                    // P9-SUPERVISE: the pipe is already drained; a failed ACL must not create the log file — P9-D02
                    return;
                }

                PruneExpired();
                var path = Path.Combine(_directory, "serve-stderr.log");
                var existing = File.Exists(path) ? new FileInfo(path).Length : 0;
                if (Supervision.SupervisionConstants.StderrShouldRotate(existing))
                {
                    Rotate(path);
                }

                File.AppendAllText(path, line + Environment.NewLine, Encoding.UTF8);
            }
        }
        catch
        {
        }
    }

    private bool EnsureAcl()
    {
        if (_aclApplied)
        {
            return true;
        }

        // P9-SUPERVISE: the client writes stderr as the interactive user, so only that user is granted — P9-D02
        var user = WindowsIdentity.GetCurrent().Name;
        var inheritance = RunIcacls(_directory, "/inheritance:r");
        var grant = RunIcacls(_directory, "/grant:r", user + ":(OI)(CI)F");
        var decision = StderrAcl.Evaluate(_aclApplied, _aclFailureLogged, inheritance, grant);
        _aclApplied = decision.Applied;
        if (decision.LogFailure)
        {
            _aclFailureLogged = true;
            SupervisionLog.Write(SupervisionConstants.ProcServe, SupervisionConstants.EventStderrAclFailed, 0, 0);
        }

        return decision.MayWrite;
    }

    private void PruneExpired()
    {
        var now = DateTimeOffset.UtcNow;
        foreach (var file in Directory.EnumerateFiles(_directory))
        {
            var info = new FileInfo(file);
            if (info.Attributes.HasFlag(FileAttributes.ReparsePoint))
            {
                continue;
            }

            if (Supervision.SupervisionConstants.RetentionExpired(info.LastWriteTimeUtc, now, Supervision.SupervisionConstants.ServeStderrRetentionDays))
            {
                info.Delete();
            }
        }
    }

    private void Rotate(string path)
    {
        var oldest = Path.Combine(_directory, "serve-stderr.log." + Supervision.SupervisionConstants.ServeStderrMaxFiles);
        if (File.Exists(oldest))
        {
            File.Delete(oldest);
        }

        for (var index = Supervision.SupervisionConstants.ServeStderrMaxFiles - 1; index >= 1; index--)
        {
            var from = Path.Combine(_directory, "serve-stderr.log." + index);
            var to = Path.Combine(_directory, "serve-stderr.log." + (index + 1));
            if (File.Exists(from))
            {
                File.Move(from, to, overwrite: true);
            }
        }

        if (File.Exists(path))
        {
            File.Move(path, Path.Combine(_directory, "serve-stderr.log.1"), overwrite: true);
        }
    }

    private static int? RunIcacls(string directory, params string[] args)
    {
        try
        {
            var start = new ProcessStartInfo
            {
                FileName = "icacls",
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            start.ArgumentList.Add(directory);
            foreach (var arg in args)
            {
                start.ArgumentList.Add(arg);
            }

            using var process = Process.Start(start);
            if (process is null || !process.WaitForExit(5_000))
            {
                return null;
            }

            return process.ExitCode;
        }
        catch
        {
            return null;
        }
    }
}
