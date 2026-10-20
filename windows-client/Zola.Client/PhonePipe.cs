using System.Text;

namespace Zola.Client;

// P10-INTAKE: a history result can be larger than one 64 KiB read — P10-D12
public static class PhonePipe
{
    public static string? ReadLine(Stream stream)
    {
        using var reader = new StreamReader(stream, Encoding.UTF8, detectEncodingFromByteOrderMarks: false, bufferSize: 1024, leaveOpen: true);
        return reader.ReadLine();
    }
}
