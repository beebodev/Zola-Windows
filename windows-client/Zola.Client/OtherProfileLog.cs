using System.Collections.Concurrent;
using System.Text.RegularExpressions;
using Zola.Client.Supervision;

namespace Zola.Client;

// PROC1-DEV: a serve for the other profile is logged once and left alone — PROC1-D4
internal static partial class OtherProfileLog
{
    private static readonly ConcurrentDictionary<int, byte> Seen = new();

    public static void Once(int pid, string profileFlag)
    {
        if (pid <= 0 || !Seen.TryAdd(pid, 0))
        {
            return;
        }

        var flag = SafeFlag().IsMatch(profileFlag) ? profileFlag : "unknown";
        SupervisionLog.WriteLine($"other_profile pid={pid.ToString(System.Globalization.CultureInfo.InvariantCulture)} profile={flag} action=ignored");
    }

    internal static void ResetForTests() => Seen.Clear();

    [GeneratedRegex("^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
    private static partial Regex SafeFlag();
}
