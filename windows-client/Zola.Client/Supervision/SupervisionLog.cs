using System.Globalization;
using System.Text;

namespace Zola.Client.Supervision;

// P9-SUPERVISE: restart lines are metadata only; stderr and dumps stay out of this file — P9-D02
public static class SupervisionLog
{
    public static string Format(string proc, string eventName, int restarts, long generation)
    {
        return Format(proc, eventName, restarts, generation, null);
    }

    public static string Format(string proc, string eventName, int restarts, long generation, int? pid)
    {
        var line = "supervisor proc=" + proc
            + " event=" + eventName
            + " restarts=" + restarts.ToString(CultureInfo.InvariantCulture)
            + " generation=" + generation.ToString(CultureInfo.InvariantCulture);
        if (pid is int value)
        {
            line += " pid=" + value.ToString(CultureInfo.InvariantCulture);
        }

        return line;
    }

    public static void Write(string proc, string eventName, int restarts, long generation)
    {
        Write(proc, eventName, restarts, generation, null);
    }

    public static void Write(string proc, string eventName, int restarts, long generation, int? pid)
    {
        var line = Format(proc, eventName, restarts, generation, pid);
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
