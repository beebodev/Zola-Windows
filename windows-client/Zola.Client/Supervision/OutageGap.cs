namespace Zola.Client.Supervision;

// P9-SUPERVISE: gap order is synchronous and finishes before any restart await — P9-D02
public interface IOutageGap
{
    void InvalidateCapture();

    void DropPendingTranscript();

    void StopPlayback();

    void BlockInput();
}

public static class OutageGap
{
    public static long Apply(ServeGenerations generations, IOutageGap gap)
    {
        // P9-SUPERVISE: bump the connection epoch before any admit or submit can pass — P9-D02
        var epoch = generations.BumpConnectionEpoch();
        gap.InvalidateCapture();
        gap.DropPendingTranscript();
        gap.StopPlayback();
        gap.BlockInput();
        return epoch;
    }
}
