namespace Zola.Client.Supervision;

// P9-SUPERVISE: process generation and connection epoch are separate Interlocked counters — P9-D02
// Bump process generation in HermesProcessManager.SpawnAsync and AttachAsync, before the process is published.
// Check it in the Exited handler, ChatSocket.TryFault, and MainWindow.NoteLoss.
// Bump connection epoch in OutageGap.Apply on every connectivity loss, including a socket-only loss.
// Check it in VoiceController.OnVoiceTranscript, MainWindow.OnTranscriptReady, and MainWindow.SubmitTurnAsync.
public sealed class ServeGenerations
{
    private long _processGeneration;
    private long _connectionEpoch;

    public long ProcessGeneration => Interlocked.Read(ref _processGeneration);

    public long ConnectionEpoch => Interlocked.Read(ref _connectionEpoch);

    public long BumpProcessGeneration() => Interlocked.Increment(ref _processGeneration);

    public long BumpConnectionEpoch() => Interlocked.Increment(ref _connectionEpoch);

    public bool IsCurrentProcess(long generation) => generation == ProcessGeneration;

    public bool IsCurrentEpoch(long epoch) => epoch == ConnectionEpoch;
}

// P9-SUPERVISE: admission, submit, and clarify answers require the epoch stamped at receipt — P9-D02
public static class ConnectionEpochGuard
{
    public static bool Allows(long stampedEpoch, long currentEpoch) => stampedEpoch == currentEpoch;
}
