using System.IO.Pipes;
using System.Text;
using System.Text.Json;

namespace Zola.Client.Voice;

// P10-READ: redeem one armed handle on the ZolaPhone named pipe, the same pipe PhoneProcess uses. The launch secret
// proves this is the client. The value comes back on this pipe only; it is not logged, and it is returned to the
// reader, which is the only caller.
internal sealed class PhoneCodeRedeemer : ICodeRedeemer
{
    public const string DefaultPipeName = "ZolaPhone";
    private const int ConnectMilliseconds = 1000;

    private readonly Func<string> _secret;
    private readonly string _pipeName;

    public PhoneCodeRedeemer(Func<string> secret, string pipeName = DefaultPipeName)
    {
        _secret = secret;
        _pipeName = pipeName;
    }

    public async Task<CodeRedeemResult> RedeemAsync(string sessionId, string handle, CancellationToken ct)
    {
        if (ct.IsCancellationRequested)
        {
            throw new OperationCanceledException(ct);
        }

        var work = Task.Run(() => Ask(sessionId, handle), CancellationToken.None);
        var cancelled = Task.Delay(Timeout.Infinite, ct);
        var first = await Task.WhenAny(work, cancelled).ConfigureAwait(false);
        if (first != work)
        {
            // the pipe thread finishes on its own; whatever it returns is dropped here and the engine discards
            // a value for a handle the tool has already disarmed
            _ = work.ContinueWith(_ => { }, TaskScheduler.Default);
            throw new OperationCanceledException(ct);
        }

        return await work.ConfigureAwait(false);
    }

    private CodeRedeemResult Ask(string sessionId, string handle)
    {
        try
        {
            using var pipe = new NamedPipeClientStream(".", _pipeName, PipeDirection.InOut, PipeOptions.None);
            pipe.Connect(ConnectMilliseconds);
            var request = JsonSerializer.Serialize(new Dictionary<string, string>
            {
                ["type"] = "code.redeem",
                ["secret"] = _secret(),
                ["handle"] = handle,
                ["session_id"] = sessionId,
            });
            var bytes = Encoding.UTF8.GetBytes(request + "\n");
            pipe.Write(bytes, 0, bytes.Length);
            var line = Zola.Client.PhonePipe.ReadLine(pipe);
            if (string.IsNullOrEmpty(line))
            {
                return new CodeRedeemResult(false, null, CodeReadConstants.ReasonNoConnection);
            }

            using var doc = JsonDocument.Parse(line);
            var root = doc.RootElement;
            var ok = root.TryGetProperty("ok", out var okEl) && okEl.ValueKind == JsonValueKind.True;
            if (ok && root.TryGetProperty("value", out var valueEl) && valueEl.ValueKind == JsonValueKind.String)
            {
                return new CodeRedeemResult(true, valueEl.GetString(), null);
            }

            var reason = root.TryGetProperty("reason", out var reasonEl) && reasonEl.ValueKind == JsonValueKind.String
                ? reasonEl.GetString()
                : null;
            return new CodeRedeemResult(false, null, reason ?? "not_identifiable");
        }
        catch (Exception)
        {
            return new CodeRedeemResult(false, null, CodeReadConstants.ReasonNoConnection);
        }
    }
}
