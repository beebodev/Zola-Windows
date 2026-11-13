using System.Text.RegularExpressions;

namespace Zola.Client;

public enum ServeProfileMatch
{
    NotDedicated,
    ThisProfile,
    OtherProfile,
}

// PROC1-DEV: the exact -p/--profile token is the authority. Hermes overwrites HERMES_HOME from -p — PROC1-D4
public static partial class ServeProfileMatcher
{
    public static ServeProfileMatch Classify(string? commandLine, string profileName, out string profileFlag)
    {
        profileFlag = "";
        if (string.IsNullOrEmpty(commandLine) || string.IsNullOrEmpty(profileName))
        {
            return ServeProfileMatch.NotDedicated;
        }

        if (commandLine.Contains("serve", StringComparison.OrdinalIgnoreCase) == false
            || commandLine.Contains("--isolated", StringComparison.OrdinalIgnoreCase) == false
            || commandLine.Contains("127.0.0.1", StringComparison.OrdinalIgnoreCase) == false)
        {
            return ServeProfileMatch.NotDedicated;
        }

        var token = ProfileToken().Match(commandLine);
        if (!token.Success)
        {
            return ServeProfileMatch.NotDedicated;
        }

        profileFlag = token.Groups[1].Value;
        if (!string.Equals(profileFlag, profileName, StringComparison.OrdinalIgnoreCase))
        {
            return ServeProfileMatch.OtherProfile;
        }

        return ServeProfileMatch.ThisProfile;
    }

    public static bool IsDedicatedServe(string commandLine, string profileName) =>
        Classify(commandLine, profileName, out _) == ServeProfileMatch.ThisProfile;

    [GeneratedRegex(
        @"(?:^|\s)(?:-p|--profile)(?:=|\s+)([A-Za-z0-9][A-Za-z0-9_-]{0,63})(?=\s|$)",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex ProfileToken();
}
