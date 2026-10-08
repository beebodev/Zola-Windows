namespace Zola.Client;

// P8-READ: WinUI-free /compress recognition — P8-D09
public static class CompressCommand
{
    public const string CommandText = "/compress";

    // P8-READ: second /compress while one slash.exec is in flight is not sent — P8-D09
    public const string AlreadyRunningText = "Compression is already running.";

    public static bool TryBegin(ref int inFlight)
    {
        return System.Threading.Interlocked.CompareExchange(ref inFlight, 1, 0) == 0;
    }

    public static void End(ref int inFlight)
    {
        System.Threading.Interlocked.Exchange(ref inFlight, 0);
    }

    public static bool IsExactCompress(string? text)
    {
        if (string.IsNullOrEmpty(text))
        {
            return false;
        }

        return string.Equals(text.Trim(), CommandText, System.StringComparison.OrdinalIgnoreCase);
    }
}
