using System.Runtime.InteropServices;

namespace Zola.Client.Presence;

// P3-LIFE: hand Core Audio session enum for Hermes ffplay presence (no peak, no capture) — P3-D14 / S17
internal static class AudioSessionInterop
{
    internal const int ClsCtxAll = 23;
    internal const int DataFlowRender = 0;
    internal const int RoleMultimedia = 1;
    internal const int SessionStateInactive = 0;
    internal const int SessionStateActive = 1;
    internal const int SessionStateExpired = 2;

    internal static readonly Guid ClsidMmDeviceEnumerator = new("BCDE0395-E52F-467C-8E3D-C4579291692E");
    internal static readonly Guid IidImmDeviceEnumerator = new("A95664D2-9614-4F35-A746-DE8DB63617E6");
    internal static readonly Guid IidIAudioSessionManager2 = new("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F");
    internal static readonly Guid IidIAudioSessionControl2 = new("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D");

    [DllImport("ole32.dll")]
    internal static extern int CoCreateInstance(
        ref Guid clsid,
        IntPtr outer,
        int ctx,
        ref Guid iid,
        out IntPtr ppv);

    [DllImport("ole32.dll")]
    internal static extern int CoInitializeEx(IntPtr pv, int coInit);

    [DllImport("ntdll.dll")]
    private static extern int NtQueryInformationProcess(
        IntPtr processHandle,
        int processInformationClass,
        ref ProcessBasicInformation processInformation,
        int processInformationLength,
        out int returnLength);

    [StructLayout(LayoutKind.Sequential)]
    private struct ProcessBasicInformation
    {
        public IntPtr Reserved1;
        public IntPtr PebBaseAddress;
        public IntPtr Reserved2_0;
        public IntPtr Reserved2_1;
        public IntPtr UniqueProcessId;
        public IntPtr InheritedFromUniqueProcessId;
    }

    private delegate int QiDelegate(IntPtr self, ref Guid iid, out IntPtr ppv);
    private delegate uint ReleaseDelegate(IntPtr self);
    private delegate int GetDefaultAudioEndpointDelegate(IntPtr self, int dataFlow, int role, out IntPtr device);
    private delegate int ActivateDelegate(IntPtr self, ref Guid iid, int clsCtx, IntPtr activationParams, out IntPtr ppv);
    private delegate int GetSessionEnumeratorDelegate(IntPtr self, out IntPtr sessionEnum);
    private delegate int GetCountDelegate(IntPtr self, out int count);
    private delegate int GetSessionDelegate(IntPtr self, int index, out IntPtr session);
    private delegate int GetProcessIdDelegate(IntPtr self, out uint pid);
    private delegate int GetStateDelegate(IntPtr self, out int state);

    private static IntPtr VTable(IntPtr com, int slot)
    {
        return Marshal.ReadIntPtr(Marshal.ReadIntPtr(com), IntPtr.Size * slot);
    }

    private static T Fn<T>(IntPtr com, int slot) where T : class
    {
        return (T)(object)Marshal.GetDelegateForFunctionPointer(VTable(com, slot), typeof(T));
    }

    internal static int QueryInterface(IntPtr com, Guid iid, out IntPtr ppv)
    {
        return Fn<QiDelegate>(com, 0)(com, ref iid, out ppv);
    }

    internal static void Release(IntPtr com)
    {
        if (com != IntPtr.Zero)
        {
            Fn<ReleaseDelegate>(com, 2)(com);
        }
    }

    internal static bool TryOpenSessionManager(out IntPtr enumerator, out IntPtr device, out IntPtr manager)
    {
        enumerator = IntPtr.Zero;
        device = IntPtr.Zero;
        manager = IntPtr.Zero;
        var clsid = ClsidMmDeviceEnumerator;
        var iidEnum = IidImmDeviceEnumerator;
        var hr = CoCreateInstance(ref clsid, IntPtr.Zero, ClsCtxAll, ref iidEnum, out enumerator);
        if (hr != 0 || enumerator == IntPtr.Zero)
        {
            return false;
        }

        hr = Fn<GetDefaultAudioEndpointDelegate>(enumerator, 4)(
            enumerator,
            DataFlowRender,
            RoleMultimedia,
            out device);
        if (hr != 0 || device == IntPtr.Zero)
        {
            Release(enumerator);
            enumerator = IntPtr.Zero;
            return false;
        }

        var iidMgr = IidIAudioSessionManager2;
        hr = Fn<ActivateDelegate>(device, 3)(device, ref iidMgr, ClsCtxAll, IntPtr.Zero, out manager);
        if (hr != 0 || manager == IntPtr.Zero)
        {
            Release(device);
            Release(enumerator);
            device = IntPtr.Zero;
            enumerator = IntPtr.Zero;
            return false;
        }

        return true;
    }

    internal static List<(uint Pid, string Name, int State)> EnumerateSessionProcesses(IntPtr manager)
    {
        var list = new List<(uint, string, int)>();
        IntPtr sessions;
        var hr = Fn<GetSessionEnumeratorDelegate>(manager, 5)(manager, out sessions);
        if (hr != 0 || sessions == IntPtr.Zero)
        {
            return list;
        }

        int count;
        Fn<GetCountDelegate>(sessions, 3)(sessions, out count);
        for (var i = 0; i < count; i++)
        {
            IntPtr control;
            hr = Fn<GetSessionDelegate>(sessions, 4)(sessions, i, out control);
            if (hr != 0 || control == IntPtr.Zero)
            {
                continue;
            }

            var state = SessionStateExpired;
            if (Fn<GetStateDelegate>(control, 3)(control, out var controlState) == 0)
            {
                state = controlState;
            }

            IntPtr control2;
            hr = QueryInterface(control, IidIAudioSessionControl2, out control2);
            if (hr == 0 && control2 != IntPtr.Zero)
            {
                uint pid;
                if (Fn<GetProcessIdDelegate>(control2, 14)(control2, out pid) == 0 && pid != 0)
                {
                    var name = "?";
                    try
                    {
                        name = System.Diagnostics.Process.GetProcessById((int)pid).ProcessName;
                    }
                    catch
                    {
                    }

                    list.Add((pid, name, state));
                }

                Release(control2);
            }

            Release(control);
        }

        Release(sessions);
        return list;
    }

    internal static int GetParentProcessId(int pid)
    {
        try
        {
            using var process = System.Diagnostics.Process.GetProcessById(pid);
            var info = new ProcessBasicInformation();
            var hr = NtQueryInformationProcess(
                process.Handle,
                0,
                ref info,
                Marshal.SizeOf<ProcessBasicInformation>(),
                out _);
            if (hr != 0)
            {
                return 0;
            }

            return unchecked((int)info.InheritedFromUniqueProcessId.ToInt64());
        }
        catch
        {
            return 0;
        }
    }
}
