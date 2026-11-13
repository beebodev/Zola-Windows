using System.Text.Json;
using System.Text.RegularExpressions;

namespace Zola.Client.Identity;

internal interface IDevProfileIo
{
    bool DirectoryExists(string path);

    bool FileExists(string path);

    string? ReadAllText(string path);

    string? LinkTarget(string path);

    bool ContainsAnyFile(string directory);
}

internal static class DevProfileIo
{
    public static IDevProfileIo Real { get; } = new RealDevProfileIo();

    private sealed class RealDevProfileIo : IDevProfileIo
    {
        public bool DirectoryExists(string path) => Directory.Exists(path);

        public bool FileExists(string path) => File.Exists(path);

        public string? ReadAllText(string path)
        {
            if (!File.Exists(path))
            {
                return null;
            }

            return File.ReadAllText(path);
        }

        public string? LinkTarget(string path)
        {
            if (!File.Exists(path) && !Directory.Exists(path))
            {
                return null;
            }

            var attributes = File.GetAttributes(path);
            if ((attributes & FileAttributes.ReparsePoint) == 0)
            {
                return null;
            }

            FileSystemInfo info = (attributes & FileAttributes.Directory) != 0
                ? new DirectoryInfo(path)
                : new FileInfo(path);
            return info.LinkTarget;
        }

        public bool ContainsAnyFile(string directory)
        {
            if (!Directory.Exists(directory))
            {
                return false;
            }

            foreach (var _ in Directory.EnumerateFiles(directory, "*", new EnumerationOptions
            {
                RecurseSubdirectories = true,
                IgnoreInaccessible = true,
                AttributesToSkip = 0,
                ReturnSpecialDirectories = false,
            }))
            {
                return true;
            }

            return false;
        }
    }
}

// PROC1-DEV: dev refuses before any write when the plan is not the dev profile — PROC1-D4 / PROC1-D5 / PROC1-D6
public static class DevProfileValidation
{
    public static bool TryValidate(ClientPaths paths, out DevProfileFailure failure, out int codexCount) =>
        TryValidate(paths, DevProfileIo.Real, out failure, out codexCount);

    internal static bool TryValidate(
        ClientPaths paths,
        IDevProfileIo io,
        out DevProfileFailure failure,
        out int codexCount)
    {
        failure = DevProfileFailure.MissingFolder;
        codexCount = 0;
        if (!io.DirectoryExists(paths.ProfileDirectory))
        {
            failure = DevProfileFailure.MissingFolder;
            return false;
        }

        var resolvedProfile = ResolveFinal(paths.ProfileDirectory, io);
        if (ClientPaths.IsUnder(resolvedProfile, paths.NativeHermesRoot)
            || !ClientPaths.PathsEqual(resolvedProfile, paths.ExpectedProfileDirectory))
        {
            failure = DevProfileFailure.NotDevProfile;
            return false;
        }

        foreach (var plan in paths.PlanPaths)
        {
            if (ClientPaths.PathsEqual(plan, paths.DeepgramKeyPath))
            {
                continue;
            }

            if (!paths.IsUnderDev(plan))
            {
                failure = DevProfileFailure.PathPointsAtLive;
                return false;
            }
        }

        if (io.LinkTarget(paths.DeepgramKeyPath) is not null)
        {
            failure = DevProfileFailure.LinkIntoLive;
            return false;
        }

        foreach (var plan in paths.PlanPaths)
        {
            if (LinksIntoLive(plan, paths, io))
            {
                failure = DevProfileFailure.LinkIntoLive;
                return false;
            }
        }

        if (io.DirectoryExists(paths.PhonePluginDirectory))
        {
            failure = DevProfileFailure.PhonePluginPresent;
            return false;
        }

        if (io.ContainsAnyFile(Path.Combine(paths.ProfileDirectory, "pairing"))
            || io.ContainsAnyFile(Path.Combine(paths.ProfileDirectory, "phone")))
        {
            failure = DevProfileFailure.PhonePairingFiles;
            return false;
        }

        var devAuth = io.ReadAllText(paths.DevAuthPath);
        if (devAuth is not null)
        {
            codexCount = CountCodexEntries(devAuth);
        }

        if (io.FileExists(paths.HermesRootAuthPath) && codexCount < 1)
        {
            failure = DevProfileFailure.NoOwnModelCredential;
            codexCount = 0;
            return false;
        }

        var config = io.ReadAllText(paths.ConfigPath);
        if (config is not null && DevConfigScan.PointsAtLive(config, paths))
        {
            failure = DevProfileFailure.SettingsPointAtLive;
            return false;
        }

        return true;
    }

    internal static int CountCodexEntries(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var count = 0;
            if (doc.RootElement.TryGetProperty("providers", out var providers)
                && providers.ValueKind == JsonValueKind.Object
                && providers.TryGetProperty("openai-codex", out var block)
                && block.ValueKind == JsonValueKind.Object)
            {
                count += 1;
            }

            if (doc.RootElement.TryGetProperty("credential_pool", out var pool)
                && pool.ValueKind == JsonValueKind.Object
                && pool.TryGetProperty("openai-codex", out var entries)
                && entries.ValueKind == JsonValueKind.Array)
            {
                count += entries.GetArrayLength();
            }

            return count;
        }
        catch (JsonException)
        {
            return 0;
        }
    }

    internal static string ResolveFinal(string path, IDevProfileIo io)
    {
        var current = ClientPaths.Normalize(path);
        for (var i = 0; i < 32; i++)
        {
            var target = io.LinkTarget(current);
            if (string.IsNullOrEmpty(target))
            {
                return current;
            }

            current = ClientPaths.Normalize(Path.IsPathRooted(target)
                ? target
                : Path.Combine(Path.GetDirectoryName(current) ?? current, target));
        }

        return current;
    }

    private static bool LinksIntoLive(string path, ClientPaths paths, IDevProfileIo io)
    {
        var cursor = path;
        for (var i = 0; i < 64 && !string.IsNullOrEmpty(cursor); i++)
        {
            var target = io.LinkTarget(cursor);
            if (!string.IsNullOrEmpty(target))
            {
                var full = Path.IsPathRooted(target)
                    ? target
                    : Path.Combine(Path.GetDirectoryName(cursor) ?? cursor, target);
                var final = ResolveFinal(full, io);
                if (paths.IsUnderLive(full) || paths.IsUnderLive(final))
                {
                    return true;
                }
            }

            var parent = Path.GetDirectoryName(ClientPaths.Normalize(cursor));
            if (string.IsNullOrEmpty(parent) || ClientPaths.PathsEqual(parent, cursor))
            {
                break;
            }

            cursor = parent;
        }

        return false;
    }
}

// PROC1-DEV: dev settings must not name the live profile or ZolaClient — PROC1-D4
internal static partial class DevConfigScan
{
    public static bool PointsAtLive(string text, ClientPaths paths)
    {
        if (string.IsNullOrEmpty(text))
        {
            return false;
        }

        // PROC1-DEV: the shared Deepgram key path is the D5 exception and stays in config — PROC1-D5
        var scanned = SharedKeyPath().Replace(text, "");
        if (ProfileMarker().IsMatch(scanned) || ClientMarker().IsMatch(scanned))
        {
            return true;
        }

        foreach (Match match in AbsolutePath().Matches(scanned))
        {
            var token = match.Value.TrimEnd(' ', '\t', ',', ';', ')', ']', '}');
            string full;
            try
            {
                full = Path.GetFullPath(Environment.ExpandEnvironmentVariables(token));
            }
            catch (Exception ex) when (ex is ArgumentException or NotSupportedException or PathTooLongException)
            {
                continue;
            }

            if (paths.IsUnderLive(full))
            {
                return true;
            }
        }

        return false;
    }

    [GeneratedRegex(@"(?i)profiles[\\/]zola(?![A-Za-z0-9_-])")]
    private static partial Regex ProfileMarker();

    [GeneratedRegex(@"(?i)(?<![A-Za-z0-9_-])ZolaClient(?![A-Za-z0-9_-])")]
    private static partial Regex ClientMarker();

    [GeneratedRegex(@"(?i)(?<![A-Za-z0-9_-])ZolaClient[\\/]secrets[\\/]deepgram_api_key")]
    private static partial Regex SharedKeyPath();

    [GeneratedRegex(@"(?i)(?:[A-Za-z]:[\\/]|%LOCALAPPDATA%[\\/])[^\s""'<>|*?\r\n]+")]
    private static partial Regex AbsolutePath();
}
