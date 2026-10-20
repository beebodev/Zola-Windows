namespace Zola.Client.Supervision;

// P10-INTAKE: a status poll that is still running skips the next tick — P10-D12
public static class PhonePollGate
{
    public static bool TryEnter(ref int busy) => System.Threading.Interlocked.CompareExchange(ref busy, 1, 0) == 0;

    public static void Exit(ref int busy) => System.Threading.Interlocked.Exchange(ref busy, 0);
}
