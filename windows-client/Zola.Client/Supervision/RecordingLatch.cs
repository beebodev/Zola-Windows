using Zola.Client.Voice;

namespace Zola.Client.Supervision;

// P9-SUPERVISE: the recording latch is local; these decisions are the only place it is cleared or stopped — P9-D02
public static class RecordingLatch
{
    public static bool StopRecordBeforeRearm(long generationAtGap, long generationAtReady)
        => generationAtGap >= 0 && generationAtGap == generationAtReady;

    public static bool ClearAfterSettledTick(
        bool hasOutstanding,
        bool hermesBusyUntilIdle,
        CaptureState state,
        bool captureActive,
        bool recorderIdle)
        => !hasOutstanding
            && !hermesBusyUntilIdle
            && state == CaptureState.Settled
            && (captureActive || !recorderIdle);
}
