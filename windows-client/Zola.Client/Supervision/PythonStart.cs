using System.Diagnostics;

namespace Zola.Client.Supervision;

// P10-INTAKE: one start plan for the watcher and zola-phone — P10-D12
public static class PythonStart
{
    public const string SecretEnv = "ZOLA_PHONE_LAUNCH_SECRET";

    public static ProcessStartInfo Build(
        string pythonPath,
        string hermesRoot,
        string profileDirectory,
        string module,
        string parentEnv,
        int parentPid,
        string? launchSecret)
    {
        var start = new ProcessStartInfo
        {
            FileName = pythonPath,
            WorkingDirectory = hermesRoot,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        start.ArgumentList.Add("-m");
        start.ArgumentList.Add(module);
        start.Environment["HERMES_HOME"] = profileDirectory;
        start.Environment["PYTHONUNBUFFERED"] = "1";
        start.Environment[parentEnv] = parentPid.ToString();
        var plugins = Path.Combine(profileDirectory, "plugins");
        start.Environment["PYTHONPATH"] = plugins + Path.PathSeparator + hermesRoot;
        if (!string.IsNullOrEmpty(launchSecret))
        {
            start.Environment[SecretEnv] = launchSecret;
        }

        return start;
    }
}
