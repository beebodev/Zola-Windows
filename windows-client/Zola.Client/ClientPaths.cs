using Zola.Client.Identity;

namespace Zola.Client;

// PROC1-DEV: one path plan per role, built once after the role is known — PROC1-D4
public sealed class ClientPaths
{
    public const string ProfileStable = "zola";
    public const string ProfileDev = "zola-dev";
    public const string HermesFolderStable = "hermes";
    public const string HermesFolderDev = "hermes-dev";
    public const string ClientFolderStable = "ZolaClient";
    public const string ClientFolderDev = "ZolaClient-dev";
    public const string DeepgramEnvVar = "ZOLA_DEEPGRAM_KEY_PATH";
    public const string WakeModelRelativePath = @"cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01\tokens.txt";

    private readonly string[] _extraPlanPaths;

    private ClientPaths(
        string role,
        string localAppData,
        string profileDirectory,
        string[] extraPlanPaths)
    {
        Role = role;
        LocalAppData = Trim(localAppData);
        IsDev = !string.Equals(role, IdentityConstants.RoleStable, StringComparison.Ordinal);
        ProfileName = IsDev ? ProfileDev : ProfileStable;
        var clientFolder = IsDev ? ClientFolderDev : ClientFolderStable;
        var hermesFolder = IsDev ? HermesFolderDev : HermesFolderStable;
        ExpectedProfileDirectory = Combine(LocalAppData, HermesFolderDev, "profiles", ProfileDev);
        LiveProfileDirectory = Combine(LocalAppData, HermesFolderStable, "profiles", ProfileStable);
        NativeHermesRoot = Combine(LocalAppData, HermesFolderStable);
        LiveClientDataRoot = Combine(LocalAppData, ClientFolderStable);
        ProfileDirectory = string.IsNullOrEmpty(profileDirectory)
            ? Combine(LocalAppData, hermesFolder, "profiles", ProfileName)
            : Trim(profileDirectory);
        ClientDataRoot = Combine(LocalAppData, clientFolder);
        LogsDirectory = Combine(ClientDataRoot, "logs");
        SupervisorLogPath = Combine(LogsDirectory, "supervisor.log");
        ServeStderrDirectory = Combine(LogsDirectory, "serve-stderr");
        ServeStderrPath = Combine(ServeStderrDirectory, "serve-stderr.log");
        VoiceTimelinePath = Combine(LogsDirectory, "voice-timeline.log");
        DisplayStateLogPath = Combine(LogsDirectory, "display-state.log");
        ToolEventsLogPath = Combine(LogsDirectory, "tool-events.log");
        CodeReadLogPath = Combine(LogsDirectory, "code-read.log");
        ProactiveLogPath = Combine(LogsDirectory, "proactive.log");
        PresenceLogPath = Combine(LogsDirectory, "presence.log");
        ServerRequestsLogPath = Combine(LogsDirectory, "server-requests.log");
        DriftCaptureDirectory = LogsDirectory;
        DumpsDirectory = Combine(ClientDataRoot, "dumps");
        DebugDirectory = Combine(ClientDataRoot, "debug");
        SecretsDirectory = Combine(ClientDataRoot, "secrets");
        WakeTokenPath = Combine(ProfileDirectory, WakeModelRelativePath);
        WatcherOutputPath = Combine(ProfileDirectory, "logs", "zola_watcher.out.log");
        PhoneOutputPath = Combine(ProfileDirectory, "logs", "zola_phone.out.log");
        DeepgramKeyPath = Combine(LiveClientDataRoot, "secrets", "deepgram_api_key");
        HermesRootAuthPath = Combine(LocalAppData, hermesFolder, "auth.json");
        DevAuthPath = Combine(ProfileDirectory, "auth.json");
        ConfigPath = Combine(ProfileDirectory, "config.yaml");
        _extraPlanPaths = extraPlanPaths;
    }

    public static ClientPaths? Current { get; private set; }

    public string Role { get; }

    public bool IsDev { get; }

    public string LocalAppData { get; }

    public string ProfileName { get; }

    public string ProfileDirectory { get; }

    public string ExpectedProfileDirectory { get; }

    public string LiveProfileDirectory { get; }

    public string NativeHermesRoot { get; }

    public string LiveClientDataRoot { get; }

    public string ClientDataRoot { get; }

    public string LogsDirectory { get; }

    public string SupervisorLogPath { get; }

    public string ServeStderrDirectory { get; }

    public string ServeStderrPath { get; }

    public string VoiceTimelinePath { get; }

    public string DisplayStateLogPath { get; }

    public string ToolEventsLogPath { get; }

    public string CodeReadLogPath { get; }

    public string ProactiveLogPath { get; }

    public string PresenceLogPath { get; }

    public string ServerRequestsLogPath { get; }

    public string DriftCaptureDirectory { get; }

    public string DumpsDirectory { get; }

    public string DebugDirectory { get; }

    public string SecretsDirectory { get; }

    public string WakeTokenPath { get; }

    public string WatcherOutputPath { get; }

    public string PhoneOutputPath { get; }

    public string DeepgramKeyPath { get; }

    public string HermesRootAuthPath { get; }

    public string DevAuthPath { get; }

    public string ConfigPath { get; }

    public string PhonePluginDirectory => Path.Combine(ProfileDirectory, "plugins", "zola_phone");

    public IEnumerable<string> PlanPaths
    {
        get
        {
            yield return ProfileDirectory;
            yield return ClientDataRoot;
            yield return LogsDirectory;
            yield return ServeStderrDirectory;
            yield return DumpsDirectory;
            yield return DebugDirectory;
            yield return SecretsDirectory;
            yield return WakeTokenPath;
            yield return WatcherOutputPath;
            yield return PhoneOutputPath;
            yield return DeepgramKeyPath;
            yield return ConfigPath;
            yield return DevAuthPath;
            foreach (var extra in _extraPlanPaths)
            {
                yield return extra;
            }
        }
    }

    public static ClientPaths ForRole(string role) =>
        ForRole(role, Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData));

    public static ClientPaths ForRole(string role, string localAppData) =>
        new(role, localAppData, "", Array.Empty<string>());

    // PROC1-DEV: publish the plan only after dev validation has passed — PROC1-D4
    public static void Install(ClientPaths paths)
    {
        Current = paths ?? throw new ArgumentNullException(nameof(paths));
    }

    internal static void ResetForTests() => Current = null;

    internal ClientPaths WithExtraPlanPath(string path) =>
        new(Role, LocalAppData, ProfileDirectory, _extraPlanPaths.Append(path).ToArray());

    internal ClientPaths WithProfileDirectory(string profileDirectory) =>
        new(Role, LocalAppData, profileDirectory, _extraPlanPaths);

    public static bool TryGetLogsDirectory(out string directory) =>
        TryGet(static paths => paths.LogsDirectory, out directory);

    public static bool TryGetDebugDirectory(out string directory) =>
        TryGet(static paths => paths.DebugDirectory, out directory);

    public static bool TryGetDumpsDirectory(out string directory) =>
        TryGet(static paths => paths.DumpsDirectory, out directory);

    public static bool TryGetWakeTokenPath(out string path) =>
        TryGet(static paths => paths.WakeTokenPath, out path);

    public bool IsUnderLive(string path) =>
        IsUnder(path, LiveProfileDirectory) || IsUnder(path, LiveClientDataRoot);

    public bool IsUnderDev(string path) =>
        IsUnder(path, ExpectedProfileDirectory) || IsUnder(path, ClientDataRoot);

    public static bool IsUnder(string path, string root)
    {
        if (string.IsNullOrWhiteSpace(path) || string.IsNullOrWhiteSpace(root))
        {
            return false;
        }

        var full = Normalize(path);
        var baseRoot = Normalize(root);
        if (string.Equals(full, baseRoot, StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return full.StartsWith(baseRoot + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase);
    }

    public static bool PathsEqual(string left, string right) =>
        string.Equals(Normalize(left), Normalize(right), StringComparison.OrdinalIgnoreCase);

    public static string Normalize(string path)
    {
        var full = Path.GetFullPath(path);
        return full.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    }

    private static bool TryGet(Func<ClientPaths, string> select, out string path)
    {
        var current = Current;
        if (current is null)
        {
            path = "";
            return false;
        }

        path = select(current);
        return !string.IsNullOrEmpty(path);
    }

    private static string Combine(params string[] parts) => Path.Combine(parts);

    private static string Trim(string path) =>
        path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
}
