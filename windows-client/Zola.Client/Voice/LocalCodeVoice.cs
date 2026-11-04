using System.Runtime.InteropServices;
using System.Speech.Synthesis;

namespace Zola.Client.Voice;

// P10-READ: the code is spoken by one named Windows voice, on this computer, from memory. System.Speech renders to a
// MemoryStream and winmm plays that buffer. There is no file, no temp file, no network, and no call to voice.tts,
// so the value never reaches the serve process or its conversation.
internal sealed class LocalCodeVoice : ICodeVoice
{
    private const uint SndAsync = 0x0001;
    private const uint SndNoDefault = 0x0002;
    private const uint SndMemory = 0x0004;
    private static readonly TimeSpan PlaybackSlack = TimeSpan.FromMilliseconds(350);

    private readonly string _voiceName;
    private readonly object _gate = new();
    private GCHandle _pin;
    private byte[]? _buffer;

    public LocalCodeVoice(string? voiceName = null)
    {
        _voiceName = voiceName ?? CodeReadConstants.VoiceName;
    }

    [DllImport("winmm.dll", EntryPoint = "PlaySoundW", SetLastError = false)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PlaySound(IntPtr sound, IntPtr module, uint flags);

    public async Task<CodePlayback> SpeakAsync(string value, CancellationToken ct)
    {
        if (ct.IsCancellationRequested)
        {
            return CodePlayback.Cancelled;
        }

        var wave = await Task.Run(() => Render(value, _voiceName), CancellationToken.None).ConfigureAwait(false);
        if (ct.IsCancellationRequested)
        {
            Wipe(wave);
            return CodePlayback.Cancelled;
        }

        if (wave is null)
        {
            return CodePlayback.Failed;
        }

        var length = WaveDuration(wave);
        if (length is null || !Start(wave))
        {
            Wipe(wave);
            return CodePlayback.Failed;
        }

        try
        {
            await Task.Delay(length.Value + PlaybackSlack, ct).ConfigureAwait(false);
            return CodePlayback.Completed;
        }
        catch (OperationCanceledException)
        {
            return CodePlayback.Cancelled;
        }
        finally
        {
            Stop();
        }
    }

    public void Stop()
    {
        lock (_gate)
        {
            if (_buffer is null)
            {
                return;
            }

            // purge first, then release the buffer winmm was reading
            PlaySound(IntPtr.Zero, IntPtr.Zero, 0);
            if (_pin.IsAllocated)
            {
                _pin.Free();
            }

            Wipe(_buffer);
            _buffer = null;
        }
    }

    private bool Start(byte[] wave)
    {
        lock (_gate)
        {
            if (_buffer is not null)
            {
                return false;
            }

            _buffer = wave;
            _pin = GCHandle.Alloc(wave, GCHandleType.Pinned);
            var started = PlaySound(_pin.AddrOfPinnedObject(), IntPtr.Zero, SndMemory | SndAsync | SndNoDefault);
            if (!started)
            {
                _pin.Free();
                _buffer = null;
            }

            return started;
        }
    }

    // The digits and letters, one at a time, so the voice never reads "4712" as a number.
    internal static string SpokenForm(string value)
    {
        var parts = new List<string>();
        foreach (var c in value)
        {
            if (char.IsDigit(c))
            {
                parts.Add(c.ToString());
            }
            else if (char.IsLetter(c))
            {
                parts.Add(char.ToUpperInvariant(c).ToString());
            }
            else if (c == '-' && parts.Count > 0)
            {
                parts.Add(".");
            }
        }

        return string.Join(" ", parts);
    }

    // WAV bytes in memory, or null when the named voice is not installed or cannot render.
    internal static byte[]? Render(string value, string voiceName)
    {
        try
        {
            using var synth = new SpeechSynthesizer();
            string? match = null;
            foreach (var installed in synth.GetInstalledVoices())
            {
                var name = installed.VoiceInfo.Name;
                if (installed.Enabled && name.Contains(voiceName, StringComparison.OrdinalIgnoreCase))
                {
                    match = name;
                    break;
                }
            }

            if (match is null)
            {
                return null;
            }

            synth.SelectVoice(match);
            using var memory = new MemoryStream();
            synth.SetOutputToWaveStream(memory);
            synth.Speak(SpokenForm(value));
            synth.SetOutputToNull();
            var bytes = memory.ToArray();
            Wipe(memory.GetBuffer());
            return bytes.Length > 44 ? bytes : null;
        }
        catch (Exception)
        {
            return null;
        }
    }

    // Playback length from the WAV header: data bytes / byte rate.
    internal static TimeSpan? WaveDuration(byte[] wave)
    {
        if (wave.Length < 44 || wave[0] != (byte)'R' || wave[1] != (byte)'I' || wave[2] != (byte)'F' || wave[3] != (byte)'F')
        {
            return null;
        }

        var byteRate = 0;
        var offset = 12;
        while (offset + 8 <= wave.Length)
        {
            var id = System.Text.Encoding.ASCII.GetString(wave, offset, 4);
            var size = BitConverter.ToInt32(wave, offset + 4);
            if (id == "fmt " && offset + 8 + 12 <= wave.Length)
            {
                byteRate = BitConverter.ToInt32(wave, offset + 8 + 8);
            }
            else if (id == "data")
            {
                var available = wave.Length - (offset + 8);
                // a streamed header may carry 0 or -1 for the data size; the real length is what is in memory
                var bytes = size <= 0 || size > available ? available : size;
                return byteRate > 0 ? TimeSpan.FromSeconds((double)bytes / byteRate) : null;
            }

            if (size < 0)
            {
                return null;
            }

            offset += 8 + size + (size & 1);
        }

        return null;
    }

    private static void Wipe(byte[]? bytes)
    {
        if (bytes is not null)
        {
            Array.Clear(bytes);
        }
    }
}
