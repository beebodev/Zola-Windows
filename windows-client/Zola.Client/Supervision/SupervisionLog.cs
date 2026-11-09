using System.Globalization;
using System.Text;

namespace Zola.Client.Supervision;

// P9-SUPERVISE: restart lines are metadata only; stderr and dumps stay out of this file — P9-D02
public static class SupervisionLog
{
    public static string Format(string proc, string eventName, int restarts, long generation)
    {
        return Format(proc, eventName, restarts, generation, null, null);
    }

    public static string Format(
        string proc,
        string eventName,
        int restarts,
        long generation,
        int? launcherPid,
        string? childPid = null)
    {
        var line = "supervisor proc=" + proc
            + " event=" + eventName
            + " restarts=" + restarts.ToString(CultureInfo.InvariantCulture)
            + " generation=" + generation.ToString(CultureInfo.InvariantCulture);
        // S51F-FIX: launcher and optional interpreter child — S51F-D06
        if (launcherPid is int launcher)
        {
            line += " launcher_pid=" + launcher.ToString(CultureInfo.InvariantCulture);
        }

        if (!string.IsNullOrEmpty(childPid))
        {
            line += " child_pid=" + childPid;
        }

        return line;
    }

    public static void Write(string proc, string eventName, int restarts, long generation)
    {
        Write(proc, eventName, restarts, generation, null, null);
    }

    public static void Write(
        string proc,
        string eventName,
        int restarts,
        long generation,
        int? launcherPid,
        string? childPid = null)
    {
        var line = Format(proc, eventName, restarts, generation, launcherPid, childPid);
        try
        {
            var root = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ZolaClient",
                "logs");
            Directory.CreateDirectory(root);
            File.AppendAllText(
                Path.Combine(root, "supervisor.log"),
                DateTimeOffset.Now.ToString("o", CultureInfo.InvariantCulture) + " " + line + Environment.NewLine,
                Encoding.UTF8);
        }
        catch
        {
        }
    }
}
