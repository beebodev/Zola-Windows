using System.Globalization;
using System.Management;

namespace Zola.Client.Supervision;

// S51F-FIX: resolve the interpreter child off the restart path; never block spawn — S51F-D06
public static class ChildPidLookup
{
    // S51F-FIX: retry window for uv → python spawn; still only on the async path — S51F-D06
    public const int TimeoutMs = 3_000;
    public const int RetryDelayMs = 100;
    public const int MaxDepth = 5;
    public const string Unknown = "unknown";

    public readonly record struct ProcessNode(int Pid, string Name);

    public static string TryResolve(
        int launcherPid,
        int timeoutMs = TimeoutMs,
        Func<int, IReadOnlyList<ProcessNode>>? listChildren = null)
    {
        listChildren ??= ListChildrenWmi;
        try
        {
            var task = Task.Run(() => ResolveWithRetries(launcherPid, timeoutMs, listChildren));
            if (!task.Wait(timeoutMs))
            {
                return Unknown;
            }

            return task.Result is int id && id > 0
                ? id.ToString(CultureInfo.InvariantCulture)
                : Unknown;
        }
        catch
        {
            return Unknown;
        }
    }

    // S51F-FIX: fire-and-forget so restart/backoff never waits on WMI — S51F-D06
    public static void WriteEventAsync(
        string proc,
        string eventName,
        int restarts,
        long generation,
        int launcherPid,
        Func<int, IReadOnlyList<ProcessNode>>? listChildren = null)
    {
        _ = Task.Run(() =>
        {
            var child = TryResolve(launcherPid, TimeoutMs, listChildren);
            SupervisionLog.Write(proc, eventName, restarts, generation, launcherPid, child);
        });
    }

    public static int? FindLeafPythonPid(
        int launcherPid,
        Func<int, IReadOnlyList<ProcessNode>> listChildren,
        int maxDepth = MaxDepth)
    {
        if (launcherPid <= 0)
        {
            return null;
        }

        int? best = null;
        var bestDepth = -1;

        void Walk(int pid, int depth)
        {
            if (depth >= maxDepth)
            {
                return;
            }

            IReadOnlyList<ProcessNode> children;
            try
            {
                children = listChildren(pid);
            }
            catch
            {
                return;
            }

            foreach (var child in children)
            {
                var childDepth = depth + 1;
                if (IsPythonExe(child.Name))
                {
                    IReadOnlyList<ProcessNode> grand;
                    try
                    {
                        grand = listChildren(child.Pid);
                    }
                    catch
                    {
                        grand = Array.Empty<ProcessNode>();
                    }

                    var hasPythonChild = false;
                    foreach (var g in grand)
                    {
                        if (IsPythonExe(g.Name))
                        {
                            hasPythonChild = true;
                            break;
                        }
                    }

                    if (!hasPythonChild && childDepth >= bestDepth)
                    {
                        bestDepth = childDepth;
                        best = child.Pid;
                    }
                }

                Walk(child.Pid, childDepth);
            }
        }

        Walk(launcherPid, 0);
        return best;
    }

    public static bool IsPythonExe(string? name)
    {
        if (string.IsNullOrEmpty(name))
        {
            return false;
        }

        // S51F-FIX: python*.exe leaf only — S51F-D06
        return name.StartsWith("python", StringComparison.OrdinalIgnoreCase)
            && name.EndsWith(".exe", StringComparison.OrdinalIgnoreCase);
    }

    public static IReadOnlyList<ProcessNode> ListChildrenWmi(int parentPid)
    {
        if (parentPid <= 0)
        {
            return Array.Empty<ProcessNode>();
        }

        var list = new List<ProcessNode>();
        try
        {
            using var searcher = new ManagementObjectSearcher(
                "SELECT ProcessId, Name FROM Win32_Process WHERE ParentProcessId="
                + parentPid.ToString(CultureInfo.InvariantCulture));
            foreach (var item in searcher.Get())
            {
                using var row = (ManagementObject)item;
                var pid = Convert.ToInt32(row["ProcessId"]);
                var name = row["Name"] as string ?? string.Empty;
                list.Add(new ProcessNode(pid, name));
            }
        }
        catch (ManagementException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }

        return list;
    }

    static int? ResolveWithRetries(
        int launcherPid,
        int timeoutMs,
        Func<int, IReadOnlyList<ProcessNode>> listChildren)
    {
        var deadline = Environment.TickCount64 + Math.Max(0, timeoutMs);
        while (true)
        {
            var found = FindLeafPythonPid(launcherPid, listChildren);
            if (found is int id && id > 0)
            {
                return id;
            }

            var left = deadline - Environment.TickCount64;
            if (left <= 0)
            {
                return null;
            }

            Thread.Sleep((int)Math.Min(RetryDelayMs, left));
        }
    }
}
