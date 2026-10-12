using System.Diagnostics;
using System.Management;

namespace Zola.Client;

public sealed partial class HermesProcessManager
{
    // P9-SUPERVISE: a failed start must not latch app shutdown, or a later restart cannot spawn — P9-D02
    private void StopSpawnedChild()
    {
        Process? child;
        lock (_gate)
        {
            child = _child;
            _child = null;
            OwnsProcess = false;
            ServeProcessId = null;
        }

        if (child is not null)
        {
            TryKill(child);
        }
    }

    // P9-SUPERVISE: one dedicated zola serve per machine, so a restart kills every match, same as attach — P9-D02 / P1-D01
    public void KillGenerationForRestart()
    {
        Volatile.Write(ref _ignoreExitGeneration, Generations.ProcessGeneration);
        Process? child;
        lock (_gate)
        {
            child = _child;
            _child = null;
            OwnsProcess = false;
            ServeProcessId = null;
            HealthPassed = false;
            SessionToken = null;
            Port = null;
        }

        if (child is not null)
        {
            TryKill(child);
        }

        foreach (var pid in FindDedicatedServePids())
        {
            TryKillPid(pid);
        }
    }

    // P9-SUPERVISE: alive means any dedicated zola serve, including a reparented child of the one serve — P9-D02 / P1-D01
    public bool IsServeProcessAlive()
    {
        var pid = ServeProcessId;
        if (pid is int tracked && PidAlive(tracked))
        {
            return true;
        }

        return FindDedicatedServePids().Count > 0;
    }

    public bool IsTrackedProcessAlive()
    {
        var pid = ServeProcessId;
        return pid is int tracked && PidAlive(tracked);
    }

    private static bool PidAlive(int pid)
    {
        try
        {
            using var process = Process.GetProcessById(pid);
            return !process.HasExited;
        }
        catch (ArgumentException)
        {
            return false;
        }
        catch (InvalidOperationException)
        {
            return false;
        }
    }

    private static void TryKillPid(int pid)
    {
        try
        {
            using var process = Process.GetProcessById(pid);
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
            }
        }
        catch (ArgumentException)
        {
        }
        catch (InvalidOperationException)
        {
        }
        catch (System.ComponentModel.Win32Exception)
        {
        }
    }

    private static List<int> FindDedicatedServePids()
    {
        var pids = new List<int>();
        try
        {
            using var searcher = new ManagementObjectSearcher(
                "SELECT ProcessId, CommandLine FROM Win32_Process WHERE CommandLine LIKE '%--isolated%'");
            foreach (var item in searcher.Get())
            {
                using var row = (ManagementObject)item;
                var commandLine = row["CommandLine"] as string ?? "";
                if (!ZolaServeCommand.IsDedicatedServe(commandLine))
                {
                    continue;
                }

                pids.Add(Convert.ToInt32(row["ProcessId"]));
            }
        }
        catch (ManagementException)
        {
        }

        return pids;
    }
}
