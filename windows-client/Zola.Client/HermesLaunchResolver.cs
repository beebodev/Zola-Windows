using System.Net;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;

namespace Zola.Client;

// P1-CLIENT: locate python and the hermes-agent checkout the serve child must run from — P1-D01
static class HermesLaunchResolver
{
    public static bool TryResolve(out string pythonPath, out string hermesRoot, out string error)
    {
        // P1-CLIENT: ZOLA_HERMES_PYTHON / ZOLA_HERMES_ROOT override discovery for a non-default install — P1-D01
        hermesRoot = ResolveHermesRoot();
        pythonPath = ResolvePython(hermesRoot);
        if (pythonPath.Length == 0)
        {
            error = "Python was not found on PATH. Set ZOLA_HERMES_PYTHON to python.exe.";
            return false;
        }

        if (hermesRoot.Length == 0)
        {
            error = "hermes-agent was not found. Set ZOLA_HERMES_ROOT to the checkout that contains hermes_cli\\main.py.";
            return false;
        }

        error = "";
        return true;
    }

    private static string ResolvePython(string hermesRoot)
    {
        // P1-CLIENT: prefer an explicit interpreter, then the checkout venv, then PATH — P1-D01
        var fromEnv = Environment.GetEnvironmentVariable("ZOLA_HERMES_PYTHON");
        if (!string.IsNullOrWhiteSpace(fromEnv) && File.Exists(fromEnv))
        {
            return fromEnv;
        }

        if (hermesRoot.Length > 0)
        {
            var venvPython = Path.Combine(hermesRoot, ".venv", "Scripts", "python.exe");
            if (File.Exists(venvPython))
            {
                return venvPython;
            }
        }

        var pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (var dir in pathEnv.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            if (dir.Contains("WindowsApps", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            var candidate = Path.Combine(dir.Trim(), "python.exe");
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        return "";
    }

    private static string ResolveHermesRoot()
    {
        // P1-CLIENT: honor ZOLA_HERMES_ROOT, else a sibling hermes-agent of this repo — P1-D01
        var fromEnv = Environment.GetEnvironmentVariable("ZOLA_HERMES_ROOT");
        if (IsHermesRoot(fromEnv))
        {
            return Path.GetFullPath(fromEnv!);
        }

        foreach (var start in new[] { Environment.CurrentDirectory, AppContext.BaseDirectory })
        {
            var dir = new DirectoryInfo(start);
            while (dir is not null)
            {
                if (IsHermesRoot(Path.Combine(dir.FullName, "hermes-agent")))
                {
                    return Path.GetFullPath(Path.Combine(dir.FullName, "hermes-agent"));
                }

                if (dir.Parent is not null && IsHermesRoot(Path.Combine(dir.Parent.FullName, "hermes-agent")))
                {
                    return Path.GetFullPath(Path.Combine(dir.Parent.FullName, "hermes-agent"));
                }

                dir = dir.Parent;
            }
        }

        return "";
    }

    private static bool IsHermesRoot(string? path)
    {
        // P1-CLIENT: a checkout is identified by hermes_cli/main.py, the serve entry point — P1-D01
        return !string.IsNullOrWhiteSpace(path)
            && File.Exists(Path.Combine(path, "hermes_cli", "main.py"));
    }
}

// P1-CLIENT: recognize a serve process that was launched for the zola profile with --isolated — P1-D01
static partial class ZolaServeCommand
{
    public const string ProfileName = "zola";
    public const string BindHost = "127.0.0.1";
    public const int BindPort = 9119;

    public static bool IsDedicatedServe(string commandLine)
    {
        // P1-CLIENT: --isolated is required; -p zola alone re-execs onto the machine server — P1-D01
        if (commandLine.Contains("serve", StringComparison.OrdinalIgnoreCase) == false)
        {
            return false;
        }

        if (commandLine.Contains("--isolated", StringComparison.OrdinalIgnoreCase) == false)
        {
            return false;
        }

        if (commandLine.Contains(BindHost, StringComparison.OrdinalIgnoreCase) == false)
        {
            return false;
        }

        return ProfileFlag().IsMatch(commandLine);
    }

    public static int ReadPort(string commandLine)
    {
        // P1-CLIENT: the spawn uses a fixed port; the ready sentinel remains the source of truth — P1-D01
        var match = PortFlag().Match(commandLine);
        return match.Success && int.TryParse(match.Groups[1].Value, out var port) ? port : BindPort;
    }

    [GeneratedRegex(@"(?:^|\s)(?:-p|--profile)(?:=|\s+)zola(?:\s|$)", RegexOptions.IgnoreCase)]
    private static partial Regex ProfileFlag();

    [GeneratedRegex(@"--port(?:=|\s+)(\d+)", RegexOptions.IgnoreCase)]
    private static partial Regex PortFlag();
}

// P1-CLIENT: --port 0 is announced on the ready line; an already-running child is matched by its listen socket — P1-D01
static class LoopbackListener
{
    public static int PortFor(int processId)
    {
        var bufferSize = 0;
        var result = GetExtendedTcpTable(IntPtr.Zero, ref bufferSize, true, 2, TcpTableOwnerPidListener, 0);
        if (result != 122 && result != 0)
        {
            return 0;
        }

        var buffer = Marshal.AllocHGlobal(bufferSize);
        try
        {
            result = GetExtendedTcpTable(buffer, ref bufferSize, true, 2, TcpTableOwnerPidListener, 0);
            if (result != 0)
            {
                return 0;
            }

            var count = Marshal.ReadInt32(buffer);
            var rowSize = Marshal.SizeOf<TcpRow>();
            var offset = Marshal.SizeOf<int>();
            for (var i = 0; i < count; i++)
            {
                var row = Marshal.PtrToStructure<TcpRow>(buffer + offset + (i * rowSize));
                if (row.OwningPid != processId)
                {
                    continue;
                }

                var address = new IPAddress(row.LocalAddr);
                if (!IPAddress.IsLoopback(address))
                {
                    continue;
                }

                // P1-CLIENT: MIB_TCPROW stores the listen port in network byte order — P1-D01
                return (int)(((row.LocalPort & 0xFF) << 8) | ((row.LocalPort >> 8) & 0xFF));
            }
        }
        finally
        {
            Marshal.FreeHGlobal(buffer);
        }

        return 0;
    }

    private const int TcpTableOwnerPidListener = 3;

    [StructLayout(LayoutKind.Sequential)]
    private struct TcpRow
    {
        public uint State;
        public uint LocalAddr;
        public uint LocalPort;
        public uint RemoteAddr;
        public uint RemotePort;
        public uint OwningPid;
    }

    [DllImport("iphlpapi.dll", SetLastError = true)]
    private static extern uint GetExtendedTcpTable(
        IntPtr table, ref int size, bool order, int ipVersion, int tableClass, uint reserved);
}
