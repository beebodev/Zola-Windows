namespace Zola.Client.Supervision;

// S51F-FIX: one-shot mark that OutageGap clears capture before the UI reads it — S51F-D04
public sealed class OutageAwaitingMark
{
    private bool _flag;

    // Call at the start of each gap (InvalidateCaptureForOutage) so a prior mark cannot leak.
    public void BeginGap() => _flag = false;

    public void NoteWasTranscribing(bool wasTranscribing)
    {
        if (wasTranscribing)
        {
            _flag = true;
        }
    }

    public void NotePendingTranscriptDropped(bool dropped)
    {
        if (dropped)
        {
            _flag = true;
        }
    }

    // Consume once for ShowSupervisionStatus.
    public bool Consume()
    {
        var value = _flag;
        _flag = false;
        return value;
    }
}
