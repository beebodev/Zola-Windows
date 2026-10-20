using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using Zola.Client.Speech;
using Zola.Client.Supervision;

namespace Zola.Client;

// P10-INTAKE: zola-phone is supervised like the watcher and is not serve's child — P10-D12
public sealed class PhoneProcess
{
    private const string PipeName = "ZolaPhone";
    private readonly SupervisedPython _inner;
    private readonly Func<string> _secret;

    public PhoneProcess(string profileDirectory, Func<string> secret)
    {
        _secret = secret;
        _inner = new SupervisedPython(
            profileDirectory,
            SupervisionConstants.ProcPhone,
            "zola_phone",
            "ZOLA_PHONE_PARENT_PID",
            SupervisionConstants.PhoneOutputFileName,
            () => _secret());
        _inner.LatchChanged += () => LatchChanged?.Invoke();
    }

    public WatcherProcessLatch Latch => _inner.Latch;

    public bool KeepsFailing => _inner.KeepsFailing;

    public event Action? LatchChanged;

    public void Start() => _inner.Start();

    public void StopDeliberate() => _inner.StopDeliberate();

    public string? ReadLink()
    {
        var body = Ask(new Dictionary<string, string> { ["type"] = "status" });
        return body is null ? null : Field(body, "link_state");
    }

    public string? StartPairing()
    {
        // P10-INTAKE: the code is returned to the dialog and is not written to a log — P10-D12
        var body = Ask(new Dictionary<string, string>
        {
            ["type"] = "pairing.start",
            ["secret"] = _secret(),
        });
        if (body is null || Field(body, "ok") == "false")
        {
            return null;
        }

        return Field(body, "code");
    }

    private static JsonElement? Ask(Dictionary<string, string> fields)
    {
        try
        {
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut, PipeOptions.None);
            pipe.Connect(300);
            var bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(fields) + "\n");
            pipe.Write(bytes, 0, bytes.Length);
            var line = PhonePipe.ReadLine(pipe);
            if (string.IsNullOrEmpty(line))
            {
                return null;
            }

            using var doc = JsonDocument.Parse(line);
            return doc.RootElement.Clone();
        }
        catch (Exception)
        {
            return null;
        }
    }

    private static string? Field(JsonElement? body, string name)
    {
        if (body is null || !body.Value.TryGetProperty(name, out var value))
        {
            return null;
        }

        return value.ValueKind switch
        {
            JsonValueKind.String => value.GetString(),
            JsonValueKind.True => "true",
            JsonValueKind.False => "false",
            _ => value.ToString(),
        };
    }
}
